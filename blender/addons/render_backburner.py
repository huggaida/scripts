# -*- coding: utf8 -*-
# python
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
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {"name": "Backburner",
           "author": "Template Matt Ebb | Blaize | Anthony Hunt | Spirou4D",
           "version": (1, 20, 0),
           "blender": (2, 80, 0),
           "location": "Properties > Render",
           "description": "Network and Queue with Autodesk Backburner",
           "warning": "",
           "wiki_url": "",
           "category": "Render"}


import bpy, os, subprocess
from subprocess import Popen, PIPE
from bpy.props import PointerProperty, StringProperty, BoolProperty, EnumProperty, IntProperty, CollectionProperty
from bpy.types import AddonPreferences, Menu, Panel, UIList, Operator

default_blender_path = bpy.app.binary_path


# PROPERTIES of BACKBURNER RENDER ############################################"""
class BackburnerSettings(bpy.types.PropertyGroup):
    pass
bpy.utils.register_class(BackburnerSettings)


# entry point for settings collection
bpy.types.Scene.backburner = PointerProperty(type=BackburnerSettings, 
                                             name='Backburner Submission', 
                                             description='Backburner Submission Settings')

# fill the new struct
BackburnerSettings.job_name = StringProperty(name='Job Name', 
                                             description='Name of the job to be shown in Backburner', 
                                             maxlen=256, 
                                             default='Job_Name')
BackburnerSettings.job_details = StringProperty(name='Description', 
                                                description='Add aditional information to render task', 
                                                maxlen=400, 
                                                default='Description')
BackburnerSettings.frames_per_task = IntProperty(name='Frames per Task', 
                                                 description='Number of frames to give each render node', 
                                                 min=1, 
                                                 max=1000, 
                                                 soft_min=1, 
                                                 soft_max=64, 
                                                 default=1)
BackburnerSettings.timeout = IntProperty(name='Timeout', 
                                         description='Timeout per task', 
                                         min=1, 
                                         max=1000, 
                                         soft_min=1, 
                                         soft_max=64, 
                                         default=120)
BackburnerSettings.priority = IntProperty(name='Priority', 
                                          description='Priority of this job', 
                                          min=1, 
                                          max=1000, 
                                          soft_min=1, 
                                          soft_max=64, 
                                          default=50)
BackburnerSettings.override_frame_range = BoolProperty(name='Override Frame Range', 
                                                       description='Override scene start and end frames', 
                                                       default=False)
BackburnerSettings.frame_start = IntProperty(name='Start Frame', 
                                             description='Start frame of animation sequence to render', 
                                             min=1, 
                                             max=50000, 
                                             soft_min=1, 
                                             soft_max=64, 
                                             default=1)
BackburnerSettings.frame_end = IntProperty(name='End Frame', 
                                           description='End frame of animation sequence to render', 
                                           min=1, 
                                           max=50000, 
                                           soft_min=1, 
                                           soft_max=64, 
                                           default=250)
BackburnerSettings.manager = StringProperty(name='Manager', 
                                            description='Name of render manager', 
                                            maxlen=400, 
                                            default='192.168.1.112')
BackburnerSettings.servers = StringProperty(name='Servers', 
                                            description='Render this job only with the servers specified (semi-colon separated list - ignored if group is used)', 
                                            maxlen=400, 
                                            default='')
BackburnerSettings.path_backburner = StringProperty(name='Backburner Path', 
                                                    description='Path to Backburner cmdjob.exe', 
                                                    maxlen=400, 
                                                    subtype='FILE_PATH')
BackburnerSettings.path_blender = StringProperty(name='Blender Path', 
                                                 description='Path to blender.exe', 
                                                 maxlen=400, 
                                                 default=default_blender_path, 
                                                 subtype='FILE_PATH')

# FUNCTIONS #####################################################################################
def Set_BackburnerPath(self, context):
    bbs = context.scene.backburner
    bbs.path_backburner = context.user_preferences.addons[__name__].preferences.backburner_path


def write_tasklist(step, sframe, eframe, filename):
    dir = os.path.dirname(filename)
    tasklist_path = os.path.join(dir,"submit_temp.txt")

    try:
        file = open(tasklist_path, 'w')
    except:
        print("couldn't open " + tasklist_path + " for writing")

    curframe = sframe
    while(curframe <= eframe):
        seq_sta = curframe
        seq_end = curframe + (step-1)
        if seq_end > eframe: seq_end = eframe
        curframe = seq_end + 1

        task = 'Frame_' + str(seq_sta)
        if seq_sta != seq_end:
            task += ' - ' + str(seq_end)
        task += '\t'
        task += str(seq_sta) + '\t' + str(seq_end) + '\n'
        file.write(task)

    file.close()
    return tasklist_path


def submit(scene):
    bb = scene.backburner
    filename = bpy.data.filepath
    blenderdir = default_blender_path

    print('--- Submitting: ')
    tasklist_path = write_tasklist(bb.frames_per_task, bb.frame_start, bb.frame_end, filename)

    cmd = '' + bb.path_backburner + ''
    cmd += ' -jobName:"' + bb.job_name + '"'
    cmd += ' -manager ' + bb.manager
    cmd += ' -description:"' + bb.job_details + '"'
    cmd += ' -priority:' + str(bb.priority)
    cmd += ' -timeout:' + str(bb.timeout)
    cmd += ' -suspended'
    #cmd += ' -logPath:' + os.path.join(os.path.dirname(filename),'log')
    if bb.servers != '':
        cmd += ' -servers:' + bb.servers
    #cmd += ' -workPath:' + blenderdir
    cmd += ' -taskList:"' + tasklist_path + '"'
    cmd += ' -taskName: 1'
    cmd += ' "' + bb.path_blender + '" --background '
    cmd += '"' + filename + '"'
    cmd += ' --frame-start %tp2 --frame-end %tp3 --render-anim'
    print(cmd)

    #result = subprocess.call(cmd)
    result = subprocess.check_output(cmd, shell=True)

    if result != 0:
        print('Submit Failed for: ' + filename)
        submit_status = "FAILED"
    else:
        print('Submit Suceeded for: ' + filename)
        submit_status = "OK"
    os.remove(tasklist_path)
    return {'FINISHED'}



class SubmitToBackburner(bpy.types.Operator):
    '''Submit the render to backburner'''
    bl_idname = "render.submit_to_backburner"
    bl_label = "Submit to Backburner"

    @classmethod
    def poll(cls, context):
        return context.scene != None

    def invoke(self, context, event):
        bb = context.scene.backburner
        if bb.path_blender == '':
            self.report({'ERROR'}, "Network path to Blender hasn't been set")
            return {'CANCELLED'}
        if bb.path_backburner == '':
            self.report({'ERROR'}, "Path to Backburner cmdjob.exe hasn't been set")
            return {'CANCELLED'}
        submit(context.scene)
        return {'FINISHED'}

    def execute(self, context):
        submit(context.scene)



class RENDER_PT_Backburner(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_label = 'Backburner'
    bl_default_closed = True


    def draw(self, context):
        scene = context.scene
        bb = scene.backburner

        layout = self.layout
        layout.operator('render.submit_to_backburner', icon='RENDER_ANIMATION')
        layout.separator()
        
        layout.prop(bb, 'job_name')
        layout.prop(bb, 'job_details')
        layout.separator()

        layout.prop(bb, 'frames_per_task')

        row = layout.row()
        row.prop(bb, 'timeout')
        row.prop(bb, 'priority')
        layout.prop(bb, 'override_frame_range')

        row = layout.row()
        row.enabled = bb.override_frame_range
        row.prop(bb, 'frame_start')
        row.prop(bb, 'frame_end')
        layout.separator()

        layout.prop(bb, 'manager')
        layout.prop(bb, 'servers')



#-----------------------------------------------Preferences of add-on
class BackburnerPrefs(AddonPreferences):
    """Inform the Backburner path"""
    bl_idname = __name__

    enable_Tab_Prefs_01 = bpy.props.BoolProperty(
        name = "Defaults",
        default=False
    )

    backburner_path = bpy.props.StringProperty(
        name="Backburner path",
        description="Choose the path to Backburner exe",
        subtype='FILE_PATH',
        update=Set_BackburnerPath
    )

    def check(context):
        return True    

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "enable_Tab_Prefs_01", icon="QUESTION")
        if self.enable_Tab_Prefs_01:
            row = layout.row(align=True)
            row.label(text="Backburner location: ")
            row.prop(self, "backburner_path", text="C:\\Program Files (x86)\\Autodesk\\Backburner\\cmdjob.exe")



# REGISTER CLASS #########################################################
dclasses = (
SubmitToBackburner,
BackburnerSettings,
RENDER_PT_Backburner,
)


def register():
    bpy.utils.register_class(SubmitToBackburner)
    # bpy.utils.register_class(BackburnerSettings)
    bpy.utils.register_class(RENDER_PT_Backburner)
   

def unregister():
    bpy.utils.unregister_class(SubmitToBackburner)
    bpy.utils.unregister_class(BackburnerSettings)
    bpy.utils.unregister_class(RENDER_PT_Backburner )


if __name__ == "__main__":
    register()