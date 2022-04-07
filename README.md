# Notion Graph View

![](https://img.shields.io/github/pipenv/locked/python-version/stevedsun/notion-graph-view)

Export [Notion](https://notion.so) pages to a Roam Research like graph view.

![](https://tva1.sinaimg.cn/large/008eGmZEly1gnhdionmecj30yf0u0115.jpg)

## How to use it

**Setup Python 3.9 dependencies**

```shell
pip install -r requirements.txt
```

**Setup Notion token**

Login notion.so and get `token_v2` from browser ([How?](https://www.redgregory.com/notion/2020/6/15/9zuzav95gwzwewdu1dspweqbv481s5)). Paste it to `config.py`>`my_token_v2`.

Paste the page url which your want to analyse into `config.py`>`my_url`.

**Run it**

```shell
python main.py
```

Finally `graph_view.html` will be generated at the current path, open it with any browser.

## Changelog

- [x] Read Notion pages, export to graph view image
- [x] Upgrade python version
- [x] Replace notion-client by notion-sdk-py
- [ ] Use lightweight renderer solution
