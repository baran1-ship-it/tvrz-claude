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
    e = bpy.data.objects[koren]
    casti = [o for o in e.children if o.type == "MESH" and o.name.split("_", 1)[1] in nazvy]
    if not casti:
        return None
    barva = _prumer_barvy(casti)
    kopie = []
    for o in casti:
        c = o.copy()
        c.data = o.data.copy()
        c.parent = None
        c.matrix_world = o.matrix_world.copy()
        bpy.context.scene.collection.objects.link(c)
        kopie.append(c)
    bpy.ops.object.select_all(action="DESELECT")
    for c in kopie:
        c.select_set(True)
    bpy.context.view_layer.objects.active = kopie[0]
    bpy.ops.object.join()
    d = bpy.context.view_layer.objects.active
    rm = d.modifiers.new("rm", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = vox
    bpy.ops.object.modifier_apply(modifier="rm")
    troj = sum(len(p.vertices) - 2 for p in d.data.polygons)
    dc = d.modifiers.new("dec", "DECIMATE")
    dc.ratio = min(1.0, cil / max(troj, 1))
    bpy.ops.object.modifier_apply(modifier="dec")
    m = bpy.data.materials.new(koren + "_daleko_" + nazvy[0])
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (barva[0], barva[1], barva[2], 1.0)
    bs.inputs["Roughness"].default_value = 0.95
    d.data.materials.clear()
    d.data.materials.append(m)
    for p in d.data.polygons:
        p.use_smooth = False
    print("%s daleko %s: %d -> %d troj, barva %s" % (koren, nazvy[0], troj, sum(len(p.vertices) - 2 for p in d.data.polygons), [round(c, 2) for c in barva]))
    return d


for koren in KORENY:
    dily = [x for x in (_daleko(koren, STRECHA, 1400, 0.12), _daleko(koren, STENY, 1600, 0.1)) if x]
    bpy.ops.object.select_all(action="DESELECT")
    for x in dily:
        x.select_set(True)
    bpy.context.view_layer.objects.active = dily[0]
    bpy.ops.object.join()
    d = bpy.context.view_layer.objects.active
    d.name = koren + "_Daleko"
    d.parent = bpy.data.objects[koren]

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
    # stejny material ve vice slotech -> jeden slot
    jedn = {}
    mapa = []
    for m in d.data.materials:
        k = m.name if m else ""
        jedn.setdefault(k, len(jedn))
        mapa.append(jedn[k])
    mats = {}
    for m in d.data.materials:
        mats.setdefault(m.name if m else "", m)
    for p in d.data.polygons:
        p.material_index = mapa[p.material_index]
    d.data.materials.clear()
    for k in jedn:
        d.data.materials.append(mats[k])
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
