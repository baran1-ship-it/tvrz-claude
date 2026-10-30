"""Cesty výseku (krok B pořadí Havrana: terén -> cesty -> budovy): osa z plánovače (pristup.py), podélný profil,
zářez/násyp do terénu, maska povrchu, vyčištění stromů a bylin.

Podloží (ČGS GeoČR50, 30. 10.): droby (šedé, lavicovité, deskovité) a jílovité břidlice -> mělká půda; kde cesta
zařízne pod terén (úvoz), vystupuje skála (B kanál masky cest). Povrch: vozová = hlína s kamením (Havran „hlina“ =
stony_dirt_path), stezka = pěšina (Havran „pesina“ = forest_ground_05).

Vstup: <vysek_upr.npy/.json> (S-JTSK 1 m, po teren_upravy.py), pravidla/svet/cesty_puchart.json (osy a typy)
Výstup: <vystup>.npy (terén s cestami), hra/textury/maska_cesty.png (R vozová, G stezka, B skála v úvozu; 2 m),
        hra/data/stromy.bin bez stromů na cestě, hra/data/stanoviste.png třída „cesta“.
python3 cesty.py <vysek_upr_prefix> <vystup_prefix> <koren>
"""
import sys, json, os, shutil
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates, distance_transform_edt
from PIL import Image

pre, out, K = sys.argv[1:4]
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json"))
S = json.load(open(os.path.join(K, "pravidla/svet/svet.json"))); P = S["pocatek"]
C = json.load(open(os.path.join(K, "pravidla/svet/cesty_puchart.json")))
ny, nx = H.shape
xh0 = M["x0"] - P["X"]; zh0 = -(M["y1"] - P["Y"])          # hra souřadnice buňky [0,0]
H0 = H.copy()
Hs = gaussian_filter(H, 1.5)

def vz(x, z):   # výška původního terénu (hra souřadnice -> m n. m.)
    return map_coordinates(Hs, [np.atleast_1d(z) - zh0, np.atleast_1d(x) - xh0], order=1)

def chaikin(p, n=3):
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        q.append(p[-1]); p = np.array(q)
    return p

maskR = np.zeros((ny, nx)); maskG = np.zeros((ny, nx)); rez = np.zeros((ny, nx))
na_ceste = np.zeros((ny, nx), bool)
rng = np.random.default_rng(1393)
sum_ = gaussian_filter(rng.standard_normal((ny // 2 + 1, nx // 2 + 1)), 2)
sum_ = np.repeat(np.repeat(sum_, 2, 0), 2, 1)[:ny, :nx]; sum_ /= np.abs(sum_).max()
for c in C["cesty"]:
    T = C["typy"][c["typ"]]
    osa = chaikin(np.array(c["osa"], float), 3)
    # převzorkovat po 1 m
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(osa, axis=0).T))]
    s = np.arange(0, d[-1], 1.0)
    px = np.interp(s, d, osa[:, 0]); pz = np.interp(s, d, osa[:, 1])
    y = vz(px, pz)
    # profil: vyhlazení (okno T.profil_okno_m) + omezení sklonu dopředu i dozadu (nejvýš T.max_sklon)
    w = int(T["profil_okno_m"])
    yp = np.convolve(np.r_[[y[0]] * w, y, [y[-1]] * w], np.ones(2 * w + 1) / (2 * w + 1), "same")[w:-w]
    yp[:3] = y[:3]; yp[-3:] = y[-3:]                  # konce na terénu (napojení na nástupy mostů a branky)
    for _ in range(4):
        for i in range(1, len(yp)): yp[i] = np.clip(yp[i], yp[i - 1] - T["max_sklon"], yp[i - 1] + T["max_sklon"])
        for i in range(len(yp) - 2, -1, -1): yp[i] = np.clip(yp[i], yp[i + 1] - T["max_sklon"], yp[i + 1] + T["max_sklon"])
    c["delka_m"] = round(float(s[-1])); c["max_rez_m"] = round(float((y - yp).max()), 1); c["max_nasyp_m"] = round(float((yp - y).max()), 1)
    # rasterizace: každá buňka v dosahu dostane výšku nejbližšího bodu osy
    hw = T["sirka_m"] / 2; okraj = T["okraj_m"]
    x0i = int(max(0, px.min() - xh0 - hw - okraj - 2)); x1i = int(min(nx, px.max() - xh0 + hw + okraj + 3))
    z0i = int(max(0, pz.min() - zh0 - hw - okraj - 2)); z1i = int(min(ny, pz.max() - zh0 + hw + okraj + 3))
    ZZ, XX = np.mgrid[z0i:z1i, x0i:x1i]; xs = XX + xh0; zs = ZZ + zh0
    from scipy.spatial import cKDTree
    dist, idx = cKDTree(np.c_[px, pz]).query(np.c_[xs.ravel(), zs.ravel()])
    dist = dist.reshape(xs.shape); idx = idx.reshape(xs.shape)
    cil = yp[idx]
    # napříč: jízdní pás rovně (příčný podíl svahu zůstane jen T.pricny_podil), okraj plynule do svahu
    wpas = np.clip((hw + okraj - dist) / okraj, 0, 1)
    wpas = wpas * wpas * (3 - 2 * wpas)
    orig = H[z0i:z1i, x0i:x1i]
    novy = orig * (1 - wpas) + (cil + (orig - cil) * T["pricny_podil"]) * wpas
    H[z0i:z1i, x0i:x1i] = np.where(wpas > 0, novy, orig)
    # maska povrchu: měkký okraj s šumem (cesta není pravítko)
    m = np.clip((hw + 0.6 + sum_[z0i:z1i, x0i:x1i] * 0.5 - dist) / 1.2, 0, 1)
    if T["povrch"] == "hlina":
        maskR[z0i:z1i, x0i:x1i] = np.maximum(maskR[z0i:z1i, x0i:x1i], m)
    else:
        maskG[z0i:z1i, x0i:x1i] = np.maximum(maskG[z0i:z1i, x0i:x1i], m)
    # skála: kde se cesta zařízla (úvoz) – boky a dno; na drobách stačí ~0,6 m
    hloubka = np.clip(orig - novy, 0, None)
    rez[z0i:z1i, x0i:x1i] = np.maximum(rez[z0i:z1i, x0i:x1i], np.clip(hloubka / T["skala_od_rezu_m"], 0, 1) * (wpas > 0.05))
    na_ceste[z0i:z1i, x0i:x1i] |= dist < hw + 1.5
    print(c["id"], "délka", c["delka_m"], "m, zářez max", c["max_rez_m"], "m, násyp max", c["max_nasyp_m"], "m")
rez = np.clip(gaussian_filter(rez, 1.0) * (0.75 + 0.35 * sum_), 0, 1)
np.save(out + ".npy", H.astype(np.float32)); shutil.copy(pre + ".json", out + ".json")
# maska 2 m (stejná mřížka jako maska stanovišť: výsek 2000 m / 2)
k = 2
mk = np.stack([maskR, maskG, rez], -1)[:ny - 1:k, :nx - 1:k][:1000, :1000]
Image.fromarray((np.clip(mk, 0, 1) * 255).astype(np.uint8), "RGB").save(os.path.join(K, "hra/textury/maska_cesty.png"))
# stromy pryč z cesty
sb = os.path.join(K, "hra/data/stromy.bin")
A = np.fromfile(sb, np.float32).reshape(-1, 5)
ci = np.clip((A[:, 0] - xh0).astype(int), 0, nx - 1); ri = np.clip((A[:, 1] - zh0).astype(int), 0, ny - 1)
keep = ~na_ceste[ri, ci]
A[keep].tofile(sb)
print("stromů odstraněno z cest", int((~keep).sum()))
# stanoviště: třída cesta (byliny se tam nesází)
sj_p = os.path.join(K, "hra/data/stanoviste.json"); sj = json.load(open(sj_p))
if "cesta" not in sj["tridy"]: sj["tridy"].append("cesta")
ic = sj["tridy"].index("cesta"); json.dump(sj, open(sj_p, "w"), ensure_ascii=False, indent=1)
st = np.array(Image.open(os.path.join(K, "hra/data/stanoviste.png")))
nc = na_ceste[:ny - 1:2, :nx - 1:2][:st.shape[0], :st.shape[1]]
st[nc] = ic; Image.fromarray(st).save(os.path.join(K, "hra/data/stanoviste.png"))
C["vysledek"] = {c["id"]: {k2: c[k2] for k2 in ("delka_m", "max_rez_m", "max_nasyp_m")} for c in C["cesty"]}
json.dump(C, open(os.path.join(K, "pravidla/svet/cesty_puchart.json"), "w"), ensure_ascii=False, indent=1)
