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


def window(P: Part, F: Frame, axis, off, s, y, w=0.55, h=0.5, out=1.0, shutter=True, dark=True):
    """Okenko v roubene stene: ram z fosen, tma za nim, jedna okenice otevrena ke stene."""
    def q(ss, yy, dd):
        return F.p(off + dd * out, yy, ss) if axis == "v" else F.p(ss, yy, off + dd * out)
    t = 0.09
    P.beam(q(s - w / 2 - t / 2, y - 0.05, 0.02), q(s - w / 2 - t / 2, y + h + 0.05, 0.02), t, t, "dub_ven")
    P.beam(q(s + w / 2 + t / 2, y - 0.05, 0.02), q(s + w / 2 + t / 2, y + h + 0.05, 0.02), t, t, "dub_ven")
    P.beam(q(s - w / 2 - 0.15, y - t / 2, 0.04), q(s + w / 2 + 0.15, y - t / 2, 0.04), 0.12, t, "dub_ven")
    P.beam(q(s - w / 2 - 0.1, y + h + t / 2, 0.02), q(s + w / 2 + 0.1, y + h + t / 2, 0.02), t, t, "dub_ven")
    # tma uvnitr (mistnost se nevidi)
    if dark:
        a, b, c, d = q(s - w / 2, y, -0.12), q(s + w / 2, y, -0.12), q(s + w / 2, y + h, -0.12), q(s - w / 2, y + h, -0.12)
        P.mesh([a, b, c, d] if out > 0 else [d, c, b, a], [(0, 1, 2, 3)], "tma")
    if shutter:
        side = R.choice((-1, 1))
        hx = s + side * (w / 2 + t)
        P.slab(q(hx, y, 0.06), q(hx + side * w * 0.98, y, 0.06), q(hx + side * w * 0.98, y + h, 0.06), q(hx, y, 0.06) + Vector((0, h, 0)),
               0.035, "okenice") if (side > 0) == (out > 0) else \
            P.slab(q(hx + side * w * 0.98, y, 0.06), q(hx, y, 0.06), q(hx, y + h, 0.06), q(hx + side * w * 0.98, y + h, 0.06), 0.035, "okenice")


def door(P: Part, F: Frame, axis, off, s, w=1.0, h=1.85, out=1.0, kind="obycejne", open_=False):
    """Dvere: zarubeň z fosen s kladem, kridlo z dubovych prken na sraz se svlaky, kovane pasy s hroty,
    zastrcka; pred nimi kamenne schody az na teren (podlaha je nad zemi)."""
    from mathutils import Matrix
    import kit

    def q(ss, yy, dd):
        return F.p(off + dd * out, yy, ss) if axis == "v" else F.p(ss, yy, off + dd * out)
    t = 0.16
    for sx in (-1, 1):
        P.beam(q(s + sx * (w / 2 + t / 2), -0.05, 0.02), q(s + sx * (w / 2 + t / 2), h + t, 0.02), t, LOG_W + 0.05, "dub_ven", j=0.6)
    P.beam(q(s - w / 2 - 0.35, h + t / 2 + 0.02, 0.02), q(s + w / 2 + 0.35, h + t / 2 + 0.02, 0.02), t * 1.4, LOG_W + 0.06, "dub_ven", j=0.6)
    P.beam(q(s - w / 2 - 0.2, -0.06, 0.03), q(s + w / 2 + 0.2, -0.06, 0.03), 0.14, LOG_W + 0.08, "dub_ven", j=0.4)   # prah
    nrm = (F.au if axis == "v" else F.av) * out
    tang = (F.av if axis == "v" else F.au)
    if out < 0:
        tang = -tang
    basis = Matrix((tang, Vector((0, 1, 0)), nrm)).transposed()
    m = M(q(s, 0.0, -0.02), basis=basis)
    if open_:
        # kridlo otevrene dovnitr: otocene kolem pantu (lokalni x = -w/2) o 95 stupnu
        m = M(q(s, 0.0, -0.02), basis=basis) @ M((-w / 2, 0, 0)) @ Matrix.Rotation(math.radians(95), 4, "Y") @ M((w / 2, 0, 0))
    kit.door_leaf(P, m, w, h, kind=kind)
    # schody: kamenne stupne od prahu dolu na teren pred dvermi
    gp = q(s, 0.0, 0.9)
    gy = _land(gp.x, gp.z)
    drop = F.y0 - gy
    nst = max(0, int(math.ceil((drop - 0.06) / 0.19)))
    for k in range(nst):
        top = -(k + 1) * drop / (nst + 0.0001) + drop / (nst + 0.0001) * 0.0
        yk = -drop * (k + 1) / (nst + 1)
        dep = 0.36 * (k + 1)
        c = q(s, yk - 0.6, 0.12 + dep / 2 + 0.02)
        P.box(M(c, basis=basis), (w + 0.5 - 0.06 * k, 1.2, dep), "kvadr_sedy", rnd=R.random())
        P.cols.append((M(c, basis=basis), (w + 0.5 - 0.06 * k, 1.2, dep)))
    return nst


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

def plinth(P: Part, F: Frame, L, W, ypad):
    """Nizka podezdivka z lomoveho kamene na maltu (jako zdivo tvrze), od zarovnaneho terenu po prah."""
    h = F.y0 - ypad + 0.25
    P.box(M(F.p(0, -h / 2, 0), basis=F.basis()), (L + 0.14, h, W + 0.14), "zdivo_hole", collide=False)


VYBAVENI = []             # predmety z katalogu uvnitr chalup: {"id", "p", "yaw"} (hra je nacte jako pevne)
MISTNOSTI = []            # mistnosti chalup (otocene): {"name", "title", "pos", "size", "yaw", "ambient"}
OHNE = 0


def _yaw_along(d):
    """Natoceni predmetu (rotation.y), aby jeho lokalni x lezelo podel vektoru d."""
    return math.atan2(-d.z, d.x)


def _put(F: Frame, id_, u, v, along="u", y=0.0, flip=False, wall=False):
    """Predmet z katalogu na misto v chalupe (u, v v ramci domu, y nad podlahou)."""
    d = F.au if along == "u" else F.av
    yw = _yaw_along(d) + (math.pi if flip else 0.0)
    p = F.p(u, y, v)
    VYBAVENI.append({"id": id_, "p": [round(p.x, 3), round(p.y, 3), round(p.z, 3)], "yaw": round(yw, 4)})


def _plaster(P: Part, F: Frame, axis, off, s0, s1, ye, holes, mat, side):
    """Hlinena vymazanka mezi tramy (za sparami), po radach jako tramy, s otvory oken a dveri."""
    y = 0.0
    while y < ye - 0.01:
        ya, yb = y, min(ye, y + LOG_H)
        for a, b in _intervals(s0, s1, ya, yb, holes):
            c = F.p((a + b) / 2, (ya + yb) / 2, off + side * 0.03) if axis == "u" else F.p(off + side * 0.03, (ya + yb) / 2, (a + b) / 2)
            size = (b - a, yb - ya, 0.1) if axis == "u" else (0.1, yb - ya, b - a)
            P.box(M(c, basis=F.basis()), size, mat)
        y += LOG_H


def _wall_cols(P: Part, F: Frame, axis, off, s0, s1, ye, holes):
    """Kolize steny: kvadry mezi otvory dveri (okna jsou vys, ty nevadi)."""
    for a, b in _intervals(s0, s1, 0.05, 0.8, holes):
        c = F.p((a + b) / 2, ye / 2, off) if axis == "u" else F.p(off, ye / 2, (a + b) / 2)
        size = (b - a, ye, 0.24) if axis == "u" else (0.24, ye, b - a)
        P.cols.append((M(c, basis=F.basis()), size))


def hearth(P: Part, F: Frame, u, v, lit, name):
    """Hlinena pec s ohnistem v koute jizby: podstavec z kamene a hliny, klenuta pec (chleba), pred ni
    otevrene ohniste na nizkem stupni s kamennym lemem, popel, polena; dym jde pod strop a ven stitem."""
    global OHNE
    B = F.basis()
    P.box(M(F.p(u, 0.25, v), basis=B), (1.9, 0.5, 1.7), "zdivo_hole", collide=True)
    P.box(M(F.p(u, 0.52, v), basis=B), (1.95, 0.05, 1.75), "mazanice")
    # pec: kopule z hliny vzadu (u steny)
    c = F.p(u - 0.2, 0.54, v - 0.2)
    P.lathe(M(c), [(0.8, 0.0), (0.78, 0.35), (0.62, 0.7), (0.35, 0.92), (0.0, 0.98)], 14, "mazanice")
    P.mesh([F.p(u + 0.35, 0.56, v + 0.35), F.p(u + 0.55, 0.56, v + 0.05), F.p(u + 0.5, 0.95, v + 0.15)], [(0, 1, 2)], "tma")
    # ohniste: kameny v kruhu, popel, polena
    oc = F.p(u + 0.45, 0.55, v + 0.45)
    for k in range(9):
        a = k * 2 * math.pi / 9
        kp = oc + F.au * math.cos(a) * 0.32 + F.av * math.sin(a) * 0.32
        import krajina
        krajina.rock(P, (kp.x, kp.y, kp.z), (0.16, 0.11, 0.13), 0.2, collide=False)
    P.lathe(M(oc), [(0.28, 0.0), (0.0, 0.03)], 10, "popel")
    for k in range(3):
        a = k * 2.1
        d = F.au * math.cos(a) + F.av * math.sin(a)
        P.rod(oc + d * 0.25 + Vector((0, 0.05, 0)), oc - d * 0.05 + Vector((0, 0.13, 0)), 0.045, 6, "kura")
    OHNE += 1
    import lib
    lib.fire("hearth", oc + Vector((0, 0.08, 0)), name=name, size=0.55, zap=lit, svetlo=[0.0, 0.7, 0.0])
    P.cols.append((M(F.p(u, 0.5, v), basis=B), (1.9, 1.0, 1.7)))


def cot_bed(P: Part, F: Frame, u, v):
    """Lidove luzko: rama z dubovych fosen na ctyrech nohach, prkna, slamnik, len."""
    B = F.basis()
    for du_ in (-0.95, 0.95):
        for dv in (-0.5, 0.5):
            P.box(M(F.p(u + du_, 0.25, v + dv), basis=B), (0.1, 0.5, 0.1), "dub_ven")
    for dv in (-0.5, 0.5):
        P.box(M(F.p(u, 0.38, v + dv), basis=B), (2.0, 0.12, 0.08), "dub_ven")
    for du_ in (-0.95, 0.95):
        P.box(M(F.p(u + du_, 0.38, v), basis=B), (0.08, 0.12, 1.0), "dub_ven")
    P.box(M(F.p(u + 0.95, 0.65, v), basis=B), (0.06, 0.5, 1.06), "dub_ven")          # celo
    P.box(M(F.p(u, 0.42, v), basis=B), (1.9, 0.04, 0.95), "prkna")
    P.box(M(F.p(u, 0.52, v), basis=B), (1.88, 0.16, 0.92), "platno")                  # slamnik
    P.box(M(F.p(u + 0.7, 0.64, v), basis=B), (0.4, 0.1, 0.6), "prosteradlo")            # podhlavnice
    P.box(M(F.p(u - 0.25, 0.61, v), basis=B), (1.2, 0.03, 0.96), "sukno_okr")          # pokryvka
    P.cols.append((M(F.p(u, 0.3, v), basis=B), (2.0, 0.6, 1.0)))


_KAT = None


def _kat():
    global _KAT
    if _KAT is None:
        import json
        import os
        _KAT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "modely", "predmety.json")))
    return _KAT


def _h(id_):
    return float(_kat().get(id_, {}).get("rozmer", [0, 0, 0])[1])


def _onwall(F: Frame, id_, face, normal, s, y):
    """Predmet na zed (venec cibule, police na zed): face = poloha lice steny, normal 'u+','u-','v+','v-'."""
    r = _kat().get(id_, {}).get("rozmer", [0.3, 0.3, 0.1])
    ax, sg = normal[0], (1 if normal[1] == "+" else -1)
    n = (F.au if ax == "u" else F.av) * sg
    off = face + sg * (float(r[2]) / 2 + 0.035)
    p = F.p(off, y - float(r[1]) / 2, s) if ax == "u" else F.p(s, y - float(r[1]) / 2, off)
    VYBAVENI.append({"id": id_, "p": [round(p.x, 3), round(p.y, 3), round(p.z, 3)], "yaw": round(math.atan2(n.x, n.z), 4)})


def interior(F: Frame, kind, L, W, Lj, Lk, uj, uk, us, Rv, P):
    """Vybaveni chalupy predmety z katalogu (kazda jina): jizba, sin, komora."""
    wi = W / 2 - 0.1                       # vnitrni lic podelnych sten
    fi = L / 2 - 0.1                       # vnitrni lic predniho stitu
    on = lambda ids, u, v, y: [_put(F, i_, u + Rv.uniform(-0.15, 0.15), v + Rv.uniform(-0.12, 0.12), "u", y, Rv.random() < 0.5) for i_ in ids]  # noqa: E731
    jidla = ["bochnik", "syr", "kase", "polevka", "hrusky", "orechy", "pecen", "slanina", "uzena_ryba", "vejce_kosik", "houska", "hriby"]
    if kind == "krcma":
        # senkovna: dlouhy stul s lavicemi, druhy stul v koute, sudy a soudek, korbely
        _put(F, "stul_hodovni", fi - 3.0, 0.3, "u")
        for dv in (-0.85, 0.85):
            _put(F, "lavice_hodovni", fi - 3.0, 0.3 + dv, "u")
        th = _h("stul_hodovni")
        for k in range(6):
            _put(F, Rv.choice(["pivo", "korbel", "pivo", "miska", "dzban"]), fi - 4.7 + k * 0.65, 0.3 + Rv.uniform(-0.25, 0.25), "u", th)
        _put(F, "stul_prkenny", fi - 0.9, -wi + 0.9, "v")
        _put(F, "lavice_nizka", fi - 0.4, -wi + 0.95, "v", flip=True)
        for k, id_ in enumerate(["sud", "sud", "soudek"]):
            _put(F, id_, uj + 2.3 + k * 0.85, wi - 0.45, "u")
        _put(F, "vino_dzban", fi - 0.9, -wi + 0.8, "u", _h("stul_prkenny"))
        _put(F, "svicen", fi - 3.0, 0.3, "u", th)
    elif kind == "rychtar":
        # rychtar: stul s ubrusem, calounene zidle, kreslo, malovana skrin, vyrezavana truhla, postel s nebesy
        _put(F, "stul_ubrus", fi - 1.9, wi - 1.5, "u")
        th = _h("stul_ubrus")
        _put(F, "kreslo_goticke", fi - 0.55, wi - 1.5, "v", flip=True)
        for du_ in (-0.6, 0.5):
            _put(F, "zidle_calounena", fi - 1.9 + du_, wi - 2.55, "u")
        _put(F, "lavice", fi - 1.9, wi - 0.35, "u", flip=True)
        on(["kniha", "kalamar"], fi - 2.4, wi - 1.5, th)
        on(["svicny"], fi - 1.6, wi - 1.4, th)
        on([Rv.choice(jidla), "vino_dzban", "pohary"], fi - 1.9, wi - 1.6, th)
        _put(F, "koberec_modry", fi - 1.9, wi - 1.5, "u")
        _put(F, "postel", fi - 1.2, -wi + 0.8, "v")
        _put(F, "truhla_vyrezavana", fi - 2.6, -wi + 0.35, "u")
        _put(F, "skrin_malovana", uj + 0.4, -0.2, "v")
        _onwall(F, "police_malovana", fi, "u-", wi - 2.9, 1.7)
        _put(F, "svicen_stojaci", fi - 0.4, -0.2, "u")
    else:
        # bezna chalupa: stul v koute (pod okny), lavice podel sten, stolicka, luzko, truhla, police u pricky
        st = Rv.choice(["stul_prkenny", "stul_prkenny", "stul_kulaty_stary", "stul_malovany"])
        if st == "stul_malovany":
            _put(F, st, fi - 1.6, wi - 1.45, "u")
        else:
            _put(F, st, fi - 1.35, wi - 1.45, "u")
        _put(F, "lavice_nizka", fi - 0.42, wi - 1.55, "v")
        _put(F, "lavice_nizka", fi - 2.0, wi - 0.42, "u")
        _put(F, Rv.choice(["stolicka", "zidle_selska", "spalek"]), fi - 1.4, wi - 2.3, "u")
        th = _h(st)
        on(["miska", "lzice"], fi - 1.25, wi - 1.35, th)
        on([Rv.choice(jidla), Rv.choice(["dzban", "korbel", "voda_mech", "pivo"])], fi - 1.6, wi - 1.55, th)
        if Rv.random() < 0.5:
            on(["svicen"], fi - 1.0, wi - 1.6, th)
        cot_bed(P, F, fi - 1.15, -wi + 0.6)
        _put(F, Rv.choice(["ovci_kuze", "polstar", "kozesina"]) if Rv.random() < 0.4 else "polstar", fi - 0.5, -wi + 0.6, "u", 0.6)
        _put(F, Rv.choice(["truhla", "truhla", "kos_viko"]), fi - 2.65, -wi + 0.32, "u")
        _put(F, Rv.choice(["police", "police_stara", "skrin_selska"]) if W > 5.8 else "police", uj + 0.3, -wi + 1.95 + 0.6, "v")
        extra = Rv.choice(["kolebka", "kolovrat", "maselnice", "stolek"])
        _put(F, extra, uj + 2.6, wi - 0.55, "u")
    # u pece: kotlik nad ohnem, dzban a panev na stupni, vence cibule a bylin na pricce
    _put(F, "kotlik", uj + 1.55, -wi + 1.35, "u", 0.6)
    _put(F, Rv.choice(["dzban", "panvice", "miska"]), uj + 1.85, -wi + 0.55, "u", 0.55)
    _onwall(F, Rv.choice(["venec_cibule", "venec_cesneku", "byliny"]), uj + 0.1, "u+", 0.6, 1.85)
    # sin: vedro, kosik, metla, naradi, spalek; nekde zernov nebo maselnice
    _put(F, "vedro", us - 0.6, -wi + 0.4, "u")
    _put(F, "metla", us, -wi + 0.2, "u")
    _put(F, Rv.choice(["kosik", "spalek", "zernov", "maselnice", "kos_viko"]), us + 0.5, -wi + 0.45, "u")
    if Rv.random() < 0.6:
        _put(F, Rv.choice(["hrabe", "vidle", "ryc", "lopata"]), us, wi - 0.25, "u")
    # komora (spiz): pytle, sudy, bedny, na bedne jidlo, na zdi vence
    _put(F, "pytel_obili", -L / 2 + 0.55, -wi + 0.35, "u")
    _put(F, "pytel_mouky", -L / 2 + 1.05, -wi + 0.35, "u")
    if Rv.random() < 0.6:
        _put(F, "pytel_obili", -L / 2 + 0.6, -wi + 0.8, "u")
    _put(F, Rv.choice(["sud", "soudek", "sud"]), -L / 2 + 1.75, -wi + 0.45, "u")
    _put(F, "bedna", -L / 2 + 0.55, wi - 0.9, "v")
    bh = _h("bedna")
    on([Rv.choice(["syr", "sunka", "med", "slanina", "susene_maso", "vejce_kosik"]), Rv.choice(["med", "mrkev", "vodnice", "zeli", "cibule"])],
       -L / 2 + 0.55, wi - 0.9, bh)
    _put(F, Rv.choice(["kos_viko", "soudek", "kosik"]), uk - 0.5, wi - 0.45, "u")
    _onwall(F, Rv.choice(["venec_cibule", "venec_cesneku"]), -L / 2 + 0.1, "u+", -0.3, 1.8)
    if Rv.random() < 0.5:
        _onwall(F, "byliny", -L / 2 + 0.1, "u+", 0.6, 1.8)


def cottage(P: Part, c, yaw, L, W, roof, white=False, sign=False, hip=False, ypad=None, var=None, idx=0):
    """Roubena chalupa s dispozici trojdilneho domu: vpredu k navsi jizba (pec s ohnistem, stul v koute
    s lavicemi, luzko, police), uprostred sin se vchodem ze dvora, vzadu komora se spizi. Kazda jina podle var.
    Dovnitr se da vejit: kolize jen steny, dvere otevrene."""
    global OHNE
    var = var or {}
    Rv = random.Random(1000 + idx)
    F = Frame(c, yaw, 0.0)
    if ypad is None:
        ypad = _ground_span(F, L, W)[1]
    F.y0 = ypad + var.get("sokl", 0.42)
    plinth(P, F, L, W, ypad)
    mat = "roubeni_bile" if white else var.get("drevo", "roubeni")
    ye = var.get("ye", 2.35)
    kind = var.get("typ", "chalupa")          # chalupa / rychtar / krcma
    # dispozice: jizba vpredu, sin, komora vzadu
    Lj = max(5.2, L * 0.5)
    Lk = 2.3 if kind != "krcma" else 2.8
    uj, uk = L / 2 - Lj, -L / 2 + Lk
    us = (uj + uk) / 2
    nwin = var.get("okna", 2)
    ws = var.get("okno_w", 0.55)
    fr = [-1.3, 1.3] if nwin == 2 else ([-1.8, 0.0, 1.8] if nwin == 3 else [0.0])
    holes_front = [(x - ws / 2 - 0.05, x + ws / 2 + 0.05, 0.85, 1.42) for x in fr]
    holes_yard = [(us - 0.62, us + 0.62, 0.0, 2.05), (L / 2 - 1.3 - 0.33, L / 2 - 1.3 + 0.33, 0.85, 1.42), (-L / 2 + 1.2 - 0.25, -L / 2 + 1.2 + 0.25, 1.0, 1.45)]
    holes_back = [(L / 2 - 2.6 - 0.33, L / 2 - 2.6 + 0.33, 0.85, 1.42)]
    dv0 = W / 2 - 1.55                                         # vnitrni dvere v pricce (u vchodu)
    holes_in = [(dv0 - 0.45, dv0 + 0.45, 0.0, 1.9)]
    ov = 0.24
    log_wall(P, F, "u", -W / 2, -L / 2 - ov, L / 2 + ov, 0.0, ye, holes_back, False, mat)
    log_wall(P, F, "u", W / 2, -L / 2 - ov, L / 2 + ov, 0.0, ye, holes_yard, False, mat)
    log_wall(P, F, "v", L / 2, -W / 2 - ov, W / 2 + ov, 0.0, ye, holes_front, True, mat)
    log_wall(P, F, "v", -L / 2, -W / 2 - ov, W / 2 + ov, 0.0, ye, [], True, mat)
    for uu in (uj, uk):
        log_wall(P, F, "v", uu, -W / 2 + 0.1, W / 2 - 0.1, 0.0, ye, holes_in, True, mat)
        # zarubeň vnitrnich dveri
        for sx in (-1, 1):
            P.beam(F.p(uu, 0.0, dv0 + sx * 0.5), F.p(uu, 1.95, dv0 + sx * 0.5), LOG_W + 0.04, 0.1, "dub_ven")
        P.beam(F.p(uu, 1.98, dv0 - 0.65), F.p(uu, 1.98, dv0 + 0.65), LOG_W + 0.04, 0.12, "dub_ven")
    mz = "mazanice_bila" if var.get("bile_spary") else "mazanice"
    _plaster(P, F, "u", -W / 2, -L / 2 + 0.1, L / 2 - 0.1, ye, holes_back, mz, 1)
    _plaster(P, F, "u", W / 2, -L / 2 + 0.1, L / 2 - 0.1, ye, holes_yard, mz, -1)
    _plaster(P, F, "v", L / 2, -W / 2 + 0.1, W / 2 - 0.1, ye, holes_front, mz, -1)
    _plaster(P, F, "v", -L / 2, -W / 2 + 0.1, W / 2 - 0.1, ye, [], mz, 1)
    # kolize sten (dovnitr se da vejit dvermi)
    _wall_cols(P, F, "u", -W / 2, -L / 2, L / 2, ye, holes_back)
    _wall_cols(P, F, "u", W / 2, -L / 2, L / 2, ye, holes_yard)
    _wall_cols(P, F, "v", L / 2, -W / 2, W / 2, ye, holes_front)
    _wall_cols(P, F, "v", -L / 2, -W / 2, W / 2, ye, [])
    for uu in (uj, uk):
        _wall_cols(P, F, "v", uu, -W / 2, W / 2, ye, holes_in)
    # podlahy: v jizbe prkna, v sini a komore udusana hlina; strop z fosen a prken
    B = F.basis()
    if kind != "chalupa" or Rv.random() < 0.6:
        # podlaha jizby z jednotlivych prken ruzne sirokych (napric domu), kazde jinak
        vv = -W / 2 + 0.1
        while vv < W / 2 - 0.12:
            pw = min(Rv.uniform(0.22, 0.34), W / 2 - 0.1 - vv)
            P.box(M(F.p((uj + L / 2) / 2, -0.03 + Rv.uniform(-0.004, 0.004), vv + pw / 2), basis=B), (Lj - 0.1, 0.06, pw - 0.006), "prkna",
                  uvo=(Rv.uniform(0, 9), Rv.uniform(0, 9)))
            vv += pw
    else:
        P.box(M(F.p((uj + L / 2) / 2, -0.03, 0), basis=B), (Lj - 0.1, 0.06, W - 0.2), "hlina_hra")
    P.box(M(F.p((uk + uj) / 2, -0.03, 0), basis=B), (uj - uk - 0.1, 0.06, W - 0.2), "hlina_hra")
    P.box(M(F.p((uk - L / 2) / 2, -0.03, 0), basis=B), (Lk - 0.1, 0.06, W - 0.2), "hlina_hra")
    P.cols.append((M(F.p(0, -0.35, 0), basis=B), (L - 0.15, 0.7, W - 0.15)))
    uu = -L / 2
    while uu < L / 2 - 0.05:
        pw = min(Rv.uniform(0.2, 0.32), L / 2 - uu)
        P.box(M(F.p(uu + pw / 2, ye - 0.02 + Rv.uniform(-0.006, 0.006), 0), basis=B), (pw - 0.008, 0.04, W), "prkna",
              uvo=(Rv.uniform(0, 9), Rv.uniform(0, 9)))
        uu += pw
    for k in range(int(L / 0.9)):
        uu = -L / 2 + 0.45 + k * 0.9
        P.beam(F.p(uu, ye - 0.12, -W / 2), F.p(uu, ye - 0.12, W / 2), 0.16, 0.2, "dub_ven", j=0.6)
    for x in fr:
        window(P, F, "v", L / 2 + LOG_W / 2, x, 0.85, w=ws, out=1.0, dark=False)
    window(P, F, "u", W / 2 + LOG_W / 2, L / 2 - 1.3, 0.85, out=1.0, dark=False)
    window(P, F, "u", W / 2 + LOG_W / 2, -L / 2 + 1.2, 1.0, w=0.4, h=0.4, out=1.0, shutter=False, dark=False)
    window(P, F, "u", -W / 2 - LOG_W / 2, L / 2 - 2.6, 0.85, out=-1.0, dark=False)
    door(P, F, "u", W / 2 + LOG_W / 2, us, w=1.05, out=1.0, kind=var.get("dvere", "obycejne"), open_=True)
    # mistnosti pro hru (ambient uvnitr, nazev)
    nm = {"rychtar": "Rychtářův dům", "krcma": "Krčma"}.get(kind, "Chalupa")
    for rn, ua, ub, amb in (("jizba", uj, L / 2, (0.2, 0.18, 0.16)), ("sin", uk, uj, (0.16, 0.15, 0.14)), ("komora", -L / 2, uk, (0.13, 0.12, 0.11))):
        cc = F.p((ua + ub) / 2, 0.0, 0)
        title = {"jizba": "Jizba" if kind != "krcma" else "Šenkovna", "sin": "Síň", "komora": "Komora"}[rn] + " – " + nm
        MISTNOSTI.append({"name": "ves_%d_%s" % (idx, rn), "title": title, "pos": [cc.x, cc.y, cc.z], "size": [ub - ua - 0.1, ye, W - 0.2],
                          "yaw": _yaw_along(F.au), "ambient": list(amb)})
    # --- jizba: pec s ohnistem v koute u sine vzadu, stul v protejsim (svatem) koute, luzko, police
    hearth(P, F, uj + 1.1, -W / 2 + 1.0, Rv.random() < 0.7, "ohen_ves_%d" % idx)
    interior(F, kind, L, W, Lj, Lk, uj, uk, us, Rv, P)
    pitch = math.radians(var.get("sklon", 48))
    pods = var.get("podsin", 0.0)
    if roof == "sindel" or not hip:
        if pods > 0:
            # podsin: strecha i stit vysunute pred dum na dvou sloupech, pod tim lavice
            G = Frame((F.c.x + F.au.x * pods / 2, F.c.z + F.au.z * pods / 2), math.atan2(F.au.z, F.au.x), F.y0)
            roof_gable(P, G, L + pods, W, ye, pitch, "sindel" if roof == "sindel" else roof)
            for v in (-W / 2 + 0.1, W / 2 - 0.1):
                P.lathe(M(F.p(L / 2 + pods - 0.15, -0.2, v)), [(0.17, 0.0), (0.15, 0.2), (0.0, 0.2)], 8, "kvadr_sedy")
                P.beam(F.p(L / 2 + pods - 0.15, 0.0, v), F.p(L / 2 + pods - 0.15, ye, v), 0.18, 0.18, "dub_ven", j=0.8)
                P.beam(F.p(L / 2 + pods - 0.15, ye - 0.6, v), F.p(L / 2 + pods - 0.75, ye - 0.05, v), 0.1, 0.1, "dub_ven", j=0.6)
                P.cols.append((M(F.p(L / 2 + pods - 0.15, ye / 2, v), basis=F.basis()), (0.2, ye, 0.2)))
            P.beam(F.p(L / 2 + pods - 0.15, ye, -W / 2 - 0.2), F.p(L / 2 + pods - 0.15, ye, W / 2 + 0.2), 0.2, 0.2, "dub_ven", j=0.5)
            for v in (-W / 2, W / 2):
                P.beam(F.p(L / 2 - 0.1, ye, v), F.p(L / 2 + pods, ye, v), 0.2, 0.2, "dub_ven", j=0.5)
            # podlaha podsine z kamennych desek, lavice u steny
            P.box(M(F.p(L / 2 + pods / 2, -0.2, 0), basis=F.basis()), (pods, 0.4, W - 0.2), "kvadr_sedy")
            P.box(M(F.p(L / 2 + 0.45, 0.42, 0), basis=F.basis()), (0.38, 0.06, W * 0.6), "drevo_plot")
            for v in (-W * 0.25, W * 0.25):
                P.box(M(F.p(L / 2 + 0.45, 0.2, v), basis=F.basis()), (0.3, 0.4, 0.07), "drevo_plot")
        else:
            roof_gable(P, F, L, W, ye, pitch, "sindel" if roof == "sindel" else roof)
        if var.get("podlomenice"):
            import lib
            for su in ((1,) if pods > 0 else (-1, 1)):
                u0, u1 = su * (L / 2 + 0.05), su * (L / 2 + 0.65)
                e0, e1 = F.p(u1, ye - 0.1, -W / 2 - 0.3), F.p(u1, ye - 0.1, W / 2 + 0.3)
                r0, r1 = F.p(u0, ye + 0.3, -W / 2 - 0.3), F.p(u0, ye + 0.3, W / 2 + 0.3)
                if pods > 0:
                    e0, e1, r0, r1 = (x + F.au * pods for x in (e0, e1, r0, r1))
                if su > 0:
                    lib.shingle_roof(P, e1, e0, r0, r1)
                else:
                    lib.shingle_roof(P, e0, e1, r1, r0)
    else:
        roof_hip(P, F, L, W, ye, pitch, roof)
    _ = 0
    if sign:
        # znameni krcmy: na tyci nad dvermi visi na provazku vechet z chvoji (smrkove vetvicky svazane do kuzele)
        a = F.p(us + 1.2, 2.15, W / 2 + LOG_W)
        b = a + F.av * 1.2
        P.rod(a, b, 0.04, 6, "dub_ven")
        P.rod(a + F.av * 0.45, a + F.av * 0.45 + Vector((0, 0.6, 0)) - F.av * 0.4, 0.02, 5, "dub_ven")   # vzpera
        P.rod(b, b - Vector((0, 0.3, 0)), 0.008, 4, "provaz_hra")
        c0 = b - Vector((0, 0.3, 0))
        for k in range(14):
            ang = k * 2.4
            d = Vector((math.cos(ang) * 0.12, -0.25 - 0.35 * (k % 3) / 2.0, math.sin(ang) * 0.12))
            P.lathe(M(c0, basis=frame(d.normalized())), [(0.07, 0.0), (0.11, 0.18), (0.08, 0.38), (0.0, 0.55)], 6, "chvoji")
        P.lathe(M(c0 + Vector((0, -0.04, 0))), [(0.06, 0.0), (0.07, 0.08), (0.0, 0.1)], 8, "provaz_hra")
    return F


def barn(P: Part, c, yaw, L, W, roof, ypad=None):
    """Chlev / stodola: dubova kostra na kamenne podezdivce, steny ze zasedlych prken s listami pres spary,
    velka dvoukridla vrata na dvorni strane (jedno kridlo otevrene), uvnitr udusana hlina, slama a jesle.
    Kolize jen steny a sloupy, dovnitr se da vejit vraty."""
    from mathutils import Matrix
    F = Frame(c, yaw, 0.0)
    if ypad is None:
        ypad = _ground_span(F, L, W)[1]
    F.y0 = ypad + 0.08
    plinth(P, F, L, W, ypad)
    ye = 2.6
    B = F.basis()
    # kostra
    for u in (-L / 2, -L / 6, L / 6, L / 2):
        for v in (-W / 2, W / 2):
            P.beam(F.p(u, 0.0, v), F.p(u, ye, v), 0.2, 0.2, "dub_ven", j=0.8)
    for v in (-W / 2, W / 2):
        P.beam(F.p(-L / 2 - 0.2, ye, v), F.p(L / 2 + 0.2, ye, v), 0.22, 0.22, "dub_ven", j=0.6)
        P.beam(F.p(-L / 2, 0.08, v), F.p(L / 2, 0.08, v), 0.2, 0.16, "dub_ven", j=0.6)      # podvalnik
    for u in (-L / 2, L / 2):
        P.beam(F.p(u, ye, -W / 2 - 0.2), F.p(u, ye, W / 2 + 0.2), 0.22, 0.22, "dub_ven", j=0.6)
        P.beam(F.p(u, 0.08, -W / 2), F.p(u, 0.08, W / 2), 0.2, 0.16, "dub_ven", j=0.6)
    # steny: svisla prkna na sraz, pres spary uzke listy (prkna se v case kroutí, nekde chybi lista)
    gate = (-1.45, 1.45)
    for axis, off, s0, s1, out in (("u", -W / 2 - 0.12, -L / 2, L / 2, -1), ("u", W / 2 + 0.12, -L / 2, L / 2, 1),
                                   ("v", L / 2 + 0.12, -W / 2, W / 2, 1), ("v", -L / 2 - 0.12, -W / 2, W / 2, -1)):
        s_ = s0
        while s_ < s1 - 0.05:
            w = min(R.uniform(0.22, 0.34), s1 - s_)
            sc = s_ + w / 2
            if axis == "u" and off > 0 and gate[0] < sc < gate[1]:
                s_ += w
                continue
            a = F.p(sc, 0.0, off) if axis == "u" else F.p(off, 0.0, sc)
            top = ye - 0.08 + R.uniform(-0.05, 0.03)
            P.beam(a, a + Vector((0, top, 0)), 0.03, w - 0.004, "drevo_plot", j=0.5)
            if R.random() < 0.88 and s_ + w < s1 - 0.05:
                e = (F.au if axis == "u" else F.av) * (w / 2)
                n = (F.av if axis == "u" else F.au) * (0.03 * out)
                P.beam(a + e + n + Vector((0, 0.05, 0)), a + e + n + Vector((0, top - 0.05, 0)), 0.025, 0.07, "drevo_plot", j=0.6)
            s_ += w
        # kolize steny (u vrat jen kusy vedle otvoru)
        if axis == "u" and off > 0:
            for a0, a1 in ((s0, gate[0]), (gate[1], s1)):
                P.cols.append((M(F.p((a0 + a1) / 2, ye / 2, off), basis=B), (a1 - a0, ye, 0.2)))
        elif axis == "u":
            P.cols.append((M(F.p(0, ye / 2, off), basis=B), (L, ye, 0.2)))
        else:
            P.cols.append((M(F.p(off, ye / 2, 0), basis=B), (0.2, ye, W)))
    # vrata: leve kridlo zavrene, prave otevrene ven (pootocene na pantu)
    for side in (-1, 1):
        n = 6
        hinge = F.p(side * 1.42, 0.0, W / 2 + 0.16)
        ang = 0.0 if side < 0 else -1.25
        rot = Matrix.Rotation(ang * side, 3, "Y")
        for i in range(n):
            loc = (F.au * (-side) * (0.05 + 1.3 * (i + 0.5) / n))
            q = hinge + rot @ loc
            P.beam(q + Vector((0, 0.04, 0)), q + Vector((0, 2.35, 0)), 0.045, 1.3 / n - 0.008, "dvere", up=rot @ F.av, j=0.4)
        for yy in (0.35, 1.95):
            q0 = hinge + rot @ (F.au * (-side) * 0.05) + Vector((0, yy, 0)) + rot @ F.av * 0.04
            q1 = hinge + rot @ (F.au * (-side) * 1.35) + Vector((0, yy, 0)) + rot @ F.av * 0.04
            P.beam(q0, q1, 0.13, 0.035, "dvere", up=rot @ F.av)
        q0 = hinge + rot @ (F.au * (-side) * 0.1) + Vector((0, 0.45, 0)) + rot @ F.av * 0.04
        q1 = hinge + rot @ (F.au * (-side) * 1.25) + Vector((0, 1.85, 0)) + rot @ F.av * 0.04
        P.beam(q0, q1, 0.11, 0.03, "dvere", up=rot @ F.av)
    # uvnitr: udusana podlaha, slama, jesle a zlab u zadni steny
    P.box(M(F.p(0, -0.03, 0), basis=B), (L - 0.1, 0.06, W - 0.1), "hlina_hra")
    for _ in range(9):
        q = F.p(R.uniform(-L / 2 + 0.6, L / 2 - 0.6), 0.0, R.uniform(-W / 2 + 0.6, W / 2 - 0.8))
        P.lathe(M(q), [(R.uniform(0.4, 0.8), 0.0), (0.3, 0.1), (0.0, 0.14)], 7, "slama_hra")
    for u in (-L / 2 + 0.5, L / 2 - 0.5):
        P.beam(F.p(u, 0.0, -W / 2 + 0.55), F.p(u, 1.0, -W / 2 + 0.55), 0.1, 0.1, "dub_ven")
    P.beam(F.p(-L / 2 + 0.5, 1.0, -W / 2 + 0.55), F.p(L / 2 - 0.5, 1.0, -W / 2 + 0.55), 0.1, 0.1, "dub_ven")
    for k in range(int(L / 0.2)):
        u = -L / 2 + 0.6 + k * 0.2
        if u > L / 2 - 0.6:
            break
        P.rod(F.p(u, 0.55, -W / 2 + 0.2), F.p(u + 0.05, 1.0, -W / 2 + 0.55), 0.015, 4, "dub_ven")
    P.box(M(F.p(0, 0.25, -W / 2 + 0.35), basis=B), (L - 1.2, 0.08, 0.45), "drevo_plot")
    pitch = math.radians(R.uniform(44, 50))
    if roof == "sindel":
        roof_gable(P, F, L, W, ye, pitch, "sindel")
    else:
        roof_hip(P, F, L, W, ye, pitch, roof)
    return F


def _pole(P: Part, base, h, r=0.065, mat="kura"):
    """Kul: kulatina s kurou, trochu krivy a nakloneny."""
    top = base + Vector((R.uniform(-0.06, 0.06), h, R.uniform(-0.06, 0.06)))
    mid = (base + top) / 2 + Vector((R.uniform(-0.03, 0.03), 0, R.uniform(-0.03, 0.03)))
    P.rod(base, mid, r * R.uniform(0.95, 1.1), 7, mat, r1=r)
    P.rod(mid, top, r, 7, mat, r1=r * R.uniform(0.8, 0.95))
    return top


def picket_fence(P: Part, a, b, gap=None, h=1.15):
    """Latkovy plot: kulove sloupky po 2 m, dve zerdi s kurou, latky ruzne siroke a vysoke, zasedle,
    nekde nakrivo nebo chybi. gap = (s0, s1) misto pro branu."""
    from mathutils import Matrix
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
        _pole(P, Vector((p.x, _land(p.x, p.z) - 0.3, p.z)) - nrm * 0.12, h + 0.35, 0.06)
    for yy in (0.3, h - 0.25):
        segs = [(0.0, L)] if not gap else [(0.0, gap[0]), (gap[1], L)]
        for s0, s1 in segs:
            if s1 - s0 < 0.3:
                continue
            p0, p1 = a + dn * s0, a + dn * s1
            y0, y1 = _land(p0.x, p0.z), _land(p1.x, p1.z)
            P.rod(Vector((p0.x, y0 + yy + R.uniform(-0.04, 0.04), p0.z)) - nrm * 0.07, Vector((p1.x, y1 + yy + R.uniform(-0.04, 0.04), p1.z)) - nrm * 0.07,
                  0.035, 6, "kura")
    s = 0.05
    while s < L:
        if gap and gap[0] < s < gap[1]:
            s = gap[1] + 0.05
            continue
        w = R.uniform(0.055, 0.1)
        if R.random() < 0.04:                    # chybejici latka
            s += w + R.uniform(0.04, 0.07)
            continue
        p = a + dn * s
        y = _land(p.x, p.z)
        hh = h + R.uniform(-0.12, 0.08)
        tilt = R.uniform(-0.05, 0.05) if R.random() < 0.85 else R.uniform(-0.18, 0.18)
        bas = frame(dn) @ Matrix.Rotation(tilt, 3, "Z") @ Matrix.Rotation(R.uniform(-0.03, 0.03), 3, "Y")
        P.box(M(Vector((p.x, y + hh / 2 - 0.05, p.z)), basis=bas), (w, hh, 0.022), "lata", rnd=R.random())
        # zkosena spicka latky
        tp = Vector((p.x, y + hh - 0.05, p.z))
        P.tri(tp - dn * w / 2, tp + dn * w / 2, tp + Vector((0, w * 0.6, 0)), 0.022, "lata", rnd=R.random()) if R.random() < 0.7 else None
        s += w + R.uniform(0.03, 0.07)
    P.cols.append((M((a + b) / 2 + Vector((0, _land(*((a + b) / 2).xz) + h / 2, 0)), basis=frame(dn)), (0.14, h, L)))


def rail_fence(P: Part, pts, h=1.1):
    """Ohrada z kulatiny (bocni a zadni ploty usedlosti): krive kuly, na nich dve az tri zerdi s kurou,
    konce zerdi presahuji a prekryvaji se, nekde zerd spadla."""
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = Vector(a), Vector(b)
        d = b - a
        L = d.length
        n = max(1, int(L / 2.8))
        dn = d.normalized()
        nrm = Vector((-dn.z, 0.0, dn.x))
        tops = []
        for i in range(n + 1):
            p = a + d * (i / n)
            y = _land(p.x, p.z)
            tops.append(_pole(P, Vector((p.x, y - 0.35, p.z)), h + 0.3, R.uniform(0.06, 0.08)))
        rows = (0.42, h - 0.1) if R.random() < 0.6 else (0.3, 0.68, h - 0.08)
        for i in range(n):
            for k, yy in enumerate(rows):
                p0 = tops[i] - Vector((0, h + 0.3 - 0.35 - yy, 0)) - dn * R.uniform(0.15, 0.3) + nrm * 0.08 * (1 if k % 2 else -1)
                p1 = tops[i + 1] - Vector((0, h + 0.3 - 0.35 - yy, 0)) + dn * R.uniform(0.15, 0.3) + nrm * 0.08 * (1 if k % 2 else -1)
                if R.random() < 0.05:            # spadla zerd: jeden konec na zemi
                    p1 = Vector((p1.x, _land(p1.x, p1.z) + 0.05, p1.z))
                p0 += Vector((0, R.uniform(-0.05, 0.05), 0))
                p1 += Vector((0, R.uniform(-0.05, 0.05), 0))
                mid = (p0 + p1) / 2 + Vector((0, R.uniform(-0.04, 0.02), 0))      # zerd se prohyba
                r = R.uniform(0.035, 0.05)
                P.rod(p0, mid, r, 6, "kura")
                P.rod(mid, p1, r, 6, "kura", r1=r * 0.85)
        P.cols.append((M((a + b) / 2 + Vector((0, _land(*((a + b) / 2).xz) + h / 2, 0)), basis=frame(dn)), (0.14, h, L)))


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


def cabbage(P: Part, c, s):
    """Hlavka zeli: hlava z nekolika vrstev listu a 6 rozevrenych spodnich listu (prohnute pruhy)."""
    y = c.y
    P.ball(Vector((c.x, y + 0.1 * s, c.z)), (0.12 * s, 0.11 * s, 0.12 * s), "zeli_hlava", seg=8, rings=5)
    a0 = R.uniform(0, 6.28)
    for k in range(6):
        a = a0 + k * 1.047 + R.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), 0, math.sin(a)))
        side = d.cross(Vector((0, 1, 0))) * 0.11 * s
        p0 = Vector((c.x, y + 0.05 * s, c.z)) + d * 0.06 * s
        p1 = p0 + d * 0.16 * s + Vector((0, 0.06 * s, 0))
        p2 = p0 + d * 0.3 * s + Vector((0, 0.02 * s, 0))
        P.mesh([p0 - side * 0.5, p0 + side * 0.5, p1 + side, p1 - side], [(0, 1, 2, 3)], "zeli_list")
        P.mesh([p1 - side, p1 + side, p2 + side * 0.6, p2 - side * 0.6], [(0, 1, 2, 3)], "zeli_list")
        P.mesh([p0 + side * 0.5, p0 - side * 0.5, p1 - side, p1 + side], [(0, 1, 2, 3)], "zeli_list")
        P.mesh([p1 + side, p1 - side, p2 - side * 0.6, p2 + side * 0.6], [(0, 1, 2, 3)], "zeli_list")


def flower(P: Part, c, kind):
    """Kvetina: stonek, dva listy a kvet (5 platku kolem stredu) - mesicek, chrpa, mak, kopretina."""
    col = {"mesicek": "kvet_mesicek", "chrpa": "kvet_chrpa", "mak": "kvet_mak", "kopretina": "kvet_kopretina"}[kind]
    h = R.uniform(0.3, 0.6)
    top = c + Vector((R.uniform(-0.03, 0.03), h, R.uniform(-0.03, 0.03)))
    P.rod(c, top, 0.005, 3, "zeli_list")
    for k in (0, 1):
        a = R.uniform(0, 6.28)
        d = Vector((math.cos(a), 0.4, math.sin(a))) * 0.1
        b = c + Vector((0, h * (0.3 + 0.2 * k), 0))
        P.mesh([b, b + d + d.cross(Vector((0, 1, 0))) * 0.3, b + d * 1.4, b + d - d.cross(Vector((0, 1, 0))) * 0.3], [(0, 1, 2, 3)], "zeli_list")
    r = 0.045 if kind in ("mak", "kopretina") else 0.035
    for k in range(5):
        a = k * 1.2566 + R.uniform(-0.1, 0.1)
        d = Vector((math.cos(a), 0.15, math.sin(a)))
        e = d.cross(Vector((0, 1, 0))).normalized()
        P.mesh([top, top + d * r + e * r * 0.45, top + d * r * 1.15, top + d * r - e * r * 0.45], [(0, 1, 2, 3)], col)
        P.mesh([top + d * r - e * r * 0.45, top + d * r * 1.15, top + d * r + e * r * 0.45, top], [(0, 1, 2, 3)], col)
    P.ball(top + Vector((0, 0.008, 0)), (r * 0.3, r * 0.2, r * 0.3), "kvet_stred" if kind != "chrpa" else "kvet_chrpa", seg=5, rings=3)


def garden(P: Part, F: Frame, u0, u1, v0, v1):
    """Zahradka: zahony se zelim v radach, na kraji mesicky, chrpy, maky a kopretiny."""
    rows = int((v1 - v0) / 0.85)
    for r in range(rows):
        v = v0 + 0.45 + r * 0.85
        u = u0 + 0.35
        while u < u1 - 0.35:
            p = F.c + F.au * u + F.av * (v + R.uniform(-0.06, 0.06))
            if R.random() < 0.85:
                cabbage(P, Vector((p.x, _land(p.x, p.z), p.z)), R.uniform(0.8, 1.2))
            u += R.uniform(0.62, 0.75)
    kinds = ["mesicek", "chrpa", "mak", "kopretina"]
    for _ in range(int((u1 - u0) * 2.5)):
        u = R.uniform(u0, u1)
        v = R.choice((v0 + R.uniform(0.05, 0.25), v1 - R.uniform(0.05, 0.25)))
        p = F.c + F.au * u + F.av * v
        flower(P, Vector((p.x, _land(p.x, p.z), p.z)), R.choice(kinds))


def well(P: Part, c):
    """Studna na navsi: kamenna roubenka (kruh), dva sloupy s rumpalem a strisekou."""
    import lib
    y = _land(*c)
    cc = Vector((c[0], y, c[1]))
    P.lathe(M(cc - Vector((0, 0.2, 0))), [(0.95, 0.0), (0.95, 0.95), (0.75, 0.95), (0.75, 0.2)], 16, "zdivo_hole")
    P.mesh([cc + Vector((math.cos(a) * 0.75, 0.3, math.sin(a) * 0.75)) for a in [i * math.pi / 8 for i in range(16)]][::-1],
           [tuple(range(16))], "tma")
    for sx in (-1, 1):
        P.beam(cc + Vector((sx * 0.85, 0.0, 0)), cc + Vector((sx * 0.85, 2.3, 0)), 0.14, 0.14, "dub_ven", j=1)
    P.rod(cc + Vector((-0.85, 1.55, 0)), cc + Vector((0.85, 1.55, 0)), 0.11, 10, "kura")
    lib.shingle_roof(P, cc + Vector((-1.1, 2.2, -0.75)), cc + Vector((1.1, 2.2, -0.75)), cc + Vector((1.1, 2.75, 0)), cc + Vector((-1.1, 2.75, 0)))
    lib.shingle_roof(P, cc + Vector((1.1, 2.2, 0.75)), cc + Vector((-1.1, 2.2, 0.75)), cc + Vector((-1.1, 2.75, 0)), cc + Vector((1.1, 2.75, 0)))
    P.cols.append((M(cc + Vector((0, 0.5, 0))), (1.9, 1.0, 1.9)))


def molehills(P: Part, c, n=60):
    """Krtince a hrboly hliny v trave na navsi a za ploty."""
    import krajina
    Rm = random.Random(31)
    au = Vector((math.cos(AXIS), 0, math.sin(AXIS)))
    av = Vector((-math.sin(AXIS), 0, math.cos(AXIS)))
    k = 0
    while k < n:
        p = c + au * Rm.uniform(-75, 75) + av * Rm.uniform(-55, 55)
        if yard_dist(p.x, p.z) < 14.0 or pond_depth(p.x, p.z) > 0.0:
            continue
        nu, nv = naves_uv(p.x, p.z)
        if abs(nv) < NAVES[1] - 2.0:
            continue
        k += 1
        s = Rm.uniform(0.35, 0.6)
        y = _land(p.x, p.z)
        P.lathe(M(Vector((p.x, y - 0.06, p.z))), [(s, 0.0), (s * 0.75, 0.09), (s * 0.4, 0.16), (0.0, 0.19)], 8, "hlina_hra")


# ------------------------------------------------------------------ cela ves

AXIS = math.atan2(0.85, 1.0)        # osa navsi (od vjezdu na severovychod)
NAVES = (62.0, 24.0)                # polovicni delka a sirka navsi

_LAYOUT = None


def layout():
    """Pevne rozlozeni usedlosti (vlastni nahoda, stejne pri kazdem volani): chalupa, chlev, strechy."""
    global _LAYOUT
    if _LAYOUT is not None:
        return _LAYOUT
    Rl = random.Random(5)
    au = Vector((math.cos(AXIS), 0, math.sin(AXIS)))
    av = Vector((-math.sin(AXIS), 0, math.cos(AXIS)))
    c = Vector((kraj.VES[0], 0, kraj.VES[1]))
    roofs = ["sindel", "dosky", "slama"]
    out = []
    k = 0
    for side in (-1, 1):
        for i, u in enumerate((-40.0, -12.0, 16.0, 44.0)):
            p = c + au * (u + Rl.uniform(-3, 3)) + av * side * (NAVES[1] + 9.5)
            d = -av * side                                  # osa chalupy kolmo na naves, stit (+u) do navsi
            yaw = math.atan2(d.z, d.x)
            tavern = side == -1 and i == 0
            rychtar = side == 1 and i == 1
            L, W = (14.0, 7.2) if tavern else ((13.0, 7.0) if rychtar else (Rl.uniform(10.5, 12.5), Rl.uniform(5.6, 6.4)))
            F = Frame((p.x, p.z), yaw, 0.0)
            bp = p - F.au * (L / 2 + 6.5) + F.av * Rl.uniform(-0.5, 1.0)
            out.append({"p": p, "yaw": yaw, "L": L, "W": W, "tavern": tavern, "side": side, "i": i,
                        "roof": "sindel" if tavern else roofs[(k * 5 + 1) % 3], "white": tavern or Rl.random() < 0.3,
                        "hip": Rl.random() < 0.5, "barn": (bp, yaw + math.pi / 2, Rl.uniform(5.5, 7.5), Rl.uniform(4.5, 5.5)),
                        "barn_roof": roofs[(k * 3 + 2) % 3], "wagon": Rl.random() < 0.5,
                        "var": {"drevo": Rl.choice(["roubeni", "roubeni_tmave", "roubeni_sede"]), "bile_spary": Rl.random() < 0.4,
                                "okna": 3 if tavern else Rl.choice([1, 2, 2, 3]), "okno_w": Rl.uniform(0.42, 0.6),
                                "podsin": 1.9 if (tavern or Rl.random() < 0.4) else 0.0, "podlomenice": Rl.random() < 0.45,
                                "dvere": "hlavni" if tavern else "obycejne", "sklon": Rl.uniform(44, 54),
                                "ye": Rl.uniform(2.3, 2.6), "sokl": Rl.uniform(0.3, 0.6),
                                "typ": "krcma" if tavern else ("rychtar" if rychtar else "chalupa")}})
            if rychtar:
                out[-1]["var"].update({"podsin": 2.0, "dvere": "hlavni", "okna": 3, "bile_spary": True, "drevo": "roubeni"})
                out[-1]["roof"] = "sindel"
            k += 1
    _LAYOUT = out
    return out


def homesteads():
    """Zpetne kompatibilni: (stred chalupy, smer osy, strana, poradi) + osy navsi."""
    au = Vector((math.cos(AXIS), 0, math.sin(AXIS)))
    av = Vector((-math.sin(AXIS), 0, math.cos(AXIS)))
    c = Vector((kraj.VES[0], 0, kraj.VES[1]))
    return [(h["p"], h["yaw"], h["side"], h["i"]) for h in layout()], au, av, c


# ------------------------------------------------------------------ podklad staveb: mirne zarovnany teren

_PADS = None


def _pads():
    """Plochy pod stavbami: (stred, osa u, osa v, polodelka, polosirka, vyska). Vyska = prumer puvodniho terenu."""
    global _PADS
    if _PADS is not None:
        return _PADS
    import fort
    out = []
    for h in layout():
        for (p, yaw, L, W) in ((h["p"], h["yaw"], h["L"], h["W"]), h["barn"]):
            F = Frame((p.x, p.z), yaw, 0.0)
            ys = [fort.land(*(F.c + F.au * u + F.av * v).xz, pads=False) for u in (-L / 2, 0, L / 2) for v in (-W / 2, 0, W / 2)]
            out.append((F.c, F.au, F.av, L / 2 + 0.6, W / 2 + 0.6, sum(ys) / len(ys)))
    _PADS = out
    return out


def pad_adjust(x, z, y):
    """Teren pod stavbou srovnany na vysku plochy, kolem plynuly prechod (2.5 m)."""
    dv = math.hypot(x - kraj.VES[0], z - kraj.VES[1])
    if dv > 160.0:
        return y
    for c, au, av, hu, hv, yp in _pads():
        dx, dz = x - c.x, z - c.z
        u = abs(dx * au.x + dz * au.z) - hu
        v = abs(dx * av.x + dz * av.z) - hv
        d = math.hypot(max(u, 0.0), max(v, 0.0))
        if d < 2.5:
            k = 1.0 - kraj.smooth(0.0, 2.5, d)
            y = y + (yp - y) * k
    return y


def pad_y(p, yaw, L, W):
    for c, au, av, hu, hv, yp in _pads():
        if (c - Vector((p.x, 0, p.z))).length < 0.01:
            return yp
    return _land(p.x, p.z)


def build(coll):
    P = Part("Vesnice", bevel=0.01)
    Pf = Part("Vesnice_ploty", bevel=0.0)
    Pg = Part("Vesnice_zahrady", bevel=0.0)
    sites, au, av, c = homesteads()
    VYBAVENI.clear()
    MISTNOSTI.clear()
    for k, h in enumerate(layout()):
        p, yaw, L, W = h["p"], h["yaw"], h["L"], h["W"]
        hip = h["hip"] and h["var"]["podsin"] == 0.0
        F = cottage(P, (p.x, p.z), yaw, L, W, h["roof"], white=h["white"] and not h["var"]["bile_spary"], sign=h["tavern"], hip=hip,
                    ypad=pad_y(p, yaw, L, W), var=h["var"], idx=k)
        bp, byaw, bL, bW = h["barn"]
        barn(P, (bp.x, bp.z), byaw, bL, bW, h["barn_roof"], ypad=pad_y(bp, byaw, bL, bW))
        # ulice: plot v linii stitu chalupy (od rohu chalupy), na dvorni strane s vraty se strisekou
        front = L / 2 + 0.05
        pa = F.c + F.au * front + F.av * (W / 2 + 0.12)
        pb = F.c + F.au * front + F.av * (W / 2 + 9.5)
        picket_fence(Pf, pa, pb, gap=(1.0, 4.2))
        roofed_gate(Pf, F, W / 2 + 0.12 + 2.6, front, 3.0)
        pg0 = F.c + F.au * front + F.av * (-W / 2 - 0.12)
        pg1 = F.c + F.au * front + F.av * (-W / 2 - 6.2)
        picket_fence(Pf, pg0, pg1)
        # bocni a zadni ohrada dvora a zahrady
        back = -(L / 2 + 13.0)
        rail_fence(Pf, [pb, F.c + F.au * back + F.av * (W / 2 + 9.5), F.c + F.au * back + F.av * (-W / 2 - 6.2), pg1])
        # zahradka u chalupy za plotem (mezi stenou a bocnim plotem)
        garden(Pg, F, -L / 2 + 0.8, L / 2 - 0.6, -W / 2 - 5.8, -W / 2 - 1.0)
        # hranice dreva u steny, vuz na dvore, sudy
        wp = F.c + F.au * (-L / 2 + 2.6) + F.av * (W / 2 + 0.75)
        PR.woodpile(P, M(wp + Vector((0, _land(wp.x, wp.z), 0)), basis=F.basis()), length=3.2, rows=7, depth=0.55)
        if h["wagon"]:
            import hospodar
            wv = F.c + F.au * (-L / 2 - 1.0) + F.av * (W / 2 + 6.0)
            hospodar.wagon(P, M(wv + Vector((0, _land(wv.x, wv.z), 0)), basis=F.basis()))
        for _ in range(R.randint(1, 3)):
            bv = F.c + F.au * R.uniform(-L / 2 + 4.0, L / 2 - 1.0) + F.av * (W / 2 + 0.9 + R.uniform(0, 0.8))
            PR.barrel(P, M(bv + Vector((0, _land(bv.x, bv.z), 0))), r=0.3, h=0.85)
    # naves: studna a rybnicek (rybnicek stranou od cesty), krtince v trave
    wc = c + au * (-6.0) + av * (-11.0)
    import studna
    studna.build(coll, (wc.x, _land(wc.x, wc.z) + 0.1, wc.z), name="Studna_ves", dynamic=False, seed=1393)
    pond(P, c)
    molehills(P, c, 25)
    naves_stones(P, c)
    P.commit(coll)
    Pf.commit(coll)
    Pg.commit(coll)
    print("vesnice: %d usedlosti" % len(sites))


POND = (74.0, 2.0, 14.0, 9.0)       # rybnicek na hornim konci navsi (za posledni usedlosti), mimo cestu


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
        pts.append(pc + au * math.cos(a) * POND[2] * 1.12 + av * math.sin(a) * POND[3] * 1.12 + Vector((0, yw, 0)))
    P.mesh(pts[::-1], [tuple(range(32))], "voda")


def _in_building(x, z, margin=1.5):
    for c, au, av, hu, hv, yp in _pads():
        dx, dz = x - c.x, z - c.z
        if abs(dx * au.x + dz * au.z) < hu + margin and abs(dx * av.x + dz * av.z) < hv + margin:
            return True
    return False


def village_trees():
    """Stromy a kere ve vsi (pro veg): na navsi par velkych briz, za chlevy sad, u plotu kere a kopřivy."""
    Rt = random.Random(9)
    sites, au, av, c = homesteads()
    out = []
    # na navsi stromy a kere na okrajich (kde se nechodi), u studny bríza, u rybnika kere
    for u, v in ((-30.0, 17.0), (-2.0, 19.0), (30.0, -18.0), (-52.0, -16.0), (8.0, -6.0), (55.0, 15.0), (64.0, -12.0)):
        p = c + au * u + av * v
        if not _in_building(p.x, p.z, 3.0) and pond_depth(p.x, p.z) == 0.0:
            out.append((Rt.choice(["lipa", "lipa", "dub", "briza"]), p.x, p.z, Rt.uniform(11, 17)))
    for _ in range(26):
        u, v = Rt.uniform(-68, 80), Rt.choice((-1, 1)) * Rt.uniform(NAVES[1] - 3.0, NAVES[1] + 2.0)
        p = c + au * u + av * v
        if not _in_building(p.x, p.z, 1.0) and pond_depth(p.x, p.z) == 0.0:
            out.append((Rt.choice(["shrub_02", "sipek", "shrub_02", "nettle_plant", "divoka_trava"]), p.x, p.z, Rt.uniform(0.6, 2.2)))
    # smutecni vrby na brehu rybnika
    for a in (0.4, 2.3, 4.4):
        p = c + au * (POND[0] + math.cos(a) * POND[2] * 1.25) + av * (POND[1] + math.sin(a) * POND[3] * 1.3)
        out.append(("vrba", p.x, p.z, Rt.uniform(8.0, 11.0)))
    for k in range(10):
        a = k * 0.63
        p = c + au * (POND[0] + math.cos(a) * POND[2] * 1.2) + av * (POND[1] + math.sin(a) * POND[3] * 1.25)
        out.append((Rt.choice(["shrub_02", "sipek", "divoka_trava"]), p.x, p.z, Rt.uniform(0.8, 2.5)))
    # zelen mezi cestami na navsi: husta trava, trsy, kopřivy u plotu, kere v rozich (3D rostliny)
    n = 0
    while n < 1400:
        u, v = Rt.uniform(-95, 85), Rt.uniform(-NAVES[1] - 2.0, NAVES[1] + 2.0)
        p = c + au * u + av * v
        if _in_building(p.x, p.z, 0.6) or pond_depth(p.x, p.z) > 0.0:
            continue
        pd = path_dist(p.x, p.z)
        if pd < 0.5:
            continue
        n += 1
        e = NAVES[1] + 2.0 - abs(v)                       # blizko plotu
        r = Rt.random()
        if pd > 3.0 and r < 0.035:
            out.append((Rt.choice(["shrub_02", "sipek"]), p.x, p.z, Rt.uniform(0.9, 2.3)))
        elif e < 2.0 and r < 0.3:
            out.append(("nettle_plant", p.x, p.z, Rt.uniform(0.35, 0.7)))
        elif r < 0.7:
            out.append(("divoka_trava", p.x, p.z, Rt.uniform(0.35, 0.8) * (0.6 if pd < 1.5 else 1.0)))
        elif r < 0.88:
            out.append(("grass_medium_02", p.x, p.z, Rt.uniform(0.25, 0.5)))
        else:
            out.append((Rt.choice(["dandelion_01", "fern_02"]), p.x, p.z, Rt.uniform(0.2, 0.5)))
    for h in layout():
        F = Frame((h["p"].x, h["p"].z), h["yaw"], 0.0)
        L, W = h["L"], h["W"]
        # sad za chlevem (mezi chlevem a zadnim plotem)
        for _ in range(Rt.randint(2, 4)):
            q = F.c + F.au * Rt.uniform(-(L / 2 + 12.0), -(L / 2 + 10.0)) + F.av * Rt.uniform(-W / 2 - 4.5, W / 2 + 8.0)
            if not _in_building(q.x, q.z):
                out.append((Rt.choice(["lipa", "dub", "briza", "shrub_02", "sipek"]), q.x, q.z, Rt.uniform(4.0, 9.0)))
        # u bocniho plotu zahrady kere a kopřivy
        for _ in range(Rt.randint(2, 5)):
            q = F.c + F.au * Rt.uniform(-L / 2, L / 2) + F.av * (-W / 2 - 6.0 + Rt.uniform(-0.3, 0.3))
            if not _in_building(q.x, q.z, 0.3):
                out.append((Rt.choice(["shrub_02", "sipek", "nettle_plant", "divoka_trava"]), q.x, q.z, Rt.uniform(0.5, 1.6)))
    return out


def yard_dist(x, z):
    """Vzdalenost k nejblizsi chalupe (udusana hlina ve dvorech)."""
    return min(math.hypot(x - h["p"].x, z - h["p"].z) for h in layout())


def naves_uv(x, z):
    """Souradnice v ramci navsi: u podel osy, v napric (0 = stred)."""
    dx, dz = x - kraj.VES[0], z - kraj.VES[1]
    return dx * math.cos(AXIS) + dz * math.sin(AXIS), -dx * math.sin(AXIS) + dz * math.cos(AXIS)


def naves_stones(P: Part, c):
    """Kameny na navsi: velke u plotu a u studny (na sezeni), drobne vyorane v trave na okrajich."""
    import krajina
    Rs = random.Random(44)
    au = Vector((math.cos(AXIS), 0, math.sin(AXIS)))
    av = Vector((-math.sin(AXIS), 0, math.cos(AXIS)))
    k = 0
    while k < 40:
        u, v = Rs.uniform(-70, 70), Rs.choice((-1, 1)) * Rs.uniform(NAVES[1] - 6, NAVES[1] + 1)
        p = c + au * u + av * v
        if _in_building(p.x, p.z, 1.5) or pond_depth(p.x, p.z) > 0.0:
            continue
        k += 1
        sz = Rs.uniform(0.25, 0.6) if Rs.random() < 0.8 else Rs.uniform(0.7, 1.1)
        krajina.rock(P, (p.x, _land(p.x, p.z), p.z), (sz * Rs.uniform(1.0, 1.5), sz * Rs.uniform(0.5, 0.8), sz), 0.35, collide=sz > 0.6)


_PATHS = None


def ves_paths():
    """Cesty ve vsi: hlavni cesta stredem navsi (sirsi uprostred, kde se nejvic chodi) a zaoblene odbocky
    od ni k vratum kazde usedlosti. [(body [(x, z)], polosirka)]."""
    global _PATHS
    if _PATHS is not None:
        return _PATHS
    au = Vector((math.cos(AXIS), 0, math.sin(AXIS)))
    av = Vector((-math.sin(AXIS), 0, math.cos(AXIS)))
    c = Vector((kraj.VES[0], 0, kraj.VES[1]))
    main = []
    for k in range(41):
        u = -95.0 + k * 4.2
        v = 2.5 * math.sin(u / 23.0) + 1.2 * math.sin(u / 9.0 + 1.0)
        p = c + au * u + av * v
        main.append((p.x, p.z))
    out = [(main, None)]
    for h in layout():
        F = Frame((h["p"].x, h["p"].z), h["yaw"], 0.0)
        front = h["L"] / 2 + 0.05
        g = F.c + F.au * front + F.av * (h["W"] / 2 + 0.12 + 2.6)           # vrata dvora
        g1 = g + F.au * 5.0                                                   # rovne ven z vrat
        nu, nv = naves_uv(g.x, g.z)
        j = c + au * (nu + 5.0) + av * (2.5 * math.sin((nu + 5.0) / 23.0))  # napojeni na hlavni cestu sikmo
        pts = []
        for k in range(13):
            t = k / 12.0
            q = g * (1 - t) ** 2 + g1 * 2 * t * (1 - t) + j * t * t           # kvadraticka krivka (zaobleni)
            pts.append((q.x, q.z))
        out.append((pts, 1.3))
    _PATHS = out
    return out


def path_width(u):
    """Polosirka hlavni cesty: u vjezdu 2 m, na navsi kolem studny a uprostred az 5 m."""
    return 2.0 + 3.0 * math.exp(-((u + 6.0) / 30.0) ** 2) + 0.5 * math.sin(u / 7.0)


def path_dist(x, z):
    """(vzdalenost od okraje nejblizsi cesty ve vsi; zaporna = na ceste)."""
    best = 1e9
    for pts, hw in ves_paths():
        d, px, pz = kraj.seg_info(x, z, pts)
        if hw is None:
            u, _ = naves_uv(px, pz)
            hw2 = path_width(u)
        else:
            hw2 = hw
        best = min(best, d - hw2)
    return best
