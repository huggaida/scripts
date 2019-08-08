import bpy
import importlib
import os
import pkgutil
import sys

BACKGROUND = False
VERSION = (0, 0, 0)
BL_VERSION = (0, 0, 0)
ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
ADDON_ID = os.path.basename(ADDON_PATH)
TEMP_PREFS_ID = "addon_" + ADDON_ID
ADDON_PREFIX = "".join([s[0] for s in ADDON_ID.split("_")])
ADDON_PREFIX_PY = ADDON_PREFIX.lower()
MODULE_NAMES = []
MODULE_MASK = None


def prefs():
    return bpy.context.user_preferences.addons[ADDON_ID].preferences


def temp_prefs():
    return getattr(bpy.context.window_manager, TEMP_PREFS_ID, None)


def init_addon(
        module_mask, use_reload=False, background=False,
        prefix=None, prefix_py=None):
    global VERSION, BL_VERSION, MODULE_MASK, BACKGROUND, \
        ADDON_PREFIX, ADDON_PREFIX_PY
    module = sys.modules[ADDON_ID]
    VERSION = module.bl_info.get("version", VERSION)
    BL_VERSION = module.bl_info.get("blender", BL_VERSION)

    if prefix:
        ADDON_PREFIX = prefix
    if prefix_py:
        ADDON_PREFIX_PY = prefix_py

    MODULE_MASK = module_mask
    for i, mask in enumerate(MODULE_MASK):
        MODULE_MASK[i] = "%s.%s" % (ADDON_ID, mask)

    BACKGROUND = background
    if not BACKGROUND and bpy.app.background:
        return

    def get_module_names(path=ADDON_PATH, package=ADDON_ID):
        module_names = []
        for _, module_name, is_package in pkgutil.iter_modules([path]):
            if module_name == "addon" or module_name.startswith("_"):
                continue

            if is_package:
                for m in get_module_names(
                        os.path.join(path, module_name),
                        "%s.%s" % (package, module_name)):
                    yield m
            else:
                module_names.append("%s.%s" % (package, module_name))

        for module_name in module_names:
            yield module_name

    module_names = []
    for module_name in get_module_names():
        module_names.append(module_name)

    sorted_module_names = []
    for mask in MODULE_MASK:
        rest_module_names = []
        for module_name in module_names:
            if not mask or module_name.startswith(mask):
                sorted_module_names.append(module_name)
            else:
                rest_module_names.append(module_name)
        module_names = rest_module_names

    global MODULE_NAMES
    MODULE_NAMES = sorted_module_names
    for module_name in MODULE_NAMES:
        if use_reload:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)


def register_modules():
    if not BACKGROUND and bpy.app.background:
        return

    bpy.utils.register_module(ADDON_ID)

    for module_name in MODULE_NAMES:
        module = sys.modules[module_name]
        if hasattr(module, "register"):
            module.register()


def unregister_modules():
    if not BACKGROUND and bpy.app.background:
        return

    for module_name in reversed(MODULE_NAMES):
        module = sys.modules[module_name]
        if hasattr(module, "unregister"):
            module.unregister()

    bpy.utils.unregister_module(ADDON_ID)
