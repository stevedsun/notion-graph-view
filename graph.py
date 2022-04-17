class Graph:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.parsed_block_ids = set()

    def has_node_parsed(self, block):
        return block.id in self.parsed_block_ids

    def add_node(self, block):
        if self.has_node_parsed(block):
            return

        self.nodes.append(dict(id=block.id, label=block.title, size=2))
        for child_id in block.children_ids:
            self.edges.append(dict({"from": block.id, "to": child_id}))

        for linked_block in block.linked_blocks:
            linked_id = linked_block['id']
            self.edges.append(dict({"from": block.id, "to": linked_id}))

        self.parsed_block_ids.add(block.id)

    def get_graph(self) -> dict[str, list]:
        return dict(nodes=self.nodes, edges=self.edges)


my_graph = Graph()
