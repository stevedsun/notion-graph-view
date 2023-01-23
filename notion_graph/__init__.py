from .parser import Parser
import networkx as nx

NOTION_VERSION = '2022-06-28'


class NotionGraph:
    """The main class to parse Notion page.

    :param bearer_token: Notion integration token`.
    """

    def __init__(self, bearer_token: str) -> None:
        self._parser = Parser(NOTION_VERSION, bearer_token)

    def parse(self, page_id: str) -> nx.Graph:
        """Parse a given Notion page, get the Networkx graph data object"""
        return self._parser.parse(page_id)

    def export(self, png_file_path):
        """Export the Networkx graph to a png file"""
        return self._parser.export_to_png(png_file_path)
