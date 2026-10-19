"""Kalibrace odrazivosti fotek terenu: prumerny jas (linearni, 0.3R+0.5G+0.2B) kazde *_diff.jpg v modely/textury
-> modely/textury/albedo.json. Hra (svet.gd) nasobi fotku cil/prumer, aby povrch mel skutecnou odrazivost
(fotky z ruznych zdroju maji ruznou expozici: obili 0.31, cesta 0.04).  python3 tools/albedo_textur.py"""
import glob
import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


out = {}
for f in sorted(glob.glob(os.path.join(ROOT, "modely", "textury", "*_diff.jpg"))):
    im = Image.open(f).convert("RGB").resize((128, 128))
    px = list(im.getdata())
    m = [sum(lin(p[i]) for p in px) / len(px) for i in range(3)]
    out[os.path.basename(f)[:-9]] = round(0.3 * m[0] + 0.5 * m[1] + 0.2 * m[2], 4)
    out[os.path.basename(f)[:-9] + "_rgb"] = [round(x, 4) for x in m]
# prumerna barva atlasu travy (jen kryte pixely): podklad louky se k ni kalibruje po kanalech (hrana trsu neni videt)
a = Image.open(os.path.join(ROOT, "obrazky", "trava_atlas.png")).convert("RGBA").resize((256, 128))
s, w = [0.0, 0.0, 0.0], 0
for p in a.getdata():
    if p[3] > 128:
        for i in range(3):
            s[i] += lin(p[i])
        w += 1
out["atlas_travy_rgb"] = [round(x / w, 4) for x in s]
json.dump(out, open(os.path.join(ROOT, "modely", "textury", "albedo.json"), "w"), indent=1)
print("albedo textur:", len(out))
