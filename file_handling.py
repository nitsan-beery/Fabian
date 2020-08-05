from fabian_classes import *
from tkinter import filedialog
import json
import ezdxf


def load_json(parent, filename=None, my_dir="./data files/"):
    if filename is None:
        filename = filedialog.askopenfilename(parent=parent, initialdir=my_dir, title="Select file",
                                              filetypes=(("json files", "*.json"), ("all files", "*.*")))
        if filename == '':
            return
    with open(filename, "r") as json_file:
        data = json.load(json_file)
    return data


def save_json(parent, data=None, my_dir="./data files/", file_name='Fabian'):
    filename = filedialog.asksaveasfilename(parent=parent, initialdir=my_dir, title="Select file",
                                            initialfile=file_name, defaultextension=".json",
                                            filetypes=(("json files", "*.json"), ("all files", "*.*")))
    if filename == '' or data is None:
        return None
    with open(filename, "w") as json_file:
        json.dump(data, json_file, indent=2, separators=(",", ":"))
    return filename


def convert_doc_to_entity_list(doc=None):
    entity_list = []
    if doc is None:
        return entity_list
    msp = doc.modelspace()
    for shape in shapes:
        for dxf_entity in msp.query(shape):
            e = None
            if shape == 'LINE':
                p1 = Point(dxf_entity.dxf.start[0], dxf_entity.dxf.start[1])
                p2 = Point(dxf_entity.dxf.end[0], dxf_entity.dxf.end[1])
                e = Entity(shape='LINE', start=p1, end=p2)
            elif shape == 'CIRCLE':
                center = Point(dxf_entity.dxf.center[0], dxf_entity.dxf.center[1])
                radius = dxf_entity.dxf.radius
                e = Entity(shape='CIRCLE', center=center, radius=radius)
            elif shape == 'ARC':
                center = Point(dxf_entity.dxf.center[0], dxf_entity.dxf.center[1])
                radius = dxf_entity.dxf.radius
                start_angle = dxf_entity.dxf.start_angle % 360
                end_angle = dxf_entity.dxf.end_angle
                e = Entity(shape='ARC', center=center, radius=radius, start_angle=start_angle, end_angle=end_angle)
            else:
                print(f"unknown shape '{shape}' in DXF file")
            if e is not None:
                entity_list.append(e)
    return entity_list


def save_inp(parent, file_name, node_list, element_list):
    filename = filedialog.asksaveasfilename(parent=parent, initialdir="./data files/", title="Select file",
                                            initialfile=file_name, defaultextension=".inp",
                                            filetypes=(("inp files", "*.inp"), ("all files", "*.*")))
    if filename == '':
        return
    f = open(filename, 'w')
    f.write('*Node\n')
    for i in range(1, len(node_list)):
        n = node_list[i]
        s = f'{i},    {n.p.x}, {n.p.y}, 0\n'
        f.write(s)
    element_3_list = []
    element_4_list = []
    for i in range(len(element_list)):
        e = element_list[i]
        if len(e.nodes) == 3:
            element_3_list.append(e.nodes)
        else:
            element_4_list.append(e.nodes)
    element_index = 1
    if len(element_3_list) > 0:
        f.write('*Element, type=R3D3\n')
        for i in range(len(element_3_list)):
            e = element_3_list[i]
            write_element_to_file(f, element_index, e)
            element_index += 1
    if len(element_4_list) > 0:
        f.write('*Element, type=R3D4\n')
        for i in range(len(element_4_list)):
            e = element_4_list[i]
            write_element_to_file(f, element_index, e)
            element_index += 1
    f.close()


def write_element_to_file(f, index, e):
    s = f'{index},    '
    for j in range(len(e)-1):
        s += f'{e[j]}, '
    s += f'{e[-1]}\n'
    f.write(s)


def save_data(parent, file_name, state):
    winfo_geometry = parent.winfo_geometry()
    data = {
        "entity_list": state.entity_list,
        "node_list": state.node_list,
        "next_node_hash_index": state.next_node_hash_index,
        "nodes_hash": state.nodes_hash,
        "net_line_list": state.net_line_list,
        "element_list": state.element_list,
        "corner_list": state.corner_list,
        "inp_nets": state.inp_nets,
        "mouse_select_mode": state.mouse_select_mode,
        "work_mode": state.work_mode,
        "select_parts_mode": state.select_parts_mode,
        "show_entities": state.show_entities,
        "show_nodes": state.show_nodes,
        "show_elements": state.show_elements,
        "show_node_number": state.show_node_number,
        "show_net": state.show_net,
        "show_corners": state.show_corners,
        "show_inps": state.show_inps,
        "scale": state.scale,
        "winfo_geometry": winfo_geometry
    }
    # debug
    # self.print_node_list()
    # self.print_line_list()
    filename = save_json(parent, data, file_name=file_name)
    if filename is not None:
        i = filename.rfind('/')
        title = filename[i+1:]
        parent.title(title)


def save_dxf(parent, file_name, entity_list):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    for e in entity_list:
        if e.shape == 'LINE':
            msp.add_line((e.start.x, e.start.y), (e.end.x, e.end.y))
        elif e.shape == 'ARC':
            msp.add_arc((e.center.x, e.center.y), e.radius, e.arc_start_angle, e.arc_end_angle)
        elif e.shape == 'CIRCLE':
            msp.add_circle((e.center.x, e.center.y), e.radius)
    filename = filedialog.asksaveasfilename(parent=parent, initialdir="./data files/", title="Select file",
                                            initialfile=file_name, defaultextension=".dxf",
                                            filetypes=(("dxf files", "*.dxf"), ("all files", "*.*")))
    if filename == '':
        return
    i = filename.rfind('/')
    title = filename[i+1:]
    parent.title(title)
    doc.saveas(filename)


def load(parent):
    filename = filedialog.askopenfilename(parent=parent, initialdir="./data files/", title="Select file",
                                          filetypes=(("Json files", "*.json"), ("DXF files", "*.dxf"),
                                                     ("INP files", "*.inp"), ("all files", "*.*")))
    if filename == '':
        return None, None
    arg = None
    i = filename.rfind('.')
    filetype = filename[i+1:].lower()
    i = filename.rfind('/')
    title = filename[i+1:]
    if filetype != 'inp':
        parent.title(title)
    if filetype == 'dxf':
        doc = ezdxf.readfile(filename)
        entity_list = convert_doc_to_entity_list(doc)
        print(f'\n{len(entity_list)} Entities in {filetype} file')
        arg = entity_list
    elif filetype == 'json':
        print('\nnew data file')
        data = load_json(parent, filename)
        state = FabianState()
        state.entity_list = data.get("entity_list")
        state.node_list = data.get("node_list")
        state.next_node_hash_index = data.get("next_node_hash_index")
        state.nodes_hash = data.get("nodes_hash")
        state.net_line_list = data.get("net_line_list")
        state.element_list = data.get("element_list")
        state.corner_list = data.get("corner_list")
        state.inp_nets = data.get("inp_nets")
        state.mouse_select_mode = data.get("mouse_select_mode")
        state.work_mode = data.get("work_mode")
        state.select_parts_mode = data.get("select_parts_mode")
        state.show_entities = data.get("show_entities")
        state.show_nodes = data.get("show_nodes")
        state.show_elements = data.get("show_elements")
        state.show_node_number = data.get("show_node_number")
        state.show_net = data.get("show_net")
        state.show_corners = data.get("show_corners")
        state.show_inps = data.get("show_inps")
        state.scale = data.get("scale")
        winfo_geometry = data.get("winfo_geometry")
        parent.geometry(winfo_geometry)
        arg = state
    elif filetype == 'inp':
        f = open(filename, 'r')
        node_list = []
        element_list = []
        line = ''
        while line.lower() != '*node':
            line = f.readline().strip('\n')
        while line is not None:
            line = f.readline().strip('\n')
            if line[:8].lower() == '*element':
                break
            words = line.split(',')
            x = float(words[1])
            y = float(words[2])
            p = Point(x, y)
            node = Node(p)
            node_list.append(node)
        while line != '':
            line = f.readline().strip('\n')
            words = line.split(',')
            if len(words) < 4:
                continue
            words.pop(0)
            n = len(words)
            element = Element()
            for i in range(n):
                node = int(words[i])
                element.nodes.append(node)
            element_list.append(element)
        f.close()
        arg = (node_list, element_list)

    return filetype, arg
