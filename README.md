![](images/snap.png)

# Notion Graph View

![github](https://img.shields.io/badge/python-3.9-blue.svg) ![github](https://img.shields.io/badge/license-MIT-green.svg) ![github](https://img.shields.io/badge/notion_api_ver.-2022.02.22-lightgrey.svg)

Export [Notion](https://notion.so) pages to a Roam-Research like graph view.

## 📜 Usage

### Environment

- Python 3.7 or later ( 3.9 is recommended )

### Install

```shell
pip install -r requirements.txt
```

### Setup Notion API

1. Create a [notion internal integration](https://www.notion.so/my-integrations) and generate an `Internal Integration Token`.

   👉 [Learn more about authorization](https://developers.notion.com/docs/authorization)

2. Open one notion page on browser and share it to your integration.
3. Find your base `Page ID` from browser url, for example:

> if page url is: https://www.notion.so/yourName/PageTitle-8a4b5ff100d648fb8d39d4bfa756ff3f, `8a4b5ff100da48fb8d39d4bfa756ff3f` is the `Page ID`

4. Paste `Internal Integration Token` and `Page ID` to `config.py`:

```python
NOTION_TOKEN = "secret_TBqfsxyH1slTpaignyZqQnDAAAn0MaeDEc2l96cdubD"
PAGE_ID = "8a4b5ff100d648fb8d39d4bfa756ff3f"
```

> On Linux, you can export these two environment varibles instead.

### Run

```shell
python main.py
```

`graph_view.html` would be generated at the project path, open it with any browser. (`/lib` and `graph_view.html` should be in the same folder)

## 🔗 Link support

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
| callout            |          |      |
| quote              |          |      |
| column             |          |      |
| column_list        |          |      |
| synced_block       |          |      |
| link_to_page       |          |      |
| table              | ✔️       | ✔️   |
| table_row          |          |      |
