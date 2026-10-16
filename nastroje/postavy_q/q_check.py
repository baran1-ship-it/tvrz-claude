"""Kontrola exportu: načte tělo + výchozí kusy z <jmeno>_sada.json, animace UAL, render (herní světlo).
python3 q_check.py <slozka> <jmeno1,jmeno2,..> <out.jpg> [ANIM=Walk_Loop]"""
import bpy, sys, os, json, math
from mathutils import Vector
D, NAMES, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
UAL = "/home/claude/dl/ual1/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p):
    b = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p); return [o for o in bpy.data.objects if o not in b]
an = imp(UAL)
for o in an: bpy.data.objects.remove(o)
act = bpy.data.actions.get(os.environ.get("ANIM", "Walk_Loop"))
arms = []
for i, n in enumerate(NAMES.split(",")):
    S = json.load(open(os.path.join(D, f"{n}_sada.json")))
    objs = imp(os.path.join(D, S["telo"])); arm = next(o for o in objs if o.type == 'ARMATURE')
    for k in S["vychozi"]:
        new = imp(os.path.join(D, S["kusy"][k]["soubor"]))
        for o in new:
            if o.type == 'MESH':
                for m in o.modifiers:
                    if m.type == 'ARMATURE': m.object = arm
                mw = o.matrix_world.copy(); o.parent = arm; o.matrix_world = mw
        for o in new:
            if o.type == 'ARMATURE': bpy.data.objects.remove(o)
    arm.location.x = (i - 1) * 0.9
    arm.animation_data_create(); arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    arms.append(arm)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'; scn.cycles.samples = 24; scn.cycles.use_denoising = True
w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True; nt = w.node_tree
bg = nt.nodes["Background"]; tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sp.inputs[0]); ramp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(sp.outputs["Z"], ramp.inputs[0])
ramp.color_ramp.elements[0].color = (0.75, 0.78, 0.8, 1); ramp.color_ramp.elements[1].color = (0.28, 0.45, 0.85, 1)
nt.links.new(ramp.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.9
sun = bpy.data.objects.new("s", bpy.data.lights.new("s", 'SUN')); scn.collection.objects.link(sun)
sun.data.energy = 4.0; sun.data.color = (1.0, 0.95, 0.88); sun.rotation_euler = (math.radians(60), 0, math.radians(35))
scn.view_settings.view_transform = 'AgX'
bpy.ops.mesh.primitive_plane_add(size=20)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); scn.collection.objects.link(cam); scn.camera = cam
cam.location = (0, -4.6, 1.0); cam.rotation_euler = (math.radians(88), 0, 0); cam.data.lens = 40
scn.render.resolution_x, scn.render.resolution_y = 900, 600
scn.frame_set(int(os.environ.get("FRAME", 12)))
scn.render.filepath = OUT; bpy.ops.render.render(write_still=True); print("OK")
