import os
from notion_client import Client


try:
    from credentials import NOTION_TOKEN, PAGE_ID
except ImportError:
    NOTION_TOKEN = PAGE_ID = None

if not NOTION_TOKEN:
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")

if not PAGE_ID:
    PAGE_ID = os.getenv("PAGE_ID")

if not (NOTION_TOKEN and PAGE_ID):
    raise RuntimeError(
        "You must provide your credentials in 'credentials.py' or as ENV variables. "
        "For the details, see https://github.com/stevedsun/notion-graph-view#setup-notion-api"
    )

notion = Client(auth=NOTION_TOKEN)
