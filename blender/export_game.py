"""Export tvrze do hry (Godot): geometrie (glTF), kolize, ohne a mistnosti, rozmisteni rostlin, textury.

Pouziti:  python blender/export_game.py
Vystup:   modely/  (tvrz.glb, rostliny/*.glb, textury/*.jpg, svet.json)
"""
import json
import math
import os
import shutil
import sys

import bpy  # noqa: E402  (musi byt prvni kvuli inicializaci Blenderu)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mathutils import Matrix, Vector  # noqa: E402

import build  # noqa: E402
import lib  # noqa: E402
import veg  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "modely")

# Blender (Z nahoru) -> hra (Y nahoru): (x, y, z) -> (x, z, -y)
C = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
CI = C.inverted()

ROOMS = [
    ("branka", (-3.15, 6.5, 9.15), (7.0 + 0.7, 4.1, 7.5 + 0.7)),
    ("prujezd", (-1.6, 0.0, 9.5), (3.2, 3.9, 7.5)),
    ("vez0", (-18.3, 0.0, -15.3), (5.0, 6.2, 5.0)),
    ("vez1", (-18.3, 6.5, -15.3), (5.0, 6.2, 5.0)),
    ("vez2", (-20.2, 13.0, -17.2), (8.8, 4.0, 8.8)),
    ("sin", (3.2, 0.0, -14.0), (13.8, 3.6, 6.4)),
    ("spiz", (-2.4, 0.0, -14.0), (5.2, 3.6, 6.4)),
    ("komnata", (-2.4, 3.9, -14.0), (9.2, 6.5, 6.4)),
    ("loznice", (7.2, 3.9, -14.0), (9.8, 6.5, 6.4)),
    ("straznice", (-11.5, 0.0, 9.0), (6.8, 5.2, 5.0)),
]
AMBIENT = {"branka": (0.34, 0.33, 0.32), "prujezd": (0.30, 0.31, 0.33), "vez0": (0.2, 0.2, 0.21), "vez1": (0.24, 0.24, 0.25),
           "vez2": (0.5, 0.52, 0.56), "sin": (0.2, 0.185, 0.17), "spiz": (0.16, 0.155, 0.15), "komnata": (0.25, 0.24, 0.23),
           "loznice": (0.24, 0.225, 0.21), "straznice": (0.21, 0.2, 0.19)}

# cilovy pocet trojuhelniku pro herni verze rostlin (decimace)
DECIMATE = {"fir_tree_01": 7000, "pine_sapling_medium": 9000, "fir_sapling_medium": 9000, "fir_sapling": 5000,
            "dandelion_01": 3000, "tree_stump_01": 6000, "rock_moss_set_01": 3000}
SPAWN = (2.5, 40.0)


def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def vertex_colors(ob):
    """Atribut 'rnd' (odstin kusu) a 'grass' (zem) -> barva vrcholu pro hru."""
    me = ob.data
    rnd = me.attributes.get("rnd")
    grass = me.attributes.get("grass")
    if rnd is None and grass is None:
        return
    col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    data = [0.0] * (len(me.loops) * 4)
    rv = [0.5] * len(me.polygons)
    if rnd is not None and rnd.domain == "FACE":
        rnd.data.foreach_get("value", rv)
    gv = None
    if grass is not None:
        gv = [0.0] * len(me.vertices)
        grass.data.foreach_get("value", gv)
    for poly in me.polygons:
        r = rv[poly.index]
        for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
            g = gv[me.loops[li].vertex_index] if gv is not None else 0.0
            data[li * 4:li * 4 + 4] = [0.8 + 0.2 * r, max(0.0, min(1.0, g)), r, 1.0]
    col.data.foreach_set("color", data)
    me.color_attributes.active_color = col


def export_glb(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_materials="EXPORT", export_image_format="NONE", export_vertex_color="ACTIVE",
                              export_normals=True, export_texcoords=True, export_extras=False)


def export_plants():
    """Kazdy druh rostliny jako jeden GLB (varianty jako uzly '<druh>_<i>'), textury se sdileji."""
    d = os.path.join(OUT, "rostliny")
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)
    # textury rostlin staci v 512 px (setri velikost APK)
    for img in bpy.data.images:
        if img.size[0] > 512 and not img.name.startswith(("zdivo", "omitka", "tram", "prkna", "podlaha", "okenice", "dlazba",
                                                           "kocicky", "piskovec", "hlina", "trava", "strecha")):
            try:
                img.scale(512, 512)
            except RuntimeError:
                pass
    tmp = bpy.data.collections.new("Export_rostliny")
    bpy.context.scene.collection.children.link(tmp)
    for pid, variants in veg.LIB.items():
        objs = []
        for i, (me, h, w) in enumerate(variants):
            name = "%s_%d" % (pid, i)
            ob = bpy.data.objects.new(name, me.copy())
            ob.data.name = name
            tmp.objects.link(ob)
            target = DECIMATE.get(pid)
            n = tris(ob.data)
            if target and n > target:
                mod = ob.modifiers.new("dec", "DECIMATE")
                mod.ratio = max(0.003, target / n)
            if pid == "divoka_trava":
                vertex_colors(ob)
            objs.append(ob)
        bpy.ops.object.select_all(action="DESELECT")
        for ob in objs:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        own = pid != "divoka_trava"
        bpy.ops.export_scene.gltf(filepath=os.path.join(d, pid + ".glb"), export_format="GLB", use_selection=True,
                                  export_apply=True, export_yup=True, export_materials="EXPORT",
                                  export_image_format="AUTO" if own else "NONE", export_vertex_color="NONE" if own else "ACTIVE")
        print("rostlina", pid, len(objs))


def mesh_variant(me):
    for pid, variants in veg.LIB.items():
        for i, (m2, h, w) in enumerate(variants):
            if m2 == me:
                return pid, i
    return None, None


def main():
    lib.GAME = True
    os.makedirs(OUT, exist_ok=True)
    build.build(["terrain", "fort", "palace", "yard", "veg"])

    # 1) rostliny: instance -> seznam transformaci ve hre
    inst = {}
    lookup = {me.name: (pid, i) for pid, vs in veg.LIB.items() for i, (me, h, w) in enumerate(vs)}
    veg_coll = bpy.data.collections.get("Vegetace")
    bpy.context.view_layer.update()  # bez toho je matrix_world novych objektu jednotkova
    gone = []
    for ob in veg_coll.objects:
        hit = lookup.get(ob.data.name)
        if hit is None:
            continue
        mg = C @ ob.matrix_world @ CI
        key = "%s_%d" % hit
        inst.setdefault(key, []).append([round(v, 4) for row in mg[:3] for v in row])
        gone.append(ob)
    bpy.data.batch_remove(gone)
    export_plants()

    # 2) budovy, teren, voda, rakos: jeden GLB
    cols = []
    objs = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.users_collection[0].name in ("Knihovna", "Export_rostliny"):
            continue
        objs.append(ob)
        cols.extend(list(c) for c in ob.get("cols", []))
        vertex_colors(ob)
    export_glb(objs, os.path.join(OUT, "tvrz.glb"))

    # 3) textury pro hru (1k): barva, normala, drsnost
    td = os.path.join(OUT, "textury")
    os.makedirs(td, exist_ok=True)
    meta = json.load(open(os.path.join(lib.TEX_ROOT, "meta_1k.json")))
    for name, m in meta.items():
        for key in ("diff", "nor", "rough"):
            src = os.path.join(lib.TEX_ROOT, m["maps"][key])
            shutil.copyfile(src, os.path.join(td, "%s_%s.jpg" % (name, key)))

    # 4) popis sveta pro hru
    lights = [{"pos": list(p), "energy": e, "col": list(c)} for p, e, c, r in lib.LIGHTS]
    world = {
        "materialy": lib.GAMEMAT,
        "textury": {k: v["size_m"] for k, v in meta.items()},
        "kolize": cols,
        "mistnosti": [{"name": n, "pos": list(p), "size": list(s), "ambient": list(AMBIENT[n])} for n, p, s in ROOMS],
        "ohne": lib.INFO["fires"],
        "pouziti": lib.INFO["use"],
        "kour": lib.INFO["smoke"],
        "svetla": lights,
        "rostliny": inst,
        "voda_y": veg.WATER_Y,
        "start": SPAWN,
    }
    with open(os.path.join(OUT, "svet.json"), "w") as f:
        json.dump(world, f)
    print("export hotov: %d objektu, %d kolizi, %d druhu rostlin, %d instanci" %
          (len(objs), len(cols), len(inst), sum(len(v) for v in inst.values())))


if __name__ == "__main__":
    main()
