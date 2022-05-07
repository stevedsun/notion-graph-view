from parser import BlockParser
from render import render
from config import *


def read_page() -> None:
    block = notion.blocks.retrieve(PAGE_ID)
    bp = BlockParser(block)
    render(bp.get_graph())


if __name__ == '__main__':
    read_page()
