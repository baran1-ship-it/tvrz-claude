# -*- coding: utf-8 -*-
"""Sdílené pomůcky pro zříceniny (vyňato z kostel_ruiny.py): zdi s rozpadlou korunou, oblouky, vytažení 2D tvarů,
zdivo z fotoskenu (voxel + posun podle výškové mapy, vektorizovaně), pískovcové detaily. exec po _spolecne/tesar/_stavba."""
import shapely
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box as sbox
from shapely.ops import unary_union
from shapely import affinity
FAST = os.environ.get("FAST") == "1"
VX = (lambda v: v * 1.6) if FAST else (lambda v: v)
_PO = np.array([PROJ_OFF[0], PROJ_OFF[1], PROJ_OFF[2]], np.float32)

def desat(c, sat=0.5, gamma=1.0, add=0.0):
    def f(a):
        a = a ** gamma; g = a.mean(2, keepdims=True)
        return ((g + (a - g) * sat) * np.array(c)) + add
    return f

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

def _hs(H, u, v):
    n = H.shape[0]; x = np.mod(u, 1.0) * n; y = (1.0 - np.mod(v, 1.0)) * n - 1e-3
    x0 = np.floor(x).astype(np.int64) % n; y0 = np.floor(y).astype(np.int64) % n; x1 = (x0 + 1) % n; y1 = (y0 + 1) % n
    fx = x - np.floor(x); fy = y - np.floor(y)
    return (H[y0, x0] * (1 - fx) + H[y0, x1] * fx) * (1 - fy) + (H[y1, x0] * (1 - fx) + H[y1, x1] * fx) * fy

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

def nzv(x, y, s=1.0, ch=3, o=3):
    return fbm(np.asarray(x, np.float32) * s, np.asarray(y, np.float32) * s, o, ch)

def survive_below(fn, u0=-3, u1=3):
    pts = [(u0, -1)] + [(u, fn(u)) for u in np.linspace(u0, u1, 40)] + [(u1, -1)]
    return Polygon(pts).buffer(0)

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
