import sys
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy, importlib
sys.path.insert(0, "/home/claude/chars")
import skin_mat, head_features
NAME = sys.argv[1]
P = {
 "muz":  dict(tone=(0.40, 0.235, 0.155), freckles=0.0, stubble=0.7, age=0.6, ruddy=0.5, brow=(0.075, 0.055, 0.04),
              hair="muz", hcol=(0.065, 0.045, 0.032)),
 "kluk": dict(tone=(0.55, 0.33, 0.24), freckles=0.8, stubble=0.0, age=0.1, ruddy=0.35, brow=(0.34, 0.15, 0.06),
              hair="kluk", hcol=(0.30, 0.10, 0.04)),
}[NAME]
bpy.ops.wm.open_mainfile(filepath=f"/home/claude/chars/{NAME}_base.blend")
body = bpy.data.objects[NAME]
L = head_features.landmarks(body)
print("LANDMARKS", {k: tuple(round(x, 3) for x in v) for k, v in L.items() if hasattr(v, "x")})
skin_mat.apply(body, tone=P["tone"], freckles=P["freckles"], stubble=P["stubble"], age=P["age"], ruddy=P["ruddy"],
               L=L, brow_col=P["brow"])
hair = head_features.hair_shell(body, L, P["hair"], P["hcol"], name=f"{NAME}_vlasy")
print("HAIR", len(hair.data.polygons))
eyes = bpy.data.objects.get(f"{NAME}.high-poly")
if eyes:
    img = bpy.data.images.load(f"/home/claude/chars/eye_{NAME}.png")
    for m in eyes.data.materials:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.name == "DiffuseTexture": n.image = img
bpy.ops.wm.save_as_mainfile(filepath=f"/home/claude/chars/{NAME}_head.blend")
