# -*- coding: utf-8 -*-
"""Tesařské pomůcky: otesaný trám s oblinou a sraženými hranami, kolíky, čepy, železné pásy.
Načítá se přes exec() po _spolecne.py (potřebuje Mesh, M, box, random, math, np, Vector, Matrix)."""

def frame_axes(p0, p1, up=(0, 0, 1)):
    d = Vector(p1) - Vector(p0); Ln = d.length; X = d / Ln
    U = Vector(up); Z = U - X * U.dot(X)
    if Z.length < 1e-4:
        U = Vector((1, 0, 0)) if abs(X.x) < 0.9 else Vector((0, 1, 0)); Z = U - X * U.dot(X)
    Z.normalize(); Y = Z.cross(X)
    return X, Y, Z, Ln

def hbeam(Ms, p0, p1, w, h, key="tram", up=(0, 0, 1), w1=None, h1=None, ch=0.018, wane=0.30, bow=0.010,
          seglen=0.5, caps=(True, True), capkey="zhlavi", jitter=0.004, wanekey="kura", octa=False):
    """Otesaný trám: průřez w (osa Y) × h (osa Z), od p0 do p1. Hrany sražené sekerou (ch), náhodně oblina
    (zbytek kulatiny s kůrou) na části délky, plochy po tesání mírně zvlněné, celý trám lehce prohnutý.
    octa=True: osmiboký (sloup, hřídel)."""
    p0 = Vector(p0); p1 = Vector(p1)
    X, Y, Z, Ln = frame_axes(p0, p1, up)
    w1 = w if w1 is None else w1; h1 = h if h1 is None else h1
    ns = max(1, int(math.ceil(Ln / seglen)))
    mn = min(w, h, w1, h1)
    cb = [ch * random.uniform(0.6, 1.5) for _ in range(4)]
    if octa: cb = [mn * 0.29] * 4
    wn = []
    for k in range(4):
        if (not octa) and random.random() < wane:
            a = random.uniform(0.0, 0.6); b = min(1.0, a + random.uniform(0.25, 0.7))
            wn.append((a, b, random.uniform(0.18, 0.32) * mn))
        else:
            wn.append(None)
    bz, by = random.uniform(-bow, bow), random.uniform(-bow, bow)
    ou, ov = random.random() * 4, random.random() * 4
    rings = []; cks = []
    for j in range(ns + 1):
        t = j / ns
        hw = (w + (w1 - w) * t) / 2; hh = (h + (h1 - h) * t) / 2
        e = 0.0 if j in (0, ns) else 1.0
        dyp, dym, dzp, dzm = [random.uniform(-jitter, jitter) * e for _ in range(4)]
        c = []
        for k in range(4):
            cc = cb[k]
            if wn[k]:
                a, b, am = wn[k]
                if a <= t <= b:
                    s_ = min(1.0, min(t - a, b - t) / 0.08 + 0.15)
                    cc = cc + am * s_
            c.append(min(cc, 0.46 * min(hw, hh) * 2))
        cks.append(c)
        P = [(hw + dyp, hh + dzp - c[0]), (hw + dyp - c[0], hh + dzp),
             (-hw - dym + c[1], hh + dzp), (-hw - dym, hh + dzp - c[1]),
             (-hw - dym, -hh - dzm + c[2]), (-hw - dym + c[2], -hh - dzm),
             (hw + dyp - c[3], -hh - dzm), (hw + dyp, -hh - dzm + c[3])]
        cen = p0 + X * (Ln * t) + Z * (bz * math.sin(math.pi * t)) + Y * (by * math.sin(math.pi * t))
        rings.append([cen + Y * py + Z * pz for (py, pz) in P])
    for j in range(ns):
        per = [0.0]
        for k in range(8):
            per.append(per[-1] + (rings[j][(k + 1) % 8] - rings[j][k]).length)
        v0 = Ln * j / ns / 0.75 + ov; v1 = Ln * (j + 1) / ns / 0.75 + ov
        for k in range(8):
            k2 = (k + 1) % 8
            q = [rings[j][k], rings[j][k2], rings[j + 1][k2], rings[j + 1][k]]
            kk = key
            if k % 2 == 0 and not octa:
                corner = k // 2
                if wn[corner] and cks[j][corner] > cb[corner] + 0.3 * wn[corner][2]:
                    kk = wanekey
            Ms.face(q, [(per[k] / 0.75 + ou, v0), (per[k + 1] / 0.75 + ou, v0), (per[k + 1] / 0.75 + ou, v1), (per[k] / 0.75 + ou, v1)], kk)
    for (ring, rev, on) in ((rings[0], True, caps[0]), (rings[-1], False, caps[1])):
        if not on: continue
        cen = sum(ring, Vector()) / 8
        pts = ring[::-1] if rev else ring
        Ms.face(pts, [(((p - cen).dot(Y)) / 0.35 + ou, ((p - cen).dot(Z)) / 0.35 + ov) for p in pts], capkey)
    return X, Y, Z, Ln

def peg(Ms, pos, n, r=0.016, proud=0.010, key="dub"):
    """dřevěný kolík: hranatá hlava vyčnívající z plochy"""
    n = Vector(n).normalized(); pos = Vector(pos)
    a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
    u = (a - n * a.dot(n)).normalized(); v = n.cross(u)
    rot = random.uniform(0, 1.57)
    b0 = [pos - n * 0.012 + (u * math.cos(rot + i * math.pi / 2) + v * math.sin(rot + i * math.pi / 2)) * r * 1.2 for i in range(4)]
    b1 = [p + n * (0.012 + proud) for p in b0]
    for i in range(4):
        i2 = (i + 1) % 4
        Ms.face([b0[i], b0[i2], b1[i2], b1[i]], [(0, 0), (0.05, 0), (0.05, 0.03), (0, 0.03)], key)
    Ms.face(b1, [(0.5 + i * 0.02, 0.5) for i in range(4)], "zhlavi")

def pegs_at(Ms, c, n, along, count=2, spacing=0.07, **kw):
    along = Vector(along).normalized()
    for i in range(count):
        o = (i - (count - 1) / 2) * spacing
        peg(Ms, Vector(c) + along * o + along.cross(Vector(n)).normalized() * random.uniform(-0.01, 0.01), n, **kw)

def strap(Ms, c, X, Y, Z, w, h, bw=0.055, t=0.007, bolts=True):
    """železný pás kolem trámu (střed c, osy rámu trámu, průřez w×h)"""
    c = Vector(c)
    Rm = Matrix((X, Y, Z)).transposed()
    for (dy, dz, sy, sz) in ((0, h / 2 + t / 2, w + 2 * t, t), (0, -h / 2 - t / 2, w + 2 * t, t), (w / 2 + t / 2, 0, t, h), (-w / 2 - t / 2, 0, t, h)):
        box(Ms, c + Y * dy + Z * dz, (bw, sy, sz), Rm, "zelezo", uvs=0.3)
    # nýty: hlavy na všech čtyřech stranách pásu
    for (n, span) in ((Z, w), (-Z, w), (Y, h), (-Y, h)):
        other = Y if n in (Z, -Z) else Z
        half = (h if n in (Z, -Z) else w) / 2 + t
        for o in ((-span * 0.3, span * 0.3) if span > 0.12 else (0.0,)):
            rv = c + n * half + other * o
            box(Ms, rv + n * 0.004, (0.022, 0.022 if n in (Z, -Z) else 0.008, 0.008 if n in (Z, -Z) else 0.022), Rm, "zelezo", uvs=0.2)
    if bolts:
        for dz in (-h * 0.25, h * 0.25):
            box(Ms, c + Y * (w / 2 + t + 0.010) + Z * dz, (0.034, 0.020, 0.034), Rm, "zelezo", uvs=0.3)

def tenon_end(Ms, c, out, along, w, h, length=0.06, key="dub"):
    """konec průchozího čepu vyčnívající z trámu, s klínem"""
    out = Vector(out).normalized(); along = Vector(along).normalized(); side = out.cross(along)
    Rm = Matrix((out, along, side)).transposed()
    box(Ms, Vector(c) + out * (length / 2), (length, w, h), Rm, key, uvs=0.4)
    box(Ms, Vector(c) + out * (length * 0.55), (0.025, w * 1.25, 0.022), Rm, "tram_d", uvs=0.3)

def iron_plate(Ms, c, n, u, size_u, size_v, nrv=2):
    """kovaný plech (úhelník/ploška) na ploše trámu s nýty"""
    n = Vector(n).normalized(); u = Vector(u).normalized(); v = n.cross(u)
    Rm = Matrix((u, v, n)).transposed()
    box(Ms, Vector(c) + n * 0.004, (size_u, size_v, 0.008), Rm, "zelezo", uvs=0.2)
    for i in range(nrv):
        for j in (-1, 1):
            rv = Vector(c) + u * ((i - (nrv - 1) / 2) * size_u * 0.7 / max(1, nrv - 1) if nrv > 1 else 0) + v * (j * size_v * 0.28) + n * 0.011
            box(Ms, rv, (0.02, 0.02, 0.008), Rm, "zelezo", uvs=0.2)
