"""Mapa panstvi na pergamenu (obrazky/mapa.png) kreslena jako stara rucni mapa: zestarly pergamen se skvrnami,
kopce stinovane sepii, lesy ze stromecku, pole v honech s lany, cesty dvojitou carou, ves s chaloupkami,
tvrz jako hradek, skalni mesto, rybnik s vlnkami, zdobny ramecek, kartus s nazvem a vetrna ruzice.
Nazvy mist jsou soucasti obrazu (Tvrz Havran, Lhota); hra kresli jen erby a polohu hrace.
  /opt/bl/bin/python tools/gen_mapa.py
Souradnice: x doprava, z dolu (sever nahore); rozsah = herni plocha hrace (player.gd AREA)."""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "blender"))

import fort  # noqa: E402
import kraj  # noqa: E402
import vesnice  # noqa: E402

X0, X1, Z0, Z1 = -240.0, 890.0, -240.0, 1340.0
KROK = 2.5                      # vzorkovani terenu (m)
S = 3                           # px na vzorek -> 0.83 m/px
OUT = os.path.join(ROOT, "obrazky", "mapa.png")
INK = (58, 36, 20)
INK_A = (58, 36, 20, 255)
FB = os.path.join(ROOT, "fonts", "GrenzeGotisch-Bold.ttf")
FM = os.path.join(ROOT, "fonts", "GrenzeGotisch-Medium.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


def sample():
    nx, nz = int((X1 - X0) / KROK) + 1, int((Z1 - Z0) / KROK) + 1
    H = np.zeros((nz, nx), np.float32)
    G = np.zeros((nz, nx), np.float32)
    LES = np.zeros((nz, nx), np.float32)
    POLE = np.zeros((nz, nx), np.float32)
    LAN = np.zeros((nz, nx), np.float32)       # 1 = mez mezi lany (srafura)
    for k in range(nz):
        z = Z0 + k * KROK
        for i in range(nx):
            x = X0 + i * KROK
            H[k, i] = fort.land(x, z)
            g, les, pole = kraj.ground_attrs(x, z)
            G[k, i], LES[k, i], POLE[k, i] = g, les, pole
            if pole > 0.5:
                h, edge, t, w = kraj.hon(x, z)
                f = t / w - math.floor(t / w)
                LAN[k, i] = 1.0 if (f < 0.16 or edge < 3.0) else 0.0
        if k % 60 == 0:
            print("mapa: radek %d/%d" % (k, nz), flush=True)
    return H, G, LES, POLE, LAN


def main():
    H, G, LES, POLE, LAN = sample()
    nz, nx = H.shape
    W, Hh = nx * S, nz * S

    def up(a, res=Image.BICUBIC):
        return np.array(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((W, Hh), res), np.float32) / 255.0
    gz, gx = np.gradient(H, KROK)
    shade = np.clip(0.5 + (-gx * 0.75 - gz * 0.75) * 0.9, 0.0, 1.0)
    shade_u, les_u, pole_u, g_u, lan_u = up(shade), up(LES), up(POLE), up(G), up(LAN, Image.NEAREST)
    rng = np.random.default_rng(7)

    def blotch(scale, n=1):
        a = rng.random((Hh // scale + 2, W // scale + 2)).astype(np.float32)
        im = Image.fromarray((a * 255).astype(np.uint8)).resize((W, Hh), Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale * 0.4))
        return np.array(im, np.float32) / 255.0
    # pergamen: teply zaklad, velke skvrny, vlakna, zestarle (ztmavle) okraje
    paper = np.array([0.90, 0.82, 0.64], np.float32)
    img = np.ones((Hh, W, 3), np.float32) * paper
    b1, b2, b3 = blotch(90), blotch(30), blotch(6)
    img *= (0.88 + 0.16 * b1)[..., None]
    img *= (0.95 + 0.07 * b2)[..., None]
    img *= (0.97 + 0.04 * b3)[..., None]
    stain = np.clip((blotch(140) - 0.72) * 4.0, 0, 1)
    img = img * (1 - stain[..., None] * 0.18) + np.array([0.62, 0.45, 0.25]) * stain[..., None] * 0.18
    # krajina akvarelem: louky do zelenoseda, pole okrova, lesy olivove, hlina hneda
    meadow = np.array([0.80, 0.79, 0.58], np.float32)
    field = np.array([0.86, 0.72, 0.45], np.float32)
    forest = np.array([0.52, 0.56, 0.36], np.float32)
    dirt = np.array([0.74, 0.60, 0.42], np.float32)
    img = img * 0.62 + meadow * 0.38
    pm = pole_u * (0.85 + 0.15 * b2)
    img = img * (1 - pm[..., None] * 0.65) + field * pm[..., None] * 0.65
    img = img * (1 - (pm * lan_u * 0.35)[..., None]) + np.array([0.55, 0.42, 0.25]) * (pm * lan_u * 0.35)[..., None]
    lm = np.clip(les_u * 1.2, 0, 1)
    img = img * (1 - lm[..., None] * 0.55) + forest * lm[..., None] * 0.55
    dm = np.clip((0.45 - g_u) / 0.3, 0, 1) * (1 - pole_u)
    img = img * (1 - dm[..., None] * 0.5) + dirt * dm[..., None] * 0.5
    # kopce sepii (stin od severozapadu) a jemne vrstevnice po 4 m
    img *= (0.78 + 0.4 * shade_u)[..., None]
    Hu = np.array(Image.fromarray(H).resize((W, Hh), Image.BICUBIC), np.float32)
    cont = np.abs(((Hu / 4.0) % 1.0) - 0.5) > 0.475
    img[cont] = img[cont] * 0.88 + np.array([0.45, 0.32, 0.18]) * 0.12
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    px = S / KROK                       # px na metr

    def P(x, z):
        return ((x - X0) * px, (z - Z0) * px)
    R = random.Random(3)
    # kopce: rucni srafy (hachures) na strmych svazich, kolmo po spadu
    for _ in range(26000):
        x, z = R.uniform(X0, X1), R.uniform(Z0, Z1)
        i, k = int((x - X0) / KROK), int((z - Z0) / KROK)
        if not (0 < i < nx - 1 and 0 < k < nz - 1):
            continue
        sx, sz = gx[k, i], gz[k, i]
        sl = math.hypot(sx, sz)
        if sl < 0.2 or LES[k, i] > 0.5:
            continue
        ln = min(9.0, 3.0 + sl * 18.0)
        cx, cy = P(x, z)
        ux, uy = sx / sl, sz / sl
        d.line([(cx, cy), (cx + ux * ln, cy + uy * ln)], fill=(90, 62, 36, int(min(150, 50 + sl * 260))), width=1)
    # lesy: stromecky inkoustem s barevnou korunou (jehlicnany trojuhelnik, listnace kulate), od severu dolu
    trees = []
    for _ in range(16000):
        x, z = R.uniform(X0, X1), R.uniform(Z0, Z1)
        if kraj.forest(x, z) < 0.55:
            continue
        trees.append((z, x))
    trees.sort()
    for z, x in trees:
        cx, cy = P(x, z)
        r = R.uniform(4.0, 6.5)
        d.line([(cx, cy + r * 0.4), (cx, cy + r * 1.5)], fill=(70, 48, 28, 230), width=2)
        if R.random() < 0.62:
            pts = [(cx, cy - r * 1.9), (cx - r * 0.95, cy + r * 0.55), (cx + r * 0.95, cy + r * 0.55)]
            d.polygon(pts, fill=(78, 92, 52, 235), outline=(40, 34, 20, 255))
        else:
            d.ellipse([cx - r, cy - r * 1.05, cx + r, cy + r * 0.75], fill=(98, 108, 58, 235), outline=(40, 34, 20, 255))
    # skalni mesto: piskovcove vezicky
    for (ax, az), (bx, bz) in zip(kraj.HREBEN[:-1], kraj.HREBEN[1:]):
        L = math.hypot(bx - ax, bz - az)
        for k in range(int(L / 8)):
            t = k * 8 / L
            zz = az + (bz - az) * t
            if not (250 < zz < 880) or R.random() < 0.35:
                continue
            x, z = ax + (bx - ax) * t + R.gauss(0, 7), zz + R.gauss(0, 7)
            cx, cy = P(x, z)
            w_, h_ = R.uniform(4, 7), R.uniform(10, 20)
            pts = [(cx - w_, cy + 3), (cx - w_ * 0.8, cy - h_ * 0.7), (cx - w_ * 0.2, cy - h_), (cx + w_ * 0.5, cy - h_ * 0.85), (cx + w_, cy + 3)]
            d.polygon(pts, fill=(196, 170, 128, 255), outline=INK_A)
            d.line([(cx - w_ * 0.3, cy - h_ * 0.6), (cx - w_ * 0.4, cy)], fill=(90, 62, 36, 200), width=1)
    # rybnik
    au = (math.cos(vesnice.AXIS), math.sin(vesnice.AXIS))
    av = (-math.sin(vesnice.AXIS), math.cos(vesnice.AXIS))
    pu, pv, ru, rv = vesnice.POND
    poly = []
    for k in range(40):
        a = k / 40 * math.tau
        u, v = pu + math.cos(a) * ru, pv + math.sin(a) * rv
        poly.append(P(kraj.VES[0] + au[0] * u + av[0] * v, kraj.VES[1] + au[1] * u + av[1] * v))
    d.polygon(poly, fill=(132, 150, 140, 255), outline=INK_A)
    pc = P(kraj.VES[0] + au[0] * pu + av[0] * pv, kraj.VES[1] + au[1] * pu + av[1] * pv)
    for k in range(3):
        y = pc[1] - 6 + k * 6
        d.arc([pc[0] - 10, y - 3, pc[0], y + 3], 200, 340, fill=(60, 80, 80, 255))
        d.arc([pc[0], y - 3, pc[0] + 10, y + 3], 200, 340, fill=(60, 80, 80, 255))
    # potok Bystrice: modrozelena stuha s inkoustovym okrajem, vlnky
    rp = [P(x, z) for x, z in kraj.REKA]
    d.line(rp, fill=INK_A, width=int(11 * px + 4), joint="curve")
    d.line(rp, fill=(118, 146, 150, 255), width=int(11 * px), joint="curve")
    for k in range(0, len(rp) - 2, 9):
        (x0_, y0_), (x1_, y1_) = rp[k], rp[k + 2]
        d.line([(x0_ * 0.7 + x1_ * 0.3, y0_ * 0.7 + y1_ * 0.3), (x0_ * 0.3 + x1_ * 0.7, y0_ * 0.3 + y1_ * 0.7)], fill=(70, 96, 104, 255), width=1)
    # cesty: dvojita inkoustova cara s okrovou vyplni
    for path, w in kraj.CESTY:
        pts = [P(x, z) for x, z in path]
        d.line(pts, fill=INK_A, width=int(w * 2 * px + 5), joint="curve")
        d.line(pts, fill=(214, 182, 128, 255), width=int(w * 2 * px + 1), joint="curve")
    for pts, hw in vesnice.ves_paths():
        q = [P(x, z) for x, z in pts]
        d.line(q, fill=(176, 140, 96, 230), width=max(3, int((hw or 2.5) * 1.6 * px)), joint="curve")
    # chaloupky: obrazek domku se strechou (stit), chlevy mensi
    for h in vesnice.layout():
        for kk, (c, yaw, L, Wd) in enumerate(((h["p"], h["yaw"], h["L"], h["W"]), h["barn"])):
            cx, cy = P(c.x, c.z)
            s_ = 1.25 if kk == 0 else 0.95
            bw, bh = 15 * s_, 10 * s_
            d.rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], fill=(226, 206, 168, 255), outline=INK_A, width=2)
            d.polygon([(cx - bw / 2 - 3, cy - bh / 2), (cx, cy - bh / 2 - 11 * s_), (cx + bw / 2 + 3, cy - bh / 2)],
                      fill=(150, 70, 44, 255), outline=INK_A)
            d.rectangle([cx - 2, cy + bh / 2 - 6, cx + 2, cy + bh / 2], fill=INK_A)
    # most pres potok: prkenna lavka se zabradlim
    br = kraj.bridge()
    if br:
        bx, bz, ddx, ddz = br
        c0, c1 = P(bx - ddx * 10, bz - ddz * 10), P(bx + ddx * 10, bz + ddz * 10)
        nx_, nz_ = -ddz * 3.2 * px, ddx * 3.2 * px
        poly = [(c0[0] + nx_, c0[1] + nz_), (c1[0] + nx_, c1[1] + nz_), (c1[0] - nx_, c1[1] - nz_), (c0[0] - nx_, c0[1] - nz_)]
        d.polygon(poly, fill=(170, 120, 70, 255), outline=INK_A)
        for k in range(1, 8):
            t = k / 8
            p0 = (poly[0][0] * (1 - t) + poly[1][0] * t, poly[0][1] * (1 - t) + poly[1][1] * t)
            p1 = (poly[3][0] * (1 - t) + poly[2][0] * t, poly[3][1] * (1 - t) + poly[2][1] * t)
            d.line([p0, p1], fill=(90, 60, 34, 255), width=1)
    # boží muka na krizovatce
    cx, cy = P(kraj.CROSS[0] + 6.5, kraj.CROSS[1] + 5.0)
    d.line([(cx, cy + 8), (cx, cy - 14)], fill=INK_A, width=3)
    d.line([(cx - 6, cy - 7), (cx + 6, cy - 7)], fill=INK_A, width=3)
    # tvrz: hradek (hradba se zuby, vez se strechou)
    cx, cy = P(-1.0, 0.0)
    ww, wh = 70, 34
    d.rectangle([cx - ww / 2, cy - wh / 2 + 10, cx + ww / 2, cy + wh / 2 + 10], fill=(222, 204, 166, 255), outline=INK_A, width=3)
    for k in range(8):
        x0 = cx - ww / 2 + k * ww / 7.5
        d.rectangle([x0, cy - wh / 2 + 4, x0 + 5, cy - wh / 2 + 10], fill=(222, 204, 166, 255), outline=INK_A)
    d.rectangle([cx - 7, cy + 12, cx + 7, cy + wh / 2 + 10], fill=INK_A)           # brana
    d.rectangle([cx - ww / 2 + 6, cy - 34, cx - ww / 2 + 26, cy + 8], fill=(222, 204, 166, 255), outline=INK_A, width=3)   # vez
    d.polygon([(cx - ww / 2 + 2, cy - 34), (cx - ww / 2 + 16, cy - 58), (cx - ww / 2 + 30, cy - 34)], fill=(150, 70, 44, 255), outline=INK_A)
    d.line([(cx - ww / 2 + 16, cy - 58), (cx - ww / 2 + 16, cy - 70)], fill=INK_A, width=2)
    d.polygon([(cx - ww / 2 + 16, cy - 70), (cx - ww / 2 + 27, cy - 66), (cx - ww / 2 + 16, cy - 62)], fill=(150, 30, 24, 255))
    d.rectangle([cx + 6, cy - 18, cx + ww / 2 - 6, cy + 6], fill=(222, 204, 166, 255), outline=INK_A, width=2)   # palac
    d.polygon([(cx + 3, cy - 18), (cx + 18, cy - 32), (cx + ww / 2 - 3, cy - 18)], fill=(120, 96, 70, 255), outline=INK_A)
    # popisky (gotickym pismem s pergamenovym podkladem)
    def label(x, z, text, size, dx=0, dy=0, fnt=FB):
        f = font(fnt, size)
        cx, cy = P(x, z)
        cx, cy = cx + dx, cy + dy
        bb = d.textbbox((0, 0), text, font=f)
        tw = bb[2] - bb[0]
        for ox in (-2, -1, 0, 1, 2):
            for oy in (-2, -1, 0, 1, 2):
                d.text((cx - tw / 2 + ox, cy + oy), text, font=f, fill=(236, 222, 186, 200))
        d.text((cx - tw / 2, cy), text, font=f, fill=INK_A)
    label(0, 0, "Tvrz Havran", 54, dx=150, dy=-20)
    label(kraj.VES[0], kraj.VES[1], "Lhota", 58, dx=0, dy=-150)
    label(-170, 560, "Skalní město", 34, dx=40, dy=0, fnt=FM)
    label(kraj.CROSS[0], kraj.CROSS[1], "Boží muka", 28, dx=70, dy=-10, fnt=FM)
    rx, rz = kraj.REKA[len(kraj.REKA) * 2 // 3]
    label(rx, rz, "Bystřice", 32, dx=70, dy=0, fnt=FM)
    # okraj: ztmaveni pergamenu a otrhany okraj
    arr = np.array(im, np.float32) / 255.0
    yy, xx = np.mgrid[0:Hh, 0:W]
    e = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, Hh - 1 - yy)).astype(np.float32)
    burn = np.clip(1.0 - (e - 10.0 + 30.0 * (b1 - 0.5)) / 110.0, 0, 1)
    arr[..., :3] = arr[..., :3] * (1 - burn[..., None] * 0.5) + np.array([0.42, 0.27, 0.12]) * burn[..., None] * 0.5
    torn = e < (8 + 10 * b2)
    arr[torn, 3] = 0.0
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    # zdobny ramecek: dvojita linka, mezi nimi stridave pole (jako lemovka), rohove ornamenty
    m0, m1 = 34, 52
    d.rectangle([m0, m0, W - m0, Hh - m0], outline=INK_A, width=4)
    d.rectangle([m1, m1, W - m1, Hh - m1], outline=INK_A, width=2)
    step = 26
    for x in range(m0 + 4, W - m0 - 4, step):
        c = (150, 40, 30, 220) if (x // step) % 2 else (190, 150, 70, 220)
        d.rectangle([x, m0 + 4, min(x + step - 4, W - m0 - 4), m1 - 4], fill=c)
        d.rectangle([x, Hh - m1 + 4, min(x + step - 4, W - m0 - 4), Hh - m0 - 4], fill=c)
    for y in range(m0 + 4, Hh - m0 - 4, step):
        c = (150, 40, 30, 220) if (y // step) % 2 else (190, 150, 70, 220)
        d.rectangle([m0 + 4, y, m1 - 4, min(y + step - 4, Hh - m0 - 4)], fill=c)
        d.rectangle([W - m1 + 4, y, W - m0 - 4, min(y + step - 4, Hh - m0 - 4)], fill=c)
    for cx, cy in ((m0 + 9, m0 + 9), (W - m0 - 9, m0 + 9), (m0 + 9, Hh - m0 - 9), (W - m0 - 9, Hh - m0 - 9)):
        d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(150, 40, 30, 255), outline=INK_A, width=3)
        d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(206, 170, 80, 255), outline=INK_A, width=2)
        for a in range(4):
            an = a * math.pi / 2 + math.pi / 4
            d.polygon([(cx + math.cos(an) * 6, cy + math.sin(an) * 6), (cx + math.cos(an + 0.3) * 24, cy + math.sin(an + 0.3) * 24),
                       (cx + math.cos(an - 0.3) * 24, cy + math.sin(an - 0.3) * 24)], fill=INK_A)
    # kartus s nazvem (svitek) vlevo dole
    cw, ch = 420, 150
    x0, y0 = 90, Hh - 90 - ch
    d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=22, fill=(236, 220, 180, 245), outline=INK_A, width=4)
    d.rounded_rectangle([x0 + 10, y0 + 10, x0 + cw - 10, y0 + ch - 10], radius=16, outline=(150, 40, 30, 255), width=2)
    for sx in (x0 - 18, x0 + cw - 2):
        d.ellipse([sx, y0 + 10, sx + 20, y0 + ch - 10], fill=(214, 194, 150, 255), outline=INK_A, width=3)
    f1, f2 = font(FB, 52), font(FM, 28)
    t1, t2 = "Panství Havran", "Léta Páně MCCCXCIV"
    b = d.textbbox((0, 0), t1, font=f1)
    d.text((x0 + cw / 2 - (b[2] - b[0]) / 2, y0 + 22), t1, font=f1, fill=INK_A)
    b = d.textbbox((0, 0), t2, font=f2)
    d.text((x0 + cw / 2 - (b[2] - b[0]) / 2, y0 + 92), t2, font=f2, fill=(110, 40, 30, 255))
    # vetrna ruzice vpravo nahore: osmicipa hvezda, sever se zlatou spickou a pismenem
    cx, cy = W - 150, 170
    for k in range(8):
        a = k * math.pi / 4 - math.pi / 2
        ln = 92 if k % 2 == 0 else 52
        for half, col in ((-1, (150, 40, 30, 255) if k == 0 else INK_A), (1, (226, 206, 160, 255))):
            tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
            side = (cx + math.cos(a + half * 0.4) * 16, cy + math.sin(a + half * 0.4) * 16)
            d.polygon([(cx, cy), side, tip], fill=col, outline=INK_A)
    d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], outline=INK_A, width=2)
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(206, 170, 80, 255), outline=INK_A)
    fN = font(FB, 40)
    b = d.textbbox((0, 0), "S", font=fN)
    d.text((cx - (b[2] - b[0]) / 2, cy - 152), "S", font=fN, fill=INK_A)
    # meritko: 100 sahu (1 cesky sah ~ 1.78 m)
    seg = 44.5 * px
    sx, sy = W - 150 - 4 * seg, Hh - 150
    for k in range(4):
        d.rectangle([sx + k * seg, sy, sx + (k + 1) * seg, sy + 10], fill=INK_A if k % 2 == 0 else (236, 220, 180, 255), outline=INK_A)
    fS = font(FM, 26)
    d.text((sx - 6, sy + 16), "0", font=fS, fill=INK_A)
    b = d.textbbox((0, 0), "100 sáhů", font=fS)
    d.text((sx + 4 * seg - (b[2] - b[0]) / 2, sy + 16), "100 sáhů", font=fS, fill=INK_A)
    im.save(OUT, optimize=True)
    print("mapa ulozena", OUT, im.size, "rozsah", (X0, X1, Z0, Z1))


if __name__ == "__main__":
    main()
