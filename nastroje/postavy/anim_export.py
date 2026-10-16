"""animace.glb: jen kostra + animace (NLA stopy), 30 fps.
python3 anim_export.py <anim.blend> <rig> <out.glb>"""
import sys
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy
AB, RIG, OUT = sys.argv[1:4]
bpy.ops.wm.open_mainfile(filepath=AB)
rig = bpy.data.objects[RIG]
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
rig.animation_data.action = None
for tr in rig.animation_data.nla_tracks: tr.mute = False; tr.is_solo = False
bpy.context.scene.render.fps = 30
for o in list(bpy.data.objects):
    if o is not rig: bpy.data.objects.remove(o)
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_yup=True,
                          export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
                          export_frame_step=1, export_optimize_animation_size=True, export_skins=True)
import json, struct
f = open(OUT, "rb"); f.read(12); ln, _ = struct.unpack("<II", f.read(8)); j = json.loads(f.read(ln))
print("ANIMS", len(j.get("animations", [])), sorted(a["name"] for a in j["animations"]))
