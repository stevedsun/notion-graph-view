from jinja2 import Template


def render(graph: dict) -> None:
    with open("libs/template.html") as f:
        template = f.read()
        t = Template(template)
        html = t.render(nodes=graph['nodes'], edges=graph['edges'])
        f = open("graph_view.html", "w")
        f.write(html)
        f.close()
