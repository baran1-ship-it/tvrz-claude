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
def _smin(a, b, k):   # hladké minimum (polynom, Quilez): přechod šířky ~k bez lomu – zaoblení brodu
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
def _smax(a, b, k): return -_smin(-a, -b, k)
from scipy.ndimage import gaussian_filter as _gauss
_YSM = _gauss(Y0, KO["brod"].get("vyhlazeni_terenu_m", 2.0) / M.get("krok_m", 1.0)) if KO.get("brod") else Y0   # terén pro nájezd brodu bez hrbolů 1 m
DRUH = np.zeros(Y.shape, np.uint8); VODA = []
# BRODY (voda_hra.json koryto.brod; Havran kraj.py voda_tvar): cesta kříží tok bez mostu – konec cesty u toku a protější
# cesta do mezera_cest_m, spojnice kříží osu toku. Tam mělké koryto a nájezdy k vodě místo prahu a svahu břehu.
BR_ = KO.get("brod"); _CES = json.load(open(K + "/pravidla/svet/cesty_puchart.json"))["cesty"]
_MOSTY = [m_["u_bodu"] for m_ in VH.get("mosty", [])]
def _husta_(o):
    o = np.array(o, float)[:, :2]; d_ = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]; s_ = np.arange(0, d_[-1] + 0.01, 0.5)
    return np.c_[np.interp(s_, d_, o[:, 0]), np.interp(s_, d_, o[:, 1])]
_HD = [_husta_(c_["osa"]) for c_ in _CES if len(c_["osa"]) >= 2]
_HT = [c_.get("typ") == "vozova" for c_ in _CES if len(c_["osa"]) >= 2]   # vozová (vůz projede) / jen pěší
# úsečky, po kterých cesta ve hře vede: osy cest, spojky (nastroje/cesty.py: konec → nejbližší bod jiné cesty 1,5–25 m)
# a dvojice konců na protějších březích (blender/voda.py brody: 2–30 m)
_USEKY = [(h_[i_], h_[i_ + 1]) for h_ in _HD for i_ in range(len(h_) - 1)]
_UVOZ = [v_ for h_, v_ in zip(_HD, _HT) for i_ in range(len(h_) - 1)]
for i_, h_ in enumerate(_HD):
    for k_ in (0, -1):
        p_ = h_[k_]; best_ = None
        for j_, q_ in enumerate(_HD):
            if j_ == i_: continue
            dd_ = np.hypot(q_[:, 0] - p_[0], q_[:, 1] - p_[1]); m_ = int(dd_.argmin())
            if best_ is None or dd_[m_] < best_[0]: best_ = (float(dd_[m_]), q_[m_], j_)
            for k2_ in (0, -1):
                if 2 < float(np.hypot(*(q_[k2_] - p_))) < BR_["mezera_cest_m"][1]: _USEKY.append((p_, q_[k2_])); _UVOZ.append(_HT[i_] and _HT[j_])
        if best_ and BR_["mezera_cest_m"][0] < best_[0] < 25: _USEKY.append((p_, best_[1])); _UVOZ.append(_HT[i_] and _HT[best_[2]])
_UA = np.array([u_[0] for u_ in _USEKY]); _UB = np.array([u_[1] for u_ in _USEKY]); _UV = np.array(_UVOZ, bool)
_BROD_VOZ = {}   # (x, z) brodu -> vozová cesta (vůz) / jen pěší (US Army tab. 1-3: pěší nájezd do 100 %)
def _brody_toku(x, z, w):
    """indexy bodů osy toku, kde ji kříží cesta (osa, spojka nebo dvojice konců) a není tam most"""
    if not BR_: return []
    ven = []
    for i_ in range(len(x) - 1):
        a_ = np.array([x[i_], z[i_]]); r_ = np.array([x[i_ + 1] - x[i_], z[i_ + 1] - z[i_]])
        s_ = _UB - _UA; qp_ = _UA - a_
        rxs = r_[0] * s_[:, 1] - r_[1] * s_[:, 0]; ok_ = np.abs(rxs) > 1e-9
        t_ = np.where(ok_, (qp_[:, 0] * s_[:, 1] - qp_[:, 1] * s_[:, 0]) / np.where(ok_, rxs, 1), -1)
        u_ = np.where(ok_, (qp_[:, 0] * r_[1] - qp_[:, 1] * r_[0]) / np.where(ok_, rxs, 1), -1)
        hit_ = (t_ >= 0) & (t_ <= 1) & (u_ >= 0) & (u_ <= 1)
        if not np.any(hit_): continue
        if any(math.hypot(x[i_] - m_[0], z[i_] - m_[1]) < BR_["od_mostu_m"] for m_ in _MOSTY): continue
        if any(abs(i_ - b_) * KO["krok_osy_m"] < 15 for b_ in ven): continue
        ven.append(i_); _BROD_VOZ[(round(float(x[i_]), 3), round(float(z[i_]), 3))] = bool(np.any(hit_ & _UV))
    return ven
for ti, t in enumerate(toky):
    b = np.array(t["body"], float)[:, [0, 2]]
    ins = (b[:, 0] > x0 + 3) & (b[:, 0] < x0 + nx - 3) & (b[:, 1] > z0 + 3) & (b[:, 1] < z0 + ny - 3)
    if ins.sum() < 6: continue
    idx = np.nonzero(ins)[0]; b = b[idx[0]:idx[-1] + 1]
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(b, axis=0).T))]; s = np.arange(0, seg[-1], KO["krok_osy_m"])
    x = np.interp(s, seg, b[:, 0]); z = np.interp(s, seg, b[:, 1])
    # osa DIBAVOD se po metrech klikatí; zářez sousedního cik-caku snižoval břeh pod hladinu (voda_v_korytu) → vyhladit
    from scipy.ndimage import gaussian_filter1d
    sg_ = KO.get("vyhlazeni_osy_m", 0) / KO["krok_osy_m"]
    if sg_ > 0: x = gaussian_filter1d(x, sg_, mode="nearest"); z = gaussian_filter1d(z, sg_, mode="nearest")
    w = min(VH["sirka"]["max_m"], VH["sirka"]["zaklad_m"] + VH["sirka"]["na_odmocninu_km2"] * math.sqrt(t.get("povodi_km2", 1.0)))
    d = np.gradient(np.c_[x, z], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.c_[-d[:, 1], d[:, 0]]
    dno = np.min([ter(x + n[:, 0] * o, z + n[:, 1] * o) for o in np.linspace(-w, w, 7)], axis=0)
    # nejnižší břeh (kraj vody + práh): hladina nad ním by visela jako plachta (test smyslu voda_v_korytu, 2. 11.)
    bm = w / 2 + KO["prah_m"] + KO.get("breh_kontrola_m", 0.8)
    breh_min = np.minimum(ter(x + n[:, 0] * bm, z + n[:, 1] * bm), ter(x - n[:, 0] * bm, z - n[:, 1] * bm))
    if dno[0] < dno[-1]: x, z, dno, n, breh_min = x[::-1], z[::-1], dno[::-1], -n[::-1], breh_min[::-1]
    k = max(1, int(VH["vyhlazeni_m"] / KO["krok_osy_m"]))
    hl = np.convolve(np.r_[[dno[0]] * k, dno, [dno[-1]] * k], np.ones(2 * k + 1) / (2 * k + 1), "same")[k:-k]
    hl = np.minimum(np.minimum.accumulate(hl), np.minimum(dno + 0.05, np.maximum(breh_min - KO.get("pod_brehem_m", 0.1), dno - KO.get("max_pod_dnem_m", 0.3))))
    # nestoupá, ne nad údolnicí, ne nad nižším břehem – ale kvůli břehu nejvýš max_pod_dnem pod dno (jinak zářez 4 m a stěna 12 m, test teren_skoky)
    hl = np.minimum.accumulate(hl)
    # plošiny a skoky z minimum.accumulate = terasy na hladině (Míša 4. 11.: „voda divná“); Havran koryto.gd: hladina vyhlazená
    # a nikdy nestoupá – skok rozložit do rampy (jen snížení, horní meze z břehu a údolnice zůstanou splněné)
    from scipy.ndimage import gaussian_filter1d as _gf
    hl = np.minimum.accumulate(np.minimum(hl, _gf(hl, KO.get("rampa_hladiny_m", 4.0) / KO["krok_osy_m"], mode="nearest")))
    hv = KO["hloubka_vody_m"]["zaklad"] + KO["hloubka_vody_m"]["na_m_sirky"] * w
    # buňky v dosahu osy
    strom = cKDTree(np.c_[x, z]); R = w / 2 + KO["prah_m"] + KO["dosah_m"]
    brody_ = _brody_toku(x, z, w); R0 = R
    if brody_: R = max(R, w / 2 + BR_["dosah_m"])   # nájezd k brodu sahá dál než běžný břeh (jen v pásu brodu, níž Rc)
    c0_, c1_ = int(max(0, x.min() - R - x0)), int(min(nx, x.max() + R - x0 + 1)); r0_, r1_ = int(max(0, z.min() - R - z0)), int(min(ny, z.max() + R - z0 + 1))
    cx, cz = np.meshgrid(x0 + np.arange(c0_, c1_), z0 + np.arange(r0_, r1_))
    dist, j = strom.query(np.c_[cx.ravel(), cz.ravel()], distance_upper_bound=R)
    ok = np.isfinite(dist); dist = np.where(ok, dist, R); j = np.minimum(j, len(x) - 1)
    hlj = hl[j]
    # šíře koryta se mění (Míša 4. 11.: „koryto okolo vody není nic moc“ – rovný kanál; docs/reference/detaily_hradu_1393.md §9:
    # hladina 0,5–2,5 m se mění, střídání tůní a peřejí po 2–5 šířkách): dvě vlny s náhodnou fází po délce toku
    VK = KO.get("kolisani_sirky", {"amp": 0.0}); s_ax = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(z)))]
    rg_ = np.random.default_rng(1000 + ti); f1, f2 = rg_.uniform(0, 2 * np.pi, 2)
    fsir = 1 + VK["amp"] * (0.6 * np.sin(2 * np.pi * s_ax / (VK.get("vlna1_sirek", 4.0) * w) + f1) + 0.4 * np.sin(2 * np.pi * s_ax / (VK.get("vlna2_sirek", 9.0) * w) + f2))
    pw = (w / 2) * fsir[j]
    prof = np.where(dist < pw, hlj - hv * (1 - (dist / pw) ** 2),
           np.where(dist < pw + KO["prah_m"], hlj + KO["prah_nad_hladinou_m"] * (dist - pw) / KO["prah_m"],
                    hlj + KO["prah_nad_hladinou_m"] + (dist - pw - KO["prah_m"]) * KO["sklon_svahu"]))
    wb = np.zeros_like(dist); dist_b = dist; brody_tvar = []; wbax = np.zeros(len(x)); brehax = np.zeros(len(x))
    if brody_:
        # BROD podle rešerše (docs/reference/brody/README.md, Míša 13. 11.: „příkop s hrbem“): mělká rozlitá plocha – voda
        # rozliti_sirky × šíře koryta, ploché dno hloubka_m pod hladinou, nájezd sklon_najezdu až na původní terén (délka =
        # výška břehu / sklon), lomy zaoblené (zaobleni_m, Clarkin 2006 „gentle vertical curve“), bez prahu břehu. Pás brodu
        # = vzdálenost od přímky přes brod kolmo na tečnu toku (polosirka_m + náběh nabeh_m); napříč se měří po kolmici brodu
        # (ne k zakřivené ose – na 20 m by skákala k jinému oblouku). Terén v pásu smí i zvednout (dno brodu je zvýšené,
        # River Cole +0,3 m; zasypané díry nájezdu), ale ne přes koryto jiného toku (jen nezměněné buňky).
        pc_ = np.c_[cx.ravel(), cz.ravel()]; sk_ = BR_["sklon_najezdu"]; kz_ = sk_ * BR_["zaobleni_m"] / 2
        Ysm_ = map_coordinates(_YSM, [cz.ravel() - z0, cx.ravel() - x0], order=1, mode="nearest")
        pwb_ = (w / 2) * BR_["rozliti_sirky"]; pb = np.full(dist.shape, 1e9); acr_ = np.full(dist.shape, 1e9); rx_ = np.zeros(dist.shape); vl_ = np.ones(dist.shape, bool)
        for b_ in brody_:
            tg_ = np.array([x[min(b_ + 2, len(x) - 1)] - x[max(b_ - 2, 0)], z[min(b_ + 2, len(z) - 1)] - z[max(b_ - 2, 0)]]); tg_ /= np.linalg.norm(tg_) + 1e-9
            nb_ = np.array([-tg_[1], tg_[0]]); rel_ = pc_ - np.array([x[b_], z[b_]])
            ds_ = np.abs(rel_ @ tg_); ac_ = np.abs(rel_ @ nb_)
            ds_ = np.where(ac_ < BR_["dosah_m"] + w, ds_, 1e9)
            # buňka u jiného oblouku téhož toku (nejbližší bod osy dál po proudu než pás brodu): brod tam jen snižuje, koryto zůstane
            vl_i = np.abs(s_ax[j] - s_ax[b_]) < BR_["polosirka_m"] + BR_["nabeh_m"] + 2
            wbi = np.clip(1 - (ds_ - BR_["polosirka_m"]) / BR_["nabeh_m"], 0, 1); wbi = wbi * wbi * (3 - 2 * wbi)
            low_ = _smax(hl[b_] - BR_["hloubka_m"], hl[b_] + sk_ * (ac_ - pwb_), kz_)   # ploché dno → zaoblení → nájezd
            pbi = _smin(low_, Ysm_, kz_)   # nájezd → zaoblení → původní terén (vyhlazený, bez děr a hrbolů)
            lep_ = wbi > wb; wb = np.where(lep_, wbi, wb); pb = np.where(lep_, pbi, pb); acr_ = np.where(lep_, ac_, acr_); vl_ = np.where(lep_, vl_i, vl_)
            # kde nájezd dosedne na terén (obě strany): do té vzdálenosti jemný pás břehů (voda.py BREH) a jemné buňky
            aa_ = np.arange(0.0, BR_["dosah_m"] + w, 0.5); ko_ = []
            for sg_ in (1, -1):
                ter_ = map_coordinates(_YSM, [z[b_] + sg_ * nb_[1] * aa_ - z0, x[b_] + sg_ * nb_[0] * aa_ - x0], order=1, mode="nearest")
                nad_ = np.nonzero(hl[b_] + sk_ * (aa_ - pwb_) >= ter_ - 0.02)[0]; nad_ = nad_[aa_[nad_] > pwb_]
                ko_.append(float(aa_[nad_[0]]) if len(nad_) else float(aa_[-1]))
            rext_ = min(max(ko_) + BR_["zaobleni_m"], w / 2 + BR_["dosah_m"] - KO.get("napojeni_m", 4.0))
            dsa_ = np.abs((np.c_[x, z] - np.array([x[b_], z[b_]])) @ tg_)
            wa_ = np.clip(1 - (dsa_ - BR_["polosirka_m"]) / BR_["nabeh_m"], 0, 1); wa_ = wa_ * wa_ * (3 - 2 * wa_)
            wa_ = np.where(np.abs(s_ax - s_ax[b_]) < BR_["polosirka_m"] + BR_["nabeh_m"] + 2, wa_, 0)   # jen tento úsek toku (ne vedlejší oblouk)
            brehax = np.where(wa_ > wbax, wa_ * rext_, brehax); wbax = np.maximum(wbax, wa_)
            rx_ = np.where(lep_, rext_, rx_)
            brody_tvar.append({"i": int(b_), "stred": [round(float(x[b_]), 3), round(float(z[b_]), 3)], "tecna": [round(float(tg_[0]), 4), round(float(tg_[1]), 4)],
                               "dosah_breh_m": round(rext_, 2), "najezd_konec_m": [round(v_, 1) for v_ in ko_],
                               "vozovy": _BROD_VOZ.get((round(float(x[b_]), 3), round(float(z[b_]), 3)), True)})
        dist_b = dist * (1 - wb) + np.minimum(acr_, dist + 1e3) * wb   # vzdálenost napříč: v brodu po kolmici brodu
        y0b_ = Y0[r0_:r1_, c0_:c1_].ravel()   # běžný profil v náběhu jen jako zářez (svah 0,9 nad terénem by se smíchal do násypu)
        bl_ = np.minimum(prof, y0b_) * (1 - wb) + pb * wb
        # jiný oblouk téhož toku: jeho koryto a práh břehu (do pw + prah_m + 1 m) zůstanou, dál nájezd jen snižuje (voda_v_korytu)
        prof = np.where(wb > 0, np.where(vl_, bl_, np.where(dist < pw + KO["prah_m"] + 1.0, prof, np.minimum(prof, bl_))), prof)
        print("brod", t.get("jmeno") or ti, [(bt_["stred"], bt_["dosah_breh_m"], bt_["najezd_konec_m"]) for bt_ in brody_tvar])
    # na kraji dosahu (posledních napojeni_m) plynule zpět k původnímu terénu – žádná svislá stěna na hranici zářezu
    Rc = R0 + (R - R0) * wb   # mimo brod původní dosah koryta
    wk = np.clip((Rc - dist_b) / KO.get("napojeni_m", 4.0), 0, 1); y0s = Y0[r0_:r1_, c0_:c1_].ravel()
    prof = np.where(prof < 1e8, prof * wk + y0s * (1 - wk), prof)
    prof = np.where(ok & (dist_b < Rc), prof, 1e9).reshape(cx.shape)
    sub = Y[r0_:r1_, c0_:c1_]
    if brody_:   # brod smí terén i zvednout (dno brodu, zasypané díry nájezdu), jen kde ho ještě nic nezměnilo (koryto jiného toku zůstane)
        nasyp_ = (wb.reshape(cx.shape) > 0) & vl_.reshape(cx.shape) & (prof < 1e8) & (np.abs(sub - Y0[r0_:r1_, c0_:c1_]) < 1e-6)
        Y[r0_:r1_, c0_:c1_] = np.where(nasyp_, prof, np.minimum(sub, prof))
    else: Y[r0_:r1_, c0_:c1_] = np.minimum(sub, prof)
    # stanoviště koryta: 1 = kamenité dno a práh (valouny, mech), 2 = břeh (kopřivy, ostružiník, vrbičky) – byliny.json
    dd = dist.reshape(cx.shape); sub_dr = DRUH[r0_:r1_, c0_:c1_]; pw2 = pw.reshape(cx.shape) if np.ndim(pw) else pw
    # kamenité jen pod vodou, břeh (tráva, keře) od kraje vody (Míša 5. 11.: „až k vodě žádná tráva ani keř“)
    sub_dr[(dd < pw2 * 0.85) & np.isfinite(dd)] = 1
    sub_dr[(dd >= pw2 * 0.85) & (dd < pw2 + KO["prah_m"] + KO["breh_m"]) & (sub_dr == 0)] = 2
    if brody_:   # brod: rozlitá voda = kamenité dno; nájezd = jemné buňky (3: kolize a síť podle jemného pásu voda.py BREH,
        # stanoviště beze změny – cesty.py bere jen 1 a 2). O 1 m užší než pás BREH (síť dlaždic se pod ním snižuje).
        wb2 = wb.reshape(cx.shape); ac2 = acr_.reshape(cx.shape); rx2 = rx_.reshape(cx.shape)
        sub_dr[(wb2 > 0.5) & (ac2 < pwb_ * 0.85) & ok.reshape(cx.shape)] = 1
        sub_dr[(wb2 > 0) & (ac2 < wb2 * rx2 - 1.0) & (sub_dr == 0) & ok.reshape(cx.shape)] = 3
    VODA.append((np.c_[x, z], (w / 2) * (1 + VK["amp"]) + 0.4))
    vystup[str(ti)] = {"jmeno": t.get("jmeno"), "sirka": w, "hloubka": hv, "osa": np.c_[x, z, hl].round(3).tolist(), "brody": brody_,
                     "brody_tvar": brody_tvar, "brod_vaha": wbax.round(3).tolist(), "brod_breh_m": brehax.round(2).tolist()}
    print("koryto", t.get("jmeno") or ti, "délka %.0f m, šíře %.1f, hloubka vody %.2f, max zářez %.1f m" % (s[-1], w, hv, float((sub - np.minimum(sub, prof)).max())))
zar = np.abs(Y0 - Y) > 0.03   # i násyp brodu (dno, zasypané díry) – vyhlazení dlaždic ho nesmí rozmazat
H2 = Y + P["H"]
if os.path.exists(pre + "_jamy.npz"):   # sklep a šíje (teren_upravy.py) mají přednost
    J = np.load(pre + "_jamy.npz"); zar[J["r"], J["c"]] = False; H2[J["r"], J["c"]] = J["y"]
    rr, cc = np.nonzero(zar); r = np.r_[J["r"], rr]; c = np.r_[J["c"], cc]; yy = np.r_[J["y"], H2[rr, cc]]
else:
    r, c = np.nonzero(zar); yy = H2[r, c]
n_upr = len(J["r"]) if os.path.exists(pre + "_jamy.npz") else 0   # prvních n_upr = sklep a šíje (kryje je hrad), zbytek zářez koryt
ex_ = {"y_puv": np.load(pre + "_jamy.npz")["y_puv"]} if os.path.exists(pre + "_jamy.npz") and "y_puv" in np.load(pre + "_jamy.npz").files else {}   # původní výšky jam (viditelná síť – teren_dlazdice.py)
np.savez(out + "_jamy.npz", r=r, c=c, y=yy.astype(np.float32), n_upr=n_upr, **ex_)
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
