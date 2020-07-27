import tkinter as tk
from tkinter import filedialog
import json
import global_vars as gv
from point import *


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

            self.button_load = tk.Button(self.frame_2, text='Load', command=lambda: self.load_json())
            self.button_save = tk.Button(self.frame_2, text='Save', command=lambda: self.save_json())
            self.button_load.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
            self.button_save.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)

        self.window_main.geometry(gv.WINDWO_SIZE)
        self.window_main.update()
        # center of canvas
        self.center = Point(int(gv.BOARD_WIDTH/2), int(gv.BOARD_HEIGHT/2))
        self.set_screen_position(self.center.x, self.center.y)

        self.scale = 1
        self.text_on_screen = None

        self.board.bind('<MouseWheel>', self.mouse_wheel)
        self.window_main.bind('<Key>', self.key)


    # scroll view to x, y in canvas coordinates
    def set_screen_position(self, x, y):
        self.board.xview_moveto((x-self.board.winfo_width()/2)/gv.BOARD_WIDTH)
        self.board.yview_moveto((y-self.board.winfo_height()/2)/gv.BOARD_HEIGHT)

    # return x, y of screen center in canvas coordinates
    def get_screen_position(self):
        x = self.board.canvasx(self.board.winfo_width()/2)
        y = self.board.canvasy(self.board.winfo_height()/2)
        return x, y

    # return center window position (key.x, key.y coordinates)
    def get_center_keyx_keyy(self):
        x = self.board.winfo_width()/2
        y = self.board.winfo_height()/2
        return x, y

    # convert window events key.x key.y to x, y
    def convert_keyx_keyy_to_xy(self, keyx, keyy):
        canvas_x = self.board.canvasx(keyx)
        canvas_y = self.board.canvasy(keyy)
        x = (canvas_x - self.center.x)/self.scale
        y = (self.center.y - canvas_y)/self.scale
        return x, y

    # convert x, y to canvas coordinates
    def convert_xy_to_screen(self, x, y):
        x = self.center.x + x*self.scale
        y = self.center.y - y*self.scale
        return x, y

    # show text on screen 'center' or left-top (lt) or left-bottom (lb)
    def show_text_on_screen(self, text, fix_position='center', color=gv.text_color):
        x, y = self.get_screen_position()
        justify = tk.CENTER
        if fix_position == 'lb':
            x = x - self.board.winfo_width()/2 + 50
            y = y + self.board.winfo_height()/2 - 30
            justify = tk.RIGHT
        elif fix_position == 'lt':
            x = x - self.board.winfo_width()/2 + 50
            y = y - self.board.winfo_height()/2 + 15
            justify = tk.RIGHT
        if self.text_on_screen is not None:
            self.board.delete(self.text_on_screen)
        self.text_on_screen = self.board.create_text(x, y, text=text, fill=color, justify=justify)

    def hide_text_on_screen(self):
        if self.text_on_screen is not None:
            self.board.delete(self.text_on_screen)
            self.text_on_screen = None

    #create line between Points() p1 and p2 with xy coordinates
    def draw_line(self, p1, p2, color=gv.default_color):
        x1, y1 = self.convert_xy_to_screen(p1.x, p1.y)
        x2, y2 = self.convert_xy_to_screen(p2.x, p2.y)
        return self.board.create_line(x1, y1, x2, y2, fill=color)

    #create circle center = Point(x, y)
    def draw_circle(self, center, radius, outline_color=gv.default_color):
        xLeft, yTop = self.convert_xy_to_screen(center.x-radius, center.y+radius)
        xRight, yBottom = self.convert_xy_to_screen(center.x+radius, center.y-radius)
        return self.board.create_oval(xLeft, yTop, xRight, yBottom, outline=outline_color)

    #create circle center = Point(x, y)
    def draw_square(self, center, length, outline_color=gv.default_color):
        xLeft = center.x-length/2
        xRight = center.x+length/2
        yTop = center.y+length/2
        yBottom = center.y-length/2
        p1 = Point(xLeft, yTop)
        p2 = Point(xRight, yTop)
        p3 = Point(xRight, yBottom)
        p4 = Point(xLeft, yBottom)
        return self.draw_polygon([p1, p2, p3, p4], fill_color='', outline=outline_color)

    #create arc center = Point(x, y)
    def draw_arc(self, center, radius, start_angle, end_angle, outline_color=gv.default_color):
        xLeft, yTop = self.convert_xy_to_screen(center.x-radius, center.y+radius)
        xRight, yBottom = self.convert_xy_to_screen(center.x+radius, center.y-radius)
        return self.board.create_arc(xLeft, yTop, xRight, yBottom, start=start_angle, extent=(end_angle-start_angle),
                              style=tk.ARC, outline=outline_color)

    #create polygon out of Point(x, y) list
    def draw_polygon(self, point_list, fill_color=gv.element_color, outline=gv.default_color):
        xy_list = []
        for p in point_list:
            x, y = self.convert_xy_to_screen(p.x, p.y)
            xy_list.append(x)
            xy_list.append(y)
        return self.board.create_polygon(xy_list, fill=fill_color, outline=outline)

    def show_center(self):
        p1 = Point(-15, 0)
        p2 = Point(15, 0)
        self.create_line(p1, p2)
        p1 = Point(0, 15)
        p2 = Point(0, -15)
        self.create_line(p1, p2)

    def mouse_wheel(self, key):
        self.hide_text_on_screen()
        if key.delta < 0:
            i = '1'
        else:
            i = '-1'
        self.board.yview('scroll', i, 'units')

    def key(self, key):
        self.hide_text_on_screen()
        if key.keycode == 37:
            self.board.xview('scroll', -1, 'units')
        elif key.keycode == 39:
            self.board.xview('scroll', 1, 'units')
        elif key.keycode == 38:
            self.board.yview('scroll', -1, 'units')
        elif key.keycode == 40:
            self.board.yview('scroll', 1, 'units')

    def load_json(self, filename=None, my_dir="./data files/"):
        if filename is None:
            filename = filedialog.askopenfilename(parent=self.window_main, initialdir=my_dir, title="Select file",
                                                       filetypes=(("json files", "*.json"), ("all files", "*.*")))
            if filename == '':
                return
        with open(filename, "r") as json_file:
            data = json.load(json_file)
        return data

    def save_json(self, data=None, my_dir="./data files/", file_name='Fabian'):
        filename = filedialog.asksaveasfilename(parent=self.window_main, initialdir=my_dir, title="Select file",
                                                initialfile=file_name, defaultextension=".json",
                                                filetypes=(("json files", "*.json"), ("all files", "*.*")))
        if filename == '' or data is None:
            return None
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=2, separators=(",", ":"))
        return filename

