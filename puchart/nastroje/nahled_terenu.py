"""Náhled výškové mřížky: stínování + vrstevnice + vrstvy (toky, sídla, hrady, výsek).

python3 nahled_terenu.py <mrizka_prefix> <vystup.png> [vrstvy.json]
vrstvy.json: {"body":[{"jmeno":..,"x":..,"y":..}], "cary":[{"jmeno":..,"body":[[x,y],..]}], "obdelniky":[...]}
Souřadnice S-JTSK (EPSG:5514).
"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

pre, out = sys.argv[1], sys.argv[2]
H = np.load(pre + ".npy"); M = json.load(open(pre + ".json"))
k = M["krok_m"]
gy, gx = np.gradient(H, k)
az, alt = np.radians(315), np.radians(40)
# řádky jdou od severu: +řádek = jih, proto -gy je sklon k severu
nx, ny, nz = -gx, gy, np.ones_like(H)
n = np.sqrt(nx**2 + ny**2 + nz**2)
L = np.array([np.cos(alt) * np.sin(az), np.cos(alt) * np.cos(az), np.sin(alt)])
sh = np.clip((nx * L[0] + ny * L[1] + nz * L[2]) / n, 0, 1)
t = (H - np.nanmin(H)) / (np.nanmax(H) - np.nanmin(H))
barva = np.stack([0.55 + 0.35 * t, 0.62 + 0.25 * t, 0.45 + 0.2 * t], -1)
img = (barva * (0.35 + 0.65 * sh[..., None]) * 255).astype(np.uint8)
# vrstevnice po 10 m (silnější po 50 m)
for krok, c in ((10, 0.82), (50, 0.6)):
    q = np.floor(H / krok)
    e = (q != np.roll(q, 1, 0)) | (q != np.roll(q, 1, 1))
    img[e] = (img[e] * c).astype(np.uint8)
im = Image.fromarray(img); d = ImageDraw.Draw(im)
def px(x, y): return ((x - M["x0"]) / k, (M["y1"] - y) / k)
try: f = ImageFont.truetype("DejaVuSans.ttf", 13)
except Exception: f = None
if len(sys.argv) > 3:
    V = json.load(open(sys.argv[3]))
    for c in V.get("cary", []):
        d.line([px(*p) for p in c["body"]], fill=tuple(c.get("barva", (30, 90, 200))), width=c.get("sirka", 2))
    for r in V.get("obdelniky", []):
        a, b = px(r["x0"], r["y1"]), px(r["x1"], r["y0"])
        d.rectangle([a, b], outline=tuple(r.get("barva", (200, 30, 30))), width=3)
        d.text((a[0] + 4, a[1] + 4), r["jmeno"], fill=(120, 0, 0), font=f)
    for b in V.get("body", []):
        x, y = px(b["x"], b["y"])
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=tuple(b.get("barva", (0, 0, 0))))
        d.text((x + 6, y - 7), b["jmeno"], fill=(0, 0, 0), font=f)
# měřítko 500 m
s = 500 / k; h = im.height
d.line([(10, h - 15), (10 + s, h - 15)], fill=(0, 0, 0), width=4); d.text((14, h - 33), "500 m", fill=(0, 0, 0), font=f)
d.text((im.width - 30, 8), "S ↑", fill=(0, 0, 0), font=f)
im.save(out)
print(out, im.size)
