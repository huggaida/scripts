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

import bpy
from bpy.props import EnumProperty, StringProperty, BoolProperty, IntProperty, FloatVectorProperty, FloatProperty

def update_panel(self, context):
    try:
        panel = bpy.types.VIEW3D_PT_snap_utilities
        panel.bl_category = context.user_preferences.addons[__package__].preferences.category
        bpy.utils.unregister_class(panel)
        bpy.utils.register_class(panel)
    except:
        print('not update')
        pass

class SnapUtilitiesPreferences(bpy.types.AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    intersect = BoolProperty(
            name="Intersect",
            description="intersects created line with the existing edges, even if the lines do not intersect.",
            default=True)

    create_new_obj = BoolProperty(
            name="Create a new object",
            description="If have not a active object, or the active object is not in edit mode, it creates a new object.",
            default=False)

    create_face = BoolProperty(
            name="Create faces",
            description="Create faces defined by enclosed edges.",
            default=False)

    outer_verts = BoolProperty(
            name="Snap to outer vertices",
            description="The vertices of the objects are not activated also snapped.",
            default=True)

    expand_snap_settings = BoolProperty(
            name="Expand",
            description="Expand, to display the settings",
            default=False)
            
    increments_grid = BoolProperty(
            name="Increments of Grid",
            description="Snap to increments of grid",
            default=False)

    category = StringProperty(
            name="Category",
            description="Choose a name for the category of the panel",
            default="Snap Utilities",
            update=update_panel
            )

    incremental = FloatProperty(
            name="Incremental",
            description="Snap in defined increments",
            default=0,
            min=0,
            step=1,
            precision=3)

    relative_scale = FloatProperty(
            name="Relative Scale",
            description="Value that divides the global scale.",
            default=1,
            min=0,
            step=1,
            precision=3)

    out_color = FloatVectorProperty(name="OUT", default=(0.0, 0.0, 0.0, 0.5), size=4, subtype="COLOR", min=0, max=1)
    face_color = FloatVectorProperty(name="FACE", default=(1.0, 0.8, 0.0, 1.0), size=4, subtype="COLOR", min=0, max=1)
    edge_color = FloatVectorProperty(name="EDGE", default=(0.0, 0.8, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1)
    vert_color = FloatVectorProperty(name="VERT", default=(1.0, 0.5, 0.0, 1.0), size=4, subtype="COLOR", min=0, max=1)
    center_color = FloatVectorProperty(name="CENTER", default=(1.0, 0.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1)
    perpendicular_color = FloatVectorProperty(name="PERPENDICULAR", default=(0.1, 0.5, 0.5, 1.0), size=4, subtype="COLOR", min=0, max=1)
    constrain_shift_color = FloatVectorProperty(name="SHIFT CONSTRAIN", default=(0.8, 0.5, 0.4, 1.0), size=4, subtype="COLOR", min=0, max=1)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Snap Colors:")
        split = layout.split()

        col = split.column()
        col.prop(self, "out_color")
        col.prop(self, "constrain_shift_color")
        col = split.column()
        col.prop(self, "face_color")
        col = split.column()
        col.prop(self, "edge_color")        
        col = split.column()
        col.prop(self, "vert_color")
        col = split.column()
        col.prop(self, "center_color")
        col = split.column()
        col.prop(self, "perpendicular_color")

        row = layout.row()

        col = row.column()
        col.label(text="Category:")
        col.prop(self, "category", text="")
        #col.label(text="Snap Items:")
        col.prop(self, "incremental")
        col.prop(self, "increments_grid")
        if self.increments_grid:
            col.prop(self, "relative_scale")

        col.prop(self, "outer_verts")
        row.separator()

        col = row.column()
        col.label(text="Line Tool:")
        col.prop(self, "intersect")
        col.prop(self, "create_face")
        col.prop(self, "create_new_obj")