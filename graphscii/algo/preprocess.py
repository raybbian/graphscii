import networkx as nx


class Preprocess:
    """
    Gives all vertices the vertex type and reformats their names, as well as transforms the graph into an undirected graph and storing edge directions (for post)
    """

    def __init__(self, G: nx.Graph | nx.DiGraph | nx.MultiGraph | nx.MultiDiGraph):
        if type(G) == nx.MultiGraph or type(G) == nx.MultiDiGraph or type(G) == nx.DiGraph:
            raise ValueError("Only undirected, simple graphs are currently supported")

        self.G = G.copy()
        label_mapping = {v: ('vertex', v) for v in self.G.nodes()}
        nx.relabel_nodes(self.G, label_mapping, copy=False)
