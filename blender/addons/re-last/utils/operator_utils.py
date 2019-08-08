import bpy
from mathutils import Euler

_OP_ICONS = dict(
    OTHER='SCRIPTWIN',
    ACTION='ACTION',
    ANIM='ANIM',
    ARMATURE='OUTLINER_OB_ARMATURE',
    BOID='BOIDS',
    BOOLEAN='MOD_BOOLEAN',
    BRUSH='BRUSH_DATA',
    BUTTONS='COLLAPSEMENU',
    CAMERA='OUTLINER_OB_CAMERA',
    CLIP='CLIP',
    CLOTH='MOD_CLOTH',
    CONSOLE='CONSOLE',
    CONSTRAINT='CONSTRAINT',
    CURVE='OUTLINER_OB_CURVE',
    CYCLES='SMOOTH',
    DPAINT='MOD_DYNAMICPAINT',
    ED='COPYDOWN',
    EXPORT='EXPORT',
    FILE='FILESEL',
    FLUID='MOD_FLUIDSIM',
    FONT='OUTLINER_OB_FONT',
    GPENCIL='GREASEPENCIL',
    GRAPH='IPO',
    GROUP='GROUP',
    IMAGE='IMAGE_COL',
    IMPORT='IMPORT',
    INFO='INFO',
    LAMP='LAMP',
    LATTICE='OUTLINER_OB_LATTICE',
    LOGIC='LOGIC',
    MARKER='PMARKER_ACT',
    MASK='MOD_MASK',
    MATERIAL='MATERIAL',
    MBALL='OUTLINER_OB_META',
    MESH='OUTLINER_OB_MESH',
    NLA='NLA',
    NODE='NODETREE',
    OBJECT='OBJECT_DATA',
    OUTLINER='OOPS',
    PAINT='BRUSH_DATA',
    PAINTCURVE='VPAINT_HLT',
    PALETTE='COLOR',
    PARTICLE='PARTICLES',
    POSE='POSE_DATA',
    POSELIB='POSE_DATA',
    RENDER='RESTRICT_RENDER_OFF',
    SCENE='SCENE_DATA',
    SCREEN='SPLITSCREEN',
    SCRIPT='SCRIPT',
    SCULPT='SCULPTMODE_HLT',
    SEQUENCER='SEQUENCE',
    SKETCH='LINE_DATA',
    SOUND='SOUND',
    SURFACE='OUTLINER_OB_SURFACE',
    TEXT='TEXT',
    TEXTURE='TEXTURE_DATA',
    TIME='TIME',
    TRANSFORM='MANIPUL',
    UI='UI',
    UV='UV_FACESEL',
    VIEW2D='MESH_PLANE',
    VIEW3D='MESH_CUBE',
    WM='NODE',
    WORLD='WORLD_DATA'
)


def split_idname_py(idname_py):
    mod, _, op = idname_py.partition(".")
    return mod, op


def to_bl_idname(idname):
    tp = getattr(bpy.types, idname, None)
    if tp and hasattr(tp, "bl_idname"):
        return getattr(tp, "bl_idname")

    return idname.lower().replace("_ot_", ".")


def to_idname(bl_idname):
    op = operator(bl_idname)
    if op:
        return op.idname()

    return None


def check_idname(idname):
    return get_rna_type(to_bl_idname(idname)) is not None


def operator(bl_idname):
    try:
        ret = eval("bpy.ops.%s" % bl_idname)
        if hasattr(ret, "get_rna"):
            ret.get_rna().rna_type
        else:
            ret.get_rna_type()
    except:
        ret = None

    return ret


def get_rna_type(op):
    try:
        if isinstance(op, str):
            if "_OT_" in op:
                op = to_bl_idname(op)

            op = eval("bpy.ops.%s" % op)

        if hasattr(op, "get_rna"):
            ret = op.get_rna().rna_type
        else:
            ret = op.get_rna_type()
    except:
        ret = None

    return ret


def idname_to_label(idname):
    rna_type = get_rna_type(to_bl_idname(idname))
    if not rna_type:
        return ""

    label = rna_type.name
    if not label:
        label = rna_type.identifier
        if "_OT_" in label:
            label = label.split("_OT_")[-1]
            label = label.replace("_", " ").title()

    return label


def idname_to_description(idname):
    rna_type = get_rna_type(to_bl_idname(idname))
    if not rna_type:
        return ""

    return rna_type.description


def idname_to_icon(idname):
    rna_type = get_rna_type(to_bl_idname(idname))
    if not rna_type:
        return 'ERROR'

    group, _, _ = idname.partition("_OT_")
    return _OP_ICONS[group] if group in _OP_ICONS else _OP_ICONS['OTHER']


def module_to_icon(module):
    group = module.upper()
    if group in _OP_ICONS:
        return _OP_ICONS[group]
    elif group.startswith("IMPORT"):
        return _OP_ICONS["IMPORT"]
    elif group.startswith("EXPORT"):
        return _OP_ICONS["EXPORT"]

    return _OP_ICONS['OTHER']


def idname_to_group(idname):
    group, _, _ = idname.partition("_OT_")
    return group if group in _OP_ICONS else 'OTHER'


def idname_to_operator(idname_py):
    mod, op = split_idname_py(idname_py)
    mod = getattr(bpy.ops, mod)
    return getattr(mod, op)


def get_prop_value(operator, group, prop):
    if not operator:
        return None

    if group:
        if group not in operator.macros:
            return None

        return getattr(operator.macros[group].properties, prop, None)

    else:
        return getattr(operator.properties, prop, None)


def to_py_value(data, key, value):
    if isinstance(value, bpy.types.PropertyGroup):
        return None

    if isinstance(value, bpy.types.OperatorProperties):
        rna_type = get_rna_type(to_bl_idname(key))
        if not rna_type:
            return None

        d = dict()
        for k in value.keys():
            py_value = to_py_value(rna_type, k, getattr(value, k))
            if py_value is None or isinstance(py_value, dict) and not py_value:
                continue
            d[k] = py_value

        return d

    is_bool = isinstance(data.properties[key], bpy.types.BoolProperty)

    if hasattr(value, "to_list"):
        value = value.to_list()
        if is_bool:
            value = [bool(v) for v in value]
    elif hasattr(value, "to_tuple"):
        value = value.to_tuple()
        if is_bool:
            value = tuple(bool(v) for v in value)
    elif isinstance(value, bpy.types.bpy_prop_array):
        value = list(value)
        if is_bool:
            value = [bool(v) for v in value]
    elif isinstance(value, Euler):
        value = (value.x, value.y, value.z)

    return value
