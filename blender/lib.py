"""Stavebnice pro modelovani tvrze v Blenderu (bpy).

Vse se zadava v souradnicich hry (Godot): X vychod, Y nahoru, Z jih.
Pri zapisu do Blenderu se prevadi na (x, -z, y), pri exportu glTF (+Y nahoru)
se to vrati zpet, takze modely sedi presne na rozvrzeni ve hre.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

R = random.Random(7)


def jit(a: float) -> float:
    return R.uniform(-a, a)


def V(x, y=None, z=None) -> Vector:
    if y is None:
        return Vector(x)
    return Vector((x, y, z))


def to_bl(p: Vector) -> tuple:
    return (p.x, -p.z, p.y)


def frame(d: Vector, up: Vector = Vector((0, 1, 0))) -> Matrix:
    """3x3 baze: lokalni Z podel d, lokalni Y co nejblize 'up'."""
    z = d.normalized()
    if abs(z.dot(up)) > 0.999:
        up = Vector((1, 0, 0)) if abs(z.x) < 0.9 else Vector((0, 0, 1))
    x = up.cross(z).normalized()
    y = z.cross(x).normalized()
    return Matrix((x, y, z)).transposed()


def M(pos=(0, 0, 0), yaw=0.0, basis: Matrix = None) -> Matrix:
    """Transformace: posun + otoceni kolem Y (stupne) nebo dana baze 3x3."""
    if basis is None:
        basis = Matrix.Rotation(math.radians(yaw), 3, "Y")
    m = basis.to_4x4()
    m.translation = Vector(pos)
    return m


def rot(axis: str, deg: float) -> Matrix:
    return Matrix.Rotation(math.radians(deg), 4, axis)


# ======================================================================= geometrie

class Part:
    """Sberna geometrie jednoho objektu (vice materialu). Vrcholy v souradnicich hry."""

    def __init__(self, name: str, bevel: float = 0.0, smooth: bool = False):
        self.name = name
        self.bevel = bevel
        self.smooth = smooth
        self.v: list = []
        self.f: list = []      # (indexy, uv, material, rnd)
        self.mats: list = []
        self.cols: list = []   # kolizni kvadry pro hru: (Matrix, size)
        self.bev: set = set()  # hrany kvadru, ktere se zkosi (zdi se nezkosuji, jinak by v nich byly spary)

    # --- zaklad
    def _mat(self, name: str) -> int:
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def _add_v(self, pts) -> int:
        base = len(self.v)
        self.v.extend(Vector(p) for p in pts)
        return base

    def face(self, pts, mat: str, uvs=None, rnd: float = None):
        """Volna plocha (vrcholy se nesdili). UV planarne v metrech."""
        pts = [Vector(p) for p in pts]
        if uvs is None:
            uvs = planar_uv(pts)
        b = self._add_v(pts)
        self.f.append((list(range(b, b + len(pts))), uvs, self._mat(mat), R.random() if rnd is None else rnd, False))

    def mesh(self, verts, faces, mat: str, uvs=None, rnd: float = None, m: Matrix = None, smooth: bool = False):
        """Sdilene vrcholy; faces = seznam indexu (lokalne), uvs = seznam seznamu UV na rohy."""
        if m is not None:
            verts = [m @ Vector(p) for p in verts]
        b = self._add_v(verts)
        mi = self._mat(mat)
        r = R.random() if rnd is None else rnd
        for i, fc in enumerate(faces):
            uv = uvs[i] if uvs is not None else planar_uv([self.v[b + k] for k in fc])
            self.f.append(([b + k for k in fc], uv, mi, r, smooth))

    # --- kvadry
    def box(self, m: Matrix, size, mat: str, uvo=None, rnd=None, collide=False):
        """Kvadr se stredem v m, rozmery size (lokalne x, y, z). UV: U podel lokalni Z."""
        # drobne nahodne nafouknuti: zadne dve plochy nelezi presne v jedne rovine (jinak cerne stiny v Cycles)
        sx, sy, sz = (s * 0.5 + R.uniform(0.0004, 0.003) for s in size)
        c = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
             (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]
        if uvo is None:
            uvo = (R.uniform(0, 7), R.uniform(0, 7))
        ou, ov = uvo
        uvs = []
        for fc in faces:
            n = Vector((0, 0, 0))
            pts = [Vector(c[k]) for k in fc]
            n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
            ax = max(range(3), key=lambda i: abs(n[i]))
            uv = []
            for p in pts:
                if ax == 0:
                    uv.append((p.z + ou, p.y + ov))
                elif ax == 1:
                    uv.append((p.z + ou, p.x + ov))
                else:
                    uv.append((p.x + ou, p.y + ov))
            uvs.append(uv)
        base = len(self.v)
        self.mesh(c, faces, mat, uvs, rnd, m)
        if not mat.startswith("zdivo") and not mat.startswith("omitka"):
            for a, b in ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)):
                self.bev.add((base + a, base + b))
        if collide:
            self.cols.append((m.copy(), tuple(size)))

    def bb(self, a, b, mat: str, grain: str = "auto", collide=False, rnd=None):
        """Osove zarovnany kvadr mezi rohy a, b. Drevo: vlakna podel nejdelsi vodorovne osy."""
        a, b = Vector(a), Vector(b)
        lo = Vector((min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)))
        hi = Vector((max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)))
        s = hi - lo
        c = (lo + hi) * 0.5
        g = grain
        if g == "auto":
            g = "x" if s.x > s.z else "z"
        if g == "x":
            self.box(M(c, basis=Matrix.Rotation(math.pi / 2, 3, "Y")), (s.z, s.y, s.x), mat, rnd=rnd, collide=collide)
        elif g == "y":
            self.box(M(c, basis=Matrix.Rotation(-math.pi / 2, 3, "X")), (s.x, s.z, s.y), mat, rnd=rnd, collide=collide)
        else:
            self.box(M(c), (s.x, s.y, s.z), mat, rnd=rnd, collide=collide)

    def beam(self, a, b, w, h, mat: str = "dub", up=Vector((0, 1, 0)), j: float = 0.0, ext: float = 0.0, collide=False, rnd=None):
        """Tram z a do b, prurez w x h. j = nahodna nepravidelnost (zkrut, rozmery)."""
        a, b = Vector(a), Vector(b)
        d = b - a
        L = d.length
        if L < 1e-4:
            return
        bas = frame(d, Vector(up))
        if j > 0:
            bas = bas @ Matrix.Rotation(jit(j * 0.06), 3, "Z") @ Matrix.Rotation(jit(j * 0.012), 3, "X")
            w *= 1 + jit(j * 0.12)
            h *= 1 + jit(j * 0.12)
        self.box(M((a + b) * 0.5, basis=bas), (w, h, L + ext * 2), mat, rnd=rnd, collide=collide)

    # --- rotacni telesa
    def lathe(self, m: Matrix, prof, seg: int, mat: str, cap_top=True, cap_bot=True, rnd=None, phase=0.0):
        """Rotacni teleso kolem lokalni Y, profil = [(r, y), ...] zdola nahoru."""
        verts = []
        for (r, y) in prof:
            for i in range(seg):
                a = phase + 2 * math.pi * i / seg
                verts.append((r * math.cos(a), y, -r * math.sin(a)))
        faces, uvs = [], []
        acc = [0.0]
        for k in range(1, len(prof)):
            acc.append(acc[-1] + math.hypot(prof[k][0] - prof[k - 1][0], prof[k][1] - prof[k - 1][1]))
        rmax = max(p[0] for p in prof)
        for k in range(len(prof) - 1):
            for i in range(seg):
                i2 = (i + 1) % seg
                faces.append((k * seg + i, k * seg + i2, (k + 1) * seg + i2, (k + 1) * seg + i))
                u0 = 2 * math.pi * rmax * i / seg
                u1 = 2 * math.pi * rmax * (i + 1) / seg
                uvs.append([(acc[k], u0), (acc[k], u1), (acc[k + 1], u1), (acc[k + 1], u0)])
        n = len(prof)
        if cap_bot and prof[0][0] > 1e-4:
            faces.append(tuple(reversed(range(seg))))
            uvs.append([(verts[i][0], verts[i][2]) for i in reversed(range(seg))])
        if cap_top and prof[-1][0] > 1e-4:
            faces.append(tuple((n - 1) * seg + i for i in range(seg)))
            uvs.append([(verts[(n - 1) * seg + i][0], verts[(n - 1) * seg + i][2]) for i in range(seg)])
        self.mesh(verts, faces, mat, uvs, rnd, m, smooth=seg >= 8)

    def cyl(self, m: Matrix, r0, r1, h, seg, mat, rnd=None):
        self.lathe(m, [(r0, 0.0), (r1, h)], seg, mat, rnd=rnd)

    def rod(self, a, b, r, seg, mat, r1=None, rnd=None):
        a, b = Vector(a), Vector(b)
        d = b - a
        bas = frame(d, Vector((0, 1, 0))) @ Matrix.Rotation(-math.pi / 2, 3, "X")
        self.lathe(M(a, basis=bas), [(r, 0.0), (r if r1 is None else r1, d.length)], seg, mat, rnd=rnd)

    def ball(self, c, rad, mat, seg=10, rings=6, rnd=None, m: Matrix = None):
        rx, ry, rz = rad
        prof = []
        for k in range(rings + 1):
            t = math.pi * k / rings - math.pi / 2
            prof.append((max(math.cos(t), 0.0), math.sin(t)))
        verts, faces = [], []
        for k, (r, y) in enumerate(prof):
            for i in range(seg):
                a = 2 * math.pi * i / seg
                verts.append((c[0] + rx * r * math.cos(a), c[1] + ry * y, c[2] - rz * r * math.sin(a)))
        for k in range(rings):
            for i in range(seg):
                i2 = (i + 1) % seg
                faces.append((k * seg + i, k * seg + i2, (k + 1) * seg + i2, (k + 1) * seg + i))
        self.mesh(verts, faces, mat, None, rnd, m, smooth=True)

    # --- desky a hranoly
    def prism(self, pts, d: Vector, mat: str, rnd=None):
        """Mnohouhelnik pts (ve smeru CCW pri pohledu proti d) vytazeny o vektor d."""
        pts = [Vector(p) for p in pts]
        n = len(pts)
        verts = pts + [p + d for p in pts]
        faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        for i in range(n):
            i2 = (i + 1) % n
            faces.append((i, i2, n + i2, n + i))
        self.mesh(verts, faces, mat, None, rnd)

    def slab(self, a, b, c, d, t: float, mat: str, rnd=None):
        """Ctyruhelnik a-b-c-d s tloustkou t (do strany opacne nez normala)."""
        a, b, c, d = (Vector(p) for p in (a, b, c, d))
        n = (b - a).cross(d - a).normalized()
        self.prism([a - n * t, b - n * t, c - n * t, d - n * t], n * t, mat, rnd)

    def tri(self, a, b, c, t: float, mat: str, rnd=None):
        a, b, c = (Vector(p) for p in (a, b, c))
        n = (b - a).cross(c - a).normalized()
        self.prism([a - n * t, b - n * t, c - n * t], n * t, mat, rnd)

    # --- zapis do Blenderu
    def commit(self, coll) -> bpy.types.Object:
        if not self.f:
            return None
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([to_bl(p) for p in self.v], [], [fc[0] for fc in self.f])
        uvl = me.uv_layers.new(name="UVMap")
        li = 0
        for poly, fc in zip(me.polygons, self.f):
            for k, uv in enumerate(fc[1]):
                uvl.data[poly.loop_start + k].uv = uv
            poly.material_index = fc[2]
        at = me.attributes.new("rnd", "FLOAT", "FACE")
        at.data.foreach_set("value", [fc[3] for fc in self.f])
        for name in self.mats:
            me.materials.append(MAT.get(name))
        sm = [self.smooth or (len(fc) > 4 and fc[4]) for fc in self.f]
        me.polygons.foreach_set("use_smooth", sm)
        me.validate()
        if self.bevel > 0:
            ew = me.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
            vals = [0.0] * len(me.edges)
            for i, e in enumerate(me.edges):
                k = (min(e.vertices[0], e.vertices[1]), max(e.vertices[0], e.vertices[1]))
                if k in self.bev:
                    vals[i] = 1.0
            ew.data.foreach_set("value", vals)
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        if self.bevel > 0:
            bm = ob.modifiers.new("bevel", "BEVEL")
            bm.width = self.bevel
            bm.segments = 1
            bm.limit_method = "WEIGHT"
            bm.use_clamp_overlap = True
        ob["cols"] = [list(m.translation) + list(m.to_quaternion()) + list(s) for m, s in self.cols]
        return ob


def planar_uv(pts):
    a, b, c = pts[0], pts[1], pts[2]
    n = (b - a).cross(c - a)
    if n.length < 1e-9:
        return [(0, 0)] * len(pts)
    n.normalize()
    if abs(n.y) > 0.7:
        return [(p.x, p.z) for p in pts]
    t = Vector((0, 1, 0)).cross(n).normalized()
    return [(p.dot(t), p.y) for p in pts]


# ---- zdi s otvory (stejna logika jako fort.gd)

def wall_x(P: Part, mat, x0, x1, z0, z1, y0, y1, holes=(), collide=True):
    hs = sorted(holes, key=lambda h: h[0])
    cur = x0
    for h in hs:
        if h[0] > cur + 1e-3:
            P.bb((cur, y0, z0), (h[0], y1, z1), mat, collide=collide)
        if h[2] > y0 + 1e-3:
            P.bb((h[0], y0, z0), (h[1], h[2], z1), mat, collide=collide)
        if h[3] < y1 - 1e-3:
            P.bb((h[0], h[3], z0), (h[1], y1, z1), mat, collide=collide)
        cur = h[1]
    if cur < x1 - 1e-3:
        P.bb((cur, y0, z0), (x1, y1, z1), mat, collide=collide)


def wall_z(P: Part, mat, z0, z1, x0, x1, y0, y1, holes=(), collide=True):
    hs = sorted(holes, key=lambda h: h[0])
    cur = z0
    for h in hs:
        if h[0] > cur + 1e-3:
            P.bb((x0, y0, cur), (x1, y1, h[0]), mat, collide=collide)
        if h[2] > y0 + 1e-3:
            P.bb((x0, y0, h[0]), (x1, h[2], h[1]), mat, collide=collide)
        if h[3] < y1 - 1e-3:
            P.bb((x0, h[3], h[0]), (x1, y1, h[1]), mat, collide=collide)
        cur = h[1]
    if cur < z1 - 1e-3:
        P.bb((x0, y0, cur), (x1, y1, z1), mat, collide=collide)


# ======================================================================= materialy

MAT: dict = {}
LIGHTS: list = []      # (pozice ve hre, vykon W, barva, polomer) - ohne, svice, louce


def light(pos, energy, color=(1.0, 0.5, 0.2), radius=0.06):
    LIGHTS.append((Vector(pos), energy, color, radius))


class NB:
    """Maly pomocnik na stavbu shaderu."""

    def __init__(self, tree):
        self.t = tree
        self.x = 0

    def n(self, kind, inp=None, **attrs):
        node = self.t.nodes.new(kind)
        node.location = (self.x, 0)
        self.x += 30
        for k, v in attrs.items():
            setattr(node, k, v)
        for k, v in (inp or {}).items():
            s = self._in(node, k)
            if isinstance(v, bpy.types.NodeSocket):
                self.t.links.new(v, s)
            else:
                if s.type == "RGBA" and isinstance(v, (tuple, list)) and len(v) == 3:
                    v = (*v, 1.0)
                s.default_value = v
        return node

    @staticmethod
    def _in(node, k):
        if isinstance(k, int):
            return node.inputs[k]
        cands = [s for s in node.inputs if s.name == k and s.enabled]
        return cands[0] if cands else node.inputs[k]

    @staticmethod
    def out(node, k=0):
        if isinstance(k, int):
            outs = [s for s in node.outputs if s.enabled]
            return outs[k]
        cands = [s for s in node.outputs if s.name == k and s.enabled]
        return cands[0] if cands else node.outputs[k]

    def link(self, a, b):
        self.t.links.new(a, b)

    # zkratky
    def math(self, op, a, b=0.0, c=0.0, clamp=False):
        return self.out(self.n("ShaderNodeMath", {0: a, 1: b, 2: c}, operation=op, use_clamp=clamp))

    def vmath(self, op, a, b=(0, 0, 0), out="Vector"):
        node = self.n("ShaderNodeVectorMath", {0: a, 1: b}, operation=op)
        return self.out(node, out)

    def mr(self, v, a, b, c=0.0, d=1.0, smooth=True):
        node = self.n("ShaderNodeMapRange", {"Value": v, "From Min": a, "From Max": b, "To Min": c, "To Max": d},
                      interpolation_type="SMOOTHSTEP" if smooth else "LINEAR")
        return self.out(node, "Result")

    def mix(self, f, a, b, blend="MIX"):
        node = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.link(f, node.inputs[0]) if isinstance(f, bpy.types.NodeSocket) else setattr(node.inputs[0], "default_value", f)
        sa = [s for s in node.inputs if s.name == "A" and s.type == "RGBA"][0]
        sb = [s for s in node.inputs if s.name == "B" and s.type == "RGBA"][0]
        for s, v in ((sa, a), (sb, b)):
            if isinstance(v, bpy.types.NodeSocket):
                self.link(v, s)
            else:
                s.default_value = v if len(v) == 4 else (*v, 1.0)
        return [o for o in node.outputs if o.name == "Result" and o.type == "RGBA"][0]

    def fmix(self, f, a, b):
        return self.math("ADD", self.math("MULTIPLY", a, self.math("SUBTRACT", 1.0, f)), self.math("MULTIPLY", b, f))

    def noise(self, vec, scale, detail=4.0, rough=0.55, dist=0.0, out="Fac", dim="3D"):
        node = self.n("ShaderNodeTexNoise", {"Vector": vec, "Scale": scale, "Detail": detail, "Roughness": rough, "Distortion": dist},
                      noise_dimensions=dim)
        return self.out(node, out)

    def voro(self, vec, scale, feature="F1", out="Distance", rnd=1.0, metric="EUCLIDEAN", dim="3D"):
        node = self.n("ShaderNodeTexVoronoi", {"Vector": vec, "Scale": scale, "Randomness": rnd},
                      feature=feature, distance=metric, voronoi_dimensions=dim)
        return self.out(node, out)

    def ramp(self, f, stops):
        node = self.n("ShaderNodeValToRGB", {"Fac": f})
        el = node.color_ramp.elements
        el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1)
        el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
        for p, c in stops[1:-1]:
            e = el.new(p)
            e.color = (*c, 1)
        return self.out(node, "Color")

    def rgb(self, c):
        node = self.n("ShaderNodeRGB")
        node.outputs[0].default_value = (*c, 1)
        return node.outputs[0]

    def attr(self, name="rnd"):
        return self.out(self.n("ShaderNodeAttribute", attribute_name=name, attribute_type="GEOMETRY"), "Fac")

    def uv(self):
        return self.out(self.n("ShaderNodeTexCoord"), "UV")

    def geo(self, k="Position"):
        return self.out(self.n("ShaderNodeNewGeometry"), k)

    def sep(self, v):
        node = self.n("ShaderNodeSeparateXYZ", {0: v})
        return node.outputs[0], node.outputs[1], node.outputs[2]

    def comb(self, x, y, z=0.0):
        return self.out(self.n("ShaderNodeCombineXYZ", {0: x, 1: y, 2: z}))

    def bump(self, h, strength=1.0, dist=0.02, normal=None):
        inp = {"Height": h, "Strength": strength, "Distance": dist}
        if normal is not None:
            inp["Normal"] = normal
        return self.out(self.n("ShaderNodeBump", inp), "Normal")

    def bsdf(self, col, rough, nrm=None, metal=0.0, spec=0.5, out_node=None, sss=0.0):
        inp = {"Base Color": col, "Roughness": rough, "Metallic": metal, "Specular IOR Level": spec}
        if nrm is not None:
            inp["Normal"] = nrm
        node = self.n("ShaderNodeBsdfPrincipled", inp)
        if sss > 0:
            node.inputs["Subsurface Weight"].default_value = sss
        return self.out(node, "BSDF")


def new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    MAT[name] = m
    return m, NB(nt), outn


def finish(nb: NB, outn, shader):
    nb.link(shader, outn.inputs["Surface"])


def wcoord(nb: NB, su=1.0, sv=1.0):
    """Svetove promitani v metrech: na svislych plochach (vodorovne podel zdi, vyska),
    na vodorovnych (x, y). Treti slozka = hloubka roviny, aby rovnobezne zdi nemely stejny vzor."""
    P = nb.geo("Position")
    N = nb.geo("Normal")
    T = nb.vmath("NORMALIZE", nb.vmath("CROSS_PRODUCT", (0, 0, 1), N))
    u = nb.vmath("DOT_PRODUCT", P, T, "Value")
    d = nb.vmath("DOT_PRODUCT", P, N, "Value")
    px, py, pz = nb.sep(P)
    nx, ny, nz = nb.sep(N)
    top = nb.math("GREATER_THAN", nb.math("ABSOLUTE", nz), 0.7)
    side = nb.comb(nb.math("MULTIPLY", u, 1.0 / su), nb.math("MULTIPLY", pz, 1.0 / sv), nb.math("MULTIPLY", d, 0.37))
    flat = nb.comb(nb.math("MULTIPLY", px, 1.0 / su), nb.math("MULTIPLY", py, 1.0 / su), nb.math("MULTIPLY", pz, 0.37))
    node = nb.n("ShaderNodeMix", data_type="VECTOR")
    nb.link(top, node.inputs[0])
    sa = [s for s in node.inputs if s.name == "A" and s.type == "VECTOR"][0]
    sb = [s for s in node.inputs if s.name == "B" and s.type == "VECTOR"][0]
    nb.link(side, sa)
    nb.link(flat, sb)
    res = [o for o in node.outputs if o.name == "Result" and o.type == "VECTOR"][0]
    return res, pz, top


def mat_masonry(name, plaster_cover=0.5, stone_tint=(1, 1, 1), plaster_col=(0.5, 0.43, 0.31), scale=1.0, grime=1.0):
    """Lomove zdivo z plochych kamenu ve vrstvach (lozne spary), s vapennou omitkou, ktera misty opadava."""
    m, nb, outn = new_mat(name)
    wc, z, top = wcoord(nb, scale, scale)
    warp = nb.noise(wc, 1.1, 3.0, 0.55, out="Color")
    co = nb.vmath("ADD", wc, nb.vmath("MULTIPLY", nb.vmath("SUBTRACT", warp, (0.5, 0.5, 0.5)), (0.25, 0.1, 0.0)))
    # dve velikosti kamenu (ploche, protahle ve vrstvach), stridaji se po oblastech
    ca = nb.vmath("MULTIPLY", co, (1 / 0.55, 1 / 0.19, 1.0))
    e1 = nb.voro(ca, 1.0, "DISTANCE_TO_EDGE", "Distance", 1.0)
    r1 = nb.sep(nb.voro(ca, 1.0, "F1", "Color", 1.0))[0]
    cb2 = nb.vmath("MULTIPLY", nb.vmath("ADD", co, (0.37, 0.11, 0.0)), (1 / 0.3, 1 / 0.12, 1.3))
    e2 = nb.voro(cb2, 1.0, "DISTANCE_TO_EDGE", "Distance", 1.0)
    r2 = nb.sep(nb.voro(cb2, 1.0, "F1", "Color", 1.0))[0]
    reg = nb.mr(nb.noise(co, 0.45, 2.0, 0.5), 0.5, 0.53)
    edge = nb.fmix(reg, e1, e2)
    edge = nb.math("ADD", edge, nb.math("MULTIPLY", nb.math("SUBTRACT", nb.noise(co, 9.0, 4.0, 0.6), 0.5), 0.06))
    mort = nb.mr(edge, 0.0, 0.16, 1.0, 0.0, False)
    rnd = nb.fmix(reg, r1, r2)
    rn = nb.noise(co, 9.0, 7.0, 0.65)
    chips = nb.noise(co, 30.0, 4.0, 0.6)
    # vypouklost kamene: polstar z mortaroveho prechodu + nerovny povrch
    sh = nb.mr(edge, 0.012, 0.11)
    und = nb.noise(co, 2.5, 3.0, 0.5)
    sh = nb.math("MULTIPLY", sh, nb.math("ADD", 0.55, nb.math("ADD", nb.math("MULTIPLY", rn, 0.3), nb.math("MULTIPLY", und, 0.4))))
    scol = nb.ramp(rnd, [(0.0, (0.1, 0.085, 0.065)), (0.2, (0.18, 0.15, 0.11)), (0.45, (0.25, 0.21, 0.15)),
                         (0.65, (0.14, 0.12, 0.1)), (0.82, (0.3, 0.24, 0.16)), (1.0, (0.2, 0.15, 0.1))])
    scol = nb.mix(1.0, scol, (*stone_tint,), "MULTIPLY")
    spots = nb.mr(nb.noise(co, 12.0, 5.0, 0.7), 0.58, 0.72, 0.0, 0.75)
    scol = nb.mix(spots, scol, (0.34, 0.33, 0.29))                                   # svetle lisejniky
    scol = nb.mix(nb.mr(rn, 0.3, 0.75), nb.mix(1.0, scol, (0.55, 0.55, 0.55), "MULTIPLY"), scol)
    scol = nb.mix(nb.mr(chips, 0.6, 0.75, 0.0, 0.4), scol, (0.3, 0.29, 0.26))
    smear = nb.mr(nb.noise(co, 2.5, 4.0, 0.6), 0.45, 0.65)
    mortar = nb.mix(smear, (0.07, 0.065, 0.055), (0.3, 0.27, 0.22))
    stone = nb.mix(nb.mr(edge, 0.034, 0.014), scol, mortar)
    # omitka
    big = nb.noise(nb.vmath("MULTIPLY", co, (0.32, 0.5, 0.3)), 0.8, 4.0, 0.6)
    lowz = nb.mr(z, 0.0, 2.2, 1.0, 0.0)
    cover = nb.math("SUBTRACT", nb.math("ADD", big, (plaster_cover - 0.5) * 0.22), nb.math("MULTIPLY", lowz, 0.07))
    pm = nb.mr(cover, 0.475, 0.49)
    fine = nb.noise(co, 18.0, 6.0, 0.62)
    rough = nb.noise(co, 60.0, 3.0, 0.5)
    px, py, pz = nb.sep(nb.geo("Position"))
    streak = nb.noise(nb.comb(nb.math("MULTIPLY", nb.math("ADD", px, py), 3.5), nb.math("MULTIPLY", z, 0.12), 0.0), 2.0, 6.0, 0.65)
    tone = nb.noise(co, 0.25, 3.0, 0.5)
    pcol = nb.mix(nb.mr(tone, 0.3, 0.7), (plaster_col[0] * 0.7, plaster_col[1] * 0.66, plaster_col[2] * 0.56),
                  (plaster_col[0] * 1.08, plaster_col[1] * 1.08, plaster_col[2] * 1.06))
    blot = nb.noise(nb.vmath("MULTIPLY", co, (1.0, 0.6, 1.0)), 1.6, 5.0, 0.65)
    pcol = nb.mix(nb.mr(blot, 0.55, 0.75, 0.0, 0.45), pcol, (plaster_col[0] * 0.55, plaster_col[1] * 0.52, plaster_col[2] * 0.42))
    pcol = nb.mix(nb.mr(fine, 0.35, 0.7, 0.0, 0.45), nb.mix(1.0, pcol, (0.78, 0.76, 0.72), "MULTIPLY"), pcol)
    pcol = nb.mix(nb.math("MULTIPLY", nb.mr(streak, 0.48, 0.72), 0.6 * grime), pcol, (0.2, 0.18, 0.14))
    # vlhko a spina u paty: tmava zona s neostrym okrajem
    damp = nb.math("MULTIPLY", nb.mr(nb.math("ADD", z, nb.math("MULTIPLY", big, 1.2)), 0.3, 1.9, 1.0, 0.0), 0.75 * grime)
    pcol = nb.mix(damp, pcol, (0.13, 0.12, 0.09))
    rim = nb.math("MULTIPLY", nb.mr(cover, 0.488, 0.5), nb.mr(cover, 0.53, 0.5))
    col = nb.mix(pm, stone, pcol)
    col = nb.mix(nb.math("MULTIPLY", rim, 0.7), col, (0.17, 0.15, 0.12))
    dirt = nb.math("MULTIPLY", nb.mr(z, -0.3, 1.0, 1.0, 0.0), nb.mr(big, 0.2, 0.8, 0.5, 1.0))
    col = nb.mix(nb.math("MULTIPLY", dirt, 0.55 * grime), col, (0.06, 0.05, 0.035))
    moss = nb.math("MAXIMUM", nb.math("MULTIPLY", top, nb.mr(nb.noise(co, 3.0, 5.0, 0.6), 0.45, 0.65, 0.0, 0.85)),
                   nb.math("MULTIPLY", nb.math("MULTIPLY", nb.mr(z, -0.5, 0.7, 1.0, 0.0), nb.mr(nb.noise(co, 4.0, 5.0, 0.6), 0.5, 0.62)), 0.8))
    col = nb.mix(moss, col, (0.05, 0.07, 0.02))
    h_stone = nb.math("ADD", nb.math("MULTIPLY", sh, 0.85), nb.math("MULTIPLY", chips, 0.08))
    h_pl = nb.math("ADD", 1.0, nb.math("ADD", nb.math("MULTIPLY", fine, 0.12), nb.math("ADD", nb.math("MULTIPLY", rough, 0.14), nb.math("MULTIPLY", big, 0.3))))
    h = nb.fmix(pm, h_stone, h_pl)
    nrm = nb.bump(h, 1.0, 0.045)
    rgh = nb.mr(pm, 0.0, 1.0, 0.82, 0.95, False)
    finish(nb, outn, nb.bsdf(col, rgh, nrm, spec=0.3))
    return m


def mat_ashlar(name, tint=(0.25, 0.21, 0.155)):
    """Pískovcove kvadry (narozi, ostění, schody). UV v metrech, nahodny posun na kvadr."""
    m, nb, outn = new_mat(name)
    uv = nb.uv()
    r = nb.attr()
    co = nb.vmath("ADD", nb.comb(nb.sep(uv)[0], nb.sep(uv)[1], nb.math("MULTIPLY", r, 13.0)), (0, 0, 0))
    n1 = nb.noise(co, 2.2, 6.0, 0.62)
    n2 = nb.noise(co, 30.0, 4.0, 0.6)
    tool = nb.noise(nb.vmath("MULTIPLY", co, (40.0, 3.0, 1.0)), 1.0, 2.0, 0.5)   # stopy dlata
    base = nb.mix(nb.math("MULTIPLY", r, 0.8), (*tint,), (tint[0] * 0.82, tint[1] * 0.84, tint[2] * 0.9))
    col = nb.mix(nb.mr(n1, 0.35, 0.7), nb.mix(1.0, base, (0.62, 0.62, 0.62), "MULTIPLY"), base)
    col = nb.mix(nb.mr(n2, 0.55, 0.8, 0.0, 0.25), col, (0.22, 0.2, 0.17))
    z = nb.sep(nb.geo("Position"))[2]
    col = nb.mix(nb.mr(z, -0.3, 1.0, 0.5, 0.0), col, (0.2, 0.17, 0.13))
    lich = nb.mr(nb.noise(nb.geo("Position"), 6.0, 5.0, 0.7), 0.66, 0.76, 0.0, 0.5)
    col = nb.mix(lich, col, (0.16, 0.17, 0.12))
    blot = nb.mr(nb.noise(nb.geo("Position"), 1.2, 4.0, 0.6), 0.5, 0.75, 0.0, 0.5)
    col = nb.mix(blot, col, (0.08, 0.075, 0.065))
    h = nb.math("ADD", nb.math("MULTIPLY", n2, 0.4), nb.math("MULTIPLY", tool, 0.25))
    finish(nb, outn, nb.bsdf(col, 0.88, nb.bump(h, 0.6, 0.01), spec=0.35))
    return m


def mat_plaster(name, col=(0.82, 0.79, 0.72), dirt=0.6):
    """Vnitrni vapenna omitka, nerovna, s ocouzanim dole a zacoudim nahore."""
    m, nb, outn = new_mat(name)
    wc, z, top = wcoord(nb, 1.0, 1.0)
    n1 = nb.noise(wc, 0.8, 5.0, 0.6)
    n2 = nb.noise(wc, 14.0, 6.0, 0.55)
    c = nb.mix(nb.mr(n1, 0.3, 0.7), (col[0] * 0.9, col[1] * 0.89, col[2] * 0.86), col)
    c = nb.mix(nb.math("MULTIPLY", nb.mr(n2, 0.55, 0.8), 0.25), c, (0.55, 0.52, 0.47))
    zl = nb.math("SUBTRACT", z, nb.math("MULTIPLY", nb.math("FLOOR", nb.math("DIVIDE", nb.math("ADD", z, 0.25), 3.9)), 3.9))
    low = nb.mr(zl, 0.0, 0.9, 1.0, 0.0)
    c = nb.mix(nb.math("MULTIPLY", low, 0.35 * dirt), c, (0.36, 0.32, 0.26))
    h = nb.math("ADD", nb.math("MULTIPLY", n1, 0.6), nb.math("MULTIPLY", n2, 0.15))
    finish(nb, outn, nb.bsdf(c, 0.92, nb.bump(h, 0.5, 0.03), spec=0.3))
    return m


def mat_wood(name, light=(0.33, 0.24, 0.16), dark=(0.13, 0.085, 0.055), grey=0.0, worn=0.0, planks=False):
    """Dubove drevo. UV: U podel vlaken. grey = zesedle vyvetrane, worn = osoupane (podlahy)."""
    m, nb, outn = new_mat(name)
    uv = nb.uv()
    r = nb.attr()
    u, v, _ = nb.sep(uv)
    co = nb.comb(nb.math("MULTIPLY", u, 0.35), nb.math("MULTIPLY", v, 9.0), nb.math("MULTIPLY", r, 17.0))
    g1 = nb.noise(co, 2.5, 8.0, 0.65, dist=0.4)
    g2 = nb.noise(nb.comb(nb.math("MULTIPLY", u, 0.6), nb.math("MULTIPLY", v, 30.0), nb.math("MULTIPLY", r, 11.0)), 3.0, 4.0, 0.5)
    rings = nb.out(nb.n("ShaderNodeTexWave", {"Vector": co, "Scale": 0.9, "Distortion": 6.0, "Detail": 3.0},
                         wave_type="BANDS", bands_direction="Y"), "Fac")
    t = nb.math("ADD", nb.math("MULTIPLY", g1, 0.6), nb.math("MULTIPLY", rings, 0.25))
    t = nb.math("ADD", t, nb.math("MULTIPLY", nb.math("SUBTRACT", r, 0.5), 0.35))
    col = nb.mix(nb.mr(t, 0.25, 0.85), dark, light)
    # praskliny podel vlaken
    crk = nb.voro(nb.comb(nb.math("MULTIPLY", u, 0.25), nb.math("MULTIPLY", v, 6.0), nb.math("MULTIPLY", r, 5.0)), 2.0, "DISTANCE_TO_EDGE")
    crack = nb.mr(crk, 0.0, 0.03, 1.0, 0.0)
    crack = nb.math("MULTIPLY", crack, nb.mr(nb.noise(co, 1.5), 0.45, 0.6))
    if grey > 0:
        gcol = nb.mix(nb.mr(g2, 0.3, 0.7), (0.06, 0.05, 0.04), (0.14, 0.12, 0.095))
        col = nb.mix(nb.math("MULTIPLY", nb.mr(g1, 0.2, 0.6, 0.5, 1.0), grey), col, gcol)
    if worn > 0:
        col = nb.mix(nb.math("MULTIPLY", nb.mr(nb.noise(co, 0.6), 0.45, 0.65), worn), col, (light[0] * 1.25, light[1] * 1.2, light[2] * 1.15))
    col = nb.mix(nb.math("MULTIPLY", crack, 0.85), col, (0.03, 0.02, 0.015))
    h = nb.math("SUBTRACT", nb.math("ADD", nb.math("MULTIPLY", g2, 0.35), nb.math("MULTIPLY", g1, 0.2)), nb.math("MULTIPLY", crack, 0.8))
    if planks:
        # spary mezi prkny
        pv = nb.math("FRACT", nb.math("DIVIDE", v, 0.24))
        gap = nb.math("MULTIPLY", nb.mr(pv, 0.0, 0.03, 1.0, 0.0), 1.0)
        gap = nb.math("MAXIMUM", gap, nb.mr(pv, 0.97, 1.0, 0.0, 1.0))
        col = nb.mix(nb.math("MULTIPLY", gap, 0.8), col, (0.03, 0.02, 0.01))
        h = nb.math("SUBTRACT", h, gap)
    rough = nb.mr(g2, 0.0, 1.0, 0.7, 0.9, False)
    finish(nb, outn, nb.bsdf(col, rough, nb.bump(h, 0.6, 0.008), spec=0.4))
    return m


def mat_shingle(name):
    """Stipany dreveny sindel: zesedly, tmavsi u spar, mech."""
    m, nb, outn = new_mat(name)
    uv = nb.uv()
    r = nb.attr()
    u, v, _ = nb.sep(uv)
    co = nb.comb(nb.math("MULTIPLY", u, 0.6), nb.math("MULTIPLY", v, 14.0), nb.math("MULTIPLY", r, 23.0))
    g = nb.noise(co, 3.0, 8.0, 0.65, dist=0.3)
    g2 = nb.noise(co, 12.0, 4.0, 0.6)
    base = nb.ramp(r, [(0.0, (0.07, 0.06, 0.05)), (0.4, (0.12, 0.1, 0.08)), (0.75, (0.16, 0.13, 0.1)), (1.0, (0.11, 0.08, 0.055))])
    col = nb.mix(nb.mr(g, 0.3, 0.75, 0.0, 0.6), nb.mix(1.0, base, (0.6, 0.6, 0.6), "MULTIPLY"), base)
    wc = nb.geo("Position")
    moss_n = nb.noise(wc, 0.9, 5.0, 0.65)
    moss = nb.math("MULTIPLY", nb.mr(moss_n, 0.55, 0.72), nb.mr(g2, 0.3, 0.6))
    col = nb.mix(nb.math("MULTIPLY", moss, 0.85), col, (0.17, 0.2, 0.07))
    h = nb.math("ADD", nb.math("MULTIPLY", g, 0.5), nb.math("MULTIPLY", g2, 0.2))
    finish(nb, outn, nb.bsdf(col, 0.85, nb.bump(h, 0.7, 0.006), spec=0.35))
    return m


def mat_flag(name, scale=0.55, tint=(0.25, 0.22, 0.18), joint=(0.09, 0.07, 0.045)):
    """Kamenna dlazba z nepravidelnych desek se zaoblenymi hranami, hlina a stérk ve sparach."""
    m, nb, outn = new_mat(name)
    wc, z, top = wcoord(nb, scale, scale)
    w = nb.noise(wc, 1.3, 2.0, 0.5, out="Color")
    co = nb.vmath("MULTIPLY", nb.vmath("ADD", wc, nb.vmath("MULTIPLY", nb.vmath("SUBTRACT", w, (0.5, 0.5, 0.5)), (0.3, 0.3, 0.0))), (1, 1, 0))
    e = nb.voro(co, 1.0, "DISTANCE_TO_EDGE", "Distance", 0.85, dim="2D")
    c = nb.voro(co, 1.0, "F1", "Color", 0.85, dim="2D")
    cr, cg, cb = nb.sep(c)
    n1 = nb.noise(co, 6.0, 7.0, 0.65)
    n2 = nb.noise(co, 40.0, 4.0, 0.6)
    edge_n = nb.noise(co, 14.0, 3.0, 0.6)
    ee = nb.math("ADD", e, nb.math("MULTIPLY", nb.math("SUBTRACT", edge_n, 0.5), 0.05))
    prof = nb.math("POWER", nb.mr(ee, 0.03, 0.16, 0.0, 1.0, False), 0.55)
    sc = nb.ramp(cr, [(0.0, (tint[0] * 0.6, tint[1] * 0.6, tint[2] * 0.6)), (0.4, tint), (0.7, (tint[0] * 0.8, tint[1] * 0.82, tint[2] * 0.85)),
                      (1.0, (tint[0] * 1.15, tint[1] * 1.1, tint[2] * 1.0))])
    sc = nb.mix(nb.mr(n1, 0.3, 0.75, 0.0, 0.6), nb.mix(1.0, sc, (0.6, 0.6, 0.6), "MULTIPLY"), sc)
    sc = nb.mix(nb.mr(n2, 0.62, 0.78, 0.0, 0.5), sc, (0.4, 0.38, 0.34))                 # svetla zrna
    sc = nb.mix(nb.math("MULTIPLY", nb.mr(nb.noise(co, 3.0, 5.0, 0.7), 0.6, 0.75, 0.0, 0.6), cg), sc, (0.07, 0.07, 0.05))
    # sparova hlina se sterkem a mechem
    grav = nb.mr(nb.noise(co, 70.0, 2.0, 0.5), 0.55, 0.65)
    jc = nb.mix(grav, joint, (0.26, 0.24, 0.2))
    jc = nb.mix(nb.mr(nb.noise(co, 5.0, 4.0, 0.6), 0.55, 0.7, 0.0, 0.8), jc, (0.06, 0.08, 0.02))
    jm = nb.mr(ee, 0.022, 0.045)
    col = nb.mix(jm, jc, sc)
    # vysleděné (osoupane) stredy desek jsou hladsi a svetlejsi
    worn = nb.mr(e, 0.15, 0.4, 0.0, 0.25)
    col = nb.mix(worn, col, (tint[0] * 1.3, tint[1] * 1.3, tint[2] * 1.25))
    h = nb.math("ADD", nb.math("MULTIPLY", prof, 1.0), nb.math("ADD", nb.math("MULTIPLY", n1, 0.12), nb.math("MULTIPLY", n2, 0.05)))
    h = nb.math("ADD", h, nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, jm), nb.math("MULTIPLY", grav, 0.08)))
    rgh = nb.fmix(worn, 0.92, 0.8)
    finish(nb, outn, nb.bsdf(col, rgh, nb.bump(h, 1.0, 0.06), spec=0.25))
    return m


def mat_cobble(name):
    """Dlazba z oblazku / kocicich hlav."""
    m, nb, outn = new_mat(name)
    P = nb.geo("Position")
    co = nb.vmath("MULTIPLY", P, (1 / 0.17, 1 / 0.17, 0))
    e = nb.voro(co, 1.0, "DISTANCE_TO_EDGE", "Distance", 0.9, dim="2D")
    c = nb.voro(co, 1.0, "F1", "Color", 0.9, dim="2D")
    n = nb.noise(P, 18.0, 5.0, 0.6)
    sc = nb.ramp(nb.sep(c)[0], [(0.0, (0.2, 0.19, 0.17)), (0.5, (0.36, 0.34, 0.3)), (1.0, (0.45, 0.41, 0.34))])
    dirt = nb.rgb((0.14, 0.11, 0.08))
    col = nb.mix(nb.mr(e, 0.03, 0.12), dirt, sc)
    col = nb.mix(nb.math("MULTIPLY", nb.mr(nb.noise(P, 0.7), 0.45, 0.7), 0.6), col, (0.2, 0.16, 0.11))
    h = nb.math("ADD", nb.mr(e, 0.0, 0.25), nb.math("MULTIPLY", n, 0.1))
    finish(nb, outn, nb.bsdf(col, 0.82, nb.bump(h, 1.0, 0.04), spec=0.4))
    return m


def mat_ground(name):
    """Udusana hlina s travou a blatem (nadvori, okoli)."""
    m, nb, outn = new_mat(name)
    P = nb.geo("Position")
    n1 = nb.noise(P, 0.35, 6.0, 0.6)
    n2 = nb.noise(P, 4.0, 6.0, 0.6)
    n3 = nb.noise(P, 40.0, 3.0, 0.5)
    a = nb.attr("grass")
    soil = nb.mix(nb.mr(n2, 0.3, 0.7), (0.07, 0.05, 0.032), (0.17, 0.12, 0.075))
    grass = nb.mix(nb.mr(n2, 0.3, 0.7), (0.06, 0.09, 0.02), (0.15, 0.17, 0.05))
    gm = nb.mr(nb.math("ADD", nb.math("MULTIPLY", a, 0.9), nb.math("MULTIPLY", nb.math("SUBTRACT", n1, 0.5), 0.8)), 0.35, 0.6)
    col = nb.mix(gm, soil, grass)
    col = nb.mix(nb.math("MULTIPLY", nb.mr(n3, 0.6, 0.8), 0.35), col, (0.2, 0.17, 0.13))
    h = nb.math("ADD", nb.math("MULTIPLY", n2, 0.5), nb.math("MULTIPLY", n3, 0.3))
    finish(nb, outn, nb.bsdf(col, 0.95, nb.bump(h, 0.7, 0.04), spec=0.3))
    return m


def mat_simple(name, col, rough=0.8, metal=0.0, noise=0.15, nscale=20.0, bumpd=0.004, sss=0.0):
    m, nb, outn = new_mat(name)
    P = nb.geo("Position")
    n = nb.noise(P, nscale, 5.0, 0.6)
    r = nb.attr()
    c = nb.mix(nb.mr(n, 0.2, 0.8, 0.0, noise * 2), col, tuple(x * 0.6 for x in col))
    c = nb.mix(nb.math("MULTIPLY", r, noise * 1.5), c, tuple(min(1, x * 1.3) for x in col))
    finish(nb, outn, nb.bsdf(c, rough, nb.bump(n, 0.4, bumpd), metal=metal, sss=sss))
    return m


def mat_grass(name):
    m, nb, outn = new_mat(name)
    r = nb.attr()
    uv = nb.uv()
    v = nb.sep(uv)[1]
    c = nb.ramp(r, [(0.0, (0.07, 0.11, 0.02)), (0.5, (0.13, 0.19, 0.04)), (0.85, (0.2, 0.22, 0.06)), (1.0, (0.34, 0.3, 0.13))])
    c = nb.mix(nb.mr(v, 0.0, 0.5, 0.5, 0.0), c, (0.03, 0.04, 0.01))
    sh = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": c, "Roughness": 0.6, "Specular IOR Level": 0.4})
    tr = nb.n("ShaderNodeBsdfTranslucent", {"Color": c})
    mx = nb.n("ShaderNodeMixShader", {0: 0.35, 1: nb.out(sh, "BSDF"), 2: nb.out(tr)})
    finish(nb, outn, nb.out(mx))
    return m


def mat_iron(name):
    m, nb, outn = new_mat(name)
    P = nb.geo("Position")
    n = nb.noise(P, 12.0, 6.0, 0.6)
    rust = nb.mr(nb.noise(P, 3.0, 5.0, 0.7), 0.5, 0.7)
    col = nb.mix(rust, (0.05, 0.05, 0.05), (0.2, 0.09, 0.04))
    rough = nb.fmix(rust, 0.55, 0.9)
    metal = nb.fmix(rust, 0.85, 0.2)
    node = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": col, "Roughness": rough, "Metallic": metal, "Normal": nb.bump(n, 0.4, 0.003)})
    finish(nb, outn, nb.out(node, "BSDF"))
    return m


def mat_emit(name, col, strength):
    m, nb, outn = new_mat(name)
    e = nb.n("ShaderNodeEmission", {"Color": (*col, 1), "Strength": strength})
    finish(nb, outn, nb.out(e))
    return m


def mat_glass(name):
    m, nb, outn = new_mat(name)
    finish(nb, outn, nb.bsdf((0.55, 0.6, 0.5), 0.15, spec=0.5))
    m.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.85
    return m


def mat_fabric(name, col, pattern=False):
    m, nb, outn = new_mat(name)
    uv = nb.uv()
    u, v, _ = nb.sep(uv)
    weave = nb.math("MULTIPLY", nb.math("SINE", nb.math("MULTIPLY", u, 900)), nb.math("SINE", nb.math("MULTIPLY", v, 900)))
    n = nb.noise(nb.geo("Position"), 6.0, 4.0, 0.6)
    c = nb.mix(nb.mr(n, 0.3, 0.8, 0.0, 0.35), col, tuple(x * 0.55 for x in col))
    if pattern:
        # jednoduchy vzor: pruhy a kosoctverce
        band = nb.math("LESS_THAN", nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", v, 2.5)), 0.5)), 0.06)
        dia = nb.math("LESS_THAN", nb.math("ADD", nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", u, 3.0)), 0.5)),
                                                nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", v, 2.5)), 0.5))), 0.12)
        c = nb.mix(nb.math("MULTIPLY", nb.math("MAXIMUM", band, nb.math("MULTIPLY", dia, 0.6)), 0.55), c, (0.45, 0.34, 0.14))
    sh = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": c, "Roughness": 0.95, "Normal": nb.bump(weave, 0.15, 0.002)})
    sh.inputs["Sheen Weight"].default_value = 0.25
    finish(nb, outn, nb.out(sh, "BSDF"))
    return m


def mat_straw(name):
    m, nb, outn = new_mat(name)
    uv = nb.uv()
    P = nb.geo("Position")
    n = nb.noise(nb.vmath("MULTIPLY", P, (3, 3, 30)), 5.0, 6.0, 0.6)
    c = nb.mix(nb.mr(n, 0.2, 0.8), (0.3, 0.22, 0.09), (0.66, 0.54, 0.28))
    finish(nb, outn, nb.bsdf(c, 0.9, nb.bump(n, 1.0, 0.02)))
    return m


def mat_water(name):
    m, nb, outn = new_mat(name)
    P = nb.geo("Position")
    n = nb.noise(P, 3.0, 3.0, 0.5)
    finish(nb, outn, nb.bsdf((0.02, 0.03, 0.025), 0.05, nb.bump(n, 0.15, 0.01), spec=0.6))
    return m


def mat_hole(name):
    """Tmava dira (kapsy po lesenich, vnitrek strilen)."""
    m, nb, outn = new_mat(name)
    finish(nb, outn, nb.bsdf((0.02, 0.018, 0.015), 1.0))
    return m


def build_materials():
    MAT.clear()
    mat_masonry("zdivo", plaster_cover=0.55, plaster_col=(0.36, 0.3, 0.2))          # hradby: omitka misty opadana
    mat_masonry("zdivo_omitka", plaster_cover=0.85, plaster_col=(0.42, 0.35, 0.23))   # budovy: krémova vapenna omitka
    mat_masonry("zdivo_bile", plaster_cover=0.9, plaster_col=(0.55, 0.53, 0.47))       # bila (vez, hrazdeni)
    mat_masonry("zdivo_hole", plaster_cover=-0.8, grime=1.3)                           # prikop, zaklady
    mat_ashlar("kvadr")
    mat_ashlar("kvadr_sedy", (0.18, 0.175, 0.16))
    mat_plaster("omitka")
    mat_plaster("omitka_ven", (0.78, 0.74, 0.66), dirt=1.0)
    mat_plaster("omitka_bila", (0.6, 0.58, 0.52), dirt=1.0)
    mat_wood("dub", (0.2, 0.13, 0.08), (0.06, 0.04, 0.025))
    mat_wood("dub_ven", (0.2, 0.15, 0.1), (0.07, 0.05, 0.035), grey=0.6)
    mat_wood("prkna", (0.26, 0.18, 0.11), (0.1, 0.065, 0.04), worn=0.5, planks=True)
    mat_wood("prkna_ven", (0.22, 0.17, 0.12), (0.08, 0.06, 0.045), grey=0.7, planks=True)
    mat_wood("deska", (0.3, 0.21, 0.13), (0.12, 0.08, 0.05), worn=0.3)
    mat_wood("lip", (0.55, 0.42, 0.28), (0.3, 0.21, 0.13))
    mat_shingle("sindel")
    mat_flag("dlazba")
    mat_flag("dlazba_hrad", 0.5, (0.22, 0.2, 0.17))
    mat_cobble("kocicky")
    mat_ground("zem")
    mat_iron("zelezo")
    mat_simple("ocel", (0.5, 0.5, 0.52), 0.35, 1.0, 0.1)
    mat_simple("mosaz", (0.62, 0.45, 0.2), 0.35, 1.0, 0.1)
    mat_simple("saze", (0.02, 0.02, 0.02), 0.95)
    mat_simple("popel", (0.25, 0.24, 0.22), 1.0, 0.0, 0.4)
    mat_simple("hlina_dzban", (0.42, 0.22, 0.12), 0.65, 0.0, 0.2, 8.0)
    mat_simple("glazura", (0.22, 0.25, 0.14), 0.25, 0.0, 0.2, 8.0)
    mat_simple("cin", (0.55, 0.55, 0.55), 0.4, 1.0, 0.15)
    mat_simple("kuze", (0.22, 0.12, 0.06), 0.6, 0.0, 0.3, 30.0)
    mat_simple("vosk", (0.85, 0.8, 0.62), 0.5, 0.0, 0.05, sss=0.6)
    mat_simple("chleb", (0.45, 0.26, 0.1), 0.85, 0.0, 0.3, 15.0, 0.01)
    mat_simple("bylinky", (0.22, 0.26, 0.1), 0.9, 0.0, 0.4, 25.0, 0.01)
    mat_simple("jablko", (0.5, 0.12, 0.05), 0.45, 0.0, 0.3, 6.0)
    mat_simple("uhli", (0.04, 0.035, 0.03), 0.9, 0.0, 0.3, 30.0, 0.01)
    mat_simple("kura", (0.17, 0.13, 0.09), 0.95, 0.0, 0.4, 25.0, 0.02)
    mat_simple("drevo_rez", (0.6, 0.47, 0.3), 0.8, 0.0, 0.3, 30.0)
    mat_simple("lano", (0.45, 0.38, 0.25), 0.95, 0.0, 0.3, 60.0)
    mat_simple("kozesina", (0.28, 0.2, 0.13), 1.0, 0.0, 0.5, 40.0, 0.01)
    mat_straw("slama")
    mat_fabric("platno", (0.62, 0.57, 0.47))
    mat_fabric("pytlovina", (0.2, 0.15, 0.09))
    mat_fabric("sukno_cervene", (0.36, 0.05, 0.04), True)
    mat_fabric("sukno_modre", (0.06, 0.1, 0.26), True)
    mat_fabric("sukno_zelene", (0.08, 0.17, 0.08), True)
    mat_fabric("sukno_okr", (0.42, 0.28, 0.07), True)
    mat_fabric("prosteradlo", (0.72, 0.68, 0.6))
    mat_water("voda")
    mat_hole("dira")
    mat_glass("sklo")
    mat_emit("plamen", (1.0, 0.3, 0.05), 4.0)
    mat_emit("zhar", (0.9, 0.1, 0.01), 0.7)
    mat_simple("cervena", (0.4, 0.05, 0.03), 0.6)
    mat_simple("bila", (0.75, 0.72, 0.65), 0.6)
    mat_simple("zluta", (0.65, 0.48, 0.12), 0.6)
    mat_simple("modra", (0.05, 0.1, 0.3), 0.6)
    mat_grass("trava")
    mat_simple("jehlici", (0.025, 0.045, 0.02), 0.85, 0.0, 0.5, 3.0, 0.05)
    mat_wood("okenice", (0.36, 0.2, 0.09), (0.16, 0.08, 0.035), worn=0.4, planks=True)
    mat_wood("hraz", (0.12, 0.085, 0.06), (0.04, 0.03, 0.022), grey=0.35)
    mat_simple("malba_okr", (0.36, 0.2, 0.07), 0.9, 0.0, 0.25, 6.0)
    mat_simple("malba_cervena", (0.28, 0.05, 0.03), 0.9, 0.0, 0.25, 6.0)
    mat_simple("syr", (0.6, 0.42, 0.12), 0.6, 0.0, 0.2, 10.0)
    mat_simple("maso", (0.3, 0.1, 0.06), 0.55, 0.0, 0.3, 12.0)


# ======================================================================= strechy

def shingle_roof(P: Part, eL, eR, rR, rL, mat="sindel", deck="prkna_ven", row=0.13, length=0.44,
                 deck_t=0.03, lift=0.0, ridge=True):
    """Sindelova strecha na ctyruhelniku eL-eR (okap) a rL-rR (hreben).
    Kdyz rL == rR, je to trojuhelnik (jehlanova strecha). Pod sindelem je bedneni."""
    eL, eR, rR, rL = (Vector(p) for p in (eL, eR, rR, rL))
    up = (rL + rR) * 0.5 - (eL + eR) * 0.5
    a = (eR - eL).normalized()
    n = a.cross(up).normalized()
    if n.y < 0:
        n = -n
    s_dir = (up - a * up.dot(a)).normalized()       # smer nahoru po spadu
    slope_len = up.dot(s_dir)
    # bedneni
    if (rR - rL).length < 1e-3:
        if (eR - eL).cross(rL - eL).dot(n) > 0:
            P.tri(eL, eR, rL, deck_t, deck)
        else:
            P.tri(eR, eL, rL, deck_t, deck)
    elif (eR - eL).cross(rL - eL).dot(n) > 0:
        P.slab(eL, eR, rR, rL, deck_t, deck)
    else:
        P.slab(eR, eL, rL, rR, deck_t, deck)
    nrows = int(slope_len / row) + 1
    tilt = math.atan2(0.022, length)
    for k in range(nrows):
        t = min(1.0, (k * row + length * 0.92) / slope_len)    # horni konec sindele
        t0 = max(0.0, t - length / slope_len)
        L = eL.lerp(rL, t0)
        Rr = eR.lerp(rR, t0)
        Lt = eL.lerp(rL, t)
        Rt = eR.lerp(rR, t)
        # sirka radu: uzsi z obou konců (u trojuhelniku)
        x0 = max((L - eL).dot(a), (Lt - eL).dot(a))
        x1 = min((Rr - eL).dot(a), (Rt - eL).dot(a))
        x = x0 + R.uniform(0.0, 0.08)
        base0 = eL + s_dir * (t0 * slope_len)
        lay = 0.012 + (k % 2) * 0.004 + lift
        while x < x1 - 0.04:
            w = R.uniform(0.08, 0.16)
            if x + w > x1:
                w = x1 - x
                if w < 0.04:
                    break
            c = base0 + a * (x + w * 0.5) + s_dir * (length * 0.5) + n * lay
            bas = Matrix((a, n, -s_dir)).transposed() @ Matrix.Rotation(-tilt + jit(0.02), 3, "X") @ Matrix.Rotation(jit(0.03), 3, "Y")
            P.box(M(c, basis=bas), (w - 0.006, 0.014 + R.uniform(0, 0.006), length), mat)
            x += w
    if ridge and (rR - rL).length > 0.1:
        # hrebenac ze dvou prken
        m = (rL + rR) * 0.5
        P.beam(rL + n * 0.05, rR + n * 0.05, 0.16, 0.04, "prkna_ven", up=n)


# ======================================================================= hrazdeni

def half_timber(P: Part, a, b, normal, y0, y1, openings=(), bay=1.15, t=0.17, proud=0.035, braces=True, mat="hraz"):
    """Hrazdeni na lici zdi: prah, vaznice, sloupky, pazdeni a vzpery.
    a, b = konce lice ve vysce y0 (jen x, z), normal = smer ven. openings = [(s0, s1, ya, yb)] podel lice od a."""
    a, b, n = Vector(a), Vector(b), Vector(normal).normalized()
    a.y = b.y = 0.0
    d = b - a
    L = d.length
    d.normalize()
    up = Vector((0, 1, 0))

    def pt(s, y, off=0.0):
        return a + d * s + up * y + n * (proud * 0.5 + off)

    def beam_s(s0, y0_, s1, y1_, w=t, dep=0.08 + proud):
        P.beam(pt(s0, y0_), pt(s1, y1_), w, dep, mat, up=n, j=0.4)

    def blocked(s, ya, yb):
        return any(o[0] - 0.02 < s < o[1] + 0.02 and not (yb <= o[2] or ya >= o[3]) for o in openings)

    beam_s(0, y0 + t / 2, L, y0 + t / 2, 0.2)
    beam_s(0, y1 - t / 2, L, y1 - t / 2, 0.2)
    # sloupky: pravidelne + u kraju otvoru
    posts = {0.09, L - 0.09}
    k = 1
    while k * bay < L - 0.4:
        posts.add(k * bay)
        k += 1
    for o in openings:
        posts.add(o[0] - t / 2)
        posts.add(o[1] + t / 2)
    posts = sorted(p for p in posts if 0.0 <= p <= L)
    clean = []
    for p_ in posts:
        if clean and p_ - clean[-1] < 0.35:
            continue
        clean.append(p_)
    posts = clean
    for p_ in posts:
        if not blocked(p_, y0 + 0.2, y1 - 0.2):
            beam_s(p_, y0 + 0.18, p_, y1 - 0.18)
        else:
            for o in openings:
                if o[0] - 0.02 < p_ < o[1] + 0.02:
                    if o[2] > y0 + 0.4:
                        beam_s(p_, y0 + 0.18, p_, o[2])
                    if o[3] < y1 - 0.4:
                        beam_s(p_, o[3], p_, y1 - 0.18)
    # pazdeni (vodorovne ve vysce parapetu) a nadprazi otvoru
    ym = y0 + (y1 - y0) * 0.42
    for i in range(len(posts) - 1):
        s0, s1 = posts[i], posts[i + 1]
        mid = (s0 + s1) / 2
        if not blocked(mid, ym - 0.1, ym + 0.1):
            beam_s(s0, ym, s1, ym, 0.15)
    for o in openings:
        if o[2] > y0 + 0.25:
            beam_s(o[0] - t, o[2] - 0.07, o[1] + t, o[2] - 0.07, 0.14)
        if o[3] < y1 - 0.25:
            beam_s(o[0] - t, o[3] + 0.07, o[1] + t, o[3] + 0.07, 0.14)
    # vzpery v krajnich polich (do tvaru K) a v polich bez otvoru
    if braces:
        for i in range(len(posts) - 1):
            s0, s1 = posts[i], posts[i + 1]
            if s1 - s0 < 0.6 or blocked((s0 + s1) / 2, y0, y1):
                continue
            if i == 0 or i == len(posts) - 2 or i % 3 == 1:
                if i < (len(posts) - 1) / 2:
                    beam_s(s0 + 0.05, ym + 0.05, s1 - 0.08, y1 - 0.25, 0.14)
                    beam_s(s0 + 0.05, ym - 0.05, s1 - 0.08, y0 + 0.25, 0.14)
                else:
                    beam_s(s1 - 0.05, ym + 0.05, s0 + 0.08, y1 - 0.25, 0.14)
                    beam_s(s1 - 0.05, ym - 0.05, s0 + 0.08, y0 + 0.25, 0.14)


def shutters_on(P: Part, a, b, normal, s0, s1, ya, yb, deg=100, mat="okenice"):
    """Okno v lici: ram, olovene sklo/tma a dve okenice otevrene ven ke zdi."""
    a, b, n = Vector(a), Vector(b), Vector(normal).normalized()
    a.y = b.y = 0.0
    d = (b - a).normalized()
    up = Vector((0, 1, 0))
    w = s1 - s0
    c = a + d * ((s0 + s1) / 2) + up * ((ya + yb) / 2)
    # tmave sklo zapustene
    bas = Matrix((d, up, n)).transposed() if d.cross(up).dot(n) > 0 else Matrix((-d, up, n)).transposed()
    P.box(M(c - n * 0.12, basis=bas), (w, yb - ya, 0.01), "sklo")
    P.beam(c - d * (w / 2) + up * 0.0 - n * 0.12, c + d * (w / 2) - n * 0.12, 0.03, 0.02, "hraz", up=n)
    for sgn in (-1, 1):
        hinge = c + d * (sgn * (w / 2 + 0.02)) + n * 0.06
        # kridlo se otaci kolem svisle osy v pantu, otevrene ven
        dirv = (d * sgn * math.cos(math.radians(deg - 90)) * 1.0 + n * math.sin(math.radians(deg - 90))).normalized()
        cc = hinge + dirv * (w / 4)
        side = dirv
        nrm = up.cross(side).normalized()
        P.box(M(cc, basis=Matrix((side, up, nrm)).transposed()), (w / 2 - 0.02, yb - ya - 0.04, 0.035), mat)
        for yy in (-0.3, 0.3):
            P.box(M(cc + up * (yy * (yb - ya)) + nrm * 0.022, basis=Matrix((side, up, nrm)).transposed()), (w / 2 - 0.05, 0.05, 0.012), "zelezo")
