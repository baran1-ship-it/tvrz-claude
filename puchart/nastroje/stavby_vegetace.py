"""Stavby → vegetace (pořadí stavby: terén → cesty → budovy → voda → vegetace; test smyslu hrad_bez_stromu a
kere_mimo_stavby, 2. 11.): ze skutečných obrysů zdí a budov (hra/data/stavby_clony.json ze stavitele hradu) stanoviště
„stavba“ (bez porostu) a uvnitř hradeb (hrad_puchart.json A.jadro, B.hradba) „nadvori“ (jen tráva, byliny.json);
stromy pryč ze staveb, nádvoří a pásu okraj_m kolem zdí. Nahrazuje ruční obdélníky hrady_bez_stromu.json.
  python3 nastroje/stavby_vegetace.py <koren>"""
import sys, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
K = os.path.abspath(sys.argv[1]); D = K + "/hra/data/"
SJ = json.load(open(D + "stanoviste.json")); st = np.array(Image.open(D + "stanoviste.png")); st = st[..., 0] if st.ndim == 3 else st
KC = json.load(open(K + "/pravidla/svet/kontroly.json"))["stavby_vegetace"]
for t in ("stavba", "nadvori"):
    if t not in SJ["tridy"]: SJ["tridy"].append(t)
ks = SJ["krok_m"]; x0, z0 = SJ["x0_hra"], SJ["z0_hra"]
def pix(p): return ((p[0] - x0) / ks, (p[1] - z0) / ks)
ms = Image.new("L", (st.shape[1], st.shape[0]), 0); dr = ImageDraw.Draw(ms)
for q in json.load(open(D + "stavby_clony.json"))["kvadry"]:
    dr.polygon([pix(r) for r in q["rohy"]], fill=1)
mn = Image.new("L", ms.size, 0); dn = ImageDraw.Draw(mn)
HP = json.load(open(K + "/pravidla/svet/hrad_puchart.json"))
for poly in (HP["A"]["jadro"], HP["B"]["hradba"]):
    dn.polygon([pix(r) for r in poly], fill=1)
stavba = binary_dilation(np.array(ms).astype(bool), iterations=1)   # +1 buňka: tenké zdi rastr 2 m míjel (kere_mimo_stavby)
nadvori = np.array(mn).astype(bool) & ~stavba
st[stavba] = SJ["tridy"].index("stavba"); st[nadvori] = SJ["tridy"].index("nadvori")
Image.fromarray(st).save(D + "stanoviste.png"); json.dump(SJ, open(D + "stanoviste.json", "w"), ensure_ascii=False, indent=1)
bez = binary_dilation(stavba | nadvori, iterations=max(1, int(KC["okraj_m"] / ks)))
A = np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5)
c = np.clip(((A[:, 0] - x0) / ks).astype(int), 0, st.shape[1] - 1); r = np.clip(((A[:, 1] - z0) / ks).astype(int), 0, st.shape[0] - 1)
keep = ~bez[r, c]; A[keep].tofile(D + "stromy.bin")
print("stavby: %d buněk, nádvoří %d, stromů pryč %d" % (stavba.sum(), nadvori.sum(), (~keep).sum()))
