"""Nove domy vsi Lhota (modelar, 25. 10.; Disk slozka "budovy" 1O1VPNjyMNDCDxm4SB3nm64OKGnopwb5x, NAVOD.md v kazdem zipu):
dum1_lhota (roubeny, sindel, hrazdeny stit), dum2_lhota (omitnuty, doskova valba), dum3_rychta (kamenna patrova
komora), chyse_A (kura / prkna). Vsechny do jednoho modely/ves/domy.glb, kazdy model pod vlastnim korenem
(Dum1, Dum2, Rychta, ChyseKura, ChysePrkna) - stejne textury (rough_wood, clay_plaster...) jen jednou.
Stazeni: curl -sSL -o x.zip "https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t"
Uprava: duplicitni obrazky sloucene podle obsahu, roughness 512, ostatni max 1024 (rozpocet tabletu).
  /opt/bl/bin/python -I ves_domy.py -- <dum1.glb> <dum2.glb> <dum3.glb> <chata_kura.glb> <chata_prkna.glb> ../modely/ves/domy.glb"""
import hashlib
import sys

import bpy

KORENY = ["Dum1", "Dum2", "Rychta", "ChyseKura", "ChysePrkna"]
args = sys.argv[sys.argv.index("--") + 1:]
vstupy, vystup = args[:-1], args[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
for koren, f in zip(KORENY, vstupy):
    pred = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    nove = [o for o in bpy.data.objects if o not in pred]
    e = bpy.data.objects.new(koren, None)
    bpy.context.scene.collection.objects.link(e)
    for o in nove:
        if o.parent is None:
            o.parent = e
        # jmeno: <koren>_<cast>; pripona -convcolonly zustava na konci (Godot z ni dela kolizi)
        jm = o.name.split(".")[0]
        cast = jm.split("_", 1)[1] if "_" in jm else jm
        o.name = koren + "_" + cast

# dalkova verze (NAVOD: "nad 60 m LOD se strechou z jedne plochy"; ves mela 2 000 kresleni a 3,4 M troj.): strecha
# a steny zvlast, voxel remesh (sindel po sindeli i tramy jsou samostatne kusy - decimace by je rozpustila na diry)
# a decimace; barva = prumer textury (z dalky detail neni videt) - 1 sit s 2 materialy na dum
STRECHA = ("Sindel", "Dosky", "Krytina")
STENY = ("Roubeni", "Podezdivka", "Stity", "Hrazdeni", "Omitka", "Krov", "Komora", "Konstrukce", "Zidka", "Okna")


def _prumer_barvy(objs):
    s = [0.0, 0.0, 0.0]
    n = 0
    for o in objs:
        for m in o.data.materials:
            if not m or not m.use_nodes:
                continue
            for nd in m.node_tree.nodes:
                if nd.type == "TEX_IMAGE" and nd.image and "diff" in nd.image.name or (nd.type == "TEX_IMAGE" and nd.image and "albedo" in nd.image.name):
                    px = nd.image.pixels[:]
                    k = max(1, len(px) // 4 // 4000)
                    for i in range(0, len(px) // 4, k):
                        for c in range(3):
                            s[c] += px[i * 4 + c]
                        n += 1
                    break
    # pixely textury jsou sRGB, Base Color je linearni (0,27 sRGB = 0,06 lin.; bez prevodu svitily domy z dalky bile)
    return [(c / max(n, 1)) ** 2.2 for c in s] if n else [0.12, 0.09, 0.07]


def _daleko(koren, nazvy, cil, vox):
    """Dalkova sit: konvexni obal dilu (strecha = hranol/jehlan, steny = kvadr). Voxel remesh sindelu po sindeli a
    doskach rozpustil plochu strechy - z dalky byl videt jen krov (Misa 0.78 "krovy, strecha az zblizka")."""
    import bmesh
    e = bpy.data.objects[koren]
    casti = [o for o in e.children if o.type == "MESH" and o.name.split("_", 1)[1] in nazvy]
    if not casti:
        return None
    barva = _prumer_barvy(casti)
    bm = bmesh.new()
    for o in casti:
        for v in o.data.vertices:
            bm.verts.new(o.matrix_world @ v.co)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.dissolve_limit(bm, angle_limit=0.05, verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    me = bpy.data.meshes.new(koren + "_d_" + nazvy[0])
    bm.to_mesh(me)
    bm.free()
    d = bpy.data.objects.new(me.name, me)
    bpy.context.scene.collection.objects.link(d)
    m = bpy.data.materials.new(koren + "_daleko_" + nazvy[0])
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (barva[0], barva[1], barva[2], 1.0)
    bs.inputs["Roughness"].default_value = 0.95
    d.data.materials.append(m)
    print("%s daleko %s: obal %d troj, barva %s" % (koren, nazvy[0], len(me.polygons), [round(c, 2) for c in barva]))
    return d


for koren in KORENY:
    dily = [x for x in (_daleko(koren, STRECHA, 0, 0), _daleko(koren, ("Roubeni", "Podezdivka", "Omitka", "Zidka", "Komora"), 0, 0)) if x]
    bpy.ops.object.select_all(action="DESELECT")
    for x in dily:
        x.select_set(True)
    bpy.context.view_layer.objects.active = dily[0]
    bpy.ops.object.join()
    d = bpy.context.view_layer.objects.active
    d.name = koren + "_Daleko"
    d.parent = bpy.data.objects[koren]

# Misa 0.78: "nastipane drevo u novych modelu hrozne, odstranit" - hranice polen z Doplnku domu (kura + zhlavi);
# u chysi cele Doplnky (spalek, polena, ohniste, kotlik, lavice) a jejich kolize - doplni se pozdeji
for koren in KORENY:
    e = bpy.data.objects[koren]
    for o in list(e.children):
        cast = o.name.split("_", 1)[1]
        if koren.startswith("Chyse") and (cast == "Doplnky" or cast.startswith("Kol_Polena") or cast.startswith("Kol_Spalek")):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        if cast == "Doplnky" and o.type == "MESH":
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(o.data)
            pryc = [f for f in bm.faces if f.material_index < len(o.data.materials) and o.data.materials[f.material_index]
                    and o.data.materials[f.material_index].name.split(".")[0] in ("M_Kura", "M_Zhlavi")]
            bmesh.ops.delete(bm, geom=pryc, context="FACES")
            bm.to_mesh(o.data)
            bm.free()
            print("%s: polena pryc %d ploch" % (koren, len(pryc)))

# rychta: patro komory (strop 1,71 m nad podlahou sine) tesne nad schody dolu do komory - hrac (1,76 m) narazil hlavou
# hned za dvermi (Misa 0.78 "do komory z chodby nelze, tram ve dverich"). Otvor v podlaze patra nad schody
# (Blender y 4,6..5,5 = hra z -4,6..-5,5), kolize patra zkracena.
import bmesh as _bm
_k = bpy.data.objects.get("Rychta_Komora")
if _k:
    bm = _bm.new()
    bm.from_mesh(_k.data)
    pryc = []
    for f in bm.faces:
        c = _k.matrix_world @ f.calc_center_median()
        if -1.55 < c.x < -0.45 and 4.55 < c.y < 5.55 and 1.6 < c.z < 2.05:
            pryc.append(f)
    _bm.ops.delete(bm, geom=pryc, context="FACES")
    bm.to_mesh(_k.data)
    bm.free()
    print("rychta: otvor nad schody komory %d ploch" % len(pryc))
for _o in bpy.data.objects:
    if _o.name.startswith("Rychta_Kol_KomoraPatro") and _o.type == "MESH":
        ys = [(_o.matrix_world @ v.co).y for v in _o.data.vertices]
        if min(ys) < 5.0 < max(ys):
            inv = _o.matrix_world.inverted()
            for v in _o.data.vertices:
                w = _o.matrix_world @ v.co
                if w.y < 5.55:
                    w.y = 5.55
                    v.co = inv @ w
            print("rychta: kolize %s zkracena" % _o.name)

# kresleni: vnejsek (steny, strecha, stity) a drobnosti (okna, doplnky) slouceny do jedne site, povrchy podle materialu
# (M_Roubeni v osmi castech = jeden povrch); dvere, vnitrek, kolize a daleko zustavaji zvlast
DROBNE = ("Okna", "Doplnky")


def _spoj(koren, nazvy, jmeno):
    e = bpy.data.objects[koren]
    casti = [o for o in e.children if o.type == "MESH" and o.name.split("_", 1)[1] in nazvy]
    if len(casti) < 1:
        return
    bpy.ops.object.select_all(action="DESELECT")
    for o in casti:
        o.select_set(True)
    bpy.context.view_layer.objects.active = casti[0]
    if len(casti) > 1:
        bpy.ops.object.join()
    d = bpy.context.view_layer.objects.active
    # stejne materialy spojuje join sam (stejny datablok = jeden slot); vlastni preindexovani (clear + append) dalo
    # vsem plocham material 0 - rychta cela z roubeni, kamenna komora nebyla videt (Misa 0.78 "rychta tu neni")
    jedn = {m.name for m in d.data.materials if m}
    d.name = koren + "_" + jmeno
    print("%s_%s: %d casti, %d materialu" % (koren, jmeno, len(casti), len(jedn)))


for koren in KORENY:
    _spoj(koren, STRECHA + STENY[:-1], "Vnejsek")
    _spoj(koren, DROBNE + ("Okna",), "Drobne")

# obrazky: stejny obsah = jeden obrazek
pod = {}
for im in list(bpy.data.images):
    if im.size[0] == 0:
        continue
    px = im.pixels[:]
    h = hashlib.md5(str((im.size[0], im.size[1], px[::997])).encode()).hexdigest()
    if h in pod:
        im.user_remap(pod[h])
        bpy.data.images.remove(im)
    else:
        pod[h] = im
for im in bpy.data.images:
    lim = 512 if "rough" in im.name else 1024
    if im.size[0] > lim:
        im.scale(lim, lim * im.size[1] // im.size[0])
print("obrazku %d" % len(bpy.data.images))
bpy.ops.export_scene.gltf(filepath=vystup, export_format="GLB", export_apply=True, export_yup=True, export_image_format="AUTO",
                          export_extras=True)
