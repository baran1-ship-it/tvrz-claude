"""Potoky ve hře (pravidla/svet/voda_hra.json): hladina jako pás podél osy toku z pravidla/svet/voda.json, lávka u brodu.
Výška hladiny = dno údolnice (herní terén pod osou, vyhlazené po délce) + hloubka, pak po proudu nikdy nestoupá; kde by
klesla pod dno o víc než min_nad_dnem, zvedne se (krátké prahy). Okraje pásu přesahují břehy – terén je schová.
Pás má UV: u = vzdálenost po proudu (m), v = 0..1 napříč (shader: proud, okraje). Výstup hra/modely/voda.glb (+KOLIZE).
  /opt/bl/bin/python blender/voda.py <koren_puchartu>
"""
import sys, math, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrady as H
from hrady import Part, M, R, ter, UP, Vector, Matrix, kit
import numpy as np
K = H.K
VH = json.load(open(os.path.join(K, "pravidla/svet/voda_hra.json")))
CESTY = [c_ for c_ in json.load(open(os.path.join(K, "pravidla/svet/cesty_puchart.json")))["cesty"] if c_.get("typ") == "vozova"]
toky = json.load(open(os.path.join(K, "pravidla/svet/voda.json")))["toky"]
VI = H.VI; X0, Z0 = VI["x0_hra"], VI["z0_hra"]; X1, Z1 = X0 + VI["sirka"] - 2, Z0 + VI["vyska"] - 2
P = Part("voda"); VD = Part("VODA_DALEKO"); VJ = []; VDK = []
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
    # po kusech (Míša 4. 11.: dvoubarevná hladina – jeden pás přes všechny toky měl střed daleko, visibility_range ho kreslil i
    # vedle jemné hladiny); kus = kus_m po proudu jako jemná hladina
    KM_ = VH["koryto"]["jemny_pas"]["kus_m"]; kus2 = [int(s[ii[k]] // KM_) for k in range(len(ii) - 1)]
    for kk in sorted(set(kus2)):
        sel = [k for k in range(len(ii) - 1) if kus2[k] == kk]
        Pd = Part("VODA_DALEKO_%d_%d" % (ti, kk)); vmap = {}; vv = []; ff = []; uu = []
        for k in sel:
            q = []
            for vi in (2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1):
                if vi not in vmap: vmap[vi] = len(vv); vv.append(vs2[vi])
                q.append(vmap[vi])
            ff.append(tuple(q)); uu.append(us2[k])
        Pd.mesh(vv, ff, "voda", uvs=uu); VDK.append(Pd)
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
                if max(hq) <= 0.0 and min(abs(off[bb]) for _, bb in q) > w * 0.3: continue   # celý čtverec nad vodou (střed toku vždy – Míša 5. 11.: „někde chybí voda“)
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
# mosty údolní cesty (Míša 5. 11.: dřevěné, hezké): kamenné opěry na březích, pilotová jařma po jarmo_po_m (rešerše: Lednica,
# Havran Most_potok), 4 podélné trámy, mostovka z fošen napříč, zábradlí (sloupky + madlo + střední tyč), kolize desky a zábradlí
for mo in VH.get("mosty", []):
    t = next((t for t in toky if t.get("jmeno") == mo["tok"] and "_osa" in t), None)
    if t is None: continue
    x, z, hl, w = t["_osa"]; q = np.array(mo["u_bodu"], float); i = int(np.argmin(np.hypot(x - q[0], z - q[1])))
    if np.hypot(x[i] - q[0], z[i] - q[1]) > 25: continue
    c = Vector((x[i], 0, z[i])); dd = Vector((x[min(i + 2, len(x) - 1)] - x[max(i - 2, 0)], 0, z[min(i + 2, len(x) - 1)] - z[max(i - 2, 0)])).normalized()
    nn = Vector((-dd.z, 0, dd.x)); half = w / 2 + mo["delka_nad_m"]
    # osa mostu = osa cesty (Havran kraj.py Most_potok + most_napojeni.py; Míša 6. 11.: „napojení na cestu je hrůza“): konce
    # přerušené cesty u mostu (do 12 m) jsou konce mostovky – most leží v ose cesty, cesta na něj navazuje rovně
    konce = []
    for cs_ in CESTY:
        o_ = cs_["osa"]
        for e_, e2_ in ((o_[0], o_[min(2, len(o_) - 1)]), (o_[-1], o_[max(-3, -len(o_))])):
            if math.hypot(e_[0] - q[0], e_[1] - q[1]) < 12.0: konce.append((Vector((e_[0], 0, e_[1])), Vector((e_[0] - e2_[0], 0, e_[1] - e2_[1])).normalized()))
    if len(konce) >= 2:
        a, b = konce[0][0], konce[1][0]; nn = (b - a).normalized()
    elif len(konce) == 1:   # cesta jen z jedné strany: most v jejím směru přes tok
        nn = konce[0][1]; a = konce[0][0]; b = a + nn * max(2 * half, 2 * abs((c - a).dot(nn)))
    else:
        a = c - nn * half; b = c + nn * half
    dd = Vector((-nn.z, 0, nn.x))   # napříč mostem
    L = (b - a).length; W2 = mo["sirka"] / 2
    # výška konce = nejvyšší terén kolem konce cesty (konec ležel v zářezu koryta – mostovka pod okrajem břehu, test povrch_kolize)
    ya = max(ter(*(a + nn * k_ + dd * w_).xz) for k_ in (-1.5, -0.75, 0.0) for w_ in (-1.0, 0.0, 1.0))
    yb = max(ter(*(b + nn * k_ + dd * w_).xz) for k_ in (0.0, 0.75, 1.5) for w_ in (-1.0, 0.0, 1.0))
    # mostovka sklonem z konce cesty na konec cesty (dřív vodorovně ve výšce vyššího břehu – u nižšího konce 2 m násyp, Míša 6. 11.),
    # nad hladinou aspoň 0,6 m, sklon nejvýš 10 %
    yA = max(ya, hl[i] + 0.6) + 0.1; yB = max(yb, hl[i] + 0.6) + 0.1
    if abs(yB - yA) > 0.1 * L:
        if yA < yB: yA = yB - 0.1 * L
        else: yB = yA - 0.1 * L
    y = max(yA, yB)
    def Y(q_, dy=0.0): f_ = max(0.0, min(1.0, (q_ - a).dot(nn) / L)); return yA + (yB - yA) * f_ + dy
    for e, ye, sg_, y in ((a, ya, -1, yA), (b, yb, 1, yB)):   # opěry dřevěné (Havran kraj.py ř. 1429–1479): zatlučené kulatiny a fošny držící hlínu násypu
        for k_ in range(7):
            q_ = e + dd * (-W2 - 0.25 + (2 * W2 + 0.5) * k_ / 6) + nn * (-sg_ * 0.15)
            if y - 0.32 < ter(q_.x, q_.z) + 0.1: continue   # kulatina celá v zemi (pod_terenem_voda)
            P.beam(q_ + UP * (min(ye, ter(q_.x, q_.z)) - 0.6), q_ + UP * (y - 0.32), 0.24, 0.24, "dub", up=nn, j=0.4, collide=None)
        for yy_ in np.arange(min(ye, y) - 0.6, y - 0.3, 0.26):   # vodorovné fošny za kulatinami (celé pod terénem se nestaví – pod_terenem_voda)
            if yy_ + 0.12 < min(ter(*(e + dd * k_).xz) for k_ in np.linspace(-W2 - 0.35, W2 + 0.35, 7)) + 0.1: continue
            P.beam(e + dd * (-W2 - 0.35) + nn * (sg_ * 0.02) + UP * yy_, e + dd * (W2 + 0.35) + nn * (sg_ * 0.02) + UP * yy_, 0.06, 0.24, "prkna_ven", up=nn, j=0.3, collide=None)
    for sv in (-1.2, -0.4, 0.4, 1.2):   # podélné trámy
        P.beam(a + dd * sv + UP * (yA - 0.2), b + dd * sv + UP * (yB - 0.2), 0.26, 0.3, "dub", j=0.6)
    kit.deck(P, a + UP * yA, b + UP * yB, W2, "prkna_ven", beams=())
    nj = max(0, int(L / mo["jarmo_po_m"]) - 1)
    for k in range(nj):   # jařma v korytě: 2 piloty + příčný trám (Lednica: svazky pilot spojené jařmovým trámem)
        f = (k + 1) / (nj + 1); q2 = a.lerp(b, f)
        for sv in (-W2 + 0.3, W2 - 0.3):
            g = q2 + dd * sv
            if Y(q2, -0.32) < ter(g.x, g.z) + 0.1: continue   # pilota celá v zemi (most šikmo přes břeh – pod_terenem_voda)
            P.beam(g + UP * (ter(g.x, g.z) - 0.6), g + UP * Y(q2, -0.32), 0.24, 0.24, "dub", up=nn, j=0.5)
        if Y(q2, -0.34) > min(ter(*(q2 + dd * k_).xz) for k_ in (-W2 - 0.2, 0.0, W2 + 0.2)):
            P.beam(q2 - dd * (W2 + 0.2) + UP * Y(q2, -0.47), q2 + dd * (W2 + 0.2) + UP * Y(q2, -0.47), 0.28, 0.26, "dub", j=0.5)
    for sg in (-1, 1):   # zábradlí
        o = dd * sg * (W2 + 0.05)
        P.beam(a + o + UP * (yA + 1.0), b + o + UP * (yB + 1.0), 0.12, 0.12, "dub", j=0.4, collide=None)
        P.beam(a + o + UP * (yA + 0.5), b + o + UP * (yB + 0.5), 0.07, 0.09, "dub", j=0.4, collide=None)
        for f in np.linspace(0, 1, max(3, int(L / 1.8) + 1)):
            q2 = a.lerp(b, f) + o; P.beam(q2 + UP * Y(q2, -0.05), q2 + UP * Y(q2, 1.05), 0.12, 0.12, "dub", up=nn, j=0.5, collide=None)
        skl_ = math.atan2(yB - yA, L); bz_ = H.frame(nn) @ Matrix.Rotation(-skl_, 3, "X")
        P.cols.append((M((a + b) / 2 + o + UP * ((yA + yB) / 2 + 0.55), basis=bz_), (0.12, 1.1, L / math.cos(skl_))))
    P.cols.append((M((a + b) / 2 + UP * ((yA + yB) / 2 - 0.1), basis=H.frame(nn) @ Matrix.Rotation(-math.atan2(yB - yA, L), 3, "X")), (W2 * 2, 0.2, math.hypot(L, yB - yA) + 0.02)))   # jen nad mostovkou: přesah 0,5 m stál nad rampou jako schod 0,26 m (hlídač 5. 11.)
    for e, sg, y in ((a, -1, yA), (b, 1, yB)):   # nájezd z terénu na mostovku (hlídač 5. 11.: hrana zastavila postavu): šikmá kolize + kamenné stupně
        ven = nn * sg; Ln = 1.0
        for _ in range(3):   # pata rampy na terénu v místě paty (svah břehu: odhad z blízkého terénu nechal patu viset – hlídač 5. 11.)
            g0 = min(ter(*(e + ven * k).xz) for k in (0.0, Ln * 0.5, Ln)); sp = y - g0 + 0.1   # i u konce mostu (prohlubeň u břehu)
            Ln = max(1.2, sp / 0.16)   # násyp ~9° (vůz vyjede; dřív schody 28°)
        if sp <= 0.05: continue
        sk = math.atan2(sp, Ln); bas = H.frame(-ven) @ Matrix.Rotation(-sk, 3, "X"); Lb = Ln + 0.5; tg_ = sp / Ln
        # horní hrana rampy přesně v konci mostovky ve výšce mostovky (dřív rampa začínala 0,3 m před koncem a přečnívala
        # nad mostovku o 0,2 m – hrb, postava uvízla, hlídač 5. 11.); dole 0,5 m pod terén
        P.cols.append((M(e + ven * (Lb / 2) + UP * (y - 0.04 - tg_ * Lb / 2 - 0.1 / math.cos(sk)), basis=bas), (W2 * 2 + 0.8, 0.2, Lb / math.cos(sk))))   # šířka a výška jako viditelný násyp (boření 0,22 m na okraji)
        # nájezd = násyp z hlíny (Havran: násyp za opěrou, svahy 1:2,5) místo kamenných stupňů (Míša 6. 11.: jen dřevěné mosty)
        PN = Part("BREH_nasyp_%s_%d" % (mo["id"], sg)); BR.append(PN)   # BREH_*: ve hře materiál terénu (navazuje na cestu i trávu)
        Wn = W2 + 0.4; n_ = max(2, int(Ln / 0.6) + 1)   # klín násypu jako jedna síť: horní plocha z mostovky do terénu, boky svahem 1:1
        for k in range(n_):
            t0_, t1_ = Ln * k / n_, Ln * (k + 1) / n_
            vs_ = []
            for t_ in (t0_, t1_):
                c2 = e + ven * t_; top = y - 0.04 - sp * t_ / Ln
                for sv_ in (-1, 1):
                    q_ = c2 + dd * sv_ * Wn; g_ = ter(q_.x, q_.z) - 0.2
                    q2_ = c2 + dd * sv_ * (Wn + max(0.0, top - g_)); g2_ = ter(q2_.x, q2_.z) - 0.2
                    vs_.append((q_ + UP * top, q2_ + UP * min(g2_, top)))   # vrch přesně jako kolize (dřív zvednutý k terénu břehu – boření 0,25 m)
            (a0, a0b), (b0, b0b), (a1, a1b), (b1, b1b) = vs_
            PN.mesh([tuple(a0), tuple(b0), tuple(b1), tuple(a1)], [(0, 3, 2, 1)], "breh")       # vrch násypu
            PN.mesh([tuple(a0), tuple(a1), tuple(a1b), tuple(a0b)], [(0, 1, 2, 3)], "breh")     # svah vlevo
            PN.mesh([tuple(b0), tuple(b0b), tuple(b1b), tuple(b1)], [(0, 1, 2, 3)], "breh")     # svah vpravo
    mo["_konce"] = [[a.x, a.z, yA], [b.x, b.z, yB]]
    print("most", mo["id"], "délka %.1f m, výška %.2f, jařem %d, konce %.2f %.2f, hladina %.2f" % (L, max(yA, yB), nj, ya, yb, hl[i]))
# brody (Havran: cesty.json prechody druh brod, _brody ř. 9403, uprava_y): kde osa cesty kříží tok a není tam most –
# štěrk plochých kamenů přes koryto (pás 4 m), šlapáky z droby těsně nad hladinou, pás bez křoví (stavby_vegetace)
# (Míša 6. 11.: „brody máš zarostlé křovím a nevypadá to jako brod“)
import random as _rnd
_rg = _rnd.Random(1393); BRODY = []
VSE_CESTY = json.load(open(os.path.join(K, "pravidla/svet/cesty_puchart.json")))["cesty"]
for t in toky:
    if "_osa" not in t: continue
    x, z, hl, w = t["_osa"]; P_ = np.c_[x, z]
    for cs_ in VSE_CESTY:
        o_ = np.array(cs_["osa"], float)
        if len(o_) < 2: continue
        for j_ in range(len(o_) - 1):
            p0_, p1_ = o_[j_, :2], o_[j_ + 1, :2]; dl_ = np.linalg.norm(p1_ - p0_)
            if dl_ < 0.1: continue
            for f_ in np.arange(0, 1, 0.5 / dl_):
                q_ = p0_ + (p1_ - p0_) * f_; dd_ = np.hypot(x - q_[0], z - q_[1]); i_ = int(np.argmin(dd_))
                if dd_[i_] < 2.0:
                    if any(np.hypot(b_[0] - q_[0], b_[1] - q_[1]) < 15 for b_ in BRODY): break
                    if any(np.hypot(m_["u_bodu"][0] - q_[0], m_["u_bodu"][1] - q_[1]) < 25 for m_ in VH.get("mosty", [])): break
                    BRODY.append((float(q_[0]), float(q_[1]), float(hl[i_]), float(w[i_]), (p1_ - p0_) / dl_, cs_["id"], t.get("jmeno", "")))
                    break
for (bx, bz, bh, bw, bd, cid, tj) in BRODY:
    c = Vector((bx, 0, bz)); dcs = Vector((bd[0], 0, bd[1])); dn = Vector((-dcs.z, 0, dcs.x))
    Pb = Part("brod_%d_%d" % (round(bx), round(bz)))
    for a_ in np.arange(-bw / 2 - 1.5, bw / 2 + 1.5, 0.45):   # podél cesty přes koryto
        for b_ in np.arange(-2.0, 2.01, 0.5):                  # napříč (šířka brodu 4 m)
            q_ = c + dcs * (a_ + _rg.uniform(-0.15, 0.15)) + dn * (b_ + _rg.uniform(-0.15, 0.15)); g_ = ter(q_.x, q_.z)
            sz_ = _rg.uniform(0.18, 0.34)
            kit.stone(Pb, M(q_ + UP * (max(g_, bh - 0.12) - 0.02), _rg.uniform(0, 180)), (sz_, 0.07, sz_ * _rg.uniform(0.7, 1.0)), "sut", cham=0.02, rough=0.01)
    for a_ in np.arange(-bw / 2 + 0.2, bw / 2, 0.6):   # šlapáky uprostřed
        q_ = c + dcs * a_ + dn * _rg.uniform(-0.6, 0.6)
        kit.stone(Pb, M(q_ + UP * (bh - 0.05), _rg.uniform(0, 180)), (0.5, 0.18, 0.4), "skala", cham=0.04, rough=0.02)
    BR.append(Pb)
    print("brod", cid, tj, "(%.0f, %.0f) šířka toku %.1f m" % (bx, bz, bw))
json.dump({"popis": "brody: křížení cesty s tokem bez mostu (blender/voda.py)", "brody": [{"stred": [b_[0], b_[1]], "smer": [float(b_[4][0]), float(b_[4][1])], "sirka_toku": b_[3], "cesta": b_[5], "tok": b_[6]} for b_ in BRODY]},
          open(os.path.join(K, "hra/data/brody.json"), "w"), ensure_ascii=False)
import bpy
R.seed(1393); H.nastav_detail(True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
H.uloz([P] + VDK + VJ + BR, "../voda", kolize=True)
json.dump({lv["id"]: lv["_konce"] for lv in VH["lavky"]}, open(os.path.join(K, "hra/data/lavky.json"), "w"))
# trasa testu průchodu přes lávku: vlastní soubor (pruchody.json píše stavitel hradu a přepisoval by ji – test smyslu trasy_pruchodu)
TRp = {}
for lv in VH["lavky"] + [m_ for m_ in VH.get("mosty", []) if "_konce" in m_]:
    (ax, az, y), (bx, bz, y2_) = lv["_konce"]; y = (y + y2_) / 2; d = np.array([bx - ax, bz - az]); d /= np.linalg.norm(d)   # střed mostovky (sklon)
    TRp["lavka_" + lv["id"]] = [[ax - d[0] * 2.5, az - d[1] * 2.5, None], [(ax + bx) / 2, (az + bz) / 2, y + 0.05], [bx + d[0] * 2.5, bz + d[1] * 2.5, None]]
json.dump({"popis": "trasy průchodu lávkami (blender/voda.py)", "trasy": TRp}, open(os.path.join(K, "hra/data/pruchody_voda.json"), "w"), ensure_ascii=False)
