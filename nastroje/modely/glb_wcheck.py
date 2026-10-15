import sys, bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[1])
ms = [o for o in bpy.data.objects if o.type == 'MESH']
print("CHECK", [(o.name, len(o.data.polygons)) for o in ms], [(i.name, i.size[0]) for i in bpy.data.images])
ms[0].name = "wagon"
for o in ms[1:]:
    o.name = "plachta"
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[2])
