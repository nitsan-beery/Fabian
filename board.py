import tkinter as tk
from tkinter import filedialog
import json
import global_vars as gv
from global_vars import Point


class Board:
    def __init__(self):
        self.window_main = tk.Tk()
        self.frame_1 = tk.Frame(self.window_main)
        self.frame_1.pack(fill='both', side='top', expand=tk.YES)
        self.frame_2 = tk.Frame(self.window_main)
        self.frame_2.pack(fill='both', side='bottom', expand=tk.NO, pady=5)

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

        self.button_load = tk.Button(self.frame_2, text='Load', command=lambda: self.load_data())
        self.button_save = tk.Button(self.frame_2, text='Save', command=lambda: self.save_data())
        self.button_load.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        self.button_save.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)

        self.window_main.geometry(gv.WINDWO_SIZE)
        self.board.xview_moveto((gv.BOARD_WIDTH-gv.WINDOW_WIDTH)/2/gv.BOARD_WIDTH)
        self.board.yview_moveto((gv.BOARD_HEIGHT-gv.WINDOW_HEIGHT)/2/gv.BOARD_HEIGHT)
        self.window_main.update()
        self.center = Point(int(gv.BOARD_WIDTH/2), int(gv.BOARD_HEIGHT/2))

        self.board.bind('<MouseWheel>', self.mouse_wheel)

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

    def get_data(self):
        return 1

    def save_data(self):
        default_file_name = f'Fabian'
        filename = filedialog.asksaveasfilename(parent=self.window_main, initialdir="./data_files/", title="Select file",
                                                initialfile=default_file_name, defaultextension=".json",
                                                filetypes=(("json files", "*.json"), ("all files", "*.*")))
        if filename == '':
            return
        data = self.get_data()
        with open(filename, "w") as json_file:
            json.dump(data, json_file)


