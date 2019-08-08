bl_info = {
    "name": "Smart Select",
    "category": "Mesh",
    "author": "Jimmy Livefjord, roaoao",
    "version": (1, 3, 2),
    "blender": (2, 79, 0),
}

use_reload = "addon" in locals()
if use_reload:
    import importlib
    importlib.reload(locals()["addon"])
    del importlib

from . import addon
addon.init_addon(
    [
        "constants",
        "utils.property_utils",
        "utils.",
        "tools.",
        "",
    ],
    use_reload=use_reload,
    background=False,
)


def register():
    addon.register_modules()


def unregister():
    addon.unregister_modules()
