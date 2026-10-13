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
    zf, t = 9.0, 0.6                          # predni zed (lic do nadvori v z = zf)
    y_hi, y_lo = 5.0, 3.05
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
    holes = [[cx - w / 2, cx + w / 2, 0.0, 2.32] for cx, w in arches]
    holes += [[-6.0, -4.9, 0.0, 2.1], [-8.9, -8.1, 1.15, 2.15]]
    wall_x(P, "zdivo_omitka", x0, x1, zf, zf + t, -0.3, ry(zf + t) - 0.02, holes)
    for cx, w in arches:
        kit.doorway(P, M((cx, 0.0, zf), 180), "obycejne", w, 2.32, t, "segment", leaf=False)
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
    # pulene dvere v kazdem boxu (spodni kridlo zavrene, horni otevrene) + zabradli nad nimi
    for i in range(nbox):
        zc = z0 + bw * (i + 0.5)
        P.beam((xf, 1.25, z0 + bw * i + 0.1), (xf, 1.25, z0 + bw * (i + 1) - 0.1), 0.1, 0.12, "dub_ven")
        for j in range(5):
            zz = zc - 1.2 + 0.6 * j
            kit.plank(P, (xf + 0.02, 0.1, zz), (xf + 0.02, 1.2, zz), 0.58, 0.05, "prkna_ven", up=(1, 0, 0), wear=0.6, seg_len=0.4)
        P.beam((xf + 0.07, 0.4, zc - 1.25), (xf + 0.07, 0.4, zc + 1.25), 0.03, 0.12, "dub_ven")
        P.beam((xf + 0.07, 0.95, zc - 1.25), (xf + 0.07, 0.95, zc + 1.25), 0.03, 0.12, "dub_ven")
        P.cols.append((M((xf, 0.65, zc)), (0.12, 1.3, bw - 0.2)))
        # jesle a zlab u zadni steny, slama na zemi
        P.beam((xb + 0.35, 0.75, zc - 1.2), (xb + 0.35, 0.75, zc + 1.2), 0.5, 0.35, "dub", j=0.6)
        for j in range(9):
            zz = zc - 1.1 + 0.275 * j
            P.rod((xb + 0.15, 1.1, zz), (xb + 0.65, 1.8, zz), 0.02, 5, "dub")
        P.beam((xb + 0.62, 1.8, zc - 1.2), (xb + 0.62, 1.8, zc + 1.2), 0.06, 0.06, "dub")
        PR.hay_pile(P, (xb + 0.3, 1.0, zc), 0.6)
        for _ in range(60):
            px, pz = R.uniform(xb + 0.4, xf - 0.2), R.uniform(zc - 1.4, zc + 1.4)
            a = R.uniform(0, math.pi)
            L = R.uniform(0.15, 0.35)
            d = Vector((math.cos(a), 0.0, math.sin(a))) * L
            s = Vector((-math.sin(a), 0, math.cos(a))) * 0.005
            b = Vector((px, 0.035, pz))
            P.face([b - s, b + s, b + d + s, b + d - s], "slama", uvs=[(0, 0), (0.01, 0), (0.01, L), (0, L)])
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
    for (a, b) in (((cx - w / 2, cz - d / 2), (cx + w / 2, cz - d / 2)), ((cx + w / 2, cz - d / 2), (cx + w / 2, cz + d / 2)),
                   ((cx - w / 2, cz - d / 2), (cx - w / 2, cz + d / 2))):
        for k in range(3):
            y = 0.12 + 0.24 * k
            kit.plank(P, (a[0], y, a[1]), (b[0], y, b[1]), 0.22, 0.05, "prkna_ven", up=Vector((0, 0, 1)) if a[1] == b[1] else Vector((1, 0, 0)),
                      wear=0.8, seg_len=0.5)
        for p in (a, b):
            P.beam((p[0], -0.1, p[1]), (p[0], 0.85, p[1]), 0.12, 0.12, "dub_ven", j=1)
    for _ in range(9):
        P.ball((cx + jit(1.2), 0.15, cz + jit(1.0) + 0.3), (R.uniform(0.6, 1.0), R.uniform(0.3, 0.55), R.uniform(0.5, 0.8)), "hnuj", 10, 6)
    for _ in range(120):
        px, pz = cx + jit(1.6), cz + jit(1.3)
        a = R.uniform(0, math.pi)
        L = R.uniform(0.15, 0.35)
        dd = Vector((math.cos(a), R.uniform(0, 0.1), math.sin(a))) * L
        s = Vector((-math.sin(a), 0, math.cos(a))) * 0.005
        b = Vector((px, R.uniform(0.2, 0.55), pz))
        P.face([b - s, b + s, b + dd + s, b + dd - s], "slama", uvs=[(0, 0), (0.01, 0), (0.01, L), (0, L)])
    P.cols.append((M((cx, 0.4, cz)), (w, 0.8, d)))
    PR.cart(P, M((XW + 3.0, 0.0, 6.8), 75))
    PR.chopping_block(P, (XW + 5.2, 0.0, 8.0))
    P.commit(coll)


def build(coll):
    forge_armory(coll)
    stable(coll)
    manure(coll)
