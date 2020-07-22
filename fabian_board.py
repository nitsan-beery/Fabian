from board import *
from fabian_classes import *
import ezdxf
import math
from tkinter import messagebox, ttk
from operator import attrgetter


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
        self.next_node_hash_index = 1
        self.nodes_hash = {"0": 0}
        self.net_line_list = []
        self.element_list = []
        self.longitude = None
        self.mouse_select_mode = gv.default_mouse_select_mode
        self.work_mode = gv.default_work_mode
        self.select_parts_mode = gv.default_select_parts_mode
        self.mark_option = gv.default_mark_option
        self.selected_part = None
        self.new_line_edge = [None, None]
        self.new_line_original_part = [None, None]
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

    def reset_board(self, empty_node_list=False, center_screen_position=True, reset_state=True):
        self.board.delete('all')
        if center_screen_position:
            self.set_screen_position(self.center.x, self.center.y)
        self.entity_list = []
        if empty_node_list:
            self.node_list = []
        else:
            self.node_list = [Node()]
            self.next_node_hash_index = 1
            self.nodes_hash = {"0": 0}
        self.net_line_list = []
        self.element_list = []
        self.longitude = None
        self.mouse_select_mode = gv.default_mouse_select_mode
        self.work_mode = gv.default_work_mode
        self.select_parts_mode = gv.default_select_parts_mode
        self.mark_option = gv.default_mark_option
        self.selected_part = None
        self.new_line_edge = [None, None]
        self.new_line_original_part = [None, None]
        self.new_line_edge_mark = [None, None]
        self.new_line_mark = None
        self.temp_line_mark = None
        self.temp_rect_start_point = None
        self.temp_rect_mark = None
        self.progress_bar = None
        if reset_state:
            self.state = []

    def resume_state(self):
        if len(self.state) < 1:
            return
        state = self.state[-1]
        self.reset_board(empty_node_list=True, center_screen_position=False, reset_state=False)
        for t in state.entity_list:
            e = Entity()
            e.get_data_from_tuple(t)
            self.entity_list.append(e)
        for t in state.node_list:
            n = Node()
            n.get_data_from_tuple(t)
            self.node_list.append(n)
        self.next_node_hash_index = state.next_node_hash_index
        self.nodes_hash = state.nodes_hash.copy()
        for t in state.net_line_list:
            line = NetLine()
            line.get_data_from_tuple(t)
            self.net_line_list.append(line)
        for t in state.element_list:
            element = Element()
            element.get_data_from_tuple(t)
            self.element_list.append(element)
        self.mouse_select_mode = state.mouse_select_mode
        self.work_mode = state.work_mode
        self.select_parts_mode = state.select_parts_mode
        self.show_entities = state.show_entities
        self.show_nodes = state.show_nodes
        self.show_elements = state.show_elements
        self.show_node_number = state.show_node_number
        self.show_net = state.show_net
        self.scale = state.scale
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
        state.next_node_hash_index = self.next_node_hash_index
        state.nodes_hash = self.nodes_hash.copy()
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
        state.mouse_select_mode = self.mouse_select_mode
        state.work_mode = self.work_mode
        state.select_parts_mode = self.select_parts_mode
        state.show_entities = self.show_entities
        state.show_nodes = self.show_nodes
        state.show_elements = self.show_elements
        state.show_node_number = self.show_node_number
        state.show_net = self.show_net
        state.scale = self.scale
        self.state.append(state)


    def mouse_1_pressed(self, key):
        if self.temp_rect_mark is not None:
            self.board.delete(self.temp_rect_mark)
        x, y = self.convert_keyx_keyy_to_xy(key.x, key.y)
        if self.selected_part is None:
            self.temp_rect_start_point = Point(x, y)
            return
        if self.selected_part is not None:
            if self.selected_part.part_type == gv.part_type_entity:
                e = self.entity_list[self.selected_part.index]
                p1 = e.left_bottom
                p2 = e.right_up
                d, p = self.get_distance_from_entity_and_nearest_point(Point(x, y), self.selected_part.index)
            elif self.selected_part.part_type == gv.part_type_net_line:
                line = self.net_line_list[self.selected_part.index]
                node_index = self.get_node_index_from_hash(line.start_node)
                node_1 = self.node_list[node_index]
                node_index = self.get_node_index_from_hash(line.end_node)
                node_2 = self.node_list[node_index]
                p1 = node_1.p
                p2 = node_2.p
                d, p = self.get_distance_from_line_and_nearest_point(Point(x, y), p1, p2)
        if self.mouse_select_mode == gv.mouse_select_mode_edge:
            d1 = p1.get_distance_to_point(Point(x, y))
            d2 = p2.get_distance_to_point(Point(x, y))
            p = p2
            if d1 < d2:
                p = p1

        # first point
        if self.new_line_edge[0] is None:
            self.new_line_edge[0] = p
            self.new_line_edge_mark[0] = self.draw_circle(p, gv.edge_line_mark_radius/self.scale)
            self.new_line_original_part[0] = self.selected_part
            return
        # remove selection of first point
        elif self.new_line_edge[0] == p:
            # only 1 edge exists
            self.board.delete(self.new_line_edge_mark[0])
            self.board.delete(self.temp_line_mark)
            if self.new_line_edge[1] is None:
                self.new_line_edge_mark[0] = None
                self.new_line_edge[0] = None
                self.new_line_original_part[0] = None
            # there is a second edge and a line between
            else:
                self.board.delete(self.new_line_mark)
                self.new_line_mark = None
                self.new_line_edge_mark[0] = self.new_line_edge_mark[1]
                self.new_line_edge[0] = self.new_line_edge[1]
                self.new_line_original_part[0] = self.new_line_original_part[1]
                self.new_line_edge_mark[1] = None
                self.new_line_edge[1] = None
                self.new_line_original_part[1] = None
            return

        # second point on the same entity or line
        if self.select_parts_mode == gv.mouse_select_mode_edge and (self.new_line_edge[0].is_equal(p1) or self.new_line_edge[0].is_equal(p2)):
            return

        # second point
        else:
            self.board.delete(self.temp_line_mark)
            if self.new_line_edge[1] is None:
                self.new_line_edge[1] = p
                self.new_line_original_part[1] = self.selected_part
                self.add_line()
            else:
                self.board.delete(self.new_line_edge_mark[1])
                self.new_line_edge_mark[1] = None
                self.board.delete(self.new_line_mark)
                self.new_line_mark = None
                self.new_line_original_part = None
                if self.new_line_edge[1] != p:
                    self.new_line_edge[1] = p
                    self.new_line_edge_mark[1] = self.draw_circle(p, gv.edge_line_mark_radius / self.scale)
                    self.new_line_mark = self.draw_line(self.new_line_edge[0], self.new_line_edge[1])
                else:
                    self.new_line_edge[1] = None
                    self.new_line_original_part[1] = None

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
            t2 = self.work_mode == gv.work_mode_dxf
            t3 = self.work_mode == gv.work_mode_inp and (self.select_parts_mode == gv.part_type_net_line or self.select_parts_mode == 'all')
            if t1 and (t2 or t3):
                mark_option = {
                    "mark": True,
                    "unmark": False
                }
                self.keep_state()
                marked_color = gv.marked_entity_color
                non_marked_color = gv.default_color
                part_list = self.entity_list
                list_name = gv.part_list_entities
                if t3:
                    part_list = self.net_line_list
                    marked_color = gv.marked_net_line_color
                    non_marked_color = gv.net_line_color
                    list_name = gv.part_list_net_lines
                i = 0
                for p in part_list:
                    if p.board_part in enclosed_parts:
                        if self.mark_option == gv.mark_option_mark or self.mark_option == gv.mark_option_unmark:
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
        if mode == gv.show_mode:
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
        work_mode_menu.add_command(label="DXF", command=lambda: self.change_work_mode(gv.work_mode_dxf))
        work_mode_menu.add_command(label="INP", command=lambda: self.change_work_mode(gv.work_mode_inp))
        work_mode_menu.add_separator()
        work_mode_menu.add_command(label="Quit")
        select_part_menu = tk.Menu(menu, tearoff=0)
        select_part_menu.add_command(label="Entities", command=lambda: self.change_select_parts_mode(gv.part_type_entity))
        select_part_menu.add_command(label="Net lines", command=lambda: self.change_select_parts_mode(gv.part_type_net_line))
        select_part_menu.add_command(label="all", command=lambda: self.change_select_parts_mode('all'))
        select_part_menu.add_separator()
        if self.work_mode == gv.work_mode_dxf:
            select_part_menu.add_command(label="Edges", command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_edge))
            select_part_menu.add_command(label="Points", command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_point))
            select_part_menu.add_separator()
        select_part_menu.add_command(label="Quit")
        mark_option_menu = tk.Menu(self.board, tearoff=0)
        mark_option_menu.add_command(label="mark", command=lambda: self.choose_mark_option(gv.mark_option_mark))
        mark_option_menu.add_command(label="unmark", command=lambda: self.choose_mark_option(gv.mark_option_unmark))
        mark_option_menu.add_command(label="invert", command=lambda: self.choose_mark_option(gv.mark_option_invert))
        mark_option_menu.add_separator()
        mark_option_menu.add_command(label="Quit", command=lambda: self.choose_mark_option("quit"))
        show_entities_menu = tk.Menu(menu, tearoff=0)
        show_entities_menu.add_command(label="Show Weak", command=lambda: self.set_all_dxf_entities_color(gv.weak_entity_color))
        show_entities_menu.add_command(label="Show Strong", command=lambda: self.set_all_dxf_entities_color(gv.default_color))
        show_entities_menu.add_command(label="Hide", command=lambda: self.hide_dxf_entities())
        show_entities_menu.add_separator()
        show_entities_menu.add_command(label="Quit")
        show_node_number_menu = tk.Menu(menu, tearoff=0)
        show_node_number_menu.add_command(label="Show", command=lambda: self.set_node_number_state(gv.show_mode))
        show_node_number_menu.add_command(label="Hide", command=lambda: self.set_node_number_state(gv.hide_mode))
        net_menu = tk.Menu(menu, tearoff=0)
        net_menu.add_command(label="show", command=lambda: self.change_show_net_mode(gv.show_mode))
        net_menu.add_command(label="hide", command=lambda: self.change_show_net_mode(gv.hide_mode))
        net_menu.add_command(label="clear", command=lambda: self.change_show_net_mode(gv.clear_mode))
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
        if self.new_line_edge[0] is not None:
            self.board.delete(self.temp_line_mark)
            menu.add_command(label="remove line", command=self.remove_temp_line)
            menu.add_separator()
        if self.selected_part is not None:
            menu.add_command(label="split", command=lambda: self.split_selected_part(gv.split_mode_evenly_n_parts))
            menu.add_command(label="split...", command=lambda: self.split_selected_part())
            if self.work_mode == gv.work_mode_inp and self.selected_part.part_type == gv.part_type_entity:
                menu.add_command(label="merge", command=self.merge)
            if self.work_mode == gv.work_mode_dxf or (self.work_mode == gv.work_mode_inp and self.selected_part.part_type == gv.part_type_net_line):
                menu.add_command(label="delete", command=self.remove_selected_part_from_list)
                menu.add_command(label="mark", command=self.mark_selected_part)
                menu.add_command(label="unmark", command=self.unmark_selected_part)
            menu.add_separator()
        if self.work_mode == gv.work_mode_dxf:
            if len(self.entity_list) > 0:
                mark_list = self.get_marked_parts(gv.part_list_entities)
                menu.add_command(label="mark all entities", command=self.mark_all_entities)
                menu.add_command(label="unmark all entities", command=self.unmark_all_entities)
                if len(mark_list) > 1:
                    menu.add_command(label="merge marked entities", command=lambda: self.merge(True))
                    menu.add_command(label="delete marked entities", command=self.remove_marked_entities_from_list)
                    menu.add_command(label="delete NON marked entities", command=self.remove_non_marked_entities_from_list)
                menu.add_separator()
        elif self.work_mode == gv.work_mode_inp:
            mark_list = self.get_marked_parts(gv.part_list_net_lines)
            if len(mark_list) > 1:
                menu.add_command(label="merge marked net lines", command=lambda: self.merge(True))
                menu.add_command(label="delete marked net lines", command=self.remove_marked_net_lines_from_list)
                menu.add_separator()
            menu.add_cascade(label='Nodes number', menu=show_node_number_menu)
            menu.add_cascade(label='Net lines', menu=net_menu)
            menu.add_cascade(label='Elements', menu=show_elements_menu)
            menu.add_cascade(label='Entities', menu=show_entities_menu)
            menu.add_separator()
            menu.add_command(label="Split arcs and lines", command=self.split_arcs_and_lines_for_inp)
            menu.add_command(label="Set net", command=self.set_net)
            menu.add_separator()
        menu.add_command(label="Quit")
        menu.post(key.x_root, key.y_root)

    def change_show_net_mode(self, mode):
        self.keep_state()
        changed = False
        if mode == gv.show_mode:
            if not self.show_net:
                self.show_net = True
                changed = True
        elif mode == gv.hide_mode:
            if self.show_net:
                self.show_net = False
                changed = True
        elif mode == gv.clear_mode:
            if len(self.net_line_list) > 0:
                self.reset_net(True)
                changed = True
        if changed:
            self.update_view()
        else:
            self.state.pop(-1)

    def change_work_mode(self, mode):
        self.work_mode = mode
        if self.selected_part is not None:
            self.remove_selected_part_mark()
        if mode.lower() == gv.work_mode_dxf:
            self.show_nodes = False
            self.show_net = False
            self.show_elements = False
            self.change_select_parts_mode(gv.part_type_entity)
            self.choose_mark_option(gv.mark_option_mark)
            self.set_all_dxf_entities_color(gv.default_color)
        elif mode.lower() == gv.work_mode_inp:
            self.split_all_circles_by_longitude()
            self.set_initial_net()
            tmp_list = self.get_unattached_nodes(True)
            if len(tmp_list) == 0:
                print('no unattached nodes')
            self.set_all_dxf_entities_color(gv.weak_entity_color)
            self.show_nodes = True
            self.show_net = True
            self.change_mouse_selection_mode(gv.mouse_select_mode_edge)
            self.change_select_parts_mode('all')
            self.choose_mark_option('quit')
        self.update_view()

    def change_mouse_selection_mode(self, mode):
        self.mouse_select_mode = mode

    def change_select_parts_mode(self, mode):
        self.remove_selected_part_mark()
        self.select_parts_mode = mode

    def motion(self, key):
        x, y = self.convert_keyx_keyy_to_xy(key.x, key.y)
        p = Point(x, y)
        d_entity = d_net_line = 100
        i_entity = i_net_line = None
        text = f'{round(x, gv.accuracy)}    {round(y, gv.accuracy)}'
        self.hide_text_on_screen()
        self.show_text_on_screen(text, 'lt')
        if self.new_line_edge[0] is not None:
            self.board.delete(self.temp_line_mark)
            self.temp_line_mark = self.draw_line(self.new_line_edge[0], p, gv.temp_line_color)
        if self.select_parts_mode == gv.part_type_entity or self.select_parts_mode == 'all':
            if len(self.entity_list) == 0:
                return
            i_entity, d_entity = self.find_nearest_entity(p, only_visible=True)
        if self.select_parts_mode == gv.part_type_net_line or self.select_parts_mode == 'all':
            if len(self.net_line_list) == 0:
                return
            i_net_line, d_net_line = self.find_nearest_net_line(p, only_visible=True)
        part_type = gv.part_type_entity
        d = d_entity
        i = i_entity
        if i_net_line is not None and (d is None or d_net_line < d):
            d = d_net_line
            i = i_net_line
            part_type = gv.part_type_net_line
        if i is None:
            return
        self.remove_selected_part_mark()
        if d*self.scale < 5:
            self.mark_part(i, part_type)

    def set_entity_edge_nodes(self, i):
        e = self.entity_list[i]
        e.nodes_list = []
        start_node = Node(e.start, entity=i)
        node_hash_index = self.add_node_to_node_list(start_node)
        e.add_node_to_entity_nodes_list(node_hash_index)
        node = self.node_list[self.get_node_index_from_hash(node_hash_index)]
        node.attached_entities.append(i)
        end_node = Node(e.end, entity=i)
        node_hash_index = self.add_node_to_node_list(end_node)
        e.add_node_to_entity_nodes_list(node_hash_index)
        node = self.node_list[self.get_node_index_from_hash(node_hash_index)]
        node.attached_entities.append(i)

    def get_split_line_points(self, p1, p2, split_mode=gv.split_mode_evenly_n_parts, split_arg=gv.default_split_parts):
        point_list = [p1]
        alfa = p1.get_alfa_to(p2) * math.pi / 180
        d = p1.get_distance_to_point(p2)
        start = p1
        if split_mode == gv.split_mode_evenly_n_parts:
            n = split_arg
            step = d / n
            for m in range(n):
                end = Point(start.x + step * math.cos(alfa), start.y + step * math.sin(alfa))
                point_list.append(end)
                start = end
        elif split_mode == gv.split_mode_2_parts_percentage_left:
            percentage_left = split_arg
            if p2.is_smaller_x_smaller_y(p1):
                percentage_left = 100-percentage_left
            d = d * percentage_left / 100
            new_point = Point(start.x + d * math.cos(alfa), start.y + d * math.sin(alfa))
            point_list.append(new_point)
            point_list.append(p2)
        elif split_mode == gv.split_mode_3_parts_percentage_middle:
            percentage_middle = split_arg
            percentage_side = (100 - percentage_middle) / 2
            d1 = d * percentage_side / 100
            d2 = d * (percentage_middle + percentage_side) / 100
            new_point_1 = Point(start.x + d1 * math.cos(alfa), start.y + d1 * math.sin(alfa))
            new_point_2 = Point(start.x + d2 * math.cos(alfa), start.y + d2 * math.sin(alfa))
            point_list.append(new_point_1)
            point_list.append(new_point_2)
            point_list.append(p2)
        return point_list

    def get_split_arc_points(self, arc, split_mode=gv.split_mode_evenly_n_parts, split_arg=gv.default_split_parts):
        point_list = [arc.start]
        start_angle = arc.arc_start_angle
        if split_mode == gv.split_mode_evenly_n_parts:
            n = split_arg
            angle = (arc.arc_end_angle - arc.arc_start_angle) / n
            for m in range(n):
                end_angle = start_angle + angle
                arc = Entity(shape=arc.shape, center=arc.center, radius=arc.radius, start_angle=start_angle,
                             end_angle=end_angle)
                point_list.append(arc.end)
                start_angle = end_angle
        # fix me - currently only split_mode_evenly_n_parts supported
        elif split_mode == gv.split_mode_2_parts_percentage_left:
            pass
        elif split_mode == gv.split_mode_3_parts_percentage_middle:
            pass
        return point_list

    def merge(self, marked_parts=False):
        self.keep_state()
        changed = False
        if marked_parts:
            if self.work_mode == gv.work_mode_dxf:
                changed = self.merge_entities()
            elif self.work_mode == gv.work_mode_inp:
                changed = self.merge_net_lines()
        # merge selected part
        elif self.selected_part is not None:
            if self.selected_part.part_type == gv.part_type_entity:
                changed = self.merge_entities()
            elif self.selected_part.part_type == gv.part_type_net_line:
                    changed = self.merge_net_lines()
        if changed:
            self.update_view()
        else:
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
        first_line = None
        # find first unattached line and node
        for i in range(len(part_list)):
            line_i = self.net_line_list[part_list[i]]
            is_line_i_start_node_connected = False
            is_line_i_end_node_connected = False
            for j in range(len(part_list)):
                if j == i:
                    continue
                line_j = self.net_line_list[part_list[j]]
                if line_i.start_node == line_j.start_node or line_i.start_node == line_j.end_node:
                    is_line_i_start_node_connected = True
                if line_i.end_node == line_j.start_node or line_i.end_node == line_j.end_node:
                    is_line_i_end_node_connected = True
                if is_line_i_start_node_connected and is_line_i_end_node_connected:
                    break
            if not is_line_i_start_node_connected:
                first_line = part_list[i]
                break
            elif not is_line_i_end_node_connected:
                first_line = part_list[i]
                line_i.start_node, line_i.end_node = line_i.end_node, line_i.start_node
                break
        if first_line is None:
            #debug
            print("can't find unattached line in sort_net_line_parts")
            return None
        entity = self.net_line_list[first_line].entity
        next_node = self.net_line_list[first_line].end_node
        sorted_list.append(first_line)
        part_list.remove(first_line)
        found_part = False
        # iterate list to find connected parts, add to list or return None if can't find
        while len(part_list) > 0:
            for j in part_list:
                found_part = False
                line = self.net_line_list[j]
                if line.entity != entity:
                    return None
                if line.start_node == next_node:
                    found_part = True
                elif line.end_node == next_node:
                    line.start_node, line.end_node = line.end_node, line.start_node
                    found_part = True
                if found_part:
                    sorted_list.append(j)
                    next_node = line.end_node
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
            found_part = False
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
            found_part = False
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
        if self.work_mode == gv.work_mode_dxf:
            e_list = self.get_marked_parts(gv.part_list_entities)
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
            self.remove_parts_from_list(e_list, gv.part_list_entities)
            self.entity_list.append(new_entity)
            self.show_entity(-1)
        # work mode inp
        else:
            if self.selected_part is None or self.selected_part.part_type != gv.part_type_entity:
                return False
            entity = self.entity_list[self.selected_part.index]
            entity_net_lines = self.get_lines_attached_to_entity(self.selected_part.index)
            if len(entity_net_lines) < 2:
                return False
            entity_start_node = entity.nodes_list[0]
            entity_end_node = entity.nodes_list[-1]
            entity.nodes_list = self.get_nodes_attached_to_lines(entity_net_lines)
            start_node = self.get_node_index_from_hash(entity_start_node)
            end_node = self.get_node_index_from_hash(entity_end_node)
            if start_node is not None and end_node is not None:
                p1 = self.node_list[start_node].p
                p2 = self.node_list[end_node].p
                self.add_line_to_net_list(p1, p2)
                self.net_line_list[-1].entity = self.selected_part.index
            self.remove_parts_from_list(entity_net_lines, gv.part_list_net_lines)
            self.clear_lonely_nodes(entity.nodes_list)
            entity.nodes_list = [entity_start_node, entity_end_node]
            #debug
            #print('after merge')
            #self.print_line_list()
        return True

    def merge_net_lines(self):
        if self.work_mode != gv.work_mode_inp:
            return False
        p_list = self.get_marked_parts(gv.part_list_net_lines)
        if len(p_list) < 2:
            return False
        p_list = self.sort_net_line_parts(p_list)
        if p_list is None:
            m = "can't merge strange lines"
            messagebox.showwarning(m)
            return False
        entity = self.net_line_list[p_list[0]].entity
        start_node = self.net_line_list[p_list[0]].start_node
        end_node = self.net_line_list[p_list[-1]].end_node
        new_line = NetLine(start_node, end_node, entity)
        # get intermediate nodes
        n_list = []
        for i in range(len(p_list)-1):
            line = self.net_line_list[p_list[i]]
            n_list.append(line.end_node)
        self.remove_parts_from_list(p_list, gv.part_list_net_lines)
        self.clear_lonely_nodes(n_list)
        self.net_line_list.append(new_line)
        self.show_net_line(-1)
        return True

    def split_part(self, s_part=None, split_mode=gv.split_mode_evenly_n_parts, split_additional_arg=gv.default_split_parts):
        if s_part is None:
            return
        self.keep_state()
        part = s_part.index
        if s_part.part_type == gv.part_type_entity and self.work_mode == gv.work_mode_dxf:
            changed = self.split_entity(part, split_mode, split_additional_arg)
        elif s_part.part_type == gv.part_type_entity and self.work_mode == gv.work_mode_inp:
            changed = self.split_net_line_by_entity(part, 0, -1, split_mode, split_additional_arg)
        # split net line
        else:
            changed = self.split_net_line(part, split_mode, split_additional_arg)
        if changed:
            self.remove_selected_part_mark()
            self.update_view()
        else:
            self.state.pop(-1)


    def split_selected_part(self, split_mode=None, split_arg=gv.default_split_parts):
        if self.selected_part is None:
            return
        s_part = self.selected_part
        if split_mode is None:
            split_mode = gv.split_mode_evenly_n_parts
            choice = SplitDialog(self.window_main).show()
            if choice is not None:
                split_mode = choice.get('split_mode')
                split_arg = choice.get('arg')
        self.split_part(s_part, split_mode, split_arg)

    def split_entity_by_point(self, s_part, p):
        if s_part.part_type != gv.part_type_entity:
            # fix me? - split net line
            return False
        e = self.entity_list[s_part.index]
        new_part_list = []
        if e.shape == 'ARC':
            angle_to_p = e.center.get_alfa_to(p)
            new_part_list.append(Entity('ARC', center=e.center, radius=e.radius, start_angle=e.arc_start_angle, end_angle=angle_to_p))
            new_part_list.append(Entity('ARC', center=e.center, radius=e.radius, start_angle=angle_to_p, end_angle=e.arc_end_angle))
        elif e.shape == 'LINE':
            new_part_list.append(Entity('LINE', start=e.start, end=p))
            new_part_list.append(Entity('LINE', start=p, end=e.end))
        elif e.shape == 'CIRCLE':
            return False
        for i in range(len(new_part_list)):
            self.entity_list.append(new_part_list[i])
            self.define_new_entity_color(-1)
            self.show_entity(-1)
        self.remove_parts_from_list([s_part.index], gv.part_list_entities)
        return True

    # split entity_list[i] into n parts
    def split_entity(self, part=0, split_mode=gv.split_mode_evenly_n_parts, split_additional_arg=gv.default_split_parts):
        # fix me
        # currently only split_mode_evenly_n_parts is supported
        n = split_additional_arg
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
            self.split_circle_by_longitude(part)
            return True
        self.remove_parts_from_list([part], gv.part_list_entities)
        for m in range(n):
            self.entity_list.append(new_part_list[m])
            self.define_new_entity_color(-1)
            self.show_entity(-1)
        return True

    def split_arcs_and_lines_for_inp(self):
        self.keep_state()
        hash_bottom_left = self.get_bottom_left_node()
        index_bottom_left = self.get_node_index_from_hash(hash_bottom_left)
        bottom_left = self.node_list[index_bottom_left].p
        hash_top_right = self.get_top_right_node()
        index_top_right = self.get_node_index_from_hash(hash_top_right)
        top_right = self.node_list[index_top_right].p
        d_dxf = bottom_left.get_distance_to_point(top_right)
        i = len(self.entity_list) - 1
        while i >= 0:
            e = self.entity_list[i]
            if e.shape == 'CIRCLE':
                continue
            n = n_length = 0
            d = e.start.get_distance_to_point(e.end)
            relative_length = d / d_dxf
            if e.shape == 'ARC':
                angle = e.arc_end_angle - e.arc_start_angle
                n = round(angle/gv.max_arc_angle_for_net_line)
                if relative_length > gv.max_arc_length_for_net_line:
                    n_length = round(relative_length / gv.max_arc_length_for_net_line)
            elif e.shape == 'LINE':
                if relative_length > gv.max_line_length_for_net_line:
                    n_length = round(relative_length / gv.max_line_length_for_net_line)
            if n_length > n:
                n = n_length
            if n > 1:
                self.split_net_line_by_entity(i, 0, -1, gv.split_mode_evenly_n_parts, n)
            i -= 1
        self.update_view()

    def split_all_circles_by_longitude(self, n=gv.default_split_circle_parts):
        longitude = self.get_longitude()
        i = len(self.entity_list) - 1
        while i >= 0:
            e = self.entity_list[i]
            if e.shape == 'CIRCLE':
                self.split_circle_by_longitude(i, longitude, n)
            i -= 1

    def split_circle_by_longitude(self, part, longitude=None, n=gv.default_split_circle_parts):
        if len(self.entity_list) < (part + 1):
            return 
        e = self.entity_list[part]
        if e.shape != 'CIRCLE':
            return
        start_angle = longitude
        if start_angle is None:
            start_angle = self.get_longitude()
        for i in range(n):
            end_angle = start_angle + (360/n)
            arc = Entity('ARC', center=e.center, radius=e.radius, start_angle=start_angle, end_angle=end_angle)
            self.entity_list.append(arc)
            start_angle = end_angle
        self.remove_parts_from_list([part], gv.part_list_entities)

    def split_net_line_by_point(self, part, p):
        new_lines = []
        line = self.net_line_list[part]
        new_node = Node(p, entity=None)
        new_node_index = self.add_node_to_node_list(new_node)
        new_lines.append(NetLine(line.start_node, new_node_index, None))
        new_lines.append(NetLine(new_node_index, line.end_node, None))
        self.remove_parts_from_list([part], gv.part_list_net_lines)

    def split_net_line_by_entity(self, part, start_node=0, end_node=-1, split_mode=gv.split_mode_evenly_n_parts,
                                 split_additional_arg=gv.default_split_parts):
        if self.work_mode != gv.work_mode_inp:
            return False
        old_lines = self.get_lines_attached_to_entity(part)
        if len(old_lines) < 1:
            # fix me
            return False
        entity = self.entity_list[part]
        if entity.shape == 'CIRCLE':
            return False
        entity_nodes = self.get_nodes_attached_to_lines(old_lines)
        start_hash_node = entity.nodes_list[0]
        end_hash_node = entity.nodes_list[-1]
        start_node_index = self.get_node_index_from_hash(start_hash_node)
        end_node_index = self.get_node_index_from_hash(end_hash_node)
        # fix me - currently only split_mode_evenly_n_parts supported
        if entity.shape == 'LINE':
            if start_node_index is None or end_node_index is None:
                #debug - fix me
                print('bug in split_net_line_by_entity')
            p1 = self.node_list[start_node_index].p
            p2 = self.node_list[end_node_index].p
            new_points = self.get_split_line_points(p1, p2, split_mode, split_additional_arg)
        # shape == 'ARC'
        else:
            arc = self.entity_list[part]
            new_points = self.get_split_arc_points(arc, split_mode, split_additional_arg)
        self.remove_parts_from_list(old_lines, gv.part_list_net_lines)
        self.clear_lonely_nodes(entity_nodes)
        for j in range(len(new_points) - 1):
            new_node = Node(new_points[j+1], entity=part)
            end_hash_node = self.add_node_to_node_list(new_node)
            end_node = self.node_list[self.get_node_index_from_hash(end_hash_node)]
            end_node.attached_entities.append(part)
            self.net_line_list.append(NetLine(start_hash_node, end_hash_node, part))
            start_hash_node = end_hash_node
        return True

    def split_net_line(self, part, split_mode=gv.split_mode_evenly_n_parts, split_additional_arg=gv.default_split_parts):
        if self.work_mode != gv.work_mode_inp:
            return False
        new_lines = []
        line = self.net_line_list[part]
        start_node_index = self.get_node_index_from_hash(line.start_node)
        end_node_index = self.get_node_index_from_hash(line.end_node)
        node1 = self.node_list[start_node_index]
        node2 = self.node_list[end_node_index]
        shape = 'LINE'
        if line.entity is not None:
            shape = self.entity_list[line.entity].shape
        if shape == 'LINE':
            new_points = self.get_split_line_points(node1.p, node2.p, split_mode, split_additional_arg)
        # line on ARC
        else:
            reference_arc = self.entity_list[line.entity]
            start_angle = reference_arc.center.get_alfa_to(node1.p)
            end_angle = reference_arc.center.get_alfa_to(node2.p)
            # set the correct order of start - end angles according to reference_arc start_angle
            accuracy = math.pow(10, -gv.accuracy)
            if start_angle + accuracy < reference_arc.arc_start_angle:
                start_angle += 360
            if end_angle + accuracy < reference_arc.arc_start_angle:
                end_angle += 360
            if end_angle < start_angle:
                start_angle, end_angle = end_angle, start_angle
            arc = Entity('ARC', reference_arc.center, reference_arc.radius, start_angle=start_angle, end_angle=end_angle)
            new_points = self.get_split_arc_points(arc, split_mode, split_additional_arg)
        start_node = line.start_node
        for j in range(len(new_points) - 1):
            new_node = Node(new_points[j+1], entity=None)
            end_node = self.add_node_to_node_list(new_node)
            new_lines.append(NetLine(start_node, end_node, line.entity))
            start_node = end_node
        self.remove_parts_from_list([part], gv.part_list_net_lines)
        for j in range(len(new_lines)):
            self.net_line_list.append(new_lines[j])
        return True

    # return all net lines crossed by line from p1 to p2
    # each line is tupled with mutual cross point
    def get_crossed_net_lines(self, p1, p2):
        net_lines_list = []
        if p1 is None or p2 is None:
            return net_lines_list
        for i in range(len(self.net_line_list)):
            p = self.get_mutual_point_of_net_line_with_crossing_line(i, p1, p2)
            if p is not None:
                net_lines_list.append((i, p))
        return net_lines_list

    # return mutual point of self.net_line_list[net_line] with crossing line p1-p2, None if there isn't
    def get_mutual_point_of_net_line_with_crossing_line(self, net_line, p1, p2):
        net_line = self.net_line_list[net_line]
        start_node_index = self.get_node_index_from_hash(net_line.start_node)
        end_node_index = self.get_node_index_from_hash(net_line.end_node)
        start_node = self.node_list[start_node_index]
        end_node = self.node_list[end_node_index]
        angle = -start_node.p.get_alfa_to(end_node.p)
        line_end = get_shifted_point(end_node.p, start_node.p, angle)
        p1 = get_shifted_point(p1, start_node.p, angle)
        p2 = get_shifted_point(p2, start_node.p, angle)
        if p1.y == p2.y:
            return None
        # x = where line p1-p2 crosses x axe
        x = p2.x - p2.y * (p2.x - p1.x) / (p2.y - p1.y)
        accuracy = math.pow(10, -gv.accuracy)
        if x-accuracy <= 0 or x+accuracy >= line_end.x:
            return None
        if p1.y * p2.y > 0:
            return None
        mutual_point = Point(x, 0)
        mutual_point = get_shifted_point(mutual_point, Point(0, 0), -angle)
        mutual_point.x += start_node.p.x
        mutual_point.y += start_node.p.y
        return mutual_point

    # return list of marked parts is list
    def get_marked_parts(self, list_name):
        mark_list = []
        part_list = []
        if list_name == gv.part_list_entities:
            part_list = self.entity_list
        elif list_name == gv.part_list_net_lines:
            part_list = self.net_line_list
        elif list_name == gv.part_list_nodes:
            part_list = self.node_list
        for i in range(len(part_list)):
            if part_list[i].is_marked:
                mark_list.append(i)
        return mark_list

    def show_part(self, part, list_name, with_number=False):
        if list_name == gv.part_list_entities:
            self.show_entity(part)
        elif list_name == gv.part_list_net_lines:
            self.show_net_line(part)
        elif list_name == gv.part_list_nodes:
            self.show_node(part, with_number)

    def hide_part(self, part, list_name):
        if list_name == gv.part_list_entities:
            self.hide_entity(part)
        elif list_name == gv.part_list_net_lines:
            self.hide_net_line(part)
        elif list_name == gv.part_list_nodes:
            self.hide_node(part)

    def set_part_color(self, list_name, part, color):
        self.hide_part(part, list_name)
        if list_name == gv.part_list_entities:
            self.entity_list[part].color = color
        elif list_name == gv.part_list_net_lines:
            self.net_line_list[part].color = color
        elif list_name == gv.part_list_nodes:
            part = self.get_node_index_from_hash(part)
            if part is not None:
                self.node_list[part].color = color
        self.show_part(part, list_name)

    def get_nodes_attached_to_lines(self, net_line_list):
        nodes_list = []
        for line_index in net_line_list:
            line = self.net_line_list[line_index]
            nodes_list.append(line.start_node)
            nodes_list.append(line.end_node)
        # remove duplicate parts from list
        nodes_list = list(dict.fromkeys(nodes_list))
        return nodes_list

    def clear_lonely_nodes(self, hash_node_list):
        lonely_nodes_list = []
        for n in hash_node_list:
            # modify attached lines
            self.set_lines_attached_to_node(n)
            node_index = self.get_node_index_from_hash(n)
            if node_index is not None:
                if len(self.node_list[node_index].attached_lines) == 0:
                    lonely_nodes_list.append(n)
        self.remove_parts_from_list(lonely_nodes_list, gv.part_list_nodes)

    def remove_parts_from_list(self, part_list, list_name):
        # remove duplicate parts from list
        part_list = list(dict.fromkeys(part_list))
        part_list = sorted(part_list, reverse=True)
        original_list = None
        if list_name == gv.part_list_nodes:
            for part in part_list:
                self.remove_node_from_node_list(part)
        else:
            if list_name == gv.part_list_entities:
                original_list = self.entity_list
            elif list_name == gv.part_list_net_lines:
                original_list = self.net_line_list
            for part in part_list:
                if part is None:
                    return
                self.hide_part(part, list_name)
                original_list.pop(part)
        self.remove_selected_part_mark()

    def get_lines_attached_to_entity(self, entity):
        net_lines = []
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            if line.entity == entity:
                net_lines.append(i)
        return net_lines

    # set all lines attached to node, and sort them by angle_to_second_node
    def set_lines_attached_to_node(self, node_hash_index):
        n = self.get_node_index_from_hash(node_hash_index)
        if n is None:
            return
        node = self.node_list[n]
        node.attached_lines = []
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            start_node_index = self.get_node_index_from_hash(line.start_node)
            end_node_index = self.get_node_index_from_hash(line.end_node)
            start_node = self.node_list[start_node_index]
            end_node = self.node_list[end_node_index]
            if node_hash_index == line.start_node:
                al = AttachedLine(i, line.end_node, start_node.p.get_alfa_to(end_node.p))
                node.attached_lines.append(al)
            elif node_hash_index == line.end_node:
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
                # debug
                #m = f'unexpected number of outer lines in set_node_expected_elements_and_exceptions'
                #print(m)
                return
            if num_outer_lines == 2:
                for i in range(len(node.attached_lines)):
                    if node.attached_lines[i].is_outer_line:
                        break
                if not node.attached_lines[i].is_outer_line:
                    #m = f"can't find the outer line in node: {n}"
                    #print(m)
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
        if self.work_mode == gv.work_mode_inp:
            self.entity_list[entity].color = gv.weak_entity_color
        else:
            self.entity_list[entity].color = gv.default_color

    # return the hash key of the exception nodes
    def get_exception_nodes(self):
        exception_list = []
        for i in range(1, len(self.node_list)):
            if len(self.node_list[i].exceptions) > 0:
                exception_list.append(self.node_list[i].hash_index)
        return exception_list

    # return hash index of the node that can make an element counter clockwise (default) or clockwise
    def get_next_relevant_node(self, current_node_hash_index, prev_node_hash_index, limit_angle=True, prev_angle=None, clockwise=False):
        current_node_index = self.get_node_index_from_hash(current_node_hash_index)
        prev_node_index = self.get_node_index_from_hash(prev_node_hash_index)
        attached_line_list = self.node_list[current_node_index].attached_lines
        if len(attached_line_list) == 0:
            return None, None
        current_node = self.node_list[current_node_index]
        prev_node = self.node_list[prev_node_index]
        if prev_angle is None:
            prev_angle = prev_node.p.get_alfa_to(current_node.p)
        next_node_hash_indx = None
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
            node_hash_index = l.second_node
            if node_hash_index == prev_node_hash_index:
                continue
            node_index = self.get_node_index_from_hash(node_hash_index)
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
                next_node_hash_indx = node_hash_index
                net_line = l
        return next_node_hash_indx, net_line

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
            node_hash_index = self.node_list[i].hash_index
            self.set_lines_attached_to_node(node_hash_index)
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

    # return list of unattached nodes with real index in list (not hash_index)
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

    # return index of node in node_list with same p, None if can't find
    def get_hash_index_of_node_with_point(self, p):
        for i in range(len(self.node_list)):
            node = self.node_list[i]
            if node.p.is_equal(p):
                return node.hash_index
        return None

    # return index of node in node_list with same hash_index
    def get_node_index_from_hash(self, hash_index):
        return self.nodes_hash.get(str(hash_index))

    # add the node if it's not in the list
    # return hash index of the node
    def add_node_to_node_list(self, n):
        hash_index = self.get_hash_index_of_node_with_point(n.p)
        n.hash_index = hash_index
        if hash_index is None:
            n.hash_index = self.next_node_hash_index
            self.node_list.append(n)
            i = len(self.node_list) - 1
            self.nodes_hash[str(self.next_node_hash_index)] = i
            self.next_node_hash_index += 1
        return n.hash_index

    # remove the node if it's in the list
    # update hash table
    def remove_node_from_node_list(self, hash_index):
        node_list_index = self.nodes_hash.get(str(hash_index))
        if node_list_index is None:
            return
        # update hash
        for i in range(node_list_index+1, len(self.node_list)):
            node_hash_index = self.node_list[i].hash_index
            self.nodes_hash[str(node_hash_index)] = i-1
        self.nodes_hash.pop(str(hash_index))
        self.hide_node(node_list_index)
        self.node_list.pop(node_list_index)

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
            line_entity = i
            line = NetLine(start_node, end_node, line_entity)
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
            start_node = self.get_node_index_from_hash(line.start_node)
            end_node = self.get_node_index_from_hash(line.end_node)
            print(f'{i}: start node: {start_node}   end node: {end_node}   entity: {line.entity}')

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

    # element list with index of node_list (not hash)
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
                node_hash_index = attached_line.second_node
                new_element_nodes = [fist_node]
                prev_node_hash_index = self.node_list[fist_node].hash_index
                # try to set a new element starting from node[i] to next_node
                while node_hash_index is not None:
                    node_index = self.get_node_index_from_hash(node_hash_index)
                    new_element_nodes.append(node_index)
                    next_node_hash_index, line = self.get_next_relevant_node(node_hash_index, prev_node_hash_index)
                    if line is not None:
                        if not line.is_available:
                            break
                        line.is_available = False
                    next_node_index = self.get_node_index_from_hash(next_node_hash_index)
                    if next_node_index == fist_node:
                        break
                    prev_node_hash_index = node_hash_index
                    node_hash_index = next_node_hash_index
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
            "next_node_hash_index": state.next_node_hash_index,
            "nodes_hash": state.nodes_hash,
            "net_line_list": state.net_line_list,
            "element_list": state.element_list,
            "mouse_select_mode": state.mouse_select_mode,
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
            print(f'\n{len(self.entity_list)} Entities in {filetype} file')
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
            self.center_view(True)
            self.change_work_mode(gv.work_mode_dxf)
        elif filetype == 'json':
            print('\nnew data file')
            data = self.load_json(filename=filename)
            state = FabianState()
            state.entity_list = data.get("entity_list")
            state.node_list = data.get("node_list")
            state.next_node_hash_index = data.get("next_node_hash_index")
            state.nodes_hash = data.get("nodes_hash")
            state.net_line_list = data.get("net_line_list")
            state.element_list = data.get("element_list")
            state.mouse_select_mode = data.get("mouse_select_mode")
            state.work_mode = data.get("work_mode")
            state.select_parts_mode = data.get("select_parts_mode")
            state.show_entities = data.get("show_entities")
            state.show_nodes = data.get("show_nodes")
            state.show_elements = data.get("show_elements")
            state.show_node_number = data.get("show_node_number")
            state.show_net = data.get("show_net")
            state.scale = data.get("scale")
            self.state.append(state)
            self.resume_state()
        self.set_accuracy()
        self.center_view()
        self.update_view()
        # debug
        #self.print_node_list()
        #self.print_line_list()

    def set_scale(self, left, right):
        object_width = right - left
        window_width = self.window_main.winfo_width()
        self.scale = window_width/(object_width*2.5)

    def center_view(self, set_scale=False):
        self.hide_text_on_screen()
        x, y = self.get_center(set_scale=set_scale)
        if x is None:
            self.set_screen_position(self.center.x, self.center.y)
        else:
            self.set_screen_position(x, y)

    # return x, y of center in canvas coordinates (default), or dxf coordinates, by entities (default) or nodes
    # left and right edges in dxf (xy) coordinates
    def get_center(self, canvas_coordinates=True, by_nodes=False, set_scale=False):
        if by_nodes:
            if len(self.node_list) < 2:
                left = right = bottom = top = 0
            else:
                left = right = self.node_list[1].p.x
                bottom = top = self.node_list[1].p.y
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
        if set_scale:
            self.set_scale(left, right)
        if canvas_coordinates:
            x, y = self.convert_xy_to_screen(x, y)
        return x, y

    def get_longitude(self):
        if len(self.entity_list) < 2:
            return None
        shape = None
        longest_line = 0
        longitude = None
        for e in self.entity_list:
            if e.shape == 'LINE' or e.shape == 'ARC':
                d_line = e.start.get_distance_to_point(e.end)
                if d_line > longest_line:
                    longest_line = d_line
                    longitude = e.left_bottom.get_alfa_to(e.right_up)
                    shape = e.shape
        # debug
        #print(f'longest - {shape}   d: {longest_line}   longitude: {longitude}\n')
        return longitude

    # return the hash index of the node
    def get_bottom_left_node(self):
        if len(self.node_list) < 2:
            return 0
        index = 1
        p = self.node_list[index].p
        for i in range(1, len(self.node_list)):
            if self.node_list[i].p.is_smaller_x_smaller_y(p, by_x=False):
                p = self.node_list[i].p
                index = i
        return self.node_list[index].hash_index

    # return the hash index of the node
    def get_top_right_node(self):
        if len(self.node_list) < 2:
            return 0
        index = 1
        p = self.node_list[index].p
        for i in range(1, len(self.node_list)):
            if p.is_smaller_x_smaller_y(self.node_list[i].p, by_x=False):
                p = self.node_list[i].p
                index = i
        return self.node_list[index].hash_index

    def mark_selected_part(self):
        if self.selected_part is None:
            return
        self.keep_state()
        i = self.selected_part.index
        if self.selected_part.part_type == gv.part_type_entity:
            e = self.entity_list[i]
            e.is_marked = True
            self.set_entity_color(i, gv.marked_entity_color)
        elif self.selected_part.part_type == gv.part_type_net_line:
            n = self.net_line_list[i]
            n.is_marked = True
            self.set_net_line_color(i, gv.marked_net_line_color)

    def unmark_selected_part(self):
        if self.selected_part is None:
            return
        self.keep_state()
        i = self.selected_part.index
        if self.selected_part.part_type == gv.part_type_entity:
            e = self.entity_list[i]
            e.is_marked = False
            self.set_entity_color(i, gv.default_color)
        elif self.selected_part.part_type == gv.part_type_net_line:
            n = self.net_line_list[i]
            n.is_marked = False
            self.set_net_line_color(i, gv.net_line_color)

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

    def remove_marked_net_lines_from_list(self):
        self.keep_state()
        temp_list = []
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            if line.is_marked:
                temp_list.append(i)
        if len(temp_list) > 0:
            self.remove_parts_from_list(temp_list, gv.part_list_net_lines)
            unattached_nodes = self.get_unattached_nodes(True)
            if len(unattached_nodes) > 0:
                hash_list = []
                for n in unattached_nodes:
                    node = self.node_list[n]
                    if len(node.attached_lines) == 0:
                        hash_list.append(node.hash_index)
                self.remove_parts_from_list(hash_list, gv.part_list_nodes)
            self.update_view()
        else:
            self.state.pop(-1)

    def remove_marked_entities_from_list(self):
        temp_list = []
        for e in self.entity_list:
            if not e.is_marked:
                temp_list.append(e)
        if len(temp_list) > 0:
            self.keep_state()
        for e in temp_list:
            e.board_part = None
        self.entity_list = temp_list
        self.remove_selected_part_mark()
        self.board.delete('all')
        self.show_dxf_entities()

    def remove_non_marked_entities_from_list(self):
        temp_list = []
        for e in self.entity_list:
            if e.is_marked:
                temp_list.append(e)
        if len(temp_list) > 0:
            self.keep_state()
        for e in temp_list:
            e.is_marked = False
            e.board_part = None
            e.color = gv.default_color
        self.entity_list = temp_list
        self.remove_temp_line()
        self.remove_selected_part_mark()
        self.board.delete('all')
        self.show_dxf_entities()

    def remove_selected_part_from_list(self):
        if self.selected_part is None:
            return
        self.keep_state()
        changed = False
        if self.selected_part.part_type == gv.part_type_entity and self.work_mode == gv.work_mode_dxf:
            changed = True
            self.remove_parts_from_list([self.selected_part.index], gv.part_list_entities)
        elif self.selected_part.part_type == gv.part_type_net_line and self.work_mode == gv.work_mode_inp:
            changed = True
            self.remove_parts_from_list([self.selected_part.index], gv.part_list_net_lines)
        if changed:
            self.remove_selected_part_mark()
        else:
            self.state.pop(-1)

    def remove_temp_line(self):
        if self.new_line_edge[1] is not None:
            self.board.delete(self.new_line_edge_mark[1])
            self.new_line_edge[1] = None
            self.new_line_original_part[1] = None
            self.board.delete(self.new_line_mark)
        if self.new_line_edge[0] is not None:
            self.board.delete(self.new_line_edge_mark[0])
            self.new_line_edge[0] = None
            self.new_line_original_part[0] = None
            self.board.delete(self.temp_line_mark)

    # add line from p1 to p2. s_part_1 and s_part_2 holds part type (entity or net_line) and index in list
    # by default the line to add is the line created by user selected points
    def add_line(self, p1=None, p2=None, s_part_1=None, s_part_2=None,
                 split_middle_lines_mode=gv.split_mode_evenly_n_parts, split_additional_arg=2):
        if p1 is None:
            p1 = self.new_line_edge[0]
        if p2 is None:
            p2 = self.new_line_edge[1]
        if p2 is None:
            return
        if s_part_1 is None:
            s_part_1 = self.new_line_original_part[0]
        if s_part_2 is None:
            s_part_2 = self.new_line_original_part[1]
        self.keep_state()
        if self.work_mode == gv.work_mode_dxf:
            if self.mouse_select_mode == gv.mouse_select_mode_point:
                entity_2 = self.entity_list[s_part_2.index]
                self.split_entity_by_point(s_part_1, p1)
                new_s_part_2_index = self.get_index_of_entity(entity_2)
                s_part_2.index = new_s_part_2_index
                self.split_entity_by_point(s_part_2, p2)
            self.add_line_to_entity_list(p1, p2)
        elif self.work_mode == gv.work_mode_inp:
            crossing_lines = self.get_crossed_net_lines(p1, p2)
            new_points = [p1, p2]
            i = len(crossing_lines) - 1
            while i >= 0:
                pair = crossing_lines[i]
                line = pair[0]
                self.split_net_line(line, split_middle_lines_mode, split_additional_arg)
                new_points.append(self.node_list[-1].p)
                i -= 1
            new_points = sort_list_point_by_distance_from_p(new_points, p1)
            start_point = new_points[0]
            for i in range(1, len(new_points)):
                end_point = new_points[i]
                self.add_line_to_net_list(start_point, end_point)
                start_point = end_point
        self.remove_temp_line()
        self.update_view()
        
    def get_index_of_entity(self, entity):
        for i in range(len(self.entity_list)):
            e = self.entity_list[i]
            if e.is_equal(entity):
                return i
        return None

    def add_line_to_net_list(self, p1, p2):
        if self.work_mode != gv.work_mode_inp:
            return
        start_node = self.get_hash_index_of_node_with_point(p1)
        end_node = self.get_hash_index_of_node_with_point(p2)
        if start_node is None or end_node is None:
            self.remove_temp_line()
            return
        line = NetLine(start_node, end_node)
        self.net_line_list.append(line)
        self.show_net_line(-1)

    def add_line_to_entity_list(self, p1, p2):
        if self.work_mode != gv.work_mode_dxf:
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
        start_node_hash = self.net_line_list[min_d_index].start_node
        end_node_hash = self.net_line_list[min_d_index].end_node
        start_node_index = self.get_node_index_from_hash(start_node_hash)
        end_node_index = self.get_node_index_from_hash(end_node_hash)
        if start_node_index is None or end_node_index is None:
            #debug
            print('fix me find_nearest_net_line min_d_index')
            return None, None
        p1 = self.node_list[start_node_index].p
        p2 = self.node_list[end_node_index].p
        min_d, nearest_point = self.get_distance_from_line_and_nearest_point(p, p1, p2)
        for i in range(len(self.net_line_list)):
            if only_visible and self.net_line_list[i].board_part is None:
                continue
            start_node_hash = self.net_line_list[i].start_node
            end_node_hash = self.net_line_list[i].end_node
            start_node_index = self.get_node_index_from_hash(start_node_hash)
            end_node_index = self.get_node_index_from_hash(end_node_hash)
            if start_node_index is None or end_node_index is None:
                # debug
                print('fix me find_nearest_net_line i loop')
                return None, None
            p1 = self.node_list[start_node_index].p
            p2 = self.node_list[end_node_index].p
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

    # part = index in node_list (not hash)
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
    # i = index in node_list (not hash)
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
                node_index = self.get_node_index_from_hash(n)
                poly.append(self.node_list[node_index].p)
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
        start_node = self.get_node_index_from_hash(line.start_node)
        end_node = self.get_node_index_from_hash(line.end_node)
        if start_node is None or end_node is None:
            #debug
            print('fix me show_net_line edge nodes missing')
            return
        p1 = self.node_list[start_node].p
        p2 = self.node_list[end_node].p
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

    def set_net_line_color(self, part, color):
        self.hide_net_line(part)
        self.net_line_list[part].color = color
        self.show_net_line(part)

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

    def mark_part(self, i, part_type, color=gv.mark_rect_color):
        self.selected_part = SelectedPart(index=i, part_type=part_type)
        if part_type == gv.part_type_entity:
            b = self.board.bbox(self.entity_list[i].board_part)
        # part_type == gv.part_type_net_line
        else:
            b = self.board.bbox(self.net_line_list[i].board_part)
        self.selected_part.board_part = self.board.create_rectangle(b, outline=color)

    def remove_selected_part_mark(self):
        if self.selected_part is None:
            return
        elif self.selected_part.board_part is None:
            self.selected_part = None
            return
        self.board.delete(self.selected_part.board_part)
        self.selected_part = None

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

            