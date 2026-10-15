"""Pískovcová skalní věž (Adršpach / Prachov) – high-poly pro zapékání.
python3 tower_geo.py <varianta> <seed> <výstup.blend>
varianty: jehla | vez | hlava | naklonena | masiv2 | masiv3
Pivot: z = 0 je úroveň terénu, model jde 1 m pod zem.
"""
import sys, math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, noise
from scipy import ndimage
from skimage import measure

VAR = sys.argv[1]; SEED = int(sys.argv[2]); OUT = sys.argv[3]
rng = random.Random(SEED); nrng = np.random.default_rng(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)

def sst(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0); return t * t * (3 - 2 * t)

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)

def smax(a, b, k):
    return -smin(-a, -b, k)

# ---------------------------------------------------------------- parametry variant
def comp(H, a, b, n=3.2, lean=(0, 0), off=(0, 0), rot=0.0, head=0.0, needle=0.0, waist=0.0):
    return dict(H=H, a=a, b=b, n=n, lean=lean, off=off, rot=rot, head=head, needle=needle, waist=waist)

if VAR == "jehla":
    C = [comp(rng.uniform(22, 27), 1.9, 1.6, 2.8, lean=(0.015, -0.01), needle=0.45, waist=0.08)]
elif VAR == "vez":
    C = [comp(rng.uniform(16, 20), 3.0, 2.4, 3.6, waist=0.05)]
elif VAR == "hlava":
    C = [comp(rng.uniform(15, 18), 2.2, 1.9, 3.0, head=0.32, waist=0.12)]
elif VAR == "naklonena":
    C = [comp(rng.uniform(17, 21), 2.4, 1.8, 3.2, lean=(0.16, 0.05), waist=0.06)]
elif VAR == "masiv2":
    C = [comp(rng.uniform(24, 28), 2.8, 2.3, 3.4, off=(-1.6, 0.2), rot=0.2),
         comp(rng.uniform(17, 21), 2.3, 2.0, 3.0, off=(2.3, -0.3), rot=-0.3, lean=(0.04, 0))]
elif VAR == "masiv3":
    C = [comp(rng.uniform(26, 30), 2.6, 2.2, 3.3, off=(-0.4, 0.6), rot=0.1),
         comp(rng.uniform(19, 23), 2.1, 1.8, 3.0, off=(2.6, -0.6), rot=-0.4, lean=(0.05, -0.02)),
         comp(rng.uniform(13, 17), 2.0, 1.7, 3.0, off=(-3.0, -0.9), rot=0.5, lean=(-0.05, 0.0), head=0.2)]
else:
    raise SystemExit("neznámá varianta")

HMAX = max(c["H"] for c in C)
# vrstvy (společné pro celý masiv – sedimentace je vodorovná)
beds = [-1.5]
while beds[-1] < HMAX + 3:
    beds.append(beds[-1] + rng.choice([rng.uniform(0.35, 0.8), rng.uniform(0.8, 1.6), rng.uniform(1.6, 3.2)]))
beds = np.array(beds)
hard = np.array([rng.random() for _ in beds])          # tvrdost vrstvy 0..1
groove = np.array([0.25 + 0.75 * rng.random() for _ in beds])  # hloubka spáry na hranici

def layer_info(z):
    k = np.clip(np.searchsorted(beds, z) - 1, 0, len(beds) - 2)
    z0 = beds[k]; z1 = beds[k + 1]
    t = (z - z0) / (z1 - z0)
    return k, t, z0, z1

# ---------------------------------------------------------------- mřížka
VX = 0.1
ext = max(max(abs(c["off"][0]) + c["a"] * 1.6 + abs(c["lean"][0]) * c["H"], abs(c["off"][1]) + c["b"] * 1.6 + abs(c["lean"][1]) * c["H"]) for c in C) + 1.0
xs = np.arange(-ext, ext + VX, VX); ys = np.arange(-ext, ext + VX, VX); zs = np.arange(-1.4, HMAX + 1.5, VX)
X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
print("grid", X.shape)

def vnoise(scale_m, amp, seed_off):
    """hladký 3D šum z hrubé náhodné mřížky (rozestup scale_m metrů)."""
    r = np.random.default_rng(SEED * 31 + seed_off)
    sh = [max(4, int(len(a) * VX / scale_m) + 4) for a in (xs, ys, zs)]
    g = r.standard_normal(sh)
    out = ndimage.zoom(g, [len(a) / n for a, n in zip((xs, ys, zs), sh)], order=3)
    out = out[:len(xs), :len(ys), :len(zs)]
    pad = [(0, max(0, n - o)) for n, o in zip((len(xs), len(ys), len(zs)), out.shape)]
    out = np.pad(out, pad, mode="edge")
    return amp * out / (out.std() + 1e-9)

K, T, Z0, Z1 = layer_info(Z)
HARD = hard[K]
# profil vrstvy: měkké vrstvy zapadlé, hrany vrstev zaoblené, spáry na hranicích
bed_prof = -0.10 * (1 - HARD) * np.sin(np.pi * np.clip(T, 0, 1)) ** 0.7
dz0 = Z - Z0; dz1 = Z1 - Z
gw = 0.14 + 0.14 * groove[K]
bed_groove = -(0.08 + 0.42 * groove[K]) * np.exp(-(dz0 / gw) ** 2) - (0.08 + 0.42 * groove[np.minimum(K + 1, len(groove) - 1)]) * np.exp(-(dz1 / gw) ** 2)
n_ang = vnoise(2.5, 1.0, 1)            # mění hloubku spár kolem dokola
bed_term = (bed_prof * 2.0 + bed_groove) * (0.6 + 0.4 * np.tanh(n_ang))

sdf = None
for ci, c in enumerate(C):
    H = c["H"]
    cx = c["off"][0] + c["lean"][0] * np.clip(Z, 0, None) + 0.002 * c["lean"][0] * np.clip(Z, 0, None) ** 2
    cy = c["off"][1] + c["lean"][1] * np.clip(Z, 0, None)
    dx = X - cx; dy = Y - cy
    cr, sr = math.cos(c["rot"]), math.sin(c["rot"])
    u = dx * cr + dy * sr; v = -dx * sr + dy * cr
    zr = np.clip(Z / H, 0, 1)
    s = np.ones_like(Z)
    s *= 1.0 - c["needle"] * zr ** 1.3                               # jehla se zužuje
    s *= 1.0 - c["waist"] * np.exp(-((zr - 0.25) / 0.2) ** 2)         # měkčí pata – mírný pas
    s *= 1.0 + 0.06 * (1 - zr)                                        # suť a širší pata
    if c["head"]:
        s *= 1.0 + c["head"] * sst(0.70, 0.74, zr) - 0.3 * c["head"] * np.exp(-((zr - 0.66) / 0.06) ** 2)
    a, b, n = c["a"], c["b"], c["n"] + 1.3
    rho = (np.abs(u / a) ** n + np.abs(v / b) ** n) ** (1.0 / n)
    rmin = min(a, b)
    side = (rho - s) * rmin                                           # ~ metry
    side -= bed_term * (0.7 + 0.6 * (1 - HARD))
    # vrchol: zaoblená kupole
    dome = 0.05 + 0.06 * rng.random()
    top = Z - (H - dome * rmin * (rho / np.maximum(s, 0.2)) ** 2 * 2.0)
    d = smax(side, top, 0.6)
    sdf = d if sdf is None else smin(sdf, d, 0.5)

# velké tvarové nepravidelnosti
sdf += vnoise(5.0, 0.13, 2) + vnoise(1.5, 0.05, 3)
# svislé pukliny (vertikální puklinový systém)
for j in range(rng.randint(3, 5) + 2 * (len(C) - 1)):
    th = rng.uniform(0, math.pi)
    nx, ny = math.cos(th), math.sin(th)
    ci = rng.randrange(len(C)); c = C[ci]
    d0 = rng.uniform(-0.6, 0.6) * min(c["a"], c["b"]) + c["off"][0] * nx + c["off"][1] * ny
    dist = X * nx + Y * ny - d0 - (c["lean"][0] * nx + c["lean"][1] * ny) * np.clip(Z, 0, None)
    dist += vnoise(3.0, 0.08, 10 + j)
    zlo = rng.uniform(-1, HMAX * 0.5); zhi = rng.uniform(zlo + 5, HMAX + 2)
    zmask = sst(zlo - 1, zlo + 1, Z) * sst(zhi + 1, zhi - 1, Z)
    w = (0.06 + 0.12 * rng.random()) * zmask
    depth = rng.uniform(0.6, 2.2)
    sdf = np.maximum(sdf, np.minimum(w - np.abs(dist), sdf + depth * zmask))
# spodek: rovný řez 1 m pod terénem
sdf = np.maximum(sdf, -1.0 - Z)

verts, faces, nrm, _ = measure.marching_cubes(sdf, level=0.0, spacing=(VX, VX, VX))
verts += np.array([xs[0], ys[0], zs[0]])
print("mc verts", len(verts), "faces", len(faces))
me = bpy.data.meshes.new("rock_hi")
me.from_pydata(verts.tolist(), [], faces.tolist())
obj = bpy.data.objects.new("rock_hi", me); bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj; obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
sm = obj.modifiers.new("sm", 'SMOOTH'); sm.factor = 0.5; sm.iterations = 4
bpy.ops.object.modifier_apply(modifier="sm")
rem = obj.modifiers.new("rem", 'REMESH'); rem.mode = 'VOXEL'; rem.voxel_size = float(sys.argv[4]) if len(sys.argv) > 4 else 0.04
bpy.ops.object.modifier_apply(modifier="rem")
me = obj.data

def get(me, a="co"):
    arr = np.empty(len(me.vertices) * 3); me.vertices.foreach_get(a, arr); return arr.reshape(-1, 3)
co = get(me); nor = get(me, "normal")
print("hi verts", len(co))

def fbm(p, octaves=3, ntype='PERLIN_ORIGINAL'):
    out = np.zeros(len(p)); amp, f = 1.0, 1.0
    for _ in range(octaves):
        out += amp * np.array([noise.noise(Vector(v * f), noise_basis=ntype) for v in p]); amp *= 0.5; f *= 2.0
    return out

k, t, z0, z1 = layer_info(co[:, 2])
hv = hard[k]
side = 1.0 - sst(0.6, 0.92, np.abs(nor[:, 2]))
under = sst(-0.1, -0.6, nor[:, 2])                      # spodní strany převisů
disp = np.zeros(len(co))
# voštiny: měkké vrstvy a spodky převisů
hc = np.clip(sst(0.55, 0.15, hv) * side + under, 0, 1) * sst(-0.2, 0.3, fbm(co * 0.25 + 61.0, 2))
idx = np.where(hc > 0.02)[0]
if len(idx):
    f21 = np.empty(len(idx))
    for ii, i in enumerate(idx):
        d_, _ = noise.voronoi(Vector(co[i] * 7.0 + 13.0), distance_metric='DISTANCE'); f21[ii] = d_[1] - d_[0]
    disp[idx] -= 0.045 * hc[idx] * sst(0.0, 0.25, f21)
honey = np.zeros(len(co)); honey[idx] = hc[idx]
# drobné pukliny
cr = np.zeros(len(co))
for ii, v in enumerate(co * 0.6 + 8.0):
    d_, _ = noise.voronoi(Vector(v), distance_metric='DISTANCE'); cr[ii] = d_[1] - d_[0]
crack = np.exp(-(cr / 0.025) ** 2) * sst(0.1, 0.5, fbm(co * 0.35 + 33.0, 2))
disp -= 0.05 * crack
disp += 0.03 * fbm(co * 1.6 + 2.0, 3) + 0.012 * fbm(co * 5.0 + 9.0, 2)
co += nor * disp[:, None]
me.vertices.foreach_set("co", co.ravel()); me.update()
for p in me.polygons: p.use_smooth = True

# stékance: pod převisy a římsami (kde nad bodem vystupuje skála) + náhodné dráhy
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
drip = np.zeros(len(co))
sub = np.arange(0, len(co), 1)
for i in sub:
    p = Vector(co[i]) + Vector(nor[i]) * 0.05
    hit = bvh.ray_cast(p, Vector((0, 0, 1)), 6.0)
    if hit[0] is not None:
        drip[i] = 1.0 - hit[3] / 6.0
drip = np.clip(drip * side, 0, 1)
for nm, arr in (("strata", (k + t) / 6.0), ("honey", honey), ("crack", np.clip(crack, 0, 1)), ("drip", drip)):
    at = me.attributes.new(nm, 'FLOAT', 'POINT'); at.data.foreach_set("value", arr.astype(np.float32))
obj["rtype"] = "piskovec"; obj["mat_scale"] = 1.0; obj["tower"] = 1; obj["H"] = HMAX
print("dims", tuple(round(x, 2) for x in obj.dimensions), "faces", len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
