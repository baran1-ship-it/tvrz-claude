"""Kun pro jizdu (Misa 27. 10. noc: „kun a jizda se vsim vsudy podle KCD2“): horse.glb z Disku (Modely, 22. 10.;
kostra 100 kosti, 28 animaci: Idle 1-3, Walk(_L/_R), Gallop(_L/_R), Run_Stop, Jump(_Run/_Land), Eat, Buck 1-3,
Swim(_L/_R), Sleep, Death, Arise, Falling/Fallen; sedlo s trmeny) -> herni verze pro tablet.
Trida postava (pravidla_modelu.json: hrac na nem sedi, je vzdy zblizka): LOD0 do 14 000 troj. (decimace po materialech),
textury tela 2048, ostatni 1024, animace s cistymi jmeny (bez 'Skeleton|' a '_Object_9').

  /opt/bl/bin/python tools/kun_priprava.py <horse.glb> modely/postavy/kun.glb
Stazeni: curl -sL "https://drive.usercontent.google.com/download?id=10NF3SfzeAT8Daqk1IjAGn4AzuGymXM8I&export=download&confirm=t"
"""
import sys

import bpy

SRC, DST = sys.argv[-2], sys.argv[-1]
# cil trojuhelniku po materialu (soucet ~13 500)
CIL = {"Horse": 8000, "Hair": 2600, "Saddle": 2400, "Horseshoe": 300, "Cornea": 200}
TEX = {"Horse": 2048}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
# hriva a ocas (material Hair) maji ve zdroji vadne vahy: po deformaci kostrou sit siaha do 32 m nad kone vysokeho 20
# (snimek kun_foto 28. 10. - tmava plachta s ostny) -> vynechat, dokud neni lepsi model
VYNECH = {"Hair"}
for o in list(bpy.data.objects):
    if o.type == "MESH" and (o.name.startswith("Icosphere") or (o.data.materials and o.data.materials[0].name in VYNECH)):
        bpy.data.objects.remove(o)
celkem = 0
for o in [o for o in bpy.data.objects if o.type == "MESH"]:
    mat = o.data.materials[0].name if o.data.materials else ""
    n = sum(len(p.vertices) - 2 for p in o.data.polygons)
    # sedlo je ve dvou sitich - cil se deli podle podilu
    sedla = [x for x in bpy.data.objects if x.type == "MESH" and x.data.materials and x.data.materials[0].name == mat]
    podil = n / max(1, sum(sum(len(p.vertices) - 2 for p in x.data.polygons) for x in sedla))
    cil = int(CIL.get(mat, n) * podil)
    if n > cil:
        m = o.modifiers.new("dec", "DECIMATE")
        m.ratio = cil / n
        m.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="dec")
    n2 = sum(len(p.vertices) - 2 for p in o.data.polygons)
    celkem += n2
    print("KUN sit", o.name, mat, n, "->", n2)
    # textury materialu
    for nd in o.data.materials[0].node_tree.nodes if o.data.materials else []:
        if nd.type == "TEX_IMAGE" and nd.image is not None:
            px = TEX.get(mat, 1024)
            if nd.image.size[0] > px:
                nd.image.scale(px, px)
for a in bpy.data.actions:
    a.name = a.name.replace("Skeleton|", "").replace("_Object_9", "").replace("Ilde", "Idle").strip()
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=DST, export_format="GLB", use_selection=True, export_animations=True,
                          export_animation_mode="ACTIONS", export_image_format="JPEG", export_jpeg_quality=88)
print("KUN celkem troj.", celkem, "animaci", len(bpy.data.actions), sorted(a.name for a in bpy.data.actions))
