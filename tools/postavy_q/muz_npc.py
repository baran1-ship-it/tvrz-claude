"""Novi vesnicane z NPC Character Pack (Misa 25. 11. „nahrada za muze, at nemame ty potrhane borce“, Disk
1qW5K2xC0Ega4xWvTlq7xGVZ5r9ZBLDhL) -> sada postavy modely/postavy/npc/<sada>_cela.gltf jako ostatni sady (scripts/vzhled.gd).
  /opt/bl/bin/python -I tools/postavy_q/muz_npc.py <vstup.glb> <slozka_textur_1k> <sada> [cil_trojuhelniku]
Vstup: glb vyvezeny Godotem z UE4 FBX (zk_muz/vyvoz.gd) - Blender UE4 FBX kostru nacte jen jako prazdne objekty bez vah.
Co dela:
 - kostra na tvar UAL (jmena jako klipy scripts/anim_ual.gd): head -> Head, nad pelvis kost root; zkrutne kosti
   (*_twist_01_*) slity do rodice (vahy secteny), pak smazany
 - site spojene do jedne, zmenseni (Decimate collapse) na cil trojuhelniku (vychozi 12 000, tablet)
 - materialy: telo+odev, hlava, vlasy/vousy (alfa) s texturami 1K (PNG z TGA 4096)
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

ARG = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
HLAVA_Z = ARG[ARG.index("--hlava") + 1] if "--hlava" in ARG else ""
ARG = [a for i, a in enumerate(ARG) if a != "--hlava" and (i == 0 or ARG[i - 1] != "--hlava")]
VSTUP, TEX, SADA = ARG[0], ARG[1], ARG[2]
CIL = int(ARG[3]) if len(ARG) > 3 else 12000
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "modely", "postavy", "npc")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=VSTUP)
# druhy odev postavy (Full_02) je bez hlavy - hlava, oci, vlasy a vousy z prvniho (Full_01, stejna kostra a klid)
if HLAVA_Z:
    arm0 = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    pred = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=HLAVA_Z)
    for o in [o for o in bpy.data.objects if o not in pred]:
        j = o.name.lower()
        if o.type == "MESH" and any(x in j for x in ("head", "eyes", "hair", "beard", "mustache", "brow")):
            m = o.matrix_world.copy()
            o.parent = arm0.parent if arm0.parent else None
            o.matrix_world = m
            for md in o.modifiers:
                if md.type == "ARMATURE":
                    md.object = arm0
            print("HLAVA z", HLAVA_Z, o.name)
        else:
            bpy.data.objects.remove(o)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
site = [o for o in bpy.data.objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)]
for o in [o for o in bpy.data.objects if o.type == "MESH" and o not in site]:
    bpy.data.objects.remove(o)  # tvar kosti z importu glTF (Icosphere)
print("VSTUP kosti", len(arm.data.bones), "site", [(o.name, len(o.data.polygons)) for o in site])
# UE4: osa z nahoru a centimetry (v Godotu postava lezela a mela 0,12 m) - otoceni a meritko do kostry a vrcholu
for o in bpy.data.objects:
    if o.type == "EMPTY":
        for ch in list(o.children):
            m = ch.matrix_world.copy()
            ch.parent = None
            ch.matrix_world = m
for o in bpy.data.objects:
    o.select_set(o.type in ("ARMATURE", "MESH"))
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
vys = max((arm.matrix_world @ b.head_local).z for b in arm.data.bones)
print("VSTUP vyska kostry %.2f m" % vys)

# --- kostra na tvar UAL
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
zkrutne = [b.name for b in eb if "_twist_" in b.name]
rodic = {b.name: b.parent.name for b in eb if b.parent}
if "head" in eb:
    eb["head"].name = "Head"
if "root" not in eb and "pelvis" in eb:
    r = eb.new("root")
    r.head = (0, 0, 0)
    r.tail = (0, 0.1, 0)
    eb["pelvis"].parent = r
bpy.ops.object.mode_set(mode="OBJECT")
for o in site:
    for z in zkrutne:
        g = o.vertex_groups.get(z)
        if g is None:
            continue
        cil = o.vertex_groups.get(rodic[z]) or o.vertex_groups.new(name=rodic[z])
        for v in o.data.vertices:
            for vg in v.groups:
                if vg.group == g.index and vg.weight > 0:
                    cil.add([v.index], vg.weight, "ADD")
        o.vertex_groups.remove(g)
    if o.vertex_groups.get("head"):
        o.vertex_groups["head"].name = "Head"
bpy.ops.object.mode_set(mode="EDIT")
for z in zkrutne:
    arm.data.edit_bones.remove(arm.data.edit_bones[z])
bpy.ops.object.mode_set(mode="OBJECT")

# --- osy kosti jako UAL (zkouska 25. 11.: klipy UAL na kostre UE4 - postava lezela; klipy Godotu jsou mistni rotace
# kosti, ty sedi jen pri stejnych osach klidove pozy). Klid se meni bez pozy - sit v Blenderu zustane (deformace =
# poza x klid^-1 = 1), vazebne matice glTF se spocitaji z noveho klidu. Poloha kloubu zustava (proporce postavy).
ZENA = SADA.startswith("npc_zena")
# vzor klidu a os: sada UAL stejneho pohlavi (proporce ramen a panve)
UAL_SADA = os.path.join(OUT, "npc_anezka_cela.gltf" if ZENA else "npc_bartos_cela.gltf")
# kontejner s daty jen z baliku (bez zdroje .gltf): vzor vyvezeny Godotem z importu (tools/postavy_q/vyvoz_res.gd)
UAL_SADA = os.environ.get("UAL_SADA_ZENA" if ZENA else "UAL_SADA", UAL_SADA)
pred = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=UAL_SADA)
nove = [o for o in bpy.data.objects if o not in pred]
ual = next(o for o in nove if o.type == "ARMATURE")
osy = {b.name: (ual.matrix_world @ b.matrix_local).to_quaternion() for b in ual.data.bones}
klouby = {b.name: ual.matrix_world @ b.head_local for b in ual.data.bones}
for o in nove:
    bpy.data.objects.remove(o)

# --- klidova poza jako UAL (zkouska 25. 11.: osy stejne, ale ruce 25 cm od tela - kostra UE4 je v klidu v A poze, UAL
# jinak; mistni rotace klipu pak natoci kosti o jiny smer kloubu). Kazdou kost (od korene) natocit tak, aby smer
# k hlavnimu potomkovi byl jako v UAL, pozu zapect do site a prijmout jako klid.
HLAVNI = {"pelvis": "spine_01", "spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "neck_01", "neck_01": "Head",
          "clavicle_l": "upperarm_l", "upperarm_l": "lowerarm_l", "lowerarm_l": "hand_l", "hand_l": "middle_01_l",
          "clavicle_r": "upperarm_r", "upperarm_r": "lowerarm_r", "lowerarm_r": "hand_r", "hand_r": "middle_01_r",
          "thigh_l": "calf_l", "calf_l": "foot_l", "foot_l": "ball_l", "thigh_r": "calf_r", "calf_r": "foot_r",
          "foot_r": "ball_r"}
for s in ("l", "r"):
    for prst in ("index", "middle", "ring", "pinky", "thumb"):
        HLAVNI["%s_01_%s" % (prst, s)] = "%s_02_%s" % (prst, s)
        HLAVNI["%s_02_%s" % (prst, s)] = "%s_03_%s" % (prst, s)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
natoceno = 0
for b in arm.data.bones:  # poradi: rodic pred potomkem
    c = HLAVNI.get(b.name)
    if c is None or c not in arm.pose.bones or b.name not in klouby or c not in klouby:
        continue
    bpy.context.view_layer.update()
    pb = arm.pose.bones[b.name]
    nyni = arm.pose.bones[c].head - pb.head
    chci = arm.matrix_world.inverted().to_3x3() @ (klouby[c] - klouby[b.name])
    if nyni.length < 1e-5 or chci.length < 1e-5:
        continue
    r = nyni.rotation_difference(chci).to_matrix().to_4x4()
    h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ r @ Matrix.Translation(-h) @ pb.matrix
    natoceno += 1
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode="OBJECT")
for o in site:
    md = next(m for m in o.modifiers if m.type == "ARMATURE")
    bpy.context.view_layer.objects.active = o
    novy = o.modifiers.new("kostra_nova", "ARMATURE")
    novy.object = arm
    bpy.ops.object.modifier_apply(modifier=md.name)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode="OBJECT")
print("POZA natoceno kosti", natoceno)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
inv = arm.matrix_world.to_quaternion().inverted()
srovnano = 0
for b in arm.data.edit_bones:
    q = osy.get(b.name)
    if q is None:
        continue
    d = b.length
    b.matrix = Matrix.LocRotScale(b.head.copy(), inv @ q, None)
    b.length = d
    srovnano += 1
bpy.ops.object.mode_set(mode="OBJECT")
print("OSY srovnano", srovnano, "z", len(arm.data.bones), "chybi v UAL", [b.name for b in arm.data.bones if b.name not in osy])


# --- sukne a dlouhe kabatce (nezavisla kontrola 26. 11., snimky chuze zblizka: noha prochazi suknemi zen 01/02 a
# kabatci muzu 03-05): spodek odevu pod panvi vazany na stehna -> kosti sukne sukne_<i>_<j> jako sady Quaternius
# (tools/postavy_q/q_obleceni.py _skirt_bones; ve hre ridi scripts/sukne_ridic.gd + pruzina, lide.gd _sukne)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from q_obleceni import _skirt_bones, _skirt_leg_weights  # noqa: E402

pel_z = (arm.matrix_world @ arm.data.bones["pelvis"].head_local).z
koleno_z = (arm.matrix_world @ arm.data.bones["calf_l"].head_local).z
odev = [o for o in site if "cloth" in o.name.lower() and not any(x in o.name.lower() for x in ("pants", "shoes", "belt", "bag"))]
spodky = []
for o in odev:
    noha = [o.vertex_groups[g].index for g in ("thigh_l", "thigh_r", "calf_l", "calf_r") if g in o.vertex_groups]
    # vse pod panvi (sukne zen jsou cele na panvi - tuhy zvon, noha jim prochazi; kabatce muzu na stehnech)
    vyber = [v.index for v in o.data.vertices if (o.matrix_world @ v.co).z < pel_z + 0.03]
    print("SUKNE kus", o.name, "pod panvi", len(vyber), "na nohou", sum(1 for i in vyber if any(
        g.group in noha and g.weight > 0.05 for g in o.data.vertices[i].groups)))
    if len(vyber) < 50:
        continue
    # 26. 11. novy rozbor (2. oprava nepomohla muzi 03-05): kosti sukne toci predni stred prumerem obou stehen - v kroku
    # (noha vpred, druha vzad) stoji a kratkou tunikou projde stehno. Kratky odev (lem nad kolenem) = vahy stehen jako
    # kotle Quaternius (leva pulka leve stehno, prava prave), kosti sukne jen pro dlouhe sukne pod koleno.
    lem = min((o.matrix_world @ o.data.vertices[i].co).z for i in vyber)
    if lem > koleno_z + 0.03:
        _skirt_leg_weights(o, arm, pel_z + 0.03, lem, ZENA)
        print("SUKNE kratky odev (vahy stehen)", o.name, "lem %.2f koleno %.2f" % (lem, koleno_z))
        continue
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for i in vyber:
        o.data.vertices[i].select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="SELECTED")
    bpy.ops.object.mode_set(mode="OBJECT")
    novy = [x for x in bpy.context.selected_objects if x != o]
    spodky += novy
    print("SUKNE spodek", o.name, len(vyber), "vrcholu")
if spodky:
    bpy.ops.object.select_all(action="DESELECT")
    for x in spodky:
        x.select_set(True)
    bpy.context.view_layer.objects.active = spodky[0]
    bpy.ops.object.join()
    sk = bpy.context.view_layer.objects.active
    z_bot = min((sk.matrix_world @ v.co).z for v in sk.data.vertices)
    _skirt_bones(sk, arm, pel_z + 0.03, z_bot)
    # spodek zpet k odevu a sev (stejne vrcholy po oddeleni) spojit - pred zmensenim, jinak by se sev rozevrel
    bpy.ops.object.select_all(action="DESELECT")
    for x in odev + [sk]:
        x.select_set(True)
    bpy.context.view_layer.objects.active = odev[0]
    bpy.ops.object.join()
    od = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.00001)
    bpy.ops.object.mode_set(mode="OBJECT")
    site = [o for o in bpy.data.objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)]
    print("SUKNE odev", od.name, len(od.data.vertices), "vrcholu")

# --- materialy a textury 1K
def obr(jm):
    p = os.path.join(TEX, jm)
    return bpy.data.images.load(p) if os.path.exists(p) else None


def material(m, barva, normal, alfa):
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    b.inputs["Roughness"].default_value = 0.85
    if barva:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = barva
        nt.links.new(t.outputs[0], b.inputs["Base Color"])
        if alfa:
            nt.links.new(t.outputs[1], b.inputs["Alpha"])
            m.blend_method = "CLIP"
    if normal:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = normal
        tn.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs[0], nm.inputs[1])
        nt.links.new(nm.outputs[0], b.inputs["Normal"])


import json  # noqa: E402
c = SADA.split("_")[2]  # npc_muz_<cislo postavy 01..05>[_varianta], npc_zena_<cislo>
_tx = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "muz_npc.json")))
TX = _tx["zena_" + c] if ZENA else _tx[c]
mat = {}
def vlasy_dilatace(img):
    """Barva pramenu do pruhledne casti a alfa x nasobek (muz_npc.json vlasy_textura) - cerne okraje na mipmapach."""
    import numpy as np
    vt = _tx["vlasy_textura"]
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    zn = a[..., 3] > 0.5
    rgb = a[..., :3] * zn[..., None]
    vah = zn.astype(np.float32)
    for _ in range(int(vt["dilatace_px"])):
        s = np.zeros_like(rgb)
        n = np.zeros_like(vah)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            s += np.roll(rgb, (dy, dx), (0, 1))
            n += np.roll(vah, (dy, dx), (0, 1))
        nove = (vah == 0) & (n > 0)
        rgb[nove] = s[nove] / n[nove][:, None]
        vah[nove] = 1.0
    a[..., :3] = np.where(zn[..., None], a[..., :3], rgb)
    a[..., 3] = np.clip(a[..., 3] * float(vt["alfa_nasobek"]), 0.0, 1.0)
    img.pixels[:] = a.ravel()
    img.update()
    return img


for k in ("telo", "hlava", "vlasy"):
    mat[k] = bpy.data.materials.new(SADA + "_" + k)
    bv = obr(TX[k][0] + ".png")
    if k == "vlasy" and bv is not None:
        bv = vlasy_dilatace(bv)
    material(mat[k], bv, obr(TX[k][1] + ".png"), k != "hlava")


def druh(o):
    """Podle jmena kusu (hlava, oci a ruce = textura hlavy; vlasy, vousy), jinak podle materialu z FBX (postava 05 ma
    materialy „20 - Default“ bez jmena)."""
    m = (o.material_slots[0].name if o.material_slots else "").lower()
    j = o.name.lower()
    if any(x in j for x in ("hair", "beard", "mustache", "brow")) or "hair" in m:
        return "vlasy"
    if any(x in j for x in ("head", "eyes", "hands", "arms")) or "head" in m or (ZENA and "character" in m):
        return "hlava"
    return "telo"


druhy = {o.name: druh(o) for o in site}  # pred smazanim materialu (druh podle materialu FBX)
for o in site:
    o.data.materials.clear()
    o.data.materials.append(mat[druhy[o.name]])

# --- vlasy (Misa 27. 11. „vlasy borec na dvore“; rešerše reserse_animace_postavy_27_11.md kap. 2): karty vlasu se
# nezmensuji collapse (roztrhal je), ale vnejsi karty se nechaji cele do rozpoctu vlasy_troj_max a vnitrni (zakryte)
# vypadnou; pod vlasy nepruhledna cepice (kopie kuze hlavy pod vlasy) v barve vlasu z husteho bloku textury vlasu -
# mezerami prosvita vlas, ne bila kuze temene (muz_npc.json cepice)
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402


def _hustý_blok(img, n=64):
    w, h = img.size
    al = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., 3]
    ii = np.cumsum(np.cumsum(np.pad(al, ((1, 0), (1, 0))), 0), 1)
    sm = ii[n:, n:] - ii[:-n, n:] - ii[n:, :-n] + ii[:-n, :-n]
    y, x = np.unravel_index(np.argmax(sm), sm.shape)
    return (x / w, y / h, (x + n) / w, (y + n) / h)


VL = _tx.get("vlasy_karty")
vlasy_o = [o for o in site if "hair" in o.name.lower()]
hlava_o = next((o for o in site if "head" in o.name.lower()), None)
if VL and vlasy_o and hlava_o:
    stred = sum((hlava_o.matrix_world @ v.co for v in hlava_o.data.vertices), Vector()) / len(hlava_o.data.vertices)
    kd = KDTree(sum(len(o.data.vertices) for o in vlasy_o))
    k = 0
    for o in vlasy_o:
        for v in o.data.vertices:
            kd.insert(o.matrix_world @ v.co, k)
            k += 1
    kd.balance()
    for o in vlasy_o:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        ostrovy = []
        hotovo = set()
        for f in bm.faces:
            if f.index in hotovo:
                continue
            fr, ost = [f], []
            hotovo.add(f.index)
            while fr:
                g = fr.pop()
                ost.append(g)
                for e in g.edges:
                    for g2 in e.link_faces:
                        if g2.index not in hotovo:
                            hotovo.add(g2.index)
                            fr.append(g2)
            c = sum((o.matrix_world @ g.calc_center_median() for g in ost), Vector()) / len(ost)
            ostrovy.append(((c - stred).length, sum(len(g.verts) - 2 for g in ost), ost))
        ostrovy.sort(key=lambda e: -e[0])
        troj, pryc = 0, []
        for d, t, ost in ostrovy:
            if troj + t <= int(VL["troj_max"]):
                troj += t
            else:
                pryc.extend(ost)
        bmesh.ops.delete(bm, geom=pryc, context="FACES")
        bm.to_mesh(o.data)
        bm.free()
        print("VLASY", o.name, "karet", len(ostrovy), "troj", troj, "(vnejsi do troj_max)")
    # cepice: plochy hlavy, jejichz vsechny vrcholy jsou do vzdal_m od vlasu
    cep = hlava_o.copy()
    cep.data = hlava_o.data.copy()
    cep.name = "Cepice_vlasu"   # zmensuje se jako telo (jednoducha nepruhledna slupka), ne jako karty vlasu
    bpy.context.collection.objects.link(cep)
    bm = bmesh.new()
    bm.from_mesh(cep.data)
    vz = float(VL["cepice_vzdal_m"])
    pryc = [f for f in bm.faces if not all(kd.find(cep.matrix_world @ v.co)[2] < vz for v in f.verts)]
    bmesh.ops.delete(bm, geom=pryc, context="FACES")
    for v in bm.verts:
        v.co += v.normal * float(VL["cepice_posun_m"])
    uvl = bm.loops.layers.uv.active
    img_v = mat["vlasy"].node_tree.nodes["Image Texture"].image if "Image Texture" in mat["vlasy"].node_tree.nodes else None
    if uvl and img_v:
        u0, v0, u1, v1 = _hustý_blok(img_v)
        xs = [v.co.x for v in bm.verts] or [0.0]
        ys = [v.co.y for v in bm.verts] or [0.0]
        for f in bm.faces:
            for lp in f.loops:
                lp[uvl].uv = (u0 + (u1 - u0) * (lp.vert.co.x - min(xs)) / max(1e-6, max(xs) - min(xs)),
                              v0 + (v1 - v0) * (lp.vert.co.y - min(ys)) / max(1e-6, max(ys) - min(ys)))
    bm.to_mesh(cep.data)
    bm.free()
    cep.data.materials.clear()
    cep.data.materials.append(mat["vlasy"])
    site.append(cep)
    print("CEPICE ploch", len(cep.data.polygons))


# --- zmenseni pro tablet (kazdy kus zvlast: hlava a ruce dvojnasobny podil - oblicej a prsty), pak jedna sit
troj = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in site)
pomer = min(1.0, CIL / troj)
for o in site:
    j = o.name.lower()
    r = min(1.0, pomer * (2.0 if ("head" in j or "hands" in j) else 1.0))
    # Misa 26. 11. (0.9999996 „nemaji oci, strasidelne obliceje“): bulva 201 vrcholu po zmenseni ~20 - duhovka z atlasu
    # hlavy rozmazana do kruhu; oci (2 x 200 troj.) se nezmensuji
    if any(x in j for x in _tx["nezmensovat"]):
        r = 1.0
    if r < 1.0:
        bpy.context.view_layer.objects.active = o
        d = o.modifiers.new("zmenseni", "DECIMATE")
        d.ratio = r
        d.use_collapse_triangulate = True
        bpy.ops.object.modifier_move_to_index(modifier=d.name, index=0)
        bpy.ops.object.modifier_apply(modifier=d.name)
bpy.ops.object.select_all(action="DESELECT")
for o in site:
    o.select_set(True)
bpy.context.view_layer.objects.active = site[0]
bpy.ops.object.join()
s = bpy.context.view_layer.objects.active
s.name = SADA + "_cela"
s.data.name = SADA + "_cela"
print("SIT", s.name, "trojuhelniku", troj, "->", sum(len(p.vertices) - 2 for p in s.data.polygons))
arm.name = "Armature"
cil = os.path.join(OUT, SADA + "_cela.gltf")
bpy.ops.export_scene.gltf(filepath=cil, export_format="GLTF_SEPARATE", export_animations=False, export_image_format="AUTO",
                          export_apply=False)
# pruhlednost: jen vlasy s orezem (MASK, jako vlasy ostatnich sad); exporter dal BLEND i telu - tablet: razeni
g = json.load(open(cil))
for m in g.get("materials", []):
    m.pop("alphaCutoff", None)
    if m["name"].endswith("_vlasy"):
        m["alphaMode"] = "MASK"
        m["alphaCutoff"] = 0.5
        m["doubleSided"] = True
    else:
        m.pop("alphaMode", None)
json.dump(g, open(cil, "w"), indent=1)
print("MUZ_NPC", cil, [(m["name"], m.get("alphaMode", "OPAQUE")) for m in g.get("materials", [])])
