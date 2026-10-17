"""Dlaždicové detailní textury látek (256 px, tileable) pro Godot detail na UV2: vlna (kepr), len (plátno), kůže (zrno)."""
import numpy as np, cv2, sys
OUT = sys.argv[1]; N = 256
y, x = np.mgrid[0:N, 0:N].astype(np.float32)
rng = np.random.default_rng(2)
def nrm(h, s):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * s; gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * s
    n = np.dstack([-gx, gy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    return (np.dstack([n[..., 2], n[..., 1], n[..., 0]]) * 0.5 + 0.5) * 255      # BGR
def tile_noise(f):
    a = rng.random((f, f)).astype(np.float32); a = np.tile(a, (3, 3))
    b = cv2.resize(a, (N * 3, N * 3), interpolation=cv2.INTER_CUBIC); return b[N:2 * N, N:2 * N]
P = N / 6.0     # vlna: 6 vazných bodů na dlaždici 2,4 cm = 4 mm
wool = 0.5 + 0.5 * np.sin(2 * np.pi * (x + y) / P) * (0.75 + 0.25 * np.sin(2 * np.pi * (x - y) / (P * 0.5)))
wool += 0.25 * (tile_noise(32) - 0.5)
P2 = N / 12.0   # len: plátnová vazba 2 mm
linen = np.sin(2 * np.pi * x / P2) * np.sin(2 * np.pi * y / P2) * 0.5 + 0.5
slub = tile_noise(16)
linen = linen * (0.8 + 0.4 * slub) + 0.15 * (tile_noise(64) - 0.5)
leather = tile_noise(48) * 0.6 + tile_noise(12) * 0.4
for nm, h, s, a in (("vlna", wool, 1.2, 0.08), ("len", linen, 0.9, 0.06), ("kuze", leather, 0.8, 0.05)):
    cv2.imwrite(f"{OUT}/vazba_{nm}_normal.png", nrm(h, s).astype(np.uint8))
    alb = np.zeros((N, N, 4), np.uint8); alb[..., 3] = np.clip((1 - h) * a * 255, 0, 255).astype(np.uint8)   # černá s alfou = jemné ztmavení v prohlubních
    cv2.imwrite(f"{OUT}/vazba_{nm}_albedo.png", alb)
print("OK")
