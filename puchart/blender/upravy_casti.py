"""Úpravy částí modelů z Disku (pravidla/svet/mista.json upravy_modelu): posun části modelu (přístřešek kovárny)
a smazání části (předměty před hájovnou). Model je sešitý z ploch s rozpojenými vrcholy – části se poznají podle souvislých
kusů po sloučení vrcholů (jen pro rozbor), kus patří k části, když jeho obal splní meze (x_min, y_max, oblast).
Souřadnice Godot (x, y nahoru, z) ↔ Blender (x, −z, y). Z originálu build/zdroj_celky/<soubor> do hra/modely/stavby_h/<soubor>
(opakované spuštění nic nezdvojí).  /opt/bl/bin/python blender/upravy_casti.py <K>"""
import sys, os, json
import bpy, bmesh
from mathutils import Vector

K = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else sys.argv[-1]
UP = json.load(open(os.path.join(K, "pravidla/svet/mista.json")))["upravy_modelu"]


def kusy(o):
    """[(množina indexů ploch, obal (x0, x1, y0, y1, z0, z1) v Godot souřadnicích světa)]"""
    bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    pos = [mw @ v.co for v in bm.verts]
    klic = {}; rodic = list(range(len(bm.verts)))
    def najdi(i):
        while rodic[i] != i: rodic[i] = rodic[rodic[i]]; i = rodic[i]
        return i
    for v in bm.verts:   # sloučení stejných poloh (2 mm)
        k = tuple(round(c / 0.002) for c in pos[v.index])
        if k in klic: rodic[najdi(v.index)] = najdi(klic[k])
        else: klic[k] = v.index
    for f in bm.faces:
        vs = [v.index for v in f.verts]
        for a in vs[1:]: rodic[najdi(a)] = najdi(vs[0])
    skup = {}
    for f in bm.faces: skup.setdefault(najdi(f.verts[0].index), []).append(f.index)
    out = []
    for fs in skup.values():
        ps = [pos[v.index] for fi in fs for v in bm.faces[fi].verts]
        out.append((set(fs), (min(p.x for p in ps), max(p.x for p in ps), min(p.z for p in ps), max(p.z for p in ps), -max(p.y for p in ps), -min(p.y for p in ps))))
    bm.free()
    return out


def splnuje(ob, u):
    x0, x1, y0, y1, z0, z1 = ob
    if "x_min" in u and x0 < u["x_min"]: return False
    if "y_max" in u and y1 > u["y_max"]: return False
    if "y_min" in u and y0 < u["y_min"]: return False
    if "oblast" in u:
        a = u["oblast"]
        if not (a[0] <= x0 and x1 <= a[1] and a[2] <= z0 and z1 <= a[3]): return False
    return True


for soubor, U in UP.items():
    if soubor in ("popis", "zdroj") or not isinstance(U, dict): continue
    src = os.path.join(K, "build/zdroj_celky", U.get("zdroj", soubor))
    if not os.path.exists(src): print("UPRAVA_CHYBI", src); continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    for u in U.get("casti", []):
        d = Vector(u.get("posun", [0, 0, 0])); d = Vector((d.x, -d.z, d.y))   # Godot → Blender
        n_ = 0
        for jm in u["uzly"]:
            o = bpy.data.objects.get(jm)
            if o is None or o.type != "MESH": continue
            vyb = set()
            for fs, ob in kusy(o):
                if splnuje(ob, u): vyb |= fs
            bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
            fs_ = [bm.faces[i] for i in vyb]
            if u.get("smazat"):
                bmesh.ops.delete(bm, geom=fs_, context="FACES")
            else:
                mwi = o.matrix_world.inverted(); mw = o.matrix_world
                for v in {v for f in fs_ for v in f.verts}: v.co = mwi @ (mw @ v.co + d)
            bm.to_mesh(o.data); bm.free(); n_ += len(fs_)
        for jm in u.get("kolize", []):
            o = bpy.data.objects.get(jm + "-convcolonly") or bpy.data.objects.get(jm)
            if o is None: print("UPRAVA_KOLIZE_CHYBI", jm); continue
            if u.get("smazat"): bpy.data.objects.remove(o, do_unlink=True)
            else: o.matrix_world.translation += d
        for q in u.get("pridat", []):   # nové trámky (zábradlí): kvádr [střed], [rozměr] v souřadnicích modelu Godot, materiál z uzlu
            if "od" in q:   # kvádr podél osy od → do (šikmý díl, např. dymník), průřez [šířka v x, hloubka] kolmo k ose
                a_ = Vector((q["od"][0], -q["od"][2], q["od"][1])); b_ = Vector((q["do"][0], -q["do"][2], q["do"][1]))
                c = [(q["od"][i] + q["do"][i]) / 2 for i in range(3)]; r = [q["prurez"][0], (b_ - a_).length, q["prurez"][1]]
            else:
                c = q["stred"]; r = q["rozmer"]
            me = bpy.data.meshes.new("pridano"); ob = bpy.data.objects.new(q.get("jmeno", "Pridano"), me); bpy.context.scene.collection.objects.link(ob)
            bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=Vector((r[0], r[2], r[1])), verts=bm.verts); bm.to_mesh(me); bm.free()
            ob.location = Vector((c[0], -c[2], c[1]))
            if "od" in q: ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference((b_ - a_).normalized())
            src_ = bpy.data.objects.get(q["material_z"]) if "material_z" in q else None
            if "material" in q and bpy.data.materials.get(q["material"]): me.materials.append(bpy.data.materials[q["material"]])
            elif src_ and src_.data.materials: me.materials.append(src_.data.materials[0])
            for uv_ in [me.uv_layers.new()]:   # UV podél nejdelší strany (textura dřeva)
                for li, lo in enumerate(me.loops): uv_.data[li].uv = (me.vertices[lo.vertex_index].co.x * r[0] + me.vertices[lo.vertex_index].co.y * r[2] + me.vertices[lo.vertex_index].co.z * r[1], 0.5 + me.vertices[lo.vertex_index].co.z * 0.1)
            if q.get("kolize"):
                kc = ob.copy(); kc.data = me.copy(); kc.name = q.get("jmeno", "Pridano") + "_Kol-convcolonly"; bpy.context.scene.collection.objects.link(kc)
            if q.get("jen_kolize"): bpy.data.objects.remove(ob, do_unlink=True)   # jen kolize (okraj schodů), bez viditelného dílu
            n_ += 1
        print("UPRAVA", soubor, u.get("popis", ""), "ploch", n_)
    bpy.ops.export_scene.gltf(filepath=os.path.join(K, "hra/modely/stavby_h", soubor), export_format="GLB", export_extras=True, export_yup=True)
