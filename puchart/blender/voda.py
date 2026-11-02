"""Potoky ve hře (pravidla/svet/voda_hra.json): hladina jako pás podél osy toku z pravidla/svet/voda.json, lávka u brodu.
Výška hladiny = dno údolnice (herní terén pod osou, vyhlazené po délce) + hloubka, pak po proudu nikdy nestoupá; kde by
klesla pod dno o víc než min_nad_dnem, zvedne se (krátké prahy). Okraje pásu přesahují břehy – terén je schová.
Pás má UV: u = vzdálenost po proudu (m), v = 0..1 napříč (shader: proud, okraje). Výstup hra/modely/voda.glb (+KOLIZE).
  /opt/bl/bin/python blender/voda.py <koren_puchartu>
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrady as H
from hrady import Part, M, R, ter, UP, Vector, Matrix, kit
import numpy as np
K = H.K
VH = json.load(open(os.path.join(K, "pravidla/svet/voda_hra.json")))
toky = json.load(open(os.path.join(K, "pravidla/svet/voda.json")))["toky"]
VI = H.VI; X0, Z0 = VI["x0_hra"], VI["z0_hra"]; X1, Z1 = X0 + VI["sirka"] - 2, Z0 + VI["vyska"] - 2
P = Part("voda")
for t in toky:
    b = np.array(t["body"])[:, [0, 2]]
    ins = (b[:, 0] > X0 + 2) & (b[:, 0] < X1) & (b[:, 1] > Z0 + 2) & (b[:, 1] < Z1)
    if ins.sum() < 6: continue
    idx = np.nonzero(ins)[0]; b = b[idx[0]:idx[-1] + 1]
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(b, axis=0).T))]; s = np.arange(0, seg[-1], VH["krok_m"])
    x = np.interp(s, seg, b[:, 0]); z = np.interp(s, seg, b[:, 1])
    dno = np.array([ter(a, c) for a, c in zip(x, z)])
    if dno[0] < dno[-1]: x, z, dno = x[::-1], z[::-1], dno[::-1]   # po proudu = dolů
    k = max(1, int(VH["vyhlazeni_m"] / VH["krok_m"]))
    hl = np.convolve(np.r_[[dno[0]] * k, dno, [dno[-1]] * k], np.ones(2 * k + 1) / (2 * k + 1), "same")[k:-k] + VH["hloubka_m"]
    hl = np.minimum.accumulate(hl)
    hl = np.maximum(hl, dno + VH["min_nad_dnem_m"])
    w = min(VH["sirka"]["max_m"], VH["sirka"]["zaklad_m"] + VH["sirka"]["na_odmocninu_km2"] * math.sqrt(t.get("povodi_km2", 1.0)))
    hw = w / 2 + VH["presah_m"]
    d = np.gradient(np.c_[x, z], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.c_[-d[:, 1], d[:, 0]]
    L = [(Vector((x[i] + n[i, 0] * hw, hl[i], z[i] + n[i, 1] * hw)), Vector((x[i] - n[i, 0] * hw, hl[i], z[i] - n[i, 1] * hw))) for i in range(len(x))]
    for i in range(len(x) - 1):
        a0, a1 = L[i]; b0, b1 = L[i + 1]
        P.mesh([tuple(a0), tuple(a1), tuple(b1), tuple(b0)], [(0, 1, 2, 3)], "voda", uvs=[[(s[i], 0.0), (s[i], 1.0), (s[i + 1], 1.0), (s[i + 1], 0.0)]])
    t["_osa"] = (x, z, hl, w)
    print("tok", t.get("jmeno") or "-", "délka %.0f m, šíře %.1f m, spád %.1f m" % (s[-1], w, hl[0] - hl[-1]))

# lávky: přes tok kolmo, z břehu na břeh, prkna na dvou trámech, zábradlí, kolize
for lv in VH["lavky"]:
    t = next(t for t in toky if t.get("jmeno") == lv["tok"] and "_osa" in t); x, z, hl, w = t["_osa"]
    q = np.array(lv["u_bodu"], float); i = int(np.argmin(np.hypot(x - q[0], z - q[1])))
    c = Vector((x[i], 0, z[i])); dd = Vector((x[min(i + 1, len(x) - 1)] - x[max(i - 1, 0)], 0, z[min(i + 1, len(x) - 1)] - z[max(i - 1, 0)])).normalized()
    nn = Vector((-dd.z, 0, dd.x)); half = w / 2 + lv["delka_nad_m"]
    a = c - nn * half; b = c + nn * half
    ya = ter(a.x, a.z) + 0.15; yb = ter(b.x, b.z) + 0.15; y = max(ya, yb, hl[i] + 0.5)
    for e, ye in ((a, ya), (b, yb)):   # nástupní kameny a náběh
        P.box(M(Vector((e.x, (ye + y) / 2 - 0.2, e.z)), basis=H.frame(nn)), (lv["sirka"] + 0.4, y - ye + 0.4, 0.8), "kvadr")
    kit.deck(P, a + UP * y, b + UP * y, lv["sirka"] / 2, "prkna_ven", beams=(-lv["sirka"] / 2 + 0.15, lv["sirka"] / 2 - 0.15))
    P.cols.append((M((a + b) / 2 + UP * (y - 0.1), basis=H.frame(nn)), (lv["sirka"], 0.2, (b - a).length + 1.0)))
    for sg in (-1, 1):
        o = dd * sg * (lv["sirka"] / 2 + 0.05)
        P.beam(a + o + UP * (y + 1.0), b + o + UP * (y + 1.0), 0.08, 0.1, "dub", j=0.4)
        for f in np.linspace(0, 1, 4):
            q2 = a.lerp(b, f) + o; P.beam(q2 + UP * (ter(q2.x, q2.z) - 0.3 if 0 < f < 1 else y - 0.05), q2 + UP * (y + 1.05), 0.1, 0.1, "dub", j=0.5)
        P.cols.append((M((a + b) / 2 + o + UP * (y + 0.55), basis=H.frame(nn)), (0.1, 1.1, (b - a).length)))
    lv["_konce"] = [[a.x, a.z, y], [b.x, b.z, y]]
    print("lávka", lv["id"], "délka %.1f m, výška %.2f" % ((b - a).length, y))
import bpy
R.seed(1393); H.nastav_detail(True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
H.uloz([P], "../voda", kolize=True)
json.dump({lv["id"]: lv["_konce"] for lv in VH["lavky"]}, open(os.path.join(K, "hra/data/lavky.json"), "w"))
# trasa testu průchodu přes lávku (pruchody.json píše stavitel hradu dřív – pořadí stavby: budovy → voda)
pp = os.path.join(K, "hra/data/pruchody.json"); TRp = json.load(open(pp))
for lv in VH["lavky"]:
    (ax, az, y), (bx, bz, _) = lv["_konce"]; d = np.array([bx - ax, bz - az]); d /= np.linalg.norm(d)
    TRp["trasy"]["lavka_" + lv["id"]] = [[ax - d[0] * 2.5, az - d[1] * 2.5, None], [(ax + bx) / 2, (az + bz) / 2, y + 0.05], [bx + d[0] * 2.5, bz + d[1] * 2.5, None]]
json.dump(TRp, open(pp, "w"), ensure_ascii=False)
