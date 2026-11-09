"""Skalní podloží Puchartu: souvislá nepravidelná skalní plocha odvozená ze skutečného reliéfu (pravidla/svet/skaly.json).

Princip (kritika 2. 11.: kvádry působily jako beton položený na kopci): skála není objekt na terénu, ale terén sám
v místě skal – výška DMR se v zónách skal rozláme na stupně podle vrstev droby. Stupeň = ceil(výška vrstvy / mocnost)
→ svislá stěna + police; mocnost lavic se mění šumem, vrstvy jsou ukloněné (ČGS ~20° k S). Pukliny (Voronoi buňky
~2 m) jsou zářezy v geometrii a každý blok mezi nimi je mírně posunutý (rozlámaná silueta jako na fotkách skalního
města). Skála je vždy nad terénem (ceil), na okraji zóny se plynule ponoří pod terén – vystupuje z kopce. Průměrná výška
odpovídá DMR (+ polovina stupně). Mech na policích (normála nahoru), šedá droba na stěnách. Malé úlomky suti pod skalou.
Výstup: hra/modely/hrady/skaly.glb (díly po 50 m, KOLIZE z hrubší sítě) a hra/data/skaly_body.json (podklad terénu).
  /opt/bl/bin/python blender/skaly.py <koren_puchartu>
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrady as H
from hrady import Part, M, R, ter, UP, Vector, Matrix
import numpy as np
from scipy.ndimage import gaussian_filter, distance_transform_edt, map_coordinates
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(H.K, "nastroje"))
import hrad_geom

K = H.K
S = json.load(open(os.path.join(K, "pravidla/svet/skaly.json")))
D = json.load(open(os.path.join(K, "pravidla/svet/hrad_puchart.json"))); A, B = D["A"], D["B"]
C = json.load(open(os.path.join(K, "pravidla/svet/cesty_puchart.json")))
P0 = json.load(open(os.path.join(K, "pravidla/svet/svet.json")))["pocatek"]
VY = S["vyloucit"]; rng = np.random.default_rng(1393)
hm = S["mrizka_m"]

# ---------------------------------------------------------------- mřížka a terén
X0, X1, Z0, Z1 = -40.0, 95.0, 0.0, 190.0
xs = np.arange(X0, X1, hm); zs = np.arange(Z0, Z1, hm); XX, ZZ = np.meshgrid(xs, zs)
Y0 = np.vectorize(ter)(XX, ZZ)
gz, gx = np.gradient(gaussian_filter(Y0, 1.0 / hm), hm); SL = np.degrees(np.arctan(np.hypot(gx, gz)))

def dl(pts):
    p = np.array(pts, float); d = np.full(XX.shape, 1e9)
    for a, b in zip(p[:-1], p[1:]):
        ab = b - a; t = np.clip(((XX - a[0]) * ab[0] + (ZZ - a[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
        d = np.minimum(d, np.hypot(XX - (a[0] + ab[0] * t), ZZ - (a[1] + ab[1] * t)))
    return d
def uvn(poly):
    p = np.array(poly, float); ins = np.zeros(XX.shape, bool)
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        ins ^= ((a[1] > ZZ) != (b[1] > ZZ)) & (XX < (b[0] - a[0]) * (ZZ - a[1]) / (b[1] - a[1] + 1e-12) + a[0])
    return ins
def sum2(m):   # hladký šum s měřítkem m metrů, rozsah ~±1
    n = gaussian_filter(rng.standard_normal(XX.shape), m / hm / 2.5); return n / (np.abs(n).max() + 1e-9)

# ---------------------------------------------------------------- zóny skal (síla 0..1)
W = np.zeros(XX.shape)
osa = S["osa_hrebene"]
for z in S["zony"]:
    if z["typ"] == "pas_osy":
        d = dl(osa); zz = (ZZ >= z["od_z"]) & (ZZ <= z["do_z"])
        w = np.clip((d - z["vzdal_m"][0]) / 0.8, 0, 1) * np.clip((z["vzdal_m"][1] - d) / 2.0, 0, 1) * zz
        w *= np.clip((sum2(z["mezery_sum_m"]) - z["mezery_prah"]) * 3, 0, 1)   # mezery mezi skalkami (hlína, suť)
    elif z["typ"] == "obdelnik":
        w = ((XX >= z["x"][0]) & (XX <= z["x"][1]) & (ZZ >= z["z"][0]) & (ZZ <= z["z"][1])) * np.clip((SL - z["sklon_min_deg"]) / 8, 0, 1)
    elif z["typ"] == "zabaged":
        gj = json.load(open(os.path.join(K, z["vrstva"]))); best = None
        for ft in gj["features"]:
            cs = ft["geometry"]["coordinates"]; ring = cs[0] if ft["geometry"]["type"] == "Polygon" else cs[0][0]
            pts = [(c[0] - P0["X"], -(c[1] - P0["Y"])) for c in ring]
            cx = sum(p[0] for p in pts) / len(pts); cz = sum(p[1] for p in pts) / len(pts)
            dd = math.hypot(cx - z["blizko"][0], cz - z["blizko"][1])
            if best is None or dd < best[0]: best = (dd, pts)
        ins = uvn(best[1]); dout = distance_transform_edt(~ins) * hm
        w = np.clip((z["rozsir_m"] - dout) / 2.0, 0, 1) * np.clip((SL - 15) / 10, 0, 1)
    elif z["typ"] == "obvod":
        poly = A["jadro"] if z["hrad"] == "A" else B["hradba"]
        dd = dl(list(poly) + [poly[0]]); out = ~uvn(poly)
        w = out * np.clip((z["vzdal_m"][1] - dd) / 3.0, 0, 1) * np.clip((SL - z["sklon_min_deg"]) / 8, 0, 1)
    W = np.maximum(W, w * z["sila"])

# vyloučení: cesty, mosty, brány, sklep, plošiny, vnitřek hradů (plynulý okraj)
ven = np.full(XX.shape, 1e9)
for c in C["cesty"]: ven = np.minimum(ven, dl(c["osa"]) - VY["cesty_m"])
j = A["jadro"]; ia = A["brana"]["usek"]; a_, b_ = np.array(j[ia], float), np.array(j[ia + 1], float)
CA = (a_ + b_) / 2; dw = (b_ - a_) / np.linalg.norm(b_ - a_); nA = np.array([dw[1], -dw[0]])
if np.dot(nA, CA - np.array(j).mean(0)) < 0: nA = -nA
hb = B["hradba"]; ib = B["brana"]["usek"]; wa, wb = np.array(hb[ib], float), np.array(hb[ib + 1], float)
GB = wa + (wb - wa) / np.linalg.norm(wb - wa) * B["brana"]["stred_m"]
ven = np.minimum(ven, dl([CA, CA + nA * 37]) - VY["mosty_m"])
for g in (CA, CA + nA * A["vnejsi_brana"]["t_m"], GB): ven = np.minimum(ven, np.hypot(XX - g[0], ZZ - g[1]) - VY["brany_m"])
for poly, t in ((A["jadro"], A["kurtina_tloustka"]), (B["hradba"], B["tloustka"])):
    ins = uvn(poly); ven = np.where(ins, -5, np.minimum(ven, dl(list(poly) + [poly[0]]) - t / 2 - VY["hradby_m"] + 0.0 * ins))
for pl in D["teren"]["plosiny"]:
    if "polygon" in pl: ven = np.where(uvn(pl["polygon"]), -5, ven)
gs = hrad_geom.sklep(A)
u = (XX - gs["o"][0]) * gs["du"][0] + (ZZ - gs["o"][1]) * gs["du"][1]; v = (XX - gs["o"][0]) * gs["dv"][0] + (ZZ - gs["o"][1]) * gs["dv"][1]
ven = np.where((u > -VY["sklep_m"]) & (u < gs["Li"] + VY["sklep_m"]) & (v > -VY["sklep_m"]) & (v < gs["Wi"] + VY["sklep_m"] + 1.5), -5, ven)
W *= np.clip(ven / S["okraj_m"], 0, 1)
W = gaussian_filter(W, 0.6 / hm)
_mb = np.array(B["most"]["od"], float); _ab = GB - _mb; _t = np.clip(((XX - _mb[0]) * _ab[0] + (ZZ - _mb[1]) * _ab[1]) / (_ab @ _ab), 0, 1)
_dm = np.hypot(XX - (_mb[0] + _ab[0] * _t), ZZ - (_mb[1] + _ab[1] * _t))
W *= np.clip((_dm - S["most_vytraceni_m"][0]) / S["most_vytraceni_m"][1], 0, 1)   # u mostu se skála vytratí (ne useknutá rovina)
# pod mostem B: strop
mb = np.array(B["most"]["od"], float); ab = GB - mb; t = np.clip(((XX - mb[0]) * ab[0] + (ZZ - mb[1]) * ab[1]) / (ab @ ab), 0, 1)
dmost = np.hypot(XX - (mb[0] + ab[0] * t), ZZ - (mb[1] + ab[1] * t))
strop = np.where(dmost < VY["mosty_m"] + 0.5, B["most"]["nastup_y"] + (B["dolni_y"] - B["most"]["nastup_y"]) * t - VY["pod_mostem_m"], 1e9)

# ---------------------------------------------------------------- skalní plocha: stupně vrstev + pukliny + posun bloků
ST = S["stupne"]; PK = S["pukliny"]
g = np.array(ST["smer_uklonu"], float); g /= np.linalg.norm(g); tg = math.tan(math.radians(ST["uklon_vrstev_deg"]))
plocha = Y0 + (XX * g[0] + ZZ * g[1]) * tg                           # výška vůči ukloněným vrstvám
mocnost = ST["vyska_m"][0] + (ST["vyska_m"][1] - ST["vyska_m"][0]) * (0.5 + 0.5 * sum2(ST["sum_m"]))
# Voronoi bloky
bx = np.arange(X0, X1, PK["rozestup_m"]); bz = np.arange(Z0, Z1, PK["rozestup_m"])
sem = np.array([(x + rng.uniform(0, PK["rozestup_m"]), z + rng.uniform(0, PK["rozestup_m"])) for x in bx for z in bz])
tree = cKDTree(sem); dd, ii = tree.query(np.c_[XX.ravel(), ZZ.ravel()], k=2)
d1 = dd[:, 0].reshape(XX.shape); d2 = dd[:, 1].reshape(XX.shape); bid = ii[:, 0].reshape(XX.shape)
posun = rng.uniform(*PK["posun_bloku_m"], len(sem))[bid]
# velké lomové plochy: Voronoi ~4 m, každý blok vlastní ukloněná rovina (rovné lomy), hluboké pukliny mezi nimi
LO = S["lomy"]
bx2 = np.arange(X0, X1, LO["rozestup_m"]); bz2 = np.arange(Z0, Z1, LO["rozestup_m"])
sem2 = np.array([(x + rng.uniform(0, LO["rozestup_m"]), z + rng.uniform(0, LO["rozestup_m"])) for x in bx2 for z in bz2])
dd2, ii2 = cKDTree(sem2).query(np.c_[XX.ravel(), ZZ.ravel()], k=2)
D1 = dd2[:, 0].reshape(XX.shape); D2 = dd2[:, 1].reshape(XX.shape); big = ii2[:, 0].reshape(XX.shape)
sx_, sz_ = rng.uniform(-1, 1, len(sem2)) * LO["sklon_ploch"], rng.uniform(-1, 1, len(sem2)) * LO["sklon_ploch"]
lom = sx_[big] * (XX - sem2[big, 0]) + sz_[big] * (ZZ - sem2[big, 1])
odstin = rng.uniform(0, 1, len(sem2))[big]
velka_pukl = np.clip(1 - (D2 - D1) / LO["sirka_m"], 0, 1)
faze = rng.uniform(0, 1, len(sem))[bid]                               # každý blok láme vrstvy jinde
k = np.ceil(plocha / mocnost + faze * 0.5) - faze * 0.5
stup = k * mocnost - (XX * g[0] + ZZ * g[1]) * tg                    # zpět do světa: vždy >= Y0
skala = stup + (posun + lom) * W + S["hrbolatost_m"] * sum2(1.2)
puklina = np.clip(1 - (d2 - d1) / PK["sirka_m"], 0, 1)             # blízko hrany Voronoi = puklina
skala = np.maximum(skala, Y0 + 0.05)
# zuby mřížky na hranách stupňů (diagonály čtverců) pryč: lehké vyhlazení 0,3 m, stěny zůstanou strmé (~70°)
skala = np.maximum(gaussian_filter(skala, S["vyhlazeni_m"] / hm), Y0 + 0.05)
skala -= puklina * PK["hloubka_m"] + velka_pukl * LO["hloubka_m"]      # pukliny až po vyhlazení (zůstanou ostré)
SN = S.get("stena")   # strmé stěny: svislé pukliny a vystouplé pilíře (kresba misa_01) – puklina v půdorysu = svislá rýha na stěně
if SN:
    st_ = np.clip((SL - SN["sklon_od_deg"]) / (SN["sklon_do_deg"] - SN["sklon_od_deg"]), 0, 1) * W
    bx3 = np.arange(X0, X1, SN["rozestup_m"]); bz3 = np.arange(Z0, Z1, SN["rozestup_m"])
    sem3 = np.array([(x + rng.uniform(0, SN["rozestup_m"]), z + rng.uniform(0, SN["rozestup_m"])) for x in bx3 for z in bz3])
    dd3, ii3 = cKDTree(sem3).query(np.c_[XX.ravel(), ZZ.ravel()], k=2)
    E1 = dd3[:, 0].reshape(XX.shape); E2 = dd3[:, 1].reshape(XX.shape); p3 = ii3[:, 0].reshape(XX.shape)
    pil = rng.uniform(0, 1, len(sem3))[p3]
    rys = np.clip(1 - (E2 - E1) / 0.5, 0, 1)
    skala += st_ * (pil * SN["posun_bloku_m"] - rys * SN["pukliny_hloubka_m"])
VC = S["vychozy"]   # výchozy různě vysoké, u mostu nižší
fv = VC["vyska_min"] + (1 - VC["vyska_min"]) * (0.5 + 0.5 * sum2(VC["sum_m"]))
fv = np.where(dmost < VC["u_mostu_m"], np.minimum(fv, VC["u_mostu_vyska"]), fv)
skala = Y0 + 0.05 + (skala - Y0 - 0.05) * fv
Yr = Y0 - 0.5 + (skala - Y0 + 0.5) * np.clip(W * 1.6, 0, 1)         # okraj zóny: ponořit pod terén
VR = S.get("vrostle")   # skála vrostlá do hradby (kresba misa_01): podél vnějšího líce vystupuje nepravidelně po zdi
if VR:
    pv = B["hradba"] if VR["hrad"] == "B" else A["jadro"]; tv = B["tloustka"] if VR["hrad"] == "B" else A["kurtina_tloustka"]
    dv = dl(list(pv) + [pv[0]]) - tv / 2; ve = ~uvn(pv)
    nv = sum2(VR["sum_m"]); hv = VR["vyska_m"][0] + (VR["vyska_m"][1] - VR["vyska_m"][0]) * np.clip(nv * 0.7 + 0.5, 0, 1)
    bump = np.where(ve & (nv > VR["prah"]), hv * np.clip(1 - np.maximum(dv, 0) / VR["sirka_m"], 0, 1) ** 0.7, 0)
    bump = np.where(dv < -0.3, 0, bump) - puklina * 0.3
    Yr = np.where(bump > 0.15, np.maximum(Yr, Y0 + bump), Yr); W = np.maximum(W, (bump > 0.15) * 0.6)
Yr = np.minimum(Yr, strop)
aktivni = W > 0.03
print("skalní plocha: buněk %d (%.0f m²), max výška nad DMR %.1f m" % (aktivni.sum(), aktivni.sum() * hm * hm, float((Yr - Y0)[aktivni].max())))

# ---------------------------------------------------------------- síť
parts = {}
def dil(x, z):
    kk = (int((x + 100) // 50), int((z + 100) // 50))
    if kk not in parts: parts[kk] = Part("skaly_%d_%d" % kk); parts[kk].svarit = 45.0   # hladké normály, ostré hrany stupňů (Míša 9. 11.: pixely)
    return parts[kk]
kol_parts = {}
def kol_dil(x, z):   # kolize = stejná síť jako viditelná skála (test pruchod:povrch_kolize: hrubší síť po 2 bodech a bez okrajů – noha se bořila do kamene), po dílech 50 m (Havran: tvar ≤ 15 k troj)
    kk = (int((x + 100) // 50), int((z + 100) // 50))
    if kk not in kol_parts: kol_parts[kk] = Part("KOLIZE_skaly_%d_%d" % kk)
    return kol_parts[kk]
nz, nx = XX.shape; nf = 0
ak = aktivni | np.roll(aktivni, 1, 0) | np.roll(aktivni, 1, 1)
for i in range(nz - 1):
    for jx in range(nx - 1):
        if not (ak[i, jx] or ak[i + 1, jx + 1]): continue
        if max(W[i, jx], W[i + 1, jx], W[i, jx + 1], W[i + 1, jx + 1]) < 0.03: continue
        v = [(xs[jx], Yr[i, jx], zs[i]), (xs[jx + 1], Yr[i, jx + 1], zs[i]), (xs[jx + 1], Yr[i + 1, jx + 1], zs[i + 1]), (xs[jx], Yr[i + 1, jx], zs[i + 1])]
        if max(Yr[i, jx] - Y0[i, jx], Yr[i, jx + 1] - Y0[i, jx + 1], Yr[i + 1, jx + 1] - Y0[i + 1, jx + 1], Yr[i + 1, jx] - Y0[i + 1, jx]) < -0.02: continue   # celý čtverec pod terénem: neviditelný (test smyslu pod_terenem_skaly 5. 11.)
        dy = max(p[1] for p in v) - min(p[1] for p in v)
        rovne = dy < hm * 0.6
        o_ = odstin[i, jx]; B_ = S["barvy"]
        # jen skála a mech na policích (Míša 9. 11.: „minecraft“ – odstíny tm/sv po čtvercích 0,4 m dělaly pixely; odstín nese textura)
        mat = "skala_mech" if rovne and (faze[i, jx] > 0.62) else "skala"
        P = dil(xs[jx], zs[i])   # dva trojúhelníky: každý vlastní projekce textury (čtverec přes hranu stupně se táhl)
        P.mesh([v[0], v[3], v[2]], [(0, 1, 2)], mat); P.mesh([v[0], v[2], v[1]], [(0, 1, 2)], mat); nf += 2
        K_ = kol_dil(xs[jx], zs[i]); K_.mesh([v[0], v[3], v[2]], [(0, 1, 2)], "kolize"); K_.mesh([v[0], v[2], v[1]], [(0, 1, 2)], "kolize")
# ---------------------------------------------------------------- suť: nepravidelné úlomky v pásu pod skalou
SU = S["sut"]; body = []
okraj = (W > SU["pas"][0]) & (W < SU["pas"][1]) & (ven > 0.3)
kand = np.argwhere(okraj); nsut = 0
for kk in rng.permutation(len(kand))[:SU["kusu"]]:
    i, jx = kand[kk]; x, z = xs[jx] + rng.uniform(-0.2, 0.2), zs[i] + rng.uniform(-0.2, 0.2); r = rng.uniform(*SU["velikost_m"])
    yb = ter(x, z); c = Vector((x, yb + r * 0.15, z))
    vs = []
    for a in range(6):     # nízký nepravidelný hranol (deska droby)
        an = a / 6 * 6.283 + rng.uniform(-0.3, 0.3); rr = r * rng.uniform(0.6, 1.0)
        vs.append(c + Vector((math.cos(an) * rr, 0, math.sin(an) * rr)) - UP * r * 0.4)
    top = [p + UP * r * rng.uniform(0.45, 0.7) + Vector((rng.uniform(-.05, .05), 0, rng.uniform(-.05, .05))) for p in vs]
    P = dil(x, z); P.mesh([tuple(p) for p in vs + top], [tuple(range(5, -1, -1)), tuple(range(6, 12))] + [(a, (a + 1) % 6, (a + 1) % 6 + 6, a + 6) for a in range(6)], "sut")
    kol_dil(x, z).mesh([tuple(p) for p in vs + top], [tuple(range(5, -1, -1)), tuple(range(6, 12))] + [(a, (a + 1) % 6, (a + 1) % 6 + 6, a + 6) for a in range(6)], "kolize")   # úlomek má kolizi (procházelo se jím – povrch_kolize)
    nsut += 1
# půdorysy pro podklad terénu (šedá hlína/suť jen u skal)
for i in range(0, nz, 5):
    for jx in range(0, nx, 5):
        if W[i, jx] > 0.25: body.append({"stred": [float(xs[jx]), float(zs[i])], "cela": [0, 0], "delka": 1.0, "typ": "stena"})
print("ploch", nf, "suť", nsut, "dílů", len(parts))

import bpy
R.seed(1393); H.nastav_detail(True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
H.uloz(list(parts.values()) + list(kol_parts.values()), "skaly", kolize=False)
json.dump({"popis": "půdorysy skalní plochy (pro šedý podklad terénu a vyloučení trávy)", "skaly": body},
          open(os.path.join(K, "hra/data/skaly_body.json"), "w"), ensure_ascii=False)
