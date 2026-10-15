"""Materiál skály + náhledové rendery.
Spuštění: python3 rock_render.py <rock_hi.blend> <prefix_výstupu> [samples]
"""
import sys, math, os
import bpy
from mathutils import Vector

SRC = sys.argv[1]
PREFIX = sys.argv[2]
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 96

bpy.ops.wm.open_mainfile(filepath=SRC)
ROCK_OBJ = os.environ.get("ROCK_OBJ", "rock_hi")
rock = bpy.data.objects[ROCK_OBJ]
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not rock and not o.name.startswith("plachta"):
        bpy.data.objects.remove(o)

scn = bpy.context.scene

import importlib.util, os
_spec = importlib.util.spec_from_file_location("rock_mat", os.path.join(os.path.dirname(os.path.abspath(__file__)), "rock_mat.py"))
rock_mat = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(rock_mat)
N, L, ramp, mix, math_, noise_tex, smooth = (rock_mat.N, rock_mat.L, rock_mat.ramp, rock_mat.mix,
                                               rock_mat.math_, rock_mat.noise_tex, rock_mat.smooth)
MATMOD = os.environ.get("MATMOD", "rock")
if not rock.data.materials or not rock.data.materials[0].name.startswith("game_"):
    if MATMOD == "wagon":
        _ws = importlib.util.spec_from_file_location("wagon_mat", os.path.join(os.path.dirname(os.path.abspath(__file__)), "wagon_mat.py"))
        wagon_mat = importlib.util.module_from_spec(_ws); _ws.loader.exec_module(wagon_mat)
        (wagon_mat.apply_log if rock.get("kind") == "log" else wagon_mat.apply)(rock)
        if "plachta" in bpy.data.objects and not bpy.data.objects["plachta"].data.materials:
            wagon_mat.apply_canvas(bpy.data.objects["plachta"])
    else:
        rock_mat.apply(rock)
if MATMOD != "wagon":
    rock.location.z = -0.05 * max(rock.dimensions) / 2.6
WIRE = os.environ.get("WIRE")
# náhled listí: prosvítání (v Godotu odpovídá volbě Back Lighting u materiálu listí)
for m in bpy.data.materials:
    if m.name.endswith("_listi") and m.use_nodes and not os.environ.get("NOTRANS"):
        t = m.node_tree
        b = next((n for n in t.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        o = next((n for n in t.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if b is None or o is None or "Translucent BSDF" in [n.bl_label for n in t.nodes]:
            continue
        tr = t.nodes.new("ShaderNodeBsdfTranslucent")
        if b.inputs["Base Color"].links:
            t.links.new(b.inputs["Base Color"].links[0].from_socket, tr.inputs["Color"])
        mx = t.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.35
        t.links.new(b.outputs[0], mx.inputs[1]); t.links.new(tr.outputs[0], mx.inputs[2])
        # alfa ořez i pro průsvitnou složku
        tp = t.nodes.new("ShaderNodeBsdfTransparent"); mx2 = t.nodes.new("ShaderNodeMixShader")
        if b.inputs["Alpha"].links:
            t.links.new(b.inputs["Alpha"].links[0].from_socket, mx2.inputs[0])
        t.links.new(tp.outputs[0], mx2.inputs[1]); t.links.new(mx.outputs[0], mx2.inputs[2])
        t.links.new(mx2.outputs[0], o.inputs["Surface"]); print('TRANSLUCENT', m.name)
# ------------------------------------------------------------ terén (hlína, tráva, jehličí)
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0.02))
ground = bpy.context.active_object
gm = bpy.data.materials.new("ground"); gm.use_nodes = True
g = gm.node_tree; g.nodes.clear()
go = N(g, "ShaderNodeOutputMaterial", (600, 0)); gb = N(g, "ShaderNodeBsdfPrincipled", (300, 0))
L(g, gb.outputs[0], go.inputs[0])
gtc = N(g, "ShaderNodeTexCoord", (-900, 0))
gn = noise_tex(g, gtc.outputs["Object"], 0.6, 8, 0.6)
gn2 = noise_tex(g, gtc.outputs["Object"], 40.0, 6, 0.7)
gmix = math_(g, 'ADD', math_(g, 'MULTIPLY', gn.outputs[0], 0.6), math_(g, 'MULTIPLY', gn2.outputs[0], 0.4))
grd = ramp(g, gmix, [(0.35, (0.055, 0.042, 0.028)), (0.5, (0.10, 0.08, 0.05)),
                     (0.58, (0.10, 0.12, 0.04)), (0.75, (0.16, 0.17, 0.06))], (0, 0))
L(g, grd.outputs[0], gb.inputs["Base Color"])
gb.inputs["Roughness"].default_value = 0.95
gbump = N(g, "ShaderNodeBump", (100, -300)); gbump.inputs["Strength"].default_value = 0.6
L(g, gn2.outputs[0], gbump.inputs["Height"]); L(g, gbump.outputs[0], gb.inputs["Normal"])
ground.data.materials.append(gm)

# ------------------------------------------------------------ světlo: odpolední slunce
world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
sky = N(wn, "ShaderNodeTexSky", (0, 0))
try:
    sky.sky_type = 'MULTIPLE_SCATTERING'
except TypeError:
    sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(34); sky.sun_rotation = math.radians(90 - 75)
sky.sun_disc = False
bg = N(wn, "ShaderNodeBackground", (250, 0)); bg.inputs["Strength"].default_value = 0.06
wo = N(wn, "ShaderNodeOutputWorld", (450, 0))
L(wn, sky.outputs[0], bg.inputs[0]); L(wn, bg.outputs[0], wo.inputs[0])

sun_d = bpy.data.lights.new("sun", 'SUN'); sun_d.energy = 3.4; sun_d.angle = math.radians(1.2)
sun_d.color = (1.0, 0.94, 0.85)
sun = bpy.data.objects.new("sun", sun_d); scn.collection.objects.link(sun)
SUN_AZ, SUN_EL = math.radians(75), math.radians(34)      # slunce zleva zepředu
sdir = Vector((math.cos(SUN_AZ) * math.cos(SUN_EL), math.sin(SUN_AZ) * math.cos(SUN_EL), math.sin(SUN_EL)))
sun.rotation_euler = sdir.to_track_quat('Z', 'Y').to_euler()

# ------------------------------------------------------------ render
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = True
scn.cycles.max_bounces = 6
scn.cycles.transparent_max_bounces = 128
scn.render.resolution_x = 1280; scn.render.resolution_y = 860
scn.view_settings.view_transform = 'AgX'
scn.view_settings.look = 'AgX - Medium High Contrast'
scn.render.image_settings.file_format = 'JPEG'
scn.render.image_settings.quality = 90

cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d)
scn.collection.objects.link(cam); scn.camera = cam
target = bpy.data.objects.new("tgt", None); scn.collection.objects.link(target)
tr = cam.constraints.new('TRACK_TO'); tr.target = target
tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'

views = {
    "a_predni":  ((4.6, 3.6, 1.7), (0, 0, 0.75), 38),
    "b_severni": ((-2.8, -4.8, 2.3), (0, 0, 0.7), 38),
    "c_bok":     ((-5.2, 1.2, 1.1), (0, 0, 0.75), 40),
    "d_detail":  ((1.6, 1.25, 1.25), (0.35, 0.1, 0.9), 55),
}
if MATMOD == "wagon":
    views = {
        "a_predni":  ((4.6, -6.0, 2.2), (0, -0.5, 0.8), 32),
        "b_zadni":   ((-4.2, 4.8, 2.6), (0, 0.3, 0.8), 32),
        "c_bok":     ((6.5, 0.4, 1.4), (0, 0.0, 0.8), 30),
        "d_detail":  ((1.9, 1.5, 1.2), (0.6, 0.9, 0.6), 40),
        "e_kolo":    ((1.8, -1.6, 0.7), (0.65, -0.85, 0.45), 45),
        "f_shora":   ((2.2, 2.2, 3.4), (0, 0.4, 0.9), 30),
    }
only = sys.argv[4].split(",") if len(sys.argv) > 4 else list(views)
for name in only:
    loc, tg, lens = views[name]
    k = max(rock.dimensions) / 2.6 if MATMOD != "wagon" else 1.0
    if os.environ.get("CAMK"): k = float(os.environ["CAMK"])
    cam.location = Vector(loc) * k; target.location = Vector(tg) * k; cam_d.lens = lens
    scn.render.filepath = f"{PREFIX}_{name}.jpg"
    bpy.ops.render.render(write_still=True)
    print("rendered", scn.render.filepath)
