import unittest
import networkx as nx
from timeit import default_timer as timer

from networkx.generators.harary_graph import hnm_harary_graph

from graphscii import to_ascii
from graphscii.algo.compaction import Compaction
from graphscii.algo.display import Display
from graphscii.algo.rectangularize import Rectangularize
from graphscii.algo.orthogonalize import Orthogonalize
from graphscii.algo.planarize import Planarize
from graphscii.algo.preprocess import Preprocess
from graphscii.algo.simplify import Simplify


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
        graph = nx.complete_graph(5)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized)

    def test_compact_star_8(self):
        graph = nx.star_graph(8)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized)

    def test_compact_k_6(self):
        graph = nx.complete_graph(6)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized)

    def test_compact_k_9(self):
        graph = nx.complete_graph(9)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized)

    def test_compact_k_10(self):
        graph = nx.complete_graph(10)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized)

    def test_compact_cycle_5(self):
        graph = nx.cycle_graph(5)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized)

    def test_compact_single_edge(self):
        graph = nx.complete_graph(2)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized)

    def test_goldman_harary(self):
        graph = hnm_harary_graph(11, 27)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized)

    def test_random_graph(self):
        graph = nx.gnp_random_graph(15, 0.5)
        processed = Preprocess(graph)
        simplified = Simplify(processed)
        planarized = Planarize(simplified)
        orthogonalized = Orthogonalize(planarized)
        rectangularized = Rectangularize(orthogonalized)
        compacted = Compaction(rectangularized)

class DisplayGraph(unittest.TestCase):
    def test_print(self):
        start = timer()
        graph = nx.gnm_random_graph(8, 15)
        after_graph = timer()
        processed = Preprocess(graph)
        after_process = timer()
        simplified = Simplify(processed)
        after_simplify = timer()
        planarized = Planarize(simplified)
        after_planarize = timer()
        orthogonalized = Orthogonalize(planarized)
        after_orth = timer()
        rectangularized = Rectangularize(orthogonalized)
        after_rect = timer()
        compacted = Compaction(rectangularized)
        after_compact = timer()
        display = Display(compacted)
        end = timer()

        print(display.build_output())

        print(f'Processing graph with {nx.number_of_nodes(graph)} nodes and {nx.number_of_edges(graph)} edges')
        print(f'Created graph in {after_graph - start} seconds')
        print(f'Processed graph in {after_process - after_graph} seconds')
        print(f'Simplified graph in {after_simplify - after_process} seconds')
        print(f'Planarized graph in {after_planarize - after_simplify} seconds')
        print(f'Orthogonalized graph in {after_orth - after_planarize} seconds')
        print(f'Rectangularized graph in {after_rect - after_orth} seconds')
        print(f'Displayed graph in {end - after_compact}')
        print(f'Compacted graph in {after_compact - after_rect} seconds')
        print(f'Took total of {end - start} seconds')


class TestProcess(unittest.TestCase):
    def test_process(self):
        graph = nx.gnp_random_graph(15, 0.5)
        print(to_ascii(graph, with_labels=True))


if __name__ == '__main__':
    unittest.main()
