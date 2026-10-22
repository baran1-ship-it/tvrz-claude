"""Stromy z Misova Disku (slozka Modely) do hry (blok 0.63 LES): z balicku modelu vybrat strom (rodicovsky objekt),
spojit jeho site se zachovanim polohy (listi byva dite vetvi), pata na 0, stred kmene v 0, vyska jako dosavadni
strom ve hre; vystup glb se sitemi pojmenovanymi jako klice v svet.json rostliny (<druh>_<n>).
  /opt/bl/bin/python blender/stromy.py <druh> <zdroj.glb> <vystup.glb>
Druhy a zdroje (licence do titulku - CC-BY 4.0):
  briza    five_birch_trees_pack_lowpoly_lods.glb (LOLIPOP) - LOD2 kazde ze 4 briz
  dub      oak_trees.glb (DJMaesen) - viz blender/duby_nove.py
  ker_husty bushcover (Misuv Disk, CC-BY) - hustý nízký keř do lesa (0.63, Misa: "chybi kere")
  kapradi_les veg.glb (Misuv Disk, CC-BY) - kapradi "paporotnik" 1 a 2 na lesni pudu
  smrk     forest.glb "Low Poly Forest Tree Pack" (99.Miles, CC-BY 4.0) - 3 smrky (kmen + vetve), 5 variant (2 zrcadlene)
  borovice, buk_stredni, lipa_stredni, lipa_stara, olse_stredni, olse_mlada
           mountain.glb "Mountain Trees" (Jagobo, CC-BY 4.0) - kura decimovana, karty listi prorezane (rozpocet tabletu
           do ~6k troj.), zbyle karty o kousek vetsi; olse = osika s listim prebarvenym do tmave zelene
Zaznam: (koren[+koren2], jmeno site, vyska m[, zapust, sirka, volby]); volby: kura = podil troj. kury po decimaci,
  listi = podil ponechanych karet, zrcadlo = zrcadleni X (dalsi varianta ze stejneho modelu), barva = nasobek listi RGB"""
import sys, bpy, mathutils

DRUHY = {
    # druh: [(objekt rodic ve zdroji, jmeno site ve hre, vyska m)]
    "briza": [("Birch_LOD2", "briza_0", 13.2), ("Birch_2_LOD2", "briza_1", 13.2), ("Birch_3_LOD2", "briza_2", 13.2),
              ("Birch_5_LOD2", "briza_3", 13.2)],
    "ker_husty": [("Bushcover_LOD0_0", "ker_husty_0", 1.7, 0.1)],
    "kapradi_les": [("3", "kapradi_les_0", 0.6, 0.05, 1.3), ("4", "kapradi_les_1", 0.5, 0.05, 1.0)],
    # 0.63 LES: vysky = AABB puvodnich modelu ve hre (meritka v svet.json zustavaji)
    "smrk": [("Tree_Trunk_01.002+Tree_Branches_01.002", "smrk_0", 0, 0.35, 0.0, {}),
             ("Tree_Trunk_01.001+Tree_Branches_01", "smrk_1", 0, 0.35, 0.0, {}),
             ("Tree_Trunk_01+Tree_Branches_01.001", "smrk_2", 0, 0.35, 0.0, {}),
             ("Tree_Trunk_01.002+Tree_Branches_01.002", "smrk_3", 0, 0.35, 0.0, {"zrcadlo": True}),
             ("Tree_Trunk_01.001+Tree_Branches_01", "smrk_4", 0, 0.35, 0.0, {"zrcadlo": True})],
    "borovice": [("structure.006_11+foliage.002_12", "borovice_0", 0, 0.35, 0.0, {"kura": 0.08, "listi": 0.3})],
    "buk_stredni": [("structure.004_3+foliage.004_4", "buk_stredni_0", 0, 0.35, 0.0, {"kura": 0.17, "listi": 0.6})],
    "lipa_stredni": [("structure.003_1+foliage.003_2", "lipa_stredni_0", 0, 0.35, 0.0, {"kura": 0.2, "listi": 0.85})],
    "lipa_stara": [("structure.003_1+foliage.003_2", "lipa_stara_0", 0, 0.35, 0.0, {"kura": 0.2, "listi": 0.85, "zrcadlo": True})],
    "olse_stredni": [("structure.007_13+foliage.005_14", "olse_stredni_0", 0, 0.35, 0.0, {"kura": 0.3, "listi": 1.0, "barva": (0.45, 0.62, 0.38), "kura_barva": (0.5, 0.48, 0.45)})],
    "olse_mlada": [("structure.007_13+foliage.005_14", "olse_mlada_0", 0, 0.25, 0.0, {"kura": 0.3, "listi": 1.0, "barva": (0.45, 0.62, 0.38), "kura_barva": (0.5, 0.48, 0.45), "zrcadlo": True})],
}
# vysky modelu = puvodni modely ve hre (obrazky/impostory/impostory.json "vyska" pred vymenou); meritka v svet.json zustavaji
VYSKY = {"smrk_0": 16.35, "smrk_1": 18.0, "smrk_2": 13.5, "smrk_3": 15.0, "smrk_4": 17.0, "borovice_0": 5.32,
         "buk_stredni_0": 15.66, "lipa_stredni_0": 14.6, "lipa_stara_0": 22.5, "olse_stredni_0": 15.76, "olse_mlada_0": 7.69}


def _alfa(mat):
    """Material s pruhlednosti (karty listi)?"""
    if mat is None or not mat.use_nodes:
        return False
    b = [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
    return bool(b) and bool(b[0].inputs["Alpha"].links)


def _prebarvi(m, rgb):
    """Vynasobi barvu textur, ktere vedou do Base Color (i pres mezilehle uzly), jednou na obrazek."""
    b = [n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"] if m and m.use_nodes else []
    if not b:
        return
    fronta = [l.from_node for l in b[0].inputs["Base Color"].links]
    while fronta:
        n = fronta.pop()
        if n.type == "TEX_IMAGE" and n.image is not None and not n.image.get("prebarveno"):
            px = list(n.image.pixels)
            for i in range(0, len(px), 4):
                px[i] *= rgb[0]
                px[i + 1] *= rgb[1]
                px[i + 2] *= rgb[2]
            n.image.pixels = px
            n.image["prebarveno"] = 1
            n.image.pack()
        for inp in n.inputs:
            fronta += [l.from_node for l in inp.links]


def _upravy(o, volby):
    """Kura: decimace a bez alfy (jinak by z ni hra udelala listi s vetrem); listi: prorezani karet a zvetseni zbylych."""
    import random
    listi = any(_alfa(m) for m in o.data.materials)
    if not listi:
        for m in o.data.materials:
            b = [n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"] if m and m.use_nodes else []
            if b and b[0].inputs["Alpha"].links:
                m.node_tree.links.remove(b[0].inputs["Alpha"].links[0])
            if m:
                m.blend_method = "OPAQUE"
                if "kura_barva" in volby:
                    _prebarvi(m, volby["kura_barva"])
        if volby.get("kura", 1.0) < 1.0:
            mod = o.modifiers.new("dec", "DECIMATE")
            mod.ratio = volby["kura"]
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier="dec")
        return
    keep = volby.get("listi", 1.0)
    if keep < 1.0:
        import bmesh
        rnd = random.Random(63)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        pryc = [f for f in bm.faces if rnd.random() > keep]
        bmesh.ops.delete(bm, geom=pryc, context="FACES")
        # zbyle karty vetsi (koruna nema byt rideji pokryta), kazda kolem sveho stredu
        k = min(1.0 / keep ** 0.35, 1.4)
        for f in bm.faces:
            c = f.calc_center_median()
            for v in f.verts:
                v.co = c + (v.co - c) * k
        bm.to_mesh(o.data)
        bm.free()
    if "barva" in volby:
        for m in o.data.materials:
            _prebarvi(m, volby["barva"])

druh, SRC, OUT = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
hotove = []
for zaz in DRUHY[druh]:
    koren, jmeno, vyska = zaz[:3]
    vyska = vyska or VYSKY[jmeno]
    zapust = zaz[3] if len(zaz) > 3 else 0.35          # kmen 0,35 m do zeme, ker a kapradi jen trochu
    sirka = zaz[4] if len(zaz) > 4 else 0.0            # kapradi: model je plochy - sirka a vyska zvlast
    volby = zaz[5] if len(zaz) > 5 else {}
    site = []
    for kn in koren.split("+"):
        top = bpy.data.objects[kn]
        site += [o for o in [top] + list(top.children_recursive) if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in site:
        o.select_set(True)
    bpy.context.view_layer.objects.active = site[0]
    bpy.ops.object.duplicate()
    kopie = list(bpy.context.selected_objects)
    for o in kopie:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in kopie:
        o.data = o.data.copy()                         # kopie site: decimace/prorezani nezmeni zdroj pro dalsi variantu
        _upravy(o, volby)
    bpy.ops.object.select_all(action="DESELECT")
    for o in kopie:
        o.select_set(True)
    bpy.context.view_layer.objects.active = kopie[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = jmeno
    ob.data.name = jmeno
    zs = [v.co.z for v in ob.data.vertices]
    zmin, zmax = min(zs), max(zs)
    pata = [v.co for v in ob.data.vertices if v.co.z < zmin + 0.04 * (zmax - zmin)]
    cx = sum(v.x for v in pata) / max(len(pata), 1)
    cy = sum(v.y for v in pata) / max(len(pata), 1)
    k = vyska / (zmax - zmin)
    xs = [v.co.x for v in ob.data.vertices]
    kx = sirka / (max(xs) - min(xs)) if sirka > 0.0 else k
    zx = -1.0 if volby.get("zrcadlo") else 1.0
    for v in ob.data.vertices:
        v.co = mathutils.Vector(((v.co.x - cx) * kx * zx, (v.co.y - cy) * kx, (v.co.z - zmin) * k - zapust))
    if zx < 0.0:
        ob.data.flip_normals()                          # zrcadleni otoci poradi vrcholu
    ob.data.update()
    vs = [v.co for v in ob.data.vertices]
    d = [max(c[i] for c in vs) - min(c[i] for c in vs) for i in range(3)]
    print("STROM", jmeno, "rozmer %.2f x %.2f x %.2f" % tuple(d), "troj", sum(len(p.vertices) - 2 for p in ob.data.polygons), [m.name for m in ob.data.materials])
    hotove.append(ob)
# textury na tablet: nejvys 1024 (zdroje maji 4K - 85 MB glb)
for img in bpy.data.images:
    if img.size[0] > 1024:
        img.scale(1024, int(1024 * img.size[1] / img.size[0]))
bpy.ops.object.select_all(action="DESELECT")
for ob in hotove:
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format="GLB")
