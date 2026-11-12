"""Kameny do koryt (Míša 10. 11.: „kamenný potok“, „podívej se na reálné fotky – to snad ne“ na krabicové kameny): 6 skutečných
naskenovaných kamenů Poly Haven rock_moss_set_01 (CC0, blender/skaly_scan, nastroje/stahni_skaly_scan.sh), zjednodušené na
~450 troj., velikost 1 m (nejdelší vodorovný rozměr), pata v počátku. Textura přebarvená na drobu (*_diff_droba.jpg).
Ve hře instance podle hra/data/koryto_kameny.bin (nastroje/koryto_kameny.py).
  /opt/bl/bin/python blender/kameny_koryta.py <koren_puchartu>
"""
import sys, os, bpy
K = os.path.abspath(sys.argv[-1]); T = os.path.join(K, "blender/skaly_scan/rock_moss_set_01")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(T, "rock_moss_set_01_1k.gltf"))
obs = sorted([o for o in bpy.context.scene.objects if o.type == "MESH"], key=lambda o: o.name)
dr = os.path.join(T, "textures/rock_moss_set_01_diff_droba.jpg")
for m in bpy.data.materials:
    if m.use_nodes and os.path.exists(dr):
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and "diff" in n.image.filepath: n.image = bpy.data.images.load(dr, check_existing=True)
for i, o in enumerate(obs):
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    o.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = o.data; n0 = len(me.polygons)
    d = o.modifiers.new("dec", "DECIMATE"); d.ratio = min(1.0, 200.0 / max(n0, 1))
    bpy.ops.object.modifier_apply(modifier="dec")
    import mathutils
    xs = [v.co for v in me.vertices]
    mn = mathutils.Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs)))
    mx = mathutils.Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
    c = (mn + mx) / 2; s = 1.0 / max(mx.x - mn.x, mx.y - mn.y)   # Blender Z nahoru
    for v in me.vertices: v.co = mathutils.Vector(((v.co.x - c.x) * s, (v.co.y - c.y) * s, (v.co.z - mn.z) * s))
    o.name = "valoun_%d" % i; o.location = (i * 2.0, 0, 0)
    for p in me.polygons: p.use_smooth = True
    print("valoun", i, n0, "->", len(me.polygons))
bpy.ops.export_scene.gltf(filepath=os.path.join(K, "hra/modely/hrady/kameny_koryta.glb"), export_format="GLB", export_yup=True)
print("ULOZENO kameny_koryta")

# Blender (bpy) občas spadne při úklidu po uložení – návratový kód přerušil řetězec postav_vse.sh (12. 11.); vše je uložené
import os as _os, sys as _sys; _sys.stdout.flush(); _os._exit(0)
