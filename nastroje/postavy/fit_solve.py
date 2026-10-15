"""Fit vah obličejových targetů na 68 bodů z fotky (perspektivní kamera, neznámá poloha hlavy).
python3 fit_solve.py <jmeno> <foto.json> [lambda]
"""
import sys, json, numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot

NAME, FJ = sys.argv[1], sys.argv[2]
LAM = float(sys.argv[3]) if len(sys.argv) > 3 else 0.02
d = np.load(f"/home/claude/chars/fit_{NAME}.npz")
vidx, base, D, names = d["vidx"], d["base"], d["deltas"], [str(n) for n in d["names"]]
ph = np.array(json.load(open(FJ)), float)
faces = json.load(open("/home/claude/chars/faces.json"))
cur = faces.get(NAME, {})
ok = vidx >= 0
K = len(names)
# jen targety, které s body něco dělají
act = np.array([np.abs(D[k][ok]).max() > 2e-4 for k in range(K)])
idx = np.where(act)[0]
lo = np.array([-cur.get(names[k], 0.0) for k in idx]); hi = np.array([1.0 - cur.get(names[k], 0.0) for k in idx])
wpt = np.ones(68); wpt[0:17] = 0.5; wpt[17:27] = 0.6
from PIL import Image
# fotka: ohnisko odhad z typické selfie kamery (~75° úhlopříčně)
# (velikost obrázku z JSON neznáme -> z argumentu)
IW, IH = Image.open(FJ.replace(".json", ".jpg")).size
f0 = 0.5 * np.hypot(IW, IH) / np.tan(np.radians(37.5))
c = np.array([IW / 2, IH / 2])
cen = base[ok].mean(0)

def project(p, X):
    rv, t, s = p[:3], p[3:6], p[6]
    Xc = Rot.from_rotvec(rv).apply(X - cen) + t       # kamera: osa +Y dopředu (do hlavy), Z nahoru
    return np.stack([f0 * s * Xc[:, 0] / Xc[:, 1], -f0 * s * Xc[:, 2] / Xc[:, 1]], 1) + c

def model(w):
    X = base.copy()
    X += np.tensordot(w, D[idx], axes=(0, 0))
    return X

def resid(q):
    p, w = q[:7], q[7:]
    pr = project(p, model(w)[ok])
    r = ((pr - ph[ok]) / (0.1 * IW)) * wpt[ok, None]
    return np.concatenate([r.ravel(), LAM * w])

# odhad vzdálenosti: šířka očí
eyew_px = np.linalg.norm(ph[45] - ph[36]); eyew_m = np.linalg.norm(base[45] - base[36]) if ok[45] and ok[36] else 0.09
dist = f0 * eyew_m / eyew_px
p0 = np.array([0, 0, 0, 0, dist, 0, 1.0])
q0 = np.concatenate([p0, np.zeros(len(idx))])
lb = np.concatenate([[-0.6, -0.6, -0.6, -0.3, 0.15, -0.3, 0.7], lo]); ub = np.concatenate([[0.6, 0.6, 0.6, 0.3, 1.5, 0.3, 1.3], hi])
# 1) jen poloha
r1 = least_squares(lambda p: resid(np.concatenate([p, np.zeros(len(idx))]))[: 68 * 2], p0, bounds=(lb[:7], ub[:7]))
print("pose-only err px", np.sqrt(np.mean(((project(r1.x, base[ok]) - ph[ok]) ** 2).sum(1))).round(1), "dist", r1.x[4].round(3))
q0[:7] = r1.x
r2 = least_squares(resid, q0, bounds=(lb, ub), max_nfev=400)
p, w = r2.x[:7], r2.x[7:]
err = np.sqrt(np.mean(((project(p, model(w)[ok]) - ph[ok]) ** 2).sum(1)))
print("fit err px", err.round(1))
new = dict(cur)
for k, wk in zip(idx, w):
    if abs(wk) > 0.03: new[names[k]] = round(cur.get(names[k], 0.0) + float(wk), 3)
# zrušit dvojice incr/decr (jen ta silnější)
for n in list(new):
    for a, b in (("-incr", "-decr"), ("-up", "-down"), ("-in", "-out"), ("-forward", "-backward"), ("-compress", "-uncompress"), ("-concave", "-convex")):
        if n.endswith(a):
            m = n[: -len(a)] + b
            if m in new:
                if new[n] >= new[m]: new[n] = round(new[n] - new[m], 3); new.pop(m)
                else: new[m] = round(new[m] - new[n], 3); new.pop(n)
new = {k: v for k, v in new.items() if v > 0.02}
changes = sorted(((names[k], round(float(wk), 2)) for k, wk in zip(idx, w) if abs(wk) > 0.05), key=lambda t: -abs(t[1]))
print("CHANGES", changes[:30])
json.dump(new, open(f"/home/claude/chars/faces_fit_{NAME}.json", "w"), indent=1)
# náhled: body z fotky (červeně) vs. model (zeleně)
from PIL import ImageDraw
im = Image.open(FJ.replace(".json", ".jpg")).convert("RGB"); dr = ImageDraw.Draw(im)
pr0 = project(r1.x, base[ok]); pr = project(p, model(w)[ok])
for a, b_, g in zip(ph[ok], pr0, pr):
    dr.ellipse((*(a - 5), *(a + 5)), fill=(255, 0, 0)); dr.ellipse((*(b_ - 4), *(b_ + 4)), outline=(0, 120, 255), width=2)
    dr.ellipse((*(g - 4), *(g + 4)), fill=(0, 255, 0))
x0, y0 = ph.min(0) - 250; x1, y1 = ph.max(0) + 150
im.crop((int(x0), int(y0), int(x1), int(y1))).save(f"/home/claude/chars/foto/{NAME}_fit.jpg")
