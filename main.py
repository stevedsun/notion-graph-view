from notion.client import NotionClient

from config import *
from render import render
from parser import CollectionParser, PageParser


def read_page(token_v2, page_url):
    client = NotionClient(token_v2=token_v2)
    base_block = client.get_block(page_url)
    print("Page title is:", base_block.title)
    bfs_block(base_block)


def bfs_block(block):
    print(block.type, block.title)
    if block.type == "collection_view_page":
        collection = block.collection
        parser = CollectionParser(collection)
    else:
        parser = PageParser(block)

    graph = parser.get_graph()
    render(block.title, graph)


if __name__ == '__main__':
    read_page(my_token_v2, my_url)
