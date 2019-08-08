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

import bpy, bmesh, bgl, mathutils, math

from mathutils import Vector, Matrix

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

def draw_callback_rot_tool(self):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(2)    
    bgl.glDepthRange(0,0.99999)
        
    amp=self.rv3d.view_distance/15
        
    if not hasattr(self, 'cache'):
        self.cache = True
        self.n_points = 12
        seg_angle = 2*math.pi / self.n_points
        self.c = math.cos(seg_angle)
        self.s = math.sin(seg_angle)

    if not hasattr(self, 'vec') or self.vec != self.normal_face or self.vector_constrain:
        if self.bool_confirm == False:
            if self.vector_constrain:
                self.vec = (self.vector_constrain[1]-self.vector_constrain[0]).normalized()
            else:
                self.vec = self.normal_face
            self.vec_norm = Vector((self.vec[0], self.vec[1])).normalized()
            if self.vec_norm[0]+self.vec[1] == 0:
                self.vec_norm = Vector((1, 0))
            self.vec_length = Vector((self.vec[0], self.vec[1])).length
    
    if self.vec == Vector((1,0,0)) or self.vec == Vector((-1,0,0)):
        bgl.glColor3f(*self.axis_x_color)
    elif self.vec == Vector((0,1,0)) or self.vec == Vector((0,-1,0)):
        bgl.glColor3f(*self.axis_y_color)
    elif self.vec == Vector((0,0,1)) or self.vec == Vector((0,0,-1)):
        bgl.glColor3f(*self.axis_z_color)        
    else:
        bgl.glColor3f(0.0, 0.0, 0.0)
        
    cos = self.vec_norm[0]
    sen = self.vec_norm[1]
    x_el = self.vec[2]
    y_el = 1
    x = amp
    y = 0
    z = 0

    if self.bool_confirm:
        bgl.glBegin(bgl.GL_LINE_STRIP)
        try:
            bgl.glVertex3f(*(self.r))
            bgl.glVertex3f(*(self.track_point))
        except:
            pass
        bgl.glEnd()

    bgl.glDisable(bgl.GL_LINE_STIPPLE)   
    
    bgl.glBegin(bgl.GL_LINE_STRIP)        
    bgl.glVertex3f(*(self.r)), bgl.glVertex3f(*(self.r + self.vec*amp))
    bgl.glEnd()
    
    bgl.glBegin(bgl.GL_LINE_LOOP)
    for i in range(self.n_points+1):
        t = x
        x = self.c*x-self.s*y
        y = self.s*t+self.c*y
        x2 = cos*x*x_el-sen*y*y_el
        y2 = sen*x*x_el+cos*y*y_el
        z = -x*self.vec_length
        bgl.glVertex3f(*(self.r + Vector((x2,y2,z))))
    bgl.glEnd()

    # restore opengl defaults
    bgl.glDepthRange(0,1)
    bgl.glPointSize(1)
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glDisable(bgl.GL_LINE_STIPPLE)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

class SnapUtilitiesRotate(Common_Modals):
    """Rotate selected entities about an axis"""
    bl_idname = "mesh.snap_utilities_rotate"
    bl_label = "Rotate Tool"
    bl_options = {'REGISTER', 'UNDO'}
    #to do: reduce calculation memory when moving the mouse

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
            try:
                if self.bm.select_history:
                    self.geom = self.bm.select_history[0]
                else:
                    self.geom = None
            except: # IndexError or AttributeError:
                self.geom = None

            mouse_co = (event.mouse_region_x, event.mouse_region_y)
            orig, view_vector = region_2d_to_orig_and_view_vector(self.region, self.rv3d, mouse_co)
            if self.blender_version:
                normal_face = context.scene.ray_cast(orig, view_vector)[2]
            else:
                end = orig + view_vector * 1000
                normal_face = context.scene.ray_cast(orig, end)[4]

            if normal_face and normal_face != Vector((0,0,0)):
                self.normal_face = normal_face
            else:
                self.normal_face = Vector((0.0, 0.0, 1.0))

            active_object = context.active_object
            if active_object or self.geom != None:
                if active_object.mode == 'EDIT' and active_object.type == 'MESH':
                    if self.geom:
                        self.geom.select = False
                        self.bm.select_history.clear()
                else:
                    bpy.ops.object.select_all(action='DESELECT')
                
            bpy.ops.view3d.select(location=mouse_co)

            if self.bool_confirm == False:
                self.r = self.location
            else:
                a = self.vec
                b = (self.location-self.r)
                self.track_point = b - a.dot(b)*a + self.r

            outer_verts = self.outer_verts and not self.keytab

            class previous_vert: co = self.original_obj_matrix.inverted()*self.r #to do: cache

            snap_utilities(self, 
                context, 
                self.obj2_matrix,
                self.geom,
                self.bool_update,
                mouse_co,
                outer_verts = self.outer_verts,
                constrain = self.vector_constrain,
                previous_vert = previous_vert,
                ignore_obj = self.obj,
                #increment = self.incremental,
                )
            self.bool_update = False

            if self.snap_to_grid and self.type == 'OUT':
                loc = self.location/self.rd
                self.location = Vector((round(loc.x),
                                        round(loc.y),
                                        round(loc.z)))*self.rd

            if self.bool_confirm_rotate:
                # self.r = Ponto de encontro dos eixos
                # self.vec = axis de rotação
                # self.track_point = Ponto de localização do cursor 3d
                # self.vec_rot_ini = vetor incial de rotação
                if self.vector_constrain:
                    vector_track = self.vector_constrain[1]-self.vector_constrain[0]
                    sign = (self.track_point - self.r).dot(vector_track)
                    if sign < 0:
                        vector_track = -vector_track
                else:
                    vector_track = self.track_point - self.r

               ### start slow rotation :( ###
                    if vector_track == Vector((0,0,0)):
                        vector_track = self.vec_rot_ini
                try:
                    angle = self.vec_rot_ini.angle(vector_track)
                    sign = self.vec.dot(self.vec_rot_ini.cross(vector_track))
                    if sign < 0:
                        angle = -angle
                except ValueError:
                    angle = 0
                mat_loc = Matrix.Translation(self.r)
                mat_rot = Matrix.Rotation(angle, 4, self.vec)
               ### end slow rotation :( ###

                #quat = self.vec_rot_ini.rotation_difference(vector_track)
                #mat_rot = quat.to_matrix().to_4x4()
                mat_loc = Matrix.Translation(self.r)
                mat = mat_loc*mat_rot*mat_loc.inverted()
                self.obj.matrix_world = mat*self.obj_matrix.copy()

                if context.scene.objects.active.type == 'MESH':# and self.geom.type == 'MESH':
                    if self.type == 'OUT' and context.object.data.is_editmode == True and not self.vector_constrain:
                        bpy.ops.object.mode_set(mode='OBJECT')
                        context.scene.objects.active = self.obj
                        self.obj2_matrix = self.obj.matrix_world.copy()
                        if hasattr(self, 'list_verts_co') or self.list_verts_co != []:
                            self.list_verts_co = []
                    
                    elif context.object.data.is_editmode == False and context.scene.objects.active != self.obj: # and self.depht == 1!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        temp_obj = context.scene.objects.active
                        self.obj2_matrix = temp_obj.matrix_world.copy()
                        bpy.ops.object.mode_set(mode='EDIT')
                        self.bm = bmesh.from_edit_mesh(temp_obj.data)

        if event.value == 'PRESS':
            if self.bool_confirm_rotate and (event.ascii in CharMap.ascii or event.type in CharMap.type):
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
                                self.vector_constrain = [self.obj2_matrix * v.co for v in self.geom.verts]+[event.type]
                    else:
                        if self.list_verts:
                            loc = self.list_verts_co[-1]
                        elif hasattr(self, 'r'):
                            loc = self.r
                        else:
                            loc = self.location
                        self.vector_constrain = [loc, loc + self.constrain_keys[event.type]]+[event.type]

            if event.type == 'LEFTMOUSE':
                if self.bool_confirm_rotate == True:
                    self.bool_confirm_rotate = False
                    self.bool_confirm = False
                    self.obj.hide_select = False
                    for ch in self.obj.children:
                        ch.hide_select = False
                    bpy.ops.object.mode_set(mode='OBJECT')
                    context.scene.objects.active = self.obj
                    self.obj2_matrix = self.obj.matrix_world.copy()
                    bpy.ops.object.mode_set(mode='EDIT')
                    self.bm = bmesh.from_edit_mesh(self.obj.data)
                    
                if self.bool_confirm == True:
                    self.obj_matrix = self.obj.matrix_world.copy()
                    self.vec_rot_ini = self.track_point - self.r
                    self.bool_confirm_rotate = True
                    bpy.ops.object.mode_set(mode='OBJECT')
                    self.obj.hide_select = True
                    for ch in self.obj.children:
                        ch.hide_select = True
                    if hasattr(self, 'list_verts_co') or self.list_verts_co != []:
                        self.list_verts_co = []
                else:
                    print("howwww???????")
                    self.bool_confirm = True
                    self.vector_constrain = None
        
            elif event.type == 'TAB':
                self.keytab = self.keytab == False
                if self.keytab:            
                    context.tool_settings.mesh_select_mode = (False, False, True)
                else:
                    context.tool_settings.mesh_select_mode = (True, True, True)

        elif event.value == 'RELEASE':
            if event.type in {'ESC', 'RIGHTMOUSE', 'RET', 'NUMPAD_ENTER'}:
                if event.type != 'ESC' and self.length_entered != "":
                    try:
                        angle = math.radians(float(self.length_entered))
                        sign = self.vec.dot(self.vec_rot_ini.cross(self.track_point - self.r))
                        if sign < 0:
                            angle = -angle
                        mat_loc = Matrix.Translation(self.r)
                        mat_rot = Matrix.Rotation(angle, 4, self.vec)
                        mat = mat_loc*mat_rot*mat_loc.inverted()
                        self.obj.matrix_world = mat*self.original_obj_matrix
                    except:
                        self.length_entered = ""
                        self.report({'INFO'}, "Operation not supported yet")
                    
                self.obj.hide_select = False
                for ch in self.obj.children:
                    ch.hide_select = False
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                bpy.types.SpaceView3D.draw_handler_remove(self._handle2, 'WINDOW')
                context.tool_settings.mesh_select_mode = self.select_mode
                context.area.header_text_set()
                context.user_preferences.view.use_rotate_around_active = self.use_rotate_around_active
                if not self.is_editmode and context.scene.objects.active.type == 'MESH':
                    bpy.ops.object.editmode_toggle()
                if event.type == 'ESC':
                    self.obj.matrix_world = self.original_obj_matrix
                    return {'CANCELLED'}
                
                return {'FINISHED'}

        a = ""
        if self.length_entered:
            pos = self.line_pos
            a = 'angle: '+ self.length_entered[:pos] + '|' + self.length_entered[pos:] + '°'
        context.area.header_text_set("hit: %.3f %.3f %.3f %s" % (self.location[0], self.location[1], self.location[2], a))

        self.modal_navigation(context, event)
        return {'RUNNING_MODAL'} 

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            self.blender_version = bpy.app.version[1] > 76 or (bpy.app.version[1] == 76 and bpy.app.version[2] > 3)
            self.location = Vector((0,0,0))
            self.original_loc = bpy.context.active_object.location.copy()
            self.original_obj_matrix = bpy.context.active_object.matrix_world.copy()
            self.bool_confirm = False
            self.bool_confirm_rotate = False
            self.normal_face = Vector((0,0,1))
            
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
            #self.obj_matrix = self.obj.matrix_world.copy()
            self.obj2_matrix = self.obj.matrix_world.copy()
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
            self._handle2 = bpy.types.SpaceView3D.draw_handler_add(draw_callback_rot_tool, (self,), 'WINDOW', 'POST_VIEW')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

def register():
    print('register SnapUtilitiesRotate')
    bpy.utils.register_class(SnapUtilitiesRotate)

if __name__ == "__main__":
    register()