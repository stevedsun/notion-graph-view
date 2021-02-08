class Parser:
    def __init__(self, block):
        self.props = []
        self.relation_props = []
        self.node_set = set()
        self.edge_set = []
        self.nodes = []
        self.edges = []
        if block.type == "collection_view_page":
            collection = block.collection
            self.add_node(collection.id, collection.name)
            self.parse_collection(collection)
        else:
            self.add_node(block.id, block.title_plaintext)
            self.parse_page(block)

    def add_node(self, node_id, node_title):
        if node_id in self.node_set:
            return
        self.node_set.add(node_id)
        self.nodes.append(dict(id=node_id, label=node_title, size=3))

    def add_edge(self, source_id, target_id):
        if {source_id, target_id} in self.edge_set:
            return
        self.edge_set.append({source_id, target_id})
        self.edges.append(dict({"from": source_id, "to": target_id}))

    def get_graph(self):
        graph = dict(nodes=self.nodes, edges=self.edges)
        return graph

    def parse_backlinks(self, page):
        backlinks = page.get_backlinks()
        if backlinks:
            for block in backlinks:
                if block.type == 'page' or block.type == 'collection_view_page':
                    linked_block = block
                else:
                    linked_block = block.parent
                self.add_node(linked_block.id, linked_block.title_plaintext)
                self.add_edge(page.id, linked_block.id)

    def parse_collection(self, collection):
        row_blocks = collection.get_rows()
        self.get_row_props(row_blocks)
        for row in row_blocks:
            self.add_node(row.id, row.title_plaintext)
            self.add_edge(collection.id, row.id)
            # parse properties
            for relation_prop in self.relation_props:
                try:
                    relation_block_list = row.get_property(relation_prop)
                except AttributeError:
                    continue

                for rb in relation_block_list:
                    self.add_node(rb.id, rb.title_plaintext)
                    self.add_edge(row.id, rb.id)
            # parse children & backlinks block
            self.parse_backlinks(row)
            self.parse_children(row)

    def parse_children(self, parent_block):
        for child_block in parent_block.children:
            if child_block.type == 'page':
                self.add_node(child_block.id, child_block.title_plaintext)
                self.add_edge(parent_block.id, child_block.id)
                self.parse_page(child_block)
            if child_block.type == 'collection_view' or child_block.type == 'collection_view_page':
                collection = child_block.collection
                self.add_node(collection.id, collection.name)
                self.add_edge(parent_block.id, child_block.id)
                self.parse_collection(collection)

    def get_row_props(self, row_blocks):
        first_block = row_blocks[0]
        for schema in first_block.schema:
            self.props.append(schema['slug'])
            if schema['type'] == 'relation':
                self.relation_props.append(schema['slug'])

    def parse_page(self, page):
        self.parse_backlinks(page)
        self.parse_children(page)
