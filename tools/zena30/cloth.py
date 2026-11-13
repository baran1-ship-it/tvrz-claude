"""Oblečení: slupky z těla + sukně z řezů. Váhy kostí převzaté z těla nebo navržené (sukně)."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector, kdtree

def body_arrays(body):
    me = body.data
    co = np.array([body.matrix_world @ v.co for v in me.vertices])
    me.calc_normals_split() if hasattr(me, "calc_normals_split") else None
    no = np.array([(body.matrix_world.to_3x3() @ v.normal).normalized() for v in me.vertices])
    names = [g.name for g in body.vertex_groups]
    W = np.zeros((len(me.vertices), len(names)))
    for v in me.vertices:
        for g in v.groups: W[v.index, g.group] = g.weight
    return co, no, names, W

def gw(names, W, *bones):
    return sum(W[:, names.index(b)] for b in bones if b in names)

def link(ob, arm):
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = arm
    md = ob.modifiers.new("Armature", 'ARMATURE'); md.object = arm
    for p in ob.data.polygons: p.use_smooth = True
    return ob

def shell(body, co, no, mask, offset, name, offset_fn=None, smooth=1):
    S = set(np.where(mask)[0].tolist())
    bm = bmesh.new(); bm.from_mesh(body.data)
    nbm = bmesh.new(); vmap = {}; src = nbm.verts.layers.int.new("src")
    for f in bm.faces:
        if not all(v.index in S for v in f.verts): continue
        vs = []
        for v in f.verts:
            if v.index not in vmap:
                nv = nbm.verts.new(Vector(co[v.index])); nv[src] = v.index; vmap[v.index] = nv
            vs.append(vmap[v.index])
        try: nbm.faces.new(vs)
        except ValueError: pass
    bm.free()
    # malé ostrůvky pryč
    seen = set(); kill = []
    for f in nbm.faces:
        if f in seen: continue
        comp = []; st = [f]; seen.add(f)
        while st:
            g = st.pop(); comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen: seen.add(h); st.append(h)
        if len(comp) < 20: kill += comp
    if kill: bmesh.ops.delete(nbm, geom=kill, context='FACES')
    bmesh.ops.delete(nbm, geom=[v for v in nbm.verts if not v.link_faces], context='VERTS')
    nbm.normal_update()
    for _ in range(smooth):
        bmesh.ops.smooth_vert(nbm, verts=[v for v in nbm.verts if not v.is_boundary], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    nbm.normal_update()
    for v in nbm.verts:
        o = offset if offset_fn is None else offset_fn(np.array(v.co), offset)
        v.co += v.normal * o
    me = bpy.data.meshes.new(name); nbm.to_mesh(me); nbm.free()
    return bpy.data.objects.new(name, me)

def transfer_weights(ob, co, names, W, k=6, only=None, mask=None):
    idx = np.arange(len(co)) if mask is None else np.where(mask)[0]
    kd = kdtree.KDTree(len(idx))
    for j, i in enumerate(idx): kd.insert(co[i], j)
    kd.balance()
    acc = np.zeros((len(ob.data.vertices), len(names)))
    for v in ob.data.vertices:
        tw = 0
        for p, j, d in kd.find_n(v.co, k):
            w = 1 / (d + 0.004); acc[v.index] += w * W[idx[j]]; tw += w
        acc[v.index] /= max(tw, 1e-9)
    return acc

def set_weights(ob, names, acc, thr=0.01):
    acc = acc / np.maximum(acc.sum(1, keepdims=True), 1e-9)
    for bi, b in enumerate(names):
        col = acc[:, bi]; nz = np.where(col > thr)[0]
        if len(nz) == 0: continue
        g = ob.vertex_groups.get(b) or ob.vertex_groups.new(name=b)
        for i in nz: g.add([int(i)], float(col[i]), 'REPLACE')

def cut_iso(ob, fn, lip=0.0):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    val = {v: fn(np.array(v.co)) for v in bm.verts}
    for v in bm.verts:
        if abs(val[v]) < 1e-7: val[v] = 1e-7
    cross = [e for e in bm.edges if (val[e.verts[0]] > 0) != (val[e.verts[1]] > 0)]
    newv = []
    for e in cross:
        a, b = e.verts; t = val[a] / (val[a] - val[b])
        ne, nv = bmesh.utils.edge_split(e, a, t); val[nv] = 0.0; newv.append(nv)
    ns = set(newv)
    for f in list({f for v in newv for f in v.link_faces}):
        vs = [v for v in f.verts if v in ns]
        if len(vs) == 2:
            try: bmesh.ops.connect_verts(bm, verts=vs)
            except Exception: pass
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if val.get(v, 1.0) < -1e-9], context='VERTS')
    bm.normal_update()
    if lip > 0:
        bnd = [e for e in bm.edges if e.is_boundary and all(v in ns for v in e.verts)]
        if bnd:
            ret = bmesh.ops.extrude_edge_only(bm, edges=bnd)
            nvs = set(g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert))
            bm.normal_update()
            for v in nvs:
                srcv = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) not in nvs]
                n = srcv[0].normal if srcv else v.normal
                v.co -= n * lip
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    return ob

def triplanar_uv(ob, tile, axis_fn=None):
    """UV v metrech / tile: válcové mapování kolem svislé osy (trup, sukně) nebo osy paže (rukávy)."""
    me = ob.data
    if not me.uv_layers: me.uv_layers.new(name="UVMap")
    uv = me.uv_layers[0].data
    for p in me.polygons:
        cs = [me.vertices[me.loops[l].vertex_index].co for l in p.loop_indices]
        c = sum(cs, Vector()) / len(cs)
        for l in p.loop_indices:
            v = me.vertices[me.loops[l].vertex_index].co
            if axis_fn and axis_fn(c) == 'x':
                a = math.atan2(v.z - 1.418, v.y - 0.055); ac = math.atan2(c.z - 1.418, c.y - 0.055)
                if a - ac > math.pi: a -= 2 * math.pi
                if a - ac < -math.pi: a += 2 * math.pi
                uv[l].uv = (a * 0.05 / tile, v.x / tile)
            else:
                a = math.atan2(v.y - 0.04, v.x); ac = math.atan2(c.y - 0.04, c.x)
                if a - ac > math.pi: a -= 2 * math.pi
                if a - ac < -math.pi: a += 2 * math.pi
                r = 0.16
                uv[l].uv = (a * r / tile, v.z / tile)
