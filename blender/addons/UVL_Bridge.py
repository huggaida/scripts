bl_info = {
    "name": "UV Layout bridge",
    "author": "Titus Lavrov",
    "version": (0, 0, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Toolbar and View3D",
    "warning": "",
    "description": "Bridge for UVs transfer between blender and headus uvlayout v2 application",
    "wiki_url": "https://blenderartists.org/t/blender-uvlayout-bridge/699580"
                "",
    "category": "UV",
}

import bpy
import collections
import os
import os.path
import subprocess
import tempfile 
import time 
from sys import platform
from bpy_extras import view3d_utils
from bpy.types import (
        Operator,
        Menu,
        Panel,
        PropertyGroup,
        AddonPreferences,
        )
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty,
        )
#Functions
def UVLBridge_IO(): 
    
    #---Variables---    
    #---Headus uvlayout path 
    UVLayoutPath = bpy.context.preferences.addons[__name__].preferences.filepath
    #Test
    #UVLayoutPath = "c:\\Program Files (x86)\\headus UVLayout v2 Professional\\"  
    
    path = "" + tempfile.gettempdir()
    path = '/'.join(path.split('\\'))
    
    file_Name = path + "/Blender2UVLayout_TMP.obj"
    file_outName =path + "/Blender2UVLayout_TMP.out"
    file_cmdName =path + "/Blender2UVLayout_TMP.cmd"
    uvl_exit_str = "exit"     
       
    print("file_Name" + file_Name)   
    print("file_outName" + file_outName)   
    print("file_cmdName" + file_cmdName)   
    expObjs = []
    expMeshes = []
    uvlObjs = []
    Objs = []
    props = bpy.data.window_managers["WinMan"].uvlBridgeProps
    
    #--Get selected objects---
    #---Lists buildUP--- 
    if len(bpy.context.selected_objects) != 0:     
        for ob in bpy.context.selected_objects:
            if ob.type == 'MESH':
                #---Check for UV channels---
                if len(ob.data.uv_layers) < props.uvlb_channel:                
                    for n in range(props.uvlb_channel - len(ob.data.uv_layers)):
                        ob.data.uv_layers.new()               
                #---Setup uv index and collect Objs---
                ob.data.uv_layers.active_index = (props.uvlb_channel - 1)
                Objs.append(ob)
    if len(Objs) != 0:   
        #---Create and prepare objects for export---
        for ob in Objs:       
            newObj = ob.copy()
            newObj.data = ob.data.copy()
            newObj.animation_data_clear()
            newObj.name = ob.name + "__UVL"
            #bpy.context.scene.objects.link(newObj)    
            bpy.context.scene.collection.objects.link(newObj)
            expObjs.append(newObj)              
            expMeshes.append(newObj.data)
        #---Texture channels cleanup exept uvlb_uv_channel 
        for ob in expMeshes:                       
            active_index = (props.uvlb_channel - 1)
            texName=ob.uv_layers[active_index].name 
            uv_layers = ob.uv_layers
            ObjTexs=[]
            for t in uv_layers:
                ObjTexs.append(t.name)    
            for u in ObjTexs:
                if u != texName:                                                    
                    uv_layers.remove(uv_layers[u])
                
        #---Select objects for EXPORT
        bpy.ops.object.select_all(action='DESELECT')     
        for ob in expObjs:
            bpy.data.objects[ob.name].select_set(True) 
              
        #---EXPORT---    
        bpy.ops.export_scene.obj(filepath = file_Name, 
                                    check_existing = True,
                                    axis_forward = '-Z',
                                    axis_up = 'Y',
                                    filter_glob = "*.obj;*.mtl",
                                    use_selection = True,
                                    use_animation = False, 
                                    use_mesh_modifiers = False, 
                                    use_mesh_modifiers_render = False, 
                                    use_edges = False, 
                                    use_smooth_groups = False, 
                                    use_smooth_groups_bitflags = False, 
                                    use_normals = True, 
                                    use_uvs = True, 
                                    use_materials = False, 
                                    use_triangles = False, 
                                    use_nurbs = False, 
                                    use_vertex_groups = True, 
                                    use_blen_objects = False, 
                                    group_by_object = True, 
                                    group_by_material = False, 
                                    keep_vertex_order = True, 
                                    global_scale = 1, 
                                    path_mode = 'AUTO')   
        
        #---OBJs Clean up and deselect before import
        for ob in expMeshes:        
            bpy.data.meshes.remove(ob, do_unlink=True)
        
        bpy.ops.object.select_all(action='DESELECT')
                          
        #-Set UVs mode        
        if (props.uvlb_mode == '0'):
            uvlb_uv_mode = 'New'
            uvlb_mode = 'Poly'
             
        if (props.uvlb_mode == '1'):
            uvlb_uv_mode = 'Edit'
            uvlb_mode = 'Poly'
            
               
        #---OS---
        #---Do not have OSx to try so comment lines under.---
        #if platform == "darwin":
        #   l = os.listdir(UVLayoutPath)
        #    appName = (str(l).strip("[]")).strip("'")
        #    uvlayout_proc = subprocess.Popen(args=[UVLayoutPath + appName, '-plugin,' + uvlb_mode + ',' + uvlb_uv_mode, path + file_Name])
        if platform == "win32":
            uvlayout_proc = subprocess.Popen(args=[UVLayoutPath + 'uvlayout.exe', '-plugin,' + uvlb_mode + ',' + uvlb_uv_mode, file_Name])
        
        #---IMPORT---
        while not os.path.isfile(file_outName) and uvlayout_proc.poll() != 0:         
            time.sleep(0.5)
            #---Import OBJ---
            if os.path.isfile(file_outName) == True:            
                bpy.ops.import_scene.obj(filepath = file_outName, 
                                        axis_forward = '-Z', 
                                        axis_up = 'Y', 
                                        filter_glob = "*.obj;*.mtl", 
                                        use_edges = False, 
                                        use_smooth_groups = False, 
                                        use_split_objects = True, 
                                        use_split_groups = True, 
                                        use_groups_as_vgroups = True, 
                                        use_image_search = False, 
                                        split_mode = 'ON', 
                                        #global_clamp_size = 0,
                                        );
                                        
                #---Close UVLAYOUT ---
                f = open(file_cmdName, "w+")
                f.write(''.join([uvl_exit_str]))
                f.close()
                
                #---Transfer UVs and CleanUP---
                for ob in bpy.context.selected_objects:
                    uvlObjs.append(ob)
                
                bpy.ops.object.select_all(action='DESELECT') 
                    
                for ob in uvlObjs:
                    #---Get source object name
                    refName=ob.name.split('__UVL')
                    
                    srcObj = bpy.data.objects[refName[0]]
                    uvlObj = bpy.data.objects[ob.name] 
                    active_index = (props.uvlb_channel - 1)                                   
                    #---Select source object---                
                    srcObj.select_set(True)
                    #---Select UVL object
                    bpy.context.view_layer.objects.active = uvlObj
                    #---Transfer UVs from UVL object to Source object
                    uvlObj.data.uv_layers.active_index = 0                            
                    srcObj.data.uv_layers.active_index = active_index                    
                    bpy.ops.object.join_uvs()                
                    bpy.ops.object.select_all(action='DESELECT')
                        
                bpy.ops.object.select_all(action='DESELECT')    
            
                for ob in Objs:
                    bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]
                    bpy.data.objects[ob.name].select_set(True)
                         
                for ob in uvlObjs:         
                    bpy.data.meshes.remove(ob.data, do_unlink=True) 
                  

class uvlBridge(Operator):
    bl_idname = "uvlbridge.props"
    bl_label = "Send to UVLayout"
    bl_description = "Connects Blender with UVLayout"
    bl_options = {'REGISTER', 'UNDO'}    
        
    uvlb_channel: IntProperty(
        name="UV channel",
        description="Select UV channel",
        default=1,
        min=1,
        max=8
        )
    uvlb_mode: EnumProperty(
        name="Mode",
        items=(('0', "New", "Create new uv channel"),
                ('1', "Edit", "Edit existing uv channel")),
        description="Mode: New or Edit",
        default='0'
        )
    
    def execute(self, context):        
        if len(bpy.context.selected_objects) == 0:
            self.report ({'INFO'}, 'UVLayout bridge - Selection is empty! Please select some objects!!') 
            return {'FINISHED'}
        else:
            UVLBridge_IO()
            self.report ({'INFO'}, 'UVLayout bridge - UV Maps were transfered.Done!')
            return {'FINISHED'}
        
# panel containing all tools
class VIEW3D_PT_tools_uvlBridge(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UVLBridge'
    bl_context = "objectmode"
    bl_label = "UVLayout bridge"
    
    @classmethod
    def poll(cls, context):        
    # Check if there's an object and whether it's a mesh
        ob = context.active_object
        return ((ob is not None) and
                (ob.type == 'MESH') and
                (context.mode == 'OBJECT'))
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        
        col = layout.column(align=True)
        box = col.column(align=True).box().column()
        col_top = box.column(align=True)
        row = col_top.row(align=True)
        col_left = row.column(align=True)
        col_right = row.column(align=True)        
        col_left.prop(wm.uvlBridgeProps, "uvlb_mode", text="",icon='GROUP_UVS')
        col_right.prop(wm.uvlBridgeProps, "uvlb_channel")
        col.operator('uvlbridge.props',icon='UV') 
        
class uvlBridgeProps(PropertyGroup):
    """
    Fake module like class
    bpy.context.window_manager.uvbBridge
    """
    # general display properties
    uvlb_channel : IntProperty(
        name="UV Map",
        description="UV Map index(channel)",
        default=1,
        min=1,
        max=8
        )
    uvlb_mode : EnumProperty(
        name = "Mode",
        items=(('0', "New", "Create new uv map(channel)"),
                ('1', "Edit", "Edit existing uv map(channel)")),
        description="Mode: New or Edit",
        default='0'
        )

class uvlBridgePreferences(AddonPreferences):
    bl_idname = __name__

    filepath : StringProperty \
            (
            name = "Path:",
            subtype = 'DIR_PATH',
            )

    def draw(self, context):
        layout = self.layout        
        layout.label(text = "Set the path to the Headus UVLayout v2.(Only path to folder)")
        layout.prop(self, "filepath")

class OBJECT_OT_uvl_addon_prefs(Operator):    
    bl_idname = "uvlbridge.prefs"
    bl_label = "UVLayout Bridge addon preferences"
    bl_options = {'REGISTER', 'UNDO'}   
       
    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        info = ("Path: %s" % (addon_prefs.filepath))
        self.report({'INFO'}, info)
        return {'FINISHED'} 
 
#Classes for register and unregister
classes = (
    uvlBridge,
    uvlBridgeProps,   
    VIEW3D_PT_tools_uvlBridge,
    OBJECT_OT_uvl_addon_prefs,
    uvlBridgePreferences          
    )
    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.uvlBridgeProps = PointerProperty(type = uvlBridgeProps)

def unregister():
    del bpy.types.WindowManager.uvlBridgeProps

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()