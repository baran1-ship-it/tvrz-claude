import bpy, os, math
HERE="/home/claude/work"
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,"out","check_kz1.blend"))
rock=bpy.data.objects["game_rock"]
for i,(n,loc,rot) in enumerate((("mech_2",(0.05,-0.1,0.72),(0.25,0.0,0)),("mech_1",(-0.4,-0.2,0.6),(0.5,-0.3,0)),("mech_3",(0.35,0.15,0.62),(-0.3,0.35,0)))):
    with bpy.data.libraries.load(os.path.join(HERE,f"{n}.blend")) as (s,d): d.objects=[n]
    o=d.objects[0]; bpy.context.collection.objects.link(o); o.location=loc; o.rotation_euler=rot
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active=rock
bpy.ops.object.join(); rock.name="game_rock"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,"mech_test.blend"))
