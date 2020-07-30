
WINDOW_HEIGHT = 500
WINDOW_WIDTH = int(WINDOW_HEIGHT*4/3)
WINDWO_SIZE = str(WINDOW_WIDTH)+'x'+str(WINDOW_HEIGHT)
BOARD_HEIGHT = 50000
BOARD_WIDTH = int(BOARD_HEIGHT*4/3)

max_nodes_to_create_element = 4

default_split_parts = 2
default_split_circle_parts = 18
max_arc_angle_for_net_line = 36
# length relative to length of object measured from bottom-left to right-up
max_line_length_for_net_line = 0.6

accuracy = 3
angle_diff_accuracy = 1
min_angle_to_create_element = 20
max_angle_to_create_element = 160
max_state_stack = 100
max_split_parts = 100
min_split_percentage = 1
max_split_side_percentage = 100-min_split_percentage
max_split_middle_percentage = 100-2*min_split_percentage

handle_corners_mode_clear = 'clear'
handle_corners_mode_set_net = 'set_net'
corners_set_net_both = 'both'
corners_set_net_left_right = 'left-right'
corners_set_net_bottom_top = 'bottom_top'
mouse_select_mode_edge = 'edge'
mouse_select_mode_point = 'point'
mouse_select_mode_corner = 'corner'
work_mode_dxf = 'dxf'
work_mode_inp = 'inp'
part_type_entity = 'entity'
part_type_net_line = 'net_line'
mark_option_mark = 'mark'
mark_option_unmark = 'unmark'
mark_option_invert = 'invert'
part_list_entities = 'entities'
part_list_net_lines = 'net_lines'
part_list_nodes = 'nodes'
show_mode = 'show'
hide_mode = 'hide'
clear_mode = 'clear'
split_mode_evenly_n_parts = 'evenly_n_parts'
split_mode_2_parts_by_point = '2_parts_by_point'
split_mode_2_parts_percentage_left = '2_parts_percentage_left'
split_mode_2_parts_percentage_side_by_point = '2_parts_percentage_side_by_point'
split_mode_3_parts_percentage_middle = '3_parts_percentage_middle'
split_mode_graduate_n_parts = 'graduate_n_parts'
split_mode_graduate_percentage_left_right = 'graduate_percentage_left_right'
split_mode_by_longitude = 'by_longitude'
split_mode_by_angle = 'by_angle'
net_line_border_type_none = 'none'
net_line_border_type_outer = 'outer'
net_line_border_type_inner = 'inner'

default_mouse_select_mode = mouse_select_mode_edge
default_work_mode = work_mode_dxf
default_select_parts_mode = part_type_entity
default_mark_option = mark_option_mark
default_show_node_number = False

edge_line_mark_radius = 5
node_mark_radius = 3

board_bg_color = '#D1EDFF'
default_color = '#0099FF'
default_entity_color = default_color
marked_entity_color = 'orange'
weak_entity_color = 'yellow'
selected_item_color = '#FFFFcc'
temp_line_color = 'red'
node_color = 'red'
invalid_node_color = 'green'
net_line_color = 'red'
marked_net_line_color = '#777777'
text_color = 'green'
element_color = 'white'
mark_rect_color = 'black'
corner_color = '#0000FF'
corner_text_color = corner_color

# node exceptions
unattached = 'unattached'
too_steep_angle = 'too steep angle'
too_wide_angle = 'too wide angle'
expected_elements_not_complete = 'expected elements not completed'






