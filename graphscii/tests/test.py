import copy
import unittest
import networkx as nx
import random

from matplotlib import pyplot as plt

from tsm.compaction import Compaction
from tsm.rectangularize import Rectangularize
from tsm.orthogonalize import Orthogonalize
from tsm.planarize import Planarize
from tsm.preprocess import Preprocess
from tsm.simplify import Simplify
from tsm.utils import v_is_structural


class PlanarizeGraph(unittest.TestCase):
    def test_planarize_petersen_graph(self):
        graph = nx.petersen_graph()

        for component in [graph.subgraph(c).copy() for c in nx.connected_components(graph)]:
            processed = Preprocess(component)
            simplified = Simplify(processed)
            planarized = Planarize(simplified)
            self.assertTrue(nx.is_planar(planarized.G))

    def test_planarize_random_graph(self):
        graph = nx.gnp_random_graph(20, 0.5)

        for component in [graph.subgraph(c).copy() for c in nx.connected_components(graph)]:
            processed = Preprocess(component)
            simplified = Simplify(processed)
            planarized = Planarize(simplified)
            self.assertTrue(nx.is_planar(planarized.G))


class OrthogonalizeGraph(unittest.TestCase):
    def test_orthogonalize_k_6(self):
        graph = nx.complete_graph(6)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)

    def test_orthogonalize_star_5(self):
        graph = nx.star_graph(5)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)


class RectangularizeGraph(unittest.TestCase):
    def test_compact_k_5(self):
        graph = nx.complete_graph(5)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        compacted = Rectangularize(orthogonalized)

    def test_compact_k_6(self):
        graph = nx.complete_graph(6)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        compacted = Rectangularize(orthogonalized)


    def test_compact_k_4(self):
        graph = nx.complete_graph(4)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        compacted = Rectangularize(orthogonalized)


    def test_compact_star_5(self):
        graph = nx.star_graph(5)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        compacted = Rectangularize(orthogonalized)

    def test_compact_single_node(self):
        graph = nx.star_graph(0)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        compacted = Rectangularize(orthogonalized)

    def test_compact_single_edge(self):
        graph = nx.complete_graph(2)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        compacted = Rectangularize(orthogonalized)


    def test_compact_petersen_graph(self):
        graph = nx.petersen_graph()
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        compacted = Rectangularize(orthogonalized)


class CompactGraph(unittest.TestCase):
    def test_compact_k_5(self):
        graph = nx.complete_graph(3)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)


        viewg = nx.Graph()
        for node in rectangularized.G.nodes():
            viewg.add_node(node, label=str(node))
        viewg.add_edges_from(rectangularized.G.edges())
        nx.write_graphml(viewg, 'out.graphml')

        compacted = Compaction(rectangularized)


if __name__ == '__main__':
    unittest.main()