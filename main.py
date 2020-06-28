from fabian_board import *

if __name__ == '__main__':
    b = FabianBoard(10)
    b.dxfDoc = ezdxf.readfile("./DXF files/DMS-6579.DXF")
    b.convert_doc_to_entity_list()
    e = b.entity_list[0]
    e.start = Point(0, 0)
    e.end = Point(5, -1)
    p = Point(6, 0)
    d = b.get_distance_from_entity(p, 0)
#    b.show_entity(0)
    print(f'start: ({e.start.x}, {e.start.y})   end: ({e.end.x}, {e.end.y})   d: {d}')
#    b.window_main.mainloop()
