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
    def mentioned_ids(self) -> list[str]:
        ids = []
        for obj in self.title_objs:
            if obj['type'] == 'mention' and obj['mention']['type'] == 'page':
                ids.add(obj['mention']['page']['id'])
            if obj['type'] == 'mention' and obj['mention']['type'] == 'database':
                ids.add(obj['mention']['database']['id'])
        return ids


class RichTextParser:
    def __init__(self, obj: dict):
        self.rich_text_objs = obj

    @property
    def mentioned_ids(self) -> list[str]:
        ids = []
        for obj in self.rich_text_objs:
            if obj['type'] == 'mention' and obj['mention']['type'] == 'page':
                ids.add(self.obj['mention']['page']['id'])
            if obj['type'] == 'mention' and obj['mention']['type'] == 'database':
                ids.add(self.obj['mention']['database']['id'])
        return ids


# Todo(steve): Notion API return relation value is [] (empty?)
class RelationParser:
    def __init__(self, obj: dict):
        self.relation_objs = obj

    @property
    def mentioned_ids(self) -> list[str]:
        return []


class BlockParser:
    def __init__(self, obj: dict):
        self.linked_block_ids = set()
        self.title = ""
        self.id = obj['id']
        self.obj = obj
        self.has_children = False
        print("parsing block id: ", self.id)
        self.parse_self()
        self.add_to_graph()
        self.parse_children()
        self.parse_relations()

    def add_to_graph(self):
        my_graph.add_node(self)

    def parse_self(self):
        if self.obj['type'] == 'child_page':
            obj = notion.pages.retrieve(self.id)
            PageParser(obj)
        if self.obj['type'] == 'child_database':
            obj = notion.databases.retrieve(self.id)
            DatabaseParser(obj)
        if self.obj['type'] in ['paragraph', 'bulleted_list_item', 'numbered_list_item', 'to_do', 'toggle', 'callout', 'quote']:
            CommonParser(self.obj)
        if self.obj['type'] == 'link_to_page':
            # Todo(steve): API return unsupport type
            pass
        if self.obj['type'] == 'table':
            TableParser(self.obj)
        if self.obj['type'] == 'table_row':
            pass

    def parse_children(self):
        if self.has_children or (self.obj and self.obj.get('has_children', None)):
            children = notion.blocks.children.list(self.id)['results']
            for block in children:
                BlockParser(block)

    def parse_relations(self):
        for block_id in self.linked_block_ids:
            BlockParser(block_id)


class PageParser(BlockParser):

    def parse_self(self):
        self.parse_properties()

    def parse_properties(self):
        properties = self.obj['properties']
        for v in properties.values():
            if v['type'] == 'title':
                title_parser = TitleParser(v['title'])
                self.title = title_parser.title
                self.linked_block_ids.update(title_parser.mentioned_ids)
            if v['type'] == 'rich_text':
                rich_text_parser = RichTextParser(v['rich_text'])
                self.linked_block_ids.update(rich_text_parser.mentioned_ids)
            if v['type'] == 'relation':
                relation_parser = RelationParser(v['relation'])
                self.linked_block_ids.update(relation_parser.mentioned_ids)


class DatabaseParser(BlockParser):
    def parse_self(self):
        self.parse_title()

    def parse_title(self):
        title_parser = TitleParser(self.obj['title'])
        self.title = title_parser.title
        self.linked_block_ids.update(title_parser.mentioned_ids)


class CommonParser(BlockParser):
    def __init__(self, obj: dict):
        self.linked_block_ids = set()
        self.id = obj['id']
        self.type = obj['type']
        self.title = '<' + self.type + '>'
        self.obj_dict = obj[self.type]
        self.obj = None
        self.has_children = obj['has_children']
        self.parse_self()
        self.add_to_graph()
        self.parse_relations()
        self.parse_children()

    def parse_self(self):
        for k, v in self.obj_dict.items():
            if k == 'rich_text':
                rich_text_parser = RichTextParser(v)
                self.linked_block_ids.update(rich_text_parser.mentioned_ids)


class TableParser(BlockParser):
    def __init__(self, obj: dict):
        self.linked_block_ids = set()
        self.obj = None
        self.id = obj['id']
        self.type = obj['type']
        self.title = '<' + self.type + '>'
        self.has_children = obj['has_children']
        self.add_to_graph()
        self.parse_children()
        self.parse_relations()


class TableRowParser(BlockParser):
    def __init__(self, obj: dict):
        self.linked_block_ids = set()
        self.id = obj['id']
        self.type = obj['type']
        self.title = '<' + self.type + '>'
        self.cells = obj[self.type]['cells']
        self.obj = None
        self.has_children = obj['has_children']
        self.parse_self()
        self.add_to_graph()
        self.parse_children()
        self.parse_relations()

    def parse_self(self):
        for cell in self.cells:
            for obj in cell:
                if obj['type'] == 'mention' and obj['mention']['type'] == 'page':
                    self.linked_block_ids.add(obj['mention']['page']['id'])
                if obj['type'] == 'mention' and obj['mention']['type'] == 'database':
                    self.linked_block_ids.add(obj['mention']['database']['id'])
