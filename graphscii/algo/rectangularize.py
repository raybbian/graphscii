import collections
import itertools
import sys

import networkx as nx

from graphscii.dcel import Dcel
from .orthogonalize import Orthogonalize
from .utils import v_is_bend, v_is_vertex

# TODO: write without recursion
sys.setrecursionlimit(100000)


class Rectangularize:
    def __init__(self, orthogonalize: Orthogonalize):
        self.G = orthogonalize.G
        self.dcel = orthogonalize.dcel
        self.angle_dict = orthogonalize.angle_dict
        self.bend_dict = orthogonalize.bend_dict
        self.rb_cnt = 0
        self.rect_edges = set()

        self.bend_point_processor()
        self.ori_ext_edge = self.dcel.ext_face.inc
        self.side_dict = self.face_side_processor()

        self.ori_edges = [edge for edge in self.G.edges]  # store edges before refine face
        self.triangle_faces = set()
        self.triangle_edges = set()
        self.bend_offsets = {}
        self.refine_faces()

    def bend_point_processor(self):
        b_cnt = 0
        ori_edges = list(self.G.edges())
        for edge in ori_edges:
            he = self.dcel.half_edges[edge]
            bend_list = self.bend_dict[he.id]
            if len(bend_list) == 0:
                continue
            # only looks at one side of half edges, other side is handled implicitly
            u, v = he.get_points()
            lf_id, rf_id = he.twin.inc.id, he.inc.id

            self.G.remove_edge(u, v)
            self.angle_dict[u][rf_id][u, ('bend', b_cnt)] = self.angle_dict[u][rf_id].pop((u, v))

            for i, bend in enumerate(bend_list):
                curr_node = ('bend', b_cnt)
                prev_node = ('bend', b_cnt - 1) if i > 0 else u
                next_node = ('bend', b_cnt + 1) if i < len(bend_list) - 1 else v
                self.G.add_edge(prev_node, curr_node)
                self.dcel.add_node_between(prev_node, curr_node, v)
                self.angle_dict.setdefault(curr_node, {}).setdefault(
                    lf_id, {})[curr_node, prev_node] = 3 if bend == 'r' else 1  # twin edge
                self.angle_dict.setdefault(curr_node, {}).setdefault(
                    rf_id, {})[curr_node, next_node] = 1 if bend == 'r' else 3
                b_cnt += 1

            self.angle_dict[v][lf_id][v, ('bend', b_cnt - 1)] = self.angle_dict[v][lf_id].pop((v, u))
            self.G.add_edge(('bend', b_cnt - 1), v)

    def face_side_processor(self):
        side_dict = {}

        def set_side(init_he, side):
            for he in init_he.traverse():
                side_dict[he] = side
                angle = self.angle_dict[he.succ.ori.id][he.inc.id][he.succ.id]
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

    def refine_faces(self):
        def find_front(init_he, target):  # first
            cnt = 0
            for he in init_he.traverse():
                side, next_side = self.side_dict[he], self.side_dict[he.succ]
                if side == next_side:  # go straight
                    pass
                elif (side + 1) % 4 == next_side:  # go right
                    cnt += 1
                elif (side + 2) % 4 == next_side:  # turn around edge
                    cnt -= 2
                else:  # go left
                    cnt -= 1
                if cnt == target and he.succ not in self.triangle_edges:
                    return he.succ
            raise Exception(f"can't find front edge of {init_he}")

        def refine_zero(vertex):
            side_list = collections.deque(
                [(he, self.side_dict[he]) for he in self.dcel.vertices[vertex].surround_half_edges()])
            count = 0
            while side_list[0][1] == side_list[-1][1] and len(
                    side_list) > 1:  # ensure that a side isn't chopped by the array
                if count > len(side_list):
                    raise Exception("All edges connected here leave the same side...")
                side_list.append(side_list.popleft())
                count += 1

            sides = {i: [] for i in range(4)}
            for he, side in side_list:
                next_side = self.side_dict[he.succ] if v_is_bend(he.twin.ori.id) else side
                turn_label = 'r' if (side + 1) % 4 == next_side else 'l' if (side + 3) % 4 == next_side else 'm'
                sides[side].append((he, turn_label))

            for side in sides:
                # must manually merge these two edges together
                # add vertex to subdivide the edge closer to the middle,
                # connect the bend from the outer edge to the new vertex
                # middle is the first m, or first r if m does not exist
                # start from the ones in the middle, then move outward
                dir_list = [el[1] for el in sides[side]]
                mid_ind = dir_list.index('m') if 'm' in dir_list else dir_list.index('r') if 'r' in dir_list else len(
                    dir_list) - 1

                # check if one before mid is left bend that goes to vertex, of which the next edge is also a 0 degree edge, then must switch
                if mid_ind > 0 and sides[side][mid_ind - 1][1] == 'l' and sides[side][mid_ind][1] == 'r':
                    cur_edge_in = sides[side][mid_ind - 1][0].succ
                    next_edge_out = sides[side][mid_ind - 1][0].succ.succ
                    if self.side_dict[cur_edge_in] == (self.side_dict[next_edge_out] + 2) % 4:
                        # interesting case here... prefer subdivide left bend edge and merge right into left
                        r_cur_edge_in = sides[side][mid_ind][0].succ
                        r_next_edge_out = sides[side][mid_ind][0].succ.succ
                        # assert self.side_dict[r_cur_edge_in] != (self.side_dict[r_next_edge_out] + 2) % 4
                        # not sure if this assert is required, need access to german phd :(
                        mid_ind = mid_ind - 1

                for i, (he, dir_label) in enumerate(sides[side]):
                    _, v = he.get_points()
                    assert (v_is_bend(v) or dir_label == 'm')
                    cur_delta = self.bend_offsets.get(v, (0, 0))
                    match side:
                        case 0:
                            self.bend_offsets[v] = cur_delta[0] + (i - mid_ind) * 2, cur_delta[1]
                        case 1:
                            self.bend_offsets[v] = cur_delta[0], cur_delta[1] + (
                                    mid_ind - i)  # if side == 0, then offsets go up and down
                        case 2:
                            self.bend_offsets[v] = cur_delta[0] + (mid_ind - i) * 2, cur_delta[1]
                        case 3:
                            self.bend_offsets[v] = cur_delta[0], cur_delta[1] + (i - mid_ind)

                def operate_pairwise(side_half):
                    for (idx, b), (_, a), in itertools.pairwise(side_half):
                        # new edges start at the same spot, should have same face inc, get updated edge
                        flipped = False
                        if a[1] == 'r':
                            # this one, we do the opposide direction
                            flipped = True

                        # following code merges a's bend into subdivision of b
                        b_he = b[0]
                        b_u, b_v = b_he.get_points()
                        a_he = a[0]
                        a_u, a_v = a_he.get_points()
                        dummy_node = (
                            'rect_dummy', self.rb_cnt)  # a_v is the bend, and we are extending it to this dummy node
                        self.rb_cnt += 1

                        # print('subdividing', b_he, 'going to', b[1], 'attaching', a_v, 'on', a_he, 'to', dummy_node)

                        # for the subdivision, update graph, dcel, and side_dict
                        he_bu2bv = self.dcel.half_edges[b_u, b_v]
                        self.G.add_node(dummy_node)
                        self.G.remove_edge(b_u, b_v)
                        self.G.add_edge(b_u, dummy_node)
                        self.G.add_edge(dummy_node, b_v)
                        self.dcel.add_node_between(b_u, dummy_node, b_v)

                        he_bu2bm = self.dcel.half_edges[b_u, dummy_node]
                        he_bm2bv = self.dcel.half_edges[dummy_node, b_v]
                        self.side_dict[he_bu2bm] = self.side_dict[he_bu2bv]
                        self.side_dict[he_bu2bm.twin] = (self.side_dict[he_bu2bv] + 2) % 4
                        self.side_dict[he_bm2bv] = self.side_dict[he_bu2bv]
                        self.side_dict[he_bm2bv.twin] = (self.side_dict[he_bu2bv] + 2) % 4
                        self.side_dict.pop(he_bu2bv)
                        self.side_dict.pop(he_bu2bv.twin)

                        # add the edge, and connect
                        face = he_bu2bv.twin.inc if not flipped else he_bu2bv.inc  # right side twin's face is in the middle of these two
                        self.G.add_edge(a_v, dummy_node)
                        self.rect_edges.add((a_v, dummy_node))
                        dummy_edge_side = self.side_dict[a_he.succ.twin]

                        # the way we call connect changes which one the external face is if face is the external face
                        # this is why we choose
                        if flipped:
                            self.dcel.connect_with_face(face, a_v, dummy_node, self.side_dict, dummy_edge_side)
                        else:
                            self.dcel.connect_with_face(face, dummy_node, a_v, self.side_dict,
                                                        (dummy_edge_side + 2) % 4)

                        he_av2dummy = self.dcel.half_edges[a_v, dummy_node]
                        self.side_dict[he_av2dummy] = dummy_edge_side
                        self.side_dict[he_av2dummy.twin] = (dummy_edge_side + 2) % 4
                        self.triangle_faces.add(he_av2dummy.inc if not flipped else he_av2dummy.twin.inc)
                        self.triangle_edges.add(he_av2dummy)
                        self.triangle_edges.add(he_av2dummy.twin)

                        sides[side][idx] = (he_bu2bm, b[1])
                        assert he_bu2bv not in self.triangle_edges and he_bu2bv.twin not in self.triangle_edges

                # we operate from the middle edge outward, such edge updates are reflected
                # pt2 is established after pt1 is finished because the middle edge, in both, may have changed
                pt1 = list(reversed(list(enumerate(sides[side]))[:mid_ind + 1]))
                operate_pairwise(pt1)
                pt2 = list(enumerate(sides[side]))[mid_ind:]
                operate_pairwise(pt2)

        def refine_internal(face):
            """Insert only one edge to make face more rect"""
            assert face not in self.triangle_faces
            for he in face.surround_half_edges():
                side, next_side = self.side_dict[he], self.side_dict[he.succ]
                # if not go straight, right turn, or 0 degree
                if side != next_side and (side + 1) % 4 != next_side:
                    front_he = find_front(he, 1)
                    extend_node_id = he.twin.ori.id

                    l, r = front_he.ori.id, front_he.twin.ori.id
                    he_l2r = self.dcel.half_edges[l, r]
                    dummy_node_id = ("rect_dummy", self.rb_cnt)
                    self.rb_cnt += 1
                    self.G.remove_edge(l, r)
                    self.G.add_edge(l, dummy_node_id)
                    self.G.add_edge(dummy_node_id, r)

                    face = self.dcel.half_edges[l, r].inc
                    self.dcel.add_node_between(l, dummy_node_id, r)
                    he_l2d = self.dcel.half_edges[l, dummy_node_id]
                    he_d2r = self.dcel.half_edges[dummy_node_id, r]
                    self.side_dict[he_l2d] = self.side_dict[he_l2r]
                    self.side_dict[he_l2d.twin] = (self.side_dict[he_l2r] + 2) % 4
                    self.side_dict[he_d2r] = self.side_dict[he_l2r]
                    self.side_dict[he_d2r.twin] = (self.side_dict[he_l2r] + 2) % 4
                    self.side_dict.pop(he_l2r)
                    self.side_dict.pop(he_l2r.twin)

                    self.G.add_edge(dummy_node_id, extend_node_id)
                    self.rect_edges.add((dummy_node_id, extend_node_id))
                    self.dcel.connect_with_face(face, extend_node_id, dummy_node_id, self.side_dict, self.side_dict[he])

                    he_e2d = self.dcel.half_edges[extend_node_id, dummy_node_id]
                    lf, rf = he_e2d.twin.inc, he_e2d.inc
                    self.side_dict[he_e2d] = self.side_dict[he]
                    self.side_dict[he_e2d.twin] = (self.side_dict[he] + 2) % 4

                    refine_internal(lf)
                    refine_internal(rf)
                    break

        def build_border(ori_ext_face):
            """Create border dcel"""
            border_nodes = [("rect_dummy", -i) for i in range(1, 5)]
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
                        self.side_dict[he] = i  # assign side
                        self.side_dict[he.twin] = (i + 2) % 4
                        border_side_dict[i] = he
                    border_dcel.faces.pop(face.id)
                    border_dcel.faces[ori_ext_face.id] = ori_ext_face
                else:
                    # rename border_dcel.ext_face's name
                    border_dcel.faces.pop(face.id)
                    face.id = ("face", -1)
                    border_dcel.faces[face.id] = face
            self.G.add_edges_from(border_edges)

            # merge border dcel into self.dcel
            self.dcel.vertices.update(border_dcel.vertices)
            self.dcel.half_edges.update(border_dcel.half_edges)
            self.dcel.faces.update(border_dcel.faces)
            self.dcel.ext_face.is_external = False
            self.dcel.ext_face = border_dcel.ext_face
            return border_side_dict

        ori_nodes = [vertex for vertex in self.G.nodes() if v_is_vertex(vertex)]
        for node in ori_nodes:
            refine_zero(node)

        ori_ext_face = self.dcel.ext_face

        border_side_dict = build_border(ori_ext_face)
        for he in ori_ext_face.surround_half_edges():
            extend_node_id = he.succ.ori.id
            side, next_side = self.side_dict[he], self.side_dict[he.succ]
            if next_side != side and next_side != (side + 1) % 4:
                # print(f'want to push {he} to border')
                # print(f'extend node {extend_node_id}, surround edges {[(edge, edge.inc) for edge in he.succ.ori.surround_half_edges()]}')
                if len(self.G[extend_node_id]) <= 2:
                    front_he = border_side_dict[(side + 1) % 4]
                    dummy_node_id = ("rect_dummy", self.rb_cnt)
                    self.rb_cnt += 1
                    l, r = front_he.ori.id, front_he.twin.ori.id
                    he_l2r = self.dcel.half_edges[l, r]
                    # process G
                    self.G.remove_edge(l, r)
                    self.G.add_edge(l, dummy_node_id)
                    self.G.add_edge(dummy_node_id, r)
                    self.G.add_edge(dummy_node_id, extend_node_id)
                    self.rect_edges.add((dummy_node_id, extend_node_id))

                    # # process dcel

                    self.dcel.add_node_between(l, dummy_node_id, r)
                    self.dcel.connect_diff(ori_ext_face, extend_node_id, dummy_node_id)

                    he_e2d = self.dcel.half_edges[extend_node_id, dummy_node_id]
                    he_l2d = self.dcel.half_edges[l, dummy_node_id]
                    he_d2r = self.dcel.half_edges[dummy_node_id, r]
                    # process halfedge_side
                    self.side_dict[he_l2d] = self.side_dict[he_l2r]
                    self.side_dict[he_l2d.twin] = (self.side_dict[he_l2r] + 2) % 4
                    self.side_dict[he_d2r] = self.side_dict[he_l2r]
                    self.side_dict[he_d2r.twin] = (self.side_dict[he_l2r] + 2) % 4

                    self.side_dict[he_e2d] = self.side_dict[he]
                    self.side_dict[he_e2d.twin] = (self.side_dict[he] + 2) % 4
                    self.side_dict.pop(he_l2r)
                    self.side_dict.pop(he_l2r.twin)
                    break
        else:
            raise Exception("not connected")

        for face in list(self.dcel.faces.values()):
            if face.id != ("face", -1) and face not in self.triangle_faces:
                refine_internal(face)
