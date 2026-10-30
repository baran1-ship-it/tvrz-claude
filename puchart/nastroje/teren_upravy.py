"""Terénní úpravy dvojhradu (krok B: terén -> pak stavby; pozdější krok terén nemění). Data: pravidla/svet/hrad_puchart.json.

Valy a příkopy jsou ve skutečném DMR 5G (lokální reliéf je ukazuje) – nic se nepřidává. Upravuje se jen to, co stavba
potřebuje: srovnané plošiny (předbraní u vnější branky, dolní a horní nádvoří zadního hradu, nástup mostu přes průrvu),
rampa za branou předního hradu (práh o 1 m níž než nádvoří) a skalní průrva před zadním hradem (zářez s plochým dnem).
Výšky jsou absolutní (y hry), aby na ně stavba hradu navázala přesně (podlahy bran, mosty).
python3 teren_upravy.py <vysek_prefix> <vystup_prefix> <koren>
"""
import sys, json, shutil, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrad_geom
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt
pre, out, K = sys.argv[1:4]
H = np.load(pre + ".npy").astype(np.float64); M = json.load(open(pre + ".json"))
P = json.load(open(K + "/pravidla/svet/svet.json"))["pocatek"]
D = json.load(open(K + "/pravidla/svet/hrad_puchart.json"))
A, B, T = D["A"], D["B"], D["teren"]
# okno 320×320 m kolem hradů (mřížka 1 m), hra souřadnice buněk
X0, Z0, n = -110, -110, 320
c0 = int(round(X0 - (M["x0"] - P["X"]))); r0 = int(round(Z0 + (M["y1"] - P["Y"])))
hx, hz = np.meshgrid(X0 + np.arange(n, dtype=float), Z0 + np.arange(n, dtype=float))
Y = H[r0:r0 + n, c0:c0 + n] - P["H"]

def maska(poly):
    im = Image.new("L", (n, n), 0); ImageDraw.Draw(im).polygon([(x - X0, z - Z0) for x, z in poly], fill=1)
    return np.array(im).astype(bool)

def obdelnik(od, smer, t0, t1, sirka):
    o = np.array(od, float); u = np.array(smer, float); u /= np.linalg.norm(u); v = np.array([-u[1], u[0]])
    return [tuple(o + u * t + v * s) for t, s in ((t0, -sirka / 2), (t1, -sirka / 2), (t1, sirka / 2), (t0, sirka / 2))]

def srovnej(poly, y, prechod):
    global Y
    m = maska(poly)
    d = distance_transform_edt(~m)                       # vzdálenost od plošiny (m)
    w = np.clip(1 - d / prechod, 0, 1); w = w * w * (3 - 2 * w)
    Y = Y * (1 - w) + y * w

def brana(ref):
    """Brána v plášti předního hradu (A.brana / A.branka): střed na líci osy, vnější normála, data brány."""
    g = A[ref.split(".")[1]]; j = np.array(A["jadro"]); i = g["usek"]
    p1, p2 = j[i], j[(i + 1) % len(j)]; L = np.linalg.norm(p2 - p1); dw = (p2 - p1) / L
    C = p1 + dw * g.get("stred_m", L / 2); n_ = np.array([dw[1], -dw[0]])
    if np.dot(n_, C - j.mean(0)) < 0: n_ = -n_
    return C, n_, g

C, nA, _ = brana("A.brana")   # osa mostu předního hradu: ze středu brány (seříznuté nároží) kolmo ven
for pl in T["plosiny"]:
    y = pl.get("y")
    if "polygon" in pl: poly = pl["polygon"]
    elif "obdelnik_osa" in pl: poly = obdelnik(C, nA, pl["t_m"][0], pl["t_m"][1], pl["sirka"])
    elif "brana_venku" in pl:
        Cb, nb, gb = brana(pl["brana_venku"]); poly = obdelnik(Cb, nb, pl["t_m"][0], pl["t_m"][1], pl["sirka"]); y = gb["prah_y"]
    else: o = pl["obdelnik"]; poly = obdelnik(o["od"], o["smer"], o["t_m"][0], o["t_m"][1], o["sirka"])
    srovnej(poly, y, pl["prechod_m"])
# rampy za branami: od prahu (vnější líc zdi) dovnitř lineárně na úroveň nádvoří, šířka brány + 1 m na každou stranu
tl = A["kurtina_tloustka"] / 2
for b in T["brany"]:
    Cb, nb, g = brana(b["brana"]); Lr = b.get("rampa_m", g.get("rampa_m", 5.0)); yin = g.get("y_vnitrni", A["nadvori_y"])
    t = (hx - Cb[0]) * nb[0] + (hz - Cb[1]) * nb[1]; q = np.abs((hx - Cb[0]) * nb[1] - (hz - Cb[1]) * nb[0])
    yr = g["prah_y"] + (yin - g["prah_y"]) * np.clip((tl - t) / (Lr + tl), 0, 1)
    w = np.clip((g["sirka"] / 2 + 1.0 + 1.5 - q) / 1.5, 0, 1) * np.clip((t + Lr + tl + 2.0) / 2.0, 0, 1) * (t < tl + 2.5)
    w = np.where(t > tl, np.clip((tl + 2.5 - t) / 2.5, 0, 1) * w, w)
    Y = Y * (1 - w) + yr * w
# skalní průrva: dno dno_y, boky 1:0,5 (droba drží strmý svah)
pr = B["prurva"]; o = np.array(pr["osa"]); dist = np.full(hx.shape, 1e9)
for a_, b_ in zip(o[:-1], o[1:]):
    ab = b_ - a_; tt = np.clip(((hx - a_[0]) * ab[0] + (hz - a_[1]) * ab[1]) / (ab @ ab), 0, 1)
    dist = np.minimum(dist, np.hypot(hx - (a_[0] + ab[0] * tt), hz - (a_[1] + ab[1] * tt)))
Y = np.minimum(Y, pr["dno_y"] + np.clip(dist - pr["sirka"] / 2, 0, None) * 2.0)
# sklep pod palácem a sklepní šíje: jáma s ostrou hranou (hrad_geom.sklep); uloží se zvlášť, aby je vyhlazení dlaždic
# nerozmazalo do prohlubně kolem paláce (teren_dlazdice.py je vrátí po vyhlazení)
jamy = np.zeros(hx.shape, bool); jy = np.zeros(hx.shape)
if A.get("sklep", {}).get("teren_jamy"):
    g = hrad_geom.sklep(A); S = g["S"]
    u = (hx - g["o"][0]) * g["du"][0] + (hz - g["o"][1]) * g["du"][1]; v = (hx - g["o"][0]) * g["dv"][0] + (hz - g["o"][1]) * g["dv"][1]
    # hrana jámy pod zdmi, ne v místnosti: k hradbě (J) a k Z zdi 0,9 m (svah zmizí v plášti), k nádvoří a k průchodu
    # na V také 0,9 m (mělký příkop vedle paláce kryje kamenný okapový chodník); k nádvoří jen 0,4 m
    m1 = (u >= -0.9) & (u <= g["Li"] + 0.9) & (v >= -0.9) & (v <= g["Wi"] + 0.4)   # V hranu kryje okapový chodník
    jamy |= m1; jy[m1] = g["y"] - 0.3
    sj = S["sije"]; v0 = g["Wi"] + g["tl"]; ytop = A["nadvori_y"]
    n_st = round((ytop - g["y"]) / 0.19); run = n_st * 0.30
    prof = np.interp(u, [sj["u_horni"], sj["u_horni"] + run], [ytop, g["y"]]) - 0.3
    m2 = (u >= sj["u_horni"] - 0.2) & (u <= sj["u_dvere"] + 1.3) & (v >= v0 - 0.4) & (v <= v0 + sj["sirka"] + 0.3)
    jamy |= m2; jy[m2] = np.minimum(np.where(m1[m2], jy[m2], 1e9), prof[m2])
    Y = np.where(jamy, np.minimum(Y, jy), Y)
rr, cc = np.nonzero(jamy)
np.savez(out + "_jamy.npz", r=rr + r0, c=cc + c0, y=(Y[rr, cc] + P["H"]).astype(np.float32))
H2 = H.copy(); H2[r0:r0 + n, c0:c0 + n] = Y + P["H"]
np.save(out + ".npy", H2.astype(np.float32)); shutil.copy(pre + ".json", out + ".json")
print("terén hradů: plošin", len(T["plosiny"]), "max změna", round(float(np.abs(H2 - H).max()), 2), "m")
