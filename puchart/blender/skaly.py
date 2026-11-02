"""Skalní výchozy z droby kolem dvojhradu a na hřbetu (pravidla/svet/skaly.json).

DMR 5G má u hradů jen 0,07 bodu/m², skály vysoké 2–6 m mezi body propadnou a terén je vyhladí do travnatého svahu.
Skály proto přidáváme jako geometrii (manuál P0, dodatek A: ostré skalní hrany doplňkovou 3D geometrií, ne deformací
mapy). Poloha ze sklonu a vypouklosti herního terénu (= DMR + schválené zásahy), vzhled podle fotek: vrstevnaté desky
droby s jednotným úklonem, stupně po svahu, suť kolem. Pod vnější líc hradeb na svahu výchoz – hradba stojí na skále.
Výstup: hra/modely/hrady/skaly.glb (díly po 60 m kvůli ořezu, uzel KOLIZE pro velké desky).
  /opt/bl/bin/python blender/skaly.py <koren_puchartu>
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrady as H
from hrady import Part, M, R, frame, ter, UP, Vector, Matrix
import numpy as np
sys.path.insert(0, os.path.join(H.K, "nastroje"))
import hrad_geom

K = H.K
S = json.load(open(os.path.join(K, "pravidla/svet/skaly.json")))
D = json.load(open(os.path.join(K, "pravidla/svet/hrad_puchart.json"))); A, B = D["A"], D["B"]
C = json.load(open(os.path.join(K, "pravidla/svet/cesty_puchart.json")))
rng = np.random.default_rng(1393)

def dist_polyline(px, pz, pts):
    p = np.array(pts, float); d = np.full(np.shape(px), 1e9)
    for a, b in zip(p[:-1], p[1:]):
        ab = b - a; t = np.clip(((px - a[0]) * ab[0] + (pz - a[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
        d = np.minimum(d, np.hypot(px - (a[0] + ab[0] * t), pz - (a[1] + ab[1] * t)))
    return d

def uvnitr(px, pz, poly):
    p = np.array(poly, float); n = len(p); ins = np.zeros(np.shape(px), bool)
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        c = ((a[1] > pz) != (b[1] > pz)) & (px < (b[0] - a[0]) * (pz - a[1]) / (b[1] - a[1] + 1e-12) + a[0])
        ins ^= c
    return ins

def dist_poly(px, pz, poly): return dist_polyline(px, pz, list(poly) + [poly[0]])

# ---------------------------------------------------------------- geometrie hradů (stejná data jako stavba)
j = np.array(A["jadro"]); a_, b_ = j[A["brana"]["usek"]], j[A["brana"]["usek"] + 1]
CA = (a_ + b_) / 2; dw = (b_ - a_) / np.linalg.norm(b_ - a_); nA = np.array([dw[1], -dw[0]])
if np.dot(nA, CA - j.mean(0)) < 0: nA = -nA
OA = CA + nA * A["vnejsi_brana"]["t_m"]
hb = np.array(B["hradba"]); wa, wb = hb[B["brana"]["usek"]], hb[B["brana"]["usek"] + 1]
GB = wa + (wb - wa) / np.linalg.norm(wb - wa) * B["brana"]["stred_m"]
mosty = [[CA.tolist(), (CA + nA * 36).tolist()], [B["most"]["od"], GB.tolist()]]
brany = [CA, OA, GB]
cesty = [c["osa"] for c in C["cesty"]]
zony = S["zony"]; hreben = next(c["osa"] for c in C["cesty"] if c["id"] == next(z["cesta"] for z in zony if "cesta" in z))

# ---------------------------------------------------------------- sklon a vypouklost herního terénu
X0, X1, Z0, Z1 = -70, 130, -75, 185
xs = np.arange(X0, X1, 1.0); zs = np.arange(Z0, Z1, 1.0); XX, ZZ = np.meshgrid(xs, zs)
Y = np.vectorize(ter)(XX, ZZ)
gz, gx = np.gradient(Y); sklon = np.degrees(np.arctan(np.hypot(gx, gz)))
def rozmaz(a, n=2):
    for _ in range(n): a = (a + np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 5
    return a
Ys = rozmaz(Y, 3)
lap = (np.roll(Ys, 2, 0) + np.roll(Ys, -2, 0) + np.roll(Ys, 2, 1) + np.roll(Ys, -2, 1) - 4 * Ys) / 4.0   # záporné = vypouklé
vyp = np.clip(-lap, 0, None)

zona = dist_polyline(XX, ZZ, hreben) < next(z["sirka_m"] for z in zony if "cesta" in z)
for z in zony:
    if "stred" in z: zona |= np.hypot(XX - z["stred"][0], ZZ - z["stred"][1]) < z["r"]
V = S["vyloucit"]
ven = np.zeros(XX.shape, bool)
for c in cesty: ven |= dist_polyline(XX, ZZ, c) < V["cesty_m"]
for m in mosty: ven |= dist_polyline(XX, ZZ, m) < V["mosty_m"]
for g in brany: ven |= np.hypot(XX - g[0], ZZ - g[1]) < V["brany_m"]
ven |= uvnitr(XX, ZZ, A["jadro"]) | (dist_poly(XX, ZZ, A["jadro"]) < A["kurtina_tloustka"] / 2 + V["uvnitr_hradu_m"])
ven |= uvnitr(XX, ZZ, B["hradba"]) | (dist_poly(XX, ZZ, B["hradba"]) < B["tloustka"] / 2 + V["uvnitr_hradu_m"])
for pl in D["teren"]["plosiny"]:
    if "polygon" in pl: ven |= uvnitr(XX, ZZ, pl["polygon"])
for hv in (A["hradba_val"]["osa"], A["hradba_vychod"]["osa"]): ven |= dist_polyline(XX, ZZ, hv) < 1.4
g = hrad_geom.sklep(A)   # sklepní šíje a palác
u = (XX - g["o"][0]) * g["du"][0] + (ZZ - g["o"][1]) * g["du"][1]; v = (XX - g["o"][0]) * g["dv"][0] + (ZZ - g["o"][1]) * g["dv"][1]
ven |= (u > -3) & (u < g["Li"] + 3) & (v > -3) & (v < g["Wi"] + 5)

skore = np.clip((sklon - S["sklon_min_deg"]) / 18.0, 0, 1) * (0.4 + np.clip(vyp / S["vypouklost_min"], 0, 2))
skore = np.maximum(skore, (vyp > S["hreben_vypouklost_min"]) * 0.6 * (dist_polyline(XX, ZZ, hreben) < 12))   # žebra na hřbetu
skore[~zona | ven] = 0
kand = np.argwhere(skore > 0.05)
poradi = rng.permutation(len(kand))
semena = []
for k in poradi:
    r, c = kand[k]
    if rng.random() > skore[r, c] * S["hustota"]: continue
    p = np.array([xs[c], zs[r]])
    if semena and min(np.hypot(*(p - q[:2])) for q in semena[-400:]) < S["rozestup_m"]: continue
    semena.append([p[0], p[1], float(sklon[r, c]), 0])

# pata hradeb: výchoz pod vnějším lícem na svahu (vrch u paty zdi)
ph = S["pata_hradeb"]
def pata(poly, t, uzavrena=True):
    pts = list(poly) + ([poly[0]] if uzavrena else [])
    st = np.array(poly, float).mean(0)
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = np.array(a, float), np.array(b, float); L = np.linalg.norm(b - a); d = (b - a) / L; n_ = np.array([d[1], -d[0]])
        if uzavrena and np.dot(n_, (a + b) / 2 - st) < 0: n_ = -n_
        for s in np.arange(ph["krok_m"] / 2, L, ph["krok_m"]):
            p = a + d * s + n_ * (t / 2 + ph["odstup_m"])
            if any(np.hypot(*(p - g_)) < V["brany_m"] for g_ in brany): continue
            if any(dist_polyline(np.array(p[0]), np.array(p[1]), m) < V["mosty_m"] for m in mosty): continue
            if any(dist_polyline(np.array(p[0]), np.array(p[1]), cc) < V["cesty_m"] for cc in cesty): continue
            sl = math.degrees(math.atan(abs(ter(*(p + n_)) - ter(*(p - n_ * 0.2))) / 1.2))
            if sl >= ph["sklon_min_deg"]: semena.append([p[0], p[1], sl, 1, d[0], d[1]])
pata(A["jadro"], A["kurtina_tloustka"]); pata(B["hradba"], B["tloustka"])
print("výchozů", len(semena), "z toho pod hradbami", sum(1 for q in semena if q[3] == 1))

# ---------------------------------------------------------------- stavba výchozů
ZB = S["zebro"]; SU = S["sut"]; DIL = 60.0
dily = {}
def dil(x, z):
    k = (int((x - X0) // DIL), int((z - Z0) // DIL))
    if k not in dily: dily[k] = Part("skaly_%d_%d" % k)
    return dily[k]

def spad(x, z):   # směr po spádu (vodorovně)
    e = 0.7; gx_ = ter(x + e, z) - ter(x - e, z); gz_ = ter(x, z + e) - ter(x, z - e)
    v = Vector((-gx_, 0, -gz_)); return v.normalized() if v.length > 1e-4 else Vector((1, 0, 0))

def balvan(P, c, sm, sp, L, W, top, naklon, mat, kol):
    """Nepravidelný skalní blok: 3 prstence po 4 rozích (spodek zapuštěný, střed vyboulený, vršek zúžený), rohy
    náhodně posunuté; osa L po vrstevnici (sm), W po spádu (sp); nakloněný po spádu (vrstvy vycházejí jako stupně)."""
    dno = min(ter(*(c + sp * (W / 2)).xz), ter(*(c - sp * (W / 2)).xz), ter(*c.xz)) - 0.8
    h = max(0.6, top - dno); up = (UP + sp * math.tan(math.radians(naklon))).normalized()
    j = lambda: rng.uniform(-0.18, 0.18)
    ringy = [(0.0, 1.0), (0.62, 1.08), (1.0, 0.72)]
    vs = []
    for yy, sc in ringy:
        for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q = c + sm * (su * L / 2 * sc * (1 + j())) + sp * (sw * W / 2 * sc * (1 + j())) + up * (h * yy * (1 + j() * 0.5))
            vs.append(Vector((q.x, dno + (q.y - c.y), q.z)))
    f = [(3, 2, 1, 0), (8, 9, 10, 11)]
    for r0 in (0, 4):
        for i in range(4):
            a_, b_ = r0 + i, r0 + (i + 1) % 4; f.append((a_, b_, b_ + 4, a_ + 4))
    P.mesh([tuple(v) for v in vs], f, mat)
    if kol:
        P.cols.append((M(Vector((c.x, dno + h / 2, c.z)), basis=frame(sm)), (W * 0.8, h, L * 0.85)))

nkol = 0
for q in semena:
    x, z, sl, typ = q[:4]
    P = dil(x, z); c0 = Vector((x, 0, z)); sp = spad(x, z)
    sm = UP.cross(sp).normalized() if typ == 0 else Vector((q[4], 0, q[5]))
    if typ == 1: sp = Vector((-sm.z, 0, sm.x)) if Vector((-sm.z, 0, sm.x)).dot(spad(x, z)) > 0 else Vector((sm.z, 0, -sm.x))
    f = min(1.0, max(0.0, (sl - 25) / 30))
    delka = rng.uniform(*ZB["delka_m"]) * (0.6 if typ == 1 else 1.0); nb = int(rng.integers(ZB["bloku"][0], ZB["bloku"][1] + 1))
    naklon = rng.uniform(*ZB["naklon_deg"])
    vyska = rng.uniform(*ZB["nad_terenem_m"]) * (0.5 + f)
    for i in range(nb):
        s_ = (i / max(1, nb - 1) - 0.5) * delka + rng.uniform(-0.4, 0.4)
        L = rng.uniform(*ZB["blok_delka_m"]); W = rng.uniform(*ZB["blok_hloubka_m"])
        c = c0 + sm * s_ + sp * rng.uniform(-0.5, 0.8)
        top = ter(*(c - sp * (W / 2)).xz) + vyska * rng.uniform(0.6, 1.15)   # vršek nad horní (návrší) hranou bloku
        if typ == 1: top = min(top, ter(*(c0 - sp * 0.6).xz) + 0.3)   # pod hradbou: vrch u paty zdi
        kol = top - ter(*c.xz) > S["kolize_nad_m"]; nkol += kol
        balvan(P, c, sm, sp, L, W, top, naklon + rng.uniform(-5, 5), "skala_mech" if rng.random() < 0.4 else "skala", kol)
    for _ in range(int(rng.integers(SU["kamenu_na_vychoz"][0], SU["kamenu_na_vychoz"][1] + 1))):   # suť po spádu pod žebrem
        r = rng.uniform(*SU["velikost_m"]); p = c0 + sp * rng.uniform(1.0, SU["rozptyl_m"]) + sm * rng.uniform(-0.6, 0.6) * delka
        if any(dist_polyline(np.array(p.x), np.array(p.z), cc) < V["cesty_m"] for cc in cesty): continue
        balvan(P, p, sm, sp, r * rng.uniform(1.0, 1.8), r * rng.uniform(0.9, 1.4), ter(p.x, p.z) + r * 0.45, rng.uniform(-20, 20), "sut", False)
print("bloků s kolizí", nkol, "dílů", len(dily))
for det, suf in ((True, ""),):
    R.seed(1393); H.nastav_detail(det)
    import bpy
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    H.uloz(list(dily.values()), "skaly", kolize=True)
json.dump({"vychozu": len(semena), "semena": [[round(q[0], 1), round(q[1], 1), q[3]] for q in semena]},
          open(os.path.join(K, "hra/data/skaly_body.json"), "w"))
