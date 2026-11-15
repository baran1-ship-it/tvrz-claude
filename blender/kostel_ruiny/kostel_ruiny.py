# -*- coding: utf-8 -*-
"""
Zřícenina vesnického gotického kostela – Odkaz Havrana (Čechy 1393)
Předloha: zříceniny kostelů v KCD (Přibyslavice) a skutečné české zříceniny (Branišov, Kuklov, Třebařov,
Klášterní Skalice, Panenský Týnec). Kostel z doby kolem 1340, vyhořelý a opuštěný.
 - západní hranolová věž, diagonálně zlomená (SZ nároží ~15 m, JV ~7 m), kapsy po trámech, ohořelý trám
 - loď 10,5 × 6,8 m (uvnitř): jižní zeď stojí s lomeným profilovaným portálem a dvěma vysokými okny,
   severní zeď zřícená na sutinový val, štít nad vítězným obloukem
 - lomený vítězný oblouk, dva schody na presbytář
 - presbytář s pětibokým závěrem (5/8): klenba – jedno pole žebrové klenby zčásti zřícené (žebra visí proti nebi),
   závěr zaklenutý celý; okna s kružbami (dvě celé, dvě rozbité), konzoly, svorníky, opěrné pilíře s kamennými stříškami
 - sakristie na severu: celá valená klenba, tma, úzká střílna, dveře visí na jednom pantu
 - zbytky omítky a fresek, sanktuář (pastoforium), rozbitá oltářní menza, převrácená křtitelnice, náhrobní desky
 - sutinové kupy, spadlé kusy žeber, ohořelé trámy, břečťan, zbytky hřbitovní zdi s křížem
Souřadnice Blender: Z nahoru, +X = východ (oltář), -Y = jih (vstup). Spuštění: python kostel_ruiny.py [--norender]
"""
import math, os, sys, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix
import shapely
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box as sbox
from shapely.ops import unary_union
from shapely import affinity

SEED = 1393
OUT = os.path.dirname(os.path.abspath(__file__))
FOTO = os.path.join(OUT, "foto"); TEX = os.path.join(OUT, "textury"); os.makedirs(TEX, exist_ok=True)
PRE = os.path.join(OUT, "nahledy_kostel"); os.makedirs(PRE, exist_ok=True)
RENDER = "--norender" not in sys.argv
FAST = os.environ.get("FAST") == "1"                 # rychlý test: hrubší voxely
random.seed(SEED); RNG = np.random.default_rng(SEED)
PFX = "Kostel"
exec(open(os.path.join(OUT, "_spolecne.py")).read())
exec(open(os.path.join(OUT, "tesar.py")).read())
exec(open(os.path.join(OUT, "_stavba.py")).read())
DOORS = []
VX = (lambda v: v * 1.6) if FAST else (lambda v: v)

# ================================================================= MATERIÁLY
def desat(c, sat=0.5, gamma=1.0, add=0.0):
    def f(a):
        a = a ** gamma; g = a.mean(2, keepdims=True)
        return ((g + (a - g) * sat) * np.array(c)) + add
    return f
HMAP["plaster_stone_wall_02"] = _load_h("plaster_stone_wall_02")
M["zdivo_in"] = vcol_mat("M_ZdivoInterier", "plaster_stone_wall_02", "zdi", desat([0.95, 0.92, 0.86], 0.75, 1.05), nstr=1.1, rough_mul=lambda a: 0.75 + 0.25 * a)
M["omitka_k"] = vcol_mat("M_OmitkaKostel", "white_rough_plaster", "omk", desat([0.93, 0.89, 0.80], 0.6, 1.0), nstr=0.9, rough_mul=lambda a: 0.8 + 0.2 * a)
M["piskovec"] = mat("M_Piskovec", "old_sandstone_02", "pis", desat([0.98, 0.93, 0.84], 0.22, 1.1), nstr=1.3, rough_mul=lambda a: 0.75 + 0.25 * a)
M["piskovec_m"] = mat("M_PiskovecMech", "old_sandstone_02", "pism", moss_k(0.55, 0.62, (0.95, 0.90, 0.82), 0.45), nstr=1.3, rough_mul=lambda a: 0.85 + 0.15 * a)
M["piskovec_c"] = mat("M_PiskovecSaze", "old_sandstone_02", "pisc", desat([0.40, 0.36, 0.32], 0.4, 1.2), nstr=1.3)
M["sut"]      = vcol_mat("M_Sut", "cobblestone_large_01", "sut", desat([0.80, 0.78, 0.74], 0.6, 1.05), nstr=1.3)
M["hlina_k"]  = vcol_mat("M_HlinaKostel", "dirt_floor", "hlk", tint([0.66, 0.60, 0.52], 1.1), nstr=1.0, rough_mul=lambda a: 0.85 + 0.15 * a)
# ohořelé dřevo: textura aligátorového uhlíku generovaná skriptem (foto/char_wood_*), hnědá místa jen opálená
M["tram_oh"]  = mat("M_TramOhoraly", "char_wood", "troh6", lambda a: a * np.array([1.0, 0.95, 0.88]), nstr=1.7, rough_mul=lambda a: a)
M["uhel_cel"] = mat("M_TramOhoralyCelo", "char_wood", "trohc3", lambda a: a * np.array([0.8, 0.75, 0.72]), nstr=2.2, rough_mul=lambda a: a)
# zvětralý dub (kříže, vrata): stříbřitě šedohnědý jako roubení kovárny, jen tmavší a vlhčí
M["dub_sedy"] = mat("M_DubZvetraly", "rough_wood", "dbs3", silver([0.56, 0.52, 0.47], 0.38, 1.15), nstr=1.8)
M["dub_celo"] = mat("M_DubZvetralyCelo", "rough_wood", "dbc", tint([0.30, 0.25, 0.20], 1.2), nstr=1.8)
M["tram_shn"] = mat("M_PrknaStara", "rough_wood", "pks3", silver([0.80, 0.72, 0.62], 0.55, 1.1), nstr=1.8)

# ================================================================= GEOMETRICKÉ POMŮCKY
def arch_ring(hw, zb, zs, r_k=1.4, n=12):
    """lomený oblouk (u, z): přímé ostění od zb do zs, nad tím dva kruhové oblouky o poloměru r_k*hw"""
    r = r_k * hw; ca = hw - r
    ta = math.acos(max(-1.0, min(1.0, -ca / r)))           # úhel, kde oblouk protne osu u = 0
    pts = [(-hw, zb), (hw, zb)]
    for k in range(n + 1):
        t = ta * k / n; pts.append((ca + r * math.cos(t), zs + r * math.sin(t)))
    for k in range(n, -1, -1):
        t = ta * k / n; pts.append((-(ca + r * math.cos(t)), zs + r * math.sin(t)))
    out = []
    for p in pts:
        if not out or (abs(out[-1][0] - p[0]) + abs(out[-1][1] - p[1])) > 1e-5: out.append(p)
    if abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) < 1e-5: out.pop()
    return out
def arch_apex(hw, zs, r_k=1.4):
    r = r_k * hw; return zs + math.sqrt(r * r - (r - hw) ** 2)
def arch_poly(hw, zb, zs, r_k=1.4, n=12):
    return Polygon(arch_ring(hw, zb, zs, r_k, n))
def prof(u, r_k=1.4):
    """normovaný lomený profil: u = 0 vrchol (1.0), u = 1 patka (0.0)"""
    u = min(1.0, max(0.0, abs(u))); r = r_k
    return math.sqrt(max(0.0, r * r - (u + r - 1) ** 2)) / math.sqrt(2 * r - 1)

class Fr:
    """rámec stěny: O na ose zdi v z = 0, U podél, N kolmo (ven = +N), Z nahoru"""
    def __init__(s, p0, p1, nsign=1):
        s.O = Vector((p0[0], p0[1], 0.0)); d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0.0)); s.L = d.length; s.U = d / s.L
        s.N = Vector((-s.U.y, s.U.x, 0.0)) * nsign; s.Z = Vector((0, 0, 1))
    def P(s, u, z, d=0.0): return s.O + s.U * u + s.Z * z + s.N * d

def mesh_obj(name, verts, faces):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return o

def _tri_rings(poly):
    tris = shapely.constrained_delaunay_triangles(poly)
    return [list(t.exterior.coords)[:3] for t in tris.geoms if t.area > 1e-10]
def extrude2d(name, poly, Pf, d0, d1):
    """2D polygon (i s dírami) vytažený mezi hloubkami d0..d1; Pf(u, v, d) -> svět"""
    if poly.is_empty: return None
    polys = list(poly.geoms) if hasattr(poly, "geoms") else [poly]
    V = []; Fc = []; idx = {}
    def vid(p, d):
        k = (round(p[0], 6), round(p[1], 6), d)
        if k not in idx: idx[k] = len(V); V.append(Pf(p[0], p[1], d))
        return idx[k]
    for pg in polys:
        if pg.geom_type != "Polygon" or pg.area < 1e-6: continue
        pg = shapely.set_precision(pg, 1e-5)
        for t in _tri_rings(pg):
            Fc.append((vid(t[0], d1), vid(t[1], d1), vid(t[2], d1))); Fc.append((vid(t[2], d0), vid(t[1], d0), vid(t[0], d0)))
        for ring in [pg.exterior] + list(pg.interiors):
            c = list(ring.coords)[:-1]
            for i in range(len(c)):
                a, b = c[i], c[(i + 1) % len(c)]
                Fc.append((vid(a, d0), vid(b, d0), vid(b, d1), vid(a, d1)))
    if not Fc: return None
    return mesh_obj(name, V, Fc)
def hull_obj(name, pts):
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(p)) for p in pts]
    r = bmesh.ops.convex_hull(bm, input=vs)
    bmesh.ops.delete(bm, geom=[v for v in r["geom_interior"] if isinstance(v, bmesh.types.BMVert)] + r["geom_unused"], context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); return o

def ragged_top(u0, u1, ztop, step=0.26, q=0.14, jit=0.10, zb=-0.35):
    """polygon zdi v (u, z): dole rovně, nahoře rozpadlé řádky (schodovitě po vrstvách kamene)"""
    pts = [(u0, zb), (u1, zb)]
    us = [u1]; u = u1
    while u > u0 + step * 0.6:
        u -= step * random.uniform(0.35, 1.7); us.append(max(u0, u))
    if us[-1] > u0: us.append(u0)
    zprev = None; ph = random.uniform(0, 50)
    for i, u in enumerate(us):
        z = ztop(u) + jit * 2.6 * (float(vnoise(np.array(u * 1.3 + ph), np.array(ph), 6)) - 0.5) + random.gauss(0, jit * 0.35)
        z -= (random.uniform(0.1, 0.3) if random.random() < 0.05 else 0.0)
        z = max(zb + 0.25, round(z / q) * q + random.uniform(-0.04, 0.04))
        if zprev is not None and random.random() < 0.6: pts.append((u + random.uniform(-0.04, 0.04) if 0 < i < len(us) - 1 else u, zprev))
        pts.append((u, z)); zprev = z
    pg = Polygon(pts)
    if not pg.is_valid: pg = pg.buffer(0)
    return pg

def wall(name, p0, p1, t, ztop, e0=0.0, e1=0.0, nsign=1, zb=-0.35, step=0.32, jit=0.10, q=0.20):
    """rovná zeď s rozpadlou korunou; vrací (objekt, rámec)"""
    fr = Fr(p0, p1, nsign)
    pg = ragged_top(-e0, fr.L + e1, ztop, step=step, jit=jit, q=q, zb=zb)
    o = extrude2d(name, pg, lambda u, z, d: fr.P(u, z, d), -t / 2, t / 2)
    return o, fr

def window_cutters(fr, uc, t, hw, zsill, zspr, frame=0.14, depth_g=0.28, splay_o=0.10, splay_i=0.55, sill_i=0.6, zspr_i=0.25, r_k=1.4):
    """okenní otvor se šambránou: venku malá špaleta, v rovině skla kamenný rám, dovnitř velká šikmá špaleta"""
    hf = hw + frame
    def ring(h, zb, zs, d):
        return [fr.P(uc + u, z, d) for (u, z) in arch_ring(h, zb, zs, r_k, 10)]
    dg = t / 2 - depth_g
    A = hull_obj("cutA", ring(hf + splay_o, zsill - 0.02, zspr, t / 2 + 0.35) + ring(hf, zsill - 0.02, zspr, dg))
    B = hull_obj("cutB", ring(hf, zsill - 0.02, zspr, dg + 0.01) + ring(hf + splay_i, zsill - sill_i, zspr + zspr_i, -t / 2 - 0.35))
    return [A, B], dg

# ================================================================= PŮDORYS
T_N, T_V, T_P = 1.0, 1.2, 0.9
NX0, NX1, NY = -6.5, 6.0, 4.4                 # loď (vnější líc)
VX0, VY = -10.9, 2.4                          # věž
PIX0 = 5.5                                    # presbytář: vnitřní polygon začíná v ose východní zdi lodi
APR = 2.6 / math.sin(math.radians(67.5)); APC = 11.2
AP = [(APC + APR * math.cos(math.radians(a)), APR * math.sin(math.radians(a))) for a in (-67.5, -22.5, 22.5, 67.5)]
P_IN = Polygon([(PIX0, -2.6), AP[0], AP[1], AP[2], AP[3], (PIX0, 2.6)])
P_AX = P_IN.buffer(T_P / 2, join_style=2, mitre_limit=5)
P_EX = P_IN.buffer(T_P, join_style=2, mitre_limit=5)
SX0, SX1, SY0, SY1, T_S = 6.0, 9.6, 3.3, 6.8, 0.75     # sakristie
ZF_P = 0.36                                    # podlaha presbytáře
Z0V, ZKV = 5.0, 8.0                            # patky a svorníky klenby
INT = unary_union([sbox(NX0 + T_N, -NY + T_N, NX1 - T_N, NY - T_N), sbox(VX0 + T_V, -VY + T_V, NX0, VY - T_V),
                   P_IN.intersection(sbox(NX1, -5, 20, 5)), sbox(NX1 - T_N - 0.2, -2.1, NX1 + 0.1, 2.1)])
INT_SAK = sbox(SX0 + T_S, SY0 + 0.2, SX1 - T_S, SY1 - T_S)
# fresky: (střed, U podél zdi, N do místnosti, šířka, výška, oblast atlasu)
DECALS = [((NX1 - T_N - 0.01, 2.85, 2.65), (0, -1, 0), (-1, 0, 0), 0.95, 1.95, "A"),
          ((NX1 - T_N - 0.01, -2.85, 2.55), (0, -1, 0), (-1, 0, 0), 0.95, 1.95, "B"),
          ((1.35, -NY + T_N + 0.01, 3.05), (1, 0, 0), (0, 1, 0), 0.62, 0.62, "C"),
          ((-4.9, -NY + T_N + 0.01, 3.0), (1, 0, 0), (0, 1, 0), 0.58, 0.58, "D"),
          ((6.85, 2.6 - 0.01, 3.35), (-1, 0, 0), (0, -1, 0), 0.55, 0.55, "C"),
          ((7.85, -2.6 + 0.01, 2.42), (1, 0, 0), (0, 1, 0), 2.9, 0.26, "E"),
          ((10.85, -2.6 + 0.01, 2.42), (1, 0, 0), (0, 1, 0), 2.3, 0.26, "E"),
          ((6.6, 2.6 - 0.01, 2.0), (-1, 0, 0), (0, -1, 0), 1.0, 0.26, "E")]
def decal_keep(P):
    k = np.zeros(len(P), np.float32)
    for (c, U, N, w, h, _) in DECALS:
        d = P - np.array(c, np.float32)
        a = np.abs(d @ np.array(U, np.float32)); b = np.abs(d[:, 2]); n = np.abs(d @ np.array(N, np.float32))
        mg = 0.04 + 0.45 * nzv(P[:, 0] * 2.2 + P[:, 1] * 2.2, P[:, 2] * 2.2, 1, 5, 3)
        k = np.maximum(k, ((a < w / 2 + mg) & (b < h / 2 + mg) & (n < 0.6)).astype(np.float32) * 2.0)
    return k
def nzv(x, y, s=1.0, ch=3, o=3):
    return fbm(np.asarray(x, np.float32) * s, np.asarray(y, np.float32) * s, o, ch)

def _bb(o):
    P = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return Vector((min(p.x for p in P), min(p.y for p in P), min(p.z for p in P))), Vector((max(p.x for p in P), max(p.y for p in P), max(p.z for p in P)))
def cut_join(objs, cutters):
    """každý kus zdi zvlášť (málo polygonů = rychlý přesný boolean), pak spojit; sjednocení udělá voxel remesh"""
    for o in objs:
        lo, hi = _bb(o)
        for c in cutters:
            a, b = _bb(c)
            if a.x > hi.x or b.x < lo.x or a.y > hi.y or b.y < lo.y or a.z > hi.z or b.z < lo.z: continue
            m = o.modifiers.new("b", 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = c; m.solver = 'EXACT'; _apply_mod(o, m)
    for c in cutters: bpy.data.objects.remove(c, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join()
    return objs[0]

# ================================================================= ZDIVO (vektorizovaná verze postupu masonry)
def _hs(H, u, v):
    n = H.shape[0]; x = np.mod(u, 1.0) * n; y = (1.0 - np.mod(v, 1.0)) * n - 1e-3
    x0 = np.floor(x).astype(np.int64) % n; y0 = np.floor(y).astype(np.int64) % n; x1 = (x0 + 1) % n; y1 = (y0 + 1) % n
    fx = x - np.floor(x); fy = y - np.floor(y)
    return (H[y0, x0] * (1 - fx) + H[y0, x1] * fx) * (1 - fy) + (H[y1, x0] * (1 - fx) + H[y1, x1] * fx) * fy
_PO = np.array([PROJ_OFF[0], PROJ_OFF[1], PROJ_OFF[2]], np.float32)
def _proj(P, ax, tile):
    """P (n,3), ax (n,) -> uv (n,2)"""
    a = np.where(ax == 0, P[:, 1], P[:, 0]); b = np.where(ax == 2, P[:, 1], P[:, 2])
    return np.stack([a / tile + _PO[ax, 0], b / tile + _PO[ax, 1]], 1)
def zdivo(o, name, cls_fn, CL, col_fn, ratio, voxel=0.045, drop_fn=None, remesh=True):
    """o: uzavřený tvar. cls_fn(P, N) -> třída (int). CL[třída] = dict(h=klíč výškové mapy|None, tile, S, mat).
    col_fn(P, N, h, c) -> (n,3) lineární násobič barvy (glTF COLOR_0)."""
    if remesh:
        m = o.modifiers.new("r", 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = VX(voxel); m.use_smooth_shade = True; _apply_mod(o, m)
    o.name = name; me = o.data; me.name = name
    if drop_fn:
        bm = bmesh.new(); bm.from_mesh(me); bm.normal_update()
        dead = [f for f in bm.faces if drop_fn(f.calc_center_median(), f.normal)]
        bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(me); bm.free()
    nv = len(me.vertices)
    P = np.zeros(nv * 3, np.float32); me.vertices.foreach_get("co", P); P = P.reshape(-1, 3)
    Nn = np.zeros(nv * 3, np.float32); me.vertex_normals.foreach_get("vector", Nn); Nn = Nn.reshape(-1, 3)
    cv = np.asarray(cls_fn(P, Nn), np.int32)
    h = np.ones(nv, np.float32); S = np.zeros(nv, np.float32); tile = np.ones(nv, np.float32)
    w = np.abs(Nn) ** 4; w /= np.maximum(1e-6, w.sum(1, keepdims=True))
    for c, d in CL.items():
        mk = cv == c
        if not mk.any(): continue
        tile[mk] = d.get("tile", 1.5)
        if d.get("h"):
            H = HMAP[d["h"]]; Pm = P[mk]; hh = np.zeros(mk.sum(), np.float32)
            for i in range(3):
                uv = _proj(Pm, np.full(len(Pm), i), d["tile"]); hh += w[mk, i] * _hs(H, uv[:, 0], uv[:, 1])
            h[mk] = hh; S[mk] = d["S"]
        else:
            h[mk] = 1.0; S[mk] = 0.0
    P2 = P + Nn * ((h - 1.0) * S)[:, None]
    flat = S == 0
    P2[flat] += Nn[flat] * (0.004 * nzv(P[flat, 0] * 9 + P[flat, 2] * 3, P[flat, 1] * 9 - P[flat, 2] * 5, 1, 7, 2))[:, None]
    me.vertices.foreach_set("co", P2.ravel())
    npg = len(me.polygons)
    FC = np.zeros(npg * 3, np.float32); me.polygons.foreach_get("center", FC); FC = FC.reshape(-1, 3)
    FN = np.zeros(npg * 3, np.float32); me.polygons.foreach_get("normal", FN); FN = FN.reshape(-1, 3)
    # centra/normály po posunu – třídu plochy určíme z původní polohy (průměr vrcholů)
    ls = np.zeros(npg, np.int32); me.polygons.foreach_get("loop_start", ls); lt = np.zeros(npg, np.int32); me.polygons.foreach_get("loop_total", lt)
    nl = len(me.loops); lv = np.zeros(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
    lf = np.repeat(np.arange(npg), lt)
    FC0 = np.zeros((npg, 3), np.float32); np.add.at(FC0, lf, P[lv]); FC0 /= lt[:, None]
    FN0 = np.zeros((npg, 3), np.float32); np.add.at(FN0, lf, Nn[lv]); FN0 /= np.maximum(1e-6, np.linalg.norm(FN0, axis=1, keepdims=True))
    cf = np.asarray(cls_fn(FC0, FN0), np.int32)
    mats = []
    for c, d in CL.items():
        if d["mat"] not in mats: mats.append(d["mat"])
    me.materials.clear()
    for k_ in mats: me.materials.append(M[k_])
    lut = {c: mats.index(d["mat"]) for c, d in CL.items()}
    me.polygons.foreach_set("material_index", np.array([lut.get(int(c), 0) for c in cf], np.int32))
    ax = np.argmax(np.abs(FN0), 1)
    tl = np.array([CL.get(int(c), {"tile": 1.5}).get("tile", 1.5) for c in range(max(CL) + 1)], np.float32)[np.clip(cf, 0, max(CL))]
    uv = _proj(P[lv], ax[lf], tl[lf])
    ul = me.uv_layers.new(name="UVMap"); ul.data.foreach_set("uv", uv.astype(np.float32).ravel())
    col = np.clip(np.asarray(col_fn(P[lv], Nn[lv], h[lv], cf[lf]), np.float32), 0, 1.5)
    ca = me.color_attributes.new("Saze", 'BYTE_COLOR', 'CORNER')
    ca.data.foreach_set("color", np.concatenate([col, np.ones((nl, 1), np.float32)], 1).ravel())
    me.update(); me.shade_smooth()
    if ratio < 1.0:
        d = o.modifiers.new("d", 'DECIMATE'); d.ratio = ratio; d.use_collapse_triangulate = True; _apply_mod(o, d)
    return o

def is_inside(P, Nn, off=0.35):
    q = P + Nn * off
    ins = shapely.contains_xy(INT, q[:, 0], q[:, 1]) | (shapely.contains_xy(INT_SAK, q[:, 0], q[:, 1]) & (P[:, 2] < 4.0))
    return ins & (np.abs(Nn[:, 2]) < 0.8)

# výškové mapy a třídy zdiva: 0 venkovní lomové zdivo, 1 vnitřní líc (zatřené spáry), 2 omítka, 3 koruna/vrch (mech)
CL_ZED = {0: dict(h="broken_wall", tile=2.7, S=0.075, mat="zdivo"),
          1: dict(h="plaster_stone_wall_02", tile=2.3, S=0.045, mat="zdivo_in"),
          2: dict(h=None, tile=1.6, mat="omitka_k"),
          3: dict(h="broken_wall", tile=2.5, S=0.075, mat="zdivo")}
def plaster_mask(P, keep):
    """kde se drží omítka: šum + výška; keep(P) -> 0..1 ochrana (pod klenbou víc)"""
    n1 = nzv(P[:, 0] * 0.55 + P[:, 1] * 0.55, P[:, 2] * 0.75, 1, 4, 4); n2 = nzv(P[:, 0] * 2.3 + P[:, 1] * 2.3, P[:, 2] * 2.6, 1, 5, 2)
    thr = 0.66 - 0.24 * (keep(P) + decal_keep(P)) + 0.10 * (P[:, 2] < 0.7)
    return (n1 * 0.8 + n2 * 0.2) > thr
def make_cls(keep):
    def f(P, Nn):
        ins = is_inside(P, Nn)
        c = np.where(ins, 1, 0)
        c = np.where(ins & plaster_mask(P, keep), 2, c)
        c = np.where(Nn[:, 2] > 0.55, 3, c)
        return c
    return f
def col_zed(fire=1.0):
    def f(P, Nn, h, c):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        n1 = nzv(x * 0.9 + y * 0.7, z * 1.1, 1, 5, 4); n2 = nzv(x * 3.1 - y * 2.7, z * 3.3, 1, 6, 3)
        nb = nzv(x * 0.22 + y * 0.22, z * 0.3, 1, 1, 3)
        g = (0.60 + 0.20 * n1) * np.where((c == 0) | (c == 3), 0.66 * (0.72 + 0.5 * nb), 1.15)
        g = np.where(c == 2, 0.66 - 0.12 * n2, g * (0.55 + 0.45 * h))
        r = np.ones_like(g); gg = np.ones_like(g); b = np.ones_like(g)
        ext = (c == 0) | (c == 3)
        # mech: u země a na korunách
        mg = np.clip(1.0 - z / (0.55 + 0.6 * n1), 0, 1) * (0.5 + 0.5 * n2)
        mt = np.clip((Nn[:, 2] - 0.3) / 0.45, 0, 1) * np.clip(0.35 + 0.9 * n2, 0, 1)
        mm = np.where(ext, np.maximum(mg, mt), mg * 0.5)
        r = r * (1 - 0.48 * mm); gg = gg * (1 - 0.20 * mm); b = b * (1 - 0.60 * mm)
        # stékance pod korunou (venku), svislé
        st = nzv(x * 2.2 + y * 2.2, z * 0.18, 1, 7, 3)
        g = np.where(ext & (Nn[:, 2] < 0.5), g * (1 - 0.30 * np.clip((st - 0.45) * 3, 0, 1)), g)
        # požár: saze uvnitř nahoře (loď hořela nejvíc), sazemi zčernalé fleky
        fz = np.clip((z - 2.8) / 4.5, 0, 1) * np.clip(0.4 + 0.9 * (n1 - 0.35), 0, 1) * fire
        ins = (c == 1) | (c == 2)
        g = np.where(ins, g * (1 - 0.62 * fz), g)
        # vlhko u země uvnitř: zelenošedé
        dmp = np.where(ins, np.clip(1 - z / 1.3, 0, 1) * 0.5, 0)
        r = r * (1 - 0.25 * dmp); b = b * (1 - 0.3 * dmp)
        return np.stack([g * r, g * gg * 0.985, g * b * 0.96], 1)
    return f

print("věž…")
ztop_vez = lambda x, y: 6.9 + 8.6 * (0.5 * (-x - 6.0) / 4.9 + 0.5 * (y + 2.4) / 4.8) ** 1.25
V_parts = []
for (p0, p1, ns) in [((VX0 + T_V / 2, -VY), (VX0 + T_V / 2, VY), -1), ((VX0, VY - T_V / 2), (NX0 + 0.2, VY - T_V / 2), 1),
                     ((VX0, -VY + T_V / 2), (NX0 + 0.2, -VY + T_V / 2), -1)]:
    fr = Fr(p0, p1, ns)
    o, fr = wall("vz", p0, p1, T_V, lambda u, fr=fr: ztop_vez(fr.P(u, 0).x, fr.P(u, 0).y), e0=0.0, e1=0.0, nsign=ns, step=0.30, jit=0.14)
    V_parts.append((o, fr))
# východní stěna věže = střed západní zdi lodi, nad lodí pokračuje
o, frVE = wall("vze", (NX0 + T_N / 2, -VY), (NX0 + T_N / 2, VY), T_N, lambda u: ztop_vez(-6.0, -VY + u) - 0.4, e0=0.0, e1=0.0, nsign=1, step=0.30, jit=0.14)
V_parts.append((o, frVE))
VZ = V_parts[0][0]
# otvory věže: západní vchod, střílny, zvonová okna, kapsy po trámech, oblouk do lodi, lešenářské díry
cut = []
frW = V_parts[0][1]
c_, dgW = window_cutters(frW, VY, T_V, 0.55, -0.05, 2.15, frame=0.13, splay_o=0.04, splay_i=0.25, sill_i=0.0, zspr_i=0.15); cut += c_
VWIN = [(frW, VY, T_V, 0.55, -0.05, 2.15, "dvere", dgW)]
for (fr, uc, zs, zt) in [(V_parts[1][1], 2.6, 4.2, 5.0), (V_parts[2][1], 2.4, 4.5, 5.3), (frW, 3.4, 7.6, 8.5)]:
    c_, _ = window_cutters(fr, uc, T_V, 0.07, zs, zt, frame=0.06, splay_o=0.02, splay_i=0.45, sill_i=0.5, zspr_i=0.3, depth_g=0.2); cut += c_
for (fr, uc) in [(frW, 1.55), (frW, 3.25), (V_parts[1][1], 1.7), (V_parts[1][1], 3.05)]:     # zvonová okna (dvojice)
    c_, dg_ = window_cutters(fr, uc, T_V, 0.30, 11.6, 13.0, frame=0.10, splay_o=0.03, splay_i=0.12, sill_i=0.1, zspr_i=0.1, depth_g=0.25); cut += c_
    VWIN.append((fr, uc, T_V, 0.30, 11.6, 13.0, "ramek", dg_))
c_, _ = window_cutters(frVE, VY, T_N, 0.80, -0.05, 2.7, frame=0.0, splay_o=0.0, splay_i=0.05, sill_i=0.0, zspr_i=0.0, depth_g=0.5); cut += c_
for zz in (5.35, 9.55):
    for k in range(3):
        y = -0.75 + k * 0.75
        cut.append(solid_box((VX0 + T_V - 0.35, y - 0.14, zz), (VX0 + T_V + 0.05, y + 0.14, zz + 0.30)))
        cut.append(solid_box((NX0 - 0.05, y - 0.14, zz), (NX0 + 0.33, y + 0.14, zz + 0.30)))
for (fr, us) in [(frW, (0.9, 2.4, 3.9)), (V_parts[1][1], (0.8, 2.2, 3.6)), (V_parts[2][1], (0.8, 2.2, 3.6))]:
    for zz in (3.0, 6.2, 9.4):
        for uu in us:
            c0 = fr.P(uu + random.uniform(-0.2, 0.2), zz + random.uniform(-0.1, 0.1), T_V / 2)
            cut.append(hull_obj("put", [c0 + fr.U * a + fr.Z * b + fr.N * dd for a in (-0.08, 0.08) for b in (-0.08, 0.08) for dd in (-0.35, 0.3)]))
VZ = cut_join([o_ for o_, fr_ in V_parts], cut)
VEZ_KEEP = lambda P: np.full(len(P), 0.15)
vez = zdivo(VZ, "Kostel_Vez", make_cls(VEZ_KEEP), CL_ZED, col_zed(0.8), 0.135, voxel=0.05,
            drop_fn=lambda c, n: n.z < -0.9 and c.z < -0.3)
print("věž hotová", len(vez.data.polygons))

# ================================================================= LOĎ
print("loď…")
def portal_parts(fr, uc, t, hw, zs, orders=3, ow=0.12, od=0.16, hwr=0.25, zr=0.45):
    """lomený ustupující portál: kamenné pásy (pískovec) + výřezy do zdiva"""
    Pf = lambda u, z, d: fr.P(uc + u, z, d)
    back = t / 2 - orders * od - 0.08
    cutters = [extrude2d("pc0", arch_poly(hw + orders * ow, -0.4, zs), Pf, back - 0.02, t / 2 + 0.4),
               extrude2d("pc1", arch_poly(hw + hwr, -0.4, zs + zr), Pf, -t / 2 - 0.4, back + 0.01)]
    bands = []
    for k in range(orders):
        ho = hw + (orders - k) * ow; hi = hw + (orders - k - 1) * ow
        fz = t / 2 - k * od
        band = arch_poly(ho, 0.0, zs).difference(arch_poly(hi, -0.1, zs))
        bands.append(extrude2d("pb", band, Pf, back, fz - 0.035))
        band2 = arch_poly(ho, 0.0, zs).difference(arch_poly(hi + 0.035, -0.1, zs))            # sražená hrana
        bands.append(extrude2d("pb", band2, Pf, fz - 0.04, fz))
        for sg in (-1, 1):                                                                         # patky (sokly)
            bands.append(extrude2d("pp", sbox(sg * hi if sg > 0 else -ho - 0.03, 0.0, sg * ho + 0.03 if sg > 0 else -hi, 0.42).buffer(0), Pf, back, fz + 0.03))
    return cutters, bands, back

ztop_S = lambda x: 8.25 + 0.35 * math.sin(x * 0.9) - 1.85 * sm(1.6, 2.4, x) * (1 - sm(4.2, 5.0, x)) + 0.4 * sm(4.8, 5.8, x) - 0.5 * (1 - sm(-6.4, -5.2, x))
def ztop_N(x):
    z = 6.1 - 4.8 * sm(-5.0, -4.3, x)
    z += 0.5 * math.sin(x * 1.7) + 0.4 * math.sin(x * 0.6 + 1.0) - 0.4 * sm(-2.0, 0.0, x) * (1 - sm(1.5, 3.0, x))
    return max(0.25, z + 1.6 * sm(3.6, 5.2, x) + 1.4 * sm(5.0, 5.8, x))
def ztop_E(y):
    gab = 8.45 + max(0.0, 3.2 - abs(y)) * 1.2
    if y > 0.25: gab = min(gab, 9.4 - (y - 0.25) * 1.15)
    return min(gab, 11.7) + (0.35 if abs(y) > 3.4 else 0.0)
L_parts = []; cut = []; SAND = Mesh("Kostel_Piskovec")
oS, frS = wall("lS", (NX0, -NY + T_N / 2), (NX1, -NY + T_N / 2), T_N, lambda u: ztop_S(NX0 + u), nsign=-1); L_parts.append(oS)
oN, frN = wall("lN", (NX0, NY - T_N / 2), (NX1, NY - T_N / 2), T_N, lambda u: ztop_N(NX0 + u), nsign=1, jit=0.18); L_parts.append(oN)
oE, frE = wall("lE", (NX1 - T_N / 2, -NY), (NX1 - T_N / 2, NY), T_N, lambda u: ztop_E(-NY + u), nsign=-1); L_parts.append(oE)
oW1, frW1 = wall("lW1", (NX0 + T_N / 2, -NY), (NX0 + T_N / 2, -VY + 0.3), T_N, lambda u: 7.7 + 0.3 * math.sin(u * 3), nsign=1); L_parts.append(oW1)
oW2, frW2 = wall("lW2", (NX0 + T_N / 2, VY - 0.3), (NX0 + T_N / 2, NY), T_N, lambda u: 5.9 - 0.6 * u, nsign=1); L_parts.append(oW2)
UPORT = -3.2 - NX0
pc, pb, PBACK = portal_parts(frS, UPORT, T_N, 0.80, 2.4); cut += pc
PORTAL_OBJS = [b for b in pb if b]
WIN = []                     # (rámec, u, t, hw, zsill, zspr, druh, dg)
for (fr, uc, kind) in [(frS, -0.4 - NX0, "kruzba2"), (frS, 3.0 - NX0, "rozbite"), (frN, -4.2 - NX0, "pahyl")]:
    c_, dg = window_cutters(fr, uc, T_N, 0.62, 3.4, 6.0); cut += c_; WIN.append((fr, uc, T_N, 0.62, 3.4, 6.0, kind, dg))
# vítězný oblouk
TA_HW, TA_ZS = 2.1, 4.6
cut.append(extrude2d("ta", arch_poly(TA_HW + 0.2, -0.4, TA_ZS), lambda u, z, d: frE.P(NY + u, z, d), -T_N / 2 - 0.3, T_N / 2 + 0.3))
TA_BAND = arch_poly(TA_HW + 0.2, 0.0, TA_ZS).difference(arch_poly(TA_HW, -0.1, TA_ZS))
# kapsy po trámech stropu lodi, kropenka u portálu, lešenářské díry
for k in range(10):
    x = NX0 + 1.4 + k * 1.05
    if ztop_S(x) > 7.75: cut.append(solid_box((x - 0.15, -NY + T_N - 0.38, 7.15), (x + 0.15, -NY + T_N + 0.05, 7.47)))
cut.append(solid_box((-2.05, -NY + T_N - 0.3, 0.95), (-1.7, -NY + T_N + 0.05, 1.45)))
for (fr, L, top) in [(frS, NX1 - NX0, lambda u: ztop_S(NX0 + u)), (frE, 2 * NY, lambda u: ztop_E(-NY + u))]:
    for zz in (2.9, 5.6, 8.3):
        for uu in np.arange(0.9, L - 0.5, 1.75):
            if top(uu) < zz + 0.4: continue
            c0 = fr.P(uu + random.uniform(-0.25, 0.25), zz + random.uniform(-0.12, 0.12), T_N / 2)
            if fr is frS and (abs(c0.x + 3.2) < 1.5 or abs(c0.x + 0.4) < 1.0 or abs(c0.x - 3.0) < 1.0): continue
            if fr is frE and abs(c0.y) < 2.6 and zz < 8: continue
            cut.append(hull_obj("put", [c0 + fr.U * a + fr.Z * b + fr.N * dd for a in (-0.08, 0.08) for b in (-0.08, 0.08) for dd in (-0.3, 0.3)]))
LOD_OBJ = cut_join(L_parts, cut)
lod_keep = lambda P: np.clip(0.25 + 0.25 * (P[:, 0] > 4.5), 0, 1)
lod_ = zdivo(LOD_OBJ, "Kostel_Lod", make_cls(lod_keep), CL_ZED, col_zed(1.0), 0.125, voxel=0.05,
             drop_fn=lambda c, n: n.z < -0.9 and c.z < -0.3)
print("loď hotová", len(lod_.data.polygons))

# ================================================================= PRESBYTÁŘ, OPĚRÁKY, SAKRISTIE
print("presbytář…")
def ztop_P(x, y):
    z = 8.75 + 0.25 * math.sin(x * 1.3 + y) + 0.2 * math.sin(y * 2.1)
    if y < 0: z -= 1.75 * sm(5.9, 6.6, x) * (1 - sm(8.6, 9.3, x))           # jižní zeď 1. pole: pobořená (proto spadla klenba)
    if x > 12.6 and y < -0.6: z -= 0.7 * sm(12.6, 13.4, x)
    return z
ring = list(P_AX.exterior.coords)[:-1]
ccw = P_AX.exterior.is_ccw
P_parts = []; cut = []; PFR = []
n_ = len(ring)
for i in range(n_):
    a, b = Vector((*ring[i], 0)), Vector((*ring[(i + 1) % n_], 0))
    if a.x < 6.0 and b.x < 6.0: continue
    def turn(i0):
        p_, q_, r_ = Vector((*ring[(i0 - 1) % n_], 0)), Vector((*ring[i0 % n_], 0)), Vector((*ring[(i0 + 1) % n_], 0))
        return (q_ - p_).normalized().angle((r_ - q_).normalized())
    e0 = T_P / 2 * math.tan(turn(i) / 2) + 0.02; e1 = T_P / 2 * math.tan(turn(i + 1) / 2) + 0.02
    fr = Fr(a, b, -1 if ccw else 1)
    o, fr = wall("pw", a, b, T_P, lambda u, fr=fr: ztop_P(fr.P(u, 0).x, fr.P(u, 0).y), e0=e0, e1=e1, nsign=-1 if ccw else 1)
    P_parts.append(o); PFR.append(fr)
def seg_for(pt):
    best = None
    for fr in PFR:
        u = (Vector((pt[0], pt[1], 0)) - fr.O).dot(fr.U); d = (Vector((pt[0], pt[1], 0)) - fr.O).dot(fr.N)
        if -0.01 < u < fr.L + 0.01 and abs(d) < 0.6 and (best is None or abs(d) < best[2]): best = (fr, u, abs(d))
    return best[0], best[1]
APM = [((AP[i][0] + AP[i + 1][0]) / 2, (AP[i][1] + AP[i + 1][1]) / 2) for i in range(3)]
def outp(p, k=0.45):
    v = Vector((p[0] - APC, p[1], 0)).normalized(); return (p[0] + v.x * k, p[1] + v.y * k)
for (pt, hw, zsl, zsp, kind) in [((7.7, -3.05), 0.55, 2.7, 5.4, "pahyl2"), ((10.85, -3.05), 0.55, 2.7, 5.4, "kruzba2"),
                                 (outp(APM[0]), 0.47, 2.7, 5.2, "rozbite"), (outp(APM[1]), 0.47, 2.7, 5.2, "kruzba2"),
                                 (outp(APM[2]), 0.47, 2.7, 5.2, "trojlist")]:
    fr, u = seg_for(pt)
    c_, dg = window_cutters(fr, u, T_P, hw, zsl, zsp); cut += c_; WIN.append((fr, u, T_P, hw, zsl, zsp, kind, dg))
# opěrné pilíře
BPROF = [(0.0, -0.35), (1.45, -0.35), (1.45, 2.2), (1.2, 2.5), (1.2, 4.6), (0.95, 4.9), (0.95, 6.4), (0.45, 7.35), (0.0, 7.55)]
BUT = []
pts_but = [(Vector((*ring[i], 0)), None) for i in range(n_) if ring[i][0] > 11.5]
pts_but.append((Vector((9.4, -3.05, 0)), Vector((0, -1, 0))))
for (pv, dirv) in pts_but:
    if dirv is None:
        dirv = Vector((pv.x - APC, pv.y, 0)).normalized()
        if abs(pv.y) > 2.9: dirv = (dirv + Vector((0, math.copysign(1, pv.y), 0))).normalized()
    side = Vector((-dirv.y, dirv.x, 0))
    broken = pv.y < -2.0 and pv.x > 12.0
    prof_ = [(d, (min(z, 4.2 + 0.25 * d) if broken else z)) for (d, z) in BPROF]
    pg = Polygon(prof_).buffer(0)
    if broken:
        pg = pg.intersection(ragged_top(-0.1, 1.6, lambda u: 4.3 + 0.3 * u, step=0.16, q=0.1, jit=0.08)).buffer(0)
    o = extrude2d("bt", pg, lambda d, z, w, pv=pv, dirv=dirv, side=side: pv + dirv * d + Vector((0, 0, z)) + side * w, -0.42, 0.42)
    P_parts.append(o); BUT.append((pv, dirv, side, broken))
# sakristie
sak = solid_box((SX0, SY0, -0.35), (SX1, SY1, 4.55))
P_parts.append(sak)
cut.append(solid_box((SX0 + T_S, SY0 + 0.15, ZF_P), (SX1 - T_S, SY1 - T_S, 2.65)))
cut.append(extrude2d("sv", arch_poly(1.05, 2.0, 2.6, r_k=1.25), lambda u, z, d: Vector((7.8 + u, d, z)), SY0 + 0.15, SY1 - T_S))
for k in range(9):                                   # rozpadlá koruna sakristie
    x = random.uniform(SX0 - 0.2, SX1); y = random.choice((SY0 + 0.3, SY1, random.uniform(SY0, SY1)))
    cut.append(solid_box((x - random.uniform(0.3, 0.8), y - 0.6, random.uniform(3.8, 4.3)), (x + random.uniform(0.3, 0.8), y + 0.6, 5.0)))
cut.append(extrude2d("sd", arch_poly(0.5, -0.1, 2.25), lambda u, z, d: Vector((8.0 + u, d, z)), 2.3, 3.7))
frSE = Fr((SX1 - T_S / 2, SY0), (SX1 - T_S / 2, SY1), -1)
c_, _ = window_cutters(frSE, 4.75 - SY0, T_S, 0.07, 1.5, 2.1, frame=0.05, splay_o=0.02, splay_i=0.38, sill_i=0.35, zspr_i=0.2, depth_g=0.15); cut += c_
cut.append(solid_box((7.5, SY1 - T_S - 0.33, 1.2), (8.1, SY1 - T_S + 0.02, 1.85)))           # výklenek-almara
# sanktuář, sedile, oltář
cut.append(solid_box((10.3, 2.6 - 0.05, 1.35), (10.9, 3.0, 2.15)))
cut.append(solid_box((7.05, -3.0, 0.82), (8.35, -2.55, 2.25)))
P_parts.append(solid_box((12.15, -0.85, 0.0), (13.15, 0.85, 1.22)))
PRES = cut_join(P_parts, cut)
pres_keep = lambda P: np.clip(0.55 + 0.4 * ((P[:, 1] > 3.3) & (P[:, 0] < 9.7)) - 0.4 * ((P[:, 1] < 0) & (P[:, 0] < 9.4)), 0, 1)
pres = zdivo(PRES, "Kostel_Presbytar", make_cls(pres_keep), CL_ZED, col_zed(0.45), 0.125, voxel=0.05,
             drop_fn=lambda c, n: n.z < -0.9 and c.z < -0.3)
print("presbytář hotový", len(pres.data.polygons))


# ================================================================= KLENBA PRESBYTÁŘE
print("klenba…")
BAY1 = [(6.0, -2.6), (9.4, -2.6), (9.4, 2.6), (6.0, 2.6)]; K1 = (7.7, 0.0)
BAY2 = [(9.4, -2.6), AP[0], AP[1], AP[2], AP[3], (9.4, 2.6)]; K2 = (APC, 0.0)
HK = ZKV - Z0V
def Hw_of(a, b):
    hwid = (Vector(b) - Vector(a)).length / 2
    return min(HK - 0.12, hwid * 1.342 * 0.95)
def vpt(key, a, b, s_, t_):
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); hw2 = ((b[0] - a[0]) / 2, (b[1] - a[1]) / 2)
    x = key[0] + s_ * (m[0] - key[0]) + s_ * t_ * hw2[0]; y = key[1] + s_ * (m[1] - key[1]) + s_ * t_ * hw2[1]
    Zr = Z0V + HK * prof(s_); Rr = ZKV + (Z0V + Hw_of(a, b) - ZKV) * s_ * s_
    return Vector((x, y, Zr + (Rr - Zr) * prof(t_)))
def cell_solid(key, a, b, s_lo, s_hi, ns=18, nt=14, thk=0.30):
    """kus klenebního pole mezi s_lo(t)..s_hi(t); uzavřené těleso (spodní líc + horní + boky)"""
    V = []; Fc = []
    def idx(i, j, top): return (i * (nt + 1) + j) * 2 + top
    for i in range(ns + 1):
        for j in range(nt + 1):
            t_ = -1 + 2 * j / nt; s0, s1 = s_lo(t_), s_hi(t_); s_ = s0 + (s1 - s0) * i / ns
            p = vpt(key, a, b, s_, t_)
            V.append(p); V.append(p + Vector((0, 0, thk + 0.25 * s_ * s_)))
    for i in range(ns):
        for j in range(nt):
            q = [idx(i, j, 0), idx(i + 1, j, 0), idx(i + 1, j + 1, 0), idx(i, j + 1, 0)]
            Fc.append(tuple(q)); Fc.append(tuple(idx(*divmod(k // 2, nt + 1), 1) for k in q[::-1]))
    def side(seq):
        for k in range(len(seq) - 1):
            (i0, j0), (i1, j1) = seq[k], seq[k + 1]
            Fc.append((idx(i0, j0, 0), idx(i1, j1, 0), idx(i1, j1, 1), idx(i0, j0, 1)))
    side([(i, 0) for i in range(ns + 1)]); side([(i, nt) for i in range(ns, -1, -1)])
    side([(ns, j) for j in range(nt + 1)]); side([(0, j) for j in range(nt, -1, -1)])
    return mesh_obj("vc", V, Fc)
def jag(base, amp, seed):
    return lambda t_: base + amp * (float(vnoise(np.array(t_ * 2.3 + seed), np.array(seed * 0.7), 4)) - 0.5) * 2
VC = []
for i in range(4):
    a, b = BAY1[i], BAY1[(i + 1) % 4]
    if i == 0:      # jižní pole: zbyl kus u svorníku a patky v rozích
        VC.append(cell_solid(K1, a, b, lambda t: 0.0, jag(0.36, 0.10, 3.1)))
    elif i == 3:    # západní pole (u vítězného oblouku): zbyl jen pás u stěny a kus u svorníku
        VC.append(cell_solid(K1, a, b, jag(0.80, 0.07, 5.3), lambda t: 1.0, ns=6))
        VC.append(cell_solid(K1, a, b, lambda t: 0.0, jag(0.30, 0.08, 7.7), ns=6))
    else:
        VC.append(cell_solid(K1, a, b, lambda t: 0.0, lambda t: 1.0))
for i in range(len(BAY2)):
    a, b = BAY2[i], BAY2[(i + 1) % len(BAY2)]
    VC.append(cell_solid(K2, a, b, lambda t: 0.0, lambda t: 1.0))
bpy.ops.object.select_all(action='DESELECT')
for o in VC: o.select_set(True)
bpy.context.view_layer.objects.active = VC[0]; bpy.ops.object.join(); KL = VC[0]
CL_KL = {1: dict(h="plaster_stone_wall_02", tile=2.3, S=0.04, mat="zdivo_in"), 2: dict(h=None, tile=1.6, mat="omitka_k"),
         3: dict(h="broken_wall", tile=2.5, S=0.07, mat="zdivo")}
def cls_kl(P, Nn):
    n1 = nzv(P[:, 0] * 0.8, P[:, 1] * 0.8, 1, 2, 4)
    c = np.where(Nn[:, 2] < -0.2, np.where(n1 > 0.30, 2, 1), np.where(Nn[:, 2] > 0.3, 3, 1))
    return c
klenba = zdivo(KL, "Kostel_Klenba", cls_kl, CL_KL, col_zed(0.3), 0.17, voxel=0.045)

# ---- žebra, svorníky, konzoly (pískovec)
SAND = Mesh("Kostel_Piskovec"); SANDM = Mesh("Kostel_PiskovecMech")
RIBP = [(-0.10, 0.07), (0.10, 0.07), (0.10, -0.07), (0.05, -0.19), (0.0, -0.23), (-0.05, -0.19), (-0.10, -0.07)]
def sweep(Ms, path, profile, key="piskovec", caps=True, uvs=0.9):
    """protažení profilu po křivce; profil (a = do strany, b = nahoru)"""
    rings = []; L = 0.0; acc = [0.0]
    for k in range(1, len(path)): L += (path[k] - path[k - 1]).length; acc.append(L)
    for k, p in enumerate(path):
        T_ = (path[min(k + 1, len(path) - 1)] - path[max(k - 1, 0)]).normalized()
        S_ = T_.cross(Vector((0, 0, 1)))
        if S_.length < 1e-4: S_ = Vector((1, 0, 0))
        S_.normalize(); Up = S_.cross(T_).normalized()
        if Up.z < 0: Up = -Up; S_ = -S_
        rings.append([p + S_ * a + Up * b for (a, b) in profile])
    n = len(profile); per = [0.0]
    for i in range(n): per.append(per[-1] + (Vector(profile[(i + 1) % n]) - Vector(profile[i])).length)
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            Ms.face([rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]],
                    [(per[i] / uvs, acc[k] / uvs), (per[i + 1] / uvs, acc[k] / uvs), (per[i + 1] / uvs, acc[k + 1] / uvs), (per[i] / uvs, acc[k + 1] / uvs)], key)
    if caps:
        for r_, sg in ((rings[0], -1), (rings[-1], 1)):
            c = sum(r_, Vector()) / n
            for i in range(n):
                j = (i + 1) % n; tri = [c, r_[i], r_[j]] if sg > 0 else [c, r_[j], r_[i]]
                Ms.face(tri, [(0.5, 0.5), (0.5 + profile[i][0], 0.5 + profile[i][1]), (0.5 + profile[j][0], 0.5 + profile[j][1])], key)
def rib(key, v, s0=0.0, s1=1.0, n=22, Ms=None):
    a, b = v, v
    path = []
    for k in range(n + 1):
        s_ = s0 + (s1 - s0) * k / n
        x = key[0] + (v[0] - key[0]) * s_; y = key[1] + (v[1] - key[1]) * s_
        path.append(Vector((x, y, Z0V + HK * prof(s_))))
    sweep(Ms or SAND, path, RIBP)
for (key, poly) in ((K1, BAY1), (K2, BAY2)):
    for v in poly:
        if key == K1 and v == (6.0, -2.6):
            rib(key, v, 0.0, 0.43); rib(key, v, 0.87, 1.0, n=5)          # zlomené žebro: visí od svorníku, pahýl v patce
        else: rib(key, v)
TR = [Vector((9.4, -2.6 + 5.2 * k / 30, Z0V + Hw_of((9.4, -2.6), (9.4, 2.6)) * prof(-1 + 2 * k / 30))) for k in range(31)]
sweep(SAND, TR, [(-0.13, 0.08), (0.13, 0.08), (0.13, -0.10), (0.07, -0.25), (-0.07, -0.25), (-0.13, -0.10)])   # pásový oblouk
def lathe(Ms, c, profile, n=12, key="piskovec", R=None, phase=0.0):
    R = R or Matrix.Identity(3); c = Vector(c)
    rings = [[c + R @ Vector((r * math.cos(phase + 2 * math.pi * k / n), r * math.sin(phase + 2 * math.pi * k / n), z)) for k in range(n)] for (r, z) in profile]
    for i in range(len(rings) - 1):
        for k in range(n):
            k2 = (k + 1) % n
            Ms.face([rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]],
                    [(k / n * 2, profile[i][1]), ((k + 1) / n * 2, profile[i][1]), ((k + 1) / n * 2, profile[i + 1][1]), (k / n * 2, profile[i + 1][1])], key)
    for (rg, sg) in ((rings[0], -1), (rings[-1], 1)):
        cc = sum(rg, Vector()) / n
        for k in range(n):
            k2 = (k + 1) % n; tri = [cc, rg[k], rg[k2]] if sg > 0 else [cc, rg[k2], rg[k]]
            Ms.face(tri, [(0.5, 0.5), (0.5 + 0.4 * math.cos(k), 0.5), (0.5, 0.5 + 0.4 * math.sin(k))], key)
for key in (K1, K2):            # svorníky s rozetou
    lathe(SAND, (key[0], key[1], ZKV), [(0.0, -0.36), (0.12, -0.35), (0.22, -0.31), (0.31, -0.26), (0.32, -0.12), (0.30, 0.04), (0.0, 0.05)], n=16)
    for k in range(6):
        a_ = k * math.pi / 3
        lathe(SAND, (key[0] + 0.17 * math.cos(a_), key[1] + 0.17 * math.sin(a_), ZKV - 0.33), [(0.0, -0.05), (0.06, -0.035), (0.075, 0.0), (0.0, 0.01)], n=6)
def console(v, inward):
    """konzola pod patkou žeber: deska + obrácený jehlan s maskou"""
    c = Vector((v[0], v[1], Z0V)) + inward * 0.10
    R = Matrix.Rotation(math.atan2(inward.y, inward.x) + math.pi / 4, 3, 'Z')
    lathe(SAND, c, [(0.0, -0.72), (0.05, -0.70), (0.13, -0.52), (0.21, -0.30), (0.25, -0.16), (0.30, -0.13), (0.30, -0.02), (0.0, -0.01)], n=4, R=R)
for poly, key in ((BAY1, K1), (BAY2, K2)):
    for v in poly:
        if v[0] < 6.05: continue
        inward = (Vector((key[0], key[1], 0)) - Vector((v[0], v[1], 0))).normalized()
        console(v, inward)
console((6.0, 2.6), Vector((1, -1, 0)).normalized()); console((6.0, -2.6), Vector((1, 1, 0)).normalized())


# ---- kružby, rámy oken, portál, vítězný oblouk (pískovec)
print("kružby…")
def obj_to_mesh(o, Ms, key, uvs=0.8):
    """objekt (bez UV) -> plochy do Mesh s krabicovou projekcí UV"""
    if o is None: return
    me = o.data; mw = o.matrix_world; ou, ov = random.random() * 3, random.random() * 3
    for p in me.polygons:
        pts = [mw @ me.vertices[i].co for i in p.vertices]; n = (mw.to_3x3() @ p.normal)
        ax = max(range(3), key=lambda i: abs(n[i]))
        if ax == 0: uv = [(q.y / uvs + ou, q.z / uvs + ov) for q in pts]
        elif ax == 1: uv = [(q.x / uvs + ou, q.z / uvs + ov) for q in pts]
        else: uv = [(q.x / uvs + ou, q.y / uvs + ov) for q in pts]
        Ms.face(pts, uv, key)
    bpy.data.objects.remove(o, do_unlink=True)
def chamfer_extrude(poly, Pf, d0, d1, ch=0.03, Ms=None, key="piskovec"):
    """kámen se sraženými hranami: tři vrstvy, krajní zúžené"""
    Ms = Ms or SAND
    inner = poly.buffer(-ch, join_style=2)
    obj_to_mesh(extrude2d("ce", poly, Pf, d0 + ch, d1 - ch), Ms, key)
    if not inner.is_empty:
        obj_to_mesh(extrude2d("ce", inner, Pf, d0, d0 + ch + 0.002), Ms, key)
        obj_to_mesh(extrude2d("ce", inner, Pf, d1 - ch - 0.002, d1), Ms, key)
def survive_below(fn, u0=-3, u1=3):
    pts = [(u0, -1)] + [(u, fn(u)) for u in np.linspace(u0, u1, 40)] + [(u1, -1)]
    return Polygon(pts).buffer(0)
for (fr, uc, t, hw, zs, zp, kind, dg) in WIN + VWIN:
    Pf = lambda u, z, d, fr=fr, uc=uc: fr.P(uc + u, z, d)
    O = arch_poly(hw, zs, zp); A = arch_apex(hw, zp)
    band = arch_poly(hw + 0.14, zs - 0.14, zp).difference(O)
    m = 0.11; lw = (2 * hw - m) / 4
    L1 = affinity.translate(arch_poly(lw, zs - 0.2, zp), -(m / 2 + lw)); L2 = affinity.translate(arch_poly(lw, zs - 0.2, zp), m / 2 + lw)
    al = arch_apex(lw, zp); rc = (A - al) * 0.40; zc = al + rc + 0.03
    tre = unary_union([Point(0.0 + rc * 0.42 * math.cos(math.radians(a_)), zc + rc * 0.42 * math.sin(math.radians(a_))).buffer(rc * 0.43, 24) for a_ in (90, 210, 330)])
    tracery2 = O.difference(unary_union([L1, L2, tre]))
    lw1 = hw - 0.07; r1 = lw1 * 0.55
    head = unary_union([sbox(-lw1, zs - 0.2, lw1, zp + 0.05), Point(0, zp + 0.05 + r1 * 0.9).buffer(r1 * 0.95, 24),
                        Point(-lw1 + r1 * 0.8, zp + 0.05).buffer(r1 * 0.8, 24), Point(lw1 - r1 * 0.8, zp + 0.05).buffer(r1 * 0.8, 24)]).intersection(arch_poly(hw - 0.07, zs - 0.3, zp))
    tracery1 = O.difference(head)
    if kind == "kruzba2":
        st, bd = tracery2, band
    elif kind == "trojlist":
        st, bd = tracery1, band
    elif kind == "rozbite":
        cutl = survive_below(lambda u: zs + 0.55 + 0.25 * math.sin(u * 7))
        st = tracery2.intersection(cutl)
        bd = band.intersection(survive_below(lambda u: zp - 0.4 + 0.9 * (u > 0) + 0.2 * math.sin(u * 9)))
    elif kind == "pahyl2":
        st = tracery2.intersection(survive_below(lambda u: zs + 0.95 + 0.2 * math.sin(u * 8)))
        bd = band.intersection(survive_below(lambda u: zp + 0.2 - 0.6 * (u > 0.2)))
    elif kind == "ramek":
        st = Polygon(); bd = arch_poly(hw + 0.10, zs - 0.12, zp).difference(O)
        bd = bd.intersection(survive_below(lambda u, fr=fr, uc=uc: ztop_vez(fr.P(uc + u, 0).x, fr.P(uc + u, 0).y) - 0.35))
    elif kind == "dvere":
        st = Polygon(); bd = arch_poly(hw + 0.13, 0.0, zp).difference(arch_poly(hw, -0.2, zp))
    else:   # "pahyl": jen část levého ostění
        st = Polygon()
        bd = band.intersection(sbox(-3, -1, -hw + 0.02, zp - 0.2))
    chamfer_extrude(bd.buffer(0), Pf, dg - 0.15, dg + 0.15, ch=0.035)
    if not st.is_empty: chamfer_extrude(st.buffer(0), Pf, dg - 0.08, dg + 0.08, ch=0.025)
    WIN_FR = None
# portál
for o in PORTAL_OBJS: obj_to_mesh(o, SAND, "piskovec")
# vítězný oblouk: pískovcový pás přes celou tloušťku se sraženou hranou
chamfer_extrude(TA_BAND, lambda u, z, d: frE.P(NY + u, z, d), -T_N / 2, T_N / 2, ch=0.06)
# opěráky: pískovcové stříšky na odskocích
for (pv, dirv, side, broken) in BUT:
    pr = BPROF
    for k in range(1, len(pr) - 1):
        (d0, z0), (d1, z1) = pr[k], pr[k + 1]
        if z1 <= z0 + 0.05 or abs(d1 - d0) < 0.05: continue
        if broken and z1 > 4.3: continue
        (d0, z0), (d1, z1) = pr[k], pr[k + 1]
        cap = Polygon([(d0 + 0.05, z0 - 0.07), (d0 + 0.05, z0 + 0.03), (d1, z1 + 0.03), (d1 - 0.02, z1 - 0.14), (d0 - 0.08, z0 - 0.14)]).buffer(0)
        obj_to_mesh(extrude2d("cap", cap, lambda d, z, w, pv=pv, dirv=dirv, side=side: pv + dirv * d + Vector((0, 0, z)) + side * w, -0.435, 0.435),
                    SANDM if random.random() < 0.5 else SAND, "piskovec_m" if random.random() < 0.6 else "piskovec")
# sanktuář s vimperkem a mřížkou
NIX = 10.6
pf = lambda u, z, d: Vector((NIX + u, 2.6 - d, z))
frame = unary_union([sbox(-0.46, 1.18, 0.46, 2.3), Polygon([(-0.52, 2.3), (0.52, 2.3), (0.0, 3.05)])]).difference(sbox(-0.30, 1.35, 0.30, 2.15))
chamfer_extrude(frame, pf, -0.02, 0.11, ch=0.025)
chamfer_extrude(Polygon([(-0.34, 2.36), (0.34, 2.36), (0.0, 2.88)]).buffer(-0.07), pf, 0.09, 0.13, ch=0.01)
lathe(SAND, (NIX, 2.55, 3.05), [(0.0, 0.0), (0.05, 0.02), (0.06, 0.12), (0.03, 0.2), (0.0, 0.24)], n=6)
GR = Mesh("Kostel_Mrize")
for k in range(4): box(GR, (NIX - 0.21 + k * 0.14, 2.58, 1.75), (0.018, 0.018, 0.82), Matrix.Identity(3), "zelezo_r", uvs=0.5)
for z in (1.52, 1.98): box(GR, (NIX, 2.585, z), (0.62, 0.012, 0.03), Matrix.Identity(3), "zelezo_r", uvs=0.5)
# dveře do sakristie: pískovcové ostění
chamfer_extrude(arch_poly(0.62, 0.36, 2.25).difference(arch_poly(0.5, 0.2, 2.25)), lambda u, z, d: Vector((8.0 + u, d, z)), 2.48, 2.70, ch=0.03)

piskovec = SAND.build(smooth_angle=35); piskovec_m = SANDM.build(smooth_angle=35); mrize = GR.build()

# ================================================================= PODLAHY, SCHODY, OLTÁŘ
print("podlahy…")
def grid_surface(name, x0, x1, y0, y1, res, zf, keep=None):
    nx = max(2, int((x1 - x0) / res)); ny = max(2, int((y1 - y0) / res))
    V = []; Fc = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny; V.append((x, y, zf(x, y)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            q = (a, a + 1, a + nx + 2, a + nx + 1)
            if keep is not None and not keep(q, V): continue
            Fc.append(q)
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], Fc)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); return o
FLOOR = unary_union([sbox(NX0 + T_N, -NY + T_N, 4.31, NY - T_N), sbox(VX0 + T_V, -VY + T_V, NX0 + T_N, VY - T_V), sbox(-4.4, -NY - 0.2, -2.0, -NY + T_N + 0.05)])
FLOOR_P = shapely.prepared.prep(FLOOR.buffer(0.12))
def keep_floor(q, V):
    c = [sum(V[k][i] for k in q) / 4 for i in range(2)]
    return FLOOR_P.contains(Point(c[0], c[1]))
fl = grid_surface("fl", -9.75, 4.4, -4.65, 3.45, 0.07, lambda x, y: 0.02 + 0.03 * float(vnoise(np.array(x * 0.8), np.array(y * 0.8), 2)), keep_floor)
def cls_fl(P, Nn):
    n1 = nzv(P[:, 0] * 0.45, P[:, 1] * 0.45, 1, 3, 4); n2 = nzv(P[:, 0] * 2.0, P[:, 1] * 2.0, 1, 4, 2)
    pav = (n1 * 0.85 + n2 * 0.15) > (0.56 + 0.12 * (np.abs(P[:, 1]) > 2.3) + 0.3 * (P[:, 0] < NX0))
    return np.where(pav, 0, 1)
CL_FL = {0: dict(h="cobblestone_large_01", tile=2.2, S=0.045, mat="dlazba"), 1: dict(h=None, tile=1.8, mat="hlina_k")}
def col_fl(P, Nn, h, c):
    n1 = nzv(P[:, 0] * 0.9, P[:, 1] * 0.9, 1, 6, 3)
    g = np.where(c == 0, (0.55 + 0.45 * h) * (0.75 + 0.25 * n1), 0.8 + 0.25 * n1)
    m = np.clip((n1 - 0.55) * 3, 0, 1) * (c == 0)
    return np.stack([g * (1 - 0.35 * m), g * (1 - 0.1 * m), g * (1 - 0.5 * m)], 1)
podl = zdivo(fl, "Kostel_Podlaha_Lod", cls_fl, CL_FL, col_fl, 0.30, remesh=False)
# presbytář: hliněný podsyp a pískovcové desky
PF = P_IN.intersection(sbox(6.0, -5, 20, 5)).union(sbox(4.95, -2.1, 6.05, 2.1)).buffer(0)
FLP = Mesh("Kostel_Podlaha_Presbytar")
for t in _tri_rings(PF):
    FLP.face([(x, y, ZF_P - 0.06) for (x, y) in t], [(x / 1.6, y / 1.6) for (x, y) in t[:3]], "hlina_k") if Polygon(t).exterior.is_ccw else \
        FLP.face([(x, y, ZF_P - 0.06) for (x, y) in t[::-1]], [(x / 1.6, y / 1.6) for (x, y) in t[::-1]], "hlina_k")
PFi = shapely.prepared.prep(PF.buffer(-0.04))
ALT = sbox(12.1, -0.9, 13.2, 0.9)
row = 0; x = 5.0
while x < 13.8:
    lx = random.uniform(0.55, 0.68); y = -2.62 + (0.3 if row % 2 else 0.0) - 0.6
    while y < 2.62:
        ly = random.uniform(0.52, 0.66)
        cx, cy = x + lx / 2, y + ly / 2
        if PFi.contains(sbox(x, y, x + lx, y + ly)) and not ALT.intersects(sbox(x, y, x + lx, y + ly)):
            r = random.random()
            if (cx < 8.2 and cy < -0.6 and r < 0.55) or r < 0.16: pass                 # chybí (vylámané)
            else:
                k_ = "piskovec_m" if random.random() < 0.3 else "piskovec"
                R = Matrix.Rotation(random.uniform(-0.03, 0.03), 3, 'Z')
                if random.random() < 0.12: R = R @ Matrix.Rotation(random.uniform(-0.09, 0.09), 3, 'X') @ Matrix.Rotation(random.uniform(-0.08, 0.08), 3, 'Y')
                if random.random() < 0.10:      # prasklá
                    box(FLP, (cx - lx * 0.25, cy, ZF_P - 0.035), (lx * 0.48 - 0.02, ly - 0.018, 0.07), R, k_, uvs=0.9)
                    box(FLP, (cx + lx * 0.26, cy, ZF_P - 0.045), (lx * 0.48 - 0.02, ly - 0.018, 0.07), R @ Matrix.Rotation(0.05, 3, 'Y'), k_, uvs=0.9)
                else:
                    box(FLP, (cx, cy, ZF_P - 0.035 + random.uniform(-0.008, 0.004)), (lx - 0.018, ly - 0.018, 0.07), R, k_, uvs=0.9)
        y += ly
    x += lx; row += 1
# schody k vítěznému oblouku
y = -2.05
while y < 2.05:
    ly = min(random.uniform(0.6, 1.05), 2.05 - y)
    for (xa, xb, zt, miss) in ((4.30, 4.66, 0.18, 0.9 < y < 1.9), (4.64, 5.02, ZF_P, False)):
        if miss: continue
        R = Matrix.Rotation(random.uniform(-0.025, 0.025), 3, 'Z') @ Matrix.Rotation(random.uniform(-0.015, 0.015), 3, 'X')
        box(FLP, ((xa + xb) / 2 + random.uniform(-0.02, 0.02), y + ly / 2, zt / 2), (xb - xa - 0.01, ly - 0.015, zt), R, "piskovec_m" if random.random() < 0.35 else "piskovec", uvs=0.9)
    y += ly
box(FLP, (3.6, 1.55, 0.13), (0.38, 0.92, 0.18), Matrix.Rotation(0.6, 3, 'Z') @ Matrix.Rotation(0.25, 3, 'Y'), "piskovec_m", uvs=0.9)   # vyvalený stupeň
# menza oltáře: rozlomená deska, kus sjel dolů
box(FLP, (12.66, -0.32, 1.32), (1.22, 1.34, 0.19), Matrix.Rotation(0.03, 3, 'Z') @ Matrix.Rotation(-0.02, 3, 'X'), "piskovec", uvs=0.9)
box(FLP, (12.62, 0.98, 0.86), (1.18, 0.78, 0.19), Matrix.Rotation(-0.62, 3, 'X') @ Matrix.Rotation(0.1, 3, 'Z'), "piskovec", uvs=0.9)
podl_p = FLP.build(smooth_angle=30)

# ---- náhrobní desky, křtitelnice
KAM = Mesh("Kostel_Kameny")
def tomb(c, yaw, cracked=False, sink=0.0, key="piskovec"):
    R = Matrix.Rotation(yaw, 3, 'Z')
    pf = lambda u, v, d: Vector(c) + R @ Vector((u, v, d))
    slab = sbox(-0.41, -0.97, 0.41, 0.97)
    cross = unary_union([sbox(-0.05, -0.55, 0.05, 0.72), sbox(-0.28, 0.33, 0.28, 0.43), sbox(-0.17, -0.74, 0.17, -0.62), sbox(-0.11, -0.62, 0.11, -0.55)])
    if cracked:
        cl = Polygon([(-1, -1.2), (1, -1.2), (1, 0.05), (-1, -0.25)])
        for k, part in enumerate((slab.intersection(cl), slab.difference(cl))):
            Rk = Matrix.Rotation(0.035 * (1 if k else -1), 3, 'X'); off = Vector((0.0, 0.015 * (1 if k else -1), 0.0))
            pfk = lambda u, v, d, Rk=Rk, off=off: Vector(c) + R @ (Rk @ Vector((u, v, d)) + off)
            chamfer_extrude(part, pfk, -0.14 - sink, 0.0 - sink, ch=0.02, Ms=KAM, key=key)
            cp = cross.intersection(cl if k == 0 else slab.difference(cl))
            if not cp.is_empty: chamfer_extrude(cp.buffer(0), pfk, -0.01 - sink, 0.035 - sink, ch=0.012, Ms=KAM, key=key)
    else:
        chamfer_extrude(slab, pf, -0.14 - sink, 0.0 - sink, ch=0.02, Ms=KAM, key=key)
        chamfer_extrude(cross, pf, -0.01 - sink, 0.035 - sink, ch=0.012, Ms=KAM, key=key)
tomb((2.65, -1.1, 0.07), 0.04, key="piskovec_m")
tomb((2.75, 1.15, 0.07), -0.06, cracked=True)
tomb((10.15, -0.75, ZF_P + 0.02), 1.57 + 0.03)
FONT = [(0.0, 0.0), (0.37, 0.0), (0.37, 0.16), (0.20, 0.22), (0.18, 0.66), (0.42, 0.75), (0.47, 0.84), (0.47, 1.18), (0.41, 1.23), (0.36, 1.23), (0.33, 0.93), (0.0, 0.91)]
lathe(KAM, (-1.45, 1.05, 0.02), FONT[:4] + [(0.18, 0.30), (0.0, 0.30)], n=8)                      # pahýl patky
Rf = Matrix.Rotation(0.5, 3, 'Z') @ Matrix.Rotation(math.radians(84), 3, 'X')
lathe(KAM, Vector((-2.45, 0.35, 0.47)) + Rf @ Vector((0, 0, -0.28)), [(0.0, 0.3), (0.18, 0.3)] + FONT[4:], n=8, R=Rf)   # převrácená mísa

# ---- sutiny
print("sutiny…")
HEAPS = [("SeverVnitrni", -0.6, 2.75, 4.6, 1.0, 0.85, 0.02, 0.0),
         ("SeverVenku", 0.2, 5.7, 6.2, 1.7, 1.15, 0.0, 0.05),
         ("Klenba", 7.2, -1.55, 1.45, 1.05, 0.75, ZF_P - 0.04, 0.4),
         ("Vez", -8.15, -0.3, 1.3, 0.9, 1.05, 0.02, 0.3),
         ("JihPresbytar", 7.6, -4.55, 2.0, 0.95, 0.65, 0.0, 0.0),
         ("Stit", 6.2, 4.6, 1.3, 1.0, 0.75, 0.0, 0.6),
         ("Zaver", 14.6, 1.6, 1.3, 1.1, 0.5, 0.0, 1.0)]
def heap_h(hp, x, y):
    _, cx, cy, rx, ry, H, zb, rot = hp
    ca, sa = math.cos(rot), math.sin(rot)
    u = ((x - cx) * ca + (y - cy) * sa) / rx; v = (-(x - cx) * sa + (y - cy) * ca) / ry
    d = math.sqrt(u * u + v * v) * (0.85 + 0.3 * float(vnoise(np.array(x * 1.7 + cx), np.array(y * 1.7 + cy), 5)))
    if d >= 1.0: return zb
    return zb + H * (1 - d * d) ** 1.6 * (0.8 + 0.4 * float(vnoise(np.array(x * 0.9), np.array(y * 0.9 + 3), 6)))
SUT = []
for hp in HEAPS:
    nm, cx, cy, rx, ry, H, zb, rot = hp
    R_ = max(rx, ry) * 1.25
    o = grid_surface("h", cx - R_, cx + R_, cy - R_, cy + R_, VX(0.065), lambda x, y, hp=hp: heap_h(hp, x, y) - 0.03,
                     lambda q, V, hp=hp: max(V[k][2] for k in q) > hp[6] - 0.02)
    SUT.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in SUT: o.select_set(True)
bpy.context.view_layer.objects.active = SUT[0]; bpy.ops.object.join()
CL_SUT = {0: dict(h="cobblestone_large_01", tile=1.4, S=0.11, mat="sut")}
def col_sut(P, Nn, h, c):
    n1 = nzv(P[:, 0] * 1.1, P[:, 1] * 1.1, 1, 6, 3); n2 = nzv(P[:, 0] * 3.0, P[:, 1] * 3.0, 1, 2, 2)
    g = (0.45 + 0.55 * h) * (0.62 + 0.25 * n1)
    m = np.clip((n2 - 0.5) * 2.5, 0, 1) * np.clip(h * 1.4 - 0.2, 0, 1)
    return np.stack([g * (1 - 0.45 * m), g * (1 - 0.15 * m), g * (1 - 0.6 * m)], 1)
sut = zdivo(SUT[0], "Kostel_Sut", lambda P, N: np.zeros(len(P), np.int32), CL_SUT, col_sut, 0.28, remesh=False)
for hp in HEAPS:                                                     # volné kameny na kupách
    nm, cx, cy, rx, ry, H, zb, rot = hp
    for k in range(int(rx * ry * 9)):
        a_ = random.uniform(0, 6.283); r_ = math.sqrt(random.random()) * 0.95
        x = cx + rx * r_ * math.cos(a_); y = cy + ry * r_ * math.sin(a_)
        z = heap_h(hp, x, y)
        s_ = random.uniform(0.12, 0.30)
        U_ = Vector((math.cos(a_ * 3), math.sin(a_ * 3), random.uniform(-0.3, 0.3))).normalized()
        N_ = Vector((0, 0, 1)); V_ = N_.cross(U_).normalized(); N_ = U_.cross(V_).normalized()
        stone(KAM, (x, y, z - 0.03), U_, V_, -N_ if False else N_, s_ * random.uniform(1.0, 1.6), s_, s_ * 0.8,
              random.choice(("kamen_r", "kamen_r", "kamen_rm")), detail=True, bulge=0.02, tilt=0.5)
# spadlé kusy žeber, kvádry a kružeb
def rib_piece(c, yaw, ln, tilt=0.0, curv=0.25):
    R = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(tilt, 3, 'X')
    path = [Vector(c) + R @ Vector((ln * (k / 6 - 0.5), 0, curv * (1 - (2 * k / 6 - 1) ** 2) * ln * 0.3)) for k in range(7)]
    Rp = [(a, -b) for (a, b) in RIBP]                    # leží na boku
    sweep(KAM, path, [(b + 0.08, a) for (a, b) in RIBP], key="piskovec")
for (c, yaw, ln) in [((6.7, -1.9, ZF_P + 0.45), 0.4, 0.95), ((7.6, -1.0, ZF_P + 0.5), 1.9, 0.7), ((5.9, -1.3, ZF_P + 0.15), 2.7, 0.8),
                     ((3.6, -0.7, 0.12), 1.2, 0.85), ((8.1, -2.0, ZF_P + 0.25), -0.5, 0.6)]:
    rib_piece(c, yaw, ln, tilt=random.uniform(-0.15, 0.15))
for (c, yaw, sz) in [((5.3, -3.0, 0.16), 0.3, (0.55, 0.32, 0.30)), ((2.8, -2.6, 0.13), 1.1, (0.42, 0.3, 0.25)), ((-2.0, -2.8, 0.13), 0.7, (0.5, 0.28, 0.26)),
                     ((9.0, -4.3, 0.55), 0.2, (0.48, 0.3, 0.28)), ((14.3, 1.3, 0.4), 1.4, (0.5, 0.3, 0.3)), ((1.8, 2.3, 0.7), 2.2, (0.45, 0.32, 0.28))]:
    box(KAM, c, sz, Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(random.uniform(-0.3, 0.3), 3, 'X'), random.choice(("piskovec", "piskovec_m")), uvs=0.9)
for (c, yaw) in [((3.1, -4.9, 0.08), 0.5), ((13.9, -2.7, 0.08), 2.0)]:          # úlomky kružby venku pod okny
    pce = arch_poly(0.25, 0.0, 0.2).difference(arch_poly(0.17, -0.1, 0.2))
    chamfer_extrude(pce, lambda u, v, d, c=c, yaw=yaw: Vector(c) + Matrix.Rotation(yaw, 3, 'Z') @ Vector((u, v - 0.3, d)), -0.08, 0.08, ch=0.02, Ms=KAM)
kameny = KAM.build(smooth_angle=40)

# ================================================================= OHOŘELÉ TRÁMY, VRATA PORTÁLU
TRM = Mesh("Kostel_Tramy")
def burnt_beam(p0, p1, w, h, broken=(False, True)):
    """ohořelý trám: uhlíková kůra, zlomený konec roztřepený do třísek"""
    X, Y, Z, Ln = T(TRM, p0, p1, w, h, key="tram_oh", caps=(not broken[0], not broken[1]), capkey="uhel_cel", wane=0.0, bow=0.02, jitter=0.012, ch=0.045)
    for k, (on, P, sg) in enumerate(((broken[0], Vector(p0), -1), (broken[1], Vector(p1), 1))):
        if not on: continue
        # rozlomená plocha: nerovná, šikmo
        q = [P + Y * a * w / 2 + Z * b * h / 2 + X * sg * random.uniform(-0.04, 0.05) for (a, b) in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        F(TRM, q if sg > 0 else q[::-1], [(0, 0), (0.3, 0), (0.3, 0.3), (0, 0.3)], "uhel_cel", X * sg)
        for j in range(random.randint(12, 18)):         # třísky
            a = random.uniform(-0.8, 0.8); b = random.uniform(-0.8, 0.8)
            base = P + Y * a * w / 2 + Z * b * h / 2
            ln = random.uniform(0.04, 0.20) * (1.3 if abs(a) < 0.5 else 0.8)
            tip = base + X * sg * ln + Y * random.uniform(-0.03, 0.03) + Z * random.uniform(-0.03, 0.03)
            cone(TRM, base - X * sg * 0.02, tip, random.uniform(0.010, 0.026), 0.002, "uhel_cel" if random.random() < 0.5 else "tram_oh", seg=4)
burnt_beam((0.6, -2.95, 0.14), (3.9, -2.45, 0.55), 0.24, 0.28, broken=(True, True))
burnt_beam((0.9, -1.6, 0.13), (4.0, 2.2, 0.62), 0.26, 0.26, broken=(False, True))
burnt_beam((-9.6, -0.75, 5.50), (-7.0, -0.95, 0.95), 0.22, 0.24, broken=(False, True))
burnt_beam((-1.0, -3.30, 7.31), (-0.98, -2.88, 7.30), 0.22, 0.26, broken=(False, True))
burnt_beam((-6.95, 1.05, 0.12), (-4.3, 2.0, 0.55), 0.20, 0.22, broken=(True, True))
# vyvalené křídlo vrat portálu: leží v lodi, prkna zčásti chybí
vc = Vector((-3.0, -2.15, 0.06)); R = Matrix.Rotation(0.35, 3, 'Z') @ Matrix.Rotation(-0.06, 3, 'Y')
for k in range(5):
    if k == 3: continue
    ln = 2.6 if k != 4 else 1.7
    board(TRM, vc + R @ Vector((-0.4 + k * 0.2, -(2.6 - ln) / 2, 0)), R @ Vector((1, 0, 0)), R @ Vector((0, 1, 0)), R @ Vector((0, 0, 1)), 0.195, ln, 0.05, "tram_shn")
for yy in (-0.9, 0.85):
    box(TRM, vc + R @ Vector((0.0, yy, 0.045)), (0.95, 0.12, 0.04), R, "tram_shn", uvs=0.8)
    box(TRM, vc + R @ Vector((-0.05, yy, 0.07)), (0.82, 0.05, 0.008), R, "zelezo_r", uvs=0.5)
tramy = TRM.build(smooth_angle=40)

# ================================================================= DVEŘE SAKRISTIE (počátek v pantu, visí nakřivo)
DV = Mesh("Kostel_Dvere_Sakristie")
hinge = Vector((8.0 - 0.49, 2.75, ZF_P + 0.01)); w_ = 0.97
leaf = arch_poly(0.485, 0.0, 2.25 - ZF_P - 0.01)
sag = Matrix.Rotation(math.radians(2.2), 3, 'Y')                        # prověšené: volný konec klesl
for k in range(5):
    bx = sbox(-0.485 + k * 0.194 + 0.002, -0.1, -0.485 + (k + 1) * 0.194 - 0.002, 4).intersection(leaf)
    if bx.is_empty: continue
    obj_to_mesh(extrude2d("dl", bx, lambda u, z, d: hinge + sag @ Vector((u + 0.485, d, z)), 0.0, 0.05), DV, "tram_shn")
for zz in (0.35, 1.0, 1.62):
    box(DV, hinge + sag @ Vector((0.485, -0.012, zz)), (0.9 if zz < 1.6 else 0.7, 0.012, 0.06), Matrix.Identity(3), "zelezo_r", uvs=0.5)
    box(DV, hinge + sag @ Vector((0.02, 0.02, zz)), (0.06, 0.07, 0.07), Matrix.Identity(3), "zelezo", uvs=0.5)
for k in range(8):
    a0 = 2 * math.pi * k / 8; a1 = 2 * math.pi * (k + 1) / 8; cc = hinge + sag @ Vector((0.82, -0.04, 1.05))
    cone(DV, cc + Vector((math.sin(a0) * 0.06, 0, math.cos(a0) * 0.06)), cc + Vector((math.sin(a1) * 0.06, 0, math.cos(a1) * 0.06)), 0.007, 0.007, "zelezo", seg=4)
dv = DV.build(smooth_angle=40, origin=tuple(hinge))
dv["otevreni_deg"] = 95.0; dv["otevira_se"] = "do sakristie"; DOORS.append(dv)

# ================================================================= FRESKY (obtisky na omítce)
print("fresky…")
from PIL import Image, ImageDraw, ImageFilter
def fresco_atlas(path):
    W_, H_ = 2048, 1024
    img = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); dr = ImageDraw.Draw(img)
    LIME = (218, 208, 186); RED = (150, 62, 40); OCH = (196, 150, 74); GRN = (104, 118, 88); BLK = (48, 38, 32); SKIN = (205, 165, 128)
    def saint(x0, robe, mantle, book):
        dr.rectangle([x0 + 18, 18, x0 + 494, 1006], fill=LIME + (255,))
        for k in range(3): dr.rectangle([x0 + 22 + k * 9, 22 + k * 9, x0 + 490 - k * 9, 1002 - k * 9], outline=RED + (255,), width=5)
        cx = x0 + 256
        dr.ellipse([cx - 92, 110, cx + 92, 294], fill=OCH + (255,), outline=BLK + (255,), width=5)
        dr.ellipse([cx - 52, 140, cx + 52, 266], fill=SKIN + (255,), outline=BLK + (255,), width=4)
        dr.line([cx - 22, 192, cx - 8, 192], fill=BLK + (255,), width=4); dr.line([cx + 8, 192, cx + 22, 192], fill=BLK + (255,), width=4)
        dr.line([cx, 196, cx - 4, 222], fill=BLK + (255,), width=3); dr.line([cx - 12, 238, cx + 12, 238], fill=RED + (255,), width=4)
        dr.polygon([(cx - 70, 280), (cx + 70, 280), (cx + 150, 940), (cx - 150, 940)], fill=robe + (255,), outline=BLK + (255,))
        dr.polygon([(cx - 75, 290), (cx + 20, 300), (cx - 10, 900), (cx - 160, 935)], fill=mantle + (255,), outline=BLK + (255,))
        for k in range(6):
            xx = cx - 100 + k * 40; dr.line([xx, 420 + k * 10, xx + (k - 3) * 12, 930], fill=BLK + (200,), width=4)
        if book: dr.rectangle([cx + 10, 470, cx + 92, 560], fill=RED + (255,), outline=BLK + (255,), width=4)
        else:
            dr.line([cx + 70, 330, cx + 85, 960], fill=BLK + (255,), width=10); dr.polygon([(cx + 60, 330), (cx + 110, 330), (cx + 85, 270)], fill=OCH + (255,))
        dr.ellipse([cx + 40, 500, cx + 88, 548], fill=SKIN + (255,), outline=BLK + (255,), width=3)
        dr.rectangle([x0 + 40, 940, x0 + 472, 990], fill=GRN + (255,))
    saint(0, RED, GRN, True); saint(512, (120, 100, 70), RED, False)
    def ccross(x0, y0):
        cx, cy = x0 + 256, y0 + 256
        dr.ellipse([cx - 230, cy - 230, cx + 230, cy + 230], fill=LIME + (255,))
        dr.ellipse([cx - 205, cy - 205, cx + 205, cy + 205], outline=RED + (255,), width=16)
        for a_ in range(4):
            R_ = lambda u, v: (cx + u * math.cos(a_ * math.pi / 2) - v * math.sin(a_ * math.pi / 2), cy + u * math.sin(a_ * math.pi / 2) + v * math.cos(a_ * math.pi / 2))
            dr.polygon([R_(20, -22), R_(170, -70), R_(170, 70), R_(20, 22)], fill=RED + (255,))
        dr.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=RED + (255,))
    ccross(1024, 0); ccross(1024, 512)
    dr.rectangle([1536, 0, 2048, 1024], fill=LIME + (255,))
    dr.rectangle([1556, 0, 1580, 1024], fill=RED + (255,)); dr.rectangle([2004, 0, 2028, 1024], fill=RED + (255,))
    for k in range(9):
        y0 = k * 128; dr.line([1600, y0, 1984, y0 + 64, 1600, y0 + 128], fill=RED + (255,), width=18)
        dr.ellipse([1770, y0 + 52, 1814, y0 + 76], fill=GRN + (255,))
    a = np.asarray(img, np.float32) / 255.0
    yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
    n1 = fbm(xx / 90.0, yy / 90.0, 5, 3); n2 = fbm(xx / 14.0, yy / 14.0, 3, 6)
    fade = np.clip(0.35 + 0.9 * (n1 - 0.4) + 0.25 * (n2 - 0.5), 0.15, 0.95)[..., None]
    lime = np.array(LIME, np.float32) / 255
    rgb = a[..., :3] * fade + lime * (1 - fade)
    rgb *= (0.86 + 0.14 * n2)[..., None]
    # okraje vydrolené: alfa podle šumu, uvnitř díry (opadaná omítka)
    ex = np.minimum.reduce([np.minimum(xx % 512, 511 - xx % 512) / 512.0 * 2, np.minimum(yy, H_ - 1 - yy) / H_ * 2])
    ex = np.where(xx >= 1536, np.minimum(np.minimum(xx - 1536, 2047 - xx) / 512.0 * 2, 1.0), ex)
    ex = np.where((xx >= 1024) & (xx < 1536), np.minimum(np.hypot((xx % 512) - 256, (yy % 512) - 256) * -1 / 256.0 + 1.0, 1.0) * 1.4, ex)
    al = a[..., 3] * np.clip((ex * 1.25 + (n1 - 0.5) * 1.3 + (n2 - 0.5) * 0.5) * 3.0, 0, 1)
    holes = fbm(xx / 40.0 + 7, yy / 40.0 - 3, 4, 7)
    al *= np.clip((0.66 - holes) * 9, 0, 1)
    out = np.concatenate([np.clip(rgb, 0, 1), al[..., None]], 2)
    Image.fromarray((out * 255).astype(np.uint8), "RGBA").save(path)
FPATH = os.path.join(TEX, "freska_atlas.png")
if not os.path.exists(FPATH) or os.environ.get("NOVE_TEX"): fresco_atlas(FPATH)
def alpha_mat(name, path, rough=0.9):
    m = bpy.data.materials.new(name); nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.image.pack()
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = rough
    try: m.blend_method = 'CLIP'; m.alpha_threshold = 0.5
    except Exception: pass
    try: m.surface_render_method = 'DITHERED'
    except Exception: pass
    m.use_backface_culling = False
    return m
M["freska"] = alpha_mat("M_Freska", FPATH)
FR_UV = {"A": (0.0, 0.0, 0.25, 1.0), "B": (0.25, 0.0, 0.5, 1.0), "C": (0.5, 0.5, 0.75, 1.0), "D": (0.5, 0.0, 0.75, 0.5), "E": (0.75, 0.0, 1.0, 1.0)}
FRE = Mesh("Kostel_Fresky")
for (c, U, N, w, h, reg) in DECALS:
    c = Vector(c); U = Vector(U); Z_ = Vector((0, 0, 1)); u0, v0, u1, v1 = FR_UV[reg]
    pts = [c - U * w / 2 - Z_ * h / 2, c + U * w / 2 - Z_ * h / 2, c + U * w / 2 + Z_ * h / 2, c - U * w / 2 + Z_ * h / 2]
    if reg == "E":     # pás: textura vede svisle, na stěně vodorovně
        uvs = [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]
    else: uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    F(FRE, pts, uvs, "freska", N)
fresky = FRE.build(smooth_angle=10, merge=False)

# ================================================================= BŘEČŤAN
print("břečťan…")
def ivy_atlas(path):
    from PIL import Image, ImageDraw
    S_ = 1024; img = Image.new("RGBA", (S_, S_), (0, 0, 0, 0)); dr = ImageDraw.Draw(img)
    rnd = random.Random(77)
    def leaf(cx, cy, sz, ang, col):
        pts = []
        for k in range(60):
            t = 2 * math.pi * k / 60
            r = sz * (0.55 + 0.45 * abs(math.cos(2.5 * t)) ** 0.6) * (1.0 if math.sin(t) > -0.6 else 0.75)
            pts.append((cx + r * math.cos(t + ang), cy + r * math.sin(t + ang)))
        dr.polygon(pts, fill=col + (255,))
        vc = tuple(min(255, int(c * 1.6) + 20) for c in col)
        for a_ in (-1.2, 0.0, 1.2):
            dr.line([cx, cy, cx + sz * 0.8 * math.cos(ang - math.pi / 2 + a_), cy + sz * 0.8 * math.sin(ang - math.pi / 2 + a_)], fill=vc + (255,), width=2)
    for q in range(4):
        ox, oy = (q % 2) * 512, (q // 2) * 512
        x, y = ox + 256 + rnd.uniform(-40, 40), oy + 500
        stem = [(x, y)]
        for k in range(24):
            x += rnd.uniform(-14, 14); y -= 19; stem.append((x, y))
        dr.line(stem, fill=(70, 52, 34, 255), width=6)
        for k in range(16 if q < 3 else 22):
            sx, sy = stem[rnd.randint(1, len(stem) - 1)]
            ang = rnd.uniform(0, 6.28); dd = rnd.uniform(20, 90)
            lx, ly = sx + dd * math.cos(ang), sy + dd * math.sin(ang) * 0.6
            lx = min(ox + 470, max(ox + 42, lx)); ly = min(oy + 470, max(oy + 42, ly))
            dr.line([sx, sy, lx, ly], fill=(60, 70, 30, 255), width=3)
            g = rnd.uniform(0.7, 1.15)
            col = (int(rnd.uniform(30, 46) * g), int(rnd.uniform(50, 76) * g), int(rnd.uniform(12, 22) * g))
            leaf(lx, ly, rnd.uniform(26, 44), rnd.uniform(0, 6.28), col)
    img.save(path)
IPATH = os.path.join(TEX, "brectan_atlas.png")
if not os.path.exists(IPATH) or os.environ.get("NOVE_TEX"): ivy_atlas(IPATH)
M["brectan"] = alpha_mat("M_Brectan", IPATH, rough=0.55)
IVY = Mesh("Kostel_Brectan")
def ivy_patch(fr, u0, u1, side, t, ztop, zbot, n, hang=0.6):
    """karty břečťanu na líci zdi (side = +1 vnější líc ve směru N, -1 opačný)"""
    for k in range(n):
        u = random.uniform(u0, u1); zt = ztop(u); zb = zbot(u)
        if zt - zb < 0.2: continue
        f = random.random() ** (1.0 / (1.0 + 2.5 * hang))          # víc u koruny (visí dolů)
        z = zt - (zt - zb) * (1 - f) if hang > 0 else zb + (zt - zb) * random.random() ** 1.6
        sz = random.uniform(0.32, 0.55)
        N = fr.N * side; c = fr.P(u, z, side * (t / 2 + 0.03 + random.uniform(0.0, 0.07)))
        a_ = random.uniform(-0.6, 0.6); tilt = random.uniform(0.1, 0.55)
        Uc = (fr.U * math.cos(a_) + Vector((0, 0, 1)) * math.sin(a_)); Vc = N.cross(Uc).normalized() * -1
        Vt = (Vc * math.cos(tilt) + N * math.sin(tilt)).normalized()
        q = random.randint(0, 3); u0_, v0_ = (q % 2) * 0.5, 0.5 - (q // 2) * 0.5
        pts = [c - Uc * sz / 2 - Vt * sz * 0.25, c + Uc * sz / 2 - Vt * sz * 0.25, c + Uc * sz / 2 + Vt * sz * 0.75, c - Uc * sz / 2 + Vt * sz * 0.75]
        F(IVY, pts, [(u0_, v0_), (u0_ + 0.5, v0_), (u0_ + 0.5, v0_ + 0.5), (u0_, v0_ + 0.5)], "brectan", N)
ivy_patch(frS, 9.9, 12.5, 1, T_N, lambda u: ztop_S(NX0 + u) - 0.05, lambda u: 0.1, 170, hang=0.2)
ivy_patch(frS, 10.6, 12.4, -1, T_N, lambda u: ztop_S(NX0 + u) - 0.05, lambda u: 4.5, 45, hang=1.0)
ivy_patch(frW, 0.0, 1.9, 1, T_V, lambda u: 6.5 - u * 1.2, lambda u: 0.05, 120, hang=0.0)
ivy_patch(frN, 0.1, 1.8, 1, T_N, lambda u: ztop_N(NX0 + u) - 0.05, lambda u: 1.0, 70, hang=1.2)
ivy_patch(frN, 0.1, 1.6, -1, T_N, lambda u: ztop_N(NX0 + u) - 0.05, lambda u: 2.0, 40, hang=1.2)
frNE, uNE = seg_for(outp(APM[2])); ivy_patch(frNE, 0.0, frNE.L, 1, T_P, lambda u: 4.8 - abs(u - frNE.L / 2), lambda u: 0.05, 110, hang=0.0)
brectan = IVY.build(smooth_angle=10, merge=False)

# ================================================================= HŘBITOVNÍ ZEĎ, BRÁNA, KŘÍŽE
print("hřbitovní zeď…")
HX0, HX1, HY0, HY1, HT_ = -17.0, 20.0, -12.5, 11.0, 0.62
def zt_hrb(x, y):
    z = 1.30 + 0.15 * math.sin(x * 0.8 + y * 0.5)
    for (gx, gy, r_) in ((9.0, HY1, 2.6), (HX0, -4.0, 2.0), (17.0, HY0, 1.6)):     # zřícené úseky
        d = math.hypot(x - gx, y - gy); z -= 1.25 * max(0.0, 1 - d / r_) ** 0.7
    return max(0.25, z)
H_parts = []
for (p0, p1, ns) in [((HX0, HY0), (-4.55, HY0), -1), ((-1.85, HY0), (HX1, HY0), -1), ((HX1, HY0), (HX1, HY1), -1), ((HX1, HY1), (HX0, HY1), -1), ((HX0, HY1), (HX0, HY0), -1)]:
    fr = Fr(p0, p1, ns)
    o, fr = wall("hz", p0, p1, HT_, lambda u, fr=fr: zt_hrb(fr.P(u, 0).x, fr.P(u, 0).y), e0=HT_ / 2, e1=HT_ / 2, nsign=ns, zb=-0.25, step=0.30, jit=0.10)
    H_parts.append(o)
for gx in (-4.55, -1.85):               # pilíře brány
    H_parts.append(solid_box((gx - 0.42, HY0 - 0.42, -0.25), (gx + 0.42, HY0 + 0.42, 2.25)))
HRB = cut_join(H_parts, [])
hrb = zdivo(HRB, "Kostel_HrbitovniZed", lambda P, N: np.where(N[:, 2] > 0.55, 3, 0), CL_ZED, col_zed(0.0), 0.085, voxel=0.055,
            drop_fn=lambda c, n: n.z < -0.9 and c.z < -0.2)
HK_ = Mesh("Kostel_Hrbitov")
for gx in (-4.55, -1.85):               # pískovcové stříšky pilířů
    lathe(HK_, (gx, HY0, 2.22), [(0.0, 0.0), (0.58, 0.0), (0.58, 0.08), (0.5, 0.12), (0.0, 0.62)], n=4, key="piskovec_m", phase=math.pi / 4)
def grave_cross(x, y, yaw, lean, ok):
    """dubový hrobový kříž: otesaný sloupek, příčka zapuštěná na polovinu (plát) s dřevěným kolíkem, vrch shnilý"""
    R = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(lean, 3, 'X')
    base = Vector((x, y, -0.25)); up = R @ Vector((0, 0, 1)); fw = R @ Vector((0, 1, 0)); sd = R @ Vector((1, 0, 0))
    H = 1.70 if ok else random.uniform(0.7, 0.95)
    T(HK_, base, base + up * H, 0.13, 0.11, key="dub_sedy", up=tuple(fw), w1=0.11, h1=0.09, wane=0.0, bow=0.012, ch=0.022, capkey="dub_celo", seglen=0.3)
    zc = 1.25
    if ok:
        c = base + up * zc + fw * (0.055 - 0.02)
        T(HK_, c - sd * 0.42, c + sd * 0.42, 0.065, 0.10, key="dub_sedy", up=tuple(up), w1=0.06, h1=0.095, wane=0.0, bow=0.008, ch=0.016, capkey="dub_celo", seglen=0.3)
        cone(HK_, c + fw * 0.02, c + fw * 0.05, 0.014, 0.012, "dub_celo", seg=6)
    else:      # zlomený: příčka a horní kus leží v trávě
        p = Vector((x + 0.45, y + 0.25, 0.06))
        T(HK_, p, p + Vector((0.78, 0.22, 0.01)), 0.10, 0.065, key="dub_sedy", wane=0.0, bow=0.01, capkey="dub_celo")
        T(HK_, p + Vector((0.1, -0.35, 0.0)), p + Vector((0.95, -0.55, 0.04)), 0.12, 0.10, key="dub_sedy", wane=0.0, bow=0.01, capkey="dub_celo")
for (x, y, yaw, lean, ok) in [(-9.0, -8.0, 0.1, 0.10, True), (-11.5, -5.0, -0.2, -0.22, True), (-7.5, 7.5, 0.3, 0.3, False), (12.0, -8.5, 0.0, 0.07, True),
                              (15.5, 6.5, 0.4, -0.3, True), (-13.0, 4.0, 0.2, 0.5, False)]:
    grave_cross(x, y, yaw, lean, ok)
# kamenný kříž u presbytáře (gotický, na odstupňovaném soklu)
cx_, cy_ = 10.5, -8.6
box(HK_, (cx_, cy_, 0.1), (1.1, 1.1, 0.3), Matrix.Rotation(0.05, 3, 'Z'), "piskovec_m", uvs=0.9)
box(HK_, (cx_, cy_, 0.38), (0.7, 0.7, 0.26), Matrix.Rotation(0.05, 3, 'Z'), "piskovec_m", uvs=0.9)
Rc = Matrix.Rotation(0.05, 3, 'Z') @ Matrix.Rotation(0.04, 3, 'Y')
cross = unary_union([sbox(-0.11, 0.5, 0.11, 2.55), sbox(-0.55, 1.85, 0.55, 2.07)])
for (cx0, cz0) in ((0, 2.55), (-0.55, 1.96), (0.55, 1.96)):
    cross = cross.union(Point(cx0, cz0).buffer(0.17, 16))
chamfer_extrude(cross, lambda u, z, d: Vector((cx_, cy_, 0)) + Rc @ Vector((u, d, z)), -0.09, 0.09, ch=0.025, Ms=HK_, key="piskovec_m")
hrbitov = HK_.build(smooth_angle=40)

# ================================================================= KOLIZE
print("kolize…")
def colseg(name, fr, u0, u1, t, z0, z1, dn=0.0):
    c = fr.P((u0 + u1) / 2, (z0 + z1) / 2, dn)
    ang = math.atan2(fr.U.y, fr.U.x)
    L = u1 - u0
    return colbox(name, c - Vector((L / 2, t / 2, (z1 - z0) / 2)), c + Vector((L / 2, t / 2, (z1 - z0) / 2)), rot=(0, 0, ang))
def mtop(fn, u0, u1): return float(np.mean([fn(u) for u in np.linspace(u0, u1, 12)]))
tS = lambda u: ztop_S(NX0 + u)
po = 1.16 + 0.02
colseg("LodJih1", frS, 0, UPORT - po, T_N, 0, mtop(tS, 0, UPORT - po)); colseg("LodJihNadPortalem", frS, UPORT - po, UPORT + po, T_N, 3.95, mtop(tS, UPORT - po, UPORT + po))
colseg("LodJih2", frS, UPORT + po, frS.L, T_N, 0, mtop(tS, UPORT + po, frS.L))
for k in range(4):
    u0, u1 = k * frN.L / 4, (k + 1) * frN.L / 4; colseg("LodSever%d" % k, frN, u0, u1, T_N, 0, mtop(lambda u: ztop_N(NX0 + u), u0, u1))
colseg("Stit1", frE, 0, NY - 2.3, T_N, 0, 9.0); colseg("Stit2", frE, NY + 2.3, 2 * NY, T_N, 0, 9.0); colseg("NadObloukem", frE, NY - 2.3, NY + 2.3, T_N, 7.4, 10.5)
colseg("LodZapad1", frW1, 0, frW1.L, T_N, 0, 7.7); colseg("LodZapad2", frW2, 0, frW2.L, T_N, 0, 5.0)
colseg("VezVychod1", frVE, 0, VY - 0.82, T_N, 0, 8.0); colseg("VezVychod2", frVE, VY + 0.82, 2 * VY, T_N, 0, 8.0); colseg("VezOblouk", frVE, VY - 0.82, VY + 0.82, T_N, 3.3, 8.0)
colseg("VezZapad1", frW, 0, VY - 0.70, T_V, 0, 12.0); colseg("VezZapad2", frW, VY + 0.70, 2 * VY, T_V, 0, 12.0); colseg("VezVchod", frW, VY - 0.7, VY + 0.7, T_V, 2.9, 12.0)
colseg("VezSever", V_parts[1][1], 0, V_parts[1][1].L, T_V, 0, 12.0); colseg("VezJih", V_parts[2][1], 0, V_parts[2][1].L, T_V, 0, 9.0)
for i, fr in enumerate(PFR):
    tp = mtop(lambda u, fr=fr: ztop_P(fr.P(u, 0).x, fr.P(u, 0).y), 0, fr.L)
    d0 = fr.P(0, 0); d1 = fr.P(fr.L, 0)
    if abs(d0.y - 3.05) < 0.1 and abs(d1.y - 3.05) < 0.1:              # severní zeď s dveřmi do sakristie
        ua = (Vector((7.48, 3.05, 0)) - fr.O).dot(fr.U); ub = (Vector((8.52, 3.05, 0)) - fr.O).dot(fr.U)
        lo_, hi_ = min(ua, ub), max(ua, ub)
        colseg("Presbytar%da" % i, fr, 0, lo_, T_P, 0, tp); colseg("Presbytar%db" % i, fr, hi_, fr.L, T_P, 0, tp); colseg("Presbytar%dc" % i, fr, lo_, hi_, T_P, 2.95, tp)
    else:
        colseg("Presbytar%d" % i, fr, 0, fr.L, T_P, 0, tp)
for k, (pv, dirv, side, broken) in enumerate(BUT):
    c = pv + dirv * 0.75; ang = math.atan2(dirv.y, dirv.x)
    colbox("Operak%d" % k, c - Vector((0.72, 0.42, 0)), c + Vector((0.72, 0.42, 4.2 if broken else 6.5)), rot=(0, 0, ang))
colbox("SakristieZapad", (SX0, SY0, 0), (SX0 + T_S, SY1, 4.5)); colbox("SakristieVychod", (SX1 - T_S, SY0, 0), (SX1, SY1, 4.5))
colbox("SakristieSever", (SX0, SY1 - T_S, 0), (SX1, SY1, 4.5)); colbox("SakristieKlenba", (SX0, SY0, 2.65), (SX1, SY1, 4.5))
colbox("Podlaha_Presbytar", (5.0, -2.6, -0.2), (13.8, 2.6, ZF_P)); colbox("Schod1", (4.3, -2.05, -0.2), (4.66, 2.05, 0.18))
colbox("Oltar", (12.1, -0.9, 0), (13.25, 0.9, 1.42))
for (nm, x0_, y0_, x1_, y1_, h_) in (("Nahrobek1", 2.24, -2.08, 3.06, -0.12, 0.1), ("Nahrobek2", 2.34, 0.17, 3.16, 2.13, 0.1), ("Kritelnice", -3.05, -0.2, -1.85, 0.9, 0.9)):
    colbox(nm, (x0_, y0_, 0), (x1_, y1_, h_))
for (nm, a, b) in (("Tram1", (0.6, -2.95, 0.14), (3.9, -2.45, 0.55)), ("Tram2", (0.9, -1.6, 0.13), (4.0, 2.2, 0.62)), ("TramVez", (-9.6, -0.75, 5.5), (-7.0, -0.95, 0.95))):
    a = Vector(a); b = Vector(b); c = (a + b) / 2; d = b - a
    o_ = colbox(nm, c - Vector((d.length / 2, 0.12, 0.13)), c + Vector((d.length / 2, 0.12, 0.13)))
    o_.rotation_euler = d.to_track_quat('X', 'Z').to_euler(); bpy.context.view_layer.update()
    me_ = o_.data; me_.transform(o_.matrix_basis); o_.matrix_basis = Matrix.Identity(4)
    for v in me_.vertices: v.co = (v.co - c)
    me_.transform(Matrix.Translation(c) @ d.to_track_quat('X', 'Z').to_matrix().to_4x4() @ Matrix.Translation(-c)); me_.update()
# sutiny: hrubá síť jako kolize (trimesh)
for hp in HEAPS:
    nm, cx, cy, rx, ry, H, zb, rot = hp; R_ = max(rx, ry) * 1.2
    o = grid_surface("Kostel_Kol_Sut_%s-colonly" % nm, cx - R_, cx + R_, cy - R_, cy + R_, 0.35, lambda x, y, hp=hp: heap_h(hp, x, y) - 0.05,
                     lambda q, V, hp=hp: max(V[k][2] for k in q) > hp[6] - 0.03)
    o.name = "Kostel_Kol_Sut_%s-colonly" % nm; o.hide_render = True; KOL.append(o)
# hřbitovní zeď a brána
for (p0, p1) in [((HX0, HY0), (-4.55, HY0)), ((-1.85, HY0), (HX1, HY0)), ((HX1, HY0), (HX1, HY1)), ((HX1, HY1), (HX0, HY1)), ((HX0, HY1), (HX0, HY0))]:
    fr = Fr(p0, p1, 1); colseg("HrbZed%d" % len(KOL), fr, 0, fr.L, HT_, 0, 1.4)
for gx in (-4.55, -1.85): colbox("PilirBrany%d" % len(KOL), (gx - 0.42, HY0 - 0.42, 0), (gx + 0.42, HY0 + 0.42, 2.6))
colbox("KamennyKriz", (cx_ - 0.55, cy_ - 0.55, 0), (cx_ + 0.55, cy_ + 0.55, 0.51)); colbox("KamennyKrizDrik", (cx_ - 0.12, cy_ - 0.1, 0.5), (cx_ + 0.12, cy_ + 0.1, 2.7))

# ================================================================= ZNAČKY, SKUPINY, LOD1
E = [empty("Kostel_Vstup_Portal", (-3.2, -6.0, 0.0)), empty("Kostel_Vstup_Vez", (-12.2, 0.0, 0.0)), empty("Kostel_Vstup_Brana", (-3.2, HY0 - 1.0, 0.0)),
     empty("Kostel_Oltar", (12.65, 0.0, 1.45)), empty("Kostel_Truhla_Sakristie", (8.4, 5.6, ZF_P)), empty("Kostel_Svicka_Sanktuar", (NIX, 2.78, 1.36)),
     empty("Kostel_Strom_Lod", (-1.6, 2.3, 0.35)), empty("Kostel_Strom_Vez", (-8.4, 0.6, 0.6)), empty("Kostel_Kerovi_Sever", (1.0, 6.4, 0.5)),
     empty("Kostel_Havran_Vez", (-10.3, 1.9, ztop_vez(-10.3, 1.9) + 0.05)), empty("Kostel_Havran_Stit", (5.5, -0.2, 11.75)), empty("Kostel_Havran_Klenba", (11.2, 0.0, 8.32)),
     empty("Kostel_Svetlo_Lod", (0.0, 0.0, 9.5)), empty("Kostel_Kour_Zadny", (0, 0, 0))]
bpy.data.objects.remove(E.pop(), do_unlink=True)
g_ext = bpy.data.objects.new("Kostel_Exterier_skupina", None); scene.collection.objects.link(g_ext)
g_int = bpy.data.objects.new("Kostel_Interier_skupina", None); scene.collection.objects.link(g_int)
INTER = ("Fresky", "Mrize", "Dvere", "Kameny", "Tramy", "Podlaha")
for o in list(scene.objects):
    if o.parent is not None or not o.name.startswith("Kostel_") or "skupina" in o.name or "_Kol_" in o.name: continue
    o.parent = g_int if (any(k_ in o.name for k_ in INTER) or o.type == 'EMPTY') else g_ext
LO = Mesh("LOD1_Kostel")
def lbox(lo, hi, key="kamen_r"):
    lo = Vector(lo); hi = Vector(hi); box(LO, (lo + hi) / 2, hi - lo, Matrix.Identity(3), key, uvs=2.5)
lbox((NX0, -NY, 0), (NX1, -NY + T_N, 8.0)); lbox((NX0, NY - T_N, 0), (NX1, NY, 1.5)); lbox((NX1 - T_N, -NY, 0), (NX1, NY, 9.5))
lbox((VX0, -VY, 0), (NX0 + T_N, VY, 10.5)); lbox((6.0, -3.5, 0), (13.6, 3.5, 8.6)); lbox((13.6, -2.2, 0), (14.7, 2.2, 8.4)); lbox((SX0, SY0, 0), (SX1, SY1, 4.4))
for (p0, p1) in [((HX0, HY0), (HX1, HY0)), ((HX1, HY0), (HX1, HY1)), ((HX0, HY1), (HX1, HY1)), ((HX0, HY0), (HX0, HY1))]:
    lbox((min(p0[0], p1[0]) - 0.3, min(p0[1], p1[1]) - 0.3, 0), (max(p0[0], p1[0]) + 0.3, max(p0[1], p1[1]) + 0.3, 1.3))
lod = LO.build(smooth_angle=30)

# ================================================================= NÁHLED, EXPORT, RENDER
preview_scene(trees=((-24, 18, 14), (26, 20, 12), (-26, -14, 11), (28, -6, 15), (4, 26, 13), (-12, 24, 12), (16, 26, 14)), dirt=(1 / 22, 1 / 16, -0.05, 0.0))
export_all("kostel_ruiny", [lod], active=vez)
if RENDER:
    dv.rotation_euler.z = math.radians(dv["otevreni_deg"] * 0.75)
    views = {
        "1_prichod":   (Vector((-14.0, -26.0, 2.0)), Vector((0.0, 0.0, 5.0)), 24, -0.2),
        "2_portal":    (Vector((-3.3, -9.0, 1.65)), Vector((-3.0, 0.0, 3.6)), 22, -0.1),
        "3_lod":       (Vector((-4.6, -1.8, 1.65)), Vector((8.0, 0.4, 4.6)), 18, 0.4),
        "4_presbytar": (Vector((4.4, 0.9, 1.75)), Vector((11.5, -0.4, 6.4)), 16, 0.6),
        "5_klenba":    (Vector((7.0, 1.2, 2.0)), Vector((7.6, -1.0, 8.5)), 14, 0.6),
        "6_zaver":     (Vector((26.0, -15.0, 4.0)), Vector((8.0, 0.0, 4.2)), 26, -0.2),
        "7_vez":       (Vector((-8.1, 0.2, 1.7)), Vector((-8.6, 0.5, 12.0)), 14, 0.8),
        "8_sakristie": (Vector((8.3, 0.9, 1.75)), Vector((8.0, 5.4, 1.6)), 18, 1.2),
        "9_sever":     (Vector((10.0, 22.0, 6.0)), Vector((0.0, 0.0, 3.5)), 26, -0.2),
        "w_kriz":      (Vector((-8.2, -10.0, 1.3)), Vector((-9.0, -8.0, 0.95)), 35, -0.1),
        "w_tram":      (Vector((-0.6, -0.4, 1.3)), Vector((2.3, -2.7, 0.4)), 30, 0.3),
        "w_vrata":     (Vector((-1.6, -0.3, 1.6)), Vector((-3.0, -2.15, 0.1)), 30, 0.3),
        "w_dvere":     (Vector((9.0, 1.4, 1.5)), Vector((7.9, 3.1, 1.2)), 30, 0.6),
        "t_brectan":   (Vector((2.0, -8.5, 2.5)), Vector((5.5, -4.4, 3.5)), 30, -0.1),
        "t_krtitelnice": (Vector((-3.6, -1.0, 1.6)), Vector((-1.0, 1.8, 0.4)), 24, 0.4),
    }
    if os.environ.get("PAPRSKY", "1") == "1":
        vm = bpy.data.materials.new("M_opar"); nt = vm.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
        pv_ = nt.nodes.new("ShaderNodeVolumePrincipled"); pv_.inputs["Density"].default_value = 0.035; pv_.inputs["Anisotropy"].default_value = 0.55
        nt.links.new(pv_.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
        bpy.ops.mesh.primitive_cube_add(size=1, location=(4.0, 0.0, 4.5)); vo = bpy.context.active_object; vo.name = "_opar"
        vo.scale = (19.0, 8.2, 9.0); vo.data.materials.append(vm); to_prev(vo)
        scene.cycles.volume_step_rate = 2.0
    render_views(views, PRE)
print("HOTOVO")
