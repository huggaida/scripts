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

import bpy, bmesh
from mathutils import Vector
from mathutils.geometry import intersect_line_line, intersect_point_line

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

class BVHco():
    i = 0
    c1x = 0.0
    c1y = 0.0
    c1z = 0.0
    c2x = 0.0
    c2y = 0.0
    c2z = 0.0

def edges_BVH_overlap(bm, edges, epsilon = 0.0001):
    bco = set()
    for e in edges:
        bvh = BVHco()
        bvh.i = e.index
        b1 = e.verts[0]
        b2 = e.verts[1]
        co1 = b1.co.x
        co2 = b2.co.x
        if co1 <= co2:
            bvh.c1x = co1 - epsilon
            bvh.c2x = co2 + epsilon
        else:
            bvh.c1x = co2 - epsilon
            bvh.c2x = co1 + epsilon
        co1 = b1.co.y
        co2 = b2.co.y
        if co1 <= co2:
            bvh.c1y = co1 - epsilon
            bvh.c2y = co2 + epsilon
        else:
            bvh.c1y = co2 - epsilon
            bvh.c2y = co1 + epsilon
        co1 = b1.co.z
        co2 = b2.co.z
        if co1 <= co2:
            bvh.c1z = co1 - epsilon
            bvh.c2z = co2 + epsilon
        else:
            bvh.c1z = co2 - epsilon
            bvh.c2z = co1 + epsilon
        bco.add(bvh)
    del edges
    overlap = {}
    oget = overlap.get
    for e1 in bm.edges:
        by = bz = True
        a1 = e1.verts[0]
        a2 = e1.verts[1]
        c1x = a1.co.x
        c2x = a2.co.x
        if c1x > c2x:
            tm = c1x
            c1x = c2x
            c2x = tm
        for bvh in bco:
            if c1x < bvh.c2x and c2x > bvh.c1x:
                if by:
                    by = False
                    c1y = a1.co.y
                    c2y = a2.co.y
                    if c1y > c2y:
                        tm = c1y
                        c1y = c2y
                        c2y = tm
                if c1y < bvh.c2y and c2y > bvh.c1y:
                    if bz:
                        bz = False
                        c1z = a1.co.z
                        c2z = a2.co.z
                        if c1z > c2z:
                            tm = c1z
                            c1z = c2z
                            c2z = tm
                    if c1z < bvh.c2z and c2z > bvh.c1z:
                        e2 = bm.edges[bvh.i]
                        if e1 != e2:
                            overlap[e1] = oget(e1, set()).union({e2})
    return overlap

def intersect_edges_edges(overlap, precision = 4):
    epsilon = .1**precision
    fpre_min = -epsilon
    fpre_max = 1+epsilon
    splits = {}
    sp_get = splits.get
    new_edges1 = set()
    new_edges2 = set()
    targetmap = {}
    for edg1 in overlap:
        #print("***", ed1.index, "***")
        for edg2 in overlap[edg1]:
            #print('loop', ed2.index)
            a1 = edg1.verts[0]
            a2 = edg1.verts[1]
            b1 = edg2.verts[0]
            b2 = edg2.verts[1]
            
            # test if are linked
            if a1 in {b1, b2} or a2 in {b1, b2}:
                #print('linked')
                continue

            aco1, aco2 = a1.co, a2.co
            bco1, bco2 = b1.co, b2.co
            tp = intersect_line_line(aco1, aco2, bco1, bco2)
            if tp:
                p1, p2 = tp
                if (p1 - p2).to_tuple(precision) == (0,0,0):
                    v = aco2-aco1
                    f = p1 - aco1
                    x,y,z = abs(v.x), abs(v.y), abs(v.z)
                    max1 = 0 if x >= y and x >= z else\
                           1 if y >= x and y >= z else 2
                    fac1 = f[max1]/v[max1]

                    v = bco2-bco1
                    f = p2 - bco1
                    x,y,z = abs(v.x), abs(v.y), abs(v.z)
                    max2 = 0 if x >= y and x >= z else\
                           1 if y >= x and y >= z else 2
                    fac2 = f[max2]/v[max2]

                    if fpre_min <= fac1 <= fpre_max:
                        #print(edg1.index, 'can intersect', edg2.index)
                        ed1 = edg1

                    elif edg1 in splits:
                        for ed1 in splits[edg1]:
                            a1 = ed1.verts[0]
                            a2 = ed1.verts[1]

                            vco1 = a1.co
                            vco2 = a2.co

                            v = vco2-vco1
                            f = p1 - vco1
                            fac1 = f[max1]/v[max1]
                            if fpre_min <= fac1 <= fpre_max:
                                #print(e.index, 'can intersect', edg2.index)
                                break
                        else:
                            #print(edg1.index, 'really does not intersect', edg2.index)
                            continue
                    else:
                        #print(edg1.index, 'not intersect', edg2.index)
                        continue

                    if fpre_min <= fac2 <= fpre_max:
                        #print(ed1.index, 'actually intersect', edg2.index)
                        ed2 = edg2

                    elif edg2 in splits:
                        for ed2 in splits[edg2]:
                            b1 = ed2.verts[0]
                            b2 = ed2.verts[1]

                            vco1 = b1.co
                            vco2 = b2.co

                            v = vco2-vco1
                            f = p2 - vco1
                            fac2 = f[max2]/v[max2]
                            if fpre_min <= fac2 <= fpre_max:
                                #print(ed1.index, 'actually intersect', e.index)
                                break
                        else:
                            #print(ed1.index, 'really does not intersect', ed2.index)
                            continue
                    else:
                        #print(ed1.index, 'not intersect', edg2.index)
                        continue

                    new_edges1.add(ed1)
                    new_edges2.add(ed2)

                    if abs(fac1) <= epsilon:
                        nv1 = a1
                    elif fac1 + epsilon >= 1:
                        nv1 = a2
                    else:
                        ne1, nv1 = bmesh.utils.edge_split(ed1, a1, fac1)
                        new_edges1.add(ne1)
                        splits[edg1] = sp_get(edg1, set()).union({ne1})

                    if abs(fac2) <= epsilon:
                        nv2 = b1
                    elif fac2 + epsilon >= 1:
                        nv2 = b2
                    else:
                        ne2, nv2 = bmesh.utils.edge_split(ed2, b1, fac2)
                        new_edges2.add(ne2)
                        splits[edg2] = sp_get(edg2, set()).union({ne2})

                    if nv1 != nv2: #necessary?
                        targetmap[nv1] = nv2
                #else:
                    #print('not coplanar')
            #else:
                #print("parallel or collinear")
    return new_edges1, new_edges2, targetmap

class SnapPushPullFace(Common_Modals):
    """ Draw edges. Connect them to split faces."""
    bl_label = "Push/Pull Face"
    bl_idname = "mesh.snap_push_pull"
    bl_context = "mesh_edit"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode in {'EDIT_MESH', 'OBJECT'} and
                context.object is not None and
                context.object.type == 'MESH')
    
    def modal(self, context, event):
        if event.type == 'MOUSEMOVE' or self.bool_update:
            context.area.tag_redraw()
            if self.rv3d.view_matrix != self.rotMat:
                self.rotMat = self.rv3d.view_matrix.copy()
                self.bool_update = True
            else:
                self.bool_update = False

            if self.bool_confirm:
                self.lgeom = self.geom

            if self.bm.select_history:
                self.geom = self.bm.select_history[0]
            else: #See IndexError or AttributeError:
                self.geom = None

            x, y = (event.mouse_region_x, event.mouse_region_y)
            if self.geom:
                self.geom.select = False
                self.bm.select_history.clear()

            bpy.ops.view3d.select(location=(x, y))           

            if self.bool_confirm and\
                (self.lgeom in self.ret or self.geom in self.ret):
                    if self.bm.faces.active:
                        self.bm.faces.active.select = False
                        self.bm.faces.active = None
                    if self.lgeom:
                        self.lgeom.select = False
                    elif self.geom:
                        self.geom.select = False
                    self.type = 'FACE'
                    orig, vector = region_2d_to_orig_and_view_vector(self.region, self.rv3d, (x, y))
                    location = intersect_line_line(self.pull_constrain[0], self.pull_constrain[1], orig, (orig+vector))
                    if not location:
                        location = self.pull_constrain[:1]
                    bmesh.ops.translate(self.bm,
                        vec = location[0] - self.obj_matrix*self.face.calc_center_median(),
                        space = self.obj_matrix,
                        verts = self.face.verts)
                    self.location = location[0]

            else:
                if self.list_verts != []:
                    bm_vert_to_perpendicular = self.list_verts[-1]
                else:
                    bm_vert_to_perpendicular = None

                outer_verts = self.outer_verts and not self.keytab

                if self.type == 'OUT':
                    constrain = self.pull_constrain
                else:
                    constrain = None

                snap_utilities(self,
                    context,
                    self.obj_matrix,
                    self.geom,
                    self.bool_update,
                    (x, y), 
                    outer_verts = self.outer_verts,
                    constrain = constrain,
                    #previous_vert = previous_vert,
                    ignore_obj = self.obj,
                    increment = self.incremental,
                    )
                
                if self.bool_confirm:
                    if self.bm.faces.active in self.ret:
                        self.bm.faces.active.select = False
                        self.bm.faces.active = None
                    location = intersect_point_line(self.location, self.pull_constrain[0], self.pull_constrain[1])[0]
                    bmesh.ops.translate(self.bm,
                        vec = location - self.obj_matrix*self.face.calc_center_median(),
                        space = self.obj_matrix,
                        verts = self.face.verts)

        elif (event.value == 'PRESS' and event.type == 'LEFTMOUSE') or\
            (event.value == 'RELEASE' and event.type in {'RET', 'NUMPAD_ENTER'}):
                self.bool_confirm = self.bool_confirm == False and self.geom != None
                #print(self.bool_confirm)
                if self.bool_confirm:
                    #self.bool_confirm = False
                    bpy.ops.ed.undo_push(message="Push Pull Face")
                    self.mesh = self.obj.data
                    sface = self.geom
                    #face.select = False
                    #bpy.ops.mesh.select_all(action='DESELECT')
                    geom = []
                    for edge in sface.edges:
                        if abs(edge.calc_face_angle(0) - 1.5707963267948966) < 0.01: #self.angle_tolerance:
                            geom.append(edge)

                    fdict = bmesh.ops.extrude_discrete_faces(self.bm, faces = [sface])

                    for face in fdict['faces']:
                        self.bm.faces.active = face
                        face.select = True
                        self.face = face

                    dfaces = bmesh.ops.dissolve_edges(self.bm, edges = geom, use_verts=True, use_face_split=False)

                    bmesh.update_edit_mesh(self.mesh, tessface=True, destructive=True)

                    context.tool_settings.mesh_select_mode = (True, True, True)
                    center = self.obj_matrix*self.face.calc_center_median()
                    normal = self.face.normal*self.obj_matrix.inverted()
                    self.pull_constrain = (center, center+normal, 'push_pull')
                    ret = [(v.link_edges[:]+v.link_faces[:]+[v]) for v in self.face.verts]
                    self.ret = [x for y in ret for x in y]
                    #bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(False, False, True), constraint_orientation='NORMAL', release_confirm=True)
                    return {'RUNNING_MODAL'}

                else:
                    if self.length_entered != "" and self.pull_constrain:
                        try:
                            text_value = bpy.utils.units.to_value(self.unit_system, 'LENGTH', self.length_entered)
                            vector = (self.pull_constrain[1]-self.pull_constrain[0]).normalized()
                            location = (self.pull_constrain[0]+(vector*text_value))
                            G_location = self.obj_matrix.inverted()*location
                            bmesh.ops.translate(self.bm,
                                vec = location - self.obj_matrix*self.face.calc_center_median(),
                                space = self.obj_matrix,
                                verts = self.face.verts)

                            self.length_entered = ""

                        except:# ValueError:
                            self.length_entered = ""
                            self.report({'INFO'}, "Operation not supported yet")

                    sface = self.face
                    # edges to intersect
                    edges = set()
                    [[edges.add(ed) for ed in v.link_edges] for v in sface.verts]

                    overlap = edges_BVH_overlap(self.bm, edges, epsilon = 0.0001)
                    overlap = {k: v for k,v in overlap.items() if k not in edges} # remove repetition

                    # add vertices where intersect
                    new_edges1, new_edges2, targetmap = intersect_edges_edges(overlap)
                    pos_weld = set()
                    for e in new_edges1:
                        v1, v2 = e.verts
                        if v1 in targetmap and v2 in targetmap:
                            pos_weld.add((targetmap[v1], targetmap[v2]))
                    if targetmap:
                        bmesh.ops.weld_verts(self.bm, targetmap=targetmap)
                    for e in pos_weld:
                        try:
                            v1, v2 = e
                            lf1 = set(v1.link_faces)
                            lf2 = set(v2.link_faces)
                            rlfe = lf1.intersection(lf2)
                            for f in rlfe:
                                bmesh.utils.face_split(f, v1, v2)
                        except:
                            #print(Exception)
                            pass
                        
                    for e in new_edges2:
                        try:
                            lfe = set(e.link_faces)
                            v1, v2 = e.verts
                            lf1 = set(v1.link_faces)
                            lf2 = set(v2.link_faces)
                            rlfe = lf1.intersection(lf2)
                            for f in rlfe.difference(lfe):
                                bmesh.utils.face_split(f, v1, v2)
                        except Exception as e:
                            print(e)
                    
                    bmesh.update_edit_mesh(self.mesh, tessface=True, destructive=True)
                    context.tool_settings.mesh_select_mode = (False, False, True)
                    self.pull_constrain = None

        elif event.value == 'PRESS':
            if self.bool_confirm and (event.ascii in CharMap.ascii or event.type in CharMap.type):
                CharMap.modal(self, context, event)
                
            elif self.bool_confirm and event.type == 'TAB':
                self.keytab = self.keytab == False
                if self.keytab:
                    context.tool_settings.mesh_select_mode = (False, False, True)
                else:
                    context.tool_settings.mesh_select_mode = (True, True, True)

        elif event.value == 'RELEASE':
            if self.bool_confirm and event.type in {'RET', 'NUMPAD_ENTER'}:
                if self.length_entered != "" and self.list_verts_co != []:
                    try:
                        text_value = bpy.utils.units.to_value(self.unit_system, 'LENGTH', self.length_entered)
                        vector = (self.location-self.list_verts_co[-1]).normalized()
                        location = (self.list_verts_co[-1]+(vector*text_value))
                        G_location = self.obj_matrix.inverted()*location
                        self.list_verts_co = draw_line(self, self.obj, self.bm, self.geom, G_location)
                        self.length_entered = ""

                    except:# ValueError:
                        self.report({'INFO'}, "Operation not supported yet")

            elif event.type in {'RIGHTMOUSE', 'ESC'}:
                if self.list_verts_co == [] or event.type == 'ESC':                
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    context.tool_settings.mesh_select_mode = self.select_mode
                    context.area.header_text_set()
                    context.user_preferences.view.use_rotate_around_active = self.use_rotate_around_active
                    if not self.is_editmode:
                        bpy.ops.object.editmode_toggle()
                    return {'FINISHED'}
                else:
                    self.pull_constrain = None
                    self.list_verts_co = []

        a = ""        
        if self.pull_constrain:
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
            self.bool_confirm = False

            preferences = context.user_preferences.addons[__package__].preferences
            #bgl.glEnable(bgl.GL_POINT_SMOOTH)

            self.is_editmode = context.object.data.is_editmode
            bpy.ops.object.mode_set(mode='EDIT')
            context.space_data.use_occlude_geometry = True

            self.scale = context.scene.unit_settings.scale_length
            self.unit_system = context.scene.unit_settings.system
            self.separate_units = context.scene.unit_settings.use_separate
            self.uinfo = get_units_info(self.scale, self.unit_system, self.separate_units)

            grid = context.scene.unit_settings.scale_length/context.space_data.grid_scale
            relative_scale = preferences.relative_scale
            self.scale = grid/relative_scale

            incremental = preferences.incremental
            self.incremental = bpy.utils.units.to_value(self.unit_system, 'LENGTH', str(incremental))

            self.use_rotate_around_active = context.user_preferences.view.use_rotate_around_active
            context.user_preferences.view.use_rotate_around_active = True
            
            self.select_mode = context.tool_settings.mesh_select_mode[:]
            context.tool_settings.mesh_select_mode = (False, False, True)
            
            self.region = context.region
            self.rv3d = context.region_data
            self.rotMat = self.rv3d.view_matrix.copy()
            self.obj = context.active_object
            self.obj_matrix = self.obj.matrix_world.copy()
            self.obj_mt_inv = self.obj_matrix.inverted()
            self.bm = bmesh.from_edit_mesh(self.obj.data)
            
            self.location = Vector()
            self.list_verts = []
            self.list_verts_co = []
            self.bool_update = False
            self.vector_constrain = None
            self.pull_constrain = None
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
    print('register PushPullFace')
    bpy.utils.register_class(SnapPushPullFace)

if __name__ == "__main__":
    register()