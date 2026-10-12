"""Nahled stavebnice detailu (dvere, okna, most, padaci most). python kit_render.py [out_dir]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import kit as K  # noqa: E402
import lib  # noqa: E402
import scene  # noqa: E402
from lib import M, Part, wall_x  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "build/kit"


def build():
    scene.reset()
    lib.build_materials()
    lib.build_pbr_materials()
    c = scene.coll("Kit")
    W = Part("Zed", bevel=0.0)
    D = Part("Detaily", bevel=0.004)
    depth = 0.7
    # otvory: (x, sirka, vyska k vrcholu)
    ops = [(-6.0, 1.15, 2.6), (-2.6, 1.6, 2.9), (0.6, 1.0, 2.15), (5.6, 0.75, 1.0 + 1.3)]
    holes = [[x - w / 2, x + w / 2, 0.0, h] for x, w, h in ops[:3]] + [[5.6 - 0.375, 5.6 + 0.375, 1.3, 2.3]]
    wall_x(W, "zdivo_omitka", -8.5, 7.5, -depth, 0.0, -0.3, 4.2, holes, collide=False)
    # zem
    W.bb((-10, -0.4, -3), (10, -0.05, 6), "zem")
    K.doorway(D, M((-6.0, 0, 0)), "hlavni", 1.15, 2.6, depth, "lomeny", open_deg=0)
    K.doorway(D, M((-2.6, 0, 0)), "hlavni", 1.6, 2.9, depth, "pulkruh", open_deg=25, lattice=True)
    K.doorway(D, M((0.6, 0, 0)), "obycejne", 1.0, 2.15, depth, "segment")
    K.window(D, M((5.6, 1.3, 0)), 0.75, 1.0, depth, shutters=True)
    # vnitrni dvere v tenke pricce
    P2 = Part("Pricka")
    wall_x(P2, "omitka", 2.3, 4.3, -0.15, 0.0, -0.05, 2.5, [[2.85, 3.75, 0.0, 2.05]], collide=False)
    K.doorway(D, M((3.3, 0, 0)), "vnitrni", 0.9, 2.05, 0.15, open_deg=55)
    # most a padaci most
    B = Part("Most", bevel=0.004)
    K.deck(B, (0, 0.0, 1.5), (0, 0.0, 9.0), 1.75, worn=1.0) if False else None
    eyes = K.drawbridge(B, M((0, 0.25, 12.0)), 3.5, 4.2, 0.0)
    for sx in (-1, 1):
        B.beam((sx * 1.3, -0.3, 16.2), (sx * 1.3, -0.3, 23.5), 0.24, 0.3, "dub_ven", j=1)
    K.deck(B, (0, 0.0, 16.25), (0, 0.0, 23.5), 1.75, worn=1.0)
    for e, sx in zip(eyes, (-1, 1)):
        K.chain(B, e, Vector((sx * 1.9, 5.2, 11.6)), sag=0.25)
    for p in (W, D, P2, B):
        p.commit(c)


VIEWS = [
    ("dvere_celek", (-0.5, 1.6, 7.0), (-0.5, 1.4, 0.0), 26),
    ("dvere_hlavni", (-5.3, 1.5, 2.6), (-6.0, 1.4, 0.0), 30),
    ("dvere_mriz", (-2.0, 1.5, 3.2), (-2.6, 1.5, 0.0), 30),
    ("dvere_obycejne", (1.4, 1.4, 2.6), (0.6, 1.1, 0.0), 30),
    ("okno", (6.3, 1.8, 2.2), (5.6, 1.8, 0.0), 30),
    ("vnitrni", (3.9, 1.5, 2.6), (3.3, 1.1, 0.0), 30),
    ("most", (3.2, 1.8, 25.5), (0.0, 0.0, 15.0), 26),
    ("most_detail", (0.9, 1.6, 21.2), (0.0, 0.0, 18.3), 26),
]

if __name__ == "__main__":
    build()
    os.makedirs(OUT, exist_ok=True)
    only = os.environ.get("VIEWS")
    for name, pos, tgt, lens in VIEWS:
        if only and name not in only.split(","):
            continue
        for ob in list(bpy.data.objects):
            if ob.type in ("CAMERA", "LIGHT") and ob.name.startswith(("Kamera", "Slunce")):
                bpy.data.objects.remove(ob)
        scene.sky(32, 160, 0.2, 4.2)
        scene.camera(pos, tgt, lens)
        scene.render(os.path.abspath(os.path.join(OUT, name + ".jpg")), int(os.environ.get("SAMPLES", "32")), (1200, 800))
        print("render", name)
