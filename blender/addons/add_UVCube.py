bl_info = {
    "name": "UVCube",
    "author": "maiw",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > UVCube",
    "description": "Adds a new cube with different materials modifications for habdy UV Editing",
    "warning": "",
    "wiki_url": "",
    "category": "Add Mesh",
}


import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty
import os, sys


class OBJECT_OT_add_UVCube(Operator):
    """Create a new Mesh UVCube"""
    bl_idname = "mesh.add_uvcube"
    bl_label = "UVCube"
    bl_options = {'REGISTER', 'UNDO'}

    
    def execute(self, context):
        path = "C:\\Users\\maiw\\Scripts\\blender\\addons\\add_UVCube.blend\\Object\\"
        object_name = "UVCube"
        bpy.ops.wm.append(filename=object_name, directory=path)
        return {'FINISHED'}

def draw_item(self, context):
    layout = self.layout
 #   layout.operator(OBJECT_OT_add_UVCube.bl_idname)
    layout.operator("mesh.add_uvcube")


def register():
    bpy.utils.register_class(OBJECT_OT_add_UVCube)

    # lets add ourselves to the main header
    bpy.types.VIEW3D_MT_mesh_add.append(draw_item)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_UVCube)

    bpy.types.INFO_HT_header.remove(draw_item)


if __name__ == "__main__":
    register()
