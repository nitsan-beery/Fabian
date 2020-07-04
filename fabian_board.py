from board import *
import ezdxf
import math
from operator import attrgetter, itemgetter

#shapes = {'ARC'}
shapes = {'CIRCLE', 'LINE', 'ARC'}


class Entity:
    def __init__(self, shape=None, center=None, radius=None, start=None, end=None, start_angle=None, end_angle=None):
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
        self.color = gv.default_color

    # ser arc start point, end point, left_bottom and right_up
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
                self.left_bottom, self.right_up = gv.get_sorted_points(self.start, self.end, sort_by_x=True)
        else:
            if self.center is None or self.radius is None:
                self.left_bottom, self.right_up = None, None
            else:
                self.left_bottom = Point(self.center.x - self.radius, self.center.y - self.radius)
                self.right_up = Point(self.center.x + self.radius, self.center.y + self.radius)


class Neighbor:
    def __init__(self, node_index=0, angle_from_p=0):
        self.node_index = node_index
        self.angle_from_p = angle_from_p
        self.is_part_of_element = False


class Node:
    def __init__(self, point):
        self.p = point
        self.neighbors_list = []


class FabianBoard(Board):
    def __init__(self, scale=1):
        super().__init__(True)
        self.scale = scale
        self.window_main.title("Fabian")
        self.button_load.config(text='Load dxf', command=lambda: self.load_dxf())
        self.button_save.config(text='Save dxf', command=lambda: self.save_dxf())
        self.button_zoom_in = tk.Button(self.frame_2, text='Zoom In', command=lambda: self.zoom(4/3))
        self.button_zoom_out = tk.Button(self.frame_2, text='Zoom Out', command=lambda: self.zoom(3/4))
        self.button_center = tk.Button(self.frame_2, text='Center view', command=lambda: self.center_view())
        self.button_zoom_in.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.button_zoom_out.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.button_center.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.button_save_inp = tk.Button(self.frame_2, text='Save inp', command=lambda: self.save_inp())
        self.button_save_inp.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)
        self.board.config(bg=gv.board_bg_color)

        self.dxfDoc = None
        self.entity_list = []
        self.node_list = []
        self.element_list = []
        self.select_mode = gv.select_mode
        self.work_mode = gv.work_mode
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
        self.node_list = []
        self.element_list = []
        self.select_mode = gv.select_mode
        self.work_mode = gv.work_mode
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
            d_left = gv.get_distance_between_points(Point(x, y), e.left_bottom)
            d_right = gv.get_distance_between_points(Point(x, y), e.right_up)
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
                    if e.is_marked:
                        e.is_marked = False
                        self.change_entity_color(i, gv.default_color)
                    else:
                        e.is_marked = True
                        self.change_entity_color(i, gv.marked_entity_color)
                i += 1

        if self.temp_rect_mark is not None:
            self.board.delete(self.temp_rect_mark)
            self.temp_rect_mark = None
        self.temp_rect_start_point = None

    def mouse_3_pressed(self, key):
        menu = tk.Menu(self.board, tearoff=0)
        work_mode_menu = tk.Menu(menu, tearoff=0)
        work_mode_menu.add_command(label="Select parts", command=lambda: self.change_work_mode('select'))
        work_mode_menu.add_command(label="Build net", command=lambda: self.change_work_mode('net'))
        work_mode_menu.add_command(label="Quit")
        select_mode_menu = tk.Menu(menu, tearoff=0)
        select_mode_menu.add_command(label="Edges", command=lambda: self.change_selection_mode('edge'))
        select_mode_menu.add_command(label="Points", command=lambda: self.change_selection_mode('point'))
        select_mode_menu.add_command(label="Quit")
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
            menu.add_command(label="mark entity", command=self.mark_selected_entity)
            menu.add_command(label="unmark entity", command=self.unmark_selected_entity)
            menu.add_command(label="split entity", command=lambda: self.split_entity(self.selected_entity))
            menu.add_command(label="delete entity", command=self.remove_selected_entity_from_list)
            menu.add_separator()
        elif len(self.entity_list) > 0:
            menu.add_command(label="mark all entities", command=self.mark_all_entities)
            menu.add_command(label="unmark all entities", command=self.unmark_all_entities)
            menu.add_separator()
            if self.work_mode == 'select':
                menu.add_command(label="delete marked entities", command=self.remove_marked_entities_from_list)
                menu.add_command(label="delete all non marked entities", command=self.remove_non_marked_entities_from_list)
                menu.add_separator()
            elif self.work_mode == 'net':
                pass
        menu.add_command(label="quit")
        menu.post(key.x_root, key.y_root)

    def change_work_mode(self, mode):
        self.work_mode = mode

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
        i, d = self.find_nearest_entity(p)
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
            alfa = self.get_alfa(e.start, e.end)*math.pi/180
            d = gv.get_distance_between_points(e.start, e.end)
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
            self.show_entity(-1)

    def get_index_of_node_with_point_p(self, p, node_list):
        for i in range(1, len(node_list)):
            if p.is_equal(node_list[i].p):
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

    def create_node_list(self):
        node_list = [0]
        for i in range(len(self.entity_list)):
            e = self.entity_list[i]
            if e.shape == 'CIRCLE':
                continue
            p1 = Point(round(e.start.x, gv.accuracy), round(e.start.y, gv.accuracy))
            p2 = Point(round(e.end.x, gv.accuracy), round(e.end.y, gv.accuracy))
            node1 = Node(p1)
            node2 = Node(p2)
            p1_index = self.get_index_of_node_with_point_p(p1, node_list)
            p2_index = self.get_index_of_node_with_point_p(p2, node_list)
            if p1_index is None:
                p1_index = len(node_list)
                node_list.append(node1)
            if p2_index is None:
                p2_index = len(node_list)
                node_list.append(node2)
            alfa = self.get_alfa(p1, p2)
            node_list[p1_index].neighbors_list.append(Neighbor(p2_index, alfa))
            alfa = (alfa+180) % 360
            node_list[p2_index].neighbors_list.append(Neighbor(p1_index, alfa))
        self.node_list = node_list

    def create_element_list(self):
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
        self.create_node_list()
        self.create_element_list()
        filename = filedialog.asksaveasfilename(parent=self.window_main, initialdir="./INP files/", title="Select file",
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
        filename = filedialog.asksaveasfilename(parent=self.window_main, initialdir="./DXF files/", title="Select file",
                                                initialfile=default_file_name, defaultextension=".dxf",
                                                filetypes=(("dxf files", "*.dxf"), ("all files", "*.*")))
        if filename == '':
            return
        doc.saveas(filename)

    def load_dxf(self):
        filename = filedialog.askopenfilename(parent=self.window_main, initialdir="./DXF files/",
                                              title="Select file",
                                              filetypes=(("DXF files", "*.dxf"), ("all files", "*.*")))
        if filename == '':
            return
        self.reset_board()
        doc = ezdxf.readfile(filename)
        self.convert_doc_to_entity_list(doc)
        self.center_view()
        self.show_all_entities()

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
        self.change_entity_color(i, gv.marked_entity_color)

    def mark_all_entities(self):
        i = 0
        for e in self.entity_list:
            if not e.is_marked:
                e.is_marked = True
                self.change_entity_color(i, gv.marked_entity_color)
            i += 1

    def unmark_all_entities(self):
        i = 0
        for e in self.entity_list:
            if e.is_marked:
                e.is_marked = False
                self.change_entity_color(i, gv.default_color)
            i += 1

    def unmark_selected_entity(self):
        if self.selected_entity_mark is None:
            return
        i = self.selected_entity
        e = self.entity_list[i]
        e.is_marked = False
        self.change_entity_color(i, gv.default_color)

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
        self.show_all_entities()

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
        self.show_all_entities()

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
        e = Entity('LINE', start=p1, end=p2)
        e.is_marked = True
        e.color = gv.marked_entity_color
        self.entity_list.append(e)
        self.board.delete(self.new_line_edge_mark[0])
        self.board.delete(self.new_line_edge_mark[1])
        self.board.delete(self.new_line_mark)
        self.new_line_edge[0] = None
        self.new_line_edge[1] = None
        self.show_entity(-1)

    def find_nearest_entity(self, p):
        min_d_index = 0
        min_d, nearest_point = self.get_distance_from_entity_and_nearest_point(p, 0)
        for i in range(len(self.entity_list)):
            d, nearest_point = self.get_distance_from_entity_and_nearest_point(p, i)
            if d < min_d:
                min_d_index = i
                min_d = d
        return min_d_index, min_d

    # return the distance of Point p from entity[i]
    def get_distance_from_entity_and_nearest_point(self, p, i):
        e = self.entity_list[i]
        d = None
        nearest_point = None
        if e.shape == 'CIRCLE':
            d = math.fabs(gv.get_distance_between_points(e.center, p)-e.radius)
            alfa = self.get_alfa(e.center, p)*math.pi/180
            if alfa is None:
                d = e.radius
                alfa = 0
            px = e.center.x+math.cos(alfa)*e.radius
            py = e.center.y+math.sin(alfa)*e.radius
            nearest_point = Point(px, py)
        elif e.shape == 'ARC':
            alfa = self.get_alfa(e.center, p)
            if alfa is None:
                d = e.radius
                nearest_point = e.start
            if e.arc_end_angle > 360 and alfa < e.arc_start_angle:
                alfa += 360
            if e.arc_start_angle <= alfa <= e.arc_end_angle:
                d = math.fabs(gv.get_distance_between_points(e.center, p) - e.radius)
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
                    d = gv.get_distance_between_points(e.start, p)
                    nearest_point = e.start
                else:
                    d = gv.get_distance_between_points(e.end, p)
                    nearest_point = e.end
        elif e.shape == 'LINE':
            alfa = self.get_alfa(e.start, e.end)
            endx = math.fabs(self.get_shifted_point(e.end, e.start, -alfa).x)
            p = self.get_shifted_point(p, e.start, -alfa)
            x = p.x
            if 0 <= x <= endx:
                d = math.fabs(p.y)
                alfa = alfa * math.pi / 180
                px = math.cos(alfa)*x+e.start.x
                py = math.sin(alfa)*x+e.start.y
                nearest_point = Point(px, py)
            elif x < 0:
                d = gv.get_distance_between_points(Point(0, 0), p)
                nearest_point = e.start
            else:
                d = gv.get_distance_between_points(Point(endx, 0), p)
                nearest_point = e.end
        return round(d, gv.accuracy), nearest_point

    def create_arc(self, center, radius, start_angle, end_angle):
        e = Entity('ARC')

    def create_line(self, p1, p2):
        e = Entity('ARC')

    def create_circle(self, center, radius):
        e = Entity('ARC')

    # return the angle vector of Point p relative to Point center, None if p == center
    def get_alfa(self, center, p):
        dx = p.x - center.x
        dy = p.y - center.y
        if dx == 0 and dy == 0:
            return None
        if dx == 0:
            if dy > 0:
                alfa = 90
            else:
                alfa = 270
        elif dy == 0:
            if dx > 0:
                alfa = 0
            else:
                alfa = 180
        else:
            alfa = math.atan(dy / dx) * 180 / math.pi
            if dx < 0:
                alfa += 180
            elif alfa < 0:
                alfa += 360
        return alfa

    # return new coordinates of Point p relative to Point new00 with rotation_angle
    def get_shifted_point(self, p, new00, rotation_angle):
        shifted_p = Point(p.x - new00.x, p.y - new00.y)
        r = gv.get_distance_between_points(Point(0, 0), shifted_p)
        if r == 0:
            return shifted_p
        alfa = self.get_alfa(Point(0, 0), shifted_p) + rotation_angle
        alfa = alfa*math.pi/180
        shifted_p.x = math.cos(alfa)*r
        shifted_p.y = math.sin(alfa)*r
        return shifted_p

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

    def get_entity_by_board_part(self, board_part):
        i = 0
        for i in range(len(self.entity_list)):
            if self.entity_list[i].board_part == board_part:
                return i
        return None

    def show_all_entities(self):
        for i in range(len(self.entity_list)):
            self.show_entity(i)

    def hide_entity(self, i):
        if self.entity_list[i].board_part is None:
            return
        self.board.delete(self.entity_list[i].board_part)
        self.entity_list[i].board_part = None

    def change_entity_color(self, i, color):
        self.hide_entity(i)
        self.entity_list[i].color = color
        self.show_entity(i)
        
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
                    start_angle = round(dxf_entity.dxf.start_angle, 2) % 360
                    end_angle = round(dxf_entity.dxf.end_angle, 2)
                    e = Entity(shape='ARC', center=center, radius=radius, start_angle=start_angle, end_angle=end_angle)
                if e is not None:
                    self.entity_list.append(e)

    def zoom(self, factor):
        self.scale = round(self.scale*factor, 1)
        self.center_view()
        self.update_view()

    def update_view(self):
        for i in range(len(self.entity_list)):
            self.hide_entity(i)
        self.show_all_entities()
        self.window_main.update()
