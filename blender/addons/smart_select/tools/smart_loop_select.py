import bpy
from mesh_looptools import (
    get_connected_selections,
    edgekey,
)
from ..addon import prefs
from ..utils.stack_key import StackKey
from ..utils import bmesh_utils as bmu


class SS_OT_smart_loop_select(bpy.types.Operator):
    bl_idname = "ss.smart_loop_select"
    bl_label = "Smart Loop Select"
    bl_options = {'INTERNAL'}

    face = None
    edge = None

    extend = bpy.props.BoolProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        return {'CANCELLED'}

    def invoke(self, context, event):
        me = context.edit_object.data
        bm = bmu.validate_bm(me)
        msm = context.tool_settings.mesh_select_mode[:]
        with bmu.sel(bm, me):
            with bmu.msm(False, False, True, True):
                face = bmu.get_face(
                    bm, event.mouse_region_x, event.mouse_region_y)
            with bmu.msm(False, True, False, True):
                edge = bmu.get_edge(
                    bm, event.mouse_region_x, event.mouse_region_y)

        if not edge or not face:
            return {'CANCELLED'}

        self.__class__.face = face.index
        self.__class__.edge = edge.index
        stack_key.next()
        if not stack_key.is_first:
            with bmu.msm(*msm, uog=True):
                bpy.ops.ed.undo()

        bm = bmu.validate_bm(me, bm)
        deselect = self.extend and (
            bm.faces[self.face].select if msm[2] else
            bm.edges[self.edge].select)
        index = stack_key.index()
        if index == 0:
            with bmu.uog(True):
                bpy.ops.ss.loop_select(
                    'INVOKE_DEFAULT', True,
                    extend=self.extend and not deselect,
                    deselect=deselect)
        elif index == 1:
            bpy.ops.ss.flat_select(
                'INVOKE_DEFAULT', True,
                extend=self.extend and not deselect,
                deselect=deselect,
                index=self.face)

        stack_key.update_state()
        return {'FINISHED'}


class MeshStackKey(StackKey):

    def __init__(self, cl, ops):
        self.cl = cl
        StackKey.__init__(self, ops)

    def get_state(self):
        state = StackKey.get_state(self)
        state += (self.cl.edge,)
        return state


stack_key = MeshStackKey(
    SS_OT_smart_loop_select,
    {"SS_OT_flat_select", "SS_OT_loop_select"})
