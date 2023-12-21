import copy
import networkx as nx

from dcel import Dcel
from tsm.orthogonalize import Orthogonalize


class Compaction:
    def __init__(self, orthogonalize: Orthogonalize):
        self.G = orthogonalize.G
        self.dcel = orthogonalize.dcel

        self.flow_dict = copy.deepcopy(orthogonalize.flow_dict)
        self.bend_point_processor()
        self.vertex_point_processor()

        side_dict = self.face_side_processor()
        self.refine_faces(side_dict)

    def bend_point_processor(self):
        bends = {}
        for he in self.dcel.half_edges.values():
            lf, rf = he.twin.inc, he.inc
            flow = self.flow_dict[lf.id][rf.id][he.id]
            r_flow = self.flow_dict[rf.id][lf.id][he.twin.id]
            if flow > 0 and he.twin not in bends:
                bends[he] = ['r'] * flow + ['l'] * r_flow

        b_cnt = 0
        for he, bend_list in bends.items():
            # only looks at one side of half edges, other side is handled implicitly
            u, v = he.get_points()
            lf_id, rf_id = he.twin.inc.id, he.inc.id

            self.G.remove_edge(u, v)
            self.flow_dict[u][rf_id][u, ('bend', b_cnt)] = self.flow_dict[u][rf_id].pop((u, v))

            for i, bend in enumerate(bend_list):
                curr_node = ('bend', b_cnt)
                prev_node = ('bend', b_cnt - 1) if i > 0 else u
                next_node = ('bend', b_cnt + 1) if i < len(bend_list) - 1 else v
                self.G.add_edge(prev_node, curr_node)
                self.dcel.add_node_between(prev_node, curr_node, v)
                self.flow_dict.setdefault(curr_node, {}).setdefault(
                    lf_id, {})[curr_node, prev_node] = 1 if bend == 'r' else 3
                self.flow_dict.setdefault(curr_node, {}).setdefault(
                    rf_id, {})[curr_node, next_node] = 3 if bend == 'r' else 1  # twin edge, bends are reversed
                b_cnt += 1

            self.flow_dict[v][lf_id][v, ('bend', b_cnt - 1)] = self.flow_dict[v][lf_id].pop((v, u))
            self.G.add_edge(('bend', b_cnt - 1), v)


    def vertex_point_processor(self):
        """
        For every vertex, need to determine its side length, and assign it a square of vertices
        """
        side_len = 0
        for v in self.G.nodes:
            # find longest sequence of 0s -> that's how long a side has to be
            # because it is circular, but cannot contain all zeroes, just loop over array twice
            flow_in_list = [self.flow_dict[v][edge.inc.id][edge.id] for edge in self.dcel.vertices[v].surround_half_edges()]
            cnt = 0
            for flow_in_val in flow_in_list + flow_in_list:
                if flow_in_val == 0:
                    cnt += 1
                    side_len = max(side_len, cnt)
                else:
                    cnt = 0

        # need to make square out of 8 * side_len vertices, and assign each edge to the appropriate one

    def face_side_processor(self):
        side_dict = {}

        def set_side(init_he, side):
            for he in init_he.traverse():
                side_dict[he] = side
                angle = self.flow_dict[he.succ.ori.id][he.inc.id][he.succ.id]
                # angle to next edge
                if angle == 1:
                    side = (side + 1) % 4
                elif angle == 3:
                    side = (side + 3) % 4
                elif angle == 4 or angle == 0:
                    # 4 is single edge, 0 is shared side
                    side = (side + 2) % 4

            for he in init_he.traverse():
                if he.twin not in side_dict:
                    set_side(he.twin, (side_dict[he] + 2) % 4)

        set_side(self.dcel.ext_face.inc, 0)
        return side_dict

    def refine_faces(self, side_dict):
        def find_front(init_he, target):  # first
            cnt = 0
            for he in init_he.traverse():
                side, next_side = side_dict[he], side_dict[he.succ]
                if side == next_side:  # go straight
                    pass
                elif (side + 1) % 4 == next_side:  # go right
                    cnt += 1
                elif (side + 2) % 4 == next_side:  # go back
                    cnt -= 2
                else:  # go left
                    cnt -= 1
                if cnt == target:
                    return he.succ
            raise Exception(f"can't find front edge of {init_he}")

        def refine_internal(face):
            """Insert only one edge to make face more rect"""
            for he in face.surround_half_edges():
                side, next_side = side_dict[he], side_dict[he.succ]
                if side != next_side and (side + 1) % 4 != next_side:
                    front_he = find_front(he, 1)
                    extend_node_id = he.twin.ori.id

                    l, r = front_he.ori.id, front_he.twin.ori.id
                    he_l2r = self.dcel.half_edges[l, r]
                    dummy_node_id = ("dummy", extend_node_id)
                    self.G.remove_edge(l, r)
                    self.G.add_edge(l, dummy_node_id)
                    self.G.add_edge(dummy_node_id, r)

                    face = self.dcel.half_edges[l, r].inc
                    self.dcel.add_node_between(l, dummy_node_id, r)
                    he_l2d = self.dcel.half_edges[l, dummy_node_id]
                    he_d2r = self.dcel.half_edges[dummy_node_id, r]
                    side_dict[he_l2d] = side_dict[he_l2r]
                    side_dict[he_l2d.twin] = (side_dict[he_l2r] + 2) % 4
                    side_dict[he_d2r] = side_dict[he_l2r]
                    side_dict[he_d2r.twin] = (side_dict[he_l2r] + 2) % 4
                    side_dict.pop(he_l2r)
                    side_dict.pop(he_l2r.twin)

                    self.G.add_edge(dummy_node_id, extend_node_id)
                    self.dcel.connect(face, extend_node_id, dummy_node_id, side_dict, side_dict[he])

                    he_e2d = self.dcel.half_edges[extend_node_id, dummy_node_id]
                    lf, rf = he_e2d.twin.inc, he_e2d.inc
                    side_dict[he_e2d] = side_dict[he]
                    side_dict[he_e2d.twin] = (side_dict[he] + 2) % 4

                    refine_internal(lf)
                    refine_internal(rf)
                    break

        def build_border(G, dcel, side_dict):
            """Create border dcel"""
            border_nodes = [("dummy", -i) for i in range(1, 5)]
            border_edges = [(border_nodes[i], border_nodes[(i + 1) % 4]) for i in range(4)]
            border_G = nx.Graph(border_edges)
            border_side_dict = {}
            is_planar, border_embedding = nx.check_planarity(border_G)
            border_dcel = Dcel(border_G, border_embedding)
            ext_face = border_dcel.half_edges[(border_nodes[0], border_nodes[1])].twin.inc
            border_dcel.ext_face = ext_face
            ext_face.is_external = True

            for face in list(border_dcel.faces.values()):
                if not face.is_external:
                    for i, he in enumerate(face.surround_half_edges()):
                        he.inc = self.dcel.ext_face
                        side_dict[he] = i  # assign side
                        side_dict[he.twin] = (i + 2) % 4
                        border_side_dict[i] = he
                    border_dcel.faces.pop(face.id)
                    border_dcel.faces[self.dcel.ext_face.id] = self.dcel.ext_face
                else:
                    # rename border_dcel.ext_face's name
                    border_dcel.faces.pop(face.id)
                    face.id = ("face", -1)
                    border_dcel.faces[face.id] = face
            G.add_edges_from(border_edges)

            # merge border dcel into self.dcel
            dcel.vertices.update(border_dcel.vertices)
            dcel.half_edges.update(border_dcel.half_edges)
            dcel.faces.update(border_dcel.faces)
            dcel.ext_face.is_external = False
            dcel.ext_face = border_dcel.ext_face
            return border_side_dict

        ori_ext_face = self.dcel.ext_face
        border_side_dict = build_border(self.G, self.dcel, side_dict)

        for he in ori_ext_face.surround_half_edges():
            extend_node_id = he.succ.ori.id
            side, next_side = side_dict[he], side_dict[he.succ]
            if next_side != side and next_side != (side + 1) % 4:
                if len(self.G[extend_node_id]) <= 2:
                    front_he = border_side_dict[(side + 1) % 4]
                    dummy_node_id = ("dummy", extend_node_id)
                    l, r = front_he.ori.id, front_he.twin.ori.id
                    he_l2r = self.dcel.half_edges[l, r]
                    # process G
                    self.G.remove_edge(l, r)
                    self.G.add_edge(l, dummy_node_id)
                    self.G.add_edge(dummy_node_id, r)
                    self.G.add_edge(dummy_node_id, extend_node_id)

                    # # process dcel

                    self.dcel.add_node_between(l, dummy_node_id, r)
                    self.dcel.connect_diff(ori_ext_face, extend_node_id, dummy_node_id)

                    he_e2d = self.dcel.half_edges[extend_node_id, dummy_node_id]
                    he_l2d = self.dcel.half_edges[l, dummy_node_id]
                    he_d2r = self.dcel.half_edges[dummy_node_id, r]
                    # process halfedge_side
                    side_dict[he_l2d] = side_dict[he_l2r]
                    side_dict[he_l2d.twin] = (side_dict[he_l2r] + 2) % 4
                    side_dict[he_d2r] = side_dict[he_l2r]
                    side_dict[he_d2r.twin] = (side_dict[he_l2r] + 2) % 4

                    side_dict[he_e2d] = side_dict[he]
                    side_dict[he_e2d.twin] = (side_dict[he] + 2) % 4
                    side_dict.pop(he_l2r)
                    side_dict.pop(he_l2r.twin)
                    break
        else:
            raise Exception("not connected")

        for face in list(self.dcel.faces.values()):
            if face.id != ("face", -1):
                refine_internal(face)
