"""Atlas drnu-vejire (radce 09:10): husty nizky porost na karte, ne jednotlive trsy. Z bunek obrazky/trava_atlas.png
a obrazky/drn_atlas.png posklada 4 bunky 512x512: spodek karty (v = 1, u paty) nepruhledny husty porost, nahoru
ridne az do roztrepanych spicek. Vystup obrazky/vejir_atlas.png (2 x 2 bunky). Spousti se jen pri zmene atlasu.
  python3 tools/vejir_atlas.py"""
import random
from PIL import Image, ImageFilter

ROOT = __file__.rsplit("/tools/", 1)[0]
C = 512


def bunky(path, sl, rd):
    im = Image.open(path).convert("RGBA")
    w, h = im.size[0] // sl, im.size[1] // rd
    out = []
    for j in range(rd):
        for i in range(sl):
            b = im.crop((i * w, j * h, (i + 1) * w, (j + 1) * h))
            bb = b.getbbox()
            if bb:
                out.append(b.crop(bb))
    return out


trsy = bunky(ROOT + "/obrazky/trava_atlas.png", 3, 2)[:4]          # nizka, stredni, vysoka (bez suche a bylin)
drny = bunky(ROOT + "/obrazky/drn_atlas.png", 3, 4)[3:]            # husty drn (bez rozcuchanych chomacu nahore)
atlas = Image.new("RGBA", (C * 2, C * 2), (0, 0, 0, 0))
for k in range(4):
    rng = random.Random(1393 + k)
    cell = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    # podklad: spodni 45 % souvisla zelen (stin uvnitr porostu), nahore roztrepana hranice
    base = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    px = base.load()
    for y in range(C):
        for x in range(C):
            t = y / C
            if t > 0.55 + 0.06 * rng.random():
                g = 0.75 + 0.25 * rng.random()
                px[x, y] = (int(52 * g), int(70 * g), int(22 * g), 255)
    cell.alpha_composite(base.filter(ImageFilter.GaussianBlur(1.2)))
    # trsy od zadu dopredu (pata nahodne 45-100 % vysky), mensi vzadu
    stoupy = []
    for _ in range(170):
        stoupy.append(0.42 + 0.58 * rng.random())
    for py in sorted(stoupy):
        src = rng.choice(drny + trsy)
        hh = int(C * (0.25 + 0.35 * rng.random()) * (0.6 + 0.4 * py))
        ww = max(4, int(src.size[0] * hh / src.size[1]))
        t = src.resize((ww, hh), Image.LANCZOS)
        if rng.random() < 0.5:
            t = t.transpose(Image.FLIP_LEFT_RIGHT)
        x = int(rng.random() * (C + ww)) - ww
        y = int(py * C) - hh
        cell.alpha_composite(t, (max(x, -ww + 1), y) if x >= 0 else (0, y))
    # spodni pas (pata) zcela nepruhledny
    px = cell.load()
    for y in range(int(C * 0.8), C):
        for x in range(C):
            r, g, b, a = px[x, y]
            if a < 255:
                px[x, y] = (int(r * a / 255 + 46 * (1 - a / 255)), int(g * a / 255 + 62 * (1 - a / 255)),
                            int(b * a / 255 + 20 * (1 - a / 255)), 255)
    atlas.alpha_composite(cell, ((k % 2) * C, (k // 2) * C))
atlas.save(ROOT + "/obrazky/vejir_atlas.png")
print("vejir_atlas.png", atlas.size)
