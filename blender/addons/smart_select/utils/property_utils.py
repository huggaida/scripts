import bpy
from types import BuiltinFunctionType


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


def to_dict(obj):
    dct = {}

    try:
        dct["name"] = obj["name"]
    except:
        pass

    for k in dir(obj.__class__):
        tup = getattr(obj.__class__, k)
        if not isinstance(tup, tuple) or len(tup) != 2 or \
                not isinstance(tup[0], BuiltinFunctionType):
            continue

        try:
            if tup[0] == bpy.props.CollectionProperty or \
                    tup[0] == bpy.props.PointerProperty:
                value = getattr(obj, k)
            else:
                value = obj[k]
        except:
            if "get" in tup[1]:
                continue

            value = getattr(obj, k)

        if tup[0] == bpy.props.PointerProperty:
            dct[k] = to_dict(value)

        elif tup[0] == bpy.props.CollectionProperty:
            dct[k] = []
            for item in value.values():
                dct[k].append(to_dict(item))

        elif isinstance(value, (bool, int, float, str)):
            dct[k] = value

    return dct


def from_dict(obj, dct):
    for k, value in dct.items():
        if isinstance(value, dict):
            from_dict(getattr(obj, k), value)

        elif isinstance(value, list):
            col = getattr(obj, k)
            col.clear()

            for item in value:
                from_dict(col.add(), item)

        else:
            obj[k] = value


def enum_item_next(data, prop, value, delta=1, loop=True):
    is_set = data.rna_type.properties[prop].is_enum_flag
    enum_items = data.rna_type.properties[prop].enum_items

    if is_set:
        idx = enum_items.find(value.pop()) if value else -1
    else:
        idx = enum_items.find(value)

    idx += delta
    if loop:
        idx = (idx + 1) % (len(enum_items) + 1) - 1
    else:
        idx = max(-1 if is_set else 0, min(idx, len(enum_items) - 1))

    if idx == -1:
        item = None
        value = set()
    else:
        item = enum_items[idx]
        value = enum_items[idx].identifier
        if is_set:
            value = {value}

    setattr(data, prop, value)
    return item
