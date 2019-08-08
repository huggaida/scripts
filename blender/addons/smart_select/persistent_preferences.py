import bpy
from bpy.app.handlers import persistent
from .addon import prefs
from .utils import property_utils


@persistent
def load_pre_handler(_):
    global tmp_data
    tmp_data = property_utils.to_dict(prefs())

    global tmp_filepath
    tmp_filepath = bpy.data.filepath
    if not tmp_filepath:
        tmp_filepath = "_"

    bpy.app.handlers.scene_update_post.append(load_post_handler)


@persistent
def load_post_handler(_):
    if tmp_filepath == bpy.data.filepath:
        return

    bpy.app.handlers.scene_update_post.remove(load_post_handler)

    global tmp_data
    if tmp_data is None:
        return

    if not bpy.data.filepath:
        property_utils.from_dict(prefs(), tmp_data)

    tmp_data = None


def register():
    bpy.app.handlers.load_pre.append(load_pre_handler)


def unregister():
    bpy.app.handlers.load_pre.remove(load_pre_handler)
    if load_post_handler in bpy.app.handlers.scene_update_post:
        bpy.app.handlers.scene_update_post.remove(load_post_handler)
