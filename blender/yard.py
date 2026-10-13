"""Nadvori: strazni domek, studna, vuz, sena, drivi; trava u zdi a v koutech."""
import math

from mathutils import Matrix, Vector

import fort as F
import props as PR
import lib
from lib import M, Part, R, jit, light, rot, shingle_roof, wall_x, wall_z


# pudorysy staveb na nadvori (bez dlazby, slamy a rostlin)
BLOCKED = [(-3.6, 18.8, -14.5, -6.75), (-21.0, -3.2, 8.4, 14.5), (-28.0, -19.4, -17.0, -8.4), (-25.5, -19.8, -8.8, 1.4),
           (-25.5, -20.4, 9.7, 13.5), (-2.4, 2.4, 9.0, 17.0), (3.8, 8.9, 4.8, 14.0)]


def build(coll, paths):
    import hospodar
    hospodar.build(coll)
    misc(coll)
    paving(coll, paths)


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
    # ostění dveri a okna ze stavebnice (kit): obycejne dvere se segmentovym zaklenkem, okno s parapetem
    import kit
    kit.doorway(P, M((-6.05, 0.0, z0), 180), "obycejne", 1.1, 2.05, t, "segment", open_deg=70)
    kit.window(P, M((-9.7, 1.2, z0), 180), 1.0, 1.0, t)
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
    W.commit(coll)

    if not lib.VYBAVENI:
        return
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
    import studna
    studna.build(coll, (-3.6, 0.0, -1.6))
    if not lib.VYBAVENI:
        P.commit(coll)
        return
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
        k = R.randint(18, 30)
        for i in range(k):
            a = R.uniform(0, 2 * math.pi)
            h = R.uniform(0.08, 0.3) * s
            w = R.uniform(0.007, 0.014) * s
            lean = R.uniform(0.04, 0.16) * s
            base = Vector((x + jit(0.14), y, z + jit(0.14)))
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


def slab(P: Part, c, r, y, mat="dlazba_kus"):
    """Jedna nepravidelna kamenna deska (mnohouhelnik), mirne naklonena a zapadla."""
    n = R.randint(7, 11)
    a0 = R.uniform(0, 2 * math.pi)
    sx, sz = r * R.uniform(0.75, 1.25), r * R.uniform(0.75, 1.25)
    tilt_x, tilt_z = jit(0.06), jit(0.06)
    pts = []
    for k in range(n):
        a = a0 + 2 * math.pi * k / n + jit(0.3)
        rr = R.uniform(0.62, 1.0)
        x = c[0] + math.cos(a) * sx * rr
        z = c[1] + math.sin(a) * sz * rr
        pts.append(Vector((x, y + tilt_x * (x - c[0]) + tilt_z * (z - c[1]), z)))
    # horni plocha CCW zhora
    if (pts[1] - pts[0]).cross(pts[2] - pts[0]).y < 0:
        pts.reverse()
    th = R.uniform(0.08, 0.14)
    P.prism([p - Vector((0, th, 0)) for p in pts], Vector((0, th, 0)), mat)


def paving(coll, paths):
    """Rozbita kamenna dlazba podel hlavnich cest: chybejici a zapadle desky, hlina a slama mezi nimi."""
    P = Part("Dlazba", bevel=0.025)
    main = [paths[0], paths[2], [(-3.6, 0.4), (-3.6, -3.6)]]
    step = 0.5
    x = F.WIX + 0.3
    while x < F.IX - 0.3:
        z = -F.IZ + 0.3
        while z < F.IZ - 0.3:
            px, pz = x + jit(0.1), z + jit(0.1)
            d = min(F.path_dist(px, pz, p) for p in main)
            dw = math.hypot(px + 3.6, pz + 1.6)
            near_well = 1.25 < dw < 2.4
            prob = (1.0 - F.smooth(1.0, 2.2, d)) * 0.9
            if near_well:
                prob = max(prob, 0.7)
            if 1.0 < dw < 1.25:
                prob = 0
            # zadne desky uvnitr budov (palac, straznice, vez)
            if any(a < px < b and c < pz < d for a, b, c, d in BLOCKED):
                prob = 0
            if R.random() < prob:
                sink = R.uniform(-0.03, 0.02) if R.random() > 0.15 else R.uniform(-0.06, -0.03)
                slab(P, (px, pz), step * R.uniform(0.52, 0.68), 0.04 + sink)
            z += step
        x += step
    P.commit(coll)
    # sláma a seno rozfoukane po nadvori
    S = Part("Slama")
    for _ in range(1400):
        px, pz = R.uniform(F.WIX + 0.5, F.IX - 0.5), R.uniform(-F.IZ + 0.5, F.IZ - 0.5)
        if any(a < px < b and c < pz < d for a, b, c, d in BLOCKED):
            continue
        if -3.0 < px < 18.8 and -14.0 < pz < -5.4:
            continue
        if -12.0 < px < -4.2 and 8.5 < pz < 14.0:
            continue
        d = min(F.path_dist(px, pz, p) for p in paths)
        if R.random() > 0.35 + 0.5 * (1 - F.smooth(0.5, 3.0, d)):
            continue
        a = R.uniform(0, math.pi)
        L = R.uniform(0.12, 0.32)
        dv = Vector((math.cos(a), R.uniform(0.0, 0.08), math.sin(a))) * L
        base = Vector((px, 0.045, pz))
        side = Vector((-math.sin(a), 0, math.cos(a))) * 0.004
        S.face([base - side, base + side, base + dv + side, base + dv - side], "slama", uvs=[(0, 0), (0.01, 0), (0.01, L), (0, L)])
    S.commit(coll)
