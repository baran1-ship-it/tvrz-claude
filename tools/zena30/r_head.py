import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
blend, tag = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=blend)
setup_render((700,800), 20)
H = 1.62
cam((0, -0.72, 1.64), (0, 0, 1.615), 85); render(f"{OUT}/{tag}_a.png")
cam((0.45, -0.58, 1.64), (0, 0, 1.615), 85); render(f"{OUT}/{tag}_b.png")
