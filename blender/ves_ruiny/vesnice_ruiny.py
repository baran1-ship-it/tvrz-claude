# -*- coding: utf-8 -*-
"""
Zaniklá středověká ves – Odkaz Havrana (Čechy 1393)
Opuštěná dávno: dřevo shnilo, střechy jsou pryč, zbyly kamenné podezdívky a zdi zarostlé drnem,
valy ze sesutého kamene a hlíny, rozvaliny pecí, studna, sklep v mezi, suché kamenné zídky a snosy z polí.
Předloha: archeologicky zkoumané zaniklé vsi na Moravě a v Čechách (Pfaffenschlag u Slavonic, Mstěnice, Konůvky,
Bystřec): trojdílný dům (jizba – síň – komora), kamenné základy, komora často celá kamenná, pec v koutě jizby,
domy štítem k protáhlé návsi.
Stromy ani keře v modelu nejsou (dá si je autor sám).
Spuštění:  python vesnice_ruiny.py --kus Dum3      (jeden díl do ves_dum3.glb, počátek uprostřed na terénu)
           python vesnice_ruiny.py --celek          (celá ves do ves_celek.glb)   [--norender]
"""
import math, os, sys, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix

SEED = 1380
OUT = os.path.dirname(os.path.abspath(__file__))
FOTO = os.path.join(OUT, "foto"); TEX = os.path.join(OUT, "textury"); os.makedirs(TEX, exist_ok=True)
PRE = os.path.join(OUT, "nahledy_ves"); os.makedirs(PRE, exist_ok=True)
RENDER = "--norender" not in sys.argv
random.seed(SEED); RNG = np.random.default_rng(SEED)
PFX = "Ves"
exec(open(os.path.join(OUT, "_spolecne.py")).read())
exec(open(os.path.join(OUT, "tesar.py")).read())
exec(open(os.path.join(OUT, "_stavba.py")).read())
exec(open(os.path.join(OUT, "_ruiny.py")).read())
DOORS = []

# ================================================================= MATERIÁLY
for k_ in ("stacked_stone_wall", "grass_ground", "aerial_ground_rock"): HMAP[k_] = _load_h(k_)
M["zdivo_v"]  = vcol_mat("M_ZdivoVes", "broken_wall", "zdv", desat([0.88, 0.86, 0.82], 0.75, 1.05), nstr=1.2, rough_mul=lambda a: 0.75 + 0.25 * a)
M["sucha"]    = vcol_mat("M_ZidkaNasucho", "stacked_stone_wall", "szk2", desat([1.25, 1.22, 1.18], 0.3, 0.9), nstr=1.3, rough_mul=lambda a: 0.8 + 0.2 * a)
M["drn"]      = vcol_mat("M_DrnVal", "grass_ground", "drn2", desat([0.78, 0.92, 0.55], 1.25, 1.1), nstr=1.0, rough_mul=lambda a: 0.9 + 0.1 * a)
M["sutzem"]   = vcol_mat("M_SutZemina", "aerial_ground_rock", "stz2", desat([0.78, 0.74, 0.68], 0.5, 1.15), nstr=1.2, rough_mul=lambda a: 0.85 + 0.15 * a)
M["pec_hl"]   = vcol_mat("M_PecVypalenaHlina", "clay_plaster", "phl3", desat([0.40, 0.34, 0.29], 0.45, 1.15), nstr=1.6, rough_mul=lambda a: 0.85 + 0.15 * a)
M["voda"]     = mat("M_VodaStudna", None, color=(0.012, 0.016, 0.014), rough=0.05)

CL_ZED = {0: dict(h="broken_wall", tile=2.4, S=0.075, mat="zdivo_v"), 3: dict(h="broken_wall", tile=2.2, S=0.07, mat="zdivo_v")}
CL_SUCHA = {0: dict(h="stacked_stone_wall", tile=1.7, S=0.085, mat="sucha"), 3: dict(h="stacked_stone_wall", tile=1.6, S=0.08, mat="sucha")}
M["sut_v"] = vcol_mat("M_SutKameni", "cobblestone_large_01", "sutv", desat([0.80, 0.78, 0.74], 0.55, 1.05), nstr=1.3)
CL_VAL = {0: dict(h="grass_ground", tile=3.0, S=0.035, mat="drn"), 1: dict(h="aerial_ground_rock", tile=2.2, S=0.07, mat="sutzem"),
          2: dict(h="aerial_ground_rock", tile=1.8, S=0.04, mat="pec_hl"), 3: dict(h="cobblestone_large_01", tile=1.4, S=0.13, mat="sut_v")}

def cls_zed(P, Nn): return np.where(Nn[:, 2] > 0.55, 3, 0)
def col_stara(P, Nn, h, c):
    """stará zeď: hodně mechu a lišejníku, nahoře zelená, u země tmavá vlhkost, světlé lišejníkové skvrny"""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    n1 = nzv(x * 0.9 + y * 0.7, z * 1.1, 1, 5, 4); n2 = nzv(x * 3.1 - y * 2.7, z * 3.3, 1, 6, 3); nb = nzv(x * 0.25 + y * 0.25, z * 0.3, 1, 1, 3)
    g = (0.58 + 0.22 * n1) * (0.72 + 0.45 * nb) * (0.5 + 0.5 * h)
    mt = np.clip((Nn[:, 2] - 0.15) / 0.45, 0, 1) * np.clip(0.45 + 1.0 * (n2 - 0.3), 0, 1)
    mg = np.clip(1.0 - z / (0.45 + 0.5 * n1), 0, 1) * (0.55 + 0.45 * n2)
    mm = np.clip(np.maximum(mt, mg) + 0.25 * np.clip((n1 - 0.55) * 3, 0, 1), 0, 1)
    lich = np.clip((n2 - 0.62) * 4, 0, 1) * (1 - mm) * (Nn[:, 2] < 0.5)
    r = g * (1 - 0.50 * mm) + 0.18 * lich; gg = g * (1 - 0.18 * mm) + 0.18 * lich; b = g * (1 - 0.62 * mm) + 0.15 * lich
    return np.stack([r, gg * 0.99, b * 0.96], 1)
def col_val(P, Nn, h, c):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    n1 = nzv(x * 0.35, y * 0.35, 1, 3, 4); n2 = nzv(x * 1.7, y * 1.7, 1, 4, 3)
    g = 0.78 + 0.3 * n1
    dry = np.clip((n2 - 0.45) * 2.5, 0, 1) * (c == 0)                  # vyschlá tráva na hřbetech valů
    dry = np.maximum(dry, np.clip((z - 0.6) * 1.2, 0, 1) * 0.6 * (c == 0))
    r = g * (1 + 0.25 * dry); gg = g * (1 + 0.05 * dry); b = g * (1 - 0.15 * dry)
    rock = (c == 1)
    gs = np.where(rock, (0.55 + 0.45 * h) * (0.8 + 0.25 * n1), 1.0)
    return np.stack([r * gs, gg * gs, b * gs], 1)

# ================================================================= POMŮCKY
_ragged0 = ragged_top
def ragged_top(u0, u1, ztop, step=0.34, q=0.06, jit=0.13, zb=-0.35):
    """starší, ohlazená koruna: méně schodů, víc plynulých šikmin"""
    pts = [(u0, zb), (u1, zb)]; us = [u1]; u = u1
    while u > u0 + step * 0.6:
        u -= step * random.uniform(0.4, 1.6); us.append(max(u0, u))
    if us[-1] > u0: us.append(u0)
    zprev = None; ph = random.uniform(0, 50)
    for i, u in enumerate(us):
        z = ztop(u) + jit * 2.4 * (float(vnoise(np.array(u * 1.1 + ph), np.array(ph), 6)) - 0.5) + random.gauss(0, jit * 0.3)
        z = max(zb + 0.25, round(z / q) * q)
        if zprev is not None and random.random() < 0.25: pts.append((u + random.uniform(-0.03, 0.03) if 0 < i < len(us) - 1 else u, zprev))
        pts.append((u, z)); zprev = z
    pg = Polygon(pts)
    return pg if pg.is_valid else pg.buffer(0)
def door(x, a, b, zlow=0.06, soft=0.12):
    """faktor 0 ve dveřním otvoru (a..b), jinak 1"""
    return 1.0 - sm(a - soft, a + 0.02, x) * (1.0 - sm(b - 0.02, b + soft, x))
class Piece:
    """jeden díl (dům, studna…): sbírá zdi, kolize, valy, kameny"""
    def __init__(s, name, cl=CL_ZED):
        s.name = name; s.walls = []; s.cut = []; s.segs = []; s.cl = cl; s.extra = []
        s.KAM = Mesh("%s_%s_Kameny" % (PFX, name)); s.lod = []
    def wall(s, p0, p1, t, ztop, e0=0.0, e1=0.0, step=0.34, jit=0.13, q=0.06, bank=0.55, bankw=1.2, col=True):
        o, fr = wall("w", p0, p1, t, ztop, e0=e0, e1=e1, step=step, jit=jit, q=q)
        s.walls.append(o); s.segs.append((fr, t, ztop, bank, bankw))
        if col:
            us = np.linspace(0, fr.L, max(3, int(fr.L / 0.5)))
            zs = np.array([ztop(u) for u in us])
            # kolize po úsecích (dveře zůstanou průchozí)
            k0 = 0
            for k in range(1, len(us) + 1):
                if k == len(us) or (zs[k] > 0.3) != (zs[k0] > 0.3):
                    if zs[k0] > 0.3 and us[min(k, len(us) - 1)] - us[k0] > 0.2:
                        zm = float(np.mean(zs[k0:k])); u0 = us[k0]; u1 = us[min(k, len(us) - 1)]
                        c = fr.P((u0 + u1) / 2, zm / 2 - 0.15, 0); L = u1 - u0
                        colbox("%s_%d" % (s.name, len(KOL)), c - Vector((L / 2, t / 2, zm / 2 + 0.15)), c + Vector((L / 2, t / 2, zm / 2 + 0.15)), rot=(0, 0, math.atan2(fr.U.y, fr.U.x)))
                        s.lod.append((c, L, t, zm, math.atan2(fr.U.y, fr.U.x)))
                    k0 = k
        return fr
    def build_walls(s, ratio=0.11, voxel=0.05, cls=cls_zed, col=col_stara):
        o = cut_join(s.walls, s.cut)
        return zdivo(o, "%s_%s_Zdivo" % (PFX, s.name), cls, s.cl, col, ratio, voxel=voxel, drop_fn=lambda c, n: n.z < -0.9 and c.z < -0.25)
    def bank_h(s, X, Y, fills=(), blobs=()):
        """výška valů nad terénem: podél zdí (sesuté kamení + hlína), výplň místností, kupy"""
        H = np.zeros_like(X)
        for (fr, t, ztop, bank, bankw) in s.segs:
            dx = X - fr.O.x; dy = Y - fr.O.y
            u = dx * fr.U.x + dy * fr.U.y; d = np.abs(dx * fr.N.x + dy * fr.N.y)
            uc = np.clip(u, 0, fr.L)
            zt = np.interp(uc, np.linspace(0, fr.L, 40), [ztop(v) for v in np.linspace(0, fr.L, 40)])
            ext = np.maximum(0, np.abs(u - uc))                    # za koncem zdi zaoblit
            dd = np.sqrt(np.maximum(0, d - t / 2) ** 2 + ext ** 2)
            wb = bankw * (0.75 + 0.5 * nzv(X * 0.6 + 7, Y * 0.6, 1, 4, 2))
            hb = (bank * 0.75 * zt + 0.10) * np.clip(1 - (dd / wb) ** 2, 0, 1) ** 1.5
            H = np.maximum(H, hb)
        for (poly, z0, amp) in fills:
            inside = shapely.contains_xy(poly, X, Y)
            H = np.where(inside, np.maximum(H, z0 + amp * nzv(X * 0.9, Y * 0.9, 1, 9, 3)), H)
        for (cx, cy, rx, ry, hh) in blobs:
            r = np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2) * (0.85 + 0.3 * nzv(X * 1.4 + cx, Y * 1.4 + cy, 1, 5, 3))
            H = np.maximum(H, hh * np.clip(1 - r * r, 0, 1) ** 1.4)
        H *= 0.85 + 0.3 * nzv(X * 1.1, Y * 1.1, 1, 11, 3)
        return H - 0.05
    def build_banks(s, x0, x1, y0, y1, fills=(), blobs=(), cls_extra=None, res=0.09, ratio=0.12, hfun=None, excl=None):
        hf = hfun or (lambda X, Y: s.bank_h(X, Y, fills, blobs))
        nx = int((x1 - x0) / VX(res)); ny = int((y1 - y0) / VX(res))
        xs = np.linspace(x0, x1, nx + 1); ys = np.linspace(y0, y1, ny + 1)
        X, Y = np.meshgrid(xs, ys); Z = hf(X, Y)
        V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
        Zg = Z
        keep = (np.maximum.reduce([Zg[:-1, :-1], Zg[1:, :-1], Zg[:-1, 1:], Zg[1:, 1:]]) > -0.035)
        if excl is not None:
            keep &= ~excl((X[:-1, :-1] + X[1:, 1:]) / 2, (Y[:-1, :-1] + Y[1:, 1:]) / 2)
        jj, ii = np.nonzero(keep)
        a = jj * (nx + 1) + ii
        Fc = np.stack([a, a + 1, a + nx + 2, a + nx + 1], 1)
        me = bpy.data.meshes.new("val"); me.from_pydata(V.tolist(), [], Fc.tolist())
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new("val", me); scene.collection.objects.link(o)
        def cls(P, Nn):
            n_ = nzv(P[:, 0] * 0.9, P[:, 1] * 0.9, 1, 8, 3)
            c = np.where((Nn[:, 2] < 0.55) & (n_ > 0.50), 1, 0)                                         # strmé = sesuté kamení
            c = np.where((P[:, 2] > 0.35) & (P[:, 2] < 1.6) & (n_ > 0.66), 1, c)                        # kamenité hřbety
            if cls_extra is not None: c = cls_extra(P, c)
            return c
        val = zdivo(o, "%s_%s_Valy" % (PFX, s.name), cls, CL_VAL, col_val, ratio, remesh=False)
        # hrubá kolizní síť valů
        cx_ = np.linspace(x0, x1, int((x1 - x0) / 0.5) + 1); cy_ = np.linspace(y0, y1, int((y1 - y0) / 0.5) + 1)
        CX, CY = np.meshgrid(cx_, cy_); CZ = hf(CX, CY) - 0.04
        n2x = len(cx_); Vc = np.stack([CX.ravel(), CY.ravel(), CZ.ravel()], 1).tolist()
        Fcc = []
        for j in range(len(cy_) - 1):
            for i in range(n2x - 1):
                if max(CZ[j, i], CZ[j + 1, i], CZ[j, i + 1], CZ[j + 1, i + 1]) > 0.08:
                    a_ = j * n2x + i; Fcc.append((a_, a_ + 1, a_ + n2x + 1, a_ + n2x))
        if Fcc:
            mc = bpy.data.meshes.new("kv"); mc.from_pydata(Vc, [], Fcc)
            bm = bmesh.new(); bm.from_mesh(mc); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(mc); bm.free()
            oc = bpy.data.objects.new("%s_Kol_%s_Valy-colonly" % (PFX, s.name), mc); scene.collection.objects.link(oc); oc.hide_render = True; KOL.append(oc)
        s.hf = hf
        return val
    def stones(s, x0, x1, y0, y1, n, smin=0.10, smax=0.32, zmin=0.12, keys=("kamen_r", "kamen_r", "kamen_rm")):
        placed = 0; tries = 0
        while placed < n and tries < n * 30:
            tries += 1
            x = random.uniform(x0, x1); y = random.uniform(y0, y1)
            z = float(s.hf(np.array([[x]]), np.array([[y]]))[0, 0])
            if z < zmin: continue
            if any(abs((Vector((x, y, 0)) - fr.O).dot(fr.N)) < t / 2 + 0.05 and -0.1 < (Vector((x, y, 0)) - fr.O).dot(fr.U) < fr.L + 0.1 for (fr, t, *_r) in s.segs): continue
            sz = random.uniform(smin, smax); a_ = random.uniform(0, 6.283)
            U_ = Vector((math.cos(a_), math.sin(a_), random.uniform(-0.25, 0.25))).normalized(); N_ = Vector((0, 0, 1)); V_ = N_.cross(U_).normalized(); N_ = U_.cross(V_).normalized()
            stone(s.KAM, (x, y, z - sz * 0.25), U_, V_, N_, sz * random.uniform(1.0, 1.6), sz, sz * 0.75, random.choice(keys), detail=True, bulge=0.02, tilt=0.4)
            placed += 1

def quern(Ms, c, yaw, broken=True):
    """rozlomený žernov (ruční mlýnek)"""
    R = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(random.uniform(-0.15, 0.15), 3, 'X')
    pg = Point(0, 0).buffer(0.25, 24).difference(Point(0, 0).buffer(0.045, 12))
    if broken: pg = pg.intersection(sbox(-0.3, -0.3, 0.3, 0.035))
    chamfer_extrude(pg, lambda u, v, d: Vector(c) + R @ Vector((u, v, d)), 0.0, 0.085, ch=0.015, Ms=Ms, key="kamen_r")

# ================================================================= DÍLY
def build_dum3():
    """velký trojdílný dům: jizba (podezdívka roubení), síň, kamenná komora (výš dochovaná, střílna)"""
    P_ = Piece("Dum3"); t = 0.75; L = 18.5; W = 7.1
    xa = -L / 2; X1 = xa + t + 6.5; X2 = X1 + t + 3.6                # vnitřní líce příček
    yf = -W / 2 + t / 2; yb = W / 2 - t / 2
    def zt_long(front):
        def f(u):
            x = xa + u
            low = 0.42 + 0.28 * math.sin(x * 0.9 + (0 if front else 2)) + 0.15 * math.sin(x * 2.3)
            hi = (1.95 if front else 2.55) + 0.35 * math.sin(x * 1.3) + (0.6 * sm(6.5, 8.6, x) if not front else 0.0)
            z = low + (hi - low) * sm(X2 - 0.6, X2 + 0.6, x)
            if front: z = z * door(x, -0.6, 0.55) + 0.06
            else: z = z * door(x, -0.4, 0.55) + 0.06
            return z
        return f
    P_.wall((xa, yf), (-xa, yf), t, zt_long(True))
    P_.wall((xa, yb), (-xa, yb), t, zt_long(False))
    P_.wall((xa + t / 2, -W / 2), (xa + t / 2, W / 2), t, lambda u: 0.55 + 0.3 * math.sin(u * 1.4) + 0.2 * math.sin(u * 3.1), jit=0.12)
    frG = P_.wall((-xa - t / 2, -W / 2), (-xa - t / 2, W / 2), t, lambda u: 2.45 + 0.35 * math.sin(u * 1.1) + 0.5 * sm(4.0, 6.0, u) - 0.9 * (1 - sm(0.0, 1.8, u)))
    P_.wall((X1 - t / 2, -W / 2), (X1 - t / 2, W / 2), t, lambda u: (0.38 + 0.12 * math.sin(u * 3)) * door(-W / 2 + u, -2.6, -1.55) + 0.05)
    P_.wall((X2 - t / 2, -W / 2), (X2 - t / 2, W / 2), t, lambda u: (1.55 + 0.4 * math.sin(u * 1.2)) * door(-W / 2 + u, 0.55, 1.6) + 0.06)
    c_, _ = window_cutters(frG, W / 2, t, 0.07, 1.25, 1.75, frame=0.0, splay_o=0.02, splay_i=0.30, sill_i=0.30, zspr_i=0.15, depth_g=0.15, r_k=1.0)
    P_.cut += c_
    c_, _ = window_cutters(P_.segs[1][0], 15.6, t, 0.08, 1.35, 1.8, frame=0.0, splay_o=0.02, splay_i=0.3, sill_i=0.3, zspr_i=0.15, depth_g=0.15, r_k=1.0)
    P_.cut += c_
    # pec v koutě jizby u příčky (kamenná plotna), zbytek klenby jen sutí vypálené hlíny
    P_.walls.append(solid_box((X1 - t - 1.95, 0.75, -0.3), (X1 - t + 0.02, W / 2 - t + 0.02, 0.55)))
    P_.walls.append(solid_box((xa + t, -W / 2 + t, -0.3), (xa + t + 0.5, -W / 2 + t + 2.6, 0.32)))     # lavice-podezdívka u štítu
    zed = P_.build_walls()
    jiz = sbox(xa + t, -W / 2 + t, X1 - t, W / 2 - t); kom = sbox(X2, -W / 2 + t, -xa - t, W / 2 - t); sin_ = sbox(X1, -W / 2 + t, X2 - t, W / 2 - t)
    OVEN = (X1 - t - 0.95, W / 2 - t - 0.95)
    def ext(P, c):
        d = np.hypot(P[:, 0] - OVEN[0], P[:, 1] - OVEN[1])
        return np.where((d < 1.15) & (P[:, 2] > 0.35), 2, c)
    P_.build_banks(xa - 2.6, -xa + 2.6, -W / 2 - 2.6, W / 2 + 2.6,
                   fills=[(jiz, 0.10, 0.22), (sin_, 0.06, 0.12), (kom, 0.22, 0.30)],
                   blobs=[(OVEN[0], OVEN[1], 1.25, 1.1, 1.05), (6.0, 0.6, 2.4, 1.7, 1.05), (-6.5, -4.6, 1.6, 0.9, 0.55), (8.4, 4.7, 1.8, 1.0, 0.8)],
                   cls_extra=ext)
    P_.stones(xa - 2, -xa + 2, -W / 2 - 2, W / 2 + 2, 170)
    for k in range(9):
        a_ = random.uniform(0, 6.28); r_ = random.uniform(0.2, 1.0)
        x = OVEN[0] + r_ * math.cos(a_); y = OVEN[1] + r_ * math.sin(a_); z = float(P_.hf(np.array([[x]]), np.array([[y]]))[0, 0])
        stone(P_.KAM, (x, y, z - 0.04), (math.cos(a_), math.sin(a_), 0), (-math.sin(a_), math.cos(a_), 0), (0, 0, 1), 0.2, 0.14, 0.1, "kamen_p", detail=True, bulge=0.02, tilt=0.3)
    quern(P_.KAM, (-6.2, -1.6, float(P_.hf(np.array([[-6.2]]), np.array([[-1.6]]))[0, 0]) - 0.02), 0.7)
    P_.KAM.build(smooth_angle=40)
    empty("%s_Dum3_Vstup" % PFX, (0.0, -W / 2 - 1.0, 0.0)); empty("%s_Dum3_Pec" % PFX, (OVEN[0], OVEN[1], 1.0))
    empty("%s_Dum3_Skrys_Komora" % PFX, (6.8, 2.2, 0.5))
    return P_

def build_dum2():
    """menší dvojdílný dům (jizba + síň), skoro celý zarostlý, jen nízké podezdívky"""
    P_ = Piece("Dum2"); t = 0.7; L = 11.6; W = 6.6
    xa = -L / 2; X1 = xa + t + 6.2
    yf = -W / 2 + t / 2; yb = W / 2 - t / 2
    P_.wall((xa, yf), (-xa, yf), t, lambda u: (0.42 + 0.25 * math.sin(u * 1.1) + 0.12 * math.sin(u * 3.3)) * door(xa + u, 2.2, 3.25) + 0.05, jit=0.12, bank=0.75)
    P_.wall((xa, yb), (-xa, yb), t, lambda u: 0.62 + 0.3 * math.sin(u * 0.8 + 1) - 0.35 * sm(5.0, 7.0, u) * (1 - sm(8.0, 9.5, u)), jit=0.12, bank=0.75)
    P_.wall((xa + t / 2, -W / 2), (xa + t / 2, W / 2), t, lambda u: 0.85 + 0.35 * math.sin(u * 1.3), jit=0.12, bank=0.7)
    P_.wall((-xa - t / 2, -W / 2), (-xa - t / 2, W / 2), t, lambda u: 0.35 + 0.2 * math.sin(u * 2.0), jit=0.10, bank=0.8)
    P_.wall((X1 - t / 2, -W / 2), (X1 - t / 2, W / 2), t, lambda u: (0.3 + 0.1 * math.sin(u * 3)) * door(-W / 2 + u, -2.1, -1.1) + 0.04, bank=0.8)
    P_.walls.append(solid_box((X1 - t - 1.8, 0.65, -0.3), (X1 - t + 0.02, W / 2 - t + 0.02, 0.45)))
    P_.build_walls(ratio=0.12)
    jiz = sbox(xa + t, -W / 2 + t, X1 - t, W / 2 - t)
    OVEN = (X1 - t - 0.9, W / 2 - t - 0.9)
    def ext(P, c):
        d = np.hypot(P[:, 0] - OVEN[0], P[:, 1] - OVEN[1]); return np.where((d < 1.05) & (P[:, 2] > 0.3), 2, c)
    P_.build_banks(xa - 2.4, -xa + 2.4, -W / 2 - 2.4, W / 2 + 2.4, fills=[(jiz, 0.14, 0.25)],
                   blobs=[(OVEN[0], OVEN[1], 1.15, 1.05, 0.9), (-4.0, 4.3, 2.2, 1.0, 0.7)], cls_extra=ext)
    P_.stones(xa - 2, -xa + 2, -W / 2 - 2, W / 2 + 2, 100)
    P_.KAM.build(smooth_angle=40)
    empty("%s_Dum2_Vstup" % PFX, (xa + 2.7, -W / 2 - 1.0, 0.0))
    return P_

def build_usedlost():
    """usedlost do L: dům + chlév se stájí kolem dvora, dvorní zeď s branou (kamenné patky vrat)"""
    P_ = Piece("Usedlost"); t = 0.7
    # dům podél x (štít k návsi na -x), chlév podél y vpravo, dvůr mezi
    hx0, hx1, hy0, hy1 = -9.5, 4.5, 2.0, 8.4
    P_.wall((hx0, hy0 + t / 2), (hx1, hy0 + t / 2), t, lambda u: (0.55 + 0.3 * math.sin(u * 0.9)) * door(hx0 + u, -3.4, -2.3) + 0.05)
    P_.wall((hx0, hy1 - t / 2), (hx1, hy1 - t / 2), t, lambda u: 0.7 + 0.35 * math.sin(u * 0.7 + 0.5) + 0.9 * sm(1.5, 3.5, hx0 + u))
    P_.wall((hx0 + t / 2, hy0), (hx0 + t / 2, hy1), t, lambda u: 0.95 + 0.4 * math.sin(u * 1.2) + 0.5 * sm(2.0, 4.5, u))
    P_.wall((hx1 - t / 2, hy0), (hx1 - t / 2, hy1), t, lambda u: 1.7 + 0.3 * math.sin(u * 1.5))
    P_.wall((-3.9, hy0), (-3.9, hy1), t, lambda u: (0.32 + 0.1 * math.sin(u * 3)) * door(hy0 + u, 2.9, 3.9) + 0.04)
    P_.wall((0.3, hy0), (0.3, hy1), t, lambda u: (1.1 + 0.3 * math.sin(u * 2)) * door(hy0 + u, 6.4, 7.4) + 0.05)
    # chlév (stáj) podél y
    cx0, cx1, cy0, cy1 = 4.5, 10.5, -9.0, 8.4
    P_.wall((cx1 - t / 2, cy0), (cx1 - t / 2, cy1), t, lambda u: 0.75 + 0.35 * math.sin(u * 0.6) + 0.25 * math.sin(u * 2.1))
    P_.wall((cx0 + t / 2, cy0), (cx0 + t / 2, hy0 + 0.3), t, lambda u: (0.55 + 0.3 * math.sin(u * 0.9 + 1)) * door(cy0 + u, -4.6, -2.8) * door(cy0 + u, -0.2, 1.0) + 0.05)
    P_.wall((cx0, cy0 + t / 2), (cx1, cy0 + t / 2), t, lambda u: 0.45 + 0.25 * math.sin(u * 1.3))
    P_.wall((cx0, -2.0), (cx1, -2.0), 0.6, lambda u: 0.3 + 0.1 * math.sin(u * 2.5), bank=0.9)
    # dvorní zeď s branou k návsi (-x) a vraty: kamenné patky
    P_.wall((hx0 + 0.3, -9.0 + 0.3), (cx0, -9.0 + 0.3), 0.6, lambda u: (0.7 + 0.3 * math.sin(u * 0.8)) * 1.0, bank=0.8, bankw=1.0)
    P_.wall((hx0 + 0.3, -9.0), (hx0 + 0.3, hy0), 0.6, lambda u: (0.75 + 0.3 * math.sin(u * 1.1)) * door(-9.0 + u, -5.1, -1.9, soft=0.05) + 0.04, bank=0.8, bankw=1.0)
    for yy in (-5.25, -1.75):
        P_.walls.append(solid_box((hx0 + 0.3 - 0.42, yy - 0.42, -0.3), (hx0 + 0.3 + 0.42, yy + 0.42, 1.35 + random.uniform(-0.2, 0.25))))
    P_.walls.append(solid_box((-3.9 - 2.0, 6.2, -0.3), (-3.9 - t / 2 + 0.02, hy1 - t + 0.02, 0.5)))      # pec
    P_.build_walls(ratio=0.10)
    OVEN = (-3.9 - 1.25, 7.0)
    def ext(P, c):
        d = np.hypot(P[:, 0] - OVEN[0], P[:, 1] - OVEN[1]); return np.where((d < 1.05) & (P[:, 2] > 0.3), 2, c)
    P_.build_banks(hx0 - 2.6, cx1 + 2.4, cy0 - 2.4, hy1 + 2.4,
                   fills=[(sbox(hx0 + t, hy0 + t, -3.9 - t / 2, hy1 - t), 0.12, 0.25), (sbox(0.3 + t / 2, hy0 + t, hx1 - t, hy1 - t), 0.25, 0.35),
                          (sbox(cx0 + t, cy0 + t, cx1 - t, -2.3), 0.10, 0.18)],
                   blobs=[(OVEN[0], OVEN[1], 1.15, 1.0, 0.95), (2.4, 5.2, 1.8, 1.6, 1.0), (8.0, 5.0, 1.4, 2.4, 0.75), ],
                   cls_extra=ext)
    P_.stones(hx0 - 2, cx1 + 2, cy0 - 2, hy1 + 2, 200)
    # kamenné koryto ve stáji (napajedlo), rozlomené
    R = Matrix.Rotation(1.57 + 0.08, 3, 'Z') @ Matrix.Rotation(0.05, 3, 'X')
    c0 = Vector((9.4, -6.0, 0.18))
    pg = sbox(-0.9, -0.32, 0.9, 0.32).difference(sbox(-0.75, -0.2, 0.75, 0.2)) if False else None
    chamfer_extrude(sbox(-0.95, -0.34, 0.95, 0.34), lambda u, v, d: c0 + R @ Vector((u, v, d)), -0.22, 0.0, ch=0.03, Ms=P_.KAM, key="kamen_rm")
    chamfer_extrude(sbox(-0.95, -0.34, 0.95, 0.34).difference(sbox(-0.78, -0.2, 0.78, 0.2)).difference(sbox(0.2, -0.5, 0.36, 0.5)),
                    lambda u, v, d: c0 + R @ Vector((u, v, d)), 0.0, 0.22, ch=0.025, Ms=P_.KAM, key="kamen_rm")
    P_.KAM.build(smooth_angle=40)
    empty("%s_Usedlost_Brana" % PFX, (hx0 - 1.2, -3.5, 0.0)); empty("%s_Usedlost_Dvur" % PFX, (-1.5, -4.0, 0.0))
    return P_

def build_stodola():
    """stodola: jen nízké kamenné prahy roubení pod drnem, průjezd na obou dlouhých stranách"""
    P_ = Piece("Stodola"); t = 0.6; L = 15.0; W = 9.0
    for (yy, d0, d1) in ((-W / 2 + t / 2, -1.9, 1.7), (W / 2 - t / 2, -1.8, 1.8)):
        P_.wall((-L / 2, yy), (L / 2, yy), t, lambda u, d0=d0, d1=d1: (0.28 + 0.12 * math.sin(u * 1.7)) * door(-L / 2 + u, d0, d1) + 0.03, jit=0.06, q=0.08, bank=1.0, bankw=0.9)
    for xx in (-L / 2 + t / 2, L / 2 - t / 2):
        P_.wall((xx, -W / 2), (xx, W / 2), t, lambda u: 0.32 + 0.14 * math.sin(u * 2.2), jit=0.06, q=0.08, bank=1.0, bankw=0.9)
    P_.build_walls(ratio=0.13)
    P_.build_banks(-L / 2 - 2.0, L / 2 + 2.0, -W / 2 - 2.0, W / 2 + 2.0, fills=[(sbox(-L / 2 + t, -W / 2 + t, L / 2 - t, W / 2 - t), 0.0, 0.06)],
                   blobs=[(5.5, 2.5, 1.6, 1.2, 0.35)], res=0.11)
    P_.stones(-L / 2 - 1.5, L / 2 + 1.5, -W / 2 - 1.5, W / 2 + 1.5, 35, smax=0.25, zmin=0.08)
    P_.KAM.build(smooth_angle=40)
    return P_

def build_studna():
    """roubená studna s kamennou obrubou: obruba pobořená, šachta vyzděná, na dně tmavá voda (−3,2 m)"""
    P_ = Piece("Studna"); R0 = 0.78; t = 0.42; n = 14
    pts = [(R0 * math.cos(2 * math.pi * k / n), R0 * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
    for k in range(n):
        a_ = 2 * math.pi * (k + 0.5) / n
        base = 0.72 + 0.12 * math.sin(a_ * 2) - 0.5 * max(0.0, math.cos(a_ - 4.0)) ** 3
        P_.wall(pts[k], pts[k + 1], t, lambda u, b=base: b, e0=0.1, e1=0.1, step=0.18, jit=0.07, q=0.09, col=False, bank=0.45, bankw=0.8)
    shaft = extrude2d("sh", Point(0, 0).buffer(R0 + t / 2, 24).difference(Point(0, 0).buffer(R0 - t / 2, 24)), lambda u, v, d: Vector((u, v, d)), -3.6, 0.0)
    P_.walls.append(shaft)
    P_.build_walls(ratio=0.12, voxel=0.045)
    colbox("Studna_%d" % len(KOL), (-R0 - t / 2, -R0 - t / 2, -0.3), (R0 + t / 2, R0 + t / 2, 0.75))
    P_.lod.append((Vector((0, 0, 0.3)), 2 * R0 + t, 2 * R0 + t, 0.7, 0.0))
    def hf(X, Y):
        r = np.hypot(X, Y)
        H = np.where(r > R0 + t / 2 - 0.05, 0.42 * np.clip(1 - ((r - R0 - t / 2) / (1.3 + 0.5 * nzv(X, Y, 1, 3, 2))) ** 2, 0, 1) ** 1.3, -0.2)
        H = np.maximum(H, 0.55 * np.clip(1 - (np.hypot(X - 1.6, Y + 0.9) / 1.0) ** 2, 0, 1))      # sesutá část obruby
        return H - 0.05
    P_.build_banks(-3.2, 3.2, -3.2, 3.2, hfun=hf, res=0.06)
    P_.stones(-2.6, 2.6, -2.6, 2.6, 26, smax=0.28, zmin=0.05)
    F(P_.KAM, [Vector((math.cos(a) * (R0 - t / 2 + 0.02), math.sin(a) * (R0 - t / 2 + 0.02), -3.2)) for a in np.linspace(0, 2 * math.pi, 17)[:-1]],
      [(0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)[:-1]], "voda", (0, 0, 1))
    P_.KAM.build(smooth_angle=40)
    empty("%s_Studna_Dno" % PFX, (0, 0, -3.2))
    return P_

def build_sklep():
    """sklep zapuštěný do meze: kamenné čelo s půlkruhovým vchodem, valená klenba 4 m do kopce, zadní část zasypaná"""
    P_ = Piece("Sklep"); RW = 1.2; D = 4.6; T_ = 0.5
    # čelní opěrná zeď s otvorem a křídla
    fr = P_.wall((-3.4, -0.25), (3.4, -0.25), 0.7, lambda u: 2.75 + 0.25 * math.sin(u * 1.4) - 0.8 * sm(5.4, 6.8, u) - 0.6 * (1 - sm(0.0, 1.2, u)), col=False, bank=0.15, bankw=0.6)
    P_.wall((-3.4, -0.25), (-4.6, -2.2), 0.6, lambda u: 1.6 - 0.6 * u, col=False, bank=0.3)
    P_.wall((3.4, -0.25), (4.4, -2.0), 0.6, lambda u: 1.4 - 0.55 * u, col=False, bank=0.3)
    vault = solid_box((-RW - T_, -0.3, -0.3), (RW + T_, D + T_, RW + 1.3 + T_))
    P_.walls.append(vault)
    hole = arch_poly(RW, -0.1, 1.3, r_k=1.0, n=14)
    P_.cut.append(extrude2d("vh", hole, lambda u, z, d: Vector((u, d, z)), -1.2, D))
    P_.build_walls(ratio=0.12, voxel=0.045)
    for (nm, lo, hi) in (("SklepCeloL", (-3.6, -0.6, 0), (-RW, 0.1, 2.7)), ("SklepCeloP", (RW, -0.6, 0), (3.6, 0.1, 2.7)), ("SklepNadVchodem", (-RW, -0.6, 2.5), (RW, 0.1, 2.9)),
                         ("SklepStenaL", (-RW - T_, 0, 0), (-RW, D, 2.5)), ("SklepStenaP", (RW, 0, 0), (RW + T_, D, 2.5)), ("SklepStrop", (-RW - T_, 0, 2.5), (RW + T_, D, 3.2)),
                         ("SklepZadni", (-RW, D - 0.1, 0), (RW, D + T_, 2.6))):
        colbox(nm, lo, hi)
    P_.lod.append((Vector((0, 2.5, 1.5)), 9.0, 7.0, 3.0, 0.0))
    def hf(X, Y):
        r = np.sqrt((X / 6.6) ** 2 + ((Y - 2.8) / 5.0) ** 2) * (0.92 + 0.16 * nzv(X * 0.8, Y * 0.8, 1, 4, 3))
        H = 3.8 * np.clip(1 - r ** 2, 0, 1) ** 0.7
        front = np.clip((Y + 0.1) / 0.6, 0, 1)
        H = H * np.where(np.abs(X) < 3.4, front, np.clip((Y + 2.2 + 0.45 * (np.abs(X) - 3.4)) / 1.5, 0, 1))
        inside = (np.abs(X) < RW + T_ + 0.15) & (Y > -0.1) & (Y < D + T_ + 0.15)
        H = np.where(inside, np.maximum(H, RW + 1.3 + T_ + 0.15), H)      # hlína přes klenbu
        return H - 0.05
    P_.build_banks(-7.6, 7.6, -3.6, 8.6, hfun=hf, res=0.09, excl=lambda X, Y: (np.abs(X) < RW + T_ + 0.2) & (Y < 0.25) & (Y > -1.2))
    # sesutá zadní část klenby: hromada uvnitř
    for k in range(32):
        x = random.uniform(-RW + 0.15, RW - 0.15); y = random.uniform(D - 1.8, D - 0.1); z = (y - (D - 1.8)) * 0.5 * random.uniform(0.6, 1.1)
        s_ = random.uniform(0.14, 0.3); a_ = random.uniform(0, 6.28)
        stone(P_.KAM, (x, y, z), (math.cos(a_), math.sin(a_), 0.1), (-math.sin(a_), math.cos(a_), 0), (0, 0, 1), s_ * 1.3, s_, s_ * 0.8, random.choice(("kamen_r", "kamen_s")), detail=True, bulge=0.02, tilt=0.5)
    P_.stones(-5.0, 5.0, -3.0, 6.0, 30, zmin=0.3)
    flo = Polygon([(-RW, -0.2), (RW, -0.2), (RW, D), (-RW, D)])
    for tr in _tri_rings(flo):
        F(P_.KAM, [Vector((x, y, 0.01)) for (x, y) in tr], [(x / 1.5, y / 1.5) for (x, y) in tr], "hlina_c", (0, 0, 1))
    P_.KAM.build(smooth_angle=40)
    empty("%s_Sklep_Vstup" % PFX, (0, -1.6, 0)); empty("%s_Sklep_Poklad" % PFX, (0.5, D - 2.2, 0.05))
    return P_

def build_zidka(kind):
    """suchá kamenná zídka (mez): 'rovna' 8 m s pobořeným úsekem, 'roh' 5 + 5 m"""
    P_ = Piece("Zidka_%s" % kind, cl=CL_SUCHA)
    if kind == "rovna":
        P_.wall((-4.0, 0.0), (4.0, 0.0), 0.75, lambda u: (0.95 + 0.12 * math.sin(u * 1.7) - 0.6 * sm(4.4, 5.2, u) * (1 - sm(6.0, 6.8, u))) * (0.45 + 0.55 * sm(0.0, 0.9, u) * (1 - sm(7.1, 8.0, u))), step=0.2, jit=0.07, q=0.08, bank=0.5, bankw=1.0)
        blobs = [(1.8, 0.9, 1.2, 0.9, 0.45), (1.6, -0.9, 1.0, 0.8, 0.35)]; box_ = (-5.5, 5.5, -2.3, 2.3)
    else:
        P_.wall((-5.0, 0.0), (0.35, 0.0), 0.75, lambda u: 0.85 + 0.12 * math.sin(u * 1.9), step=0.2, jit=0.07, q=0.08, bank=0.5, bankw=1.0)
        P_.wall((0.0, -0.35), (0.0, 5.0), 0.75, lambda u: 0.9 - 0.45 * sm(2.5, 4.8, u), step=0.2, jit=0.07, q=0.08, bank=0.5, bankw=1.0)
        blobs = [(0.4, 4.4, 1.0, 1.3, 0.4)]; box_ = (-6.5, 2.2, -2.2, 6.5)
    P_.build_walls(ratio=0.14, voxel=0.05)
    P_.build_banks(*box_, blobs=blobs, res=0.09)
    P_.stones(*box_, 22, keys=("kamen_r", "kamen_rm", "kamen_rm"))
    P_.KAM.build(smooth_angle=40)
    return P_

def build_snos():
    """snos: kupa kamení vybraného z polí, zarostlá"""
    P_ = Piece("Snos")
    def hf(X, Y):
        r = np.sqrt((X / 2.6) ** 2 + (Y / 1.8) ** 2) * (0.85 + 0.3 * nzv(X * 1.2, Y * 1.2, 1, 4, 3))
        return 0.9 * np.clip(1 - r * r, 0, 1) ** 1.2 - 0.05
    P_.build_banks(-3.4, 3.4, -2.6, 2.6, hfun=hf, res=0.07, cls_extra=lambda P, c: np.where(P[:, 2] > 0.12, 3, c))
    P_.stones(-2.6, 2.6, -1.9, 1.9, 150, smin=0.14, smax=0.40, zmin=0.06, keys=("kamen_r", "kamen_rm", "kamen_s"))
    P_.KAM.build(smooth_angle=40)
    colbox("Snos_%d" % len(KOL), (-2.0, -1.3, 0), (2.0, 1.3, 0.55)); P_.lod.append((Vector((0, 0, 0.3)), 4.0, 2.6, 0.6, 0.0))
    return P_

BUILDERS = {"Dum3": build_dum3, "Dum2": build_dum2, "Usedlost": build_usedlost, "Stodola": build_stodola, "Studna": build_studna,
            "Sklep": build_sklep, "Zidka_rovna": lambda: build_zidka("rovna"), "Zidka_roh": lambda: build_zidka("roh"), "Snos": build_snos}

def lod_for(P_, LO):
    for (c, L, t, zm, ang) in P_.lod:
        box(LO, (c.x, c.y, zm / 2), (L, t, zm), Matrix.Rotation(ang, 3, 'Z'), "kamen_rm", uvs=2.0)

def place(tag, name, x, y, rot, LO):
    before = set(scene.objects)
    k0 = len(KOL)
    P_ = BUILDERS[name]()
    lod_for(P_, LO)
    T = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rot, 4, 'Z')
    for o in set(scene.objects) - before:
        o.matrix_world = T @ o.matrix_world
        base = o.name.split(".")[0]
        suf = ""
        for s_ in ("-convcolonly", "-colonly"):
            if base.endswith(s_): base = base[:-len(s_)]; suf = s_
        o.name = base.replace(PFX + "_", "%s_%s_" % (PFX, tag), 1) + suf
    # LOD boxy transformovat: řeší se přes LOD mesh ve světových souřadnicích – doplnit posun
    return T

# ================================================================= HLAVNÍ
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
LO = Mesh("LOD1_Ves")
if "--kus" in args:
    name = args[args.index("--kus") + 1]
    P_ = BUILDERS[name]()
    lod_for(P_, LO); lod = LO.build(smooth_angle=30)
    preview_scene(trees=(), dirt=(0.0, 0.0, 50.0, 0.0))
    base = "ves_" + name.lower()
    export_all(base, [lod])
    if RENDER:
        R_ = {"Dum3": 13, "Dum2": 10, "Usedlost": 14, "Stodola": 12, "Studna": 4.5, "Sklep": 9, "Zidka_rovna": 7, "Zidka_roh": 7, "Snos": 5}[name]
        views = {base + "_a": (Vector((-R_ * 1.1, -R_ * 1.35, R_ * 0.55)), Vector((0, 0, 0.4)), 28, 0.0),
                 base + "_b": (Vector((R_ * 0.9, R_ * 0.4, 1.65)), Vector((-R_ * 0.2, -R_ * 0.1, 0.5)), 22, 0.0)}
        if name == "Sklep":
            views[base + "_c"] = (Vector((0.2, -0.6, 1.5)), Vector((0.0, 4.0, 0.8)), 18, 1.6)
        render_views(views, PRE)
else:
    # CELÁ VES: protáhlá náves s cestou, domy štítem k návsi
    LAY = [("D3a", "Dum3", -24.0, 16.0, math.pi / 2), ("D2a", "Dum2", -5.0, 13.5, math.pi / 2), ("U1", "Usedlost", 13.0, 17.5, math.pi), ("D3b", "Dum3", 33.0, 16.0, math.pi / 2),
           ("D2b", "Dum2", -31.0, -13.5, -math.pi / 2), ("D3c", "Dum3", -11.0, -16.0, -math.pi / 2), ("D2c", "Dum2", 8.0, -13.5, -math.pi / 2 + 0.06),
           ("S1", "Stodola", 28.0, -17.0, 0.04), ("S2", "Stodola", -24.0, 36.0, 0.0),
           ("St", "Studna", 3.0, 3.6, 0.0), ("Sk", "Sklep", -47.0, 2.0, math.pi / 2),
           ("Z1", "Zidka_rovna", -36.0, 29.0, 0.0), ("Z2", "Zidka_rovna", -4.0, 29.5, 0.03), ("Z3", "Zidka_roh", 41.0, 28.0, 0.0),
           ("Z4", "Zidka_rovna", -20.0, -31.0, 0.0), ("Z5", "Zidka_rovna", 14.0, -31.5, -0.02), ("Z6", "Zidka_roh", -44.0, -30.0, -math.pi / 2),
           ("N1", "Snos", -40.0, 40.0, 0.4), ("N2", "Snos", 46.0, -38.0, 1.2), ("N3", "Snos", 10.0, 40.0, 2.0)]
    lod_off = []
    for (tag, name, x, y, rot) in LAY:
        LOt = Mesh("tmp")
        place(tag, name, x, y, rot, LOt)
        lod_off.append((LOt, x, y, rot))
    # LOD: krabice z jednotlivých dílů posunout
    for (LOt, x, y, rot) in lod_off:
        o = LOt.build(smooth_angle=30)
        if o is None: continue
        o.matrix_world = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rot, 4, 'Z')
        o.name = "LODtmp"
    tmp = [o for o in scene.objects if o.name.startswith("LODtmp")]
    bpy.ops.object.select_all(action='DESELECT')
    for o in tmp: o.select_set(True)
    bpy.context.view_layer.objects.active = tmp[0]; bpy.ops.object.join(); lod = tmp[0]; lod.name = "LOD1_Ves"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    E = [empty("Ves_Naves_Stred", (0, 0, 0)), empty("Ves_Cesta_Zapad", (-60, 0, 0)), empty("Ves_Cesta_Vychod", (60, 0, 0))]
    preview_scene(trees=(), dirt=(0.0, 0.0, 50.0, 0.0))
    export_all("ves_celek", [lod])
    if RENDER:
        views = {"ves_1_nadhled": (Vector((-38.0, -62.0, 30.0)), Vector((2.0, 4.0, 0.0)), 26, 0.0),
                 "ves_2_naves":   (Vector((-14.0, -4.0, 1.7)), Vector((6.0, 9.0, 0.8)), 22, 0.0),
                 "ves_3_dum":     (Vector((-17.0, 9.0, 1.7)), Vector((-24.5, 20.0, 0.6)), 20, 0.0),
                 "ves_4_sklep":   (Vector((-38.5, 4.5, 1.7)), Vector((-46.0, 2.0, 1.3)), 24, 0.0),
                 "ves_5_usedlost": (Vector((22.0, 5.0, 3.0)), Vector((13.0, 17.0, 0.4)), 22, 0.0)}
        render_views(views, PRE)
print("HOTOVO")
