from .preprocess import Preprocess


class Simplify:
    """
    Given a graph, which may contain loops, return a simplified graph by inserting dummy nodes.
    """

    def __init__(self, preprocess: Preprocess):
        self.G = preprocess.G
        self.s_cnt = 0

        for u, v in list(self.G.edges()):
            if u == v:
                raise Exception("Graphs with loops are not supported yet.")
