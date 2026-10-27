# Pouziti: /opt/bl/bin/python tools/ual_anim_jen.py <UAL1_Standard.glb z Disku Postavy/Universal Animation Library[Standard].zip> modely/postavy/anim/UAL1.glb
# Z knihovny UAL jen kostra a animace (bez figuriny a textur) -> mensi glb pro hru
import bpy, sys
src, dst = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in list(bpy.data.objects):
    if o.type == "MESH":
        bpy.data.objects.remove(o)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", use_selection=True, export_animations=True,
                          export_animation_mode="ACTIONS", export_force_sampling=True, export_skins=True, export_def_bones=False)
print("ANIM", dst, len(bpy.data.actions))
