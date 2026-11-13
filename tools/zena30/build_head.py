import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import numpy as np, bmesh, face
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = imp(BASE)
arm = next(o for o in objs if o.type=='ARMATURE'); arm.name = "zena30_kostra"
body = next(o for o in objs if o.name.startswith("Superhero")); body.name = "zena30_telo"
eyes = next(o for o in objs if o.name.startswith("Eyes")); eyes.name = "zena30_oci"
brows = next(o for o in objs if o.name=="Eyebrows"); brows.name = "zena30_obocí"
print("shape keys", body.data.shape_keys and [k.name for k in body.data.shape_keys.key_blocks])
DO_FACE = int(os.environ.get("FACE", "1"))
if DO_FACE:
    for o in (body, eyes, brows): face.apply(o)
    # obočí: tenčí (komponenty s průměrem z > 1.67)
    bm = bmesh.new(); bm.from_mesh(brows.data); bm.verts.ensure_lookup_table()
    mw = brows.matrix_world; mi = mw.inverted()
    seen = set()
    for v in bm.verts:
        if v.index in seen: continue
        st=[v]; comp=[]; seen.add(v.index)
        while st:
            x=st.pop(); comp.append(x)
            for e in x.link_edges:
                y=e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        P = np.array([mw @ x.co for x in comp])
        if P[:,2].mean() < 1.668:   # řasy/linky: zkrátit vnější „křidélko“
            for x, p in zip(comp, P):
                q = p.copy(); ax = abs(p[0])
                if ax > 0.046:
                    k = 0.035 + (ax-0.046)*0.35
                    q[0] = np.sign(p[0])*(0.046 + (ax-0.046)*0.62); q[2] = 1.657 + (p[2]-1.657)*0.85
                    q[1] = p[1] + (ax-0.046)*0.15
                x.co = mi @ Vector(q)
            continue
        if P[:,2].mean() > 1.668:   # obočí
            c = P.mean(0)
            for x, p in zip(comp, P):
                q = p.copy(); q[2] = c[2] + (p[2]-c[2])*0.58
                # lehký oblouk: vnější část výš o kus, vnitřní konec níž
                ax = abs(p[0]); q[2] += 0.0025*np.sin(np.clip((ax-0.012)/0.05,0,1)*np.pi) - 0.0008
                x.co = mi @ Vector(q)
    bm.to_mesh(brows.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/z30/head.blend")

# ---------- textura kůže
import skin_tex
from PIL import Image, ImageFilter
TEXD = "/home/claude/z30/tex"; os.makedirs(TEXD, exist_ok=True)
BC = f"{UBC}/Base Characters"
src = np.asarray(Image.open(f"{BC}/T_Superhero_Female_Dark_BaseColor.png").convert("RGB")).astype(float)/255
S = src.shape[0]
mw = body.matrix_world
P = np.array([mw @ v.co for v in body.data.vertices])
def ell(c, r):
    d = (P - np.array(c)) / np.array(r); return np.clip(1 - np.sum(d*d, 1), 0, 1) ** 1.5
eye = np.maximum(ell((0.036, -0.064, 1.657), (0.03, 0.03, 0.02)), ell((-0.036, -0.064, 1.657), (0.03, 0.03, 0.02)))
nose = ell((0, -0.108, 1.613), (0.022, 0.03, 0.02))
blush = np.maximum(ell((0.05, -0.072, 1.603), (0.025, 0.03, 0.02)), ell((-0.05, -0.072, 1.603), (0.025, 0.03, 0.02)))
mE = skin_tex.raster_attr(body, eye, S); mN = skin_tex.raster_attr(body, nose, S); mB = skin_tex.raster_attr(body, blush, S)
def blur(a, r): return np.asarray(Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(float)/255
mE, mN, mB = blur(mE, 6), blur(mN, 6), blur(mB, 10)
skin = np.asarray(Image.fromarray((src*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28))).astype(float)/255
img = src.copy()
# oční stíny: zesvětlit k okolní kůži, zachovat detail (poměr k rozmazané verzi)
det = src / np.maximum(np.asarray(Image.fromarray((src*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))).astype(float)/255, 1e-3)
fixE = np.clip(skin * det**0.6, 0, 1)
img = img*(1-0.75*mE[...,None]) + fixE*(0.75*mE[...,None])
img = img*(1-0.55*mN[...,None]) + np.clip(skin*det**0.8,0,1)*(0.55*mN[...,None])
img = img + mB[...,None]*0.10*np.array([0.9, 0.25, 0.25]) - mB[...,None]*0.04
# celkově světlejší, růžovější pleť (střední Evropa)
lum = img.mean(2, keepdims=True)
img = img*1.10 + (img - lum)*(-0.12)
img = img * np.array([1.0, 0.97, 0.95]) + np.array([0.015, 0.01, 0.012])
Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8)).save(f"{TEXD}/zena30_kuze.png")

def set_tex(mat, path, cs="sRGB"):
    for n in mat.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image and "BaseColor" in n.image.name or (n.type=='TEX_IMAGE' and n.image and "Dark" in n.image.name):
            n.image = bpy.data.images.load(path); return
skm = body.data.materials[0]
for n in skm.node_tree.nodes:
    if n.type == 'TEX_IMAGE' and n.image and ("Dark" in n.image.name or "BaseColor" in n.image.name):
        n.image = bpy.data.images.load(f"{TEXD}/zena30_kuze.png")
skm.name = "zena30_kuze"
# obočí a řasy: tmavě hnědé (šedá textura × barva)
HAIRCOL = (0.055, 0.032, 0.02)
def tint(mat, col):
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    lk = bsdf.inputs['Base Color'].links
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type='RGBA'; mix.blend_type='MULTIPLY'; mix.inputs['Factor'].default_value = 1
    mix.inputs['B'].default_value = (*col, 1)
    if lk: nt.links.new(lk[0].from_socket, mix.inputs['A'])
    else: mix.inputs['A'].default_value = (1,1,1,1)
    nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
bm_ = brows.data.materials[0].copy(); bm_.name = "zena30_obocí"; brows.data.materials[0] = bm_
tint(bm_, tuple(c*2.2 for c in HAIRCOL))
# oči: oříškově zelené
em = eyes.data.materials[0]; em.name = "zena30_oci"
for n in em.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image and "Eye_Brown" in n.image.name:
        e = np.asarray(n.image.pixels[:]).reshape(n.image.size[1], n.image.size[0], 4)[..., :3] if False else None
ei = np.asarray(Image.open(f"{BC}/T_Eye_Brown.png").convert("RGB")).astype(float)/255
lum = ei.mean(2, keepdims=True); sat = np.abs(ei - lum).sum(2, keepdims=True)
iris = np.clip((sat-0.12)*8, 0, 1)
hz = np.clip(lum * np.array([0.95, 1.05, 0.7]) * 1.25, 0, 1)
ei2 = ei*(1-iris) + hz*iris
Image.fromarray((ei2*255).astype(np.uint8)).save(f"{TEXD}/zena30_oko.png")
for n in em.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image and "Eye_Brown" in n.image.name: n.image = bpy.data.images.load(f"{TEXD}/zena30_oko.png")
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/z30/head.blend")
