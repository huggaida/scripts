import bpy
import os
from copy import deepcopy
from . import constants as cc
from .addon import ADDON_ID, ADDON_PATH, prefs, uprefs, timeout, ic
from .types.property_types import Hotkey
from .utils.hotkeys import hotkeys
from .utils.ui_utils import operator
from .utils.overlay import Overlay
from .utils import operator_utils
from .utils.last_operator import last_operator as lo
from .utils import prop_data as pdu
from .utils import operator_utils as ou
from .utils import collection_utils as cu
from .ops import ui as o_ui


class RepeatHistoryItem:
    def __init__(
            self, idx=None, label=None, idname=None, func=None, props=None):
        self.idx = idx
        self.label = label
        self.idname = idname
        self.func = func
        self.props = dict() if props is None else props

    def clear(self):
        self.idx = None
        self.label = None
        self.idname = None
        self.func = None
        self.props.clear()

    def update(self, lo):
        self.clear()
        self.label = lo.label
        self.idname = lo.idname
        self.func = lo.func
        self.props.update(lo.ao_props)


class RepeatData:
    def __init__(self):
        self.idx = 0
        self.op = None
        self.history = []
        self.history_idx = 1

        self.skip_operators = {
            'MESH_OT_shortest_path_pick',
            'OBJECT_OT_editmode_toggle',
        }

    def check(self):
        wm = bpy.context.window_manager
        wm_lo = wm.operators and wm.operators[-1] or None
        return wm_lo and self.op and wm_lo == self.op

    def check_operator(self, idname):
        if idname.startswith("MESH_OT_select"):
            return False

        pr = prefs()
        if idname in pr.operators and pr.operators[idname].skip:
            return False

        return idname not in self.skip_operators

    def update(self, delta):
        pr = prefs()
        wm = bpy.context.window_manager
        self.idx += delta
        self.op = wm.operators and wm.operators[-1] or None

        if pr.repeat_history_auto and self.idx == 1 and delta > 0:
            self.update_history()

    def reset(self):
        self.idx = 0
        self.op = None

    def clear_history(self):
        self.history.clear()
        self.history_idx = 1

    def exec_history(self, idx):
        pr = prefs()
        if -1 > idx >= len(self.history):
            return

        item = pr.last_redo_data if idx == -1 else self.history.pop(idx)
        item.func('EXEC_DEFAULT', True, **item.props)

        if idx != -1:
            self.history.insert(0, item)

    def rename_history(self, idx, name):
        if 0 > idx >= len(self.history):
            return

        item = self.history[idx]
        item.label = name

    def update_history(self):
        pr = prefs()

        for item in self.history:
            if item.idname == lo.idname and item.props == lo.ao_props:
                return

        if len(self.history) >= pr.repeat_history_size:
            self.history.pop()

        self.history.insert(
            0, RepeatHistoryItem(
                self.history_idx,
                lo.label, lo.idname, lo.func, deepcopy(lo.ao_props)))
        self.history_idx += 1


class RL_UL_operator_list(bpy.types.UIList):
    def draw_item(
            self, context, layout, data, item,
            icon, active_data, active_propname, index):
        if operator_utils.check_idname(item.name):
            od = pdu.OperatorData(item.name)
            layout.label(text=od.label, icon=ic(od.icon))
        else:
            layout.prop(item, "name", text="", emboss=False, icon=ic('ERROR'))

        if item.skip:
            row = layout.row(align=True)
            row.enabled = False
            row.operator(
                o_ui.RL_OT_operator_skip.bl_idname,
                text="", icon=ic('GHOST_DISABLED'), emboss=False)

    def filter_items(self, context, data, propname):
        pr = prefs()
        items = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        filtered = []
        ordered = []

        if self.filter_name:
            filtered = helper_funcs.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item,
                items, "name")

        if not filtered:
            filtered = [self.bitflag_filter_item] * len(items)

        if pr.use_filter:
            for idx, item in enumerate(items):
                if ou.idname_to_group(item.name) not in pr.filter:
                    filtered[idx] = 0

        # if self.use_filter_sort_alpha:
        #     ordered = helper_funcs.sort_items_by_name(items, "name")

        return filtered, ordered


class RL_MT_repeat_history(bpy.types.Menu):
    bl_label = "Repeat History"

    def draw(self, context):
        pr = prefs()
        layout = self.layout

        for i, item in enumerate(pr.rd.history):
            layout.operator(
                o_ui.RL_OT_repeat_history.bl_idname,
                text="%i. %s" % (item.idx, item.label),
                icon=ic(pdu.OperatorData(item.idname).icon)).idx = i

        if pr.rd.history:
            layout.separator()

        ao = context.active_operator
        text = "Add %s" % ou.idname_to_label(ao.bl_idname) if ao else \
            "No Active Operator"

        layout.operator(
            o_ui.RL_OT_repeat_history_add.bl_idname,
            text=text, icon=ic('ZOOMIN'))

        if pr.rd.history:
            layout.separator()
            layout.operator(
                o_ui.RL_OT_repeat_history_clear.bl_idname,
                text="Clear", icon=ic('X'))


class RL_MT_pie_menu(bpy.types.Menu):
    bl_label = "Re-Last"

    def draw_slot(self, layout, idx):
        pr = prefs()

        item = pr.pie_slots[idx]
        text = " "
        icon = 'NONE'
        for eitem in cc.ACTION_ITEMS:
            if eitem[0] == item.id:
                text = eitem[1]
                icon = eitem[3]
                break

        ao = bpy.context.active_operator
        ao_text = text
        if not ao:
            ao_text = "No Active Operator"

        if item.id == 'NONE':
            layout.separator()

        elif item.id == 'EDIT':
            if ao:
                added = ao.bl_idname in pr.operators
                icon = icon if added else 'ZOOMIN'
                text = "Edit Operator" if added else "Add Operator"
            layout.operator(
                o_ui.RL_OT_edit.bl_idname, text=text, icon=ic(icon))

        elif item.id == 'PIE':
            operator(
                layout, "wm.call_menu_pie", text=text, icon=ic(icon),
                name="RL_MT_pie_menu")

        elif item.id == 'RESET':
            layout.operator(
                o_ui.RL_OT_reset.bl_idname, text=text, icon=ic(icon))

        elif item.id == 'RESET_ALL':
            layout.operator(
                o_ui.RL_OT_reset_all.bl_idname, text=text, icon=ic(icon))

        elif item.id == 'F6':
            layout.operator("screen.redo_last", text=ao_text, icon=ic(icon))

        elif item.id == 'OVERVIEW':
            layout.operator(
                o_ui.RL_OT_overview.bl_idname, text=text, icon=ic(icon))

        elif item.id == 'HISTORY':
            layout.operator(
                o_ui.RL_OT_repeat_history.bl_idname, text=text, icon=ic(icon))

        elif item.id == 'SKIP':
            layout.operator(
                o_ui.RL_OT_operator_skip.bl_idname, text=text, icon=ic(icon))

    def draw(self, context):
        layout = self.layout.menu_pie()
        layout.operator_context = 'INVOKE_DEFAULT'

        for i in range(8):
            self.draw_slot(layout, i)


def update_operators_idx(self, context):
    if self.operators_idx < 0:
        return

    pr = prefs()
    items = pr.prop_enum_items
    items.clear()

    if not pr.selected_operator:
        return

    od = pdu.OperatorData(pr.selected_operator.name)
    pd = od.prop_data
    if not pd:
        return

    idx = 0
    for k, v in pd.items():
        for pd in v:
            if pd.type == 'REPEAT':
                continue

            label = pd.label
            if pd.group:
                label += " (%s)" % ou.idname_to_label(pd.group)

            items.append(
                ("%s.%s" % (pd.group, pd.id),
                    label, pd.description, cc.TYPE_ICONS[pd.type], idx))
            idx += 1


class RL_Action(bpy.types.PropertyGroup):
    id: bpy.props.EnumProperty(items=cc.ACTION_ITEMS)


class RL_Prop(bpy.types.PropertyGroup):
    group: bpy.props.StringProperty()
    data: bpy.props.StringProperty()
    hotkey: bpy.props.PointerProperty(type=Hotkey)
    use_click: bpy.props.BoolProperty(
        description="To change the value:\n"
        "* Click the button or\n"
        "* Move the mouse while holding down the button")

    def custom_items(self, context):
        pr = prefs()
        if not pr.custom_items:
            pr.custom_items.append((
                'NONE', "Mouse Wheel", "Scroll the mouse wheel",
                cc.IC_WHEEL, 0))

            idx = 1
            for k in pr.custom_keys:
                name = bpy.types.UILayout.enum_item_name(
                    pr, "default_prop_mode", k)
                pr.custom_items.append((
                    k, name, "Hold down the hotkey and move the mouse",
                    cc.IC_KEY_MOVE, idx))
                idx += 1

            pr.custom_items.append((
                'NEW', "New Sticky Hotkey", "New sticky hotkey",
                'ADD', idx))

        return pr.custom_items

    def custom_get(self):
        pr = prefs()
        if self.hotkey.key == 'NONE' or len(pr.custom_items) == 0:
            return 0
        else:
            for item in pr.custom_items:
                if self.hotkey.key == item[0]:
                    return item[4]

        return 0

    def custom_set(self, value):
        pr = prefs()
        if value == 0:
            self.hotkey.key = 'NONE'
        elif value == len(pr.custom_items) - 1:
            op = pr.selected_operator
            ctx = {}
            for i, prop in enumerate(op.props):
                if prop == self:

                    def call_operator(scene=None):
                        bpy.ops.rl.prop_hotkey_select(
                            ctx, 'INVOKE_DEFAULT', mode='NEW', idx=i)

                    ctx["window"] = bpy.context.window
                    ctx["screen"] = bpy.context.screen
                    ctx["area"] = bpy.context.area
                    ctx["region"] = bpy.context.region
                    ctx["scene"] = bpy.context.scene
                    ctx["blend_data"] = bpy.context.blend_data
                    timeout(call_operator)
                    break
        else:
            self.hotkey.key = pr.custom_items[value][0]

    custom: bpy.props.EnumProperty(
        name="Hotkey", description="Hotkey", items=custom_items,
        get=custom_get, set=custom_set)

    items = None

    def get_mode_data(self, data=None, prop=None):
        if self:
            data = self.hotkey
            prop = "key"
        else:
            data = data or prefs()
            prop = prop or "default_prop_mode"

        if getattr(data, prop) in {'NONE', 'WHEELUPMOUSE'}:
            return "Mouse Wheel", cc.IC_WHEEL
        else:
            name = bpy.types.UILayout.enum_item_name(
                data, prop, getattr(data, prop))
            return name, cc.IC_KEY_MOVE

    def get_items(self, context):
        return prefs().prop_enum_items

    def get_prop(self):
        pr = prefs()
        if not pr.selected_operator:
            return -1

        id = "%s.%s" % (self.group, self.data)
        for item in pr.prop_enum_items:
            if item[0] == id:
                return item[4]

        return -1

    def set_prop(self, value):
        item = prefs().prop_enum_items[value]
        self.group, _, self.data = item[0].partition(".")
        pd = pdu.OperatorData(prefs().selected_operator.name).get_prop_data(
            self.group, self.data)

        if pd and pd.is_number:
            self.step = pd.step
        else:
            self.step = 1

    prop: bpy.props.EnumProperty(
        items=get_items, name="Property", description="Property",
        get=get_prop, set=set_prop)
    step: bpy.props.FloatProperty(
        name="Step", description="Step",
        default=0.1, min=-10000, max=10000, step=10,
        precision=4)

    def step_angle_get(self):
        return self.step

    def step_angle_set(self, value):
        self.step = value

    step_angle: bpy.props.FloatProperty(
        name="Step", description="Step",
        default=0.1, min=-10000, max=10000, step=10,
        precision=4, subtype='ANGLE',
        get=step_angle_get, set=step_angle_set)

    def step_int_get(self):
        return int(self.step)

    def step_int_set(self, value):
        self.step = value

    step_int: bpy.props.IntProperty(
        name="Step", description="Step",
        default=1, min=-10000, max=10000,
        get=step_int_get, set=step_int_set)


class RL_Operator(bpy.types.PropertyGroup):

    def label_get(self):
        od = pdu.OperatorData(self.name)
        return od.label

    label: bpy.props.StringProperty(get=label_get)

    skip: bpy.props.BoolProperty(
        description=(
            "Skip the operator when using Repeat tool \n"
            "and try to repeat the previous operator"))
    props: bpy.props.CollectionProperty(type=RL_Prop)

    def has_prop(self, group, id):
        for p in self.props:
            if p.data == id and p.group == group:
                return True

        return False

    def get_prop(self, event, key):
        for prop in self.props:
            if prop.hotkey.check_event(event, False) and \
                    prop.hotkey.key == key:
                return prop

        return None

    def get_prop_data(self, event, key):
        prop = self.get_prop(event, key)
        if not prop:
            return None, None

        pd = pdu.OperatorData(self.name).get_prop_data(prop.group, prop.data)
        if pd and pd.is_number:
            pd.step = prop.step

        return prop, pd


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    custom_keys = set()
    custom_items = []
    rd = RepeatData()
    last_redo_data = RepeatHistoryItem()

    def get_filter_items(self, context):
        return self.filter_enum_items

    def update_use_filter(self, context):
        pass

    operators: bpy.props.CollectionProperty(type=RL_Operator)
    operators_idx: bpy.props.IntProperty(update=update_operators_idx)
    actions: bpy.props.CollectionProperty(type=RL_Action)
    pie_slots: bpy.props.CollectionProperty(type=RL_Action)
    tab: bpy.props.EnumProperty(
        items=(
            ('OPERATORS', "Operators",
                "Operators\n"
                "Manage registered operators for Redo tool"),
            ('HOTKEYS', "Hotkeys",
                "Hotkeys"),
            ('PIE', "Pie Menu",
                "Configure Pie Menu"),
            ('SETTINGS', "Settings",
                "Settings\n"
                "Configure add-on settings"),
            ('ADVANCED', "Advanced Settings",
                "Advanced Settings\n"
                "Assign actions to the hotkey"),
        ))
    adv_settings: bpy.props.BoolProperty(description="Show advanced settings")
    redo_settings: bpy.props.BoolProperty(description="Show Settings")
    import_filepath: bpy.props.StringProperty(
        default=os.path.join(ADDON_PATH, "examples", "examples.json"),
        options={'HIDDEN'})
    export_filepath: bpy.props.StringProperty(options={'HIDDEN'})
    hold_timeout: bpy.props.IntProperty(
        name="Hold Time (ms)", description="Hold time (in ms)",
        default=200, min=100, max=1000, step=10)
    default_prop_mode: bpy.props.EnumProperty(
        name="Default Hotkey", description="Default hotkey",
        items=cc.KEY_ITEMS)
    hk_edit: bpy.props.PointerProperty(type=Hotkey)
    overlay: bpy.props.PointerProperty(type=Overlay)
    use_filter: bpy.props.BoolProperty(
        description="Use filter", update=update_use_filter)
    looping: bpy.props.BoolProperty(
        name="Loop Boolean and Enum Properties",
        description="Loop boolean and enum properties "
        "(checkboxes and drop-down lists)")
    filter: bpy.props.EnumProperty(
        name="Filter", description="Filter",
        options={'ENUM_FLAG'},
        items=get_filter_items)
    default_step_float: bpy.props.FloatProperty(
        name="Default Float Step", description="Default step (Float)",
        default=0.1)
    custom_threshold_float: bpy.props.IntProperty(
        name="Slider (Float)", description="Slider (Float)",
        subtype='PIXEL', default=10)
    # repeat_global: bpy.props.BoolProperty(
    #     name="Use Global Hotkey",
    #     description="Use the hotkey for unregistered operators",
    #     default=True)
    repeat: bpy.props.BoolProperty(
        name="Enable Repeat Tool", description="Enable Repeat tool",
        default=True)
    repeat_global_hk: bpy.props.PointerProperty(type=Hotkey)
    repeat_history_auto: bpy.props.BoolProperty(
        name="Auto Repeat History",
        description="Allow Repeat tool to add operators "
        "to the Repeat History",
        default=True)

    def repeat_history_size_update(self, context):
        pr = prefs()
        while len(pr.rd.history) > self.repeat_history_size:
            pr.rd.history.pop()

    repeat_history_size: bpy.props.IntProperty(
        name="Repeat History Size", description="Repeat history size",
        default=20, min=1, max=100, update=repeat_history_size_update)
    custom_threshold_int: bpy.props.IntProperty(
        name="Slider (Int)", description="Slider (Integer)",
        subtype='PIXEL', default=20)
    custom_threshold_bool: bpy.props.IntProperty(
        name="Checkbox (Bool)", description="Checkbox (Boolean)",
        subtype='PIXEL', default=40)
    custom_threshold_enum: bpy.props.IntProperty(
        name="Drop-Down List (Enum)", description="Drop-down list (Enum)",
        subtype='PIXEL', default=40)
    custom_threshold_repeat: bpy.props.IntProperty(
        name="Repeat Last", description="Repeat Last tool",
        subtype='PIXEL', default=40)
    custom_mode: bpy.props.EnumProperty(
        name="Mode", description="Mode",
        items=(
            ('H', "Horizontal", ""),
            ('V', "Vertical", ""),
        ))

    prop_enum_items = []
    filter_enum_items = []

    def get_threshold(self, prop_data=None):
        if not prop_data:
            return self.custom_threshold_repeat
        elif prop_data.type == 'FLOAT':
            return self.custom_threshold_float
        elif prop_data.type == 'INT':
            return self.custom_threshold_int
        elif prop_data.type == 'ENUM':
            return self.custom_threshold_enum
        elif prop_data.type == 'BOOL':
            return self.custom_threshold_bool

        return 20

    def update_filter_items(self, select_all=False):
        old_items = {item[0] for item in self.filter_enum_items}
        self.filter_enum_items.clear()

        last_group = None
        new_items = set()
        for op in self.operators:
            group = ou.idname_to_group(op.name)
            if last_group != group:
                last_group = group
                self.filter_enum_items.append((
                    group, group.title(), group.title(),
                    ic(ou.idname_to_icon(op.name)),
                    int(pow(2, len(self.filter_enum_items)))
                ))
                new_items.add(group)

        if select_all:
            self.filter = new_items
        else:
            self.filter |= new_items - old_items

    @property
    def selected_operator(self):
        if self.operators_idx >= len(self.operators):
            return None
        return self.operators[self.operators_idx]

    def add_key(self, key):
        if key in self.custom_keys:
            return

        self.custom_keys.add(key)
        hotkeys.keymap("Screen Editing")
        hotkeys.add(o_ui.RL_OT_modal, key, 1, 1, 1, 1, 1)
        self.custom_items.clear()

    def update_operator(self):
        update_operators_idx(self, bpy.context)

    def get_operator(self, idname):
        if idname not in self.operators:
            op = self.operators.add()
            op.name = idname
            self.operators_idx = len(self.operators) - 1

            if pdu.OperatorData(idname).num_props:
                o_ui.add_prop()

            self.sort_operators()
            self.update_filter_items()

        else:
            self.operators_idx = self.operators.find(idname)

        return self.operators[idname]

    def sort_operators(self):
        cu.sort_collection(
            self.operators,
            lambda item:
                ou.idname_to_group(item.name) + ou.idname_to_label(item.name),
            self, "operators_idx")

    def get_prop_mode_data(self):
        return RL_Prop.get_mode_data(None)

    def draw_editor(self, layout, context):
        op = self.selected_operator

        row = layout.split(factor=0.3) if op else layout.row()
        col = row.column(align=True)

        box = col.box().row(align=True)
        self.hlabel(
            box, "Operators",
            msg="Add/Select the operator\n"
            "to assign hotkeys to its properties")

        col.template_list(
            RL_UL_operator_list.__name__, "",
            self, "operators",
            self, "operators_idx",
            rows=max(min(len(self.operators), 10), 3))

        subrow = col.row(align=True)
        subrow.operator(o_ui.RL_OT_import.bl_idname, text="Import")
        if op:
            subrow.operator(o_ui.RL_OT_export.bl_idname, text="Export")

        if op:
            row = row.row()

        col = row.column(align=True)
        operator(col, o_ui.RL_OT_item_add.bl_idname, "", 'ZOOMIN')
        if op:
            operator(
                col, o_ui.RL_OT_item_remove.bl_idname, "", 'ZOOMOUT',
                idx=self.operators_idx)
            operator(
                col, o_ui.RL_OT_item_remove.bl_idname, "", 'X',
                all=True)

            col.separator()
            col.prop(
                self, "use_filter", text="", icon=ic('FILTER'), toggle=True)
            if self.use_filter:
                col.prop(self, "filter", text="", expand=True)

            if op:
                col.separator()
                col.prop(op, "skip", text="", icon=ic('GHOST_DISABLED'))

            o_ui.draw_operator(row.column(), False)

    def hprop(
            self, layout, data, prop, text=None,
            mode=None, icon='NONE', msg="", title=""):
        row = layout.row(align=True)
        if msg:
            mode = 'MSG'
        if not title and text:
            title = text.strip(":")

        if text:
            row.prop(data, prop, text=text)
        else:
            row.prop(data, prop)

        operator(
            row, o_ui.RL_OT_help.bl_idname, "", 'QUESTION', False,
            mode=mode, msg=msg, title=title)

    def hlabel(
            self, layout, text, mode=None, icon='NONE', msg="", title=""):
        row = layout.row(align=False)
        row.label(text=text, icon=ic(icon))
        if msg:
            mode = 'MSG'

        if not title:
            title = text.strip(":")

        operator(
            row, o_ui.RL_OT_help.bl_idname, "", 'QUESTION', False,
            mode=mode, msg=msg, title=title)

    def scaled_col(self, layout, scale):
        if False:  # Blender 2.8 scale bug
            row = layout.row()
            row.scale_x = scale
            row.alignment = 'CENTER'
        else:
            scale = 0.5
            scale1 = 0.5 * (1 - scale)
            scale2 = scale / (1 - scale1)
            split1 = layout.split(factor=scale1)
            split1.column()
            split2 = split1.split(factor=scale2)
            ret = split2.column()
            split2.column()
            return ret

    def titled_box(self, layout):
        col = layout.column(align=True)
        header = col.box().row(align=True)
        header.scale_y = 0.6
        return header, col.box().column()

    def pie_slot(self, layout, idx, title):
        slot = layout.row(align=True)
        slot.scale_y = 1.25
        slot.operator_context = 'INVOKE_DEFAULT'
        if idx < 0:
            slot.alignment = 'CENTER'
            slot.label(text="", icon=ic('PROP_CON'))

        else:
            pr = prefs()
            item = pr.pie_slots[idx]
            if item.id == 'NONE':
                slot.active = False
                text = " "

            else:
                text = slot.enum_item_name(self.pie_slots[0], "id", item.id)

            operator(
                slot, o_ui.RL_OT_action_select.bl_idname, text,
                idx=idx, target='PIE', title=title)

    def action(self, layout, idx, title):
        layout.operator_context = 'INVOKE_DEFAULT'
        item = self.actions[idx]

        if idx == 0:
            row = layout.row()
        else:
            row = layout.split(factor=0.7, align=True)

        if item.id == 'NONE':
            row.active = False

        row.scale_y = 1.25

        operator(
            row, o_ui.RL_OT_action_select.bl_idname,
            layout.enum_item_name(self.actions[0], "id", item.id),
            idx=idx, target='HOTKEY', title=title)

        if False:
            row.prop(
                uprefs().inputs, "mouse_double_click_time",
                text="Time (ms)")
        elif idx == 1:
            row.prop(self, "hold_timeout", text="Time (ms)")
        elif idx == 2:
            row.prop(
                uprefs().inputs, "tweak_threshold",
                text="Distance")

    def draw_settings(self, layout, context):
        pr = prefs()

        if self.tab == 'HOTKEYS':
            col = self.scaled_col(layout, 0.25)

            text = "Hotkey:"
            actions = []
            for a in pr.actions:
                if a.id == 'NONE':
                    continue

                actions.append(
                    bpy.types.UILayout.enum_item_name(a, "id", a.id))

            if actions:
                text = "%s %s" % ("/".join(actions), text)

            self.hlabel(col, text, mode='HOTKEY')
            subcol = col.column(align=True)
            self.hk_edit.draw(subcol, context, any=True)

            col.separator()
            self.hprop(
                col, pr, "repeat", "Repeat Tool Hotkey:",
                msg="Blender's Repeat tool (shift+R)")
            sub = col.column(align=True)
            name, icon = RL_Prop.get_mode_data(
                None, self.repeat_global_hk, "key")
            operator(
                sub, o_ui.RL_OT_prop_hotkey_select.bl_idname, name, icon,
                target='REPEAT')

            sub = sub.row(align=True)
            sub.prop(self.repeat_global_hk, "ctrl", text="Ctrl", toggle=True)
            sub.prop(self.repeat_global_hk, "shift", text="Shift", toggle=True)
            sub.prop(self.repeat_global_hk, "alt", text="Alt", toggle=True)
            sub.prop(self.repeat_global_hk, "oskey", text="OSKey", toggle=True)
            sub.prop(self.repeat_global_hk, "key_mod", text="", event=True)

            if pr.custom_keys:
                col.separator()
                self.hlabel(
                    col, "Mouse Movement Direction and Distance:",
                    msg="Used by sticky hotkeys",
                    icon=ic(cc.IC_KEY_MOVE))
                sub = col.column(align=True)
                sub.prop(self, "custom_mode", text="")
                sub.prop(self, "custom_threshold_float")
                sub.prop(self, "custom_threshold_int")
                sub.prop(self, "custom_threshold_bool")
                sub.prop(self, "custom_threshold_enum")
                sub.prop(self, "custom_threshold_repeat")

        if self.tab == 'PIE':
            col = self.scaled_col(layout, 1)

            subrow = col.row()
            subrow.alignment = 'CENTER'
            self.pie_slot(subrow, 3, "Top Action")

            col.separator()
            subrow = col.row()
            subrow.alignment = 'CENTER'
            self.pie_slot(subrow, 4, "Top-Left Action")
            subrow.label(text=" ")
            self.pie_slot(subrow, 5, "Top-Right Action")

            col.separator()
            subrow = col.row()
            subrow.alignment = 'CENTER'
            self.pie_slot(subrow, 0, "Left Action")

            center = subrow.row(align=True)
            center.scale_x = 0.4
            center.label(text=" ")

            self.pie_slot(subrow, 1, "Right Action")

            col.separator()
            subrow = col.row()
            subrow.alignment = 'CENTER'
            self.pie_slot(subrow, 6, "Bottom-Left Action")
            subrow.label(text=" ")
            self.pie_slot(subrow, 7, "Bottom-Right Action")

            col.separator()
            subrow = col.row()
            subrow.alignment = 'CENTER'
            self.pie_slot(subrow, 2, "Bottom Action")

        elif self.tab == 'SETTINGS':
            col = self.scaled_col(layout, 0.7)

            col.prop(self, "repeat_history_auto")
            col.prop(self, "repeat_history_size")

            col.separator()
            col.separator()
            self.overlay.draw(col)

        elif self.tab == 'ADVANCED':
            col = self.scaled_col(layout, 1)

            col.label(text="Configure Hotkey Actions:")

            sub = col.column(align=True)
            box = sub.box().column()
            self.hlabel(
                box, "Click/Double Click Action:",
                msg="Click/Double click the hotkey\n"
                "to trigger the action",
                title="Click/Double Click Action")
            self.action(box, 0, "Click/Double Click Action")

            box = sub.box().column()
            self.hlabel(
                box, "Hold Action:",
                msg="Hold down the hotkey (%d ms)\n"
                "to trigger the action" % pr.hold_timeout,
                title="Hold Action")
            self.action(box, 1, "Hold Action")

            box = sub.box().column()
            self.hlabel(
                box, "Hold and Move Action:",
                msg="Hold down the hotkey and move the mouse (%d px)\n"
                "to trigger the action" %
                uprefs().inputs.tweak_threshold,
                title="Hold and Move Action")
            self.action(box, 2, "Hold and Move Action")

    def draw(self, context):
        pr = prefs()
        col = self.layout
        row = col.row(align=True)
        row.prop_enum(pr, "tab", 'OPERATORS')
        row.prop_enum(pr, "tab", 'HOTKEYS')
        row.prop_enum(pr, "tab", 'PIE')
        row.prop_enum(pr, "tab", 'SETTINGS')
        if pr.adv_settings:
            row.prop_enum(pr, "tab", 'ADVANCED', text="", icon=ic('SETTINGS'))

        if pr.tab == 'OPERATORS':
            self.draw_editor(self.layout, context)

        else:
            self.draw_settings(self.layout, context)

    @staticmethod
    def context_menu(menu, context):
        layout = menu.layout
        layout.operator(
            o_ui.RL_OT_context_menu.bl_idname,
            text="Re-Last", icon=ic('CURVE_PATH'))


def register():
    pr = prefs()
    pr.tab = 'OPERATORS'
    pr.redo_settings = False

    hotkeys.keymap("Screen Editing")
    hotkeys.add(
        o_ui.RL_OT_redo, 'WHEELUPMOUSE', 1, 1, 1, 1, 1, delta=1)
    hotkeys.add(
        o_ui.RL_OT_redo, 'WHEELDOWNMOUSE', 1, 1, 1, 1, 1, delta=-1)

    if pr.hk_edit.is_clear():
        pr.hk_edit.init('MIDDLEMOUSE', any=True, value='DOUBLE_CLICK')

    if pr.repeat_global_hk.is_clear():
        pr.repeat_global_hk.init('NONE', alt=True)

    pr.hk_edit.add_kmi(
        hotkeys.add(o_ui.RL_OT_action_exec, hotkey=pr.hk_edit))

    if not pr.actions:
        pr.actions.add().id = 'PIE'
        pr.actions.add()
        pr.actions.add()

    if not pr.pie_slots:
        for i in range(8):
            pr.pie_slots.add()

        pr.pie_slots[0].id = 'RESET'
        pr.pie_slots[1].id = 'F6'
        pr.pie_slots[2].id = 'EDIT'
        pr.pie_slots[3].id = 'OVERVIEW'
        pr.pie_slots[4].id = 'RESET_ALL'
        pr.pie_slots[6].id = 'SKIP'
        pr.pie_slots[7].id = 'HISTORY'

    for op in pr.operators:
        for prop in op.props:
            if prop.hotkey.key != 'NONE':
                pr.add_key(prop.hotkey.key)

    if pr.repeat_global_hk.key not in {'NONE', 'WHEELUPMOUSE'}:
        pr.add_key(pr.repeat_global_hk.key)

    if pr.default_prop_mode != 'NONE':
        pr.add_key(pr.default_prop_mode)

    pr.use_filter = False
    update_operators_idx(pr, bpy.context)
    pr.update_filter_items(select_all=True)


def unregister():
    pr = prefs()
    pr.custom_keys.clear()
