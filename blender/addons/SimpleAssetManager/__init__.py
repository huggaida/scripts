# -*- coding: utf-8 -*-
from bpy.types import WindowManager
import bpy.utils.previews
from bpy.props import BoolProperty, PointerProperty, \
    StringProperty, EnumProperty
import bpy
import bmesh
import os
import subprocess
from math import pi, cos, sin, radians
from mathutils import Euler

bl_info = {
    "name": "Simple Asset Manager",
    "description": "Manager for objects, materials, particles, "
                   "hdr. Before official.",
    "author": "Dawid Huczyński",
    "version": (0, 9, 5),
    "blender": (2, 80, 0),
    "location": "View 3D > Properties",
    "wiki_url": "https://gitlab.com/tibicen/simple-asset-manager",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export"
}

# TODO: append same object instance not new one
# TODO: search with recursion (how many subfolders to search)
# TODO: textures library
# TODO: row and columns in asset grid goes to preferences?
# TODO: add licence info

# FIXED: fix at origin import (all elements!)
# FIXED: fix non english characters Büro (german language) Kuchyně (czech language)
# FIXED: relative paths
# FIXED: random objects rendered (hide_select)

DEBUG = True

EXRS = ('city.exr', 'courtyard.exr', 'forest.exr', 'interior.exr',
        'night.exr', 'studio.exr', 'sunrise.exr', 'sunset.exr')
FORMATS = ('.blend', '.obj', '.fbx', '.hdr', '.exr')


def purge(data):
    # RENDER PREVIEW SCENE PREPARATION METHODS
    for el in data:
        if el.users == 0:
            data.remove(el)


def prepare_scene(blendFile):
    # clean scene
    for ob in bpy.data.objects:
        ob.hide_select = False
        ob.hide_render = False
        ob.hide_viewport = False
        ob.hide_set(False)
    for coll in bpy.data.collections:
        coll.hide_select = False
        coll.hide_render = False
        coll.hide_viewport = False
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)
    purge(bpy.data.collections)
    purge(bpy.data.objects)
    purge(bpy.data.cameras)
    purge(bpy.data.lights)
    purge(bpy.data.meshes)
    purge(bpy.data.particles)
    purge(bpy.data.materials)
    purge(bpy.data.textures)
    purge(bpy.data.images)
    purge(bpy.data.collections)
    # set output
    eevee = bpy.context.scene.eevee
    render = bpy.context.scene.render
    eevee.use_ssr_refraction = True
    eevee.use_ssr = True
    eevee.use_gtao = True
    eevee.gtao_distance = 1
    render.filepath = os.path.splitext(blendFile)[0]
    render.stamp_note_text = os.path.splitext(blendFile)[1][1:].upper()
    render.film_transparent = True
    render.resolution_x = 200
    render.resolution_y = 200
    render.use_stamp_date = False
    render.use_stamp_render_time = False
    render.use_stamp_camera = False
    render.use_stamp_scene = False
    render.use_stamp_filename = False
    render.use_stamp_frame = False
    render.use_stamp_time = False
    render.use_stamp = True
    render.use_stamp_note = True
    render.stamp_font_size = 20


def add_camera():
    cam = bpy.data.cameras.new('SAM_cam')
    cam_ob = bpy.data.objects.new('SAM_cam_ob', cam)
    bpy.context.collection.objects.link(cam_ob)
    cam_ob.rotation_euler = (pi / 2, 0, -pi / 6)
    cam.shift_y = -.3
    cam.lens = 71
    bpy.data.scenes[0].camera = cam_ob
    bpy.ops.view3d.camera_to_view_selected()
    return cam_ob


def find_layer(coll, lay_coll=None):
    if lay_coll is None:
        lay_coll = bpy.context.view_layer.layer_collection
    if lay_coll.collection == coll:
        return lay_coll
    else:
        for child in lay_coll.children:
            a = find_layer(coll, child)
            if a:
                return a
        return None


def import_scenes(blendFile, link):
    scenes = []
    with bpy.data.libraries.load(blendFile) as (data_from, data_to):
        for name in data_from.scenes:
            scenes.append({'name': name})
    action = bpy.ops.wm.link if link else bpy.ops.wm.append
    action(directory=blendFile + "/Scene/", files=scenes)
    scenes = bpy.data.scenes[-len(scenes):]


def append_element(blendFile, link=False):
    scenes = []
    asset_coll = bpy.data.collections['Assets']
    coll_name = os.path.splitext(
        os.path.basename(blendFile))[0].title()
    # if coll_name in bpy.data.collections.keys():
    #     bpy.ops.object.collection_instance_add(collection=coll_name)
    # else:
    obj_coll = bpy.data.collections.new(coll_name)
    asset_coll.children.link(obj_coll)
    obj_lay_coll = find_layer(obj_coll)
    bpy.context.view_layer.active_layer_collection = obj_lay_coll
    objects = []
    if blendFile.endswith('.obj'):
        bpy.ops.import_scene.obj(filepath=blendFile)
    elif blendFile.endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=blendFile)
    elif blendFile.endswith('.blend'):
        with bpy.data.libraries.load(blendFile) as (data_from, data_to):
            for name in data_from.scenes:
                scenes.append({'name': name})
        action = bpy.ops.wm.link if link else bpy.ops.wm.append
        action(directory=blendFile + "/Scene/", files=scenes)
        scenes = bpy.data.scenes[-len(scenes):]
        for scene in scenes:
            objs = 0
            for object in scene.collection.objects:
                # TODO: if there is any object in master collection
                obj_coll.objects.link(object)
                objs += 1
                objects.append(object)
            for coll in scene.collection.children:
                if coll.name.startswith('Collection'):
                    for object in coll.objects:
                        obj_coll.objects.link(object)
                        objects.append(object)
                    for sub_coll in coll.children:
                        obj_coll.children.link(sub_coll)
                else:
                    obj_coll.children.link(coll)
            bpy.data.scenes.remove(scene)
        for obj in objects:
            obj.select_set(True)


def append_hdr(blendFile):
    file = os.path.basename(blendFile)
    # check if already loaded
    if file in bpy.data.worlds.keys():
        world = bpy.data.worlds[file]
    else:
        bpy.ops.image.open(filepath=blendFile)
        im = bpy.data.images[file]
        world = bpy.data.worlds.new(file)
        world.use_nodes = True
        nodes = world.node_tree.nodes
        tex = nodes.new('ShaderNodeTexEnvironment')
        tex.image = im
        background = nodes['Background']
        world.node_tree.links.new(background.inputs['Color'],
                                  tex.outputs['Color'])
    bpy.context.scene.world = world


def append_material(blendFile, link=False):
    files = []
    with bpy.data.libraries.load(blendFile) as (data_from, data_to):
        for name in data_from.materials:
            files.append({'name': name})
    action = bpy.ops.wm.link if link else bpy.ops.wm.append
    action(directory=blendFile + "/Material/", files=files)
    return files


def append_particles(blendFile, link=False):
    particles = []
    asset_coll = bpy.data.collections['Assets']
    if "Particles" not in bpy.data.collections.keys():
        particles_coll = bpy.data.collections.new('Particles')
        asset_coll.children.link(particles_coll)
    else:
        particles_coll = bpy.data.collections['Particles']
    with bpy.data.libraries.load(blendFile) as (data_from, data_to):
        for name in data_from.particles:
            particles.append({'name': name})
    exists = True
    for name in [x['name'] for x in particles]:
        if name not in bpy.data.particles.keys():
            exists = False
    if exists:
        return particles
    coll_name = os.path.splitext(
        os.path.basename(blendFile))[0].title()
    obj_coll = bpy.data.collections.new(coll_name)
    particles_coll.children.link(obj_coll)
    obj_lay_coll = find_layer(obj_coll)
    bpy.context.view_layer.active_layer_collection = obj_lay_coll
    action = bpy.ops.wm.link if link else bpy.ops.wm.append
    colls = bpy.data.collections[:]
    action(directory=blendFile + "/ParticleSettings/", files=particles)
    # # doublecheck if collections are imported properly
    # for coll in bpy.data.collections:
    #     if coll not in colls:
    #         obj_coll.children.link(coll) # TODO
    #     for obj in coll.objects:
    #         if obj in obj_coll.objects.values():
    #             obj_coll.objects.unlink(obj)
    return particles


def rot_point(point, angle):
    angle = radians(angle)
    x, y = point
    rx = x * cos(angle) - y * sin(angle)
    ry = x * sin(angle) + y * cos(angle)
    return (rx, ry)


def rotate_uv(ob, angle):
    UV = ob.data.uv_layers[0]
    for v in ob.data.loops:
        UV.data[v.index].uv = rot_point(UV.data[v.index].uv, angle)


def set_scene_hdr(blendFile, cam):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,
                                         ring_count=32,
                                         location=(0, 0, 0))
    bpy.ops.object.shade_smooth()
    bpy.ops.object.material_slot_add()
    bpy.ops.material.new()
    ob = bpy.context.active_object
    mat = bpy.data.materials[-1]
    ob.material_slots[0].material = mat
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Metallic'].default_value = 1
    shader.inputs['Roughness'].default_value = 0
    append_hdr(blendFile)
    cam.rotation_euler = Euler((pi / 2, 0, 0), 'XYZ')
    cam.data.shift_y = 0
    cam.data.lens = 41


def set_scene_material(blendFile, cam):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,
                                         ring_count=32,
                                         location=(0, 0, 0))
    ob = bpy.context.active_object
    bpy.ops.object.editmode_toggle()
    bpy.ops.uv.sphere_project(direction='ALIGN_TO_OBJECT')
    mesh = bmesh.from_edit_mesh(ob.data)
    for v in mesh.verts:
        v.select = True if v.co[1] < 0 else False
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.uv.unwrap(method='CONFORMAL', margin=0)
    # bpy.ops.uv.pack_islands()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.uv.unwrap(method='CONFORMAL', margin=0)
    # bpy.ops.uv.pack_islands()
    bpy.ops.object.editmode_toggle()
    rotate_uv(ob, 46.5)
    bpy.ops.object.shade_smooth()
    bpy.ops.object.material_slot_add()
    # append material
    files = append_material(blendFile)
    name = files[0]['name']
    mat = bpy.data.materials[name]
    ob.material_slots[0].material = mat
    # modify camera settings
    cam.rotation_euler = Euler((pi / 2, 0, 0), 'XYZ')
    cam.data.shift_y = 0
    cam.data.lens = 41


def set_scene_particle_settings(blendFile):
    lay_coll = find_layer(bpy.context.scene.collection)
    bpy.context.view_layer.active_layer_collection = lay_coll
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,
                                         ring_count=32,
                                         enter_editmode=True,
                                         location=(0, 0, 0))
    bpy.ops.uv.sphere_project()
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.shade_smooth()
    sphere = bpy.context.active_object
    files = append_particles(blendFile)
    for f in files:
        name = f['name']
        bpy.ops.object.particle_system_add()
        settings = bpy.data.particles[name]
        sphere.particle_systems[-1].settings = settings
        # for render preview
        settings.child_nbr = settings.rendered_child_count
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        if ob.type == 'CAMERA' or ob == sphere:
            pass
        else:
            ob.select_set(True)
    bpy.context.view_layer.objects.active = sphere
    bpy.data.collections['Assets'].hide_viewport = True
    sphere.select_set(True)
    sphere.particle_systems[-1].seed = 1


class SAM_render_previews(bpy.types.Operator):
    bl_idname = "asset_manager.render_previews"
    bl_label = "(re)Render all previews"

    sub_process: BoolProperty()
    rerender: StringProperty()
    render_env: StringProperty()

    def execute(self, context):
        pref = context.preferences.addons[__name__].preferences
        if self.rerender == '':
            rerender = pref.rerender
        else:
            rerender = True if self.rerender == 'True' else False
        if 'Assets' not in bpy.context.scene.collection.children.keys():
            asset_coll = bpy.data.collections.new('Assets')
            context.scene.collection.children.link(asset_coll)
        else:
            asset_coll = bpy.data.collections['Assets']
        # IF is for rendering in separate blender instance
        if not self.sub_process:
            command = [bpy.app.binary_path,
                       "--python-expr",
                       'import bpy; bpy.ops.asset_manager.render_previews('
                       f'sub_process=True, rerender="{str(rerender)}", '
                       f'render_env="{str(pref.render_env)}");'
                       'bpy.context.preferences.view.use_save_prompt=False;'
                       'bpy.ops.wm.quit_blender();']
            subprocess.Popen(command)
            bpy.context.scene['asset_manager']['cat'] = 0
            pcoll = preview_collections["main"]
            pcoll.clear()
        else:
            lib_path = bpy.path.abspath(pref.lib_path)
            for r, d, fs in os.walk(lib_path):
                for f in fs:
                    render_type = 'RENDERED' if f.endswith(
                        ('.hdr', '.exr')) else 'MATERIAL'
                    if f.endswith(FORMATS):
                        blendFile = os.path.join(r, f)
                        png = os.path.splitext(blendFile)[0] + '.png'
                        if not rerender and os.path.exists(png):
                            continue
                        prepare_scene(blendFile)
                        cam = add_camera()
                        if f.endswith(('.hdr', '.exr')):
                            continue
                            # TODO: render previews like texture haven
                            # set_scene_hdr(blendFile, cam)
                        elif 'material' in r.lower():
                            set_scene_material(blendFile, cam)
                        elif 'particle' in r.lower():
                            set_scene_particle_settings(blendFile)
                        elif 'node' in r.lower():
                            pass
                        else:
                            append_element(blendFile)
                        bpy.ops.object.select_all(action='SELECT')
                        bpy.ops.view3d.camera_to_view_selected()
                        cam.data.lens = 40 if 'material' in r.lower() else 70
                        for area in bpy.context.screen.areas:
                            area.type = 'VIEW_3D'
                            space = area.spaces[0]
                            space.region_3d.view_perspective = 'CAMERA'
                            space.shading.type = render_type
                            space.overlay.show_overlays = False
                            if render_type == 'MATERIAL':
                                space.shading.studio_light = self.render_env
                        bpy.ops.render.opengl(write_still=True)
        return{'FINISHED'}


def execute_insert(context, link):
    active_layer = context.view_layer.active_layer_collection
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    selected_preview = bpy.data.window_managers["WinMan"].asset_manager_prevs
    folder = os.path.split(os.path.split(selected_preview)[0])[1]
    if 'Assets' not in bpy.context.scene.collection.children.keys():
        asset_coll = bpy.data.collections.new('Assets')
        context.scene.collection.children.link(asset_coll)
    else:
        asset_coll = bpy.data.collections['Assets']
    # Append objects
    if 'material' in folder.lower():
        return append_material(selected_preview, link)
    elif 'particle' in folder.lower():
        files = append_particles(selected_preview, link)
        context.view_layer.active_layer_collection = active_layer
        return files
    elif selected_preview.endswith(('.hdr', '.exr')):
        append_hdr(selected_preview)
    else:
        append_element(selected_preview, link)
        if context.scene.asset_manager.origin:
            if context.scene.asset_manager.incl_cursor_rot:
                temp = context.scene.tool_settings.transform_pivot_point
                context.scene.tool_settings.transform_pivot_point = 'CURSOR'
                cur = context.scene.cursor
                cur_loc = cur.location.copy()
                cur_rot = cur.rotation_euler.copy()
                cur.location = (0,0,0)
                cur.rotation_euler = (0,0,0)
                for x,y in list(zip(cur_rot,'XYZ')):
                    bpy.ops.transform.rotate(value=x,orient_axis=y)
                bpy.ops.transform.translate(value=cur_loc)
                cur.location = cur_loc
                cur.rotation_euler = cur_rot
                context.scene.tool_settings.transform_pivot_point = temp
            else:
                cur_loc = context.scene.cursor.location
                bpy.ops.transform.translate(value=cur_loc)
        context.view_layer.active_layer_collection = active_layer


class SAM_LinkButton(bpy.types.Operator):
    bl_idname = "asset_manager.link_object"
    bl_label = "Link"
    bl_description = 'Links object to scene'

    def execute(self, context):
        execute_insert(context, link=True)
        return{'FINISHED'}


class SAM_AppendButton(bpy.types.Operator):
    bl_idname = "asset_manager.append_object"
    bl_label = "Append"
    bl_description = 'Appends object to scene'

    def execute(self, context):
        execute_insert(context, link=False)
        return{'FINISHED'}


class SAM_AppendMaterialButton(bpy.types.Operator):
    bl_idname = "asset_manager.append_material"
    bl_label = "Append"
    bl_description = 'Adds material to blendfile'

    def execute(self, context):
        execute_insert(context, link=False)
        return{'FINISHED'}


class SAM_AddMaterialButton(bpy.types.Operator):
    bl_idname = "asset_manager.add_material"
    bl_label = "Add"
    bl_description = 'Adds material to object'

    def execute(self, context):
        active_ob = context.active_object
        wm = bpy.data.window_managers["WinMan"]
        for ob in bpy.context.scene.objects:
            ob.select_set(False)
        bpy.ops.object.select_all(action='DESELECT')
        selected_preview = wm.asset_manager_prevs
        files = append_material(selected_preview)
        for file in files:
            mat = bpy.data.materials[file['name']]
            active_ob.data.materials.append(mat)
        active_ob.select_set(True)
        return{'FINISHED'}


class SAM_ReplaceMaterialButton(bpy.types.Operator):
    bl_idname = "asset_manager.replace_material"
    bl_label = "Replace"
    bl_description = 'Replace objects material'

    def execute(self, context):
        active_ob = context.active_object
        wm = bpy.data.window_managers["WinMan"]
        for ob in bpy.context.scene.objects:
            ob.select_set(False)
        bpy.ops.object.select_all(action='DESELECT')
        selected_preview = wm.asset_manager_prevs
        files = append_material(selected_preview)
        for file in files:
            mat = bpy.data.materials[file['name']]
            active_ob.data.materials[active_ob.active_material_index] = mat
        active_ob.select_set(True)
        return{'FINISHED'}


class SAM_AddParticlesButton(bpy.types.Operator):
    bl_idname = "asset_manager.add_particles"
    bl_label = "Add to object"
    bl_description = 'Adds particles to object'

    def execute(self, context):
        active_ob = context.active_object
        bpy.ops.object.select_all(action='DESELECT')
        files = execute_insert(context, link=False)
        active_ob.select_set(True)
        for file in files:
            bpy.ops.object.particle_system_add()
            par_sys = active_ob.particle_systems[-1]
            par_sys.settings = bpy.data.particles[file['name']]
            par_sys.name = file['name']
        return{'FINISHED'}


class SAM_OpenButton(bpy.types.Operator):
    bl_idname = "asset_manager.open_file"
    bl_label = "Open File"

    def execute(self, context):
        addon_prefs = context.preferences.addons[__name__].preferences
        wm = bpy.data.window_managers["WinMan"]
        if addon_prefs.opensame:
            selected_preview = wm.asset_manager_prevs
            bpy.ops.wm.open_mainfile(filepath=selected_preview)
        else:
            selected_preview = wm.asset_manager_prevs
            command = [bpy.app.binary_path, selected_preview]
            subprocess.Popen(command)
        return{'FINISHED'}


# Update
def update_category(self, context):
    enum_previews_from_directory_items(self, context)


def search_library(self, context):  
    pref = context.preferences.addons[__name__].preferences
    lib_path = bpy.path.abspath(pref.lib_path)
    empty_path = os.path.join(os.path.dirname(__file__), 'empty.png')
    pcoll = preview_collections["main"]
    keyword = context.scene.asset_manager.search.lower()
    items = []
    enum_items = []
    for r,dirs,files in os.walk(lib_path):
        if keyword in ''.join(files).lower():
            for file in files:
                if keyword in file.lower():
                    prev = scan_for_elements(os.path.join(r,file))
                    if prev:
                        items.append(prev)
    enum_items = gen_thumbnails(items, enum_items, pcoll, empty_path)
    if len(enum_items) == 0:
        if 'empty' in pcoll:
            enum_items.append(('empty', '', "", pcoll['empty'].icon_id, 0))
        else:
            empty = pcoll.load('empty', empty_path, 'IMAGE')
            enum_items.append(('empty', '', '', empty.icon_id, 0))
    pcoll.asset_manager_prevs = enum_items
    bpy.data.window_managers[0]['asset_manager_prevs'] = 0
    


def subcategory_callout(self, context):
    global subcategories
    pref = context.preferences.addons[__name__].preferences
    lib_path = bpy.path.abspath(pref.lib_path)
    path = os.path.join(lib_path, self.cat)
    if self.cat in ('.', 'empty'):
        return [('empty', '', '', 0)]
    for r, d, f in os.walk(path):
        subcategories = sorted([(x, x, '', nr + 1) for nr, x in enumerate(d)])
        subcategories.insert(0, ('.', '.', '', 0))
        if len(subcategories) > 1:
            return subcategories
        else:
            bpy.context.scene['asset_manager']['subcat'] = 0
            return [('empty', '', '', 0), ]


def categories(self, context):
    global categories
    categories = []
    nr = 0
    pref = context.preferences.addons[__name__].preferences
    lib_path = bpy.path.abspath(pref.lib_path)
    for el in sorted(os.listdir(lib_path)):
        p = os.path.join(lib_path, el)
        if os.path.isdir(p) and not el.startswith('.'):
            nr += 1
            categories.append((el, el, '', nr))
    categories.insert(0, ('.', '.', '', 0))
    if len(categories) > 1:
        return categories
    else:
        bpy.context.scene['asset_manager']['cat'] = 0
        return [('empty', '', '', 0), ]


# Drop Down Menu
class SimpleAssetManager(bpy.types.PropertyGroup):
    cat: EnumProperty(
        items=categories,
        name="Category",
        description="Select a Category",
        update=update_category)

    subcat: EnumProperty(
        items=subcategory_callout,
        name="Subcategory",
        description="Select subcategory",
        update=update_category)

    origin: BoolProperty(
        name='Origin',
        description='Placement location')

    incl_cursor_rot: BoolProperty(
        name='Rotation',
        description='fIncludes cursor rotation on import.')
    
    search: StringProperty(
        name='Search',
        description='Search through whole library',
        update=search_library)


def scan_for_elements(path):
    if path.lower().endswith(FORMATS):
        png = os.path.splitext(path)[0] + '.png'
        if path.lower().endswith(('.hdr', '.exr')):
            return (path, True)
        elif os.path.exists(png):
            return (path, True)
        else:
            return (path, False)
    else:
        return None


def gen_thumbnails(image_paths, enum_items, pcoll, empty_path):
    # For each image in the directory, load the thumb
    # unless it has already been loaded
    for i, im in enumerate(image_paths):
        filepath, prev = im
        name = os.path.splitext(os.path.basename(filepath))[0]
        name = name.replace('.', ' ').replace('_', ' ').lower().capitalize()
        if filepath in pcoll:
            enum_items.append((filepath, name,
                               "", pcoll[filepath].icon_id, i))
        else:
            if prev:
                imgpath = filepath.rsplit('.', 1)[0] + '.png'
                if filepath.endswith(('.hdr', '.exr')):
                    imgpath = filepath
                thumb = pcoll.load(filepath, imgpath, 'IMAGE')
            else:
                thumb = pcoll.load(filepath, empty_path, 'IMAGE')
            enum_items.append((filepath, name,
                               "", thumb.icon_id, i))
    return enum_items


def enum_previews_from_directory_items(self, context):
    # Get the Preview Collection (defined in register func)
    pcoll = preview_collections["main"]
    pref = context.preferences.addons[__name__].preferences
    category = context.scene.asset_manager.cat
    subcategory = context.scene.asset_manager.subcat
    lib_path = bpy.path.abspath(pref.lib_path)
    empty_path = os.path.join(os.path.dirname(__file__), 'empty.png')
    enum_items = []
    if category in ('empty', '.'):
        directory = lib_path
    elif subcategory in ('empty', '.'):
        directory = os.path.join(lib_path, category)
    else:
        directory = os.path.join(lib_path, category, subcategory)
    # EnumProperty Callback
    if context is None:
        return enum_items
    # wm = context.window_manager
    if directory == pcoll.asset_manager_prev_dir:
        return pcoll.asset_manager_prevs
    print("Simple Asset Manager - Scanning directory: %s" % directory)
    if directory and os.path.exists(directory):
        image_paths = []
        for fn in os.listdir(directory):
            prev = scan_for_elements(os.path.join(directory,fn))
            if prev:
                image_paths.append(prev)

        enum_items = gen_thumbnails(image_paths, enum_items, pcoll,
                                    empty_path)
    # Return validation
    if len(enum_items) == 0:
        if 'empty' in pcoll:
            enum_items.append(('empty', '',
                               "", pcoll['empty'].icon_id, 0))
        else:
            empty = pcoll.load('empty', empty_path, 'IMAGE')
            enum_items.append(('empty', '', '', empty.icon_id, 0))
    pcoll.asset_manager_prevs = enum_items
    pcoll.asset_manager_prev_dir = directory
    bpy.data.window_managers[0]['asset_manager_prevs'] = 0
    return pcoll.asset_manager_prevs

from .ui import SAM_UI, SAM_Panel, SAM_Popup, SAM_PrefPanel, SAM_button

preview_collections = {}


#####################################################################
# Register

classes = (
    SAM_render_previews,
    SAM_LinkButton,
    SAM_AppendButton,
    SAM_AppendMaterialButton,
    SAM_AddMaterialButton,
    SAM_ReplaceMaterialButton,
    SAM_AddParticlesButton,
    SAM_OpenButton,
    SimpleAssetManager,
    SAM_Panel,
    SAM_Popup,
    SAM_PrefPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    WindowManager.asset_manager_prev_dir = StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
        default="")

    WindowManager.asset_manager_prevs = EnumProperty(
        items=enum_previews_from_directory_items)

    pcoll = bpy.utils.previews.new()
    pcoll.asset_manager_prev_dir = ""
    pcoll.asset_manager_prevs = ""

    preview_collections["main"] = pcoll
    bpy.types.Scene.asset_manager = PointerProperty(
        type=SimpleAssetManager)

    bpy.types.VIEW3D_MT_add.append(SAM_button)


# Unregister
def unregister():
    bpy.types.VIEW3D_MT_add.remove(SAM_button)
    del WindowManager.asset_manager_prevs

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.asset_manager


if __name__ == "__main__":
    register()
