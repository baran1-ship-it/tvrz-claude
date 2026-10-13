"""Velky pergamen pro napovedu: skvrnity podklad, vlakna, ztmavle a otrepane okraje (RGBA).
  python3 tools/gen_pergamen.py  -> obrazky/pergamen_velky.png"""
import numpy as np
from PIL import Image, ImageFilter

W, H = 1600, 1000
rng = np.random.default_rng(1403)


def noise(scale):
    small = rng.random((max(2, H // scale), max(2, W // scale))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


n = sum(noise(s) * w for s, w in ((160, 0.4), (60, 0.3), (20, 0.2), (6, 0.1)))
n = (n - n.min()) / (n.max() - n.min())
base = np.array([0.87, 0.76, 0.55], np.float32)
dark = np.array([0.62, 0.48, 0.3], np.float32)
col = base[None, None] * (1 - n[..., None] * 0.35) + dark[None, None] * (n[..., None] * 0.35)
# vodni skvrny
for _ in range(4):
    cx, cy, r = rng.random() * W, rng.random() * H, 60 + rng.random() * 180
    yy, xx = np.ogrid[:H, :W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    ring = np.exp(-((d - 1.0) ** 2) / 0.05) * 0.035 + np.clip(1 - d, 0, 1) ** 2 * 0.05
    col *= (1 - ring[..., None] * np.array([0.6, 0.8, 1.0]))
# vlakna
fib = Image.fromarray((rng.random((H, W)) * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(0)).resize((W // 8, H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
fib = np.asarray(fib, np.float32) / 255.0
col *= (0.96 + fib[..., None] * 0.06)
# okraje: ztmaveni a otrepany obrys
yy, xx = np.mgrid[:H, :W].astype(np.float32)
edge = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
wob = noise(25) * 12 + noise(90) * 22 + noise(6) * 5
e = edge - wob
burn = np.clip(1 - e / 80.0, 0, 1) ** 2.0
col *= (1 - burn[..., None] * np.array([0.55, 0.62, 0.72]))
alpha = np.clip((e - 6) / 4.0, 0, 1)
out = np.dstack([np.clip(col, 0, 1), alpha]) * 255
Image.fromarray(out.astype(np.uint8), "RGBA").save("obrazky/pergamen_velky.png", optimize=True)
print("ok")
