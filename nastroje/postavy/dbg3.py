exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy
bpy.ops.wm.open_mainfile(filepath="/home/claude/chars/kluk_head.blend")
o = bpy.data.objects["kluk.high-poly"]
for m in o.data.materials:
    print("MAT", m.name)
    for n in m.node_tree.nodes:
        print("  ", n.type, n.name, getattr(getattr(n, "image", None), "filepath", ""))
