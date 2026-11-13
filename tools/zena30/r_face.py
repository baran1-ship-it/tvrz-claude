import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import anim_util
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); tag = sys.argv[-1]
arm = bpy.data.objects["zena30_kostra"]
setup_render((700, 800), 16)
cam((0.0, -0.75, 1.64), (0, 0, 1.6), 85); render(f"{OUT}/{tag}_a.png")
cam((0.5, -0.55, 1.66), (0, 0, 1.6), 85); render(f"{OUT}/{tag}_b.png")
