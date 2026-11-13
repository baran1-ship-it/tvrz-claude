"""Dlouhé vlasy: sčesané dozadu z pěšinky, silný cop po záda, dva volné prameny u obličeje.
Stylizované chomáče (bez průhlednosti – na tabletu bez problémů s řazením)."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree

C = Vector((0, 0.008, 1.655))   # střed hlavy

def make_bvh(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.transform(obj.matrix_world)
    return BVHTree.FromBMesh(bm)

def surf(bvh, d, off):
    """bod na povrchu hlavy ve směru d od středu + odsazení po normále"""
    d = d.normalized()
    hit = bvh.ray_cast(C + d * 0.25, -d, 0.3)
    if hit[0] is None:
        loc, n, i, dist = bvh.find_nearest(C + d * 0.1)
    else: loc, n = hit[0], hit[1]
    return loc + n.normalized() * off, n.normalized()

def catmull(P, n):
    P = [P[0]] + list(P) + [P[-1]]
    out = []
    segs = len(P) - 3
    for s in range(segs):
        p0, p1, p2, p3 = P[s:s+4]
        for k in range(n):
            t = k / n
            out.append(0.5*((2*p1) + (-p0+p2)*t + (2*p0-5*p1+4*p2-p3)*t*t + (-p0+3*p1-3*p2+p3)*t*t*t))
    out.append(P[-2]); return out

def ribbon(bm, uvl, pts, nrm, widths, thick, sides=6, v_scale=0.18, u0=0.0):
    """tubus se zploštělým průřezem podél pts; nrm = normála (směr zploštění)"""
    rings = []
    L = 0.0; vv = [0.0]
    for i in range(1, len(pts)): L += (pts[i]-pts[i-1]).length; vv.append(L)
    for i, p in enumerate(pts):
        t = (pts[min(i+1, len(pts)-1)] - pts[max(i-1, 0)]).normalized()
        n = (nrm[i] - t * nrm[i].dot(t)).normalized()
        b = t.cross(n).normalized()
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            ring.append(bm.verts.new(p + b * math.cos(a) * widths[i] * 0.5 + n * math.sin(a) * thick[i] * 0.5))
        rings.append(ring)
    faces = []
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i+1][k2], rings[i+1][k]))
            for l, (ii, kk) in zip(f.loops, ((i, k), (i, k+1), (i+1, k+1), (i+1, k))):
                l[uvl].uv = (u0 + kk / sides * 0.5, vv[ii] / v_scale)
            faces.append(f)
    # uzávěry
    for ring in (rings[0], rings[-1][::-1]):
        try:
            f = bm.faces.new(ring[::-1] if ring is rings[0] else ring)
            for l in f.loops: l[uvl].uv = (u0 + 0.25, 0.5)
            faces.append(f)
        except ValueError: pass
    return [v for r in rings for v in r], faces

def build(head_obj, arm, name="zena30_vlasy", seed=3):
    rng = np.random.default_rng(seed)
    bvh = make_bvh(head_obj)
    me = bpy.data.meshes.new(name); obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    groups = {}   # vertex -> [(bone, w)]
    def V(x, y, z): return (Vector((x, y, z)) - C)
    nape = Vector((0, 0.088, 1.585))
    # ---- vlasy na hlavě: rodina drah od linie čela (s=0) po temeno (s=1), obě strany
    for side in (1, -1):
        N = 15
        for i in range(N):
            s = i / (N - 1)
            s2 = s + rng.uniform(-0.02, 0.02)
            # řídicí body (směry od středu)
            part_y = -0.07 + 0.13 * s2        # začátek na pěšince
            P0 = V(side * 0.006, part_y, 1.765 - 0.02 * abs(part_y) / 0.07 if part_y < 0 else 1.768)
            # okraj (vlasová linie) vs. temeno
            edge = [V(side*0.006, -0.075, 1.735), V(side*0.05, -0.065, 1.715), V(side*0.078, -0.03, 1.69),
                    V(side*0.088, 0.015, 1.665), V(side*0.075, 0.07, 1.625), V(side*0.03, 0.095, 1.592)]
            crown = [V(side*0.006, 0.06, 1.77), V(side*0.012, 0.095, 1.73), V(side*0.014, 0.115, 1.68),
                     V(side*0.012, 0.11, 1.63), V(side*0.01, 0.1, 1.60), V(side*0.008, 0.094, 1.588)]
            ctrl = [P0] + [e*(1-s) + c*s for e, c in zip(edge[1:], crown[1:])]
            dirs = catmull(ctrl, 3)
            off = 0.006 + 0.004 * (1 - s) + rng.uniform(0, 0.002)
            pts, nrm = [], []
            for j, d in enumerate(dirs):
                p, n = surf(bvh, d, off + 0.002 * math.sin(math.pi * j / (len(dirs)-1)))
                pts.append(p); nrm.append(n)
            # poslední body sbíhají do týlu (začátek copu)
            k = len(pts)
            for j in range(k - 4, k):
                a = (j - (k - 5)) / 4
                pts[j] = pts[j].lerp(nape + Vector((side * 0.012, 0.004, 0)), a * 0.85)
            w = [0.034 + 0.010 * (1 - s)] * k
            for j in range(k):
                tt = j / (k - 1)
                w[j] *= (0.55 + 0.45 * math.sin(math.pi * min(tt * 1.6 + 0.2, 1.0))) * (1 - 0.45 * tt ** 2)
            th = [0.006 + 0.002 * math.sin(math.pi * j / (k - 1)) for j in range(k)]
            vs, _ = ribbon(bm, uvl, pts, nrm, w, th, sides=5, u0=rng.uniform(0, 0.5))
            for v in vs: groups[v] = [("Head", 1.0)]
    # ---- volné prameny u obličeje (před ušima), na každé straně 2
    for side in (1, -1):
        for k in range(0):
            a = [V(side*(0.040+0.012*k), -0.068+0.01*k, 1.728), V(side*(0.072+0.006*k), -0.048+0.008*k, 1.695),
                 V(side*(0.084+0.004*k), -0.035+0.01*k, 1.64), V(side*(0.082), -0.03+0.012*k, 1.595)]
            dirs = catmull(a, 3); pts, nrm = [], []
            for j, d in enumerate(dirs):
                p, n = surf(bvh, d, 0.009 + 0.004 * k)
                pts.append(p); nrm.append(n)
            # konec volně dolů k čelisti
            last = pts[-1]
            for j in range(1, 7):
                pts.append(last + Vector((side * (0.0035 * j - 0.0002 * j * j), -0.0025 * j, -0.011 * j))); nrm.append(nrm[-1])
            kk = len(pts)
            w = [0.024 * (1 - 0.75 * (j / (kk - 1)) ** 1.3) for j in range(kk)]
            th = [0.006 * (1 - 0.5 * j / (kk - 1)) for j in range(kk)]
            vs, _ = ribbon(bm, uvl, pts, nrm, w, th, u0=0.25)
            for v in vs: groups[v] = [("Head", 1.0)]
    # ---- cop
    def back_y(z):  # povrch zad + šaty + poloměr copu
        tab = [(1.585, 0.095), (1.52, 0.115), (1.46, 0.140), (1.40, 0.165), (1.32, 0.17), (1.22, 0.162), (1.10, 0.15), (1.00, 0.145)]
        zs = [t[0] for t in tab][::-1]; ys = [t[1] for t in tab][::-1]
        return float(np.interp(z, zs, ys))
    z0, z1 = 1.585, 1.02
    nl = 17
    path = [Vector((0, back_y(z), z)) for z in np.linspace(z0, z1, nl * 2 + 1)]
    for i in range(nl):
        t = i / (nl - 1)
        for side in (1, -1):
            zc = z0 - (z0 - z1) * (i + (0.5 if side < 0 else 0)) / nl
            r = 0.022 * (1 - 0.45 * t) + 0.004
            c = Vector((side * r * 0.42, back_y(zc), zc))
            ln = (z0 - z1) / nl * 1.25
            # lalok = zploštělý elipsoid nakloněný ke středu
            segs, ringn = 5, 7
            q = Quaternion((0, 1, 0), side * math.radians(32))
            rings = []
            for a in range(segs + 1):
                u = a / segs; zz = (u - 0.5) * ln
                rr = math.sin(math.pi * u) ** 0.7 * r * 0.95 + 0.0015
                ring = []
                for b in range(ringn):
                    ang = 2 * math.pi * b / ringn
                    loc = Vector((math.cos(ang) * rr, math.sin(ang) * rr * 0.8, zz))
                    ring.append(bm.verts.new(c + q @ loc))
                rings.append(ring)
            for a in range(segs):
                for b in range(ringn):
                    b2 = (b + 1) % ringn
                    f = bm.faces.new((rings[a][b], rings[a][b2], rings[a+1][b2], rings[a+1][b]))
                    for l, (aa, bb) in zip(f.loops, ((a, b), (a, b+1), (a+1, b+1), (a+1, b))):
                        l[uvl].uv = (0.5 + bb / ringn * 0.5, aa / segs * 0.6)
            for v in [v for r_ in rings for v in r_]:
                groups[v] = None
    # konec copu: stužka (kožený řemínek) + volný štětec
    zt = z1 - 0.01
    tail = []
    for j in range(8):
        zz = zt - 0.012 * j; rr = 0.011 * (1 - j / 9) + 0.002 + (0.004 if j in (0, 1) else 0)
        tail.append((Vector((0, back_y(zz) - 0.002 * j, zz)), rr))
    rings = []
    for (p, rr) in tail:
        rings.append([bm.verts.new(p + Vector((math.cos(2*math.pi*b/8)*rr, math.sin(2*math.pi*b/8)*rr*0.8, 0))) for b in range(8)])
    for a in range(len(rings) - 1):
        for b in range(8):
            f = bm.faces.new((rings[a][b], rings[a][(b+1)%8], rings[a+1][(b+1)%8], rings[a+1][b]))
            for l, (aa, bb) in zip(f.loops, ((a, b), (a, b+1), (a+1, b+1), (a+1, b))):
                l[uvl].uv = (bb / 8 * 0.5, aa * 0.06)
    for v in [v for r_ in rings for v in r_]: groups[v] = None
    # řemínek
    tie = []
    for j in range(3):
        zz = z1 - 0.004 * j; rr = 0.0135
        tie.append([bm.verts.new(Vector((math.cos(2*math.pi*b/10)*rr, back_y(zz) + math.sin(2*math.pi*b/10)*rr*0.85, zz))) for b in range(10)])
    tie_faces = []
    for a in range(2):
        for b in range(10):
            f = bm.faces.new((tie[a][b], tie[a][(b+1)%10], tie[a+1][(b+1)%10], tie[a+1][b])); tie_faces.append(f)
            for l in f.loops: l[uvl].uv = (0.02, 0.98)
    for v in [v for r_ in tie for v in r_]: groups[v] = None
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # váhy copu podle výšky (hlava -> krk -> hrudník), aby se neprořezával do zad
    bones = arm.data.bones
    def bz(n): return (arm.matrix_world @ bones[n].head_local).z
    zH, zN, z3, z2 = bz("Head"), bz("neck_01"), bz("spine_03"), bz("spine_02")
    for v, g in list(groups.items()):
        if g is not None: continue
        z = v.co.z
        if z > zH - 0.01: groups[v] = [("Head", 1.0)]
        elif z > zN: a = (z - zN) / (zH - 0.01 - zN); groups[v] = [("Head", 0.5 + 0.5 * a), ("neck_01", 0.5 - 0.5 * a)]
        elif z > zN - 0.08: a = (z - (zN - 0.08)) / 0.08; groups[v] = [("neck_01", 0.5 * a + 0.2), ("spine_03", 0.8 - 0.5 * a)]
        else: groups[v] = [("spine_03", 1.0)]
    bm.verts.index_update()
    order = {v: v.index for v in bm.verts}
    tie_idx = set(f.index for f in tie_faces)
    bm.to_mesh(me); bm.free()
    for nm in set(b for g in groups.values() for b, _ in g):
        obj.vertex_groups.new(name=nm)
    for v, g in groups.items():
        for b, w in g: obj.vertex_groups[b].add([order[v]], w, 'REPLACE')
    obj.parent = arm
    mod = obj.modifiers.new("Armature", 'ARMATURE'); mod.object = arm
    for p in me.polygons: p.use_smooth = True
    return obj, tie_idx

def scalp_shell(body, hair_obj, arm, off=0.002, reach=0.015, name="zena30_vlasy_pokryv"):
    """Slupka pod vlasy z vrcholů hlavy, nad kterými jsou vlasy (žádná holá místa mezi chomáči)."""
    hm = hair_obj.data
    # jen chomáče hlavy (skupina Head)
    gi = hair_obj.vertex_groups["Head"].index
    pts = [hair_obj.matrix_world @ v.co for v in hm.vertices if any(g.group == gi and g.weight > 0.99 for g in v.groups) and (hair_obj.matrix_world @ v.co).z > 1.57]
    from mathutils.kdtree import KDTree
    kd = KDTree(len(pts))
    for i, p in enumerate(pts): kd.insert(p, i)
    kd.balance()
    bm = bmesh.new(); bm.from_mesh(body.data); bm.transform(body.matrix_world)
    keep = set()
    for v in bm.verts:
        if v.co.z < 1.575: continue
        co, i, d = kd.find(v.co)
        if d < reach: keep.add(v.index)
    bm.verts.ensure_lookup_table()
    dele = [f for f in bm.faces if not all(v.index in keep for v in f.verts)]
    bmesh.ops.delete(bm, geom=dele, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.normal_update()
    for v in bm.verts: v.co += v.normal * off
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.vertex_groups.new(name="Head").add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    o.parent = arm; md = o.modifiers.new("Armature", 'ARMATURE'); md.object = arm
    for p in me.polygons: p.use_smooth = True
    return o
