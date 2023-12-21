import networkx as nx

from tsm.preprocess import Preprocess


class Simplify:
    """
    Given a graph, which may contain loops, return a simplified graph by inserting dummy nodes.
    """
    def __init__(self, preprocess: Preprocess):
        self.G = preprocess.G.copy()
        self.s_cnt = 0

        # should iterate a copy of original edges such that we can modify the graph
        for u, v in list(self.G.edges()):
            if u == v:
                self.simplify_self_loop(u, v)

    def simplify_self_loop(self, u, v):
        """
        Given a self-loop, insert dummy nodes to simplify it.
        """
        self.G.add_edge(u, ("loop_dummy", self.s_cnt))
        self.G.add_edge(("loop_dummy", self.s_cnt), ("simple_dummy", self.s_cnt + 1))
        self.G.add_edge(("loop_dummy", self.s_cnt + 1), v)

        self.s_cnt += 2
        self.G.remove_edge(u, v)
