import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import numpy as np, hair, tex_gen
from PIL import Image, ImageFilter
bpy.ops.wm.open_mainfile(filepath="/home/claude/z30/head.blend")
body = bpy.data.objects["zena30_telo"]; arm = bpy.data.objects["zena30_kostra"]
obj, tie = hair.build(body, arm)
print("vlasy troj.", sum(len(p.vertices)-2 for p in obj.data.polygons))
TEXD = "/home/claude/z30/tex"
HC = np.array([0.20, 0.105, 0.055])   # kaštanová (sRGB násobič)
a = tex_gen.hair_strands(512)
col = np.clip(a[..., None] * HC[None, None] * 1.6, 0, 1)
# řemínek (roh UV 0.02,0.98) – kůže
col[0:20, 0:20] = [0.25, 0.16, 0.09]
Image.fromarray((col * 255).astype(np.uint8)).save(f"{TEXD}/zena30_vlasy_barva.png")
Image.fromarray(tex_gen.to_normal(a, 3.0)).save(f"{TEXD}/zena30_vlasy_normal.png")
m = bpy.data.materials.new("zena30_vlasy"); m.use_nodes = True
nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(f"{TEXD}/zena30_vlasy_barva.png")
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(f"{TEXD}/zena30_vlasy_normal.png"); tn.image.colorspace_settings.name = "Non-Color"
nm = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(t.outputs[0], bs.inputs["Base Color"]); nt.links.new(tn.outputs[0], nm.inputs["Color"]); nt.links.new(nm.outputs[0], bs.inputs["Normal"])
bs.inputs["Roughness"].default_value = 0.55; bs.inputs["Specular IOR Level"].default_value = 0.25
obj.data.materials.append(m)
sh = hair.scalp_shell(body, obj, arm)
sh.data.materials.clear(); sh.data.materials.append(m)
print("pokryv troj.", sum(len(p.vertices)-2 for p in sh.data.polygons))
# obočí do stejného odstínu
# pokožka hlavy pod vlasy do barvy vlasů (měkký okraj)
import skin_tex
from mathutils.kdtree import KDTree
gi = obj.vertex_groups["Head"].index
hp = [obj.matrix_world @ v.co for v in obj.data.vertices if any(g.group == gi and g.weight > 0.99 for g in v.groups)]
kd = KDTree(len(hp))
for i, p_ in enumerate(hp): kd.insert(p_, i)
kd.balance()
att = np.zeros(len(body.data.vertices))
for v in body.data.vertices:
    co = body.matrix_world @ v.co
    if co.z < 1.57: continue
    d = kd.find(co)[2]; att[v.index] = np.clip((0.011 - d) / 0.009, 0, 1) * 0.85
skin = bpy.data.images.load(f"{TEXD}/zena30_kuze.png")
S = skin.size[0]
mk = skin_tex.raster_attr(body, att, S)
mk = np.asarray(Image.fromarray((mk*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7))).astype(float)/255
img = np.asarray(Image.open(f"{TEXD}/zena30_kuze.png").convert("RGB")).astype(float)/255
hc = HC * 1.2
img = img * (1 - mk[..., None]) + hc * mk[..., None]
Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8)).save(f"{TEXD}/zena30_kuze.png")
for im in bpy.data.images:
    if im.filepath.endswith("zena30_kuze.png"): im.reload()
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/z30/hair.blend")
