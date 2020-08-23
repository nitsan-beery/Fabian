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
        m = f'unexpected number of border lines in set_node_expected_elements_and_exceptions node {n}  outer: {num_outer_lines}   inner: {num_inner_lines}'
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


