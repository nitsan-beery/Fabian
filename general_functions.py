from fabian_classes import *
from point import *


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
    if split_mode == gv.split_mode_2_parts_percentage_side_by_reference_point:
        percentage_left = split_arg[0]
        reference_point = split_arg[1]
        d1 = p1.get_distance_to_point(reference_point)
        d2 = p2.get_distance_to_point(reference_point)
        if d2 < d1:
            split_arg[0] = 100 - percentage_left
        split_mode = gv.split_mode_2_parts_percentage_left
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
    return point_list


def get_split_arc_points(arc, split_mode=gv.split_mode_evenly_n_parts, split_arg=gv.default_split_parts):
    point_list = [arc.start]
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
    start_angle = arc.arc_start_angle
    for p in p_list:
        end_angle = arc.arc_start_angle + diff_angle * p / 100
        new_arc = Entity(shape=arc.shape, center=arc.center, radius=arc.radius, start_angle=start_angle,
                         end_angle=end_angle)
        point_list.append(new_arc.end)
        start_angle = end_angle
    point_list.append(arc.end)
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
    # if mode is split_mode_2_parts_percentage_side_by_reference_point, check for valid point
    if split_mode == gv.split_mode_2_parts_percentage_side_by_reference_point:
        if not isinstance(split_arg, tuple):
            split_mode = gv.split_mode_2_parts_percentage_left
        elif len(split_arg) < 2:
            split_mode = gv.split_mode_2_parts_percentage_left
        elif split_arg[1] is None:
            split_arg = split_arg[0]
            split_mode = gv.split_mode_2_parts_percentage_left
        elif not isinstance(split_arg[1], Point):
            split_arg = split_arg[0]
            split_mode = gv.split_mode_2_parts_percentage_left
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
        sum = left + right
        residual = left - right
        chunk = math.ceil(diff / sum)
        bulk = 100 / chunk
        add_on = (bulk - sum) / 2
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
    return p_list
