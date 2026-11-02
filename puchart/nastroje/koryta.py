"""Koryta potoků zaříznutá do terénu (pravidla/svet/voda_hra.json koryto; osy pravidla/svet/voda.json). Krok po teren_upravy.py,
před cesty.py: pozdější krok (voda.py) jen čte hladinu z hra/data/toky_hladina.json – hladina a koryto vždy sedí (Havran koryto.gd).
Hladina = nejnižší terén napříč osou (±šíře), vyhlazená po délce a po proudu nikdy nestoupá. Profil od osy: dno (parabola,
hloubka podle šíře) → práh břehu nad hladinou → svah až k původnímu terénu; terén se jen snižuje. Zaříznuté buňky jdou do
_jamy.npz, aby je vyhlazení dlaždic nerozmazalo.  python3 koryta.py <vstup_prefix> <vystup_prefix> <koren>"""
import sys, json, os, shutil, math
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.spatial import cKDTree
pre, out, K = sys.argv[1:4]
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json"))
P = json.load(open(K + "/pravidla/svet/svet.json"))["pocatek"]
VH = json.load(open(K + "/pravidla/svet/voda_hra.json")); KO = VH["koryto"]
toky = json.load(open(K + "/pravidla/svet/voda.json"))["toky"]
x0 = M["x0"] - P["X"]; z0 = -(M["y1"] - P["Y"]); ny, nx = H.shape
Y = H - P["H"]; Y0 = Y.copy()
def ter(x, z): return map_coordinates(Y0, [np.asarray(z) - z0, np.asarray(x) - x0], order=1, mode="nearest")
vystup = {}
DRUH = np.zeros(Y.shape, np.uint8); VODA = []
for ti, t in enumerate(toky):
    b = np.array(t["body"], float)[:, [0, 2]]
    ins = (b[:, 0] > x0 + 3) & (b[:, 0] < x0 + nx - 3) & (b[:, 1] > z0 + 3) & (b[:, 1] < z0 + ny - 3)
    if ins.sum() < 6: continue
    idx = np.nonzero(ins)[0]; b = b[idx[0]:idx[-1] + 1]
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(b, axis=0).T))]; s = np.arange(0, seg[-1], KO["krok_osy_m"])
    x = np.interp(s, seg, b[:, 0]); z = np.interp(s, seg, b[:, 1])
    w = min(VH["sirka"]["max_m"], VH["sirka"]["zaklad_m"] + VH["sirka"]["na_odmocninu_km2"] * math.sqrt(t.get("povodi_km2", 1.0)))
    d = np.gradient(np.c_[x, z], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.c_[-d[:, 1], d[:, 0]]
    dno = np.min([ter(x + n[:, 0] * o, z + n[:, 1] * o) for o in np.linspace(-w, w, 7)], axis=0)
    if dno[0] < dno[-1]: x, z, dno, n = x[::-1], z[::-1], dno[::-1], -n[::-1]
    k = max(1, int(VH["vyhlazeni_m"] / KO["krok_osy_m"]))
    hl = np.convolve(np.r_[[dno[0]] * k, dno, [dno[-1]] * k], np.ones(2 * k + 1) / (2 * k + 1), "same")[k:-k]
    hl = np.minimum(np.minimum.accumulate(hl), dno + 0.05)   # nikdy nestoupá a nikdy nad údolnicí
    hl = np.minimum.accumulate(hl)
    hv = KO["hloubka_vody_m"]["zaklad"] + KO["hloubka_vody_m"]["na_m_sirky"] * w
    # buňky v dosahu osy
    strom = cKDTree(np.c_[x, z]); R = w / 2 + KO["prah_m"] + KO["dosah_m"]
    c0_, c1_ = int(max(0, x.min() - R - x0)), int(min(nx, x.max() + R - x0 + 1)); r0_, r1_ = int(max(0, z.min() - R - z0)), int(min(ny, z.max() + R - z0 + 1))
    cx, cz = np.meshgrid(x0 + np.arange(c0_, c1_), z0 + np.arange(r0_, r1_))
    dist, j = strom.query(np.c_[cx.ravel(), cz.ravel()], distance_upper_bound=R)
    ok = np.isfinite(dist); dist = np.where(ok, dist, R); j = np.minimum(j, len(x) - 1)
    hlj = hl[j]; pw = w / 2
    prof = np.where(dist < pw, hlj - hv * (1 - (dist / pw) ** 2),
           np.where(dist < pw + KO["prah_m"], hlj + KO["prah_nad_hladinou_m"] * (dist - pw) / KO["prah_m"],
                    hlj + KO["prah_nad_hladinou_m"] + (dist - pw - KO["prah_m"]) * KO["sklon_svahu"]))
    prof = np.where(ok, prof, 1e9).reshape(cx.shape)
    sub = Y[r0_:r1_, c0_:c1_]; Y[r0_:r1_, c0_:c1_] = np.minimum(sub, prof)
    # stanoviště koryta: 1 = kamenité dno a práh (valouny, mech), 2 = břeh (kopřivy, ostružiník, vrbičky) – byliny.json
    dd = dist.reshape(cx.shape); sub_dr = DRUH[r0_:r1_, c0_:c1_]
    sub_dr[(dd < pw + KO["prah_m"]) & np.isfinite(dd)] = 1
    sub_dr[(dd >= pw + KO["prah_m"]) & (dd < pw + KO["prah_m"] + KO["breh_m"]) & (sub_dr == 0)] = 2
    VODA.append((np.c_[x, z], pw + 0.4))
    vystup[str(ti)] = {"jmeno": t.get("jmeno"), "sirka": w, "hloubka": hv, "osa": np.c_[x, z, hl].round(3).tolist()}
    print("koryto", t.get("jmeno") or ti, "délka %.0f m, šíře %.1f, hloubka vody %.2f, max zářez %.1f m" % (s[-1], w, hv, float((sub - np.minimum(sub, prof)).max())))
zar = (Y0 - Y) > 0.03
H2 = Y + P["H"]
if os.path.exists(pre + "_jamy.npz"):   # sklep a šíje (teren_upravy.py) mají přednost
    J = np.load(pre + "_jamy.npz"); zar[J["r"], J["c"]] = False; H2[J["r"], J["c"]] = J["y"]
    rr, cc = np.nonzero(zar); r = np.r_[J["r"], rr]; c = np.r_[J["c"], cc]; yy = np.r_[J["y"], H2[rr, cc]]
else:
    r, c = np.nonzero(zar); yy = H2[r, c]
np.savez(out + "_jamy.npz", r=r, c=c, y=yy.astype(np.float32))
np.save(out + ".npy", H2.astype(np.float32)); shutil.copy(pre + ".json", out + ".json")
rr, cc = np.nonzero(DRUH); np.savez(out + "_koryta.npz", r=rr, c=cc, druh=DRUH[rr, cc])   # cesty.py → stanoviště
# stromy z vody pryč (koruny nad vodou smí, kmen ve vodě ne)
sb = K + "/hra/data/stromy.bin"; A = np.fromfile(sb, np.float32).reshape(-1, 5); keep = np.ones(len(A), bool)
for osa, r in VODA:
    d_, _ = cKDTree(osa).query(A[:, :2]); keep &= d_ > r
A[keep].tofile(sb); print("stromů z koryt pryč", int((~keep).sum()))
json.dump({"popis": "hladina potoků (nastroje/koryta.py): osa [x, z, hladina] po 1 m po proudu", "toky": vystup},
          open(K + "/hra/data/toky_hladina.json", "w"))
print("zaříznuto buněk", int(zar.sum()))
