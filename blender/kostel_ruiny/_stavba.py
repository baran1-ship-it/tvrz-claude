# -*- coding: utf-8 -*-
"""Společná stavební knihovna (z kovárny + roubení). Načítá se přes exec() po _spolecne.py a tesar.py.
Před načtením musí být definováno: PFX (předpona jmen objektů do hry)."""

M["zelezo"]  = mat("M_Zelezo", None, color=(0.07, 0.064, 0.058), rough=0.62)
M["zelezo_r"]= mat("M_ZelezoRezave", "rock_surface", "zr", tint([0.20, 0.11, 0.06], 1.3), nstr=0.8)
M["dub"]     = mat("M_Dub", "rough_wood", "dub", silver([0.60, 0.53, 0.44], 0.6, 1.15), nstr=1.7)
M["tram_s"]  = mat("M_RoubeniSaze", "rough_wood", "tram_s", tint([0.42, 0.35, 0.28], 1.2), nstr=1.3)      # uvnitř kovárny, prach a saze
M["tram_c"]  = mat("M_RoubeniZacouzene2", "rough_wood", "tram_c2", tint([0.13, 0.11, 0.095], 1.5), nstr=1.2)
M["kamen_r"] = mat("M_KamenLom", "rock_surface", "kr", tint([0.74, 0.71, 0.66], 1.1), nstr=1.7)
M["kamen_s"] = mat("M_KamenPrach", "rock_surface", "ks", tint([0.33, 0.315, 0.30], 1.25), nstr=1.7)
M["kamen_c"] = mat("M_KamenSaze", "rock_surface", "kc", tint([0.16, 0.155, 0.15], 1.35), nstr=1.7, rough_mul=lambda a: 0.75 + 0.25 * a)
M["kamen_c2"]= mat("M_KamenCerny", "rock_surface", "kc2", tint([0.065, 0.06, 0.056], 1.4), nstr=1.6, rough_mul=lambda a: 0.85 + 0.15 * a)
M["kamen_p"] = mat("M_KamenVypaleny", "rock_surface", "kp", tint([0.50, 0.30, 0.20], 1.2), nstr=1.5)
M["kamen_rm"]= mat("M_KamenLomMech", "rock_surface", "krm", moss_k(0.85, 0.66), nstr=1.7, rough_mul=lambda a: 0.85 + 0.15 * a)
M["malta"]   = mat("M_MaltaHlina", "clay_plaster", "mal", tint([0.21, 0.19, 0.165], 1.2), nstr=1.8)
M["malta_c"] = mat("M_MaltaSaze", "clay_plaster", "malc", tint([0.075, 0.068, 0.06], 1.3), nstr=1.8)
M["uhli"]    = mat("M_Uhli", "rock_surface", "uh", tint([0.035, 0.034, 0.033], 1.5), nstr=2.0, rough_mul=lambda a: 0.55 + 0.4 * a)
M["popel"]   = mat("M_Popel", "clay_plaster", "pop", tint([0.36, 0.34, 0.32], 1.0), nstr=1.2)
M["zhar"]    = mat("M_Zhar", None, color=(0.08, 0.025, 0.01), rough=0.9, emit=((1.0, 0.22, 0.03), 2.2))
M["kuze"]    = mat("M_Kuze", "brown_leather", "kz", tint([0.30, 0.235, 0.18], 1.25), nstr=2.4, rough_mul=lambda a: 0.7 + 0.3 * a)
M["hlina_c"] = mat("M_HlinaSaze", "dirt_floor", "hlc", tint([0.30, 0.27, 0.24], 1.2), nstr=1.0, rough_mul=lambda a: 0.8 + 0.2 * a)
M["provaz"]  = mat("M_Provaz", "rough_linen", "prv", lambda a: (a ** 1.3) * np.array([0.42, 0.36, 0.26]), nstr=1.5)

# ---------------------------------------------------------------- pomocné funkce
VZ = Vector((0, 0, 1))
def F(Ms, pts, uvs, key, want):
    """plocha orientovaná normálou k vektoru want"""
    pts = [Vector(p) for p in pts]
    n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    if len(pts) > 3 and n.length < 1e-9: n = (pts[2] - pts[0]).cross(pts[3] - pts[0])
    if n.dot(Vector(want)) < 0: pts = pts[::-1]; uvs = uvs[::-1]
    Ms.face(pts, uvs, key)


WK_INSIDE = lambda c: 0          # 0 = venku, 1 = uvnitř, 2 = uvnitř u ohně (saze) – generátor přepíše
def wk(c):
    """materiál trámu podle polohy: venku zvětralý, dole mech, uvnitř hnědý, u ohně začouzený"""
    c = Vector(c); st = WK_INSIDE(c)
    if st == 2: return "tram_c" if random.random() < 0.7 else "tram_s"
    if st == 1: return random.choice(("tram_in", "tram_in", "tram_s"))
    if c.z < 0.65: return random.choice(("tram_m", "tram_d"))
    return random.choice(("tram", "tram", "tram_b", "tram_g"))

def T(Ms, p0, p1, w, h, key=None, up=(0, 0, 1), **kw):
    """otesaný trám: křivý, nerovný, s oblinou"""
    k = key or wk((Vector(p0) + Vector(p1)) / 2)
    kw.setdefault("bow", random.uniform(0.02, 0.045)); kw.setdefault("jitter", 0.009)
    kw.setdefault("ch", random.uniform(0.018, 0.04)); kw.setdefault("wane", 0.45); kw.setdefault("seglen", 0.45)
    return hbeam(Ms, p0, p1, w * random.uniform(0.93, 1.07), h * random.uniform(0.93, 1.07), k, up=up, **kw)

def pole(Ms, p0, p1, r0, r1=None, key="tram_s", bend=0.035, seg=8, seglen=0.4, bark=0.30, caps=(True, True), capkey="zhlavi"):
    """křivý odkorněný kuláč se zbytky kůry"""
    p0 = Vector(p0); p1 = Vector(p1); r1 = r0 * 0.85 if r1 is None else r1
    X, Y, Z, Ln = frame_axes(p0, p1, (0, 0, 1) if abs((p1 - p0).normalized().z) < 0.9 else (1, 0, 0))
    ns = max(2, int(math.ceil(Ln / seglen)))
    ph = [random.uniform(0, 6.28) for _ in range(4)]
    ay, az = random.uniform(-1, 1) * bend, random.uniform(-1, 1) * bend
    ob = random.uniform(0, 50)
    rings = []
    for j in range(ns + 1):
        t = j / ns; e = 0.0 if j in (0, ns) else 1.0
        cen = p0 + X * (Ln * t) + Y * (ay * math.sin(math.pi * t) + e * 0.3 * bend * math.sin(2 * math.pi * t + ph[0])) \
              + Z * (az * math.sin(math.pi * t) + e * 0.3 * bend * math.sin(2 * math.pi * t + ph[1]))
        r = r0 + (r1 - r0) * t
        rings.append([cen + (Y * math.cos(2 * math.pi * k / seg) + Z * math.sin(2 * math.pi * k / seg)) *
                      r * (1 + 0.07 * math.sin(k * 2.3 + ph[2] + t * 5) + random.uniform(-0.03, 0.03) * e) for k in range(seg)])
    ou = random.random() * 3
    for j in range(ns):
        for k in range(seg):
            k2 = (k + 1) % seg
            kk = "kura" if float(vnoise(np.array(ob + j * 0.7), np.array(k * 0.9 + ob), 3)) > 1 - bark * 0.9 else key
            q = [rings[j][k], rings[j][k2], rings[j + 1][k2], rings[j + 1][k]]
            v0 = Ln * j / ns / 0.75; v1 = Ln * (j + 1) / ns / 0.75
            Ms.face(q, [(ou + k / seg * 0.6, v0), (ou + (k + 1) / seg * 0.6, v0), (ou + (k + 1) / seg * 0.6, v1), (ou + k / seg * 0.6, v1)], kk)
    for (ring, rev, on) in ((rings[0], True, caps[0]), (rings[-1], False, caps[1])):
        if not on: continue
        cen = sum(ring, Vector()) / seg; pts = ring[::-1] if rev else ring
        Ms.face(pts, [(((p - cen).dot(Y)) / 0.3 + 0.5, ((p - cen).dot(Z)) / 0.3 + 0.5) for p in pts], capkey)
    return X, Y, Z, Ln

def cone(Ms, p0, p1, r0, r1, key, seg=10):
    a = Vector(p0); b = Vector(p1); X, Y, Z, Ln = frame_axes(a, b, (0, 0, 1))
    ra = [a + (Y * math.cos(2 * math.pi * k / seg) + Z * math.sin(2 * math.pi * k / seg)) * r0 for k in range(seg)]
    rb = [b + (Y * math.cos(2 * math.pi * k / seg) + Z * math.sin(2 * math.pi * k / seg)) * r1 for k in range(seg)]
    for k in range(seg):
        k2 = (k + 1) % seg
        Ms.face([ra[k], ra[k2], rb[k2], rb[k]], [(k / seg, 0), ((k + 1) / seg, 0), ((k + 1) / seg, Ln), (k / seg, Ln)], key)
    Ms.face(ra[::-1], [(0, 0)] * seg, key); Ms.face(rb, [(0, 0)] * seg, key)

def board(Ms, c, U, V, N, wid, ln, th, key, waney=False, tilt=0.012):
    """prkno: nerovné konce, mírně kónické, lehce natočené; waney = krajinka s kůrou na boku"""
    U = Vector(U); V = Vector(V); N = Vector(N)
    a = random.uniform(-tilt, tilt); U2 = U * math.cos(a) + V * math.sin(a); V2 = V * math.cos(a) - U * math.sin(a)
    hw0, hw1 = wid / 2, wid / 2 * random.uniform(0.86, 1.0)
    poly = [(-hw0 + random.uniform(0, 0.01), -ln / 2 + random.uniform(-0.02, 0.02)), (hw0, -ln / 2 + random.uniform(-0.02, 0.02)),
            (hw1, ln / 2 + random.uniform(-0.015, 0.015)), (-hw1 + random.uniform(0, 0.01), ln / 2 + random.uniform(-0.015, 0.015))]
    prism(Ms, poly, Vector(c) - N * (th / 2), U2, V2, N, th, key, uvs=1.0, key_side=("kura" if waney else key),
          uoff=(random.random() * 3, random.random() * 3))

def stone(Ms, c, U, V, N, w, h, d, key, detail=True, bulge=0.045, tilt=0.10):
    """nepravidelný kámen: líc v rovině c (normála N), do hloubky d; seká se do zdi.
    detail=2: zaoblený (2 segmenty zkosení), 1/True: zkosený, False: hrubý blok"""
    U = Vector(U).normalized(); V = Vector(V).normalized(); N = Vector(N).normalized()
    a = random.uniform(-tilt, tilt); U, V = U * math.cos(a) + V * math.sin(a), V * math.cos(a) - U * math.sin(a)
    Rm = Matrix((U, N, V)).transposed(); flip = Rm.determinant() < 0
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, v.co.y * d - d / 2, v.co.z * h))
    mn = min(w, h)
    for v in bm.verts:                                   # nepravidelný obrys ještě před zkosením
        if v.co.y < -d / 2:                              # záda kamene užší: boky mizí do malty
            v.co.x *= random.uniform(0.70, 0.85); v.co.z *= random.uniform(0.70, 0.85)
        else:
            v.co.x *= random.uniform(0.97, 1.03); v.co.z *= random.uniform(0.97, 1.03)
    if detail:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(w, h, d) * random.uniform(0.16, 0.27), segments=2 if detail == 2 else 1, affect='EDGES')
    sk = random.uniform(-0.22, 0.22)                    # kámen je kosý, ne pravoúhlý
    tp = random.uniform(-0.18, 0.18)                    # a zúžený k jedné straně
    ph = [random.uniform(0, 6.28) for _ in range(4)]     # plynulá deformace celého kamene (žádné střepy)
    am = [random.uniform(0.04, 0.10) * mn for _ in range(2)]
    for v in bm.verts:
        x, y, z = v.co
        x += z * sk; x *= 1 + tp * (z / max(h, 0.01))
        x += am[0] * math.sin(3.0 * z / max(h, 0.01) + ph[0]); z += am[1] * math.sin(2.6 * x / max(w, 0.01) + ph[1])
        y += 0.012 * math.sin(4.0 * x / max(w, 0.01) + ph[2]) * math.sin(3.0 * z / max(h, 0.01) + ph[3])
        x += random.uniform(-1, 1) * mn * 0.012; z += random.uniform(-1, 1) * mn * 0.012
        if y > -0.03:
            fx = max(0.0, 1 - (2 * x / w) ** 2); fz = max(0.0, 1 - (2 * z / h) ** 2)
            y += bulge * random.uniform(0.4, 1.3) * (fx * fz) ** 0.7 * (1 if detail else 0.6)
        v.co = Vector((x, y, z))
    bm.normal_update()
    ou, ov = random.random() * 4, random.random() * 4; sc = random.uniform(0.55, 0.85)
    for f in bm.faces:
        n = f.normal
        if n.y < -0.75: continue                        # zadní plocha je ve zdi
        pts = [Vector(c) + Rm @ v.co for v in f.verts]
        loc = [v.co for v in f.verts]
        if abs(n.y) > 0.6: uv = [(p.x / sc + ou, p.z / sc + ov) for p in loc]
        elif abs(n.x) > 0.6: uv = [(p.y / sc + ou, p.z / sc + ov) for p in loc]
        else: uv = [(p.x / sc + ou, p.y / sc + ov) for p in loc]
        if flip: pts = pts[::-1]; uv = uv[::-1]
        Ms.face(pts, uv, key)
    bm.free()

def stone_face(Ms, O, U, V, N, ulen, vlen, keyf, hole=None, d=(0.20, 0.32), hr=(0.14, 0.32), wr=(0.20, 0.52), gap=0.014,
               detail=True, bulge=0.045):
    """líc zdi z kamenů v nepravidelných řádcích; hole(u, v) = True v otvoru"""
    O = Vector(O); U = Vector(U); V = Vector(V); N = Vector(N)
    def free(u0, u1, v0, v1):
        if hole is None: return True
        for (uu, vv) in ((u0, v0), (u1, v0), (u0, v1), (u1, v1), ((u0 + u1) / 2, v0), ((u0 + u1) / 2, v1), (u0, (v0 + v1) / 2), (u1, (v0 + v1) / 2), ((u0 + u1) / 2, (v0 + v1) / 2)):
            if hole(uu, vv): return False
        return True
    v = 0.0
    while v < vlen - 0.03:
        h = random.uniform(*hr)
        if vlen - (v + h) < hr[0] * 0.7: h = vlen - v
        u = 0.0; first = True
        while u < ulen - 0.03:
            w = random.uniform(*wr) * (random.uniform(0.4, 1.0) if first else 1.0); first = False
            if ulen - (u + w) < wr[0] * 0.6: w = ulen - u
            hh = h * random.uniform(0.72, 1.12); vv = v + (h - hh) * random.random() + random.uniform(-0.025, 0.025)
            vv = max(0.0, min(vv, vlen - hh)) if hh < vlen else 0.0
            pieces = [(u, u + w)]
            if not free(u + gap / 2, u + w - gap / 2, vv + gap / 2, vv + hh - gap / 2):
                pieces = [(u, u + w / 2), (u + w / 2, u + w)] if w > 0.2 else []
            for (a, b) in pieces:
                if not free(a + gap / 2, b - gap / 2, vv + gap / 2, vv + hh - gap / 2): continue
                cc = O + U * ((a + b) / 2) + V * (vv + hh / 2) + N * random.uniform(0.012, 0.042)
                stone(Ms, cc, U, V, N, b - a - gap * random.uniform(0.6, 1.5), hh - gap * random.uniform(0.6, 1.5),
                      random.uniform(*d), keyf(cc, N), detail=detail, bulge=bulge)
            u += w
        v += h


def colbox(name, lo, hi, rot=None):
    lo = Vector(lo); hi = Vector(hi)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lo + hi) / 2)
    o = bpy.context.active_object; o.name = "%s_Kol_%s-convcolonly" % (PFX, name)
    o.scale = hi - lo
    if rot is not None: o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); o.hide_render = True
    KOL.append(o); return o
KOL = []

# Postup: tvar se poskládá z kvádrů a válců (booleany), přesíťuje se na hustou pravidelnou síť (voxel remesh),
# každý vrchol se posune po normále podle výškové mapy skenu skutečné kamenné zdi (triplanárně, takže rohy
# nepraskají), UV se promítne stejně jako výška (kámen v geometrii = kámen na fotce), saze a prach jsou
# barva vrcholů (glTF COLOR_0 násobí albedo), nakonec se síť zredukuje (decimate) pro tablet.
from PIL import Image as _PILImage
def _load_h(pid):
    a = np.asarray(_PILImage.open(os.path.join(FOTO, pid + "_disp.png")).convert("L").resize((1024, 1024), _PILImage.LANCZOS), np.float32) / 255.0
    return (a - a.min()) / max(1e-6, (a.max() - a.min()))
HMAP = {"broken_wall": _load_h("broken_wall"), "cobblestone_large_01": _load_h("cobblestone_large_01")}
def hsample(H, u, v):
    n = H.shape[0]
    x = (u % 1.0) * n; y = (1.0 - (v % 1.0)) * n - 1e-3
    x0 = int(x) % n; y0 = int(y) % n; x1 = (x0 + 1) % n; y1 = (y0 + 1) % n; fx = x - int(x); fy = y - int(y)
    return (H[y0, x0] * (1 - fx) + H[y0, x1] * fx) * (1 - fy) + (H[y1, x0] * (1 - fx) + H[y1, x1] * fx) * fy
PROJ_OFF = {0: (0.37, 0.11), 1: (0.0, 0.0), 2: (0.71, 0.53)}
def proj(p, ax, tile):
    o = PROJ_OFF[ax]
    if ax == 0: return (p.y / tile + o[0], p.z / tile + o[1])
    if ax == 1: return (p.x / tile + o[0], p.z / tile + o[1])
    return (p.x / tile + o[0], p.y / tile + o[1])

def vcol_mat(name, pid, tag, upravit, nstr=1.0, rough_mul=None):
    """materiál z fotoskenu × barva vrcholů 'Saze' (v glTF COLOR_0)"""
    m = mat(name, pid, tag, upravit, nstr=nstr, rough_mul=rough_mul)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    img = [n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.outputs["Color"].links and n.outputs["Color"].links[0].to_socket == b.inputs["Base Color"]][0]
    ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "Saze"
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    sA = [x for x in mx.inputs if x.name == "A" and x.type == 'RGBA'][0]; sB = [x for x in mx.inputs if x.name == "B" and x.type == 'RGBA'][0]
    sR = [x for x in mx.outputs if x.name == "Result" and x.type == 'RGBA'][0]
    nt.links.new(img.outputs["Color"], sA); nt.links.new(ca.outputs["Color"], sB); nt.links.new(sR, b.inputs["Base Color"])
    return m
M["zdivo"]  = vcol_mat("M_ZdivoKamen", "broken_wall", "zd", tint([0.92, 0.90, 0.88], 1.05), nstr=1.2, rough_mul=lambda a: 0.7 + 0.3 * a)
M["dlazba"] = vcol_mat("M_DlazbaPolniKamen", "cobblestone_large_01", "dl", tint([0.95, 0.92, 0.88], 1.0), nstr=1.2)
M["plotna"] = vcol_mat("M_PlotnaVyhne", "clay_plaster", "plv", tint([0.55, 0.50, 0.45], 1.1), nstr=1.4)

def _apply_mod(o, m):
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], selected_editable_objects=[o]):
        bpy.ops.object.modifier_apply(modifier=m.name)
def solid_box(lo, hi):
    lo = Vector(lo); hi = Vector(hi)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lo + hi) / 2); o = bpy.context.active_object
    o.scale = hi - lo; bpy.ops.object.transform_apply(location=True, rotation=False, scale=True); return o
def solid_cyl_y(cx, cz, r, y0, y1, n=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=y1 - y0, location=(cx, (y0 + y1) / 2, cz), rotation=(math.pi / 2, 0, 0))
    o = bpy.context.active_object; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); return o
def csg(base, others, op):
    for ob in others:
        m = base.modifiers.new("b", 'BOOLEAN'); m.operation = op; m.object = ob; m.solver = 'EXACT'
        _apply_mod(base, m); bpy.data.objects.remove(ob, do_unlink=True)
    return base

def masonry(o, name, tile, S, keyf_bed, soot, ratio, voxel=0.035, drop=None, flat_top=None, hkey="broken_wall", mats=("zdivo", "plotna"), remesh=True):
    """o: uzavřený tvar. tile: m na dlaždici skenu, S: hloubka spár (m). keyf_bed(p, n) -> True = plotna (bez kamene).
    soot(p, n, h) -> (r, g, b) násobič barvy. drop(p, n) -> True = smazat plochu (skrytá). flat_top(p, n) -> 0..1 ztlumení reliéfu."""
    if remesh:
        m = o.modifiers.new("r", 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = voxel; m.use_smooth_shade = True; _apply_mod(o, m)
    o.name = name; me = o.data; me.name = name
    bm = bmesh.new(); bm.from_mesh(me); bm.normal_update()
    if drop:
        dead = [f for f in bm.faces if drop(f.calc_center_median(), f.normal)]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.normal_update()
    H = HMAP[hkey]
    orig = {v.index: (v.co.copy(), v.normal.copy()) for v in bm.verts}
    hv = {}
    for v in bm.verts:
        p, n = orig[v.index]
        if keyf_bed(p, n):
            hv[v.index] = 1.0; v.co = p + n * (0.004 * float(vnoise(np.array(p.x * 9), np.array(p.y * 9), 7))); continue
        w = [abs(n.x) ** 4, abs(n.y) ** 4, abs(n.z) ** 4]; sw = sum(w) or 1.0
        h = sum(w[i] / sw * hsample(H, *proj(p, i, tile)) for i in range(3))
        hv[v.index] = h
        k = flat_top(p, n) if flat_top else 1.0
        v.co = p + n * ((h - 1.0) * S * k)
    uvl = bm.loops.layers.uv.new("UVMap")
    col = bm.loops.layers.color.new("Saze")
    for f in bm.faces:
        fc = sum((orig[v.index][0] for v in f.verts), Vector()) / len(f.verts)
        fn = sum((orig[v.index][1] for v in f.verts), Vector()).normalized()
        bed = keyf_bed(fc, fn)
        f.material_index = 1 if bed else 0
        ax = max(range(3), key=lambda i: abs(fn[i]))
        for lp in f.loops:
            p, n = orig[lp.vert.index]
            lp[uvl].uv = (p.x / 1.2, p.y / 1.2) if bed else proj(p, ax, tile)
            c = soot(p, n, hv[lp.vert.index], bed)
            lp[col] = (max(0.0, c[0]) ** (1 / 2.2), max(0.0, c[1]) ** (1 / 2.2), max(0.0, c[2]) ** (1 / 2.2), 1.0)   # bajtová barva je sRGB
    bm.to_mesh(me); bm.free()
    me.materials.clear()
    for k_ in mats: me.materials.append(M[k_])
    me.shade_smooth()
    if ratio < 1.0:
        d = o.modifiers.new("d", 'DECIMATE'); d.ratio = ratio; d.use_collapse_triangulate = True; _apply_mod(o, d)
    return o

def nzf(p, s=1.0, ch=5):
    return float(vnoise(np.array(p.x * 2.1 * s + p.y * 1.3 * s), np.array(p.z * 2.4 * s + p.y * 0.7), ch))

def clad(Ms, O, U, N, u0, u1, z0, ztop, holes=(), key="prkna", th=0.028, battens=True, peg_z=(1.4,)):
    O = Vector(O); U = Vector(U); N = Vector(N)
    u = u0; joints = []
    while u < u1 - 0.02:
        wd = random.uniform(0.19, 0.33)
        if u1 - (u + wd) < 0.12: wd = u1 - u
        ua, ub = u, u + wd; uc = (ua + ub) / 2
        zt_l, zt_r = ztop(ua), ztop(ub)
        segs = [(z0, None)]
        hs = [h for h in holes if h[0] < ub - 0.02 and h[1] > ua + 0.02]
        pieces = [(z0, min(zt_l, zt_r), False)]
        if hs:
            h = hs[0]; pieces = [(z0, h[2], False), (h[3], min(zt_l, zt_r), True)]
        kk = key if random.random() > 0.2 else random.choice(("dvere", "tram_l", "tram_g"))
        wn = random.random() < 0.3
        for (za, zb, upper) in pieces:
            if zb - za < 0.05: continue
            top_l = zt_l if (not hs or upper) else zb; top_r = zt_r if (not hs or upper) else zb
            e = [random.uniform(-0.02, 0.02) for _ in range(4)]
            hw = (ub - ua) / 2 - 0.004; hw2 = hw * random.uniform(0.9, 1.0)
            poly = [(-hw, za + e[0]), (hw, za + e[1]), (hw2, top_r + e[2] * 0.4), (-hw2, top_l + e[3] * 0.4)]
            a = random.uniform(-0.01, 0.01)
            prism(Ms, poly, O + U * uc + N * random.uniform(0.0, 0.008), U, Vector((0, 0, 1)) + U * a, N, th, kk, uvs=1.0,
                  key_side=("kura" if wn else kk), uoff=(random.random() * 3, random.random() * 3))
        joints.append(ub)
        u = ub
    if battens:
        for j in joints[:-1]:
            if random.random() < 0.35: continue
            zt = min(ztop(j - 0.03), ztop(j + 0.03)) - 0.03
            hs = [h for h in holes if h[0] - 0.05 < j < h[1] + 0.05]
            spans = [(z0 + 0.03, zt)] if not hs else [(z0 + 0.03, hs[0][2]), (hs[0][3], zt)]
            for (za, zb) in spans:
                if zb - za < 0.1: continue
                prism(Ms, [(-0.03, za), (0.03, za), (0.028, zb), (-0.028, zb)], O + U * j + N * th, U, Vector((0, 0, 1)), N, 0.018, "dvere", uvs=1.0)
                for zz in peg_z:
                    if za < zz < zb: peg(Ms, O + U * j + N * (th + 0.018), N, r=0.010, proud=0.005)

EXP = 0.16
SH_W = (0.085, 0.17)
def shingles(SH, P0, Ax, S, N, xa, xb, SL, skip, keyf):
    P0 = Vector(P0); Ax = Vector(Ax); S = Vector(S); N = Vector(N); cnt = 0
    r = 0
    while True:
        s0 = r * EXP; r += 1
        if s0 > SL - 0.03: break
        s1 = min(s0 + EXP + 0.06, SL + 0.02)
        x = xa - random.uniform(0.0, 0.08)
        while x < xb + 0.02:
            bw = random.uniform(*SH_W); x0, x1 = max(x, xa), min(x + bw, xb); x = x + bw + random.uniform(0.002, 0.008)
            if x1 - x0 < 0.03 or skip((x0 + x1) / 2, s0, s1): continue
            key = keyf((x0 + x1) / 2, s0)
            sl0 = s0 + random.uniform(-0.012, 0.010)
            h_lo = 0.048 + random.uniform(-0.006, 0.006); lift = random.uniform(-0.004, 0.004)
            if random.random() < 0.03: h_lo += random.uniform(0.015, 0.035); lift = random.choice((-1, 1)) * random.uniform(0.008, 0.018)
            dx0, dx1 = random.uniform(-0.008, 0.008), random.uniform(-0.008, 0.008)
            if x0 <= xa + 0.001 or x1 >= xb - 0.001: dx0 = dx1 = 0.0          # u závětrné desky rovně, nepřesahuje
            pA = P0 + Ax * (x0 + dx0) + S * sl0 + N * (h_lo + lift); pB = P0 + Ax * (x1 + dx0) + S * sl0 + N * (h_lo - lift)
            pC = P0 + Ax * (x1 + dx1) + S * s1 + N * 0.012; pD = P0 + Ax * (x0 + dx1) + S * s1 + N * 0.012
            ou, ov = random.random() * 4, random.random() * 4; Lsh = s1 - sl0
            F(SH, [pA, pB, pC, pD], [(ou, ov), (ou + (x1 - x0) / 0.75, ov), (ou + (x1 - x0) / 0.75, ov + Lsh / 0.75), (ou, ov + Lsh / 0.75)], key, N)
            dn = N * 0.026
            F(SH, [pA - dn, pB - dn, pB, pA], [(ou, ov), (ou + (x1 - x0) / 0.75, ov), (ou + (x1 - x0) / 0.75, ov + 0.02), (ou, ov + 0.02)], key, -S)
            cnt += 1
    pu = [P0 + Ax * (xa - 0.08) + S * (-0.02) + N * 0.006, P0 + Ax * (xb + 0.03) + S * (-0.02) + N * 0.006,
          P0 + Ax * (xb + 0.03) + S * (SL + 0.02) + N * 0.006, P0 + Ax * (xa - 0.08) + S * (SL + 0.02) + N * 0.006]
    F(SH, pu, [(0, 0), ((xb - xa) / 0.75, 0), ((xb - xa) / 0.75, SL / 0.75), (0, SL / 0.75)], "sindel_t", -N)      # spodní líc šindele mezi latěmi
    return cnt

def preview_scene(trees=((-14, 16, 13), (16, 20, 12), (-20, -4, 11), (22, 6, 15), (-4, 28, 14)), dirt=(1 / 5.5, 1 / 4.6, -0.15, 0.25)):
    print("scéna…")
    gm = bpy.data.materials.new("M_zem"); nt = gm.node_tree; b = nt.nodes["Principled BSDF"]
    ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(os.path.join(FOTO, "trava_grass004.jpg"))
    td = nt.nodes.new("ShaderNodeTexImage"); td.image = M["hlina"].node_tree.nodes["Image Texture"].image
    mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord"); mp.inputs["Scale"].default_value = (0.5, 0.5, 0.5)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], ti.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], td.inputs["Vector"])
    nz_ = nt.nodes.new("ShaderNodeTexNoise"); nz_.inputs["Scale"].default_value = 0.6; nt.links.new(tc.outputs["Object"], nz_.inputs["Vector"])
    ln_ = nt.nodes.new("ShaderNodeVectorMath"); ln_.operation = 'LENGTH'
    sc_ = nt.nodes.new("ShaderNodeVectorMath"); sc_.operation = 'MULTIPLY'; sc_.inputs[1].default_value = (dirt[0], dirt[1], 0)
    of_ = nt.nodes.new("ShaderNodeVectorMath"); of_.operation = 'ADD'; of_.inputs[1].default_value = (dirt[2], dirt[3], 0)
    nt.links.new(tc.outputs["Object"], sc_.inputs[0]); nt.links.new(sc_.outputs["Vector"], of_.inputs[0]); nt.links.new(of_.outputs["Vector"], ln_.inputs[0])
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.5
    nt.links.new(nz_.outputs["Fac"], ad.inputs[0]); nt.links.new(ln_.outputs["Value"], ad.inputs[2])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 1.0; mr.inputs["From Max"].default_value = 1.4
    nt.links.new(ad.outputs[0], mr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    nt.links.new(mr.outputs["Result"], mix.inputs["Factor"]); nt.links.new(td.outputs["Color"], mix.inputs["A"]); nt.links.new(ti.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.005))
    gnd = bpy.context.active_object; gnd.name = "_zem"; gnd.data.materials.append(gm); to_prev(gnd)
    tm = bpy.data.materials.new("M_koruna"); tm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.055, 0.016, 1)
    tk = bpy.data.materials.new("M_kmen"); tk.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.06, 0.045, 1)
    for (x, y, hgt) in trees:
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=hgt * 0.03, depth=hgt * 0.6, location=(x, y, hgt * 0.3))
        t = bpy.context.active_object; t.data.materials.append(tk); to_prev(t)
        for j in range(7):
            rr = hgt * random.uniform(0.15, 0.24)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=rr, location=(x + random.gauss(0, hgt * 0.12), y + random.gauss(0, hgt * 0.12), hgt * random.uniform(0.55, 0.85)))
            t = bpy.context.active_object; t.data.materials.append(tm); to_prev(t); bpy.ops.object.shade_smooth()
            d = t.modifiers.new("d", 'DISPLACE'); tx = bpy.data.textures.new("t%d%d" % (x, j), 'CLOUDS'); tx.noise_scale = rr * 0.3; tx.noise_depth = 3
            d.texture = tx; d.strength = rr * 0.5
    world = bpy.data.worlds.new("Svet"); scene.world = world
    wnt = world.node_tree; sky = wnt.nodes.new("ShaderNodeTexSky")
    try: sky.sky_type = 'MULTIPLE_SCATTERING'
    except Exception: pass
    sky.sun_elevation = math.radians(34); sky.sun_rotation = math.radians(140)
    bg = wnt.nodes["Background"]; bg.inputs["Strength"].default_value = 0.30; wnt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    sun = bpy.data.lights.new("Slunce", 'SUN'); sun.energy = 4.2; sun.angle = math.radians(1.2); sun.color = (1.0, 0.94, 0.84)
    so = bpy.data.objects.new("Slunce", sun); scene.collection.objects.link(so)
    so.rotation_euler = Vector((-0.55, 0.62, -0.56)).to_track_quat('-Z', 'Y').to_euler(); to_prev(so)

# ================================================================= ROUBENÍ A STAVEBNÍ PRVKY (hospody)
M["slama"] = mat("M_Slama", "reed_roof_04", "slm", tint([0.62, 0.52, 0.36], 1.15), nstr=1.4)
M["len"]   = mat("M_Platno", "rough_linen", "lnp", lambda a: (a ** 1.35) * np.array([0.50, 0.45, 0.37]), nstr=1.8)
M["pec"]   = mat("M_PecHlina2", "clay_plaster", "pec2", tint([0.50, 0.44, 0.37], 1.15), nstr=2.2, rough_mul=lambda a: 0.85 + 0.15 * a)
M["pec_c"] = mat("M_PecZacouzena2", "clay_plaster", "pecc2", tint([0.16, 0.13, 0.11], 1.3), nstr=1.6)
LOG_H, LOG_T, LOG_SEG = 0.25, 0.22, 1.3

def splitr(s0, s1, holes):
    out = []; cur = s0
    for h0, h1 in sorted(holes):
        if h1 <= cur or h0 >= s1: continue
        if h0 > cur: out.append((cur, h0))
        cur = max(cur, h1)
    if cur < s1: out.append((cur, s1))
    return out

def recolor(Ms, n0, inward, key_in):
    """plochy přidané od indexu n0, které míří dovnitř (inward), dostanou materiál key_in (funkce středu nebo klíč)"""
    inward = Vector(inward)
    for fi in range(n0, len(Ms.f)):
        idx = Ms.f[fi]; p0, p1, p2 = Vector(Ms.v[idx[0]]), Vector(Ms.v[idx[1]]), Vector(Ms.v[idx[2]])
        nn = (p1 - p0).cross(p2 - p0)
        if nn.length > 1e-9 and nn.normalized().dot(inward) > 0.35:
            k = key_in(p0) if callable(key_in) else key_in
            Ms.m[fi] = Ms.mi(k)

def wall_frame2(p0, p1):
    a = Vector((p0[0], p0[1], 0)); b = Vector((p1[0], p1[1], 0)); d = b - a; Ln = d.length; d.normalize()
    return a, d, Ln, Vector((-d.y, d.x, 0))

def log_wall(Ms, p0, p1, z0, z1, phase, holes=(), ext=(0.0, 0.0), inward=None, key_in="tram_in", chink=True, t=LOG_T, moss_z=0.9):
    """roubená stěna z otesaných trámů (vodorovně), spáry vymazané hlínou; phase 1 = posun o půl trámu (kolmé stěny
    se v rozích střídají), ext = přesah zhlaví na koncích, holes = [(u0, u1, z0, z1)] otvory podél stěny"""
    a, d, Ln, n = wall_frame2(p0, p1)
    zs = []
    zc = z0
    if phase: zs.append((z0, z0 + LOG_H / 2)); zc = z0 + LOG_H / 2
    while zc + LOG_H <= z1 + 0.02: zs.append((zc, zc + LOG_H)); zc += LOG_H
    if z1 - zc > 0.06: zs.append((zc, z1))
    for ci, (za, zb) in enumerate(zs):
        hs = [(h[0], h[1]) for h in holes if h[2] < zb - 0.03 and h[3] > za + 0.03]
        for (ua, ub) in splitr(-ext[0], Ln + ext[1], hs):
            if ub - ua < 0.08: continue
            zc_ = (za + zb) / 2; hh = (zb - za) - 0.035
            low = zc_ < moss_z
            ko = random.choice(("tram_m", "tram_d", "tram_m")) if low else random.choice(("tram", "tram", "tram_b", "tram_g", "tram_l"))
            n0 = len(Ms.f)
            hbeam(Ms, a + d * ua + Vector((0, 0, zc_)), a + d * ub + Vector((0, 0, zc_)), t * random.uniform(0.95, 1.05), hh * random.uniform(0.95, 1.02),
                  ko, up=(0, 0, 1), ch=random.uniform(0.035, 0.06), wane=0.5, bow=0.012, seglen=LOG_SEG, jitter=0.006,
                  capkey="zhlavi_m" if low else "zhlavi")
            if inward is not None: recolor(Ms, n0, inward, key_in)
            if chink and ci > 0:
                for sg in (1, -1):
                    side = n * sg
                    if inward is not None and side.dot(Vector(inward)) > 0:
                        kc = "mazanice_c" if (callable(key_in) and key_in(a + d * ((ua + ub) / 2) + Vector((0, 0, za))) == "tram_c") else "mazanice"
                    else: kc = "mazanice"
                    off = side * (t / 2 - 0.03)
                    pa = a + d * max(ua, 0.0) + off + Vector((0, 0, za)); pb = a + d * min(ub, Ln) + off + Vector((0, 0, za))
                    if (pb - pa).length < 0.05: continue
                    F(Ms, [pa - Vector((0, 0, 0.028)), pb - Vector((0, 0, 0.028)), pb + Vector((0, 0, 0.028)), pa + Vector((0, 0, 0.028))],
                      [(0, 0), ((pb - pa).length, 0), ((pb - pa).length, 0.056), (0, 0.056)], kc, side)

def opening_frame(Ms, p0, p1, u0, u1, zb, zt, kind="okno", t=LOG_T, key="tram_b"):
    """veřeje (boční trámy s drážkou, drží konce trámů), nadpraží a práh / parapet"""
    a, d, Ln, n = wall_frame2(p0, p1)
    for u in (u0 - 0.06, u1 + 0.06):
        hbeam(Ms, a + d * u + Vector((0, 0, zb - (0.10 if kind == "okno" else 0.0))), a + d * u + Vector((0, 0, zt + 0.12)), 0.12, t + 0.05, key,
              up=tuple(n), ch=0.02, wane=0.2, bow=0.006, seglen=0.8)
        for zz in (zb + 0.15, zt - 0.15):
            peg(Ms, a + d * u + n * ((t + 0.05) / 2) + Vector((0, 0, zz)), n, r=0.013)
    hbeam(Ms, a + d * (u0 - 0.14) + Vector((0, 0, zt + 0.07)), a + d * (u1 + 0.14) + Vector((0, 0, zt + 0.07)), t + 0.05, 0.14, key, ch=0.02, wane=0.3)
    if kind == "okno":
        hbeam(Ms, a + d * (u0 - 0.14) + Vector((0, 0, zb - 0.06)), a + d * (u1 + 0.14) + Vector((0, 0, zb - 0.06)), t + 0.07, 0.12, key, ch=0.02, wane=0.2)
    else:
        hbeam(Ms, a + d * (u0 - 0.10) + Vector((0, 0, zb - 0.04)), a + d * (u1 + 0.10) + Vector((0, 0, zb - 0.04)), t + 0.06, 0.10, "tram_d", ch=0.02, wane=0.2)

def window(Ms, p0, p1, u0, u1, zb, zt, out_sign=1, shutter_ang=155, t=LOG_T, bars=2):
    """malé okno: rám, svislé dřevěné příčky, okenice venku na kovaných závěsech"""
    a, d, Ln, n = wall_frame2(p0, p1); nout = n * out_sign
    opening_frame(Ms, p0, p1, u0, u1, zb, zt, "okno", t)
    for k in range(bars):
        u = u0 + (k + 1) * (u1 - u0) / (bars + 1)
        pole(Ms, a + d * u + Vector((0, 0, zb - 0.02)), a + d * u + Vector((0, 0, zt + 0.02)), 0.018, 0.016, key="tram_d", bend=0.004, seg=6, bark=0.0)
    if shutter_ang is None: return
    w = u1 - u0 + 0.06; hinge = a + d * (u1 + 0.03) + nout * (t / 2 + 0.03)
    ang = math.radians(shutter_ang); dd = (-d * math.cos(ang) + nout * math.sin(ang)).normalized()     # zavřená = -d, otevřená ven
    sd = dd.cross(Vector((0, 0, 1)))
    k = 0; x = 0.0
    while x < w - 0.02:
        bw = min(random.uniform(0.11, 0.16), w - x)
        board(Ms, hinge + dd * (x + bw / 2) + Vector((0, 0, (zb + zt) / 2)), dd, (0, 0, 1), sd, bw - 0.004, zt - zb + 0.05, 0.025, "dvere", tilt=0.004)
        x += bw
    for zz in (zb + 0.07, zt - 0.07):
        box(Ms, hinge + dd * (w / 2) - sd * 0.022 + Vector((0, 0, zz)), (w - 0.03, 0.022, 0.07), Matrix((dd, sd, Vector((0, 0, 1)))).transposed(), "dvere", uvs=0.8)
        iron_plate(Ms, hinge + dd * (w * 0.32) + sd * 0.016 + Vector((0, 0, zz)), sd, dd, w * 0.6, 0.032, nrv=3)

DOORS = []
def door_leaf(name, p0, p1, u0, u1, zb, zt, out_sign=1, hinge_side=0, opens_in=True, ang_max=100, t=LOG_T):
    """dveře jako samostatný objekt s počátkem v pantu (ve hře se otáčí kolem svislé osy)"""
    a, d, Ln, n = wall_frame2(p0, p1); nin = -n * out_sign
    uh = u0 if hinge_side == 0 else u1; dir_ = d if hinge_side == 0 else -d
    face = nin if opens_in else -nin
    hinge = a + d * uh + face * (t / 2 - 0.02) + Vector((0, 0, zb + 0.01))
    D = Mesh(name); w = u1 - u0 - 0.01; h = zt - zb - 0.02
    x = 0.0
    while x < w - 0.02:
        bw = min(random.uniform(0.15, 0.24), w - x)
        board(D, hinge + dir_ * (x + bw / 2) + face * 0.022 + Vector((0, 0, h / 2)), dir_, (0, 0, 1), face, bw - 0.004, h, 0.04, "dvere", tilt=0.003)
        x += bw
    for zz in (0.25, h - 0.28):
        box(D, hinge + dir_ * (w / 2) + face * 0.06 + Vector((0, 0, zz)), (w - 0.05, 0.035, 0.11), Matrix((dir_, face, Vector((0, 0, 1)))).transposed(), "dvere", uvs=0.8)
        iron_plate(D, hinge + dir_ * (w * 0.32) - face * 0.004 + Vector((0, 0, zz)), -face, dir_, w * 0.62, 0.045, nrv=4)
    dz = h - 0.53 - 0.11; dx = w - 0.16
    R = Matrix((dir_, face, Vector((0, 0, 1)))).transposed() @ Matrix.Rotation(-math.atan2(dz, dx), 3, 'Y')
    box(D, hinge + dir_ * (w / 2) + face * 0.06 + Vector((0, 0, (0.25 + h - 0.28) / 2)), (math.hypot(dx, dz), 0.03, 0.10), R, "dvere", uvs=0.8)
    for zz in (0.12, h - 0.12): box(D, hinge + Vector((0, 0, zz)), (0.05, 0.05, 0.08), Matrix.Identity(3), "zelezo")
    for sg in (1, -1):                                              # kruh s klikou z obou stran
        c = hinge + dir_ * (w - 0.12) + face * (0.0 if sg < 0 else 0.07) - face * (0.03 if sg < 0 else 0) + Vector((0, 0, 1.0))
        for k in range(8):
            a0 = 2 * math.pi * k / 8; a1 = 2 * math.pi * (k + 1) / 8
            cone(D, c + Vector((0, 0, math.cos(a0) * 0.05 - 0.05)) + dir_ * math.sin(a0) * 0.05, c + Vector((0, 0, math.cos(a1) * 0.05 - 0.05)) + dir_ * math.sin(a1) * 0.05,
                 0.006, 0.006, "zelezo", seg=4)
    o = D.build(smooth_angle=40, origin=tuple(hinge))
    sgn = 1.0 if Vector((-dir_.y, dir_.x, 0)).dot(face) > 0 else -1.0       # kladné otočení kolem svislé osy = ke straně face
    o["otevreni_deg"] = float(ang_max) * sgn; o["otevira_se"] = "dovnitř" if opens_in else "ven"
    DOORS.append(o)
    return o

def ceiling(Ms, x0, x1, y0, y1, z, beam_axis="y", spacing=0.85, holes=(), key_beam="tram_in", key_board="podbiti", top_board=True):
    """strop: trámy (stropnice) + fošny navrch (zároveň podlaha půdy); z = spodek fošen"""
    if beam_axis == "y":
        for x in np.arange(x0 + 0.25, x1 - 0.1, spacing):
            T(Ms, (x, y0 - 0.05, z - 0.09), (x, y1 + 0.05, z - 0.09), 0.16, 0.18, key=key_beam, wane=0.5, bow=0.02)
    else:
        for y in np.arange(y0 + 0.25, y1 - 0.1, spacing):
            T(Ms, (x0 - 0.05, y, z - 0.09), (x1 + 0.05, y, z - 0.09), 0.16, 0.18, key=key_beam, wane=0.5, bow=0.02)
    if not top_board: return
    if beam_axis == "y":                                             # fošny kolmo na trámy
        y = y0
        while y < y1 - 0.02:
            bw = min(random.uniform(0.22, 0.32), y1 - y); ya, yb = y, y + bw
            for (xa, xb) in splitr(x0, x1, [(h[0], h[1]) for h in holes if h[2] < yb and h[3] > ya]):
                box(Ms, ((xa + xb) / 2, (ya + yb) / 2, z + 0.025), (xb - xa, bw - 0.006, 0.05), Matrix.Identity(3), key_board, uvs=1.2)
            y = yb
    else:
        x = x0
        while x < x1 - 0.02:
            bw = min(random.uniform(0.22, 0.32), x1 - x); xa, xb = x, x + bw
            for (ya, yb) in splitr(y0, y1, [(h[2], h[3]) for h in holes if h[0] < xb and h[1] > xa]):
                box(Ms, ((xa + xb) / 2, (ya + yb) / 2, z + 0.025), (bw - 0.006, yb - ya, 0.05), Matrix.Identity(3), key_board, uvs=1.2)
            x = xb

def plank_floor(Ms, x0, x1, y0, y1, z, axis="x", key="podbiti", holes=()):
    if axis == "x":
        y = y0
        while y < y1 - 0.02:
            bw = min(random.uniform(0.24, 0.34), y1 - y)
            for (xa, xb) in splitr(x0, x1, [(h[0], h[1]) for h in holes if h[2] < y + bw and h[3] > y]):
                box(Ms, ((xa + xb) / 2, y + bw / 2, z - 0.025 + random.uniform(-0.004, 0.004)), (xb - xa, bw - 0.005, 0.05), Matrix.Identity(3), key, uvs=1.3)
            y += bw
    else:
        x = x0
        while x < x1 - 0.02:
            bw = min(random.uniform(0.24, 0.34), x1 - x)
            for (ya, yb) in splitr(y0, y1, [(h[2], h[3]) for h in holes if h[0] < x + bw and h[1] > x]):
                box(Ms, (x + bw / 2, (ya + yb) / 2, z - 0.025 + random.uniform(-0.004, 0.004)), (bw - 0.005, yb - ya, 0.05), Matrix.Identity(3), key, uvs=1.3)
            x += bw

def dirt_floor(Ms, x0, x1, y0, y1, z, key="hlina"):
    F(Ms, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [(x0 / 1.5, y0 / 1.5), (x1 / 1.5, y0 / 1.5), (x1 / 1.5, y1 / 1.5), (x0 / 1.5, y1 / 1.5)], key, (0, 0, 1))

def clay_oven(Ms, x0, x1, y0, y1, zf, base_h=0.55, top_h=1.55, sooty=False):
    """hliněná pec (vytápění a pečení): podezdívka s lavicí kolem, oblá klenba z hlíny, nahoře začouzená"""
    box(Ms, ((x0 + x1) / 2, (y0 + y1) / 2, zf + base_h / 2), (x1 - x0, y1 - y0, base_h), Matrix.Identity(3), "pec", uvs=1.0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; rx, ry = (x1 - x0) / 2 - 0.06, (y1 - y0) / 2 - 0.06; hz = top_h - base_h
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
    for v in bm.verts:
        if v.co.z < 0: v.co.z = 0
        v.co = Vector((cx + v.co.x * rx * (1 + 0.04 * math.sin(v.co.y * 5 + v.co.z * 3)), cy + v.co.y * ry * (1 + 0.03 * math.sin(v.co.x * 6)), zf + base_h + v.co.z * hz * (1 + 0.05 * math.sin(v.co.x * 4 + v.co.y * 3))))
    for f in bm.faces:
        pts = [v.co.copy() for v in f.verts]; cz = sum(p.z for p in pts) / len(pts)
        if all(p.z <= zf + base_h + 1e-4 for p in pts): continue
        key = "pec_c" if (sooty or cz > zf + base_h + hz * (0.45 + 0.3 * random.random())) else "pec"
        Ms.face(pts, [(p.x / 0.8 + p.z / 0.8, p.y / 0.8) for p in pts], key)
    bm.free()

def wall_bench(Ms, p0, p1, z, depth, inward, key="tram_in"):
    """lavice podél stěny: fošna na kozlících z kuláčů"""
    a = Vector((p0[0], p0[1], 0)); b = Vector((p1[0], p1[1], 0)); d = (b - a); Ln = d.length; d.normalize(); n = Vector(inward).normalized()
    board(Ms, (a + b) / 2 + n * (depth / 2) + Vector((0, 0, z - 0.025)), d, n, (0, 0, 1), Ln, depth, 0.05, key, tilt=0.003)
    for k in range(max(2, int(Ln / 1.3) + 1)):
        p = a.lerp(b, (k + 0.5) / max(2, int(Ln / 1.3) + 1)) + n * (depth / 2)
        for sg in (-1, 1):
            pole(Ms, p + n * (sg * depth * 0.32) + Vector((0, 0, z - 0.05)), p + n * (sg * depth * 0.38) + Vector((0, 0, z - 0.45)), 0.03, 0.028, key="tram_d", bend=0.01, seg=6, bark=0.2)

def bed(Ms, c, yaw, w=0.95, l=1.95, h=0.45):
    """postel: rám z fošen, slamník a lněná pokrývka"""
    c = Vector(c); U = Vector((math.cos(yaw), math.sin(yaw), 0)); V = Vector((-U.y, U.x, 0)); Rm = Matrix((U, V, Vector((0, 0, 1)))).transposed()
    for sg in (-1, 1):
        T(Ms, c + V * (sg * w / 2) - U * (l / 2) + Vector((0, 0, h - 0.10)), c + V * (sg * w / 2) + U * (l / 2) + Vector((0, 0, h - 0.10)), 0.05, 0.16, key="tram_in", wane=0.3)
        for su in (-1, 1):
            T(Ms, c + V * (sg * (w / 2 - 0.02)) + U * (su * (l / 2 - 0.02)) + Vector((0, 0, 0.0)), c + V * (sg * (w / 2 - 0.02)) + U * (su * (l / 2 - 0.02)) + Vector((0, 0, h + (0.35 if su < 0 else 0.1))),
              0.07, 0.07, key="tram_in", wane=0.3)
    board(Ms, c - U * (l / 2) + Vector((0, 0, h + 0.10)), V, (0, 0, 1), U, w, 0.40, 0.035, "tram_in", tilt=0.003)
    box(Ms, c + Vector((0, 0, h + 0.04)), (l - 0.12, w - 0.12, 0.14), Rm, "slama", uvs=0.8)
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=8, y_segments=5, size=0.5)
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        v.co = c + U * (x * (l - 0.25) + 0.1) + V * (y * (w + 0.06)) + Vector((0, 0, h + 0.13 + 0.03 * math.sin(x * 9 + y * 4) * (1 - abs(y) * 1.6) - max(0.0, abs(y) - 0.42) * 1.2))
    for f in bm.faces: Ms.face([v.co.copy() for v in f.verts], [(v.co.x * 2, v.co.y * 2) for v in f.verts], "len")
    bm.free()

def ladder(Ms, p0, p1, w=0.46, step=0.30, key="tram_in"):
    a = Vector(p0); b = Vector(p1); d = (b - a); Ln = d.length; s = Vector((d.y, -d.x, 0)).normalized() if abs(d.z) < Ln * 0.999 else Vector((1, 0, 0))
    side = s if s.length > 0.1 else Vector((1, 0, 0))
    for sg in (-1, 1): pole(Ms, a + side * (sg * w / 2), b + side * (sg * w / 2), 0.035, 0.03, key=key, bend=0.015, seg=7, bark=0.25)
    k = 1
    while k * step < Ln - 0.15:
        p = a + d.normalized() * (k * step)
        pole(Ms, p - side * (w / 2 + 0.03), p + side * (w / 2 + 0.03), 0.019, 0.017, key=key, bend=0.004, seg=6, bark=0.0)
        k += 1

def stairs(Ms, p0, p1, w, rail=True, key="tram_in"):
    """schody: dvě schodnice (otesané), stupně z fošen, zábradlí"""
    a = Vector(p0); b = Vector(p1); hd = Vector((b.x - a.x, b.y - a.y, 0)); run = hd.length; hd.normalize(); s = Vector((-hd.y, hd.x, 0))
    rise = b.z - a.z; n = max(3, int(round(rise / 0.19))); st = rise / n
    for sg in (-1, 1):
        T(Ms, a + s * (sg * w / 2) + Vector((0, 0, 0.05)), b + s * (sg * w / 2) + Vector((0, 0, -0.08)), 0.07, 0.24, key=key, up=tuple(s.cross(b - a).normalized() * -1), wane=0.3, bow=0.01)
    for k in range(1, n + 1):
        p = a + hd * (run * (k - 0.5) / n) + Vector((0, 0, st * k - 0.02))
        board(Ms, p, s, hd, (0, 0, 1), w + 0.06, run / n + 0.05, 0.045, key, tilt=0.004)
    if rail:
        for t_ in (0.05, 0.5, 0.95):
            p = a.lerp(b, t_) + s * (w / 2 + 0.05)
            T(Ms, p, p + Vector((0, 0, 0.95)), 0.07, 0.07, key=key, up=(1, 0, 0), wane=0.2)
        pole(Ms, a + s * (w / 2 + 0.05) + Vector((0, 0, 1.0)), b + s * (w / 2 + 0.05) + Vector((0, 0, 0.92)), 0.035, 0.03, key=key, bend=0.01, seg=6, bark=0.0)

def counter(Ms, p0, p1, depth, inward, h=1.05, key="tram_in"):
    """výčepní pult: čelo z fošen, deska, sloupky"""
    a = Vector((p0[0], p0[1], 0)); b = Vector((p1[0], p1[1], 0)); d = (b - a); Ln = d.length; d.normalize(); n = Vector(inward).normalized()
    x = 0.0
    while x < Ln - 0.02:
        bw = min(random.uniform(0.2, 0.3), Ln - x)
        board(Ms, a + d * (x + bw / 2) + Vector((0, 0, (h - 0.06) / 2 + 0.02)), d, (0, 0, 1), -n, bw - 0.004, h - 0.08, 0.04, "dvere", tilt=0.004)
        x += bw
    board(Ms, (a + b) / 2 + n * (depth / 2 - 0.05) + Vector((0, 0, h)), d, n, (0, 0, 1), Ln + 0.12, depth + 0.08, 0.07, key, waney=True, tilt=0.002)
    board(Ms, (a + b) / 2 + n * (depth - 0.05) + Vector((0, 0, 0.55)), d, n, (0, 0, 1), Ln - 0.1, depth * 0.6, 0.04, key, tilt=0.002)
    for t_ in (0.02, 0.5, 0.98):
        p = a.lerp(b, t_) + n * (depth - 0.08)
        T(Ms, p, p + Vector((0, 0, h - 0.05)), 0.09, 0.09, key=key, up=(1, 0, 0), wane=0.3)

def barrel_rack(Ms, p0, p1, h=0.45):
    """ležení na sudy: dva otesané trámy na kamenech"""
    a = Vector((p0[0], p0[1], 0)); b = Vector((p1[0], p1[1], 0)); d = (b - a).normalized(); n = Vector((-d.y, d.x, 0))
    for sg in (-1, 1):
        T(Ms, a + n * (sg * 0.22) + Vector((0, 0, h)), b + n * (sg * 0.22) + Vector((0, 0, h)), 0.14, 0.16, key="tram_d", wane=0.5)
        for t_ in (0.1, 0.9):
            stone(Ms, a.lerp(b, t_) + n * (sg * 0.22) + Vector((0, 0, h - 0.09)), d, n, (0, 0, 1), 0.28, 0.24, h - 0.07, "kamen_s", detail=True, bulge=0.02, tilt=0.15)

def manger(Ms, p0, p1, z=0.75):
    """jesle (žlab) + žebřiny na seno nad nimi"""
    a = Vector((p0[0], p0[1], 0)); b = Vector((p1[0], p1[1], 0)); d = (b - a); Ln = d.length; d.normalize(); n = Vector((-d.y, d.x, 0))
    board(Ms, (a + b) / 2 + Vector((0, 0, z - 0.25)), d, n, (0, 0, 1), Ln, 0.5, 0.05, "tram_d")
    board(Ms, (a + b) / 2 + n * 0.25 + Vector((0, 0, z - 0.1)), d, (0, 0, 1), n, Ln, 0.32, 0.05, "tram_d", waney=True)
    for k in range(int(Ln / 1.2) + 2):
        p = a + d * min(Ln, k * 1.2)
        T(Ms, p + n * 0.25, p + n * 0.25 + Vector((0, 0, z)), 0.10, 0.10, key="tram_d", up=(1, 0, 0), wane=0.4)
    pole(Ms, a + Vector((0, 0, 1.0)), b + Vector((0, 0, 1.0)), 0.04, key="tram_d", bend=0.01)
    pole(Ms, a + n * 0.45 + Vector((0, 0, 1.7)), b + n * 0.45 + Vector((0, 0, 1.7)), 0.04, key="tram_d", bend=0.01)
    for k in range(int(Ln / 0.14)):
        p = a + d * (k * 0.14 + 0.07)
        pole(Ms, p + Vector((0, 0, 1.0)), p + n * 0.45 + Vector((0, 0, 1.7)), 0.015, key="tram_d", bend=0.003, seg=5, bark=0.0, caps=(False, False))

def wall_cols(name, p0, p1, z0, z1, t, door_holes=()):
    a, d, Ln, n = wall_frame2(p0, p1)
    for (ua, ub) in splitr(0, Ln, [(h[0], h[1]) for h in door_holes]):
        if ub - ua < 0.05: continue
        c0 = a + d * ua; c1 = a + d * ub
        lo = Vector((min(c0.x, c1.x), min(c0.y, c1.y), z0)) - Vector((abs(n.x) * t / 2, abs(n.y) * t / 2, 0))
        hi = Vector((max(c0.x, c1.x), max(c0.y, c1.y), z1)) + Vector((abs(n.x) * t / 2, abs(n.y) * t / 2, 0))
        colbox("%s%d" % (name, len(KOL)), lo, hi)
    for h in door_holes:                                            # nadpraží nad dveřmi
        c0 = a + d * h[0]; c1 = a + d * h[1]
        lo = Vector((min(c0.x, c1.x), min(c0.y, c1.y), h[3])) - Vector((abs(n.x) * t / 2, abs(n.y) * t / 2, 0))
        hi = Vector((max(c0.x, c1.x), max(c0.y, c1.y), z1)) + Vector((abs(n.x) * t / 2, abs(n.y) * t / 2, 0))
        if hi.z - lo.z > 0.05: colbox("%sN%d" % (name, len(KOL)), lo, hi)

# ---------------------------------------------------------------- sedlová střecha (krokve z kuláčů, latě, šindel, štíty)
class Roof:
    """sedlová střecha nad obdélníkem: osa hřebene A (jednotkový vektor x nebo y), střed c0, délka (a0..a1),
    polovina šířky hw (k vnějšímu líci zdi), zp = výška vršku pozednice, sklon, přesahy"""
    def __init__(s, c0, A, a0, a1, hw, zp, pitch=45, over=0.6, gover=0.4, r=0.08):
        s.c0 = Vector(c0); s.A = Vector(A).normalized(); s.C = Vector((-s.A.y, s.A.x, 0)); s.a0, s.a1 = a0, a1; s.hw = hw; s.zp = zp
        s.p = math.radians(pitch); s.over = over; s.gover = gover; s.r = r
        s.tp, s.cp, s.sp = math.tan(s.p), math.cos(s.p), math.sin(s.p)
        s.dmax = (hw + over) / s.cp; s.zr = zp + 2 * r / s.cp + hw * s.tp
    def W(s, a, c, z): return s.c0 + s.A * a + s.C * c + Vector((0, 0, z))
    def S(s, sg): return (s.C * (-sg * s.cp) + Vector((0, 0, s.sp))).normalized()
    def N(s, sg): return (s.C * (sg * s.sp) + Vector((0, 0, s.cp))).normalized()
    def Q(s, sg, a, d):                                    # bod na vršku krokví
        return s.W(a, sg * (s.hw + s.over), s.zp + 2 * s.r / s.cp - s.over * s.tp) + s.S(sg) * d
    def z_under(s, c): return s.zp + (s.hw - abs(c)) * s.tp - 0.02
    def build(s, KS, SH, rafter_a, tie_a=(), collar_z=None, skip=None, keyf=None, gable_vent=True, gables=(True, True), gable_z0=None,
              key_r="tram_in", dymnik_a=None, laths_inside_key="tram_in"):
        """skip(sg, a, d) -> True: vynechat šindel (komín, dymník)"""
        for a in rafter_a:
            for sg in (-1, 1):
                pole(KS, s.Q(sg, a, 0) - s.N(sg) * s.r, s.Q(sg, a, s.dmax + 0.12) - s.N(sg) * s.r, s.r, s.r * 0.85, key=key_r, bend=0.03, seglen=0.55)
            if collar_z:
                c_ = s.hw - (collar_z - s.zp - s.r / s.cp) / s.tp
                if c_ > 0.3:
                    T(KS, s.W(a + 0.1, -c_ - 0.1, collar_z), s.W(a + 0.1, c_ + 0.1, collar_z), 0.10, 0.15, key=key_r, wane=0.6)
                    for sg in (-1, 1): peg(KS, s.W(a + 0.16, sg * c_, collar_z), s.A, r=0.014)
        for a in tie_a:
            T(KS, s.W(a, -s.hw - 0.25, s.zp + 0.11), s.W(a, s.hw + 0.25, s.zp + 0.11), 0.22, 0.22, key=key_r, wane=0.5)
        for sg in (-1, 1):                                   # latě
            for d in np.arange(0.06, s.dmax - 0.05, 0.36):
                segs = [(s.a0 - s.gover + 0.02, s.a1 + s.gover - 0.02)]
                if skip:
                    cut = [(a_ - 0.02, a_ + 0.02) for a_ in np.arange(s.a0 - s.gover, s.a1 + s.gover, 0.04) if skip(sg, a_, d)]
                    segs = splitr(segs[0][0], segs[0][1], cut)
                for (aa, ab) in segs:
                    if ab - aa < 0.2: continue
                    T(KS, s.Q(sg, aa, d) + s.N(sg) * 0.02, s.Q(sg, ab, d) + s.N(sg) * 0.02, 0.065, 0.04, key=laths_inside_key, up=tuple(s.N(sg)),
                      wane=0.3, seglen=2.2, bow=0.012, ch=0.008)
        for ag in (s.a0 - s.gover - 0.04, s.a1 + s.gover + 0.04):        # závětrné desky (krajinky)
            for sg in (-1, 1):
                p0 = s.Q(sg, ag, -0.02) + s.N(sg) * 0.06; p1 = s.Q(sg, ag, s.dmax + 0.18) + s.N(sg) * 0.06
                X_, Y_, Z_, L_ = frame_axes(p0, p1, (0, 0, 1))
                board(SH, (p0 + p1) / 2, Y_ if abs(Y_.z) > 0.5 else Z_, X_, s.A * (1 if ag > 0 else -1) if True else s.A, 0.26, L_, 0.035, "prkna", waney=True, tilt=0.003)
        cnt = 0
        for sg in (-1, 1):
            P0 = s.Q(sg, 0, 0) + s.N(sg) * 0.04
            sk = (lambda am, s0, s1, sg=sg: skip(sg, am, s0) or skip(sg, am, s1)) if skip else (lambda am, s0, s1: False)
            kf = keyf or (lambda am, s0, sg=sg: s.roof_key(sg, am, s0))
            cnt += shingles(SH, P0 - s.A * 0.0, s.A, s.S(sg), s.N(sg), s.a0 - s.gover + 0.03, s.a1 + s.gover - 0.03, s.dmax + 0.03, sk,
                            (lambda am, s0, kf=kf, sg=sg: kf(am, s0)) if keyf is None else (lambda am, s0, sg=sg: keyf(sg, am, s0)))
        for sg in (-1, 1):                                   # hřebenová prkna (přerušená u komína/dymníku)
            a = s.Q(sg, 0, s.dmax - 0.14) + s.N(sg) * (0.04 + 0.075)
            cut = [(a_ - 0.02, a_ + 0.02) for a_ in np.arange(s.a0 - s.gover, s.a1 + s.gover, 0.04) if skip and skip(sg, a_, s.dmax - 0.05)]
            for (aa, ab) in splitr(s.a0 - s.gover + 0.02, s.a1 + s.gover - 0.02, cut):
                if ab - aa < 0.1: continue
                box(SH, a + s.A * ((aa + ab) / 2), (ab - aa, 0.30, 0.03), Matrix((s.A, s.S(sg), s.N(sg))).transposed(), "prkna", uvs=1.2)
        for gi, ag in enumerate((s.a0, s.a1)):              # štíty z prken s průduchem
            if not gables[gi]: continue
            nrm = s.A * (-1 if gi == 0 else 1)
            O = s.W(ag, 0, 0) + nrm * 0.01
            z0g = gable_z0 if gable_z0 is not None else s.zp
            ztop = (lambda u: min(s.z_under(u), s.zr - 0.75) if (gable_vent and abs(u) < 0.32) else s.z_under(u))
            clad(KS, O, s.C, nrm, -s.hw - 0.05, s.hw + 0.05, z0g, ztop, battens=False)
            if gable_vent: pole(KS, O + nrm * 0.03 - s.C * 0.36 + Vector((0, 0, s.zr - 0.75)), O + nrm * 0.03 + s.C * 0.36 + Vector((0, 0, s.zr - 0.75)), 0.035, key="tram_g", bend=0.01, seg=6)
        if dymnik_a is not None:                            # dymník: stříška nad otvorem v hřebeni (černá kuchyně)
            for sg in (-1, 1):
                for da in (-0.45, 0.45):
                    T(KS, s.W(dymnik_a + da, sg * 0.42, s.zr - 0.3), s.W(dymnik_a + da, sg * 0.42, s.zr + 0.45), 0.08, 0.08, key="tram_c", up=tuple(s.A), wane=0.3)
            sub = Roof(s.W(dymnik_a, 0, 0), s.A, -0.55, 0.55, 0.5, s.zr + 0.42, pitch=35, over=0.15, gover=0.12, r=0.04)
            for sg in (-1, 1):
                P0 = sub.Q(sg, 0, 0) + sub.N(sg) * 0.02
                shingles(SH, P0, sub.A, sub.S(sg), sub.N(sg), -0.66, 0.66, sub.dmax + 0.02, lambda am, s0, s1: False, lambda am, s0: "sindel_t")
                for a_ in (-0.5, 0.5): pole(KS, sub.Q(sg, a_, 0) - sub.N(sg) * 0.04, sub.Q(sg, a_, sub.dmax + 0.05) - sub.N(sg) * 0.04, 0.035, key="tram_c", bend=0.01, seg=6)
        return cnt
    def roof_key(s, sg, a, d):
        nmx = float(fbm(np.array(a * 0.25 + sg * 7.3 + s.c0.x * 0.1), np.array(d * 0.32 + 3.1 + s.c0.y * 0.1), 4, 3))
        wet = 0.28 * (1 - sm(0.0, 1.8, d)) + (0.20 if (s.C * sg).y > 0.5 or (s.C * sg).x < -0.5 else -0.04) - 0.2 * sm(s.dmax - 1.2, s.dmax, d)
        mval = nmx + wet + random.gauss(0, 0.05)
        if mval > 0.72: return "sindel_m"
        if mval > 0.60: return "sindel_m1"
        if float(fbm(np.array(a * 1.6), np.array(d * 0.08), 2, 1)) > 0.66 and random.random() < 0.45: return "sindel_t"
        return "sindel"

def empty(name, loc, size=0.15):
    e = bpy.data.objects.new(name, None); e.location = loc; e.empty_display_size = size; scene.collection.objects.link(e); return e

def export_all(basename, lod_objs=(), active=None):
    for o in scene.objects: o.select_set(False)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, basename + ".blend"), compress=True)
    game = [o for o in scene.objects if o.name.startswith(PFX + "_")]
    for o in game: o.select_set(True)
    bpy.context.view_layer.objects.active = active or game[0]
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, basename + ".glb"), export_format='GLB', use_selection=True,
                              export_apply=False, export_yup=True, export_image_format='AUTO', export_extras=True, export_vertex_color='MATERIAL')
    tris = 0; dg = bpy.context.evaluated_depsgraph_get(); per = {}
    for o in game:
        if o.type != 'MESH' or "Kol_" in o.name: continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); per[o.name] = len(me.loop_triangles); tris += len(me.loop_triangles)
        o.evaluated_get(dg).to_mesh_clear()
    for k_ in sorted(per, key=lambda k: -per[k])[:25]: print("  %-34s %7d tri" % (k_, per[k_]))
    print("CELKEM trojúhelníků:", tris, "| kolizních kvádrů:", len(KOL), "| dveří:", len(DOORS))
    if lod_objs:
        for o in scene.objects: o.select_set(False)
        for o in lod_objs: o.select_set(True)
        bpy.context.view_layer.objects.active = lod_objs[0]
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, basename + "_lod1.glb"), export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_image_format='AUTO')
        lt = 0
        for o in lod_objs:
            me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); lt += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear(); to_prev(o); o.hide_render = True
        print("LOD1 trojúhelníků:", lt)

def cam(nm, loc, target, lens=24):
    c = bpy.data.cameras.new(nm); c.lens = lens; c.clip_start = 0.05
    o = bpy.data.objects.new(nm, c); scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o
def render_views(views, outdir):
    scene.render.engine = 'CYCLES'; cy = scene.cycles; cy.device = 'CPU'
    cy.samples = int(os.environ.get("SAMPLES", 32)); cy.use_denoising = True; cy.max_bounces = 6
    scene.render.resolution_x = int(os.environ.get("RX", 1280)); scene.render.resolution_y = int(os.environ.get("RY", 720))
    scene.view_settings.view_transform = 'AgX'
    try: scene.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    only = os.environ.get("VIEWS")
    for nm, (loc, tgt, lens, ex) in views.items():
        if only and nm not in only.split(","): continue
        scene.view_settings.exposure = ex
        scene.camera = cam("Kam_" + nm, loc, tgt, lens)
        scene.render.filepath = os.path.join(outdir, nm + ".png")
        print("render", nm); bpy.ops.render.render(write_still=True)
