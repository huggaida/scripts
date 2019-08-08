import bpy
import os
import pathlib

from . pbaker_functions import *

NODE_TAG = 'p_baker_node'
MATERIAL_TAG = 'p_baker_material'

NODE_INPUTS = [
    'Color',
    'Subsurface',
    # 'Subsurface Radius', # TODO
    'Subsurface Color',
    'Metallic',
    'Specular',
    'Specular Tint',
    'Roughness',
    'Anisotropic',
    'Anisotropic Rotation',
    'Sheen',
    'Sheen Tint',
    'Clearcoat',
    'Clearcoat Roughness',
    'IOR',
    'Transmission',
    'Transmission Roughness',
    'Normal',
    'Clearcoat Normal',
    'Tangent'
]

NORMAL_INPUTS = ['Normal', 'Clearcoat Normal', 'Tangent']

SRGB_INPUTS = ['Color', 'Base Color']

ALPHA_NODES = {
    "Alpha":'BSDF_TRANSPARENT',
    "Translucent_Alpha":'BSDF_TRANSLUCENT',
    "Glass_Alpha":'BSDF_GLASS'
}

BSDF_NODES = [
    'BSDF_PRINCIPLED',
    'BSDF_DIFFUSE',
    'BSDF_TOON',
    'BSDF_VELVET',
    'BSDF_GLOSSY',
    'BSDF_TRANSPARENT',
    'BSDF_TRANSLUCENT',
    'BSDF_GLASS'
    ]

IMAGE_FILE_ENDINGS = {
    "BMP": "bmp",
    "PNG": "png",
    "JPEG": "jpg",
    "TIFF": "tif",
    "TARGA": "tga",
}

NODE_OFFSET_X = 300
NODE_OFFSET_Y = 200

IMAGE_NODE_OFFSET_X = -900
IMAGE_NODE_OFFSET_Y = -260
IMAGE_NODE_WIDTH = 300


class PBAKER_OT_bake(bpy.types.Operator):
    bl_idname = "object.principled_baker_bake"
    bl_label = "Bake"
    bl_description = "bake all inputs of a Principled BSDF to image textures" 
    bl_options = {'REGISTER', 'UNDO'} 

    settings = None

    def get_bake_type(self, job_name):
        if job_name == 'Emission':
            return 'EMIT'
        elif job_name in NORMAL_INPUTS:
            return 'NORMAL'
        else:
            return 'DIFFUSE'
            
    def get_joblist_manual(self):
        joblist = []

        if self.settings.use_Alpha:
            joblist.append("Alpha")
        if self.settings.use_Emission:
            joblist.append("Emission")

        if self.settings.use_Base_Color:
            joblist.append("Color")
        if self.settings.use_Metallic:
            joblist.append("Metallic")
        if self.settings.use_Roughness:
            joblist.append("Roughness")
        if self.settings.use_Normal:
            joblist.append("Normal")
        if self.settings.use_Bump:
            joblist.append("Bump")
        if self.settings.use_Displacement:
            joblist.append("Displacement")

        if self.settings.use_Specular:
            joblist.append("Specular")
        if self.settings.use_Anisotropic:
            joblist.append("Anisotropic")
        if self.settings.use_Anisotropic_Rotation:
            joblist.append("Anisotropic Rotation")
        if self.settings.use_Clearcoat:
            joblist.append("Clearcoat")
        if self.settings.use_Clearcoat_Normal:
            joblist.append("Clearcoat Normal")
        if self.settings.use_Clearcoat_Roughness:
            joblist.append("Clearcoat Roughness")
        if self.settings.use_IOR:
            joblist.append("IOR")
        if self.settings.use_Sheen:
            joblist.append("Sheen")
        if self.settings.use_Sheen_Tint:
            joblist.append("Sheen Tint")
        if self.settings.use_Specular_Tint:
            joblist.append("Specular Tint")
        if self.settings.use_Subsurface:
            joblist.append("Subsurface")
        if self.settings.use_Subsurface_Color:
            joblist.append("Subsurface Color")
        if self.settings.use_Subsurface_Radius:
            joblist.append("Subsurface Radius")
        if self.settings.use_Tangent:
            joblist.append("Tangent")
        if self.settings.use_Transmission:
            joblist.append("Transmission")
        return joblist

    def get_suffix(self, input_name):
        suffix = ""
        if input_name == 'Color':
            suffix = self.settings.suffix_color
        elif input_name == 'Metallic':
            suffix = self.settings.suffix_metallic
        elif input_name == 'Roughness':
            suffix = self.settings.suffix_roughness
        elif input_name == 'Normal':
            suffix = self.settings.suffix_normal
        elif input_name == 'Bump':
            suffix = self.settings.suffix_bump
        elif input_name == 'Displacement':
            suffix = self.settings.suffix_displacement
        else:
            suffix = '_' + input_name

        if self.settings.suffix_text_mod == 'lower':
            suffix = suffix.lower()
        elif self.settings.suffix_text_mod == 'upper':
            suffix = suffix.upper()
        elif self.settings.suffix_text_mod == 'title':
            suffix = suffix.title()
        return suffix

    def new_material(self, name):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat[MATERIAL_TAG] = 1

        mat_output = mat.node_tree.nodes['Material Output']
        mat_output.location = (300.0, 300.0)

        principled_node = mat.node_tree.nodes['Principled BSDF']
        principled_node.location = (10.0, 300.0)
        
        # copy settings to new principled_node
        for k, v in self.new_principled_node_settings.items():
            if k == 'Color':
                k = 'Base Color'
            principled_node.inputs[k].default_value = v

        mat.node_tree.links.new(principled_node.outputs['BSDF'], mat_output.inputs['Surface'])
        return mat

    def add_images_to_material(self, new_mat, new_images):
        node_offset_index = 0

        principled_node = find_node_by_type(new_mat, 'BSDF_PRINCIPLED')
        material_output = find_node_by_type(new_mat, 'OUTPUT_MATERIAL')

        for name, image in new_images.items():
            image_node = self.new_image_node(new_mat)
            image_node.label = name

            image_node.color_space = 'COLOR' if name in SRGB_INPUTS else 'NONE'

            image_node.image = image

            # rearrange nodes
            image_node.width = IMAGE_NODE_WIDTH
            image_node.location.x = principled_node.location.x + IMAGE_NODE_OFFSET_X
            image_node.location.y = principled_node.location.y + IMAGE_NODE_OFFSET_Y * node_offset_index

            # link nodes
            if name in NORMAL_INPUTS:
                normal_node = new_mat.node_tree.nodes.new(type="ShaderNodeNormalMap")
                normal_node.location.x = IMAGE_NODE_OFFSET_X + 1.5*IMAGE_NODE_WIDTH
                normal_node.location.y = IMAGE_NODE_OFFSET_Y * node_offset_index
                new_mat.node_tree.links.new(image_node.outputs['Color'], normal_node.inputs['Color'])
                new_mat.node_tree.links.new(normal_node.outputs[name], principled_node.inputs[name])
            elif name == 'Bump':
                bump_node = new_mat.node_tree.nodes.new(type="ShaderNodeBump")
                bump_node.location.x = IMAGE_NODE_OFFSET_X + 1.5*IMAGE_NODE_WIDTH
                bump_node.location.y = IMAGE_NODE_OFFSET_Y * node_offset_index
                new_mat.node_tree.links.new(image_node.outputs['Color'], bump_node.inputs['Height'])
                new_mat.node_tree.links.new(bump_node.outputs['Normal'], principled_node.inputs['Normal'])
            elif name == "Displacement":
                disp_node = new_mat.node_tree.nodes.new(type='ShaderNodeDisplacement')
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            disp_node.inputs["Height"])
                new_mat.node_tree.links.new(disp_node.outputs["Displacement"],
                                            material_output.inputs["Displacement"])
                disp_node.location.x = NODE_OFFSET_X
            elif name in ALPHA_NODES.keys():
                if not self.settings.use_alpha_to_color:
                    if name == "Alpha":
                        alpha_node = new_mat.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
                    elif name == "Translucent_Alpha":
                        alpha_node = new_mat.node_tree.nodes.new(type='ShaderNodeBsdfTranslucent')
                    elif name == "Glass_Alpha":
                        alpha_node = new_mat.node_tree.nodes.new(type='ShaderNodeBsdfGlass')                    
                    # color
                    alpha_node.inputs['Color'].default_value = self.new_node_colors[name]
                    
                    mixshader_node = new_mat.node_tree.nodes.new(type='ShaderNodeMixShader')

                    # links
                    new_mat.node_tree.links.new(material_output.inputs[0].links[0].from_socket,
                                                mixshader_node.inputs[2])
                    new_mat.node_tree.links.new(material_output.inputs[0], mixshader_node.outputs['Shader'])
                    new_mat.node_tree.links.new(alpha_node.outputs['BSDF'],
                                                mixshader_node.inputs[1])
                    new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                mixshader_node.inputs['Fac'])

                    # node locations
                    sib = get_sibling_node(alpha_node)
                    alpha_node.location = (sib.location.x, sib.location.y + NODE_OFFSET_Y)
                    mid_offset_y = alpha_node.location.y
                    mixshader_node.location = (sib.location.x + NODE_OFFSET_X, mid_offset_y)
                    
            elif name == 'Emission':
                emission_node = new_mat.node_tree.nodes.new(type='ShaderNodeEmission')
                emission_node.inputs['Color'] = self.new_node_colors[name]

                addshader_node = new_mat.node_tree.nodes.new(type='ShaderNodeAddShader')                

                # links
                new_mat.node_tree.links.new(material_output.inputs[0].links[0].from_socket,
                                            addshader_node.inputs[1])
                new_mat.node_tree.links.new(emission_node.outputs['Emission'],
                                            addshader_node.inputs[0])
                new_mat.node_tree.links.new(addshader_node.outputs['Shader'], material_output.inputs[0])
                new_mat.node_tree.links.new(image_node.outputs['Color'], emission_node.inputs['Color'])

                # node locations
                sib = get_sibling_node(emission_node)
                emission_node.location = (sib.location.x, sib.location.y + NODE_OFFSET_Y)
                mid_offset_y = emission_node.location.y
                addshader_node.location = (sib.location.x + NODE_OFFSET_X, mid_offset_y)

            elif name == 'Color':
                name = 'Base Color'
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            principled_node.inputs[name])
                                            
                if self.settings.use_alpha_to_color and "Alpha" in new_images.keys():
                    alpha_node = new_mat.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
                    mixshader_node = new_mat.node_tree.nodes.new(type='ShaderNodeMixShader')

                    # links
                    new_mat.node_tree.links.new(material_output.inputs[0].links[0].from_socket,
                                                mixshader_node.inputs[2])
                    new_mat.node_tree.links.new(material_output.inputs[0], mixshader_node.outputs['Shader'])
                    new_mat.node_tree.links.new(alpha_node.outputs['BSDF'],
                                                mixshader_node.inputs[1])
                    new_mat.node_tree.links.new(image_node.outputs["Alpha"],
                                                mixshader_node.inputs['Fac'])

                    # node locations
                    sib = get_sibling_node(alpha_node)
                    alpha_node.location = (sib.location.x, sib.location.y + NODE_OFFSET_Y)
                    mid_offset_y = alpha_node.location.y
                    mixshader_node.location = (sib.location.x + NODE_OFFSET_X, mid_offset_y)
                    
            else:
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            principled_node.inputs[name])
            node_offset_index += 1

    def new_pb_diffuse_node(self, material, color=[0, 0, 0, 1]):
        # node = material.node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')
        node = material.node_tree.nodes.new(type='ShaderNodeEmission')
        node.inputs['Color'].default_value = color#[0, 0, 0, 1]
        node[NODE_TAG] = 1
        return node

    def new_pb_output_node(self, material):
        node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        node.is_active_output = True
        node[NODE_TAG] = 1
        return node

    def get_file_path(self, image_file_name):
        path = os.path.join(
            os.path.dirname(bpy.data.filepath),  # absolute file path of current blend file
            self.settings.file_path.lstrip("/"),  # relativ file path from user input
            image_file_name)
        return path

    def new_image(self, image_file_name, alpha=False):
        if self.settings.resolution == "custom":
            res = self.settings.custom_resolution
        else:
            res = int(self.settings.resolution)
        image = bpy.data.images.new(name=image_file_name, width=res, height=res, alpha=alpha)

        image.use_alpha = alpha  # self.settings.use_alpha
        image.alpha_mode = 'STRAIGHT'

        if alpha:
            fill_image(image, (0.0, 0.0, 0.0, 0.0))

        image.filepath_raw = self.get_file_path(image_file_name)
        image.file_format = self.settings.file_format
        image.save()
        return image

    def new_bake_image(self, object_name, job_name):
        # image file data
        prefix = self.settings.image_prefix
        if prefix == "" or len(self.selected_objects) > 1 or self.settings.use_object_name:
            prefix = self.settings.image_prefix + object_name
        image_file_format = IMAGE_FILE_ENDINGS[self.settings.file_format]
        image_file_name = "{0}{1}.{2}".format(prefix, self.get_suffix(job_name), image_file_format)  # include ending
        image_file_path = self.get_file_path(image_file_name)
        image_is_file = os.path.isfile(image_file_path)

        colorspace = 'sRGB' if job_name == 'Color' else 'Non-Color'
        
        if job_name == 'Color' and self.settings.use_alpha_to_color:
            alpha_channel = 0.0
        elif self.settings.use_alpha:
            alpha_channel = 0.0
        else:
            alpha_channel = 1.0

        image_alpha = True if alpha_channel == 0.0 else False
        color = (0.5, 0.5, 1.0, alpha_channel) if self.get_bake_type(job_name) == 'NORMAL' else (0.0, 0.0, 0.0, alpha_channel)

        if self.settings.use_overwrite:
            if image_file_name in bpy.data.images.keys():
                if image_is_file:
                    image = bpy.data.images[image_file_name]

                    image.use_alpha = self.settings.use_alpha

                    # rescale
                    if self.settings.resolution == "custom":
                        res = self.settings.custom_resolution
                    else:
                        res = int(self.settings.resolution)
                    if not image.size[0] == res:
                        image.scale(res, res)
                else:
                    # new image
                    image = self.new_image(image_file_name, image_alpha)
                    image.colorspace_settings.name = colorspace

                fill_image(image, color)
            else:
                # new image
                image = self.new_image(image_file_name, image_alpha)
                image.colorspace_settings.name = colorspace
                fill_image(image, color)
        else:
            if not image_is_file:
                # new image
                image = self.new_image(image_file_name, image_alpha)
                image.colorspace_settings.name = colorspace
            else:
                image = bpy.data.images.load(image_file_path, check_existing=False)
        
        return image

    def new_image_node(self, material):
        image_node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
        return image_node

    def prepare_for_bake_factor(self, mat, socket, new_socket, node_type):
        node = socket.node
        if node.type == node_type:
            to_node = node.outputs[0].links[0].to_node
            if 'Fac' in to_node.inputs.keys():
                socket = to_node.inputs['Fac']
                self.prepare_for_bake(mat, socket, new_socket, 'Fac')
        else:
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    self.prepare_for_bake_factor(mat, from_socket, new_socket, node_type)

    def prepare_for_bake(self, mat, socket, new_socket, input_socket_name):
        if input_socket_name in NORMAL_INPUTS:
            color = (0.5, 0.5, 1.0, 1.0)
        else:
            color = (0.0, 0.0, 0.0, 0.0)
        
        node = socket.node

        if node.type == 'OUTPUT_MATERIAL':
            from_socket = socket.links[0].from_socket
            self.prepare_for_bake(mat, from_socket, new_socket, input_socket_name)

        elif node.type == 'MIX_SHADER':
            color2 = [1,1,1,0] if input_socket_name == 'Fac' else color
            mix_node = new_mixrgb_node(mat, color, color2)
            mix_node.inputs['Fac'].default_value = node.inputs['Fac'].default_value
            mat.node_tree.links.new(mix_node.outputs[0], new_socket)
            mix_node.label = input_socket_name

            if node.inputs['Fac'].is_linked:
                from_socket = node.inputs[0].links[0].from_socket
                new_socket = mix_node.inputs[0]
                mat.node_tree.links.new(from_socket, new_socket)

            for i in range(1, 3):
                if node.inputs[i].is_linked:
                    next_node = node.inputs[i].links[0].from_node                    
                    if next_node.type in ALPHA_NODES.values() and self.settings.use_exclude_transparent_colors:
                        other_i = i % 2 + 1
                        if node.inputs[other_i].is_linked:
                            from_socket = node.inputs[other_i].links[0].from_socket
                            new_socket = mix_node.inputs[i]
                    else:
                        from_socket = node.inputs[i].links[0].from_socket
                        new_socket = mix_node.inputs[i]
                    self.prepare_for_bake(mat, from_socket, new_socket, input_socket_name)

        elif node.type == 'ADD_SHADER' and not input_socket_name == 'Fac':
            mix_node = new_mixrgb_node(mat, color, color)
            mix_node.blend_type = 'ADD'
            mix_node.inputs['Fac'].default_value = 1
            mat.node_tree.links.new(mix_node.outputs[0], new_socket)
            mix_node.label = input_socket_name

            for i in range(0, 2):
                if node.inputs[i].is_linked:
                    from_socket = node.inputs[i].links[0].from_socket
                    new_socket = mix_node.inputs[i + 1]
                    self.prepare_for_bake(mat, from_socket, new_socket, input_socket_name)

        # exclude some colors from color
        elif node.type in ['EMISSION']:
            return

        # elif node.type in ALPHA_NODES.values():
        #     if self.use_exclude_transparent_colors:
        #         return

        else:
            if node.type == 'BSDF_PRINCIPLED' and input_socket_name == 'Color':
                input_socket_name = 'Base Color'

            if input_socket_name in node.inputs.keys():                
                input_socket = node.inputs[input_socket_name]
                
                if input_socket.type == 'RGBA':
                    if input_socket.is_linked:
                        from_socket = input_socket.links[0].from_socket
                        mat.node_tree.links.new(from_socket, new_socket)
                    else:
                        color = node.inputs[input_socket_name].default_value
                        rgb_node = new_rgb_node(mat, color)
                        mat.node_tree.links.new(rgb_node.outputs[0], new_socket)

                elif input_socket.type == 'VALUE':
                    if input_socket.is_linked:
                        from_socket = input_socket.links[0].from_socket
                        mat.node_tree.links.new(from_socket, new_socket)
                    else:
                        value_node = mat.node_tree.nodes.new(type="ShaderNodeValue")
                        value_node[NODE_TAG] = 1
                        value_node.outputs[0].default_value = node.inputs[input_socket_name].default_value
                        mat.node_tree.links.new(value_node.outputs[0], new_socket)

                elif input_socket.type == 'VECTOR':                   
                    if input_socket.name == input_socket_name:
                        if input_socket.is_linked:
                            from_socket = input_socket.links[0].from_socket
                            mat.node_tree.links.new(from_socket, new_socket)

            else:
                for input_socket in node.inputs:
                    if input_socket.is_linked:
                        from_socket = input_socket.links[0].from_socket
                        self.prepare_for_bake(mat, from_socket, new_socket, input_socket_name)

    def is_socket_linked_in_node_tree(self, node, input_socket_name):
        if input_socket_name == 'Color':
            if node.type == 'NORMAL_MAP':
                return False # exclude 'Color' from Normal Map input!
            if node.type == 'BSDF_PRINCIPLED':
                input_socket_name = 'Base Color'
        for input_socket in node.inputs:
            if input_socket.is_linked:
                if input_socket_name == input_socket.name:                
                    return True
                else:
                    from_node = input_socket.links[0].from_node
                    if self.is_socket_linked_in_node_tree(from_node, input_socket_name):
                        return True
        return False

    def get_value_list(self, node, value_name):
        value_list = []
        def find_values(node, value_name):
            if not node.type == 'NORMAL_MAP':
                if value_name == 'Color' and node.type == 'BSDF_PRINCIPLED':
                    tmp_value_name = 'Base Color'
                else:
                    tmp_value_name = value_name
                if tmp_value_name in node.inputs.keys():
                    if node.inputs[tmp_value_name].type == 'RGBA':
                        [r, g, b, a] = node.inputs[tmp_value_name].default_value
                        value_list.append([r, g, b, a])
                    else:
                        value_list.append(node.inputs[value_name].default_value)

                for socket in node.inputs:
                    if socket.is_linked:
                        from_node = socket.links[0].from_node
                        find_values(from_node, value_name)
        find_values(node, value_name)
        return value_list
        
    def get_value_list_from_node_types(self, node, value_name, node_types):
        value_list = []
        def find_values(node, value_name, node_types):
            if value_name == 'Color' and node.type == 'BSDF_PRINCIPLED':
                tmp_value_name = 'Base Color'
            else:
                tmp_value_name = value_name
            if node.type in node_types and tmp_value_name in node.inputs.keys():
                if node.inputs[tmp_value_name].type == 'RGBA':
                    [r, g, b, a] = node.inputs[tmp_value_name].default_value
                    value_list.append([r, g, b, a])
                else:
                    value_list.append(node.inputs[value_name].default_value)

            for socket in node.inputs:
                if socket.is_linked:
                    from_node = socket.links[0].from_node
                    find_values(from_node, value_name, node_types)        
        find_values(node, value_name, node_types)
        return value_list

    def get_joblist_from_object(self, obj):
        joblist = []

        # add to joblist if values differ
        for value_name in NODE_INPUTS:
            if value_name not in joblist:
                if value_name not in ['Subsurface Radius', 'Normal', 'Clearcoat Normal', 'Tangent']:
                    value_list = []
                    for mat_slot in obj.material_slots:
                        mat = mat_slot.material
                        if not MATERIAL_TAG in mat.keys():
                            # material_output = find_node_by_type(mat, 'OUTPUT_MATERIAL')
                            material_output = find_active_output(mat)
                            value_list.extend(self.get_value_list(material_output, value_name))
                    if len(value_list) >= 1:
                        if is_list_equal(value_list):
                            if self.settings.use_new_material or self.render_settings.use_selected_to_active:
                                self.new_principled_node_settings[value_name] = value_list[0]
                        else:
                            joblist.append(value_name)
                    
        # search material for jobs
        for mat_slot in obj.material_slots:
            if not MATERIAL_TAG in mat_slot.material.keys():
                # material_output = find_node_by_type(mat_slot.material, 'OUTPUT_MATERIAL')
                material_output = find_active_output(mat_slot.material)
                # add special cases:
                # Alpha for nodes: Transparent, Translucent, Glass
                for alpha_name, n_type in ALPHA_NODES.items():
                    if is_node_type_in_node_tree(material_output, n_type):
                        if not alpha_name in joblist:
                            joblist.append(alpha_name)
                # Emission
                if is_node_type_in_node_tree(material_output, 'EMISSION'):
                    if not 'Emission' in joblist:
                        joblist.append('Emission')                    
                # Displacement                    
                socket_name = 'Displacement'
                if is_node_type_in_node_tree(material_output, 'DISPLACEMENT'):
                    if self.is_socket_linked_in_node_tree(material_output, socket_name):
                        if not socket_name in joblist:
                            joblist.append(socket_name)                                    
                # Bump
                socket_name = 'Bump'
                if self.settings.use_bake_bump and is_node_type_in_node_tree(material_output, 'BUMP'):
                        if not socket_name in joblist:
                            joblist.append(socket_name)  
  
                # add linked inputs to joblist
                if are_node_types_in_node_tree(material_output, BSDF_NODES):
                    for socket_name in NODE_INPUTS:
                        if self.is_socket_linked_in_node_tree(material_output, socket_name):
                            if not socket_name in joblist:
                                joblist.append(socket_name)
                
                # TODO remove 'color' from joblist, if added from Normal Map Color input

        # force bake of Color, if user wants alpha in color
        if self.settings.use_alpha_to_color:
            if not 'Color' in joblist:
                joblist.append('Color')

        return joblist


    def execute(self, context):
        self.settings = context.scene.principled_baker_settings
        self.render_settings = context.scene.render.bake
        self.active_object = context.active_object
        self.selected_objects = bpy.context.selected_objects

        self.new_principled_node_settings = {}
        self.new_node_colors = {
            "Alpha":[1.0, 1.0, 1.0, 1.0],
            "Translucent_Alpha":[0.8, 0.8, 0.8, 1.0],
            "Glass_Alpha":[1.0, 1.0, 1.0, 1.0],
            'Emission':[1.0, 1.0, 1.0, 1.0],
            }

        new_images = {}

        # bake only works in cycles (for now)
        if not bpy.context.scene.render.engine == 'CYCLES':
            self.report({'ERROR'}, 'Error: Current render engine ({0}) does not support baking'.format(bpy.context.scene.render.engine))
            return {'CANCELLED'}

        # input error handling
        if not self.active_object.type == 'MESH':
            self.report({'ERROR'}, '{0} is not a mesh object'.format(self.active_object.name))
            return {'CANCELLED'}
        if self.render_settings.use_selected_to_active:
            if len(self.selected_objects) < 2:
                self.report({'ERROR'}, 'Select at least 2 objects!')
                return {'CANCELLED'}
        
        # object not mesh or has no material
        orig_selected_objects = []
        for obj in self.selected_objects:
            if not obj.type == 'MESH' or len(obj.material_slots) == 0:
                orig_selected_objects.append(obj)
                self.selected_objects.remove(obj)
                obj.select_set(False)
        
        # error handling: cancel if Material Output is missing or missing inputs in Material Output
        for obj in self.selected_objects:
            for mat_slot in obj.material_slots:
                if not MATERIAL_TAG in mat_slot.material.keys():
                    # material_output = find_node_by_type(mat_slot.material, 'OUTPUT_MATERIAL')
                    material_output = find_active_output(mat_slot.material)
                    if material_output == None:
                        self.report({'ERROR'}, 'Material Output missing in "{0}"'.format(mat_slot.material.name))
                        return {'CANCELLED'}
                    else:
                        if not material_output.inputs['Surface'].is_linked:
                            self.report({'WARNING'}, 'Surface Input missing in Material Output in "{0}"'.format(mat_slot.material.name))
                            return {'CANCELLED'}                    

        joblist = []
        if not self.settings.use_autodetect:
            joblist = self.get_joblist_manual()

        ########
        # bake single or batch:
        ########
        if not self.render_settings.use_selected_to_active:
            for obj in self.selected_objects:
                new_images.clear()
                
                # find active material outpus for later clean up
                active_outputs = []
                for mat_slot in obj.material_slots:
                    if not MATERIAL_TAG in mat_slot.material.keys():
                        # material_output = find_node_by_type(mat_slot.material, 'OUTPUT_MATERIAL')
                        active_outputs.append( find_active_output(mat_slot.material) )

                # populate joblist auto                
                if self.settings.use_autodetect:
                    joblist = self.get_joblist_from_object(obj)

                # create new material
                if self.settings.use_new_material:
                    # new_mat_name = self.active_object.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
                    new_mat_name = obj.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
                    new_mat = self.new_material(new_mat_name)
                    obj.data.materials.append(new_mat)

                # go through joblist
                for job_name in joblist:
    
                    # bake_type
                    bake_type = self.get_bake_type(job_name)

                    # image to bake on
                    image = self.new_bake_image(obj.name, job_name)
                    
                    # append to image dict for new material
                    new_images[job_name] = image

                    # guess colors for Transparent, Translucent, Glass, Emission
                    if self.settings.use_new_material:
                        if job_name in self.new_node_colors.keys():
                            for mat_slot in obj.material_slots:
                                mat = mat_slot.material
                                if not MATERIAL_TAG in mat.keys():
                                    # mat_out = find_node_by_type(mat, 'OUTPUT_MATERIAL')
                                    mat_out = find_active_output(mat_slot.material)
                                    node_types = ALPHA_NODES[job_name]
                                    color_list = self.get_value_list_from_node_types(mat_out, 'Color', node_types)
                                    if len(color_list) >= 1:
                                        self.new_node_colors[job_name] = color_list[0]

                    if not self.settings.use_overwrite and os.path.isfile(image.file_path):
                        # do not bake!
                        self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(image.name))
                    else:  # do bake

                        # prepare materials before baking
                        for mat_slot in obj.material_slots:
                            mat = mat_slot.material
                            if not MATERIAL_TAG in mat.keys():
                                # material_output = find_node_by_type(mat, 'OUTPUT_MATERIAL')
                                material_output = find_active_output(mat_slot.material)
                                socket_to_surface = material_output.inputs['Surface'].links[0].from_socket
                                
                                if bake_type == 'DIFFUSE':
                                    # new temp Material Output node
                                    pb_output_node = self.new_pb_output_node(mat)
                                    pb_output_node[NODE_TAG] = 1
                                    pb_output_node.is_active_output = True

                                    material_output.is_active_output = False

                                    # temp Diffuse node
                                    pb_diffuse_node_color = [1, 1, 1, 1]
                                    pb_diffuse_node = self.new_pb_diffuse_node(mat, pb_diffuse_node_color)

                                    socket_to_pb_diffuse_node_color = pb_diffuse_node.inputs['Color']
                                    
                                    if job_name in ALPHA_NODES.keys():
                                        node_type = ALPHA_NODES[job_name]
                                        self.prepare_for_bake_factor(mat, socket_to_surface, socket_to_pb_diffuse_node_color, node_type)

                                    elif job_name == 'Displacement':
                                        if material_output.inputs['Displacement'].is_linked:
                                            socket_to_displacement = material_output.inputs['Displacement'].links[0].from_socket
                                            self.prepare_for_bake(mat, socket_to_displacement, socket_to_pb_diffuse_node_color, 'Height')
                                    
                                    elif job_name == 'Bump':
                                        self.prepare_for_bake(mat, socket_to_surface, socket_to_pb_diffuse_node_color, 'Height')

                                    else:
                                        self.prepare_for_bake(mat, socket_to_surface, socket_to_pb_diffuse_node_color, job_name)

                                    # link pb_diffuse_node to material_output
                                    mat.node_tree.links.new(pb_diffuse_node.outputs[0], pb_output_node.inputs['Surface'])

                                    # material_output.is_active_output = True
                        
                                # create temp image node to bake on
                                bake_image_node = self.new_image_node(mat)
                                # bake_image_node.color_space = 'COLOR' if image.colorspace_settings.name == 'sRGB' else 'NONE'
                                bake_image_node.color_space = 'COLOR' if job_name == 'Color' else 'NONE'
                                bake_image_node.image = image  # add image to node
                                bake_image_node[NODE_TAG] = 1  # tag for clean up
                                # make only bake_image_node active
                                bake_image_node.select = True
                                mat.node_tree.nodes.active = bake_image_node

                        # bake!
                        self.report({'INFO'}, "baking... '{0}'".format(image.name))
                        # pass_filter = set(['COLOR']) if bake_type == 'DIFFUSE' else set()                        
                        if not bake_type == "NORMAL":
                            bake_type = "EMIT"
                        bpy.ops.object.bake(
                            type=bake_type,
                            margin=self.settings.margin,
                            use_clear=False,
                            use_selected_to_active=False)
                            # pass_filter=pass_filter)

                        # save image!
                        image.save()

                        # clean up: delete all nodes with tag = NODE_TAG
                        for mat_slot in obj.material_slots:
                            for node in mat_slot.material.node_tree.nodes:
                                if NODE_TAG in node.keys():
                                    mat_slot.material.node_tree.nodes.remove(node)
                        if self.settings.use_new_material:
                            for node in new_mat.node_tree.nodes:
                                if NODE_TAG in node.keys():
                                    new_mat.node_tree.nodes.remove(node)

                        # clean up: reactivate Material Outputs
                        for mat_slot in obj.material_slots:
                            for node in mat_slot.material.node_tree.nodes:
                                if node.type == "OUTPUT_MATERIAL":
                                    node.is_active_output = False
                        for mat_output in active_outputs:
                            mat_output.is_active_output = True
                        
                # add alpha channel to color
                if self.settings.use_alpha_to_color:
                    if 'Color' in new_images and "Alpha" in new_images:
                        combine_images(new_images['Color'], new_images["Alpha"], 0, 3)

                # add new images to new material
                if self.settings.use_new_material:
                    self.add_images_to_material(new_mat, new_images)
            # clean up: reselect original selected objects
            for obj in orig_selected_objects:
                obj.select_set(True)

        ########
        # bake selected to active:
        ########
        elif self.render_settings.use_selected_to_active:
            new_images.clear()
            
            if self.active_object in self.selected_objects:
                self.selected_objects.remove(self.active_object)

            # find active material outpus for later clean up
            for obj in self.selected_objects:
                active_outputs = []
                for mat_slot in obj.material_slots:
                    if not MATERIAL_TAG in mat_slot.material.keys():
                        # material_output = find_node_by_type(mat_slot.material, 'OUTPUT_MATERIAL')
                        active_outputs.append( find_active_output(mat_slot.material) )
                        
            # populate joblist auto
            for obj in self.selected_objects:
                if self.settings.use_autodetect:
                    job_extend = self.get_joblist_from_object(obj)
                    for j in job_extend:
                        if j not in joblist:
                            joblist.append(j)
            
            # create new material
            new_mat_name = self.active_object.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
            new_mat = self.new_material(new_mat_name)
            self.active_object.data.materials.append(new_mat)

            # go through joblist
            for job_name in joblist:

                # bake_type
                bake_type = self.get_bake_type(job_name)                

                # image to bake on
                image = self.new_bake_image(obj.name, job_name)
                
                # append to image dict for new material
                new_images[job_name] = image

                # guess color for Transparent, Translucent, Glass, Emission
                if job_name in self.new_node_colors.keys():
                    for obj in self.selected_objects:
                        for mat_slot in obj.material_slots:
                            mat = mat_slot.material
                            if not MATERIAL_TAG in mat.keys():
                                # mat_out = find_node_by_type(mat, 'OUTPUT_MATERIAL')
                                mat_out = find_active_output(mat)
                                node_types = ALPHA_NODES[job_name]
                                color_list = self.get_value_list_from_node_types(mat_out, 'Color', node_types)
                                if len(color_list) >= 1:
                                    self.new_node_colors[job_name] = color_list[0]

                if not self.settings.use_overwrite and os.path.isfile(image.file_path):
                    # do not bake!
                    self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(image.name))
                else:  # do bake
                    # prepare materials before baking
                    for obj in self.selected_objects:
                        for mat_slot in obj.material_slots:
                            mat = mat_slot.material
                            # material_output = find_node_by_type(mat, 'OUTPUT_MATERIAL')
                            material_output = find_active_output(mat)
                            socket_to_surface = material_output.inputs['Surface'].links[0].from_socket
                            
                            if bake_type == 'DIFFUSE':
                                # new temp Material Output node
                                pb_output_node = self.new_pb_output_node(mat)
                                pb_output_node[NODE_TAG] = 1
                                pb_output_node.is_active_output = True

                                material_output.is_active_output = False

                                # temp Diffuse node
                                pb_diffuse_node_color = [1, 1, 1, 1]
                                pb_diffuse_node = self.new_pb_diffuse_node(mat, pb_diffuse_node_color)

                                socket_to_pb_diffuse_node_color = pb_diffuse_node.inputs['Color']

                                if job_name in ALPHA_NODES.keys():
                                    node_type = ALPHA_NODES[job_name]
                                    self.prepare_for_bake_factor(mat, socket_to_surface, socket_to_pb_diffuse_node_color, node_type)

                                elif job_name == 'Displacement':
                                    if material_output.inputs['Displacement'].is_linked:
                                        socket_to_displacement = material_output.inputs['Displacement'].links[0].from_socket
                                        self.prepare_for_bake(mat, socket_to_displacement, socket_to_pb_diffuse_node_color, 'Height')
                                
                                elif job_name == 'Bump':
                                    self.prepare_for_bake(mat, socket_to_surface, socket_to_pb_diffuse_node_color, 'Height')

                                else:
                                    self.prepare_for_bake(mat, socket_to_surface, socket_to_pb_diffuse_node_color, job_name)

                                # link pb_diffuse_node to material_output
                                mat.node_tree.links.new(pb_diffuse_node.outputs[0], pb_output_node.inputs['Surface'])
                                                    
                    # create temp image node to bake on
                    for mat_slot in self.active_object.material_slots:
                        mat = mat_slot.material
                        bake_image_node = self.new_image_node(mat)
                        # bake_image_node.color_space = 'COLOR' if image.colorspace_settings.name == 'sRGB' else 'NONE'
                        bake_image_node.color_space = 'COLOR' if job_name == 'Color' else 'NONE'
                        bake_image_node.image = image  # add image to node
                        bake_image_node[NODE_TAG] = 1  # tag for clean up
                        # make only bake_image_node active
                        bake_image_node.select = True
                        mat.node_tree.nodes.active = bake_image_node

                    # bake!
                    self.report({'INFO'}, "baking... '{0}'".format(image.name))
                    # pass_filter = set(['COLOR']) if bake_type == 'DIFFUSE' else set()
                    if not bake_type == "NORMAL":
                        bake_type = "EMIT"
                    bpy.ops.object.bake(
                        type=bake_type,
                        margin=self.settings.margin,
                        use_clear=False,
                        use_selected_to_active=True)
                        # pass_filter=pass_filter)

                    # save image!
                    image.save()

                    # add alpha channel to color
                    if self.settings.use_alpha_to_color:
                        if 'Color' in new_images and "Alpha" in new_images:
                            combine_images(new_images['Color'], new_images["Alpha"], 0, 3)

                    # clean up!
                    # delete all nodes with tag = NODE_TAG
                    for obj in self.selected_objects:
                        for mat_slot in obj.material_slots:
                            for node in mat_slot.material.node_tree.nodes:
                                if NODE_TAG in node.keys():
                                    mat_slot.material.node_tree.nodes.remove(node)
                    for mat_slot in self.active_object.material_slots:
                        for node in mat_slot.material.node_tree.nodes:
                            if NODE_TAG in node.keys():
                                mat_slot.material.node_tree.nodes.remove(node)
                        if MATERIAL_TAG in mat_slot.material.keys():
                            del new_mat[MATERIAL_TAG]
                    
                    # reactivate Material Outputs
                    for mat_output in active_outputs:
                        mat_output.is_active_output = True

            # add new images to new material
            self.add_images_to_material(new_mat, new_images)
            
        return {'FINISHED'}
