import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
)
from .property_utils import DynamicPropertyGroup

KMI_MAP_TYPES = ('KEYBOARD', 'MOUSE', 'TWEAK', 'NDOF', 'TEXTINPUT', 'TIMER')
key_items = [
    (i.identifier, i.name, "", i.value)
    for k, i in bpy.types.Event.bl_rna.properties["type"].enum_items.items()
]
value_items = [
    (i.identifier, i.name, "", i.value)
    for k, i in bpy.types.KeyMapItem.bl_rna.properties[
        "value"].enum_items.items()
]


class Hotkey(DynamicPropertyGroup, bpy.types.PropertyGroup):
    def _hotkey_update(self, context):
        if hasattr(self, "kmis"):
            for kmi in self.kmis:
                self.to_kmi(kmi)

        if hasattr(self, "update"):
            try:
                self.update(self, context)
            except:
                pass

    label = BoolProperty(
        description="Label", get=lambda s: False, set=lambda s, v: None)
    key = EnumProperty(
        items=key_items, description="Key pressed", update=_hotkey_update)
    scroll = BoolProperty()
    ctrl = BoolProperty(
        description="Ctrl key pressed", update=_hotkey_update)
    shift = BoolProperty(
        description="Shift key pressed", update=_hotkey_update)
    alt = BoolProperty(
        description="Alt key pressed", update=_hotkey_update)
    oskey = BoolProperty(
        description="Operating system key pressed", update=_hotkey_update)
    key_mod = EnumProperty(
        items=key_items,
        description="Regular key pressed as a modifier",
        update=_hotkey_update)
    value = EnumProperty(
        items=value_items,
        update=_hotkey_update)

    def add_kmi(self, kmi):
        if not hasattr(self, "kmis"):
            self.kmis = []

        self.kmis.append(kmi)

    def draw(
            self, layout, context,
            ctrl=True, shift=True, alt=True, oskey=True, key_mod=True,
            value=True, label=None):
        box = layout.box()
        if label:
            box.label(label)
        col = box.column(True)

        if not self.scroll:
            row = col.row(True)
            row.prop(self, "key", "", event=True)
            if value:
                row.prop(self, "value", "")
        else:
            row = col.row(True)
            row.enabled = False
            # row.operator("pme.none", "Mouse Wheel Up/Down")
            row.prop(self, "label", "Mouse Wheel Up/Down", toggle=True)

        row = col.row(True)
        if ctrl:
            row.prop(self, "ctrl", "Ctrl", toggle=True)
        if shift:
            row.prop(self, "shift", "Shift", toggle=True)
        if alt:
            row.prop(self, "alt", "Alt", toggle=True)
        if oskey:
            row.prop(self, "oskey", "OSKey", toggle=True)
        if key_mod:
            row.prop(self, "key_mod", "", event=True)

    def from_kmi(
            self, kmi,
            key=None, ctrl=None, shift=None, alt=None, oskey=None,
            key_mod=None, value=None):
        self.key = kmi.type if key is None else key
        self.value = kmi.value if value is None else value
        self.ctrl = kmi.ctrl if ctrl is None else ctrl
        self.shift = kmi.shift if shift is None else shift
        self.alt = kmi.alt if alt is None else alt
        self.oskey = kmi.oskey if oskey is None else oskey
        self.key_mod = kmi.key_modifier if key_mod is None else key_mod

    def to_kmi(
            self, kmi,
            key=None, ctrl=None, shift=None, alt=None, oskey=None,
            key_mod=None, value=None):

        if not self.scroll:
            for map_type in KMI_MAP_TYPES:
                try:
                    kmi.type = self.key if key is None else key
                    break
                except TypeError:
                    kmi.map_type = map_type

            kmi.value = self.value if value is None else value

        kmi.ctrl = self.ctrl if ctrl is None else ctrl
        kmi.shift = self.shift if shift is None else shift
        kmi.alt = self.alt if alt is None else alt
        kmi.oskey = self.oskey if oskey is None else oskey
        kmi.key_modifier = self.key_mod if key_mod is None else key_mod

    def update(self, context):
        pass


class Hotkeys:

    @staticmethod
    def get_instance():
        if hasattr(Hotkeys, "_instance"):
            Hotkeys._instance.clear()

        Hotkeys._instance = Hotkeys()
        return Hotkeys._instance

    def __init__(self):
        self.items = {}
        self.km = None

    def keymap(self, name="Window", space_type='EMPTY', region_type='WINDOW'):
        self.km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            name, space_type, region_type)

    def add(
            self, bl_class,
            key, ctrl=False, shift=False, alt=False, oskey=False,
            key_mod='NONE', value='PRESS', **props):

        item = self.km.keymap_items.new(
            bl_class.bl_idname, key, value,
            ctrl=ctrl, shift=shift, alt=alt, oskey=oskey, key_modifier=key_mod)

        if props:
            for p in props.keys():
                setattr(item.properties, p, props[p])

        if self.km.name not in self.items:
            self.items[self.km.name] = []
        self.items[self.km.name].append(item)

        return item

    def keymap_items(self):
        for kmis in self.items.values():
            for kmi in kmis:
                yield kmi

    def clear(self):
        if not self.items:
            return

        keymaps = bpy.context.window_manager.keyconfigs.addon.keymaps
        for k, v in self.items.items():
            if k in keymaps:
                for item in v:
                    keymaps[k].keymap_items.remove(item)

        self.items.clear()


hotkeys = Hotkeys.get_instance()


def unregister():
    hotkeys.clear()
