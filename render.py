from jinja2 import Template

template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style type="text/css">
    #container {
      width: 800px;
      height: 800px;
      border: 1px solid lightgray;
    }

  </style>
  <title>{{title}}</title>
</head>
<body>
<div id="container"></div>
<script type="text/javascript" src="vis-network.min.js"></script>
<script>
    var nodes = new vis.DataSet({{nodes}});
    var edges = new vis.DataSet({{edges}});
    var container = document.getElementById('container');
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {
        edges: { 
            width: 0.5,
            smooth: {
              enabled: false,
            },
            color: {
              color:'#696969',
              highlight:'#848484',
              hover: '#848484',
              opacity:0.6
            }
        },
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
    f = open("graph_view.html", "w")
    f.write(html)
    f.close()
