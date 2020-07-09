from board import *
import ezdxf
import math
from tkinter import messagebox
from operator import attrgetter, itemgetter

shapes = {'CIRCLE', 'LINE', 'ARC'}


class Entity:
    def __init__(self, shape=None, center=None, radius=None, start=None, end=None, start_angle=None, end_angle=None, 
                 color=gv.default_color, is_part_of_dxf=True):
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
        self.is_marked = False
        self.board_part = None
        self.color = color
        self.is_part_of_dxf = is_part_of_dxf

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
        t = (self.shape, center, self.radius, self.arc_start_angle, self.arc_end_angle, start, end, self.color, self.is_part_of_dxf)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 9:
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
        self.is_part_of_dxf = t[8]
        self.set_arc()
        self.set_left_bottom_right_up()


class Neighbor:
    def __init__(self, node_index=0, angle_from_p=0):
        self.node_index = node_index
        self.angle_from_p = angle_from_p
        self.is_part_of_element = False

    def convert_into_tuple(self):
        t = (self.node_index, self.angle_from_p, self.is_part_of_element)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 3:
            print(f"tuple doesn't match Neighbor type: {t}")
            return
        self.node_index = t[0]
        self.angle_from_p = t[1]
        self.is_part_of_element = t[2]


class Node:
    def __init__(self, point=None):
        if point is None:
            point = Point()
        self.p = point
        self.entities_list = []
        self.neighbors_list = []
        self.board_part = None
        self.color = gv.node_color

    def is_in_neighbors_list(self, i):
        for n in self.neighbors_list:
            if i == n:
                return True
        return False

    def is_in_entities_list(self, i):
        for e in self.entities_list:
            if i == e:
                return True
        return False

    def convert_into_tuple(self):
        tuple_neighbors_list = []
        for n in self.neighbors_list:
            tuple_neighbors_list.append(n.convert_into_tuple())
        t = (self.p.convert_into_tuple(), self.entities_list, tuple_neighbors_list)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 3:
            print(f"tuple doesn't match Node type: {t}")
            return
        self.p.get_data_from_tuple(t[0])
        self.entities_list = t[1]
        neighbors_list = []
        for i in t[2]:
            n = Neighbor()
            n.get_data_from_tuple(i)
            neighbors_list.append(n)
        self.neighbors_list = neighbors_list


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

        self.dxfDoc = None
        self.entity_list = []
        self.node_list = [Node()]
        self.element_list = []
        self.net_line_list = []
        self.select_mode = gv.default_select_mode
        self.work_mode = gv.default_work_mode
        self.selected_entity = 0
        self.selected_entity_mark = None
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
        self.show_net = True

        self.board.bind('<Motion>', self.motion)
        self.board.bind('<Button-1>', self.mouse_1_pressed)
        self.board.bind('<B1-Motion>', self.mouse_1_motion)
        self.board.bind('<ButtonRelease-1>', self.mouse_1_released)
        self.board.bind('<Button-3>', self.mouse_3_pressed)

    def reset_board(self):
        self.board.delete('all')
        self.set_screen_position(self.center.x, self.center.y)
        self.dxfDoc = None
        self.entity_list = []
        self.node_list = [Node()]
        self.element_list = []
        self.net_line_list = []
        self.select_mode = gv.default_select_mode
        self.work_mode = gv.default_work_mode
        self.selected_entity = 0
        self.selected_entity_mark = None
        self.new_line_edge = [None, None]
        self.new_line_edge_mark = [None, None]
        self.new_line_mark = None
        self.temp_line_mark = None
        self.temp_rect_start_point = None
        self.temp_rect_mark = None

    def mouse_1_pressed(self, key):
        if self.temp_rect_mark is not None:
            self.board.delete(self.temp_rect_mark)
        x, y = self.convert_screen_to_xy(key.x, key.y)
        if self.selected_entity_mark is None:
            self.temp_rect_start_point = Point(x, y)
            return
        e = self.entity_list[self.selected_entity]
        if self.select_mode == 'edge':
            d_left = e.left_bottom.get_distance_from_point(Point(x, y))
            d_right = e.right_up.get_distance_from_point(Point(x, y))
            if d_left < d_right:
                p = e.left_bottom
            else:
                p = e.right_up
        else:
            d, p = self.get_distance_from_entity_and_nearest_point(Point(x, y), self.selected_entity)
        # first point
        if self.new_line_edge[0] is None:
            self.new_line_edge[0] = p
            self.new_line_edge_mark[0] = self.draw_circle(p, gv.edge_line_mark_radius/self.scale)
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

        # second point on the same entity
        elif self.new_line_edge[0] == e.left_bottom or self.new_line_edge[0] == e.right_up:
            return

        # second point
        else:
            self.board.delete(self.temp_line_mark)
            if self.new_line_edge[1] is None:
                self.new_line_edge[1] = p
                self.new_line_edge_mark[1] = self.draw_circle(p, gv.edge_line_mark_radius/self.scale)
                self.new_line_mark = self.draw_line(self.new_line_edge[0], self.new_line_edge[1])
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
            i = 0
            for e in self.entity_list:
                if e.board_part in enclosed_parts:
                    e.is_marked = True
                    self.set_entity_color(i, gv.marked_entity_color)
                i += 1

        if self.temp_rect_mark is not None:
            self.board.delete(self.temp_rect_mark)
            self.temp_rect_mark = None
        self.temp_rect_start_point = None

    def mouse_3_pressed(self, key):
        menu = tk.Menu(self.board, tearoff=0)
        work_mode_menu = tk.Menu(menu, tearoff=0)
        work_mode_menu.add_command(label="DXF", command=lambda: self.change_work_mode('dxf'))
        work_mode_menu.add_command(label="INP", command=lambda: self.change_work_mode('inp'))
        work_mode_menu.add_separator()
        work_mode_menu.add_command(label="Quit")
        select_mode_menu = tk.Menu(menu, tearoff=0)
        select_mode_menu.add_command(label="Edges", command=lambda: self.change_selection_mode('edge'))
        select_mode_menu.add_command(label="Points", command=lambda: self.change_selection_mode('point'))
        select_mode_menu.add_separator()
        select_mode_menu.add_command(label="Quit")
        show_entities_menu = tk.Menu(menu, tearoff=0)
        show_entities_menu.add_command(label="Weak", command=lambda: self.set_all_entities_color(gv.weak_entity_color))
        show_entities_menu.add_command(label="Strong", command=lambda: self.set_all_entities_color(gv.default_color))
        show_entities_menu.add_command(label="Hide", command=lambda: self.hide_dxf_entities())
        show_entities_menu.add_separator()
        show_entities_menu.add_command(label="Quit")
        menu.add_cascade(label='Work mode', menu=work_mode_menu)
        menu.add_separator()
        menu.add_cascade(label='Select mode', menu=select_mode_menu)
        menu.add_separator()
        if self.new_line_edge[0] is not None:
            self.board.delete(self.temp_line_mark)
        if self.new_line_edge[1] is not None:
            menu.add_command(label="add line", command=self.add_line_to_entity_list)
            menu.add_command(label="remove line", command=self.remove_temp_line)
            menu.add_separator()
        if self.selected_entity_mark is not None:
            menu.add_command(label="split entity", command=lambda: self.split_entity(self.selected_entity))
            if self.work_mode == 'dxf':
                menu.add_command(label="unmark entity", command=self.unmark_selected_entity)
                menu.add_command(label="mark entity", command=self.mark_selected_entity)
                menu.add_command(label="delete entity", command=self.remove_selected_entity_from_list)
            menu.add_separator()
        if self.work_mode == 'dxf':
            if len(self.entity_list) > 0:
                menu.add_command(label="mark all entities", command=self.mark_all_entities)
                menu.add_command(label="unmark all entities", command=self.unmark_all_entities)
                menu.add_command(label="delete marked entities", command=self.remove_marked_entities_from_list)
                menu.add_command(label="delete all non marked entities", command=self.remove_non_marked_entities_from_list)
                menu.add_separator()
        elif self.work_mode == 'inp':
            menu.add_command(label="Show net", command=self.show_net_lines)
            menu.add_command(label="Hide net", command=self.hide_net_lines)
            menu.add_cascade(label='Show entities', menu=show_entities_menu)
            menu.add_separator()
        menu.add_command(label="quit")
        menu.post(key.x_root, key.y_root)

    def change_work_mode(self, mode):
        self.work_mode = mode
        if mode.lower() == 'dxf':
            self.set_all_entities_color(gv.default_color)
            self.show_nodes = False
            self.show_net = False
        elif mode.lower() == 'inp':
            self.set_all_entities_color(gv.weak_entity_color)
            print('setting nodes list')
            self.set_initial_node_list()
            self.show_nodes = True
            print('checking unattached nodes')
            tmp_list = self.get_unattached_nodes()
            counter = len(tmp_list)
            if counter > 0:
                print(f'found {counter} unattached nodes')
                messagebox.showwarning("Warning", f"{counter} unattached nodes")
            else:
                # debug
                print('no unattached nodes')
                pass
        self.update_view()

    def change_selection_mode(self, mode):
        self.select_mode = mode

    def motion(self, key):
        if len(self.entity_list) == 0:
            return
        x, y = self.convert_screen_to_xy(key.x, key.y)
        p = Point(x, y)
        if self.new_line_edge[0] is not None:
            self.board.delete(self.temp_line_mark)
            self.temp_line_mark = self.draw_line(self.new_line_edge[0], p, gv.temp_line_color)
        selected_d, nearest_point = self.get_distance_from_entity_and_nearest_point(p, self.selected_entity)
        i, d = self.find_nearest_entity(p, only_visible=True)
        if i is None:
            return
        if selected_d*self.scale > 5:
            self.remove_selected_entity_mark()
        if d*self.scale < 5:
            self.remove_selected_entity_mark()
            self.mark_entity(self.selected_entity)
            self.selected_entity = i

    # split entity_list[i] into n parts
    def split_entity(self, i=0, n=4):
        e = self.entity_list[i]
        new_part_list = []
        if e.shape == 'ARC':
            angle = (e.arc_end_angle-e.arc_start_angle) / n
            start_angle = e.arc_start_angle
            for m in range(n):
                end_angle = start_angle + angle
                arc = Entity(shape=e.shape, center=e.center, radius=e.radius, start_angle=start_angle,
                             end_angle=end_angle)
                new_part_list.append(arc)
                start_angle = end_angle
        elif e.shape == 'LINE':
            alfa = e.start.get_alfa_to(e.end)*math.pi/180
            d = e.start.get_distance_from_point(e.end)
            step = d/n
            start = e.start
            for m in range(n):
                end = Point(start.x + step * math.cos(alfa), start.y + step * math.sin(alfa))
                line = Entity(shape='LINE', start=start, end=end)
                new_part_list.append(line)
                start = end
        elif e.shape == 'CIRCLE':
            return
        self.hide_entity(i)
        self.entity_list.remove(e)
        for m in range(n):
            self.entity_list.append(new_part_list[m])
            self.define_new_entity_color(-1)
            self.show_entity(-1)

    def define_new_entity_color(self, i):
        if self.work_mode == 'inp':
            if self.entity_list[i].is_part_of_dxf:
                self.entity_list[i].color = gv.weak_entity_color
            else:
                self.entity_list[i].color = gv.net_line_color
        else:
            self.entity_list[i].color = gv.default_color

    def set_node_list_of_entities(self, n):
        e_list = []
        for i in range(len(self.entity_list)):
            e = self.entity_list[i]
            if n.p.is_equal(e.start) or n.p.is_equal(e.end):
                e_list.append(i)
        return e_list
    
    def get_index_of_node_with_point_p(self, p):
        for i in range(1, len(self.node_list)):
            if p.is_equal(self.node_list[i].p):
                return i
        return None

    # return index of the neighbor that can make an element counter clockwise
    def get_next_relevant_neighbor(self, node, prev_angle):
        if len(node.neighbors_list) == 0:
            return None
        next_neighbor = None
        min_angle = 180-gv.min_diff_angle_to_create_element
        alfa = prev_angle + 180
        for i in range(len(node.neighbors_list)):
            n = node.neighbors_list[i]
            if n.is_part_of_element:
                continue
            angle = n.angle_from_p
            if angle < prev_angle:
                angle += 360
            diff_angle = alfa - angle
            if gv.min_diff_angle_to_create_element < diff_angle < min_angle:
                min_angle = diff_angle
                next_neighbor = i
        return next_neighbor

    def get_duplicated_entities(self):
        duplicate_entities_list = []
        for i in range(len(self.entity_list)):
            ei = self.entity_list[i]
            for j in range(i):
                ej = self.entity_list[j]
                if ei.is_equal(ej):
                    duplicate_entities_list.append(ei)
                    break
        return duplicate_entities_list

    def get_unattached_nodes(self):
        tmp_list = []
        for i in range(1, len(self.node_list)):
            n = self.node_list[i]
            if len(n.neighbors_list) < 2:
                n.color = gv.invalid_node_color
                tmp_list.append(i)
        return tmp_list

    def add_node_to_node_list(self, n):
        if not self.is_node_in_node_list(n):
            n.entities_list = self.set_node_list_of_entities(n)
            self.node_list.append(n)

    def set_initial_node_list(self):
        for i in range(len(self.entity_list)):
            e = self.entity_list[i]
            if e.shape == 'CIRCLE':
                continue
            p1 = e.start
            p2 = e.end
            node1 = Node(p1)
            node2 = Node(p2)
            self.add_node_to_node_list(node1)
            self.add_node_to_node_list(node2)
        self.set_all_nodes_neighbor_list()
        # debug
        # self.print_node_list()
    
    def set_all_nodes_neighbor_list(self):
        for i in range(1, len(self.node_list)):
            n = self.node_list[i]
            self.set_node_neighbors_list(n)

    def is_node_in_node_list(self, node):
        for n in self.node_list:
            if n.p.is_equal(node.p):
                return True
        return False

    def set_node_neighbors_list(self, n):
        e_list = n.entities_list
        for i in e_list:
            n_index = None
            alfa = None
            e = self.entity_list[i]
            neighbor = Neighbor()
            if n.p.is_equal(e.start):
                n_index = self.get_index_of_node_with_point_p(e.end)
                alfa = e.start.get_alfa_to(e.end)
            elif n.p.is_equal(e.end):
                n_index = self.get_index_of_node_with_point_p(e.start)
                alfa = e.start.get_alfa_to(e.start)
            if n_index is not None and not n.is_in_neighbors_list(n_index):
                neighbor.node_index = n_index
                neighbor.angle_from_p = alfa
                n.neighbors_list.append(neighbor)

    # debug
    def print_node_list(self):
        for i in range(1, len(self.node_list)):
            n = self.node_list[i]
            b = []
            for j in n.neighbors_list:
                b.append(j.node_index)
            print(f'{i}: {n.p.convert_into_tuple()}   neigbors: {b}')

    def create_net_element_list(self):
        element_list = []
        # iterate all nodes
        for i in range(1, len(self.node_list)):
            start_node = self.node_list[i]
            # iterate all nodes neighbors
            for j in range(len(start_node.neighbors_list)):
                new_element = [i]
                n = start_node.neighbors_list[j]
                if n.is_part_of_element:
                    continue
                node = start_node
                next_neighbor_index = j
                # try to set a new element starting from node[i] to neighbor j
                while next_neighbor_index is not None:
                    node.neighbors_list[next_neighbor_index].is_part_of_element = True
                    next_node_index = node.neighbors_list[next_neighbor_index].node_index
                    if next_node_index == i:
                        break
                    alfa = node.neighbors_list[next_neighbor_index].angle_from_p
                    node = self.node_list[next_node_index]
                    new_element.append(next_node_index)
                    next_neighbor_index = self.get_next_relevant_neighbor(node, alfa)
                if next_node_index == i and len(new_element) > 2:
                    element_list.append(new_element)
        self.element_list = element_list

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
            if len(e) == 3:
                element_3_list.append(e)
            else:
                element_4_list.append(e)
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
        entity_list = []
        for e in self.entity_list:
            t = e.convert_into_tuple()
            entity_list.append(t)
        node_list = []
        for e in self.node_list:
            t = e.convert_into_tuple()
            node_list.append(t)
        data = {
            "entity_list": entity_list,
            "node_list": node_list
        }
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
                                              filetypes=(("DXF files", "*.dxf"), ("Json files", "*.json"), ("all files", "*.*")))
        if filename == '':
            return
        self.reset_board()
        work_mode = gv.default_work_mode
        i = filename.find('.')
        filetype = filename[i+1:].lower()
        if filetype == 'dxf':
            doc = ezdxf.readfile(filename)
            self.convert_doc_to_entity_list(doc)
            print(f'{len(self.entity_list)} Entities in {filetype} file')
            print('checking for duplicated entities')
            d_list = self.get_duplicated_entities()
            if len(d_list) > 0:
                print(f'found {len(d_list)} duplicated entities')
                m = f'Removed {len(d_list)} duplicated entities'
                messagebox.showwarning("Warning", m)
                for e in d_list:
                    self.entity_list.remove(e)
            else:
                # debug
                print('no duplicated entities')
                pass
            work_mode = 'dxf'
        elif filetype == 'json':
            data = self.load_json(filename=filename)
            entity_list = data.get("entity_list")
            node_list = data.get("node_list")
            for t in entity_list:
                e = Entity()
                e.get_data_from_tuple(t)
                self.entity_list.append(e)
            for t in node_list:
                n = Node()
                n.get_data_from_tuple(t)
                self.node_list.append(n)
            work_mode = 'inp'
        self.set_accuracy()
        self.center_view()
        self.change_work_mode(work_mode)

    def center_view(self):
        x, y = self.get_center()
        if x is None:
            self.set_screen_position(self.center.x, self.center.y)
        else:
            self.set_screen_position(x, y)

    def get_center(self):
        if len(self.entity_list) == 0:
            return self.center.x, self.center.y
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
        x, y = self.convert_xy_to_screen((left+right)/2, (bottom+top)/2)
        return x, y

    def mark_selected_entity(self):
        if self.selected_entity_mark is None:
            return
        i = self.selected_entity
        e = self.entity_list[i]
        e.is_marked = True
        self.set_entity_color(i, gv.marked_entity_color)

    def mark_all_entities(self):
        i = 0
        for e in self.entity_list:
            if not e.is_marked:
                e.is_marked = True
                self.set_entity_color(i, gv.marked_entity_color)
            i += 1

    def unmark_all_entities(self):
        i = 0
        for e in self.entity_list:
            if e.is_marked:
                e.is_marked = False
                self.set_entity_color(i, gv.default_color)
            i += 1

    def unmark_selected_entity(self):
        if self.selected_entity_mark is None:
            return
        i = self.selected_entity
        e = self.entity_list[i]
        e.is_marked = False
        self.set_entity_color(i, gv.default_color)

    def remove_marked_entities_from_list(self):
        temp_list = []
        for e in self.entity_list:
            if not e.is_marked:
                temp_list.append(e)
        for e in temp_list:
            e.board_part = None
        self.entity_list = temp_list
        self.selected_entity = 0
        self.board.delete('all')
        self.show_dxf_entities()

    def remove_non_marked_entities_from_list(self):
        temp_list = []
        for e in self.entity_list:
            if e.is_marked:
                temp_list.append(e)
        for e in temp_list:
            e.is_marked = False
            e.board_part = None
            e.color = gv.default_color
        self.entity_list = temp_list
        self.selected_entity = 0
        if self.new_line_edge[1] is not None:
            self.remove_temp_line()
        elif self.new_line_edge[0] is not None:
            self.board.delete(self.new_line_edge_mark[0])
            self.new_line_edge[0] = None
            self.board.delete(self.temp_line_mark)
        self.board.delete('all')
        self.show_dxf_entities()

    def remove_selected_entity_from_list(self):
        if self.selected_entity_mark is None:
            return
        i = self.selected_entity
        e = self.entity_list[i]
        self.selected_entity = 0
        self.hide_entity(i)
        self.entity_list.remove(e)

    def remove_temp_line(self):
        if self.new_line_edge[1] is None:
            return
        self.board.delete(self.new_line_edge_mark[0])
        self.board.delete(self.new_line_edge_mark[1])
        self.board.delete(self.new_line_mark)
        self.new_line_edge[0] = None
        self.new_line_edge[1] = None

    def add_line_to_entity_list(self):
        p1 = self.new_line_edge[0]
        p2 = self.new_line_edge[1]
        if p2 is None:
            return
        is_part_of_dxf = (self.work_mode == 'dxf')
        e = Entity('LINE', start=p1, end=p2, is_part_of_dxf=is_part_of_dxf)
        if is_part_of_dxf:
            e.is_marked = True
            e.color = gv.marked_entity_color
        else:
            e.color = gv.net_line_color
        self.entity_list.append(e)
        self.board.delete(self.new_line_edge_mark[0])
        self.board.delete(self.new_line_edge_mark[1])
        self.board.delete(self.new_line_mark)
        self.new_line_edge[0] = None
        self.new_line_edge[1] = None
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

    # return the distance of Point p from entity[i]
    def get_distance_from_entity_and_nearest_point(self, p, i, only_visible=False):
        e = self.entity_list[i]
        if only_visible and e.board_part is None:
            return None, None
        d = None
        nearest_point = None
        if e.shape == 'CIRCLE':
            d = math.fabs(e.center.get_distance_from_point(p)-e.radius)
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
                d = math.fabs(e.center.get_distance_from_point(p) - e.radius)
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
                    d = e.start.get_distance_from_point(p)
                    nearest_point = e.start
                else:
                    d = e.end.get_distance_from_point(p)
                    nearest_point = e.end
        elif e.shape == 'LINE':
            alfa = e.start.get_alfa_to(e.end)
            endx = math.fabs(get_shifted_point(e.end, e.start, -alfa).x)
            p = get_shifted_point(p, e.start, -alfa)
            x = p.x
            if 0 <= x <= endx:
                d = math.fabs(p.y)
                alfa = alfa * math.pi / 180
                px = math.cos(alfa)*x+e.start.x
                py = math.sin(alfa)*x+e.start.y
                nearest_point = Point(px, py)
            elif x < 0:
                d = p.get_distance_from_point(Point(0, 0))
                nearest_point = e.start
            else:
                d = p.get_distance_from_point(Point(endx, 0))
                nearest_point = e.end
        return round(d, gv.accuracy), nearest_point

    def get_entity_by_board_part(self, board_part):
        i = 0
        for i in range(len(self.entity_list)):
            if self.entity_list[i].board_part == board_part:
                return i
        return None

    def hide_node(self, i):
        if self.node_list[i].board_part is None:
            return
        self.board.delete(self.node_list[i].board_part)
        self.node_list[i].board_part = None

    def hide_all_nodes(self):
        for i in range(len(self.node_list)):
            self.hide_node(i)

    def show_node(self, i):
        if self.node_list[i].board_part is not None:
            return
        part = self.draw_circle(self.node_list[i].p, gv.node_mark_radius/self.scale, self.node_list[i].color)
        self.node_list[i].board_part = part

    def show_all_nodes(self):
        self.show_nodes = True
        for i in range(1, len(self.node_list)):
            self.show_node(i)

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

    def show_net_lines(self):
        self.show_net = True
        for i in range(len(self.entity_list)):
            if not self.entity_list[i].is_part_of_dxf:
                self.show_entity(i)

    def hide_net_lines(self):
        for i in range(len(self.entity_list)):
            if not self.entity_list[i].is_part_of_dxf:
                self.hide_entity(i)

    def show_dxf_entities(self):
        self.show_entities = True
        for i in range(len(self.entity_list)):
            if self.entity_list[i].is_part_of_dxf:
                self.show_entity(i)

    def hide_entity(self, i):
        if self.entity_list[i].board_part is None:
            return
        self.board.delete(self.entity_list[i].board_part)
        self.entity_list[i].board_part = None

    def hide_dxf_entities(self):
        for i in range(len(self.entity_list)):
            if self.entity_list[i].is_part_of_dxf:
                self.hide_entity(i)

    def set_entity_color(self, i, color):
        self.hide_entity(i)
        self.entity_list[i].color = color
        self.show_entity(i)

    def set_all_entities_color(self, color):
        for i in range(len(self.entity_list)):
            self.set_entity_color(i, color)

    def mark_entity(self, i):
        b = self.board.bbox(self.entity_list[i].board_part)
        self.selected_entity_mark = self.board.create_rectangle(b)

    def remove_selected_entity_mark(self):
        if self.selected_entity_mark is None:
            return
        else:
            self.board.delete(self.selected_entity_mark)
            self.selected_entity_mark = None

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
        x, y = self.get_screen_center()
        x, y = self.convert_screen_to_xy(x, y)
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

    def update_view(self):
        self.hide_dxf_entities()
        self.hide_net_lines()
        self.hide_all_nodes()
        if self.show_entities:
            self.show_dxf_entities()
        if self.show_nodes:
            self.show_all_nodes()
        if self.show_net:
            self.show_net_lines()            
        self.window_main.update()

            