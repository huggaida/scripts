import bpy
from pprint import pformat
from .. import constants as cc
from ..utils.debug_utils import *
from ..utils import operator_utils as ou
from ..addon import prefs


class LastOperator:
    bl_lo = None

    def __init__(self):
        self.ao_props = {}
        self.idname = None

    def update(self, idname=None, operator=None, repeat_mode=False):
        self.clear()

        if repeat_mode:
            self.from_operators()

        elif idname:
            self.from_idname(idname, operator)

        elif bpy.context.active_operator:
            self.from_active(bpy.context.active_operator)

        DBG and logi(str(self))

    def __str__(self):
        return "[%s] %s" % (('OP', 'MACRO')[self.is_macro], self.idname)

    def clear(self):
        self.idname = None
        self.func = None
        self.script = None
        self.enum_items = None
        self.is_macro = False
        self.ao_props.clear()

    def parse_props(self, operator):
        if not operator:
            return

        self.is_macro = len(operator.macros) > 0
        if getattr(operator, "macros", None):
            for m in operator.macros:
                self.ao_props[m.bl_idname] = d = {}

                for k in m.properties.keys():
                    v = getattr(m.properties, k)
                    value = ou.to_py_value(m, k, v)
                    if value is None or isinstance(value, dict) and not value:
                        continue

                    d[k] = value

        else:
            for k in operator.properties.keys():
                v = getattr(operator.properties, k)
                value = ou.to_py_value(operator, k, v)
                if value is None or isinstance(value, dict) and not value:
                    continue

                self.ao_props[k] = value

        DBG and logi(pformat(self.ao_props, compact=True))

    def from_idname(self, idname, operator):
        if not ou.check_idname(idname):
            return

        self.idname = idname
        self.idname_py = ou.to_bl_idname(idname)
        self.tp = ou.get_rna_type(self.idname_py)
        self.label = getattr(self.tp, "bl_label", None) or \
            self.tp.name or idname
        self.modname, self.name = ou.split_idname_py(self.idname_py)
        self.func = getattr(getattr(bpy.ops, self.modname), self.name)

        self.parse_props(operator)

    def from_active(self, ao):
        if not ou.check_idname(ao.bl_idname):
            return

        self.from_idname(ao.bl_idname, ao)

    def from_operators(self):
        pr = prefs()
        for op in reversed(bpy.context.window_manager.operators):
            if 'REGISTER' not in op.bl_options:
                continue

            func = ou.idname_to_operator(ou.to_bl_idname(op.bl_idname))
            if not func or not func.poll():
                continue

            if pr.rd.check_operator(op.bl_idname):
                self.from_active(op)
                break

    def change_enum_value(self, prop_data, value, delta, loop):
        self.enum_idx = 0

        if self.enum_items is None:
            if hasattr(self.tp, "bl_idname"):
                _, args = getattr(self.tp, prop_data.id)
                self.enum_items = list(
                    (item[0], item[1]) for item in args["items"])
            else:
                bl_props = self.tp.properties
                if prop_data.group != cc.PGROUP:
                    rna_type = ou.get_rna_type(prop_data.group)
                    bl_props = rna_type.properties
                self.enum_items = list(
                    (item.identifier, item.name)
                    for item in bl_props[prop_data.id].enum_items)

        if not len(self.enum_items):
            return value

        is_set = isinstance(value, set)
        if is_set:
            if value:
                value = next(iter(value))

        if value:
            for i, item in enumerate(self.enum_items):
                if item[0] == value:
                    self.enum_idx = i
                    break

        self.enum_idx += delta
        if loop:
            self.enum_idx %= len(self.enum_items)
        else:
            self.enum_idx = \
                min(max(self.enum_idx, 0), len(self.enum_items) - 1)

        return {self.enum_items[self.enum_idx][0]} if is_set else \
            self.enum_items[self.enum_idx][0]


last_operator = LastOperator()
