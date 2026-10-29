"""Stanoviště a stromy pro rok 1393 ze skutečných dat (postup KCD: skutečné místo → historická úprava).

Vstupy (S-JTSK, výsek ze svet.json):
  biotopy.json  – AOPK mapování biotopů (ArcGIS query, polygony)       pravidla: historie_vegetace.json "biotopy"
  ppv.json      – potenciální přirozená vegetace (AOPK)               pravidla: historie_vegetace.json "ppv"
  chm.npy       – výška porostu = DMP 1G − DMR 5G, 1 m (ČÚZK)          polohy a výšky dnešních stromů
  vysek1m.npy   – terén 1 m (sklon pro pole/pastviny)
Výstupy:
  hra/data/stanoviste.png + stanoviste.json  – třída 1393 po 2 m (index → jméno)
  hra/textury/maska_vysek.png                – R louka, G les (opad), B skála, A koryto/břeh (pro zem.gdshader)
  hra/data/stromy.bin + stromy.json          – stromy (x, z, výška, druh, natočení) float32
  docs/screens/02_stanoviste_1393.png        – mapa tříd; 02_stromy_1393.png – stromy
python3 stanoviste_realne.py <pracovni_dir> <koren>
"""
import sys, os, json, re
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, maximum_filter, distance_transform_edt, binary_dilation

W, K = sys.argv[1], sys.argv[2]
S = json.load(open(os.path.join(K, "pravidla/svet/svet.json")))
HV = json.load(open(os.path.join(K, "pravidla/svet/historie_vegetace.json")))
L = {l["id"]: l for l in json.load(open(os.path.join(K, "pravidla/svet/lokace.json")))["hrady"]}
L.update({l["id"]: l for l in json.load(open(os.path.join(K, "pravidla/svet/lokace.json")))["sidla"]})
V = S["vysek"]["sjtsk"]; P = S["pocatek"]
KR = 2.0
n = int((V["x1"] - V["x0"]) / KR)
rng = np.random.default_rng(1393)

def px(x, y):
    return ((x - V["x0"]) / KR, (V["y1"] - y) / KR)

def plocha(r):
    a = np.array(r); return 0.5 * np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1])

def rastr(features, hodnota):
    """Polygony ArcGIS (vnější kruh po směru hodin = záporná plocha v x-y, díry opačně) -> index rastru."""
    im = Image.new("I", (n, n), 0); d = ImageDraw.Draw(im)
    for i, f in enumerate(features):
        v = hodnota(f)
        if v is None: continue
        rings = f["geometry"]["rings"]
        for r in rings:
            if plocha(r) < 0: d.polygon([px(*p) for p in r], fill=v)
        for r in rings:
            if plocha(r) > 0: d.polygon([px(*p) for p in r], fill=0)
    return np.array(im)

# --- třídy 1393 ---
TRIDY = ["nic", "les_bucina", "les_bucina_kysela", "les_sut", "les_dubohabrina", "les_doubrava", "luh", "les_okraj",
         "les_paseka", "skala", "koryto_kamenite", "louka_kosena", "pastvina", "pole", "zemedelstvi", "breh"]
TI = {t: i for i, t in enumerate(TRIDY)}
LES = {TI[t] for t in TRIDY if t.startswith("les_") or t == "luh"}

# PPV
ppv = json.load(open(os.path.join(W, "ppv.json")))["features"]
ppv_nazvy = [f["attributes"]["NAZEV_MJ"] for f in ppv]
R_ppv = rastr(ppv, lambda f: 1 + ppv_nazvy.index(f["attributes"]["NAZEV_MJ"]))
def ppv_cil(i):
    if i == 0: return "les_bucina"
    return HV["ppv"].get(ppv_nazvy[i - 1], {"cil": "les_bucina"})["cil"]

# biotopy: každý segment může být směs „L5.1 (70), X9A (30)“ -> pixel losuje podle podílů (mozaika, ne pravítko)
bio = json.load(open(os.path.join(W, "biotopy.json")))["features"]
R_bio = rastr(bio, lambda f: bio.index(f) + 1)
sum_ = gaussian_filter(rng.random((n, n)), 3); sum_ = (sum_ - sum_.min()) / (sum_.max() - sum_.min())
T = np.zeros((n, n), np.uint8)
druh_mix = {}   # pixel třída -> skladba dřevin
for i, f in enumerate(bio):
    m = R_bio == i + 1
    if not m.any(): continue
    slozky = [(c, int(p)) for c, p in re.findall(r"([A-Z0-9.\-]+) \((\d+)\)", f["attributes"]["BIOTOP_SEZ"] or "-1 (100)")]
    hranice = np.cumsum([p for _, p in slozky]) / 100.0
    for (kod, _), h0, h1 in zip(slozky, np.r_[0, hranice[:-1]], hranice):
        mm = m & (sum_ >= h0) & (sum_ < h1 + (1e-6 if h1 >= 0.999 else 0))
        b = HV["biotopy"].get(kod) or HV["biotopy"].get(kod.split(".")[0]) or {"cil": "PPV"}
        cil = b["cil"]
        if cil == "PPV":
            for pi in np.unique(R_ppv[mm]):
                T[mm & (R_ppv == pi)] = TI[ppv_cil(pi)]
        else:
            T[mm] = TI[cil]

# nezmapováno: dnešní výška porostu rozhodne les / bezlesí (pole na mírném svahu, jinak pastvina)
CHM = np.load(os.path.join(W, "chm.npy"))
Hm = np.load(os.path.join(W, "vysek1m.npy"))[:2000, :2000]
chm2 = CHM.reshape(n, 2, n, 2).mean((1, 3)); h2 = gaussian_filter(Hm, 10).reshape(n, 2, n, 2).mean((1, 3))
gz, gx = np.gradient(h2, KR); sklon = np.hypot(gx, gz)
nez = T == 0
les_dnes = gaussian_filter((chm2 > 3).astype(float), 2) > 0.5
for pi in np.unique(R_ppv):
    T[nez & les_dnes & (R_ppv == pi)] = TI[ppv_cil(pi)]
T[nez & ~les_dnes & (sklon < 0.15)] = TI["pole"]
T[nez & ~les_dnes & (sklon >= 0.15)] = TI["pastvina"]

# zásahy 1393 (historie_vegetace.json zasahy_1393)
yy, xx = np.mgrid[0:n, 0:n]
Xs = V["x0"] + (xx + 0.5) * KR; Ys = V["y1"] - (yy + 0.5) * KR
for z in HV["zasahy_1393"]:
    if "kolem" not in z: continue
    for lid in z["kolem"]:
        l = L[lid]; d = np.hypot(Xs - l["X"], Ys - l["Y"])
        okraj = d < z["r_m"] * (0.85 + 0.3 * sum_)   # nepravidelný okraj
        if z["cil"] == "pastvina":
            T[okraj & ~np.isin(T, [TI["skala"], TI["koryto_kamenite"]])] = TI["pastvina"]
        elif z["cil"] == "zemedelstvi":
            m = okraj & ~np.isin(T, [TI["skala"], TI["koryto_kamenite"], TI["les_sut"]])
            T[m & (sklon < 0.15)] = TI["pole"]
            T[m & (sklon >= 0.15) & (sklon < 0.35)] = TI["louka_kosena"]

# koryto a břeh z os toků (voda.json, souřadnice hry)
voda = json.load(open(os.path.join(K, "pravidla/svet/voda.json")))
tok = np.zeros((n, n), bool)
for t in voda["toky"]:
    for x, y, z in t["body"]:
        c, r = px(x + P["X"], P["Y"] - z)
        if 0 <= r < n and 0 <= c < n: tok[int(r), int(c)] = True
dt = distance_transform_edt(~tok) * KR
T[(dt < 3.0)] = TI["koryto_kamenite"]
T[(dt >= 3.0) & (dt < 7.0) & ~np.isin(T, list(LES) + [TI["skala"]])] = TI["breh"]

os.makedirs(os.path.join(K, "hra/data"), exist_ok=True)
Image.fromarray(T).save(os.path.join(K, "hra/data/stanoviste.png"))
json.dump({"krok_m": KR, "x0_hra": V["x0"] - P["X"], "z0_hra": -(V["y1"] - P["Y"]), "tridy": TRIDY},
          open(os.path.join(K, "hra/data/stanoviste.json"), "w"), ensure_ascii=False, indent=1)

# maska pro shader (zem.gdshader): R louka, G les, B skála, A koryto+břeh – rozmazaná o 2 m, ať hrany nejsou pixelové
def kan(trs): return gaussian_filter(np.isin(T, [TI[t] for t in trs]).astype(float), 1.0)
mR = kan(["louka_kosena", "pastvina", "zemedelstvi", "les_paseka", "pole"])
mG = gaussian_filter(np.isin(T, list(LES - {TI["les_paseka"]})).astype(float), 1.0)
gzj, gxj = np.gradient(gaussian_filter(Hm, 2.5).reshape(n, 2, n, 2).mean((1, 3)), KR)
strm = np.degrees(np.arctan(np.hypot(gxj, gzj)))
mB = np.maximum(kan(["skala"]), np.clip((strm - 38) / 10, 0, 1)) * 1.0
mB = np.maximum(mB, kan(["les_sut"]) * 0.35 * (sum_ > 0.45))   # suťové lesy: balvany prosvítají (L4 poznámky)
mA = kan(["koryto_kamenite", "breh"])
s = mR + mG + mB + mA
mR, mG = mR * (1 - mB) * (1 - mA), mG * (1 - mB) * (1 - mA)
maska = (np.clip(np.stack([mR, mG, mB, mA], -1), 0, 1) * 255).astype(np.uint8)
Image.fromarray(maska, "RGBA").save(os.path.join(K, "hra/textury/maska_vysek.png"))

# --- stromy: polohy a výšky z dnešních korun (lokální maxima CHM), druh podle skladby 1393 ---
chm_s = gaussian_filter(CHM, 1.2)
vrch = (chm_s == maximum_filter(chm_s, size=5)) & (chm_s > 4.0)
r, c = np.nonzero(vrch)
h = chm_s[r, c]
# rozestup podle velikosti koruny (poloměr ~ 0,12 h + 1 m): řídnout od nejvyšších
poradi = np.argsort(-h); obsazeno = np.zeros((2000, 2000), bool); kept = []
for i in poradi:
    rr, cc = r[i], c[i]
    if obsazeno[rr, cc]: continue
    kept.append(i)
    rad = int(0.12 * h[i] + 1.0)
    obsazeno[max(0, rr - rad):rr + rad + 1, max(0, cc - rad):cc + rad + 1] = True
r, c, h = r[kept], c[kept], h[kept]
# DMP 1G je obrazová korelace (hladká) -> maxima najdou jen nejvyšší koruny (~32/ha). Doplnit horní patro do hustoty
# z historie_vegetace.json "hustota_ha" (rozestup podle koruny); výška = okolní porost × 0,55–1,0 (mezi-patro).
hust = HV["hustota_ha"]
T1 = np.repeat(np.repeat(T, 2, 0), 2, 1)
chm_okoli = gaussian_filter(CHM, 6)
dopl = []
for t_jm, ha in hust.items():
    if t_jm.startswith("_"): continue
    m = T1 == TI[t_jm]
    plocha_ha = m.sum() / 1e4
    want = int(plocha_ha * ha * 2.5)   # kandidátů víc, rozestup část odmítne
    rr = rng.integers(0, 2000, want); cc = rng.integers(0, 2000, want)
    ok = m[rr, cc]
    for a, b in zip(rr[ok], cc[ok]):
        if obsazeno[a, b]: continue
        hh = float(max(4.0, chm_okoli[a, b] * rng.uniform(0.55, 1.0)))
        rad = int(0.12 * hh + 1.0)
        obsazeno[max(0, a - rad):a + rad + 1, max(0, b - rad):b + rad + 1] = True
        dopl.append((a, b, hh))
if dopl:
    D_ = np.array(dopl)
    r = np.r_[r, D_[:, 0].astype(int)]; c = np.r_[c, D_[:, 1].astype(int)]; h = np.r_[h, D_[:, 2]]
tr = T[r // 2, c // 2]
DREVA = ["BK", "JD", "SM", "DB", "HB", "KL", "JS", "LP", "OL", "VR", "BR", "BO", "JL", "LS"]
skladba = {}
for kod, b in list(HV["biotopy"].items()) + list(HV["ppv"].items()):
    if "drevy" in b: skladba.setdefault(b["cil"], b["drevy"])
skladba["les_paseka"] = {"BR": 0.4, "VR": 0.3, "BK": 0.2, "JD": 0.1}
# shluky druhů: každý druh má vlastní pomalý šum (stromy rostou ve skupinách, ne jako sůl a pepř)
sumy = {d: gaussian_filter(rng.random((200, 200)), 4) for d in DREVA}
out = []
for rr, cc, hh, t in zip(r, c, h, tr):
    jm = TRIDY[t]
    if t in LES:
        sk = skladba.get(jm, skladba["les_bucina"])
    elif jm in ("pastvina", "louka_kosena", "breh") and rng.random() < (0.04 if jm != "breh" else 0.25):
        sk = {"DB": 0.3, "LP": 0.3, "VR": 0.2, "HB": 0.2} if jm != "breh" else {"OL": 0.6, "VR": 0.4}   # solitéry
    else:
        continue
    w = np.array([sk.get(d, 0) * (0.3 + sumy[d][rr // 10, cc // 10] * 2) for d in DREVA]); w /= w.sum()
    d = rng.choice(len(DREVA), p=w)
    x = V["x0"] + cc + 0.5 - P["X"]; z = -(V["y1"] - rr - 0.5 - P["Y"])
    # 1393: les byl využívaný (pastva, palivo) – staré buky ponechat, výšky dnešních smrkových kultur nepřebírat 1:1
    out.append((x, z, float(min(hh, 38.0)), d, rng.random() * 6.283))
A = np.array(out, np.float32)
A.tofile(os.path.join(K, "hra/data/stromy.bin"))
pocty = {DREVA[i]: int((A[:, 3] == i).sum()) for i in range(len(DREVA))}
json.dump({"pocet": len(A), "z_korun": int(len(kept)), "doplneno": len(dopl), "pole": ["x", "z", "vyska_m", "drevina", "natoceni"], "dreviny": DREVA, "pocty": pocty,
           "zdroj": "polohy a výšky: lokální maxima DMP 1G − DMR 5G (ČÚZK); druh: historie_vegetace.json"},
          open(os.path.join(K, "hra/data/stromy.json"), "w"), ensure_ascii=False, indent=1)

# náhledy
PAL = {"nic": (0, 0, 0), "les_bucina": (40, 110, 40), "les_bucina_kysela": (60, 110, 60), "les_sut": (90, 100, 60),
       "les_dubohabrina": (80, 130, 40), "les_doubrava": (120, 130, 40), "luh": (40, 120, 110), "les_okraj": (110, 150, 70),
       "les_paseka": (160, 170, 90), "skala": (150, 150, 150), "koryto_kamenite": (60, 110, 200), "louka_kosena": (170, 210, 90),
       "pastvina": (200, 210, 120), "pole": (220, 190, 110), "zemedelstvi": (210, 180, 120), "breh": (120, 160, 170)}
img = np.zeros((n, n, 3), np.uint8)
for i, t in enumerate(TRIDY): img[T == i] = PAL[t]
os.makedirs(os.path.join(K, "docs/screens"), exist_ok=True)
Image.fromarray(img).save(os.path.join(K, "docs/screens/02_stanoviste_1393.png"))
BAR = [(30, 120, 30), (20, 70, 40), (10, 60, 20), (150, 120, 20), (110, 150, 40), (200, 120, 40), (220, 220, 90), (180, 200, 60),
       (40, 160, 160), (120, 160, 200), (230, 230, 230), (200, 80, 40), (160, 120, 80), (140, 200, 120)]
st = Image.fromarray((img * 0.35).astype(np.uint8)).resize((2000, 2000), Image.NEAREST); d = ImageDraw.Draw(st)
for x, z, hh, dd, _ in A:
    cc = x + P["X"] - V["x0"]; rr = (V["y1"] - P["Y"]) + z
    rad = 0.12 * hh + 1.0
    d.ellipse([cc - rad, rr - rad, cc + rad, rr + rad], fill=BAR[int(dd)])
st.save(os.path.join(K, "docs/screens/02_stromy_1393.png"))
pod = {t: round(100 * float((T == i).mean()), 1) for i, t in enumerate(TRIDY) if (T == i).any()}
print("třídy %", pod); print("stromů", len(A), pocty)
