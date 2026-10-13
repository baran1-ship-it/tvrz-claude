"""Kameny a skalky v okoli tvrze: balvany u paty hradeb, skalky na kopeccich, rozhazene kameny v louce.
Kameny jsou vlastni geometrie (nepravidelny konvexni obal, ploss spodek zapusteny do zeme) s fotografickou
texturou skaly; vetsi maji kolizi."""
import math
import random

from mathutils import Matrix, Vector

import fort as F
import kit
from lib import M, Part

R = random.Random(2024)


def rock(P: Part, c, size, sink=0.3, flat=0.65, collide=True):
    """Balvan se stredem paty v c (hra), size = (sirka, vyska, hloubka). Spodek zapusten o sink * vyska."""
    sx, sy, sz = size
    pts = []
    n = 56
    # dve az tri odstipnute plochy (rovne lomy), jinak oble otlucene telo
    cuts = []
    for _ in range(R.randint(2, 3)):
        a, u = R.uniform(0, 2 * math.pi), R.uniform(-0.3, 0.9)
        r = math.sqrt(1 - u * u)
        cuts.append((Vector((r * math.cos(a), u, r * math.sin(a))), R.uniform(0.55, 0.8)))
    for i in range(n):
        # rovnomerne body na kouli (Fibonacci) s nahodnym posunem
        u = 1 - 2 * (i + 0.5) / n
        a = i * 2.39996 + R.uniform(-0.2, 0.2)
        r = math.sqrt(1 - u * u)
        d = Vector((r * math.cos(a), u, r * math.sin(a)))
        k = R.uniform(0.86, 1.0)
        for nn, lim in cuts:
            if d.dot(nn) * k > lim:
                k = lim / max(0.2, d.dot(nn))
        p = Vector((d.x * sx / 2 * k, d.y * sy / 2 * k, d.z * sz / 2 * k))
        if p.y > sy * 0.25:                      # zaoblena, ale lomena hlava
            p.y = sy * 0.25 + (p.y - sy * 0.25) * flat
        pts.append(p)
    verts, faces = kit._hull(pts)
    rot = Matrix.Rotation(R.uniform(0, 2 * math.pi), 3, "Y") @ Matrix.Rotation(R.uniform(-0.15, 0.15), 3, "X")
    base = Vector(c) + Vector((0, sy / 2 - sink * sy, 0))
    m = M(base, basis=rot)
    P.mesh(verts, faces, "skala", m=m, smooth=True)
    if collide and min(sx, sz) > 0.55 and sy * (1 - sink) > 0.35:
        P.cols.append((M(base, basis=rot), (sx * 0.8, sy * 0.85, sz * 0.8)))


def _ok(x, z):
    # cesta k bridge a most nechat volne
    return not (abs(x) < 4.5 and z > 15.0)


def build(coll):
    P = Part("Skaly", bevel=0.0)
    # 1) u paty hradeb: balvany a hromadky kamenu (vypadle ze zdiva, vytazene z prikopu)
    placed = 0
    tries = 0
    while placed < 50 and tries < 3000:
        tries += 1
        x, z = R.uniform(-40, 32), R.uniform(-30, 32)
        d = F.rect_dist(x, z)
        if not (0.25 < d < 1.5) or not _ok(x, z):
            continue
        big = R.random() < 0.55
        s = R.uniform(0.8, 1.7) if big else R.uniform(0.3, 0.6)
        y = F.land(x, z)
        rock(P, (x, y, z), (s * R.uniform(1.0, 1.5), s * R.uniform(0.6, 0.9), s * R.uniform(0.8, 1.2)), 0.3)
        for _ in range(R.randint(1, 4)):
            ox, oz = x + R.uniform(-1.0, 1.0), z + R.uniform(-1.0, 1.0)
            if F.rect_dist(ox, oz) < 0.15 or not _ok(ox, oz):
                continue
            t = R.uniform(0.18, 0.45)
            rock(P, (ox, F.land(ox, oz), oz), (t * 1.3, t * 0.7, t), 0.35, collide=False)
        placed += 1
    # 2) skalky na kopeccich za valem: nekolik velkych kamenu u sebe, vyrustaji ze svahu
    spots = 0
    tries = 0
    while spots < 12 and tries < 5000:
        tries += 1
        x, z = R.uniform(-62, 52), R.uniform(-55, 68)
        d = F.rect_dist(x, z)
        if not (15.0 < d < 45.0) or not _ok(x, z) or F.bumps(x, z) < 0.25:
            continue
        for _ in range(R.randint(3, 6)):
            ox, oz = x + R.uniform(-2.2, 2.2), z + R.uniform(-2.2, 2.2)
            s = R.uniform(1.0, 2.6)
            rock(P, (ox, F.land(ox, oz), oz), (s * R.uniform(1.0, 1.6), s * R.uniform(0.6, 1.1), s * R.uniform(0.8, 1.3)), 0.35, 0.8)
        spots += 1
    # 3) rozhazene kameny v louce a na svazich prikopu
    for _ in range(140):
        x, z = R.uniform(-55, 47), R.uniform(-45, 55)
        d = F.rect_dist(x, z)
        if d < 1.5 or not _ok(x, z) or (4.0 < d < 10.5 and F.land(x, z) < -2.7):
            continue
        s = R.uniform(0.2, 0.7) if R.random() < 0.85 else R.uniform(0.8, 1.3)
        rock(P, (x, F.land(x, z), z), (s * R.uniform(1.0, 1.4), s * R.uniform(0.5, 0.8), s), 0.4)
    P.commit(coll)
