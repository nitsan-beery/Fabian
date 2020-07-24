from point import *
import tkinter as tk
from tkinter import ttk

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

    # node[0] = start node,   node[-1] = end node    i = node hash index
    def add_node_to_entity_nodes_list(self, node_hash):
        for j in self.nodes_list:
            if j == node_hash:
                return
        if len(self.nodes_list) < 2:
            self.nodes_list.append(node_hash)
        else:
            self.nodes_list.insert(1, node_hash)

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
        self.hash_index = 0
        self.attached_entities = []
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
        attached_lines = []
        for al in self.attached_lines:
            attached_lines.append(al.convert_into_tuple())
        t = (self.p.convert_into_tuple(), self.hash_index, self.attached_entities, attached_lines)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 4:
            print(f"tuple doesn't match Node type: {t}")
            return
        self.p.get_data_from_tuple(t[0])
        self.hash_index = t[1]
        self.attached_entities = t[2]
        attached_lines = t[3]
        self.attached_lines = []
        for t in attached_lines:
            al = AttachedLine()
            al.get_data_from_tuple(t)
            self.attached_lines.append(al)


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

    def convert_into_tuple(self):
        t = (self.line_index, self.second_node, self.angle_to_second_node, self.is_outer_line, self.is_available)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 5:
            print(f"tuple doesn't match AttachedLine type: {t}")
        self.line_index = t[0]
        self.second_node = t[1]
        self.angle_to_second_node = t[2]
        self.is_outer_line = t[3]
        self.is_available = t[4]


class SelectedPart(Part):
    def __init__(self, part_type='entity', index=0, color=gv.mark_rect_color):
        super().__init__(color)
        self.part_type = part_type
        self.index = index


class FabianState:
    def __init__(self):
        self.entity_list = None
        self.node_list = None
        self.next_node_hash_index = 1
        self.nodes_hash = {'0': 0}
        self.net_line_list = None
        self.element_list = None
        self.mouse_select_mode = None
        self.work_mode = None
        self.select_parts_mode = None
        self.show_entities = True
        self.show_nodes = True
        self.show_elements = False
        self.show_node_number = gv.default_show_node_number
        self.show_net = True
        self.scale = None


split_arc_and_line_choices_list = ['n parts evenly', '2 different parts', '3 parts different middle part',
                                   'graduate from left']

split_arc_and_line_mode_dictionary = {
    split_arc_and_line_choices_list[0]: gv.split_mode_evenly_n_parts,
    split_arc_and_line_choices_list[1]: gv.split_mode_2_parts_percentage_left,
    split_arc_and_line_choices_list[2]: gv.split_mode_3_parts_percentage_middle,
    split_arc_and_line_choices_list[3]: gv.split_mode_graduate_from_left
}


class SplitDialog(object):
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title(' Choose')
        self.window.geometry('305x160')
#        self.window.resizable(0, 0)

        self.frame_1 = tk.Frame(self.window)
        self.frame_1.pack(side=tk.TOP, fill=tk.BOTH, pady=5)
        self.frame_2 = tk.Frame(self.window)
        self.frame_2.pack(side=tk.TOP, fill=tk.BOTH, ipady=6)
        self.frame_3 = tk.Frame(self.window)
        self.frame_3.pack(side=tk.BOTTOM, fill=tk.BOTH, ipady=0)

        self.label_mode = tk.Label(self.frame_2, text='Split mode', padx=10)
        self.label_arg = tk.Label(self.frame_2, width=15, text='n', padx=7)

        self.label_mode.grid(row=0, column=0, sticky='w')
        self.label_arg.grid(row=0, column=1)

        self.split_choice_menu = ttk.Combobox(self.frame_2, width=25, values=split_arc_and_line_choices_list)
        self.entry_arg = tk.Entry(self.frame_2, width=6)
        self.split_choice_menu.grid(row=1, column=0, padx=10, pady=5)
        self.entry_arg.grid(row=1, column=1)

        button_ok = tk.Button(self.frame_3, text="OK", width=5, command=self.get_choice)
        button_cancel = tk.Button(self.frame_3, text="Cancel", width=5, command=self.window.destroy)
        button_ok.pack(side=tk.RIGHT, padx=5, pady=5)
        button_cancel.pack(side=tk.LEFT, padx=5)

        self.window.bind('<Key>', self.key)
        self.window.lift()

        # set default values
        self.split_choice_menu.current(0)
        self.split_choice_menu.bind("<<ComboboxSelected>>", self.mode_selected)
        self.entry_arg.insert(0, '3')
        self.choice = None

    def mode_selected(self, key):
        split_mode = self.split_choice_menu.get()
        if split_arc_and_line_mode_dictionary.get(split_mode) == gv.split_mode_evenly_n_parts:
            self.label_arg.config(text='n')
            self.entry_arg.delete(0, tk.END)
            self.entry_arg.insert(0, '2')
        elif split_arc_and_line_mode_dictionary.get(split_mode) == gv.split_mode_2_parts_percentage_left:
            self.label_arg.config(text='% left')
            self.entry_arg.delete(0, tk.END)
            self.entry_arg.insert(0, '33')
        elif split_arc_and_line_mode_dictionary.get(split_mode) == gv.split_mode_3_parts_percentage_middle:
            self.label_arg.config(text='% middle')
            self.entry_arg.delete(0, tk.END)
            self.entry_arg.insert(0, '70')
        elif split_arc_and_line_mode_dictionary.get(split_mode) == gv.split_mode_graduate_from_left:
            self.label_arg.config(text='% left - % right')
            self.entry_arg.delete(0, tk.END)
            self.entry_arg.insert(0, '10-20')

        self.entry_arg.focus_set()

    def get_choice(self):
        split_mode = split_arc_and_line_mode_dictionary.get(self.split_choice_menu.get())
        split_arg = self.entry_arg.get()
        # validity check
        is_valid = False
        min_arg = 2
        max_arg = gv.max_split_parts
        if split_mode == gv.split_mode_graduate_from_left:
            i = split_arg.find('-')
            if i < 0:
                print('choose format %left - %right')
                return
            left = split_arg[:i]
            right = split_arg[i+1:]
            try:
                left = int(left)
            except ValueError:
                print('choose a number for %left')
                return
            try:
                right = int(right)
            except ValueError:
                print('choose a number for %right')
                return
            if left + right > 100:
                print('%left + %right should not exceed 100%')
                return
            if left < gv.min_split_percentage or right < gv.min_split_percentage:
                print(f'%left - %right must be >= {gv.min_split_percentage}')
                return
            split_arg = (left, right)
            is_valid = True
        else:
            try:
                split_arg = int(split_arg)
            except ValueError:
                print('choose a number')
                return
            if split_mode == gv.split_mode_2_parts_percentage_left:
                min_arg = gv.min_split_percentage
                max_arg = gv.max_split_side_percentage
            elif split_mode == gv.split_mode_3_parts_percentage_middle:
                min_arg = gv.min_split_percentage
                max_arg = gv.max_split_middle_percentage
            if min_arg <= split_arg <= max_arg:
                is_valid = True
            else:
                print(f'Please select a valid number')
        if is_valid:
            self.choice = {
                'split_mode': split_mode,
                'arg': split_arg
            }
            self.window.destroy()

    def show(self):
        self.window.deiconify()
        self.window.wait_window()
        return self.choice

    def key(self, event):
        if event.keycode == 13:
            self.get_choice()


class SetInitialNetDialog(object):
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title(' Choose')
        self.window.geometry('290x120')
        self.window.resizable(0, 0)

        self.frame_1 = tk.Frame(self.window)
        self.frame_1.pack(side=tk.TOP, fill=tk.BOTH, pady=5)
        self.frame_2 = tk.Frame(self.window)
        self.frame_2.pack(side=tk.TOP, fill=tk.BOTH, ipady=6)
        self.frame_3 = tk.Frame(self.window)
        self.frame_3.pack(side=tk.BOTTOM, fill=tk.BOTH, ipady=0)

        self.label_arc_angle = tk.Label(self.frame_2, text='Max Arc angle', padx=10)
        self.label_line_length = tk.Label(self.frame_2, text='Max Line length', padx=10)
        self.label_circle_parts = tk.Label(self.frame_2, text='Circle parts', padx=10)

        self.label_arc_angle.grid(row=0, column=0)
        self.label_line_length.grid(row=0, column=1)
        self.label_circle_parts.grid(row=0, column=2)

        self.entry_arc_angle = tk.Entry(self.frame_2, width=5)
        self.entry_line_length = tk.Entry(self.frame_2, width=5)
        self.entry_circle_parts = tk.Entry(self.frame_2, width=5)

        self.entry_arc_angle.grid(row=1, column=0)
        self.entry_line_length.grid(row=1, column=1)
        self.entry_circle_parts.grid(row=1, column=2)

        button_ok = tk.Button(self.frame_3, text="OK", width=5, command=self.get_choice)
        button_cancel = tk.Button(self.frame_3, text="Cancel", width=5, command=self.window.destroy)
        button_ok.pack(side=tk.RIGHT, padx=5, pady=5)
        button_cancel.pack(side=tk.LEFT, padx=5)

        self.window.bind('<Key>', self.key)
        self.window.lift()

        # set default values
        self.entry_arc_angle.insert(0, gv.max_arc_angle_for_net_line)
        self.entry_line_length.insert(0, gv.max_line_length_for_net_line)
        self.entry_circle_parts.insert(0, gv.default_split_circle_parts)
        self.choice = None

    def get_choice(self):
        arc_angle = self.entry_arc_angle.get()
        line_length = self.entry_line_length.get()
        circle_parts = self.entry_circle_parts.get()

        min_arc_angle = 1
        max_arc_angle = 359
        min_length_percentage = math.pow(10, -gv.accuracy)
        max_length_percentage = 100
        min_circle_parts = 2
        max_circle_parts = 45

        # validity check
        try:
            arc_angle = float(arc_angle)
        except ValueError:
            print(f'choose arc angle between {min_arc_angle}-{max_arc_angle}')
            return
        try:
            line_length = float(line_length)
        except ValueError:
            print(f'choose line length percentage between {min_length_percentage}-{max_length_percentage}')
            return
        try:
            circle_parts = int(circle_parts)
        except ValueError:
            print(f'choose circle parts between {min_circle_parts}-{max_circle_parts}')
            return

        if arc_angle < min_arc_angle or arc_angle > max_arc_angle:
            print(f'choose arc angle between {min_arc_angle}-{max_arc_angle}')
            return
        if line_length < min_length_percentage or line_length > max_length_percentage:
            print(f'choose line length percentage between {min_length_percentage}-{max_length_percentage}')
            return
        if circle_parts < min_circle_parts or circle_parts > max_circle_parts:
            print(f'choose circle parts between {min_circle_parts}-{max_circle_parts}')
            return

        self.choice = {
            'arc_max_angle': arc_angle,
            'line_max_length': line_length,
            'circle_parts': circle_parts
        }
        self.window.destroy()

    def show(self):
        self.window.deiconify()
        self.window.wait_window()
        return self.choice

    def key(self, event):
        if event.keycode == 13:
            self.get_choice()


split_circle_choices_list = ['by longitude', 'by absolute angle']

split_circle_mode_dictionary = {
    split_circle_choices_list[0]: gv.split_mode_by_longitude,
    split_circle_choices_list[1]: gv.split_mode_by_angle
}


class SplitCircleDialog(object):
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title(' Choose')
        self.window.geometry('305x160')
        self.window.resizable(0, 0)

        self.frame_1 = tk.Frame(self.window)
        self.frame_1.pack(side=tk.TOP, fill=tk.BOTH, pady=5)
        self.frame_2 = tk.Frame(self.window)
        self.frame_2.pack(side=tk.TOP, fill=tk.BOTH, ipady=6)
        self.frame_3 = tk.Frame(self.window)
        self.frame_3.pack(side=tk.BOTTOM, fill=tk.BOTH, ipady=0)

        self.label_mode = tk.Label(self.frame_2, text='Split mode', padx=10)
        self.label_angle = tk.Label(self.frame_2, width=15, text='relative start angle', padx=7)
        self.label_parts = tk.Label(self.frame_2, width=5, text='#parts', padx=7)

        self.label_mode.grid(row=0, column=0)
        self.label_angle.grid(row=0, column=1)
        self.label_parts.grid(row=0, column=2)

        self.split_choice_menu = ttk.Combobox(self.frame_2, width=15, values=split_circle_choices_list)
        self.entry_angle = tk.Entry(self.frame_2, width=3)
        self.entry_parts = tk.Entry(self.frame_2, width=3)

        self.split_choice_menu.grid(row=1, column=0, padx=10, pady=5)
        self.entry_angle.grid(row=1, column=1)
        self.entry_parts.grid(row=1, column=2)

        button_ok = tk.Button(self.frame_3, text="OK", width=5, command=self.get_choice)
        button_cancel = tk.Button(self.frame_3, text="Cancel", width=5, command=self.window.destroy)
        button_ok.pack(side=tk.RIGHT, padx=5, pady=5)
        button_cancel.pack(side=tk.LEFT, padx=5)

        self.window.bind('<Key>', self.key)
        self.window.lift()

        # set default values
        self.split_choice_menu.current(0)
        self.split_choice_menu.bind("<<ComboboxSelected>>", self.mode_selected)
        self.entry_angle.insert(0, '45')
        self.entry_parts.insert(0, '4')
        self.choice = None

    def mode_selected(self, key):
        split_mode = self.split_choice_menu.get()
        if split_circle_mode_dictionary.get(split_mode) == gv.split_mode_by_longitude:
            self.label_angle.config(text='relative start angle')
            self.entry_angle.delete(0, tk.END)
            self.entry_angle.insert(0, '45')
        #  split_circle_mode_dictionary.get(split_mode) == gv.split_mode_by_angle
        else:
            self.label_angle.config(text='absolute start angle')
            self.entry_angle.delete(0, tk.END)
            self.entry_angle.insert(0, '0')

    def get_choice(self):
        split_mode = split_circle_mode_dictionary.get(self.split_choice_menu.get())
        angle = self.entry_angle.get()
        parts = self.entry_parts.get()
        # validity check
        try:
            angle = int(angle)
        except ValueError:
            print('choose a number for angle')
            return
        try:
            parts = int(parts)
        except ValueError:
            print('choose a number for #parts')
            return

        self.choice = {
            'angle': angle,
            'parts': parts
        }
        self.window.destroy()


    def show(self):
        self.window.deiconify()
        self.window.wait_window()
        return self.choice

    def key(self, event):
        if event.keycode == 13:
            self.get_choice()


