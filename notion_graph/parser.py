'''
Parsing progress:

block -> children_page, children_database, rich_text object, cells object, children blocks
databse -> title, pages
page -> title, property objects
property object -> relation object | mention object
rich_text | title -> mention objects
relation object -> page titles
mention object -> database title | page title
column_list -> column -> block
table -> table_row -> block
'''

import asyncio
import logging
from typing import Any, Callable

from notion_client import APIErrorCode, APIResponseError, Client
from pyvis.network import Network

from .helper import contains_mention_or_relation_type, is_same_block_id

__all__ = ["Parser"]

# All heading blocks("heading_1", "heading_2", and "heading_3") support children when the is_toggleable property is
# true.
SUPPORTED_BLOCK_TYPES = [
    "paragraph", "bulleted_list_item", "numbered_list_item", "toggle", "to_do", "quote", "callout",
    "column_list", "column", "child_page", "child_database", "table", "table_row", "heading_1", "heading_2",
    "heading_3", "link_to_page"
]

SUPPORTED_PAGE_PROPERTY_TYPES = [
    "relation", "rich_text", "title"
]

COLOR_BG = "#fff"
COLOR_NODE = "#757575"

logging.basicConfig(level=logging.INFO)


class Parser:
    def __init__(self, notion_version: str, bearer_token: str) -> None:
        self._notion = Client(notion_version=notion_version, auth=bearer_token)
        self._graph = Network(
            bgcolor=COLOR_BG,
            font_color=True,
            height="750px",
            cdn_resources="in_line")
        self._loop = asyncio.get_event_loop()

    async def parse(self, root_id: str) -> Network:
        logging.info('Parsing ...')
        await self._parse_block(root_id)
        logging.info('Parsing ... done')
        return self._graph

    async def export_to_html(self, file_path: str) -> None:
        logging.info('Graph is generated at: %s', file_path)
        self._graph.repulsion(node_distance=200, spring_length=200)
        html = self._graph.generate_html()
        with open(file_path, mode='w', encoding='utf-8') as fp:
            fp.write(html)

    async def _parse_block(self, root_id: str, obj: Any = None) -> None:
        if obj is None:
            obj = await self._retrieve_with_retry(
                self._notion.blocks.retrieve, root_id)
            if obj is None:
                return

        await self._parse_block_object(obj, root_id)

    async def _parse_database(self, id: str, db: Any = None, parent_page_or_database_id: str = "") -> None:
        if db is None:
            db = await self._retrieve_with_retry(self._notion.databases.retrieve, id)
            if db is None:
                return

        if db['archived']:
            return

        self._add_node(db)
        self._add_edge(parent_page_or_database_id, id)
        await self._parse_database_pages(id)

    async def _parse_page(self, id: str, page: Any = None, parent_page_or_database_id: str = "") -> None:
        if page is None:
            page = await self._retrieve_with_retry(self._notion.pages.retrieve, id)
            if page is None:
                return

        if page['archived']:
            return

        self._add_node(page)
        self._add_edge(parent_page_or_database_id, id)
        await self._parse_page_properties(page['properties'], id)
        await self._parse_block_children(id, id)

    async def _parse_block_object(self, obj: dict, parent_page_or_database_id: str = "") -> None:
        if obj['type'] not in SUPPORTED_BLOCK_TYPES or obj['archived']:
            return

        if obj['type'] == 'child_database':
            await self._parse_database(obj['id'], None, parent_page_or_database_id)
            return

        if obj['type'] == 'child_page':
            await self._parse_page(obj['id'], None, parent_page_or_database_id)
            return

        if obj['type'] == 'column_list' or obj['type'] == 'column':
            if obj['has_children']:
                await self._parse_block_children(
                    obj['id'], parent_page_or_database_id)
            return

        await self._parse_block_content(obj, parent_page_or_database_id)

    async def _parse_block_children(self, block_id: str, parent_page_or_database_id: str) -> None:
        list_object = None
        try:
            list_object = await self._retrieve_with_retry(
                self._notion.blocks.children.list, block_id)
        except Exception as e:
            logging.error("Error retrieving block children: %s", e)
        if list_object is None:
            return

        if isinstance(list_object, dict):
            block_list = list_object['results']

            for block in block_list:
                await self._parse_block_object(block, parent_page_or_database_id)

    async def _parse_database_pages(self, database_id: str) -> None:
        has_more = True
        next_cursor = None
        while has_more:
            data = await self._retrieve_with_retry(
                self._notion.databases.query, database_id, page_size=100, start_cursor=next_cursor)
            if data is None:
                return

            if isinstance(data, dict):
                pages = data['results']
                has_more = data['has_more']
                next_cursor = data['next_cursor']
                for page in pages:
                    await self._parse_page(page['id'], None, database_id)

    async def _parse_page_properties(self, prop_obj: dict, parent_page_or_database_id: str) -> None:
        '''Search page properties which contains "mention" or "relation" type.

        No need to deep search into relation pages, because if the relation page is under root page,
        it will be parsed as well; if the relation page is out of root page, it cannot be visited by this bearer token.
        '''

        if not contains_mention_or_relation_type(str(prop_obj)):
            return

        for i in prop_obj.values():
            if i['type'] not in SUPPORTED_PAGE_PROPERTY_TYPES:
                return

            if i['type'] == 'relation':
                await self._retrieve_relation_page_title(
                    i['relation'], parent_page_or_database_id)
            if i['type'] == 'rich_text' or i['type'] == 'title':
                await self._parse_rich_text_list(
                    i[i['type']], parent_page_or_database_id)

    async def _parse_block_content(self, obj: dict, parent_page_or_database_id: str) -> None:
        obj_value = obj[obj['type']]
        rich_text_list = obj_value.get('rich_text', None)
        if rich_text_list:
            await self._parse_rich_text_list(
                rich_text_list, parent_page_or_database_id)

        cells_metrics = obj_value.get('cells', None)
        if cells_metrics:
            await self._parse_cells_metrics(
                cells_metrics, parent_page_or_database_id)

        if obj.get('is_toggleable', False) or obj.get('has_children', False):
            await self._parse_block_children(obj['id'], parent_page_or_database_id)

    async def _parse_cells_metrics(self, cells_metrics: list, parent_page_or_database_id: str) -> None:
        for row_cells in cells_metrics:
            await self._parse_rich_text_list(row_cells, parent_page_or_database_id)

    async def _parse_rich_text_list(self, rich_text_list: list, parent_page_or_database_id: str) -> None:
        '''Example:

        [
            {
                "type": "mention",
                "mention": {
                    "type": "page",
                    "page": {
                        "id": "960ce6bd-eeb8-4674-bf79-996ff40e14f8"
                    }
                },
                "annotations": {
                    "bold": false,
                    "italic": false,
                    "strikethrough": false,
                    "underline": false,
                    "code": false,
                    "color": "default"
                },
                "plain_text": "paragraph sub-page",
                "href": "https://www.notion.so/960ce6bdeeb84674bf79996ff40e14f8"
            }
        ]
        '''
        if not contains_mention_or_relation_type(str(rich_text_list)):
            return

        for i in rich_text_list:
            if i['type'] == 'mention':
                await self._retrieve_mention_object_title(
                    i['mention'], parent_page_or_database_id)

    async def _retrieve_relation_page_title(self, relation_list: list, parent_page_or_database_id: str, **kwargs):
        '''Example:

        [
            {
                "id": "7d2d2701-5f09-48af-a1c5-d0b17b160a8a"
            }
        ]
        '''
        for relation_obj in relation_list:
            page = await self._retrieve_with_retry(
                self._notion.pages.retrieve, relation_obj['id'])
            if page is None:
                continue

            if isinstance(page, dict):
                self._add_node(page)
                self._add_edge(parent_page_or_database_id, page['id'])

    async def _retrieve_mention_object_title(self, mention_obj: dict, parent_page_or_database_id: str):
        '''Example:

        {
            "type": "page",
            "page": {
                "id": "960ce6bd-eeb8-4674-bf79-996ff40e14f8"
            }
        }
        '''
        if mention_obj['type'] == 'page':
            page = await self._retrieve_with_retry(
                self._notion.pages.retrieve, mention_obj[mention_obj['type']]['id'])
            if page is None:
                return

            if isinstance(page, dict):
                self._add_node(page)
                self._add_edge(parent_page_or_database_id, page['id'])

    def _add_node(self, block: any, **kwargs):
        """
        :param block: any type of block, page, database
        :kwargs url: page or database url
        """
        url = block.get('url', '')
        title = block.get('title', None)
        if not title or not isinstance(title, str):
            if block['object'] == 'database':
                title = block['title'][0]['plain_text']
            elif block['object'] == 'page':
                if block['parent']['type'] != "database_id":
                    title = block['properties']['title']['title'][0]['plain_text']
                else:
                    try:
                        title = block['properties']['Name']['title'][0]['plain_text']
                    except KeyError:
                        for key in block['properties'].keys():
                            if block['properties'][key]["id"] == "title":
                                title = block['properties'][key]['title'][0]['plain_text']
            else:
                title = block[block['type']]['title']

        logging.info("+node: %s", title)
        self._graph.add_node(
            block['id'],
            label=title,
            title=f'<a href="{url}">open page</a>',
            color=COLOR_NODE,
            size=10,
            borderWidth=0)

    def _add_edge(self, lnode_id: str, rnode_id: str):
        if is_same_block_id(lnode_id, rnode_id):
            return

        self._graph.add_edge(lnode_id, rnode_id)

    async def _retrieve_with_retry(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except APIResponseError as e:
            if e.code == APIErrorCode.RateLimited:
                await asyncio.sleep(1)
                return await func(*args, **kwargs)
            else:
                return None
