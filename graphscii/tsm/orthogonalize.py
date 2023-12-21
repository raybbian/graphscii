import networkx as nx
import math

from tsm.planarize import Planarize
from tsm.utils import *


class Orthogonalize:
    def __init__(self, planarize: Planarize):
        self.G = planarize.G.copy()
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

        if self.network_flow is None:
            self.network_flow = nx.DiGraph()

        self.network_flow.add_nodes_from(["source", "sink"])
        self.network_flow.add_nodes_from(self.G.nodes())
        self.network_flow.add_nodes_from([face_id for face_id in self.dcel.faces])

        c = 6 * self.G.number_of_nodes()
        for v in self.G.nodes():
            if self.G.degree[v] <= 3:
                # type a arcs
                self.network_flow.add_edge("source", v, cost=0, capacity=4 - self.G.degree[v])
            elif self.G.degree[v] >= 5:
                # type f arcs
                self.network_flow.add_edge(v, "sink", cost=0, capacity=self.G.degree[v] - 4)

            e_list = [e.id for e in self.dcel.vertices[v].surround_half_edges()]
            f_list = [e.inc.id for e in self.dcel.vertices[v].surround_half_edges()]
            k = len(e_list)

            for i in range(k):
                next_i = (i + 1) % k
                prev_i = (i - 1) % k
                # type h1, edge stores the edge this face to face edge is going across, destination stores the face it goes to
                self.network_flow.add_edge(f_list[i], (f'h_aux_{v}_edge_r', i), cost=2 * c + 1, capacity=1,
                                           edge=e_list[i], destination=f_list[prev_i])
                self.network_flow.add_edge(f_list[i], (f'h_aux_{v}_edge_l', next_i), cost=2 * c + 1, capacity=1,
                                           edge=e_list[next_i], destination=f_list[next_i])
                # type h2, the original face to vertex reverse edges, stores l_edge and r_edge and what is supposed to be u
                self.network_flow.add_edge((f'h_aux_{v}_face', i), v, cost=0, capacity=1, l_edge=e_list[next_i][::-1],
                                           r_edge=e_list[i], face=f_list[i])
                # type h3
                self.network_flow.add_edge((f'h_aux_{v}_edge_l', i), (f'h_aux_{v}_face', i), cost=0, capacity=1)
                self.network_flow.add_edge((f'h_aux_{v}_edge_r', next_i), (f'h_aux_{v}_face', i), cost=0, capacity=1)
                # type h4
                self.network_flow.add_edge((f'h_aux_{v}_edge_l', i), (f'h_aux_{v}_edge_r', i), cost=-c, capacity=1)
                self.network_flow.add_edge((f'h_aux_{v}_edge_r', i), (f'h_aux_{v}_edge_l', i), cost=-c, capacity=1)

        for i, face in enumerate(self.dcel.faces.values()):
            face_edges = [e.id for e in face.surround_half_edges()]
            face_len = len(face_edges)

            if face_len <= 3 and i != 0:
                # type b arcs
                self.network_flow.add_edge("source", face.id, cost=0, capacity=4 - face_len)
            elif i == 0:
                # type c arc
                self.network_flow.add_edge(face.id, "sink", cost=0, capacity=face_len + 4)
            elif face_len >= 5:
                # type c arc
                self.network_flow.add_edge(face.id, "sink", cost=0, capacity=face_len - 4)

            for j, edge in enumerate(face_edges):
                n_edge = face_edges[(j + 1) % face_len]
                # create two edges here instead of one just in case of cut vertex like node,
                # where it is incident to the same face more than once (such that flow is simple)
                # type d arcs here, this one stores the l_edge and r_edge of the v->f arc
                self.network_flow.add_edge(edge[1], ('vertex_face_dummy', edge), cost=0, capacity=math.inf,
                                           l_edge=edge, r_edge=n_edge, face=face.id)
                self.network_flow.add_edge(('vertex_face_dummy', edge), face.id, cost=0, capacity=math.inf)

    def solve_network_flow(self):
        self.flow_dict = nx.max_flow_min_cost(self.network_flow, "source", "sink", "capacity", "cost")

    def strip_h_structures(self):
        """
        Strip the H structures as described in the paper.
        """
        if self.clean_flow is None:
            self.clean_flow = nx.MultiDiGraph()

        for v in self.network_flow.nodes():
            if v_is_h_aux(v):
                continue
            self.clean_flow.add_node(v)

        for u, v, data in self.network_flow.edges(data=True):
            flow = self.flow_dict[u][v]

            if v_is_face(u) and v_is_h_aux(v):
                self.clean_flow.add_edge(u, data['destination'], edge=data['edge'], flow=flow)
            elif v_is_h_aux(u) and v_is_structural(v):
                self.clean_flow.add_edge(data['face'], v, l_edge=data['l_edge'], r_edge=data['r_edge'], flow=flow)
            elif v_is_structural(u) and v_is_face_dummy(v):
                self.clean_flow.add_edge(u, data['face'], l_edge=data['l_edge'], r_edge=data['r_edge'], flow=flow)

    def clean_network_flow(self):
        """
        Compresses multiple and reverse edges (which represent the same data) that were formed as a result of the aux h structures.
        Also rebuilds the flow dict to use keys (which are necessary because this is a multigraph)
        """
        v_f_map = {}
        f_f_map = {}
        for u, v, data in self.clean_flow.edges(data=True):
            if v_is_structural(u) and v_is_face(v):
                key = (u, v, data['l_edge'], data['r_edge'])
                if key not in v_f_map:
                    v_f_map[key] = 0
                v_f_map[key] += data['flow'] + 1  # this paper removes lower bound, so each flow for this type is 1 less
            elif v_is_face(u) and v_is_structural(v):
                key = (v, u, data['l_edge'], data['r_edge'])
                if key not in v_f_map:
                    v_f_map[key] = 0
                v_f_map[key] -= data['flow']  # reversed edge, so subtract
            elif v_is_face(u) and v_is_face(v):
                if data['edge'] in self.dcel.faces[u].surround_half_edges():
                    key = (u, v, data['edge'])
                    if key not in f_f_map:
                        f_f_map[key] = 0
                    f_f_map[key] += data['flow']
                else:
                    key = (u, v, data['edge'][::-1])
                    if key not in f_f_map:
                        f_f_map[key] = 0
                    f_f_map[key] += data['flow']

        self.clean_flow.clear()
        for (u, v, l_edge, r_edge), flow in v_f_map.items():
            self.clean_flow.add_edge(u, v, l_edge=l_edge, r_edge=r_edge, flow=flow)
        for (u, v, edge), flow in f_f_map.items():
            self.clean_flow.add_edge(u, v, edge=edge, flow=flow)

        self.flow_dict = {}
        for u, v, data in self.clean_flow.edges(data=True):
            key = data['l_edge'] if 'l_edge' in data else data['edge']
            if u not in self.flow_dict:
                self.flow_dict[u] = {}
            if v not in self.flow_dict[u]:
                self.flow_dict[u][v] = {}
            self.flow_dict[u][v][key] = data['flow']
