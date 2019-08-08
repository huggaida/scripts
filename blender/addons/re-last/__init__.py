bl_info = {
    "name": "Re-Last",
    "category": "User Interface",
    "author": "roaoao, Jimmy Livefjord",
    "version": (2, 1, 1),
    "blender": (2, 80, 0),
    "tracker_url": "https://blenderartists.org/forum/showthread.php?411927",
    "wiki_url": "https://wiki.blender.org/index.php/User:Raa/Addons/Re-Last",
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
        "utils.debug_utils",
        "utils.operator_utils",
        "types.",
        "utils.",
        "ops.",
        "",
    ],
    use_reload=use_reload,
    background=False,
)


def register():
    addon.register_modules()


def unregister():
    addon.unregister_modules()
