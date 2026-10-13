"""Studna na nadvori: roubena z lomoveho sedeho kamene (kazdy kamen jiny, nepravidelne vrstvy),
nahore kryci desky, dva sloupy s vidlici, rumpal s klikou (pohyblivy, navijeni lana) a vedro na lane,
ktere se spousti do studny. Sindelova strizka na krokvich."""
import math
import random

from mathutils import Matrix, Vector

import kit
import props as PR
from lib import M, Part, jit, shingle_roof

R = random.Random(77)


def build(coll, pos=(-3.6, 0.0, -1.6)):
    P = Part("Studna", bevel=0.006)
    p = Vector(pos)
    r_in, r_out = 0.68, 1.12
    # --- roubeni: vrstvy lomovych kamenu po obvodu, spary vystridane
    y = -0.12
    layer = 0
    while y < 0.72:
        h = R.uniform(0.17, 0.25)
        a = R.uniform(0, 0.4)
        while a < 2 * math.pi - 0.05:
            ln = R.uniform(0.32, 0.55)               # delka kamene po obvodu (m)
            da = ln / ((r_in + r_out) / 2)
            if a + da > 2 * math.pi:
                da = 2 * math.pi - a
            am = a + da / 2
            rr = (r_in + r_out) / 2 + jit(0.02)
            c = p + Vector((math.cos(am) * rr, y + h / 2, math.sin(am) * rr))
            # kamen otoceny tecne k obvodu (lokalni x = tecna, z = radialne)
            yaw = -math.degrees(am) - 90
            kit.stone(P, M(c, yaw), (ln * 0.97, h * R.uniform(0.9, 1.0), (r_out - r_in) * R.uniform(0.85, 1.0)),
                      "kvadr_sedy", cham=R.uniform(0.02, 0.05), rough=0.018)
            a += da
        y += h
        layer += 1
    # kryci desky: sirsi a plochejsi, mirne pres hranu
    a = 0.0
    yt = y
    while a < 2 * math.pi - 0.05:
        ln = R.uniform(0.55, 0.8)
        da = min(ln / ((r_in + r_out) / 2), 2 * math.pi - a)
        am = a + da / 2
        rr = (r_in + r_out) / 2 + 0.02
        c = p + Vector((math.cos(am) * rr, yt + 0.06, math.sin(am) * rr))
        kit.stone(P, M(c, -math.degrees(am) - 90), (ln * 0.98, 0.12, (r_out - r_in) + 0.12), "kvadr", cham=0.025, rough=0.01)
        a += da
    # kolize az po horni plochu krycich desek (svicen nebo vedro na studni nesmi zapadnout)
    P.cols.append((M(p + Vector((0, yt / 2 + 0.03, 0))), (2.2, yt + 0.24, 2.2)))
    # sachta a voda hluboko dole
    P.lathe(M(p + Vector((0, -3.4, 0))), [(r_in + 0.02, 0), (r_in + 0.02, 3.3)], 20, "zdivo_hole", False, False)
    P.lathe(M(p + Vector((0, -3.0, 0))), [(r_in, 0), (r_in, 0.002)], 20, "voda")
    # --- sloupy s vidlici a vzperami, zapustene do roubeni
    yr = yt + 0.12
    hy = yr + 0.95                  # osa rumpalu
    for sx in (-1, 1):
        x = sx * 1.02
        P.beam(p + Vector((x, -0.2, 0)), p + Vector((x, hy + 1.25, 0)), 0.17, 0.17, "dub_ven", j=1)
        P.beam(p + Vector((x, yr + 0.35, -0.08)), p + Vector((x - sx * 0.4, yr + 0.05, -0.08)), 0.08, 0.08, "dub_ven", j=0.6)
        # lozisko: kovany trmen
        P.rod(p + Vector((x - sx * 0.1, hy - 0.08, 0)), p + Vector((x - sx * 0.1, hy + 0.08, 0)), 0.035, 8, "zelezo")
    # --- strizka: vaznice, krokve a sindel
    yb = hy + 1.2
    for sx in (-1, 1):
        P.beam(p + Vector((sx * 1.02, yb, -0.95)), p + Vector((sx * 1.02, yb, 0.95)), 0.12, 0.13, "dub_ven", j=0.5)
    P.beam(p + Vector((-1.35, yb + 0.85, 0)), p + Vector((1.35, yb + 0.85, 0)), 0.13, 0.13, "dub_ven", j=0.5)
    for sx in (-1, 1):
        P.beam(p + Vector((sx * 1.02, yb, 0)), p + Vector((sx * 1.02, yb + 0.85, 0)), 0.1, 0.1, "dub_ven")
        for sz in (-1, 1):
            P.beam(p + Vector((sx * 1.15, yb - 0.05, sz * 1.0)), p + Vector((sx * 1.15, yb + 0.88, 0)), 0.07, 0.09, "dub_ven")
    for sz in (-1, 1):
        eL = p + Vector((-1.38 * sz, yb - 0.08, sz * 1.12))
        eR = p + Vector((1.38 * sz, yb - 0.08, sz * 1.12))
        rR = p + Vector((1.38 * sz, yb + 0.94, 0))
        rL = p + Vector((-1.38 * sz, yb + 0.94, 0))
        shingle_roof(P, eL, eR, rR, rL, row=0.11, length=0.36)
    P.commit(coll)

    # --- rumpal (otaci se kolem X) s klikou; lano se navijí dynamicky (navin, obracene: vedro nahore = plny buben)
    c = p + Vector((0, hy, 0))
    L = 1.75

    def drum(Q):
        rot = Matrix.Rotation(-math.pi / 2, 4, "Z")
        Q.lathe(M((-L / 2, 0, 0)) @ rot, [(0.03, 0.0), (0.11, 0.0), (0.11, L), (0.03, L)], 12, "dub_ven")
        for sx in (-1, 1):
            Q.lathe(M((sx * 0.55 - 0.02, 0, 0)) @ rot, [(0.15, 0.0), (0.15, 0.04)], 12, "dub_ven")
        Q.rod(Vector((-L / 2 - 0.1, 0, 0)), Vector((L / 2 + 0.05, 0, 0)), 0.025, 6, "zelezo")
        # klika: kovana zalomena tyc s drevenou rukojeti
        Q.rod(Vector((L / 2 + 0.05, 0, 0)), Vector((L / 2 + 0.05, 0.32, 0)), 0.022, 6, "zelezo")
        Q.rod(Vector((L / 2 + 0.05, 0.32, 0)), Vector((L / 2 + 0.28, 0.32, 0)), 0.03, 6, "dub")
    kit.movable("studna_rumpal", "navijak", M(c), drum, use=list(c + Vector((1.3, -0.4, 0.0))), group="studna", turns=9.0,
                navin={"r": 0.11, "L": 1.1, "typ": "lano", "obracene": True})
    # vedro: visi pod bubnem, spousti se do studny (posun dolu)
    top = Vector((0.0, hy - 0.62, 0.0))
    kit.movable("studna_vedro", "vedro", M(p + top), lambda Q: PR.bucket(Q, Vector((0, 0, 0)), False),
                group="studna", lift=-(hy + 2.55), init=0.0, dur=6.0,
                ropes=[[list(c + Vector((0.0, -0.11, 0.0))), [0.0, 0.48, 0.0]]])
