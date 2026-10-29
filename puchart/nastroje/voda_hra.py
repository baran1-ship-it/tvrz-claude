"""Toky z toky.py (S-JTSK, 5 m) -> pravidla/svet/voda.json v souřadnicích hry, jen ve výseku + okraj.

Osa se zjemní: Chaikin (2×), pak posun každého bodu po kolmici na nejnižší místo 1 m mřížky (±8 m),
a dno se srovná, aby nikdy nestoupalo po proudu. OSM jen jméno (PDF kap. 7 krok 3: výšky vody kontrolovat proti terénu).
python3 voda_hra.py <toky_teren.json> <vysek_prefix> <koren>
"""
import sys, json, os
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

src, pre, koren = sys.argv[1:4]
S = json.load(open(os.path.join(koren, "pravidla/svet/svet.json"))); P = S["pocatek"]
H = gaussian_filter(np.load(pre + ".npy").astype(np.float64), 1.5); M = json.load(open(pre + ".json"))
okraj = 100.0
def vyska(x, y):
    return map_coordinates(H, [[M["y1"] - y], [x - M["x0"]]], order=1)[0]
def chaikin(p):
    q = [p[0]]
    for a, b in zip(p[:-1], p[1:]):
        q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
    q.append(p[-1]); return np.array(q)
out = []
for t in json.load(open(src))["toky"]:
    p = np.array(t["body"])[:, :2]
    m = (p[:, 0] > M["x0"] - okraj) & (p[:, 0] < M["x1"] + okraj) & (p[:, 1] > M["y0"] - okraj) & (p[:, 1] < M["y1"] + okraj)
    if m.sum() < 4: continue
    i = np.nonzero(m)[0]; p = p[i[0]:i[-1] + 1]
    for _ in range(2): p = chaikin(p)
    # přichytit k údolnici
    d = np.gradient(p, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    nrm = np.c_[-d[:, 1], d[:, 0]]
    q = []
    for (x, y), n in zip(p, nrm):
        if not (M["x0"] + 9 < x < M["x1"] - 9 and M["y0"] + 9 < y < M["y1"] - 9):
            q.append((x, y)); continue
        s = np.arange(-8, 8.5, 0.5); h = [vyska(x + n[0] * a, y + n[1] * a) for a in s]
        a = s[int(np.argmin(h))]; q.append((x + n[0] * a, y + n[1] * a))
    q = np.array(q)
    q = np.c_[np.convolve(q[:, 0], np.ones(5) / 5, "same"), np.convolve(q[:, 1], np.ones(5) / 5, "same")][2:-2]
    z = np.array([vyska(x, y) for x, y in q]); z = np.minimum.accumulate(z)
    b = [[round(x - P["X"], 2), round(float(zz) - P["H"], 2), round(-(y - P["Y"]), 2)] for (x, y), zz in zip(q, z)]
    out.append({"jmeno": t["jmeno"], "povodi_km2": t["povodi_km2_na_konci"], "body": b})
json.dump({"popis": "Osy toků ve výseku, souřadnice hry [x, y_dna, z]. Odvozeno z terénu (D8 nad DMR 5G, nastroje/toky.py), jména OSM (ODbL). Šířka a hladina zatím NEOVERENO – krok C (koryto jako v Havranovi koryto.gd).",
           "toky": out}, open(os.path.join(koren, "pravidla/svet/voda.json"), "w"), ensure_ascii=False)
for t in out: print(t["jmeno"], len(t["body"]), t["povodi_km2"])
