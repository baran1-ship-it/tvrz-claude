"""Střední stupeň detailu staveb (Míša 15. 11.: „dodělej ty střední zobrazení domů“): z podrobného modelu vnějšek (sítě
podle vzoru, bez vnitřku, kolizí a drobností) sloučený do jedné sítě, sloučené vrcholy, zjednodušený (Decimate collapse) na
cílový počet trojúhelníků – materiály a UV zůstanou (stejné textury jako podrobný model, hra je přiřadí podle jména
materiálu). Dřívější domy_stredni.glb měl stejně trojúhelníků jako podrobný (53 tis.) a jen barvu vrcholů → černý.
Data pravidla/svet/mista.json lod_stredni: [{vstup, vystup, modely: {koren: cil_troj}, vynechat: [podřetězce jmen]}].
  /opt/bl/bin/python blender/stredni_lod.py -- <K>"""
import sys, os, json
import bpy, bmesh

K = sys.argv[sys.argv.index("--") + 1]
CFG = json.load(open(os.path.join(K, "pravidla/svet/mista.json")))["lod_stredni"]


def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


for z in CFG["soubory"]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(K, z["vstup"]))
    vyst = []
    for koren, cil in z["modely"].items():
        r = bpy.data.objects.get(koren)
        kandidati = [o for o in bpy.data.objects if o.type == "MESH" and (o == r or (r and o in r.children_recursive) or (not r and o.name.startswith(koren)))]
        sit = [o for o in kandidati if not any(v in o.name for v in z["vynechat"])]
        if not sit: print("STREDNI_CHYBI", koren); continue
        kopie = []
        for o in sit:
            c = o.copy(); c.data = o.data.copy(); c.parent = None; c.matrix_world = o.matrix_world.copy()
            bpy.context.scene.collection.objects.link(c); kopie.append(c)
            # jedna UV vrstva stejného jména u všech kusů – join jinak nechá více vrstev a glTF vyveze jen aktivní (stěny bez UV = šedé)
            if c.data.uv_layers:
                act = c.data.uv_layers.active or c.data.uv_layers[0]
                for u in [u for u in c.data.uv_layers if u != act]: c.data.uv_layers.remove(u)
                c.data.uv_layers[0].name = "UVMap"
        bpy.ops.object.select_all(action="DESELECT")
        for c in kopie: c.select_set(True)
        bpy.context.view_layer.objects.active = kopie[0]
        bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active
        # zpět do souřadnic kořene (hra vkládá síť jako dítě instance domu)
        if r is not None:
            inv = r.matrix_world.inverted(); j.data.transform(inv @ j.matrix_world); j.matrix_world = r.matrix_world.copy()
        vm = z.get("vynechat_materialy", [])
        if vm:   # střecha z jednotlivých šindelů/došků a vnitřní líce stěn pryč (60 % troj.; zjednodušení je rozmazalo – 15. 11.)
            bm = bmesh.new(); bm.from_mesh(j.data)
            pryc = [f for f in bm.faces if f.material_index < len(j.data.materials) and j.data.materials[f.material_index] and any(v in j.data.materials[f.material_index].name for v in vm)]
            bmesh.ops.delete(bm, geom=pryc, context="FACES"); bm.to_mesh(j.data); bm.free()
        sz = z.get("strecha_z")
        if sz:   # hladká střecha z hrubého obalu (<koren>_Daleko, plocha *_Sindel) – hra jí dá texturu jako obalu (daleko_textury)
            d_ = bpy.data.objects.get(koren + sz)
            if d_ is not None:
                c = d_.copy(); c.data = d_.data.copy(); c.parent = None; c.matrix_world = d_.matrix_world.copy(); bpy.context.scene.collection.objects.link(c)
                if not c.data.uv_layers: c.data.uv_layers.new(name="UVMap")   # obal nemá UV (hra mu dá trojrozměrné promítání)
                bm = bmesh.new(); bm.from_mesh(c.data)
                bmesh.ops.delete(bm, geom=[f for f in bm.faces if not (c.data.materials[f.material_index] and c.data.materials[f.material_index].name.endswith("_Sindel"))], context="FACES")
                bm.to_mesh(c.data); bm.free()
                if r is not None: c.data.transform(r.matrix_world.inverted() @ c.matrix_world); c.matrix_world = r.matrix_world.copy()
                bpy.ops.object.select_all(action="DESELECT"); j.select_set(True); c.select_set(True); bpy.context.view_layer.objects.active = j
                bpy.ops.object.join()
        bm = bmesh.new(); bm.from_mesh(j.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004); bm.to_mesh(j.data); bm.free()
        t0 = tri_count(j)
        if cil and t0 > cil:
            md = j.modifiers.new("dec", "DECIMATE"); md.decimate_type = "COLLAPSE"; md.ratio = cil / t0; md.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=md.name)
        j.name = koren + "_Stredni"; j.data.name = koren + "_Stredni"
        print("STREDNI", koren, t0, "->", tri_count(j), "materialu", len(j.data.materials))
        vyst.append(j)
    bpy.ops.object.select_all(action="DESELECT")
    for o in vyst: o.select_set(True); o.parent = None
    bpy.ops.export_scene.gltf(filepath=os.path.join(K, z["vystup"]), export_format="GLB", use_selection=True, export_yup=True,
                              export_image_format="NONE", export_materials="EXPORT")
