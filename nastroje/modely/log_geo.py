"""Pařezy a padlé kmeny: kůra, letokruhy na řezu, praskliny, mech, choroš.
Spuštění: python3 log_geo.py <seed> <výstup.blend> <parez|kmen> [průměr_m] [délka_m]
Atributy pro materiál: lp (osa X = podél vláken), bark (1 = kůra), rad (poměr poloměru), fung (choroš)
"""
import sys, math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, noise

SEED = int(sys.argv[1]); OUT = sys.argv[2]; KIND = sys.argv[3]
DIAM = float(sys.argv[4]) if len(sys.argv) > 4 else (0.6 if KIND == "parez" else 0.45)
LEN = float(sys.argv[5]) if len(sys.argv) > 5 else (0.55 if KIND == "parez" else 4.5)
rng = random.Random(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)
R0 = DIAM / 2
NA = 36                                   # dílků po obvodu
NL = 10 if KIND == "parez" else 22        # dílků po délce

def radius(t, a):
    """Poloměr v místě t (0..1 po délce) a úhlu a."""
    r = R0 * (1 + 0.06 * noise.noise(Vector((math.cos(a) * 1.5, math.sin(a) * 1.5, t * 3 + SEED))))
    r *= 1 + 0.025 * math.sin(a * 7 + SEED)                    # žebra kmene
    if KIND == "parez":
        # kořenové náběhy u země (t=0 dole)
        flare = 0.0
        for k in range(5):
            ak = k * math.tau / 5 + SEED
            d = math.atan2(math.sin(a - ak), math.cos(a - ak))
            flare += math.exp(-(d / 0.35) ** 2)
        r *= 1 + (0.55 * flare + 0.18) * max(0.0, 1 - t / 0.45) ** 2
    else:
        r *= 1 - 0.18 * t                                       # kmen se zužuje
    return r

bm = bmesh.new()
lp_l = bm.verts.layers.float_vector.new("lp")
bark_l = bm.verts.layers.float.new("bark")
rad_l = bm.verts.layers.float.new("rad")
fung_l = bm.verts.layers.float.new("fung")
rings = []
for i in range(NL + 1):
    t = i / NL
    ring = []
    for j in range(NA):
        a = j / NA * math.tau
        r = radius(t, a)
        x = t * LEN
        if KIND == "parez":
            pos = Vector((r * math.cos(a), r * math.sin(a), x - 0.12))
            lpv = Vector((x, r * math.cos(a), r * math.sin(a)))
        else:
            sag = 0.03 * math.sin(math.pi * t) + 0.12 * R0 * math.sin(t * 2.2 + SEED)
            yb = 0.08 * LEN * 0.1 * math.sin(t * 2.7 + SEED * 0.7)
            pos = Vector((x - LEN / 2, r * math.cos(a) + yb, r * math.sin(a) + R0 * 0.82 - sag))
            lpv = Vector((x, r * math.cos(a), r * math.sin(a)))
        v = bm.verts.new(pos); v[lp_l] = lpv; v[bark_l] = 1.0; v[rad_l] = 1.0
        ring.append(v)
    rings.append(ring)
for i in range(NL):
    for j in range(NA):
        j2 = (j + 1) % NA
        bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))

def cap(ring, end_t, top):
    """Řezná plocha: okraj kůry (lem), uvnitř dřevo s letokruhy. U pařezu šikmý řez sekerou."""
    c = sum((v.co for v in ring), Vector()) / len(ring)
    inner_prev = ring
    layers = [(0.93, 0.0), (0.6, 0.0), (0.3, 0.0)]
    vs_all = []
    for k, (f, _) in enumerate(layers):
        nr = []
        for j, v in enumerate(ring):
            p = c + (v.co - c) * f
            if KIND == "parez":
                # řez sekerou: dva šikmé zásahy -> hřbet uprostřed, střed vylomený
                d = (v.co - c); ang = math.atan2(d.y, d.x)
                p.z += 0.05 * abs(math.cos(ang)) * (1 - f) - 0.02 * f
            nv = bm.verts.new(p)
            lpo = v[lp_l]
            nv[lp_l] = Vector((lpo.x, lpo.y * f, lpo.z * f)); nv[bark_l] = 0.0 if k > 0 else 0.5; nv[rad_l] = f
            nr.append(nv)
        for j in range(len(ring)):
            j2 = (j + 1) % len(ring)
            if top:
                bm.faces.new((inner_prev[j], inner_prev[j2], nr[j2], nr[j]))
            else:
                bm.faces.new((inner_prev[j2], inner_prev[j], nr[j], nr[j2]))
        inner_prev = nr
    cv = bm.verts.new(c + Vector((0, 0, 0.03 if KIND == "parez" else 0)))
    cv[lp_l] = Vector((ring[0][lp_l].x, 0, 0)); cv[bark_l] = 0.0; cv[rad_l] = 0.0
    for j in range(len(ring)):
        j2 = (j + 1) % len(ring)
        if top: bm.faces.new((inner_prev[j], inner_prev[j2], cv))
        else: bm.faces.new((inner_prev[j2], inner_prev[j], cv))

cap(rings[-1], 1.0, True)
if KIND == "kmen":
    cap(rings[0], 0.0, False)
    # zlomený konec: několik ostrých třísek
    for k in range(5):
        a = rng.uniform(0, math.tau); r = R0 * rng.uniform(0.2, 0.7)
        base = Vector((-LEN / 2 - 0.005, r * math.cos(a), r * math.sin(a) + R0 * 0.82))
        L = rng.uniform(0.08, 0.25); w = rng.uniform(0.02, 0.05)
        vs = [bm.verts.new(base + Vector((0, -w, -w * 0.5))), bm.verts.new(base + Vector((0, w, -w * 0.5))),
              bm.verts.new(base + Vector((0, 0, w))), bm.verts.new(base + Vector((-L, rng.uniform(-0.02, 0.02), 0)))]
        for v in vs:
            v[lp_l] = Vector((0, (v.co.y), (v.co.z - R0 * 0.82))); v[bark_l] = 0.0; v[rad_l] = 0.5
        for f in ((0, 1, 3), (1, 2, 3), (2, 0, 3)):
            bm.faces.new([vs[i] for i in f])
else:
    # spodek pařezu zakrytý zemí – uzavřít
    cbot = sum((v.co for v in rings[0]), Vector()) / NA
    cb = bm.verts.new(cbot); cb[lp_l] = Vector((0, 0, 0)); cb[bark_l] = 1.0; cb[rad_l] = 0.0
    for j in range(NA):
        bm.faces.new((rings[0][(j + 1) % NA], rings[0][j], cb))

# pahýly ulomených větví (jen kmen)
if KIND == "kmen":
    for k in range(rng.randint(3, 6)):
        i = rng.randint(3, NL - 2); j = rng.randrange(NA)
        v = rings[i][j]
        cen = sum((q.co for q in rings[i]), Vector()) / NA
        out = (v.co - cen).normalized()
        if out.z < -0.3:
            continue
        dirb = (out + Vector((rng.uniform(0.2, 0.6), 0, 0))).normalized()
        L = rng.uniform(0.08, 0.35); rb = R0 * rng.uniform(0.12, 0.25)
        side = dirb.cross(Vector((0, 0, 1)))
        if side.length < 0.1: side = dirb.cross(Vector((1, 0, 0)))
        side.normalize(); up2 = dirb.cross(side)
        base_ring, tip_ring = [], []
        for q in range(7):
            a = q / 7 * math.tau
            off = (side * math.cos(a) + up2 * math.sin(a))
            bv = bm.verts.new(v.co - out * 0.02 + off * rb * 1.3); tv = bm.verts.new(v.co + dirb * L + off * rb * rng.uniform(0.7, 1.0))
            for vv, xx in ((bv, 0.0), (tv, L)):
                vv[lp_l] = Vector((xx, math.cos(a) * rb, math.sin(a) * rb)); vv[bark_l] = 1.0; vv[rad_l] = 1.0
            base_ring.append(bv); tip_ring.append(tv)
        for q in range(7):
            q2 = (q + 1) % 7
            bm.faces.new((base_ring[q], base_ring[q2], tip_ring[q2], tip_ring[q]))
        tc = bm.verts.new(v.co + dirb * (L + 0.01)); tc[lp_l] = Vector((L, 0, 0)); tc[bark_l] = 0.0; tc[rad_l] = 0.0
        for q in range(7):
            f = bm.faces.new((tip_ring[q], tip_ring[(q + 1) % 7], tc))

# choroš (troudnatec) – 2–4 polokruhové plodnice na boku
for k in range(rng.randint(2, 4) if rng.random() < 0.8 else 0):
    for _try in range(30):
        i = rng.randint(2, NL - 2); j = rng.randrange(NA)
        v = rings[i][j]
        out = (v.co - (sum((q.co for q in rings[i]), Vector()) / NA)).normalized()
        if out.z > -0.1 and abs(out.z) < 0.8:
            break
    up = Vector((0, 0, 1))
    side = out.cross(up).normalized() if abs(out.z) < 0.9 else Vector((1, 0, 0))
    rr_ = rng.uniform(0.05, 0.12)
    n = 10
    top_vs, bot_vs = [], []
    for q in range(n + 1):
        a = math.pi * q / n
        p = v.co + side * math.cos(a) * rr_ + out * math.sin(a) * rr_ * 0.9
        tv = bm.verts.new(p + up * rr_ * 0.45 * math.sin(a)); bv = bm.verts.new(p - up * rr_ * 0.2)
        for vv in (tv, bv):
            vv[lp_l] = Vector((math.cos(a), math.sin(a), 0)); vv[bark_l] = 0.0; vv[rad_l] = 0.0; vv[fung_l] = 1.0
        top_vs.append(tv); bot_vs.append(bv)
    hub_t = bm.verts.new(v.co + up * rr_ * 0.15); hub_b = bm.verts.new(v.co - up * rr_ * 0.15)
    for vv in (hub_t, hub_b):
        vv[lp_l] = Vector((0, 0, 0)); vv[fung_l] = 1.0
    for q in range(n):
        bm.faces.new((top_vs[q], top_vs[q + 1], hub_t))
        bm.faces.new((bot_vs[q + 1], bot_vs[q], hub_b))
        bm.faces.new((top_vs[q + 1], top_vs[q], bot_vs[q], bot_vs[q + 1]))

bm.normal_update()
me = bpy.data.meshes.new("log"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("wagon", me)          # jméno 'wagon' kvůli sdílenému render/bake skriptu
bpy.context.collection.objects.link(ob)
for p in me.polygons: p.use_smooth = True
# UV: chytrá projekce + zabalení
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.004)
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
# pivot dole uprostřed
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
barkv = np.empty(len(me.vertices)); me.attributes["bark"].data.foreach_get("value", barkv)
zbase = co[barkv > 0.9, 2].min() if KIND == "kmen" else co[:, 2].min()
co[:, 2] -= zbase + (0.03 if KIND == "kmen" else 0.0)
co[:, 0] -= (co[:, 0].max() + co[:, 0].min()) / 2; co[:, 1] -= (co[:, 1].max() + co[:, 1].min()) / 2
me.vertices.foreach_set("co", co.ravel()); me.update()
ob["kind"] = "log"
print("LOG tris", sum(len(p.vertices) - 2 for p in me.polygons), "dims", tuple(round(x, 2) for x in ob.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
