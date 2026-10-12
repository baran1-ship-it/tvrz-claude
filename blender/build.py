"""Postavi celou tvrz v Blenderu, ulozi .blend a vyrenderuje nahledy.

Pouziti:  python build.py [--parts fort,palace,yard] [--views 1,2] [--samples 48] [--res 1600x900] [--out DIR] [--blend FILE]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import fort  # noqa: E402
import lib  # noqa: E402
import scene  # noqa: E402

PATHS = [
    [(0, 14), (0, 3.5), (8, -4.5), (8, -7)],
    [(0, 3.5), (-8, -6), (-11.6, -12.8)],
    [(0, 6), (-6, 8.3)],
    [(2, 9), (14.2, 12.6)],
    [(8, -4.5), (-0.05, -6.6)],
    [(0, 3.5), (-9.4, -6.3)],
]

# pohledy: (nazev, pozice kamery, cil, ohnisko, slunce (vyska, azimut))
VIEWS = {
    1: ("ptaci_pohled", (34, 26, 52), (0, 2, 0), 30, (32, 140)),
    2: ("prijezd", (2.2, 0.4, 40), (0, 4, 15), 26, (30, 150)),
    3: ("brana", (-1.2, 1.4, 25.5), (0, 3.5, 16), 24, (35, 200)),
    4: ("nadvori_palac", (-2.5, 1.65, 7.5), (6, 3.0, -8), 22, (38, 170)),
    5: ("nadvori_brana", (6, 1.65, -3.5), (-3, 3, 12), 22, (38, 160)),
    6: ("sin", (5.6, 1.7, -8.1), (15, 1.2, -11.6), 20, (38, 170)),
    7: ("loznice", (8.2, 5.5, -8.4), (16, 4.4, -13), 20, (38, 170)),
    8: ("komnata", (6.0, 5.5, -8.4), (-1, 4.4, -12), 20, (38, 170)),
    9: ("ochoz", (-17.6, 8.15, 12.5), (-10, 7, -6), 22, (30, 230)),
    10: ("vez_z_hradby", (10, 8.15, 13.6), (-15, 8, -10), 24, (30, 220)),
    11: ("straznice", (-5.2, 1.6, 9.4), (-10.5, 1.0, 13), 20, (38, 170)),
    12: ("spiz", (2.3, 1.6, -8.0), (-2, 0.6, -13), 20, (38, 170)),
    14: ("roh_brany", (8, 2, 22), (3.5, 3, 16), 30, (30, 150)),
    13: ("zapad", (-40, 6, -2), (-10, 5, -2), 30, (25, 250)),
}


def build(parts):
    scene.reset()
    lib.build_materials()
    lib.LIGHTS.clear()
    t0 = time.time()
    if "terrain" in parts:
        c = scene.coll("Teren")
        fort.terrain(c)
        fort.yard_ground(c, PATHS)
    if "fort" in parts:
        c = scene.coll("Opevneni")
        fort.walls(c)
        fort.gatehouse(c)
        fort.tower(c)
        fort.wall_stair(c)
        fort.bridge(c)
    if "palace" in parts:
        import palace
        palace.build(scene.coll("Palac"))
    if "yard" in parts:
        import yard
        yard.build(scene.coll("Nadvori"), PATHS)
    for k, (pos, energy, col, rad) in enumerate(lib.LIGHTS):
        scene.point_light(pos, energy, col, rad, "Ohen%03d" % k)
    print("stavba %.1f s, svetel %d" % (time.time() - t0, len(lib.LIGHTS)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="terrain,fort,palace,yard")
    ap.add_argument("--views", default="")
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--res", default="1600x900")
    ap.add_argument("--out", default="build/nahledy")
    ap.add_argument("--blend", default="")
    a = ap.parse_args(sys.argv[1:] if "--" not in sys.argv else sys.argv[sys.argv.index("--") + 1:])
    build(a.parts.split(","))
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    if a.views:
        os.makedirs(a.out, exist_ok=True)
        w, h = (int(v) for v in a.res.split("x"))
        for v in (int(x) for x in a.views.split(",")):
            name, pos, tgt, lens, (el, az) = VIEWS[v]
            for ob in list(bpy.data.objects):
                if ob.type in ("CAMERA", "LIGHT") and ob.name.startswith(("Kamera", "Slunce")):
                    bpy.data.objects.remove(ob)
            scene.sky(el, az, 0.3, 2.6)
            scene.camera(pos, tgt, lens)
            path = os.path.abspath(os.path.join(a.out, "%02d_%s.jpg" % (v, name)))
            t = time.time()
            scene.render(path, a.samples, (w, h))
            print("render %s %.0f s" % (name, time.time() - t))


if __name__ == "__main__":
    main()
