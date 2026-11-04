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
P = Part("voda"); VD = Part("VODA_DALEKO"); VJ = []
TH = json.load(open(os.path.join(K, "hra/data/toky_hladina.json")))["toky"]   # hladina z nastroje/koryta.py (koryto je zaříznuté)
# SOUTOK (Míša 4. 11.: „zub“ – přítok vtékal s jinou hladinou než hlavní tok, schod na hladině): konec (i začátek) toku,
# který leží v jiném toku, dostane jeho hladinu; náběh plynule po soutok_m metrech (nikdy proti proudu nahoru)
for k1, t1 in TH.items():
    o1 = np.array(t1["osa"], float)
    for kon in (-1, 0):
        p_ = o1[kon]; nej = None
        for k2, t2 in TH.items():
            if k2 == k1: continue
            o2 = np.array(t2["osa"], float); dd_ = np.hypot(o2[:, 0] - p_[0], o2[:, 1] - p_[1]); j = int(np.argmin(dd_))
            if dd_[j] < t2["sirka"] / 2 + t1["sirka"] / 2 + 1.5 and (nej is None or dd_[j] < nej[0]): nej = (dd_[j], float(o2[j, 2]))
        if nej is None: continue
        sv = np.r_[0, np.cumsum(np.hypot(np.diff(o1[:, 0]), np.diff(o1[:, 1])))]
        od_kon = (sv[-1] - sv) if kon == -1 else sv
        w_ = np.clip(1.0 - od_kon / VH.get("soutok_m", 8.0), 0.0, 1.0); w_ = w_ * w_ * (3 - 2 * w_)
        o1[:, 2] = o1[:, 2] * (1 - w_) + nej[1] * w_
        print("soutok: tok %s %s -> hladina %.2f (rozdíl byl %.2f m)" % (k1, "konec" if kon == -1 else "začátek", nej[1], float(p_[2]) - nej[1]))
    t1["osa"] = o1.tolist()
for ti, t in enumerate(toky):
    if str(ti) not in TH: continue
    o = np.array(TH[str(ti)]["osa"]); kk = max(1, int(round(VH["krok_m"])))
    o = np.r_[o[::kk], o[-1:]]
    x, z, hl = o[:, 0], o[:, 1], o[:, 2]
    s = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(z)))]
    w = TH[str(ti)]["sirka"]
    hw = w / 2 + VH["presah_m"]
    d = np.gradient(np.c_[x, z], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.c_[-d[:, 1], d[:, 0]]
    # jedna souvislá síť se sdílenými vrcholy a hladkým stínováním (Havran reka: dřív samostatné čtyřúhelníky = viditelné stupně),
    # 5 vrcholů napříč (v = 0..1 → hloubka v shaderu)
    # UV.y: 0 a 1 = skutečný kraj vody (šíře w), přesah za břeh má v < 0 / > 1 → shader tam hloubku 0 a průhlednost
    # (Havran: průhlednost u břehu podle hloubky – zubatý průsečík s terénem a přetečení v zatáčkách zmizí)
    VV = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]; vs_ = []; fs_ = []; us_ = []
    for i in range(len(x)):
        for v in VV:
            o = hw * (1 - 2 * v); vs_.append((x[i] + n[i, 0] * o, hl[i], z[i] + n[i, 1] * o))
    # UV.y = skutečná hloubka vody nad viditelným terénem v tom vrcholu (Havran reka_bake: COLOR.r = hloubka) – shader podle ní
    # barví a u břehu plynule zprůhlední; průsečík roviny vody se šikmým břehem (zuby po 1 m) tak není vidět
    hloubky = [max(0.0, vs_[q][1] - float(ter(vs_[q][0], vs_[q][2]))) for q in range(len(vs_))]
    m5 = len(VV)
    for i in range(len(x) - 1):
        for j in range(m5 - 1):
            a = i * m5 + j; fs_.append((a, a + m5, a + 1 + m5, a + 1))   # normála nahoru (shader cull_back)
            us_.append([(s[i], hloubky[a]), (s[i + 1], hloubky[a + m5]), (s[i + 1], hloubky[a + 1 + m5]), (s[i], hloubky[a + 1])])
    # jemná hladina je na mřížce jemného pásu (níž, jen do jemny_pas.dosah_kresleni_m); dál jednoduchý pás po 4 m (VODA_DALEKO)
    vs2 = []; fs2 = []; us2 = []; st = 2
    ii = list(range(0, len(x), st)) + ([len(x) - 1] if (len(x) - 1) % st else [])
    for i in ii:
        for o in (hw, -hw): vs2.append((x[i] + n[i, 0] * o, hl[i] - 0.03, z[i] + n[i, 1] * o))
    for k in range(len(ii) - 1):
        a = 2 * k; fs2.append((a, a + 2, a + 3, a + 1)); us2.append([(s[ii[k]], 0.0), (s[ii[k + 1]], 0.0), (s[ii[k + 1]], 0.3), (s[ii[k]], 0.3)])
    VD.mesh(vs2, fs2, "voda", uvs=us2)
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
        for a in range(len(idx) - 1):   # trojúhelníky výslovně (stejná úhlopříčka jako hladina)
            for b in range(m_ - 1):
                i0 = a * m_ + b; F_ += [(i0, i0 + 1, i0 + m_ + 1), (i0, i0 + m_ + 1, i0 + m_)]
        Pk.mesh(V_, F_, "breh_teren", smooth=True)
        # HLADINA na téže mřížce (Míša 4. 11.: „má to zuby a hladina je přerušena“ – hladina měla mřížku 2 m a jiné body napříč,
        # průsečík dvou triangulací byl pila): vrcholy nad vrcholy břehu, UV.y = hloubka nad nimi (0 na břehu → průhlednost)
        hlr = o[:, 2]; VW = []; UW = []
        sl = [b for b, ov in enumerate(off) if abs(ov) <= pw + 1.3]
        for a, i in enumerate(idx):
            for b in sl: VW.append((V_[a * m_ + b][0], hlr[i], V_[a * m_ + b][2]))
        mw = len(sl); FW = []; UWf = []
        for a in range(len(idx) - 1):
            for bi in range(mw - 1):
                q = [(a, sl[bi]), (a, sl[bi + 1]), (a + 1, sl[bi + 1]), (a + 1, sl[bi])]
                hq = [max(0.0, hlr[idx[aa]] - V_[aa * m_ + bb][1]) for aa, bb in q]
                if max(hq) <= 0.0: continue   # celý čtverec nad vodou
                j0 = a * mw + bi; tri = [(j0, j0 + 1, j0 + mw + 1, (0, 1, 2)), (j0, j0 + mw + 1, j0 + mw, (0, 2, 3))]
                for t0, t1, t2, kk_ in tri:
                    FW.append((t0, t1, t2)); UWf.append([(s_[idx[q[k_][0]]], hq[k_]) for k_ in kk_])
        if FW:   # po kusech jako břeh (dosah kreslení podle vzdálenosti kusu, ne celé sítě všech potoků)
            Pw = Part("VODA_%d_%d" % (ti, k)); Pw.mesh(VW, FW, "voda", uvs=UWf, smooth=True); VJ.append(Pw)
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
H.uloz([P, VD] + VJ + BR, "../voda", kolize=True)
json.dump({lv["id"]: lv["_konce"] for lv in VH["lavky"]}, open(os.path.join(K, "hra/data/lavky.json"), "w"))
# trasa testu průchodu přes lávku: vlastní soubor (pruchody.json píše stavitel hradu a přepisoval by ji – test smyslu trasy_pruchodu)
TRp = {}
for lv in VH["lavky"]:
    (ax, az, y), (bx, bz, _) = lv["_konce"]; d = np.array([bx - ax, bz - az]); d /= np.linalg.norm(d)
    TRp["lavka_" + lv["id"]] = [[ax - d[0] * 2.5, az - d[1] * 2.5, None], [(ax + bx) / 2, (az + bz) / 2, y + 0.05], [bx + d[0] * 2.5, bz + d[1] * 2.5, None]]
json.dump({"popis": "trasy průchodu lávkami (blender/voda.py)", "trasy": TRp}, open(os.path.join(K, "hra/data/pruchody_voda.json"), "w"), ensure_ascii=False)
