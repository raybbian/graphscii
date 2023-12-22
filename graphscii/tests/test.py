import copy
import unittest
import networkx as nx
import random

from matplotlib import pyplot as plt

from tsm.compaction import Compaction
from tsm.orthogonalize import Orthogonalize
from tsm.planarize import Planarize
from tsm.preprocess import Preprocess
from tsm.simplify import Simplify
from tsm.utils import v_is_structural


class SimplifyGraph(unittest.TestCase):
    def test_simplify_random_graph(self):
        graph = nx.gnp_random_graph(8, 0.7)

        for component in [graph.subgraph(c).copy() for c in nx.connected_components(graph)]:
            processed = Preprocess(component)
            simplified = Simplify(processed)
            for u, v in simplified.G.edges():
                self.assertTrue(simplified.G.number_of_edges(u, v) == 1)
                self.assertTrue(u != v)

    def test_simplify_graph_with_loops(self):
        graph = nx.Graph()
        for i in range(5):
            graph.add_edge(i, i)
            graph.add_edge(i, i + 1)

        processed = Preprocess(graph)
        simplified = Simplify(processed)
        for u, v in simplified.G.edges():
            self.assertTrue(simplified.G.number_of_edges(u, v) == 1)
            self.assertTrue(u != v)


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
        orthogonalized = Orthogonalize(planarized)
        # print(*orthogonalized.flow_dict.items(), sep='\n')
        for v in orthogonalized.clean_flow.nodes():
            sum_out = sum(sum(flow for face, flow in orthogonalized.flow_dict[v][u].items()) for u in orthogonalized.flow_dict[v])
            if v_is_structural(v):
                assert sum_out == 4

    def test_orthogonalize_star_5(self):
        graph = nx.star_graph(5)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        # print(*orthogonalized.clean_flow.edges(keys=True, data=True), sep='\n')
        # print(*orthogonalized.flow_dict.items(), sep='\n')
        for v in orthogonalized.clean_flow.nodes():
            sum_out = sum(sum(flow for face, flow in orthogonalized.flow_dict[v][u].items()) for u in orthogonalized.flow_dict[v])
            if v_is_structural(v):
                assert sum_out == 4


class CompactGraph(unittest.TestCase):
    def test_compact_k_5(self):
        graph = nx.complete_graph(5)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        compacted = Compaction(orthogonalized)


        nx.draw_planar(planarized.G)
        plt.show()
        write_out = copy.deepcopy(compacted.G)
        for v in write_out.nodes():
            write_out.nodes[v]['label'] = str(v)
        nx.write_graphml(write_out, 'temp.graphml')


if __name__ == '__main__':
    unittest.main()
