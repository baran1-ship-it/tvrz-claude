"""Textury ukazatele stavu (Misa 28. 10., predloha KCD1/KCD2: bronzovy kovany ram s volutami na koncich, vlevo
vyrezavane pole, nahore cervene zivoty, pod nimi zluta vydrz, prazdna cast bily popraskany smalt).
Vystup obrazky/ui/stav_ram.png (ram s pruhlednymi okny), stav_rezba.png (vyrezavane pole), stav_prask.png (smalt),
stav_lava.png (zrnita vypln, sedotonova - hra ji barvi). Okna (px v ram.png) zapise do pravidla/svet/hrac.json
ukazatel.okna - hud.gd kresli pruhy presne do nich.
  python3 tools/hud_stav.py"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "obrazky", "ui")
R = np.random.default_rng(1393)
W, H = 1024, 112
# okna (x0, y0, x1, y1): vyrezavane pole vlevo, horni rada (zivoty), dolni rada (vydrz pres celou sirku)
OK_REZBA = (92, 26, 300, 60)
OK_ZIVOTY = (300, 26, 930, 60)
OK_VYDRZ = (92, 66, 930, 84)
OK_KOMPAS = (40, 14, 520, 52)


def sum2(w, h, sc, okt=4):
    a = np.zeros((h, w))
    for o in range(okt):
        s = sc * 2 ** o
        g = R.random((int(h / s) + 2, int(w / s) + 2))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((int(w / s + 2) * int(s), int(h / s + 2) * int(s)), Image.BICUBIC)
        a += np.asarray(im, dtype=float)[:h, :w] / 255.0 / 2 ** o
    return a / a.max()


STYL = "pergamen"          # Misa 28. 10.: vse jako puvodni HUD (KCD), ale pergamen nasi hry misto bronzu


def bronz(mask, svetlo):
    """RGBA ramu: zaklad + zkoseni (svetlo -1..1) + sum. Pergamen: svetla kuze, k okraji ztmavla (opalena),
    zkoseni slabe; bronz: kov s patinou."""
    n = sum2(mask.shape[1], mask.shape[0], 3)
    if STYL == "pergamen":
        base = np.array([0.80, 0.68, 0.48])
        hl = np.array([0.93, 0.84, 0.66])
        dk = np.array([0.42, 0.27, 0.12])
        svetlo = svetlo * 0.45
    else:
        base = np.array([0.50, 0.33, 0.15])
        hl = np.array([0.93, 0.76, 0.42])
        dk = np.array([0.16, 0.09, 0.04])
    t = np.clip(svetlo, -1, 1)[..., None]
    c = np.where(t > 0, base + (hl - base) * t, base + (base - dk) * t)
    c = c * (0.82 + 0.3 * n[..., None])
    rgba = np.zeros(mask.shape + (4,))
    rgba[..., :3] = np.clip(c, 0, 1)
    rgba[..., 3] = mask
    return rgba


def _opal(rgb, m):
    """Pergamen: okraj (vnejsi i u oken) opaleny do hneda jako list a pruhy nasi hry; bronz beze zmeny."""
    if STYL != "pergamen":
        return rgb
    vz = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.GaussianBlur(3)), dtype=float) / 255.0
    n = sum2(m.shape[1], m.shape[0], 2, 3)
    t = np.clip((1.0 - vz) * 1.6 + (n - 0.5) * 0.35, 0, 1)[..., None]
    return rgb * (1 - t) + np.array([0.33, 0.18, 0.07]) * t


def ram():
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    # hlavni deska
    d.rounded_rectangle((70, 16, 950, 94), 6, fill=255)
    # leva hlava: zaoblena deska s volutou
    d.rounded_rectangle((30, 22, 100, 88), 14, fill=255)
    # prava voluta: svisly sloupek s zavitky nahore a dole
    d.rounded_rectangle((938, 8, 958, 104), 6, fill=255)
    for cy, sg in ((14, -1), (98, 1)):
        d.arc((950, cy - 14, 990, cy + 14), 90 if sg < 0 else 180, 360 if sg < 0 else 90, fill=255, width=9)
        d.ellipse((976, cy - 6, 992, cy + 6), fill=255)
    d.arc((10, 30, 60, 80), 90, 270, fill=255, width=10)
    d.ellipse((6, 48, 22, 62), fill=255)
    m = np.asarray(im, dtype=float) / 255.0
    # okna pruhledna
    win = np.zeros_like(m)
    for x0, y0, x1, y1 in (OK_REZBA, OK_ZIVOTY, OK_VYDRZ):
        win[y0:y1, x0:x1] = 1.0
    m = m * (1.0 - win)
    # zkoseni: gradient vzdalenosti od okraje (rozmazana maska) - svetlo zleva nahore
    bl = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), dtype=float) / 255.0
    gy, gx = np.gradient(bl)
    sv = (-gy - gx * 0.5) * 9.0
    # vnitrni lem oken tmavy (vtisk) a ryhovani desky
    rgba = bronz(m, sv)
    for x0, y0, x1, y1 in (OK_REZBA, OK_ZIVOTY, OK_VYDRZ):
        rgba[y0 - 3:y0, x0 - 3:x1 + 3, :3] *= 0.45
        rgba[y1:y1 + 3, x0 - 3:x1 + 3, :3] *= 1.25
    rgba[..., :3] = np.clip(rgba[..., :3], 0, 1)
    # tmavy obrys
    obr = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)), dtype=float) / 255.0
    out = np.zeros_like(rgba)
    out[..., 3] = np.maximum(obr * 0.9, m)
    out[..., :3] = np.where(m[..., None] > 0.5, _opal(rgba[..., :3], m), np.array([0.2, 0.11, 0.04]))
    Image.fromarray((out * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "stav_ram.png"))


def rezba():
    w, h = OK_REZBA[2] - OK_REZBA[0], OK_REZBA[3] - OK_REZBA[1]
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    # rostlinny ornament: vlnovka s listky
    pts = [(x, h / 2 + math.sin(x / w * math.pi * 3) * h * 0.25) for x in range(0, w, 2)]
    d.line(pts, fill=255, width=3)
    for k in range(6):
        x = w * (k + 0.5) / 6
        y = h / 2 + math.sin(x / w * math.pi * 3) * h * 0.25
        sg = 1 if k % 2 else -1
        d.arc((x - 9, y - 9 + sg * 6, x + 9, y + 9 + sg * 6), 0, 300, fill=255, width=3)
    m = np.asarray(im.filter(ImageFilter.GaussianBlur(1.2)), dtype=float) / 255.0
    gy, gx = np.gradient(m)
    rgba = bronz(np.ones((h, w)), (-gy - gx) * 6.0)
    if STYL == "pergamen":
        rgba[..., :3] = rgba[..., :3] * (1 - 0.85 * m[..., None]) + np.array([0.2, 0.11, 0.04]) * 0.85 * m[..., None]
    else:
        rgba[..., :3] *= (0.42 + 0.58 * m)[..., None] * np.array([0.9, 0.85, 0.8])
    Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "stav_rezba.png"))


def prask():
    w, h = 256, 48
    n = sum2(w, h, 6)
    c = 0.86 + 0.1 * n
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for _ in range(26):
        x, y = R.uniform(0, w), R.uniform(0, h)
        a = R.uniform(0, math.pi)
        pts = [(x, y)]
        for _k in range(R.integers(3, 8)):
            a += R.uniform(-0.9, 0.9)
            x += math.cos(a) * R.uniform(5, 16)
            y += math.sin(a) * R.uniform(3, 9)
            pts.append((x, y))
        d.line(pts, fill=255, width=1)
    cr = np.asarray(im, dtype=float) / 255.0
    c = c * (1 - 0.45 * cr)
    rgb = np.stack([c * 0.97, c * 0.95, c * 0.9], -1)
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB").save(os.path.join(OUT, "stav_prask.png"))


def lava():
    w, h = 256, 48
    n = sum2(w, h, 5) * 0.6 + sum2(w, h, 2, 3) * 0.4
    v = 0.72 + 0.28 * n
    v *= 0.9 + 0.1 * np.linspace(1, 0, h)[:, None]       # hore svetlejsi
    Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8), "L").save(os.path.join(OUT, "stav_lava.png"))


def kompas():
    """Kompas nahore (predloha KCD1/2): bronzovy ram, pergamenove okno, uprostred zlata sipka dolu."""
    w, h = 560, 70
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((26, 8, w - 26, h - 12), 6, fill=255)
    for cx in (16, w - 16):
        d.ellipse((cx - 14, 14, cx + 14, 42), fill=255)
    d.polygon([(w / 2 - 12, h - 13), (w / 2 + 12, h - 13), (w / 2, h - 1)], fill=255)
    m = np.asarray(im, dtype=float) / 255.0
    win = np.zeros_like(m)
    x0, y0, x1, y1 = OK_KOMPAS
    win[y0:y1, x0:x1] = 1.0
    m = m * (1.0 - win)
    bl = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5)), dtype=float) / 255.0
    gy, gx = np.gradient(bl)
    rgba = bronz(m, (-gy - gx * 0.5) * 9.0)
    rgba[y0 - 2:y0, x0 - 2:x1 + 2, :3] *= 0.45
    rgba[..., :3] = np.clip(rgba[..., :3], 0, 1)
    # medailony na koncich: tmavy stred
    for cx in (16, w - 16):
        yy, xx = np.ogrid[:h, :w]
        st = (xx - cx) ** 2 + (yy - 28) ** 2 < 8 ** 2
        rgba[st, :3] = rgba[st, :3] * 0.35
    obr = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)), dtype=float) / 255.0
    out = np.zeros_like(rgba)
    out[..., 3] = np.maximum(obr * 0.9, m)
    out[..., :3] = np.where(m[..., None] > 0.5, _opal(rgba[..., :3], m), np.array([0.2, 0.11, 0.04]))
    Image.fromarray((out * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "kompas_ram.png"))
    return (w, h)


ram()
KV = kompas()
rezba()
prask()
lava()
p = os.path.join(ROOT, "pravidla", "svet", "hrac.json")
J = json.load(open(p))
J["ukazatel"]["okna"] = {"velikost": [W, H], "rezba": list(OK_REZBA), "zivoty": list(OK_ZIVOTY), "vydrz": list(OK_VYDRZ)}
J["kompas"]["okna"] = {"velikost": list(KV), "pergamen": list(OK_KOMPAS)}
json.dump(J, open(p, "w"), ensure_ascii=False, indent=1)
print("hud_stav: obrazky/ui/stav_*.png, okna do hrac.json")
