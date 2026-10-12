"""Listnate stromy a kere pro hru (stejny postup jako smrk v trees.py): vetvicky s listy se vymodeluji,
vyrenderuji shora do textury s pruhlednosti (karta) a strom/ker se poskladá z kmene, vetvi a karet.

  python listnace.py  -> tex_cache/briza_karta.png, sipek_karta.png, briza_kura.png
Druhy v knihovne vegetace: "briza" (bríza, i nalet) a "sipek" (sipkovy ker s plody).
"""
import math
import os
import random
import sys

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import TEX_ROOT  # noqa: E402

CARD = {k: os.path.join(TEX_ROOT, "%s_karta.png" % k) for k in ("briza", "sipek")}
BIRCH_BARK = os.path.join(TEX_ROOT, "briza_kura.png")


# ------------------------------------------------------------------ zapeceni karet

def _leaf(verts, faces, cols, c, d, nrm, L, W, col, serr=0.0):
    """List: osa d, sirka W, delka L, lehce prohnuty; pridava do seznamu."""
    side = d.cross(nrm).normalized()
    pts = [c]
    prof = [(0.0, 0.0), (0.15, 0.35), (0.35, 0.5), (0.55, 0.45), (0.75, 0.3), (0.92, 0.12), (1.0, 0.0)]
    i0 = len(verts)
    verts.append(c)
    for s, wv in prof[1:-1]:
        for sg in (-1, 1):
            p = c + d * (L * s) + side * (sg * W * wv * (1 + serr * random.uniform(-1, 1))) + nrm * (0.08 * L * (s - s * s))
            verts.append(p)
    verts.append(c + d * L)
    # vejir trojuhelniku: stred -> obrys
    left = [i0 + 1 + 2 * k for k in range(len(prof) - 2)]
    right = [i0 + 2 + 2 * k for k in range(len(prof) - 2)]
    tip = len(verts) - 1
    chain_l = [i0] + left + [tip]
    chain_r = [i0] + right + [tip]
    for k in range(len(chain_l) - 1):
        faces.append((chain_l[k], chain_r[k], chain_r[k + 1], chain_l[k + 1]) if chain_l[k] != chain_r[k] else
                     (chain_l[k], chain_r[k + 1], chain_l[k + 1]))
        cols.append(col)


def bake_card(kind, res=1024):
    import scene
    scene.reset()
    rnd = random.Random(5 if kind == "briza" else 9)
    random.seed(3)
    verts, faces, cols = [], [], []
    L = 1.0
    up = Vector((0, 0, 1))
    # hlavni vetvicka od leveho okraje (x=0) doprava, s bocnimi vetvickami
    twig_pts = [Vector((0.0, 0.0, 0.0))]
    for i in range(1, 11):
        x = L * i / 10
        twig_pts.append(Vector((x, 0.06 * math.sin(i * 1.3) * (x), 0.0)))
    twigs = [twig_pts]
    for i in range(2, 10):
        base = twig_pts[i]
        sg = 1 if i % 2 else -1
        a = math.radians(rnd.uniform(28, 50)) * sg
        dl = rnd.uniform(0.18, 0.32) * (1.15 - 0.5 * i / 10)
        d = Vector((math.cos(a), math.sin(a), 0))
        twigs.append([base + d * (dl * k / 4) for k in range(5)])
    green = (0.13, 0.22, 0.04) if kind == "briza" else (0.09, 0.17, 0.035)
    for tw in twigs:
        for k in range(1, len(tw)):
            p, q = tw[k - 1], tw[k]
            d = (q - p).normalized()
            # listy stridave po obou stranach
            n_leaves = 3 if kind == "briza" else 2
            for j in range(n_leaves):
                sg = 1 if (k + j) % 2 else -1
                a = math.radians(rnd.uniform(35, 70)) * sg
                ld = (Matrix.Rotation(a, 3, "Z") @ d).normalized()
                tone = rnd.uniform(0.75, 1.15)
                col = tuple(min(1, c * tone) for c in green)
                if rnd.random() < 0.06:
                    col = (0.3, 0.3, 0.06) if kind == "briza" else (0.24, 0.2, 0.05)
                # list naklopeny kolem stopky -> ruzne stiny
                tilt = Matrix.Rotation(rnd.uniform(-0.8, 0.8), 3, ld)
                up_l = (tilt @ up).normalized()
                if kind == "briza":
                    _leaf(verts, faces, cols, p.lerp(q, rnd.uniform(0.2, 0.8)), ld, up_l, rnd.uniform(0.05, 0.07), rnd.uniform(0.035, 0.048), col, 0.15)
                else:
                    # zpereny list sipku: stopka a 5-7 listku
                    c0 = p.lerp(q, 0.5)
                    for m_ in range(rnd.choice((2, 3))):
                        cc = c0 + ld * (0.035 * m_)
                        for sg2 in (-1, 1):
                            ld2 = (Matrix.Rotation(sg2 * math.radians(55), 3, "Z") @ ld).normalized()
                            _leaf(verts, faces, cols, cc, ld2, up_l, rnd.uniform(0.03, 0.04), rnd.uniform(0.018, 0.025), col, 0.2)
                    _leaf(verts, faces, cols, c0 + ld * 0.08, ld, up_l, 0.035, 0.022, col, 0.2)
        if kind == "sipek" and rnd.random() < 0.8:
            # sipky: 1-3 cervene plody na konci vetvicky
            tip = tw[-1]
            for m_ in range(rnd.randint(1, 3)):
                c = tip + Vector((rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), 0.02))
                i0 = len(verts)
                seg = 8
                for r_ in range(seg):
                    a = 2 * math.pi * r_ / seg
                    verts.append(c + Vector((0.013 * math.cos(a), 0.019 * math.sin(a), 0.0)))
                verts.append(c + Vector((0, 0, 0.02)))
                for r_ in range(seg):
                    faces.append((i0 + r_, i0 + (r_ + 1) % seg, i0 + seg))
                    cols.append((0.4, 0.03, 0.015))
    me = bpy.data.meshes.new("karta")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    for poly in me.polygons:
        c = cols[poly.index]
        for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
            ca.data[li].color = (c[0], c[1], c[2], 1.0)
    ob = bpy.data.objects.new("karta", me)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new("list")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    at = nt.nodes.new("ShaderNodeVertexColor")
    at.layer_name = "Col"
    nt.links.new(at.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.7
    me.materials.append(m)
    # vetvicky: tenke hnede valecky
    for tw in twigs:
        for p, q in zip(tw, tw[1:]):
            d = q - p
            bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.0035, depth=d.length, location=(p + q) / 2)
            o = bpy.context.object
            o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
            mt = bpy.data.materials.new("vetvicka")
            mt.use_nodes = True
            mt.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.07, 0.045, 0.03, 1) if kind == "sipek" else (0.09, 0.05, 0.035, 1)
            o.data.materials.append(mt)
    sc = bpy.context.scene
    cam = bpy.data.cameras.new("K")
    cam.type = "ORTHO"
    cam.ortho_scale = L
    co = bpy.data.objects.new("K", cam)
    sc.collection.objects.link(co)
    co.location = (L / 2, 0, 3)
    sc.camera = co
    sc.render.resolution_x = res
    sc.render.resolution_y = res // 2
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 24
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.92, 1.0, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    sc.world = w
    sun = bpy.data.lights.new("S", "SUN")
    sun.energy = 2.4
    so = bpy.data.objects.new("S", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(35), math.radians(-25), 0)
    sc.render.filepath = CARD[kind]
    bpy.ops.render.render(write_still=True)
    print("karta", kind)


def bake_bark(res=512):
    """Kura brizy: bila az sedobila, vodorovne tmave cocky, cerne praskliny a tmavy spodek (v=0 dole)."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(4)
    h, w = res * 2, res
    img = np.ones((h, w, 3), np.float32) * np.array([0.86, 0.85, 0.8])
    img *= (0.9 + 0.1 * rng.random((h, 1, 1)))
    for _ in range(420):
        y, x = rng.integers(0, h), rng.integers(0, w)
        L = rng.integers(6, 40)
        th = rng.integers(1, 4)
        img[y:y + th, max(0, x - L // 2):x + L // 2] *= rng.uniform(0.15, 0.5)
    for _ in range(60):
        y, x = rng.integers(0, h), rng.integers(0, w)
        r = rng.integers(4, 14)
        img[max(0, y - r):y + r, max(0, x - r // 2):x + r // 2] *= rng.uniform(0.1, 0.35)
    # tmavsi, rozpraskany spodek kmene
    yy = np.linspace(1, 0, h)[:, None, None]
    img *= 1 - 0.75 * np.clip((yy - 0.82) / 0.18, 0, 1) * (0.6 + 0.4 * rng.random((h, w, 1)))
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(BIRCH_BARK)
    print("kura brizy")


# ------------------------------------------------------------------ stromy a kere z karet

def _card_mat(kind):
    name = "%s_listi" % kind
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(CARD[kind], check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.8
    m.blend_method = "CLIP" if hasattr(m, "blend_method") else m.blend_method
    try:
        m.surface_render_method = "DITHERED"
    except AttributeError:
        pass
    m.use_backface_culling = False
    return m


def _bark_mat(kind):
    name = "%s_kura" % kind
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    if kind == "briza":
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(BIRCH_BARK, check_existing=True)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.16, 0.1, 0.07, 1)
    bsdf.inputs["Roughness"].default_value = 0.85
    return m


class _Mesh:
    def __init__(self):
        self.v, self.f, self.uv, self.mat = [], [], [], []

    def quad(self, p, uv, mat):
        i = len(self.v)
        self.v.extend(p)
        self.f.append((i, i + 1, i + 2, i + 3))
        self.uv.append(uv)
        self.mat.append(mat)

    def tube(self, pts, radii, sides, mat, v_scale=1.0):
        rings = []
        for k, (p, r) in enumerate(zip(pts, radii)):
            d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
            a = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))).normalized()
            b = d.cross(a)
            rings.append([p + (a * math.cos(2 * math.pi * s / sides) + b * math.sin(2 * math.pi * s / sides)) * r for s in range(sides)])
        acc = [0.0]
        for k in range(1, len(pts)):
            acc.append(acc[-1] + (pts[k] - pts[k - 1]).length)
        for k in range(len(pts) - 1):
            for s in range(sides):
                s2 = (s + 1) % sides
                self.quad([rings[k][s], rings[k][s2], rings[k + 1][s2], rings[k + 1][s]],
                          [(s / sides, acc[k] * v_scale), ((s + 1) / sides, acc[k] * v_scale),
                           ((s + 1) / sides, acc[k + 1] * v_scale), (s / sides, acc[k + 1] * v_scale)], mat)

    def card(self, base, d, up_, length, width):
        """Karta: vetvicka od base ve smeru d (u kmene vlevo v texture), dve poloviny do mirneho V."""
        side = d.cross(up_).normalized()
        nrm = side.cross(d).normalized()
        sag = -nrm * 0.12 * width
        tip = base + d * length
        self.quad([base, tip, tip + side * width / 2 + sag, base + side * width / 2 + sag], [(0, 0.5), (1, 0.5), (1, 1), (0, 1)], 0)
        self.quad([base - side * width / 2 + sag, tip - side * width / 2 + sag, tip, base], [(0, 0), (1, 0), (1, 0.5), (0, 0.5)], 0)

    def build(self, name, mats):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.v], [], self.f)
        uvl = me.uv_layers.new(name="UVMap")
        for poly, uv, mt in zip(me.polygons, self.uv, self.mat):
            for k in range(poly.loop_total):
                uvl.data[poly.loop_start + k].uv = uv[k]
            poly.material_index = mt
        for m in mats:
            me.materials.append(m)
        return me


def birch_mesh(name, seed, h=14.0):
    """Briza: stihly kmen s lehkym ohybem, vetve stoupaji a konce previsaji, listove karty visi dolu."""
    rnd = random.Random(seed)
    B = _Mesh()
    lean = Vector((rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), 1.0))
    trunk = []
    for k in range(9):
        t = k / 8
        off = Vector((math.sin(t * 2.3 + seed) * 0.08 * h / 14, math.cos(t * 1.7 + seed) * 0.06 * h / 14, 0))
        trunk.append(lean * (h * 0.92 * t) + off)
    r0 = 0.012 * h + 0.03
    B.tube(trunk, [r0 * (1 - t / 9) ** 1.3 + 0.015 for t in range(9)], 7, 1, 0.5)
    nb = int(10 + h * 1.4)
    for i in range(nb):
        t = rnd.uniform(0.32, 0.95)
        base = trunk[0].lerp(trunk[-1], t)
        a = rnd.uniform(0, 2 * math.pi)
        out = Vector((math.cos(a), math.sin(a), 0))
        L = h * rnd.uniform(0.16, 0.28) * (1.15 - t * 0.7)
        rise = rnd.uniform(0.6, 1.0)
        pts = []
        for k in range(5):
            s = k / 4
            pts.append(base + out * (L * s) + Vector((0, 0, L * (rise * s - 0.9 * s * s))))
        B.tube(pts, [0.04 * h / 14 * (1 - s / 5) + 0.008 for s in range(5)], 3, 1, 0.5)
        # previsle karty listi podel vetve
        for k in range(1, 5):
            p = pts[k]
            for _ in range(2):
                d = (out * rnd.uniform(0.2, 0.6) + Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), -1.0))).normalized()
                size = h / 14 * rnd.uniform(1.0, 1.5)
                B.card(p, d, out, size, size * 0.55)
    return B.build(name, [_card_mat("briza"), _bark_mat("briza")])


def rose_mesh(name, seed, h=1.8):
    """Sipkovy ker: obloukovite pruty od zeme, karty s listy a plody podel prutu."""
    rnd = random.Random(seed)
    B = _Mesh()
    for i in range(rnd.randint(9, 14)):
        a = rnd.uniform(0, 2 * math.pi)
        out = Vector((math.cos(a), math.sin(a), 0))
        L = h * rnd.uniform(0.9, 1.4)
        pts = [out * (L * 0.5 * s) + Vector((0, 0, L * (1.1 * s - 0.75 * s * s))) for s in [k / 5 for k in range(6)]]
        B.tube(pts, [0.012 * (1 - k / 7) + 0.004 for k in range(6)], 3, 1, 1.0)
        for k in range(1, 6):
            p = pts[k]
            d = (out * rnd.uniform(0.3, 0.9) + Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.3)))).normalized()
            size = h * rnd.uniform(0.28, 0.4)
            B.card(p, d, Vector((0, 0, 1)), size, size * 0.5)
    return B.build(name, [_card_mat("sipek"), _bark_mat("sipek")])


def add_to_library(LIB):
    LIB["briza"] = []
    for i in range(4):
        h = 14.0
        me = birch_mesh("briza_%d" % i, 200 + i, h)
        LIB["briza"].append((me, h, 4.0))
    LIB["sipek"] = []
    for i in range(3):
        h = 1.8
        me = rose_mesh("sipek_%d" % i, 300 + i, h)
        LIB["sipek"].append((me, h, 2.0))


if __name__ == "__main__":
    bake_bark()
    bake_card("briza")
    bake_card("sipek")
