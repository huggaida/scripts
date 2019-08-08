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
    "name": "3D Viewport SubSurf modifier Toggle",
    "author": "maiw",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "description": "3D Viewport SubSurf modifier Toggle",
    "location": "Addons Preferences",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/viewport_pies",
    "category": "Pie Menu"
    }




import bpy
from bpy.types import Header, Menu, Panel



class Add_Subsurf(bpy.types.Operator):
    bl_idname = "object.add_subsurf"
    bl_label = "Toggle a subsurf modifier"

    def execute(self, context):
        obj = context.object
        for modifier in obj.modifiers:
            if modifier.type == "SUBSURF":
                obj.modifiers["Subdivision"].show_viewport = not obj.modifiers["Subdivision"].show_viewport

        if not obj.modifiers or not any([m for m in obj.modifiers if m.type == "SUBSURF"]):
            subsurf = obj.modifiers.new(name='Subdivision', type='SUBSURF')
            subsurf.levels = 1
            subsurf.show_on_cage = True
        
        return {'FINISHED'}

classes = (Add_Subsurf,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
def unregister():
       for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
