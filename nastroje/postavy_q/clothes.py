"""Oblečení postav: slupky z těla (kopírují tvar a váhy kostí) a trubky ze řezů (sukně kabátce, pláštík kapuce).
Vše se váže na armaturu postavy -> hýbe se s animacemi.
"""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, kdtree

BONES = None

def body_data(obj):
    import head_features as hf
    co, no = hf.evaluated_coords(obj)
    bones = _bone_list(obj)
    W = {b: hf.group_weights(obj, b) for b in bones}
    W["body"] = hf.group_weights(obj, "body")
    return co, no, W

BONE_NAMES = set("""pelvis spine_01 spine_02 spine_03 clavicle_l upperarm_l lowerarm_l hand_l clavicle_r upperarm_r lowerarm_r hand_r
neck_01 head thigh_l calf_l foot_l ball_l thigh_r calf_r foot_r ball_r""".split())

def _bone_list(obj):
    return [g.name for g in obj.vertex_groups if g.name in BONE_NAMES or g.name.startswith(("index_", "middle_", "ring_", "pinky_", "thumb_"))]

def mask_from(W, groups, thr=0.5):
    m = np.zeros(len(W["body"]))
    for g in groups:
        if g in W: m += W[g]
    return (m > thr) & (W["body"] > 0.5)

def _link(ob, obj):
    bpy.context.collection.objects.link(ob)
    arm = obj.parent if obj.parent and obj.parent.type == 'ARMATURE' else next((m.object for m in obj.modifiers if m.type == 'ARMATURE'), None)
    if obj.parent: ob.parent = obj.parent; ob.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
    if arm:
        md = ob.modifiers.new("Armature", 'ARMATURE'); md.object = arm
    return ob

def shell(obj, co, no, mask, offset, name, smooth=0, subdiv=0, offset_fn=None, smooth_border=0):
    """Kopie ploch těla, kde všechny vrcholy splňují mask; posun po normále; váhy kostí převzaté."""
    sel = np.where(mask)[0]; S = set(sel.tolist())
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    uv_src = bm.loops.layers.uv.active
    nbm = bmesh.new(); vmap = {}
    uv_dst = nbm.loops.layers.uv.new("UVMap")
    src_l = nbm.verts.layers.int.new("src")
    for f in bm.faces:
        if not all(v.index in S for v in f.verts): continue
        vs = []
        for v in f.verts:
            if v.index not in vmap:
                nv = nbm.verts.new(Vector(co[v.index])); nv[src_l] = v.index; vmap[v.index] = nv
            vs.append(vmap[v.index])
        try:
            nf = nbm.faces.new(vs)
            for l_new, l_old in zip(nf.loops, f.loops): l_new[uv_dst].uv = l_old[uv_src].uv
        except ValueError:
            pass
    bm.free()
    # osamělé kousky (méně než 30 ploch) pryč
    nbm.verts.ensure_lookup_table(); nbm.faces.ensure_lookup_table()
    seen = set(); kill = []
    for f in nbm.faces:
        if f in seen: continue
        comp = []; stack = [f]; seen.add(f)
        while stack:
            g = stack.pop(); comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen: seen.add(h); stack.append(h)
        if len(comp) < 30: kill += comp
    if kill: bmesh.ops.delete(nbm, geom=kill, context='FACES')
    loose = [v for v in nbm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(nbm, geom=loose, context='VERTS')
    nbm.normal_update()
    for _ in range(smooth):
        bmesh.ops.smooth_vert(nbm, verts=[v for v in nbm.verts if not v.is_boundary], factor=0.5,
                              use_axis_x=True, use_axis_y=True, use_axis_z=True)
    for _ in range(smooth_border):
        bv = [v for v in nbm.verts if v.is_boundary]
        newp = {}
        for v in bv:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2: newp[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
        for v, p in newp.items(): v.co = p
    nbm.normal_update()
    for v in nbm.verts:
        o = offset if offset_fn is None else offset_fn(v.co, offset)
        v.co += v.normal * o
    if subdiv:
        bmesh.ops.subdivide_edges(nbm, edges=list(nbm.edges), cuts=subdiv, use_grid_fill=True, smooth=0.5)
    me = bpy.data.meshes.new(name); nbm.to_mesh(me); nbm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    transfer_weights(ob, obj, co)
    return _link(ob, obj)

def transfer_weights(ob, obj, co, k=6, pelvis_blend=None):
    """Váhy kostí z nejbližších vrcholů těla (průměr k sousedů)."""
    import head_features as hf
    bones = _bone_list(obj)
    body = hf.group_weights(obj, "body")
    idx = np.where(body > 0.5)[0]
    kd = kdtree.KDTree(len(idx))
    for j, i in enumerate(idx): kd.insert(co[i], j)
    kd.balance()
    Wb = np.stack([hf.group_weights(obj, b) for b in bones], 1)
    me = ob.data
    acc = np.zeros((len(me.vertices), len(bones)))
    for v in me.vertices:
        res = kd.find_n(v.co, k)
        tw = 0
        for (p, j, d) in res:
            w = 1.0 / (d + 0.005); acc[v.index] += w * Wb[idx[j]]; tw += w
        acc[v.index] /= max(tw, 1e-9)
    if pelvis_blend is not None:
        pb = pelvis_blend(np.array([v.co[:] for v in me.vertices]))
        pi = bones.index("pelvis")
        acc *= (1 - pb)[:, None]; acc[:, pi] += pb
    acc /= np.maximum(acc.sum(1, keepdims=True), 1e-9)
    for bi, b in enumerate(bones):
        col = acc[:, bi]
        nz = np.where(col > 0.01)[0]
        if len(nz) == 0: continue
        g = ob.vertex_groups.new(name=b)
        for i in nz: g.add([int(i)], float(col[i]), 'REPLACE')

def tube(obj, co, sel_mask, z_top, z_bot, name, N=64, rows=None, ease=0.012, flare=0.0, hang=True,
         center=None, hem_noise=0.0, seed=0, cap_bottom=False, slice_tol=0.02, row_center=False):
    """Trubka podle obrysu řezů těla (obalová křivka); pod boky visí rovně (nepodléhá mezeře mezi nohama)."""
    rng = np.random.default_rng(seed)
    P = co[sel_mask]
    if center is None:
        band = P[(P[:, 2] < z_top) & (P[:, 2] > z_bot)]
        center = band[:, :2].mean(0)
    rows = rows or max(6, int((z_top - z_bot) / 0.025))
    zs = np.linspace(z_top, z_bot, rows + 1)
    th = np.linspace(0, 2 * np.pi, N, endpoint=False)
    R = np.zeros((rows + 1, N)); C = np.tile(np.asarray(center, float), (rows + 1, 1))
    for r, z in enumerate(zs):
        sl = P[np.abs(P[:, 2] - z) < slice_tol]
        if len(sl) < 5:
            R[r] = R[r - 1] if r else 0.1; C[r] = C[r - 1] if r else C[r]; continue
        if row_center: C[r] = 0.5 * (sl[:, :2].min(0) + sl[:, :2].max(0))
        d = sl[:, :2] - C[r]
        a = np.arctan2(d[:, 1], d[:, 0]); rad = np.hypot(d[:, 0], d[:, 1])
        for i, t in enumerate(th):
            da = np.abs((a - t + np.pi) % (2 * np.pi) - np.pi)
            m = da < 0.12
            R[r, i] = rad[m].max() if m.any() else 0
        # díry doplnit z konvexního obalu: v každém úhlu aspoň promítnutí bodů
        for i, t in enumerate(th):
            proj = d[:, 0] * math.cos(t) + d[:, 1] * math.sin(t)
            R[r, i] = max(R[r, i], proj.max() * 0.985)
    if row_center and rows > 2:
        R[0] = np.minimum(R[0], R[1]); C[0] = C[1]
    # vyhladit po obvodu
    for _ in range(3):
        R = 0.25 * np.roll(R, 1, 1) + 0.5 * R + 0.25 * np.roll(R, -1, 1)
    if hang:
        for r in range(1, rows + 1):
            R[r] = np.maximum(R[r], R[r - 1] * 0.995)
    for r in range(rows + 1):
        t = r / rows
        R[r] += ease + flare * t ** 1.5
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap"); hem_l = bm.verts.layers.float.new("hem")
    vs = []
    total_len = z_top - z_bot
    for r, z in enumerate(zs):
        row = []
        for i, t in enumerate(th):
            rr = R[r, i]
            zz = z
            if r == rows and hem_noise: zz += hem_noise * (rng.random() - 0.5)
            v = bm.verts.new((C[r][0] + rr * math.cos(t), C[r][1] + rr * math.sin(t), zz))
            v[hem_l] = r / rows
            row.append(v)
        vs.append(row)
    for r in range(rows):
        for i in range(N):
            j = (i + 1) % N
            f = bm.faces.new((vs[r][i], vs[r + 1][i], vs[r + 1][j], vs[r][j]))
            for lp, (uu, vv) in zip(f.loops, ((i, r), (i, r + 1), (i + 1, r + 1), (i + 1, r))):
                lp[uvl].uv = (uu / N, 1 - vv / rows)
    if cap_bottom:
        bmesh.ops.contextual_create(bm, geom=vs[-1])
    bm.normal_update()
    # normály ven
    for f in bm.faces:
        c = f.calc_center_median()
        if len(f.verts) > 4:
            if f.normal.z > 0: f.normal_flip()
            continue
        cc = C[min(range(len(zs)), key=lambda k: abs(zs[k] - c.z))]
        if f.normal.dot(Vector((c.x - cc[0], c.y - cc[1], 0))) < 0: f.normal_flip()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    return ob, center, R, zs

def hide_body_under(obj, mask, name="skryto"):
    """Plochy těla schované pod oblečením odstranit (aby nepropichovaly) – přes masku vertex group."""
    g = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
    g.add([int(i) for i in np.where(mask)[0]], 1.0, 'REPLACE')
    md = obj.modifiers.new("Skryj pod oblečením", 'MASK'); md.vertex_group = name; md.invert_vertex_group = True
    return md

def cut_iso(ob, fn, lip=0.0):
    """Ořízne síť podél izočáry fn(co)=0 (ponechá fn>0) – hladký okraj místo zubů po plochách těla.
    lip>0: okraj se podvine dovnitř (k tělu) o lip metrů, aby nebyla vidět mezera pod látkou."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    val = {v: fn(np.array(v.co)) for v in bm.verts}
    for v in bm.verts:
        if abs(val[v]) < 1e-6: val[v] = 1e-6
    cross = [e for e in bm.edges if (val[e.verts[0]] > 0) != (val[e.verts[1]] > 0)]
    newv = []
    for e in cross:
        a, b = e.verts; fa, fb = val[a], val[b]
        t = fa / (fa - fb)
        ne, nv = bmesh.utils.edge_split(e, a, t)
        val[nv] = 0.0; newv.append(nv)
    # spojit nové vrcholy v plochách
    nset = set(newv)
    for f in list({f for v in newv for f in v.link_faces}):
        vs = [v for v in f.verts if v in nset]
        if len(vs) == 2:
            try: bmesh.ops.connect_verts(bm, verts=vs)
            except Exception: pass
    kill = [v for v in bm.verts if val.get(v, 1.0) < -1e-9]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.normal_update()
    if lip > 0:
        bnd = [e for e in bm.edges if e.is_boundary and all(v in set(newv) for v in e.verts)]
        if bnd:
            ret = bmesh.ops.extrude_edge_only(bm, edges=bnd)
            nvs = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
            bm.normal_update()
            # posun dovnitř: proti normále sousední plochy
            for v in nvs:
                src = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) not in nvs]
                n = src[0].normal if src else v.normal
                v.co -= n * lip
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    for p in ob.data.polygons: p.use_smooth = True
    return ob
