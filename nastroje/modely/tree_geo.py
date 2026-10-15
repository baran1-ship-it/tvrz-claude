"""Listnatý strom: kmen a větve jako geometrie s kůrou, koruna z listových karet atlasu.
Spuštění: python3 tree_geo.py <druh> <seed> <název> <mlady|stredni|stary>
"""
import sys, os, math, json, random
import numpy as np
import bpy
from mathutils import Vector, Quaternion, noise
from PIL import Image, ImageFilter

SPECIES, SEED, NAME, AGE = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
rng = random.Random(SEED); np.random.seed(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)

SP = {   # kůra (tmavá, světlá sRGB), brázdy (0 = hladká), tvar koruny
    "dub":   dict(bark=((52, 46, 40), (118, 108, 96)), furrow=1.0, spread=1.0, droop=0.0, apical=0.35),
    "lipa":  dict(bark=((58, 52, 46), (120, 112, 100)), furrow=0.6, spread=0.8, droop=0.1, apical=0.55),
    "buk":   dict(bark=((92, 92, 88), (150, 150, 144)), furrow=0.0, spread=0.75, droop=0.05, apical=0.6),
    "briza": dict(bark=((210, 206, 196), (240, 236, 226)), furrow=0.0, spread=0.55, droop=0.35, apical=0.7, birch=True),
    "smrk":  dict(bark=((62, 48, 40), (122, 96, 80)), furrow=0.25, spread=1.0, droop=0.45, apical=1.0, conifer="smrk"),
    "borovice": dict(bark=((84, 56, 40), (168, 112, 74)), furrow=0.8, spread=1.0, droop=0.0, apical=1.0, conifer="borovice"),
}[SPECIES]
AG = {   # výška, průměr kmene u země, výška nasazení koruny, karty
    "mlady":   dict(h=(5.0, 7.0), d=0.15, crown0=0.3, card=(0.8, 1.05), lv=2, nb=(8, 11)),
    "stredni": dict(h=(10.0, 14.0), d=0.5, crown0=0.27, card=(1.0, 1.4), lv=3, nb=(8, 11)),
    "stary":   dict(h=(15.0, 20.0), d=0.95, crown0=0.2, card=(1.2, 1.7), lv=3, nb=(9, 12)),
}[AGE]
if SPECIES == "briza":
    AG = dict(AG); AG["d"] *= 0.7

# ------------------------------------------------------------------ kůra (opakovatelná)
def pnoise(n, cx, cy, seed):
    r = np.random.RandomState(seed); g = r.rand(cy, cx)
    ty = np.arange(n) / n * cy; tx = np.arange(n) / n * cx
    iy, ix = ty.astype(int), tx.astype(int); fy, fx = ty - iy, tx - ix
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    iy1, ix1 = (iy + 1) % cy, (ix + 1) % cx
    a = g[iy][:, ix]; b = g[iy][:, ix1]; c = g[iy1][:, ix]; d = g[iy1][:, ix1]
    top = a + (b - a) * fx[None, :]; bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]

def bark(px=1024):
    # řádky = podél kmene (V), sloupce = obvod (U)
    n = sum(pnoise(px, 4 * 2 ** o, 2 * 2 ** o, SEED + o) * 0.55 ** o for o in range(5)) / 2.0
    fur = pnoise(px, 24, 3, SEED + 50) * 0.7 + pnoise(px, 48, 6, SEED + 51) * 0.3   # podélné brázdy
    ridges = np.clip((fur - 0.42) * 4, 0, 1) if SP["furrow"] > 0 else np.ones_like(fur)
    crossb = np.clip((pnoise(px, 10, 30, SEED + 52) - 0.3) * 3, 0, 1)
    ridges = ridges * (0.6 + 0.4 * crossb) if SP["furrow"] > 0 else ridges
    dark, light = np.array(SP["bark"][0]), np.array(SP["bark"][1])
    t = np.clip(n * 0.5 + ridges * 0.5 * SP["furrow"] + (1 - SP["furrow"]) * n * 0.5, 0, 1)
    col = dark[None, None, :] * (1 - t[..., None]) + light[None, None, :] * t[..., None]
    if SP.get("birch"):
        # vodorovné tmavé čočky a černé praskliny březové kůry
        lent = np.zeros((px, px)); rr = np.random.RandomState(SEED + 9)
        for _ in range(int(px * 0.6)):
            y, x = rr.randint(0, px), rr.randint(0, px); L = rr.randint(px // 40, px // 12)
            lent[y:y + rr.randint(1, 4), :][:, (np.arange(L) + x) % px] = 1
        lent = np.asarray(Image.fromarray((lent * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))) / 255
        blk = np.clip((pnoise(px, 8, 16, SEED + 60) - 0.62) * 6, 0, 1)
        col = col * (1 - lent[..., None] * 0.7) + np.array((40, 36, 34))[None, None, :] * lent[..., None] * 0.7
        col = col * (1 - blk[..., None]) + np.array((30, 28, 26))[None, None, :] * blk[..., None]
        ridges = 1 - blk * 0.8
    lich = np.clip((pnoise(px, 6, 6, SEED + 70) * pnoise(px, 20, 20, SEED + 71) - 0.36) * 5, 0, 1)
    col = col * (1 - 0.45 * lich[..., None]) + np.array((122, 132, 104))[None, None, :] * 0.45 * lich[..., None]
    Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f"{NAME}_kura_color.png"))
    h = n * 0.4 + ridges * 0.8
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5; gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    st = 10.0 if SP["furrow"] else 5.0
    nx, ny, nz = -gx * st, gy * st, np.ones_like(h); ln = np.sqrt(nx ** 2 + ny ** 2 + 1)
    Image.fromarray(((np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5) * 255).astype(np.uint8)).save(
        os.path.join(OUT, f"{NAME}_kura_normal.png"))
bark()

# ------------------------------------------------------------------ kostra
H = rng.uniform(*AG["h"])
TUBES, TIPS = [], []
def grow(p0, d0, length, r0, level, maxl):
    pts, rads = [Vector(p0)], [r0]
    d = Vector(d0).normalized(); p = Vector(p0)
    seg = max(0.25, length / (14 if level == 0 else (8 if level == 1 else 5)))
    n = max(3, int(length / seg))
    for i in range(1, n + 1):
        t = i / n
        wob = Vector((noise.noise(Vector((p.x * 0.7, p.y * 0.7, i * 0.4 + level * 11 + SEED))),
                      noise.noise(Vector((p.y * 0.7, i * 0.4 + SEED, p.x * 0.7 + 5))), 0)) * (0.12 if level == 0 else 0.3)
        grav = -SP["droop"] * 0.35 * t if level > 0 else 0.0
        d = (d + wob + Vector((0, 0, 0.05 * (1 - t) + grav))).normalized()
        p = p + d * (length / n)
        pts.append(p.copy())
        rads.append(r0 * (1 - 0.8 * t ** 0.85) + 0.004)
    TUBES.append((pts, rads, level)); TIPS.append((pts[-1], d.copy(), level))
    if level == 0 and SP.get("conifer") == "borovice":
        # borovice: málo silných větví v horní třetině, šikmo vzhůru, na koncích husté chomáče
        c0 = {"mlady": 0.35, "stredni": 0.5, "stary": 0.6}[AGE]
        nl = {"mlady": (8, 11), "stredni": (9, 12), "stary": (10, 13)}[AGE]
        n = rng.randint(*nl)
        for k in range(n):
            t = c0 + (0.97 - c0) * (k + rng.uniform(0.1, 0.9)) / n
            u_ = (t - c0) / (1 - c0)
            j = int(t * (len(pts) - 1)); base = pts[j]
            a = k * 2.39996 + rng.uniform(-0.5, 0.5)
            el = rng.uniform(0.35, 0.75) + 0.25 * u_
            L = H * rng.uniform(0.17, 0.27) * (1 - 0.45 * u_) + 0.6
            nd = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
            grow(base, nd, L, max(0.02, rads[j] * 0.55), 1, maxl)
        return pts
    if level == 0 and SP.get("conifer"):
        sm = SP["conifer"] == "smrk"
        c0 = 0.06 if sm else 0.55
        dz = (0.6 if sm else 0.8) * (1.3 if AGE == "stary" else 1.0)
        z = c0 * length
        wi = 0
        while z < length * 0.97:
            t = z / length
            j = int(t * (len(pts) - 1)); base = pts[j]
            nwh = rng.randint(4, 5) if sm else rng.randint(3, 5)
            a0 = rng.uniform(0, math.tau)
            for k in range(nwh):
                a = a0 + k * math.tau / nwh + rng.uniform(-0.3, 0.3)
                if sm:
                    L = (1 - t) / (1 - c0) * H * 0.3 + 0.35
                    el = rng.uniform(-0.15, 0.1)
                else:
                    u_ = (t - c0) / (1 - c0)
                    L = H * 0.2 * (1 - 0.45 * u_) + 0.8
                    el = 0.15 + 0.35 * u_ + rng.uniform(-0.1, 0.1)
                nd = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
                grow(base, nd, L * rng.uniform(0.85, 1.1), max(0.012, rads[j] * (0.32 if sm else 0.4)), 1, maxl)
            z += dz * rng.uniform(0.85, 1.15); wi += 1
        return pts
    if level < maxl:
        nb = rng.randint(*AG["nb"]) if level == 0 else rng.randint(*((5, 9), (4, 7), (2, 4))[min(level - 1, 2)])
        if SP.get("conifer"): nb = (rng.randint(3, 6) if SP["conifer"] == "smrk" else rng.randint(6, 10)) if level == 1 else (rng.randint(3, 5) if SP["conifer"] == "borovice" and level == 2 else 0)
        t0 = AG["crown0"] if level == 0 else (0.45 if SP.get("conifer") == "borovice" else 0.2)
        for k in range(nb):
            t = t0 + (0.95 - t0) * (k + rng.uniform(0.2, 0.8)) / nb
            j = int(t * (len(pts) - 1))
            dp = (pts[min(j + 1, len(pts) - 1)] - pts[max(j - 1, 0)]).normalized()
            side = dp.cross(Vector((0, 0, 1)))
            if side.length < 0.1: side = Vector((1, 0, 0))
            side = Quaternion(dp, k * 2.39996 + rng.uniform(-0.4, 0.4)) @ side.normalized()   # fylotaxe
            ang = rng.uniform(0.6, 1.05) * SP["spread"] + (0.15 if level == 0 else 0.0)
            nd = (dp * math.cos(ang) + side * math.sin(ang)).normalized()
            L = length * (1 - t) * rng.uniform(0.6, 0.95) * (1.0 if level == 0 else 0.8)
            if level == 0:
                L = max(L * 1.3, H * 0.22) * (1.0 - SP["apical"] * (t - t0))
            grow(pts[j], nd, L + 0.2, rads[j] * rng.uniform(0.45, 0.65), level + 1, maxl)
    return pts

lean = rng.uniform(0, 0.06); la = rng.uniform(0, math.tau)
grow(Vector((0, 0, -0.15)), Vector((math.cos(la) * lean, math.sin(la) * lean, 1)), H, AG["d"] / 2, 0, AG["lv"])

# ------------------------------------------------------------------ síť větví
import bmesh
bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
for pts, rads, level in TUBES:
    sides = (12 if AG["d"] > 0.5 else 9) if level == 0 else ((4 if SP.get("conifer") else 6) if level == 1 else (3 if SP.get("conifer") else (4 if level == 2 else 3)))
    rings = []; vacc = 0.0; prev_n = None
    for i, (p, r) in enumerate(zip(pts, rads)):
        tng = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev_n is None:
            prev_n = tng.cross(Vector((0, 0, 1)) if abs(tng.z) < 0.9 else Vector((1, 0, 0))).normalized()
        nrm = (prev_n - tng * prev_n.dot(tng)).normalized(); prev_n = nrm; bn = tng.cross(nrm)
        ring = []
        for k in range(sides):
            a = k / sides * math.tau
            rr = r
            if level == 0 and i <= 2:          # kořenové náběhy
                rr *= 1 + (0.5 - 0.2 * i) * max(0.0, math.cos(a * 5 + SEED)) ** 3 + (0.15 if i == 0 else 0)
            ring.append(bm.verts.new(p + (nrm * math.cos(a) + bn * math.sin(a)) * rr))
        rings.append((ring, vacc, r))
        if i < len(pts) - 1: vacc += (pts[i + 1] - p).length
    for (ra, va, r_a), (rb, vb, _) in zip(rings[:-1], rings[1:]):
        us = max(1, round(2 * math.pi * r_a / 0.6))
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((ra[k], ra[k2], rb[k2], rb[k]))
            for lo, (uu, vv) in zip(f.loops, ((k / sides, va), ((k + 1) / sides, va), ((k + 1) / sides, vb), (k / sides, vb))):
                lo[uvl].uv = (uu * us, vv / 1.2)
me_b = bpy.data.meshes.new("vetve"); bm.to_mesh(me_b); bm.free()
for p in me_b.polygons: p.use_smooth = True
ob_b = bpy.data.objects.new(f"{NAME}_vetve", me_b); bpy.context.collection.objects.link(ob_b)

# ------------------------------------------------------------------ listové karty
cards = json.load(open(os.path.join(HERE, "atlas", f"{SPECIES}T_cards.json")))["cards"]
cl = [c for c in cards if c["kind"] == "cluster"]
verts, faces, uvs = [], [], []
def add_card(base, up, size, card, outward):
    up = up.normalized()
    side = up.cross(Vector((0, 0, 1)))
    if side.length < 1e-3: side = up.cross(Vector((1, 0, 0)))
    side = Quaternion(up, rng.uniform(-0.7, 0.7)) @ side.normalized()
    w = size * 0.5; fold = side.cross(up).normalized() * size * rng.uniform(0.04, 0.1)
    p = [base - side * w, base + side * w, base + side * w + up * size, base - side * w + up * size,
         base + up * size * 0.5 + fold, base + fold * 0.5, base + up * size + fold * 0.5]
    i0 = len(verts); verts.extend(p)
    u0, u1, v0, v1 = card["u0"], card["u1"], card["v0"], card["v1"]; um = (u0 + u1) / 2
    uvs.extend([(u0, v0), (u1, v0), (u1, v1), (u0, v1), (um, (v0 + v1) / 2), (um, v0), (um, v1)])
    faces.extend([(i0, i0 + 5, i0 + 4), (i0, i0 + 4, i0 + 3), (i0 + 3, i0 + 4, i0 + 6),
                  (i0 + 5, i0 + 1, i0 + 4), (i0 + 1, i0 + 2, i0 + 4), (i0 + 4, i0 + 2, i0 + 6)])
crown_c = Vector((0, 0, H * 0.65))
for pts, rads, level in TUBES:
    if level == 0 and SP.get("conifer") == "borovice":
        # jehličí podél vrcholové části kmene, aby koruna neměla díru
        n_top = int(H * 0.8)
        for q in range(n_top):
            zt = H * (0.62 + 0.36 * q / n_top)
            j = min(len(pts) - 1, int(zt / H * (len(pts) - 1)))
            a_ = rng.uniform(0, math.tau)
            ow = Vector((math.cos(a_), math.sin(a_), 0))
            add_card(pts[j] + ow * 0.2, (ow + Vector((0, 0, 0.6))).normalized(), rng.uniform(*AG["card"]), rng.choice(cl), ow)
        continue
    if level < (1 if SP.get("conifer") else AG["lv"] - 1):
        continue
    L = sum((b - a).length for a, b in zip(pts[:-1], pts[1:]))
    step = AG["card"][0] * (0.12 if SP.get("conifer") == "borovice" else 0.2)
    acc = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        acc += (b - a).length
        if acc / L < (((0.5 if level == 1 else 0.1) if SP.get("conifer") == "borovice" else 0.15) if (level >= AG["lv"] or SP.get("conifer")) else 0.4) or rng.random() > (b - a).length / step:
            continue
        outward = (b - Vector((0, 0, b.z))).normalized() if (b.xy.length > 0.1) else Vector((1, 0, 0))
        rv = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))) * 0.4
        upv = (b - a).normalized() * 0.6 + outward * 0.8 + rv; upv.z *= (0.25 if SP.get("conifer") == "smrk" else (0.35 if SP.get("conifer") == "borovice" else 0.6))
        sz = rng.uniform(*AG["card"])
        add_card(b - upv.normalized() * sz * 0.15, upv, sz, rng.choice(cl), outward)
for p, d, level in TIPS:
    if level == 0 and SP.get("conifer"):        # vrcholový chomáč
        for q in range(6):
            add_card(p - Vector((0, 0, 0.5 + q * 0.15)), Vector((math.cos(q * 1.05), math.sin(q * 1.05), 0.8)), rng.uniform(*AG["card"]), rng.choice(cl), Vector((math.cos(q * 1.05), math.sin(q * 1.05), 0)))
    if level >= (1 if SP.get("conifer") else AG["lv"] - 1):
        outward = (p - Vector((0, 0, p.z))).normalized() if p.xy.length > 0.1 else Vector((1, 0, 0))
        add_card(p - d * 0.2, (d + Vector((0, 0, 0.25))).normalized(), rng.uniform(*AG["card"]), rng.choice(cl), outward)
me_l = bpy.data.meshes.new("listi"); me_l.from_pydata([tuple(v) for v in verts], [], faces)
uv2 = me_l.uv_layers.new(name="UVMap")
for poly in me_l.polygons:
    for li in poly.loop_indices: uv2.data[li].uv = uvs[me_l.loops[li].vertex_index]
for p in me_l.polygons: p.use_smooth = True
ob_l = bpy.data.objects.new(f"{NAME}_listi", me_l); bpy.context.collection.objects.link(ob_l)

# ------------------------------------------------------------------ materiály
def img(p, color=True):
    im = bpy.data.images.load(p); im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; return im
mb = bpy.data.materials.new(f"game_{NAME}_kura"); mb.use_nodes = True; mb.use_backface_culling = True
t = mb.node_tree; b = t.nodes["Principled BSDF"]
c = t.nodes.new("ShaderNodeTexImage"); c.image = img(os.path.join(OUT, f"{NAME}_kura_color.png"))
n_ = t.nodes.new("ShaderNodeTexImage"); n_.image = img(os.path.join(OUT, f"{NAME}_kura_normal.png"), False)
nm = t.nodes.new("ShaderNodeNormalMap"); t.links.new(c.outputs[0], b.inputs["Base Color"])
t.links.new(n_.outputs[0], nm.inputs["Color"]); t.links.new(nm.outputs[0], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.85
ml = bpy.data.materials.new(f"game_{NAME}_listi"); ml.use_nodes = True; ml.use_backface_culling = False
t = ml.node_tree; b = t.nodes["Principled BSDF"]
c = t.nodes.new("ShaderNodeTexImage"); c.image = img(os.path.join(HERE, "atlas", f"{SPECIES}T_color.png"))
n_ = t.nodes.new("ShaderNodeTexImage"); n_.image = img(os.path.join(HERE, "atlas", f"{SPECIES}T_normal.png"), False)
nm = t.nodes.new("ShaderNodeNormalMap"); t.links.new(c.outputs["Color"], b.inputs["Base Color"])
r = t.nodes.new("ShaderNodeMath"); r.operation = 'ROUND'
t.links.new(c.outputs["Alpha"], r.inputs[0]); t.links.new(r.outputs[0], b.inputs["Alpha"])
t.links.new(n_.outputs[0], nm.inputs["Color"]); t.links.new(nm.outputs[0], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.6
ob_b.data.materials.append(mb); ob_l.data.materials.append(ml)
tb = sum(len(p.vertices) - 2 for p in me_b.polygons); tl = sum(len(p.vertices) - 2 for p in me_l.polygons)
bpy.ops.object.select_all(action='DESELECT'); ob_b.select_set(True); ob_l.select_set(True)
bpy.context.view_layer.objects.active = ob_b; bpy.ops.object.join(); tree = bpy.context.active_object; tree.name = NAME
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"{NAME}.glb"), export_format='GLB', use_selection=True,
                          export_yup=True, export_apply=True, export_cameras=False, export_lights=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{NAME}.blend"))
d = tree.dimensions
print(f"RESULT {NAME} tris={tb + tl} (vetve {tb}, listi {tl}) dims_m(sxvxh)={d.x:.2f} x {d.z:.2f} x {d.y:.2f}")
