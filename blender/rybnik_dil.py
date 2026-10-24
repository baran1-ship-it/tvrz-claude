"""Navesni rybnik Lhota (Misa 24. 10.): Disk rybnik_lhota_v3.zip (id 1eSRPpTJKsxGsWVZNzkUEy-YrS_bEA-Wt) -> rybnik.glb.
Stazeni: curl -sSL -o rybnik_lhota_v3.zip "https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t"
Uprava pro hru: teren a hladina dostanou material hry (zem.gdshader, voda.gdshader) - vlastni textury terenu pryc
(3 x 2048 nad rozpocet tabletu), barvy vrcholu zachovat (R = hloubka x 4 / stanoviste), roughness na 512.
  /opt/bl/bin/python -I rybnik_dil.py -- <rozbaleny>/rybnik.glb ../modely/rybnik/rybnik.glb"""
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[-2])
# teren a voda dostanou material hry (zem.gdshader / voda.gdshader) - vlastni textury pryc (3 x 2048 = rozpocet tabletu)
for o in bpy.context.scene.objects:
    if o.type == "MESH" and o.name in ("Rybnik_Teren-col", "Rybnik_Voda"):
        for i, m in enumerate(o.data.materials):
            nm = bpy.data.materials.new("hra_" + o.name.split("-")[0])
            o.data.materials[i] = nm
for im in list(bpy.data.images):
    if im.name.startswith("teren_") or im.users == 0:
        bpy.data.images.remove(im)
for im in bpy.data.images:
    if im.size[0] > 512 and ("rough" in im.name):
        im.scale(512, 512)
bpy.ops.export_scene.gltf(filepath=sys.argv[-1], export_format="GLB", export_apply=True, export_yup=True, export_image_format="AUTO", export_vertex_color="ACTIVE", export_all_vertex_colors=True)
