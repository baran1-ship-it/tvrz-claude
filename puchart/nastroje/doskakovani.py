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
ap.add_argument("--od", type=float, default=0.25); ap.add_argument("--do", type=float, default=0.7); ap.add_argument("--vyrez", action="store_true"); ap.add_argument("--pomer", type=float, default=5.0)
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

# skok = velká změna mezi i−1 a i v místě, kde je obraz před (i−2 → i−1) i po (i → i+1) klidný (vítr a pohyb mění obraz
# pořád, doskočení jen jednou)
img = [nacti(f) for f in fs]; h = img[0].shape[0]; r0, r1 = int(h * a.od), int(h * a.do); nalezy = []
for i in range(2, len(fs) - 1):
    d = np.abs(img[i] - img[i - 1])[r0:r1]
    dp = np.abs(img[i - 1] - img[i - 2])[r0:r1]; dn = np.abs(img[i + 1] - img[i])[r0:r1]
    for s_ in sorted((s for s in skvrny(d > a.prah) if s[0] >= a.plocha), reverse=True):
        n, x0, y0, x1, y1 = s_; R = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        if d[R].mean() > a.pomer * max(dp[R].mean(), dn[R].mean(), 1.0):
            nalezy.append((i, s_))
            print("SKOK %s plocha %d obdélník x %d–%d y %d–%d (změna %.0f, před %.0f, po %.0f)" % (os.path.basename(fs[i]), n, x0, x1, y0 + r0, y1 + r0, d[R].mean(), dp[R].mean(), dn[R].mean()))
            if a.vyrez:
                X0, X1 = max(0, x0 - 40), x1 + 40; Y0, Y1 = max(0, y0 + r0 - 40), y1 + r0 + 40
                A = Image.open(fs[i - 1]).crop((X0, Y0, X1, Y1)); B = Image.open(fs[i]).crop((X0, Y0, X1, Y1))
                W = Image.new("RGB", (A.width * 2 + 4, A.height), (255, 0, 0)); W.paste(A, (0, 0)); W.paste(B, (A.width + 4, 0))
                W.resize((W.width * 2, W.height * 2)).save(os.path.join(a.adr, "skok_%03d.png" % i))
            break
print("DOSKAKOVANI %d skoků v %d snímcích" % (len(nalezy), len(fs)))
