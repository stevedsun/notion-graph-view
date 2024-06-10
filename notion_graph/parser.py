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

from typing import Any
import time
from notion_client import Client, APIResponseError, APIErrorCode
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


class Parser:
    def __init__(self, notion_version: str, bearer_token: str) -> None:
        self._notion = Client(notion_version=notion_version, auth=bearer_token)
        self._graph = Network(
            bgcolor=COLOR_BG,
            font_color=True,
            height="750px",
            cdn_resources="in_line")

    def parse(self, root_id: str) -> Network:
        print('Parsing ...')
        self._parse_block(root_id)
        print('Prasing ... done')
        return self._graph

    def export_to_html(self, file_path: str):
        print('Graph is generated at:', file_path)
        self._graph.repulsion(node_distance=200, spring_length=200)
        html = self._graph.generate_html()
        with open(file_path, mode='w', encoding='utf-8') as fp:
            fp.write(html)

    def _parse_block(self, root_id: str, obj: Any = None) -> None:
        if obj is None:
            try:
                obj = self._notion.blocks.retrieve(root_id)
            except APIResponseError:
                if APIResponseError.code == APIErrorCode.RateLimited:
                    time.sleep(1)
                    obj = self._notion.blocks.retrieve(root_id)
                else:
                    return

        self._parse_block_object(obj, root_id)

    def _parse_database(self, id: str, db: Any = None, parent_page_or_database_id: str = "") -> None:
        if db is None:
            try:
                db = self._notion.databases.retrieve(id)
            except APIResponseError:
                if APIResponseError.code == APIErrorCode.RateLimited:
                    time.sleep(1)
                    db = self._notion.databases.retrieve(id)
                else:
                    return

        if db['archived']:
            return

        self._add_node(db)
        self._add_edge(parent_page_or_database_id, id)
        self._parse_database_pages(id)

    def _parse_page(self, id: str, page: Any = None, parent_page_or_database_id: str = "") -> None:
        if page is None:
            try:
                page = self._notion.pages.retrieve(id)
            except APIResponseError:
                if APIResponseError.code == APIErrorCode.RateLimited:
                    time.sleep(1)
                    page = self._notion.pages.retrieve(id)
                else:
                    return

        if page['archived']:
            return

        self._add_node(page)
        self._add_edge(parent_page_or_database_id, id)
        self._parse_page_properties(page['properties'], id)
        self._parse_block_children(id, id)

    def _parse_block_object(self, obj: dict, parent_page_or_database_id: str = "") -> None:
        '''API Ref: https://developers.notion.com/reference/block#block-type-object

        Example:
        {
            "object": "block",
            "id": "136a23da-e2cf-4438-b40b-f9fb779b3172",
            "parent": {
                "type": "page_id",
                "page_id": "8080c51b-6c93-4342-9f4f-7d9f358ab9ba"
            },
            "created_time": "2023-01-19T23:54:00.000Z",
            "last_edited_time": "2023-01-19T23:54:00.000Z",
            "created_by": {
                "object": "user",
                "id": "1237204c-1cfe-4ddb-a8bd-61865a28f5d3"
            },
            "last_edited_by": {
                "object": "user",
                "id": "1237204c-1cfe-4ddb-a8bd-61865a28f5d3"
            },
            "has_children": false,
            "archived": false,
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "mention",
                        "mention": {
                            "type": "page",
                            "page": {
                                "id": "62788faf-1f04-4b33-9e10-f94a7ec1ddbf"
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
                        "plain_text": "database_page_1_sub-page",
                        "href": "https://www.notion.so/62788faf1f044b339e10f94a7ec1ddbf"
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": " ",
                            "link": null
                        },
                        "annotations": {
                            "bold": false,
                            "italic": false,
                            "strikethrough": false,
                            "underline": false,
                            "code": false,
                            "color": "default"
                        },
                        "plain_text": " ",
                        "href": null
                    }
                ],
                "color": "default"
            }
        }
        '''
        if obj['type'] not in SUPPORTED_BLOCK_TYPES or obj['archived']:
            return

        if obj['type'] == 'child_database':
            self._parse_database(obj['id'], None, parent_page_or_database_id)
            return

        if obj['type'] == 'child_page':
            self._parse_page(obj['id'], None, parent_page_or_database_id)
            return

        # column_list -> column -> block
        if obj['type'] == 'column_list' or obj['type'] == 'column':
            if obj['has_children']:
                self._parse_block_children(
                    obj['id'], parent_page_or_database_id)
            return

        obj_value = obj[obj['type']]
        # For the supported types with rich_text
        rich_text_list = obj_value.get(
            'rich_text', None)
        if rich_text_list:
            self._parse_rich_text_list(
                rich_text_list, parent_page_or_database_id)

        # table -> table_row -> cells
        cells_metrics = obj_value.get('cells', None)
        if cells_metrics:
            self._parse_cells_metrics(
                cells_metrics, parent_page_or_database_id)

        if obj.get('is_toggleable', False) or obj.get('has_children', False):
            self._parse_block_children(obj['id'], parent_page_or_database_id)

    def _parse_page_properties(self, prop_obj: dict, parent_page_or_database_id: str) -> None:
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
                self._retrieve_relation_page_title(
                    i['relation'], parent_page_or_database_id)
            if i['type'] == 'rich_text' or i['type'] == 'title':
                self._parse_rich_text_list(
                    i[i['type']], parent_page_or_database_id)

    def _parse_database_pages(self, database_id: str) -> None:
        has_more = True
        next_cursor = None
        while has_more:
            try:
                data = self._notion.databases.query(
                    database_id, page_size=100, start_cursor=next_cursor)
            except APIResponseError:
                if APIResponseError.code == APIErrorCode.RateLimited:
                    time.sleep(1)
                    data = self._notion.databases.query(
                        database_id, page_size=100, start_cursor=next_cursor)
                else:
                    return

            if isinstance(data, dict):
                pages = data['results']
                has_more = data['has_more']
                next_cursor = data['next_cursor']
                for page in pages:
                    self._parse_page(page['id'], None, database_id)

    def _parse_block_children(self, block_id: str, parent_page_or_database_id: str) -> None:
        try:
            list_object = self._notion.blocks.children.list(block_id)
        except APIResponseError:
            if APIResponseError.code == APIErrorCode.RateLimited:
                time.sleep(1)
                list_object = self._notion.blocks.children.list(block_id)
            else:
                return

        if isinstance(list_object, dict):
            block_list = list_object['results']

            for block in block_list:
                self._parse_block_object(block, parent_page_or_database_id)

    def _parse_cells_metrics(self, cells_metrics: list, parent_page_or_database_id: str) -> None:
        for row_cells in cells_metrics:
            self._parse_rich_text_list(row_cells, parent_page_or_database_id)

    def _parse_rich_text_list(self, rich_text_list: list, parent_page_or_database_id: str) -> None:
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
                self._retrieve_mention_object_title(
                    i['mention'], parent_page_or_database_id)

    def _retrieve_relation_page_title(self, relation_list: list, parent_page_or_database_id: str, **kwargs):
        '''Example:

        [
            {
                "id": "7d2d2701-5f09-48af-a1c5-d0b17b160a8a"
            }
        ]
        '''
        for relation_obj in relation_list:
            try:
                page = self._notion.pages.retrieve(relation_obj['id'])
            except APIResponseError:
                if APIResponseError.code == APIErrorCode.RateLimited:
                    time.sleep(1)
                    page = self._notion.pages.retrieve(relation_obj['id'])
                else:
                    continue

            if isinstance(page, dict):
                self._add_node(page)
                self._add_edge(parent_page_or_database_id, page['id'])

    def _retrieve_mention_object_title(self, mention_obj: dict, parent_page_or_database_id: str):
        '''Example:

        {
            "type": "page",
            "page": {
                "id": "960ce6bd-eeb8-4674-bf79-996ff40e14f8"
            }
        }
        '''
        if mention_obj['type'] == 'page':
            try:
                page = self._notion.pages.retrieve(
                    mention_obj[mention_obj['type']]['id'])
            except APIResponseError:
                if APIResponseError.code == APIErrorCode.RateLimited:
                    time.sleep(1)
                    page = self._notion.pages.retrieve(
                        mention_obj[mention_obj['type']]['id'])
                else:
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
                    title = block['properties']['Name']['title'][0]['plain_text']
            else:
                title = block[block['type']]['title']

        print("+node:", title)
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
