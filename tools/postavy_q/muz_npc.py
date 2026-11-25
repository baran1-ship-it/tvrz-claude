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
import os
import sys

import bpy

VSTUP, TEX, SADA = sys.argv[-4:-1] if len(sys.argv) > 4 and sys.argv[-1].isdigit() else sys.argv[-3:]
CIL = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 12000
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "modely", "postavy", "npc")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=VSTUP)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
site = [o for o in bpy.data.objects if o.type == "MESH"]
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


c = SADA.split("_")[-1]  # cislo postavy v balicku (01..05)
predpona = "T_NPC_Character_%s" % c
mat = {"telo": bpy.data.materials.new(SADA + "_telo"), "hlava": bpy.data.materials.new(SADA + "_hlava"),
       "vlasy": bpy.data.materials.new(SADA + "_vlasy")}
material(mat["telo"], obr(predpona + "_Albedo.png"), obr(predpona + "_Normals.png"), True)
material(mat["hlava"], obr(predpona + "_Heads_Albedo.png"), obr(predpona + "_Heads_Normals.png"), False)
material(mat["vlasy"], obr(predpona + "_Hair_Albedo_01.png"), obr(predpona + "_Hair_Normals.png"), True)


def druh(o):
    j = o.name.lower()
    if "hair" in j or "beard" in j or "mustache" in j or "brow" in j:
        return "vlasy"
    if "head" in j or "eyes" in j:
        return "hlava"
    return "telo"


for o in site:
    o.data.materials.clear()
    o.data.materials.append(mat[druh(o)])

# --- jedna sit, zmenseni pro tablet
bpy.ops.object.select_all(action="DESELECT")
for o in site:
    o.select_set(True)
bpy.context.view_layer.objects.active = site[0]
bpy.ops.object.join()
s = bpy.context.view_layer.objects.active
s.name = SADA + "_cela"
s.data.name = SADA + "_cela"
troj = sum(len(p.vertices) - 2 for p in s.data.polygons)
if troj > CIL:
    d = s.modifiers.new("zmenseni", "DECIMATE")
    d.ratio = CIL / troj
    d.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=d.name)
print("SIT", s.name, "trojuhelniku", troj, "->", sum(len(p.vertices) - 2 for p in s.data.polygons))
arm.name = "Armature"
cil = os.path.join(OUT, SADA + "_cela.gltf")
bpy.ops.export_scene.gltf(filepath=cil, export_format="GLTF_SEPARATE", export_animations=False, export_image_format="AUTO",
                          export_apply=False)
print("MUZ_NPC", cil)
