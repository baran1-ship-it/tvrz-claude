exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy
bpy.ops.wm.open_mainfile(filepath="/home/claude/chars/muz_base.blend")
for o in bpy.data.objects:
    print(o.name, o.type, len(o.data.vertices) if o.type=='MESH' else "", [m.type+":"+m.name for m in getattr(o,'modifiers',[])])
o = bpy.data.objects["muz"]
print([g.name for g in o.vertex_groups])
