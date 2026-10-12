"""Palac u severni hradby: dole hodovni sin a spiz, nahore komnata a loznice, na dvorni strane pavlac."""
import math

from mathutils import Matrix, Vector

import fort as F
import props as PR
from lib import M, Part, R, jit, light, rot, shingle_roof, wall_x, wall_z

X0, X1, OX = -3.0, 17.0, 18.8
ZN, OZN, ZS = -14.0, -15.8, -7.0
T = 0.6
F1 = 3.9
EAVE = 7.5
RIDGE_Z, RIDGE_Y = -11.4, 11.46
BASE = -4.5

# otvory v dvornim pruceli
DOOR_HALL = (7.1, 8.9, 0.0, 2.95)
DOOR_PANTRY = (-0.6, 0.5, 0.0, 2.15)
WIN_GROUND = [(4.5, 5.5), (11.0, 12.0), (14.0, 15.0)]       # y 1.3..2.6
WIN_UP = [(4.0, 5.0), (13.5, 14.5)]                          # y 4.9..6.2
DOOR_UP = [(0.5, 1.6), (10.4, 11.5)]                         # y F1..5.95
NORTH_WIN = [(5.7, 6.3, 1.9, 3.1), (9.7, 10.3, 1.9, 3.1), (13.7, 14.3, 1.9, 3.1), (1.6, 2.4, 4.9, 6.2), (11.6, 12.4, 4.9, 6.2)]


def roof_y(z):
    return RIDGE_Y - 0.9 * abs(z - RIDGE_Z)


def build(coll):
    shell(coll)
    gallery(coll)
    hall(coll)
    pantry(coll)
    chamber(coll)
    bedroom(coll)


# ------------------------------------------------------------------ obvodove zdi a strecha

def shell(coll):
    P = Part("Palac", bevel=0.025)
    # severni hradba v delce palace
    wall_x(P, "zdivo", X0, OX, OZN, ZN, BASE, EAVE, NORTH_WIN)
    for (xa, xb, ya, yb) in NORTH_WIN:
        _frame_z(P, (xa + xb) / 2, xb - xa, ya, yb, OZN, -1)
    # vychodni zed se stitem a oknem loznice
    wall_z(P, "zdivo", ZN, ZS, X1, OX, BASE, EAVE, [[-9.4, -8.5, 4.9, 6.3]])
    _frame_x(P, -8.95, 0.9, 4.9, 6.3, OX, 1)
    P.tri((OX, EAVE, OZN), (OX, EAVE, ZS), (OX, RIDGE_Y - 0.15, RIDGE_Z), 0.9, "zdivo")
    # dvorni pruceli
    holes = [list(DOOR_HALL), list(DOOR_PANTRY)]
    holes += [[a, b, 1.3, 2.6] for a, b in WIN_GROUND]
    holes += [[a, b, F1, 5.95] for a, b in DOOR_UP]
    holes += [[a, b, 4.9, 6.2] for a, b in WIN_UP]
    wall_x(P, "zdivo_omitka", X0, X1, ZS - T, ZS, 0.0, EAVE, holes)
    P.bb((X0, BASE + 3.0, ZS - T), (X1, 0.0, ZS), "zdivo_hole")
    # zapadni stit (zdeny do vysky okapu)
    wall_z(P, "zdivo_omitka", ZN, ZS - T, X0, X0 + T, 0.0, EAVE)
    P.bb((X0, BASE + 3.0, ZN), (X0 + T, 0.0, ZS - T), "zdivo_hole")
    # sokl z lomoveho kamene - prerusený ve dverich
    cuts = sorted([DOOR_HALL[:2], DOOR_PANTRY[:2]])
    x = X0 - 0.07
    for a, b in cuts + [(X1, X1)]:
        if a - x > 0.05:
            P.bb((x, 0.0, ZS - 0.02), (a, 0.48, ZS + 0.08), "zdivo_hole")
            P.bb((x, 0.46, ZS - 0.02), (a, 0.52, ZS + 0.1), "kvadr_sedy")
        x = b
    P.bb((X0 - 0.08, 0.0, ZN), (X0 + 0.02, 0.48, ZS + 0.08), "zdivo_hole")
    # narozi z kvadru
    F.quoins(P, X0, ZS, 1, -1, 0.0, EAVE, 0.7, 0.4, 0.33)
    # kamenna ostění
    _gothic_portal(P, (DOOR_HALL[0] + DOOR_HALL[1]) / 2, (DOOR_HALL[1] - DOOR_HALL[0]) / 2, 1.75, ZS)
    _rect_portal(P, (DOOR_PANTRY[0] + DOOR_PANTRY[1]) / 2, DOOR_PANTRY[1] - DOOR_PANTRY[0], DOOR_PANTRY[3], ZS)
    for a, b in WIN_GROUND:
        _frame_z(P, (a + b) / 2, b - a, 1.3, 2.6, ZS, 1)
    for a, b in WIN_UP:
        _cross_window(P, (a + b) / 2, b - a, 4.9, 6.2, ZS)
    # podlahy prizemi
    P.bb((X0 + T, -0.2, ZN), (X1, 0.02, ZS - T), "dlazba", collide=True)
    # vnitrni omitka (tenka vrstva na vnitrnich licich, se stejnymi otvory)
    _liners(P)
    # komin
    P.bb((15.5, 3.0, -11.5), (16.9, 13.3, -10.1), "zdivo_hole", collide=True)
    P.bb((15.38, 13.3, -11.62), (17.02, 13.44, -9.98), "kvadr_sedy")
    for sx in (-1, 1):
        P.bb((16.2 + sx * 0.5 - 0.12, 13.44, -11.4), (16.2 + sx * 0.5 + 0.12, 13.75, -10.2), "zdivo_hole")
    P.bb((15.6, 13.75, -11.45), (16.8, 13.85, -10.15), "kvadr_sedy")
    P.bb((15.8, 13.42, -11.2), (16.6, 13.44, -10.4), "saze")
    P.commit(coll)

    W = Part("PalacKrov", bevel=0.012)
    # strecha: dve roviny, hreben podel X
    xa, xb = X0 - 0.55, OX + 0.4
    zn, zs = OZN - 0.5, -5.3
    shingle_roof(W, (xa, roof_y(zn), zn), (xb, roof_y(zn), zn), (xb, RIDGE_Y, RIDGE_Z), (xa, RIDGE_Y, RIDGE_Z))
    shingle_roof(W, (xb, roof_y(zs), zs), (xa, roof_y(zs), zs), (xa, RIDGE_Y, RIDGE_Z), (xb, RIDGE_Y, RIDGE_Z))
    # stitova prkna na zapadnim konci
    for zz in (zn, zs):
        a = Vector((xa - 0.02, roof_y(zz) - 0.05, zz))
        b = Vector((xa - 0.02, RIDGE_Y - 0.05, RIDGE_Z))
        W.beam(a, b, 0.05, 0.28, "dub_ven")
    # zapadni stit z prken nad okapem
    gx = X0 + 0.22
    z = OZN + 0.25
    while z < ZS - 0.02:
        w = min(0.24 + jit(0.03), ZS - z)
        ztop = min(roof_y(z), roof_y(z + w)) - 0.1
        if ztop > EAVE + 0.05:
            W.bb((gx - 0.025, EAVE - 0.05, z), (gx + 0.025, ztop, z + w - 0.008), "prkna_ven", grain="y")
        z += w
    for yy in (EAVE + 0.4, 9.6):
        hw = (RIDGE_Y - yy) / 0.9
        W.beam((gx - 0.06, yy, RIDGE_Z - hw + 0.3), (gx - 0.06, yy, RIDGE_Z + hw - 0.3), 0.06, 0.14, "dub_ven")
    # okenko na pude ve stitu
    W.bb((gx - 0.09, 9.0, RIDGE_Z - 0.3), (gx - 0.03, 9.6, RIDGE_Z + 0.3), "dira")
    # krokve, hambalky, pozednice
    x = X0 + 1.0
    while x < X1 - 0.3:
        W.beam((x, EAVE - 0.1, ZN + 0.1), (x, RIDGE_Y - 0.25, RIDGE_Z), 0.14, 0.18, "dub", j=1)
        W.beam((x, EAVE - 0.1, ZS - T + 0.1), (x, RIDGE_Y - 0.25, RIDGE_Z), 0.14, 0.18, "dub", j=1)
        W.beam((x, 9.3, RIDGE_Z - 2.25), (x, 9.3, RIDGE_Z + 2.25), 0.12, 0.16, "dub", j=1)
        x += 1.85
    W.beam((X0 + T, EAVE - 0.14, ZN + 0.14), (X1, EAVE - 0.14, ZN + 0.14), 0.24, 0.24, "dub", j=0.5)
    W.beam((X0 + T, EAVE - 0.14, ZS - T - 0.14), (X1, EAVE - 0.14, ZS - T - 0.14), 0.24, 0.24, "dub", j=0.5)
    W.beam((xa, RIDGE_Y - 0.12, RIDGE_Z), (xb, RIDGE_Y - 0.12, RIDGE_Z), 0.18, 0.2, "dub")
    # dozdivka a omitka pod strechou
    W.bb((X0 + T, EAVE, ZN - 0.3), (X1, roof_y(ZN - 0.3) - 0.03, ZN + 0.04), "omitka")
    W.bb((X0 + T, EAVE, ZS - T), (X1, roof_y(ZS - T + 0.25) - 0.03, ZS - T + 0.25), "omitka")
    # strop prizemi = podlaha patra: tramy a prkna
    z = ZN + 0.5
    while z < ZS - T:
        W.beam((X0 + T - 0.1, F1 - 0.42, z), (X1 + 0.1, F1 - 0.42, z), 0.22, 0.28, "dub", j=1)
        z += 1.08
    W.bb((X0 + T, F1 - 0.28, ZN), (X1, F1 - 0.24, ZS - T), "prkna")
    W.bb((X0 + T, F1 - 0.04, ZN), (X1, F1, ZS - T), "prkna", collide=True)
    # pricky
    wall_z(W, "omitka", ZN, ZS - T, 2.8, 3.2, 0.02, F1 - 0.28, [[-11.2, -10.0, 0.02, 2.1]])
    wall_z(W, "omitka", ZN, ZS - T, 6.8, 7.2, F1, EAVE, [[-9.7, -8.5, F1, 5.95]])
    q = [Vector((7.0, EAVE, ZN)), Vector((7.0, roof_y(ZN) - 0.2, ZN)), Vector((7.0, RIDGE_Y - 0.2, RIDGE_Z)),
         Vector((7.0, roof_y(ZS - T) - 0.2, ZS - T)), Vector((7.0, EAVE, ZS - T))]
    W.prism(list(reversed(q)), Vector((0.2, 0, 0)), "omitka")
    for (zc, y1, w) in ((-10.6, 2.1, 1.2), (-9.1, 5.95, 1.2)):
        xw = 3.0 if y1 < 3 else 7.0
        W.bb((xw - 0.25, y1, zc - w / 2 - 0.12), (xw + 0.25, y1 + 0.18, zc + w / 2 + 0.12), "dub")
    # dverni ramy patra a okenice prizemi
    for a, b in DOOR_UP:
        _wood_door(W, a, b, F1, 5.95, ZS, open_deg=-60 if a < 5 else 0)
    for a, b in WIN_GROUND:
        _grille(W, (a + b) / 2, b - a, 1.3, 2.6, ZS - 0.12)
        _shutters(W, (a + b) / 2, b - a, 1.3, 2.6, ZS - T, inside=True)
    _door_leaves(W)
    W.commit(coll)


def _liners(P: Part):
    """Vnitrni omitka: tenke desky na vnitrnich licich zdi s otvory."""
    t = 0.025
    nw = [[a, b, ya, yb] for (a, b, ya, yb) in NORTH_WIN]
    wall_x(P, "omitka", X0 + T, X1, ZN, ZN + t, 0.02, EAVE, nw, collide=False)
    holes = [list(DOOR_HALL), list(DOOR_PANTRY)] + [[a, b, 1.3, 2.6] for a, b in WIN_GROUND] + \
            [[a, b, F1, 5.95] for a, b in DOOR_UP] + [[a, b, 4.9, 6.2] for a, b in WIN_UP]
    wall_x(P, "omitka", X0 + T, X1, ZS - T - t, ZS - T, 0.02, EAVE, holes, collide=False)
    wall_z(P, "omitka", ZN, ZS - T, X1 - t, X1, 0.02, EAVE, [[-9.4, -8.5, 4.9, 6.3]], collide=False)
    wall_z(P, "omitka", ZN, ZS - T, X0 + T, X0 + T + t, 0.02, EAVE, collide=False)
    # malovany sokl a vlys v sini
    for (xa, xb) in ((3.2, X1),):
        P.bb((xa, 0.02, ZN + t), (xb, 0.95, ZN + t + 0.006), "malba_okr")
        P.bb((xa, 0.02, ZS - T - t - 0.006), (xb, 0.95, ZS - T - t), "malba_okr")
        P.bb((xa, 2.95, ZN + t), (xb, 3.08, ZN + t + 0.006), "malba_cervena")
        P.bb((xa, 2.95, ZS - T - t - 0.006), (xb, 3.08, ZS - T - t), "malba_cervena")
        P.bb((xa, 0.95, ZN + t), (xb, 1.0, ZN + t + 0.006), "malba_cervena")
        P.bb((xa, 0.95, ZS - T - t - 0.006), (xb, 1.0, ZS - T - t), "malba_cervena")


def _frame_z(P: Part, cx, w, y0, y1, z, o):
    """Kamenne ostění okna na lici z (o = smer ven)."""
    w2 = w / 2 - 0.01
    P.bb((cx - w2 - 0.2, y0 - 0.15, z - o * 0.03), (cx + w2 + 0.2, y0 + 0.01, z + o * 0.12), "kvadr")
    P.bb((cx - w2 - 0.17, y1 - 0.01, z - o * 0.03), (cx + w2 + 0.17, y1 + 0.24, z + o * 0.07), "kvadr")
    for sx in (-1, 1):
        P.bb((cx + sx * w2, y0, z - o * 0.03), (cx + sx * (w2 + 0.16), y1, z + o * 0.06), "kvadr")


def _frame_x(P: Part, cz, w, y0, y1, x, o):
    w2 = w / 2 - 0.01
    P.bb((x - o * 0.03, y0 - 0.15, cz - w2 - 0.2), (x + o * 0.12, y0 + 0.01, cz + w2 + 0.2), "kvadr")
    P.bb((x - o * 0.03, y1 - 0.01, cz - w2 - 0.17), (x + o * 0.07, y1 + 0.24, cz + w2 + 0.17), "kvadr")
    for sz in (-1, 1):
        P.bb((x - o * 0.03, y0, cz + sz * w2), (x + o * 0.06, y1, cz + sz * (w2 + 0.16)), "kvadr")
    # olovene sklo zapustene v ostění
    P.bb((x - 0.32, y0, cz - w2), (x - 0.3, y1, cz + w2), "sklo")


def _cross_window(P: Part, cx, w, y0, y1, z):
    """Gotické křížové okno: kamenny ram, sloupek a prieka, olovene sklo."""
    _frame_z(P, cx, w, y0, y1, z, 1)
    ym = y0 + (y1 - y0) * 0.62
    P.bb((cx - 0.055, y0, z - 0.25), (cx + 0.055, y1, z + 0.03), "kvadr")
    P.bb((cx - w / 2, ym - 0.05, z - 0.25), (cx + w / 2, ym + 0.05, z + 0.03), "kvadr")
    P.bb((cx - w / 2, y0, z - 0.2), (cx + w / 2, y1, z - 0.18), "sklo")
    # olovene pruty
    for k in range(1, 6):
        yy = y0 + (y1 - y0) * k / 6
        P.bb((cx - w / 2, yy - 0.006, z - 0.17), (cx + w / 2, yy + 0.006, z - 0.165), "zelezo")
    for sx in (-1, 1):
        P.bb((cx + sx * w / 4 - 0.006, y0, z - 0.17), (cx + sx * w / 4 + 0.006, y1, z - 0.165), "zelezo")


def _gothic_portal(P: Part, cx, hw, spring, z):
    """Lomeny portal hlavniho vchodu do sine: klenaky, patky se zkosenim, vyplne v cviklech."""
    top = DOOR_HALL[3]
    r = (hw * hw + (top - spring) ** 2) / (2 * hw)
    pointed = r / hw - 1.0
    # cvikly (vyplne nad lomenym obloukem v otvoru zdi)
    n = 10
    for side in (-1, 1):
        c0 = cx - side * (r - hw)
        amax = math.acos((r - hw) / r)
        pts = []
        for i in range(n + 1):
            tt = i / n
            a = (math.pi - amax * tt) if side < 0 else (amax * tt)
            pts.append(Vector((c0 + r * math.cos(a), spring + r * math.sin(a), z)))
        poly = pts + [Vector((cx + side * hw, top, z))]
        if side < 0:
            poly = [Vector((cx - hw, spring, z))] + pts[1:] + [Vector((cx - hw, top, z))]
        # orientace: lice smerem +Z
        nrm = (poly[1] - poly[0]).cross(poly[2] - poly[0])
        if nrm.z < 0:
            poly.reverse()
        P.prism([p - Vector((0, 0, T + 0.02)) for p in poly], Vector((0, 0, T + 0.02)), "zdivo_omitka")
    F.arch_ring(P, cx, spring, hw, z + 0.08, 0.6, 0.36, 11, pointed, "kvadr", 1)
    # patky ostění se zkosenou hranou
    for sx in (-1, 1):
        y = 0.0
        k = 0
        while y < spring - 0.01:
            hh = min(0.36 + jit(0.03), spring - y)
            wd = 0.42 if k % 2 == 0 else 0.3
            P.bb((cx + sx * (hw - 0.01), y, z - 0.55), (cx + sx * (hw + wd), y + hh - 0.012, z + 0.08), "kvadr")
            y += hh
            k += 1
        P.beam((cx + sx * (hw + 0.0), 0.3, z + 0.08), (cx + sx * (hw + 0.0), spring, z + 0.08), 0.1, 0.1, "kvadr", up=(0, 0, 1))
    # schod pred vchodem
    P.bb((cx - hw - 0.35, -0.05, z - 0.02), (cx + hw + 0.35, 0.16, z + 0.55), "kvadr_sedy", collide=True)


def _rect_portal(P: Part, cx, w, h, z):
    hw = w / 2
    for sx in (-1, 1):
        P.bb((cx + sx * (hw - 0.01), 0.0, z - 0.5), (cx + sx * (hw + 0.24), h, z + 0.07), "kvadr")
    P.bb((cx - hw - 0.3, h - 0.01, z - 0.5), (cx + hw + 0.3, h + 0.34, z + 0.08), "kvadr")
    P.bb((cx - hw - 0.3, -0.05, z - 0.02), (cx + hw + 0.3, 0.12, z + 0.4), "kvadr_sedy", collide=True)


def _grille(P: Part, cx, w, y0, y1, z):
    for k in range(3):
        x = cx - w / 2 + w * (k + 1) / 4
        P.rod((x, y0, z), (x, y1, z), 0.016, 6, "zelezo")
    for yy in (y0 + (y1 - y0) / 3, y0 + 2 * (y1 - y0) / 3):
        P.rod((cx - w / 2, yy, z + 0.02), (cx + w / 2, yy, z + 0.02), 0.014, 6, "zelezo")


def _shutters(P: Part, cx, w, y0, y1, z, inside=True, deg=75):
    """Okenice: dve kridla otevrena ke zdi (z = vnitrni lic)."""
    s = -1 if inside else 1
    for sx in (-1, 1):
        hinge = Vector((cx + sx * (w / 2 + 0.02), (y0 + y1) / 2, z + s * 0.03))
        ang = math.radians(sx * s * deg)
        m = M(hinge) @ rot("Y", math.degrees(ang)) @ M((sx * -w / 4, 0, s * 0.02))
        PR.bx(P, m, (0, 0, 0), (w / 2 - 0.02, y1 - y0 - 0.04, 0.035), "prkna", yaw=0)
        for yy in (-0.3, 0.3):
            PR.bx(P, m, (0, yy * (y1 - y0) / 1.3, s * 0.025), (w / 2 - 0.04, 0.06, 0.02), "dub")
            PR.bx(P, m, (sx * 0.1, yy * (y1 - y0) / 1.3, s * 0.036), (w / 4, 0.025, 0.006), "zelezo")


def _wood_door(P: Part, a, b, y0, y1, z, open_deg=0):
    """Dubovy ram dveri na pavlac a dverni kridlo."""
    P.bb((a - 0.12, y0, z - T - 0.03), (a + 0.0, y1, z + 0.05), "dub")
    P.bb((b - 0.0, y0, z - T - 0.03), (b + 0.12, y1, z + 0.05), "dub")
    P.bb((a - 0.12, y1, z - T - 0.03), (b + 0.12, y1 + 0.18, z + 0.05), "dub")
    w = b - a
    hinge = Vector((a + 0.02, (y0 + y1) / 2, z - T + 0.06))
    m = M(hinge) @ rot("Y", open_deg) @ M((w / 2, 0, 0))
    _plank_leaf(P, m, w - 0.04, y1 - y0 - 0.04)


def _plank_leaf(P: Part, m, w, h, t=0.05):
    """Dverni kridlo ze svislych fosen s pricnymi lisnami a zeleznymi pasy."""
    n = max(3, int(w / 0.2))
    for k in range(n):
        x = -w / 2 + w * (k + 0.5) / n
        PR.bx(P, m, (x, 0, 0), (w / n - 0.006, h, t), "prkna", basis=Matrix.Rotation(-math.pi / 2, 3, "X"))
    for yy in (-0.32, 0.32):
        PR.bx(P, m, (0, yy * h, -t / 2 - 0.015), (w - 0.06, 0.12, 0.03), "dub")
        PR.bx(P, m, (-w * 0.15, yy * h + 0.0, t / 2 + 0.004), (w * 0.65, 0.05, 0.008), "zelezo")
    P.rod(PR.T(m, (w * 0.35, 0, t / 2)), PR.T(m, (w * 0.35, 0, t / 2 + 0.05)), 0.008, 5, "zelezo")
    P.lathe(m @ M((w * 0.35, 0, t / 2 + 0.05)) @ rot("X", 90), [(0.05, -0.006), (0.05, 0.006)], 12, "zelezo", False, False)


def _door_leaves(W: Part):
    # sin: dve kridla, jedno pootevrene dovnitr
    cx = (DOOR_HALL[0] + DOOR_HALL[1]) / 2
    hw = 0.88
    zf = ZS - 0.42
    _plank_leaf(W, M((cx + hw / 2, 1.42, zf)), hw - 0.02, 2.84, 0.07)
    m = M((cx - hw + 0.04, 1.42, zf - 0.02)) @ rot("Y", 68) @ M((hw / 2, 0, 0))
    _plank_leaf(W, m, hw - 0.02, 2.84, 0.07)
    # spiz: kridlo pootevrene
    cxp = (DOOR_PANTRY[0] + DOOR_PANTRY[1]) / 2
    m = M((DOOR_PANTRY[0] + 0.03, 1.05, ZS - 0.42)) @ rot("Y", 35) @ M((0.53, 0, 0))
    _plank_leaf(W, m, 1.04, 2.08)


# ------------------------------------------------------------------ pavlac

def gallery(coll):
    P = Part("Pavlac", bevel=0.012)
    gz0, gz1 = ZS, -5.6
    gx0, gx1 = X0, 14.2
    # podlaha z prken napric
    x = gx0
    while x < gx1 - 0.01:
        w = min(0.25 + jit(0.03), gx1 - x)
        P.bb((x, F1 - 0.07, gz0), (x + w - 0.01, F1, gz1 + jit(0.02)), "prkna_ven", grain="z")
        x += w
    P.cols.append((M(((gx0 + gx1) / 2, F1 - 0.04, (gz0 + gz1) / 2)), (gx1 - gx0, 0.08, gz1 - gz0)))
    posts = []
    x = gx0 + 0.15
    while x <= gx1 + 0.01:
        posts.append(x)
        x += 2.86
    zp = gz1 - 0.08
    for px in posts:
        P.beam((px, 0.0, zp), (px, roof_y(zp) - 0.14, zp), 0.2, 0.2, "dub_ven", j=1.2)
        P.cols.append((M((px, 3.0, zp)), (0.2, 6.0, 0.2)))
        P.lathe(M((px, -0.02, zp)), [(0.2, 0), (0.18, 0.12), (0.0, 0.12)], 8, "kvadr_sedy", phase=math.pi / 8)
        P.beam((px, F1 - 0.2, gz0 - 0.15), (px, F1 - 0.2, gz1 + 0.1), 0.16, 0.2, "dub_ven", j=1)
        # sedlo (sattlholz) a pasove vzpery
        P.beam((px - 0.55, F1 - 0.36, zp), (px + 0.55, F1 - 0.36, zp), 0.18, 0.14, "dub_ven", j=1)
        P.beam((px, 2.55, zp), (px + 0.8, F1 - 0.42, zp), 0.12, 0.12, "dub_ven", j=1)
        P.beam((px, 2.55, zp), (px - 0.8, F1 - 0.42, zp), 0.12, 0.12, "dub_ven", j=1)
        P.beam((px, F1 + 1.6, zp), (px + 0.6, roof_y(zp) - 0.3, zp), 0.1, 0.1, "dub_ven", j=1)
        P.beam((px, F1 + 1.6, zp), (px - 0.6, roof_y(zp) - 0.3, zp), 0.1, 0.1, "dub_ven", j=1)
    P.beam((gx0, F1 - 0.2, zp), (gx1, F1 - 0.2, zp), 0.18, 0.22, "dub_ven", j=0.5)
    P.beam((gx0 - 0.4, roof_y(zp) - 0.22, zp), (gx1 + 0.4, roof_y(zp) - 0.22, zp), 0.18, 0.2, "dub_ven", j=0.5)
    # zabradli s prkennymi kuzelkami
    P.beam((gx0, F1 + 1.0, zp), (gx1, F1 + 1.0, zp), 0.1, 0.1, "dub_ven", j=0.4)
    P.beam((gx0, F1 + 0.16, zp), (gx1, F1 + 0.16, zp), 0.08, 0.08, "dub_ven", j=0.4)
    bx = gx0 + 0.2
    while bx < gx1:
        m = M((bx, F1 + 0.58, zp))
        _baluster(P, m)
        bx += 0.24
    P.cols.append((M(((gx0 + gx1) / 2, F1 + 0.55, zp)), (gx1 - gx0, 1.1, 0.12)))
    P.beam((gx1, F1 + 1.0, gz0), (gx1, F1 + 1.0, gz1), 0.09, 0.1, "dub_ven", collide=True)
    P.beam((gx1, F1 + 0.5, gz0), (gx1, F1 + 0.5, gz1), 0.07, 0.08, "dub_ven")
    # schodiste ze dvora od zapadu
    sz = (gz0 + gz1) / 2
    F.stairs(P, Vector((-9.4, 0.0, sz)), Vector((1, 0, 0)), 6.4, F1, 1.25, 20, "prkna_ven")
    for s2 in (gz0 + 0.02, gz1 - 0.02):
        P.beam((-9.45, -0.1, s2), (gx0, F1 - 0.1, s2), 0.09, 0.3, "dub_ven", j=0.5)
    rx0 = -8.4
    ry0 = F1 * (rx0 + 9.4) / 6.4 + 0.95
    for s3 in (gz0 + 0.04, gz1 - 0.04):
        P.beam((rx0, ry0, s3), (gx0, F1 + 0.95, s3), 0.08, 0.1, "dub_ven", collide=True)
    for k in range(4):
        px2 = rx0 + (gx0 - rx0) * k / 3
        t = (px2 + 9.4) / 6.4
        for s3 in (gz0 + 0.04, gz1 - 0.04):
            P.beam((px2, F1 * t - 0.1, s3), (px2, F1 * t + 1.0, s3), 0.1, 0.1, "dub_ven", j=1)
        if 0 < k < 3:
            for s3 in (gz0 + 0.04, gz1 - 0.04):
                P.beam((px2, 0.0, s3), (px2, F1 * t - 0.1, s3), 0.14, 0.14, "dub_ven", j=1)
    P.commit(coll)


def _baluster(P: Part, m):
    """Vyrezavana prkenna kuzelka (silueta)."""
    prof = [(0.05, -0.42), (0.05, -0.3), (0.035, -0.22), (0.065, -0.05), (0.065, 0.05), (0.035, 0.22), (0.05, 0.3), (0.05, 0.42)]
    pts = [Vector((x, y, 0)) for x, y in prof] + [Vector((-x, y, 0)) for x, y in reversed(prof)]
    poly = [PR.T(m, p) for p in pts]
    d = m.to_3x3() @ Vector((0, 0, 0.03))
    poly = [p - d * 0.5 for p in poly]
    nrm = (poly[1] - poly[0]).cross(poly[2] - poly[0])
    if nrm.dot(d) < 0:
        poly.reverse()
    P.prism(poly, d, "prkna_ven")


# ------------------------------------------------------------------ interiery

def hall(coll):
    P = Part("Sin", bevel=0.008)
    cz = (ZN + ZS - T) / 2          # -10.8
    fx = X1
    # gotický krb: kamenna ostění, rimsa na krakorcich, omitnuta digestor
    P.bb((fx - 1.5, 0.0, cz - 1.7), (fx, 0.2, cz + 1.7), "kvadr_sedy", collide=True)
    for sz in (-1, 1):
        P.bb((fx - 1.05, 0.2, cz + sz * 1.35 - 0.22), (fx, 1.55, cz + sz * 1.35 + 0.22), "kvadr", collide=True)
        P.bb((fx - 1.25, 1.35, cz + sz * 1.35 - 0.24), (fx - 0.95, 1.6, cz + sz * 1.35 + 0.24), "kvadr")
    P.bb((fx - 1.3, 1.6, cz - 1.75), (fx, 1.95, cz + 1.75), "kvadr")
    P.bb((fx - 1.36, 1.95, cz - 1.8), (fx, 2.05, cz + 1.8), "kvadr")
    h0, h1 = 2.05, F1 - 0.3
    P.slab((fx - 1.2, h0, cz - 1.7), (fx - 1.2, h0, cz + 1.7), (fx - 0.6, h1, cz + 0.9), (fx - 0.6, h1, cz - 0.9), 0.1, "omitka")
    P.slab((fx - 1.2, h0, cz - 1.7), (fx, h0, cz - 1.7), (fx, h1, cz - 0.9), (fx - 0.6, h1, cz - 0.9), 0.1, "omitka")
    P.slab((fx, h0, cz + 1.7), (fx - 1.2, h0, cz + 1.7), (fx - 0.6, h1, cz + 0.9), (fx, h1, cz + 0.9), 0.1, "omitka")
    P.bb((fx - 0.05, 0.2, cz - 1.13), (fx - 0.02, 1.6, cz + 1.13), "saze")
    P.bb((fx - 0.95, 0.2, cz - 1.13), (fx - 0.04, 0.215, cz + 1.13), "popel")
    # ohen: polena na kozlicich, plameny a zhar
    for sz in (-1, 1):
        P.rod((fx - 0.75, 0.21, cz + sz * 0.45), (fx - 0.75, 0.42, cz + sz * 0.45), 0.018, 6, "zelezo")
        P.rod((fx - 0.75, 0.42, cz + sz * 0.45), (fx - 0.25, 0.32, cz + sz * 0.45), 0.018, 6, "zelezo")
    PR.logs(P, M((fx - 0.5, 0.25, cz), 90), 4, 0.8)
    P.ball((fx - 0.5, 0.22, cz), (0.45, 0.03, 0.3), "zhar", 12, 4)
    for k in range(5):
        P.lathe(M((fx - 0.5 + jit(0.15), 0.32, cz + (k - 2) * 0.14)), [(0.0, 0), (0.07, 0.06), (0.05, 0.22), (0.0, 0.42 + jit(0.1))], 7, "plamen")
    light((fx - 0.6, 0.65, cz), 900, (1.0, 0.45, 0.15), 0.3)
    PR.woodpile(P, M((fx - 0.4, 0.02, cz + 2.4), 90), 1.0, 4, 0.45)
    # stoly a lavice
    tx = 9.2
    PR.table(P, M((tx, 0.02, cz), 90), 6.4, 1.05)
    PR.bench(P, M((tx, 0.02, cz - 0.95), 90), 6.0)
    PR.bench(P, M((tx, 0.02, cz + 0.95), 90), 6.0)
    PR.chair(P, M((tx + 3.75, 0.02, cz), 90))
    ty = 0.82
    for k in range(6):
        px = tx - 2.6 + 1.04 * k
        PR.plate(P, (px, ty, cz - 0.3), k % 2 == 0)
        PR.plate(P, (px + 0.3, ty, cz + 0.32), k % 3 == 0)
        PR.mug(P, (px + 0.22, ty, cz - 0.18), "cin" if k % 2 else "hlina_dzban")
        PR.mug(P, (px + 0.05, ty, cz + 0.2))
    PR.jug(P, (tx - 1.4, ty, cz + 0.02), 1.15)
    PR.jug(P, (tx + 1.7, ty, cz - 0.04), 1.0, "glazura")
    PR.bread(P, (tx + 0.4, ty, cz))
    PR.bread(P, (tx - 2.2, ty, cz + 0.05), 0.8)
    PR.bowl(P, (tx - 0.3, ty, cz + 0.05), 0.16, "deska", "jablko")
    PR.apples(P, (tx + 1.1, ty, cz + 0.1), 4)
    P.ball((tx + 2.4, ty + 0.06, cz), (0.18, 0.08, 0.13), "maso", 12, 6)
    PR.plate(P, (tx + 2.4, ty, cz))
    for (dx, dz) in ((-0.6, 0.0), (2.5, 0.02)):
        p = PR.candle(P, (tx + dx, ty, cz + dz), True, 0.18)
        light(p, 25, (1.0, 0.55, 0.25), 0.02)
    for p in PR.chandelier(P, (tx, 2.55, cz), 0.75, F1 - 0.42, 10):
        pass
    light((tx, 2.75, cz), 140, (1.0, 0.55, 0.25), 0.4)
    # podel sten
    hx0 = 3.2
    PR.chest(P, M((hx0 + 0.45, 0.02, cz + 1.4), 90), 1.15)
    PR.shelf(P, M((hx0 + 0.25, 0.02, cz - 1.8), -90), 1.6, 1.9, 4)
    for k in range(3):
        PR.jug(P, (hx0 + 0.25, 0.135, cz - 2.4 + 0.5 * k), 0.9 + 0.1 * k)
        PR.plate(P, (hx0 + 0.25, 0.735, cz - 2.3 + 0.5 * k))
        PR.bowl(P, (hx0 + 0.25, 1.335, cz - 2.35 + 0.5 * k), 0.1, "hlina_dzban")
    PR.barrel(P, M((hx0 + 0.6, 0.02, ZN + 0.6)))
    PR.hanging(P, M((6.6, 3.2, ZN + 0.06), 180), 2.2, 1.9, "sukno_cervene")
    PR.hanging(P, M((12.0, 3.2, ZN + 0.06), 180), 2.2, 1.9, "sukno_modre")
    PR.rug(P, M((14.6, 0.02, cz)), 2.2, 3.2, "sukno_cervene")
    PR.shield(P, M((8.0, 2.6, ZS - T - 0.06)), "sukno_cervene", "bila")
    for sx in (-1, 1):
        PR.sword(P, M((8.0 + sx * 0.55, 1.95, ZS - T - 0.1), basis=Matrix.Rotation(sx * 0.6, 3, "Z")))
    for pos, nrm in (((4.2, 2.1, ZN + 0.03), 180), ((13.2, 2.1, ZS - T - 0.03), 0)):
        p = PR.torch(P, M(pos, nrm))
        light(p, 60, (1.0, 0.5, 0.2), 0.05)
    P.commit(coll)


def pantry(coll):
    P = Part("Spiz", bevel=0.006)
    px0 = X0 + T
    PR.barrel(P, M((px0 + 0.5, 0.02, ZN + 0.55)))
    PR.barrel(P, M((px0 + 1.25, 0.02, ZN + 0.5)))
    PR.barrel(P, M((px0 + 0.55, 0.02, ZN + 1.3)), 0.3, 0.8)
    PR.barrel(P, M((px0 + 2.0, 0.02, ZN + 0.6)), 0.36, 1.05)
    PR.shelf(P, M((2.55, 0.02, -12.6), 90), 2.2, 2.0, 4)
    for k in range(4):
        z = -13.4 + 0.5 * k
        PR.jug(P, (2.55, 0.135, z), 1.0)
        PR.bread(P, (2.55, 0.735, z))
        P.lathe(M((2.55, 1.335, z + 0.1)), [(0.0, 0), (0.15, 0), (0.15, 0.1), (0.0, 0.1)], 16, "syr")
        PR.bowl(P, (2.55, 1.935, z), 0.1, "hlina_dzban")
    PR.sack(P, M((px0 + 0.45, 0.02, -9.0)))
    PR.sack(P, M((px0 + 0.95, 0.02, -8.6)))
    PR.sack(P, M((px0 + 0.5, 0.02, -8.3)), 0.3, True)
    PR.crate(P, M((px0 + 0.5, 0.02, -10.2), 8))
    PR.crate(P, M((px0 + 0.55, 0.72, -10.25), -12), 0.55)
    PR.table(P, M((0.6, 0.02, -8.4), 90), 1.8, 0.8)
    PR.jug(P, (0.3, 0.82, -8.4))
    PR.bread(P, (0.9, 0.82, -8.35))
    p = PR.candle(P, (1.2, 0.82, -8.5), True)
    light(p, 20, (1.0, 0.55, 0.25), 0.02)
    # susene byliny a sunky na tramu
    for k in range(5):
        hx = -1.6 + 0.8 * k
        P.rod((hx, F1 - 0.56, -11.2), (hx, F1 - 0.9, -11.2), 0.004, 3, "lano")
        P.ball((hx, F1 - 1.05, -11.2), (0.09, 0.17, 0.09), "bylinky", 6, 5)
    for k in range(3):
        hx = -1.2 + 1.0 * k
        P.rod((hx, F1 - 0.56, -12.3), (hx, F1 - 1.0, -12.3), 0.004, 3, "lano")
        P.ball((hx, F1 - 1.28, -12.3), (0.13, 0.26, 0.1), "maso", 10, 6)
    P.commit(coll)


def chamber(coll):
    P = Part("Komnata", bevel=0.006)
    cx0 = X0 + T
    y = F1
    PR.table(P, M((4.5, y, -8.5), 90), 1.9, 0.85)
    PR.chair(P, M((4.5, y, -9.3), 180))
    PR.book(P, M((4.2, y + 0.78, -8.5), 12), "cervena")
    PR.book(P, M((4.24, y + 0.84, -8.48), -8), "zluta")
    p = PR.candle(P, (5.1, y + 0.78, -8.4), True, 0.16)
    light(p, 20, (1.0, 0.55, 0.25), 0.02)
    PR.jug(P, (3.8, y + 0.78, -8.35), 0.8)
    P.lathe(M((4.75, y + 0.78, -8.65)), [(0.0, 0), (0.03, 0), (0.03, 0.04), (0.01, 0.05), (0, 0.05)], 10, "hlina_dzban")
    P.rod((4.75, y + 0.82, -8.65), (4.82, y + 1.0, -8.7), 0.003, 3, "bila")
    PR.shelf(P, M((cx0 + 0.22, y, -11.5), -90), 2.2, 2.0, 4)
    cols = ["cervena", "modra", "zluta", "kuze", "cervena", "kuze", "modra"]
    for k in range(7):
        PR.book(P, M((cx0 + 0.22, y + 0.73, -12.4 + 0.12 * k), 0, basis=Matrix.Rotation(math.pi / 2, 3, "Z") @ Matrix.Rotation(math.pi / 2, 3, "Y")) @ M((0, -0.1, 0)), cols[k], 0.22, 0.3, 0.08)
        PR.jug(P, (cx0 + 0.22, y + 1.33, -12.3 + 0.4 * (k % 5)), 0.7)
    PR.chest(P, M((1.0, y, ZN + 0.4)), 1.2)
    PR.chest(P, M((5.6, y, ZN + 0.4)), 0.9)
    PR.rug(P, M((2.4, y, -10.6)), 3.2, 2.2, "sukno_modre")
    PR.hanging(P, M((3.9, y + 2.9, ZN + 0.06), 180), 2.6, 2.0, "sukno_okr")
    PR.stool(P, M((1.6, y, -9.6)))
    p = PR.brazier(P, (-0.2, y, -9.2))
    light(p, 80, (1.0, 0.35, 0.1), 0.2)
    p = PR.torch(P, M((6.77, y + 2.0, -12.4), 90))
    light(p, 50, (1.0, 0.5, 0.2), 0.05)
    P.commit(coll)


def bedroom(coll):
    P = Part("Loznice", bevel=0.006)
    y = F1
    bx, bz = 15.9, -12.7
    PR.bed(P, M((bx, y, bz), 180), 2.1, 1.5, cover="sukno_cervene")
    # nebesa
    for sx in (-0.75, 0.75):
        for sz in (-1.05, 1.05):
            P.beam((bx + sx, y, bz + sz), (bx + sx, y + 2.3, bz + sz), 0.08, 0.08, "dub", j=0.3)
    for sz in (-1.05, 1.05):
        P.beam((bx - 0.8, y + 2.3, bz + sz), (bx + 0.8, y + 2.3, bz + sz), 0.08, 0.1, "dub")
    for sx in (-0.75, 0.75):
        P.beam((bx + sx, y + 2.3, bz - 1.1), (bx + sx, y + 2.3, bz + 1.1), 0.08, 0.1, "dub")
    P.bb((bx - 0.8, y + 2.36, bz - 1.1), (bx + 0.8, y + 2.4, bz + 1.1), "sukno_cervene")
    # zavesy: zrasene pruhy
    for k in range(10):
        x = bx - 0.75 + 1.5 * k / 9
        P.bb((x - 0.08, y + 0.5, bz - 1.09 + 0.02 * (k % 2)), (x + 0.08, y + 2.3, bz - 1.06 + 0.02 * (k % 2)), "sukno_cervene")
    for k in range(5):
        z = bz - 1.05 + 0.6 * k / 4
        P.bb((bx + 0.76 + 0.02 * (k % 2), y + 0.6, z - 0.08), (bx + 0.79 + 0.02 * (k % 2), y + 2.3, z + 0.08), "sukno_cervene")
    PR.chest(P, M((12.6, y, ZN + 0.4)), 1.1)
    PR.rug(P, M((13.6, y, -11.4)), 2.6, 2.0, "sukno_zelene")
    PR.table(P, M((14.3, y, -13.45), 90), 1.0, 0.6, 0.72)
    p = PR.candle(P, (14.1, y + 0.72, -13.45), True, 0.17)
    light(p, 20, (1.0, 0.55, 0.25), 0.02)
    PR.jug(P, (14.6, y + 0.72, -13.5), 0.85)
    PR.book(P, M((14.3, y + 0.72, -13.3), 20), "kuze")
    PR.chair(P, M((13.2, y, -8.6), 200))
    # almara se dvermi
    ax = 7.45
    P.bb((7.22, y, -13.15), (7.68, y + 1.95, -11.65), "deska")
    P.bb((7.68, y + 0.05, -13.1), (7.71, y + 1.9, -12.42), "prkna", grain="y")
    P.bb((7.68, y + 0.05, -12.38), (7.71, y + 1.9, -11.7), "prkna", grain="y")
    for z in (-12.48, -12.32):
        P.ball((7.73, y + 1.0, z), (0.015, 0.015, 0.015), "zelezo", 6, 4)
    P.bb((7.2, y + 1.95, -13.2), (7.72, y + 2.05, -11.6), "dub")
    PR.bucket(P, (8.4, y, -13.4), True)
    PR.stool(P, M((9.0, y, -13.3)))
    PR.bowl(P, (9.0, y + 0.45, -13.3), 0.18, "hlina_dzban")
    p = PR.brazier(P, (16.3, y, -8.4))
    light(p, 80, (1.0, 0.35, 0.1), 0.2)
    PR.hanging(P, M((10.6, y + 2.9, ZN + 0.06), 180), 2.2, 1.9, "sukno_zelene")
    PR.shield(P, M((7.26, y + 2.2, -9.0), -90), "sukno_modre", "zluta")
    P.commit(coll)
