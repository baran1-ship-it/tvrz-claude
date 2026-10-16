"""Kontrola: postava.glb + animace.glb -> render několika snímků. python3 glb_check.py <postava.glb> <animace.glb> <out.jpg> anim:frame,..."""
import sys, math, bpy
from mathutils import Vector
CH, AN, OUT, LIST = sys.argv[1:5]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=AN)
arm_a = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); arm_a.name = "ANIM"
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=CH)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o not in before)
for o in list(bpy.data.objects):
    if o.parent == arm_a or o == arm_a: bpy.data.objects.remove(o)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'; scn.cycles.samples = 16; scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = 400, 600
w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.65, 0.75, 1)
sun = bpy.data.objects.new("s", bpy.data.lights.new("s", 'SUN')); scn.collection.objects.link(sun); sun.data.energy = 3; sun.rotation_euler = (0.9, 0, 0.6)
bpy.ops.mesh.primitive_plane_add(size=20)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); scn.collection.objects.link(cam); scn.camera = cam
import os
H = max(o.dimensions.z for o in bpy.data.objects if o.type == 'MESH' and o.parent == arm) if False else 1.8
for o in bpy.data.objects:
    if o.type == 'MESH' and (((("cop" if os.environ.get("LOOSE") else "rozpustene")) in o.name) or (os.environ.get("NOHOOD") and "kapuce" in o.name)): o.hide_render = True
zs = [ (o.matrix_world @ Vector(c)).z for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Plane' for c in o.bound_box]
H = max(zs)
CL = float(os.environ.get("CLOSE", "0"))
tgt = Vector((0, 0, H * (0.5 if not CL else 0.87)))
d = 3.6 * H / 1.8 if not CL else 1.1
cam.location = tgt + Vector((math.sin(math.radians(30)) * d, -math.cos(math.radians(30)) * d, 0.05))
cam.rotation_euler = (math.radians(90), 0, math.radians(30)); cam.data.lens = 50
arm.animation_data_create()
from PIL import Image, ImageDraw
tiles = []
for i, it in enumerate(LIST.split(",")):
    nm, fr = it.split(":")
    act = bpy.data.actions.get(nm) or next((a for a in bpy.data.actions if a.name.startswith(nm)), None)
    arm.animation_data.action = act
    if act is None:
        for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    scn.frame_set(int(fr))
    p = f"/tmp/claude-0/gc_{i}.png"; scn.render.filepath = p; bpy.ops.render.render(write_still=True)
    im = Image.open(p).convert("RGB"); ImageDraw.Draw(im).text((6, 6), nm, fill=(0, 0, 0)); tiles.append(im)
c = Image.new("RGB", (400 * len(tiles), 600))
for i, t in enumerate(tiles): c.paste(t, (400 * i, 0))
c.save(OUT); print("OK", [a.name for a in bpy.data.actions][:5])
