from board import *
import ezdxf
import math
from tkinter import messagebox, ttk
from operator import attrgetter, itemgetter

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


class FabianBoard(Board):
    def __init__(self, scale=1):
        super().__init__(True)
        self.scale = scale
        self.window_main.title("Fabian")
        self.button_load.config(text='Load', command=lambda: self.load())
        self.button_save.config(text='Save as', command=lambda: self.save_as())
        self.button_zoom_in = tk.Button(self.frame_2, text='Zoom In', command=lambda: self.zoom(4/3))
        self.button_zoom_out = tk.Button(self.frame_2, text='Zoom Out', command=lambda: self.zoom(3/4))
        self.button_center = tk.Button(self.frame_2, text='Center view', command=lambda: self.center_view())
        self.button_zoom_in.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.button_zoom_out.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.button_center.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.board.config(bg=gv.board_bg_color)

        self.entity_list = []
        self.node_list = [Node()]
        self.net_line_list = []
        self.element_list = []
        self.longitude = None
        self.select_mode = gv.default_select_mode
        self.work_mode = gv.default_work_mode
        self.select_parts_mode = gv.default_select_parts_mode
        self.mark_option = gv.default_mark_option
        self.selected_part = None
        self.selected_part_mark = None
        self.new_line_edge = [None, None]
        self.new_line_edge_mark = [None, None]
        # line after selecting 2 points
        self.new_line_mark = None
        # line following mouse
        self.temp_line_mark = None
        self.temp_rect_start_point = None
        self.temp_rect_mark = None
        self.show_entities = True
        self.show_nodes = True
        self.show_elements = False
        self.show_node_number = gv.default_show_node_number
        self.show_net = True
        self.progress_bar = None
        self.state = []

        self.board.bind('<Motion>', self.motion)
        self.board.bind('<Button-1>', self.mouse_1_pressed)
        self.board.bind('<B1-Motion>', self.mouse_1_motion)
        self.board.bind('<ButtonRelease-1>', self.mouse_1_released)
        self.board.bind('<Button-3>', self.mouse_3_pressed)

    def reset_board(self, empty_node_list=False, center_screen_position=True):
        self.board.delete('all')
        if center_screen_position:
            self.set_screen_position(self.center.x, self.center.y)
        self.entity_list = []
        if empty_node_list:
            self.node_list = []
        else:
            self.node_list = [Node()]
        self.net_line_list = []
        self.element_list = []
        self.longitude = None
        self.select_mode = gv.default_select_mode
        self.work_mode = gv.default_work_mode
        self.select_parts_mode = gv.default_select_parts_mode
        self.mark_option = gv.default_mark_option
        self.selected_part = None
        self.selected_part_mark = None
        self.new_line_edge = [None, None]
        self.new_line_edge_mark = [None, None]
        self.new_line_mark = None
        self.temp_line_mark = None
        self.temp_rect_start_point = None
        self.temp_rect_mark = None
        self.progress_bar = None

    def resume_state(self):
        if len(self.state) < 1:
            return
        state = self.state[-1]
        self.reset_board(empty_node_list=True, center_screen_position=False)
        for t in state.entity_list:
            e = Entity()
            e.get_data_from_tuple(t)
            self.entity_list.append(e)
        for t in state.node_list:
            n = Node()
            n.get_data_from_tuple(t)
            self.node_list.append(n)
        for t in state.net_line_list:
            line = NetLine()
            line.get_data_from_tuple(t)
            self.net_line_list.append(line)
        for t in state.element_list:
            element = Element()
            element.get_data_from_tuple(t)
            self.element_list.append(element)
        self.select_mode = state.select_mode
        self.work_mode = state.work_mode
        self.select_parts_mode = state.select_parts_mode
        self.show_entities = state.show_entities
        self.show_nodes = state.show_nodes
        self.show_elements = state.show_elements
        self.show_node_number = state.show_node_number
        self.show_net = state.show_net
        self.scale = state.scale
        self.board = state.board
        self.state.pop(-1)
        self.update_view()

    def keep_state(self):
        if len(self.state) == gv.max_state_stack:
            self.state.pop(0)
        state = FabianState()
        entity_list = []
        for e in self.entity_list:
            t = e.convert_into_tuple()
            entity_list.append(t)
        node_list = []
        for e in self.node_list:
            t = e.convert_into_tuple()
            node_list.append(t)
        net_list = []
        for e in self.net_line_list:
            t = e.convert_into_tuple()
            net_list.append(t)
        element_list = []
        for e in self.element_list:
            t = e.convert_into_tuple()
            element_list.append(t)
        state.entity_list = entity_list
        state.node_list = node_list
        state.net_line_list = net_list
        state.element_list = element_list
        state.select_mode = self.select_mode
        state.work_mode = self.work_mode
        state.select_parts_mode = self.select_parts_mode
        state.show_entities = self.show_entities
        state.show_nodes = self.show_nodes
        state.show_elements = self.show_elements
        state.show_node_number = self.show_node_number
        state.show_net = self.show_net
        state.scale = self.scale
        state.board = self.board
        self.state.append(state)

    def mouse_1_pressed(self, key):
        if self.temp_rect_mark is not None:
            self.board.delete(self.temp_rect_mark)
        x, y = self.convert_keyx_keyy_to_xy(key.x, key.y)
        if self.selected_part_mark is None:
            self.temp_rect_start_point = Point(x, y)
            return
        if self.select_parts_mode == 'entity' and self.selected_part is not None:
            e = self.entity_list[self.selected_part]
            p1 = e.left_bottom
            p2 = e.right_up
            d, p = self.get_distance_from_entity_and_nearest_point(Point(x, y), self.selected_part)
        elif self.select_parts_mode == 'net_line' and self.selected_part is not None:
            line = self.net_line_list[self.selected_part]
            node_1 = self.node_list[line.start_node]
            node_2 = self.node_list[line.end_node]
            p1 = node_1.p
            p2 = node_2.p
            d, p = self.get_distance_from_line_and_nearest_point(Point(x, y), p1, p2)
        if self.select_mode == 'edge':
            d1 = p1.get_distance_to_point(Point(x, y))
            d2 = p2.get_distance_to_point(Point(x, y))
            p = p2
            if d1 < d2:
                p = p1

        # first point
        if self.new_line_edge[0] is None:
            self.new_line_edge[0] = p
            self.new_line_edge_mark[0] = self.draw_circle(p, gv.edge_line_mark_radius/self.scale)
            return
        # remove selection of first point
        elif self.new_line_edge[0] == p:
            # only 1 edge exists
            self.board.delete(self.new_line_edge_mark[0])
            self.board.delete(self.temp_line_mark)
            if self.new_line_edge[1] is None:
                self.new_line_edge_mark[0] = None
                self.new_line_edge[0] = None
            # there is a second edge and a line between
            else:
                self.board.delete(self.new_line_mark)
                self.new_line_mark = None
                self.new_line_edge_mark[0] = self.new_line_edge_mark[1]
                self.new_line_edge[0] = self.new_line_edge[1]
                self.new_line_edge_mark[1] = None
                self.new_line_edge[1] = None
            return

        # second point on the same entity or line
        if self.new_line_edge[0].is_equal(p1) or self.new_line_edge[0].is_equal(p2):
            return

        # second point
        else:
            self.board.delete(self.temp_line_mark)
            if self.new_line_edge[1] is None:
                self.new_line_edge[1] = p
                if self.work_mode == 'dxf':
                    self.new_line_edge_mark[1] = self.draw_circle(p, gv.edge_line_mark_radius/self.scale)
                    self.new_line_mark = self.draw_line(self.new_line_edge[0], self.new_line_edge[1])
                # work mode = inp
                else:
                    self.add_line()
            else:
                self.board.delete(self.new_line_edge_mark[1])
                self.new_line_edge_mark[1] = None
                self.board.delete(self.new_line_mark)
                self.new_line_mark = None
                if self.new_line_edge[1] != p:
                    self.new_line_edge[1] = p
                    self.new_line_edge_mark[1] = self.draw_circle(p, gv.edge_line_mark_radius / self.scale)
                    self.new_line_mark = self.draw_line(self.new_line_edge[0], self.new_line_edge[1])
                else:
                    self.new_line_edge[1] = None

    def mouse_1_motion(self, key):
        if self.temp_rect_start_point is None:
            self.motion(key)
            return
        p1 = Point()
        p1.x, p1.y = self.convert_xy_to_screen(self.temp_rect_start_point.x, self.temp_rect_start_point.y)
        canvas_x = self.board.canvasx(key.x)
        canvas_y = self.board.canvasy(key.y)
        p2 = Point(canvas_x, canvas_y)
        if self.temp_rect_mark is not None:
            self.board.delete(self.temp_rect_mark)
        self.temp_rect_mark = self.board.create_rectangle(p1.x, p1.y, p2.x, p2.y)

    def mouse_1_released(self, key):
        if self.temp_rect_start_point is not None:
            p1 = self.temp_rect_start_point
            p1.x, p1.y = self.convert_xy_to_screen(p1.x, p1.y)
            p2 = Point()
            p2.x = self.board.canvasx(key.x)
            p2.y = self.board.canvasy(key.y)
            left = p1.x
            right = p2.x
            lower = p1.y
            upper = p2.y
            if left > right:
                left, right = right, left
            if upper > lower:
                upper, lower = lower, upper
            enclosed_parts = self.board.find_enclosed(left, upper, right, lower)
            t1 = len(enclosed_parts) > 0
            t2 = self.work_mode == 'dxf'
            t3 = self.work_mode == 'inp' and self.select_parts_mode == 'net_line'
            if t1 and (t2 or t3):
                mark_option = {
                    "mark": True,
                    "unmark": False
                }
                self.keep_state()
                marked_color = gv.marked_entity_color
                non_marked_color = gv.default_color
                part_list = self.entity_list
                list_name = 'entities'
                if self.select_parts_mode == 'net_line':
                    part_list = self.net_line_list
                    marked_color = gv.marked_net_line_color
                    non_marked_color = gv.net_line_color
                    list_name = 'net_lines'
                i = 0
                for p in part_list:
                    if p.board_part in enclosed_parts:
                        if self.mark_option == "mark" or self.mark_option == "unmark":
                            p.is_marked = mark_option.get(self.mark_option)
                        # invert
                        else:
                            p.is_marked = not p.is_marked
                        if p.is_marked:
                            self.set_part_color(list_name, i, marked_color)
                        else:
                            self.set_part_color(list_name, i, non_marked_color)
                    i += 1
        if self.temp_rect_mark is not None:
            self.board.delete(self.temp_rect_mark)
            self.temp_rect_mark = None
        self.temp_rect_start_point = None

    def choose_mark_option(self, option):
        self.mark_option = option

    def set_node_number_state(self, mode):
        if mode == 'show':
            should_show = True
        else:
            should_show = False
        if self.show_node_number != should_show:
            self.keep_state()
            self.show_node_number = should_show
            self.update_view()

    def mouse_3_pressed(self, key):
        menu = tk.Menu(self.board, tearoff=0)
        work_mode_menu = tk.Menu(menu, tearoff=0)
        work_mode_menu.add_command(label="DXF", command=lambda: self.change_work_mode('dxf'))
        work_mode_menu.add_command(label="INP", command=lambda: self.change_work_mode('inp'))
        work_mode_menu.add_separator()
        work_mode_menu.add_command(label="Quit")
        select_part_menu = tk.Menu(menu, tearoff=0)
        select_part_menu.add_command(label="Entities", command=lambda: self.change_select_parts_mode('entity'))
        select_part_menu.add_command(label="Net lines", command=lambda: self.change_select_parts_mode('net_line'))
        select_mode_menu = tk.Menu(menu, tearoff=0)
        select_mode_menu.add_command(label="Edges", command=lambda: self.change_mouse_selection_mode('edge'))
        select_mode_menu.add_command(label="Points", command=lambda: self.change_mouse_selection_mode('point'))
        select_mode_menu.add_separator()
        select_mode_menu.add_command(label="Quit")
        mark_option_menu = tk.Menu(self.board, tearoff=0)
        mark_option_menu.add_command(label="mark", command=lambda: self.choose_mark_option("mark"))
        mark_option_menu.add_command(label="unmark", command=lambda: self.choose_mark_option("unmark"))
        mark_option_menu.add_command(label="invert", command=lambda: self.choose_mark_option("invert"))
        mark_option_menu.add_separator()
        mark_option_menu.add_command(label="Quit", command=lambda: self.choose_mark_option("quit"))
        show_entities_menu = tk.Menu(menu, tearoff=0)
        show_entities_menu.add_command(label="Show Weak", command=lambda: self.set_all_dxf_entities_color(gv.weak_entity_color))
        show_entities_menu.add_command(label="Show Strong", command=lambda: self.set_all_dxf_entities_color(gv.default_color))
        show_entities_menu.add_command(label="Hide", command=lambda: self.hide_dxf_entities())
        show_entities_menu.add_separator()
        show_entities_menu.add_command(label="Quit")
        show_node_number_menu = tk.Menu(menu, tearoff=0)
        show_node_number_menu.add_command(label="Show", command=lambda: self.set_node_number_state('show'))
        show_node_number_menu.add_command(label="Hide", command=lambda: self.set_node_number_state('hide'))
        net_menu = tk.Menu(menu, tearoff=0)
        net_menu.add_command(label="show", command=lambda: self.change_show_net_mode('show'))
        net_menu.add_command(label="hide", command=lambda: self.change_show_net_mode('hide'))
        net_menu.add_command(label="clear", command=lambda: self.change_show_net_mode('clear'))
        show_elements_menu = tk.Menu(menu, tearoff=0)
        show_elements_menu.add_command(label="show", command=self.show_all_elements)
        show_elements_menu.add_command(label="hide", command=self.hide_all_elements)
        menu.add_command(label="Undo", command=self.resume_state)
        menu.add_separator()
        menu.add_cascade(label='Select mode', menu=select_part_menu)
        menu.add_separator()
        menu.add_cascade(label='Work mode', menu=work_mode_menu)
        menu.add_separator()
        menu.add_cascade(label='Mark mode', menu=mark_option_menu)
        menu.add_separator()
        # menu.add_cascade(label='Select mode', menu=select_mode_menu)
        # menu.add_separator()
        if self.new_line_edge[1] is not None:
            menu.add_command(label="add line", command=self.add_line)
        if self.new_line_edge[0] is not None and self.work_mode == 'dxf':
            self.board.delete(self.temp_line_mark)
            menu.add_command(label="remove line", command=self.remove_temp_line)
            menu.add_separator()
        if self.selected_part_mark is not None:
            menu.add_command(label="split", command=lambda: self.split(self.selected_part))
            menu.add_command(label="delete", command=self.remove_selected_part_from_list)
            if self.work_mode == 'dxf':
                menu.add_command(label="unmark", command=self.unmark_selected_entity)
                menu.add_command(label="mark", command=self.mark_selected_entity)
            menu.add_separator()
        if self.work_mode == 'dxf':
            if len(self.entity_list) > 0:
                mark_list = self.get_marked_parts('entities')
                if len(mark_list) > 1:
                    menu.add_command(label="merge marked entities", command=self.merge)
                    menu.add_separator()
                menu.add_command(label="mark all entities", command=self.mark_all_entities)
                menu.add_command(label="unmark all entities", command=self.unmark_all_entities)
                menu.add_command(label="delete marked entities", command=self.remove_marked_entities_from_list)
                menu.add_command(label="delete NON marked entities", command=self.remove_non_marked_entities_from_list)
                menu.add_separator()
        elif self.work_mode == 'inp':
            menu.add_cascade(label='Nodes number', menu=show_node_number_menu)
            menu.add_cascade(label='Net lines', menu=net_menu)
            menu.add_cascade(label='Elements', menu=show_elements_menu)
            menu.add_cascade(label='Entities', menu=show_entities_menu)
            menu.add_separator()
            menu.add_command(label="Set net", command=self.set_net)
            menu.add_separator()
        menu.add_command(label="Quit")
        menu.post(key.x_root, key.y_root)

    def change_show_net_mode(self, mode):
        self.keep_state()
        changed = False
        if mode == 'show':
            if not self.show_net:
                self.show_net = True
                changed = True
        elif mode == 'hide':
            if self.show_net:
                self.show_net = False
                changed = True
        elif mode == 'clear':
            if len(self.net_line_list) > 0:
                self.reset_net(True)
                changed = True
        if changed:
            self.update_view()
        else:
            self.state.pop(-1)

    def change_work_mode(self, mode):
        self.work_mode = mode
        if self.selected_part_mark is not None:
            self.board.delete(self.selected_part_mark)
            self.selected_part_mark = None
        self.selected_part = None
        if mode.lower() == 'dxf':
            self.show_nodes = False
            self.show_net = False
            self.show_elements = False
            self.change_select_parts_mode('entity')
            self.choose_mark_option('mark')
            self.set_all_dxf_entities_color(gv.default_color)
        elif mode.lower() == 'inp':
            self.set_initial_net()
            tmp_list = self.get_unattached_nodes(True)
            if len(tmp_list) == 0:
                print('no unattached nodes')
            self.set_all_dxf_entities_color(gv.weak_entity_color)
            self.show_nodes = True
            self.choose_mark_option('quit')
        self.update_view()

    def change_mouse_selection_mode(self, mode):
        self.select_mode = mode

    def change_select_parts_mode(self, mode):
        if self.selected_part_mark is not None:
            self.board.delete(self.selected_part_mark)
            self.selected_part_mark = None
        self.selected_part = None
        self.select_parts_mode = mode

    def motion(self, key):
        x, y = self.convert_keyx_keyy_to_xy(key.x, key.y)
        p = Point(x, y)
        selected_d = 100
        d = 100
        text = f'{round(x, gv.accuracy)}    {round(y, gv.accuracy)}'
        self.hide_text_on_screen()
        self.show_text_on_screen(text, 'lt')
        if self.new_line_edge[0] is not None:
            self.board.delete(self.temp_line_mark)
            self.temp_line_mark = self.draw_line(self.new_line_edge[0], p, gv.temp_line_color)
        if self.select_parts_mode == 'entity':
            if len(self.entity_list) == 0:
                return
            if self.selected_part is not None:
                selected_d, nearest_point = self.get_distance_from_entity_and_nearest_point(p, self.selected_part)
            i, d = self.find_nearest_entity(p, only_visible=True)
            if i is None:
                return
        elif self.select_parts_mode == 'net_line':
            if len(self.net_line_list) == 0:
                return
            if self.selected_part is not None:
                start_node = self.net_line_list[self.selected_part].start_node
                end_node = self.net_line_list[self.selected_part].end_node
                p1 = self.node_list[start_node].p
                p2 = self.node_list[end_node].p
                if self.selected_part is not None:
                    selected_d, nearest_point = self.get_distance_from_line_and_nearest_point(p, p1, p2)
            i, d = self.find_nearest_net_line(p, only_visible=True)
            if i is None:
                return
        if selected_d*self.scale > 5:
            self.remove_selected_part_mark()
        if d*self.scale < 5:
            self.remove_selected_part_mark()
            self.selected_part = i
            if self.select_parts_mode == 'entity':
                self.mark_entity(self.selected_part)
            elif self.select_parts_mode == 'net_line':
                self.mark_net_line(self.selected_part)

    def set_entity_edge_nodes(self, i):
        e = self.entity_list[i]
        e.nodes_list = []
        start_node = Node(e.start, entity=i)
        node_index = self.add_node_to_node_list(start_node)
        e.add_node_to_entity_nodes_list(node_index)
        end_node = Node(e.end, entity=i)
        node_index = self.add_node_to_node_list(end_node)
        e.add_node_to_entity_nodes_list(node_index)

    def get_split_line_points(self, p1, p2, n=gv.default_split_parts):
        point_list = [p1]
        alfa = p1.get_alfa_to(p2) * math.pi / 180
        d = p1.get_distance_to_point(p2)
        step = d / n
        start = p1
        for m in range(n):
            end = Point(start.x + step * math.cos(alfa), start.y + step * math.sin(alfa))
            point_list.append(end)
            start = end
        return point_list

    def get_split_entity_points(self, entity=0, n=gv.default_split_parts):
        e = self.entity_list[entity]
        if e.shape == 'ARC':
            point_list = []
            angle = (e.arc_end_angle-e.arc_start_angle) / n
            start_angle = e.arc_start_angle
            point_list.append(e.start)
            for m in range(n):
                end_angle = start_angle + angle
                arc = Entity(shape=e.shape, center=e.center, radius=e.radius, start_angle=start_angle,
                             end_angle=end_angle)
                point_list.append(arc.end)
                start_angle = end_angle
            return point_list
        elif e.shape == 'LINE':
            return self.get_split_line_points(e.start, e.end, n)
        elif e.shape == 'CIRCLE':
            return None

    def merge(self):
        self.keep_state()
        if self.work_mode == 'dxf':
            changed = self.merge_entities()
        elif self.work_mode == 'inp':
            changed = self.merge_net_lines()
        if not changed:
            self.state.pop(-1)

    # return continues list of lines, None if the list is broken
    def sort_net_line_parts(self, part_list):
        if part_list is None:
            return None
        elif len(part_list) == 0:
            return None
        elif len(part_list) == 1:
            return part_list
        sorted_list = []
        # sort start and end points of all lines in list
        for i in part_list:
            line = self.net_line_list[i]
            if self.node_list[line.end_node].p.is_smaller_x_smaller_y(self.node_list[line.start_node].p):
                line.start_node, line.end_node = line.end_node, line.start_node
        first_part = part_list[0]
        line_0 = self.net_line_list[first_part]
        p0 = self.node_list[line_0.start_node].p
        # find most left-bottom edge
        for i in part_list:
            line = self.net_line_list[i]
            p1 = self.node_list[line.start_node].p
            if p1.is_smaller_x_smaller_y(p0):
                first_part = i
                line_0 = self.net_line_list[first_part]
        sorted_list.append(first_part)
        part_list.remove(first_part)
        # iterate list to find connected parts, add to list or return None if can't find
        while len(part_list) > 0:
            start = self.net_line_list[sorted_list[-1]].end_node
            for j in part_list:
                found_part = False
                if self.net_line_list[j].start_node == start:
                    sorted_list.append(j)
                    found_part = True
                    part_list.remove(j)
                    break
            if not found_part:
                return None
        return sorted_list

    # return continues list of parts from same entity, None if the list is broken
    def sort_entity_parts(self, part_list):
        if part_list is None:
            return None
        elif len(part_list) == 0:
            return None
        elif len(part_list) == 1:
            return part_list
        sorted_list = []
        first_part = part_list[0]
        e_0 = self.entity_list[first_part]
        shape = e_0.shape
        if shape == 'ARC':
            # find smallest start_angle, and check all parts with same center and radius
            for i in part_list:
                ei = self.entity_list[i]
                if ei.shape != e_0.shape or ei.center != e_0.center or ei.radius != e_0.radius:
                    return None
                if ei.arc_start_angle < e_0.arc_start_angle:
                    first_part = i
                    e_0 = self.entity_list[first_part]
            sorted_list.append(first_part)
            part_list.remove(first_part)
            # iterate list to find connected parts, add to list or return None if can't find
            while len(part_list) > 0:
                start = self.entity_list[sorted_list[-1]].arc_end_angle
                for j in part_list:
                    found_part = False
                    if self.entity_list[j].arc_start_angle == start:
                        sorted_list.append(j)
                        found_part = True
                        part_list.remove(j)
                        break
                if not found_part:
                    return None
        elif shape == 'LINE':
            for i in part_list:
                ei = self.entity_list[i]
                if ei.shape != e_0.shape:
                    return None
                if ei.left_bottom.is_smaller_x_smaller_y(e_0.left_bottom):
                    first_part = i
                    e_0 = self.entity_list[first_part]
            sorted_list.append(first_part)
            part_list.remove(first_part)
            # iterate list to find connected parts, add to list or return None if can't find
            while len(part_list) > 0:
                start = self.entity_list[sorted_list[-1]].right_up
                for j in part_list:
                    found_part = False
                    if self.entity_list[j].left_bottom == start:
                        sorted_list.append(j)
                        found_part = True
                        part_list.remove(j)
                        break
                if not found_part:
                    return None
            # set start and end points accordingly
            for i in sorted_list:
                e = self.entity_list[i]
                e.start, e.end = e.left_bottom, e.right_up
        return sorted_list

    def merge_entities(self):
        if self.work_mode != 'dxf':
            return False
        e_list = self.get_marked_parts('entities')
        if len(e_list) < 2:
            return False
        e_list = self.sort_entity_parts(e_list)
        if e_list is None:
            m = "can't merge strange entities"
            messagebox.showwarning(m)
            return False
        e_start = self.entity_list[e_list[0]]
        e_end = self.entity_list[e_list[-1]]
        new_entity = Entity(shape=e_start.shape, center=e_start.center, radius=e_start.radius, start=e_start.start,
                            end=e_end.end, start_angle=e_start.arc_start_angle, end_angle=e_end.arc_end_angle)
        self.remove_parts_from_list(e_list, 'entities')
        self.entity_list.append(new_entity)
        self.show_entity(-1)
        return True

    def merge_net_lines(self):
        if self.work_mode != 'inp':
            return False
        '''
        # problem to get out nodes after merging
        p_list = self.get_marked_parts('net_lines')
        if len(p_list) < 2:
            return False
        p_list = self.sort_net_line_parts(p_list)
        if p_list is None:
            m = "can't merge strange lines"
            messagebox.showwarning(m)
            return False
        start_node = self.net_line_list[p_list[0]].start_node
        end_node = self.net_line_list[p_list[-1]].end_node
        entity = self.net_line_list[p_list[0]].entity
        new_line = NetLine(start_node, end_node, entity)
        # intermediate nodes
        n_list = []
        for i in range(len(p_list)-1):
            line = self.net_line_list[p_list[i]]
            n_list.append(line.end_node)
        self.remove_parts_from_list(p_list, 'net_lines')
        self.remove_parts_from_list(n_list, 'nodes')
        self.net_line_list.append(new_line)
        self.show_net_line(-1)
        return True
        '''
        return False

    def split(self, part=0, n=gv.default_split_parts):
        self.keep_state()
        if self.work_mode == 'dxf':
            changed = self.split_entity(part, n)
        elif self.work_mode == 'inp':
            changed = self.split_net_line(part, n)
        self.update_view()
        if not changed:
            self.state.pop(-1)

    # split entity_list[i] into n parts
    def split_entity(self, part=0, n=gv.default_split_parts):
        if self.work_mode != 'dxf':
            return False
        e = self.entity_list[part]
        new_part_list = []
        if e.shape == 'ARC':
            angle = (e.arc_end_angle-e.arc_start_angle) / n
            start_angle = e.arc_start_angle
            for m in range(n):
                end_angle = start_angle + angle
                arc = Entity(shape=e.shape, center=e.center, radius=e.radius, start_angle=start_angle, end_angle=end_angle)
                new_part_list.append(arc)
                start_angle = end_angle
        elif e.shape == 'LINE':
            alfa = e.start.get_alfa_to(e.end)*math.pi/180
            d = e.start.get_distance_to_point(e.end)
            step = d/n
            start = e.start
            for m in range(n):
                end = Point(start.x + step * math.cos(alfa), start.y + step * math.sin(alfa))
                line = Entity(shape='LINE', start=start, end=end)
                new_part_list.append(line)
                start = end
        elif e.shape == 'CIRCLE':
            return False
        self.remove_parts_from_list([part], 'entities')
        for m in range(n):
            self.entity_list.append(new_part_list[m])
            self.define_new_entity_color(-1)
            self.show_entity(-1)
        return True

    def split_net_line(self, part=0, n=gv.default_split_parts):
        # debug
        # print(f'selected part: {self.selected_part}   Entity: {part}')
        if self.work_mode != 'inp':
            return False
        # split net line not on entity
        if self.select_parts_mode == 'net_line':
            new_lines = []
            line = self.net_line_list[part]
            node1 = self.node_list[line.start_node]
            node2 = self.node_list[line.end_node]
            new_points = self.get_split_line_points(node1.p, node2.p, n)
            start_node = line.start_node
            for j in range(len(new_points) - 1):
                new_node = Node(new_points[j+1], entity=None)
                end_node = self.add_node_to_node_list(new_node)
                new_lines.append(NetLine(start_node, end_node, None))
                start_node = end_node
            self.remove_parts_from_list([part], 'net_lines')
            for j in range(len(new_lines)):
                self.net_line_list.append(new_lines[j])
        elif self.select_parts_mode == 'entity':
            net_lines = self.get_lines_attached_to_entity(part)
            if len(net_lines) < 1:
                # fix me
                return False
            new_lines = []
            n = n * len(net_lines)
            new_points = self.get_split_entity_points(part, n)
            line = self.net_line_list[net_lines[0]]
            entity = line.entity
            entity_nodes_list = self.entity_list[entity].nodes_list
            self.entity_list[entity].nodes_list = [entity_nodes_list[0], entity_nodes_list[-1]]
            start_node = line.start_node
            for j in range(len(new_points) - 1):
                new_node = Node(new_points[j+1], entity=entity)
                end_node = self.add_node_to_node_list(new_node)
                self.entity_list[entity].add_node_to_entity_nodes_list(end_node)
                new_lines.append(NetLine(start_node, end_node, line.entity))
                start_node = end_node
            self.remove_parts_from_list(net_lines, 'net_lines')
            for j in range(len(new_lines)):
                self.net_line_list.append(new_lines[j])
        return True

    # return list of marked parts is list
    def get_marked_parts(self, list_name):
        mark_list = []
        if list_name == 'entities':
            part_list = self.entity_list
        elif list_name == 'net_lines':
            part_list = self.net_line_list
        elif list_name == 'nodes':
            part_list = self.node_list
        for i in range(len(part_list)):
            if part_list[i].is_marked:
                mark_list.append(i)
        return mark_list

    def show_part(self, part, list_name, with_number=False):
        if list_name == 'entities':
            self.show_entity(part)
        elif list_name == 'net_lines':
            self.show_net_line(part)
        elif list_name == 'nodes':
            self.show_node(part, with_number)

    def hide_part(self, part, list_name):
        if list_name == 'entities':
            self.hide_entity(part)
        elif list_name == 'net_lines':
            self.hide_net_line(part)
        elif list_name == 'nodes':
            self.hide_node(part)

    def set_part_color(self, list_name, part, color):
        self.hide_part(part, list_name)
        if list_name == 'entities':
            self.entity_list[part].color = color
        elif list_name == 'net_lines':
            self.net_line_list[part].color = color
        elif list_name == 'nodes':
            self.node_list[part].color = color
        self.show_part(part, list_name)

    def remove_parts_from_list(self, part_list, list_name):
        original_list = None
        if list_name == 'entities':
            original_list = self.entity_list
        elif list_name == 'net_lines':
            original_list = self.net_line_list
        elif list_name == 'nodes':
            original_list = self.node_list
        part_list = sorted(part_list, reverse=True)
        for part in part_list:
            if part is None:
                return
            self.hide_part(part, list_name)
            original_list.pop(part)
        self.selected_part = None

    def get_lines_attached_to_entity(self, entity):
        net_lines = []
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            if line.entity == entity:
                net_lines.append(i)
        return net_lines

    # set all lines attached to node, and sort them by angle_to_second_node
    def set_lines_attached_to_node(self, n):
        node = self.node_list[n]
        node.attached_lines = []
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            start_node = self.node_list[line.start_node]
            end_node = self.node_list[line.end_node]
            if n == line.start_node:
                al = AttachedLine(i, line.end_node, start_node.p.get_alfa_to(end_node.p))
                node.attached_lines.append(al)
            elif n == line.end_node:
                al = AttachedLine(i, line.start_node, end_node.p.get_alfa_to(start_node.p))
                node.attached_lines.append(al)
        node.attached_lines = sorted(node.attached_lines, key=attrgetter('angle_to_second_node'))

    def set_all_nodes_expected_elements_and_exceptions(self):
        for i in range(1, len(self.node_list)):
            self.set_node_expected_elements_and_exceptions(i)
    
    # set expected elements
    # set exeptions for unattached and exceeding angles
    def set_node_expected_elements_and_exceptions(self, n):
        node = self.node_list[n]
        node.exceptions = []
        num_lines = len(node.attached_lines)
        lines_to_check = num_lines
        start_line = 0
        if num_lines < 2:
            node.exceptions.append(gv.unattached)
            node.expected_elements = 0
        else:
            num_outer_lines = 0
            for al in node.attached_lines:
                if self.net_line_list[al.line_index].is_outer_line:
                    num_outer_lines += 1
            if num_outer_lines == 0:
                node.expected_elements = len(node.attached_lines)
            elif num_outer_lines == 2:
                node.expected_elements = len(node.attached_lines)-1
                lines_to_check -= 1
            else:
                m = f'unexpected number of outer lines in set_node_expected_elements_and_exceptions'
                print(m)
                return
            if num_outer_lines == 2:
                for i in range(len(node.attached_lines)):
                    if node.attached_lines[i].is_outer_line:
                        break
                if not node.attached_lines[i].is_outer_line:
                    m = f"can't find the outer line in node: {n}"
                    print(m)
                    return
                # skeep angle between 2 outer lines
                start_line = i
                second_outer_line = node.attached_lines[(i-1) % num_lines]
                second_outer_line.is_available = False
            prev_line = node.attached_lines[start_line]
            angle = prev_line.angle_to_second_node
            for i in range(lines_to_check):
                prev_angle = angle
                line = node.attached_lines[(i+start_line+1) % num_lines]
                angle = line.angle_to_second_node
                if angle < prev_angle:
                    angle += 360
                diff_angle = angle - prev_angle
                if diff_angle < gv.min_angle_to_create_element:
                    prev_line.is_available = False
                    node.exceptions.append(gv.too_steep_angle)
                elif diff_angle > gv.max_angle_to_create_element:
                    prev_line.is_available = False
                    node.exceptions.append(gv.too_wide_angle)
                prev_line = line

    def define_new_entity_color(self, entity):
        if self.work_mode == 'inp':
            self.entity_list[entity].color = gv.weak_entity_color
        else:
            self.entity_list[entity].color = gv.default_color

    def get_exception_nodes(self):
        exception_list = []
        for i in range(1, len(self.node_list)):
            if len(self.node_list[i].exceptions) > 0:
                exception_list.append(i)
        return exception_list

    # return index of the node that can make an element counter clockwise (default) or clockwise
    def get_next_relevant_node(self, current_node_index, prev_node_index, limit_angle=True, prev_angle=None, clockwise=False):
        attached_line_list = self.node_list[current_node_index].attached_lines
        if len(attached_line_list) == 0:
            return None, None
        current_node = self.node_list[current_node_index]
        prev_node = self.node_list[prev_node_index]
        if prev_angle is None:
            prev_angle = prev_node.p.get_alfa_to(current_node.p)
        next_node = None
        net_line = None
        min_angle_to_create_elelment = gv.angle_diff_accuracy
        max_angle_to_create_elelment = 360 - gv.angle_diff_accuracy
        if limit_angle:
            min_angle_to_create_elelment = gv.min_angle_to_create_element
            max_angle_to_create_elelment = gv.max_angle_to_create_element
        best_angle = max_angle_to_create_elelment
        if clockwise:
            min_angle_to_create_elelment, max_angle_to_create_elelment = (360 - max_angle_to_create_elelment), (360 - min_angle_to_create_elelment)
            best_angle = min_angle_to_create_elelment
        for l in attached_line_list:
            if not l.is_available:
                continue
            node_index = l.second_node
            if node_index == prev_node_index:
                continue
            n = self.node_list[node_index]
            angle = current_node.p.get_alfa_to(n.p)
            if angle < prev_angle:
                angle += 360
            angle -= prev_angle
            if 0 <= angle <= 180:
                diff_angle = 180 - angle
            else:
                diff_angle = 540 - angle
            replace_best_angle = False
            if clockwise and best_angle <= diff_angle <= max_angle_to_create_elelment:
                replace_best_angle = True
            elif not clockwise and min_angle_to_create_elelment <= diff_angle <= best_angle:
                replace_best_angle = True
            if replace_best_angle:
                best_angle = diff_angle
                next_node = node_index
                net_line = l
        return next_node, net_line

    def show_progress_bar(self, max_counter=100):
        self.progress_bar = ttk.Progressbar(self.frame_1, orient=tk.HORIZONTAL, length=300, mode='determinate', maximum=max_counter)
        self.progress_bar.pack(side=tk.TOP, fill=tk.BOTH, pady=5)

    def hide_progress_bar(self):
        if self.progress_bar is not None:
            self.progress_bar.destroy()
            self.progress_bar = None

    def get_duplicated_entities(self):
        duplicate_entities_list = []
        c = len(self.entity_list)
        self.show_text_on_screen('checking duplicated entities')
        self.show_progress_bar(c)
        for i in range(c):
            ei = self.entity_list[i]
            for j in range(i):
                ej = self.entity_list[j]
                if ei.is_equal(ej):
                    duplicate_entities_list.append(ei)
                    break
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()
        return duplicate_entities_list

    def set_all_nodes_attached_line_list(self):
        c = len(self.node_list)
        self.show_text_on_screen('matching lines to nodes')
        self.show_progress_bar(c)
        for i in range(1, len(self.node_list)):
            self.set_lines_attached_to_node(i)
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()

    def mark_outer_lines(self):
        n = self.get_bottom_left_node()
        nodes_outer_list = [n]
        alfa = 0
        line = AttachedLine()
        line.second_node = n
        next_node_index = 0
        while next_node_index != n and len(nodes_outer_list) <= len(self.net_line_list):
            next_node_index, line = self.get_next_relevant_node(line.second_node, 0, limit_angle=False, prev_angle=alfa,
                                                                clockwise=True)
            if line is None:
                print(f"can't set outer lines")
                return
            line.is_outer_line = True
            self.net_line_list[line.line_index].is_outer_line = True
            alfa = line.angle_to_second_node
            nodes_outer_list.append(next_node_index)
        return nodes_outer_list

    def get_unattached_nodes(self, set_nodes_lines=True):
        tmp_list = []
        if set_nodes_lines:
            self.set_nodes_attached_lines_and_exception()
        c = len(self.node_list)
        self.show_text_on_screen('checking unattached nodes')
        self.show_progress_bar(c)
        for i in range(1, c):
            node = self.node_list[i]
            if gv.unattached in node.exceptions:
                self.node_list[i].color = gv.invalid_node_color
                tmp_list.append(i)
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()
        if len(tmp_list) > 0:
            m = f"{len(tmp_list)} unattached nodes: {tmp_list}"
            print(m)
            messagebox.showwarning("Warning", m)
        return tmp_list

    # return index of node in node_list with same p, None if it's a new node
    def get_index_of_node_with_point(self, p):
        for i in range(len(self.node_list)):
            node = self.node_list[i]
            if node.p.is_equal(p):
                return i
        return None

    def add_node_to_node_list(self, n):
        i = self.get_index_of_node_with_point(n.p)
        if i is None:
            self.node_list.append(n)
            i = len(self.node_list) - 1
        return i

    # set nodes out of entities edges
    def set_nodes_list_from_dxf(self):
        self.node_list = [Node()]
        c = len(self.entity_list)
        self.show_text_on_screen('setting nodes')
        self.show_progress_bar(c)
        for i in range(c):
            e = self.entity_list[i]
            if e.shape == 'CIRCLE':
                continue
            self.set_entity_edge_nodes(i)
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()

    # set net with nodes only on entity edges
    def set_initial_net(self):
        self.node_list = [Node()]
        self.reset_net()
        c = len(self.entity_list)
        self.show_text_on_screen('setting initial net')
        self.show_progress_bar(c)
        for i in range(c):
            e = self.entity_list[i]
            if e.shape == 'CIRCLE':
                continue
            self.set_entity_edge_nodes(i)
            start_node = e.nodes_list[0]
            end_node = e.nodes_list[1]
            line = NetLine(start_node, end_node, i)
            self.net_line_list.append(line)
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()
        # debug
        #self.print_node_list()
        #self.print_line_list()

    # debug
    def print_node_list(self):
        print('nodes:')
        for i in range(1, len(self.node_list)):
            n = self.node_list[i]
            print(f'{i}: {n.p.convert_into_tuple()}   entity: {n.entity}')

    # debug
    def print_line_list(self):
        print('lines:')
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            print(f'{i}: start node: {line.start_node}   end node: {line.end_node}   entity: {line.entity}')

    # debug
    def print_elements(self, element_list):
        print('elements:')
        for i in range(len(element_list)):
            e = element_list[i]
            print(f'{i+1}: {e.nodes}')

    # debug
    def print_nodes_exceptions(self, node_list):
        print('Exception nodes:')
        for n in node_list:
            print(f'{n}: {self.node_list[n].exceptions}')

    # debug
    def print_nodes_expected_elements(self):
        print('Expected elements for each node:')
        for i in range(1, len(self.node_list)):
            print(f'{i}: {self.node_list[i].expected_elements}')

    def set_net(self):
        self.create_net_element_list()
        self.show_elements = True
        self.show_net = True
        self.update_view()

    def set_nodes_attached_lines_and_exception(self):
        self.set_all_nodes_attached_line_list()
        nodes_outer_list = self.mark_outer_lines()
        #debug
        #print(nodes_outer_list)
        self.set_all_nodes_expected_elements_and_exceptions()

    def create_net_element_list(self):
        self.set_nodes_attached_lines_and_exception()
        unattaced_list = self.get_unattached_nodes(False)
        if len(unattaced_list) > 0:
            return
        c = len(self.node_list)
        self.show_text_on_screen('creating net elements')
        self.show_progress_bar(c)
        # debug
        #self.print_node_list()
        #self.print_line_list()
        #self.print_nodes_expected_elements()
        element_list = []
        exception_element_list = []
        # iterate all nodes
        for i in range(1, len(self.node_list)):
            node = self.node_list[i]
            attached_lines = node.attached_lines
            num_lines = len(attached_lines)
            # iterate all nodes attached_lines
            for j in range(num_lines):
                fist_node = i
                attached_line = node.attached_lines[j]
                if not attached_line.is_available:
                    continue
                node_index = attached_line.second_node
                new_element_nodes = [fist_node]
                prev_node_index = fist_node
                # try to set a new element starting from node[i] to next_node
                while node_index is not None:
                    new_element_nodes.append(node_index)
                    next_node_index, line = self.get_next_relevant_node(node_index, prev_node_index)
                    if line is not None:
                        if not line.is_available:
                            break
                        line.is_available = False
                    if next_node_index == fist_node:
                        break
                    prev_node_index = node_index
                    node_index = next_node_index
                if next_node_index == fist_node and len(new_element_nodes) > 2:
                    element = Element()
                    element.nodes = new_element_nodes
                    if len(new_element_nodes) <= gv.max_nodes_to_create_element:
                        element_list.append(element)
                        for element_node in new_element_nodes:
                            self.node_list[element_node].expected_elements -= 1
                    else:
                        exception_element_list.append(element)
            self.node_list[i].attached_lines = []
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()
        self.element_list = element_list
        # debug
        #self.print_nodes_expected_elements()
        exception_nodes = self.get_exception_nodes()
        m = None
        if len(exception_nodes) > 0:
            m = f'{len(exception_nodes)} exception nodes    '
            print(m)
            self.print_nodes_exceptions(exception_nodes)
            messagebox.showwarning("Warning", m)
        if len(exception_element_list) > 0:
            m = f'{len(exception_element_list)} elements with more than {gv.max_nodes_to_create_element} nodes'
            print(m)
            self.print_elements(exception_element_list)
            messagebox.showwarning("Warning", m)
        if m is None:
            print(f'SUCCESS: net created with {len(element_list)} elements\n')
        # debug
        #self.print_nodes_expected_elements()
        self.print_elements(self.element_list)

    def save_inp(self):
        self.create_net_element_list()
        filename = filedialog.asksaveasfilename(parent=self.window_main, initialdir="./data files/", title="Select file",
                                                initialfile='Fabian', defaultextension=".inp",
                                                filetypes=(("inp files", "*.inp"), ("all files", "*.*")))
        if filename == '':
            return
        f = open(filename, 'w')
        f.write('*Node\n')
        for i in range(1, len(self.node_list)):
            n = self.node_list[i]
            s = f'{i},    {n.p.x}, {n.p.y}, 0\n'
            f.write(s)
        element_3_list = []
        element_4_list = []
        for i in range(len(self.element_list)):
            e = self.element_list[i]
            if len(e.nodes) == 3:
                element_3_list.append(e.nodes)
            else:
                element_4_list.append(e.nodes)
        element_index = 1
        if len(element_3_list) > 0:
            f.write('*Element, type=R3D3\n')
            for i in range(len(element_3_list)):
                e = element_3_list[i]
                self.write_element_to_file(f, element_index, e)
                element_index += 1
        if len(element_4_list) > 0:
            f.write('*Element, type=R3D4\n')
            for i in range(len(element_4_list)):
                e = element_4_list[i]
                self.write_element_to_file(f, element_index, e)
                element_index += 1
        f.close()

    def write_element_to_file(self, f, index, e):
        s = f'{index},    '
        for j in range(len(e)-1):
            s += f'{e[j]}, '
        s += f'{e[-1]}\n'
        f.write(s)

    def save_as(self):
        menu = tk.Menu(self.board, tearoff=0)
        menu.add_command(label="DATA", command=lambda: self.save_data())
        menu.add_command(label="INP", command=lambda: self.save_inp())
        menu.add_command(label="DXF", command=lambda: self.save_dxf())
        menu.add_separator()
        menu.add_command(label="Quit")
        x = self.frame_2.winfo_pointerx()
        y = self.frame_2.winfo_pointery()
        menu.post(x, y)

    def save_data(self):
        self.keep_state()
        state = self.state[-1]
        data = {
            "entity_list": state.entity_list,
            "node_list": state.node_list,
            "net_line_list": state.net_line_list,
            "element_list": state.element_list,
            "work_mode": state.work_mode,
            "select_parts_mode": state.select_parts_mode,
            "show_entities": state.show_entities,
            "show_nodes": state.show_nodes,
            "show_elements": state.show_elements,
            "show_node_number": state.show_node_number,
            "show_net": state.show_net,
            "scale": state.scale
        }
        # debug
        #self.print_node_list()
        #self.print_line_list()
        self.save_json(data)

    def save_dxf(self):
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        for e in self.entity_list:
            if e.shape == 'LINE':
                msp.add_line((e.start.x, e.start.y), (e.end.x, e.end.y))
            elif e.shape == 'ARC':
                msp.add_arc((e.center.x, e.center.y), e.radius, e.arc_start_angle, e.arc_end_angle)
            elif e.shape == 'CIRCLE':
                msp.add_circle((e.center.x, e.center.y), e.radius)
        default_file_name = f'Fabian'
        filename = filedialog.asksaveasfilename(parent=self.window_main, initialdir="./data files/", title="Select file",
                                                initialfile=default_file_name, defaultextension=".dxf",
                                                filetypes=(("dxf files", "*.dxf"), ("all files", "*.*")))
        if filename == '':
            return
        doc.saveas(filename)

    def load(self):
        filename = filedialog.askopenfilename(parent=self.window_main, initialdir="./data files/",
                                              title="Select file",
                                              filetypes=(("Json files", "*.json"), ("DXF files", "*.dxf"), ("all files", "*.*")))
        if filename == '':
            return
        self.reset_board()
        i = filename.find('.')
        filetype = filename[i+1:].lower()
        if filetype == 'dxf':
            doc = ezdxf.readfile(filename)
            self.convert_doc_to_entity_list(doc)
            self.center_view()
            self.set_initial_net()
            # remove me
            self.set_longitude()
            print(f'{len(self.entity_list)} Entities in {filetype} file')
            d_list = self.get_duplicated_entities()
            self.hide_text_on_screen()
            if len(d_list) > 0:
                m = f'Removed {len(d_list)} duplicated entities'
                print(m)
                messagebox.showwarning("Warning", m)
                for e in d_list:
                    self.entity_list.remove(e)
            else:
                # debug
                print('no duplicated entities')
            self.change_work_mode('dxf')
        elif filetype == 'json':
            data = self.load_json(filename=filename)
            self.node_list = []
            entity_list = data.get("entity_list")
            node_list = data.get("node_list")
            net_line_list = data.get("net_line_list")
            element_list = data.get("element_list")
            for t in entity_list:
                e = Entity()
                e.get_data_from_tuple(t)
                self.entity_list.append(e)
            for t in node_list:
                n = Node()
                n.get_data_from_tuple(t)
                self.node_list.append(n)
            for t in net_line_list:
                line = NetLine()
                line.get_data_from_tuple(t)
                self.net_line_list.append(line)
            for t in element_list:
                element = Element()
                element.get_data_from_tuple(t)
                self.element_list.append(element)
            self.work_mode = data.get('work_mode')
            self.select_parts_mode = data.get('select_parts_mode')
            self.show_entities = data.get('show_entities')
            self.show_nodes = data.get('show_nodes')
            self.show_elements = data.get('show_elements')
            self.show_node_number = data.get('show_node_number')
            self.show_net = data.get('show_net')
            self.scale = data.get('scale')
        self.set_accuracy()
        self.center_view()
        self.update_view()
        # debug
        #self.print_node_list()
        #self.print_line_list()

    def center_view(self):
        self.hide_text_on_screen()
        x, y = self.get_center()
        if x is None:
            self.set_screen_position(self.center.x, self.center.y)
        else:
            self.set_screen_position(x, y)

    # return x, y of center in canvas coordinates (default), or dxf coordinates, by entities (default) or nodes
    def get_center(self, canvas_coordinates=True, by_nodes=False):
        if by_nodes:
            if len(self.node_list) < 2:
                left = right = bottom = top = 0
            else:
                left = right = self.node_list[1].p.x
                bottom = top = self.node_list[1].p.x
                for i in range(1, len(self.node_list)):
                    n = self.node_list[i]
                    if n.p.x < left:
                        left = n.p.x
                    elif n.p.x > right:
                        right = n.p.x
                    if n.p.y < bottom:
                        bottom = n.p.y
                    elif n.p.y > top:
                        top = n.p.y
        # by entities
        else:
            if len(self.entity_list) == 0:
                left = right = bottom = top = 0
            else:
                left = self.entity_list[0].left_bottom.x
                right = self.entity_list[0].right_up.x
                top = self.entity_list[0].right_up.y
                bottom = self.entity_list[0].left_bottom.y
                for e in self.entity_list:
                    if e.left_bottom.x < left:
                        left = e.left_bottom.x
                    if e.left_bottom.y < bottom:
                        bottom = e.left_bottom.y
                    if e.right_up.x > right:
                        right = e.right_up.x
                    if e.right_up.y > top:
                        top = e.right_up.y
        x, y = (left+right)/2, (bottom+top)/2
        if canvas_coordinates:
            x, y = self.convert_xy_to_screen(x, y)
        return x, y

    def set_longitude(self):
        if len(self.node_list) < 2:
            return None
        shape = None
        longest_line = 0
        longitude_line = None
        x, y = self.get_center(canvas_coordinates=False, by_nodes=True)
        c = Point(x, y)
        left_top = bottom_left = right_bottom = top_right = 0
        d_left_top = d_bottom_left = d_right_bottom = d_top_right = 0
        for e in self.entity_list:
            if e.shape == 'LINE' or e.shape == 'ARC':
                d_line = e.start.get_distance_to_point(e.end)
                if d_line > longest_line:
                    longest_line = d_line
                    longitude_line = e.left_bottom.get_alfa_to(e.right_up)
                    shape = e.shape
        for n in self.node_list:
            angle = c.get_alfa_to(n.p)
            d = c.get_distance_to_point(n.p)
            if 0 < angle <= 90 and d > d_top_right:
                d_top_right = d
                top_right = n.p
            elif 90 < angle <= 180 and d > d_left_top:
                d_left_top = d
                left_top = n.p
            elif 180 < angle <= 270 and d > d_bottom_left:
                d_bottom_left = d
                bottom_left = n.p
            elif (angle == 0 or 270 < angle <= 360) and d > d_right_bottom:
                d_right_bottom = d
                right_bottom = n.p
        d_corners = 0
        longitude_corners = 0
        d = left_top.get_distance_to_point(bottom_left)
        angle = left_top.get_alfa_to(bottom_left)
        if d > d_corners:
            d_corners = d
            longitude_corners = angle
        d = bottom_left.get_distance_to_point(right_bottom)
        angle = bottom_left.get_alfa_to(right_bottom)
        if d > d_corners:
            d_corners = d
            longitude_corners = angle
        d = right_bottom.get_distance_to_point(top_right)
        angle = right_bottom.get_alfa_to(top_right)
        if d > d_corners:
            d_corners = d
            longitude_corners = angle
        d = top_right.get_distance_to_point(left_top)
        angle = top_right.get_alfa_to(left_top)
        if d > d_corners:
            d_corners = d
            longitude_corners = angle
        # debug
        print(f'longitude corners: {longitude_corners}   left_top: {left_top.convert_into_tuple()}   bottom_left: {bottom_left.convert_into_tuple()}   '
              f'right_bottom: {right_bottom.convert_into_tuple()}   top_right: {top_right.convert_into_tuple()}')
        print(f'longest - {shape}   d: {longest_line}   longitude: {longitude_line}\n')
        return longitude_line

    def get_bottom_left_node(self):
        if len(self.node_list) < 2:
            return 0
        node = 1
        p = self.node_list[node].p
        for i in range(1, len(self.node_list)):
            if self.node_list[i].p.is_smaller_x_smaller_y(p, by_x=False):
                p = self.node_list[i].p
                node = i
        return node

    def mark_selected_entity(self):
        if self.selected_part_mark is None:
            return
        self.keep_state()
        i = self.selected_part
        e = self.entity_list[i]
        e.is_marked = True
        self.set_entity_color(i, gv.marked_entity_color)

    def mark_all_entities(self):
        self.keep_state()
        i = 0
        for e in self.entity_list:
            if not e.is_marked:
                e.is_marked = True
                self.set_entity_color(i, gv.marked_entity_color)
            i += 1

    def unmark_all_entities(self):
        self.keep_state()
        i = 0
        for e in self.entity_list:
            if e.is_marked:
                e.is_marked = False
                self.set_entity_color(i, gv.default_color)
            i += 1

    def unmark_selected_entity(self):
        if self.selected_part_mark is None:
            return
        self.keep_state()
        i = self.selected_part
        e = self.entity_list[i]
        e.is_marked = False
        self.set_entity_color(i, gv.default_color)

    def remove_marked_entities_from_list(self):
        self.keep_state()
        temp_list = []
        for e in self.entity_list:
            if not e.is_marked:
                temp_list.append(e)
        for e in temp_list:
            e.board_part = None
        self.entity_list = temp_list
        self.selected_part = None
        self.board.delete('all')
        self.show_dxf_entities()

    def remove_non_marked_entities_from_list(self):
        self.keep_state()
        temp_list = []
        for e in self.entity_list:
            if e.is_marked:
                temp_list.append(e)
        for e in temp_list:
            e.is_marked = False
            e.board_part = None
            e.color = gv.default_color
        self.entity_list = temp_list
        self.remove_temp_line()
        self.selected_part = None
        self.board.delete('all')
        self.show_dxf_entities()

    def remove_selected_part_from_list(self):
        if self.selected_part is None:
            return
        self.keep_state()
        changed = False
        if self.select_parts_mode == 'entity' and self.work_mode == 'dxf':
            changed = True
            self.remove_parts_from_list([self.selected_part], 'entities')
        elif self.select_parts_mode == 'net_line' and self.work_mode == 'inp':
            changed = True
            self.remove_parts_from_list([self.selected_part], 'net_lines')
        if not changed:
            self.state.pop(-1)

    def remove_temp_line(self):
        if self.new_line_edge[1] is not None:
            self.board.delete(self.new_line_edge_mark[1])
            self.new_line_edge[1] = None
            self.board.delete(self.new_line_mark)
        if self.new_line_edge[0] is not None:
            self.board.delete(self.new_line_edge_mark[0])
            self.new_line_edge[0] = None
            self.board.delete(self.temp_line_mark)

    def add_line(self):
        p1 = self.new_line_edge[0]
        p2 = self.new_line_edge[1]
        if p2 is None:
            return
        self.keep_state()
        if self.work_mode == 'dxf':
            self.add_line_to_entity_list(p1, p2)
        elif self.work_mode == 'inp':
            self.add_line_to_net_list(p1, p2)
        self.board.delete(self.new_line_edge_mark[0])
        self.board.delete(self.new_line_edge_mark[1])
        self.board.delete(self.new_line_mark)
        self.new_line_edge[0] = None
        self.new_line_edge[1] = None

    def add_line_to_net_list(self, p1, p2):
        if self.work_mode != 'inp':
            return
        start_node = self.get_index_of_node_with_point(p1)
        end_node = self.get_index_of_node_with_point(p2)
        if start_node is None or end_node is None:
            # debug
            print(f"in add line to net list, no mach node for points {p1.convert_into_tuple()}   {p2.convert_into_tuple()}")
        line = NetLine(start_node, end_node)
        self.net_line_list.append(line)
        self.show_net_line(-1)

    def add_line_to_entity_list(self, p1, p2):
        if self.work_mode != 'dxf':
            return
        e = Entity('LINE', start=p1, end=p2)
        e.is_marked = False
        e.color = gv.default_color
        self.entity_list.append(e)
        self.show_entity(-1)

    def get_first_visible_entity(self):
        for i in range(len(self.entity_list)):
            if self.entity_list[i].board_part is not None:
                return i
        return None

    def find_nearest_entity(self, p, only_visible=False):
        min_d_index = 0
        if only_visible:
            min_d_index = self.get_first_visible_entity()
        if len(self.entity_list) == 0 or min_d_index is None:
            return None, None
        min_d, nearest_point = self.get_distance_from_entity_and_nearest_point(p, min_d_index, only_visible)
        for i in range(len(self.entity_list)):
            if only_visible and self.entity_list[i].board_part is None:
                continue
            d, nearest_point = self.get_distance_from_entity_and_nearest_point(p, i, only_visible)
            if d < min_d:
                min_d_index = i
                min_d = d
        return min_d_index, min_d

    def get_first_visible_net_line(self):
        for i in range(len(self.net_line_list)):
            if self.net_line_list[i].board_part is not None:
                return i
        return None

    def find_nearest_net_line(self, p, only_visible=False):
        min_d_index = 0
        if only_visible:
            min_d_index = self.get_first_visible_net_line()
        if len(self.net_line_list) == 0 or min_d_index is None:
            return None, None
        start_node = self.net_line_list[min_d_index].start_node
        end_node = self.net_line_list[min_d_index].end_node
        p1 = self.node_list[start_node].p
        p2 = self.node_list[end_node].p
        min_d, nearest_point = self.get_distance_from_line_and_nearest_point(p, p1, p2)
        for i in range(len(self.net_line_list)):
            if only_visible and self.net_line_list[i].board_part is None:
                continue
            start_node = self.net_line_list[i].start_node
            end_node = self.net_line_list[i].end_node
            p1 = self.node_list[start_node].p
            p2 = self.node_list[end_node].p
            d, nearest_point = self.get_distance_from_line_and_nearest_point(p, p1, p2)
            if d < min_d:
                min_d_index = i
                min_d = d
        return min_d_index, min_d

    # return the distance of Point p from entity[i]
    def get_distance_from_entity_and_nearest_point(self, p, i, only_visible=False):
        e = self.entity_list[i]
        if only_visible and e.board_part is None:
            return None, None
        d = None
        nearest_point = None
        if e.shape == 'CIRCLE':
            d = math.fabs(e.center.get_distance_to_point(p)-e.radius)
            alfa = e.center.get_alfa_to(p)*math.pi/180
            if alfa is None:
                d = e.radius
                alfa = 0
            px = e.center.x+math.cos(alfa)*e.radius
            py = e.center.y+math.sin(alfa)*e.radius
            nearest_point = Point(px, py)
        elif e.shape == 'ARC':
            alfa = e.center.get_alfa_to(p)
            if alfa is None:
                d = e.radius
                nearest_point = e.start
            if e.arc_end_angle > 360 and alfa < e.arc_start_angle:
                alfa += 360
            if e.arc_start_angle <= alfa <= e.arc_end_angle:
                d = math.fabs(e.center.get_distance_to_point(p) - e.radius)
                alfa = alfa*math.pi/180
                px = e.center.x + math.cos(alfa) * e.radius
                py = e.center.y + math.sin(alfa) * e.radius
                nearest_point = Point(px, py)
            else:
                mid_angle = (e.arc_start_angle + e.arc_end_angle)/2
                if mid_angle < 180:
                    mid_angle += 360
                a1 = (mid_angle-180)
                if a1 < alfa < mid_angle:
                    d = e.start.get_distance_to_point(p)
                    nearest_point = e.start
                else:
                    d = e.end.get_distance_to_point(p)
                    nearest_point = e.end
        elif e.shape == 'LINE':
            d, nearest_point = self.get_distance_from_line_and_nearest_point(p, e.start, e.end)
        return round(d, gv.accuracy), nearest_point

    def get_distance_from_line_and_nearest_point(self, p, line_start, line_end):
        alfa = line_start.get_alfa_to(line_end)
        endx = math.fabs(get_shifted_point(line_end, line_start, -alfa).x)
        p = get_shifted_point(p, line_start, -alfa)
        x = p.x
        if 0 <= x <= endx:
            d = math.fabs(p.y)
            alfa = alfa * math.pi / 180
            px = math.cos(alfa)*x+line_start.x
            py = math.sin(alfa)*x+line_start.y
            nearest_point = Point(px, py)
        elif x < 0:
            d = p.get_distance_to_point(Point(0, 0))
            nearest_point = line_start
        else:
            d = p.get_distance_to_point(Point(endx, 0))
            nearest_point = line_end
        return round(d, gv.accuracy), nearest_point

    def get_net_line_by_board_part(self, board_part):
        i = 0
        for i in range(len(self.net_line_list)):
            if self.net_line_list[i].board_part == board_part:
                return i
        return None

    def get_entity_by_board_part(self, board_part):
        i = 0
        for i in range(len(self.entity_list)):
            if self.entity_list[i].board_part == board_part:
                return i
        return None

    def hide_node(self, part):
        n = self.node_list[part]
        if n.board_part is not None:
            self.board.delete(n.board_part)
            self.node_list[part].board_part = None
        if n.board_text is not None:
            self.board.delete(n.board_text)
            self.node_list[part].board_text = None

    def hide_all_nodes(self):
        for i in range(len(self.node_list)):
            self.hide_node(i)

    def show_node(self, i, with_number=False):
        n = self.node_list[i]
        if n.board_part is None:
            part = self.draw_circle(n.p, gv.node_mark_radius/self.scale, n.color)
            self.node_list[i].board_part = part
        if with_number and n.board_text is None:
            x, y = self.convert_xy_to_screen(n.p.x, n.p.y)
            x += 7
            y += 7
            self.node_list[i].board_text = self.board.create_text(x, y, text=i, fill=gv.text_color, justify=tk.RIGHT)

    def show_all_nodes(self):
        for i in range(1, len(self.node_list)):
            self.show_node(i, self.show_node_number)

    def show_entity(self, i):
        part = None
        if self.entity_list[i].board_part is not None:
            return
        if self.entity_list[i].shape == 'LINE':
            part = self.draw_line(self.entity_list[i].start, self.entity_list[i].end, self.entity_list[i].color)
        elif self.entity_list[i].shape == 'CIRCLE':
            part = self.draw_circle(self.entity_list[i].center, self.entity_list[i].radius, self.entity_list[i].color)
        elif self.entity_list[i].shape == 'ARC':
            part = self.draw_arc(self.entity_list[i].center, self.entity_list[i].radius, self.entity_list[i].arc_start_angle,
                                   self.entity_list[i].arc_end_angle, self.entity_list[i].color)
        self.entity_list[i].board_part = part

    def show_element(self, e):
        element = self.element_list[e]
        nodes = element.nodes
        if element.board_part is None:
            poly = []
            for n in nodes:
                poly.append(self.node_list[n].p)
            self.element_list[e].board_part = self.draw_polygon(poly)

    def hide_element(self, e):
        part = self.element_list[e].board_part
        if part is not None:
            self.board.delete(part)
            self.element_list[e].board_part = None

    def show_all_elements(self):
        for i in range(len(self.element_list)):
            self.show_element(i)

    def hide_all_elements(self):
        for i in range(len(self.element_list)):
            self.hide_element(i)

    def show_net_line(self, i):
        line = self.net_line_list[i]
        p1 = self.node_list[line.start_node].p
        p2 = self.node_list[line.end_node].p
        if line.board_part is None:
            line.board_part = self.draw_line(p1, p2, line.color)

    def hide_net_line(self, part):
        line = self.net_line_list[part]
        if line.board_part is not None:
            self.board.delete(line.board_part)
            line.board_part = None

    def show_all_net_lines(self):
        for i in range(len(self.net_line_list)):
            self.show_net_line(i)

    def hide_all_net_lines(self):
        for i in range(len(self.net_line_list)):
            self.hide_net_line(i)

    def show_dxf_entities(self):
        for i in range(len(self.entity_list)):
            self.show_entity(i)

    def hide_entity(self, part):
        if self.entity_list[part].board_part is None:
            return
        self.board.delete(self.entity_list[part].board_part)
        self.entity_list[part].board_part = None

    def hide_dxf_entities(self):
        for i in range(len(self.entity_list)):
            self.hide_entity(i)

    def set_entity_color(self, part, color):
        self.hide_entity(part)
        self.entity_list[part].color = color
        self.show_entity(part)

    def reset_net(self, keep_state=False):
        if keep_state:
            self.keep_state()
        self.hide_all_net_lines()
        self.hide_all_elements()
        self.net_line_list = []

    def set_all_dxf_entities_color(self, color):
        for i in range(len(self.entity_list)):
            self.set_entity_color(i, color)

    def mark_entity(self, i):
        b = self.board.bbox(self.entity_list[i].board_part)
        self.selected_part_mark = self.board.create_rectangle(b)

    def mark_net_line(self, i):
        b = self.board.bbox(self.net_line_list[i].board_part)
        self.selected_part_mark = self.board.create_rectangle(b)

    def remove_selected_part_mark(self):
        if self.selected_part_mark is None:
            return
        else:
            self.board.delete(self.selected_part_mark)
            self.selected_part_mark = None

    def convert_doc_to_entity_list(self, doc=None):
        if doc is None:
            return
        msp = doc.modelspace()
        for shape in shapes:
            for dxf_entity in msp.query(shape):
                e = None
                if shape == 'LINE':
                    p1 = Point(dxf_entity.dxf.start[0], dxf_entity.dxf.start[1])
                    p2 = Point(dxf_entity.dxf.end[0], dxf_entity.dxf.end[1])
                    e = Entity(shape='LINE', start=p1, end=p2)
                elif shape == 'CIRCLE':
                    center = Point(dxf_entity.dxf.center[0], dxf_entity.dxf.center[1])
                    radius = dxf_entity.dxf.radius
                    e = Entity(shape='CIRCLE', center=center, radius=radius)
                elif shape == 'ARC':
                    center = Point(dxf_entity.dxf.center[0], dxf_entity.dxf.center[1])
                    radius = dxf_entity.dxf.radius
                    start_angle = dxf_entity.dxf.start_angle % 360
                    end_angle = dxf_entity.dxf.end_angle
                    e = Entity(shape='ARC', center=center, radius=radius, start_angle=start_angle, end_angle=end_angle)
                if e is not None:
                    self.entity_list.append(e)

    def zoom(self, factor):
        self.hide_text_on_screen()
        x, y = self.get_center_keyx_keyy()
        x, y = self.convert_keyx_keyy_to_xy(x, y)
        self.scale = round(self.scale*factor, 1)
        x, y = self.convert_xy_to_screen(x, y)
        self.set_screen_position(x, y)
        self.update_view()

    def get_first_entity_to_set_accuracy(self):
        for i in range(len(self.entity_list)):
            if self.entity_list[i].start is not None:
                return i
        return None
    
    def set_accuracy(self):
        zeros = 0
        i = self.get_first_entity_to_set_accuracy()
        if len(self.entity_list) > 0:
            max = self.entity_list[i].start.x
            min = self.entity_list[i].start.y
            for e in self.entity_list:
                if e.start is not None:
                    m = e.start.x
                    if m > max:
                        max = m
                    if m < min:
                        min = m
                    m = e.start.y
                    if m > max:
                        max = m
                    if m < min:
                        min = m
                if e.end is not None:
                    m = e.end.x
                    if m > max:
                        max = m
                    if m < min:
                        min = m
                    m = e.end.y
                    if m > max:
                        max = m
                    if m < min:
                        min = m
                if (max-min) > 1:
                    break
            if (max-min) < 1:
                s = str(max-min)
                p = s.find('.')
                s = s[p+1:]
                i = 0
                while i < len(s) and s[i] == '0':
                    i += 1
                zeros = i
        gv.accuracy = zeros+3
        # debug
        print(f'set accuracy: 1/{int(math.pow(10, gv.accuracy))}')

    def update_view(self):
        self.hide_dxf_entities()
        self.hide_all_net_lines()
        self.hide_all_nodes()
        self.hide_all_elements()
        if self.show_elements:
            self.show_all_elements()
        if self.show_entities:
            self.show_dxf_entities()
        if self.show_nodes:
            self.show_all_nodes()
        if self.show_net:
            self.show_all_net_lines()            
        self.window_main.update()

            