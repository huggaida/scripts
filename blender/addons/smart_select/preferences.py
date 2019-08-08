import bpy
from .utils.hotkeys import hotkeys, Hotkey
from .addon import ADDON_ID, prefs
from .tools.smart_select import SS_OT_smart_select
from .tools.redo_select import SS_OT_redo_select


class Overlay(bpy.types.PropertyGroup):
    overlay = bpy.props.BoolProperty(
        name="Overlay",
        description="Display the angle value as overlay text in your viewport",
        default=True)
    operator = bpy.props.BoolProperty(name="Operator Name", default=True)
    prop = bpy.props.BoolProperty(name="Property Name", default=True)
    size = bpy.props.IntProperty(
        name="Size", description="Overlay size",
        default=24, min=10, max=50, options={'SKIP_SAVE'})
    color = bpy.props.FloatVectorProperty(
        name="Color", description="Overlay color",
        default=(1, 1, 1, 1), subtype='COLOR', size=4, min=0, max=1)
    alignment = bpy.props.EnumProperty(
        name="Alignment",
        items=(
            ('TOP', "Top", ""),
            ('TOP_LEFT', "Top Left", ""),
            ('TOP_RIGHT', "Top Right", ""),
            ('BOTTOM', "Bottom", ""),
            ('BOTTOM_LEFT', "Bottom Left", ""),
            ('BOTTOM_RIGHT', "Bottom Right", ""),
        ),
        default='TOP')
    duration = bpy.props.FloatProperty(
        name="Duration", subtype='TIME', min=1, max=10, default=3, step=10)
    offset = bpy.props.IntProperty(
        name="Offset", subtype='PIXEL', default=10, min=0)
    shadow = bpy.props.BoolProperty(name="Shadow", default=True)


class SSPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    hotkey = bpy.props.PointerProperty(type=Hotkey)
    hotkey_toggle = bpy.props.PointerProperty(type=Hotkey)
    hotkey_wheel1 = bpy.props.PointerProperty(type=Hotkey)
    hotkey_wheel2 = bpy.props.PointerProperty(type=Hotkey)
    sharpness = bpy.props.FloatProperty(
        name="Default Sharpness", description="",
        subtype='ANGLE',
        default=20 * 0.017453, min=0.017453, max=3.141593)
    sharpness_step = bpy.props.FloatProperty(
        name="Sharpness Step", description="",
        subtype='ANGLE',
        default=5 * 0.017453, min=0, soft_min=0.017453, max=45 * 0.017453,
        step=100)
    overlay = bpy.props.PointerProperty(type=Overlay)
    hold_timeout = bpy.props.IntProperty(
        name="Hold Timeout", description="Hold timeout (ms)",
        default=200, min=100, max=1000, step=10)

    def draw(self, context):
        layout = self.layout

        column = layout.column(True)
        row = column.row(True)
        self.hotkey.draw(row, context, label="Smart Select Hotkey")
        self.hotkey_toggle.draw(
            row, context, label="Toggle Selection Hotkey")

        row = column.row(True)
        self.hotkey_wheel1.draw(row, context, label="Change Angle Hotkey")
        self.hotkey_wheel2.draw(
            row, context, label="Change Delimit Mode Hotkey")

        row = column.row(True)
        col = row.box()
        col.label("Sharpness")
        col = col.column(True)
        col.prop(self, "sharpness")
        col.prop(self, "sharpness_step")

        col = row.box()
        col.label("Duration and Distance")
        col = col.column(True)
        col.prop(self, "hold_timeout")
        col.prop(context.user_preferences.inputs, "tweak_threshold")

        box = column.box()
        row = box.row()
        col = row.column(True)
        col.prop(self.overlay, "overlay")

        if self.overlay.overlay:
            col.prop(self.overlay, "shadow")
            col.prop(self.overlay, "size")
            col.prop(self.overlay, "duration")

            row.separator()
            row.separator()
            col = row.column(True)

            col.prop(self.overlay, "color")
            col.label("Alignment:")
            col.prop(self.overlay, "alignment", "")
            col.prop(self.overlay, "offset")

        row = column.row(True)
        row.scale_y = 1.5
        row.operator(
            "wm.url_open", "Other Jimmy's addons",
            icon='SOLO_ON').url = "https://gumroad.com/handpaintedtextures"
        row.operator(
            "wm.url_open", "Other roaoao's addons",
            icon='SOLO_ON').url = "https://gumroad.com/roaoao"


def register():
    pr = prefs()
    hk = pr.hotkey
    hkt = pr.hotkey_toggle
    hkw1 = pr.hotkey_wheel1
    hkw2 = pr.hotkey_wheel2

    if hk.key == 'NONE':
        hk.key = 'SELECTMOUSE'
        hk.alt = True
        hk.value = 'PRESS'

        hkt.key = 'SELECTMOUSE'
        hkt.alt = True
        hkt.shift = True
        hkt.value = 'PRESS'

        hkw1.key = 'WHEELUPMOUSE'
        hkw1.ctrl = True
        hkw1.scroll = True
        hkw1.value = 'PRESS'

        hkw2.key = 'WHEELUPMOUSE'
        hkw2.shift = True
        hkw2.scroll = True
        hkw2.value = 'PRESS'

    hotkeys.keymap("Mesh")
    hk.add_kmi(hotkeys.add(
        SS_OT_smart_select,
        hk.key, hk.ctrl, hk.shift, hk.alt, hk.oskey, hk.key_mod, hk.value,
        invoke_mode='HOTKEY',
        toggle=False))
    hkt.add_kmi(hotkeys.add(
        SS_OT_smart_select,
        hkt.key, hkt.ctrl, hkt.shift, hkt.alt, hkt.oskey, hkt.key_mod,
        hkt.value,
        invoke_mode='HOTKEY',
        toggle=True))

    hkw1.add_kmi(hotkeys.add(
        SS_OT_redo_select, 'WHEELUPMOUSE',
        hkw1.ctrl, hkw1.shift, hkw1.alt, hkw1.oskey, hkw1.key_mod, hkw1.value,
        delta=1, mode='SHARPNESS'))
    hkw1.add_kmi(hotkeys.add(
        SS_OT_redo_select, 'WHEELDOWNMOUSE',
        hkw1.ctrl, hkw1.shift, hkw1.alt, hkw1.oskey, hkw1.key_mod, hkw1.value,
        delta=-1, mode='SHARPNESS'))

    hkw2.add_kmi(hotkeys.add(
        SS_OT_redo_select, 'WHEELUPMOUSE',
        hkw2.ctrl, hkw2.shift, hkw2.alt, hkw2.oskey, hkw2.key_mod, hkw2.value,
        delta=1, mode='DELIMIT'))
    hkw2.add_kmi(hotkeys.add(
        SS_OT_redo_select, 'WHEELDOWNMOUSE',
        hkw2.ctrl, hkw2.shift, hkw2.alt, hkw2.oskey, hkw2.key_mod, hkw2.value,
        delta=-1, mode='DELIMIT'))
