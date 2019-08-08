import bpy
from bpy.props import StringProperty
from bl_ui.space_toolsystem_common import ToolSelectPanelHelper


class CallDecalPie(bpy.types.Operator):
    bl_idname = "machin3.call_decal_pie"
    bl_label = "MACHIN3: Call Decal Pie"
    bl_options = {'REGISTER', 'UNDO'}

    idname: StringProperty()

    def invoke(self, context, event):
        current_tool = ToolSelectPanelHelper._tool_get_active(context, 'VIEW_3D', None)[0][0]

        if current_tool == 'BoxCutter':
            return {'PASS_THROUGH'}

        else:
            context.window_manager.decal_mousepos = (event.mouse_region_x, event.mouse_region_y)

            bpy.ops.wm.call_menu_pie(name='MACHIN3_MT_%s' % (self.idname))
            return {'FINISHED'}
