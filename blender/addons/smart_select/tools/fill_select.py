import bpy
from ..constants import DELIMIT_ITEMS
from ..utils import bmesh_utils as bmu


class SS_OT_fill_select(bpy.types.Operator):
    bl_idname = "ss.fill_select"
    bl_label = "Fill Select"
    bl_options = {'REGISTER', 'UNDO'}

    index = bpy.props.IntProperty(
        default=-1, options={'HIDDEN', 'SKIP_SAVE'})
    delimit = bpy.props.EnumProperty(
        name="Delimit",
        description="Delimit selected region",
        items=DELIMIT_ITEMS,
        default=set(),
        options={'ENUM_FLAG', 'SKIP_SAVE'})

    def walk_face(self, f, select):
        f.tag = True
        faces_a = [f]
        faces_b = []

        while faces_a:
            for f in faces_a:
                for l in f.loops:
                    l_edge = l.edge
                    if l_edge.select != select:
                        l_other = l.link_loop_radial_next
                        f_other = l_other.face
                        if not f_other.tag and f_other.select != select and \
                                f_other.index not in self.sel_faces:
                            yield f_other
                            f_other.tag = True
                            faces_b.append(f_other)

            faces_a, faces_b = faces_b, faces_a
            faces_b.clear()

    def walk_edge(self, edge, select):
        edge.tag = True
        edges_a = [edge]
        edges_b = []

        while edges_a:
            for e in edges_a:
                for f in e.link_faces:
                    for fe in f.edges:
                        if fe is e:
                            continue

                        if fe.select != select and \
                                not fe.tag and \
                                fe.index not in self.sel_edges:
                            yield fe
                            fe.tag = True
                            edges_b.append(fe)

            edges_a, edges_b = edges_b, edges_a
            edges_b.clear()

    def walk_vert(self, vert, select):
        vert.tag = True
        verts_a = [vert]
        verts_b = []

        while verts_a:
            for v in verts_a:
                for e in v.link_edges:
                    v_other = e.other_vert(v)
                    if v_other.select != select and \
                            not v_other.tag and \
                            v_other.index not in self.sel_verts:
                        yield v_other
                        v_other.tag = True
                        verts_b.append(v_other)

            verts_a, verts_b = verts_b, verts_a
            verts_b.clear()

    def fill_face(self, bm, face, select, mask):
        for f in bm.faces:
            f.tag = False

        face.tag = True

        self.sel_faces = set()
        for f in self.walk_face(face, select):
            self.sel_faces.add(f.index)

        face.select_set(select)
        for e in bm.faces:
            if e.index not in self.sel_faces:
                continue
            if not self.delimit or e.index in mask:
                bm.faces[e.index].select_set(select)

    def fill_edge(self, bm, edge, select, mask):
        for e in bm.edges:
            e.tag = False

        edge.tag = True

        self.sel_edges = set()
        for v in self.walk_edge(edge, select):
            self.sel_edges.add(v.index)

        edge.select_set(select)
        # with bmu.msm(True, True, True, True):
        if True:
            for e in bm.edges:
                if e.index not in self.sel_edges:
                    continue
                if not self.delimit or e.index in mask:
                    e.select_set(select)

            bm.select_flush_mode()

    def fill_vert(self, bm, vert, select, mask):
        for e in bm.verts:
            e.tag = False

        vert.tag = True

        self.sel_verts = set()
        for v in self.walk_vert(vert, select):
            self.sel_verts.add(v.index)

        vert.select_set(select)
        with bmu.msm(True, True, True, True):
            for e in bm.verts:
                if e.index not in self.sel_verts:
                    continue
                if not self.delimit or e.index in mask:
                    e.select_set(select)

            bm.select_flush_mode()

    def elems(self):
        if self.msm[2]:
            return self.bm.faces
        elif self.msm[0]:
            return self.bm.verts

        return self.bm.edges

    def execute(self, context):
        if not self.options.is_invoke:
            return {'CANCELLED'}

        self.bm = bmu.validate_bm(context.edit_object.data, self.bm)
        elem = self.elems()[self.elem_idx]

        if self.delimit:
            bpy.ops.mesh.select_all(action='DESELECT')
            elem.select_set(True)
            bpy.ops.mesh.select_linked(delimit=self.delimit)
            self.mask = {e.index for e in self.elems() if e.select}
            bmu.tuple_to_select(self.bm, self.selection)
        else:
            self.mask.clear()

        if self.msm[2]:
            self.fill_face(self.bm, elem, not self.deselect, self.mask)
        elif self.msm[0]:
            self.fill_vert(self.bm, elem, not self.deselect, self.mask)
        else:
            self.fill_edge(self.bm, elem, not self.deselect, self.mask)

        return {'FINISHED'}

    def invoke(self, context, event):
        me = context.edit_object.data
        self.msm = context.tool_settings.mesh_select_mode[:]
        self.bm = bmu.validate_bm(me)
        self.selection = bmu.select_to_tuple(self.bm)
        self.mask = set()

        if self.msm[2]:
            get_elem = bmu.get_face
            elem_msm = (False, False, True)
        elif self.msm[0]:
            get_elem = bmu.get_vert
            elem_msm = (True, False, False)
        else:
            get_elem = bmu.get_edge
            elem_msm = (False, True, False)

        if sum(self.msm) > 1:
            with bmu.sel(self.bm, me), bmu.msm(*elem_msm, uog=True):
                elem = get_elem(
                    self.bm, event.mouse_region_x, event.mouse_region_y)
        else:
            elem = get_elem(
                self.bm, event.mouse_region_x, event.mouse_region_y)

        if not elem:
            return {'CANCELLED'}

        self.elem_idx = elem.index
        self.deselect = elem.select

        return self.execute(context)

    @classmethod
    def poll(cls, context):
        ao = context.active_object
        return ao and ao.type == 'MESH' and ao.mode == 'EDIT'
