"""Stromy z Misova Disku (slozka Modely) do hry (blok 0.63 LES): z balicku modelu vybrat strom (rodicovsky objekt),
spojit jeho site se zachovanim polohy (listi byva dite vetvi), pata na 0, stred kmene v 0, vyska jako dosavadni
strom ve hre; vystup glb se sitemi pojmenovanymi jako klice v svet.json rostliny (<druh>_<n>).
  /opt/bl/bin/python blender/stromy.py <druh> <zdroj.glb> <vystup.glb>
Druhy a zdroje (licence do titulku - CC-BY 4.0):
  briza    five_birch_trees_pack_lowpoly_lods.glb (LOLIPOP) - LOD2 kazde ze 4 briz
  dub      oak_trees.glb (DJMaesen) - viz blender/duby_nove.py
  ker_husty bushcover (Misuv Disk, CC-BY) - hustý nízký keř do lesa (0.63, Misa: "chybi kere")
  kapradi_les veg.glb (Misuv Disk, CC-BY) - kapradi "paporotnik" 1 a 2 na lesni pudu"""
import sys, bpy, mathutils

DRUHY = {
    # druh: [(objekt rodic ve zdroji, jmeno site ve hre, vyska m)]
    "briza": [("Birch_LOD2", "briza_0", 13.2), ("Birch_2_LOD2", "briza_1", 13.2), ("Birch_3_LOD2", "briza_2", 13.2),
              ("Birch_5_LOD2", "briza_3", 13.2)],
    "ker_husty": [("Bushcover_LOD0_0", "ker_husty_0", 1.7, 0.1)],
    "kapradi_les": [("3", "kapradi_les_0", 0.6, 0.05, 1.3), ("4", "kapradi_les_1", 0.5, 0.05, 1.0)],
}

druh, SRC, OUT = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
hotove = []
for zaz in DRUHY[druh]:
    koren, jmeno, vyska = zaz[:3]
    zapust = zaz[3] if len(zaz) > 3 else 0.35          # kmen 0,35 m do zeme, ker a kapradi jen trochu
    sirka = zaz[4] if len(zaz) > 4 else 0.0            # kapradi: model je plochy - sirka a vyska zvlast
    top = bpy.data.objects[koren]
    site = [o for o in [top] + list(top.children_recursive) if o.type == "MESH"]
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
    for v in ob.data.vertices:
        v.co = mathutils.Vector(((v.co.x - cx) * kx, (v.co.y - cy) * kx, (v.co.z - zmin) * k - zapust))
    d = ob.dimensions
    print("STROM", jmeno, "rozmer %.2f x %.2f x %.2f" % (d.x, d.y, d.z), "troj", sum(len(p.vertices) - 2 for p in ob.data.polygons), [m.name for m in ob.data.materials])
    hotove.append(ob)
# textury na tablet: nejvys 1024 (zdroje maji 4K - 85 MB glb)
for img in bpy.data.images:
    if img.size[0] > 1024:
        img.scale(1024, int(1024 * img.size[1] / img.size[0]))
bpy.ops.object.select_all(action="DESELECT")
for ob in hotove:
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format="GLB")
