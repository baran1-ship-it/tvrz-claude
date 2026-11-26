# -*- coding: utf-8 -*-
"""
Krčma do L – Odkaz Havrana (Čechy 1393), varianta C
Hlavní dům: přízemní roubený, trojdílný – šenkovna s hliněnou pecí a výčepem, síň s černou kuchyní (dým odchází dymníkem
v hřebeni), jizba hospodského, komůrka šenkýřky, komora se sudy (poklop do sklepa). Podezdívka z lomového kamene.
Křídlo (samostatná stavba vedle domu): kamenné přízemí se stájí pro 4 koně, roubené patro se 3 pokojíky, společnou nocležnou
a seníkem; vstup po venkovních schodech na pavlač. Mezi domem a křídlem vrata do dvora.
Pevné vybavení: pece, ohniště, výčepní pult, ležení na sudy, lavice podél stěn, postele, žebřík, schody, jesle.
Souřadnice Blender: Z nahoru, ulice = -Y (v Godotu +Z). Spuštění: python krcma_L.py [--norender]
"""
import math, os, sys, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix

SEED = 1393
OUT = os.path.dirname(os.path.abspath(__file__))
FOTO = os.path.join(OUT, "foto"); TEX = os.path.join(OUT, "textury"); os.makedirs(TEX, exist_ok=True)
PRE = os.path.join(OUT, "nahledy_krcma_L"); os.makedirs(PRE, exist_ok=True)
RENDER = "--norender" not in sys.argv
# Misa 16. 11.: pec v senkovne z katalogu hry (Topeni_1400 Pec_Krcma, lokace.json krcma_l pec_senkovna_katalog) - vlastni
# hlinena pec senkovny a jeji kolize se nestavi (nahodna cisla se spotrebuji stejne - ostatni model beze zmeny)
import json as _json
with open(os.path.join(OUT, "..", "..", "pravidla", "svet", "lokace.json"), encoding="utf-8") as _f:
    _KL = _json.load(_f)["krcma_l"]
    PEC_KATALOG = bool(_KL.get("pec_senkovna_katalog", False))
# Misa 16. 11. r. 4 tabulky misa_16_11 (snimky 04, 05: „dum s ubytovnou zarovnat s pruchodem napojenym na hospodu“): kridlo
# (stáj, pavlac, pokoje) posunuto o kridlo_posun_y_m podel Y tak, aby jeho ulicni lic lezel v care vrat pruchodu (Y0) -
# drive kamenne lice SY0 -1,2 o 2,8 m za vraty a domem (lokace.json krcma_l kridlo_posun_y_m)
KDY = float(_KL.get("kridlo_posun_y_m", 0.0))
random.seed(SEED)
W, L, ZE, P_MAIN = 8.0, 15.0, 3.15, math.radians(45)
PFX = "KrcmaL"
exec(open(os.path.join(OUT, "_spolecne.py")).read())
exec(open(os.path.join(OUT, "tesar.py")).read())
exec(open(os.path.join(OUT, "_stavba.py")).read())
SH_W = (0.15, 0.27); EXP = 0.17; LOG_SEG = 1.8

# ================================================================= ROZMĚRY
X0, XS, XJ, X1 = -8.0, -1.0, 2.2, 7.0          # osy stěn: západ, šenkovna|síň, síň|jizba, východ
Y0, Y1 = -4.0, 4.0
ZP, ZF, ZW = 0.40, 0.45, 3.15                   # vršek podezdívky, podlaha, vršek stěn
ZC = 2.90                                       # spodek stropních fošen (strop = podlaha půdy)
def bnd(phase, z0=ZP): return [z0] + [z0 + phase * LOG_H / 2 + k * LOG_H for k in range(0, 40)]
def snap_up(z, ph, z0=ZP): return min(b for b in bnd(ph, z0) if b >= z - 1e-6)
def snap_dn(z, ph, z0=ZP): return max(b for b in bnd(ph, z0) if b <= z + 1e-6)
DT0, DT1 = snap_up(ZF + 1.90, 0), snap_up(ZF + 1.90, 1)          # vršky dveří ve stěnách fáze 0 / 1
WB0, WB1 = snap_dn(ZF + 0.95, 0), snap_dn(ZF + 0.95, 1)
# křídlo
KX0, KX1, KY0, KY1 = 11.95, 18.0, -1.0 + KDY, 11.0 + KDY     # osy roubeného patra (západní stěna ustoupená: pavlač 1,9 m na kameni pod střechou)
KZ = 2.80; KZF = 2.85; KZW = 5.65                # patro: světlá výška pokojů ~2,5 m                # vršek kamene, podlaha patra, vršek stěn patra
KDT = snap_up(KZF + 1.90, 0, KZF)
SX0, SX1, SY0, SY1, ST = 9.80, 18.20, -1.20 + KDY, 11.20 + KDY, 0.60          # kamenné přízemí (vnější líc, tloušťka)

def inside_house(c): return X0 + 0.1 < c.x < X1 - 0.1 and Y0 + 0.1 < c.y < Y1 - 0.1 and c.z < ZW + 4
def WK_INSIDE(c):
    c = Vector(c)
    if XS - 0.15 < c.x < XJ + 0.15 and -0.1 < c.y < Y1 + 0.2 and c.z > ZP: return 2           # černá kuchyně a nad ní
    if inside_house(c):
        if c.z > ZC: return 2 if (XS - 2 < c.x < XJ + 2 and c.y > -1.5) else 1                   # půda: saze od dymníku
        return 1
    if KX0 + 0.1 < c.x < KX1 - 0.1 and KY0 + 0.1 < c.y < KY1 - 0.1: return 1
    return 0
def key_in_house(p):
    p = Vector(p)
    if XS - 0.2 < p.x < XJ + 0.2 and p.y > -0.2: return "tram_c"
    if p.x < XS and p.y > 0.8 and p.z > 2.0: return random.choice(("tram_c", "tram_s"))           # nad pecí
    return random.choice(("tram_in", "tram_in", "tram_s"))

# ================================================================= HLAVNÍ DŮM – STĚNY
print("roubení domu…")
RB = Mesh("KrcmaL_Roubeni_Dum")
EXT = 0.30
# otvory: (u0, u1, z0, z1) podél stěny od p0
FRONT = ((X0, Y0), (X1, Y0)); BACK = ((X0, Y1), (X1, Y1)); WEST = ((X0, Y0), (X0, Y1)); EAST = ((X1, Y0), (X1, Y1))
def U(wall, x_or_y): return x_or_y - (wall[0][0] if wall[0][1] == wall[1][1] else wall[0][1])
W_FRONT = [(U(FRONT, -6.8), U(FRONT, -6.2), WB0, WB0 + 0.5), (U(FRONT, -3.6), U(FRONT, -3.0), WB0, WB0 + 0.5),
           (U(FRONT, 4.3), U(FRONT, 4.85), WB0, WB0 + 0.5)]
D_FRONT = [(U(FRONT, 0.15), U(FRONT, 1.15), ZF - 0.05, DT0)]
W_BACK = [(U(BACK, -5.0), U(BACK, -4.45), WB0, WB0 + 0.5), (U(BACK, 3.05), U(BACK, 3.5), WB0, WB0 + 0.5)]
D_BACK = [(U(BACK, 1.0), U(BACK, 1.95), ZF - 0.05, DT0)]
W_WEST = [(U(WEST, -0.3), U(WEST, 0.25), WB1, WB1 + 0.5)]
W_EAST = [(U(EAST, -2.0), U(EAST, -1.45), WB1, WB1 + 0.5), (U(EAST, 2.2), U(EAST, 2.45), WB1, WB1 + 0.5)]
log_wall(RB, *FRONT, ZP, ZW, 0, holes=W_FRONT + D_FRONT, ext=(EXT, EXT), inward=(0, 1, 0), key_in=key_in_house)
log_wall(RB, *BACK, ZP, ZW, 0, holes=W_BACK + D_BACK, ext=(EXT, EXT), inward=(0, -1, 0), key_in=key_in_house)
log_wall(RB, *WEST, ZP, ZW, 1, holes=W_WEST, ext=(EXT, EXT), inward=(1, 0, 0), key_in=key_in_house)
log_wall(RB, *EAST, ZP, ZW, 1, holes=W_EAST, ext=(EXT, EXT), inward=(-1, 0, 0), key_in=key_in_house)
# příčky (s průchozími zhlavími na fasádě)
PS = ((XS, Y0), (XS, Y1)); PJ = ((XJ, Y0), (XJ, Y1)); PK = ((XS, 0.0), (XJ, 0.0)); PB = ((XJ, 0.5), (X1, 0.5)); PZ = ((4.4, 0.5), (4.4, Y1))
D_PS = [(U(PS, -2.6), U(PS, -1.6), ZF - 0.05, DT1)]
D_PJ = [(U(PJ, -2.3), U(PJ, -1.4), ZF - 0.05, DT1), (U(PJ, 1.55), U(PJ, 2.35), ZF - 0.05, DT1)]
D_PK = [(0.3, 2.0, ZF - 0.05, DT0)]                                         # široký průchod síň → černá kuchyně
D_PB = [(U(((XJ, 0.5), (X1, 0.5)), 5.2), U(((XJ, 0.5), (X1, 0.5)), 6.0), ZF - 0.05, DT0)]
D_PZ = []
log_wall(RB, *PS, ZP, ZW, 1, holes=D_PS, ext=(EXT + 0.02, EXT + 0.02), inward=(1, 0, 0), key_in=key_in_house)
log_wall(RB, *PJ, ZP, ZW, 1, holes=D_PJ, ext=(EXT + 0.02, EXT + 0.02), inward=(-1, 0, 0), key_in=key_in_house)
log_wall(RB, *PK, ZP, ZC - 0.02, 0, holes=D_PK, ext=(0, 0), inward=(0, 1, 0), key_in=key_in_house)
log_wall(RB, *PB, ZP, ZW, 0, holes=D_PB, ext=(0, EXT + 0.02), inward=(0, 1, 0), key_in=key_in_house)
log_wall(RB, *PZ, ZP, ZC - 0.02, 1, holes=D_PZ, ext=(0, EXT + 0.02), inward=(1, 0, 0), key_in=key_in_house)
for (wall, ws, ds, ph) in ((FRONT, W_FRONT, D_FRONT, 0), (BACK, W_BACK, D_BACK, 0), (WEST, W_WEST, [], 1), (EAST, W_EAST, [], 1)):
    sign = {FRONT: -1, BACK: 1, WEST: 1, EAST: -1}[wall]
    for (u0, u1, zb, zt) in ws: window(RB, *wall, u0, u1, zb, zt, out_sign=sign)
    for (u0, u1, zb, zt) in ds: opening_frame(RB, *wall, u0, u1, zb, zt, "dvere")
for (wall, ds) in ((PS, D_PS), (PJ, D_PJ), (PB, D_PB)):
    for (u0, u1, zb, zt) in ds: opening_frame(RB, *wall, u0, u1, zb, zt, "dvere")
# podlahy, strop (nad černou kuchyní otevřeno do krovu, poklop/otvor pro žebřík)
plank_floor(RB, X0 + 0.11, XS - 0.11, Y0 + 0.11, Y1 - 0.11, ZF, "x")                   # šenkovna
plank_floor(RB, XJ + 0.11, X1 - 0.11, Y0 + 0.11, 0.5 - 0.11, ZF, "x")                  # jizba
plank_floor(RB, XJ + 0.11, 4.4 - 0.11, 0.5 + 0.11, Y1 - 0.11, ZF, "y")                  # šenkýřka
dirt_floor(RB, XS + 0.11, XJ - 0.11, Y0 + 0.11, Y1 - 0.11, ZF - 0.03, "hlina_c")       # síň, kuchyně
dirt_floor(RB, 4.4 + 0.11, X1 - 0.11, 0.5 + 0.11, Y1 - 0.11, ZF - 0.03, "hlina")       # komora
dirt_floor(RB, X0 - 0.2, X1 + 0.2, Y0 - 0.2, Y1 + 0.2, ZF - 0.08, "hlina")             # pod vším (žádné díry)
ceiling(RB, X0 + 0.11, XS - 0.11, Y0 + 0.11, Y1 - 0.11, ZC, "y", key_beam="tram_s")
ceiling(RB, XS + 0.11, XJ - 0.11, Y0 + 0.11, -0.11, ZC, "x", key_beam="tram_c", key_board="povala_c")
ceiling(RB, XJ + 0.11, X1 - 0.11, Y0 + 0.11, Y1 - 0.11, ZC, "y", key_beam="tram_in")
# ================================================================= HLAVNÍ DŮM – KROV A STŘECHA
print("krov domu…")
KS = Mesh("KrcmaL_Krov_Dum"); SH = Mesh("KrcmaL_Strecha_Dum")
RD = Roof(((X0 + X1) / 2, 0, 0), (1, 0, 0), X0 - (X0 + X1) / 2 - 0.13, X1 - (X0 + X1) / 2 + 0.13, (Y1 - Y0) / 2 + 0.13, ZW, pitch=45, over=0.65, gover=0.40)
DYM_A = 0.6 - (X0 + X1) / 2
rx = list(np.arange(RD.a0 + 0.05, RD.a1, 0.95))
skip_d = lambda sg, a, d: abs(a - DYM_A) < 0.62 and d > RD.dmax - 0.62
RD.build(KS, SH, rx, collar_z=5.6, skip=skip_d, dymnik_a=DYM_A, key_r="tram_s", laths_inside_key="tram_s")
# ================================================================= HLAVNÍ DŮM – VYBAVENÍ (pevné)
print("vybavení domu…")
IN = Mesh("KrcmaL_Interier_Dum")
clay_oven(Mesh("KrcmaL_Pec_Zahozena") if PEC_KATALOG else IN, -2.75, XS - 0.12, 1.25, Y1 - 0.12, ZF, base_h=0.55, top_h=1.65)  # pec v šenkovně (topí se z kuchyně)
# černá kuchyně: ohniště na hliněném stupni u stěny pece, žebřík na půdu
box(IN, (-0.15, 3.05, ZF + 0.25), (1.5, 1.6, 0.5), Matrix.Identity(3), "pec_c", uvs=1.0)
F(IN, [(-0.75, 2.45, ZF + 0.505), (0.45, 2.45, ZF + 0.505), (0.45, 3.70, ZF + 0.505), (-0.75, 3.70, ZF + 0.505)], [(0, 0), (1, 0), (1, 1), (0, 1)], "popel", (0, 0, 1))
for k in range(30):
    x = random.uniform(-0.5, 0.2); y = random.uniform(2.7, 3.4); s_ = random.uniform(0.03, 0.06)
    stone(IN, (x, y, ZF + 0.52), (1, 0, 0), (0, 1, 0), (0, 0, 1), s_, s_ * 0.8, s_ * 0.6, "uhli", detail=False, bulge=0.005, tilt=0.8)
for (x, y) in ((-0.55, 2.75), (0.25, 2.75), (-0.15, 3.55)):
    stone(IN, (x, y, ZF + 0.6), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.18, 0.15, 0.12, "kamen_c", tilt=0.3)
ladder(IN, (1.55, 1.2, ZF), (1.55, -0.25, ZC + 0.45), w=0.46, key="tram_c")
# jizba hospodského: malá pec, postel, lavice; komůrka šenkýřky: postel; komora: ležení na sudy, poklop
clay_oven(IN, XJ + 0.12, 3.55, -0.95, 0.5 - 0.12, ZF, base_h=0.45, top_h=1.35)
for k in range(5): board(IN, (5.4 + (k - 2) * 0.17, 2.6, ZF + 0.015), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.16, 0.85, 0.03, "dvere", tilt=0.005)
cone(IN, (5.4, 2.25, ZF + 0.03), (5.4, 2.25, ZF + 0.05), 0.05, 0.05, "zelezo", seg=8)
roubeni = RB.build(smooth_angle=35, merge=False); krov = KS.build(smooth_angle=35, merge=False); strecha = SH.build(smooth_angle=20, merge=False)
interier = IN.build(smooth_angle=40, merge=False)
# dveře domu
door_leaf("KrcmaL_Dvere_Vchod", *FRONT, *D_FRONT[0], out_sign=-1, hinge_side=0, opens_in=True)
door_leaf("KrcmaL_Dvere_Dvur", *BACK, *D_BACK[0], out_sign=1, hinge_side=1, opens_in=True)
door_leaf("KrcmaL_Dvere_Senkovna", *PS, *D_PS[0], out_sign=1, hinge_side=0, opens_in=False)
door_leaf("KrcmaL_Dvere_Jizba", *PJ, *D_PJ[0], out_sign=-1, hinge_side=0, opens_in=False)
door_leaf("KrcmaL_Dvere_Senkyrka", *PJ, *D_PJ[1], out_sign=-1, hinge_side=1, opens_in=False)
door_leaf("KrcmaL_Dvere_Komora", *PB, *D_PB[0], out_sign=-1, hinge_side=0, opens_in=False)
# podezdívka (lomový kámen ze skenu)
print("podezdívka…")
pz = solid_box((X0 - 0.17, Y0 - 0.17, 0.0), (X1 + 0.17, Y0 + 0.17, ZP))
csg(pz, [solid_box((X0 - 0.17, Y1 - 0.17, 0.0), (X1 + 0.17, Y1 + 0.17, ZP)), solid_box((X0 - 0.17, Y0, 0.0), (X0 + 0.17, Y1, ZP)),
         solid_box((X1 - 0.17, Y0, 0.0), (X1 + 0.17, Y1, ZP))], 'UNION')
def soot_ext(p, n, h, bed=False):
    nz = nzf(p, 1.0, 4); nz2 = nzf(p, 3.0, 2); g = 0.82 + 0.12 * nz
    mm = max(0.0, 1.0 - p.z / (0.35 + 0.3 * nz)) * (0.6 + 0.4 * nz2) if n.z < 0.6 else 0.0
    g *= 0.6 + 0.4 * h
    return (g * (1 - 0.35 * mm), g * (1 - 0.12 * mm) * 0.98, g * (1 - 0.45 * mm) * 0.95)
podezdivka = masonry(pz, "KrcmaL_Podezdivka", 2.5, 0.07, lambda p, n: False, soot_ext, 0.14, voxel=0.045,
                     drop=lambda c, n: (n.z < -0.9 and c.z < 0.02), flat_top=lambda p, n: 0.25 if n.z > 0.7 else 1.0)

# ================================================================= KŘÍDLO: KAMENNÉ PŘÍZEMÍ (STÁJ)
print("křídlo – kámen…")
kz = solid_box((SX0, SY0, 0.0), (SX1, SY1, KZ))
STAJ_D = [(1.6 + KDY, 4.0 + KDY)]                            # dvoukřídlá vrata stáje na západ do dvora (y), 2,4 × 2,5 m
VZ_T = 2.50
csg(kz, [solid_box((SX0 + ST, SY0 + ST, -0.1), (SX1 - ST, SY1 - ST, KZ + 0.1))] +
    [solid_box((SX0 - 0.2, y0, -0.1), (SX0 + ST + 0.2, y1, VZ_T)) for (y0, y1) in STAJ_D] +
    [solid_box((SX1 - ST - 0.2, y - 0.13, 1.35), (SX1 + 0.2, y + 0.13, 1.85)) for y in (0.5 + KDY, 3.5 + KDY, 6.5 + KDY, 9.5 + KDY)] +
    [solid_box((x - 0.13, SY1 - ST - 0.2, 1.35), (x + 0.13, SY1 + 0.2, 1.85)) for x in (12.5, 15.0, 17.0)], 'DIFFERENCE')
def soot_kridlo(p, n, h, bed=False):
    inside = SX0 + ST - 0.05 < p.x < SX1 - ST + 0.05 and SY0 + ST - 0.05 < p.y < SY1 - ST + 0.05
    nz = nzf(p, 1.0, 4); nz2 = nzf(p, 3.0, 2)
    if inside:
        g = (0.55 + 0.15 * nz) * (0.6 + 0.4 * h); dirt = max(0.0, 1 - p.z / 0.9)
        return (g * (1 - 0.25 * dirt), g * (1 - 0.3 * dirt) * 0.97, g * (1 - 0.4 * dirt) * 0.92)
    return soot_ext(p, n, h)
kridlo_kamen = masonry(kz, "KrcmaL_Kridlo_Kamen", 2.5, 0.08, lambda p, n: False, soot_kridlo, 0.28, voxel=0.045,
                       drop=lambda c, n: (n.z < -0.9 and c.z < 0.02), flat_top=lambda p, n: 0.25 if (n.z > 0.7 and c_top(p)) else 1.0) if False else None
def _flat(p, n): return 0.25 if (n.z > 0.7 and p.z > KZ - 0.1) else 1.0
kridlo_kamen = masonry(kz, "KrcmaL_Kridlo_Kamen", 2.5, 0.08, lambda p, n: False, soot_kridlo, 0.11, voxel=0.05,
                       drop=lambda c, n: (n.z < -0.9 and c.z < 0.02), flat_top=_flat)
# ================================================================= KŘÍDLO: ROUBENÉ PATRO, PAVLAČ, SCHODY, KROV
print("křídlo – patro…")
KR = Mesh("KrcmaL_Roubeni_Kridlo")
KW = ((KX0, KY0), (KX0, KY1)); KE = ((KX1, KY0), (KX1, KY1)); KSo = ((KX0, KY0), (KX1, KY0)); KN = ((KX0, KY1), (KX1, KY1))
ROOMS_Y = [KY0, 3.0 + KDY, 7.0 + KDY, KY1]                    # pokoj 1, pokoj 2, nocležna – každá 4 × 6 m
KD = [(ROOMS_Y[0] + 0.5 - KY0, ROOMS_Y[0] + 1.4 - KY0, KZF - 0.03, KDT), (ROOMS_Y[1] + 0.5 - KY0, ROOMS_Y[1] + 1.4 - KY0, KZF - 0.03, KDT),
      (ROOMS_Y[2] + 0.4 - KY0, ROOMS_Y[2] + 1.3 - KY0, KZF - 0.03, KDT)]
KWB = snap_dn(KZF + 1.0, 1, KZF)
KWI = [(a + KDY - KY0, a + KDY + 0.5 - KY0, KWB, KWB + 0.5) for a in (1.9, 5.9, 9.9)]          # okénka na pavlač
KEW = [(a + KDY - KY0, a + KDY + 0.55 - KY0, KWB, KWB + 0.5) for a in (0.7, 4.7, 8.7)]    # okna na východ
KNW = [(14.7 - KX0, 15.25 - KX0, snap_dn(KZF + 1.0, 0, KZF), snap_dn(KZF + 1.0, 0, KZF) + 0.5)]
log_wall(KR, *KW, KZF - 0.04, KZW, 1, holes=KD + KWI, ext=(EXT, EXT), inward=(1, 0, 0))
log_wall(KR, *KE, KZF - 0.04, KZW, 1, holes=KEW, ext=(EXT, EXT), inward=(-1, 0, 0))
log_wall(KR, *KSo, KZF - 0.04, KZW, 0, ext=(EXT, EXT), inward=(0, 1, 0))
log_wall(KR, *KN, KZF - 0.04, KZW, 0, holes=KNW, ext=(EXT, EXT), inward=(0, -1, 0))
for (u0, u1, zb, zt) in KD: opening_frame(KR, *KW, u0, u1, zb, zt, "dvere")
for (u0, u1, zb, zt) in KWI: window(KR, *KW, u0, u1, zb, zt, out_sign=1)
for (u0, u1, zb, zt) in KEW: window(KR, *KE, u0, u1, zb, zt, out_sign=1)
for (u0, u1, zb, zt) in KNW: window(KR, *KN, u0, u1, zb, zt, out_sign=1)
for y in ROOMS_Y[1:-1]:                                                   # příčky mezi pokoji (celá hloubka)
    log_wall(KR, (KX0, y), (KX1, y), KZF - 0.04, KZW, 0, ext=(EXT + 0.02, EXT + 0.02), inward=(0, 1, 0))
plank_floor(KR, SX0 - 0.02, SX1 + 0.02, SY0 - 0.02, SY1 + 0.02, KZF, "y")
F(KR, [(SX0, SY0, KZF - 0.052), (SX1, SY0, KZF - 0.052), (SX1, SY1, KZF - 0.052), (SX0, SY1, KZF - 0.052)], [(0, 0), (8, 0), (8, 12), (0, 12)], "podbiti", (0, 0, -1))   # záklop pod fošnami (žádné světelné škvíry)          # podlaha patra i pavlače (fošny přes kámen)
for x in np.arange(SX0 + ST + 0.3, SX1 - ST, 0.9):                        # stropnice stáje
    T(KR, (x, SY0 + 0.25, KZ - 0.11), (x, SY1 - 0.25, KZ - 0.11), 0.18, 0.20, key="tram_d", wane=0.5)
ceiling(KR, KX0, KX1, KY0, KY1, KZW - 0.05, "x", key_beam="tram_in", top_board=True)
# pavlač: na kamenné zdi stáje pod přetaženou střechou; sloupy, pásky, vaznice, zábradlí s mezerou pro schody
PX_ = SX0 + 0.14                                   # osa sloupů pavlače (na kameni)
PVX0, PVX1, PVY0, PVY1 = SX0 - 1.2, KX0 - 0.12, SY0, SY1          # PVX0 zůstává kvůli plotu (mezera za křídlem)
ST_Y0, ST_Y1 = 7.15 + KDY, 8.15 + KDY                          # průchod v zábradlí na schody
POST_Y = [SY0 + 0.12, 2.0 + KDY, 4.4 + KDY, 6.9 + KDY, 8.4 + KDY, SY1 - 0.12]
for y in POST_Y:
    T(KR, (PX_, y, KZF), (PX_, y, KZW + 0.02), 0.18, 0.18, up=(1, 0, 0), wane=0.5)
    T(KR, (PX_, y, KZW + 0.11), (KX0 + 0.2, y, KZW + 0.11), 0.16, 0.18, key="tram", wane=0.4)              # trámek k roubení
    for sg in (-1, 1):
        if SY0 + 0.4 < y + sg * 0.7 < SY1 - 0.4:
            T(KR, (PX_, y, KZW - 0.75), (PX_, y + sg * 0.7, KZW - 0.02), 0.11, 0.12, key="tram", wane=0.4)
T(KR, (PX_, SY0 - 0.3, KZW + 0.11), (PX_, SY1 + 0.3, KZW + 0.11), 0.20, 0.22, key="tram", wane=0.4)             # vaznice pod krokvemi
for (ya, yb) in splitr(SY0 + 0.05, SY1 - 0.05, [(ST_Y0, ST_Y1)]):
    pole(KR, (PX_ - 0.02, ya, KZF + 1.0), (PX_ - 0.02, yb, KZF + 1.0), 0.04, key="tram", bend=0.02)
    pole(KR, (PX_ - 0.02, ya, KZF + 0.5), (PX_ - 0.02, yb, KZF + 0.5), 0.03, key="tram", bend=0.02)
    for y in np.arange(ya + 0.2, yb - 0.1, 0.45):
        T(KR, (PX_ - 0.02, y, KZF), (PX_ - 0.02, y, KZF + 0.98), 0.05, 0.05, key="tram", up=(1, 0, 0), wane=0.3)
# venkovní schody podél západní zdi stáje (od severu nahoru k jihu), na pavlač vstup z boku
STX = SX0 - 0.50
# schody konci na severnim kraji podesty (Misa 15. 11. „spatne zabradli nahoru“: drive vybihaly az na jizni kraj podesty,
# posledni metr schodu pod podestou = schod 0,5 m) a zabradli maji na volne strane, ne u zdi stane
STA, STB = Vector((STX, 12.05 + KDY, 0.0)), Vector((STX, ST_Y1, KZF))
stairs(KR, STA, STB, 0.85, rail=True, key="tram", rail_side=-1)
def zabradli(Ms, p0, p1, z0):
    """rovne zabradli jako pavlac: madlo 1,0 m, prostredni zerd 0,5 m, svislice po 0,45 m, sloupky na koncich"""
    a = Vector((p0[0], p0[1], z0)); b = Vector((p1[0], p1[1], z0)); d = b - a; Ln = d.length
    pole(Ms, a + Vector((0, 0, 1.0)), b + Vector((0, 0, 1.0)), 0.04, key="tram", bend=0.02)
    pole(Ms, a + Vector((0, 0, 0.5)), b + Vector((0, 0, 0.5)), 0.03, key="tram", bend=0.02)
    for t_ in (0.0, 1.0):
        q = a.lerp(b, t_)
        T(Ms, q, q + Vector((0, 0, 1.02)), 0.08, 0.08, key="tram", up=(1, 0, 0), wane=0.3)
    for u in np.arange(0.3, Ln - 0.2, 0.45):
        q = a + d.normalized() * u
        T(Ms, q, q + Vector((0, 0, 0.98)), 0.05, 0.05, key="tram", up=(1, 0, 0), wane=0.3)
ZAB = []                                           # [p0, p1] zabradli navic - i kolize
# podesta: vnejsi kraj a jizni konec (sever = prichod ze schodu, vychod = mezera v zabradli pavlace)
ZAB += [((SX0 - 0.93, ST_Y0 + 0.03), (SX0 - 0.93, ST_Y1)), ((SX0 - 0.93, ST_Y0 + 0.03), (SX0 - 0.02, ST_Y0 + 0.03))]
# konce pavlace mezi sloupem a roubenim (Misa 15. 11. „na koncich ochozu chybi zabradli“)
ZAB += [((PX_, SY0 + 0.06), (KX0 - LOG_T / 2, SY0 + 0.06)), ((PX_, SY1 - 0.06), (KX0 - LOG_T / 2, SY1 - 0.06))]
for (za, zb) in ZAB[:2]:
    zabradli(KR, za, zb, KZF - 0.03)
for (za, zb) in ZAB[2:]:
    zabradli(KR, za, zb, KZF)
board(KR, (SX0 - 0.48, (ST_Y0 + ST_Y1) / 2, KZF - 0.03), (0, 1, 0), (1, 0, 0), (0, 0, 1), ST_Y1 - ST_Y0, 0.96, 0.05, "prkna")      # podesta u zdi
for y in (ST_Y0, ST_Y1):
    T(KR, (SX0 - 0.9, y, -0.1), (SX0 - 0.9, y, KZF - 0.05), 0.14, 0.14, key="tram", up=(1, 0, 0), wane=0.5)
# krov křídla (hřeben podél Y): přes roubení i pavlač
KRS = Mesh("KrcmaL_Strecha_Kridlo")
RCX = (PX_ + KX1) / 2
RK = Roof((RCX, (KY0 + KY1) / 2, 0), (0, 1, 0), SY0 - (KY0 + KY1) / 2 - 0.13, SY1 - (KY0 + KY1) / 2 + 0.13, (KX1 - PX_) / 2 + 0.13, KZW,
          pitch=40, over=0.65, gover=0.45)
RK.build(KR, KRS, list(np.arange(RK.a0 + 0.05, RK.a1, 0.95)), collar_z=KZW + 2.4, key_r="tram_in", laths_inside_key="tram_in")
# stáj: jesle, přepážky stání, sláma; pokoje: postele, lavice; nocležna: slamníky
IK = Mesh("KrcmaL_Interier_Kridlo")
dirt_floor(IK, SX0 + ST, SX1 - ST, SY0 + ST, SY1 - ST, 0.03, "hlina_c")
BEDS = [(KX1 - 1.15, ROOMS_Y[0] + 0.62, math.pi), (KX1 - 1.15, ROOMS_Y[1] - 0.62, math.pi),          # pokoj 1: dvě postele
        (KX1 - 1.15, ROOMS_Y[1] + 0.62, math.pi)]                                                    # pokoj 2: postel
roub_k = KR.build(smooth_angle=35, merge=False); strecha_k = KRS.build(smooth_angle=20, merge=False); int_k = IK.build(smooth_angle=40, merge=False)
for i in range(2): door_leaf("KrcmaL_Dvere_Pokoj%d" % (i + 1), *KW, *KD[i], out_sign=1, hinge_side=0, opens_in=False)
door_leaf("KrcmaL_Dvere_Noclezna", *KW, *KD[2], out_sign=1, hinge_side=0, opens_in=False)
(gy0, gy1) = STAJ_D[0]; gm = (gy0 + gy1) / 2
door_leaf("KrcmaL_Vrata_Staj_L", (SX0 + ST / 2, SY0), (SX0 + ST / 2, SY1), gy0 - SY0 + 0.02, gm - SY0 - 0.005, 0.02, VZ_T - 0.03, out_sign=1, hinge_side=0, opens_in=False, t=ST)
door_leaf("KrcmaL_Vrata_Staj_P", (SX0 + ST / 2, SY0), (SX0 + ST / 2, SY1), gm - SY0 + 0.005, gy1 - SY0 - 0.02, 0.02, VZ_T - 0.03, out_sign=1, hinge_side=1, opens_in=False, t=ST)
for y_ in (gy0 - 0.06, gy1 + 0.06):                                        # dubové veřeje vrat v kameni
    T(KR, (SX0 + 0.1, y_, 0.0), (SX0 + 0.1, y_, VZ_T + 0.05), 0.16, 0.14, key="tram_d", up=(1, 0, 0), wane=0.3)
T(KR, (SX0 + 0.1, gy0 - 0.25, VZ_T + 0.1), (SX0 + 0.1, gy1 + 0.25, VZ_T + 0.1), 0.18, 0.18, key="tram_d", wane=0.3)

# ================================================================= DVŮR: VRATA, PLOT, KŮLNA, VÍCH, LAVICE
print("dvůr…")
DV = Mesh("KrcmaL_Dvur")
def palisade(p0, p1, h=1.6):
    a = Vector((p0[0], p0[1], 0)); b = Vector((p1[0], p1[1], 0)); Ln = (b - a).length; n = max(2, int(Ln / 0.15))
    for k in range(n):
        p = a.lerp(b, (k + 0.5) / n); hh = h + random.uniform(-0.15, 0.08)
        pole(DV, p - Vector((0, 0, 0.1)), p + Vector((0, 0, hh)), random.uniform(0.055, 0.075), key=random.choice(("tram", "tram_g", "tram_d")), bend=0.02, seg=5, seglen=0.9, bark=0.45, caps=(False, True))
    for zz in (0.45, h - 0.35):
        pole(DV, a + Vector((0, 0, zz)) + Vector((0, 0, 0)), b + Vector((0, 0, zz)), 0.04, key="tram_d", bend=0.02, seg=6)
YARD_Y1 = 12.8
# Misa 15. 11. „pozemek me nepustil na schody k pokojum“: pata schodu (x 8,85…9,75) a zabradli (x 8,78) zaplnily mezeru
# v zadnim plotu (x 8,4…9,8) - od konce plotu k zabradli 0,52 m < hrac 0,56 m. Plot konci o PRUCHOD_M driv nez zabradli.
PRUCHOD_M = 1.2
PLOT_S1_X1 = STA.x - (0.85 / 2 + 0.05) - 0.05 - PRUCHOD_M     # vnejsi lic kolize zabradli schodu (KrcmaL_Kol_ZabrSchodu) - 1,2 m
palisade((X0 - 0.2, Y1 + 0.2), (X0 - 0.2, YARD_Y1)); palisade((X0 - 0.2, YARD_Y1), (PLOT_S1_X1, YARD_Y1))
palisade((PVX0 + 1.2, YARD_Y1), (SX1, YARD_Y1)); palisade((SX1, YARD_Y1), (SX1, SY1 + 0.05))
GX0, GX1 = X1 + 0.35, SX0 - 0.05                 # vrata z ulice do dvora mezi domem a křídlem
for x in (GX0 - 0.1, GX1 + 0.1):
    T(DV, (x, Y0, -0.2), (x, Y0, 2.9), 0.24, 0.24, key="tram", up=(1, 0, 0), wane=0.5)
T(DV, (GX0 - 0.35, Y0, 2.95), (GX1 + 0.35, Y0, 2.95), 0.22, 0.24, key="tram", wane=0.5)
sub = Roof(((GX0 + GX1) / 2, Y0, 0), (1, 0, 0), -(GX1 - GX0) / 2 - 0.3, (GX1 - GX0) / 2 + 0.3, 0.35, 3.06, pitch=40, over=0.25, gover=0.15, r=0.05)
for sg in (-1, 1):
    shingles(DV, sub.Q(sg, 0, 0) + sub.N(sg) * 0.02, sub.A, sub.S(sg), sub.N(sg), sub.a0 - 0.12, sub.a1 + 0.12, sub.dmax + 0.02, lambda am, s0, s1: False, lambda am, s0: random.choice(("sindel", "sindel_m1")))
    pole(DV, sub.Q(sg, sub.a0 - 0.1, 0) - sub.N(sg) * 0.05, sub.Q(sg, sub.a0 - 0.1, sub.dmax) - sub.N(sg) * 0.05, 0.05, key="tram", bend=0.01)
    pole(DV, sub.Q(sg, sub.a1 + 0.1, 0) - sub.N(sg) * 0.05, sub.Q(sg, sub.a1 + 0.1, sub.dmax) - sub.N(sg) * 0.05, 0.05, key="tram", bend=0.01)
# kůlna v rohu dvora
for (x, y) in ((-7.4, 10.2), (-3.4, 10.2)):
    T(DV, (x, y, -0.1), (x, y, 2.3), 0.16, 0.16, key="tram", up=(1, 0, 0), wane=0.5)
T(DV, (-7.7, 10.2, 2.35), (-3.1, 10.2, 2.35), 0.16, 0.18, key="tram", wane=0.5)
lean = Roof((-5.4, 11.5, 0), (1, 0, 0), -2.3, 2.3, 1.3, 2.45, pitch=20, over=0.35, gover=0.2, r=0.05)
for x in (-7.5, -6.5, -5.5, -4.5, -3.5):
    pole(DV, (x, YARD_Y1 - 0.15, 2.85), (x, 10.0, 2.32), 0.06, key="tram", bend=0.02)
Sdl = Vector((0, 1, 0.364)).normalized(); Ndl = Vector((0, -0.364, 1)).normalized()
shingles(DV, Vector((0, 9.8, 2.30)) + Ndl * 0.08, (1, 0, 0), Sdl, Ndl, -7.85, -2.95, (YARD_Y1 - 9.8) / math.cos(math.radians(20)) + 0.1, lambda am, s0, s1: False, lambda am, s0: random.choice(("sindel_t", "sindel_m", "sindel_m1", "sindel_m")))
for x in (-7.4, -5.4, -3.4):                                                   # zadní sloupy a stěna kůlny (u plotu)
    T(DV, (x, YARD_Y1 - 0.3, -0.1), (x, YARD_Y1 - 0.3, 2.95), 0.16, 0.16, key="tram", up=(1, 0, 0), wane=0.5)
T(DV, (-7.7, YARD_Y1 - 0.3, 2.95), (-3.1, YARD_Y1 - 0.3, 2.95), 0.16, 0.18, key="tram", wane=0.5)
clad(DV, (0, YARD_Y1 - 0.2, 0), (1, 0, 0), (0, 1, 0), -7.7, -3.1, 0.0, lambda u: 2.9, battens=False)
for x in (-7.4, -3.4): clad(DV, (x + (-0.12 if x < -5 else 0.12), 0, 0), (0, 1, 0), (-1 if x < -5 else 1, 0, 0), 10.3, YARD_Y1 - 0.3, 0.0, lambda u: 2.30 + (u - 10.2) * 0.364 - 0.05, battens=False)
# štít krčmy (Míša 17. 11. ř. 4: věchet „bochník“ pryč, pěkná cedule) – kovaná konzola ze zdi, dubová deska na dvou
# řetízcích kolmo ke stěně (čitelná z cesty podél průčelí), na obou stranách vypálený džbán. Hotový model nenalezen
# (Disk, Poly Haven, Quaternius/Kenney, CC0 weby 17. 11.) – postaveno z materiálů krčmy.
# Misa 26. 11. (0.9999996 snimek u x 462 z 818: „cedule u hospody patri na roh budovy ne do dveri“): cedule byla nad
# hlavnimi dvermi (x 0,15-1,15) - ted u zapadniho rohu pruceli (roh X0, zhlaví kuláčů EXT), prvni videt od vsi
CX, CY, CZ = X0 + 0.45, Y0, 2.85
I3 = Matrix.Identity(3)
box(DV, (CX, CY - 0.025, CZ - 0.2), (0.07, 0.03, 0.5), I3, "zelezo")                       # nástěnná deska konzoly
cone(DV, (CX, CY - 0.02, CZ), (CX, CY - 1.08, CZ), 0.016, 0.014, "zelezo", seg=6)           # rameno
cone(DV, (CX, CY - 0.02, CZ - 0.4), (CX, CY - 0.62, CZ), 0.012, 0.012, "zelezo", seg=6)      # vzpěra
cone(DV, (CX, CY - 1.08, CZ), (CX, CY - 1.1, CZ + 0.06), 0.014, 0.01, "zelezo", seg=6)       # zahnutý konec
for yy in (CY - 0.37, CY - 0.93):                                                            # řetízky
    cone(DV, (CX, yy, CZ - 0.01), (CX, yy, CZ - 0.25), 0.006, 0.006, "zelezo", seg=4)
SY, SZ = CY - 0.65, CZ - 0.52                                                                # střed desky
box(DV, (CX, SY, SZ), (0.045, 0.74, 0.54), I3, "dub")
box(DV, (CX, SY, SZ + 0.29), (0.06, 0.78, 0.05), I3, "dub")                                  # horní lišta
for sx in (-1, 1):                                                                           # džbán na obou stranách
    x = CX + sx * 0.025
    box(DV, (x, SY + 0.02, SZ - 0.02), (0.006, 0.17, 0.22), I3, "malta_c")                   # tělo
    box(DV, (x, SY + 0.02, SZ + 0.115), (0.006, 0.21, 0.035), I3, "malta_c")                 # víčko
    box(DV, (x, SY + 0.02, SZ - 0.145), (0.006, 0.21, 0.03), I3, "malta_c")                  # pata
    box(DV, (x, SY - 0.1, SZ + 0.04), (0.006, 0.07, 0.025), I3, "malta_c")                   # ucho nahoře
    box(DV, (x, SY - 0.1, SZ - 0.07), (0.006, 0.07, 0.025), I3, "malta_c")                   # ucho dole
    box(DV, (x, SY - 0.125, SZ - 0.015), (0.006, 0.025, 0.12), I3, "malta_c")                # ucho svisle
    for dy in (-0.27, 0.29):                                                                 # rámeček – rohové čárky
        box(DV, (x, SY + dy, SZ), (0.006, 0.02, 0.42), I3, "malta_c")
dvur = DV.build(smooth_angle=35, merge=False)
for (nm, hs, sg) in (("KrcmaL_Vrata_L", 0, 1), ("KrcmaL_Vrata_P", 1, -1)):
    half = (GX1 - GX0) / 2
    door_leaf(nm, (GX0, Y0), (GX1, Y0), 0.0 if hs == 0 else half, half if hs == 0 else GX1 - GX0, 0.05, 2.45, out_sign=-1, hinge_side=hs, opens_in=True, t=0.24)

# ================================================================= KOLIZE
print("kolize…")
DH = lambda ds: [(d[0], d[1], d[2], d[3]) for d in ds]
for (nm, wl, ds) in (("Pred", FRONT, D_FRONT), ("Zad", BACK, D_BACK), ("Zapad", WEST, []), ("Vychod", EAST, []), ("PricS", PS, D_PS), ("PricJ", PJ, D_PJ),
                     ("PricK", PK, D_PK), ("PricB", PB, D_PB), ("PricZ", PZ, [])):
    wall_cols(nm, *wl, 0.0, ZW, LOG_T, DH(ds))
colbox("PodlahaDum", (X0, Y0, ZF - 0.3), (X1, Y1, ZF - 0.02))
None if PEC_KATALOG else colbox("Pec", (-2.75, 1.15, ZF), (XS - 0.1, Y1 - 0.1, ZF + 1.6)); colbox("PecJizba", (XJ, -0.95, ZF), (3.55, 0.4, ZF + 1.3))
colbox("Strop", (X0, Y0, ZC), (X1, Y1, ZC + 0.06))
# křídlo
for (nm, lo, hi) in (("StajJ", (SX0, SY0, 0), (SX1, SY0 + ST, KZ)), ("StajS", (SX0, SY1 - ST, 0), (SX1, SY1, KZ)), ("StajV", (SX1 - ST, SY0, 0), (SX1, SY1, KZ))):
    colbox(nm, lo, hi)
for (ya, yb) in splitr(SY0, SY1, STAJ_D): colbox("StajZ%d" % len(KOL), (SX0, ya, 0), (SX0 + ST, yb, KZ))
for (y0, y1) in STAJ_D: colbox("StajZN%d" % len(KOL), (SX0, y0, VZ_T), (SX0 + ST, y1, KZ))
colbox("PodlahaPatro", (SX0, SY0, KZ), (SX1, SY1, KZF))
for (nm, wl, ds) in (("KZ", KW, KD), ("KV", KE, []), ("KJ", KSo, []), ("KS", KN, [])): wall_cols(nm, *wl, KZF, KZW, LOG_T, DH(ds))
for y in ROOMS_Y[1:-1]: colbox("KPric%d" % len(KOL), (KX0, y - 0.11, KZF), (KX1, y + 0.11, KZW))
for (ya, yb) in splitr(SY0, SY1, [(ST_Y0, ST_Y1)]): colbox("PavlacZabr%d" % len(KOL), (PX_ - 0.09, ya, KZF), (PX_ + 0.05, yb, KZF + 1.05))
for y in POST_Y: colbox("PavSloup%d" % len(KOL), (PX_ - 0.09, y - 0.09, KZF), (PX_ + 0.09, y + 0.09, KZW))
colbox("Podesta", (SX0 - 0.96, ST_Y0, KZF - 0.08), (SX0, ST_Y1, KZF))
for (za, zb) in ZAB:
    colbox("Zabr%d" % len(KOL), (min(za[0], zb[0]) - 0.05, min(za[1], zb[1]) - 0.05, KZF), (max(za[0], zb[0]) + 0.05, max(za[1], zb[1]) + 0.05, KZF + 1.05))
ang = math.atan2(STB.z - STA.z, STA.y - STB.y)
colbox("Schody", ((STA + STB) / 2 - Vector((0.43, 0, 0.12))) + Vector((0, 0, 0)), ((STA + STB) / 2 + Vector((0.43, 0, 0.0))), rot=None) if False else None
bpy.ops.mesh.primitive_cube_add(size=1, location=(STA + STB) / 2 + Vector((0, 0, -0.05)))
o_ = bpy.context.active_object; o_.name = "KrcmaL_Kol_Schody-convcolonly"; o_.scale = (0.9, (STB - STA).length, 0.12); o_.rotation_euler = (-ang, 0, 0)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); o_.hide_render = True; KOL.append(o_)
# zabradli schodu na volne strane (stairs rail_side=-1: vnejsi strana = -x): sikmy kvadr podel madla, aby se ze schodu nespadlo
bpy.ops.mesh.primitive_cube_add(size=1, location=(STA + STB) / 2 + Vector((-(0.85 / 2 + 0.05), 0, 0.55)))
o_ = bpy.context.active_object; o_.name = "KrcmaL_Kol_ZabrSchodu-convcolonly"; o_.scale = (0.1, (STB - STA).length, 1.0); o_.rotation_euler = (-ang, 0, 0)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); o_.hide_render = True; KOL.append(o_)
colbox("PlotZ", (X0 - 0.3, Y1, 0), (X0 - 0.1, YARD_Y1, 1.6)); colbox("PlotS1", (X0 - 0.3, YARD_Y1 - 0.1, 0), (PLOT_S1_X1, YARD_Y1 + 0.1, 1.6))
colbox("PlotS2", (PVX0 + 1.2, YARD_Y1 - 0.1, 0), (SX1, YARD_Y1 + 0.1, 1.6)); colbox("PlotV", (SX1 - 0.1, SY1, 0), (SX1 + 0.1, YARD_Y1, 1.6))
for x in (GX0 - 0.1, GX1 + 0.1): colbox("VrataSloup%d" % len(KOL), (x - 0.12, Y0 - 0.12, 0), (x + 0.12, Y0 + 0.12, 2.9))
for (x, y) in ((-7.4, 10.2), (-3.4, 10.2)): colbox("Kulna%d" % len(KOL), (x - 0.1, y - 0.1, 0), (x + 0.1, y + 0.1, 2.3))

# ================================================================= ZNAČKY, SKUPINY, LOD1
E = [empty("KrcmaL_Spani_Hrac", (BEDS[0][0], BEDS[0][1], KZF + 0.6)),
     empty("KrcmaL_Hospodsky_stani", (-3.6, -0.3, ZF)), empty("KrcmaL_Senkyrka_stani", (-2.05, 0.3, ZF)),
     empty("KrcmaL_Ohen_Kuchyne", (-0.15, 3.05, ZF + 0.65)), empty("KrcmaL_Pec_Senkovna", (-2.0, 2.6, ZF + 1.0)),
     empty("KrcmaL_Svetlo_Senkovna", (-4.5, 0.0, ZC - 0.3)), empty("KrcmaL_Kour_Dymnik", ((X0 + X1) / 2 + DYM_A, 0, RD.zr + 0.9))]
g_ext = bpy.data.objects.new("KrcmaL_Exterier_skupina", None); scene.collection.objects.link(g_ext)
g_int = bpy.data.objects.new("KrcmaL_Interier_skupina", None); scene.collection.objects.link(g_int)
for o in list(scene.objects):
    if o.parent is not None or not o.name.startswith("KrcmaL_") or "skupina" in o.name or "_Kol_" in o.name: continue
    o.parent = g_int if ("Interier" in o.name or o.type == 'EMPTY') else g_ext
LO = Mesh("LOD1_KrcmaL")
box(LO, ((X0 + X1) / 2, 0, ZW / 2), (X1 - X0 + 0.3, Y1 - Y0 + 0.3, ZW), Matrix.Identity(3), "tram", uvs=2.0)
box(LO, ((SX0 + KX1) / 2, (SY0 + SY1) / 2, KZW / 2), (KX1 - SX0 + 0.3, SY1 - SY0 + 0.2, KZW), Matrix.Identity(3), "tram", uvs=2.0)
for (R_, ) in ((RD,), (RK,)):
    for sg in (-1, 1):
        p = [R_.Q(sg, R_.a0 - R_.gover, 0) + R_.N(sg) * 0.08, R_.Q(sg, R_.a1 + R_.gover, 0) + R_.N(sg) * 0.08, R_.Q(sg, R_.a1 + R_.gover, R_.dmax) + R_.N(sg) * 0.08, R_.Q(sg, R_.a0 - R_.gover, R_.dmax) + R_.N(sg) * 0.08]
        F(LO, p, [(0, 0), (6, 0), (6, 4), (0, 4)], "sindel", R_.N(sg))
    for ag, nn in ((R_.a0, -1), (R_.a1, 1)):
        F(LO, [R_.W(ag, -R_.hw, R_.zp), R_.W(ag, R_.hw, R_.zp), R_.W(ag, 0, R_.zr)], [(0, 0), (4, 0), (2, 2)], "prkna", R_.A * nn)
lod = LO.build(smooth_angle=30)

# ================================================================= NÁHLED, EXPORT, RENDER
print("scéna…")
preview_scene(trees=((-18, 18, 13), (20, 24, 12), (-22, -6, 11), (26, 4, 15), (2, 34, 14), (-14, 30, 12)), dirt=(1 / 13, 1 / 10, -0.25, -0.35))
for (pos, en, col_) in [((-4.5, 0.0, ZC - 0.4), 60, (1.0, 0.78, 0.55)), ((-0.15, 3.05, ZF + 0.9), 45, (1.0, 0.5, 0.2)), ((4.6, -1.8, ZC - 0.4), 35, (1.0, 0.78, 0.55)),
                        ((3.3, 2.3, ZC - 0.4), 20, (1.0, 0.78, 0.55)), ((14.0, 4.0, 2.2), 60, (1.0, 0.8, 0.6)), ((15.0, 1.0, KZW - 0.5), 40, (1.0, 0.78, 0.55)),
                        ((15.0, 9.0, KZW - 0.5), 40, (1.0, 0.78, 0.55)), ((15.0, 5.0, KZW - 0.5), 40, (1.0, 0.78, 0.55)), ((-6.5, -2.0, ZC - 0.4), 50, (1.0, 0.78, 0.55)), ((-6.5, 2.5, ZC - 0.4), 40, (1.0, 0.78, 0.55)),
                        ((0.6, -2.5, ZC - 0.3), 30, (1.0, 0.78, 0.55)), ((11.5, 3.0, 2.2), 50, (1.0, 0.8, 0.6))]:
    pl = bpy.data.lights.new("Svetlo", 'POINT'); pl.energy = en * 2.2; pl.color = col_; pl.shadow_soft_size = 0.4
    po = bpy.data.objects.new("Svetlo", pl); scene.collection.objects.link(po); po.location = pos; to_prev(po)
export_all("krcma_L", [lod], active=roubeni)
if RENDER:
    for o in DOORS:
        if any(k_ in o.name for k_ in ("Vchod", "Senkovna", "Jizba", "Pokoj1", "Staj_", "Noclezna")):
            o.rotation_euler.z = math.radians(o["otevreni_deg"] * 0.8)
    views = {
        "1_ulice":     (Vector((-13.5, -17.0, 3.2)), Vector((1.0, 0.5, 2.6)), 24, -0.1),
        "2_dvur":      (Vector((-6.5, 21.0, 7.5)), Vector((3.0, 3.5, 2.2)), 24, -0.1),
        "3_pavlac":    (Vector((3.0, 15.5, 2.0)), Vector((10.0, 4.0, 3.2)), 24, -0.1),
        "3b_vrata":    (Vector((7.9, -2.6, 1.7)), Vector((9.8, 2.8, 1.5)), 16, -0.1),
        "3c_ochoz":    (Vector((10.6, -0.7, KZF + 1.65)), Vector((10.8, 9.0, KZF + 1.3)), 18, 0.3),
        "4_senkovna":  (Vector((-1.7, -3.3, 1.65)), Vector((-6.3, 1.5, 1.1)), 18, 1.4),
        "5_vycep":     (Vector((-6.2, -3.0, 1.7)), Vector((-1.6, 0.6, 1.2)), 20, 1.4),
        "6_kuchyne":   (Vector((1.5, -3.4, 1.65)), Vector((0.0, 3.2, 1.6)), 18, 1.4),
        "7_jizba":     (Vector((2.75, -3.45, 1.65)), Vector((6.4, -0.3, 1.0)), 18, 1.4),
        "8_staj":      (Vector((11.0, 9.8, 1.7)), Vector((16.5, 2.0, 0.9)), 18, 1.4),
        "9_pokojik":   (Vector((12.4, 2.6, KZF + 1.65)), Vector((17.5, -0.6, KZF + 0.8)), 18, 1.4),
        "10_noclezna": (Vector((12.9, 7.6, KZF + 1.65)), Vector((17.5, 10.6, KZF + 0.6)), 18, 1.4),
    }
    render_views(views, PRE)
print("HOTOVO")
