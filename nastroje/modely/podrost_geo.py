"""Podrost a rostliny u vody z karet atlasu (alpha clip, oboustranné).
Spuštění: python3 podrost_geo.py <kapradi|kopriva|ostruzina|rakos|orobinec> <seed> <název>
"""
import sys, os, math, json, random
import bpy, bmesh
from mathutils import Vector, Quaternion

KIND, SEED, NAME = sys.argv[1], int(sys.argv[2]), sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")
rng = random.Random(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)
cards = json.load(open(os.path.join(HERE, "atlas", f"{KIND}P_cards.json")))["cards"]
verts, faces, uvs, cols = [], [], [], []

def bent_card(base, up_dir, out_dir, length, width, bend, nseg, card, shade=1.0):
    """Karta ohnutá podél délky (oblouk dolů o úhel bend), uv po délce."""
    side = up_dir.cross(out_dir)
    if side.length < 1e-4: side = Vector((1, 0, 0))
    side.normalize()
    i0 = len(verts)
    p = base.copy(); d = up_dir.normalized()
    for k in range(nseg + 1):
        t = k / nseg
        for s in (-0.5, 0.5):
            verts.append(tuple(p + side * s * width))
            uvs.append((card["u0"] + (s + 0.5) * (card["u1"] - card["u0"]), card["v0"] + t * (card["v1"] - card["v0"])))
            cols.append((shade * (0.55 + 0.45 * t),) * 3)
        if k < nseg:
            d = (Quaternion(side, -bend / nseg) @ d).normalized()
            p = p + d * (length / nseg)
    for k in range(nseg):
        a = i0 + k * 2
        faces.append((a, a + 1, a + 3, a + 2))

if KIND == "kapradi":
    n = rng.randint(9, 15); L = rng.uniform(0.6, 1.0)
    for i in range(n):
        az = i * math.tau / n + rng.uniform(-0.25, 0.25)
        out = Vector((math.cos(az), math.sin(az), 0))
        el = rng.uniform(0.85, 1.3)
        up = (out * math.cos(el) + Vector((0, 0, math.sin(el)))).normalized()
        bent_card(Vector((0, 0, -0.02)) + out * 0.04, up, out, L * rng.uniform(0.8, 1.1), L * 0.42,
                  -rng.uniform(0.7, 1.1), 4, rng.choice(cards))
elif KIND == "kopriva":
    n = rng.randint(9, 15)
    for i in range(n):
        p = Vector((rng.gauss(0, 0.28), rng.gauss(0, 0.28), -0.02)); hgt = rng.uniform(0.7, 1.3)
        az = rng.uniform(0, math.pi)
        out = Vector((math.cos(az), math.sin(az), 0))
        for c in range(2):                                   # zkřížená dvojice
            o = Quaternion((0, 0, 1), c * math.pi / 2) @ out
            bent_card(p, Vector((rng.gauss(0, 0.06), rng.gauss(0, 0.06), 1)), o, hgt, hgt * 0.5, rng.uniform(0.0, 0.25), 2, rng.choice(cards))
elif KIND == "ostruzina":
    # oblouky prutů (3D) + listové karty podél nich
    bm = bmesh.new()
    canes = []
    for i in range(rng.randint(5, 8)):
        az = rng.uniform(0, math.tau); L = rng.uniform(1.4, 2.6); hmax = rng.uniform(0.5, 1.0)
        pts = []
        for k in range(10):
            t = k / 9
            r = L * t
            pts.append(Vector((math.cos(az) * r, math.sin(az) * r, hmax * math.sin(math.pi * min(1, t * 1.1)) - 0.03)))
        canes.append(pts)
        prev = None
        for k, p in enumerate(pts):
            ring = []
            dvec = (pts[min(k + 1, 9)] - pts[max(k - 1, 0)]).normalized()
            sd = dvec.cross(Vector((0, 0, 1))).normalized(); up = sd.cross(dvec)
            rr = 0.012 * (1 - 0.6 * k / 9)
            for q in range(5):
                a = q / 5 * math.tau
                ring.append(bm.verts.new(p + (sd * math.cos(a) + up * math.sin(a)) * rr))
            if prev:
                for q in range(5):
                    bm.faces.new((prev[q], prev[(q + 1) % 5], ring[(q + 1) % 5], ring[q]))
            prev = ring
    me_c = bpy.data.meshes.new("pruty"); bm.to_mesh(me_c); bm.free()
    m_c = bpy.data.materials.new(f"game_{NAME}_prut"); m_c.use_nodes = True
    m_c.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.06, 0.06, 1)
    m_c.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
    me_c.materials.append(m_c)
    ob_c = bpy.data.objects.new("pruty", me_c); bpy.context.collection.objects.link(ob_c)
    for pts in canes:
        for k in range(2, 10):
            if rng.random() < 0.85:
                p = pts[k]; dvec = (pts[min(k + 1, 9)] - pts[k - 1]).normalized()
                out = Vector((p.x, p.y, 0)).normalized()
                up = (dvec * 0.5 + Vector((0, 0, 0.7)) + out * 0.3).normalized()
                bent_card(p - up * 0.1, up, out, rng.uniform(0.45, 0.65), rng.uniform(0.45, 0.65), 0.3, 2, rng.choice(cards))
elif KIND in ("rakos", "orobinec"):
    n = rng.randint(10, 16) if KIND == "rakos" else rng.randint(6, 10)
    for i in range(n):
        p = Vector((rng.gauss(0, 0.35), rng.gauss(0, 0.35), -0.05)); hgt = rng.uniform(2.0, 2.8) if KIND == "rakos" else rng.uniform(1.4, 2.0)
        az = rng.uniform(0, math.pi); out = Vector((math.cos(az), math.sin(az), 0))
        for c in range(2):
            o = Quaternion((0, 0, 1), c * math.pi / 2) @ out
            bent_card(p, Vector((rng.gauss(0, 0.05), rng.gauss(0, 0.05), 1)), o, hgt, hgt / 3.0, rng.uniform(0.0, 0.2), 3, rng.choice(cards))

me = bpy.data.meshes.new(NAME); me.from_pydata(verts, [], faces)
uvl = me.uv_layers.new(name="UVMap")
ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'CORNER')
for poly in me.polygons:
    for li in poly.loop_indices:
        vi = me.loops[li].vertex_index
        uvl.data[li].uv = uvs[vi]; ca.data[li].color = (*cols[vi], 1.0)
for p in me.polygons: p.use_smooth = True
m = bpy.data.materials.new(f"game_{NAME}"); m.use_nodes = True; m.use_backface_culling = False
t = m.node_tree; b = t.nodes["Principled BSDF"]
tx = t.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(HERE, "atlas", f"{KIND}P_color.png"))
nx = t.nodes.new("ShaderNodeTexImage"); nx.image = bpy.data.images.load(os.path.join(HERE, "atlas", f"{KIND}P_normal.png"))
nx.image.colorspace_settings.name = 'Non-Color'
vc = t.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"
mx = t.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
t.links.new(tx.outputs["Color"], mx.inputs[6]); t.links.new(vc.outputs["Color"], mx.inputs[7]); t.links.new(mx.outputs[2], b.inputs["Base Color"])
r = t.nodes.new("ShaderNodeMath"); r.operation = 'ROUND'
t.links.new(tx.outputs["Alpha"], r.inputs[0]); t.links.new(r.outputs[0], b.inputs["Alpha"])
nm = t.nodes.new("ShaderNodeNormalMap"); t.links.new(nx.outputs[0], nm.inputs["Color"]); t.links.new(nm.outputs[0], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.65
me.materials.append(m)
o = bpy.data.objects.new(NAME, me); bpy.context.collection.objects.link(o)
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = o
if len(bpy.context.selected_objects) > 1:
    bpy.ops.object.join()
o = bpy.context.active_object; o.name = NAME
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"{NAME}.glb"), export_format='GLB', use_selection=True,
                          export_yup=True, export_apply=True, export_cameras=False, export_lights=False,
                          export_vertex_color='MATERIAL')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{NAME}.blend"))
d = o.dimensions
print(f"RESULT {NAME} tris={sum(len(p.vertices) - 2 for p in o.data.polygons)} dims_m(sxvxh)={d.x:.2f} x {d.z:.2f} x {d.y:.2f}")
