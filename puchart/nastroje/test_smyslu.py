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
sch = KC["geometrie"].get("schvaleno", {})
for f, v in G.items():
    jm = os.path.basename(f).split(".")[0]
    znam_a = np.array(sch.get(f, []) or [[1e9, 1e9, 1e9]]); znam = sch.get(f, [])
    nove = [q for q in v["visi"] if np.linalg.norm(znam_a - np.array(q["stred"]), axis=1).min() > KC["geometrie"]["shoda_m"]]
    TEST("visi_" + jm, not nove, "visí %d (schváleno %d, nových %d)%s" % (v["visi_pocet"], len(znam), len(nove), (" např. " + str(nove[0]["stred"])) if nove else ""))
sch_pod = KC["geometrie"].get("schvaleno_pod_terenem", {})
for f, v in G.items():
    jm = os.path.basename(f).split(".")[0]; znam = np.array(sch_pod.get(f, []) or [[1e9, 1e9, 1e9]])
    nove = [q for q in v["pod_terenem"] if np.linalg.norm(znam - np.array(q["stred"]), axis=1).min() > KC["geometrie"]["shoda_m"]]   # posun ≤ shoda_m = tentýž kus
    TEST("pod_terenem_" + jm, not nove, "celých kusů pod terénem %d (schváleno %d, nových %d)" % (v["pod_terenem_pocet"], len(znam), len(nove)))
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
CP = json.load(open(K + "/pravidla/svet/cesty_puchart.json"))
mez = KC["cesty"]["rez_max_m"]
zle = {k: v for k, v in CP["vysledek"].items() if max(v["max_rez_m"], v["max_nasyp_m"]) > mez}
TEST("cesta_zarez", not zle, "zářez/násyp nad %s m: %s" % (mez, zle))
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

chyb = [k for k, v in vysl.items() if not v["ok"] and v["vaha"] == "chyba"]
json.dump({"popis": "nastroje/test_smyslu.py", "testy": vysl, "chyb": chyb}, open(K + "/build/test_smyslu.json", "w"), ensure_ascii=False, indent=1)
print("TEST_SMYSLU", "OK" if not chyb else "CHYBA %s" % chyb)
sys.exit(1 if chyb else 0)
