import bpy
from ..addon import prefs
from ..utils.sticky_key import StickyKey

DELIMIT_ITEMS = (
    ('NORMAL', "Normal", ""),
    ('MATERIAL', "Material", ""),
    ('SEAM', "Seam", ""),
    ('SHARP', "Sharp", ""),
    ('UV', "UVs", ""),
)


class SS_OT_smart_select(StickyKey, bpy.types.Operator):
    bl_idname = "ss.smart_select"
    bl_label = "Smart Select"
    bl_description = "Smart select"
    bl_options = {'INTERNAL'}

    toggle = bpy.props.BoolProperty(name="Toggle", options={'SKIP_SAVE'})
    redo = bpy.props.IntProperty(options={'HIDDEN', 'SKIP_SAVE'})
    redo_mode = bpy.props.EnumProperty(
        items=(
            ('SHARPNESS', "Sharpness", ""),
            ('DELIMIT', "Delimit", ""),
        ),
        options={'SKIP_SAVE'}
    )
    force_tool = bpy.props.EnumProperty(
        items=(
            ('NONE', "None", ""),
            ('FILL', "Fill", ""),
        ),
        options={'SKIP_SAVE'}
    )
    invoke_mode = bpy.props.EnumProperty(
        items=(
            ('HOTKEY', "Hotkey", ""),
            ('RELEASE', "Release", ""),
            ('HOLD', "Hold", ""),
        ))
    delimit = bpy.props.EnumProperty(
        items=DELIMIT_ITEMS,
        default=set(),
        options={'ENUM_FLAG', 'SKIP_SAVE'})

    def get_hold_timeout(self):
        return prefs().hold_timeout / 1000

    def execute_release(self, context):
        bpy.ops.ss.smart_loop_select(
            'INVOKE_DEFAULT', True, extend=self.toggle)
        return {'FINISHED'}

    def execute_hold(self, context):
        bpy.ops.ss.fill_select('INVOKE_DEFAULT', True)
        return {'FINISHED'}

    def execute_tweak(self, context):
        bpy.ops.ss.quick_select(
            'INVOKE_DEFAULT', True,
            extend=self.toggle, x=self.x, y=self.y)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.x, self.y = event.mouse_region_x, event.mouse_region_y
        return StickyKey.invoke(self, context, event)

    @classmethod
    def poll(cls, context):
        ao = context.active_object
        return ao and ao.type == 'MESH' and ao.mode == 'EDIT'
