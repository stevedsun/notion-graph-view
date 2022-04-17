from graph import my_graph
from config import notion


class TitleParser:
    def __init__(self, obj: dict):
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
    def __init__(self, obj: dict):
        self.rich_text_objs = obj

    @property
    def mentioned_blocks(self) -> list:
        blocks = []
        for obj in self.rich_text_objs:
            if obj['type'] == 'mention' and obj['mention']['type'] == 'page':
                blocks.append(obj['mention']['page'])
            if obj['type'] == 'mention' and obj['mention']['type'] == 'database':
                blocks.append(obj['mention']['database'])
        return blocks


# Todo(steve): Notion API return relation value is [] (empty?)
class RelationParser:
    def __init__(self, obj: dict):
        self.relation_objs = obj

    @property
    def mentioned_blocks(self) -> list:
        return []


class BlockParser:
    def __init__(self, obj: dict, parent_id=None):
        print("[{}] -> {}".format(self.__class__.__name__, obj['id']))
        self.linked_blocks = []
        self.children_ids = set()
        self.title = ""
        self.id = obj['id']
        self.obj = obj
        self.has_children = False
        self.parent_id = parent_id
        self.parse_self()
        self.parse_children()
        self.add_to_graph()
        self.parse_relations()

    def add_to_graph(self):
        my_graph.add_node(self)

    def add_linked_block(self, block):
        if block and type(block) == dict:
            self.linked_blocks.append(block)
        if block and type(block) == list:
            self.linked_blocks.extend(block)

    def add_children_id(self, id):
        if not id:
            return
        if type(id) == list:
            self.children_ids.update(id)
        else:
            self.children_ids.add(id)

    def parse_self(self):
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

    def parse_children(self):
        if self.has_children or (self.obj and self.obj.get('has_children', None)):
            children = notion.blocks.children.list(self.id)['results']
            for block in children:
                self.add_children_id(block['id'])
                BlockParser(block, self.parent_id)

    def parse_relations(self):
        for block in self.linked_blocks:
            BlockParser(block, self.parent_id)


class PageParser(BlockParser):

    def parse_self(self):
        self.parse_properties()

    def parse_properties(self):
        properties = self.obj['properties']
        for v in properties.values():
            if v['type'] == 'title':
                title_parser = TitleParser(v['title'])
                self.title = title_parser.title
                self.add_linked_block(title_parser.mentioned_blocks)
            if v['type'] == 'rich_text':
                rich_text_parser = RichTextParser(v['rich_text'])
                self.add_linked_block(rich_text_parser.mentioned_blocks)
            if v['type'] == 'relation':
                relation_parser = RelationParser(v['relation'])
                self.add_linked_block(relation_parser.mentioned_blocks)


class ChildPageParser(PageParser):
    pass


class DatabaseParser(BlockParser):
    def parse_self(self):
        self.parse_title()

    def parse_title(self):
        title_parser = TitleParser(self.obj['title'])
        self.title = title_parser.title
        self.add_linked_block(title_parser.mentioned_blocks)

    def parse_children(self):
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
                BlockParser(page, self.parent_id)


class ChildDatabaseParser(DatabaseParser):
    pass


class CommonTextParser(BlockParser):
    def __init__(self, obj: dict, parent_id: str):
        print("[{}] -> {}".format(self.__class__.__name__, obj['id']))
        self.linked_blocks = set()
        self.children_ids = set()
        self.id = obj['id']
        self.type = obj['type']
        self.title = '<' + self.type + '>'
        self.obj_dict = obj[self.type]
        self.obj = None
        self.has_children = obj['has_children']
        self.parent_id = parent_id
        self.parse_self()
        self.parse_children()
        self.add_to_graph()
        self.parse_relations()

    def parse_self(self):
        for k, v in self.obj_dict.items():
            if k == 'rich_text':
                rich_text_parser = RichTextParser(v)
                self.add_linked_block(rich_text_parser.mentioned_blocks)


class TableParser(BlockParser):
    def __init__(self, obj: dict, parent_id: str):
        print("[{}] -> {}".format(self.__class__.__name__, obj['id']))
        self.linked_blocks = set()
        self.children_ids = set()
        self.obj = None
        self.id = obj['id']
        self.type = obj['type']
        self.title = '<' + self.type + '>'
        self.has_children = obj['has_children']
        self.parent_id = parent_id
        self.parse_children()
        self.add_to_graph()
        self.parse_relations()


class TableRowParser(BlockParser):
    def __init__(self, obj: dict, parent_id: str):
        print("[{}] -> {}".format(self.__class__.__name__, obj['id']))
        self.linked_blocks = set()
        self.children_ids = set()
        self.id = obj['id']
        self.type = obj['type']
        self.title = '<' + self.type + '>'
        self.cells = obj[self.type]['cells']
        self.obj = None
        self.has_children = obj['has_children']
        self.parent_id = parent_id
        self.parse_self()
        self.parse_children()
        self.add_to_graph()
        self.parse_relations()

    def parse_self(self):
        for cell in self.cells:
            for obj in cell:
                if obj['type'] == 'mention' and obj['mention']['type'] == 'page':
                    self.add_linked_block(obj['mention']['page'])
                if obj['type'] == 'mention' and obj['mention']['type'] == 'database':
                    self.add_linked_block(obj['mention']['database'])
