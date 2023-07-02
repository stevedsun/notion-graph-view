import argparse
from .parser import Parser
from . import NOTION_VERSION


def main():
    parser = argparse.ArgumentParser(prog="notion-graph")

    parser.add_argument('--page', '-p', help='Notion page ID', required=True)
    parser.add_argument(
        '--token', '-t', help='Notion integration token', required=True)
    parser.add_argument(
        '--out', '-o', help='Output path, e.g. `./graph_out.html`', required=False, default="./graph_out.html")
    args = parser.parse_args()
    parser = Parser(NOTION_VERSION, args.token)
    parser.parse(args.page)
    parser.export_to_html(args.out)


if __name__ == '__main__':
    main()
