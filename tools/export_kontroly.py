"""Kontroly kroku exportu s navratovym kodem (Astra/radce 29. 10. 07:10: zadny grep jako test uspechu v shellu).
  python3 tools/export_kontroly.py pyflakes      chyby jmen/syntaxe ve skriptech Blenderu (rc 1)
  python3 tools/export_kontroly.py blender       build/export_hotov.json z tohoto behu Blenderu (rc 1 chybi/stary)
  python3 tools/export_kontroly.py import LOG     chyby importu Godotu v logu (rc 1)
  python3 tools/export_kontroly.py drevo         jas materialu dreva (Misa 13. 11. cerne drevo; rc 1)
  python3 tools/export_kontroly.py reka          potok predpecen pro tento export? (rc 0 ano, 1 ne = predpect)"""
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
co = sys.argv[1]
if co == "pyflakes":
    r = subprocess.run(["/opt/bl/bin/python", "-m", "pyflakes"] + sorted(glob.glob("blender/*.py")) + ["tools/test_smyslu.py"],
                       capture_output=True, text=True)
    zle = [ln for ln in (r.stdout + r.stderr).splitlines()
           if "undefined name" in ln or "unable to detect undefined" in ln or "invalid syntax" in ln or "No module named pyflakes" in ln]
    for ln in zle:
        print(ln)
    sys.exit(1 if zle else 0)
if co == "blender":
    try:
        h = json.load(open("build/export_hotov.json"))
    except (OSError, ValueError):
        sys.exit("export_hotov.json chybi - Blender nedobehl")
    if h.get("svet_md5") != __import__("hashlib").md5(open("modely/svet.json", "rb").read()).hexdigest():
        sys.exit("export_hotov.json neni z tohoto svet.json")
    print("blender hotov: %s" % h.get("souhrn", ""))
    sys.exit(0)
if co == "import":
    t = open(sys.argv[2], errors="replace").read()
    zle = [ln for ln in t.splitlines() if any(k in ln for k in ("ERR_FILE_CORRUPT", "Error loading image", "Failed loading resource"))]
    for ln in zle[:10]:
        print(ln)
    sys.exit(1 if zle else 0)
if co == "reka":
    sj = json.load(open("modely/svet.json")).get("reka_otisk")
    rj = json.load(open("modely/reka/reka.json")).get("reka_otisk") if os.path.exists("modely/reka/reka.json") else None
    sys.exit(0 if sj == rj else 1)
if co == "drevo":
    # Misa 13. 11. (drevo cerne): materialy dreva v svet.json - jas textury x tint >= pravidla/svet/modely.json drevo_jas.min
    from PIL import Image
    dj = json.load(open("pravidla/svet/modely.json"))["drevo_jas"]
    zle = []
    for k, d in json.load(open("modely/svet.json"))["materialy"].items():
        if d.get("type") != "tex" or d.get("tex") not in dj["textury"] or k in dj["vyjimky"]:
            continue
        im = Image.open("modely/textury/%s_diff.jpg" % d["tex"]).convert("RGB").resize((64, 64))
        px = list(im.getdata()) if not hasattr(im, "get_flattened_data") else list(im.get_flattened_data()); n = len(px)
        sr = [sum(p[i] for p in px) / n / 255.0 * float(d["tint"][i]) for i in range(3)]
        g = 0.3 * sr[0] + 0.59 * sr[1] + 0.11 * sr[2]
        if g < float(dj["min"]):
            zle.append("%s (%s) jas %.2f" % (k, d["tex"], g))
    for z in zle:
        print("DREVO TMAVE", z)
    sys.exit(1 if zle else 0)
sys.exit("neznama kontrola %s" % co)
