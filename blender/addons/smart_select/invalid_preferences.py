import bpy
from . import addon


def register_modules():
    def draw(self, context):
        col = self.layout.column(True)
        row = col.row()
        row.alignment = 'CENTER'
        row.label("Please update Blender to the latest version", icon='INFO')

    addon_preferences_type = type(
        "AddonPreferences",
        (bpy.types.AddonPreferences, ),
        dict(bl_idname=addon.ADDON_ID, draw=draw))
    bpy.utils.register_class(addon_preferences_type)


def unregister_modules():
    bpy.utils.unregister_class(addon.prefs().__class__)


if bpy.app.version < addon.BL_VERSION:
    addon.register_modules = register_modules
    addon.unregister_modules = unregister_modules
