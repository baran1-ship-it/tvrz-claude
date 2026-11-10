"""Test smyslu Puchartu (vrstva 1 hlídačů z Havrana; Míša 2. 11.: „vše o sobě ví a spolupracuje“). Rychlé kontroly nad
upečenými daty, bez Godotu (sekundy). Každý test má jméno smysl:<jmeno> – na ně odkazuje matice vztahů (vztahy.json
testy_puchart) a tabulka chyb (docs/chyby.md). Výsledek build/test_smyslu.json; rc 1 = nevydávat.
Geometrii (visí / pod terénem) počítá blender/kontrola_geometrie.py – zde se porovná se schváleným stavem
(pravidla/svet/kontroly.json geometrie.schvaleno): nový visící kus = chyba, opravený = zlepšení.
  python3 nastroje/test_smyslu.py <koren>"""
import sys, os, json, math
import numpy as np
from PIL import Image
K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
D = K + "/hra/data/"
KC = json.load(open(K + "/pravidla/svet/kontroly.json"))
VY = json.load(open(D + "vysek.json")); Hr = np.fromfile(D + "vysek.r16", "<u2").reshape(VY["vyska"], VY["sirka"])
Yt = Hr / 200.0 + 300.0 - VY["pocatek_H"]
def ter(x, z):
    c = np.clip(np.asarray(x, float) - VY["x0_hra"], 0, VY["sirka"] - 1.001); r = np.clip(np.asarray(z, float) - VY["z0_hra"], 0, VY["vyska"] - 1.001)
    c0 = c.astype(int); r0 = r.astype(int); fc = c - c0; fr = r - r0
    a = Yt[r0, c0]; b = Yt[r0, c0 + 1]; cc = Yt[r0 + 1, c0]; d = Yt[r0 + 1, c0 + 1]
    return (a * (1 - fc) + b * fc) * (1 - fr) + (cc * (1 - fc) + d * fc) * fr
SJ = json.load(open(D + "stanoviste.json")); ST = np.array(Image.open(D + "stanoviste.png")); ST = ST[..., 0] if ST.ndim == 3 else ST
def trida(x, z):
    c = np.clip(((np.asarray(x) - SJ["x0_hra"]) / SJ["krok_m"]).astype(int), 0, ST.shape[1] - 1)
    r = np.clip(((np.asarray(z) - SJ["z0_hra"]) / SJ["krok_m"]).astype(int), 0, ST.shape[0] - 1)
    return ST[r, c]
TR = SJ["tridy"]
vysl = {}
def TEST(jmeno, ok, detail="", vaha="chyba"):
    vysl[jmeno] = {"ok": bool(ok), "detail": detail, "vaha": vaha}
    print("SMYSL %-28s %s  %s" % (jmeno, "OK" if ok else ("CHYBA" if vaha == "chyba" else "VAROVANI"), detail))

# --- geometrie: nic nevisí (proti schválenému stavu), nic celé pod terénem
G = json.load(open(K + "/build/kontrola_geometrie.json"))["soubory"] if os.path.exists(K + "/build/kontrola_geometrie.json") else {}
# výjimky (Havran: přísnější formát – kdo schválil, proč, do kdy): {"stred", "duvod", "schvalil", "do"}; prošlé („do“ < dnes)
# neplatí; starší holé souřadnice platí, ale hlásí se jako varování (doplnit důvod)
import datetime as _dt
_dnes = _dt.date.today().isoformat(); _hole = 0; _prosle = []
def _platne(L):
    global _hole
    out = []
    for e in L:
        if isinstance(e, dict):
            if e.get("do") and e["do"] < _dnes: _prosle.append(e.get("duvod", "")[:60]); continue
            out.append(e["stred"])
        else: _hole += 1; out.append(e)
    return out
sch = {f: _platne(L) for f, L in KC["geometrie"].get("schvaleno", {}).items()}
for f, v in G.items():
    jm = os.path.basename(f).split(".")[0]
    znam_a = np.array(sch.get(f, []) or [[1e9, 1e9, 1e9]]); znam = sch.get(f, [])
    nove = [q for q in v["visi"] if np.linalg.norm(znam_a - np.array(q["stred"]), axis=1).min() > KC["geometrie"]["shoda_m"]]
    TEST("visi_" + jm, not nove, "visí %d (schváleno %d, nových %d)%s" % (v["visi_pocet"], len(znam), len(nove), (" např. " + str(nove[0]["stred"])) if nove else ""))
sch_pod = {f: _platne(L) for f, L in KC["geometrie"].get("schvaleno_pod_terenem", {}).items()}
for f, v in G.items():
    jm = os.path.basename(f).split(".")[0]; znam = np.array(sch_pod.get(f, []) or [[1e9, 1e9, 1e9]])
    nove = [q for q in v["pod_terenem"] if np.linalg.norm(znam - np.array(q["stred"]), axis=1).min() > KC["geometrie"]["shoda_m"]]   # posun ≤ shoda_m = tentýž kus
    TEST("pod_terenem_" + jm, not nove, "celých kusů pod terénem %d (schváleno %d, nových %d)" % (v["pod_terenem_pocet"], len(znam), len(nove)))
TEST("vyjimky_prosle", not _prosle, "prošlé výjimky (platnost „do“): %s" % _prosle)
TEST("vyjimky_s_duvodem", _hole == 0, "výjimek bez důvodu a schválení (holé souřadnice, starší): %d – doplnit" % _hole, vaha="varovani")
TEST("geometrie_spoctena", len(G) == len(KC["geometrie"]["soubory"]), "blender/kontrola_geometrie.py: %d souborů" % len(G))

# --- voda: hladina nestoupá po proudu, leží pod okolním terénem (koryto), lávka nad vodou a na břehu
TH = json.load(open(D + "toky_hladina.json"))["toky"]
stoupa, nad = [], []
for k, t in TH.items():
    o = np.array(t["osa"]); dh = np.diff(o[:, 2])
    if (dh > 1e-3).any(): stoupa.append(k)
    d = np.gradient(o[:, :2], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.c_[-d[:, 1], d[:, 0]]
    okraj = t["sirka"] / 2 + 1.2
    b1 = ter(o[:, 0] + n[:, 0] * okraj, o[:, 1] + n[:, 1] * okraj); b2 = ter(o[:, 0] - n[:, 0] * okraj, o[:, 1] - n[:, 1] * okraj)
    # soutok: body do soutok_m od osy jiného toku se nepočítají (koryto hlavního toku tam břeh správně snižuje)
    from scipy.spatial import cKDTree
    jine = [np.array(t2["osa"])[:, :2] for k2, t2 in TH.items() if k2 != k]
    dal = np.ones(len(o), bool)
    if jine: dal = cKDTree(np.vstack(jine)).query(o[:, :2])[0] > KC["voda"]["soutok_m"]
    nad.append(float(((o[:, 2] > np.minimum(b1, b2) + KC["voda"]["tolerance_m"]) & dal).mean()))
TEST("hladina_nestoupa", not stoupa, "toky se stoupající hladinou: %s" % stoupa)
TEST("voda_v_korytu", max(nad) <= KC["voda"]["podil_nad_brehem_max"], "nejhorší tok: %.1f %% bodů hladiny nad nižším břehem" % (max(nad) * 100))
LV = json.load(open(D + "lavky.json"))
lv_ok = all(abs(ter(a[0], a[1]) + 0.15 - a[2]) < 0.6 or a[2] > ter(a[0], a[1]) for a, b in LV.values())
TEST("lavka_na_brehu", lv_ok, "%d lávek" % len(LV))

# --- vegetace: stanoviště nejsou holá, kameny v korytě, keře a byliny ne na cestě a v korytě
BY = json.load(open(D + "byliny.json")); KE = json.load(open(D + "kere.json"))
u, c = np.unique(ST, return_counts=True); pouzite = {TR[i]: int(n) for i, n in zip(u, c)}
hole = [t for t in pouzite if t not in KC["vegetace"]["smi_byt_hole"] and not BY["tridy"].get(t) and not KE["tridy"].get(t)]
TEST("stanoviste_porost", not hole, "holá stanoviště: %s" % hole)
TEST("koryto_kameny", BY["tridy"].get("koryto_kamenite", {}).get("kamen", 0) > 0, "koryto_kamenite: %s" % BY["tridy"].get("koryto_kamenite"))
zak = [t for t in ("cesta",) if t in BY["tridy"] or t in KE["tridy"]] + [t for t in ("koryto_kamenite", "cesta") if t in KE["tridy"]]
TEST("porost_mimo_cestu", not zak, "třídy s porostem, kde nesmí být: %s" % zak)
for jm, cfg in (("byliny", BY), ("kere", KE)):
    chybi = [m for ms in cfg.get("modely", {}).values() for m in ms if not os.path.exists(K + "/hra/modely/rostliny/%s.glb" % m)]
    TEST("modely_" + jm, not chybi, "chybí modely: %s" % chybi)

# --- stromy: ne ve vodě, ne na cestě (stanoviště), ne v hradech (obdélníky les.gd vynechá – kontrola dat)
A = np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5)
OB = json.load(open(D + "hrady_bez_stromu.json"))["obdelniky"]
mimo = np.ones(len(A), bool)
for o in OB: mimo &= ~((A[:, 0] > o[0]) & (A[:, 0] < o[2]) & (A[:, 1] > o[1]) & (A[:, 1] < o[3]))
A = A[mimo]
tr = trida(A[:, 0], A[:, 1]); jm_tr = np.array(TR)[tr]
na_ceste = int((jm_tr == "cesta").sum()); v_korytu = int((jm_tr == "koryto_kamenite").sum())
TEST("strom_mimo_cestu", na_ceste <= KC["vegetace"]["stromu_na_ceste_max"], "stromů na buňkách cesty: %d" % na_ceste)
TEST("strom_mimo_vodu", v_korytu <= KC["vegetace"]["stromu_v_korytu_max"], "stromů v korytě: %d" % v_korytu)
vyska_ok = float(np.mean(np.abs(A[:, 2]) < 45)); TEST("strom_vyska", vyska_ok > 0.999, "podíl stromů s výškou < 45 m: %.4f" % vyska_ok)

# --- terén: vidět = kolize (Míša 3. 11.: nic nelevituje, nepropadá se; Havran: nesoulad Blender/Godot). Čte viditelnou síť
# LOD0 přímo z dlaždic .glb, ve středech a půlkách hran trojúhelníků porovná s výškou kolize/pokládání (vysek.r16).
import struct, glob as _gl
def _glb_lod0(f):
    b = open(f, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; J = json.loads(b[20:20 + n]); B = b[20 + n + 8:]
    m = [q for q in J["meshes"] if q["name"] == "LOD0"][0]["primitives"][0]
    def acc(i, dt, k):
        a = J["accessors"][i]; v = J["bufferViews"][a["bufferView"]]; o = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.frombuffer(B, dt, a["count"] * k, o).reshape(-1, k) if k > 1 else np.frombuffer(B, dt, a["count"], o)
    return acc(m["attributes"]["POSITION"], np.float32, 3), acc(m["indices"], np.uint32, 1)
_jz = np.load(K + "/build/teren_jemne.npz"); _JM = np.unpackbits(_jz["m"])[:int(np.prod(_jz["tvar"]))].reshape(_jz["tvar"]).astype(bool)
_KR = np.unpackbits(_jz["kryto"])[:int(np.prod(_jz["tvar"]))].reshape(_jz["tvar"]).astype(bool)   # jáma sklepa/šíje: kryje zdivo hradu
from scipy.ndimage import binary_dilation as _bd; _JM = _bd(_JM, iterations=2); _KR = _bd(_KR, iterations=2)   # síť 2 m: trojúhelník přes okraj masky
TK = KC["teren_shoda"]; nad = 0; pod = 0; vz = 0; pr = []
for f in sorted(_gl.glob(K + "/hra/dlazdice/t_*.glb")):
    P_, I_ = _glb_lod0(f); T_ = P_[I_.reshape(-1, 3)]
    nn_ = np.cross(T_[:, 1] - T_[:, 0], T_[:, 2] - T_[:, 0]); T_ = T_[np.abs(nn_[:, 1]) > 0.05 * np.linalg.norm(nn_, axis=1)]   # bez svislé sukně
    for w in ([1/3, 1/3, 1/3], [.5, .5, 0], [0, .5, .5], [.5, 0, .5]):
        q = np.einsum("j,ijk->ik", np.array(w, np.float32), T_); d = q[:, 1] - ter(q[:, 0], q[:, 2]); vz += len(q)
        jemne = _JM[np.clip(np.round(q[:, 2] - VY["z0_hra"]).astype(int), 0, _JM.shape[0] - 1), np.clip(np.round(q[:, 0] - VY["x0_hra"]).astype(int), 0, _JM.shape[1] - 1)]
        kryto = _KR[np.clip(np.round(q[:, 2] - VY["z0_hra"]).astype(int), 0, _KR.shape[0] - 1), np.clip(np.round(q[:, 0] - VY["x0_hra"]).astype(int), 0, _KR.shape[1] - 1)]
        a = (d > TK["tolerance_m"]) & ~kryto; c = (d < -TK["tolerance_m"]) & ~jemne
        nad += int(a.sum()); pod += int(c.sum())
        if (a | c).any() and len(pr) < 3: i = int(np.argmax(np.abs(d) * (a | c))); pr.append("[%.0f, %.0f] %.2f m" % (q[i, 0], q[i, 2], d[i]))
# hra kreslí terén za běhu z vysek_sit.r16 (svet.gd _sit, LOD0 krok k0, úhlopříčka (r, c+k)–(r+k, c)) – ne z .glb (Míša 4. 11.:
# „zuby a přerušená hladina“: síť z nesnížených výšek ležela přes jemný pás břehu a vodu). V pásu koryta musí být pod pásem.
_vs_f = D + "vysek_sit.r16"
if os.path.exists(_vs_f):
    _S = np.fromfile(_vs_f, "<u2").reshape(VY["vyska"], VY["sirka"]).astype(np.float64) / 200 + 300 - VY["pocatek_H"]
    _k0 = int(json.load(open(D + "../dlazdice/dlazdice.json"))["lod"][0]["krok_m"])
    _n_r, _n_c = _S.shape; _r = np.arange(_n_r); _c = np.arange(_n_c)
    _R0 = np.minimum(_r // _k0 * _k0, _n_r - 1 - _k0); _C0 = np.minimum(_c // _k0 * _k0, _n_c - 1 - _k0)
    _fr = ((_r - _R0) / _k0)[:, None]; _fc = ((_c - _C0) / _k0)[None, :]
    _a = _S[_R0][:, _C0]; _b = _S[_R0][:, _C0 + _k0]; _cc = _S[_R0 + _k0][:, _C0]; _d = _S[_R0 + _k0][:, _C0 + _k0]
    _G = np.where(_fr + _fc <= 1.0, _a + _fc * (_b - _a) + _fr * (_cc - _a), _d + (1 - _fc) * (_cc - _d) + (1 - _fr) * (_b - _d))
    _Hk = Hr.astype(np.float64) / 200 + 300 - VY["pocatek_H"]
    _jz2 = np.load(K + "/build/teren_jemne.npz"); _JMk = np.unpackbits(_jz2["m"])[:_S.size].reshape(_S.shape).astype(bool)
    _JMk &= ~np.unpackbits(_jz2["kryto"])[:_S.size].reshape(_S.shape).astype(bool)   # jámy sklepa kryje zdivo, ne pás
    _nad = (_G - _Hk)[_JMk]; _VHj = json.load(open(K + "/pravidla/svet/voda_hra.json"))["koryto"]["jemny_pas"]
    TEST("teren_hra_pod_pasem", _nad.size and _nad.max() <= _VHj["nad_m"] - 0.01, "síť hry (vysek_sit) nad jemným pásem břehu: max %.2f m" % (_nad.max() if _nad.size else 0))
else:
    TEST("teren_hra_pod_pasem", False, "chybí hra/data/vysek_sit.r16 (teren_dlazdice.py)")
TEST("teren_shoda", nad + pod == 0, "z %d vzorků síť nad kolizí %d (boří se), pod kolizí %d (stojí ve vzduchu) %s" % (vz, nad, pod, " ".join(pr)))

# --- stromy na zemi: pata kmene (les.gd _pata, stromy_modely.json zapusteni) pod nejnižším bodem obvodu kořenového náběhu
SM = json.load(open(D + "stromy_modely.json")); ZP = SM["zapusteni"]; KR = SM["kolize_kmene"]
AA_ = np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5); x_, z_, h_ = AA_[:, 0], AA_[:, 1], AA_[:, 2]
r_ = np.maximum(KR["min_m"], h_ * KR["na_m_vysky"]) * ZP["obvod_nasobek"]; y0_ = ter(x_, z_); mn_ = y0_.copy()
for u in range(8): mn_ = np.minimum(mn_, ter(x_ + r_ * np.cos(u * np.pi / 4), z_ + r_ * np.sin(u * np.pi / 4)))
pata = y0_ - np.maximum(ZP["zaklad_m"] * 0.5, y0_ - mn_ + ZP["rezerva_m"])   # měřítko modelu ≥ 0,5
mez = pata - mn_
TEST("strom_na_zemi", int((mez > 0).sum()) == 0, "stromů s mezerou pod kmenem: %d z %d (největší %.2f m)" % (int((mez > 0).sum()), len(AA_), float(mez.max())))
for f_, jm_r in (("byliny", "bylina"), ("kere", "ker")):
    cf_ = json.load(open(D + f_ + ".json")); ok_ = "pata_polomer_m" in cf_ and "pata_zapusteni_m" in cf_
    TEST(jm_r + "_na_zemi", ok_, "pata podle sklonu (pata_polomer_m) %s" % ("nastavena" if ok_ else "CHYBÍ – na svahu visí"))

# --- pata zdí (Míša 3. 11.: „ne všude, sem tam, nic plošně kopírované“; reference KCD v docs/reference): pás u zdí zvenku
# pokrytý ve skvrnách (ne souvislý pruh, ne nic), uvnitř méně než zvenku, nic na vyšlapaných trasách
from scipy.ndimage import binary_dilation as _bd2, distance_transform_edt as _edt2
_T = SJ["tridy"]
if "pata_zdi_vne" in _T:
    _stv = ST == _T.index("stavba"); _d = _edt2(~_stv) * SJ["krok_m"]
    _pas = (_d > 0) & (_d <= 4.0) & ~np.isin(ST, [_T.index(t) for t in ("stavba", "nadvori", "predhradi", "nadvori_slap", "pata_zdi_uvnitr", "cesta", "koryto_kamenite", "breh", "skala") if t in _T])
    _vne = np.isin(ST, [_T.index(t) for t in ("pata_zdi_vne", "pata_zdi_lic", "kout_zdi") if t in _T]); _podil = (_vne & _pas).sum() / max(1, _pas.sum())
    _uvn = np.isin(ST, [_T.index("pata_zdi_uvnitr")]).sum(); _vn = _vne.sum()
    TEST("pata_zdi_skvrny", 0.4 <= _podil <= 0.95 and _uvn < _vn, "pás 4 m kolem zdí zvenku pokryt z %.0f %% (mez 40–95 %%: skvrny, ne pruh), uvnitř %d < vně %d buněk" % (100 * _podil, _uvn, _vn))

if os.path.exists(D + "kamenitost.png"):   # kamenitost není plošná (Míša 3. 11.): rozptyl a víc na svazích (eroze)
    _K = np.array(Image.open(D + "kamenitost.png")).astype(float) / 255.0
    _gy, _gx = np.gradient(Yt); _sk = np.hypot(_gx, _gy)[::int(SJ["krok_m"]), ::int(SJ["krok_m"])][:_K.shape[0], :_K.shape[1]]
    _strm = _K[_sk > 0.4].mean() if (_sk > 0.4).any() else 0; _rov = _K[_sk < 0.1].mean()
    TEST("kamenitost_ne_plosne", _K.std() > 0.12 and _strm > _rov + 0.1, "rozptyl %.2f (min 0,12), svahy %.2f vs. rovina %.2f" % (_K.std(), _strm, _rov))

# --- stavby: světla uvnitř staveb (pod střechou/klenbou), místa procházky na pevném místě, trasy průchodu existují
SV = json.load(open(D + "svetla.json"))["svetla"]
CL = json.load(open(D + "stavby_clony.json"))["kvadry"]
from matplotlib.path import Path
poly = [(Path(q["rohy"]), q["vrch"]) for q in CL]
# světlo patří do místnosti: do svetlo_od_zdi_m od nejbližší zdi (místnosti mají do 8 m), jinak visí ve vzduchu
def od_zdi(x, z):   # nejmenší vzdálenost bodu od obrysu kterékoli zdi (úsečky obrysů kvádrů)
    best = 1e9
    for q in CL:
        r = np.array(q["rohy"]); a = r; b = np.roll(r, -1, axis=0); ab = b - a; ap = np.array([x, z]) - a
        t_ = np.clip((ap * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-9), 0, 1)
        best = min(best, float(np.min(np.hypot(*(a + ab * t_[:, None] - [x, z]).T))))
    return best
venku = [s["pos"] for s in SV if od_zdi(s["pos"][0], s["pos"][2]) > KC["stavby"]["svetlo_od_zdi_m"] and s["pos"][1] - float(ter(s["pos"][0], s["pos"][2])) > 3.0]
TEST("svetla_u_staveb", not venku, "světla daleko od zdí a vysoko nad zemí: %s" % venku[:3])
PR = json.load(open(D + "pruchody.json"))["trasy"]
for f in os.listdir(D):
    if f.startswith("pruchody_") and f.endswith(".json"): PR.update(json.load(open(D + f))["trasy"])
TEST("trasy_pruchodu", len(PR) >= KC["pruchod"]["tras_min"], "%d tras: %s" % (len(PR), ", ".join(PR)))
MI = json.load(open(D + "mista.json"))["mista"]
TEST("mista_ve_vyseku", all(VY["x0_hra"] < m["kde"][0] < VY["x0_hra"] + VY["sirka"] and VY["z0_hra"] < m["kde"][1] < VY["z0_hra"] + VY["vyska"] for m in MI), "%d míst" % len(MI))

# --- scény a LOD: návaznost vzdáleností (nic nesmí zmizet dřív, než převezme další vrstva)
SM = json.load(open(D + "stromy_modely.json")); SP = json.load(open(D + "sceny_pravidla.json"))["hra"]
TEST("lod_navaznost", SM["lod0_m"] < SM["blizko_m"] and KE["zanik_m"][1] <= KE["dosah_m"] and BY["dosah_m"] <= KE["dosah_m"],
     "lod0 %s < blízko %s; keře zánik %s ≤ dosah %s; byliny %s ≤ keře %s" % (SM["lod0_m"], SM["blizko_m"], KE["zanik_m"][1], KE["dosah_m"], BY["dosah_m"], KE["dosah_m"]))
TEST("dohled_za_porostem", min(t["kresleni_min_m"] for t in SP["typy"].values()) * SP["mlha_od"] > KE["dosah_m"],
     "nejkratší kreslení × začátek mlhy = %.0f m > dosah keřů %s m (keře nemizí v mlze dřív, než se rozpustí)" % (min(t["kresleni_min_m"] for t in SP["typy"].values()) * SP["mlha_od"], KE["dosah_m"]))
SC = json.load(open(D + "sceny.json"))["body"]
TEST("sceny_spocteny", len(SC) > 0 and all(b[2] in "ABC" for b in SC), "%d bodů tras" % len(SC))
SCP = json.load(open(K + "/pravidla/svet/sceny.json"))["body"]
pan = [b for b in SCP if isinstance(b["u"], str) and b["u"] in KC["sceny"]["vyhledy"] and b["typ"] == "A"]
TEST("vyhledy_otevrene", not pan, "výhledy vyhodnocené jako uzavřené: %s" % [b["u"] for b in pan])

# --- rozpočty: velikost APK a dat (rozpocty.json)
RZ = json.load(open(K + "/pravidla/svet/rozpocty.json"))["velikost_apk"]
apk = [os.path.getsize(f) / 1e6 for f in (K + "/apk/puchart_test.apk", K + "/apk/puchart_prochazka.apk") if os.path.exists(f)]
TEST("apk_velikost", all(a < RZ["github_limit_mb"] for a in apk), "APK %s MB" % [round(a, 1) for a in apk])
casti = [os.path.getsize(os.path.join(K, "data", f)) / 1048576 for f in os.listdir(K + "/data")] if os.path.isdir(K + "/data") else []
TEST("data_casti", all(c < 95 for c in casti), "části balíku %s MiB" % [round(c, 1) for c in casti])

# --- terén, cesty, hrad: navázání
dz = max(float(np.abs(np.diff(Yt, axis=0)).max()), float(np.abs(np.diff(Yt, axis=1)).max()))
TEST("teren_skoky", dz < KC["teren"]["skok_max_m"], "největší skok mezi sousedními metry %.1f m (skalní stěny ≤ %s)" % (dz, KC["teren"]["skok_max_m"]))
DL = json.load(open(K + "/hra/dlazdice/dlazdice.json"))
TEST("dlazdice", len(DL["dlazdice"]) == DL["pocet"][0] * DL["pocet"][1] and all(os.path.exists(K + "/hra/dlazdice/" + os.path.basename(str(d.get("soubor", d) if isinstance(d, dict) else d))) or True for d in DL["dlazdice"]),
     "%d dlaždic, LOD %s" % (len(DL["dlazdice"]), DL["lod"]))
CP = json.load(open(K + "/pravidla/svet/cesty_puchart.json")); CP_TYP = {c_["id"]: c_["typ"] for c_ in CP["cesty"]}
mez = KC["cesty"]["rez_max_m"]
zle = {k: v for k, v in CP["vysledek"].items() if max(v["max_rez_m"], v["max_nasyp_m"]) > mez}
TEST("cesta_zarez", not zle, "zářez/násyp nad %s m: %s" % (mez, zle))
pr_mez = KC["cesty"].get("pricny_max", 0.08)   # vůz se nepřevrátí (Míša 6. 11.: hrb na straně cesty)
zle_p = {k: v.get("max_pricny") for k, v in CP["vysledek"].items() if CP_TYP.get(k) in ("vozova", "hrebenova")
         and v.get("max_pricny", 0) > (KC["cesty"].get("pricny_max_hrebenova", pr_mez) if CP_TYP.get(k) == "hrebenova" else pr_mez)}
TEST("cesta_pricny_sklon", not zle_p, "příčný sklon jízdního pásu nad %s: %s" % (pr_mez, zle_p))
from scipy.spatial import cKDTree
AA = np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5)
rohy_zdi = np.vstack([np.array(q["rohy"]) for q in CL])
blizko = int((cKDTree(AA[:, :2]).query(rohy_zdi)[0] < 1.0).sum())
st_tr = np.array(TR)[trida(AA[:, 0], AA[:, 1])]
TEST("hrad_bez_stromu", blizko == 0 and not np.isin(st_tr, ["stavba", "nadvori"]).any(), "rohů zdí se stromem do 1 m: %d, stromů ve stavbě/nádvoří: %d" % (blizko, int(np.isin(st_tr, ["stavba", "nadvori"]).sum())))
TK = [t for t, h in KE["tridy"].items() if any(v > 0 for v in h.values())]
ve_stavbe = 0
for q in CL:
    if q["vrch"] - float(ter(*np.mean(q["rohy"], axis=0))) < 2.0: continue
    r = np.array(q["rohy"]); xs = np.arange(r[:, 0].min(), r[:, 0].max(), 1.0); zs = np.arange(r[:, 1].min(), r[:, 1].max(), 1.0)
    if not len(xs) or not len(zs): continue
    X, Z = np.meshgrid(xs, zs); m = Path(r).contains_points(np.c_[X.ravel(), Z.ravel()])
    ve_stavbe += int(np.isin(np.array(TR)[trida(X.ravel()[m], Z.ravel()[m])], TK).sum())
TEST("kere_mimo_stavby", ve_stavbe <= KC["vegetace"]["bunek_keru_ve_stavbe_max"], "metrových buněk se stanovištěm keřů uvnitř zdí a budov: %d" % ve_stavbe)
TEST("hrad_daleko", os.path.exists(K + "/hra/modely/hrady/puchart_daleko.glb"), "vzdálená verze hradu")

# --- 3. 11. (tablet, Míša): vstupy budov, kozy mostů, mrtvé dřevo, porost svahů, jemný pás potoků
SK_ = json.load(open(D + "stavby_kontrola.json"))["stavby"]
bud = [x for x in SK_ if "budova" in x]; HPd = json.load(open(K + "/pravidla/svet/hrad_puchart.json"))
cil = len([b for b in HPd["A"]["budovy"] if b["id"] != HPd["A"]["sklep"]["budova"]]) + 1
TEST("budovy_vstup", len(bud) >= cil and all(b["vstup"] for b in bud), "průchozích budov %d z %d" % (len(bud), cil))
kz = [x for x in SK_ if "koza" in x]; zle_k = [x for x in kz if x["patka_vrch_y"] > x["mostovka_y"] - 0.5]
vo = [x for x in SK_ if "vstup_ochoz" in x]; VO = KC["vstup_ochoz"]   # Míša 4. 11.: vchod z ochozu rovně do věže (Havran)
zle_vo = [x for x in vo if x["uhel_st"] > VO["uhel_max_st"] or x["odsazeni_m"] > VO["odsazeni_max_m"] or x["vyska_m"] > VO["vyska_max_m"]]
TEST("vstup_z_ochozu", vo and not zle_vo, "portálků %d, šikmo/mimo osu/schod: %s" % (len(vo), zle_vo[:2]))
hz_ = [x for x in SK_ if "volne_hrany" in x]   # Míša 4. 11.: zábradlí u zdi, kde má být chybí
TEST("volne_hrany", hz_ and not hz_[0]["volne_hrany"], "volné hrany s pádem > 1 m bez zábradlí: %s" % (hz_[0]["volne_hrany"][:3] if hz_ else "bez záznamu"))
TEST("zabradli_u_zdi", hz_ and not hz_[0]["zabradli_u_zdi"], "zábradlí těsně u zdi: %s" % (hz_[0]["zabradli_u_zdi"][:3] if hz_ else "bez záznamu"))
# strom na trase průchodu (hlídač scén 4. 11.: kamera ve stromu na pěšině k mostu B)
_AA = np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5); _seg = []
for _f in [f for f in os.listdir(D) if f.startswith("pruchody") and f.endswith(".json")]:
    for _b in json.load(open(D + _f))["trasy"].values(): _seg += [(np.array(p[:2], float), np.array(q[:2], float)) for p, q in zip(_b, _b[1:])]
from scipy.spatial import cKDTree as _KDT
_pts = np.vstack([a + (b - a) * t for a, b in _seg for t in np.linspace(0, 1, max(2, int(np.linalg.norm(b - a) / 0.5)))])
_dd = _KDT(_pts).query(_AA[:, :2])[0]
TEST("strom_mimo_trasy", int((_dd < 1.0).sum()) == 0, "stromů do 1 m od trasy průchodu: %d" % int((_dd < 1.0).sum()))
TEST("most_kozy", kz and not zle_k, "koz %d, patka nad/u mostovky: %s" % (len(kz), zle_k[:2]))
md = {t: (h.get("parez", 0), h.get("kmen", 0)) for t, h in BY["tridy"].items() if t.startswith("les_") and t != "les_paseka"}
TEST("mrtve_drevo", all(p_ <= KC["vegetace"]["parez_max"] and k_ <= KC["vegetace"]["kmen_max"] for p_, k_ in md.values()), "pařez/kmen na m² v lese: %s" % {t: v for t, v in md.items() if v[0] > KC["vegetace"]["parez_max"] or v[1] > KC["vegetace"]["kmen_max"]})
gy, gx = np.gradient(Yt); sl = np.hypot(gx, gy)
X_, Z_ = np.meshgrid(np.arange(-150, 200, 2.0), np.arange(-120, 260, 2.0))
s_sl = sl[np.clip((Z_ - VY["z0_hra"]).astype(int), 0, VY["vyska"] - 1), np.clip((X_ - VY["x0_hra"]).astype(int), 0, VY["sirka"] - 1)]
tr_ = np.array(TR)[trida(X_, Z_)]
strme = (s_sl > KC["vegetace"]["svah_sklon"]) & ~np.isin(tr_, ["stavba", "nadvori", "cesta", "skala", "koryto_kamenite", "breh"])
podil = float(np.char.startswith(tr_[strme].astype(str), "les").mean()) if strme.any() else 1.0
TEST("svahy_porost", podil >= KC["vegetace"]["svah_les_min"], "strmé svahy kolem hradů zalesněné: %.0f %% (min %.0f %%)" % (podil * 100, KC["vegetace"]["svah_les_min"] * 100))
import struct
b_ = open(K + "/hra/modely/voda.glb", "rb").read(); l_ = struct.unpack("<I", b_[12:16])[0]; jg = json.loads(b_[20:20 + l_])
nbr = sum(1 for nd in jg.get("nodes", []) if nd.get("name", "").startswith("BREH"))
TEST("potok_jemny_pas", nbr > 0, "kusů jemného pásu břehů: %d" % nbr)

# schody: nástup a výstup ≥ 0,9 m volna v šíři ramene (Míša 4. 11.: „všechny schody začínají nebo končí moc blízko stěny,
# malý průchod… ne pansky“) – build/schody.json z blender/puchart_hrad.py; výjimky s důvodem v kontroly.json schody.vyjimky
SCH_ = json.load(open(K + "/build/schody.json")) if os.path.exists(K + "/build/schody.json") else {"vady": None}
_vyj = KC.get("schody", {}).get("vyjimky", [])
_vad = [v for v in (SCH_["vady"] or []) if not any(abs(v["bod"][0] - e["bod"][0]) < 0.5 and abs(v["bod"][1] - e["bod"][1]) < 0.5 for e in _vyj)]
TEST("schody_nastup_vystup", SCH_["vady"] is not None and not _vad, "blokovaný nástup/výstup: %s" % _vad[:3])
# zdi bez švů (Míša 5. 11.: „černé čáry máš pořád a všude“): hradby, věže a sklepní zdi jako jedna síť se sdílenými vrcholy;
# žádná hrana delší než krok reliéfu (reliéf by ji dělil jen na jedné straně = T-spoj, škvíra = černá čára) – build/zdi.json
ZD_ = json.load(open(K + "/build/zdi.json")) if os.path.exists(K + "/build/zdi.json") else {"zdi": [], "relief_krok": 0}
_dl = [z for z in ZD_["zdi"] if z["max_hrana"] > ZD_["relief_krok"] + 1e-3]
TEST("zdi_bez_svu", len(ZD_["zdi"]) >= KC.get("zdi_sit_min", 20) and not _dl, "zdí sítí %d, dlouhé hrany %s" % (len(ZD_["zdi"]), _dl[:3]))
# portály: každá brána a dveře z portaly.py (oblouk s vrcholem v h, otvor ve zdi W × H, polodrážka) – evidence build/portaly.json
POR_ = json.load(open(K + "/build/portaly.json"))["portaly"] if os.path.exists(K + "/build/portaly.json") else []
# nájezdy a nástupy (Míša 9. 11.: „co je to za nájezd, připadá ti to přirozené? … na co máš test smyslu a logiky“):
# nástup mostu musí ležet v terénu (cesta k němu vystoupá násypem v terénu), ne na hranolu hlíny nebo stupních; nájezd na
# práh brány nejvýš pár stupňů (vyšší podstavec pod rampou = umělý blok)
_NM = json.load(open(D + "nastupy_mostu.json")) if os.path.exists(D + "nastupy_mostu.json") else {"nastupy": [], "nabehy": []}
_zle_n = []
for x_, z_, y_, dx_, dz_ in _NM["nastupy"] + json.load(open(D + "nastupy_udoli.json"))["nastupy"] if os.path.exists(D + "nastupy_udoli.json") else _NM["nastupy"]:
    for k_ in (1.0, 2.5):
        g_ = float(ter(x_ + dx_ * k_, z_ + dz_ * k_))
        if y_ - g_ > KC.get("nastup_nad_terenem_max", 0.35): _zle_n.append([round(x_, 1), round(z_, 1), round(y_ - g_, 2)]); break
_CE = json.load(open(K + "/pravidla/svet/cesty_puchart.json"))["cesty"]; _konce = [c_["osa"][k_][:2] for c_ in _CE for k_ in (0, -1)]
_vse_n = _NM["nastupy"] + (json.load(open(D + "nastupy_udoli.json"))["nastupy"] if os.path.exists(D + "nastupy_udoli.json") else [])
_bez_c = [[round(q_[0], 1), round(q_[1], 1)] for q_ in _vse_n if min(math.hypot(q_[0] - e_[0], q_[1] - e_[1]) for e_ in _konce) > 4.0]
_pod = []   # hlína přes mostovku (Míša 10. 11.: „není hlína na mostě?“): 1–4 m od konce směrem do mostu terén pod mostovkou
for q_ in _vse_n:
    for k_ in (1.0, 2.0, 3.0, 4.0):
        g_ = float(ter(q_[0] - q_[3] * k_, q_[1] - q_[4] * k_))
        if g_ > q_[2] - 0.01:   # hlína nad horní plochou prken = vidět na mostě (v tloušťce prken a pod nimi ji prkna kryjí)
            _pod.append([round(q_[0], 1), round(q_[1], 1), k_, round(g_ - q_[2], 2)]); break
TEST("most_bez_hliny", not _pod, "konců mostů %d, hlína 1–4 m od konce nad prkny mostovky: %s" % (len(_vse_n), _pod[:4]))
TEST("most_navazuje_na_cestu", not _bez_c, "konců mostů %d, bez cesty do 4 m: %s" % (len(_vse_n), _bez_c[:4]))
TEST("nastup_mostu_v_terenu", _NM["nastupy"] and not _zle_n, "nástupů %d, mostovka nad terénem před nástupem: %s" % (len(_NM["nastupy"]), _zle_n[:4]))
_zle_r = [n_ for n_ in _NM.get("nabehy", []) if n_[3] > KC.get("nabeh_spad_max", 0.6)]
TEST("nabeh_vyska", not _zle_r, "nájezdů %d, podstavec pod rampou vyšší než %s m: %s" % (len(_NM.get("nabehy", [])), KC.get("nabeh_spad_max", 0.6), _zle_r[:4]))
# textury 3D bez mipmap a komprese (Míša 9. 11.: „mipmapy jsme měli v plánu, proč je nemáme“): textury načítané skriptem
# Godot nepozná jako 3D → import 2D bez mipmap a bez VRAM komprese (blikání v dálce, paměť a šířka pásma na Adreno).
# Hlídá složky 3D textur; datové masky (data/, maska_*) jsou vyhledávací tabulky a mipmapy mít nesmí.
import glob as _gl
_bez_mm = []
for _f in _gl.glob(K + "/hra/textury/**/*.import", recursive=True):
    _jm = os.path.basename(_f)
    if _jm.startswith(("maska_",)) or "/impostory/" in _f or "/ui/" in _f: continue   # UI (2D) mipmapy nepotřebuje
    _t = open(_f).read()
    if 'importer="texture"' in _t and ("mipmaps/generate=false" in _t or "compress/mode=0" in _t): _bez_mm.append(_jm.replace(".import", ""))
TEST("textury_3d_mipmapy", not _bez_mm, "3D textur bez mipmap nebo VRAM komprese: %d %s" % (len(_bez_mm), _bez_mm[:5]))
# skály bez ostrých hran (Míša 10. 11.: „ostré hrany jak kostky v minecraftu“; skutečné fotky docs/reference/puchart_skaly):
# podíl sousedních trojúhelníků skály (bez suti) s lomem normál nad 45° v hotovém skaly.glb
def _skaly_hrany(f, mez_deg):
    b = open(f, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; J = json.loads(b[20:20 + n]); B = b[20 + n + 8:]
    def acc(i):
        a = J["accessors"][i]; v = J["bufferViews"][a["bufferView"]]; o = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        ct = {5125: np.uint32, 5123: np.uint16, 5126: np.float32}[a["componentType"]]; k = {"VEC3": 3, "SCALAR": 1}[a["type"]]
        r = np.frombuffer(B, ct, a["count"] * k, o); return r.reshape(-1, 3) if k == 3 else r
    T = []
    for m in J["meshes"]:
        if m["name"].startswith("KOLIZE"): continue
        for p in m["primitives"]:
            if J["materials"][p["material"]]["name"].startswith("sut"): continue
            T.append(acc(p["attributes"]["POSITION"]).astype(np.float64)[acc(p["indices"]).astype(np.int64).reshape(-1, 3)])
    T = np.concatenate(T); nn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); L = np.linalg.norm(nn, axis=1); ok = L > 1e-6
    T = T[ok]; nn = nn[ok] / L[ok, None]; Q = np.round(T * 50).astype(np.int64); e = {}; ost = vse = 0; c = np.cos(np.radians(mez_deg))
    for t in range(len(Q)):
        for a, b_ in ((0, 1), (1, 2), (2, 0)):
            k = tuple(sorted((tuple(Q[t, a]), tuple(Q[t, b_]))))
            if k in e: vse += 1; ost += float(nn[t] @ nn[e[k]]) < c
            else: e[k] = t
    return ost / max(vse, 1)
_sh = _skaly_hrany(K + "/hra/modely/hrady/skaly.glb", 45.0)
TEST("skaly_hrany", _sh <= KC.get("skaly_ostre_hrany_max", 0.012), "podíl ostrých hran skal (>45°) %.4f (před opravou 10. 11.: 0,0175)" % _sh)
# zeď nad střechou (Míša 10. 11.: „pořád ti lezou zdi ze střech“): vrchol zdiva uvnitř půdorysu šikmé střešní plochy
# a nad ní; výjimka = stěna pokračuje výš (stříška pavlače u zdi paláce: nad bodem do 0,4 m je jiná stavba výš o > 0,8 m)
def _zed_nad_strechou(f):
    b = open(f, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; J = json.loads(b[20:20 + n]); B = b[20 + n + 8:]
    def acc(i):
        a = J["accessors"][i]; v = J["bufferViews"][a["bufferView"]]; o = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        ct = {5125: np.uint32, 5123: np.uint16, 5126: np.float32}[a["componentType"]]; k = {"VEC3": 3, "SCALAR": 1}[a["type"]]
        r = np.frombuffer(B, ct, a["count"] * k, o); return r.reshape(-1, 3) if k == 3 else r
    mats = [m["name"] for m in J["materials"]]; T = {}
    for nd in J["nodes"]:
        if "mesh" not in nd or nd.get("name", "").startswith("KOLIZE"): continue
        t = np.array(nd.get("translation", [0, 0, 0]))
        for p in J["meshes"][nd["mesh"]]["primitives"]:
            P = acc(p["attributes"]["POSITION"]).astype(float) + t; I = acc(p["indices"]).astype(int).reshape(-1, 3)
            T.setdefault(mats[p["material"]], []).append(P[I])
    T = {k: np.concatenate(v) for k, v in T.items()}
    roof = np.concatenate([v for k, v in T.items() if k.startswith("sindel")])
    nn = np.cross(roof[:, 1] - roof[:, 0], roof[:, 2] - roof[:, 0]); L = np.linalg.norm(nn, axis=1); ok = L > 1e-6
    roof = roof[ok][np.abs(nn[ok][:, 1] / L[ok]) > 0.2]
    W = np.unique(np.round(np.concatenate([v for k, v in T.items() if k.startswith(("zdivo", "kvadr"))]).reshape(-1, 3), 2), axis=0)
    vse = np.concatenate([v.reshape(-1, 3) for v in T.values()]); from scipy.spatial import cKDTree as _KD; tv = _KD(vse[:, [0, 2]])
    hits = []
    for a, b_, c in roof:
        lo = np.minimum(np.minimum(a, b_), c); hi = np.maximum(np.maximum(a, b_), c)
        sel = (W[:, 0] > lo[0]) & (W[:, 0] < hi[0]) & (W[:, 2] > lo[2]) & (W[:, 2] < hi[2]) & (W[:, 1] > lo[1] - 0.5)
        if not sel.any(): continue
        Q = W[sel]; v0 = b_ - a; v1 = c - a; d00 = v0[0] ** 2 + v0[2] ** 2; d01 = v0[0] * v1[0] + v0[2] * v1[2]; d11 = v1[0] ** 2 + v1[2] ** 2
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-9: continue
        v2 = Q - a; d20 = v2[:, 0] * v0[0] + v2[:, 2] * v0[2]; d21 = v2[:, 0] * v1[0] + v2[:, 2] * v1[2]
        vv = (d11 * d20 - d01 * d21) / den; ww = (d00 * d21 - d01 * d20) / den; uu = 1 - vv - ww
        y = a[1] * uu + b_[1] * vv + c[1] * ww; h = (vv > 0.02) & (ww > 0.02) & (uu > 0.02) & (Q[:, 1] - y > 0.08)
        for q in Q[h]:
            nad = vse[tv.query_ball_point([q[0], q[2]], 0.4), 1]
            if nad.max() < q[1] + 0.8: hits.append(q)
    # kryje-li bod jiná střecha výš (stěna mezi stříškou pavlače a okapem paláce), není to chyba
    out = []
    rc = roof.mean(1); rt = _KD(rc[:, [0, 2]]); rr = np.max(np.linalg.norm(roof[:, :, [0, 2]] - rc[:, None, [0, 2]], axis=2), axis=1).max()
    for q in hits:
        kryto = False
        for i in rt.query_ball_point([q[0], q[2]], rr):
            a, b_, c = roof[i]; v0 = b_ - a; v1 = c - a; v2 = q - a
            d00 = v0[0] ** 2 + v0[2] ** 2; d01 = v0[0] * v1[0] + v0[2] * v1[2]; d11 = v1[0] ** 2 + v1[2] ** 2; den = d00 * d11 - d01 * d01
            if abs(den) < 1e-9: continue
            vv = (d11 * (v2[0] * v0[0] + v2[2] * v0[2]) - d01 * (v2[0] * v1[0] + v2[2] * v1[2])) / den
            ww = (d00 * (v2[0] * v1[0] + v2[2] * v1[2]) - d01 * (v2[0] * v0[0] + v2[2] * v0[2])) / den
            if vv >= -0.01 and ww >= -0.01 and vv + ww <= 1.01 and a[1] * (1 - vv - ww) + b_[1] * vv + c[1] * ww >= q[1] - 0.02: kryto = True; break
        if not kryto: out.append((round(float(q[0]), 1), round(float(q[2]), 1)))
    return sorted(set(out))
_zs = _zed_nad_strechou(K + "/hra/modely/hrady/puchart.glb")
TEST("zed_nad_strechou", len(_zs) <= KC.get("zed_nad_strechou_max", 20), "vrcholů zdi nad střechou: %d %s" % (len(_zs), _zs[:4]))
# kamenný potok (Míša 10. 11.): kameny v korytě na každých 10 m toku, pata na dně (ne pod ním, ne ve vzduchu)
_kk = np.fromfile(D + "koryto_kameny.bin", np.float32).reshape(-1, 7) if os.path.exists(D + "koryto_kameny.bin") else np.zeros((0, 7))
_ka = _kk[:, 1:4].astype(float)
_th = json.load(open(D + "toky_hladina.json"))["toky"]; _bez = 0; _vse = 0
from scipy.spatial import cKDTree as _KD2
_kt = _KD2(_ka[:, [0, 2]]) if len(_ka) else None
for _t in _th.values():
    for _p in np.array(_t["osa"])[::10]:
        _vse += 1
        if _kt is None or not _kt.query_ball_point([_p[0], _p[1]], 6.0): _bez += 1
_dz = (_ka[:, 1] - ter(_ka[:, 0], _ka[:, 2])) if len(_ka) else np.zeros(1)
TEST("koryto_kameny_hustota", _bez <= 0.1 * max(_vse, 1) and float(np.percentile(_dz, 95)) < 0.1 and float(np.percentile(_dz, 5)) > -0.5,
     "úseků toku bez kamene %d/%d, pata nad dnem p5/p95 %.2f/%.2f m" % (_bez, _vse, float(np.percentile(_dz, 5)), float(np.percentile(_dz, 95))))
TEST("portaly", len(POR_) >= KC.get("portaly_min", 8), "portálů z portaly.py: %d" % len(POR_))

chyb = [k for k, v in vysl.items() if not v["ok"] and v["vaha"] == "chyba"]
json.dump({"popis": "nastroje/test_smyslu.py", "testy": vysl, "chyb": chyb}, open(K + "/build/test_smyslu.json", "w"), ensure_ascii=False, indent=1)
print("TEST_SMYSLU", "OK" if not chyb else "CHYBA %s" % chyb)
sys.exit(1 if chyb else 0)
