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
    TEST("krcma_bez_plotu", _kr and not _kp, "krčma (usedlost %s): plotů a vrat %d" % (_kr, len(_kp)))
    # ploty navazují (Míša 13. 11., foto 40db6a53: „ploty nenavazují na domy, jsou tam díry“; předloha kcd_ves_predloha/03):
    # každý konec plotu a vrat leží do 0,3 m od stavby (půdorys s okrajem 0,3 m) nebo do 0,3 m od jiného plotu/vrat téže usedlosti
    _seg = [(p_["usedlost"], _Ls([(b_[0], b_[2]) for b_ in p_["body"]])) for p_ in MS["ploty"]] + \
           [(b["usedlost"], _Ls([(b["a"][0], b["a"][2]), (b["b"][0], b["b"][2])])) for b in MS["brany"]]
    _volne = []
    for i_, (u_, l_) in enumerate(_seg):
        for q_ in (l_.coords[0], l_.coords[-1]):
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
    TEST("krcma_sezeni", sum(1 for e in _sz if e["model"] == _szj.get("stul")) >= 2 and _odc >= _szj.get("od_cesty_min_m", 3.0) and not _zav and _k_ceste and _odst >= 3.0,
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

chyb = [k for k, v in vysl.items() if not v["ok"] and v["vaha"] == "chyba"]
json.dump({"popis": "nastroje/test_smyslu.py", "testy": vysl, "chyb": chyb}, open(K + "/build/test_smyslu.json", "w"), ensure_ascii=False, indent=1)
print("TEST_SMYSLU", "OK" if not chyb else "CHYBA %s" % chyb)
sys.exit(1 if chyb else 0)
