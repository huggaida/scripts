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

#python tip: from-imports don't save memory.
#They execute and cache the entire module just like a regular import.

import bmesh
from mathutils import Vector
from mathutils.geometry import (
    intersect_point_line,
    intersect_line_line,
    intersect_line_plane,
    intersect_ray_tri)

def get_units_info(scale, unit_system, separate_units):
    if unit_system == 'METRIC':
            scale_steps = ((1000, 'km'), (1, 'm'), (1 / 100, 'cm'),
                (1 / 1000, 'mm'), (1 / 1000000, '\u00b5m'))
    elif unit_system == 'IMPERIAL':
            scale_steps = ((5280, 'mi'), (1, '\''),
                (1 / 12, '"'), (1 / 12000, 'thou'))
            scale /= 0.3048  # BU to feet
    else:
            scale_steps = ((1, ' BU'),)
            separate_units = False

    return (scale, scale_steps, separate_units)

def convert_distance(val, units_info, PRECISION = 5):
    scale, scale_steps, separate_units = units_info
    sval = val * scale
    idx = 0
    while idx < len(scale_steps) - 1:
            if sval >= scale_steps[idx][0]:
                    break
            idx += 1
    factor, suffix = scale_steps[idx]
    sval /= factor
    if not separate_units or idx == len(scale_steps) - 1:
            dval = str(round(sval, PRECISION)) + suffix
    else:
            ival = int(sval)
            dval = str(round(ival, PRECISION)) + suffix
            fval = sval - ival
            idx += 1
            while idx < len(scale_steps):
                    fval *= scale_steps[idx - 1][0] / scale_steps[idx][0]
                    if fval >= 1:
                            dval += ' ' \
                                + ("%.1f" % fval) \
                                + scale_steps[idx][1]
                            break
                    idx += 1
    return dval

def location_3d_to_region_2d(region, rv3d, coord):
    prj = rv3d.perspective_matrix * coord.to_4d()
    width_half = region.width / 2.0
    height_half = region.height / 2.0
    return Vector((width_half + width_half * (prj.x / prj.w),
                   height_half + height_half * (prj.y / prj.w),
                   ))

def region_2d_to_orig_and_view_vector(region, rv3d, coord, clamp=None):
    viewinv = rv3d.view_matrix.inverted()
    persinv = rv3d.perspective_matrix.inverted()

    dx = (2.0 * coord[0] / region.width) - 1.0
    dy = (2.0 * coord[1] / region.height) - 1.0

    if rv3d.is_perspective:
        origin_start = viewinv.translation.copy()

        out = Vector((dx, dy, -0.5))

        w = out.dot(persinv[3].xyz) + persinv[3][3]

        view_vector = ((persinv * out) / w) - origin_start
    else:
        view_vector = -viewinv.col[2].xyz

        origin_start = ((persinv.col[0].xyz * dx) +
                        (persinv.col[1].xyz * dy) +
                        viewinv.translation)

        if clamp != 0.0:
            if rv3d.view_perspective != 'CAMERA':
                # this value is scaled to the far clip already
                origin_offset = persinv.col[2].xyz
                if clamp is not None:
                    if clamp < 0.0:
                        origin_offset.negate()
                        clamp = -clamp
                    if origin_offset.length > clamp:
                        origin_offset.length = clamp

                origin_start -= origin_offset

    view_vector.normalize()
    return origin_start, view_vector

def out_Location(rv3d, region, orig, vector):
    view_matrix = rv3d.view_matrix
    v1 = (int(view_matrix[0][0]*1.5),int(view_matrix[0][1]*1.5),int(view_matrix[0][2]*1.5))
    v2 = (int(view_matrix[1][0]*1.5),int(view_matrix[1][1]*1.5),int(view_matrix[1][2]*1.5))

    hit = intersect_ray_tri((1,0,0), (0,1,0), (0,0,0), (vector), (orig), False)
    if hit == None:
        hit = intersect_ray_tri(v1, v2, (0,0,0), (vector), (orig), False)        
    if hit == None:
        hit = intersect_ray_tri(v1, v2, (0,0,0), (-vector), (orig), False)
    if hit == None:
        hit = Vector()
    return hit

import bpy
B_VERSION = bpy.app.version
B_VERSION = B_VERSION[1] > 76 or (B_VERSION[1] == 76 and B_VERSION[2] >= 3)
def snap_utilities(self,
                context,
                obj_matrix_world,
                bm_geom,
                bool_update,
                mcursor,
                outer_verts = False,
                constrain = None,
                previous_vert = None,
                ignore_obj = None,
                increment = 0.0):

    rv3d = context.region_data
    region = context.region
    is_increment = False

    if not hasattr(self, 'snap_cache'):
        self.snap_cache = True
        self.type = 'OUT'
        self.bvert = None
        self.bedge = None
        self.bface = None
        self.hit = False
        self.out_obj = None

    if bool_update:
        #self.bvert = None
        self.bedge = None
        #self.bface = None

    if isinstance(bm_geom, bmesh.types.BMVert):
        self.type = 'VERT'

        if self.bvert != bm_geom:
            self.bvert = bm_geom
            self.vert = obj_matrix_world * self.bvert.co
            #self.Pvert = location_3d_to_region_2d(region, rv3d, self.vert)
        
        if constrain:
            #self.location = (self.vert-self.const).project(vector_constrain) + self.const
            location = intersect_point_line(self.vert, constrain[0], constrain[1])
            #factor = location[1]
            self.location = location[0]
        else:
            self.location = self.vert

    elif isinstance(bm_geom, bmesh.types.BMEdge):
        if self.bedge != bm_geom:
            self.bedge = bm_geom
            self.vert0 = obj_matrix_world*self.bedge.verts[0].co
            self.vert1 = obj_matrix_world*self.bedge.verts[1].co
            self.po_cent = (self.vert0+self.vert1)/2
            self.Pcent = location_3d_to_region_2d(region, rv3d, self.po_cent)
            self.Pvert0 = location_3d_to_region_2d(region, rv3d, self.vert0)
            self.Pvert1 = location_3d_to_region_2d(region, rv3d, self.vert1)
        
            if previous_vert and previous_vert not in self.bedge.verts:
                    pvert_co = obj_matrix_world*previous_vert.co
                    point_perpendicular = intersect_point_line(pvert_co, self.vert0, self.vert1)
                    self.po_perp = point_perpendicular[0]
                    #factor = point_perpendicular[1] 
                    self.Pperp = location_3d_to_region_2d(region, rv3d, self.po_perp)

        if constrain:
            location = intersect_line_line(constrain[0], constrain[1], self.vert0, self.vert1)
            if location == None:
                is_increment = True
                orig, view_vector = region_2d_to_orig_and_view_vector(region, rv3d, mcursor)
                end = orig + view_vector
                location = intersect_line_line(constrain[0], constrain[1], orig, end)
            if location:
                self.location = location[0]
            else:
                self.location = constrain[0]
        
        elif hasattr(self, 'Pperp') and abs(self.Pperp[0]-mcursor[0]) < 10 and abs(self.Pperp[1]-mcursor[1]) < 10:
            self.type = 'PERPENDICULAR'
            self.location = self.po_perp

        elif abs(self.Pcent[0]-mcursor[0]) < 10 and abs(self.Pcent[1]-mcursor[1]) < 10:
            self.type = 'CENTER'
            self.location = self.po_cent

        else:
            if increment and previous_vert in self.bedge.verts:
                is_increment = True
            self.type = 'EDGE'
            orig, view_vector = region_2d_to_orig_and_view_vector(region, rv3d, mcursor)
            end = orig + view_vector
            location = intersect_line_line(self.vert0, self.vert1, orig, end)
            if location:
                self.location = location[0]
            else: # Impossível, uma vez que não dá para selecionar essa edge.
                self.location = self.po_cent

    elif isinstance(bm_geom, bmesh.types.BMFace):
        is_increment = True
        self.type = 'FACE'

        if self.bface != bm_geom:
            self.bface = bm_geom
            self.face_center = obj_matrix_world*bm_geom.calc_center_median()
            self.face_normal = bm_geom.normal*obj_matrix_world.inverted()

        orig, view_vector = region_2d_to_orig_and_view_vector(region, rv3d, mcursor)
        end = orig + view_vector
        location = intersect_line_plane(orig, end, self.face_center, self.face_normal, False)
        if not location:
            l1 = self.bface.loops[0]
            l = l1.link_loop_next
            loc_orig = obj_matrix_world.inverted()*orig
            loc_ray = view_vector*obj_matrix_world
            while l != l1:
                location = intersect_ray_tri(l1.vert.co, l.vert.co, l.link_loop_next.vert.co, loc_ray, loc_orig, True)
                if location:
                    location = obj_matrix_world*location
                    print("intersect_ray_tri", location)
                    break
                l = l.link_loop_next
            else: # Pelo Clip ser True as vezes location pode ser None e isso dá erro
                location = self.face_center
            
        if constrain:
            is_increment = False
            location = intersect_point_line(location, constrain[0], constrain[1])[0]

        self.location = location

    else:
        is_increment = True
        self.type = 'OUT'

        orig, view_vector = region_2d_to_orig_and_view_vector(region, rv3d, mcursor)

        if B_VERSION:
            result, self.location, normal, face_index, self.out_obj, self.out_mat = context.scene.ray_cast(orig, view_vector, 3.3e+38)
            if result and self.out_obj != ignore_obj:
                self.type = 'FACE'
                if outer_verts:
                    if face_index != -1:
                        try:
                            verts = self.out_obj.data.polygons[face_index].vertices
                            v_dist = 100

                            for i in verts:
                                v_co = self.out_mat*self.out_obj.data.vertices[i].co
                                v_2d = location_3d_to_region_2d(region, rv3d, v_co)
                                dist = (Vector(mcursor)-v_2d).length_squared
                                if dist < v_dist:
                                    is_increment = False
                                    self.type = 'VERT'
                                    v_dist = dist
                                    self.location = v_co
                        except:
                            print('Fail')
                if constrain:
                    is_increment = False
                    self.preloc = self.location
                    self.location = intersect_point_line(self.preloc, constrain[0], constrain[1])[0]
            else:
                if constrain:
                    location = intersect_line_line(constrain[0], constrain[1], orig, orig+view_vector)
                    if location:
                        self.location = location[0]
                    else:
                        self.location = constrain[0]
                else:
                    self.location = out_Location(rv3d, region, orig, view_vector)

        else: ### VERSION 2.76 deprecated ###
            end = orig + view_vector * 1000

            result, self.out_obj, self.out_mat, self.location, normal = context.scene.ray_cast(orig, end)
            
            if result and self.out_obj != ignore_obj:
                self.type = 'FACE'
                if outer_verts:
                    # get the ray relative to the self.out_obj
                    self.out_mat_inv = self.out_mat.inverted()
                    ray_origin_obj = self.out_mat_inv * orig
                    ray_target_obj = self.out_mat_inv * end
                    try:
                        location, normal, face_index = self.out_obj.ray_cast(ray_origin_obj, ray_target_obj)
                        if face_index == -1:
                            self.out_obj = None
                        else:
                            self.location = self.out_mat*location
                            verts = self.out_obj.data.polygons[face_index].vertices
                            v_dist = 100

                            for i in verts:
                                v_co = self.out_mat*self.out_obj.data.vertices[i].co
                                v_2d = location_3d_to_region_2d(region, rv3d, v_co)
                                dist = (Vector(mcursor)-v_2d).length_squared
                                if dist < v_dist:
                                    is_increment = False
                                    self.type = 'VERT'
                                    v_dist = dist
                                    self.location = v_co
                    except Exception as e:
                        print(e)
                if constrain:
                    is_increment = False
                    self.preloc = self.location
                    self.location = intersect_point_line(self.preloc, constrain[0], constrain[1])[0]
            else:
                if constrain:
                    location = intersect_line_line(constrain[0], constrain[1], orig, end)
                    if location:
                        self.location = location[0]
                    else:
                        self.location = constrain[0]
                else:
                    self.location = out_Location(rv3d, region, orig, view_vector)
    ### END 2.76 VERSION ###

    if previous_vert:
        pvert_co = obj_matrix_world*previous_vert.co
        vec = self.location - pvert_co
        if is_increment and increment:
            pvert_co = obj_matrix_world*previous_vert.co
            vec = self.location - pvert_co
            self.len = round((1/increment)*vec.length)*increment
            self.location = self.len*vec.normalized() + pvert_co
        else:
            self.len = vec.length

    #return self.location, self.type