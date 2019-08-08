# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


import bpy
from bpy.props import (
    BoolProperty,
    PointerProperty,
)
from bpy.types import (
    PropertyGroup,
    AddonPreferences,
)


bl_info = {
    "name": "3D Viewport Pie Menus Symmetry",
    "author": "meta-androcto, pitiwazou, chromoly, italic",
    "version": (1, 1, 8),
    "blender": (2, 80, 0),
    "description": "Individual Pie Menu Activation List",
    "location": "Addons Preferences",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/viewport_pies",
    "category": "Pie Menu"
    }




import bpy
from bpy.types import Header, Menu, Panel



class VIEW3D_MT_symmetry_pie(Menu):
    bl_label = "View"
    bl_idname = "VIEW3D_MT_symmetry_pie"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        obj = context.active_object
        mode = context.mode
       
  

             # 4 - LEFT
        pie.operator("mesh.symmetrize", text="Symmetry +X", icon='AXIS_SIDE').direction='POSITIVE_X'
            #1 6 - RIGHT
        pie.operator("mesh.symmetrize", text="Symmetry -X", icon='AXIS_SIDE').direction='NEGATIVE_X'
        #     # 2 - BOTTOM
        pie.operator("mesh.symmetrize", text="Symmetry +Z", icon='AXIS_TOP').direction='POSITIVE_Z'
        #     # 8 - TOP
        pie.operator("mesh.symmetrize", text="Symmetry -Z", icon='AXIS_TOP').direction='NEGATIVE_Z'
        #     # 7 - TOP - LEFT
        pie.operator("mesh.symmetrize", text="Symmetry -Y", icon='AXIS_FRONT').direction='NEGATIVE_Y'
        pie.operator("mesh.symmetrize", text="Symmetry +Y", icon='AXIS_FRONT').direction='POSITIVE_Y'    

        # pie.operator("object.origin_set", text="Origin to Center of Mass (Volume)", icon='VOLUME').type = 'ORIGIN_CENTER_OF_VOLUME'


classes = (VIEW3D_MT_symmetry_pie,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # prefs = get_addon_preferences()
    # for mod in sub_modules:
    #     if not hasattr(mod, '__addon_enabled__'):
    #         mod.__addon_enabled__ = False
    #     name = mod.__name__.split('.')[-1]
    #     if getattr(prefs, 'use_' + name):
    #         register_submodule(mod)


def unregister():
    # for mod in sub_modules:
    #     if mod.__addon_enabled__:
    #         unregister_submodule(mod)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
