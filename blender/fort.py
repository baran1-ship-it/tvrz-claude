"""Opevneni: hradby s cimbuřím a ochozem, brana s padacim mostem, obytna vez, schody na hradbu, teren."""
import math

from mathutils import Matrix, Vector

import props as PR
import lib
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
    at = me.attributes.new("grass", "FLOAT", "POINT")
    vals = []
    for vv in me.vertices:
        c = vv.co
        x, z = c.x, -c.y
        d = rect_dist(x, z)
        road = abs(x) < 2.2 and z > 16
        g = 0.0 if road else 0.4 + 0.45 * smooth(0.5, 2.0, d)
        if land(x, z) < -2.45 and d < 13.0:
            g = 0.1          # bahnity breh a dno prikopu
        vals.append(g + jit(0.1))
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
            # pod budovami (vez, palac, straznice) zem zapustit, aby neprosvitala podlahou
            inside = any(a - 0.3 < x < b + 0.3 and c - 0.3 < z < d + 0.3 for a, b, c, d in
                         ((-19.8, -11.8, -16.8, -8.8), (-3.0, 18.8, -14.0, -7.0), (-12.0, -4.2, 8.5, 14.0)))
            verts.append((x, jit(0.025) - (0.4 if inside else 0.0), z))
    for i in range(n_x):
        for k in range(n_z):
            faces.append((idx[(i, k)], idx[(i, k + 1)], idx[(i + 1, k + 1)], idx[(i + 1, k)]))
    P.mesh(verts, faces, "zem")
    o = P.commit(coll)
    me = o.data
    at = me.attributes.new("grass", "FLOAT", "POINT")
    vals = []
    for vv in me.vertices:
        c = vv.co
        x, z = c.x, -c.y
        dp = min(path_dist(x, z, p) for p in paths)
        dw = min(IX - abs(x), IZ - abs(z))
        g = smooth(0.8, 2.6, dp) * 0.75 + (0.35 if dw < 1.2 else 0.0)
        vals.append(min(1.0, g) + jit(0.08))
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
    """Narozni kvadry: (x, z) = vnejsi roh, sx/sz = smer do zdi. Kazda vrstva je jeden nepravidelny tesany
    kamen (stridave dlouhou stranou na jedno a druhe lice), vystupuje z omitky o par centimetru."""
    import kit
    y = max(y0, -0.8)
    k = 0
    while y < y1 - 0.05:
        hh = min(h + jit(0.04), y1 - y)
        a = (long_ if k % 2 == 0 else short) * (1 + jit(0.08))
        b = (short if k % 2 == 0 else long_) * (1 + jit(0.08))
        pr = 0.035 + jit(0.015)
        cx = x - sx * pr + sx * (a + pr) / 2
        cz = z - sz * pr + sz * (b + pr) / 2
        kit.stone(P, M((cx, y + hh / 2, cz), jit(1.2)), (a + pr, hh - 0.014, b + pr), mat, cham=0.03, rough=0.015)
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


def buttress(P: Part, c, o, along, w=1.3, top=5.2, d0=1.25, d1=0.35):
    """Operny pilir: lichobeznikovy profil, sikma kryci deska z kvadru."""
    x, z = c
    ox, oz = o
    out = Vector((ox, 0, oz))
    side = Vector((1, 0, 0)) if along == "x" else Vector((0, 0, 1))
    base = Vector((x, 0, z))
    prof = [(0.0, BASE), (d0, BASE), (d0 * 0.8, 1.0), (d1, top - 0.6), (0.0, top + 0.4)]
    pts = [base + out * dd + Vector((0, yy, 0)) - side * (w / 2) for dd, yy in prof]
    nrm = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    if nrm.dot(side) < 0:
        pts.reverse()
    P.prism(pts, side * w, "zdivo")
    a = base + out * (d1 + 0.06) + Vector((0, top - 0.62, 0))
    b2 = base + out * 0.02 + Vector((0, top + 0.42, 0))
    P.beam(a, b2, w + 0.1, 0.12, "kvadr_sedy", up=out + Vector((0, 1, 0)))


def covered_walk(P: Part, W: Part, a, e, inward, wall_t=1.8, gal=0.85, miter_a=None, miter_e=None, w0=0.25):
    """Krytý ochoz: nizka kamenna zidka, na ni sloupky s prkennym bednenim a strilnami,
    pultova sindelova stříška sklonena do nadvori, nesena vnitrnimi sloupky na kraji ochozu."""
    a, e, inward = Vector(a), Vector(e), Vector(inward).normalized()
    ln = (e - a).length
    d = (e - a) / ln
    up = Vector((0, 1, 0))
    side = up.cross(d).normalized()
    bas = Matrix((side, up, d)).transposed()
    y0 = a.y

    # rohy hradby: konec ochozu seriznuty pod 45 stupni (miter), aby se strechy sousednich ochozu potkaly
    # v narozi a uzlabi; miter_a/miter_e = podelna souradnice vnejsiho rohu, w0 = odstup osy a-e od vnejsiho lice
    def ts(u, ovh=0.3):
        return miter_a + (w0 + u) if miter_a is not None else -ovh

    def te(u, ovh=0.3):
        return miter_e - (w0 + u) if miter_e is not None else ln + ovh

    def at(t, u, y):
        return a + d * t + inward * u + up * (y - y0)
    # kamenna zidka
    P.box(M((a + e) * 0.5 + up * 0.5, basis=bas), (0.5, 1.0, ln), "zdivo", collide=True)
    P.box(M((a + e) * 0.5 + up * 1.03, basis=bas), (0.6, 0.07, ln + 0.02), "kvadr_sedy")
    yb, yt = y0 + 1.06, y0 + 2.75
    outer = -inward * 0.16
    # sloupky a vaznice
    n = max(2, round(ln / 1.7) + 1)
    posts = [0.1 + (ln - 0.2) * i / (n - 1) for i in range(n)]
    for s_ in posts:
        p = a + d * s_
        W.beam(p + up * (yb - y0) + inward * 0.05, p + up * (yt - y0) + inward * 0.05, 0.16, 0.16, "dub_ven", j=1)
    W.beam(a + up * (yt - y0 + 0.08) + inward * 0.05, e + up * (yt - y0 + 0.08), 0.18, 0.16, "dub_ven", j=0.5)
    W.beam(a + up * (yb - y0 + 0.06) + inward * 0.05, e + up * (yb - y0 + 0.06) + inward * 0.05, 0.14, 0.12, "dub_ven", j=0.5)
    # prkenne bedneni se strilnami v kazdem druhem poli
    s_ = ts(-0.16, 0.0)
    s_end = te(-0.16, 0.0)
    while s_ < s_end - 0.02:
        w = min(0.2 + jit(0.04), s_end - s_)
        mid = s_ + w / 2
        bay = min(range(n - 1), key=lambda i: abs((posts[i] + posts[i + 1]) / 2 - mid)) if n > 1 else 0
        slot = bay % 2 == 1 and abs((posts[bay] + posts[bay + 1]) / 2 - mid) < 0.25
        c = a + d * mid + outer
        top = yt + jit(0.04)
        spans = [(yb, top)] if not slot else [(yb, y0 + 1.5), (y0 + 1.95, top)]
        for (ya, yb2) in spans:
            W.box(M(c + up * ((ya + yb2) / 2 - y0), basis=bas), (0.035, yb2 - ya, w - 0.012), "prkna_ven")
        s_ += w
    # vnitrni sloupky na kraji ochozu a strisky
    inner = inward * (wall_t - 0.25 + gal - 0.06)
    yi = y0 + 2.1
    m = max(2, round(ln / 1.9) + 1)
    for i in range(m):
        p = a + d * (0.12 + (ln - 0.24) * i / (m - 1)) + inner
        W.beam(p - up * 0.05, p + up * (yi - y0), 0.13, 0.13, "dub_ven", j=1)
        # pasova vzpera k vaznici
        W.beam(p + up * (yi - y0 - 0.5), p + up * (yi - y0 - 0.05) + d * (0.45 if i < m - 1 else -0.45), 0.09, 0.09, "dub_ven")
    W.beam(a + inner + up * (yi - y0 + 0.07), e + inner + up * (yi - y0 + 0.07), 0.16, 0.16, "dub_ven", j=0.5)
    # sedlova strecha (jako na budovach): hreben nad stredem ochozu, okapy nad bednenim a nad vnitrnimi sloupky
    u_out = -0.45
    u_in = inward.dot(inner) + 0.45
    u_mid = (u_out + u_in) * 0.5
    y_out, y_in = yt + 0.12, yi - 0.12
    y_r = max(y_out, y_in) + 0.95
    k = max(0.0, ts(u_in, 0.0))
    while k <= min(ln, te(u_in, 0.0)) + 0.01:
        p = a + d * min(k, ln - 0.05)
        W.beam(p + inward * u_out + up * (y_out - y0 - 0.1), p + inward * u_mid + up * (y_r - y0 - 0.1), 0.1, 0.14, "dub_ven", j=0.8)
        W.beam(p + inward * u_in + up * (y_in - y0 - 0.1), p + inward * u_mid + up * (y_r - y0 - 0.1), 0.1, 0.14, "dub_ven", j=0.8)
        k += 0.95
    W.beam(at(ts(u_mid), u_mid, y_r - 0.2), at(te(u_mid), u_mid, y_r - 0.2), 0.14, 0.16, "dub_ven", j=0.5)
    # vnejsi rovina (eave vnejsi, hreben) a vnitrni rovina
    shingle_roof(W, at(te(u_out), u_out, y_out), at(ts(u_out), u_out, y_out), at(ts(u_mid), u_mid, y_r), at(te(u_mid), u_mid, y_r), ridge=False)
    shingle_roof(W, at(ts(u_in), u_in, y_in), at(te(u_in), u_in, y_in), at(te(u_mid), u_mid, y_r), at(ts(u_mid), u_mid, y_r), ridge=True)
    # stitky z prken na koncich bez rohu (u vezi a brany)
    for t0, use in ((ts(0) + 0.02, miter_a is None), (te(0) - 0.02, miter_e is None)):
        if not use:
            continue
        n = 7
        for i in range(n):
            f = (i + 0.5) / n
            u = u_out + (u_in - u_out) * f
            yb_ = y_out if f < 0.5 else y_in
            ytop = yb_ + (y_r - yb_) * (1 - abs(f - 0.5) * 2)
            W.beam(at(t0, u, min(y_out, y_in) - 0.1), at(t0, u, ytop - 0.12), 0.035, (u_in - u_out) / n - 0.01, "prkna_ven", up=d)


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
    # dlazba na korune
    for a, b in [((-OX + 0.5, WALK, IZ), (-3.5, WALK + 0.04, OZ - 0.5)), ((3.5, WALK, IZ), (OX - 0.5, WALK + 0.04, OZ - 0.5)),
                 ((-OX + 0.5, WALK, -8.8), (-IX, WALK + 0.04, IZ)), ((IX, WALK, -7.0), (OX - 0.5, WALK + 0.04, IZ)),
                 ((-11.8, WALK, -OZ + 0.5), (-3.0, WALK + 0.04, -IZ))]:
        P.bb(a, b, "dlazba_hrad")
    # operaky na dlouhych vnejsich licich
    for (c, o, along) in (((-OX, -2.0), (-1, 0), "z"), ((-OX, 7.0), (-1, 0), "z"), ((OX, -1.0), (1, 0), "z"), ((OX, 8.0), (1, 0), "z"),
                          ((-11.0, OZ), (0, 1), "x"), ((11.0, OZ), (0, 1), "x")):
        buttress(P, c, o, along)
    # chrliče: kamenne zlabky z koruny ven
    for x in (-14.0, -8.0, 8.0, 14.0):
        P.bb((x - 0.12, WALK - 0.1, OZ - 0.05), (x + 0.12, WALK + 0.04, OZ + 0.45), "kvadr_sedy")

    G = Part("Ochozy", bevel=0.012)
    gallery(G, (-IX, WALK, IZ), (-3.5, WALK, IZ), (0, 0, -1))
    gallery(G, (4.7, WALK, IZ), (IX - 0.9, WALK, IZ), (0, 0, -1))
    gallery(G, (-IX, WALK, -8.8), (-IX, WALK, IZ - 0.9), (1, 0, 0))
    gallery(G, (IX, WALK, -7.0), (IX, WALK, IZ - 0.9), (-1, 0, 0))
    gallery(G, (-11.8, WALK, -IZ), (-3.0, WALK, -IZ), (0, 0, 1))
    G.bb((-IX, WALK - 0.08, IZ - 0.85), (-IX + 0.85, WALK - 0.01, IZ), "prkna_ven", collide=True)
    G.bb((IX - 0.85, WALK - 0.08, IZ - 0.85), (IX, WALK - 0.01, IZ), "prkna_ven", collide=True)
    # krytý ochoz misto cimburi
    covered_walk(P, G, (-OX, WALK, OZ - 0.25), (-3.5, WALK, OZ - 0.25), (0, 0, -1), miter_a=0.0)
    covered_walk(P, G, (3.5, WALK, OZ - 0.25), (OX, WALK, OZ - 0.25), (0, 0, -1), miter_e=OX - 3.5)
    covered_walk(P, G, (-OX + 0.25, WALK, -8.8), (-OX + 0.25, WALK, OZ - 0.5), (1, 0, 0), miter_e=OZ + 8.8)
    covered_walk(P, G, (OX - 0.25, WALK, -7.0), (OX - 0.25, WALK, OZ - 0.5), (-1, 0, 0), miter_e=OZ + 7.0)
    covered_walk(P, G, (-11.8, WALK, -OZ + 0.25), (-3.0, WALK, -OZ + 0.25), (0, 0, 1))
    P.commit(coll)
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
    # kamenne ostění vjezdu na obou licich: nepravidelne kvadry a pulkruhovy zaklenek z klenaku (kit)
    import kit
    for z, yaw in ((z1, 0), (z0, 180)):
        mm = M((0.0, 0.0, z), yaw)
        kit.stone_jambs(P, mm, 2 * pw, 2.3, 0.55, "kvadr", 0.07, 0.38)
        kit.stone_arch(P, mm, 2 * pw, 2.3, "pulkruh", 0.55, "kvadr", 0.45, 0.08, 13)
    # erbovni deska nad vjezdem
    P.bb((-0.55, 4.55, z1), (0.55, 5.85, z1 + 0.12), "kvadr")
    PR.shield(P, M((0, 5.25, z1 + 0.17), 180), "sukno_cervene", "bila")
    # dratka pro retezy padaciho mostu
    for sx in (-1, 1):
        P.box(M((sx * 1.9, 5.0, z1 + 0.01)), (0.16, 0.16, 0.02), "dira")
    # narozi kamenne casti
    quoins(P, -gx, z1, 1, -1, BASE, WALK)
    quoins(P, gx, z1, -1, -1, BASE, WALK)
    t = 0.8
    jt = 0.35
    W = Part("BranaDrevo", bevel=0.01)
    timber_storey(P, W, -gx, gx, z0, z1, WALK, top, jt,
                  {"S": [(1.55, 2.35, 7.55, 8.65, "okno"), (5.35, 6.15, 7.55, 8.65, "okno")],
                   "N": [(3.4, 4.3, 7.55, 8.65, "okno")],
                   "W": [(14.1 - (z0 - jt), 15.2 - (z0 - jt), WALK - 0.05, 8.6, "dvere")],
                   "E": [(14.1 - (z0 - jt), 15.2 - (z0 - jt), WALK - 0.05, 8.6, "dvere")]})
    P.commit(coll)

    pyramid_roof(W, -gx - jt - 0.6, gx + jt + 0.6, z0 - jt - 0.6, z1 + jt + 0.6, top + 0.2, (0, top + 5.6, (z0 + z1) / 2))
    # podlaha patra brany: prkna pres celou vylozenou plochu, v urovni ochozu (bez prahu)
    import kit
    kit.deck(W, (0, WALK - 0.025, z0 - jt + 0.04), (0, WALK - 0.025, z1 + jt - 0.04), gx + jt - 0.09, "prkna", worn=0.5,
             beams=(-2.6, -1.3, 0.0, 1.3, 2.6), plank_w=(0.22, 0.3), t=0.06)
    W.cols.append((M((0, WALK - 0.065, (z0 + z1) / 2)), (2 * (gx + jt), 0.2, z1 - z0 + 2 * jt)))
    for k in range(5):
        x = -2.6 + 1.3 * k
        W.beam((x, top - 0.14, z0 + 0.4), (x, top - 0.14, z1 - 0.4), 0.22, 0.26, "dub", j=1)
    W.bb((-gx - jt + 0.2, top - 0.04, z0 - jt + 0.2), (gx + jt - 0.2, top, z1 + jt - 0.2), "prkna")
    # vrata: dve okovana kridla (mrizove kovani) otevrena ke stenam prujezdu
    import kit
    for sx in (-1, 1):
        bas = Matrix(((0, 0, sx * 1), (0, 1, 0), (-sx * 1, 0, 0))).transposed() if False else None
        lx = Vector((0, 0, 1)) if sx > 0 else Vector((0, 0, -1))
        lz = Vector((-sx, 0, 0))
        basis = Matrix((lx, Vector((0, 1, 0)), lz)).transposed()
        kit.door_leaf(W, M((sx * (pw - 0.12), 0.02, 15.3), basis=basis), 1.6, 3.3, "hlavni", "rovny", lattice=True)
    W.commit(coll)
    gate_mechanisms(coll, gx, z0, z1, pw, jt)


DB_L = 5.0      # delka padaciho mostu (zbytek prikopu prekleni pevny most na kozach)


def gate_mechanisms(coll, gx, z0, z1, pw, jt):
    """Padaci most a mriz jako pohyblive dilky, navijaky v patre brany (pouziti u rucniho kola),
    vodici ram mrize na nadvorni strane brany s kladkami."""
    import kit
    S = Part("BranaMechanismy", bevel=0.01)
    # --- padaci most (otaci se kolem hrany brany, zdvih = zaporny uhel kolem X)
    Lb, wb = DB_L, 3.5
    eyes_local = [Vector((sx * (wb / 2 + 0.02), 0.0, Lb - 0.25)) for sx in (-1, 1)]
    anchors = [Vector((sx * 1.9, 5.0, z1 + 0.05)) for sx in (-1, 1)]
    kit.movable("most", "most", M((0.0, 0.0, z1)), lambda Q: kit.drawbridge(Q, Matrix.Identity(4), wb, Lb, 0.0),
                cols=[((0.0, -0.12, Lb / 2), (wb, 0.24, Lb))],
                group="most", open=-78.0, init=0.0, dur=7.0,
                chains=[[list(a_), list(e_)] for a_, e_ in zip(anchors, eyes_local)])
    # --- mriz na nadvorni strane: vodici ram, kladky, pohybliva mriz (posun nahoru)
    zp = z0 - 0.55
    wm, hm = 2 * pw + 0.2, 2.3 + pw + 0.2
    lift = 2.3 + pw + 0.15
    top_y = hm + lift + 0.45
    for sx in (-1, 1):
        x = sx * (wm / 2 + 0.12)
        S.beam((x, -0.05, zp), (x, top_y, zp), 0.2, 0.24, "dub_ven", j=0.5)
        # drazka: dve listy kolem mrize
        for dz in (-0.12, 0.12):
            S.beam((x - sx * 0.12, 0.0, zp + dz), (x - sx * 0.12, top_y - 0.1, zp + dz), 0.06, 0.05, "dub_ven")
        S.beam((x, 0.0, zp), (x, 0.0, zp), 0.3, 0.3, "kvadr_sedy")
        kit.stone(S, M((x, 0.12, zp)), (0.42, 0.24, 0.42), "kvadr_sedy", cham=0.03)
        # vzpery do zdi
        for yb in (3.0, 5.6):
            S.beam((x, yb, zp + 0.1), (x, yb + 0.5, z0 - 0.02), 0.12, 0.12, "dub_ven", j=0.5)
    S.beam((-wm / 2 - 0.35, top_y, zp), (wm / 2 + 0.35, top_y, zp), 0.24, 0.26, "dub_ven", j=0.5)
    pulleys = []
    for sx in (-1, 1):
        px = sx * wm * 0.36
        c = Vector((px, top_y - 0.3, zp))
        S.lathe(M(c) @ Matrix.Rotation(math.pi / 2, 4, "Z"), [(0.16, -0.04), (0.18, -0.03), (0.13, 0.0), (0.18, 0.03), (0.16, 0.04)], 14, "dub")
        S.rod(c + Vector((-0.08, 0, 0)), c + Vector((0.08, 0, 0)), 0.025, 6, "zelezo")
        S.beam(c + Vector((-0.07, 0, 0)), c + Vector((-0.07, 0.3, 0)), 0.03, 0.06, "zelezo")
        S.beam(c + Vector((0.07, 0, 0)), c + Vector((0.07, 0.3, 0)), 0.03, 0.06, "zelezo")
        pulleys.append(c + Vector((0, 0.0, 0.0)))
        # lano od kladky do zdi brany (do patra k navijaku)
        hole = Vector((px, top_y - 0.15, z0 - jt))
        S.rod(c + Vector((0, 0.16, 0)), hole, 0.016, 6, "lano")
    tops_local = [Vector((sx * wm * 0.36, hm + 0.1, 0.05)) for sx in (-1, 1)]
    kit.movable("mriz", "mriz", M((0.0, 0.0, zp)), lambda Q: kit.portcullis(Q, wm, hm),
                cols=[((0.0, hm / 2, 0.03), (wm, hm, 0.22))], group="mriz", lift=lift, init=lift, dur=6.0,
                ropes=[[list(p_), list(t_)] for p_, t_ in zip(pulleys, tops_local)])
    # --- navijaky v patre brany
    yd = WALK + 0.8
    for name, cz, grp in (("navijak_most", z1 - 0.9, "most"), ("navijak_mriz", z0 + 0.9, "mriz")):
        c = Vector((-0.2, yd, cz))
        kit.windlass_frame(S, c, 2.4, 0.8)
        kit.movable(name, "navijak", M(c), lambda Q: kit.windlass_drum(Q, 2.4, 0.2, 0.55, "zelezo" if grp == "most" else "lano"),
                    use=list(c + Vector((1.6, 0.2, 0.0))), group=grp, turns=6.0)
    # retezy mostu: od bubnu k otvorum ve zdi nad dratkami (pevne)
    for sx in (-1, 1):
        kit.chain(S, Vector((sx * 0.9, yd + 0.2, z1 - 0.9)), Vector((sx * 1.9, WALK - 0.02, z1 - 0.35)), sag=0.05)
    # lana mrize: od bubnu ke zdi na nadvorni strane
    for sx in (-1, 1):
        S.rod(Vector((sx * 0.9, yd + 0.2, z0 + 0.9)), Vector((sx * wm * 0.36, top_y - 0.15, z0 - jt + 0.05)), 0.016, 6, "lano")
    S.commit(coll)



def timber_storey(P: Part, W: Part, x0, x1, z0, z1, y0, y1, j, ops):
    """Vylozene hrazdene patro nad kamennym zdivem.
    ops: {'S'|'N'|'E'|'W': [(s0, s1, ya, yb, 'okno'|'dvere'), ...]}, s merene od rohu (x0-j / z0-j)."""
    from lib import half_timber, shutters_on
    tw = 0.22
    X0, X1, Z0, Z1 = x0 - j, x1 + j, z0 - j, z1 + j
    # zhlavi tramu (vyloženi) a obvodovy prah
    for (pa, pb, nrm) in (((X0, Z1), (X1, Z1), (0, 0, 1)), ((X0, Z0), (X1, Z0), (0, 0, -1)),
                          ((X0, Z0), (X0, Z1), (-1, 0, 0)), ((X1, Z0), (X1, Z1), (1, 0, 0))):
        a_, b_ = Vector((pa[0], 0, pa[1])), Vector((pb[0], 0, pb[1]))
        n = Vector(nrm)
        L = (b_ - a_).length
        d = (b_ - a_).normalized()
        k = 0.3
        while k < L - 0.2:
            p_ = a_ + d * k + Vector((0, y0 - 0.12, 0))
            W.beam(p_ - n * (j + 0.3), p_ + n * 0.1, 0.17, 0.2, "hraz", j=0.6)
            k += 0.62
        W.beam(a_ + Vector((0, y0 + 0.02, 0)) - n * 0.02, b_ + Vector((0, y0 + 0.02, 0)) - n * 0.02, 0.22, 0.22, "hraz", up=n)
    # zdi s otvory (vapenna omitka, hrazdeni na lici)
    def holes(side, base):
        return [[base + o[0], base + o[1], o[2], o[3]] for o in ops.get(side, [])]
    wall_x(P, "omitka_bila", X0, X1, Z1 - tw, Z1, y0, y1, holes("S", X0))
    wall_x(P, "omitka_bila", X0, X1, Z0, Z0 + tw, y0, y1, holes("N", X0))
    wall_z(P, "omitka_bila", Z0 + tw, Z1 - tw, X0, X0 + tw, y0, y1, holes("W", Z0))
    wall_z(P, "omitka_bila", Z0 + tw, Z1 - tw, X1 - tw, X1, y0, y1, holes("E", Z0))
    faces = {"S": ((X0, Z1), (X1, Z1), (0, 0, 1)), "N": ((X0, Z0), (X1, Z0), (0, 0, -1)),
             "W": ((X0, Z0), (X0, Z1), (-1, 0, 0)), "E": ((X1, Z0), (X1, Z1), (1, 0, 0))}
    for side, (pa, pb, nrm) in faces.items():
        a_, b_ = (pa[0], 0, pa[1]), (pb[0], 0, pb[1])
        oo = [(o[0], o[1], o[2], o[3]) for o in ops.get(side, [])]
        half_timber(W, a_, b_, nrm, y0 + 0.13, y1, oo)
        for o in ops.get(side, []):
            if o[4] == "okno":
                shutters_on(W, a_, b_, nrm, o[0], o[1], o[2], o[3], 110)
    # rohove sloupky
    for (xx, zz) in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)):
        W.beam((xx, y0 + 0.1, zz), (xx, y1, zz), 0.24, 0.24, "hraz", j=0.4)
    W.beam((X0, y1 + 0.08, Z1), (X1, y1 + 0.08, Z1), 0.22, 0.2, "hraz")
    W.beam((X0, y1 + 0.08, Z0), (X1, y1 + 0.08, Z0), 0.22, 0.2, "hraz")


def _win_frame(P: Part, cx, w, y0, y1, z, o):
    """Kamenne ostění obdelnikoveho okna s parapetem a nadprazim."""
    P.bb((cx - w / 2 - 0.2, y0 - 0.16, z - o * 0.02), (cx + w / 2 + 0.2, y0, z + o * 0.1), "kvadr")
    P.bb((cx - w / 2 - 0.18, y1, z - o * 0.02), (cx + w / 2 + 0.18, y1 + 0.24, z + o * 0.07), "kvadr")
    for sx in (-1, 1):
        P.bb((cx + sx * w / 2, y0, z - o * 0.02), (cx + sx * (w / 2 + 0.16), y1, z + o * 0.06), "kvadr")


def _deck(P: Part, z0, z1, y0, y1, hw, mat):
    import kit
    # ochozena prkna (kit): stopa uprostred, ruzne odstiny, mezery, hreby nad tramy
    kit.deck(P, (0, y0 - 0.065, z0), (0, y1 - 0.065, z1), hw, mat, worn=1.0, beams=(-1.3, 0.0, 1.3))
    # kolize sklonena s mostovkou (rovna krabice delala na konci schod)
    ang = math.atan2(y1 - y0, z1 - z0)
    P.cols.append((M((0, (y0 + y1) / 2 - 0.1, (z0 + z1) / 2), basis=Matrix.Rotation(-ang, 3, "X")), (hw * 2, 0.2, math.hypot(z1 - z0, y1 - y0))))


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
    st = 13.0          # kamenna cast; nad ni vylozene hrazdene patro
    S = "zdivo_bile"
    wall_x(P, S, x0, x1, iz1, z1, BASE, st, [[-17.9, -16.7, WALK, 8.6], [-15.1, -14.9, 2.2, 3.3], [-15.1, -14.9, 9.6, 10.9]])
    wall_x(P, S, x0, x1, z0, iz0, BASE, st, [[-15.95, -15.65, 8.0, 9.3]])
    wall_z(P, S, iz0, iz1, ix1, x1, BASE, st, [[-13.4, -12.2, 0.0, 2.1], [-14.9, -13.7, WALK, 8.6]])
    wall_z(P, S, iz0, iz1, x0, ix0, BASE, st, [[-12.95, -12.65, 1.4, 2.6], [-12.95, -12.65, 8.0, 9.3]])
    for (xa, za, sx, sz) in ((x0, z0, 1, 1), (x1, z0, -1, 1), (x0, z1, 1, -1), (x1, z1, -1, -1)):
        quoins(P, xa, za, sx, sz, BASE, st, 0.9, 0.5, 0.38)
    W = Part("VezDrevo", bevel=0.012)
    jt = 0.4
    wo = [(0.95, 1.9, 14.1, 15.3, "okno"), (3.75, 4.7, 14.1, 15.3, "okno"), (6.55, 7.5, 14.1, 15.3, "okno")]
    timber_storey(P, W, x0, x1, z0, z1, st, top, jt, {"S": wo, "N": wo, "E": wo, "W": wo})
    # kordonove rimsy v urovni pater
    # (jen pasy na vnejsich licich - drive plna deska pres celou vez zakryvala otvor nad schody)
    for yy in (WALK - 0.2,):
        for a_, b_ in (((x0 - 0.08, z0 - 0.08), (x1 + 0.08, z0 + 0.1)), ((x0 - 0.08, z1 - 0.1), (x1 + 0.08, z1 + 0.08)),
                       ((x0 - 0.08, z0 - 0.08), (x0 + 0.1, z1 + 0.08)), ((x1 - 0.1, z0 - 0.08), (x1 + 0.08, z1 + 0.08))):
            P.bb((a_[0], yy, a_[1]), (b_[0], yy + 0.16, b_[1]), "kvadr_sedy")
    # dalsi strilny v patrech
    for (xa, za, o) in ((-17.2, z0, -1), (-14.4, z0, -1)):
        P.bb((xa - 0.1, 3.0, za - 0.02 * o), (xa + 0.1, 4.2, za + 0.02 * o), "dira")
        P.bb((xa - 0.1, 9.8, za - 0.02 * o), (xa + 0.1, 11.0, za + 0.02 * o), "dira")
    for zz in (-14.0, -11.6):
        P.bb((x0 - 0.02, 3.0, zz - 0.1), (x0 + 0.02, 4.2, zz + 0.1), "dira")
        P.bb((x0 - 0.02, 9.8, zz - 0.1), (x0 + 0.02, 11.0, zz + 0.1), "dira")
    P.bb((x0 - 0.25, BASE, z0 - 0.25), (x1 + 0.25, -0.6, z1 + 0.25), "zdivo_hole")
    # ostění: dvere v prizemi (lomeny portal), strilny, okna vyhlidky
    import kit
    kit.doorway(P, M((x1, 0.0, -12.8), 90), "obycejne", 1.2, 2.1, t, "segment", open_deg=80)
    for cx in (-15.0,):
        window_slit(P, cx, 2.2, 3.3, face_z=z1, outward=1)
        window_slit(P, cx, 9.6, 10.9, face_z=z1, outward=1)
    # podlaha prizemi
    P.bb((ix0, -0.25, iz0), (ix1, 0.0, iz1), "dlazba", collide=True)
    P.commit(coll)

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
        # zabradli druheho ramene (strana do mistnosti)
        # (konci pred vystupem: horni cast ramene je volna, vystupuje se do strany na podlahu)
        xe = -14.6
        ye = sy + 3.25 + 3.25 * (xe + 17.2) / 3.9
        W.beam((-17.2, sy + 4.25, -14.18), (xe, ye + 1.0, -14.18), 0.07, 0.09, "dub", collide=True)
        W.beam((-17.2, sy + 3.75, -14.18), (xe, ye + 0.5, -14.18), 0.05, 0.07, "dub")
        for k in range(1, 4):
            px = -17.2 + (xe + 17.2) * k / 3
            py = sy + 3.25 + 3.25 * (px + 17.2) / 3.9
            W.beam((px, py - 0.05, -14.18), (px, py + 1.0, -14.18), 0.08, 0.08, "dub")
    # horni patro: prkenna podlaha pres celou vylozenou plochu (bez mezery ke zdi), otvor nad schody
    import kit
    yd = 12.99
    for (xa, xb, za, zb) in ((x0 - jt + 0.04, x1 + jt - 0.04, z0 - jt + 0.04, iz0), (x0 - jt + 0.04, x1 + jt - 0.04, -14.2, z1 + jt - 0.04),
                             (x0 - jt + 0.04, -17.2, iz0, -14.2)):
        kit.deck(W, ((xa + xb) / 2, yd, za), ((xa + xb) / 2, yd, zb), (xb - xa) / 2 - 0.04, "prkna", worn=0.3,
                 beams=(), plank_w=(0.2, 0.28), t=0.05)
        W.cols.append((M(((xa + xb) / 2, yd - 0.06, (za + zb) / 2)), (xb - xa, 0.2, zb - za)))
    for k in range(4):
        bx2 = -17.6 + 1.2 * k
        W.beam((bx2, top - 0.2, z0 + 0.3), (bx2, top - 0.2, z1 - 0.3), 0.2, 0.26, "dub", j=1)
    pyramid_roof(W, x0 - jt - 0.7, x1 + jt + 0.7, z0 - jt - 0.7, z1 + jt + 0.7, top + 0.2, ((x0 + x1) / 2, top + 8.0, (z0 + z1) / 2))
    W.commit(coll)
    # vybaveni veze
    if not lib.VYBAVENI:
        return
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
    """Schodiste: n stupnu od start (pata uprostred sirky) ve smeru d. Stupne ze dvou prken (kit.plank),
    pod nimi dve sikme schodnice z tramu."""
    import kit
    d = Vector(d).normalized()
    up_ = Vector((0, 1, 0))
    side = up_.cross(d).normalized()
    sd = run / n
    sh = rise / n
    for k in range(n):
        base = Vector(start) + up_ * (sh * (k + 1) - 0.055)
        for j, (a0, a1) in enumerate(((0.0, 0.52), (0.5, 1.0))):
            c0 = base + d * (sd * k + (sd + 0.05) * a0)
            c1 = base + d * (sd * k + (sd + 0.05) * a1)
            cm = (c0 + c1) / 2
            pw = (c1 - c0).length - 0.008
            kit.plank(P, cm - side * (width / 2 + kit.J(0.02)), cm + side * (width / 2 + kit.J(0.02)), pw, 0.05, mat, up=up_, wear=0.7,
                      seg_len=0.3)
    for sx in (-1, 1):
        o = side * sx * (width / 2 - 0.06)
        P.beam(Vector(start) + o - up_ * 0.12, Vector(start) + o + d * run + up_ * (rise - 0.12), 0.08, 0.24, "dub", j=0.5)
    ang = math.atan2(rise, run)
    c = Vector(start) + d * (run / 2) + Vector((0, rise / 2, 0))
    P.cols.append((M(c, basis=Matrix((side, Vector((0, 1, 0)), d)).transposed() @ Matrix.Rotation(-ang, 3, "X")), (width, 0.1, math.hypot(run, rise))))


# ------------------------------------------------------------------ schody na hradbu

def wall_stair(coll):
    """Kamenne schodiste na hradbu podel jizni zdi: dve ramena s podestou uprostred, cele mimo pavlac
    a strechu ochozu (pas z 10.8..12.55), nahore plosina napojena na ochoz u brany."""
    import kit
    P = Part("SchodyHradba", bevel=0.02)
    za, zb = 10.82, 12.55          # pochozi sirka schodu
    zw = za - 0.27                 # zidka do nadvori
    n1 = 17
    rise = WALK
    sh = rise / (2 * n1)
    sd = 0.27
    land = 1.3
    x_top = 6.0                    # siroka horni podesta u brany (3.5..6.0)
    x_land1 = x_top + n1 * sd            # horni rameno: x_top .. x_land1
    x_land0 = x_land1 + land             # podesta
    x_bot = x_land0 + n1 * sd            # dolni rameno: x_land0 .. x_bot

    def prof(x):
        """Vyska pochozi plochy v miste x."""
        if x >= x_bot:
            return 0.0
        if x >= x_land0:
            return rise / 2 * (x_bot - x) / (x_bot - x_land0)
        if x >= x_land1:
            return rise / 2
        return rise / 2 + rise / 2 * (x_land1 - x) / (x_land1 - x_top)
    steps = [(x_bot - sd * (k + 1), sh * (k + 1)) for k in range(n1)] + [(x_land1 - sd * (k + 1), rise / 2 + sh * (k + 1)) for k in range(n1)]
    for x, y in steps:
        P.bb((x, 0.0, za + 0.02), (x + sd + 0.03, y - 0.08, zb + 0.05), "zdivo")
        kit.stone(P, M((x + sd / 2, y - 0.045, (za + zb) / 2 + 0.03)), (sd + 0.05, 0.1, zb - za + 0.06), "kvadr_sedy", cham=0.02)
    # podesta
    P.bb((x_land1, 0.0, za + 0.02), (x_land0 + 0.03, rise / 2 - 0.08, zb + 0.05), "zdivo")
    kit.stone(P, M(((x_land1 + x_land0) / 2, rise / 2 - 0.045, (za + zb) / 2 + 0.03)), (land + 0.04, 0.1, zb - za + 0.06), "kvadr_sedy", cham=0.02)
    P.cols.append((M(((x_land1 + x_land0) / 2, rise / 2 - 0.1, (za + zb) / 2)), (land, 0.2, zb - za)))
    # horni plosina u brany, napojena na ochoz a pavlac
    P.bb((3.5, 0.0, zw), (x_top, WALK, 14.0), "zdivo", collide=True)
    P.bb((3.5, WALK, zw), (x_top, WALK + 0.04, 14.0), "dlazba_hrad")
    # zidka do nadvori s kamennou kryci deskou (sleduje profil schodu)
    xs = [x_bot + 0.1] + [x_bot - (x_bot - x_top) * k / 24 for k in range(1, 25)]
    for xa_, xb_ in zip(xs, xs[1:]):
        ya, yb = prof(xa_), prof(xb_)
        P.prism([Vector((xa_, 0.0, zw)), Vector((xa_, ya + 0.85, zw)), Vector((xb_, yb + 0.85, zw)), Vector((xb_, 0.0, zw))], Vector((0, 0, 0.25)), "zdivo")
        P.beam(Vector((xa_ + 0.01, ya + 0.89, zw + 0.125)), Vector((xb_ - 0.01, yb + 0.89, zw + 0.125)), 0.34, 0.08, "kvadr_sedy")
    P.bb((3.5, WALK, zw), (x_top, WALK + 0.85, zw + 0.25), "zdivo", collide=True)
    # kolize: ramena jako sikme rampy, zidka jako steny
    for (x0_, x1_, y0_, y1_) in ((x_land0, x_bot, rise / 2, 0.0), (x_top, x_land1, rise, rise / 2)):
        ang = math.atan2(abs(y1_ - y0_), x1_ - x0_)
        L = math.hypot(x1_ - x0_, y1_ - y0_)
        cy = (y0_ + y1_) / 2
        P.cols.append((M(((x0_ + x1_) / 2, cy - 0.05, (za + zb) / 2), basis=Matrix.Rotation(-ang, 3, "Z")), (L + 0.2, 0.1, zb - za)))
        P.cols.append((M(((x0_ + x1_) / 2, cy + 0.45, zw + 0.125), basis=Matrix.Rotation(-ang, 3, "Z")), (L + 0.2, 1.7, 0.25)))
    P.commit(coll)


# ------------------------------------------------------------------ most

def bridge(coll):
    P = Part("Most", bevel=0.01)
    z0, z1 = 17.0 + DB_L, 28.6
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
