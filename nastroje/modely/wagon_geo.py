"""Žebřiňák – čtyřkolový selský vůz, Čechy kolem r. 1400.
Každý kus dřeva je samostatný díl s vlastní kresbou, stářím a opotřebením.
Spuštění: python3 wagon_geo.py <seed> <výstup.blend> [plachta 0/1]
Osy Blenderu: X = šířka, -Y = předek (oj), Z = nahoru. Export do glTF -> předek míří na +Z.
"""
import sys, math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, noise
from mathutils.kdtree import KDTree

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 3
OUT = sys.argv[2] if len(sys.argv) > 2 else "wagon_hi.blend"
COVER = int(sys.argv[3]) if len(sys.argv) > 3 else 0
rng = random.Random(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)

# ------------------------------------------------------------------ barvy dřev
# (světlé dřevo / tmavá léta) – lineární RGB
WOOD = {
    "dub":    ((0.27, 0.170, 0.095), (0.110, 0.066, 0.036)),
    "jasan":  ((0.36, 0.260, 0.160), (0.170, 0.110, 0.062)),
    "jilm":   ((0.25, 0.150, 0.085), (0.100, 0.058, 0.032)),
    "smrk":   ((0.40, 0.290, 0.170), (0.200, 0.125, 0.065)),
    "buk":    ((0.33, 0.215, 0.135), (0.160, 0.095, 0.058)),
}

PIECES = []          # (objekt) – na konci se spojí
PID = [0]

def jitter(c, amt):
    return tuple(max(0.0, x * (1 + rng.uniform(-amt, amt))) for x in c)

def new_piece_bm():
    bm = bmesh.new()
    for n in ("pid", "age", "metal", "wheel", "handled", "fresh"):
        bm.verts.layers.float.new(n)
    for n in ("lp", "wl", "wd"):
        bm.verts.layers.float_vector.new(n)
    return bm

def box_bm(L, w, h, nseg=6, bevel=0.006, rough=0.002):
    """Kvádr podél lokální osy X od 0 do L, průřez w (Y) × h (Z), středěný v YZ."""
    bm = new_piece_bm()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((v.co.x + 0.5) * L, v.co.y * w, v.co.z * h))
    if nseg > 1:
        long_edges = [e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > L * 0.5]
        bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=nseg - 1, use_grid_fill=True)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, w * 0.3, h * 0.3),
                        segments=1, affect='EDGES', profile=0.5, clamp_overlap=True)
    return bm

def cyl_bm(L, r, sides=8, nseg=3, r2=None, rough=0.0):
    """Válec podél lokální osy X od 0 do L."""
    bm = new_piece_bm()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=sides,
                          radius1=r, radius2=r if r2 is None else r2, depth=L)
    # osa Z -> osa X, posun do 0..L
    for v in bm.verts:
        x, y, z = v.co
        v.co = Vector((z + L / 2, y, -x))
    if nseg > 1:
        long_edges = [e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > L * 0.5]
        bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=nseg - 1)
    return bm

def handmade(bm, L, sag=0.0, twist=0.0, hew=0.002, seed=0.0):
    """Ruční nepravidelnost: průhyb, zkroucení, stopy po sekeře/tesle."""
    for v in bm.verts:
        x, y, z = v.co
        t = x / L if L > 0 else 0
        a = twist * (t - 0.5)
        y2 = y * math.cos(a) - z * math.sin(a)
        z2 = y * math.sin(a) + z * math.cos(a)
        z2 -= sag * math.sin(math.pi * t)
        n = noise.noise(Vector((x * 3.0 + seed, y * 9.0, z * 9.0)))
        n2 = noise.noise(Vector((x * 11.0 + seed * 2, y * 25.0, z * 25.0)))
        k = 1.0 + (n * 0.6 + n2 * 0.4) * hew / max(0.01, (abs(y) + abs(z)))
        v.co = Vector((x, y2 * k, z2 * k))

def frame(A, B, up=Vector((0, 0, 1))):
    A, B = Vector(A), Vector(B)
    x = (B - A).normalized()
    up = Vector(up)
    if abs(x.dot(up.normalized())) > 0.98:
        up = Vector((0, 1, 0)) if abs(x.y) < 0.9 else Vector((1, 0, 0))
    z = (up - x * up.dot(x)).normalized()
    y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = A
    return M, (B - A).length

def finish(bm, M, name, wood="dub", age=None, metal=0.0, wheel=0.0, handled=0.0, fresh=0.0, pre_lp=None):
    """Zapíše atributy, box-UV v lokálu, transformuje a vytvoří objekt."""
    PID[0] += 1
    pid = PID[0] * 0.6180339 % 1.0
    if age is None:
        age = rng.uniform(0.45, 1.0)
    if fresh:
        age = rng.uniform(0.05, 0.2)         # později vyměněný kus
    wl, wd = WOOD.get(wood, WOOD["dub"])
    wl = jitter(wl, 0.12); wd = jitter(wd, 0.12)
    L = {n: bm.verts.layers.float[n] for n in ("pid", "age", "metal", "wheel", "handled", "fresh")}
    V = {n: bm.verts.layers.float_vector[n] for n in ("lp", "wl", "wd")}
    for i, v in enumerate(bm.verts):
        v[V["lp"]] = pre_lp[i] if pre_lp is not None else v.co.copy()
        v[V["wl"]] = wl; v[V["wd"]] = wd
        v[L["pid"]] = pid; v[L["age"]] = age; v[L["metal"]] = metal
        v[L["wheel"]] = wheel; v[L["handled"]] = handled; v[L["fresh"]] = fresh
    # box mapping v lokálních souřadnicích (metry) – ostrovy se na konci zabalí
    uv = bm.loops.layers.uv.new("UVMap")
    bm.normal_update()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lo in f.loops:
            c = lo.vert.co
            lo[uv].uv = (c.y, c.z) if ax == 0 else ((c.x, c.z) if ax == 1 else (c.x, c.y))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    PIECES.append(ob)
    return ob

def beam(A, B, w, h, wood="dub", up=(0, 0, 1), nseg=6, sag=0.004, twist=0.03, hew=0.003,
         bevel=None, **kw):
    M, Lg = frame(A, B, up)
    age_bevel = bevel if bevel is not None else rng.uniform(0.006, 0.014)
    bm = box_bm(Lg, w, h, nseg, age_bevel)
    handmade(bm, Lg, sag * rng.uniform(0.5, 1.5), twist * rng.uniform(-1, 1), hew, rng.uniform(0, 100))
    return finish(bm, M, "beam", wood, **kw)

def pole(A, B, r, wood="jasan", up=(0, 0, 1), sides=9, nseg=6, r2=None, sag=0.01, hew=0.004, **kw):
    M, Lg = frame(A, B, up)
    bm = cyl_bm(Lg, r, sides, nseg, r2)
    handmade(bm, Lg, sag * rng.uniform(0.5, 1.5), rng.uniform(-0.1, 0.1), hew, rng.uniform(0, 100))
    return finish(bm, M, "pole", wood, **kw)

# ------------------------------------------------------------------ rozměry
TRACK = 0.64                  # polovina rozchodu (střed kola od osy vozu)
RA_Y, FA_Y = 1.00, -1.00      # zadní / přední náprava
RR, FR = 0.54, 0.44           # poloměry kol
BED_Z = 0.80                  # spodek ložné plochy (horní hrana podsedníků)
BED_L0, BED_L1 = -1.55, 1.85  # délka ložné plochy
SILL_X = 0.34

# ------------------------------------------------------------------ kolo
def wheel(cx, cy, R, nspokes, front):
    cz = R
    hub_r, hub_L = 0.115 if front else 0.13, 0.34
    side = 1 if cx > 0 else -1
    # náboj (jilm) – soudkovitý válec podél X
    M, Lg = frame((cx - side * hub_L * 0.45, cy, cz), (cx + side * hub_L * 0.55, cy, cz), (0, 0, 1))
    bm = cyl_bm(Lg, hub_r * 0.85, 14, 6)
    for v in bm.verts:                          # soudek
        t = v.co.x / Lg
        k = 1 + 0.18 * math.sin(math.pi * t)
        v.co.y *= k; v.co.z *= k
    handmade(bm, Lg, 0, 0, 0.002, rng.uniform(0, 99))
    finish(bm, M, "hub", "jilm", wheel=1.0)
    # železné obruče na náboji
    for t in (0.12, 0.88):
        x0 = cx + side * (-hub_L * 0.45 + hub_L * t)
        M, Lg = frame((x0 - 0.018, cy, cz), (x0 + 0.018, cy, cz), (0, 0, 1))
        k = 1 + 0.18 * math.sin(math.pi * t)
        bm = cyl_bm(Lg, hub_r * 0.85 * k + 0.006, 14, 1)
        finish(bm, M, "hubband", "dub", metal=1.0, wheel=1.0)
    # loukotě (6 nebo 5 dílů) – ohnuté kvádry
    nfel = 6 if not front else 5
    fel_t, fel_w = 0.075, 0.07                  # radiální tloušťka, šířka
    Rm = R - 0.012 - fel_t / 2                  # střed loukotě (obruč 12 mm)
    dish = 0.035 * side                         # kolo je mírně miskovité
    a_off = rng.uniform(0, math.tau)
    for i in range(nfel):
        a0 = a_off + i * math.tau / nfel + 0.004
        a1 = a_off + (i + 1) * math.tau / nfel - 0.004
        Lg = (a1 - a0) * Rm
        bm = box_bm(Lg, fel_w, fel_t, 7, rng.uniform(0.006, 0.012))
        handmade(bm, Lg, 0, 0, 0.002, rng.uniform(0, 99))
        pre = [v.co.copy() for v in bm.verts]
        # ohnutí: x -> úhel, z -> poloměr, y -> osa kola
        for v in bm.verts:
            x, y, z = v.co
            a = a0 + x / Rm
            r = Rm + z
            v.co = Vector((y + dish, r * math.cos(a), r * math.sin(a)))
        # lp musí zůstat v nerozohnutém tvaru -> zapíšeme ručně před finish:
        # (finish bere aktuální co jako lp; ohyb zachová směr let po obvodu jen přibližně – stačí)
        finish(bm, Matrix.Translation((cx, cy, cz)), "felloe", "dub",
               fresh=1.0 if rng.random() < 0.12 else 0.0, wheel=1.0, pre_lp=pre)
    # železné šíny (strakes) přes spoje loukotí
    nstr = nfel
    s_off = a_off + math.pi / nfel
    for i in range(nstr):
        a0 = s_off + i * math.tau / nstr + 0.01
        a1 = s_off + (i + 1) * math.tau / nstr - 0.01
        Lg = (a1 - a0) * (R - 0.006)
        bm = box_bm(Lg, fel_w * 0.92, 0.012, 9, 0.002)
        handmade(bm, Lg, 0, 0, 0.0008, rng.uniform(0, 99))
        for v in bm.verts:
            x, y, z = v.co
            a = a0 + x / (R - 0.006)
            r = R - 0.006 + z
            v.co = Vector((y + dish, r * math.cos(a), r * math.sin(a)))
        finish(bm, Matrix.Translation((cx, cy, cz)), "strake", "dub", metal=1.0, wheel=1.0)
    # paprsky (dub/jasan), mírně kónické a do misky
    for i in range(nspokes):
        a = a_off + (i + 0.5) * math.tau / nspokes
        dirv = Vector((0, math.cos(a), math.sin(a)))
        A = Vector((cx + side * 0.03, cy, cz)) + dirv * (hub_r * 0.95)
        B = Vector((cx + dish * 1.0 + side * 0.0, cy, cz)) + dirv * (Rm - fel_t * 0.3)
        M, Lg = frame(A, B, (1, 0, 0))
        bm = box_bm(Lg, 0.042, 0.032, 5, 0.008)
        for v in bm.verts:                       # zúžení k loukoti
            t = v.co.x / Lg
            v.co.y *= 1.0 - 0.25 * t; v.co.z *= 1.0 - 0.15 * t
        handmade(bm, Lg, 0, rng.uniform(-0.05, 0.05), 0.0025, rng.uniform(0, 99))
        finish(bm, M, "spoke", rng.choice(["dub", "jasan"]),
               fresh=1.0 if rng.random() < 0.08 else 0.0, wheel=1.0)
    # zákolník (železný klín v ose)
    xo = cx + side * (hub_L * 0.55 + 0.03)
    beam((xo, cy - 0.006, cz + 0.05), (xo, cy - 0.006, cz - 0.06), 0.012, 0.02,
         "dub", up=(1, 0, 0), nseg=1, sag=0, twist=0, hew=0, bevel=0.002, metal=1.0, wheel=1.0)

for (cy, R, n, fr) in ((RA_Y, RR, 12, False), (FA_Y, FR, 10, True)):
    for sx in (-1, 1):
        wheel(sx * TRACK, cy, R, n, fr)

# ------------------------------------------------------------------ nápravy, podsedníky, rozvora
for (cy, R, front) in ((RA_Y, RR, False), (FA_Y, FR, True)):
    # dřevěná náprava (osa) s čepy do nábojů
    beam((-TRACK + 0.12, cy, R + 0.0), (TRACK - 0.12, cy, R + 0.0), 0.12, 0.13, "buk", nseg=8, sag=0.002)
    for sx in (-1, 1):
        pole((sx * (TRACK - 0.14), cy, R), (sx * (TRACK + 0.2), cy, R), 0.042, "buk",
             sides=10, nseg=2, r2=0.034, sag=0, hew=0.001)
    # podsedník (bolster) – na zadní nápravě rovnou, na přední s točnicí výš
    zb = BED_Z - 0.065
    if front:
        beam((-0.55, cy, R + 0.065 + 0.05), (0.55, cy, R + 0.065 + 0.05), 0.13, 0.10, "dub", nseg=6)   # točna
        zb = BED_Z - 0.065
    beam((-0.62, cy, zb), (0.62, cy, zb), 0.14, 0.13, "dub", nseg=8, sag=0.006)
    # klanice – šikmé kolíky na koncích podsedníku držící žebřiny
    for sx in (-1, 1):
        A = Vector((sx * 0.57, cy, zb - 0.05))
        B = Vector((sx * 0.80, cy + rng.uniform(-0.02, 0.02), BED_Z + 0.70))
        beam(A, B, 0.055, 0.06, "dub", up=(0, -1, 0), nseg=6, sag=0.006, hew=0.004)

# rozvora (perch) – dlouhý trám spojující nápravy
beam((0, FA_Y - 0.25, FR + 0.02), (0, RA_Y + 0.45, RR + 0.03), 0.10, 0.10, "dub", nseg=10, sag=0.01)
# zadní a přední rozvory (hounds) – šikmé vzpěry
for sx in (-1, 1):
    beam((sx * 0.42, RA_Y, RR + 0.02), (0, RA_Y - 0.75, RR + 0.03), 0.06, 0.07, "dub", nseg=5)
    beam((sx * 0.40, FA_Y, FR + 0.03), (sx * 0.06, FA_Y - 0.55, FR + 0.01), 0.06, 0.07, "dub", nseg=5)

# ------------------------------------------------------------------ ložná plocha
for sx in (-1, 1):   # dlouhé podélníky
    beam((sx * SILL_X, BED_L0, BED_Z + 0.05), (sx * SILL_X, BED_L1, BED_Z + 0.05), 0.11, 0.10,
         "dub", nseg=12, sag=0.012)
# podlaha z prken (smrk) – volně ložená, nestejná, mezery
x = -SILL_X - 0.02
while x < SILL_X + 0.02:
    w = rng.uniform(0.12, 0.2)
    if x + w > SILL_X + 0.06:
        w = SILL_X + 0.06 - x
    if w < 0.06:
        break
    y0 = BED_L0 + rng.uniform(0.0, 0.08); y1 = BED_L1 - rng.uniform(0.0, 0.1)
    z = BED_Z + 0.10 + 0.012 + rng.uniform(-0.003, 0.004)
    beam((x + w / 2, y0, z), (x + w / 2, y1, z), w - rng.uniform(0.008, 0.02), 0.024 + rng.uniform(-0.003, 0.004),
         "smrk", up=(0, 0, 1), nseg=14, sag=0.006, twist=0.04, hew=0.0015, bevel=0.004,
         fresh=1.0 if rng.random() < 0.18 else 0.0)
    x += w

# ------------------------------------------------------------------ žebřiny
LAD_H = 0.72
def ladder(sx):
    yb0, yb1 = BED_L0 + 0.05, BED_L1 - 0.05
    bot = lambda y: Vector((sx * (SILL_X + 0.03), y, BED_Z + 0.14))
    top = lambda y: Vector((sx * (SILL_X + 0.03 + 0.42), y, BED_Z + 0.14 + LAD_H))
    # spodní lať a horní bidlo (ohlazené rukama)
    beam(bot(yb0 - 0.05), bot(yb1 + 0.08), 0.07, 0.08, "dub", nseg=14, sag=0.01)
    pole(top(yb0 - 0.25), top(yb1 + 0.3), 0.042, "jasan", sides=10, nseg=10, r2=0.036,
         sag=0.03, hew=0.004, handled=1.0)
    # příčky – nestejné rozestupy, některé vyměněné, jedna chybí
    y = yb0 + 0.05
    missing = rng.randrange(4, 16)
    i = 0
    while y < yb1:
        i += 1
        if i != missing:
            jitter_top = Vector((0, rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.01)))
            tp = top(y) + jitter_top
            tp = tp + (tp - bot(y)).normalized() * rng.uniform(0.035, 0.06)   # konec čouhá nad bidlo
            pole(bot(y) + Vector((0, 0, -0.02)), tp, 0.017 + rng.uniform(-0.002, 0.003),
                 rng.choice(["jasan", "buk", "dub"]), sides=7, nseg=3, sag=0.004, hew=0.002,
                 fresh=1.0 if rng.random() < 0.12 else 0.0)
        y += rng.uniform(0.15, 0.21)
for sx in (-1, 1):
    ladder(sx)

# čela – přední prkno a zadní zástěra (vyjímatelná)
for (yy, h) in ((BED_L0 + 0.02, 0.38), (BED_L1 - 0.02, 0.30)):
    for k in range(2):
        z = BED_Z + 0.14 + k * h / 2 + 0.01
        beam((-SILL_X - 0.08, yy, z + h / 4), (SILL_X + 0.08, yy, z + h / 4), 0.03, h / 2 - 0.01,
             "smrk", up=(0, -1, 0), nseg=6, sag=0.002, bevel=0.005)
    for sx in (-1, 1):
        beam((sx * (SILL_X + 0.03), yy + 0.03 * (1 if yy < 0 else -1), BED_Z + 0.06),
             (sx * (SILL_X + 0.05), yy + 0.03 * (1 if yy < 0 else -1), BED_Z + 0.16 + h), 0.045, 0.045,
             "dub", up=(0, -1, 0), nseg=3)

# ------------------------------------------------------------------ oj a rozporka
tip = Vector((rng.uniform(-0.15, 0.15), FA_Y - 3.0, 0.045))
pole((0, FA_Y - 0.15, FR + 0.04), tip, 0.055, "jasan", sides=10, nseg=12, r2=0.042, sag=-0.02,
     hew=0.004, handled=0.5)
# kovové oko na konci oje
pdir = (tip - Vector((0, FA_Y - 0.15, FR + 0.04))).normalized()
pole(tip - pdir * 0.12, tip + pdir * 0.01, 0.047, "dub", sides=12, nseg=1, sag=0, hew=0.0005, metal=1.0)
# kované oko (kruh) na konci oje
ring_c = tip + pdir * 0.06 + Vector((0, 0, 0.0))
Rr, rr = 0.055, 0.011
bm = cyl_bm(math.tau * Rr, rr, 8, 16)
for v in bm.verts:
    x, y, z = v.co
    a = x / Rr
    r = Rr + z
    v.co = Vector((y, r * math.cos(a), r * math.sin(a)))
finish(bm, Matrix.Translation(ring_c + pdir * Rr * 0.6), "ring", "dub", metal=1.0)
# dřevěné kolíky ve spojích klanic a podsedníků
for (cy, R) in ((RA_Y, RR), (FA_Y, FR)):
    for sx in (-1, 1):
        A = Vector((sx * 0.60, cy - 0.09, BED_Z - 0.065)); B = Vector((sx * 0.60, cy + 0.09, BED_Z - 0.065))
        pole(A, B, 0.012, "buk", sides=6, nseg=1, sag=0, hew=0.0005)
# rozporka (vahadlo) u přední nápravy
beam((-0.45, FA_Y - 0.62, FR + 0.03), (0.45, FA_Y - 0.62, FR + 0.03), 0.06, 0.06, "jasan",
     nseg=6, handled=0.3)

# ------------------------------------------------------------------ plachta (volitelně)
CANVAS = None
if COVER:
    TOP_Z = BED_Z + 0.14 + LAD_H
    HX = SILL_X + 0.03 + 0.42 + 0.02          # polovina šířky oblouku (na horních bidlech)
    HZ = 0.70                                  # výška oblouku nad bidly
    hoop_ys = [BED_L0 + 0.15 + i * (BED_L1 - BED_L0 - 0.3) / 4 for i in range(5)]
    hoop_ys = [y + rng.uniform(-0.04, 0.04) for y in hoop_ys]
    # oblouky z ohýbaných lískových prutů
    for hy in hoop_ys:
        npts = 18
        Larc = 2.6
        bm = cyl_bm(Larc, 0.022, 7, npts)
        pre = [v.co.copy() for v in bm.verts]
        for v in bm.verts:
            x, y, z = v.co
            t = min(max(x / Larc, 0.0), 1.0)
            a = math.pi * (1 - t)
            # elipsa; průřez prutu (y,z) kolmo na oblouk
            cx_, cz_ = HX * math.cos(a), HZ * math.sin(a)
            nx, nz = math.cos(a) / HX, math.sin(a) / HZ
            nl = math.hypot(nx, nz); nx, nz = nx / nl, nz / nl
            wob = 0.01 * noise.noise(Vector((t * 4, hy * 3, 0.5)))
            v.co = Vector((cx_ + nx * (z + wob), hy + y, TOP_Z + cz_ + nz * (z + wob)))
        finish(bm, Matrix(), "hoop", "jasan", pre_lp=pre)
        # konce oblouků přivázané k bidlům – lýková/provazová vazba
        for sx in (-1, 1):
            pole(Vector((sx * HX, hy - 0.035, TOP_Z - 0.01)), Vector((sx * HX, hy + 0.035, TOP_Z - 0.01)), 0.017,
                 "dub", sides=7, nseg=1, sag=0, hew=0.002)

    # plachta – samostatný objekt (vlastní materiál a textura)
    NU, NV = 64, 40
    y0, y1 = BED_L0 - 0.08, BED_L1 + 0.12
    drop = 0.30
    # profil: svislý převis vlevo, elipsa, převis vpravo (podle délky oblouku)
    prof = []
    for i in range(8):
        prof.append(Vector((-HX - 0.03, TOP_Z - drop + drop * i / 8)))
    for i in range(NV - 16 + 1):
        a = math.pi * (1 - i / (NV - 16))
        prof.append(Vector(((HX + 0.03) * math.cos(a), TOP_Z + (HZ + 0.03) * math.sin(a))))
    for i in range(1, 9):
        prof.append(Vector((HX + 0.03, TOP_Z - drop * i / 8)))
    arcl = [0.0]
    for i in range(1, len(prof)):
        arcl.append(arcl[-1] + (prof[i] - prof[i - 1]).length)
    S = arcl[-1]
    me_c = bpy.data.meshes.new("plachta")
    verts, faces, uvs, lps = [], [], [], []
    for iu in range(NU + 1):
        u = iu / NU
        y = y0 + (y1 - y0) * u
        # průhyb mezi oblouky
        dmin = min(abs(y - hy) for hy in hoop_ys)
        sag = 0.045 * math.sin(min(dmin / 0.45, 1.0) * math.pi / 2) ** 2
        # stažení na koncích (zadrhnuté provazem)
        endk = min(u, 1 - u) / 0.07
        gather = 1.0 if endk >= 1 else 0.82 + 0.18 * endk
        for iv, pnt in enumerate(prof):
            s = arcl[iv]
            px, pz = pnt.x, pnt.y - TOP_Z
            # radiální směr pro průhyb/vrásky
            r = math.hypot(px, max(pz, 0.0) * HX / HZ) or 1.0
            k = (1 - sag) * gather
            x = px * k
            z = TOP_Z + (pz if pz < 0 else pz * k)
            # vrásky: svislé sklady u spodního okraje, jemné zvlnění všude
            low = max(0.0, (drop * 0.9 - min(s, S - s)) / drop) if min(s, S - s) < drop else 0.0
            fold = 0.02 * low * (0.6 * math.sin(y * 13 + noise.noise(Vector((y * 1.3, s, 1.0))) * 5) + 0.6 * noise.noise(Vector((y * 7, s * 2, 5.0))))
            wr = 0.012 * noise.noise(Vector((y * 3.0, s * 3.0, 7.0))) + 0.005 * noise.noise(Vector((y * 9, s * 9, 3.0)))
            endfold = 0.012 * max(0.0, 1 - endk) * (math.sin(s * 14 + noise.noise(Vector((s * 3, u * 9, 2.0))) * 2) + 0.6 * noise.noise(Vector((s * 6, u * 20, 4.0))))
            nx = (px / (abs(px) + 1e-6)) if pz < 0 else px / r
            nz = 0.0 if pz < 0 else (pz * HX / HZ) / r
            d = fold + wr + endfold
            verts.append((x + nx * d, y, z + nz * d))
            uvs.append((u, s / S)); lps.append((y - y0, s, 0.0))
    W = len(prof)
    for iu in range(NU):
        for iv in range(W - 1):
            a = iu * W + iv
            faces.append((a, a + 1, a + W + 1, a + W))
    me_c.from_pydata(verts, [], faces)
    uvl = me_c.uv_layers.new(name="UVMap")
    for poly in me_c.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me_c.loops[li].vertex_index]
    a_lp = me_c.attributes.new("lp", 'FLOAT_VECTOR', 'POINT')
    a_lp.data.foreach_set("vector", [c for v in lps for c in v])
    me_c.update()
    for p in me_c.polygons:
        p.use_smooth = True
    CANVAS = bpy.data.objects.new("plachta", me_c)
    bpy.context.collection.objects.link(CANVAS)

# ------------------------------------------------------------------ spojení a rez u kovu
bpy.ops.object.select_all(action='DESELECT')
for o in PIECES:
    o.select_set(True)
bpy.context.view_layer.objects.active = PIECES[0]
bpy.ops.object.join()
wag = bpy.context.active_object
wag.name = "wagon"
me = wag.data

# blízkost kovu -> rezavé stékance na dřevě
n = len(me.vertices)
co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
met = np.empty(n); me.attributes["metal"].data.foreach_get("value", met)
kd = KDTree(int((met > 0.5).sum()))
for i in np.where(met > 0.5)[0]:
    kd.insert(co[i], int(i))
kd.balance()
rust = np.zeros(n)
for i in np.where(met < 0.5)[0]:
    _, _, d = kd.find(co[i])
    rust[i] = max(0.0, 1.0 - d / 0.06)
a = me.attributes.new("rust_near", 'FLOAT', 'POINT'); a.data.foreach_set("value", rust.astype(np.float32))

# pivot dole uprostřed (země = nejnižší bod kol)
zmin = co[:, 2].min()
co[:, 2] -= zmin
cx = (co[:, 0].max() + co[:, 0].min()) / 2
cy = (co[:, 1].max() + co[:, 1].min()) / 2
co[:, 0] -= cx; co[:, 1] -= cy
me.vertices.foreach_set("co", co.ravel()); me.update()
if CANVAS is not None:
    for v in CANVAS.data.vertices:
        v.co.x -= cx; v.co.y -= cy; v.co.z -= zmin
for p in me.polygons:
    p.use_smooth = False
try:
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
except Exception as e:
    print("smooth by angle n/a", e)

# zabalení UV ostrovů do jedné textury
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(margin=0.0015, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')

print("WAGON tris", sum(len(p.vertices) - 2 for p in me.polygons), "dims",
      tuple(round(x, 2) for x in wag.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
