#!/usr/bin/env python3
"""Proceduralni PBR textury pro Tvrz. Vsechno se pocita, zadne fotky.
Vystup: textures/<jmeno>_a.png (barva), _n.png (normala, OpenGL Y+), _orm.png (AO, drsnost, kov)."""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "textures")
os.makedirs(OUT, exist_ok=True)


# ------------------------------------------------------------------ zaklady

def noise(n, beta=2.0, seed=0, ax=1.0, ay=1.0, lo=0.0, hi=None):
    """Dlazdicovatelny sum z FFT, standardizovany (prumer 0, odchylka 1). ax/ay > 1 protahuje utvary v dane ose."""
    rng = np.random.default_rng(seed)
    f = np.fft.fft2(rng.standard_normal((n, n)))
    fy = np.fft.fftfreq(n)[:, None] * n * ay
    fx = np.fft.fftfreq(n)[None, :] * n * ax
    rad = np.sqrt(fx * fx + fy * fy)
    rad[0, 0] = 1.0
    amp = rad ** (-beta / 2.0)
    if lo:
        amp[rad < lo] = 0
    if hi:
        amp[rad > hi] = 0
    amp[0, 0] = 0
    x = np.real(np.fft.ifft2(f * amp))
    x -= x.mean()
    x /= x.std() + 1e-9
    return x


def u(x, k=0.25):
    """Standardizovany sum -> 0..1."""
    return np.clip(0.5 + k * x, 0, 1)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-12), 0, 1)
    return t * t * (3 - 2 * t)


def blur(x, s):
    return ndimage.gaussian_filter(x, s, mode="wrap")


def rgb(c):
    return np.array(c, dtype=np.float64) / 255.0


def mix(a, b, t):
    if t.ndim == 2 and (np.ndim(a) == 3 or np.ndim(b) == 3 or np.ndim(a) == 1 or np.ndim(b) == 1):
        t = t[..., None]
    return a * (1 - t) + b * t


def normal_map(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    nx, ny, nz = -dx * strength, dy * strength, np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / l * 0.5 + 0.5, ny / l * 0.5 + 0.5, nz / l * 0.5 + 0.5], -1)


def cavity(h, radius, k):
    return np.clip(1.0 - k * np.maximum(blur(h, radius) - h, 0), 0, 1)


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def save(name, albedo, height=None, strength=6.0, rough=0.9, ao=None, metal=0.0, orm=True):
    n = albedo.shape[0]
    to_img(albedo).save(os.path.join(OUT, name + "_a.png"))
    if height is not None:
        to_img(normal_map(height, strength)).save(os.path.join(OUT, name + "_n.png"))
    if orm:
        r = np.broadcast_to(np.asarray(rough, dtype=np.float64), (n, n))
        m = np.broadcast_to(np.asarray(metal, dtype=np.float64), (n, n))
        a = np.ones((n, n)) if ao is None else ao
        to_img(np.stack([a, r, m], -1)).save(os.path.join(OUT, name + "_orm.png"))
    print("  ", name, n)


def warp(arr, n, amp, seed, order=1):
    wx = noise(n, 3.0, seed) * amp
    wy = noise(n, 3.0, seed + 1) * amp
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64)
    coords = [yy + wy, xx + wx]
    if arr.ndim == 2:
        return ndimage.map_coordinates(arr, coords, order=order, mode="wrap")
    return np.stack([ndimage.map_coordinates(arr[..., i], coords, order=order, mode="wrap") for i in range(arr.shape[2])], -1)


# ------------------------------------------------------------------ zdivo

def masonry(n, tile_m, course, width, gap, radius, bevel, seed, palette, power=0.55, tilt=0.12):
    """Radkove zdivo z nepravidelnych kamenu. Vraci (vyska 0..1, barva kamenu, nahodne id)."""
    rng = np.random.default_rng(seed)
    ppm = n / tile_m
    H = np.zeros((n, n))
    C = np.zeros((n, n, 3))
    ID = np.zeros((n, n))
    heights = []
    total = 0.0
    while total < tile_m - course[0]:
        h = rng.uniform(*course)
        heights.append(h)
        total += h
    heights = np.array(heights) * tile_m / total
    y = 0.0
    for ch in heights:
        x = rng.uniform(0, tile_m)
        x_end = x + tile_m
        ws = []
        tot = 0.0
        while tot < tile_m - width[0]:
            w = rng.uniform(*width)
            ws.append(w)
            tot += w
        ws = np.array(ws) * tile_m / tot
        for w in ws:
            x0, x1, y0, y1 = x * ppm, (x + w) * ppm, y * ppm, (y + ch) * ppm
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            g = gap * rng.uniform(0.7, 1.4)
            hw, hh = (x1 - x0) / 2 - g / 2, (y1 - y0) / 2 - g / 2
            r = min(radius * rng.uniform(0.5, 1.3), hw * 0.9, hh * 0.9)
            xs = np.arange(int(math.floor(x0)), int(math.ceil(x1)))
            ys = np.arange(int(math.floor(y0)), int(math.ceil(y1)))
            px = xs[None, :] + 0.5 - cx
            py = ys[:, None] + 0.5 - cy
            qx = np.abs(px) - (hw - r)
            qy = np.abs(py) - (hh - r)
            d = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - r
            prof = np.clip(-d / bevel, 0, 1) ** power
            top = rng.uniform(0.72, 1.0) + (px / max(hw, 1)) * rng.uniform(-tilt, tilt) + (py / max(hh, 1)) * rng.uniform(-tilt, tilt)
            hv = prof * top
            ix = np.ix_(ys % n, xs % n)
            cur = H[ix]
            m = hv > cur
            cur[m] = hv[m]
            H[ix] = cur
            col = rgb(palette[rng.integers(len(palette))]) * rng.uniform(0.86, 1.12)
            cc = C[ix]
            cc[m] = col
            C[ix] = cc
            ii = ID[ix]
            ii[m] = rng.uniform()
            ID[ix] = ii
            x += w
        y += ch
    return H, C, ID


STONE_PAL = [(162, 150, 128), (144, 135, 118), (176, 162, 136), (130, 123, 110), (154, 138, 114), (138, 132, 124), (168, 156, 140)]


def stone_wall(name="stone_wall", n=2048, tile=4.0, seed=3, course=(0.17, 0.34), width=(0.22, 0.62),
               palette=STONE_PAL, lichen=0.28, power=0.55, gap=11.0, radius=26.0, bevel=20.0, strength=9.0):
    k = n / 2048.0
    H, C, ID = masonry(n, tile, course, width, gap * k, radius * k, bevel * k, seed, palette, power)
    H = warp(H, n, 7.0 * k, seed + 10)
    C = warp(C, n, 7.0 * k, seed + 10)
    mask = smooth(0.02, 0.3, H)
    fine = noise(n, 1.6, seed + 20)
    mid = noise(n, 2.4, seed + 21, lo=6)
    coarse = noise(n, 3.0, seed + 22)
    pits = smooth(1.4, 2.2, noise(n, 1.9, seed + 23, lo=40))
    hs = 0.42 + 0.5 * H + 0.05 * mid + 0.035 * fine - 0.12 * pits
    hm = 0.22 + 0.05 * noise(n, 1.2, seed + 24, lo=30)
    height = mix(hm, hs, mask)
    stone = C * (0.84 + 0.3 * u(fine))[..., None] * (0.9 + 0.2 * u(mid))[..., None]
    stone *= (0.72 + 0.28 * smooth(0.1, 0.75, H))[..., None]
    stone *= (1 - 0.35 * pits)[..., None]
    mortar = rgb((176, 164, 142)) * (0.8 + 0.3 * u(noise(n, 1.4, seed + 25)))[..., None]
    alb = mix(mortar, stone, mask)
    # lisejniky a zatekle skvrny
    lm = smooth(0.6, 1.5, noise(n, 2.6, seed + 30)) * u(noise(n, 1.5, seed + 31), 0.4) * lichen
    alb = mix(alb, rgb((168, 164, 112)) * (0.8 + 0.4 * u(fine))[..., None], lm * mask)
    lm2 = smooth(1.0, 1.9, noise(n, 2.4, seed + 32)) * lichen * 0.8
    alb = mix(alb, rgb((96, 108, 74)), lm2 * 0.6)
    alb *= (0.9 + 0.16 * u(coarse))[..., None]
    ao = cavity(height, 9 * k, 3.2) * (0.75 + 0.25 * mask)
    rough = mix(np.full((n, n), 0.96), 0.86 + 0.08 * u(fine), mask)
    save(name, alb, height, strength * k, rough, ao)
    return alb, height


def flagstone():
    pal = [(150, 144, 132), (134, 130, 122), (160, 150, 134), (124, 118, 108), (142, 132, 118)]
    stone_wall("flagstone", 1024, 3.0, 41, (0.4, 0.7), (0.45, 0.95), pal, lichen=0.0, power=0.22, gap=14.0, radius=18.0, bevel=26.0, strength=7.0)


def ashlar():
    pal = [(170, 160, 140), (158, 148, 130), (180, 168, 146), (150, 142, 126)]
    stone_wall("ashlar", 1024, 2.0, 57, (0.26, 0.34), (0.42, 0.7), pal, lichen=0.1, power=0.25, gap=10.0, radius=10.0, bevel=22.0, strength=7.0)


# ------------------------------------------------------------------ omitka

def plaster(stone_alb, stone_h):
    n = 1024
    seed = 70
    low = noise(n, 3.2, seed)
    mid = noise(n, 2.2, seed + 1, lo=4)
    fine = noise(n, 1.3, seed + 2, lo=40)
    base = rgb((228, 217, 196))
    alb = base[None, None, :] * (0.9 + 0.12 * u(low))[..., None] * (0.95 + 0.07 * u(mid))[..., None] * (0.97 + 0.05 * u(fine))[..., None]
    # spinave skvrny a zatekani
    stain = smooth(0.4, 1.8, noise(n, 2.8, seed + 3, ay=0.35)) * 0.22
    alb = mix(alb, rgb((150, 132, 104)), stain)
    # praskliny
    cr = np.abs(noise(n, 2.3, seed + 4, lo=2, hi=60))
    crack = (1 - smooth(0.012, 0.035, cr)) * smooth(0.2, 1.2, noise(n, 3.0, seed + 5))
    alb *= (1 - 0.45 * crack)[..., None]
    height = 0.6 + 0.1 * u(low) + 0.05 * u(mid) + 0.02 * u(fine) - 0.25 * crack
    rough = 0.9 + 0.06 * u(fine)
    save("plaster", alb, height, 5.0, rough, cavity(height, 5, 2.0))

    # omitka s opadanymi misty, pod kterymi je kamen
    sa = np.asarray(Image.fromarray((stone_alb * 255).astype(np.uint8)).resize((n, n), Image.LANCZOS)) / 255.0
    sh = np.asarray(Image.fromarray((np.clip(stone_h, 0, 1) * 255).astype(np.uint8)).resize((n, n), Image.LANCZOS)) / 255.0
    m = noise(n, 2.7, seed + 9) + 0.25 * noise(n, 1.6, seed + 10, lo=12)
    hole = smooth(0.95, 1.12, m)
    edge = smooth(0.7, 0.95, m) * (1 - hole)
    alb2 = mix(alb, alb * 0.82, edge)
    alb2 = mix(alb2, sa * 0.92, hole)
    h2 = mix(height + 0.25, sh * 0.6, hole) - 0.08 * edge
    rough2 = mix(rough, np.full((n, n), 0.9), hole)
    save("plaster_worn", alb2, h2, 8.0, rough2, cavity(h2, 6, 2.6))


# ------------------------------------------------------------------ drevo

def grain(n, seed, stretch=14.0):
    g = noise(n, 2.1, seed, ax=1.0, ay=stretch)
    g2 = noise(n, 1.4, seed + 1, ax=1.0, ay=stretch * 2.2, lo=30)
    return g, g2


def wood_planks():
    n, tile, seed = 1024, 2.0, 90
    rng = np.random.default_rng(seed)
    ppm = n / tile
    g, g2 = grain(n, seed)
    alb = np.zeros((n, n, 3))
    height = np.zeros((n, n))
    ws = []
    tot = 0.0
    while tot < tile - 0.16:
        w = rng.uniform(0.17, 0.3)
        ws.append(w)
        tot += w
    ws = np.array(ws) * tile / tot
    x = 0.0
    xs = np.arange(n)
    base_cols = [(124, 92, 62), (112, 84, 58), (134, 102, 70), (104, 80, 58), (120, 96, 72)]
    for w in ws:
        x0, x1 = int(round(x * ppm)), int(round((x + w) * ppm))
        sh = rng.integers(0, n)
        gg = np.roll(g, sh, 0)[:, x0:x1]
        gg2 = np.roll(g2, sh // 2, 0)[:, x0:x1]
        col = rgb(base_cols[rng.integers(len(base_cols))]) * rng.uniform(0.88, 1.1)
        t = u(gg, 0.3)
        c = col[None, None, :] * (0.72 + 0.5 * t)[..., None] * (0.92 + 0.14 * u(gg2))[..., None]
        loc = (xs[x0:x1] - x0 + 0.5) / max(x1 - x0, 1)
        edge = np.minimum(loc, 1 - loc) * (x1 - x0)
        e = smooth(0.0, 5.0, edge)[None, :]
        c *= (0.35 + 0.65 * e)[..., None]
        alb[:, x0:x1] = c
        height[:, x0:x1] = (0.5 + 0.22 * t + 0.05 * u(gg2) + rng.uniform(-0.06, 0.06)) * (0.25 + 0.75 * e)
        x += w
    # suky
    for _ in range(9):
        cx, cy, r = rng.uniform(0, n), rng.uniform(0, n), rng.uniform(7, 16)
        yy, xx = np.mgrid[0:n, 0:n]
        dx = (xx - cx + n / 2) % n - n / 2
        dy = ((yy - cy + n / 2) % n - n / 2) * 0.55
        d = np.sqrt(dx * dx + dy * dy) / r
        k = np.clip(1 - d, 0, 1)
        alb *= (1 - 0.55 * smooth(0, 1, k))[..., None]
        height -= 0.12 * smooth(0, 1, k)
    rough = 0.72 + 0.16 * u(g2)
    save("wood_planks", alb, height, 6.0, rough, cavity(height, 4, 2.4))


def wood_beam():
    n, seed = 1024, 110
    g, g2 = grain(n, seed, 18.0)
    low = noise(n, 3.0, seed + 5)
    t = u(g, 0.3)
    col = rgb((92, 66, 44))
    alb = col[None, None, :] * (0.66 + 0.6 * t)[..., None] * (0.9 + 0.18 * u(g2))[..., None] * (0.88 + 0.2 * u(low))[..., None]
    # vysychaci trhliny po delce
    cr = np.abs(noise(n, 2.2, seed + 6, ax=1.0, ay=30.0, lo=3))
    crack = (1 - smooth(0.02, 0.07, cr)) * smooth(0.3, 1.4, noise(n, 2.8, seed + 7, ay=6.0))
    alb *= (1 - 0.6 * crack)[..., None]
    adze = u(noise(n, 2.6, seed + 8, ax=3.0, ay=1.0, lo=6, hi=40))
    height = 0.5 + 0.2 * t + 0.14 * adze - 0.3 * crack
    save("wood_beam", alb, height, 6.5, 0.78 + 0.12 * u(g2), cavity(height, 4, 2.2))


def bark():
    n, seed = 512, 130
    r = np.abs(noise(n, 2.0, seed, ax=1.0, ay=7.0, lo=4))
    ridges = smooth(0.0, 0.9, r)
    fine = noise(n, 1.4, seed + 1, lo=30)
    col = rgb((84, 70, 56))
    alb = col[None, None, :] * (0.72 + 0.4 * blur(ridges, 1.2))[..., None] * (0.92 + 0.16 * u(fine))[..., None]
    alb = mix(alb, rgb((110, 118, 96)), smooth(0.9, 2.0, noise(n, 2.6, seed + 2)) * 0.35)
    height = ridges * 0.8 + 0.1 * u(fine)
    save("bark", alb, height, 7.0, 0.92, cavity(height, 3, 2.0), orm=False)


# ------------------------------------------------------------------ sindel

def shingles():
    n, tile, seed = 1024, 2.0, 150
    rng = np.random.default_rng(seed)
    ppm = n / tile
    rows = 8
    rh = n / rows
    g, g2 = grain(n, seed, 10.0)
    alb = np.zeros((n, n, 3))
    height = np.zeros((n, n))
    ys = np.arange(n)
    cols = [(126, 110, 92), (112, 98, 84), (138, 122, 100), (100, 90, 80), (120, 104, 84), (146, 132, 112)]
    for r in range(rows):
        y0 = int(round(r * rh))
        x = rng.uniform(0, 0.2) * ppm
        end = x + n
        while x < end - 1:
            w = rng.uniform(0.09, 0.18) * ppm
            if end - (x + w) < 0.07 * ppm:
                w = end - x
            x0, x1 = int(round(x)), int(round(x + w))
            ln = int(rh + rng.uniform(-0.05, 0.12) * rh)
            yy = (y0 + np.arange(ln)) % n
            xx = np.arange(x0, x1) % n
            if len(xx) < 3:
                x += w
                continue
            ix = np.ix_(yy, xx)
            ly = (np.arange(ln) + 0.5) / ln
            lx = (np.arange(len(xx)) + 0.5) / len(xx)
            edge = np.minimum(lx, 1 - lx) * len(xx)
            e = smooth(0.0, 2.5, edge)[None, :]
            col = rgb(cols[rng.integers(len(cols))]) * rng.uniform(0.85, 1.12)
            t = u(g[ix], 0.3)
            c = col[None, None, :] * (0.74 + 0.45 * t)[..., None]
            c *= (0.35 + 0.65 * e)[..., None]
            c *= (0.78 + 0.22 * smooth(0.0, 0.25, ly))[:, None, None]  # stin pod hornim radem
            hv = (0.25 + 0.6 * ly[:, None] + 0.08 * t + rng.uniform(-0.04, 0.04)) * (0.3 + 0.7 * e)
            cur = height[ix]
            m = hv >= cur * 0.0  # pozdejsi rada prekryva predchozi
            alb[ix] = np.where(m[..., None], c, alb[ix])
            height[ix] = np.where(m, hv, cur)
            x += w
    moss = smooth(0.7, 1.8, noise(n, 2.6, seed + 4)) * u(noise(n, 1.5, seed + 5), 0.4)
    alb = mix(alb, rgb((92, 110, 64)), moss * 0.55)
    alb *= (0.9 + 0.16 * u(noise(n, 3.0, seed + 6)))[..., None]
    save("shingles", alb, height, 9.0, 0.86 + 0.1 * u(g2), cavity(height, 5, 3.0))


# ------------------------------------------------------------------ dlazba, hlina, trava

def voronoi(n, pts):
    """Vzdalenost k nejblizsimu a druhemu bodu a index nejblizsiho, s opakovanim pres hrany."""
    allp = np.concatenate([pts + np.array([dx, dy]) * n for dx in (-1, 0, 1) for dy in (-1, 0, 1)])
    tree = cKDTree(allp)
    yy, xx = np.mgrid[0:n, 0:n]
    q = np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], -1)
    d, i = tree.query(q, k=2)
    return d[:, 0].reshape(n, n), d[:, 1].reshape(n, n), (i[:, 0] % len(pts)).reshape(n, n)


def cobble():
    n, tile, seed = 1024, 3.0, 170
    rng = np.random.default_rng(seed)
    cells = 24
    step = n / cells
    pts = np.array([[(i + 0.5 + rng.uniform(-0.38, 0.38)) * step, (j + 0.5 + rng.uniform(-0.38, 0.38)) * step]
                    for i in range(cells) for j in range(cells)])
    f1, f2, idx = voronoi(n, pts)
    border = (f2 - f1) / step
    dome = smooth(0.02, 0.45, border)
    tone = rng.uniform(0.78, 1.15, len(pts))[idx]
    pal = np.array([rgb(c) for c in [(138, 132, 122), (120, 114, 104), (150, 140, 124), (112, 108, 102), (132, 120, 104)]])
    col = pal[rng.integers(len(pal), size=len(pts))][idx] * tone[..., None]
    fine = noise(n, 1.5, seed + 1)
    mid = noise(n, 2.6, seed + 2)
    stone = col * (0.84 + 0.3 * u(fine))[..., None] * (0.7 + 0.3 * dome)[..., None]
    dirt = rgb((92, 78, 60)) * (0.75 + 0.4 * u(noise(n, 1.3, seed + 3)))[..., None]
    # misty hlina prekryva kameny
    cover = smooth(0.5, 1.6, mid) * 0.7
    m = smooth(0.03, 0.2, border) * (1 - cover * (1 - smooth(0.25, 0.5, dome * u(fine))))
    alb = mix(dirt, stone, m)
    alb = mix(alb, rgb((84, 100, 54)), smooth(1.2, 2.2, noise(n, 2.4, seed + 5)) * (1 - m) * 0.6)
    height = mix(0.2 + 0.06 * u(fine), 0.35 + 0.6 * dome ** 0.6 * (0.8 + 0.2 * tone) + 0.04 * u(fine), m)
    save("cobble", alb, height, 10.0, mix(np.full((n, n), 0.95), 0.8 + 0.1 * u(fine), m), cavity(height, 6, 3.0))


def dirt():
    n, seed = 1024, 190
    low, mid, fine = noise(n, 3.0, seed), noise(n, 2.2, seed + 1, lo=5), noise(n, 1.3, seed + 2, lo=30)
    col = rgb((112, 92, 68))
    alb = col[None, None, :] * (0.8 + 0.25 * u(low))[..., None] * (0.85 + 0.25 * u(mid))[..., None] * (0.92 + 0.14 * u(fine))[..., None]
    rng = np.random.default_rng(seed)
    pts = rng.uniform(0, n, (380, 2))
    f1, f2, idx = voronoi(n, pts)
    rad = rng.uniform(2.0, 6.5, len(pts))[idx]
    peb = smooth(1.0, 0.5, f1 / rad)
    tone = rng.uniform(0.7, 1.15, len(pts))[idx]
    alb = mix(alb, rgb((128, 118, 102)) * tone[..., None], peb * 0.7)
    alb = mix(alb, rgb((78, 92, 50)), smooth(1.3, 2.3, noise(n, 2.6, seed + 6)) * 0.5)
    height = 0.4 + 0.2 * u(mid) + 0.08 * u(fine) + 0.3 * peb
    save("dirt", alb, height, 6.0, 0.93, cavity(height, 5, 2.0), orm=False)


def grass():
    n, seed = 1024, 210
    low, mid = noise(n, 3.0, seed), noise(n, 2.2, seed + 1, lo=5)
    blades = noise(n, 1.2, seed + 2, ax=5.0, ay=1.0, lo=40) + noise(n, 1.2, seed + 3, ax=1.0, ay=5.0, lo=40)
    fine = noise(n, 1.0, seed + 4, lo=80)
    a, b, c = rgb((62, 88, 36)), rgb((96, 118, 52)), rgb((124, 126, 66))
    t = u(mid + 0.6 * blades, 0.22)
    alb = mix(a, b, t)
    alb = mix(alb, c, smooth(0.6, 2.0, low) * 0.5)
    alb *= (0.8 + 0.4 * u(blades))[..., None] * (0.92 + 0.14 * u(fine))[..., None]
    height = 0.5 + 0.25 * u(blades) + 0.1 * u(mid)
    save("grass", alb, height, 5.0, 0.92, orm=False)


# ------------------------------------------------------------------ kov, slama, latka

def iron():
    n, seed = 512, 230
    low, mid, fine = noise(n, 3.0, seed), noise(n, 2.2, seed + 1, lo=5, hi=60), noise(n, 1.2, seed + 2, lo=40)
    rust = smooth(0.6, 1.6, noise(n, 2.5, seed + 3)) * 0.7
    base = rgb((70, 68, 66))[None, None, :] * (0.8 + 0.3 * u(low))[..., None] * (0.92 + 0.14 * u(fine))[..., None]
    alb = mix(base, rgb((112, 72, 46)) * (0.8 + 0.4 * u(fine))[..., None], rust)
    height = 0.5 + 0.3 * u(mid) + 0.05 * u(fine)
    save("iron", alb, height, 3.5, mix(0.42 + 0.14 * u(mid), np.full((n, n), 0.9), rust), None, mix(np.full((n, n), 0.9), np.full((n, n), 0.1), rust))


def straw():
    n = 1024
    rng = np.random.default_rng(250)
    s = 2
    img = Image.new("RGB", (n * s, n * s), (88, 68, 38))
    d = ImageDraw.Draw(img)
    cols = [(204, 172, 104), (184, 150, 88), (160, 128, 72), (214, 186, 124), (140, 110, 62), (190, 160, 98)]
    for i in range(15000):
        x, y = rng.uniform(0, n * s), rng.uniform(0, n * s)
        ang = rng.normal(0, 0.22) + (math.pi / 2 if rng.uniform() < 0.07 else 0)
        ln = rng.uniform(50, 190) * s
        dx, dy = math.cos(ang) * ln / 2, math.sin(ang) * ln / 2
        c = cols[rng.integers(len(cols))]
        k = rng.uniform(0.65, 1.1)
        c = tuple(min(255, int(v * k)) for v in c)
        w = int(rng.integers(2, 5))
        for ox in (-n * s, 0, n * s):
            for oy in (-n * s, 0, n * s):
                if -ln < x + ox < n * s + ln and -ln < y + oy < n * s + ln:
                    d.line([(x - dx + ox, y - dy + oy), (x + dx + ox, y + dy + oy)], fill=c, width=w)
    img = img.resize((n, n), Image.LANCZOS)
    alb = np.asarray(img) / 255.0
    lum = alb.mean(-1)
    height = blur(lum, 0.7)
    height = (height - height.min()) / (height.max() - height.min())
    save("straw", alb, height, 7.0, 0.9, cavity(height, 4, 2.0), orm=False)


def fabric():
    n = 512
    yy, xx = np.mgrid[0:n, 0:n]
    f = 2 * math.pi * 96 / n
    wx = 0.5 + 0.5 * np.sin(xx * f)
    wy = 0.5 + 0.5 * np.sin(yy * f)
    over = (np.sin(xx * f / 2) * np.sin(yy * f / 2)) > 0
    weave = np.where(over, wx, wy)
    fine = noise(n, 1.4, 271)
    low = noise(n, 2.8, 272)
    v = 0.74 + 0.2 * weave + 0.05 * u(fine)
    alb = np.stack([v, v * 0.97, v * 0.9], -1) * (0.9 + 0.14 * u(low))[..., None]
    height = 0.5 + 0.4 * weave + 0.05 * u(low)
    save("fabric", alb, height, 2.5, 0.95, orm=False)


def target_face():
    n = 512
    s = 2
    img = Image.new("RGB", (n * s, n * s), (196, 168, 110))
    d = ImageDraw.Draw(img)
    c = n * s / 2
    rings = [(1.0, (226, 214, 190)), (0.8, (60, 52, 46)), (0.6, (226, 214, 190)), (0.4, (172, 40, 34)), (0.2, (226, 196, 80))]
    for fr, col in rings:
        r = c * 0.94 * fr
        d.ellipse([c - r, c - r, c + r, c + r], fill=col)
    img = img.resize((n, n), Image.LANCZOS)
    alb = np.asarray(img) / 255.0
    # slamena spirala pod barvou
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.sqrt((xx - n / 2) ** 2 + (yy - n / 2) ** 2)
    coil = 0.5 + 0.5 * np.sin(r * 2 * math.pi / 15.0)
    fine = noise(n, 1.3, 290, ax=4.0)
    alb = alb * (0.72 + 0.3 * coil)[..., None] * (0.86 + 0.24 * u(fine))[..., None]
    height = 0.3 + 0.6 * coil + 0.08 * u(fine)
    save("target", alb, height, 6.0, 0.92, orm=False)


# ------------------------------------------------------------------ listi, trava, castice

def leaf_cluster():
    n, s = 512, 2
    rng = np.random.default_rng(310)
    img = Image.new("RGBA", (n * s, n * s), (70, 100, 40, 0))
    cols = [(52, 84, 30), (70, 104, 38), (88, 122, 46), (60, 96, 34), (102, 132, 52), (46, 72, 28)]
    for i in range(420):
        # hustejsi uprostred, ridsi na okrajich
        r = abs(rng.normal(0, 0.27)) * n * s
        a = rng.uniform(0, 2 * math.pi)
        x, y = n * s / 2 + math.cos(a) * r, n * s / 2 + math.sin(a) * r
        if not (30 < x < n * s - 30 and 30 < y < n * s - 30):
            continue
        ln, wd = rng.uniform(26, 46) * s / 2 * 1.6, rng.uniform(14, 24) * s / 2 * 1.6
        leaf = Image.new("RGBA", (int(ln * 2), int(ln * 2)), (0, 0, 0, 0))
        ld = ImageDraw.Draw(leaf)
        c = cols[rng.integers(len(cols))]
        k = rng.uniform(0.8, 1.15)
        c = tuple(min(255, int(v * k)) for v in c)
        cx = cy = ln
        ld.polygon([(cx - ln * 0.9, cy), (cx - ln * 0.3, cy - wd * 0.8), (cx + ln * 0.5, cy - wd * 0.55), (cx + ln * 0.95, cy),
                    (cx + ln * 0.5, cy + wd * 0.55), (cx - ln * 0.3, cy + wd * 0.8)], fill=c + (255,))
        ld.line([(cx - ln * 0.9, cy), (cx + ln * 0.9, cy)], fill=tuple(int(v * 0.7) for v in c) + (255,), width=2)
        leaf = leaf.rotate(rng.uniform(0, 360), resample=Image.BICUBIC)
        img.alpha_composite(leaf, (int(x - ln), int(y - ln)))
    img = img.resize((n, n), Image.LANCZOS)
    a = np.asarray(img).astype(np.float64) / 255.0
    a[..., :3] = np.where(a[..., 3:4] > 0.02, a[..., :3], rgb((70, 100, 40)))
    Image.fromarray((a * 255).astype(np.uint8)).save(os.path.join(OUT, "leaves.png"))
    print("   leaves")


def spruce_branch():
    n, s = 512, 2
    rng = np.random.default_rng(330)
    img = Image.new("RGBA", (n * s, n * s), (40, 66, 44, 0))
    d = ImageDraw.Draw(img)
    cols = [(30, 54, 38), (40, 68, 46), (52, 84, 54), (36, 60, 40), (62, 96, 60)]

    def twig(x, y, ang, ln, depth):
        steps = int(ln / (5 * s))
        px, py = x, y
        for i in range(steps):
            t = i / max(steps - 1, 1)
            nx_, ny_ = px + math.cos(ang) * 5 * s, py + math.sin(ang) * 5 * s
            d.line([(px, py), (nx_, ny_)], fill=(58, 44, 30, 255), width=max(1, int((3 - 2 * t) * s)))
            for side in (-1, 1):
                for j in range(2):
                    na = ang + side * rng.uniform(0.7, 1.25)
                    nl = rng.uniform(10, 17) * s * (1.0 - 0.45 * t)
                    c = cols[rng.integers(len(cols))]
                    d.line([(px, py), (px + math.cos(na) * nl, py + math.sin(na) * nl)], fill=c + (255,), width=int(rng.integers(2, 4)) * s // 2 + 1)
            if depth > 0 and i > 2 and i % 5 == 0:
                for side in (-1, 1):
                    twig(px, py, ang + side * rng.uniform(0.45, 0.75), ln * (1 - t) * 0.62, depth - 1)
            px, py = nx_, ny_
            ang += rng.uniform(-0.05, 0.05)

    # vetev roste shora od kmene dolu a do stran
    twig(n * s / 2, 14 * s, math.pi / 2, 440 * s, 2)
    img = img.resize((n, n), Image.LANCZOS)
    a = np.asarray(img).astype(np.float64) / 255.0
    a[..., :3] = np.where(a[..., 3:4] > 0.02, a[..., :3], rgb((40, 66, 44)))
    Image.fromarray((a * 255).astype(np.uint8)).save(os.path.join(OUT, "spruce.png"))
    print("   spruce")


def spruce_tree():
    """Cely smrk jako silueta pro zkrizene karty."""
    w, h, s = 256, 512, 3
    rng = np.random.default_rng(341)
    img = Image.new("RGBA", (w * s, h * s), (36, 60, 40, 0))
    d = ImageDraw.Draw(img)
    cx = w * s / 2
    d.rectangle([cx - 5 * s, h * s * 0.9, cx + 5 * s, h * s], fill=(70, 56, 42, 255))
    layers = 19
    top = 10 * s
    bottom = h * s * 0.93
    cols = [(26, 48, 34), (34, 60, 40), (44, 74, 48), (30, 54, 36), (54, 86, 54)]
    for i in range(layers - 1, -1, -1):
        t = i / (layers - 1)
        y = top + (bottom - top) * t
        hw = (0.05 + 0.43 * t ** 0.85) * w * s * rng.uniform(0.86, 1.08)
        lh = (bottom - top) / layers * 2.3
        n = 16
        pts = [(cx, y - lh)]
        for k in range(n + 1):
            x = -hw + 2 * hw * k / n
            droop = (abs(x) / hw) ** 1.4 * lh * 0.55
            jag = rng.uniform(-0.25, 0.25) * lh if k % 2 else rng.uniform(0.0, 0.3) * lh
            pts.append((cx + x, y - lh * 0.25 + droop + jag))
        c = cols[rng.integers(len(cols))]
        k_ = rng.uniform(0.85, 1.15)
        d.polygon(pts, fill=tuple(min(255, int(v * k_)) for v in c) + (255,))
        # jehlici na spodnim okraji
        for q in range(46):
            x = rng.uniform(-hw, hw)
            yy = y - lh * 0.25 + (abs(x) / hw) ** 1.4 * lh * 0.55 + rng.uniform(-0.3, 0.2) * lh
            ln = rng.uniform(5, 13) * s
            ang = math.pi / 2 + (x / hw) * 0.9 + rng.uniform(-0.3, 0.3)
            c2 = cols[rng.integers(len(cols))]
            d.line([(cx + x, yy), (cx + x + math.cos(ang) * ln, yy + math.sin(ang) * ln)], fill=c2 + (255,), width=2 * s)
    img = img.resize((w, h), Image.LANCZOS)
    a = np.asarray(img).astype(np.float64) / 255.0
    a[..., :3] = np.where(a[..., 3:4] > 0.02, a[..., :3], rgb((36, 60, 40)))
    Image.fromarray((a * 255).astype(np.uint8)).save(os.path.join(OUT, "spruce_tree.png"))
    print("   spruce_tree")


def grass_blades():
    n, s = 256, 4
    rng = np.random.default_rng(350)
    img = Image.new("RGBA", (n * s, n * s), (96, 120, 52, 0))
    d = ImageDraw.Draw(img)
    for i in range(26):
        x0 = n * s * (0.5 + rng.normal(0, 0.17))
        h = rng.uniform(0.45, 0.97) * n * s
        lean = rng.normal(0, 0.2) * n * s
        w = rng.uniform(5, 10) * s
        base, tip = (52, 78, 30), (126, 150, 70)
        k = rng.uniform(0.85, 1.15)
        segs = 10
        for j in range(segs):
            t0, t1 = j / segs, (j + 1) / segs
            xa, xb = x0 + lean * t0 * t0, x0 + lean * t1 * t1
            ya, yb = n * s - h * t0, n * s - h * t1
            wa, wb = w * (1 - t0) + 1, w * (1 - t1) + 1
            c = tuple(min(255, int((base[q] * (1 - t0) + tip[q] * t0) * k)) for q in range(3))
            d.polygon([(xa - wa / 2, ya), (xa + wa / 2, ya), (xb + wb / 2, yb), (xb - wb / 2, yb)], fill=c + (255,))
    img = img.resize((n, n), Image.LANCZOS)
    a = np.asarray(img).astype(np.float64) / 255.0
    a[..., :3] = np.where(a[..., 3:4] > 0.02, a[..., :3], rgb((96, 120, 52)))
    Image.fromarray((a * 255).astype(np.uint8)).save(os.path.join(OUT, "grass_blades.png"))
    print("   grass_blades")


def particles():
    n = 128
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.sqrt((xx - n / 2 + 0.5) ** 2 + (yy - n / 2 + 0.5) ** 2) / (n / 2)
    soft = np.clip(1 - r, 0, 1) ** 2
    Image.fromarray((np.stack([np.ones_like(soft)] * 3 + [soft], -1) * 255).astype(np.uint8)).save(os.path.join(OUT, "p_soft.png"))
    n = 256
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.sqrt((xx - n / 2 + 0.5) ** 2 + (yy - n / 2 + 0.5) ** 2) / (n / 2)
    nz = u(noise(n, 3.0, 371, hi=10), 0.3)
    puff = np.clip(1 - r * (0.75 + 0.6 * nz), 0, 1) ** 1.3
    Image.fromarray((np.stack([np.ones_like(puff)] * 3 + [puff], -1) * 255).astype(np.uint8)).save(os.path.join(OUT, "p_smoke.png"))
    # plamen: slza siroka dole, spicata nahore
    u_ = (xx + 0.5) / n - 0.5
    v_ = 1 - (yy + 0.5) / n
    width = 0.34 * np.sin(np.clip(v_, 0, 1) * math.pi) ** 0.6 * (1 - 0.55 * v_)
    nz2 = noise(n, 3.0, 373, hi=8)
    fl = np.clip(1 - np.abs(u_ + 0.03 * nz2) / (width + 1e-4), 0, 1) ** 1.2 * smooth(0.0, 0.12, v_) * smooth(1.0, 0.75, v_)
    Image.fromarray((np.stack([np.ones_like(fl)] * 3 + [fl], -1) * 255).astype(np.uint8)).save(os.path.join(OUT, "p_flame.png"))
    print("   particles")


def clouds_and_misc():
    n = 512
    c = u(noise(n, 2.7, 390, lo=1.5) + 0.35 * noise(n, 1.9, 391, lo=10), 0.22)
    to_img(np.stack([c, c, c], -1)).save(os.path.join(OUT, "cloud_noise.png"))
    w = noise(256, 2.2, 395, lo=2)
    w2 = noise(256, 2.0, 396, lo=4)
    to_img(normal_map(u(w) * 0.6 + u(w2) * 0.4, 14.0)).save(os.path.join(OUT, "water_n.png"))
    print("   clouds, water")


def banner():
    w, h, s = 256, 512, 2
    img = Image.new("RGB", (w * s, h * s), (150, 28, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w * s, h * s * 0.5], fill=(214, 204, 180))
    d.rectangle([0, h * s * 0.5 - 10 * s, w * s, h * s * 0.5 + 10 * s], fill=(40, 34, 30))
    # veze jako znak
    cx, cy = w * s / 2, h * s * 0.27
    d.rectangle([cx - 34 * s, cy - 30 * s, cx + 34 * s, cy + 50 * s], fill=(150, 28, 30))
    for k in (-1, 0, 1):
        d.rectangle([cx + k * 26 * s - 9 * s, cy - 48 * s, cx + k * 26 * s + 9 * s, cy - 30 * s], fill=(150, 28, 30))
    d.rectangle([cx - 10 * s, cy + 14 * s, cx + 10 * s, cy + 50 * s], fill=(40, 34, 30))
    cy2 = h * s * 0.76
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = (44 if i % 2 == 0 else 18) * s
        pts.append((cx + math.cos(a) * r, cy2 + math.sin(a) * r))
    d.polygon(pts, fill=(226, 190, 80))
    img = img.resize((w, h), Image.LANCZOS)
    a = np.asarray(img) / 255.0
    f = np.asarray(Image.open(os.path.join(OUT, "fabric_a.png")).resize((w, h))) / 255.0
    a = a * (0.55 + 0.6 * f.mean(-1, keepdims=True))
    to_img(a).save(os.path.join(OUT, "banner.png"))
    print("   banner")


if __name__ == "__main__":
    only = set(sys.argv[1:])

    def want(k):
        return not only or k in only

    sa = sh = None
    if want("stone") or want("plaster"):
        sa, sh = stone_wall()
    if want("stone"):
        flagstone()
        ashlar()
    if want("plaster"):
        plaster(sa, sh)
    if want("wood"):
        wood_planks()
        wood_beam()
        bark()
        shingles()
    if want("ground"):
        cobble()
        dirt()
        grass()
    if want("misc"):
        iron()
        straw()
        fabric()
        target_face()
        banner()
    if want("foliage"):
        leaf_cluster()
        spruce_branch()
        spruce_tree()
        grass_blades()
    if want("fx"):
        particles()
        clouds_and_misc()
