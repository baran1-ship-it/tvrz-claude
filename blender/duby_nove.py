"""Nove duby (0.63, Misa: "stromy placacky"; model oak_trees.glb z Misova Disku, DJMaesen, CC-BY 4.0, Sketchfab):
tri stromy ze souboru -> kazdy jedna sit (kura + listi), pata na 0, stred kmene v 0, vyska jako puvodni dub ve hre.
  /opt/bl/bin/python blender/duby_nove.py <oak_trees.glb> <vystupni slozka>
Vystup: dub_stredni.glb (sit dub_stredni_0), dub_stary.glb (dub_stary_0) - jmena jako v svet.json rostliny."""
import sys, bpy, mathutils

SRC, OUT = sys.argv[-2], sys.argv[-1]
CIL = {"Treemedium": ("dub_stredni", 13.9), "treelarge": ("dub_stary", 19.1)}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
for koren, (jmeno, vyska) in CIL.items():
    top = bpy.data.objects[koren]
    site = [o for o in top.children_recursive if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in site:
        o.select_set(True)
    bpy.context.view_layer.objects.active = site[0]
    bpy.ops.object.duplicate()
    kopie = list(bpy.context.selected_objects)
    for o in kopie:
        mw = o.matrix_world.copy()          # listi jsou deti vetvi: bez toho spadne k pate
        o.parent = None
        o.matrix_world = mw
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.objects.active = kopie[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = jmeno + "_0"
    ob.data.name = jmeno + "_0"
    vs = [v.co for v in ob.data.vertices]
    zmin = min(v.z for v in vs)
    zmax = max(v.z for v in vs)
    # stred kmene: vrcholy kury v dolnich 5 % vysky
    kura = [v.co for v in ob.data.vertices if v.co.z < zmin + 0.05 * (zmax - zmin)]
    cx = sum(v.x for v in kura) / max(len(kura), 1)
    cy = sum(v.y for v in kura) / max(len(kura), 1)
    k = vyska / (zmax - zmin)
    for v in ob.data.vertices:
        v.co = mathutils.Vector(((v.co.x - cx) * k, (v.co.y - cy) * k, (v.co.z - zmin) * k))
    tri = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print("DUB", jmeno, "troj", tri, "vyska", vyska, "materialy", [m.name for m in ob.data.materials])
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath="%s/%s.glb" % (OUT, jmeno), use_selection=True, export_format="GLB",
                              export_image_format="JPEG", export_jpeg_quality=88)
    bpy.data.objects.remove(ob)
