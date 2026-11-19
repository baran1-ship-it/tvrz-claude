"""Test smyslu Puchartu (vrstva 1 hlídačů z Havrana; Míša 2. 11.: „vše o sobě ví a spolupracuje“). Rychlé kontroly nad
upečenými daty, bez Godotu (sekundy). Každý test má jméno smysl:<jmeno> – na ně odkazuje matice vztahů (vztahy.json
testy_puchart) a tabulka chyb (docs/chyby.md). Výsledek build/test_smyslu.json; rc 1 = nevydávat.
Geometrii (visí / pod terénem) počítá blender/kontrola_geometrie.py – zde se porovná se schváleným stavem
(pravidla/svet/kontroly.json geometrie.schvaleno): nový visící kus = chyba, opravený = zlepšení.
  python3 nastroje/test_smyslu.py <koren>"""
import sys, os, json, math, re
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
TEST("geometrie_spoctena", len(G) == len(KC["geometrie"]["soubory"]) and json.load(open(K + "/build/kontrola_geometrie.json")).get("hotovo"), "blender/kontrola_geometrie.py: %d souborů" % len(G))

# --- voda: hladina nestoupá po proudu, leží pod okolním terénem (koryto), lávka nad vodou a na břehu
TH = json.load(open(D + "toky_hladina.json"))["toky"]
stoupa, nad = [], []
for k, t in TH.items():
    o = np.array(t["osa"]); dh = np.diff(o[:, 2])
    if (dh > 1e-3).any(): stoupa.append(k)
    d = np.gradient(o[:, :2], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.c_[-d[:, 1], d[:, 0]]
    # brod (voda_hra.json koryto.brod rozliti_sirky, Míša 13. 11.): voda se v pásu brodu rozlévá – břeh se měří od rozlitého kraje
    _rz = json.load(open(K + "/pravidla/svet/voda_hra.json"))["koryto"].get("brod", {}).get("rozliti_sirky", 1.0)
    okraj = t["sirka"] / 2 * (1 + np.array(t.get("brod_vaha", [0.0] * len(o))) * (_rz - 1)) + 1.2
    b1 = ter(o[:, 0] + n[:, 0] * okraj, o[:, 1] + n[:, 1] * okraj); b2 = ter(o[:, 0] - n[:, 0] * okraj, o[:, 1] - n[:, 1] * okraj)
    # soutok: body do soutok_m od osy jiného toku se nepočítají (koryto hlavního toku tam břeh správně snižuje)
    from scipy.spatial import cKDTree
    jine = [np.array(t2["osa"])[:, :2] for k2, t2 in TH.items() if k2 != k]
    dal = np.ones(len(o), bool)
    if jine: dal = cKDTree(np.vstack(jine)).query(o[:, :2])[0] > KC["voda"]["soutok_m"]
    nad.append(float(((o[:, 2] > np.minimum(b1, b2) + KC["voda"]["tolerance_m"]) & dal).mean()))
TEST("hladina_nestoupa", not stoupa, "toky se stoupající hladinou: %s" % stoupa)
TEST("voda_v_korytu", max(nad) <= KC["voda"]["podil_nad_brehem_max"], "nejhorší tok: %.1f %% bodů hladiny nad nižším břehem" % (max(nad) * 100))
# brod (Míša 13. 11.: „brod k hájovně není dobrý“ – příkop s hrbem): od kraje vody napříč tokem pozvolný nájezd
# (voda_hra.json koryto.brod sklon_najezdu, s rezervou na vyhlazení terénu a profil cesty)
KO_ = json.load(open(K + "/pravidla/svet/voda_hra.json"))["koryto"]; BRK = KO_.get("brod", {}); spatne_br = []
for k, t in TH.items():
    o = np.array(t["osa"])
    for i in t.get("brody", []):
        d = o[min(i + 1, len(o) - 1), :2] - o[max(i - 1, 0), :2]; d /= np.linalg.norm(d) + 1e-9; n = np.array([-d[1], d[0]])
        # nájezd končí u jiného koryta (druhé rameno téhož toku nebo jiný tok): jeho břeh a práh už nejsou nájezd brodu
        # (tok 9 (211, 848): rameno o 2 m výš 6 m od brodu – nájezd 10 % se tam nevejde, viz docs/chyby.md)
        so_ = np.r_[0, np.cumsum(np.hypot(*np.diff(o[:, :2], axis=0).T))]
        jine_ = [np.array(t2["osa"])[:, :2] for k2, t2 in TH.items() if k2 != k] + [o[np.abs(so_ - so_[i]) > BRK.get("polosirka_m", 3) + BRK.get("nabeh_m", 5) + 2, :2]]
        sir_ = [t2["sirka"] for k2, t2 in TH.items() if k2 != k] + [t["sirka"]]
        for sg in (1, -1):
            dd = t["sirka"] / 2 + np.arange(0.0, 9.0, 1.0)
            px_, pz_ = o[i, 0] + sg * n[0] * dd, o[i, 1] + sg * n[1] * dd
            u_ = np.zeros(len(dd), bool)
            for a_, s2_ in zip(jine_, sir_):
                if len(a_): u_ |= cKDTree(a_).query(np.c_[px_, pz_])[0] < s2_ / 2 + KO_["prah_m"] + 1.0
            if u_.any(): dd = dd[:max(1, int(np.argmax(u_)))]
            y = ter(o[i, 0] + sg * n[0] * dd, o[i, 1] + sg * n[1] * dd)
            mx = float(np.max(np.diff(y))) if len(y) > 1 else 0
            voz_ = next((bt_.get("vozovy", True) for bt_ in t.get("brody_tvar", []) if bt_["i"] == i), True)
            if mx > KC["voda"].get("brod_sklon_max" if voz_ else "brod_sklon_max_pesi", 0.3): spatne_br.append("%s (%.0f, %.0f) %.0f %%" % (t.get("jmeno") or k, o[i, 0], o[i, 1], mx * 100))
TEST("brod_najezd", not spatne_br, "%d brodů; strmé: %s" % (sum(len(t.get("brody", [])) for t in TH.values()), spatne_br[:6]))
# hladina bez hrany (Míša 13. 11., misa_13_11_voda_deska.jpg: „deska s ostrou hranou“): v hra/modely/voda.glb každá hrana na
# okraji sítě hladiny podél toku má aspoň jeden vrchol s krytím 0 (barva vrcholu A) a vrchol s krytím > 0 má hloubku > 0
# (UV v = 1 − hloubka – glTF převrací v, dřív shader četl v přímo a krytí bylo všude 0,55)
def _glb_voda(f):
    import struct
    b = open(f, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n]); b0 = 20 + n + 8
    TY = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}; CN = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    def acc(i):
        a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]; dt = TY[a["componentType"]]; k = CN[a["type"]]
        o = b0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        x = np.frombuffer(b[o:o + a["count"] * k * np.dtype(dt).itemsize], dt).reshape(-1, k).astype(np.float64)
        return x / np.iinfo(dt).max if a.get("normalized") else x
    for m in j["meshes"]:
        if not m["name"].startswith("VODA_") or m["name"].startswith("VODA_DALEKO"): continue
        pr = m["primitives"][0]; at = pr["attributes"]
        yield acc(at["POSITION"]), (acc(at["COLOR_0"]) if "COLOR_0" in at else None), acc(at["TEXCOORD_0"]), acc(pr["indices"]).astype(int).ravel()
_tvrde = 0; _bez_barvy = 0; _mel = 0; _kusu = 0
_OSA_ = np.vstack([np.array(t["osa"])[:, :2] for t in TH.values()]); _TG_ = np.vstack([np.gradient(np.array(t["osa"])[:, :2], axis=0) for t in TH.values()])
_TG_ /= np.linalg.norm(_TG_, axis=1, keepdims=True) + 1e-9; _KO_ = cKDTree(_OSA_)
_KE_ = cKDTree(np.array([np.array(t["osa"])[e, :2] for t in TH.values() for e in (0, -1)]))
if os.path.exists(K + "/hra/modely/voda.glb"):
    for P_, C_, U_, I_ in _glb_voda(K + "/hra/modely/voda.glb"):
        _kusu += 1
        if C_ is None: _bez_barvy += 1; continue
        a_ = C_[:, 3]; h_ = 1.0 - U_[:, 1]
        _mel += int(((a_ > 0.01) & (h_ <= 0.0)).sum())
        T_ = I_.reshape(-1, 3); E_ = np.sort(np.r_[T_[:, [0, 1]], T_[:, [1, 2]], T_[:, [2, 0]]], axis=1)
        u_, c_ = np.unique(E_, axis=0, return_counts=True); ok_ = u_[c_ == 1]   # okrajové hrany sítě
        d_ = P_[ok_[:, 1]][:, [0, 2]] - P_[ok_[:, 0]][:, [0, 2]]; d_ /= np.linalg.norm(d_, axis=1, keepdims=True) + 1e-9
        tg_ = _TG_[_KO_.query((P_[ok_[:, 0]][:, [0, 2]] + P_[ok_[:, 1]][:, [0, 2]]) / 2)[1]]
        podel_ = np.abs((d_ * tg_).sum(1)) > 0.5   # hrana podél toku = kraj vody (napříč = šev mezi kusy po kus_m)
        podel_ &= _KE_.query((P_[ok_[:, 0]][:, [0, 2]] + P_[ok_[:, 1]][:, [0, 2]]) / 2)[0] > KC["voda"]["soutok_m"]   # konec toku (soutok, kraj výseku): přítok končí ve vodě hlavního toku
        _tvrde += int((podel_ & (a_[ok_[:, 0]] > 0.01) & (a_[ok_[:, 1]] > 0.01)).sum())
TEST("voda_bez_hrany", _kusu > 0 and _tvrde == 0 and _bez_barvy == 0 and _mel == 0,
     "kusů hladiny %d, bez barvy vrcholu %d, tvrdých hran na kraji %d, krytí bez vody %d" % (_kusu, _bez_barvy, _tvrde, _mel))
# porost až k vodě (Míša 13. 11.: „hlavně ty břehy a přechod vody a hlíny plus vegetace“; misa_real_01/04): břeh u vody není
# třída cesta (mimo brody) a pás trsů na čáře vody (byliny.json voda_pas, pata_pas.json skvrny voda_*) kryje dost délky
_bc = []; _bd = 0
for k, t in TH.items():
    o = np.array(t["osa"]); d = np.gradient(o[:, :2], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.c_[-d[:, 1], d[:, 0]]
    bv_ = np.array(t.get("brod_vaha", [0.0] * len(o))); m_ = bv_ == 0
    for sg in (1, -1):
        q_ = o[:, :2] + sg * n * (t["sirka"] / 2 + 1.0)
        _bc.append(np.array(TR)[trida(q_[m_, 0], q_[m_, 1])] == "cesta"); _bd += float(m_.sum())
_bc = float(np.concatenate(_bc).mean()) if _bc else 1.0
_PP = json.load(open(D + "pata_pas.json"))["bunky"] if os.path.exists(D + "pata_pas.json") else {}
_vd = sum(math.hypot(sk[2] - sk[0], sk[3] - sk[1]) for v in _PP.values() for sk in v if str(sk[7]).startswith("voda"))
TEST("breh_porost", _bc <= KC["voda"]["breh_cesta_max"] and _vd >= KC["voda"]["voda_pas_pokryti_min"] * _bd,
     "břeh u vody třídy cesta %.1f %% (mez %.0f %%), pás na čáře vody %.0f m z %.0f m čáry (mez %.0f %%)" % (_bc * 100, KC["voda"]["breh_cesta_max"] * 100, _vd, _bd, KC["voda"]["voda_pas_pokryti_min"] * 100))
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
    _fine = np.linalg.norm(T_[:, 1] - T_[:, 0], axis=1) < 0.5   # trojúhelníky jemné sítě otvoru (0,25 m)
    for w in ([1/3, 1/3, 1/3], [.5, .5, 0], [0, .5, .5], [.5, 0, .5]):
        q = np.einsum("j,ijk->ik", np.array(w, np.float32), T_); d = q[:, 1] - ter(q[:, 0], q[:, 2]); vz += len(q)
        jemne = _JM[np.clip(np.round(q[:, 2] - VY["z0_hra"]).astype(int), 0, _JM.shape[0] - 1), np.clip(np.round(q[:, 0] - VY["x0_hra"]).astype(int), 0, _JM.shape[1] - 1)]
        kryto = _KR[np.clip(np.round(q[:, 2] - VY["z0_hra"]).astype(int), 0, _KR.shape[0] - 1), np.clip(np.round(q[:, 0] - VY["x0_hra"]).astype(int), 0, _KR.shape[1] - 1)]
        # jemná síť 0,25 m kolem otvoru (zemljanka, štola – teren_dlazdice.py dira) leží v rovinách sítě 2 m; kolize (r16, 1 m) se mezi
        # uzly interpoluje bilineárně a na úhlopříčce sítě 2 m se od roviny odchýlí – vzorky jemných trojúhelníků to zachytí ve strmém
        # svahu (16. 11.: otvor zemljanky u lomu přes celý půdorys pod střechou sahá k hraně zářezu, −0,12 m); tolerance jemne_m
        tol_ = np.where(_fine, max(TK["tolerance_m"], TK.get("jemna_sit_tolerance_m", 0.15)), TK["tolerance_m"])
        a = (d > tol_) & ~kryto; c = (d < -tol_) & ~jemne
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

# zajímavá místa mimo cesty (Míša 16. 11. ke snímku mista_mlyn_kolo: „kde jsi dal ten mlýn? není v cestě?“ – mlýn stál na údolní
# cestě): zábor každého dílu (obdélník půdorysu z nastroje/zajimava_mista.py) nezasahuje do pásu cesty (osa ± sirka_m / 2)
# žádné cesty kromě pěšiny k témuž místu (k_<id>); pěšiny k místům začínají na cestě a končí v bodě přístupu místa
_CZ = json.load(open(K + "/pravidla/svet/cesty_puchart.json")); _ZM = json.load(open(D + "zajimava_mista.json")); _c30 = []; _c31 = []
def _hu(o, k=0.5):
    o = np.asarray(o, float)[:, :2]; d_ = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]; s_ = np.arange(0, d_[-1] + 1e-6, k)
    return np.c_[np.interp(s_, d_, o[:, 0]), np.interp(s_, d_, o[:, 1])]
from scipy.spatial import cKDTree as _KDT
_pasy = [(c["id"], c.get("k_mistu"), float(_CZ["typy"][c["typ"]]["sirka_m"]) / 2, _KDT(_hu(c["osa"]))) for c in _CZ["cesty"] if c.get("osa") and not c.get("jen_maska")]
_ndil = 0
for _m in _ZM["mista"]:
    for _q in _m["dily"]:
        for _zb in _q.get("zabor", []):
            _ndil += 1; _b = _hu(_zb + _zb[:1], 0.25)
            _b = np.vstack([_b, (np.array(_zb).mean(0))[None]])
            for _cid, _km, _pul, _kd in _pasy:
                if _km == _m["id"]: continue
                _d = float(_kd.query(_b)[0].min())
                if _d < _pul: _c30.append("%s %s do cesty %s (%.1f m od osy, pás %.1f m)" % (_m["id"], _q.get("model", _q.get("predmet", _q.get("balvan", _q.get("strom", "?")))), _cid, _d, _pul)); break
TEST("zajimava_mimo_cest", _ndil > 0 and not _c30, "; ".join(_c30[:8]) if _c30 else "%d záborů dílů míst mimo pás cest" % _ndil)
_kd_cest = _KDT(np.vstack([_hu(c["osa"]) for c in _CZ["cesty"] if c.get("osa") and not c.get("k_mistu") and not c.get("jen_maska")]))
for _m in _ZM["mista"]:
    if not _m.get("pristup"): continue
    _kc = [c for c in _CZ["cesty"] if c.get("k_mistu") == _m["id"]]
    if not _kc: _c31.append("%s: chybí pěšina k_%s (nastroje/pesiny_k_mistum.py)" % (_m["id"], _m["id"])); continue
    _o = np.array(_kc[0]["osa"], float)[:, :2]
    _d0 = float(_kd_cest.query(_o[0])[0]); _d1 = float(np.hypot(*(_o[-1] - np.array(_m["pristup"]["bod"]))))
    _ho = _hu(_o, 1.0); _ho = _ho[np.hypot(*(_ho - _o[-1]).T) > 2.5]   # poslední 2,5 m u místa (pata stavby, dvůr) se nepočítají
    _tr = trida(_ho[:, 0], _ho[:, 1]) if len(_ho) else np.array([TR.index("cesta")]); _ces = float(np.mean([TR[int(t_)].startswith(("cesta", "pesina")) for t_ in _tr]))
    if _d0 > 1.5 or _d1 > 3.0 or _ces < 0.8: _c31.append("%s: pěšina začíná %.1f m od cesty, končí %.1f m od přístupu, vyšlapaná (třída cesta) %.0f %%" % (_m["id"], _d0, _d1, _ces * 100))
TEST("zajimava_pesiny", not _c31, "; ".join(_c31) if _c31 else "pěšiny k místům (k_studanka, k_mlyn) vedou od cesty k přístupu, vyšlapané")
odl = [m["id"] for m in json.load(open(K + "/pravidla/svet/zajimava_mista.json"))["mista"] if m.get("odlozeno")]
TEST("zajimava_odlozena", not [m for m in _ZM["mista"] if m["id"] in odl] and set(odl) <= set(_ZM.get("odlozena", [])), "odložená místa (%s) nejsou ve světě" % ", ".join(odl))

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
    _pas = (_d > 0) & (_d <= 4.0) & ~np.isin(ST, [_T.index(t) for t in ("stavba", "nadvori", "predhradi", "nadvori_slap", "pata_zdi_uvnitr", "cesta", "koryto_kamenite", "breh", "skala", "ves_slap") if t in _T])   # ves_slap: vyšlapáno ve vsi, ne pata hradní zdi
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
# P2 výkon (17. 11., vykon_z_havrana_15_11.md): vrstvy po buňkách berou MultiMesh ze zásoby (zasoba_mm.gd), ne MultiMesh.new() při přestavbě
_RZ = json.load(open(D + "rozpocty.json")).get("zasoba_mm", {}); _tk = _RZ.get("tridy_kapacity", [])
_mmnew = [f for f in ("louka.gd", "byliny.gd", "bunky_kolem.gd") if re.search(r"^\s*func (_vloz|mmi)[\s\S]*?MultiMesh\.new\(", open(K + "/hra/scripts/" + f).read(), re.M) and "ZasobaMM.vezmi" not in open(K + "/hra/scripts/" + f).read()]
TEST("zasoba_multimeshu", bool(_RZ.get("zapnuto")) and _tk == sorted(_tk) and len(_tk) > 0 and int(_RZ.get("stari_snimku", 0)) >= 2 and not _mmnew and _RZ.get("zdroj"),
     "rozpocty.json zasoba_mm zapnuto %s, třídy %s, stáří %s snímků; vrstvy s MultiMesh.new při přestavbě: %s" % (_RZ.get("zapnuto"), _tk, _RZ.get("stari_snimku"), _mmnew))
# časované prolnutí LOD stromů (video Míši 16. 11., Havran K13): data, shadery s kamera_pred, ≤ 13 vzorkovačů (Adreno), bez kopie obrazovky
_LC = SM.get("lod_casove", {}); _shz = []
for _f in ("listi", "kura", "impostor"):
    _t = open(K + "/hra/shaders/%s.gdshader" % _f).read()
    if "lod_casove" not in _t or "kamera_pred" not in _t or len(re.findall(r"uniform\s+sampler2D", _t)) > 13 or re.search(r"screen_texture|hint_screen_texture|SCREEN_TEXTURE", _t): _shz.append(_f)
TEST("lod_casove_prolnuti", 0.05 <= float(_LC.get("cas_s", 0)) <= 1.0 and float(_LC.get("skok_m", 0)) > 2.0 and not _shz and _LC.get("zdroj") and "_kamera_pred" in open(K + "/hra/scripts/les.gd").read(),
     "stromy_modely.json lod_casove %s s; shadery bez časovaného prolnutí / nad 13 vzorkovačů / kopie obrazovky: %s" % (_LC.get("cas_s"), _shz))
# shluky keřů a bylin: šum s vlnou ~vlna_m (17. 11.: frekvence 0,01 dávala vlnu 4,8 km – shluky nefungovaly)
TEST("shluky_vlna", all(float(x.get("shluky_frekvence", 0)) == 1.0 for x in (BY, KE)) and re.search(r"_sum\.frequency\s*=", open(K + "/hra/scripts/byliny.gd").read()) is not None,
     "byliny/kere shluky_frekvence %s / %s" % (BY.get("shluky_frekvence"), KE.get("shluky_frekvence")))
# houštiny podle Havrana (les_podrost.json houstina, Míša 16. 11.): plášť lesa souvislý a hustý, břeh v pásech s mezerami, paseka zarůstá
_ok_pl = sum(KE["tridy"].get("les_okraj", {}).values()); _sht = KE.get("shluky_tridy", {})
_pas_z = sum(v for k_, v in KE["tridy"].get("les_paseka", {}).items() if k_.startswith("zmlazeni"))
TEST("houstiny_plast", _ok_pl >= 0.1 and float(_sht.get("les_okraj", {}).get("min", 0)) >= 0.5 and float(_sht.get("breh", {}).get("prah", 0)) > 0.2 and _pas_z >= 0.02 and _sht.get("zdroj") and
     float(BY["tridy"].get("les_okraj", {}).get("kapradi", 0)) >= 0.1,
     "plášť les_okraj %.3f/m² (≥ 0,1), shluky plášť min %s, břeh práh %s, zmlazení paseky %.3f, kapradí lemu %s" % (_ok_pl, _sht.get("les_okraj", {}).get("min"), _sht.get("breh", {}).get("prah"), _pas_z, BY["tridy"].get("les_okraj", {}).get("kapradi")))
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
_zjz = np.load(K + "/build/teren_jemne.npz")   # snížená kolize pod jámou zemljanky a chodbou štoly (nastroje/zajimava_mista.py) není skok terénu
from scipy.ndimage import binary_dilation as _bdz
_ZJ = _bdz(np.unpackbits(_zjz["zajimava"])[:Yt.size].reshape(Yt.shape).astype(bool), iterations=1) if "zajimava" in _zjz.files else np.zeros(Yt.shape, bool)
dz = max(float(np.abs(np.diff(Yt, axis=0))[~(_ZJ[1:] | _ZJ[:-1])].max()), float(np.abs(np.diff(Yt, axis=1))[~(_ZJ[:, 1:] | _ZJ[:, :-1])].max()))
TEST("teren_skoky", dz < KC["teren"]["skok_max_m"], "největší skok mezi sousedními metry %.1f m (skalní stěny ≤ %s)" % (dz, KC["teren"]["skok_max_m"]))
DL = json.load(open(K + "/hra/dlazdice/dlazdice.json"))
TEST("dlazdice", len(DL["dlazdice"]) == DL["pocet"][0] * DL["pocet"][1] and all(os.path.exists(K + "/hra/dlazdice/" + os.path.basename(str(d.get("soubor", d) if isinstance(d, dict) else d))) for d in DL["dlazdice"]),   # dřív „or True“ (audit 15. 11.)
     "%d dlaždic, LOD %s" % (len(DL["dlazdice"]), DL["lod"]))
CP = json.load(open(K + "/pravidla/svet/cesty_puchart.json")); CP_TYP = {c_["id"]: c_["typ"] for c_ in CP["cesty"] if not c_.get("jen_maska")}   # brod: terén (koryto) beze změny
mez = KC["cesty"]["rez_max_m"]
zle = {k: v for k, v in CP["vysledek"].items() if max(v["max_rez_m"], v["max_nasyp_m"]) > mez}
TEST("cesta_zarez", not zle, "zářez/násyp nad %s m: %s" % (mez, zle))
pr_mez = KC["cesty"].get("pricny_max", 0.08)   # vůz se nepřevrátí (Míša 6. 11.: hrb na straně cesty)
zle_p = {k: v.get("max_pricny") for k, v in CP["vysledek"].items() if CP_TYP.get(k) in ("vozova", "hrebenova")
         and v.get("max_pricny", 0) > (KC["cesty"].get("pricny_max_hrebenova", pr_mez) if CP_TYP.get(k) == "hrebenova" else pr_mez)}
TEST("cesta_pricny_sklon", not zle_p, "příčný sklon jízdního pásu nad %s: %s" % (pr_mez, zle_p))
# Míša 11. 11.: cesty podle terénu („nevykopat půl kopce“) – změna terénu cestou nejvýš podle typu (cesty_puchart.json typy
# max_uprava_m podélně / max_uprava_napric_m napříč), mimo doložené nájezdy k mostům
zle_u = {k: v.get("max_uprava_m") for k, v in CP["vysledek"].items() if k in CP_TYP and v.get("podle_terenu", True)
         and v.get("max_uprava_m", 99) > max(CP["typy"][CP_TYP[k]].get("max_uprava_m", 0.5), CP["typy"][CP_TYP[k]].get("max_uprava_napric_m", 0.5)) + 0.05}
TEST("cesta_uprava_terenu", not zle_u, "cesta mění terén víc, než dovoluje její typ: %s" % zle_u)
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
# Míša 13. 11. („není tam těch klád zase moc? a mají to být popadané stromy, ne pokácené“): břeh ≤ kmen_breh_max, kmen = padlé stromy, ležící jen mimo louku/ves
_kb = BY["tridy"].get("breh", {}).get("kmen", 0); _lz = BY.get("lezi", {}).get("kmen", {})
TEST("padle_stromy", _kb <= KC["vegetace"].get("kmen_breh_max", 0) and all(m_.startswith("padly_strom") for m_ in BY["modely"]["kmen"]) and "louka_kosena" in _lz.get("zakazane_tridy", []) and "cesta" in _lz.get("zakazane_tridy", []) and "breh" in _lz.get("les_okoli", {}),
     "břeh kmen %.4f/m² (max %s), modely %s, ležení %s" % (_kb, KC["vegetace"].get("kmen_breh_max"), BY["modely"]["kmen"], sorted(_lz)))
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
_vyj = [e for e in KC.get("schody", {}).get("vyjimky", []) if e.get("do", "9999") >= _dnes]   # prošlé výjimky neplatí (audit 15. 11.)
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
import glob as _gl, re
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
            if "material" not in p: continue   # kolizní proxy bez materiálu (-convcolonly sedátek oken, 15. 11.) – není viditelná síť
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
# střecha souměrná (Míša 13. 11.: „spodní budova spodního hradu nemá stejnou střechu na obě strany“): stejný přesah i výška
# okapu na obou stranách, kromě strany, která končí na koruně vyšší hradby
_ns = []
if os.path.exists(D + "strechy.json"):
    for st_ in json.load(open(D + "strechy.json"))["strechy"]:
        if any(st_["v_hradbe"]): continue
        if abs(st_["presah"][0] - st_["presah"][1]) > 0.05 or abs(st_["okap_y"][0] - st_["okap_y"][1]) > 0.05: _ns.append(st_["stred"])
TEST("strecha_soumerna", os.path.exists(D + "strechy.json") and not _ns, "nesouměrné střechy: %s" % _ns[:5])
# plošiny hradů po vyhlazení terénu rovné (Míša 13. 11.: hlína pod prahem věžičky A – malá plošina se rozmazala): vnitřek
# plošiny (1 m od kraje) ve výšce y ± plosina_tol_m
from matplotlib.path import Path as _Path
_pz = []
for q_ in json.load(open(K + "/pravidla/svet/hrad_puchart.json"))["teren"]["plosiny"]:
    if "polygon" not in q_ or q_.get("y") is None or not q_.get("kontrola_rovna"): continue   # nádvoří B mají rampy za branami
    pg_ = np.array(q_["polygon"], float); x0_, z0_ = pg_.min(0) + 1.0; x1_, z1_ = pg_.max(0) - 1.0
    body_ = q_.get("kontrola_body") or [(xx_, zz_) for xx_ in np.linspace(x0_, x1_, 5) for zz_ in np.linspace(z0_, z1_, 5) if _Path(pg_).contains_point((xx_, zz_))]
    for xx_, zz_ in body_:
        dy_ = float(ter(xx_, zz_)) - q_["y"]
        if abs(dy_) > KC.get("plosina_tol_m", 0.12): _pz.append("%s (%.1f, %.1f) %+.2f m" % (q_["id"], xx_, zz_, dy_))
TEST("plosiny_rovne", not _pz, "nerovné plošiny: %s" % _pz[:5])
# vstupy domů (Míša 13. 11.: „do hájovny nemůžu vstoupit, všechny budovy musí být vstupné“): terén před dveřmi ve výšce
# domu (stupeň 0,15 m a podlaha 0,3 m nad základem modelu – víc postava nevyleze)
_vd = []
for v_ in json.load(open(D + "mista_stavby.json")).get("vstupy_domu", []):
    for q_ in v_["body"]:
        dy_ = float(ter(q_[0], q_[1])) - v_["y"]
        if abs(dy_) > KC.get("vstup_domu_tol_m", 0.12): _vd.append("%s %s (%.1f, %.1f) %+.2f m" % (v_["misto"], v_["stavba"], q_[0], q_[1], dy_))
TEST("vstup_domu_teren", not _vd, "terén před vstupy mimo výšku domu: %s" % _vd[:6])
# padací most zakryje otvor brány (Míša 13. 11.: zvednutý most užší a nižší než oblouk, kolem nebe)
_mk = json.load(open(D + "mosty_kryti.json"))["mosty"] if os.path.exists(D + "mosty_kryti.json") else []
_mk_zle = [m_ for m_ in _mk if m_["most"][0] < m_["otvor"][0] + 0.2 or m_["most"][1] < m_["otvor"][1] + 0.03]   # nahoře brána B pod korunou: přesah 3 cm (výklenek nejvýš 0,15 m pod korunou)
TEST("most_kryje_otvor", bool(_mk) and not _mk_zle, "%d výpočtů mostů; nekryje: %s" % (len(_mk), _mk_zle[:3]))
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
# zábradlí jako celek (Míša 10. 11.: „zábradlí řešíme už tolikrát – navrhni, ať se to neopakuje“): na OBOU hradech každý konec
# zábradlí buď sdílí sloupek s jiným (spojeno), nebo je od nejbližšího jiného konce/zábradlí dál než 1,0 m (volný konec u zdi či
# schodů); dva rovnoběžné kusy v jedné výšce se nesmí překrývat (zdvojené zábradlí). build/zabradli.json ze stavitele hradu.
_ZB = json.load(open(K + "/build/zabradli.json"))["zabradli"] if os.path.exists(K + "/build/zabradli.json") else []
_zv = []
_TRZ = list(json.load(open(D + "pruchody.json")).get("trasy", json.load(open(D + "pruchody.json"))).values()) if os.path.exists(D + "pruchody.json") else []
_TRZ = [t_ for t_ in _TRZ if isinstance(t_, list)]
def _bod_usecka(q, a, b):
    a, b, q = np.array(a, float), np.array(b, float), np.array(q, float); d = b[:2] - a[:2]; L = np.linalg.norm(d)
    t = 0.0 if L < 1e-6 else max(0.0, min(1.0, float((q[:2] - a[:2]) @ d) / L ** 2)); p = a + (b - a) * t
    return float(np.linalg.norm(p[:2] - q[:2])), float(abs(p[2] - q[2]))
for i, z in enumerate(_ZB):
    for k in ("a", "b"):
        if z["s" + k]: continue
        for j, o in enumerate(_ZB):
            if i == j: continue
            dh, dv = _bod_usecka(z[k], o["a"], o["b"])
            if 0.02 < dh < 1.0 and dv < 0.3:   # mezera 0,6–1,0 m je v pořádku jen jako průchod (vede jí trasa průchodu – výstup schodů)
                if dh >= 0.6 and any(_bod_usecka(z[k], [p_[0], p_[1], 0], [q_[0], q_[1], 0])[0] < dh + 0.3 for t_ in _TRZ for p_, q_ in zip(t_, t_[1:])): continue
                _zv.append({"konec": z[k], "u": [o["a"], o["b"]], "m": round(dh, 2)}); break
for i, z in enumerate(_ZB):   # zdvojené: rovnoběžné, do 0,2 m od sebe, stejná výška, překryv > 0,3 m
    a, b = np.array(z["a"]), np.array(z["b"]); d = (b - a)[:2]; L = np.linalg.norm(d)
    if L < 0.3 or abs(a[2] - b[2]) > 0.05: continue
    for o in _ZB[i + 1:]:
        c, e = np.array(o["a"]), np.array(o["b"]); d2 = (e - c)[:2]; L2 = np.linalg.norm(d2)
        if L2 < 0.3 or abs(c[2] - e[2]) > 0.05 or abs(c[2] - a[2]) > 0.25 or abs(float(d @ d2) / L / L2) < 0.98: continue
        if _bod_usecka(c, a, b)[0] > 0.2 and _bod_usecka(e, a, b)[0] > 0.2: continue
        u = sorted([float((c[:2] - a[:2]) @ d) / L, float((e[:2] - a[:2]) @ d) / L]); prekryv = min(L, u[1]) - max(0.0, u[0])
        if prekryv > 0.3: _zv.append({"zdvojene": [z["a"], z["b"]], "s": [o["a"], o["b"]]})
_ul = [z for z in _ZB if np.linalg.norm(np.array(z["b"][:2]) - np.array(z["a"][:2])) < 0.9 and not z["sa"] and not z["sb"]]   # Míša 12. 11.: úlomky u branky A
TEST("zabradli_ulomky", not _ul, "samostatné kusy zábradlí kratší než 0,9 m: %d %s" % (len(_ul), _ul[:3]))
TEST("zabradli_spojite", len(_ZB) > 20 and not _zv, "zábradlí %d kusů, nenavazujících/zdvojených %d %s" % (len(_ZB), len(_zv), _zv[:3]))
TEST("portaly", len(POR_) >= KC.get("portaly_min", 8), "portálů z portaly.py: %d" % len(POR_))

# --- cesty bez porostu (Míša 12. 11. večer: „cesty jsou na hodně místech zarostlé travou a keři, hlavně u hospody a od hradu
# k vesnici“ – stanoviste_realne.py v postav_vse.sh přepsal třídu cesta): na celé šíři každé cesty (osy cesty_puchart.json,
# šířka podle typu) nesmí být třída s trávou (louka.json), bylinami (byliny.json) ani keři (kere.json), ani strom lesa.
# Mimo: obrys stavby (brána) a 28 m od konce mostu (cesty.py tam osu stáčí rovně do osy mostu – ROVNE_M/OBLOUK_M).
LO_ = json.load(open(D + "louka.json"))["tridy"]
def _roste(t): return float(LO_.get(t, 0.0)) > 0 or any(float(v) > 0 for v in BY["tridy"].get(t, {}).values() if not isinstance(v, str)) or bool(KE["tridy"].get(t))
# zemljanky bez trávy (Míša 16. 11. ke snímku luzka_barvy_zemljanka_svetlo.jpg: „neleze ti tráva do té zemljanky?“): půdorys pod
# střechou (zajimava_modely.json pod_strechou) celý v otvoru terénu (build/zajimava_teren.json diry) a bez porostu (stanoviště)
_zmo = json.load(open(D + "zajimava_modely.json"))["modely"]; _zt = json.load(open(K + "/build/zajimava_teren.json")) if os.path.exists(K + "/build/zajimava_teren.json") else {"diry": []}
def _v_poly(x, z, P):
    c = False
    for i_ in range(len(P)):
        (x1, z1), (x2, z2) = P[i_], P[(i_ + 1) % len(P)]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1: c = not c
    return c
_c32 = []; _nz = 0
for _m in json.load(open(D + "zajimava_mista.json"))["mista"]:
    for _q in _m["dily"]:
        if not _q.get("zemljanka"): continue
        _nz += 1; _ps = _zmo[_q["model"]].get("pod_strechou")
        if not _ps: _c32.append("%s: model bez pod_strechou" % _q["model"]); continue
        _cs, _sn = math.cos(_q["yaw"]), math.sin(_q["yaw"]); _od = 0.2
        _body = [(_q["x"] + a * _cs + b * _sn, _q["z"] - a * _sn + b * _cs) for a in np.linspace(_ps[0] + _od, _ps[1] - _od, 9) for b in np.linspace(_ps[2] + _od, _ps[3] - _od, 11)]
        _mimo = sum(1 for x_, z_ in _body if not any(_v_poly(x_, z_, d_["poly"]) for d_ in _zt["diry"]))
        _rost = sum(1 for x_, z_ in _body if _roste(TR[int(trida(x_, z_))]))
        if _mimo or _rost: _c32.append("%s %s: bodů pod střechou mimo otvor terénu %d, s porostem %d z %d" % (_m["id"], _q["model"], _mimo, _rost, len(_body)))
TEST("zemljanka_bez_travy", _nz > 0 and not _c32, "; ".join(_c32) if _c32 else "%d zemljanek: půdorys pod střechou v otvoru terénu, bez porostu" % _nz)
# mlýn: koryto Veličky u mlýna zůstane korytem (voda, ne porost) a pod kolem nic neroste (Míša 16. 11.: „kolo stojí v trávě“)
# kameny v korytě (byliny.json koryto_kamenite: kamen) nejsou porost – dno řeky pod kolem je kamenité
def _roste_rostliny(t): return float(LO_.get(t, 0.0)) > 0 or any(float(v) > 0 for k_, v in BY["tridy"].get(t, {}).items() if not isinstance(v, str) and k_ != "kamen") or bool(KE["tridy"].get(t))
_c33 = []; _zmj = json.load(open(K + "/pravidla/svet/zajimava_mista.json"))
for _m in json.load(open(D + "zajimava_mista.json"))["mista"]:
    if _m["id"] != "mlyn": continue
    _ml = [q for q in _zmj["mista"] if q["id"] == "mlyn"][0]["mlyn"]; _cs, _sn = math.cos(_m["yaw"]), math.sin(_m["yaw"])
    _sv = lambda a, b: (_m["x"] + a * _cs + b * _sn, _m["z"] - a * _sn + b * _cs)
    _r = _ml["bez_porostu_kolo"]; _rost = [p_ for p_ in (_sv(a, b) for a in np.linspace(_r[0] + .2, _r[1] - .2, 6) for b in np.linspace(_r[2] + .2, _r[3] - .2, 8)) if _roste_rostliny(TR[int(trida(*p_))])]
    if _rost: _c33.append("pod kolem roste porost v %d bodech, např. [%.1f, %.1f] %s" % (len(_rost), _rost[0][0], _rost[0][1], TR[int(trida(*_rost[0]))]))
    _vel = [t for t in json.load(open(D + "toky_hladina.json"))["toky"].values() if t.get("jmeno") == "Velička"][0]; _o = np.array(_vel["osa"])
    _bl = _o[np.hypot(_o[:, 0] - _m["x"], _o[:, 1] - _m["z"]) < 12]
    _jine = [(round(float(p_[0]), 1), round(float(p_[1]), 1), TR[int(trida(p_[0], p_[1]))]) for p_ in _bl if TR[int(trida(p_[0], p_[1]))] != "koryto_kamenite"]
    if not len(_bl): _c33.append("Velička není do 12 m od mlýna")
    if _jine: _c33.append("osa Veličky u mlýna mimo třídu koryta: %s" % _jine[:3])
TEST("mlyn_koryto", not _c33, "; ".join(_c33) if _c33 else "koryto Veličky u mlýna je koryto, pod kolem bez porostu")
_ROSTE = np.array([_roste(t) for t in TR])
_CP = json.load(open(K + "/pravidla/svet/cesty_puchart.json")); _MO = np.array([m_["u_bodu"][:2] for m_ in json.load(open(K + "/pravidla/svet/voda_hra.json")).get("mosty", [])] or [[1e9, 1e9]])
def _chaikin(p_, n=3):
    for _ in range(n):
        q_ = [p_[0]]
        for a_, b_ in zip(p_[:-1], p_[1:]): q_ += [0.75 * a_ + 0.25 * b_, 0.25 * a_ + 0.75 * b_]
        q_.append(p_[-1]); p_ = np.array(q_)
    return p_
_zar = {}; _vz = 0; _osy_body = []
for c_ in _CP["cesty"]:
    hw_ = _CP["typy"][c_["typ"]]["sirka_m"] / 2; o_ = _chaikin(np.array(c_["osa"], float)[:, :2])
    d_ = np.r_[0, np.cumsum(np.hypot(*np.diff(o_, axis=0).T))]; s_ = np.arange(0, d_[-1], 0.5)
    px_ = np.interp(s_, d_, o_[:, 0]); pz_ = np.interp(s_, d_, o_[:, 1]); tx_ = np.gradient(px_); tz_ = np.gradient(pz_); ln_ = np.hypot(tx_, tz_) + 1e-9
    _osy_body.append(np.c_[px_, pz_, np.full(len(px_), hw_)])
    for f_ in np.linspace(-hw_, hw_, 5):
        X_ = px_ - tz_ / ln_ * f_; Z_ = pz_ + tx_ / ln_ * f_
        ok_ = (np.hypot(X_[:, None] - _MO[None, :, 0], Z_[:, None] - _MO[None, :, 1]).min(1) > 28.0)
        ok_ &= (X_ > SJ["x0_hra"]) & (Z_ > SJ["z0_hra"]) & (X_ < SJ["x0_hra"] + ST.shape[1] * SJ["krok_m"]) & (Z_ < SJ["z0_hra"] + ST.shape[0] * SJ["krok_m"])
        t_ = trida(X_[ok_], Z_[ok_]); _vz += int(ok_.sum())
        zl_ = _ROSTE[t_]
        if zl_.any(): _zar[c_["id"]] = _zar.get(c_["id"], 0) + int(zl_.sum())
TEST("cesta_bez_porostu", not _zar, "vzorků pásu cest %d, se zarostlou třídou %d: %s" % (_vz, sum(_zar.values()), dict(sorted(_zar.items(), key=lambda a: -a[1])[:6])))
from scipy.spatial import cKDTree as _KDT
_ob = np.vstack(_osy_body); _dd, _ii = _KDT(_ob[:, :2]).query(np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5)[:, :2])
_sc = int(((_dd < _ob[_ii, 2] + 0.5) & (np.hypot(*(np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5)[:, None, :2] - _MO[None]).transpose(2, 0, 1)).min(1) > 28.0)).sum())
TEST("strom_mimo_pas_cesty", _sc == 0, "stromů lesa na šířce cesty (osa ± půl šířky + 0,5 m): %d" % _sc)

# --- ves (Míša 12. 11. večer): vyšlapáno, kde se chodí; volné vstupy; krčma bez plotů; žádné vybavení
if os.path.exists(D + "mista_stavby.json"):
    from shapely.geometry import Polygon as _Pg, Point as _Pt, LineString as _Ls
    MS = json.load(open(D + "mista_stavby.json")); MIJ = json.load(open(K + "/pravidla/svet/mista.json"))
    _holy = lambda x_, z_: not _ROSTE[trida(np.array([x_]), np.array([z_]))[0]]
    # vyšlapáno: dvůr, plocha před každým vstupem, vrata a branky (1 m ven), studna, osa ulice – třída bez porostu
    _body = [("dvur", *_Pg(q).centroid.coords[0]) for q in MS.get("dvory", [])] + [("pred_vstupem", *_Pg(v["pred"]).centroid.coords[0]) for v in MS.get("vstupy", [])]
    _uz = {u["i"]: u for u in MS["usedlosti"]}
    for b in MS["brany"]:
        a_ = (np.array(b["a"])[[0, 2]] + np.array(b["b"])[[0, 2]]) / 2; d_ = np.array(b["b"])[[0, 2]] - np.array(b["a"])[[0, 2]]; n_ = np.array([-d_[1], d_[0]]) / (np.linalg.norm(d_) + 1e-9)
        _body += [("brana", *(a_ + n_ * 1.0)), ("brana", *(a_ - n_ * 1.0))]
    _body += [("studna", s_["x"] + 2.0, s_["z"]) for s_ in MS.get("studny", [])]
    _body += [("ulice", *q) for c_ in MS.get("vyslapano", {}).get("cary", []) if c_["druh"] == "ulice" for q in c_["body"]]
    _zle = [(k, round(x_), round(z_), TR[trida(np.array([x_]), np.array([z_]))[0]]) for k, x_, z_ in _body if not _holy(x_, z_)]
    TEST("ves_vyslapano", len(_body) > 50 and not _zle, "míst, kudy se ve vsi chodí: %d, zarostlých %d %s" % (len(_body), len(_zle), _zle[:5]))
    # volné vstupy: před dveřmi domů a vraty stodol/kůlen (pruh mista.json usedlosti.vstupy.pred_m) žádná stavba, plot, strom
    # ani předmět; každý dům má tolik vstupů, kolik má model vnějších dveří (uzly *_Dvere_* v domy.glb)
    _pud = [_Pg(q) for q in MS["pudorysy"]]; _zv = []
    for v in MS.get("vstupy", []):
        pr_ = _Pg(v["pred"]); vnitr_ = _Pt(v["c"][0] - v["n"][0] * 0.6, v["c"][1] - v["n"][1] * 0.6)
        for q in _pud:
            if not q.contains(vnitr_) and q.intersects(pr_): _zv.append((v["stavba"], v["c"], "stavba"))
        for p_ in MS["ploty"]:
            if _Ls([(b_[0], b_[2]) for b_ in p_["body"]]).intersects(pr_): _zv.append((v["stavba"], v["c"], "plot")); break
        for s_ in MS["stromy"] + MS["drobne"]:
            if _Pt(s_["x"], s_["z"]).buffer(0.5).intersects(pr_): _zv.append((v["stavba"], v["c"], s_.get("druh", s_.get("model")))); break
    import struct as _st
    _f = open(K + "/hra/" + MIJ["modely"]["domy"]["soubor"][6:], "rb").read(); _gj = json.loads(_f[20:20 + _st.unpack("<I", _f[12:16])[0]])
    _ndv = {}
    for nd in _gj["nodes"]:
        m_ = nd.get("name", "").split("_Dvere")[0]
        if "_Dvere" in nd.get("name", "") and m_ in MIJ["pudorysy"] and abs(nd.get("translation", [0])[0]) > MIJ["pudorysy"][m_][0] - 0.3: _ndv[m_] = _ndv.get(m_, 0) + 1
    _uh = [s_ for s_ in MS["stavby"] if any(abs(s_["x"] - u_["stred"][0]) < 40 and abs(s_["z"] - u_["stred"][1]) < 40 for u_ in MS["usedlosti"])]
    _pocty = [(s_["model"], sum(1 for v in MS.get("vstupy", []) if v["stavba"] == s_["model"] and math.hypot(v["c"][0] - s_["x"], v["c"][1] - s_["z"]) < 12)) for s_ in _uh]
    _chybi = [p_ for p_ in _pocty if p_[1] < _ndv.get(p_[0], 0)]
    _nh = sum(1 for h in MS["hospodarske"] if h["model"] in MIJ["usedlosti"]["vstupy"]["hospodarske"])
    _nhv = sum(1 for v in MS.get("vstupy", []) if v["druh"] == "vrata")
    TEST("ves_vstupy_volne", not _zv and not _chybi and _nhv == _nh, "vstupů %d (domy %s, vrat %d/%d staveb), zatarasených %d %s" % (len(MS.get("vstupy", [])), _pocty[:3], _nhv, _nh, len(_zv), _zv[:4]))
    _kr = [u["i"] for u in MS["usedlosti"] if u["typ"] == "krcma"]
    _kp = [p_ for p_ in MS["ploty"] if p_["usedlost"] in _kr] + [b for b in MS["brany"] if b["usedlost"] in _kr]
    _kcel = any(s_["misto"] == "krcma" and "soubor" in s_ for s_ in MS["stavby"])   # 14. 11.: krčma = celek z Disku (plot a vrata v modelu)
    TEST("krcma_bez_plotu", _kcel or (_kr and not _kp), "krčma je celek z modelu (vlastní plot a vrata), usedlost se nestaví" if _kcel else "krčma (usedlost %s): plotů a vrat %d" % (_kr, len(_kp)))
    # ploty navazují (Míša 13. 11., foto 40db6a53: „ploty nenavazují na domy, jsou tam díry“; předloha kcd_ves_predloha/03):
    # každý konec plotu a vrat leží do 0,3 m od stavby (půdorys s okrajem 0,3 m) nebo do 0,3 m od jiného plotu/vrat téže usedlosti
    _seg = [(p_["usedlost"], _Ls([(b_[0], b_[2]) for b_ in p_["body"]])) for p_ in MS["ploty"]] + \
           [(b["usedlost"], _Ls([(b["a"][0], b["a"][2]), (b["b"][0], b["b"][2])])) for b in MS["brany"]]
    _otev = [bool(p_.get("otevreny_zacatek")) for p_ in MS["ploty"]] + [False] * len(MS["brany"])   # záměrně volný začátek u ulice (bez plotu před kovárnou, Míša 14. 11.)
    _volne = []
    for i_, (u_, l_) in enumerate(_seg):
        for q_ in ((l_.coords[-1],) if _otev[i_] else (l_.coords[0], l_.coords[-1])):
            P_ = _Pt(q_)
            if any(pp_.buffer(0.01).contains(P_) for pp_ in _pud): continue
            if any(j_ != i_ and s_[0] == u_ and s_[1].distance(P_) < 0.3 for j_, s_ in enumerate(_seg)): continue
            _volne.append((u_, round(q_[0], 1), round(q_[1], 1)))
    TEST("ploty_navazuji", _seg and not _volne, "konců plotů a vrat %d, volných (díra u stavby) %d %s" % (2 * len(_seg), len(_volne), _volne[:4]))
    # krčma (Míša 13. 11., foto 99af0653): venkovní sezení ne v cestě a ne před vstupem, stáj vraty k cestě, boční stavby dál od domu
    _kr9 = [u["i"] for u in MS["usedlosti"] if u["typ"] == "krcma"]; _sz = [e for e in MS.get("sezeni", []) if e["usedlost"] in _kr9]
    _osy = [_Ls(np.array(c_["osa"])[:, :2]) for c_ in json.load(open(K + "/pravidla/svet/cesty_puchart.json"))["cesty"] if c_.get("osa") and not c_.get("jen_maska")]
    _odc = min((min(o_.distance(_Pt(e["x"], e["z"])) for o_ in _osy) for e in _sz), default=0.0)
    _vst = [_Pg(v["pred"]) for v in MS.get("vstupy", []) if v["usedlost"] in _kr9]
    _zav = [e["model"] for e in _sz if any(q_.intersects(_Pt(e["x"], e["z"]).buffer(0.5)) for q_ in _vst) or any(q_.contains(_Pt(e["x"], e["z"])) for q_ in _pud)]
    _dk = [s_ for s_ in MS["stavby"] if s_["misto"] == "krcma"]; _hk = [h for h in MS["hospodarske"] if h["usedlost"] in _kr9]
    _vr = [v for v in MS.get("vstupy", []) if v["usedlost"] in _kr9 and v["stavba"] == "stodola_mala"]
    _k_ceste = bool(_vr) and all(min(o_.distance(_Pt(*v["c"])) for o_ in _osy) < min(o_.distance(_Pt(h["x"], h["z"])) for o_ in _osy for h in _hk if h["model"] == "stodola_mala") for v in _vr)
    _odst = min((_Pg(MS["pudorysy"][MS["stavby"].index(_dk[0])]).distance(_Pg(MS["pudorysy"][len(MS["stavby"]) + MS["hospodarske"].index(h)])) for h in _hk), default=0.0) if _dk else 0.0
    _szj = MIJ["usedlosti"]["typy"]["krcma"].get("sezeni", {})
    if _kcel: TEST("krcma_sezeni", True, "krčma je celek z modelu – venkovní sezení si Míša rozmístí sama (stavby bez výbavy)")
    else: TEST("krcma_sezeni", sum(1 for e in _sz if e["model"] == _szj.get("stul")) >= 2 and _odc >= _szj.get("od_cesty_min_m", 3.0) and not _zav and _k_ceste and _odst >= 3.0,
         "stolů %d, od osy cesty %.1f m, zavazí %s, stáj vraty k cestě %s, boční stavby od domu %.1f m (půdorysy s okrajem)" % (sum(1 for e in _sz if e["model"] == _szj.get("stul")), _odc, _zav, _k_ceste, _odst))
    # pás trávy u paty plotů a zdí (Míša 13. 11.; předloha kcd_ves_predloha: tráva 0,3–1 m u paty, ne kde se chodí): skvrny
    # pokrývají část délky (sem tam, ne pruh ani nic), žádná na cestě, ulici, cestičce, před vstupem, ve vratech
    if os.path.exists(D + "pata_pas.json"):
        _PP = json.load(open(D + "pata_pas.json")); _pk = _PP["pokryti"]
        _zak = [_Ls(c_["body"]).buffer(c_["polosirka"] - 0.2) for c_ in MS["vyslapano"]["cary"] if len(c_["body"]) > 1] + _vst + \
               [_Pg(v["pred"]) for v in MS.get("vstupy", [])] + [_Ls([(b["a"][0], b["a"][2]), (b["b"][0], b["b"][2])]).buffer(0.8) for b in MS["brany"]]
        from shapely.ops import unary_union as _uu2
        _Z = _uu2(_zak); _cs = TR.index("cesta"); _spat = []
        for v_ in _PP["bunky"].values():
            for sk in v_:
                m_ = ((sk[0] + sk[2]) / 2 + sk[4] * sk[6] / 2, (sk[1] + sk[3]) / 2 + sk[5] * sk[6] / 2)
                if _Z.contains(_Pt(*m_)) or trida(np.array([m_[0]]), np.array([m_[1]]))[0] == _cs: _spat.append((sk[7], round(m_[0], 1), round(m_[1], 1)))
        _okp = all(0.15 <= _pk.get(k_, 0) <= 0.85 for k_ in ("ves_plot", "ves_stavba")) and _pk.get("hrad_zed", 0) + _pk.get("hrad_budova", 0) > 0.02
        TEST("pata_pas_u_zdi", _okp and not _spat, "pokrytí délky hran %s (ves 15–85 %%, hrad > 2 %%), skvrn v cestě/před vstupem %d %s" % (_pk, len(_spat), _spat[:3]))
    else: TEST("pata_pas_u_zdi", False, "chybí hra/data/pata_pas.json (nastroje/stavby_vegetace.py)")
    TEST("ves_bez_vybaveni", not MS["drobne"] and not any(h["model"] == "kurnik" for h in MS["hospodarske"]),
         "drobností %d, kurníků %d (Míša 12. 11. večer: vybavení si udělá sama)" % (len(MS["drobne"]), sum(1 for h in MS["hospodarske"] if h["model"] == "kurnik")))

# textury staveb, plotů a vrat vsi existují (Míša 14. 11.: „všude ve vsi bílé ploty a brány“ – přestavba stodol smazala textury,
# na které ukazovaly ploty; chybějící textura = bílá plocha)
_tx_ch = []
for _src in ("hra/data/mista_stavby.json",):
    _d = json.load(open(K + "/" + _src)) if os.path.exists(K + "/" + _src) else {}
    for _k, _e in (_d.get("ploty_pravidla", {}).get("textury", {}) or {}).items():
        if isinstance(_e, dict):
            for _a in ("albedo", "normal"):
                if _e.get(_a) and not os.path.exists(K + "/hra/" + _e[_a][len("res://"):]): _tx_ch.append("%s.%s" % (_k, _a))
TEST("textury_vsi", not _tx_ch, "chybí %s" % _tx_ch if _tx_ch else "všechny textury plotů a vrat existují")

# Míša 14. 11.: „z dálky jsou to bílé kostky… chybí tam něco okolo, alespoň hmota“ – každá stavba má hrubý stupeň
# s texturou kreslený do dálky: domy _Daleko (daleko_textury pro každou plochu), celky a kovárna LOD1, stodoly a kůlny obal
_ms = json.load(open(K + "/pravidla/svet/mista.json")); _md = _ms["modely"]; _lv = _ms["usedlosti"]["lod"]; _dal_ch = []
for _m in _md["domy"]["koreny"]:
    if _m not in _md["domy"].get("daleko_textury", {}): _dal_ch.append("dům %s bez daleko_textury" % _m)
for _c, _e in _md.get("celky", {}).items():
    if isinstance(_e, dict) and not _e.get("lod1"): _dal_ch.append("celek %s bez lod1" % _c)
_ob = _md["hospodarske"].get("obal", {})
for _h in {h["model"] for h in json.load(open(K + "/hra/data/mista_stavby.json"))["hospodarske"]}:
    if _h not in _ob and not os.path.exists(K + "/hra/modely/stavby_h/%s_lod1.glb" % _h): _dal_ch.append("hospodářská %s bez obalu i LOD1" % _h)
if float(_lv.get("obal_do_m", 0)) < float(_lv["strom_daleko_do_m"]): _dal_ch.append("obal_do_m < strom_daleko_do_m (stavby zmizí dřív než les)")
TEST("stavby_z_dalky", not _dal_ch, "; ".join(_dal_ch) if _dal_ch else "všechny stavby mají texturovaný hrubý stupeň do %s m" % _lv.get("obal_do_m"))

# Míša 14. 11.: „tři druhy jabloní, ty naše stávající se mi nelíbí“ + „stará jabloň u hájovny a u hospody“
_jb = _md["stromy"]["jablon"]; _jb_ch = []
for _v in _jb.get("varianty", []):
    for _k in ("soubor", "lod1", "daleko"):
        if _k in _v and not os.path.exists(K + "/hra/" + _v[_k][6:]): _jb_ch.append("chybí " + _v[_k])
if len([_v for _v in _jb.get("varianty", []) if not _v.get("mlada")]) < 3: _jb_ch.append("méně než 3 staré jabloně")
_ms2 = json.load(open(K + "/hra/data/mista_stavby.json"))
for _st in [s for s in _ms2["stavby"] if s.get("soubor")]:
    if not any(t.get("stara") and math.hypot(t["x"] - _st["x"], t["z"] - _st["z"]) < 35 for t in _ms2["stromy"]): _jb_ch.append("u %s není stará jabloň" % _st["misto"])
TEST("jablone", not _jb_ch, "; ".join(_jb_ch) if _jb_ch else "varianty jabloní z Disku, stará jabloň u krčmy i hájovny")

# Míša 14. 11. noc: „plot před kovárnou zruš“, „domy … až moc vypadají bílé“ (#261)
_kv_ch = []
_kus = {h["usedlost"] for h in _ms2["hospodarske"] if h["model"] == "kovarna"}
for _u in _kus:
    if not any(p_.get("otevreny_zacatek") for p_ in _ms2["ploty"] if p_["usedlost"] == _u): _kv_ch.append("usedlost %d: uliční plot před kovárnou" % _u)
    if any(b_["druh"] == "branka" for b_ in _ms2["brany"] if b_.get("usedlost") == _u): _kv_ch.append("usedlost %d: branka před kovárnou" % _u)
if float(_md["domy"].get("jas_podrobny", 1.0)) >= 1.0: _kv_ch.append("domy bez ztlumení (jas_podrobny)")
if float(_ms["usedlosti"]["ploty"]["textury"]["kura"].get("nasob", 1.0)) >= 1.0: _kv_ch.append("kůly z kůry bez ztmavení")
TEST("kovarna_domy_jas", _kus and not _kv_ch, "; ".join(_kv_ch) if _kv_ch else "kovárna bez plotu do ulice, domy × %s, kůra × %s" % (_md["domy"]["jas_podrobny"], _ms["usedlosti"]["ploty"]["textury"]["kura"]["nasob"]))

# Míša 14. 11. noc: rostliny pásu u paty zdi přímo před dveřmi hájovny a před otevřenou kovárnou (#263)
from shapely.geometry import Polygon as _Pg2, LineString as _Ls2
_pp = json.load(open(K + "/hra/data/pata_pas.json")); _vyp = [_Pg2(e["poly"]) for e in _ms2["vyslapano"]["plochy"] if e["druh"] in ("pred_vstupem", "kovarna")]
_pv = 0
for _sk in (s_ for b_ in _pp["bunky"].values() for s_ in b_):
    _l = _Ls2([(_sk[0], _sk[1]), (_sk[2], _sk[3])])
    if any(_l.intersects(v_) for v_ in _vyp): _pv += 1
TEST("pred_vstupem_bez_rostlin", _vyp and _pv == 0, "skvrn pásu u paty v plochách před vstupy a před kovárnou: %d (ploch %d)" % (_pv, len(_vyp)))

# Míša 15. 11. (19 fotek): bílá voda a kameny, přístřešek kovárny, předměty před hájovnou, cesta u skály, hradba po valu
_vh = json.load(open(K + "/hra/data/voda_hra.json"))["vzhled_13_11"]; _c15 = []
if sum(_vh["pena_barva"]) / 3 > 0.5: _c15.append("pěna vody světlejší než 0,5")
if max(_vh.get("kameny_jas", [9])) > 1.1: _c15.append("kameny koryta jas > 1,1")
TEST("voda_kameny_nejsou_bile", not _c15, "; ".join(_c15) if _c15 else "pěna %s, kameny %s" % (_vh["pena_barva"], _vh["kameny_jas"]))
def _glb_uzly(f):
    import struct as _st
    b = open(f, "rb").read(); n_ = _st.unpack("<I", b[12:16])[0]; j_ = json.loads(b[20:20 + n_])
    return {nd["name"]: nd for nd in j_["nodes"]}
_ku = _glb_uzly(K + "/hra/modely/stavby_h/kovarna.glb"); _hu = _glb_uzly(K + "/hra/modely/stavby_h/hajovna.glb"); _c16 = []
_p4 = _ku.get("Kovarna_Kol_SloupP4-convcolonly", {}).get("translation", [0, 0, 0])[0]
if _p4 < 4.3: _c16.append("sloup přístřešku kovárny x %.2f (bok kovárny 3,14, má být ≥ 4,3)" % _p4)
for _jm in ("Hajovna_Kol_Sibenice22", "Hajovna_Kol_Stul", "Hajovna_Kol_Spalek"):
    if _jm + "-convcolonly" in _hu: _c16.append("hájovna má %s" % _jm)
TEST("upravy_modelu_disk", not _c16, "; ".join(_c16) if _c16 else "přístřešek kovárny dál (sloup x %.2f), před hájovnou bez šibenice, stolu a špalku" % _p4)
_c17 = []
_u3 = [c_ for c_ in json.load(open(K + "/pravidla/svet/cesty_puchart.json"))["cesty"] if c_["id"] == "udoli_440_3"][0]
_hrb = [q for q in _u3["osa"] if 188 < q[1] < 213 and q[0] > 0.0]
if _hrb: _c17.append("cesta k mostu u skály vede přes hrb (x > 0): %s" % _hrb[:3])
_hvj = json.load(open(K + "/pravidla/svet/hrad_puchart.json"))["A"]["hradba_val"]
if _hvj.get("plynula_koruna") or _hvj.get("rovna_koruna") != "ochoz": _c17.append("hradba po valu nemá rovnou korunu")
if float(_hvj.get("ochoz_od_branky_m", 0)) <= 0: _c17.append("hradba po valu bez ochozu")
TEST("cesta_skala_hradba_val", not _c17, "; ".join(_c17) if _c17 else "cesta k mostu po rovince, hradba po valu rovná s ochozem")

# Míša 15. 11.: „na budovu musí pršet, z okna a zpod přístřešku uvidím déšť“ – déšť se nevypíná pod střechou, shader zahazuje
# kapky jen pod mapou střech (pocasi.gd _strechy)
_dg = open(K + "/hra/scripts/pocasi.gd").read(); _ds = open(K + "/hra/shaders/dest.gdshader").read(); _c18 = []
if "mi.visible = venku" in _dg: _c18.append("déšť se pod střechou vypíná celý")
if "strechy" not in _ds or "_strechy(" not in _dg: _c18.append("chybí mapa střech v dešti")
if not json.load(open(K + "/hra/data/pocasi.json")).get("strechy"): _c18.append("pocasi.json bez strechy")
TEST("dest_pod_strechou", not _c18, "; ".join(_c18) if _c18 else "déšť vidět oknem, dveřmi a zpod přístřešku, pod střechou neprší")

# rozpočet trojúhelníků staveb (audit 15. 11.: žádný rozpočet na stavbu; Míša: „další optimalizace“) – z hlavičky glb
import struct as _st2
def _troj_glb(f, jen=None, bez=()):
    b_ = open(f, "rb").read(); n_ = _st2.unpack("<I", b_[12:16])[0]; j_ = json.loads(b_[20:20 + n_]); t_ = 0
    for nd in j_["nodes"]:
        if "mesh" not in nd or any(x in nd["name"] for x in bez) or (jen and not any(nd["name"].startswith(x) for x in jen)): continue
        t_ += sum(j_["accessors"][p_["indices"]]["count"] // 3 for p_ in j_["meshes"][nd["mesh"]]["primitives"] if "indices" in p_)
    return t_
_RS = json.load(open(K + "/pravidla/svet/rozpocty.json")).get("stavby", {}); _c19 = []
for _f, _e in _RS.get("soubory", {}).items():
    if not os.path.exists(K + "/" + _f): _c19.append("chybí " + _f); continue
    for _m in _e.get("modely", [None]):
        _t = _troj_glb(K + "/" + _f, [_m] if _m else None, tuple(_e.get("bez", [])))
        if _t > _e["max_troj"]: _c19.append("%s %s: %d troj. > %d" % (os.path.basename(_f), _m or "", _t, _e["max_troj"]))
TEST("stavby_rozpocet_troj", _RS and not _c19, "; ".join(_c19) if _c19 else "všechny stavby v rozpočtu (rozpocty.json stavby)")

# Míša 16. 11.: krb síně hradu B přesahoval okenní niky o 0,12–0,25 m („Posunout okna“) – topení na hradech (krb, kamna,
# topeniště z topeni.json vlozit, kam hrad) nesmí zasahovat do niky okna paláce (hra/data/okna_niky.json z hrady.okno_palace)
# ve stejné výšce; mezi nimi zdivo aspoň topeni.json odstup_niky_m. Půdorys topení = bbox LOD0 natočený yaw (Godot: +Z → (sin, cos)).
import sys as _sys2; _sys2.path.insert(0, K + "/nastroje"); import glb_sit as _gs
def _bbox_glb(f):
    j_, b_, _ = _gs.nacti(f); lo_ = np.full(3, 1e9); hi_ = -lo_
    def _w(i, M_):
        nonlocal lo_, hi_
        n_ = j_["nodes"][i]; M2 = M_ @ _gs.matice(n_)
        if "mesh" in n_ and "colonly" not in n_.get("name", ""):
            for pr_ in j_["meshes"][n_["mesh"]]["primitives"]:
                P_ = _gs.cti(j_, b_, pr_["attributes"]["POSITION"]); W_ = (M2 @ np.c_[P_, np.ones(len(P_))].T).T[:, :3]
                lo_ = np.minimum(lo_, W_.min(0)); hi_ = np.maximum(hi_, W_.max(0))
        for c_ in n_.get("children", []): _w(c_, M2)
    for r_ in j_["scenes"][0]["nodes"]: _w(r_, np.eye(4))
    return lo_, hi_
_TP = json.load(open(K + "/pravidla/svet/topeni.json")); _odst = float(_TP.get("odstup_niky_m", 0.2)); _c20 = []; _min20 = []
_pred20 = float(json.load(open(K + "/pravidla/svet/hrac.json"))["sezeni"]["vstat_m"]) + float(json.load(open(K + "/pravidla/svet/hrad_puchart.json"))["sedatko_niky"]["okraj_otvoru_m"])
_nk = json.load(open(D + "okna_niky.json"))["niky"] if os.path.exists(D + "okna_niky.json") else []
if not _nk: _c20.append("chybí hra/data/okna_niky.json (blender/puchart_hrad.py)")
for _v in _TP.get("vlozit", []):
    if _v.get("kam") != "hrad": continue
    _f = K + "/hra/modely/topeni/%s_LOD0.glb" % _v["topeni"]
    if not os.path.exists(_f): _c20.append("%s: chybí %s" % (_v["id"], os.path.basename(_f))); continue
    _lo, _hi = _bbox_glb(_f); _a = math.radians(_v["yaw_deg"]); _q = _v["poloha"]
    _ex = np.array([math.cos(_a), -math.sin(_a)]); _ez = np.array([math.sin(_a), math.cos(_a)])   # místní X a Z ve světě (x, z)
    _rc = [np.array([_q[0], _q[2]]) + _ex * x_ + _ez * z_ for x_ in (_lo[0], _hi[0]) for z_ in (_lo[2], _hi[2])]
    _ty0, _ty1 = _q[1] + _lo[1], _q[1] + _hi[1]; _bl = None
    for _n in _nk:
        if _n["y1"] <= _ty0 or _n["y0"] >= _ty1: continue
        _c = np.array([_n["stred"][0], _n["stred"][2]]); _u = np.array(_n["ven"]); _p = np.array(_n["podel"])
        # nika + volno před ní do místnosti (vstání ze sedátka hrac.json vstat_m + poloměr postavy sedatko_niky.okraj_otvoru_m):
        # krb přisazený k líci by jinak „nezasahoval“ (záda krbu 1 cm před nikou) – rozhoduje přesah podél zdi
        _nr = [_c + _u * (su * _n["hloubka"] / 2) + _p * (sp * _n["sirka"] / 2) for su in (-1, 1) for sp in (-1, 1)]
        _nr += [r_ - _u * _pred20 for r_ in _nr]
        if min(np.linalg.norm(r_ - _c) for r_ in _rc) > 6.0: continue
        # mezera = největší oddělení půdorysů na osách obou obdélníků (SAT); záporná = překryv
        _gap = -1e9
        for _ax in (_u, _p, _ex, _ez):
            a0, a1 = min(r_ @ _ax for r_ in _rc), max(r_ @ _ax for r_ in _rc); b0, b1 = min(r_ @ _ax for r_ in _nr), max(r_ @ _ax for r_ in _nr)
            _gap = max(_gap, b0 - a1, a0 - b1)
        if _bl is None or _gap < _bl: _bl = _gap
        if _gap < _odst - 1e-3: _c20.append("%s (%s) od niky okna u (%.2f; %.2f) jen %.2f m (min %.2f; záporné = zasahuje)" % (_v["id"], _v["topeni"], _c[0], _c[1], _gap, _odst))
    if _bl is not None: _min20.append("%s %.2f m" % (_v["id"], _bl))
TEST("krb_okna", not _c20, "; ".join(_c20) if _c20 else "topení hradů mimo okenní niky (nejbližší zdivo: %s; min %.2f m)" % (", ".join(_min20) or "žádná nika ve výšce", _odst))

# Míša 16. 11.: Dům 2 „černé fleky a světlé pruhy na omítce“ – stín vrhal hrubý obal, jehož stěny ležely před lícem domu;
# stěna obrácená ke slunci nesmí ležet ve stínu vlastní stínové kopie (mista.json modely.domy.stin_obal). Paprsek z vrcholu
# vnějšího líce (síť <Dům>_Vnejsek bez střechy, normála ven a vodorovně) šikmo vzhůru ke slunci (sklon stin_test_sklon) nesmí
# narazit do stěn <Dům>_Daleko_Stin; povolený podíl zásahů stin_test_max (okraje otvorů, nároží).
def _paprsky_troj(O, D, T):
    e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]; hit = np.zeros(len(O), bool)
    for k in range(0, len(O), 256):
        o = O[k:k + 256, None, :]; dd = D[k:k + 256, None, :]
        pv = np.cross(dd, e2[None]); det = np.einsum("ijk,jk->ij", pv, e1); inv = 1.0 / np.where(np.abs(det) < 1e-12, 1e-12, det)
        tv = o - T[None, :, 0]; u = np.einsum("ijk,ijk->ij", tv, pv) * inv
        qv = np.cross(tv, e1[None]); v = np.einsum("ijk,ijk->ij", dd, qv) * inv; t = np.einsum("ijk,jk->ij", qv, e2) * inv
        hit[k:k + 256] = ((np.abs(det) > 1e-12) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4)).any(1)
    return hit
_SO = json.load(open(K + "/pravidla/svet/mista.json"))["modely"]["domy"]; _so = _SO.get("stin_obal", {}); _c21 = []; _r21 = []
_jd, _bd, _ = _gs.nacti(K + "/hra/" + _SO["soubor"][len("res://"):]); _Nd = {n_.get("name"): n_ for n_ in _jd["nodes"]}
_MATd = [m_.get("name", "") for m_ in _jd["materials"]]
for _dum in _SO["koreny"]:
    _ns = _Nd.get(_dum + _so.get("obal", "_Daleko") + _so.get("pripona", "_Stin")); _nv = _Nd.get(_dum + "_Vnejsek")
    if _nv is None: continue
    _no = _Nd.get(_dum + _so.get("obal", "_Daleko"))   # obal bez stěn (chýše s kůrou: stěny = střecha) – nástroj kopii nedělá
    if _no is None or "mesh" not in _no or not any(_MATd[p_["material"]].endswith(_so["steny"]) for p_ in _jd["meshes"][_no["mesh"]]["primitives"]): continue
    if _ns is None: _c21.append("%s bez stínové kopie obalu" % _dum); continue
    _T = np.concatenate([_gs.cti(_jd, _bd, p_["attributes"]["POSITION"])[_gs.cti(_jd, _bd, p_["indices"]).reshape(-1, 3)] for p_ in _jd["meshes"][_ns["mesh"]]["primitives"] if _MATd[p_["material"]].endswith(_so["steny"])] or [np.zeros((0, 3, 3))]).astype(np.float64)
    if not len(_T): continue
    _V = []   # vrcholy líců (poloha, normála) v pásu test_y
    for p_ in _jd["meshes"][_nv["mesh"]]["primitives"]:
        if any(x_ in _MATd[p_["material"]] for x_ in _so.get("test_bez", [])): continue
        P_ = _gs.cti(_jd, _bd, p_["attributes"]["POSITION"]).astype(np.float64); N_ = _gs.cti(_jd, _bd, p_["attributes"]["NORMAL"]).astype(np.float64)
        m_ = (np.abs(N_[:, 1]) < 0.3) & (P_[:, 1] > _so["test_y"][0]) & (P_[:, 1] < _so["test_y"][1])
        _V.append(np.c_[P_[m_], N_[m_]])
    _V = np.concatenate(_V); _O = []; _D = []
    for _ax in (0, 2):   # jen vnější plášť: líc s normálou ven podél osy, nejvýš odsazeni_m za nejvzdálenějším lícem na té straně
        for _sg in (1, -1):
            _s = _V[:, 3 + _ax] * _sg > 0.9
            if _s.sum() < 5: continue
            _kr = _V[_s, _ax] * _sg; _s[_s] = _kr >= np.percentile(_kr, 95) - _so["odsazeni_m"]
            d_ = np.zeros((_s.sum(), 3)); d_[:, _ax] = _sg; d_[:, 1] = _so["test_sklon"]; d_ /= np.linalg.norm(d_, axis=1)[:, None]
            _O.append(_V[_s, :3] + d_ * 0.01); _D.append(d_)
    if not _O: continue
    _O = np.concatenate(_O); _D = np.concatenate(_D)
    if len(_O) > 4000: _ix = np.linspace(0, len(_O) - 1, 4000).astype(int); _O = _O[_ix]; _D = _D[_ix]
    _h = _paprsky_troj(_O, _D, _T).mean(); _r21.append("%s %.1f %%" % (_dum, 100 * _h))
    if _h > _so["test_max"]: _c21.append("%s: %.1f %% líce na slunci ve stínu vlastní stínové kopie obalu (max %.1f %%)" % (_dum, 100 * _h, 100 * _so["test_max"]))
TEST("stin_domu", not _c21, "; ".join(_c21) if _c21 else "líc domů na slunci mimo stín vlastního obalu (zásahy: %s)" % ", ".join(_r21))

# lůžka: okraj LOD bez prolínání nechá po načtení v pásmu okraje skrytý LOD0 i LOD1 (chyby.md 355)
import glob as _gl, re
_c22 = []
for _f in sorted(_gl.glob(K + "/hra/modely/luzka/*.tscn")):
    for _m in re.findall(r"visibility_range_(?:begin|end)_margin = ([0-9.]+)", open(_f).read()):
        if float(_m) > 0.0: _c22.append("%s margin %s" % (os.path.basename(_f), _m)); break
TEST("luzka_lod_okraj", not _c22, "; ".join(_c22) if _c22 else "lůžka: LOD bez okraje (žádná mezera ve viditelnosti)")

# barvy vrcholů modelů od modeláře (glTF COLOR_0 lineární) převedené na sRGB – Compatibility je násobí s albedem v sRGB
# (chyby.md 356: houně černá); sady pravidla/svet/barvy_vrcholu.json, zpráva nastroje/barvy_vrcholu.py
_bv = json.load(open(K + "/pravidla/svet/barvy_vrcholu.json")); _c23 = []; _n23 = {}
_zp = json.load(open(K + "/" + _bv["zprava"])) if os.path.exists(K + "/" + _bv["zprava"]) else {}
for _sd, _sv in _bv["sady"].items():
    _site = sorted(_gl.glob(K + "/" + _sv["site"])); _n23[_sd] = len(_site)
    if not _site: _c23.append("sada %s: žádné sítě %s" % (_sd, _sv["site"]))
    for _f in _site:
        _z = _zp.get("res://" + os.path.relpath(_f, K + "/hra"))
        if _z is None: _c23.append("%s chybí ve zprávě %s (barvy_vrcholu.py nepřevedl)" % (os.path.basename(_f), _bv["zprava"])); continue
        if _z["velikost"] != os.path.getsize(_f): _c23.append("%s změněna po převodu (velikost %d ≠ %d)" % (os.path.basename(_f), os.path.getsize(_f), _z["velikost"])); continue
        if _bv["prevest_na_srgb"] and _z["vrcholu_s_barvou"] > 0 and not _z["srgb"]: _c23.append("%s barvy vrcholů lineární (nepřevedené)" % os.path.basename(_f))
TEST("barvy_vrcholu", not _c23, "; ".join(_c23) if _c23 else "barvy vrcholů v sRGB: " + ", ".join("%s %d sítí" % kv for kv in _n23.items()))
# importy normálových map lůžek jako normálové (luzka.json normal_import)
_ni = json.load(open(K + "/pravidla/svet/luzka.json"))["normal_import"]; _c24 = []
for _f in sorted(_gl.glob(K + "/hra/modely/luzka/textures/*" + _ni["pripona"])):
    _t = open(_f + ".import").read() if os.path.exists(_f + ".import") else ""
    if "compress/normal_map=%d" % _ni["normal_map"] not in _t: _c24.append("%s import bez compress/normal_map=%d" % (os.path.basename(_f), _ni["normal_map"]))
TEST("luzka_normaly", not _c24, "; ".join(_c24) if _c24 else "lůžka: normálové mapy importované jako normálové")

# --- stavby vsi z Míšina průchodu 17. 11. (docs/rozpracovane/chyby_misa_17_11.md 8–16) ---------------------------------
def _glb_svet(f):   # [(jméno uzlu, materiál, P trojúhelníků (n,3,3))] ve světě modelu
    j_, b_, _ = _gs.nacti(f); out_ = []
    def go(i, M):
        n = j_["nodes"][i]; M = M @ _gs.matice(n)
        if "mesh" in n:
            for p in j_["meshes"][n["mesh"]]["primitives"]:
                X = _gs.cti(j_, b_, p["attributes"]["POSITION"]).astype(float); X = X @ M[:3, :3].T + M[:3, 3]
                I = _gs.cti(j_, b_, p["indices"]).reshape(-1, 3) if "indices" in p else np.arange(len(X)).reshape(-1, 3)
                out_.append((n.get("name", ""), j_["materials"][p["material"]]["name"] if "material" in p else "", X[I]))
        for c in n.get("children", []): go(c, M)
    for r in j_["scenes"][j_.get("scene", 0)]["nodes"]: go(r, np.eye(4))
    return out_, j_

# pavlače celků bez mezer v zábradlí (Míša 17. 11., snímky 09, 10: „chybí zábradlí v mezeře mezi sloupem a stěnou“): po obvodu
# pochozí plochy (mista.json modely.celky.<model>.pavlace) po 0,2 m – od 0,15 m uvnitř do 0,35 m ven kolize (konvexní -convcolonly) ve výšce
# 0,3–0,9 m nad podlahou (zábradlí, stěna), nebo navazující pochozí plocha 0–0,5 m pod úrovní (podesta, podlaha za dveřmi)
from scipy.spatial import Delaunay as _Del
_MJ = json.load(open(K + "/pravidla/svet/mista.json")); _c25 = []; _n25 = 0
for _mm, _cv in _MJ["modely"]["celky"].items():
    if not isinstance(_cv, dict) or not _cv.get("pavlace"): continue
    _f = K + "/hra/" + _cv["soubor"].replace("res://", "")
    if not os.path.exists(_f): _c25.append("%s chybí %s" % (_mm, _f)); continue
    _hull = []
    for _jm, _mt, _T in _glb_svet(_f)[0]:
        if "colonly" in _jm and len(_T): _hull.append(_Del(np.unique(_T.reshape(-1, 3).round(4), axis=0)))
    def _v_kolizi(P): return np.any([h.find_simplex(P) >= 0 for h in _hull], axis=0)
    for _pv in _cv["pavlace"]:
        x0, x1, z0, z1 = _pv["oblast"]; y = _pv["y"]
        obv = [((x, z0), (0, -1)) for x in np.arange(x0, x1 + 1e-6, 0.2)] + [((x, z1), (0, 1)) for x in np.arange(x0, x1 + 1e-6, 0.2)] + \
              [((x0, z), (-1, 0)) for z in np.arange(z0, z1 + 1e-6, 0.2)] + [((x1, z), (1, 0)) for z in np.arange(z0, z1 + 1e-6, 0.2)]
        for (px, pz), (dx, dz) in obv:
            _n25 += 1; ok = False
            for d in (-0.15, -0.08, 0.0, 0.1, 0.2, 0.35):   # zábradlí stojí i kousek uvnitř hrany podlahy (sloupy pavlače)
                q = np.array([[px + dx * d, y + h, pz + dz * d] for h in (0.3, 0.6, 0.9)])
                if _v_kolizi(q).all(): ok = True; break
                if d > 0 and _v_kolizi(np.array([[px + dx * d, y - h, pz + dz * d] for h in (0.05, 0.3, 0.5)])).any(): ok = True; break
            if not ok: _c25.append("%s (%.2f; %.2f) ven (%d, %d)" % (_mm, px, pz, dx, dz))
TEST("pavlac_zabradli", _n25 > 0 and not _c25, ("%d míst bez zábradlí: %s" % (len(_c25), _c25[:6])) if _c25 else "pavlače celků: %d bodů obvodu, všude zábradlí, stěna nebo navazující podlaha" % _n25)

# chýše (zemljanky z A-chýší Havrana) bez průduchů u země (Míša 17. 11., snímek 16: „stěna nesahá až na zem“; „kontroluj všechny
# strany… ať jim tam fouká“): vodorovné paprsky ze středu chýše ve výšce 0,05–0,45 m nad zemí do všech stran (144 směrů, 3 body
# podél osy) musí do 4 m trefit stěnu, střechu nebo zídku; jen dveřní otvor nad prahem je volný. Dveře v otvoru: pant uzlu
# křídla na ostění (dvere_x, dvere_z), křídlo nejdál 1 m od pantu (snímek 15: dveře stály 1,9 m vedle chýše)
_ZT = json.load(open(K + "/pravidla/svet/zajimava_mista.json"))["modely"]["zemljanky"]; _c26 = []; _n26 = 0
def _paprsek(T, o, d):
    e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]; hh = np.cross(d, e2); a = (e1 * hh).sum(1)
    okk = np.abs(a) > 1e-9; f = np.where(okk, 1 / np.where(okk, a, 1), 0); s_ = o - T[:, 0]; u = f * (s_ * hh).sum(1)
    q = np.cross(s_, e1); v = f * (q @ d); t = f * (e2 * q).sum(1)
    hit = okk & (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (t > 1e-4)
    return t[hit].min() if hit.any() else None
for _zm, _zt in _ZT["typy"].items():
    _f = "%s/%s/%s.glb" % (K, _ZT["vystup"], _zm)
    if not os.path.exists(_f): _c26.append("%s chybí" % _zm); continue
    _site, _j26 = _glb_svet(_f)
    _T = np.concatenate([T for jm, mt, T in _site if not any(v in jm for v in ("Jama", "Rohoze", "Daleko", "Spani", "colonly", "Kol"))])
    _yt = 0.02; _der = []
    for h in (0.05, 0.15, 0.25, 0.35, 0.45):
        for k in range(144):
            a = 2 * math.pi * k / 144; d = np.array([math.sin(a), 0.0, math.cos(a)])
            for z0_ in (-1.2, 0.0, 1.2):
                _n26 += 1; tt = _paprsek(_T, np.array([0.0, _yt + h, z0_]), d)
                if tt is not None and tt < 4.0: continue
                if d[2] > 0.05:
                    xg = d[0] * (_zt["dvere_z"] - z0_) / d[2]
                    if _zt["dvere_x"][0] - 0.02 <= xg <= _zt["dvere_x"][1] + 0.02 and _yt + h >= _zt["prah_y"] - 0.05: continue
                _der.append("h %.2f směr %d°" % (h, round(math.degrees(a))))
    if _der: _c26.append("%s: %d průduchů (%s)" % (_zm, len(_der), ", ".join(_der[:4])))
    _dv = next((n for n in _j26["nodes"] if n.get("name", "").endswith("_Dvere")), None)
    if _dv is None: _c26.append("%s bez dveří" % _zm)
    else:
        _tr = _dv.get("translation", [0, 0, 0])
        if not (_zt["dvere_x"][0] - 0.1 <= _tr[0] <= _zt["dvere_x"][1] + 0.1 and abs(_tr[2] - _zt["dvere_z"]) <= 0.15):
            _c26.append("%s: pant dveří (%.2f; %.2f) mimo otvor x %s z %.2f" % (_zm, _tr[0], _tr[2], _zt["dvere_x"], _zt["dvere_z"]))
        _P = np.concatenate([T.reshape(-1, 3) for jm, mt, T in _site if jm.endswith("_Dvere")])
        if np.linalg.norm((_P - np.array(_tr))[:, [0, 2]], axis=1).max() > 1.0: _c26.append("%s: křídlo dveří dál než 1 m od pantu" % _zm)
TEST("chyse_bez_pruduchu", _n26 > 0 and not _c26, "; ".join(_c26) if _c26 else "zemljanky %s: %d paprsků u země, všechny strany uzavřené, dveře v otvoru" % (", ".join(_ZT["typy"]), _n26))

# krytina všech staveb pro déšť a „pod střechou“ (Míša 17. 11., snímek 12: v podkroví krčmy pršelo; hra/scripts/strechy.gd):
# každý model stavby vsi, celku a zemljanky má hrubý obal (*_Daleko / LOD1_*) s plochou krytiny (pocasi.json strechy.materialy)
_PS = json.load(open(K + "/pravidla/svet/pocasi.json"))["strechy"]; _c27 = []; _n27 = 0
def _krytina(f, jen=None):
    j_, _, _ = _gs.nacti(f); n_ = 0
    for n in j_["nodes"]:
        nm = n.get("name", "")
        if "mesh" not in n or nm.endswith("_Stin") or not (any(nm.endswith(k) for k in _PS["uzly_konec"]) or any(nm.startswith(k) for k in _PS["uzly_zacatek"])): continue
        if jen and not nm.startswith(jen): continue
        for p in j_["meshes"][n["mesh"]]["primitives"]:
            if "material" in p and any(m.lower() in j_["materials"][p["material"]]["name"].lower() for m in _PS["materialy"]): n_ += 1
    return n_
_MS = json.load(open(D + "mista_stavby.json"))
for _md in sorted({s["model"] for s in _MS["stavby"] if "soubor" not in s}):
    _n27 += 1
    if _krytina(K + "/hra/modely/stavby_h/domy.glb", _md + "_Daleko") == 0: _c27.append("dům %s bez krytiny v obalu" % _md)
for _s in {s["soubor"]: s for s in _MS["stavby"] if "soubor" in s}.values():
    _n27 += 1; _f = K + "/hra/" + str(_s.get("lod1", "")).replace("res://", "")
    if not _s.get("lod1") or not os.path.exists(_f) or _krytina(_f) == 0: _c27.append("celek %s bez LOD1 s krytinou" % _s["model"])
for _zm in _ZT["typy"]:
    _n27 += 1
    if _krytina("%s/%s/%s.glb" % (K, _ZT["vystup"], _zm)) == 0: _c27.append("%s bez krytiny v obalu" % _zm)
if os.path.exists(K + "/hra/modely/stavby_h/mlyn_lod1.glb"):
    _n27 += 1
    if _krytina(K + "/hra/modely/stavby_h/mlyn_lod1.glb") == 0: _c27.append("mlýn bez krytiny v LOD1")
TEST("strechy_krytina", _n27 > 0 and not _c27, "; ".join(_c27) if _c27 else "%d typů staveb má v obalu krytinu (strechy.gd: pod ní neprší, uvnitř světlo interiéru)" % _n27)

# topení bez výbavy sloučené do sítě (Míša 17. 11., snímek 11: lopata prochází pecí): v přebalených modelech (hra/modely/topeni)
# nezbyl žádný trojúhelník celý v kvádru topeni.json modely.<model>.odebrat (LOD0, LOD1 i varianty z něj)
_TJ = json.load(open(K + "/pravidla/svet/topeni.json")); _c28 = []; _n28 = 0
for _tm, _tv in _TJ["modely"].items():
    if not isinstance(_tv, dict) or not _tv.get("odebrat"): continue
    _jm28 = [_tm] + [k for k, v in _TJ["varianty"].items() if isinstance(v, dict) and v.get("z") == _tm]
    for _v in _jm28:
        for _lod in ("LOD0", "LOD1"):
            _f = "%s/%s/%s_%s.glb" % (K, _TJ["vystup"], _v, _lod)
            if not os.path.exists(_f): _c28.append("%s chybí" % os.path.basename(_f)); continue
            j_, b_, _ = _gs.nacti(_f); _n28 += 1
            for n in j_["nodes"]:
                for o in _tv["odebrat"]:
                    if "mesh" not in n or not n.get("name", "").startswith(o["uzel"]): continue
                    for p in j_["meshes"][n["mesh"]]["primitives"]:
                        V = _gs.cti(j_, b_, p["attributes"]["POSITION"])[_gs.cti(j_, b_, p["indices"]).reshape(-1, 3)]; kv = o["kvadr"]
                        uv = np.ones(len(V), bool)
                        for a_ in range(3): uv &= (V[..., a_] >= kv[2 * a_]).all(1) & (V[..., a_] <= kv[2 * a_ + 1]).all(1)
                        if uv.any(): _c28.append("%s %s: %d troj. v kvádru odebrat" % (os.path.basename(_f), n["name"], int(uv.sum())))
TEST("topeni_bez_vybavy", _n28 > 0 and not _c28, "; ".join(_c28) if _c28 else "%d modelů topení bez odebrané výbavy (lopata pece krčmy)" % _n28)

# Míša 17. 11. (snímek 06, palác B): pavlač hradby vedla skrz zeď do paláce – prkna, krakorce a zábradlí ochozu v přízemní síni
# („spodek ochozu černý“). Deska žádného ochozu obou hradů (hra/data/ochozy_kontrola.json z puchart_hrad.ochoz2) nesmí ležet
# v obrysu budovy nebo věže po vnější líc zdí (BUDOVY_K) ve výšce budovy – ochoz končí na líci, dovnitř vede jen portálkem.
_OK29 = D + "ochozy_kontrola.json"; _c29 = []; _n29 = 0
if not os.path.exists(_OK29): _c29.append("chybí hra/data/ochozy_kontrola.json (blender/puchart_hrad.py)")
else:
    _oj = json.load(open(_OK29)); _bd29 = _oj.get("budovy", [])
    if not _bd29: _c29.append("žádné budovy v ochozy_kontrola.json")
    for _rh, _y in _oj.get("ochozy", []):
        _n29 += 1; _R = np.array(_rh, float); _vz = []
        for a_ in np.linspace(0.03, 0.97, 12):
            for b_ in np.linspace(0.06, 0.94, 4):
                _vz.append(_R[0] + (_R[1] - _R[0]) * a_ + (_R[3] - _R[0]) * b_)
        for _b in _bd29:
            if not (_b["y0"] - 0.05 <= _y <= _b["y1"] + 0.05): continue
            _c = np.array(_b["c"]); _d = np.array(_b["d"]); _s = np.array(_b["s"])
            _z = _b.get("zed", 0.0)   # vnitřek = obrys bez zdí (konec desky smí být zapuštěný ve zdivu – šikmý líc)
            _in = [q for q in _vz if abs((q - _c) @ _d) < _b["pul_d"] - _z - 0.02 and abs((q - _c) @ _s) < _b["pul_s"] - _z - 0.02]
            if _in: _c29.append("ochoz y %.2f u (%.1f; %.1f) vede do %s (%d vzorků desky uvnitř)" % (_y, _in[0][0], _in[0][1], _b["jm"], len(_in)))
TEST("ochoz_mimo_budovy", _n29 > 0 and not _c29, "; ".join(_c29[:6]) if _c29 else "%d desek ochozů obou hradů mimo budovy a věže (%d obrysů)" % (_n29, len(_bd29)))

# Míša 17. 11. (snímek 03, „Uhasit oheň“): ústí kamen paláce A ze síně – z dřevěné příčky trčela čela přikládacího tunelu modelu
# kamen kolem tmavé desky. Kamenné ostění ústí (hrad_puchart.json A.palac_interier.dispozice.kamna.usti) musí krýt průřez zdí
# tunelu modelu (uzly Zadni_prikladaci_tunel* v LOD0) a otvor nesmí být širší/vyšší než světlost tunelu.
_c30 = []; _KM = K + "/hra/modely/topeni/Kamna_Hradni_Nadobkova_LOD0.glb"
_us = json.load(open(K + "/pravidla/svet/hrad_puchart.json"))["A"]["palac_interier"]["dispozice"]["kamna"].get("usti")
if not _us: _c30.append("chybí hrad_puchart.json A.palac_interier.dispozice.kamna.usti")
elif not os.path.exists(_KM): _c30.append("chybí %s" % os.path.basename(_KM))
else:
    j_, b_, _ = _gs.nacti(_KM); _tl = []
    def _w30(i, M_):
        n_ = j_["nodes"][i]; M2 = M_ @ _gs.matice(n_)
        if "mesh" in n_ and n_.get("name", "").startswith("Zadni_prikladaci_tunel"):
            for pr_ in j_["meshes"][n_["mesh"]]["primitives"]:
                P_ = _gs.cti(j_, b_, pr_["attributes"]["POSITION"]); _tl.append((M2 @ np.c_[P_, np.ones(len(P_))].T).T[:, :3])
        for c_ in n_.get("children", []): _w30(c_, M2)
    for r_ in j_["scenes"][0]["nodes"]: _w30(r_, np.eye(4))
    if not _tl: _c30.append("v modelu kamen chybí uzly Zadni_prikladaci_tunel*")
    else:
        _T = np.vstack(_tl); _x1 = float(np.abs(_T[:, 0]).max()); _y0, _y1 = float(_T[:, 1].min()), float(_T[:, 1].max())
        _sv = min(float(np.abs(_T[:, 0][np.abs(_T[:, 0]) > 0.01]).min()), 1.0)   # vnitřní líc boků tunelu
        _ow, (_oy0, _oy1), _rw = _us["otvor_sirka_m"], _us["otvor_y_m"], _us["ramec_m"]
        if _ow / 2 + _rw < _x1 + 0.02: _c30.append("rám ±%.2f m nekryje boky tunelu ±%.2f m" % (_ow / 2 + _rw, _x1))
        if _oy1 + 0.28 < _y1 + 0.02 or _oy0 - 0.15 > _y0 - 0.0: _c30.append("rám %.2f–%.2f m nekryje tunel %.2f–%.2f m" % (_oy0 - 0.15, _oy1 + 0.28, _y0, _y1))
        if _ow / 2 > _sv + 0.02: _c30.append("otvor ±%.2f m širší než světlost tunelu ±%.2f m" % (_ow / 2, _sv))
TEST("usti_kamen", not _c30, "; ".join(_c30) if _c30 else "kamenné ostění ústí kamen kryje čela přikládacího tunelu modelu (A.palac_interier kamna.usti)")

# --- tráva podle zápoje korun (Míša 17. 11.: „Havran má velkou hustotu trávy, ale pod stromy v lese ne“; Havran test les_trava,
# pravidla/svet/louka.json les + test): pod zapojenými korunami ≈ žádná tráva louky, na louce a světlinách hustá; koruny se tu
# počítají nezávisle na kryt.png (kruh poloměru koruny glb modelu × měřítko les.gd) – chyba 17. 11.: kryt_korun.py brala
# korunu 0,2 × výška (modely 0,23–0,6) a tráva rostla pod korunami
import glob as _gl, struct as _sx
from scipy.ndimage import uniform_filter as _uf
_LO = json.load(open(D + "louka.json")); _LL = _LO["les"]; _LT = _LO["test"]; _SM = json.load(open(D + "stromy_modely.json"))
_KRP = np.array(Image.open(D + "kryt.png"), float) / 255.0; _KRP = _KRP[..., 0] if _KRP.ndim == 3 else _KRP
def _rglb(f):
    b = open(f, "rb").read(); n = _sx.unpack("<I", b[12:16])[0]; g = json.loads(b[20:20 + n]); mn, mx = [1e9] * 3, [-1e9] * 3
    for m in g["meshes"]:
        for p in m["primitives"]:
            a = g["accessors"][p["attributes"]["POSITION"]]; mn = [min(x, y) for x, y in zip(mn, a["min"])]; mx = [max(x, y) for x, y in zip(mx, a["max"])]
    return ((mx[0] - mn[0]) + (mx[2] - mn[2])) / 4.0
_RM = {os.path.basename(f)[:-4]: _rglb(f) for f in _gl.glob(K + "/hra/modely/stromy/*.glb") if not f.endswith(("_daleko.glb", "_lod1.glb"))}
_SA = np.fromfile(D + "stromy.bin", np.float32).reshape(-1, 5); _SDR = json.load(open(D + "stromy.json"))["dreviny"]
_kk = SJ["krok_m"]; _cov = np.zeros(ST.shape, bool); _yy, _xx = np.mgrid[-14:15, -14:15]; _mer = _SM["meritko"]
for x_, z_, h_, d_, _ in _SA:
    mo = _SM["dreviny"][_SDR[int(d_)]]["model"]; vh = _SM["varianty"][mo]
    nj = min((v for v in vh if not v.startswith("star")), key=lambda v: abs(vh[v] - h_))
    r_ = _RM.get("%s_%s" % (mo, nj), 0.3 * vh[nj]) * min(max(h_ / vh[nj], _mer[0]), max(_mer[1], _SM.get("meritko_max_stare", _mer[1]))) * 0.88 / _kk   # 0,88: kraj koruny (smoothstep 0,7–1,05)
    ci = int((x_ - SJ["x0_hra"]) / _kk); ri = int((z_ - SJ["z0_hra"]) / _kk)
    if not (14 <= ci < ST.shape[1] - 14 and 14 <= ri < ST.shape[0] - 14): continue
    _cov[ri - 14:ri + 15, ci - 14:ci + 15] |= (_xx + ci + 0.5 - (x_ - SJ["x0_hra"]) / _kk) ** 2 + (_yy + ri + 0.5 - (z_ - SJ["z0_hra"]) / _kk) ** 2 <= r_ * r_
_nok = max(1, int(round(_LL["okoli_m"] / (2 * _kk)))) * 2 + 1
_okol = _uf(_cov.astype(float), _nok)
_lesm = np.isin(ST, [i for i, t in enumerate(TR) if t.startswith("les")])
def _ss(a, e0, e1): t = np.clip((a - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
_HU = np.array([float(_LO["tridy"].get(t, 0.0)) for t in TR])[ST] * (1 - _LL["ubytek"] * _ss(_KRP, _LL["kryt_od"], _LL["kryt_do"]))
_pz = _lesm & _cov & (_okol >= _LL["okoli_do"])
_lou = np.isin(ST, [TR.index(t) for t in ("louka_kosena", "pastvina") if t in TR])
_svt = _lesm & (_uf(_cov.astype(float), 3) == 0) & np.isin(ST, [i for i, t in enumerate(TR) if _LO["tridy"].get(t, 0) > 0])   # světlo: bez koruny ±3 m
_h_pz = float(_HU[_pz].mean()) if _pz.any() else 1.0; _p_pz = float((_HU[_pz] >= _LT["prah"]).mean()) if _pz.any() else 1.0
_h_lo = float(_HU[_lou].mean()) if _lou.any() else 0.0; _h_sv = float(_HU[_svt].mean()) if _svt.any() else 0.0
_bz = "trava" in BY.get("zapoj", {}).get("druhy", [])
TEST("trava_zapoj", _pz.sum() > 1000 and _h_pz <= _LT["max_hustota"] and _p_pz <= _LT["max_podil_travy"] and _h_lo >= _LT["louka_min"] and _h_sv >= _LT["svetlina_min"] and _bz,
     "pod zapojenými korunami (%d bodů 2 m, %.0f %% lesa): hustota trávy %.3f (mez %.2f), bodů s trávou %.1f %% (mez %.0f %%); louka %.2f (min %.2f), světliny v lese %.2f (min %.2f, %d bodů); byliny tráva podle zápoje %s"
     % (int(_pz.sum()), 100 * _pz.sum() / max(_lesm.sum(), 1), _h_pz, _LT["max_hustota"], 100 * _p_pz, 100 * _LT["max_podil_travy"], _h_lo, _LT["louka_min"], _h_sv, _LT["svetlina_min"], int(_svt.sum()), _bz))

# --- skupina C Míšina průchodu 17. 11. (voda, mlýn, lávka, mapa) ---
# voda je vidět (Míša 17. 11., snímky 13 a 19: „nemáš vodu v potoce“): hladina má nejmenší krytí i na mělčině a lesk vlnek,
# hra čte stejná čísla, shader je použije (kryti_min v ALPHA, hlavni.gd předá)
_c29 = []; _vz29 = json.load(open(K + "/pravidla/svet/voda_hra.json"))["vzhled_13_11"]; _vh29 = json.load(open(K + "/hra/data/voda_hra.json"))["vzhled_13_11"]
if float(_vz29.get("kryti_min", 0)) < 0.3: _c29.append("kryti_min %.2f < 0,3 (mělká voda shora průhledná = prázdné koryto)" % float(_vz29.get("kryti_min", 0)))
if float(_vz29.get("specular", 0)) < 0.2: _c29.append("specular %.2f < 0,2 (hladina bez lesku)" % float(_vz29.get("specular", 0)))
for _k29 in ("kryti_min", "cirost_m", "specular", "drsnost_klid"):
    if _vz29.get(_k29) != _vh29.get(_k29): _c29.append("hra/data/voda_hra.json %s %s ≠ pravidla %s" % (_k29, _vh29.get(_k29), _vz29.get(_k29)))
_sh29 = open(K + "/hra/shaders/voda.gdshader").read()
if "uniform float kryti_min" not in _sh29 or not re.search(r"ALPHA\s*=.*kryti_min", _sh29): _c29.append("voda.gdshader nepoužije kryti_min")
if '"kryti_min"' not in open(K + "/hra/scripts/hlavni.gd").read(): _c29.append("hlavni.gd nepředá kryti_min shaderu")
TEST("voda_viditelna", not _c29, "; ".join(_c29) if _c29 else "krytí hladiny ≥ %.2f, specular %.2f, drsnost %.2f (hra = pravidla)" % (_vz29["kryti_min"], _vz29["specular"], _vz29["drsnost_klid"]))

# mlýn (Míša 17. 11.: „do mlýna se nedá dostat, nemá funkční dveře“; snímky 17, 18: pytle a plot pryč): všechna křídla
# Mlyn_Dvere_* modelu mají záznam dveří (pohyb_mista.json, kořen Zajimava), výbava dvora a plot cesty modelu se vynechá,
# trasy dovnitř vedou otvory dveří a po podlaze (Mlyn_Kol_Podlaha) – průchod pruchod:zajimava_mlyn_dvur/_lavka, pruchod:dvere_mist
_c30 = []; _mu30 = _glb_uzly(K + "/hra/modely/stavby_h/mlyn.glb")
_pm30 = {e["name"]: e for e in json.load(open(K + "/hra/data/pohyb_mista.json"))["dily"] if e.get("koren") == "Zajimava"}
_dv30 = [n_ for n_, nd in _mu30.items() if n_.startswith("Mlyn_Dvere_") and "mesh" in nd]
for _n30 in _dv30:
    if _n30 not in _pm30: _c30.append("%s bez záznamu dveří" % _n30)
_zm30 = [m_ for m_ in json.load(open(K + "/pravidla/svet/zajimava_mista.json"))["mista"] if m_["id"] == "mlyn"][0]["mlyn"]
_zh30 = [m_ for m_ in json.load(open(K + "/hra/data/zajimava_mista.json"))["mista"] if m_["id"] == "mlyn"][0]
for _n30 in ("Mlyn_Dvur", "Mlyn_Cesta"):
    if _n30 not in _mu30: _c30.append("%s v mlyn.glb není (jméno uzlu?)" % _n30)
    if _n30 not in _zm30["vynechat"] or _n30 not in _zh30["mlyn"]["vynechat"]: _c30.append("%s se nevynechá" % _n30)
_tr30 = json.load(open(K + "/hra/data/pruchody_zajimava.json"))["trasy"]
for _t30 in ("zajimava_mlyn_dvur", "zajimava_mlyn_lavka"):
    if _t30 not in _tr30: _c30.append("trasa %s chybí" % _t30); continue
    _yw30 = math.cos(_zh30["yaw"]), math.sin(_zh30["yaw"]); _uvn = 0
    for _b30 in _tr30[_t30]:
        _dx, _dz = _b30[0] - _zh30["x"], _b30[1] - _zh30["z"]; _lx = _dx * _yw30[0] - _dz * _yw30[1]; _lz = _dx * _yw30[1] + _dz * _yw30[0]
        if _b30[2] is not None:
            _uvn += 1
            if not (-3.31 < _lx < 3.31 and -5.61 < _lz < 5.61): _c30.append("%s bod [%.1f, %.1f] s výškou podlahy mimo podlahu mlýna" % (_t30, _lx, _lz))
    if _uvn < 3: _c30.append("%s nevede dovnitř" % _t30)
TEST("mlyn_dvere_dvur", not _c30 and len(_dv30) >= 5, "; ".join(_c30) if _c30 else "%d křídel mlýna funkčních, bez výbavy dvora a plotu, trasy dovnitř z dvora i od lávky" % len(_dv30))

# nájezd na most bez háku (Míša 17. 11., snímek 14: pěšina za lávkou most_440_1 dělala kličku do kopce; 15. 11. most_440_3):
# stejný výpočet jako cesty.py (rovně najezd_rovne_m v ose mostu, pak oblouk do původní osy) – u mostů, které Míša hlásila,
# se cesta od původní osy neodchýlí víc než 3 m; ostatní mosty jen ve výpisu
def _husta31(o):
    o = np.array(o, float)[:, :2]; d_ = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]; s_ = np.arange(0, d_[-1] + 0.01, 0.5)
    return np.c_[np.interp(s_, d_, o[:, 0]), np.interp(s_, d_, o[:, 1])]
_HLASENE31 = {("most_440_1", "udoli_440_1"), ("most_440_3", "udoli_440_3")}   # Míša 17. 11. (snímek 14) a 15. 11. (x −27,2 z 206,2)
_c31 = []; _info31 = []; _cs31 = [c_ for c_ in json.load(open(K + "/pravidla/svet/cesty_puchart.json"))["cesty"] if not c_.get("spojka")]
for _m31 in json.load(open(K + "/pravidla/svet/voda_hra.json"))["mosty"]:
    _R, _O = float(_m31.get("najezd_rovne_m", 6.0)), float(_m31.get("najezd_oblouk_m", 26.0)); _u31 = np.array(_m31["u_bodu"], float); _ko = []
    for c_ in _cs31:
        for k_ in (0, -1):
            e_ = np.array(c_["osa"][k_][:2], float)
            if np.hypot(*(e_ - _u31)) < 15: _ko.append((float(np.hypot(*(e_ - _u31))), c_, k_))
    _ko.sort(key=lambda t_: t_[0])
    if len(_ko) < 2: continue
    (_, c1_, k1_), (_, c2_, k2_) = _ko[:2]; e1_ = np.array(c1_["osa"][k1_][:2], float); e2_ = np.array(c2_["osa"][k2_][:2], float); _mx = 0.0
    for c_, k_, e_, a_ in ((c1_, k1_, e1_, (e1_ - e2_) / np.hypot(*(e1_ - e2_))), (c2_, k2_, e2_, (e2_ - e1_) / np.hypot(*(e2_ - e1_)))):
        _nc31 = _m31.get("najezd_cesty", {}).get(c_["id"], {}); _R = float(_nc31.get("rovne_m", _m31.get("najezd_rovne_m", 6.0))); _O = float(_nc31.get("oblouk_m", _m31.get("najezd_oblouk_m", 26.0)))
        o_ = np.array(c_["osa"], float); o_ = o_[::-1] if k_ == -1 else o_
        hu_ = _husta31(o_); dl_ = np.r_[0, np.cumsum(np.hypot(*np.diff(hu_, axis=0).T))]
        if dl_[-1] < _O + 4: continue
        w_ = np.clip((_O - dl_) / (_O - _R), 0, 1); w_ = w_ * w_ * (3 - 2 * w_)
        nov_ = (e_[None, :] + a_[None, :] * dl_[:, None]) * w_[:, None] + hu_ * (1 - w_[:, None]); _od = float(np.hypot(*(nov_ - hu_).T).max())
        _info31.append("%s/%s %.1f m" % (_m31["id"], c_["id"], _od))
        if (_m31["id"], c_["id"]) in _HLASENE31 and _od > 3.0: _c31.append("%s: cesta %s za mostem uhne od osy %.1f m (hák do svahu)" % (_m31["id"], c_["id"], _od))
TEST("most_najezd_bez_haku", not _c31 and len(_info31) >= 4, "; ".join(_c31) if _c31 else "odchylka nájezdu od osy cesty: " + ", ".join(_info31))

# mapa (Míša 17. 11.: „nevím kde je důl a další zajímavé věci, hoď mi je do mapy“): každé zajímavé místo z dat má na mapě
# značku (mapa_body.json zajimava, druh nebo výchozí tvar), leží uvnitř mapy a mapa.gd značky kreslí
_c32 = []; _mb32 = json.load(open(K + "/hra/data/mapa_body.json")).get("zajimava", {}); _mi32 = json.load(open(K + "/hra/data/mapa.json"))
_tv32 = {"kriz", "kolo", "kladivka", "ohen", "kapka", "strom", "kruh"}
if not _mb32: _c32.append("mapa_body.json bez zajimava")
else:
    if _mb32.get("soubor") != "res://data/zajimava_mista.json": _c32.append("značky nečtou hra/data/zajimava_mista.json")
    for t_ in list(_mb32["druhy"].values()) + [_mb32["vychozi"]]:
        if t_ not in _tv32: _c32.append("neznámý tvar značky %s" % t_)
_zz32 = json.load(open(K + "/hra/data/zajimava_mista.json"))["mista"]
for m_ in _zz32:
    if not (_mi32["x0"] <= m_["x"] <= _mi32["x1"] and _mi32["z0"] <= m_["z"] <= _mi32["z1"]): _c32.append("%s mimo mapu" % m_["id"])
_mg32 = open(K + "/hra/scripts/mapa.gd").read()
if "_draw_zajimava(r, u)" not in _mg32 or "nacti_zajimava(cfg)" not in _mg32: _c32.append("mapa.gd značky nekreslí")
for _id32 in ("stola", "lom", "mlyn", "studanka", "uhlir"):
    if _id32 not in [m_["id"] for m_ in _zz32]: _c32.append("místo %s chybí v datech" % _id32)
TEST("mapa_zajimava", not _c32, "; ".join(_c32) if _c32 else "%d zajímavých míst na mapě se značkou a názvem (důl, lom, mlýn, studánka, milíř…)" % len(_zz32))

# znaky mapy a objevování (Míša 17. 11.: „zájmové body pod pěkným malým znakem, ale jen v pískovišti a potom v příběhu, když
# to objevím“): každé zajímavé místo má znak ze sady (popis, zdroj, kresba v nastroje/mapa_znaky.py, obrázek v
# hra/textury/ui/mapa_znaky), okruh objevení v mezích, stav objevení se ukládá a nová hra ho smaže; test hry mapa_znaky
_c33m = []; _zs33 = _mb32.get("znak_sada", {}); _zn33 = _zs33.get("znaky", {}); _ob33 = _mb32.get("objev", {})
_mz33 = open(K + "/nastroje/mapa_znaky.py").read()
for m_ in _zz32:
    j_ = _mb32.get("znaky", {}).get(m_["id"])
    if not j_: _c33m.append("%s bez znaku (mapa_body.json zajimava.znaky)" % m_["id"]); continue
    if j_ not in _zn33: _c33m.append("%s: znak %s není v znak_sada" % (m_["id"], j_))
for j_, v_ in _zn33.items():
    if not v_.get("popis") or not v_.get("zdroj"): _c33m.append("znak %s bez popisu nebo zdroje" % j_)
    if "def %s(p)" % j_ not in _mz33: _c33m.append("znak %s nemá kresbu v mapa_znaky.py" % j_)
    if not os.path.exists(K + "/hra/textury/ui/mapa_znaky/%s.png" % j_): _c33m.append("chybí obrázek hra/textury/ui/mapa_znaky/%s.png" % j_)
for f_ in ("velikost_px", "textura_px", "barvy"):
    if f_ not in _zs33: _c33m.append("znak_sada bez %s" % f_)
_ok33 = [float(_ob33.get("okruh_m", 0))] + [float(v_) for v_ in _ob33.get("okruh_druh", {}).values()]
if not _ok33 or not all(20.0 <= o_ <= 60.0 for o_ in _ok33): _c33m.append("okruh objevení mimo 20–60 m: %s" % _ok33)
if "%s" not in str(_ob33.get("oznameni", "")): _c33m.append("oznámení objevení bez názvu místa")
if not set(_ob33.get("okruh_druh", {})) <= {m_["id"] for m_ in _zz32}: _c33m.append("okruh_druh pro neznámé místo")
_pr33 = open(K + "/hra/scripts/prochazka.gd").read()
if '"objevena": mapa.objevena' not in _pr33 or 'mapa.objevena = Array(j.get("objevena"' not in _pr33 or "mapa.objevena.clear()" not in _pr33: _c33m.append("prochazka.gd neukládá / nenahrává / nemaže objevená místa")
if 'rezim() == "piskoviste" or objevena.has' not in _mg32 or "kontroluj_objevy()" not in _mg32: _c33m.append("mapa.gd: znaky nezávisí na režimu a objevení")
TEST("mapa_znaky", not _c33m, "; ".join(_c33m) if _c33m else "%d míst se znakem ze sady %d znaků (obrázky, kresba, zdroj); okruh objevení %.0f–%.0f m, stav v uložené hře" % (len(_zz32), len(_zn33), min(_ok33), max(_ok33)))

# dymník černé kuchyně celku (Míša 17. 11., snímek 12: digestoř končí v podkroví „?“; NAVOD_KRCMA_L: kouř odchází dymníkem
# v hřebeni): průduch (díly Dymnik_* v mista.json upravy_modelu) začíná na odtahu topeniště (topeni.json kuchyne, značka
# Pec_Kour), končí pod značkou kouře dymníku (*_Kour_Dymnik, vodorovně ≤ 0,8 m, pod hřebenem) a neprostupuje krovem ani krytinou
_c29 = []; _n29 = 0
for _sb, _uv in _MJ["upravy_modelu"].items():
    if not isinstance(_uv, dict): continue
    _dd = [q for c_ in _uv.get("casti", []) for q in c_.get("pridat", []) if str(q.get("jmeno", "")).startswith("Dymnik_")]
    if not _dd: continue
    _f = K + "/hra/modely/stavby_h/" + _sb
    if not os.path.exists(_f): _c29.append("%s chybí" % _sb); continue
    _site, _j29 = _glb_svet(_f); _n29 += 1
    _mod = next((m for m, cv in _MJ["modely"]["celky"].items() if isinstance(cv, dict) and cv.get("soubor", "").endswith(_sb.replace(".glb", "") + ".glb")), None)
    _ku = [v for v in _TJ["vlozit"] if v.get("kam") == "celek" and v.get("model") == _mod and _TJ["modely"].get(v["topeni"], {}).get("druh") == "kuchyne"]
    if not _ku: _c29.append("%s: bez kuchyňského topeniště" % _sb); continue
    _jt, _, _ = _gs.nacti("%s/%s/%s_LOD0.glb" % (K, _TJ["vystup"], _ku[0]["topeni"]))
    _mk = next(n.get("translation") for n in _jt["nodes"] if n.get("name") == "Pec_Kour")
    _a = math.radians(_ku[0]["yaw_deg"]); _po = _ku[0]["poloha"]
    _odt = np.array([_po[0] + math.cos(_a) * _mk[0] + math.sin(_a) * _mk[2], _po[1] + _mk[1], _po[2] - math.sin(_a) * _mk[0] + math.cos(_a) * _mk[2]])
    if np.linalg.norm(np.array(_dd[0]["od"]) - _odt) > 0.15: _c29.append("%s: průduch nezačíná na odtahu %s (od %s)" % (_sb, _odt.round(2).tolist(), _dd[0]["od"]))
    _zn = next((n.get("translation") for n in _j29["nodes"] if n.get("name", "").endswith("_Kour_Dymnik")), None)
    if _zn is None: _c29.append("%s: bez značky dymníku" % _sb)
    else:
        _e = np.array(_dd[-1]["do"])
        if math.hypot(_e[0] - _zn[0], _e[2] - _zn[2]) > 0.8 or not (_zn[1] - 2.0 < _e[1] < _zn[1]): _c29.append("%s: ústí %s není pod dymníkem %s" % (_sb, _e.tolist(), _zn))
    _K29 = np.concatenate([T for jm, mt, T in _site if ("Krov" in jm or "Strecha" in jm) and "colonly" not in jm])
    for q in _dd:
        if not any(jm == q["jmeno"] for jm, mt, T in _site): _c29.append("%s: chybí díl %s" % (_sb, q["jmeno"])); continue
        A_ = np.array(q["od"], float); B_ = np.array(q["do"], float); ax = (B_ - A_) / np.linalg.norm(B_ - A_)
        u_ = np.cross(ax, [0, 1, 0] if abs(ax[1]) < 0.9 else [1, 0, 0]); u_ /= np.linalg.norm(u_); w_ = np.cross(ax, u_)
        hs = np.array(q["prurez"]) / 2 - 0.01; L_ = np.linalg.norm(B_ - A_)
        kol = 0
        for a_, c_ in ((0, 1), (1, 2), (2, 0)):
            for t in np.linspace(0, 1, 400):
                S = _K29[:, a_] + (_K29[:, c_] - _K29[:, a_]) * t - A_
                pa = S @ ax; pu = np.abs(S @ u_); pw = np.abs(S @ w_)
                kol += int(((pa > 0.01) & (pa < L_ - 0.01) & (pu < min(hs)) & (pw < min(hs))).sum())
        if kol: _c29.append("%s %s: prostupuje krovem/krytinou (%d bodů)" % (_sb, q["jmeno"], kol))
TEST("dymnik_kuchyne", _n29 > 0 and not _c29, "; ".join(_c29) if _c29 else "%d celků: dymník z černé kuchyně od odtahu pod hřeben, bez prostupu krovem" % _n29)

# souvislost sítě cest a pěšin (plán 17. 11. B2, Havran: síť cest = graf): komponenty grafu os cesty_puchart.json
# (dotyk os, konec podle cesty_puchart.json spojky_pravidlo = spojka cesty.py, přes potok do brod_max_m, most, nástupy hradů) ≤ komponent_max; odtržené kusy s polohou
_KS = KC["cesty_sit"]; _CP = json.load(open(K + "/pravidla/svet/cesty_puchart.json")); _CC = _CP["cesty"]
def _hust_c(o, k):
    o = np.array(o, float)[:, :2]; d = np.r_[0, np.cumsum(np.hypot(*np.diff(o, axis=0).T))]; s_ = np.r_[np.arange(0, d[-1], k), d[-1]]
    return np.c_[np.interp(s_, d, o[:, 0]), np.interp(s_, d, o[:, 1])]
_HC = [_hust_c(c["osa"], float(_KS["zhusteni_m"])) for c in _CC]; _par = list(range(len(_CC)))
def _fc(a):
    while _par[a] != a: _par[a] = _par[_par[a]]; a = _par[a]
    return a
def _uc(a, b): _par[_fc(a)] = _fc(b)
_vyn = [set(v["mezi"]) for v in _CP.get("spojky_vynechat", [])]
_SPJ = _CP["spojky_pravidlo"]   # stejné pravidlo spojek jako nastroje/cesty.py (přes potok – brod – až brod_max_m, chyby.md 388)
_TOK = np.vstack([np.array(t["osa"])[:, :2] for t in json.load(open(D + "toky_hladina.json"))["toky"].values()])
for _i, _a in enumerate(_HC):
    for _j, _b in enumerate(_HC):
        if _i == _j: continue
        _dd = np.hypot(_b[:, 0][:, None] - _a[:, 0][None, :], _b[:, 1][:, None] - _a[:, 1][None, :])
        if _dd.min() <= float(_KS["dotyk_m"]): _uc(_i, _j); continue
        for _ko in (0, -1):
            if _CC[_i].get("k_mistu") and _ko == -1: continue   # pěšina k místu končí u místa (cesty.py)
            if {_CC[_i]["id"], _CC[_j]["id"]} in _vyn: continue
            _k2 = int(_dd[:, _ko].argmin()); _d2 = float(_dd[_k2, _ko])
            _mid = (_a[_ko] + _b[_k2]) / 2
            if _d2 <= float(_SPJ["max_m"]) or (_d2 <= float(_SPJ["brod_max_m"]) and float(np.hypot(*(_TOK - _mid).T).min()) < float(_SPJ["brod_tok_m"])): _uc(_i, _j)
_skup = [([m_["u_bodu"]], float(_KS["most_r_m"])) for m_ in json.load(open(K + "/pravidla/svet/voda_hra.json")).get("mosty", [])]   # konce u téhož mostu
_skup.append(([q[:2] for q in json.load(open(D + "nastupy_mostu.json"))["nastupy"]], float(_KS["hrad_r_m"])))   # nástupy hradů: skrz hrady
for _body, _r in _skup:
    _k = [i for i in range(len(_CC)) for ko in (0, -1) for q in _body if math.dist(_HC[i][ko], q) < _r]
    for _a in _k[1:]: _uc(_k[0], _a)
_g = {}
for _i in range(len(_CC)): _g.setdefault(_fc(_i), []).append(_i)
_dl = lambda i: float(np.hypot(*np.diff(np.array(_CC[i]["osa"], float)[:, :2], axis=0).T).sum())
_gs = sorted(_g.values(), key=lambda v: -sum(_dl(i) for i in v)); _Ph = np.vstack([_HC[i] for i in _gs[0]]); _odt = []
for _v in _gs[1:]:
    _P = np.vstack([_HC[i] for i in _v]); _dd = np.hypot(_P[:, 0][:, None] - _Ph[:, 0][None, :], _P[:, 1][:, None] - _Ph[:, 1][None, :]); _a = np.unravel_index(_dd.argmin(), _dd.shape)
    _odt.append("%s (%.0f m) %.0f m od sítě u [%.0f, %.0f]" % ("+".join(sorted({_CC[i]["id"] for i in _v})), sum(_dl(i) for i in _v), _dd.min(), _P[_a[0]][0], _P[_a[0]][1]))
_cg = json.load(open(D + "cesty_graf.json")); _sg = [[] for _ in _cg["uzly"]]
for _a, _b in _cg["hrany"]: _sg[_a].append(_b); _sg[_b].append(_a)
_vg = {0} if _sg else set(); _st = [0] if _sg else []
while _st:
    for _b in _sg[_st.pop()]:
        if _b not in _vg: _vg.add(_b); _st.append(_b)
for _o in _odt: print("SMYSL   odtržený kus cest:", _o)
TEST("cesty_souvislost", len(_gs) <= int(_KS["komponent_max"]) and len(_vg) == len(_cg["uzly"]),
     "komponent sítě cest %d (mez %d), hlavní %.0f m; mapa cesty_graf %d/%d uzlů souvisle; odtržené: %s" % (len(_gs), int(_KS["komponent_max"]), sum(_dl(i) for i in _gs[0]), len(_vg), len(_cg["uzly"]), "; ".join(_odt[:4]) + (" …" if len(_odt) > 4 else "")))

# sdílené textury modelů (nastroje/stromy_sdilene_textury.py – stromy, stavby_h, predmety_h; Míša 17. 11.: „uprav i pískoviště“):
# žádný glb neodkazuje (uri) na chybějící obrázek a každý odkazovaný obrázek má import Godotu (jinak model bez textury)
import glob as _g31, struct as _s31
_c31 = []; _n31 = 0; _u31 = 0
for _f in _g31.glob(K + "/hra/modely/**/*.glb", recursive=True):
    _b = open(_f, "rb").read(20); _l = _s31.unpack("<I", _b[12:16])[0]
    try: _j = json.loads(open(_f, "rb").read(20 + _l)[20:])
    except Exception: continue
    _n31 += 1
    for _im in _j.get("images", []):
        _u = _im.get("uri")
        if not _u or _u.startswith("data:"): continue
        _u31 += 1; _q = os.path.join(os.path.dirname(_f), _u)
        if not os.path.exists(_q): _c31.append("%s → %s chybí" % (os.path.relpath(_f, K + "/hra"), _u))
        elif not os.path.exists(_q + ".import"): _c31.append("%s → %s bez importu" % (os.path.relpath(_f, K + "/hra"), _u))
TEST("modely_textury_odkazy", not _c31, "; ".join(_c31[:8]) if _c31 else "%d glb, %d odkazů na sdílené textury – všechny existují a jsou importované" % (_n31, _u31))

# 394 (Míša 18. 11.): náhled pokládání v pískovišti nesmí mít kolizi ani ve vnořených tělech (postele skákaly, obrys blikal)
_c394 = []
_pg = open(K + "/hra/scripts/predmety.gd", encoding="utf-8").read()
if 'find_children("*", "CollisionObject3D", true, false)' not in _pg:
    _c394.append("predmety.gd: náhled vypíná kolizi jen u kořene – vnořená StaticBody (lůžka) zůstávají")
TEST("nahled_bez_kolize", not _c394, "; ".join(_c394) if _c394 else "náhled pokládání bez kolize i ve vnořených tělech")

# 395 (Míša 18. 11.): na nádvořích a v koutech hradů žádná tráva ani byliny
_c395 = []
_lk = json.load(open(K + "/hra/data/louka.json")); _bl = json.load(open(K + "/hra/data/byliny.json"))
for _t in ("nadvori", "nadvori_slap", "pata_zdi_uvnitr", "kout_zdi"):
    if float(_lk["tridy"].get(_t, 0.0)) > 0.0: _c395.append("louka %s=%s" % (_t, _lk["tridy"][_t]))
    for _k in ("trava", "vysoka", "kopriva", "ostruzina", "kapradi"):
        if float(_bl.get(_t, {}).get(_k, 0.0)) > 0.0: _c395.append("byliny %s.%s" % (_t, _k))
TEST("hrad_nadvori_bez_travy", not _c395, "; ".join(_c395) if _c395 else "nádvoří a kouty hradů bez trávy a bylin")

# 396 (Míša 18. 11.): kámen zdí matný a bez parallaxu (lesk, rozmazaná textura)
_zs = open(K + "/hra/shaders/zdivo.gdshader", encoding="utf-8").read()
_c396 = [] if ("uniform int kroky = 0;" in _zs and "SPECULAR = 0.3;" not in _zs) else ["zdivo.gdshader: parallax zapnutý nebo lesk kamene 0,3"]
TEST("zdivo_matne", not _c396, "; ".join(_c396) if _c396 else "zdivo matné, bez parallaxu")

# 397 (Míša 18. 11., chýše u lomu bez lůžek): každá zemljanka má rohože, dvě značky spánku pro houně (zajimava.gd) a obě leží
# v otvoru terénu (build/zajimava_teren.json diry) – houně ani rohož nesmí zakrýt terén; model houně od modeláře existuje
_zt96 = json.load(open(K + "/build/zajimava_teren.json")) if os.path.exists(K + "/build/zajimava_teren.json") else {"diry": []}
_c396 = []; _n396 = 0; _ZE96 = json.load(open(K + "/pravidla/svet/zajimava_mista.json"))["modely"]["zemljanky"]
if not os.path.exists(K + "/hra/" + _ZE96["houne"]["model"].replace("res://", "")): _c396.append("chybí model houně %s" % _ZE96["houne"]["model"])
for _m in json.load(open(D + "zajimava_mista.json"))["mista"]:
    for _q in _m["dily"]:
        if not _q.get("zemljanka"): continue
        _n396 += 1; _sp = _zmo[_q["model"]].get("spani", {})
        if sorted(_sp) != ["Zemljanka_Spani_L", "Zemljanka_Spani_P"]: _c396.append("%s %s: značky spánku %s" % (_m["id"], _q["model"], sorted(_sp))); continue
        _cs, _sn = math.cos(_q["yaw"]), math.sin(_q["yaw"])
        for _k, (_a, _y, _b) in _sp.items():
            _xs, _zs = _q["x"] + _a * _cs + _b * _sn, _q["z"] - _a * _sn + _b * _cs
            if not any(_v_poly(_xs, _zs, d_["poly"]) for d_ in _zt96["diry"]): _c396.append("%s %s: lůžko mimo otvor terénu" % (_m["id"], _k))
            elif float(ter(_xs, _zs)) - (_q["y"] + _y) > 0.05: _c396.append("%s %s: terén %.2f m nad lůžkem" % (_m["id"], _k, float(ter(_xs, _zs)) - _q["y"] - _y))
TEST("zemljanka_luzka", _n396 > 0 and not _c396, "; ".join(_c396) if _c396 else "%d zemljanek: rohože a 2 houně v otvoru terénu" % _n396)

# 398 (Míša 18. 11., podezdívka štítů „rozmazaná“): síť Zemljanka_Podezdivka bez slitých UV (Jacobián UV/3D anizotropie > 3)
_c397 = []
for _jt, _t in _ZE96["typy"].items():
    if not _t.get("podezdivka_stitu"): continue
    _gp = K + "/hra/modely/stavby_h/%s.glb" % _jt
    if not os.path.exists(_gp): _c397.append("%s: chybí model" % _jt); continue
    import glb_sit as _gs97; _r = _gs97.nacti(_gp); _jj, _bb = _r[0], _r[1]; _an = []
    for _nd in _jj["nodes"]:
        if _nd.get("name") != "Zemljanka_Podezdivka" or "mesh" not in _nd: continue
        for _pr in _jj["meshes"][_nd["mesh"]]["primitives"]:
            _X = _gs97.cti(_jj, _bb, _pr["attributes"]["POSITION"]).astype(float); _U = _gs97.cti(_jj, _bb, _pr["attributes"]["TEXCOORD_0"]).astype(float)
            _I = _gs97.cti(_jj, _bb, _pr["indices"]).reshape(-1, 3); _e1 = _X[_I[:, 1]] - _X[_I[:, 0]]; _e2 = _X[_I[:, 2]] - _X[_I[:, 0]]
            _nr = np.cross(_e1, _e2); _ar = np.linalg.norm(_nr, axis=1); _ok = _ar > 1e-6; _e1, _e2, _nr = _e1[_ok], _e2[_ok], _nr[_ok] / _ar[_ok, None]
            _ex = _e1 / np.linalg.norm(_e1, axis=1, keepdims=True); _ey = np.cross(_nr, _ex)
            _P2 = np.stack([np.c_[(_e1 * _ex).sum(1), (_e1 * _ey).sum(1)], np.c_[(_e2 * _ex).sum(1), (_e2 * _ey).sum(1)]], 1)
            _U2 = np.stack([(_U[_I[:, 1]] - _U[_I[:, 0]])[_ok], (_U[_I[:, 2]] - _U[_I[:, 0]])[_ok]], 1)
            _sv = np.linalg.svd(np.linalg.solve(_P2, _U2), compute_uv=False); _an.append(_sv[:, 0] / np.maximum(_sv[:, 1], 1e-9))
    if not _an: _c397.append("%s: bez sítě Zemljanka_Podezdivka" % _jt); continue
    _f = float((np.concatenate(_an) > 3).mean())
    if _f > 0.05: _c397.append("%s: %.0f %% ploch podezdívky se slitým UV" % (_jt, _f * 100))
TEST("podezdivka_uv", not _c397, "; ".join(_c397) if _c397 else "podezdívka štítů: UV bez pruhů (anizotropie > 3 pod 5 %)")

# 399 (Míša 18. 11., krumpáč svisle u skály): dlouhé nářadí míst (katalog kat naradi, výška > 0,8 m) neleží ani nestojí svisle
# volně – je opřené (naklon 10–35°) patou na terénu
_c398 = []; _n398 = 0; _KP = json.load(open(K + "/hra/modely/predmety_h.json"))
for _m in json.load(open(D + "zajimava_mista.json"))["mista"]:
    for _q in _m["dily"]:
        _kp = _KP.get(_q.get("predmet", ""), {})
        if _kp.get("kat") != "naradi" or float(_kp.get("rozmer", [0, 0, 0])[1]) < 0.8: continue
        _n398 += 1; _nk = abs(math.degrees(float(_q.get("naklon", 0.0))))
        if not 10.0 <= _nk <= 35.0: _c398.append("%s %s: stojí svisle (náklon %.0f°)" % (_m["id"], _q["predmet"], _nk))
        elif abs(float(ter(_q["x"], _q["z"])) - _q["y"]) > 0.1: _c398.append("%s %s: pata %.2f m od terénu" % (_m["id"], _q["predmet"], _q["y"] - float(ter(_q["x"], _q["z"]))))
TEST("naradi_oprene", not _c398, "; ".join(_c398) if _c398 else "%d kusů dlouhého nářadí opřeno patou na zemi" % _n398)

# 400 (Míša 18. 11., nádvoří A: hrbol u věžičky – „srovnat do roviny s okolním dvorem“) a 402 (Míša 19. 11., SZ kout nádvoří A
# u paty hradby pod ochozem – svah k nároží): v plošinách A_nadvori_jih a A_nadvori_sz (1 m od kraje) převýšení terénu nejvýš
# kontroly.json nadvori_prevyseni_m
_c399 = []; _pl399 = {_q["id"]: _q for _q in json.load(open(K + "/pravidla/svet/hrad_puchart.json"))["teren"]["plosiny"]}
for _id in ("A_nadvori_jih", "A_nadvori_sz"):
    _q = _pl399.get(_id)
    if _q is None: _c399.append("plošina %s chybí" % _id); continue
    _pg = np.array(_q["polygon"], float); _xx, _zz = np.meshgrid(np.arange(_pg[:, 0].min() + 1, _pg[:, 0].max() - 0.99, 0.5), np.arange(_pg[:, 1].min() + 1, _pg[:, 1].max() - 0.99, 0.5))
    _P2 = np.c_[_xx.ravel(), _zz.ravel()]; _dk = np.full(len(_P2), 1e9)   # body uvnitř polygonu aspoň 1 m od kraje (SZ kout je šikmý)
    for _a, _b in zip(_pg, np.roll(_pg, -1, 0)):
        _t = np.clip(((_P2 - _a) @ (_b - _a)) / max(float((_b - _a) @ (_b - _a)), 1e-9), 0, 1); _dk = np.minimum(_dk, np.linalg.norm(_P2 - (_a + _t[:, None] * (_b - _a)), axis=1))
    _in = _Path(_pg).contains_points(_P2) & (_dk >= 1.0)
    _h = ter(_xx.ravel()[_in], _zz.ravel()[_in]); _dv = float(_h.max() - _h.min())
    if _dv > KC.get("nadvori_prevyseni_m", 0.25): _c399.append("%s: převýšení %.2f m (%.2f–%.2f)" % (_id, _dv, _h.min(), _h.max()))
TEST("nadvori_A_rovne", not _c399, "; ".join(_c399) if _c399 else "nádvoří A u věžičky a v SZ koutě srovnané (převýšení pod %.2f m)" % KC.get("nadvori_prevyseni_m", 0.25))

# 401 (Míša 19. 11.): louče osvětlují prostor místnosti
_sv401 = json.load(open(K + "/hra/data/prostredi.json"))["atmosfera"]["svitidla"]
TEST("svitidla_sila", float(_sv401["energie_nasobek"]) >= 2.5 and float(_sv401["dosah_nasobek"]) >= 2.0, "svítidla energie %s, dosah %s" % (_sv401["energie_nasobek"], _sv401["dosah_nasobek"]))

# 403 (Míša 19. 11., docs/screens/misa_19_11_staj_misto.jpg: stáj z Havrana u J hradby nádvoří A pod ochozem): stáj postavená
# (hra/data/staj_kontrola.json z blender/puchart_hrad.py staj), zády na vnitřním líci hradby, podlaha na terénu (nic nevisí),
# střecha pod ochozem (koruna − 1,5 m), půdorys mimo budovy a věže (BUDOVY_K) a mimo dveře přízemí věžičky
_c403 = []; _sk = json.load(open(D + "staj_kontrola.json")).get("staje", []) if os.path.exists(D + "staj_kontrola.json") else []
_HA = json.load(open(K + "/pravidla/svet/hrad_puchart.json"))["A"]
if not _sk: _c403.append("stáj nádvoří A chybí (A.staj)")
_bk = json.load(open(D + "ochozy_kontrola.json")).get("budovy", []) if os.path.exists(D + "ochozy_kontrola.json") else []
for _st in _sk:
    _r = np.array(_st["rohy"], float)   # [zeď z0, čelo z0, čelo z1, zeď z1]
    _j = np.array(_HA["jadro"], float); _a5, _b5 = _j[_HA["staj"]["usek"]], _j[(_HA["staj"]["usek"] + 1) % len(_j)]
    _nz = np.array([-(_b5 - _a5)[1], (_b5 - _a5)[0]]) / np.linalg.norm(_b5 - _a5)
    for _q in (_r[0], _r[3]):
        _dz = abs(float((_q - _a5) @ _nz)) - _HA["kurtina_tloustka"] / 2
        if abs(_dz) > 0.1: _c403.append("%s: záda %.2f m od líce hradby" % (_st["id"], _dz))
    for _q in _r:
        _dy = _st["podlaha_y"] - float(ter(_q[0], _q[1]))
        if _dy > 0.3 or _dy < -0.1: _c403.append("%s: podlaha %+.2f m nad terénem v (%.1f, %.1f)" % (_st["id"], _dy, _q[0], _q[1]))
    if _st["vyska_u_zdi_y"] > _HA["koruna_y"] - 1.5: _c403.append("%s: střecha u zdi %.2f nad koruna − 1,5 (ochoz)" % (_st["id"], _st["vyska_u_zdi_y"]))
    _uu, _vv = np.meshgrid(np.linspace(0.05, 0.95, 10), np.linspace(0.05, 0.95, 10)); _uu = _uu.ravel(); _vv = _vv.ravel()
    _pts = _r[0] + _uu[:, None] * (_r[1] - _r[0]) + _vv[:, None] * (_r[3] - _r[0])
    for _b in _bk:
        _c = np.array(_b["c"]); _dd = np.array(_b["d"]); _ss = np.array(_b["s"])
        _vb = (np.abs((_pts - _c) @ _dd) < _b["pul_d"]) & (np.abs((_pts - _c) @ _ss) < _b["pul_s"])
        if _vb.any(): _c403.append("%s: zasahuje do %s" % (_st["id"], _b["jm"]))
    _vz = _HA["vezicka"]; _rc = _j[_vz["roh"]]; _cen = _j.mean(0)   # dveře přízemí věžičky: před nimi 2,5 m volno
    if _vz.get("prizemi"):
        _dvr = _rc + (_cen - _rc) / np.linalg.norm(_cen - _rc) * (_vz["rozmer"] / 2 + 1.0)
        if (np.linalg.norm(_pts - _dvr, axis=1) < 2.0).any(): _c403.append("%s: u dveří přízemí věžičky" % _st["id"])
TEST("staj_A", not _c403, "; ".join(_c403[:5]) if _c403 else "stáj nádvoří A: %d, zády k hradbě, podlaha na terénu, mimo budovy" % len(_sk))
# 404 (Míša 19. 11., docs/screens/misa_19_11_voda_1/2.jpg: „voda je bílá, nic moc, skoro vyschla“ – mělký potok jako bílý štěrk):
# hladina kryje i na mělčině (kryti_min), tělo vody tmavé (jas melka), pěna za kameny tlumená a shader ji čte z dat
_c404 = []; _vz404 = json.load(open(D + "voda_hra.json"))["vzhled_13_11"]; _KV = KC.get("voda_vzhled", {})
if float(_vz404.get("kryti_min", 0)) < _KV.get("kryti_min_min", 0.65): _c404.append("kryti_min %.2f < %.2f" % (_vz404.get("kryti_min", 0), _KV.get("kryti_min_min", 0.65)))
_jm = 0.2126 * _vz404["melka"][0] + 0.7152 * _vz404["melka"][1] + 0.0722 * _vz404["melka"][2]
if _jm > _KV.get("melka_jas_max", 0.28): _c404.append("melka jas %.2f > %.2f" % (_jm, _KV.get("melka_jas_max", 0.28)))
if float(_vz404.get("pena_kamen_sila", 1.0)) > _KV.get("pena_kamen_max", 0.6): _c404.append("pena_kamen_sila %.2f" % _vz404.get("pena_kamen_sila", 1.0))
if "pena_kamen_sila" not in open(K + "/hra/shaders/voda.gdshader", encoding="utf-8").read() or '"pena_kamen_sila"' not in open(K + "/hra/scripts/hlavni.gd", encoding="utf-8").read(): _c404.append("voda.gdshader/hlavni.gd nečte pena_kamen_sila")
TEST("voda_neni_bila", not _c404, "; ".join(_c404) if _c404 else "voda: krytí mělčiny %.2f, jas těla %.2f, pěna za kameny %.2f" % (_vz404["kryti_min"], _jm, _vz404.get("pena_kamen_sila", 1.0)))
# 405 (Míša 19. 11., „kámen jako tapeta“): zdivo klidné – drobný kámen, nízký kontrast a sytost, anizotropní filtrování
_c405 = []; _zs405 = open(K + "/hra/shaders/zdivo.gdshader", encoding="utf-8").read()
for _q in ("uniform float kamen_m = 3.2;", "uniform float kontrast = 0.55;", "uniform float sytost = 0.3;", "kamen_a : source_color, filter_linear_mipmap_anisotropic"):
    if _q not in _zs405: _c405.append("zdivo.gdshader: chybí " + _q)
TEST("zdivo_klidne", not _c405, "; ".join(_c405) if _c405 else "zdivo klidné: kámen 3,2 m, kontrast 0,55, sytost 0,3, anizotropie")

# 406 (Míša 19. 11.: v podlaze stáje hradu A prorůstají trsy trávy): půdorys stáje (staj_kontrola.json rohy) bez porostu – každá
# buňka stanovišť, které se dotkne, má nulovou trávu louky i bylin (trava, vysoka), a žádný pruh u paty (pata_pas.json, i s přesahem
# trsů okraj_budov_m) do půdorysu nezasahuje (stavby_vegetace.py: půdorysy = stavba v každé dotčené buňce, pruh nesmí do jiné budovy)
from shapely.geometry import Polygon as _Pg406
_c406 = []; _SJ406 = json.load(open(D + "stanoviste.json")); _st406 = np.array(Image.open(D + "stanoviste.png")); _st406 = _st406[..., 0] if _st406.ndim == 3 else _st406
_LT406 = json.load(open(D + "louka.json"))["tridy"]; _BT406 = json.load(open(D + "byliny.json"))["tridy"]
_ob406 = json.load(open(K + "/pravidla/svet/pata_zdi.json"))["pas_u_paty"].get("okraj_budov_m", 0.0)
_pp406 = [q for v in json.load(open(D + "pata_pas.json"))["bunky"].values() for q in v]
_ks406, _x406, _z406 = _SJ406["krok_m"], _SJ406["x0_hra"], _SJ406["z0_hra"]
for _st in _sk:
    _P = _Pg406(_st["rohy"]); _bx = _P.bounds
    for _r in range(int((_bx[1] - _z406) // _ks406), int((_bx[3] - _z406) // _ks406) + 1):
        for _c in range(int((_bx[0] - _x406) // _ks406), int((_bx[2] - _x406) // _ks406) + 1):
            _cl = _Pg406([(_x406 + _c * _ks406, _z406 + _r * _ks406), (_x406 + (_c + 1) * _ks406, _z406 + _r * _ks406), (_x406 + (_c + 1) * _ks406, _z406 + (_r + 1) * _ks406), (_x406 + _c * _ks406, _z406 + (_r + 1) * _ks406)])
            if _cl.intersection(_P).area < 0.01: continue
            _tr = _SJ406["tridy"][int(_st406[_r, _c])]; _bt = _BT406.get(_tr, {})
            if float(_LT406.get(_tr) or 0) > 0 or float(_bt.get("trava", 0)) + float(_bt.get("vysoka", 0)) > 0:
                _c406.append("%s: buňka (%.0f, %.0f) třída %s s trávou" % (_st["id"], _x406 + _c * _ks406, _z406 + _r * _ks406, _tr))
    for _q in _pp406:
        _a, _b, _n = np.array(_q[0:2]), np.array(_q[2:4]), np.array(_q[4:6]); _w = _q[6]
        if _Pg406([tuple(_a), tuple(_b), tuple(_b + _n * (_w + _ob406)), tuple(_a + _n * (_w + _ob406))]).buffer(0.0).intersection(_P).area > 0.01:
            _c406.append("%s: pruh u paty %s (%.1f, %.1f) do půdorysu" % (_st["id"], _q[7], _q[0], _q[1]))
TEST("staj_bez_porostu", bool(_sk) and not _c406, "; ".join(_c406[:5]) if _c406 else "stáj bez porostu: %d stájí, buňky bez trávy, žádný pruh u paty do půdorysu" % len(_sk))
chyb = [k for k, v in vysl.items() if not v["ok"] and v["vaha"] == "chyba"]
json.dump({"popis": "nastroje/test_smyslu.py", "testy": vysl, "chyb": chyb}, open(K + "/build/test_smyslu.json", "w"), ensure_ascii=False, indent=1)
print("TEST_SMYSLU", "OK" if not chyb else "CHYBA %s" % chyb)
sys.exit(1 if chyb else 0)

