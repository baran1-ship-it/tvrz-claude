import bpy, os
HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.read_factory_settings(use_empty=True)
names = ["trava_vysoka_1", "trava_vysoka_2", "trava_vysoka_3", "trava_nizka_1", "trava_nizka_2", "trava_nizka_3"]
mat = None
for i, n in enumerate(names):
    with bpy.data.libraries.load(os.path.join(HERE, f"{n}.blend")) as (src, dst):
        dst.objects = [n]
    o = dst.objects[0]; bpy.context.collection.objects.link(o)
    if mat is None:
        mat = o.data.materials[0]; mat.name = "game_trava_sada"
    o.data.materials[0] = mat
    o.location = (i * 1.5, 0, 0)       # jen pro přehled; v Godotu se trsy použijí jednotlivě
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, "out", "trava_sada.glb"), export_format='GLB', use_selection=True,
                          export_yup=True, export_apply=False, export_cameras=False, export_lights=False)
print("SET ok", len(bpy.data.images))
