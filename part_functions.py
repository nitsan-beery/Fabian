from point import *


# return index of node in node_list with same p, None if can't find
def get_hash_index_of_node_with_point(node_list, p):
    for i in range(len(node_list)):
        node = node_list[i]
        if node.p.is_equal(p):
            return node.hash_index
    return None

