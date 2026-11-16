"""Pěšiny od nejbližší cesty k zajímavým místům (Míša 16. 11.: „vyšlapaná pěšina od nejbližší cesty ke studánce“; k mlýnu
odbočka z cesty k vratům dvora – „přístupný, cesta vede ke dveřím, ne skrz budovu“). Osa pěšiny se zapíše jako záznam
k_<místo> (typ pesina, k_mistu: <id>) do pravidla/svet/cesty_puchart.json – tvar, zářez, hlína a vegetaci pak dělá
nastroje/cesty.py stejně jako u ostatních pěšin (data, ne záplata). Osa = A* nad terénem 1 m (cena = délka × (1 + k·nadsklon),
koryta toků a stavby jsou drahé – pěšina obchází, potok překročí jen kde musí), začátek na ose nejbližší cesty typu
pristup.cesty, konec v bodě pristup.bod (hra/data/zajimava_mista.json z nastroje/zajimava_mista.py).
Pořadí: zajimava_mista.py (poloha místa) → tento nástroj → cesty.py … → zajimava_mista.py (místo stojí, pěšina vede k němu;
zajimava_mista.py hlásí ZAJIMAVA_POZOR, když se místo posune a pěšina k němu nevede).
  python3 nastroje/pesiny_k_mistum.py <K> <vysek_prefix (build/vysek1m_kor)>"""
import sys, os, json, math, heapq
import numpy as np
from scipy.spatial import cKDTree

K, pre = sys.argv[1], sys.argv[2]
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json"))
P = json.load(open(K + "/pravidla/svet/svet.json"))["pocatek"]
CP = K + "/pravidla/svet/cesty_puchart.json"; C = json.load(open(CP))
Z = json.load(open(K + "/hra/data/zajimava_mista.json"))
PR = json.load(open(K + "/pravidla/svet/zajimava_mista.json"))["pesiny"]
TH = json.load(open(K + "/hra/data/toky_hladina.json"))["toky"]
ny, nx = H.shape; xh0 = M["x0"] - P["X"]; zh0 = -(M["y1"] - P["Y"])


def hust(o, k=1.0):
    o = np.asarray(o, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]; s = np.arange(0, d[-1] + 1e-6, k)
    return np.c_[np.interp(s, d, o[:, 0]), np.interp(s, d, o[:, 1])]


KT = cKDTree(np.vstack([hust(np.array(t["osa"])[:, :2]) for t in TH.values()]))
MS = json.load(open(K + "/hra/data/mista_stavby.json"))
KS = cKDTree(np.array([p for q in MS["pudorysy"] for p in q] + [[s["x"], s["z"]] for s in MS["stavby"]]))
dily = [p for m in Z["mista"] for q in m["dily"] for z in q.get("zabor", []) for p in hust(z + z[:1], 0.5)]
KZ = cKDTree(np.array(dily)) if dily else None
C["cesty"] = [c for c in C["cesty"] if not c.get("k_mistu")]
for m in Z["mista"]:
    pr = m.get("pristup")
    if not pr: continue
    osy = [hust(np.array(c["osa"])[:, :2]) for c in C["cesty"] if c["typ"] in pr["cesty"] and c.get("osa") and not c.get("jen_maska")]
    kd = cKDTree(np.vstack(osy)); cil = np.array(pr["bod"], float)
    _, i = kd.query(cil); st = kd.data[i]
    # A* v okně kolem úsečky začátek–cíl (okraj PR.okno_m)
    ok = PR["okno_m"]; x0 = int(min(st[0], cil[0]) - ok - xh0); x1 = int(max(st[0], cil[0]) + ok - xh0)
    z0 = int(min(st[1], cil[1]) - ok - zh0); z1 = int(max(st[1], cil[1]) + ok - zh0)
    x0, z0 = max(x0, 1), max(z0, 1); x1, z1 = min(x1, nx - 2), min(z1, ny - 2)
    W = np.ones((z1 - z0 + 1, x1 - x0 + 1))   # přirážka buňky: koryto, stavba, díl místa
    gx, gz = np.meshgrid(np.arange(x0, x1 + 1) + xh0, np.arange(z0, z1 + 1) + zh0)
    body = np.c_[gx.ravel(), gz.ravel()]
    W += (KT.query(body)[0] < PR["tok_m"]).reshape(W.shape) * PR["tok_prirazka"]
    W += (KS.query(body)[0] < PR["stavba_m"]).reshape(W.shape) * PR["stavba_prirazka"]
    if KZ is not None: W += (KZ.query(body)[0] < PR["dil_m"]).reshape(W.shape) * PR["dil_prirazka"]
    s = (int(round(st[1] - zh0)) - z0, int(round(st[0] - xh0)) - x0); g = (int(round(cil[1] - zh0)) - z0, int(round(cil[0] - xh0)) - x0)
    Hl = H[z0:z1 + 1, x0:x1 + 1]; dist = {s: 0.0}; prev = {}; q = [(0.0, s)]
    while q:
        d, u = heapq.heappop(q)
        if u == g: break
        if d > dist[u]: continue
        for dj in (-1, 0, 1):
            for di in (-1, 0, 1):
                if not di and not dj: continue
                w = (u[0] + dj, u[1] + di)
                if not (0 <= w[0] < W.shape[0] and 0 <= w[1] < W.shape[1]): continue
                L = math.hypot(di, dj); sl = abs(Hl[w] - Hl[u]) / L
                c_ = d + L * W[w] * (1 + PR["k_sklon"] * max(0.0, sl - PR["sklon_volny"]))
                if c_ < dist.get(w, 1e18): dist[w] = c_; prev[w] = u; heapq.heappush(q, (c_ + math.hypot(w[0] - g[0], w[1] - g[1]), w))
    if g not in prev: print("PESINA %s: cesta nenalezena" % m["id"]); continue
    cesta = [g]
    while cesta[-1] != s: cesta.append(prev[cesta[-1]])
    cesta = np.array([[c_[1] + x0 + xh0, c_[0] + z0 + zh0] for c_ in cesta[::-1]], float)
    cesta[0] = st; cesta[-1] = cil
    # vyhladit (klouzavý průměr, konce drží) a zředit na krok PR.krok_m
    hc = hust(cesta, 1.0)
    if len(hc) > 7:
        k_ = 3; sm = hc.copy()
        for i_ in range(k_, len(hc) - k_): sm[i_] = hc[i_ - k_:i_ + k_ + 1].mean(0)
        hc = sm
    osa = hust(hc, PR["krok_m"]); osa[-1] = cil
    dl = float(np.hypot(*np.diff(osa, axis=0).T).sum())
    C["cesty"].append({"id": "k_" + m["id"], "typ": "pesina", "k_mistu": m["id"],
                       "jistota": "NAVRH (Míša 16. 11.: vyšlapaná pěšina od nejbližší cesty k místu – nastroje/pesiny_k_mistum.py)",
                       "osa": [[round(float(a), 2), round(float(b), 2)] for a, b in osa]})
    print("PESINA k_%s: od cesty [%.1f, %.1f] k [%.1f, %.1f], %.0f m, %d bodů" % (m["id"], st[0], st[1], cil[0], cil[1], dl, len(osa)))
json.dump(C, open(CP, "w"), ensure_ascii=False, indent=1)
