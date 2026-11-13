import bpy, os, math
from mathutils import Vector
UBC = "/home/claude/dl/kc/assets/universal_base_characters"
BASE = f"{UBC}/Base Characters/Superhero_Female_FullBody.gltf"
HAIR = f"{UBC}/Hairstyles/Rigged"
UAL1 = "/home/claude/tvrz-claude/modely/postavy/animace_ual/UAL1_Standard.glb"
UAL2 = "/home/claude/tvrz-claude/modely/postavy/animace_ual/UAL2_Standard.glb"
OUT = "/home/claude/z30/out"

def imp(p):
    b = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in b]
    for o in list(new):
        if o.type == 'MESH' and o.name.startswith("Icosphere"):
            new.remove(o); bpy.data.objects.remove(o)
    return new

def setup_render(res=(900, 1200), samples=24):
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = samples
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.view_settings.view_transform = 'AgX'
    w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.75, 0.8, 0.88, 1); bg.inputs[1].default_value = 0.6
    def light(name, rot, energy, size=3):
        l = bpy.data.lights.new(name, 'SUN'); l.energy = energy; l.angle = math.radians(size)
        o = bpy.data.objects.new(name, l); scn.collection.objects.link(o); o.rotation_euler = [math.radians(a) for a in rot]
    light("key", (55, 0, 35), 3.2, 8); light("fill", (70, 0, -60), 0.9, 20); light("rim", (60, 0, 180), 1.5, 5)

def cam(loc, target, lens=50, name="cam"):
    scn = bpy.context.scene
    c = bpy.data.cameras.new(name); c.lens = lens
    o = bpy.data.objects.new(name, c); scn.collection.objects.link(o)
    o.location = Vector(loc); d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); scn.camera = o
    return o

def render(path):
    bpy.context.scene.render.filepath = path; bpy.ops.render.render(write_still=True)
