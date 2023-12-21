import networkx as nx
import itertools

from dcel import Dcel
from tsm.simplify import Simplify


class Planarize:
    """
    Given a simple graph, planarize it by inserting dummy nodes at edge crossings
    """

    def __init__(self, simplify: Simplify):
        self.G = simplify.G.copy()
        self.d_cnt = 0
        self.edges_to_add = set(edge for edge in self.G.edges())
        self.form_maximal_planar_subgraph()

        for edge in self.edges_to_add:
            self.add_edge_form_dummies(edge)

        self.dcel = self.get_dcel_of_cur_graph()

    def form_maximal_planar_subgraph(self):
        """
        Gets MPS by first generating the DFS spanning tree, then trying to add each edge and checking planarity
        """
        added_edges = set()
        T = nx.dfs_tree(self.G)
        self.G.clear_edges()
        self.G.add_edges_from([edge for edge in T.edges()])
        added_edges.update([edge for edge in T.edges()])
        self.edges_to_add.difference_update(added_edges)

        for edge in self.edges_to_add:
            self.G.add_edge(edge[0], edge[1])
            if not nx.is_planar(self.G):
                self.G.remove_edge(edge[0], edge[1])
            else:
                added_edges.add(edge)
        self.edges_to_add.difference_update(added_edges)

    def add_edge_form_dummies(self, edge):
        # can possibly do online updates instead of creating new planar dual every time, but i too smol brain
        ext_planar_dual = self.get_planar_dual_of_cur_graph(edge[0], edge[1])
        shortest_path = nx.shortest_path(ext_planar_dual, edge[0], edge[1])

        for i, (u, v) in enumerate(list(itertools.pairwise(shortest_path))[1:-1]):
            # even though there may be multiple edges from u to v (faces), we choose any one of them to form the edge
            # crossing
            bad_edge = ext_planar_dual[u][v][0]['over_edge']

            prev_node = ('crossing_dummy', self.d_cnt - 1) if i > 0 else edge[0]
            cur_node = ('crossing_dummy', self.d_cnt)
            next_node = ('crossing_dummy', self.d_cnt + 1) if i < len(shortest_path) - 4 else edge[1]

            self.G.remove_edge(bad_edge[0], bad_edge[1])
            self.G.add_edge(bad_edge[0], cur_node)
            self.G.add_edge(cur_node, bad_edge[1])

            self.G.add_edge(prev_node, cur_node)
            if next_node == edge[1]:
                self.G.add_edge(cur_node, next_node)

            self.d_cnt += 1

    def get_dcel_of_cur_graph(self):
        def get_external_face(of_dcel, of_pos):
            """
            Taken from tsmpy
            """
            corner_node = min(of_pos, key=lambda k: (of_pos[k][0], of_pos[k][1]))

            sine_vals = {}
            for node in self.G.adj[corner_node]:
                dx = of_pos[node][0] - of_pos[corner_node][0]
                dy = of_pos[node][1] - of_pos[corner_node][1]
                sine_vals[node] = dy / (dx ** 2 + dy ** 2) ** 0.5

            other_node = min(sine_vals, key=lambda node: sine_vals[node])
            return of_dcel.half_edges[corner_node, other_node].inc

        is_planar, embedding = nx.check_planarity(self.G)
        assert is_planar
        pos = nx.combinatorial_embedding_to_pos(embedding)
        dcel = Dcel(self.G, embedding)
        dcel.ext_face = get_external_face(dcel, pos)
        dcel.ext_face.is_external = True
        return dcel

    def get_planar_dual_of_cur_graph(self, u, v):
        dcel = self.get_dcel_of_cur_graph()
        cur_planar_dual = nx.MultiGraph()
        ok_list = [u, v]

        for edge in self.G.edges():
            he, he_twin = dcel.half_edges[edge], dcel.half_edges[edge].twin
            cur_planar_dual.add_edge(he.inc.id, he_twin.inc.id, over_edge=edge)  # connect the two faces

            if he.ori.id in ok_list:
                cur_planar_dual.add_edge(he.ori.id, he.inc.id)  # connect the vertex to each of their faces
                cur_planar_dual.add_edge(he.ori.id, he_twin.inc.id)
            if he_twin.ori.id in ok_list:
                cur_planar_dual.add_edge(he_twin.ori.id, he.inc.id)
                cur_planar_dual.add_edge(he_twin.ori.id, he_twin.inc.id)

        return cur_planar_dual
