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
for t_ in ("cesta",):   # třída pro pěšiny v nádvořích (níž) – po přestavbě stanovišť chyběla (12. 11.: pád skriptu → stromy zůstaly ve stavbách)
    if t_ not in SJ["tridy"]: SJ["tridy"].append(t_)
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
if os.path.exists(D + "mista_stavby.json"):   # domy nových míst (mista_rozmisteni.py: Předhradí, krčma, hájovna)
    for q in json.load(open(D + "mista_stavby.json"))["pudorysy"]: dr.polygon([pix(r) for r in q], fill=1)
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
# usedlosti nových míst (nastroje/mista_rozmisteni.py → mista_stavby.json; pravidla/svet/mista.json usedlosti): dvůr = udusaná
# hlína (KCD1 ves_2, ves_6: dvůr a náves hliněné), zahrádka a sad tráva bez lesa, lány: orané = hlína, strniště = pole,
# úhor = pastvina (mista.json usedlosti.pole); celá parcela a lány bez stromů lesa (stromy sadu staví ves.gd)
bez_usedlosti = np.zeros(st.shape, bool); slap_v = np.zeros(st.shape, bool)
if os.path.exists(D + "mista_stavby.json"):
    MS_ = json.load(open(D + "mista_stavby.json")); UP_ = json.load(open(K + "/pravidla/svet/mista.json"))["usedlosti"]["povrch"]
    def _m(polys):
        im_ = Image.new("L", ms.size, 0); di_ = ImageDraw.Draw(im_)
        for q_ in polys: di_.polygon([pix(r) for r in q_], fill=1)
        return np.array(im_).astype(bool)
    for t in set(UP_["tridy"].values()):
        if t not in SJ["tridy"]: SJ["tridy"].append(t)
    hl_u = np.zeros(st.shape, np.float32)
    for klic, polys in (("dvur", MS_.get("dvory", [])), ("zahrada", MS_.get("zahrady", [])), ("sad", MS_.get("sady", []))):
        m_ = _m(polys) & ~stavba; st[m_] = SJ["tridy"].index(UP_["tridy"][klic]); hl_u[m_] = UP_["hlina"].get(klic, 0.0)
    for pl_ in MS_.get("pole", []):
        m_ = _m([pl_["poly"]]) & ~stavba; st[m_] = SJ["tridy"].index(UP_["tridy"][pl_["plodina"]]); hl_u[m_] = UP_["hlina"].get(pl_["plodina"], 0.0)
    # vyšlapáno ve vsi (mista.json usedlosti.vyslapano → mista_rozmisteni.py): ulice, náves, cestičky od vrat a dveří, okap,
    # plochy před vstupy, dvůr – hlína bez porostu (Míša 12. 11. večer: „tam, kde se chodí, je přece cesta, ne tráva“)
    VYS_ = MS_.get("vyslapano")
    if VYS_:
        if VYS_["trida"] not in SJ["tridy"]: SJ["tridy"].append(VYS_["trida"])
        hl_v = Image.new("F", ms.size, 0.0); dv_ = ImageDraw.Draw(hl_v)
        for e_ in sorted(VYS_["plochy"], key=lambda e: e["hlina"]):
            dv_.polygon([pix(r) for r in e_["poly"]], fill=float(e_["hlina"]))
        for e_ in sorted(VYS_["cary"], key=lambda e: e["hlina"]):
            dv_.line([pix(r) for r in e_["body"]], fill=float(e_["hlina"]), width=max(1, int(round(2 * e_["polosirka"] / ks))), joint="curve")
        hl_v = np.array(hl_v); slap_v = (hl_v > 0) & ~stavba_jadro
        st[slap_v] = SJ["tridy"].index(VYS_["trida"]); hl_u = np.maximum(hl_u, np.where(slap_v, hl_v, 0.0))
        print("vyšlapáno ve vsi: %d buněk" % slap_v.sum())
    mk[..., 0] = np.maximum(mk[..., 0], gaussian_filter(hl_u, UP_["mekkost_m"] / ks))
    bez_usedlosti = _m([u_["parcela"] for u_ in MS_.get("usedlosti", [])] + [p_["poly"] for p_ in MS_.get("pole", [])])
    print("usedlosti: %d buněk parcel a lánů, hlína %d" % (bez_usedlosti.sum(), (hl_u > 0).sum()))
Image.fromarray((np.clip(mk, 0, 1) * 255).astype(np.uint8), "RGB").save(_mc); open(_hz, "w").write(_h(_mc))
pas = ~stavba & (d_zed <= V["sirka_m"][1]) & ~chran & ~slap & ~nadvori
print("pata zdí: vně %d buněk (%.0f %% pásu – skvrny), uvnitř %d, kouty %d, vyšlapáno %d" % (vne.sum(), 100 * vne.sum() / max(1, pas.sum()), uvn.sum(), ko.sum(), (nadvori & slap).sum()))
Image.fromarray(st).save(D + "stanoviste.png"); json.dump(SJ, open(D + "stanoviste.json", "w"), ensure_ascii=False, indent=1)
bez = binary_dilation(stavba | nadvori | predhradi, iterations=max(1, int(KC["okraj_m"] / ks))) | binary_dilation(slap, iterations=1)   # ani strom na trase průchodu
A = np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5)
c = np.clip(((A[:, 0] - x0) / ks).astype(int), 0, st.shape[1] - 1); r = np.clip(((A[:, 1] - z0) / ks).astype(int), 0, st.shape[0] - 1)
# a ze stanoviště koryta (kmen ve vodě/na kamenitém dně; koryta.py maže jen do kraje vody) – test strom_mimo_vodu 3. 11.
keep = ~bez[r, c] & ~bez_usedlosti[r, c] & (st[r, c] != SJ["tridy"].index("koryto_kamenite"))
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
# mosty a lávky přes toky (pruchody_voda.json): pás šířky mostu + 2 m bez stromů a keřů, třída cesta (Míša 5. 11.: most zarostlý křovím)
if os.path.exists(D + "pruchody_voda.json"):
    mm = Image.new("L", ms.size, 0); dm_ = ImageDraw.Draw(mm)
    for b_ in json.load(open(D + "pruchody_voda.json"))["trasy"].values():
        dm_.line([pix(q[:2]) for q in b_], fill=1, width=max(2, int(5.5 / ks)))
    mm = np.array(mm).astype(bool); st[mm] = SJ["tridy"].index("cesta"); Image.fromarray(st).save(D + "stanoviste.png")
    keep &= ~mm[r, c]
# brody (blender/voda.py → hra/data/brody.json): pás 9 m podél cesty přes tok, 6 m široký, bez stromů a keřů, třída cesta
# (Havran _cesty_rostliny + louka.gd: bez trsů v potoce u brodu; Míša 6. 11.: brody zarostlé křovím)
if os.path.exists(D + "brody.json"):
    mb = Image.new("L", ms.size, 0); db_ = ImageDraw.Draw(mb)
    for b_ in json.load(open(D + "brody.json"))["brody"]:
        cx_, cz_ = b_["stred"]; sx_, sz_ = b_["smer"]; dl_ = b_.get("delka", b_["sirka_toku"] + 9) / 2 + 2.0
        db_.line([pix((cx_ - sx_ * dl_, cz_ - sz_ * dl_)), pix((cx_ + sx_ * dl_, cz_ + sz_ * dl_))], fill=1, width=max(2, int(6.0 / ks)))
    mb = np.array(mb).astype(bool); st[mb] = SJ["tridy"].index("cesta"); Image.fromarray(st).save(D + "stanoviste.png")
    keep &= ~mb[r, c]
# pás cest z cesty.py (build/cesty_pas.png) navrch všeho, co krok vegetace přidal (dvory, lány, odlesnění) – na cestě
# nic neroste (Míša 12. 11. večer: „cesty jsou na hodně místech zarostlé travou a keři, hlavně u hospody a od hradu k vesnici“);
# jen obrys budov a zdí (stavba) zůstane
_pc = K + "/build/cesty_pas.png"
if os.path.exists(_pc):
    pas_c = np.array(Image.open(_pc)) > 0; pas_c = pas_c[:st.shape[0], :st.shape[1]] & ~stavba_jadro
    st[pas_c] = SJ["tridy"].index("cesta"); Image.fromarray(st).save(D + "stanoviste.png")
    keep &= ~pas_c[r, c]
    print("pás cest: %d buněk třídy cesta" % pas_c.sum())
else: print("CHYBA: chybí build/cesty_pas.png (nastroje/cesty.py) – cesty zůstanou zarostlé"); sys.exit(1)
keep &= ~slap_v[r, c]   # ani strom lesa na ulici a cestičkách vsi
# --- pás trávy a bylin u paty plotů a zdí (Míša 13. 11.: „sem tam kolem plotu a kolem zdí staveb i na hradě by měla nějaká
# růst – mrkni na KCD“; závazná předloha docs/reference/kcd_ves_predloha: tráva v pruhu 0,3–1 m u paty zdí, plotů, kůlů).
# Raster stanovišť má 2 m – pruh se zapíše přesně podél hran jako skvrny (pata_zdi.json pas_u_paty) do hra/data/pata_pas.json,
# trsy rozseje byliny.gd (byliny.json pata_pas). Ne ve stavbě, na cestě, ulici, cestičce, před vstupem, ve vratech a na trasách.
from shapely.geometry import Polygon as _Pg, LineString as _Ls, Point as _Pt
from shapely.ops import unary_union as _uu
PP = PZ["pas_u_paty"]; rg = np.random.default_rng(PP["seminko"]); B_ = float(json.load(open(D + "byliny.json"))["bunka_m"])
hrany = []   # (a, b, strany: [n...]) – n = jednotková normála ven od hrany
budovy = []; nogo = []
def _hrany_poly(q_, zdroj):
    P_ = _Pg(q_)
    if not P_.is_valid or P_.area < 0.05: return
    budovy.append(P_); q_ = list(P_.exterior.coords)
    for k_ in range(len(q_) - 1):
        a_, b_ = np.array(q_[k_]), np.array(q_[k_ + 1]); d_ = b_ - a_; L_ = np.hypot(*d_)
        if L_ < 0.4: continue
        n_ = np.array([-d_[1], d_[0]]) / L_
        if P_.contains(_Pt(*((a_ + b_) / 2 + n_ * 0.05))): n_ = -n_
        hrany.append((a_, b_, [n_], zdroj))
if os.path.exists(D + "mista_stavby.json"):
    if PP["zdroje"]["ves_stavby"]:
        for q_ in MS_["pudorysy"]: _hrany_poly(list(_Pg(q_).buffer(-0.3, join_style=2).exterior.coords), "ves_stavba")
    if PP["zdroje"]["ves_ploty"]:
        for p_ in MS_["ploty"]:
            a_, b_ = np.array(p_["body"][0])[[0, 2]], np.array(p_["body"][-1])[[0, 2]]; d_ = b_ - a_; L_ = np.hypot(*d_)
            if L_ < 0.4: continue
            n_ = np.array([-d_[1], d_[0]]) / L_; hrany.append((a_, b_, [n_, -n_], "ves_plot"))
    VYS_ = MS_.get("vyslapano", {})
    for c_ in VYS_.get("cary", []):
        if len(c_["body"]) > 1: nogo.append(_Ls(c_["body"]).buffer(c_["polosirka"]))
    for e_ in VYS_.get("plochy", []):
        if e_["druh"] in ("pred_vstupem", "naves", "sezeni"): nogo.append(_Pg(e_["poly"]).buffer(PP["vstup_okraj_m"]))
    for b_ in MS_["brany"]: nogo.append(_Ls([(b_["a"][0], b_["a"][2]), (b_["b"][0], b_["b"][2])]).buffer(PP["brana_okraj_m"]))
if PP["zdroje"]["hrad_zdi"]:
    for q in json.load(open(D + "stavby_clony.json"))["kvadry"]: _hrany_poly(q["rohy"], "hrad_zed")
if PP["zdroje"]["hrad_budovy"] and os.path.exists(D + "stavby_pudorysy.json"):
    for q in json.load(open(D + "stavby_pudorysy.json"))["budovy"]: _hrany_poly(q, "hrad_budova")
BUD_ = _uu(budovy).buffer(0.02) if budovy else _Pg(); NOGO_ = _uu(nogo) if nogo else _Pg()
from shapely.prepared import prep as _prep
BUDp, NOGOp = _prep(BUD_), _prep(NOGO_)
_vyn = [SJ["tridy"].index(t) for t in PP["vynechat_tridy"] if t in SJ["tridy"]]; _uzr = [SJ["tridy"].index(t) for t in PP["uz_roste_tridy"] if t in SJ["tridy"]]
def _cell(p_):
    c__ = int((p_[0] - x0) / ks); r__ = int((p_[1] - z0) / ks)
    return (r__, c__) if 0 <= r__ < st.shape[0] and 0 <= c__ < st.shape[1] else None
skvrny = {}; pocty = {}; delky = {}
for a_, b_, strany, zdroj in hrany:
    d_ = b_ - a_; L_ = float(np.hypot(*d_)); d_ = d_ / L_
    for n_ in strany:
        t_ = rg.uniform(0, PP["mezera_m"][1]); delky[zdroj] = delky.get(zdroj, 0.0) + L_
        while t_ < L_ - 0.3:
            l_ = min(rg.uniform(*PP["skvrna_m"]), L_ - t_); w_ = rg.uniform(*PP["sirka_m"])
            p0 = a_ + d_ * t_ + n_ * PP["od_hrany_m"]; p1 = a_ + d_ * (t_ + l_) + n_ * PP["od_hrany_m"]
            vz = [p0 + n_ * w_ * 0.5, (p0 + p1) / 2 + n_ * w_ * 0.5, p1 + n_ * w_ * 0.5, (p0 + p1) / 2 + n_ * w_]
            ok_ = l_ >= 0.4
            for q_ in vz:
                if not ok_: break
                rc = _cell(q_)
                if rc is None or st[rc] in _vyn or st[rc] in _uzr or slap[rc] or pas_c[rc] or BUDp.contains(_Pt(*q_)) or NOGOp.contains(_Pt(*q_)): ok_ = False
            if ok_:
                m_ = (p0 + p1) / 2; k_ = "%d,%d" % (int(np.floor(m_[0] / B_)), int(np.floor(m_[1] / B_)))
                skvrny.setdefault(k_, []).append([round(float(p0[0]), 2), round(float(p0[1]), 2), round(float(p1[0]), 2), round(float(p1[1]), 2), round(float(n_[0]), 3), round(float(n_[1]), 3), round(float(w_), 2), zdroj])
                pocty[zdroj] = pocty.get(zdroj, 0.0) + l_
            t_ += l_ + rg.uniform(*PP["mezera_m"])
json.dump({"popis": "pás trávy u paty plotů a zdí (nastroje/stavby_vegetace.py z pravidla/svet/pata_zdi.json pas_u_paty) – čte byliny.gd; skvrna = [x0, z0, x1, z1, nx, nz, šířka, zdroj] podél hrany, n ven od zdi; klíč = buňka bylin (bunka_m)",
           "bunka_m": B_, "bunky": skvrny, "pokryti": {k: round(pocty.get(k, 0.0) / max(v, 1e-6), 3) for k, v in delky.items()}},
          open(D + "pata_pas.json", "w"), ensure_ascii=False)
print("pás u paty: skvrn %d, pokrytí délky hran %s" % (sum(len(v) for v in skvrny.values()), {k: "%.0f %%" % (100 * pocty.get(k, 0.0) / max(v, 1e-6)) for k, v in delky.items()}))
A[keep].tofile(D + "stromy.bin")
print("stavby: %d buněk, nádvoří %d, stromů pryč %d" % (stavba.sum(), nadvori.sum(), (~keep).sum()))
