"""Terénní úpravy hradů podle plánu atlasu (krok B: terén -> pak stavby; pozdější krok terén nemění).

Fialová = val (+val_vyska), světle šedá mimo jádro = příkop (−prikop_hloubka), šedá v jádru = plošina srovnaná na
70. percentil, fialové oblouky u zadního hradu = skalní příkopy. Hodnoty z hrady_navrhy.json spolecne.A.teren.
Rozdíl se vyhladí (σ 1,5 m), ať val není schod. Výstup: <vystup>.npy (+ .json kopie metadat).
python3 teren_upravy.py <plan.jpg> <vysek_prefix> <vystup_prefix> <koren>
"""
import sys, json, shutil
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, map_coordinates, binary_dilation
from pyproj import Transformer
plan, pre, out, K = sys.argv[1:5]
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json"))
S = json.load(open(K + "/pravidla/svet/svet.json")); P = S["pocatek"]
N_ = json.load(open(K + "/pravidla/svet/hrady_navrhy.json"))["spolecne"]
T = N_["A"]["teren"]
# okno 260×260 m kolem hradů (souřadnice mřížky)
x0, y1 = P["X"] - 90, P["Y"] + 90
n = 260
XX, YY = np.meshgrid(x0 + np.arange(n), y1 - np.arange(n))
t = Transformer.from_crs(5514, 32633, always_xy=True)
E, Nn = t.transform(XX, YY)
s = 3.25
px = 52 + (E - 693700) * s; py = 113 + (5499000 - Nn) * s
A = np.asarray(Image.open(plan).convert("RGB")).astype(float) / 255
pl = np.stack([map_coordinates(A[..., i], [py, px], order=1, cval=1) for i in range(3)], -1)
fial = (pl[..., 0] > 0.43) & (pl[..., 1] < 0.24) & (pl[..., 2] > 0.4)
seda = np.abs(pl - 0.866).max(-1) < 0.06
# jádro A (hra x,z -> mřížka)
hx = XX - P["X"]; hz = -(YY - P["Y"])
jadro = Image.new("L", (n, n), 0)
ImageDraw.Draw(jadro).polygon([(x - (x0 - P["X"]), z - (-(y1 - P["Y"]))) for x, z in N_["A"]["jadro"]], fill=1)
jadro = np.array(jadro).astype(bool)
oblastA = hz < 30
r0 = int(M["y1"] - y1); c0 = int(x0 - M["x0"])
okno = H[r0:r0 + n, c0:c0 + n]
d = np.zeros_like(okno)
d[fial & oblastA] += T["val_vyska"]
prik = seda & oblastA & ~jadro & ~binary_dilation(fial, iterations=1)
d[prik] -= T["prikop_hloubka"]
# skalní příkopy zadního hradu: fialové oblouky dole (hz > 60), rozšířit na 3 m
fB = binary_dilation(fial & (hz > 60) & ~(seda), iterations=1)
d[fB] -= 3.0
d = gaussian_filter(d, 1.5)
if T.get("jadro_vyrovnat"):
    cil = np.percentile(okno[jadro], 70)
    w = gaussian_filter(jadro.astype(float), 1.5)
    okno_n = okno * (1 - w) + cil * w
else:
    okno_n = okno
okno2 = okno_n + d
# skalní průrva (hrady_navrhy.json spolecne.prurva) – zářez s plochým dnem a strmými boky
pr = N_.get("prurva")
if pr:
    o = np.array(pr["osa"]); dist = np.full(hx.shape, 1e9)
    for a_, b_ in zip(o[:-1], o[1:]):
        ab = b_ - a_; t = np.clip(((hx - a_[0]) * ab[0] + (hz - a_[1]) * ab[1]) / (ab @ ab), 0, 1)
        dist = np.minimum(dist, np.hypot(hx - (a_[0] + ab[0] * t), hz - (a_[1] + ab[1] * t)))
    w = pr["sirka"] / 2
    okno2 -= pr["hloubka"] * np.clip((w + 1.0 - dist) / 1.5, 0, 1)
# příkop pod každým mostem (Míša 30. 10.: most nesmí ležet v trávě, jinak ztrácí smysl): zářez napříč osou mostu
# mezi nástupem a prahem, dno ~5 m pod spojnicí nástup–práh, šířka 10 m, svahy 1:1 (droba drží strmý svah)
for m in N_.get("mosty", []):
    A_ = np.array(m["od"], float); B_ = np.array(m["do"], float); ab = B_ - A_; L_ = np.linalg.norm(ab); u = ab / L_
    t = ((hx - A_[0]) * u[0] + (hz - A_[1]) * u[1]); q = np.abs((hx - A_[0]) * u[1] - (hz - A_[1]) * u[0])
    ya_ = float(np.median(okno2[(np.hypot(hx - A_[0], hz - A_[1]) < 3)])); yb_ = float(np.median(okno2[(np.hypot(hx - B_[0], hz - B_[1]) < 3)]))
    linie = ya_ + (yb_ - ya_) * np.clip(t / L_, 0, 1)
    dno = linie - m.get("prikop_m", 5.0)
    vnitr = np.clip(np.minimum(t - 3.0, L_ - 2.0 - t), 0, None)          # od nástupu 3 m, od prahu 2 m
    svah = np.minimum(vnitr, np.clip(6.0 - q, 0, None) + 0) * 1.0          # svah 1:1 a šířka ±6 m kolem osy
    hladina = dno + (m.get("prikop_m", 5.0)) * (1 - np.clip(svah / 2.5, 0, 1))
    pas = (t > 0) & (t < L_) & (q < 9)
    okno2 = np.where(pas, np.minimum(okno2, hladina), okno2)
# nástupy mostů: plošina srovnaná na střední výšku v poloměru, plynulý přechod 3 m (Havran: dum_teren)
for m in N_.get("mosty", []):
    x, z = m["od"]; rr = m["nastup_r"]
    dd = np.hypot(hx - x, hz - z)
    cil = float(np.median(okno2[dd < rr]))
    w = np.clip((rr + 3.0 - dd) / 3.0, 0, 1)
    okno2 = okno2 * (1 - w) + cil * w
H2 = H.copy(); H2[r0:r0 + n, c0:c0 + n] = okno2
np.save(out + ".npy", H2.astype(np.float32)); shutil.copy(pre + ".json", out + ".json")
print("val px", int((fial & oblastA).sum()), "příkop px", int(prik.sum()), "skalní příkop px", int(fB.sum()), "plošina jádra", round(float(np.percentile(okno[jadro], 70)) - P["H"], 2))
