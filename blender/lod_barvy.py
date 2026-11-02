"""Stredni LOD velkeho predmetu katalogu (stodola, kulna...; Misa 2. 11. sekani, manual: LOD pro staticke stavby, pocet
draw calls): vsechny site modelu jako jedna sit s jednim materialem, barva zapecena do barev vrcholu (jako
blender/ves_domy_lod.py - atlas pres smart_project u tisicu prken/sindelu cerny). Souradnice stejne jako vstupni glb.
  /opt/bl/bin/python -I blender/lod_barvy.py modely/predmety/stodola.glb [dalsi.glb ...]
Vystup vedle vstupu: <id>_stredni.glb (uzel <id>_Stredni). Hra: predmety.gd (modely.json predmety_lod)."""
import os
import sys

import bpy

for vstup in sys.argv[1:]:
    pid = os.path.splitext(os.path.basename(vstup))[0]
    vystup = os.path.join(os.path.dirname(vstup), pid + "_stredni.glb")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=vstup)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 1
    src = [o for o in bpy.data.objects if o.type == "MESH"]
    kopie = []
    for o in src:
        me = o.data.copy()
        me.transform(o.matrix_world)
        if me.uv_layers:
            me.uv_layers[0].name = "UVMap"
        c = bpy.data.objects.new(pid + "_s_" + o.name, me)
        sc.collection.objects.link(c)
        kopie.append(c)
    for o in src:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for c in kopie:
        c.select_set(True)
    bpy.context.view_layer.objects.active = kopie[0]
    if len(kopie) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = pid + "_Stredni"
    me = j.data
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[-1])
    me.uv_layers[0].active_render = True
    ca = me.color_attributes.new(name="Col", type="BYTE_COLOR", domain="CORNER")
    me.color_attributes.active_color = ca
    me.attributes.active_color = ca
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_clear=True, target="VERTEX_COLORS")
    me.materials.clear()
    mat = bpy.data.materials.new(pid + "_stredni")
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
        me.uv_layers.remove(me.uv_layers[0])
    bpy.ops.object.select_all(action="DESELECT")
    j.select_set(True)
    bpy.ops.export_scene.gltf(filepath=vystup, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                              export_materials="EXPORT", export_vertex_color="ACTIVE")
    print("STREDNI %s: %d troj, 1 material -> %s" % (pid, sum(len(p.vertices) - 2 for p in me.polygons), vystup))
