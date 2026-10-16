"""Hrdina z Quaternius (CC0): oblečení + hlava základní postavy upravená podle fotek, vlasy, textury.
python3 q_postava.py <muz|zena|kluk> <vystup.jpg> [ANIM=Idle_Loop]
Výstup: <vystup>.jpg (celek + tvář zepředu + tvář z 3/4), <vystup>.blend
"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector
from PIL import Image, ImageFilter
NAME, OUT = sys.argv[sys.argv.index("--") + 1:][:2]
Q = "/home/claude/dl/quat/quaternius"
BD = f"{Q}/base_characters/Base Characters/Godot - UE"
OD = f"{Q}/outfits/Exports/glTF (Godot-Unreal)"
HD = f"{Q}/base_characters/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)"
UAL = "/home/claude/dl/ual1/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb"
TEXOUT = f"/home/claude/chars/q/tex_{NAME}"; os.makedirs(TEXOUT, exist_ok=True)
CFG = json.load(open("/home/claude/chars/q/postavy.json"))[NAME]
SEX = CFG["sex"]

bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p):
    b = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    keep = []
    for o in [o for o in bpy.data.objects if o not in b]:
        if o.type == 'MESH' and o.name.startswith("Icosphere"): bpy.data.objects.remove(o)
        else: keep.append(o)
    return keep

# --- oblečení (vlastní kostra = kostra postavy)
if CFG.get("parts"):
    outfit = []; arm = None
    for pn in CFG["parts"]:
        objs = imp(f"{OD}/Modular Parts/{SEX}_{pn}.gltf")
        a_ = next(o for o in objs if o.type == 'ARMATURE')
        if arm is None: arm = a_; outfit += objs; continue
        for o in objs:
            if o.type == 'MESH':
                mw = o.matrix_world.copy(); o.parent = arm; o.matrix_world = mw
                for m in o.modifiers:
                    if m.type == 'ARMATURE': m.object = arm
                outfit.append(o)
        bpy.data.objects.remove(a_)
else:
    outfit = imp(f"{OD}/Outfits/{SEX}_{CFG['outfit']}.gltf")
    arm = next(o for o in outfit if o.type == 'ARMATURE')
arm.name = f"{NAME}_kostra"
for o in outfit:
    if o.type == 'MESH': o.name = f"{NAME}_{o.name.split('_')[-1].lower()}"
# --- hlava ze základní postavy
base = imp(f"{BD}/Superhero_{SEX}_FullBody.gltf")
barm = next(o for o in base if o.type == 'ARMATURE')
NZ = (barm.matrix_world @ barm.data.bones['neck_01'].head_local).z
head = eyes = brows = None
for o in base:
    if o.type != 'MESH': continue
    n = o.name.lower()
    if n.startswith("superhero"): head = o
    elif n.startswith("eyes"): eyes = o
    elif n.startswith("eyebrows"): brows = o
gi = {g.index: g.name for g in head.vertex_groups}
bm = bmesh.new(); bm.from_mesh(head.data); dl = bm.verts.layers.deform.active; kill = []
for v in bm.verts:
    w = sum(wt for g, wt in v[dl].items() if gi[g] in ("Head", "neck_01", "neck_02"))
    w2 = sum(wt for g, wt in v[dl].items() if gi[g] in ("spine_03", "clavicle_l", "clavicle_r"))
    pw = head.matrix_world @ v.co
    chest = w + w2 > 0.5 and pw.z > NZ - 0.12 and abs(pw.x) < 0.045 and pw.y < -0.02
    if w < 0.5 and not (w + w2 > 0.5 and pw.z > NZ - 0.035) and not chest: kill.append(v)
bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(head.data); bm.free()
head.name = f"{NAME}_hlava"; eyes.name = f"{NAME}_oci"; brows.name = f"{NAME}_oboci"
def rebind(o, bone_parent=False):
    mw = o.matrix_world.copy()
    if bone_parent:
        o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = "Head"
    else:
        o.parent = arm
        for m in o.modifiers:
            if m.type == 'ARMATURE': m.object = arm
    bpy.context.view_layer.update(); o.matrix_world = mw
for o in (head, eyes, brows): rebind(o)
bpy.data.objects.remove(barm)
# --- vlasy (+ vousy)
hairs = []
for hn in CFG["hair"]:
    for o in imp(f"{HD}/{hn}.gltf"):
        if o.type == 'ARMATURE':
            for c in list(o.children):
                rebind(c, bone_parent=not any(m.type == 'ARMATURE' for m in c.modifiers))
                c.name = f"{NAME}_{hn.lower()}"; hairs.append(c)
            bpy.data.objects.remove(o)
        elif o.type == 'MESH' and o.parent is None:
            rebind(o, bone_parent=True); o.name = f"{NAME}_{hn.lower()}"; hairs.append(o)

# --- tvar obličeje (klidová poloha, světové souřadnice; jen hlava, obočí, vlasy)
ec = np.array([eyes.matrix_world @ v.co for v in eyes.data.vertices])
E = ec.mean(0)                                  # střed mezi očima
EX = np.abs(ec[:, 0]).mean()                    # půlvzdálenost očí
YF = ec[:, 1].min()                             # přední plocha očí
F = CFG["face"]
def ss(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def gauss(p, c, r): return np.exp(-np.sum(((p - c) / r) ** 2, axis=1))
def deform(P):
    x, y, z = P[:, 0].copy(), P[:, 1].copy(), P[:, 2].copy()
    front = ss((E[1] + 0.075 - y) / 0.05)                         # přední polovina hlavy
    low = ss((E[2] - 0.025 - z) / 0.07) * ss((z - (E[2] - 0.20)) / 0.04)   # pod lícními kostmi, nad krkem
    # čelist / brada užší, obličej delší
    x = x * (1 - F.get("jaw_x", 0) * low * front)
    z = z - F.get("face_len", 0) * ss((E[2] - 0.04 - z) / 0.09) * front * ss((z - (E[2] - 0.22)) / 0.05)
    # lícní kosti
    cb = gauss(np.abs(P), np.array([EX + 0.012, abs(E[1] - 0.005), E[2] - 0.022]), np.array([0.022, 0.03, 0.018]))
    x = x * (1 + F.get("cheekbone", 0) * cb)
    # propadlé / plné tváře
    ch = gauss(np.abs(P), np.array([EX + 0.012, abs(E[1] + 0.005), E[2] - 0.055]), np.array([0.02, 0.03, 0.022]))
    x = x - np.sign(x) * F.get("cheek_in", 0) * ch
    # nos: šířka, délka (špička dolů), vystouplost
    nz = gauss(P, np.array([0, YF - 0.012, E[2] - 0.04]), np.array([0.018, 0.03, 0.03]))
    x = x * (1 - F.get("nose_w", 0) * nz)
    tip = gauss(P, np.array([0, YF - 0.02, E[2] - 0.052]), np.array([0.016, 0.02, 0.014]))
    z = z - F.get("nose_len", 0) * tip
    y = y - F.get("nose_out", 0) * tip
    # rty: tloušťka (svisle k linii úst)
    zm = E[2] + F.get("mouth_dz", -0.088)
    lp = gauss(P, np.array([0, YF - 0.005, zm]), np.array([0.026, 0.03, 0.014]))
    z = zm + (z - zm) * (1 + F.get("lips", 0) * lp)
    for sg in (1, -1):
        co_ = gauss(P, np.array([sg * 0.024, YF - 0.0, zm]), np.array([0.011, 0.025, 0.01]))
        z = z + F.get("smile", 0) * co_
    for sg in (1, -1):
        co_ = gauss(P, np.array([sg * 0.024, YF, zm]), np.array([0.011, 0.025, 0.01]))
        z = z + F.get("smile", 0) * co_
    # uši (odstávání)
    ear = ss((np.abs(x) - (EX + 0.045)) / 0.012) * gauss(P * np.array([0, 1, 1]), np.array([0, E[1] + 0.06, E[2] - 0.02]), np.array([1, 0.035, 0.04]))
    x = x * (1 + F.get("ears", 0) * ear)
    return np.stack([x, y, z], 1)
for o in [head, brows] + hairs:
    P = np.array([o.matrix_world @ v.co for v in o.data.vertices])
    Q2 = deform(P)
    inv = o.matrix_world.inverted()
    for v, q in zip(o.data.vertices, Q2): v.co = inv @ Vector(q)
    o.data.update()
for o in hairs:
    cut = CFG.get("hair_back", {}).get(o.name.split("_", 1)[1], None)
    if cut is None: continue
    b2 = bmesh.new(); b2.from_mesh(o.data)
    kill = [v for v in b2.verts if (o.matrix_world @ v.co).y < E[1] + cut or (CFG.get("one_bun") and (o.matrix_world @ v.co).x < 0)]
    bmesh.ops.delete(b2, geom=kill, context='VERTS'); b2.to_mesh(o.data); b2.free()
    if CFG.get("one_bun"):
        # jediný drdol doprostřed týla
        P_ = np.array([o.matrix_world @ v.co for v in o.data.vertices]); cx = P_[:, 0].mean()
        dz, dy = CFG["one_bun"]
        inv_ = o.matrix_world.inverted()
        for v, q in zip(o.data.vertices, P_): v.co = inv_ @ Vector((q[0] - cx, q[1] + dy, q[2] + dz))
for o in hairs:
    cut = CFG.get("hair_back", {}).get(o.name.split("_", 1)[1], None)
    if cut is None: continue
    b2 = bmesh.new(); b2.from_mesh(o.data)
    kill = [v for v in b2.verts if (o.matrix_world @ v.co).y < E[1] + cut or (CFG.get("one_bun") and (o.matrix_world @ v.co).x < 0)]
    bmesh.ops.delete(b2, geom=kill, context='VERTS'); b2.to_mesh(o.data); b2.free()
    if CFG.get("one_bun"):
        # jediný drdol doprostřed týla
        P_ = np.array([o.matrix_world @ v.co for v in o.data.vertices]); cx = P_[:, 0].mean()
        dz, dy = CFG["one_bun"]
        inv_ = o.matrix_world.inverted()
        for v, q in zip(o.data.vertices, P_): v.co = inv_ @ Vector((q[0] - cx, q[1] + dy, q[2] + dz))
# obočí a řasy (jsou v jedné síti): komponenty pod horní hranou oka = řasy
bc = np.array([brows.matrix_world @ v.co for v in brows.data.vertices])
_b = bmesh.new(); _b.from_mesh(brows.data); _b.verts.ensure_lookup_table()
comp = -np.ones(len(bc), int); k = 0
for v in _b.verts:
    if comp[v.index] >= 0: continue
    st = [v]
    while st:
        u = st.pop()
        if comp[u.index] >= 0: continue
        comp[u.index] = k; st += [e.other_vert(u) for e in u.link_edges]
    k += 1
_b.free()
lash = np.zeros(len(bc), bool)
for c in range(k):
    if bc[comp == c, 2].mean() < E[2] + 0.009: lash[comp == c] = True
for c in range(k):
    sel = comp == c
    if not lash[sel].any(): continue
    cc = bc[sel].mean(0)
    bc[sel, 0] = cc[0] + (bc[sel, 0] - cc[0]) * CFG.get("lash_w", 1.0)
    bc[sel, 2] = cc[2] + (bc[sel, 2] - cc[2]) * CFG.get("lash_h", 1.0)
for side in (1, -1):
    sel = (np.sign(bc[:, 0]) == side) & ~lash
    if not sel.any(): continue
    c = bc[sel].mean(0)
    bc[sel, 2] = c[2] + (bc[sel, 2] - c[2]) * CFG.get("brow_th", 1.0) - CFG.get("brow_dz", 0)
    inner = ss(1 - (np.abs(bc[sel, 0]) - np.abs(bc[sel, 0]).min()) / 0.02)
    bc[sel, 2] -= CFG.get("frown", 0) * inner
print("RASY komponent", int(len(set(comp[lash]))), "OBOCI", int(len(set(comp[~lash]))))
inv = brows.matrix_world.inverted()
for v, q in zip(brows.data.vertices, bc): v.co = inv @ Vector(q)

# --- textury
def img_np(im):
    w, h = im.size; a = np.array(im.pixels[:], np.float32).reshape(h, w, 4); return a
def np_img(name, a, path):
    h, w = a.shape[:2]; im = bpy.data.images.new(name, w, h, alpha=True)
    im.pixels[:] = a.reshape(-1); im.filepath_raw = path; im.file_format = 'PNG'; im.save(); return im
def tex_node(m, key="Base Color"):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    st = [l.from_node for l in b.inputs[key].links]; seen = set()
    while st:
        n = st.pop()
        if n.name in seen: continue
        seen.add(n.name)
        if n.type == 'TEX_IMAGE' and n.image: return n, b
        for i in n.inputs: st += [l.from_node for l in i.links]
    return None, b
def face_mask(o, wfun, size):
    """UV maska ploch hlavy podle váhy wfun(světové body) -> pole size×size (řádky zdola jako Blender pixels)"""
    from PIL import ImageDraw
    m = Image.new("L", (size, size), 0); d = ImageDraw.Draw(m)
    P = np.array([o.matrix_world @ v.co for v in o.data.vertices]); W = wfun(P)
    uv = o.data.uv_layers.active.data
    for p in o.data.polygons:
        w = float(np.mean([W[i] for i in p.vertices]))
        if w < 0.02: continue
        d.polygon([(uv[li].uv[0] * size, uv[li].uv[1] * size) for li in p.loop_indices], fill=int(255 * min(1, w)))
    return np.asarray(m.filter(ImageFilter.GaussianBlur(size / 300)), np.float32) / 255
# --- dlouhá sukně (šaty) místo kalhot: kužel od boků ke kotníkům, váhy pánev -> stehna
def make_skirt():
    legs = next(o for o in outfit if o.type == 'MESH' and o.name.endswith("_legs"))
    feet = [o for o in outfit if o.type == 'MESH' and (o.name.endswith("_feet") or o.name.endswith("_boots"))]
    LP = np.array([legs.matrix_world @ v.co for v in legs.data.vertices])
    z_top = LP[:, 2].max() - CFG["skirt"].get("top_down", 0.03); z_bot = CFG["skirt"].get("bottom", 0.12)
    cy = LP[:, 1].mean()
    allp = [LP] + [np.array([f.matrix_world @ v.co for v in f.data.vertices]) for f in feet]
    allp = np.concatenate(allp)
    N, R = 28, 12
    rows = []
    r_prev = None
    for r in range(R + 1):
        t = r / R; z = z_top + (z_bot - z_top) * t
        sl = allp[np.abs(allp[:, 2] - z) < 0.03]
        rx = (np.abs(sl[:, 0]).max() if len(sl) else 0.15) + 0.02
        ry = (np.abs(sl[:, 1] - cy).max() if len(sl) else 0.12) + 0.02
        rx = max(rx, 0.0); ry = max(ry, 0.0)
        fl = CFG["skirt"].get("flare", 0.12) * t ** 1.3
        rx += fl; ry += fl * 0.9
        if r_prev is not None: rx = max(rx, r_prev[0]); ry = max(ry, r_prev[1])
        r_prev = (rx, ry)
        ring = []
        for k in range(N):
            a = 2 * math.pi * k / N
            wob = 1 + 0.025 * math.sin(a * 7 + t * 2) * t
            ring.append((math.sin(a) * rx * wob, cy - math.cos(a) * ry * wob, z))
        rows.append(ring)
    V = [p for ring in rows for p in ring]
    F = [(r * N + k, r * N + (k + 1) % N, (r + 1) * N + (k + 1) % N, (r + 1) * N + k) for r in range(R) for k in range(N)]
    me = bpy.data.meshes.new(f"{NAME}_sukne"); me.from_pydata(V, [], F)
    ob = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(ob)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            r, k = divmod(vi, N)
            u = k / N
            if poly.vertices[0] % N == N - 1 and k == 0: u = 1.0
            uvl.data[li].uv = (u * 3.0, 1 - r / R)
    for poly in me.polygons: poly.use_smooth = True
    # váhy
    tl = (arm.matrix_world @ arm.data.bones["thigh_l"].head_local).x
    gp = ob.vertex_groups.new(name="pelvis"); gl = ob.vertex_groups.new(name="thigh_l"); gr = ob.vertex_groups.new(name="thigh_r")
    for i, (x, y, z) in enumerate(V):
        t = (z_top - z) / (z_top - z_bot)
        a = 0.55 * ss(t / 0.7)
        sx = np.clip(x / 0.12, -1, 1) * np.sign(tl)
        wl = a * (0.5 + 0.5 * sx); wr = a * (0.5 - 0.5 * sx)
        gp.add([i], 1 - a, 'REPLACE'); gl.add([i], wl, 'REPLACE'); gr.add([i], wr, 'REPLACE')
    md = ob.modifiers.new("Armature", 'ARMATURE'); md.object = arm; ob.parent = arm
    so = ob.modifiers.new("tl", 'SOLIDIFY'); so.thickness = 0.004; so.offset = 1
    # textura sukně: vlněná látka (šum + jemná vazba + svislé záhyby), lem dole tmavší
    rng_ = np.random.default_rng(5); Wd = 512
    yy, xx = np.mgrid[0:Wd, 0:Wd].astype(np.float32)
    n1 = np.asarray(Image.fromarray((rng_.random((64, 64)) * 255).astype(np.uint8)).resize((Wd, Wd), Image.BICUBIC), np.float32) / 255
    n2 = rng_.random((Wd, Wd)).astype(np.float32)
    weave = 0.5 + 0.5 * np.sin(xx * 2 * np.pi / 3.0) * np.sin(yy * 2 * np.pi / 3.0)
    folds = 0.86 + 0.14 * np.sin(xx / Wd * 2 * np.pi * 3 + 0.6 * np.sin(yy / Wd * 6))
    lumf = (0.9 + 0.12 * (n1 - 0.5) + 0.05 * (n2 - 0.5) + 0.05 * (weave - 0.5)) * folds
    tc_ = np.array(CFG["skirt"]["color"], np.float32)
    arr = np.clip(tc_[None, None, :] * lumf[..., None], 0, 1)
    arr[:14] *= 0.72                                  # lem (řádek 0 = spodek)
    a4 = np.dstack([arr, np.ones(arr.shape[:2], np.float32)])
    sm_ = bpy.data.materials.new(f"{NAME}_sukne_mat"); sm_.use_nodes = True
    b = next(n for n in sm_.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    tx = sm_.node_tree.nodes.new("ShaderNodeTexImage"); tx.image = np_img(f"{NAME}_sukne", a4, f"{TEXOUT}/{NAME}_sukne.png")
    sm_.node_tree.links.new(tx.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.85
    me.materials.append(sm_)
    legs.hide_render = True; legs.hide_viewport = True
    outfit.append(ob)
    print("SUKNE tris", len(F) * 2)
if CFG.get("skirt"): make_skirt()
mh = head.data.materials[0]; tn, _ = tex_node(mh)
A = img_np(tn.image); S = A.shape[0]
P = np.array([head.matrix_world @ v.co for v in head.data.vertices])
# tón pleti
A[..., :3] *= np.array(CFG.get("skin_mul", [1, 1, 1]), np.float32)
# odstranění linek kolem očí (ženská textura má namalované oční linky)
if CFG.get("no_liner"):
    import cv2
    em = face_mask(head, lambda p: np.maximum(gauss(p, np.array([EX, E[1], E[2]]), np.array([0.03, 0.04, 0.02])),
                                              gauss(p, np.array([-EX, E[1], E[2]]), np.array([0.03, 0.04, 0.02]))), S)
    rgb = (np.clip(A[..., :3], 0, 1) * 255).astype(np.uint8)[::-1].copy()
    lum = rgb.mean(2); skin_l = np.percentile(lum[em[::-1] > 0.12], 70) if (em > 0.12).any() else 150
    blu = rgb[..., 2].astype(int) - rgb[..., 0].astype(int)
    mask = ((em[::-1] > 0.12) & ((lum < skin_l * 0.9) | ((rgb[..., 0].astype(int) - rgb[..., 2].astype(int)) < 60))).astype(np.uint8) * 255
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
    fixed = cv2.inpaint(rgb, mask, 9, cv2.INPAINT_TELEA)
    Image.fromarray((em[::-1] * 255).astype(np.uint8)).save(f"{TEXOUT}/dbg_em.png"); Image.fromarray(mask).save(f"{TEXOUT}/dbg_mask.png")
    print("LINER", float(em.max()), int((mask > 0).sum()), skin_l)
    Image.fromarray((em[::-1] * 255).astype(np.uint8)).save(f"{TEXOUT}/dbg_em.png"); Image.fromarray(mask).save(f"{TEXOUT}/dbg_mask.png")
    print("LINER", float(em.max()), int((mask > 0).sum()), skin_l)
    A[..., :3] = (fixed[::-1].astype(np.float32) / 255)
# strniště
if CFG.get("stubble", 0) > 0:
    zm = E[2] + CFG["face"].get("mouth_dz", -0.088)
    def stw(p):
        below_nose = ss((E[2] - 0.062 - p[:, 2]) / 0.012)
        jaw = ss((E[1] + 0.065 - p[:, 1]) / 0.02) * ss((p[:, 2] - (E[2] - 0.17)) / 0.03)
        lips = gauss(p, np.array([0, YF - 0.005, zm]), np.array([0.022, 0.03, 0.009]))
        return np.clip(below_nose * jaw - lips * 1.2, 0, 1)
    sm = face_mask(head, stw, S)[..., None]
    rng = np.random.default_rng(3); dots = (rng.random((S, S)) < 0.35).astype(np.float32)
    dots = np.asarray(Image.fromarray((dots * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32)[..., None] / 255
    k = CFG["stubble"] * sm * (0.55 + 0.45 * dots)
    sc = np.array(CFG.get("stubble_col", [0.12, 0.1, 0.09]), np.float32)
    A[..., :3] = A[..., :3] * (1 - k) + sc * k
# pihy
if CFG.get("freckles", 0) > 0:
    def fw(p):
        return np.clip(gauss(p * np.array([0.6, 1, 1]), np.array([0, YF, E[2] - 0.035]), np.array([0.05, 0.04, 0.03])) * 1.3, 0, 1)
    fm = face_mask(head, fw, S)
    rng = np.random.default_rng(11); n = int(CFG["freckles"] * 2600)
    fr = np.zeros((S, S), np.float32)
    ys, xs = np.nonzero(fm > 0.15)
    pick = rng.choice(len(ys), size=min(n, len(ys)), replace=False)
    for i in pick:
        yy, xx = ys[i], xs[i]; r = rng.uniform(1.2, 3.0) * S / 2048
        y0, y1, x0, x1 = int(yy - r - 1), int(yy + r + 2), int(xx - r - 1), int(xx + r + 2)
        gy, gx = np.mgrid[y0:y1, x0:x1]
        dd = np.clip(1 - np.sqrt((gy - yy) ** 2 + (gx - xx) ** 2) / r, 0, 1) * rng.uniform(0.35, 0.8)
        fr[max(0, y0):y1, max(0, x0):x1] = np.maximum(fr[max(0, y0):y1, max(0, x0):x1], dd[max(0, -y0):, max(0, -x0):][:fr[max(0, y0):y1, max(0, x0):x1].shape[0], :fr[max(0, y0):y1, max(0, x0):x1].shape[1]])
    fr *= fm
    fc = np.array([0.42, 0.2, 0.09], np.float32)
    A[..., :3] = A[..., :3] * (1 - fr[..., None] * 0.55) + fc * fr[..., None] * 0.55
if CFG.get("scalp", True):
    def scw(p):
        return ss((p[:, 2] - (E[2] - 0.12)) / 0.02) * np.clip(ss((p[:, 2] - (E[2] + 0.035)) / 0.02) + ss((p[:, 1] - (E[1] + 0.085)) / 0.02), 0, 1)
    scm = face_mask(head, scw, S)
    rgb = np.clip(A[..., :3], 0, 1)
    crown = face_mask(head, lambda p: ss((p[:, 2] - (E[2] + 0.09)) / 0.01), S) > 0.9
    refc = np.median(rgb[crown], 0) if crown.any() else rgb.reshape(-1, 3).mean(0)
    dist = np.linalg.norm(rgb - refc, axis=2)
    hairpx = np.clip((0.16 - dist) / 0.08, 0, 1) * scm
    hairpx = np.asarray(Image.fromarray((hairpx * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
    lum_ = rgb.mean(2, keepdims=True); hc = (np.array(CFG["hair_col"], np.float32) * 0.6) ** (1 / 2.2)
    rec = np.clip(hc * (lum_ / max(float(lum_[hairpx > 0.5].mean()) if (hairpx > 0.5).any() else 0.5, 1e-3)) * 0.9, 0, 1)
    A[..., :3] = rgb * (1 - hairpx[..., None]) + rec * hairpx[..., None]
    print("SCALP px", int((hairpx > 0.5).sum()))
if CFG.get("scalp", True):
    def scw(p):
        return ss((p[:, 2] - (E[2] - 0.12)) / 0.02) * np.clip(ss((p[:, 2] - (E[2] + 0.035)) / 0.02) + ss((p[:, 1] - (E[1] + 0.085)) / 0.02), 0, 1)
    scm = face_mask(head, scw, S)
    rgb = np.clip(A[..., :3], 0, 1); sat = (rgb.max(2) - rgb.min(2)) / np.maximum(rgb.max(2), 1e-3)
    hairpx = np.clip((0.42 - sat) / 0.15, 0, 1) * scm
    lum_ = rgb.mean(2, keepdims=True); hc = (np.array(CFG["hair_col"], np.float32) * 0.6) ** (1 / 2.2)
    ref = float(lum_[..., 0][hairpx > 0.5].mean()) if (hairpx > 0.5).any() else 0.5
    rec = np.clip(hc * (lum_ / max(ref, 1e-3)) * 0.9, 0, 1)
    A[..., :3] = rgb * (1 - hairpx[..., None]) + rec * hairpx[..., None]
    print("SCALP px", int((hairpx > 0.5).sum()))
A = np.clip(A, 0, 1)
tn.image = np_img(f"{NAME}_kuze", A, f"{TEXOUT}/{NAME}_kuze.png"); mh.name = f"{NAME}_telo_kuze"
# ruce v oblečení (mužské Arms má materiál kůže Regular) -> stejný tón
for o in outfit:
    if o.type != 'MESH': continue
    for m in o.data.materials:
        if m and "Regular" in m.name:
            t2, _ = tex_node(m)
            if t2:
                a2 = img_np(t2.image); a2[..., :3] *= np.array(CFG.get("skin_mul", [1, 1, 1]), np.float32)
                t2.image = np_img(f"{NAME}_ruce", np.clip(a2, 0, 1), f"{TEXOUT}/{NAME}_ruce.png"); m.name = f"{NAME}_telo_ruce"
# oči: duhovka do cílové barvy (hue podle jasu)
te, _ = tex_node(eyes.data.materials[0])
a = img_np(te.image); rgb = a[..., :3]
sat = rgb.max(2) - rgb.min(2); iris = (sat > 0.08)[..., None]
lum = rgb.mean(2, keepdims=True)
tgt = np.array(CFG["eye"], np.float32)
a[..., :3] = np.where(iris, np.clip(tgt * (lum / max(float(lum[iris[..., 0]].mean()), 1e-3)), 0, 1), rgb)
te.image = np_img(f"{NAME}_oko", a, f"{TEXOUT}/{NAME}_oko.png"); eyes.data.materials[0].name = f"{NAME}_oci"
# vlasy, vousy, obočí: barva
def tint(o, col, grey=0.0, tag="vlasy"):
    """barva zapečená do textury (glTF nepřenese uzly Mix): lineárně tex * col, příměs šedi; materiál přejmenován pro import Godotu"""
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        t, b = tex_node(m)
        if t is None: continue
        a = img_np(t.image)
        rgb = np.clip(a[..., :3], 0, 1)
        lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        lin = lin * np.array(col, np.float32)
        if grey > 0: lin = lin * (1 - grey) + np.array([0.55, 0.53, 0.5], np.float32) * grey
        srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(np.clip(lin, 0, None), 1 / 2.4) - 0.055)
        a[..., :3] = np.clip(srgb, 0, 1)
        nm = f"{NAME}_{tag}"
        im = np_img(nm, a, f"{TEXOUT}/{nm}.png")
        # obrázek přímo do Base Color, Alpha zachovat
        for l in list(b.inputs["Base Color"].links): m.node_tree.links.remove(l)
        t.image = im; m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
        m.name = f"{NAME}_{tag}_mat"
def matte(o, rough=0.75, spec=0.25):
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for l in list(b.inputs["Roughness"].links): m.node_tree.links.remove(l)
        b.inputs["Roughness"].default_value = rough
        for k in ("Specular IOR Level", "Specular"):
            if k in b.inputs: b.inputs[k].default_value = spec
for k_, o in enumerate(hairs): tint(o, CFG["hair_col"], CFG.get("grey", 0), tag=f"vlasy{k_}"); matte(o)
matte(brows)
tint(brows, CFG.get("brow_col", CFG["hair_col"]), tag="rasy_oboci")
# oblečení: barevná varianta + tón
for o in outfit:
    if o.type != 'MESH': continue
    for m in o.data.materials:
        if m and CFG["outfit"] in m.name and CFG.get("outfit_mul"):
            tint(o, CFG["outfit_mul"], tag="obleceni"); break

# --- scéna, animace, render
an = imp(UAL); aarm = next(o for o in an if o.type == 'ARMATURE')
for o in an:
    if o is not aarm: bpy.data.objects.remove(o)
bpy.data.objects.remove(aarm)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'; scn.cycles.samples = 32; scn.cycles.use_denoising = True
w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True; nt = w.node_tree
bg = nt.nodes["Background"]; tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sp.inputs[0]); ramp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(sp.outputs["Z"], ramp.inputs[0])
ramp.color_ramp.elements[0].color = (0.75, 0.78, 0.8, 1); ramp.color_ramp.elements[1].color = (0.28, 0.45, 0.85, 1)
nt.links.new(ramp.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.9
sun = bpy.data.objects.new("s", bpy.data.lights.new("s", 'SUN')); scn.collection.objects.link(sun)
sun.data.energy = 4.0; sun.data.angle = math.radians(1.5); sun.data.color = (1.0, 0.95, 0.88); sun.rotation_euler = (math.radians(60), 0, math.radians(35))
scn.view_settings.view_transform = 'AgX'
bpy.ops.mesh.primitive_plane_add(size=20)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); scn.collection.objects.link(cam); scn.camera = cam
ANIM = os.environ.get("ANIM", "Idle_Loop")
act = bpy.data.actions.get(ANIM)
if act:
    arm.animation_data_create(); arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
scn.frame_set(10); bpy.context.view_layer.update()
hp = arm.matrix_world @ arm.pose.bones["Head"].head
tiles = []
shots = [(Vector((0, 0, 0.9)), 3.4, 25, 50), (Vector((hp.x, hp.y, hp.z + 0.06)), 0.8, 0, 60), (Vector((hp.x, hp.y, hp.z + 0.06)), 0.8, 35, 60)]
for i, (tgt, d, az, lens) in enumerate(shots):
    cam.location = tgt + Vector((math.sin(math.radians(az)) * d, -math.cos(math.radians(az)) * d, 0.0))
    cam.rotation_euler = (math.radians(90), 0, math.radians(az)); cam.data.lens = lens
    scn.render.resolution_x, scn.render.resolution_y = 400, 600
    p = f"/tmp/claude-0/qp_{NAME}_{i}.png"; scn.render.filepath = p; bpy.ops.render.render(write_still=True)
    tiles.append(Image.open(p).convert("RGB"))
c = Image.new("RGB", (1200, 600))
for i, t in enumerate(tiles): c.paste(t, (400 * i, 0))
c.save(OUT, quality=90)
bpy.ops.wm.save_as_mainfile(filepath=OUT.rsplit(".", 1)[0] + ".blend")
print("OK", NAME)
