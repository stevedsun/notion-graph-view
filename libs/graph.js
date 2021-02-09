var container = document.getElementById('container');
var data = {
    nodes: nodes,
    edges: edges
};
var options = {
    layout: {
        randomSeed: 1
    },
    edges: {
        width: 0.5,
        smooth: {
          enabled: false,
        },
        color: {
          color:'#A9A9A9',
          highlight:'#191970',
          opacity:0.6
        }
    },
    nodes: {
        shape: "dot",
        size: 10,
        color: {
          border: '#A9A9A9',
          background: '#A9A9A9',
          highlight: {
            border: '#191970',
            background: '#191970'
          }
        },
        font: {
          color: '#A9A9A9',
          size: 12
        }
    },
};
var network = new vis.Network(container, data, options);
