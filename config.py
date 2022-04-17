import os
from notion_client import Client


# Paste your NOTION token (e.g. secret_balabalabalabala) and page id (e.g. 43a57ade6650460b980e96fde16b03f1) in "" below.
NOTION_TOKEN = ""
PAGE_ID = ""

if not NOTION_TOKEN:
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")

if not PAGE_ID:
    PAGE_ID = os.getenv("PAGE_ID")

notion = Client(auth=NOTION_TOKEN)
