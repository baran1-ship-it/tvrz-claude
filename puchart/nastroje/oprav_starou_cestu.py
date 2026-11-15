"""Stará trasa cesty po přeložení (pravidla/svet/cesty_puchart.json cesta._osa_pred_<datum>): buňky stanoviště „cesta“ podél
staré osy, které nejsou u žádné současné cesty, dostanou nejčastější okolní třídu (jinak by tam zůstal holý pruh bez trávy –
cesty.py třídu cesta jen přidává). Míša 15. 11.: cesta u skály přeložena na rovinku k mostu.
  python3 nastroje/oprav_starou_cestu.py <K>"""
import sys, os, json
import numpy as np
from PIL import Image
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from shapely.prepared import prep
K = sys.argv[1]; D = K + "/hra/data/"
SJ = json.load(open(D + "stanoviste.json")); st = np.array(Image.open(D + "stanoviste.png")); st = st[..., 0] if st.ndim == 3 else st
ic = SJ["tridy"].index("cesta"); ks = SJ["krok_m"]; x0, z0 = SJ["x0_hra"], SJ["z0_hra"]
C = json.load(open(K + "/pravidla/svet/cesty_puchart.json"))["cesty"]
stare = [LineString(v) for c in C for k, v in c.items() if k.startswith("_osa_pred_") and len(v) > 1]
if not stare: print("STARA_CESTA žádná"); sys.exit(0)
nove = prep(unary_union([LineString([q[:2] for q in c["osa"]]).buffer(4.5) for c in C if len(c["osa"]) > 1]))
pas = unary_union([s.buffer(4.0) for s in stare]); mn = pas.bounds; n = 0
for r in range(max(0, int((mn[1] - z0) / ks)), min(st.shape[0], int((mn[3] - z0) / ks) + 2)):
    for c_ in range(max(0, int((mn[0] - x0) / ks)), min(st.shape[1], int((mn[2] - x0) / ks) + 2)):
        if st[r, c_] != ic: continue
        p = Point(x0 + (c_ + 0.5) * ks, z0 + (r + 0.5) * ks)
        if not pas.contains(p) or nove.contains(p): continue
        ok = st[max(0, r - 4):r + 5, max(0, c_ - 4):c_ + 5].ravel(); ok = ok[ok != ic]
        if ok.size: st[r, c_] = np.bincount(ok).argmax(); n += 1
Image.fromarray(st).save(D + "stanoviste.png")
print("STARA_CESTA buněk vráceno", n)
