"""Šedý podklad a suť jen těsně u skal (pravidla/svet/skaly.json podklad, půdorysy hra/data/skaly_body.json ze stavitele
blender/skaly.py): maska_vysek B, stanoviště skala (bez trávy) a bez stromů v půdorysu skály. Mezi skalami zůstává les
a hrabanka (fotky). Spustit po blender/skaly.py; mění jen masku a stanoviště, ne terén.
python3 skaly_podklad.py <koren>"""
import sys, json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
K = sys.argv[1]
S = json.load(open(K + "/pravidla/svet/skaly.json"))["podklad"]
Bd = json.load(open(K + "/hra/data/skaly_body.json"))["skaly"]
VI = json.load(open(K + "/hra/data/vysek.json"))
x0, z0 = VI["x0_hra"], VI["z0_hra"]
w = np.zeros((1000, 1000), np.float32)   # maska 2 m
for b in Bd:
    cx, cz = b["stred"]; r = (S["sut_m"] if b["typ"] == "sut" else S["okolo_m"]) + min(b["delka"] / 2, 3.0)
    c0, r0 = int((cx - x0) / 2), int((cz - z0) / 2); rr = int(r / 2) + 2
    for i in range(max(0, r0 - rr), min(1000, r0 + rr + 1)):
        for j in range(max(0, c0 - rr), min(1000, c0 + rr + 1)):
            d = np.hypot(j * 2 + 1 + x0 - cx, i * 2 + 1 + z0 - cz)
            w[i, j] = max(w[i, j], np.clip((r - d) / 1.5, 0, 1) * (0.7 if b["typ"] == "sut" else 1.0))
w = gaussian_filter(w, 0.6)
mk = np.array(Image.open(K + "/hra/textury/maska_vysek.png")).astype(np.float32) / 255
mk[..., 0] *= 1 - w; mk[..., 3] *= 1 - w; mk[..., 1] *= 1 - w * 0.5; mk[..., 2] = np.maximum(mk[..., 2], w)
Image.fromarray((mk * 255).astype(np.uint8), "RGBA").save(K + "/hra/textury/maska_vysek.png")
sj = json.load(open(K + "/hra/data/stanoviste.json")); ic = sj["tridy"].index("skala")
st = np.array(Image.open(K + "/hra/data/stanoviste.png")); st[w > 0.6] = ic; Image.fromarray(st).save(K + "/hra/data/stanoviste.png")
A = np.fromfile(K + "/hra/data/stromy.bin", np.float32).reshape(-1, 5)
ci = np.clip(((A[:, 0] - x0) / 2).astype(int), 0, 999); ri = np.clip(((A[:, 1] - z0) / 2).astype(int), 0, 999)
keep = w[ri, ci] < 0.8; A[keep].tofile(K + "/hra/data/stromy.bin")
print("podklad skal: %d buněk 2 m, stromů pryč %d" % ((w > 0.5).sum(), (~keep).sum()))
