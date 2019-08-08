# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>
import bpy
from bpy.app.handlers import persistent

bl_info = {
    'name': 'Text Typewriter',
    'author': 'Bassam Kurdali',
    'version': '1.0',
    'blender': (2, 80, 0),
    'location': 'Properties Editor, Text Context',
    'description': 'Text Animation Effects, formerly Typewriter Text',
    'url': 'http://urchn.org',
    'category': 'Text'}

__bpydoc__ = """
Typewriter Text Animation For Font Objects

"""


def uptext(text):
    '''
    slice the source text up to the character_count
    '''
    source = text.source_text
    if source in bpy.data.texts:
        text.body = bpy.data.texts[source].as_string()[:text.character_count]
    else:
        text.body = source[:text.character_count]


@persistent   
def typewriter_text_update_frame(scene):
    '''
    sadly we need this for frame change updating
    '''
    for text in scene.objects:
        if text.type == 'FONT' and text.data.use_animated_text:
            uptext(text.data)


def update_func(self, context):
    '''
    updates when changing the value
    '''
    uptext(self)


class TEXT_PT_Typewriter(bpy.types.Panel):
    '''
    Typewriter Effect Panel
    '''
    bl_label = "Typewriter Effect"
    bl_idname = "TEXT_PT_Typewriter"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'FONT'

    def draw_header(self, context):
        text = context.active_object.data
        layout = self.layout
        layout.prop(text, 'use_animated_text', text="")

    def draw(self, context):
        st = context.space_data
        text = context.active_object.data
        layout = self.layout
        layout.prop(text, 'character_count')
        layout.prop(text, 'use_text_datablock')
        if not text.use_text_datablock:
            layout.prop(text, 'source_text')
        else:
            layout.prop(text, 'source_text_file')


def get_text_blocks(self, context):
    '''Return Text Datablocks for Enum Property'''
    return [tuple([dblock.name] * 3) for dblock in bpy.data.texts]


def register():
    '''
    addon registration function
    '''
    # create properties
    bpy.types.TextCurve.character_count = bpy.props.IntProperty(
      update=update_func, min=0, options={'ANIMATABLE'})
    bpy.types.TextCurve.backup_text = bpy.props.StringProperty()
    bpy.types.TextCurve.use_animated_text = bpy.props.BoolProperty(
      default=False)
    bpy.types.TextCurve.source_text = bpy.props.StringProperty()
    bpy.types.TextCurve.use_text_datablock = bpy.props.BoolProperty(
      default=False)
    bpy.types.TextCurve.source_datablock = bpy.props.EnumProperty(
      items=get_text_blocks)
    # register the module:
    bpy.utils.register_class(TEXT_PT_Typewriter)
    # add the frame change handler
    bpy.app.handlers.frame_change_post.append(typewriter_text_update_frame)


def unregister():
    '''
    addon unregistration function
    '''
    # remove the frame change handler
    bpy.app.handlers.frame_change_post.remove(typewriter_text_update_frame)
    # remove the panel
    bpy.utils.unregister_class(TEXT_PT_Typewriter)
    # remove the properties
    del(bpy.types.TextCurve.character_count)
    del(bpy.types.TextCurve.backup_text)
    del(bpy.types.TextCurve.use_animated_text)
    del(bpy.types.TextCurve.source_text)
    del(bpy.types.TextCurve.use_text_datablock)


if __name__ == "__main__":
    register()

 
