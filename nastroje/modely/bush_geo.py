"""Keř – větve jako skutečná geometrie s kůrou, listí jako karty z atlasu (alpha clip, oboustranné).
Spuštění: python3 bush_geo.py <druh> <seed> <název> [výška_m]
Potřebuje atlas/<druh>_color.png, _normal.png, _cards.json (leaf_atlas.py).
Výstup: out/<název>.glb + out/<název>_daleko.glb + <název>.blend (náhled)
"""
import sys, os, math, json, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, noise
from PIL import Image

SPECIES = sys.argv[1]; SEED = int(sys.argv[2]); NAME = sys.argv[3]
HEIGHT = float(sys.argv[4]) if len(sys.argv) > 4 else 3.2
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
rng = random.Random(SEED); np.random.seed(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)

PARAM = {   # stonky, sklon, větvení, kůra (sRGB tmavá, světlá), velikost karty, hustota listí
    "liska": dict(stems=(13, 19), lean=(0.1, 0.6), spread=0.4, br=(3, 6), bark=((78, 66, 54), (128, 112, 94)),
                  lent=(165, 150, 120), card=(0.42, 0.62), dens=1.0, droop=0.15),
    "bez":   dict(stems=(5, 8), lean=(0.15, 0.6), spread=0.22, br=(3, 5), bark=((92, 84, 70), (150, 138, 116)),
                  lent=(170, 160, 135), card=(0.45, 0.65), dens=0.9, droop=0.25),
    "trnka": dict(stems=(9, 13), lean=(0.05, 0.45), spread=0.35, br=(3, 5), bark=((38, 32, 30), (74, 64, 58)),
                  lent=(110, 100, 88), card=(0.3, 0.45), dens=1.1, droop=0.05),
    "hloh":  dict(stems=(4, 7), lean=(0.1, 0.45), spread=0.2, br=(4, 7), bark=((70, 66, 60), (124, 118, 108)),
                  lent=(140, 132, 120), card=(0.35, 0.5), dens=1.1, droop=0.1),
    "sipek": dict(stems=(8, 14), lean=(0.2, 0.8), spread=0.3, br=(2, 4), bark=((70, 60, 40), (120, 108, 70)),
                  lent=(130, 120, 80), card=(0.3, 0.45), dens=0.9, droop=0.45),
}[SPECIES]

# ------------------------------------------------------------------ kůra (opakovatelná textura)
def periodic_noise(n, cells, seed):
    r = np.random.RandomState(seed)
    g = r.rand(cells, cells)
    t = np.arange(n) / n * cells
    i = t.astype(int); f = t - i; f = f * f * (3 - 2 * f)
    i1 = (i + 1) % cells
    a = g[i][:, i]; b = g[i][:, i1]; c = g[i1][:, i]; d = g[i1][:, i1]
    top = a + (b - a) * f[None, :]; bot = c + (d - c) * f[None, :]
    return top + (bot - top) * f[:, None]

def bark_texture(px=1024):
    n = np.zeros((px, px)); amp = 1.0; tot = 0
    for o, cells in enumerate((4, 8, 16, 32, 64)):
        n += amp * periodic_noise(px, cells, SEED * 7 + o); tot += amp; amp *= 0.55
    n /= tot
    # vodorovné lenticely (krátké světlé čárky napříč kmenem = podél U)
    lent = np.zeros((px, px))
    rr = np.random.RandomState(SEED + 3)
    for _ in range(int(px * 0.9)):
        y, x = rr.randint(0, px), rr.randint(0, px)
        L = rr.randint(px // 90, px // 35); w = rr.randint(1, 3)
        xs = (np.arange(L) + x) % px
        for k in range(w):
            lent[(y + k) % px, xs] = 1.0
    from PIL import ImageFilter
    lent = np.asarray(Image.fromarray((lent * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))) / 255.0
    dark, light = np.array(PARAM["bark"][0]), np.array(PARAM["bark"][1])
    col = dark[None, None, :] * (1 - n[..., None]) + light[None, None, :] * n[..., None]
    lich = periodic_noise(px, 6, SEED + 11) * periodic_noise(px, 24, SEED + 12)
    lm = np.clip((lich - 0.42) * 5, 0, 1)[..., None]
    col = col * (1 - 0.5 * lm) + np.array((120, 128, 100))[None, None, :] * 0.5 * lm
    col = col * (1 - lent[..., None] * 0.6) + np.array(PARAM["lent"])[None, None, :] * lent[..., None] * 0.6
    Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f"{NAME}_kura_color.png"))
    h = n * 0.7 + lent * 0.4
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5; gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    st = 8.0
    nx, ny, nz = -gx * st, gy * st, np.ones_like(h)
    ln = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    nm = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5
    Image.fromarray((nm * 255).astype(np.uint8)).save(os.path.join(OUT, f"{NAME}_kura_normal.png"))

bark_texture()

# ------------------------------------------------------------------ větve
TUBES = []      # (body, poloměry)
TIPS = []       # (bod, směr, úroveň)
def grow(p0, d0, length, r0, level, max_level):
    pts, rads = [Vector(p0)], [r0]
    d = Vector(d0).normalized()
    seg = 0.22 if level == 0 else (0.17 if level == 1 else 0.16)
    n = max(3, int(length / seg))
    p = Vector(p0)
    for i in range(1, n + 1):
        t = i / n
        # fototropismus nahoru + náhodné vlnění, konce se mírně sklánějí
        wob = Vector((noise.noise(Vector((p.x * 3, p.y * 3, i * 0.3 + level * 7))),
                      noise.noise(Vector((p.y * 3, i * 0.3, p.x * 3 + 5))), 0.0)) * 0.18
        d = (d + wob + Vector((0, 0, 0.06 if t < 0.6 else -PARAM["droop"] * 0.25 * t))).normalized()
        p = p + d * (length / n)
        pts.append(p.copy()); rads.append(r0 * (1 - 0.85 * t ** 0.9) + 0.0015)
    TUBES.append((pts, rads, level))
    TIPS.append((pts[-1], d.copy(), level))
    if level < max_level:
        nb = rng.randint(*PARAM["br"]) if level == 0 else rng.randint(1, 3)
        for k in range(nb):
            t = rng.uniform(0.2 if level == 0 else 0.25, 0.92)
            j = int(t * (len(pts) - 1))
            base = pts[j]; dir_par = (pts[min(j + 1, len(pts) - 1)] - pts[max(j - 1, 0)]).normalized()
            # boční směr: kolmice + rotace kolem rodiče
            side = dir_par.cross(Vector((0, 0, 1)))
            if side.length < 0.1: side = Vector((1, 0, 0))
            side = Quaternion(dir_par, rng.uniform(0, math.tau)) @ side.normalized()
            ang = rng.uniform(0.45, 0.9)
            nd = (dir_par * math.cos(ang) + side * math.sin(ang)).normalized()
            L = length * (1 - t) * rng.uniform(0.55, 0.95) + 0.15
            grow(base, nd, L, rads[j] * rng.uniform(0.5, 0.7), level + 1, max_level)
    return pts

nst = rng.randint(*PARAM["stems"])
for s in range(nst):
    a = rng.uniform(0, math.tau)
    rb = PARAM["spread"] * math.sqrt(rng.random())
    base = Vector((math.cos(a) * rb, math.sin(a) * rb, -0.08))
    lean = rng.uniform(*PARAM["lean"])
    d = Vector((math.cos(a) * math.sin(lean), math.sin(a) * math.sin(lean), math.cos(lean)))
    L = HEIGHT * rng.uniform(0.55, 0.92) / max(0.6, math.cos(lean))
    grow(base, d, L, rng.uniform(0.018, 0.04) * (HEIGHT / 3.2), 0, 2)

bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")
for pts, rads, level in TUBES:
    sides = 6 if level == 0 else (4 if level == 1 else 3)
    rings = []
    vacc = 0.0
    prev_n = None
    for i, (p, r) in enumerate(zip(pts, rads)):
        tng = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev_n is None:
            prev_n = tng.cross(Vector((0, 0, 1)) if abs(tng.z) < 0.9 else Vector((1, 0, 0))).normalized()
        nrm = (prev_n - tng * prev_n.dot(tng)).normalized(); prev_n = nrm
        bin_ = tng.cross(nrm)
        ring = []
        for k in range(sides):
            a = k / sides * math.tau
            ring.append(bm.verts.new(p + (nrm * math.cos(a) + bin_ * math.sin(a)) * r))
        rings.append((ring, vacc, r))
        if i < len(pts) - 1:
            vacc += (pts[i + 1] - p).length
    for (ra, va, r_a), (rb_, vb, r_b) in zip(rings[:-1], rings[1:]):
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((ra[k], ra[k2], rb_[k2], rb_[k]))
            uscale = max(1, round(2 * math.pi * r_a / 0.25 * 4)) / 4    # kůra 25 cm na dlaždici
            for lo, (uu, vv) in zip(f.loops, ((k / sides, va), (k2 / sides if k2 else 1.0, va),
                                              (k2 / sides if k2 else 1.0, vb), (k / sides, vb))):
                lo[uvl].uv = (uu * max(0.25, uscale), vv / 0.5)
    # uzavření špičky
    tip = bm.verts.new(pts[-1] + (pts[-1] - pts[-2]).normalized() * rads[-1])
    last = rings[-1][0]
    for k in range(sides):
        f = bm.faces.new((last[k], last[(k + 1) % sides], tip))
        for lo in f.loops: lo[uvl].uv = (k / sides, rings[-1][1] / 0.5)
me_b = bpy.data.meshes.new(f"{NAME}_vetve"); bm.to_mesh(me_b); bm.free()
for p in me_b.polygons: p.use_smooth = True
ob_b = bpy.data.objects.new(f"{NAME}_vetve", me_b); bpy.context.collection.objects.link(ob_b)

# ------------------------------------------------------------------ listové karty
cards = json.load(open(os.path.join(HERE, "atlas", f"{SPECIES}_cards.json")))["cards"]
clusters = [c for c in cards if c["kind"] == "cluster"]; singles = [c for c in cards if c["kind"] == "single"]
center = Vector((0, 0, HEIGHT * 0.55))
verts, faces, uvs, nrms = [], [], [], []
def add_card(base, up, size, card, outward):
    up = up.normalized()
    # rovina karty: natočená tak, aby byla vidět zvenku, s náhodným pootočením
    side = up.cross(Vector((0, 0, 1)))
    if side.length < 1e-3: side = up.cross(Vector((1, 0, 0)))
    side = (Quaternion(up, rng.uniform(-0.6, 0.6)) @ side.normalized())
    w = size * 0.5
    # karta trochu prohnutá (2 trojúhelníky na každé půlce = 4 trojúhelníky)
    fold = side.cross(up).normalized() * size * rng.uniform(0.03, 0.09)
    p = [base - side * w, base + side * w, base + side * w + up * size, base - side * w + up * size,
         base + up * size * 0.5 + fold, base + fold * 0.5, base + up * size + fold * 0.5]
    i0 = len(verts)
    verts.extend(p)
    u0, u1, v0, v1 = card["u0"], card["u1"], card["v0"], card["v1"]
    um = (u0 + u1) / 2
    uvs.extend([(u0, v0), (u1, v0), (u1, v1), (u0, v1), (um, (v0 + v1) / 2), (um, v0), (um, v1)])
    # normály karet směřují ven od středu keře (měkké stínování listí)
    for q in p:
        nrms.append(((q - center).normalized() + outward * 0.5).normalized())
    faces.extend([(i0 + 0, i0 + 5, i0 + 4), (i0 + 0, i0 + 4, i0 + 3), (i0 + 3, i0 + 4, i0 + 6),
                  (i0 + 5, i0 + 1, i0 + 4), (i0 + 1, i0 + 2, i0 + 4), (i0 + 4, i0 + 2, i0 + 6)])

ncards = 0
for pts, rads, level in TUBES:
    L = sum((b - a).length for a, b in zip(pts[:-1], pts[1:]))
    start = 0.22 if level == 0 else 0.1
    step = 0.16 / PARAM["dens"]
    acc = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        seg = (b - a).length
        acc += seg
        t = acc / L
        if t < start or rng.random() > (seg / step):
            continue
        p = b
        if p.z < 0.25:
            continue
        outward = (p - Vector((0, 0, p.z * 0.6))).normalized()
        rv = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))) * 0.35
        upv = ((b - a).normalized() * 0.5 + outward * rng.uniform(0.6, 1.1) + rv)
        upv.z *= 0.55
        upv.normalize()
        sz = rng.uniform(*PARAM["card"]) * (0.8 + 0.3 * t)
        add_card(p - upv * sz * 0.1, upv, sz, rng.choice(clusters), outward); ncards += 1
for p, d, level in TIPS:
    outward = (p - Vector((0, 0, p.z * 0.6))).normalized()
    sz = rng.uniform(*PARAM["card"])
    add_card(p - d * sz * 0.25, (d + Vector((0, 0, 0.2))).normalized(), sz, rng.choice(clusters), outward); ncards += 1
    if rng.random() < 0.5:
        add_card(p, (outward + Vector((0, 0, 0.5))).normalized(), sz * 0.45, rng.choice(singles), outward); ncards += 1

me_l = bpy.data.meshes.new(f"{NAME}_listi")
me_l.from_pydata([tuple(v) for v in verts], [], faces)
uvl2 = me_l.uv_layers.new(name="UVMap")
for poly in me_l.polygons:
    for li in poly.loop_indices:
        uvl2.data[li].uv = uvs[me_l.loops[li].vertex_index]
me_l.update()
for p in me_l.polygons: p.use_smooth = True
# vlastní normály karet vypnuty – na oboustranných kartách tmavly rubové strany
ob_l = bpy.data.objects.new(f"{NAME}_listi", me_l); bpy.context.collection.objects.link(ob_l)

# ------------------------------------------------------------------ materiály (jen obrázky)
def img(path, color=True):
    im = bpy.data.images.load(path); im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    return im

def bark_mat():
    m = bpy.data.materials.new(f"game_{NAME}_kura"); m.use_nodes = True
    m.use_backface_culling = True
    t = m.node_tree; t.nodes.clear()
    o = t.nodes.new("ShaderNodeOutputMaterial"); b = t.nodes.new("ShaderNodeBsdfPrincipled")
    t.links.new(b.outputs[0], o.inputs[0])
    c = t.nodes.new("ShaderNodeTexImage"); c.image = img(os.path.join(OUT, f"{NAME}_kura_color.png"))
    n = t.nodes.new("ShaderNodeTexImage"); n.image = img(os.path.join(OUT, f"{NAME}_kura_normal.png"), False)
    nm = t.nodes.new("ShaderNodeNormalMap")
    t.links.new(c.outputs[0], b.inputs["Base Color"]); t.links.new(n.outputs[0], nm.inputs["Color"])
    t.links.new(nm.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.8
    return m

def leaf_mat():
    m = bpy.data.materials.new(f"game_{NAME}_listi"); m.use_nodes = True
    m.use_backface_culling = False
    try:
        m.blend_method = 'CLIP'
    except Exception:
        pass
    t = m.node_tree; t.nodes.clear()
    o = t.nodes.new("ShaderNodeOutputMaterial"); b = t.nodes.new("ShaderNodeBsdfPrincipled")
    t.links.new(b.outputs[0], o.inputs[0])
    c = t.nodes.new("ShaderNodeTexImage"); c.image = img(os.path.join(HERE, "atlas", f"{SPECIES}_color.png"))
    c.image.alpha_mode = 'STRAIGHT'
    n = t.nodes.new("ShaderNodeTexImage"); n.image = img(os.path.join(HERE, "atlas", f"{SPECIES}_normal.png"), False)
    nm = t.nodes.new("ShaderNodeNormalMap")
    t.links.new(c.outputs["Color"], b.inputs["Base Color"])
    rnd = t.nodes.new("ShaderNodeMath"); rnd.operation = 'ROUND'      # glTF exportér -> alphaMode MASK
    t.links.new(c.outputs["Alpha"], rnd.inputs[0]); t.links.new(rnd.outputs[0], b.inputs["Alpha"])
    t.links.new(n.outputs[0], nm.inputs["Color"]); t.links.new(nm.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.6
    return m

ob_b.data.materials.append(bark_mat()); ob_l.data.materials.append(leaf_mat())

tris_b = sum(len(p.vertices) - 2 for p in me_b.polygons); tris_l = sum(len(p.vertices) - 2 for p in me_l.polygons)
print(f"BUSH {NAME} vetve={tris_b} listi={tris_l} karet={ncards}")

def export(objs, path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=True, export_image_format='AUTO',
                              export_cameras=False, export_lights=False, export_animations=False)

# spojit do jednoho objektu se dvěma materiály
bpy.ops.object.select_all(action='DESELECT')
ob_b.select_set(True); ob_l.select_set(True); bpy.context.view_layer.objects.active = ob_b
bpy.ops.object.join(); bush = bpy.context.active_object; bush.name = NAME
d = bush.dimensions
export([bush], os.path.join(OUT, f"{NAME}.glb"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{NAME}.blend"))
print(f"RESULT {NAME} tris={tris_b + tris_l} dims_m(sxvxh)={d.x:.2f} x {d.z:.2f} x {d.y:.2f}")
