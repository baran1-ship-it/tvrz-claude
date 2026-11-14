"""Úpravy celých staveb z Disku Míši před vložením do hry (pravidla/svet/mista.json modely.celky.<model>.uprava).
Míša 14. 11.: „chci ji [krčmu] na tom místě“, „můžeme nějak dát vedle sebe hospodu a stáje?“, „modely si uprav podle
potřeby“ – krčma do L se na skutečné místo U Tlustého Jana (úzký pruh mezi silnicí a Veličkou) nevejde: křídlo se stájí
a pokojíky se otočí o 90° a postaví vedle hospody v řadě podél cesty (vrata do dvora mezi nimi), zadní dvůr s ohradou a
kůlnou se vypustí. Data: uprava = {kridlo: [jména uzlů], kridlo_od_x: x (uzly s obalem od x jsou křídlo), otoceni_deg,
posun: [x, z] (Godot), smazat: [jména uzlů], dvur_uzel, dvur_ponechat: [x0, x1, z0, z1] (Godot – část sítě dvora, která
zůstane: sloupy a stříška vrat)}. Souřadnice Godot (x, z) ↔ Blender (x, −y).
  /opt/bl/bin/python blender/celky_upravy.py <K> <model> <vstup.glb> <vystup.glb> [<vstup_lod1.glb> <vystup_lod1.glb>]"""
import sys, os, json, math
import bpy, bmesh
from mathutils import Matrix, Vector

K, MODEL = sys.argv[1], sys.argv[2]
U = json.load(open(os.path.join(K, "pravidla/svet/mista.json")))["modely"]["celky"][MODEL]["uprava"]


def nacti(cesta):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=cesta)
    return list(bpy.context.scene.objects)


def obal_x(o):
    """nejmenší x (Godot = Blender x) obalu objektu ve světě"""
    if o.type != "MESH" or not o.data.vertices: return None
    return min((o.matrix_world @ v.co).x for v in o.data.vertices)


def uprav(vstup, vystup, lod=False):
    objs = nacti(vstup)
    th = math.radians(U["otoceni_deg"]); tx, tz = U["posun"]
    # Godot: x' = x cos + z sin, z' = −x sin + z cos (Basis(UP, θ)) + posun; Blender (x, y = −z): rotace kolem Z o θ
    M = Matrix.Translation(Vector((tx, -tz, 0.0))) @ Matrix.Rotation(th, 4, "Z")
    kridlo = set(U["kridlo"]); smazat = set(U["smazat"])
    for o in objs:
        if o.name in smazat:
            bpy.data.objects.remove(o, do_unlink=True); continue
    objs = list(bpy.context.scene.objects)
    for o in objs:
        if o.parent is not None and o.parent.name in kridlo: continue   # děti otočí rodič
        je_kridlo = o.name in kridlo or (o.type == "MESH" and o.name.endswith("-convcolonly") and (obal_x(o) or -1e9) >= U["kridlo_od_x"]
                                        and not any(o.name.startswith(p) for p in U.get("ne_kridlo", [])))
        if lod and o.type == "MESH":   # LOD1 je jedna síť: plochy křídla (střed x ≥ kridlo_od_x) se otočí, dvůr se ořízne
            bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world; mwi = mw.inverted()
            x0, x1, z0, z1 = U["dvur_ponechat"]
            pryc = []
            for f in bm.faces:
                c = mw @ f.calc_center_median()
                if c.x >= U["kridlo_od_x"]: continue
                if c.y > U["dvur_za_domem_z"] and not (x0 <= c.x <= x1 and z0 <= -c.y <= z1): pryc.append(f)   # plot a kůlna za domem (Godot z < −dvur_za_domem_z)
            bmesh.ops.delete(bm, geom=pryc, context="FACES")
            kv = {v for f in bm.faces if (mw @ f.calc_center_median()).x >= U["kridlo_od_x"] for v in f.verts}
            for v in kv: v.co = mwi @ (M @ (mw @ v.co))
            bm.to_mesh(o.data); bm.free(); continue
        if je_kridlo:
            o.matrix_world = M @ o.matrix_world
        elif o.name == U.get("dvur_uzel") and o.type == "MESH":
            bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world; x0, x1, z0, z1 = U["dvur_ponechat"]
            pryc = [f for f in bm.faces if not (x0 <= (mw @ f.calc_center_median()).x <= x1 and z0 <= -(mw @ f.calc_center_median()).y <= z1)]
            bmesh.ops.delete(bm, geom=pryc, context="FACES"); bm.to_mesh(o.data); bm.free()
    bpy.ops.export_scene.gltf(filepath=vystup, export_format="GLB", export_extras=True, export_yup=True)
    print("CELEK_UPRAVA", MODEL, vystup)


uprav(sys.argv[3], sys.argv[4])
if len(sys.argv) > 6: uprav(sys.argv[5], sys.argv[6], lod=True)
