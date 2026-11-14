"""Figurka hráče pro rychlé cestování po mapě (Míša 14. 11.: „panáčka nějakého hezkého rytíře“): silueta z game-icons.net
(CC BY 3.0 – skoll/mounted-knight na koni, delapouite/pikeman pěšky, nastroje/zdroje/game_icons) obarvená jako malovaná
cínová figurka: červený šat s odleskem, zlatý lem, inkoustový obrys, oválný podstavec a stín. Výstup
hra/textury/ui/figurka_kun.png a figurka_pesky.png (hledí doprava; hra zrcadlí podle směru jízdy).
Použití: python3 nastroje/mapa_figurka.py <K> <godot>"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter

K, G = sys.argv[1], sys.argv[2]
OUT = os.path.join(K, "hra/textury/ui"); os.makedirs(OUT, exist_ok=True)
W = 256   # výsledné plátno

def silueta(svg):
    t = tempfile.mktemp(suffix=".png")
    subprocess.run([G, "--headless", "-s", os.path.join(K, "nastroje/godot/svg_png.gd"), "--", svg, t, "768"], check=True, capture_output=True)
    a = np.asarray(Image.open(t).convert("L"), float) / 255.0; os.remove(t)
    ys, xs = np.where(a > 0.5); a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return Image.fromarray((a * 255).astype("uint8"))

def figurka(svg, zrcadlit, jmeno):
    m = silueta(svg)
    if zrcadlit: m = m.transpose(Image.FLIP_LEFT_RIGHT)
    k = min(190 / m.height, 200 / m.width); m = m.resize((max(1, int(m.width * k)), max(1, int(m.height * k))), Image.LANCZOS)
    M = Image.new("L", (W, W), 0); ox = (W - m.width) // 2; oy = 214 - m.height; M.paste(m, (ox, oy))
    zlato = M.filter(ImageFilter.MaxFilter(7)); ink = zlato.filter(ImageFilter.MaxFilter(5))
    y = np.linspace(0, 1, W)[:, None] * np.ones((1, W))
    sat = np.stack([0.66 - 0.28 * y, 0.12 - 0.05 * y, 0.08 - 0.03 * y], -1)   # červený šat, dole tmavší
    x = np.ones((W, 1)) * np.linspace(0, 1, W)[None, :]
    sat += (np.clip(1.0 - np.hypot(x - 0.42, y - 0.3) * 2.6, 0, 1) * 0.22)[..., None]   # odlesk vlevo nahoře
    img = np.zeros((W, W, 4))
    # podstavec: oval s vrchem 0,85, stín pod ním
    yy, xx = np.mgrid[0:W, 0:W]
    stin = np.clip(1 - ((xx - W / 2 - 6) / 96) ** 2 - ((yy - 226) / 20) ** 2, 0, 1) ** 0.6 * 0.45
    img[..., 3] = stin
    pod = (((xx - W / 2) / 84) ** 2 + ((yy - 216) / 16) ** 2) <= 1
    img[pod] = [0.32, 0.22, 0.12, 1]
    hor = (((xx - W / 2) / 80) ** 2 + ((yy - 212) / 13) ** 2) <= 1
    img[hor] = [0.55, 0.42, 0.22, 1]
    for vrstva, barva in ((np.asarray(ink, float) / 255, [0.12, 0.07, 0.03]), (np.asarray(zlato, float) / 255, [0.86, 0.68, 0.28])):
        a = vrstva[..., None]; img[..., :3] = img[..., :3] * (1 - a) + np.array(barva) * a; img[..., 3] = np.maximum(img[..., 3], vrstva)
    a = (np.asarray(M, float) / 255)[..., None]; img[..., :3] = img[..., :3] * (1 - a) + sat * a
    Image.fromarray((np.clip(img, 0, 1) * 255).astype("uint8")).save(os.path.join(OUT, jmeno))
    print("FIGURKA", jmeno)

Z = os.path.join(K, "nastroje/zdroje/game_icons")
figurka(os.path.join(Z, "mounted-knight.svg"), False, "figurka_kun.png")
figurka(os.path.join(Z, "pikeman.svg"), False, "figurka_pesky.png")
