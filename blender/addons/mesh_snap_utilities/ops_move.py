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

import bpy, bmesh, mathutils

from mathutils import Vector

from .common_classes import (
    CharMap,
    Common_Modals,
    )

from .common_utilities import (
    get_units_info,
    convert_distance,
    location_3d_to_region_2d,
    region_2d_to_orig_and_view_vector,
    out_Location,
    snap_utilities,
    )

if not __package__:
    __package__ = "mesh_snap_utilities"

class SnapUtilitiesMove(Common_Modals):
    """Move selected entities"""
    bl_idname = "mesh.snap_utilities_move"
    bl_label = "Move Tool"
    bl_options = {'REGISTER', 'UNDO'}

    constrain_keys = {
        'X': Vector((1,0,0)),
        'Y': Vector((0,1,0)),
        'Z': Vector((0,0,1)),
        'RIGHT_SHIFT': 'shift',
        'LEFT_SHIFT': 'shift',
        }

    @classmethod
    def poll(cls, context):
        return (context.mode in {'EDIT_MESH', 'OBJECT'} and
                context.object is not None and
                context.object.type == 'MESH')
    
    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
        
        if event.type == 'MOUSEMOVE' or self.bool_update:
            if self.rv3d.view_matrix != self.rotMat:
                self.rotMat = self.rv3d.view_matrix.copy()
                self.bool_update = True
            else:
                self.bool_update = False

            try:
                if self.bm.select_history:
                    self.geom = self.bm.select_history[0]
                else:
                    self.geom = None
            except: # IndexError or AttributeError:
                self.geom = None

            x, y = (event.mouse_region_x, event.mouse_region_y)

            active_object = context.active_object
            if active_object or self.geom != None:
                if active_object.mode == 'EDIT' and active_object.type == 'MESH':
                    if self.geom:
                        self.geom.select = False
                        self.bm.select_history.clear()
                else:
                    bpy.ops.object.select_all(action='DESELECT')
                
            bpy.ops.view3d.select(location=(x, y))

            if self.list_verts:
                previous_vert = self.list_verts[-1]
            else:
                previous_vert = None

            outer_verts = self.outer_verts and not self.keytab

            snap_utilities(self, 
                context, 
                self.obj_matrix,
                self.geom,
                self.bool_update,
                (x, y),
                outer_verts = self.outer_verts,
                constrain = self.vector_constrain,
                previous_vert = previous_vert,
                ignore_obj = self.obj,
                increment = self.incremental,
                )
            
            if self.snap_to_grid and self.type == 'OUT':
                loc = self.location/self.rd
                self.location = Vector((round(loc.x),
                                        round(loc.y),
                                        round(loc.z)))*self.rd

            if self.bool_confirm == True:

                if context.scene.objects.active.type == 'MESH':# and self.geom.type == 'MESH':
                    self.obj.location = self.location+self.Lloc
                    if isinstance(self.geom, bmesh.types.BMVert): # for the distance value
                        self.list_verts_co = [self.obj_matrix*self.geom.co]
                        
                    if self.type == 'OUT' and context.object.data.is_editmode == True and not self.vector_constrain:
                        #print('OBJECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        context.scene.objects.active = self.obj
                        if self.list_verts_co != []:
                            self.list_verts_co = []
                    
                    elif context.scene.objects.active != self.obj and context.object.data.is_editmode == False:
                        #print('EDIT')
                        temp_obj = context.scene.objects.active
                        self.obj_matrix = temp_obj.matrix_world.copy()
                        bpy.ops.object.mode_set(mode='EDIT')
                        self.bm = bmesh.from_edit_mesh(temp_obj.data)

                elif context.scene.objects.active.type in {'LAMP','CAMERA','EMPTY'}:
                    self.obj.location = context.scene.objects.active.location+self.Lloc

        if event.value == 'PRESS':
            if self.list_verts_co and (event.ascii in CharMap.ascii or event.type in CharMap.type):
                CharMap.modal(self, context, event)

            if event.type in self.constrain_keys:
                self.bool_update = True
                if self.vector_constrain and self.vector_constrain[2] == event.type:
                    self.vector_constrain = ()

                else:
                    if event.shift:
                        if isinstance(self.geom, bmesh.types.BMEdge):
                            if self.list_verts:
                                loc = self.list_verts_co[-1]
                                self.vector_constrain = (loc, loc + self.geom.verts[1].co - self.geom.verts[0].co, event.type)
                            else:
                                self.vector_constrain = [self.obj_matrix * v.co for v in self.geom.verts]+[event.type]
                    else:
                        if self.list_verts:
                            loc = self.list_verts_co[-1]
                        else:
                            loc = self.location
                        self.vector_constrain = [loc, loc + self.constrain_keys[event.type]]+[event.type]

            elif event.type == 'LEFTMOUSE':
                snap_3d = self.location
                self.Lloc = self.obj.location-snap_3d
                self.bool_confirm = self.bool_confirm == False
                if self.bool_confirm == True:
                    bpy.ops.object.mode_set(mode='OBJECT')
                    self.obj.hide_select = True
                    for ch in self.obj.children:
                        ch.hide_select = True
                else:
                    self.obj.hide_select = False
                    for ch in self.obj.children:
                        ch.hide_select = False
                    bpy.ops.object.mode_set(mode='OBJECT')
                    context.scene.objects.active = self.obj
                    self.obj_matrix = self.obj.matrix_world.copy()
                    bpy.ops.object.mode_set(mode='EDIT')
                    self.bm = bmesh.from_edit_mesh(self.obj.data)
                    if hasattr(self, 'list_verts_co') or self.list_verts_co != []:
                        self.list_verts_co = []

            elif event.type == 'TAB' and event.value == 'PRESS':
                self.keytab = self.keytab == False
                if self.keytab:            
                    context.tool_settings.mesh_select_mode = (False, False, True)
                else:
                    context.tool_settings.mesh_select_mode = (True, True, True)
        
        elif event.value == 'RELEASE':
            if event.type in {'RET', 'NUMPAD_ENTER'}:
                if self.length_entered != "" and self.list_verts_co != []:
                    try:
                        text_value = bpy.utils.units.to_value(self.unit_system, 'LENGTH', self.length_entered)
                        vector_h0_h1 = (self.location-self.list_verts_co[-1]).normalized()
                        Glocation = ((vector_h0_h1*text_value)+self.list_verts_co[-1])
                        #Glocation = self.obj_matrix*location
                        self.obj.location = Glocation+self.Lloc
                        self.bool_confirm = False
                        
                        self.length_entered = ""
                    
                    except:# ValueError:
                        self.report({'INFO'}, "Operation not supported yet")
            
            elif event.type in {'ESC', 'RIGHTMOUSE'}:
                self.obj.hide_select = False
                for ch in self.obj.children:
                    ch.hide_select = False
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                context.tool_settings.mesh_select_mode = self.select_mode
                context.area.header_text_set()
                context.user_preferences.view.use_rotate_around_active = self.use_rotate_around_active
                if not self.is_editmode and context.scene.objects.active.type == 'MESH':
                    bpy.ops.object.editmode_toggle()
                if event.type == 'ESC':
                    self.obj.location = self.original_loc
                    return {'CANCELLED'}
                
                return {'FINISHED'}

        a = ""        
        if self.list_verts_co:
            if self.length_entered:
                pos = self.line_pos
                a = 'length: '+ self.length_entered[:pos] + '|' + self.length_entered[pos:]
            else:
                length = self.len
                length = convert_distance(length, self.uinfo)
                a = 'length: '+ length
        context.area.header_text_set("hit: %.3f %.3f %.3f %s" % (self.location[0], self.location[1], self.location[2], a))

        self.modal_navigation(context, event)
        return {'RUNNING_MODAL'} 

    def invoke(self, context, event):        
        if context.space_data.type == 'VIEW_3D':
            self.original_loc = bpy.context.active_object.location.copy()
            self.bool_confirm = False
            
            # General Invoke... 
            preferences = context.user_preferences.addons[__package__].preferences
            #create_new_obj = preferences.create_new_obj
            #if context.mode == 'OBJECT' and (create_new_obj or context.object == None or context.object.type != 'MESH'):

                #mesh = bpy.data.meshes.new("")
                #obj = bpy.data.objects.new("", mesh)
                #context.scene.objects.link(obj)
                #context.scene.objects.active = obj

            #bgl.glEnable(bgl.GL_POINT_SMOOTH)
            self.is_editmode = bpy.context.object.data.is_editmode
            bpy.ops.object.mode_set(mode='EDIT')
            context.space_data.use_occlude_geometry = True
            
            self.scale = context.scene.unit_settings.scale_length
            self.unit_system = context.scene.unit_settings.system
            self.separate_units = context.scene.unit_settings.use_separate
            self.uinfo = get_units_info(self.scale, self.unit_system, self.separate_units)

            grid = context.scene.unit_settings.scale_length/context.space_data.grid_scale
            relative_scale = preferences.relative_scale
            self.scale = grid/relative_scale
            self.rd = bpy.utils.units.to_value(self.unit_system, 'LENGTH', str(1/self.scale))

            incremental = preferences.incremental
            self.incremental = bpy.utils.units.to_value(self.unit_system, 'LENGTH', str(incremental))

            self.use_rotate_around_active = context.user_preferences.view.use_rotate_around_active
            context.user_preferences.view.use_rotate_around_active = True
            
            self.select_mode = context.tool_settings.mesh_select_mode[:]
            context.tool_settings.mesh_select_mode = (True, True, True)
            
            self.region = context.region
            self.rv3d = context.region_data
            self.rotMat = self.rv3d.view_matrix.copy()
            self.obj = bpy.context.active_object
            self.obj_matrix = self.obj.matrix_world.copy()
            self.bm = bmesh.from_edit_mesh(self.obj.data)
            
            self.location = Vector()
            self.list_verts = []
            self.list_verts_co = []
            self.bool_update = False
            self.vector_constrain = None
            self.keytab = False
            self.keyf8 = False
            self.type = 'OUT'
            self.len = 0
            self.length_entered = ""
            self.line_pos = 0
            
            self.out_color = preferences.out_color
            self.face_color = preferences.face_color
            self.edge_color = preferences.edge_color
            self.vert_color = preferences.vert_color
            self.center_color = preferences.center_color
            self.perpendicular_color = preferences.perpendicular_color
            self.constrain_shift_color = preferences.constrain_shift_color

            self.axis_x_color = tuple(context.user_preferences.themes[0].user_interface.axis_x)
            self.axis_y_color = tuple(context.user_preferences.themes[0].user_interface.axis_y)
            self.axis_z_color = tuple(context.user_preferences.themes[0].user_interface.axis_z)

            #self.intersect = preferences.intersect
            #self.create_face = preferences.create_face
            self.outer_verts = preferences.outer_verts
            self.snap_to_grid = preferences.increments_grid

            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (context,), 'WINDOW', 'POST_VIEW')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}