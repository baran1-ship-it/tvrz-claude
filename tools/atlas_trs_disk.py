"""Bunka 1 atlasu travy (vysoka trava, byla nejridsi) z trsu grass_filed.glb z Misova Disku (radce 07:45):
textura trsu 512 RGBA (alpha MASK), model 1 708 troj. se nepouziva - nas trs zustava 3 karty. Dva trsy vedle sebe
(druhy zrcadleny, mensi), spodek na spodku bunky; barva se rozleje do pruhlednych pixelu (mipmapy bez lemu).
Spusteni: python3 tools/atlas_trs_disk.py  (vstup blender/tex_cache/grass_filed_trs.png, vystup obrazky/trava_atlas.png)."""
import os
import numpy as np
from PIL import Image, ImageFilter

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# vstup = puvodni atlas z blender/atlas_travy.py (skript se nesmi spoustet na uz upraveny atlas dvakrat)
PUV = os.path.join(KOREN, "blender", "tex_cache", "trava_atlas_blender.png")
if not os.path.exists(PUV):
    Image.open(os.path.join(KOREN, "obrazky", "trava_atlas.png")).save(PUV)
atlas = Image.open(PUV).convert("RGBA")
trs = Image.open(os.path.join(KOREN, "blender", "tex_cache", "grass_filed_trs.png")).convert("RGBA")
a = np.asarray(trs)
m = a[..., 3] > 127
ys, xs = np.where(m)
trs = trs.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
BW, BH = 341, 256
x0, y0 = 341, 0                       # bunka 1 (sloupec 1, radek 0)
bunka = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
for sx, h, mir in ((0.30, 250, False), (0.70, 215, True)):
    t = trs.resize((int(trs.width * h / trs.height), h), Image.LANCZOS)
    if mir:
        t = t.transpose(Image.FLIP_LEFT_RIGHT)
    bunka.alpha_composite(t, (int(BW * sx - t.width / 2), BH - h - 2))
# alfa ostra (MASK), barva rozlita do pruhlednych pixelu
b = np.asarray(bunka).astype(np.float32)
al = (b[..., 3] > 127).astype(np.float32)
rgb = b[..., :3] * al[..., None]
w = al.copy()
for _ in range(12):
    im_rgb = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    im_w = Image.fromarray((w * 255).astype(np.uint8))
    rgb_b = np.asarray(im_rgb.filter(ImageFilter.BoxBlur(2))).astype(np.float32)
    w_b = np.asarray(im_w.filter(ImageFilter.BoxBlur(2))).astype(np.float32) / 255.0
    nov = (w < 0.5) & (w_b > 0.01)
    rgb[nov] = rgb_b[nov] / w_b[nov][:, None]
    w[nov] = 1.0
# barvu srovnat s bunkou 0 (nizka trava z Poly Haven) - jinak by trsy v louce svitily jinou zeleni
ref = np.asarray(atlas).astype(np.float32)[0:BH, 0:BW]
rm = ref[..., 3] > 127
k = ref[..., :3][rm].mean(0) / np.maximum(rgb[al > 0.5].mean(0), 1.0)
rgb = rgb * (0.5 + 0.5 * k)            # pul cesty: trs si necha vlastni kresbu
out = np.dstack([np.clip(rgb, 0, 255), al * 255]).astype(np.uint8)
cela = np.asarray(atlas).copy()
cela[y0:y0 + BH, x0:x0 + BW] = out
Image.fromarray(cela).save(os.path.join(KOREN, "obrazky", "trava_atlas.png"))
print("bunka 1 atlasu z grass_filed: pokryti %.0f %%, barva x %s" % (al.mean() * 100, np.round(0.5 + 0.5 * k, 2)))
