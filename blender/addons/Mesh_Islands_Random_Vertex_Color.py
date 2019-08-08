bl_info = {
    "name": "Mesh Islands Random Vertex Color",
    "author": "batFINGER",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "F3 Search",
    "description": "Assign random greyscale vertex color to mesh islands",
    "warning": "",
    "wiki_url": "",
    "category": "Mesh"}

import bpy
import bmesh
from random import random
from bpy.props import StringProperty, BoolProperty
from mathutils import Vector


def walk_island(vert):
    ''' walk all un-tagged linked verts '''
    vert.tag = True
    yield (vert)
    linked_verts = [
        e.other_vert(vert) for e in vert.link_edges
        if not e.other_vert(vert).tag
    ]
    for v in linked_verts:
        if v.tag:
            continue
        yield from walk_island(v)


def get_islands(bm, verts=[]):
    def tag(verts, switch):
        for v in verts:
            v.tag = switch

    tag(bm.verts, True)
    tag(verts, False)
    ret = {"islands": []}
    verts = set(verts)
    while verts:
        v = verts.pop()
        verts.add(v)
        island = set(walk_island(v))
        faces = set(
            f for x in island for f in x.link_faces
            if all(v.tag for v in f.verts))
        edges = set(
            e for x in island for e in x.link_edges
            if all(v.tag for v in e.verts))
        ret["islands"].append(island.union(edges).union(faces))
        tag(island, False)  # remove tag = True
        verts -= island
    return ret


class BMIslands(list):
    def __init__(self, bm):
        self.extend(BMeshIsland(i, island) for i, island in enumerate(get_islands(bm, verts=bm.verts)["islands"]))
        self.sort(key=lambda i: (i.co.x, i.co.y))
        for i, island in enumerate(self):
            island.index = i


class BMeshIsland:
    def __init__(self, index, geom):
        self.index = index
        self.verts = [e for e in geom if isinstance(e, bmesh.types.BMVert)]
        self.co = sum([v.co for v in self.verts], Vector()) / len(self.verts)
        self.faces = [e for e in geom if isinstance(e, bmesh.types.BMFace)]


class MESH_OT_random_island_vertex_color(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "mesh.random_island_vert_color"
    bl_label = "Random Island Vert Color"
    bl_options = {'REGISTER', 'UNDO'}
    islands = None
    bm = None

    refresh: BoolProperty(name="Refresh")
    color_map: StringProperty(
        name="Color Map", default="vertcol")

    @classmethod
    def poll(cls, context):
        return(context.object
               and context.object.mode == 'OBJECT'
               and context.object.type == 'MESH')

    def main(self, ob):
        me = ob.data

        bm = bmesh.new()
        bm.from_mesh(me)
        self.bm = bm

        self.islands = BMIslands(bm)

    def randomize(self, ob):
        me = ob.data
        clayers = self.bm.loops.layers.color
        color_layer = clayers.get(self.color_map) or clayers.new(self.color_map)

        ami = ob.active_material_index
        for island in self.islands:
            r = random()
            for f in island.faces:
                f.material_index = ami
                for l in f.loops:
                    #l[color_layer] = (r, r, r, 1)
                    l[color_layer] = (r, ) * 4

        self.bm.to_mesh(me)
        me.update()

    def invoke(self, context, event):
        ob = context.object
        self.main(ob)
        return self.execute(context)

    def execute(self, context):
        self.randomize(context.object)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "color_map")

        row.prop(self, "refresh", text="", icon='FILE_REFRESH')
        layout.operator(self.__class__.bl_idname)


def register():
    bpy.utils.register_class(MESH_OT_random_island_vertex_color)


def unregister():
    bpy.utils.unregister_class(MESH_OT_random_island_vertex_color)


if __name__ == "__main__":
    register()