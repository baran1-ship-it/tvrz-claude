"""DMR 5G (LAZ, S-JTSK) -> výšková mřížka (float32 .npy) + náhledy.

Použití: python3 dmr_mrizka.py <adresář_laz> <výstup_prefix> <x0> <y0> <x1> <y1> <krok_m>
Souřadnice jsou S-JTSK (EPSG:5514). DMR 5G jsou klíčové body terénu (TIN), proto lineární
interpolace přes Delaunayho triangulaci, ne průměrování buněk.
"""
import sys, glob, json
import numpy as np, laspy
from scipy.interpolate import LinearNDInterpolator

d, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1, krok = map(float, sys.argv[3:8])
okraj = 30.0
P = []
for f in sorted(glob.glob(d + "/*.laz")):
    l = laspy.read(f)
    x, y, z = np.asarray(l.x), np.asarray(l.y), np.asarray(l.z)
    m = (x > x0 - okraj) & (x < x1 + okraj) & (y > y0 - okraj) & (y < y1 + okraj)
    P.append(np.c_[x[m], y[m], z[m]])
P = np.concatenate(P)
print("body", len(P), "hustota", len(P) / ((x1 - x0) * (y1 - y0)), "/m2")
xs = np.arange(x0, x1 + krok / 2, krok)
ys = np.arange(y1, y0 - krok / 2, -krok)  # řádky od severu (S-JTSK: y roste k jihu? ne – Y je záporné, sever = větší y)
X, Y = np.meshgrid(xs, ys)
f = LinearNDInterpolator(P[:, :2], P[:, 2])
H = f(X, Y).astype(np.float32)
print("NaN", int(np.isnan(H).sum()), "výšky", np.nanmin(H), np.nanmax(H), "tvar", H.shape)
np.save(out + ".npy", H)
json.dump({"crs": "EPSG:5514", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "krok_m": krok,
           "radky": "od severu (y1) k jihu (y0)", "sloupce": "od západu (x0) k východu (x1)",
           "zdroj": "ČÚZK DMR 5G, LAZ S-JTSK, mapové listy " + ", ".join(sorted(g.split('/')[-1][:-4] for g in glob.glob(d + '/*.laz'))),
           "hmin": float(np.nanmin(H)), "hmax": float(np.nanmax(H))},
          open(out + ".json", "w"), ensure_ascii=False, indent=1)
