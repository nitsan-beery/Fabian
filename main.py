from fabian_board import *

if __name__ == '__main__':
    b = FabianBoard(20)
    b.dxfDoc = ezdxf.readfile("./DXF files/DMS-6579.DXF")
    b.convert_doc_to_entity_list()
#    b.show_center()
    b.show_all_entities()
    b.window_main.mainloop()
