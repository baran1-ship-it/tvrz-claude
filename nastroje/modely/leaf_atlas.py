"""Atlas listových karet (RGBA + normal) pro keře – kreslené procedurálně.
Spuštění: python3 leaf_atlas.py <druh> <výstupní_prefix> [px] [seed]
Výstup: <prefix>_color.png (RGBA, alfa = ořez), <prefix>_normal.png, <prefix>_cards.json
"""
import sys, math, json, random
import numpy as np
from PIL import Image, ImageFilter

SPECIES = sys.argv[1] if len(sys.argv) > 1 else "liska"
PREFIX = sys.argv[2] if len(sys.argv) > 2 else "atlas_liska"
PX = int(sys.argv[3]) if len(sys.argv) > 3 else 2048
SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 1
rng = random.Random(SEED); np.random.seed(SEED)

GRID = 4                      # 4×4 karet
CELL = PX // GRID
SS = 2                        # supersampling

# ---------------------------------------------------------------- šum
def value_noise(shape, scale, seed):
    r = np.random.RandomState(seed)
    gh, gw = int(shape[0] / scale) + 3, int(shape[1] / scale) + 3
    g = r.rand(gh, gw)
    y = np.arange(shape[0]) / scale; x = np.arange(shape[1]) / scale
    yi, xi = y.astype(int), x.astype(int)
    yf, xf = y - yi, x - xi
    yf = yf * yf * (3 - 2 * yf); xf = xf * xf * (3 - 2 * xf)
    a = g[yi][:, xi]; b = g[yi][:, xi + 1]; c = g[yi + 1][:, xi]; d = g[yi + 1][:, xi + 1]
    top = a + (b - a) * xf[None, :]; bot = c + (d - c) * xf[None, :]
    return top + (bot - top) * yf[:, None]

def fbm(shape, scale, seed, oct=4):
    out = np.zeros(shape); amp = 1; tot = 0
    for i in range(oct):
        out += amp * value_noise(shape, scale / 2 ** i, seed + i * 17); tot += amp; amp *= 0.5
    return out / tot

# ---------------------------------------------------------------- tvary listů
def leaf_profile(species, u):
    """Polovina šířky listu (0..1) podle polohy na hlavní žilce u ∈ [0,1] (0 = řapík)."""
    if species == "liska":       # okrouhle obvejčitý, srdčitá báze, krátce zašpičatělý
        w = np.sin(np.pi * np.clip(u, 0, 1) ** 0.75) ** 0.8 * 0.92
        w += 0.12 * np.exp(-((u - 0.06) / 0.06) ** 2)          # srdčitá báze
        w *= 1 - 0.55 * np.clip((u - 0.86) / 0.14, 0, 1) ** 1.5  # špička
        return w * 0.82
    if species == "trnka":       # malý eliptický
        return np.sin(np.pi * np.clip(u, 0, 1)) ** 0.9 * 0.42
    if species == "bez":         # lístek zpeřeného listu – kopinatý
        return np.sin(np.pi * np.clip(u, 0, 1) ** 0.85) ** 1.1 * 0.36
    if species == "hloh":        # laločnatý
        base = np.sin(np.pi * np.clip(u, 0, 1) ** 0.7) * 0.7
        return base * (0.75 + 0.25 * np.cos(u * np.pi * 5) ** 2)
    if species == "olse":        # obvejčitý, tupý až vykrojený vrchol
        w = np.sin(np.pi * np.clip(u, 0, 1) ** 0.6) ** 0.7 * 0.85
        w *= 1 - 0.25 * np.exp(-((u - 1.0) / 0.06) ** 2)
        return w * np.clip((1.02 - u) * 8, 0, 1) ** 0.3
    if species == "vrba":        # kopinatý, úzký
        return np.sin(np.pi * np.clip(u, 0, 1) ** 0.9) ** 1.1 * 0.24
    if species == "dub":         # laločnatý list dubu letního
        base = np.sin(np.pi * np.clip(u, 0, 1) ** 0.85) ** 0.7 * 0.62
        lob = 0.55 + 0.45 * np.abs(np.cos(u * np.pi * 5.5 + 0.3))
        return base * lob * (0.7 + 0.3 * np.clip(u * 2, 0, 1))
    if species == "lipa":        # srdčitý, zašpičatělý
        w = np.sin(np.pi * np.clip(u, 0, 1) ** 0.65) ** 0.75 * 0.95
        w += 0.18 * np.exp(-((u - 0.05) / 0.07) ** 2)
        w *= 1 - 0.6 * np.clip((u - 0.8) / 0.2, 0, 1) ** 1.3
        return w * 0.85
    if species == "buk":         # eliptický, celokrajný, zvlněný
        return np.sin(np.pi * np.clip(u, 0, 1) ** 0.9) ** 0.85 * 0.6
    if species == "briza":       # trojúhelníkovitě vejčitý, malý
        w = np.clip(1.15 - u, 0, 1) * np.sin(np.pi * np.clip(u, 0, 1) ** 0.5) * 0.9
        return w
    if species == "sipek":       # malý vejčitý lístek
        return np.sin(np.pi * np.clip(u, 0, 1) ** 0.9) ** 0.9 * 0.5
    return np.sin(np.pi * np.clip(u, 0, 1)) * 0.5

SERR = {"olse": (36, 0.03, 0.02), "vrba": (60, 0.012, 0.0), "dub": (10, 0.0, 0.0), "lipa": (40, 0.02, 0.01), "buk": (12, 0.015, 0.0), "briza": (30, 0.04, 0.02),
        "liska": (44, 0.022, 0.014), "trnka": (26, 0.03, 0.01), "bez": (30, 0.05, 0.0),
        "hloh": (18, 0.06, 0.02), "sipek": (22, 0.05, 0.0)}
GREEN = {   # sRGB 0–255: (tmavá, světlá), rubová strana světlejší
    "olse":  ((44, 70, 28), (88, 118, 48)),
    "vrba":  ((92, 112, 72), (150, 166, 120)),
    "dub":   ((62, 84, 30), (112, 134, 54)),
    "lipa":  ((70, 98, 34), (124, 150, 60)),
    "buk":   ((66, 92, 30), (120, 146, 56)),
    "briza": ((76, 104, 36), (132, 158, 62)),
    "liska": ((72, 98, 36), (128, 152, 64)),
    "trnka": ((60, 84, 34), (108, 132, 58)),
    "bez":   ((50, 74, 28), (98, 122, 50)),
    "hloh":  ((50, 72, 28), (92, 116, 46)),
    "sipek": ((52, 74, 32), (96, 118, 52)),
}

def draw_leaf(buf_rgb, buf_a, buf_h, cx, cy, length, angle, species, tint, seed):
    """Nakreslí jeden list do bufferů (supersampling souřadnice)."""
    H, W = buf_a.shape
    pad = int(length * 1.2) + 4
    x0, x1 = max(0, int(cx - pad)), min(W, int(cx + pad))
    y0, y1 = max(0, int(cy - pad)), min(H, int(cy + pad))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    dx, dy = xx - cx, yy - cy
    ca, sa = math.cos(angle), math.sin(angle)
    along = (dx * ca + dy * sa) / length           # u
    across = (-dx * sa + dy * ca) / length          # v
    # lehké prohnutí hlavní žilky
    bend = rng.uniform(-0.08, 0.08)
    across = across - bend * along ** 2
    u = along
    teeth, a1, a2 = SERR.get(species, (30, 0.04, 0.01))
    w = leaf_profile(species, u)
    t = u * teeth
    saw = (t - np.floor(t))                          # pilovitý okraj
    t2 = u * teeth * 2.3
    saw2 = (t2 - np.floor(t2))
    wedge = w * (1 + a1 * (saw - 0.5) * 2 + a2 * (saw2 - 0.5) * 2)
    inside = (u > 0) & (u < 1) & (np.abs(across) < wedge * 0.5)
    # řapík
    pet = (u > -0.16) & (u <= 0.02) & (np.abs(across) < 0.012)
    # žilky: hlavní + postranní (zpeřená žilnatina)
    av = np.abs(across)
    mid = np.exp(-(av / 0.008) ** 2)
    npairs = 7 if species == "liska" else 6
    phase = (u * npairs - av * 1.6 * npairs)
    lat = np.exp(-((phase - np.round(phase)) / 0.06) ** 2) * (av < wedge * 0.47) * (u > 0.05)
    veins = np.clip(mid + 0.55 * lat, 0, 1)
    # barva
    dark, light = GREEN[species]
    nseed = seed * 13
    n = fbm((y1 - y0, x1 - x0), max(4.0, length * 0.15), nseed, 3)
    base = np.array(dark)[None, None, :] * (1 - n[..., None]) + np.array(light)[None, None, :] * n[..., None]
    base = base * tint[None, None, :]
    # okraj a špička trochu zažloutlé/hnědé u některých listů
    edge = np.clip(1 - (wedge * 0.5 - av) / (0.06 + 1e-6), 0, 1) * (rng.random() < 0.35)
    brown = np.array((118, 92, 46))[None, None, :]
    base = base * (1 - 0.6 * edge[..., None]) + brown * 0.6 * edge[..., None]
    # skvrny a okus
    if rng.random() < 0.4:
        sp = fbm((y1 - y0, x1 - x0), max(3.0, length * 0.05), nseed + 5, 2)
        spot = np.clip((sp - 0.72) * 8, 0, 1)
        base = base * (1 - 0.7 * spot[..., None]) + np.array((92, 70, 34))[None, None, :] * 0.7 * spot[..., None]
    hole = np.zeros_like(u, dtype=bool)
    if rng.random() < 0.15:     # okousaný okraj nebo dírka od hmyzu – nepravidelná
        hx, hy = rng.uniform(0.3, 0.8), rng.uniform(-0.25, 0.25)
        hn = fbm(u.shape, max(3.0, length * 0.04), seed + 77, 2)
        hole = ((u - hx) ** 2 + (across - hy * 0.4) ** 2) < (rng.uniform(0.02, 0.05) * (0.6 + 0.8 * hn)) ** 2
    vcol = base * (1 + 0.28 * veins[..., None])
    m = inside & ~hole
    sl_rgb = buf_rgb[y0:y1, x0:x1]
    sl_rgb[m] = vcol[m]
    sl_rgb[pet] = np.array((82, 86, 40)) * tint
    buf_a[y0:y1, x0:x1][m | pet] = 1.0
    # výška pro normal: mírná klenba + vtlačené žilky
    hgt = 0.5 + 0.35 * (1 - (2 * av / np.maximum(wedge, 1e-3)) ** 2) - 0.25 * veins
    buf_h[y0:y1, x0:x1][m] = hgt[m]

def draw_twig(buf_rgb, buf_a, buf_h, pts, width):
    """Větvička jako polyline (kůra světle šedohnědá)."""
    H, W = buf_a.shape
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        x0, x1 = int(max(0, min(ax, bx) - width - 2)), int(min(W, max(ax, bx) + width + 2))
        y0, y1 = int(max(0, min(ay, by) - width - 2)), int(min(H, max(ay, by) + width + 2))
        if x1 <= x0 or y1 <= y0:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        vx, vy = bx - ax, by - ay
        l2 = vx * vx + vy * vy + 1e-9
        t = np.clip(((xx - ax) * vx + (yy - ay) * vy) / l2, 0, 1)
        d = np.hypot(xx - (ax + t * vx), yy - (ay + t * vy))
        m = d < width
        shade = (1 - (d / width) ** 2)
        col = np.array((96, 80, 62))[None, None, :] * (0.65 + 0.35 * shade[..., None])
        buf_rgb[y0:y1, x0:x1][m] = col[m]
        buf_a[y0:y1, x0:x1][m] = 1.0
        buf_h[y0:y1, x0:x1][m] = 0.5 + 0.4 * shade[m]

def draw_blade(rgb, a, h, x0, y0, length, ang, curve, width, col_base, col_tip, dry):
    """Stéblo trávy jako zužující se zakřivený pruh."""
    pts = []
    x, y, an = x0, y0, ang
    n = 24
    for i in range(n + 1):
        pts.append((x, y))
        an += curve / n
        x += math.cos(an) * length / n; y += math.sin(an) * length / n
    H_, W_ = a.shape
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        t = i / n
        wdt = width * (1 - t) ** 0.7 + 0.6
        x0_, x1_ = int(max(0, min(ax, bx) - wdt - 2)), int(min(W_, max(ax, bx) + wdt + 2))
        y0_, y1_ = int(max(0, min(ay, by) - wdt - 2)), int(min(H_, max(ay, by) + wdt + 2))
        if x1_ <= x0_ or y1_ <= y0_: continue
        yy, xx = np.mgrid[y0_:y1_, x0_:x1_].astype(np.float64)
        vx, vy = bx - ax, by - ay; l2 = vx * vx + vy * vy + 1e-9
        tt = np.clip(((xx - ax) * vx + (yy - ay) * vy) / l2, 0, 1)
        d = np.hypot(xx - (ax + tt * vx), yy - (ay + tt * vy))
        m = d < wdt
        k = min(1.0, t * 1.3) ** 2 * dry
        c = np.array(col_base) * (1 - k) + np.array(col_tip) * k
        shade = 0.75 + 0.25 * (1 - d / wdt)
        rgb[y0_:y1_, x0_:x1_][m] = (c[None, None, :] * shade[..., None])[m]
        a[y0_:y1_, x0_:x1_][m] = 1
        h[y0_:y1_, x0_:x1_][m] = (0.5 + 0.4 * (1 - d / wdt))[m]
    return pts[-1]

def make_grass(kind, seed):
    S = CELL * SS
    rgb = np.zeros((S, S, 3)); a = np.zeros((S, S)); h = np.zeros((S, S))
    rr = random.Random(seed)
    tall = kind == "cluster"
    nb = rr.randint(40, 70) if tall else rr.randint(25, 45)
    for i in range(nb):
        x0 = S * 0.5 + rr.gauss(0, S * 0.07)
        L = S * rr.uniform(0.45, 0.95) * (1.0 if tall else 0.6)
        ang = -math.pi / 2 + rr.gauss(0, 0.25)
        curve = rr.gauss(0, 0.9)
        dry = rr.uniform(0.0, 1.0) if rr.random() < 0.6 else 0.0
        base = (rr.uniform(55, 80), rr.uniform(80, 110), rr.uniform(28, 42))
        tip = (rr.uniform(150, 175), rr.uniform(140, 160), rr.uniform(85, 105))
        end = draw_blade(rgb, a, h, x0, S * 0.995, L, ang, curve, S * rr.uniform(0.006, 0.011), base, tip, dry)
        if tall and rr.random() < 0.18:      # klas / lata
            ex, ey = end
            for q in range(rr.randint(8, 16)):
                draw_blade(rgb, a, h, ex + rr.gauss(0, 2), ey + q * S * 0.006, S * rr.uniform(0.02, 0.04),
                           -math.pi / 2 + rr.gauss(0, 0.7), 0, S * 0.004, (150, 140, 90), (175, 160, 110), 1.0)
    return rgb, a, h

TREE = len(sys.argv) > 5 and sys.argv[5] == "strom"

def twig_leaves(rgb, a, h, pts, species, tint, rr, Lleaf, seed, n):
    for i in range(n):
        t = 0.15 + 0.85 * i / max(1, n - 1)
        k = t * (len(pts) - 1); j = min(int(k), len(pts) - 2); f = k - j
        px = pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f
        py = pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f
        dx, dy = pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1]
        base = math.atan2(dy, dx)
        side = 1 if i % 2 else -1
        la = base + side * rr.uniform(0.5, 1.0)
        L = Lleaf * rr.uniform(0.75, 1.1) * (0.85 + 0.25 * t)
        pet = L * 0.12
        draw_leaf(rgb, a, h, px + math.cos(la) * pet, py + math.sin(la) * pet, L, la, species, tint * rr.uniform(0.88, 1.1), seed * 31 + i)

def make_branchlet(species, seed):
    """Větévka stromu: hlavní výhon s 3–5 postranními, 20–35 listů, list ~1/9 karty."""
    S = CELL * SS
    rgb = np.zeros((S, S, 3)); a = np.zeros((S, S)); h = np.zeros((S, S))
    rr = random.Random(seed)
    tint = np.array([rr.uniform(0.9, 1.08), rr.uniform(0.92, 1.06), rr.uniform(0.85, 1.05)])
    if rr.random() < 0.12: tint = tint * np.array((1.2, 1.06, 0.78))
    Lleaf = S * {"dub": 0.13, "lipa": 0.12, "buk": 0.11, "briza": 0.075, "olse": 0.12, "vrba": 0.15}.get(species, 0.11)
    main = [(S * 0.5, S * 0.99)]; x, y, ang = S * 0.5, S * 0.99, -math.pi / 2 + rr.uniform(-0.15, 0.15)
    for i in range(10):
        ang += rr.uniform(-0.15, 0.15); x += math.cos(ang) * S * 0.08; y += math.sin(ang) * S * 0.08
        main.append((x, y))
    draw_twig(rgb, a, h, main, S * 0.008)
    sides = []
    nsides = rr.randint(5, 7)
    for k in range(nsides):
        t = 0.12 + 0.75 * k / nsides
        j = int(t * (len(main) - 1)); sx, sy = main[j]
        sd = 1 if k % 2 else -1
        an = -math.pi / 2 + sd * rr.uniform(0.55, 1.05)
        pts = [(sx, sy)]
        for q in range(5):
            an += rr.uniform(-0.12, 0.12) - sd * 0.06
            sx += math.cos(an) * S * 0.06; sy += math.sin(an) * S * 0.06
            pts.append((sx, sy))
        draw_twig(rgb, a, h, pts, S * 0.005)
        sides.append(pts)
    # listy: nejdřív postranní (vzadu), pak hlavní
    for k, pts in enumerate(sides):
        twig_leaves(rgb, a, h, pts, species, tint, rr, Lleaf, seed * 7 + k, rr.randint(6, 9))
    twig_leaves(rgb, a, h, main[2:], species, tint, rr, Lleaf * 1.05, seed * 11, rr.randint(8, 12))
    return rgb, a, h

def make_conifer(species, seed):
    """Jehličnatá větévka: hlavní osa + postranní výhony hustě obsypané jehlicemi."""
    S = CELL * SS
    rgb = np.zeros((S, S, 3)); a = np.zeros((S, S)); h = np.zeros((S, S))
    rr = random.Random(seed)
    fir = species == "jedle"
    spruce = species in ("smrk", "jedle")
    nd = (58, 92, 42) if fir else ((64, 92, 48) if spruce else (88, 114, 60))
    nt = (98, 136, 66) if fir else ((104, 138, 76) if spruce else (138, 160, 92))
    main = [(S * 0.5, S * 0.99)]; x, y, ang = S * 0.5, S * 0.99, -math.pi / 2
    for i in range(10):
        ang += rr.uniform(-0.08, 0.08); x += math.cos(ang) * S * 0.08; y += math.sin(ang) * S * 0.08
        main.append((x, y))
    shoots = [main]
    for k in range(rr.randint(7, 10) if spruce else rr.randint(5, 7)):
        t = min(0.95, 0.12 + 0.8 * k / 10)
        j = int(t * (len(main) - 1)); sx, sy = main[j]
        sd = 1 if k % 2 else -1; an = -math.pi / 2 + sd * (rr.uniform(1.0, 1.3) if spruce else rr.uniform(0.7, 1.1))
        pts = [(sx, sy)]
        for q in range(5):
            sx += math.cos(an) * S * (0.07 if spruce else 0.06); sy += math.sin(an) * S * (0.07 if spruce else 0.06)
            an += -sd * 0.05; pts.append((sx, sy))
        shoots.append(pts)
    for pts in shoots:
        draw_twig(rgb, a, h, pts, S * 0.006)
    for pts in shoots:
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            base = math.atan2(by - ay, bx - ax)
            nn = 10 if fir else (20 if spruce else 14)
            for q in range(nn):
                f = q / nn
                px, py = ax + (bx - ax) * f, ay + (by - ay) * f
                for sd in (-1, 1):
                    L = S * (0.05 if fir else (0.05 if spruce else 0.09)) * rr.uniform(0.8, 1.15)
                    an = base + sd * (rr.uniform(1.25, 1.5) if fir else (rr.uniform(0.35, 1.35) if spruce and not fir else rr.uniform(0.25, 0.6)))
                    c0 = tuple(np.array(nd) * rr.uniform(0.85, 1.15)); c1 = tuple(np.array(nt) * rr.uniform(0.9, 1.1))
                    draw_blade(rgb, a, h, px, py, L, an, rr.gauss(0, 0.2), S * (0.0045 if fir else (0.0035 if spruce else 0.0042)), c0, c1, 1.0)
    if not spruce and rr.random() < 0.3:     # šiška
        cx_, cy_ = shoots[-1][-1]
        yy, xx = np.mgrid[0:S, 0:S]
        m = ((xx - cx_) / (S * 0.025)) ** 2 + ((yy - cy_ - S * 0.03) / (S * 0.045)) ** 2 < 1
        rgb[m] = np.array((92, 70, 44)); a[m] = 1; h[m] = 0.8
    return rgb, a, h

def make_card(species, kind, seed):
    if species in ("smrk", "borovice", "jedle"):
        return make_conifer(species, seed)
    if species == "trava":
        return make_grass(kind, seed)
    if TREE and kind == "cluster":
        return make_branchlet(species, seed)
    S = CELL * SS
    rgb = np.zeros((S, S, 3)); a = np.zeros((S, S)); h = np.zeros((S, S))
    rr = random.Random(seed)
    tint = np.array([rr.uniform(0.9, 1.08), rr.uniform(0.92, 1.06), rr.uniform(0.85, 1.05)])
    if rr.random() < 0.15:        # podzimní nádech
        tint = tint * np.array((1.25, 1.08, 0.75))
    # větvička od spodního středu vzhůru
    n = rr.randint(5, 9) if kind == "cluster" else 1
    if kind == "cluster":
        pts = [(S * 0.5, S * 0.98)]
        x, y, ang = S * 0.5, S * 0.98, -math.pi / 2 + rr.uniform(-0.2, 0.2)
        for i in range(8):
            ang += rr.uniform(-0.18, 0.18)
            x += math.cos(ang) * S * 0.095; y += math.sin(ang) * S * 0.095
            pts.append((x, y))
        draw_twig(rgb, a, h, pts, S * 0.007)
        if species in ("bez", "sipek"):
            # zpeřené listy: vřeteno + páry lístků + koncový lístek
            for i in range(rr.randint(3, 5) if species == "bez" else rr.randint(4, 6)):
                t = 0.15 + 0.8 * i / 4
                k = t * (len(pts) - 1); j = min(int(k), len(pts) - 2); f = k - j
                px = pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f
                py = pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f
                side = 1 if i % 2 else -1
                ra = -math.pi / 2 + side * rr.uniform(0.5, 1.0)
                RL = S * (0.42 if species == "bez" else 0.3) * rr.uniform(0.8, 1.05)
                rpts = [(px, py)]
                for q in range(6):
                    rpts.append((px + math.cos(ra) * RL * (q + 1) / 6, py + math.sin(ra) * RL * (q + 1) / 6))
                draw_twig(rgb, a, h, rpts, S * 0.004)
                npair = 2 if species == "bez" else 3
                LL = S * (0.17 if species == "bez" else 0.085)
                for q in range(npair):
                    tq = 0.25 + 0.6 * q / max(1, npair)
                    qx, qy = px + math.cos(ra) * RL * tq, py + math.sin(ra) * RL * tq
                    for sd in (-1, 1):
                        la = ra + sd * rr.uniform(0.9, 1.2)
                        draw_leaf(rgb, a, h, qx, qy, LL * rr.uniform(0.85, 1.1), la, species, tint * rr.uniform(0.9, 1.08), seed * 53 + i * 7 + q * 2 + (sd > 0))
                draw_leaf(rgb, a, h, rpts[-1][0], rpts[-1][1], LL * 1.1, ra, species, tint, seed * 59 + i)
            if species == "sipek" and rr.random() < 0.5:      # šípky
                for q in range(rr.randint(1, 3)):
                    hx, hy = pts[-1][0] + rr.uniform(-S * 0.08, S * 0.08), pts[-1][1] + rr.uniform(0, S * 0.1)
                    yy, xx = np.mgrid[0:S, 0:S]
                    m = ((xx - hx) / (S * 0.022)) ** 2 + ((yy - hy) / (S * 0.032)) ** 2 < 1
                    rgb[m] = np.array((150, 28, 18)); a[m] = 1; h[m] = 0.9
            if species == "bez" and rr.random() < 0.5:        # chocholík bobulí
                cx_, cy_ = pts[-1][0], pts[-1][1] + S * 0.05
                yy, xx = np.mgrid[0:S, 0:S]
                for q in range(rr.randint(25, 45)):
                    bx, by = cx_ + rr.gauss(0, S * 0.05), cy_ + rr.gauss(0, S * 0.03)
                    m = (xx - bx) ** 2 + (yy - by) ** 2 < (S * 0.008) ** 2
                    rgb[m] = np.array((24, 18, 26)); a[m] = 1; h[m] = 0.8
            return rgb, a, h
        # listy střídavě podél větvičky, od spodu (vzadu) po špičku
        Lbase = S * {"liska": 0.30, "hloh": 0.24, "dub": 0.32, "lipa": 0.3, "buk": 0.26, "briza": 0.18}.get(species, 0.2)
        for i in range(n):
            t = 0.12 + 0.85 * i / max(1, n - 1)
            k = t * (len(pts) - 1); j = min(int(k), len(pts) - 2); f = k - j
            px = pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f
            py = pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f
            side = 1 if i % 2 else -1
            la = -math.pi / 2 + side * rr.uniform(0.55, 1.05) + rr.uniform(-0.12, 0.12)
            L = Lbase * rr.uniform(0.7, 1.05) * (0.8 + 0.3 * t)
            pet = L * 0.14
            draw_leaf(rgb, a, h, px + math.cos(la) * pet, py + math.sin(la) * pet, L, la, species, tint * rr.uniform(0.88, 1.08), seed * 31 + i)
    else:
        draw_leaf(rgb, a, h, S * 0.5, S * 0.9, S * 0.78, -math.pi / 2, species, tint, seed)
    return rgb, a, h

def main():
    S = CELL * SS
    big_rgb = np.zeros((GRID * S, GRID * S, 3)); big_a = np.zeros((GRID * S, GRID * S)); big_h = np.zeros((GRID * S, GRID * S))
    cards = []
    for gy in range(GRID):
        for gx in range(GRID):
            idx = gy * GRID + gx
            kind = "cluster" if idx < 12 else "single"
            rgb, a, h = make_card(SPECIES, kind, SEED * 100 + idx)
            big_rgb[gy * S:(gy + 1) * S, gx * S:(gx + 1) * S] = rgb
            big_a[gy * S:(gy + 1) * S, gx * S:(gx + 1) * S] = a
            big_h[gy * S:(gy + 1) * S, gx * S:(gx + 1) * S] = h
            # UV obdélník karty (glTF/Blender: v roste nahoru)
            cards.append({"kind": kind, "u0": gx / GRID, "u1": (gx + 1) / GRID,
                          "v0": 1 - (gy + 1) / GRID, "v1": 1 - gy / GRID})
    # zmenšení (supersampling) – barvu rozšířit pod průhledné okraje (proti tmavým lemům)
    img = Image.fromarray(np.clip(big_rgb, 0, 255).astype(np.uint8))
    alpha = Image.fromarray((big_a * 255).astype(np.uint8))
    dil = img
    for _ in range(6):
        dil = dil.filter(ImageFilter.MaxFilter(5))
    comp = Image.composite(img, dil, alpha)
    comp = comp.resize((PX, PX), Image.LANCZOS)
    alpha_s = alpha.resize((PX, PX), Image.LANCZOS)
    out = comp.convert("RGBA"); out.putalpha(alpha_s)
    out.save(PREFIX + "_color.png")
    # normal z výšky
    hh = Image.fromarray((big_h * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)).resize((PX, PX), Image.LANCZOS)
    hz = np.asarray(hh).astype(np.float64) / 255.0
    gx = np.zeros_like(hz); gy = np.zeros_like(hz)
    gx[:, 1:-1] = (hz[:, 2:] - hz[:, :-2]) * 0.5; gy[1:-1, :] = (hz[2:, :] - hz[:-2, :]) * 0.5
    st = 6.0
    nx, ny, nz = -gx * st, gy * st, np.ones_like(hz)       # OpenGL: Y nahoru
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nrm = np.stack([(nx / ln) * 0.5 + 0.5, (ny / ln) * 0.5 + 0.5, (nz / ln) * 0.5 + 0.5], -1)
    Image.fromarray((nrm * 255).astype(np.uint8)).save(PREFIX + "_normal.png")
    json.dump({"species": SPECIES, "grid": GRID, "cards": cards}, open(PREFIX + "_cards.json", "w"))
    print("ATLAS", PREFIX, PX)

main()
