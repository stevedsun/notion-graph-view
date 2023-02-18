'''
Parsing progress:

block -> children_page, children_database, rich_text object, cells object, children blocks
databse -> title, pages
page -> title, property objects
property object -> relation object | mention object
rich_text | title -> mention objects
relation object -> page titles
mention object -> database title | page title
'''

from notion_client import Client
import networkx as nx
import matplotlib.pyplot as plt
from .helper import contains_mention_or_relation_type

__all__ = ["Parser"]

# All heading blocks("heading_1", "heading_2", and "heading_3") support children when the is_toggleable property is true.
SUPPORTED_BLOCK_TYPES = [
    "paragraph", "bulleted_list_item", "numbered_list_item", "toggle", "to_do", "quote", "callout",
    "column", "child_page", "child_database", "table", "table_row", "heading_1", "heading_2",  "heading_3"
]

SUPPORTED_PAGE_PROPERTY_TYPES = [
    "relation", "rich_text", "title"
]


class Parser:
    def __init__(self, notion_version: str, bearer_token: str) -> None:
        self._notion = Client(notion_version=notion_version, auth=bearer_token)
        self._graph = nx.Graph()
        self._caching_ids = set()

    def parse(self, root_id: str) -> nx.Graph:
        self._parse_block(root_id)
        return self._graph

    def export_to_png(self, png_path: str):
        pos = nx.spring_layout(self._graph)
        labels = nx.get_node_attributes(self._graph, 'title')
        options = {
            "node_size": 10,
            "node_color": "black",
            "edge_color": "tab:gray",
            "linewidths": 0.5,
            "font_size": 6,
            "font_color": "black",
            "width": 0.5,
            "with_labels": True,
            "labels": labels,
            "alpha": 0.7,
            "verticalalignment": 'bottom',
        }

        nx.draw(self._graph, pos, **options)
        plt.savefig(png_path, dpi=300)
        print('Graph image is generated at:', png_path)

    def _parse_block(self, root_id: str, obj: dict = None) -> None:
        if obj is None:
            obj = self._notion.blocks.retrieve(root_id)

        self._parse_block_object(obj, root_id)

    def _parse_database(self, id: str, obj: dict = None, parent_page_or_database_id: str = None) -> None:
        if obj is None:
            obj = self._notion.databases.retrieve(id)

        if obj['archived']:
            return

        self._retrieve_page_or_database_title(id, parent_page_or_database_id)
        self._parse_database_pages(id)

    def _parse_page(self, id: str, obj: dict = None, parent_page_or_database_id: str = None) -> None:
        if obj is None:
            obj = self._notion.pages.retrieve(id)

        if obj['archived']:
            return

        self._retrieve_page_or_database_title(id, parent_page_or_database_id)
        self._parse_page_properties(obj['properties'], id)

    def _parse_block_object(self, obj: dict, parent_page_or_database_id: str = None) -> None:
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
            if obj['has_children']:
                self._parse_block_children(obj['id'], obj['id'])
            return

        obj_value = obj[obj['type']]
        # For the supported types with rich_text
        rich_text_list = obj_value.get(
            'rich_text', None)
        if rich_text_list:
            self._parse_rich_text_list(
                rich_text_list, parent_page_or_database_id)

        # For table -> table_row -> cells
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
            data = self._notion.databases.query(
                database_id, page_size=100, start_cursor=next_cursor)
            pages = data['results']
            has_more = data['has_more']
            next_cursor = data['next_cursor']
            for page in pages:
                self._parse_page(page['id'], None, database_id)

    def _parse_block_children(self, block_id: str, parent_page_or_database_id: str) -> None:
        list_object = self._notion.blocks.children.list(block_id)
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

    def _retrieve_relation_page_title(self, relation_list: list, parent_page_or_database_id: str):
        '''Example:

        [
            {
                "id": "7d2d2701-5f09-48af-a1c5-d0b17b160a8a"
            }
        ]
        '''
        for relation_obj in relation_list:
            block = self._notion.blocks.retrieve(relation_obj['id'])
            title = block[block['type']]['title']
            print('Found relation node:', title)
            self._graph.add_node(block['id'], title=title)
            self._graph.add_edge(parent_page_or_database_id, block['id'])

    def _retrieve_mention_object_title(self, mention_obj: dict, parent_page_or_database_id: str):
        '''Example:

        {
            "type": "page",
            "page": {
                "id": "960ce6bd-eeb8-4674-bf79-996ff40e14f8"
            }
        }
        '''
        block = self._notion.blocks.retrieve(
            mention_obj[mention_obj['type']]['id'])

        title = block[block['type']]['title']
        print('Found mention node:', title)
        self._graph.add_node(block['id'], title=title)
        self._graph.add_edge(parent_page_or_database_id, block['id'])

    def _retrieve_page_or_database_title(self, page_or_database_id: str, parent_page_or_database_id: str):
        block = self._notion.blocks.retrieve(page_or_database_id)
        title = block[block['type']]['title']
        print('Found node:', title)
        self._graph.add_node(page_or_database_id, title=title)
        self._graph.add_edge(parent_page_or_database_id, page_or_database_id)
