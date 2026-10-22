"""Kvetiny z Misova Disku (bush_daisies_sunflower.glb, CC-BY) do louky (0.63, Misa: "to ze obsahuje neco, co nechceme,
neznamena, ze mezi tim neni neco, co vyuzijeme"): jedna sit, slunecnice pryc - z casti site (souvisle kusy) vybrat
shluk kopretin a shluk bilych kvetu podle polohy, kazdy pata 0, vyska ve hre.
  /opt/bl/bin/python blender/kvety.py <zdroj.glb> <vystupni slozka>   -> kopretiny.glb, kvety_bile.glb"""
import sys, bpy, bmesh, mathutils

# jmeno site: (x od, x do, y od, y do) v souradnicich zdroje (Blender, z nahoru), vyska m
SHLUKY = {"kopretiny_0": ((-400.0, -40.0, -120.0, 80.0), 0.42), "kvety_bile_0": ((-160.0, 130.0, 400.0, 545.0), 0.3)}

SRC, OUT = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
zdroj = [o for o in bpy.data.objects if o.type == "MESH"][0]
mw = zdroj.matrix_world.copy()
hotove = []
for jmeno, (r, vyska) in SHLUKY.items():
    bm = bmesh.new()
    bm.from_mesh(zdroj.data)
    bm.transform(mw)
    bm.verts.ensure_lookup_table()
    # souvisle kusy; kus patri do shluku, kdyz jeho stred lezi v obdelniku
    videno = set()
    pryc = []
    for v in bm.verts:
        if v.index in videno:
            continue
        kus = [v]
        zas = [v]
        videno.add(v.index)
        while zas:
            x = zas.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in videno:
                    videno.add(y.index)
                    zas.append(y)
                    kus.append(y)
        s = sum((x.co for x in kus), mathutils.Vector()) / len(kus)
        if not (r[0] < s.x < r[1] and r[2] < s.y < r[3]):
            pryc.extend(kus)
    bmesh.ops.delete(bm, geom=pryc, context="VERTS")
    me = bpy.data.meshes.new(jmeno)
    for m in zdroj.data.materials:
        me.materials.append(m)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(jmeno, me)
    bpy.context.scene.collection.objects.link(ob)
    zs = [v.co.z for v in me.vertices]
    zmin, zmax = min(zs), max(zs)
    cx = sum(v.co.x for v in me.vertices) / len(me.vertices)
    cy = sum(v.co.y for v in me.vertices) / len(me.vertices)
    k = vyska / (zmax - zmin)
    for v in me.vertices:
        v.co = mathutils.Vector(((v.co.x - cx) * k, (v.co.y - cy) * k, (v.co.z - zmin) * k - 0.02))
    print("KVETY", jmeno, "troj", sum(len(p.vertices) - 2 for p in me.polygons), "sirka %.2f" % ((max(v.co.x for v in me.vertices) - min(v.co.x for v in me.vertices))))
    hotove.append(ob)
for img in bpy.data.images:
    if img.size[0] > 1024:
        img.scale(1024, int(1024 * img.size[1] / img.size[0]))
bpy.data.objects.remove(zdroj)
for ob in hotove:
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=OUT + "/" + ob.name[:-2] + ".glb", use_selection=True, export_format="GLB")
