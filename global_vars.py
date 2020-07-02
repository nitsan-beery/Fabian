import math

WINDOW_HEIGHT = 500
WINDOW_WIDTH = int(WINDOW_HEIGHT*4/3)
WINDWO_SIZE = str(WINDOW_WIDTH)+'x'+str(WINDOW_HEIGHT)
BOARD_HEIGHT = 10000
BOARD_WIDTH = int(BOARD_HEIGHT*4/3)

edge_line_mark_radius = 5
accuracy = 9

select_mode = 'edge'
board_bg_color = '#D1EDFF'
default_color = '#0099FF'
marked_entity_color = 'orange'
selected_item_color = '#FFFFcc'
temp_line_color = 'red'

class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

def get_distance_between_points(p1, p2):
    return math.sqrt(pow(p1.x-p2.x, 2) + pow(p1.y-p2.y, 2))


