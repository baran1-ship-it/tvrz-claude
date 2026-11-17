"""Zajímavá místa (pravidla/svet/zajimava_mista.json, Míša 15. 11.): kde přesně stojí, úpravy terénu, trasy průchodu.
Pořadí stavby světa: terén → cesty → stavby vsi (mista_rozmisteni.py) → ZAJÍMAVÁ MÍSTA → dlaždice (teren_dlazdice.py).
- poloha: nejlepší bod v okolí hledat.u podle podmínek záznamu (u cesty v pásu od_osy_m, v lese, od staveb, od toku,
  na rovině do max_prevyseni_m v poloměru, sklon svahu, rozcestí, pramen potoka, skála, břeh Veličky u mlýna);
  natočení: +z místa k cestě (k_ceste), po spádu (do_svahu – vstup do svahu je −z), od skály.
- terén (buňky se připíší k _jamy.npz – ostrá hrana, dlaždice je nevyhladí): plošina (medián, přechod), zářez lomu,
  zářez štoly (portál tam, kde je nad chodbou kryt_m skály), plošina mlýna, násyp náhonu, kanál kola a lednice.
- díry ve viditelné síti (jáma zemljanky, ústí štoly) a snížená kolize terénu (jáma, chodba) → build/zajimava_teren.json
  (čte teren_dlazdice.py); víko kolize nad chodbou štoly staví hra (zajimava.gd) z viditelné sítě.
- hra/data/zajimava_mista.json (pro hru: díly s polohou, LOD, funkce, půdorysy pro stavby_vegetace.py) a
  hra/data/pruchody_zajimava.json (trasy průchodu: k místu, do zemljanky po schodech a ven, do štoly k čelbě a ven).
  python3 nastroje/zajimava_mista.py <vstup_prefix> <vystup_prefix> <K>"""
import sys, os, json, math, shutil
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image

pre, out, K = sys.argv[1:4]
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json"))
P = json.load(open(K + "/pravidla/svet/svet.json"))["pocatek"]
Z = json.load(open(K + "/pravidla/svet/zajimava_mista.json")); ZM = json.load(open(K + "/hra/data/zajimava_modely.json"))["modely"]
C = json.load(open(K + "/pravidla/svet/cesty_puchart.json"))
TH = json.load(open(K + "/hra/data/toky_hladina.json"))["toky"]
ny, nx = H.shape; xh0 = M["x0"] - P["X"]; zh0 = -(M["y1"] - P["Y"])
Y0 = H - P["H"]; Y = Y0.copy()
UPR = {}   # (r, c) -> y (úpravy terénu)


def vys(x, z, A=None):
    A = Y if A is None else A
    fr, fc = z - zh0, x - xh0; r0, c0 = int(math.floor(fr)), int(math.floor(fc)); tr, tc = fr - r0, fc - c0
    r0 = min(max(r0, 0), ny - 2); c0 = min(max(c0, 0), nx - 2)
    return float((A[r0, c0] * (1 - tc) + A[r0, c0 + 1] * tc) * (1 - tr) + (A[r0 + 1, c0] * (1 - tc) + A[r0 + 1, c0 + 1] * tc) * tr)


def spad(x, z, b=4.0):   # gradient (do kopce) na základně 2b
    return np.array([vys(x + b, z) - vys(x - b, z), vys(x, z + b) - vys(x, z - b)]) / (2 * b)


def hust(o, k=1.0):
    o = np.asarray(o, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]; s = np.arange(0, d[-1] + 1e-6, k)
    return np.c_[np.interp(s, d, o[:, 0]), np.interp(s, d, o[:, 1])]


OSY = {}
for c in C["cesty"]:   # pěšiny k místům (k_mistu, nastroje/pesiny_k_mistum.py) se při hledání polohy nepočítají – vedou k místu, které se teprve hledá
    if c.get("osa") and not c.get("jen_maska") and not c.get("k_mistu"): OSY.setdefault(c["typ"], []).append(hust(np.array(c["osa"])[:, :2]))
SIRKA = {t: float(v["sirka_m"]) for t, v in C["typy"].items()}   # pás cesty = sirka_m / 2 od osy (test smysl:zajimava_mimo_cest)
K_MISTU = {c["k_mistu"]: c for c in C["cesty"] if c.get("k_mistu") and c.get("osa") and not c.get("propojka")}   # pěšina k_<id>; propojka k místu (chyby.md 388) je druhý přístup
KD = {t: cKDTree(np.vstack(v)) for t, v in OSY.items()}
VSE = cKDTree(np.vstack([np.vstack(v) for v in OSY.values()]))
SEG = [(c["id"], hust(np.array(c["osa"])[:, :2])) for c in C["cesty"] if c.get("osa") and not c.get("jen_maska") and not c.get("k_mistu")]
TOKY = [np.array(t["osa"]) for t in TH.values()]
KT = cKDTree(np.vstack([hust(t[:, :2]) for t in TOKY]))
MS = json.load(open(K + "/hra/data/mista_stavby.json"))
pts = [[s["x"], s["z"]] for s in MS["stavby"]] + [p for q in MS["pudorysy"] for p in q]
pts += [r for q in json.load(open(K + "/hra/data/stavby_clony.json"))["kvadry"] for r in q["rohy"]]
KS = cKDTree(np.array(pts))
STJ = json.load(open(K + "/hra/data/stanoviste.json"))
_sp = K + "/build/stanoviste_pred_stavbami.png"
ST = np.array(Image.open(_sp if os.path.exists(_sp) else K + "/hra/data/stanoviste.png")); ST = ST[..., 0] if ST.ndim == 3 else ST
SKALY = np.array([s["stred"] for s in json.load(open(K + "/hra/data/skaly_body.json"))["skaly"]])


def trida(x, z):
    c = int((x - STJ["x0_hra"]) / STJ["krok_m"]); r = int((z - STJ["z0_hra"]) / STJ["krok_m"])
    return STJ["tridy"][ST[r, c]] if 0 <= r < ST.shape[0] and 0 <= c < ST.shape[1] else "nic"


def d_cesty(x, z, typy=None):
    if typy is None:
        d, i = VSE.query([x, z]); return d, VSE.data[i]
    best = (1e9, None)
    for t in typy:
        if t in KD:
            d, i = KD[t].query([x, z])
            if d < best[0]: best = (d, KD[t].data[i])
    return best


def rot(yaw, lx, lz):   # místní (x, z) → svět (Godot: x' = x cos + z sin, z' = −x sin + z cos)
    c, s = math.cos(yaw), math.sin(yaw); return lx * c + lz * s, -lx * s + lz * c


def svet(o, lx, lz):
    dx, dz = rot(o["yaw"], lx, lz); return o["x"] + dx, o["z"] + dz


def prevyseni(x, z, r):
    v = [vys(x + dx, z + dz) for dx in np.arange(-r, r + 0.1, max(1.0, r / 4)) for dz in np.arange(-r, r + 0.1, max(1.0, r / 4)) if dx * dx + dz * dz <= r * r]
    return max(v) - min(v)


# ------------------------------------------------------------------ úpravy terénu
def bunky_obdelnik(o, x0, x1, z0, z1, okraj=0.0):
    """buňky mřížky v obdélníku místního rámce (+ okraj) → [(r, c, lx, lz, vzdálenost za okrajem obdélníku)]"""
    R_ = max(abs(x0), abs(x1), abs(z0), abs(z1)) + okraj + 2
    cx, cz = o["x"], o["z"]; out = []
    for r in range(int(cz - R_ - zh0), int(cz + R_ - zh0) + 2):
        for c in range(int(cx - R_ - xh0), int(cx + R_ - xh0) + 2):
            if not (0 <= r < ny and 0 <= c < nx): continue
            wx, wz = xh0 + c, zh0 + r; dx, dz = wx - cx, wz - cz
            cs, sn = math.cos(o["yaw"]), math.sin(o["yaw"]); lx = dx * cs - dz * sn; lz = dx * sn + dz * cs
            ex = max(x0 - lx, 0, lx - x1); ez = max(z0 - lz, 0, lz - z1); d = math.hypot(ex, ez)
            if d <= okraj: out.append((r, c, lx, lz, d))
    return out


def nastav(r, c, y):
    UPR[(r, c)] = y; Y[r, c] = y


def plosina(o, x0, x1, z0, z1, prechod, y=None):
    b = bunky_obdelnik(o, x0, x1, z0, z1, prechod)
    if y is None: y = float(np.median([Y[r, c] for r, c, *_ , d in b if d == 0])) if any(d == 0 for *_, d in b) else vys(o["x"], o["z"])
    for r, c, lx, lz, d in b:
        t = min(d / prechod, 1.0) if prechod > 0 else 1.0
        t = t * t * (3 - 2 * t)
        nastav(r, c, y * (1 - t) + Y[r, c] * t)
    return y


def kruh(o, sx, sz, rr, prechod, y=None):
    wx, wz = svet(o, sx, sz); o2 = {"x": wx, "z": wz, "yaw": 0.0}
    b = [(r, c, d) for r, c, lx, lz, _ in bunky_obdelnik(o2, -rr - prechod, rr + prechod, -rr - prechod, rr + prechod) for d in [math.hypot(lx, lz)] if d <= rr + prechod]
    if y is None: y = float(np.median([Y[r, c] for r, c, d in b if d <= rr]))
    for r, c, d in b:
        t = min(max(d - rr, 0) / prechod, 1.0); t = t * t * (3 - 2 * t)
        nastav(r, c, y * (1 - t) + Y[r, c] * t)
    return y


KRYTE = []   # buňky, kde terén zakrývá model (skalní tlama štoly – schod zářez/svah), pro test smysl:teren_shoda
DIRY = []; KOL = []; VIKA = []; TRASY = {}; PUD = []; VYSL = []


def poly_svet(o, x0, x1, z0, z1):
    return [list(svet(o, a, b)) for a, b in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]


# ------------------------------------------------------------------ hledání polohy
def hledej(m, hotova):
    h = m["hledat"]; u = np.array(h["u"], float); rr = h["r_m"]
    kand = []
    if h.get("rozcesti"):   # body, kde se potkají osy dvou různých cest
        jun = []
        for i, (ia, a) in enumerate(SEG):
            ta = cKDTree(a)
            for ib, b in SEG[i + 1:]:
                if ia == ib: continue
                d, j_ = ta.query(b)
                for k in np.where(d < 1.5)[0][::3]: jun.append(b[k])
        jun = [p for p in jun if np.hypot(*(p - u)) < rr]
        for p in jun:
            for a in np.linspace(0, 2 * math.pi, 24, endpoint=False):
                for dd in (3.5, 5.0, 7.0):
                    kand.append((p[0] + dd * math.cos(a), p[1] + dd * math.sin(a), float(np.hypot(*(p - u))) * 0.05))
    elif h.get("pramen"):
        for t in TOKY:
            if t[-1, 2] > t[0, 2]: t = t[::-1]   # pramen = horní konec (vyšší hladina)
            s0 = t[0]
            if not (xh0 + 20 < s0[0] < xh0 + nx - 20 and zh0 + 20 < s0[1] < zh0 + ny - 20): continue   # začátek toku na okraji výseku = přítok zvenku
            if np.hypot(*(s0[:2] - u)) > rr: continue
            f = t[min(6, len(t) - 1), :2] - s0[:2]; f /= np.linalg.norm(f)
            for back in np.arange(-6.0, 1.1, 1.0):
                for side in (-1.0, 0.0, 1.0):
                    kand.append((s0[0] + f[0] * back - f[1] * side, s0[1] + f[1] * back + f[0] * side, abs(back + 3.0) * 0.3 + abs(side) * 0.2, math.atan2(f[0], f[1])))
    elif h.get("skala"):
        for s in SKALY:
            if np.hypot(*(s - u)) > rr: continue
            g = spad(s[0], s[1])
            if np.linalg.norm(g) < 0.5: continue
            dn = -g / np.linalg.norm(g)   # od skály po spádu
            for dd in (2.5, 3.5, 4.5):
                kand.append((s[0] + dn[0] * dd, s[1] + dn[1] * dd, float(np.hypot(*(s - u))) * 0.01 - np.linalg.norm(g) * 2.0, math.atan2(dn[0], dn[1])))
    else:
        for dx in np.arange(-rr, rr + 0.1, 2.0):
            for dz in np.arange(-rr, rr + 0.1, 2.0):
                if dx * dx + dz * dz <= rr * rr: kand.append((u[0] + dx, u[1] + dz, math.hypot(dx, dz) / rr))
    best = None
    for k in kand:
        x, z, sk = k[0], k[1], k[2]
        if not (xh0 + 30 < x < xh0 + nx - 30 and zh0 + 30 < z < zh0 + ny - 30): continue
        if h.get("les") and not trida(x, z).startswith("les"): continue
        dc, cp = d_cesty(x, z, h.get("cesty"))
        if "od_osy_m" in h and not (h["od_osy_m"][0] <= dc <= h["od_osy_m"][1]): continue
        if h.get("cesty") is not None or h.get("rozcesti"):
            if VSE.query([x, z])[0] < min(h.get("od_osy_m", [2.5])[0], 2.5): continue   # ne na jiné cestě
        if KS.query([x, z])[0] < h.get("od_staveb_m", 0): continue
        if VSE.query([x, z])[0] < h.get("od_cest_min_m", 0): continue
        dt = KT.query([x, z])[0]; ot = h.get("od_toku_m")
        if ot is not None and (dt < ot if not isinstance(ot, list) else not (ot[0] <= dt <= ot[1])): continue
        om = h.get("od_mista")
        if om:
            q = hotova.get(om[0])
            if q is None: continue
            d_ = math.hypot(x - q["x"], z - q["z"])
            if not (om[1] <= d_ <= om[2]): continue
        g = spad(x, z); sl = float(np.linalg.norm(g))
        if sl < h.get("sklon_min", -1): continue
        if h.get("stena_min_m"):   # lom: terén do svahu stoupne o stěnu (jinak není co lámat)
            gu = g / max(sl, 1e-6); hl_ = m["teren"][0]["hloubka_m"]
            if min(vys(x + gu[0] * hl_ + gu[1] * s_, z + gu[1] * hl_ - gu[0] * s_) for s_ in (-4, 0, 4)) - vys(x, z) < h["stena_min_m"]: continue
        pv = prevyseni(x, z, h.get("polomer_m", 1.0))
        if pv > h.get("max_prevyseni_m", 99): continue
        if h.get("kryt_m"):   # štola: portál, nad chodbou kryt
            ok = stola_ok(x, z, g, m)
            if ok is None: continue
            sk += ok["cena"]
        skore = sk + pv * 0.3
        if best is None or skore < best[0]:
            yaw = k[3] if len(k) > 3 else None
            if yaw is None:
                if h.get("do_svahu") or h.get("zady_do_svahu"):
                    yaw = math.atan2(-g[0], -g[1])
                elif h.get("k_ceste") or "od_osy_m" in h and cp is not None:
                    yaw = math.atan2(cp[0] - x, cp[1] - z)
                else: yaw = 0.0
            best = (skore, x, z, yaw, dc, pv, sl)
    return best


def stola_ok(x, z, g, m):
    """portál v (x, z): y0 = terén − kryt; zářez po spádu, dokud terén neklesne pod y0 (≤ zarez_max_m); nad chodbou kryt"""
    h = m["hledat"]; T = m["teren"][0]; dn = -g / max(np.linalg.norm(g), 1e-6); y0 = vys(x, z) - h["kryt_m"]
    L = None
    for s in np.arange(0.5, T["zarez_max_m"] + 0.01, 0.5):
        if vys(x + dn[0] * s, z + dn[1] * s) <= y0 + 0.2: L = s; break
    if L is None: return None
    dl = Z["modely"]["stola"]["delka_m"]
    for s in np.arange(1.5, dl + 0.6, 1.0):
        for side in (-1.6, 0, 1.6):
            px = x - dn[0] * s - dn[1] * side; pz = z - dn[1] * s + dn[0] * side
            if vys(px, pz) < y0 + 3.4: return None
    return {"y0": y0, "L": L, "cena": L * 0.08}


# ------------------------------------------------------------------ mlýn na Veličce
def _zabor_body(o, obdelniky, n=8):
    return [svet(o, a, b) for (x0, x1, z0, z1) in obdelniky for a in np.linspace(x0, x1, n) for b in np.linspace(z0, z1, n)]


def od_pasu_cest(body):
    """nejmenší vzdálenost bodů od kraje pásu kterékoli cesty (osa − sirka_m / 2); záporná = v cestě"""
    return min(float(KD[t].query(body)[0].min()) - SIRKA.get(t, 2.0) / 2 for t in KD)


def hledej_mlyn(m):
    """Míša 16. 11.: mlýn přímo na břehu Veličky, kolo na spodní vodu v proudu (bez náhonu a odtoku), mimo cestu.
    Osa kola (mlyn.kolo) kolo_od_osy_m od osy toku k vlastnímu břehu, podlaha z hladiny (ponor lopatek), +z místa po proudu
    nebo proti proudu (mlýn na jednom či druhém břehu – směr otáčení kola podle toho). Zábor (budova, dvůr, cesta modelu)
    mimo pás cest (od_cest_m), mimo koryto Veličky i jiné toky, do max_vyrovnani_m od podlahy, přístup do cesta_max_m od cesty."""
    h = m["hledat"]; ml = m["mlyn"]; best = None
    vel = [t for t in TH.values() if t.get("jmeno") == h["tok"]][0]; osa = np.array(vel["osa"]); sir_t = float(vel["sirka"])
    kv = cKDTree(hust(osa[:, :2], 0.5))
    jine = [np.array(t["osa"]) for t in TH.values() if t is not vel]
    kj = cKDTree(np.vstack([hust(t[:, :2]) for t in jine])) if jine else None
    kx, ky, kz = ml["kolo"]; R = ml["kolo_r_m"]; posun = ml["kolo_od_osy_m"]
    for i in range(2, len(osa) - 2):
        p = osa[i]
        if np.hypot(p[0] - h["u"][0], p[1] - h["u"][1]) > h["r_m"]: continue
        f = osa[i + 2, :2] - osa[i - 2, :2]; f /= np.linalg.norm(f)
        for smer in (1, -1):
            yaw = math.atan2(f[0] * smer, f[1] * smer)
            o = {"yaw": yaw, "x": 0.0, "z": 0.0}
            bx, bz = svet(o, kx - posun, kz)   # osa toku = kolo posunuté o kolo_od_osy_m dál od budovy (−x)
            o["x"] = p[0] - bx; o["z"] = p[1] - bz
            if not (xh0 + 40 < o["x"] < xh0 + nx - 40 and zh0 + 40 < o["z"] < zh0 + ny - 40): continue
            wl = float(p[2]); y0 = wl - ml["ponor_m"] - ky + R
            body = _zabor_body(o, ml["zabor"])
            if od_pasu_cest(body) < h["od_cest_m"]: continue
            if float(kv.query(body)[0].min()) < sir_t / 2 - 0.05: continue
            if kj is not None and float(kj.query(body)[0].min()) < h["od_jinych_toku_m"]: continue
            if float(KS.query(body)[0].min()) < h["od_staveb_m"]: continue
            dy = np.array([vys(*q) for q in body]) - y0
            if np.abs(dy).max() > h["max_vyrovnani_m"]: continue
            pr = svet(o, *m["pristup"]["bod"]); dc = d_cesty(pr[0], pr[1], m["pristup"]["cesty"])[0]
            if dc > h["cesta_max_m"]: continue
            cena = float(np.abs(dy).mean()) + 0.5 * float(np.abs(dy).max()) + dc * 0.02 + np.hypot(p[0] - h["u"][0], p[1] - h["u"][1]) * 0.002
            if best is None or cena < best[0]: best = (cena, o["x"], o["z"], yaw, y0, float(np.abs(dy).max()), wl, smer, dc, od_pasu_cest(body))
    return best


# ------------------------------------------------------------------ místa
hotova = {}
ODLOZENA = []
for m in Z["mista"]:
    if m.get("odlozeno"):   # Míša 16. 11.: poustevna odložená (záznam zůstává, ve světě není – test pruchod:zajimava_mista)
        ODLOZENA.append(m["id"]); print("ZAJIMAVA_MISTO %s ODLOŽENO (%s)" % (m["id"], m.get("odlozeno_pozn", "")[:60])); continue
    if m["hledat"].get("mlyn"):
        b = hledej_mlyn(m)
        if b is None: print("ZAJIMAVA_MISTO %s NENALEZENO" % m["id"]); continue
        o = {"x": b[1], "z": b[2], "yaw": b[3], "y0": b[4], "smer": b[7]}
        print("ZAJIMAVA_MISTO mlyn [%.1f, %.1f] yaw %.0f°, podlaha y %.2f (vyrovnání do %.2f m), hladina %.2f, %s, přístup %.0f m od cesty, od pásu cest %.1f m, cena %.2f" % (b[1], b[2], math.degrees(b[3]), b[4], b[5], b[6], "po proudu" if b[7] > 0 else "proti proudu", b[8], b[9], b[0]))
    else:
        b = hledej(m, hotova)
        if b is None: print("ZAJIMAVA_MISTO %s NENALEZENO" % m["id"]); continue
        o = {"x": b[1], "z": b[2], "yaw": b[3]}
        print("ZAJIMAVA_MISTO %s [%.1f, %.1f] yaw %.0f°, od cesty %.1f m, převýšení %.2f, sklon %.2f" % (m["id"], b[1], b[2], math.degrees(b[3]), b[4], b[5], b[6]))
    hotova[m["id"]] = o
    o["y"] = vys(o["x"], o["z"])
    zaz = {"id": m["id"], "nazev": m["nazev"], "znacka": m["znacka"], "zdroj": m["zdroj"], "x": round(o["x"], 3), "z": round(o["z"], 3), "yaw": round(o["yaw"], 5), "dily": []}
    tr = []   # trasa průchodu
    # ---- terén
    for t in m.get("teren", []):
        if t["typ"] == "plosina" and "obdelnik" not in t:
            kruh(o, t["stred"][0], t["stred"][1], t["r_m"], Z["teren"]["prechod_m"])
        elif t["typ"] == "zarez":   # lom: dno ve výšce počátku, zadní stěna hloubka_m do svahu (−z)
            y0 = o["y"]; w = t["sirka_m"] / 2
            for r, c, lx, lz, d in bunky_obdelnik(o, -w, w, -t["hloubka_m"], 0.0, Z["teren"]["prechod_m"]):
                if d == 0: nastav(r, c, min(Y[r, c], y0))   # dno lomu (jen snížení – před lomem terén klesá po spádu)
                elif lz > -t["hloubka_m"] and abs(lx) > w: nastav(r, c, max(y0, min(Y[r, c], y0 + (abs(lx) - w) * 2.5)))
            zaz["zarez"] = {"stena_y": round(vys(*svet(o, 0, -t["hloubka_m"] - 1.5), Y0) - y0, 2)}
            PUD.append(poly_svet(o, -w - 1, w + 1, -t["hloubka_m"] - 1, 4))
        elif t["typ"] == "stola":
            T_SV = t.get("svah_boku", 0.7)
            g = spad(o["x"], o["z"]); so = stola_ok(o["x"], o["z"], g, m); y0 = so["y0"]; L = so["L"]; w = t["sirka_m"] / 2
            for r, c, lx, lz, d in bunky_obdelnik(o, -w, w, -0.5, L + 1.5, 6.0):
                if d == 0: nastav(r, c, min(Y[r, c], y0) if lz > L else y0)
                elif lz > -0.5 and abs(lx) > w: nastav(r, c, min(Y[r, c], max(y0, y0 + (abs(lx) - w) * T_SV)))
            o["y"] = y0
            cw = t["chodba_sirka_m"] / 2; dl = Z["modely"]["stola"]["delka_m"] + 0.6
            DIRY.append({"misto": m["id"], "poly": poly_svet(o, -1.75, 1.75, -3.6, -0.3)})
            KOL.append({"misto": m["id"], "poly": poly_svet(o, -cw, cw, -dl, -0.3), "y": round(y0 - 1.5, 3)})
            VIKA.append({"misto": m["id"], "poly": poly_svet(o, -cw - 0.6, cw + 0.6, -dl, -3.6), "od_z": -3.6})
            # viditelná záplata nad otvorem: síť terénu, ale ne níž než strop chodby (snímek 16. 11. f_stola: otvorem nad tlamou bylo vidět nebe)
            # i víko kolize (chyby.md 389, mřížka dosahu 17. 11.): nad ústím je otvor viditelné sítě (DIRY) i snížená kolize (KOL),
            # bez víka hráč z trávy záplaty propadl na strop výdřevy (−3,4) do dutiny pod víkem chodby a zpět nevylezl
            VIKA.append({"misto": m["id"] + "_otvor", "poly": poly_svet(o, -1.8, 1.8, -3.7, -0.25), "y_min": round(y0 + t["strop_m"], 3), "viditelne": True, "kolize": True})
            KRYTE.append({"misto": m["id"], "poly": poly_svet(o, -4.6, 4.5, -1.6, 0.6)})
            zaz["stola"] = {"zarez_m": round(L, 2), "kryt_m": m["hledat"]["kryt_m"], "y0": round(y0, 3)}
            PUD.append(poly_svet(o, -w - 2, w + 2, -1, L + 3))
            c0 = svet(o, 0, L + 6); tr += [[*c0, None], [*svet(o, 0, 2.5), None], [*svet(o, 0, -6.0), y0, 0.6], [*svet(o, 0, -15.5), y0, 0.6], [*svet(o, 0, -6.0), y0, 0.6], [*svet(o, 0, 2.5), None]]
        elif t["typ"] == "mlyn":   # plošina záboru ve výšce podlahy (koryto toku a pás cest zůstanou), kolo stojí v proudu
            ml = m["mlyn"]; y0 = o["y0"]; KO_ = json.load(open(K + "/pravidla/svet/voda_hra.json"))["koryto"]
            vel = [t_ for t_ in TH.values() if t_.get("jmeno") == m["hledat"]["tok"]][0]; kv = cKDTree(hust(np.array(vel["osa"])[:, :2], 0.5))
            breh = float(vel["sirka"]) / 2 + float(KO_["prah_m"]); pr_ = Z["teren"]["prechod_m"] + 1.0
            bun = {}
            for (x0, x1, z0, z1) in ml["zabor"]:
                for r, c, lx, lz, d in bunky_obdelnik(o, x0, x1, z0, z1, pr_):
                    if (r, c) not in bun or d < bun[(r, c)]: bun[(r, c)] = d
            for (r, c), d in bun.items():
                wx, wz = xh0 + c, zh0 + r
                if od_pasu_cest([[wx, wz]]) < 1.0: continue   # cesta (dřívější krok) zůstane
                t_ = min(d / pr_, 1.0); t_ = t_ * t_ * (3 - 2 * t_); cil = y0 * (1 - t_) + Y[r, c] * t_
                nastav(r, c, min(Y[r, c], cil) if kv.query([wx, wz])[0] < breh else cil)
            o["y"] = y0
            zaz["mlyn"] = {k_: ml[k_] for k_ in ("vynechat", "kolo_rad_s", "cevnik_nasobek", "lod1_od_m", "dil_do_m", "interier_do_m", "zastavit", "ovladani")}
            zaz["mlyn"]["smer"] = o["smer"]
            for (x0, x1, z0, z1) in ml["zabor"]: PUD.append(poly_svet(o, x0 - 1, x1 + 1, z0 - 1, z1 + 1))
            if ml.get("bez_porostu_kolo"): PUD.append(poly_svet(o, *ml["bez_porostu_kolo"]))
            bx_, bz_ = m["pristup"]["bod"]
            tr += [[*svet(o, bx_, bz_), None], [*svet(o, 6.8, -9.0), None], [*svet(o, 6.0, -4.0), None], [*svet(o, 4.3, 0.2), None]]
    # ---- díly
    for di in m["dily"]:
        d = dict(di); lx, ly, lz = d.get("poloha", [0, 0, 0]); yaw = o["yaw"] + math.radians(d.get("yaw_st", 0))
        if d.get("v_zemljance") or d.get("pred_dvermi_m") is not None:
            zm = next(q for q in zaz["dily"] if q.get("zemljanka"))
            if d.get("v_zemljance"):
                bx, by, bz = ZM[zm["model"]]["bedna"]; wx, wz = rot(zm["yaw"], bx, bz)
                zaz["dily"].append({"predmet": d["predmet"], "x": zm["x"] + wx, "y": zm["y"] + by, "z": zm["z"] + wz, "yaw": zm["yaw"]})
            else:
                wx, wz = rot(zm["yaw"], d.get("bokem_m", 0.0), ZM[zm["model"]]["dvere_z"] + d["pred_dvermi_m"]); px, pz = zm["x"] + wx, zm["z"] + wz
                zaz["dily"].append({"predmet": d["predmet"], "x": px, "y": vys(px, pz), "z": pz, "yaw": zm["yaw"], "efekt": d.get("efekt")})
            continue
        wx, wz = svet(o, lx, lz)
        if d.get("k_bodu"):
            tx, tz = svet(o, *d["k_bodu"]); yaw = math.atan2(tx - wx, tz - wz)
        if d.get("zemljanka"):
            zj = ZM[d["model"]]; x0, x1, z0, z1 = zj["jama"]
            # otvor jámy musí ležet celý v jedné dlaždici terénu (teren_dlazdice.py dira: přes hranici dlaždic se otvor nevyřízne –
            # snímek 16. 11. zemljanka u lomu: v jámě tráva) → posunout po místní ose x o nejméně
            DL = float(json.load(open(K + "/pravidla/svet/teren.json"))["dlazdice_m"])
            def _u_hranice(px, pz):
                return any(min((v - o_) % DL, DL - (v - o_) % DL) < 9.0 for v, o_ in ((px, xh0), (pz, zh0)))
            for sx, sz in sorted(((a_, b_) for a_ in range(-12, 13) for b_ in range(-12, 13)), key=lambda q: q[0] ** 2 + q[1] ** 2):
                px, pz = svet(o, lx + sx, lz + sz)
                if not _u_hranice(px, pz): wx, wz = px, pz; break
            oz = {"x": wx, "z": wz, "yaw": yaw}
            yz = plosina(oz, -2.4, 2.4, -3.0, 3.1, Z["teren"]["prechod_m"])
            if d.get("mimo_zarez"): pass
            ZE = Z["modely"]["zemljanky"]; rz = ZE["jama_kolize_rozsir_m"]
            ZZ = Z["modely"]["zemljanky"]["zem"]; ps_ = zj.get("pod_strechou") or [x0, x1, z0, z1]; od_ = ZZ["otvor_dovnitr_m"]
            DIRY.append({"misto": m["id"], "poly": poly_svet(oz, ps_[0] + od_, ps_[1] - od_, ps_[2] + od_, ps_[3] - od_), "zemljanka": True})   # celý půdorys pod střechou (Míša 16. 11.: tráva v zemljance)
            KOL.append({"misto": m["id"], "poly": poly_svet(oz, x0 - rz, x1 + rz, z0 - rz, z1 - 0.05), "y": round(yz + zj["podlaha_y"] - 0.6, 3)})
            q = {"model": d["model"], "x": wx, "y": yz, "z": wz, "yaw": yaw, "zemljanka": True}
            po_ = ZZ["porost_okraj_m"]; zaz["dily"].append(q); PUD.append(poly_svet(oz, min(-2.6, ps_[0] - po_), max(2.6, ps_[1] + po_), min(-3.2, ps_[2] - po_), max(4.2, ps_[3] + po_)))
            # trasa: před dveřmi → stupně → podlaha → zpět ven
            n_ = zj.get("schody_pocet", ZE["schody"]["pocet"]); hst = (zj["prah_y"] - zj["podlaha_y"]) / (n_ + 1); dz_ = ZE["schody"]["hloubka_m"]; zd = zj["dvere_z"]
            ven = [*svet(oz, 0, zd + 2.2), None]
            tz = [ven, [*svet(oz, 0, zd + 0.6), None, 0.35]]
            prah_ = [[*svet(oz, 0, zd), round(yz + zj["prah_y"], 3), 0.3]] if zj["prah_y"] > 0.2 else []   # kamenný práh pod dveřmi (zajimava_mista.json podezdivka_stitu)
            tz += prah_
            for k_ in range(n_): tz.append([*svet(oz, 0, z1 - (k_ + 0.5) * dz_), round(yz + zj["prah_y"] - (k_ + 1) * hst, 3), 0.3])
            tz.append([*svet(oz, 0, z0 + 1.2), round(yz + zj["podlaha_y"], 3), 0.5])
            for k_ in reversed(range(n_)): tz.append([*svet(oz, 0, z1 - (k_ + 0.5) * dz_), round(yz + zj["prah_y"] - (k_ + 1) * hst, 3), 0.3])
            tz += prah_
            tz.append(ven)
            TRASY["zajimava_%s_zemljanka" % m["id"]] = tz
            continue
        q = {"x": wx, "z": wz, "yaw": yaw}
        for k_ in ("model", "predmet", "strom", "balvan", "scena", "efekt", "funkce", "meritko", "lod1_do_m"):
            if k_ in d: q[k_] = d[k_]
        if d.get("brt"):
            q["brt"] = dict(d["brt"]); kr = ZM.get("strom_" + d["strom"], {}).get("kmen_r", {})
            hb = d["brt"]["vyska_m"]; kk = min(kr, key=lambda s: abs(float(s) - hb)) if kr else None
            q["brt"]["kmen_r"] = kr[kk] if kk else 0.5
        if d.get("u_steny"): q["y"] = o["y"] - 0.15; q["u_steny"] = True   # kámen opřený o stěnu lomu: na dno, ne na hranu stěny
        elif d.get("model") == "mlyn" or d.get("model") == "stola": q["y"] = o["y"]
        else: q["y"] = vys(wx, wz) + ly; q["_ly"] = ly
        zaz["dily"].append(q)
    # půdorys bez porostu (stavby_vegetace.py) a trasa od cesty k místu
    rp = {"uhlir": 13.0, "smolarna": 5.0, "studanka": 3.5, "poustevna": 3.5, "brte": 2.0}.get(m["id"], 1.6)
    if m["id"] == "brte":
        for q in zaz["dily"]: PUD.append([[q["x"] + 2.0 * math.cos(a), q["z"] + 2.0 * math.sin(a)] for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)])
    elif m["id"] not in ("lom", "stola", "mlyn"):
        PUD.append([[o["x"] + rp * math.cos(a), o["z"] + rp * math.sin(a)] for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)])
    dc, cp = d_cesty(o["x"], o["z"], m["hledat"].get("cesty"))
    if cp is not None and not tr:
        dvec = np.array([o["x"], o["z"]]) - cp; dl_ = np.linalg.norm(dvec)
        if dl_ > 0.1:
            cil = np.array([o["x"], o["z"]]) - dvec / dl_ * (rp + 1.2)
            tr = [[float(cp[0]), float(cp[1]), None], [float(cil[0]), float(cil[1]), None]]
    if m["id"] == "lom":
        tr = [[float(cp[0]), float(cp[1]), None], [*svet(o, 0, 4), None], [*svet(o, 0, -4.0), None]]
    for jm_, body_ in m.get("mlyn", {}).get("trasy_mistni", {}).items():   # trasy dovnitř stavby (Míša 17. 11.: do mlýna se nedá dostat)
        if jm_ == "pozn": continue
        TRASY["zajimava_%s_%s" % (m["id"], jm_)] = [[*svet(o, b_[0], b_[1]), None if b_[2] is None else round(o["y"] + b_[2], 3)] + list(b_[3:]) for b_ in body_]
    if m.get("pristup"):   # přístup od cesty (Míša 16. 11.): bod, ke kterému vede pěšina k_<id> (nastroje/pesiny_k_mistum.py → cesty_puchart.json)
        pb = svet(o, *m["pristup"]["bod"]); zaz["pristup"] = {"bod": [round(pb[0], 2), round(pb[1], 2)], "cesty": m["pristup"]["cesty"]}
        kc = K_MISTU.get(m["id"])
        if kc is None: print("ZAJIMAVA_POZOR %s: pěšina k místu chybí v cesty_puchart.json (python3 nastroje/pesiny_k_mistum.py)" % m["id"])
        else:
            ko = np.array(kc["osa"], float)[:, :2]; dk = float(np.hypot(*(ko[-1] - np.array(pb))))
            if dk > 3.0: print("ZAJIMAVA_POZOR %s: pěšina k místu končí %.1f m od přístupu (místo se posunulo – python3 nastroje/pesiny_k_mistum.py)" % (m["id"], dk))
            hk = hust(ko, 6.0)   # trasa průchodu po pěšině od cesty k místu (test pruchod:zajimava_<id>_pesina)
            TRASY["zajimava_%s_pesina" % m["id"]] = [[float(a_), float(b_), None] for a_, b_ in hk[1:]] + [[float(ko[-1][0]), float(ko[-1][1]), None]]
            TRASY["zajimava_%s_pesina" % m["id"]].insert(0, [float(ko[0][0]), float(ko[0][1]), None])
    if tr: TRASY["zajimava_%s" % m["id"]] = [[round(p[0], 2), round(p[1], 2)] + p[2:] for p in tr]
    zaz["y"] = round(o["y"], 3)
    VYSL.append(zaz)

for k, v in TRASY.items(): TRASY[k] = [[round(float(p[0]), 2), round(float(p[1]), 2)] + list(p[2:]) for p in v]
# ---- výška dílů po všech úpravách terénu (plošina pozdějšího dílu mohla změnit terén pod dřívějším)
for zaz in VYSL:
    for q in zaz["dily"]:
        if "_ly" in q: q["y"] = vys(q["x"], q["z"]) + q.pop("_ly")
# ---- zábor dílů na zemi (obdélníky v půdorysu) – test smysl:zajimava_mimo_cest: nic z místa nezasahuje do pásu cesty
_KATP = K + "/hra/modely/predmety_h.json"; KAT_ = json.load(open(_KATP)) if os.path.exists(_KATP) else {}
def zabor_dilu(q, m_):
    s_ = float(q.get("meritko", 1.0)); ob = []
    if q.get("model") == "mlyn": ob = m_["mlyn"]["zabor"]; s_ = 1.0
    elif q.get("model") == "stola":
        (a0, _, b0), (a1, _, b1) = ZM["stola"]["aabb"]; ob = [[a0, a1, -1.0, b1]]   # jen ústí nad zemí (chodba je pod terénem)
    elif q.get("model") in ZM: (a0, _, b0), (a1, _, b1) = ZM[q["model"]]["aabb"]; ob = [[a0, a1, b0, b1]]
    elif "balvan" in q and q["balvan"] in ZM: (a0, _, b0), (a1, _, b1) = ZM[q["balvan"]]["aabb"]; ob = [[a0, a1, b0, b1]]
    elif "predmet" in q and q["predmet"] in KAT_:
        rx, _, rz = KAT_[q["predmet"]].get("rozmer", [0.4, 0.4, 0.4]); ob = [[-rx / 2, rx / 2, -rz / 2, rz / 2]]
    elif "strom" in q: kr = 0.5; ob = [[-kr, kr, -kr, kr]]
    o_ = {"x": q["x"], "z": q["z"], "yaw": q["yaw"]}
    return [[[round(v, 2) for v in svet(o_, a * s_, b * s_)] for a, b in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))] for x0, x1, z0, z1 in ob]
_MZ = {m_["id"]: m_ for m_ in Z["mista"]}
for zaz in VYSL:
    for q in zaz["dily"]:
        zb = zabor_dilu(q, _MZ[zaz["id"]])
        if zb: q["zabor"] = zb
for zaz in VYSL:
    for q in zaz["dily"]:
        for k_ in ("x", "y", "z", "yaw"):
            if k_ in q: q[k_] = round(float(q[k_]), 3 if k_ != "yaw" else 5)

# ------------------------------------------------------------------ výstupy
np.save(out + ".npy", (Y + P["H"]).astype(np.float32)); json.dump(M, open(out + ".json", "w"), ensure_ascii=False, indent=1)
for suf in ("_koryta.npz", "_jamy.npz"):
    if os.path.exists(pre + suf): shutil.copy(pre + suf, out + suf)
# upravené buňky jako plošiny míst (teren_dlazdice.py: bez vyhlazení, kolize = viditelná síť – test teren_shoda)
_pm = dict(np.load(pre + "_plosiny_mista.npz")) if os.path.exists(pre + "_plosiny_mista.npz") else {"r": np.zeros(0, int), "c": np.zeros(0, int)}
if UPR:
    rc = np.array(list(UPR.keys())); stare = {(int(r), int(c)) for r, c in zip(_pm["r"], _pm["c"])}
    nove = np.array([i for i, (r, c) in enumerate(rc) if (int(r), int(c)) not in stare], int)
    if len(nove): _pm["r"] = np.r_[_pm["r"], rc[nove, 0]]; _pm["c"] = np.r_[_pm["c"], rc[nove, 1]]
np.savez(out + "_plosiny_mista.npz", **_pm)
json.dump({"popis": "úpravy terénu zajímavých míst (nastroje/zajimava_mista.py) pro teren_dlazdice.py: diry = otvory ve viditelné síti (jáma zemljanky, ústí štoly), kolize = snížená kolize terénu v mnohoúhelníku na y (jáma, chodba štoly)",
           "diry": DIRY, "kolize": KOL, "kryte": KRYTE}, open(K + "/build/zajimava_teren.json", "w"), ensure_ascii=False, indent=1)
json.dump({"popis": "zajímavá místa pro hru (nastroje/zajimava_mista.py z pravidla/svet/zajimava_mista.json) – hra/scripts/zajimava.gd; pudorysy pro stavby_vegetace.py (bez porostu)",
           "lod_les": Z["modely"]["lod_les"], "zemljanky_lod": Z["modely"]["zemljanky"]["lod"], "stola_lod": Z["modely"]["stola"]["lod"],
           "stola_kahany": ZM.get("stola", {}).get("kahany", []), "funkce": Z["funkce"], "vika": VIKA,
           "mista": VYSL, "odlozena": ODLOZENA, "pudorysy": [[[round(a, 2), round(b, 2)] for a, b in p] for p in PUD]},
          open(K + "/hra/data/zajimava_mista.json", "w"), ensure_ascii=False, indent=1)
json.dump({"popis": "trasy průchodu zajímavých míst (nastroje/zajimava_mista.py) – test_pruchod.gd", "trasy": TRASY},
          open(K + "/hra/data/pruchody_zajimava.json", "w"), ensure_ascii=False, indent=1)
_DL = float(json.load(open(K + "/pravidla/svet/teren.json"))["dlazdice_m"]); _spatne = []
for q in DIRY:   # otvor musí ležet v jedné dlaždici (teren_dlazdice.py dira – jinak se nevyřízne a jámu zakryje tráva)
    xs = [p[0] - xh0 for p in q["poly"]]; zs = [p[1] - zh0 for p in q["poly"]]
    if int((min(xs) - 5) // _DL) != int((max(xs) + 5) // _DL) or int((min(zs) - 5) // _DL) != int((max(zs) + 5) // _DL): _spatne.append(q["misto"])
if _spatne: print("ZAJIMAVA_CHYBA otvor přes hranici dlaždic:", _spatne); sys.exit(1)
print("ZAJIMAVA míst %d, upravených buněk %d, děr %d, snížených kolizí %d, tras %d" % (len(VYSL), len(UPR), len(DIRY), len(KOL), len(TRASY)))
