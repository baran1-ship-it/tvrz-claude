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
for c in C["cesty"]:
    if c.get("osa") and not c.get("jen_maska"): OSY.setdefault(c["typ"], []).append(hust(np.array(c["osa"])[:, :2]))
KD = {t: cKDTree(np.vstack(v)) for t, v in OSY.items()}
VSE = cKDTree(np.vstack([np.vstack(v) for v in OSY.values()]))
SEG = [(c["id"], hust(np.array(c["osa"])[:, :2])) for c in C["cesty"] if c.get("osa") and not c.get("jen_maska")]
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
def hledej_mlyn(m):
    h = m["hledat"]; ml = m["mlyn"]; best = None
    vel = [t for t in TH.values() if t.get("jmeno") == h["tok"]][0]; osa = np.array(vel["osa"])
    kv = cKDTree(hust(osa[:, :2], 0.5))
    for i in range(2, len(osa) - 2, 2):
        p = osa[i]
        if np.hypot(p[0] - h["u"][0], p[1] - h["u"][1]) > h["r_m"]: continue
        f = osa[i + 2, :2] - osa[i - 2, :2]; f /= np.linalg.norm(f)
        yaw = math.atan2(f[0], f[1])   # +z místa = po proudu (náhon začíná proti proudu)
        for posun_ in np.arange(-6, 6.1, 2.0):
            for odsaz in np.arange(9.0, 15.1, 1.0):
                lx_e, lz_e = ml["lednice_konec"]
                # o + rot(lednice_konec) = bod osy (o posun_ po proudu)
                tx, tz = p[0] + f[0] * posun_, p[1] + f[1] * posun_
                o = {"yaw": yaw}
                ex, ez = rot(yaw, lx_e, lz_e); o["x"] = tx - ex * (odsaz / abs(lx_e)); o["z"] = tz - ez * (odsaz / abs(lx_e))
                xa, xb, za, zb = ml["dvur_aabb"]
                body = [svet(o, a, b) for a in np.linspace(xa, xb, 6) for b in np.linspace(za, zb, 6)]
                hy = [vys(*q) for q in body]; y0 = float(np.median(hy)); pv = max(hy) - min(hy)
                dmin = min(kv.query(q)[0] for q in body)
                if dmin < 5.0: continue
                led = svet(o, *ml["lednice_konec"]); d_led = kv.query(led)[0]
                wl = float(osa[min(range(len(osa)), key=lambda k: (osa[k, 0] - led[0]) ** 2 + (osa[k, 1] - led[1]) ** 2), 2])
                ns = svet(o, *ml["nahon_zacatek"]); hn = vys(*ns)
                dc = d_cesty(o["x"], o["z"], ["vozova"])[0]
                if KS.query([o["x"], o["z"]])[0] < 25: continue
                cena = pv * 0.6 + abs(wl - (y0 + ml["lednice_y"])) * 1.5 + max(0, (y0 + ml["nahon_y"]) - hn) * 0.4 + d_led * 0.3 + max(0, dc - 25) * 0.05
                if best is None or cena < best[0]: best = (cena, o["x"], o["z"], yaw, y0, pv, wl, hn, dc)
    return best


# ------------------------------------------------------------------ místa
hotova = {}
for m in Z["mista"]:
    if m["hledat"].get("mlyn"):
        b = hledej_mlyn(m)
        if b is None: print("ZAJIMAVA_MISTO %s NENALEZENO" % m["id"]); continue
        o = {"x": b[1], "z": b[2], "yaw": b[3]}
        print("ZAJIMAVA_MISTO mlyn [%.1f, %.1f] yaw %.0f°, dvůr y %.2f (převýšení %.2f), hladina u lednice %.2f, terén u náhonu %.2f, cesta %.0f m, cena %.2f" % (b[1], b[2], math.degrees(b[3]), b[4], b[5], b[6], b[7], b[8], b[0]))
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
            VIKA.append({"misto": m["id"] + "_otvor", "poly": poly_svet(o, -1.8, 1.8, -3.7, -0.25), "y_min": round(y0 + t["strop_m"], 3), "viditelne": True})
            KRYTE.append({"misto": m["id"], "poly": poly_svet(o, -4.6, 4.5, -1.6, 0.6)})
            zaz["stola"] = {"zarez_m": round(L, 2), "kryt_m": m["hledat"]["kryt_m"], "y0": round(y0, 3)}
            PUD.append(poly_svet(o, -w - 2, w + 2, -1, L + 3))
            c0 = svet(o, 0, L + 6); tr += [[*c0, None], [*svet(o, 0, 2.5), None], [*svet(o, 0, -6.0), y0, 0.6], [*svet(o, 0, -15.5), y0, 0.6], [*svet(o, 0, -6.0), y0, 0.6], [*svet(o, 0, 2.5), None]]
        elif t["typ"] == "mlyn":
            ml = m["mlyn"]; xa, xb, za, zb = ml["dvur_aabb"]
            y0 = float(np.median([vys(*svet(o, a, b_)) for a in np.linspace(xa, xb, 6) for b_ in np.linspace(za, zb, 6)]))
            plosina(o, xa, xb, za, zb, 4.0, y0)
            # násyp náhonu na kozách (Mlyn_Nahon: od začátku ke kolu) – kozy stojí na zemi
            n0 = np.array(ml["nahon_zacatek"]); n1 = np.array([-1.5, -11.0])
            for s in np.linspace(0, 1, 30):
                q = n0 + (n1 - n0) * s
                for r, c, lx, lz, d in bunky_obdelnik({"x": svet(o, *q)[0], "z": svet(o, *q)[1], "yaw": o["yaw"]}, -1.2, 1.2, -1.2, 1.2, 3.0):
                    cil = y0 + 2.2 - max(d - 0.0, 0) * 0.66
                    if Y[r, c] < cil: nastav(r, c, cil)
            for a in (ml["jama_kola"], ml["lednice_pas"]):   # kanál kola a lednice
                for r, c, lx, lz, d in bunky_obdelnik(o, a[0], a[1], a[2], a[3], 0.0): nastav(r, c, y0 + ml["lednice_y"] - 0.3)
            o["y"] = y0; zaz["mlyn"] = {k_: ml[k_] for k_ in ("vynechat", "kolo_rad_s", "cevnik_nasobek", "lod1_od_m", "dil_do_m", "interier_do_m")}
            PUD.append(poly_svet(o, xa - 1, xb + 1, za - 1, zb + 1)); PUD.append(poly_svet(o, -19, -0.5, -26, -10))
            tr += [[*svet(o, xb + 8, 0), None], [*svet(o, xb - 1, 0), None], [*svet(o, 6.0, -6.0), None]]
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
            zj = ZM[d["model"]]; x0, x1, z0, z1 = zj["jama"]; oz = {"x": wx, "z": wz, "yaw": yaw}
            yz = plosina(oz, -2.4, 2.4, -3.0, 3.1, Z["teren"]["prechod_m"])
            if d.get("mimo_zarez"): pass
            ZE = Z["modely"]["zemljanky"]; rz = ZE["jama_kolize_rozsir_m"]
            DIRY.append({"misto": m["id"], "poly": poly_svet(oz, x0, x1, z0, z1)})
            KOL.append({"misto": m["id"], "poly": poly_svet(oz, x0 - rz, x1 + rz, z0 - rz, z1 - 0.05), "y": round(yz + zj["podlaha_y"] - 0.6, 3)})
            q = {"model": d["model"], "x": wx, "y": yz, "z": wz, "yaw": yaw, "zemljanka": True}
            zaz["dily"].append(q); PUD.append(poly_svet(oz, -2.6, 2.6, -3.2, 4.2))
            # trasa: před dveřmi → stupně → podlaha → zpět ven
            n_ = ZE["schody"]["pocet"]; hst = (zj["prah_y"] - zj["podlaha_y"]) / (n_ + 1); dz_ = ZE["schody"]["hloubka_m"]; zd = zj["dvere_z"]
            ven = [*svet(oz, 0, zd + 2.2), None]
            tz = [ven, [*svet(oz, 0, zd + 0.6), None, 0.35]]
            for k_ in range(n_): tz.append([*svet(oz, 0, z1 - (k_ + 0.5) * dz_), round(yz + zj["prah_y"] - (k_ + 1) * hst, 3), 0.3])
            tz.append([*svet(oz, 0, z0 + 1.2), round(yz + zj["podlaha_y"], 3), 0.5])
            for k_ in reversed(range(n_)): tz.append([*svet(oz, 0, z1 - (k_ + 0.5) * dz_), round(yz + zj["prah_y"] - (k_ + 1) * hst, 3), 0.3])
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
        if d.get("model") == "mlyn" or d.get("model") == "stola": q["y"] = o["y"]
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
    if tr: TRASY["zajimava_%s" % m["id"]] = [[round(p[0], 2), round(p[1], 2)] + p[2:] for p in tr]
    zaz["y"] = round(o["y"], 3)
    VYSL.append(zaz)

for k, v in TRASY.items(): TRASY[k] = [[round(float(p[0]), 2), round(float(p[1]), 2)] + list(p[2:]) for p in v]
# ---- výška dílů po všech úpravách terénu (plošina pozdějšího dílu mohla změnit terén pod dřívějším)
for zaz in VYSL:
    for q in zaz["dily"]:
        if "_ly" in q: q["y"] = vys(q["x"], q["z"]) + q.pop("_ly")
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
           "mista": VYSL, "pudorysy": [[[round(a, 2), round(b, 2)] for a, b in p] for p in PUD]},
          open(K + "/hra/data/zajimava_mista.json", "w"), ensure_ascii=False, indent=1)
json.dump({"popis": "trasy průchodu zajímavých míst (nastroje/zajimava_mista.py) – test_pruchod.gd", "trasy": TRASY},
          open(K + "/hra/data/pruchody_zajimava.json", "w"), ensure_ascii=False, indent=1)
print("ZAJIMAVA míst %d, upravených buněk %d, děr %d, snížených kolizí %d, tras %d" % (len(VYSL), len(UPR), len(DIRY), len(KOL), len(TRASY)))
