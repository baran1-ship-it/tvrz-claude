"""Lůžka od Míšina modeláře do hry (pravidla/svet/luzka.json; modelový filtr CLAUDE.md: licence → měřítko → materiály →
LOD + kolize → interakce → katalog). Ze sady build/zdroj_modelar/Luzka_1400 zkopíruje jen tabletové nativní scény
(<Model>_Tablet_1K.tscn – LOD0/LOD1 přes Visibility Range, kolize StaticBody3D, značky Luzko_*), jejich sítě *_mesh.res,
1K materiály (.tres, COLOR_0 × albedo) a 1K textury (albedo, normal GL, ORM) do vystup; struktura sady zůstane (scény
odkazují relativně: sítě vedle scény, materials/, textures/). Soubory, které tam nepatří (GLB, 2K, dokumentace), smaže.
Pro katalog pískoviště zapíše hra/modely/predmety_h/luzko_<Model>.tscn (instance nativní scény) a záznamy do
hra/modely/predmety_h.json (rozměr z ASSETY.json v osách Godotu, lehat: true). Pravidla zkopíruje do hra/pravidla/svet.
  python3 nastroje/luzka_modely.py <K> [--ikony]"""
import sys, os, json, re, shutil, subprocess

K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ".")
C = json.load(open(os.path.join(K, "pravidla/svet/luzka.json")))
shutil.copy2(os.path.join(K, "pravidla/svet/luzka.json"), os.path.join(K, "hra/pravidla/svet/luzka.json"))
ZD = os.path.join(K, C["slozka"]); OUT = os.path.join(K, C["vystup"])
if not os.path.isdir(ZD):
    print("LUZKA_CHYBI sada", ZD); sys.exit(0)
os.makedirs(os.path.join(OUT, "textures"), exist_ok=True); os.makedirs(os.path.join(OUT, "materials"), exist_ok=True)


def kopie(src, dst):
    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst) or os.path.getsize(src) != os.path.getsize(dst):
        shutil.copy2(src, dst)


chci = set()
for sc in C["sceny"]:
    tscn = sc + C["varianta"] + ".tscn"
    t = open(os.path.join(ZD, tscn)).read()
    kopie(os.path.join(ZD, tscn), os.path.join(OUT, tscn)); chci.add(tscn)
    for p in re.findall(r'\[ext_resource [^\]]*path="([^"]+)"', t):
        if p.startswith("res://") or not os.path.exists(os.path.join(ZD, p)):
            print("LUZKA_CHYBA cesta %s v %s" % (p, tscn)); sys.exit(1)
        kopie(os.path.join(ZD, p), os.path.join(OUT, p)); chci.add(p)
for m in C["materialy"]:
    p = "materials/" + m
    t = open(os.path.join(ZD, p)).read()
    if "vertex_color_use_as_albedo = true" not in t:   # NAVOD_LUZKA.md: COLOR_0 se násobí s albedem
        print("LUZKA_CHYBA %s bez vertex_color_use_as_albedo" % m); sys.exit(1)
    kopie(os.path.join(ZD, p), os.path.join(OUT, p)); chci.add(p)
    for q in re.findall(r'path="([^"]+)"', t):
        tp = os.path.normpath(os.path.join("materials", q))
        if not any(tp.endswith(x) for x in C["textury_pripony"]):
            print("LUZKA_CHYBA textura %s mimo 1K sadu" % tp); sys.exit(1)
        kopie(os.path.join(ZD, tp), os.path.join(OUT, tp)); chci.add(tp)
# úklid: co sada nepotřebuje (GLB, 2K, dokumentace z dřívější kopie celé složky) i s importem
smaz = 0
for d, _, fs in os.walk(OUT):
    for f in fs:
        r = os.path.relpath(os.path.join(d, f), OUT)
        zaklad = r[:-7] if r.endswith(".import") else r
        if zaklad not in chci:
            os.remove(os.path.join(d, f)); smaz += 1

# katalog pískoviště: obalová scéna + záznam (rozměr z ASSETY.json: Blender X šířka, Y délka, Z výška → Godot [x, y, z])
PRED = os.path.join(K, "hra/modely/predmety_h"); KATP = os.path.join(K, "hra/modely/predmety_h.json")
KAT = json.load(open(KATP)) if os.path.exists(KATP) else {}
AS = {a["name"]: a for a in json.load(open(os.path.join(ZD, "ASSETY.json")))}
res = "res://" + os.path.relpath(OUT, os.path.join(K, "hra")).replace(os.sep, "/")
ids = []
if not os.path.exists(KATP):   # katalog Havrana ještě není (postav_vse: předměty až po zajímavých místech) – nezakládat predmety_h
    print("LUZKA bez katalogu (predmety_h.json chybí – doplní druhé volání po predmety_z_havrana)"); C["sceny_kat"] = []
for model in C.get("sceny_kat", C["sceny"]):
    z = C["katalog"][model]; mid = "luzko_" + model
    open(os.path.join(PRED, mid + ".tscn"), "w").write("\n".join([
        '[gd_scene load_steps=2 format=3]', '', '[ext_resource type="PackedScene" path="%s/%s%s.tscn" id="1"]' % (res, model, C["varianta"]), '',
        '[node name="%s" instance=ExtResource("1")]' % mid, '']))
    (x0, y0, z0), (x1, y1, z1) = AS[model]["bounds_blender"]
    zaznam = {"nazev": z["nazev"], "kat": None, "stav": z["stav"], "vaha": z["vaha"], "cena": z["cena"],
              "rozmer": [round(x1 - x0, 3), round(z1 - z0, 3), round(y1 - y0, 3)], "lehat": True, "mist": z["mist"],
              "zdroj": "Luzka_1400 (Míšin modelář 16. 11., textury Poly Haven CC0)"}
    if z.get("pruchozi"): zaznam["pruchozi"] = True
    KAT[mid] = zaznam; ids.append(mid)
    print("LUZKA_KATALOG %s %s" % (mid, zaznam["rozmer"]))
if ids: json.dump(KAT, open(KATP, "w"), ensure_ascii=False, indent=1)
if "--ikony" in sys.argv and ids:   # ikony 128 px jako ostatní předměty (nastroje/godot/ikony_predmetu.gd), po importu
    G = os.environ.get("G", "/opt/godot47/Godot_v4.7.2-stable_linux.x86_64")
    shutil.copy2(os.path.join(K, "nastroje/godot/ikony_predmetu.gd"), os.path.join(K, "hra/_ikony.gd"))
    subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 640x400x24", G, "--rendering-driver", "opengl3", "--path", os.path.join(K, "hra"), "-s", "res://_ikony.gd", "--"] + ids)
    for f in ("_ikony.gd", "_ikony.gd.uid"):
        if os.path.exists(os.path.join(K, "hra", f)): os.remove(os.path.join(K, "hra", f))
print("LUZKA hotovo: %d scén, %d souborů, smazáno navíc %d, výstup %s" % (len(C["sceny"]), len(chci), smaz, OUT))
