"""Atlasy pro lesní podrost a rostliny u vody (karty RGBA + normal).
Spuštění: python3 podrost_atlas.py <kapradi|kopriva|ostruzina|rakos|orobinec> <prefix> [px] [seed]
Vysoké karty (rákos, orobinec) se kreslí na plátno 1:3 a stlačí do čtverce – na kartě 1:3 se zase roztáhnou.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
KIND = sys.argv[1]
_args = [sys.argv[0], "liska", sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "1024", sys.argv[4] if len(sys.argv) > 4 else "1"]
sys.argv = _args
src = open(os.path.join(HERE, "leaf_atlas.py")).read().replace("\nmain()\n", "\n")
exec(src)

ASP = 3 if KIND in ("rakos", "orobinec") else 1

# nové tvary listů
_lp = leaf_profile
def leaf_profile(species, u):
    if species == "pinna":      # lístek kapradiny: kopinatý, hluboce vroubkovaný (lístečky)
        return np.sin(np.pi * np.clip(u, 0, 1) ** 0.75) ** 0.9 * 0.3
    if species == "kopriva":    # srdčitý, hrubě pilovitý
        w = np.sin(np.pi * np.clip(u, 0, 1) ** 0.7) ** 0.8 * 0.62
        w += 0.1 * np.exp(-((u - 0.06) / 0.06) ** 2)
        return w * (1 - 0.6 * np.clip((u - 0.8) / 0.2, 0, 1) ** 1.2)
    if species == "ostruzina":  # vejčitý lístek, pilovitý
        return np.sin(np.pi * np.clip(u, 0, 1) ** 0.75) ** 0.85 * 0.58
    if species == "rakos":      # dlouhý úzký list
        return np.sin(np.pi * np.clip(u, 0, 1) ** 0.6) ** 0.5 * 0.07
    return _lp(species, u)
SERR.update({"pinna": (16, 0.45, 0.1), "kopriva": (16, 0.16, 0.05), "ostruzina": (22, 0.08, 0.04), "rakos": (1, 0.0, 0.0)})
GREEN.update({"pinna": ((52, 86, 30), (104, 140, 56)), "kopriva": ((46, 70, 28), (90, 116, 50)),
              "ostruzina": ((44, 66, 28), (88, 108, 48)), "rakos": ((86, 104, 58), (146, 152, 96))})

def poly(pts_fn, n):
    return [pts_fn(i / n) for i in range(n + 1)]

def card_kapradi(seed):
    S = CELL * SS
    rgb = np.zeros((S, S, 3)); a = np.zeros((S, S)); h = np.zeros((S, S))
    rr = random.Random(seed)
    tint = np.array([rr.uniform(0.92, 1.06), rr.uniform(0.94, 1.06), rr.uniform(0.85, 1.0)])
    if rr.random() < 0.2: tint *= np.array((1.25, 1.1, 0.7))            # žloutnoucí list
    bend = rr.uniform(-0.15, 0.15)
    rach = poly(lambda t: (S * (0.5 + bend * t * t), S * (0.99 - 0.95 * t)), 40)
    draw_twig(rgb, a, h, rach, S * 0.006)
    npair = rr.randint(16, 22)
    for k in range(npair):
        t = 0.1 + 0.88 * k / npair
        j = int(t * 40); px, py = rach[j]
        Lp = S * 0.26 * np.sin(np.pi * (0.12 + 0.88 * t)) ** 0.7 * (1.05 - 0.6 * t)
        for sd in (-1, 1):
            ang = -math.pi / 2 + sd * rr.uniform(1.05, 1.3)
            draw_leaf(rgb, a, h, px, py, Lp, ang, "pinna", tint * rr.uniform(0.92, 1.06), seed * 31 + k * 2 + (sd > 0))
    return rgb, a, h

def card_kopriva(seed):
    S = CELL * SS
    rgb = np.zeros((S, S, 3)); a = np.zeros((S, S)); h = np.zeros((S, S))
    rr = random.Random(seed)
    tint = np.array([rr.uniform(0.92, 1.05), rr.uniform(0.94, 1.05), rr.uniform(0.9, 1.02)])
    stem = poly(lambda t: (S * (0.5 + 0.03 * math.sin(t * 5 + seed)), S * (0.995 - 0.97 * t)), 30)
    draw_twig(rgb, a, h, stem, S * 0.007)
    nn = rr.randint(5, 7)
    for k in range(nn):
        t = 0.15 + 0.8 * k / nn
        j = int(t * 30); px, py = stem[j]
        L = S * 0.2 * (1.1 - 0.55 * t)
        for sd in (-1, 1):
            ang = -math.pi / 2 + sd * rr.uniform(0.75, 1.15)
            draw_leaf(rgb, a, h, px, py, L, ang, "kopriva", tint * rr.uniform(0.9, 1.06), seed * 17 + k * 2 + (sd > 0))
            if t < 0.75 and rr.random() < 0.7:        # visící květenství
                fl = [(px + sd * S * 0.01, py)]
                for q in range(8):
                    fl.append((fl[-1][0] + sd * S * 0.012, fl[-1][1] + S * 0.012))
                draw_twig(rgb, a, h, fl, S * 0.003)
    return rgb, a, h

def card_ostruzina(seed):
    S = CELL * SS
    rgb = np.zeros((S, S, 3)); a = np.zeros((S, S)); h = np.zeros((S, S))
    rr = random.Random(seed)
    tint = np.array([rr.uniform(0.9, 1.05), rr.uniform(0.92, 1.05), rr.uniform(0.88, 1.0)])
    if rr.random() < 0.25: tint *= np.array((1.3, 0.95, 0.75))          # červenající list
    cane = poly(lambda t: (S * (0.15 + 0.7 * t), S * (0.95 - 0.55 * math.sin(math.pi * t * 0.8))), 30)
    draw_twig(rgb, a, h, cane, S * 0.009)
    for k in range(rr.randint(3, 5)):
        t = 0.15 + 0.8 * k / 4
        j = int(t * 30); px, py = cane[j]
        ang0 = -math.pi / 2 + rr.uniform(-0.6, 0.6)
        ex, ey = px + math.cos(ang0) * S * 0.08, py + math.sin(ang0) * S * 0.08
        draw_twig(rgb, a, h, [(px, py), (ex, ey)], S * 0.004)
        nlf = rr.choice((3, 5))
        for q in range(nlf):
            ang = ang0 + (q - (nlf - 1) / 2) * 0.75
            draw_leaf(rgb, a, h, ex, ey, S * rr.uniform(0.13, 0.17), ang, "ostruzina", tint * rr.uniform(0.92, 1.05), seed * 29 + k * 5 + q)
    if rr.random() < 0.6:                                                 # plody
        yy, xx = np.mgrid[0:S, 0:S]
        bx, by = cane[-1]
        for q in range(rr.randint(2, 6)):
            cx_, cy_ = bx + rr.uniform(-S * 0.08, S * 0.02), by + rr.uniform(0, S * 0.1)
            ripe = rr.random()
            colr = (25, 18, 28) if ripe < 0.5 else ((140, 30, 30) if ripe < 0.8 else (120, 140, 60))
            for d in range(12):
                ox, oy = cx_ + rr.gauss(0, S * 0.006), cy_ + rr.gauss(0, S * 0.007)
                m = (xx - ox) ** 2 + (yy - oy) ** 2 < (S * 0.006) ** 2
                rgb[m] = np.array(colr) * rr.uniform(0.85, 1.15); a[m] = 1; h[m] = 0.9
    return rgb, a, h

def card_rakos(seed, plume=True):
    W = CELL * SS; S = W * ASP          # plátno W x S (výška S)
    rgb = np.zeros((S, W, 3)); a = np.zeros((S, W)); h = np.zeros((S, W))
    rr = random.Random(seed)
    nst = rr.randint(2, 3)
    for s_ in range(nst):
        x0 = W * (0.5 + rr.uniform(-0.12, 0.12)); lean = rr.uniform(-0.08, 0.08)
        top = S * rr.uniform(0.04, 0.15)
        stem = poly(lambda t: (x0 + W * lean * t * t, S * 0.998 - (S * 0.998 - top) * t), 40)
        draw_twig(rgb, a, h, stem, W * 0.012)
        for k in range(rr.randint(6, 9)):
            t = 0.12 + 0.72 * k / 8
            j = int(t * 40); px, py = stem[j]
            sd = 1 if k % 2 else -1
            # list: dlouhý, ohnutý dolů – kreslený jako stéblo
            draw_blade(rgb, a, h, px, py, S * rr.uniform(0.16, 0.24), -math.pi / 2 + sd * rr.uniform(0.25, 0.5),
                       sd * rr.uniform(0.5, 1.1), W * 0.022, (88, 108, 58), (160, 150, 96), rr.uniform(0.2, 0.8))
        if plume:
            px, py = stem[-1]
            for q in range(70):
                draw_blade(rgb, a, h, px + rr.gauss(0, W * 0.02), py + rr.uniform(0, S * 0.07), S * rr.uniform(0.03, 0.07),
                           math.pi / 2 + rr.gauss(0, 0.35), rr.gauss(0, 0.4), W * 0.006, (110, 84, 78), (164, 140, 120), 1.0)
    return rgb, a, h

def card_orobinec(seed):
    W = CELL * SS; S = W * ASP
    rgb = np.zeros((S, W, 3)); a = np.zeros((S, W)); h = np.zeros((S, W))
    rr = random.Random(seed)
    for k in range(rr.randint(5, 8)):        # ploché listy
        x0 = W * (0.5 + rr.gauss(0, 0.08))
        draw_blade(rgb, a, h, x0, S * 0.998, S * rr.uniform(0.75, 0.95), -math.pi / 2 + rr.gauss(0, 0.05),
                   rr.gauss(0, 0.35), W * 0.05, (72, 98, 48), (150, 140, 90), rr.uniform(0.0, 0.7))
    for k in range(rr.randint(1, 2)):        # stvol s palicí
        x0 = W * (0.5 + rr.gauss(0, 0.06)); top = S * rr.uniform(0.05, 0.15)
        stem = poly(lambda t: (x0, S * 0.998 - (S * 0.998 - top) * t), 30)
        draw_twig(rgb, a, h, stem, W * 0.012)
        yy, xx = np.mgrid[0:S, 0:W]
        cy0 = top + S * 0.03
        m = ((xx - x0) / (W * 0.045)) ** 2 + ((yy - cy0 - S * 0.05) / (S * 0.055)) ** 2 < 1
        n = fbm((S, W), 6.0, seed + k, 2)
        rgb[m] = (np.array((92, 58, 34))[None, :] * (0.8 + 0.4 * n[m][:, None])); a[m] = 1; h[m] = 0.85
        draw_twig(rgb, a, h, [(x0, cy0), (x0, top - S * 0.04)], W * 0.006)      # samčí špička
    return rgb, a, h

FN = {"kapradi": card_kapradi, "kopriva": card_kopriva, "ostruzina": card_ostruzina,
      "rakos": card_rakos, "orobinec": card_orobinec}[KIND]

def main2():
    W = CELL * SS; Hc = W * ASP
    big_rgb = np.zeros((GRID * Hc, GRID * W, 3)); big_a = np.zeros((GRID * Hc, GRID * W)); big_h = np.zeros((GRID * Hc, GRID * W))
    cards = []
    for gy in range(GRID):
        for gx in range(GRID):
            idx = gy * GRID + gx
            rgb, a, hh = FN(SEED * 100 + idx)
            big_rgb[gy * Hc:(gy + 1) * Hc, gx * W:(gx + 1) * W] = rgb
            big_a[gy * Hc:(gy + 1) * Hc, gx * W:(gx + 1) * W] = a
            big_h[gy * Hc:(gy + 1) * Hc, gx * W:(gx + 1) * W] = hh
            cards.append({"kind": "cluster", "u0": gx / GRID, "u1": (gx + 1) / GRID,
                          "v0": 1 - (gy + 1) / GRID, "v1": 1 - gy / GRID, "aspect": ASP})
    img = Image.fromarray(np.clip(big_rgb, 0, 255).astype(np.uint8))
    alpha = Image.fromarray((big_a * 255).astype(np.uint8))
    dil = img
    for _ in range(6):
        dil = dil.filter(ImageFilter.MaxFilter(5))
    comp = Image.composite(img, dil, alpha).resize((PX, PX), Image.LANCZOS)
    alpha_s = alpha.resize((PX, PX), Image.LANCZOS)
    out = comp.convert("RGBA"); out.putalpha(alpha_s); out.save(PREFIX + "_color.png")
    hh = Image.fromarray((big_h * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)).resize((PX, PX), Image.LANCZOS)
    hz = np.asarray(hh).astype(np.float64) / 255.0
    gx = np.zeros_like(hz); gy = np.zeros_like(hz)
    gx[:, 1:-1] = (hz[:, 2:] - hz[:, :-2]) * 0.5; gy[1:-1, :] = (hz[2:, :] - hz[:-2, :]) * 0.5
    nx, ny, nz = -gx * 6.0, gy * 6.0, np.ones_like(hz); ln = np.sqrt(nx * nx + ny * ny + 1)
    Image.fromarray(((np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5) * 255).astype(np.uint8)).save(PREFIX + "_normal.png")
    json.dump({"species": KIND, "grid": GRID, "cards": cards}, open(PREFIX + "_cards.json", "w"))
    print("ATLAS", PREFIX, PX)

main2()
