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

import bpy, bgl

class CharMap:
    ascii = {
        ".", ",", "-", "+", "1", "2", "3",
        "4", "5", "6", "7", "8", "9", "0",
        "c", "m", "d", "k", "h", "a",
        " ", "/", "*", "'", "\""
        #"="
        }
    type = {
        'BACK_SPACE', 'DEL',
        'LEFT_ARROW', 'RIGHT_ARROW'
        }

    @staticmethod
    def modal(self, context, event):
        c = event.ascii
        if c:
            if c == ",":
                c = "."
            self.length_entered = self.length_entered[:self.line_pos] + c + self.length_entered[self.line_pos:]
            self.line_pos += 1
        if self.length_entered:
            if event.type == 'BACK_SPACE':
                self.length_entered = self.length_entered[:self.line_pos-1] + self.length_entered[self.line_pos:]
                self.line_pos -= 1

            elif event.type == 'DEL':
                self.length_entered = self.length_entered[:self.line_pos] + self.length_entered[self.line_pos+1:]

            elif event.type == 'LEFT_ARROW':
                self.line_pos = (self.line_pos - 1) % (len(self.length_entered)+1)

            elif event.type == 'RIGHT_ARROW':
                self.line_pos = (self.line_pos + 1) % (len(self.length_entered)+1)

class Common_Modals(bpy.types.Operator):
    def modal_navigation(self, context, event):
        #TO DO:
        #'View Orbit', 'View Pan', 'NDOF Orbit View', 'NDOF Pan View'
        rv3d = context.region_data
        if not hasattr(self, 'navigation_cache'): # or self.navigation_cache == False:
            #print('update navigation')
            self.navigation_cache = True
            self.keys_rotate = set()
            self.keys_move = set()
            self.keys_zoom = set()
            for key in context.window_manager.keyconfigs.user.keymaps['3D View'].keymap_items:
                if key.idname == 'view3d.rotate':
                    #self.keys_rotate[key.id]={'Alt': key.alt, 'Ctrl': key.ctrl, 'Shift':key.shift, 'Type':key.type, 'Value':key.value}
                    self.keys_rotate.add((key.alt, key.ctrl, key.shift, key.type, key.value))
                if key.idname == 'view3d.move':
                    self.keys_move.add((key.alt, key.ctrl, key.shift, key.type, key.value))
                if key.idname == 'view3d.zoom':
                    self.keys_zoom.add((key.alt, key.ctrl, key.shift, key.type, key.value, key.properties.delta))
                    if key.type == 'WHEELINMOUSE':
                        self.keys_zoom.add((key.alt, key.ctrl, key.shift, 'WHEELDOWNMOUSE', key.value, key.properties.delta))
                    if key.type == 'WHEELOUTMOUSE':
                        self.keys_zoom.add((key.alt, key.ctrl, key.shift, 'WHEELUPMOUSE', key.value, key.properties.delta))

        evkey = (event.alt, event.ctrl, event.shift, event.type, event.value)
        if evkey in self.keys_rotate:
            bpy.ops.view3d.rotate('INVOKE_DEFAULT')
        elif evkey in self.keys_move:
            if event.shift and self.vector_constrain and self.vector_constrain[2] in {'RIGHT_SHIFT', 'LEFT_SHIFT', 'shift'}:
                self.vector_constrain = None
            bpy.ops.view3d.move('INVOKE_DEFAULT')
        else:
            for key in self.keys_zoom:
                if evkey == key[0:5]:
                    delta = key[5]
                    if delta == 0:
                        bpy.ops.view3d.zoom('INVOKE_DEFAULT')
                    else:
                        rv3d.view_distance += delta*rv3d.view_distance/6
                        rv3d.view_location -= delta*(self.location - rv3d.view_location)/6
                    break

    def draw_callback_px(self, context):
        # draw 3d point OpenGL in the 3D View
        bgl.glEnable(bgl.GL_BLEND)

        if self.vector_constrain:
            vc = self.vector_constrain
            if hasattr(self, 'preloc') and self.type in {'VERT', 'FACE'}:
                bgl.glColor4f(1.0,1.0,1.0,0.5)
                bgl.glDepthRange(0,0)
                bgl.glPointSize(5)
                bgl.glBegin(bgl.GL_POINTS)
                bgl.glVertex3f(*self.preloc)
                bgl.glEnd()
            if vc[2] == 'X':
                Color4f = (self.axis_x_color + (1.0,))
            elif vc[2] == 'Y':
                Color4f = (self.axis_y_color + (1.0,))
            elif vc[2] == 'Z':
                Color4f = (self.axis_z_color + (1.0,))
            else:
                Color4f = self.constrain_shift_color
        else:
            if self.type == 'OUT':
                Color4f = self.out_color 
            elif self.type == 'FACE':
                Color4f = self.face_color
            elif self.type == 'EDGE':
                Color4f = self.edge_color
            elif self.type == 'VERT':
                Color4f = self.vert_color
            elif self.type == 'CENTER':
                Color4f = self.center_color
            elif self.type == 'PERPENDICULAR':
                Color4f = self.perpendicular_color
                
        bgl.glColor4f(*Color4f)
        bgl.glDepthRange(0,0)
        bgl.glPointSize(10)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex3f(*self.location)
        bgl.glEnd()
        bgl.glDisable(bgl.GL_BLEND)

        # draw 3d line OpenGL in the 3D View
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glDepthRange(0,0.9999)
        bgl.glColor4f(1.0, 0.8, 0.0, 1.0)    
        bgl.glLineWidth(2)    
        bgl.glEnable(bgl.GL_LINE_STIPPLE)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for vert_co in self.list_verts_co:
            bgl.glVertex3f(*vert_co)        
        bgl.glVertex3f(*self.location)        
        bgl.glEnd()
            
        # restore opengl defaults
        bgl.glDepthRange(0,1)
        bgl.glPointSize(1)
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_LINE_STIPPLE)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)