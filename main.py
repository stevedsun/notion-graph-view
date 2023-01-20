from db_to_graph_parser import BlockParser
from db_to_graph_parser import my_graph
from render import render
from config import *


def read_page() -> None:
    block = notion.blocks.retrieve(PAGE_ID)
    BlockParser(block)
    render(my_graph.get_graph())


if __name__ == '__main__':
    read_page()
