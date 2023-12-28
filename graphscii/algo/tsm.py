from timeit import default_timer as timer

import networkx as nx

from .compaction import Compaction
from .display import Display
from .orthogonalize import Orthogonalize
from .planarize import Planarize
from .preprocess import Preprocess
from .rectangularize import Rectangularize
from .simplify import Simplify


def to_ascii(graph: nx.Graph, verbose=False, with_labels=False):
    start = timer()
    out = ""
    for component in [graph.subgraph(c) for c in nx.connected_components(graph)]:
        if nx.number_of_nodes(component) == 1:
            single_node = list(component.nodes())[0]
            out += handle_degenerate(single_node, with_labels)
            continue
        processed = Preprocess(component)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized, with_labels=with_labels)
        display = Display(compacted, with_labels=with_labels)
        out += display.build_output()

    end = timer()

    if verbose:
        print(
            f'Processing graph (component) with {nx.number_of_nodes(graph)} nodes and {nx.number_of_edges(graph)} edges')
        print(f'Took total of {end - start} seconds')

    return out


def handle_degenerate(vertex_id, with_labels=False):
    if with_labels:
        vertex_id = str(vertex_id)
        return f"┏━{'━' * len(vertex_id)}━┓\n┃ {vertex_id} ┃\n┗━{'━' * len(vertex_id)}━┛\n"
    else:
        return f"┏━━━┓\n┃   ┃\n┗━━━┛\n"
