import bpy
import bmesh
from itertools import chain


def get_elem(bm, x, y):
    for e in chain(bm.verts, bm.edges, bm.faces):
        e.tag = e.select

    ret = bpy.ops.view3d.select(extend=True, location=(x, y))
    if 'FINISHED' not in ret:
        return None

    elem = len(bm.select_history) and bm.select_history[-1] or None

    if elem and not elem.tag:
        elem.select_set(False)
        bm.select_history.remove(elem)
        bm.select_flush_mode()

    return elem


class SS_OT_quick_select(bpy.types.Operator):
    bl_idname = "ss.quick_select"
    bl_label = "Quick Select"
    bl_description = "Quick select"
    bl_options = {'REGISTER', 'UNDO'}

    extend = bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})
    x = bpy.props.IntProperty(default=-1, options={'HIDDEN', 'SKIP_SAVE'})
    y = bpy.props.IntProperty(default=-1, options={'HIDDEN', 'SKIP_SAVE'})

    def select(self, x, y):
        d = max(abs(self.x - x), abs(self.y - y))
        if d == 0:
            return

        for i in range(d + 1):
            loc = (
                self.x + round(i * (x - self.x) / d),
                self.y + round(i * (y - self.y) / d)
            )
            if self.prev_loc == loc:
                continue
            self.prev_loc = loc
            bpy.ops.view3d.select(
                extend=self.extend and not self.deselect,
                deselect=self.deselect, toggle=False,
                center=False, enumerate=False, object=False,
                location=loc)

            self.extend = True

        self.x = x
        self.y = y

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            if context.area.type == 'VIEW_3D':
                self.select(event.mouse_region_x, event.mouse_region_y)

        elif event.value == 'RELEASE':
            return {'FINISHED'}

        elif event.value == 'PRESS':
            if event.type in {'ESC', 'RIGHTMOUSE'}:
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.x == -1 and self.y == -1:
            self.x = event.mouse_region_x
            self.y = event.mouse_region_y

        bm = bmesh.from_edit_mesh(context.edit_object.data)
        elem = get_elem(bm, self.x, self.y)
        if not elem:
            return {'CANCELLED'}

        self.deselect = elem.select
        self.prev_loc = None
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        ao = context.active_object
        return ao and ao.type == 'MESH' and ao.mode == 'EDIT'
