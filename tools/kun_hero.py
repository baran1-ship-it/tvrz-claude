"""Kun Hero Horse v2.0 (Míša 25. 11., placený balík „Horse for Heroes“, Disk; rozbor docs/rozpracovane/kun_hero.md)
-> modely/kone/kun_hero.glb pro hru.
  /opt/bl/bin/python tools/kun_hero.py <rozbaleny_archiv> <srst> <hriva>
    rozbaleny_archiv: slozka s Export/Hero_Horse_PoorArmor.FBX a Textures/*.tif (CH_Hero_Horse.v.2.0_LIGHT.rar)
    srst: Bay | Black | Chestnut | Palomino | White,  hriva: Brown | Black | Palomino | White
Co dela:
 - telo (Hero_Horse 10 374 troj.), hriva (1 000), ocas (192) a z chudeho postroje jen PA_Harness (uzdecka + poprsnik,
   skinovane na kosti kone, pohybuje se s nim); sedlo, deka, trmeny, otezi a sukne postroje pryc - hra ma dobove sedlo
   z Balt Horse (jizda.json kun.vystroj) a otezi pocita sama (scripts/otezi.gd)
 - textury z TIF 4096 -> PNG (telo 1024, hriva 512 s alfou, postroj 1024) - tablet, pravidla kvalita.json
 - animace: jedna stopa „Take 001“ (1555 snimku, 30 FPS); klipy dela hra jako useky (jizda.json kun.klipy_z_useku
   podle tabulky snimku z Hero_Horse_notes.rtf)
"""
import os
import sys

import bpy

SRC, SRST, HRIVA = sys.argv[-3], sys.argv[-2], sys.argv[-1]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modely", "kone")
PRYC = ("PA_Saddle", "PA_Blanket", "PA_Stirrups", "PA_Reins", "PA_Skirt")
TEX = os.path.join(OUT, "kun_hero_tex")
os.makedirs(TEX, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(SRC, "Export", "Hero_Horse_PoorArmor.FBX"))
for o in list(bpy.data.objects):
    if o.type == "MESH" and o.name.startswith(PRYC):
        bpy.data.objects.remove(o)


def png(tif, jm, px, alfa):
    """PNG z tools/kun_hero_tex.py (TIF tu Blender bez okna nenacte)."""
    return bpy.data.images.load(os.path.join(TEX, jm + ".png"))


def material(m, barva, normal, alfa):
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
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
    b.inputs["Roughness"].default_value = 0.7


telo = png("Horse_%s.tif" % SRST, "srst_%s" % SRST.lower(), 1024, False)
telo_n = png("Horse_Normals.tif", "srst_normaly", 1024, False)
hriva = png("Horse_Hair_%s.tif" % HRIVA, "hriva_%s" % HRIVA.lower(), 512, True)
hriva_n = png("Horse_Hair_Normals.tif", "hriva_normaly", 512, False)
postroj = png("Poor_Armor.tif", "postroj", 1024, True)
postroj_n = png("Poor_Armor_normals.tif", "postroj_normaly", 1024, False)
hotovo = set()
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    for m in o.data.materials:
        if m is None or m.name in hotovo:
            continue
        hotovo.add(m.name)
        jm = m.name.lower()
        if "hair" in jm:
            material(m, hriva, hriva_n, True)
        elif "armor" in jm:
            material(m, postroj, postroj_n, True)
        else:
            material(m, telo, telo_n, False)
    print("SIT", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), [m.name for m in o.data.materials])
cil = os.path.join(OUT, "kun_hero.glb")
bpy.ops.export_scene.gltf(filepath=cil, export_format="GLB", export_animations=True, export_force_sampling=True,
                          export_image_format="AUTO", export_apply=False)
print("KUN_HERO", cil, os.path.getsize(cil))
