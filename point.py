import math
import global_vars as gv
from operator import itemgetter


class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def is_equal(self, p, accuracy=gv.accuracy):
        if p is None:
            return False
        min_d = math.pow(10, -accuracy) * gv.min_distance_between_nodes
        distance = math.sqrt(math.pow(self.x - p.x, 2) + math.pow(self.y - p.y, 2))
        # debug
        '''
        if distance < min_d:
            print(f"equal points ({p.x}, {p.y})  ({self.x}, {self.y})   distance: {distance}   min_d: {min_d}")
        '''
        return distance < min_d

    def is_smaller_x_smaller_y(self, p, by_x=True):
        if by_x:
            if self.x < p.x:
                return True
            elif self.x == p.x and self.y < p.y:
                return True
            return False
        else:
            if self.y < p.y:
                return True
            elif self.y == p.y and self.x < p.x:
                return True
            return False

    def is_smaller_x_bigger_y(self, p):
        if self.x < p.x:
            return True
        elif self.x == p.x and self.y > p.y:
            return True
        return False

    def is_smaller_y_bigger_x(self, p):
        if self.y < p.y:
            return True
        elif self.y == p.y and self.x > p.x:
            return True
        return False

    def convert_into_tuple(self):
        t = (self.x, self.y)
        return t

    def get_data_from_tuple(self, t):
        if len(t) < 2:
            print(f"tuple does not match Point type: {t}")
            return
        self.x = t[0]
        self.y = t[1]

    def get_distance_to_point(self, p):
        return math.sqrt(pow(self.x - p.x, 2) + pow(self.y - p.y, 2))

    # return the angle vector to Point p (degrees), None if p == self
    def get_alfa_to(self, p):
        if p is None or self.is_equal(p):
            return 0
        dx = p.x - self.x
        dy = p.y - self.y
        if dx == 0:
            if dy > 0:
                alfa = 90
            else:
                alfa = 270
        elif dy == 0:
            if dx > 0:
                alfa = 0
            else:
                alfa = 180
        else:
            alfa = math.atan(dy / dx) * 180 / math.pi
            if dx < 0:
                alfa += 180
            elif alfa < 0:
                alfa += 360
        return alfa

    def get_middle_point(self, p):
        mid_point = Point()
        mid_point.x = (self.x + p.x) / 2
        mid_point.y = (self.y + p.y) / 2
        return mid_point


# return new coordinates of Point p relative to Point new00 with rotation_angle
def get_shifted_point(p, new00, rotation_angle):
    shifted_p = Point(p.x - new00.x, p.y - new00.y)
    point_zero = Point(0, 0)
    if shifted_p.is_equal(point_zero):
        return point_zero
    r = shifted_p.get_distance_to_point(point_zero)
    alfa = point_zero.get_alfa_to(shifted_p) + rotation_angle
    alfa = alfa * math.pi / 180
    shifted_p.x = math.cos(alfa) * r
    shifted_p.y = math.sin(alfa) * r
    return shifted_p


# if sort by x return left --> right points. if left == right return bottom --> up
# else: return bottom --> up. if bottom == up return left --> right
def get_sorted_points(p1, p2, sort_by_x=True):
    if p1.x == p2.x and p1.y == p2.y:
        return p1, p2
    if sort_by_x:
        if p1.x > p2.x:
            return p2, p1
        elif p1.x < p2.x:
            return p1, p2
        else:
            if p1.y < p2.y:
                return p1, p2
            else:
                return p2, p1
    else:
        if p1.y > p2.y:
            return p2, p1
        elif p1.y < p2.y:
            return p1, p2
        else:
            if p1.x < p2.x:
                return p1, p2
            else:
                return p2, p1


def sort_list_point_by_distance_from_p(point_list, p):
    sorted_list = []
    d_list = []
    for point in point_list:
        d = point.get_distance_to_point(p)
        d_list.append((point, d))
    d_list = sorted(d_list, key=itemgetter(1))
    for item in d_list:
        sorted_list.append(item[0])
    return sorted_list
