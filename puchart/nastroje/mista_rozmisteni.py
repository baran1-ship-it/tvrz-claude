"""Stavby nových míst (pravidla/svet/mista.json, Míša 11. 11. schválila polohy): rozmístění domů z Havrana a terén pod nimi.
Pořadí stavby světa: terén → cesty → STAVBY → voda → vegetace (krok po cesty.py, před teren_dlazdice.py).
- ves (typ „ves“): usedlosti podél cesty, která místem vede – dům štítem (+z modelu) do ulice jako ve vsi Havrana
  (svet.gd VES_STARE: „štít do návsi, vstup +x“), rozestup usedlostí rozestup_m, odstup od osy cesty odstup_m;
  jen kde je pod půdorysem malý sklon (max_prevyseni_m) a mimo jiné cesty a toky.
- samota (krčma, hájovna): nejbližší vhodné místo k bodu stred, štít k nejbližší cestě.
Terén: plošina pod podezdívkou (výška = medián terénu pod půdorysem; Havran DUM_MER pod = výška podlahy nad terénem)
s plynulým přechodem prechod_m (žádné schody, žádné kopání půl kopce). Výstup: hra/data/mista_stavby.json (stavby
pro hru, půdorysy pro vegetaci stavby_vegetace.py) a mřížka terénu <out>.npy.
  python3 mista_rozmisteni.py <vstup_prefix> <vystup_prefix> <koren>"""
import sys, json, math, os
import numpy as np
from scipy.ndimage import distance_transform_edt
pre, out, K = sys.argv[1:4]
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json"))
P = json.load(open(K + "/pravidla/svet/svet.json"))["pocatek"]
MI = json.load(open(K + "/pravidla/svet/mista.json")); R = MI["rozmisteni"]
C = json.load(open(K + "/pravidla/svet/cesty_puchart.json"))
V = json.load(open(K + "/pravidla/svet/voda.json"))["toky"]
ny, nx = H.shape; xh0 = M["x0"] - P["X"]; zh0 = -(M["y1"] - P["Y"])
Y = H - P["H"]
def ij(x, z): return int(round(z - zh0)), int(round(x - xh0))
def vys(x, z):
    r, c = ij(x, z); return Y[min(max(r, 0), ny - 1), min(max(c, 0), nx - 1)]
# překážky: osy cest (bez spojek přes brody) a toky
osy = []
for c in C["cesty"]:
    if c.get("osa") and not c.get("jen_maska"): osy.append((c["id"], np.array(c["osa"], float), c["typ"]))
toky = [np.array(t["body"])[:, [0, 2]] for t in V]
def hust(o, k=1.0):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]; s = np.arange(0, d[-1] + 1e-6, k)
    return np.c_[np.interp(s, d, o[:, 0]), np.interp(s, d, o[:, 1])]
CEST = np.vstack([hust(o) for _, o, _ in osy]); TOK = np.vstack([hust(t) for t in toky])
HLAV = np.vstack([hust(o) for _, o, t in osy if t in ("vozova", "hrebenova")])   # ulice: štít k vozové / hřebenové cestě, ne k pěšině
from scipy.spatial import cKDTree
kc = cKDTree(CEST); kt = cKDTree(TOK); kh = cKDTree(HLAV)
PUD = MI["pudorysy"]   # model -> [hw (x), z_b, z_f, pod] podle Havrana DUM_MER

def rohy(x, z, yaw, m, okraj=0.0):
    hw, zb, zf = PUD[m][0] + okraj, PUD[m][1] - okraj, PUD[m][2] + okraj
    cs, sn = math.cos(yaw), math.sin(yaw)
    # model: +x vstup, +z štít; svět: otočení kolem Y o yaw (Godot: x' = x cos + z sin, z' = -x sin + z cos)
    return [[x + px * cs + pz * sn, z - px * sn + pz * cs] for px, pz in ((-hw, zb), (hw, zb), (hw, zf), (-hw, zf))]

def body_pudorysu(x, z, yaw, m, okraj=0.0, krok=1.0):
    hw, zb, zf = PUD[m][0] + okraj, PUD[m][1] - okraj, PUD[m][2] + okraj
    cs, sn = math.cos(yaw), math.sin(yaw); out_ = []
    for px in np.arange(-hw, hw + 1e-6, krok):
        for pz in np.arange(zb, zf + 1e-6, krok): out_.append((x + px * cs + pz * sn, z - px * sn + pz * cs))
    return np.array(out_)

def vhodne(x, z, yaw, m, uz):
    b = body_pudorysu(x, z, yaw, m, R["okraj_m"])
    h = np.array([vys(p[0], p[1]) for p in b])
    if h.max() - h.min() > R["max_prevyseni_m"]: return None
    if kc.query(b)[0].min() < R["od_cesty_m"] or kt.query(b)[0].min() < R["od_toku_m"]: return None
    for s in uz:
        if math.hypot(s["x"] - x, s["z"] - z) < R["mezi_domy_m"]: return None
    return float(np.median(h)), float(h.max() - h.min())

def yaw_k_ceste(x, z):
    d, i = kh.query([x, z]); q = HLAV[i]
    return math.atan2(q[0] - x, q[1] - z)   # +z modelu (štít) míří k cestě

stavby = []
for misto in MI["mista"]:
    if misto.get("stav") not in ("SCHVALENO",) or misto.get("typ") == "mlyn": continue
    sx, sz = misto["stred"]
    if misto.get("typ") == "ves":
        # cesta, která místem vede: nejbližší vozová / hřebenová osa
        nej = min(((np.hypot(*(o - [sx, sz]).T).min(), i_, o) for i_, o, t in osy if t in ("vozova", "hrebenova")), key=lambda a: a[0])
        o = hust(nej[2]); dd = np.hypot(o[:, 0] - sx, o[:, 1] - sz); o = o[dd < misto["dosah_m"]]
        modely = misto["modely"]; k = 0; uz = []
        for i in range(0, len(o) - 2, int(R["rozestup_m"])):
            t = o[min(i + 2, len(o) - 1)] - o[max(i - 2, 0)]; t = t / (np.linalg.norm(t) or 1.0); n_ = np.array([-t[1], t[0]])
            for strana in (1, -1):
                if k >= len(modely): break   # počet usedlostí = seznam modelů místa (mista.json)
                m = modely[k]
                for od in np.arange(R["odstup_m"], R["odstup_m"] + 10.1, 2.0):
                    x, z = o[i] + n_ * strana * od
                    yaw = yaw_k_ceste(x, z); v = vhodne(x, z, yaw, m, uz + stavby)
                    if v: uz.append({"misto": misto["id"], "model": m, "x": round(float(x), 2), "z": round(float(z), 2), "yaw": round(yaw, 4), "y": round(v[0] + PUD[m][3], 3), "teren_y": round(v[0], 3), "prevyseni": round(v[1], 2)}); k += 1; break
        stavby += uz
        print(misto["id"], "usedlostí", len(uz))
    else:
        m = misto["modely"][0]; best = None
        for r_ in np.arange(0, misto.get("dosah_m", 40), 2.0):
            for a in np.linspace(0, 2 * math.pi, max(1, int(2 * math.pi * r_ / 2.0)), endpoint=False):
                x, z = sx + r_ * math.cos(a), sz + r_ * math.sin(a); yaw = yaw_k_ceste(x, z); v = vhodne(x, z, yaw, m, stavby)
                if v: best = {"misto": misto["id"], "model": m, "x": round(x, 2), "z": round(z, 2), "yaw": round(yaw, 4), "y": round(v[0] + PUD[m][3], 3), "teren_y": round(v[0], 3), "prevyseni": round(v[1], 2)}; break
            if best: break
        if best: stavby.append(best); print(misto["id"], "na", best["x"], best["z"], "převýšení", best["prevyseni"])
        else: print("NENALEZENO", misto["id"])

# terén: plošina pod půdorysem (+okraj) ve výšce teren_y, přechod prechod_m do okolí
for s in stavby:
    msk = np.zeros_like(Y, bool); b = body_pudorysu(s["x"], s["z"], s["yaw"], s["model"], R["okraj_m"], 0.5)
    for p in b:
        r, c = ij(*p)
        if 0 <= r < ny and 0 <= c < nx: msk[r, c] = True
    r0, c0 = ij(s["x"], s["z"]); w = 30
    sl = (slice(max(r0 - w, 0), r0 + w), slice(max(c0 - w, 0), c0 + w))
    d = distance_transform_edt(~msk[sl]); a = np.clip(1 - d / R["prechod_m"], 0, 1); a = a * a * (3 - 2 * a)
    Y[sl] = Y[sl] * (1 - a) + s["teren_y"] * a
np.save(out + ".npy", (Y + P["H"]).astype(np.float32)); json.dump(M, open(out + ".json", "w"), ensure_ascii=False, indent=1)
json.dump({"popis": "stavby nových míst (nastroje/mista_rozmisteni.py z pravidla/svet/mista.json) – čte hra (hlavni.gd _mista) a stavby_vegetace.py",
           "modely": MI["modely"], "stavby": stavby,
           "pudorysy": [rohy(s["x"], s["z"], s["yaw"], s["model"], 0.3) for s in stavby]},
          open(K + "/hra/data/mista_stavby.json", "w"), ensure_ascii=False, indent=1)
print("staveb", len(stavby))
