bl_info = {
    "name": "Backburner",
    "author": "Blaize - original script by Matt Ebb",
    "version": (1, 1),
    "blender": (2, 80, 1),
    "location": "Properties > Render",
    "description": "Network and Queue with Autodesk Backburner",
    "warning": "",
    "wiki_url": "",
    "category": "Render"}


import bpy, os, subprocess
from subprocess import Popen, PIPE
from bpy.props import PointerProperty, StringProperty, BoolProperty, EnumProperty, IntProperty, CollectionProperty


default_backburner_path = 'C:\\Program Files (x86)\\Autodesk\\Backburner\\cmdjob.exe'
default_blender_path = 'C:\\blender\\blender.exe'


class BackburnerSettings(bpy.types.PropertyGroup):
    pass

bpy.utils.register_class(BackburnerSettings)


# entry point for settings collection
bpy.types.Scene.backburner = PointerProperty(type=BackburnerSettings, name='Backburner Submission', description='Backburner Submission Settings')


# fill the new struct
BackburnerSettings.job_name = StringProperty(
    name='Job Name', description='Name of the job to be shown in Backburner', maxlen=256, default='Job_Name')
BackburnerSettings.job_details = StringProperty(
    name='Description', description='Add aditional information to render task', maxlen=400, default='Description')


BackburnerSettings.frames_per_task = IntProperty(
    name='Frames per Task', description='Number of frames to give each render node', min=1, max=1000, soft_min=1, soft_max=64, default=1)
BackburnerSettings.timeout = IntProperty(
    name='Timeout', description='Timeout per task', min=1, max=1000, soft_min=1, soft_max=64, default=120)
BackburnerSettings.priority = IntProperty(name='Priority', description='Priority of this job', min=1, max=1000, soft_min=1, soft_max=64, default=50)


BackburnerSettings.override_frame_range = BoolProperty(
    name='Override Frame Range', description='Override scene start and end frames', default=False)
BackburnerSettings.frame_start = IntProperty(
    name='Start Frame', description='Start frame of animation sequence to render', min=1, max=50000, soft_min=1, soft_max=64, default=1)
BackburnerSettings.frame_end = IntProperty(
    name='End Frame', description='End frame of animation sequence to render', min=1, max=50000, soft_min=1, soft_max=64, default=1)


BackburnerSettings.manager = StringProperty(
    name='Manager', description='Name of render manager', maxlen=400, default='192.168.1.112')
BackburnerSettings.servers = StringProperty(
    name='Servers', description='Render this job only with the servers specified (semi-colon separated list - ignored if group is used)', maxlen=400, default='')

BackburnerSettings.uncpath = StringProperty(
    name='UNC Path', description='UNC path of the file ', maxlen=400, default='\\\\192.168.1.107\\Project\\')



print(BackburnerSettings.servers )

BackburnerSettings.path_backburner = StringProperty(
    name='Backburner Path', description='Path to Backburner cmdjob.exe', maxlen=400, default=default_backburner_path, subtype='FILE_PATH')
BackburnerSettings.path_blender = StringProperty(
    name='Blender Path', description='Path to blender.exe', maxlen=400, default=default_blender_path, subtype='FILE_PATH')



class RENDER_PT_Backburner(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_label = 'Backburner'
    bl_default_closed = True


    def draw(self, context):
        layout = self.layout


        scene = context.scene
        bb = scene.backburner
        print ((bb))

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
        layout.prop(bb, 'uncpath')


        layout.prop(bb, 'path_backburner')
        #layout.prop(bb, 'path_blender')



def write_tasklist(step, sframe, eframe, filename):
    dir = os.path.dirname(filename)


    tasklist_path = dir + '\\submit_temp.txt'
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


    filename = bb.uncpath + os.path.splitdrive(bpy.data.filepath)[1]
    blenderdir = default_blender_path


    print('--- Submitting: ' + bb.servers)



    tasklist_path = write_tasklist(bb.frames_per_task, bb.frame_start, bb.frame_end, filename)


    cmd = '"' + bb.path_backburner + '"'
    cmd += ' -jobName:"' + bb.job_name + '"'
    cmd += ' -manager ' + bb.manager
    cmd += ' -description:"' + bb.job_details + '"'
    cmd += ' -priority:' + str(bb.priority)
    cmd += ' -timeout:' + str(bb.timeout)
    if bb.servers != '':
        cmd += ' -servers:' + bb.servers
    #cmd += ' -workPath:' + blenderdir
    cmd += ' -taskList:"' + tasklist_path + '"'
    cmd += ' -taskName: 1'
    cmd += ' "' + bb.path_blender + '" --background '
    cmd += '"' + filename + '"'
    cmd += ' --frame-start %tp2 --frame-end %tp3 --render-anim'


    print("+++++++++++++++" + bb.path_blender)


    result = subprocess.call(cmd)

    if result != 0:
        print('Submit Failed for: ' + filename)
        submit_status = "FAILED"
    else:
        print('Submit Suceeded for: ' + filename)
        submit_status = "OK"


    os.remove(tasklist_path)
    print("++++++++++++++++++++++++" + tasklist_path)
    return {'FINISHED'}



class SubmitToBackburner(bpy.types.Operator):
    ''''''
    bl_idname = "render.submit_to_backburner"
    bl_label = "Submit to Backburner"


    @classmethod
    def poll(cls, context):
        return context.scene != None


    def invoke(self, context, event):
        bb = context.scene.backburner
        print("|||||||||||||||||||||||||" + str(bb) + str(bb.servers))
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



classes = (
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