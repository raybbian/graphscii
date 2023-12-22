import networkx as nx
import math

from tsm.planarize import Planarize
from tsm.utils import *


class Orthogonalize:
    def __init__(self, planarize: Planarize):
        self.G = planarize.G
        self.dcel = planarize.dcel
        self.network_flow = None
        self.flow_dict = None
        self.clean_flow = None

        self.build_network_flow()
        self.solve_network_flow()

        self.strip_h_structures()
        self.clean_network_flow()

    def build_network_flow(self):
        assert nx.is_planar(self.G)

        self.network_flow = nx.MultiDiGraph()

        for v in self.G.nodes():
            self.network_flow.add_node(v, demand=self.G.degree[v] - 4)

        for i, face in enumerate(self.dcel.faces.values()):
            face_edges = [e.id for e in face.surround_half_edges()]
            face_len = len(face_edges)

            if i == 0:
                self.network_flow.add_node(face.id, demand=face_len + 4)
            else:
                self.network_flow.add_node(face.id, demand=face_len - 4)

            for j, edge in enumerate(face_edges):
                n_edge = face_edges[(j + 1) % face_len]
                self.network_flow.add_edge(edge[1], face.id, cost=0, capacity=math.inf, key=n_edge)

        c = 6 * self.G.number_of_nodes()
        for v in self.G.nodes():
            e_list = [e.id for e in self.dcel.vertices[v].surround_half_edges()]
            f_list = [e.inc.id for e in self.dcel.vertices[v].surround_half_edges()]
            k = len(e_list)

            for i in range(k):
                self.network_flow.add_node((f'h_aux_{v}_edge_l', i), demand=0)
                self.network_flow.add_node((f'h_aux_{v}_edge_r', i), demand=0)
                self.network_flow.add_node((f'h_aux_{v}_face', i), demand=0)

            for i in range(k):
                next_i = (i + 1) % k
                prev_i = (i - 1) % k
                if not v_is_dummy(v):
                    # type h1, edge stores the edge this face to face edge is going across, destination stores the face it goes to
                    self.network_flow.add_edge(f_list[i], (f'h_aux_{v}_edge_r', i), cost=2 * c + 1, capacity=1,
                                               key=e_list[i], destination=f_list[prev_i])
                    self.network_flow.add_edge(f_list[i], (f'h_aux_{v}_edge_l', next_i), cost=2 * c + 1, capacity=1,
                                               key=e_list[next_i], destination=f_list[next_i])
                    # type h2, the original face to vertex reverse edges, stores l_edge and r_edge and what is supposed to be u
                    self.network_flow.add_edge((f'h_aux_{v}_face', i), v, cost=0, capacity=1,
                                               key=e_list[i], origin=f_list[i])
                    # type h3
                    self.network_flow.add_edge((f'h_aux_{v}_edge_l', i), (f'h_aux_{v}_face', i), cost=0, capacity=1)
                    self.network_flow.add_edge((f'h_aux_{v}_edge_r', next_i), (f'h_aux_{v}_face', i), cost=0,
                                               capacity=1)
                    # type h4
                    self.network_flow.add_edge((f'h_aux_{v}_edge_l', i), (f'h_aux_{v}_edge_r', i), cost=-c, capacity=1)
                    self.network_flow.add_edge((f'h_aux_{v}_edge_r', i), (f'h_aux_{v}_edge_l', i), cost=-c, capacity=1)
                else:
                    self.network_flow.add_edge(f_list[i], (f'h_aux_{v}_edge_r', i), cost=1, capacity=math.inf,
                                               key=e_list[i], destination=f_list[prev_i])
                    self.network_flow.add_edge(f_list[i], (f'h_aux_{v}_edge_l', next_i), cost=1, capacity=math.inf,
                                               key=e_list[next_i], destination=f_list[next_i])
                    self.network_flow.add_edge((f'h_aux_{v}_edge_l', i), f_list[prev_i], cost=0, capacity=math.inf)
                    self.network_flow.add_edge((f'h_aux_{v}_edge_r', next_i), f_list[next_i], cost=0, capacity=math.inf)


    def solve_network_flow(self):
        self.flow_dict = nx.min_cost_flow(self.network_flow, "demand", "capacity", "cost")

    def strip_h_structures(self):
        """
        Strip the H structures as described in the paper.
        """
        self.clean_flow = nx.MultiDiGraph()

        for v in self.network_flow.nodes():
            if v_is_h_aux(v):
                continue
            self.clean_flow.add_node(v)

        for u, v, key in self.network_flow.edges:
            data = self.network_flow[u][v][key]
            flow = self.flow_dict[u][v][key]

            if v_is_face(u) and v_is_h_aux(v):
                self.clean_flow.add_edge(u, data['destination'], pseudokey=key, flow=flow)
            elif v_is_h_aux(u) and v_is_structural(v):
                self.clean_flow.add_edge(data['origin'], v, pseudokey=key, flow=flow)
            elif v_is_h_aux(u) and v_is_h_aux(v):
                pass
            else:
                self.clean_flow.add_edge(u, v, pseudokey=key, flow=flow)

    def clean_network_flow(self):
        """
        Compresses multiple and reverse edges (which represent the same data) that were formed as a result of the aux h structures.
        Also rebuilds the flow dict to use keys (which are necessary because this is a multigraph)
        """
        v_f_map = {}
        f_f_map = {}
        for u, v, k in self.clean_flow.edges:
            data = self.clean_flow[u][v][k]
            if v_is_structural(u) and v_is_face(v):
                key = (u, v, data['pseudokey'])
                if key not in v_f_map:
                    v_f_map[key] = 0
                v_f_map[key] += data['flow'] + 1  # this paper removes lower bound, so each flow for this type is 1 less
            elif v_is_face(u) and v_is_structural(v):
                key = (v, u, data['pseudokey'])
                if key not in v_f_map:
                    v_f_map[key] = 0
                v_f_map[key] -= data['flow']  # reversed edge, so subtract
            elif v_is_face(u) and v_is_face(v):
                edge = data['pseudokey']
                face_edges = set(self.dcel.faces[u].surround_half_edges())
                if self.dcel.half_edges[edge] in face_edges:
                    key = (u, v, edge)
                else:
                    key = (u, v, edge[::-1])
                if key not in f_f_map:
                    f_f_map[key] = 0
                f_f_map[key] += data['flow']

        self.clean_flow.clear()
        for (u, v, key), flow in v_f_map.items():
            self.clean_flow.add_edge(u, v, key=key, flow=flow)
        for (u, v, key), flow in f_f_map.items():
            self.clean_flow.add_edge(u, v, key=key, flow=flow)

        self.flow_dict = {}
        for u, v, key in self.clean_flow.edges:
            data = self.clean_flow[u][v][key]
            if u not in self.flow_dict:
                self.flow_dict[u] = {}
            if v not in self.flow_dict[u]:
                self.flow_dict[u][v] = {}
            self.flow_dict[u][v][key] = data['flow']
