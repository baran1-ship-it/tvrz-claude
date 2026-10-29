"""Textura dreveneho sindele (Misa 29. 10.: stodola a kulna podle KCD se sindelovou strechou). Peceni z geometrie
(blender/bake_tex.py sindel) davalo cernou barvu (prumer 3/255 - i ve hre modely/textury/sindel_diff.jpg). Tady
primo z fotografie prken (tex_cache/prkna_ven, CC0 Poly Haven): dlazdice 1,5 x 1,5 m, 7 rad na metr, sindele
sirky 8-16 cm se stridanymi sparami, kazdy vyrez prkna jinak posunuty a tonovany (zesedle drevo), stin pod radou,
spary, misty mech u spodni hrany. Vystup diff/nor/disp/rough 2k a 1k do blender/tex_cache a modely/textury/sindel_*.
  /opt/bl/bin/python tools/sindel_tex.py"""
import os
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TC = os.path.join(ROOT, "blender", "tex_cache")
N = 2048
SIZE = 1.5
RADY = int(7 * SIZE)                      # rad na dlazdici
rng = np.random.default_rng(11)
wood = np.asarray(Image.open(os.path.join(TC, "prkna_ven_diff_2k.jpg")).convert("RGB")).astype(np.float32) / 255
W = wood.shape[0]
diff = np.zeros((N, N, 3), np.float32)
vys = np.zeros((N, N), np.float32)
rad_px = N / RADY
for r in range(RADY):
    y0 = int(round(r * rad_px))
    y1 = int(round((r + 1) * rad_px))
    x = int(rng.uniform(0, 60))
    while x < N + 200:
        w = int(rng.uniform(0.08, 0.16) / SIZE * N)
        # vyrez prkna: svisla vlakna (prkna_ven ma vlakna vodorovne -> transpozice)
        sx, sy = rng.integers(0, W - 200), rng.integers(0, W - 200)
        h = y1 - y0
        kus = wood[sy:sy + h, sx:sx + w] if wood[sy:sy + h, sx:sx + w].shape[:2] == (h, w) else wood[:h, :w]
        j = rng.uniform(0.85, 1.12)
        ton = np.array([j * rng.uniform(0.97, 1.03), j * rng.uniform(0.95, 1.0), j * rng.uniform(0.9, 0.96)], np.float32)
        sedy = rng.uniform(0.6, 0.85)                  # zesednuti sluncem a destem
        g = kus.mean(axis=2, keepdims=True)
        kus = (kus * (1 - sedy) + g * sedy * np.array([1.0, 0.96, 0.9])) * ton
        for xx in range(w):
            X = (x + xx) % N
            diff[y0:y1, X] = kus[:, xx]
            # vyska: spodni hrana rady (y1) nejvys, ke hlave (y0) klesa pod dalsi radu; okraj sindele nize
            t = np.linspace(0.35, 1.0, y1 - y0)
            hr = 1.0 - min(xx, w - 1 - xx) * 0.0
            vys[y0:y1, X] = t * (0.9 if xx in (0, w - 1) else 1.0) * hr
        x += w + int(rng.uniform(0, 2))
# spary mezi sindeli (tmave svisle cary) a stin pod spodni hranou rady
gx = np.abs(np.diff(vys, axis=1, append=vys[:, :1]))
spara = (gx > 0.05).astype(np.float32)
spara = np.asarray(Image.fromarray((spara * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
ao = np.clip(0.62 + 0.55 * vys ** 0.8, 0, 1.1)
# zesvetleni: zesedly sindel (KCD) je svetle sedohnedy, ne tmavy
GAIN = 1.45
# mech u spodnich hran (sever, vlhko): skvrny
m = rng.random((N // 64, N // 64))
mech = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)).astype(np.float32) / 255
mech = np.clip((mech - 0.62) * 4, 0, 1) * np.clip((vys - 0.75) * 4, 0, 1)
out = diff * GAIN * ao[..., None] * (1 - 0.5 * spara[..., None])
out = out * (1 - mech[..., None] * 0.6) + np.array([0.24, 0.27, 0.12]) * mech[..., None] * 0.6
# normala z vysky
h = np.asarray(Image.fromarray((vys * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
dy, dx = np.gradient(h)
s = 6.0
nx, ny, nz = -dx * s * 10, dy * s * 10, np.ones_like(h)
L = np.sqrt(nx * nx + ny * ny + nz * nz)
nor = np.stack([nx / L, ny / L, nz / L], -1) * 0.5 + 0.5
rough = np.full((N, N), 0.82, np.float32) + mech * 0.1
for res, nn in (("2k", N), ("1k", N // 2)):
    for kind, arr in (("diff", out), ("nor", nor), ("disp", vys), ("rough", rough)):
        a = np.clip(arr, 0, 1)
        im = Image.fromarray((a * 255).astype(np.uint8))
        if nn != N:
            im = im.resize((nn, nn), Image.LANCZOS)
        im.save(os.path.join(TC, "sindel_%s_%s.jpg" % (kind, res)), quality=92)
for kind in ("diff", "nor", "disp", "rough"):
    Image.open(os.path.join(TC, "sindel_%s_1k.jpg" % kind)).save(os.path.join(ROOT, "modely", "textury", "sindel_%s.jpg" % kind), quality=92)
print("sindel: prumer barvy", (out.mean(axis=(0, 1)) * 255).astype(int))
