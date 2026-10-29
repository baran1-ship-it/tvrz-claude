"""Textura dřevěného šindele (postup Havrana tools/sindel_tex.py): z fotografie šedých prken (Poly Haven wood_planks_grey,
CC0) vyřezává šindele 8–16 cm, řady 7 na metr se střídanými spárami, stín pod řadou, zešedlé tóny, místy mech.
Výstup blender/tex/sindel_Diffuse.jpg, _nor_gl.jpg, _Rough.jpg (1024, dlaždice 1,5 m)."""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
K = sys.argv[1]; T = os.path.join(K, "blender/tex")
N, SIZE = 1024, 1.5; RADY = int(7 * SIZE); rng = np.random.default_rng(11)
wood = np.asarray(Image.open(os.path.join(T, "wood_planks_grey_Diffuse.jpg")).convert("RGB")).astype(np.float32) / 255
wood = np.transpose(wood, (1, 0, 2))   # vlákna svisle (po spádu)
W = wood.shape[0]
diff = np.zeros((N, N, 3), np.float32); vys = np.zeros((N, N), np.float32)
rad = N / RADY
for r in range(RADY + 1):
    y0 = int(round(r * rad)); y1 = min(N, int(round((r + 1) * rad)) + int(rad * 0.15))
    x = int(rng.uniform(0, 30)) - 40
    while x < N:
        w = int(rng.uniform(0.08, 0.16) / SIZE * N); h = y1 - y0
        sx, sy = rng.integers(0, W - w - 1), rng.integers(0, W - h - 1)
        kus = wood[sy:sy + h, sx:sx + w] * rng.uniform(0.75, 1.1) * np.array([1.0, 0.98, 0.95]) * rng.uniform(0.85, 1.0)
        xa, xb = max(0, x), min(N, x + w)
        if xb > xa and h > 0:
            t = np.linspace(0, 1, h)[:, None]
            stin = 0.55 + 0.45 * np.clip(t * 3, 0, 1)        # horní kraj pod předchozí řadou ve stínu
            diff[y0:y1, xa:xb] = (kus[:, xa - x:xb - x] * stin[:, :, None])[: y1 - y0]
            vys[y0:y1, xa:xb] = (0.3 + 0.7 * t)[: y1 - y0]
            diff[y0:y1, max(0, xb - 2):xb] *= 0.35              # spára
        x += w
mech = np.asarray(Image.fromarray((rng.random((64, 64)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)) / 255.0
m = np.clip((mech - 0.62) * 4, 0, 1)[:, :, None] * (1 - vys[:, :, None]) * 0.6
diff = diff * (1 - m) + np.array([0.22, 0.25, 0.12]) * m
Image.fromarray((np.clip(diff, 0, 1) * 255).astype(np.uint8)).save(os.path.join(T, "sindel_Diffuse.jpg"), quality=92)
gy, gx = np.gradient(np.asarray(Image.fromarray((vys * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255 * 6)
n = np.stack([-gx, gy, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(T, "sindel_nor_gl.jpg"), quality=92)
Image.fromarray((np.full((N, N), 0.85) * 255 - vys * 20).astype(np.uint8)).save(os.path.join(T, "sindel_Rough.jpg"))
print("sindel ok")
