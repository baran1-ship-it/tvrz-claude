#!/usr/bin/env python3
"""Pečený atlas středního pásu trávy (plán E1, Míša 18.–20. 11., předloha docs/reference/lod_trava_video/ obr. 15–20:
dál od kamery „impostor buňky“ – jedna karta s pečenou texturou celého porostu místo desítek trsů).

Z atlasu jednotlivých trsů hra/textury/trava_atlas.png (3×2 buňky 341×256: 0 louka, 1 střední, 2 suchá, 3 byliny,
4 kapradí, 5 květy) složí široké pruhy porostu 512×128 (karta 4 : 1, ve hře ~2,4 × 0,6 m) – hustý spodek, nahoře
jednotlivá stébla, květy a byliny podle varianty. Výstup hra/textury/trava_pas_atlas.png (2 sloupce × 4 řádky),
varianty a jejich složení v pravidla/svet/louka.json pas.atlas (čte se odtud, aby data a atlas nešly od sebe).
Průhledné texely dostanou barvu sousedních stébel (rozlití) – mipmapy a ETC2 bez černých okrajů.

  python3 nastroje/trava_pas_atlas.py [kořen puchart]
"""
import json
import os
import random
import sys

from PIL import Image, ImageFilter

K = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CFG = json.load(open(os.path.join(K, "pravidla/svet/louka.json"), encoding="utf-8"))["pas"]["atlas"]
SRC = Image.open(os.path.join(K, "hra/textury/trava_atlas.png")).convert("RGBA")
SW, SH = SRC.size[0] // 3, SRC.size[1] // 2
CW, CH = int(CFG["bunka_px"][0]), int(CFG["bunka_px"][1])
SL, RA = int(CFG["sloupce"]), int(CFG["radky"])


def trs(i: int) -> Image.Image:
    c = SRC.crop(((i % 3) * SW, (i // 3) * SH, (i % 3 + 1) * SW, (i // 3 + 1) * SH))
    bb = c.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
    return c.crop(bb) if bb else c


TRSY = [trs(i) for i in range(6)]


def varianta(slozeni: dict, seed: int) -> Image.Image:
    rnd = random.Random(seed)
    out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    bunky = [int(b) for b in slozeni["trsy"]]
    vahy = [float(v) for v in slozeni["vahy"]]
    n = int(slozeni.get("pocet", 16))
    vys = slozeni.get("vyska", [0.6, 1.0])
    kusy = []
    for _ in range(n):
        b = rnd.choices(bunky, vahy)[0]
        kusy.append((rnd.random(), b))
    kusy.sort()   # zezadu dopředu (y posun = hloubka)
    for hloubka, b in kusy:
        t = TRSY[b]
        h = int(CH * rnd.uniform(vys[0], vys[1]) * (0.85 + 0.15 * hloubka))
        w = max(8, int(t.size[0] * h / t.size[1] * rnd.uniform(0.8, 1.15)))
        s = t.resize((w, h), Image.LANCZOS)
        if rnd.random() < 0.5: s = s.transpose(Image.FLIP_LEFT_RIGHT)
        # zadní trsy o kousek výš a tmavší (stín v porostu), přední u spodní hrany
        tm = 0.72 + 0.28 * hloubka
        r, g, bb, a = s.split()
        s = Image.merge("RGBA", (r.point(lambda v: int(v * tm)), g.point(lambda v: int(v * tm)), bb.point(lambda v: int(v * tm)), a))
        w = min(w, CW - 4); s = s.resize((w, h)) if s.size[0] != w else s
        x = int(rnd.uniform(0, CW - w))   # celý trs uvnitř buňky (oříznutý okraj = svislá hrana na kartě)
        y = CH - h - int((1.0 - hloubka) * CH * 0.06)
        out.alpha_composite(s, (x, max(y, 0)))
    return out


def rozlit(im: Image.Image) -> Image.Image:
    """Barva průhledných texelů z okolních stébel (alfa beze změny)."""
    a = im.getchannel("A")
    rgb = im.convert("RGB")
    plna = a.point(lambda v: 255 if v > 8 else 0)
    acc = Image.composite(rgb, Image.new("RGB", im.size, (0, 0, 0)), plna)
    m = plna
    for r in (2, 4, 8, 16, 32):
        rb = acc.filter(ImageFilter.BoxBlur(r)); mb = m.filter(ImageFilter.BoxBlur(r))
        px, pm, pr, pa = rb.load(), mb.load(), acc.load(), m.load()
        for y in range(im.size[1]):
            for x in range(im.size[0]):
                if pa[x, y] == 0 and pm[x, y] > 0:
                    k = 255.0 / pm[x, y]
                    c = px[x, y]
                    pr[x, y] = (min(255, int(c[0] * k)), min(255, int(c[1] * k)), min(255, int(c[2] * k)))
                    pa[x, y] = 255
    r, g, b = acc.split()
    return Image.merge("RGBA", (r, g, b, a))


atlas = Image.new("RGBA", (CW * SL, CH * RA), (0, 0, 0, 0))
for i, v in enumerate(CFG["varianty"]):
    atlas.alpha_composite(varianta(v, 1393 + 17 * i), ((i % SL) * CW, (i // SL) * CH))
atlas = rozlit(atlas)
cil = os.path.join(K, "hra/textury/trava_pas_atlas.png")
atlas.save(cil)
print("PAS_ATLAS %s %dx%d, %d variant" % (cil, atlas.size[0], atlas.size[1], len(CFG["varianty"])))
