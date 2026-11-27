#!/usr/bin/env python3
"""Hledání doskakování v chůzi kamerou (Míša 27. 11.: „pořád něco doskakuje… najdi to“).

Vstup: snímky <adresář>/<jméno>_NNN.png z PUCHART_FOTO_CHUZE (hlavni.gd _chuze). Mezi dvěma sousedními snímky se kamera
posune o pár cm – plynulý pohyb mění obraz jen málo a rozprostřeně; věc, která se objeví nebo zmizí (doskočí), dá
ostrou souvislou skvrnu velké změny. Porovnává se jen pás obrazu ve střední dálce (řádky od..do), kde je doskakování
vidět (dole je zem u nohou, ta se mění pohybem). Výstup: snímky se skvrnou, její plocha a obdélník; s --vyrez uloží
výřezy před/po do <adresář>/skok_NNN.png.

python3 nastroje/doskakovani.py <adresář> [--prah 60] [--plocha 40] [--od 0.25] [--do 0.7] [--vyrez]
"""
import sys, os, glob, argparse
import numpy as np
from PIL import Image, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("adr"); ap.add_argument("--prah", type=float, default=60.0); ap.add_argument("--plocha", type=int, default=40)
ap.add_argument("--od", type=float, default=0.25); ap.add_argument("--do", type=float, default=0.7); ap.add_argument("--vyrez", action="store_true")
a = ap.parse_args()
fs = sorted(glob.glob(os.path.join(a.adr, "*_[0-9][0-9][0-9].png")))
if len(fs) < 2: sys.exit("málo snímků")

def nacti(f):
    im = Image.open(f).convert("L").filter(ImageFilter.GaussianBlur(1.2))
    return np.asarray(im, np.float32)

def skvrny(m):   # souvislé oblasti (4-sousedství) -> [(plocha, x0, y0, x1, y1)]
    h, w = m.shape; vid = np.zeros_like(m, bool); out = []
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if vid[y, x]: continue
        st = [(y, x)]; vid[y, x] = True; n = 0; x0 = x1 = x; y0 = y1 = y
        while st:
            cy, cx = st.pop(); n += 1; x0 = min(x0, cx); x1 = max(x1, cx); y0 = min(y0, cy); y1 = max(y1, cy)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not vid[ny, nx]: vid[ny, nx] = True; st.append((ny, nx))
        out.append((n, x0, y0, x1, y1))
    return out

pred = nacti(fs[0]); h = pred.shape[0]; r0, r1 = int(h * a.od), int(h * a.do); nalezy = []
for i in range(1, len(fs)):
    po = nacti(fs[i]); d = np.abs(po - pred)[r0:r1]
    sk = [s for s in skvrny(d > a.prah) if s[0] >= a.plocha]
    if sk:
        nej = max(sk); nalezy.append((i, nej))
        print("SKOK %s plocha %d obdélník x %d–%d y %d–%d" % (os.path.basename(fs[i]), nej[0], nej[1], nej[3], nej[2] + r0, nej[4] + r0))
        if a.vyrez:
            x0, x1 = max(0, nej[1] - 40), nej[3] + 40; y0, y1 = max(0, nej[2] + r0 - 40), nej[4] + r0 + 40
            A = Image.open(fs[i - 1]).crop((x0, y0, x1, y1)); B = Image.open(fs[i]).crop((x0, y0, x1, y1))
            W = Image.new("RGB", (A.width * 2 + 4, A.height), (255, 0, 0)); W.paste(A, (0, 0)); W.paste(B, (A.width + 4, 0))
            W = W.resize((W.width * 2, W.height * 2)); W.save(os.path.join(a.adr, "skok_%03d.png" % i))
    pred = po
print("DOSKAKOVANI %d skoků v %d snímcích" % (len(nalezy), len(fs)))
