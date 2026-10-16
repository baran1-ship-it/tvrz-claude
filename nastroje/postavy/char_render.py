"""Náhled postavy: portrét a celá postava.
Spuštění: python3 char_render.py <blend> <prefix> [samples] [views] [tone r,g,b] [freckles] [age]
"""
import sys, math, os
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy
from mathutils import Vector
sys.path.insert(0, "/home/claude/chars")
import importlib, skin_mat; importlib.reload(skin_mat)

SRC, PREFIX = sys.argv[1], sys.argv[2]
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 32
VIEWS = sys.argv[4].split(",") if len(sys.argv) > 4 else ["portret", "cela"]
TONE = tuple(float(x) for x in sys.argv[5].split(",")) if len(sys.argv) > 5 else (0.62, 0.42, 0.33)
FRECK = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
AGE = float(sys.argv[7]) if len(sys.argv) > 7 else 0.4

bpy.ops.wm.open_mainfile(filepath=SRC)
scn = bpy.context.scene
body = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
if not body.data.materials or not body.data.materials[0].name.endswith("_kuze") and not body.data.materials[0].name.startswith("game_"):
    skin_mat.apply(body, tone=TONE, freckles=FRECK, age=AGE)
H = body.dimensions.z
_rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if _rig and "head" in _rig.data.bones: H = (_rig.matrix_world @ _rig.data.bones["head"].tail_local).z
if os.environ.get("POSE", "1") == "1":
    from mathutils import Matrix
    rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if rig:
        for side, sg in (("l", 1), ("r", -1)):
            pb = rig.pose.bones.get(f"upperarm_{side}")
            if not pb: continue
            d = (pb.tail - pb.head).normalized()          # klidová póza (armature space)
            ang = math.atan2(abs(d.x), -d.z)               # odklon od svislice
            rot = Matrix.Rotation(sg * (ang - math.radians(12)), 4, 'Y')
            hd = pb.head.copy()
            M = Matrix.Translation(hd) @ rot @ Matrix.Translation(-hd) @ pb.bone.matrix_local
            pb.matrix = M
            bpy.context.view_layer.update()
            print("POSE", side, round(math.degrees(ang), 1))

world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
sky = wn.nodes.new("ShaderNodeTexSky")
try: sky.sky_type = 'MULTIPLE_SCATTERING'
except TypeError: sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(30); sky.sun_rotation = math.radians(200); sky.sun_disc = False
bg = wn.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 0.08
wo = wn.nodes.new("ShaderNodeOutputWorld")
wn.links.new(sky.outputs[0], bg.inputs[0]); wn.links.new(bg.outputs[0], wo.inputs[0])
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); scn.collection.objects.link(sun)
sun.data.energy = 3.0; sun.data.angle = math.radians(3); sun.data.color = (1.0, 0.95, 0.88)
sd = Vector((-0.6, -1.0, 0.75)).normalized()
sun.rotation_euler = sd.to_track_quat('Z', 'Y').to_euler()
fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", 'AREA')); scn.collection.objects.link(fill)
fill.data.energy = 60; fill.data.size = 2.0; fill.location = (1.6, -1.6, H * 0.8)
fill.rotation_euler = (Vector((0, 0, H * 0.8)) - fill.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
gm = bpy.data.materials.new("zem"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.1, 0.08, 1)
bpy.context.active_object.data.materials.append(gm)

scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = True
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
scn.render.image_settings.file_format = 'JPEG'; scn.render.image_settings.quality = 90
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scn.collection.objects.link(cam); scn.camera = cam
tgt = bpy.data.objects.new("t", None); scn.collection.objects.link(tgt)
tr = cam.constraints.new('TRACK_TO'); tr.target = tgt; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
V = {
    "portret": ((0.22, -0.75, H * 0.94), (0, 0, H * 0.935), 85, (900, 1100)),
    "profil":  ((-0.75, -0.05, H * 0.94), (0, 0, H * 0.935), 85, (900, 1100)),
    "cela":    ((1.2, -3.6, H * 0.6), (0, 0, H * 0.5), 50, (800, 1200)),
    "predni":  ((0.0, -1.1, H * 0.925), (0, -0.1, H * 0.92), 110, (700, 900)),
    "bok":     ((-1.1, -0.06, H * 0.925), (0, -0.06, H * 0.92), 110, (700, 900)),
    "cela_zad": ((-1.4, 3.4, H * 0.6), (0, 0, H * 0.5), 50, (800, 1200)),
}
for v in VIEWS:
    loc, tg, lens, res = V[v]
    cam.location = loc; tgt.location = tg; cam.data.lens = lens
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.filepath = f"{PREFIX}_{v}.jpg"
    bpy.ops.render.render(write_still=True); print("rendered", scn.render.filepath)
