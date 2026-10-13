"""Predmety pro inventar a staveni: modely Poly Haven (CC0) ve 2k, kazdy jako samostatny GLB s texturami,
k nemu ikona (render 3/4 pohled) a zapis v katalogu modely/predmety.json.
  /opt/bl/bin/python predmety.py fetch     -> stahne modely do tex_cache/models/<id>
  /opt/bl/bin/python predmety.py build     -> modely/predmety/<id>.glb, modely/predmety/<id>.png, modely/predmety.json
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "tex_cache", "models")
OUT = os.path.join(HERE, "..", "modely", "predmety")

# id: (poly haven id, nazev, kategorie brasny nebo None, podzalozka staveni nebo None, vaha kg, cena gr, vlastnosti)
# vlastnosti: kont=N (uloziste s N mista), sed (da se sednout), lehat
KATALOG = {
    "sud": ("wine_barrel_01", "Sud", "nadoby", "uvnitr", 25.0, 30, {"kont": 80}),
    "truhla": ("treasure_chest", "Okovaná truhla", None, "uvnitr", 30.0, 120, {"kont": 120}),
    "bedna": ("wooden_crate_01", "Bedna", None, "venku", 12.0, 15, {"kont": 60}),
    "bedna_znak": ("wooden_crate_02", "Bedna se značkou", None, "venku", 12.0, 18, {"kont": 60}),
    "vedro": ("wooden_bucket_01", "Vědro", "nadoby", "venku", 2.0, 4, {}),
    "kad": ("wooden_bucket_02", "Káď", "nadoby", "remeslo", 14.0, 12, {"meritko": 1.55, "kont": 60}),
    "kosik": ("wicker_basket_01", "Košík", "nadoby", "uvnitr", 0.5, 4, {"kont": 10}),
    "kos_viko": ("wicker_basket_02", "Koš s víkem", "nadoby", "uvnitr", 3.0, 10, {"meritko": 2.3, "kont": 40}),
    "postel": ("GothicBed_01", "Gotická postel", None, "uvnitr", 60.0, 400, {"lehat": True}),
    "skrin": ("GothicCabinet_01", "Gotická skříň", None, "uvnitr", 70.0, 450, {"kont": 150}),
    "lavice_nizka": ("WoodenTable_01", "Nízká lavice", None, "uvnitr", 15.0, 20, {"sed": True}),
    "stolicka": ("wooden_stool_01", "Stolička", None, "uvnitr", 3.0, 6, {"sed": True}),
    "spalek": ("wooden_stool_02", "Špalková stolička", None, "venku", 4.0, 4, {"sed": True}),
    "stolicka_skladaci": ("folding_wooden_stool", "Skládací stolička", None, "venku", 2.5, 8, {"sed": True}),
    "lavice": ("painted_wooden_bench", "Lavice s opěradlem", None, "uvnitr", 25.0, 60, {"sed": True}),
    "kolovrat": ("spinning_wheel_01", "Kolovrat", None, "remeslo", 12.0, 90, {}),
    "sekera": ("wooden_axe", "Sekera", "naradi", "zbrojnice", 2.2, 90, {"zed": True}),
    "sekera_tesarska": ("wooden_axe_02", "Tesařská sekera", "naradi", "zbrojnice", 2.4, 110, {"zed": True}),
    "sekera_valecna": ("wooden_axe_03", "Válečná sekera", "zbrane", "zbrojnice", 2.6, 310, {"zed": True}),
    "stit": ("kite_shield", "Štít", "zbroj", "zbrojnice", 4.5, 260, {"zed": True}),
    "kladivo_valecne": ("ornate_war_hammer", "Válečné kladivo", "zbrane", "zbrojnice", 3.0, 420, {"zed": True}),
    "lucerna": ("wooden_lantern_01", "Lucerna", "ostatni", "dekorace", 1.2, 25, {}),
    "svicen": ("wooden_candlestick", "Svícen", "ostatni", "dekorace", 0.6, 12, {}),
    "miska": ("wooden_bowl_01", "Miska", "nadoby", "dekorace", 0.3, 2, {}),
    "lzice": ("wooden_spoon", "Lžíce", "ostatni", "dekorace", 0.1, 1, {}),
    "talir": ("carved_wooden_plate", "Talíř", "nadoby", "dekorace", 0.4, 3, {}),
    "prkenko": ("wooden_cutting_board", "Prkénko", "ostatni", "dekorace", 0.8, 3, {}),
    # druha varka: stoly, zidle, kresla, nadobi
    "stul_prkenny": ("wooden_table_02", "Prkenný stůl", None, "uvnitr", 25.0, 40, {}),
    "stolek": ("small_wooden_table_01", "Stolek", None, "uvnitr", 12.0, 18, {}),
    "stul_malovany": ("painted_wooden_table", "Malovaný stůl na kozách", None, "uvnitr", 30.0, 60, {}),
    "stul_ubrus": ("dining_table", "Stůl s ubrusem", None, "uvnitr", 35.0, 80, {}),
    "stolek_goticky": ("gothic_coffee_table", "Gotický stolek", None, "uvnitr", 18.0, 120, {}),
    "truhla_vyrezavana": ("gallinera_table", "Vyřezávaná truhla", None, "uvnitr", 40.0, 160, {"kont": 120}),
    "zidle_goticka": ("WoodenChair_01", "Gotická židle", None, "uvnitr", 8.0, 90, {"sed": True}),
    "zidle_selska": ("painted_wooden_chair_02", "Selská židle", None, "uvnitr", 5.0, 15, {"sed": True}),
    "kreslo": ("gallinera_chair", "Vyřezávané křeslo", None, "uvnitr", 18.0, 140, {"sed": True}),
    "stolicka_vysoka": ("painted_wooden_stool", "Vysoká stolička", None, "remeslo", 4.0, 8, {"sed": True}),
    "hrnec": ("ceramic_pot", "Hliněný hrnec", "nadoby", "dekorace", 2.0, 5, {}),
    "kotlik": ("brass_pot_01", "Měděný kotlík", "nadoby", "remeslo", 4.0, 45, {}),
    "panev": ("brass_pot_02", "Měděná pánev", "nadoby", "dekorace", 2.5, 30, {}),
    "svicny": ("brass_candleholders", "Mosazné svícny", "ostatni", "dekorace", 2.0, 60, {}),
    # vlastni modely (vlastni.py)
    "kozesina": ("@", "Medvědí kožešina", "ostatni", "dekorace", 8.0, 150, {}),
    "ovci_kuze": ("@", "Ovčí kůže", "ostatni", "dekorace", 2.0, 25, {}),
    "koberec": ("@", "Koberec", None, "dekorace", 12.0, 200, {}),
    "koberec_modry": ("@", "Modrý koberec", None, "dekorace", 7.0, 140, {}),
    "polstar": ("@", "Polštář", "ostatni", "dekorace", 0.6, 12, {}),
    "polstar_zeleny": ("@", "Zelený polštář", "ostatni", "dekorace", 0.6, 10, {}),
    "stul_hodovni": ("@", "Hodovní stůl", None, "uvnitr", 90.0, 300, {}),
    "lavice_hodovni": ("@", "Hodovní lavice", None, "uvnitr", 30.0, 60, {"sed": True}),
    "stul_pansky": ("@", "Panský hodovní stůl", None, "uvnitr", 160.0, 900, {}),
    "kreslo_panske": ("@", "Panské křeslo", None, "uvnitr", 22.0, 260, {"sed": True}),
    "drzak_louce": ("@", "Držák s loučí", None, "dekorace", 2.0, 30, {"zed": True, "louc": True}),
    "louc": ("@", "Louč", "ostatni", "dekorace", 0.6, 2, {}),
}


def fetch(res="2k"):
    import urllib.request
    UA = {"User-Agent": "tvrz-blender/1.0"}

    def get_json(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            return json.load(r)

    def download(url, path):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(path, "wb") as f:
            f.write(r.read())
    for key, (pid, *_rest) in KATALOG.items():
        if pid == "@":
            continue
        d = os.path.join(ROOT, pid + "_" + res)
        main = os.path.join(d, pid + ".gltf")
        if os.path.exists(main):
            continue
        files = get_json("https://api.polyhaven.com/files/" + pid)
        g = files["gltf"][res]["gltf"]
        os.makedirs(d, exist_ok=True)
        download(g["url"], main)
        for rel, inc in g.get("include", {}).items():
            path = os.path.join(d, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            download(inc["url"], path)
        print("stazeno", key, pid)


if __name__ == "__main__":
    if sys.argv[-1] == "fetch":
        fetch()


def build():
    import bpy  # noqa: E402
    from mathutils import Vector
    os.makedirs(OUT, exist_ok=True)
    hdr = os.path.join(HERE, "tex_cache", "studio_small_09_1k.hdr")
    cat = {}
    only = [a for a in sys.argv[sys.argv.index("build") + 1:]] if "build" in sys.argv else []
    for key, (pid, name, kat, stav, wt, price, props) in KATALOG.items():
        if only and key not in only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if pid == "@":
            import vlastni
            vlastni.BUILD[key]()
        else:
            bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, pid + "_2k", pid + ".gltf"))
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes:
            o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        if len(meshes) > 1:
            bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
        ob.parent = None
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        for o in list(bpy.context.scene.objects):
            if o is not ob:
                bpy.data.objects.remove(o)
        vs = [v.co for v in ob.data.vertices]
        mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        c = (mn + mx) / 2
        ob.data.transform(__import__("mathutils").Matrix.Translation(Vector((-c.x, -c.y, -mn.z))))
        k = float(props.get("meritko", 1.0))
        if k != 1.0:
            ob.data.transform(__import__("mathutils").Matrix.Scale(k, 4))
            mn, mx = mn * k, mx * k
        ob.name = key
        ob.data.name = key
        size = mx - mn
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        if tris > 40000:
            # tablet: nejvys ~40k trojuhelniku na predmet (sken svicnu ma 200k)
            dm = ob.modifiers.new("dec", "DECIMATE")
            dm.ratio = 40000 / tris
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.modifier_apply(modifier="dec")
            tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, key + ".glb"), export_format="GLB", use_selection=False,
                                  export_apply=True, export_yup=True, export_image_format="AUTO")
        # ikona: 3/4 pohled shora, studiove svetlo, pruhledne pozadi
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 48
        sc.render.resolution_x = sc.render.resolution_y = 384
        sc.render.film_transparent = True
        sc.view_settings.view_transform = "AgX"
        w = bpy.data.worlds.new("W")
        w.use_nodes = True
        env = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(hdr)
        w.node_tree.links.new(env.outputs["Color"], w.node_tree.nodes["Background"].inputs[0])
        w.node_tree.nodes["Background"].inputs[1].default_value = 1.1
        sc.world = w
        cam = bpy.data.cameras.new("K")
        cam.type = "ORTHO"
        co = bpy.data.objects.new("K", cam)
        sc.collection.objects.link(co)
        sc.camera = co
        tgt = Vector((0, 0, size.z / 2))
        d = Vector((math.cos(math.radians(-50)), math.sin(math.radians(-50)), 0.65)).normalized()
        co.location = tgt + d * (size.length * 3 + 2)
        co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
        # ortho meritko podle promitnuteho obrysu
        bpy.context.view_layer.update()
        inv = co.matrix_world.inverted()
        corners = [Vector((x, y, z)) for x in (-size.x / 2, size.x / 2) for y in (-size.y / 2, size.y / 2) for z in (0, size.z)]
        pc = [inv @ p for p in corners]
        cam.ortho_scale = max(max(p.x for p in pc) - min(p.x for p in pc), max(p.y for p in pc) - min(p.y for p in pc)) * 1.12
        sc.render.filepath = os.path.join(OUT, key + ".png")
        bpy.ops.render.render(write_still=True)
        cat[key] = {"nazev": name, "kat": kat, "stav": stav, "vaha": wt, "cena": price,
                    "rozmer": [round(size.x, 3), round(size.z, 3), round(size.y, 3)],
                    **{a: b for a, b in props.items() if a != "meritko"}}
        print("predmet", key, "%d troj." % tris, [round(v, 2) for v in size])
    p = os.path.join(OUT, "..", "predmety.json")
    old = json.load(open(p)) if os.path.exists(p) and only else {}
    old.update(cat)
    json.dump(old, open(p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__" and "build" in sys.argv:
    build()
