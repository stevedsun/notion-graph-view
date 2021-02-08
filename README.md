# notion-graph-view

Exporting Notion pages to obsidian-like graph view.

![](https://tva1.sinaimg.cn/large/008eGmZEly1gng2xuwjutj30u10u0tjo.jpg)

## How to use it

Install dependencies with `pipenv` or `pip`:

```shell
pip install
# or
pipenv install
```

Login notion.so and get `token_v2` from browser ([How?](https://www.redgregory.com/notion/2020/6/15/9zuzav95gwzwewdu1dspweqbv481s5)). Paste it to `config.py`>`my_token_v2`.

Paste the page url which your want to analyse into `config.py`>`my_url`. 

Then run:

```shell
python main.py
```

Finally `graph_view.html` will be generated at the current path, open it with any browser.

## Todo

- [x] Read Notion pages, export to graph view image
- [ ] Generate js snippet which can be embedded to Notion
- [ ] Deploy as a SasS
