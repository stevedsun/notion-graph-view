class Graph:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.parsed_block_ids = set()

    def has_node_parsed(self, block):
        return block.id in self.parsed_block_ids and block.title != '<block>'

    def add_node(self, block):
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
