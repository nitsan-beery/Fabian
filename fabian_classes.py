from point import *


shapes = {'CIRCLE', 'LINE', 'ARC'}


class Part:
    def __init__(self, color=gv.default_color):
        self.is_marked = False
        self.board_part = None
        self.color = color


class Entity(Part):
    def __init__(self, shape=None, center=None, radius=None, start=None, end=None, start_angle=None, end_angle=None,
                 color=gv.default_color):
        super().__init__(color)
        self.shape = shape
        self.center = center
        self.radius = radius
        self.arc_start_angle = start_angle
        self.arc_end_angle = end_angle
        self.start = start
        self.end = end
        self.left_bottom = None
        self.right_up = None
        self.set_arc()
        self.set_left_bottom_right_up()
        self.nodes_list = []

    # set arc start point, end point, left_bottom and right_up
    def set_arc(self):
        if self.shape != 'ARC' or self.arc_start_angle is None or self.arc_end_angle is None:
            return
        if self.arc_start_angle >= 360:
            self.arc_start_angle -= 360
            self.arc_end_angle -= 360
        if self.arc_end_angle < self.arc_start_angle:
            self.arc_end_angle += 360
        p1 = Point(self.center.x + self.radius * math.cos(self.arc_start_angle * math.pi / 180),
                   self.center.y + self.radius * math.sin(self.arc_start_angle * math.pi / 180))
        p2 = Point(self.center.x + self.radius * math.cos(self.arc_end_angle * math.pi / 180),
                   self.center.y + self.radius * math.sin(self.arc_end_angle * math.pi / 180))
        self.start = p1
        self.end = p2

    def set_left_bottom_right_up(self):
        if self.shape != 'CIRCLE':
            if self.start is None or self.end is None:
                self.left_bottom, self.right_up = None, None
            else:
                self.left_bottom, self.right_up = get_sorted_points(self.start, self.end, sort_by_x=True)
        else:
            if self.center is None or self.radius is None:
                self.left_bottom, self.right_up = None, None
            else:
                self.left_bottom = Point(self.center.x - self.radius, self.center.y - self.radius)
                self.right_up = Point(self.center.x + self.radius, self.center.y + self.radius)

    def is_equal(self, e):
        t1 = (self.shape == e.shape and self.radius == e.radius)
        if self.shape == 'CIRCLE':
            return t1 and self.center.is_equal(e.center)
        else:
            t2 = self.start.is_equal(e.start) and self.end.is_equal(e.end)
            t3 = self.start.is_equal(e.end) and self.end.is_equal(e.start)
            return t1 and (t2 or t3)

    # node[0] = start node,   node[-1] = end node
    def add_node_to_entity_nodes_list(self, i):
        for j in self.nodes_list:
            if j == i:
                return
        if len(self.nodes_list) < 2:
            self.nodes_list.append(i)
        else:
            self.nodes_list.insert(1, i)

    def convert_into_tuple(self):
        center = self.center
        if center is not None:
            center = center.convert_into_tuple()
        start = self.start
        if start is not None:
            start = start.convert_into_tuple()
        end = self.end
        if end is not None:
            end = end.convert_into_tuple()
        t = (self.shape, center, self.radius, self.arc_start_angle, self.arc_end_angle, start, end, self.color,
             self.nodes_list, self.is_marked)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 10:
            print(f"tuple doesn't match Entity type: {t}")
            return
        self.shape = t[0]
        center = t[1]
        if center is not None:
            center = Point()
            center.get_data_from_tuple(t[1])
        self.center = center
        self.radius = t[2]
        self.arc_start_angle = t[3]
        self.arc_end_angle = t[4]
        start = t[5]
        if start is not None:
            start = Point()
            start.get_data_from_tuple(t[5])
        self.start = start
        end = t[6]
        if end is not None:
            end = Point()
            end.get_data_from_tuple(t[6])
        self.end = end
        self.color = t[7]
        self.nodes_list = t[8]
        self.set_arc()
        self.set_left_bottom_right_up()
        self.is_marked = t[9]


class Node(Part):
    def __init__(self, point=None, entity=None):
        super().__init__(gv.node_color)
        if point is None:
            point = Point()
        self.p = point
        self.entity = entity
        self.attached_lines = []
        self.expected_elements = 0
        self.exceptions = []
        self.board_text = None

    def is_equal(self, node):
        return self.p.is_equal(node.p)

    def get_index_of_node_in(self, node_list):
        for i in range(len(node_list)):
            node = node_list[i]
            if self.p.is_equal(node.p):
                return i
        return None

    def convert_into_tuple(self):
        t = (self.p.convert_into_tuple(), self.entity)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 2:
            print(f"tuple doesn't match Node type: {t}")
            return
        self.p.get_data_from_tuple(t[0])
        self.entity = t[1]


class NetLine(Part):
    def __init__(self, start_node=None, end_node=None, entity=None, color=gv.net_line_color, is_outer_line=False):
        super().__init__(color)
        self.start_node = start_node
        self.end_node = end_node
        self.entity = entity
        self.is_outer_line = is_outer_line

    def is_equal(self, line):
        t1 = self.start_node == line.start_node and self.end_node == line.end_node
        t2 = self.start_node == line.end_node and self.end_node == line.start_node
        return t1 or t2

    def is_in_list(self, line_list):
        for i in range(len(line_list)):
            if self.is_equal(line_list[i]):
                return True
        return False

    def convert_into_tuple(self):
        t = (self.start_node, self.end_node, self.entity, self.color, self.is_marked, self.is_outer_line)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 6:
            print(f"tuple doesn't match NetLine type: {t}")
            return
        self.start_node = t[0]
        self.end_node = t[1]
        self.entity = t[2]
        self.color = t[3]
        self.is_marked = t[4]
        self.is_outer_line = t[5]


class Element(Part):
    def __init__(self, color=gv.element_color):
        super().__init__(color)
        self.nodes = []
    def convert_into_tuple(self):
        t = (self.nodes, self.color)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 2:
            print(f"tuple doesn't match Element type: {t}")
        self.nodes = t[0]
        self.color = t[1]


class AttachedLine:
    def __init__(self, line_index=None, second_node=0, angle_to_second_node=0, is_outer_line=False, is_available=True):
        self.line_index = line_index
        self.second_node = second_node
        self.angle_to_second_node = angle_to_second_node
        self.is_outer_line = is_outer_line
        self.is_available = is_available


class SelectedPart(Part):
    def __init__(self, part_type='entity', index=0, color=gv.mark_rect_color):
        super().__init__(color)
        self.part_type = part_type
        self.index = index


class FabianState:
    def __init__(self):
        self.entity_list = None
        self.node_list = None
        self.net_line_list = None
        self.element_list = None
        self.select_mode = None
        self.work_mode = None
        self.select_parts_mode = None
        self.show_entities = True
        self.show_nodes = True
        self.show_elements = False
        self.show_node_number = gv.default_show_node_number
        self.show_net = True
        self.scale = None
        self.board = None


