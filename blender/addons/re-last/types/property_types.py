import bpy

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


class DynamicPropertyGroupData:
    instances = {}

    @staticmethod
    def get_instance(key):
        if key not in DynamicPropertyGroupData.instances:
            DynamicPropertyGroupData.instances[key] = \
                DynamicPropertyGroupData()

        return DynamicPropertyGroupData.instances[key]


class DynamicPropertyGroup:
    def __getattr__(self, name):
        data = DynamicPropertyGroupData.get_instance(self.as_pointer())
        return getattr(data, name)

    def __setattr__(self, name, value):
        if name in self.rna_type.properties:
            bpy.types.PropertyGroup.__setattr__(self, name, value)
        else:
            data = DynamicPropertyGroupData.get_instance(self.as_pointer())
            setattr(data, name, value)

    def __delattr__(self, name):
        if name in self.rna_type.properties:
            bpy.types.PropertyGroup.__delattr__(self, name)
        else:
            data = DynamicPropertyGroupData.get_instance(self.as_pointer())
            delattr(data, name)


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

    label: bpy.props.BoolProperty(
        description="Label", get=lambda s: False, set=lambda s, v: None)
    key: bpy.props.EnumProperty(
        items=key_items, description="Key pressed", update=_hotkey_update)
    scroll: bpy.props.BoolProperty()
    ctrl: bpy.props.BoolProperty(
        description="Ctrl key pressed", update=_hotkey_update)
    shift: bpy.props.BoolProperty(
        description="Shift key pressed", update=_hotkey_update)
    alt: bpy.props.BoolProperty(
        description="Alt key pressed", update=_hotkey_update)
    oskey: bpy.props.BoolProperty(
        description="Operating system key pressed", update=_hotkey_update)
    any: bpy.props.BoolProperty(
        description="Any modifier keys pressed", update=_hotkey_update)
    key_mod: bpy.props.EnumProperty(
        items=key_items,
        description="Regular key pressed as a modifier",
        update=_hotkey_update)
    value: bpy.props.EnumProperty(
        items=value_items,
        update=_hotkey_update)

    def init(
            self,
            key, ctrl=False, shift=False, alt=False, oskey=False, any=False,
            key_mod='NONE', value='PRESS'):
        self.key = key
        self.ctrl = ctrl
        self.shift = shift
        self.alt = alt
        self.oskey = oskey
        self.any = any
        self.key_mod = key_mod
        self.value = value

    def clear(self):
        self.value = 'PRESS'
        self.key = 'NONE'
        self.ctrl = False
        self.shift = False
        self.alt = False
        self.oskey = False
        self.any = False
        self.key_mod = 'NONE'

    def is_clear(self):
        return self.key == 'NONE' and not self.ctrl and not self.shift and \
            not self.alt and not self.oskey and not self.any and \
            self.key_mod == 'NONE'

    def check_event(self, event, key=True):
        return (not key or self.key == event.type) and (
            self.any or
            self.ctrl == event.ctrl and
            self.shift == event.shift and
            self.alt == event.alt and
            self.oskey == event.oskey)

    def encode(self):
        # if not self.key or self.key == 'NONE':
        #     return ''

        hotkey = ''
        if self.ctrl:
            hotkey += 'ctrl+'
        if self.shift:
            hotkey += 'shift+'
        if self.alt:
            hotkey += 'alt+'
        if self.oskey:
            hotkey += 'oskey+'
        if self.key_mod and self.key_mod != 'NONE':
            hotkey += self.key_mod + "+"
        hotkey += self.key

        if hotkey:
            hotkey = "%s:%s" % (self.value, hotkey)

        return hotkey

    def decode(self, value):
        mode, _, value = value.partition(":")
        if not value:
            return

        self.value = mode

        parts = value.upper().split("+")

        ctrl = 'CTRL' in parts
        if ctrl:
            parts.remove('CTRL')

        alt = 'ALT' in parts
        if alt:
            parts.remove('ALT')

        shift = 'SHIFT' in parts
        if shift:
            parts.remove('SHIFT')

        oskey = 'OSKEY' in parts
        if oskey:
            parts.remove('OSKEY')

        key_mod = 'NONE' if len(parts) == 1 else parts[0]
        key = parts[-1]

        enum_items = bpy.types.Event.bl_rna.properties["type"].enum_items
        if key_mod not in enum_items:
            key_mod = 'NONE'
        if key not in enum_items:
            key = 'NONE'

        self.key = key
        self.ctrl = ctrl
        self.shift = shift
        self.alt = alt
        self.oskey = oskey
        self.key_mod = key_mod

        self._hotkey_update(bpy.context)

    def add_kmi(self, kmi):
        if not hasattr(self, "kmis"):
            self.kmis = []

        self.kmis.append(kmi)

    def draw(
            self, layout, context,
            ctrl=True, shift=True, alt=True, oskey=True, key_mod=True,
            value=True, label=None, any=False):
        box = layout.box()
        if label:
            box.label(text=label)
        col = box.column(align=True)

        if not self.scroll:
            row = col.row(align=True)
            row.prop(self, "key", text="", event=True)
            if value:
                row.prop(self, "value", text="")
        else:
            row = col.row(align=True)
            row.enabled = False
            # row.operator("pme.none", text="Mouse Wheel Up/Down")
            row.prop(self, "label", text="Mouse Wheel Up/Down", toggle=True)

        row = col.row(align=True)
        if any:
            sub = row.row(align=True)
            sub.prop(self, "any", text="Any", toggle=True)
            if self.any:
                sub.scale_x = 5

        if not self.any:
            if ctrl:
                row.prop(self, "ctrl", text="Ctrl", toggle=True)
            if shift:
                row.prop(self, "shift", text="Shift", toggle=True)
            if alt:
                row.prop(self, "alt", text="Alt", toggle=True)
            if oskey:
                row.prop(self, "oskey", text="OSKey", toggle=True)

        if key_mod:
            row.prop(self, "key_mod", text="", event=True)

    def from_kmi(
            self, kmi,
            key=None, ctrl=None, shift=None, alt=None, oskey=None,
            key_mod=None, value=None, any=None):
        self.key = kmi.type if key is None else key
        self.ctrl = kmi.ctrl if ctrl is None else ctrl
        self.shift = kmi.shift if shift is None else shift
        self.alt = kmi.alt if alt is None else alt
        self.oskey = kmi.oskey if oskey is None else oskey
        self.any = kmi.any if any is None else any
        self.key_mod = kmi.key_modifier if key_mod is None else key_mod
        self.value = kmi.value if value is None else value

    def to_kmi(
            self, kmi,
            key=None, ctrl=None, shift=None, alt=None, oskey=None,
            key_mod=None, value=None, any=None):

        for map_type in KMI_MAP_TYPES:
            try:
                kmi.type = self.key if key is None else key
                break
            except TypeError:
                kmi.map_type = map_type

        kmi.ctrl = self.ctrl if ctrl is None else ctrl
        kmi.shift = self.shift if shift is None else shift
        kmi.alt = self.alt if alt is None else alt
        kmi.oskey = self.oskey if oskey is None else oskey
        any = self.any if any is None else any
        if any:
            kmi.any = True
        kmi.key_modifier = self.key_mod if key_mod is None else key_mod
        kmi.value = self.value if value is None else value

    def update(self, context):
        pass

    def __str__(self):
        if self.key == 'NONE':
            return 'NONE'

        keys = []
        if self.ctrl:
            keys.append("Ctrl")
        if self.shift:
            keys.append("Shift")
        if self.alt:
            keys.append("Alt")
        if self.oskey:
            keys.append("OSKey")
        if self.key_mod != 'NONE':
            keys.append(self.key_mod)
        keys.append(self.key)
        return " + ".join(keys)

    def to_ui_string(self):
        hotkey = ""
        if self.any:
            hotkey += "?"
        else:
            if self.ctrl:
                hotkey += "c"
            if self.shift:
                hotkey += "s"
            if self.alt:
                hotkey += "a"
            if self.oskey:
                hotkey += "o"
        if hotkey:
            hotkey += "+"
        if self.key_mod and self.key_mod != 'NONE':
            hotkey += "[%s]+" % self.key_mod

        if self.key and self.key != 'NONE':
            hotkey += "[%s]" % self.key
        else:
            hotkey += "Wheel"

        return hotkey
