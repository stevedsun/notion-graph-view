import argparse
from .parser import Parser
from . import NOTION_VERSION


def main():
    parser = argparse.ArgumentParser(prog="notion-graph")

    parser.add_argument('--page', '-p', help='Notion page ID', required=True)
    parser.add_argument(
        '--token', '-t', help='Notion integration token', required=True)
    parser.add_argument(
        '--serve', '-s', help='Running a web page to display graph view', required=False)
    parser.add_argument(
        '--out', '-o', help='Image output path, e.g. `./graph_out.png`', required=False, default="./graph_out.png")
    args = parser.parse_args()
    parser = Parser(NOTION_VERSION, args.token)
    parser.parse(args.page)
    parser.export_to_png(args.out)


if __name__ == '__main__':
    main()
