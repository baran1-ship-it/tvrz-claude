import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import anim_util, bmesh
from PIL import Image
bpy.ops.wm.open_mainfile(filepath="/home/claude/z30/final.blend")
arm = bpy.data.objects["zena30_kostra"]; acts = anim_util.load_actions()
anim_util.assign(arm, acts["Idle_Volne_1_Loop"], 20)
setup_render((520, 900), 20)
fl = bpy.data.objects.new("floor", bpy.data.meshes.new("floor")); bpy.context.scene.collection.objects.link(fl)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3); bm.to_mesh(fl.data)
ims = []
for loc, nm in (((0, -3.4, 1.0), "a"), ((2.3, -2.5, 1.05), "b"), ((0, 3.4, 1.0), "c")):
    cam(loc, (0, 0, 0.86), 50); render(f"/tmp/h_{nm}.png"); ims.append(Image.open(f"/tmp/h_{nm}.png").convert("RGB"))
bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 780, 900
cam((0.28, -0.62, 1.63), (0, 0, 1.585), 85); render("/tmp/h_f.png"); ims.append(Image.open("/tmp/h_f.png").convert("RGB"))
sheet = Image.new("RGB", (520 * 3 + 780, 900), "white")
x = 0
for im in ims: sheet.paste(im, (x, 0)); x += im.width
sheet.save("/home/claude/z30/out/nahled_blender.jpg", quality=90)
