"""Postaví jednu tvář: python3 tvar.py -- <id> [render]
Čte specifikaci z tvare_spec.json, výstup: out/<id>.glb, out/<id>_pred.png, out/<id>_profil.png, out/<id>_data.json"""
import sys, os, json, math; sys.path.insert(0, "/home/claude/z30/scripts"); sys.path.insert(0, "/home/claude/tv/scripts")
from common import imp, UBC, setup_render, cam, render
import bpy, bmesh, numpy as np
from mathutils import Vector, Quaternion
import lmk, face2, skin2, hair2, cloth, q_oci, tex_gen
from PIL import Image
ID = sys.argv[sys.argv.index("--") + 1]; DO_R = "render" in sys.argv
SPEC = json.load(open("/home/claude/tv/scripts/tvare_spec.json"))[ID]
OUT = "/home/claude/tv/out"; TEX = f"{OUT}/tex"; os.makedirs(TEX, exist_ok=True)
rng = np.random.default_rng(SPEC.get("seed", 1))
SEX = SPEC["pohlavi"]
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = imp(f"{UBC}/Base Characters/Superhero_{SEX}_FullBody.gltf")
arm = next(o for o in objs if o.type == 'ARMATURE'); arm.name = "Armature"
body = next(o for o in objs if o.type == 'MESH' and "superhero" in o.name.lower()); body.name = f"{ID}_telo"
eyes = next(o for o in objs if o.name.startswith("Eyes")); eyes.name = f"{ID}_oci"
brows = next(o for o in objs if o.name.startswith("Eyebrows")); brows.name = f"{ID}_oboci"
L0 = lmk.landmarks(body, eyes)
OPS = face2.build_ops(L0, SPEC["tvar"])
for o in (body, eyes, brows): face2.apply(o, OPS)
L = lmk.landmarks(body, eyes)
zE, zN = float(L["eye"][2]), float(L["nose"][2])
# ---- obočí: tloušťka, výška, sklon
bt, bz, btilt = SPEC.get("oboci", [1.0, 0.0, 0.0])
bm = bmesh.new(); bm.from_mesh(brows.data); mw = brows.matrix_world; mi = mw.inverted()
seen = set(); lash_mask = np.zeros(len(bm.verts), bool); bm.verts.ensure_lookup_table()
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; comp = []; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    Pc = np.array([mw @ x.co for x in comp])
    if Pc[:, 2].mean() < zE + 0.012:
        for x in comp: lash_mask[x.index] = True
        continue
    c = Pc.mean(0)
    for x, p in zip(comp, Pc):
        q = p.copy(); q[2] = c[2] + (p[2] - c[2]) * bt + bz + btilt * (abs(p[0]) - 0.035)
        x.co = mi @ Vector(q)
bm.to_mesh(brows.data); bm.free()
# ---- barvy
HC = np.array(SPEC["vlasy"]["barva"]); grey = SPEC["vlasy"].get("sedive", 0.0)
HC = HC * (1 - grey) + np.array([0.40, 0.385, 0.37]) * grey
def mat_col(name, col, rough=0.6, tex=None, normal=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    if tex:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(tex)
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1
        mix.inputs['B'].default_value = (*[c ** 2.2 for c in col], 1)
        nt.links.new(t.outputs[0], mix.inputs['A']); nt.links.new(mix.outputs['Result'], bs.inputs['Base Color'])
    else: bs.inputs['Base Color'].default_value = (*[c ** 2.2 for c in col], 1)
    if normal:
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(normal); tn.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(tn.outputs[0], nm.inputs['Color']); nt.links.new(nm.outputs[0], bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value = rough; bs.inputs['Specular IOR Level'].default_value = 0.25
    return m
if not os.path.exists(f"{TEX}/prameny.png"):
    a = tex_gen.hair_strands(256, 3)
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGB").save(f"{TEX}/prameny.png")
    Image.fromarray(tex_gen.to_normal(a, 2.5)).save(f"{TEX}/prameny_n.png")
M_HAIR = mat_col(f"{ID}_vlasy", HC * 1.05, 0.55, f"{TEX}/prameny.png", f"{TEX}/prameny_n.png")
bcol = HC * (0.75 if grey < 0.5 else 1.0)
M_BROW = mat_col(f"{ID}_oboci", bcol * 2.0, 0.6, f"{UBC}/Hairstyles/Rigged/T_Hair_2_BaseColor.png")
brows.data.materials.clear(); brows.data.materials.append(M_BROW)
# oči
ei = np.asarray(Image.open(f"{UBC}/Base Characters/T_Eye_Brown.png").convert("RGB")).astype(float) / 255
lum = ei.mean(2, keepdims=True); sat = np.abs(ei - lum).sum(2, keepdims=True); iris = np.clip((sat - 0.12) * 8, 0, 1)
ic = np.array(SPEC.get("oci", [0.55, 0.38, 0.2]))
ei2 = ei * (1 - iris) + np.clip(lum * ic * 2.2, 0, 1) * iris
Image.fromarray((ei2 * 255).astype(np.uint8)).save(f"{TEX}/{ID}_oko.png")
em = eyes.data.materials[0]; em.name = f"{ID}_oci"
for n in em.node_tree.nodes:
    if n.type == 'TEX_IMAGE' and n.image and "Eye_Brown" in n.image.name: n.image = bpy.data.images.load(f"{TEX}/{ID}_oko.png")
# ---- vlasy
HS = SPEC["vlasy"]
parts = []
lin = dict(HS.get("linie", {}))
if SEX == "Male": lin.setdefault("kouty", 0.008); lin.setdefault("nad_usima", 0.004); lin.setdefault("predni", 0.062)
fnH = hair2.hairline_fn(L, lin)
def off_fn(c, o):
    edge = max(0.0, min(1.0, fnH(c) / 0.02))          # k okraji se čepice přitiskne k hlavě
    return (o + HS.get("objem", 0.0) * max(0.0, min(1.0, (c[2] - (zE - 0.02)) / 0.08))) * edge
cap = hair2.shell(body, L, fnH, HS.get("cepice", 0.006), f"{ID}_cepice", off_fn=off_fn, lip=0.0015)
parts.append(cap)
bmc = hair2.flow_clumps(body, L, fnH, HS.get("chomacu", 8), HS.get("delka_chomacu", 0.10), HS.get("cepice", 0.006) + HS.get("objem", 0) * 0.8,
                        HS.get("sirka_chomacu", 0.035), rng, droop=HS.get("pad", 0.0), flow_mode=[HS.get("smer", "temeno")])
parts.append(hair2.to_object(bmc, f"{ID}_chomace"))
zC = float(L["chin"][2]); yc = hair2.head_frame(L)[1]
def lobes(bm, centers, radii, tilt, segs=4, ringn=6):
    for c, r, s in zip(centers, radii, tilt):
        q = Quaternion((0, 1, 0), s)
        rings = []
        for a in range(segs + 1):
            u = a / segs; zz = (u - 0.5) * r[2] * 2
            rr = math.sin(math.pi * u) ** 0.7 + 0.05
            rings.append([bm.verts.new(Vector(c) + q @ Vector((math.cos(2 * math.pi * b / ringn) * r[0] * rr, math.sin(2 * math.pi * b / ringn) * r[1] * rr, zz))) for b in range(ringn)])
        for a in range(segs):
            for b in range(ringn):
                bm.faces.new((rings[a][b], rings[a][(b + 1) % ringn], rings[a + 1][(b + 1) % ringn], rings[a + 1][b]))
def back_y(z):
    co = L["V"]; m = (np.abs(co[:, 0]) < 0.03) & (np.abs(co[:, 2] - z) < 0.012)
    return float(co[m, 1].max()) if m.any() else L["back_y"]
extra = HS.get("doplnek")
if extra == "drdol":
    bm = bmesh.new(); yb = L["back_y"] + 0.012; z0 = zE - 0.005 + HS.get("drdol_z", 0.0)
    lobes(bm, [(0, yb + 0.012, z0), (0.018, yb, z0 - 0.004), (-0.018, yb, z0 - 0.004)], [(0.028, 0.022, 0.026), (0.02, 0.018, 0.022), (0.02, 0.018, 0.022)], [0, 0.6, -0.6], 5, 7)
    parts.append(hair2.to_object(bm, f"{ID}_drdol"))
elif extra == "cop":
    bm = bmesh.new(); n = HS.get("cop_laloku", 10); z0 = zE - 0.075; z1 = z0 - HS.get("cop_delka", 0.40)
    cs, rs, ts = [], [], []
    for i in range(n):
        for sd in (1, -1):
            z = z0 - (z0 - z1) * (i + (0.5 if sd < 0 else 0)) / n; r = 0.018 * (1 - 0.4 * i / n) + 0.004
            cs.append((sd * r * 0.4, back_y(z) + 0.028, z)); rs.append((r, r * 0.8, (z0 - z1) / n * 0.65)); ts.append(sd * 0.55)
    lobes(bm, cs, rs, ts, 4, 6)
    parts.append(hair2.to_object(bm, f"{ID}_cop"))
elif extra == "dlouhe":
    bm = bmesh.new(); n = HS.get("pramenu", 7); dl = HS.get("dlouhe_delka", 0.22)
    Vb = L["V"]
    def surf_r(a, z):
        """vzdálenost povrchu (hlava/krk/záda) od osy v azimutu a ve výšce z"""
        m = np.abs(Vb[:, 2] - z) < 0.012
        Q = Vb[m]; d = np.stack([Q[:, 0], Q[:, 1] - yc], 1)
        u = np.array([math.sin(a), -math.cos(a)]); pr = d @ u
        side = np.abs(d @ np.array([u[1], -u[0]])) < 0.025
        return float(pr[side].max()) if side.any() else 0.06
    for i in range(n):
        a = math.pi + (-1.1 + 2.2 * i / (n - 1))
        pts, nrm = [], []
        for k in range(7):
            z = zE + 0.02 - dl * k / 6
            zz = max(z, zE - 0.10)
            r = max(surf_r(a, zz), surf_r(a, zz + 0.03), surf_r(a, zE) * 0.92) + 0.010 + 0.002 * k
            if z < zE - 0.10 and abs(math.sin(a)) < 0.7: r = max(r, back_y(z) - yc + 0.02) if math.cos(a) < 0 else r
            pts.append(Vector((math.sin(a) * r, yc - math.cos(a) * r, z))); nrm.append(Vector((math.sin(a), -math.cos(a), 0)))
        hair2.ribbon(bm, pts, nrm, [0.05 - 0.02 * k / 6 for k in range(7)], [0.010] * 7, 4)
    parts.append(hair2.to_object(bm, f"{ID}_dlouhe"))
# vousy
B = SPEC.get("vousy")
fnB = None
if B and B.get("typ") not in (None, "strniste"):
    fnB = hair2.beard_fn(L, B)
    ln = B.get("delka", 0.008)
    def boff(c, o):
        edge = max(0.1, min(1.0, fnB(c) / 0.012))
        return (o + ln * max(0.0, min(1.0, (zC + 0.02 - c[2]) / 0.03))) * edge
    bs = hair2.shell(body, L, fnB, B.get("tloustka", 0.004), f"{ID}_vousy", off_fn=boff, smooth=2, lip=0.002)
    parts.append(bs)
elif B: fnB = hair2.beard_fn(L, dict(B, typ="plny"))
# spojit vlasy + vousy do jedné sítě, váhy
print('CASTI', [(p.name, sum(len(f.vertices)-2 for f in p.data.polygons)) for p in parts])
for p in parts:
    if p.name not in bpy.context.scene.collection.objects: bpy.context.scene.collection.objects.link(p)
bpy.ops.object.select_all(action='DESELECT')
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
hair = bpy.context.view_layer.objects.active; hair.name = f"{ID}_vlasy"
for m in list(hair.modifiers): hair.modifiers.remove(m)
hair.vertex_groups.clear()
for p in hair.data.polygons: p.use_smooth = True
hair.data.materials.clear(); hair.data.materials.append(M_HAIR)
print("CASTI", [(p.name, len(p.data.polygons)) for p in parts] if False else "")
hair2.strand_uv(hair, L)
bones = arm.data.bones
zNk = (arm.matrix_world @ bones["neck_01"].head_local).z; zH = (arm.matrix_world @ bones["Head"].head_local).z
gH = hair.vertex_groups.new(name="Head"); gN = hair.vertex_groups.new(name="neck_01"); g3 = hair.vertex_groups.new(name="spine_03")
for v in hair.data.vertices:
    z = (hair.matrix_world @ v.co).z
    if z >= zH - 0.01: gH.add([v.index], 1, 'REPLACE')
    elif z >= zNk: a = (z - zNk) / max(zH - 0.01 - zNk, 1e-3); gH.add([v.index], 0.5 + 0.5 * a, 'REPLACE'); gN.add([v.index], 0.5 - 0.5 * a, 'REPLACE')
    else:
        a = min(1, (zNk - z) / 0.12); gN.add([v.index], 1 - a, 'REPLACE'); g3.add([v.index], a, 'REPLACE')
hair.parent = arm; md = hair.modifiers.new("Armature", 'ARMATURE'); md.object = arm
hair_tris = sum(len(p.vertices) - 2 for p in hair.data.polygons)
BUD = 1450
if hair_tris > BUD:
    dm = hair.modifiers.new("dec", 'DECIMATE'); dm.ratio = BUD / hair_tris
    hair.modifiers.move(hair.modifiers.find("dec"), 0)
    with bpy.context.temp_override(object=hair, active_object=hair): bpy.ops.object.modifier_apply(modifier="dec")
    hair_tris = sum(len(p.vertices) - 2 for p in hair.data.polygons)
# ---- pleť 512
P, Mk = skin2.posmap(body, 512)
src = f"{UBC}/Base Characters/" + ("T_Superhero_Female_Dark_BaseColor.png" if SEX == "Female" else "T_Superhero_Male_Dark.png")
sp = dict(SPEC["plet"]); sp["vlasy_barva"] = list(HC * 0.9)
img = skin2.make(src, P, Mk, L, sp, hair_fn=fnH, beard_fn=fnB, S=512, rng=rng)
Image.fromarray((img * 255).astype(np.uint8)).save(f"{TEX}/{ID}_kuze.png")
skm = body.data.materials[0]; skm.name = f"{ID}_kuze"
for n in skm.node_tree.nodes:
    if n.type == 'TEX_IMAGE' and n.image and ("Dark" in n.image.name or "BaseColor" in n.image.name):
        n.image = bpy.data.images.load(f"{TEX}/{ID}_kuze.png")
# ---- mrkání
q_oci.add_blink(body, brows, eyes, lash_mask)
json.dump(dict(id=ID, pohlavi=SEX, vek=SPEC.get("vek_let"), role=SPEC.get("role"), posuvniky=SPEC["tvar"], OPS=[[list(map(float, c)), float(r), (list(d) if d[0] != "scale" else ["scale", float(d[1])])] for c, r, d in OPS],
               plet=SPEC["plet"], vlasy=SPEC["vlasy"], vousy=SPEC.get("vousy"), oboci=SPEC.get("oboci"), oci=SPEC.get("oci"),
               trojuhelniky_vlasy_vousy=hair_tris), open(f"{OUT}/{ID}_data.json", "w"), ensure_ascii=False, indent=1)
print("VLASY_TROJ", ID, hair_tris)
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/{ID}.blend")
for o in bpy.data.objects: o.select_set(o.type in ('MESH', 'ARMATURE'))
bpy.ops.export_scene.gltf(filepath=f"{OUT}/{ID}.glb", export_format='GLB', use_selection=True, export_yup=True, export_animations=False, export_skins=True)
if DO_R:
    setup_render((380, 440), 12)
    top = float(L["top"][2]); zc = (top + zC) / 2 - 0.01
    cam((0, -0.85, zc + 0.01), (0, 0, zc), 85, "c1"); render(f"{OUT}/{ID}_pred.png")
    cam((0.85, -0.08, zc + 0.01), (0, 0.0, zc), 85, "c2"); render(f"{OUT}/{ID}_profil.png")
