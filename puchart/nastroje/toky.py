"""Vodní síť z terénu (D8 nad DMR 5G), jména z OSM.

OSM linie leží v údolí s mediánem ~15 m vedle dna a ~1,2 m nad ním (změřeno 29. 10.) – proto osa toku
vzniká z terénu (odtok) a OSM jen pojmenuje větev. Výstup: polylinie S-JTSK s výškou dna, klesající po proudu.

python3 toky.py <mrizka_5m_prefix> <osm_vrstvy.json> <vystup.json> [min_povodi_km2]
"""
import sys, json
import numpy as np
if not hasattr(np, "in1d"): np.in1d = np.isin  # pysheds s numpy 2.x
from pysheds.sview import Raster, ViewFinder
from pysheds.grid import Grid
from affine import Affine

pre, osm, out = sys.argv[1:4]
min_km2 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json")); k = M["krok_m"]
aff = Affine(k, 0, M["x0"] - k / 2, 0, -k, M["y1"] + k / 2)
vf = ViewFinder(affine=aff, shape=H.shape, nodata=-9999.0)
dem = Raster(H, viewfinder=vf)
g = Grid(viewfinder=vf)
f = g.resolve_flats(g.fill_depressions(g.fill_pits(dem)))
dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
fd = g.flowdir(f, dirmap=dirmap)
acc = g.accumulation(fd, dirmap=dirmap)
prah = min_km2 * 1e6 / (k * k)
tok = np.asarray(acc) > prah
FD = np.asarray(fd)
kroky = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
# prameny = buňky toku bez přítoku z jiné buňky toku
pritok = np.zeros_like(tok, dtype=np.int32)
R, C = np.nonzero(tok)
for r, c in zip(R, C):
    d = kroky.get(int(FD[r, c]))
    if d:
        rr, cc = r + d[0], c + d[1]
        if 0 <= rr < H.shape[0] and 0 <= cc < H.shape[1] and tok[rr, cc]:
            pritok[rr, cc] += 1
navstiveno = np.zeros_like(tok)
vetve = []
def stopa(r, c):
    body = []
    while True:
        body.append((r, c))
        if navstiveno[r, c]:
            break
        navstiveno[r, c] = True
        d = kroky.get(int(FD[r, c]))
        if not d:
            break
        rr, cc = r + d[0], c + d[1]
        if not (0 <= rr < H.shape[0] and 0 <= cc < H.shape[1]) or not tok[rr, cc]:
            break
        if pritok[rr, cc] > 1 and navstiveno[rr, cc]:
            body.append((rr, cc)); break
        r, c = rr, cc
    return body
# nejdřív nejdelší (nejvýš položené prameny), aby hlavní tok byl jedna větev
prameny = sorted([(r, c) for r, c in zip(R, C) if pritok[r, c] == 0], key=lambda p: -H[p])
for r, c in prameny:
    b = stopa(r, c)
    if len(b) > 3:
        vetve.append(b)
# jména z OSM: nejbližší OSM linie (průměrná vzdálenost)
V = json.load(open(osm))
osm_body = [(c["jmeno"].split(",")[0], np.array(c["body"])) for c in V["cary"]]
Fz = np.asarray(f)
vystup = []
for b in vetve:
    xy = np.array([(M["x0"] + c * k, M["y1"] - r * k) for r, c in b])
    z = np.array([Fz[r, c] for r, c in b])
    z = np.minimum.accumulate(z)  # dno nikdy nestoupá po proudu
    nejl, dmin = None, 1e9
    for j, P in osm_body:
        d = np.mean([np.min(np.hypot(P[:, 0] - x, P[:, 1] - y)) for x, y in xy[:: max(1, len(xy) // 30)]])
        if d < dmin:
            nejl, dmin = j, d
    a = float(np.asarray(acc)[b[-1]]) * k * k / 1e6
    vystup.append({"jmeno": nejl if dmin < 60 else None, "osm_vzdalenost_m": round(dmin, 1), "povodi_km2_na_konci": round(a, 2),
                   "body": [[round(x, 1), round(y, 1), round(float(zz), 2)] for (x, y), zz in zip(xy, z)]})
json.dump({"crs": "EPSG:5514", "zdroj": "D8 nad " + M["zdroj"] + "; jména OSM (ODbL)", "min_povodi_km2": min_km2, "toky": vystup},
          open(out, "w"), ensure_ascii=False)
for t in vystup:
    print(t["jmeno"], len(t["body"]), t["osm_vzdalenost_m"], t["povodi_km2_na_konci"])
