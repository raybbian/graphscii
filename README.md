# Graphscii

An application that prints ASCII representations of graphs! Implemented with
Topology-Shape-Metrics [1]. Huge thanks to https://github.com/uknfire/tsmpy for
their Doubly Connected Edge List and Compaction implementations. You can find
some examples of graphscii's example outputs
[here.](https://github.com/raybbian/graphscii/tree/main/examples/)

## Features

- [x] Support for nonplanar graphs.
- [x] Support for disconnected graphs.
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

## Contributing

If you find a bug in the code, and you can reproduce it for a certain graph,
please feel free to open up an issue or a pull request. Your help towards fixing
my ~~terrible~~ code is greatly appreciated.

## Areas for Improvement

- [ ] Clean code up, merge the management of 3 data structures at once into one.
- [ ] Better comments and better code structure.
- [ ] Improved edge insertion (should yield much better drawings, see [4]).
- [ ] Successive shortest path algorithm, modified for negative cycles of length
      2 (potentially could speed up process on large graphs, compared to MILP
      solution, see [2]).

## Citations

[1] R. Tamassia. "On Embedding a Graph in the Grid with the Minimum Number of
Bends," in SIAM Journal on Computing, vol. 16, no. 3, pp. 421-444, 1987.

[2] M. Foßmeier, "Drawing high degree graphs with low bend numbers," in Graph
Drawing, 1996, pp. 254–266.

[3] M. Eiglsperger, M. Kaufmann, "Fast Compaction for Orthogonal Drawings with
Vertices of Prescribed Size," in Lecture Notes in Computer Science, 2002.

[4] Carsten Gutwenger, P. Mutzel, and R. Weiskircher, “Inserting an Edge into a
Planar Graph,” Algorithmica, vol. 41, no. 4, pp. 289–308, Jan. 2005.
