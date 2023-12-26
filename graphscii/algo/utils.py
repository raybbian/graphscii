def v_is_h_aux(vertex):
    return vertex[0][:5] == 'h_aux'


def v_is_structural(vertex):
    return vertex[0] == 'loop_dummy' or vertex[0] == 'vertex' or vertex[0] == 'crossing_dummy'


def v_is_face(vertex):
    return vertex[0] == 'face'


def v_is_face_dummy(vertex):
    return vertex[0] == 'vertex_face_dummy'


def v_is_struct_dummy(vertex):
    return vertex[0] == 'loop_dummy' or vertex[0] == 'crossing_dummy'


def v_is_rect_dummy(vertex):
    return vertex[0] == 'rect_dummy'


def v_is_crossing_dummy(vertex):
    return vertex[0] == 'crossing_dummy'


def v_is_corner(vertex):
    return vertex[0][:6] == 'corner'


def v_is_bend(vertex):
    return vertex[0] == 'bend'


def v_is_vertex(vertex):
    return vertex[0] == 'vertex'
