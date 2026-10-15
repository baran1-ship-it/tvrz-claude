"""Stromy v2: kostra rostoucí k obálce koruny (plná souvislá koruna), správné poměry kmene,
koruna z překrývajících se karet větévek, světlo/stín koruny zapečené do barvy vrcholů (COLOR_0).
Spuštění: python3 tree2_geo.py <druh> <seed> <název> <mlady|stredni|stary>
Druhy: dub lipa buk briza olse vrba vrba_hlavata smrk jedle borovice
"""
import sys, os, math, json, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Quaternion, Matrix, noise
from PIL import Image, ImageFilter

SPECIES, SEED, NAME, AGE = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
rng = random.Random(SEED); np.random.seed(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)
AI = {"mlady": 0, "stredni": 1, "stary": 2}[AGE]
def by_age(t): return t[AI]

# ------------------------------------------------------------------ parametry druhů
# arch: broad = listnáč (kmen se větví do obálky), cone = smrk/jedle, pine, pollard = hlavatá vrba
# H výška, r0 poloměr kmene u země, fork = výška rozvětvení (podíl H; 1 = kmen až do vrcholu)
# crown = (spodek koruny podíl H, poloměr koruny podíl H, tvar), limbs = počet hlavních větví
SPC = {
 "dub":   dict(arch="broad", H=((6, 8), (12, 15), (14, 18)), r0=(0.12, 0.38, 0.75), fork=(0.55, 0.32, 0.22),
               crown=((0.3, 0.45), (0.27, 0.5), (0.24, 0.68)), shape="dome", limbs=((5, 7), (5, 7), (4, 6)),
               elev=(0.35, 1.0), crook=0.55, droop=0.15, dead=(0, 1, 3), leaf="dub",
               bark=((48, 42, 36), (112, 102, 90)), furrow=1.0, budget=(9000, 20000, 29500)),
 "lipa":  dict(arch="broad", H=((6, 8), (13, 16), (18, 23)), r0=(0.12, 0.33, 0.62), fork=(1.0, 1.0, 0.45),
               crown=((0.25, 0.32), (0.22, 0.32), (0.2, 0.38)), shape="oval", limbs=((8, 11), (10, 14), (8, 11)),
               elev=(0.5, 1.15), crook=0.3, droop=0.25, dead=(0, 0, 2), leaf="lipa",
               bark=((56, 50, 44), (118, 110, 98)), furrow=0.6, budget=(9000, 20000, 29500)),
 "buk":   dict(arch="broad", H=((6, 8), (14, 18), (20, 25)), r0=(0.1, 0.3, 0.55), fork=(1.0, 0.7, 0.45),
               crown=((0.3, 0.3), (0.28, 0.3), (0.25, 0.34)), shape="oval", limbs=((8, 11), (9, 12), (7, 10)),
               elev=(0.65, 1.25), crook=0.25, droop=0.15, dead=(0, 0, 1), leaf="buk",
               bark=((96, 96, 92), (150, 150, 144)), furrow=0.0, budget=(9000, 20000, 29500)),
 "briza": dict(arch="broad", H=((6, 8), (13, 16), (17, 21)), r0=(0.07, 0.17, 0.27), fork=(1.0, 1.0, 1.0),
               crown=((0.35, 0.22), (0.35, 0.22), (0.3, 0.25)), shape="oval", limbs=((10, 14), (12, 16), (12, 16)),
               elev=(0.7, 1.2), crook=0.3, droop=0.55, dead=(0, 0, 1), leaf="briza",
               bark=((214, 210, 200), (240, 236, 226)), furrow=0.0, birch=True, budget=(8000, 18000, 26000)),
 "olse":  dict(arch="broad", H=((6, 8), (12, 15), (16, 20)), r0=(0.1, 0.22, 0.38), fork=(1.0, 1.0, 1.0),
               crown=((0.3, 0.24), (0.3, 0.24), (0.28, 0.26)), shape="cone", limbs=((10, 14), (12, 16), (12, 16)),
               elev=(0.55, 1.0), crook=0.3, droop=0.1, dead=(0, 1, 2), leaf="olse", stems=(1, 3),
               bark=((44, 40, 36), (92, 86, 78)), furrow=0.7, budget=(8000, 18000, 26000)),
 "vrba":  dict(arch="broad", H=((5, 7), (10, 13), (13, 17)), r0=(0.14, 0.4, 0.65), fork=(0.5, 0.3, 0.22),
               crown=((0.3, 0.45), (0.27, 0.52), (0.24, 0.6)), shape="dome", limbs=((5, 7), (5, 7), (4, 6)),
               elev=(0.6, 1.2), crook=0.5, droop=0.15, dead=(0, 1, 3), leaf="vrba", lean=0.18,
               bark=((58, 52, 44), (130, 120, 104)), furrow=1.0, budget=(9000, 20000, 29500)),
 "vrba_hlavata": dict(arch="pollard", H=((3.5, 4.5), (5, 6), (6, 7.5)), r0=(0.18, 0.32, 0.5), leaf="vrba",
               bark=((58, 52, 44), (130, 120, 104)), furrow=1.0, budget=(7000, 12000, 16000)),
 "smrk":  dict(arch="cone", H=((6, 8.5), (13, 16), (22, 26)), r0=(0.1, 0.25, 0.45), crownR=(0.24, 0.2, 0.17),
               whorl=(0.42, 0.55, 0.62), droopc=0.35, leaf="smrk", deadfrac=(0.0, 0.12, 0.33),
               bark=((70, 58, 50), (128, 112, 100)), furrow=0.3, scaly=True, budget=(9000, 20000, 29500)),
 "jedle": dict(arch="cone", H=((6, 8.5), (14, 17), (24, 28)), r0=(0.1, 0.27, 0.5), crownR=(0.25, 0.21, 0.17),
               whorl=(0.4, 0.55, 0.65), droopc=0.08, leaf="jedle", deadfrac=(0.0, 0.1, 0.3), flattop=True,
               bark=((80, 78, 74), (134, 130, 122)), furrow=0.15, budget=(9000, 20000, 29500)),
 "borovice": dict(arch="broad", H=((6, 8), (12, 15), (18, 22)), r0=(0.1, 0.22, 0.36), fork=(1.0, 1.0, 1.0),
               crown=((0.35, 0.22), (0.5, 0.22), (0.6, 0.24)), shape="umbrella", limbs=((10, 13), (9, 12), (8, 11)),
               elev=(0.3, 0.9), crook=0.5, droop=0.0, dead=(0, 2, 4), leaf="borovice", pinebark=True,
               bark=((150, 92, 56), (205, 140, 92)), furrow=0.55, budget=(7000, 13000, 17000)),
}
SP = SPC[SPECIES]
H = rng.uniform(*by_age(SP["H"]))
R0 = by_age(SP["r0"]) * rng.uniform(0.9, 1.1)
BUDGET = by_age(SP["budget"])
CARD = by_age(((0.75, 1.0), (1.05, 1.4), (1.25, 1.7)))
if SP["arch"] == "cone":
    CARD = (CARD[0] * 1.1, CARD[1] * 1.15)

# ------------------------------------------------------------------ kůra
def pnoise(n, cx, cy, seed):
    r = np.random.RandomState(seed); g = r.rand(cy, cx)
    ty = np.arange(n) / n * cy; tx = np.arange(n) / n * cx
    iy, ix = ty.astype(int), tx.astype(int); fy, fx = ty - iy, tx - ix
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    iy1, ix1 = (iy + 1) % cy, (ix + 1) % cx
    a = g[iy][:, ix]; b = g[iy][:, ix1]; c = g[iy1][:, ix]; d = g[iy1][:, ix1]
    top = a + (b - a) * fx[None, :]; bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]

def bark_texture(px=1024):
    n = sum(pnoise(px, 4 * 2 ** o, 2 * 2 ** o, SEED + o) * 0.55 ** o for o in range(5)) / 2.0
    fur = pnoise(px, 24, 3, SEED + 50) * 0.7 + pnoise(px, 48, 6, SEED + 51) * 0.3
    F = SP["furrow"]
    ridges = np.clip((fur - 0.42) * 4, 0, 1)
    crossb = np.clip((pnoise(px, 10, 30, SEED + 52) - 0.3) * 3, 0, 1)
    ridges = ridges * (0.6 + 0.4 * crossb)
    if SP.get("scaly") or SP.get("pinebark"):
        # šupiny / plotny: buňky, mezi nimi tmavé spáry
        cells = pnoise(px, 26, 40, SEED + 80)
        q = np.floor(cells * 7) / 7
        edge = np.abs(cells * 7 - np.round(cells * 7))
        ridges = np.clip(q * 0.8 + 0.2, 0, 1) * np.clip(edge * 6, 0, 1)
        F = 0.8
    dark, light = np.array(SP["bark"][0]), np.array(SP["bark"][1])
    t = np.clip(n * 0.5 + ridges * 0.5 * F + (1 - F) * n * 0.5, 0, 1)
    col = dark[None, None, :] * (1 - t[..., None]) + light[None, None, :] * t[..., None]
    if SP.get("birch"):
        lent = np.zeros((px, px)); rr = np.random.RandomState(SEED + 9)
        for _ in range(int(px * 0.6)):
            y, x = rr.randint(0, px), rr.randint(0, px); L = rr.randint(px // 40, px // 12)
            lent[y:y + rr.randint(1, 4), :][:, (np.arange(L) + x) % px] = 1
        lent = np.asarray(Image.fromarray((lent * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))) / 255
        blk = np.clip((pnoise(px, 8, 16, SEED + 60) - 0.62) * 6, 0, 1)
        col = col * (1 - lent[..., None] * 0.7) + np.array((40, 36, 34))[None, None, :] * lent[..., None] * 0.7
        col = col * (1 - blk[..., None]) + np.array((30, 28, 26))[None, None, :] * blk[..., None]
        ridges = 1 - blk * 0.8
    lich = np.clip((pnoise(px, 6, 6, SEED + 70) * pnoise(px, 20, 20, SEED + 71) - 0.36) * 5, 0, 1)
    col = col * (1 - 0.4 * lich[..., None]) + np.array((122, 132, 104))[None, None, :] * 0.4 * lich[..., None]
    Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f"{NAME}_kura_color.png"))
    hgt = n * 0.4 + ridges * 0.8
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5; gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
    st = 4.0 + 8.0 * F
    nx, ny, nz = -gx * st, gy * st, np.ones_like(hgt); ln = np.sqrt(nx ** 2 + ny ** 2 + 1)
    Image.fromarray(((np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5) * 255).astype(np.uint8)).save(
        os.path.join(OUT, f"{NAME}_kura_normal.png"))
bark_texture()

# ------------------------------------------------------------------ obálka koruny
def crown_params():
    if SP["arch"] in ("broad",):
        c0, rr_ = by_age(SP["crown"])
        return c0 * H, rr_ * H
    return 0.0, 1.0
CZ0, CR = crown_params()

def env_radius(z):
    """Poloměr obálky koruny ve výšce z."""
    if SP["arch"] != "broad":
        return 1.0
    u = (z - CZ0) / max(0.1, H - CZ0)
    if u <= 0 or u >= 1:
        return 0.15 * CR
    shp = SP["shape"]
    if shp == "dome":       # široká nízká klenba (starý dub, vrba), spodek se rychle zaobluje
        c = 0.4
        k = (u - c) / ((1 - c) if u > c else c)
        return CR * math.sqrt(max(0.02, 1 - k * k))
    if shp == "oval":
        return CR * (math.sin(math.pi * u) ** 0.65)
    if shp == "cone":
        return CR * (math.sin(math.pi * min(1.0, u * 0.6 + 0.08)) ** 0.8) * (1.05 - 0.75 * u)
    if shp == "umbrella":   # borovice: plochý deštník
        return CR * (math.sin(math.pi * min(1.0, u * 0.7 + 0.3)) ** 0.5)
    return CR

def env_point(az, z):
    r = env_radius(z) * rng.uniform(0.82, 1.02)
    return Vector((math.cos(az) * r, math.sin(az) * r, z))

# ------------------------------------------------------------------ kostra
BR = []   # dict(pts, rads, level, dead)
def grow(p0, d0, L, r0, level, target=None, crook=0.3, droop=0.0, seg=0.5, r_end=None, dead=False, up=0.0):
    pts, rads = [Vector(p0)], [r0]
    d = Vector(d0).normalized(); p = Vector(p0)
    n = max(2, int(L / seg))
    r_end = r_end if r_end is not None else max(0.006, r0 * 0.12)
    for i in range(1, n + 1):
        t = i / n
        if target is not None:
            want = (target - p)
            if want.length > 1e-3:
                d = (d * 0.65 + want.normalized() * 0.35).normalized()
        wob = Vector((noise.noise(Vector((p.x * 0.6 + level * 13, p.y * 0.6, i * 0.37 + SEED))),
                      noise.noise(Vector((p.y * 0.6, i * 0.37 + SEED, p.x * 0.6 + 7))),
                      noise.noise(Vector((i * 0.37, p.x * 0.6 + 3, p.y * 0.6 + SEED))) * 0.5)) * crook * 0.5
        if rng.random() < crook * 0.12:                 # zalomení (lomené větve dubu)
            ax = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 0.3))).normalized()
            d = (Quaternion(ax, rng.uniform(0.25, 0.6)) @ d).normalized()
        d = (d + wob + Vector((0, 0, up - droop * t * t))).normalized()
        p = p + d * (L / n)
        pts.append(p.copy()); rads.append(r0 + (r_end - r0) * (t ** 0.9))
    b = dict(pts=pts, rads=rads, level=level, dead=dead)
    BR.append(b)
    return b

def along(b, t):
    pts = b["pts"]; k = t * (len(pts) - 1); j = min(int(k), len(pts) - 2); f = k - j
    p = pts[j].lerp(pts[j + 1], f); r = b["rads"][j] * (1 - f) + b["rads"][j + 1] * f
    d = (pts[j + 1] - pts[j]).normalized()
    return p, d, r

def side_dir(d, az_bias=None, elev=None):
    s = d.cross(Vector((0, 0, 1)))
    if s.length < 0.1: s = Vector((1, 0, 0))
    s = (Quaternion(d, rng.uniform(0, math.tau)) @ s.normalized())
    return s

def twigs_on(b, n_per_m, L_rng, dead=False):
    """Krátké koncové větévky (3. řád) – nesou listí."""
    L = sum((q - p).length for p, q in zip(b["pts"][:-1], b["pts"][1:]))
    n = max(1, int(L * n_per_m))
    for k in range(n):
        t = rng.uniform(0.25, 1.0)
        p, d, r = along(b, t)
        out = Vector((p.x, p.y, 0)); out = out.normalized() if out.length > 0.05 else side_dir(d)
        nd = (d * 0.4 + out * 0.6 + side_dir(d) * 0.6 + Vector((0, 0, 0.25))).normalized()
        Lt = rng.uniform(*L_rng)
        grow(p, nd, Lt, max(0.006, r * 0.5), 3, crook=0.5, droop=SP.get("droop", 0) * 0.6,
             seg=Lt / 1.5, dead=dead)

SEEDS = []
SC_NODES = []   # (pozice, počet listů v podstromu) – kandidáti na listí

def space_colonize():
    """Kolonizace prostoru: větve dorůstají k bodům rozmístěným v obálce koruny -> plná koruna."""
    from mathutils.kdtree import KDTree
    nattr = by_age((450, 1100, 1700))
    attr = []
    tries = 0
    # shluky (kupovitá koruna): část bodů v elipsoidech kolem náhodných míst na obálce
    clump = {"borovice": 0.95, "dub": 0.6, "vrba": 0.65, "briza": 0.6}.get(SPECIES, 0.5)
    nclu = by_age((5, 9, 13)) if SPECIES != "borovice" else by_age((6, 9, 12))
    centers = []
    for k in range(nclu):
        zc = rng.uniform(CZ0 + (H - CZ0) * (0.55 if SPECIES == "borovice" else 0.2), H * 0.97)
        ac = rng.uniform(0, math.tau)
        rc = env_radius(zc) * rng.uniform(0.45, 0.9)
        centers.append((Vector((math.cos(ac) * rc, math.sin(ac) * rc, zc)), rng.uniform(0.18, 0.3) * max(CR, 2.0)))
    while len(attr) < nattr * clump and centers:
        c, rad_ = centers[rng.randrange(len(centers))]
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 0.35 if SPECIES == "borovice" else 0.55))) * rad_ * 0.5
        attr.append(c + v)
    while len(attr) < nattr and tries < nattr * 40:
        tries += 1
        z = rng.uniform(CZ0, H)
        a = rng.uniform(0, math.tau)
        R = env_radius(z) * (0.62 + 0.55 * (noise.noise(Vector((math.cos(a) * 1.3, math.sin(a) * 1.3, z * 0.25 + SEED))) * 0.5 + 0.5))
        rr = R * math.sqrt(rng.uniform(0.12, 1.0))
        attr.append(Vector((math.cos(a) * rr, math.sin(a) * rr, z)))
    nodes, parent, rootb = [], [], []
    for b in SEEDS:
        pts = b["pts"]
        for i in range(len(pts) // 3, len(pts)):
            nodes.append(pts[i].copy()); parent.append(-1); rootb.append((b, i))
    D = by_age((0.35, 0.55, 0.65)); di = D * 7; dk = D * 1.6
    for it in range(60):
        if not attr: break
        kd = KDTree(len(nodes))
        for i, p in enumerate(nodes): kd.insert(p, i)
        kd.balance()
        acc = {}
        for a in attr:
            co, i, dist = kd.find(a)
            if dist < di:
                v = (a - co).normalized()
                acc.setdefault(i, Vector()); acc[i] += v
        if not acc: break
        new = []
        for i, v in acc.items():
            dvec = (v.normalized() + Vector((0, 0, 0.12 - SP["droop"] * 0.15)) +
                    Vector((rng.gauss(0, 0.15), rng.gauss(0, 0.15), rng.gauss(0, 0.1)))).normalized()
            q = nodes[i] + dvec * D
            nodes.append(q); parent.append(i); rootb.append(None); new.append(q)
        kd2 = KDTree(len(new))
        for i, p in enumerate(new): kd2.insert(p, i)
        kd2.balance()
        attr = [a for a in attr if kd2.find(a)[2] > dk]
    n = len(nodes)
    cnt = [1] * n
    for i in range(n - 1, -1, -1):
        if parent[i] >= 0: cnt[parent[i]] += cnt[i]
    children = [[] for _ in range(n)]
    for i in range(n):
        if parent[i] >= 0: children[parent[i]].append(i)
    rt = by_age((0.006, 0.008, 0.009))
    def rad(i): return rt * cnt[i] ** 0.45
    # řetězce -> větve
    def chain(start, level):
        pts = [nodes[start]]; rads = [rad(start)]
        cur = start
        while children[cur]:
            ch = sorted(children[cur], key=lambda c: -cnt[c])
            for c in ch[1:]:
                chain_from(cur, c, min(3, level + 1))
            cur = ch[0]
            pts.append(nodes[cur]); rads.append(rad(cur))
        return pts, rads
    def chain_from(par, c, level):
        pts, rads = chain(c, level)
        pts.insert(0, nodes[par]); rads.insert(0, rads[0])
        BR.append(dict(pts=pts, rads=rads, level=level, dead=False, sc=True))
    for i in range(n):
        if parent[i] == -1:
            for c in children[i]:
                chain_from(i, c, 2)
    for i in range(n):
        if rootb[i] is None:
            SC_NODES.append((nodes[i], cnt[i], nodes[parent[i]]))

def build_broad():
    stems = rng.randint(*SP.get("stems", (1, 1))) if AGE != "mlady" else 1
    fork = by_age(SP["fork"])
    lean = SP.get("lean", 0.04)
    nl = rng.randint(*by_age(SP["limbs"]))
    ndead = by_age(SP["dead"])
    for s in range(stems):
        la = rng.uniform(0, math.tau); ls = lean * rng.uniform(0.3, 1.0) + (0.12 if stems > 1 else 0)
        base = Vector((math.cos(la) * 0.15 * (s > 0), math.sin(la) * 0.15 * (s > 0), -0.2))
        r0 = R0 * (1.0 if s == 0 else 0.7)
        excur = fork >= 0.99
        trunk_L = H * (0.97 if excur else fork)
        trunk = grow(base, Vector((math.cos(la) * ls, math.sin(la) * ls, 1)), trunk_L + 0.2, r0, 0,
                     crook=0.12 + 0.2 * SP["crook"], seg=max(0.4, trunk_L / 14),
                     r_end=r0 * (0.12 if excur else 0.72))
        # hlavní větve
        if excur:
            t0 = max(0.08, (CZ0 + 0.3) / trunk_L)
            ts = sorted(rng.uniform(t0, 0.96) for _ in range(nl))
        else:
            ts = sorted(rng.uniform(0.82, 1.0) for _ in range(nl))
        az0 = rng.uniform(0, math.tau)
        for k, t in enumerate(ts):
            p, d, r = along(trunk, t)
            az = az0 + k * 2.39996 + rng.uniform(-0.4, 0.4)
            emin, emax = SP["elev"]
            u = (p.z - CZ0) / max(0.1, H - CZ0)
            el = emin + (emax - emin) * min(1.0, max(0.0, u)) + rng.uniform(-0.15, 0.15)
            if not excur:
                el = rng.uniform(0.35, 1.1)
            zt = min(H * 0.98, max(CZ0 + 0.5, p.z + math.tan(el) * env_radius(p.z + 1.0) * 0.9))
            if not excur:
                zt = CZ0 + (H - CZ0) * rng.uniform(0.3, 0.85)
            if SP["shape"] == "umbrella":
                zt = rng.uniform(max(p.z, H * 0.82), H * 0.98)
            tgt = env_point(az, zt)
            L = (tgt - p).length * rng.uniform(0.85, 1.0)
            dd = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
            rl = r * (0.55 if not excur else 0.42) * rng.uniform(0.85, 1.1)
            limb = grow(p - d * r * 0.3, dd, L * 0.62, rl, 1, target=tgt, crook=SP["crook"], droop=SP["droop"] * 0.6,
                        seg=0.6 if AGE != "mlady" else 0.35, dead=False)
            SEEDS.append(limb)
        # suché větve (dub, vrba, borovice …)
        for k in range(ndead):
            t = rng.uniform(0.3, 0.95) if excur else rng.uniform(0.9, 1.0)
            p, d, r = along(trunk, t)
            az = rng.uniform(0, math.tau)
            if SP["shape"] == "dome":
                el = rng.uniform(0.55, 1.15)
                zt = H * rng.uniform(0.95, 1.08)       # suchá větev prostrčená nad korunu
                L = max(2.0, (zt - p.z) / max(0.3, math.sin(el)) * rng.uniform(0.9, 1.05))
            else:
                p, d, r = along(trunk, rng.uniform(0.12, max(0.15, CZ0 / trunk_L)))   # pahýl pod korunou
                el = rng.uniform(-0.3, 0.3); L = rng.uniform(0.4, 2.0)
            dd = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
            db = grow(p, dd, L, r * 0.2, 1, crook=0.8, seg=0.5, dead=True, r_end=0.012)
            for q in range(rng.randint(2, 4)):
                p2, d2, r2 = along(db, rng.uniform(0.3, 0.9))
                grow(p2, (d2 + side_dir(d2) * 0.8).normalized(), rng.uniform(0.3, 1.0), r2 * 0.5, 2,
                     crook=0.8, seg=0.3, dead=True)

def build_cone():
    sm = SPECIES == "smrk"
    crownR = by_age(SP["crownR"]) * H
    trunk = grow(Vector((0, 0, -0.2)), Vector((rng.gauss(0, 0.01), rng.gauss(0, 0.01), 1)), H + 0.2, R0, 0,
                 crook=0.05, seg=max(0.4, H / 18), r_end=0.015)
    dz = by_age(SP["whorl"])
    deadz = by_age(SP["deadfrac"]) * H
    z = 0.35 if AGE == "mlady" else 0.6
    flat = SP.get("flattop") and AGE == "stary"
    while z < H - 0.25:
        u = z / H
        p, d, r = along(trunk, min(0.999, (z + 0.2) / (H + 0.2)))
        nwh = rng.randint(4, 6)
        a0 = rng.uniform(0, math.tau)
        for k in range(nwh):
            az = a0 + k * math.tau / nwh + rng.uniform(-0.35, 0.35)
            uc = max(0.0, (z - deadz) / max(1.0, H - deadz))
            Rz = crownR * (1 - uc) ** 1.1 + 0.2
            if flat and uc > 0.9:
                Rz = max(Rz, crownR * 0.2)
            if z < deadz:
                # suchá spodní část: holé pahýly, občas delší suchá větev
                L = rng.uniform(0.3, 1.0) if rng.random() < 0.7 else rng.uniform(1.2, 2.4)
                dd = Vector((math.cos(az), math.sin(az), rng.uniform(-0.5, -0.05))).normalized()
                db = grow(p, dd, L, max(0.015, r * 0.12), 1, crook=0.5, seg=0.4, dead=True, r_end=0.006)
                if L > 0.8:
                    for q in range(rng.randint(1, 3)):
                        p2, d2, r2 = along(db, rng.uniform(0.3, 0.9))
                        grow(p2, (d2 + side_dir(d2)).normalized(), rng.uniform(0.2, 0.5), 0.004, 2,
                             crook=0.6, seg=0.25, dead=True)
                continue
            L = Rz * rng.uniform(0.85, 1.05)
            # smrk: spodní větve svěšené se zvednutou špičkou; jedle: vodorovné
            el = (rng.uniform(-0.25, -0.05) if u < 0.6 else rng.uniform(-0.05, 0.25)) if sm else rng.uniform(-0.08, 0.08)
            dd = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
            limb = grow(p, dd, L, max(0.012, r * 0.18 * (1 - u * 0.5)), 1, crook=0.15, droop=SP["droopc"] * 0.2,
                        up=SP["droopc"] * 0.12 if sm else 0.0, seg=0.55)
            # 2. řád ve vodorovné rovině (ploché vějíře)
            n2 = max(1, int(L / 0.3))
            for q in range(n2):
                tq = (q + rng.uniform(0.2, 0.8)) / n2
                p2, d2, r2 = along(limb, tq)
                sd = 1 if q % 2 else -1
                hor = d2.cross(Vector((0, 0, 1))).normalized() * sd
                nd = (d2 * 0.55 + hor * 0.85 + Vector((0, 0, -SP["droopc"] * 0.3))).normalized()
                L2 = max(0.2, L * (1 - tq) * rng.uniform(0.35, 0.6) + 0.2)
                b2 = grow(p2, nd, L2, max(0.005, r2 * 0.5), 2, crook=0.2, droop=SP["droopc"] * 0.5, seg=max(0.3, L2 / 2))
                b2["thin"] = True
        z += dz * rng.uniform(0.85, 1.15)

def build_pollard():
    hh = rng.uniform(1.9, 2.6)
    trunk = grow(Vector((0, 0, -0.2)), Vector((rng.gauss(0, 0.06), rng.gauss(0, 0.06), 1)), hh + 0.2, R0, 0,
                 crook=0.25, seg=0.25, r_end=R0 * 1.35)    # hlava se rozšiřuje
    top = trunk["pts"][-1]
    nrod = by_age(((14, 20), (22, 30), (26, 36)))
    for k in range(rng.randint(*nrod)):
        az = rng.uniform(0, math.tau); el = rng.uniform(0.95, 1.45)
        rr = R0 * 1.2 * rng.uniform(0.5, 1.0)
        p = top + Vector((math.cos(az) * rr, math.sin(az) * rr, rng.uniform(-0.15, 0.1)))
        dd = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
        L = (H - hh) * rng.uniform(0.6, 1.0)
        rod = grow(p, dd, L, rng.uniform(0.015, 0.04), 2, crook=0.1, droop=0.12, seg=0.35)
        twigs_on(rod, 1.5, (0.25, 0.6))

{"broad": build_broad, "cone": build_cone, "pollard": build_pollard}[SP["arch"]]()
if SP["arch"] == "broad":
    space_colonize()

# ------------------------------------------------------------------ síť větví (+ barva vrcholů)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
col_l = bm.loops.layers.color.new("Col")
SIDES = by_age(((8, 5, 3, 3), (10, 6, 4, 3), (12, 7, 4, 3)))
for b in BR:
    pts, rads, level, dead = b["pts"], b["rads"], b["level"], b["dead"]
    if level == 3 and rads[0] < 0.004:
        continue
    if b.get("sc") and max(rads) < by_age((0.012, 0.016, 0.02)):
        continue
    sides = SIDES[min(level, 3)]
    if b.get("thin"):
        sides = 3
        if max(rads) < 0.014: continue
    if SP["arch"] == "cone" and level == 1:
        sides = 4
    rings, vacc, prev_n = [], 0.0, None
    for i, (p, r) in enumerate(zip(pts, rads)):
        tng = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev_n is None:
            prev_n = tng.cross(Vector((0, 0, 1)) if abs(tng.z) < 0.9 else Vector((1, 0, 0))).normalized()
        nrm = (prev_n - tng * prev_n.dot(tng)).normalized(); prev_n = nrm; bn = tng.cross(nrm)
        ring = []
        for k in range(sides):
            a = k / sides * math.tau
            rr = r
            if level == 0 and i <= 2 and SP["arch"] != "pollard":
                rr *= 1 + (0.55 - 0.22 * i) * max(0.0, math.cos(a * 5 + SEED)) ** 3 + (0.12 if i == 0 else 0)
            if level == 0 and SP["arch"] == "pollard" and i >= len(pts) - 3:   # hrbolatá hlava
                rr *= 1 + 0.25 * max(0.0, math.cos(a * 4 + i)) ** 2
            ring.append(bm.verts.new(p + (nrm * math.cos(a) + bn * math.sin(a)) * rr))
        rings.append((ring, vacc, r, p.z))
        if i < len(pts) - 1: vacc += (pts[i + 1] - p).length
    for (ra, va, r_a, za), (rb, vb, _, zb) in zip(rings[:-1], rings[1:]):
        us = max(1, round(2 * math.pi * r_a / 0.6))
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((ra[k], ra[k2], rb[k2], rb[k]))
            for lo, (uu, vv, zz) in zip(f.loops, ((k / sides, va, za), ((k + 1) / sides, va, za),
                                                  ((k + 1) / sides, vb, zb), (k / sides, vb, zb))):
                lo[uvl].uv = (uu * us, vv / 1.2)
                c = 1.0
                if zz < 0.8: c *= 0.62 + 0.38 * max(0.0, zz) / 0.8          # vlhko a hlína u paty
                if SP.get("birch") and zz < 2.0: c *= 0.3 + 0.7 * min(1.0, max(0.0, (zz - 0.2) / 1.8)) ** 1.5
                if SP.get("pinebark"):                                         # dole šedohnědá, nahoře oranžová
                    w = min(1.0, max(0.0, (H * 0.45 - zz) / (H * 0.35)))
                    lo[col_l] = (c * (1 - 0.45 * w), c * (1 - 0.5 * w), c * (1 - 0.42 * w), 1.0)
                    continue
                if dead: lo[col_l] = (c * 0.92, c * 0.9, c * 0.92, 1.0)
                else: lo[col_l] = (c, c, c, 1.0)
me_b = bpy.data.meshes.new("vetve"); bm.to_mesh(me_b); bm.free()
for p in me_b.polygons: p.use_smooth = True
ob_b = bpy.data.objects.new(f"{NAME}_vetve", me_b); bpy.context.collection.objects.link(ob_b)
tris_b = sum(len(p.vertices) - 2 for p in me_b.polygons)

# ------------------------------------------------------------------ listové karty
cards = json.load(open(os.path.join(HERE, "atlas", f"{SP['leaf']}T_cards.json")))["cards"]
cl = [c for c in cards if c["kind"] == "cluster"]
cand = []   # (base, up, size, flat)
conif = SP["arch"] == "cone"
for b in BR:
    if b["dead"] or b["level"] == 0:
        continue
    lv = b["level"]
    if SP["arch"] == "broad" and lv == 1:
        start, step = 0.45, CARD[0] * 0.45
    elif conif:
        start, step = (0.2 if lv == 1 else 0.0), CARD[0] * 0.2
    else:
        start, step = (0.0 if lv == 3 else 0.3), CARD[0] * 0.22
    L = sum((q - p).length for p, q in zip(b["pts"][:-1], b["pts"][1:]))
    acc = 0.0
    for p, q in zip(b["pts"][:-1], b["pts"][1:]):
        seg = (q - p).length; acc += seg
        t = acc / max(L, 1e-3)
        if t < start: continue
        n = seg / step
        while n > 0:
            if rng.random() < min(1.0, n):
                pos = p.lerp(q, rng.random())
                d = (q - p).normalized()
                cand.append((pos, d, lv))
            n -= 1.0
    cand.append((b["pts"][-1], (b["pts"][-1] - b["pts"][-2]).normalized(), lv))

for pos, c, par in SC_NODES:
    if c <= 16:
        cand.append((pos, (pos - par).normalized(), 3))
        if c <= 2 and rng.random() < 0.6:
            cand.append((pos.lerp(par, 0.5), (pos - par).normalized(), 3))

def shell(pos):
    if conif:
        dz_ = by_age(SP["deadfrac"]) * H
        R = by_age(SP["crownR"]) * H * (1 - max(0.0, (pos.z - dz_) / max(1.0, H - dz_))) ** 1.1 + 0.2
        return min(1.0, Vector((pos.x, pos.y)).length / max(0.3, R))
    if SP["arch"] == "pollard":
        return min(1.0, 0.4 + Vector((pos.x, pos.y)).length / 2.5)
    R = env_radius(pos.z)
    return min(1.0, Vector((pos.x, pos.y)).length / max(0.3, R))

max_cards = max(200, int((BUDGET - tris_b) / 6))
if len(cand) > max_cards:
    w = np.array([0.5 + shell(c[0]) for c in cand]); w /= w.sum()
    idx = np.random.choice(len(cand), max_cards, replace=False, p=w)
    cand = [cand[i] for i in sorted(idx)]
elif cand:
    extra = []
    while len(cand) + len(extra) < max_cards * 0.8:
        pos, d, lv = cand[rng.randrange(len(cand))]
        j = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 0.6))) * CARD[0] * (0.25 if conif else 0.3)
        extra.append((pos + j, d, lv))
    cand += extra
verts, faces, uvs, cols = [], [], [], []
ztop = max(b["pts"][-1].z for b in BR)
for pos, d, lv in cand:
    sz = rng.uniform(*CARD) * (0.8 if lv == 3 else 1.0)
    out = Vector((pos.x, pos.y, 0)); out = out.normalized() if out.length > 0.05 else Vector((1, 0, 0))
    if conif:
        up = (d * 0.85 + out * 0.3 + Vector((0, 0, -SP["droopc"] * 0.15))).normalized()
        side = up.cross(Vector((0, 0, 1))).normalized()
        side = Quaternion(up, rng.uniform(-0.7, 0.7)) @ side            # karta leží spíš vodorovně
    else:
        rv = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))) * 0.45
        up = (d * 0.5 + out * 0.8 + Vector((0, 0, 0.35)) + rv).normalized()
        side = up.cross(Vector((0, 0, 1)))
        if side.length < 1e-3: side = Vector((1, 0, 0))
        side = Quaternion(up, rng.uniform(-math.pi, math.pi)) @ side.normalized()
    nrm = side.cross(up).normalized()
    fold = nrm * sz * rng.uniform(0.04, 0.1)
    base = pos - up * sz * 0.12
    w2 = sz * 0.5
    P = [base - side * w2, base + side * w2, base + side * w2 + up * sz, base - side * w2 + up * sz,
         base + up * sz * 0.5 + fold, base + fold * 0.5, base + up * sz + fold * 0.5]
    c = rng.choice(cl)
    i0 = len(verts); verts.extend(P)
    u0, u1, v0, v1 = c["u0"], c["u1"], c["v0"], c["v1"]; um = (u0 + u1) / 2
    uvs.extend([(u0, v0), (u1, v0), (u1, v1), (u0, v1), (um, (v0 + v1) / 2), (um, v0), (um, v1)])
    faces.extend([(i0, i0 + 5, i0 + 4), (i0, i0 + 4, i0 + 3), (i0 + 3, i0 + 4, i0 + 6),
                  (i0 + 5, i0 + 1, i0 + 4), (i0 + 1, i0 + 2, i0 + 4), (i0 + 4, i0 + 2, i0 + 6)])
    # světlo koruny: vnější a horní karty světlejší, nitro tmavší
    s = shell(pos); hz = max(0.0, min(1.0, (pos.z - CZ0) / max(0.5, ztop - CZ0)))
    br = min(1.0, (0.62 if SPECIES == "borovice" else (0.45 if conif else 0.34)) + 0.48 * s ** 1.2 + 0.22 * hz + rng.uniform(-0.06, 0.06))
    tint = (br * rng.uniform(0.95, 1.03), br, br * rng.uniform(0.9, 1.0))
    for _ in P:
        cols.append(tint)

me_l = bpy.data.meshes.new("listi"); me_l.from_pydata([tuple(v) for v in verts], [], faces)
uv2 = me_l.uv_layers.new(name="UVMap")
ca = me_l.color_attributes.new("Col", 'FLOAT_COLOR', 'CORNER')
for poly in me_l.polygons:
    for li in poly.loop_indices:
        vi = me_l.loops[li].vertex_index
        uv2.data[li].uv = uvs[vi]
        ca.data[li].color = (*cols[vi], 1.0)
for p in me_l.polygons: p.use_smooth = True
ob_l = bpy.data.objects.new(f"{NAME}_listi", me_l); bpy.context.collection.objects.link(ob_l)
# větve: barvu vrcholů převést na stejný název
if "Col" not in me_b.color_attributes:
    pass

# ------------------------------------------------------------------ materiály (obrázek × barva vrcholů)
def img(p, color=True):
    im = bpy.data.images.load(p); im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; return im
def make_mat(name, color_path, normal_path, rough, leaf):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.use_backface_culling = not leaf
    t = m.node_tree; b = t.nodes["Principled BSDF"]
    c = t.nodes.new("ShaderNodeTexImage"); c.image = img(color_path)
    n_ = t.nodes.new("ShaderNodeTexImage"); n_.image = img(normal_path, False)
    vc = t.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"
    mx = t.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = 1.0
    t.links.new(c.outputs["Color"], mx.inputs[6]); t.links.new(vc.outputs["Color"], mx.inputs[7])
    t.links.new(mx.outputs[2], b.inputs["Base Color"])
    nm = t.nodes.new("ShaderNodeNormalMap"); t.links.new(n_.outputs[0], nm.inputs["Color"])
    t.links.new(nm.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    if leaf:
        r = t.nodes.new("ShaderNodeMath"); r.operation = 'ROUND'
        t.links.new(c.outputs["Alpha"], r.inputs[0]); t.links.new(r.outputs[0], b.inputs["Alpha"])
    return m
ob_b.data.materials.append(make_mat(f"game_{NAME}_kura", os.path.join(OUT, f"{NAME}_kura_color.png"),
                                    os.path.join(OUT, f"{NAME}_kura_normal.png"), 0.85, False))
ob_l.data.materials.append(make_mat(f"game_{NAME}_listi", os.path.join(HERE, "atlas", f"{SP['leaf']}T_color.png"),
                                    os.path.join(HERE, "atlas", f"{SP['leaf']}T_normal.png"), 0.6, True))
tris_l = len(faces)
bpy.ops.object.select_all(action='DESELECT'); ob_b.select_set(True); ob_l.select_set(True)
bpy.context.view_layer.objects.active = ob_b; bpy.ops.object.join()
tree = bpy.context.active_object; tree.name = NAME
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"{NAME}.glb"), export_format='GLB', use_selection=True,
                          export_yup=True, export_apply=True, export_cameras=False, export_lights=False,
                          export_vertex_color='MATERIAL', export_image_format='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{NAME}.blend"))
d = tree.dimensions
print(f"RESULT {NAME} tris={tris_b + tris_l} (vetve {tris_b}, listi {tris_l}) dims_m(sxvxh)={d.x:.2f} x {d.z:.2f} x {d.y:.2f}")
