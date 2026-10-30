"""Nastavení importu textur hradu v Godotu (rozpocty.json hrad_textury): limit velikosti a VRAM komprese.
Spustit po exportu hradu z Blenderu a godot --import, pak znovu godot --import (přeimportuje změněné).
python3 import_hrady.py <koren>"""
import sys, os, re, json, glob
K = sys.argv[1]; R = json.load(open(os.path.join(K, "pravidla/svet/rozpocty.json")))["hrad_textury"]
n = 0
for f in glob.glob(os.path.join(K, "hra/modely/hrady/*.jpg.import")):
    s = open(f).read()
    px = R["normal_px"] if "_nor_gl" in f else R["diffuse_px"]
    s2 = re.sub(r"process/size_limit=\d+", "process/size_limit=%d" % px, s)
    if R["vram"]:
        s2 = re.sub(r"compress/mode=\d+", "compress/mode=2", s2)
        if "_nor_gl" in f: s2 = re.sub(r"compress/normal_map=\d+", "compress/normal_map=1", s2)
    if s2 != s: open(f, "w").write(s2); n += 1
print("textur hradu upraveno", n)
