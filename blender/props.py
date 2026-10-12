"""Vybaveni tvrze: nabytek, nadobi, nastroje, zbrane. Vse v souradnicich hry.

Kazda funkce bere Part a transformaci m (Matrix 4x4, lokalni Y nahoru, lokalni -Z = 'predek').
"""
import math

from mathutils import Matrix, Vector

from lib import M, R, jit, rot


def T(m, p):
    return m @ Vector(p)


def bx(P, m, c, size, mat, yaw=0.0, basis=None, collide=False):
    """Kvadr v lokalnich souradnicich predmetu."""
    lm = M(c, yaw, basis)
    P.box(m @ lm, size, mat, collide=collide)


def beam(P, m, a, b, w, h, mat="dub", j=0.0):
    P.beam(T(m, a), T(m, b), w, h, mat, up=(m.to_3x3() @ Vector((0, 1, 0))), j=j)


# ---------------------------------------------------------------- nabytek

def table(P, m, length=2.0, width=0.85, h=0.78, mat="deska"):
    """Stul na kozach: silna deska, dve kozy s kosymi nohami, rozpera."""
    t = 0.07
    bx(P, m, (0, h - t / 2, 0), (width, t, length), mat, collide=True)
    for sz in (-1, 1):
        z = sz * (length * 0.5 - 0.3)
        bx(P, m, (0, h - t - 0.05, z), (width - 0.1, 0.1, 0.1), "dub", yaw=90)
        for sx in (-1, 1):
            beam(P, m, (sx * (width * 0.5 - 0.06), 0, z + sz * 0.04), (sx * 0.15, h - t - 0.08, z), 0.08, 0.08, "dub", 0.5)
    beam(P, m, (0, 0.28, -length * 0.5 + 0.3), (0, 0.28, length * 0.5 - 0.3), 0.07, 0.09, "dub")


def bench(P, m, length=2.0, h=0.45, w=0.3):
    bx(P, m, (0, h - 0.03, 0), (w, 0.06, length), "deska", collide=True)
    for sz in (-1, 1):
        z = sz * (length * 0.5 - 0.22)
        for sx in (-1, 1):
            beam(P, m, (sx * w * 0.42, 0, z + sz * 0.05), (sx * w * 0.2, h - 0.06, z), 0.05, 0.05, "dub", 0.6)


def stool(P, m, h=0.45):
    P.cyl(m @ M((0, h - 0.05, 0)), 0.19, 0.19, 0.05, 14, "deska")
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.3
        beam(P, m, (math.cos(a) * 0.2, 0, math.sin(a) * 0.2), (math.cos(a) * 0.1, h - 0.05, math.sin(a) * 0.1), 0.04, 0.04, "dub")


def chair(P, m, h=0.47):
    """Tezka zidle s vysokou operadlovou deskou (predek = -Z)."""
    s = 0.48
    bx(P, m, (0, h - 0.03, 0), (s, 0.05, s), "deska")
    for sx in (-1, 1):
        for sz in (-1, 1):
            top = h if sz < 0 else 1.15
            bx(P, m, (sx * (s / 2 - 0.03), top / 2, sz * (s / 2 - 0.03)), (0.05, top, 0.05), "dub")
    bx(P, m, (0, 0.85, s / 2 - 0.03), (s - 0.04, 0.5, 0.025), "deska")
    bx(P, m, (0, 1.13, s / 2 - 0.03), (s + 0.04, 0.06, 0.06), "dub")
    for sx in (-1, 1):
        bx(P, m, (sx * (s / 2 - 0.03), 0.15, 0), (0.035, 0.035, s - 0.05), "dub")
    bx(P, m, (0, 0.15, -s / 2 + 0.03), (s - 0.05, 0.035, 0.035), "dub")


def chest(P, m, length=1.1, depth=0.55, h=0.55, open_=False):
    """Truhla z fosen se zelezným kovanim a zamkem."""
    bx(P, m, (0, h * 0.45, 0), (length, h * 0.9, depth), "deska", yaw=90, collide=True)
    # vika (mirne klenute)
    for k in range(4):
        a0 = -0.5 + k / 4.0
        y = h * 0.9 + 0.05 * math.cos(a0 * 2.2)
        bx(P, m, (0, y, (a0 + 0.125) * depth * 0.98), (length + 0.02, 0.04, depth / 4 + 0.01), "deska", yaw=0)
    # kovani
    for x in (-length * 0.32, 0, length * 0.32):
        for sz in (-1, 1):
            bx(P, m, (x, h * 0.5, sz * (depth / 2 + 0.005)), (0.05, h * 0.98, 0.008), "zelezo")
        bx(P, m, (x, h * 0.94, 0), (0.05, 0.008, depth + 0.02), "zelezo")
    for sx in (-1, 1):
        bx(P, m, (sx * (length / 2 + 0.005), h * 0.45, 0), (0.008, 0.06, depth * 0.9), "zelezo")
    bx(P, m, (0, h * 0.7, -depth / 2 - 0.012), (0.12, 0.14, 0.02), "zelezo")
    # nozky
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(P, m, (sx * (length / 2 - 0.06), 0.02, sz * (depth / 2 - 0.06)), (0.1, 0.04, 0.1), "dub")


def barrel(P, m, r=0.34, h=0.95, lid=True, staves=16):
    """Sud z dug s obruci: soudkovity profil, kazda duga zvlast."""
    prof = []
    for k in range(7):
        t = k / 6
        prof.append((r * (0.86 + 0.14 * math.sin(math.pi * t)), h * t))
    for i in range(staves):
        a0 = 2 * math.pi * i / staves
        a1 = 2 * math.pi * (i + 1) / staves - 0.012
        verts = []
        for (rr, y) in prof:
            for a in (a0, a1):
                verts.append((rr * math.cos(a), y, -rr * math.sin(a)))
            for a in (a0, a1):
                verts.append(((rr - 0.022) * math.cos(a), y, -(rr - 0.022) * math.sin(a)))
        faces = []
        n = len(prof)
        for k in range(n - 1):
            o, q = 4 * k, 4 * (k + 1)
            faces.append((o + 0, o + 1, q + 1, q + 0))        # vnejsi
            faces.append((o + 3, o + 2, q + 2, q + 3))        # vnitrni
        faces.append((0, 2, 3, 1))
        faces.append((4 * (n - 1), 4 * (n - 1) + 1, 4 * (n - 1) + 3, 4 * (n - 1) + 2))
        for k in range(n - 1):
            o, q = 4 * k, 4 * (k + 1)
            faces.append((o + 2, o + 0, q + 0, q + 2))
            faces.append((o + 1, o + 3, q + 3, q + 1))
        P.mesh(verts, faces, "dub", None, R.random(), m)
    # dna a obruce
    if lid:
        P.cyl(m @ M((0, h - 0.06, 0)), r * 0.84, r * 0.84, 0.03, 18, "deska")
    P.cyl(m @ M((0, 0.03, 0)), r * 0.84, r * 0.84, 0.03, 18, "deska")
    for t in (0.07, 0.2, 0.8, 0.93):
        rr = r * (0.86 + 0.14 * math.sin(math.pi * t)) + 0.006
        P.lathe(m @ M((0, h * t - 0.025, 0)), [(rr, 0), (rr, 0.05)], 20, "zelezo", False, False)


def crate(P, m, s=0.7):
    """Bedna z prken s lisnami."""
    bx(P, m, (0, s / 2, 0), (s - 0.04, s - 0.04, s - 0.04), "deska", collide=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(P, m, (sx * (s / 2 - 0.03), s / 2, sz * (s / 2 - 0.03)), (0.07, s, 0.07), "dub")
    for y in (0.04, s - 0.04):
        for sz in (-1, 1):
            bx(P, m, (0, y, sz * (s / 2 - 0.01)), (s, 0.07, 0.03), "dub")
            bx(P, m, (sz * (s / 2 - 0.01), y, 0), (0.03, 0.07, s), "dub")
    for sz in (-1, 1):
        beam(P, m, (-s / 2 + 0.05, 0.05, sz * (s / 2 + 0.005)), (s / 2 - 0.05, s - 0.05, sz * (s / 2 + 0.005)), 0.06, 0.02, "dub")


def sack(P, m, r=0.25, slump=False):
    h = r * (1.4 if not slump else 0.9)
    P.ball((0, 0, 0), (r, h, r * 0.85), "pytlovina", 12, 8, m=m @ M((0, h * 0.85, 0)))
    if not slump:
        P.lathe(m @ M((0, h * 1.6, 0)), [(0.06, 0), (0.035, 0.05), (0.07, 0.14), (0.0, 0.16)], 8, "pytlovina")
        P.lathe(m @ M((0, h * 1.6 + 0.02, 0)), [(0.045, 0), (0.045, 0.02)], 8, "lano")


def shelf(P, m, length=1.6, h=1.9, boards=4, depth=0.4):
    """Regal u zdi (zada = +Z)."""
    for sx in (-1, 1):
        bx(P, m, (sx * (length / 2 - 0.02), h / 2, 0), (0.04, h, depth), "deska")
    for k in range(boards):
        y = 0.1 + (h - 0.15) * k / (boards - 1)
        bx(P, m, (0, y, 0), (length, 0.03, depth), "deska", yaw=0)
    bx(P, m, (0, h / 2, depth / 2 - 0.01), (length, h, 0.015), "prkna")


def bed(P, m, length=2.1, width=1.5, canopy=None, cover="sukno_cervene"):
    """Postel: ram z fosen, slamnik, pokryvka, polstar, kozesina."""
    bx(P, m, (0, 0.3, 0), (width, 0.12, length), "dub", collide=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(P, m, (sx * (width / 2 - 0.04), 0.25, sz * (length / 2 - 0.04)), (0.1, 0.5, 0.1), "dub")
    bx(P, m, (0, 0.7, length / 2 - 0.03), (width, 0.7, 0.05), "deska")
    P.ball((0, 0, 0), (width / 2 - 0.05, 0.1, length / 2 - 0.08), "platno", 16, 6, m=m @ M((0, 0.43, 0)))
    P.ball((0, 0, 0), (width / 2, 0.06, length * 0.36), cover, 16, 6, m=m @ M((0, 0.5, -length * 0.12)))
    bx(P, m, (0, 0.42, -length * 0.12), (width + 0.04, 0.18, length * 0.7), cover)
    P.ball((0, 0, 0), (width * 0.38, 0.08, 0.2), "prosteradlo", 14, 6, m=m @ M((0, 0.55, length / 2 - 0.3)))
    P.ball((0, 0, 0), (width * 0.3, 0.025, 0.4), "kozesina", 14, 4, m=m @ M((0.1, 0.56, -0.1)) @ rot("Y", 25))


def candle(P, pos, lit=True, h=0.15, holder=True):
    x, y, z = pos
    if holder:
        P.lathe(M((x, y, z)), [(0.06, 0), (0.06, 0.008), (0.015, 0.02), (0.012, 0.05), (0.035, 0.06), (0.035, 0.07)], 12, "mosaz")
        y += 0.07
    P.cyl(M((x, y, z)), 0.016, 0.014, h, 10, "vosk")
    if lit:
        P.lathe(M((x, y + h + 0.004, z)), [(0.0, 0), (0.007, 0.012), (0.006, 0.026), (0.0, 0.045)], 6, "plamen")
    return Vector((x, y + h + 0.03, z))


def plate(P, pos, wood=False):
    mat = "deska" if wood else "cin"
    P.lathe(M(pos), [(0.0, 0), (0.08, 0.0), (0.11, 0.015), (0.125, 0.022), (0.118, 0.024), (0.07, 0.008), (0.0, 0.008)], 18, mat)


def mug(P, pos, mat="hlina_dzban"):
    P.lathe(M(pos), [(0.0, 0.0), (0.038, 0.0), (0.042, 0.06), (0.04, 0.11), (0.036, 0.11), (0.032, 0.012), (0.0, 0.012)], 14, mat)
    P.rod(Vector(pos) + Vector((0.04, 0.085, 0)), Vector(pos) + Vector((0.065, 0.06, 0)), 0.007, 5, mat)
    P.rod(Vector(pos) + Vector((0.065, 0.06, 0)), Vector(pos) + Vector((0.04, 0.025, 0)), 0.007, 5, mat)


def jug(P, pos, s=1.0, mat="hlina_dzban"):
    prof = [(0.0, 0.0), (0.06, 0.0), (0.095, 0.08), (0.1, 0.13), (0.07, 0.22), (0.045, 0.27), (0.055, 0.3), (0.05, 0.3), (0.035, 0.03), (0.0, 0.03)]
    P.lathe(M(pos) @ Matrix.Scale(s, 4), prof, 16, mat)
    p = Vector(pos)
    P.rod(p + Vector((0.05 * s, 0.28 * s, 0)), p + Vector((0.11 * s, 0.22 * s, 0)), 0.01 * s, 5, mat)
    P.rod(p + Vector((0.11 * s, 0.22 * s, 0)), p + Vector((0.085 * s, 0.12 * s, 0)), 0.01 * s, 5, mat)


def bowl(P, pos, r=0.12, mat="deska", fill=None):
    P.lathe(M(pos), [(0.0, 0.0), (r * 0.5, 0.0), (r * 0.9, r * 0.35), (r, r * 0.55), (r * 0.94, r * 0.55), (r * 0.45, r * 0.08), (0, r * 0.08)], 16, mat)
    if fill:
        P.ball((0, 0, 0), (r * 0.85, r * 0.15, r * 0.85), fill, 12, 4, m=M(Vector(pos) + Vector((0, r * 0.4, 0))))


def bread(P, pos, s=1.0):
    P.ball((0, 0, 0), (0.11 * s, 0.065 * s, 0.09 * s), "chleb", 12, 6, m=M(Vector(pos) + Vector((0, 0.03 * s, 0))))


def apples(P, pos, n=5):
    for k in range(n):
        a = k * 2.4
        P.ball((math.cos(a) * 0.05 * (k > 0), 0.035 + 0.03 * (k > 3), math.sin(a) * 0.05 * (k > 0)), (0.035, 0.032, 0.035), "jablko", 8, 5, m=M(pos))


def book(P, m, col="cervena", w=0.22, d=0.3, t=0.06, open_=False):
    bx(P, m, (0, t / 2, 0), (w, t, d), col)
    bx(P, m, (0.005, t / 2, 0), (w - 0.012, t - 0.012, d - 0.012), "platno")


def rug(P, m, w, l, mat="sukno_cervene"):
    bx(P, m, (0, 0.006, 0), (w, 0.012, l), mat)


def hanging(P, m, w=2.0, h=1.8, mat="sukno_cervene"):
    """Tapiserie na tyci (m = stred horni hrany, zada +Z ke zdi)."""
    P.rod(T(m, (-w / 2 - 0.1, 0, 0.04)), T(m, (w / 2 + 0.1, 0, 0.04)), 0.02, 8, "dub")
    n = 14
    for k in range(n):
        x0 = -w / 2 + w * k / n
        x1 = -w / 2 + w * (k + 1) / n
        z0 = 0.04 + 0.025 * math.sin(k * 1.3)
        z1 = 0.04 + 0.025 * math.sin((k + 1) * 1.3)
        P.face([T(m, (x0, -0.03, z0)), T(m, (x1, -0.03, z1)), T(m, (x1, -h, z1)), T(m, (x0, -h, z0))], mat,
               uvs=[(x0 + w / 2, h), (x1 + w / 2, h), (x1 + w / 2, 0), (x0 + w / 2, 0)])
        P.face([T(m, (x1, -0.03, z1 + 0.005)), T(m, (x0, -0.03, z0 + 0.005)), T(m, (x0, -h, z0 + 0.005)), T(m, (x1, -h, z1 + 0.005))], "platno")


def shield(P, m, mat="sukno_cervene", charge="bila"):
    """Stit (m = stred, licem -Z)."""
    pts = []
    for k in range(13):
        a = math.pi * k / 12
        pts.append((0.3 * math.cos(a), 0.2 + 0.05 * math.sin(a)))
    pts = [(0.3, 0.2)] + [(0.3 * math.cos(math.pi * (1 - k / 12)) * 1.0, -0.2 - 0.35 * math.sin(math.pi * k / 12) ** 1.5) for k in range(13)] + [(-0.3, 0.2)]
    poly = [T(m, (x, y, 0)) for x, y in pts]
    d = (m.to_3x3() @ Vector((0, 0, -0.03)))
    P.prism(list(reversed(poly)), d, "dub")
    P.prism([T(m, (x * 0.94, y * 0.94 + 0.01, -0.031)) for x, y in reversed(pts)], m.to_3x3() @ Vector((0, 0, -0.004)), mat)
    # znak: kosmy pruh
    P.box(m @ M((0, -0.05, -0.038)) @ rot("Z", 35), (0.12, 0.62, 0.006), charge)


def torch(P, m, lit=True):
    """Louc v zeleznem drzaku na zdi (m = bod na zdi, -Z od zdi)."""
    P.box(m @ M((0, 0, -0.01)), (0.08, 0.16, 0.02), "zelezo")
    P.rod(T(m, (0, 0, -0.02)), T(m, (0, 0.08, -0.2)), 0.012, 6, "zelezo")
    P.lathe(m @ M((0, 0.06, -0.2)), [(0.02, 0), (0.035, 0.03), (0.04, 0.08), (0.04, 0.09)], 8, "zelezo", False, False)
    P.rod(T(m, (0, -0.15, -0.16)), T(m, (0, 0.2, -0.22)), 0.022, 8, "dub", 0.03)
    P.ball((0, 0, 0), (0.04, 0.045, 0.04), "saze", 8, 5, m=m @ M((0, 0.2, -0.22)))
    if lit:
        P.lathe(m @ M((0, 0.22, -0.22)), [(0.0, 0), (0.04, 0.03), (0.03, 0.1), (0.0, 0.2)], 8, "plamen")
    return T(m, (0, 0.33, -0.25))


def chandelier(P, pos, r=0.7, ceiling_y=3.5, n=8):
    """Dreveny kruhovy lustr se svickami na retezech."""
    x, y, z = pos
    P.lathe(M((x, y, z)), [(r, 0), (r + 0.04, 0.02), (r + 0.04, 0.08), (r, 0.1), (r - 0.05, 0.1), (r - 0.05, 0), ], 32, "dub", False, False)
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        pts.append(candle(P, (x + r * math.cos(a), y + 0.1, z + r * math.sin(a)), True, 0.12, False))
        P.lathe(M((x + r * math.cos(a), y + 0.09, z + r * math.sin(a))), [(0.03, 0), (0.03, 0.015)], 8, "zelezo")
    for k in range(3):
        a = 2 * math.pi * k / 3
        P.rod((x + r * math.cos(a), y + 0.1, z + r * math.sin(a)), (x, y + 0.9, z), 0.006, 4, "zelezo")
    P.rod((x, y + 0.9, z), (x, ceiling_y, z), 0.01, 4, "zelezo")
    return pts


def logs(P, m, n=4, length=0.7, r=0.07):
    for k in range(n):
        a = (k - (n - 1) / 2) * 0.2
        y = r + (0.12 if k == n - 1 and n > 2 else 0)
        P.rod(T(m, (a, y, -length / 2)), T(m, (a + jit(0.05), y, length / 2)), r + jit(0.015), 9, "kura")


def woodpile(P, m, length=2.0, rows=5, depth=0.5):
    """Hranice stipanych polen (m = stred, delka podel X)."""
    r = 0.075
    for row in range(rows):
        x = -length / 2 + (r if row % 2 else 0)
        while x < length / 2 - r:
            y = r + row * r * 1.75
            c = (x + r, y, 0)
            a = R.uniform(0, 2 * math.pi)
            # pulena polena: trojboky
            pts = [(r * math.cos(a), r * math.sin(a)), (r * math.cos(a + 2.2), r * math.sin(a + 2.2)), (r * math.cos(a + 4.1), r * math.sin(a + 4.1))]
            poly = [T(m, (c[0] + p[0], c[1] + p[1] * 0.9, -depth / 2 + jit(0.04))) for p in pts]
            if (poly[1] - poly[0]).cross(poly[2] - poly[0]).dot(m.to_3x3() @ Vector((0, 0, 1))) < 0:
                poly.reverse()
            P.prism(poly, m.to_3x3() @ Vector((0, 0, depth + jit(0.05))), "drevo_rez" if R.random() < 0.4 else "kura")
            x += 2 * r + 0.01
    # opery a striska
    for sx in (-1, 1):
        beam(P, m, (sx * (length / 2 + 0.05), 0, 0), (sx * (length / 2 + 0.05), rows * r * 1.75 + 0.1, 0), 0.08, 0.08, "dub_ven", 0.8)


def bucket(P, pos, water=True):
    P.lathe(M(pos), [(0.0, 0.0), (0.13, 0.0), (0.16, 0.3), (0.145, 0.3), (0.12, 0.02), (0.0, 0.02)], 16, "dub")
    for t in (0.06, 0.24):
        P.lathe(M(Vector(pos) + Vector((0, t, 0))), [(0.13 + 0.03 * t / 0.3 + 0.004, 0), (0.13 + 0.03 * t / 0.3 + 0.004, 0.025)], 16, "zelezo", False, False)
    if water:
        P.cyl(M(Vector(pos) + Vector((0, 0.24, 0))), 0.15, 0.15, 0.002, 16, "voda")
    p = Vector(pos)
    for k in range(8):
        a0, a1 = math.pi * k / 8, math.pi * (k + 1) / 8
        P.rod(p + Vector((0.16 * math.cos(a0), 0.3 + 0.18 * math.sin(a0), 0)), p + Vector((0.16 * math.cos(a1), 0.3 + 0.18 * math.sin(a1), 0)), 0.005, 4, "zelezo")


def brazier(P, pos):
    p = Vector(pos)
    for k in range(3):
        a = 2 * math.pi * k / 3
        P.rod(p + Vector((0.28 * math.cos(a), 0, 0.28 * math.sin(a))), p + Vector((0.2 * math.cos(a), 0.62, 0.2 * math.sin(a))), 0.015, 6, "zelezo")
    P.lathe(M(p + Vector((0, 0.5, 0))), [(0.0, 0), (0.12, 0), (0.25, 0.12), (0.27, 0.16), (0.25, 0.16), (0.11, 0.02), (0, 0.02)], 16, "zelezo")
    P.ball((0, 0, 0), (0.22, 0.05, 0.22), "zhar", 12, 4, m=M(p + Vector((0, 0.63, 0))))
    for k in range(7):
        P.ball((jit(0.14), 0, jit(0.14)), (0.05, 0.035, 0.04), "uhli", 6, 4, m=M(p + Vector((0, 0.67, 0))))
    return p + Vector((0, 0.8, 0))


# ---------------------------------------------------------------- zbrane a zbroj

def spear(P, a, b):
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    P.rod(a, b, 0.016, 6, "dub")
    P.rod(b, b + d * 0.08, 0.02, 6, "zelezo", 0.016)
    P.rod(b + d * 0.08, b + d * 0.32, 0.03, 4, "ocel", 0.001)


def sword(P, m):
    """Mec (m = hrot, osa Y = smer k jilci)."""
    P.box(m @ M((0, 0.45, 0)), (0.045, 0.9, 0.006), "ocel")
    P.box(m @ M((0, 0.92, 0)), (0.2, 0.025, 0.025), "ocel")
    P.box(m @ M((0, 1.02, 0)), (0.03, 0.17, 0.03), "kuze")
    P.ball((0, 0, 0), (0.03, 0.03, 0.02), "ocel", 8, 5, m=m @ M((0, 1.12, 0)))


def helmet(P, pos, kind=0):
    """Kotlik nebo bacinet."""
    p = Vector(pos)
    if kind == 0:
        P.lathe(M(p), [(0.14, 0), (0.17, 0.012), (0.16, 0.02), (0.13, 0.03), (0.12, 0.1), (0.08, 0.17), (0.0, 0.2)], 18, "ocel")
    else:
        P.lathe(M(p), [(0.11, 0), (0.115, 0.1), (0.1, 0.2), (0.06, 0.27), (0.0, 0.31)], 18, "ocel")


def weapon_rack(P, m, length=2.0, n=6):
    for sx in (-1, 1):
        beam(P, m, (sx * length / 2, 0, 0), (sx * length / 2, 1.6, 0), 0.08, 0.08, "dub")
    beam(P, m, (-length / 2 - 0.05, 1.45, 0), (length / 2 + 0.05, 1.45, 0), 0.06, 0.09, "dub")
    beam(P, m, (-length / 2, 0.1, 0.0), (length / 2, 0.1, 0.0), 0.12, 0.06, "dub")
    for k in range(n):
        x = -length / 2 + 0.2 + (length - 0.4) * k / max(1, n - 1)
        spear(P, T(m, (x, 0.12, 0.03)), T(m, (x + 0.02, 2.2, -0.05)))


def armor_stand(P, m):
    """Stojan s kroužkovou kosili a prilbou."""
    beam(P, m, (0, 0, 0), (0, 1.6, 0), 0.06, 0.06, "dub")
    beam(P, m, (-0.3, 0.02, 0), (0.3, 0.02, 0), 0.08, 0.06, "dub")
    beam(P, m, (0, 0.02, -0.3), (0, 0.02, 0.3), 0.06, 0.08, "dub")
    beam(P, m, (-0.25, 1.4, 0), (0.25, 1.4, 0), 0.05, 0.05, "dub")
    # kroužkova kosile: lathe s kovovym materialem
    P.lathe(m @ M((0, 0.75, 0)), [(0.2, 0.0), (0.22, 0.2), (0.19, 0.45), (0.21, 0.6), (0.14, 0.68), (0.07, 0.72)], 16, "zelezo")
    for sx in (-1, 1):
        P.rod(T(m, (sx * 0.2, 1.38, 0)), T(m, (sx * 0.3, 1.0, 0.02)), 0.06, 8, "zelezo", 0.05)
    helmet(P, T(m, (0, 1.55, 0)), 1)


# ---------------------------------------------------------------- nadvori

def well(P, pos):
    """Kamenna studna s drevenou strizkou, rumpalem a vedrem."""
    p = Vector(pos)
    r0, r1 = 0.75, 1.2
    seg = 18
    # obruba z kamenu: dve vrstvy kvadru do kruhu
    for layer in range(4):
        y = layer * 0.22
        off = (layer % 2) * 0.5
        for k in range(seg):
            a0 = 2 * math.pi * (k + off) / seg
            a1 = 2 * math.pi * (k + 1 + off) / seg - 0.03
            pts = []
            for a, rr in ((a0, r1), (a1, r1), (a1, r0), (a0, r0)):
                pts.append(p + Vector((rr * math.cos(a), y, rr * math.sin(a))))
            pts.reverse()
            P.prism(pts, Vector((0, 0.21 + jit(0.01), 0)), "kvadr_sedy" if layer == 3 else "zdivo_hole")
    P.lathe(M(p + Vector((0, -0.6, 0))), [(r0 - 0.01, 0), (r0 - 0.01, 0.002)], seg, "voda")
    P.lathe(M(p + Vector((0, -2.0, 0))), [(r0, 0), (r0, 2.1)], seg, "zdivo_hole", False, False)
    # sloupky, rumpal, strizka
    for sx in (-1, 1):
        P.beam(p + Vector((sx * 1.0, 0, 0)), p + Vector((sx * 1.0, 2.3, 0)), 0.16, 0.16, "dub_ven", j=1)
        P.beam(p + Vector((sx * 1.0, 1.2, 0.0)), p + Vector((sx * 0.55, 0.9, 0)), 0.08, 0.08, "dub_ven")
    P.rod(p + Vector((-1.05, 1.25, 0)), p + Vector((1.05, 1.25, 0)), 0.09, 10, "dub_ven")
    P.rod(p + Vector((1.05, 1.25, 0)), p + Vector((1.25, 1.25, 0)), 0.02, 6, "zelezo")
    P.rod(p + Vector((1.25, 1.25, 0)), p + Vector((1.25, 1.0, 0)), 0.02, 6, "zelezo")
    P.rod(p + Vector((1.25, 1.0, 0)), p + Vector((1.4, 1.0, 0)), 0.025, 6, "dub")
    P.rod(p + Vector((0.2, 1.25, 0)), p + Vector((0.2, 0.75, 0.0)), 0.012, 5, "lano")
    P.lathe(M(p + Vector((0, 1.25, 0))) @ rot("Z", 90) @ M((0, -0.35, 0)), [(0.1, 0), (0.1, 0.7)], 12, "lano", False, False)
    bucket(P, p + Vector((0.2, 0.45, 0.0)), False)
    yb = 2.3
    for sx in (-1, 1):
        P.beam(p + Vector((sx * 1.0, yb, -0.9)), p + Vector((sx * 1.0, yb, 0.9)), 0.12, 0.12, "dub_ven")
    P.beam(p + Vector((-1.3, yb + 0.85, 0)), p + Vector((1.3, yb + 0.85, 0)), 0.12, 0.12, "dub_ven")
    for sx in (-1, 1):
        P.beam(p + Vector((sx * 1.0, yb, 0)), p + Vector((sx * 1.0, yb + 0.85, 0)), 0.1, 0.1, "dub_ven")
    from lib import shingle_roof
    for sz in (-1, 1):
        eL = p + Vector((-1.35 * sz, yb - 0.1, sz * 1.1))
        eR = p + Vector((1.35 * sz, yb - 0.1, sz * 1.1))
        rR = p + Vector((1.35 * sz, yb + 0.92, 0))
        rL = p + Vector((-1.35 * sz, yb + 0.92, 0))
        shingle_roof(P, eL, eR, rR, rL, row=0.11, length=0.36)


def cart(P, m):
    """Zebrinovy vuz na dvou kolech s ojí."""
    L, W, H = 2.6, 1.2, 0.75
    for sx in (-1, 1):
        beam(P, m, (sx * W / 2, H, -L / 2), (sx * W / 2, H, L / 2), 0.1, 0.12, "dub_ven", 0.6)
    for k in range(9):
        z = -L / 2 + L * k / 8
        bx(P, m, (0, H + 0.07, z), (W + 0.08, 0.03, L / 8 - 0.01), "prkna_ven")
    for sx in (-1, 1):
        # zebrina
        beam(P, m, (sx * (W / 2 + 0.15), H + 0.7, -L / 2), (sx * (W / 2 + 0.15), H + 0.7, L / 2), 0.07, 0.07, "dub_ven")
        for k in range(7):
            z = -L / 2 + 0.1 + (L - 0.2) * k / 6
            beam(P, m, (sx * W / 2, H + 0.08, z), (sx * (W / 2 + 0.15), H + 0.7, z), 0.04, 0.04, "dub_ven")
    # osa a kola
    beam(P, m, (-W / 2 - 0.25, 0.55, 0.2), (W / 2 + 0.25, 0.55, 0.2), 0.1, 0.1, "dub_ven")
    for sx in (-1, 1):
        wm = m @ M((sx * (W / 2 + 0.2), 0.55, 0.2)) @ rot("Z", 90)
        P.lathe(wm @ M((0, -0.05, 0)), [(0.53, 0), (0.56, 0.01), (0.56, 0.09), (0.53, 0.1)], 28, "zelezo", False, False)
        P.lathe(wm @ M((0, -0.04, 0)), [(0.43, 0), (0.53, 0), (0.53, 0.08), (0.43, 0.08), (0.43, 0)], 28, "dub_ven", False, False)
        P.lathe(wm @ M((0, -0.12, 0)), [(0.09, 0), (0.11, 0.06), (0.11, 0.18), (0.08, 0.24)], 12, "dub_ven")
        for k in range(10):
            a = 2 * math.pi * k / 10
            P.rod(T(wm, (0.1 * math.cos(a), 0.0, 0.1 * math.sin(a))), T(wm, (0.45 * math.cos(a), 0.0, 0.45 * math.sin(a))), 0.025, 6, "dub_ven")
    # oj spustena k zemi
    beam(P, m, (0, H - 0.05, -L / 2 + 0.3), (0, 0.06, -L / 2 - 2.0), 0.09, 0.09, "dub_ven", 0.5)


def hay_pile(P, pos, s=1.0):
    p = Vector(pos)
    P.ball((0, 0, 0), (1.3 * s, 0.75 * s, 1.1 * s), "slama", 18, 8, m=M(p + Vector((0, 0.0, 0))))
    for k in range(5):
        P.ball((jit(0.9 * s), 0.0, jit(0.8 * s)), (0.5 * s, 0.25 * s, 0.4 * s), "slama", 10, 5, m=M(p))


def chopping_block(P, pos):
    p = Vector(pos)
    P.lathe(M(p), [(0.32, 0), (0.3, 0.05), (0.28, 0.5), (0.0, 0.5)], 14, "kura")
    P.cyl(M(p + Vector((0, 0.5, 0))), 0.275, 0.275, 0.004, 14, "drevo_rez")
    # sekera zatnuta do spalku
    a = p + Vector((0.05, 0.52, 0.0))
    P.rod(a, a + Vector((0.3, 0.55, 0.05)), 0.018, 6, "dub")
    P.box(M(a + Vector((-0.02, 0.03, 0)), basis=Matrix.Rotation(0.5, 3, "Z")), (0.16, 0.1, 0.02), "ocel")


def trough(P, pos, length=2.2):
    p = Vector(pos)
    for sz in (-1, 1):
        P.bb(p + Vector((-length / 2, 0.05, sz * 0.3)), p + Vector((length / 2, 0.6, sz * 0.3 - sz * 0.06)), "deska")
    for sx in (-1, 1):
        P.bb(p + Vector((sx * length / 2, 0.05, -0.3)), p + Vector((sx * (length / 2 - 0.06), 0.6, 0.3)), "deska")
    P.bb(p + Vector((-length / 2, 0.05, -0.3)), p + Vector((length / 2, 0.11, 0.3)), "deska")
    for sx in (-1, 1):
        P.bb(p + Vector((sx * (length / 2 - 0.4) - 0.06, 0, -0.38)), p + Vector((sx * (length / 2 - 0.4) + 0.06, 0.08, 0.38)), "dub")
    P.bb(p + Vector((-length / 2 + 0.06, 0.5, -0.24)), p + Vector((length / 2 - 0.06, 0.505, 0.24)), "voda")


def hitching_post(P, a, b):
    a, b = Vector(a), Vector(b)
    for q in (a, b):
        P.beam(q, q + Vector((0, 1.1, 0)), 0.16, 0.16, "dub_ven", j=1)
    P.beam(a + Vector((0, 1.0, 0)), b + Vector((0, 1.0, 0)), 0.12, 0.12, "dub_ven", j=1)
    P.rod(a + Vector((0.3, 1.0, 0)) + (b - a).normalized() * 0.3, a + Vector((0.3, 0.7, 0.1)) + (b - a).normalized() * 0.3, 0.015, 5, "lano")


def candelabrum(P, pos, h=1.45, n=4):
    """Vysoky kovany svicen na trojnozce: stredni svice a n ramen se svicemi."""
    p = Vector(pos)
    for k in range(3):
        a = 2 * math.pi * k / 3
        f = p + Vector((0.28 * math.cos(a), 0.0, 0.28 * math.sin(a)))
        P.rod(f, p + Vector((0, 0.32, 0)), 0.014, 6, "zelezo")
        P.ball(f, (0.03, 0.015, 0.03), "zelezo", 6, 3)
    P.rod(p + Vector((0, 0.3, 0)), p + Vector((0, h, 0)), 0.018, 8, "zelezo")
    for yy in (0.6, 1.0):
        P.ball(p + Vector((0, yy, 0)), (0.035, 0.03, 0.035), "zelezo", 8, 5)
    tips = [candle(P, (p.x, p.y + h, p.z), True, 0.2, False)]
    for k in range(n):
        a = 2 * math.pi * k / n + 0.4
        e = p + Vector((0.24 * math.cos(a), h - 0.12, 0.24 * math.sin(a)))
        P.rod(p + Vector((0, h - 0.3, 0)), e, 0.01, 5, "zelezo")
        P.lathe(M(e), [(0.0, 0), (0.04, 0.0), (0.045, 0.02), (0.04, 0.02)], 10, "zelezo")
        tips.append(candle(P, (e.x, e.y + 0.02, e.z), True, 0.16, False))
    return tips
