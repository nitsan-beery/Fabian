from point import *
from fabian_classes import *


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
            if e is not None:
                entity_list.append(e)
    return entity_list

