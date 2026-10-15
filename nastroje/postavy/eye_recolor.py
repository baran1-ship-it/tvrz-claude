"""Přebarvení duhovky MakeHuman oka (CC0) na zadanou barvu: python3 eye_recolor.py <jmeno> r g b [r2 g2 b2]"""
import sys, numpy as np
from PIL import Image
src = "/home/claude/dl/mh/makehuman/data/eyes/materials/brown_eye.png"
name = sys.argv[1]; c1 = np.array([float(x) for x in sys.argv[2:5]]); c2 = np.array([float(x) for x in sys.argv[5:8]]) if len(sys.argv) > 7 else c1 * 1.6
im = np.asarray(Image.open(src).convert("RGBA")).astype(float) / 255
rgb = im[..., :3]; mx = rgb.max(-1); mn = rgb.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
iris = np.clip((sat - 0.2) / 0.15, 0, 1) * (rgb[..., 0] > rgb[..., 2])
lum = rgb @ np.array([0.3, 0.5, 0.2])
l = np.clip(lum / np.percentile(lum[iris > 0.5], 95), 0, 1)
new = c1[None, None] * (1 - l[..., None]) + c2[None, None] * l[..., None]
new = new * (0.55 + 0.6 * l[..., None])
out = rgb * (1 - iris[..., None]) + np.clip(new, 0, 1) * iris[..., None]
Image.fromarray((np.dstack([out, im[..., 3]]) * 255).astype(np.uint8)).save(f"/home/claude/chars/eye_{name}.png")
print("ok", name)
