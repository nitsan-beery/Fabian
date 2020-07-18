import math
import global_vars as gv


class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def is_equal(self, p):
        if p == None:
            return False
        return round(self.x, gv.accuracy) == round(p.x, gv.accuracy) and \
               round(self.y, gv.accuracy) == round(p.y, gv.accuracy)

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
            print(f"tuple doesn't match Point type: {t}")
            return
        self.x = t[0]
        self.y = t[1]

    def get_distance_to_point(self, p):
        return math.sqrt(pow(self.x-p.x, 2) + pow(self.y-p.y, 2))

    # return the angle vector to Point p (degrees), None if p == self
    def get_alfa_to(self, p):
        if self.is_equal(p):
            return None
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

# return new coordinates of Point p relative to Point new00 with rotation_angle
def get_shifted_point(p, new00, rotation_angle):
    shifted_p = Point(p.x - new00.x, p.y - new00.y)
    r = shifted_p.get_distance_to_point(Point(0, 0))
    if r == 0:
        return shifted_p
    alfa = Point(0, 0).get_alfa_to(shifted_p) + rotation_angle
    alfa = alfa*math.pi/180
    shifted_p.x = math.cos(alfa)*r
    shifted_p.y = math.sin(alfa)*r
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

