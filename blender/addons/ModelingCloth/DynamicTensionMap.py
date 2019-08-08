import bpy
import numpy as np
from numpy import newaxis as nax
import bmesh


bl_info = {
    "name": "Dynamic Tension Map",
    "author": "Rich Colburn, email: the3dadvantage@gmail.com",
    "version": (1, 0),
    "blender": (2, 78, 0),
    "location": "View3D > Extended Tools > Tension Map",
    "description": "Compares the current state of the mesh agains a stored version and displays stretched edges as a color",
    "warning": "'For the empire!' should not be shouted when paying for gum.",
    "wiki_url": "",
    "category": '3D View'}


def hide_unhide_store(ob=None, unhide=True, storage=None):
    """Stores the hidden state of the geometry, """
    if ob is None:
        ob = bpy.context.object
    if ob is None:
        return 'No mesh object'
    
    if unhide:
        v = np.zeros(len(ob.data.vertices), dtype=np.bool)
        e = np.zeros(len(ob.data.edges), dtype=np.bool)
        f = np.zeros(len(ob.data.polygons), dtype=np.bool)
        vsel = np.zeros(len(ob.data.vertices), dtype=np.bool)
        esel = np.zeros(len(ob.data.edges), dtype=np.bool)
        fsel = np.zeros(len(ob.data.polygons), dtype=np.bool)        
        if storage is not None:
            ob.data.vertices.foreach_get('hide', v)
            ob.data.edges.foreach_get('hide', e)
            ob.data.polygons.foreach_get('hide', f)

            ob.data.vertices.foreach_get('select', vsel)
            ob.data.edges.foreach_get('select', esel)
            ob.data.polygons.foreach_get('select', fsel)

            
            storage['hide'] = {}
            storage['hide']['v'] = np.copy(v)
            storage['hide']['e'] = np.copy(e)
            storage['hide']['f'] = np.copy(f)
            
            storage['hide']['vsel'] = np.copy(vsel)
            storage['hide']['esel'] = np.copy(esel)
            storage['hide']['fsel'] = np.copy(fsel)

        
        v[:] = False
        e[:] = False
        f[:] = False

        ob.data.vertices.foreach_set('hide', v)
        ob.data.edges.foreach_set('hide', e)
        ob.data.polygons.foreach_set('hide', f)    
    else:
        ob.data.vertices.foreach_set('hide', storage['hide']['v'])
        ob.data.edges.foreach_set('hide', storage['hide']['e'])
        ob.data.polygons.foreach_set('hide', storage['hide']['f'])

        ob.data.vertices.foreach_set('select', storage['hide']['vsel'])
        ob.data.edges.foreach_set('select', storage['hide']['esel'])
        ob.data.polygons.foreach_set('select', storage['hide']['fsel'])
        

def get_key_coords(ob=None, key='Basis', proxy=False):
    '''Creates an N x 3 numpy array of vertex coords.
    from shape keys'''
    if key is None:
        return get_coords(ob)
    if proxy:
        mesh = proxy.to_mesh(bpy.context.scene, True, 'PREVIEW')
        verts = mesh.data.shape_keys.key_blocks[key].data
    else:
        verts = ob.data.shape_keys.key_blocks[key].data
    v_count = len(verts)
    coords = np.zeros(v_count * 3, dtype=np.float32)
    verts.foreach_get("co", coords)
    if proxy:
        bpy.data.meshes.remove(mesh)
    return coords.reshape(v_count, 3)


def get_coords(ob=None, proxy=False):
    '''Creates an N x 3 numpy array of vertex coords. If proxy is used the
    coords are taken from the object specified with modifiers evaluated.
    For the proxy argument put in the object: get_coords(ob, proxy_ob)'''
    if ob is None:
        ob = bpy.context.object
    if proxy:
        mesh = proxy.to_mesh(bpy.context.scene, True, 'PREVIEW')
        verts = mesh.vertices
    else:
        verts = ob.data.vertices
    v_count = len(verts)
    coords = np.zeros(v_count * 3, dtype=np.float32)
    verts.foreach_get("co", coords)
    if proxy:
        bpy.data.meshes.remove(mesh)
    return coords.reshape(v_count, 3)


def get_edge_idx(ob=None):
    if ob is None:
        ob = bpy.context.object
    ed = np.zeros(len(ob.data.edges)*2, dtype=np.int32)
    ob.data.edges.foreach_get('vertices', ed)
    return ed.reshape(len(ed)//2, 2)


def get_bmesh(ob=None):
    '''Returns a bmesh. Works either in edit or object mode.
    ob can be either an object or a mesh.'''
    obm = bmesh.new()
    if ob is None:
        mesh = bpy.context.object.data
    if 'data' in dir(ob):
        mesh = ob.data
        if ob.mode == 'OBJECT':
            obm.from_mesh(mesh)
        elif ob.mode == 'EDIT':
            obm = bmesh.from_edit_mesh(mesh)    
    else:
        mesh = ob
        obm.from_mesh(mesh)
    return obm


def material_setup(ob=None):
    '''Creates a node material for displaying the vertex colors'''
    if ob is None:
        ob = bpy.context.object
    mats = bpy.data.materials
    tens = mats.new('TensionMap')
    data[ob.name]['material'] = tens
    tens.use_nodes = True
    tens.specular_intensity = 0.1
    tens.specular_hardness = 17
    tens.use_transparency = True
    tens.node_tree.nodes.new(type="ShaderNodeGeometry")
    tens.node_tree.links.new(tens.node_tree.nodes['Geometry'].outputs['Vertex Color'], 
        tens.node_tree.nodes['Material'].inputs[0])
    if 'Tension' not in ob.data.vertex_colors:    
        ob.data.vertex_colors.new('Tension')
    ob.data.materials.append(tens)
    tens.node_tree.nodes['Geometry'].color_layer = 'Tension'
    tens.node_tree.nodes['Material'].material = tens


def reassign_mats(ob=None, type=None):
    '''Resets materials based on stored face indices'''
    if ob is None:
        ob = bpy.context.object
    if type == 'off':
        ob.data.polygons.foreach_set('material_index', data[ob.name]['mat_index'])
        ob.data.update()
        idx = ob.data.materials.find(data[ob.name]['material'].name)        
        if idx != -1:    
            ob.data.materials.pop(idx, update_data=True)
        bpy.data.materials.remove(data[ob.name]['material'])
        del(data[ob.name])    
    if type == 'on':
        idx = ob.data.materials.find(data[ob.name]['material'].name)
        mat_idx = np.zeros(len(ob.data.polygons), dtype=np.int32) + idx
        ob.data.polygons.foreach_set('material_index', mat_idx)
        ob.data.update()


def initalize(ob, key):
    '''Set up the indexing for viewing each edge per vert per face loop'''
    obm = get_bmesh(ob)
    ed_pairs_per_v = []
    for f in obm.faces:
        for v in f.verts:
            set = []
            for e in f.edges:
                if v in e.verts:
                    set.append(e.index)
            ed_pairs_per_v.append(set)    
    data[ob.name]['ed_pairs_per_v'] = np.array(ed_pairs_per_v)
    data[ob.name]['zeros'] = np.zeros(len(data[ob.name]['ed_pairs_per_v']) * 3).reshape(len(data[ob.name]['ed_pairs_per_v']), 3)
    key_coords = get_key_coords(ob, key)
    ed1 = get_edge_idx(ob)
    #linked = np.array([len(i.link_faces) for i in obm.edges]) > 0
    data[ob.name]['edges'] = get_edge_idx(ob)#[linked]
    dif = key_coords[data[ob.name]['edges'][:,0]] - key_coords[data[ob.name]['edges'][:,1]]
    data[ob.name]['mags'] = np.sqrt(np.einsum('ij,ij->i', dif, dif))
    mat_idx = np.zeros(len(ob.data.polygons), dtype=np.int64)
    ob.data.polygons.foreach_get('material_index', mat_idx)
    data[ob.name]['mat_index'] = mat_idx
    if 'material' not in data[ob.name]:
        print('ran this')
        material_setup(ob)


def dynamic_tension_handler(scene):
    stretch = bpy.context.scene.dynamic_tension_map_max_stretch / 100
    items = data.items()
    if len(items) == 0:
        for i in bpy.data.objects:
            i.dynamic_tension_map_on = False
        
        for i in bpy.app.handlers.scene_update_post:
            if i.__name__ == 'dynamic_tension_handler':
                bpy.app.handlers.scene_update_post.remove(i)
    
    for i, value in items:    
        if i in bpy.data.objects:
            update(ob=bpy.data.objects[i], max_stretch=stretch, bleed=0.2)   
        else:
            del(data[i])
            break


def prop_callback(self, context):
    stretch = bpy.context.scene.dynamic_tension_map_max_stretch / 100
    edit=False
    ob = bpy.context.object
    if not ob.dynamic_tension_map_on:
        return
    if ob.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
        edit = True
    update(coords=None, ob=None, max_stretch=stretch, bleed=0.2)    
    if edit:
        bpy.ops.object.mode_set(mode='EDIT')
        
    
def update(coords=None, ob=None, max_stretch=1, bleed=0.2):
    '''Measure the edges against the stored lengths.
    Look up those distances with fancy indexing on
    a per-vertex basis.'''
    if ob is None:
        ob = bpy.context.object
    
    if data[ob.name]['source']:
        coords = get_key_coords(ob, 'modeling cloth key')
    if bpy.context.scene.dynamic_tension_map_show_from_flat:
        if ob.data.shape_keys is not None:
            if len(ob.data.shape_keys.key_blocks) > 1:
                coords = get_key_coords(ob, ob.data.shape_keys.key_blocks[1].name)
    if coords is None:
        coords = get_coords(ob, ob)
        
    dif = coords[data[ob.name]['edges'][:,0]] - coords[data[ob.name]['edges'][:,1]]
    mags = np.sqrt(np.einsum('ij,ij->i', dif, dif))
    if bpy.context.scene.dynamic_tension_map_percentage:    
        div = (mags / data[ob.name]['mags']) - 1
    else:
        div = mags - data[ob.name]['mags']
    color = data[ob.name]['zeros']
    eye = np.eye(3,3)
    G, B = eye[1], eye[2]
    ed_pairs = data[ob.name]['ed_pairs_per_v']
    mix = np.mean(div[ed_pairs], axis=1)
    mid = (max_stretch) * 0.5     
    BG_range = mix < mid
    GR_range = -BG_range

    #to_y = np.array([ 0,  1, -1]) / np.clip(max_stretch, 0, 100)
    to_y = np.array([ 0,  1, -1]) / max_stretch
    #to_x = np.array([ 1, -1,  0]) / np.clip(max_stretch, 0, 100)
    to_x = np.array([ 1, -1,  0]) / max_stretch

    BG_blend = to_y * (mix[BG_range])[:, nax]
    GR_blend = to_x * (mix[GR_range])[:, nax]
    
    color[BG_range] = B
    color[BG_range] += BG_blend
    color[GR_range] = G
    color[GR_range] += GR_blend

    UV = np.nan_to_num(color / np.sqrt(np.einsum('ij,ij->i', color, color)[:, nax]))
    ob.data.vertex_colors["Tension"].data.foreach_set('color', UV.ravel())
    ob.data.update()
    

def toggle_display(self, context):
    global data
    data = bpy.context.scene.dynamic_tension_map_dict
    source = False
    use_key = False
    if self.type == 'MESH':
        
        keys = self.data.shape_keys
        if keys != None:
            if 'RestShape' in keys.key_blocks:    
                key = 'RestShape'
    
            elif 'modeling cloth source key' in keys.key_blocks:
                key = 'modeling cloth source key'
                source = True
            else:
                key = keys.key_blocks[0].name

            use_key = True
                
        if self.dynamic_tension_map_on:
            # to avoid duplicating the material:
            mat = None
            if self.name in data:
                if 'material' in data[self.name]:
                    mat = data[self.name]['material']
            
            #---
            data[self.name] = {}
            data[self.name]['source'] = source
            if mat is not None:    
                data[self.name]['material'] = mat
            if use_key:    
                initalize(self, key)
            else:
                initalize(self, None)
            reassign_mats(self, 'on')
            self.data.vertex_colors['Tension'].active = True
        else:
            if self.name in data:
                reassign_mats(self, 'off')
        
        prop_callback(bpy.context.scene, bpy.context)
        
        for i in bpy.app.handlers.scene_update_post:
            if i.__name__ == 'dynamic_tension_handler':
                return

        bpy.app.handlers.scene_update_post.append(dynamic_tension_handler)        


def pattern_on_off(self, context):
    if self.dynamic_tension_flat_pattern_on:
        self.data.shape_keys.key_blocks[1].value = 1
        self.active_shape_key_index = 1
        
    else:
        self.data.shape_keys.key_blocks[1].value = 0
        self.active_shape_key_index = 0

def tension_from_flat_update(self, context):
    toggle_display(bpy.context.object, context)
    prop_callback(bpy.context.scene, bpy.context)

        
# Create Properties----------------------------:
def percentage_prop_update(self, context):
    if self.dynamic_tension_map_percentage:
        self['dynamic_tension_map_edge'] = False
    else:
        self['dynamic_tension_map_edge'] = True        

    
def edge_prop_update(self, context):
    if self.dynamic_tension_map_edge:
        self['dynamic_tension_map_percentage'] = False
    else:
        self['dynamic_tension_map_percentage'] = True

        
def create_properties():            
    
    bpy.types.Object.dynamic_tension_map_on = bpy.props.BoolProperty(name="Dynamic Tension Map On", 
        description="Amount of stretch on an edge is blender units. ", 
        default=False, update=toggle_display)

    bpy.types.Scene.dynamic_tension_map_max_stretch = bpy.props.FloatProperty(name="avatar height", 
        description="Stretch distance where tension map appears red", default=20, min=0.001, max=200,  precision=2, update=prop_callback)

    bpy.types.Scene.dynamic_tension_map_percentage = bpy.props.BoolProperty(name="Dynamic Tension Map Percentage", 
        description="For toggling between percentage and geometry", 
        default=True, update=percentage_prop_update)

    bpy.types.Scene.dynamic_tension_map_edge = bpy.props.BoolProperty(name="Dynamic Tension Map Edge", 
        description="For toggling between percentage and geometry", 
        default=False, update=edge_prop_update)

    bpy.types.Scene.dynamic_tension_map_show_from_flat = bpy.props.BoolProperty(name="Dynamic Tension From Flat", 
        description="Tension is displayed as the difference between the current shape and the source shape.", 
        default=False, update=tension_from_flat_update)

    bpy.types.Object.dynamic_tension_flat_pattern_on = bpy.props.BoolProperty(name="Dynamic Tension Flat Pattern On", 
        description="Toggles the flat pattern shape on and off.", 
        default=False, update=pattern_on_off)

    # create data dictionary
    bpy.types.Scene.dynamic_tension_map_dict = {}
    bpy.types.Scene.dynamic_tension_map_selection = {}


def remove_properties():
        
    del(bpy.types.Object.dynamic_tension_map_on)
    del(bpy.types.Scene.dynamic_tension_map_max_stretch)
    del(bpy.types.Scene.dynamic_tension_map_percentage)
    del(bpy.types.Scene.dynamic_tension_map_edge)
    del(bpy.types.Scene.dynamic_tension_map_show_from_flat)
    del(bpy.types.Object.dynamic_tension_flat_pattern_on)
    
    del(bpy.types.Scene.dynamic_tension_map_dict)
    del(bpy.types.Scene.dynamic_tension_map_selection)

    
# Create Classes-------------------------------:
class UpdatePattern(bpy.types.Operator):
    """Update Pattern"""
    bl_idname = "object.dynamic_tension_map_update_pattern"
    bl_label = "dynamic_tension_update_pattern"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        ob = bpy.context.object
        edit = True
        if ob.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        storage = bpy.context.scene.dynamic_tension_map_selection
        hide_unhide_store(ob, True, storage)
        bpy.ops.object.shape_from_uv()
        hide_unhide_store(ob, False, storage)
        if edit:
            bpy.ops.object.mode_set(mode='EDIT')            
        toggle_display(bpy.context.object, context)
        prop_callback(bpy.context.scene, bpy.context)
        return {'FINISHED'}


class DynamicTensionMap(bpy.types.Panel):
    """Dynamic Tension Map Panel"""
    bl_label = "Dynamic Tension Map"
    bl_idname = "dynamic tension map"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Extended Tools"
    gt_show = True
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Dynamic Tension Map")
        ob = bpy.context.object
        if ob is not None:
            if ob.dynamic_tension_map_on:    
                col.alert=True
            if ob.type == 'MESH':
                col.prop(ob ,"dynamic_tension_map_on", text="Toggle Dynamic Tension Map", icon='MOD_TRIANGULATE')
                col = layout.column()
                col.prop(bpy.context.scene ,"dynamic_tension_map_max_stretch", text="Max Stretch", slider=True)
                col = layout.column(align=True)
                col.prop(bpy.context.scene ,"dynamic_tension_map_show_from_flat", text="Show Tension From Flat", icon='MESH_GRID')
                if ob.data.shape_keys is not None:
                    if len(ob.data.shape_keys.key_blocks) > 1:
                        col.prop(ob ,"dynamic_tension_flat_pattern_on", text="Show Pattern", icon='OUTLINER_OB_LATTICE')
                        col = layout.column()
                        col.scale_y = 2.0
                        col.operator("object.dynamic_tension_map_update_pattern", text="Update Pattern")
                col = layout.column(align=True)

                #col.prop(bpy.context.scene ,"dynamic_tension_map_percentage", text="Percentage Based", icon='STICKY_UVS_VERT')
                #col.prop(bpy.context.scene ,"dynamic_tension_map_edge", text="Edge Difference", icon='UV_VERTEXSEL')        
                return
            
        col.label(text="Select Mesh Object")


# Register Clases -------------->>>
def register():
    create_properties()
    bpy.utils.register_class(DynamicTensionMap)
    bpy.utils.register_class(UpdatePattern)
    

def unregister():
    remove_properties()
    for i in bpy.app.handlers.scene_update_post:
        if i.__name__ == 'dynamic_tension_handler':
            bpy.app.handlers.scene_update_post.remove(i)
    bpy.utils.unregister_class(DynamicTensionMap)
    bpy.utils.unregister_class(UpdatePattern)

    
if __name__ == "__main__":
    register()
    
    
    for i in bpy.data.objects:
        i.dynamic_tension_map_on = False
    
    for i in bpy.app.handlers.scene_update_post:
        if i.__name__ == 'dynamic_tension_handler':
            bpy.app.handlers.scene_update_post.remove(i)    
