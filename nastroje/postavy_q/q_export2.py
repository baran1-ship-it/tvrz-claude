"""Export hrdiny v dobovém oblečení (q_postava.py s "kroj") do Godotu – rozpočet a textury podle rádce:
  hlava (kůže hlavy a krku, výstřih, oči, obočí+řasy, vlasy) -> atlas 1024 (RGBA: barva+alfa, normála, ORM)
  tělo (ruce, paže, trup, nohy) + všechno oblečení       -> atlas 1024 (barva, normála, ORM), AO zapečené
  tělo rozdělené na díly; kusy oblečení zvlášť; <jmeno>_sada.json říká, které díly kus zakrývá.
python3 q_export2.py <jmeno> <postava.blend> <vystup>
"""
import bpy, bmesh, sys, os, json, math, numpy as np, cv2
from mathutils import Vector
NAME, BLEND, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
CFG = json.load(open("/home/claude/chars/q/postavy.json"))[NAME]
KROJ = CFG["kroj"]
TD = os.path.join(OUT, "textury"); os.makedirs(TD, exist_ok=True)
A = 512 if CFG.get("npc") else 1024
bpy.ops.wm.open_mainfile(filepath=BLEND)
arm = bpy.data.objects[f"{NAME}_kostra"]
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT') or o.name == "Plane": bpy.data.objects.remove(o)
bpy.context.view_layer.update()

def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
def sel_only(objs, active=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.hide_set(False); o.hide_viewport = False; o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]
def tex_of(m, key="Base Color"):
    if m is None or not m.use_nodes: return None
    b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is None: return None
    st = [l.from_node for l in b.inputs[key].links]; seen = set()
    while st:
        n = st.pop()
        if n.name in seen: continue
        seen.add(n.name)
        if n.type == 'TEX_IMAGE' and n.image: return n.image
        for i in n.inputs: st += [l.from_node for l in i.links]
    return None
def img_path(im):
    p = bpy.path.abspath(im.filepath_raw or im.filepath)
    return p if os.path.exists(p) else None
_cache = {}
def load_img(path, alpha=False):
    k = (path, alpha)
    if k not in _cache:
        flag = cv2.IMREAD_UNCHANGED
        a = cv2.imread(path, flag)
        if a is None: _cache[k] = None
        else:
            if a.ndim == 2: a = cv2.cvtColor(a, cv2.COLOR_GRAY2BGRA)
            if a.shape[2] == 3: a = cv2.cvtColor(a, cv2.COLOR_BGR2BGRA)
            if a.dtype != np.uint8: a = (a / 257).astype(np.uint8)
            _cache[k] = a
    return _cache[k]

body = bpy.data.objects[f"{NAME}_hlava"]          # celé tělo (v režimu kroj)
for m in list(body.modifiers):
    if m.type == 'MASK': body.modifiers.remove(m)
eyes = bpy.data.objects[f"{NAME}_oci"]; brows = bpy.data.objects[f"{NAME}_oboci"]
hairs = [o for o in bpy.data.objects if o.type == 'MESH' and "_hair_" in o.name]
GAR = {}   # kus -> objekty
import importlib; sys.path.insert(0, "/home/claude/chars/q"); sys.path.insert(0, "/home/claude/chars")
KUS_OF = {"kosile": "kosile", "svrchni_h": None, "svrchni_d": None, "nohavice": "nohavice", "skorne": "skorne", "opasek": "opasek",
          "kapuce": "kape", "limec": "kape", "rouska": "rouska", "rouska_cip": "rouska"}
main_k = "cotte" if KROJ.get("zena") else "kotle"
for o in bpy.data.objects:
    if o.type != 'MESH' or o.parent != arm or o in (body, eyes, brows) or o in hairs: continue
    suf = o.name[len(NAME) + 1:]
    k = KUS_OF.get(suf, suf)
    if k is None: k = main_k
    GAR.setdefault(k, []).append(o); o.hide_render = False
for o in [body, eyes, brows] + hairs: o.hide_render = False
print("KUSY", {k: [o.name for o in v] for k, v in GAR.items()})

# --- 1) tělo na díly podle kostí
NZ = (arm.matrix_world @ arm.data.bones['neck_01'].head_local).z
SEG = {"hlava": ("Head", "neck_01", "neck_02"), "ruce": ("hand_", "thumb", "index", "middle", "ring", "pinky"),
       "paze": ("upperarm", "lowerarm"), "trup": ("pelvis", "spine", "clavicle"), "stehna": ("thigh",), "lytka": ("calf",),
       "chodidla": ("foot", "ball")}
vg = {g.index: g.name for g in body.vertex_groups}
vseg = []
for v in body.data.vertices:
    acc = {}
    for ge in v.groups:
        bn = vg[ge.group]
        for s, keys in SEG.items():
            if any(bn.startswith(k) for k in keys): acc[s] = acc.get(s, 0) + ge.weight
    vseg.append(max(acc, key=acc.get) if acc else "trup")
CO = np.array([body.matrix_world @ v.co for v in body.data.vertices])
fseg = []
for p in body.data.polygons:
    ss_ = [vseg[i] for i in p.vertices]; s = max(set(ss_), key=ss_.count)
    c = CO[list(p.vertices)].mean(0)
    if s in ("trup", "paze"):
        # výstřih zůstává viditelný: o 2–3 cm větší než výstřih svrchního šatu (vpředu i vzadu)
        front = c[1] < 0.02 and (c[0] / 0.12) ** 2 + ((c[2] - (NZ - 0.012)) / 0.1) ** 2 < 1.0
        back = c[1] >= 0.02 and (c[0] / 0.11) ** 2 + ((c[2] - (NZ + 0.018)) / 0.065) ** 2 < 1.0
        if front or back: s = "dekolt"
    fseg.append(s)
PARTS = {}
for s in sorted(set(fseg)):
    sel_only([body]); bpy.ops.object.duplicate(); d = bpy.context.view_layer.objects.active
    bm = bmesh.new(); bm.from_mesh(d.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if fseg[f.index] != s], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(d.data); bm.free()
    d.name = f"{NAME}_telo_{s}"; d.data.name = d.name; PARTS[s] = d
bpy.data.objects.remove(body)
print("DILY", {s: tris(o) for s, o in PARTS.items()})

# --- 2) decimace na rozpočet (hlava, oči, vlasy beze změny)
DEC = {"trup": 0.55, "paze": 0.6, "stehna": 0.55, "lytka": 0.55, "chodidla": 0.6, "ruce": 0.6}
TGT = {"kosile": 1200, main_k: 2200 if main_k == "kotle" else 2600, "nohavice": 900, "skorne": 700, "opasek": 200, "kape": 1100, "rouska": 1100}
if CFG.get("npc"):
    # NPC ≤ 8 000 troj.: hlava, ruce, oči, obočí i oblečení úsporněji
    DEC = {"trup": 0.35, "paze": 0.4, "stehna": 0.35, "lytka": 0.35, "chodidla": 0.4, "ruce": 0.33, "hlava": 0.5, "dekolt": 1.0}
    TGT = {"kosile": 500, main_k: 1400 if main_k == "kotle" else 1700, "nohavice": 450, "skorne": 380, "opasek": 120, "kape": 600, "rouska": 650}
def decimate(o, ratio, keep_edges=False):
    if ratio >= 0.99: return
    if keep_edges:
        b2 = bmesh.new(); b2.from_mesh(o.data)
        edge = {v.index for e in b2.edges if e.is_boundary for v in e.verts}; b2.free()
        g = o.vertex_groups.get("_dec") or o.vertex_groups.new(name="_dec")
        for i in range(len(o.data.vertices)): g.add([i], 0.05 if i in edge else 1.0, 'REPLACE')
    sel_only([o]); md = o.modifiers.new("dec", 'DECIMATE'); md.ratio = ratio
    if keep_edges: md.vertex_group = "_dec"; md.vertex_group_factor = 1.0
    while o.modifiers.find("dec") > 0: bpy.ops.object.modifier_move_up(modifier="dec")
    bpy.ops.object.modifier_apply(modifier="dec")
    if "_dec" in o.vertex_groups: o.vertex_groups.remove(o.vertex_groups["_dec"])
for s, r in DEC.items():
    if s in PARTS: decimate(PARTS[s], r)
for k, objs in GAR.items():
    t = sum(tris(o) for o in objs)
    if k in TGT and t > TGT[k]:
        for o in objs: decimate(o, TGT[k] / t, keep_edges=True)
if CFG.get("npc"):
    decimate(eyes, 0.5); decimate(brows, 0.5)
    th = sum(tris(h) for h in hairs)
    if th > 900:
        for h in hairs: decimate(h, 900 / th)
# všechno na trojúhelníky (atlas se přenáší po trojúhelnících)
for o in list(PARTS.values()) + [eyes, brows] + hairs + [o for v in GAR.values() for o in v]:
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free()

# --- 3) atlasy: nová UV "atlas", zabalení ostrovů bez rotace (tečné normály zůstanou platné)
def pack(objs, density):
    for o in objs:
        uv = o.data.uv_layers
        src = uv.active
        if "atlas" in uv: uv.remove(uv["atlas"])
        dst = uv.new(name="atlas")
        if src is not None:
            buf = np.zeros(len(o.data.loops) * 2, np.float32); src.data.foreach_get("uv", buf); dst.data.foreach_set("uv", buf)
        uv.active = dst
    sel_only(objs)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in objs:
        f = density.get(o.name, 1.0)
        dst = o.data.uv_layers["atlas"]; buf = np.zeros(len(o.data.loops) * 2, np.float32); dst.data.foreach_get("uv", buf)
        dst.data.foreach_set("uv", buf * f)
    sel_only(objs)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.select_all(action='SELECT')
    try:
        bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=False, scale=True, margin_method='FRACTION', margin=0.01)
    except TypeError:
        bpy.ops.uv.pack_islands(rotate=False, margin=0.006)
    bpy.ops.object.mode_set(mode='OBJECT')
    # původní UV (zdroj) = první vrstva, která není "atlas"
    for o in objs:
        o.data.uv_layers.active = o.data.uv_layers["atlas"]

HEAD = [PARTS["hlava"]] + ([PARTS["dekolt"]] if "dekolt" in PARTS else []) + [eyes, brows] + hairs
BODY = [o for s, o in PARTS.items() if s not in ("hlava", "dekolt")] + [o for v in GAR.values() for o in v]
dens_h = {PARTS["hlava"].name: 1.0, eyes.name: 0.55, brows.name: 0.6}
if "dekolt" in PARTS: dens_h[PARTS["dekolt"].name] = 0.7
for h in hairs: dens_h[h.name] = 0.55
dens_b = {}
for s, o in PARTS.items():
    if s == "ruce": dens_b[o.name] = 1.4
    elif s not in ("hlava", "dekolt"): dens_b[o.name] = 0.8
for k, objs in GAR.items():
    for o in objs: dens_b[o.name] = 1.0
pack(HEAD, dens_h); pack(BODY, dens_b)

def tri_lists(o):
    """[(src_uv (3,2), dst_uv (3,2), material_index)]"""
    me = o.data; src = next(u for u in me.uv_layers if u.name != "atlas"); dst = me.uv_layers["atlas"]
    out = []
    for p in me.polygons:
        li = list(p.loop_indices)
        out.append((np.array([src.data[i].uv[:] for i in li]), np.array([dst.data[i].uv[:] for i in li]), p.material_index))
    return out
def warp_into(atlas, mask, srcimg, tri_src, tri_dst):
    H, W = srcimg.shape[:2]
    ps = np.float32([[u * W, (1 - v) * H] for u, v in tri_src])
    pd = np.float32([[u * A, (1 - v) * A] for u, v in tri_dst])
    x0, y0 = np.floor(pd.min(0)).astype(int) - 2; x1, y1 = np.ceil(pd.max(0)).astype(int) + 2
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, A), min(y1, A)
    if x1 <= x0 or y1 <= y0: return
    pl = pd - np.float32([x0, y0])
    try: M = cv2.getAffineTransform(pl, ps)
    except cv2.error: return
    if not np.isfinite(M).all(): return
    patch = cv2.warpAffine(srcimg, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_WRAP)
    mk = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.fillConvexPoly(mk, np.round(pl * 4).astype(np.int32), 255, lineType=cv2.LINE_8, shift=2)
    mk = cv2.dilate(mk, np.ones((3, 3), np.uint8))
    sub = atlas[y0:y1, x0:x1]; m3 = mk > 0
    sub[m3] = patch[m3]; mask[y0:y1, x0:x1][m3] = 255
def fill_tri(atlas, mask, tri_dst, pattern):
    pd = np.float32([[u * A, (1 - v) * A] for u, v in tri_dst])
    x0, y0 = np.floor(pd.min(0)).astype(int) - 2; x1, y1 = np.ceil(pd.max(0)).astype(int) + 2
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, A), min(y1, A)
    if x1 <= x0 or y1 <= y0: return
    mk = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillConvexPoly(mk, np.round((pd - np.float32([x0, y0])) * 4).astype(np.int32), 255, shift=2)
    mk = cv2.dilate(mk, np.ones((3, 3), np.uint8)); m3 = mk > 0
    atlas[y0:y1, x0:x1][m3] = pattern[y0:y1, x0:x1][m3]; mask[y0:y1, x0:x1][m3] = 255
def pad(img, mask, it=12):
    img = img.copy(); m = mask > 0
    for _ in range(it):
        dil = cv2.dilate(img, np.ones((3, 3), np.uint8))
        mb = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        new = mb & ~m
        img[new] = dil[new]; m = mb
    return img
FLAT_N = np.array([255, 128, 128, 255], np.uint8)      # BGRA plochá normála (128,128,255)
def bgra(rgb, a=255):
    return np.array([rgb[2], rgb[1], rgb[0], a], np.uint8)

def build_atlas(objs, label, garments=None):
    col = np.zeros((A, A, 4), np.uint8); nor = np.zeros((A, A, 4), np.uint8); nor[:] = FLAT_N
    rgh = np.zeros((A, A, 4), np.uint8); rgh[:] = bgra((255, 200, 0))
    mask = np.zeros((A, A), np.uint8); mn = np.zeros((A, A), np.uint8); mr = np.zeros((A, A), np.uint8)
    dirt = np.zeros((A, A), np.uint8); dmk = np.zeros((A, A), np.uint8)
    gar_of = {}
    for k, v in (garments or {}).items():
        for o in v: gar_of[o.name] = k
    pats = {}
    for o in objs:
        tl = tri_lists(o)
        if o.name in gar_of:
            k = gar_of[o.name]
            if k not in pats: pats[k] = fabric_pattern(k)
            pc, pr = pats[k]
            skirt = o.name.endswith(("_svrchni_d",)) or "rouska_cip" in o.name or "limec" in o.name
            dw = dirt_weights(o, k)
            for ti, (s_, d, _m) in enumerate(tl):
                fill_tri(col, mask, d, pc); fill_tri(rgh, mr, d, pr)
                if skirt: warp_into(nor, mn, FOLDS, s_, d)
                if dw[ti] > 0.02: fill_tri(dirt, dmk, d, np.broadcast_to(np.uint8(min(255, dw[ti] * 255)), (A, A)))
            continue
        mats = o.data.materials
        for mi, m in enumerate(mats):
            ic = tex_of(m); inn = tex_of(m, "Normal"); ir = tex_of(m, "Roughness")
            sc = load_img(img_path(ic)) if ic is not None and img_path(ic) else None
            sn = load_img(img_path(inn)) if inn is not None and img_path(inn) else None
            sr = load_img(img_path(ir)) if ir is not None and img_path(ir) else None
            if sc is None:
                print("BEZ TEXTURY", o.name, m.name if m else None); continue
            hair_like = "_hair_" in o.name or o.name.endswith("_oboci")
            for s, d, pm in tl:
                if pm != mi: continue
                warp_into(col, mask, sc, s, d)
                if sn is not None: warp_into(nor, mn, sn, s, d)
                if sr is not None:
                    warp_into(rgh, mr, sr, s, d)
            if sr is None or hair_like:
                rv = 190 if hair_like else 150
                for s, d, pm in tl:
                    if pm == mi: fill_tri(rgh, mr, d, np.broadcast_to(bgra((255, rv, 0)), (A, A, 4)))
    # ušpinění/ošoupání: tmavší, do hlinité barvy, rozmazané
    if dirt.max() > 0:
        dm = cv2.GaussianBlur(dirt.astype(np.float32) / 255, (0, 0), A / 256 * 2.5)
        rng_ = np.random.default_rng(9); nz = cv2.resize(rng_.random((A // 8, A // 8)).astype(np.float32), (A, A), interpolation=cv2.INTER_CUBIC)
        dm = np.clip(dm * (0.6 + 0.8 * nz), 0, 1)[..., None] * 0.55
        earth = np.array([40, 52, 62], np.float32)            # BGR hlína
        c3 = col[..., :3].astype(np.float32)
        col[..., :3] = np.clip(c3 * (1 - dm) + (c3 * 0.55 + earth * 0.45) * dm, 0, 255).astype(np.uint8)
    # drsnost: zdroj (Quaternius) má drsnost v R/G/B šedě -> do G kanálu ORM
    g = rgh[..., 1].copy() if rgh[..., 1].max() > 0 else rgh[..., 2]
    orm = np.dstack([np.zeros_like(g), g, np.full_like(g, 255), np.full_like(g, 255)])   # BGRA: B=0(metal), G=rough, R=1(AO)
    colp = pad(col, mask, 24); norp = pad(nor, np.maximum(mn, mask), 24); ormp = pad(orm, np.maximum(mr, mask), 24)
    return colp, norp, ormp, mask

# záhyby sukní: normála ve zdrojovém UV trubky (u = obvod, v = 1 nahoře .. 0 lem), sílí k lemu
def _folds(n=512):
    rng = np.random.default_rng(4)
    u = np.linspace(0, 1, n, endpoint=False)[None, :]; v = np.linspace(1, 0, n)[:, None]
    ph = np.zeros((1, n))
    for k_, a_ in ((9, 1.0), (14, 0.45), (5, 0.6)):
        ph = ph + a_ * np.sin(2 * np.pi * (k_ * u + rng.random()))
    amp = 0.18 + 0.55 * (1 - v) ** 1.2
    dx = np.gradient(ph, axis=1) * n / (2 * np.pi * 9) * amp
    nx = -dx; ny = np.zeros_like(nx); nz_ = np.ones_like(nx)
    L = np.sqrt(nx ** 2 + ny ** 2 + nz_ ** 2)
    img = np.dstack([(nz_ / L * 0.5 + 0.5), (ny / L * 0.5 + 0.5), (nx / L * 0.5 + 0.5)])      # BGR = (z, y, x)
    out = np.dstack([(img * 255).astype(np.uint8), np.full((n, n), 255, np.uint8)])
    return out
FOLDS = _folds()
def dirt_weights(o, k):
    """ušpinění po trojúhelnících: lem dole (země), lokty, kolena, boty celé"""
    mw = o.matrix_world
    V = np.array([mw @ v.co for v in o.data.vertices])
    C = np.array([V[list(p.vertices)].mean(0) for p in o.data.polygons]) if len(o.data.polygons) else np.zeros((0, 3))
    w = np.zeros(len(C))
    if len(C) == 0: return w
    w += np.clip((0.35 - C[:, 2]) / 0.3, 0, 1) * 0.9                       # u země
    for b in ("lowerarm_l", "lowerarm_r", "calf_l", "calf_r"):
        p = np.array(arm.matrix_world @ arm.data.bones[b].head_local)
        w += np.clip(1 - np.linalg.norm(C - p, axis=1) / 0.07, 0, 1) * 0.6
    if k == "skorne": w += 0.35
    return np.clip(w, 0, 1)
def fabric_pattern(k):
    """barva + drsnost látky pro kus k v prostoru atlasu"""
    druh, barva = MATS[k]
    rng = np.random.default_rng(abs(hash(k)) % 1000)
    yy, xx = np.mgrid[0:A, 0:A].astype(np.float32)
    n1 = cv2.resize(rng.random((A // 16, A // 16)).astype(np.float32), (A, A), interpolation=cv2.INTER_CUBIC)
    n2 = rng.random((A, A)).astype(np.float32)
    if druh == "kuze":
        lum = 0.85 + 0.25 * (n1 - 0.5) + 0.06 * (n2 - 0.5); rough = 150
    elif druh == "len":
        weave = 0.5 + 0.5 * np.sin(xx * np.pi / 1.5) * np.sin(yy * np.pi / 1.5)
        lum = 0.92 + 0.08 * (n1 - 0.5) + 0.06 * (weave - 0.5) + 0.04 * (n2 - 0.5); rough = 215
    else:
        weave = 0.5 + 0.5 * np.sin((xx + yy) * np.pi / 2.0)
        lum = 0.9 + 0.14 * (n1 - 0.5) + 0.07 * (weave - 0.5) + 0.06 * (n2 - 0.5); rough = 230
    c = np.clip(np.array(barva, np.float32)[None, None, :] * lum[..., None], 0, 1)
    srgb = np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)
    rgb8 = (np.clip(srgb, 0, 1) * 255).astype(np.uint8)
    col = np.dstack([rgb8[..., 2], rgb8[..., 1], rgb8[..., 0], np.full((A, A), 255, np.uint8)])
    r = np.zeros((A, A, 4), np.uint8); r[..., 1] = rough; r[..., 0] = 0; r[..., 2] = 255; r[..., 3] = 255
    return col, r

sys.path.insert(0, "/home/claude/chars/q")
MATS = {}
for k in GAR:
    MATS[k] = {"kosile": ("len", KROJ.get("kosile", [0.78, 0.74, 0.64])), "kotle": ("vlna", KROJ["barva"]), "cotte": ("vlna", KROJ["barva"]),
               "nohavice": ("vlna", KROJ.get("nohavice", [0.24, 0.22, 0.18])), "skorne": ("kuze", KROJ.get("skorne", [0.2, 0.13, 0.08])),
               "opasek": ("kuze", KROJ.get("opasek", [0.16, 0.1, 0.06])), "kape": ("vlna", KROJ.get("kape_barva", [0.3, 0.28, 0.2])),
               "rouska": ("len", KROJ.get("rouska_barva", [0.86, 0.84, 0.78]))}.get(k, ("vlna", [0.3, 0.3, 0.3]))

hc, hn, ho, hm = build_atlas(HEAD, "hlava")
bc, bn, bo, bmk = build_atlas(BODY, "telo", GAR)

# --- 4) materiály s atlasy, AO zapečené do těla+oblečení
def save(a, nm, alpha=False):
    p = os.path.join(TD, nm)
    if alpha: cv2.imwrite(p, a)
    else: cv2.imwrite(p, a[..., :3])
    return p
pc_h = save(hc, f"{NAME}_hlava_barva.png", alpha=True); pn_h = save(hn, f"{NAME}_hlava_normal.png"); po_h = save(ho, f"{NAME}_hlava_orm.png")
def make_mat(nm, pc, pn, po, alpha=None):
    m = bpy.data.materials.new(nm); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs[0])
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "atlas"
    def t(p, cs):
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(p, check_existing=True); n.image.colorspace_settings.name = cs
        nt.links.new(uvn.outputs[0], n.inputs["Vector"]); return n
    tc = t(pc, 'sRGB'); nt.links.new(tc.outputs["Color"], b.inputs["Base Color"])
    if alpha: nt.links.new(tc.outputs["Alpha"], b.inputs["Alpha"])
    tn = t(pn, 'Non-Color'); nm_ = nt.nodes.new("ShaderNodeNormalMap"); nm_.uv_map = "atlas"
    nt.links.new(tn.outputs["Color"], nm_.inputs["Color"]); nt.links.new(nm_.outputs[0], b.inputs["Normal"])
    to = t(po, 'Non-Color'); sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(to.outputs["Color"], sp.inputs[0])
    nt.links.new(sp.outputs[1], b.inputs["Roughness"]); nt.links.new(sp.outputs[2], b.inputs["Metallic"])
    if alpha:
        try: m.blend_method = 'CLIP'
        except Exception: pass
        m.use_backface_culling = False
    return m
M_kuze = make_mat(f"{NAME}_telo_kuze", pc_h, pn_h, po_h)
M_vlasy = make_mat(f"{NAME}_vlasy", pc_h, pn_h, po_h, alpha=True)
M_rasy = make_mat(f"{NAME}_rasy_oboci", pc_h, pn_h, po_h, alpha=True)
M_oci = make_mat(f"{NAME}_oci", pc_h, pn_h, po_h)
def setmat(o, m):
    o.data.materials.clear(); o.data.materials.append(m)
    for p in o.data.polygons: p.material_index = 0
setmat(PARTS["hlava"], M_kuze)
if "dekolt" in PARTS: setmat(PARTS["dekolt"], M_kuze)
setmat(eyes, M_oci); setmat(brows, M_rasy)
for h in hairs: setmat(h, M_vlasy)
# AO pro tělo + výchozí oblečení (jedno pečení, ostatní kusy zvlášť s tělem)
pc_b = save(bc, f"{NAME}_telo_barva.png"); pn_b = save(bn, f"{NAME}_telo_normal.png"); po_b = save(bo, f"{NAME}_telo_orm.png")
scn = bpy.context.scene; scn.render.engine = 'CYCLES'; scn.cycles.samples = 24; scn.cycles.device = 'CPU'
ao_img = bpy.data.images.new("ao", A, A, alpha=False); ao_img.colorspace_settings.name = 'Non-Color'
aom = bpy.data.materials.new("ao_bake"); aom.use_nodes = True
an = aom.node_tree.nodes.new("ShaderNodeTexImage"); an.image = ao_img
au = aom.node_tree.nodes.new("ShaderNodeUVMap"); au.uv_map = "atlas"; aom.node_tree.links.new(au.outputs[0], an.inputs["Vector"])
aom.node_tree.nodes.active = an
default = KROJ.get("vychozi", list(GAR))
HIDE = {"kosile": ["trup", "paze"], main_k: ["trup", "paze", "stehna"] + (["lytka"] if main_k == "cotte" else []),
        "nohavice": ["stehna", "lytka"], "skorne": ["chodidla"], "opasek": [], "kape": [], "rouska": []}
def bake_ao(objs, visible):
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o not in visible
    saved = {o.name: list(o.data.materials) for o in objs}
    for o in objs: o.data.materials.clear(); o.data.materials.append(aom)
    sel_only(objs); scn.render.bake.margin = 4; scn.render.bake.use_clear = False
    bpy.ops.object.bake(type='AO')
    for o in objs:
        o.data.materials.clear()
        for m in saved[o.name]: o.data.materials.append(m)
ao_img.pixels[:] = np.ones(A * A * 4, np.float32)
hidden_def = set(s for k in default for s in HIDE.get(k, []))
vis_parts = [o for s, o in PARTS.items() if s not in hidden_def]
def_gar = [o for k in default for o in GAR.get(k, [])]
bake_ao([o for o in BODY if o in def_gar or o in vis_parts], vis_parts + def_gar + HEAD)
for k, objs in GAR.items():
    if k in default: continue
    bake_ao(objs, vis_parts + def_gar + objs + HEAD)
hid_parts = [o for s, o in PARTS.items() if s in hidden_def and o in BODY]
if hid_parts: bake_ao(hid_parts, hid_parts + [o for o in vis_parts if o in BODY])
ao = np.array(ao_img.pixels[:], np.float32).reshape(A, A, 4)[::-1, :, 0]
ao = cv2.GaussianBlur(ao, (0, 0), 2.5)
b8 = bc.astype(np.float32); b8[..., :3] *= (0.62 + 0.38 * np.clip(ao, 0, 1))[..., None]
bc = np.clip(b8, 0, 255).astype(np.uint8); save(bc, f"{NAME}_telo_barva.png")
M_druh = {d: make_mat(f"{NAME}_obleceni_{d}", pc_b, pn_b, po_b) for d in ("vlna", "len", "kuze")}
M_tkuze = make_mat(f"{NAME}_telo_kuze_tela", pc_b, pn_b, po_b)
for s, o in PARTS.items():
    if o in BODY: setmat(o, M_tkuze)
# hustota atlasu (UV na metr) -> UV2 "vazba" = atlas * K, dlaždice detailu 2,4 cm (Godot: detail textura vazby na UV2)
_ua = _a3 = 0.0
for k, objs in GAR.items():
    for o in objs:
        uvd = o.data.uv_layers["atlas"].data; mw = o.matrix_world
        for p in o.data.polygons:
            li = list(p.loop_indices); a = Vector(uvd[li[0]].uv); b_ = Vector(uvd[li[1]].uv); c_ = Vector(uvd[li[2]].uv)
            _ua += abs((b_ - a).cross(c_ - a)) / 2
            P3 = [mw @ o.data.vertices[i].co for i in p.vertices]; _a3 += ((P3[1] - P3[0]).cross(P3[2] - P3[0])).length / 2
KV = 1.0 / (math.sqrt(_ua / max(_a3, 1e-9)) * 0.024)
print("VAZBA K", round(KV, 1))
for k, objs in GAR.items():
    druh = MATS[k][0] if MATS[k][0] in M_druh else "vlna"
    for o in objs:
        setmat(o, M_druh[druh])
        src = o.data.uv_layers["atlas"]; dst = o.data.uv_layers.new(name="vazba")
        buf = np.zeros(len(o.data.loops) * 2, np.float32); src.data.foreach_get("uv", buf); dst.data.foreach_set("uv", buf * KV)
        o.data.uv_layers.active = src
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = False
# odstranit původní UV (zůstává jen "atlas" -> v glTF TEXCOORD_0)
for o in HEAD + BODY:
    for u in [u for u in o.data.uv_layers if u.name not in ("atlas", "vazba")]: o.data.uv_layers.remove(u)
    if "atlas" in o.data.uv_layers:
        o.data.uv_layers["atlas"].active = True; o.data.uv_layers["atlas"].active_render = True

# --- 5) oči: tvarový klíč "mrknuti" (víčka + řasy), oči jako dva uzly na kosti Head (pohled)
import q_oci
_bc = np.array([brows.matrix_world @ v.co for v in brows.data.vertices])
_ez = np.array([eyes.matrix_world @ v.co for v in eyes.data.vertices])[:, 2].mean()
q_oci.add_blink(PARTS["hlava"], brows, eyes, lash_mask=_bc[:, 2] < _ez + 0.009)
_eo = q_oci.split_eyes(eyes, arm, NAME)
HEAD = [o for o in HEAD if o.name in bpy.data.objects and o is not eyes] if False else [o for o in HEAD if o != eyes]
HEAD += _eo; eyes = None
# --- 6) export
arm.name = "Armature"
if CFG.get("vyska"): arm.scale = (CFG["vyska"],) * 3          # výška postavy (celá kostra)
def export(objs, path):
    sel_only([arm] + objs, active=arm)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', export_texture_dir="textury", use_selection=True,
                              export_yup=True, export_skins=True, export_animations=False, export_apply=False, export_morph=True, export_morph_normal=False)
TELO = HEAD + [o for s, o in PARTS.items() if o in BODY]
export(TELO, os.path.join(OUT, f"{NAME}_telo.gltf"))
for k, objs in GAR.items():
    for o in objs: o.name = f"{NAME}_{k}" + ("" if len(objs) == 1 else f"_{objs.index(o)}")
    export(objs, os.path.join(OUT, f"{NAME}_{k}.gltf"))
tri = {k: sum(tris(o) for o in objs) for k, objs in GAR.items()}
dil = {s: tris(o) for s, o in PARTS.items()}
dressed = sum(t for s, t in dil.items() if s not in hidden_def) + sum(tris(o) for o in [brows] + hairs + _eo) + sum(tri[k] for k in default)
sada = {"postava": NAME, "telo": f"{NAME}_telo.gltf",
        "dily_tela": {s: f"{NAME}_telo_{s}" for s in PARTS},
        "kusy": {k: {"soubor": f"{NAME}_{k}.gltf", "skryva": HIDE.get(k, []), "trojuhelniky": tri[k], "spodni": k == "kosile"} for k in GAR},
        "vychozi": default, "oblecena_trojuhelniky": dressed,
        "textury": "2 atlasy 1024 (hlava RGBA, tělo+oblečení) – barva, normála, ORM",
        "animace": "UAL1_Standard.glb, UAL2_Standard.glb (stejná kostra Armature/Skeleton3D, bez retargetu)"}
json.dump(sada, open(os.path.join(OUT, f"{NAME}_sada.json"), "w"), indent=1, ensure_ascii=False)
print("SADA", json.dumps(sada, ensure_ascii=False))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"_{NAME}_export.blend"))
