import math


def get_index_from_hash(hash_table, hash_index):
    return hash_table.get(str(hash_index))


def get_smallest_diff_angle(angle1, angle2):
    if angle2 < angle1:
        angle1, angle2 = angle2, angle1
    if angle2 - angle1 > 180:
        angle1 += 360
    return math.fabs(angle2 - angle1)


