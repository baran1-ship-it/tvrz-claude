"""Vzdálená verze keře (LOD): 3 zkřížené karty s vyrenderovaným obrazem keře.
Spuštění: python3 bush_far.py <název>   (čte <název>.blend, píše out/<název>_daleko.glb)
"""
import sys, os, math
import bpy
from mathutils import Vector

NAME = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, f"{NAME}.blend"))
scn = bpy.context.scene
bush = bpy.data.objects[NAME]
d = bush.dimensions
bb = [bush.matrix_world @ Vector(c) for c in bush.bound_box]
zmax = max(v.z for v in bb); zmin = max(0.0, min(v.z for v in bb))
W = max(d.x, d.y); H = zmax

# měkké rovnoměrné světlo, průhledné pozadí
world = bpy.data.worlds.new("w"); scn.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.9
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); scn.collection.objects.link(sun)
sun.data.energy = 2.0; sun.rotation_euler = (math.radians(40), 0, math.radians(30))
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 24; scn.cycles.use_denoising = True; scn.cycles.transparent_max_bounces = 128
scn.render.film_transparent = True
scn.render.resolution_x = 512; scn.render.resolution_y = int(512 * H / W)
scn.view_settings.view_transform = 'Standard'
scn.render.image_settings.file_format = 'PNG'; scn.render.image_settings.color_mode = 'RGBA'
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scn.collection.objects.link(cam); scn.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = W

imgs = []
for i in range(3):
    a = math.radians(i * 60)
    dirv = Vector((-math.sin(a), math.cos(a), 0))   # směr pohledu kamery
    cam.location = Vector((0, 0, H / 2)) - dirv * 20
    cam.rotation_euler = (math.radians(90), 0, a)
    p = os.path.join(OUT, f"{NAME}_daleko_{i}.png")
    scn.render.filepath = p
    bpy.ops.render.render(write_still=True)
    imgs.append(p)

# nová scéna jen s kartami
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = []
for i, p in enumerate(imgs):
    a = math.radians(i * 60)
    rt = Vector((math.cos(a), math.sin(a), 0))
    v = [tuple(-rt * W / 2), tuple(rt * W / 2), tuple(rt * W / 2 + Vector((0, 0, H))), tuple(-rt * W / 2 + Vector((0, 0, H)))]
    me = bpy.data.meshes.new(f"karta{i}"); me.from_pydata(v, [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for li, c in zip(me.polygons[0].loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = c
    m = bpy.data.materials.new(f"{NAME}_daleko_{i}"); m.use_nodes = True; m.use_backface_culling = False
    t = m.node_tree; b = t.nodes["Principled BSDF"]
    tx = t.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(p)
    t.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    r = t.nodes.new("ShaderNodeMath"); r.operation = 'ROUND'
    t.links.new(tx.outputs["Alpha"], r.inputs[0]); t.links.new(r.outputs[0], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.8
    me.materials.append(m)
    o = bpy.data.objects.new(f"karta{i}", me); bpy.context.collection.objects.link(o); objs.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join(); objs[0].name = f"{NAME}_daleko"
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"{NAME}_daleko.glb"), export_format='GLB', use_selection=True,
                          export_yup=True, export_apply=True, export_cameras=False, export_lights=False)
print("FAR", NAME, "tris 6")
