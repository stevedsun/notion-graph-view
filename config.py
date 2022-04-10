from notion_client import Client


NOTION_TOKEN = "<your-sercet-token-here>"
PAGE_ID = "<base-page-id-here>"

notion = Client(auth=NOTION_TOKEN)
