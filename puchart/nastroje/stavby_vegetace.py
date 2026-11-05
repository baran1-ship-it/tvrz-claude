"""Stavby → vegetace (pořadí stavby: terén → cesty → budovy → voda → vegetace; test smyslu hrad_bez_stromu a
kere_mimo_stavby, 2. 11.): ze skutečných obrysů zdí a budov (hra/data/stavby_clony.json ze stavitele hradu) stanoviště
„stavba“ (bez porostu) a uvnitř hradeb (hrad_puchart.json A.jadro, B.hradba) „nadvori“ (jen tráva, byliny.json);
stromy pryč ze staveb, nádvoří a pásu okraj_m kolem zdí. Nahrazuje ruční obdélníky hrady_bez_stromu.json.
  python3 nastroje/stavby_vegetace.py <koren>"""
import sys, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
K = os.path.abspath(sys.argv[1]); D = K + "/hra/data/"
SJ = json.load(open(D + "stanoviste.json")); st = np.array(Image.open(D + "stanoviste.png")); st = st[..., 0] if st.ndim == 3 else st
_orig = K + "/build/stanoviste_pred_stavbami.png"   # opakovaný běh: vždy z originálu stanovišť (pata zdí se nenabaluje)
_nase = [SJ["tridy"].index(t) for t in ("stavba", "nadvori", "predhradi", "pata_zdi_vne", "pata_zdi_uvnitr", "kout_zdi", "nadvori_slap", "pata_zdi_lic") if t in SJ["tridy"]]
if not np.isin(st, _nase).any(): os.makedirs(K + "/build", exist_ok=True); Image.fromarray(st).save(_orig)
elif os.path.exists(_orig): st = np.array(Image.open(_orig))
KC = json.load(open(K + "/pravidla/svet/kontroly.json"))["stavby_vegetace"]
for t in ("stavba", "nadvori"):
    if t not in SJ["tridy"]: SJ["tridy"].append(t)
ks = SJ["krok_m"]; x0, z0 = SJ["x0_hra"], SJ["z0_hra"]
def pix(p): return ((p[0] - x0) / ks, (p[1] - z0) / ks)
ms = Image.new("L", (st.shape[1], st.shape[0]), 0); dr = ImageDraw.Draw(ms)
for q in json.load(open(D + "stavby_clony.json"))["kvadry"]:
    dr.polygon([pix(r) for r in q["rohy"]], fill=1)
if os.path.exists(D + "stavby_pudorysy.json"):   # celé půdorysy budov (tráva prorůstala podlahou – Míša 4. 11.)
    for q in json.load(open(D + "stavby_pudorysy.json"))["budovy"]: dr.polygon([pix(r) for r in q], fill=1)
mn = Image.new("L", ms.size, 0); dn = ImageDraw.Draw(mn)
HP = json.load(open(K + "/pravidla/svet/hrad_puchart.json"))
for poly in (HP["A"]["jadro"], HP["B"]["hradba"]):
    dn.polygon([pix(r) for r in poly], fill=1)
# předhradí A: mezi hradbou s valem, východní hradbou a jádrem (obrys z dat hradeb) – ne les uvnitř hradeb (3. 11.)
mp = Image.new("L", ms.size, 0); dp = ImageDraw.Draw(mp)
pr_ = HP["A"]["hradba_val"]["osa"] + HP["A"]["hradba_vychod"]["osa"] + [r for r in reversed(HP["A"]["jadro"])]
dp.polygon([pix(r) for r in pr_], fill=1)
stavba_jadro = np.array(ms).astype(bool)
stavba = binary_dilation(stavba_jadro, iterations=1)   # +1 buňka: tenké zdi rastr 2 m míjel (kere_mimo_stavby)
nadvori = np.array(mn).astype(bool) & ~stavba_jadro
predhradi = np.array(mp).astype(bool) & ~stavba_jadro & ~nadvori
if "predhradi" not in SJ["tridy"]: SJ["tridy"].append("predhradi")
st[predhradi] = SJ["tridy"].index("predhradi")
st[stavba] = SJ["tridy"].index("stavba"); st[nadvori] = SJ["tridy"].index("nadvori")
st[okraj_ := (stavba & ~stavba_jadro & ~nadvori & ~predhradi)] = SJ["tridy"].index("stavba")   # vnější prstenec určí pata zdí níž

# --- pata zdí (Míša 3. 11.: „tráva u zdi ne všude, sem tam keřík, suť nebo kámen, jako v realitě, nic plošně kopírované;
# hlavně zvenku, zevnitř méně“; Havran kraj.uzivani_smi pasma.budova plevel_u_zdi_m/drn_m a ruiny._pata). Pás podél zdí
# s proměnlivou šíří (šum), ve skvrnách (mezery), kouty hustší; uvnitř jen místy, kolem tras (dveře, brány) vyšlapáno.
PZ = json.load(open(K + "/pravidla/svet/pata_zdi.json"))
from scipy.ndimage import distance_transform_edt, gaussian_filter, uniform_filter
rng = np.random.default_rng(PZ["seminko"])
def sum_(sigma_m):
    n = gaussian_filter(rng.standard_normal(st.shape), sigma_m / ks); return (n - n.mean()) / (n.std() + 1e-9)
d_zed = distance_transform_edt(~stavba_jadro) * ks   # m od zdi (od skutečného obrysu – pata zdí až k líci, Míša 4. 11.: „u zdí nic“)
okraj = stavba & ~stavba_jadro   # prstenec rozšíření: patří patě zdí (ne holé „stavbě“)
kout = uniform_filter(stavba_jadro.astype(float), size=PZ["kout"]["okno_bunek"]) >= PZ["kout"]["podil_zdi"]
trasy = Image.new("L", ms.size, 0); dt_ = ImageDraw.Draw(trasy)   # vyšlapáno: trasy průchodu (dveře, brány, schody)
for f in [f for f in os.listdir(D) if f.startswith("pruchody") and f.endswith(".json")]:
    for body in json.load(open(D + f))["trasy"].values():
        dt_.line([pix(b) for b in body], fill=1, width=max(1, int(PZ["slap_sirka_m"] / ks)))
if os.path.exists(K + "/build/portaly.json"):   # před a za každou bránou a dveřmi vyšlapaná plocha (Míša 4. 11.: tráva před mostem a v bráně)
    pp_ = PZ["pred_portalem"]
    for po in json.load(open(K + "/build/portaly.json"))["portaly"]:
        x_, _, z_ = po["pos"]; vx_, vz_ = po["ven"]; sx_, sz_ = -vz_, vx_; hw_ = po["w"] / 2 + pp_["okraj_m"]
        for z0_, z1_ in ((0.0, pp_["delka_m"]), (-po["hloubka"] - pp_["delka_m"], -po["hloubka"])):
            q_ = [(x_ + vx_ * zz + sx_ * ss, z_ + vz_ * zz + sz_ * ss) for zz, ss in ((z0_, -hw_), (z1_, -hw_), (z1_, hw_), (z0_, hw_))]
            dt_.polygon([pix(qq) for qq in q_], fill=1)
slap = np.array(trasy).astype(bool)
chran = np.isin(st, [SJ["tridy"].index(t) for t in PZ["nesahat"] if t in SJ["tridy"]])   # cesty, voda, skály zůstanou
for t in ("pata_zdi_vne", "pata_zdi_uvnitr", "kout_zdi", "nadvori_slap"):
    if t not in SJ["tridy"]: SJ["tridy"].append(t)
V = PZ["vne"]; sirka = V["sirka_m"][0] + (V["sirka_m"][1] - V["sirka_m"][0]) * np.clip(sum_(V["vlna_m"]) * 0.5 + 0.5, 0, 1)
vne = (~stavba | okraj) & ~nadvori & ~chran & ~slap & (d_zed <= sirka) & (sum_(V["skvrny_m"]) > V["mezery_prah"])
U = PZ["uvnitr"]
nadvori = nadvori | predhradi   # pata zdí uvnitř i v předhradí
uvn = nadvori & ~slap & (d_zed <= U["sirka_m"]) & (sum_(U["skvrny_m"]) > U["mezery_prah"])
ko = (vne | uvn | (nadvori & ~slap & (d_zed <= U["sirka_m"]))) & kout & (sum_(PZ["kout"]["skvrny_m"]) > PZ["kout"]["mezery_prah"])
st[vne] = SJ["tridy"].index("pata_zdi_vne"); st[uvn] = SJ["tridy"].index("pata_zdi_uvnitr"); st[ko] = SJ["tridy"].index("kout_zdi")
if "pata_zdi_lic" not in SJ["tridy"]: SJ["tridy"].append("pata_zdi_lic")
st[okraj & (vne | uvn | ko)] = SJ["tridy"].index("pata_zdi_lic")   # buňka zasahující do zdi: byliny až k líci, keře ne (kere_mimo_stavby)
st[nadvori & slap] = SJ["tridy"].index("nadvori_slap")
# trasy průchodu i mimo hradby (přístup k mostům a branám, pěšiny): vyšlapáno, bez keřů (Míša 4. 11. / hlídač scén: strom na pěšině k mostu B)
st[slap & ~nadvori & ~stavba & ~chran] = SJ["tridy"].index("nadvori_slap")
# povrch (KCD2 ref_kcd2_dvur_zed: nádvoří = udusaná hlína, tráva jen u zdí a v koutech; KCD1 18_brana_zvenku: k bráně
# vyšlapaná hlína): maska_cesty.R (vrstva hlína). Nádvoří hlína kromě pásu u zdí, předhradí hlína jen na vyšlapaných
# trasách a ve skvrnách. Maska z cesty.py (originál v build/) – opakovaný běh se nenabaluje.
H_ = PZ["hlina"]; _mo = K + "/build/maska_cesty_pred_stavbami.png"; _mc = K + "/hra/textury/maska_cesty.png"
import hashlib
_hz = K + "/build/maska_cesty_zapsano.md5"; _h = lambda f: hashlib.md5(open(f, "rb").read()).hexdigest()
if not (os.path.exists(_mo) and os.path.exists(_hz) and open(_hz).read() == _h(_mc)): Image.open(_mc).save(_mo)   # maska je od cesty.py (ne naše)
mk = np.array(Image.open(_mo)).astype(np.float32) / 255.0
jadra = np.array(mn).astype(bool)   # celý obrys nádvoří (i buňky „stavba“ – rozšířené obrysy budov zabraly 90 % malého jádra A)
hl = np.zeros(st.shape, np.float32)
hl[jadra] = H_["nadvori"]; hl[jadra & (uvn | ko)] = H_["u_zdi"]
hl[predhradi & (sum_(H_["predhradi_skvrny_m"]) > H_["predhradi_prah"])] = H_["predhradi"]
hl[slap & (jadra | predhradi)] = H_["slap"]
hl = gaussian_filter(hl, H_["mekkost_m"] / ks)   # měkký přechod (hlína není pravítko)
mk[..., 0] = np.maximum(mk[..., 0], hl)
# kamenitost (Míša 3. 11.: „není to nic, co jde plošně kopírovat“): úlomky droby nejsou všude stejně – víc na svahu (eroze
# odnáší hlínu), u paty zdí (opadané zdivo), na kraji vyšlapaných pruhů (odkopnuté), málo na vyšlapané rovině; k tomu shluky.
# hra/data/kamenitost.png (2 m, 0..1) řídí 3D úlomky (byliny.gd) a výchozy droby v hlíně (maska_cesty.B).
KM = PZ["kamenitost"]; VYJ = json.load(open(D + "vysek.json"))
Hm = np.fromfile(D + "vysek.r16", "<u2").reshape(VYJ["vyska"], VYJ["sirka"]).astype(np.float32) / 200.0
gy, gx = np.gradient(Hm); sk1 = np.hypot(gx, gy)
r_ = np.clip(((np.arange(st.shape[0]) * ks + z0) - VYJ["z0_hra"]).astype(int), 0, VYJ["vyska"] - 1); c_ = np.clip(((np.arange(st.shape[1]) * ks + x0) - VYJ["x0_hra"]).astype(int), 0, VYJ["sirka"] - 1)
sklon = sk1[np.ix_(r_, c_)]
kraj = binary_dilation(slap, iterations=1) & ~slap
kam = (KM["zaklad"] + KM["svah"] * np.clip((sklon - KM["svah_od"]) / KM["svah_rozsah"], 0, 1) + KM["u_zdi"] * np.exp(-d_zed / KM["u_zdi_m"])
       + KM["kraj_pruhu"] * kraj - KM["vyslapano"] * slap + KM["shluky"] * sum_(KM["shluky_m"]))
kam = np.clip(kam, 0, 1)
Image.fromarray((kam * 255).astype(np.uint8), "L").save(D + "kamenitost.png")
VY_ = PZ["vychozy"]   # výchozy droby v hlíně (maska_cesty.B: shader ji kreslí jen tam, kde je hlína) – kde je kamenito
vy = ((jadra | predhradi) & (kam > VY_["prah_kamenitosti"])).astype(np.float32) * VY_["sila"]
mk[..., 2] = np.maximum(mk[..., 2], gaussian_filter(vy, 1.0))
Image.fromarray((np.clip(mk, 0, 1) * 255).astype(np.uint8), "RGB").save(_mc); open(_hz, "w").write(_h(_mc))
pas = ~stavba & (d_zed <= V["sirka_m"][1]) & ~chran & ~slap & ~nadvori
print("pata zdí: vně %d buněk (%.0f %% pásu – skvrny), uvnitř %d, kouty %d, vyšlapáno %d" % (vne.sum(), 100 * vne.sum() / max(1, pas.sum()), uvn.sum(), ko.sum(), (nadvori & slap).sum()))
Image.fromarray(st).save(D + "stanoviste.png"); json.dump(SJ, open(D + "stanoviste.json", "w"), ensure_ascii=False, indent=1)
bez = binary_dilation(stavba | nadvori | predhradi, iterations=max(1, int(KC["okraj_m"] / ks))) | binary_dilation(slap, iterations=1)   # ani strom na trase průchodu
A = np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5)
c = np.clip(((A[:, 0] - x0) / ks).astype(int), 0, st.shape[1] - 1); r = np.clip(((A[:, 1] - z0) / ks).astype(int), 0, st.shape[0] - 1)
# a ze stanoviště koryta (kmen ve vodě/na kamenitém dně; koryta.py maže jen do kraje vody) – test strom_mimo_vodu 3. 11.
keep = ~bez[r, c] & (st[r, c] != SJ["tridy"].index("koryto_kamenite"))
# odlesnění okolí hradů roku 1393 (Míša 5. 11.: „vyhodnoť těch 600 let“; kresby GC80T08: hrady na holých skalních hřbetech)
OD = KC.get("odlesneni_1393")
if OD:
    jadro_ = stavba | nadvori | predhradi
    if OD.get("hreben_mezi_hrady"):   # hřbet mezi hrady (osa hřebenové cesty cesty_puchart.json)
        hr_ = Image.new("L", ms.size, 0); dh_ = ImageDraw.Draw(hr_)
        for c_ in json.load(open(K + "/pravidla/svet/cesty_puchart.json"))["cesty"]:
            if c_["id"] == "hrebenova": dh_.line([pix(b[:2]) for b in c_["osa"]], fill=1, width=max(1, int(8 / ks)))
        jadro_ = jadro_ | np.array(hr_).astype(bool)
    d_h = distance_transform_edt(~jadro_) * ks
    zv = (d_h <= OD["vnitrni_m"]) & ~jadro_; zn = (d_h > OD["vnitrni_m"]) & (d_h <= OD["vnejsi_m"])
    lesni = np.isin(st, [SJ["tridy"].index(t) for t in SJ["tridy"] if t.startswith("les")])
    st[zv & lesni] = SJ["tridy"].index(OD["trida_vnitrni"]); st[zn & lesni] = SJ["tridy"].index(OD["trida_vnejsi"])
    Image.fromarray(st).save(D + "stanoviste.png")
    rn_ = np.random.default_rng(1393).random(len(A))
    keep &= ~zv[r, c] & ~(zn[r, c] & (rn_ > OD["vnejsi_stromu_podil"]))
    print("odlesnění 1393: pastvina %d buněk, paseka %d" % ((zv & lesni).sum(), (zn & lesni).sum()))
A[keep].tofile(D + "stromy.bin")
print("stavby: %d buněk, nádvoří %d, stromů pryč %d" % (stavba.sum(), nadvori.sum(), (~keep).sum()))
