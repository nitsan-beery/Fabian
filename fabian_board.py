from board import *
import ezdxf
import math
from operator import attrgetter

#shapes = {'ARC'}
shapes = {'CIRCLE', 'LINE', 'ARC'}


class Entity:
    def __init__(self, shape=None):
        self.shape = shape
        self.center = None
        self.radius = None
        self.arc_start_angle = None
        self.arc_end_angle = None
        self.start = None
        self.end = None
        self.left_bottom = None
        self.right_up = None
        self.is_marked = False
        self.board_part = None
        self.color = gv.default_color


class FabianBoard(Board):
    def __init__(self, scale=1):
        super().__init__(True)
        self.scale = scale
        self.window_main.title("Fabian")
        self.button_load.config(command=lambda: self.load_dxf())
        self.button_zoom_in = tk.Button(self.frame_2, text='Zoom In', command=lambda: self.zoom(4/3))
        self.button_zoom_out = tk.Button(self.frame_2, text='Zoom Out', command=lambda: self.zoom(3/4))
        self.button_zoom_in.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.button_zoom_out.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.board.config(bg=gv.board_bg_color)

        self.dxfDoc = None
        self.entity_list = []
        self.selected_entity = 0
        self.selected_entity_mark = None
        self.new_line_edge = [None, None]
        self.new_line_edge_mark = [None, None]
        self.new_line_mark = None
        self.temp_line_mark = None

        self.board.bind('<Motion>', self.motion)
        self.board.bind('<Button-1>', self.mouse_1_pressed)
        self.board.bind('<B1-Motion>', self.mouse_1_motion)
        self.board.bind('<ButtonRelease-1>', self.mouse_1_released)
        self.board.bind('<Button-3>', self.mouse_3_pressed)

    def mouse_1_pressed(self, key):
        if self.selected_entity_mark is None:
            return
        x, y = self.convert_screen_to_xy(key.x, key.y)
        p = Point(x, y)
        e = self.entity_list[self.selected_entity]
        d_left = gv.get_distance_between_points(Point(x, y), e.left_bottom)
        d_right = gv.get_distance_between_points(Point(x, y), e.right_up)
        if d_left < d_right:
            p = e.left_bottom
        else:
            p = e.right_up
        # first point
        if self.new_line_edge[0] is None:
            self.new_line_edge[0] = p
            self.new_line_edge_mark[0] = self.create_circle(p, gv.edge_line_mark_radius/self.scale)
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
                self.new_line_edge_mark[1] = self.create_circle(p, gv.edge_line_mark_radius/self.scale)
                self.new_line_mark = self.create_line(self.new_line_edge[0], self.new_line_edge[1])
            else:
                self.board.delete(self.new_line_edge_mark[1])
                self.new_line_edge_mark[1] = None
                self.board.delete(self.new_line_mark)
                self.new_line_mark = None
                if self.new_line_edge[1] != p:
                    self.new_line_edge[1] = p
                    self.new_line_edge_mark[1] = self.create_circle(p, gv.edge_line_mark_radius / self.scale)
                    self.new_line_mark = self.create_line(self.new_line_edge[0], self.new_line_edge[1])
                else:
                    self.new_line_edge[1] = None

    def mouse_1_motion(self, key):
        self.motion(key)

    def mouse_1_released(self, key):
        pass

    def mouse_3_pressed(self, key):
        menu = tk.Menu(self.board, tearoff=0)
        if self.new_line_edge[0] is not None:
            self.board.delete(self.temp_line_mark)
        if self.new_line_edge[1] is not None:
            menu.add_command(label="add line", command=self.add_line_to_entity_list)
            menu.add_command(label="remove line", command=self.remove_temp_line)
        if self.selected_entity_mark is not None:
            menu.add_command(label="mark entity", command=self.mark_selected_entity)
            menu.add_command(label="unmark entity", command=self.unmark_selected_entity)
            menu.add_command(label="delete entity", command=self.remove_selected_entity_from_list)
        else:
            menu.add_command(label="mark all entities", command=self.mark_all_entities)
            menu.add_command(label="unmark all entities", command=self.unmark_all_entities)
            menu.add_command(label="delete marked entities", command=self.remove_marked_entities_from_list)
            menu.add_command(label="delete all non marked entities", command=self.remove_non_marked_entities_from_list)
        menu.add_command(label="quit")
        menu.post(key.x_root, key.y_root)

    def motion(self, key):
        if len(self.entity_list) == 0:
            return 
        x, y = self.convert_screen_to_xy(key.x, key.y)
        p = Point(x, y)
        if self.new_line_edge[0] is not None:
            self.board.delete(self.temp_line_mark)
            self.temp_line_mark = self.create_line(self.new_line_edge[0], p, gv.temp_line_color)
        selected_d = self.get_distance_from_entity_and_nearest_point(p, self.selected_entity)
        i, d = self.find_nearest_entity(p)
        if selected_d*self.scale > 5:
            self.remove_selected_entity_mark()
        if d*self.scale < 5:
            self.remove_selected_entity_mark()
            self.mark_entity(self.selected_entity)
            self.selected_entity = i

    def load_dxf(self):
        filename = filedialog.askopenfilename(parent=self.window_main, initialdir="./DXF files/",
                                              title="Select file",
                                              filetypes=(("DXF files", "*.dxf"), ("all files", "*.*")))
        if filename == '':
            return
        self.dxfDoc = ezdxf.readfile(filename)

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
        e = Entity('LINE')
        p1, p2 = self.get_sorted_points(p1, p2, sort_by_x=True)
        if p1.x == p2.x:
            p1, p2 = self.get_sorted_points(p1, p2, sort_by_x=False)
        e.start = e.left_bottom = p1
        e.end = e.right_up = p2
#        e.is_marked = True
#        e.color = gv.marked_entity_color
        self.entity_list.append(e)
        self.board.delete(self.new_line_edge_mark[0])
        self.board.delete(self.new_line_edge_mark[1])
        self.board.delete(self.new_line_mark)
        self.new_line_edge[0] = None
        self.new_line_edge[1] = None
        self.show_entity(-1)

    def find_nearest_entity(self, p):
        min_d_index = 0
        min_d = self.get_distance_from_entity_and_nearest_point(p, 0)
        for i in range(len(self.entity_list)):
            d = self.get_distance_from_entity_and_nearest_point(p, i)
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
            x = math.cos(alfa)*e.radius
            y = math.sin(alfa)*e.radius
            nearest_point = Point(x, y)
        elif e.shape == 'ARC':
            alfa = self.get_alfa(e.center, p)
            if alfa is None:
                d = e.radius
            if e.arc_end_angle > 360 and alfa < e.arc_start_angle:
                alfa += 360
            if e.arc_start_angle <= alfa <= e.arc_end_angle:
                d = math.fabs(gv.get_distance_between_points(e.center, p) - e.radius)
            else:
                mid_angle = (e.arc_start_angle + e.arc_end_angle)/2
                if mid_angle < 180:
                    mid_angle += 360
                a1 = (mid_angle-180)
                if a1 < alfa < mid_angle:
                    d = gv.get_distance_between_points(e.start, p)
                else:
                    d = gv.get_distance_between_points(e.end, p)
        elif e.shape == 'LINE':
            alfa = self.get_alfa(e.start, e.end)
            endx = math.fabs(self.get_shifted_point(e.end, e.start, -alfa).x)
            p = self.get_shifted_point(p, e.start, -alfa)
            x = p.x
            if 0 <= x <= endx:
                d = math.fabs(p.y)
            elif x < 0:
                d = gv.get_distance_between_points(Point(0, 0), p)
            else:
                d = gv.get_distance_between_points(Point(endx, 0), p)
        return round(d, 3)

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
            part = self.create_line(self.entity_list[i].start, self.entity_list[i].end, self.entity_list[i].color)
        elif self.entity_list[i].shape == 'CIRCLE':
            part = self.create_circle(self.entity_list[i].center, self.entity_list[i].radius, self.entity_list[i].color)
        elif self.entity_list[i].shape == 'ARC':
            part = self.create_arc(self.entity_list[i].center, self.entity_list[i].radius, self.entity_list[i].arc_start_angle,
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

    def convert_doc_to_entity_list(self):
        if self.dxfDoc is None:
            return
        msp = self.dxfDoc.modelspace()
        for shape in shapes:
            for dxf_entity in msp.query(shape):
                e = Entity(shape)
                if shape == 'LINE':
                    p1 = Point(dxf_entity.dxf.start[0], dxf_entity.dxf.start[1])
                    p2 = Point(dxf_entity.dxf.end[0], dxf_entity.dxf.end[1])
                    p1, p2 = self.get_sorted_points(p1, p2, sort_by_x=True)
                    if p1.x == p2.x:
                        p1, p2 = self.get_sorted_points(p1, p2, sort_by_x=False)
                    e.start = e.left_bottom = p1
                    e.end = e.right_up = p2
                elif shape == 'CIRCLE':
                    e.center = Point(dxf_entity.dxf.center[0], dxf_entity.dxf.center[1])
                    e.radius = dxf_entity.dxf.radius
                    e.left_bottom = Point(e.center.x-e.radius, e.center.y-e.radius)
                    e.right_up = Point(e.center.x+e.radius, e.center.y+e.radius)
                elif shape == 'ARC':
                    e.center = Point(dxf_entity.dxf.center[0], dxf_entity.dxf.center[1])
                    e.radius = dxf_entity.dxf.radius
                    start_angle = round(dxf_entity.dxf.start_angle, 2) % 360
                    end_angle = round(dxf_entity.dxf.end_angle, 2)
                    if end_angle < start_angle:
                        end_angle += 360
                    e.arc_start_angle = start_angle
                    e.arc_end_angle = end_angle
                    p1 = Point(e.center.x + e.radius*math.cos(e.arc_start_angle*math.pi/180), e.center.y + e.radius*math.sin(e.arc_start_angle*math.pi/180))
                    p2 = Point(e.center.x + e.radius*math.cos(e.arc_end_angle*math.pi/180), e.center.y + e.radius*math.sin(e.arc_end_angle*math.pi/180))
                    e.start = p1
                    e.end = p2
                    p1, p2 = self.get_sorted_points(p1, p2, sort_by_x=True)
                    e.left_bottom = p1
                    e.right_up = p2
                self.entity_list.append(e)

    # if sort by x return left --> right points. if left == right return bottom --> up
    # else: return bottom --> up. if bottom == up return left --> right
    def get_sorted_points(self, p1, p2, sort_by_x=True):
        if p1 == p2:
            return p1, p2
        if sort_by_x:
            if p1.x > p2.x:
                return p2, p1
            elif p1.x < p2.x:
                return p1, p2
            else:
                return self.get_sorted_points(p1, p2, sort_by_x=False)
        else:
            if p1.y > p2.y:
                return p2, p1
            elif p1.y < p2.y:
                return p1, p2
            else:
                return self.get_sorted_points(p1, p2, sort_by_x=True)

    def zoom(self, factor):
        self.scale = round(self.scale*factor, 1)
        self.update_view()

    def update_view(self):
        for i in range(len(self.entity_list)):
            self.hide_entity(i)
        self.show_all_entities()
        self.window_main.update()
