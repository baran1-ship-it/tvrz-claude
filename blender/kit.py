"""Stavebnice detailu: nepravidelne kameny ostění, dvere ve trech urovnich, okna, prkna mostu a ochozu,
padaci most s retezy. Vsechno plasticke (kovani a kameny vystupuji z licu) a schvalne nedokonale.

Souradnice jako ve hre: X vychod, Y nahoru, Z jih. Dilky se stavi v lokalnim ramci m (Matrix 4x4):
lokalni X = sirka otvoru, Y = nahoru, Z = ven ze zdi (lic zdi je v z = 0).
"""
import math
import random

import bpy  # noqa: F401  (bmesh potrebuje nacteny Blender)
import bmesh
from mathutils import Matrix, Vector

from lib import M, Part

RND = random.Random(11)


def J(a):
    return RND.uniform(-a, a)


# ======================================================================= zakladni tvary

def _hull(pts):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    bmesh.ops.convex_hull(bm, input=vs)
    used = sorted({v for f in bm.faces for v in f.verts}, key=lambda v: v.index)
    idx = {v: i for i, v in enumerate(used)}
    verts = [v.co.copy() for v in used]
    faces = [[idx[v] for v in f.verts] for f in bm.faces]
    bm.free()
    return verts, faces


def stone(P: Part, m: Matrix, size, mat="kvadr", cham=0.035, rough=0.018, rnd=None):
    """Nepravidelny tesany kamen: kvadr se zkosenymi hranami, rohy a hrany nahodne otlucene.
    m = stred kamene, size = (x, y, z)."""
    a, b, c = (s / 2 for s in size)
    ch = [cham * RND.uniform(0.5, 1.6) for _ in range(8)]
    pts = []
    k = 0
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                h = min(ch[k], a * 0.45, b * 0.45, c * 0.45)
                k += 1
                for p in ((sx * a, sy * (b - h), sz * (c - h)), (sx * (a - h), sy * b, sz * (c - h)), (sx * (a - h), sy * (b - h), sz * c)):
                    pts.append(Vector((p[0] + J(rough), p[1] + J(rough), p[2] + J(rough))))
    # vypoukla lice: par bodu uprostred ploch mirne ven
    for ax in range(3):
        for s in (-1, 1):
            p = Vector((0, 0, 0))
            p[ax] = s * ((a, b, c)[ax] + RND.uniform(0.0, rough * 0.8))
            for o in range(2):
                q = p.copy()
                q[(ax + 1) % 3] += J((a, b, c)[(ax + 1) % 3] * 0.5)
                q[(ax + 2) % 3] += J((a, b, c)[(ax + 2) % 3] * 0.5)
                pts.append(q)
    verts, faces = _hull(pts)
    P.mesh(verts, faces, mat, rnd=rnd, m=m)


def plank(P: Part, a, b, w, t, mat="prkna_ven", up=(0, 1, 0), wear=0.0, rnd=None, seg_len=0.3, cup=0.004, uvo=None,
          dip=None):
    """Prkno z a do b (osa podel), sirka w, tloustka t (smerem up od spodni plochy).
    wear 0..1: zaoblene a osoupane horni hrany, prohlubne. dip(s) -> pokles horni plochy v miste s (0..1)."""
    a, b, up = Vector(a), Vector(b), Vector(up).normalized()
    d = b - a
    L = d.length
    d.normalize()
    side = up.cross(d).normalized()
    up = d.cross(side).normalized()
    n = max(2, int(L / seg_len))
    r = 0.004 + 0.012 * wear
    prof = [(-0.5, 0.0), (0.5, 0.0), (0.5, 1.0), (0.5, 1.0), (-0.5, 1.0), (-0.5, 1.0)]
    twist0, bow = J(0.02), J(0.006)
    wj = [1.0 + J(0.03) for _ in range(n + 1)]
    ring = []
    for i in range(n + 1):
        s = i / n
        c = a + d * (L * s) + up * (bow * math.sin(math.pi * s))
        tw = twist0 * (s - 0.5) * 2
        sd = (side * math.cos(tw) + up * math.sin(tw))
        uu = (up * math.cos(tw) - side * math.sin(tw))
        ww = w * wj[i]
        tt = t * (1 + J(0.05))
        dd = dip(s) if dip else 0.0
        rr = r * (1 + J(0.4))
        pts = [
            c - sd * ww / 2,
            c + sd * ww / 2,
            c + sd * ww / 2 + uu * (tt - rr - dd * 0.4),
            c + sd * (ww / 2 - rr) + uu * (tt - dd * 0.6),
            c - sd * (ww / 2 - rr) + uu * (tt - dd * 0.6),
            c - sd * ww / 2 + uu * (tt - rr - dd * 0.4),
        ]
        # mirne prohnuti (miskovani) horni plochy
        mid_drop = uu * (cup + dd)
        pts[3] = pts[3] - mid_drop * 0.3
        pts[4] = pts[4] - mid_drop * 0.3
        ring.append(pts)
    verts, faces, uvs = [], [], []
    if uvo is None:
        uvo = (RND.uniform(0, 8), RND.uniform(0, 8))
    per = [0.0, w, w + t, w + t + 0.02, 2 * w + t, 2 * w + 2 * t]
    k = len(prof)
    for i in range(n + 1):
        verts.extend(ring[i])
    for i in range(n):
        for j in range(k):
            j2 = (j + 1) % k
            f = (i * k + j, i * k + j2, (i + 1) * k + j2, (i + 1) * k + j)
            faces.append(f)
            u0, u1 = L * i / n + uvo[0], L * (i + 1) / n + uvo[0]
            v0, v1 = per[j] + uvo[1], (per[j2] if j2 else 2 * w + 2 * t + 0.02) + uvo[1]
            uvs.append([(u0, v0), (u0, v1), (u1, v1), (u1, v0)])
    # cela prken
    faces.append(tuple(reversed(range(k))))
    uvs.append([(J(1), J(1)) for _ in range(k)])
    faces.append(tuple(n * k + j for j in range(k)))
    uvs.append([(J(1), J(1)) for _ in range(k)])
    P.mesh(verts, faces, mat, uvs, rnd=rnd)


def nail(P: Part, p, nrm, r=0.011):
    """Kovana hlavicka hrebu (nizky jehlan)."""
    nrm = Vector(nrm).normalized()
    from lib import frame
    f = frame(nrm, Vector((0, 1, 0)) if abs(nrm.y) < 0.9 else Vector((1, 0, 0)))
    m = M(Vector(p), basis=f @ Matrix.Rotation(-math.pi / 2, 3, "X") @ Matrix.Rotation(RND.uniform(0, 1), 3, "Y"))
    P.lathe(m, [(0.0, -0.002), (r, -0.002), (r * 0.8, r * 0.35), (r * 0.25, r * 0.7), (0.0, r * 0.75)], 5, "zelezo", cap_bot=False)


def iron_band(P: Part, m: Matrix, a, b, w=0.05, t=0.008, nails=0.14, end="spic"):
    """Kovany pas na lici dveri (lokalne v rovine z=0, vystupuje do +z). a, b = (x, y) konce.
    end: 'spic' (kosovy hrot), 'liliie' (rozvilina se dvema zavitky), None."""
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    d = (b - a).normalized()
    L = (b - a).length
    side = Vector((-d.y, d.x, 0))
    pa, pb = m @ a, m @ b
    zz = m.to_3x3() @ Vector((0, 0, 1))
    plank(P, pa, pb, w, t, "zelezo", up=zz, wear=0.2, seg_len=0.12, cup=-0.001, rnd=0.3)
    if nails:
        k = max(2, int(L / nails))
        for i in range(k + 1):
            s = 0.05 + (L - 0.1) * i / k
            nail(P, m @ (a + d * s + Vector((0, 0, t))), zz, 0.013)
    if end == "spic":
        tip = b + d * 0.09
        for sgn in (-1, 1):
            q0 = m @ (b + side * sgn * w * 0.5 + Vector((0, 0, t * 0.5)))
            P.rod(q0, m @ (tip + Vector((0, 0, t * 0.5))), 0.006, 4, "zelezo")
        P.mesh([m @ (b + side * w * 0.5 + Vector((0, 0, t))), m @ (tip + Vector((0, 0, t * 0.6))), m @ (b - side * w * 0.5 + Vector((0, 0, t)))],
               [(0, 1, 2)], "zelezo", rnd=0.3)
    elif end == "lilie":
        for sgn in (-1, 1):
            pts = []
            for i in range(9):
                ang = i / 8 * math.pi * 1.3
                rr = 0.09 * (1 - i / 11)
                p = b + d * (0.02 + rr * math.sin(ang)) + side * sgn * (rr * (1 - math.cos(ang)) + w * 0.2)
                pts.append(m @ (p + Vector((0, 0, t * 0.6))))
            for q0, q1 in zip(pts, pts[1:]):
                P.rod(q0, q1, 0.009, 5, "zelezo")
        P.rod(m @ (b + Vector((0, 0, t * 0.6))), m @ (b + d * 0.12 + Vector((0, 0, t * 0.6))), 0.011, 5, "zelezo")


def ring_handle(P: Part, m: Matrix, x, y, r=0.07, plate=True):
    """Kruh na otevirani s kovanou plotnou a skobou."""
    zz = m.to_3x3() @ Vector((0, 0, 1))
    if plate:
        stone(P, m @ M((x, y + 0.02, 0.006)), (0.11, 0.13, 0.012), "zelezo", cham=0.01, rough=0.002, rnd=0.3)
        for dx, dy in ((-0.04, 0.06), (0.04, 0.06), (-0.04, -0.02), (0.04, -0.02)):
            nail(P, m @ Vector((x + dx, y + 0.02 + dy, 0.012)), zz, 0.009)
    P.rod(m @ Vector((x, y + 0.02, 0.012)), m @ Vector((x, y + 0.02, 0.05)), 0.008, 5, "zelezo")
    pts = []
    for i in range(13):
        ang = i / 12 * 2 * math.pi
        pts.append(m @ Vector((x + r * math.sin(ang), y + 0.02 - r + r * math.cos(ang), 0.05 - 0.03 * (1 - math.cos(ang)) * 0.5)))
    for q0, q1 in zip(pts, pts[1:]):
        P.rod(q0, q1, 0.009, 5, "zelezo")


# ======================================================================= otvory

def arch_top(kind, w, spring):
    """Funkce horni hrany otvoru y(x) pro x v <-w/2, w/2>."""
    hw = w / 2
    if kind == "lomeny":
        r = hw * 1.35
        def f(x):
            c = -hw + r if x < 0 else hw - r
            return spring + math.sqrt(max(0.0, r * r - (x - c) ** 2))
        return f
    if kind == "pulkruh":
        return lambda x: spring + math.sqrt(max(0.0, hw * hw - x * x))
    if kind == "segment":
        rise = 0.12
        r = (hw * hw + rise * rise) / (2 * rise)
        return lambda x: spring - (r - rise) + math.sqrt(max(0.0, r * r - x * x))
    return lambda x: spring


def stone_jambs(P: Part, m: Matrix, w, spring, depth, mat="kvadr", proud=0.05, course=0.32):
    """Ostění: stridave dlouhe a kratke kvadry po stranach otvoru, vystupuji z lice o 'proud'."""
    for sx in (-1, 1):
        y = 0.0
        k = 0
        while y < spring - 0.05:
            h = min(course * RND.uniform(0.85, 1.15), spring - y)
            wid = (0.42 if k % 2 == 0 else 0.26) * RND.uniform(0.9, 1.1)
            x = sx * (w / 2 + wid / 2 - 0.02)
            pr = proud * RND.uniform(0.6, 1.3)
            dz = depth + pr
            stone(P, m @ M((x, y + h / 2, pr - dz / 2)) @ Matrix.Rotation(J(0.02), 4, "Z"), (wid, h - 0.012, dz), mat)
            y += h
            k += 1


def stone_arch(P: Part, m: Matrix, w, spring, kind, depth, mat="kvadr", ring=0.3, proud=0.06, n=None):
    """Zaklenek z klenaku (nepravidelne, kazdy klenak lehce jinak vystupuje)."""
    f = arch_top(kind, w, spring)
    hw = w / 2
    if kind == "rovny":
        L = w + 0.8
        stone(P, m @ M((J(0.02), spring + 0.18, proud - (depth + proud) / 2)), (L, 0.36, depth + proud), mat, cham=0.03)
        return
    n = n or (9 if kind != "segment" else 7)
    # body vnitrni krivky
    xs = [-hw + w * i / n for i in range(n + 1)]
    inner = [Vector((x, f(x), 0)) for x in xs]
    inner[0].y = inner[-1].y = spring
    for i in range(n):
        p0, p1 = inner[i], inner[i + 1]
        mid = (p0 + p1) / 2
        # smer ven z oblouku (od stredu oblouku)
        cen = Vector((0, spring - (hw * 0.5 if kind == "lomeny" else 0.0), 0))
        o0 = (p0 - cen).normalized()
        o1 = (p1 - cen).normalized()
        rr = ring * RND.uniform(0.9, 1.15)
        pr = proud * RND.uniform(0.5, 1.4)
        g = 0.006
        q = [p0 + (p1 - p0).normalized() * g, p1 - (p1 - p0).normalized() * g]
        pts = []
        for zf in (pr, -depth):
            for pp, oo in ((q[0], o0), (q[1], o1)):
                for rad in (0.0, rr):
                    v = pp + oo * rad + Vector((J(0.012), J(0.012), zf + J(0.008)))
                    pts.append(v)
        verts, faces = _hull(pts)
        P.mesh(verts, faces, mat, m=m)
    # zaver: vetsi klenak nahore je soucasti rady (lichy pocet)


def threshold(P: Part, m: Matrix, w, depth, mat="kvadr_sedy"):
    stone(P, m @ M((J(0.02), -0.06, -depth / 2 + 0.12)), (w + 0.3, 0.14, depth + 0.24), mat, cham=0.02, rough=0.01)


def wood_frame(P: Part, m: Matrix, w, h, depth, top_kind="rovny"):
    """Dubova zarubeň (vnitrni dvere a hrazdeni): stojky, nadprazi s presahem, osoupane hrany."""
    for sx in (-1, 1):
        x = sx * (w / 2 + 0.06)
        plank(P, m @ Vector((x, 0, 0.0)), m @ Vector((x, h + 0.12, 0.0)), 0.12, depth, "dub", up=m.to_3x3() @ Vector((0, 0, -1)),
              wear=0.5, seg_len=0.5)
    plank(P, m @ Vector((-w / 2 - 0.25, h + 0.09, 0.0)), m @ Vector((w / 2 + 0.25, h + 0.09, 0.0)), 0.16, depth + 0.02, "dub",
          up=m.to_3x3() @ Vector((0, 0, -1)), wear=0.5, seg_len=0.5)


# ======================================================================= dvere

def door_leaf(P: Part, m: Matrix, w, h, kind="hlavni", top="rovny", spring=None, lattice=False, arch_w=None, xoff=0.0):
    """Dverni kridlo s pantem v lokalnim x = -w/2, lic v z = 0 (vystupuje do +z o kovani).
    kind: 'hlavni' (tezky dub, huste hreby, pasy s rozvilinami, kruh), 'obycejne' (vzpera, 2 pasy),
          'vnitrni' (lehke, petlice)."""
    t = {"hlavni": 0.07, "obycejne": 0.055, "vnitrni": 0.04}[kind]
    spring = spring if spring is not None else h
    f0 = arch_top(top, arch_w or w, spring)
    f = lambda x: f0(x + xoff)  # noqa: E731  (kridlo dvoukridlych dveri: oblouk spolecny pro oba)
    nb = max(3, round(w / (RND.uniform(0.16, 0.22) if top == "rovny" else 0.13)))
    zz = m.to_3x3() @ Vector((0, 0, 1))
    yy = m.to_3x3() @ Vector((0, 1, 0))
    x = -w / 2
    tone = RND.random()
    for i in range(nb):
        bw = w / nb
        cx = x + bw / 2
        top_y = f(cx) if top != "rovny" else h
        plank(P, m @ Vector((cx, 0.0, -t)), m @ Vector((cx, top_y - 0.004, -t)), bw - 0.006, t,
              "dvere" if kind != "vnitrni" else "prkna", up=zz, wear=0.35, seg_len=0.4, rnd=min(1, max(0, tone + J(0.15))))
        x += bw
    # zadni pricky (lisny) a u obycejnych sikma vzpera vpredu
    ys = [0.18 * h, 0.82 * min(h, spring)]
    back = m.to_3x3() @ Vector((0, 0, -1))
    for yb in ys:
        plank(P, m @ Vector((-w / 2 + 0.03, yb, -t)), m @ Vector((w / 2 - 0.03, yb, -t)), 0.13, 0.035, "dvere", up=back, wear=0.4)
    if kind == "obycejne":
        for yb in ys:
            plank(P, m @ Vector((-w / 2 + 0.03, yb, 0.0)), m @ Vector((w / 2 - 0.03, yb, 0.0)), 0.12, 0.03, "dvere", up=zz, wear=0.5)
        plank(P, m @ Vector((-w / 2 + 0.1, ys[0] + 0.08, 0.0)), m @ Vector((w / 2 - 0.1, ys[1] - 0.08, 0.0)), 0.1, 0.028, "dvere",
              up=zz, wear=0.5)
        for yb in ys:
            iron_band(P, m @ M((0, 0, 0.03)), (-w / 2 + 0.02, yb + 0.03), (w * 0.25, yb + 0.03), 0.045, 0.007, 0.16, "spic")
        # zelezna zavora/zastrcka
        stone(P, m @ M((w / 2 - 0.12, h * 0.5, 0.02)), (0.16, 0.05, 0.02), "zelezo", cham=0.006, rough=0.002)
        P.rod(m @ Vector((w / 2 - 0.25, h * 0.5, 0.04)), m @ Vector((w / 2 + 0.02, h * 0.5, 0.04)), 0.012, 6, "zelezo")
    elif kind == "hlavni":
        if lattice:
            # mrizove kovani: dve sady sikmych pasu, hreby v krizenich
            step = 0.3
            for sgn in (-1, 1):
                k = -int((w + h) / step)
                while k * step < w + h:
                    x0 = -w / 2 + k * step
                    a = Vector((x0, 0.04, 0))
                    bb = Vector((x0 + sgn * (h - 0.08), h - 0.04, 0))
                    # orez do kridla
                    pts = []
                    for s in [i / 40 for i in range(41)]:
                        p = a.lerp(bb, s)
                        if -w / 2 + 0.03 < p.x < w / 2 - 0.03 and p.y < f(p.x) - 0.04:
                            pts.append(p)
                    if len(pts) > 2:
                        iron_band(P, m @ M((0, 0, 0.002 if sgn > 0 else 0.01)), (pts[0].x, pts[0].y), (pts[-1].x, pts[-1].y), 0.04, 0.007,
                                  0.11, None)
                    k += 1
        else:
            # husta mrizka hrebu a tri pasy s rozvilinou
            for row in range(int(spring / 0.13)):
                yy_ = 0.1 + row * 0.13
                for col in range(int(w / 0.12)):
                    xx = -w / 2 + 0.07 + col * 0.12 + (0.06 if row % 2 else 0)
                    if xx < w / 2 - 0.05 and yy_ < f(xx) - 0.06:
                        nail(P, m @ Vector((xx + J(0.004), yy_ + J(0.004), 0.0)), zz, 0.012)
            for yb in (0.16 * h, 0.5 * spring, 0.82 * spring):
                iron_band(P, m @ M((0, 0, 0.0)), (-w / 2 + 0.01, yb), (w * 0.3, yb), 0.055, 0.009, 0.15, "lilie")
        ring_handle(P, m, w / 2 - 0.2, h * 0.5 if top == "rovny" else spring * 0.55, 0.075)
        # zamkovy stitek
        stone(P, m @ M((w / 2 - 0.2, h * 0.42 if top == "rovny" else spring * 0.45, 0.006)), (0.09, 0.14, 0.01), "zelezo", cham=0.008, rough=0.002)
    else:
        # vnitrni: drevena klika a kovana petlice
        stone(P, m @ M((w / 2 - 0.12, h * 0.48, 0.03)), (0.05, 0.16, 0.05), "dub", cham=0.012, rough=0.004)
        P.rod(m @ Vector((w / 2 - 0.35, h * 0.55, 0.012)), m @ Vector((w / 2 - 0.05, h * 0.55, 0.012)), 0.007, 5, "zelezo")
        for yb in ys:
            iron_band(P, m @ M((0, 0, 0.0)), (-w / 2 + 0.01, yb), (-w / 2 + 0.3, yb), 0.035, 0.006, 0.1, "spic")


def doorway(P: Part, m: Matrix, kind="hlavni", w=1.1, h=2.2, depth=0.7, top=None, open_deg=0.0, lattice=False,
            leaf=True, double=False, LP: Part = None, open2=None):
    """Kompletni otvor: ostění (kamenne / zarubeň), zaklenek, prah a kridlo na pantech."""
    if top is None:
        top = {"hlavni": "lomeny", "obycejne": "segment", "vnitrni": "rovny"}[kind]
    spring = h - (w / 2 * 0.95 if top == "lomeny" else w / 2 if top == "pulkruh" else 0.12 if top == "segment" else 0)
    if kind == "vnitrni":
        wood_frame(P, m, w, h, depth)
    else:
        stone_jambs(P, m, w, spring, depth, "kvadr", 0.06 if kind == "hlavni" else 0.035, 0.3 if kind == "hlavni" else 0.36)
        stone_arch(P, m, w, spring, top, depth, "kvadr", 0.34 if kind == "hlavni" else 0.26, 0.07 if kind == "hlavni" else 0.04)
        threshold(P, m, w, depth)
    # vyplne nad obloukem (cvikly) v otvoru zdi
    if kind != "vnitrni" and top != "rovny":
        f = arch_top(top, w, spring)
        for sx in (-1, 1):
            xs = [sx * (w / 2) * (1 - i / 8) for i in range(9)]
            pts = [Vector((x, f(x) if i else spring, 0.0)) for i, x in enumerate(xs)] + [Vector((sx * w / 2, h + 0.02, 0.0))]
            P.prism([m @ (p - Vector((0, 0, depth))) for p in pts], m.to_3x3() @ Vector((0, 0, depth - 0.02)), "zdivo_omitka")
    if not leaf:
        return
    LP = LP or P
    zl = -depth * 0.45 if kind != "vnitrni" else -0.02
    if double:
        # dve kridla, panty po stranach, spolecny oblouk
        hw = w / 2
        for sx, ang in ((-1, open_deg), (1, open2 if open2 is not None else 0.0)):
            hinge = m @ M((sx * (w / 2 - 0.01), 0.0, zl)) @ Matrix.Rotation(math.radians(sx * -ang), 4, "Y")
            door_leaf(LP, hinge @ M((-sx * (hw / 2 - 0.005), 0.0, 0.0)), hw - 0.02, h - 0.02, kind, top, spring - 0.01, lattice,
                      arch_w=w - 0.02, xoff=-sx * hw / 2)
    else:
        # kridlo: pant u -w/2, osazene v polovine hloubky zdi (u vnitrnich v zarubni)
        hinge = m @ M((-w / 2 + 0.01, 0.0, zl)) @ Matrix.Rotation(math.radians(-open_deg), 4, "Y")
        door_leaf(LP, hinge @ M((w / 2 - 0.01, 0.0, 0.0)), w - 0.02, h - 0.02, kind, top, spring - 0.01, lattice)
    # panty (kovane cepy v ostění)
    for sx in ((-1, 1) if double else (-1,)):
        for yb in (0.18 * h, 0.82 * spring):
            P.rod(m @ Vector((sx * (w / 2 + 0.02), yb - 0.06, zl - 0.03)), m @ Vector((sx * (w / 2 + 0.02), yb + 0.06, zl - 0.03)), 0.014, 6,
                  "zelezo")


def window(P: Part, m: Matrix, w=0.7, h=0.95, depth=0.7, kind="okno", shutters=False):
    """Okno v kamennem ostění: vystupujici parapet a nadprazi, olovene sklo nebo mriz, okenice."""
    stone_jambs(P, m @ M((0, 0, 0)), w, h, depth, "kvadr", 0.04, 0.32)
    stone_arch(P, m, w, h, "rovny" if kind != "lomene" else "lomeny", depth, "kvadr", 0.26, 0.05)
    stone(P, m @ M((J(0.01), -0.07, 0.06 - (depth + 0.12) / 2)), (w + 0.42, 0.13, depth + 0.12), "kvadr_sedy", cham=0.02)
    zg = -depth * 0.35
    P.face([m @ Vector((-w / 2, 0, zg)), m @ Vector((w / 2, 0, zg)), m @ Vector((w / 2, h, zg)), m @ Vector((-w / 2, h, zg))], "sklo_terce")
    for k in range(1, 3):
        x = -w / 2 + w * k / 3
        P.rod(m @ Vector((x, 0.02, zg + 0.04)), m @ Vector((x, h - 0.02, zg + 0.04)), 0.013, 6, "zelezo")
    for yb in (h * 0.35, h * 0.7):
        P.rod(m @ Vector((-w / 2, yb, zg + 0.07)), m @ Vector((w / 2, yb, zg + 0.07)), 0.012, 6, "zelezo")
    if shutters:
        zz = m.to_3x3() @ Vector((0, 0, 1))
        for sx in (-1, 1):
            hinge = m @ M((sx * (w / 2 + 0.22), 0.0, 0.07)) @ Matrix.Rotation(math.radians(sx * 100), 4, "Y")
            leaf = hinge @ M((-sx * (w / 4), 0, 0))
            for i in range(3):
                x = -w / 4 + w / 2 * (i + 0.5) / 3
                plank(P, leaf @ Vector((x, 0.0, 0.0)), leaf @ Vector((x, h, 0.0)), w / 6 - 0.006, 0.03, "okenice",
                      up=leaf.to_3x3() @ Vector((0, 0, 1)), wear=0.4)
            for yb in (h * 0.2, h * 0.8):
                iron_band(P, leaf @ M((0, 0, 0.03)), (sx * w / 4, yb), (-sx * w / 8, yb), 0.03, 0.005, 0.09, "spic")


# ======================================================================= most a ochoz

def deck(P: Part, a, b, hw, mat="prkna_ven", worn=0.8, beams=(-1.3, 0.0, 1.3), plank_w=(0.24, 0.32), t=0.06):
    """Mostovka/podlaha ochozu: prkna napric (osa a->b), kazde jine, mezery, hreby nad tramy,
    vysoupana stopa uprostred (pokles a zaobleni), nekde prasklé prkno nebo chybejici kus hrany."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    d.normalize()
    up = Vector((0, 1, 0))
    side = up.cross(d).normalized()
    up = d.cross(side).normalized()
    s = 0.0
    while s < L - 0.05:
        pw = min(RND.uniform(*plank_w), L - s)
        c = a + d * (s + pw / 2)
        ext = (J(0.06), J(0.06))
        tone = RND.random()

        def dip(u, worn=worn):
            x = (u - 0.5) * 2 * (hw + 0.05)
            return worn * 0.012 * max(0.0, 1 - (abs(x) / 0.75) ** 2)
        if RND.random() < 0.06 and worn > 0:
            # prasklé prkno: dva kusy se sparou
            cut = RND.uniform(-0.5, 0.5)
            plank(P, c - side * (hw + 0.05 + ext[0]), c + side * cut, pw - 0.012, t, mat, up=up, wear=worn, rnd=tone, seg_len=0.25)
            plank(P, c + side * (cut + 0.015), c + side * (hw + 0.05 + ext[1]), pw - 0.012, t, mat, up=up, wear=worn, rnd=tone, seg_len=0.25)
        else:
            plank(P, c - side * (hw + 0.05 + ext[0]), c + side * (hw + 0.05 + ext[1]), pw - RND.uniform(0.008, 0.022), t, mat, up=up,
                  wear=worn, rnd=tone, seg_len=0.22, dip=dip)
        for bx in beams:
            for o in (-0.25, 0.25):
                nail(P, c + side * bx + d * (pw * o) + up * (t - 0.004), up, 0.009)
        s += pw


def chain(P: Part, a, b, link=0.11, wire=0.012, sag=0.1):
    """Retez z clanku (kazdy druhy pootoceny o 90 stupnu), lehce prověšený."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    n = int(L / (link * 0.72))
    from lib import frame
    for k in range(n):
        s0, s1 = k / n, (k + 1) / n
        p0 = a.lerp(b, s0) - Vector((0, sag * math.sin(math.pi * s0), 0))
        p1 = a.lerp(b, s1) - Vector((0, sag * math.sin(math.pi * s1), 0))
        c = (p0 + p1) / 2
        d = (p1 - p0).normalized()
        f = frame(d, Vector((0, 1, 0)) if k % 2 else Vector((1, 0, 0)))
        rx, ry = link * 0.32, link * 0.5
        pts = [c + f @ Vector((rx * math.cos(t), 0, ry * math.sin(t))) for t in [i / 10 * 2 * math.pi for i in range(11)]]
        for q0, q1 in zip(pts, pts[1:]):
            P.rod(q0, q1, wire, 4, "zelezo")


def drawbridge(P: Part, m: Matrix, w=3.5, L=4.2, angle=0.0):
    """Padaci most: dva podelne tramy, pricne trámky, mostovka z ochozenych prken, kovane pasy na hrane,
    oka a kladky. m = osa otaceni (na hrane brany), most vede do +z, angle = zdvih ve stupnich."""
    mm = m @ Matrix.Rotation(math.radians(angle), 4, "X")
    for sx in (-1, 1):
        x = sx * (w / 2 - 0.15)
        P.beam(mm @ Vector((x, -0.2, 0.0)), mm @ Vector((x, -0.2, L)), 0.24, 0.28, "dub_ven", j=1)
    for k in range(5):
        z = 0.2 + (L - 0.4) * k / 4
        P.beam(mm @ Vector((-w / 2, -0.4, z)), mm @ Vector((w / 2, -0.4, z)), 0.16, 0.14, "dub_ven", j=1)
    deck(P, mm @ Vector((0, -0.06, 0.02)), mm @ Vector((0, -0.06, L - 0.02)), w / 2 - 0.05, "prkna_ven", 0.9,
         beams=(-(w / 2 - 0.15), 0.0, w / 2 - 0.15))
    # kovane hrany a oka pro retezy
    yy = mm.to_3x3() @ Vector((0, 1, 0))
    for sx in (-1, 1):
        x = sx * (w / 2 - 0.15)
        iron_band(P, mm @ M((x, -0.06, L - 0.3)) @ Matrix.Rotation(-math.pi / 2, 4, "X"), (0, -0.3), (0, 0.3), 0.06, 0.008, 0.12, None)
        eye = mm @ Vector((sx * (w / 2 + 0.02), 0.0, L - 0.25))
        pts = [eye + Vector((0, 0.06 * math.sin(t), 0.06 * math.cos(t))) for t in [i / 10 * 2 * math.pi for i in range(11)]]
        for q0, q1 in zip(pts, pts[1:]):
            P.rod(q0, q1, 0.014, 5, "zelezo")
    plank(P, mm @ Vector((-w / 2, -0.02, L)), mm @ Vector((w / 2, -0.02, L)), 0.1, 0.012, "zelezo", up=mm.to_3x3() @ Vector((0, 0, 1)),
          wear=0.1, seg_len=0.3)
    return [mm @ Vector((sx * (w / 2 + 0.02), 0.0, L - 0.25)) for sx in (-1, 1)]
