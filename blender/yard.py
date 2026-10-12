"""Nadvori: strazni domek, studna, vuz, sena, drivi; trava u zdi a v koutech."""
import math

from mathutils import Matrix, Vector

import fort as F
import props as PR
from lib import M, Part, R, jit, light, rot, shingle_roof, wall_x, wall_z


def build(coll, paths):
    guardhouse(coll)
    misc(coll)
    grass(coll, paths)
    forest(coll)


def guardhouse(coll):
    P = Part("Straznice", bevel=0.02)
    x0, x1, z0, z1 = -12.0, -4.2, 8.5, 14.0
    h, t = 3.0, 0.5
    top = h + 2.4
    slope = 2.4 / (z1 - z0)
    wall_x(P, "zdivo_omitka", x0, x1, z0, z0 + t, 0.0, h, [[-6.6, -5.5, 0.0, 2.05], [-10.2, -9.2, 1.2, 2.2]])
    wall_z(P, "zdivo_omitka", z0 + t, z1, x0, x0 + t, 0.0, h)
    wall_z(P, "zdivo_omitka", z0 + t, z1, x1 - t, x1, 0.0, h)
    for xa in (x0, x1 - t):
        q = [Vector((xa, h, z0)), Vector((xa, h, z1)), Vector((xa, top, z1))]
        P.prism(q, Vector((t, 0, 0)), "zdivo_omitka")
    P.bb((x0, -0.6, z0), (x1, 0.0, z1), "zdivo_hole")
    # sokl s mezerou ve dverich
    for a, b in ((x0 - 0.06, -6.6), (-5.5, x1 + 0.06)):
        P.bb((a, 0.0, z0 - 0.07), (b, 0.42, z0 + 0.02), "zdivo_hole")
    F.quoins(P, x0, z0, 1, 1, 0.0, h, 0.6, 0.35, 0.3)
    F.quoins(P, x1, z0, -1, 1, 0.0, h, 0.6, 0.35, 0.3)
    # ostění dveri a okna
    for sx in (-1, 1):
        cx, hw = -6.05, 0.55
        P.bb((cx + sx * (hw - 0.01), 0.0, z0 - 0.06), (cx + sx * (hw + 0.2), 2.05, z0 + 0.3), "kvadr")
    P.bb((-6.05 - 0.78, 2.04, z0 - 0.07), (-6.05 + 0.78, 2.34, z0 + 0.3), "kvadr")
    P.bb((-6.9, -0.05, z0 - 0.5), (-5.2, 0.1, z0 + 0.02), "kvadr_sedy", collide=True)
    for sx in (-1, 1):
        P.bb((-9.7 + sx * 0.49, 1.2, z0 - 0.05), (-9.7 + sx * 0.66, 2.2, z0 + 0.2), "kvadr")
    P.bb((-10.4, 1.05, z0 - 0.08), (-9.0, 1.21, z0 + 0.2), "kvadr")
    P.bb((-10.36, 2.19, z0 - 0.06), (-9.04, 2.4, z0 + 0.2), "kvadr")
    for bx in (-9.95, -9.7, -9.45):
        P.rod((bx, 1.2, z0 + 0.12), (bx, 2.2, z0 + 0.12), 0.016, 6, "zelezo")
    P.rod((-10.2, 1.7, z0 + 0.1), (-9.2, 1.7, z0 + 0.1), 0.014, 6, "zelezo")
    P.bb((x0 + t, 0.0, z0 + t), (x1 - t, 0.04, z1), "prkna", collide=True)
    P.commit(coll)

    W = Part("StrazniceKrov", bevel=0.01)
    ya = h - 0.5 * slope
    shingle_roof(W, (x1 + 0.45, ya, z0 - 0.5), (x0 - 0.45, ya, z0 - 0.5), (x0 - 0.45, top + 0.02, z1), (x1 + 0.45, top + 0.02, z1), ridge=False)
    for sx, xx in ((-1, x0 - 0.45), (1, x1 + 0.45)):
        W.beam((xx, ya - 0.05, z0 - 0.5), (xx, top - 0.05, z1), 0.05, 0.26, "dub_ven")
    rx = x0 + 0.9
    while rx < x1 - 0.3:
        W.beam((rx, h - 0.16, z0 - 0.3), (rx, top - 0.12, z1), 0.12, 0.16, "dub", j=1)
        rx += 1.2
    W.beam((x0, h - 0.1, z0 + 0.25), (x1, h - 0.1, z0 + 0.25), 0.2, 0.2, "dub", j=0.5)
    # dvere pootevrene
    from palace import _plank_leaf
    m = M((-6.6 + 0.03, 1.02, z0 + t - 0.08)) @ rot("Y", -70) @ M((0.53, 0, 0))
    _plank_leaf(W, m, 1.04, 2.0)
    W.commit(coll)

    V = Part("StrazniceVybaveni", bevel=0.006)
    PR.weapon_rack(V, M((-8.3, 0.04, 13.72)), 2.4, 6)
    # mece na stene
    for k in range(4):
        PR.sword(V, M((x0 + t + 0.05, 1.0, 9.7 + 0.32 * k), 90))
    for k, (c1, c2) in enumerate((("sukno_cervene", "bila"), ("sukno_modre", "zluta"), ("sukno_cervene", "zluta"))):
        PR.shield(V, M((x1 - t - 0.05, 1.95, 10.3 + 0.9 * k), 90), c1, c2)
    PR.armor_stand(V, M((-5.5, 0.04, 13.3), 180))
    PR.armor_stand(V, M((-6.4, 0.04, 13.4), 170))
    PR.table(V, M((-8.0, 0.04, 10.7), 90), 2.0, 0.8)
    PR.bench(V, M((-8.0, 0.04, 10.0), 90), 1.9)
    PR.bench(V, M((-8.0, 0.04, 11.4), 90), 1.9)
    PR.mug(V, (-8.4, 0.82, 10.6))
    PR.mug(V, (-7.6, 0.82, 10.85), "cin")
    PR.jug(V, (-8.0, 0.82, 10.7))
    p = PR.candle(V, (-7.3, 0.82, 10.6), True)
    light(p, 18, (1.0, 0.55, 0.25), 0.02)
    for k in range(3):
        V.box(M((-8.7 + 0.06 * k, 0.835, 10.9 + 0.05 * k), 20 * k), (0.03, 0.03, 0.03), "bila")
    PR.bed(V, M((-10.75, 0.04, 12.9)), 2.0, 1.0, cover="pytlovina")
    PR.chest(V, M((-10.75, 0.04, 11.4), 90), 1.0)
    p = PR.brazier(V, (-6.4, 0.04, 11.6))
    light(p, 70, (1.0, 0.35, 0.1), 0.2)
    PR.barrel(V, M((-5.1, 0.04, 9.5)), 0.32, 0.9, False)
    for k in range(4):
        PR.spear(V, (-5.1 + 0.05 * k, 0.5, 9.45 + 0.03 * k), (-5.0 + 0.1 * k, 2.3, 9.6 - 0.05 * k))
    PR.shelf(V, M((-8.2, 0.04, z0 + t + 0.2), 180), 1.6, 1.8, 3)
    for k in range(3):
        PR.helmet(V, (-8.7 + 0.5 * k, 0.94, z0 + t + 0.2), k % 2)
    p = PR.torch(V, M((-9.0, 2.0, z1 - 0.02)))
    light(p, 45, (1.0, 0.5, 0.2), 0.05)
    V.commit(coll)


def misc(coll):
    P = Part("NadvoriVybaveni", bevel=0.008)
    PR.well(P, (-3.6, 0.0, -1.6))
    PR.cart(P, M((8.6, 0.0, 1.2), 35))
    PR.hay_pile(P, (10.2, 0.0, -1.2), 1.1)
    PR.woodpile(P, M((12.6, 0.0, -6.35)), 2.2, 6, 0.5)
    PR.woodpile(P, M((15.6, 0.0, 2.0), 90), 3.0, 7, 0.5)
    PR.chopping_block(P, (15.6, 0.0, -5.2))
    PR.logs(P, M((15.0, 0.0, -4.6), 30), 3, 0.5)
    for k in range(6):
        P.box(M((14.6 + jit(0.6), 0.04, -5.6 + jit(0.6)), R.uniform(0, 180)), (0.06, 0.06, 0.35), "drevo_rez")
    PR.barrel(P, M((1.6, 0.0, -6.3)))
    PR.barrel(P, M((2.3, 0.0, -6.25)), 0.3, 0.85)
    PR.bucket(P, (-4.9, 0.0, -0.6), True)
    PR.crate(P, M((3.2, 0.0, 8.6), 12))
    PR.crate(P, M((3.3, 0.7, 8.55), -8), 0.5)
    PR.sack(P, M((2.5, 0.0, 8.0)))
    PR.sack(P, M((2.9, 0.0, 7.6)), 0.3, True)
    PR.barrel(P, M((-3.0, 0.0, 8.8)), 0.36, 1.0)
    PR.trough(P, (7.1, 0.0, 11.3), 2.2)
    PR.hitching_post(P, (5.0, 0.0, 9.9), (5.0, 0.0, 12.4))
    # kmeny k porezu u vychodni zdi
    for k in range(5):
        y = 0.22 + (0.38 if k > 2 else 0.0)
        z = 5.0 + (k % 3) * 0.48 + (0.24 if k > 2 else 0.0)
        P.rod((12.0, y, z), (16.4 + jit(0.2), y, z + jit(0.1)), 0.21 + jit(0.03), 12, "kura")
    PR.hay_pile(P, (14.0, 0.0, 8.0), 0.8)
    PR.barrel(P, M((-14.5, 0.0, -6.8)), 0.34, 0.95)
    PR.barrel(P, M((-15.2, 0.0, -7.2)), 0.3, 0.8)
    PR.crate(P, M((-15.6, 0.0, 12.5), 20))
    P.commit(coll)


def grass(coll, paths):
    """Trsy travy: u paty zdi, v koutech a mimo vyjete cesty; venku po svazich."""
    P = Part("Trava")
    n = 0

    def clump(x, y, z, s=1.0):
        nonlocal n
        k = R.randint(9, 16)
        for i in range(k):
            a = R.uniform(0, 2 * math.pi)
            h = R.uniform(0.12, 0.34) * s
            w = R.uniform(0.022, 0.04) * s
            lean = R.uniform(0.04, 0.16) * s
            base = Vector((x + jit(0.1), y, z + jit(0.1)))
            d = Vector((math.cos(a), 0, math.sin(a)))
            side = Vector((-d.z, 0, d.x)) * w
            tip = base + Vector((0, h, 0)) + d * lean
            P.face([base - side, base + side, tip], "trava", uvs=[(0, 0), (1, 0), (0.5, 1)])
        n += 1

    # uvnitr: pas u zdi a mista mimo cesty
    for _ in range(9000):
        x = R.uniform(-F.IX + 0.1, F.IX - 0.1)
        z = R.uniform(-F.IZ + 0.1, F.IZ - 0.1)
        dw = min(F.IX - abs(x), F.IZ - abs(z))
        dp = min(F.path_dist(x, z, p) for p in paths)
        p_ok = (dw < 0.8 and R.random() < 0.9) or (dp > 2.2 and R.random() < 0.3 * F.smooth(2.2, 4.0, dp))
        if not p_ok:
            continue
        if -3.0 < x < 18.8 and -14.0 < z < -5.4:     # palac a pavlac
            continue
        if -12.0 < x < -4.2 and 8.5 < z < 14.0:      # straznice
            continue
        if -19.8 < x < -11.8 and -16.8 < z < -8.8:
            continue
        clump(x, 0.0, z, 0.8 + 0.6 * (dw < 0.8))
    # venku
    for _ in range(14000):
        x = R.uniform(-45, 45)
        z = R.uniform(-40, 50)
        d = F.rect_dist(x, z)
        if d < 0.05 or (abs(x) < 2.3 and z > 16):
            continue
        y = F.land(x, z)
        clump(x, y - 0.02, z, 1.0 + 0.5 * (d < 1.6))
    o = P.commit(coll)
    return n


def spruce(P: Part, base, h):
    """Smrk: kmen a patra zubatych vetvi (zubaty obrys, previslé konce)."""
    base = Vector(base)
    P.rod(base - Vector((0, 0.3, 0)), base + Vector((0, h * 0.95, 0)), 0.03 * h ** 0.8, 7, "kura", 0.01)
    tiers = int(h / 0.9) + 3
    for k in range(tiers):
        t = k / tiers
        y = h * (0.12 + 0.85 * t)
        r = (1.0 - t) * h * 0.22 + 0.15
        seg = 11
        verts = [tuple(base + Vector((0, y + r * 0.35, 0)))]
        for i in range(seg * 2):
            a = math.pi * i / seg + jit(0.1)
            rr = r * (1.0 if i % 2 == 0 else 0.62) * (1 + jit(0.15))
            verts.append(tuple(base + Vector((rr * math.cos(a), y - r * 0.28 * (1.0 if i % 2 == 0 else 0.5) + jit(0.05), rr * math.sin(a)))))
        n = seg * 2
        faces = [(0, 1 + (i + 1) % n, 1 + i) for i in range(n)]
        P.mesh(verts, faces, "jehlici")
    P.lathe(M(base + Vector((0, h * 0.97, 0))), [(0.12, 0), (0.0, 0.5)], 6, "jehlici")


def forest(coll):
    P = Part("Les")
    placed = []
    tries = 0
    while len(placed) < 260 and tries < 20000:
        tries += 1
        x = R.uniform(-120, 120)
        z = R.uniform(-110, 130)
        d = F.rect_dist(x, z)
        if d < 26 or (abs(x) < 9 and z > 0) or abs(x - 0.25 * (z - 20)) < 8 and z > 20:
            continue
        # skupiny: hustsi les na severu a zapade
        dens = 0.25 + 0.75 * F.smooth(-20, -60, z) + 0.5 * F.smooth(-20, -70, x)
        if R.random() > dens:
            continue
        if any((x - a) ** 2 + (z - b) ** 2 < 9 for a, b in placed):
            continue
        placed.append((x, z))
        spruce(P, (x, F.land(x, z), z), R.uniform(11, 22))
    P.commit(coll)
