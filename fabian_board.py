from board import *
from file_handling import *
from general_functions import *
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
        self.button_zoom_in.config(command=lambda: self.zoom_modified(4 / 3))
        self.button_zoom_out.config(command=lambda: self.zoom_modified(3 / 4))
        self.button_center = tk.Button(self.frame_2, text='Center view', command=lambda: self.center_view())
        self.button_clear = tk.Button(self.frame_2, text='Clear all', command=lambda: self.reset_board(reset_state=False))
        # debug
        self.button_print = tk.Button(self.frame_2, text='Print lines', command=self.print_line_list)
        self.button_center.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.button_clear.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)
        # debug
        #self.button_print.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.board.config(bg=gv.board_bg_color)

        self.entity_list = []
        self.node_list = [Node()]
        self.next_node_hash_index = 1
        self.nodes_hash = {"0": 0}
        self.net_line_list = []
        self.element_list = []
        self.corner_list = []
        self.inp_nets = []
        self.longitude = None
        self.mouse_select_mode = gv.default_mouse_select_mode
        self.work_mode = gv.default_work_mode
        self.select_parts_mode = gv.default_select_parts_mode
        self.mark_option = gv.default_mark_option
        self.selected_part = None
        self.mouse_click_point = Point(0, 0)
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
        self.show_corners = True
        self.show_inps = True
        self.progress_bar = None
        self.state = []
        self.redo_state = []

        self.board.bind('<Motion>', self.motion)
        self.board.bind('<Button-1>', self.mouse_1_pressed)
        self.board.bind('<B1-Motion>', self.mouse_1_motion)
        self.board.bind('<ButtonRelease-1>', self.mouse_1_released)
        self.board.bind('<Control-ButtonRelease-1>', self.control_mouse_1_released)
        self.board.bind('<Button-3>', self.mouse_3_pressed)
        self.board.bind('<Control-MouseWheel>', self.control_mouse_wheel)

        self.window_main.bind('<Delete>', self.remove_selected_part_from_list)
        self.window_main.bind('d', self.remove_selected_part_from_list)
        self.window_main.bind('m', self.mark_selected_part)
        self.window_main.bind('u', self.unmark_selected_part)
        self.window_main.bind('r', self.remove_temp_line)
        self.window_main.bind('<Control-z>', self.undo)
        self.window_main.bind('<Control-y>', self.redo)

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
        self.corner_list = []
        self.inp_nets = []
        self.longitude = None
        self.mouse_select_mode = gv.default_mouse_select_mode
        self.work_mode = gv.default_work_mode
        self.select_parts_mode = gv.default_select_parts_mode
        self.mark_option = gv.default_mark_option
        self.selected_part = None
        self.mouse_click_point = Point(0, 0)
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

    def undo(self, key=None):
        if len(self.state) > 0:
            self.keep_state()
            if len(self.redo_state) == gv.max_state_stack:
                self.redo_state.pop(0)
            state = self.state[-1]
            self.redo_state.append(state)
            self.state.pop(-1)
        self.resume_state()

    def redo(self, key=None):
        if len(self.redo_state) > 0:
            self.keep_state()
            state = self.redo_state[-1]
            self.state.append(state)
            self.redo_state.pop(-1)
            self.resume_state()

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
        for t in state.corner_list:
            corner = Corner()
            corner.get_data_from_tuple(t)
            self.corner_list.append(corner)
        for t in state.inp_nets:
            inp_net = InpNet()
            inp_net.get_data_from_tuple(t)
            self.inp_nets.append(inp_net)
        self.mouse_select_mode = state.mouse_select_mode
        self.work_mode = state.work_mode
        self.select_parts_mode = state.select_parts_mode
        self.show_entities = state.show_entities
        self.show_nodes = state.show_nodes
        self.show_elements = state.show_elements
        self.show_node_number = state.show_node_number
        self.show_net = state.show_net
        self.show_corners = state.show_corners
        self.show_inps = state.show_inps
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
        corner_list = []
        for e in self.corner_list:
            t = e.convert_into_tuple()
            corner_list.append(t)
        inp_nets = []
        for e in self.inp_nets:
            t = e.convert_into_tuple()
            inp_nets.append(t)
        state.entity_list = entity_list.copy()
        state.node_list = node_list.copy()
        state.net_line_list = net_list.copy()
        state.element_list = element_list.copy()
        state.corner_list = corner_list.copy()
        state.inp_nets = inp_nets.copy()
        state.mouse_select_mode = self.mouse_select_mode
        state.work_mode = self.work_mode
        state.select_parts_mode = self.select_parts_mode
        state.show_entities = self.show_entities
        state.show_nodes = self.show_nodes
        state.show_elements = self.show_elements
        state.show_node_number = self.show_node_number
        state.show_net = self.show_net
        state.show_corners = self.show_corners
        state.show_inps = self.show_inps
        state.scale = self.scale
        self.state.append(state)

    def mouse_1_pressed(self, key):
        if self.temp_rect_mark is not None:
            self.board.delete(self.temp_rect_mark)
        x, y = self.convert_keyx_keyy_to_xy(key.x, key.y)
        mouse_point = Point(x, y)
        self.mouse_click_point = mouse_point
        p = p1 = p2 = mouse_point
        if self.selected_part is None:
            self.temp_rect_start_point = mouse_point
            return
        # selected part is not None
        if self.selected_part.part_type == gv.part_type_entity:
            e = self.entity_list[self.selected_part.index]
            if e.shape == 'CIRCLE':
                return
            p1 = e.left_bottom
            p2 = e.right_up
            d, p = self.get_distance_from_entity_and_nearest_point(Point(x, y), self.selected_part.index)
        # self.selected_part.part_type == gv.part_type_net_line
        elif self.selected_part.part_type == gv.part_type_net_line:
            line = self.net_line_list[self.selected_part.index]
            node_index = get_index_from_hash(self.nodes_hash, line.start_node)
            p1 = self.get_node_p(line.start_node)
            p2 = self.get_node_p(line.end_node)
            d, p = self.get_distance_from_line_and_nearest_point(Point(x, y), p1, p2)
        if self.mouse_select_mode == gv.mouse_select_mode_point and self.work_mode == gv.work_mode_inp:
            self.new_line_edge[0] = p
            self.keep_state()
            self.split_selected_part(gv.split_mode_2_parts_by_point)
            self.mouse_select_mode = gv.mouse_select_mode_edge
            return
        if self.mouse_select_mode != gv.mouse_select_mode_point:
            d1 = p1.get_distance_to_point(mouse_point)
            d2 = p2.get_distance_to_point(mouse_point)
            p = p2
            if d1 < d2:
                p = p1

        if self.mouse_select_mode == gv.mouse_select_mode_corner:# and self.work_mode == gv.work_mode_inp:
            corner = Corner()
            node_hash_index = self.get_hash_index_of_node_with_point(p)
            #debug
            if node_hash_index is None:
                print("can't find match node for corner")
                return
            corner.hash_node = node_hash_index
            self.add_corner_to_corner_list(corner)
            return

        # first point
        if self.new_line_edge[0] is None:
            if self.mouse_select_mode == gv.mouse_select_mode_rotate_net and self.inp_nets[-1].rotation_point is None:
                self.inp_nets[-1].rotation_point = InpRotationPoint(p)
                self.show_inp_rotation_point()
                return
            self.new_line_edge[0] = p
            self.new_line_edge_mark[0] = self.draw_circle(p, gv.edge_line_mark_radius/self.scale)
            self.new_line_original_part[0] = self.selected_part
            if self.mouse_select_mode == gv.mouse_select_mode_copy_net or \
                    self.mouse_select_mode == gv.mouse_select_mode_move_net or \
                    self.mouse_select_mode == gv.mouse_select_mode_rotate_net:
                self.select_parts_mode = gv.part_type_entity
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
            # keep second point (make it first)
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
        if self.select_parts_mode == gv.mouse_select_mode_edge and (self.new_line_edge[0].is_equal(p1) or
                                                                    self.new_line_edge[0].is_equal(p2)):
            return

        # valid second point - add line or handle net
        else:
            self.board.delete(self.temp_line_mark)
            #  handle net
            if self.mouse_select_mode == gv.mouse_select_mode_copy_net or \
                    self.mouse_select_mode == gv.mouse_select_mode_move_net or \
                    self.mouse_select_mode == gv.mouse_select_mode_flip_net or \
                    self.mouse_select_mode == gv.mouse_select_mode_rotate_net:
                if len(self.inp_nets) < 1:
                    self.remove_temp_line()
                    return
                inp_node_list = self.inp_nets[-1].node_list
                reference_point = self.new_line_edge[0]
                if is_point_in_node_list(reference_point, inp_node_list):
                    self.keep_state()
                    diff_x = p.x - self.new_line_edge[0].x
                    diff_y = p.y - self.new_line_edge[0].y
                    new_inp_net = InpNet()
                    new_inp_net.node_list = self.inp_nets[-1].node_list.copy()
                    new_inp_net.elements = self.inp_nets[-1].elements.copy()
                    if self.mouse_select_mode == gv.mouse_select_mode_flip_net:
                        new_inp_net = new_inp_net.get_fliped_net(self.new_line_edge[0], p)
                    elif self.mouse_select_mode == gv.mouse_select_mode_rotate_net:
                        new_inp_net.rotation_point = self.inp_nets[-1].rotation_point
                        angle1 = self.inp_nets[-1].rotation_point.reference_point.get_alfa_to(self.new_line_edge[0])
                        angle2 = self.inp_nets[-1].rotation_point.reference_point.get_alfa_to(p)
                        rotation_angle = angle2 - angle1
                        new_inp_net = new_inp_net.get_rotated_net(rotation_angle)
                        self.clear_inp_rotation_point()
                    # copy or move
                    else:
                        new_inp_net = new_inp_net.get_shifted_net(diff_x, diff_y)
                    if self.mouse_select_mode != gv.mouse_select_mode_copy_net:
                        self.hide_inp(-1)
                        self.inp_nets.pop(-1)
                    self.add_inp_net(new_inp_net.node_list, new_inp_net.elements)
                    self.mouse_select_mode = gv.mouse_select_mode_edge
                    self.select_parts_mode = gv.part_type_entity
                else:
                    print('choose reference point on INP net (white parts)')
                self.remove_temp_line()
                return
            # add line
            else:
                self.keep_state()
                self.new_line_edge[1] = p
                self.new_line_original_part[1] = self.selected_part
                new_points = self.add_line()
                if new_points is not None:
                    start_point = new_points[0]
                    for i in range(1, len(new_points)):
                        end_point = new_points[i]
                        self.add_line_to_net_list_by_points(start_point, end_point)
                        start_point = end_point
                self.remove_temp_line()
                self.update_view()

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

    def control_mouse_1_released(self, key):
        x, y = self.convert_keyx_keyy_to_xy(key.x, key.y)
        mouse_point = Point(x, y)
        if self.work_mode == gv.work_mode_inp or (self.work_mode == gv.work_mode_dxf and self.select_parts_mode == gv.part_type_net_line):
            if self.mouse_select_mode != gv.mouse_select_mode_point and self.new_line_edge[0] is not None and not self.mouse_click_point.is_equal(mouse_point):
                node_index = get_index_of_node_with_point_in_list(self.new_line_edge[0], self.node_list)
                self.keep_state()
                self.node_list[node_index].p = mouse_point
                self.remove_temp_line()
                self.update_view()
        if self.temp_rect_mark is not None:
            self.board.delete(self.temp_rect_mark)
            self.temp_rect_mark = None
        self.temp_rect_start_point = None

    def mouse_1_released(self, key):
        # mark parts inside the "choose" rect
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
                non_marked_color = gv.default_entity_color
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

    def mouse_3_pressed(self, key):
        menu = tk.Menu(self.board, tearoff=0)
        work_mode_menu = tk.Menu(menu, tearoff=0)
        work_mode_menu.add_command(label="DXF", command=lambda: self.change_work_mode(gv.work_mode_dxf))
        work_mode_menu.add_command(label="INP", command=lambda: self.change_work_mode(gv.work_mode_inp))
        work_mode_menu.add_separator()
        work_mode_menu.add_command(label="Quit")
        select_part_menu = tk.Menu(menu, tearoff=0)
        if self.work_mode == gv.work_mode_inp or len(self.inp_nets) > 0:
            select_part_menu.add_command(label="Entities", command=lambda: self.change_select_parts_mode(gv.part_type_entity))
            select_part_menu.add_command(label="Net lines", command=lambda: self.change_select_parts_mode(gv.part_type_net_line))
            select_part_menu.add_command(label="both", command=lambda: self.change_select_parts_mode('all'))
            select_part_menu.add_separator()
        select_part_menu.add_command(label="Edges", command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_edge))
        select_part_menu.add_command(label="Points", command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_point))
        select_part_menu.add_separator()
        select_part_menu.add_command(label="Quit")
        mark_option_menu = tk.Menu(self.board, tearoff=0)
        mark_option_menu.add_command(label="Mark", command=lambda: self.choose_mark_option(gv.mark_option_mark))
        mark_option_menu.add_command(label="Unmark", command=lambda: self.choose_mark_option(gv.mark_option_unmark))
        mark_option_menu.add_command(label="Invert", command=lambda: self.choose_mark_option(gv.mark_option_invert))
        mark_option_menu.add_separator()
        mark_option_menu.add_command(label="Quit", command=lambda: self.choose_mark_option("quit"))
        show_entities_menu = tk.Menu(menu, tearoff=0)
        show_entities_menu.add_command(label="Show Weak", command=lambda: self.set_all_entities_color(gv.weak_entity_color))
        show_entities_menu.add_command(label="Show Strong", command=lambda: self.set_all_entities_color(gv.default_entity_color))
        show_entities_menu.add_command(label="Hide", command=lambda: self.hide_all_entities())
        show_entities_menu.add_separator()
        show_entities_menu.add_command(label="Quit")
        show_node_menu = tk.Menu(menu, tearoff=0)
        show_node_menu.add_command(label="Show with numbers", command=lambda: self.set_node_number_state(gv.show_mode))
        show_node_menu.add_command(label="Show without numbers", command=lambda: self.set_node_number_state(gv.hide_mode))
        show_node_menu.add_command(label="Hide", command=self.hide_all_nodes)
        show_net_menu = tk.Menu(menu, tearoff=0)
        show_net_menu.add_command(label="Show", command=lambda: self.change_show_net_mode(gv.show_mode))
        show_net_menu.add_command(label="Hide", command=lambda: self.change_show_net_mode(gv.hide_mode))
        show_net_menu.add_command(label="Clear", command=lambda: self.change_show_net_mode(gv.clear_mode))
        show_inp_menu = tk.Menu(menu, tearoff=0)
        show_inp_menu.add_command(label="Show", command=lambda: self.change_show_inp_mode(gv.show_mode))
        show_inp_menu.add_command(label="Hide", command=lambda: self.change_show_inp_mode(gv.hide_mode))
        show_inp_menu.add_command(label="Clear", command=lambda: self.change_show_inp_mode(gv.clear_mode))
        show_elements_menu = tk.Menu(menu, tearoff=0)
        show_elements_menu.add_command(label="Show", command=self.show_all_elements)
        show_elements_menu.add_command(label="Hide", command=self.hide_all_elements)

        menu.add_command(label="Undo", command=self.undo)
        menu.add_command(label="Redo", command=self.redo)
        menu.add_separator()
        menu.add_cascade(label='Select mode', menu=select_part_menu)
        menu.add_separator()
        menu.add_cascade(label='Work mode', menu=work_mode_menu)
        menu.add_separator()
        menu.add_cascade(label='Mark mode', menu=mark_option_menu)
        menu.add_separator()
        if self.new_line_edge[0] is not None:
            self.board.delete(self.temp_line_mark)
            menu.add_command(label="Remove line", command=self.remove_temp_line)
            menu.add_separator()
        if self.selected_part is not None:
            if self.new_line_edge[0] is not None:
                menu.add_command(label="Split by point", command=lambda: self.split_selected_part(gv.split_mode_2_parts_by_point))
            menu.add_command(label="split", command=lambda: self.split_selected_part(gv.split_mode_evenly_n_parts))
            menu.add_command(label="split...", command=lambda: self.split_selected_part())
            if self.work_mode == gv.work_mode_inp and self.selected_part.part_type == gv.part_type_entity:
                menu.add_command(label="Merge", command=self.merge)
                entity = self.entity_list[self.selected_part.index]
                if entity.shape == 'ARC':
                    menu.add_command(label="Extend arc", command=self.extend_arc)
            if self.work_mode == gv.work_mode_dxf or (self.work_mode == gv.work_mode_inp and self.selected_part.part_type == gv.part_type_net_line):
                menu.add_command(label="Delete", command=self.remove_selected_part_from_list)
                menu.add_command(label="Mark", command=self.mark_selected_part)
                menu.add_command(label="Unmark", command=self.unmark_selected_part)
            menu.add_separator()
        if self.work_mode == gv.work_mode_dxf:
            if len(self.entity_list) > 0:
                mark_list = self.get_marked_parts(gv.part_list_entities)
                menu.add_command(label="Mark all entities", command=self.mark_all_entities)
                menu.add_command(label="Unmark all entities", command=self.unmark_all_entities)
                if len(mark_list) > 0:
                    menu.add_command(label="Merge marked entities", command=lambda: self.merge(True))
                    menu.add_command(label="Delete marked entities", command=self.remove_marked_entities_from_list)
                    menu.add_command(label="Delete NON marked entities", command=self.remove_non_marked_entities_from_list)
                menu.add_separator()
                if len(self.node_list) > 1:
                    menu.add_cascade(label='Nodes', menu=show_node_menu)
                    menu.add_separator()
                if len(self.inp_nets) > 0:
                    menu.add_command(label="Copy net", command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_copy_net))
                    menu.add_command(label="Move net", command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_move_net))
                    menu.add_command(label="Flip net", command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_flip_net))
                    if self.inp_nets[-1].rotation_point is not None:
                        menu.add_command(label="Clear reference point", command=self.clear_inp_rotation_point)
                    else:
                        menu.add_command(label="Rotate net", command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_rotate_net))
                    menu.add_separator()
                    menu.add_command(label="Set Corners",
                                     command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_corner))
                    if len(self.corner_list) > 0:
                        menu.add_command(label="Clear corners",
                                         command=lambda: self.handle_corners(gv.handle_corners_mode_clear))
                    menu.add_command(label="Match net", command=self.match_inp_net)
                    if len(self.inp_nets) > 1:
                        menu.add_command(label="Merge nets", command=self.merge_inp_nets)
                    menu.add_cascade(label='Show / Hide nets', menu=show_inp_menu)
                    menu.add_separator()
        elif self.work_mode == gv.work_mode_inp:
            mark_list = self.get_marked_parts(gv.part_list_net_lines)
            if len(mark_list) > 0:
                menu.add_command(label="Merge marked net lines", command=lambda: self.merge(True))
                menu.add_command(label="Delete marked net lines", command=self.remove_marked_net_lines_from_list)
                menu.add_command(label="Unmark all net lines", command=self.unmark_all_net_lines)
                menu.add_separator()
            menu.add_cascade(label='Nodes', menu=show_node_menu)
            menu.add_cascade(label='Net lines', menu=show_net_menu)
            menu.add_cascade(label='INP net', menu=show_inp_menu)
            menu.add_cascade(label='Elements', menu=show_elements_menu)
            menu.add_cascade(label='Entities', menu=show_entities_menu)
            menu.add_separator()
            if len(self.corner_list) == 4:
                set_corner_net_menu = tk.Menu(menu, tearoff=0)
                set_corner_net_menu.add_command(label="Both sides (1 -> 4 first)", command=lambda: self.handle_corners(gv.handle_corners_mode_set_net, gv.corners_set_net_both))
                set_corner_net_menu.add_command(label="1 -> 4", command=lambda: self.handle_corners(gv.handle_corners_mode_set_net, gv.corners_set_net_1_4))
                set_corner_net_menu.add_command(label="1 -> 2", command=lambda: self.handle_corners(gv.handle_corners_mode_set_net, gv.corners_set_net_1_2))
                menu.add_cascade(label="Set net between corners", menu=set_corner_net_menu)
            else:
                menu.add_command(label="Set Corners", command=lambda: self.change_mouse_selection_mode(gv.mouse_select_mode_corner))
            if len(self.corner_list) > 0:
                menu.add_command(label="Clear corners",
                                         command=lambda: self.handle_corners(gv.handle_corners_mode_clear))
                menu.add_separator()
            menu.add_command(label="Set net", command=self.set_net)
            menu.add_command(label="Set initial border nodes...", command=self.set_initial_border_nodes)
            menu.add_command(label="Clear inner net", command=self.clear_net)
            menu.add_separator()
        menu.add_command(label="Quit")
        menu.post(key.x_root, key.y_root)

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

    def choose_mark_option(self, option):
        self.mark_option = option

    def set_node_number_state(self, mode):
        changed = False
        if not self.show_nodes:
            self.show_nodes = True
            changed = True
        if mode == gv.show_mode:
            should_show = True
        else:
            should_show = False
        if self.show_node_number != should_show:
            changed = True
            self.show_node_number = should_show
        if changed:
            self.keep_state()
            self.update_view()

    def change_show_net_mode(self, mode, with_elements=False):
        self.keep_state()
        changed = False
        if mode == gv.show_mode:
            if not self.show_net:
                self.show_net = True
                if with_elements:
                    self.show_elements = True
                changed = True
        elif mode == gv.hide_mode:
            if self.show_net:
                self.show_net = False
                self.show_elements = False
                changed = True
        elif mode == gv.clear_mode:
            if len(self.net_line_list) > 0:
                if with_elements:
                    self.reset_net()
                else:
                    self.clear_net()
                changed = True
        if changed:
            self.update_view()
        else:
            self.state.pop(-1)

    def change_show_inp_mode(self, mode):
        self.keep_state()
        changed = False
        if mode == gv.show_mode:
            if not self.show_inps:
                self.show_inps = True
                changed = True
        elif mode == gv.hide_mode:
            if self.show_inps:
                self.clear_corner_list()
                self.hide_all_inp_nets()
                self.show_inps = False
                self.change_mouse_selection_mode(gv.mouse_select_mode_edge)
                changed = True
        elif mode == gv.clear_mode:
            if len(self.inp_nets) > 0:
                self.clear_corner_list()
                self.hide_all_inp_nets()
                self.inp_nets = []
                self.change_mouse_selection_mode(gv.mouse_select_mode_edge)
                changed = True
        if changed:
            if self.work_mode == gv.work_mode_dxf:
                self.state.pop(-1)
                self.change_show_net_mode(mode, with_elements=True)
            else:
                self.update_view()
        else:
            self.state.pop(-1)

    def change_work_mode(self, mode):
        if mode == self.work_mode:
            return
        self.remove_selected_part_mark()
        self.remove_temp_line()
        self.keep_state()
        self.mouse_select_mode = gv.mouse_select_mode_edge
        self.choose_mark_option(gv.mark_option_mark)
        self.clear_corner_list()
        self.change_show_inp_mode(gv.clear_mode)
        if mode == gv.work_mode_dxf:
            self.reset_net()
            self.show_nodes = False
            self.show_net = False
            self.show_elements = False
            self.show_entities = True
            self.select_parts_mode = gv.part_type_entity
            self.set_all_entities_color(gv.default_entity_color)
        elif mode == gv.work_mode_inp:
            self.set_initial_net()
            tmp_list = self.get_unattached_nodes()
            if len(tmp_list) == 0:
                pass
                # optional
                # print('no unattached nodes')
            self.set_all_entities_color(gv.weak_entity_color)
            self.show_entities = True
            self.show_nodes = True
            self.show_net = True
            self.show_corners = True
            self.select_parts_mode = 'all'
            self.choose_mark_option('quit')
        self.work_mode = mode
        self.update_view()

    def change_mouse_selection_mode(self, mode):
        self.remove_temp_line()
        if self.mouse_select_mode != mode:
            self.mouse_select_mode = mode
        if mode != gv.mouse_select_mode_rotate_net:
            self.clear_inp_rotation_point()
        if mode == gv.mouse_select_mode_copy_net or mode == gv.mouse_select_mode_move_net or \
                mode == gv.mouse_select_mode_flip_net or mode == gv.mouse_select_mode_rotate_net:
            self.select_parts_mode = gv.part_type_net_line
        elif self.work_mode == gv.work_mode_dxf:
            if mode == gv.mouse_select_mode_corner:
                self.select_parts_mode = gv.part_type_net_line
            else:
                self.select_parts_mode = gv.part_type_entity

    def change_select_parts_mode(self, mode):
        self.remove_temp_line()
        self.remove_selected_part_mark()
        if mode != self.select_parts_mode:
            self.select_parts_mode = mode
        if self.mouse_select_mode == gv.mouse_select_mode_corner:
            self.mouse_select_mode = gv.mouse_select_mode_edge

    def handle_corners(self, mode, arg=gv.corners_set_net_both):
        if mode == gv.handle_corners_mode_clear:
            self.clear_corner_list(True)
            if self.work_mode == gv.work_mode_dxf:
                self.select_parts_mode = gv.part_type_entity
        elif mode == gv.handle_corners_mode_set_net:
            self.keep_state()
            changed = self.set_net_between_corners(arg)
            if changed:
                self.clear_corner_list()
                self.mouse_select_mode = gv.mouse_select_mode_edge
                self.update_view()
            else:
                self.state.pop(-1)

    def set_entity_edge_nodes(self, i):
        e = self.entity_list[i]
        if e.shape == 'CIRCLE':
            return
        e.nodes_list = []
        start_node = Node(e.start, entity=i)
        node_hash_index = self.add_node_to_node_list(start_node)
        e.add_node_to_entity_nodes_list(node_hash_index)
        end_node = Node(e.end, entity=i)
        node_hash_index = self.add_node_to_node_list(end_node)
        e.add_node_to_entity_nodes_list(node_hash_index)

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
        for i in part_list:
            ei = self.entity_list[i]
            if ei.shape != e_0.shape:
                return None
        if shape == 'CIRCLE':
            return None
        elif shape == 'ARC':
            # find smallest start_angle, and check all parts with same center and radius
            for i in part_list:
                ei = self.entity_list[i]
                if ei.center != e_0.center or ei.radius != e_0.radius:
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

    def extend_arc(self):
        if self.work_mode != gv.work_mode_inp:
            return
        if self.selected_part is None or self.selected_part.part_type != gv.part_type_entity:
            return
        entity_index = self.selected_part.index
        entity = self.entity_list[entity_index]
        if entity.shape != 'ARC':
            return
        entity_nodes = self.get_nodes_attached_to_entity(entity_index)
        if len(entity_nodes) < 3:
            return
        d = entity.start.get_distance_to_point(entity.end)
        n = len(entity_nodes) - 1
        extension = 2 * (d / n)
        choice = ExtendArcDialog(self.window_main, extension).show()
        if choice is not None:
            extend_left_edge = choice.get('extend_left_edge')
            extend_right_edge = choice.get('extend_right_edge')
            length = entity.radius + choice.get('length')
        else:
            return
        left_node = entity.nodes_list[0]
        right_node = entity.nodes_list[1]
        if self.get_node_p(right_node).is_equal(entity.left_bottom):
            left_node, right_node = right_node, left_node
        if not extend_left_edge:
            entity_nodes.remove(left_node)
        if not extend_right_edge:
            entity_nodes.remove(right_node)
        if len(entity_nodes) < 2:
            return
        self.remove_selected_part_mark()
        self.keep_state()
        angle_list = []
        for node in entity_nodes:
            point = self.get_node_p(node)
            angle = entity.center.get_alfa_to(point)
            if round(angle, gv.accuracy) < round(entity.arc_start_angle, gv.accuracy):
                angle += 360
            angle_list.append((angle, node))
        angle_list.sort(key=itemgetter(0))
        extended_nodes = []
        for item in angle_list:
            angle = item[0]
            node = item[1]
            alfa = angle * math.pi / 180
            x = entity.center.x + length * math.cos(alfa)
            y = entity.center.y + length * math.sin(alfa)
            new_node = Node(Point(x, y))
            extended_nodes.append(self.add_node_to_node_list(new_node))
            self.show_node(get_index_from_hash(self.nodes_hash, extended_nodes[-1]))
            self.add_line_to_net_list_by_nodes(node, extended_nodes[-1])
        for i in range(len(extended_nodes) - 1):
            self.add_line_to_net_list_by_nodes(extended_nodes[i], extended_nodes[i + 1])

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
            entity_index = self.selected_part.index
            entity = self.entity_list[entity_index]
            entity_net_lines = self.get_lines_attached_to_entity(self.selected_part.index)
            if len(entity_net_lines) < 2:
                return False
            entity_start_node = entity.nodes_list[0]
            entity_end_node = entity.nodes_list[-1]
            entity.nodes_list = self.get_nodes_attached_to_lines(entity_net_lines)
            self.remove_parts_from_list(entity_net_lines, gv.part_list_net_lines)
            self.add_line_to_net_list_by_nodes(entity_start_node, entity_end_node, entity_index)
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
        # get intermediate nodes
        n_list = []
        for i in range(len(p_list)-1):
            line = self.net_line_list[p_list[i]]
            n_list.append(line.end_node)
        self.remove_parts_from_list(p_list, gv.part_list_net_lines)
        self.clear_lonely_nodes(n_list)
        self.add_line_to_net_list_by_nodes(start_node, end_node, entity)
        self.show_net_line(-1)
        return True

    def split_part(self, s_part=None, split_mode=gv.split_mode_evenly_n_parts, split_additional_arg=gv.default_split_parts):
        if s_part is None:
            return
        part = s_part.index
        if s_part.part_type == gv.part_type_entity and self.work_mode == gv.work_mode_dxf:
            changed = self.split_entity(part, split_mode, split_additional_arg)
        elif s_part.part_type == gv.part_type_entity and self.work_mode == gv.work_mode_inp:
            start = None
            if self.entity_list[s_part.index].shape == 'CIRCLE':
                start = split_mode
                split_mode = gv.split_mode_by_angle
            changed = self.split_net_line_by_entity(part, split_mode, split_additional_arg, start)
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
        if s_part.part_type == gv.part_type_entity and self.entity_list[self.selected_part.index].shape == 'CIRCLE':
            longitude = self.get_longitude()
            if split_mode is None:
                choice = SplitCircleDialog(self.window_main).show()
                if choice is not None:
                    split_mode = choice.get('split_mode')
                    angle = choice.get('angle')
                    parts = choice.get('parts')
                    if split_mode == gv.split_mode_by_longitude:
                        angle = longitude + angle
                else:
                    return
            # default split circle
            else:
                angle = longitude
                parts = 4
            split_mode = angle
            split_arg = parts
        else:
            if split_mode is None:
                choice = SplitDialog(self.window_main).show()
                if choice is not None:
                    split_mode = choice.get('split_mode')
                    split_arg = choice.get('arg')
                else:
                    return
            elif split_mode == gv.split_mode_2_parts_by_point:
                split_arg = self.new_line_edge[0]
                self.remove_temp_line()
        self.keep_state()
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
        n = 0
        e = self.entity_list[part]
        new_part_list = []
        if e.shape == 'ARC':
            if split_mode == gv.split_mode_2_parts_by_point:
                n = 2
                p = split_additional_arg
                mid_angle = e.center.get_alfa_to(p)
                arc = Entity(shape=e.shape, center=e.center, radius=e.radius, start_angle=e.arc_start_angle, end_angle=mid_angle)
                new_part_list.append(arc)
                arc = Entity(shape=e.shape, center=e.center, radius=e.radius, start_angle=mid_angle, end_angle=e.arc_end_angle)
                new_part_list.append(arc)
            else:
                new_points = get_split_arc_points(e, split_mode, split_additional_arg)
                n = len(new_points) - 1
                start_angle = e.arc_start_angle
                for i in range(n):
                    p = new_points[i+1]
                    end_angle = e.center.get_alfa_to(p)
                    arc = Entity(shape=e.shape, center=e.center, radius=e.radius, start_angle=start_angle, end_angle=end_angle)
                    new_part_list.append(arc)
                    start_angle = end_angle
        elif e.shape == 'LINE':
            if split_mode == gv.split_mode_2_parts_by_point:
                n = 2
                mid_point = split_additional_arg
                line = Entity(shape='LINE', start=e.start, end=mid_point)
                new_part_list.append(line)
                line = Entity(shape='LINE', start=mid_point, end=e.end)
                new_part_list.append(line)
            else:
                new_points = get_split_line_points(e.start, e.end, split_mode, split_additional_arg)
                n = len(new_points) - 1
                start = e.start
                for i in range(n):
                    end = new_points[i+1]
                    line = Entity(shape='LINE', start=start, end=end)
                    new_part_list.append(line)
                    start = end
        elif e.shape == 'CIRCLE':
            self.split_circle(part, split_mode, split_additional_arg)
            return True
        for i in range(n):
            self.entity_list.append(new_part_list[i])
            self.define_new_entity_color(-1)
            self.show_entity(-1)
        self.remove_parts_from_list([part], gv.part_list_entities)
        if split_mode == gv.split_mode_2_parts_by_point:
            self.mouse_select_mode = gv.mouse_select_mode_edge
        return True

    def split_all_circles(self, n=gv.default_split_circle_parts):
        longitude = self.get_longitude()
        i = len(self.entity_list) - 1
        while i >= 0:
            e = self.entity_list[i]
            if e.shape == 'CIRCLE':
                self.split_circle(i, longitude, n)
            i -= 1

    def split_circle(self, part, start_angle, n=gv.default_split_circle_parts):
        if len(self.entity_list) < (part + 1):
            return 
        e = self.entity_list[part]
        if e.shape != 'CIRCLE' or self.work_mode != gv.work_mode_dxf:
            return
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

    def split_net_line_by_entity(self, part, split_mode=gv.split_mode_evenly_n_parts, split_additional_arg=gv.default_split_parts,
                                 start=None):
        if self.work_mode != gv.work_mode_inp:
            return False
        old_lines = self.get_lines_attached_to_entity(part)
        self.remove_parts_from_list(old_lines, gv.part_list_net_lines)
        entity = self.entity_list[part]
        self.set_entity_edge_nodes(part)
        if entity.shape == 'LINE':
            start_hash_node = entity.nodes_list[0]
            end_hash_node = entity.nodes_list[-1]
            p1 = self.get_node_p(start_hash_node)
            p2 = self.get_node_p(end_hash_node)
            new_points = get_split_line_points(p1, p2, split_mode, split_additional_arg)
        elif entity.shape == 'ARC':
            start_hash_node = entity.nodes_list[0]
            arc = self.entity_list[part]
            new_points = get_split_arc_points(arc, split_mode, split_additional_arg)
        # entity.shape == 'CIRCLE'
        else:
            new_points = get_split_circle_points(entity, split_additional_arg, start)
            new_node = Node(new_points[0], entity=part)
            start_hash_node = self.add_node_to_node_list(new_node)
            circle_first_node = start_hash_node
        for j in range(len(new_points) - 1):
            new_node = Node(new_points[j+1], entity=part)
            end_hash_node = self.add_node_to_node_list(new_node)
            self.add_line_to_net_list_by_nodes(start_hash_node, end_hash_node, part)
            start_hash_node = end_hash_node
        if entity.shape == 'CIRCLE':
            self.add_line_to_net_list_by_nodes(start_hash_node, circle_first_node, part)
        return True

    def split_net_line(self, part, split_mode=gv.split_mode_evenly_n_parts, split_additional_arg=gv.default_split_parts):
        if self.work_mode != gv.work_mode_inp:
            return False
        new_lines = []
        line = self.net_line_list[part]
        p1 = self.get_node_p(line.start_node)
        p2 = self.get_node_p(line.end_node)
        shape = 'LINE'
        if line.entity is not None:
            shape = self.entity_list[line.entity].shape
        start_node = line.start_node
        if shape == 'LINE':
            new_points = get_split_line_points(p1, p2, split_mode, split_additional_arg)
        elif shape == 'ARC':
            reference_entity = self.entity_list[line.entity]
            start_angle = reference_entity.center.get_alfa_to(p1)
            end_angle = reference_entity.center.get_alfa_to(p2)
            if reference_entity.arc_end_angle >= 360:
                if round(start_angle, gv.accuracy) < round(reference_entity.arc_start_angle, gv.accuracy):
                    start_angle += 360
                if round(end_angle, gv.accuracy) < round(reference_entity.arc_start_angle, gv.accuracy):
                    end_angle += 360
            diff1 = reference_entity.arc_end_angle - end_angle
            diff2 = reference_entity.arc_end_angle - start_angle
            if diff1 > diff2:
                start_angle, end_angle = end_angle, start_angle
            arc = Entity('ARC', reference_entity.center, reference_entity.radius, start_angle=start_angle, end_angle=end_angle)
            new_points = get_split_arc_points(arc, split_mode, split_additional_arg)
            new_node = Node(new_points[0], entity=line.entity)
            start_node = self.add_node_to_node_list(new_node)
        # shape == 'CIRCLE'
        else:
            circle_lines = self.get_lines_attached_to_entity(line.entity)
            circle_lines.remove(part)
            p = None
            for cl in circle_lines:
                net_line = self.net_line_list[cl]
                if net_line.start_node != line.start_node and net_line.start_node != line.end_node:
                    p = self.get_node_p(net_line.start_node)
                    break
                elif net_line.end_node != line.start_node and net_line.end_node != line.end_node:
                    p = self.get_node_p(net_line.end_node)
                    break
            reference_entity = self.entity_list[line.entity]
            start_angle = reference_entity.center.get_alfa_to(p1)
            end_angle = reference_entity.center.get_alfa_to(p2)
            if p is not None:
                p = get_shifted_point(p, p1, -p1.get_alfa_to(p2))
                if p.y < 0:
                    start_angle, end_angle = end_angle, start_angle
            if end_angle < start_angle:
                end_angle += 360
            arc = Entity('ARC', reference_entity.center, reference_entity.radius, start_angle=start_angle, end_angle=end_angle)
            new_points = get_split_arc_points(arc, split_mode, split_additional_arg)
            new_node = Node(new_points[0], entity=line.entity)
            start_node = self.add_node_to_node_list(new_node)
        for j in range(len(new_points) - 1):
            new_node = Node(new_points[j+1], entity=line.entity)
            end_node = self.add_node_to_node_list(new_node)
            new_lines.append(NetLine(start_node, end_node, line.entity))
            start_node = end_node
        for j in range(len(new_lines)):
            self.add_line_to_net_list_by_line(new_lines[j])
        self.remove_parts_from_list([part], gv.part_list_net_lines)
        return True

    # return all net lines crossed by line from p1 to p2
    # each line is tupled with mutual cross point
    def get_crossed_net_lines(self, p1, p2):
        net_lines_list = []
        start_hash_node = self.get_hash_index_of_node_with_point(p1)
        if start_hash_node is None:
            start_hash_node = 0
        end_hash_node = self.get_hash_index_of_node_with_point(p2)
        if end_hash_node is None:
            end_hash_node = 0
        if p1 is None or p2 is None:
            return net_lines_list
        for i in range(len(self.net_line_list)):
            p, hash_node = self.get_mutual_point_of_net_line_with_crossing_line(i, p1, p2)
            if hash_node is not None:
                if hash_node == start_hash_node or hash_node == end_hash_node:
                    continue
            if p is not None:
                net_lines_list.append((i, hash_node, p))
        return net_lines_list

    # return
    # first parameter: mutual point of self.net_line_list[net_line] with crossing line p1-p2, None if there isn't
    # second parameter: existing node with mutual point, None if there isn't
    def get_mutual_point_of_net_line_with_crossing_line(self, net_line, p1, p2):
        net_line = self.net_line_list[net_line]
        start_node_p = self.get_node_p(net_line.start_node)
        end_node_p = self.get_node_p(net_line.end_node)
        angle = -start_node_p.get_alfa_to(end_node_p)
        line_end = get_shifted_point(end_node_p, start_node_p, angle)
        p1 = get_shifted_point(p1, start_node_p, angle)
        p2 = get_shifted_point(p2, start_node_p, angle)
        if p1.y == p2.y:
            return None, None
        if p1.y * p2.y > 0:
            return None, None
        # x = where line p1-p2 crosses x axe
        x = p2.x - p2.y * (p2.x - p1.x) / (p2.y - p1.y)
        if round(x, gv.accuracy) == 0:
            return start_node_p, net_line.start_node
        elif round(x, gv.accuracy) == round(line_end.x, gv.accuracy):
            return end_node_p, net_line.end_node
        elif round(x, gv.accuracy) < 0 or round(x, gv.accuracy) > line_end.x:
            return None, None
        mutual_point = Point(x, 0)
        mutual_point = get_shifted_point(mutual_point, Point(0, 0), -angle)
        mutual_point.x += start_node_p.x
        mutual_point.y += start_node_p.y
        return mutual_point, None

    def set_initial_border_nodes(self):
        choice = SetInitialNetDialog(self.window_main).show()
        if choice is not None:
            arc_max_angle = choice.get('arc_max_angle')
            line_max_length = choice.get('line_max_length')
            circle_parts = choice.get('circle_parts')
        else:
            return
        self.reset_net()
        self.set_initial_net()
        for i in range(len(self.entity_list)):
            e = self.entity_list[i]
            if e.shape == 'CIRCLE':
                angle = self.get_longitude() + 45
                self.split_net_line_by_entity(i, gv.split_mode_by_angle, circle_parts, angle)
                continue
            n = n_length = 0
            d = e.start.get_distance_to_point(e.end)
            if e.shape == 'ARC':
                angle = e.arc_end_angle - e.arc_start_angle
                n = round(angle/arc_max_angle)
                if d > line_max_length:
                    n_length = round(d / line_max_length)
            elif e.shape == 'LINE':
                if d > line_max_length:
                    n_length = round(d / line_max_length)
            if n_length > n:
                n = n_length
            if n > 1:
                self.split_net_line_by_entity(i, gv.split_mode_evenly_n_parts, n)
        self.update_view()

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

    def get_node_p(self, hash_index):
        node_index = get_index_from_hash(self.nodes_hash, hash_index)
        if node_index is None:
            print(f"in get_node_p can't find node index for hash {hash_index}")
            return Point(0, 0)
        node = self.node_list[node_index]
        return node.p

    def get_nodes_attached_to_lines(self, net_line_list):
        nodes_list = []
        for line_index in net_line_list:
            line = self.net_line_list[line_index]
            nodes_list.append(line.start_node)
            nodes_list.append(line.end_node)
        # remove duplicate parts from list
        nodes_list = list(dict.fromkeys(nodes_list))
        return nodes_list

    def clear_lonely_nodes(self, hash_node_list=None):
        lonely_nodes_list = []
        if hash_node_list is None:
            hash_node_list = []
            for i in range(1, len(self.node_list)):
                node = self.node_list[i]
                hash_node_list.append(node.hash_index)
        for n in hash_node_list:
            # modify attached lines
            self.set_lines_attached_to_node(n)
            node_index = get_index_from_hash(self.nodes_hash, n)
            if node_index is not None:
                if len(self.node_list[node_index].attached_lines) == 0:
                    lonely_nodes_list.append(n)
        self.remove_parts_from_list(lonely_nodes_list, gv.part_list_nodes)

    def remove_parts_from_list(self, part_list, list_name):
        if part_list is None:
            return
        # remove duplicate parts from list
        part_list = list(dict.fromkeys(part_list))
        part_list = sorted(part_list, reverse=True)
        original_list = None
        attached_nodes = []
        if list_name == gv.part_list_nodes:
            for part in part_list:
                self.remove_node_from_node_list(part)
        else:
            if list_name == gv.part_list_entities:
                original_list = self.entity_list
            elif list_name == gv.part_list_net_lines:
                original_list = self.net_line_list
                attached_nodes = self.get_nodes_attached_to_lines(part_list)
            for part in part_list:
                if part is None:
                    return
                self.hide_part(part, list_name)
                original_list.pop(part)
        if len(attached_nodes) > 0:
            self.clear_lonely_nodes(attached_nodes)
        self.remove_selected_part_mark()

    def get_lines_attached_to_entity(self, entity):
        net_lines = []
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            if line.entity == entity:
                net_lines.append(i)
        return net_lines

    # return unsorted list
    def get_nodes_attached_to_entity(self, entity):
        nodes = []
        net_lines = self.get_lines_attached_to_entity(entity)
        for i in net_lines:
            line = self.net_line_list[i]
            nodes.append(line.start_node)
            nodes.append(line.end_node)
        return list(dict.fromkeys(nodes))

    # set all lines attached to node, and sort them by angle_to_second_node
    def set_lines_attached_to_node(self, node_hash_index):
        n = get_index_from_hash(self.nodes_hash, node_hash_index)
        if n is None:
            return
        node = self.node_list[n]
        node.attached_lines = []
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            start_node_index = get_index_from_hash(self.nodes_hash, line.start_node)
            end_node_index = get_index_from_hash(self.nodes_hash, line.end_node)
            start_node = self.node_list[start_node_index]
            end_node = self.node_list[end_node_index]
            if node_hash_index == line.start_node:
                # debug
                if start_node_index == end_node_index:
                    print(
                        f'in set_lines_attached_to_node line {i} start_node_index = end_node_index {start_node_index}')
                    continue
                al = AttachedLine(i, line.end_node, start_node.p.get_alfa_to(end_node.p))
                node.attached_lines.append(al)
            elif node_hash_index == line.end_node:
                # debug
                if start_node_index == end_node_index:
                    print(
                        f'in set_lines_attached_to_node line {i} start_node_index = end_node_index {start_node_index}')
                    continue
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
        if num_lines < 2:
            node.exceptions.append(gv.unattached)
            node.expected_elements = 0
            node.exceptions.append(gv.unattached)
            return
        num_outer_lines = 0
        num_inner_lines = 0
        for al in node.attached_lines:
            if al.border_type == gv.line_border_type_outer:
                num_outer_lines += 1
            elif al.border_type == gv.line_border_type_inner:
                num_inner_lines += 1
        num_border_lines = num_outer_lines + num_inner_lines
        node.expected_elements = len(node.attached_lines) - int(num_border_lines / 2)
        if num_border_lines == 1 or num_border_lines == 3:
            # debug
            m = f'unexpected number of border lines in set_node_expected_elements_and_exceptions node {n}  outer: {num_outer_lines}   inner: {num_inner_lines}'
            print(m)
            return
        prev_line = node.attached_lines[0]
        angle = prev_line.angle_to_second_node
        for i in range(num_lines):
            prev_angle = angle
            line = node.attached_lines[(i+1) % num_lines]
            angle = line.angle_to_second_node
            if not prev_line.is_available:
                prev_line = line
                continue
            if angle < prev_angle:
                angle += 360
            diff_angle = round(angle - prev_angle, gv.accuracy)
            if diff_angle < gv.min_angle_to_create_element:
                prev_line.is_available = False
                node.exceptions.append(gv.too_steep_angle)
            elif diff_angle > gv.max_angle_to_create_element:
                prev_line.is_available = False
                node.exceptions.append(gv.too_wide_angle)
            prev_line = line

    # return the hash key of the nodes with specific exception, or all exceptions (default)
    def get_exception_nodes(self, exception='all'):
        exception_list = []
        for i in range(1, len(self.node_list)):
            if (exception == 'all' and len(self.node_list[i].exceptions) > 0) or exception in self.node_list[i].exceptions:
                exception_list.append(self.node_list[i].hash_index)
        return exception_list

    # return hash index of the node that can make an element counter clockwise (default) or clockwise
    def get_next_relevant_node(self, current_node_hash_index, prev_node_hash_index, prev_angle=None, clockwise=False):
        current_node_index = get_index_from_hash(self.nodes_hash, current_node_hash_index)
        prev_node_index = get_index_from_hash(self.nodes_hash, prev_node_hash_index)
        attached_line_list = self.node_list[current_node_index].attached_lines
        if len(attached_line_list) == 0:
            return None, None
        current_node = self.node_list[current_node_index]
        prev_node = self.node_list[prev_node_index]
        if prev_angle is None:
            prev_angle = prev_node.p.get_alfa_to(current_node.p)
        next_node_hash_index = None
        net_line = None
        min_angle_to_create_elelment = gv.angle_diff_accuracy
        max_angle_to_create_elelment = 360 - gv.angle_diff_accuracy
        best_angle = max_angle_to_create_elelment
        if clockwise:
            min_angle_to_create_elelment, max_angle_to_create_elelment = (360 - max_angle_to_create_elelment), (360 - min_angle_to_create_elelment)
            best_angle = min_angle_to_create_elelment
        for l in attached_line_list:
            node_hash_index = l.second_node
            if node_hash_index == prev_node_hash_index:
                continue
            node_index = get_index_from_hash(self.nodes_hash, node_hash_index)
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
                next_node_hash_index = node_hash_index
                net_line = l
        return next_node_hash_index, net_line

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
        self.show_text_on_screen('checking for duplicated entities')
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
        self.frame_1.update_idletasks()
        return duplicate_entities_list

    def set_all_nodes_attached_line_list(self):
        c = len(self.node_list)
        if c < 2:
            return
        self.show_text_on_screen('matching lines to nodes')
        self.show_progress_bar(c)
        for i in range(1, len(self.node_list)):
            node_hash_index = self.node_list[i].hash_index
            self.set_lines_attached_to_node(node_hash_index)
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()
        self.frame_1.update_idletasks()

    def get_lines_attached_to_node(self, node_hash_index):
        node_index = get_index_from_hash(self.nodes_hash, node_hash_index)
        node = self.node_list[node_index]
        self.set_lines_attached_to_node(node_hash_index)
        return node.attached_lines

    # return list of border nodes, [] if can't find
    def set_border_lines(self, set_attached_lines=True):
        if set_attached_lines:
            self.set_all_nodes_attached_line_list()
        # reset all net lines
        for line in self.net_line_list:
            line.border_type = gv.line_border_type_none
        n_hash = self.get_bottom_left_node()
        n_index = get_index_from_hash(self.nodes_hash, n_hash)
        outer_border_nodes = [n_index]
        alfa = 0
        line = AttachedLine()
        line.second_node = n_hash
        next_node_hash_index = 0
        while next_node_hash_index != n_hash and len(outer_border_nodes) <= len(self.net_line_list):
            next_node_hash_index, line = self.get_next_relevant_node(line.second_node, 0, prev_angle=alfa,
                                                                clockwise=True)
            if line is None:
                m = "can't set outer lines"
                messagebox.showwarning("Warning", m)
                return []
            line.border_type = gv.line_border_type_outer
            self.net_line_list[line.line_index].border_type = gv.line_border_type_outer
            alfa = line.angle_to_second_node
            next_node_index = get_index_from_hash(self.nodes_hash, next_node_hash_index)
            outer_border_nodes.append(next_node_index)
        # mark relevant attached lines as unavailale
        for node_index in outer_border_nodes:
            node = self.node_list[node_index]
            for al in node.attached_lines:
                net_line = self.net_line_list[al.line_index]
                if net_line.border_type == gv.line_border_type_outer and al.border_type != gv.line_border_type_outer:
                    al.is_available = False
                    al.border_type = gv.line_border_type_outer
        # debug
        #print(f'outer line: {outer_border_nodes}')
        inner_border_nodes = []
        for i in range(len(self.net_line_list)):
            net_line = self.net_line_list[i]
            if net_line.entity is not None and net_line.border_type != gv.line_border_type_outer:
                net_line.border_type = gv.line_border_type_inner
                if get_index_from_hash(self.nodes_hash, net_line.start_node) not in outer_border_nodes:
                    inner_border_nodes.append(net_line.start_node)
                if get_index_from_hash(self.nodes_hash, net_line.end_node) not in outer_border_nodes:
                    inner_border_nodes.append(net_line.end_node)
        if len(inner_border_nodes) == 0:
            return outer_border_nodes + inner_border_nodes
        # remove duplicate nodes
        inner_border_nodes = list(dict.fromkeys(inner_border_nodes))
        # debug
        #print(f'inner nodes (hash): {inner_border_nodes}')
        while len(inner_border_nodes) > 0:
            if len(inner_border_nodes) < 3:
                m = f'There are open inner entities. remove or fix before INP mode'
                messagebox.showwarning("Warning", m)
                print(m)
                return []
            inner_border_nodes = self.set_inner_attached_lines(inner_border_nodes)

    def set_inner_attached_lines(self, inner_border_nodes):
        if len(inner_border_nodes) == 0:
            return inner_border_nodes
        # find lowest node
        lowest_index = 0
        lowest_hash = inner_border_nodes[lowest_index]
        lowest_node_index = get_index_from_hash(self.nodes_hash, lowest_hash)
        lowest_p = self.node_list[lowest_node_index].p
        for i in range(len(inner_border_nodes)):
            p = self.get_node_p(inner_border_nodes[i])
            if p.is_smaller_x_smaller_y(lowest_p, by_x=False):
                lowest_p = p
                lowest_index = i
                lowest_hash = inner_border_nodes[lowest_index]
                lowest_node_index = get_index_from_hash(self.nodes_hash, lowest_hash)
        # set lowest nodes attached line
        lowest_node = self.node_list[lowest_node_index]
        inner_attached_line = -1
        lowest_angle = 359
        next_inner_node = 0
        for i in range(len(lowest_node.attached_lines)):
            al = lowest_node.attached_lines[i]
            if self.net_line_list[al.line_index].border_type != gv.line_border_type_inner:
                continue
            if al.angle_to_second_node < lowest_angle:
                inner_attached_line = i
                lowest_angle = al.angle_to_second_node
                next_inner_node = al.second_node
        if inner_attached_line < 0:
            print(f"can't find inner line in lowest inner node")
            return None
        lowest_node.attached_lines[inner_attached_line].border_type = gv.line_border_type_inner
        lowest_node.attached_lines[inner_attached_line].is_available = False
        inner_border_nodes.pop(lowest_index)
        removed_nodes = [lowest_hash]
        while next_inner_node is not None and len(inner_border_nodes) > 0:
            node_index = get_index_from_hash(self.nodes_hash, next_inner_node)
            node = self.node_list[node_index]
            inner_border_nodes.remove(next_inner_node)
            removed_nodes.append(next_inner_node)
            next_inner_node = None
            for i in range(len(node.attached_lines)):
                al = node.attached_lines[i]
                if al.second_node in inner_border_nodes:
                    net_line = self.net_line_list[al.line_index]
                    if net_line.border_type != gv.line_border_type_inner:
                        continue
                    al.is_available = False
                    al.border_type = gv.line_border_type_inner
                    next_inner_node = al.second_node
                    break
        # validity check
        if len(removed_nodes) > 0:
            node_index = get_index_from_hash(self.nodes_hash, removed_nodes[-1])
            node = self.node_list[node_index]
            is_valid = False
            for al in node.attached_lines:
                if al.second_node == removed_nodes[0]:
                    is_valid = True
                    al.is_available = False
                    al.border_type = gv.line_border_type_inner
                    break
            if not is_valid:
                print("can't close inner line loop. check DXF")
        # mark relevant attached lines as unavailale
        for node_hash in removed_nodes:
            node_index = get_index_from_hash(self.nodes_hash, node_hash)
            node = self.node_list[node_index]
            for al in node.attached_lines:
                net_line = self.net_line_list[al.line_index]
                if net_line.border_type == gv.line_border_type_inner and al.border_type != gv.line_border_type_inner:
                    al.border_type = gv.line_border_type_inner
        return inner_border_nodes

    # return list of unattached nodes with real index in list (not hash_index)
    def get_unattached_nodes(self):
        tmp_list = []
        self.set_all_nodes_attached_line_list()
        c = len(self.node_list)
        self.show_text_on_screen('checking unattached nodes')
        self.show_progress_bar(c)
        for i in range(1, c):
            node = self.node_list[i]
            if len(node.attached_lines) < 2:
                self.node_list[i].color = gv.invalid_node_color
                tmp_list.append(i)
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()
        self.frame_1.update_idletasks()
        if len(tmp_list) > 0:
            m = f"{len(tmp_list)} unattached nodes: {tmp_list}"
            print(m)
            messagebox.showwarning("Warning", m)
        return tmp_list

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
        # make sure that corner will not remain on invalid node
        for corner in self.corner_list:
            if corner.hash_node == hash_index:
                self.clear_corner_list()
                break
        # update hash
        for i in range(node_list_index+1, len(self.node_list)):
            node_hash_index = self.node_list[i].hash_index
            self.nodes_hash[str(node_hash_index)] = i-1
        self.nodes_hash.pop(str(hash_index))
        self.hide_node(node_list_index)
        self.node_list.pop(node_list_index)

    # return index of node in node_list with same p, None if can't find
    def get_hash_index_of_node_with_point(self, p):
        for i in range(len(self.node_list)):
            node = self.node_list[i]
            if node.p.is_equal(p):
                return node.hash_index
        return None

    # set net with nodes only on entity edges
    def set_initial_net(self):
        self.reset_net()
        c = len(self.entity_list)
        self.show_text_on_screen('setting initial net')
        self.show_progress_bar(c)
        for i in range(c):
            e = self.entity_list[i]
            if e.shape == 'CIRCLE':
                continue
            self.set_entity_edge_nodes(i)
            # debug
            if len(e.nodes_list) < 2:
                print(f'in set_entity_edge_nodes: entity {i}  shape {e.shape}  len e.nodes_list: {len(e.nodes_list)}')
            start_node = e.nodes_list[0]
            end_node = e.nodes_list[1]
            line_entity = i
            self.net_line_list.append(NetLine(start_node, end_node, line_entity))
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()
        self.frame_1.update_idletasks()
        # debug
        #self.print_node_list()
        #self.print_line_list()

    # debug
    def print_node_list(self):
        print('nodes:')
        for i in range(1, len(self.node_list)):
            n = self.node_list[i]
            print(f'{i}: {n.p.convert_into_tuple()}')

    # debug
    def print_line_list(self):
        print('\nlines:')
        print(self.nodes_hash)
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            start_node = get_index_from_hash(self.nodes_hash, line.start_node)
            end_node = get_index_from_hash(self.nodes_hash, line.end_node)
            print(f'{i}: start node: {start_node}  end node: {end_node}        start_hash: {line.start_node}   end_hash: {line.end_node}   entity: {line.entity}')

    # debug
    def print_elements(self, element_list):
        for i in range(len(element_list)):
            e = element_list[i]
            print(f'{i+1}: {e.nodes}')

    # debug
    def print_nodes_exceptions(self, node_list):
        for hash_index in node_list:
            n = get_index_from_hash(self.nodes_hash, hash_index)
            print(f'{n}: {self.node_list[n].exceptions}')

    # debug
    def print_nodes_expected_elements(self):
        print('Expected elements for each node:')
        for i in range(1, len(self.node_list)):
            print(f'{i}: {self.node_list[i].expected_elements}')

    # the terms left-right-top-bottom assume that self.corner_list[0] is the bottom left corner and 2-4 order clockwise
    # net will start with horizontal lines (1-4) and then split them with vertical lines
    def set_net_between_corners(self, mode=gv.corners_set_net_both):
        if len(self.corner_list) < 4:
            return False
        hash_node = []
        corner_p = []
        for i in range(len(self.corner_list)):
            hash_node.append(self.corner_list[i].hash_node)
            corner_p.append(self.get_node_p(hash_node[-1]))
        border_nodes = self.set_border_lines()
        if len(border_nodes) == 0:
            return False
        middle_nodes_1_2, found_track_1_2 = self.get_middle_nodes_between_node1_and_node_2(hash_node[0], hash_node[1], [hash_node[0], hash_node[2], hash_node[3]])
        middle_nodes_2_3, found_track_2_3 = self.get_middle_nodes_between_node1_and_node_2(hash_node[1], hash_node[2], [hash_node[0], hash_node[1], hash_node[3]])
        middle_nodes_4_3, found_track_4_3 = self.get_middle_nodes_between_node1_and_node_2(hash_node[3], hash_node[2], [hash_node[0], hash_node[1], hash_node[3]])
        middle_nodes_1_4, found_track_1_4 = self.get_middle_nodes_between_node1_and_node_2(hash_node[0], hash_node[3], [hash_node[0], hash_node[1], hash_node[2]])
        msg = ""
        if not found_track_1_2:
            msg += ' 1-2 '
        if not found_track_2_3:
            msg += ' 2-3 '
        if not found_track_4_3:
            msg += ' 3-4 '
        if not found_track_1_4:
            msg += ' 1-4 '
        if msg != "":
            msg = "couldn't find middle nodes between" + msg
            print(msg)
        if mode != gv.corners_set_net_1_2 and len(middle_nodes_1_2) != len(middle_nodes_4_3):
            print(f'mismatch number of nodes between 1-2 ({len(middle_nodes_1_2)}) and 4-3 ({len(middle_nodes_4_3)})')
            return False
        if mode != gv.corners_set_net_1_4 and len(middle_nodes_2_3) != len(middle_nodes_1_4):
            print(f'mismatch number of nodes between 1-4 ({len(middle_nodes_1_4)}) and 2-3 ({len(middle_nodes_2_3)})')
            return False
        if mode == gv.corners_set_net_1_4 or mode == gv.corners_set_net_both:
            self.add_lines_between_2_node_list(middle_nodes_1_2, middle_nodes_4_3, corner_p[0], corner_p[1], middle_nodes_1_4, middle_nodes_2_3)
        if mode == gv.corners_set_net_1_2 or mode == gv.corners_set_net_both:
            self.add_lines_between_2_node_list(middle_nodes_1_4, middle_nodes_2_3, corner_p[0], corner_p[3], middle_nodes_1_2, middle_nodes_4_3)
        return True

    # return indexes of lines with one node in one list and the second node in the other list
    def get_lines_between_2_node_lists(self, node_list_1, node_list_2):
        line_list = []
        for node1 in node_list_1:
            attached_lines = self.get_lines_attached_to_node(node1)
            for al in attached_lines:
                if al.second_node in node_list_2:
                    line_list.append(al.line_index)
        return line_list

    # reference_point is to make sure that middle lines will be split in the correct order
    # (left - right or right - left) according to distance from reference_point
    def add_lines_between_2_node_list(self, bottom_node_list, top_node_list, reference_point, other_edge_point, left_node_list, right_node_list):
        if bottom_node_list is None or top_node_list is None:
            return
        if len(bottom_node_list) != len(top_node_list):
            return
        middle_lines = self.get_lines_between_2_node_lists(left_node_list, right_node_list)
        vertical_nodes = []
        horizontal_nodes = []
        for line_index in middle_lines:
            line = self.net_line_list[line_index]
            if line.start_node in left_node_list:
                horizontal_nodes.append([line.start_node, line.end_node])
            else:
                horizontal_nodes.append([line.end_node, line.start_node])
        if len(middle_lines) == 0:
            middle_lines = None
        n = len(bottom_node_list) + 1
        for i in range(len(bottom_node_list)):
            start_hash = bottom_node_list[i]
            end_hash = top_node_list[i]
            p1 = self.get_node_p(start_hash)
            p2 = self.get_node_p(end_hash)
            if middle_lines is None:
                percentage = 100 / (n - i)
            else:
                percentage = (i + 1) * 100 / n
            line_points = self.add_line(p1, p2, percentage, reference_point, other_edge_point, middle_lines)
            line_nodes = []
            for point in line_points:
                node = Node(point)
                node_hash_index = self.add_node_to_node_list(node)
                line_nodes.append(node_hash_index)
            vertical_nodes.append(line_nodes.copy())
            line_nodes = line_nodes[1:-1]
            for j in range(len(horizontal_nodes)):
                node_list = horizontal_nodes[j]
                node_list.insert(i+1, line_nodes[j])
        for line_nodes in vertical_nodes:
            self.add_list_of_lines_by_nodes(line_nodes)
        for line_nodes in horizontal_nodes:
            self.add_list_of_lines_by_nodes(line_nodes)
        self.remove_parts_from_list(middle_lines, gv.part_list_net_lines)

    def set_net(self):
        self.keep_state()
        self.create_net_element_list()
        self.show_elements = True
        self.show_net = True
        self.update_view()

    # element list with index of node_list (not hash)
    def create_net_element_list(self):
        self.hide_all_elements()
        element_list = []
        exception_element_list = []
        counter_r3_elements = 0
        counter_r4_elements = 0
        unattaced_list = self.get_unattached_nodes()
        if len(unattaced_list) > 0:
            self.hide_all_elements()
            self.element_list = []
            return
        border_nodes = self.set_border_lines(False)
        if len(border_nodes) == 0:
            self.hide_all_elements()
            self.element_list = []
            return
        self.set_all_nodes_expected_elements_and_exceptions()
        c = len(self.node_list)
        self.show_text_on_screen('creating net elements')
        self.show_progress_bar(c)
        # debug
        #self.print_node_list()
        #self.print_line_list()
        #self.print_nodes_expected_elements()
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
                next_node_index = -1
                while node_hash_index is not None:
                    node_index = get_index_from_hash(self.nodes_hash, node_hash_index)
                    new_element_nodes.append(node_index)
                    next_node_hash_index, line = self.get_next_relevant_node(node_hash_index, prev_node_hash_index)
                    next_node_index = get_index_from_hash(self.nodes_hash, next_node_hash_index)
                    if line is not None:
                        if not line.is_available:
                            next_node_index = -1
                            break
                        line.is_available = False
                    if next_node_index is None:
                        break
                    if next_node_index == fist_node:
                        break
                    prev_node_hash_index = node_hash_index
                    node_hash_index = next_node_hash_index
                if next_node_index is not None and next_node_index == fist_node and len(new_element_nodes) > 2:
                    element = Element()
                    element.nodes = new_element_nodes
                    if len(new_element_nodes) <= gv.max_nodes_to_create_element:
                        element_list.append(element)
                        if len(new_element_nodes) == 4:
                            counter_r4_elements += 1
                        elif len(new_element_nodes) == 3:
                            counter_r3_elements += 1
                        for element_node in new_element_nodes:
                            self.node_list[element_node].expected_elements -= 1
                    else:
                        exception_element_list.append(element)
                    #node.attached_lines[j].is_available = False
            if node.expected_elements > 0:
                pass
                # optional
                # node.exceptions.append(gv.expected_elements_not_complete)
            for al in node.attached_lines:
                al.is_available = False
            #self.node_list[i].attached_lines = []
            self.progress_bar['value'] += 1
            self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()
        self.frame_1.update_idletasks()
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
            print(f'\nSUCCESS')
        if counter_r4_elements > 0:
            m = f'net created with {counter_r4_elements} R4 elements'
        if counter_r3_elements > 0:
            m += f' and {counter_r3_elements} R3 elements'
        m += f'   {len(self.node_list)-1} nodes\n'
        print(m)
        # debug
        #self.print_nodes_expected_elements()
        #self.print_elements(self.element_list)

    def zoom_modified(self, factor):
        self.remove_temp_line()
        self.remove_selected_part_mark()
        self.zoom(factor)
        self.update_view()

    def control_mouse_wheel(self, key):
        if key.delta < 0:
            factor = 5/4
        else:
            factor = 4/5
        self.zoom_modified(factor)

    def save_as(self):
        file_name = self.window_main.title()
        dot_index = file_name.find('.')
        if dot_index is not None:
            file_name = file_name[:dot_index]
        menu = tk.Menu(self.board, tearoff=0)
        menu.add_command(label="DATA", command=lambda: self.save_data(file_name))
        menu.add_command(label="INP", command=lambda: self.save_inp(file_name))
        menu.add_command(label="DXF", command=lambda: save_dxf(self.window_main, file_name, self.entity_list))
        menu.add_separator()
        menu.add_command(label="Quit")
        x = self.frame_2.winfo_pointerx()
        y = self.frame_2.winfo_pointery()
        menu.post(x, y)

    def save_inp(self, file_name='Fabian'):
        if len(self.element_list) < 1:
            self.create_net_element_list()
            self.show_elements = True
        self.update_view()
        save_inp(self.window_main, file_name, self.node_list, self.element_list)

    def save_data(self, file_name='Fabian'):
        self.keep_state()
        state = self.state[-1]
        self.state.pop(-1)
        x, y = self.get_screen_position()
        save_data(self.window_main, file_name, state)

    def load(self):
        filetype, arg = load(self.window_main)
        if filetype is None:
            return
        if filetype == 'inp':
            node_list = arg[0]
            element_list = arg[1]
            if len(element_list) > 0:
                self.keep_state()
                self.add_inp_net(node_list, element_list)
            return
        self.reset_board()
        if filetype == 'dxf':
            self.entity_list = arg
            d_list = self.get_duplicated_entities()
            self.hide_text_on_screen()
            if len(d_list) > 0:
                m = f'Removed {len(d_list)} duplicated entities'
                print(m)
                messagebox.showwarning("Warning", m)
                for e in d_list:
                    self.entity_list.remove(e)
            else:
                pass
                # optional
                # print('no duplicated entities')
            # enable the change work mode to operate
            self.work_mode = gv.work_mode_inp
            self.change_work_mode(gv.work_mode_dxf)
            self.center_view(set_scale=True)
            self.update_view()
            self.state = []
        elif filetype == 'json':
            state = arg
            self.state.append(state)
            self.resume_state()
            self.window_main.update()
            self.center_view()
            self.set_accuracy()
            self.update_view()
        # debug
        #self.print_node_list()
        #self.print_line_list()

    def match_inp_net(self):
        if self.work_mode != gv.work_mode_dxf or len(self.inp_nets) < 1:
            return
        border_nodes = self.set_border_lines()
        if len(border_nodes) < 1:
            return
        entity_edge_points = []
        corner_nodes = []
        if len(self.corner_list) > 0:
            for corner in self.corner_list:
                corner_nodes.append(corner.hash_node)
            for entity in self.entity_list:
                if entity.start is not None:
                    entity_edge_points.append(entity.start)
                if entity.end is not None:
                    entity_edge_points.append(entity.end)
        self.keep_state()
        for hash_node in border_nodes:
            node_index = get_index_from_hash(self.nodes_hash, hash_node)
            node = self.node_list[node_index]
            # adjust corner to closest node
            if hash_node in corner_nodes:
                min_d = gv.infinite_size
                closest_point = entity_edge_points[0]
                node_p = self.get_node_p(hash_node)
                for p in entity_edge_points:
                    d = node_p.get_distance_to_point(p)
                    if d < min_d:
                        min_d = d
                        closest_point = p
                node.p = closest_point
            # adjust node to closest point on entity
            else:
                index, d = self.find_nearest_entity(node.p)
                d, p = self.get_distance_from_entity_and_nearest_point(node.p, index)
                node.p = p
        self.clear_corner_list()
        self.update_view()

    def merge_inp_nets(self):
        if len(self.inp_nets) < 2:
            return
        self.keep_state()
        merged_node_list = []
        merged_elements = []
        counter = 0
        for inp_net in self.inp_nets:
            for node in inp_net.node_list:
                merged_node_list.append(node)
            for element in inp_net.elements:
                new_element = get_shifted_element(element, counter)
                merged_elements.append(new_element)
            counter += len(inp_net.node_list)
        self.hide_all_inp_nets(False)
        self.inp_nets = []
        self.add_inp_net(merged_node_list, merged_elements)

    def add_inp_net(self, node_list, element_list):
        new_inp = InpNet()
        is_empty_board = len(self.entity_list) == 0
        if is_empty_board:
            self.change_work_mode(gv.work_mode_inp)
        if self.work_mode == gv.work_mode_dxf or is_empty_board:
            self.show_net = False
            self.show_inps = False
            self.show_elements = False
            self.reset_net(keep_state=False)
            c = len(node_list)
            self.show_text_on_screen('adding nodes')
            self.show_progress_bar(c)
            node_hash_index_list = {"0": 0}
            for i in range(len(node_list)):
                node = node_list[i]
                node_hash_index = self.add_node_to_node_list(node)
                node_hash_index_list[str(i + 1)] = node_hash_index
                self.progress_bar['value'] += 1
                self.frame_1.update_idletasks()
            self.hide_text_on_screen()
            self.hide_progress_bar()
            self.frame_1.update_idletasks()
            c = len(element_list)
            self.show_text_on_screen('adding lines and elements')
            self.show_progress_bar(c)
            for element in element_list:
                element_nodes = element.nodes
                n = len(element_nodes)
                element_nodes[0] = node_hash_index_list.get(str(element_nodes[0]))
                for i in range(1, n):
                    element_nodes[i] = node_hash_index_list.get(str(element_nodes[i]))
                    self.add_line_to_net_list_by_nodes(element_nodes[i - 1], element_nodes[i], show_new_line=False)
                self.add_line_to_net_list_by_nodes(element_nodes[-1], element_nodes[0], show_new_line=False)
                self.progress_bar['value'] += 1
                self.frame_1.update_idletasks()
            self.hide_text_on_screen()
            self.hide_progress_bar()
            self.frame_1.update_idletasks()
        self.clear_corner_list()
        if is_empty_board:
            self.center_view(by_nodes=True, set_scale=True)
        if self.work_mode == gv.work_mode_dxf:
            self.element_list = element_list
            node_list = self.node_list[1:]
            self.set_inp_net(new_inp, node_list, element_list)
            self.inp_nets.append(new_inp)
            self.show_elements = True
            self.show_inps = True
        # inp mode
        else:
            if is_empty_board:
                self.clear_lonely_nodes()
                self.change_select_parts_mode(gv.part_type_net_line)
            else:
                self.set_inp_net(new_inp, node_list, element_list)
                self.inp_nets.append(new_inp)
                self.show_inp(-1)
                self.show_inps = True
        self.show_net = True
        self.update_view()

    def set_inp_net(self, inp_net, node_list, element_list):
        inp_net.set_nodes_and_elements(node_list.copy(), element_list.copy())
        c = inp_net.get_total_nodes()
        self.show_text_on_screen('setting inp net')
        self.show_progress_bar(c)
        for element in inp_net.elements:
            element_nodes = element.nodes
            n = len(element_nodes)
            for i in range(n):
                line = NetLine(element_nodes[i]-1, element_nodes[(i + 1) % n]-1, color=gv.inp_line_color)
                if not is_line_in_net_line_list(line, inp_net.lines):
                    inp_net.lines.append(line)
                self.progress_bar['value'] += 1
                self.frame_1.update_idletasks()
        self.hide_text_on_screen()
        self.hide_progress_bar()
        self.frame_1.update_idletasks()

    def set_scale(self, left, right):
        object_width = right - left
        window_width = self.window_main.winfo_width()
        self.scale = window_width/(object_width*2)

    def center_view(self, by_nodes=False, set_scale=False):
        self.hide_text_on_screen()
        x, y = self.get_center(by_nodes=by_nodes, set_scale=set_scale)
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

    def mark_selected_part(self, key=None):
        if self.selected_part is None:
            return
        i = self.selected_part.index
        if self.selected_part.part_type == gv.part_type_entity:
            e = self.entity_list[i]
            if not e.is_marked:
                self.keep_state()
            e.is_marked = True
            self.set_entity_color(i, gv.marked_entity_color)
        elif self.selected_part.part_type == gv.part_type_net_line:
            n = self.net_line_list[i]
            if not n.is_marked:
                self.keep_state()
            n.is_marked = True
            self.set_net_line_color(i, gv.marked_net_line_color)

    def unmark_selected_part(self, key=None):
        if self.selected_part is None:
            return
        i = self.selected_part.index
        if self.selected_part.part_type == gv.part_type_entity:
            e = self.entity_list[i]
            if e.is_marked:
                self.keep_state()
            e.is_marked = False
            self.set_entity_color(i, gv.default_entity_color)
        elif self.selected_part.part_type == gv.part_type_net_line:
            n = self.net_line_list[i]
            if n.is_marked:
                self.keep_state()
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
                self.set_entity_color(i, gv.default_entity_color)
            i += 1

    def unmark_all_net_lines(self):
        self.keep_state()
        i = 0
        for n in self.net_line_list:
            if n.is_marked:
                n.is_marked = False
                self.set_net_line_color(i, gv.net_line_color)
            i += 1

    def remove_marked_net_lines_from_list(self):
        temp_list = []
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            if line.is_marked:
                temp_list.append(i)
        if len(temp_list) > 0:
            self.keep_state()
            self.remove_parts_from_list(temp_list, gv.part_list_net_lines)
            self.update_view()

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
        self.remove_temp_line()
        self.remove_selected_part_mark()
        self.board.delete('all')
        self.show_all_entities()

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
            e.color = gv.default_entity_color
        self.entity_list = temp_list
        self.remove_temp_line()
        self.remove_selected_part_mark()
        self.board.delete('all')
        self.show_all_entities()

    def remove_selected_part_from_list(self, key=None):
        if self.selected_part is None:
            self.remove_temp_line()
            return
        self.keep_state()
        changed = False
        if self.selected_part.part_type == gv.part_type_entity and self.work_mode == gv.work_mode_dxf:
            changed = True
            self.remove_parts_from_list([self.selected_part.index], gv.part_list_entities)
        elif self.selected_part.part_type == gv.part_type_net_line:
            changed = True
            self.remove_parts_from_list([self.selected_part.index], gv.part_list_net_lines)
        if changed:
            self.remove_selected_part_mark()
        else:
            self.state.pop(-1)

    def remove_temp_line(self, key=None):
        if self.new_line_edge_mark[1] is not None:
            self.board.delete(self.new_line_edge_mark[1])
        self.new_line_edge[1] = None
        self.new_line_original_part[1] = None
        if self.new_line_mark is not None:
            self.board.delete(self.new_line_mark)
        if self.new_line_edge_mark[0] is not None:
            self.board.delete(self.new_line_edge_mark[0])
        self.new_line_edge[0] = None
        self.new_line_original_part[0] = None
        if self.temp_line_mark is not None:
            self.board.delete(self.temp_line_mark)

    # add line from p1 to p2. split_middle_lines_side_percentage = way to split the crossing middle lines. by default
    # percentage from left. if reference_point is not None, side to split is according to reference_point relative to other_edge_point
    # by default the line to add is the line created by user selected points
    def add_line(self, p1=None, p2=None, split_middle_lines_side_percentage=50.0, reference_point=None, other_edge_point=None, middle_lines=None):
        if p1 is None:
            p1 = self.new_line_edge[0]
        if p2 is None:
            p2 = self.new_line_edge[1]
        if p2 is None:
            return None
        if p1.is_equal(p2):
            # debug
            print(f'in add_line p1 == p2 ({p1.x}, {p1.y})')
            return None
        new_points = None
        s_part_1 = self.new_line_original_part[0]
        s_part_2 = self.new_line_original_part[1]
        if self.work_mode == gv.work_mode_dxf:
            if self.mouse_select_mode == gv.mouse_select_mode_point:
                entity_2 = self.entity_list[s_part_2.index]
                self.split_entity_by_point(s_part_1, p1)
                new_s_part_2_index = self.get_index_of_entity(entity_2)
                s_part_2.index = new_s_part_2_index
                self.split_entity_by_point(s_part_2, p2)
            self.add_line_to_entity_list(p1, p2)
        elif self.work_mode == gv.work_mode_inp:
            if middle_lines is None:
                crossing_lines = self.get_crossed_net_lines(p1, p2)
                new_points = [p1, p2]
                i = len(crossing_lines) - 1
                while i >= 0:
                    item = crossing_lines[i]
                    # index of line in self.net_line_list
                    line = item[0]
                    hash_node = item[1]
                    p = item[2]
                    if hash_node is None:
                        arg = (split_middle_lines_side_percentage, reference_point)
                        self.split_net_line(line, gv.split_mode_2_parts_percentage_side_by_reference_point, arg)
                        p = self.node_list[-1].p
                    new_points.append(p)
                    i -= 1
                # remove duplicate points
                new_points = list(dict.fromkeys(new_points))
                new_points = sort_list_point_by_distance_from_p(new_points, p1)
            # middle lines not none
            else:
                new_points = [p1]
                for i in middle_lines:
                    line = self.net_line_list[i]
                    start_node_p = self.get_node_p(line.start_node)
                    end_node_p = self.get_node_p(line.end_node)
                    middle_prev_line = reference_point.get_middle_point(other_edge_point)
                    middle_current_line = start_node_p.get_middle_point(end_node_p)
                    angle = middle_prev_line.get_alfa_to(middle_current_line)
                    shifted_reference_y = get_shifted_point(reference_point, middle_prev_line, -angle).y
                    shifted_start_y = get_shifted_point(start_node_p, middle_prev_line, -angle).y
                    if shifted_reference_y * shifted_start_y > 0:
                        reference_point = start_node_p
                        other_edge_point = end_node_p
                    else:
                        reference_point = end_node_p
                        other_edge_point = start_node_p
                    arg = (split_middle_lines_side_percentage, reference_point)
                    tmp_points = get_split_line_points(start_node_p, end_node_p, gv.split_mode_2_parts_percentage_side_by_reference_point, arg)
                    new_points.append(tmp_points[1])
                new_points.append(p2)
        return new_points

    # return list of nodes_hash_index between the 2 nodes in the shortest path
    def get_middle_nodes_between_node1_and_node_2(self, node1_hash_index, node2_hash_index, wrong_nodes=[]):
        # try to set middle nodes direction oriented
        middle_nodes, found_track = self.get_middle_nodes_direction_oriented(node1_hash_index, node2_hash_index, wrong_nodes)
        if found_track:
            return middle_nodes, True
        # try to set middle nodes on border lines only
        middle_nodes, found_track = self.get_middle_nodes_on_border_lines(node1_hash_index, node2_hash_index, wrong_nodes)
        if found_track:
            return middle_nodes, True
        else:
            return [], False

    # return list of nodes_hash_index between the 2 nodes on lines towards node2_hash_index
    def get_middle_nodes_direction_oriented(self, node1_hash_index, node2_hash_index, wrong_nodes):
        middle_nodes = []
        p1 = self.get_node_p(node1_hash_index)
        p2 = self.get_node_p(node2_hash_index)
        original_angle = p1.get_alfa_to(p2)
        node_hash = node1_hash_index
        next_node_hash = -1
        prev_node_hash = -1
        while node_hash != node2_hash_index and next_node_hash not in wrong_nodes:
            angle_to_target = self.get_node_p(node_hash).get_alfa_to(p2)
            diff_original_angle = get_smallest_diff_angle(angle_to_target, original_angle)
            if diff_original_angle > gv.max_diff_angle_for_direction_oriented:
                break
            node_index = get_index_from_hash(self.nodes_hash, node_hash)
            attached_lines = self.node_list[node_index].attached_lines
            next_node_hash = None
            smallest_diff_angle = gv.max_diff_angle_for_direction_oriented
            for al in attached_lines:
                if al.second_node == prev_node_hash:
                    continue
                diff_prev_angle = get_smallest_diff_angle(al.angle_to_second_node, angle_to_target)
                if diff_prev_angle < smallest_diff_angle:
                    next_node_hash = al.second_node
                    smallest_diff_angle = diff_prev_angle
                    continue
            if next_node_hash is not None:
                prev_node_hash = node_hash
                node_hash = next_node_hash
                middle_nodes.append(node_hash)
                continue
            else:
                break
        if node_hash == node2_hash_index:
            middle_nodes.pop(-1)
            return middle_nodes, True
        return [], False

    def get_middle_nodes_on_one_direction(self, node, prev_node, target_node, wrong_nodes=[]):
        middle_nodes = [node]
        c = len(self.node_list)
        while c > 0:
            node_index = get_index_from_hash(self.nodes_hash, node)
            attached_lines = self.node_list[node_index].attached_lines
            found_next = False
            for al in attached_lines:
                if al.border_type == gv.line_border_type_none or al.second_node == prev_node:
                    continue
                elif al.second_node == target_node:
                    return middle_nodes, True
                elif al.second_node in wrong_nodes:
                    return [], False
                else:
                    middle_nodes.append(al.second_node)
                    prev_node = node
                    node = al.second_node
                    found_next = True
                    break
            if not found_next:
                return [], False
            c -= 1
        return middle_nodes, True

    # return list of nodes_hash_index between the 2 nodes in the shortest path
    def get_middle_nodes_on_border_lines(self, node1_hash_index, node2_hash_index, wrong_nodes=[]):
        node_index = get_index_from_hash(self.nodes_hash, node1_hash_index)
        attached_lines = self.node_list[node_index].attached_lines
        side_border_node = []
        for al in attached_lines:
            if al.border_type != gv.line_border_type_none:
                side_border_node.append(al.second_node)
        if len(side_border_node) < 2:
            return [], False
        shortest_path = gv.infinite_size
        # try side 1
        next_node = side_border_node[0]
        middle_nodes, found_track = self.get_middle_nodes_on_one_direction(next_node, node1_hash_index, node2_hash_index, wrong_nodes)
        if found_track:
            shortest_path = len(middle_nodes)
        # try other side
        next_node = side_border_node[1]
        middle_nodes_2, found_track_2 = self.get_middle_nodes_on_one_direction(next_node, node1_hash_index, node2_hash_index, wrong_nodes)
        if found_track_2 and len(middle_nodes_2) < shortest_path:
            return middle_nodes_2, True
        return middle_nodes, found_track

    def get_index_of_entity(self, entity):
        for i in range(len(self.entity_list)):
            e = self.entity_list[i]
            if e.is_equal(entity):
                return i
        return None

    def clear_corner_list(self, keep_state=False):
        if len(self.corner_list) > 0:
            if keep_state:
                self.keep_state()
            self.hide_all_corners(keep_new_state=False)
            self.corner_list = []

    def add_corner_to_corner_list(self, corner):
        # in DXF mode - unlimited corners
        max_corners = len(self.node_list) - 1
        if self.work_mode == gv.work_mode_inp:
            max_corners = 4
        i = len(self.corner_list)
        if i < max_corners:
            if not self.is_corner_in_list(corner):
                self.keep_state()
                self.corner_list.append(corner)
                self.show_corner(i)

    def is_corner_in_list(self, corner):
        for c in self.corner_list:
            if c.hash_node == corner.hash_node:
                return True
        return False

    def add_list_of_lines_by_nodes(self, node_list):
        start_node = node_list[0]
        for i in range(1, len(node_list)):
            end_node = node_list[i]
            self.add_line_to_net_list_by_nodes(start_node, end_node)
            start_node = end_node

    def add_line_to_net_list_by_line(self, net_line, show_new_line=True):
        if not is_line_in_net_line_list(net_line, self.net_line_list):
            self.net_line_list.append(net_line)
            if show_new_line:
                self.show_net_line(-1)

    def add_line_to_net_list_by_nodes(self, start_hash_node, end_hash_node, entity=None, show_new_line=True):
        if start_hash_node == end_hash_node:
            # debug
            print(f'trying to add line by nodes with start_hash_node = end_hash_node {end_hash_node}')
            return
        line = NetLine(start_hash_node, end_hash_node, entity)
        self.add_line_to_net_list_by_line(line, show_new_line)

    def add_line_to_net_list_by_points(self, p1, p2, entity=None, show_new_line=True):
        if p1 == p2:
            # debug
            print(f'trying to add line by points with p1 = p2 ({p1.x}, {p1.y})')
            return
        start_hash_node = self.add_node_to_node_list(Node(p1))
        end_hash_node = self.add_node_to_node_list(Node(p2))
        line = NetLine(start_hash_node, end_hash_node, entity)
        self.add_line_to_net_list_by_line(line, show_new_line)

    def is_line_in_net_line_list(self, line):
        if line.start_node is None or line.end_node is None:
            # debug
            print('line with None nodes in is_line_in_net_line_list')
            return True
        if line.start_node == line.end_node:
            # debug
            print('line with start_node = end_node in is_line_in_net_line_list')
            return True
        for net_line in self.net_line_list:
            if (line.start_node == net_line.start_node and line.end_node == net_line.end_node) or (line.start_node == net_line.end_node and line.end_node == net_line.start_node):
                return True
        return False
    
    def add_line_to_entity_list(self, p1, p2):
        if self.work_mode != gv.work_mode_dxf:
            return
        if p1.is_equal(p2):
            # debug
            print(f'inadd_line_to_entity_list p1 == p2 ({p1.x}, {p1.y})')
            return
        e = Entity('LINE', start=p1, end=p2)
        e.is_marked = False
        e.color = gv.default_entity_color
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
        start_node_index = get_index_from_hash(self.nodes_hash, start_node_hash)
        end_node_index = get_index_from_hash(self.nodes_hash, end_node_hash)
        if start_node_index is None or end_node_index is None:
            #debug
            print('line start or end nodes are None in find_nearest_net_line min_d_index')
            return None, None
        p1 = self.get_node_p(start_node_hash)
        p2 = self.get_node_p(end_node_hash)
        min_d, nearest_point = self.get_distance_from_line_and_nearest_point(p, p1, p2)
        for i in range(len(self.net_line_list)):
            if only_visible and self.net_line_list[i].board_part is None:
                continue
            start_node_hash = self.net_line_list[i].start_node
            end_node_hash = self.net_line_list[i].end_node
            start_node_index = get_index_from_hash(self.nodes_hash, start_node_hash)
            end_node_index = get_index_from_hash(self.nodes_hash, end_node_hash)
            if start_node_index is None or end_node_index is None:
                # debug
                print('line start or end nodes are None in loop find_nearest_net_line min_d_index')
                return None, None
            p1 = self.get_node_p(start_node_hash)
            p2 = self.get_node_p(end_node_hash)
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
            part = get_index_from_hash(self.nodes_hash, part)
            if part is not None:
                self.node_list[part].color = color
        self.show_part(part, list_name)

    # part = index in node_list (not hash)
    def hide_node(self, part):
        n = self.node_list[part]
        if n.board_part is not None:
            self.board.delete(n.board_part)
            self.node_list[part].board_part = None
        if n.board_text is not None:
            self.board.delete(n.board_text)
            self.node_list[part].board_text = None

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

    def hide_all_nodes(self, keep_new_state=True):
        for i in range(len(self.node_list)):
            self.hide_node(i)
        if keep_new_state:
            self.show_nodes = False

    def show_all_nodes(self, keep_new_state=True):
        for i in range(1, len(self.node_list)):
            self.show_node(i, self.show_node_number)
        if keep_new_state:
            self.show_nodes = True
        self.window_main.update()

    # i = index in corner_list
    def show_corner(self, i):
        corner = self.corner_list[i]
        p = self.get_node_p(corner.hash_node)
        if corner.board_part is None:
            part = self.draw_square(p, 10/self.scale, gv.corner_color)
            self.corner_list[i].board_part = part
        if corner.board_text is None:
            x, y = self.convert_xy_to_screen(p.x, p.y)
            x += 9
            y -= 9
            self.corner_list[i].board_text = self.board.create_text(x, y, text=i+1, fill=gv.corner_text_color, justify=tk.RIGHT)

    def hide_corner(self, i):
        corner = self.corner_list[i]
        if corner.board_part is not None:
            self.board.delete(corner.board_part)
            self.corner_list[i].board_part = None
        if corner.board_text is not None:
            self.board.delete(corner.board_text)
            self.corner_list[i].board_text = None

    def show_all_corners(self, keep_new_state=True):
        for i in range(len(self.corner_list)):
            self.show_corner(i)
        if keep_new_state:
            self.show_corners = True
        self.window_main.update()

    def hide_all_corners(self, keep_new_state=True):
        for i in range(len(self.corner_list)):
            self.hide_corner(i)
        if keep_new_state:
            self.show_corners = False

    def show_element(self, e):
        element = self.element_list[e]
        nodes = element.nodes
        if element.board_part is None:
            poly = []
            for node_index in nodes:
                poly.append(self.node_list[node_index].p)
            self.element_list[e].board_part = self.draw_polygon(poly)

    def hide_element(self, e):
        part = self.element_list[e].board_part
        if part is not None:
            self.board.delete(part)
            self.element_list[e].board_part = None

    def show_all_elements(self, keep_new_state=True):
        for i in range(len(self.element_list)):
            self.show_element(i)
        if keep_new_state:
            self.show_elements = True
        self.window_main.update()

    def hide_all_elements(self, keep_new_state=True):
        for i in range(len(self.element_list)):
            self.hide_element(i)
        if keep_new_state:
            self.show_elements = False

    def show_inp_line(self, inp_index, line_index):
        if inp_index > len(self.inp_nets) - 1:
            return
        line = self.inp_nets[inp_index].lines[line_index]
        if line.board_part is None:
            node1 = self.inp_nets[inp_index].node_list[line.start_node]
            p1 = node1.p
            node2 = self.inp_nets[inp_index].node_list[line.end_node]
            p2 = node2.p
            line.board_part = self.draw_line(p1, p2, line.color)

    def hide_inp_line(self, inp_index, line_index):
        if inp_index > len(self.inp_nets) - 1:
            return
        line = self.inp_nets[inp_index].lines[line_index]
        if line.board_part is not None:
            self.board.delete(line.board_part)
            line.board_part = None

    def show_inp_rotation_point(self):
        if len(self.inp_nets) < 1:
            return
        inp_net = self.inp_nets[-1]
        if inp_net.rotation_point is not None and inp_net.rotation_point.reference_point is not None and inp_net.rotation_point.board_part is None:
            self.keep_state()
            inp_net.rotation_point.board_part = self.draw_circle(inp_net.rotation_point.reference_point, 3/self.scale, inp_net.rotation_point.color)
            inp_net.rotation_point.second_board_part = self.draw_circle(inp_net.rotation_point.reference_point, 6/self.scale, inp_net.rotation_point.color)

    def clear_inp_rotation_point(self):
        if len(self.inp_nets) < 1:
            return
        inp_net = self.inp_nets[-1]
        if inp_net.rotation_point is not None:
            if inp_net.rotation_point.board_part is not None:
                self.keep_state()
                self.board.delete(inp_net.rotation_point.board_part)
            if inp_net.rotation_point.second_board_part is not None:
                self.board.delete(inp_net.rotation_point.second_board_part)
        inp_net.rotation_point = None

    def show_inp(self, inp_index):
        if inp_index > len(self.inp_nets) - 1:
            return
        for i in range(len(self.inp_nets[inp_index].lines)):
            self.show_inp_line(inp_index, i)

    def hide_inp(self, inp_index):
        if inp_index > len(self.inp_nets) - 1:
            return
        for i in range(len(self.inp_nets[inp_index].lines)):
            self.hide_inp_line(inp_index, i)

    def show_all_inp_nets(self, keep_new_state=True):
        for i in range(len(self.inp_nets)):
            self.show_inp(i)
        if keep_new_state:
            self.show_inps = True

    def hide_all_inp_nets(self, keep_new_state=True):
        for i in range(len(self.inp_nets)):
            self.hide_inp(i)
        if keep_new_state:
            self.show_inps = False

    def show_net_line(self, i):
        line = self.net_line_list[i]
        start_node = get_index_from_hash(self.nodes_hash, line.start_node)
        end_node = get_index_from_hash(self.nodes_hash, line.end_node)
        if start_node is None or end_node is None:
            #debug
            print('line start or end nodes are None in show_net_line')
            return
        p1 = self.get_node_p(line.start_node)
        p2 = self.get_node_p(line.end_node)
        if line.board_part is None:
            line.board_part = self.draw_line(p1, p2, line.color)

    def hide_net_line(self, part):
        line = self.net_line_list[part]
        if line.board_part is not None:
            self.board.delete(line.board_part)
            line.board_part = None

    def show_all_net_lines(self, keep_new_state=True):
        for i in range(len(self.net_line_list)):
            self.show_net_line(i)
        if keep_new_state:
            self.show_net = True
        self.window_main.update()

    def hide_all_net_lines(self, keep_new_state=True):
        for i in range(len(self.net_line_list)):
            self.hide_net_line(i)
        if keep_new_state:
            self.show_net = False

    def set_net_line_color(self, part, color):
        self.hide_net_line(part)
        self.net_line_list[part].color = color
        self.show_net_line(part)

    def define_new_entity_color(self, entity):
        if self.work_mode == gv.work_mode_inp:
            self.entity_list[entity].color = gv.weak_entity_color
        else:
            self.entity_list[entity].color = gv.default_entity_color

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

    def hide_entity(self, part):
        if self.entity_list[part].board_part is None:
            return
        self.board.delete(self.entity_list[part].board_part)
        self.entity_list[part].board_part = None

    def show_all_entities(self, keep_new_state=True):
        for i in range(len(self.entity_list)):
            self.show_entity(i)
        if keep_new_state:
            self.show_entities = True
        self.window_main.update()

    def hide_all_entities(self, keep_new_state=True):
        for i in range(len(self.entity_list)):
            self.hide_entity(i)
        if keep_new_state:
            self.show_entities = False

    def set_entity_color(self, part, color):
        self.hide_entity(part)
        self.entity_list[part].color = color
        self.show_entity(part)
        
    def set_all_entities_color(self, color):
        for i in range(len(self.entity_list)):
            self.set_entity_color(i, color)
        self.show_entities = True
        self.update_view()

    def clear_net(self):
        self.hide_all_elements()
        line_list = []
        border_nodes = self.set_border_lines()
        if len(border_nodes) == 0:
            print('Attention - border lines not set properly')
        for i in range(len(self.net_line_list)):
            line = self.net_line_list[i]
            if line.border_type == gv.line_border_type_none:
                line_list.append(i)
        if len(line_list) > 0:
            self.keep_state()
            self.remove_parts_from_list(line_list, gv.part_list_net_lines)

    def reset_net(self, keep_state=False):
        if keep_state:
            self.keep_state()
        self.hide_all_elements(keep_new_state=False)
        self.hide_all_net_lines(keep_new_state=False)
        self.hide_all_nodes(keep_new_state=False)
        self.node_list = [Node()]
        self.nodes_hash = {'0': 0}
        self.next_node_hash_index = 1
        self.net_line_list = []
        self.element_list = []

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
        gv.accuracy = zeros + gv.default_accuracy
        # debug
        print(f'set accuracy: 1/{int(math.pow(10, gv.accuracy))}')

    def update_view(self):
        self.hide_all_entities(False)
        self.hide_all_inp_nets(False)
        self.hide_all_net_lines(False)
        self.hide_all_nodes(False)
        self.hide_all_elements(False)
        self.hide_all_corners(False)
        if self.show_elements:
            self.show_all_elements()
        if self.show_entities:
            self.show_all_entities()
        if self.show_inps:
            self.show_all_inp_nets()
        if self.show_nodes:
            self.show_all_nodes()
        if self.show_net:
            self.show_all_net_lines()            
        if self.show_corners:
            self.show_all_corners()
        self.window_main.update()

    # debug
    def test_key(self, key):
        print(key.keycode)

