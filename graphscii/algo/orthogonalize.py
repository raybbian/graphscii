import collections

import networkx as nx
import pulp

from .planarize import Planarize
from .utils import v_is_struct_dummy, v_is_face, v_is_structural, v_is_h_aux


class Orthogonalize:
    def __init__(self, planarize: Planarize):
        self.G = planarize.G
        self.dcel = planarize.dcel
        self.network_flow = None
        self.angle_dict = None
        self.bend_dict = None

        self.build_network_flow()
        self.solve_network_flow()

    def build_network_flow(self):
        assert nx.is_planar(self.G)

        self.network_flow = nx.MultiDiGraph()

        for v in self.G.nodes():
            self.network_flow.add_node(v, demand=self.G.degree[v] - 4)
            if v_is_struct_dummy(v):
                continue
            surround_faces = list(self.dcel.vertices[v].surround_faces())
            for i, face in enumerate(surround_faces):
                helper_face = (f"h_aux_face", (v, face.id, i))
                self.network_flow.add_node(helper_face, demand=0)

        for face in self.dcel.faces.values():
            face_len = len(list(face.surround_half_edges()))
            if face.is_external:
                self.network_flow.add_node(face.id, demand=face_len + 4)
            else:
                self.network_flow.add_node(face.id, demand=face_len - 4)

        for face in self.dcel.faces.values():
            for edge in face.surround_half_edges():
                o_face = edge.twin.inc
                self.network_flow.add_edge(edge.id[0], face.id, cost=0, capacity=3, key=edge.id)
                self.network_flow.add_edge(face.id, o_face.id, cost=1, capacity=2 ** 32, key=edge.id)

        for v in self.G.nodes():
            if v_is_struct_dummy(v):
                continue
            surround_edges = list(self.dcel.vertices[v].surround_half_edges())
            surround_faces = [he.inc for he in surround_edges]  # identical index edge is one to the left
            for i, face in enumerate(surround_faces):
                prev_h_face = (
                f"h_aux_face", (v, surround_faces[(i - 1) % len(surround_faces)].id, (i - 1) % len(surround_faces)))
                prev_edge = surround_edges[i]
                helper_face = (f"h_aux_face", (v, face.id, i))
                next_h_face = (
                f"h_aux_face", (v, surround_faces[(i + 1) % len(surround_faces)].id, (i + 1) % len(surround_faces)))
                next_edge = surround_edges[(i + 1) % len(surround_edges)]
                self.network_flow.add_edge(helper_face, v, cost=0, capacity=1, key=prev_edge.id)
                self.network_flow.add_edge(face.id, prev_h_face, cost=1, capacity=1, key=prev_edge.id)
                self.network_flow.add_edge(face.id, next_h_face, cost=1, capacity=1, key=next_edge.twin.id)

    def solve_network_flow(self):
        # flow_cost, self.flow_dict = nx.capacity_scaling(self.network_flow, "demand", "capacity", "cost")
        lp_dict = {}
        problem = pulp.LpProblem("KandinskyFlow", pulp.LpMinimize)
        for u, v, key, data in self.network_flow.edges(keys=True, data=True):
            var_name = f"flow_{u}_to_{v}_for_{key}"
            if u not in lp_dict:
                lp_dict[u] = {}
            if v not in lp_dict[u]:
                lp_dict[u][v] = {}
            lp_dict[u][v][key] = pulp.LpVariable(name=var_name, lowBound=0, upBound=data['capacity'],
                                                 cat=pulp.LpInteger)  # try integer?

        for node, data in self.network_flow.nodes(data=True):
            # inflow = outflow + deman
            inflow = pulp.lpSum(lp_dict[u][v][key] for u, v, key in self.network_flow.in_edges(node, keys=True))
            outflow = pulp.lpSum(lp_dict[u][v][key] for u, v, key in self.network_flow.out_edges(node, keys=True))
            demand = data['demand']
            problem += (inflow - outflow == demand)

        # define bundles
        for node in self.G.nodes():
            if v_is_struct_dummy(node):
                continue
            # for each face1 to helper_v_face2
            # and face2 to helper_v_face1
            # the sum of these two flow values <= 1
            surround_edges = list(self.dcel.vertices[node].surround_half_edges())
            surround_faces = [he.inc for he in surround_edges]  # identical index edge is one to the left
            for i in range(len(surround_faces)):
                cur_face = surround_faces[i].id
                helper_face = (f"h_aux_face", (node, cur_face, i))
                next_face = surround_faces[(i + 1) % len(surround_faces)].id
                n_helper_face = (f"h_aux_face", (node, next_face, (i + 1) % len(surround_faces)))
                key = surround_edges[(i + 1) % len(surround_edges)].twin

                problem += (lp_dict[cur_face][n_helper_face][key.id] + lp_dict[next_face][helper_face][
                    key.twin.id] <= 1)

        problem += pulp.lpSum(
            lp_dict[u][v][key] * data['cost'] for u, v, key, data in self.network_flow.edges(keys=True, data=True))

        solver = pulp.PULP_CBC_CMD(msg=False)
        problem.solve(solver)
        assert problem.status == 1

        self.build_flow_dict(lp_dict)

    def build_flow_dict(self, lp_dict):
        # can first merge face -> vertex and vertex -> face
        # for face to face, must be careful
        # need to determine the order, and which bend to do, maybe return a bend dict instead
        self.bend_dict = {e: collections.deque() for e in self.dcel.half_edges}
        for u in lp_dict:
            for v in lp_dict[u]:
                for key in lp_dict[u][v]:
                    if v_is_face(u) and v_is_face(v):
                        he = self.dcel.half_edges[key]
                        if int(lp_dict[u][v][key].varValue) > 0:
                            assert len(self.bend_dict[
                                           he.twin.id]) == 0  # should not have left and right bends over middle of edge
                            for i in range(int(lp_dict[u][v][key].varValue)):
                                self.bend_dict[he.id].append('r')
                                self.bend_dict[he.twin.id].append('l')

        self.angle_dict = {}  # stores angle before the edge
        for u in lp_dict:
            for v in lp_dict[u]:
                for key in lp_dict[u][v]:
                    if v_is_structural(u) and v_is_face(v):
                        if u not in self.angle_dict:
                            self.angle_dict[u] = {}
                        if v not in self.angle_dict[u]:
                            self.angle_dict[u][v] = {}
                        if key not in self.angle_dict[u][v]:
                            self.angle_dict[u][v][key] = 0
                        self.angle_dict[u][v][key] += int(lp_dict[u][v][key].varValue) + 1
                    elif v_is_h_aux(u) and v_is_structural(v):
                        ori_face = u[1][1]
                        if v not in self.angle_dict:
                            self.angle_dict[v] = {}
                        if ori_face not in self.angle_dict[v]:
                            self.angle_dict[v][ori_face] = {}
                        if key not in self.angle_dict[v][ori_face]:
                            self.angle_dict[v][ori_face][key] = 0
                        self.angle_dict[v][ori_face][key] -= int(lp_dict[u][v][key].varValue)
                    elif v_is_face(u) and v_is_h_aux(v):
                        # these bends should go towards the side of the vertex defined by v
                        # which direction should the bend go? all on right side of u
                        vertex = v[1][0]
                        he = self.dcel.half_edges[key]
                        if int(lp_dict[u][v][key].varValue) == 1:  # cap is one for these
                            ori, dest = he.get_points()
                            if dest == vertex:
                                # this is the next edge
                                self.bend_dict[he.id].append('r')
                                self.bend_dict[he.twin.id].appendleft('l')
                            else:
                                assert ori == vertex
                                self.bend_dict[he.id].appendleft('r')
                                self.bend_dict[he.twin.id].append('l')
