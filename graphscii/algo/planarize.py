import collections
import itertools

import networkx as nx

from graphscii.dcel import Dcel
from .simplify import Simplify
from .utils import v_is_face


class Planarize:
    """
    Given a simple graph, planarize it by inserting dummy nodes at edge crossings
    """

    def __init__(self, simplify: Simplify):
        self.G = simplify.G

        self.d_cnt = 0
        self.ori_edges = [edge for edge in self.G.edges()]
        self.edges_to_add = [edge for edge in self.G.edges()]
        self.form_maximal_planar_subgraph()

        self.dcel = self.get_dcel_of_cur_graph()
        self.planar_dual = self.get_planar_dual()

        for edge in self.edges_to_add:
            self.add_edge_form_dummies(edge)

    def add_edge_form_dummies(self, edge):
        # first, find shortest path in planar dual consisting of only edge vertices, and faces
        vis = set()
        par = {}
        path = []
        q = collections.deque()
        ok_vertices = [edge[0], edge[1]]

        q.append((edge[0], None))
        par[edge[0]] = None
        vis.add(edge[0])

        while len(q) > 0:
            node, prev = q.popleft()
            if node == edge[1]:
                cur_node = node
                while cur_node is not None:
                    path.append(cur_node)
                    cur_node = par[cur_node]
                path = list(reversed(path))
            for nxt in self.planar_dual.neighbors(node):
                if nxt in vis or (not v_is_face(nxt) and nxt not in ok_vertices):
                    continue
                vis.add(nxt)
                par[nxt] = node
                q.append((nxt, node))

        def connect_nodes(prev_node, cur_node, succ_vu, succ_uv):
            self.G.add_edge(prev_node, cur_node)
            self.dcel.connect_with_he(prev_node, cur_node, succ_uv, succ_vu)

            he_p2m = self.dcel.half_edges[prev_node, cur_node]
            for he in he_p2m.traverse():
                self.planar_dual.add_edge(he.inc.id, he.twin.inc.id, key=he.id)
                self.planar_dual.add_edge(he.twin.inc.id, he.inc.id, key=he.twin.id)
            for he in he_p2m.twin.traverse():
                self.planar_dual.add_edge(he.inc.id, he.twin.inc.id, key=he.id)
                self.planar_dual.add_edge(he.twin.inc.id, he.inc.id, key=he.twin.id)
            for node in he_p2m.inc.surround_vertices():
                self.planar_dual.add_edge(node.id, he_p2m.inc.id, key=0)
                self.planar_dual.add_edge(he_p2m.inc.id, node.id, key=0)
            for node in he_p2m.twin.inc.surround_vertices():
                self.planar_dual.add_edge(node.id, he_p2m.twin.inc.id, key=0)
                self.planar_dual.add_edge(he_p2m.twin.inc.id, node.id, key=0)

        for i, (u, v) in enumerate(list(itertools.pairwise(path))[1:-1]):
            # even though there may be multiple edges from u to v (faces), we choose any one of them to form the edge
            # crossing
            bad_edge = None
            for e in self.planar_dual[u][v]:
                bad_edge = e
                break

            # bad_edge inc face is u
            bad_he = self.dcel.half_edges[bad_edge]
            assert bad_he.inc.id == u

            prev_node = ('crossing_dummy', self.d_cnt - 1) if i > 0 else edge[0]
            cur_node = ('crossing_dummy', self.d_cnt)
            next_node = ('crossing_dummy', self.d_cnt + 1) if i < len(path) - 4 else edge[1]

            self.G.remove_edge(bad_edge[0], bad_edge[1])
            self.G.add_edge(bad_edge[0], cur_node)
            self.G.add_edge(cur_node, bad_edge[1])
            self.dcel.add_node_between(bad_edge[0], cur_node, bad_edge[1])

            succ_vu = self.dcel.vertices[prev_node].get_half_edge(bad_he.inc)
            succ_uv = self.dcel.vertices[cur_node].get_half_edge(bad_he.inc)
            connect_nodes(prev_node, cur_node, succ_vu, succ_uv)
            self.planar_dual.remove_node(u)  # nuke all relations to this face, reestablish after face split

            if next_node == edge[1]:
                # need to add the last connection
                succ_vu = self.dcel.vertices[cur_node].get_half_edge(bad_he.twin.inc)
                succ_uv = self.dcel.vertices[next_node].get_half_edge(bad_he.twin.inc)
                connect_nodes(cur_node, next_node, succ_vu, succ_uv)
                self.planar_dual.remove_node(v)

            self.d_cnt += 1

    def form_maximal_planar_subgraph(self):
        """
        Gets MPS by first generating the DFS spanning tree, then trying to add each edge and checking planarity
        """
        added_edges = set()
        T = nx.dfs_tree(self.G)
        self.G.clear_edges()
        self.G.add_edges_from([edge for edge in T.edges()])
        added_edges.update([edge for edge in T.edges()])
        self.edges_to_add = [edge for edge in self.ori_edges if edge not in added_edges]

        for edge in self.edges_to_add:
            self.G.add_edge(edge[0], edge[1])
            if not nx.is_planar(self.G):
                self.G.remove_edge(edge[0], edge[1])
            else:
                added_edges.add(edge)
        self.edges_to_add = [edge for edge in self.ori_edges if edge not in added_edges]

    def get_dcel_of_cur_graph(self):
        def get_external_face(of_dcel, of_pos):
            """
            Taken from tsmpy
            """
            if len(of_dcel.vertices) == 1:
                for face in of_dcel.faces.values():
                    return face
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

    def get_planar_dual(self):
        cur_planar_dual = nx.MultiDiGraph()

        for edge in self.G.edges():
            he = self.dcel.half_edges[edge]
            cur_planar_dual.add_edge(he.inc.id, he.twin.inc.id, key=he.id)  # connect the two faces
            cur_planar_dual.add_edge(he.twin.inc.id, he.inc.id, key=he.twin.id)  # connect the two faces

        for face in self.dcel.faces.values():
            for vertex in face.surround_vertices():
                cur_planar_dual.add_edge(face.id, vertex.id, key=0)  # only need one of these edges, ever
                cur_planar_dual.add_edge(vertex.id, face.id, key=0)

        return cur_planar_dual
