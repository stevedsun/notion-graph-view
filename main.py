import os
from notion_client import Client
from parser import Parser
from render import render
from config import *


def read_page(token_v2, page_url):
    client = Client(auth=token_v2)
    base_block = client.get_block(page_url)
    print("Root Page:", base_block.title)
    bfs_block(base_block)
    print("Graph view generated")
    os.system("open graph_view.html")


def bfs_block(block):
    print(block.type, block.title)
    parser = Parser(block)
    graph = parser.get_graph()
    render(block.title, graph)


if __name__ == '__main__':
    read_page(my_token_v2, my_url)
