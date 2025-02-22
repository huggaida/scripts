import bpy

class PBAKER_PT_panel(bpy.types.Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Principled Baker"
    bl_context = "objectmode"
    bl_category = "Principled Baker"

    @classmethod
    def poll(cls, context):
        if context.space_data.tree_type == 'ShaderNodeTree':
            return True
        return False

    def draw(self, context):
        settings = context.scene.principled_baker_settings
        render_settings = context.scene.render.bake

        self.layout.operator('object.principled_baker_bake', text='Bake', icon='RENDER_STILL')

        # box = self.layout.box()

        # bake/render options:
        col = self.layout.box().column(align=True)
        col.prop(render_settings, "margin")
        # col.prop(render_settings, "use_clear", text="Clear Image")
        col.separator()
        col.prop(render_settings, "use_selected_to_active")
        sub = col.column()
        sub.active = render_settings.use_selected_to_active
        sub.prop(render_settings, "use_cage", text="Cage")
        if render_settings.use_cage:
            sub.prop(render_settings, "cage_extrusion", text="Extrusion")
            sub.prop(render_settings, "cage_object", text="Cage Object")
        else:
            sub.prop(render_settings, "cage_extrusion", text="Ray Distance")

        # output options:        
        col = self.layout.box().column(align=True)
        row = col.row()
        row.prop(settings, "resolution", expand=True)
        if settings.resolution == "custom":
            col.prop(settings, "custom_resolution")



        col.separator()
        col.prop(settings, "file_path")
        col.prop(settings, "use_overwrite")
        col.prop(settings, "use_alpha")
        col.prop(settings, "use_alpha_to_color")
        col.prop(settings, "file_format", text="")
        col.separator()
        col.prop(settings, "image_prefix")
        col.prop(settings, "use_object_name")

        # image_suffix_settings_show
        col.prop(settings, "image_suffix_settings_show", toggle=True)
        if settings.image_suffix_settings_show:
            col.prop(settings, "suffix_color")
            col.prop(settings, "suffix_metallic")
            col.prop(settings, "suffix_roughness")
            # col.prop(settings, "suffix_specular")
            col.prop(settings, "suffix_normal")
            col.prop(settings, "suffix_bump")
            col.prop(settings, "suffix_displacement")        
            row = col.row()
            row.prop(settings, 'suffix_text_mod', expand=True)

        # new material:
        col = self.layout.box().column(align=True)
        col.prop(settings, "use_new_material")
        col.prop(settings, "new_material_prefix")
        
        # settings:
        col = self.layout.box().column(align=True)        
        col.prop(settings, "use_exclude_transparent_colors")
        # col.prop(settings, "use_invert_roughness")

        # autodetect
        col = self.layout.box().column(align=True)
        col.prop(settings, "use_autodetect", toggle=True)
        col.separator()
        if settings.use_autodetect:
            col.prop(settings, "use_bake_bump")
        else:
            col.prop(settings, "use_Base_Color", toggle=True)
            col.prop(settings, "use_Metallic", toggle=True)
            col.prop(settings, "use_Roughness", toggle=True)

            col.prop(settings, "use_Normal", toggle=True)
            col.prop(settings, "use_Bump", toggle=True)
            col.prop(settings, "use_Displacement", toggle=True)

            col.separator()
            col.prop(settings, "use_Alpha", toggle=True)
            col.prop(settings, "use_Emission", toggle=True)

            col.separator()
            col.prop(settings, "use_Subsurface", toggle=True)
            # TODO col.prop(settings, "use_Subsurface_Radius", toggle=True)
            col.prop(settings, "use_Subsurface_Color", toggle=True)
            col.prop(settings, "use_Specular", toggle=True)
            col.prop(settings, "use_Specular_Tint", toggle=True)
            col.prop(settings, "use_Anisotropic", toggle=True)
            col.prop(settings, "use_Anisotropic_Rotation", toggle=True)
            col.prop(settings, "use_Sheen", toggle=True)
            col.prop(settings, "use_Sheen_Tint", toggle=True)
            col.prop(settings, "use_Clearcoat", toggle=True)
            col.prop(settings, "use_Clearcoat_Roughness", toggle=True)
            col.prop(settings, "use_IOR", toggle=True)
            col.prop(settings, "use_Transmission", toggle=True)
            col.prop(settings, "use_Transmission_Roughness", toggle=True)
            col.prop(settings, "use_Clearcoat_Normal", toggle=True)
            col.prop(settings, "use_Tangent", toggle=True)
