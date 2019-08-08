import bpy
from types import BuiltinFunctionType


def to_dict(obj, dct=None, encode=False, include=None):
    if encode and hasattr(obj, "encode"):
        return obj.encode()

    if dct is None:
        dct = {}

    try:
        dct["name"] = obj["name"]
    except:
        pass

    for k in dir(obj.__class__):
        if include and k not in include:
            continue

        tup = getattr(obj.__class__, k)
        if not isinstance(tup, tuple) or len(tup) != 2 or \
                not isinstance(tup[0], BuiltinFunctionType):
            continue

        tp, attrs = tup

        if "options" in attrs and 'HIDDEN' in attrs["options"]:
            continue

        try:
            if tp == bpy.props.CollectionProperty or \
                    tp == bpy.props.PointerProperty:
                value = getattr(obj, k)
            else:
                value = obj[k]
        except:
            if "get" in attrs:
                continue

            value = getattr(obj, k)

        if tp == bpy.props.PointerProperty:
            dct[k] = to_dict(value, None, encode)

        elif tp == bpy.props.CollectionProperty:
            dct[k] = []
            for item in value.values():
                dct[k].append(to_dict(item, None, encode))

        elif isinstance(value, (bool, int, float, str)):
            dct[k] = value

        elif isinstance(value, set):
            dct[k] = str(value)

    return dct


def from_dict(obj, dct, decode=False):
    for k, value in dct.items():
        if decode and hasattr(obj, k):
            pg = getattr(obj, k)
            if pg and isinstance(pg, bpy.types.PropertyGroup) and \
                    hasattr(pg, "decode"):
                pg.decode(value)
                continue

        if isinstance(value, dict):
            from_dict(getattr(obj, k), value, decode)

        elif isinstance(value, list):
            col = getattr(obj, k)
            col.clear()

            for item in value:
                from_dict(col.add(), item, decode)

        elif isinstance(value, str):
            if value.startswith("{") and value.endswith("}"):
                try:
                    value = eval(value)
                except:
                    value = None

                if value:
                    setattr(obj, k, value)

            else:
                obj[k] = value

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
