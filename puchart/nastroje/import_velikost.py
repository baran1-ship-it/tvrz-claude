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
for f in glob.glob(K + "/hra/textury/impostory/*.png.import"):   # impostory nových druhů jako ostatní (512, VRAM)
    n += uprav(f, [("process/size_limit", 512)] + VRAM)
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
print("upraveno importů", n)
