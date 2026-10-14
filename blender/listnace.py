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

CARD = {k: os.path.join(TEX_ROOT, "%s_karta.png" % k) for k in ("briza", "sipek", "dub", "lipa", "vrba")}
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
    rnd = random.Random({"briza": 5, "sipek": 9, "dub": 13, "lipa": 17, "vrba": 21}[kind])
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
    green = {"briza": (0.13, 0.22, 0.04), "sipek": (0.09, 0.17, 0.035), "dub": (0.07, 0.15, 0.03),
             "lipa": (0.1, 0.2, 0.04), "vrba": (0.12, 0.19, 0.06)}[kind]
    for tw in twigs:
        for k in range(1, len(tw)):
            p, q = tw[k - 1], tw[k]
            d = (q - p).normalized()
            # listy stridave po obou stranach
            n_leaves = {"briza": 3, "sipek": 2, "dub": 4, "lipa": 3, "vrba": 5}[kind]
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
                elif kind == "dub":
                    # dubovy list: protahly, laloky (serr) - vic listu pres sebe, husty
                    _leaf(verts, faces, cols, p.lerp(q, rnd.uniform(0.1, 0.9)), ld, up_l, rnd.uniform(0.08, 0.1), rnd.uniform(0.04, 0.055), col, 0.45)
                elif kind == "lipa":
                    _leaf(verts, faces, cols, p.lerp(q, rnd.uniform(0.2, 0.8)), ld, up_l, rnd.uniform(0.07, 0.09), rnd.uniform(0.06, 0.075), col, 0.1)
                elif kind == "vrba":
                    _leaf(verts, faces, cols, p.lerp(q, rnd.uniform(0.0, 1.0)), ld, up_l, rnd.uniform(0.09, 0.12), rnd.uniform(0.012, 0.018), col, 0.0)
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
            mt.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.07, 0.045, 0.03, 1) if kind != "briza" else (0.09, 0.05, 0.035, 1)
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


def bake_bark(res=1024):
    """Kura brizy (bezesvy dlazdice nahoru i dokola): krémove bila s jemnym sedym zrnem, vodorovne cocky
    s mekkym okrajem, odlupujici se proužky (narudle hnede pod nimi), cerne kosoctverce kolem jizev po vetvich,
    svisle jemne sedé zilkovani. Tmavy spodek kmene neni v texture (opakoval by se)."""
    import numpy as np
    from PIL import Image, ImageFilter
    rng = np.random.default_rng(4)
    h, w = res * 2, res
    yy, xx = np.mgrid[0:h, 0:w]

    def blob(sigma):
        a = rng.random((h, w)).astype(np.float32)
        im = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
        return np.array(im, np.float32) / 255.0
    base = np.array([0.9, 0.88, 0.83], np.float32)
    img = np.ones((h, w, 3), np.float32) * base
    n1, n2 = blob(18), blob(3)
    img *= (0.88 + 0.22 * n1)[..., None]
    img *= (0.95 + 0.08 * n2)[..., None]
    # svisle sede zilkovani
    vs = np.array(Image.fromarray((rng.random((h // 40, w)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    img *= (0.93 + 0.08 * vs)[..., None]
    gray = np.array([0.62, 0.61, 0.58], np.float32)

    def put(y0, x0, mask, col, k):
        hh, ww = mask.shape
        ys = (np.arange(hh) + y0) % h
        xs = (np.arange(ww) + x0) % w
        sub = img[np.ix_(ys, xs)]
        m = (mask * k)[..., None]
        img[np.ix_(ys, xs)] = sub * (1 - m) + col * m
    # odlupujici se proužky: tenke krémove/narudle pasky s tmavym spodnim okrajem
    for _ in range(140):
        L, th = int(rng.integers(40, 260)), int(rng.integers(4, 12))
        m = np.zeros((th + 3, L), np.float32)
        x = np.linspace(-1, 1, L)
        m[:th, :] = np.clip(1.2 - np.abs(x) ** 3, 0, 1)
        m[th:, :] = 0.0
        put(int(rng.integers(0, h)), int(rng.integers(0, w)), m, np.array([0.96, 0.9, 0.82]) * rng.uniform(0.9, 1.05), rng.uniform(0.4, 0.8))
        sh = np.zeros_like(m)
        sh[th:th + 2, :] = np.clip(1.2 - np.abs(x) ** 3, 0, 1)
        put(int(rng.integers(0, h)), int(rng.integers(0, w)), sh, np.array([0.55, 0.38, 0.28]), 0.5)
    # cocky (lenticely): vodorovne tmave carky s mekkym koncem, ruzne dlouhe
    for _ in range(900):
        L, th = int(rng.integers(10, 70)), int(rng.integers(2, 5))
        x = np.linspace(-1, 1, L)
        yv = np.linspace(-1, 1, th)
        m = np.clip(1.0 - np.abs(x)[None, :] ** 2 - 0.4 * np.abs(yv)[:, None] ** 2, 0, 1)
        put(int(rng.integers(0, h)), int(rng.integers(0, w)), m, np.array([0.12, 0.11, 0.1]), rng.uniform(0.5, 0.95))
    # cerne kosoctverce (jizvy po vetvich) a sede skvrny lisejniku
    for _ in range(9):
        r = int(rng.integers(10, 34))
        yv, xv = np.mgrid[-r:r, -r * 2:r * 2]
        m = np.clip(1.0 - (np.abs(yv) / r + np.abs(xv) / (2 * r)), 0, 1) ** 0.5
        put(int(rng.integers(0, h)), int(rng.integers(0, w)), m, np.array([0.08, 0.075, 0.07]), 0.9)
    for _ in range(40):
        r = int(rng.integers(20, 70))
        yv, xv = np.mgrid[-r:r, -r:r]
        m = np.clip(1.0 - np.hypot(yv, xv) / r, 0, 1) * (0.6 + 0.4 * rng.random((2 * r, 2 * r)))
        put(int(rng.integers(0, h)), int(rng.integers(0, w)), m, gray * rng.uniform(0.85, 1.1), 0.35)
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
    elif kind in ("dub", "lipa", "vrba"):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(os.path.join(TEX_ROOT, "kura_diff_2k.jpg"), check_existing=True)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nrm = nt.nodes.new("ShaderNodeTexImage")
        nrm.image = bpy.data.images.load(os.path.join(TEX_ROOT, "kura_nor_2k.jpg"), check_existing=True)
        nrm.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
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
    B.tube(trunk, [r0 * (1 - t / 9) ** 1.3 + 0.015 for t in range(9)], 12, 1, 0.5)
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


def _crown(B, rnd, center, rx, ry, rz, n, size, up_bias=0.0, droop=0.0):
    """Hustá koruna: karty na plaste elipsoidu (vetvicky miri ven) a cast uvnitr, aby nebyla pruhledna."""
    for i in range(n):
        u = rnd.uniform(-1.0, 1.0)
        a = rnd.uniform(0, 2 * math.pi)
        r = math.sqrt(1 - u * u)
        shell = rnd.uniform(0.55, 1.0) ** 0.5
        d = Vector((r * math.cos(a), r * math.sin(a), u))
        p = center + Vector((d.x * rx, d.y * ry, d.z * rz)) * shell
        out = (d + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), up_bias - droop))).normalized()
        sz = size * rnd.uniform(0.75, 1.25)
        B.card(p - out * sz * 0.35, out, Vector((0, 0, 1)) if abs(out.z) < 0.9 else Vector((1, 0, 0)), sz, sz * 0.55)


def oak_mesh(name, seed, h=12.0, kind="dub"):
    """Dub / lipa: silny kmen, v trecine vysky se deli na 4-6 mohutnych vetvi, siroka klenuta koruna
    (dub rozlozity a nizsi, lipa vyssi vejcita)."""
    rnd = random.Random(seed)
    B = _Mesh()
    s = h / 12.0
    r0 = (0.42 if kind == "dub" else 0.33) * s
    split = h * (0.32 if kind == "dub" else 0.4)
    trunk = [Vector((math.sin(k * 0.9 + seed) * 0.08 * s, math.cos(k * 0.7 + seed) * 0.08 * s, split * k / 4)) for k in range(5)]
    B.tube(trunk, [r0 * (1.25 if k == 0 else 1.0 - 0.08 * k) for k in range(5)], 9, 1, 0.5)
    top = trunk[-1]
    nl = rnd.randint(4, 6)
    tips = []
    for i in range(nl):
        a = 2 * math.pi * i / nl + rnd.uniform(-0.3, 0.3)
        out = Vector((math.cos(a), math.sin(a), 0))
        L = h * rnd.uniform(0.32, 0.45) * (1.2 if kind == "dub" else 0.85)
        rise = rnd.uniform(0.8, 1.3) * (0.8 if kind == "dub" else 1.4)
        pts = [top + out * (L * t) + Vector((0, 0, L * rise * (t - 0.3 * t * t))) for t in [k / 4 for k in range(5)]]
        B.tube(pts, [r0 * 0.55 * (1 - t / 5) + 0.03 for t in range(5)], 6, 1, 0.5)
        tips.append(pts[-1])
        for k in (2, 3):
            b = pts[k]
            a2 = a + rnd.choice((-1, 1)) * rnd.uniform(0.5, 1.0)
            o2 = Vector((math.cos(a2), math.sin(a2), rnd.uniform(0.2, 0.6))).normalized()
            B.tube([b, b + o2 * L * 0.35], [0.06 * s, 0.025 * s], 4, 1, 0.5)
    cz = split + h * (0.33 if kind == "dub" else 0.38)
    if kind == "dub":
        rx = ry = h * 0.42
        rz = h * 0.3
    else:
        rx = ry = h * 0.3
        rz = h * 0.42
    _crown(B, rnd, Vector((0, 0, cz)), rx, ry, rz, int(380 * (1.0 if kind == "dub" else 0.9)), h * 0.24, up_bias=0.2)
    _crown(B, rnd, Vector((0, 0, cz)), rx * 0.6, ry * 0.6, rz * 0.6, 90, h * 0.2, up_bias=0.1)
    for t in tips:
        _crown(B, rnd, t + Vector((0, 0, h * 0.04)), h * 0.15, h * 0.15, h * 0.11, 25, h * 0.16, up_bias=0.3)
    return B.build(name, [_card_mat(kind), _bark_mat(kind)])


def willow_mesh(name, seed, h=10.0):
    """Smutecni vrba u vody: kratky silny kmen (casto nakloneny), z hlavy vetve do deštníku a z nich
    az k zemi visi dlouhe pruty s uzkymi listy."""
    rnd = random.Random(seed)
    B = _Mesh()
    s = h / 10.0
    lean = Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 1.0))
    trunk = [lean * (h * 0.45 * k / 4) for k in range(5)]
    B.tube(trunk, [0.38 * s * (1.2 if k == 0 else 1 - 0.07 * k) for k in range(5)], 9, 1, 0.5)
    top = trunk[-1]
    for i in range(9):
        a = 2 * math.pi * i / 9 + rnd.uniform(-0.25, 0.25)
        out = Vector((math.cos(a), math.sin(a), 0))
        L = h * rnd.uniform(0.35, 0.5)
        pts = [top + out * (L * t) + Vector((0, 0, L * (1.0 * t - 0.75 * t * t))) for t in [k / 4 for k in range(5)]]
        B.tube(pts, [0.12 * s * (1 - t / 5) + 0.02 for t in range(5)], 4, 1, 0.5)
        for k in range(1, 5):
            p = pts[k]
            for _ in range(9):
                d = Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), -1.0)).normalized()
                ln = (p.z - 0.4) * rnd.uniform(0.45, 0.9)
                if ln > 0.8:
                    side = Vector((-out.y, out.x, 0)) if rnd.random() < 0.5 else out
                    B.card(p + Vector((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), 0)) * s, d, side, ln, h * 0.12)
    _crown(B, rnd, top + Vector((0, 0, h * 0.25)), h * 0.34, h * 0.34, h * 0.16, 140, h * 0.2, droop=0.8)
    return B.build(name, [_card_mat("vrba"), _bark_mat("dub")])


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
    for kind, base in (("dub", 400), ("lipa", 500)):
        LIB[kind] = []
        for i in range(4):
            h = 12.0
            LIB[kind].append((oak_mesh("%s_%d" % (kind, i), base + i, h, kind), h, 9.0))
    LIB["vrba"] = []
    for i in range(3):
        h = 10.0
        LIB["vrba"].append((willow_mesh("vrba_%d" % i, 600 + i, h), h, 7.0))


if __name__ == "__main__":
    bake_bark()
    for k in (sys.argv[1:] or ["briza", "sipek", "dub", "lipa", "vrba"]):
        bake_card(k)
