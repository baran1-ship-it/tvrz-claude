"""Textury vody (Havran reka.gdshader/Waterways: normálová mapa vln + šum pěny), dlaždicové, generované – žádné stažené.
  python3 nastroje/voda_tex.py <koren>  → hra/textury/voda_normal.png (256 px), hra/textury/voda_pena.png (128 px)"""
import os, sys
import numpy as np
from PIL import Image
K = sys.argv[1] if len(sys.argv) > 1 else "."
rng = np.random.default_rng(1393)
def tile_noise(n, okt):   # dlaždicový šum: součet sinusovek s celočíselnými frekvencemi (bez švu)
    y, x = np.mgrid[0:n, 0:n] / n * 2 * np.pi; h = np.zeros((n, n))
    for o in range(okt):
        for _ in range(6):
            fx, fy = rng.integers(1, 3 + 3 * o, 2) * rng.choice([-1, 1], 2); ph = rng.uniform(0, 2 * np.pi)
            h += np.sin(fx * x + fy * y + ph) / (1.6 ** o) / (1 + 0.3 * abs(fy))   # vlny protažené napříč (proud po x)
    return (h - h.min()) / (h.max() - h.min())
h = tile_noise(256, 4)
gy, gx = np.gradient(h); s = 3.5
nx, ny, nz = -gx * 256 / 2 / np.pi * s / 40, -gy * 256 / 2 / np.pi * s / 40, np.ones_like(h)
L = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2); nm = np.stack([nx / L, ny / L, nz / L], -1) * 0.5 + 0.5
os.makedirs(K + "/hra/textury", exist_ok=True)
Image.fromarray((nm * 255).astype(np.uint8)).save(K + "/hra/textury/voda_normal.png")
p = tile_noise(128, 5); Image.fromarray((p * 255).astype(np.uint8)).save(K + "/hra/textury/voda_pena.png")
print("voda_tex: voda_normal.png, voda_pena.png")
# ODRAZ LESA (Hvozd 18. 11., plán D1; Míša 20. 11. H1: „voda není pěkná“): equirect panorama mlhavého smíšeného lesa z Poly Haven
# (CC0, voda_hra.json vzhled_13_11 panorama_*), zmenšená na 2048×1024 – voda.gdshader z ní čte odraz podle odraženého vektoru
import json, urllib.request, io
_VZ = json.load(open(K + "/pravidla/svet/voda_hra.json"))["vzhled_13_11"]
_pf = K + "/hra/textury/" + _VZ["panorama_soubor"]
if not os.path.exists(_pf):
    _r = urllib.request.urlopen(_VZ["panorama_url"], timeout=300).read()
    Image.open(io.BytesIO(_r)).convert("RGB").resize(tuple(_VZ["panorama_px"]), Image.LANCZOS).save(_pf, quality=90)
    print("voda_tex: panorama", _pf)
