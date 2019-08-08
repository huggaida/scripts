### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# Contact for more information about the Addon:
# Email:    germano.costa@ig.com.br
# Twitter:  wii_mano @mano_wii

bl_info = {
    "name": "Snap_Utilities",
    "author": "Germano Cavalcante",
    "version": (5, 7, 4),
    "blender": (2, 76, 11),
    "location": "View3D > TOOLS > Snap Utilities > snap utilities",
    "description": "Extends Blender Snap controls",
    "wiki_url" : "http://blenderartists.org/forum/showthread.php?363859-Addon-CAD-Snap-Utilities",
    "category": "Mesh"}

import os
import bpy

from .preferences import SnapUtilitiesPreferences
from .ops_push_pull import SnapPushPullFace
from .ops_line import SnapUtilitiesLine
from .ops_move import SnapUtilitiesMove
from .ops_rotate import SnapUtilitiesRotate

class PanelSnapUtilities(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_snap_utilities"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "mesh_edit"
    bl_category = "Snap Utilities"
    bl_label = "Snap Utilities"

    @classmethod
    def poll(cls, context):
        preferences = context.user_preferences.addons[__package__].preferences
        return (context.mode in {'EDIT_MESH', 'OBJECT'} and
                preferences.create_new_obj or 
                (context.object is not None and
                context.object.type == 'MESH'))

    def draw(self, context):
        layout = self.layout
        TheCol = layout.column(align = True)
        pcoll = preview_collections["main"]

        line_icon = pcoll["su_line_icon"]
        move_icon = pcoll["su_move_icon"]
        rotate_icon = pcoll["su_rotate_icon"]
        push_pull_icon = pcoll["su_push_pull_icon"]

        addon_prefs = context.user_preferences.addons[__package__].preferences

        TheCol.operator("mesh.snap_utilities_line", text = "Line", icon_value=line_icon.icon_id)
        if context.object is not None and context.object.type == 'MESH':
            TheCol.operator("mesh.snap_utilities_move", text = "Move", icon_value=move_icon.icon_id)
            TheCol.operator("mesh.snap_utilities_rotate", text = "Rotate", icon_value=rotate_icon.icon_id)
            TheCol.operator("mesh.snap_push_pull", text = "Push/Pull Face", icon_value=push_pull_icon.icon_id)

        expand = addon_prefs.expand_snap_settings
        icon = "TRIA_DOWN" if expand else "TRIA_RIGHT"

        box = layout.box()
        box.prop(addon_prefs, "expand_snap_settings", icon=icon,
            text="Settings:", emboss=False)
        if expand:
            #box.label(text="Snap Items:")
            box.prop(addon_prefs, "outer_verts")
            box.prop(addon_prefs, "incremental")
            box.prop(addon_prefs, "increments_grid")
            if addon_prefs.increments_grid:
                box.prop(addon_prefs, "relative_scale")
            box.label(text="Line Tool:")
            box.prop(addon_prefs, "intersect")
            box.prop(addon_prefs, "create_face")
            box.prop(addon_prefs, "create_new_obj")

preview_collections = {}

def register():
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    pcoll.load("su_line_icon", os.path.join(icons_dir, "line_32.png"), 'IMAGE')
    pcoll.load("su_move_icon", os.path.join(icons_dir, "move_32.png"), 'IMAGE')
    pcoll.load("su_rotate_icon", os.path.join(icons_dir, "rotate_32.png"), 'IMAGE')
    pcoll.load("su_push_pull_icon", os.path.join(icons_dir, "push_pull_32.png"), 'IMAGE')

    preview_collections["main"] = pcoll

    bpy.utils.register_class(SnapUtilitiesPreferences)
    bpy.utils.register_class(SnapPushPullFace)
    bpy.utils.register_class(SnapUtilitiesLine)
    bpy.utils.register_class(SnapUtilitiesMove)
    bpy.utils.register_class(SnapUtilitiesRotate)
    
    try:
        PanelSnapUtilities.bl_category = bpy.context.user_preferences.addons[__package__].preferences.category
    except:
        pass
    bpy.utils.register_class(PanelSnapUtilities)

def unregister():
    bpy.utils.unregister_class(PanelSnapUtilities)
    bpy.utils.unregister_class(SnapUtilitiesRotate)
    bpy.utils.unregister_class(SnapUtilitiesMove)
    bpy.utils.unregister_class(SnapUtilitiesLine)
    bpy.utils.unregister_class(SnapPushPullFace)
    bpy.utils.unregister_class(SnapUtilitiesPreferences)

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

if __name__ == "__main__":
    __name__ = "mesh_snap_utilities"
    __package__ = "mesh_snap_utilities"
    register()