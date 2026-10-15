"""Procedurální high-poly skála (droba / šedý pískovec, 14. stol. Morava).
Spuštění: python3 rock_geo.py <seed> <výstup.blend>
"""
import sys, math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, noise

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7
OUT = sys.argv[2] if len(sys.argv) > 2 else "rock_hi.blend"
TYPE = sys.argv[3] if len(sys.argv) > 3 else "piskovec"     # piskovec | droba
rng = random.Random(SEED)
np.random.seed(SEED)

bpy.ops.wm.read_factory_settings(use_empty=True)

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)

def get_co(me):
    a = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)

def set_co(me, co):
    me.vertices.foreach_set("co", co.astype(np.float32).ravel())
    me.update()

def get_nor(me):
    a = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("normal", a)
    return a.reshape(-1, 3).astype(np.float64)

def fbm(p, octaves=4, lac=2.0, gain=0.5, ntype='PERLIN_ORIGINAL'):
    out = np.zeros(len(p))
    amp, freq = 1.0, 1.0
    for _ in range(octaves):
        out += amp * np.array([noise.noise(Vector(v * freq), noise_basis=ntype) for v in p])
        amp *= gain
        freq *= lac
    return out

# ---------- 1) hrubý tvar: elipsoid + lomové plochy ----------
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=6, radius=1.0)
me = bpy.data.meshes.new("rock_hi")
bm.to_mesh(me); bm.free()
obj = bpy.data.objects.new("rock_hi", me)
bpy.context.collection.objects.link(obj)

co = get_co(me)
co *= np.array([1.55, 1.05, 0.95])                       # podlouhlý balvan ~3,1 x 2,1 x 1,9 m
off = np.array([rng.uniform(0, 50) for _ in range(3)])
co += 0.28 * np.stack([fbm(co * 0.7 + off + i * 13.1, 3) for i in range(3)], 1)

# lomové plochy – kámen se láme po rovinách, ne do kulata
for k in range(15 if TYPE != "zula" else 9):
    th = rng.uniform(0, 2 * math.pi)
    up = rng.uniform(-0.3, 0.75) if k > 1 else rng.uniform(0.75, 0.95)   # první dvě = horní plotny
    n = np.array([math.cos(th) * math.sqrt(1 - up * up), math.sin(th) * math.sqrt(1 - up * up), up])
    proj = co @ n
    d = np.percentile(proj, rng.uniform(74, 93) if TYPE != "zula" else rng.uniform(84, 96))
    over = proj - d
    m = over > 0
    wav = 0.018 * fbm(co[m] * 2.0 + k * 7.7, 2)
    co[m] -= np.outer(over[m] * rng.uniform(0.93, 1.0) - wav, n)

# odštípnuté kusy – lastrurovité vylomeniny na hranách
cen = co.mean(0)
zmin, zmax = co[:, 2].min(), co[:, 2].max()
cand = np.where(co[:, 2] > zmin + 0.35 * (zmax - zmin))[0]
for k in range(22 if TYPE != "zula" else 6):
    i = int(rng.choice(cand))
    p = co[i]
    r = rng.uniform(0.10, 0.30)
    outward = p - cen; outward /= np.linalg.norm(outward)
    rnd = np.array([rng.gauss(0, 1) for _ in range(3)])
    n = outward + 0.6 * rnd / np.linalg.norm(rnd); n /= np.linalg.norm(n)
    plane_d = p @ n - r * rng.uniform(0.18, 0.38)
    dd = np.linalg.norm(co - p, axis=1)
    w = smoothstep(r, r * 0.55, dd)
    over = co @ n - plane_d
    m = (over > 0) & (w > 0)
    # lehce miskovitý lom (konchoidální)
    bowl = 0.25 * (1 - (dd[m] / r) ** 2) * r * 0.25
    co[m] -= np.outer((over[m] + bowl) * w[m], n)

# spodek zaříznutý do terénu
z0 = np.percentile(co[:, 2], 12)
co[:, 2] = np.where(co[:, 2] < z0, z0 + (co[:, 2] - z0) * 0.15, co[:, 2])
co[:, 2] -= z0
# normalizace na cílovou velikost balvanu (~2,6 x 1,8 x 1,5 m)
ext = co.max(0) - co.min(0)
co[:, :2] -= (co.max(0) + co.min(0))[:2] / 2
_sr = random.Random(SEED + 999)
SIZE = float(sys.argv[4]) if len(sys.argv) > 4 else _sr.uniform(0.8, 1.3)
GEN = max(SIZE, 0.6)            # malé kameny se modelují větší a nakonec zmenší (detail škáluje s nimi)
co *= GEN * np.array([2.6 * _sr.uniform(0.9, 1.1), 1.8 * _sr.uniform(0.85, 1.15), 1.5 * _sr.uniform(0.8, 1.2)]) / ext
set_co(me, co)

# zvětralé, oblé hrany pískovce
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
if TYPE in ("piskovec", "zula"):
    big = max(obj.dimensions)
    r0 = obj.modifiers.new("r0", 'REMESH'); r0.mode = 'VOXEL'
    r0.voxel_size = 0.03 if TYPE == "piskovec" else 0.02 * big
    sm = obj.modifiers.new("sm", 'SMOOTH')
    sm.factor = 0.6 if TYPE == "piskovec" else 0.9
    sm.iterations = 5 if TYPE == "piskovec" else 14     # žula: oblé „bochníky“
    bpy.ops.object.modifier_apply(modifier="r0")
    bpy.ops.object.modifier_apply(modifier="sm")
# rovnoměrná síť pro detail
rem = obj.modifiers.new("remesh", 'REMESH')
rem.mode = 'VOXEL'; rem.voxel_size = 0.007; rem.adaptivity = 0.0
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.modifier_apply(modifier="remesh")
me = obj.data
me.update()

# ---------- 2) vrstvy horniny (vrstevnatost droby) ----------
co = get_co(me); nor = get_nor(me)
tilt = np.array([0.22, -0.12, 1.0]); tilt /= np.linalg.norm(tilt)
h = co @ tilt + 0.05 * fbm(co * 1.3 + 3.3, 3)
layer_f = 6.0                                              # vrstvy 10–25 cm, nepravidelně
ph = h * layer_f + 0.45 * fbm(co * 0.45 + 9.0, 2) + 0.25 * np.sin(h * 2.3)
layer_id = np.floor(ph)
frac = ph - layer_id
def lhash(l, s):
    return np.array([(math.sin(x * 12.9898 + s * 78.233) * 43758.5453) % 1.0 for x in l])
r_groove = lhash(layer_id, 1.0) ** 2.5                     # jen některé spáry jsou výrazné
r_soft = lhash(layer_id, 2.0)
side = 1.0 - smoothstep(0.6, 0.92, np.abs(nor @ tilt))
if TYPE == "zula":
    side = side * 0.0          # žula nemá vrstvy
groove = np.exp(-(frac / 0.045) ** 2) + np.exp(-((frac - 1.0) / 0.045) ** 2)
along = smoothstep(-0.25, 0.35, fbm(co * 1.4 + 1.1, 2))    # spára mizí a zase se objeví
disp = -groove * 0.022 * r_groove * along * side
# měkčí vrstvy víc zvětralé = zapadlé, tvrdší vystupují
disp -= 0.016 * smoothstep(0.55, 0.95, r_soft) * side * smoothstep(0.08, 0.2, frac) * smoothstep(0.92, 0.8, frac)

# voštinové zvětrávání v měkčích vrstvách (typické pro Český ráj)
def vor(p, scale):
    f1 = np.zeros(len(p)); f21 = np.zeros(len(p))
    for i, v in enumerate(p * scale):
        dists, _ = noise.voronoi(Vector(v), distance_metric='DISTANCE')
        f1[i] = dists[0]; f21[i] = dists[1] - dists[0]
    return f1, f21
hc_mask = smoothstep(0.6, 0.85, r_soft) * side * smoothstep(-0.1, 0.3, fbm(co * 0.9 + 61.0, 2))
idx = np.where(hc_mask > 0.01)[0] if TYPE == "piskovec" else np.array([], dtype=int)
if len(idx):
    f1, f21 = vor(co[idx] + 13.0, 16.0)
    disp[idx] -= 0.018 * hc_mask[idx] * smoothstep(0.0, 0.22, f21)
honey = np.zeros(len(co)); honey[idx] = hc_mask[idx]

# ---------- 3) pukliny: několik průběžných ploch napříč vrstvami ----------
crack = np.zeros(len(co))
for j in range(3):
    th = rng.uniform(0, 2 * math.pi)
    n = np.array([math.cos(th), math.sin(th), rng.uniform(-0.25, 0.25)]); n /= np.linalg.norm(n)
    d = np.percentile(co @ n, rng.uniform(30, 70))
    dist = co @ n - d + 0.03 * fbm(co * 1.8 + j * 5.1, 3)
    mask = smoothstep(-0.15, 0.25, fbm(co * 0.7 + 21.0 + j, 2))
    width = 0.010 + 0.008 * smoothstep(0.0, 0.6, fbm(co * 2.5 + j * 2.2, 2))
    c = np.exp(-(dist / width) ** 2) * mask
    crack = np.maximum(crack, c)
    disp -= 0.04 * c * (0.15 if SIZE < 0.2 else 1.0)
    # blok za puklinou lehce posunutý – vznikne schodek
    disp += 0.008 * smoothstep(0.0, 0.03, dist) * mask * (1 - side * 0.5) * (0.2 if SIZE < 0.2 else 1.0)

def crack_field(p, scale, width):
    out = np.zeros(len(p))
    for i, v in enumerate(p * scale):
        dists, _ = noise.voronoi(Vector(v), distance_metric='DISTANCE')
        out[i] = dists[1] - dists[0]
    return np.exp(-(out / width) ** 2)

cr_small = crack_field(co + 8.0, 3.2, 0.02) * smoothstep(0.15, 0.5, fbm(co * 1.7 + 33.0, 2))
disp -= 0.007 * cr_small * (0.4 if SIZE < 0.2 else 1.0)
crack = np.maximum(crack, 0.6 * cr_small)

# ---------- 4) zvětrání: důlky, odprýsky, zrnitost ----------
pits = fbm(co * 9.0 + 51.0, 3, ntype='VORONOI_F1')
disp -= 0.006 * smoothstep(0.0, 0.35, -pits + 0.15)
chips = fbm(co * 3.2 + 77.0, 2, ntype='VORONOI_F2F1')
disp -= 0.012 * smoothstep(0.08, 0.0, chips) * smoothstep(0.1, 0.5, fbm(co * 1.1 + 5.0, 2))
disp += 0.011 * fbm(co * 6.0 + 2.0, 4)
# ostřejší hrbolatost lomové plochy (ridged)
rid = 1.0 - np.abs(fbm(co * 11.0 + 41.0, 3))
disp += 0.005 * (rid ** 3 - 0.3)
disp += 0.0025 * fbm(co * 28.0 + 9.0, 2)

# zahrabaný spodek – detail slábne u země
disp *= smoothstep(0.0, 0.12, co[:, 2])

co += nor * disp[:, None]
set_co(me, co)
for p in me.polygons:
    p.use_smooth = True

# atributy pro materiál: výška vrstvy a maska prasklin
attr = me.attributes.new("strata", 'FLOAT', 'POINT')
attr.data.foreach_set("value", (ph / layer_f).astype(np.float32))
attr = me.attributes.new("honey", 'FLOAT', 'POINT')
attr.data.foreach_set("value", honey.astype(np.float32))
attr = me.attributes.new("crack", 'FLOAT', 'POINT')
attr.data.foreach_set("value", (np.clip(crack, 0, 1) * (0.2 if SIZE < 0.2 else 1.0)).astype(np.float32))

print("verts", len(me.vertices), "faces", len(me.polygons),
      "dims", tuple(round(x, 2) for x in obj.dimensions))
if SIZE < GEN:
    co2 = get_co(me) * (SIZE / GEN); set_co(me, co2)
obj["rtype"] = TYPE
obj["mat_scale"] = GEN / SIZE
bpy.ops.wm.save_as_mainfile(filepath=OUT)
