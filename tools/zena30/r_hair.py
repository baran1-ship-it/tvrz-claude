import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
blend, tag = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=blend)
setup_render((600,700), 16)
cam((0, -0.85, 1.64), (0, 0, 1.6), 70); render(f"{OUT}/{tag}_a.png")
cam((0.6, -0.6, 1.66), (0, 0, 1.6), 70); render(f"{OUT}/{tag}_b.png")
cam((0.5, 0.9, 1.5), (0, 0, 1.38), 50); render(f"{OUT}/{tag}_c.png")
