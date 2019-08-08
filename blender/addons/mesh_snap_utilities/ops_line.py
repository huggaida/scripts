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

def get_isolated_edges(bmvert):
    linked = [ed for ed in bmvert.link_edges if not ed.link_faces[:]]
    for a in linked:
        edges = [b for c in a.verts if not c.link_faces[:] for b in c.link_edges[:] if b not in linked]
        for e in edges:
            linked.append(e)
    return linked

def draw_line(self, obj, Bmesh, bm_geom, location):
    if not hasattr(self, 'list_verts'):
        self.list_verts = []

    if not hasattr(self, 'list_edges'):
        self.list_edges = []

    if not hasattr(self, 'list_faces'):
        self.list_faces = []

    if bm_geom == None:
        vertices = (bmesh.ops.create_vert(Bmesh, co=(location)))
        self.list_verts.append(vertices['vert'][0])

    elif isinstance(bm_geom, bmesh.types.BMVert):
        if (bm_geom.co - location).length < .01:
            if self.list_verts == [] or self.list_verts[-1] != bm_geom:
                self.list_verts.append(bm_geom)
        else:
            vertices = bmesh.ops.create_vert(Bmesh, co=(location))
            self.list_verts.append(vertices['vert'][0])
        
    elif isinstance(bm_geom, bmesh.types.BMEdge):
        self.list_edges.append(bm_geom)
        vector_p0_l = (bm_geom.verts[0].co-location)
        vector_p1_l = (bm_geom.verts[1].co-location)
        cross = vector_p0_l.cross(vector_p1_l)/bm_geom.calc_length()

        if cross < Vector((0.001,0,0)): # or round(vector_p0_l.angle(vector_p1_l), 2) == 3.14:
            factor = vector_p0_l.length/bm_geom.calc_length()
            vertex0 = bmesh.utils.edge_split(bm_geom, bm_geom.verts[0], factor)
            self.list_verts.append(vertex0[1])
            #self.list_edges.append(vertex0[0])

        else: # constrain point is near
            vertices = bmesh.ops.create_vert(Bmesh, co=(location))
            self.list_verts.append(vertices['vert'][0])

    elif isinstance(bm_geom, bmesh.types.BMFace):
        self.list_faces.append(bm_geom)
        vertices = (bmesh.ops.create_vert(Bmesh, co=(location)))
        self.list_verts.append(vertices['vert'][0])
    
    # draw, split and create face
    if len(self.list_verts) >= 2:
        V1 = self.list_verts[-2]
        V2 = self.list_verts[-1]
        #V2_link_verts = [x for y in [a.verts for a in V2.link_edges] for x in y if x != V2]
        for edge in V2.link_edges:
            if V1 in edge.verts:
                self.list_edges.append(edge)
                break
        else: #if V1 not in V2_link_verts:
            if not V2.link_edges:
                edge = Bmesh.edges.new([V1, V2])
                self.list_edges.append(edge)
            else:
                face = [x for x in V2.link_faces[:] if x in V1.link_faces[:]]
                if face != []:# and self.list_faces == []:
                    self.list_faces = face
                    
                elif V1.link_faces[:] == [] or V2.link_faces[:] == []:
                    if self.list_faces == []:
                        if V1.link_faces[:] != []:
                            Vfaces = V1.link_faces
                            Vtest = V2.co
                        elif V2.link_faces[:] != []:
                            Vfaces = V2.link_faces
                            Vtest = V1.co
                        else:
                            Vfaces = []
                        for face in Vfaces:
                            testface = bmesh.geometry.intersect_face_point(face, Vtest)
                            if testface:
                                self.list_faces.append(face)

                if self.list_faces != []:
                    edge = Bmesh.edges.new([V1, V2])
                    self.list_edges.append(edge)
                    ed_list = get_isolated_edges(V2)
                    for face in list(set(self.list_faces)):
                        facesp = bmesh.utils.face_split_edgenet(face, list(set(ed_list)))
                        self.list_faces = []
                else:
                    if self.intersect:
                        facesp = bmesh.ops.connect_vert_pair(Bmesh, verts = [V1, V2])
                    if not self.intersect or facesp['edges'] == []:
                        edge = Bmesh.edges.new([V1, V2])
                        self.list_edges.append(edge)
                    else:   
                        for edge in facesp['edges']:
                            self.list_edges.append(edge)
                bmesh.update_edit_mesh(obj.data, tessface=True, destructive=True)

        # create face
        if self.create_face:
            ed_list = self.list_edges.copy()
            for edge in V2.link_edges:
                for vert in edge.verts:
                    if vert in self.list_verts:
                        ed_list.append(edge)
                        for edge in get_isolated_edges(V2):
                            if edge not in ed_list:
                                ed_list.append(edge)
                        bmesh.ops.edgenet_fill(Bmesh, edges = list(set(ed_list)))
                        bmesh.update_edit_mesh(obj.data, tessface=True, destructive=True)
                        break
            #print('face created')

    return [obj.matrix_world*a.co for a in self.list_verts]

class SnapUtilitiesLine(Common_Modals):
    """ Draw edges. Connect them to split faces."""
    bl_idname = "mesh.snap_utilities_line"
    bl_label = "Line Tool"
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
        preferences = context.user_preferences.addons[__package__].preferences
        return (context.mode in {'EDIT_MESH', 'OBJECT'} and
                preferences.create_new_obj or 
                (context.object is not None and
                context.object.type == 'MESH'))

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
            
        if event.ctrl and event.type == 'Z' and event.value == 'PRESS':
            bpy.ops.ed.undo()
            self.vector_constrain = None
            self.list_verts_co = []
            self.list_verts = []
            self.list_edges = []
            self.list_faces = []
            self.obj = bpy.context.active_object
            self.obj_matrix = self.obj.matrix_world.copy()
            self.bm = bmesh.from_edit_mesh(self.obj.data)
            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE' or self.bool_update:
            if self.rv3d.view_matrix != self.rotMat:
                self.rotMat = self.rv3d.view_matrix.copy()
                self.bool_update = True
            else:
                self.bool_update = False

            if self.bm.select_history:
                self.geom = self.bm.select_history[0]
            else: #See IndexError or AttributeError:
                self.geom = None

            x, y = (event.mouse_region_x, event.mouse_region_y)
            if self.geom:
                self.geom.select = False
                self.bm.select_history.clear()

            bpy.ops.view3d.select(location=(x, y))

            if self.list_verts != []:
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

            if self.keyf8 and self.list_verts_co:
                lloc = self.list_verts_co[-1]
                orig, view_vec = region_2d_to_orig_and_view_vector(self.region, self.rv3d, (x, y))
                location = mathutils.geometry.intersect_point_line(lloc, orig, (orig+view_vec))
                vec = (location[0] - lloc)
                ax, ay, az = abs(vec.x),abs(vec.y),abs(vec.z)
                vec.x = ax > ay > az or ax > az > ay
                vec.y = ay > ax > az or ay > az > ax
                vec.z = az > ay > ax or az > ax > ay
                if vec == Vector():
                    self.vector_constrain = None
                else:
                    vc = lloc+vec
                    try:
                        if vc != self.vector_constrain[1]:
                            type = 'X' if vec.x else 'Y' if vec.y else 'Z' if vec.z else 'shift'
                            self.vector_constrain = [lloc, vc, type]
                    except:
                        type = 'X' if vec.x else 'Y' if vec.y else 'Z' if vec.z else 'shift'
                        self.vector_constrain = [lloc, vc, type]

        if event.value == 'PRESS':
            if self.list_verts_co and (event.ascii in CharMap.ascii or event.type in CharMap.type):
                CharMap.modal(self, context, event)

            elif event.type in self.constrain_keys:
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
                # SNAP 2D
                snap_3d = self.location
                Lsnap_3d = self.obj_matrix.inverted()*snap_3d
                Snap_2d = location_3d_to_region_2d(self.region, self.rv3d, snap_3d)
                if self.vector_constrain and isinstance(self.geom, bmesh.types.BMVert): # SELECT FIRST
                    bpy.ops.view3d.select(location=(int(Snap_2d[0]), int(Snap_2d[1])))
                    try:
                        geom2 = self.bm.select_history[0]
                    except: # IndexError or AttributeError:
                        geom2 = None
                else:
                    geom2 = self.geom
                self.vector_constrain = None
                self.list_verts_co = draw_line(self, self.obj, self.bm, geom2, Lsnap_3d)
                bpy.ops.ed.undo_push(message="Undo draw line*")

            elif event.type == 'TAB':
                self.keytab = self.keytab == False
                if self.keytab:            
                    context.tool_settings.mesh_select_mode = (False, False, True)
                else:
                    context.tool_settings.mesh_select_mode = (True, True, True)

            elif event.type == 'F8':
                self.vector_constrain = None
                self.keyf8 = self.keyf8 == False

        elif event.value == 'RELEASE':
            if event.type in {'RET', 'NUMPAD_ENTER'} and\
               self.length_entered != "" and self.list_verts_co != []:
                try:
                    text_value = bpy.utils.units.to_value(self.unit_system, 'LENGTH', self.length_entered)
                    vector = (self.location-self.list_verts_co[-1]).normalized()
                    location = (self.list_verts_co[-1]+(vector*text_value))
                    G_location = self.obj_matrix.inverted()*location
                    self.list_verts_co = draw_line(self, self.obj, self.bm, self.geom, G_location)
                    self.length_entered = ""
                    self.vector_constrain = None

                except:# ValueError:
                    self.report({'INFO'}, "Operation not supported yet")

            elif event.type in {'RIGHTMOUSE', 'ESC', 'RET', 'NUMPAD_ENTER'}:
                if self.list_verts_co == [] or event.type == 'ESC':                
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    context.tool_settings.mesh_select_mode = self.select_mode
                    context.area.header_text_set()
                    context.user_preferences.view.use_rotate_around_active = self.use_rotate_around_active
                    if not self.is_editmode:
                        bpy.ops.object.editmode_toggle()
                    return {'FINISHED'}
                else:
                    self.vector_constrain = None
                    self.list_verts = []
                    self.list_verts_co = []
                    self.list_faces = []

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
            #print('name', __name__, __package__)
            preferences = context.user_preferences.addons[__package__].preferences
            create_new_obj = preferences.create_new_obj
            if context.mode == 'OBJECT' and (create_new_obj or context.object == None or context.object.type != 'MESH'):

                mesh = bpy.data.meshes.new("")
                obj = bpy.data.objects.new("", mesh)
                context.scene.objects.link(obj)
                context.scene.objects.active = obj

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
            self.vector_constrain = ()
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

            self.intersect = preferences.intersect
            self.create_face = preferences.create_face
            self.outer_verts = preferences.outer_verts
            self.snap_to_grid = preferences.increments_grid

            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (context,), 'WINDOW', 'POST_VIEW')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(SnapUtilitiesLine)

if __name__ == "__main__":
    register()