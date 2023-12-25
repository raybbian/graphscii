import copy
import itertools

import networkx as nx
import collections

from dcel import Dcel
from dcel.face import Face
from tsm.orthogonalize import Orthogonalize
from tsm.utils import v_is_corner, v_is_bend, v_is_vertex, v_is_structural


class Rectangularize:
    def __init__(self, orthogonalize: Orthogonalize):
        self.G = orthogonalize.G
        self.dcel = orthogonalize.dcel
        self.angle_dict = orthogonalize.angle_dict
        self.bend_dict = orthogonalize.bend_dict
        self.port_cnt = -1

        self.bend_point_processor()
        self.ori_ext_edge = self.dcel.ext_face.inc
        self.side_dict = self.face_side_processor()

        for face in self.dcel.faces.values():
            print(face.id, face.is_external)
            for edge in face.surround_half_edges():
                print(edge, self.side_dict[edge])

        #self.vertex_point_processor()
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

    def vertex_point_processor(self):
        """
        For every vertex, need to determine its side length, and assign it a square of vertices. This is also where
        I could do processing for multiedges, to be reinserted back into the graph, maybe also loop dummies
        """

        def get_min_side_len():
            side_len = 0
            for v in self.G.nodes():
                if not v_is_vertex(v):
                    continue
                counter = collections.Counter(
                    [self.side_dict[he] for he in self.dcel.vertices[v].surround_half_edges()])
                side_len = max(side_len, counter.most_common(1)[0][1])
            return side_len

        side_len = get_min_side_len()
        self.port_cnt = 2 * side_len + 1  # this is how many "ports" there are on each side

        def get_port_node(v, side, number):
            return 'side', (v, side, number)

        def get_mirror_port(port_node, other_v):
            type = port_node[0]
            side = port_node[1][1]
            number = port_node[1][2]
            if type == 'side':
                opp_side = (side + 2) % 4
                opp_number = (self.port_cnt - number - 1)
                return 'side', (other_v, opp_side, opp_number)
            elif type == 'corner':
                raise Exception("not supported for corners")

        def get_corner_node(v, side_at_left_of):
            return 'corner', (v, side_at_left_of)

        def get_vertex_of_port(port_node):
            return port_node[1][0]

        def get_port_list(init_port):
            start_node = init_port
            yield start_node
            cur_node = get_adjacent_port_nodes(start_node)[1]
            while cur_node != start_node:
                yield cur_node
                cur_node = get_adjacent_port_nodes(cur_node)[1]

        def get_port_edge_side(port_u, port_v):
            assert port_v == get_adjacent_port_nodes(port_u)[1]
            u_side = port_u[1][1]
            return (u_side + 1) % 4

        def get_adjacent_port_nodes(port_node):
            type = port_node[0]
            if type == 'side':
                v = port_node[1][0]
                side = port_node[1][1]
                number = port_node[1][2]
                if number == 0:
                    return get_corner_node(v, side), get_port_node(v, side, number + 1)
                elif number >= self.port_cnt - 1:
                    return get_port_node(v, side, number - 1), get_corner_node(v, (side + 1) % 4)
                else:
                    return get_port_node(v, side, number - 1), get_port_node(v, side, number + 1)
            elif type == 'corner':
                v = port_node[1][0]
                side = port_node[1][1]
                return get_port_node(v, (side + 3) % 4, self.port_cnt - 1), get_port_node(v, side, 0)

        origin_port = {}
        for u in self.G.nodes():
            if not v_is_vertex(u):
                continue
            # because side list is circular, shift it such that no segment of edges all on the same side is chopped
            side_list = collections.deque(
                [(he, self.side_dict[he]) for he in self.dcel.vertices[u].surround_half_edges()])
            count = 0
            while side_list[0][1] == side_list[-1][1] and len(side_list) > 1:  # ensure that a side isn't chopped by the array
                if count > len(side_list):
                    raise Exception("All edges connected here leave the same side...")
                side_list.append(side_list.popleft())
                count += 1

            l_cnt, r_cnt = 0, 1
            for he, side in list(side_list):
                next_dir = self.side_dict[he.succ]
                if (side + 3) % 4 == next_dir and v_is_bend(he.twin.ori.id):
                    l_cnt -= 1

            for he, side in list(side_list):
                next_dir = self.side_dict[he.succ]
                _, v = he.get_points()
                if v_is_vertex(u) and v_is_bend(v):  # vertex to bend
                    assert he not in origin_port
                    assert he.twin not in origin_port
                    if (side + 1) % 4 == next_dir:
                        # this edge bends to the right
                        origin_port[he] = get_port_node(he.ori.id, side, side_len + r_cnt)
                        r_cnt += 1
                    elif (side + 3) % 4 == next_dir:
                        # this edge bends to the left
                        origin_port[he] = get_port_node(he.ori.id, side, side_len + l_cnt)
                        l_cnt += 1
                else: # vertex vertex, vertex crossing dummy
                    assert he not in origin_port
                    # this edge goes straight (vertex to vertex), or start at bend, crossing, or loop dummy
                    origin_port[he] = get_port_node(he.ori.id, side, side_len)

        ori_nodes = [node for node in self.G.nodes() if v_is_vertex(node)]
        ori_edges = {node: list(self.G.edges(node)) for node in ori_nodes}

        v_existing_ports = {}
        for u, v, in list(self.G.edges()):
            # for every edge going out from vertex in g, subdivide it with two (one)? vertices, which correspond to each of its ports its attached to
            # should only subdivide into two if vertex vertex, otherwise just do one
            he = self.dcel.half_edges[u, v]
            he_l2r = he

            if v_is_vertex(u) and v_is_vertex(v):
                ori_port = origin_port[he]
                dest_port = origin_port[he.twin]

                # update graph, dcel, and side_dict
                self.G.remove_edge(u, v)
                self.G.add_node(ori_port)
                self.G.add_node(dest_port)
                self.G.add_edge(u, ori_port)
                self.G.add_edge(ori_port, dest_port)
                self.G.add_edge(dest_port, v)
                self.dcel.add_node_between(u, ori_port, v)
                self.dcel.add_node_between(ori_port, dest_port, v)

                he_l2a = self.dcel.half_edges[u, ori_port]
                he_a2b = self.dcel.half_edges[ori_port, dest_port]
                he_b2r = self.dcel.half_edges[dest_port, v]

                self.side_dict[he_l2a] = self.side_dict[he_l2r]
                self.side_dict[he_l2a.twin] = (self.side_dict[he_l2r] + 2) % 4
                self.side_dict[he_a2b] = self.side_dict[he_l2r]
                self.side_dict[he_a2b.twin] = (self.side_dict[he_l2r] + 2) % 4
                self.side_dict[he_b2r] = self.side_dict[he_l2r]
                self.side_dict[he_b2r.twin] = (self.side_dict[he_l2r] + 2) % 4
                self.side_dict.pop(he_l2r)
                self.side_dict.pop(he_l2r.twin)

                if u not in v_existing_ports:
                    v_existing_ports[u] = []
                v_existing_ports[u].append(ori_port)
                if v not in v_existing_ports:
                    v_existing_ports[v] = []
                v_existing_ports[v].append(dest_port)
            elif v_is_vertex(u) or v_is_vertex(v):
                if v_is_vertex(v):
                    u, v = v, u
                ori_port = origin_port[he]
                self.G.remove_edge(u, v)
                self.G.add_node(ori_port)
                self.G.add_edge(u, ori_port)
                self.G.add_edge(ori_port, v)
                self.dcel.add_node_between(u, ori_port, v)

                he_l2m = self.dcel.half_edges[u, ori_port]
                he_m2r = self.dcel.half_edges[ori_port, v]

                self.side_dict[he_l2m] = self.side_dict[he_l2r]
                self.side_dict[he_l2m.twin] = (self.side_dict[he_l2m] + 2) % 4
                self.side_dict[he_m2r] = self.side_dict[he_l2r]
                self.side_dict[he_m2r.twin] = (self.side_dict[he_m2r] + 2) % 4
                self.side_dict.pop(he_l2r)
                self.side_dict.pop(he_l2r.twin)

                if u not in v_existing_ports:
                    v_existing_ports[u] = []
                v_existing_ports[u].append(ori_port)


        for v in ori_nodes:
            # connect all these vertices in the graph, dcel and side_list
            init_port = v_existing_ports[v][0]  # start with a port guaranteed in the dcel
            port_list = list(get_port_list(init_port)) + [init_port]
            for cur_port, next_port in itertools.pairwise(port_list):
                v_to_cur = (get_vertex_of_port(cur_port), cur_port)
                if v_to_cur in self.G.edges():  # means this current port is already existing, should use the vertex subdivided for the prevu and succu
                    u_prev = self.dcel.half_edges[v_to_cur]
                    u_succ = u_prev.succ
                else:
                    prev_port = get_adjacent_port_nodes(cur_port)[0]
                    u_prev = self.dcel.half_edges[prev_port, cur_port]
                    u_succ = self.dcel.half_edges[cur_port, prev_port]

                if next_port in self.G.nodes():
                    self.G.add_edge(cur_port, next_port)
                    self.dcel.connect(u_prev.inc, cur_port, next_port, self.side_dict,
                                      get_port_edge_side(cur_port, next_port))
                    # update side dict now
                    he = self.dcel.half_edges[cur_port, next_port]
                    self.side_dict[he] = get_port_edge_side(cur_port, next_port)
                    self.side_dict[he.twin] = (self.side_dict[he] + 2) % 4
                else:
                    self.G.add_node(cur_port)
                    self.G.add_edge(cur_port, next_port)
                    self.dcel.extend_vertex_between_edges(cur_port, next_port, u_prev, u_succ)

                    he = self.dcel.half_edges[cur_port, next_port]
                    self.side_dict[he] = get_port_edge_side(cur_port, next_port)
                    self.side_dict[he.twin] = (self.side_dict[he] + 2) % 4

        for v in ori_nodes:
            # pop these original nodes from the graph, manually pop edges from dcel,
            # for the vertex cycle, go around and update their faces, prev, and succ
            # but no need to update anything in side dict
            self.G.remove_node(v)
            ori_he = list(self.dcel.half_edges.values())
            for he in ori_he:
                he_u, he_v = he.get_points()
                if he_u == v or he_v == v:
                    self.dcel.half_edges.pop((he_u, he_v))
                    self.side_dict.pop(he)
                    print('popping', he)

            # clockwise
            for port in get_port_list(get_corner_node(v, 0)):
                prev_port, next_port = get_adjacent_port_nodes(port)
                cur_port, next_next_port = get_adjacent_port_nodes(next_port)
                assert cur_port == port

                prev_he = self.dcel.half_edges[prev_port, cur_port]
                succ_he = self.dcel.half_edges[next_port, next_next_port]
                he = self.dcel.half_edges[port, next_port]

                # if the face adjacent to this guy is still in the face list, pop
                if he.inc.id in self.dcel.faces:
                    self.dcel.faces.pop(he.inc.id)

                # check if our new face is created, and create it if is
                face_id = ('face_vertex', v)
                if face_id not in self.dcel.faces:
                    new_face = Face(face_id)
                    self.dcel.faces[face_id] = new_face
                    new_face.inc = he

                he.inc = self.dcel.faces[face_id]
                he.prev = prev_he
                prev_he.succ = he
                he.succ = succ_he
                succ_he.prev = he

        new_ext_edge = (origin_port[self.ori_ext_edge], origin_port.get(self.ori_ext_edge.twin, self.ori_ext_edge.twin.ori.id))
        for face in self.dcel.faces.values():
            face.is_external = False
        ext_face = self.dcel.half_edges[new_ext_edge].inc
        ext_face.is_external = True
        self.dcel.ext_face = ext_face

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
                side, next_side = self.side_dict[he], self.side_dict[he.succ]
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
                    self.side_dict[he_l2d] = self.side_dict[he_l2r]
                    self.side_dict[he_l2d.twin] = (self.side_dict[he_l2r] + 2) % 4
                    self.side_dict[he_d2r] = self.side_dict[he_l2r]
                    self.side_dict[he_d2r.twin] = (self.side_dict[he_l2r] + 2) % 4
                    self.side_dict.pop(he_l2r)
                    self.side_dict.pop(he_l2r.twin)

                    self.G.add_edge(dummy_node_id, extend_node_id)
                    self.dcel.connect(face, extend_node_id, dummy_node_id, self.side_dict, self.side_dict[he])

                    he_e2d = self.dcel.half_edges[extend_node_id, dummy_node_id]
                    lf, rf = he_e2d.twin.inc, he_e2d.inc
                    self.side_dict[he_e2d] = self.side_dict[he]
                    self.side_dict[he_e2d.twin] = (self.side_dict[he] + 2) % 4

                    refine_internal(lf)
                    refine_internal(rf)
                    break

        def build_border():
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
                        self.side_dict[he] = i  # assign side
                        self.side_dict[he.twin] = (i + 2) % 4
                        border_side_dict[i] = he
                    border_dcel.faces.pop(face.id)
                    border_dcel.faces[self.dcel.ext_face.id] = self.dcel.ext_face
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

        ori_ext_face = self.dcel.ext_face
        border_side_dict = build_border()

        for he in ori_ext_face.surround_half_edges():
            extend_node_id = he.succ.ori.id
            side, next_side = self.side_dict[he], self.side_dict[he.succ]
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
            if face.id != ("face", -1):
                refine_internal(face)