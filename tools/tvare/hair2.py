"""Lehké stylizované vlasy a vousy (bez průhlednosti, do ~1500 troj.):
čepice ze slupky hlavy s hladkým okrajem (izočára) + pár chomáčů pro obrys + doplňky (cop, drdol, dlouhé vlasy, vousy)."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import sys; sys.path.insert(0, "/home/claude/z30/scripts")
import cloth

def head_frame(L):
    zE = float(L["eye"][2]); yF = float(L["nose"][1]); yB = L["back_y"]
    return zE, (yF + yB) / 2

def azim(p, yc):
    """0 = vpředu, ±pi vzadu"""
    return math.atan2(p[0], -(p[1] - yc))

def interp_ang(a, table):
    a = abs(a); xs = [t[0] for t in table]; ys = [t[1] for t in table]
    return float(np.interp(a, xs, ys))

def hairline_fn(L, st):
    """kladné = vlasy. st: predni (výška čela nad okem), kouty (ústup), za_usima, tyl (výška týlu pod okem)"""
    zE, yc = head_frame(L)
    tab = [(0.0, zE + st.get("predni", 0.058)), (0.6, zE + st.get("predni", 0.058) - 0.006 + st.get("kouty", 0.0)),
           (1.0, zE + st.get("spanky", 0.040)), (1.45, zE + st.get("nad_usima", 0.028)),
           (1.9, zE + st.get("za_usima", -0.02)), (2.6, zE + st.get("tyl", -0.075)), (math.pi, zE + st.get("tyl", -0.075))]
    plesh = st.get("plesh", 0.0)       # pleš na temeni (poloměr v m)
    top = np.array(L["top"]); top[0] = 0
    def f(c):
        a = azim(c, yc)
        v = c[2] - interp_ang(a, tab) + 0.0025 * math.sin(a * 23) + 0.0015 * math.sin(a * 41 + 1)
        if plesh > 0:
            d = math.hypot(c[0], c[1] - (top[1] + 0.01)) if c[2] > zE + 0.06 else 1
            v = min(v, d - plesh)
        return v
    return f

def shell(body, L, fn, off, name, smooth=2, lip=0.003, off_fn=None):
    co = np.array([body.matrix_world @ v.co for v in body.data.vertices])
    no = None
    mask = np.array([fn(c) > -0.012 for c in co]) & (co[:, 2] > float(L["eye"][2]) - 0.25)
    ob = cloth.shell(body, co, no, mask, off, name, offset_fn=off_fn, smooth=smooth)
    cloth.cut_iso(ob, fn, lip=lip)
    return ob

def strand_uv(ob, L):
    zE, yc = head_frame(L)
    me = ob.data
    if not me.uv_layers: me.uv_layers.new(name="UVMap")
    uv = me.uv_layers[0].data
    for p in me.polygons:
        cs = [me.vertices[me.loops[l].vertex_index].co for l in p.loop_indices]
        ac = azim(sum(cs, Vector()) / len(cs), yc)
        for l in p.loop_indices:
            v = me.vertices[me.loops[l].vertex_index].co
            a = azim(v, yc)
            if a - ac > math.pi: a -= 2 * math.pi
            if a - ac < -math.pi: a += 2 * math.pi
            uv[l].uv = (a * 0.09 / 0.05, v.z / 0.12)

def ribbon(bm, pts, nrm, widths, thick, sides=4):
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = (nrm[i] - t * nrm[i].dot(t)).normalized(); b = t.cross(n).normalized()
        rings.append([bm.verts.new(p + b * math.cos(2 * math.pi * k / sides) * widths[i] * 0.5 + n * math.sin(2 * math.pi * k / sides) * thick[i] * 0.5) for k in range(sides)])
    for i in range(len(rings) - 1):
        for k in range(sides):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % sides], rings[i + 1][(k + 1) % sides], rings[i + 1][k]))
    try: bm.faces.new(rings[-1])
    except ValueError: pass
    return [v for r in rings for v in r]

def flow_clumps(body, L, fn, n, length, off, width, rng, side_bias=1.0, droop=0.0, flow_mode=None):
    """chomáče tečou po hlavě od temene dolů a dozadu (siluetu dělá čepice, tohle je reliéf)"""
    bm_b = bmesh.new(); bm_b.from_mesh(body.data); bm_b.transform(body.matrix_world)
    bvh = BVHTree.FromBMesh(bm_b); bm_b.free()
    zE, yc = head_frame(L); top = Vector(L["top"])
    bm = bmesh.new(); allv = []
    mode = flow_mode[0] if flow_mode else "temeno"
    yF = float(L["nose"][1]) + 0.07
    for i in range(n):
        if mode == "pesinka":                      # od pěšinky do stran a dozadu
            side = 1 if i % 2 == 0 else -1; t = (i // 2 + 0.5) / max(1, n // 2)
            start = Vector((side * 0.006, yF + (yc + 0.06 - yF) * t, top.z)); dirv = lambda sd=side, tt=t: Vector((sd * 1.0, 0.25 + 0.8 * tt, -1.0 - droop))
        elif mode == "dozadu":                     # sčesané z čela dozadu
            t = (i + 0.5) / n - 0.5; start = Vector((t * 0.11, yF, top.z - 0.012)); dirv = lambda tt=t: Vector((tt * 0.8, 1.0, -0.35 - droop))
        else:
            a = (i + 0.5) / n * 2 * math.pi + rng.uniform(-0.15, 0.15); r0 = 0.02 + rng.uniform(0, 0.02)
            start = Vector((math.sin(a) * r0, yc - math.cos(a) * r0 * 0.9, top.z)); dirv = lambda aa=a: Vector((math.sin(aa) * side_bias, -math.cos(aa), -1.2 - droop))
        loc, nn, _, _ = bvh.find_nearest(start)
        p = loc.copy(); pts = []; nrm = []
        for _ in range(6):                          # start kousek za vlasovou linií
            if fn(np.array(p)) > 0.014: break
            p = p + Vector((0, 0.008, 0.004)); p = bvh.find_nearest(p)[0]
        for k in range(9):
            loc, nn, _, _ = bvh.find_nearest(p)
            pts.append(loc + nn * off); nrm.append(nn)
            d = dirv(); d = (d - nn * d.dot(nn)).normalized()
            p = loc + d * (length / 8)
            if fn(np.array(p)) < 0.004: break
        if len(pts) < 3: continue
        k = len(pts)
        w = [width * (0.3 + 0.7 * min(1.0, j / 2)) * (1 - 0.6 * (j / (k - 1)) ** 2) for j in range(k)]
        th = [0.003] * k
        allv += ribbon(bm, pts, nrm, w, th)
    return bm

def to_object(bm, name):
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    return ob

def beard_fn(L, st):
    """oblast vousů (kladné = vousy): pod lícemi, kolem úst, brada, pod čelistí"""
    zE = float(L["eye"][2]); zN = float(L["nose"][2]); zC = float(L["chin"][2]); yN = float(L["nose"][1])
    zM = zN + (zC - zN) * 0.42
    kind = st["typ"]
    def f(c):
        x, y, z = c; ax = abs(x)
        if y > yN + 0.105: return -1
        v_back = (yN + 0.095) - y
        if kind == "knir":
            v = min(0.010 - abs(z - (zM + 0.010)) - max(0, ax - 0.022) * 0.6, (zM + 0.019) - z)
            return v if y < yN + 0.07 else -1
        top = zN - 0.012 - ax * 0.12 + 0.03 * max(0, ax - 0.05) / 0.02    # horní okraj na lících, k uším výš (kotlety)
        v = top - z
        if ax > 0.068: v = min(v, 0.08 - ax + 0.0)                        # konec před ušima
        v = min(v, z - (zC - st.get("pod", 0.022) - max(0, 0.03 - ax) * 0.4))   # pod bradou, ke krku jen kousek
        v = min(v, v_back)
        if z < zC + 0.01: v = min(v, (yN + 0.065) - y)
        # rty volné
        lip = max(0.008 - abs(z - zM), 0) if ax < 0.024 and y < yN + 0.06 else 0
        v = min(v, 0.006 - lip * 3) if lip > 0 else v
        if kind == "bradka": v = min(v, 0.03 - ax)
        return v
    return f
