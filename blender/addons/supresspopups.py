# for http://blender.stackexchange.com/questions/61546/how-do-i-turn-off-confirmation-dialogues

bl_info = {
    "name": "Suppress popups",
    "description": "Suppress delete, parent & mesh mode popup ",
    "author": "maiw",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "3D View",
    "category": "3D View"
}
from bpy.types import (
        Menu,
        Operator,
        )
from bpy.props import EnumProperty
import bpy, os
from os.path import expanduser
# from pie_align_menu import AlignSelectedXYZ
# operators
class RemoveObject(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.remove_object"
    bl_label = "Remove the selected Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.delete()
        return {'FINISHED'}

class CopyApplayShrinkwrap(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.copy_applay_shrinkwrap"
    bl_label = "Copy and then Applay Shrinkwrap modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.modifier_copy(modifier="Shrinkwrap")
        bpy.ops.object.modifier_move_up(modifier="Shrinkwrap.001")
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Shrinkwrap.001")
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}

class SplitViewHorizontal(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "area.split_view_horizontal"
    bl_label = "Split Area Horizontal"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.area.type = 'VIEW_3D'
        orig_width = bpy.context.area.width 
        bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.5)
        return {'FINISHED'}

class SplitViewVertical(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "area.split_view_vertical"
    bl_label = "Split Area Vertical"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.area.type = 'VIEW_3D'
        orig_width = bpy.context.area.width 
        bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
        return {'FINISHED'}
                         

class RemoveMeshElements(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.remove_mesh_elements"
    bl_label = "Remove the selected Face/Edge/Vertex"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.object
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[0]:
            bpy.ops.mesh.delete(type="VERT")
        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[1]:
            bpy.ops.mesh.delete(type="EDGE")
        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[2]:
            bpy.ops.mesh.delete(type="FACE")

        return {'FINISHED'}


# Align to X, Y, Z
class AlignSelectedXYZ(Operator):
    bl_idname = "align.selected2xyz"
    bl_label = "Align to X, Y, Z"
    bl_description = "Align Selected Along the chosen axis"
    bl_options = {'REGISTER', 'UNDO'}

    axis = EnumProperty(
        name="Axis",
        items=[
            ('X', "X", "X Axis"),
            ('Y', "Y", "Y Axis"),
            ('Z', "Z", "Z Axis")
            ],
        description="Choose an axis for alignment",
        default='X'
        )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def execute(self, context):
        values = {
            'X': [(0, 1, 1), (True, False, False)],
            'Y': [(1, 0, 1), (False, True, False)],
            'Z': [(1, 1, 0), (False, False, True)]
            }
        chosen_value = values[self.axis][0]
        constraint_value = values[self.axis][1]
        for vert in bpy.context.object.data.vertices:
            bpy.ops.transform.resize(
                    value=chosen_value, constraint_axis=constraint_value,
                    constraint_orientation='GLOBAL',
                    mirror=False, proportional='DISABLED',
                    proportional_edit_falloff='SMOOTH',
                    proportional_size=1
                    )
        return {'FINISHED'}

class MAlignX(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.malignx"
    bl_label = "Align X"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.object
        bpy.ops.align.selected2xyz(axis='X')
        return {'FINISHED'}

class MAlignY(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.maligny"
    bl_label = "Align Y"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.object
        bpy.ops.align.selected2xyz(axis='Y')
        return {'FINISHED'}

class MAlignZ(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.malignz"
    bl_label = "Align Z"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.object
        bpy.ops.align.selected2xyz(axis='Z')
        return {'FINISHED'}

class MeshElementsBackwards(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.mesh_elements_backwards"
    bl_label = "Mesh Select Mode Cycle backwards"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.object

        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[0]:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            return {'FINISHED'}
        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[1]:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            return {'FINISHED'}
        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[2]:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            return {'FINISHED'}

        return {'FINISHED'}

class MeshElementsUV(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.mesh_elements_uv"
    bl_label = "Mesh Select Mode Cycle Forward"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.object

        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[0] and  context.tool_settings.use_uv_select_sync:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            return {'FINISHED'}
        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[1] and  context.tool_settings.use_uv_select_sync:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            return {'FINISHED'}
        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[2] and  context.tool_settings.use_uv_select_sync:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            return {'FINISHED'}
        
        if ob and ob.type == 'MESH' and bpy.context.scene.tool_settings.uv_select_mode == "VERTEX" and not context.tool_settings.use_uv_select_sync:
            bpy.context.scene.tool_settings.uv_select_mode = 'EDGE'
            return {'FINISHED'}
        if ob and ob.type == 'MESH' and context.scene.tool_settings.uv_select_mode == 'EDGE' and not context.tool_settings.use_uv_select_sync:
            bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
            return {'FINISHED'}
        if ob and ob.type == 'MESH' and context.scene.tool_settings.uv_select_mode=='FACE' and not context.tool_settings.use_uv_select_sync:
            bpy.context.scene.tool_settings.uv_select_mode = 'ISLAND'
            return {'FINISHED'}
        if ob and ob.type == 'MESH' and context.scene.tool_settings.uv_select_mode=='ISLAND' and not context.tool_settings.use_uv_select_sync:
            bpy.context.scene.tool_settings.uv_select_mode = 'VERTEX'
            return {'FINISHED'}
        return {'FINISHED'}

class MeshElements3DView(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.mesh_elements_3dview"
    bl_label = "Mesh Select Mode Cycle Forward"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.object

        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[0]:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            return {'FINISHED'}
        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[1]:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            return {'FINISHED'}
        if ob and ob.type == 'MESH' and context.scene.tool_settings.mesh_select_mode[2]:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            return {'FINISHED'}
        
        return {'FINISHED'}

class MeshElements3DViewToggle(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.mesh_elements_3dview_toggle"
    bl_label = "Mesh Select Mode Cycle Forward Toggle"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.object

        if ob and ob.type == 'MESH':
            context.scene.tool_settings.mesh_select_mode[0] = not (context.scene.tool_settings.mesh_select_mode[0])
            context.scene.tool_settings.mesh_select_mode[1] = not (context.scene.tool_settings.mesh_select_mode[1])
            context.scene.tool_settings.mesh_select_mode[2] = not (context.scene.tool_settings.mesh_select_mode[2])
            return {'FINISHED'}
        
        return {'FINISHED'}

# operators
class SetParentToObject(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.set_parent_object"
    bl_label = "Set Parent to Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.parent_set(type="OBJECT")
        return {'FINISHED'}

class SetParentKeepTransform(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.set_parent_keep"
    bl_label = "Set Parent to Object (Keep Transform)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)
        return {'FINISHED'}


class Export_FBX_no_UI(bpy.types.Operator):
    bl_idname = "object.export_fbx_no_ui"
    bl_label = ""

    def execute(self, context):
        #bpy.ops.view3d.copybuffer()
        #bpy.ops.export_scene.fbx(filepath = os.path.dirname(bpy.data.filepath)+ "\\tmp.fbx", use_selection = True, use_mesh_modifiers = False)
        #bpy.ops.export_scene.fbx(filepath = expanduser('~') + "\\AppData\\tmp\\copybuffer.fbx", use_selection = True, use_mesh_modifiers = False, use_anim = False)
        bpy.ops.export_scene.fbx(filepath = expanduser('~') + "\\AppData\\tmp\\copybuffer.fbx", use_selection = True, use_mesh_modifiers = False, use_anim = False)
      
        
        return {'FINISHED'}


class Import_FBX_no_UI(bpy.types.Operator):
    bl_idname = "object.import_fbx_no_ui"
    bl_label = ""

    def execute(self, context):
        path_fbx = expanduser('~') + "\\AppData\\tmp\\copybuffer.fbx"
        path_blend = expanduser('~') + "\\AppData\\tmp\\copybuffer.blend"
        if ( os.path.getmtime(path_blend) > os.path.getmtime(path_fbx) ):
            bpy.ops.view3d.pastebuffer()
        else:
            bpy.ops.import_scene.fbx(filepath = expanduser('~') + "\\AppData\\tmp\\copybuffer.fbx", use_anim = False, use_custom_normals=True)
        #bpy.ops.import_scene.fbx(filepath = expanduser('~') + "\\AppData\\tmp\\tmp.fbx")
        #bpy.ops.import_scene.fbx(filepath = os.path.dirname(bpy.data.filepath)+ "\\tmp.fbx")
            bpy.ops.object.mode_set(mode='OBJECT')
           
        return {'FINISHED'}



class Add_Shrinkwrap(bpy.types.Operator):
    bl_idname = "object.add_shrinkwrap"
    bl_label = "Add a shrinkwrap modifier with target selected"

    def execute(self, context):
        lst = bpy.context.selected_objects
        act = bpy.context.active_object
        lst.remove(act)
        scn = lst[0]
        bpy.context.scene.objects.active = scn
        bpy.ops.object.modifier_add(type = 'SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].use_keep_above_surface = True
        bpy.context.object.modifiers["Shrinkwrap"].target = act
        bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True
           
        return {'FINISHED'}


class Add_Subsurf(bpy.types.Operator):
    bl_idname = "object.add_subsurf"
    bl_label = "Toggle a subsurf modifier"

    def execute(self, context):
        obj = context.object
        for modifier in obj.modifiers:
            if modifier.type == "SUBSURF":
                obj.modifiers["Subsurf"].levels = int (not obj.modifiers["Subsurf"].levels)

        if not obj.modifiers or not any([m for m in obj.modifiers if m.type == "SUBSURF"]):
            subsurf = obj.modifiers.new(name='Subsurf', type='SUBSURF')
            subsurf.levels = 1
            subsurf.show_on_cage = True
        
        return {'FINISHED'}

# Check object for modifiers
# import bpy
# obj = bpy.context.object
# if not obj.modifiers:
#     print ("no modifiers")
# else:
#     print ("object has modifier(s)")
# Check object for specific modifiers
# import bpy
# obj = bpy.context.object
# for modifier in obj.modifiers:
#     if modifier.type == "SUBSURF":
#         print ("subsurf")

# print(0 < len([m for m in bpy.context.object.modifiers if m.type == "SUBSURF"]))
# print(any([m for m in bpy.context.object.modifiers if m.type == "SUBSURF"]))

# addon_keymaps = []
# Adding the Modifier if it isn't present
# import bpy
# obj = bpy.context.active_object
# subsurf = obj.modifiers.new(name='MySubSurf', type='SUBSURF')
# subsurf.levels = 2
# subsurf.render_levels = 3
# [‘DATA_TRANSFER’, ‘MESH_CACHE’, ‘MESH_SEQUENCE_CACHE’, ‘NORMAL_EDIT’, ‘UV_PROJECT’, ‘UV_WARP’, ‘VERTEX_WEIGHT_EDIT’, ‘VERTEX_WEIGHT_MIX’, ‘VERTEX_WEIGHT_PROXIMITY’, ‘ARRAY’, ‘BEVEL’, ‘BOOLEAN’, ‘BUILD’, ‘DECIMATE’, ‘EDGE_SPLIT’, ‘MASK’, ‘MIRROR’, ‘MULTIRES’, ‘REMESH’, ‘SCREW’, ‘SKIN’, ‘SOLIDIFY’, ‘SUBSURF’, ‘TRIANGULATE’, ‘WIREFRAME’, ‘ARMATURE’, ‘CAST’, ‘CORRECTIVE_SMOOTH’, ‘CURVE’, ‘DISPLACE’, ‘HOOK’, ‘LAPLACIANSMOOTH’, ‘LAPLACIANDEFORM’, ‘LATTICE’, ‘MESH_DEFORM’, ‘SHRINKWRAP’, ‘SIMPLE_DEFORM’, ‘SMOOTH’, ‘WARP’, ‘WAVE’, ‘CLOTH’, ‘COLLISION’, ‘DYNAMIC_PAINT’, ‘EXPLODE’, ‘FLUID_SIMULATION’, ‘OCEAN’, ‘PARTICLE_INSTANCE’, ‘PARTICLE_SYSTEM’, ‘SMOKE’, ‘SOFT_BODY’, ‘SURFACE’], default ‘DATA_TRANSFER’, (readonly)
addon_keymaps = []
# register
def register():
    bpy.utils.register_class(Add_Shrinkwrap)
    bpy.utils.register_class(SplitViewHorizontal)
    bpy.utils.register_class(SplitViewVertical)
    bpy.utils.register_class(CopyApplayShrinkwrap)
    bpy.utils.register_class(SetParentToObject)
    bpy.utils.register_class(SetParentKeepTransform)
    bpy.utils.register_class(RemoveObject)
    bpy.utils.register_class(RemoveMeshElements)
    bpy.utils.register_class(MeshElementsUV)
    bpy.utils.register_class(MeshElements3DView)
    bpy.utils.register_class(MeshElements3DViewToggle)
    bpy.utils.register_class(MeshElementsBackwards)
    bpy.utils.register_class(Export_FBX_no_UI)
    bpy.utils.register_class(Import_FBX_no_UI)
    bpy.utils.register_class(Add_Subsurf)
    bpy.utils.register_class(MAlignX)
    bpy.utils.register_class(MAlignY)
    bpy.utils.register_class(MAlignZ)
    bpy.utils.register_class(AlignSelectedXYZ)

    # handle the keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new(SetParentToObject.bl_idname, type='P', value='PRESS', shift=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(SetParentKeepTransform.bl_idname, type='P', value='PRESS', alt=True, shift=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(RemoveObject.bl_idname, type='X', value='PRESS')
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(Import_FBX_no_UI.bl_idname, type='V', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(Export_FBX_no_UI.bl_idname, type='X', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(Add_Shrinkwrap.bl_idname, 'F2', value='PRESS')
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(Add_Subsurf.bl_idname, 'F1', 'PRESS')
        addon_keymaps.append((km, kmi))
        
        km = wm.keyconfigs.addon.keymaps.new(name='Mesh')
        kmi = km.keymap_items.new(RemoveMeshElements.bl_idname, type='X', value='RELEASE')
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new(MAlignX.bl_idname, type='X', value='PRESS', ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new(MAlignY.bl_idname, type='Y', value='PRESS', ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(MAlignZ.bl_idname, type='Z', value='PRESS', ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(MeshElements3DView.bl_idname, 'LEFTMOUSE', 'PRESS')
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(Add_Subsurf.bl_idname, 'F1', 'PRESS')
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(CopyApplayShrinkwrap.bl_idname, type='A', value='PRESS', ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='UV Editor')
        kmi = km.keymap_items.new(MeshElementsUV.bl_idname, 'LEFTMOUSE', 'PRESS')
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(Add_Shrinkwrap)
    bpy.utils.unregister_class(SplitViewHorizontal)
    bpy.utils.unregister_class(SplitViewVertical)
    bpy.utils.unregister_class(SetParentToObject)
    bpy.utils.unregister_class(SetParentKeepTransform)
    bpy.utils.unregister_class(RemoveObject)
    bpy.utils.unregister_class(RemoveMeshElements)
    bpy.utils.unregister_class(MeshElements3DView)
    bpy.utils.unregister_class(MeshElements3DViewToggle)
    bpy.utils.unregister_class(MeshElementsUV)
    bpy.utils.unregister_class(MAlignX)
    bpy.utils.unregister_class(MAlignY)
    bpy.utils.unregister_class(MAlignZ)
    bpy.utils.unegister_class(MeshElementsBackwards)
    bpy.utils.uregister_class(CopyApplayShrinkwrap)
    bpy.utils.uregister_class(Export_FBX_no_UI)
    bpy.utils.uregister_class(Import_FBX_no_UI)
    bpy.utils.uregister_class(Add_Subsurf)



if __name__ == "__main__":
    register()
