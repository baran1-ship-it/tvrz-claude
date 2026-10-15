exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy, sys, numpy as np
sys.path.insert(0, "/home/claude/chars")
import head_features as hf
bpy.ops.wm.open_mainfile(filepath="/home/claude/chars/muz_base.blend")
o = bpy.data.objects["muz"]
co, no = hf.evaluated_coords(o)
body = hf.group_weights(o, "body"); ears = hf.group_weights(o, "ears")
head = co[:, 2] > 1.6
for nm, m in (("head", head), ("head&body", head & (body > 0.5)), ("x<0", head & (body > 0.5) & (co[:, 0] < 0)), ("x>0", head & (body > 0.5) & (co[:, 0] > 0))):
    print(nm, m.sum())
print("groups with Left/Right:", [g.name for g in o.vertex_groups][:6])
L = hf.group_weights(o, "Left"); R = hf.group_weights(o, "Right")
print("Left head", (head & (L > 0.5)).sum(), "Right head", (head & (R > 0.5)).sum())
