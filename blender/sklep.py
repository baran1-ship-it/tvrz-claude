"""Sklepeni pod vezi tvrze (Misa 9. 11.): zaznam pravidla/svet/lokace.json sklep_tvrz.

Postup podle Puchartu (valena klenba, chodba s kobkami a dvermi, sklad se sudy, schody s test cestou dolu i ven),
postaveno nasi stavebnici (lib.Part, kit.doorway, fort.stairs). Vstup ve vezi pod prvnim ramenem schodu do patra
(otvor v podlaze, zabradli a zaklad veze jako ram: fort.tower). Souradnice sveta (vez uz posunuta o fort.TX).
Sudy a pytle jsou kusy katalogu v pravidla/svet/nabytek.json svet (budova tvrz_sklep)."""
import json
import math
import os

from mathutils import Matrix, Vector

import kit
import lib
import props as PR
from lib import M, Part, light, wall_x, wall_z

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def zaznam():
    with open(os.path.join(_ROOT, "pravidla", "svet", "lokace.json"), encoding="utf-8") as f:
        return json.load(f)["sklep_tvrz"]


def _pasmo_vyska():
    with open(os.path.join(_ROOT, "pravidla", "pravidla_sveta.json"), encoding="utf-8") as f:
        return float(json.load(f)["pasma"]["budova"]["svetla_vyska_m"])


def schody_geom(s=None):
    """Schody dolu: (x0, x1, z_horni, z_dolni, n, vyska stupne, y podlahy). Spolecne pro sklep.py a fort.tower."""
    s = s or zaznam()
    sc = s["schody"]
    n = round(-s["y"] / sc["stupen_vyska"])
    return sc["x"][0], sc["x"][1], sc["z_horni"], sc["z_horni"] + n * sc["stupen_hloubka"], n, -s["y"] / n, s["y"]


def kontrola(s=None):
    """Hlidac (chyba exportu, ne varovani): otvor v terenu jen pod budovou (v pudorysu veze) a svetla vyska nad schody
    dolu >= pasma.budova.svetla_vyska_m (pod ramenem schodu nahoru: z -11,3 y 0 -> z_horni y 3,25; dal podlaha prizemi)."""
    s = s or zaznam()
    a, b, c, d = s["otvor_terenu"]
    vx0, vx1, vz0, vz1 = s["vez"]
    if not (vx0 <= a < b <= vx1 and vz0 <= c < d <= vz1):
        raise ValueError("sklep: otvor_terenu %s mimo pudorys veze %s - teren se vyhlubuje jen pod budovou" % (s["otvor_terenu"], s["vez"]))
    x0, x1, zh, zd, n, h, y = schody_geom(s)
    pas = _pasmo_vyska()
    sc = s["schody"]
    # spodni hrana ramene nahoru (fort.tower: 16 stupnu 3,25 m na 2,9 m od z -11,3) a strop prizemi
    z_paty, beh, vys = -11.3, 2.9, 3.25
    nejmin = 99.0
    for k in range(n + 1):
        z = zh + k * sc["stupen_hloubka"]
        yd = -k * h
        strop = sc["strop_prizemi_y"] if z > z_paty else vys * (z_paty - z) / beh - 0.3
        nejmin = min(nejmin, strop - yd)
    if nejmin < pas:
        raise ValueError("sklep: svetla vyska nad schody %.2f m < %.2f m (pasma.budova.svetla_vyska_m)" % (nejmin, pas))
    return nejmin


def v_otvoru(x0, x1, z0, z1):
    """Zasahuje plocha [x0,x1]x[z0,z1] do otvoru v terenu (fort.terrain, yard_ground: plocha se vynecha)?"""
    a, b, c, d = zaznam()["otvor_terenu"]
    return x0 < b and x1 > a and z0 < d and z1 > c


def _klenba(P: Part, osa, a0, a1, s0, s1, y_patka, vzepeti, mat="zdivo", n=10):
    """Valena (segmentova) klenba: osa 'z' (pres x od s0 do s1, podel z od a0 do a1) nebo 'x'. Obe strany plochy
    (zespodu je videt, shora ji skryva teren)."""
    w = (s1 - s0) / 2
    r = (w * w + vzepeti * vzepeti) / (2 * vzepeti)
    yc = y_patka + vzepeti - r
    sc = (s0 + s1) / 2
    pts = []
    for i in range(n + 1):
        s = s0 + (s1 - s0) * i / n
        pts.append((s, yc + math.sqrt(max(0.0, r * r - (s - sc) ** 2))))

    def V(s, y, a):
        return Vector((s, y, a)) if osa == "z" else Vector((a, y, s))
    for i in range(n):
        (sa, ya), (sb, yb) = pts[i], pts[i + 1]
        q = [V(sa, ya, a0), V(sb, yb, a0), V(sb, yb, a1), V(sa, ya, a1)]
        P.face(q, mat)
        P.face(list(reversed(q)), mat)
    # kolize: strop v hrebeni a sikme kouty u patek (hlava hrace se o klenbu zarazi tam, kde je videt)
    da = a1 - a0
    ca = (a0 + a1) / 2

    def box(s_lo, s_hi, y_lo):
        c = V((s_lo + s_hi) / 2, y_lo + 0.25, ca)
        size = (s_hi - s_lo, 0.5, da) if osa == "z" else (da, 0.5, s_hi - s_lo)
        P.cols.append((M(c), size))
    box(s0, s1, y_patka + vzepeti)
    q = 0.3
    for s_lo, s_hi in ((s0, s0 + q), (s1 - q, s1)):
        box(s_lo, s_hi, y_patka + vzepeti * 0.45)


def build(coll):
    s = zaznam()
    kontrola(s)
    y = s["y"]
    yv = s["y_vrch"]
    t = s["zed_t"]
    kb = s["klenba"]
    P = Part("Sklep", bevel=0.01)
    # --- sklep pod vezi: dlazba, strop z tramu pod podlahou prizemi (zdi veze jdou az do zakladu)
    sx0, sx1 = s["sklep"]["x"]
    sz0, sz1 = s["sklep"]["z"]
    P.bb((sx0, y - 0.25, sz0), (sx1, y, sz1), "dlazba", collide=True)
    ys = s["schody"]["strop_prizemi_y"]
    th = s["sklep"]["tram_vyska"]
    z = sz0 + 0.45
    while z < sz1 - 0.2:
        P.beam((sx0 - 0.1, ys - th / 2, z), (sx1 + 0.1, ys - th / 2, z), 0.2, th, "dub", j=1)
        z += 1.0
    # --- schody dolu (pod ramenem schodu prizemi), zabradli do sklepa
    x0, x1, zh, zd, n, h, _ = schody_geom(s)
    xm = (x0 + x1) / 2
    import fort
    fort.stairs(P, Vector((xm, y, zd)), Vector((0, 0, -1)), zd - zh, -y, x1 - x0, n, "prkna")
    # podesta u paty schodu az ke zdi veze (dlazba je pod ni)
    for k in range(4):                      # zabradli na strane sklepa (spad ze schodu do mistnosti)
        zz = zd - (zd - zh) * k / 3
        P.beam((x1 + 0.04, y + (zd - zz) / (zd - zh) * -y - 0.05, zz), (x1 + 0.04, y + (zd - zz) / (zd - zh) * -y + 1.0, zz), 0.08, 0.08, "dub")
    P.beam((x1 + 0.04, y + 1.0, zd), (x1 + 0.04, 1.0, zh), 0.07, 0.09, "dub", collide=True)
    # --- chodba pruchodem v zakladu veze a pod stajemi; kobky za prickou s dvermi
    cx0, cx1 = s["chodba"]["x"]
    cz0, cz1 = s["chodba"]["z"]
    P.bb((cx0, y - 0.25, cz0), (s["kobky"]["x"][1] + t, y, cz1), "dlazba", collide=True)
    kx0, kx1 = s["kobky"]["x"]
    px0, px1 = s["pricka"]
    dw, dh = s["kobky"]["dvere"]
    zv = s["vez"][3]                         # jizni lic veze: odtud chodba pod stajemi
    holes = [[(a + b) / 2 - dw / 2, (a + b) / 2 + dw / 2, y, y + dh] for a, b in s["kobky"]["z"]]
    wall_z(P, "zdivo", zv, cz1, px0, px1, y - 0.25, yv, holes)
    wall_z(P, "zdivo", zv, cz1 + t, kx1, kx1 + t, y - 0.25, yv)              # vychodni zed kobek (pod celem staje)
    wall_x(P, "zdivo", cx0, kx1 + t, cz1, cz1 + t, y - 0.25, yv)            # celo chodby
    # zdi mezi kobkami (pred prvni az k veži, za posledni k celu)
    hrany = [zv] + [v for ab in s["kobky"]["z"] for v in ab] + [cz1]
    for k in range(0, len(hrany), 2):
        if hrany[k + 1] - hrany[k] > 0.01:
            wall_x(P, "zdivo", px1, kx1, hrany[k], hrany[k + 1], y - 0.25, yv)
    # klenby: chodba (osa z) od lice veze, pruchod zakladem veze rovny strop (zdivo veze), kobky (osa x)
    _klenba(P, "z", zv, cz1, cx0, cx1, y + kb["patka"], kb["vzepeti"])
    P.bb((cx0, y + kb["patka"] + kb["vzepeti"], sz1), (cx1, yv, zv), "zdivo", collide=True)
    for a, b in s["kobky"]["z"]:
        _klenba(P, "x", px1, kx1, a, b, y + kb["patka"], kb["vzepeti"])
        # kruh s retezem v zadni stene kobky
        c = Vector((kx1 - 0.06, y + 1.3, (a + b) / 2))
        for i in range(10):
            t0, t1 = i / 10 * 2 * math.pi, (i + 1) / 10 * 2 * math.pi
            P.rod(c + Vector((0, 0.07 * math.sin(t0), 0.07 * math.cos(t0))), c + Vector((0, 0.07 * math.sin(t1), 0.07 * math.cos(t1))), 0.012, 5, "zelezo")
        kit.chain(P, c - Vector((0, 0.07, 0)), c + Vector((-0.12, -0.95, 0.1)), sag=0.05)
    # dvere kobek: kamenne osteni v pricce, kridlo pohyblive (jmeno Pohyb_sklep_*: lide.gd je nepouziva jako dvere domu)
    for i, (a, b) in enumerate(s["kobky"]["z"]):
        zc = (a + b) / 2
        m = M((px0, y, zc), -90)
        kit.doorway(P, m, "obycejne", dw, dh, px1 - px0, "segment", leaf=False)
        mriz = bool(s["kobky"]["mriz"][i])
        spring = dh - 0.12
        zl = -(px1 - px0) * 0.45
        hm = m @ M((-dw / 2 + 0.01, 0.0, zl))

        def stav(Q, mriz=mriz, spring=spring):
            kit.door_leaf(Q, M((dw / 2 - 0.01, 0.0, 0.0)), dw - 0.02, dh - 0.02, "obycejne", "segment", spring - 0.01, mriz)
        kit.movable("sklep_kobka%d" % (i + 1), "dvere", hm, stav, cols=[((dw / 2, dh / 2, -0.03), (dw - 0.04, dh - 0.04, 0.09))],
                    use=m @ Vector((0.0, 1.2, -(px1 - px0) * 0.5)), group="sklep_kobka%d" % (i + 1), open=88.0, init=0.0, dur=1.1)
    # --- louce se svetlem
    for lx, ly, lz, yaw in s["louce"]:
        p = PR.torch(P, M((lx, y + ly, lz), yaw))
        light(p, 40, (1.0, 0.5, 0.2), 0.05)
    P.commit(coll)
    print("sklep: %d schodu, svetla vyska nad schody %.2f m, %d kobky" % (n, kontrola(s), len(s["kobky"]["z"])))
    lib.INFO.setdefault("sklep", True)
