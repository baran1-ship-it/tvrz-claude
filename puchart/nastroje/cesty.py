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
import math, sys, json, os, shutil
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
PORADI_ = {"pesina": 0, "stezka": 1, "hrebenova": 2, "vozova": 3}
# SPOJKY (Míša 9. 11.: „na spoustě míst je cesta přerušená travou“, brody „děs“): volný konec úseku cesty, který končí
# 1,5–25 m od jiné cesty, se s ní spojí rovným úsekem. Přes potok (brod) jen povrch a bez porostu – terén se nemění,
# koryto (koryta.py) zůstane a cesta vede jeho dnem jako v Havranovi (brod = cesta přes mělké koryto, bez kamenů navíc).
# U mostu (střed spojky do 15 m od mostu) se nespojuje – tam navazuje most.
_VH = json.load(open(os.path.join(K, "pravidla/svet/voda_hra.json")))
_TH = os.path.join(K, "hra/data/toky_hladina.json")
_tok = np.vstack([np.array(t["osa"])[:, :2] for t in json.load(open(_TH))["toky"].values()]) if os.path.exists(_TH) else np.zeros((1, 2)) + 1e9
C["cesty"] = [c for c in C["cesty"] if not c.get("spojka")]
def _husta(o):
    o = np.array(o, float)[:, :2]; d = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]; s_ = np.arange(0, d[-1] + 0.01, 0.5)
    return np.c_[np.interp(s_, d, o[:, 0]), np.interp(s_, d, o[:, 1])]
# NAJETÍ NA MOST ROVNĚ (Míša 6. a 9. 11.: „mosty nesmyslně navazují na cestu, má navazovat rovně“): oba konce cest u mostu
# určují osu mostu (blender/voda.py); posledních ROVNE_M metrů každé z nich se položí do té osy (plynulý přechod)
ROVNE_M = 12.0
for m_ in _VH.get("mosty", []):
    u_ = np.array(m_["u_bodu"], float); kon_ = []
    for c in C["cesty"]:
        for kon in (0, -1):
            e_ = np.array(c["osa"][kon][:2], float)
            if np.hypot(*(e_ - u_)) < 15: kon_.append((float(np.hypot(*(e_ - u_))), c, kon))
    kon_.sort(key=lambda t_: t_[0])
    if len(kon_) < 2: continue
    (_, c1, k1), (_, c2, k2) = kon_[:2]
    e1 = np.array(c1["osa"][k1][:2], float); e2 = np.array(c2["osa"][k2][:2], float)
    if np.hypot(*(e2 - e1)) < 2: continue
    for (c, k, e, a_) in ((c1, k1, e1, (e1 - e2) / np.hypot(*(e1 - e2))), (c2, k2, e2, (e2 - e1) / np.hypot(*(e2 - e1)))):
        o_ = np.array(c["osa"], float)
        if k == -1: o_ = o_[::-1]
        hu = _husta(o_); dl = np.r_[0, np.cumsum(np.hypot(*np.diff(hu, axis=0).T))]
        if dl[-1] < ROVNE_M * 1.5: continue
        za = int(np.searchsorted(dl, ROVNE_M))
        nov = [e + a_ * t_ for t_ in np.arange(0, ROVNE_M, 2.0)]   # rovně od mostu
        zb = hu[za:]; zb = zb[np.hypot(zb[:, 0] - nov[-1][0], zb[:, 1] - nov[-1][1]) > 4.0]   # zbytek cesty, plynulé napojení
        o2 = np.vstack([np.array(nov), zb[::4], hu[-1:]])
        if k == -1: o2 = o2[::-1]
        c["osa"] = [[round(float(x_), 2), round(float(z_), 2)] for x_, z_ in o2]
        print("most", m_["id"], c["id"], "konec rovně do osy mostu", ROVNE_M, "m")
_D = [_husta(c["osa"]) for c in C["cesty"]]; SPOJKY = []
for i, c in enumerate(C["cesty"]):
    for kon in (0, -1):
        p_ = np.array(c["osa"][kon][:2], float); best = None
        for j, q in enumerate(_D):
            if j == i: continue
            dd = np.hypot(q[:, 0] - p_[0], q[:, 1] - p_[1]); k_ = int(dd.argmin())
            if best is None or dd[k_] < best[0]: best = (float(dd[k_]), j, q[k_])
        if best is None or not (1.5 < best[0] < 25): continue
        mid = (p_ + best[2]) / 2
        if min(np.hypot(m_["u_bodu"][0] - mid[0], m_["u_bodu"][1] - mid[1]) for m_ in _VH.get("mosty", [])) < 15: continue
        if any(np.hypot(*(np.array(sp["osa"][0]) - best[2])) < 3 and np.hypot(*(np.array(sp["osa"][1]) - p_)) < 3 for sp in SPOJKY): continue   # opačný směr už je
        typ = min((c["typ"], C["cesty"][best[1]]["typ"]), key=lambda t_: PORADI_.get(t_, 0))
        brod = float(np.hypot(_tok[:, 0] - mid[0], _tok[:, 1] - mid[1]).min()) < 8.0
        SPOJKY.append({"id": "spojka_%s_%s" % (c["id"], C["cesty"][best[1]]["id"]), "typ": typ, "osa": [p_.tolist(), best[2].tolist()],
                       "spojka": True, "jen_maska": brod})
        print("spojka", SPOJKY[-1]["id"], "%.1f m" % best[0], "brod" if brod else "")
C["cesty"] += SPOJKY
PORADI = {"pesina": 0, "stezka": 1, "hrebenova": 2, "vozova": 3}   # pěšiny první, vozové nakonec: kde se kříží, vyhraje rovný jízdní pás
# (Míša 6. 11.: boční hrb na hřebenové cestě – přes ni vedla žlutá pěšina, která po ní přepsala terén se svým příčným sklonem)
for c in sorted(C["cesty"], key=lambda c_: PORADI.get(c_["typ"], 0)):
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
    if "max_rez_nasyp_m" in T: yp = np.clip(yp, y - T["max_rez_nasyp_m"], y + T["max_rez_nasyp_m"])   # Havran _cesty_profil: zářez/násyp omezený
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
    if c.get("jen_maska"): novy = orig   # brod: terén (koryto) beze změny, jen povrch cesty
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
    na_ceste[z0i:z1i, x0i:x1i] |= dist < T.get("bez_porostu_m", hw + 1.5)   # Havran pasma.cesta: keře 3 m od okraje hlíny
    print(c["id"], "délka", c["delka_m"], "m, zářez max", c["max_rez_m"], "m, násyp max", c["max_nasyp_m"], "m")
    c["_osa_px"] = px; c["_osa_pz"] = pz; c["_hw"] = hw
# příčný sklon jízdního pásu na výsledném terénu (Míša 6. 11.: „hrb na straně cesty, vozy by se převrátily do rokle“)
for c in C["cesty"]:
    px, pz, hw = c["_osa_px"], c["_osa_pz"], c["_hw"]; mx = 0.0
    for i in range(2, len(px) - 2, 3):
        tx, tz = px[i + 1] - px[i - 1], pz[i + 1] - pz[i - 1]; ln = math.hypot(tx, tz) or 1.0; nx_, nz_ = -tz / ln, tx / ln
        hs = []
        for sg in (-1, 1):
            xi = int(round(px[i] + nx_ * sg * hw * 0.8 - xh0)); zi = int(round(pz[i] + nz_ * sg * hw * 0.8 - zh0))
            if 0 <= xi < nx and 0 <= zi < ny: hs.append(H[zi, xi])
        if len(hs) == 2: mx = max(mx, abs(hs[1] - hs[0]) / (2 * hw * 0.8))
    c["max_pricny"] = round(float(mx), 3)
# koleje vozových cest (Míša 5. 11.: „vozová cesta jako z Havrana“ – Havran zem.gdshader: dvě vyjeté koleje, travnatý hřbet
# mezi nimi, prach a kamínky na krajích): textura 0,5 m s příčnou vzdáleností od osy (A = 1 − |d|/4 m, 0 mimo vozovou cestu)
KR = 2; kol = np.zeros((ny * KR, nx * KR), np.float32)
from scipy.spatial import cKDTree as _KD
for c in C["cesty"]:
    if C["typy"][c["typ"]]["povrch"] != "hlina": continue
    osa = chaikin(np.array(c["osa"], float), 3); d_ = np.r_[0, np.cumsum(np.hypot(*np.diff(osa, axis=0).T))]
    s_ = np.arange(0, d_[-1], 0.25); qx = np.interp(s_, d_, osa[:, 0]); qz = np.interp(s_, d_, osa[:, 1])
    x0i = int(max(0, (qx.min() - xh0 - 5) * KR)); x1i = int(min(nx * KR, (qx.max() - xh0 + 5) * KR))
    z0i = int(max(0, (qz.min() - zh0 - 5) * KR)); z1i = int(min(ny * KR, (qz.max() - zh0 + 5) * KR))
    ZZ, XX = np.mgrid[z0i:z1i, x0i:x1i]; xs = XX / KR + xh0 + 0.25; zs = ZZ / KR + zh0 + 0.25
    dd, _ = _KD(np.c_[qx, qz]).query(np.c_[xs.ravel(), zs.ravel()]); dd = dd.reshape(xs.shape)
    kol[z0i:z1i, x0i:x1i] = np.maximum(kol[z0i:z1i, x0i:x1i], np.clip(1 - dd / 4.0, 0, 1))
Image.fromarray((kol[:2000 * KR // 1, :2000 * KR // 1][:4000, :4000] * 255).astype(np.uint8), "L").save(os.path.join(K, "hra/textury/maska_koleje.png"))
rez = np.clip(gaussian_filter(rez, 1.0) * (0.75 + 0.35 * sum_), 0, 1)
np.save(out + ".npy", H.astype(np.float32)); shutil.copy(pre + ".json", out + ".json")
if os.path.exists(pre + "_jamy.npz"):   # sklep a šíje (teren_upravy.py): cesty je nemění, jen se předají dál
    J = np.load(pre + "_jamy.npz"); H[J["r"], J["c"]] = J["y"]; np.save(out + ".npy", H.astype(np.float32)); shutil.copy(pre + "_jamy.npz", out + "_jamy.npz")
    na_ceste[J["r"], J["c"]] = True
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
st[nc] = ic
if os.path.exists(pre + "_koryta.npz"):   # koryta (koryta.py): dno a práh = koryto_kamenite, pás nad ním = breh
    KR_ = np.load(pre + "_koryta.npz"); rr, cc_ = KR_["r"] // 2, KR_["c"] // 2; ok = (rr < st.shape[0]) & (cc_ < st.shape[1])
    for druh, jm in ((2, "breh"), (1, "koryto_kamenite")):
        m_ = ok & (KR_["druh"] == druh); st[rr[m_], cc_[m_]] = sj["tridy"].index(jm)
    st[nc] = ic   # cesta (brod) má přednost
    shutil.copy(pre + "_koryta.npz", out + "_koryta.npz")
if os.path.exists(pre + "_jamy.npz"):   # sklep a šíje: žádné byliny (každá buňka 2 m, kterou jáma zasáhne); koryta ne
    J = np.load(pre + "_jamy.npz"); mj = np.zeros(st.shape, bool)
    jen = np.ones(len(J["r"]), bool)
    if os.path.exists(pre + "_koryta.npz"):
        kk = set(zip(KR_["r"].tolist(), KR_["c"].tolist())); jen = np.array([(a, b) not in kk for a, b in zip(J["r"].tolist(), J["c"].tolist())])
    rr, cc_ = J["r"][jen] // 2, J["c"][jen] // 2; ok = (rr < st.shape[0]) & (cc_ < st.shape[1]); mj[rr[ok], cc_[ok]] = True
    from scipy.ndimage import binary_dilation
    st[binary_dilation(mj, iterations=1)] = ic   # i pás 2 m kolem (trsy s náhodným posunem padaly na schody šíje)
# okraj lesa (byliny.json okraj_lesa_m): lesní buňky do této vzdálenosti od louky, pole, cesty, vody a pasek = les_okraj
# (keře, ostružiník, světlá tráva – GPT scény bod 3: lesní okraje a křoviny jako přirozené clony)
OK_M = json.load(open(os.path.join(K, "pravidla/svet/byliny.json"))).get("okraj_lesa_m", 0)
if OK_M:
    tr = sj["tridy"]; les_i = [tr.index(t) for t in tr if t.startswith("les_") and t not in ("les_paseka", "les_okraj")]
    otevr = [tr.index(t) for t in ("louka_kosena", "pastvina", "pole", "zemedelstvi", "cesta", "breh", "luh", "les_paseka", "koryto_kamenite") if t in tr]
    jl = np.isin(st, les_i); do = distance_transform_edt(~np.isin(st, otevr)) * 2.0
    st[jl & (do <= OK_M)] = tr.index("les_okraj")
    print("okraj lesa: %.1f %% plochy" % ((jl & (do <= OK_M)).mean() * 100))
Image.fromarray(st).save(os.path.join(K, "hra/data/stanoviste.png"))
# stromy i z buněk 2 m třídy „cesta“ (jedna definice cesty pro stromy i porost – test smyslu strom_mimo_cestu)
A = np.fromfile(sb, np.float32).reshape(-1, 5)
c2 = np.clip(((A[:, 0] - sj["x0_hra"]) / sj["krok_m"]).astype(int), 0, st.shape[1] - 1); r2 = np.clip(((A[:, 1] - sj["z0_hra"]) / sj["krok_m"]).astype(int), 0, st.shape[0] - 1)
keep = st[r2, c2] != ic; A[keep].tofile(sb); print("stromů z buněk cesty", int((~keep).sum()))
C["cesty"] = [c for c in C["cesty"] if not c.get("spojka")]   # spojky se počítají při každé stavbě znovu
C["vysledek"] = {c["id"]: {k2: c[k2] for k2 in ("delka_m", "max_rez_m", "max_nasyp_m", "max_pricny")} for c in C["cesty"]}
for c in C["cesty"]:
    for k_ in ("_osa_px", "_osa_pz", "_hw"): c.pop(k_, None)
json.dump(C, open(os.path.join(K, "pravidla/svet/cesty_puchart.json"), "w"), ensure_ascii=False, indent=1)
