import sys; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import numpy as np, bmesh, cloth, tex_gen, json
from PIL import Image, ImageFilter
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/claude/z30/hair.blend")
body = bpy.data.objects["zena30_telo"]; arm = bpy.data.objects["zena30_kostra"]
co, no, names, W = cloth.body_arrays(body)
X, Y, Z = co[:, 0], co[:, 1], co[:, 2]
P = json.load(open("/home/claude/z30/scripts/params.json"))
def ss(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

head_w = cloth.gw(names, W, "neck_01", "Head")
hand_w = cloth.gw(names, W, *[n for n in names if n.startswith(("hand_", "index", "middle", "ring", "pinky", "thumb"))])
torso_arm = (Z > 0.84) & (head_w < 0.5) & (hand_w < 0.3)

def neck_fn(front, back, side_rise):
    def f(c):
        x, y, z = c; k = ss(y, -0.03, 0.07)
        nz = (front + side_rise * (x / 0.11) ** 2) * (1 - k) + (back + 0.05 * (x / 0.11) ** 2) * k
        return nz - z
    return f
TEXD = "/home/claude/z30/tex"
def srgb(c): return tuple((np.array(c) ** 2.2).tolist())
def fabric(name, col, threads, tile_m, slub, rough, nstr=2.5, seed=0, extra=None):
    h = tex_gen.weave(512, threads, seed, slub)
    rng = np.random.default_rng(seed)
    blot = tex_gen.smooth_noise((512, 512), 64, rng)
    a = (0.82 + 0.18 * h)[..., None] * np.array(col)[None, None] * (0.93 + 0.14 * blot[..., None])
    if extra is not None: a = extra(a)
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(f"{TEXD}/zena30_{name}_barva.png")
    Image.fromarray(tex_gen.to_normal(h, nstr)).save(f"{TEXD}/zena30_{name}_normal.png")
    m = bpy.data.materials.new(f"zena30_{name}"); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(f"{TEXD}/zena30_{name}_barva.png")
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(f"{TEXD}/zena30_{name}_normal.png"); tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.8
    nt.links.new(t.outputs[0], bs.inputs["Base Color"]); nt.links.new(tn.outputs[0], nm.inputs["Color"]); nt.links.new(nm.outputs[0], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = rough; bs.inputs["Specular IOR Level"].default_value = 0.25
    bs.inputs["Sheen Weight"].default_value = 0.3
    m["tile_m"] = tile_m
    return m
M_len = fabric("kosile", (0.86, 0.83, 0.74), 64, 0.04, 0.3, 0.85, 1.5, 1)
M_vl = fabric("saty", P["saty_barva"], 40, 0.06, 0.2, 0.92, 2.5, 2)
M_zas = fabric("zastera", (0.70, 0.64, 0.52), 52, 0.05, 0.35, 0.88, 2.0, 3)
M_kuz = fabric("kuze_bot", (0.30, 0.19, 0.11), 6, 0.10, 0.6, 0.6, 0.8, 4)

def finish(ob, mat, acc=None, uv_axis=True):
    if acc is None: acc = cloth.transfer_weights(ob, co, names, W)
    cloth.set_weights(ob, names, acc)
    cloth.triplanar_uv(ob, mat["tile_m"] * 8, (lambda c: 'x' if abs(c.x) > 0.17 and c.z > 1.3 else 'z') if uv_axis else None)
    ob.data.materials.append(mat)
    return cloth.link(ob, arm)

# ---------- košile (len): trup + paže po zápěstí
def off_k(c, o):
    ax = abs(c[0]); return o + 0.010 * ss(ax, 0.45, 0.60) + 0.002 * ss(ax, 0.2, 0.3)
kos = cloth.shell(body, co, no, torso_arm, 0.0035, "zena30_kosile", off_k)
cloth.cut_iso(kos, neck_fn(1.372, 1.445, 0.095), lip=0.003)
cloth.cut_iso(kos, lambda c: 0.618 - abs(c[0]), lip=0.004)
kos = finish(kos, M_len)
# ---------- šaty (vlna): živůtek + rukávy k loktům
def off_s(c, o):
    ax = abs(c[0]); return o + 0.012 * ss(ax, 0.30, 0.41)
sat = cloth.shell(body, co, no, torso_arm, 0.010, "zena30_zivutek", off_s)
cloth.cut_iso(sat, neck_fn(1.345, 1.43, 0.115), lip=0.004)
cloth.cut_iso(sat, lambda c: 0.405 - abs(c[0]), lip=0.005)
sat = finish(sat, M_vl)

# ---------- sukně: řezy pánve a nohou, visí rovně, rozšiřuje se (A-střih), sklady
legmask = (Z < 1.08) & (head_w < 0.5) & (hand_w < 0.3) & (np.abs(X) < 0.32)
PL = co[legmask]
ZT, ZB = P["sukne_hore"], P["sukne_lem"]
rows, N = 30, 72
zs = np.linspace(ZT, ZB, rows + 1)
th = np.linspace(0, 2 * np.pi, N, endpoint=False)
CEN = np.array([0.0, 0.040])
R = np.zeros((rows + 1, N))
for r, z in enumerate(zs):
    sl = PL[np.abs(PL[:, 2] - z) < 0.02]
    if len(sl) < 5: R[r] = R[r - 1]; continue
    d = sl[:, :2] - CEN
    for i, t in enumerate(th):
        R[r, i] = (d[:, 0] * math.cos(t) + d[:, 1] * math.sin(t)).max()
for _ in range(4): R = 0.25 * np.roll(R, 1, 1) + 0.5 * R + 0.25 * np.roll(R, -1, 1)
for r in range(1, rows + 1): R[r] = np.maximum(R[r], R[r - 1] * 0.998)
FL = P["sukne_rozsir"]; ZFL = P["sukne_rozsir_od"]
for r, z in enumerate(zs):
    t = np.clip((ZFL - z) / (ZFL - ZB), 0, 1)
    fold = P["sklady"] * t ** 1.2 * (np.sin(th * 11 + 0.6) * 0.65 + np.sin(th * 7 + 1.7) * 0.35)
    R[r] += 0.016 + FL * t ** 1.4 + fold
sk_bm = bmesh.new(); uvl = sk_bm.loops.layers.uv.new("UVMap")
grid = []
for r, z in enumerate(zs):
    grid.append([sk_bm.verts.new((CEN[0] + R[r, i] * math.cos(t), CEN[1] + R[r, i] * math.sin(t), z)) for i, t in enumerate(th)])
for r in range(rows):
    for i in range(N):
        j = (i + 1) % N
        f = sk_bm.faces.new((grid[r][i], grid[r][j], grid[r + 1][j], grid[r + 1][i]))
sk_bm.normal_update()
for f in sk_bm.faces:
    c = f.calc_center_median()
    if f.normal.dot(Vector((c.x - CEN[0], c.y - CEN[1], 0))) < 0: f.normal_flip()
me = bpy.data.meshes.new("zena30_sukne"); sk_bm.to_mesh(me); sk_bm.free()
sk = bpy.data.objects.new("zena30_sukne", me)
# lem dovnitř (tloušťka látky)
SKV = np.array([v.co[:] for v in me.vertices])

def skirt_weights(V):
    """Pás boků jede s pánví; níž se sukně míchá s nohou své strany (stehno, pod kolenem lýtko).
    Vzadu a vpředu víc lýtka (pata kope do lemu, koleno se zvedá pod látkou)."""
    acc = np.zeros((len(V), len(names)))
    ip, i1 = names.index("pelvis"), names.index("spine_01")
    il, ir = names.index("thigh_l"), names.index("thigh_r")
    cl, cr = names.index("calf_l"), names.index("calf_r")
    ang = np.arctan2(V[:, 1] - CEN[1], V[:, 0] - CEN[0])
    s = np.cos(ang); back = np.clip(np.sin(ang), 0, 1); front = np.clip(-np.sin(ang), 0, 1)
    wl = np.clip(0.5 + 0.5 * np.sign(s) * np.abs(s) ** P["strana_exp"], 0, 1)
    a = P["stehno_max"] * ss(-V[:, 2], -P["stehno_od"], -P["stehno_plne"])
    cmax = P["lytko_bok"] + (P["lytko_zad"] - P["lytko_bok"]) * back ** 0.7 + (P["lytko_pred"] - P["lytko_bok"]) * front ** 0.7
    c = cmax * ss(-V[:, 2], -P["lytko_od"], -P["lytko_plne"])
    top = ss(V[:, 2], 0.98, 1.05)
    acc[:, il] = a * wl * (1 - c); acc[:, ir] = a * (1 - wl) * (1 - c)
    acc[:, cl] = a * wl * c; acc[:, cr] = a * (1 - wl) * c
    acc[:, ip] = (1 - a) * (1 - top * 0.5); acc[:, i1] = (1 - a) * top * 0.5
    return acc
acc_sk = skirt_weights(SKV)
sk = finish(sk, M_vl, acc_sk, uv_axis=False)

# ---------- zástěra: výsek sukně vpředu, o kus odsazený, stejné váhy
ap_bm = bmesh.new(); ag = []
ZA = P["zastera_lem"]
ar = [r for r, z in enumerate(zs) if z >= ZA - 1e-6]
zs_a = np.linspace(zs[0] - 0.01, ZA, len(ar))
A0, A1 = -math.pi / 2 - P["zastera_sirka"], -math.pi / 2 + P["zastera_sirka"]
na = 26
tha = np.linspace(A0, A1, na)
for k, z in enumerate(zs_a):
    rr = []
    for t in tha:
        Rz = np.array([np.interp(t % (2 * np.pi), np.append(th, 2 * np.pi), np.append(R[r], R[r][0])) for r in range(rows + 1)])
        Ri = float(np.interp(-z, -zs, Rz)) + 0.007 + 0.006 * (k / (len(zs_a) - 1))
        rr.append(ap_bm.verts.new((CEN[0] + Ri * math.cos(t), CEN[1] + Ri * math.sin(t), z)))
    ag.append(rr)
for k in range(len(ag) - 1):
    for i in range(na - 1):
        f = ap_bm.faces.new((ag[k][i], ag[k][i + 1], ag[k + 1][i + 1], ag[k + 1][i]))
ap_bm.normal_update()
for f in ap_bm.faces:
    c = f.calc_center_median()
    if f.normal.dot(Vector((c.x - CEN[0], c.y - CEN[1], 0))) < 0: f.normal_flip()
# tloušťka: vysunout okraj dozadu (žádná viditelná rubová strana)
bmesh.ops.solidify(ap_bm, geom=ap_bm.faces[:], thickness=-0.003)
me = bpy.data.meshes.new("zena30_zastera"); ap_bm.to_mesh(me); ap_bm.free()
ap = bpy.data.objects.new("zena30_zastera", me)
APV = np.array([v.co[:] for v in me.vertices])
ap = finish(ap, M_zas, skirt_weights(APV), uv_axis=False)

# ---------- opasek (kůže) v pase přes šaty i zástěru
zb0, zb1 = P["opasek"], P["opasek"] - 0.032
b_bm = bmesh.new(); bg = []
for z in (zb0, zb1):
    r0 = np.interp(-z, -zs, R[:, 0]) * 0
    row = []
    for i, t in enumerate(th):
        Rz = np.array([R[r][i] for r in range(rows + 1)])
        Ri = float(np.interp(-z, -zs, Rz)) + 0.012
        row.append(b_bm.verts.new((CEN[0] + Ri * math.cos(t), CEN[1] + Ri * math.sin(t), z)))
    bg.append(row)
for i in range(N):
    j = (i + 1) % N; b_bm.faces.new((bg[0][i], bg[0][j], bg[1][j], bg[1][i]))
b_bm.normal_update()
for f in b_bm.faces:
    c = f.calc_center_median()
    if f.normal.dot(Vector((c.x - CEN[0], c.y - CEN[1], 0))) < 0: f.normal_flip()
bmesh.ops.solidify(b_bm, geom=b_bm.faces[:], thickness=-0.004)
me = bpy.data.meshes.new("zena30_opasek"); b_bm.to_mesh(me); b_bm.free()
op = bpy.data.objects.new("zena30_opasek", me)
op = finish(op, M_kuz, skirt_weights(np.array([v.co[:] for v in me.vertices])), uv_axis=False)

# ---------- boty: slupka chodidla
foot_w = cloth.gw(names, W, "foot_l", "foot_r", "ball_l", "ball_r", "ball_leaf_l", "ball_leaf_r")
fm = (Z < 0.13) & ((foot_w > 0.05) | (Z < 0.09))
bo = cloth.shell(body, co, no, fm, 0.007, "zena30_boty", smooth=12)
cloth.cut_iso(bo, lambda c: 0.092 - c[2] + 0.012 * max(0, -(c[1] - 0.02)) * 4, lip=0.004)
bo = finish(bo, M_kuz, uv_axis=False)

# ---------- tělo: pryč vše schované pod oblečením
fn_k = neck_fn(1.372, 1.445, 0.095)
hide = torso_arm & (np.array([fn_k(c) for c in co]) > 0.012) & (np.abs(X) < 0.60)
hide |= (Z > P["puncochy_do"]) & (Z < 1.0) & (np.abs(X) < 0.3) & (head_w < 0.5) & (hand_w < 0.3)
hide |= (Z < 0.075) | ((Z < 0.10) & (foot_w > 0.3))
bm = bmesh.new(); bm.from_mesh(body.data)
bm.verts.ensure_lookup_table()
kill = [f for f in bm.faces if all(hide[v.index] for v in f.verts)]
bmesh.ops.delete(bm, geom=kill, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(body.data); bm.free()
# punčochy (vlna) – lýtka v textuře kůže přebarvit
import skin_tex
co2 = np.array([body.matrix_world @ v.co for v in body.data.vertices])
att = ((co2[:, 2] < 0.60) & (co2[:, 2] > 0.02) & (np.abs(co2[:, 0]) < 0.3)).astype(float)
S = 1024
mk = skin_tex.raster_attr(body, att, S)
mk = np.asarray(Image.fromarray((mk * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1))).astype(float) / 255
img = np.asarray(Image.open(f"{TEXD}/zena30_kuze.png").convert("RGB")).astype(float) / 255
wv = tex_gen.weave(S, 160, 7, 0.2)
stc = np.array(P["puncochy_barva"]) * (0.85 + 0.15 * wv[..., None])
img = img * (1 - mk[..., None]) + stc * mk[..., None]
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(f"{TEXD}/zena30_kuze.png")
for im in bpy.data.images:
    if im.filepath.endswith("zena30_kuze.png"): im.reload()
tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'}
print("TROJ", tris, sum(tris.values()))
np.savez("/home/claude/z30/skirt_grid.npz", R=R, zs=zs, th=th, CEN=CEN)
bpy.ops.wm.save_as_mainfile(filepath="/home/claude/z30/outfit.blend")
