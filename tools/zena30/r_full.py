import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import anim_util
blend, tag, anim, frame = sys.argv[-4:]
bpy.ops.wm.open_mainfile(filepath=blend)
arm = bpy.data.objects["zena30_kostra"]
acts = anim_util.load_actions()
if anim != "-":
    a = next((acts[k] for k in acts if k == anim), None) or next(acts[k] for k in acts if anim.lower() in k.lower())
    print("ANIM", a.name, a.frame_range)
    anim_util.assign(arm, a, frame)
setup_render((500, 900), 16)
fl = bpy.data.objects.new("floor", bpy.data.meshes.new("floor")); bpy.context.scene.collection.objects.link(fl)
import bmesh; bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3); bm.to_mesh(fl.data)
VIEWS = [((0, -3.4, 1.0), "a"), ((2.4, -2.4, 1.0), "b"), ((0, 3.4, 1.0), "c"), ((3.4, 0, 0.6), "d")]
for i, (loc, nm) in enumerate([v for v in VIEWS if v[1] in os.environ.get("V", "abc")]):
    cam(loc, (0, 0, 0.88), 50, "c" + nm); render(f"{OUT}/{tag}_{nm}.png")
