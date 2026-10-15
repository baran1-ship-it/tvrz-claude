"""Modely z druheho chatu (vetev main, modely/nove): balvany, kameny, kaminky, vozy.

Ve hre se instancuji jako rostliny (veg.LIB -> modely/rostliny/<model>.glb + rozmisteni ve svet.json),
kolize maji kvadrem (pridavaji se do Part.cols tam, kde se misto vybira). Soubory se vytahnou z gitu
(origin/main) do tex_cache/nove, pokud tam jeste nejsou."""
import math
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "tex_cache", "nove")
GIT_REF = os.environ.get("TVRZ_NOVE_REF", "origin/main")

# rozmer modelu (sirka x, vyska y, hloubka z v m) podle modely/nove/seznam.txt
DIM = {
    "balvan_piskovec_1": (2.58, 1.49, 1.78), "balvan_piskovec_2": (2.20, 1.11, 1.46), "balvan_piskovec_3": (3.12, 2.23, 2.14),
    "balvan_droba_1": (2.59, 1.50, 1.79), "balvan_zula_1": (2.46, 1.53, 2.01),
    "kamen_zula_1": (1.36, 0.76, 0.94), "kamen_zula_2": (0.63, 0.39, 0.41), "kamen_piskovec_1": (1.08, 0.61, 0.81),
    "kamen_piskovec_2": (1.31, 0.62, 0.91), "kamen_droba_1": (0.83, 0.50, 0.71),
    "kamen_maly_1": (0.29, 0.19, 0.18), "kamen_maly_2": (0.25, 0.13, 0.16), "kamen_maly_3": (0.34, 0.16, 0.21),
    "kamen_maly_4": (0.14, 0.10, 0.11), "kamen_maly_5": (0.27, 0.17, 0.22),
    "zebrinak_1": (1.73, 1.76, 6.26), "zebrinak_plachta_1": (1.73, 2.43, 6.26),
}
# horniny: piskovec na hrebeni a ve skalnim meste, jinde polni kameny ze zuly a droby (z ledovcu a potoku)
BALVANY_PISKOVEC = ["balvan_piskovec_1", "balvan_piskovec_2", "balvan_piskovec_3"]
BALVANY_POLE = ["balvan_zula_1", "balvan_droba_1", "balvan_piskovec_2"]
KAMENY_PISKOVEC = ["kamen_piskovec_1", "kamen_piskovec_2"]
KAMENY_POLE = ["kamen_zula_1", "kamen_zula_2", "kamen_droba_1", "kamen_piskovec_1"]
KAMINKY = ["kamen_maly_%d" % i for i in range(1, 6)]

MISTA = []      # (model, x, y, z, meritko, yaw ve hre) - doplni kraj/vesnice, rozmisti veg


def misto(pid, x, y, z, k, yaw, P=None, sink=0.18, collide=None):
    """Zapsat instanci modelu (meritko k vuci skutecne velikosti, yaw = otoceni ve hre kolem svisle osy).
    Pata se zapusti o sink * vyska. Kolize kvadrem do P.cols (vetsi kameny a vozy)."""
    w, h, d = DIM[pid]
    y0 = y - sink * h * k
    MISTA.append((pid, x, y0, z, k, yaw))
    if P is not None and (collide if collide is not None else h * k > 0.45):
        from lib import M
        from mathutils import Matrix
        B = Matrix.Rotation(yaw, 3, "Y")
        hh = h * k * (1.0 - sink)
        P.cols.append((M((x, y + hh / 2 - 0.02, z), basis=B), (w * k * 0.82, hh, d * k * 0.82)))


def _extract(pid):
    f = os.path.join(DIR, pid + ".glb")
    if not os.path.exists(f):
        os.makedirs(DIR, exist_ok=True)
        data = subprocess.run(["git", "-C", HERE, "show", "%s:modely/nove/%s.glb" % (GIT_REF, pid)], capture_output=True, check=True).stdout
        with open(f, "wb") as fh:
            fh.write(data)
    return f


def add_to_library(LIB):
    """Kazdy model jako druh s jednou variantou (sit s paty na pocatku); obrazky prejmenovane 'nove_<model>_...'."""
    import bpy
    from mathutils import Matrix
    for pid in sorted({m[0] for m in MISTA}):
        before = set(bpy.data.objects)
        imgs0 = set(bpy.data.images)
        bpy.ops.import_scene.gltf(filepath=_extract(pid))
        new = [o for o in bpy.data.objects if o not in before]
        for i, img in enumerate(set(bpy.data.images) - imgs0):
            img.name = "nove_%s_%d" % (pid, i)
        meshes = [o for o in new if o.type == "MESH"]
        parts = []
        for o in meshes:
            me = o.data.copy()
            me.transform(o.matrix_world.copy())
            parts.append(me)
        # vic siti (vuz: drevo + platno) -> jedna sit s vice materialy
        ob = bpy.data.objects.new("tmp_" + pid, parts[0])
        bpy.context.scene.collection.objects.link(ob)
        for me in parts[1:]:
            o2 = bpy.data.objects.new("tmp2", me)
            bpy.context.scene.collection.objects.link(o2)
            bpy.ops.object.select_all(action="DESELECT")
            ob.select_set(True)
            o2.select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.join()
        me = ob.data
        xs = [v.co.x for v in me.vertices]
        ys = [v.co.y for v in me.vertices]
        zs = [v.co.z for v in me.vertices]
        me.transform(Matrix.Translation(((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)))))
        h = max(zs) - min(zs)
        w = max(max(xs) - min(xs), max(ys) - min(ys))
        bpy.data.objects.remove(ob)
        for o in new:
            bpy.data.objects.remove(o)
        LIB[pid] = [(me, h, w)]
        print("knihovna (nove)", pid, round(h, 2), round(w, 2))


def rozmistit(V, place):
    """Instance do kolekce vegetace (veg.place: vyska = meritko * vyska modelu)."""
    for pid, x, y, z, k, yaw in MISTA:
        # Blender: model hledi do -Y, otoceni kolem Z; ve hre yaw kolem Y (stejny smysl)
        place(V, pid, (x, y, z), DIM[pid][1] * k, yaw=yaw, variant=0)
    print("nove modely: %d instanci" % len(MISTA))
