import math


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









