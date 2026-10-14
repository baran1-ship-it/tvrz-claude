"""Vesnice asi kilometr od tvrze: navesni ves se zelenou navsi, rybnickem a studnou, kolem osm usedlosti.
Usedlost: roubena chalupa (otesane tramy na kamenne podezdivce, spary vymazane hlinou, mala okenka s okenicemi,
nekdy obilena), stit z prken, strecha sindelova sedlova nebo doskova / slamena s valbou; za ni chlev z prken,
laťkovy plot do navsi s vraty se strisekou, zahradka se zelim a kvetinami, hranice dreva. U vjezdu krcma s vencem.
Souradnice hry (x, y, z), y nahoru; ruzne usedlosti se lisi nahodou (pevne semeno)."""
import math
import random

from mathutils import Vector

import kraj
import props as PR
from lib import M, Part, frame

R = random.Random(1393)


def _land(x, z):
    import fort
    return fort.land(x, z)


class Frame:
    """Mistni souradnice stavby: u podel osy (hreben), v napric, y nahoru od podlahy (y0)."""

    def __init__(self, c, yaw, y0):
        self.c = Vector((c[0], 0.0, c[1]))
        self.au = Vector((math.cos(yaw), 0.0, math.sin(yaw)))
        self.av = Vector((-math.sin(yaw), 0.0, math.cos(yaw)))
        self.y0 = y0

    def p(self, u, y, v):
        return self.c + self.au * u + self.av * v + Vector((0.0, self.y0 + y, 0.0))

    def basis(self):
        from mathutils import Matrix
        return Matrix((self.au, Vector((0, 1, 0)), self.av)).transposed()


def _ground_span(F: Frame, L, W):
    ys = [_land(*(F.c + F.au * u + F.av * v).xz) for u in (-L / 2, 0, L / 2) for v in (-W / 2, 0, W / 2)]
    return min(ys), max(ys)


# ------------------------------------------------------------------ steny z otesanych tramu

LOG_H = 0.26
LOG_W = 0.2


def _intervals(s0, s1, y_a, y_b, holes):
    """Useky steny mezi otvory v rade tramu [y_a, y_b]: holes = [(s0, s1, ya, yb)]."""
    cut = sorted((a, b) for a, b, ya, yb in holes if ya < y_b - 0.02 and yb > y_a + 0.02)
    out, s = [], s0
    for a, b in cut:
        if a > s + 0.05:
            out.append((s, a))
        s = max(s, b)
    if s1 > s + 0.05:
        out.append((s, s1))
    return out


def log_wall(P: Part, F: Frame, axis, off, s0, s1, y_bot, y_top, holes, phase, mat):
    """Roubena stena: axis 'u' (podelna, v = off) nebo 'v' (stitova, u = off). Tramy po LOG_H,
    na sousednich stenach posunute o pul tramu (nahodne zhlavi pres roh)."""
    k = 0
    y = y_bot + (LOG_H * 0.5 if phase else 0.0)
    while y + LOG_H * 0.5 < y_top + 0.01:
        ya, yb = y, y + LOG_H - 0.022
        for a, b in _intervals(s0, s1, ya, yb, holes):
            if axis == "u":
                pa, pb = F.p(a, (ya + yb) / 2, off), F.p(b, (ya + yb) / 2, off)
            else:
                pa, pb = F.p(off, (ya + yb) / 2, a), F.p(off, (ya + yb) / 2, b)
            P.beam(pa, pb, LOG_W + R.uniform(-0.015, 0.02), yb - ya, mat, j=0.8)
        y += LOG_H
        k += 1


def window(P: Part, F: Frame, axis, off, s, y, w=0.55, h=0.5, out=1.0, shutter=True):
    """Okenko v roubene stene: ram z fosen, tma za nim, jedna okenice otevrena ke stene."""
    def q(ss, yy, dd):
        return F.p(off + dd * out, yy, ss) if axis == "v" else F.p(ss, yy, off + dd * out)
    t = 0.09
    P.beam(q(s - w / 2 - t / 2, y - 0.05, 0.02), q(s - w / 2 - t / 2, y + h + 0.05, 0.02), t, t, "dub_ven")
    P.beam(q(s + w / 2 + t / 2, y - 0.05, 0.02), q(s + w / 2 + t / 2, y + h + 0.05, 0.02), t, t, "dub_ven")
    P.beam(q(s - w / 2 - 0.15, y - t / 2, 0.04), q(s + w / 2 + 0.15, y - t / 2, 0.04), 0.12, t, "dub_ven")
    P.beam(q(s - w / 2 - 0.1, y + h + t / 2, 0.02), q(s + w / 2 + 0.1, y + h + t / 2, 0.02), t, t, "dub_ven")
    # tma uvnitr (mistnost se nevidi)
    a, b, c, d = q(s - w / 2, y, -0.12), q(s + w / 2, y, -0.12), q(s + w / 2, y + h, -0.12), q(s - w / 2, y + h, -0.12)
    P.mesh([a, b, c, d] if out > 0 else [d, c, b, a], [(0, 1, 2, 3)], "tma")
    if shutter:
        side = R.choice((-1, 1))
        hx = s + side * (w / 2 + t)
        P.slab(q(hx, y, 0.06), q(hx + side * w * 0.98, y, 0.06), q(hx + side * w * 0.98, y + h, 0.06), q(hx, y, 0.06) + Vector((0, h, 0)),
               0.035, "okenice") if (side > 0) == (out > 0) else \
            P.slab(q(hx + side * w * 0.98, y, 0.06), q(hx, y, 0.06), q(hx, y + h, 0.06), q(hx + side * w * 0.98, y + h, 0.06), 0.035, "okenice")


def door(P: Part, F: Frame, axis, off, s, w=1.0, h=1.85, out=1.0):
    """Dvere z prken se dvema svlaky v ramu z fosen, pod nimi kamenny prah."""
    def q(ss, yy, dd):
        return F.p(off + dd * out, yy, ss) if axis == "v" else F.p(ss, yy, off + dd * out)
    t = 0.14
    for sx in (-1, 1):
        P.beam(q(s + sx * (w / 2 + t / 2), 0.0, 0.0), q(s + sx * (w / 2 + t / 2), h + t, 0.0), t, LOG_W + 0.03, "dub_ven")
    P.beam(q(s - w / 2 - 0.3, h + t / 2, 0.0), q(s + w / 2 + 0.3, h + t / 2, 0.0), t * 1.3, LOG_W + 0.04, "dub_ven")
    n = 5
    for i in range(n):
        a = s - w / 2 + w * i / n
        P.beam(q(a + w / n / 2, 0.02, -0.03), q(a + w / n / 2, h, -0.03), w / n - 0.008, 0.045, "dvere", j=0.4)
    for yy in (0.35, h - 0.35):
        P.beam(q(s - w / 2 + 0.06, yy, 0.0), q(s + w / 2 - 0.06, yy, 0.0), 0.14, 0.04, "dvere")
    P.box(M(q(s, -0.08, 0.25), basis=F.basis()), (0.5, 0.16, w + 0.3) if axis == "v" else (w + 0.3, 0.16, 0.5), "skala")


# ------------------------------------------------------------------ strechy

def roof_gable(P: Part, F: Frame, L, W, ye, pitch, kind, ov=0.55, ovg=0.45):
    """Sedlova strecha: sindel (tenka deska s texturou) nebo dosky/slama (silna vrstva), stity z prken."""
    hr = (W / 2) * math.tan(pitch)
    tanp = math.tan(pitch)
    eL0, eR0 = F.p(-L / 2 - ovg, ye - ov * tanp, -W / 2 - ov), F.p(L / 2 + ovg, ye - ov * tanp, -W / 2 - ov)
    eL1, eR1 = F.p(-L / 2 - ovg, ye - ov * tanp, W / 2 + ov), F.p(L / 2 + ovg, ye - ov * tanp, W / 2 + ov)
    rL, rR = F.p(-L / 2 - ovg, ye + hr, 0.0), F.p(L / 2 + ovg, ye + hr, 0.0)
    if kind == "sindel":
        import lib
        lib.shingle_roof(P, eL0, eR0, rR, rL)
        lib.shingle_roof(P, eR1, eL1, rL, rR)
    else:
        mat = "dosky_hra" if kind == "dosky" else "slama_hra"
        t = 0.32
        up = Vector((0, 0.12, 0))
        P.slab(eR0, eL0, rL + up, rR + up, t, mat)
        P.slab(eL1, eR1, rR + up, rL + up, t, mat)
        P.beam(rL + up * 1.6, rR + up * 1.6, 0.4, 0.22, mat)              # hreben z vazanych dosek
    # stity: svisla prkna, pod hrebenem vetraci otvor (kour z jizby)
    for su in (-1, 1):
        u = su * (L / 2 + 0.02)
        n = int(W / 0.24)
        for i in range(n):
            v0 = -W / 2 + W * i / n
            vc = v0 + W / n / 2
            top = ye + hr * (1 - abs(vc) / (W / 2)) - 0.05
            if top < ye + 0.15:
                continue
            P.beam(F.p(u, ye, vc), F.p(u, top, vc), 0.035, W / n - 0.01, "prkna_ven", j=0.5)
        P.mesh([F.p(u + su * 0.03, ye + hr * 0.62, -0.25), F.p(u + su * 0.03, ye + hr * 0.62, 0.25), F.p(u + su * 0.03, ye + hr * 0.82, 0.0)],
               [(0, 1, 2) if su > 0 else (2, 1, 0)], "tma")
    P.cols.append((M(F.p(0, ye + hr * 0.45, 0), basis=F.basis()), (L + 0.6, hr * 0.9, W + 0.8)))


def roof_hip(P: Part, F: Frame, L, W, ye, pitch, kind, ov=0.6):
    """Valbova strecha (dosky/slama): dve lichobezniky a dve trojuhelnikove valby, silna vrstva."""
    hr = (W / 2) * math.tan(pitch)
    tanp = math.tan(pitch)
    yE = ye - ov * tanp
    hu = L / 2 - W / 2 * 0.7                          # hreben je kratsi nez dum (valba strmejsi)
    A, B = F.p(-L / 2 - ov, yE, -W / 2 - ov), F.p(L / 2 + ov, yE, -W / 2 - ov)
    C, D = F.p(L / 2 + ov, yE, W / 2 + ov), F.p(-L / 2 - ov, yE, W / 2 + ov)
    rL, rR = F.p(-hu, ye + hr, 0.0), F.p(hu, ye + hr, 0.0)
    mat = "dosky_hra" if kind == "dosky" else "slama_hra"
    t = 0.34
    P.slab(B, A, rL, rR, t, mat)
    P.slab(D, C, rR, rL, t, mat)
    P.tri(C, B, rR, t, mat)
    P.tri(A, D, rL, t, mat)
    up = Vector((0, 0.1, 0))
    P.beam(rL + up, rR + up, 0.42, 0.24, mat)
    P.cols.append((M(F.p(0, ye + hr * 0.45, 0), basis=F.basis()), (L + 0.6, hr * 0.9, W + 0.8)))


# ------------------------------------------------------------------ stavby

def cottage(P: Part, c, yaw, L, W, roof, white=False, sign=False):
    """Roubena chalupa: vpredu (+u) stit do navsi se dvema okenky, dvere na dvorni strane (+v)."""
    F = Frame(c, yaw, 0.0)
    g0, g1 = _ground_span(F, L, W)
    F.y0 = g1 + 0.35                                    # podlaha nad nejvyssim mistem terenu
    base = g0 - F.y0 - 0.3
    P.box(M(F.p(0, (base - 0.0) / 2, 0), basis=F.basis()), (L + 0.12, -base, W + 0.12), "skala", collide=False)
    mat = "roubeni_bile" if white else "roubeni"
    ye = 2.35
    holes_front = [(-1.3 - 0.33, -1.3 + 0.33, 0.85, 1.42), (1.3 - 0.33, 1.3 + 0.33, 0.85, 1.42)]
    du = L / 2 - 3.2
    holes_yard = [(du - 0.57, du + 0.57, 0.0, 2.0), (L / 2 - 1.3 - 0.33, L / 2 - 1.3 + 0.33, 0.85, 1.42), (-L / 2 + 2.0 - 0.3, -L / 2 + 2.0 + 0.3, 1.0, 1.45)]
    holes_back = [(L / 2 - 1.6 - 0.33, L / 2 - 1.6 + 0.33, 0.85, 1.42)]
    ov = 0.24
    log_wall(P, F, "u", -W / 2, -L / 2 - ov, L / 2 + ov, 0.0, ye, holes_back, False, mat)
    log_wall(P, F, "u", W / 2, -L / 2 - ov, L / 2 + ov, 0.0, ye, holes_yard, False, mat)
    log_wall(P, F, "v", L / 2, -W / 2 - ov, W / 2 + ov, 0.0, ye, holes_front, True, mat)
    log_wall(P, F, "v", -L / 2, -W / 2 - ov, W / 2 + ov, 0.0, ye, [], True, mat)
    # hlinena vymazanka za sparami (vnitrni lic)
    for su, sv, a, b in ((0, -1, L, W), (0, 1, L, W)):
        pass
    mz = "mazanice"
    P.box(M(F.p(0, ye / 2, -W / 2 + 0.06), basis=F.basis()), (L - 0.1, ye, 0.03), mz)
    P.box(M(F.p(0, ye / 2, W / 2 - 0.06), basis=F.basis()), (L - 0.1, ye, 0.03), mz)
    P.box(M(F.p(L / 2 - 0.06, ye / 2, 0), basis=F.basis()), (0.03, ye, W - 0.1), mz)
    P.box(M(F.p(-L / 2 + 0.06, ye / 2, 0), basis=F.basis()), (0.03, ye, W - 0.1), mz)
    P.box(M(F.p(0, ye - 0.02, 0), basis=F.basis()), (L, 0.04, W), "prkna")                # strop
    for s in (-1.3, 1.3):
        window(P, F, "v", L / 2 + LOG_W / 2, s, 0.85, out=1.0)
    window(P, F, "u", W / 2 + LOG_W / 2, L / 2 - 1.3, 0.85, out=1.0)
    window(P, F, "u", W / 2 + LOG_W / 2, -L / 2 + 2.0, 1.0, w=0.45, h=0.4, out=1.0, shutter=False)
    window(P, F, "u", -W / 2 - LOG_W / 2, L / 2 - 1.6, 0.85, out=-1.0)
    door(P, F, "u", W / 2 + LOG_W / 2, du, out=1.0)
    pitch = math.radians(R.uniform(46, 52))
    if roof == "sindel":
        roof_gable(P, F, L, W, ye, pitch, "sindel")
    elif R.random() < 0.5:
        roof_hip(P, F, L, W, ye, pitch, roof)
    else:
        roof_gable(P, F, L, W, ye, pitch, roof)
    P.cols.append((M(F.p(0, ye / 2 - 0.2, 0), basis=F.basis()), (L + 0.4, ye + 0.4 - base, W + 0.4)))
    if sign:
        # znameni krcmy: vec na tyci nad dvermi
        a = F.p(du, 2.1, W / 2 + LOG_W)
        b = a + F.av * 1.1
        P.rod(a, b, 0.035, 6, "dub_ven")
        P.lathe(M(b - Vector((0, 0.35, 0)), basis=frame(F.au)), [(0.22, -0.06), (0.27, 0.0), (0.22, 0.06)], 10, "vencek")
    return F


def barn(P: Part, c, yaw, L, W, roof):
    """Chlev / stodola z prken na kamenne podezdivce, velka vrata na dvorni strane, strecha jako chalupa."""
    F = Frame(c, yaw, 0.0)
    g0, g1 = _ground_span(F, L, W)
    F.y0 = g1 + 0.15
    base = g0 - F.y0 - 0.3
    P.box(M(F.p(0, base / 2, 0), basis=F.basis()), (L + 0.1, -base, W + 0.1), "skala")
    ye = 2.6
    # kostra
    for u in (-L / 2, -L / 6, L / 6, L / 2):
        for v in (-W / 2, W / 2):
            P.beam(F.p(u, 0.0, v), F.p(u, ye, v), 0.2, 0.2, "dub_ven", j=0.8)
    for v in (-W / 2, W / 2):
        P.beam(F.p(-L / 2 - 0.2, ye, v), F.p(L / 2 + 0.2, ye, v), 0.22, 0.22, "dub_ven", j=0.6)
    for u in (-L / 2, L / 2):
        P.beam(F.p(u, ye, -W / 2 - 0.2), F.p(u, ye, W / 2 + 0.2), 0.22, 0.22, "dub_ven", j=0.6)
    # svisla prkna
    gate = (-1.4, 1.4)
    for axis, off, s0, s1 in (("u", -W / 2 - 0.1, -L / 2, L / 2), ("u", W / 2 + 0.1, -L / 2, L / 2),
                              ("v", L / 2 + 0.1, -W / 2, W / 2), ("v", -L / 2 - 0.1, -W / 2, W / 2)):
        s = s0
        while s < s1 - 0.05:
            w = R.uniform(0.2, 0.32)
            sc = s + w / 2
            if axis == "u" and off > 0 and gate[0] < sc < gate[1]:
                s += w
                continue
            a = F.p(sc, 0.05, off) if axis == "u" else F.p(off, 0.05, sc)
            P.beam(a, a + Vector((0, ye - 0.1 + R.uniform(-0.04, 0.04), 0)), 0.03, w - 0.012, "prkna_ven", j=0.6)
            s += w
    # vrata: dve kridla z prken, jedno pootevrene
    for side in (-1, 1):
        n = 6
        for i in range(n):
            sc = side * (0.12 + 1.28 * (i + 0.5) / n)
            a = F.p(sc, 0.05, W / 2 + 0.16 + (0.25 * (i / n) if side > 0 else 0.0))
            P.beam(a, a + Vector((0, 2.3, 0)), 0.04, 1.28 / n - 0.01, "dvere", j=0.4)
    P.mesh([F.p(-1.4, 0.0, W / 2 - 0.3), F.p(1.4, 0.0, W / 2 - 0.3), F.p(1.4, 2.4, W / 2 - 0.3), F.p(-1.4, 2.4, W / 2 - 0.3)], [(0, 1, 2, 3)], "tma")
    pitch = math.radians(R.uniform(44, 50))
    if roof == "sindel":
        roof_gable(P, F, L, W, ye, pitch, "sindel")
    else:
        roof_hip(P, F, L, W, ye, pitch, roof)
    P.cols.append((M(F.p(0, ye / 2, 0), basis=F.basis()), (L + 0.3, ye, W + 0.3)))
    return F


def picket_fence(P: Part, a, b, gap=None, h=1.15):
    """Latkovy plot: sloupky po 2 m, dve zerdi, latky po 13 cm s nahodnou vyskou; gap = (s0, s1) brana."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    dn = d.normalized()
    nrm = Vector((-dn.z, 0.0, dn.x))
    nposts = max(1, int(L / 2.0))
    for i in range(nposts + 1):
        s = L * i / nposts
        if gap and gap[0] - 0.1 < s < gap[1] + 0.1:
            continue
        p = a + dn * s
        y = _land(p.x, p.z)
        P.beam(Vector((p.x, y - 0.3, p.z)), Vector((p.x, y + h + 0.08, p.z)), 0.1, 0.1, "dub_ven", j=1.0)
    s = 0.0
    while s < L:
        if gap and gap[0] < s < gap[1]:
            s = gap[1] + 0.05
            continue
        p = a + dn * s
        y = _land(p.x, p.z)
        for yy in (0.3, h - 0.25):
            q2 = a + dn * min(L, s + 2.0)
            if gap and s < gap[0] < s + 2.0:
                q2 = a + dn * gap[0]
            P.rod(Vector((p.x, y + yy, p.z)) - nrm * 0.07, Vector((q2.x, _land(q2.x, q2.z) + yy, q2.z)) - nrm * 0.07, 0.035, 5, "dub_ven")
        s += 2.0
    s = 0.05
    while s < L:
        if gap and gap[0] < s < gap[1]:
            s = gap[1] + 0.05
            continue
        p = a + dn * s
        y = _land(p.x, p.z)
        hh = h + R.uniform(-0.08, 0.08)
        P.box(M(Vector((p.x, y + hh / 2 + 0.02, p.z)) + nrm * 0.0, basis=frame(dn) @ __import__("mathutils").Matrix.Rotation(R.uniform(-0.04, 0.04), 3, "Z")),
              (0.065, hh, 0.022), "lata")
        s += R.uniform(0.12, 0.15)
    P.cols.append((M((a + b) / 2 + Vector((0, _land(*((a + b) / 2).xz) + h / 2, 0)), basis=frame(dn)), (0.12, h, L)))


def rail_fence(P: Part, pts, h=1.1):
    """Ohrada z zerdi (bocni a zadni ploty usedlosti): kuly a dve vodorovne tyce."""
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = Vector(a), Vector(b)
        d = b - a
        L = d.length
        n = max(1, int(L / 2.6))
        prev = None
        for i in range(n + 1):
            p = a + d * (i / n)
            y = _land(p.x, p.z)
            top = Vector((p.x, y, p.z))
            P.beam(top - Vector((0, 0.3, 0)), top + Vector((0, h, 0)), 0.11, 0.11, "dub_ven", j=1.2)
            if prev is not None:
                for yy in (0.45, h - 0.12):
                    P.rod(prev + Vector((0, yy + R.uniform(-0.05, 0.05), 0)), top + Vector((0, yy + R.uniform(-0.05, 0.05), 0)), 0.045, 6, "kura")
            prev = top
        dn = d.normalized()
        P.cols.append((M((a + b) / 2 + Vector((0, _land(*((a + b) / 2).xz) + h / 2, 0)), basis=frame(dn)), (0.12, h, L)))


def roofed_gate(P: Part, F: Frame, s, off, w=3.0):
    """Vrata se strisekou: dva silne sloupy, prah nahore, stříška ze sindele, dve kridla z prken."""
    import lib
    y = _land(*(F.c + F.au * off + F.av * s).xz)
    pa = F.c + F.au * off + F.av * (s - w / 2)
    pb = F.c + F.au * off + F.av * (s + w / 2)
    for p in (pa, pb):
        P.beam(Vector((p.x, y - 0.4, p.z)), Vector((p.x, y + 2.7, p.z)), 0.24, 0.24, "dub_ven", j=1.0)
    ta, tb = Vector((pa.x, y + 2.75, pa.z)) - F.av * 0.4, Vector((pb.x, y + 2.75, pb.z)) + F.av * 0.4
    P.beam(ta, tb, 0.22, 0.22, "dub_ven", j=0.6)
    for su in (-1, 1):
        e0 = ta + F.au * su * 0.75 - Vector((0, 0.2, 0))
        e1 = tb + F.au * su * 0.75 - Vector((0, 0.2, 0))
        r0, r1 = ta + Vector((0, 0.45, 0)), tb + Vector((0, 0.45, 0))
        if su > 0:
            lib.shingle_roof(P, e1, e0, r0, r1)
        else:
            lib.shingle_roof(P, e0, e1, r1, r0)
    # kridla (zavrena)
    n = 10
    for i in range(n):
        sc = s - w / 2 + 0.12 + (w - 0.24) * (i + 0.5) / n
        p = F.c + F.au * off + F.av * sc
        P.beam(Vector((p.x, y + 0.08, p.z)), Vector((p.x, y + 1.85 + 0.08 * math.sin(i / (n - 1) * math.pi), p.z)), 0.04, (w - 0.24) / n - 0.01, "dvere", j=0.4)
    for yy in (0.4, 1.5):
        P.beam(F.c + F.au * (off + 0.04) + F.av * (s - w / 2 + 0.15) + Vector((0, y + yy, 0)),
               F.c + F.au * (off + 0.04) + F.av * (s + w / 2 - 0.15) + Vector((0, y + yy, 0)), 0.12, 0.04, "dvere")
    P.cols.append((M(F.c + F.au * off + F.av * s + Vector((0, y + 1.0, 0)), basis=F.basis()), (0.2, 2.0, w)))


def garden(P: Part, F: Frame, u0, u1, v0, v1):
    """Zahradka: zahony se zelim v radach, mezi nimi mesicky, chrpy a maky."""
    rows = int((v1 - v0) / 0.7)
    for r in range(rows):
        v = v0 + 0.35 + r * 0.7
        u = u0 + 0.3
        while u < u1 - 0.3:
            p = F.c + F.au * u + F.av * (v + R.uniform(-0.06, 0.06))
            y = _land(p.x, p.z)
            if R.random() < 0.85:
                s = R.uniform(0.75, 1.15)
                P.ball(Vector((p.x, y + 0.11 * s, p.z)), (0.13 * s, 0.12 * s, 0.13 * s), "zeli_hlava", seg=6, rings=4)
                for k in range(3):
                    a = k * 2.094 + R.uniform(-0.2, 0.2)
                    d = Vector((math.cos(a), 0, math.sin(a)))
                    c0 = Vector((p.x, y + 0.03, p.z))
                    P.tri(c0 + d * 0.05 + Vector((0, 0.04, 0)), c0 + d * 0.3 * s + d.cross(Vector((0, 1, 0))) * 0.14 * s,
                          c0 + d * 0.3 * s - d.cross(Vector((0, 1, 0))) * 0.14 * s + Vector((0, 0.07, 0)), 0.01, "zeli_list")
            u += R.uniform(0.5, 0.62)
    # kvetiny podel okraje
    cols = ["kvet_mesicek", "kvet_chrpa", "kvet_mak", "kvet_kopretina"]
    for _ in range(int((u1 - u0) * 3)):
        u = R.uniform(u0, u1)
        v = v1 + R.uniform(-0.35, 0.15)
        p = F.c + F.au * u + F.av * v
        y = _land(p.x, p.z)
        h = R.uniform(0.25, 0.55)
        P.rod(Vector((p.x, y, p.z)), Vector((p.x, y + h, p.z)), 0.006, 3, "zeli_list")
        rr = R.uniform(0.025, 0.04)
        P.ball(Vector((p.x, y + h, p.z)), (rr, rr * 0.6, rr), R.choice(cols), seg=4, rings=2)


def well(P: Part, c):
    """Studna na navsi: kamenna roubenka (kruh), dva sloupy s rumpalem a strisekou."""
    import lib
    y = _land(*c)
    cc = Vector((c[0], y, c[1]))
    P.lathe(M(cc - Vector((0, 0.2, 0))), [(0.95, 0.0), (0.95, 0.95), (0.75, 0.95), (0.75, 0.2)], 16, "skala")
    P.mesh([cc + Vector((math.cos(a) * 0.75, 0.3, math.sin(a) * 0.75)) for a in [i * math.pi / 8 for i in range(16)]][::-1],
           [tuple(range(16))], "tma")
    for sx in (-1, 1):
        P.beam(cc + Vector((sx * 0.85, 0.0, 0)), cc + Vector((sx * 0.85, 2.3, 0)), 0.14, 0.14, "dub_ven", j=1)
    P.rod(cc + Vector((-0.85, 1.55, 0)), cc + Vector((0.85, 1.55, 0)), 0.11, 10, "kura")
    lib.shingle_roof(P, cc + Vector((-1.1, 2.2, -0.75)), cc + Vector((1.1, 2.2, -0.75)), cc + Vector((1.1, 2.75, 0)), cc + Vector((-1.1, 2.75, 0)))
    lib.shingle_roof(P, cc + Vector((1.1, 2.2, 0.75)), cc + Vector((-1.1, 2.2, 0.75)), cc + Vector((-1.1, 2.75, 0)), cc + Vector((1.1, 2.75, 0)))
    P.cols.append((M(cc + Vector((0, 0.5, 0))), (1.9, 1.0, 1.9)))


# ------------------------------------------------------------------ cela ves

AXIS = math.atan2(0.85, 1.0)        # osa navsi (od vjezdu na severovychod)
NAVES = (62.0, 24.0)                # polovicni delka a sirka navsi


def homesteads():
    """Mista usedlosti: (stred chalupy, smer osy chalupy, strana, poradi). Chalupy stitem do navsi."""
    au = Vector((math.cos(AXIS), 0, math.sin(AXIS)))
    av = Vector((-math.sin(AXIS), 0, math.cos(AXIS)))
    c = Vector((kraj.VES[0], 0, kraj.VES[1]))
    out = []
    Rh = random.Random(5)                 # vlastni nahoda: polohy stejne pri kazdem volani
    for side in (-1, 1):
        for i, u in enumerate((-40.0, -12.0, 16.0, 44.0)):
            p = c + au * (u + Rh.uniform(-3, 3)) + av * side * (NAVES[1] + 9.5)
            # osa chalupy kolmo na naves, stit (+u chalupy) do navsi
            d = -av * side
            out.append((p, math.atan2(d.z, d.x), side, i))
    return out, au, av, c


def build(coll):
    P = Part("Vesnice", bevel=0.01)
    Pf = Part("Vesnice_ploty", bevel=0.0)
    Pg = Part("Vesnice_zahrady", bevel=0.0)
    sites, au, av, c = homesteads()
    roofs = ["sindel", "dosky", "slama"]
    for k, (p, yaw, side, i) in enumerate(sites):
        L, W = R.uniform(9.5, 12.0), R.uniform(5.4, 6.4)
        tavern = (side == -1 and i == 0)
        if tavern:
            L, W = 14.0, 7.2
        roof = "sindel" if tavern else roofs[(k * 5 + 1) % 3]
        F = cottage(P, (p.x, p.z), yaw, L, W, roof, white=tavern or R.random() < 0.3, sign=tavern)
        # chlev za chalupou (dal od navsi), osa rovnobezne
        bp = p - F.au * (L / 2 + 6.5) + F.av * R.uniform(-1.0, 1.5)
        barn(P, (bp.x, bp.z), yaw + math.pi / 2, R.uniform(5.5, 7.5), R.uniform(4.5, 5.5), roofs[(k * 3 + 2) % 3])
        # plot do navsi s vraty se strisekou (na dvorni strane chalupy)
        front = L / 2 + 3.5
        gate_v = W / 2 + 3.2
        pa = F.c + F.au * front + F.av * (W / 2 + 0.8)
        pb = F.c + F.au * front + F.av * (W / 2 + 9.5)
        picket_fence(Pf, pa, pb, gap=(1.0, 4.2))
        roofed_gate(Pf, F, W / 2 + 0.8 + 2.6, front, 3.0)
        # bocni a zadni ohrada dvora a zahrady
        back = -(L / 2 + 13.0)
        rail_fence(Pf, [pb, F.c + F.au * back + F.av * (W / 2 + 9.5), F.c + F.au * back + F.av * (-W / 2 - 6.0),
                        F.c + F.au * front + F.av * (-W / 2 - 6.0), F.c + F.au * front + F.av * (-W / 2 - 0.3)])
        # zahradka pred chalupou u navsi (mezi stitem a plotem, na druhe strane nez dvur)
        garden(Pg, F, -L / 2 + 0.5, L / 2 + 2.6, -W / 2 - 5.6, -W / 2 - 1.2)
        # hranice dreva u steny, vuz na dvore
        wp = F.c + F.au * (-L / 2 + 2.6) + F.av * (W / 2 + 0.75)
        PR.woodpile(P, M(wp + Vector((0, _land(wp.x, wp.z), 0)), basis=F.basis()), length=3.2, rows=7, depth=0.55)
        if R.random() < 0.5:
            import hospodar
            wv = F.c + F.au * (-L / 2 - 1.5) + F.av * (W / 2 + 5.5)
            hospodar.wagon(P, M(wv + Vector((0, _land(wv.x, wv.z), 0)), basis=F.basis()))
        for _ in range(R.randint(1, 3)):
            bv = F.c + F.au * R.uniform(-L / 2, L / 2) + F.av * (W / 2 + 1.0 + R.uniform(0, 1.5))
            PR.barrel(P, M(bv + Vector((0, _land(bv.x, bv.z), 0))), r=0.3, h=0.85)
    # naves: studna a rybnicek
    wc = c + au * 8.0 + av * 6.0
    well(P, (wc.x, wc.z))
    pond(P, c)
    P.commit(coll)
    Pf.commit(coll)
    Pg.commit(coll)
    print("vesnice: %d usedlosti" % len(sites))


POND = (-24.0, -2.0, 21.0, 12.0)     # rybnicek: posun podel osy, napric, polosy


def pond_depth(x, z):
    """Hloubka terenu pod rybnickem (pouziva kraj.hills)."""
    au = (math.cos(AXIS), math.sin(AXIS))
    av = (-math.sin(AXIS), math.cos(AXIS))
    dx, dz = x - kraj.VES[0], z - kraj.VES[1]
    u, v = dx * au[0] + dz * au[1], dx * av[0] + dz * av[1]
    q = ((u - POND[0]) / POND[2]) ** 2 + ((v - POND[1]) / POND[3]) ** 2
    if q > 1.6:
        return 0.0
    return 1.6 * (1.0 - kraj.smooth(0.45, 1.4, q))


def pond(P: Part, c):
    au = Vector((math.cos(AXIS), 0, math.sin(AXIS)))
    av = Vector((-math.sin(AXIS), 0, math.cos(AXIS)))
    pc = c + au * POND[0] + av * POND[1]
    yw = _land(pc.x, pc.z) + 0.45
    pts = []
    for i in range(32):
        a = 2 * math.pi * i / 32
        pts.append(pc + au * math.cos(a) * POND[2] * 0.8 + av * math.sin(a) * POND[3] * 0.8 + Vector((0, yw, 0)))
    P.mesh(pts[::-1], [tuple(range(32))], "voda")


def village_trees():
    """Stromy a kere ve vsi (pro veg): na navsi par velkych briz, ve dvorech a zahradach kere a stromy."""
    Rt = random.Random(9)
    sites, au, av, c = homesteads()
    out = []
    for u, v in ((-30.0, 12.0), (2.0, -14.0), (30.0, 10.0), (50.0, -8.0)):
        p = c + au * u + av * v
        out.append(("briza", p.x, p.z, Rt.uniform(13, 18)))
    for p, yaw, side, i in sites:
        F = Frame((p.x, p.z), yaw, 0.0)
        for _ in range(Rt.randint(1, 3)):
            q = F.c + F.au * Rt.uniform(-12, -6) + F.av * Rt.uniform(-4, 8)
            out.append((Rt.choice(["briza", "shrub_02", "sipek"]), q.x, q.z, Rt.uniform(2.5, 11.0)))
        for _ in range(Rt.randint(2, 5)):
            q = F.c + F.au * Rt.uniform(-6, 6) + F.av * (-6.5 + Rt.uniform(-0.5, 0.5))
            out.append((Rt.choice(["shrub_02", "sipek", "nettle_plant", "divoka_trava"]), q.x, q.z, Rt.uniform(0.5, 1.6)))
    return out


def yard_dist(x, z):
    """Vzdalenost k nejblizsi chalupe (udusana hlina ve dvorech)."""
    sites, au, av, c = homesteads()
    return min(math.hypot(x - p.x, z - p.z) for p, yaw, side, i in sites)
