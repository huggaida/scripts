import bpy


class StackKey:

    def __init__(self, ops):
        self.ops = ops
        self._reset()

    def _reset(self):
        self.is_first = True
        self._index = 0
        self.state = None

    def index(self, n=2):
        return self._index % n

    def get_state(self):
        context = bpy.context
        atype = context.area and context.area.type or ""

        if atype == 'IMAGE_EDITOR':
            return (
                atype,
                context.mode,
                context.tool_settings.uv_select_mode if
                context.space_data.mode != 'PAINT' else None)

        elif atype == 'VIEW_3D':
            ao = context.active_object
            return (
                atype,
                context.mode,
                context.tool_settings.mesh_select_mode[:] if
                ao and ao.mode == 'EDIT' and ao.type == 'MESH' else None)

        else:
            return (atype,)

    def check_operator(self):
        lo = len(bpy.context.window_manager.operators) > 0 and \
            bpy.context.window_manager.operators[-1]
        return lo and lo.bl_idname in self.ops

    def check_state(self):
        return self.state is None or self.get_state() == self.state

    def update_state(self):
        self.state = self.get_state()

    def next(self):
        if self.check_operator() and self.check_state():
            self._index += 1
            self.is_first = False
        else:
            self._reset()
