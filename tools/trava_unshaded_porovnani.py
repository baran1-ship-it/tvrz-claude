#!/usr/bin/env python3
"""Porovnani snimku travy stinovana (st_*) x unshaded (un_*) ze stejneho behu (rozbor 5. 11., modely.json _trava_unshaded).

Vyrez spodni casti obrazu (bez HUD) se rozdeli na bloky 20x20 px; bloky travy (zelena prevazuje) se podle jasu ve
stinovanem snimku rozdeli na slunce / stin (prah Otsu, jen kdyz je rozdil zretelny). Pro tytez bloky se spocte prumer
v obou snimcich (sRGB 0-255) a pomer unshaded / stinovana po kanalech. Bloky, ne pixely: vitr stebla mezi snimky posune.

python3 tools/trava_unshaded_porovnani.py build/f160 les1 les2 louka1 ...
"""
import sys
from PIL import Image
import numpy as np

B = 20
VYREZ = (200, 360, 1000, 700)       # x0, y0, x1, y1 - bez horni listy, ukazatelu a ovladacu


def bloky(img):
    a = np.asarray(img.convert("RGB"), dtype=np.float64)[VYREZ[1]:VYREZ[3], VYREZ[0]:VYREZ[2]]
    h, w = a.shape[0] // B, a.shape[1] // B
    return a[:h * B, :w * B].reshape(h, B, w, B, 3).mean(axis=(1, 3)).reshape(-1, 3)


def otsu(v):
    best, tb = -1.0, float(np.median(v))
    for t in np.linspace(v.min(), v.max(), 64)[1:-1]:
        a, b = v[v < t], v[v >= t]
        if len(a) == 0 or len(b) == 0:
            continue
        s = len(a) * len(b) * (a.mean() - b.mean()) ** 2
        if s > best:
            best, tb = s, t
    return tb


def main():
    d = sys.argv[1]
    for m in sys.argv[2:]:
        s = bloky(Image.open(f"{d}/st_{m}.png"))
        u = bloky(Image.open(f"{d}/un_{m}.png"))
        tr = (s[:, 1] > s[:, 0] * 1.02) & (s[:, 1] > s[:, 2] * 1.1)
        if tr.sum() < 10:
            print(f"{m}: malo bloku travy ({tr.sum()})")
            continue
        jas = s[:, 1]
        t = otsu(jas[tr])
        sl = tr & (jas >= t)
        st = tr & (jas < t)
        # zretelne rozdeleni: stredy skupin o > 35 %
        if sl.sum() and st.sum() and s[sl, 1].mean() < 1.35 * s[st, 1].mean():
            sl, st = tr, tr & False
        print(f"{m}: bloku travy {tr.sum()} (slunce {sl.sum()}, stin {st.sum()}, prah G {t:.0f})")
        for jm, mk in (("vse", tr), ("slunce", sl), ("stin", st)):
            if mk.sum() == 0:
                continue
            a, b = s[mk].mean(axis=0), u[mk].mean(axis=0)
            print(f"   {jm:6s} stinovana {np.round(a).astype(int)}  unshaded {np.round(b).astype(int)}  pomer un/st {np.round(b / np.maximum(a, 1), 2)}")


if __name__ == "__main__":
    main()
