"""Plán lokality z Archeologického atlasu (Tomášek a kol. 2015, mřížka UTM 33N v obrázku) -> polygony v S-JTSK.

Barvy plánu: fialová = valy a zdivo, světle šedá = plošiny, černá = dochované zdivo (B, C), bílý obrys = jádro A.
Měřítko z popisků mřížky (693700/693800 E, 5499000/5498900 N): změřeno v pixelech níže.
Výstup: pravidla/svet/hrady_plan.json (DOLOZENO – tvar podle plánu, výšky z DMR) + náhled nad stínovaným DMR.
python3 plan_atlas.py <obrazek_planu> <vysek_prefix> <koren>
"""
import sys, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from pyproj import Transformer

img, pre, K = sys.argv[1:4]
A = np.asarray(Image.open(img).convert("RGB")).astype(int)
# georeference: px x = 52 + (E-693700)*s, px y = 113 + (5499000-N)*s ; s = (377-52)/100
s = (377 - 52) / 100.0
def utm(px, py): return 693700 + (px - 52) / s, 5499000 - (py - 113) / s
t = Transformer.from_crs(32633, 5514, always_xy=True)
r, g, b = A[..., 0], A[..., 1], A[..., 2]
masky = {
    "val_a_zdivo": (r > 110) & (r < 190) & (g < 60) & (b > 100),          # fialová
    "plosina": (abs(r - 221) < 14) & (abs(g - 221) < 14) & (abs(b - 221) < 14),  # světle šedá
    "zdivo_dochovane": (r < 60) & (g < 60) & (b < 60),                       # černá (B, C, popisky)
}
# omezit na oblast hradu (bez legendy, popisků os a značek)
oblast = np.zeros(A.shape[:2], bool); oblast[230:880, 230:720] = True
out = {"popis": "Plán Pustý zámek / Puchart podle Archeologického atlasu (plán: Tomášek a kol. 2015), přepočet UTM 33N -> S-JTSK. Polygony = obrysy barevných ploch plánu. jistota DOLOZENO pro polohu a půdorys valů, příkopů a dochovaného zdiva; výšky staveb NEJSOU v plánu.",
       "zdroj": "https://www.archeologickyatlas.cz/cs/lokace/kyzlirov_pr_hrad_pusty_zamek (Plán lokality)", "vrstvy": {}}
for jm, m in masky.items():
    m = ndimage.binary_opening(m & oblast, iterations=1)
    lab, n = ndimage.label(m)
    polys = []
    for i in range(1, n + 1):
        mm = lab == i
        if mm.sum() < 60: continue
        ys, xs = np.nonzero(mm)
        # obrys: konvexní obal je moc hrubý (valy jsou oblouky) -> obrysové body po řádcích (levý a pravý okraj)
        body = []
        rows = sorted(set(ys))
        L = [(xs[ys == y].min(), y) for y in rows]; R = [(xs[ys == y].max(), y) for y in rows][::-1]
        for px, py in (L + R)[::2]:
            E, N = utm(px, py); X, Y = t.transform(E, N); body.append([round(X, 1), round(Y, 1)])
        cy, cx = ndimage.center_of_mass(mm); E, N = utm(cx, cy); X, Y = t.transform(E, N)
        polys.append({"stred": [round(X, 1), round(Y, 1)], "plocha_m2": round(mm.sum() / s / s, 1), "obrys": body})
    out["vrstvy"][jm] = polys
    print(jm, [(p["stred"], p["plocha_m2"]) for p in polys])
json.dump(out, open(os.path.join(K, "pravidla/svet/hrady_plan.json"), "w"), ensure_ascii=False, indent=1)
