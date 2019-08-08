import bpy
import bmesh
from itertools import chain
from contextlib import contextmanager


@contextmanager
def sel(bm, me=None):
    sel_verts = {e.index for e in bm.verts if e.select}
    sel_edges = {e.index for e in bm.edges if e.select}
    sel_faces = {e.index for e in bm.faces if e.select}

    yield

    if me:
        bm = validate_bm(me, bm)

    for e in bm.faces:
        e.select_set(e.index in sel_faces)
    for e in bm.edges:
        e.select_set(e.index in sel_edges)
    for e in bm.verts:
        e.select_set(e.index in sel_verts)


@contextmanager
def uog(value):
    _uog = bpy.context.space_data.use_occlude_geometry
    bpy.context.space_data.use_occlude_geometry = value

    yield

    bpy.context.space_data.use_occlude_geometry = _uog


@contextmanager
def msm(verts, edges, faces, uog=None):
    _msm = bpy.context.tool_settings.mesh_select_mode[:]
    bpy.context.tool_settings.mesh_select_mode = (verts, edges, faces)

    if uog is not None:
        _uog = bpy.context.space_data.use_occlude_geometry
        bpy.context.space_data.use_occlude_geometry = uog

    yield

    bpy.context.tool_settings.mesh_select_mode = _msm

    if uog is not None:
        bpy.context.space_data.use_occlude_geometry = _uog


def validate_bm(mesh, bm=None):
    if not bm or not bm.is_valid:
        bm = bmesh.from_edit_mesh(mesh)

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    return bm


def select_to_tag(bm, verts=True, edges=True, faces=True):
    for e in chain(
            faces and bm.faces or [],
            edges and bm.edges or [],
            verts and bm.verts or []):
        e.tag = e.select


def select_to_tuple(bm, verts=True, edges=True, faces=True):
    return tuple(e.select for e in chain(
        faces and bm.faces or [],
        edges and bm.edges or [],
        verts and bm.verts or []))


def tag_to_select(bm, verts=True, edges=True, faces=True, op="set"):
    if op == "set":
        for e in chain(
                faces and bm.faces or [],
                edges and bm.edges or [],
                verts and bm.verts or []):
            e.select_set(e.tag)
    elif op == "add":
        for e in chain(
                faces and bm.faces or [],
                edges and bm.edges or [],
                verts and bm.verts or []):
            e.select_set(e.select or e.tag)
    elif op == "sub":
        for e in chain(
                faces and bm.faces or [],
                edges and bm.edges or [],
                verts and bm.verts or []):
            e.select_set(e.tag and not e.select)


def tuple_to_select(bm, tpl, verts=True, edges=True, faces=True, op="set"):
    if op == "set":
        for e, i in zip(chain(
                faces and bm.faces or [],
                edges and bm.edges or [],
                verts and bm.verts or []), tpl):
            e.select_set(i)
    elif op == "add":
        for e, i in zip(chain(
                faces and bm.faces or [],
                edges and bm.edges or [],
                verts and bm.verts or []), tpl):
            if i and not e.select:
                e.select_set(True)
    elif op == "sub":
        for e, i in zip(chain(
                faces and bm.faces or [],
                edges and bm.edges or [],
                verts and bm.verts or []), tpl):
            if i and e.select:
                e.select_set(False)


def get_elem(bm, x, y, verts=True, edges=True, faces=True):
    select_to_tag(bm, verts, edges, faces)

    elem = None
    ret = bpy.ops.view3d.select(extend=True, location=(x, y))
    if 'FINISHED' in ret:
        elem = bm.select_history.active

        if elem and not elem.tag:
            elem.select_set(False)
            bm.select_history.remove(elem)

    return elem


def get_vert(bm, x, y):
    return get_elem(bm, x, y, True, False, False)


def get_edge(bm, x, y):
    return get_elem(bm, x, y, False, True, False)


def get_face(bm, x, y):
    return get_elem(bm, x, y, False, False, True)
