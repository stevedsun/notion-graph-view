from graph import my_graph
from parser import BlockParser
from render import render
from config import *


def read_page():
    block = notion.blocks.retrieve(PAGE_ID)
    BlockParser(block)
    render(my_graph.get_graph())


if __name__ == '__main__':
    read_page()
