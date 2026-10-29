"""Planek dvorcu vsi (Misa 29. 10.: „udelej takhle ves“, kompozice_mapy.md bod 1, KCD reference stodola/kulna/plot).
Kazda usedlost (lokace.json ves.usedlosti, pudorys jako blender/vesnice.py: dum stitem do ulice, dvur na +v, zadni
plot u = -(L/2 + 13)) dostane podle lokace.json ves.dvorec: stodolu napric za dvorem (misto maleho chleva), kulnu
na stejne care az k boku dvora (zadni stena dvora zavrena), sad jabloni za zadnim plotem; na navsi lipa (vnitrek
zatacky ulice). Dohled pocita stejne jako tools/mapa_vyhledu.py (teren vysky.json, koruny, stavby) na bodech ulice
po 10 m a mrizce 15 m v oblasti vsi mimo pudorysy - pred a po. Kolize navrhu (ulice, jina usedlost, voda) vypise.
Vystup: docs/screens/ves_dvorce_plan.png (vlevo dnes, vpravo navrh; sever nahoru) + souhrn.
  python3 tools/ves_dvorce.py"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = 5.0
vys = json.load(open(os.path.join(ROOT, "tools", "krok_b", "vysky.json")))
nx, nz, X0, Z0 = vys["nx"], vys["nz"], vys["X0"], vys["Z0"]
H = np.array(vys["h"], dtype=np.float32).reshape(nz, nx)
lok = json.load(open(os.path.join(ROOT, "pravidla", "svet", "lokace.json")))
VES = lok["ves"]
DV = VES["dvorec"]
OBL = next(o for o in lok["kompozice"]["dohled_oblasti"] if o["id"] == "ves")
MEZ = float(OBL["max_m"])
LISTI = lok["kompozice"]["mapa_dohledu"]
JEMNE = 1.0                                   # mrizka prekazek 1 m (stodola 10 m musi byt videt)
x0, z0 = OBL["stred"][0] - 260.0, OBL["stred"][1] - 260.0
NJ = int(520 / JEMNE)
gx = x0 + np.arange(NJ) * JEMNE
gz = z0 + np.arange(NJ) * JEMNE


def vyska(x, z, pole=H):
    i, j = (np.asarray(x) - X0) / K, (np.asarray(z) - Z0) / K
    i0, j0 = np.clip(i.astype(int), 0, nx - 2), np.clip(j.astype(int), 0, nz - 2)
    fi, fj = np.clip(i - i0, 0, 1), np.clip(j - j0, 0, 1)
    return (pole[j0, i0] * (1 - fi) + pole[j0, i0 + 1] * fi) * (1 - fj) + (pole[j0 + 1, i0] * (1 - fi) + pole[j0 + 1, i0 + 1] * fi) * fj


# koruny stromu (jako mapa_vyhledu: valec 0,3 h)
dr = {d["id"]: d for d in json.load(open(os.path.join(ROOT, "pravidla", "svet", "druhy.json")))["druhy"]}
ids = sorted(dr, key=len, reverse=True)
svet = json.load(open(os.path.join(ROOT, "modely", "svet.json")))
GX, GZ = np.meshgrid(gx, gz)
class Vrstvy:
    """A) pevne zakryti (zdi staveb: vyska od zeme) a B) listi (koruny, kere: pas od nasazeni po vrchol) zvlast
    (Astra 29. 10.: koruna nezavre pruhled pod ni mezi kmeny, listi neni nepruhledna stena)."""
    def __init__(s):
        s.P = np.zeros((NJ, NJ), np.float32)
        s.VL = np.full((NJ, NJ), np.inf, np.float32)
        s.VH = np.zeros((NJ, NJ), np.float32)

    def copy(s):
        o = Vrstvy()
        o.P, o.VL, o.VH = s.P.copy(), s.VL.copy(), s.VH.copy()
        return o


KOR0 = Vrstvy()
stromy = []
for k, arr in svet["rostliny"].items():
    i = next((i for i in ids if k == i or k.startswith(i + "_")), None)
    if i is None or dr[i]["skupina"] != "strom" or "daleko" in k:
        continue
    for m in arr:
        sy = math.sqrt(m[1] ** 2 + m[5] ** 2 + m[9] ** 2)
        h = max(4.0, min(30.0, sy * (12.0 if sy < 3.0 else 1.0)))
        x, z = m[3], m[11]
        if abs(x - OBL["stred"][0]) < 270 and abs(z - OBL["stred"][1]) < 270:
            stromy.append((x, z, max(2.0, 0.3 * h), h))


def razit(cil, poly=None, kruh=None, h=0.0, lo=None):
    if kruh is not None:
        cx, cz, r = kruh
        msk = (GX - cx) ** 2 + (GZ - cz) ** 2 < r * r
    else:
        msk = np.ones_like(GX, bool)
        n = len(poly)
        for a in range(n):
            (ax, az), (bx, bz) = poly[a], poly[(a + 1) % n]
            msk &= (bx - ax) * (GZ - az) - (bz - az) * (GX - ax) >= 0
    if lo is None:
        cil.P[msk] = np.maximum(cil.P[msk], h)
    else:
        cil.VL[msk] = np.minimum(cil.VL[msk], lo)
        cil.VH[msk] = np.maximum(cil.VH[msk], h)


for x, z, r, h in stromy:
    razit(KOR0, kruh=(x, z, r), h=h, lo=h * LISTI["nasazeni_koruny"])


class Usedlost:
    def __init__(s, e):
        s.k = e["k"]
        s.c = np.array(e["novy_stred"])
        a = e["novy_yaw"]
        s.au, s.av = np.array([math.cos(a), math.sin(a)]), np.array([-math.sin(a), math.cos(a)])
        s.L, s.W = e["L"], e["W"]
        s.back, s.vR, s.vL = -(s.L / 2 + 13.0), s.W / 2 + 9.5, -s.W / 2 - 6.2

    def w(s, u, v):
        return tuple(s.c + s.au * u + s.av * v)

    def obd(s, u0, u1, v0, v1):
        p = [s.w(u0, v0), s.w(u1, v0), s.w(u1, v1), s.w(u0, v1)]
        # proti smeru hodinovych rucicek v (x, z)
        a = sum((p[i][0] * p[(i + 1) % 4][1] - p[(i + 1) % 4][0] * p[i][1]) for i in range(4))
        return p if a > 0 else p[::-1]

    def uvnitr(s, x, z, okraj=0.0):
        d = np.array([x, z]) - s.c
        u, v = d @ s.au, d @ s.av
        return s.back - okraj < u < s.L / 2 + 2.5 + okraj and s.vL - okraj < v < s.vR + okraj


us = [Usedlost(e) for e in VES["usedlosti"]]


def osa_ulice():
    ul = VES["ulice"]
    p = np.array(ul["vjezd"], float)
    h = float(ul["smer"])
    out = [p.copy()]
    for _ in range(int(ul["L1"])):
        p = p + [math.cos(h), math.sin(h)]
        out.append(p.copy())
    t = math.radians(ul["turn_st"])
    n = int(abs(t) * ul["R"])
    for _ in range(n):
        h += t / n
        p = p + np.array([math.cos(h), math.sin(h)]) * abs(t) * ul["R"] / n
        out.append(p.copy())
    for _ in range(int(ul["L2"])):
        p = p + [math.cos(h), math.sin(h)]
        out.append(p.copy())
    return np.array(out)


OSA = osa_ulice()


def od_ulice(x, z):
    return float(np.min(np.hypot(OSA[:, 0] - x, OSA[:, 1] - z)))


# --- dnes: domy (vyska hrebene) a male chlevy ---
def zaklad(seznam):
    KOR = KOR0.copy()
    for s in seznam:
        razit(KOR, s.obd(-s.L / 2, s.L / 2, -s.W / 2, s.W / 2), h=DV["dum_vyska_m"])
        razit(KOR, s.obd(-(s.L / 2 + 6.5) - 2.5, -(s.L / 2 + 6.5) + 2.5, -3.0, 3.5), h=DV["chlev_vyska_m"])
    return KOR


sd, kl, sa = DV["stodola"], DV["kolna"], DV["sad"]
kolize = []


def dvorce(seznam):
    """Stodola, kulna, zahumenek a zivy plot pro kazdou usedlost seznamu (prekazky bez chleva)."""
    KOR = KOR0.copy()
    navrh = []
    for s in seznam:
        razit(KOR, s.obd(-s.L / 2, s.L / 2, -s.W / 2, s.W / 2), h=DV["dum_vyska_m"])
        ub = -(s.L / 2) - sd["za_domem_m"] - sd["hloubka_m"] / 2
        uk1 = ub + sd["hloubka_m"] / 2

        def rozlozeni(zrc):
            # stodola od boku vL a kulna k vR; zrc: obracene (stodola od vR) - kdyz roh vjede do jine usedlosti
            v0 = s.vL + sd["od_boku_m"]
            v1 = v0 + sd["delka_m"] + kl["mezera_m"]
            v2 = min(s.vR - 0.5, v1 + kl["delka_m"])
            if zrc:
                m = lambda v: s.vL + s.vR - v
                v0, v1, v2 = m(v0 + sd["delka_m"]), m(v2), m(v1)
            return (s.obd(ub - sd["hloubka_m"] / 2, ub + sd["hloubka_m"] / 2, v0, v0 + sd["delka_m"]),
                    s.obd(uk1 - kl["hloubka_m"], uk1, v1, v2))

        def narazi(rz):
            return sum(any(o.uvnitr(x, z) for o in seznam if o is not s) for pg in rz for x, z in pg)
        pst, pkl = min((rozlozeni(False), rozlozeni(True)), key=narazi)
        razit(KOR, pst, h=sd["vyska_m"])
        razit(KOR, pkl, h=kl["vyska_m"])
        navrh += [("stodola", pst, s.k), ("kolna", pkl, s.k)]
        # zelen u staveni (tradicni schema, Dohnalova 2023: predzahradka, strom u vjezdu, strom na dvore, protipozarni
        # strom u stodoly v humne, ovocna zahrada) - lokace.json ves.dvorec.zelen
        for zn, z_ in DV["zelen"].items():
            if not isinstance(z_, dict) or "u" not in z_:
                continue
            uu = {"predek": s.L / 2, "stodola": ub - sd["hloubka_m"] / 2, "dum": 0.0}[z_["u"][0]] + z_["u"][1]
            vv = {"vR": s.vR, "vL": s.vL, "dum": s.W / 2}[z_["v"][0]] + z_["v"][1]
            if "pas" in z_:
                pz = s.obd(uu, uu + z_["pas"][0], -s.W / 2, s.W / 2)
                razit(KOR, pz, h=z_["vyska_m"], lo=0.0)
                navrh.append(("predzahradka", pz, s.k))
                continue
            x, z = s.w(uu, vv)
            if od_ulice(x, z) > z_.get("od_ulice_m", 3.0):
                razit(KOR, kruh=(x, z, z_["polomer_m"]), h=z_["vyska_m"], lo=z_["vyska_m"] * LISTI["nasazeni_koruny"])
                navrh.append(("strom_" + zn, (x, z, z_["polomer_m"]), s.k))
        # zahumenek: sad jabloni v radach od zadniho plotu do hloubky, na konci zivy plot (bez, sipek) u zahumenni cesty
        rng = np.random.default_rng(s.k)
        u = s.back - sa["za_plotem_m"]
        while u > s.back - sa["hloubka_m"]:
            v = s.vL + 2.0
            while v < s.vR - 1.0:
                x, z = s.w(u + rng.uniform(-1, 1), v + rng.uniform(-1, 1))
                if od_ulice(x, z) > sa["od_ulice_m"] and not any(o.uvnitr(x, z, 1.0) for o in seznam if o is not s):
                    razit(KOR, kruh=(x, z, sa["polomer_m"]), h=sa["vyska_m"], lo=sa["vyska_m"] * LISTI["nasazeni_koruny"])
                    navrh.append(("jablon", (x, z, sa["polomer_m"]), s.k))
                v += sa["rozestup_m"]
            u -= sa["rozestup_m"]
        zp = DV["zivy_plot"]
        uz = s.back - sa["hloubka_m"] - 1.0
        pzp = s.obd(uz - zp["sire_m"] / 2, uz + zp["sire_m"] / 2, s.vL, s.vR)
        if all(od_ulice(x, z) > sa["od_ulice_m"] for x, z in pzp):
            razit(KOR, pzp, h=zp["vyska_m"], lo=0.0)
            navrh.append(("plot", pzp, s.k))
        else:
            kolize.append("usedlost %d: zivy plot zahumenku na ulici - vynechan" % s.k)
        for nm, p in (("stodola", pst), ("kolna", pkl)):
            for x, z in p:
                if od_ulice(x, z) < VES["ulice"]["od_pudorysu_m"] + 2:
                    kolize.append("usedlost %d: %s roh u ulice (%.0f, %.0f)" % (s.k, nm, x, z))
                if any(o.uvnitr(x, z) for o in seznam if o is not s):
                    kolize.append("usedlost %d: %s roh v jine usedlosti (%.0f, %.0f)" % (s.k, nm, x, z))
    # lipa na navsi: vnitrek zatacky (stred oblouku ulice posunuty dovnitr)
    ul = VES["ulice"]
    im_ = int(ul["L1"]) + int(abs(math.radians(ul["turn_st"])) * ul["R"]) // 2
    t = OSA[im_ + 1] - OSA[im_ - 1]
    t = t / np.linalg.norm(t)
    nrm = np.array([-t[1], t[0]]) * (1 if ul["turn_st"] > 0 else -1)
    lp = OSA[im_] + nrm * DV["lipa"]["od_osy_m"]
    razit(KOR, kruh=(lp[0], lp[1], DV["lipa"]["polomer_m"]), h=DV["lipa"]["vyska_m"], lo=DV["lipa"]["vyska_m"] * LISTI["nasazeni_koruny"])
    navrh.append(("lipa", (lp[0], lp[1], DV["lipa"]["polomer_m"]), -1))
    return KOR, navrh


def doplnit(seznam):
    """Chalupy do mezer podel ulice (lokace.json ves.dvorec.doplnit): na kazde strane ulice, kde je mezi pudorysy
    usedlosti vic nez mezera_max_m, nova usedlost uprostred mezery, stitem do ulice, odstup od osy jako sousede."""
    dp = DV["doplnit"]
    t = np.gradient(OSA, axis=0)
    t = t / np.linalg.norm(t, axis=1)[:, None]
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    rady = {-1: [], 1: []}
    for s in seznam:
        i = int(np.argmin(np.hypot(OSA[:, 0] - s.c[0], OSA[:, 1] - s.c[1])))
        lat = float((s.c - OSA[i]) @ nrm[i])
        rady[int(np.sign(lat))].append((i, abs(lat), s))
    nove = []
    k = 100
    for strana, r in rady.items():
        r.sort(key=lambda q: q[0])
        meze = [(0, None)] + [(q[0], q) for q in r] + [(len(OSA) - 1, None)]
        for (ia, qa), (ib, qb) in zip(meze, meze[1:]):
            pol_a = 0 if qa is None else (qa[2].vR - qa[2].vL) / 2
            pol_b = 0 if qb is None else (qb[2].vR - qb[2].vL) / 2
            mez = (ib - ia) - pol_a - pol_b
            n = int(mez // dp["rozestup_m"])
            if mez < dp["mezera_max_m"] or n < 1:
                continue
            lat = np.mean([q[1] for q in (qa, qb) if q is not None])
            for j in range(n):
                f = ia + pol_a + mez * (j + 0.5) / n
                i = int(round(f))
                c = OSA[i] + nrm[i] * strana * lat
                au = -nrm[i] * strana                      # stit (+u) k ulici
                yaw = math.atan2(au[1], au[0])
                e = {"k": k, "novy_stred": list(c), "novy_yaw": yaw, "L": dp["L"], "W": dp["W"]}
                n_ = Usedlost(e)
                rohy = n_.obd(n_.back, n_.L / 2 + 2.5, n_.vL, n_.vR)
                if any(o.uvnitr(x, z, dp["okraj_m"]) for o in seznam + nove for x, z in rohy) or \
                        any(n_.uvnitr(x, z, dp["okraj_m"]) for o in seznam + nove for x, z in o.obd(o.back, o.L / 2 + 2.5, o.vL, o.vR)):
                    kolize.append("doplneni: chalupa u (%.0f, %.0f) by vjela do sousedni usedlosti - vynechana" % tuple(c))
                    continue
                k += 1
                nove.append(n_)
    return nove


KOR_DNES = zaklad(us)
KOR_PO, navrh = dvorce(us)
DOPLNIT = "--doplnit" in os.sys.argv           # Astra 29. 10.: domy navic jen kvuli mape dohledu ne (kazdy dum stoji vykon)
us_c = us + (doplnit(us) if DOPLNIT else [])
KOR_C, navrh_c = dvorce(us_c)


def dohled(px, pz, oko, KOR):
    """16 smeru, paprsek z oci vodorovne (+0,5 st. obzor): (pevne, vizualne) - pevne = kde narazi na teren nebo zed
    stavby; vizualne = kde paprsek proleti listim celkem vic nez listi_zavre_m (jen dojem, okluze ve hre to neni)."""
    y0 = float(vyska(px, pz)) + oko
    d = np.arange(4.0, 600.0, 1.0)
    pev, viz = [], []
    for k in range(16):
        a = k * math.pi / 8
        xs, zs = px + math.sin(a) * d, pz + math.cos(a) * d
        i = np.clip(((xs - x0) / JEMNE).astype(int), 0, NJ - 1)
        j = np.clip(((zs - z0) / JEMNE).astype(int), 0, NJ - 1)
        uv = (xs > x0) & (xs < x0 + NJ) & (zs > z0) & (zs < z0 + NJ)
        zem = vyska(xs, zs)
        yr = y0 + d * math.tan(math.radians(0.5)) - zem          # vyska paprsku nad zemi
        hit = (yr < 0) | (uv & (KOR.P[j, i] > yr))
        dp = float(d[np.argmax(hit)]) if hit.any() else 600.0
        vl = uv & (KOR.VL[j, i] <= yr) & (KOR.VH[j, i] >= yr) & (d < dp)
        cum = np.cumsum(vl) * JEMNE
        dv = float(d[np.argmax(cum >= LISTI["listi_zavre_m"])]) if cum[-1] >= LISTI["listi_zavre_m"] else dp
        pev.append(dp)
        viz.append(min(dp, dv))
    return pev, viz


body = [("ulice", float(p[0]), float(p[1])) for p in OSA[::10]]
for x in np.arange(OBL["stred"][0] - OBL["polomer_m"], OBL["stred"][0] + OBL["polomer_m"], 15.0):
    for z in np.arange(OBL["stred"][1] - OBL["polomer_m"], OBL["stred"][1] + OBL["polomer_m"], 15.0):
        if math.hypot(x - OBL["stred"][0], z - OBL["stred"][1]) < OBL["polomer_m"] and not any(s.uvnitr(x, z) for s in us):
            body.append(("mrizka", float(x), float(z)))
vys_ = {}
VAR = [("dnes", KOR_DNES), ("navrh", KOR_PO)] + ([("doplnit", KOR_C)] if DOPLNIT else [])
for nm, KOR in VAR:
    for oko in (1.7, 2.4):                     # pesi a jezdec
        vys_[(nm, oko)] = [(t, x, z) + dohled(x, z, oko, KOR) for t, x, z in body]

# --- obrazek: dva panely, sever (-z) nahoru ---
SC = 3.0
R0 = OBL["polomer_m"] + 45
cx, cz = OBL["stred"]
PW = int(2 * R0 * SC)


def px(x, z):
    return ((x - cx + R0) * SC, (z - cz + R0) * SC)


xs = np.linspace(cx - R0, cx + R0, PW)
zs = np.linspace(cz - R0, cz + R0, PW)
XX, ZZ = np.meshgrid(xs, zs)
HH = vyska(XX.ravel(), ZZ.ravel()).reshape(PW, PW)
gy, gxx = np.gradient(HH)
stin = np.clip(0.75 + (-gxx - gy) * 1.2, 0.35, 1.0)
zakl = np.stack([110 * stin, 140 * stin, 90 * stin], -1).astype(np.uint8)
try:
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    Fm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except OSError:
    F = Fm = ImageFont.load_default()
panely = []
PAN = [("dnes", "A) DNES", us, []), ("navrh", "B) dvorce: stodola, kulna, zahumenek, zelen u staveni", us, navrh)]
if DOPLNIT:
    PAN.append(("doplnit", "C) jako B + chalupy do mezer ulice", us_c, navrh_c))
for nm, titul, seznam, nv in PAN:
    im = Image.fromarray(zakl.copy())
    dw = ImageDraw.Draw(im, "RGBA")
    for x, z, r, h in stromy:
        p = px(x, z)
        dw.ellipse([p[0] - r * SC, p[1] - r * SC, p[0] + r * SC, p[1] + r * SC], fill=(40, 80, 35, 200))
    dw.line([px(*p) for p in OSA], fill=(200, 180, 140), width=int(3.2 * SC))
    for s in seznam:
        dw.polygon([px(*p) for p in s.obd(s.back, s.L / 2 + 2.5, s.vL, s.vR)], outline=(240, 240, 220))
        dw.polygon([px(*p) for p in s.obd(-s.L / 2, s.L / 2, -s.W / 2, s.W / 2)], fill=(170, 60, 40) if s.k < 100 else (220, 120, 60))
        if nm == "dnes":
            dw.polygon([px(*p) for p in s.obd(-(s.L / 2 + 6.5) - 2.5, -(s.L / 2 + 6.5) + 2.5, -3.0, 3.5)], fill=(150, 120, 80))
        p = px(*s.w(0, 0))
        dw.text((p[0] - 6, p[1] - 10), str(s.k) if s.k < 100 else "N", fill="white", font=F)
    if True:
        for druh, g, k in nv:
            if druh == "predzahradka":
                dw.polygon([px(*p) for p in g], fill=(220, 120, 200), outline=(80, 30, 70))
            elif druh.startswith("strom_"):
                p = px(g[0], g[1])
                r = g[2] * SC
                dw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(20, 90, 60, 235), outline=(10, 30, 10))
            elif druh == "plot":
                dw.polygon([px(*p) for p in g], fill=(70, 110, 40), outline=(20, 40, 20))
            elif druh == "stodola":
                dw.polygon([px(*p) for p in g], fill=(110, 70, 35), outline=(30, 20, 10))
            elif druh == "kolna":
                dw.polygon([px(*p) for p in g], fill=(190, 150, 90), outline=(30, 20, 10))
            else:
                p = px(g[0], g[1])
                r = g[2] * SC
                dw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(60, 140, 50, 230) if druh == "jablon" else (30, 110, 30, 240),
                           outline=(20, 40, 20))
    c = px(cx, cz)
    rr = OBL["polomer_m"] * SC
    dw.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], outline=(255, 255, 255, 120), width=2)
    # bod: vypln = pevne zakryti (teren, zdi), obrys = vizualne s listim; horsi z oci pesiho a jezdce
    st = {"P": 0, "V": 0, "uP": 0, "uV": 0, "uprum": [], "smP": [], "smV": []}
    for (t, x, z, p1, v1), (_, _, _, p2, v2) in zip(vys_[(nm, 1.7)], vys_[(nm, 2.4)]):
        p = px(x, z)
        pv = [max(a_, b_) for a_, b_ in zip(p1, p2)]
        vv = [max(a_, b_) for a_, b_ in zip(v1, v2)]
        mp, mv = max(pv), max(vv)
        st["P"] += mp > MEZ
        st["V"] += mv > MEZ
        if t == "ulice":
            st["uP"] += mp > MEZ
            st["uV"] += mv > MEZ
            st["uprum"].append(np.mean(pv))
            st["smP"].append(np.mean([d_ > MEZ for d_ in pv]))
            st["smV"].append(np.mean([d_ > MEZ for d_ in vv]))
        barva = lambda m: (220, 40, 40) if m > MEZ else ((235, 200, 40) if m > 90 else (60, 210, 60))
        for k, d in enumerate(pv):              # paprsky pevne otevrene pres mez
            if d > MEZ:
                a = k * math.pi / 8
                dw.line([p, px(x + math.sin(a) * 35, z + math.cos(a) * 35)], fill=(220, 40, 40, 110), width=1)
        dw.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill=barva(mv))
        dw.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=barva(mp), outline=(0, 0, 0))
    nu = sum(1 for b_ in body if b_[0] == "ulice")
    prum, uo, up = 0.0, 100 * np.mean(st["smP"]), float(np.mean(st["uprum"]))
    dw.rectangle([0, 0, PW, 64], fill=(0, 0, 0, 170))
    dw.text((10, 6), titul, fill="white", font=F)
    dw.text((10, 36), "ulice: smeru otevrenych > %d m pevne %.0f %%, s listim %.0f %%; prumer pevneho dohledu %.0f m (oci 1,7 a 2,4 m)" %
            (MEZ, 100 * np.mean(st["smP"]), 100 * np.mean(st["smV"]), np.mean(st["uprum"])), fill="white", font=Fm)
    otev = 100 * np.mean(st["smV"])
    panely.append((im, otev, prum, uo, up))
out = Image.new("RGB", (PW * len(panely) + 10 * (len(panely) - 1), PW + 64), (20, 20, 20))
for i, pn in enumerate(panely):
    out.paste(pn[0], (i * (PW + 10), 0))
dw = ImageDraw.Draw(out)
dw.text((10, PW + 34), "stred bodu = pevne zakryti (teren, zdi staveb), okraj = vizualne s listim (koruna jen od nasazeni po vrchol, "
        "zavre az po %.0f m listi) - jen navrhova pomucka, vykon se overi merenim ve hre" % LISTI["listi_zavre_m"], fill="white", font=Fm)
dw.text((10, PW + 8), "cervena = dohled pres mez vsi (paprsky ukazuji kam), zluta 90-%d m, zelena zavreno do 90 m; "
        "hnede = stodola, svetle = kulna, svetle zelene = jablone sadu, tmave = stromy u staveni a lipa na navsi, ruzove = predzahradka" % MEZ, fill="white", font=Fm)
cesta = os.path.join(ROOT, "docs", "screens", "ves_dvorce_plan.png")
out.save(cesta)
for nm, pn in zip("ABC", panely):
    print("DVORCE %s: ulice - smeru otevrenych pevne %.0f %%, s listim %.0f %%, prumer pevneho dohledu %.0f m" % (nm, pn[3], pn[1], pn[4]))
print("DVORCE doplnenych chalup %d -> %s" % (len(us_c) - len(us), cesta))
for k in kolize:
    print("KOLIZE", k)
