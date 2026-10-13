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
from lib import M, Part, R, fire, jit, light, shingle_roof, wall_x

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
    y_hi, y_lo = 5.3, 3.6
    z_lo = zf - 0.55
    slope = (y_hi - y_lo) / (ZW - z_lo)

    def ry(z):
        return y_lo + (z - z_lo) * slope
    # --- predni zed: kovarna s podloubim (2 vysoke oblouky), zbrojnice s dvermi a oknem
    arches = []
    span = (xm - x0 - 0.6) / 2
    for i in range(2):
        cx = x0 + 0.3 + span * (i + 0.5)
        arches.append((cx, 3.1))
    a_spring = 1.05
    a_top = kit.arch_top("lomeny", arches[0][1], a_spring)(0.0) + 0.52
    holes = [[cx - w / 2, cx + w / 2, 0.0, a_top] for cx, w in arches]
    # okno zbrojnice: ram z celistvych kamenu s kovanou mrizi
    wx, wy = -8.5, 1.2
    ox0, ox1, oy0, oy1 = kit.stone_window(P, M((wx, wy, zf), 180), 0.6, 0.85, t, "mriz")
    holes += [[-6.0, -4.9, 0.0, 2.1], [wx - ox1, wx - ox0, wy + oy0, wy + oy1]]
    wall_x(P, "zdivo_omitka", x0, x1, zf, zf + t, -0.3, ry(zf + t) - 0.02, holes)
    # lomene oblouky podloubi jako v Suchdole (hrube tesane klenaky po cele tloustce zdi)
    for cx, w in arches:
        kit.arcade(P, M((cx, 0.0, zf), 180), w, a_spring, t)
    kit.doorway(P, M((-5.45, 0.0, zf), 180), "obycejne", 1.1, 2.1, t, "segment", open_deg=0)

    # boky a delici zed (pod pultovou strechou); v delici zdi dvere mezi kovarnou a zbrojnici
    def side_wall(xa, za, zb, yb=-0.3):
        q = [Vector((xa, yb, za)), Vector((xa, yb, zb)), Vector((xa, ry(zb), zb)), Vector((xa, ry(za), za))]
        P.prism(q, Vector((t, 0, 0)), "zdivo_omitka")
        P.cols.append((M((xa + t / 2, (yb + ry(zb)) / 2, (za + zb) / 2)), (t, ry(zb) - yb, zb - za)))
    side_wall(x0, zf, ZW)
    side_wall(x1 - t, zf, ZW)
    dz0, dz1, dh = 11.05, 12.05, 2.05
    xp = xm - t / 2
    side_wall(xp, zf, dz0)
    side_wall(xp, dz1, ZW)
    side_wall(xp, dz0, dz1, dh)
    kit.doorway(P, M((xp, 0.0, (dz0 + dz1) / 2), -90), "obycejne", dz1 - dz0, dh, t, "segment", open_deg=0)
    F.quoins(P, x0, zf, 1, 1, 0.0, ry(zf), 0.6, 0.35, 0.3)
    F.quoins(P, x1, zf, -1, 1, 0.0, ry(zf), 0.6, 0.35, 0.3)
    # podlahy: kovarna udusana hlina s kocickami, zbrojnice prkna
    P.bb((x0 + t, -0.2, zf + t), (xm - t / 2, 0.02, ZW), "kocicky", collide=True)
    P.bb((xm + t / 2, -0.2, zf + t), (x1 - t, 0.04, ZW), "prkna", collide=True)
    # --- vybaveni kovarny (podle KCD: zdena vyhen s klenutou kapuci, mech na paku, kovadlina na spalku...)
    forge_interior(P, x0 + t, xm - t / 2, zf + t, ZW, ry)
    # --- strop/krov
    lean_roof(W, x0, x1, ZW, y_hi + 0.15, z_lo, y_lo)
    W.beam((x0, ry(zf + 0.3) - 0.2, zf + 0.3), (x1, ry(zf + 0.3) - 0.2, zf + 0.3), 0.22, 0.24, "dub", j=0.5)
    W.beam((x0, y_hi - 0.1, ZW - 0.15), (x1, y_hi - 0.1, ZW - 0.15), 0.2, 0.2, "dub", j=0.5)
    P.commit(coll)
    W.commit(coll)


# ======================================================================= kovarna

def _anvil(P: Part, c: Vector, yaw: float, s=1.0):
    """Kovadlina s rohem: patka se ctyrmi nozkami, zuzeny pas, telo s rovnou drahou, kuzelovy roh a ctyrhranna pata."""
    m = M(c, yaw)
    T = lambda x, y, z: m @ Vector((x * s, y * s, z * s))   # noqa: E731
    # patka a nozky
    P.mesh(*_frustum(T, 0.0, 0.1, (0.2, 0.15), (0.12, 0.09)), "zelezo")
    P.mesh(*_frustum(T, 0.1, 0.24, (0.12, 0.09), (0.075, 0.06)), "zelezo")
    P.mesh(*_frustum(T, 0.24, 0.3, (0.075, 0.06), (0.17, 0.08)), "zelezo")
    # telo s drahou
    P.mesh(*_frustum(T, 0.3, 0.36, (0.17, 0.08), (0.2, 0.085)), "zelezo")
    # roh: kuzel do spicky (lokalne +x), mirne zahnuty dolu
    ring = []
    for k in range(10):
        a = 2 * math.pi * k / 10
        ring.append((math.cos(a), math.sin(a)))
    verts = []
    faces = []
    secs = [(0.2, 0.33, 0.07), (0.3, 0.325, 0.058), (0.4, 0.315, 0.044), (0.5, 0.3, 0.028), (0.6, 0.285, 0.012), (0.66, 0.275, 0.0)]
    for i, (x, y, r) in enumerate(secs):
        for cy, cz in ring:
            verts.append(T(x, y + cy * r * 0.9, cz * r))
    for i in range(len(secs) - 1):
        for k in range(10):
            a0, a1 = i * 10 + k, i * 10 + (k + 1) % 10
            faces.append((a0, a1, a1 + 10, a0 + 10))
    P.mesh(verts, faces, "zelezo")
    # pata s otvorem
    P.box(m @ M((-0.25 * s, 0.33 * s, 0)), (0.12 * s, 0.05 * s, 0.13 * s), "zelezo")


def _frustum(T, y0, y1, a, b):
    """Komolý jehlan (obdelnik a dole, b nahore) -> (verts, faces) v lokalnich souradnicich prevedenych T."""
    v = []
    for (hx, hz), y in ((a, y0), (b, y1)):
        for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            v.append(T(sx * hx, y, sz * hz))
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return v, f


def _tongs(P: Part, top: Vector, ang=0.0, L=0.6):
    """Kovarske kleste visici na hacku: dve ramena prekrizena v cepu, kratke celisti."""
    for s in (-1, 1):
        a = top + Vector((s * 0.02, 0, 0))
        mid = top + Vector((s * -0.012, -L * 0.78, 0))
        jaw = mid + Vector((s * 0.03, -L * 0.22, 0.01))
        P.rod(a, mid, 0.008, 5, "zelezo")
        P.rod(mid, jaw, 0.011, 5, "zelezo")
    P.ball(top + Vector((0, -L * 0.78, 0)), (0.016, 0.016, 0.016), "zelezo", 6, 4)


def _hammer(P: Part, c: Vector, d: Vector, L=0.42, head=0.13):
    """Kladivo: topurko ve smeru d (od rukojeti k hlave), hlava kolmo."""
    d = d.normalized()
    top = c + d * L
    P.rod(c, top, 0.016, 6, "dub")
    side = d.cross(Vector((0, 0, 1))) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    side.normalize()
    P.rod(top - side * head * 0.45, top + side * head * 0.55, 0.026, 8, "zelezo")


def _bellows(P: Part, W: Part, c: Vector, nozzle_to: Vector):
    """Velky kozeny mech (kapkovity tvar, delka podel +x) na kozlich a paka na sloupku s retezem."""
    L, wmax = 1.5, 0.75
    def outline(y):
        pts = []
        for i in range(12):
            t = i / 11
            w = wmax * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.8 * (1 - 0.65 * t) + 0.08
            pts.append((c.x + t * L, y, c.z + w / 2))
        for i in range(11, -1, -1):
            t = i / 11
            w = wmax * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.8 * (1 - 0.65 * t) + 0.08
            pts.append((c.x + t * L, y, c.z - w / 2))
        return [Vector(p) for p in pts]
    lo, hi = c.y, c.y + 0.32
    for y in (lo, hi):
        P.prism(outline(y), Vector((0, 0.035, 0)), "dub")
    # kuze mezi deskami (prohnuta)
    o0, o1 = outline(lo + 0.035), outline(hi)
    for i in range(len(o0)):
        j = (i + 1) % len(o0)
        mid0 = (o0[i] + o1[i]) / 2
        mid1 = (o0[j] + o1[j]) / 2
        ctr = Vector((c.x + L * 0.4, mid0.y, c.z))
        b0 = mid0 + (mid0 - ctr).normalized() * 0.07
        b1 = mid1 + (mid1 - ctr).normalized() * 0.07
        P.face([o0[i], o0[j], b1, b0], "kuze")
        P.face([b0, b1, o1[j], o1[i]], "kuze")
    # hubice do vyhne
    P.rod(Vector((c.x + L, lo + 0.18, c.z)), nozzle_to, 0.035, 8, "zelezo")
    # kozy
    for t in (0.2, 0.75):
        x = c.x + L * t
        for sz in (-1, 1):
            P.beam((x, 0.0, c.z + sz * 0.3), (x, lo, c.z + sz * 0.12), 0.07, 0.07, "dub", j=0.5)
        P.beam((x, lo - 0.04, c.z - 0.3), (x, lo - 0.04, c.z + 0.3), 0.08, 0.06, "dub")
    # sloupek s pakou a retez k horni desce
    px = c.x + L * 0.35
    pz = c.z - 0.75
    W.beam((px, 0.0, pz), (px, 2.3, pz), 0.16, 0.16, "dub", j=0.8)
    a = Vector((px - 1.1, 2.0, pz + 0.75))
    b = Vector((px + 1.2, 2.45, pz + 0.75))
    W.beam(Vector((px, 2.25, pz)), Vector((px, 2.25, pz + 0.75)), 0.1, 0.1, "dub")
    W.beam(a, b, 0.09, 0.11, "dub", j=0.6)
    kit.chain(W, a + Vector((0.3, -0.03, 0)), Vector((c.x + 0.45, hi + 0.04, c.z)), link=0.07, wire=0.009, sag=0.02)
    kit.chain(W, b + Vector((-0.05, -0.03, 0)), b + Vector((-0.05, -0.9, 0)), link=0.07, wire=0.009, sag=0.0)


def forge_interior(P: Part, xa, xb, za, zb, ry):
    """Vnitrek kovarny (x od zapadni steny xa po delici zed xb, z od predni zdi za po hradbu zb)."""
    W = P   # vse v jednom dilu
    # --- vyhen u zapadni steny: zdeny stul z kamenu, na nem ohniste s uhlim a zharem,
    #     nad nim klenuta kamenna kapuce prechazejici v komin
    hz = 11.3
    hw, hd, hh = 1.9, 1.25, 0.82          # sirka (z), hloubka (x), vyska stolu
    y = 0.0
    while y < hh - 0.02:
        h = min(R.uniform(0.2, 0.28), hh - y)
        z = hz - hw / 2
        while z < hz + hw / 2 - 0.05:
            ln = min(R.uniform(0.32, 0.55), hz + hw / 2 - z)
            kit.stone(P, M((xa + hd - 0.12, y + h / 2, z + ln / 2)), (0.26, h - 0.01, ln - 0.01), "kvadr_sedy", cham=0.03, rough=0.015)
            z += ln
        y += h
    P.bb((xa, 0.0, hz - hw / 2), (xa + hd - 0.24, hh - 0.02, hz + hw / 2), "zdivo_hole", collide=True)
    P.cols.append((M((xa + hd / 2, hh / 2, hz)), (hd, hh, hw)))
    # kryci desky stolu a ohniste
    kit.stone(P, M((xa + hd - 0.12, hh + 0.05, hz)), (0.3, 0.1, hw + 0.08), "kvadr_sedy", cham=0.02)
    P.bb((xa + 0.15, hh - 0.04, hz - 0.55), (xa + hd - 0.28, hh + 0.05, hz + 0.55), "uhli")
    P.ball(Vector((xa + 0.6, hh + 0.06, hz)), (0.3, 0.06, 0.35), "zhar", 12, 4)
    for k in range(14):
        P.ball(Vector((xa + 0.6 + jit(0.35), hh + 0.07, hz + jit(0.42))), (0.06, 0.035, 0.05), "uhli", 6, 4)
    fire("forge", (xa + 0.6, hh + 0.1, hz), name="vyhen")
    # klenuta kapuce: dva boky z kamene, klenba nad ohnistem (lomeny oblouk), nad ni stupnovity komin
    ky = hh + 0.05
    spring = 1.75
    for sz in (-1, 1):
        y = ky
        while y < spring - 0.02:
            h = min(R.uniform(0.24, 0.32), spring - y)
            kit.stone(P, M((xa + hd * 0.5, y + h / 2, hz + sz * (hw / 2 - 0.15))), (hd - 0.05, h - 0.01, 0.3), "kvadr_sedy", cham=0.035, rough=0.015)
            y += h
    kit.stone_arch(P, M((xa + hd - 0.05, 0.0, hz), 90), hw - 0.6, spring, "lomeny", hd - 0.1, "kvadr_sedy", ring=0.3, proud=0.04, n=11)
    top = spring + (hw - 0.6) / 2 * 1.35 * 0.9
    # cvikly a stena kapuce nad obloukem az ke stropu, komin nad strechu
    P.bb((xa, spring, hz - hw / 2), (xa + hd - 0.12, top + 0.55, hz + hw / 2), "zdivo_hole", collide=False)
    P.slab((xa, top + 0.55, hz - hw / 2), (xa + hd - 0.12, top + 0.55, hz - hw / 2), (xa + 0.75, ry(hz) - 0.2, hz - 0.45),
           (xa, ry(hz) - 0.2, hz - 0.45), 0.12, "zdivo_hole")
    P.slab((xa + hd - 0.12, top + 0.55, hz + hw / 2), (xa, top + 0.55, hz + hw / 2), (xa, ry(hz) - 0.2, hz + 0.45),
           (xa + 0.75, ry(hz) - 0.2, hz + 0.45), 0.12, "zdivo_hole")
    P.slab((xa + hd - 0.12, top + 0.55, hz - hw / 2), (xa + hd - 0.12, top + 0.55, hz + hw / 2), (xa + 0.75, ry(hz) - 0.2, hz + 0.45),
           (xa + 0.75, ry(hz) - 0.2, hz - 0.45), 0.12, "zdivo_hole")
    P.bb((xa, ry(hz) - 0.25, hz - 0.45), (xa + 0.75, ry(hz) + 1.7, hz + 0.45), "zdivo_hole", collide=True)
    P.bb((xa - 0.05, ry(hz) + 1.7, hz - 0.5), (xa + 0.8, ry(hz) + 1.82, hz + 0.5), "kvadr_sedy")
    # kovany hak a kleste na boku vyhne
    for k in range(3):
        _tongs(P, Vector((xa + hd + 0.02, 1.55, hz + hw / 2 + 0.1 + 0.12 * k)) + Vector((0, 0, 0)), L=0.55 + 0.05 * k)
    # --- mech na pravo od vyhne (smer do nadvori), hubice do ohniste
    _bellows(P, W, Vector((xa + 0.15, 0.62, hz - hw / 2 - 0.55)), Vector((xa + 0.45, hh + 0.05, hz - 0.55)))
    # --- kovadlina na mohutnem spalku pred vyhni
    sx, sz = xa + hd + 1.25, hz + 0.1
    P.lathe(M((sx, 0.0, sz)), [(0.0, 0.0), (0.42, 0.0), (0.44, 0.08), (0.41, 0.55), (0.43, 0.62), (0.0, 0.62)], 18, "kura")
    for yb in (0.15, 0.48):
        P.lathe(M((sx, yb, sz)), [(0.43, 0.0), (0.43, 0.04)], 18, "zelezo", False, False)
    _anvil(P, Vector((sx, 0.62, sz)), 90 + jit(10), 1.15)
    P.cols.append((M((sx, 0.5, sz)), (0.85, 1.0, 0.85)))
    # druha mala kovadlina (rohatina) na spalku stranou a kad na kaleni
    P.lathe(M((sx + 0.9, 0.0, sz + 1.2)), [(0.0, 0.0), (0.24, 0.0), (0.25, 0.5), (0.0, 0.5)], 12, "kura")
    _anvil(P, Vector((sx + 0.9, 0.5, sz + 1.2)), jit(20), 0.6)
    PR.barrel(P, M((xa + hd + 0.5, 0.0, hz + hw / 2 + 0.75)), 0.42, 0.55, False)
    P.cyl(M((xa + hd + 0.5, 0.47, hz + hw / 2 + 0.75)), 0.38, 0.38, 0.004, 16, "voda")
    P.cols.append((M((xa + hd + 0.5, 0.3, hz + hw / 2 + 0.75)), (0.85, 0.6, 0.85)))
    # kladiva u kovadliny
    _hammer(P, Vector((sx + 0.28, 0.63, sz - 0.25)), Vector((-0.2, 0.02, 1)), 0.38, 0.12)
    _hammer(P, Vector((sx - 0.4, 0.0, sz - 0.5)), Vector((0, 1, 0.05)), 0.7, 0.18)
    # --- zadni stena (hradba): stojan s naradim, police, tyc s retezy a obrucemi
    rx0 = xa + 2.0
    P.beam((rx0, 1.75, zb - 0.06), (rx0 + 2.6, 1.75, zb - 0.06), 0.08, 0.06, "dub", j=0.5)
    for k in range(6):
        _tongs(P, Vector((rx0 + 0.2 + 0.22 * k, 1.75, zb - 0.12)), L=0.5 + 0.06 * (k % 3))
    for k in range(4):
        _hammer(P, Vector((rx0 + 1.65 + 0.24 * k, 1.75, zb - 0.12)), Vector((0, -1, 0)), 0.4 + 0.05 * k, 0.12)
    P.bb((rx0 + 2.8, 1.25, zb - 0.38), (rx0 + 4.4, 1.29, zb - 0.02), "deska")
    P.bb((rx0 + 2.8, 1.75, zb - 0.38), (rx0 + 4.4, 1.79, zb - 0.02), "deska")
    for xx in (rx0 + 2.85, rx0 + 4.35):
        P.beam((xx, 0.0, zb - 0.35), (xx, 1.85, zb - 0.35), 0.06, 0.06, "dub")
    for k in range(5):
        P.cyl(M((rx0 + 3.0 + 0.3 * k, 1.29, zb - 0.2)), 0.06 + jit(0.02), 0.06, 0.12 + jit(0.04), 8, "hlina_dzban")
    # tyc pod stropem s retezy a obrucemi
    py_ = ry(zb - 1.2) - 0.45
    P.beam((xa + 2.6, py_, zb - 1.2), (xb - 0.4, py_, zb - 1.2), 0.08, 0.08, "dub", j=0.5)
    for k in range(5):
        x = xa + 3.0 + 0.9 * k
        kit.chain(P, Vector((x, py_ - 0.03, zb - 1.2)), Vector((x + 0.25, py_ - 0.8 - 0.2 * (k % 2), zb - 1.15)), link=0.06, wire=0.008, sag=0.05)
        P.lathe(M((x + 0.45, py_ - 0.25, zb - 1.2)) @ Matrix.Rotation(math.pi / 2, 4, "X"),
                [(0.28 + 0.04 * (k % 3), -0.012), (0.3 + 0.04 * (k % 3), 0.0), (0.28 + 0.04 * (k % 3), 0.012)], 18, "zelezo", False, False)
    # stojan na zelezne tyce u delici zdi
    for k in range(9):
        x = xb - 0.35 - 0.05 * (k % 3)
        z = zb - 0.6 - 0.12 * k
        P.rod((x, 0.0, z), (x - 0.08 + jit(0.05), 1.5 + jit(0.25), z + jit(0.05)), 0.014, 5, "zelezo")
    P.beam((xb - 0.45, 1.1, zb - 0.5), (xb - 0.45, 1.1, zb - 1.7), 0.06, 0.06, "dub")
    # --- brus: kamenne kolo v drevenem kozlu, korytko s vodou a klika
    gx, gz = xb - 1.6, zb - 1.15
    for sz2 in (-1, 1):
        P.beam((gx - 0.7, 0.0, gz + sz2 * 0.22), (gx - 0.4, 0.55, gz + sz2 * 0.22), 0.07, 0.07, "dub", j=0.6)
        P.beam((gx + 0.7, 0.0, gz + sz2 * 0.22), (gx + 0.4, 0.55, gz + sz2 * 0.22), 0.07, 0.07, "dub", j=0.6)
        P.beam((gx - 0.75, 0.55, gz + sz2 * 0.22), (gx + 0.75, 0.55, gz + sz2 * 0.22), 0.08, 0.08, "dub", j=0.5)
    P.lathe(M((gx, 0.86, gz)) @ Matrix.Rotation(math.pi / 2, 4, "X") @ M((0, -0.07, 0)),
            [(0.04, 0.0), (0.42, 0.0), (0.44, 0.02), (0.44, 0.12), (0.42, 0.14), (0.04, 0.14)], 24, "kvadr_sedy")
    P.rod((gx, 0.86, gz - 0.35), (gx, 0.86, gz + 0.38), 0.025, 6, "zelezo")
    P.rod((gx, 0.86, gz + 0.38), (gx, 0.62, gz + 0.38), 0.02, 6, "zelezo")
    P.rod((gx, 0.62, gz + 0.38), (gx, 0.62, gz + 0.55), 0.028, 6, "dub")
    P.bb((gx - 0.5, 0.36, gz - 0.16), (gx + 0.5, 0.5, gz + 0.16), "dub")
    P.cols.append((M((gx, 0.6, gz)), (1.5, 1.2, 0.6)))
    # --- ponk s naradim u predni zdi
    bx0 = xa + 0.4
    bz = za + 0.45
    P.bb((bx0, 0.8, bz - 0.35), (bx0 + 2.0, 0.88, bz + 0.35), "deska", collide=True)
    for xx in (bx0 + 0.12, bx0 + 1.88):
        for zz in (bz - 0.28, bz + 0.28):
            P.beam((xx, 0.0, zz), (xx, 0.8, zz), 0.09, 0.09, "dub", j=0.6)
    P.beam((bx0 + 0.12, 0.25, bz), (bx0 + 1.88, 0.25, bz), 0.07, 0.07, "dub")
    _hammer(P, Vector((bx0 + 0.5, 0.9, bz)), Vector((1, 0.02, 0.2)), 0.35, 0.1)
    _tongs(P, Vector((bx0 + 1.2, 0.9, bz - 0.1)), L=0.5)
    for k in range(4):
        P.rod((bx0 + 1.4 + 0.07 * k, 0.9, bz + 0.1), (bx0 + 1.43 + 0.07 * k, 0.9, bz - 0.2), 0.012, 5, "zelezo")
    PR.bucket(P, Vector((bx0 + 2.3, 0.0, bz + 0.1)), True)


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
    """Zebrinak (selsky vuz na seno a snopy): dva podvozky s oplenem, rozvora, na oplenech dno z prken,
    sikme zebriny (silne zerdi s pricli), klanice na koncich oplenu drzi zebriny, luchy od naprav k horni zerdi,
    zebrinova cela vpredu a vzadu, oj s hounky a vahami, paprskova kola s okovanym nabojem."""
    L = 3.6                       # delka zebrin
    yb = 0.82                     # vyska dna
    T = lambda p: m @ Vector(p)  # noqa: E731
    up = m.to_3x3() @ Vector((0, 1, 0))
    ax = m.to_3x3() @ Vector((1, 0, 0))
    fz, rz = -L / 2 + 0.6, L / 2 - 0.55          # predni a zadni naprava
    fr, rr = 0.42, 0.56                            # polomery kol
    # --- napravy (drevene s okovanymi konci), oplenky nad nimi, rozvora
    for zz, r in ((fz, fr), (rz, rr)):
        P.beam(T((-0.82, r, zz)), T((0.82, r, zz)), 0.11, 0.12, "dub_ven", j=0.4)
        for sx in (-1, 1):
            P.rod(T((sx * 0.62, r, zz)), T((sx * 0.7, r, zz)), 0.065, 8, "zelezo")
        P.beam(T((-0.66, yb - 0.17, zz)), T((0.66, yb - 0.17, zz)), 0.14, 0.13, "dub_ven", j=0.5)   # oplen
        P.beam(T((0, r + 0.06, zz)), T((0, yb - 0.23, zz)), 0.12, 0.1, "dub_ven")                 # podlozka
        for sx in (-1, 1):
            _wheel(P, T((sx * 0.86, r, zz)), ax * sx, r, 10 if r < 0.5 else 12)
    P.beam(T((0, yb - 0.27, fz - 0.25)), T((0, yb - 0.27, rz + 0.45)), 0.11, 0.11, "dub_ven", j=0.4)   # rozvora
    P.rod(T((0, yb - 0.4, fz)), T((0, yb - 0.05, fz)), 0.025, 6, "zelezo")                            # ojnik (cep)
    # hounky: vidlice od predni napravy k oji
    for sx in (-1, 1):
        P.beam(T((sx * 0.45, fr + 0.02, fz + 0.15)), T((sx * 0.08, fr - 0.06, fz - 0.75)), 0.06, 0.07, "dub_ven", j=0.5)
    # --- dno: podelne trámky na oplenech a prkna napric
    for sx in (-1, 1):
        P.beam(T((sx * 0.36, yb - 0.08, -L / 2 + 0.15)), T((sx * 0.36, yb - 0.08, L / 2 - 0.1)), 0.09, 0.1, "dub_ven", j=0.5)
    k = -L / 2 + 0.15
    while k < L / 2 - 0.12:
        pw = min(0.22 + jit(0.03), L / 2 - 0.1 - k)
        kit.plank(P, T((-0.47, yb - 0.01, k + pw / 2)), T((0.47, yb - 0.01, k + pw / 2)), pw - 0.012, 0.035, "prkna_ven",
                  up=up, wear=0.7, seg_len=0.35)
        k += pw
    # --- zebriny: dolni a horni zerd (oble, oloupane), pricle; horni zerd vyklonena ven a presahuje dopredu i dozadu
    for sx in (-1, 1):
        lo = Vector((sx * 0.47, yb + 0.04, 0))
        hi = Vector((sx * 0.86, yb + 0.86, 0))
        P.rod(T((lo.x, lo.y, -L / 2 + 0.05)), T((lo.x, lo.y, L / 2 - 0.02)), 0.045, 8, "dub_ven")
        P.rod(T((hi.x, hi.y, -L / 2 - 0.35)), T((hi.x, hi.y + 0.03, L / 2 + 0.3)), 0.05, 8, "dub_ven")
        z = -L / 2 + 0.12
        while z < L / 2 - 0.05:
            P.rod(T((lo.x, lo.y, z)), T((hi.x, hi.y, z + jit(0.015))), 0.02, 6, "dub_ven")
            z += 0.2
        # klanice: na koncich oplenu, sikmo podel zebriny, nahore zelezny kruh kolem horni zerdi
        for zz in (fz, rz):
            base = T((sx * 0.6, yb - 0.17, zz + 0.1))
            top = T((hi.x * 1.04, hi.y + 0.1, zz + 0.1))
            P.beam(base, top, 0.07, 0.08, "dub_ven", j=0.6)
            P.rod(T((hi.x * 1.02, hi.y - 0.06, zz + 0.1)), T((hi.x * 1.02, hi.y + 0.06, zz + 0.1)), 0.06, 8, "zelezo")
        # luchy: od konce napravy k horni zerdi (opora zebriny)
        for zz, r in ((fz, fr), (rz, rr)):
            P.beam(T((sx * 0.74, r + 0.02, zz - 0.18)), T((hi.x * 0.98, hi.y - 0.02, zz - 0.42)), 0.05, 0.055, "dub_ven", j=0.6)
            P.rod(T((sx * 0.74, r + 0.02, zz - 0.18)), T((sx * 0.74, r + 0.1, zz - 0.18)), 0.03, 6, "zelezo")
    # --- cela: vpredu a vzadu nizky zebrinovy ram (rozsiruje se nahoru stejne jako zebriny)
    for zz in (-L / 2 + 0.12, L / 2 - 0.1):
        P.beam(T((-0.47, yb + 0.06, zz)), T((0.47, yb + 0.06, zz)), 0.06, 0.07, "dub_ven")
        P.rod(T((-0.72, yb + 0.6, zz)), T((0.72, yb + 0.6, zz)), 0.035, 7, "dub_ven")
        for k in range(6):
            x0 = -0.4 + 0.16 * k
            P.rod(T((x0, yb + 0.06, zz)), T((x0 * 1.6, yb + 0.6, zz)), 0.017, 5, "dub_ven")
    # --- oj s vahami, oprena o zem; retez s petlici na zavirani kola
    a_ = T((0, fr - 0.04, fz - 0.7))
    b_ = T((0.12, 0.06, fz - 3.0))
    P.beam(a_, b_, 0.085, 0.085, "dub_ven", j=0.5)
    P.rod(b_, b_ + (b_ - a_).normalized() * 0.1, 0.05, 6, "zelezo")
    vm = a_.lerp(b_, 0.35)
    P.beam(vm + ax * 0.55 + up * 0.08, vm - ax * 0.55 + up * 0.08, 0.06, 0.07, "dub_ven", j=0.4)
    for sx in (-1, 1):
        P.rod(vm + ax * (sx * 0.5) + up * 0.08, vm + ax * (sx * 0.5) + up * 0.08 + (b_ - a_).normalized() * 0.12, 0.012, 5, "zelezo")
    kit.chain(P, T((0.7, yb - 0.12, rz - 0.3)), T((0.82, rr + 0.25, rz - 0.15)), link=0.06, wire=0.008, sag=0.06)
    P.cols.append((m @ M((0, 0.75, 0)), (1.9, 1.5, L)))


def build(coll):
    forge_armory(coll)
    stable(coll)
    manure(coll)
