"""Trs trávy z karet atlasu (alpha clip, oboustranné).
Spuštění: python3 grass_geo.py <seed> <název> <vysoka|nizka>
"""
import sys, os, math, json, random
import bpy
from mathutils import Vector

SEED = int(sys.argv[1]); NAME = sys.argv[2]; KIND = sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")
rng = random.Random(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)
cards = json.load(open(os.path.join(HERE, "atlas", "trava1k_cards.json")))["cards"]
pool = [c for c in cards if c["kind"] == ("cluster" if KIND == "vysoka" else "single")]

verts, faces, uvs = [], [], []
n = rng.randint(5, 7) if KIND == "vysoka" else rng.randint(4, 6)
H = rng.uniform(0.75, 1.05) if KIND == "vysoka" else rng.uniform(0.28, 0.42)
for i in range(n):
    a = i * math.pi / n + rng.uniform(-0.2, 0.2)
    rt = Vector((math.cos(a), math.sin(a), 0))
    off = Vector((rng.gauss(0, 0.04), rng.gauss(0, 0.04), 0))
    w = H * rng.uniform(0.9, 1.15)
    h = H * rng.uniform(0.85, 1.1)
    lean = rt.cross(Vector((0, 0, 1))) * rng.uniform(-0.15, 0.15) * h
    c = rng.choice(pool)
    i0 = len(verts)
    # 2 řady (dole, uprostřed, nahoře) – horní polovina se rozevírá
    for row, t in enumerate((0.0, 0.5, 1.0)):
        spread = 1.0 + 0.25 * t
        for side in (-0.5, 0.5):
            p = off + rt * (side * w * spread) + Vector((0, 0, t * h - 0.02)) + lean * t * t
            verts.append(tuple(p))
            uvs.append((c["u0"] + (side + 0.5) * (c["u1"] - c["u0"]), c["v0"] + t * (c["v1"] - c["v0"])))
    faces += [(i0, i0 + 1, i0 + 3, i0 + 2), (i0 + 2, i0 + 3, i0 + 5, i0 + 4)]
me = bpy.data.meshes.new(NAME); me.from_pydata(verts, [], faces)
uvl = me.uv_layers.new(name="UVMap")
for poly in me.polygons:
    for li in poly.loop_indices:
        uvl.data[li].uv = uvs[me.loops[li].vertex_index]
for p in me.polygons: p.use_smooth = True
m = bpy.data.materials.new(f"game_{NAME}"); m.use_nodes = True; m.use_backface_culling = False
t = m.node_tree; b = t.nodes["Principled BSDF"]
tx = t.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(HERE, "atlas", "trava1k_color.png"))
nx = t.nodes.new("ShaderNodeTexImage"); nx.image = bpy.data.images.load(os.path.join(HERE, "atlas", "trava1k_normal.png"))
nx.image.colorspace_settings.name = 'Non-Color'
nm = t.nodes.new("ShaderNodeNormalMap")
t.links.new(tx.outputs["Color"], b.inputs["Base Color"])
r = t.nodes.new("ShaderNodeMath"); r.operation = 'ROUND'
t.links.new(tx.outputs["Alpha"], r.inputs[0]); t.links.new(r.outputs[0], b.inputs["Alpha"])
t.links.new(nx.outputs[0], nm.inputs["Color"]); t.links.new(nm.outputs[0], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.7
me.materials.append(m)
o = bpy.data.objects.new(NAME, me); bpy.context.collection.objects.link(o)
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"{NAME}.glb"), export_format='GLB', use_selection=True,
                          export_yup=True, export_apply=True, export_cameras=False, export_lights=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{NAME}.blend"))
d = o.dimensions
print(f"RESULT {NAME} tris={len(faces) * 2} dims_m(sxvxh)={d.x:.2f} x {d.z:.2f} x {d.y:.2f}")
