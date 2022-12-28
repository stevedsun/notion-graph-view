from typing import Any
from config import notion
from relation_logger import relationLogger

class TitleParser:
    def __init__(self, obj: dict) -> None:
        self.title_objs = obj

    @property
    def title(self) -> str:
        title = ''
        for obj in self.title_objs:
            title += obj['plain_text']
        return title

    @property
    def mentioned_blocks(self) -> list:
        blocks = []
        for obj in self.title_objs:
            if obj['type'] == 'mention' and obj['mention']['type'] == 'page':
                blocks.append(obj['mention']['page'])
            if obj['type'] == 'mention' and obj['mention']['type'] == 'database':
                blocks.append(obj['mention']['database'])
        return blocks


class RichTextParser:
    def __init__(self, obj: dict, parent_id) -> None:
        self.rich_text_objs = obj
        self.parent_id = parent_id

    @property
    def mentioned_blocks(self) -> list:
        blocks = []
        for obj in self.rich_text_objs:
            if obj['type'] == 'mention' and obj['mention']['type'] == 'page':
                blocks.append(obj['mention']['page'])
            if obj['type'] == 'mention' and obj['mention']['type'] == 'database':
                blocks.append(obj['mention']['database'])
            if obj['type'] == 'text' and obj['href'] != None:
                relationId = obj['href'].replace('/', '')
                if(relationLogger.relationExists(self.parent_id, relationId) == False):
                    try:
                        page = notion.pages.retrieve(relationId)
                        blocks.append(page)
                        relationLogger.addRelation(self.parent_id, relationId)
                    except Exception:
                        pass

                    
        return blocks


class RelationParser:
    def __init__(self, obj: dict, parent_id):
        self.relation_objs = obj
        self.parent_id = parent_id

    @property
    def mentioned_blocks(self) -> list:
        pages = []
        for relation in self.relation_objs:
            relationId = relation['id']
            if(relationLogger.relationExists(self.parent_id, relationId) == False):
                page = notion.pages.retrieve(relationId)
                pages.append(page)
                relationLogger.addRelation(self.parent_id, relationId)
        return pages


class BlockParser:
    def __init__(self, obj: dict, parent_id: str = None) -> None:
        print("[{}] -> {}".format(self.__class__.__name__, obj['id']))
        self.linked_blocks = []
        self.children_ids = set()
        self.title = "<block>"
        self.id = obj['id']
        self.obj = obj
        self.has_children = self.obj.get('has_children', True)
        self.parent_id = parent_id
        self.parse_self()
        self.parse_children()
        self.parse_relations()
        self.add_to_graph()

    def add_to_graph(self):
        my_graph.add_node(self)

    def add_linked_block(self, block: Any) -> None:
        if block and type(block) == dict:
            self.linked_blocks.append(block)
        if block and type(block) == list:
            self.linked_blocks.extend(block)

    def add_children_id(self, id: Any) -> None:
        if not id:
            return
        if type(id) == list:
            self.children_ids.update(id)
        else:
            self.children_ids.add(id)

    def parse_self(self) -> None:
        if self.obj.get('object', None) and self.obj['object'] == 'page':
            obj = notion.pages.retrieve(self.id)
            PageParser(obj)
        if self.obj.get('object', None) and self.obj['object'] == 'database':
            obj = notion.databases.retrieve(self.id)
            DatabaseParser(obj)
        if self.obj.get('object', None) and self.obj['object'] == 'block':
            if self.obj['type'] == 'child_page':
                obj = notion.pages.retrieve(self.id)
                ChildPageParser(obj)
            if self.obj['type'] == 'child_database':
                obj = notion.databases.retrieve(self.id)
                ChildDatabaseParser(obj)
            if self.obj['type'] in ['paragraph', 'bulleted_list_item', 'numbered_list_item', 'to_do', 'toggle', 'callout', 'quote']:
                CommonTextParser(self.obj, self.parent_id)
            if self.obj['type'] == 'link_to_page':
                # Todo(steve): API return unsupport type
                pass
            if self.obj['type'] == 'table':
                TableParser(self.obj, self.parent_id)
            if self.obj['type'] == 'table_row':
                pass

    def parse_children(self, parent_id: str = None) -> None:
        if self.has_children:
            children = notion.blocks.children.list(self.id)['results']
            for block in children:
                if block['type'] in ['child_page', 'child_database']:
                    self.add_children_id(block['id'])
                BlockParser(block, parent_id if parent_id else self.id)

    def parse_relations(self, parent_id: str = None) -> None:
        for block in self.linked_blocks:
            BlockParser(block, parent_id if parent_id else self.id)


class PageParser(BlockParser):

    def parse_self(self) -> None:
        self.parse_properties()
        

    def parse_properties(self) -> None:
        properties = self.obj['properties']
        for v in properties.values():
            if v['type'] == 'title':
                title_parser = TitleParser(v['title'])
                self.title = title_parser.title
                self.add_linked_block(title_parser.mentioned_blocks)
            if v['type'] == 'rich_text':
                rich_text_parser = RichTextParser(v['rich_text'], self.id)
                self.add_linked_block(rich_text_parser.mentioned_blocks)
            if v['type'] == 'relation':
                relation_parser = RelationParser(v['relation'], self.id)
                self.add_linked_block(relation_parser.mentioned_blocks)


class ChildPageParser(PageParser):
    pass


class DatabaseParser(BlockParser):
    def parse_self(self) -> None:
        self.parse_title()

    def parse_title(self) -> None:
        title_parser = TitleParser(self.obj['title'])
        self.title = title_parser.title
        self.add_linked_block(title_parser.mentioned_blocks)

    def parse_children(self) -> None:
        has_more = True
        next_cursor = None
        while has_more:
            data = notion.databases.query(
                self.id, page_size=10, start_cursor=next_cursor)
            pages = data['results']
            has_more = data['has_more']
            next_cursor = data['next_cursor']
            for page in pages:
                self.add_children_id(page['id'])
                BlockParser(page)


class ChildDatabaseParser(DatabaseParser):
    pass


class CommonTextParser(BlockParser):
    def __init__(self, obj: dict, parent_id: str) -> None:
        print("[{}] -> {}".format(self.__class__.__name__, obj['id']))
        self.linked_blocks = []
        self.children_ids = []
        self.id = obj['id']
        self.type = obj['type']
        self.title = '<' + self.type + '>'
        self.obj_dict = obj[self.type]
        self.obj = None
        self.has_children = obj['has_children']
        self.parent_id = parent_id
        self.parse_self()
        self.parse_children(self.parent_id)
        self.parse_relations(self.parent_id)
        self.add_to_graph()

    def parse_self(self) -> None:
        for k, v in self.obj_dict.items():
            if k == 'rich_text':
                rich_text_parser = RichTextParser(v, self.id)
                self.add_linked_block(rich_text_parser.mentioned_blocks)


class TableParser(BlockParser):
    def __init__(self, obj: dict, parent_id: str) -> None:
        print("[{}] -> {}".format(self.__class__.__name__, obj['id']))
        self.linked_blocks = []
        self.children_ids = []
        self.obj = None
        self.id = obj['id']
        self.type = obj['type']
        self.title = '<' + self.type + '>'
        self.has_children = obj['has_children']
        self.parent_id = parent_id
        self.parse_children(self.parent_id)
        self.parse_relations(self.parent_id)
        self.add_to_graph()


class TableRowParser(BlockParser):
    def __init__(self, obj: dict, parent_id: str) -> None:
        print("[{}] -> {}".format(self.__class__.__name__, obj['id']))
        self.linked_blocks = []
        self.children_ids = []
        self.id = obj['id']
        self.type = obj['type']
        self.title = '<' + self.type + '>'
        self.cells = obj[self.type]['cells']
        self.obj = None
        self.has_children = obj['has_children']
        self.parent_id = parent_id
        self.parse_self()
        self.parse_children(self.parent_id)
        self.parse_relations(self.parent_id)
        self.add_to_graph()

    def parse_self(self) -> None:
        for cell in self.cells:
            for obj in cell:
                if obj['type'] == 'mention' and obj['mention']['type'] == 'page':
                    self.add_linked_block(obj['mention']['page'])
                if obj['type'] == 'mention' and obj['mention']['type'] == 'database':
                    self.add_linked_block(obj['mention']['database'])


class Graph:
    def __init__(self) -> None:
        self.nodes = []
        self.edges = []
        self.parsed_block_ids = set()

    def has_node_parsed(self, block: BlockParser) -> bool:
        return block.id in self.parsed_block_ids and block.title != '<block>'

    def add_node(self, block: BlockParser) -> None:
        if self.has_node_parsed(block):
            return

        page_block_id = ''
        if block.parent_id:
            # for text block
            page_block_id = block.parent_id
        else:
            # for page and database block
            page_block_id = block.id
            if block.title != '<block>':
                self.nodes.append(
                    dict(id=page_block_id, label=block.title, size=2))

        for child_id in block.children_ids:
            self.edges.append(dict({"from": page_block_id, "to": child_id}))

        for linked_block in block.linked_blocks:
            linked_id = linked_block['id']
            self.edges.append(dict({"from": page_block_id, "to": linked_id}))

        self.parsed_block_ids.add(block.id)

    def get_graph(self) -> dict[str, list]:
        return dict(nodes=self.nodes, edges=self.edges)


my_graph = Graph()
