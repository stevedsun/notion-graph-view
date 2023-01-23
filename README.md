![](images/snap.png)

# Notion Graph View

![github](https://img.shields.io/badge/python-3.9-blue.svg) ![github](https://img.shields.io/badge/license-MIT-green.svg) ![github](https://img.shields.io/badge/notion_version-2022.06.28-lightgrey.svg)

Export [Notion](https://notion.so) pages to a Roam-Research like graph view.

## 📜 Usage

### Environment

- Python >= 3.9

### Installing

```shell
pip install notion-graph
```

### Notion API Setup

1. Create a [notion internal integration](https://www.notion.so/my-integrations) and generate an `Internal Integration Token`.

   👉 [Learn more about authorization](https://developers.notion.com/docs/authorization)

2. Open one notion page on browser, select "Add connections" and add your integration account.
3. Find your base `Page ID` from browser url, for example:

> if page url is: https://www.notion.so/yourName/PageTitle-8a4b5ff100d648fb8d39d4bfa756ff3f, `8a4b5ff100da48fb8d39d4bfa756ff3f` is the `Page ID`

### Quickly Running

```shell
python -m notion_graph -p <Page ID> -t <Integration Token> -o <PNG file path to export>
```

For instance,

```shell
python -m notion_graph -p 856391c93ae64bd1b7ebf699ca0cd861 -t secret_b8p7uLp3j3n95IDgofC9GviXP111Skx6NOt2d20U8e -o ./graph_out.png
```

`graph_out.png` would be generated at your specific path.

### Importing as a Python Library

You can also import `notion_graph` as a library.

For instance, drawing your own diagram by [matplotlib](https://matplotlib.org/).

```python
import notion_graph as ng
import networkx as nx
import matplotlib.pyplot as plt

my_ng = ng.NotionGraph(bearer_token="secret_b8p7uLp3j3n95IDgofC9GviXP111Skx6NOt2d20U8e")
graph = my_ng.parse(page_id="856391c93ae64bd1b7ebf699ca0cd861")
# graph is a networkx.classes.graph.Graph object

pos = nx.spring_layout(graph)
labels = nx.get_node_attributes(graph, 'title')
options = {
    "node_size": 50,
    "node_color": "tab:gray",
    "font_size": 10,
    "width": 0.5,
    "with_labels": True,
    "labels": labels
}

nx.draw(graph, pos, **options)
plt.show()
plt.savefig('./graph.png')
```

## Testing Environment

The testing page is [Notion-grap-view-demo](https://sund.notion.site/Notion-graph-view-Demo-856391c93ae64bd1b7ebf699ca0cd861). You can duplicate the page to your Notion account and run the project to test if everything goes well.

## Development Guide

This project's dependencies are managed by [PDM](https://pdm.fming.dev/latest/).

```shell
brew install pdm
pdm install
```

Running the project by:

```shell
pdm run start -p <page_id> -t <notion_token> -o ./graph_out.png
```

## 🔗 Supported Link

|                    | database | page |
| ------------------ | -------- | ---- |
| paragraph          | ✔️       | ✔️   |
| bulleted_list_item | ✔️       | ✔️   |
| numbered_list_item | ✔️       | ✔️   |
| to_do              | ✔️       | ✔️   |
| toggle             | ✔️       | ✔️   |
| child_page         | ✔️       | ✔️   |
| child_database     | ✔️       | ✔️   |
| embed              |          |      |
| callout            | ✔️       | ✔️   |
| quote              | ✔️       | ✔️   |
| heading_1          | ✔️       | ✔️   |
| heading_2          | ✔️       | ✔️   |
| heading_3          | ✔️       | ✔️   |
| column             |          |      |
| column_list        |          |      |
| synced_block       |          |      |
| link_to_page       |          |      |
| table              | ✔️       | ✔️   |
| table_row          | ✔️       | ✔️   |
