#!/usr/bin/env python3
"""Obrys karet travy (Misa 4. 11. „udelej orez karet“, reserse_trava_hry.md bod 1): pro kazdou bunku atlasu
obdelnik [u0, u1, v vrchu], ve kterem je alfa. Karta se ve vertex shaderu stahne na nej (bez dalsich vrcholu)
kolem stebel - mene pixelu do discardu. Konzervativne: kazdy texel s alfou > PRAH_A lezi uvnitr (kontrola --test).
Vystup pravidla/svet/trava_karty.json. Spusteni: python3 tools/karty_obrys.py [--test]"""
import json, sys
import numpy as np
from PIL import Image

PRAH_A = 60          # alfa (0-255): shader prah 0,5, mipmapy alfu zesili az ~2x (1 + mip*0,3) - texel nad 60 muze projit
OKRAJ = 0.02         # rezerva u (podil sirky bunky) na kazdou stranu
ATLASY = {"trava_atlas": (3, 2), "trava_nizka_atlas": (3, 1), "trava_vysoka_atlas": (3, 2)}


def obrys(m):
    """[u0, u1, v vrchu] - obdelnik kolem stebel v bunce (pata zustava v = 1). Lichobezniky po pasech (2-6 pasu)
    ubraly jen o 3-8 % plochy vic za 2-6x vic trojuhelniku (trsy jsou siroke vejire) - 4. 11. zmereno, zamitnuto."""
    h, w = m.shape
    ys = np.nonzero(m.any(1))[0]
    xs = np.nonzero(m.any(0))[0]
    if len(ys) == 0:
        return [0.0, 1.0, 0.0]
    return [round(max(0.0, xs.min() / w - OKRAJ), 4), round(min(1.0, (xs.max() + 1) / w + OKRAJ), 4),
            round(max(0.0, ys.min() / h - OKRAJ), 4)]


def main():
    out = {"popis": __doc__.split("\n")[0] + " Generuje tools/karty_obrys.py z obrazky/*.png - neupravovat rucne.",
           "prah_alfa": PRAH_A, "okraj_u": OKRAJ}
    celk = {}
    for f, (sl, rd) in ATLASY.items():
        a = np.array(Image.open(f"obrazky/{f}.png").convert("RGBA"))[:, :, 3]
        H, W = a.shape
        h, w = H // rd, W // sl
        bunky = []
        plocha = 0.0
        for r in range(rd):
            for s in range(sl):
                m = a[r * h:(r + 1) * h, s * w:(s + 1) * w] > PRAH_A
                o = obrys(m)
                bunky.append(o)
                plocha += (o[1] - o[0]) * (1.0 - o[2])
                if "--test" in sys.argv:
                    ys, xs = np.nonzero(m)
                    for y, x in zip(ys, xs):
                        u = (x + 0.5) / w
                        v = (y + 0.5) / h
                        if v < o[2] or u < o[0] or u > o[1]:
                            print("CHYBA", f, r, s, "texel mimo obdelnik", u, v, o); sys.exit(1)
        out[f] = bunky
        celk[f] = plocha / (sl * rd)
    out["podil_plochy"] = {k: round(float(v), 3) for k, v in celk.items()}
    json.dump(out, open("pravidla/svet/trava_karty.json", "w"), ensure_ascii=False, indent=1)
    print("KARTY podil plochy po orezu:", out["podil_plochy"], "OK test" if "--test" in sys.argv else "")


main()
