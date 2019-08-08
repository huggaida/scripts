
bl_info = {
    "name": "Pie Menu maiw",
    "description": "Pie's",
    "author": "Sergey Barabanov",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "location": "You need ti assign key maps",
    "warning": "",
    "wiki_url": "",
    "category": "Pie Menu"
    }

import bpy
from bpy.types import Menu

class VIEW3D_MT_origin_me_pie(Menu):
    bl_label = "Set Origin"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        obj = context.active_object
        mode = context.mode

        if obj :# and obj.type == 'MESH':
            # 4 - LEFT
            pie.operator("object.set_bottom_pivot", text="Origin to Bottom", icon='AXIS_TOP')
            # 6 - RIGHT
            pie.operator("object.origin_set", text="Geometry To Origin", icon='ORIENTATION_NORMAL').type = 'GEOMETRY_ORIGIN'
            # 2 - BOTTOM
            pie.operator("object.origin_set", text="Origin To 3D Cursor", icon='PIVOT_CURSOR').type = 'ORIGIN_CURSOR'
            # 8 - TOP
            pie.operator("object.origin_set", text="Origin To Geometry", icon='OBJECT_ORIGIN').type = 'ORIGIN_GEOMETRY'
            # 7 - TOP - LEFT
            pie.operator("object.origin_set", text="To Center of Mass (Surface)", icon='SURFACE_DATA').type = 'ORIGIN_CENTER_OF_MASS'
            # 9 - TOP - RIGHT
            pie.operator("object.origin_set", text="to Center of Mass (Volume)", icon='VOLUME').type = 'ORIGIN_CENTER_OF_VOLUME'



class VIEW3D_MT_origin_pie_BottomPivot(bpy.types.Operator):
    bl_label = "Set Origin to bottom"
    bl_idname = "object.set_bottom_pivot"

    def execute(self, context):
       
        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.context.scene.cursor_location[2] = 0
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        return {'FINISHED'}


class VIEW3D_MT_snap_me_pie(Menu):
    bl_label = "Snap"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
                
        pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Keep Offset)", icon='RESTRICT_SELECT_OFF').use_offset = True
        pie.operator("view3d.snap_cursor_to_center", text="Cursor to Center", icon='PIVOT_CURSOR')
        pie.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon='PIVOT_CURSOR')
        pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon='RESTRICT_SELECT_OFF').use_offset = False
        pie.operator("view3d.snap_selected_to_active", text="Selection to Active", icon='RESTRICT_SELECT_OFF')
        pie.operator("view3d.snap_cursor_to_active", text="Cursor to Active", icon='PIVOT_CURSOR')
        pie.operator("view3d.snap_selected_to_grid", text="Selection to Grid", icon='RESTRICT_SELECT_OFF')
        pie.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon='PIVOT_CURSOR')



class VIEW3D_MT_select_edit_mode(Menu):
    bl_label = "Select edit mode"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
                

        pie.operator("mesh.faces_select_linked_flat", text="Linked Flat",                    icon='NONE')
        pie.operator("mesh.select_non_manifold", text="Non Manifold", icon='NONE')
        pie.operator("mesh.select_linked", text="Linked", icon='NONE')
        pie.operator("mesh.select_all", text="Invert",                     icon='NONE').action = 'INVERT'
        pie.operator("mesh.select_loose", text="Loose",                     icon='NONE')
        pie.operator("mesh.select_nth", text="Checker", icon='NONE')
        pie.operator("mesh.loop_to_region", text="Inner-Region",                    icon='NONE')
        pie.operator("mesh.region_to_loop", text="Boundary Loop",                    icon='NONE') 


class VIEW3D_MT_pivot_pie_maiw(Menu):
    bl_label = "Pivot Point"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        obj = context.active_object
        mode = context.mode

        pie.separator()
        pie.separator()
        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='CURSOR')
        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='MEDIAN_POINT')
        if (obj is None) or (mode in {'OBJECT', 'POSE', 'WEIGHT_PAINT'}):
            pie.prop(context.scene.tool_settings, "use_transform_pivot_point_align", text="Only Origins")
        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='ACTIVE_ELEMENT')
        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='INDIVIDUAL_ORIGINS')
        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='BOUNDING_BOX_CENTER', text="B.Box Center")



class VIEW3D_MT_shading_ex_pie_maiw(Menu):
    bl_label = "Shading"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        view = context.space_data

        if (
                (context.mode == 'POSE') or
                ((context.mode == 'WEIGHT_PAINT') and (context.active_object.find_armature()))
        ):
            pie.prop(view.overlay, "show_xray_bone", icon='XRAY')
        else:
            xray_active = (
                (context.mode == 'EDIT_MESH') or
                (view.shading.type in {'SOLID', 'WIREFRAME'})
            )
            if xray_active:
                sub = pie
            else:
                sub = pie.row()
                sub.active = False
            sub.prop(
                view.shading,
                "show_xray_wireframe" if (view.shading.type == 'WIREFRAME') else "show_xray",
                text="Toggle X-Ray",
                icon='XRAY',
            )

        pie.prop_enum(view.shading, "type", value='SOLID')
        # Note this duplicates 'view3d.toggle_xray' logic, so we can see the active item: T58661.
        pie.prop_enum(view.shading, "type", value='WIREFRAME')
        pie.prop(view.overlay, "show_overlays", text="Overlays", icon='OVERLAY')


        pie.prop(view.shading, "show_backface_culling", text = "Backface Cull", icon='SNAP_FACE')
        pie.prop(view.overlay, "show_wireframes", text = "Wire Toggle", icon='CUBE')
        pie.prop_enum(view.shading, "type", value='MATERIAL')
        pie.prop_enum(view.shading, "type", value='RENDERED')



# Pie Delete - X
class VIEW3D_MT_Delete_maiw(Menu):
    bl_label = "Pie Delete"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("mesh.delete", text="Only Faces", icon='UV_FACESEL').type = 'ONLY_FACE'
        # 6 - RIGHT
        pie.operator("mesh.remove_doubles", text="Rem. Doubles", icon='STICKY_UVS_VERT')
        # 2 - BOTTOM
        pie.operator("mesh.dissolve_mode", text="Dissolve ", icon='SNAP_EDGE')
        # 8 - TOP
        pie.operator("mesh.delete", text="Delete Edges", icon='EDGESEL').type = 'EDGE'
        # pie.operator("mesh.dissolve_edges", text="Dissolve Edges", icon='SNAP_EDGE')
        # 7 - TOP - LEFT
        pie.operator("mesh.delete", text="Delete Vertices", icon='VERTEXSEL').type = 'VERT'
        # pie.operator("mesh.dissolve_verts", text="Dissolve Vertices", icon='SNAP_VERTEX')
        # 9 - TOP - RIGHT
        pie.operator("mesh.delete", text="Delete Faces", icon='FACESEL').type = 'FACE'
        # pie.operator("mesh.dissolve_faces", text="Dissolve Faces", icon='SNAP_FACE')
        # 1 - BOTTOM - LEFT
        # box.operator("mesh.dissolve_limited", text="Limited Dissolve", icon='STICKY_UVS_LOC')
        # box.operator("mesh.delete_edgeloop", text="Delete Edge Loops", icon='NONE')
        # box.operator("mesh.edge_collapse", text="Edge Collapse", icon='UV_EDGESEL')
        # # 3 - BOTTOM - RIGHT
        # box.operator("mesh.delete", text="Only Edge & Faces", icon='NONE').type = 'EDGE_FACE'



class VIEW3D_MT_Apply_maiw(Menu):
    bl_label = "Pie Apply Transforms"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("object.duplicates_make_real", text="Make Duplicates Real", icon="MOD_ARRAY")
        # 6 - RIGHT
        pie.operator("object.visual_transform_apply", text="Visual Transforms",icon="CONSTRAINT")
        # 2 - BOTTOM
        pie.operator("object.transforms_to_deltas", text="Location to Deltas", icon='MOD_PARTICLES').mode = 'LOC'
        # 8 - TOP
        pie.operator("object.transform_apply", text="Location", icon='ORIENTATION_GLOBAL').location = True
        # 7 - TOP - LEFT
        pie.operator("object.transform_apply", text="Rotation", icon='GROUP_VCOL').rotation = True
        # 9 - TOP - RIGHT
        pie.operator("object.transform_apply", text="Scale", icon='SHAPEKEY_DATA').scale = True
        # 1 - BOTTOM - LEFT
        pie.operator("object.transforms_to_deltas", text="Rotation to Deltas", icon='MOD_TINT').mode = 'ROT'
        # 3 - BOTTOM - RIGHT
        pie.operator("object.transforms_to_deltas", text="Scale to Deltas", icon='MOD_SOLIDIFY').mode = 'SCALE'
        # bpy.ops.object.transforms_to_deltas(mode='LOC')

class VIEW3D_MT_EdgesOperators_maiw(Menu):
    bl_label = "Pie Edge Transforms"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("mesh.set_edge_linear", text="Edge Linear") #, icon='')
        # 6 - RIGHT
        pie.operator("mesh.set_edge_flow", text="Edge Flow") #,icon="")
        # 2 - BOTTOM
        # pie.operator("mesh.extrude_faces_move", text="Individual") #, icon="")
        pie.operator("mesh.offset_edges", text="Offset") #, icon='')
        # 8 - TOP
        pie.operator("view3d.edit_mesh_extrude_move_shrink_fatten", text="Individual Normals") #, icon='')
        # 7 - TOP - LEFT
        # 9 - TOP - RIGHT
        # pie.operator("object.transform_apply", text="Scale", icon='SHAPEKEY_DATA').scale = True
        # # 1 - BOTTOM - LEFT
        # pie.operator("object.transforms_to_deltas", text="Rotation to Deltas", icon='MOD_TINT').mode = 'ROT'
        # # 3 - BOTTOM - RIGHT
        # pie.operator("object.transforms_to_deltas", text="Scale to Deltas", icon='MOD_SOLIDIFY').mode = 'SCALE'
        # # bpy.ops.object.transforms_to_deltas(mode='LOC')


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


classes = (
    VIEW3D_MT_origin_me_pie,
    VIEW3D_MT_origin_pie_BottomPivot,
    VIEW3D_MT_snap_me_pie,
    VIEW3D_MT_select_edit_mode,
    VIEW3D_MT_pivot_pie_maiw,
    VIEW3D_MT_shading_ex_pie_maiw,
    VIEW3D_MT_Delete_maiw,
    VIEW3D_MT_Apply_maiw,
    RemoveMeshElements,
    VIEW3D_MT_EdgesOperators_maiw,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
   

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
