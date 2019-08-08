
bl_info = {
    "name": "blend-max",
    "description": "FBX I/O Ctrl+C/V like",
    "author": "maiw",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "F3 search menu: max-to, max-from ",
    "category": "Import-Export"
}
from bpy.types import (
        Menu,
        Operator,
        )
from bpy.props import EnumProperty
import bpy, os
from os.path import expanduser

class Export_FBX_no_UI(bpy.types.Operator):
    bl_idname = "object.export_fbx_no_ui"
    bl_label = "Blend to max"

    def execute(self, context):
        bpy.ops.export_scene.fbx(filepath = "c:\\temp\\copybuffer.fbx", use_selection = True, use_mesh_modifiers = False)#, use_anim = False)
        return {'FINISHED'}


class Import_FBX_no_UI(bpy.types.Operator):
    bl_idname = "object.import_fbx_no_ui"
    bl_label = "Max to blend"

    def execute(self, context):
        # path_fbx = expanduser('~') + "\\AppData\\tmp\\copybuffer.fbx"
        path_fbx = "c:\\temp\\copybuffer.fbx"
        path_blend = "c:\\temp\\copybuffer.blend"
        # path_blend = expanduser('~') + "\\AppData\\tmp\\copybuffer.blend"
        if ( os.path.getmtime(path_blend) > os.path.getmtime(path_fbx) ):
            bpy.ops.view3d.pastebuffer()
        else:
            bpy.ops.import_scene.fbx(filepath = "c:\\temp\\copybuffer.fbx", use_anim = False, use_custom_normals=True)
     #       bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

# register
def register():
    
    bpy.utils.register_class(Export_FBX_no_UI)
    bpy.utils.register_class(Import_FBX_no_UI)
    
def unregister():
    bpy.utils.uregister_class(Export_FBX_no_UI)
    bpy.utils.uregister_class(Import_FBX_no_UI)

if __name__ == "__main__":
    register()
