"""Seno od Míšina modeláře do hry (pravidla/svet/seno.json; modelový filtr CLAUDE.md: licence → měřítko → materiály → LOD →
katalog). Ze sady build/zdroj_modelar/Seno_1400 zkopíruje nativní scény Godotu (.tscn s LOD0/LOD1 přes Visibility Range),
sítě *_mesh.res, sdílené materiály (.tres) a textury do vystup (struktura sady zůstane – scény odkazují relativně).
Materiál sena dostane albedo modulaci z dat (albedo_color). Dodané .glb se nekopírují (každý nese vlastní kopii textur).
Pro katalog pískoviště zapíše hra/modely/predmety_h/seno_<Model>.tscn (instance nativní scény) a záznamy do
hra/modely/predmety_h.json (rozměr z LOD0 .glb sady, osy Godotu).
  python3 nastroje/seno_modely.py <K>"""
import sys, os, json, re, shutil, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_sit import nacti, cti

K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
C = json.load(open(os.path.join(K, "pravidla/svet/seno.json")))
ZD = os.path.join(K, C["slozka"]); OUT = os.path.join(K, C["vystup"])
if not os.path.isdir(ZD):
    print("SENO_CHYBI sada", ZD); sys.exit(0)
os.makedirs(os.path.join(OUT, "textures"), exist_ok=True)


def kopie(src, dst):
    # sítě *_mesh.res se po kopii převádějí (barvy vrcholů → sRGB, barvy_vrcholu.py), velikost se smí lišit – kopie jen při novějším zdroji
    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst) or (not dst.endswith("_mesh.res") and os.path.getsize(src) != os.path.getsize(dst)):
        shutil.copy2(src, dst)


for f in os.listdir(os.path.join(ZD, "textures")):
    kopie(os.path.join(ZD, "textures", f), os.path.join(OUT, "textures", f))
for sc in C["sceny"]:
    kopie(os.path.join(ZD, sc + ".tscn"), os.path.join(OUT, sc + ".tscn"))
    for lod in ("LOD0", "LOD1"):
        kopie(os.path.join(ZD, "%s_%s_mesh.res" % (sc, lod)), os.path.join(OUT, "%s_%s_mesh.res" % (sc, lod)))
for m in C["materialy"]:
    t = open(os.path.join(ZD, m)).read()
    if m.startswith("Seno_"):   # albedo modulace (barva níž – data, ne přepis textury)
        r, g, b = C["albedo_modulace"]
        t = re.sub(r"\nalbedo_color = [^\n]*", "", t)
        t = t.replace("\nalbedo_texture", "\nalbedo_color = Color(%.3f, %.3f, %.3f, 1)\nalbedo_texture" % (r, g, b), 1)
    open(os.path.join(OUT, m), "w").write(t)
# barvy vrcholů lineární → sRGB (pravidla/svet/barvy_vrcholu.json sada seno; Compatibility je násobí s albedem v sRGB – chyby.md 356)
if subprocess.run([sys.executable, os.path.join(K, "nastroje/barvy_vrcholu.py"), K, C["barvy_vrcholu_sada"]]).returncode != 0: sys.exit(1)

# katalog pískoviště: obalová scéna + záznam s rozměrem z LOD0 glb
PRED = os.path.join(K, "hra/modely/predmety_h"); KATP = os.path.join(K, "hra/modely/predmety_h.json")
KAT = json.load(open(KATP)) if os.path.exists(KATP) else {}
res = "res://" + os.path.relpath(OUT, os.path.join(K, "hra")).replace(os.sep, "/")
for model, z in C["katalog"].items():
    if model.startswith("_"): continue
    os.makedirs(PRED, exist_ok=True)
    open(os.path.join(PRED, "seno_%s.tscn" % model), "w").write("\n".join([
        '[gd_scene load_steps=2 format=3]', '', '[ext_resource type="PackedScene" path="%s/%s.tscn" id="1"]' % (res, model), '',
        '[node name="seno_%s" instance=ExtResource("1")]' % model, '']))
    rozmer = z.get("rozmer")
    glb = os.path.join(ZD, model + "_LOD0.glb")
    if os.path.exists(glb):
        j, b, _ = nacti(glb); body = []
        for n in j["nodes"]:
            if "mesh" in n:
                for p in j["meshes"][n["mesh"]]["primitives"]:
                    body.append(cti(j, b, p["attributes"]["POSITION"]) + np.array(n.get("translation", [0, 0, 0])))
        B = np.vstack(body); rozmer = [round(float(v), 3) for v in (B.max(0) - B.min(0))]
    KAT["seno_" + model] = {"nazev": z["nazev"], "kat": z["kat"], "stav": z["stav"], "vaha": z["vaha"], "cena": z["cena"], "rozmer": rozmer}
    print("SENO_KATALOG seno_%s %s" % (model, rozmer))
if os.path.exists(KATP):
    json.dump(KAT, open(KATP, "w"), ensure_ascii=False, indent=1)
print("SENO hotovo: %d scén, materiál sena × %s, výstup %s" % (len(C["sceny"]), C["albedo_modulace"], OUT))
