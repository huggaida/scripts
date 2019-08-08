import bpy


class SS_OT_loop_select(bpy.types.Operator):
    bl_idname = "ss.loop_select"
    bl_label = "Loop Select"
    bl_options = {'REGISTER', 'UNDO'}

    face = None

    extend = bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})
    deselect = bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        if not self.options.is_invoke:
            return {'CANCELLED'}

        return bpy.ops.mesh.loop_select(
            'INVOKE_DEFAULT',
            extend=self.extend,
            deselect=self.deselect, toggle=False)

    def invoke(self, context, event):
        return self.execute(context)
