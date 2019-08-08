import bpy
from .. import constants as cc
from ..utils.debug_utils import *
from ..utils import operator_utils as ou
from ..addon import prefs


class PropData:

    def __init__(
            self, type, subtype, id, label, description, group,
            default=None, min=0, max=0, step=1, resettable=True):
        self.type = type
        self.subtype = subtype
        self.is_number = type == 'INT' or type == 'FLOAT'
        self.id = id
        self.label = label or id
        self.description = description
        self.group = group
        self.default = default
        if not default:
            if type == 'INT' or type == 'FLOAT':
                self.default = 0
            elif type == 'STRING':
                self.default = ""
        self.min = min
        self.max = max
        self.step = step
        self.resettable = resettable

    def __str__(self):
        if self.type == 'INT' or self.type == 'FLOAT':
            return "[PD:%s %s.%s '%s' (%f<%s<%f) <%f>]" % (
                self.type, self.group, self.id, self.label,
                self.min, str(self.default), self.max, self.step)
        return "[PD:%s %s.%s '%s' (%s)]" % (
            self.type, self.group, self.id, self.label, str(self.default))

    def __repr__(self):
        return self.__str__()

    def clone(self):
        return PropData(
            self.type, self.subtype, self.id, self.label, self.description,
            self.group, self.default, self.min, self.max, self.step,
            self.resettable)


def _is_resetable_bl(bl_prop):
    return not bl_prop.is_hidden


def _is_resetable_addon(args):
    return "options" not in args or 'HIDDEN' not in args["options"]


def _gen_repeat_prop_data():
    return PropData(
        'REPEAT',
        None,
        'REPEAT',
        "Repeat",
        "Repeat",
        "REPEAT",
        1,
        1,
        10000,
        1,
        False
    )


def _get_prop_data_bl(idname, all_props=False, props=None, group=cc.PGROUP):
    pr = prefs()

    num_props = 0
    has_pointer = False
    if props is None:
        props = {
            cc.PGROUP: [],
            cc.PREPEAT: [_gen_repeat_prop_data()]
        }

    supported_types = {'INT', 'FLOAT', 'BOOLEAN', 'ENUM'}
    number_types = {'INT', 'FLOAT'}

    rna_type = ou.get_rna_type(ou.to_bl_idname(idname))
    for bl_prop in rna_type.properties:
        if bl_prop.identifier == "rna_type":
            continue

        if bl_prop.type == 'POINTER':
            if "_OT_" not in bl_prop.identifier:
                continue
            has_pointer = True
            props[bl_prop.identifier] = []
            _, n, _ = _get_prop_data_bl(
                bl_prop.identifier, all_props, props, bl_prop.identifier)
            num_props += n

        elif bl_prop.type in supported_types:
            if bl_prop.is_hidden:
                continue
            if hasattr(bl_prop, "default_array") and \
                    len(bl_prop.default_array) > 1:
                if all_props:
                    props[group].append(PropData(
                        bl_prop.type,
                        bl_prop.subtype,
                        bl_prop.identifier,
                        bl_prop.name,
                        bl_prop.description,
                        group,
                        bl_prop.default_array,
                        resettable=_is_resetable_bl(bl_prop)))
                    continue
                else:
                    continue

            # if bl_prop.type == 'ENUM' and bl_prop.default == "":
            #     continue

            if bl_prop.type in number_types:
                props[group].append(PropData(
                    bl_prop.type,
                    bl_prop.subtype,
                    bl_prop.identifier,
                    bl_prop.name,
                    bl_prop.description,
                    group,
                    bl_prop.default, bl_prop.soft_min, bl_prop.soft_max,
                    # bl_prop.step * 0.01 if bl_prop.type == 'FLOAT' else
                    pr.default_step_float if bl_prop.type == 'FLOAT' else
                    bl_prop.step,
                    resettable=_is_resetable_bl(bl_prop)))
            else:
                props[group].append(PropData(
                    bl_prop.type,
                    bl_prop.subtype,
                    bl_prop.identifier,
                    bl_prop.name,
                    bl_prop.description,
                    group,
                    bl_prop.default,
                    resettable=_is_resetable_bl(bl_prop)))

            num_props += 1

        elif all_props:
            props[group].append(PropData(
                bl_prop.type,
                bl_prop.subtype,
                bl_prop.identifier,
                bl_prop.name,
                bl_prop.description,
                group,
                bl_prop.default,
                resettable=_is_resetable_bl(bl_prop)))

    if has_pointer and cc.PGROUP in props:
        del props[cc.PGROUP]

    return props, num_props, has_pointer


def _get_prop_data_addon(idname, all_props=False, props=None, group=cc.PGROUP):
    num_props = 0
    has_pointer = False
    if props is None:
        props = {
            cc.PGROUP: [],
            cc.PREPEAT: [_gen_repeat_prop_data()]
        }

    number_funcs = {bpy.props.IntProperty, bpy.props.FloatProperty}
    enum_funcs = {bpy.props.EnumProperty, bpy.props.BoolProperty}

    tp = getattr(bpy.types, idname)
    if issubclass(tp, bpy.types.Macro):
        op_idname = tp.bl_idname
        op = eval("bpy.ops.%s" % op_idname)
        rna = op.get_rna()
        for k in dir(rna):
            ktp = hasattr(bpy.types, k) and getattr(bpy.types, k)
            is_op = ktp and issubclass(ktp, (
                bpy.types.Operator, bpy.types.OperatorProperties))

            if is_op:
                props[k] = []
                # if hasattr(ktp, "bl_idname"):
                if False:
                    d, n, _ = _get_prop_data_addon(k, all_props, props, k)
                else:
                    d, n, _ = _get_prop_data_bl(k, all_props, props, k)

                num_props += n

        del props[cc.PGROUP]
        return props, num_props, True

    for pname in tp.order:
        p = getattr(tp, pname)
        if not isinstance(p, tuple):
            continue

        if len(p) != 2:
            continue

        func, args = p
        subtype = 'NONE'

        if "options" in args and 'HIDDEN' in args["options"]:
            continue

        if func in number_funcs:
            number_type = 'INT' if func == bpy.props.IntProperty else 'FLOAT'
            step = args["step"] if "step" in args else 1
            if "subtype" in args:
                subtype = args["subtype"]
            if number_type == 'FLOAT':
                step *= 0.01
            props[group].append(PropData(
                number_type,
                subtype,
                pname,
                args["name"] if "name" in args else pname,
                args["description"] if "description" in args else "",
                group,
                args["default"] if "default" in args else 0,
                args["min"] if "min" in args else -10000,
                args["max"] if "max" in args else 10000,
                step,
                resettable=_is_resetable_addon(args)
            ))
            num_props += 1

        elif func in enum_funcs:
            enum_type = 'ENUM' if func == bpy.props.EnumProperty else 'BOOLEAN'
            default = False
            if "default" in args:
                default = args["default"]
            elif enum_type == 'ENUM' and "items" in args:
                items = args["items"]
                if not isinstance(items, list) and \
                        not isinstance(items, tuple):
                    continue
                if len(items) == 0:
                    continue
                default = items[0][0]
            props[group].append(PropData(
                enum_type,
                subtype,
                pname,
                args["name"] if "name" in args else pname,
                args["description"] if "description" in args else "",
                group,
                args["default"] if "default" in args else default,
                resettable=_is_resetable_addon(args)
            ))
            num_props += 1

        elif all_props:
            props[group].append(PropData(
                None,
                subtype,
                pname,
                args["name"] if "name" in args else pname,
                args["description"] if "description" in args else "",
                group,
                args["default"] if "default" in args else default,
                resettable=_is_resetable_addon(args)
            ))

    return props, num_props, has_pointer


def get_prop_data(idname, all_props=False, sort_props=False):
    rna_type = ou.get_rna_type(ou.to_bl_idname(idname))
    if not rna_type:
        return None, None

    # if hasattr(tp, "bl_idname"):
    if False:
        prop_data, num_props, has_pointer = _get_prop_data_addon(
            idname, all_props)
    else:
        prop_data, num_props, has_pointer = _get_prop_data_bl(
            idname, all_props)

    if sort_props:
        for v in prop_data.values():
            v.sort(key=lambda pd: (pd.type, pd.label), reverse=True)

    # if has_pointer:
    #     num_props = 0

    return prop_data, num_props


def multiton(cls):
    instances = {}

    def getinstance(idname):
        if idname not in instances:
            instances[idname] = cls(idname)
        return instances[idname]
    return getinstance


@multiton
class OperatorData():
    def __init__(self, idname):
        self.idname = idname

    @property
    def icon(self):
        if not hasattr(self, "_icon"):
            self._icon = ou.idname_to_icon(self.idname)
        return self._icon

    @property
    def label(self):
        if not hasattr(self, "_label"):
            self._label = ou.idname_to_label(self.idname)
        return self._label

    @property
    def description(self):
        if hasattr(self, "_description"):
            self._description = ou.idname_to_description(self.idname)
        return self._description

    @property
    def prop_data(self):
        if getattr(self, "_prop_data", None) is None:
            self._prop_data, self._num_props = get_prop_data(
                self.idname, False, True)
        return self._prop_data

    @property
    def num_props(self):
        if getattr(self, "_num_props", None) is None:
            self.prop_data

        return self._num_props

    def get_prop_data(self, group, prop):
        pdd = self.prop_data
        if group not in pdd:
            return None

        pds = pdd[group]
        for pd in pds:
            if pd.id == prop:
                return pd

        return None
