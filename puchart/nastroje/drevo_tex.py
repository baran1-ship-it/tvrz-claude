"""Odvozené textury dřeva hradu (jpg v blender/tex nejsou v gitu – vyrobí je tento skript; volá stahni_textury_hradu.sh).
- letokruhy: čela trámů a prken (Havran vlastni._tex_endgrain; Míša 3. 11.: „víš jak vypadá řez dřeva?“), zešedlé na tón
  zvětralého dubu (čerstvě oranžová svítila)
- rough_wood_sedy: jedno prkno = jeden kus dřeva s vlákny, zešedlé jako Havran prkna_ven (grey 0,7) – hrad_vzhled.json drevo.deska
"""
import math, os, random, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
K = sys.argv[1] if len(sys.argv) > 1 else "."
T = os.path.join(K, "blender/tex")
def sedy(a, ton, sat=0.3):
    L = a.mean(2, keepdims=True); b = L * (1 - sat) + a * sat
    return np.clip(b / b.mean((0, 1)) * np.array(ton), 0, 255).astype("uint8")
R = random.Random(4); W = 512
im = Image.new("RGB", (W, W), (150, 118, 82)); d = ImageDraw.Draw(im)
for k in range(46, 0, -1):
    r = W / 2 * k / 46 * 1.02
    c = (int(150 - k * 0.9), int(118 - k * 0.95), int(82 - k * 0.8)) if k % 2 else (128, 98, 66)
    d.ellipse((W / 2 - r + R.uniform(-3, 3), W / 2 - r * 0.96, W / 2 + r, W / 2 + r * 0.96 + R.uniform(-3, 3)), fill=c)
for _ in range(6):
    a = R.uniform(0, 2 * math.pi); d.line((W / 2, W / 2, W / 2 + math.cos(a) * W * 0.46, W / 2 + math.sin(a) * W * 0.46), fill=(70, 50, 32), width=3)
im = im.filter(ImageFilter.GaussianBlur(0.8))
Image.fromarray(sedy(np.asarray(im, float), (92, 86, 77))).save(os.path.join(T, "letokruhy_Diffuse.jpg"), quality=88)
Image.new("RGB", (64, 64), (128, 128, 255)).save(os.path.join(T, "letokruhy_nor_gl.jpg"), quality=95)
a = np.asarray(Image.open(os.path.join(T, "rough_wood_Diffuse.jpg")).convert("RGB"), float)
Image.fromarray(sedy(a, (100, 97, 91))).save(os.path.join(T, "rough_wood_sedy_Diffuse.jpg"), quality=88)
shutil.copy(os.path.join(T, "rough_wood_nor_gl.jpg"), os.path.join(T, "rough_wood_sedy_nor_gl.jpg"))
# vápenná omítka (docs/reference/okna_palace.md, KCD: palác omítnutý světle) – plastered_stone_wall byla nejtmavší textura (jas 68)
a = np.asarray(Image.open(os.path.join(T, "plastered_stone_wall_Diffuse.jpg")).convert("RGB"), float)
Image.fromarray(sedy(a, (176, 168, 150), 0.25)).save(os.path.join(T, "omitka_vapno_Diffuse.jpg"), quality=88)
shutil.copy(os.path.join(T, "plastered_stone_wall_nor_gl.jpg"), os.path.join(T, "omitka_vapno_nor_gl.jpg"))
# tesaný kámen ostění: světlejší a jemnější než lomové zdivo (droba)
a = np.asarray(Image.open(os.path.join(T, "droba_Diffuse.jpg")).convert("RGB"), float)
Image.fromarray(sedy(a, (158, 150, 134), 0.35)).save(os.path.join(T, "kamen_teseny_Diffuse.jpg"), quality=88)
shutil.copy(os.path.join(T, "droba_nor_gl.jpg"), os.path.join(T, "kamen_teseny_nor_gl.jpg"))
print("drevo_tex: letokruhy, rough_wood_sedy, omitka_vapno, kamen_teseny")
