"""Překryv georeferencovaného plánu atlasu přes stínovaný DMR 5G (kontrola, že plán sedí na terén).
python3 plan_prekryv.py <plan.jpg> <vysek_prefix> <vystup.png> [x0 y0 velikost_m] (S-JTSK, výchozí okolí hradů)"""
import sys, json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
from pyproj import Transformer
plan, pre, out = sys.argv[1:4]
x0, y0, vel = (map(float, sys.argv[4:7]) if len(sys.argv) > 6 else (-516030.0, -1122400.0, 300.0))
H = gaussian_filter(np.load(pre + ".npy").astype(float), 1.0); M = json.load(open(pre + ".json"))
k = 0.25; n = int(vel / k)
X = x0 + np.arange(n) * k; Y = y0 - np.arange(n) * k
XX, YY = np.meshgrid(X, Y)
h = map_coordinates(H, [M["y1"] - YY, XX - M["x0"]], order=1)
gy, gx = np.gradient(h, k); sh = np.clip((-gx * 0.5 + gy * 0.5 + 1) / np.sqrt(gx**2 + gy**2 + 1) / 1.2, 0, 1)
c = ((h - h.min()) / (h.max() - h.min()))
q = np.floor(h / 2); vrst = (q != np.roll(q, 1, 0)) | (q != np.roll(q, 1, 1))
base = np.stack([sh * 0.9 + 0.1] * 3, -1); base[vrst] *= 0.6
t = Transformer.from_crs(5514, 32633, always_xy=True)
E, N = t.transform(XX, YY)
s = (377 - 52) / 100.0
px = 52 + (E - 693700) * s; py = 113 + (5499000 - N) * s
P = np.asarray(Image.open(plan).convert("RGB")).astype(float) / 255
pl = np.stack([map_coordinates(P[..., i], [py, px], order=1, cval=1) for i in range(3)], -1)
fial = (pl[..., 0] > 0.43) & (pl[..., 1] < 0.24) & (pl[..., 2] > 0.4)
cerna = (pl.sum(-1) < 0.7)
seda = (np.abs(pl - 0.866).max(-1) < 0.06)
o = base.copy()
o[seda] = o[seda] * 0.6 + np.array([0.9, 0.9, 0.6]) * 0.4
o[fial] = o[fial] * 0.35 + np.array([0.7, 0.1, 0.7]) * 0.65
o[cerna] = [0.05, 0.05, 0.05]
Image.fromarray((o * 255).astype(np.uint8)).resize((900, 900)).save(out)
print(out)
