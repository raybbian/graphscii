# Graphscii

An application that prints ASCII representations of graphs!

## Features

- [x] Support for nonplanar graphs.
- [x] Support for graphs with maximum degree > 4.
- [x] Support for vertex labels.
- [ ] Support for directed graphs and multigraphs.
- [ ] Support for edge labels.
- [ ] Support for alternate character choices.

## Usage

First, clone the repository, set up a virtual environment, and install the
requirements. That might look something like this:

<pre>
$ git clone https://github.com/raybbian/graphscii && cd graphscii
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
</pre>

Then, you can print your graphs like this:

```pycon
>>> import networkx as nx
>>> from graphscii import to_ascii
>>> graph = nx.complete_graph(5)
>>> print(to_ascii(graph, with_labels=True))

          ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
          ┃                                       ┃
          ┃                                       ┃
          ┃      ┏━━━━━┓                          ┃
          ┃      ┃     ┃                          ┃
          ┃ ┏━━━━┫  2  ┣━━━━━━━━━━━━━━━━┓         ┃
          ┃ ┃    ┃     ┣━━━━━━┓         ┃         ┃
          ┃ ┃    ┗━━┳━━┛      ┃         ┃         ┃
       ┏━━┻━┻┓   ┏━━┻━━┓   ┏━━┻━━┓      ┃         ┃
       ┃     ┃   ┃     ┃   ┃     ┃      ┃         ┃
       ┃  0  ┣━━━┫  3  ┣━━━┫  1  ┣━━━━━━╋━━━━━━━━━┛
       ┃     ┃   ┃     ┃   ┃     ┃      ┃
       ┗━━┳━━┛   ┗━━┳━━┛   ┗━━┳━━┛      ┃
          ┃         ┃      ┏━━┻━━┓      ┃
          ┃         ┗━━━━━━┫     ┃      ┃
          ┗━━━━━━━━━━━━━━━━┫  4  ┣━━━━━━┛
                           ┃     ┃
                           ┗━━━━━┛
```

Or maybe even write your graph to a file:

```python
import networkx as nx
from graphscii import to_ascii

graph = nx.complete_bipartite_graph(3,3)
with open("output.txt", "w") as f:
    f.write(to_ascii(graph))
```
