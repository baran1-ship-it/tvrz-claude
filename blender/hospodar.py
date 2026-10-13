"""Hospodarske stavby u hradeb (po rozsireni hradu na zapad):
- zbrojnice a kovarna pod jizni hradbou zapadne od brany, jedna budova s pultovou strechou svazitou od hradeb;
  kovarna je do nadvori otevrena podloubim se tremi oblouky (jako v Suchdole),
- dreveny staj se tremi boxy pod zapadni hradbou vedle veze,
- v rohu mezi nimi hnojiste a vuz.
Souradnice ve hre: X vychod, Y nahoru, Z jih. Jizni hradba ma vnitrni lic v z = 14, zapadni v x = -25.
"""
import math

from mathutils import Matrix, Vector

import fort as F
import kit
import lib
import props as PR
from lib import M, Part, R, jit, light, shingle_roof, wall_x

ZW = F.IZ             # vnitrni lic jizni hradby
XW = F.WIX            # vnitrni lic zapadni hradby


def lean_roof(W: Part, x0, x1, z_hi, y_hi, z_lo, y_lo, ovx=0.35):
    """Pultova sindelova strecha podel osy X: vysoko u hradby (z_hi), nizko do nadvori (z_lo)."""
    shingle_roof(W, (x1 + ovx, y_lo, z_lo), (x0 - ovx, y_lo, z_lo), (x0 - ovx, y_hi, z_hi), (x1 + ovx, y_hi, z_hi), ridge=False)
    # krokve a pozednice
    x = x0 + 0.3
    while x < x1:
        W.beam((x, y_lo - 0.12, z_lo + 0.2), (x, y_hi - 0.12, z_hi), 0.12, 0.16, "dub", j=0.8)
        x += 1.2
    W.beam((x0 - ovx, y_lo - 0.08, z_lo + 0.05), (x1 + ovx, y_lo - 0.08, z_lo + 0.05), 0.05, 0.24, "dub_ven")


def forge_armory(coll):
    P = Part("ZbrojniceKovarna", bevel=0.02)
    W = Part("ZbrojniceKovarnaKrov", bevel=0.01)
    x0, xm, x1 = -20.5, -10.6, -3.7          # kovarna x0..xm, zbrojnice xm..x1
    zf, t = 9.0, 0.8                          # predni zed (lic do nadvori v z = zf)
    y_hi, y_lo = 5.3, 3.4
    z_lo = zf - 0.55
    slope = (y_hi - y_lo) / (ZW - z_lo)

    def ry(z):
        return y_lo + (z - z_lo) * slope
    # --- predni zed: kovarna s podloubim (3 oblouky), zbrojnice s dvermi a oknem
    arches = []
    span = (xm - x0 - 0.6) / 3
    for i in range(3):
        cx = x0 + 0.3 + span * (i + 0.5)
        arches.append((cx, span - 0.95))
    a_spring = 0.85
    a_top = kit.arch_top("lomeny", arches[0][1], a_spring)(0.0) + 0.52
    holes = [[cx - w / 2, cx + w / 2, 0.0, a_top] for cx, w in arches]
    holes += [[-6.0, -4.9, 0.0, 2.1], [-8.9, -8.1, 1.15, 2.15]]
    wall_x(P, "zdivo_omitka", x0, x1, zf, zf + t, -0.3, ry(zf + t) - 0.02, holes)
    # lomene oblouky podloubi jako v Suchdole (hrube tesane klenaky po cele tloustce zdi)
    for cx, w in arches:
        kit.arcade(P, M((cx, 0.0, zf), 180), w, a_spring, t)
    kit.doorway(P, M((-5.45, 0.0, zf), 180), "obycejne", 1.1, 2.1, t, "segment", open_deg=0)
    kit.window(P, M((-8.5, 1.15, zf), 180), 0.8, 1.0, t)
    # boky a delici zed (pod pultovou strechou), sokl
    for xa in (x0, xm - t / 2, x1 - t):
        q = [Vector((xa, -0.3, zf)), Vector((xa, -0.3, ZW)), Vector((xa, y_hi, ZW)), Vector((xa, ry(zf), zf))]
        P.prism(q, Vector((t, 0, 0)), "zdivo_omitka")
        P.cols.append((M((xa + t / 2, 2.0, (zf + ZW) / 2)), (t, 4.0, ZW - zf)))
    # delici zed: pruchod mezi kovarnou a zbrojnici
    P.bb((xm - t / 2 - 0.02, 0.0, 11.0), (xm + t / 2 + 0.02, 2.1, 12.1), "dira")
    F.quoins(P, x0, zf, 1, 1, 0.0, ry(zf), 0.6, 0.35, 0.3)
    F.quoins(P, x1, zf, -1, 1, 0.0, ry(zf), 0.6, 0.35, 0.3)
    # podlahy: kovarna udusana hlina s kocickami, zbrojnice prkna
    P.bb((x0 + t, -0.2, zf + t), (xm - t / 2, 0.02, ZW), "kocicky", collide=True)
    P.bb((xm + t / 2, -0.2, zf + t), (x1 - t, 0.04, ZW), "prkna", collide=True)
    # --- vyhen kovarny u zapadni steny: zdena vyzdivka, ohniste, kozeny mech, digestor a komin nad strechu
    hx = x0 + t
    hz = 11.2
    P.bb((hx, 0.0, hz - 0.9), (hx + 1.4, 0.85, hz + 0.9), "kvadr_sedy", collide=True)
    kit.stone(P, M((hx + 1.42, 0.86, hz)), (0.18, 0.12, 1.84), "kvadr_sedy", cham=0.02)
    P.bb((hx + 0.25, 0.84, hz - 0.45), (hx + 1.05, 0.9, hz + 0.45), "uhli")
    P.bb((hx + 0.45, 0.86, hz - 0.2), (hx + 0.85, 0.92, hz + 0.2), "popel")
    # digestor (komolý jehlan) a komin
    a0, a1 = 0.95, 0.45
    for k in range(4):
        pass
    P.slab((hx, 2.0, hz - a0), (hx + 1.3, 2.0, hz - a0), (hx + 0.55, 3.6, hz - a1), (hx, 3.6, hz - a1), 0.1, "omitka")
    P.slab((hx + 1.3, 2.0, hz + a0), (hx, 2.0, hz + a0), (hx, 3.6, hz + a1), (hx + 0.55, 3.6, hz + a1), 0.1, "omitka")
    P.slab((hx + 1.3, 2.0, hz - a0), (hx + 1.3, 2.0, hz + a0), (hx + 0.55, 3.6, hz + a1), (hx + 0.55, 3.6, hz - a1), 0.1, "omitka")
    P.bb((hx - 0.05, 1.9, hz - a0 - 0.05), (hx + 1.35, 2.02, hz + a0 + 0.05), "dub")
    P.bb((hx, 3.6, hz - a1), (hx + 0.55, ry(hz) + 1.6, hz + a1), "zdivo_omitka", collide=True)
    P.bb((hx - 0.04, ry(hz) + 1.6, hz - a1 - 0.04), (hx + 0.59, ry(hz) + 1.72, hz + a1 + 0.04), "kvadr_sedy")
    # mech: dve kozena prkna s klinem
    mz = hz - 1.3
    for dy, ang in ((0.0, 0.0), (0.22, 0.18)):
        P.box(M((hx + 0.7, 0.95 + dy, mz - 0.3), basis=Matrix.Rotation(ang, 3, "X")), (0.55, 0.04, 0.9), "dub")
    P.ball((hx + 0.7, 1.06, mz - 0.3), (0.26, 0.1, 0.42), "kuze", 10, 5)
    # kovadlina na spalku a kad na kaleni
    ax, az = hx + 2.3, hz + 0.2
    P.cyl(M((ax, 0.0, az)), 0.32, 0.3, 0.62, 12, "kura")
    P.bb((ax - 0.12, 0.62, az - 0.3), (ax + 0.12, 0.78, az + 0.22), "zelezo")
    P.bb((ax - 0.14, 0.78, az - 0.32), (ax + 0.14, 0.86, az + 0.3), "zelezo")
    P.mesh([Vector((ax - 0.1, 0.78, az + 0.3)), Vector((ax + 0.1, 0.78, az + 0.3)), Vector((ax + 0.1, 0.86, az + 0.3)),
            Vector((ax - 0.1, 0.86, az + 0.3)), Vector((ax, 0.84, az + 0.62))],
           [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)], "zelezo")
    P.cols.append((M((ax, 0.4, az)), (0.6, 0.8, 0.6)))
    PR.barrel(P, M((hx + 1.9, 0.0, hz + 1.5)), 0.38, 0.75, False)
    # police na naradi na zadni stene
    P.bb((x0 + 3.2, 1.5, ZW - 0.32), (x0 + 5.6, 1.56, ZW - 0.02), "deska")
    for k in range(7):
        x = x0 + 3.4 + 0.33 * k
        P.rod((x, 1.62, ZW - 0.05), (x + jit(0.04), 1.05 + jit(0.1), ZW - 0.07), 0.01, 5, "zelezo")
    # --- strop/krov
    lean_roof(W, x0, x1, ZW, y_hi + 0.15, z_lo, y_lo)
    W.beam((x0, ry(zf + 0.3) - 0.2, zf + 0.3), (x1, ry(zf + 0.3) - 0.2, zf + 0.3), 0.22, 0.24, "dub", j=0.5)
    W.beam((x0, y_hi - 0.1, ZW - 0.15), (x1, y_hi - 0.1, ZW - 0.15), 0.2, 0.2, "dub", j=0.5)
    P.commit(coll)
    W.commit(coll)


def stable(coll):
    """Dreveny staj pod zapadni hradbou: tri boxy, celo do nadvori s pulenymi dvermi, zlaby a jesle,
    pultova strecha svazita od hradby."""
    P = Part("Staj", bevel=0.012)
    W = Part("StajKrov", bevel=0.01)
    xb, xf = XW, XW + 4.6            # zadni stena = hradba, celo v x = xf
    z0, nbox, bw = -8.3, 3, 3.1
    z1 = z0 + nbox * bw
    y_hi, y_lo = 4.4, 2.55
    # sloupy cela, prahy a vaznice
    zs = [z0 + bw * i for i in range(nbox + 1)]
    for z in zs:
        P.beam((xf, -0.05, z), (xf, y_lo - 0.1, z), 0.22, 0.22, "dub_ven", j=1)
        P.lathe(M((xf, -0.02, z)), [(0.2, 0), (0.18, 0.12), (0.0, 0.12)], 8, "kvadr_sedy", phase=math.pi / 8)
        P.cols.append((M((xf, 1.3, z)), (0.22, 2.6, 0.22)))
        P.beam((xf, y_lo - 0.85, z + 0.12), (xf, y_lo - 0.2, z + 0.75), 0.12, 0.12, "dub_ven", j=0.6) if z < z1 else None
        P.beam((xf, y_lo - 0.85, z - 0.12), (xf, y_lo - 0.2, z - 0.75), 0.12, 0.12, "dub_ven", j=0.6) if z > z0 else None
    P.beam((xf, y_lo - 0.08, z0 - 0.3), (xf, y_lo - 0.08, z1 + 0.3), 0.22, 0.24, "dub_ven", j=0.5)
    # bocni a delici steny z prken (svisla prkna), nahore otevrene k vetrani
    for z in zs:
        y_top = y_lo - 0.3
        k = 0.0
        while k < xf - xb - 0.15:
            w = 0.22 + jit(0.03)
            x = xb + 0.1 + k
            ht = y_top + (y_hi - y_lo) * (1 - (x - xb) / (xf - xb)) * 0.6 if z in (z0, z1) else 1.6
            kit.plank(P, (x + w / 2, 0.0, z), (x + w / 2, ht, z), w - 0.01, 0.05, "prkna_ven", up=(0, 0, 1), wear=0.5, seg_len=0.5)
            k += w
        P.cols.append((M(((xb + xf) / 2, 0.9, z)), (xf - xb, 1.8, 0.1)))
    # boxy bez dvirek (kone uvazane): u zadni steny korytko na nozkach, nad nim sikme zebriny (zebrinove jesle)
    # se senem, kruh na uvazani
    for i in range(nbox):
        zc = z0 + bw * (i + 0.5)
        zl, zr = zc - 1.25, zc + 1.25
        # korytko z fosen
        for zz in (zl + 0.1, zr - 0.1):
            P.beam((xb + 0.55, 0.0, zz), (xb + 0.55, 0.62, zz), 0.1, 0.1, "dub", j=0.6)
        P.bb((xb + 0.1, 0.55, zl), (xb + 0.7, 0.6, zr), "deska")
        P.bb((xb + 0.66, 0.6, zl), (xb + 0.71, 0.82, zr), "deska", grain="z")
        P.bb((xb + 0.1, 0.6, zl), (xb + 0.15, 0.82, zr), "deska", grain="z")
        P.cols.append((M((xb + 0.4, 0.4, zc)), (0.65, 0.8, 2.5)))
        # zebriny: horni tram odsazeny od zdi, dolni u zdi nad korytkem, svisle prisazene pricle
        top_x, bot_x = xb + 0.85, xb + 0.12
        P.beam((top_x, 2.05, zl), (top_x, 2.05, zr), 0.1, 0.1, "dub", j=0.4)
        P.beam((bot_x, 1.0, zl), (bot_x, 1.0, zr), 0.1, 0.1, "dub", j=0.4)
        for zz in (zl, zr):
            P.beam((bot_x, 0.95, zz), (top_x, 2.1, zz), 0.08, 0.08, "dub", j=0.4)
        k = 0
        z = zl + 0.12
        while z < zr - 0.05:
            P.rod((bot_x, 1.0, z), (top_x, 2.05, z + kit.J(0.01)), 0.022, 6, "dub")
            z += 0.13
            k += 1
        # seno za zebrinami: stebla v trsech
        for _ in range(220):
            u = R.random()
            px = bot_x + (top_x - bot_x) * u - 0.12 - R.uniform(0, 0.15)
            py = 1.0 + 1.05 * u * R.uniform(0.3, 0.95)
            pz = R.uniform(zl + 0.1, zr - 0.1)
            a = R.uniform(0, math.pi)
            L = R.uniform(0.15, 0.4)
            d = Vector((math.cos(a) * 0.4, R.uniform(-0.5, 0.5), math.sin(a))).normalized() * L
            s_ = Vector((0, 0.004, 0)) if abs(d.y) < 0.9 else Vector((0.004, 0, 0))
            b = Vector((px, py, pz))
            P.face([b - s_, b + s_, b + d + s_, b + d - s_], "slama", uvs=[(0, 0), (0.01, 0), (0.01, L), (0, L)])
        # kruh na uvazani kone ve zdi
        c = Vector((xb + 0.04, 1.45, zc + 0.9))
        P.rod(c - Vector((0.04, 0, 0)), c + Vector((0.04, 0, 0)), 0.012, 5, "zelezo")
        pts = [c + Vector((0.05, -0.06 + 0.06 * math.cos(t), 0.06 * math.sin(t))) for t in [j / 10 * 2 * math.pi for j in range(11)]]
        for q0, q1 in zip(pts, pts[1:]):
            P.rod(q0, q1, 0.009, 5, "zelezo")
        # slama na podlaze
        for _ in range(70):
            px, pz = R.uniform(xb + 0.8, xf - 0.2), R.uniform(zc - 1.4, zc + 1.4)
            a = R.uniform(0, math.pi)
            L = R.uniform(0.15, 0.35)
            d = Vector((math.cos(a), 0.0, math.sin(a))) * L
            s_ = Vector((-math.sin(a), 0, math.cos(a))) * 0.005
            b = Vector((px, 0.035, pz))
            P.face([b - s_, b + s_, b + d + s_, b + d - s_], "slama", uvs=[(0, 0), (0.01, 0), (0.01, L), (0, L)])
    P.bb((xb, -0.2, z0), (xf, 0.02, z1), "prkna", collide=True)
    # strecha
    shingle_roof(W, (xf + 0.5, y_lo, z1 + 0.4), (xf + 0.5, y_lo, z0 - 0.4), (xb, y_hi, z0 - 0.4), (xb, y_hi, z1 + 0.4), ridge=False)
    x = xb + 0.2
    for z in zs + [z0 + bw * (i + 0.5) for i in range(nbox)]:
        W.beam((xb + 0.1, y_hi - 0.15, z), (xf + 0.45, y_lo - 0.12, z), 0.12, 0.16, "dub", j=0.8)
    W.beam((xb + 0.15, y_hi - 0.2, z0 - 0.3), (xb + 0.15, y_hi - 0.2, z1 + 0.3), 0.2, 0.2, "dub", j=0.5)
    P.commit(coll)
    W.commit(coll)


def manure(coll):
    """Hnojiste v rohu mezi kovarnou a stají (ohrazene prkny na kolech) a vuz."""
    P = Part("Hnojiste", bevel=0.01)
    cx, cz = XW + 2.4, 11.6
    w, d = 3.6, 3.0
    # ohrada ze tri stran, otevrena strana smerem ke staji (na sever)
    for (a, b) in (((cx - w / 2, cz + d / 2), (cx + w / 2, cz + d / 2)), ((cx + w / 2, cz - d / 2), (cx + w / 2, cz + d / 2)),
                   ((cx - w / 2, cz - d / 2), (cx - w / 2, cz + d / 2))):
        for k in range(3):
            y = 0.12 + 0.24 * k
            kit.plank(P, (a[0], y, a[1]), (b[0], y, b[1]), 0.22, 0.05, "prkna_ven", up=Vector((0, 0, 1)) if a[1] == b[1] else Vector((1, 0, 0)),
                      wear=0.8, seg_len=0.5)
        for p in (a, b):
            P.beam((p[0], -0.1, p[1]), (p[0], 0.85, p[1]), 0.12, 0.12, "dub_ven", j=1)
    for _ in range(9):
        P.ball((cx + jit(1.2), 0.15, cz + jit(1.0) + 0.2), (R.uniform(0.6, 1.0), R.uniform(0.3, 0.55), R.uniform(0.5, 0.8)), "hnuj", 10, 6)
    for _ in range(120):
        px, pz = cx + jit(1.6), cz + jit(1.3)
        a = R.uniform(0, math.pi)
        L = R.uniform(0.15, 0.35)
        dd = Vector((math.cos(a), R.uniform(0, 0.1), math.sin(a))) * L
        s = Vector((-math.sin(a), 0, math.cos(a))) * 0.005
        b = Vector((px, R.uniform(0.2, 0.55), pz))
        P.face([b - s, b + s, b + dd + s, b + dd - s], "slama", uvs=[(0, 0), (0.01, 0), (0.01, L), (0, L)])
    P.cols.append((M((cx, 0.4, cz)), (w, 0.8, d)))
    pitchfork(P, Vector((cx + 0.4, 0.35, cz + 0.2)), Vector((0.25, 1.0, -0.35)))
    wagon(P, M((XW + 3.4, 0.0, 6.6), 78))
    PR.chopping_block(P, (XW + 5.2, 0.0, 8.0))
    P.commit(coll)


def pitchfork(P: Part, tip: Vector, up: Vector):
    """Vidle zapichnute hroty do hnoje: tri kovane hroty, objimka, dreveny nasad."""
    u = up.normalized()
    side = u.cross(Vector((0, 0, 1)) if abs(u.z) < 0.9 else Vector((1, 0, 0))).normalized()
    head = tip + u * 0.32
    for sx in (-1, 0, 1):
        a = tip + side * (sx * 0.075)
        b = head + side * (sx * 0.035)
        P.rod(a, b, 0.008, 5, "zelezo", r1=0.012)
    P.rod(head - side * 0.04, head + side * 0.04, 0.012, 5, "zelezo")
    P.rod(head, head + u * 0.12, 0.022, 6, "zelezo", r1=0.018)
    P.rod(head + u * 0.1, head + u * 1.55, 0.018, 7, "dub")


def _wheel(P: Part, c: Vector, axis: Vector, r, spokes=12, w=0.07):
    """Dreveny paprskovy kolo: naboj, paprsky (mirne do kuzele), loukote z dilu, zelezna obruc."""
    a = axis.normalized()
    u = a.cross(Vector((0, 1, 0))).normalized()
    v = a.cross(u).normalized()
    from lib import frame
    hub_m = M(c, basis=frame(a, Vector((0, 1, 0))) @ Matrix.Rotation(-math.pi / 2, 3, "X"))
    P.lathe(hub_m @ M((0, -0.14, 0)), [(0.05, 0.0), (0.085, 0.04), (0.095, 0.14), (0.085, 0.24), (0.05, 0.28)], 10, "dub")
    P.rod(c - a * 0.18, c + a * 0.18, 0.03, 6, "zelezo")
    nseg = 24
    pts = [c + (u * math.cos(2 * math.pi * k / nseg) + v * math.sin(2 * math.pi * k / nseg)) * r for k in range(nseg + 1)]
    for p0, p1 in zip(pts, pts[1:]):
        P.beam(p0 - (p0 - c).normalized() * 0.03, p1 - (p1 - c).normalized() * 0.03, w, 0.06, "dub", up=a)
        P.beam(p0 + (p0 - c).normalized() * 0.005, p1 + (p1 - c).normalized() * 0.005, w + 0.01, 0.014, "zelezo", up=a)
    for k in range(spokes):
        t = 2 * math.pi * k / spokes
        d = u * math.cos(t) + v * math.sin(t)
        P.beam(c + d * 0.09 + a * 0.03, c + d * (r - 0.05), 0.035, 0.05, "dub", up=a)


def wagon(P: Part, m: Matrix):
    """Zebrinovy vuz (zebrinak): podelne tramy, prkenne dno, sikme zebrinove bocnice s pricli, dve napravy,
    paprskova kola (zadni vetsi), voj s rozvorou opreny o zem."""
    L, W_ = 3.4, 1.0
    yb = 0.78
    T = lambda p: m @ Vector(p)  # noqa: E731
    # podvozek
    for sx in (-1, 1):
        P.beam(T((sx * 0.38, yb - 0.1, -L / 2)), T((sx * 0.38, yb - 0.1, L / 2)), 0.1, 0.12, "dub_ven", j=0.6)
    P.beam(T((0, yb - 0.22, -L / 2 - 0.2)), T((0, yb - 0.22, L / 2 + 0.1)), 0.1, 0.1, "dub_ven", j=0.4)   # rozvora
    k = -L / 2
    while k < L / 2:
        pw = 0.24 + jit(0.03)
        kit.plank(P, T((-W_ / 2, yb - 0.02, k + pw / 2)), T((W_ / 2, yb - 0.02, k + pw / 2)), pw - 0.01, 0.04, "prkna_ven", up=m.to_3x3() @ Vector((0, 1, 0)),
                  wear=0.6, seg_len=0.4)
        k += pw
    # zebriny: sikme bocnice (horni tram vychyleny ven), svisle pricle
    for sx in (-1, 1):
        lo = sx * 0.45
        hi = sx * 0.78
        P.beam(T((lo, yb + 0.05, -L / 2 - 0.1)), T((lo, yb + 0.05, L / 2 + 0.1)), 0.07, 0.07, "dub_ven", j=0.4)
        P.beam(T((hi, yb + 0.72, -L / 2 - 0.25)), T((hi, yb + 0.72, L / 2 + 0.25)), 0.08, 0.08, "dub_ven", j=0.4)
        z = -L / 2 + 0.05
        while z <= L / 2:
            P.rod(T((lo, yb + 0.05, z)), T((hi, yb + 0.72, z)), 0.018, 5, "dub_ven")
            z += 0.26
        # opery (luchy) k naprave
        for zz in (-L / 2 + 0.4, L / 2 - 0.4):
            P.beam(T((sx * 0.5, yb - 0.2, zz)), T((hi * 0.95, yb + 0.6, zz)), 0.05, 0.05, "dub_ven")
    # celo a zadek: prkno
    for zz in (-L / 2, L / 2):
        kit.plank(P, T((-0.5, yb + 0.18, zz)), T((0.5, yb + 0.18, zz)), 0.26, 0.04, "prkna_ven", up=m.to_3x3() @ Vector((0, 0, 1)), wear=0.6)
    # napravy a kola
    ax = m.to_3x3() @ Vector((1, 0, 0))
    for zz, r in ((-L / 2 + 0.55, 0.43), (L / 2 - 0.5, 0.55)):
        P.beam(T((-0.8, r, zz)), T((0.8, r, zz)), 0.1, 0.1, "dub_ven", j=0.4)
        P.beam(T((0, r, zz)), T((0, yb - 0.16, zz)), 0.14, 0.1, "dub_ven")
        for sx in (-1, 1):
            _wheel(P, T((sx * 0.86, r, zz)), ax * sx, r)
    # voj (oj) s vahadlem, opreny o zem
    a = T((0, 0.45, -L / 2 + 0.55))
    b = T((0.15, 0.05, -L / 2 - 2.3))
    P.beam(a, b, 0.08, 0.08, "dub_ven", j=0.5)
    P.beam(b + ax * 0.45 + m.to_3x3() @ Vector((0, 0.04, 0.1)), b - ax * 0.45 + m.to_3x3() @ Vector((0, 0.04, 0.1)), 0.06, 0.06, "dub_ven")
    P.cols.append((m @ M((0, 0.7, 0)), (1.8, 1.4, L)))


def build(coll):
    forge_armory(coll)
    stable(coll)
    manure(coll)
