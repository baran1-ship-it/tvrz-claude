"""Procedurální textury: prameny vlasů, vazba plátna/vlny, kůže bot."""
import numpy as np
from PIL import Image, ImageFilter
def smooth_noise(shape, scale, rng):
    h, w = shape
    g = rng.random((h // scale + 2, w // scale + 2))
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((w + scale*2, h + scale*2), Image.BICUBIC)
    return np.asarray(im).astype(float)[:h, :w] / 255

def hair_strands(size=512, seed=1):
    rng = np.random.default_rng(seed)
    x = np.arange(size)
    a = np.zeros((size, size))
    for k, amp in ((size//2, 0.45), (size//4, 0.3), (size//16, 0.25)):
        col = rng.random(k); col = np.repeat(col, size // k)
        a += amp * col[None, :]
    # jemné vlnění podél délky (tileable ve v)
    sh = (np.sin(np.arange(size) / size * 2 * np.pi * 2) * 3).astype(int)
    a = np.stack([np.roll(a[i], sh[i]) for i in range(size)])
    a = np.asarray(Image.fromarray((a / a.max() * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(float) / 255
    a = 0.72 + 0.28 * a
    return a

def to_normal(h, strength=2.0):
    gy, gx = np.gradient(h)
    n = np.stack([-gx * strength, gy * strength, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)

def weave(size=512, threads=48, seed=2, slub=0.25):
    """plátnová vazba, tileable"""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size] / size * threads
    wx = np.abs(np.sin(np.pi * x)); wy = np.abs(np.sin(np.pi * y))
    chk = ((np.floor(x) + np.floor(y)) % 2)
    h = np.where(chk > 0, wx * 0.7 + 0.3 * wy, wy * 0.7 + 0.3 * wx)
    # nepravidelnost nití (tileable přes roll šumu po řádcích/sloupcích)
    rowv = np.repeat(rng.random(threads), size // threads + 1)[:size]
    colv = np.repeat(rng.random(threads), size // threads + 1)[:size]
    var = 1 - slub * (rowv[:, None] * (chk == 0) + colv[None, :] * (chk > 0))
    return np.clip(h * var, 0, 1)
