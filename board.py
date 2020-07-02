import tkinter as tk
from tkinter import filedialog
import json
import global_vars as gv
from global_vars import Point


class Board:
    def __init__(self, with_frame_2=False):
        self.window_main = tk.Tk()
        self.frame_1 = tk.Frame(self.window_main)
        self.frame_1.pack(fill='both', side='top', expand=tk.YES)

        self.board = tk.Canvas(self.frame_1, width=gv.WINDOW_WIDTH, height=gv.WINDOW_HEIGHT)
        self.board.pack(expand=tk.YES, fill=tk.BOTH)
        self.yscrollbar = tk.Scrollbar(self.board, orient=tk.VERTICAL)
        self.xscrollbar = tk.Scrollbar(self.board, orient=tk.HORIZONTAL)
        self.yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.board.config(yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set,
                          scrollregion=(0, 0, gv.BOARD_WIDTH, gv.BOARD_HEIGHT))
        self.yscrollbar.config(command=self.board.yview, repeatdelay=0, repeatinterval=0)
        self.xscrollbar.config(command=self.board.xview, repeatdelay=0, repeatinterval=0)

        if with_frame_2:
            self.frame_2 = tk.Frame(self.window_main)
            self.frame_2.pack(fill='both', side='bottom', expand=tk.NO, pady=5)

            self.button_load = tk.Button(self.frame_2, text='Load', command=lambda: self.load_data())
            self.button_save = tk.Button(self.frame_2, text='Save', command=lambda: self.save_data())
            self.button_load.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
            self.button_save.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)

        self.window_main.geometry(gv.WINDWO_SIZE)
        self.window_main.update()
        self.center = Point(int(gv.BOARD_WIDTH/2), int(gv.BOARD_HEIGHT/2))
        self.set_screen_position(self.center.x, self.center.y)
#        self.board.xview_moveto((gv.BOARD_WIDTH-gv.WINDOW_WIDTH)/2/gv.BOARD_WIDTH)
#        self.board.yview_moveto((gv.BOARD_HEIGHT-gv.WINDOW_HEIGHT)/2/gv.BOARD_HEIGHT)

        self.scale = 1

        self.board.bind('<MouseWheel>', self.mouse_wheel)

    # scroll view to the center of (x, y) in canvas coordinates
    def set_screen_position(self, x, y):
        self.board.xview_moveto((x-self.board.winfo_width()/2)/gv.BOARD_WIDTH)
        self.board.yview_moveto((y-self.board.winfo_height()/2)/gv.BOARD_HEIGHT)

    def mouse_wheel(self, key):
        if key.delta < 0:
            i = '1'
        else:
            i = '-1'
        self.board.yview('scroll', i, 'units')

    def load_data(self):
        filename = filedialog.askopenfilename(parent=self.window_main, initialdir="./data_files/", title="Select file",
                                                   filetypes=(("json files", "*.json"), ("all files", "*.*")))
        if filename == '':
            return
        with open(filename, "r") as json_file:
            data = json.load(json_file)
        return data

    def save_data(self, data=None, file_name='Fabian'):
        default_file_name = file_name
        filename = filedialog.asksaveasfilename(parent=self.window_main, initialdir="./data_files/", title="Select file",
                                                initialfile=default_file_name, defaultextension=".json",
                                                filetypes=(("json files", "*.json"), ("all files", "*.*")))
        if filename == '' or data is None:
            return
        with open(filename, "w") as json_file:
            json.dump(data, json_file)

    # convert screen points (key.x, key.y) to x, y
    def convert_screen_to_xy(self, keyx, keyy):
        canvas_x = self.board.canvasx(keyx)
        canvas_y = self.board.canvasy(keyy)
        x = (canvas_x - self.center.x)/self.scale
        y = (self.center.y - canvas_y)/self.scale
        return x, y

    def convert_xy_to_screen(self, x, y):
        x = self.center.x + x*self.scale
        y = self.center.y - y*self.scale
        return x, y

    def show_center(self):
        p1 = Point(-15, 0)
        p2 = Point(15, 0)
        self.create_line(p1, p2)
        p1 = Point(0, 15)
        p2 = Point(0, -15)
        self.create_line(p1, p2)

    #create line between Points() p1 and p2 with xy coordinates
    def create_line(self, p1, p2, color=gv.default_color):
        x1, y1 = self.convert_xy_to_screen(p1.x, p1.y)
        x2, y2 = self.convert_xy_to_screen(p2.x, p2.y)
        return self.board.create_line(x1, y1, x2, y2, fill=color)

    #create circle with xy coordinates
    def create_circle(self, center, radius, outline_color=gv.default_color):
        xLeft, yTop = self.convert_xy_to_screen(center.x-radius, center.y+radius)
        xRight, yBottom = self.convert_xy_to_screen(center.x+radius, center.y-radius)
        return self.board.create_oval(xLeft, yTop, xRight, yBottom, outline=outline_color)

    #create arc with xy coordinates
    def create_arc(self, center, radius, start_angle, end_angle, outline_color=gv.default_color):
        xLeft, yTop = self.convert_xy_to_screen(center.x-radius, center.y+radius)
        xRight, yBottom = self.convert_xy_to_screen(center.x+radius, center.y-radius)
        return self.board.create_arc(xLeft, yTop, xRight, yBottom, start=start_angle, extent=(end_angle-start_angle),
                              style=tk.ARC, outline=outline_color)


