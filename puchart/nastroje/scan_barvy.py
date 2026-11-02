"""Barva naskenovaných skal (blender/skaly_scan) podle skutečnosti: droba zvětralá hnědošedá až šedá s lišejníkem (fotky
vyraznavylet.cz, GC80T08; ČGS: šedá, modrošedá). Poly Haven skeny jsou teplejší a pestřejší → sytost 45 %, mírně do studena.
Výstup <id>/textures/<id>_diff_droba.jpg. python3 scan_barvy.py <koren>"""
import sys, glob
import numpy as np
from PIL import Image
for f in glob.glob(sys.argv[1] + "/blender/skaly_scan/*/textures/*_diff_1k.jpg"):
    a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32) / 255
    l = (a @ np.array([0.3, 0.55, 0.15]))[..., None]
    sat = 0.55 if "moss" in f or "rock_face_02" in f else (0.18 if "boulder" in f else 0.45)   # mech zelenější, balvan je rezavý sken
    if "boulder" in f: a = a * 0.9
    g = (l + (a - l) * sat) * np.array([0.98, 1.0, 1.03])
    Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).save(f.replace("_diff_1k.jpg", "_diff_droba.jpg"), quality=92)
    print(f)
