"""Modely zajímavých míst (pravidla/svet/zajimava_mista.json modely; Míša 15. 11.) – modelový filtr CLAUDE.md:
1) lesní díly od modeláře (build/zdroj_modelar/les) přebalené do hra/modely/les se sdílenými texturami (glb_prebal),
2) zemljanky: chýše do tvaru A z Havrana (domy.glb ChyseKura/ChysePrkna) bez podlahy a pryčen, s jámou, dvěma stupni,
   rohožemi s houněmi a otevřenými dveřmi (hra/modely/stavby_h/zemljanka_*.glb, kolize OMI jako domy),
3) průzkumná štola: z dolu z Disku jen vstup a první úsek chodby s čelbou, textury zmenšené (hra/modely/les/stola.glb),
4) brť: dlužka s česnem pro brtní strom (hra/modely/les/brt.glb),
5) kameny lomu z modelů Havrana (modely/nove balvan_droba_1, kamen_droba_1) do hra/modely/les.
Výstup i hra/data/zajimava_modely.json (rozměry, značky – čte nastroje/zajimava_mista.py).
  python3 nastroje/zajimava_modely.py <K> [--stola-zdroj <rozbalená složka>]"""
import sys, os, json, math, shutil, subprocess, zipfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_sit import nacti, cti, matice
from glb_prebal import Prebal, kvadr, spoj, posun

K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
Z = json.load(open(K + "/pravidla/svet/zajimava_mista.json")); MO = Z["modely"]
OUT = K + "/" + MO["les"]["vystup"]; TEX = OUT + "/textury"; os.makedirs(TEX, exist_ok=True)
INFO = {"popis": "rozměry a značky modelů zajímavých míst (nastroje/zajimava_modely.py)", "modely": {}}


def bbox(path, bez_kolizi=True):
    j, b, _ = nacti(path); P = []
    def walk(i, M):
        n = j["nodes"][i]; M = M @ matice(n)
        if "mesh" in n and not (bez_kolizi and ("colonly" in n.get("name", "") or "Kol" in n.get("name", ""))):
            for p in j["meshes"][n["mesh"]]["primitives"]:
                X = cti(j, b, p["attributes"]["POSITION"]); P.append((np.c_[X, np.ones(len(X))] @ M.T)[:, :3])
        for c in n.get("children", []): walk(c, M)
    for r in j["scenes"][j.get("scene", 0)]["nodes"]: walk(r, np.eye(4))
    if not P: return None
    P = np.vstack(P); return [np.round(P.min(0), 3).tolist(), np.round(P.max(0), 3).tolist()]


def znacky(path):
    j, _, _ = nacti(path); out = {}
    def walk(i, M):
        n = j["nodes"][i]; M = M @ matice(n)
        if "mesh" not in n and not n.get("children") and "Collision" not in n.get("name", ""): out[n.get("name", "")] = np.round(M[:3, 3], 3).tolist()
        for c in n.get("children", []): walk(c, M)
    for r in j["scenes"][j.get("scene", 0)]["nodes"]: walk(r, np.eye(4))
    return out


# ------------------------------------------------------------------ 1) lesní díly
ZL = K + "/" + MO["les"]["zdroj"]
for jm in MO["les"]["soubory"]:
    for suf in ("", "_lod1"):
        src = "%s/%s%s.glb" % (ZL, jm, suf); dst = "%s/%s%s.glb" % (OUT, jm, suf)
        if not os.path.exists(src): print("ZAJIMAVA_CHYBI", src); continue
        pb = Prebal(src).vyber(vynechat_fn=(lambda n: "colonly" in n) if suf else None)   # LOD1 bez kolizí
        n, vel, tri = pb.uloz(dst, TEX)
        if not suf: INFO["modely"]["les/" + jm] = {"aabb": bbox(dst), "znacky": znacky(dst), "troj": tri}
        else: INFO["modely"]["les/" + jm]["troj_lod1"] = tri
        print("ZAJIMAVA %s%s uzlů %d, %.2f MB, troj %d" % (jm, suf, n, vel / 1e6, tri))

# ------------------------------------------------------------------ 2) zemljanky
ZE = MO["zemljanky"]


def jama_steny(t, kp):
    """hliněné stěny jámy (vnitřní líc), podlaha, stupně a obklad z kůlů; vše v souřadnicích chýše (+z dveře)"""
    x0, x1, z0, z1 = t["jama"]; yf = t["podlaha_y"]; yt = 0.02
    n = t.get("schody_pocet", ZE["schody"]["pocet"]); h = (t["prah_y"] - yf) / (n + 1); dz = ZE["schody"]["hloubka_m"]; sw = ZE["schody"]["sirka_m"] / 2
    zs = z1 - n * dz   # začátek stupňů (strana do jámy)
    hl = []; dr = []; kol = []
    # podlaha
    hl.append(kvadr(x0, x1, yf - 0.25, yf, z0, zs))
    kol.append(kvadr(x0, x1, yf - 0.3, yf, z0, zs)[0])
    # stupně (hlína s dřevěnou hranou)
    for k in range(n):
        ytop = t["prah_y"] - (k + 1) * h; za = z1 - (k + 1) * dz; zb = z1 - k * dz
        hl.append(kvadr(-sw, sw, yf - 0.25, ytop, za, zb))
        kol.append(kvadr(-sw, sw, yf - 0.3, ytop, za, zb)[0])
        dr.append(posun(kvadr(-sw, sw, -0.045, 0.045, -0.045, 0.045), (0, ytop - 0.04, za + 0.05)))   # kulatina na hraně stupně
    # stěny – tenké desky obrácené líc dovnitř (kvádr 0,15 m za lícem)
    T = 0.15
    hl.append(kvadr(x0 - T, x0, yf, yt, z0 - T, z1))
    hl.append(kvadr(x1, x1 + T, yf, yt, z0 - T, z1))
    hl.append(kvadr(x0 - T, x1 + T, yf, yt, z0 - T, z0))
    hl.append(kvadr(x0 - T, -sw, yf, yt, z1, z1 + T)); hl.append(kvadr(sw, x1 + T, yf, yt, z1, z1 + T))
    for k in range(n):   # boky stupňů
        ytop = t["prah_y"] - (k + 1) * h; za = z1 - (k + 1) * dz
        hl.append(kvadr(-sw - T, -sw, yf, yt, za, z1)); hl.append(kvadr(sw, sw + T, yf, yt, za, z1))
    # obklad z kůlů podél stěn (líc stěny, polovina kůlu ve stěně)
    r = kp["prumer_m"] / 2; ys = (yf, yt + kp["nad_teren_m"])
    def kul(x, z):
        return kvadr(x - r, x + r, ys[0], ys[1], z - r, z + r, uv_m=0.5)
    for z in np.arange(z0 + 0.15, zs + 0.01, kp["rozestup_m"]):
        dr.append(kul(x0, z)); dr.append(kul(x1, z))
    for x in np.arange(x0 + 0.16, x1, kp["rozestup_m"]): dr.append(kul(x, z0))
    # zem chýše pod střechou kolem jámy (Míša 16. 11.: tráva v zemljance) – horní plocha ve výšce hrany stěn, s kolizí
    if t.get("pod_strechou"):
        a0, a1, b0, b1 = t["pod_strechou"]; tz_ = ZE["zem"]["tl_m"]
        for q in ((a0, x0 - T, b0, b1), (x1 + T, a1, b0, b1), (x0 - T, x1 + T, b0, z0 - T), (x0 - T, -sw, z1 + T, b1), (sw, x1 + T, z1 + T, b1), (-sw, sw, z1, b1)):
            if q[1] - q[0] < 0.01 or q[3] - q[2] < 0.01: continue
            hl.append(kvadr(q[0], q[1], yt - tz_, yt, q[2], q[3], uv_m=1.0)); kol.append(kvadr(q[0], q[1], yt - tz_ - 0.2, yt, q[2], q[3])[0])
    return spoj(*hl), spoj(*dr), kol, zs


def podezdivka_stitu(pb, t):
    """Štíty až k zemi (Míša 17. 11., snímek 16: „stěna nesahá až na zem“; „ať jim tam fouká“): u chýše na zvýšené podlaze
    (ChysePrkna – štíty od 0,41 m, pod nimi byla podlaha, která se v zemljance vypouští) pokračuje kamenná zídka na sucho
    z boků i pod oběma štíty. Kameny = kopie kamenů boční zídky vzoru (oblast zdroj [x0, x1, y_max, z0, z1]) otočené o ±90°
    pod štít (osa z_stit); pod dveřmi tvoří kamenný práh ve výšce podlahy chýše, před dveřmi kamenný stupeň (schod)."""
    P_ = t["podezdivka_stitu"]; j, b = pb.j, pb.b
    vn = pb.najdi(P_["uzel"]); M = matice(j["nodes"][vn]); R3 = M[:3, :3]
    x0, x1, ym, z0, z1 = P_["zdroj"]; xc = P_["osa_zidky_x"]; zg = P_["z_stit"]
    casti = []
    for pr in j["meshes"][j["nodes"][vn]["mesh"]]["primitives"]:
        mn = j["materials"][pr["material"]]["name"] if "material" in pr else ""
        if mn not in P_["materialy"]: continue
        X = cti(j, b, pr["attributes"]["POSITION"]).astype(float); X = X @ R3.T + M[:3, 3]
        Nn = cti(j, b, pr["attributes"]["NORMAL"]).astype(float) @ R3.T
        UV = cti(j, b, pr["attributes"]["TEXCOORD_0"]).astype(float)
        I = cti(j, b, pr["indices"]).reshape(-1, 3)
        V = X[I]; ok = (V[..., 0].min(1) >= x0) & (V[..., 0].max(1) <= x1) & (V[..., 1].max(1) <= ym) & (V.mean(1)[:, 2] >= z0) & (V.mean(1)[:, 2] <= z1)
        if not ok.any(): continue
        I = I[ok]; u, inv = np.unique(I, return_inverse=True); I2 = inv.reshape(-1, 3)
        Xs, Ns, UVs = X[u], Nn[u], UV[u]
        # Míša 18. 11. (misa_18_11_lom_chyse_2.jpg: „struktura na prd“): kameny vzoru mají UV promítnuté z boku zídky – horní
        # plochy kamenů (normála nahoru) jsou v UV slité do pruhů (anizotropie > 3 u 97 %). V boční zídce je kryje stěna, pod
        # štítem jsou vidět → plochy s |n.y| > uv_shora_ny dostanou vlastní vrcholy a UV promítnuté shora v měřítku zídky (uv_na_m).
        V3 = Xs[I2]; nrm = np.cross(V3[:, 1] - V3[:, 0], V3[:, 2] - V3[:, 0]); nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        hore = np.abs(nrm[:, 1]) > P_["uv_shora_ny"]
        It = I2[hore].ravel(); I2 = np.r_[I2[~hore].ravel(), len(Xs) + np.arange(len(It))].reshape(-1, 3)
        UVt = np.c_[Xs[It, 2], Xs[It, 0]] * P_["uv_na_m"]   # shora: u podél zídky, v napříč (jako bok)
        Xs = np.r_[Xs, Xs[It]]; Ns = np.r_[Ns, Ns[It]]; UVs = np.r_[UVs, UVt]
        for sm in (1, -1):   # přední štít (+z): x' = −z, z' = (x − xc) + zg (otočení +90°); zadní: x' = z, z' = −(x − xc) − zg
            Xn = np.c_[-sm * Xs[:, 2], Xs[:, 1], sm * ((Xs[:, 0] - xc) + zg)]
            Nr = np.c_[-sm * Ns[:, 2], Ns[:, 1], sm * Ns[:, 0]]
            casti.append((pb.material(mn), Xn, Nr, UVs, I2.ravel()))
    tl = P_["tl_m"]; ya = t["prah_y"]; S = P_["stupen"]
    kol = [kvadr(-xc + tl / 2, xc - tl / 2, -0.2, ya, sm * zg - tl / 2, sm * zg + tl / 2)[0] for sm in (1, -1)]
    zs0 = zg + tl / 2; ys = (ya + 0.02) / 2   # stupeň před dveřmi v polovině výšky prahu (pod hrac.json schod_m)
    st = kvadr(-S["sirka_m"] / 2, S["sirka_m"] / 2, -0.1, ys, zs0, zs0 + S["hloubka_m"], uv_m=1.0 / P_["uv_na_m"])   # měřítko kamenů zídky (dřív 0,5 m → 3× drobnější)
    casti.append((pb.material(P_["materialy"][0]),) + st); kol.append(kvadr(-S["sirka_m"] / 2, S["sirka_m"] / 2, -0.2, ys, zs0, zs0 + S["hloubka_m"])[0])
    pb.pridej_sit("Zemljanka_Podezdivka", casti, kolize=kol)


VZ = K + "/" + ZE["vzor"]
for jm_t, t in ZE["typy"].items():
    if not os.path.exists(VZ): print("ZAJIMAVA_CHYBI", VZ); break
    pb = Prebal(VZ).vyber([t["koren"]], vynechat=[t["koren"] + v for v in ZE["vynechat"]])
    kor = pb.uzly[pb.koreny[0]]; kor["name"] = "Zemljanka"
    # dveře otevřené ven: otočení kolem svislé osy v pantu (levá zárubeň)
    # počátek uzlu dveří = pant (síť křídla x 0…0,81 od počátku, uzel v (−0,41; práh; 2,28)) → jen otočit, poloha zůstává;
    # dřív se poloha přepsala, jako by síť byla v souřadnicích chýše – křídlo stálo 1,9 m vedle chýše (Míša 17. 11., snímek 15)
    dv = pb.uzel(t["koren"] + "_Dvere")
    if dv:
        a = math.radians(ZE["dvere_otevrit_st"])
        dv["rotation"] = [0, math.sin(a / 2), 0, math.cos(a / 2)]
    hl, dr, kol, zs = jama_steny(t, ZE["kuly"])
    mh = pb.material(t["hlina_mat"]); md = pb.material(t["drevo_mat"]); mr = pb.material(t["rohoz_mat"])
    pb.pridej_sit("Zemljanka_Jama", [(mh,) + hl, (md,) + dr], kolize=kol)
    if t.get("podezdivka_stitu"): podezdivka_stitu(pb, t)
    if t.get("podmazavka"):   # spodek stěn zevnitř podmazaný hlínou – bez průduchů u země (Míša 17. 11.)
        pb.pridej_sit("Zemljanka_Podmazavka", [(mh,) + spoj(*[kvadr(*q, uv_m=0.8) for q in t["podmazavka"]])])
    # rohože a houně vlevo a vpravo (pevný díl), značky spánku
    R = ZE["rohoz"]; x0, x1 = t["jama"][0], t["jama"][1]; yf = t["podlaha_y"]
    ro = []; zn = {}
    for strana, xs in (("L", x0 + R["od_steny_m"] + R["sirka_m"] / 2), ("P", x1 - R["od_steny_m"] - R["sirka_m"] / 2)):
        za = R["z_konec"]; zb = za + R["delka_m"]
        ro.append(kvadr(xs - R["sirka_m"] / 2, xs + R["sirka_m"] / 2, yf, yf + R["tl_m"], za, zb, uv_m=0.7))
        zn["Zemljanka_Spani_" + strana] = [xs, yf + R["tl_m"], (za + zb) / 2]
    pb.pridej_sit("Zemljanka_Rohoze", [(mr,) + spoj(*ro)])   # houně od modeláře (Luzka_1400) osazuje hra na značky spánku
    for k_, p_ in zn.items():   # prázdné uzly = značky (funkce.gd spánek)
        pb.uzly.append({"name": k_, "translation": p_}); kor.setdefault("children", []).append(len(pb.uzly) - 1)
    dst = "%s/%s/%s.glb" % (K, ZE["vystup"], jm_t)
    n, vel, tri = pb.uloz(dst, "%s/%s/textury_zemljanka" % (K, ZE["vystup"]))
    INFO["modely"][jm_t] = {"aabb": bbox(dst), "jama": t["jama"], "pod_strechou": t.get("pod_strechou"), "podlaha_y": yf, "prah_y": t["prah_y"], "schody_od_z": zs,
                            "spani": zn, "bedna": [0.0, yf, t["jama"][2] + 0.31], "dvere_z": t["dvere_z"], "troj": tri,
                            "schody_pocet": t.get("schody_pocet", ZE["schody"]["pocet"])}
    print("ZAJIMAVA %s uzlů %d, %.2f MB, troj %d" % (jm_t, n, vel / 1e6, tri))

# ------------------------------------------------------------------ 3) štola
ST = MO["stola"]
_sz = sys.argv[sys.argv.index("--stola-zdroj") + 1] if "--stola-zdroj" in sys.argv else K + "/build/zdroj_modelar/stola"
SG = os.path.join(_sz, ST["glb"])
if not os.path.exists(SG):   # stáhnout z Disku jen glb (zip 149 MB: .blend se nerozbaluje)
    os.makedirs(_sz, exist_ok=True); zp = os.path.join(_sz, "stola.zip")
    subprocess.run(["curl", "-sSL", "-m", "1200", "-o", zp, "https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t" % ST["disk_id"]], check=False)
    if os.path.exists(zp):
        with zipfile.ZipFile(zp) as zf:
            for i in zf.namelist():
                if i.endswith((".glb", ".tscn", ".txt")): zf.extract(i, _sz)
        os.remove(zp)
if os.path.exists(SG):
    import re
    def mimo(jm):   # úseky chodeb po 9 m: _i_j (j = úsek ve směru chodby) – jen vstup a první úseky
        m = re.search(r"_(-?\d+)_(-?\d+)(-colonly)?$", jm)
        return bool(m) and int(m.group(2)) not in ST["useky_j"]
    pb = Prebal(SG).vyber(vynechat_fn=mimo, vynechat_prim=ST["vynechat_prim"])
    # čelba: nepravidelná skalní stěna na konci chodby (mřížka s hrboly), kolize kvádr
    C = ST["celba"]; nx_, ny_ = 14, 12
    xs = np.linspace(C["x"][0], C["x"][1], nx_); ys = np.linspace(C["y"][0], C["y"][1], ny_)
    rng = np.random.default_rng(1393); dz = rng.normal(0, 0.07, (ny_, nx_))
    P = np.array([[x, y, C["z"] + dz[a, b]] for a, y in enumerate(ys) for b, x in enumerate(xs)])
    I = []
    for a in range(ny_ - 1):
        for b in range(nx_ - 1):
            q = a * nx_ + b; I += [q, q + 1, q + nx_, q + 1, q + nx_ + 1, q + nx_]
    N = np.tile([0, 0, 1.0], (len(P), 1)); UV = P[:, [0, 1]] / 2.0
    mref = None
    for i_, m_ in enumerate(pb.j["materials"]):
        if m_.get("name", "").startswith(C["material"]): mref = ("src", i_); break
    kv = kvadr(C["x"][0], C["x"][1], C["y"][0], C["y"][1], C["z"] - 0.6, C["z"])[0]
    pb.pridej_sit("Stola_Celba", [(mref, P, N, UV, np.array(I))], kolize=[kv])
    dst = OUT + "/stola.glb"
    n, vel, tri = pb.uloz(dst, TEX, max_px=ST["max_px"])
    # světla kahanů z dodané scény (jen ta v ponechané části chodby)
    ka = []
    tscn = os.path.join(os.path.dirname(SG), "Stara_stola_1393.tscn")
    if os.path.exists(tscn):
        for m in re.finditer(r'\[node name="Kahan_\d+"[^\]]*\]\ntransform = Transform3D\(([^)]*)\)', open(tscn).read()):
            v = [float(x) for x in m.group(1).split(",")]
            if v[11] > C["z"] + 0.5: ka.append([v[9], v[10], v[11]])
    INFO["modely"]["stola"] = {"aabb": bbox(dst), "celba_z": C["z"], "kahany": ka, "troj": tri}
    print("ZAJIMAVA stola uzlů %d, %.2f MB, troj %d, kahanů %d" % (n, vel / 1e6, tri, len(ka)))
else:
    print("ZAJIMAVA_CHYBI štola", SG)

# ------------------------------------------------------------------ 4) brť (dlužka s česnem) – materiál dřeva lesních dílů
src = ZL + "/les_uhlir_naradi.glb"
if os.path.exists(src):
    pb = Prebal(src).vyber(["Les_Naradi"]); kor = pb.uzly[pb.koreny[0]]; kor.pop("mesh", None); kor["name"] = "Brt"
    mdr = pb.material("M_LesDrevo"); mku = pb.material("M_LesKura")
    tma = pb.novy_material("M_BrtCesno", None, barva=(0.05, 0.035, 0.02, 1.0))
    # dlužka 0,26 × 0,95 m na líci kmene (počátek = líc kmene, +z ven), dva klíny, česno (tmavý otvor) dole
    dl = kvadr(-0.13, 0.13, -0.48, 0.48, 0.0, 0.05, uv_m=0.5)
    kl = spoj(posun(kvadr(-0.03, 0.03, -0.05, 0.05, 0.0, 0.07), (0.16, 0.25, 0)), posun(kvadr(-0.03, 0.03, -0.05, 0.05, 0.0, 0.07), (-0.16, -0.25, 0)))
    ce = kvadr(-0.035, 0.035, -0.32, -0.29, 0.049, 0.052)
    lem = kvadr(-0.17, 0.17, -0.55, 0.55, -0.04, 0.005, uv_m=0.5)   # okraj otesané kůry kolem brti
    pb.pridej_sit("Brt_Dluzka", [(mdr,) + spoj(dl, kl), (tma,) + ce, (mku,) + lem])
    dst = OUT + "/brt.glb"; n, vel, tri = pb.uloz(dst, TEX)
    INFO["modely"]["brt"] = {"aabb": bbox(dst), "troj": tri}
    print("ZAJIMAVA brt %.2f MB" % (vel / 1e6))

# ------------------------------------------------------------------ 5) kameny lomu a stromy brtí (modely Havrana)
for m in ("balvan_droba_1", "kamen_droba_1"):
    s_ = K + "/../modely/nove/%s.glb" % m
    if os.path.exists(s_):
        pb = Prebal(s_).vyber(); n, vel, tri = pb.uloz(OUT + "/%s.glb" % m, TEX, max_px=1024)
        INFO["modely"][m] = {"aabb": bbox(OUT + "/%s.glb" % m), "troj": tri}
for m in ("borovice_stara", "dub_stary"):   # poloměr kmene ve výšce brti (pro přiložení dlužky)
    p_ = K + "/hra/modely/stromy/%s.glb" % m
    if not os.path.exists(p_): continue
    j, b, _ = nacti(p_); R = {}
    def walk(i, M):
        n = j["nodes"][i]; M = M @ matice(n)
        if "mesh" in n:
            for p in j["meshes"][n["mesh"]]["primitives"]:
                X = cti(j, b, p["attributes"]["POSITION"]); X = (np.c_[X, np.ones(len(X))] @ M.T)[:, :3]
                mj = j["materials"][p.get("material", 0)].get("name", "").lower() if j.get("materials") else ""
                if "list" in mj or "leaf" in mj or "jehl" in mj or "needle" in mj: continue
                for h in (3.0, 3.5, 4.0):
                    sel = np.abs(X[:, 1] - h) < 0.15
                    if sel.sum() > 6:
                        d = np.hypot(X[sel, 0], X[sel, 2]); R.setdefault(h, []).append(float(np.percentile(d, 50)))
        for c in n.get("children", []): walk(c, M)
    for r_ in j["scenes"][0]["nodes"]: walk(r_, np.eye(4))
    INFO["modely"]["strom_" + m] = {"kmen_r": {str(h): round(min(v), 3) for h, v in R.items()}, "aabb": bbox(p_)}
json.dump(INFO, open(K + "/hra/data/zajimava_modely.json", "w"), ensure_ascii=False, indent=1)
print("ZAJIMAVA modely hotovo:", ", ".join(INFO["modely"]))
