"""Modely z druheho chatu (vetev main, modely/nove): balvany, kameny, kaminky, vozy.

Ve hre se instancuji jako rostliny (veg.LIB -> modely/rostliny/<model>.glb + rozmisteni ve svet.json),
kolize maji kvadrem (pridavaji se do Part.cols tam, kde se misto vybira). Soubory se vytahnou z gitu
(origin/main) do tex_cache/nove, pokud tam jeste nejsou."""
import math
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "tex_cache", "nove")
GIT_REF = os.environ.get("TVRZ_NOVE_REF", "origin/main")

# rozmer modelu (sirka x, vyska y, hloubka z v m) podle modely/nove/seznam.txt
DIM = {
    "balvan_piskovec_1": (2.58, 1.49, 1.78), "balvan_piskovec_2": (2.20, 1.11, 1.46), "balvan_piskovec_3": (3.12, 2.23, 2.14),
    "balvan_droba_1": (2.59, 1.50, 1.79), "balvan_zula_1": (2.46, 1.53, 2.01),
    "kamen_zula_1": (1.36, 0.76, 0.94), "kamen_zula_2": (0.63, 0.39, 0.41), "kamen_piskovec_1": (1.08, 0.61, 0.81),
    "kamen_piskovec_2": (1.31, 0.62, 0.91), "kamen_droba_1": (0.83, 0.50, 0.71),
    "kamen_maly_1": (0.29, 0.19, 0.18), "kamen_maly_2": (0.25, 0.13, 0.16), "kamen_maly_3": (0.34, 0.16, 0.21),
    "kamen_maly_4": (0.14, 0.10, 0.11), "kamen_maly_5": (0.27, 0.17, 0.22),
    "zebrinak_1": (1.73, 1.76, 6.26), "zebrinak_plachta_1": (1.73, 2.43, 6.26),
    "bez_cerny_1": (3.88, 3.89, 4.23), "bez_cerny_2": (2.89, 3.10, 3.90), "bez_cerny_3": (5.28, 3.91, 4.34),
}
# stromy v2 (jen solitery, cesty, voda, ruiny - les zustava z lehkych stromu): (sirka, vyska, hloubka) podle seznam.txt
STROMY = {
    "dub_stary": (22.08, 19.12, 23.47), "dub_stredni": (13.04, 13.89, 16.05), "lipa_stara": (16.78, 22.52, 16.97),
    "lipa_stredni": (10.56, 14.60, 9.88), "buk_stredni": (9.77, 15.66, 10.60), "olse_stredni": (7.24, 15.76, 7.06),
    "olse_mlada": (4.19, 7.69, 4.15), "vrba_hlavata_1": (6.05, 6.60, 6.40), "vrba_hlavata_2": (9.21, 7.65, 9.43),
}
DIM.update(STROMY)
LOD = set(STROMY)            # ke kazdemu stromu vzdalena verze <model>_daleko (zblizka plny strom, dal nez ~60 m karta)
PODROST = {"kapradi_1": (1.45, 0.63, 1.52), "kapradi_2": (1.92, 0.68, 1.67), "kapradi_3": (1.42, 0.48, 1.43),
           "orobinec_1": (1.74, 1.98, 1.57), "orobinec_2": (1.25, 1.95, 1.55), "rakos_1": (2.01, 2.77, 2.00),
           "rakos_2": (2.82, 2.82, 2.30), "mech_1": (0.35, 0.03, 0.35), "mech_2": (0.70, 0.05, 0.70), "mech_3": (0.45, 0.10, 0.45),
           "borovice": (2.18, 5.32, 2.17),         # borovice na piskovcovych skalach (pine_tree.glb z disku hrace)
           # psenice na lanech (Misa 28. 10., Sketchfab „Wheat“ ljungman CC-BY 4.0; tex_cache/nove/psenice.glb), dve
           # zkrizene karty; zelena varianta = tataz sit s prebarvenou texturou (add_to_library)
           "psenice": (1.77, 2.0, 1.77), "psenice_2": (1.77, 2.0, 1.77)}
DIM.update(PODROST)
# skalni veze pro skalni mesto (chat s modely): (sirka, vyska vcetne 1 m pod zemi, hloubka); mech a lisejnik na +Z modelu
SKALY = {"skala_jehla": (4.2, 28.3, 3.9), "skala_vez": (6.9, 22.5, 5.1), "skala_hlava": (6.0, 20.6, 5.3),
         "skala_naklonena": (7.6, 18.8, 4.6), "skala_masiv_2veze": (10.6, 31.8, 6.4), "skala_masiv_3veze": (12.4, 31.3, 7.3)}
SKALY_POD = 1.03          # kolik metru modelu je pod terenem
# nejvyssi bod kamene (bez puvodni borovice, ta byla v DIM): (vyska od paty modelu, x, y v Blenderu od stredu modelu)
SKALY_VRCHOL = {"skala_hlava": (17.02, -0.16, 0.39), "skala_jehla": (25.26, 0.07, -0.15),
                "skala_masiv_2veze": (28.99, -1.66, 0.02), "skala_masiv_3veze": (28.38, 0.62, 1.12),
                "skala_naklonena": (18.47, 2.00, -0.13), "skala_vez": (18.94, -1.09, -0.62)}
DIM.update(SKALY)
LOD |= set(SKALY)         # vzdalena verze se vyrobi decimaci (bez borovic a travy), viz add_to_library

# horniny: piskovec na hrebeni a ve skalnim meste, jinde polni kameny ze zuly a droby (z ledovcu a potoku)
BALVANY_PISKOVEC = ["balvan_piskovec_1", "balvan_piskovec_2", "balvan_piskovec_3"]
BALVANY_POLE = ["balvan_zula_1", "balvan_droba_1", "balvan_piskovec_2"]
KAMENY_PISKOVEC = ["kamen_piskovec_1", "kamen_piskovec_2"]
KAMENY_POLE = ["kamen_zula_1", "kamen_zula_2", "kamen_droba_1", "kamen_piskovec_1"]
KAMINKY = ["kamen_maly_%d" % i for i in range(1, 6)]

MISTA = []      # (model, x, y, z, meritko, yaw ve hre) - doplni kraj/vesnice, rozmisti veg
KOLIZE = []     # (Matrix, rozmer) - kvadry kameni a vozu; export_game je prida ke kolizim sveta


def misto(pid, x, y, z, k, yaw, P=None, sink=0.18, collide=None):
    """Zapsat instanci modelu (meritko k vuci skutecne velikosti, yaw = otoceni ve hre kolem svisle osy).
    Pata se zapusti o sink * vyska. Kolize kvadrem (vetsi kameny a vozy) do KOLIZE; P jen rika, ze kolizi chceme
    (cast P nemusi mit zadnou vlastni geometrii, pak by se jeji cols neulozily)."""
    w, h, d = DIM[pid]
    import kraj
    if pid in SKALY or pid.startswith("balvan"):
        kraj.zapis_skalu(x, z)
    elif not pid.startswith("kamen") and (kraj.rostlina_ve_vode(pid, x, z, y) or not kraj.druh_smi(pid, x, z, y)):
        return
    y0 = y - sink * h * k
    MISTA.append((pid, x, y0, z, k, yaw))
    if P is not None and (collide if collide is not None else h * k > 0.45):
        from lib import M
        from mathutils import Matrix
        B = Matrix.Rotation(yaw, 3, "Y")
        hh = h * k * (1.0 - sink)
        KOLIZE.append((M((x, y + hh / 2 - 0.02, z), basis=B), (w * k * 0.82, hh, d * k * 0.82)))


def _extract(pid):
    if pid == "psenice_2":
        pid = "psenice"                    # tataz sit, textura se prebarvi v add_to_library
    f = os.path.join(DIR, pid + ".glb")
    zdroj = os.path.join(HERE, "zdroje", pid + ".glb")        # modely od Misi v repu (psenice; licence docs/modely_misa.md)
    if not os.path.exists(f) and os.path.exists(zdroj):
        os.makedirs(DIR, exist_ok=True)
        import shutil
        shutil.copy(zdroj, f)
    if not os.path.exists(f):
        os.makedirs(DIR, exist_ok=True)
        data = subprocess.run(["git", "-C", HERE, "show", "%s:modely/nove/%s.glb" % (GIT_REF, pid)], capture_output=True, check=True).stdout
        with open(f, "wb") as fh:
            fh.write(data)
    return f


def _decimuj_material(me, prefix, cil):
    """Decimace jen ploch s materialem prefix* na ~cil trojuhelniku (ostatni plochy beze zmeny)."""
    import bpy
    import bmesh
    idx = {i for i, m in enumerate(me.materials) if m and m.name.startswith(prefix)}
    tri = sum(len(p.vertices) - 2 for p in me.polygons if p.material_index in idx)
    if tri <= cil:
        return me
    me = me.copy()                       # vlastni kopie (puvodni sit muze patrit jinemu objektu)
    ob = bpy.data.objects.new("tmp_dec", me)
    bpy.context.scene.collection.objects.link(ob)
    vg = ob.vertex_groups.new(name="dec")
    vg.add(list({v for p in me.polygons if p.material_index in idx for v in p.vertices}), 1.0, "REPLACE")
    dm = ob.modifiers.new("dec", "DECIMATE")
    dm.ratio = cil / tri
    dm.vertex_group = "dec"
    dm.vertex_group_factor = 1.0
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier="dec")
    me = ob.data
    bpy.data.objects.remove(ob)
    return me


def _obj(me, name):
    import bpy
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    return ob


def _apply(ob, mod):
    import bpy
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)


def _skala_lod(pid, me):
    """Skalni vez: puvodni sken ma tisice neuzavrenych hran (strepy), decimaci se roztrhal na supiny.
    Kamen: voxel remesh (uzavreny objem) -> decimace na 2700 troj. -> nove UV -> zapeceni barvy a normal
    z originalu (Cycles, 1024 px). LOD1 (800) a LOD2 (150) decimaci uz uzavrene site, stejny material.
    Trava na skale (jine materialy) zustava jen v LOD0. Vraci (LOD0, LOD1, LOD2)."""
    import bpy
    import bmesh
    rock_idx = {i for i, m in enumerate(me.materials) if m and m.name.startswith("skala")}
    hi_me = me.copy()
    bm = bmesh.new()
    bm.from_mesh(hi_me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in rock_idx], context="FACES")
    bm.to_mesh(hi_me)
    bm.free()
    rest = me.copy()
    bm = bmesh.new()
    bm.from_mesh(rest)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in rock_idx], context="FACES")
    bm.to_mesh(rest)
    bm.free()
    hi = _obj(hi_me, "hi_" + pid)
    lo = _obj(hi_me.copy(), "lo_" + pid)
    r = lo.modifiers.new("rm", "REMESH")
    r.mode = "VOXEL"
    r.voxel_size = 0.15
    r.use_smooth_shade = True
    _apply(lo, r)
    d = lo.modifiers.new("dec", "DECIMATE")
    d.ratio = 2700.0 / (2.0 * len(lo.data.polygons))
    _apply(lo, d)
    while lo.data.uv_layers:
        lo.data.uv_layers.remove(lo.data.uv_layers[0])
    lo.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    mat = bpy.data.materials.new("skala_%s_pec" % pid)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.92
    ic = bpy.data.images.new("nove_%s_pec_barva" % pid, 1024, 1024)
    inn = bpy.data.images.new("nove_%s_pec_normala" % pid, 1024, 1024)
    inn.colorspace_settings.name = "Non-Color"
    tc = nt.nodes.new("ShaderNodeTexImage")
    tc.image = ic
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = inn
    tn.interpolation = "Linear"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    lo.data.materials.clear()
    lo.data.materials.append(mat)
    sc = bpy.context.scene
    eng = sc.render.engine
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 1
    sc.cycles.device = "CPU"
    sc.render.bake.use_selected_to_active = True
    sc.render.bake.cage_extrusion = 0.4
    sc.render.bake.max_ray_distance = 0.8
    sc.render.bake.margin = 6
    bpy.ops.object.select_all(action="DESELECT")
    hi.select_set(True)
    lo.select_set(True)
    bpy.context.view_layer.objects.active = lo
    nt.nodes.active = tc
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"})
    nt.nodes.active = tn
    bpy.ops.object.bake(type="NORMAL")
    sc.render.engine = eng
    ic.pack()
    inn.pack()
    rock = lo.data
    bpy.data.objects.remove(hi)
    bpy.data.objects.remove(lo)
    # LOD1, LOD2 z uzavrene site (UV i material zustavaji)
    lods = []
    for cil in (800.0, 150.0):
        ob = _obj(rock.copy(), "lod_" + pid)
        dm = ob.modifiers.new("dec", "DECIMATE")
        dm.ratio = min(1.0, cil / max(1, len(ob.data.polygons)))
        _apply(ob, dm)
        lods.append(ob.data)
        bpy.data.objects.remove(ob)
    # LOD0 = kamen + trava ze skaly
    ob = _obj(rock.copy(), "lod0_" + pid)
    if len(rest.polygons):
        o2 = _obj(rest, "rest_" + pid)
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        o2.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.join()
    lod0 = ob.data
    bpy.data.objects.remove(ob)
    return lod0, lods[0], lods[1]


def _prebarvi_zelene(img):
    """Zrala psenice -> zeleny (cervnovy) lan: jas zustane, odstin ze zlate do zelene (alfa beze zmeny)."""
    import numpy as np
    if img.size[0] == 0:
        return
    a = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
    lum = a[:, :3] @ np.array([0.3, 0.59, 0.11], dtype=np.float32)
    zel = np.stack([lum * 0.55, lum * 1.05, lum * 0.38], axis=1)
    a[:, :3] = np.clip(a[:, :3] * 0.2 + zel * 0.8, 0.0, 1.0)
    img.pixels[:] = a.ravel()
    img.update()
    img.pack()


def add_to_library(LIB):
    """Kazdy model jako druh s jednou variantou (sit s paty na pocatku); obrazky prejmenovane 'nove_<model>_...'."""
    import bpy
    from mathutils import Matrix
    used = {m[0] for m in MISTA} | set(STROMY) | set(PODROST)      # stromy a podrost se rozmistuji az ve veg
    for pid in sorted(used | {p + "_daleko" for p in used if p in LOD}):
        if (pid.endswith("_daleko") and pid[:-7] in SKALY) or pid.endswith("_daleko2"):
            continue                                                  # vyrobi se z plneho modelu nize
        before = set(bpy.data.objects)
        imgs0 = set(bpy.data.images)
        bpy.ops.import_scene.gltf(filepath=_extract(pid))
        new = [o for o in bpy.data.objects if o not in before]
        for i, img in enumerate(set(bpy.data.images) - imgs0):
            img.name = "nove_%s_%d" % (pid, i)
            if pid == "psenice_2":
                _prebarvi_zelene(img)
        meshes = [o for o in new if o.type == "MESH"]
        parts = []
        for o in meshes:
            me = o.data.copy()
            me.transform(o.matrix_world.copy())
            parts.append(me)
        # vic siti (vuz: drevo + platno) -> jedna sit s vice materialy
        ob = bpy.data.objects.new("tmp_" + pid, parts[0])
        bpy.context.scene.collection.objects.link(ob)
        for me in parts[1:]:
            o2 = bpy.data.objects.new("tmp2", me)
            bpy.context.scene.collection.objects.link(o2)
            bpy.ops.object.select_all(action="DESELECT")
            ob.select_set(True)
            o2.select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.join()
        me = ob.data
        xs = [v.co.x for v in me.vertices]
        ys = [v.co.y for v in me.vertices]
        zs = [v.co.z for v in me.vertices]
        me.transform(Matrix.Translation(((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)))))
        h = max(zs) - min(zs)
        w = max(max(xs) - min(xs), max(ys) - min(ys))
        if pid in SKALY:
            # ROZPOCET: LOD0 = kamen zjednoduseny na ~2700 troj. + trava; borovice z modelu pryc (5750 troj. kazda),
            # na vrcholy vezi se sazi samostatne borovice s vlastnimi LOD (kraj.rocks)
            import bmesh
            bm0 = bmesh.new()
            bm0.from_mesh(me)
            pine = {i for i, m in enumerate(me.materials) if m and "borovice" in m.name}
            bmesh.ops.delete(bm0, geom=[f for f in bm0.faces if f.material_index in pine], context="FACES")
            bm0.to_mesh(me)
            bm0.free()
            me, far, far2 = _skala_lod(pid, me)
            print("knihovna (nove)", pid, "LOD0", sum(len(p.vertices) - 2 for p in me.polygons), "troj.",
                  "LOD1", len(far.polygons), "LOD2", len(far2.polygons))
            LIB[pid + "_daleko"] = [(far, h, w)]
            LIB[pid + "_daleko2"] = [(far2, h, w)]
        bpy.data.objects.remove(ob)
        for o in new:
            bpy.data.objects.remove(o)
        LIB[pid] = [(me, h, w)]
        print("knihovna (nove)", pid, round(h, 2), round(w, 2))


def rozmistit(V, place, LIB):
    """Instance do kolekce vegetace; meritko k presne (vyska = k * skutecna vyska modelu v knihovne).
    Stromy maji dvojici: plny model (ve hre zblizka) a <model>_daleko (karty, dal nez ~60 m)."""
    n = 0
    for pid, x, y, z, k, yaw in MISTA:
        # Blender: model hledi do -Y, otoceni kolem Z; ve hre yaw kolem Y (stejny smysl)
        for p in ((pid, pid + "_daleko", pid + "_daleko2") if pid in SKALY else ((pid, pid + "_daleko") if pid in LOD else (pid,))):
            if p in LIB:
                place(V, p, (x, y, z), LIB[p][0][1] * k, yaw=yaw, variant=0)
                n += 1
    print("nove modely: %d instanci" % n)


def skala(pid, x, y, z, k, yaw, P):
    """Skalni vez na teren: pata 1 m (krat meritko) pod zemi, kolize kvadrem jadra veze."""
    misto(pid, x, y, z, k, yaw, P, sink=SKALY_POD / DIM[pid][1], collide=True)


def strom(pid, x, y, z, vyska):
    """Strom v2 na misto (vyska v m); bez kolize jako ostatni stromy. Ve vode a na brehovem pasu ne."""
    import kraj
    if kraj.rostlina_ve_vode(pid, x, z, y) or not kraj.druh_smi(pid, x, z, y):
        return
    MISTA.append((pid, x, y - 0.1, z, vyska / DIM[pid][1], R_.uniform(0, 2 * math.pi)))


import random as _random  # noqa: E402
R_ = _random.Random(2026)


# ------------------------------------------------------------------ modely od Misi (SketchUp / Sketchfab)
# klicove slovo v nazvu materialu -> herni material (svet.gd ho priradi stejne jako ostatnim stavbam)
SKETCHUP_MAT = [
    (("roof", "tile", "shingle", "strech", "sindel"), "sindel_hra"),
    (("thatch", "straw", "dosk", "slam"), "dosky_hra"),
    (("logedge", "log_end", "stump"), "drevo_rez"),
    (("bark", "kura"), "kura"),
    (("plank", "floor", "board", "prkn", "podlah"), "prkna_ven"),
    (("wood", "beam", "timber", "tram", "drev"), "dub_ven"),
    (("plaster", "omit", "stucco"), "omitka_ven"),
]


def _import_sketchup(ob, tris_max=4000, tex_max=1024, stavba=False):
    """Jedna pruchozi uprava modelu ze SketchUpu/Sketchfabu (hostinec a dalsi Misovy modely):
    1. sloucit vrcholy (1 mm) a otocit normaly ven (SketchUp casto otaci plochy);
    2. materialy: podle klicoveho slova na herni fotograficke materialy (UV prepocitane na metry krychlovou
       projekci, herni shader deli UV velikosti fotky); co nema protejsek (kamen, kov, stit), zustava z glb,
       ale bez lesku: drsnost >= 0,85, kov jen u kovu - zadny vychozi 0,5 lesk (modra strecha);
    3. rovinna decimace (1 st.) a pokud je stale vic nez tris_max, decimace na tris_max;
    4. textury nejvys tex_max px.
    Vraci (troj. pred, troj. po, seznam (material -> herni material))."""
    import math
    import bmesh
    import bpy
    me = ob.data
    pred = sum(len(p.vertices) - 2 for p in me.polygons)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # materialy
    mapa = {}
    for i, m in enumerate(me.materials):
        if m is None:
            continue
        low = m.name.lower()
        for keys, game in SKETCHUP_MAT:
            if any(k in low for k in keys):
                mapa[i] = game
                break
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new()
    for f in bm.faces:
        if f.material_index not in mapa:
            continue
        n = f.normal
        for lp in f.loops:
            p = lp.vert.co
            if abs(n.z) > 0.7:
                u, v = p.x, p.y
            elif abs(n.x) > abs(n.y):
                u, v = (p.y if n.x > 0 else -p.y), p.z
            else:
                u, v = (-p.x if n.y > 0 else p.x), p.z
            lp[uv].uv = (u, v)
    bm.to_mesh(me)
    bm.free()
    for i, game in mapa.items():
        nm = bpy.data.materials.get(game) or bpy.data.materials.new(game)
        me.materials[i] = nm
    for m in me.materials:
        if m is None or m.name in mapa.values() or not m.use_nodes:
            continue
        b = m.node_tree.nodes.get("Principled BSDF")
        if b is None:
            continue
        kov = any(k in m.name.lower() for k in ("metal", "iron", "steel", "zelez", "kov"))
        for s in ("Roughness", "Metallic"):
            for l in list(b.inputs[s].links):
                m.node_tree.links.remove(l)
        b.inputs["Roughness"].default_value = 0.7 if kov else 0.9
        b.inputs["Metallic"].default_value = 0.6 if kov else 0.0
    # geometrie
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    d = ob.modifiers.new("plan", "DECIMATE")
    d.decimate_type = "DISSOLVE"
    d.angle_limit = math.radians(1.0)
    d.delimit = {"MATERIAL", "UV"}
    bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode="OBJECT")
    po = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    # hrube zjednoduseni (collapse) jen u predmetu: u stavby by zuzilo dvere a okna (kolize je ze site, hrac se zasekne)
    if po > tris_max and not stavba:
        d = ob.modifiers.new("dec", "DECIMATE")
        d.ratio = tris_max / po
        bpy.ops.object.modifier_apply(modifier=d.name)
        po = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    for img in bpy.data.images:
        if img.size[0] > tex_max or img.size[1] > tex_max:
            k = tex_max / max(img.size[0], img.size[1])
            img.scale(max(1, int(img.size[0] * k)), max(1, int(img.size[1] * k)))
    print("sketchup import:", ob.name, pred, "->", po, "troj.", sorted(set(mapa.values())))
    return pred, po, sorted({(me.materials[i].name, g) for i, g in mapa.items()})
