import bpy
from ..addon import prefs
from ..constants import DELIMIT_ITEMS
from ..utils import bmesh_utils as bmu


class SS_OT_flat_select(bpy.types.Operator):
    bl_idname = "ss.flat_select"
    bl_label = "Flat Select"
    bl_options = {'REGISTER', 'UNDO'}

    index = bpy.props.IntProperty(default=-1, options={'HIDDEN', 'SKIP_SAVE'})
    extend = bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})
    deselect = bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})
    sharpness = bpy.props.FloatProperty(
        name="Sharpness", description="Sharpness",
        subtype='ANGLE',
        default=0, min=0, soft_min=0.017453, max=3.141593,
        step=100, options={'SKIP_SAVE'})
    delimit = bpy.props.EnumProperty(
        name="Delimit",
        description="Delimit selected region",
        items=DELIMIT_ITEMS,
        default=set(),
        options={'ENUM_FLAG', 'SKIP_SAVE'})

    def execute(self, context):
        if not self.options.is_invoke:
            return {'CANCELLED'}

        context.tool_settings.mesh_select_mode = self.msm
        self.bm = bmu.validate_bm(context.edit_object.data, self.bm)

        if self.delimit:
            bpy.ops.mesh.select_all(action='DESELECT')
            with bmu.msm(False, False, True, True):
                self.bm.faces[self.index].select_set(True)
                bpy.ops.mesh.select_linked(delimit=self.delimit)
                self.mask = {f.index for f in self.bm.faces if f.select}
        else:
            self.mask.clear()

        bpy.ops.mesh.select_all(action='DESELECT')
        with bmu.msm(False, False, True, True):
            self.bm.faces[self.index].select_set(True)
            bpy.ops.mesh.faces_select_linked_flat(sharpness=self.sharpness)

        if self.delimit:
            for f in self.bm.faces:
                if f.select and f.index not in self.mask:
                    f.select_set(False)

        if not self.msm[2]:
            with bmu.msm(False, True, False, True):
                bpy.ops.mesh.region_to_loop()

        if self.deselect:
            flat_selection = bmu.select_to_tuple(self.bm)
            bmu.tuple_to_select(self.bm, self.selection, op="set")
            bmu.tuple_to_select(self.bm, flat_selection, op="sub")
        elif self.extend:
            bmu.tuple_to_select(self.bm, self.selection, op="add")

        self.bm.select_flush_mode()

        return {'FINISHED'}

    def invoke(self, context, event):
        self.sharpness = prefs().sharpness
        me = context.edit_object.data
        self.bm = bmu.validate_bm(me)
        self.msm = context.tool_settings.mesh_select_mode[:]
        self.selection = bmu.select_to_tuple(self.bm)
        self.mask = set()

        if self.index == -1:
            with bmu.sel(self.bm, me), bmu.msm(False, False, True, True):
                face = bmu.get_face(
                    self.bm, event.mouse_region_x, event.mouse_region_y)

            if not face:
                return {'CANCELLED'}

            self.index = face.index

        return self.execute(context)

    @classmethod
    def poll(cls, context):
        ao = context.active_object
        return ao and ao.type == 'MESH' and ao.mode == 'EDIT'
