"""Stredni LOD domu vsi (Misa 2. 11. „a co to sekani, pouzil jsi rady z manualu?“ - manual: LOD pro staticke stavby,
pocet draw calls, ne jen trojuhelniky; mereni 0996 ves_cesta 1133 kresleni, bez staveb -466).
Podrobny vnejsek domu ma 21-25 povrchu (material = 1 kresleni), hruby _Daleko je obal se 2 barvami (Misa 0.83 „hneda
krabice“). Mezi ne: _Stredni = vnejsek + drobne jako jedna sit s jednim materialem, barva zapecena z puvodnich textur
do barev vrcholu (Cycles bake DIFFUSE/COLOR, target VERTEX_COLORS). Geometrie stejna (sindel po sindeli - decimace dela diry).
Vstup modely/ves/domy.glb (blender/ves_domy.py), vystup modely/ves/domy_stredni.glb (jen uzly <koren>_Stredni v ramci
korene, stejne jako puvodni uzly). Puvodni domy.glb se nemeni.
  /opt/bl/bin/python -I blender/ves_domy_lod.py modely/ves/domy.glb modely/ves/domy_stredni.glb"""
import math
import sys

import bpy

KORENY = ["Dum1", "Dum2", "Rychta", "ChyseKura", "ChysePrkna"]
CASTI = ("Vnejsek", "Drobne")
vstup, vystup = sys.argv[1], sys.argv[2]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=vstup)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 1
sc.render.bake.margin = 4

hotove = []
for koren in KORENY:
    src = [o for o in bpy.data.objects if o.type == "MESH" and o.name.split(".")[0] in [koren + "_" + c for c in CASTI]]
    if not src:
        print("STREDNI %s: chybi vnejsek" % koren)
        continue
    root = bpy.data.objects.get(koren)
    inv = root.matrix_world.inverted() if root else None
    kopie = []
    for o in src:
        me = o.data.copy()
        me.transform(o.matrix_world if inv is None else inv @ o.matrix_world)
        c = bpy.data.objects.new(koren + "_s_" + o.name, me)
        sc.collection.objects.link(c)
        # prvni UV vrstva se jmenuje stejne (jinak join rozdeli UV do dvou vrstev - predmety._uv_jednotne)
        if me.uv_layers:
            me.uv_layers[0].name = "UVMap"
        kopie.append(c)
    bpy.ops.object.select_all(action="DESELECT")
    for c in kopie:
        c.select_set(True)
    bpy.context.view_layer.objects.active = kopie[0]
    if len(kopie) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = koren + "_Stredni"
    me = j.data
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[-1])
    me.uv_layers[0].active_render = True
    # barva do barev vrcholu (atlas pres smart_project: tisice sindelu = drobne ostruvky, atlas skoro cerny -
    # zkouska 2. 11.); sit je husta (sindel po sindeli, tram po tramu), z 30 m a dal barva vrcholu staci
    ca = me.color_attributes.new(name="Col", type="BYTE_COLOR", domain="CORNER")
    me.color_attributes.active_color = ca
    me.attributes.active_color = ca
    bpy.ops.object.select_all(action="DESELECT")
    j.select_set(True)
    bpy.context.view_layer.objects.active = j
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_clear=True, target="VERTEX_COLORS")
    me.materials.clear()
    mat = bpy.data.materials.new(koren + "_stredni")
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get("Principled BSDF")
    vc = mat.node_tree.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    mat.node_tree.links.new(vc.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.9
    me.materials.append(mat)
    for p in me.polygons:
        p.material_index = 0
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])            # bez textury - UV jen zvetsuje soubor
    j.parent = None
    j.matrix_world.identity()
    hotove.append(j)
    print("STREDNI %s: %d troj, 1 material, barva vrcholu" % (koren, sum(len(p.vertices) - 2 for p in me.polygons)))

bpy.ops.object.select_all(action="DESELECT")
for j in hotove:
    j.select_set(True)
bpy.ops.export_scene.gltf(filepath=vystup, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                          export_materials="EXPORT", export_vertex_color="ACTIVE")
print("STREDNI hotovo %d domu -> %s" % (len(hotove), vystup))
