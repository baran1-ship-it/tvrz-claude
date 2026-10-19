"""Pergamenove textury pro UI (menu, nabidky, mapa): roztrepeny okraj, ohorele hrany, skvrny.
python3 tools/gen_ui.py  -> obrazky/ui/*.png"""
import numpy as np
from PIL import Image, ImageFilter

OUT = "obrazky/ui/"
rng = np.random.default_rng(1393)


def noise2(h, w, scales=((4, 1.0), (12, 0.5), (40, 0.25), (120, 0.12))):
    acc = np.zeros((h, w), np.float32)
    tot = 0.0
    for s, a in scales:
        r = rng.random((max(2, h * s // max(h, w)), max(2, w * s // max(h, w)))).astype(np.float32)
        im = Image.fromarray((r * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, np.float32) / 255.0 * a
        tot += a
    return acc / tot


def noise1(n, scales=((6, 1.0), (24, 0.5), (90, 0.3), (300, 0.15))):
    acc = np.zeros(n, np.float32)
    tot = 0.0
    for s, a in scales:
        k = rng.random(s + 2)
        acc += np.interp(np.linspace(0, s + 1, n), np.arange(s + 2), k) * a
        tot += a
    return acc / tot - 0.5


def parchment(w, h, edge=34, burn=1.0, tone=(226, 202, 156), char=0.0, holes=0):
    """List pergamenu: vzdalenost od roztrepeneho okraje -> alfa a ohoreni."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    low = ((4, 1.0), (14, 0.45))
    amp = edge * 0.55
    l = edge + noise1(h, low) * amp
    r = w - edge - noise1(h, low) * amp
    t = edge + noise1(w, low) * amp
    b = h - edge - noise1(w, low) * amp
    d = np.minimum.reduce([x - l[:, None], r[:, None] - x, y - t[None, :], b[None, :] - y])
    cr = edge * 1.2
    for cx, cy, sx, sy in ((edge + cr, edge + cr, -1, -1), (w - edge - cr, edge + cr, 1, -1),
                           (edge + cr, h - edge - cr, -1, 1), (w - edge - cr, h - edge - cr, 1, 1)):
        m = ((x - cx) * sx > 0) & ((y - cy) * sy > 0)
        d = np.where(m, np.minimum(d, cr - np.hypot(x - cx, y - cy)), d)
    # roztrepeni: 2D sum (vlakna a drobne natrzeni), ne po radcich -> bez pruhu
    s = max(w, h)
    tear = noise2(h, w, ((s // 40, 1.0), (s // 14, 0.6), (s // 6, 0.25)))
    de = d + (tear - 0.5) * edge * 0.5
    # propalene dirky a vykousnuti u okraje
    for _ in range(holes):
        side = rng.integers(4)
        if side < 2:
            hx = rng.uniform(edge * 2, w - edge * 2); hy = edge * 0.8 if side == 0 else h - edge * 0.8
        else:
            hy = rng.uniform(edge, h - edge); hx = edge * 0.8 if side == 2 else w - edge * 0.8
        hr = rng.uniform(0.5, 1.1) * edge
        dh = np.hypot(x - hx, (y - hy) * 1.3) - hr + (tear - 0.5) * edge * 0.6
        de = np.minimum(de, dh)
    alpha = np.clip(de / 1.6, 0, 1)
    n = noise2(h, w)
    n2 = noise2(h, w, ((3, 1.0), (8, 0.6)))
    fib = noise2(h, w, ((s // 3, 1.0), (int(s / 1.5), 0.5)))
    base = np.array(tone, np.float32)
    col = base[None, None, :] * (0.88 + 0.16 * n[..., None])
    col -= (np.clip(n2 - 0.6, 0, 1) * 80)[..., None] * np.array([0.55, 0.75, 1.0])
    col -= ((fib - 0.5) * 14)[..., None]
    # ohorely a zasedly okraj (z hladke vzdalenosti)
    band = np.clip(1 - de / (edge * 1.2), 0, 1) ** 1.8 * burn
    dark = np.array([104, 64, 30], np.float32)
    col = col * (1 - band[..., None] * 0.7) + dark * band[..., None] * 0.7
    rim = np.clip(1 - de / 4.0, 0, 1) * burn
    col = col * (1 - rim[..., None] * 0.55) + np.array([62, 36, 16]) * rim[..., None] * 0.55
    if char > 0:
        # ohorele: siroky hnedy pruh pripaleni a skoro cerny zuhelnately lem
        nn = noise2(h, w, ((5, 1.0), (16, 0.6)))
        reach = edge * (1.2 + 3.2 * nn)          # misty propalene hloubeji
        sc = np.clip(1 - de / reach, 0, 1) ** 1.7
        col = col * (1 - sc[..., None] * 0.7 * char) + np.array([118, 62, 20]) * sc[..., None] * 0.7 * char
        ch = np.clip(1 - de / (edge * (0.35 + 0.5 * nn)), 0, 1) ** 1.2 * char
        col = col * (1 - ch[..., None] * 0.85) + np.array([28, 15, 6]) * ch[..., None] * 0.85
    img = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def wash(w, h, rgb=(120, 24, 12), a=0.33):
    """Vyber polozky: mekky tah stetcem s inkoustem, suche roztrepene konce."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cy = h / 2 + noise1(w, ((3, 1.0),)) * h * 0.12
    hh = h * 0.34 * (1 + noise1(w, ((4, 1.0), (16, 0.4))) * 0.4)
    v = np.clip(1 - np.abs(y - cy[None, :]) / hh[None, :], 0, 1) ** 0.6
    ends = np.clip(np.minimum(x, w - x) / (w * 0.16), 0, 1) ** 0.8
    streak = noise2(h, w, ((3, 0.5), (w // 6, 1.0)))
    al = v * ends[None, :] * (0.7 + 0.3 * streak)
    al *= np.clip((ends[None, :] - (1 - streak) * 0.5) * 2.5, 0, 1)
    img = np.zeros((h, w, 4), np.uint8)
    img[..., :3] = rgb
    img[..., 3] = (np.clip(al, 0, 1) * a * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA").filter(ImageFilter.GaussianBlur(1.2))


def rule(w, h=24):
    """Ozdobna linka (inkoust): tenka cara s kosoctvercem uprostred."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    a = np.zeros((h, w), np.float32)
    x = np.arange(w, dtype=np.float32)
    fade = np.clip(np.minimum(x, w - x) / (w * 0.3), 0, 1)
    thick = 1.2 + fade * 1.0
    yy = np.arange(h, dtype=np.float32)[:, None]
    a = np.clip(thick[None, :] - np.abs(yy - h / 2), 0, 1) * fade[None, :]
    cx = w / 2
    dia = np.clip(7 - (np.abs(x[None, :] - cx) + np.abs(yy - h / 2) * 1.1), 0, 1)
    a = np.maximum(a, dia)
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., :3] = (58, 30, 12)
    arr[..., 3] = (a * 230).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


parchment(1024, 1024, edge=40, char=0.8, holes=7).save(OUT + "list.png")
parchment(768, 160, edge=20, burn=0.9, char=0.9, holes=3).save(OUT + "pruh.png")
for i in range(4):
    parchment(720, 76, edge=11, burn=0.9, char=1.0, holes=3 + i % 3).save(OUT + "tlacitko_%d.png" % i)
wash(512, 80, a=0.5).save(OUT + "vyber.png")
wash(512, 80, rgb=(70, 40, 16), a=0.18).save(OUT + "vyber_jemny.png")
rule(512).save(OUT + "linka.png")
print("ok")
