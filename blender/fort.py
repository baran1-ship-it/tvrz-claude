"""Opevneni: hradby s cimbuřím a ochozem, brana s padacim mostem, obytna vez, schody na hradbu, teren."""
import math

from mathutils import Matrix, Vector

import props as PR
from lib import M, Part, R, jit, rot, shingle_roof, wall_x, wall_z

IX, IZ = 17.0, 14.0      # vnitrni lic hradeb
OX, OZ = 18.8, 15.8      # vnejsi lic
WALK = 6.5
BASE = -4.5


# ------------------------------------------------------------------ teren (prikop, svah, nadvori)

def rect_dist(x, z):
    dx = abs(x) - OX
    dz = abs(z) - OZ
    return math.hypot(max(dx, 0), max(dz, 0)) + min(max(dx, dz), 0)


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def land(x, z):
    """Profil jako v terrain.gd: tesne u zdi bermа, pak prikop a val."""
    d = rect_dist(x, z)
    if d < 0:
        return 0.0
    if d < 1.5:
        prof = -0.35
    elif d < 5.5:
        prof = -0.35 + (-3.6 + 0.35) * smooth(1.5, 5.5, d)
    elif d < 8.5:
        prof = -3.6
    else:
        prof = -3.6 + 2.3 * smooth(8.5, 12.5, d)
    far = -1.3 + 1.2 * math.sin(x * 0.05) * math.cos(z * 0.04) - 4.0 * smooth(30, 120, math.hypot(x, z))
    return prof + (far - (-1.3)) * smooth(11.5, 34.0, d)


def terrain(coll):
    P = Part("Teren")
    # okoli: mrizka 1 m blizko, ridsi dal
    far = [float(v) for v in range(-200, -60, 5)]
    xs = far + [x * 1.0 for x in range(-60, 61)] + [-v for v in reversed(far)]
    zs = far + [z * 1.0 for z in range(-55, 71)] + [float(v) for v in range(75, 201, 5)]
    verts, faces, uvs = [], [], []
    idx = {}
    for i, x in enumerate(xs):
        for k, z in enumerate(zs):
            inside = abs(x) < OX - 0.6 and abs(z) < OZ - 0.6
            y = land(x, z) + (0.0 if inside else jit(0.06))
            if inside:
                y = -0.3
            idx[(i, k)] = len(verts)
            verts.append((x, y, z))
    for i in range(len(xs) - 1):
        for k in range(len(zs) - 1):
            fc = (idx[(i, k)], idx[(i, k + 1)], idx[(i + 1, k + 1)], idx[(i + 1, k)])
            faces.append(fc)
    P.mesh(verts, faces, "zem")
    o = P.commit(coll)
    # travnatost: atribut "grass" na plochach podle vzdalenosti od zdi a cesty
    me = o.data
    at = me.attributes.new("grass", "FLOAT", "FACE")
    vals = []
    for poly in me.polygons:
        c = poly.center
        x, z = c.x, -c.y
        d = rect_dist(x, z)
        road = abs(x) < 2.2 and z > 16
        g = 0.0 if road else (0.85 if d > 1.0 else 0.4)
        if 5.0 < d < 9.0:
            g = 0.55
        vals.append(g + jit(0.15))
    at.data.foreach_set("value", vals)
    return o


def yard_ground(coll, paths):
    """Nadvori: udusana hlina, vyjete cesty, trava u zdi."""
    P = Part("Nadvori")
    verts, faces = [], []
    n_x, n_z = 68, 56
    x0, x1, z0, z1 = -IX, IX, -IZ, IZ
    idx = {}
    for i in range(n_x + 1):
        for k in range(n_z + 1):
            x = x0 + (x1 - x0) * i / n_x
            z = z0 + (z1 - z0) * k / n_z
            idx[(i, k)] = len(verts)
            verts.append((x, jit(0.025), z))
    for i in range(n_x):
        for k in range(n_z):
            faces.append((idx[(i, k)], idx[(i, k + 1)], idx[(i + 1, k + 1)], idx[(i + 1, k)]))
    P.mesh(verts, faces, "zem")
    o = P.commit(coll)
    me = o.data
    at = me.attributes.new("grass", "FLOAT", "FACE")
    vals = []
    for poly in me.polygons:
        c = poly.center
        x, z = c.x, -c.y
        dp = min(path_dist(x, z, p) for p in paths)
        dw = min(IX - abs(x), IZ - abs(z))
        g = smooth(0.8, 2.6, dp) * 0.75 + (0.35 if dw < 1.2 else 0.0)
        vals.append(min(1.0, g) + jit(0.12))
    at.data.foreach_set("value", vals)
    return o


def path_dist(x, z, path):
    best = 1e9
    for a, b in zip(path[:-1], path[1:]):
        ax, az = a
        bx, bz = b
        dx, dz = bx - ax, bz - az
        t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(x - ax - dx * t, z - az - dz * t))
    return best


# ------------------------------------------------------------------ prvky

def quoins(P: Part, x, z, sx, sz, y0, y1, long_=0.75, short=0.4, h=0.34, mat="kvadr"):
    """Narozni kvadry: (x, z) = vnejsi roh, sx/sz = smer do zdi."""
    y = y0
    k = 0
    while y < y1 - 0.05:
        hh = min(h + jit(0.04), y1 - y)
        a = long_ if k % 2 == 0 else short
        b = short if k % 2 == 0 else long_
        P.bb((x - sx * 0.03, y, z - sz * 0.02), (x + sx * a, y + hh - 0.015, z + sz * 0.3), mat)
        P.bb((x - sx * 0.02, y, z - sz * 0.03), (x + sx * 0.3, y + hh - 0.015, z + sz * b), mat)
        y += hh
        k += 1


def putlogs(P: Part, a, b, normal, ys, step=1.7):
    """Kapsy po lesenich: male tmave ctverce v radach."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    d.normalize()
    n = Vector(normal)
    for y in ys:
        t = R.uniform(0.4, 1.2)
        while t < L - 0.3:
            p = a + d * t + Vector((0, y + jit(0.08), 0)) + n * 0.004
            P.box(M(p, basis=Matrix((Vector((0, 1, 0)).cross(n), Vector((0, 1, 0)), n)).transposed()), (0.11, 0.11, 0.01), "dira")
            t += step + jit(0.3)


def parapet(P: Part, a, e, thick=0.5, slits=True):
    """Cimbuří: nizka zidka, zuby s kamennou kryci deskou, kazdy druhy se strilnou."""
    a, e = Vector(a), Vector(e)
    ln = (e - a).length
    d = (e - a) / ln
    side = Vector((0, 1, 0)).cross(d).normalized()
    bas = Matrix((side, Vector((0, 1, 0)), d)).transposed()
    P.box(M((a + e) * 0.5 + Vector((0, 0.45, 0)), basis=bas), (thick, 0.9, ln), "zdivo", collide=True)
    P.box(M((a + e) * 0.5 + Vector((0, 0.93, 0)), basis=bas), (thick + 0.08, 0.06, ln), "kvadr_sedy")
    mw, gap = 1.25, 0.8
    n = int((ln + gap) // (mw + gap))
    if n < 1:
        return
    margin = (ln - (n * mw + (n - 1) * gap)) * 0.5
    for k in range(n):
        s0 = margin + k * (mw + gap)
        w = mw
        if k == 0:
            s0, w = 0.0, mw + margin
        elif k == n - 1:
            w = ln - s0
        c = a + d * (s0 + w * 0.5)
        if slits and k % 2 == 1 and w > 0.9:
            sw = 0.09
            for sgn in (-1, 1):
                cc = c + d * sgn * (w + sw) * 0.25
                P.box(M(cc + Vector((0, 1.38, 0)), basis=bas), (thick, 0.9, (w - sw) * 0.5), "zdivo", collide=True)
            P.box(M(c + Vector((0, 1.0, 0)), basis=bas), (thick, 0.14, sw + 0.02), "zdivo")
            P.box(M(c + Vector((0, 1.79, 0)), basis=bas), (thick, 0.08, sw + 0.02), "zdivo")
        else:
            P.box(M(c + Vector((0, 1.38, 0)), basis=bas), (thick, 0.9, w), "zdivo", collide=True)
        P.box(M(c + Vector((0, 1.87, 0)), basis=bas), (thick + 0.1, 0.08, w + 0.06), "kvadr_sedy")


def gallery(P: Part, a, e, inward, width=0.85, rail=True):
    """Dreveny ochoz vylozeny do nadvori na krakorcich se vzperami."""
    a, e, inward = Vector(a), Vector(e), Vector(inward)
    ln = (e - a).length
    d = (e - a) / ln
    side = Vector((0, 1, 0)).cross(inward)
    n = max(2, round(ln / 1.9) + 1)
    # prkna napric
    k = 0.0
    while k < ln - 0.01:
        w = min(0.26 + jit(0.03), ln - k)
        c = a + d * (k + w / 2) + inward * (width / 2) + Vector((0, -0.04, 0))
        P.box(M(c, basis=Matrix((side, Vector((0, 1, 0)), inward)).transposed()), (w - 0.012, 0.06, width + jit(0.03)), "prkna_ven")
        k += w
    P.cols.append((M(a.lerp(e, 0.5) + inward * (width / 2) + Vector((0, -0.04, 0)), basis=Matrix((side, Vector((0, 1, 0)), inward)).transposed()), (ln, 0.08, width)))
    for i in range(n):
        p = a + d * (0.12 + (ln - 0.24) * i / (n - 1))
        P.beam(p + Vector((0, -0.17, 0)) - inward * 0.3, p + Vector((0, -0.17, 0)) + inward * (width + 0.12), 0.16, 0.2, "dub_ven", j=1)
        P.beam(p + Vector((0, -1.15, 0)) + inward * 0.02, p + Vector((0, -0.28, 0)) + inward * (width - 0.08), 0.12, 0.12, "dub_ven", j=1)
        if rail:
            P.beam(p + inward * (width - 0.05) + Vector((0, -0.1, 0)), p + inward * (width - 0.05) + Vector((0, 1.08, 0)), 0.11, 0.11, "dub_ven", j=1)
    if rail:
        r0 = a + inward * (width - 0.05)
        r1 = e + inward * (width - 0.05)
        P.beam(r0 + Vector((0, 1.05, 0)), r1 + Vector((0, 1.05, 0)), 0.1, 0.09, "dub_ven", j=0.5)
        P.beam(r0 + Vector((0, 0.55, 0)), r1 + Vector((0, 0.55, 0)), 0.07, 0.08, "dub_ven", j=0.5)
        P.cols.append((M((r0 + r1) * 0.5 + Vector((0, 0.55, 0)), basis=Matrix((d.cross(Vector((0, 1, 0))), Vector((0, 1, 0)), d)).transposed()), (0.12, 1.1, ln)))


def pyramid_roof(P: Part, x0, x1, z0, z1, y, apex):
    apex = Vector(apex)
    c = [Vector((x0, y, z0)), Vector((x1, y, z0)), Vector((x1, y, z1)), Vector((x0, y, z1))]
    # kazda strana: okap z vnejsi strany po smeru hodinovych rucicek
    for k in range(4):
        a, b = c[(k + 1) % 4], c[k]
        shingle_roof(P, a, b, apex, apex, ridge=False)
    # narozni hrebenace
    for k in range(4):
        n = (c[k] - apex).cross(Vector((0, 1, 0))).cross(c[k] - apex).normalized()
        if n.y < 0:
            n = -n
        P.beam(c[k] + n * 0.06, apex + n * 0.06, 0.34, 0.05, "prkna_ven", up=n)
    # spodni podbiti a vaznice
    P.bb((x0 + 0.15, y - 0.07, z0 + 0.15), (x1 - 0.15, y - 0.01, z1 - 0.15), "prkna")
    # makovice a korouhev
    P.rod(apex - Vector((0, 0.15, 0)), apex + Vector((0, 1.3, 0)), 0.03, 8, "zelezo")
    P.ball(apex + Vector((0, 0.28, 0)), (0.14, 0.17, 0.14), "mosaz", 12, 8)
    P.ball(apex + Vector((0, 1.32, 0)), (0.05, 0.05, 0.05), "mosaz", 8, 5)
    fl = apex + Vector((0.02, 0.85, 0))
    P.face([fl, fl + Vector((0.55, 0.0, 0.05)), fl + Vector((0.55, 0.32, 0.05)), fl + Vector((0, 0.36, 0))], "zelezo")


def window_slit(P: Part, cx, y0, y1, face_z=None, face_x=None, outward=1, thick=1.5, mat="kvadr"):
    """Strilna/uzke okno s kamennym ostenim na vnejsim lici."""
    w = 0.16
    if face_z is not None:
        z = face_z
        for sx in (-1, 1):
            P.bb((cx + sx * w / 2, y0 - 0.1, z), (cx + sx * (w / 2 + 0.22), y1 + 0.1, z + outward * 0.06), mat)
        P.bb((cx - w / 2 - 0.22, y1, z), (cx + w / 2 + 0.22, y1 + 0.3, z + outward * 0.07), mat)
        P.bb((cx - w / 2 - 0.22, y0 - 0.2, z), (cx + w / 2 + 0.22, y0, z + outward * 0.07), mat)


# ------------------------------------------------------------------ hradby

def walls(coll):
    P = Part("Hradby", bevel=0.03)
    P.bb((-OX, BASE, IZ), (-3.5, WALK, OZ), "zdivo", collide=True)
    P.bb((3.5, BASE, IZ), (OX, WALK, OZ), "zdivo", collide=True)
    P.bb((-OX, BASE, -8.8), (-IX, WALK, IZ), "zdivo", collide=True)
    P.bb((IX, BASE, -7.0), (OX, WALK, IZ), "zdivo", collide=True)
    P.bb((-11.8, BASE, -OZ), (-3.0, WALK, -IZ), "zdivo", collide=True)
    # sikma pata hradeb (eskarpa) z hrubeho kamene
    segs = [((-OX - 1.0, OZ), (-3.5, OZ), (0, 1)), ((3.5, OZ), (OX + 1.0, OZ), (0, 1)),
            ((-OX, -8.8), (-OX, OZ + 1.0), (-1, 0)), ((OX, -OZ - 1.0), (OX, OZ + 1.0), (1, 0)),
            ((-11.8, -OZ), (OX + 1.0, -OZ), (0, -1))]
    for (ax, az), (ex, ez), (ox, oz) in segs:
        o = Vector((ox, 0, oz))
        a = Vector((ax, 0, az))
        e = Vector((ex, 0, ez))
        y0, y1, out = BASE, -0.9, 1.0
        pa, qa = a + Vector((0, y1, 0)), e + Vector((0, y1, 0))
        pb, qb = a + Vector((0, y0, 0)) + o * out, e + Vector((0, y0, 0)) + o * out
        # ctyruhelnik sikme plochy + horni rimsa
        if (pb - pa).cross(qa - pa).dot(o) > 0:
            P.slab(pa, pb, qb, qa, 0.6, "zdivo_hole")
        else:
            P.slab(qa, qb, pb, pa, 0.6, "zdivo_hole")
        P.beam(pa + o * 0.08 + Vector((0, 0.05, 0)), qa + o * 0.08 + Vector((0, 0.05, 0)), 0.22, 0.12, "kvadr_sedy", up=(0, 1, 0))
    # narozi z kvadru
    quoins(P, -OX, OZ, 1, -1, BASE, WALK + 0.9)
    quoins(P, OX, OZ, -1, -1, BASE, WALK + 0.9)
    # cimburi
    parapet(P, (-OX, WALK, OZ - 0.25), (-3.5, WALK, OZ - 0.25))
    parapet(P, (3.5, WALK, OZ - 0.25), (OX, WALK, OZ - 0.25))
    parapet(P, (-OX + 0.25, WALK, -8.8), (-OX + 0.25, WALK, OZ - 0.5))
    parapet(P, (OX - 0.25, WALK, -7.0), (OX - 0.25, WALK, OZ - 0.5))
    parapet(P, (-11.8, WALK, -OZ + 0.25), (-3.0, WALK, -OZ + 0.25))
    # dlazba na korune
    for a, b in [((-OX + 0.5, WALK, IZ), (-3.5, WALK + 0.04, OZ - 0.5)), ((3.5, WALK, IZ), (OX - 0.5, WALK + 0.04, OZ - 0.5)),
                 ((-OX + 0.5, WALK, -8.8), (-IX, WALK + 0.04, IZ)), ((IX, WALK, -7.0), (OX - 0.5, WALK + 0.04, IZ)),
                 ((-11.8, WALK, -OZ + 0.5), (-3.0, WALK + 0.04, -IZ))]:
        P.bb(a, b, "dlazba_hrad")
    # kapsy po lesenich na vnejsim lici
    putlogs(P, (-OX + 0.5, 0, OZ), (-3.6, 0, OZ), (0, 0, 1), [0.8, 2.4, 4.0, 5.5])
    putlogs(P, (3.6, 0, OZ), (OX - 0.5, 0, OZ), (0, 0, 1), [0.8, 2.4, 4.0, 5.5])
    putlogs(P, (-OX, 0, OZ - 0.5), (-OX, 0, -8.6), (-1, 0, 0), [0.8, 2.4, 4.0, 5.5])
    putlogs(P, (OX, 0, OZ - 0.5), (OX, 0, -6.8), (1, 0, 0), [0.8, 2.4, 4.0, 5.5])
    # chrliče: kamenne zlabky z koruny ven
    for x in (-14.0, -8.0, 8.0, 14.0):
        P.bb((x - 0.12, WALK - 0.1, OZ - 0.05), (x + 0.12, WALK + 0.04, OZ + 0.45), "kvadr_sedy")
    P.commit(coll)

    G = Part("Ochozy", bevel=0.012)
    gallery(G, (-IX, WALK, IZ), (-3.5, WALK, IZ), (0, 0, -1))
    gallery(G, (4.7, WALK, IZ), (IX - 0.9, WALK, IZ), (0, 0, -1))
    gallery(G, (-IX, WALK, -8.8), (-IX, WALK, IZ - 0.9), (1, 0, 0))
    gallery(G, (IX, WALK, -7.0), (IX, WALK, IZ - 0.9), (-1, 0, 0))
    gallery(G, (-11.8, WALK, -IZ), (-3.0, WALK, -IZ), (0, 0, 1))
    G.bb((-IX, WALK - 0.08, IZ - 0.85), (-IX + 0.85, WALK - 0.01, IZ), "prkna_ven", collide=True)
    G.bb((IX - 0.85, WALK - 0.08, IZ - 0.85), (IX, WALK - 0.01, IZ), "prkna_ven", collide=True)
    G.beam((-3.05, WALK + 1.05, -IZ + 0.8), (-3.05, WALK + 1.05, -OZ + 0.5), 0.09, 0.1, "dub_ven", collide=True)
    G.beam((-3.05, WALK + 0.55, -IZ + 0.8), (-3.05, WALK + 0.55, -OZ + 0.5), 0.06, 0.08, "dub_ven")
    G.commit(coll)


# ------------------------------------------------------------------ brana

def vault_z(P: Part, cx, z0, z1, hw, spring, top, mat="zdivo"):
    """Valena klenba pruchodu podel Z: cela a podhled z klinku."""
    n = 14
    for i in range(n):
        a0 = math.pi - math.pi * i / n
        a1 = math.pi - math.pi * (i + 1) / n
        p0 = (cx + hw * math.cos(a0), spring + hw * math.sin(a0))
        p1 = (cx + hw * math.cos(a1), spring + hw * math.sin(a1))
        for z, s in ((z0, -1), (z1, 1)):
            q = [Vector((p0[0], p0[1], z)), Vector((p1[0], p1[1], z)), Vector((p1[0], top, z)), Vector((p0[0], top, z))]
            if s < 0:
                q.reverse()
            P.face(q, mat)
        # podhled: klenaky (kazdy pas zvlast, mirne nepravidelne)
        zz = z0
        while zz < z1 - 0.01:
            dz = min(0.5 + jit(0.12), z1 - zz)
            P.face([Vector((p0[0], p0[1], zz)), Vector((p1[0], p1[1], zz)), Vector((p1[0], p1[1], zz + dz)), Vector((p0[0], p0[1], zz + dz))], "kvadr_sedy")
            zz += dz


def arch_ring(P: Part, cx, spring, hw, z, depth, ring=0.42, n=13, pointed=0.0, mat="kvadr", outward=1):
    """Kamenne obloukove ostění (klenaky) na lici z. pointed > 0 = lomeny oblouk."""
    pts_in, pts_out = [], []
    for i in range(n + 1):
        t = i / n
        a = math.pi * (1 - t)
        if pointed > 0:
            # lomeny oblouk ze dvou kruznic
            r = hw * (1 + pointed)
            side = -1 if t < 0.5 else 1
            tt = t * 2 if t < 0.5 else (1 - t) * 2           # 0 u patky, 1 u vrcholu
            c0 = cx - side * (r - hw)                         # stred kruznice
            amax = math.acos((r - hw) / r)
            a = math.pi - amax * tt if side < 0 else amax * tt
            x = c0 + r * math.cos(a)
            y = spring + r * math.sin(a)
            xo = c0 + (r + ring) * math.cos(a)
            yo = spring + (r + ring) * math.sin(a)
        else:
            x = cx + hw * math.cos(a)
            y = spring + hw * math.sin(a)
            xo = cx + (hw + ring) * math.cos(a)
            yo = spring + (hw + ring) * math.sin(a)
        pts_in.append((x, y))
        pts_out.append((xo, yo))
    for i in range(n):
        q = [Vector((pts_in[i][0], pts_in[i][1], z)), Vector((pts_out[i][0], pts_out[i][1], z)),
             Vector((pts_out[i + 1][0], pts_out[i + 1][1], z)), Vector((pts_in[i + 1][0], pts_in[i + 1][1], z))]
        # zmensit klenak o sparu
        c = sum(q, Vector()) / 4
        q = [c + (p - c) * 0.96 for p in q]
        if outward > 0:
            q.reverse()
        P.prism(q, Vector((0, 0, -outward * depth)), mat)


def gatehouse(coll):
    P = Part("Brana", bevel=0.03)
    gx, z0, z1, pw, top = 3.5, 9.5, 17.0, 1.6, 10.6
    # piliře a zdivo nad prujezdem
    P.bb((-gx, BASE, z0), (-pw, WALK, z1), "zdivo", collide=True)
    P.bb((pw, BASE, z0), (gx, WALK, z1), "zdivo", collide=True)
    P.bb((-pw, 3.9 + 0.35, z0), (pw, WALK, z1), "zdivo", collide=True)
    vault_z(P, 0.0, z0, z1, pw, 2.3, 3.9 + 0.35)
    P.bb((-pw, -0.25, z0 - 0.5), (pw, 0.0, z1), "kocicky", collide=True)
    P.bb((-pw, BASE, IZ), (pw, -0.25, z1), "zdivo_hole")
    # kamenne ostění vjezdu na obou licich (pulkruhovy oblouk na kvadrovych patkach)
    for z, o in ((z1, 1), (z0, -1)):
        arch_ring(P, 0.0, 2.3, pw, z + o * 0.06, 0.5, 0.45, 15, outward=o)
        for sx in (-1, 1):
            y = 0.0
            k = 0
            while y < 2.3 - 0.01:
                hh = min(0.38, 2.3 - y)
                w = 0.5 if k % 2 == 0 else 0.32
                P.bb((sx * (pw - 0.015), y, z - o * 0.5), (sx * (pw + w), y + hh - 0.012, z + o * 0.06), "kvadr")
                y += hh
                k += 1
    # erbovni deska nad vjezdem
    P.bb((-0.55, 4.55, z1), (0.55, 5.85, z1 + 0.12), "kvadr")
    PR.shield(P, M((0, 5.25, z1 + 0.17), 180), "sukno_cervene", "bila")
    # dratka pro retezy padaciho mostu
    for sx in (-1, 1):
        P.box(M((sx * 1.9, 5.0, z1 + 0.01)), (0.16, 0.16, 0.02), "dira")
    # strazni svetnice v patre
    t = 0.8
    wall_x(P, "zdivo", -gx, gx, z1 - t, z1, WALK, top, [[-2.3, -1.5, 7.5, 8.9], [1.5, 2.3, 7.5, 8.9]])
    wall_x(P, "zdivo", -gx, gx, z0, z0 + t, WALK, top, [[-0.5, 0.5, 7.5, 8.8]])
    wall_z(P, "zdivo", z0 + t, z1 - t, -gx, -gx + t, WALK, top, [[14.1, 15.2, WALK, 8.6]])
    wall_z(P, "zdivo", z0 + t, z1 - t, gx - t, gx, WALK, top, [[14.1, 15.2, WALK, 8.6]])
    # narozi
    quoins(P, -gx, z1, 1, -1, BASE, top)
    quoins(P, gx, z1, -1, -1, BASE, top)
    quoins(P, -gx, z0, 1, 1, WALK, top)
    quoins(P, gx, z0, -1, 1, WALK, top)
    # kamenna ostění oken svetnice
    for cx in (-1.9, 1.9):
        _win_frame(P, cx, 0.8, 7.5, 8.9, z1, 1)
    _win_frame(P, 0.0, 1.0, 7.5, 8.8, z0, -1)
    # rimsa pod strechou
    P.bb((-gx - 0.12, top - 0.2, z0 - 0.12), (gx + 0.12, top, z1 + 0.12), "kvadr_sedy")
    P.commit(coll)

    W = Part("BranaDrevo", bevel=0.01)
    pyramid_roof(W, -gx - 0.55, gx + 0.55, z0 - 0.55, z1 + 0.55, top, (0, top + 4.8, (z0 + z1) / 2))
    W.bb((-gx + t, WALK, z0 + t), (gx - t, WALK + 0.04, z1 - t), "prkna", collide=True)
    for k in range(5):
        x = -2.6 + 1.3 * k
        W.beam((x, top - 0.14, z0 + 0.4), (x, top - 0.14, z1 - 0.4), 0.22, 0.26, "dub", j=1)
    W.bb((-gx + t, top - 0.04, z0 + t), (gx - t, top, z1 - t), "prkna")
    # dvere z ochozu do svetnice
    for sx in (-1, 1):
        x = sx * (gx - t / 2)
        W.bb((x - t / 2 - 0.02, 8.6, 14.0), (x + t / 2 + 0.02, 8.8, 15.3), "dub")
    # vrata: dve kridla otevrena dovnitr podel sten prujezdu, okovana
    for sx in (-1, 1):
        x = sx * (pw - 0.08)
        zz = 14.5
        while zz < 16.1:
            w = min(0.27, 16.1 - zz)
            W.bb((x - 0.05, 0.05, zz), (x + 0.05, 3.3, zz + w - 0.008), "dub", grain="y")
            zz += w
        for hy in (0.5, 1.6, 2.7):
            W.bb((x - sx * 0.06, hy - 0.06, 14.5), (x - sx * 0.07, hy + 0.06, 16.1), "zelezo")
            for k in range(6):
                W.ball((x - sx * 0.075, hy, 14.65 + 0.27 * k), (0.012, 0.018, 0.018), "zelezo", 6, 4)
        W.beam((x - sx * 0.08, 0.6, 14.6), (x - sx * 0.08, 2.6, 16.0), 0.04, 0.12, "dub")
    # padaci mriz (dubova s okovanymi hroty) vytazena
    zg = 16.55
    for k in range(9):
        x = -1.4 + 0.35 * k
        W.beam((x, 3.05, zg), (x, 4.6, zg), 0.09, 0.09, "dub")
        W.rod((x, 2.85, zg), (x, 3.06, zg), 0.0, 6, "zelezo", 0.045)
    for y in (3.3, 3.75, 4.2):
        W.beam((-1.5, y, zg - 0.06), (1.5, y, zg - 0.06), 0.09, 0.09, "dub")
    # padaci most: prvni dil u brany, zdvihaci retezy
    zb, zm = z1, z1 + 3.2
    _deck(W, zb, zm, 0.0, -0.05, 1.75, "prkna_ven")
    for sx in (-1, 1):
        W.beam((sx * 1.6, -0.25, zb), (sx * 1.6, -0.3, zm), 0.2, 0.22, "dub_ven")
        a = Vector((sx * 1.6, 0.25, zm - 0.1))
        b = Vector((sx * 1.9, 5.0, z1 + 0.05))
        _chain(W, a, b)
    W.commit(coll)


def _win_frame(P: Part, cx, w, y0, y1, z, o):
    """Kamenne ostění obdelnikoveho okna s parapetem a nadprazim."""
    P.bb((cx - w / 2 - 0.2, y0 - 0.16, z - o * 0.02), (cx + w / 2 + 0.2, y0, z + o * 0.1), "kvadr")
    P.bb((cx - w / 2 - 0.18, y1, z - o * 0.02), (cx + w / 2 + 0.18, y1 + 0.24, z + o * 0.07), "kvadr")
    for sx in (-1, 1):
        P.bb((cx + sx * w / 2, y0, z - o * 0.02), (cx + sx * (w / 2 + 0.16), y1, z + o * 0.06), "kvadr")


def _deck(P: Part, z0, z1, y0, y1, hw, mat):
    n = int((z1 - z0) / 0.27)
    for k in range(n):
        t = (k + 0.5) / n
        z = z0 + (z1 - z0) * t
        y = y0 + (y1 - y0) * t
        P.box(M((jit(0.02), y - 0.04, z), jit(0.8)), (hw * 2 + jit(0.06), 0.07, (z1 - z0) / n - 0.012), mat, collide=False)
    P.cols.append((M((0, (y0 + y1) / 2 - 0.1, (z0 + z1) / 2)), (hw * 2, 0.2, z1 - z0)))


def _chain(P: Part, a, b):
    d = b - a
    L = d.length
    n = int(L / 0.075)
    dn = d.normalized()
    for k in range(n):
        p = a + dn * (k + 0.5) * L / n
        sag = math.sin(math.pi * k / n) * 0.12
        p = p - Vector((0, sag, 0))
        P.lathe(M(p, basis=_frame_ring(dn, k % 2)), [(0.03, -0.012), (0.03, 0.012)], 8, "zelezo", False, False)


def _frame_ring(d, flip):
    from lib import frame
    f = frame(d, Vector((0, 1, 0)) if not flip else Vector((1, 0, 0)))
    # ocko retezu: osa Y kruhu kolma na smer retezu
    return f @ Matrix.Rotation(math.pi / 2, 3, "Z")


# ------------------------------------------------------------------ obytna vez

def tower(coll):
    P = Part("Vez", bevel=0.03)
    x0, x1, z0, z1 = -19.8, -11.8, -16.8, -8.8
    t, top = 1.5, 17.0
    ix0, ix1, iz0, iz1 = x0 + t, x1 - t, z0 + t, z1 - t
    wy0, wy1 = 13.95, 15.85
    wall_x(P, "zdivo", x0, x1, iz1, z1, BASE, top, [[-17.9, -16.7, WALK, 8.6], [-17.95, -16.45, wy0, wy1], [-15.15, -13.65, wy0, wy1],
                                                    [-15.1, -14.9, 2.2, 3.3], [-15.1, -14.9, 9.6, 10.9]])
    wall_x(P, "zdivo", x0, x1, z0, iz0, BASE, top, [[-15.95, -15.65, 8.0, 9.3], [-17.95, -16.45, wy0, wy1], [-15.15, -13.65, wy0, wy1]])
    wall_z(P, "zdivo", iz0, iz1, ix1, x1, BASE, top, [[-13.4, -12.2, 0.0, 2.1], [-14.9, -13.7, WALK, 8.6],
                                                     [-14.75, -13.25, wy0, wy1], [-12.35, -10.85, wy0, wy1]])
    wall_z(P, "zdivo", iz0, iz1, x0, ix0, BASE, top, [[-12.95, -12.65, 1.4, 2.6], [-12.95, -12.65, 8.0, 9.3],
                                                     [-14.75, -13.25, wy0, wy1], [-12.35, -10.85, wy0, wy1]])
    for (xa, za, sx, sz) in ((x0, z0, 1, 1), (x1, z0, -1, 1), (x0, z1, 1, -1), (x1, z1, -1, -1)):
        quoins(P, xa, za, sx, sz, BASE, top, 0.9, 0.5, 0.38)
    # rimsy: pod strechou a kordonove v urovni pater
    P.bb((x0 - 0.15, top - 0.22, z0 - 0.15), (x1 + 0.15, top, z1 + 0.15), "kvadr_sedy")
    for yy in (WALK - 0.2, 12.8):
        P.bb((x0 - 0.08, yy, z0 - 0.08), (x1 + 0.08, yy + 0.16, z1 + 0.08), "kvadr_sedy")
    # dalsi strilny v patrech
    for (xa, za, o) in ((-17.2, z0, -1), (-14.4, z0, -1)):
        P.bb((xa - 0.1, 3.0, za - 0.02 * o), (xa + 0.1, 4.2, za + 0.02 * o), "dira")
        P.bb((xa - 0.1, 9.8, za - 0.02 * o), (xa + 0.1, 11.0, za + 0.02 * o), "dira")
    for zz in (-14.0, -11.6):
        P.bb((x0 - 0.02, 3.0, zz - 0.1), (x0 + 0.02, 4.2, zz + 0.1), "dira")
        P.bb((x0 - 0.02, 9.8, zz - 0.1), (x0 + 0.02, 11.0, zz + 0.1), "dira")
    P.bb((x0 - 0.25, BASE, z0 - 0.25), (x1 + 0.25, -0.6, z1 + 0.25), "zdivo_hole")
    # ostění: dvere v prizemi (lomeny portal), strilny, okna vyhlidky
    _portal_x(P, x1, -12.8, 1.2, 2.1, 1)
    for cx in (-15.0,):
        window_slit(P, cx, 2.2, 3.3, face_z=z1, outward=1)
        window_slit(P, cx, 9.6, 10.9, face_z=z1, outward=1)
    for (wx, wz, o) in ((-17.2, z1, 1), (-14.4, z1, 1), (-17.2, z0, -1), (-14.4, z0, -1)):
        _win_frame(P, wx, 1.5, wy0, wy1, wz, o)
    for (wz, xf, o) in ((-14.0, x1, 1), (-11.6, x1, 1), (-14.0, x0, -1), (-11.6, x0, -1)):
        _win_frame_x(P, wz, 1.5, wy0, wy1, xf, o)
    putlogs(P, (x0, 0, z0 + 0.5), (x0, 0, z1 - 0.5), (-1, 0, 0), [1.0, 4.2, 9.0, 12.0], 2.2)
    putlogs(P, (x0 + 0.5, 0, z0), (x1 - 0.5, 0, z0), (0, 0, -1), [1.0, 4.2, 9.0, 12.0], 2.2)
    # podlaha prizemi
    P.bb((ix0, -0.25, iz0), (ix1, 0.0, iz1), "dlazba", collide=True)
    P.commit(coll)

    W = Part("VezDrevo", bevel=0.012)
    for fy in (WALK, 13.0):
        W.bb((ix0, fy - 0.1, -14.2), (ix1, fy, iz1), "prkna", collide=True)
        W.bb((ix0, fy - 0.1, iz0), (-17.2, fy, -14.2), "prkna", collide=True)
        for k in range(4):
            bz = -13.6 + 1.05 * k
            W.beam((ix0 - 0.2, fy - 0.24, bz), (ix1 + 0.2, fy - 0.24, bz), 0.22, 0.28, "dub", j=1)
        W.beam((-17.2, fy + 1.0, -14.2), (-14.5, fy + 1.0, -14.2), 0.08, 0.1, "dub", collide=True)
        W.beam((-17.2, fy + 0.5, -14.2), (-14.5, fy + 0.5, -14.2), 0.06, 0.08, "dub")
        for px in (-17.2, -15.85, -14.5):
            W.beam((px, fy, -14.2), (px, fy + 1.02, -14.2), 0.1, 0.1, "dub")
    for sy in (0.0, WALK):
        stairs(W, Vector((-17.75, sy, -11.3)), Vector((0, 0, -1)), 2.9, 3.25, 1.1, 16, "prkna")
        W.bb((ix0, sy + 3.15, iz0), (-17.2, sy + 3.25, -14.2), "prkna", collide=True)
        stairs(W, Vector((-17.2, sy + 3.25, -14.75)), Vector((1, 0, 0)), 3.9, 3.25, 1.1, 16, "prkna")
        W.beam((-17.2, sy - 0.05, -11.3), (-17.2, sy + 3.2, -14.2), 0.08, 0.26, "dub")
        W.beam((-17.2, sy + 0.95, -11.3), (-17.2, sy + 4.2, -14.2), 0.07, 0.09, "dub", collide=True)
        W.beam((-17.2, sy + 3.2, -14.2), (-13.3, sy + 6.45, -14.2), 0.08, 0.26, "dub")
        W.beam((-17.2, sy, -11.35), (-17.2, sy + 1.0, -11.35), 0.1, 0.1, "dub")
        W.beam((-17.2, sy + 3.25, -14.2), (-17.2, sy + 4.25, -14.2), 0.1, 0.1, "dub")
        W.beam((-17.3, sy, -14.3), (-17.3, sy + 3.15, -14.3), 0.14, 0.14, "dub")
    for k in range(4):
        bx2 = -17.6 + 1.2 * k
        W.beam((bx2, top - 0.2, z0 + 0.3), (bx2, top - 0.2, z1 - 0.3), 0.2, 0.26, "dub", j=1)
    # dvere prizemi: otevrene kridlo
    W.bb((ix1 - 0.05, 0.0, -12.2), (ix1 + 0.02, 2.05, -11.15), "dub", grain="y")
    pyramid_roof(W, x0 - 0.7, x1 + 0.7, z0 - 0.7, z1 + 0.7, top, ((x0 + x1) / 2, top + 7.0, (z0 + z1) / 2))
    W.commit(coll)
    # vybaveni veze
    V = Part("VezVybaveni", bevel=0.006)
    PR.barrel(V, M((-17.9, 0.0, -15.6)))
    PR.barrel(V, M((-17.1, 0.0, -15.7)), 0.3, 0.8)
    PR.crate(V, M((-14.5, 0.0, -15.6), 12))
    PR.sack(V, M((-15.4, 0.0, -15.7)))
    PR.chest(V, M((-14.6, WALK, -15.6), 0), 1.1)
    PR.bed(V, M((-13.9, WALK, -12.0), 0), 2.0, 1.0, cover="pytlovina")
    PR.weapon_rack(V, M((-16.0, 13.0, -15.65)), 1.6, 4)
    PR.stool(V, M((-15.0, 13.0, -10.6)))
    V.commit(coll)


def _win_frame_x(P: Part, cz, w, y0, y1, x, o):
    P.bb((x - o * 0.02, y0 - 0.16, cz - w / 2 - 0.2), (x + o * 0.1, y0, cz + w / 2 + 0.2), "kvadr")
    P.bb((x - o * 0.02, y1, cz - w / 2 - 0.18), (x + o * 0.07, y1 + 0.24, cz + w / 2 + 0.18), "kvadr")
    for sz in (-1, 1):
        P.bb((x - o * 0.02, y0, cz + sz * w / 2), (x + o * 0.06, y1, cz + sz * (w / 2 + 0.16)), "kvadr")


def _portal_x(P: Part, x, cz, w, h, o):
    """Kamenny portal s lomenym zaklenkem na lici kolmem na X."""
    for sz in (-1, 1):
        P.bb((x - o * 0.02, 0.0, cz + sz * w / 2), (x + o * 0.12, h - 0.25, cz + sz * (w / 2 + 0.22)), "kvadr")
    # preklad se zkosenym lomenym vykrojem: dve sikme desky
    for sz in (-1, 1):
        a = Vector((x + o * 0.05, h - 0.25, cz + sz * (w / 2 + 0.22)))
        P.beam(a, Vector((x + o * 0.05, h + 0.25, cz)), 0.17, 0.36, "kvadr", up=(0, 1, 0))
    P.bb((x - o * 0.02, h, cz - 0.25), (x + o * 0.12, h + 0.5, cz + 0.25), "kvadr")


def stairs(P: Part, start, d, run, rise, width, n, mat):
    """Schodiste: n stupnu od start (pata uprostred sirky) ve smeru d."""
    d = Vector(d).normalized()
    side = Vector((0, 1, 0)).cross(d).normalized()
    sd = run / n
    sh = rise / n
    for k in range(n):
        c = Vector(start) + d * (sd * (k + 0.5)) + Vector((0, sh * (k + 1) - 0.03, 0))
        P.box(M(c, basis=Matrix((side, Vector((0, 1, 0)), d)).transposed()), (width, 0.06, sd + 0.04), mat)
    ang = math.atan2(rise, run)
    c = Vector(start) + d * (run / 2) + Vector((0, rise / 2, 0))
    P.cols.append((M(c, basis=Matrix((side, Vector((0, 1, 0)), d)).transposed() @ Matrix.Rotation(-ang, 3, "X")), (width, 0.1, math.hypot(run, rise))))


# ------------------------------------------------------------------ schody na hradbu

def wall_stair(coll):
    P = Part("SchodyHradba", bevel=0.02)
    n = 36
    run, rise, w = 9.6, WALK, 1.4
    x_start = 14.2
    for k in range(n):
        x = x_start - run * (k + 1) / n
        y = rise * (k + 1) / n
        P.bb((x, 0.0, 12.5 - w / 2 + 0.05), (x + run / n + 0.03, y, 12.5 + w / 2 + 0.6), "zdivo")
        P.bb((x - 0.02, y - 0.06, 12.5 - w / 2), (x + run / n + 0.03, y + 0.02, 12.5 + w / 2 + 0.6), "kvadr_sedy")
    P.bb((3.5, 0.0, 11.8), (4.6, WALK, 14.0), "zdivo", collide=True)
    P.bb((3.5, WALK, 11.8), (4.6, WALK + 0.04, 14.0), "dlazba_hrad")
    # zidka do nadvori s kamennou kryci deskou
    for k in range(12):
        xa = x_start + 0.1 - (run + 0.1) * k / 12
        xb = x_start + 0.1 - (run + 0.1) * (k + 1) / 12
        ya = rise * (x_start - xa) / run
        yb = rise * (x_start - xb) / run
        P.prism([Vector((xa, 0.0, 11.8)), Vector((xa, max(0, ya) + 0.85, 11.8)), Vector((xb, yb + 0.85, 11.8)), Vector((xb, 0.0, 11.8))],
                                  Vector((0, 0, 0.25)), "zdivo")
    P.beam((x_start + 0.1, 0.9, 11.925), (4.6, WALK + 0.9, 11.925), 0.34, 0.08, "kvadr_sedy")
    P.bb((3.5, WALK, 11.8), (4.6, WALK + 0.85, 12.05), "zdivo", collide=True)
    P.cols.append((M((9.4, 3.25, 11.92), basis=Matrix.Rotation(math.atan2(rise, run), 3, "Z")), (11.0, 1.7, 0.25)))
    P.commit(coll)


# ------------------------------------------------------------------ most

def bridge(coll):
    P = Part("Most", bevel=0.01)
    z0, z1 = 20.2, 28.6
    y0, y1 = -0.05, land(0.0, z1) + 0.1
    hw = 1.75
    _deck(P, z0, z1, y0, y1, hw, "prkna_ven")
    for sx in (-1.3, 0.0, 1.3):
        P.beam((sx, y0 - 0.25, z0 - 0.1), (sx, y1 - 0.25, z1), 0.24, 0.3, "dub_ven", j=1)
    # pilire v prikopu (kozy)
    for t in (0.0, 0.45, 0.85):
        z = z0 + (z1 - z0) * t
        y = y0 + (y1 - y0) * t
        gy = land(0.0, z) - 0.4
        for sx in (-1.5, 1.5):
            P.beam((sx, gy, z), (sx, y - 0.3, z), 0.28, 0.28, "dub_ven", j=1)
        P.beam((-1.85, y - 0.5, z), (1.85, y - 0.5, z), 0.24, 0.26, "dub_ven", j=1)
        P.beam((-1.5, gy + 0.6, z), (1.5, y - 0.7, z), 0.14, 0.16, "dub_ven", j=1)
        P.beam((1.5, gy + 0.6, z), (-1.5, y - 0.7, z), 0.14, 0.16, "dub_ven", j=1)
    for sx in (-hw + 0.08, hw - 0.08):
        r0 = Vector((sx, y0, z0 + 0.15))
        r1 = Vector((sx, y1, z1 - 0.2))
        P.beam(r0 + Vector((0, 1.05, 0)), r1 + Vector((0, 1.05, 0)), 0.11, 0.12, "dub_ven", j=0.5)
        P.beam(r0 + Vector((0, 0.55, 0)), r1 + Vector((0, 0.55, 0)), 0.07, 0.09, "dub_ven", j=0.5)
        for k in range(6):
            p = r0.lerp(r1, k / 5)
            P.beam(p - Vector((0, 0.1, 0)), p + Vector((0, 1.12, 0)), 0.13, 0.13, "dub_ven", j=1)
    P.commit(coll)
