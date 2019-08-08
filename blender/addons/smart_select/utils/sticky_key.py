import bpy


class StickyKey:
    invoke_mode = bpy.props.EnumProperty(
        items=(
            ('HOTKEY', "Hotkey", ""),
            ('RELEASE', "Release", ""),
            ('HOLD', "Hold", ""),
            ('TWEAK', "Tweak", ""),
        ),
        options={'HIDDEN', 'SKIP_SAVE'})

    active = False

    def key_is_pressed(self):
        return StickyKey.active

    def get_hold_timeout(self):
        return 200 / 1000

    def execute(self, context):
        return {'FINISHED'}

    def execute_release(self, context):
        return {'FINISHED'}

    def execute_hold(self, context):
        return {'FINISHED'}

    def execute_tweak(self, context):
        return {'FINISHED'}

    def modal(self, context, event):
        if event.value == 'RELEASE' and event.type == self.key:
            self.modal_end()
            return self.execute_release(context)

        elif event.type == 'MOUSEMOVE':
            tt = context.user_preferences.inputs.tweak_threshold
            if abs(self.mouse_x - event.mouse_x) > tt or \
                    abs(self.mouse_y - event.mouse_y) > tt:
                self.modal_end()
                return self.execute_tweak(context)

        elif event.type == 'TIMER' and self.timer:
            if self.timer.time_duration >= self.hold_timeout:
                self.modal_end()
                return self.execute_hold(context)

        return {'PASS_THROUGH'}

    def modal_begin(self):
        StickyKey.active = True
        self.hold_timeout = self.get_hold_timeout()
        wm = bpy.context.window_manager
        self.timer = wm.event_timer_add(0.05, bpy.context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal_end(self):
        StickyKey.active = False
        if self.timer:
            bpy.context.window_manager.event_timer_remove(self.timer)
            self.timer = None

    def invoke(self, context, event):
        if self.invoke_mode == 'RELEASE':
            return self.execute_release(context)

        elif self.invoke_mode == 'HOLD':
            return self.execute_hold(context)

        elif self.invoke_mode == 'TWEAK':
            return self.execute_tweak(context)

        elif self.invoke_mode == 'HOTKEY':
            if StickyKey.active:
                return {'CANCELLED'}

            self.mouse_x, self.mouse_y = event.mouse_x, event.mouse_y
            self.key = event.type
            return self.modal_begin()

        return {'CANCELLED'}
