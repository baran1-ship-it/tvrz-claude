# ---------------------------------------------------------------- šum
_tab = np.random.default_rng(SEED).random((8, 256, 256)).astype(np.float32)
def vnoise(x, y, ch=0):
    x = np.asarray(x, np.float32); y = np.asarray(y, np.float32)
    xi = np.floor(x).astype(np.int64); yi = np.floor(y).astype(np.int64)
    fx = x - xi; fy = y - yi; fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    t = _tab[ch % 8]; x0 = xi & 255; y0 = yi & 255; x1 = (xi + 1) & 255; y1 = (yi + 1) & 255
    a = t[x0, y0]; b = t[x1, y0]; c = t[x0, y1]; d = t[x1, y1]
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy
def fbm(x, y, oct=4, ch=0):
    s = 0; amp = 0.5; f = 1.0; n = 0
    for o in range(oct):
        s = s + amp * vnoise(x * f + 17.3 * o, y * f - 9.1 * o, ch + o); n += amp; amp *= 0.5; f *= 2.03
    return s / n
def sm(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)

# ---------------------------------------------------------------- scéna, materiály
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("cycles", default_set=True)
addon_utils.enable("io_scene_gltf2", default_set=True)
scene = bpy.context.scene
prev_col = bpy.data.collections.new("_jen_nahled"); scene.collection.children.link(prev_col)
def to_prev(o):
    for c_ in o.users_collection: c_.objects.unlink(o)
    prev_col.objects.link(o)

def foto(pid, key, srgb=True, res=1024, upravit=None, tag=None):
    from PIL import Image
    src = os.path.join(FOTO, "%s_%s.jpg" % (pid, key))
    dst = os.path.join(TEX, "%s%s_%s.jpg" % (pid, "_" + tag if tag else "", key))
    im = Image.open(src).convert("RGB").resize((res, res), Image.LANCZOS)
    if upravit is not None:
        a = np.asarray(im, np.float32) / 255.0
        im = Image.fromarray((np.clip(upravit(a), 0, 1) * 255).astype(np.uint8))
    im.save(dst, quality=90)
    img = bpy.data.images.load(dst)
    if not srgb: img.colorspace_settings.name = 'Non-Color'
    img.pack()
    return img

def mat(name, pid=None, tag=None, upravit=None, color=(0.5, 0.5, 0.5), rough=0.85, nstr=1.0, rough_mul=None, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    try: b.inputs["Specular IOR Level"].default_value = 0.3        # dřevo, hlína, kámen: slabý odlesk
    except KeyError: pass
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    if pid:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = foto(pid, "diff", upravit=upravit, tag=tag)
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = foto(pid, "nor", False)
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = nstr
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
        if os.path.exists(os.path.join(FOTO, "%s_rough.jpg" % pid)):
            tr = nt.nodes.new("ShaderNodeTexImage")
            rm = rough_mul or (lambda a: 0.62 + 0.38 * a)
            tr.image = foto(pid, "rough", False, upravit=rm, tag=(tag or "r"))
            nt.links.new(tr.outputs["Color"], b.inputs["Roughness"])
    return m

def mossmix(a):
    from PIL import Image
    mr = np.asarray(Image.open(os.path.join(FOTO, "mossy_rock_diff.jpg")).convert("RGB").resize(a.shape[:2][::-1]), np.float32) / 255
    g = np.clip((mr[..., 1] - mr[..., 2]) * 4.0, 0, 1)[..., None]
    return a ** 1.15 * 0.75 * (1 - g * 0.85) + mr * g * 0.85
def tint(c, gamma=1.0):
    return lambda a: (a ** gamma) * np.array(c)
def moss_k(k, dark=0.75, base_tint=(1, 1, 1), lichen=0.0):
    """mech ze skutečné fotky mechového kamene: k = kolik zeleně, lichen = šedobílý lišejník"""
    def f(a):
        from PIL import Image
        mr = np.asarray(Image.open(os.path.join(FOTO, "mossy_rock_diff.jpg")).convert("RGB").resize(a.shape[:2][::-1]), np.float32) / 255
        g = np.clip((mr[..., 1] - mr[..., 2]) * 4.0, 0, 1)[..., None] * k
        out = a ** 1.1 * dark * np.array(base_tint) * (1 - g) + mr * g
        if lichen > 0:
            li = np.clip((mr.mean(2) - 0.55) * 5.0, 0, 1)[..., None] * lichen
            out = out * (1 - li) + np.array([0.70, 0.71, 0.64]) * li
        return out
    return f
def silver(c, sat=0.35, gamma=1.0):
    """sluncem a deštěm vybledlé dřevo: odbarvené do stříbřitě šedé"""
    def f(a):
        a = a ** gamma; g = a.mean(2, keepdims=True)
        return (g + (a - g) * sat) * np.array(c)
    return f

M = {}
M["tram"]     = mat("M_Roubeni", "rough_wood", "tram", silver([0.88, 0.82, 0.74], 0.55, 1.05), nstr=1.4)
M["tram_d"]   = mat("M_RoubeniSpodni", "rough_wood", "tram_d", tint([0.66, 0.60, 0.51], 1.15), nstr=1.3)
M["tram_in"]  = mat("M_RoubeniVnitrni", "rough_wood", "tram_in", tint([0.78, 0.64, 0.48], 1.0), nstr=1.0)     # uvnitř: nezvětralé, hnědší
M["tram_c"]   = mat("M_RoubeniZacouzene", "rough_wood", "tram_c", tint([0.16, 0.13, 0.11], 1.5), nstr=1.0)  # dymná jizba
M["tram_g"]   = mat("M_RoubeniVybledle", "rough_wood", "tram_g", silver([0.84, 0.82, 0.78], 0.35, 1.0), nstr=1.5)        # jižní strana, slunce
M["tram_b"]   = mat("M_RoubeniHnede", "rough_wood", "tram_b", silver([0.66, 0.57, 0.46], 0.7, 1.12), nstr=1.3)                  # pod okapem, chráněné
M["tram_m"]   = mat("M_RoubeniMech", "rough_wood", "tram_m", moss_k(0.75, 0.62, (0.95, 0.9, 0.82), 0.25), nstr=1.3, rough_mul=lambda a: 0.85 + 0.15 * a)
M["tram_l"]   = mat("M_RoubeniLisejnik", "rough_wood", "tram_l", moss_k(0.30, 0.80, (0.95, 0.92, 0.86), 0.55), nstr=1.3)
M["zhlavi_m"] = mat("M_ZhlaviMech", "rough_wood", "zhlavi_m", moss_k(0.6, 0.55, (0.9, 0.82, 0.7), 0.35), nstr=1.6)
M["zhlavi"]   = mat("M_Zhlavi", "rough_wood", "zhlavi", tint([0.62, 0.54, 0.44], 1.2), nstr=1.6)
M["hraz"]     = mat("M_Hrazdeni", "rough_wood", "hraz", tint([0.52, 0.42, 0.32], 1.2), nstr=1.1)
M["mazanice"] = mat("M_Mazanice", "clay_plaster", "maz", tint([0.62, 0.55, 0.45], 1.05), nstr=1.5)
M["mazanice_c"]= mat("M_MazaniceZacouzena", "clay_plaster", "mazc", tint([0.22, 0.19, 0.16], 1.2), nstr=1.5)
M["omitka"]   = mat("M_Omitka", "white_rough_plaster", "om", lambda a: 0.55 * a + 0.38 * np.array([0.88, 0.85, 0.78]), nstr=1.0)
M["prkna"]    = mat("M_StitPrkna", "weathered_planks", "stit", silver([0.95, 0.92, 0.88], 0.45, 1.0))
M["dvere"]    = mat("M_Dvere", "weathered_planks", "dv", silver([0.80, 0.76, 0.70], 0.5, 1.1))
M["podbiti"]  = mat("M_Podbiti", "weathered_planks", "pod", tint([0.70, 0.64, 0.58], 1.1))
M["povala_c"] = mat("M_PovalaZacouzena", "weathered_planks", "povc", tint([0.17, 0.14, 0.12], 1.4))
M["sindel"]   = mat("M_Sindel", "rough_wood", "sin", silver([0.80, 0.77, 0.72], 0.45, 1.05), nstr=1.5, rough_mul=lambda a: 0.75 + 0.25 * a)
M["sindel_m"] = mat("M_SindelMech", "rough_wood", "sinm", moss_k(1.0, 0.62), nstr=1.5, rough_mul=lambda a: 0.85 + 0.15 * a)
M["sindel_m1"]= mat("M_SindelMechSlaby", "rough_wood", "sinm1", moss_k(0.45, 0.72, (0.95, 0.92, 0.86), 0.4), nstr=1.5, rough_mul=lambda a: 0.8 + 0.2 * a)
M["sindel_t"] = mat("M_SindelTmavy", "rough_wood", "sint", silver([0.50, 0.48, 0.45], 0.45, 1.2), nstr=1.5, rough_mul=lambda a: 0.8 + 0.2 * a)   # nasáklý, ztmavlý
M["sindel_n"] = mat("M_SindelNovy", "rough_wood", "sinn", tint([1.20, 1.04, 0.84], 0.8), nstr=1.5, rough_mul=lambda a: 0.75 + 0.25 * a)
M["kamen"]    = mat("M_Kamen", "stone_wall", "k", tint([0.80, 0.78, 0.74], 1.1), nstr=1.4)
M["kamen_m"]  = mat("M_KamenMech", "stone_wall", "km", moss_k(0.9, 0.70), nstr=1.4, rough_mul=lambda a: 0.85 + 0.15 * a)
M["kura"]     = mat("M_Kura", "bark_brown_02", nstr=1.2)
M["hlina"]    = mat("M_Hlina", "dirt_floor", "hl", tint([0.62, 0.55, 0.47], 1.1), nstr=1.0, rough_mul=lambda a: 0.8 + 0.2 * a)
M["pec"]      = mat("M_PecHlina", "clay_plaster", "pec", tint([1.00, 0.88, 0.74], 0.95), nstr=1.6)
M["pec_c"]    = mat("M_PecZacouzena", "clay_plaster", "pecc", tint([0.18, 0.15, 0.12], 1.3), nstr=1.6)
M["zhar"]     = mat("M_Zhar", None, color=(0.05, 0.02, 0.01), rough=1.0, emit=((1.0, 0.32, 0.08), 2.5))
M["tma"]      = mat("M_Tma", None, color=(0.012, 0.010, 0.008), rough=1.0)

# ---------------------------------------------------------------- stavitel sítí
class Mesh:
    def __init__(s, name): s.name = name; s.v = []; s.f = []; s.uv = []; s.m = []; s.mats = []
    def mi(s, key):
        m = M[key]
        if m not in s.mats: s.mats.append(m)
        return s.mats.index(m)
    def face(s, pts, uvs, key):
        b = len(s.v); s.v += [tuple(p) for p in pts]; s.uv += list(uvs)
        s.f.append(tuple(range(b, b + len(pts)))); s.m.append(s.mi(key))
    def build(s, smooth_angle=35, origin=None, merge=True):
        o3 = Vector(origin) if origin else Vector((0, 0, 0))
        me = bpy.data.meshes.new(s.name)
        me.from_pydata([tuple(Vector(v) - o3) for v in s.v], [], s.f)
        ul = me.uv_layers.new(name="UVMap")
        ul.data.foreach_set("uv", np.array([s.uv[i] for f in s.f for i in f], np.float32).ravel())
        for m in s.mats: me.materials.append(m)
        me.polygons.foreach_set("material_index", np.array(s.m, np.int32))
        me.update()
        if merge:
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
            bm.to_mesh(me); bm.free()
        me.shade_smooth()
        try: me.set_sharp_from_angle(angle=math.radians(smooth_angle))
        except Exception: pass
        o = bpy.data.objects.new(s.name, me); scene.collection.objects.link(o)
        o.location = o3
        return o

def box(Ms, c, size, R, key, uvs=1.0, uoff=None):
    c = Vector(c); hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    C = [Vector((sx * hx, sy * hy, sz * hz)) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    quads = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    longest = max(range(3), key=lambda i: size[i])
    ou, ov = uoff if uoff else (random.random() * 3, random.random() * 3)
    for q in quads:
        pts = [C[i] for i in q]
        axes = [i for i in range(3) if abs((pts[1] - pts[0])[i]) + abs((pts[3] - pts[0])[i]) > 1e-6]
        a1 = longest if longest in axes else axes[0]
        a2 = [i for i in axes if i != a1][0] if len(axes) > 1 else a1
        Ms.face([c + R @ p for p in pts], [(p[a2] / uvs + ou, p[a1] / uvs + ov) for p in pts], key)

def prism(Ms, poly2d, origin, ax_u, ax_v, ax_n, depth, key, uvs=1.0, key_side=None, uoff=(0, 0), vgrain=True):
    o = Vector(origin); U = Vector(ax_u); V = Vector(ax_v); N = Vector(ax_n)
    P = lambda u, v, d: o + U * u + V * v + N * d
    # orientace: horní plocha (ve vzdálenosti depth) musí mířit po +N, boky ven
    area = sum(poly2d[i][0] * poly2d[(i + 1) % len(poly2d)][1] - poly2d[(i + 1) % len(poly2d)][0] * poly2d[i][1] for i in range(len(poly2d)))
    if (area > 0) != (U.cross(V).dot(N) * (1 if depth > 0 else -1) > 0):
        poly2d = poly2d[::-1]
    n = len(poly2d)
    uvf = lambda u, v: ((u / uvs + uoff[0], v / uvs + uoff[1]) if vgrain else (v / uvs + uoff[0], u / uvs + uoff[1]))
    Ms.face([P(u, v, depth) for (u, v) in poly2d], [uvf(u, v) for (u, v) in poly2d], key)
    Ms.face([P(u, v, 0) for (u, v) in poly2d[::-1]], [uvf(u, v) for (u, v) in poly2d[::-1]], key)
    ks = key_side or key
    for i in range(n):
        (u0, v0), (u1, v1) = poly2d[i], poly2d[(i + 1) % n]
        el = math.hypot(u1 - u0, v1 - v0)
        Ms.face([P(u0, v0, 0), P(u1, v1, 0), P(u1, v1, depth), P(u0, v0, depth)],
                [(uoff[0], uoff[1]), (uoff[0] + el / uvs, uoff[1]), (uoff[0] + el / uvs, uoff[1] + depth / uvs), (uoff[0], uoff[1] + depth / uvs)], ks)

def clip(poly, a, b, c):
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        fp = a * p[0] + b * p[1] - c; fq = a * q[0] + b * q[1] - c
        if fp <= 0: out.append(p)
        if (fp <= 0) != (fq <= 0):
            t = fp / (fp - fq); out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out
def under_roof(poly, gap=0.04):
    t = math.tan(P_MAIN); zt = ZE + W / 2 * t - gap
    return clip(clip(poly, t, 1, zt), -t, 1, zt)
def roof_x(z):
    return W / 2 - (z - ZE + 0.03) / math.tan(P_MAIN)

