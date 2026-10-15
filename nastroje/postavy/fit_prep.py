"""Příprava fitování obličeje na fotku: render modelu zepředu, 68 bodů (dlib), průsečík s meshem,
delty všech obličejových targetů v těch bodech -> fit_<jmeno>.npz
python3 fit_prep.py <jmeno>
"""
import sys, os, json, math, glob
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy, numpy as np
from mathutils import Vector
sys.path.insert(0, "/home/claude/chars")
import head_features as hf

NAME = sys.argv[1]
bpy.ops.wm.open_mainfile(filepath=f"/home/claude/chars/{NAME}_head.blend")
body = bpy.data.objects[NAME]
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body and "high-poly" not in o.name: o.hide_render = True
L = hf.landmarks(body)
E = (L["eye_l"] + L["eye_r"]) / 2
scn = bpy.context.scene
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scn.collection.objects.link(cam); scn.camera = cam
D = 0.5
cam.location = (0, E.y - D, E.z - 0.03); cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.lens = 50; cam.data.sensor_width = 36
scn.render.resolution_x, scn.render.resolution_y = 900, 1200
scn.render.engine = 'CYCLES'; scn.cycles.samples = 24; scn.cycles.use_denoising = True
world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.6, 0.6, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); scn.collection.objects.link(sun)
sun.data.energy = 2.5; sun.rotation_euler = (math.radians(60), 0, math.radians(-20))
scn.view_settings.view_transform = 'Standard'
out = f"/home/claude/chars/foto/{NAME}_model_predni.png"
scn.render.filepath = out; scn.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
os.system(f"python3 /home/claude/chars/lmk.py {out} /home/claude/chars/foto/{NAME}_model_predni.json /home/claude/chars/foto/{NAME}_model_lm.jpg")
pts = json.load(open(f"/home/claude/chars/foto/{NAME}_model_predni.json"))
# paprsky z kamery
for m in body.modifiers: m.show_viewport = False
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
co, _ = hf.evaluated_coords(body)
W, Hh = scn.render.resolution_x, scn.render.resolution_y
fpx = cam.data.lens / cam.data.sensor_width * W
vidx = []
for (px, py) in pts:
    d = Vector(((px - W / 2) / fpx, 1.0, -(py - Hh / 2) / fpx)).normalized()
    hit, loc, nrm, fi, ob, _ = scn.ray_cast(dg, cam.location, d)
    if not hit or ob.name != body.name:
        vidx.append(-1); continue
    poly = body.data.polygons[fi]
    vi = min(poly.vertices, key=lambda i: (Vector(co[i]) - loc).length)
    vidx.append(vi)
print("HITS", sum(1 for v in vidx if v >= 0), "/ 68")
# delty targetů
troot = "/home/claude/dl/mpfb2/src/mpfb/data/targets"
files = []
for g in ("head", "forehead", "eyebrows", "eyes", "nose", "mouth", "cheek", "chin"):
    files += sorted(glob.glob(f"{troot}/{g}/*.target.gz"))
names = []; deltas = []
vi = np.array([v if v >= 0 else 0 for v in vidx])
for f in files:
    n = os.path.basename(f).replace(".target.gz", "")
    kb = body.data.shape_keys.key_blocks if body.data.shape_keys else {}
    ex = next((k for k in kb if k.name.endswith(n)), None) if kb else None
    if ex is not None:
        v0 = ex.value; ex.slider_max = 2.0; ex.value = v0 + 1.0
        c2, _ = hf.evaluated_coords(body); ex.value = v0
    else:
        nb = len(kb) if kb else 0
        TargetService.load_target(body, f, weight=1.0)
        c2, _ = hf.evaluated_coords(body)
        body.shape_key_remove(body.data.shape_keys.key_blocks[-1])
    deltas.append(c2[vi] - co[vi]); names.append(n)
print("TARGETS", len(names))
np.savez(f"/home/claude/chars/fit_{NAME}.npz", vidx=np.array(vidx), base=co[vi], deltas=np.array(deltas), names=np.array(names),
         model_px=np.array(pts), cam=np.array([cam.location.x, cam.location.y, cam.location.z, fpx, W, Hh]))
print("SAVED")
