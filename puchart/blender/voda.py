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
TH = json.load(open(os.path.join(K, "hra/data/toky_hladina.json")))["toky"]   # hladina z nastroje/koryta.py (koryto je zaříznuté)
for ti, t in enumerate(toky):
    if str(ti) not in TH: continue
    o = np.array(TH[str(ti)]["osa"]); kk = max(1, int(round(VH["krok_m"])))
    o = np.r_[o[::kk], o[-1:]]
    x, z, hl = o[:, 0], o[:, 1], o[:, 2]
    s = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(z)))]
    w = TH[str(ti)]["sirka"]
    hw = w / 2 + VH["presah_m"]
    d = np.gradient(np.c_[x, z], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.c_[-d[:, 1], d[:, 0]]
    L = [(Vector((x[i] + n[i, 0] * hw, hl[i], z[i] + n[i, 1] * hw)), Vector((x[i] - n[i, 0] * hw, hl[i], z[i] - n[i, 1] * hw))) for i in range(len(x))]
    for i in range(len(x) - 1):
        a0, a1 = L[i]; b0, b1 = L[i + 1]
        P.mesh([tuple(a0), tuple(a1), tuple(b1), tuple(b0)], [(0, 1, 2, 3)], "voda", uvs=[[(s[i], 0.0), (s[i], 1.0), (s[i + 1], 1.0), (s[i + 1], 0.0)]])
    t["_osa"] = (x, z, hl, w)
    print("tok", t.get("jmeno") or "-", "délka %.0f m, šíře %.1f m, spád %.1f m" % (s[-1], w, hl[0] - hl[-1]))

# jemný pás břehů (voda_hra.json koryto.jemny_pas; Míša 3. 11.: hrany potoka jak pila – terén dlaždic má 2m trojúhelníky):
# síť podél osy po krok_podel_m × body_napric, výšky ze skutečného terénu (vysek.r16 = DMR 1 m s korytem) + nad_m;
# kusy po kus_m (ořez pohledem); ve hře materiál terénu, terén dlaždic je pod pásem snížen (teren_dlazdice.py)
JP = VH["koryto"]["jemny_pas"]; BR = []
for ti, t in enumerate(toky):
    if str(ti) not in TH: continue
    o = np.array(TH[str(ti)]["osa"]); w = TH[str(ti)]["sirka"]; pw = w / 2 + VH["koryto"]["prah_m"]
    off = []
    for f in JP["body_napric"]: off.append(f * pw if f <= 1.0 else pw + (f - 1.0) / (JP["body_napric"][-1] - 1.0) * VH["koryto"]["breh_m"])
    off = sorted(set([-x for x in off] + off))
    kk = max(1, int(round(JP["krok_podel_m"])))
    o = np.r_[o[::kk], o[-1:]]; x, z = o[:, 0], o[:, 1]
    d = np.gradient(np.c_[x, z], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.c_[-d[:, 1], d[:, 0]]
    s_ = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(z)))]
    kus = np.floor(s_ / JP["kus_m"]).astype(int)
    for k in range(kus.max() + 1):
        idx = np.nonzero(kus == k)[0]
        if len(idx) == 0: continue
        idx = np.r_[idx, idx[-1] + 1] if idx[-1] + 1 < len(x) else idx
        if len(idx) < 2: continue
        Pk = Part("BREH_%d_%d" % (ti, k)); V_ = []; F_ = []
        for i in idx:
            for ov in off:
                px_, pz_ = x[i] + n[i, 0] * ov, z[i] + n[i, 1] * ov
                V_.append((px_, ter(px_, pz_) + JP["nad_m"], pz_))
        m_ = len(off)
        for a in range(len(idx) - 1):
            for b in range(m_ - 1):
                i0 = a * m_ + b; F_.append((i0, i0 + 1, i0 + m_ + 1, i0 + m_))
        Pk.mesh(V_, F_, "breh_teren", smooth=True)
        BR.append(Pk)
print("jemný pás břehů: %d kusů" % len(BR))

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
H.uloz([P] + BR, "../voda", kolize=True)
json.dump({lv["id"]: lv["_konce"] for lv in VH["lavky"]}, open(os.path.join(K, "hra/data/lavky.json"), "w"))
# trasa testu průchodu přes lávku: vlastní soubor (pruchody.json píše stavitel hradu a přepisoval by ji – test smyslu trasy_pruchodu)
TRp = {}
for lv in VH["lavky"]:
    (ax, az, y), (bx, bz, _) = lv["_konce"]; d = np.array([bx - ax, bz - az]); d /= np.linalg.norm(d)
    TRp["lavka_" + lv["id"]] = [[ax - d[0] * 2.5, az - d[1] * 2.5, None], [(ax + bx) / 2, (az + bz) / 2, y + 0.05], [bx + d[0] * 2.5, bz + d[1] * 2.5, None]]
json.dump({"popis": "trasy průchodu lávkami (blender/voda.py)", "trasy": TRp}, open(os.path.join(K, "hra/data/pruchody_voda.json"), "w"), ensure_ascii=False)
