import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import anim_util, bmesh
blend, tag = sys.argv[-2], sys.argv[-1]
SHOTS = [s.split(":") for s in os.environ["SHOTS"].split(",")]   # anim:frame:view
bpy.ops.wm.open_mainfile(filepath=blend)
arm = bpy.data.objects["zena30_kostra"]; acts = anim_util.load_actions()
setup_render((360, 600), int(os.environ.get("SAMPLES", "10")))
fl = bpy.data.objects.new("floor", bpy.data.meshes.new("floor")); bpy.context.scene.collection.objects.link(fl)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3); bm.to_mesh(fl.data)
VIEW = {"x": (-1.4, 1.0, 0.5), "w": (1.4, 0.0, 0.45), "z": (0.4, -1.6, 0.5), "y": (1.2, -1.2, 0.5), "a": (0, -3.4, 1.0), "b": (2.4, -2.4, 1.0), "c": (0, 3.4, 1.0), "d": (3.4, 0, 0.8), "e": (-2.4, -2.4, 1.0), "f": (-2.4, 2.4, 1.0)}
from PIL import Image, ImageDraw
ims = []
for an, fr, vw in SHOTS:
    anim_util.assign(arm, acts[an], int(fr))
    cam(VIEW[vw], (0, 0, 0.45) if vw in 'zyxw' else (0, 0, 0.8), 50); render(f"/tmp/_s.png")
    im = Image.open("/tmp/_s.png").convert("RGB"); ImageDraw.Draw(im).text((6, 6), f"{an} {fr}", fill=(0, 0, 0)); ims.append(im)
cols = min(len(ims), 5); rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (360 * cols, 600 * rows), "white")
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 360, (i // cols) * 600))
sheet.save(f"{OUT}/{tag}.jpg", quality=88)
