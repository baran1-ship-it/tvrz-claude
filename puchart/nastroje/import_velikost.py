"""Nastavení importu kvůli velikosti APK (rozpocty.json velikost_apk): rostliny a mapa s limitem velikosti, hrad a skály
bez stínových kopií sítě. Spustit po godot --import, pak znovu godot --import. python3 import_velikost.py <koren>"""
import sys, re, glob, json, os
K = sys.argv[1]; R = json.load(open(K + "/pravidla/svet/rozpocty.json"))["velikost_apk"]
def uprav(f, pary):
    s = open(f).read(); s2 = s
    for k, v in pary: s2 = re.sub(r"^%s=.*$" % re.escape(k), "%s=%s" % (k, v), s2, flags=re.M)
    if s2 != s: open(f, "w").write(s2); return 1
    return 0
n = 0
VRAM = [("compress/mode", 2), ("mipmaps/generate", "true")]
for f in glob.glob(K + "/hra/modely/rostliny/*.png.import"):
    n += uprav(f, [("process/size_limit", R["rostliny_px"])])
for f in glob.glob(K + "/hra/modely/rostliny/*.jpg.import") + glob.glob(K + "/hra/modely/voda_*.import"):   # podrost a lávka: bez alfy -> VRAM
    n += uprav(f, [("process/size_limit", R["rostliny_px"])] + VRAM)
IMP = json.load(open(K + "/pravidla/svet/stromy_modely.json")).get("impostor", {})
for f in glob.glob(K + "/hra/textury/impostory/*.png.import"):   # impostory (stromy_modely.json impostor): barva plně, normály menší
    n += uprav(f, [("process/size_limit", IMP.get("normaly_max_px", 512) if f.endswith("_n.png.import") else IMP.get("barva_max_px", 512))] + VRAM)
n += uprav(K + "/hra/textury/ui/mapa.png.import", [("process/size_limit", R["mapa_px"])])
for f in (K + "/hra/modely/hrady/puchart.glb.import", K + "/hra/modely/hrady/skaly.glb.import"):
    if os.path.exists(f):
        n += uprav(f, [("meshes/create_shadow_meshes", str(R["hrad_shadow_meshes"]).lower()), ("meshes/ensure_tangents", str(R["hrad_tangenty"]).lower())])
# stromy mají vlastní LOD1/impostory, podrost a voda jsou malé: bez automatických LOD a stínových kopií (2. 11.: APK 110 MB)
for f in glob.glob(K + "/hra/modely/stromy/*.glb.import") + glob.glob(K + "/hra/modely/rostliny/*.glb.import") + [K + "/hra/modely/voda.glb.import"]:
    if os.path.exists(f): n += uprav(f, [("meshes/create_shadow_meshes", "false")])
for f in [K + "/hra/modely/voda.glb.import"]:   # podrost a nové stromy LOD potřebují (bez nich 0,9 → 1,7 M troj.)
    if os.path.exists(f): n += uprav(f, [("meshes/generate_lods", "false")])
for f in glob.glob(K + "/hra/modely/rostliny/*.glb.import"): n += uprav(f, [("meshes/generate_lods", "true")])
for jm in ("javor", "jasan", "habr", "jilm"):
    for f in glob.glob(K + "/hra/modely/stromy/%s_*.glb.import" % jm): n += uprav(f, [("meshes/generate_lods", "true")])
# stromy: barva listí max 512 px, normály 256 px (zblízka jen LOD0 do 16 m); normály podrostu VRAM (2. 11.: APK 107 MB)
for f in glob.glob(K + "/hra/modely/stromy/tex/*.import"):
    t = open(f).read()
    n += uprav(f, [("process/size_limit", 256 if "compress/normal_map=1" in t else min(512, int(re.search(r"size_limit=(\d+)", t).group(1)) or 512))])
for f in glob.glob(K + "/hra/modely/rostliny/*normal*.png.import"):
    n += uprav(f, VRAM + [("compress/normal_map", 1)])
# textury v grafické paměti (rozpocty.json textury_vram, docs/rozpracovane/textury_vram_17_11.md T1–T4)
TV = json.load(open(K + "/pravidla/svet/rozpocty.json")).get("textury_vram", {})
if TV.get("rostliny_barva_vram"):   # barvy rostlin s alfou: RGBA8 → ETC2_RGBA8 (4× méně)
    for f in glob.glob(K + "/hra/modely/rostliny/*.png.import"):
        if "normal" not in os.path.basename(f): n += uprav(f, VRAM)
MK = TV.get("maska_koleje")
if MK and os.path.exists(K + "/hra/textury/maska_koleje.png.import"):   # maska kolejí 4000² L8 → ETC2_R11 s mipmapami
    n += uprav(K + "/hra/textury/maska_koleje.png.import", [("compress/mode", 2 if MK.get("vram") else 0), ("mipmaps/generate", str(bool(MK.get("mipmapy"))).lower())])
for f in glob.glob(K + "/hra/modely/stavby_h/tex/*.import"):   # sdílené textury staveb (stromy_sdilene_textury.py): jako dřív vytažené
    # z glb (VRAM, normály ETC2_RGB8 jako dosud – detekce normálové mapy by je zdvojnásobila na RG11), horní mez stavby_max_px
    n += uprav(f, VRAM + [("compress/normal_map", 2), ("process/size_limit", TV.get("stavby_max_px", 0))])
_PV = os.path.join(K, "hra/modely/predmety_h/tex/puvod.json"); PV = json.load(open(_PV)) if os.path.exists(_PV) else {}
for f in glob.glob(K + "/hra/modely/predmety_h/tex/*.import"):   # sdílené textury předmětů pískoviště (Míša 17. 11.): jako dřív vytažené
    h = os.path.basename(f).split(".")[0]   # kovadlina_1393 (i stupně _stredni/_daleko): horní mez kovadlina_max_px
    kov = any(m.startswith("kovadlina_1393") for m in PV.get(h, []))
    n += uprav(f, VRAM + [("compress/normal_map", 2), ("process/size_limit", TV.get("kovadlina_max_px", 0) if kov else 0)])
for f in glob.glob(K + "/hra/modely/predmety_h/kovadlina_1393_*.import"):   # před sdílením (vytažené z glb vedle modelu)
    n += uprav(f, [("process/size_limit", TV.get("kovadlina_max_px", 0))])
print("upraveno importů", n)
