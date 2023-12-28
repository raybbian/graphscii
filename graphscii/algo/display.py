from .compaction import Compaction
from .utils import v_is_vertex, v_is_rect_dummy


class BoxChar:
    def __init__(self, val):
        # val is 4 digit string (number between 0, 15 incl)
        if not 0 <= val <= 15:
            raise Exception("bad val")
        self.val = val

    def char(self):
        match self.val:
            case 0:
                return ' '
            case 1:
                return '╹'
            case 2:
                return '╸'
            case 3:
                return '┛'
            case 4:
                return '╻'
            case 5:
                return '┃'
            case 6:
                return '┓'
            case 7:
                return '┫'
            case 8:
                return '╺'
            case 9:
                return '┗'
            case 10:
                return '━'
            case 11:
                return '┻'
            case 12:
                return '┏'
            case 13:
                return '┣'
            case 14:
                return '┳'
            case 15:
                return '╋'

    @staticmethod
    def l():
        return BoxChar(2)

    @staticmethod
    def b():
        return BoxChar(4)

    @staticmethod
    def r():
        return BoxChar(8)

    @staticmethod
    def t():
        return BoxChar(1)

    @staticmethod
    def tb():
        return BoxChar.t() + BoxChar.b()

    @staticmethod
    def lr():
        return BoxChar.l() + BoxChar.r()

    def __add__(self, other):
        return BoxChar(self.val | other.val)

    def __iadd__(self, other):
        return BoxChar(self.val | other.val)

    def __sub__(self, other):
        return BoxChar(self.val & ~other.val)

    def __isub__(self, other):
        return BoxChar(self.val & ~other.val)


class Display:
    def __init__(self, compaction: Compaction, with_labels=False):
        self.G = compaction.G
        self.pos = compaction.pos
        self.dcel = compaction.dcel
        self.rect_edges = compaction.rect_edges
        self.v_w = compaction.v_w
        self.v_h = compaction.v_h
        self.ori_edges = compaction.ori_edges
        self.bend_offsets = compaction.bend_offsets

        self.minx = min(c[0] for v, c in self.pos.items() if not v_is_rect_dummy(v)) - self.v_w
        self.maxx = max(c[0] for v, c in self.pos.items() if not v_is_rect_dummy(v)) + self.v_w
        self.miny = min(c[1] for v, c in self.pos.items() if not v_is_rect_dummy(v)) - self.v_h
        self.maxy = max(c[1] for v, c in self.pos.items() if not v_is_rect_dummy(v)) + self.v_h

        self.output = {r: {c: BoxChar(0) for c in range(self.minx, self.maxx + 1)} for r in
                       range(self.miny, self.maxy + 1)}

        self.draw_edges()
        self.draw_vertices(with_labels)

    def draw_vertices(self, with_labels=False):
        for vertex, (x, y) in self.pos.items():
            if not v_is_vertex(vertex):
                continue
            self.draw_box(x, y, self.v_w, self.v_h)
            if with_labels:
                label_len = len(str(vertex[1]))
                mid_ind = label_len // 2
                for c in range(label_len):
                    self.output[y][x + c - mid_ind] = str(vertex[1])[c]

    def draw_edges(self):
        for edge in self.ori_edges:
            self.draw_edge(edge)

    def assert_inbounds(self, x, y):
        if not (self.minx <= x <= self.maxx and self.miny <= y <= self.maxy):
            raise Exception("Tried to draw out of bounds")

    def draw_box(self, x0, y0, half_x, half_y):
        """halfw/h is unit squares excluding center to including side"""
        self.draw_line(x0 - half_x, y0 - half_y, x0 + half_x, y0 - half_y)
        self.draw_line(x0 - half_x, y0 + half_y, x0 + half_x, y0 + half_y)
        self.draw_line(x0 - half_x, y0 - half_y, x0 - half_x, y0 + half_y)
        self.draw_line(x0 + half_x, y0 - half_y, x0 + half_x, y0 + half_y)

    def draw_edge(self, edge):
        # difference between drawing edge and drawing line is that we need to do some processing!
        a = edge[0]
        b = edge[1]
        (x0, y0), (x1, y1) = self.pos[a], self.pos[b]
        if a in self.bend_offsets and v_is_vertex(b) and not (x0 == x1 or y0 == y1):
            x1, y1 = x1 + self.bend_offsets[a][0], y1 + self.bend_offsets[a][1]
        if b in self.bend_offsets and v_is_vertex(a) and not (x0 == x1 or y0 == y1):
            x0, y0 = x0 + self.bend_offsets[b][0], y0 + self.bend_offsets[b][1]

        if x0 == x1:
            if v_is_vertex(a):
                y0 += ((y1 - y0) // abs(y1 - y0)) * self.v_h
            if v_is_vertex(b):
                y1 -= ((y1 - y0) // abs(y1 - y0)) * self.v_h
        if y0 == y1:
            if v_is_vertex(a):
                x0 += ((x1 - x0) // abs(x1 - x0)) * self.v_w
            if v_is_vertex(b):
                x1 -= ((x1 - x0) // abs(x1 - x0)) * self.v_w
        self.draw_line(x0, y0, x1, y1)

    def draw_line(self, x0, y0, x1, y1):
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])
        self.assert_inbounds(x0, y0)
        self.assert_inbounds(x1, y1)
        if x0 == x1:
            self.output[y0][x0] += BoxChar.b()
            self.output[y1][x0] += BoxChar.t()
            for i in range(y0 + 1, y1):
                self.output[i][x0] += BoxChar.tb()
        elif y0 == y1:
            self.output[y0][x0] += BoxChar.r()
            self.output[y0][x1] += BoxChar.l()
            for i in range(x0 + 1, x1):
                self.output[y0][i] += BoxChar.lr()
        else:
            raise Exception("Input coordinates are not lines")

    def build_output(self):
        out = ""
        for r in range(self.miny, self.maxy + 1):
            for c in range(self.minx, self.maxx + 1):
                out += self.output[r][c].char() if type(self.output[r][c]) is BoxChar else self.output[r][c]
            out += '\n'
        return out

    def write_to_file(self, path="./output.txt"):
        with open(path, "w") as f:
            f.write(self.build_output())

    def __repr__(self):
        return self.build_output()
