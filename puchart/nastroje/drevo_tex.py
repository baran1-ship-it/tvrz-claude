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
import json as _json
_DV = _json.load(open(os.path.join(K, "pravidla/svet/hrad_vzhled.json"))).get("drevo", {})
TON_P = tuple(_DV.get("ton_prken", [100, 97, 91])); SAT_P = float(_DV.get("sytost_prken", 0.3))   # Míša 13. 11.: hnědé opotřebované, ne šedé
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
Image.fromarray(sedy(a, TON_P, SAT_P)).save(os.path.join(T, "rough_wood_sedy_Diffuse.jpg"), quality=88)
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
# atlas prken (Míša 4. 11.: „most pořád vypadá jako jeden rastr“ – textura 0,6 m s vlákny NAPŘÍČ prkna a suky opakovanými po
# 0,6 m na každém prkně): 8 různých prken pod sebou, vlákna podél délky, jedno prkno = 2,56 × 0,32 m bez opakování;
# kit.plank vybírá řádek náhodně (blender/hrady.py TEX prkno_ven, vel 2,56)
src = np.rot90(np.asarray(Image.open(os.path.join(T, "rough_wood_Diffuse.jpg")).convert("RGB"), float), 1)
nsrc = np.rot90(np.asarray(Image.open(os.path.join(T, "rough_wood_nor_gl.jpg")).convert("RGB"), float), 1).copy()
nsrc = nsrc[..., [1, 0, 2]]; nsrc[..., 0] = 255 - nsrc[..., 0]   # otočení normálové mapy o 90°
R2 = random.Random(11); atl = np.zeros((1024, 1024, 3)); atn = np.zeros((1024, 1024, 3))
for k in range(8):
    y0 = R2.randrange(0, 1024 - 128); sh = R2.randrange(0, 1024)
    blk = np.roll(src[y0:y0 + 128], sh, axis=1); nb = np.roll(nsrc[y0:y0 + 128], sh, axis=1)
    if R2.random() < 0.5: blk = blk[:, ::-1]; nb = nb[:, ::-1].copy(); nb[..., 0] = 255 - nb[..., 0]
    ton = np.array(TON_P) * R2.uniform(0.82, 1.12) * np.array([R2.uniform(0.97, 1.04), 1.0, R2.uniform(0.94, 1.0)])
    atl[k * 128:(k + 1) * 128] = sedy(blk, tuple(ton), SAT_P); atn[k * 128:(k + 1) * 128] = nb
    atl[k * 128:k * 128 + 2] *= 0.55; atl[(k + 1) * 128 - 2:(k + 1) * 128] *= 0.55   # hrana prkna
Image.fromarray(atl.clip(0, 255).astype("uint8")).save(os.path.join(T, "prkna_atlas_Diffuse.jpg"), quality=88)
Image.fromarray(atn.clip(0, 255).astype("uint8")).save(os.path.join(T, "prkna_atlas_nor_gl.jpg"), quality=92)
print("drevo_tex: prkna_atlas (8 prken)")
