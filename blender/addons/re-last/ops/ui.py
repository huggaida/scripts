import bpy
import os
from bpy_extras.io_utils import ExportHelper, ImportHelper
import json
from math import pi
from ..addon import prefs, uprefs, ic
from .. import constants as cc
from ..utils import collection_utils as cu
from ..utils import operator_utils as ou
from ..utils import prop_data as pdu
from ..utils import last_operator as lou
from ..utils.last_operator import last_operator as lo
from ..utils.ui_utils import tag_redraw, operator
from ..utils.icon_utils import icons
from ..utils.sticky_key import StickyKey
from ..utils.debug_utils import *
from ..utils import property_utils


class RL_OT_help(bpy.types.Operator):
    bl_idname = "rl.help"
    bl_label = "Help (RL)"
    bl_description = "Help"
    bl_options = {'INTERNAL'}

    mode: bpy.props.StringProperty(default='PROP', options={'SKIP_SAVE'})
    title: bpy.props.StringProperty(options={'SKIP_SAVE'})
    msg: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def _help_props(self, menu, context):
        row = menu.layout.row()
        col = row.column()
        col.label(text="Property Icons", icon=ic('INFO'))
        col.separator()
        col.label(text="Integer (Slider)", icon=ic(cc.TYPE_ICONS["INT"]))
        col.label(text="Float (Slider)", icon=ic(cc.TYPE_ICONS["FLOAT"]))
        col.label(
            text="Boolean (Check box)", icon=ic(cc.TYPE_ICONS["BOOLEAN"]))
        col.label(
            text="Enum (Drop-down list, radio button)",
            icon=ic(cc.TYPE_ICONS["ENUM"]))

        col.label(text=" ")
        col.label(text="Hotkey Icons", icon=ic('INFO'))
        col.separator()
        col.label(text="Scroll mouse wheel", icon=ic(cc.IC_WHEEL))
        col.label(
            text="Move mouse while holding down button",
            icon=ic(cc.IC_KEY_MOVE))
        col.label(
            text="Press button",
            icon=ic(cc.IC_KEY_CLICK))

        col = row.column()
        col.label(text="Hotkey Modifier Icons", icon=ic('INFO'))
        col.separator()
        col.label(text="Ctrl", icon_value=icons.get_icon("ctrl"))
        col.label(text="Shift", icon_value=icons.get_icon("shift"))
        col.label(text="Alt", icon_value=icons.get_icon("alt"))
        col.label(text="OSKey", icon_value=icons.get_icon("oskey"))

        col.label(text=" ")
        col.label(text=" ")
        col.separator()

    def _help_hotkey(self, menu, context):
        self.msg = (
            "You can configure the action(s) assigned to the hotkey\n"
            "in advanced settings")
        self._help_msg(menu, context)

        layout = menu.layout
        layout.separator()
        layout.operator(
            RL_OT_adv_settings_enable.bl_idname,
            text="Go to Advanced Settings",
            icon=ic('SETTINGS'))

    def _help_msg(self, menu, context):
        layout = menu.layout
        lines = self.msg.split("\n")
        for i, line in enumerate(lines):
            layout.label(
                text=line.strip(), icon=ic('INFO' if i == 0 else 'NONE'))

    def _help_url(self, menu, context):
        layout = menu.layout
        layout.label(text="Open URL", icon=ic('WORLD'))
        layout.separator()
        layout.operator("wm.url_open", text="OK").url = self.mode

    def execute(self, context):
        if self.mode == 'PROP':
            context.window_manager.popup_menu(self._help_props)
        elif self.mode == 'HOTKEY':
            context.window_manager.popup_menu(self._help_hotkey, "Hotkey")
        elif self.mode == 'MSG':
            context.window_manager.popup_menu(
                self._help_msg, title=self.title)
        else:
            context.window_manager.popup_menu(self._help_url)

        return {'FINISHED'}


class RL_OT_adv_settings_enable(bpy.types.Operator):
    bl_idname = "rl.adv_settings_enable"
    bl_label = "Enable Advanced Settings"
    bl_description = "Enable advanced settings"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        pr = prefs()
        pr.adv_settings = True
        pr.tab = 'ADVANCED'
        tag_redraw()
        return {'FINISHED'}


def exec_action(idx):
    pr = prefs()
    item = pr.actions[idx]

    if item.id == 'NONE':
        pass

    elif item.id == 'EDIT':
        if bpy.ops.rl.edit.poll():
            bpy.ops.rl.edit('INVOKE_DEFAULT')

    elif item.id == 'PIE':
        if bpy.ops.wm.call_menu_pie.poll():
            bpy.ops.wm.call_menu_pie(name="RL_MT_pie_menu")

    elif item.id == 'RESET':
        if bpy.ops.rl.reset.poll():
            bpy.ops.rl.reset('INVOKE_DEFAULT')

    elif item.id == 'RESET_ALL':
        if bpy.ops.rl.reset_all.poll():
            bpy.ops.rl.reset_all('INVOKE_DEFAULT')

    elif item.id == 'F6':
        if bpy.ops.screen.redo_last.poll():
            bpy.ops.screen.redo_last('INVOKE_DEFAULT')

    elif item.id == 'OVERVIEW':
        if bpy.ops.rl.overview.poll():
            bpy.ops.rl.overview('INVOKE_DEFAULT')

    elif item.id == 'HISTORY':
        if bpy.ops.rl.repeat_history.poll():
            bpy.ops.rl.repeat_history('INVOKE_DEFAULT')

    elif item.id == 'SKIP':
        if bpy.ops.rl.operator_skip.poll():
            bpy.ops.rl.operator_skip('INVOKE_DEFAULT')


class RL_OT_action_exec(StickyKey, bpy.types.Operator):
    bl_idname = "rl.action_exec"
    bl_label = "Execute Action"
    bl_description = "Execute action"
    bl_options = {'INTERNAL'}

    def get_hold_timeout(self):
        return 0.001 * prefs().hold_timeout

    def execute_release(self, context):
        exec_action(0)
        return {'FINISHED'}

    def execute_hold(self, context):
        exec_action(1)
        return {'FINISHED'}

    def execute_tweak(self, context):
        exec_action(2)
        return {'FINISHED'}

    def invoke(self, context, event):
        pr = prefs()
        if pr.actions[1].id == 'NONE' and pr.actions[2].id == 'NONE':
            self.invoke_mode = 'RELEASE'

        return StickyKey.invoke(self, context, event)


class RL_OT_action_select(bpy.types.Operator):
    bl_idname = "rl.action_select"
    bl_label = "Select Action (RL)"
    bl_description = "Click the button to select the action"
    bl_options = {'INTERNAL'}

    idx: bpy.props.IntProperty(default=-1, options={'SKIP_SAVE'})
    action: bpy.props.EnumProperty(
        items=cc.ACTION_ITEMS, options={'SKIP_SAVE'})
    target: bpy.props.EnumProperty(
        items=(
            ('HOTKEY', "", ""),
            ('PIE', "", ""),
        ),
        options={'SKIP_SAVE'})
    title: bpy.props.StringProperty(
        default="Select Action", options={'SKIP_SAVE'})

    def draw_action_select_menu(self, menu, context):
        pr = prefs()
        layout = menu.layout
        items = [item for item in cc.ACTION_ITEMS if item[2]]
        items.sort(key=lambda item: "" if item[0] == 'NONE' else item[1])

        if self.target == 'HOTKEY':
            target = pr.actions[self.idx]

        elif self.target == 'PIE':
            target = pr.pie_slots[self.idx]

        for item in items:
            if self.target == 'PIE' and item[0] == 'PIE':
                continue

            layout.prop_enum(
                target, "id", item[0],
                icon=ic('X') if item[0] == 'NONE' else 'NONE')

            if item[0] == 'NONE':
                layout.separator()

    def execute(self, context):
        pr = prefs()
        if self.target == 'HOTKEY':
            pr.actions[self.idx].id = self.action

        elif self.target == 'PIE':
            pr.pie_slots[self.idx].id = self.action

        tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.popup_menu(
            self.draw_action_select_menu, self.title)
        return {'FINISHED'}


class RL_OT_repeat_history(bpy.types.Operator):
    bl_idname = "rl.repeat_history"
    bl_label = "Repeat History (RL)"
    bl_description = "Repeat history\nShift+LMB - Rename Item"
    bl_options = {'INTERNAL'}

    idx: bpy.props.IntProperty(default=-2, options={'SKIP_SAVE'})

    def _draw_menu(self, menu, context):
        pr = prefs()
        layout = menu.layout
        layout.operator_context = 'INVOKE_DEFAULT'

        for i, item in enumerate(pr.rd.history):
            layout.operator(
                self.bl_idname,
                text="%i. %s" % (item.idx, item.label),
                icon=ic(ou.idname_to_icon(item.idname))).idx = i

        if pr.rd.history:
            layout.separator()

        if pr.last_redo_data.idname:
            item = pr.last_redo_data
            layout.operator(
                self.bl_idname,
                text=item.label,
                icon=ic(ou.idname_to_icon(item.idname))).idx = -1
            layout.separator()

        ao = context.active_operator
        text = "Add " + ou.idname_to_label(ao.bl_idname) if ao else \
            "No Active Operator"

        layout.operator(
            RL_OT_repeat_history_add.bl_idname,
            text=text, icon=ic('ZOOMIN'))

        if pr.rd.history:
            layout.operator(
                RL_OT_repeat_history_clear.bl_idname,
                text="Clear History", icon=ic('X'))

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.idx < -1:
            context.window_manager.popup_menu(
                self._draw_menu, "Repeat History")
        elif event.shift:
            bpy.ops.rl.repeat_history_rename('INVOKE_DEFAULT', idx=self.idx)
        else:
            prefs().rd.exec_history(self.idx)

        return {'FINISHED'}


class RL_OT_repeat_history_rename(bpy.types.Operator):
    bl_idname = "rl.repeat_history_rename"
    bl_label = "Rename"
    bl_options = {'INTERNAL'}
    bl_property = "pre"

    lock = False

    idx: bpy.props.IntProperty()

    def pre_update(self, context):
        if RL_OT_repeat_history_rename.lock:
            return
        self.name = self.pre

    pre: bpy.props.StringProperty(
        options={'SKIP_SAVE'}, update=pre_update)
    name: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def check(self, context):
        return True

    def draw(self, context):
        if not self.name:
            self.layout.prop(self, "pre", text="", icon=ic('TIME'))
        else:
            self.layout.prop(self, "name", text="", icon=ic('TIME'))

    def execute(self, context):
        prefs().rd.rename_history(self.idx, self.name)
        return {'FINISHED'}

    def invoke(self, context, modal):
        pr = prefs()
        if self.idx >= len(pr.rd.history):
            return {'CANCELLED'}

        RL_OT_repeat_history_rename.lock = True
        self.pre = pr.rd.history[self.idx].label
        RL_OT_repeat_history_rename.lock = False

        return context.window_manager.invoke_props_dialog(self)


class RL_OT_repeat_history_add(bpy.types.Operator):
    bl_idname = "rl.repeat_history_add"
    bl_label = "Add to Repeat History (RL)"
    bl_description = "Add to repeat history"
    bl_options = {'INTERNAL'}

    idx: bpy.props.IntProperty()

    def execute(self, context):
        lo.update()
        if lo.idname:
            prefs().rd.update_history()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_operator is not None


class RL_OT_repeat_history_clear(bpy.types.Operator):
    bl_idname = "rl.repeat_history_clear"
    bl_label = "Clear Repeat History (RL)"
    bl_description = "Clear repeat history"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        prefs().rd.clear_history()
        return {'FINISHED'}


class RL_OT_operator_skip(bpy.types.Operator):
    bl_idname = "rl.operator_skip"
    bl_label = "Skip Operator (RL)"
    bl_description = (
        "Skip the operator when using Repeat tool \n"
        "and try to repeat the previous operator")
    bl_options = {'INTERNAL'}

    def draw_operator_skip_menu(self, menu, context):
        pr = prefs()
        layout = menu.layout
        ao = context.active_operator
        if not ao:
            layout.label(text="No Active Operator", icon=ic('INFO'))
            return

        if ao.bl_idname in pr.operators:
            layout.label(text="Already in the Operators list", icon=ic('INFO'))
            return

        layout.operator(
            self.bl_idname, text="Skip Operator", icon=ic('GHOST_DISABLED'))

    def execute(self, context):
        pr = prefs()
        ao = context.active_operator
        if ao and ao.bl_idname not in pr.operators:
            item = pr.operators.add()
            item.name = ao.bl_idname
            item.skip = True
            pr.sort_operators()
            pr.update_filter_items()

        return {'FINISHED'}

    def invoke(self, context, event):
        ao = context.active_operator
        title = ou.idname_to_label(ao.bl_idname) if ao else "Skip Operator"
        context.window_manager.popup_menu(
            self.draw_operator_skip_menu, title)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_operator is not None


class RL_OT_item_add(bpy.types.Operator):
    bl_idname = "rl.item_add"
    bl_label = "Add Operator (RL)"
    bl_description = "Add operator"
    bl_options = {'INTERNAL'}
    bl_property = "operator"

    idx: bpy.props.IntProperty(default=-1, options={'SKIP_SAVE'})

    def get_items(self, context):
        if not hasattr(self.__class__, "enum_items"):
            enum_items = []
            for op_module_name in dir(bpy.ops):
                op_module = getattr(bpy.ops, op_module_name)
                for op_submodule_name in dir(op_module):
                    op = getattr(op_module, op_submodule_name)
                    op_name = ou.get_rna_type(op).name

                    label = op_name or op_submodule_name
                    if op_submodule_name != label:
                        label = "[%s] %s (%s)" % (
                            op_module_name.upper(), label, op_submodule_name)
                    else:
                        label = "[%s] %s" % (
                            op_module_name.upper(),
                            label.replace("_", " ").title())

                    enum_items.append((
                        "%s.%s" % (op_module_name, op_submodule_name),
                        label, ""))

            self.__class__.enum_items = enum_items

        return self.__class__.enum_items

    operator: bpy.props.EnumProperty(items=get_items)

    def execute(self, context):
        op_module_name, _, op_submodule_name = self.operator.partition(".")
        op_module = getattr(bpy.ops, op_module_name)
        op = getattr(op_module, op_submodule_name)
        op_type_name = op.idname()

        pr = prefs()
        pr.get_operator(op_type_name)

        tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


class RL_OT_item_remove(
        bpy.types.Operator, cu.RemoveItemOperator):
    label_prop = "label"
    bl_idname = "rl.item_remove"
    bl_options = {'INTERNAL'}

    def get_collection(self):
        return prefs().operators

    def get_idx_data(self):
        return prefs()

    def get_idx_prop(self):
        return "operators_idx"

    def finish(self):
        prefs().update_filter_items()


def add_prop():
    pr = prefs()
    key = pr.default_prop_mode
    hotkeys = (
        "Ctrl+", "Shift+", "Alt+", "OSKey+",
        "Ctrl+Shift+", "Ctrl+Alt+", "Ctrl+OSKey+",
        "Shift+Alt+", "Shift+OSKey+",
        "Alt+OSKey+",
        "Ctrl+Shift+Alt+", "Ctrl+Shift+OSKey+",
        "Ctrl+Alt+OSKey+", "Shift+Alt+OSKey+",
        "Ctrl+Shift+Alt+OSKey+",
    )

    op = pr.selected_operator
    prop = op.props.add()
    prop_hk = prop.hotkey
    # repeat_hk = pr.repeat_global_hk

    hotkey_idx = (len(op.props) - 1) % len(hotkeys)
    hotkey = hotkeys[hotkey_idx]
    hotkey = "PRESS:%s%s" % (hotkey, key)
    prop_hk.decode(hotkey)

    # if repeat_hk.key in {'NONE', 'WHEELUPMOUSE'} and \
    #         prop_hk.key == 'NONE' and \
    #         repeat_hk.ctrl == prop_hk.ctrl and \
    #         repeat_hk.shift == prop_hk.shift and \
    #         repeat_hk.alt == prop_hk.alt and \
    #         repeat_hk.oskey == prop_hk.oskey and \
    #         repeat_hk.key_mod == prop_hk.key_mod:
    #     hotkey_idx += 1
    #     hotkey_idx %= len(hotkeys)
    #     hotkey = hotkeys[hotkey_idx]
    #     hotkey = "PRESS:%s%s" % (hotkey, key)
    #     prop_hk.decode(hotkey)

    props = pdu.OperatorData(op.name).prop_data
    data = None
    for k, v in props.items():
        if k == cc.PREPEAT:
            continue

        for data in v:
            prop.data = data.id
            prop.group = data.group
            prop.step = data.step if data.is_number else 1
            break
        if data:
            break


class RL_OT_prop_hotkey_add(bpy.types.Operator):
    bl_idname = "rl.prop_hotkey_add"
    bl_label = "Add Property Hotkey (RL)"
    bl_description = "Add property hotkey"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        add_prop()
        return {'FINISHED'}


class RL_OT_prop_hotkey_remove(bpy.types.Operator):
    bl_idname = "rl.prop_hotkey_remove"
    bl_label = "Remove Property Hotkey (RL)"
    bl_description = "Remove property hotkey"
    bl_options = {'INTERNAL'}

    idx: bpy.props.IntProperty()

    def execute(self, context):
        op = prefs().selected_operator
        op.props.remove(self.idx)
        return {'FINISHED'}


class RL_OT_prop_hotkey_select(bpy.types.Operator):
    bl_idname = "rl.prop_hotkey_select"
    bl_label = "New Hotkey"
    bl_description = "Select hotkey"
    bl_options = {'INTERNAL'}

    items = None

    idx: bpy.props.IntProperty(default=-1, options={'SKIP_SAVE'})
    default: bpy.props.BoolProperty(
        name="Use as Default Hotkey", description="Use as default hotkey",
        options={'SKIP_SAVE'})

    mode: bpy.props.StringProperty(
        name="Mode", description="Mode", options={'SKIP_SAVE'})

    def key_update(self, context):
        if self.key in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            self.key = 'NONE'

    key: bpy.props.EnumProperty(
        name="Key", description="Key", items=cc.KEY_ITEMS,
        options={'SKIP_SAVE'}, update=key_update)
    target: bpy.props.EnumProperty(
        items=(
            ('REDO', "", ""),
            ('REPEAT', "", ""),
        ),
        options={'SKIP_SAVE'})

    def cancel(self, context):
        pass

    def _draw_menu(self, menu, context):
        layout = menu.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        pr = prefs()

        if self.key != 'NONE':
            col.prop(self, "default", toggle=True)

        operator(
            layout, self.bl_idname, "Mouse Wheel",
            ic(cc.IC_WHEEL),
            idx=self.idx, target=self.target, key='NONE', mode='SET')

        for key in pr.custom_keys:
            operator(
                layout, self.bl_idname,
                layout.enum_item_name(
                    self, "key", key), ic(cc.IC_KEY_MOVE),
                idx=self.idx, target=self.target, key=key, mode='SET')

        layout.separator()
        operator(
            layout, self.bl_idname, "New Sticky Hotkey",
            ic('ZOOMIN'), idx=self.idx, target=self.target, mode='NEW')

    def check(self, context):
        return True

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.prop(self, "key", text="", event=True)
        if self.key != 'NONE' and self.target == 'REDO':
            col.prop(self, "default", toggle=True)

    def execute(self, context):
        pr = prefs()
        if self.idx != -1:
            op = pr.selected_operator
            prop = op.props[self.idx]
            prop.hotkey.key = self.key

        if self.key != 'NONE' and self.key not in pr.custom_keys:
            pr.add_key(self.key)

        if self.target == 'REDO':
            if self.default or self.idx == -1:
                pr.default_prop_mode = self.key

        elif self.target == 'REPEAT':
            pr.repeat_global_hk.key = self.key

        tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.mode:
            context.window_manager.popup_menu(
                self._draw_menu, "Select Hotkey")
            return {'FINISHED'}

        elif self.mode == 'NEW':
            return context.window_manager.invoke_props_dialog(
                self, width=round(200 * uprefs().view.ui_scale))

        return self.execute(context)


def draw_prop(layout, prop, od, i):
    pr = prefs()
    split = layout.split(factor=0.5, align=True)
    row = split.row(align=True)

    if len(prop.bl_rna.properties["prop"].enum_items) == 0:
        pr.update_operator()

    pd = od.get_prop_data(prop.group, prop.data)
    if not pd:
        sub = row.row(align=True)
        sub.alert = True
        operator(
            sub, RL_OT_help.bl_idname,
            "'%s' Property Not Found" % prop.data, ic('ERROR'),
            mode='MSG',
            title="Property Not Found",
            msg=prop.data)

    else:
        row.prop(prop, "prop", text="")

        row.prop(
            prop.hotkey, "ctrl", text="", icon_value=icons.get_icon("ctrl"),
            toggle=True)
        row.prop(
            prop.hotkey, "shift", text="", icon_value=icons.get_icon("shift"),
            toggle=True)
        row.prop(
            prop.hotkey, "alt", text="", icon_value=icons.get_icon("alt"),
            toggle=True)
        row.prop(
            prop.hotkey, "oskey", text="", icon_value=icons.get_icon("oskey"),
            toggle=True)

        row = split.row(align=True)
        sub_split = row.split(factor=0.5, align=True)
        row = sub_split.row(align=True)
        # row.prop(prop, "custom", text="")
        if prop.hotkey.key == 'NONE':
            name, icon = "Mouse Wheel", cc.IC_WHEEL
        else:
            row.prop(
                prop, "use_click", text="",
                icon=cc.IC_KEY_CLICK if prop.use_click else cc.IC_KEY_MOVE,
                toggle=True)
            name, icon = layout.enum_item_name(
                prop.hotkey, "key", prop.hotkey.key), 'NONE'
        operator(
            row,
            RL_OT_prop_hotkey_select.bl_idname,
            name, icon,
            idx=i)

        row = sub_split.row(align=True)
        sub = row
        if prop.data == cc.PREPEAT:
            sub = row.row(align=True)
            sub.enabled = False

        if pd.type == 'FLOAT':
            if pd.subtype == 'ANGLE':
                sub.prop(prop, "step_angle")
            else:
                sub.prop(prop, "step")
        else:
            sub.prop(prop, "step_int")

    operator(row, RL_OT_prop_hotkey_remove.bl_idname, "", 'X', idx=i)


def draw_operator(layout, popup=True):
    pr = prefs()
    op = pr.selected_operator

    if not ou.check_idname(op.name):
        layout.box().label(text="%s not found" % op.name, icon=ic('INFO'))
        return

    layout = layout.column(align=True)

    od = pdu.OperatorData(op.name)

    row = layout.box().row()
    sub = row.row()
    sub.alignment = 'LEFT'
    sub.label(text=od.label, icon=ic(od.icon))
    sub.label(text="%d Supported Properties" % od.num_props, icon=ic('GROUP'))

    sub = row.row(align=True)
    sub.alignment = 'RIGHT'
    sub.operator(
        RL_OT_help.bl_idname, text="",
        icon=ic('QUESTION'), emboss=False)

    col = layout.box().column(align=True)
    sub = col.column(align=True)
    for i, prop in enumerate(op.props):
        draw_prop(sub, prop, od, i)

    row = col.row(align=True)
    row.enabled = len(pr.prop_enum_items) > 0
    operator(row, RL_OT_prop_hotkey_add.bl_idname, "Add Hotkey")

    if not popup:
        if pr.redo_settings:
            col = pr.scaled_col(layout.box(), 1.2)

            if pr.custom_keys:
                pr.hlabel(
                    col, "Default Hotkey:",
                    msg="The hotkey that will be used by default "
                    "in the property list above")
                name, icon = pr.get_prop_mode_data()
                operator(col, RL_OT_prop_hotkey_select.bl_idname, name, icon)

                col.separator()

            col.prop(pr, "looping")
            col.prop(pr, "default_step_float")

        layout.prop(pr, "redo_settings", text="Settings", toggle=True)


class RL_OT_reset(bpy.types.Operator):
    bl_idname = "rl.reset"
    bl_label = "Reset Properties (RL)"
    bl_description = "Redo last operator using default values"
    bl_options = {'REGISTER'}

    def clear_props(self, operator, group=""):
        macros = getattr(operator, "macros", None)
        if macros:
            for m in macros:
                self.clear_props(m, m.bl_idname)

        else:
            for k in operator.properties.keys():
                p = "%s.%s" % (group, k) if group else k

                if p not in self.props:
                    continue

                del operator.properties[k]

    def execute(self, context):
        ao = context.active_operator
        pr = prefs()
        self.op = pr.operators.get(ao.bl_idname, None)
        if not ao or not self.op:
            return {'CANCELLED'}

        self.od = pdu.OperatorData(self.op.name)
        self.props = set()
        for p in self.op.props:
            self.props.add("%s.%s" % (p.group, p.data) if p.group else p.data)

        self.clear_props(ao)

        bpy.ops.ed.undo_redo(True)

        text = self.od.label + "\n\tReset Properties"
        props = []

        if props:
            text += "\n" + "\n".join(props)
        bpy.ops.rl.overlay(
            text=text,
            duration=min(9, max(3, 0.6 * pr.overlay.duration * len(props))))

        pr.rd.reset()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        pr = prefs()
        ao = context.active_operator
        return ao is not None and ao.bl_idname in pr.operators and \
            bpy.ops.ed.undo_redo.poll()


class RL_OT_reset_all(bpy.types.Operator):
    bl_idname = "rl.reset_all"
    bl_label = "Reset All Properties (RL)"
    bl_description = "Redo last operator using default values"
    bl_options = {'INTERNAL'}

    def clear_props(self, operator):
        for k in operator.properties.keys():
            del operator.properties[k]

        macros = getattr(operator, "macros", None)
        if macros:
            for m in macros:
                self.clear_props(m)

    def execute(self, context):
        ao = context.active_operator
        if not ao:
            return {'CANCELLED'}

        self.clear_props(ao)

        bpy.ops.ed.undo_redo(True)
        bpy.ops.rl.overlay(
            text="%s\n\tReset All Properties" %
            ou.idname_to_label(ao.bl_idname))

        prefs().rd.reset()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_operator is not None and \
            bpy.ops.ed.undo_redo.poll()


class RL_OT_edit(bpy.types.Operator):
    bl_idname = "rl.edit"
    bl_label = "Re-Last Operator Editor"
    bl_description = "Re-Last operator editor"
    bl_options = {'REGISTER', 'UNDO'}

    save_settings: bpy.props.BoolProperty(
        name="Save User Settings", description="Save user settings",
        options={'SKIP_SAVE'})
    mode: bpy.props.StringProperty(options={'SKIP_SAVE'})
    idname: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def check(self, context):
        return True

    def draw(self, context):
        layout = self.layout

        if not lo.idname:
            layout.box().label(text="No active operator", icon=ic('INFO'))
            return

        draw_operator(layout)

        # if not self.always_save_settings:
        if True:
            row = self.layout.row(align=True)
            row.prop(
                self, "save_settings", toggle=True,
                icon=ic('FILE_TICK' if self.save_settings else 'BLANK1'))

            # if self.save_settings:
            #     row.prop(
            #         prefs(), "always_save_settings", text="", toggle=True,
            #         icon='SAVE_PREFS')

    def cancel(self, context):
        if self.is_new:
            pr = prefs()
            if lo.idname and lo.idname in pr.operators:
                cu.remove_item_by(
                    pr.operators, "name", lo.idname, pr, "operators_idx")

                tag_redraw()

    def execute(self, context):
        # if self.save_settings or prefs().always_save_settings:
        if self.save_settings:
            bpy.ops.wm.save_userpref()

        tag_redraw()
        return {'CANCELLED'}

    def invoke(self, context, event):
        pr = prefs()
        # self.always_save_settings = pr.always_save_settings

        self.is_new = None
        lo.update(self.idname)
        if lo.idname:
            self.is_new = lo.idname not in pr.operators
            pr.get_operator(lo.idname)

        context.window.cursor_warp(
            context.window.width >> 1, int(1.5 * context.window.height) >> 1)
        return context.window_manager.invoke_props_dialog(
            self, width=round(500 * uprefs().view.ui_scale))

    # @classmethod
    # def poll(cls, context):
    #     return context.active_operator is not None


class RL_OT_edit_reset(StickyKey, bpy.types.Operator):
    bl_idname = "rl.edit_reset"
    bl_label = "Edit/Reset Operator (RL)"
    bl_options = {'INTERNAL'}

    def get_hold_timeout(self):
        return 0.001 * prefs().hold_timeout

    def execute_release(self, context):
        # bpy.ops.rl.reset('INVOKE_DEFAULT')
        return {'FINISHED'}

    def execute_hold(self, context):
        bpy.ops.rl.edit('INVOKE_DEFAULT')
        return {'CANCELLED'}


class RL_OT_edit_reset_macro(bpy.types.Macro):
    bl_idname = "rl.edit_reset_macro"
    bl_label = "Edit/Reset Operator (RL)"
    bl_options = {'MACRO', 'INTERNAL'}


class RL_OT_redo(bpy.types.Operator):
    bl_idname = "rl.redo"
    bl_label = "Redo (RL)"
    bl_description = "Redo the last operator"
    bl_options = {'MACRO', 'INTERNAL'}

    delta: bpy.props.IntProperty(options={'SKIP_SAVE'})
    key: bpy.props.StringProperty(default='NONE', options={'SKIP_SAVE'})

    def change_value(self):
        if lo.func:
            op = bpy.context.active_operator
            ao_props = lo.ao_props
            if op and op.macros:
                op = op.macros.get(self.prop_data.group, None)
                ao_props = ao_props[self.prop_data.group]

            if not op:
                return

            self.value = getattr(
                op.properties,
                self.prop_data.id, self.prop_data.default)

            # if self.prop_data.group in ao_props:
            #     ao_props = ao_props[self.prop_data.group]

            # if self.prop_data.id in ao_props:
            #     self.value = ao_props[self.prop_data.id]
            # else:
            #     self.value = self.prop_data.default

        if self.prop_data.type == 'BOOLEAN':
            if prefs().looping or self.prop.use_click:
                self.value = not self.value
            else:
                step = self.prop_data.step or 1
                self.value = self.delta * step > 0

        elif self.prop_data.type == 'ENUM':
            step = self.prop_data.step or 1
            self.value = lo.change_enum_value(
                self.prop_data, self.value, self.delta * step,
                prefs().looping or self.prop.use_click)

        else:
            self.value += self.delta * self.prop_data.step

            if self.value < self.prop_data.min:
                self.value = self.prop_data.min
            elif self.value > self.prop_data.max:
                self.value = self.prop_data.max

        if lo.func:
            ao_props[self.prop_data.id] = self.value

        try:
            setattr(op.properties, self.prop_data.id, self.value)
        except:
            pass

    def round_value(self, value, step):
        # step = abs(step)
        # ndigits = 0
        # if step != 0:
        #     step = step % 1
        #     while step < 1 or round(step % 1 * 10) % 10 != 0:
        #         step *= 10
        #         ndigits += 1

        ndigits = 4
        svalue = "%%.%df" % ndigits
        svalue = svalue % value
        return svalue

    def draw_value(self):
        if not prefs().overlay:
            return

        if self.prop_data.type == 'INT':
            svalue = str(int(self.value))

        elif self.prop_data.type == 'FLOAT':
            svalue = self.value
            if self.prop_data.subtype == 'ANGLE':
                svalue = 180 * svalue / pi

            svalue = self.round_value(svalue, self.prop_data.step)

            if self.prop_data.subtype == 'ANGLE':
                svalue = str(svalue) + "°"

        elif self.prop_data.type == 'ENUM':
            if len(lo.enum_items):
                svalue = lo.enum_items[lo.enum_idx][1]
            else:
                svalue = str(self.value) + "*"

        elif self.prop_data.type == 'BOOLEAN':
            svalue = "On" if self.value else "Off"

        else:
            svalue = "?"

        bpy.ops.rl.overlay(
            text="%s\n%s: \t%s" % (lo.label, self.prop_data.label, svalue))

    def redo_last(self):
        DBG and logw("Redo Last")

        ao = bpy.context.active_operator
        is_first_redo = ao and lou.LastOperator.bl_lo != ao

        if not is_first_redo:
            self.delta = 0

        self.change_value()
        self.draw_value()

        if bpy.ops.ed.undo_redo.poll():
            bpy.ops.ed.undo_redo(True)
            prefs().last_redo_data.update(lo)

    def repeat_last(self):
        DBG and logw("Repeat Last")
        pr = prefs()

        if self.delta < 0:
            if not pr.rd.check():
                pr.rd.reset()
                return

            if pr.rd.idx > 1:
                bpy.ops.ed.undo()
                bpy.ops.ed.undo()
                lo.func('EXEC_DEFAULT', True, **lo.ao_props)
                pr.rd.update(-1)
        else:
            if not pr.rd.check():
                bpy.ops.ed.undo_push()
                pr.rd.reset()

            lo.func('EXEC_DEFAULT', True, **lo.ao_props)
            # bpy.ops.screen.repeat_last(True)
            pr.rd.update(1)

        bpy.ops.rl.overlay(
            text="%s\nRepeat: \tx%i" % (lo.label, pr.rd.idx))

    # @classmethod
    # def poll(cls, context):
    #     return bpy.ops.ed.undo_redo.poll()

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        DBG and logh("Re-Last")

        self.event = event
        pr = prefs()

        repeat_mode = False
        ao = context.active_operator
        if not ao:
            if pr.repeat and pr.repeat_global_hk.check_event(event, key=False):
                # if pr.rd.history:
                #     pr.rd.exec_history(0)
                return {'CANCELLED'}
            else:
                DBG and logw("AO is None")
                return {'PASS_THROUGH'}

        elif ao.bl_idname in pr.operators:
            self.prop, self.prop_data = \
                pr.operators[ao.bl_idname].get_prop_data(
                    self.event, self.key)
            if not self.prop_data:
                if pr.repeat and pr.repeat_global_hk.check_event(
                        event,
                        key=pr.repeat_global_hk.key not in (
                        'NONE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE')):
                    repeat_mode = True
                else:
                    DBG and logw("Not prop_data")
                    return {'PASS_THROUGH'}

        elif pr.repeat and pr.repeat_global_hk.check_event(
                event,
                key=pr.repeat_global_hk.key not in (
                'NONE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE')):
            repeat_mode = True

        else:
            DBG and logw("AO (%s) is not registered" % ao.bl_idname)
            return {'PASS_THROUGH'}

        lo.update(repeat_mode=repeat_mode)
        if not lo.idname:
            DBG and logw("!lo.idname")
            return {'PASS_THROUGH'}

        # if self.prop_data.id == cc.PREPEAT:
        if repeat_mode:
            self.repeat_last()
        else:
            self.redo_last()
            pr.rd.reset()
        # self.redo_last(selection_state.check())
        # selection_state.update()

        return {'CANCELLED'}


class RL_OT_modal(bpy.types.Operator):
    bl_idname = "rl.modal"
    bl_label = "Re-Last"
    bl_options = {'INTERNAL', 'BLOCKING', 'GRAB_CURSOR'}

    def execute(self, context):
        return {'FINISHED'}

    def modal(self, context, event):
        pr = prefs()
        mouse = event.mouse_x if pr.custom_mode == 'H' else event.mouse_y
        if event.type == 'MOUSEMOVE' and mouse == self.last_mouse:
            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE':
            if abs(mouse - self.last_mouse) > pr.get_threshold(
                    self.prop_data):
                delta = 1 if mouse > self.last_mouse else -1
                self.last_mouse = mouse
                bpy.ops.rl.redo(
                    'INVOKE_DEFAULT', True, delta=delta, key=self.key)

        if event.value == 'RELEASE':
            if event.type == self.key:
                return {'CANCELLED'}

            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        pr = prefs()
        self.last_mouse = \
            event.mouse_x if pr.custom_mode == 'H' else event.mouse_y
        self.key = event.type
        self.prop_data = None

        ao = context.active_operator
        if not ao:
            return {'PASS_THROUGH'}

        elif ao.bl_idname in pr.operators:
            prop, self.prop_data = pr.operators[ao.bl_idname].get_prop_data(
                event, self.key)
            if not self.prop_data:
                if pr.repeat and pr.repeat_global_hk.check_event(event):
                    pass
                else:
                    return {'PASS_THROUGH'}

            if prop and prop.use_click:
                bpy.ops.rl.redo(
                    'INVOKE_DEFAULT', True, delta=1, key=self.key)

        elif pr.repeat and pr.repeat_global_hk.check_event(event):
            pass

        else:
            return {'PASS_THROUGH'}

        lo.update()
        if not lo.idname:
            return {'PASS_THROUGH'}

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class RL_OT_overview(bpy.types.Operator):
    bl_idname = "rl.overview"
    bl_label = "Hotkey Overview"
    bl_description = "Hotkey overview"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        pr = prefs()
        ao = context.active_operator
        if not ao or ao.bl_idname not in pr.operators:
            return {'CANCELLED'}

        op = pr.operators[ao.bl_idname]
        od = pdu.OperatorData(op.name)
        text = od.label
        props = []
        for p in op.props:
            pd = od.get_prop_data(p.group, p.data)
            props.append("\t%s\t%s" % (p.hotkey.to_ui_string(), pd.label))

        if props:
            text += "\n" + "\n".join(props)
        bpy.ops.rl.overlay(
            text=text,
            duration=min(9, max(3, 0.6 * pr.overlay.duration * len(props))))
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        pr = prefs()
        ao = context.active_operator
        return ao is not None and ao.bl_idname in pr.operators


class RL_OT_export(bpy.types.Operator, ExportHelper):
    bl_idname = "rl.export"
    bl_label = "Export Preferences"
    bl_description = "Export preferences"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    filename_ext = ".json"
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', default="*.json")
    filter_glob: bpy.props.StringProperty(
        default="*.json", options={'HIDDEN'})

    def export_data(self, filepath):
        data = property_utils.to_dict(
            prefs(), None, True, include={"operators"})

        try:
            with open(self.filepath, 'w') as f:
                f.write(json.dumps(
                    data, indent=2, separators=(", ", ": "), sort_keys=True))
        except:
            pass

    def execute(self, context):
        if not self.filepath.endswith(".json"):
            self.filepath += ".json"
        prefs().export_filepath = self.filepath

        self.export_data(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = prefs().export_filepath
        if not self.filepath:
            self.filepath = "re-last.json"

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class RL_OT_import(bpy.types.Operator, ImportHelper):
    bl_idname = "rl.import"
    bl_label = "Import Preferences"
    bl_description = "Import preferences"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    filename_ext = ".json"
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', default="*.json")
    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement)
    filter_glob: bpy.props.StringProperty(
        default="*.json", options={'HIDDEN'})
    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    def import_data(self, filepath):
        try:
            with open(filepath, 'r') as f:
                s = f.read()
        except:
            self.report({'WARNING'}, "Bad file")
            return

        data = None
        try:
            data = json.loads(s)
        except:
            self.report({'WARNING'}, "Bad json")
            return

        if data:
            if not isinstance(data, dict):
                self.report({'WARNING'}, "Bad json")
                return

            pr = prefs()
            for opd in data["operators"]:
                if opd["name"] in pr.operators:
                    continue

                op = pr.operators.add()
                op.name = opd["name"]
                op.skip = opd.get("skip", False)
                for propd in opd["props"]:
                    prop = op.props.add()
                    prop.hotkey.decode(propd["hotkey"])
                    prop.data = propd["data"]
                    prop.group = propd["group"]
                    prop.step = propd["step"]
                    if "use_click" in propd:
                        prop.use_click = propd["use_click"]

            pr.sort_operators()
            pr.update_filter_items()

    def execute(self, context):
        for f in self.files:
            filepath = os.path.join(self.directory, f.name)
            if os.path.isfile(filepath):
                self.import_data(filepath)
                break

        prefs().import_filepath = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = prefs().import_filepath
        if not self.filepath:
            self.filepath = "re-last.json"

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class RL_OT_context_menu(bpy.types.Operator):
    bl_idname = "rl.context_menu"
    bl_label = ""
    bl_description = ""
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return hasattr(context, "button_operator")

    def execute(self, context):
        button_operator = getattr(context, "button_operator", None)
        if button_operator:
            idname = button_operator.__class__.__name__
            bpy.ops.rl.edit('INVOKE_DEFAULT', idname=idname)

        return {'FINISHED'}


def register():
    RL_OT_edit_reset_macro.define("RL_OT_edit_reset")
    RL_OT_edit_reset_macro.define("RL_OT_reset")
