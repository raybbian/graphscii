from collections import defaultdict

import networkx as nx

from .rectangularize import Rectangularize


class Compaction:
    def __init__(self, rectangularize: Rectangularize, with_labels=False):
        self.G = rectangularize.G
        self.side_dict = rectangularize.side_dict
        self.dcel = rectangularize.dcel
        self.triangle_faces = rectangularize.triangle_faces
        self.triangle_edges = rectangularize.triangle_edges
        self.rect_edges = rectangularize.rect_edges
        self.bend_offsets = rectangularize.bend_offsets
        self.ori_edges = rectangularize.ori_edges

        if with_labels:
            max_label_w = max(len(str(label[1])) for label in self.G.nodes())
        else:
            max_label_w = 0

        self.v_w = max(max([abs(coord[0]) for _, coord in self.bend_offsets.items()]) + 1, max_label_w // 2 + 1)
        self.v_h = max([abs(coord[1]) for _, coord in self.bend_offsets.items()]) + 1
        self.e_w = 4
        self.e_h = 1

        self.length_dict = self.tidy_rectangle_compaction()
        self.pos = self.layout()
        self.apply_bend_offsets()

    def tidy_rectangle_compaction(self):
        def build_flow(target_side):
            flow = nx.MultiDiGraph()
            for he, side in self.side_dict.items():
                if side == target_side:
                    lf, rf = he.twin.inc, he.inc
                    # skip triangle faces
                    if he in self.triangle_edges or he.twin in self.triangle_edges:
                        continue
                    lf_id = lf.id
                    rf_id = rf.id if not rf.is_external else ('face', 'end')
                    # for each side with a vertex, add 2?
                    lb = (2 * self.v_w + self.e_w) if target_side % 2 == 1 else (2 * self.v_h + self.e_h)
                    flow.add_edge(lf_id, rf_id, key=he.id, lowerbound=lb, cost=1, capacity=2 ** 32)
            flow.add_edge(self.dcel.ext_face.id, ('face', 'end'), key='extend_edge', lowerbound=0, cost=0,
                          capacity=2 ** 32)
            for node in flow.nodes():
                flow.nodes[node]['demand'] = 0
            flow.nodes[self.dcel.ext_face.id]['demand'] = -2 ** 32
            flow.nodes[('face', 'end')]['demand'] = 2 ** 32
            return flow

        def min_cost_flow(flow):
            def get_demand(flow_dict, node):
                in_flow = sum(flow_dict[u][v][key] for u, v, key in flow.in_edges(node, keys=True))
                out_flow = sum(flow_dict[u][v][key] for u, v, key in flow.out_edges(node, keys=True))
                if in_flow == 0 and node != ('face', -1):
                    print('inflow 0', node)
                    print(
                        f"bad face:{[(he, he in self.triangle_edges or he.twin in self.triangle_edges, self.side_dict[he]) for he in self.dcel.faces[node].surround_half_edges()]}")
                    print(f"surrounded by:")
                    for face in list(self.dcel.faces[node].surround_faces()):
                        print(
                            f"face: {[(he, he in self.triangle_edges or he.twin in self.triangle_edges, self.side_dict[he]) for he in face.surround_half_edges()]}")
                    raise Exception(
                        "This should not happen, something went wrong during rectangularization. I think I know where this stems from, open a GH issue and I will get back to you.")
                if out_flow == 0 and node != ('face', 'end'):
                    print('outflow 0', node)
                    print(
                        f"bad face:{[(he, he in self.triangle_edges or he.twin in self.triangle_edges, self.side_dict[he]) for he in self.dcel.faces[node].surround_half_edges()]}")
                    print(f"surrounded by:")
                    for face in list(self.dcel.faces[node].surround_faces()):
                        print(
                            f"face: {[(he, he in self.triangle_edges or he.twin in self.triangle_edges, self.side_dict[he]) for he in face.surround_half_edges()]}")
                    raise Exception(
                        "this should not happen, something went wrong during rectangularization. I think I know where this stems from, open a GH issue and I will get back to you.")
                return in_flow - out_flow

            def split():
                base_dict = defaultdict(lambda: defaultdict(dict))
                new_mdg = nx.MultiDiGraph()

                for u, v, key in flow.edges:
                    lowerbound = flow[u][v][key]['lowerbound']
                    base_dict[u][v][key] = lowerbound
                    new_mdg.add_edge(u, v, key, capacity=flow[u][v][key]['capacity'] - lowerbound,
                                     weight=flow[u][v][key]['cost'], )
                for node in flow:
                    new_mdg.nodes[node]['demand'] = flow.nodes[node]['demand'] - get_demand(base_dict, node)
                return base_dict, new_mdg

            base_dict, new_mdg = split()
            flow_dict = nx.min_cost_flow(new_mdg)
            for u, v, key in flow.edges:
                flow_dict[u][v][key] += base_dict[u][v][key]

            return flow_dict

        hor_flow = build_flow(1)  # up -> bottom
        ver_flow = build_flow(0)  # left -> right

        hor_flow_dict = min_cost_flow(hor_flow)
        ver_flow_dict = min_cost_flow(ver_flow)

        halfedge_length = {}

        for he, side in self.side_dict.items():
            if side in (0, 1):
                rf = he.inc
                rf_id = ('face', 'end') if rf.is_external else rf.id
                lf_id = he.twin.inc.id

                if side == 0:
                    hv_flow_dict = ver_flow_dict
                else:
                    hv_flow_dict = hor_flow_dict

                length = hv_flow_dict[lf_id][rf_id][he.id] if he not in self.triangle_edges else 0
                halfedge_length[he] = length
                halfedge_length[he.twin] = length

        return halfedge_length

    def layout(self):
        """ return pos of self.G"""
        pos = {}

        def set_coord(init_he, x, y):
            for he in init_he.traverse():
                pos[he.ori.id] = (x, y)
                side = self.side_dict[he]
                length = self.length_dict[he]
                if side == 1:
                    x += length
                elif side == 3:
                    x -= length
                elif side == 0:
                    y += length
                else:
                    y -= length

            for he in init_he.traverse():
                for e in he.ori.surround_half_edges():
                    if e.twin.ori.id not in pos:
                        set_coord(e, *pos[e.ori.id])

        set_coord(self.dcel.ext_face.inc, 0, 0)
        return pos

    def apply_bend_offsets(self):
        for vertex in self.pos:
            delta = self.bend_offsets.get(vertex, (0, 0))
            self.pos[vertex] = self.pos[vertex][0] + delta[0], self.pos[vertex][1] + delta[1]
