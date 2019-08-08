import bpy
from math import pi
from ..addon import prefs
from ..utils import property_utils as pu


class SS_OT_redo_select(bpy.types.Operator):
    bl_idname = "ss.redo_select"
    bl_label = "Redo Select"
    bl_options = {'INTERNAL'}

    delta = bpy.props.IntProperty(options={'SKIP_SAVE'})
    mode = bpy.props.EnumProperty(
        items=(
            ('SHARPNESS', "Sharpness", ""),
            ('DELIMIT', "Delimit", ""),
        ),
        options={'SKIP_SAVE'}
    )

    def execute(self, context):
        pr = prefs()
        aop = context.active_operator
        if self.mode == 'SHARPNESS' and hasattr(aop, "sharpness"):
            aop.sharpness += pr.sharpness_step * self.delta
            aop.sharpness = max(0.017453, aop.sharpness)
            aop.sharpness = min(pi, aop.sharpness)
            bpy.ops.ss.draw(
                value="Smart Select\nAngle: %d°" %
                round(180 * aop.sharpness / pi))

            bpy.ops.ed.undo_redo(True)

        elif self.mode == 'DELIMIT' and hasattr(aop, "delimit"):
            item = pu.enum_item_next(
                aop, "delimit", aop.delimit, self.delta, False)
            bpy.ops.ss.draw(
                value="Delimit Mode:\n%s" % (item and item.name or "None"))
            bpy.ops.ed.undo_redo(True)

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        ao = context.active_object
        aop = context.active_operator
        return ao and ao.type == 'MESH' and ao.mode == 'EDIT' and \
            aop and aop.bl_idname in {
                "SS_OT_loop_select", "SS_OT_flat_select", "SS_OT_fill_select"}
