from jinja2 import Template

template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style type="text/css">
    #container {
      width: 600px;
      height: 600px;
      border: 1px solid lightgray;
    }

  </style>
  <title>{{title}}</title>
</head>
<body>
<div id="container"></div>
<script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<script>
    var nodes = new vis.DataSet({{nodes}});
    var edges = new vis.DataSet({{edges}});
    var container = document.getElementById('container');
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {
        nodes: {
            shape: "dot",
            size: 5, 
        },
    };
    var network = new vis.Network(container, data, options);
</script>
</body>
</html>
'''


def render(title, graph):
    t = Template(template)
    html = t.render(title=title, nodes=graph['nodes'], edges=graph['edges'])
    f = open("graph.html", "w")
    f.write(html)
    f.close()
