from fabian_classes import *
from point import *
from tkinter import messagebox


def get_index_from_hash(hash_table, hash_index):
    return hash_table.get(str(hash_index))


def get_smallest_diff_angle(angle1, angle2):
    if angle2 < angle1:
        angle1, angle2 = angle2, angle1
    if angle2 - angle1 > 180:
        angle1 += 360
    return math.fabs(angle2 - angle1)


def is_line_in_net_line_list(line, net_line_list):
    # validity check
    if line.start_node is None or line.end_node is None:
        # debug
        print('line with None nodes in is_line_in_net_line_list')
        return True
    if line.start_node == line.end_node:
        # debug
        print('line with start_node = end_node in is_line_in_net_line_list')
        return True
    for net_line in net_line_list:
        if (line.start_node == net_line.start_node and line.end_node == net_line.end_node) or (
                line.start_node == net_line.end_node and line.end_node == net_line.start_node):
            return True
    return False


# return True if p is equal any node.p in node_list
def is_point_in_node_list(p, node_list):
    for node in node_list:
        if p.is_equal(node.p):
            return True
    return False


# return the real index, not the hash
def get_index_of_node_with_point_in_list(p, node_list):
    for i in range(len(node_list)):
        node = node_list[i]
        if p.is_equal(node.p):
            return i
    return None


def get_split_line_points(p1, p2, split_mode=gv.split_mode_evenly_n_parts, split_arg=gv.default_split_parts):
    point_list = [p1]
    alfa = p1.get_alfa_to(p2) * math.pi / 180
    d = p1.get_distance_to_point(p2)
    start = p1
    if split_mode == gv.split_mode_2_parts_by_point:
        middle_point = split_arg
        point_list.append(middle_point)
        point_list.append(p2)
        return point_list
    # check for valid point
    if split_mode == gv.split_mode_2_parts_percentage_side_by_reference_point:
        if not isinstance(split_arg, tuple):
            percentage_left = split_arg
        else:
            percentage_left = split_arg[0]
            if len(split_arg) > 1 and isinstance(split_arg[1], Point):
                reference_point = split_arg[1]
                d1 = p1.get_distance_to_point(reference_point)
                d2 = p2.get_distance_to_point(reference_point)
                if d2 < d1:
                    percentage_left = 100 - percentage_left
        p_list = [percentage_left]
    else:
        if split_mode == gv.split_mode_by_percentage_list:
            p_list = split_arg
        else:
            p_list = get_middle_split_points_percentage_list(split_mode, split_arg)
        if p2.is_smaller_x_smaller_y(p1):
            for i in range(len(p_list)):
                p_list[i] = 100 - p_list[i]
            p_list.reverse()
    for p in p_list:
        current_d = d * p / 100
        middle_point = Point(start.x + current_d * math.cos(alfa), start.y + current_d * math.sin(alfa))
        point_list.append(middle_point)
    point_list.append(p2)
    point_list = check_point_list_validity(point_list)
    return point_list


def get_split_arc_points(arc, split_mode=gv.split_mode_evenly_n_parts, split_arg=gv.default_split_parts):
    point_list = [arc.start]
    start_angle = arc.arc_start_angle
    diff_angle = arc.arc_end_angle - arc.arc_start_angle
    if split_mode == gv.split_mode_2_parts_by_point:
        middle_point = split_arg
        end_angle = arc.center.get_alfa_to(middle_point)
        new_arc = Entity(shape=arc.shape, center=arc.center, radius=arc.radius, start_angle=start_angle,
                         end_angle=end_angle)
        point_list.append(new_arc.end)
        point_list.append(arc.end)
        return point_list
    if split_mode == gv.split_mode_by_percentage_list:
        p_list = split_arg
    else:
        p_list = get_middle_split_points_percentage_list(split_mode, split_arg)
    if arc.end.is_smaller_x_smaller_y(arc.start):
        for i in range(len(p_list)):
            p_list[i] = 100 - p_list[i]
        p_list.reverse()
    for p in p_list:
        end_angle = arc.arc_start_angle + diff_angle * p / 100
        new_arc = Entity(shape=arc.shape, center=arc.center, radius=arc.radius, start_angle=start_angle,
                         end_angle=end_angle)
        point_list.append(new_arc.end)
        start_angle = end_angle
    point_list.append(arc.end)
    point_list = check_point_list_validity(point_list)
    return point_list


def get_split_circle_points(circle, parts, start_angle, end_angle=None):
    point_list = []
    n = parts
    diff_angle = 360
    if end_angle is not None:
        if end_angle < start_angle:
            end_angle += 360
        diff_angle = end_angle - start_angle
    for i in range(n):
        end_angle = start_angle + (diff_angle / n)
        arc = Entity('ARC', center=circle.center, radius=circle.radius, start_angle=start_angle, end_angle=end_angle)
        point_list.append(arc.start)
        start_angle = end_angle
    return point_list


def get_middle_split_points_percentage_list(split_mode, split_arg):
    p_list = []
    if split_mode == gv.split_mode_evenly_n_parts:
        n = split_arg
        for i in range(1, n):
            p_list.append(i * 100 / n)
    elif split_mode == gv.split_mode_2_parts_percentage_left:
        percentage_left = split_arg
        p_list.append(percentage_left)
    elif split_mode == gv.split_mode_2_parts_percentage_side_by_reference_point:
        percentage_left = split_arg[0]
        p_list.append(percentage_left)
    elif split_mode == gv.split_mode_3_parts_percentage_middle:
        percentage_middle = split_arg
        percentage_side = (100 - percentage_middle) / 2
        p_list.append(percentage_side)
        p_list.append(percentage_side + percentage_middle)
    elif split_mode == gv.split_mode_graduate_n_parts:
        n = split_arg[0]
        left = split_arg[1]
        diff = 100 - (n * left)
        sum_n = n * (n - 1) / 2
        step = diff / sum_n
        add_on = 0
        for i in range(n - 1):
            add_on = add_on + left + step * i
            p_list.append(add_on)
    elif split_mode == gv.split_mode_graduate_from_middle:
        total_parts = split_arg[0]
        side_parts = math.ceil(total_parts / 2)
        middle = split_arg[1]
        start_middle_percentage = 50
        if total_parts % 2 == 1:
            start_middle_percentage -= middle / 2
        side_ratio = 100 / (100 - start_middle_percentage)
        middle_side = middle * side_ratio
        diff = 100 - (side_parts * middle_side)
        sum_n = side_parts * (side_parts - 1) / 2
        step = diff / sum_n / side_ratio
        add_on = 0
        # collect points from middle to one side
        for i in range(side_parts - 1):
            add_on = add_on + middle + step * i
            p_list.append(start_middle_percentage + add_on)
        n = len(p_list)
        # insert symmetrical points from other side to middle
        for i in range(n):
            p_list.insert(i, 100 - p_list[-(i + 1)])
        if total_parts % 2 == 0:
            p_list.insert(n, 50)
    elif split_mode == gv.split_mode_graduate_percentage_left_right:
        left = split_arg[0]
        right = split_arg[1]
        diff = 100 - (left + right)
        both_sides = left + right
        residual = left - right
        chunk = math.ceil(diff / both_sides)
        bulk = 100 / chunk
        add_on = (bulk - both_sides) / 2
        left += add_on
        right += add_on
        n = 2 * chunk - 1
        step = residual / n
        current_p = left
        add_on = left
        for i in range(1, n + 1):
            p_list.append(current_p)
            add_on -= step
            current_p += add_on
    if split_mode == gv.split_mode_graduate_from_middle or split_mode == gv.split_mode_graduate_n_parts:
        p_list = check_percentage_list_validity(p_list)
    return p_list


def check_percentage_list_validity(p_list):
    p = p_list[0]
    valid = False
    if p > 0:
        valid = True
        for i in range(len(p_list)):
            if p_list[i] < p or p_list[i] >= 100:
                valid = False
                break
    if not valid:
        m = f"can't split with current parameters"
        messagebox.showwarning("Warning", m)
        p_list = [50]
    return p_list


def check_point_list_validity(point_list):
    if len(point_list) < 3:
        return point_list
    # check closest nodes (list edges)
    if point_list[0].is_equal(point_list[1]) or point_list[-1].is_equal(point_list[-2]):
        m = f"Too short lines, change split parameters"
        messagebox.showwarning("Warning", m)
        point_list = [point_list[0], point_list[-1]]
    return point_list


# return continues list of lines, None if the list is broken
def sort_net_line_parts(net_line_list, part_list):
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
        line_i = net_line_list[part_list[i]]
        is_line_i_start_node_connected = False
        is_line_i_end_node_connected = False
        for j in range(len(part_list)):
            if j == i:
                continue
            line_j = net_line_list[part_list[j]]
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
    entity = net_line_list[first_line].entity
    next_node = net_line_list[first_line].end_node
    sorted_list.append(first_line)
    part_list.remove(first_line)
    found_part = False
    # iterate list to find connected parts, add to list or return None if can't find
    while len(part_list) > 0:
        for j in part_list:
            found_part = False
            line = net_line_list[j]
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
def sort_entity_parts(entity_list, part_list):
    if part_list is None:
        return None
    elif len(part_list) == 0:
        return None
    elif len(part_list) == 1:
        return part_list
    sorted_list = []
    first_part = part_list[0]
    e_0 = entity_list[first_part]
    shape = e_0.shape
    for i in part_list:
        ei = entity_list[i]
        if ei.shape != e_0.shape:
            return None
    if shape == 'CIRCLE':
        return None
    elif shape == 'ARC':
        # check that all parts with same center and radius
        for i in part_list:
            ei = entity_list[i]
            if ei.center != e_0.center or ei.radius != e_0.radius:
                return None
        sorted_list.append(first_part)
        part_list.remove(first_part)
        found_part = False
        # iterate list to find connected parts, add to list or return None if can't find
        while len(part_list) > 0:
            start = entity_list[sorted_list[0]].arc_start_angle % 360
            end = entity_list[sorted_list[-1]].arc_end_angle % 360
            for j in part_list:
                found_part = False
                if entity_list[j].arc_start_angle % 360 == end:
                    sorted_list.append(j)
                    found_part = True
                    part_list.remove(j)
                    break
                elif entity_list[j].arc_end_angle % 360 == start:
                    sorted_list.insert(0, j)
                    found_part = True
                    part_list.remove(j)
                    break
            if not found_part:
                return None
    elif shape == 'LINE':
        for i in part_list:
            if ei.left_bottom.is_smaller_x_smaller_y(e_0.left_bottom):
                first_part = i
                e_0 = entity_list[first_part]
        sorted_list.append(first_part)
        part_list.remove(first_part)
        found_part = False
        # iterate list to find connected parts, add to list or return None if can't find
        while len(part_list) > 0:
            start = entity_list[sorted_list[-1]].right_up
            for j in part_list:
                found_part = False
                if entity_list[j].left_bottom == start:
                    sorted_list.append(j)
                    found_part = True
                    part_list.remove(j)
                    break
            if not found_part:
                return None
        # set start and end points accordingly
        for i in sorted_list:
            e = entity_list[i]
            e.start, e.end = e.left_bottom, e.right_up
    return sorted_list


# set expected elements
# set exceptions for unattached and exceeding angles
def set_node_expected_elements_and_exceptions(node):
    node.exceptions = []
    num_lines = len(node.attached_lines)
    if num_lines < 2:
        node.exceptions.append(gv.unattached)
        node.expected_elements = 0
        node.exceptions.append(gv.unattached)
        return node
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
        m = f'unexpected number of border lines in set_node_expected_elements_and_exceptions node(hash) {node.hash_index}  outer: {num_outer_lines}   inner: {num_inner_lines}'
        print(m)
        return node
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
    return node


def get_distance_from_line_and_nearest_point(p, line_start, line_end):
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


# return the distance of Point p from entity[i]
def get_distance_from_entity_and_nearest_point(p, index, entity_list, only_visible=False):
    e = entity_list[index]
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
        d, nearest_point = get_distance_from_line_and_nearest_point(p, e.start, e.end)
    return round(d, gv.accuracy), nearest_point


# return closest inp node - inp_net_index, node_index, distance
def find_nearest_inp_node(p, inp_net_list):
    if inp_net_list is None:
        return None, None, None
    min_d_inp_index = 0
    min_d_node_index = 0
    min_d = gv.infinite_size
    for inp_index in range(len(inp_net_list)):
        inp_net = inp_net_list[inp_index]
        for node_index in range(len(inp_net.node_list)):
            node = inp_net.node_list[node_index]
            d = p.get_distance_to_point(node.p)
            if d < min_d:
                min_d_inp_index = inp_index
                min_d_node_index = node_index
                min_d = d
    return min_d_inp_index, min_d_node_index, min_d


# return index of the most bottom - left node
def get_bottom_left_node(node_list):
    if len(node_list) < 2:
        return 0
    index = 0
    p = node_list[index].p
    for i in range(len(node_list)):
        if node_list[i].p.is_smaller_x_smaller_y(p, by_x=False):
            p = node_list[i].p
            index = i
    return index


# return index of the most top - right node
def get_top_right_node(node_list):
    if len(node_list) < 2:
        return 0
    index = 0
    p = node_list[index].p
    for i in range(len(node_list)):
        if p.is_smaller_x_smaller_y(node_list[i].p, by_x=False):
            p = node_list[i].p
            index = i
    return index


# return index of node in node_list which is the most external relative to p0 and prev_angle
def get_most_external_node(p0, prev_angle, node_list, counter_clockwise=True):
    if node_list is None:
        return None
    if len(node_list) == 0:
        return None
    most_external_index = 0
    min_angle = gv.angle_diff_accuracy
    max_angle = 360 - gv.angle_diff_accuracy
    best_angle = max_angle
    if counter_clockwise:
        min_angle, max_angle = (360 - max_angle), (360 - min_angle)
        best_angle = min_angle
    for i in range(len(node_list)):
        node = node_list[i]
        angle = p0.get_alfa_to(node.p)
        if angle < prev_angle:
            angle += 360
        angle -= prev_angle
        if 0 <= angle <= 180:
            diff_angle = 180 - angle
        else:
            diff_angle = 540 - angle
        replace_best_angle = False
        if counter_clockwise and best_angle <= diff_angle <= max_angle:
            replace_best_angle = True
        elif not counter_clockwise and min_angle <= diff_angle <= best_angle:
            replace_best_angle = True
        if replace_best_angle:
            best_angle = diff_angle
            most_external_index = i
    return most_external_index


def get_inp_percentage_middle_nodes(inp_net, corner_list):
    middle_nodes = get_inp_corners_middle_nodes(inp_net, corner_list)
    if middle_nodes is None:
        return None
    middle_nodes_1_2 = middle_nodes[0]
    middle_nodes_2_3 = middle_nodes[1]
    middle_nodes_3_4 = middle_nodes[2]
    middle_nodes_4_1 = middle_nodes[3]
    middle_nodes_1_2 = convert_partial_node_list_to_middle_nodes_percentage_list(middle_nodes_1_2, inp_net.node_list)
    middle_nodes_2_3 = convert_partial_node_list_to_middle_nodes_percentage_list(middle_nodes_2_3, inp_net.node_list)
    middle_nodes_3_4 = convert_partial_node_list_to_middle_nodes_percentage_list(middle_nodes_3_4, inp_net.node_list)
    middle_nodes_4_1 = convert_partial_node_list_to_middle_nodes_percentage_list(middle_nodes_4_1, inp_net.node_list)
    return middle_nodes_1_2, middle_nodes_2_3, middle_nodes_3_4, middle_nodes_4_1


# return distance of middle nodes in partial_node_list from partial_node_list[0] as percentage (0-1) of
# distance between partial_node_list[0] and partial_node_list[-1]
def convert_partial_node_list_to_middle_nodes_percentage_list(partial_node_list, node_list):
    if partial_node_list is None or node_list is None:
        return None
    if len(partial_node_list) < 3:
        return []
    middle_nodes_p_list = []
    p1 = node_list[partial_node_list[0]].p
    d = 0
    for i in range(len(partial_node_list) - 1):
        p2 = node_list[partial_node_list[i + 1]].p
        d += p1.get_distance_to_point(p2)
        middle_nodes_p_list.append(d)
        p1 = p2
    middle_nodes_p_list.pop(-1)
    for i in range(len(middle_nodes_p_list)):
        node_d = middle_nodes_p_list[i]
        middle_nodes_p_list[i] = float(node_d / d)
    return middle_nodes_p_list


def get_inp_border_nodes(inp_net):
    start_node = get_inp_bottom_left_node(inp_net)
    border_nodes = [start_node]
    current_node = start_node
    prev_angle = 0
    next_node = -1
    while next_node != start_node and len(border_nodes) <= len(inp_net.node_list):
        node_list = []
        node_list_indexes = inp_net.get_attached_nodes(current_node)
        for index in node_list_indexes:
            node_list.append(inp_net.node_list[index])
        p = inp_net.node_list[current_node].p
        next_node = get_most_external_node(p, prev_angle, node_list)
        next_node = node_list_indexes[next_node]
        border_nodes.append(next_node)
        prev_angle = p.get_alfa_to(inp_net.node_list[next_node].p)
        current_node = next_node
    if border_nodes[-1] == start_node:
        border_nodes.pop(-1)
        return border_nodes
    else:
        print("can't set border for inp")
        return []


# return 4 node list include the corners
def get_inp_corners_middle_nodes(inp_net, corner_list):
    if len(corner_list) != 4:
        return None
    borde_nodes = get_inp_border_nodes(inp_net)
    if len(borde_nodes) == 0:
        return None
    # check that all corners on border line
    for corner in corner_list:
        if corner.hash_node not in borde_nodes:
            print("inp corners not on inp border")
            return None
    # check that corners are set by order on border line
    corner_1_index = borde_nodes.index(corner_list[0].hash_node)
    corner_set = '1'
    for i in range(1, len(borde_nodes)):
        n = borde_nodes[(i + corner_1_index) % len(borde_nodes)]
        if n == corner_list[1].hash_node:
            corner_set += '2'
        elif n == corner_list[2].hash_node:
            corner_set += '3'
        elif n == corner_list[3].hash_node:
            corner_set += '4'
    if corner_set == '1234':
        order_value = 1
    elif corner_set == '1432':
        order_value = -1
    else:
        print("inp corners not set by order (" + corner_set + ")")
        return None
    middle_nodes_1_2 = [corner_list[0].hash_node]
    middle_nodes_2_3 = [corner_list[1].hash_node]
    middle_nodes_3_4 = [corner_list[2].hash_node]
    middle_nodes_4_1 = [corner_list[3].hash_node]
    index = corner_1_index
    middle_node = -1
    while middle_node != corner_list[1].hash_node:
        index = (index + order_value) % len(borde_nodes)
        middle_node = borde_nodes[index]
        middle_nodes_1_2.append(middle_node)
    while middle_node != corner_list[2].hash_node:
        index = (index + order_value) % len(borde_nodes)
        middle_node = borde_nodes[index]
        middle_nodes_2_3.append(middle_node)
    while middle_node != corner_list[3].hash_node:
        index = (index + order_value) % len(borde_nodes)
        middle_node = borde_nodes[index]
        middle_nodes_3_4.append(middle_node)
    while middle_node != corner_list[0].hash_node:
        index = (index + order_value) % len(borde_nodes)
        middle_node = borde_nodes[index]
        middle_nodes_4_1.append(middle_node)
    return middle_nodes_1_2, middle_nodes_2_3, middle_nodes_3_4, middle_nodes_4_1


def get_inp_bottom_left_node(inp_net):
    node_list = inp_net.node_list.copy()
    top_right_index = get_top_right_node(node_list)
    top_right_p = node_list[top_right_index].p
    attached_nodes = []
    while len(attached_nodes) < 2:
        bottom_left_index = get_bottom_left_node(node_list)
        if bottom_left_index == top_right_index:
            return None
        attached_nodes = inp_net.get_attached_nodes(bottom_left_index)
        if len(attached_nodes) > 1:
            return bottom_left_index
        else:
            node_list[bottom_left_index].p = top_right_p
    return None


# return list of entities connected between p1-p2, None if can't find
# invalid_p is necessary to define correct direction
def get_entities_between_points(entity_list, p1, p2, invalid_p):
    p1_entities = get_entities_with_edge_point(entity_list, p1)
    if len(p1_entities) < 2:
        return []
    # validity check
    p2_entities = get_entities_with_edge_point(entity_list, p2)
    if len(p2_entities) < 2:
        return []
    # try one direction
    e_list = get_entities_towards_point(entity_list, p1_entities[0], p1, p2, invalid_p)
    if e_list is not None:
        return e_list
    e_list = get_entities_towards_point(entity_list, p1_entities[1], p1, p2, invalid_p)
    if e_list is None:
        return []
    return e_list


def get_entities_towards_point(entity_list, start_entity, p1, p2, invalid_p):
    e_list = []
    entity_index = start_entity
    next_point = p1
    while not next_point.is_equal(p2):
        entity = entity_list[entity_index]
        if entity.start.is_equal(next_point):
            next_point = entity.end
        else:
            next_point = entity.start
        if next_point.is_equal(invalid_p):
            return None
        e_list.append(entity_index)
        next_entities = get_entities_with_edge_point(entity_list, next_point)
        next_entities.remove(entity_index)
        if len(next_entities) < 1:
            return None
        entity_index = next_entities[0]
    return e_list


def get_entities_with_edge_point(entity_list, p):
    e_list = []
    for i in range(len(entity_list)):
        entity = entity_list[i]
        if entity.shape == 'CIRCLE':
            continue
        if entity.start.is_equal(p) or entity.end.is_equal(p):
            e_list.append(i)
    return e_list


def get_entities_relative_length(entity_list, connected_entities):
    len_list = []
    len_p_list = []
    length = 0
    for e in connected_entities:
        start_length = length
        entity = entity_list[e]
        length += entity.get_length()
        end_length = length
        len_list.append((start_length, end_length))
    for i in range(len(len_list)):
        entity_edges = len_list[i]
        start_p_length = entity_edges[0] / length
        end_p_length = entity_edges[1] / length
        len_p_list.append((start_p_length, end_p_length))
    return len_p_list


def get_entity_relative_p_list(entity_start_p, entity_end_p, total_p_list):
    accuracy = 6
    e_relative_length = entity_end_p - entity_start_p
    if round(entity_start_p, accuracy) > round(total_p_list[-1], accuracy) or round(entity_end_p, accuracy) < round(total_p_list[0], accuracy):
        return []
    p_list = []
    i = 0
    while round(total_p_list[i], accuracy) < round(entity_start_p, accuracy):
        i += 1
    while i < len(total_p_list):
        p = total_p_list[i]
        if round(p, accuracy) > round(entity_end_p, accuracy):
            break
        p_list.append(100 * round((p - entity_start_p) / e_relative_length, accuracy))
        i += 1
    return p_list


def get_entities_p_list(entities_relative_len, total_p_list):
    p_list = []
    for i in range(len(entities_relative_len)):
        entity_start_p = entities_relative_len[i][0]
        entity_end_p = entities_relative_len[i][1]
        p_list.append(get_entity_relative_p_list(entity_start_p, entity_end_p, total_p_list))
    return p_list


def get_connected_entities_split_points(p1, p2, entity_list, connected_entities, entities_p_list):
    first_entity = entity_list[connected_entities[0]]
    if len(connected_entities) == 1:
        p_list = entities_p_list[0]
        if p2.is_smaller_x_smaller_y(p1):
            p_list.reverse()
            for i in range(len(p_list)):
                p_list[i] = 100 - p_list[i]
        if first_entity.shape == 'LINE':
            return get_split_line_points(p1, p2, gv.split_mode_by_percentage_list, p_list)
        else:
            return get_split_arc_points(first_entity, gv.split_mode_by_percentage_list, p_list)
    p_list = [p1]
    next_p = p1
    for i in range(len(connected_entities)):
        tmp_p_list = entities_p_list[i]
        e_index = connected_entities[i]
        entity = entity_list[e_index]
        is_left_to_right = entity.start.is_smaller_x_smaller_y(entity.end)
        change_order = False
        if entity.start.is_equal(next_p):
            next_p = entity.end
            p1_equal_start = True
            if not is_left_to_right:
                change_order = True
        else:
            next_p = entity.start
            p1_equal_start = False
            if is_left_to_right:
                change_order = True
        keep_last = False
        if p1_equal_start:
            if 100 in tmp_p_list:
                keep_last = True
                tmp_p_list.remove(100)
            if 0 in tmp_p_list:
                tmp_p_list.remove(0)
        else:
            if 0 in tmp_p_list:
                keep_last = True
                tmp_p_list.remove(0)
            if 100 in tmp_p_list:
                tmp_p_list.remove(100)
        if change_order:
            tmp_p_list.reverse()
            for j in range(len(tmp_p_list)):
                tmp_p_list[j] = 100 - tmp_p_list[j]
        if entity.shape == 'LINE':
            tmp_p_list = get_split_line_points(entity.start, entity.end, gv.split_mode_by_percentage_list, tmp_p_list)
        else:
            tmp_p_list = get_split_arc_points(entity, gv.split_mode_by_percentage_list, tmp_p_list)
        if not p1_equal_start:
            tmp_p_list.reverse()
        tmp_p_list.pop(0)
        if not keep_last:
            tmp_p_list.pop(-1)
        p_list += tmp_p_list
    p_list.append(p2)
    return p_list

