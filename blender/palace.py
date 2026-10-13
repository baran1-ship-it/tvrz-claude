"""Palac u severni hradby: dole hodovni sin a spiz, nahore komnata a loznice, na dvorni strane pavlac."""
import math

from mathutils import Matrix, Vector

import fort as F
import props as PR
import lib
from lib import INFO, M, Part, R, fire, jit, light, rot, shingle_roof, wall_x, wall_z

X0, X1, OX = -3.0, 17.0, 18.8
ZN, OZN, ZS = -14.0, -15.8, -7.0
T = 0.6
F1 = 3.9
EAVE = 7.5
RIDGE_Z, RIDGE_Y = -11.4, 11.46
HIP_Y = 9.2              # vyska polovalby na zapadnim stitu
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
    if lib.VYBAVENI:
        pantry(coll)
        chamber(coll)
        bedroom(coll)


# ------------------------------------------------------------------ obvodove zdi a strecha

def shell(coll):
    P = Part("Palac", bevel=0.025)
    # severni hradba v delce palace
    # severni hradba: vnejsi cast s okny, vnitrni cast s hlubokymi vyklenky (sedatka v oknech)
    wall_x(P, "zdivo", X0, OX, OZN, OZN + 0.5, BASE, EAVE, NORTH_WIN)
    wall_x(P, "zdivo_bile", X0, OX, OZN + 0.5, ZN, BASE, EAVE, [list(n[:4]) for n in niches()])
    W0 = Part("Vyklenky", bevel=0.01)
    for w_ in NORTH_WIN:
        _niche(P, W0, *w_)
    W0.commit(coll)
    for (xa, xb, ya, yb) in NORTH_WIN:
        _frame_z(P, (xa + xb) / 2, xb - xa, ya, yb, OZN, -1)
    # vychodni zed se stitem a oknem loznice
    wall_z(P, "zdivo", ZN, ZS, X1, OX, BASE, EAVE, [[-9.4, -8.5, 4.9, 6.3]])
    _frame_x(P, -8.95, 0.9, 4.9, 6.3, OX, 1)
    # stit zarovnany s licem zdi (tloustka smerem dovnitr)
    P.tri((OX, EAVE, ZS), (OX, EAVE, OZN), (OX, RIDGE_Y - 0.15, RIDGE_Z), 0.9, "zdivo")
    # dvorni pruceli
    holes = [list(DOOR_HALL), list(DOOR_PANTRY)]
    holes += [[a, b, 1.3, 2.6] for a, b in WIN_GROUND]
    up_holes = [[a, b, F1, 5.95] for a, b in DOOR_UP] + [[a, b, 4.9, 6.2] for a, b in WIN_UP]
    wall_x(P, "zdivo_omitka", X0, X1, ZS - T, ZS, 0.0, F1, holes)
    wall_x(P, "omitka_bila", X0, X1, ZS - T, ZS, F1, EAVE, up_holes)
    P.bb((X0 - 0.02, F1 - 0.12, ZS - 0.03), (X1, F1 + 0.04, ZS + 0.09), "kvadr_sedy")
    P.bb((X0, BASE + 3.0, ZS - T), (X1, 0.0, ZS), "zdivo_hole")
    # zapadni stit (zdeny do vysky okapu)
    wall_z(P, "zdivo_omitka", ZN, ZS - T, X0, X0 + T, 0.0, F1, [[-11.3, -10.5, 1.5, 2.5]])
    wall_z(P, "omitka_bila", ZN, ZS - T, X0, X0 + T, F1, EAVE, [[-11.6, -10.6, 4.9, 6.1]])
    _frame_x(P, -10.9, 0.8, 1.5, 2.5, X0, -1)
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
    # plasticke portaly ze stavebnice (kit): hlavni lomeny do sine, obycejny do spize
    import kit
    kit.doorway(P, M(((DOOR_HALL[0] + DOOR_HALL[1]) / 2, 0.0, ZS)), "hlavni", DOOR_HALL[1] - DOOR_HALL[0], DOOR_HALL[3], T,
                "lomeny", open_deg=70, double=True, open2=0.0)
    kit.doorway(P, M(((DOOR_PANTRY[0] + DOOR_PANTRY[1]) / 2, 0.0, ZS)), "obycejne", DOOR_PANTRY[1] - DOOR_PANTRY[0], DOOR_PANTRY[3], T,
                "segment", open_deg=35)
    for a, b in WIN_GROUND:
        _frame_z(P, (a + b) / 2, b - a, 1.3, 2.6, ZS, 1)

    # podlahy prizemi
    P.bb((X0 + T, -0.2, ZN), (X1, 0.02, ZS - T), "dlazba", collide=True)
    # vnitrni omitka (tenka vrstva na vnitrnich licich, se stejnymi otvory)
    _liners(P)
    # komin
    P.bb((15.6, F1 - 0.3, -11.5), (17.0, 13.3, -10.1), "zdivo_omitka", collide=True)
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
    yh = HIP_Y
    zhn, zhs = RIDGE_Z - (RIDGE_Y - yh) / 0.9, RIDGE_Z + (RIDGE_Y - yh) / 0.9
    xr = xa + (RIDGE_Y - yh) / 0.9
    # severni a jizni rovina: dolni cast az ke stitu, horni s polovalbou
    shingle_roof(W, (xa, roof_y(zn), zn), (xb, roof_y(zn), zn), (xb, yh, zhn), (xa, yh, zhn), ridge=False)
    shingle_roof(W, (xa, yh, zhn), (xb, yh, zhn), (xb, RIDGE_Y, RIDGE_Z), (xr, RIDGE_Y, RIDGE_Z))
    shingle_roof(W, (xb, roof_y(zs), zs), (xa, roof_y(zs), zs), (xa, yh, zhs), (xb, yh, zhs), ridge=False)
    shingle_roof(W, (xb, yh, zhs), (xa, yh, zhs), (xr, RIDGE_Y, RIDGE_Z), (xb, RIDGE_Y, RIDGE_Z))
    # polovalba
    shingle_roof(W, (xa, yh, zhs), (xa, yh, zhn), (xr, RIDGE_Y, RIDGE_Z), (xr, RIDGE_Y, RIDGE_Z), ridge=False)
    for zz in (zhn, zhs):
        a = Vector((xa, yh + 0.06, zz))
        n = (Vector((xr, RIDGE_Y, RIDGE_Z)) - a).cross(Vector((0, 0, 1)) if zz > RIDGE_Z else Vector((0, 0, -1)))
        W.beam(a, (xr, RIDGE_Y + 0.06, RIDGE_Z), 0.3, 0.05, "prkna_ven", up=(0, 1, 0))
    # stitova prkna na zapadnim konci
    for zz in (zn, zs):
        a = Vector((xa - 0.02, roof_y(zz) - 0.05, zz))
        b = Vector((xa - 0.02, yh - 0.05, zhn if zz < RIDGE_Z else zhs))
        W.beam(a, b, 0.05, 0.28, "dub_ven")
    W.beam((xa - 0.02, yh - 0.1, zhn), (xa - 0.02, yh - 0.1, zhs), 0.06, 0.2, "dub_ven")
    # cela prkna na vychodnim stitu: kryji hranu strechy pres stit
    for zz in (zn, zs):
        W.beam((xb + 0.03, roof_y(zz) - 0.12, zz), (xb + 0.03, RIDGE_Y - 0.06, RIDGE_Z), 0.05, 0.3, "dub_ven")
    # zapadni stit z prken nad okapem
    gx = X0 + 0.22
    z = OZN + 0.25
    while z < ZS - 0.02:
        w = min(0.24 + jit(0.03), ZS - z)
        ztop = min(roof_y(z), roof_y(z + w), HIP_Y) - 0.1
        if ztop > EAVE + 0.05:
            W.bb((gx - 0.025, EAVE - 0.05, z), (gx + 0.025, ztop, z + w - 0.008), "prkna_ven", grain="y")
        z += w
    for yy in (EAVE + 0.4,):
        hw = (RIDGE_Y - yy) / 0.9
        W.beam((gx - 0.06, yy, RIDGE_Z - hw + 0.3), (gx - 0.06, yy, RIDGE_Z + hw - 0.3), 0.06, 0.14, "dub_ven")
    # okenko na pude ve stitu
    W.bb((gx - 0.09, 8.3, RIDGE_Z - 0.3), (gx - 0.03, 8.9, RIDGE_Z + 0.3), "dira")
    # krokve, hambalky, pozednice
    x = X0 + 1.0
    while x < X1 - 0.3:
        W.beam((x, EAVE - 0.1, ZN + 0.1), (x, RIDGE_Y - 0.25, RIDGE_Z), 0.14, 0.18, "dub", j=1)
        W.beam((x, EAVE - 0.1, ZS - T + 0.1), (x, RIDGE_Y - 0.25, RIDGE_Z), 0.14, 0.18, "dub", j=1)
        W.beam((x, 9.3, RIDGE_Z - 2.25), (x, 9.3, RIDGE_Z + 2.25), 0.12, 0.16, "dub", j=1)
        x += 1.85
    W.beam((X0 + T, EAVE - 0.14, ZN + 0.14), (X1, EAVE - 0.14, ZN + 0.14), 0.24, 0.24, "dub", j=0.5)
    W.beam((X0 + T, EAVE - 0.14, ZS - T - 0.14), (X1, EAVE - 0.14, ZS - T - 0.14), 0.24, 0.24, "dub", j=0.5)
    W.beam((xr, RIDGE_Y - 0.12, RIDGE_Z), (xb, RIDGE_Y - 0.12, RIDGE_Z), 0.18, 0.2, "dub")
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
    # dvere z patra na pavlac: vnitrni dvere ve stavebnici (funkcni)
    import kit
    for a, b in DOOR_UP:
        kit.doorway(W, M(((a + b) / 2, F1, ZS)), "vnitrni", b - a, 5.95 - F1, T)
    for a, b in WIN_GROUND:
        _glazed(W, (a + b) / 2, b - a, 1.3, 2.6, ZS - 0.16)
        _shutters(W, (a + b) / 2, b - a, 1.3, 2.6, ZS - T, inside=True)
    # hrazdene patro: dvorni pruceli a zapadni stit
    from lib import half_timber, shutters_on
    ops = [(a - X0, b - X0, F1, 5.95) for a, b in DOOR_UP] + [(a - X0, b - X0, 4.9, 6.2) for a, b in WIN_UP]
    half_timber(W, (X0, 0, ZS), (X1, 0, ZS), (0, 0, 1), F1 + 0.04, EAVE, ops)
    for a, b in WIN_UP:
        shutters_on(W, (X0, 0, ZS), (X1, 0, ZS), (0, 0, 1), a - X0, b - X0, 4.9, 6.2, 115)
    half_timber(W, (X0, 0, ZN), (X0, 0, ZS), (-1, 0, 0), F1 + 0.04, EAVE, [(-11.6 - ZN, -10.6 - ZN, 4.9, 6.1)])
    shutters_on(W, (X0, 0, ZN), (X0, 0, ZS), (-1, 0, 0), -11.6 - ZN, -10.6 - ZN, 4.9, 6.1, 115)
    W.commit(coll)


def niches():
    """Vyklenky v severni zdi: (x0, x1, y0, y1, podlaha) - sirsi nez okno, od podlahy."""
    out = []
    for (a, b, ya, yb) in NORTH_WIN:
        cx = (a + b) / 2
        hw = 0.78 if ya > F1 else 0.72
        fl = F1 if ya > F1 else 0.02
        out.append((cx - hw, cx + hw, fl, yb + 0.38, fl))
    return out


def _niche(P: Part, W: Part, a, b, ya, yb):
    """Hluboky okenni vyklenek: kamenna sedatka po stranach, dubovy preklad,
    okno s dubovym ramem, nahore terckove olovene sklo, dole ciré tabulky."""
    cx = (a + b) / 2
    n = [x for x in niches() if abs((x[0] + x[1]) / 2 - cx) < 0.01][0]
    x0, x1, fl, top = n[0], n[1], n[4], n[3]
    zi, zo = ZN, OZN + 0.5            # vnitrni lic, lic okenni steny
    seat = fl + 0.46
    for sx, xs in ((-1, x0), (1, x1)):
        xa, xb = (xs, xs + 0.42) if sx < 0 else (xs - 0.42, xs)
        P.bb((xa, fl, zo + 0.02), (xb, seat - 0.06, zi - 0.03), "zdivo_bile", collide=True)
        sa, sb = (xa, xb + 0.03) if sx < 0 else (xa - 0.03, xb)
        P.bb((sa, seat - 0.07, zo + 0.02), (sb, seat, zi + 0.02), "kvadr_sedy", collide=True)
        # sednout si do vyklenku (ve hre A), pohled na protejsi sedatko a okno
        xm = (xa + xb) / 2
        INFO["use"].append({"kind": "sed", "pos": [xm, seat + 0.3, (zi + zo) / 2], "r": 1.5,
                            "sit": [xm, fl, (zi + zo) / 2 + 0.05], "h": 0.46, "yaw": -sx * math.pi / 2 + sx * 0.5})
    # kozesina a polstar na jednom sedatku
    P.ball((x0 + 0.22, seat + 0.02, (zi + zo) / 2), (0.2, 0.025, 0.5), "kozesina", 12, 4)
    P.ball((x1 - 0.2, seat + 0.07, zo + 0.35), (0.17, 0.08, 0.15), "sukno_cervene", 10, 5)
    # preklad
    W.beam((x0 - 0.15, top + 0.1, zi + 0.02), (x1 + 0.15, top + 0.1, zi + 0.02), 0.3, 0.22, "dub", up=(0, 1, 0), j=0.5)
    W.beam((x0, top + 0.02, (zi + zo) / 2), (x1, top + 0.02, (zi + zo) / 2), 0.15, 0.12, "dub", up=(0, 1, 0))
    # okno: ram, sloupek, prieka, sklo
    w = b - a
    zf = zo - 0.06
    for xx in (a, b):
        W.bb((xx - 0.05, ya, zf - 0.06), (xx + 0.05, yb, zf + 0.06), "dub")
    for yy in (ya, yb):
        W.bb((a - 0.05, yy - 0.05, zf - 0.06), (b + 0.05, yy + 0.05, zf + 0.06), "dub")
    ym = ya + (yb - ya) * 0.58
    W.bb((cx - 0.035, ya, zf - 0.05), (cx + 0.035, yb, zf + 0.05), "dub")
    W.bb((a, ym - 0.035, zf - 0.05), (b, ym + 0.035, zf + 0.05), "dub")
    W.bb((a, ym, zf - 0.008), (b, yb, zf + 0.008), "sklo_terce")
    W.bb((a, ya, zf - 0.008), (b, ym, zf + 0.008), "sklo_olovo")
    # parapet
    P.bb((a - 0.08, ya - 0.08, zo - 0.02), (b + 0.08, ya, zo + 0.3), "kvadr_sedy")


def _dormer(W: Part, xc, w=1.5, zf=-8.0):
    """Sedlovy vikyr na jizni rovine strechy: hrazdene celo s okenkem a okenicemi."""
    from lib import half_timber, shutters_on
    yb = roof_y(zf)
    yt = yb + 1.25
    hw = w / 2
    zr = RIDGE_Z + (RIDGE_Y - (yt + 0.55)) / 0.9          # kde hreben vikyre protne strechu
    ze = RIDGE_Z + (RIDGE_Y - yt) / 0.9                   # kde okap vikyre protne strechu
    # celo a bocni stenky
    W.bb((xc - hw, yb - 0.1, zf - 0.12), (xc + hw, yt, zf), "omitka_bila")
    for sx in (-1, 1):
        q = [Vector((xc + sx * hw, yb, zf - 0.1)), Vector((xc + sx * hw, yt, zf - 0.1)), Vector((xc + sx * hw, yt, ze))]
        if sx < 0:
            q.reverse()
        W.prism(q, Vector((-sx * 0.08, 0, 0)), "prkna_ven")
    half_timber(W, (xc - hw, 0, zf), (xc + hw, 0, zf), (0, 0, 1), yb, yt, [(0.35, w - 0.35, yb + 0.3, yt - 0.25)], bay=0.6, braces=False)
    shutters_on(W, (xc - hw, 0, zf), (xc + hw, 0, zf), (0, 0, 1), 0.35, w - 0.35, yb + 0.3, yt - 0.25, 120)
    # trojuhelnik stitku
    q = [Vector((xc - hw - 0.05, yt, zf)), Vector((xc + hw + 0.05, yt, zf)), Vector((xc, yt + 0.6, zf))]
    W.prism([p - Vector((0, 0, 0.1)) for p in q], Vector((0, 0, 0.1)), "prkna_ven")
    # sindelova striska
    for sx in (-1, 1):
        eA = Vector((xc + sx * (hw + 0.2), yt - 0.08, zf + 0.25))
        eB = Vector((xc + sx * (hw + 0.2), yt - 0.08, ze - 0.1))
        rB = Vector((xc, yt + 0.62, zr - 0.1))
        rA = Vector((xc, yt + 0.62, zf + 0.25))
        if sx < 0:
            shingle_roof(W, eA, eB, rB, rA, row=0.11, length=0.36)
        else:
            shingle_roof(W, eB, eA, rA, rB, row=0.11, length=0.36)


def _liners(P: Part):
    """Vnitrni omitka: tenke desky na vnitrnich licich zdi s otvory."""
    t = 0.025
    nw = [list(n[:4]) for n in niches()]
    wall_x(P, "omitka", X0 + T, X1, ZN, ZN + t, 0.02, EAVE, nw, collide=False)
    holes = [list(DOOR_HALL), list(DOOR_PANTRY)] + [[a, b, 1.3, 2.6] for a, b in WIN_GROUND] + \
            [[a, b, F1, 5.95] for a, b in DOOR_UP] + [[a, b, 4.9, 6.2] for a, b in WIN_UP]
    wall_x(P, "omitka", X0 + T, X1, ZS - T - t, ZS - T, 0.02, EAVE, holes, collide=False)
    wall_z(P, "omitka", ZN, ZS - T, X1 - t, X1, 0.02, EAVE, [[-9.4, -8.5, 4.9, 6.3]], collide=False)
    wall_z(P, "omitka", ZN, ZS - T, X0 + T, X0 + T + t, 0.02, EAVE, collide=False)


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


def _glazed(W: Part, cx, w, y0, y1, z):
    """Okno sine misto mrize: dubovy ram s krizem (sloupek a prieka), nahore terckove sklo, dole olovene."""
    for xx in (cx - w / 2, cx + w / 2):
        W.bb((xx - 0.05, y0, z - 0.05), (xx + 0.05, y1, z + 0.05), "dub")
    for yy in (y0, y1):
        W.bb((cx - w / 2 - 0.05, yy - 0.05, z - 0.05), (cx + w / 2 + 0.05, yy + 0.05, z + 0.05), "dub")
    ym = y0 + (y1 - y0) * 0.62
    W.bb((cx - 0.03, y0, z - 0.04), (cx + 0.03, y1, z + 0.04), "dub")
    W.bb((cx - w / 2, ym - 0.03, z - 0.04), (cx + w / 2, ym + 0.03, z + 0.04), "dub")
    W.bb((cx - w / 2, ym, z - 0.006), (cx + w / 2, y1, z + 0.006), "sklo_terce")
    W.bb((cx - w / 2, y0, z - 0.006), (cx + w / 2, ym, z + 0.006), "sklo_olovo")
    # kovane zavesy a zastrcky kridel
    for sx in (-1, 1):
        for yy in (y0 + 0.2, ym - 0.2, ym + 0.15, y1 - 0.15):
            W.bb((cx + sx * (w / 2 - 0.12), yy - 0.012, z - 0.06), (cx + sx * (w / 2 - 0.01), yy + 0.012, z - 0.05), "zelezo")


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
    """Dverni kridlo ze svislych fosen: na lici dve pricne lisny a sikma vzpera (tvar Z),
    hlavicky hrebu, kovane pasy, kruh na otevirani."""
    n = max(3, int(w / 0.18))
    for k in range(n):
        x = -w / 2 + w * (k + 0.5) / n
        PR.bx(P, m, (x, 0, 0), (w / n - 0.006, t, h + PR.R.uniform(-0.01, 0.01)), "okenice", basis=Matrix.Rotation(-math.pi / 2, 3, "X"))
    f = t / 2 + 0.015
    ys = (-0.33 * h, 0.33 * h)
    for yy in ys:
        PR.bx(P, m, (0, yy, f), (w - 0.04, 0.13, 0.03), "okenice")
        PR.bx(P, m, (0, yy, -f), (w - 0.04, 0.13, 0.03), "okenice")
        for k in range(max(3, int(w / 0.14))):
            x = -w / 2 + 0.08 + (w - 0.16) * k / max(1, int(w / 0.14) - 1)
            for dy in (-0.035, 0.035):
                P.ball(PR.T(m, (x, yy + dy, f + 0.017)), (0.009, 0.009, 0.006), "zelezo", 6, 3)
    # sikma vzpera mezi lisnami
    a = PR.T(m, (-w / 2 + 0.1, ys[0] + 0.07, f))
    b = PR.T(m, (w / 2 - 0.1, ys[1] - 0.07, f))
    P.beam(a, b, 0.11, 0.028, "okenice", up=m.to_3x3() @ Vector((0, 0, 1)))
    # kovane pasy s pantem
    for yy in ys:
        PR.bx(P, m, (-w * 0.12, yy + 0.1, t / 2 + 0.004), (w * 0.72, 0.045, 0.008), "zelezo")
    P.rod(PR.T(m, (w * 0.33, 0, f)), PR.T(m, (w * 0.33, 0, f + 0.05)), 0.008, 5, "zelezo")
    P.lathe(m @ M((w * 0.33, -0.06, f + 0.05)) @ rot("X", 90), [(0.055, -0.006), (0.055, 0.006)], 12, "zelezo", False, False)


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
    gx0, gx1 = X0, 16.95
    # podlaha z prken napric
    x = gx0
    while x < gx1 - 0.01:
        w = min(0.25 + jit(0.03), gx1 - x)
        P.bb((x, F1 - 0.07, gz0), (x + w - 0.01, F1, gz1 + jit(0.02)), "prkna_ven", grain="z")
        x += w
    P.cols.append((M(((gx0 + gx1) / 2, F1 - 0.04, (gz0 + gz1) / 2)), (gx1 - gx0, 0.08, gz1 - gz0)))
    # sloupy pavlace mimo vchody a okna (i se vzperami)
    posts = [-2.85, 1.5, 3.6, 5.9, 10.1, 13.0, 16.8]
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
    P.beam((gx1, F1 + 0.16, gz0), (gx1, F1 + 0.16, gz1), 0.08, 0.08, "dub_ven")
    bz = gz0 + 0.2
    while bz < gz1 - 0.1:
        _baluster(P, M((gx1, F1 + 0.58, bz), 90))
        bz += 0.24
    # schodiste ze dvora od zapadu
    sz = (gz0 + gz1) / 2
    F.stairs(P, Vector((-9.4, 0.0, sz)), Vector((1, 0, 0)), 6.4, F1, 1.25, 20, "prkna_ven")
    for s2 in (gz0 + 0.02, gz1 - 0.02):
        P.beam((-9.45, -0.1, s2), (gx0, F1 - 0.1, s2), 0.09, 0.3, "dub_ven", j=0.5)
    rx0 = -9.3
    ry0 = F1 * (rx0 + 9.4) / 6.4 + 0.95
    for s3 in (gz0 + 0.04, gz1 - 0.04):
        P.beam((rx0, ry0, s3), (gx0, F1 + 0.95, s3), 0.08, 0.1, "dub_ven", collide=True)
    # kuzelky i v zabradli schodu (sikmo, kazda svisla)
    for s3 in (gz0 + 0.04, gz1 - 0.04):
        P.beam((rx0, ry0 - 0.82, s3), (gx0, F1 + 0.13, s3), 0.07, 0.08, "dub_ven")
        bx2 = rx0 + 0.2
        while bx2 < gx0 - 0.1:
            yb = F1 * (bx2 + 9.4) / 6.4
            _baluster(P, M((bx2, yb + 0.53, s3)) @ Matrix.Diagonal((1, 0.92, 1, 1)))
            bx2 += 0.24
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
    fireplace(P, X1, cz)
    if not lib.VYBAVENI:
        # prazdna tvrz: krb zustava jako soucast stavby, vybaveni si hrac postavi sam
        P.commit(coll)
        return
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
    PR.hanging(P, M((7.9, 3.2, ZN + 0.16), 180), 1.8, 1.9, "sukno_cervene")
    PR.hanging(P, M((11.95, 3.2, ZN + 0.16), 180), 1.8, 1.9, "sukno_modre")
    PR.rug(P, M((14.6, 0.02, cz)), 2.2, 3.2, "sukno_cervene")
    PR.shield(P, M((8.0, 2.6, ZS - T - 0.06)), "sukno_cervene", "bila")
    for sx in (-1, 1):
        PR.sword(P, M((8.0 + sx * 0.55, 1.95, ZS - T - 0.1), basis=Matrix.Rotation(sx * 0.6, 3, "Z")))
    for pos, nrm in (((4.2, 2.1, ZN + 0.03), 180), ((13.2, 2.1, ZS - T - 0.03), 0)):
        p = PR.torch(P, M(pos, nrm))
        light(p, 60, (1.0, 0.5, 0.2), 0.05)
    P.commit(coll)


def fireplace(P: Part, fx, cz):
    """Gotický krb v sini: vyvysene ohniste z kvadru, ostění se sloupky, hlavicemi a stupnovitymi krakorci,
    rovny preklad z klinovych kamenu (zubovity), profilovana rimsa, omitnuta kapuce s narozim z kvadru a erbem,
    ktera plynule prechazi do kominu. Uvnitr litinova plotna, kozlice s polenty. Ohen se zapaluje a zhasina (A / X)."""
    import kit

    def W(u, y, v):                 # u = od zdi do mistnosti, v = podel zdi
        return Vector((fx - u, y, cz + v))

    def stone(u, y, v, su, sy, sv, mat="kvadr", cham=0.025):
        kit.stone(P, M(W(u, y, v)), (su, sy, sv), mat, cham=cham, rough=0.006)

    HW = 1.12                       # polovicni sirka topeniste
    D = 0.9                         # hloubka topeniste
    # ohniste: podlaha z velkych desek, predni obruba
    for k, (v0, v1) in enumerate(((-1.95, -1.0), (-1.0, -0.05), (-0.05, 0.9), (0.9, 1.95))):
        stone(0.72, 0.06, (v0 + v1) / 2, 1.42, 0.12, v1 - v0 - 0.012, "kvadr_sedy", 0.012)
    P.bb((fx - 1.44, -0.02, cz - 1.96), (fx, 0.115, cz + 1.96), "kvadr_sedy", collide=True)
    for k in range(5):
        v = -1.6 + k * 0.8
        stone(1.38, 0.09, v, 0.14, 0.18, 0.79, "kvadr_sedy", 0.02)
    P.bb((fx - 0.88, 0.122, cz - HW), (fx - 0.02, 0.13, cz + HW), "popel")
    # zadni stena a sikme boky topeniste (zcernale sazemi)
    P.bb((fx - 0.06, 0.12, cz - 0.95), (fx - 0.01, 1.8, cz + 0.95), "saze")
    for sv in (-1, 1):
        q = [W(0.03, 0.12, sv * 0.95), W(D, 0.12, sv * HW), W(D, 1.8, sv * HW), W(0.03, 1.8, sv * 0.95)]
        P.slab(*(q if sv > 0 else q[::-1]), 0.08, "saze")
    P.slab(W(0.03, 1.8, -0.95), W(0.03, 1.8, 0.95), W(D, 1.8, HW), W(D, 1.8, -HW), 0.06, "saze")
    # litinova plotna s obloukem a reliefem (kriz v kruhu)
    pts = [W(0.075, 0.13, -0.55), W(0.075, 0.13, 0.55), W(0.075, 0.78, 0.55)]
    for i in range(1, 12):
        a = math.pi * i / 12
        pts.append(W(0.075, 0.78 + 0.22 * math.sin(a), 0.55 * math.cos(a)))
    pts.append(W(0.075, 0.78, -0.55))
    P.prism(pts, Vector((0.025, 0, 0)), "zelezo")
    P.lathe(M(W(0.08, 0.6, 0)) @ rot("Z", 90), [(0.17, 0), (0.19, 0.015), (0.17, 0.03)], 20, "zelezo", False, False)
    P.bb((fx - 0.105, 0.45, cz - 0.015), (fx - 0.085, 0.75, cz + 0.015), "zelezo")
    P.bb((fx - 0.105, 0.585, cz - 0.15), (fx - 0.085, 0.615, cz + 0.15), "zelezo")
    # kovane kozlice (andirony) s kulickou a polena na nich
    for sv in (-1, 1):
        v = sv * 0.48
        P.rod(W(0.78, 0.12, v - 0.08), W(0.78, 0.12, v + 0.08), 0.018, 6, "zelezo")
        P.rod(W(0.78, 0.12, v), W(0.78, 0.5, v), 0.022, 8, "zelezo")
        P.ball(W(0.78, 0.54, v), (0.045, 0.045, 0.045), "zelezo", 10, 6)
        P.rod(W(0.78, 0.3, v), W(0.12, 0.2, v), 0.018, 6, "zelezo")
        P.rod(W(0.12, 0.2, v), W(0.12, 0.13, v), 0.016, 6, "zelezo")
    for k, (u, y, ln, r) in enumerate(((0.42, 0.3, 1.25, 0.075), (0.62, 0.32, 1.15, 0.07), (0.52, 0.45, 1.1, 0.065))):
        P.rod(W(u + jit(0.03), y, -ln / 2), W(u + jit(0.03), y + jit(0.02), ln / 2), r, 9, "kura")
    P.ball(W(0.5, 0.15, 0.0), (0.38, 0.04, 0.6), "saze", 12, 4)
    # ostění: patka, prisazeny sloupek s hlavici, nad nim stupnovity krakorec
    for sv in (-1, 1):
        vc = sv * (HW + 0.2)
        stone(1.05, 0.26, vc, 0.44, 0.28, 0.44)
        y = 0.4
        k = 0
        while y < 1.5:
            hh = min(0.36, 1.52 - y)
            stone(0.97 if k % 2 else 1.0, y + hh / 2, vc + (0.02 if k % 2 else 0), 0.36, hh - 0.01, 0.4)
            y += hh
            k += 1
        # prisazeny sloupek na celni strane
        P.lathe(M(W(1.2, 0.4, vc)), [(0.11, 0), (0.085, 0.06), (0.075, 0.1), (0.075, 1.0), (0.085, 1.05), (0.12, 1.12), (0.14, 1.18), (0.14, 1.22)],
                12, "kvadr", rnd=0.3)
        # krakorce: tri vrstvy vystupujici do mistnosti
        for j, (u1, yy) in enumerate(((1.3, 1.62), (1.4, 1.74), (1.48, 1.86))):
            P.bb((fx - u1, yy - 0.06, cz + vc - 0.22), (fx - 0.8, yy + 0.06, cz + vc + 0.22), "kvadr")
    # preklad: rovny zubovity oblouk z 7 klinu, stredovy zaverak mirne vystupuje
    n = 7
    span = 2 * (HW + 0.42)
    for i in range(n):
        v0 = -span / 2 + span * i / n
        v1 = v0 + span / n
        k = 0.08 if i == n // 2 else 0.0
        stone(1.1 + k * 0.3, 2.13, (v0 + v1) / 2, 0.68 + k, 0.42 + k * 0.6, v1 - v0 - 0.012, cham=0.02)
    # profilovana rimsa (dva odstupnovane pasy a zlabek)
    P.bb((fx - 1.56, 2.34, cz - span / 2 - 0.12), (fx, 2.44, cz + span / 2 + 0.12), "kvadr")
    P.bb((fx - 1.5, 2.44, cz - span / 2 - 0.06), (fx, 2.5, cz + span / 2 + 0.06), "kvadr")
    P.lathe(M(W(1.5, 2.36, -span / 2 - 0.12)) @ rot("X", -90), [(0.04, 0), (0.04, span + 0.24)], 8, "kvadr")
    # kapuce: lichobezniky od rimsy ke stropu, prechazi do kominu (pudorys kominu = vrch kapuce)
    yb, yt = 2.5, F1 - 0.28
    hb, ht = span / 2 + 0.02, 0.7
    ub, ut = 1.46, 1.4
    P.slab(W(ub, yb, hb), W(ub, yb, -hb), W(ut, yt, -ht), W(ut, yt, ht), 0.1, "omitka_bila")
    for sv in (-1, 1):
        a, b, c, d = W(0.0, yb, sv * hb), W(ub, yb, sv * hb), W(ut, yt, sv * ht), W(0.0, yt, sv * ht)
        P.slab(*((a, b, c, d) if sv < 0 else (d, c, b, a)), 0.1, "omitka_bila")
        # narozi kapuce z kvadru (stridave delsi a kratsi)
        for j in range(4):
            t0, t1 = j / 4, (j + 1) / 4
            p0 = W(ub + (ut - ub) * t0, yb + (yt - yb) * t0, sv * (hb + (ht - hb) * t0))
            p1 = W(ub + (ut - ub) * t1, yb + (yt - yb) * t1, sv * (hb + (ht - hb) * t1))
            P.beam(p0 + Vector((-0.02, 0, -sv * 0.02)), p1 + Vector((-0.02, 0, -sv * 0.02)), 0.24 if j % 2 else 0.16, 0.12, "kvadr", up=(1, 0, 0))
    # erb na kapuci
    PR.shield(P, M(W(ub + 0.03 + (ut - ub) * 0.45, yb + (yt - yb) * 0.45, 0)) @ rot("Y", -90) @ rot("X", -2), "sukno_cervene", "bila")
    P.cols.append((M(W(0.75, 1.2, 0)), (1.5, 2.4, 2 * HW + 1.0)))
    # ohen (zapaluje / zhasina se ve hre), zvuk a kour z kominu
    fire("hearth", W(0.48, 0.3, 0.0), name="krb", size=1.0, zap=True, svetlo=[-0.75, 0.6, 0.0])
    INFO["use"].append({"kind": "fire", "pos": list(W(1.5, 0.9, 0.0)), "r": 2.2, "name": "krb"})
    INFO["smoke"].append([16.3, 13.9, -10.8])


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
    p = PR.torch(P, M((X0 + T + 0.03, 2.1, -10.0), -90))
    light(p, 50, (1.0, 0.5, 0.2), 0.05)
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


def _room_decor(P: Part, y, walls, paint="malba_modra", wains=1.0, band_top=2.75):
    """Dreveny obklad (svisla prkna s listou) a sablonovy malovany pas na omitce.
    walls: [(osa, souradnice lice, smer do mistnosti, od, do, [(a, b), ...] mezery)]"""
    for axis, c, inw, s0, s1, gaps in walls:
        segs = []
        cur = s0
        for a, b in sorted(gaps):
            if a > cur + 0.05:
                segs.append((cur, a))
            cur = max(cur, b)
        if s1 > cur + 0.05:
            segs.append((cur, s1))
        for a, b in segs:
            def box(lo_s, hi_s, ylo, yhi, d0, d1, mat, grain="auto"):
                if axis == "z":
                    P.bb((lo_s, ylo, c + inw * d0), (hi_s, yhi, c + inw * d1), mat, grain=grain)
                else:
                    P.bb((c + inw * d0, ylo, lo_s), (c + inw * d1, yhi, hi_s), mat, grain=grain)
            # obklad z prken
            k = a
            while k < b - 0.02:
                w = min(0.21 + jit(0.03), b - k)
                box(k + 0.004, k + w - 0.004, y, y + wains, 0.03, 0.055, "deska", "y")
                k += w
            box(a, b, y + wains - 0.02, y + wains + 0.06, 0.03, 0.09, "dub")
            box(a, b, y, y + 0.12, 0.03, 0.075, "dub")
            # malovany pas nad obkladem
            box(a, b, y + wains + 0.06, y + band_top, 0.026, 0.03, paint)
            box(a, b, y + band_top, y + band_top + 0.06, 0.026, 0.034, "malba_cervena")


def chamber(coll):
    P = Part("Komnata", bevel=0.006)
    cx0 = X0 + T
    y = F1
    _room_decor(P, y, [
        ("z", ZN, 1, cx0, 6.8, [(1.22, 2.78)]),
        ("z", ZS - T, -1, cx0, 6.8, [(0.4, 1.7), (3.95, 5.05)]),
        ("x", cx0, 1, ZN, ZS - T, [(-12.7, -10.2), (-11.65, -10.55)]),
        ("x", 6.8, -1, ZN, ZS - T, [(-9.8, -8.4)]),
    ], "malba_modra")
    PR.candelabrum(P, (5.9, y, -12.9))
    light((5.9, y + 1.75, -12.9), 70, (1.0, 0.55, 0.25), 0.15)
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
    PR.chest(P, M((-1.3, y, ZN + 0.4)), 1.2)
    PR.chest(P, M((5.6, y, ZN + 0.4)), 0.9)
    PR.rug(P, M((2.4, y, -10.6)), 3.2, 2.2, "sukno_modre")
    PR.hanging(P, M((3.9, y + 2.9, ZN + 0.16), 180), 2.6, 2.0, "sukno_okr")
    PR.stool(P, M((1.6, y, -9.6)))
    p = PR.brazier(P, (-0.2, y, -9.2))
    light(p, 80, (1.0, 0.35, 0.1), 0.2)
    p = PR.torch(P, M((6.77, y + 2.0, -12.4), 90))
    light(p, 50, (1.0, 0.5, 0.2), 0.05)
    P.commit(coll)


def bedroom(coll):
    P = Part("Loznice", bevel=0.006)
    y = F1
    _room_decor(P, y, [
        ("z", ZN, 1, 7.2, X1, [(11.22, 12.78), (14.8, 17.0)]),
        ("z", ZS - T, -1, 7.2, X1, [(10.3, 11.6), (13.45, 14.55)]),
        ("x", X1, -1, ZN, ZS - T, [(-11.6, -10.0), (-9.45, -8.45)]),
        ("x", 7.2, 1, ZN, ZS - T, [(-13.2, -11.6), (-9.8, -8.4)]),
    ], "malba_cervena_vzor")
    PR.candelabrum(P, (13.9, y, -9.6))
    light((13.9, y + 1.75, -9.6), 70, (1.0, 0.55, 0.25), 0.15)
    bx, bz = 15.9, -12.7
    PR.bed(P, M((bx, y, bz), 180), 2.1, 1.5, cover="sukno_cervene")
    INFO["use"].append({"kind": "bed", "pos": [bx, y + 0.7, bz + 0.3], "r": 2.2})
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
    PR.chest(P, M((9.4, y, ZN + 0.4)), 1.1)
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
    PR.hanging(P, M((9.4, y + 2.9, ZN + 0.16), 180), 1.8, 1.7, "sukno_zelene")
    PR.shield(P, M((7.26, y + 2.2, -9.0), -90), "sukno_modre", "zluta")
    P.commit(coll)
