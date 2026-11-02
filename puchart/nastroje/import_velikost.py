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
for f in glob.glob(K + "/hra/modely/rostliny/*.png.import"):
    n += uprav(f, [("process/size_limit", R["rostliny_px"])])
n += uprav(K + "/hra/textury/ui/mapa.png.import", [("process/size_limit", R["mapa_px"])])
for f in (K + "/hra/modely/hrady/puchart.glb.import", K + "/hra/modely/hrady/skaly.glb.import"):
    if os.path.exists(f):
        n += uprav(f, [("meshes/create_shadow_meshes", str(R["hrad_shadow_meshes"]).lower()), ("meshes/ensure_tangents", str(R["hrad_tangenty"]).lower())])
print("upraveno importů", n)
