from board import *
import ezdxf
import math
from operator import attrgetter

shapes = {'LINE'}#CIRCLE', 'LINE', 'ARC'}


class Entity:
    def __init__(self, shape=None):
        self.shape = shape
        self.lim_x_left = None
        self.lim_x_right = None
        self.lim_y_top = None
        self.lim_y_bottom = None
        self.center = None
        self.radius = None
        self.arc_start_angle = None
        self.arc_end_angle = None
        self.start = None
        self.end = None
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

        self.dxfDoc = None
        self.entity_list = []

    def load_dxf(self):
        filename = filedialog.askopenfilename(parent=self.window_main, initialdir="./DXF files/",
                                              title="Select file",
                                              filetypes=(("DXF files", "*.dxf"), ("all files", "*.*")))
        if filename == '':
            return
        self.dxfDoc = ezdxf.readfile(filename)

    def find_nearest_entity(self, key):
        p = Point(self.convert_screen_to_xy(key.x, key.y))
        min_d_index = 0
        min_d = self.get_distance_from_entity(p, 0)
        for i in range(len(self.entity_list)):
            d = self.get_distance_from_entity(p, i)
            if d < min_d:
                min_d_index = i
                min_d = d
        return min_d_index

    # return the distance of Point p from entity[i]
    def get_distance_from_entity(self, p, i):
        e = self.entity_list[i]
        d = None
        if e.shape == 'CIRCLE':
            d = math.fabs(self.get_distance_between_points(e.center, p)-e.radius)
        elif e.shape == 'ARC':
            alfa = self.get_alfa(e.center, p)
            if alfa is None:
                d = e.radius
            if e.arc_end_angle > 360 and alfa < e.arc_start_angle:
                alfa += 360
            if e.arc_start_angle <= alfa <= e.arc_end_angle:
                d = math.fabs(self.get_distance_between_points(e.center, p) - e.radius)
            else:
                mid_angle = (e.arc_start_angle + e.arc_end_angle)/2
                if mid_angle < 180:
                    mid_angle += 360
                a1 = (mid_angle-180)
                if a1 < alfa < mid_angle:
                    d = self.get_distance_between_points(e.start, p)
                else:
                    d = self.get_distance_between_points(e.end, p)
        elif e.shape == 'LINE':
            alfa = self.get_alfa(e.start, e.end)
            endx = math.fabs(self.get_shifted_point(e.end, e.start, -alfa).x)
            p = self.get_shifted_point(p, e.start, -alfa)
            x = p.x
            if 0 <= x <= endx:
                d = math.fabs(p.y)
            elif x < 0:
                d = self.get_distance_between_points(Point(0, 0), p)
            else:
                d = self.get_distance_between_points(Point(endx, 0), p)
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

    def get_distance_between_points(self, p1, p2):
        return math.sqrt(pow(p1.x-p2.x, 2) + pow(p1.y-p2.y, 2))

    # return new coordinates of Point p relative to Point new00 with rotation_angle
    def get_shifted_point(self, p, new00, rotation_angle):
        shifted_p = Point(p.x - new00.x, p.y - new00.y)
        r = self.get_distance_between_points(Point(0, 0), shifted_p)
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
                    e.start = p1
                    e.end = p2
                    e.lim_x_left = p1.x
                    e.lim_x_right = p2.x
                    p1, p2 = self.get_sorted_points(p1, p2, sort_by_x=False)
                    e.lim_y_bottom = p1.y
                    e.lim_y_top = p2.y
                elif shape == 'CIRCLE':
                    e.center = Point(dxf_entity.dxf.center[0], dxf_entity.dxf.center[1])
                    e.radius = dxf_entity.dxf.radius
                    e.lim_x_left = e.center.x-e.radius
                    e.lim_x_right = e.center.x+e.radius
                    e.lim_y_bottom = e.center.y-e.radius
                    e.lim_y_top = e.center.y+e.radius
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
                    e.lim_x_left = p1.x
                    e.lim_x_right = p2.x
                    p1, p2 = self.get_sorted_points(p1, p2, sort_by_x=False)
                    e.lim_y_bottom = p1.y
                    e.lim_y_top = p2.y
                self.entity_list.append(e)

    def get_sorted_points(self, p1, p2, sort_by_x=True):
        if sort_by_x:
            if p1.x > p2.x:
                return p2, p1
            else:
                return p1, p2
        else:
            if p1.y > p2.y:
                return p2, p1
            else:
                return p1, p2

    def zoom(self, factor):
        self.scale = round(self.scale*factor, 1)
        self.update_view()

    def update_view(self):
        for i in range(len(self.entity_list)):
            self.hide_entity(i)
        self.show_all_entities()
        self.window_main.update()
