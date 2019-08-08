import bpy


def find_user_kmi(addon_kmi, keymap_name=None):
    kcs = bpy.context.window_manager.keyconfigs
    akm = kcs.active.keymaps[keymap_name]
    km = kcs.user.keymaps[keymap_name]
    return km.keymap_items.from_id(addon_kmi.id + len(akm.keymap_items))


def draw_addon_kmi(layout, kmi, keymap_name, show_props=False):
    kmi = find_user_kmi(kmi, keymap_name)
    if not kmi:
        return

    map_type = kmi.map_type
    layout.context_pointer_set(
        "keymap",
        bpy.context.window_manager.keyconfigs.user.keymaps[keymap_name])

    col = layout
    col = col.column(align=True)
    box = col.box()
    split = box.split()

    row = split.row(align=True)
    row.prop(kmi, "show_expanded", text="", emboss=False)
    row.prop(kmi, "active", text="", emboss=False)

    row.label(text=kmi.name)

    row = split.row(align=True)
    row.prop(kmi, "map_type", text="")
    if map_type == 'KEYBOARD':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'MOUSE':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'NDOF':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'TWEAK':
        # subrow = row.row()
        row.prop(kmi, "type", text="")
        row.prop(kmi, "value", text="")
    elif map_type == 'TIMER':
        row.prop(kmi, "type", text="")

    if kmi.is_user_modified:
        row.separator()
        row.operator(
            "wm.keyitem_restore", text="", icon='BACK').item_id = kmi.id

    if kmi.show_expanded:
        box = col.box()

        if map_type not in {'TEXTINPUT', 'TIMER'}:
            sub = box.column(align=True)
            subrow = sub.row(align=True)

            if map_type == 'KEYBOARD':
                subrow.prop(kmi, "type", text="", event=True)
                subrow.prop(kmi, "value", text="")
            elif map_type in {'MOUSE', 'NDOF'}:
                subrow.prop(kmi, "type", text="")
                subrow.prop(kmi, "value", text="")

            subrow = sub.row(align=True)
            subrow.prop(kmi, "any", toggle=True)
            subrow.prop(kmi, "shift", toggle=True)
            subrow.prop(kmi, "ctrl", toggle=True)
            subrow.prop(kmi, "alt", toggle=True)
            subrow.prop(kmi, "oskey", toggle=True)
            subrow.prop(kmi, "key_modifier", text="", event=True)

        if show_props:
            box.template_keymap_item_properties(kmi)


class Hotkeys:

    @staticmethod
    def get_instance():
        if hasattr(Hotkeys, "_instance"):
            Hotkeys._instance.clear()

        Hotkeys._instance = Hotkeys()
        return Hotkeys._instance

    def __init__(self):
        self.keymaps = {}
        self.km = None

    def keymap(self, name="Window", space_type='EMPTY', region_type='WINDOW'):
        if name not in self.keymaps:
            self.keymaps[name] = \
                bpy.context.window_manager.keyconfigs.addon.keymaps.new(
                name, space_type=space_type, region_type=region_type)

        self.km = self.keymaps[name]

    def add(
            self, bl_class,
            key='NONE',
            ctrl=False, shift=False, alt=False, oskey=False, any=False,
            key_mod='NONE', value='PRESS', hotkey=None, **props):
        if not isinstance(bl_class, str):
            bl_class = bl_class.bl_idname

        if hotkey:
            key, ctrl, shift, alt, oskey, any, key_mod, value = \
                hotkey.key, hotkey.ctrl, hotkey.shift, hotkey.alt, \
                hotkey.oskey, hotkey.any, hotkey.key_mod, hotkey.value

        item = self.km.keymap_items.new(
            bl_class, key, value,
            ctrl=ctrl, shift=shift, alt=alt, oskey=oskey, any=any,
            key_modifier=key_mod)

        if props:
            for p in props.keys():
                setattr(item.properties, p, props[p])

        return item

    def keymap_items(self):
        for km in self.keymaps.values():
            for kmi in km.keymap_items:
                yield kmi

    def clear(self):
        if not self.keymaps:
            return

        for km in self.keymaps.values():
            while len(km.keymap_items):
                km.keymap_items.remove(km.keymap_items[-1])

            bpy.context.window_manager.keyconfigs.addon.keymaps.remove(km)

        self.keymaps.clear()


hotkeys = Hotkeys.get_instance()


def unregister():
    hotkeys.clear()
