import sys, bpy
glb, out = sys.argv[1], sys.argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
o = [o for o in bpy.data.objects if o.type == 'MESH'][0]
bb = [o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box]
print("CHECK", o.name, "tris", sum(len(p.vertices) - 2 for p in o.data.polygons),
      "minZ %.3f" % min(v.z for v in bb), "center xy %.3f %.3f" % (sum(v.x for v in bb)/8, sum(v.y for v in bb)/8),
      "mats", [m.name for m in o.data.materials],
      "imgs", [(i.name, i.size[0]) for i in bpy.data.images])
o.name = "game_rock"
bpy.ops.wm.save_as_mainfile(filepath=out)
