import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
setup_render((600,600), 12)
cam((0, -0.25, 1.95), (0, 0.0, 1.74), 60); render(f"{OUT}/top.png")
