import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = imp(BASE); objs += imp(f"{HAIR}/Hair_Long.gltf")
zs=[ (o.matrix_world @ v.co).z for o in objs if o.type=='MESH' and o.name.startswith('Super') for v in o.data.vertices]
print("height", max(zs), min(zs))
arm = next(o for o in objs if o.type=='ARMATURE')
print("Head", arm.matrix_world @ arm.data.bones['Head'].head_local)
setup_render((800,800), 20)
H = max(zs)
cam((0, -0.75, H-0.1), (0, 0, H-0.12), 85); render(f"{OUT}/base_face.png")
cam((0.5, -0.6, H-0.1), (0, 0, H-0.12), 85); render(f"{OUT}/base_face34.png")
