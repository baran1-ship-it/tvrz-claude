"""Zápoj korun (0..1) na mřížce stanoviště (2 m) pro trávu, podrost a lesní půdu – převzato z Havrana (17. 11.,
větev claude/new-session-0dtk58: pravidla/svet/les_podrost.json „trava“, scripts/svet.gd _koruny_stin + zapoj_v + _puda_zapoj):
v lese roste tráva jen tam, kam dopadne světlo (světliny, okraje, paseky, pruh u pěšin); pod zapojenými korunami lesní
půda a řídký podrost.

Zápoj = krytí korunami VŠECH stromů (hra/data/stromy.bin bez hrady_bez_stromu.json, tj. totéž, co kreslí les.gd)
  krytí: každý strom přičte 1 − smoothstep(0,7; 1,05; vzdálenost / poloměr koruny), strop 1 (Havran _koruny_stin);
  poloměr koruny = poloměr koruny modelu (glb hra/modely/stromy, průměr polovin šířky x a z – Havran tools/koruny_rozmery.py)
  × měřítko, jakým ho les.gd postaví (nejbližší varianta podle výšky, star* jen jako střední, meze meritko) – 17. 11. dřív
  koruna_k 0,2 × výška, ale modely mají 0,23–0,6 (buk 0,32–0,35) → koruny 1,6× menší, pod korunami rostla tráva;
× zápoj okolí: krytí 2× rozmazané čtvercem ±okoli_m/2, smoothstep(okoli_od, okoli_do) – samotný strom v louce zápoj nemá;
krytí se před násobením 2× rozmaže čtvercem ±prechod_m/2 (tráva řídne plynule od kraje korun, ne ostrou hranou).
Výstup hra/data/kryt.png (L8 = zápoj, stejná mřížka jako stanoviste.png); čte louka.gd, byliny.gd, zem.gdshader.
  python3 nastroje/kryt_korun.py <koren> [vystup.png]"""
import glob, json, os, struct, sys
import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter
K = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else K + "/hra/data/kryt.png"
SJ = json.load(open(K + "/hra/data/stanoviste.json")); L = json.load(open(K + "/pravidla/svet/louka.json"))["les"]
SM = json.load(open(K + "/hra/data/stromy_modely.json")); SI = json.load(open(K + "/hra/data/stromy.json"))
st = np.array(Image.open(K + "/hra/data/stanoviste.png")); H, W = st.shape; ks = SJ["krok_m"]
A = np.fromfile(K + "/hra/data/stromy.bin", np.float32).reshape(-1, 5)
vyn = json.load(open(K + "/hra/data/hrady_bez_stromu.json"))["obdelniky"] if os.path.exists(K + "/hra/data/hrady_bez_stromu.json") else []


def koruna_glb(f):   # Havran tools/koruny_rozmery.py: poloměr = průměr polovin šířky x a z (akcesory POSITION)
    b = open(f, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; g = json.loads(b[20:20 + n])
    mn, mx = [1e9] * 3, [-1e9] * 3
    for m in g["meshes"]:
        for p in m["primitives"]:
            a = g["accessors"][p["attributes"]["POSITION"]]
            mn = [min(x, y) for x, y in zip(mn, a["min"])]; mx = [max(x, y) for x, y in zip(mx, a["max"])]
    return ((mx[0] - mn[0]) + (mx[2] - mn[2])) / 4.0


R_MOD = {}
for f in glob.glob(K + "/hra/modely/stromy/*.glb"):
    n = os.path.basename(f)[:-4]
    if n.endswith("_daleko") or n.endswith("_lod1"): continue
    R_MOD[n] = koruna_glb(f)
mer = SM["meritko"]; mer_max = max(mer[1], float(SM.get("meritko_max_stare", mer[1])))


def polomer(dr, h):   # les.gd postav(): varianta a měřítko stromu
    model = SM["dreviny"][dr]["model"]; var_h = SM["varianty"][model]
    nej = min((v for v in var_h if not (SM.get("stare_jako_stredni", False) and v.startswith("star"))), key=lambda v: abs(var_h[v] - h))
    sc = min(max(h / var_h[nej], mer[0]), mer_max)
    r = R_MOD.get("%s_%s" % (model, nej))
    return (r if r is not None else L.get("koruna_k", 0.3) * var_h[nej]) * sc


kr = np.zeros((H, W), np.float32)
yy, xx = np.mgrid[-14:15, -14:15]
pol = {}
for x, z, h, d, _r in A:
    if any(o[0] < x < o[2] and o[1] < z < o[3] for o in vyn): continue
    dr = SI["dreviny"][int(d)]; hk = round(float(h), 1)
    if (dr, hk) not in pol: pol[(dr, hk)] = polomer(dr, float(h))
    r = max(pol[(dr, hk)], L.get("koruna_min_m", 1.5)) / ks
    c = (x - SJ["x0_hra"]) / ks; rr = (z - SJ["z0_hra"]) / ks; ci, ri = int(c), int(rr)
    if not (14 <= ci < W - 14 and 14 <= ri < H - 14): continue
    dist = np.sqrt((xx + ci + 0.5 - c) ** 2 + (yy + ri + 0.5 - rr) ** 2) / max(r, 0.25)
    w = 1.0 - np.clip((dist - 0.7) / 0.35, 0, 1) ** 2 * (3 - 2 * np.clip((dist - 0.7) / 0.35, 0, 1))
    sub = kr[ri - 14:ri + 15, ci - 14:ci + 15]; sub += w; np.minimum(sub, 1.0, out=sub)


def box2(a, m):   # Havran _rozmaz_mriz 2× čtvercem ±m/2
    n = max(1, int(round(m / (2.0 * ks)))) * 2 + 1
    return uniform_filter(uniform_filter(a, n, mode="nearest"), n, mode="nearest")


def ss(a, e0, e1):
    t = np.clip((a - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


zap = np.clip(box2(kr, L["prechod_m"]), 0, 1) * ss(box2(kr, L["okoli_m"]), L["okoli_od"], L["okoli_do"])
Image.fromarray((np.clip(zap, 0, 1) * 255).astype(np.uint8)).save(OUT)
les = np.isin(st, [i for i, t in enumerate(SJ["tridy"]) if t.startswith("les")])
print("zápoj korun: stromů %d, koruna/výška medián %.2f, v lese průměr %.2f, pod zápojem (> kryt_do %.1f) %.0f %% lesa, světlo (< kryt_od %.1f) %.0f %% lesa"
      % (len(A), float(np.median([v / max(k[1], 0.1) for k, v in pol.items()])), float(zap[les].mean()), L["kryt_do"], 100 * float((zap[les] > L["kryt_do"]).mean()),
         L["kryt_od"], 100 * float((zap[les] < L["kryt_od"]).mean())))
print("krytí korunami (bez rozmazání): v lese průměr %.2f, kryto > 0,5 %.0f %% lesa" % (float(kr[les].mean()), 100 * float((kr[les] > 0.5).mean())))
