"""Zrno travy pro teren (radce 07:30 C): z atlasu trsu (obrazky/trava_atlas.png, bunky 0-2 = trava) se nahodne
narazi stovky malych trsu pri pohledu shora/zesikma do opakovatelne dlazdice 512 px (ve hre 0,8 m), vystup:
obrazky/zrno_travy.png - RGB = normala (tecna, z jasu), A = jas kolem 0,5 (stejna frekvence jako trsy).
  python3 tools/zrno_travy.py"""
import os
import random

from PIL import Image, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 512
atlas = Image.open(os.path.join(ROOT, "obrazky", "trava_atlas.png")).convert("RGBA")
cw, ch = atlas.width // 3, atlas.height // 2
rnd = random.Random(1393)
jas = Image.new("L", (N, N), 0)
for k in range(900):
    b = rnd.choice([0, 0, 1, 2])
    cell = atlas.crop(((b % 3) * cw, (b // 3) * ch, (b % 3 + 1) * cw, (b // 3 + 1) * ch))
    s = rnd.uniform(0.12, 0.22)
    t = cell.resize((max(4, int(cw * s)), max(4, int(ch * s * rnd.uniform(0.35, 0.6)))), Image.LANCZOS)
    t = t.rotate(rnd.uniform(0, 360), expand=True, resample=Image.BICUBIC)
    lum = t.convert("L")
    a = t.split()[3]
    x, y = rnd.randrange(N), rnd.randrange(N)
    for dx in (-N, 0, N):
        for dy in (-N, 0, N):
            jas.paste(lum, (x + dx, y + dy), a)
jas = jas.filter(ImageFilter.GaussianBlur(0.6))
# jas normalizovat kolem 0,5
px = list(jas.getdata())
m = sum(px) / len(px)
sd = (sum((v - m) ** 2 for v in px) / len(px)) ** 0.5 or 1.0
jas = Image.new("L", (N, N))
jas.putdata([max(0, min(255, int(128 + (v - m) / sd * 40))) for v in px])
# normala z jasu (vyska = jas), opakovatelne
h = [[jas.getpixel((x, y)) / 255.0 for x in range(N)] for y in range(N)]
nor = Image.new("RGB", (N, N))
sila = 2.5
data = []
for y in range(N):
    for x in range(N):
        dx = (h[y][(x + 1) % N] - h[y][(x - 1) % N]) * sila
        dy = (h[(y + 1) % N][x] - h[(y - 1) % N][x]) * sila
        l = (dx * dx + dy * dy + 1.0) ** 0.5
        data.append((int((-dx / l * 0.5 + 0.5) * 255), int((-dy / l * 0.5 + 0.5) * 255), int((1.0 / l * 0.5 + 0.5) * 255)))
nor.putdata(data)
out = Image.merge("RGBA", (*nor.split(), jas))
out.save(os.path.join(ROOT, "obrazky", "zrno_travy.png"))
print("zrno travy:", N, "px, prumer jasu", round(m, 1))
