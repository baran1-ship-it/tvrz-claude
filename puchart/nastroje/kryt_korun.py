"""Krytí korunami (0..1) na mřížce stanoviště (2 m) pro louku v lese – podle Havrana (scripts/louka.gd: „pod korunami
tráva −90 %, mezi korunami (světliny) zůstává“; Míša 4. 11.: „v lese má být řídká, ale ne jak ji máš ty, svahy plné
jako v realitě“). Koruna = kruh o poloměru louka.json les.koruna_k × výška stromu (hra/data/stromy.bin: x, z, výška, druh,
otočení), rozmazáno o les.rozmazani_m. Výstup hra/data/kryt.png (L8, stejná mřížka jako stanoviste.png).
  python3 nastroje/kryt_korun.py <koren>"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
K = sys.argv[1] if len(sys.argv) > 1 else "."
SJ = json.load(open(K + "/hra/data/stanoviste.json")); L = json.load(open(K + "/pravidla/svet/louka.json"))["les"]
st = np.array(Image.open(K + "/hra/data/stanoviste.png")); H, W = st.shape; ks = SJ["krok_m"]
A = np.fromfile(K + "/hra/data/stromy.bin", np.float32).reshape(-1, 5)
kr = np.zeros((H, W), np.float32)
yy, xx = np.mgrid[-4:5, -4:5]
for x, z, h, _d, _r in A:
    r = max(L["koruna_min_m"], L["koruna_k"] * float(h)) / ks
    c = (x - SJ["x0_hra"]) / ks; rr = (z - SJ["z0_hra"]) / ks; ci, ri = int(c), int(rr)
    if not (4 <= ci < W - 4 and 4 <= ri < H - 4): continue
    m = (xx + ci + 0.5 - c) ** 2 + (yy + ri + 0.5 - rr) ** 2 <= r * r
    sub = kr[ri - 4:ri + 5, ci - 4:ci + 5]; sub[m] = 1.0
kr = np.clip(gaussian_filter(kr, L["rozmazani_m"] / ks), 0, 1)
Image.fromarray((kr * 255).astype(np.uint8)).save(K + "/hra/data/kryt.png")
les = np.isin(st, [i for i, t in enumerate(SJ["tridy"]) if t.startswith("les")])
print("krytí korun: stromů %d, v lese průměr %.2f, světlin (krytí < 0,6) %.0f %% lesa" % (len(A), float(kr[les].mean()), 100 * float((kr[les] < 0.6).mean())))
