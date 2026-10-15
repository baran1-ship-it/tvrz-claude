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
import kraj  # noqa: E402
import vesnice  # noqa: E402
import hostinec  # noqa: E402
import ruiny  # noqa: E402
import fort as F  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "modely")

# Blender (Z nahoru) -> hra (Y nahoru): (x, y, z) -> (x, z, -y)
C = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
CI = C.inverted()

ROOMS = [
    ("branka", (-3.15, 6.5, 9.15), (7.0 + 0.7, 4.1, 7.5 + 0.7)),
    ("prujezd", (-1.6, 0.0, 9.5), (3.2, 3.9, 7.5)),
    ("vez0", (-26.3, 0.0, -15.3), (5.0, 6.2, 5.0)),
    ("vez1", (-26.3, 6.5, -15.3), (5.0, 6.2, 5.0)),
    ("vez2", (-28.2, 13.0, -17.2), (8.8, 4.0, 8.8)),
    ("sin", (3.2, 0.0, -14.0), (13.8, 3.6, 6.4)),
    ("spiz", (-2.4, 0.0, -14.0), (5.2, 3.6, 6.4)),
    ("komnata", (-2.4, 3.9, -14.0), (9.2, 6.5, 6.4)),
    ("loznice", (7.2, 3.9, -14.0), (9.8, 6.5, 6.4)),
    ("zbrojnice", (-10.3, 0.0, 9.6), (6.0, 4.2, 4.4)),
]
AMBIENT = {"branka": (0.34, 0.33, 0.32), "prujezd": (0.30, 0.31, 0.33), "vez0": (0.2, 0.2, 0.21), "vez1": (0.24, 0.24, 0.25),
           "vez2": (0.5, 0.52, 0.56), "sin": (0.2, 0.185, 0.17), "spiz": (0.16, 0.155, 0.15), "komnata": (0.25, 0.24, 0.23),
           "loznice": (0.24, 0.225, 0.21), "zbrojnice": (0.21, 0.2, 0.19)}

# cilovy pocet trojuhelniku pro herni verze rostlin (decimace)
DECIMATE = {"fir_tree_01": 7000, "pine_sapling_medium": 9000, "fir_sapling_medium": 9000, "fir_sapling": 5000,
            "dandelion_01": 3000, "tree_stump_01": 6000, "rock_moss_set_01": 3000,
            # kameny a vozy z druheho chatu: tvar staci hruby, detail nese normalova mapa (tablet)
            "balvan_piskovec_1": 4000, "balvan_piskovec_2": 3500, "balvan_piskovec_3": 4500, "balvan_droba_1": 4000,
            "balvan_zula_1": 4000, "kamen_zula_1": 1500, "kamen_zula_2": 1000, "kamen_piskovec_1": 1500,
            "kamen_piskovec_2": 1500, "kamen_droba_1": 1200, "kamen_maly_1": 400, "kamen_maly_2": 400, "kamen_maly_3": 400,
            "kamen_maly_4": 300, "kamen_maly_5": 400, "zebrinak_1": 14000, "zebrinak_plachta_1": 16000,
            "rock_moss_set_02": 3000, "dead_tree_trunk": 5000, "dead_tree_trunk_02": 5000, "tree_stump_02": 4000,
            "root_cluster_01": 3000, "root_cluster_02": 3000}
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
    les = me.attributes.get("les")
    pole = me.attributes.get("pole")
    lv = pv = None
    if grass is not None:
        gv = [0.0] * len(me.vertices)
        grass.data.foreach_get("value", gv)
        # teren: cervena = plodina na poli (0 = zadna), modra = les
        lv = [0.0] * len(me.vertices)
        pv = [0.0] * len(me.vertices)
        if les is not None:
            les.data.foreach_get("value", lv)
        if pole is not None:
            pole.data.foreach_get("value", pv)
    for poly in me.polygons:
        r = rv[poly.index]
        for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
            vi = me.loops[li].vertex_index
            if gv is not None:
                data[li * 4:li * 4 + 4] = [pv[vi], max(0.0, min(1.0, gv[vi])), lv[vi], 1.0]
            else:
                data[li * 4:li * 4 + 4] = [0.8 + 0.2 * r, 0.0, r, 1.0]
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
    # textury rostlin a predmetu nejvys 1k
    for img in bpy.data.images:
        if img.size[0] > 1024 and not img.name.startswith(("zdivo", "omitka", "tram", "prkna", "podlaha", "okenice", "dlazba",
                                                           "kocicky", "piskovec", "hlina", "trava", "strecha", "nove_balvan")):
            try:
                img.scale(1024, 1024)
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
    import nove
    cols.extend(list(m.translation) + list(m.to_quaternion()) + list(sz) for m, sz in nove.KOLIZE)
    export_glb(objs, os.path.join(OUT, "tvrz.glb"))

    # 3) textury pro hru (2k, plna kvalita; drsnost 1k - na ni oko rozdil nepozna)
    td = os.path.join(OUT, "textury")
    if os.path.isdir(td):
        shutil.rmtree(td)
    os.makedirs(td, exist_ok=True)
    meta = json.load(open(os.path.join(lib.TEX_ROOT, "meta_2k.json")))
    for name, m in meta.items():
        for key in ("diff", "nor", "rough", "disp"):
            src = os.path.join(lib.TEX_ROOT, m["maps"][key])
            dst = os.path.join(td, "%s_%s.jpg" % (name, key))
            if key == "rough":
                img = bpy.data.images.load(src)
                img.scale(1024, 1024)
                img.filepath_raw = dst
                img.file_format = "JPEG"
                img.save()
                bpy.data.images.remove(img)
            else:
                shutil.copyfile(src, dst)
    hostinec.textury(td)

    # 3b) trava ve vsi: mrizka 2 m (vyska terenu v cm, hustota trsu 0..255) pro instancovane trsy ve hre
    import base64
    import struct
    import vesnice
    gk, gn = 2.0, 121
    gx0, gz0 = kraj.VES[0] - (gn - 1) * gk / 2, kraj.VES[1] - (gn - 1) * gk / 2
    hs, ms = [], []
    for k in range(gn):
        for i in range(gn):
            x, z = gx0 + i * gk, gz0 + k * gk
            hs.append(int(round(F.land(x, z) * 100.0)))
            g, les, pole = kraj.ground_attrs(x, z)
            m = max(0.0, min(1.0, (g - 0.3) / 0.45)) * (1.0 - 0.7 * les) * (0.5 if pole > 0.5 else 1.0)
            if vesnice._in_building(x, z, 1.6) or vesnice.pond_depth(x, z) > 0.0:
                m = 0.0
            ms.append(int(round(m * 255)))
    trava_ves = {"x0": gx0, "z0": gz0, "k": gk, "n": gn,
                 "y": base64.b64encode(struct.pack("<%dh" % len(hs), *hs)).decode(),
                 "m": base64.b64encode(bytes(ms)).decode()}

    # 4) popis sveta pro hru
    lights = [{"pos": list(p), "energy": e, "col": list(c)} for p, e, c, r in lib.LIGHTS]
    world = {
        "materialy": lib.GAMEMAT,
        "textury": {**{k: v["size_m"] for k, v in meta.items()}, **hostinec.TEXTURY},
        "kolize": cols,
        # pevne umistene predmety z katalogu (bozi muka na krizovatce)
        "staticke": [{"id": "bozi_muka", "p": [kraj.CROSS[0] + 6.5, F.land(kraj.CROSS[0] + 6.5, kraj.CROSS[1] + 5.0) - 0.15,
                                                 kraj.CROSS[1] + 5.0], "yaw": 0.6}] +
                     [{"id": id_, "p": [cx, F.land(cx, cz) + hostinec.ZVEDNUTI.get(id_, -0.04), cz], "yaw": yaw,
                       **({"boxy": hostinec.stan_boxy()} if id_ == "stan_kupce" else {"kolize": "trimesh"})} for id_, cx, cz, yaw, r in kraj.STAVBY] +
                     [{"id": id_, "p": [x, F.land(x, z) + dy, z], "yaw": yw, "kolize": "trimesh"} for id_, x, z, yw, dy in ruiny.STATICKE],
        "nazvy_mist": ruiny.NAZVY,
        "mistnosti": [{"name": n, "pos": list(p), "size": list(s), "ambient": list(AMBIENT[n])} for n, p, s in ROOMS] + vesnice.MISTNOSTI,
        "vybaveni": vesnice.VYBAVENI,
        "ohne": lib.INFO["fires"],
        "pouziti": lib.INFO["use"],
        "kour": lib.INFO["smoke"],
        "svetla": lights,
        "rostliny": inst,
        "pohyb": lib.MOVABLE,
        "voda_y": veg.WATER_Y,
        "trava_ves": trava_ves,
        "start": SPAWN,
    }
    with open(os.path.join(OUT, "svet.json"), "w") as f:
        json.dump(world, f)
    print("export hotov: %d objektu, %d kolizi, %d druhu rostlin, %d instanci" %
          (len(objs), len(cols), len(inst), sum(len(v) for v in inst.values())))


if __name__ == "__main__":
    main()
