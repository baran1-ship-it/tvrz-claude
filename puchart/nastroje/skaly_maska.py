"""Maska skalnatého hřbetu (pravidla/svet/skaly.json maska): kde je v zónách hřbetu a hradních kopců svah strmý nebo
hřbítek vyklenutý, je podkladem drobová skála – šedá vrstva terénu (maska_vysek B), žádná tráva (stanoviště skala),
žádné stromy. Terén se nemění. Výstup také build/skaly_maska.npz (maska 1 m pro skalní plášť v blender/skaly.py).
Pořadí: teren_upravy → cesty → skaly_maska → teren_dlazdice.
python3 skaly_maska.py <vysek_cesty_prefix> <koren>"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom
pre, K = sys.argv[1:3]
H = np.load(pre + ".npy").astype(np.float64); Mt = json.load(open(pre + ".json"))
P = json.load(open(K + "/pravidla/svet/svet.json"))["pocatek"]
S = json.load(open(K + "/pravidla/svet/skaly.json"))["maska"]
D = json.load(open(K + "/pravidla/svet/hrad_puchart.json")); A, B = D["A"], D["B"]
C = json.load(open(K + "/pravidla/svet/cesty_puchart.json"))
X0, Z0, n = -110, -110, 340
c0 = int(round(X0 - (Mt["x0"] - P["X"]))); r0 = int(round(Z0 + (Mt["y1"] - P["Y"])))
hx, hz = np.meshgrid(X0 + np.arange(n, dtype=float), Z0 + np.arange(n, dtype=float))
Y = gaussian_filter(H[r0:r0 + n, c0:c0 + n], 1.0)

def dl(pts):
    p = np.array(pts, float); d = np.full(hx.shape, 1e9)
    for a, b in zip(p[:-1], p[1:]):
        ab = b - a; t = np.clip(((hx - a[0]) * ab[0] + (hz - a[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
        d = np.minimum(d, np.hypot(hx - (a[0] + ab[0] * t), hz - (a[1] + ab[1] * t)))
    return d
def uvn(poly):
    p = np.array(poly, float); ins = np.zeros(hx.shape, bool)
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        ins ^= ((a[1] > hz) != (b[1] > hz)) & (hx < (b[0] - a[0]) * (hz - a[1]) / (b[1] - a[1] + 1e-12) + a[0])
    return ins

gz, gx = np.gradient(Y); sk = np.degrees(np.arctan(np.hypot(gx, gz)))
Ys = gaussian_filter(Y, 2.0); lap = (np.roll(Ys, 3, 0) + np.roll(Ys, -3, 0) + np.roll(Ys, 3, 1) + np.roll(Ys, -3, 1) - 4 * Ys) / 9.0
vyp = np.clip(-lap * 4, 0, None)
cesty = {c["id"]: c["osa"] for c in C["cesty"]}
zona = np.zeros(hx.shape)
for z in S["zony"]:
    d = dl(cesty[z["cesta"]]) / z["sirka_m"] if "cesta" in z else np.hypot(hx - z["stred"][0], hz - z["stred"][1]) / z["r"]
    zona = np.maximum(zona, np.clip((1 - d) * 3, 0, 1))
w = np.maximum(np.clip((sk - S["sklon_od_deg"]) / (S["sklon_plne_deg"] - S["sklon_od_deg"]), 0, 1),
               np.clip((vyp - S["vypouklost_od"]) / (S["vypouklost_plne"] - S["vypouklost_od"]), 0, 1))
rng = np.random.default_rng(1393)
sum_ = gaussian_filter(rng.standard_normal(hx.shape), S["sum_m"] / 2.5); sum_ /= np.abs(sum_).max()
w = np.clip(w * zona + sum_ * S["sum_sila"], 0, 1)
w = (w > S["prah"]).astype(float) * w
ven = np.zeros(hx.shape, bool)
for c in cesty.values(): ven |= dl(c) < S["vyloucit_cesty_m"] + 1.2
j = np.array(A["jadro"]); a_, b_ = j[A["brana"]["usek"]], j[A["brana"]["usek"] + 1]; CA = (a_ + b_) / 2
dw = (b_ - a_) / np.linalg.norm(b_ - a_); nA = np.array([dw[1], -dw[0]]); nA = nA if np.dot(nA, CA - j.mean(0)) > 0 else -nA
hb = np.array(B["hradba"]); wa, wb = hb[B["brana"]["usek"]], hb[B["brana"]["usek"] + 1]; GB = wa + (wb - wa) / np.linalg.norm(wb - wa) * B["brana"]["stred_m"]
for m in ([CA, CA + nA * 37], [np.array(B["most"]["od"]), GB]): ven |= dl(m) < S["vyloucit_mosty_m"]
ven |= uvn(A["jadro"]) | uvn(B["hradba"])
for pl in D["teren"]["plosiny"]:
    if "polygon" in pl: ven |= uvn(pl["polygon"])
for hv in (A["hradba_val"]["osa"], A["hradba_vychod"]["osa"]): ven |= dl(hv) < 1.2
ven |= np.hypot(hx - (CA + nA * 30.5)[0], hz - (CA + nA * 30.5)[1]) < 5
w[ven] = 0
w = gaussian_filter(w, 0.7)
os.makedirs(K + "/build", exist_ok=True); np.savez(K + "/build/skaly_maska.npz", w=w.astype(np.float32), x0=X0, z0=Z0)
print("skála v masce: %.0f m² (w>0.5)" % (w > 0.5).sum())
# vysek mřížka -> 2 m maska a stanoviště
cc0 = c0; rr0 = r0
full = np.zeros(H.shape, np.float32); full[rr0:rr0 + n, cc0:cc0 + n] = w
m2 = full[:H.shape[0] - 1:2, :H.shape[1] - 1:2][:1000, :1000]
mk = np.array(Image.open(K + "/hra/textury/maska_vysek.png")).astype(np.float32) / 255
b = np.clip(m2 * 1.15, 0, 1)
mk[..., 0] *= 1 - b; mk[..., 1] *= 1 - b; mk[..., 3] *= 1 - b; mk[..., 2] = np.maximum(mk[..., 2], b)
Image.fromarray((mk * 255).astype(np.uint8), "RGBA").save(K + "/hra/textury/maska_vysek.png")
sj = json.load(open(K + "/hra/data/stanoviste.json")); ic = sj["tridy"].index("skala")
st = np.array(Image.open(K + "/hra/data/stanoviste.png")); st[m2[:st.shape[0], :st.shape[1]] > 0.45] = ic
Image.fromarray(st).save(K + "/hra/data/stanoviste.png")
VI = Mt; xh0 = VI["x0"] - P["X"]; zh0 = -(VI["y1"] - P["Y"])
Ast = np.fromfile(K + "/hra/data/stromy.bin", np.float32).reshape(-1, 5)
ci = np.clip((Ast[:, 0] - xh0).astype(int), 0, H.shape[1] - 1); ri = np.clip((Ast[:, 1] - zh0).astype(int), 0, H.shape[0] - 1)
keep = full[ri, ci] < S["stromy_pryc_nad"]; Ast[keep].tofile(K + "/hra/data/stromy.bin")
print("stromů odstraněno ze skal", int((~keep).sum()))
