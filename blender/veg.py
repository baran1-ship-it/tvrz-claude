"""Vegetace a voda: naskenovane rostliny z Poly Haven (instancovane), rakos, stojata voda v prikopu.

Rostliny se nacitaji jednou do skryte knihovny a rozmistuji jako instance (sdilena geometrie),
takze i tisice trsu nebo stovky stromu jsou levne.
"""
import math


def vesnice_pads():
    import vesnice
    return vesnice._pads()
import random
import os

import bpy
from mathutils import Matrix, Vector

import fort as F
from lib import GAMEMAT, TEX_ROOT, M, Part, R, jit, new_mat, finish, to_bl

LIB: dict = {}          # model -> [(mesh, vyska, sirka)]
# pouzite varianty u tezkych modelu (miliony trojuhelniku) - setri pamet
KEEP = {"grass_medium_01": list(range(11))}
# stromy z Poly Haven maji jehlici jako geometrii (miliony trojuhelniku) -> nahrazuje je herni smrk z karet (trees.py)
SKIP = {"pine_tree_01", "shrub_01", "shrub_04", "fir_tree_01", "pine_sapling_medium", "fir_sapling_medium", "fir_sapling"}


# ------------------------------------------------------------------ knihovna modelu

def load_library(models):
    lib_coll = bpy.data.collections.new("Knihovna")
    bpy.context.scene.collection.children.link(lib_coll)
    lib_coll.hide_render = True
    lib_coll.hide_viewport = True
    for pid in models:
        if pid in SKIP:
            continue
        path = os.path.join(TEX_ROOT, "models", pid, pid + ".gltf")
        if not os.path.exists(path):
            # 0.97: chybejici model se driv jen vypsal a export pokracoval - ze sveta tise zmizelo 76 druhu / 34 000
            # rostlin. Bez zdroje se nevyvazi: stahnout (textures.fetch_models) nebo model vyradit z dat.
            raise SystemExit("CHYBA: chybi model rostliny %s (%s) - python3 -c 'import textures; textures.fetch_models()'" % (pid, path))
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        variants = []
        meshes = sorted([o for o in new if o.type == "MESH"], key=lambda o: o.name)
        keep = KEEP.get(pid)
        for i, o in enumerate(meshes):
            if keep is not None and i not in keep:
                continue
            # zapect svetovou transformaci do geometrie, pata na pocatek
            mw = o.matrix_world.copy()
            me = o.data.copy()
            me.transform(mw)
            xs = [v.co.x for v in me.vertices]
            ys = [v.co.y for v in me.vertices]
            zs = [v.co.z for v in me.vertices]
            cx, cy, z0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
            me.transform(Matrix.Translation((-cx, -cy, -z0)))
            h = max(zs) - z0
            w = max(max(xs) - min(xs), max(ys) - min(ys))
            variants.append((me, h, w))
        old = [o.data for o in meshes]
        for o in new:
            bpy.data.objects.remove(o)
        for me_ in old:
            if me_.users == 0:
                bpy.data.meshes.remove(me_)
        LIB[pid] = variants
        print("knihovna", pid, [(round(h, 2), round(w, 2)) for _, h, w in variants])
    make_wild_grass()
    import trees
    trees.add_to_library(LIB)
    import listnace
    listnace.add_to_library(LIB)
    import nove
    nove.add_to_library(LIB)


FLAT = {"grass_medium_02", "dandelion_01", "grass_medium_01", "fern_02", "weed_plant_02"}


def place(coll, pid, pos, height=None, yaw=None, tilt=0.0, variant=None, flat=False):
    """Instance modelu na pozici ve hre. height = cilova vyska (m), flat = lezici predmet (vetve)."""
    vs = LIB.get(pid)
    if not vs:
        return None
    import kraj
    if not pid.startswith(("balvan", "kamen")) and kraj.rostlina_ve_vode(pid, pos[0], pos[2], pos[1]):
        return None
    me, h, w = vs[variant if variant is not None else R.randrange(len(vs))]
    ob = bpy.data.objects.new(pid, me)
    coll.objects.link(ob)
    ob.location = to_bl(Vector(pos))
    s = 1.0 if height is None or h < 1e-3 else height / h
    if pid in FLAT and w > 1e-3:
        s = height / w       # u prizemnich ruzic (plevel, pampelisky, trava) je mira sirka
    ob.scale = (s, s, s)
    ob.rotation_euler = (jit(tilt), jit(tilt), R.uniform(0, 2 * math.pi) if yaw is None else yaw)
    return ob


# ------------------------------------------------------------------ divoka trava (vlastni trsy, instancovane)

def make_wild_grass(nvar=6):
    """Nekolik variant trsu vysoke neposecene travy: prohnute listy, nekterE se suchymi konci, latky."""
    out = []
    for vi in range(nvar):
        P = Part("divoka_trava_%d" % vi)
        nb_ = R.randint(45, 80)
        for _ in range(nb_):
            a = R.uniform(0, 2 * math.pi)
            rr = 0.16 * math.sqrt(R.random())
            base = Vector((math.cos(a) * rr, 0.0, math.sin(a) * rr))
            hh = R.uniform(0.35, 1.0)
            d = Vector((math.cos(a), 0, math.sin(a)))
            bend = R.uniform(0.15, 0.55) * hh
            w = R.uniform(0.006, 0.012)
            side = Vector((-d.z, 0, d.x)) * w
            mat = "trava_sucha" if R.random() < 0.22 else "trava_divoka"
            segs = 4
            pts = []
            for s_ in range(segs + 1):
                t = s_ / segs
                p = base + Vector((0, hh * (t - 0.35 * t * t * bend / hh), 0)) + d * (bend * t * t)
                pts.append((p - side * (1 - t * 0.85), p + side * (1 - t * 0.85)))
            for s_ in range(segs):
                P.face([pts[s_][0], pts[s_][1], pts[s_ + 1][1], pts[s_ + 1][0]], mat,
                       uvs=[(0, s_ / segs), (1, s_ / segs), (1, (s_ + 1) / segs), (0, (s_ + 1) / segs)])
        # par latek (klasky)
        for _ in range(R.randint(2, 6)):
            a = R.uniform(0, 2 * math.pi)
            top = Vector((math.cos(a) * 0.12, R.uniform(0.7, 1.15), math.sin(a) * 0.12))
            P.rod(Vector((0, 0, 0)), top, 0.003, 3, "trava_sucha")
            P.rod(top, top + Vector((jit(0.04), 0.12, jit(0.04))), 0.012, 5, "trava_sucha", 0.003)
        coll = bpy.data.collections.get("Knihovna")
        ob = P.commit(coll)
        out.append((ob.data, 1.0, 0.35))
        bpy.data.objects.remove(ob)
    LIB["divoka_trava"] = out


# ------------------------------------------------------------------ voda v prikopu

WATER_Y = -2.75


def mat_pond(name):
    """Stojata voda: tmava zelenohneda, zrcadlici, s okřehkem a riasou u brehu a nanesenym listim."""
    GAMEMAT[name] = {"type": "rybnik"}
    m, nb, outn = new_mat(name)
    P = nb.geo("Position")
    px, py, pz = nb.sep(P)
    # vzdalenost od brehu priblizne podle atributu 'breh' (0 u brehu, 1 uprostred)
    br = nb.attr("breh")
    n1 = nb.noise(P, 0.25, 4.0, 0.6)
    n2 = nb.noise(P, 1.2, 5.0, 0.65)
    cells = nb.voro(nb.vmath("MULTIPLY", P, (60, 60, 0)), 1.0, "F1", "Distance", 1.0, dim="2D")
    weed = nb.math("ADD", nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, br), 0.55), nb.math("MULTIPLY", n1, 0.6))
    weed = nb.mr(nb.math("ADD", weed, nb.math("MULTIPLY", n2, 0.25)), 0.72, 0.78)
    weed = nb.math("MULTIPLY", weed, nb.mr(cells, 0.55, 0.35))
    scum = nb.mr(nb.noise(nb.vmath("MULTIPLY", P, (0.6, 2.5, 1)), 1.5, 3.0, 0.6), 0.6, 0.7, 0.0, 0.5)
    wcol = nb.mix(nb.mr(n2, 0.3, 0.7), (0.01, 0.014, 0.006), (0.025, 0.03, 0.012))
    wcol = nb.mix(scum, wcol, (0.07, 0.07, 0.045))
    dcol = nb.mix(nb.mr(n2, 0.3, 0.7), (0.07, 0.14, 0.02), (0.16, 0.22, 0.04))
    col = nb.mix(weed, wcol, dcol)
    rough = nb.fmix(weed, nb.fmix(scum, 0.07, 0.3), 0.55)
    ripple = nb.noise(nb.vmath("MULTIPLY", P, (1, 1, 0)), 6.0, 3.0, 0.5)
    h = nb.math("ADD", nb.math("MULTIPLY", ripple, 0.15), nb.math("MULTIPLY", weed, 1.0))
    node = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": col, "Roughness": rough, "IOR": 1.33,
                                            "Specular IOR Level": 0.35, "Normal": nb.bump(h, 1.0, 0.01)})
    finish(nb, outn, nb.out(node, "BSDF"))
    return m


def water(coll):
    import lib as _lib
    if "voda_prikop" not in _lib.MAT:
        _lib.MAT["voda_prikop"] = mat_pond("voda_prikop")
    P = Part("Prikop_voda")
    verts, faces, idx, vals = [], [], {}, []
    # cely prstenec kolem tvrze (i za zapadni hradbou, ta je o EXT dal)
    step = 0.7
    X0, Z0 = -44.0, -34.0
    n = int(82 / step)
    for i in range(n + 1):
        for k in range(n + 1):
            x, z = X0 + i * step, Z0 + k * step
            idx[(i, k)] = len(verts)
            verts.append((x, WATER_Y, z))
    for i in range(n):
        for k in range(n):
            cx, cz = X0 + (i + 0.5) * step, Z0 + (k + 0.5) * step
            d = F.rect_dist(cx, cz)
            if 3.0 < d < 11.5 and F.land(cx, cz) < WATER_Y + 0.4 and not (abs(cx) < 2.0 and cz > 15):
                faces.append((idx[(i, k)], idx[(i, k + 1)], idx[(i + 1, k + 1)], idx[(i + 1, k)]))
    P.mesh(verts, faces, "voda_prikop")
    o = P.commit(coll)
    me = o.data
    at = me.attributes.new("breh", "FLOAT", "POINT")
    vals = []
    for v in me.vertices:
        x, z = v.co.x, -v.co.y
        depth = WATER_Y - F.land(x, z)
        vals.append(min(1.0, max(0.0, depth / 0.8)))
    at.data.foreach_set("value", vals)
    # bridge pres vodu bez vody pod mostem je v poradku (most stoji na kozach ve vode)
    return o


# ------------------------------------------------------------------ rakos (vlastni geometrie)

def reeds(P: Part, c, n=30, h=1.6, r=0.45):
    """Trs rakosu/orobince: dlouhe prohnute listy, nekolik stonku s hnedou palicí."""
    c = Vector(c)
    for _ in range(n):
        a = R.uniform(0, 2 * math.pi)
        rr = r * math.sqrt(R.random())
        base = c + Vector((math.cos(a) * rr, 0, math.sin(a) * rr))
        hh = h * R.uniform(0.55, 1.1)
        lean = Vector((jit(1), 0, jit(1))).normalized() * hh * R.uniform(0.05, 0.3)
        w = R.uniform(0.012, 0.022)
        side = Vector((math.cos(a + 1.57), 0, math.sin(a + 1.57))) * w
        pts = []
        segs = 5
        for s_ in range(segs + 1):
            t = s_ / segs
            p = base + Vector((0, hh * t, 0)) + lean * (t * t)
            ww = (1 - t * 0.9)
            pts.append((p - side * ww, p + side * ww))
        for s_ in range(segs):
            P.face([pts[s_][0], pts[s_][1], pts[s_ + 1][1], pts[s_ + 1][0]], "rakos",
                   uvs=[(0, s_ / segs), (1, s_ / segs), (1, (s_ + 1) / segs), (0, (s_ + 1) / segs)])
    for _ in range(max(1, n // 8)):
        a = R.uniform(0, 2 * math.pi)
        base = c + Vector((math.cos(a), 0, math.sin(a))) * r * 0.6 * R.random()
        hh = h * R.uniform(0.9, 1.25)
        top = base + Vector((jit(0.08), hh, jit(0.08)))
        P.rod(base, top, 0.006, 4, "rakos")
        P.rod(top - Vector((0, 0.32, 0)), top - Vector((0, 0.12, 0)), 0.022, 7, "orobinec")


# ------------------------------------------------------------------ rozmisteni

def scatter(coll, paths, inside=True, outside=True, forest=True):
    import nove
    V = bpy.data.collections.new("Vegetace")
    coll.children.link(V)
    count = {}

    lesni_v2 = {"dub": ["dub_stredni", "dub_stredni", "dub_stary"], "lipa": ["lipa_stredni", "lipa_stara"]}

    def put(pid, pos, h, **kw):
        if pid in lesni_v2:
            # listnace v lese a na okrajich: kvalitni stromy v2 (vzdalene verze az za 220 m)
            nove.strom(R.choice(lesni_v2[pid]), pos[0], pos[1], pos[2], max(9.0, h))
            count[pid] = count.get(pid, 0) + 1
            return
        if place(V, pid, pos, h, **kw):
            count[pid] = count.get(pid, 0) + 1

    def ground_out(x, z):
        return F.land(x, z)

    import yard
    blocked_in = yard.BLOCKED + [(-9.6, -3.0, -7.4, -5.4), (-4.9, -2.3, -2.9, -0.3)]

    def free_in(x, z):
        return not any(a <= x <= b and c <= z <= d for a, b, c, d in blocked_in)

    # --- uvnitr: trava a kopřivy u paty zdi a v koutech, pampelisky v trave, naletovy stromek
    if inside:
        for _ in range(4200):
            x, z = R.uniform(F.WIX + 0.15, F.IX - 0.15), R.uniform(-F.IZ + 0.15, F.IZ - 0.15)
            if not free_in(x, z):
                continue
            dw = min(F.HIX - abs(x - F.CX), F.IZ - abs(z))
            dp = min(F.path_dist(x, z, p) for p in paths)
            if dw < 0.9:
                k = R.random()
                if k < 0.55:
                    put("grass_medium_01", (x, 0.0, z), R.uniform(0.18, 0.4))
                elif k < 0.8:
                    put("nettle_plant", (x, 0.0, z), R.uniform(0.25, 0.45))
                elif k < 0.9:
                    put("grass_medium_02", (x, 0.0, z), R.uniform(0.2, 0.4))
                else:
                    put("grass_medium_02", (x, 0.0, z), R.uniform(0.25, 0.5))
            elif dp > 2.0 and R.random() < 0.55 * F.smooth(2.0, 4.0, dp):
                k = R.random()
                if k < 0.7:
                    put("grass_medium_01", (x, 0.0, z), R.uniform(0.12, 0.3))
                elif k < 0.85:
                    put("grass_medium_02", (x, 0.0, z), R.uniform(0.15, 0.35))
                elif k < 0.95:
                    put("dandelion_01", (x, 0.0, z), R.uniform(0.15, 0.3))
                else:
                    put("grass_medium_02", (x, 0.0, z), R.uniform(0.15, 0.3))
        # vysoka trava u paty zdi uvnitr
        for _ in range(2500):
            x, z = R.uniform(F.WIX + 0.1, F.IX - 0.1), R.uniform(-F.IZ + 0.1, F.IZ - 0.1)
            if not free_in(x, z) or min(F.HIX - abs(x - F.CX), F.IZ - abs(z)) > 0.7:
                continue
            put("divoka_trava", (x, -0.01, z), R.uniform(0.4, 0.8), tilt=0.1)
        # naletove stromky a keriky v koutech
        for (x, z) in ((-24.3, 7.5), (16.2, 9.6), (-17.0, -8.2), (16.3, -6.2)):
            put("shrub_02", (x, 0.0, z), R.uniform(0.9, 1.4))
        put("briza", (15.9, 0.0, -4.2), 2.6)
        put("briza", (-24.3, 0.0, 4.0), 1.8)
        put("sipek", (-24.2, 0.0, 6.0), 1.1)
        put("sipek", (15.9, 0.0, -2.5), 1.3)
        for (x, z) in ((-4.8, -2.4), (-2.3, -0.4)):
            put("fern_02", (x, 0.0, z), 0.5)

    # --- venku: pata hradeb, svahy prikopu, louka
    if outside:
        for _ in range(16000):
            x, z = R.uniform(-60, 48), R.uniform(-44, 52)
            d = F.rect_dist(x, z)
            if d < 0.05 or (abs(x) < 2.4 and z > 15.8):
                continue
            y = ground_out(x, z)
            if y < F.land(x, z) - 0.01:
                continue
            if 4.0 < d < 10.5 and y < WATER_Y + 0.05:
                continue                      # pod vodou
            if d < 1.6:
                k = R.random()
                if k < 0.4:
                    put("nettle_plant", (x, y, z), R.uniform(0.25, 0.45))
                elif k < 0.75:
                    put("grass_medium_02", (x, y, z), R.uniform(0.3, 0.6))
                elif k < 0.9:
                    put("grass_medium_02", (x, y, z), R.uniform(0.25, 0.45))
                elif z < -10 or x < -15:
                    put("fern_02", (x, y, z), R.uniform(0.5, 0.9))
                else:
                    put("grass_medium_01", (x, y, z), R.uniform(0.25, 0.45))
            elif d < 12.5:
                k = R.random()
                if k < 0.45:
                    put("grass_medium_02", (x, y, z), R.uniform(0.3, 0.65))
                elif k < 0.75:
                    put("grass_medium_01", (x, y, z), R.uniform(0.2, 0.45))
                elif k < 0.85:
                    put("nettle_plant", (x, y, z), R.uniform(0.25, 0.45))
                elif k < 0.93:
                    put("dandelion_01", (x, y, z), R.uniform(0.2, 0.35))
                else:
                    put("grass_medium_02", (x, y, z), R.uniform(0.3, 0.5))
            elif R.random() < 0.6:
                k = R.random()
                if k < 0.6:
                    put("grass_medium_01", (x, y, z), R.uniform(0.2, 0.45))
                elif k < 0.85:
                    put("grass_medium_02", (x, y, z), R.uniform(0.3, 0.6))
                else:
                    put("dandelion_01", (x, y, z), R.uniform(0.2, 0.35))
        # husta neposecena trava: svahy prikopu, pata hradeb, louka kolem tvrze
        for _ in range(42000):
            x, z = R.uniform(-48, 40), R.uniform(-38, 44)
            d = F.rect_dist(x, z)
            if d < 0.08 or (abs(x) < 2.6 and z > 15.8):
                continue
            y = F.land(x, z)
            if y < WATER_Y - 0.05:
                continue
            dens = 1.0 if d < 14 else 0.55 * (1 - F.smooth(14, 30, d)) + 0.1
            if R.random() > dens:
                continue
            ob = place(V, "divoka_trava", (x, y - 0.02, z), R.uniform(0.55, 1.05) * (1.15 if d < 1.6 or y < WATER_Y + 0.6 else 1.0), tilt=0.12)
            if ob:
                count["divoka_trava"] = count.get("divoka_trava", 0) + 1
        # keře a naletove stromky u hradeb a na svazich prikopu
        spots = 0
        tries = 0
        while spots < 150 and tries < 12000:
            tries += 1
            x, z = R.uniform(-52, 44), R.uniform(-42, 48)
            d = F.rect_dist(x, z)
            if (abs(x) < 4.5 and z > 15) or not (0.4 < d < 4.6 or 9.6 < d < 26):
                continue
            y = ground_out(x, z)
            if y < WATER_Y + 0.1:
                continue
            k = R.random()
            # houstiny: k keri pribude par dalsich keru kolem
            if k < 0.55 and d > 9.6:
                for _ in range(R.randint(1, 3)):
                    ox, oz = x + R.uniform(-1.6, 1.6), z + R.uniform(-1.6, 1.6)
                    oy = ground_out(ox, oz)
                    if oy > WATER_Y + 0.1 and not (abs(ox) < 4.5 and oz > 15):
                        put("sipek" if R.random() < 0.5 else "shrub_02", (ox, oy, oz), R.uniform(0.8, 1.8))
            # u hradeb a prikopu naletove brizy a kere (sipek, liska), zadne smrky
            if k < 0.25:
                put("shrub_02", (x, y, z), R.uniform(1.0, 2.2))
            elif k < 0.55:
                put("sipek", (x, y, z), R.uniform(1.0, 2.0))
            elif k < 0.8:
                put("briza", (x, y, z), R.uniform(1.6, 4.0))
            else:
                put("briza", (x, y, z), R.uniform(5.0, 9.0))
            spots += 1
        # kameny s mechem, parez, spadle vetve u vody a na svazich
        for _ in range(60):
            x, z = R.uniform(-42, 34), R.uniform(-32, 32)
            d = F.rect_dist(x, z)
            if (abs(x) < 3 and z > 15) or not (3.5 < d < 12.0):
                continue
            put("rock_moss_set_01", (x, ground_out(x, z) - 0.25, z), R.uniform(0.4, 1.0))
        for _ in range(18):
            x, z = R.uniform(-42, 34), R.uniform(-32, 32)
            d = F.rect_dist(x, z)
            if (abs(x) < 3 and z > 15) or not (2.0 < d < 13.0):
                continue
            ob = place(V, "dry_branches_medium_01", (x, ground_out(x, z) + 0.05, z), R.uniform(0.9, 1.5))
            if ob:
                ob.rotation_euler = (jit(0.12), jit(0.12), R.uniform(0, 2 * math.pi))
        put("tree_stump_01", (-24.0, F.land(-24.0, 6.0), 6.0), 0.55)
        put("tree_stump_01", (21.5, F.land(21.5, -20.5), -20.5), 0.5)

    # --- les: smrky a borovice, podrost z mladych stromku
    if forest:
        placed = []
        tries = 0
        while len(placed) < 340 and tries < 40000:
            tries += 1
            x = R.uniform(-150, 150)
            z = R.uniform(-140, 160)
            d = F.rect_dist(x, z)
            if d < 24 or (abs(x) < 10 and z > 0) or (abs(x - 0.25 * (z - 20)) < 9 and z > 20):
                continue
            dens = 0.22 + 0.75 * F.smooth(-20, -60, z) + 0.5 * F.smooth(-20, -70, x)
            if R.random() > dens:
                continue
            if any((x - a) ** 2 + (z - b) ** 2 < 14 for a, b in placed):
                continue
            placed.append((x, z))
            y = F.land(x, z)
            k = R.random()
            # les: smrky, na okraji vic briz
            edge = 1.0 - F.smooth(30, 60, d)
            if k < 0.7 - 0.35 * edge:
                put("smrk", (x, y, z), R.uniform(14, 24))
            elif k < 0.9:
                put("briza", (x, y, z), R.uniform(10, 17))
            else:
                put("smrk", (x, y, z), R.uniform(5, 9))
        # sirsi krajina (kraj.py): lesy na kopcich a na skalnim hrebeni, osamele stromy na mezich
        import kraj
        for x, z, kind, f in kraj.tree_spots(R):
            if kraj.v_skale(x, z, 1.5):
                continue                                  # strom by rostl skrz skalni vez
            y = F.land(x, z)
            k = R.random()
            if kind == "les" and kraj.skaly_podstava(x, z) > 2.0:
                # ve skalnim meste borovice (na piskovci), mezi nimi brizy
                if k < 0.7:
                    put("borovice", (x, y, z), R.uniform(5.0, 14.0))
                else:
                    put("briza", (x, y, z), R.uniform(6.0, 13.0))
                continue
            if kind == "les":
                # smiseny les: uprostred smrky, na okraji (f mensi) duby, lipy a brizy
                listn = 0.15 + 0.55 * (1.0 - min(1.0, (f - 0.5) * 2.5))
                if k < 1.0 - listn:
                    put("smrk", (x, y, z), R.uniform(13, 25) if R.random() < 0.85 else R.uniform(4, 8))
                elif k < 1.0 - listn * 0.55:
                    put("dub", (x, y, z), R.uniform(11, 17))
                elif k < 1.0 - listn * 0.25:
                    put("lipa", (x, y, z), R.uniform(12, 18))
                else:
                    put("briza", (x, y, z), R.uniform(9, 16))
            else:
                # samotne stromy na pastvinach a mezich: hlavne duby a lipy, nekdy briza
                # solitery na mezich a pastvinach: stare duby a lipy (stromy v2, zblizka plne, daleko karty)
                import nove
                if k < 0.5:
                    nove.strom("dub_stary" if R.random() < 0.45 else "dub_stredni", x, y, z, R.uniform(11, 19))
                elif k < 0.8:
                    nove.strom("lipa_stara" if R.random() < 0.4 else "lipa_stredni", x, y, z, R.uniform(12, 20))
                else:
                    put("briza", (x, y, z), R.uniform(8, 16))
        import nove
        # potok Bystrice: olse po brezich, sem tam vrba hlavata (stromy v2)
        Rr = random.Random(77)
        acc = 0.0
        for (ax, az), (bx, bz) in zip(kraj.REKA[:-1], kraj.REKA[1:]):
            L = math.hypot(bx - ax, bz - az)
            if L < 1e-3:
                continue
            nx, nz = -(bz - az) / L, (bx - ax) / L
            s_ = acc % 1.0
            while s_ < L:
                side = Rr.choice((-1, 1))
                off = Rr.uniform(5.5, 9.0)
                x, z = ax + (bx - ax) * s_ / L + nx * off * side, az + (bz - az) * s_ / L + nz * off * side
                if not kraj.road_near(x, z) or kraj.road_near(x, z)[0] > kraj.road_near(x, z)[3] + 3.0:
                    q = Rr.random()
                    if q < 0.55:
                        nove.strom("olse_stredni", x, F.land(x, z), z, Rr.uniform(11, 16))
                    elif q < 0.8:
                        nove.strom("olse_mlada", x, F.land(x, z), z, Rr.uniform(6, 9))
                    else:
                        nove.strom(Rr.choice(["vrba_hlavata_1", "vrba_hlavata_2"]), x, F.land(x, z), z, Rr.uniform(5.5, 7.5))
                s_ += Rr.uniform(16.0, 34.0)
            acc += L
        # rybnik ve vsi: rakos a orobinec v trsech na mělcine u brehu (ne dokola stejne), dal vrby hlavate a olse
        import vesnice
        a0_ = Rr.uniform(0, 2 * math.pi)
        a_ = a0_
        while a_ < a0_ + 2 * math.pi:
            if Rr.random() < 0.7:                       # trs, mezi trsy volny breh
                pid0 = Rr.choice(["orobinec_1", "orobinec_2", "rakos_1", "rakos_2"])
                for _ in range(Rr.randint(4, 9)):
                    x, z = vesnice.pond_point(a_ + Rr.uniform(-0.12, 0.12), Rr.uniform(0.86, 1.08))
                    pid = pid0 if Rr.random() < 0.8 else Rr.choice(["orobinec_1", "rakos_2"])
                    nove.misto(pid, x, F.land(x, z), z, Rr.uniform(0.75, 1.15), Rr.uniform(0, 2 * math.pi), None, sink=0.05)
            a_ += Rr.uniform(0.35, 0.7)
        for i in range(7):
            x, z = vesnice.pond_point(i / 7 * 2 * math.pi + Rr.uniform(-0.3, 0.3), Rr.uniform(1.3, 1.6))
            if i % 3 == 2:
                nove.strom("olse_mlada", x, F.land(x, z), z, Rr.uniform(6, 8.5))
            else:
                nove.strom(Rr.choice(["vrba_hlavata_1", "vrba_hlavata_2"]), x, F.land(x, z), z, Rr.uniform(5.0, 7.0))
        nove.rozmistit(V, place, LIB)
        import ruiny
        for pid, x, z, h in ruiny.ROSTLINY:
            put(pid, (x, F.land(x, z), z), h)
        for pid, x, z, h, y in kraj.ROCK_PLANTS:
            put(pid, (x, F.land(x, z) if y is None else y, z), h)
        # obrost kolem domu (chalupy ve vsi, hostinec, stan): u zdi kopřivy, vysoka trava, keriky, pampelisky
        Ro = random.Random(808)
        obvody = []
        for c, au, av, hu, hv, yp in vesnice_pads():
            obvody.append((c.x, c.z, (au.x, au.z), (av.x, av.z), hu, hv))
        for id_, (x0, x1, y0, y1) in kraj.PUDORYS.items():
            cx, cz = kraj.stavba_bod(id_, (x0 + x1) / 2, (y0 + y1) / 2)
            yaw = kraj.stavba_yaw(id_)
            obvody.append((cx, cz, (math.cos(yaw), -math.sin(yaw)), (math.sin(yaw), math.cos(yaw)), (x1 - x0) / 2, (y1 - y0) / 2))
        for cx, cz, au, av, hu, hv in obvody:
            per = 4 * (hu + hv)
            for _ in range(int(per * 1.4)):
                # bod na obvodu, 0.2-2.2 m od zdi ven (u rohu a zadnich sten hustsi)
                t = Ro.uniform(-1, 1)
                side = Ro.randrange(4)
                off = 0.2 + Ro.random() ** 1.6 * 2.0
                if side < 2:
                    u, v = t * hu, (hv + off) * (1 if side == 0 else -1)
                else:
                    u, v = (hu + off) * (1 if side == 2 else -1), t * hv
                x = cx + au[0] * u + av[0] * v
                z = cz + au[1] * u + av[1] * v
                if kraj.road_near(x, z) and kraj.road_near(x, z)[0] < 2.0:
                    continue
                c = Ro.random()
                pid = "nettle_plant" if c < 0.3 else ("divoka_trava" if c < 0.6 else ("grass_medium_02" if c < 0.75 else
                      ("shrub_02" if c < 0.85 else ("dandelion_01" if c < 0.95 else "sipek"))))
                h = {"nettle_plant": Ro.uniform(0.6, 1.2), "divoka_trava": Ro.uniform(0.5, 1.0), "shrub_02": Ro.uniform(0.6, 1.3),
                     "sipek": Ro.uniform(0.7, 1.4)}.get(pid, Ro.uniform(0.3, 0.6))
                put(pid, (x, F.land(x, z) - (0.02 if pid == "divoka_trava" else 0.0), z), h)
        import vesnice
        for pid, x, z, h in vesnice.village_trees():
            put(pid, (x, F.land(x, z), z), h)
        for pid, x, z, h, tilt in kraj.plant_spots(R):
            put(pid, (x, F.land(x, z) - (0.02 if pid == "divoka_trava" else 0.0), z), h, tilt=tilt)
        # podrost na okraji lesa
        for (x, z) in placed:
            if R.random() < 0.35:
                for _ in range(R.randint(1, 3)):
                    xx, zz = x + jit(3), z + jit(3)
                    put(R.choice(["fern_02", "sipek", "shrub_02", "briza"]), (xx, F.land(xx, zz), zz), R.uniform(0.6, 1.8))

    # --- rakos u vody
    Rk = Part("Rakos")
    clusters = 0
    tries = 0
    while clusters < 34 and tries < 6000:
        tries += 1
        x, z = R.uniform(-42, 34), R.uniform(-32, 32)
        d = F.rect_dist(x, z)
        if not (3.0 < d < 11.5) or (abs(x) < 3 and z > 15):
            continue
        y = F.land(x, z)
        if not (WATER_Y - 0.35 < y < WATER_Y + 0.2):
            continue
        for _ in range(R.randint(2, 6)):
            xx, zz = x + jit(1.2), z + jit(1.2)
            reeds(Rk, (xx, max(F.land(xx, zz), WATER_Y - 0.4), zz), R.randint(18, 40), R.uniform(1.2, 2.0), R.uniform(0.25, 0.5))
        clusters += 1
    # rakos jen misty u potoka (v tisinach a zatokach), jinde jen kere a trava
    import kraj
    br = kraj.bridge()
    for i in range(0, len(kraj.REKA), 6):
        if R.random() > 0.3:
            continue
        x, z = kraj.REKA[i]
        if not (kraj.ACT[0] + 8 < x < kraj.ACT[1] - 8 and kraj.ACT[2] + 8 < z < kraj.ACT[3] - 8):
            continue
        if br and math.hypot(x - br[0], z - br[1]) < 16.0:
            continue
        a_, b_ = kraj.REKA[max(0, i - 1)], kraj.REKA[min(len(kraj.REKA) - 1, i + 1)]
        L = math.hypot(b_[0] - a_[0], b_[1] - a_[1]) or 1.0
        nx, nz = -(b_[1] - a_[1]) / L, (b_[0] - a_[0]) / L
        wl = F.land(x, z) + 0.75
        sd = R.choice((-1, 1))
        for _ in range(R.randint(2, 5)):
            o = sd * R.uniform(3.4, 5.0)
            xx, zz = x + nx * o + jit(1.5), z + nz * o + jit(1.5)
            reeds(Rk, (xx, max(F.land(xx, zz), wl - 0.4), zz), R.randint(18, 40), R.uniform(1.2, 2.0), R.uniform(0.25, 0.5))
    Rk.commit(V)
    print("vegetace", sum(count.values()), count)
