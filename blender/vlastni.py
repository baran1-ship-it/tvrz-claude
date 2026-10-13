"""Vlastni predmety, ktere Poly Haven nema: kozesiny, koberce, polstare. Textury se generuji (PIL) do
tex_cache/vlastni, modely se stavi primo v Blenderu (volano z predmety.build pro id zacinajici '@')."""
import math
import os
import random

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
TD = os.path.join(HERE, "tex_cache", "vlastni")


def _save(im, name):
    os.makedirs(TD, exist_ok=True)
    p = os.path.join(TD, name + ".png")
    im.save(p)
    return p


def tex_fur(name, base, tip, seed, curly=False):
    """Srst: tisice kratkych chlupu ve smeru 'po srsti' (od hlavy dozadu), svetlejsi spicky, tmavsi podsada."""
    R = random.Random(seed)
    W = 1024
    im = Image.new("RGB", (W, W), tuple(int(c * 0.55) for c in base))
    d = ImageDraw.Draw(im)
    for _ in range(26000 if not curly else 9000):
        x, y = R.uniform(0, W), R.uniform(0, W)
        if curly:
            r = R.uniform(5, 13)
            col = tuple(int(c * R.uniform(0.75, 1.1)) for c in tip)
            d.arc((x - r, y - r, x + r, y + r), R.uniform(0, 360), R.uniform(180, 400), fill=col, width=3)
        else:
            L = R.uniform(10, 26)
            a = math.radians(90 + R.uniform(-25, 25))
            k = R.random()
            col = tuple(int(base[i] + (tip[i] - base[i]) * k) for i in range(3))
            d.line((x, y, x + math.cos(a) * L, y + math.sin(a) * L), fill=col, width=2)
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    return _save(im, name)


def tex_rug(name, field, border, accent, seed):
    """Tkany koberec: pole s kosoctverci, siroky okraj s cik-cak vzorem, utkana struktura a opotrebeni."""
    R = random.Random(seed)
    W, H = 1024, 1536
    im = Image.new("RGB", (W, H), field)
    d = ImageDraw.Draw(im)
    b = 130
    d.rectangle((0, 0, W, H), fill=border)
    d.rectangle((b, b, W - b, H - b), fill=field)
    # cik-cak v okraji
    for edge in range(4):
        n = 18 if edge % 2 == 0 else 26
        for i in range(n):
            if edge == 0:
                x0 = i * W / n
                d.polygon([(x0, 30), (x0 + W / n / 2, b - 30), (x0 + W / n, 30)], fill=accent)
            elif edge == 1:
                x0 = i * W / n
                d.polygon([(x0, H - 30), (x0 + W / n / 2, H - b + 30), (x0 + W / n, H - 30)], fill=accent)
            elif edge == 2:
                y0 = i * H / n
                d.polygon([(30, y0), (b - 30, y0 + H / n / 2), (30, y0 + H / n)], fill=accent)
            else:
                y0 = i * H / n
                d.polygon([(W - 30, y0), (W - b + 30, y0 + H / n / 2), (W - 30, y0 + H / n)], fill=accent)
    d.rectangle((b - 12, b - 12, W - b + 12, H - b + 12), outline=accent, width=8)
    # kosoctverce v poli
    for row in range(5):
        for col in range(3):
            cx = b + (W - 2 * b) * (col + 0.5) / 3
            cy = b + (H - 2 * b) * (row + 0.5) / 5
            s = 90
            d.polygon([(cx, cy - s), (cx + s * 0.7, cy), (cx, cy + s), (cx - s * 0.7, cy)], fill=border)
            s2 = 45
            d.polygon([(cx, cy - s2), (cx + s2 * 0.7, cy), (cx, cy + s2), (cx - s2 * 0.7, cy)], fill=accent)
    # tkana struktura a opotrebeni
    px = im.load()
    for y in range(H):
        for x in range(W):
            if (x + y) % 6 < 2 or (x - y) % 6 < 1:
                r, g, bb = px[x, y]
                px[x, y] = (int(r * 0.86), int(g * 0.86), int(bb * 0.86))
    noise = Image.effect_noise((W // 8, H // 8), 40).resize((W, H), Image.BICUBIC)
    im = Image.composite(im, Image.blend(im, Image.new("RGB", (W, H), (150, 130, 100)), 0.35), noise.point(lambda v: 255 if v > 95 else 140))
    return _save(im, name)


def tex_cloth(name, col, seed, stripes=None):
    R = random.Random(seed)
    W = 512
    im = Image.new("RGB", (W, W), col)
    d = ImageDraw.Draw(im)
    if stripes:
        for i in range(0, W, 64):
            d.rectangle((0, i + 20, W, i + 30), fill=stripes)
    px = im.load()
    for y in range(W):
        for x in range(W):
            k = 0.9 if (x % 4 < 2) ^ (y % 4 < 2) else 1.0
            k *= R.uniform(0.94, 1.04)
            r, g, b = px[x, y]
            px[x, y] = (int(r * k), int(g * k), int(b * k))
    return _save(im, name)


def _mat(name, img, rough=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(img)
    m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    return m


def _flat(outline, thick, mat, name, bulge=0.0, seed=1):
    """Ploche teleso z obrysu (x, z) s tloustkou; UV = pudorys v obrysu; horni plocha mirne zvlnena."""
    R = random.Random(seed)
    bm = bmesh.new()
    xs = [p[0] for p in outline]
    zs = [p[1] for p in outline]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    top = [bm.verts.new((x, -z, thick)) for x, z in outline]
    bot = [bm.verts.new((x, -z, 0.0)) for x, z in outline]
    ft = bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.triangulate(bm, faces=[ft])
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if all(v.co.z > thick * 0.5 for v in e.verts)], cuts=2, use_grid_fill=True)
    for v in bm.verts:
        if v.co.z > thick * 0.5:
            v.co.z += bulge * R.uniform(0, 1)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = ((l.vert.co.x - x0) / (x1 - x0), (-l.vert.co.y - z0) / (z1 - z0))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def bear(name):
    """Medvedi kozesina: trup, ctyri tlapy, hlava, krajem nepravidelne chlupy."""
    pts = []
    R = random.Random(5)
    # obrys parametricky: elipsa trupu + vybezky tlap a hlavy
    for i in range(96):
        a = 2 * math.pi * i / 96
        r = 1.0
        for ca, w, h in ((0.75, 0.22, 0.55), (2.39, 0.22, 0.55), (3.89, 0.22, 0.6), (5.53, 0.22, 0.6), (math.pi / 2 * 3, 0.0, 0.0)):
            da = math.atan2(math.sin(a - ca), math.cos(a - ca))
            r += h * math.exp(-(da / max(w, 0.01)) ** 2) if w else 0
        da = math.atan2(math.sin(a - math.pi * 1.5), math.cos(a - math.pi * 1.5))
        r += 0.35 * math.exp(-(da / 0.28) ** 2)
        r += R.uniform(-0.03, 0.03)
        pts.append((math.cos(a) * r * 0.62, math.sin(a) * r * 0.9))
    m = _mat(name, tex_fur("srst_medved", (60, 40, 25), (120, 88, 58), 3), 0.95)
    return _flat(pts, 0.035, m, name, 0.02)


def sheep(name):
    R = random.Random(9)
    pts = []
    for i in range(64):
        a = 2 * math.pi * i / 64
        r = 1.0 + 0.12 * math.sin(3 * a + 1) + 0.08 * math.sin(5 * a) + R.uniform(-0.04, 0.04)
        pts.append((math.cos(a) * r * 0.45, math.sin(a) * r * 0.62))
    m = _mat(name, tex_fur("srst_ovce", (200, 188, 160), (235, 226, 205), 4, curly=True), 0.95)
    return _flat(pts, 0.05, m, name, 0.03)


def rug(name, w, l, cols, seed):
    m = _mat(name, tex_rug("koberec_" + name, *cols, seed), 0.95)
    pts = [(-w / 2, -l / 2), (w / 2, -l / 2), (w / 2, l / 2), (-w / 2, l / 2)]
    ob = _flat(pts, 0.012, m, name, 0.0)
    # trasne na kratkych koncich
    tm = bpy.data.materials.new(name + "_trasne")
    tm.use_nodes = True
    tm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.68, 0.55, 1)
    for sz in (-1, 1):
        for k in range(int(w / 0.035)):
            x = -w / 2 + 0.02 + k * 0.035
            bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=0.004, depth=0.08, location=(x, -(sz * (l / 2 + 0.035)), 0.006),
                                                rotation=(math.pi / 2, 0, 0))
            o = bpy.context.object
            o.data.materials.append(tm)
    return ob


def pillow(name, col, stripes, seed):
    m = _mat(name, tex_cloth("latka_" + name, col, seed, stripes), 0.85)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=1.0)
    ob = bpy.context.object
    for v in ob.data.vertices:
        p = v.co
        f = lambda c: math.copysign(abs(c) ** 0.35, c)  # noqa: E731
        v.co = Vector((f(p.x) * 0.25, f(p.y) * 0.25, f(p.z) * 0.07 * (1.0 - 0.35 * max(abs(f(p.x)), abs(f(p.y))))))
    ob.data.materials.append(m)
    ob.name = name
    bpy.ops.object.shade_smooth()
    return ob


BUILD = {
    "kozesina": lambda: bear("kozesina"),
    "ovci_kuze": lambda: sheep("ovci_kuze"),
    "koberec": lambda: rug("koberec", 1.6, 2.4, ((128, 30, 24), (32, 44, 92), (206, 160, 70)), 11),
    "koberec_modry": lambda: rug("koberec_modry", 1.1, 1.7, ((36, 52, 100), (130, 34, 26), (210, 176, 96)), 12),
    "polstar": lambda: pillow("polstar", (140, 36, 28), (200, 160, 80), 21),
    "polstar_zeleny": lambda: pillow("polstar_zeleny", (46, 84, 44), None, 22),
}


# ======================================================================= drevo a zelezo (hodovni stul, louce)

def _wood_mat(name, tex="tram", tint=(1, 1, 1)):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(HERE, "tex_cache", tex + "_diff_2k.jpg"), check_existing=True)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(t.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = (*tint, 1)
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(os.path.join(HERE, "tex_cache", tex + "_nor_2k.jpg"), check_existing=True)
    n.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(n.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.8
    return m


def _plain(name, col, metal=0.0, rough=0.6):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    return m


def _box(c, size, mat, rot=0.0, uvs=1.2, bevel=0.008):
    """Hranol se stredem c (Blender, Z nahoru), UV podle rozmeru (vlakna podel nejdelsi strany)."""
    bpy.ops.mesh.primitive_cube_add(location=c, rotation=(0, 0, rot))
    o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.verify()
    R = random.Random(len(bpy.data.objects))
    ou, ov = R.random(), R.random()
    longx = size[0] >= size[1]
    for f in bm.faces:
        n = f.normal
        for l in f.loops:
            p = l.vert.co
            if abs(n.z) > 0.5:
                a, b = (p.x, p.y) if longx else (p.y, p.x)
            elif abs(n.x) > 0.5:
                a, b = (p.z, p.y) if not longx else (p.y, p.z)
            else:
                a, b = (p.x, p.z) if longx else (p.z, p.x)
            l[uv].uv = (b / uvs + ou, a / uvs + ov)
    bm.to_mesh(o.data)
    bm.free()
    if bevel:
        m = o.modifiers.new("b", "BEVEL")
        m.width = bevel
        m.segments = 2
    o.data.materials.append(mat)
    return o


def feast_table(name, L=4.2, W=1.05, H=0.78):
    """Hodovni stul na kozach: deska ze ctyr silnych fosen, dve kozy do X s podnozi a vzpera po delce."""
    R = random.Random(41)
    dub = _wood_mat("dub_hodovni", "tram", (0.62, 0.5, 0.38))
    n = 4
    pw = W / n
    for k in range(n):
        y = -W / 2 + pw * (k + 0.5)
        _box((R.uniform(-0.02, 0.02), y, H - 0.04), (L + R.uniform(-0.03, 0.03), pw - 0.008, 0.075), dub, rot=math.radians(R.uniform(-0.3, 0.3)))
    for sx in (-1, 1):
        x = sx * (L / 2 - 0.55)
        _box((x, 0, H - 0.12), (0.12, W - 0.1, 0.1), dub)                  # hlava kozy pod deskou
        for sy in (-1, 1):
            # nohy do X (sikme hranoly)
            bpy.ops.mesh.primitive_cube_add(location=(x, sy * 0.22, (H - 0.17) / 2), rotation=(sy * math.radians(22), 0, 0))
            o = bpy.context.object
            o.scale = (0.05, 0.05, (H - 0.17) / 2 / math.cos(math.radians(22)))
            o.data.materials.append(dub)
        _box((x, 0, 0.04), (0.14, W - 0.15, 0.08), dub)                    # patka
    _box((0, 0, 0.32), (L - 1.0, 0.1, 0.12), dub)                          # podelna vzpera
    for sx in (-1, 1):
        _box((sx * (L / 2 - 0.55), 0, 0.32), (0.06, 0.06, 0.2), dub)       # klin
    return None


def feast_bench(name, L=4.0):
    dub = _wood_mat("dub_hodovni", "tram", (0.62, 0.5, 0.38))
    _box((0, 0, 0.44), (L, 0.32, 0.07), dub)
    for sx in (-1, 1):
        x = sx * (L / 2 - 0.35)
        _box((x, 0, 0.2), (0.07, 0.3, 0.4), dub)
        _box((x, 0, 0.03), (0.09, 0.36, 0.06), dub)
    _box((0, 0, 0.22), (L - 0.8, 0.07, 0.08), dub)
    return None


def torch_bracket(name, with_torch=True):
    """Kovany drzak louce na zed: ctvercova plotna se ctyrmi hreby, vyhnute rameno s rozvilinou
    a objimka; zed je rovina y = 0 (Blender), drzak vycniva do -y (ve hre +z = od zdi)."""
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    _box((0, 0.006, 0.0), (0.09, 0.012, 0.14), fe, bevel=0.002)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.009, location=(sx * 0.03, -0.003, sz * 0.05), segments=8, ring_count=4)
            bpy.context.object.data.materials.append(fe)
    # rameno: kratky profil vodorovne ven, pak objimka
    _box((0, -0.06, -0.02), (0.022, 0.12, 0.018), fe, bevel=0.002)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.032, minor_radius=0.007, location=(0, -0.14, -0.02))
    bpy.context.object.data.materials.append(fe)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.006, location=(0, -0.14, 0.06))
    bpy.context.object.data.materials.append(fe)
    _box((0, -0.11, 0.02), (0.012, 0.012, 0.09), fe, bevel=0.0)
    # rozvilina pod ramenem
    bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.005, location=(0, -0.05, -0.065), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(fe)
    if with_torch:
        torch(None, (0, -0.14, -0.13))
    return None


def torch(name, base=(0, 0, 0)):
    """Louc jako v KCD: soustruzena jasanova nasada (dolu se zuzuje, oslapana rukojet), hlava ze svazku
    stipanych louci stazenych dvema kovanymi krouzky, pres ne pruhy pytloviny napustene smolou
    (leskle, ovinute do sroubovice) a ohorela spicka."""
    R = random.Random(3)
    wood = _wood_mat("louc_drevo", "tram", (0.85, 0.72, 0.58))
    split = _wood_mat("louc_trisky", "tram", (0.7, 0.55, 0.4))
    tar = _plain("louc_smola", (0.035, 0.025, 0.018), 0.0, 0.32)
    char = _plain("louc_uhel", (0.015, 0.013, 0.012), 0.0, 0.9)
    cloth = _plain("louc_pytlovina", (0.12, 0.085, 0.05), 0.0, 0.7)
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    bx, by, bz = base
    # nasada
    prof = [(0.0, 0.0), (0.012, 0.0), (0.014, 0.01), (0.015, 0.12), (0.0165, 0.14), (0.016, 0.16), (0.018, 0.34), (0.02, 0.4), (0.0, 0.4)]
    sh = _turned((bx, by, bz), prof, wood, 12)
    # omotana rukojet (kozeny remen)
    _turned((bx, by, bz + 0.06), [(0.0155, 0.0), (0.0175, 0.005), (0.0175, 0.11), (0.0155, 0.115)], cloth, 12)
    for v in sh.data.vertices:
        v.co.x += 0.002 * math.sin(v.co.z * 9.0)
    # svazek louci: 9 stipanych hranolku kolem konce nasady, nahore se rozevira
    for k in range(9):
        a = 2 * math.pi * k / 9 + R.uniform(-0.1, 0.1)
        r = 0.02
        h = R.uniform(0.2, 0.24)
        o = _box((bx + math.cos(a) * r, by + math.sin(a) * r, bz + 0.36 + h / 2), (0.012, 0.016, h), split, rot=a, bevel=0.001)
        for v in o.data.vertices:
            t = (v.co.z + h / 2) / h
            v.co.x *= 1.0 + 0.5 * t
        o.rotation_euler = (math.cos(a + math.pi / 2) * 0.08, math.sin(a + math.pi / 2) * 0.08, a)
    for zz in (0.38, 0.47):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.031, minor_radius=0.0045, location=(bx, by, bz + zz), major_segments=16, minor_segments=6)
        bpy.context.object.data.materials.append(fe)
    # smolou napustene pruhy pytloviny ve sroubovici
    for layer, (z0, z1, rr) in enumerate(((0.395, 0.53, 0.034), (0.41, 0.545, 0.037), (0.4, 0.5, 0.039))):
        n = 70
        bm = bmesh.new()
        prev = None
        for i in range(n + 1):
            t = i / n
            a = t * 2 * math.pi * (4.2 if layer != 1 else -3.6) + layer * 2.1
            z = z0 + (z1 - z0) * t
            r = rr * (1.0 + 0.05 * math.sin(i * 0.9) + 0.03 * math.sin(i * 2.3)) * (1 - 0.12 * t)
            c = (bx + math.cos(a) * r, by + math.sin(a) * r, bz + z)
            ring = [bm.verts.new((c[0] + math.cos(a) * dx, c[1] + math.sin(a) * dx, c[2] + dz))
                    for dx, dz in ((-0.0035, -0.011), (0.0035, -0.012), (0.0035, 0.012), (-0.0035, 0.011))]
            if prev:
                for j in range(4):
                    bm.faces.new((prev[j], prev[(j + 1) % 4], ring[(j + 1) % 4], ring[j]))
            prev = ring
        me = bpy.data.meshes.new("pruh")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(cloth if layer == 0 else tar)
        ob = bpy.data.objects.new("pruh", me)
        bpy.context.scene.collection.objects.link(ob)
    # jadro hlavy (smola) a ohorela spicka
    _turned((bx, by, bz + 0.39), [(0.0, 0.0), (0.028, 0.0), (0.032, 0.06), (0.03, 0.13), (0.022, 0.16), (0.0, 0.165)], tar, 14)
    _turned((bx, by, bz + 0.525), [(0.0, 0.0), (0.027, 0.0), (0.022, 0.03), (0.012, 0.042), (0.0, 0.046)], char, 10)
    return None


BUILD.update({
    "stul_hodovni": lambda: feast_table("stul_hodovni"),
    "lavice_hodovni": lambda: feast_bench("lavice_hodovni"),
    "drzak_louce": lambda: torch_bracket("drzak_louce", False),
    "louc": lambda: torch("louc"),
})


def _turned(c, profile, mat, seg=16):
    """Soustruzeny dil: profil [(r, z)] rotovany kolem svisle osy v bode c."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0.0, z)) for r, z in profile]
    for a, b in zip(vs, vs[1:]):
        bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), steps=seg, angle=2 * math.pi)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for l in f.loops:
            p = l.vert.co
            l[uv].uv = (math.atan2(p.y, p.x) / (2 * math.pi) * 0.4, p.z / 1.2)
    me = bpy.data.meshes.new("soustruh")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new("soustruh", me)
    ob.location = c
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth()
    return ob


def lord_table(name, L=4.6, W=1.3, H=0.82):
    """Pansky hodovni stul: silna deska (12 cm) ze tri fosen s profilovanou hranou, lub s vyrezavanym obloucky,
    sest soustruzenych noh (baluster), podnozky pri zemi a kovane rohove pasy."""
    dub = _wood_mat("dub_pansky", "tram", (0.42, 0.3, 0.2))
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    n = 3
    pw = W / n
    for k in range(n):
        y = -W / 2 + pw * (k + 0.5)
        _box((0, y, H - 0.06), (L, pw - 0.006, 0.12), dub, bevel=0.012)
    # profilovana hrana: lista po obvodu pod deskou
    for sy in (-1, 1):
        _box((0, sy * (W / 2 - 0.02), H - 0.14), (L - 0.04, 0.06, 0.05), dub, bevel=0.015)
    for sx in (-1, 1):
        _box((sx * (L / 2 - 0.02), 0, H - 0.14), (0.06, W - 0.04, 0.05), dub, bevel=0.015)
    # lub s obloucky (desky s vyrezem: aproximace dilci zubu)
    for sy in (-1, 1):
        _box((0, sy * (W / 2 - 0.12), H - 0.24), (L - 0.5, 0.05, 0.16), dub)
        for k in range(14):
            x = -L / 2 + 0.45 + k * (L - 0.9) / 13
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(x, sy * (W / 2 - 0.095), H - 0.32), segments=8, ring_count=4)
            bpy.context.object.data.materials.append(dub)
    for sx in (-1, 1):
        _box((sx * (L / 2 - 0.25), 0, H - 0.24), (0.05, W - 0.3, 0.16), dub)
    # soustruzene nohy (baluster): 3 pary
    leg = [(0.0, 0.0), (0.085, 0.0), (0.085, 0.06), (0.06, 0.09), (0.07, 0.16), (0.1, 0.28), (0.1, 0.36), (0.065, 0.46),
           (0.055, 0.55), (0.07, 0.6), (0.07, 0.62), (0.06, H - 0.3), (0.075, H - 0.3), (0.075, H - 0.14), (0.0, H - 0.14)]
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            _turned((sx * (L / 2 - 0.25), sy * (W / 2 - 0.15), 0.0), leg, dub)
    # podnozky
    for sy in (-1, 1):
        _box((0, sy * (W / 2 - 0.15), 0.12), (L - 0.5, 0.08, 0.08), dub)
    for sx in (-1, 0, 1):
        _box((sx * (L / 2 - 0.25), 0, 0.12), (0.08, W - 0.3, 0.08), dub)
    # kovane rohove pasy na desce
    for sx in (-1, 1):
        for sy in (-1, 1):
            _box((sx * (L / 2 - 0.12), sy * (W / 2 - 0.004), H - 0.06), (0.24, 0.012, 0.1), fe, bevel=0.002)
            _box((sx * (L / 2 - 0.004), sy * (W / 2 - 0.12), H - 0.06), (0.012, 0.24, 0.1), fe, bevel=0.002)
    return None


def lord_chair(name):
    """Panske kreslo k hodovnimu stolu: vysoke opradlo s gotickou korunou, podrucky, soustruzene nohy."""
    dub = _wood_mat("dub_pansky", "tram", (0.42, 0.3, 0.2))
    leg = [(0.0, 0.0), (0.04, 0.0), (0.04, 0.05), (0.03, 0.1), (0.045, 0.22), (0.032, 0.38), (0.04, 0.44), (0.0, 0.44)]
    for sx in (-1, 1):
        _turned((sx * 0.26, -0.22, 0.0), leg, dub, 12)
        _box((sx * 0.26, 0.22, 0.65), (0.07, 0.07, 1.3), dub)
        _box((sx * 0.26, 0.0, 0.7), (0.06, 0.5, 0.05), dub)               # podrucka
        _turned((sx * 0.26, -0.2, 0.47), [(0.0, 0.0), (0.03, 0.0), (0.025, 0.1), (0.032, 0.2), (0.0, 0.22)], dub, 10)
    _box((0, 0, 0.47), (0.62, 0.55, 0.06), dub)
    _box((0, 0.22, 0.95), (0.5, 0.04, 0.75), dub)
    for k in range(5):
        x = -0.2 + 0.1 * k
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.035, depth=0.14, location=(x, 0.22, 1.37))
        bpy.context.object.data.materials.append(dub)
    _box((0, 0.22, 1.3), (0.6, 0.06, 0.06), dub)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(sx * 0.26, 0.22, 1.33), segments=10, ring_count=6)
        bpy.context.object.data.materials.append(dub)
    return None


BUILD.update({
    "stul_pansky": lambda: lord_table("stul_pansky"),
    "kreslo_panske": lambda: lord_chair("kreslo_panske"),
})


# ======================================================================= ctvrta varka: stity, tapiserie, koberce,
# dlouhe zbrane a hak na zed. Stity a zbrane lezi (lici nahoru) - na hak je hra otoci licem ke zdi ven.

ERBY = os.path.join(HERE, "..", "obrazky", "erby")


def _poly_mesh(name, outline, thick, mat_face, mat_side, uv_rect, curve=0.0, mat_back=None):
    """Deska z obrysu v rovine XY (lice nahoru +Z), lice s UV podle obdelniku uv_rect (x0, y0, w, h),
    volitelne mirne vypoukla (curve = prohnuti ve stredu)."""
    bm = bmesh.new()
    xs = [p[0] for p in outline]
    wmax = max(abs(x) for x in xs) or 1.0

    def bend(x):
        return curve * (1.0 - (x / wmax) ** 2)
    top = [bm.verts.new((x, y, thick + bend(x))) for x, y in outline]
    bot = [bm.verts.new((x, y, bend(x))) for x, y in outline]
    ft = bm.faces.new(top)
    fb = bm.faces.new(list(reversed(bot)))
    n = len(outline)
    sides = []
    for i in range(n):
        j = (i + 1) % n
        sides.append(bm.faces.new((bot[i], bot[j], top[j], top[i])))
    ft.material_index = 0
    fb.material_index = 2 if mat_back else 1
    for f in sides:
        f.material_index = 1
    r = bmesh.ops.triangulate(bm, faces=[ft, fb])
    uv = bm.loops.layers.uv.new("UVMap")
    x0, y0, w, h = uv_rect
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = ((l.vert.co.x - x0) / w, (l.vert.co.y - y0) / h)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat_face)
    me.materials.append(mat_side)
    if mat_back:
        me.materials.append(mat_back)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


ICONS = os.path.join(HERE, "tex_cache", "game_icons")


def _charge(icon, col, size):
    """Figura ze SVG (game-icons.net, CC BY 3.0) obarvena barvou col, s cernou konturou jako na malovanem stitu."""
    import io
    import cairosvg
    if icon == "@ruze":
        return _heraldic_rose(col, size)
    if icon == "@ostrve":
        return _ragged_staffs(col, size)
    if icon == "@hvezda":
        return _star8(col, size)
    if icon == "@zubr":
        return _aurochs(col, size)
    svg = open(os.path.join(ICONS, icon + ".svg")).read()
    svg = svg.replace('<path d="M0 0h512v512H0z"/>', "").replace('fill="#fff"', 'fill="#ffffff"')
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    m = Image.open(io.BytesIO(png)).convert("RGBA").split()[3]          # alfa = tvar figury
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    edge = m.filter(ImageFilter.MaxFilter(7))
    out.paste((20, 16, 12, 255), (0, 0), edge)
    out.paste((*col, 255), (0, 0), m)
    return out


def _heraldic_rose(col, size):
    """Heraldicka ruze: pet zaoblenych platku, mezi nimi zelene kališní lístky, uprostred semeník s tecka­mi;
    cerne obrysy jako na malovanem stitu."""
    S = size * 2                      # kresli se ve dvojnasobku a zmensi (vyhlazeni)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    ink = (20, 16, 12, 255)
    green = (40, 110, 50, 255)
    for i in range(5):                # kalisni listky (spicate, mezi platky)
        a = math.radians(-90 + 36 + 72 * i)
        tip = (c + math.cos(a) * S * 0.47, c + math.sin(a) * S * 0.47)
        l = (c + math.cos(a - 0.22) * S * 0.25, c + math.sin(a - 0.22) * S * 0.25)
        r = (c + math.cos(a + 0.22) * S * 0.25, c + math.sin(a + 0.22) * S * 0.25)
        d.polygon([l, tip, r], fill=green, outline=ink, width=S // 120)
    for i in range(5):                # platky: kruhy kolem stredu se srdcovitym zarezem
        a = math.radians(-90 + 72 * i)
        px, py = c + math.cos(a) * S * 0.2, c + math.sin(a) * S * 0.2
        R = S * 0.19
        d.ellipse((px - R, py - R, px + R, py + R), fill=(*col, 255), outline=ink, width=S // 100)
    for i in range(5):                # zarezy na platcich
        a = math.radians(-90 + 72 * i)
        px, py = c + math.cos(a) * S * 0.37, c + math.sin(a) * S * 0.37
        d.line((px, py, c + math.cos(a) * S * 0.3, c + math.sin(a) * S * 0.3), fill=ink, width=S // 120)
    R = S * 0.11
    d.ellipse((c - R, c - R, c + R, c + R), fill=(214, 160, 40, 255) if col[2] > 150 else (40, 110, 50, 255), outline=ink, width=S // 100)
    for i in range(8):
        a = 2 * math.pi * i / 8
        x, y = c + math.cos(a) * R * 0.6, c + math.sin(a) * R * 0.6
        d.ellipse((x - S / 120, y - S / 120, x + S / 120, y + S / 120), fill=ink)
    return im.resize((size, size), Image.LANCZOS)


def _ragged_staffs(col, size):
    """Ronovske ostrve: dva zkrizene osekane kmeny s pahyly po stranach (pani z Lipe, z Dube, Lichtenburkove)."""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ink = (20, 16, 12, 255)
    w = S * 0.085
    for sgn in (-1, 1):
        a = math.radians(45 * sgn)
        dx, dy = math.sin(a), -math.cos(a)            # smer kmene (zdola nahoru)
        nx, ny = -dy, dx
        L = S * 0.46
        p0 = (S / 2 - dx * L, S / 2 - dy * L)
        p1 = (S / 2 + dx * L, S / 2 + dy * L)
        poly = [(p0[0] + nx * w, p0[1] + ny * w), (p1[0] + nx * w, p1[1] + ny * w), (p1[0] - nx * w, p1[1] - ny * w), (p0[0] - nx * w, p0[1] - ny * w)]
        d.polygon(poly, fill=ink)
        poly2 = [(p0[0] + nx * w * 0.8, p0[1] + ny * w * 0.8), (p1[0] + nx * w * 0.8, p1[1] + ny * w * 0.8),
                 (p1[0] - nx * w * 0.8, p1[1] - ny * w * 0.8), (p0[0] - nx * w * 0.8, p0[1] - ny * w * 0.8)]
        d.polygon(poly2, fill=(*col, 255))
        # pahyly: stridave vlevo a vpravo, sikmo nahoru
        for k in range(6):
            t = -0.8 + 0.3 * k
            side = 1 if k % 2 == 0 else -1
            bx, by = S / 2 + dx * L * t + nx * w * side * 0.6, S / 2 + dy * L * t + ny * w * side * 0.6
            ex, ey = bx + (nx * side * 0.75 + dx * 0.65) * S * 0.11, by + (ny * side * 0.75 + dy * 0.65) * S * 0.11
            d.line((bx, by, ex, ey), fill=ink, width=int(w * 1.05))
            d.line((bx, by, ex, ey), fill=(*col, 255), width=int(w * 0.7))
    return im.resize((size, size), Image.LANCZOS)


def _aurochs(col, size):
    """Pernstejnska zubri hlava zepredu: mohutna hlava, zahnute rohy, usi, zlate oci a zlaty kruh v nozdrach."""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    gold = (226, 182, 52, 255)
    body = (*col, 255)
    # rohy: tluste oblouky nahoru a dovnitr
    for sgn in (-1, 1):
        pts = []
        for i in range(21):
            t = i / 20
            a = math.radians(200 - 150 * t) if sgn < 0 else math.radians(-20 + 150 * t)
            r = S * 0.22
            x = c + sgn * S * 0.2 + math.cos(a) * r * (1 if sgn > 0 else 1)
            y = S * 0.3 - math.sin(a) * r * 0.9
            pts.append((x, y))
        for i in range(len(pts) - 1):
            wdt = int(S * (0.07 * (1 - i / 20) + 0.015))
            d.line((pts[i], pts[i + 1]), fill=body, width=wdt)
    # usi
    for sgn in (-1, 1):
        d.polygon([(c + sgn * S * 0.15, S * 0.33), (c + sgn * S * 0.4, S * 0.3), (c + sgn * S * 0.36, S * 0.4), (c + sgn * S * 0.16, S * 0.42)], fill=body)
    # hlava: siroke celo zuzene k cumaku
    d.polygon([(c - S * 0.2, S * 0.28), (c + S * 0.2, S * 0.28), (c + S * 0.22, S * 0.45), (c + S * 0.15, S * 0.72),
               (c + S * 0.13, S * 0.82), (c - S * 0.13, S * 0.82), (c - S * 0.15, S * 0.72), (c - S * 0.22, S * 0.45)], fill=body)
    d.ellipse((c - S * 0.16, S * 0.7, c + S * 0.16, S * 0.88), fill=body)
    # oci, nozdry, kruh
    for sgn in (-1, 1):
        d.ellipse((c + sgn * S * 0.12 - S * 0.03, S * 0.45 - S * 0.02, c + sgn * S * 0.12 + S * 0.03, S * 0.45 + S * 0.02), fill=gold)
        d.ellipse((c + sgn * S * 0.07 - S * 0.022, S * 0.79 - S * 0.018, c + sgn * S * 0.07 + S * 0.022, S * 0.79 + S * 0.018), fill=gold)
    d.ellipse((c - S * 0.075, S * 0.8, c + S * 0.075, S * 0.95), outline=gold, width=int(S * 0.025))
    return im.resize((size, size), Image.LANCZOS)


def _star8(col, size):
    """Osmicipa hvezda (Sternberkove)."""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(16):
        a = math.radians(-90 + 22.5 * i)
        r = S * (0.47 if i % 2 == 0 else 0.2)
        pts.append((S / 2 + math.cos(a) * r, S / 2 + math.sin(a) * r))
    d.polygon(pts, fill=(*col, 255), outline=(20, 16, 12, 255), width=S // 90)
    return im.resize((size, size), Image.LANCZOS)


def tex_shield(name, field, charges, ordinary=None, seed=1, W=1024, H=None, prefix="stit_"):
    """Malovane lice stitu: pole, pripadne brevno, figury (icon, barva, velikost, stred x, y v 0..1),
    tahy stetce, jemne odrene okraje a patina."""
    R = random.Random(seed)
    H = H or W
    im = Image.new("RGBA", (W, H), (*field, 255))
    d = ImageDraw.Draw(im)
    if ordinary:
        kind, col = ordinary
        if kind == "brevno":
            d.rectangle((0, int(H * 0.47), W, int(H * 0.6)), fill=(*col, 255))
            d.line((0, int(H * 0.47), W, int(H * 0.47)), fill=(20, 16, 12, 255), width=5)
            d.line((0, int(H * 0.6), W, int(H * 0.6)), fill=(20, 16, 12, 255), width=5)
        elif kind == "kul":
            d.rectangle((int(W * 0.42), 0, int(W * 0.58), H), fill=(*col, 255))
        elif kind == "polceny":              # heraldicky vlevo (pro divaka vpravo) druha barva
            d.rectangle((W // 2, 0, W, H), fill=(*col, 255))
            d.line((W // 2, 0, W // 2, H), fill=(20, 16, 12, 255), width=5)
        elif kind == "deleny":
            d.rectangle((0, H // 2, W, H), fill=(*col, 255))
            d.line((0, H // 2, W, H // 2), fill=(20, 16, 12, 255), width=5)
        elif kind == "ctvrceny":
            d.rectangle((W // 2, 0, W, H // 2), fill=(*col, 255))
            d.rectangle((0, H // 2, W // 2, H), fill=(*col, 255))
            d.line((W // 2, 0, W // 2, H), fill=(20, 16, 12, 255), width=5)
            d.line((0, H // 2, W, H // 2), fill=(20, 16, 12, 255), width=5)
    for icon, col, sz, cx, cy in charges:
        m_ = min(W, H)
        c = _charge(icon, col, int(m_ * sz))
        im.alpha_composite(c, (int(W * cx - m_ * sz / 2), int(H * cy - m_ * sz / 2)))
    im = im.convert("RGB")
    px = im.load()
    # tahy stetce (svisle pruhy jemne svetlejsi/tmavsi) a zrno barvy
    stroke = [R.uniform(0.95, 1.05) for _ in range(W // 6 + 1)]
    for y in range(H):
        for x in range(W):
            k = stroke[x // 6] * R.uniform(0.96, 1.03)
            r, g, b = px[x, y]
            px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)))
    noise = Image.effect_noise((W // 16, H // 16), 50).resize((W, H), Image.BICUBIC)
    dark = Image.blend(im, Image.new("RGB", (W, H), (60, 50, 35)), 0.12)
    im = Image.composite(dark, im, noise.point(lambda v: 255 if v > 185 else 0).filter(ImageFilter.GaussianBlur(10)))
    return _save(im, prefix + name)


def heraldic_shield(name, design, size=0.62):
    """Gotický stit (heater) jako na fotkach: prohnuta deska (barel), malovane lice s erbem,
    hrana a rub z drevene desky potazene kuzi, zezadu remeny (enarmy) a nosny remen pres rameno."""
    import erby
    k = size / 2.0
    out = erby.outline(48)
    pts = [(x * k, y * k) for x, y in out]
    ys = [p[1] for p in pts]
    xs = [p[0] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    face = _mat(name + "_lic", tex_shield(name, *design), 0.5)
    back = _wood_mat("stit_rub", "tram", (0.42, 0.32, 0.24))
    rim = _plain("stit_hrana", (0.12, 0.07, 0.04), 0.0, 0.6)
    # paprskova sit od stredu k obrysu (heater je hvezdicovy vzhledem k bodu nad stredem)
    cx, cy = 0.0, y0 + (y1 - y0) * 0.6
    rings = 14
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    grid = []
    wmax = max(abs(x) for x in xs)
    for r in range(rings + 1):
        t = r / rings
        row = []
        for (x, y) in pts:
            px_, py_ = cx + (x - cx) * t, cy + (y - cy) * t
            z = 0.07 * (1.0 - (px_ / wmax) ** 2) + 0.02 * (1.0 - ((py_ - cy) / (y1 - y0)) ** 2)   # barel + mirne nahoru/dolu
            row.append(bm.verts.new((px_, py_, z)))
        grid.append(row)
    n = len(pts)
    for r in range(rings):
        for i in range(n):
            j = (i + 1) % n
            if r == 0:
                f = bm.faces.new((grid[0][i], grid[1][i], grid[1][j])) if i < n else None
            else:
                f = bm.faces.new((grid[r][i], grid[r + 1][i], grid[r + 1][j], grid[r][j]))
            for l in f.loops:
                l[uv].uv = ((l.vert.co.x - x0) / (x1 - x0), (l.vert.co.y - y0) / (y1 - y0))
    rim_pts = [tuple(v.co) for v in grid[-1]]
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(face)
    me.materials.append(back)
    me.materials.append(rim)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    so = ob.modifiers.new("t", "SOLIDIFY")
    so.thickness = 0.018
    so.offset = -1.0
    so.material_offset = 1
    so.material_offset_rim = 2
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth()
    # kozeny lem po obvodu (trubka)
    cu = bpy.data.curves.new("lem", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(n - 1)
    for p_, v in zip(sp.points, rim_pts):
        p_.co = (v[0], v[1], v[2] - 0.009, 1)
    sp.use_cyclic_u = True
    cu.bevel_depth = 0.011
    cu.bevel_resolution = 2
    lo = bpy.data.objects.new("lem", cu)
    bpy.context.scene.collection.objects.link(lo)
    lo.data.materials.append(rim)
    # rub: enarmy (dva remeny s prezkami), polstarek, nosny remen
    kuze = _plain("remen", (0.2, 0.11, 0.05), 0.0, 0.7)
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    for yy in (cy - 0.06, cy + 0.1):
        _box((0, yy, -0.012), (0.3, 0.035, 0.008), kuze, bevel=0.002)
        _box((0.1, yy, -0.016), (0.03, 0.04, 0.006), fe, bevel=0.001)
    _box((0, cy + 0.02, -0.02), (0.12, 0.12, 0.02), _plain("polstar_stit", (0.4, 0.3, 0.2), 0.0, 0.9), bevel=0.008)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=(sx * 0.14, cy - 0.06, 0.07 * (1 - (0.14 / wmax) ** 2) + 0.005), segments=8, ring_count=4)
        bpy.context.object.data.materials.append(fe)
    return None


ZLATA, STRIBRO, CERVENA, MODRA, CERNA, ZELENA = (226, 182, 52), (232, 232, 226), (176, 30, 26), (34, 66, 140), (24, 22, 20), (34, 104, 52)
STITY = {
    # erby ceskych panskych rodu (pole, figury, delení)
    "stit_lipa": (ZLATA, [("@ostrve", CERNA, 0.72, 0.5, 0.47)]),                 # pani z Lipe
    "stit_lichtenburk": (CERVENA, [("@ostrve", STRIBRO, 0.72, 0.5, 0.47)]),      # Lichtenburkove
    "stit_rozmberk": (STRIBRO, [("@ruze", CERVENA, 0.62, 0.5, 0.47)]),           # Rozmberkove
    "stit_hradec": (MODRA, [("@ruze", ZLATA, 0.62, 0.5, 0.47)]),                 # pani z Hradce
    "stit_krumlov": (STRIBRO, [("@ruze", ZELENA, 0.62, 0.5, 0.47)]),             # pani z Krumlova
    "stit_sternberk": (MODRA, [("@hvezda", ZLATA, 0.62, 0.5, 0.47)]),            # Sternberkove
    "stit_pernstejn": (ZLATA, [("@zubr", CERNA, 0.7, 0.5, 0.5)]),                # Pernstejnove
    "stit_svamberk": (CERVENA, [("swan", STRIBRO, 0.62, 0.5, 0.5)]),             # Svamberkove
    "stit_michalovic": (CERVENA, [("feathered-wing", STRIBRO, 0.62, 0.5, 0.5)]), # Michalovici
    "stit_vartenberk": (ZLATA, [], ("polceny", CERNA)),                          # Vartenberkove
    "stit_kolovrat": (CERVENA, [], ("deleny", STRIBRO)),                         # Kolovratove
    "stit_lobkovic": (STRIBRO, [], ("ctvrceny", CERVENA)),                       # Lobkovicove
}


def pavise(name):
    """Pavéza (velky cesky stit pro kusnickare): obdelnik se zuzenim dolu, svisly zlab uprostred,
    malovany erb (lev) na barevnem poli s okrajem."""
    W, H = 0.62, 1.2
    # textura: pole, dvojity okraj, erb uprostred
    im = Image.new("RGBA", (512, 1024), (150, 30, 24, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 511, 1023), outline=(210, 170, 80, 255), width=26)
    d.rectangle((40, 40, 471, 983), outline=(40, 40, 60, 255), width=10)
    for y in range(80, 980, 90):
        d.line((60, y, 451, y + 45), fill=(170, 40, 30, 255), width=6)
    e = Image.open(os.path.join(ERBY, "vse.png")).convert("RGBA").resize((380, 380))
    im.alpha_composite(e, (66, 300))
    px = im.load()
    R = random.Random(31)
    for y in range(0, 1024, 2):
        for x in range(0, 512, 2):
            if R.random() < 0.25:
                r, g, b, a = px[x, y]
                f = R.uniform(0.78, 0.95)
                px[x, y] = (int(r * f), int(g * f), int(b * f), a)
    p = _save(im.convert("RGB"), "paveza")
    face = _mat(name + "_lic", p, 0.7)
    wood = _wood_mat("stit_drevo", "tram", (0.55, 0.42, 0.3))
    # deska s pricnym profilem: ploche kridla, uprostred zlab (hrbet) a mirne prohnuti; dole se zuzuje
    nx, ny = 40, 30
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")

    def prof(u):                      # u -1..1 pres sirku -> vyska licni plochy
        ridge = 0.028 * max(0.0, 1.0 - abs(u) / 0.3) ** 1.2
        return 0.05 * (1.0 - u * u) + ridge
    top, bot = [], []
    for j in range(ny + 1):
        t = j / ny
        y = -H / 2 + H * t
        wj = W / 2 * (0.9 + 0.1 * t)
        rt, rb = [], []
        for i in range(nx + 1):
            u = -1 + 2 * i / nx
            z = prof(u)
            rt.append(bm.verts.new((u * wj, y, z + 0.035)))
            rb.append(bm.verts.new((u * wj, y, z)))
        top.append(rt)
        bot.append(rb)
    faces = []
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
            f.material_index = 0
            for l in f.loops:
                l[uv].uv = ((l.vert.co.x + W / 2) / W, (l.vert.co.y + H / 2) / H)
            g = bm.faces.new((bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1]))
            g.material_index = 1
    for j in range(ny):
        for i in (0, nx):
            f = bm.faces.new((bot[j][i], top[j][i], top[j + 1][i], bot[j + 1][i]) if i == 0 else (bot[j][i], bot[j + 1][i], top[j + 1][i], top[j][i]))
            f.material_index = 1
    for j in (0, ny):
        for i in range(nx):
            f = bm.faces.new((bot[j][i], bot[j][i + 1], top[j][i + 1], top[j][i]) if j == 0 else (bot[j][i], top[j][i], top[j][i + 1], bot[j][i + 1]))
            f.material_index = 1
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(face)
    me.materials.append(wood)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth()
    # kovane pasy na hornim a dolnim okraji, nyty, zezadu podpera a remen
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    for yy in (H / 2 - 0.015, -H / 2 + 0.015):
        _box((0, yy, 0.06), (W * 0.95, 0.02, 0.012), fe, bevel=0.002)
        for k in range(7):
            x = -W * 0.42 + W * 0.84 * k / 6
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.007, location=(x, yy, 0.068 + 0.05 * (1 - (x / (W / 2)) ** 2) * 0.9), segments=8, ring_count=4)
            bpy.context.object.data.materials.append(fe)
    _box((0, 0, -0.012), (0.05, H * 0.8, 0.02), wood, bevel=0.003)
    _box((0, 0.1, -0.03), (0.3, 0.04, 0.012), _plain("remen", (0.18, 0.1, 0.05), 0.0, 0.7), bevel=0.002)
    return None


def buckler(name):
    """Puklíř: maly kulaty pestni stit, kovany s vypouklou puklici a nyty po okraji."""
    st = _plain("puklir_ocel", (0.5, 0.5, 0.52), 0.9, 0.35)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=16, radius=1.0)
    o = bpy.context.object
    for v in o.data.vertices:
        z = max(0.0, v.co.z)
        v.co = Vector((v.co.x * 0.17, v.co.y * 0.17, z * 0.035))
    o.data.materials.append(st)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=10, radius=0.06, location=(0, 0, 0.03))
    o = bpy.context.object
    o.scale = (1, 1, 0.6)
    o.data.materials.append(st)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.165, minor_radius=0.008, location=(0, 0, 0.004))
    bpy.context.object.data.materials.append(st)
    for i in range(16):
        a = 2 * math.pi * i / 16
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=(math.cos(a) * 0.14, math.sin(a) * 0.14, 0.018), segments=8, ring_count=4)
        bpy.context.object.data.materials.append(st)
    return None


def tex_tapestry(name, field, border, accent, erb, seed, W=768, H=1152):
    """Tapiserie: tkane pole s kosoctverecnym vzorem a liliemi, siroky okraj s kruznicemi, uprostred erb."""
    R = random.Random(seed)
    im = Image.new("RGBA", (W, H), (*border, 255))
    d = ImageDraw.Draw(im)
    b = 70
    d.rectangle((b, b, W - b, H - b), fill=(*field, 255))
    # diagonalni mrizka s body v poli
    s = 64
    for i in range(-H // s, W // s + H // s):
        d.line((b + i * s, b, b + i * s + H, b + H), fill=(*[int(c * 0.82) for c in field], 255), width=3)
        d.line((b + i * s, b, b + i * s - H, b + H), fill=(*[int(c * 0.82) for c in field], 255), width=3)
    for y in range(b + s // 2, H - b, s):
        for x in range(b + s // 2, W - b, s):
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(*accent, 255))
    d.rectangle((b, b, W - b, H - b), outline=(*accent, 255), width=8)
    # okraj: kruznice
    for x in range(b // 2, W, 56):
        for y in (b // 2, H - b // 2):
            d.ellipse((x - 18, y - 18, x + 18, y + 18), outline=(*accent, 255), width=5)
    for y in range(b // 2, H, 56):
        for x in (b // 2, W - b // 2):
            d.ellipse((x - 18, y - 18, x + 18, y + 18), outline=(*accent, 255), width=5)
    e = Image.open(erb if os.path.isabs(erb) else os.path.join(ERBY, erb + ".png")).convert("RGBA").resize((420, 420))
    im.alpha_composite(e, ((W - 420) // 2, (H - 420) // 2 - 40))
    im = im.convert("RGB")
    px = im.load()
    for y in range(H):
        for x in range(W):
            k = 0.88 if (x % 3 == 0) or (y % 4 == 0) else 1.0
            k *= R.uniform(0.93, 1.03)
            r, g, bb = px[x, y]
            px[x, y] = (int(r * k), int(g * k), int(bb * k))
    im = im.filter(ImageFilter.GaussianBlur(0.5))
    return _save(im, "tapiserie_" + name)


def tapestry(name, w, h, cols, erb, seed):
    """Tapiserie na zed: latka s jemnymi svislymi zvlny (lici do -Y = od zdi), nahore dubova tyc
    s hlavicemi a kovanymi drzaky, dole strapce."""
    m = _mat(name, tex_tapestry(name, *cols, erb, seed), 0.95)
    nx, nz = 24, 30
    bm = bmesh.new()
    vs = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            x = -w / 2 + w * i / nx
            z = h * j / nz
            y = -0.02 - 0.012 * math.sin(i / nx * math.pi * 5) * (0.4 + 0.6 * (1 - j / nz))
            row.append(bm.verts.new((x, y, z)))
        vs.append(row)
    uv = bm.loops.layers.uv.new("UVMap")
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            for l in f.loops:
                l[uv].uv = ((l.vert.co.x + w / 2) / w, l.vert.co.z / h)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    sol = ob.modifiers.new("t", "SOLIDIFY")
    sol.thickness = 0.008
    dub = _wood_mat("dub_tyc", "tram", (0.4, 0.28, 0.18))
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.022, depth=w + 0.16, location=(0, -0.045, h + 0.01), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(dub)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(sx * (w / 2 + 0.1), -0.045, h + 0.01), segments=10, ring_count=6)
        bpy.context.object.data.materials.append(dub)
        _box((sx * (w / 2 - 0.05), -0.025, h + 0.03), (0.02, 0.05, 0.06), fe, bevel=0.002)
    # strapce
    tm = _plain(name + "_strapce", tuple(c / 255 * 0.9 for c in cols[2]), 0.0, 0.8)
    for k in range(int(w / 0.06)):
        x = -w / 2 + 0.03 + k * 0.06
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.012, depth=0.07, location=(x, -0.02, -0.03))
        bpy.context.object.data.materials.append(tm)
    return None


def longsword(name):
    """Dlouhy mec (bastard): cepel s kosoctverecnym prurezem a zlabkem, rovna zastita, kozena rukojet, hruska."""
    st = _plain("ocel_cepel", (0.62, 0.63, 0.66), 0.95, 0.22)
    fe = _plain("ocel_tmava", (0.2, 0.2, 0.21), 0.9, 0.4)
    kuze = _plain("kuze_rukojet", (0.16, 0.08, 0.04), 0.0, 0.65)
    L = 0.92
    bm = bmesh.new()
    prof = []
    for i in range(13):
        t = i / 12
        wdt = 0.026 * (1 - t) + 0.006 * t
        if i == 12:
            wdt = 0.0005
        prof.append((t * L, wdt))
    rows = []
    for x, wdt in prof:
        rows.append([bm.verts.new((x, -wdt, 0.0)), bm.verts.new((x, 0.0, 0.0045)), bm.verts.new((x, wdt, 0.0)), bm.verts.new((x, 0.0, -0.0045))])
    for a, b in zip(rows, rows[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(list(reversed(rows[0])))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(st)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    _box((-0.01, 0, 0), (0.025, 0.24, 0.022), fe, bevel=0.004)                         # zastita
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.014, location=(-0.01, sy * 0.12, 0), segments=8, ring_count=5)
        bpy.context.object.data.materials.append(fe)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.016, depth=0.22, location=(-0.135, 0, 0), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(kuze)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.032, depth=0.022, location=(-0.26, 0, 0), rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(fe)
    return None


def polearm(name, kind="halapartna"):
    """Halapartna (sekera, hak a bodec na jasanove tyci) nebo kopi s listovym hrotem; lezi na zemi."""
    dub = _wood_mat("jasan_tyc", "tram", (0.75, 0.6, 0.45))
    st = _plain("ocel_tmava", (0.3, 0.3, 0.31), 0.9, 0.35)
    L = 2.0
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.017, depth=L, location=(L / 2, 0, 0.017), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(dub)
    if kind == "kopi":
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.035, depth=0.3, location=(L + 0.15, 0, 0.017), rotation=(0, math.pi / 2, 0))
        o = bpy.context.object
        o.scale = (0.25, 1, 1)
        o.data.materials.append(st)
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.02, depth=0.1, location=(L - 0.02, 0, 0.017), rotation=(0, math.pi / 2, 0))
        bpy.context.object.data.materials.append(st)
        return None
    # sekera (pulmesic s vypouklym ostrim), hak na druhe strane: zkosene hrany (ostri tenci nez hrbet)
    def blade(pts, t_back, t_edge, edge_idx):
        bm = bmesh.new()
        top, bot = [], []
        for k, (x, y) in enumerate(pts):
            t = t_edge if k in edge_idx else t_back
            top.append(bm.verts.new((x, y, 0.017 + t)))
            bot.append(bm.verts.new((x, y, 0.017 - t)))
        bm.faces.new(top)
        bm.faces.new(list(reversed(bot)))
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new((bot[i], bot[j], top[j], top[i]))
        me = bpy.data.meshes.new(name + "_cepel")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(st)
        o = bpy.data.objects.new(name + "_cepel", me)
        bpy.context.scene.collection.objects.link(o)
        m = o.modifiers.new("b", "BEVEL")
        m.width = 0.002
        m.segments = 2
    axe = [(L - 0.24, 0.02)]
    for i in range(13):
        a = math.radians(-70 + 140 * i / 12)
        axe.append((L - 0.06 + math.sin(a) * 0.17, 0.2 + math.cos(a) * 0.07 - 0.07 + 0.07 * math.cos(a)))
    axe += [(L + 0.08, 0.02)]
    blade(axe, 0.008, 0.0012, list(range(1, 14)))
    hook = [(L - 0.1, -0.02), (L - 0.13, -0.08), (L - 0.07, -0.19), (L - 0.04, -0.21), (L - 0.05, -0.12), (L - 0.0, -0.02)]
    blade(hook, 0.007, 0.0015, [2, 3])
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.022, depth=0.38, location=(L + 0.17, 0, 0.017), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(st)
    # objimka, langety podel tyce a nyty
    _box((L - 0.04, 0, 0.017), (0.34, 0.046, 0.046), st, bevel=0.004)
    for sy in (-1, 1):
        _box((L - 0.38, sy * 0.019, 0.017), (0.42, 0.006, 0.022), st, bevel=0.001)
        for xx in (L - 0.52, L - 0.36, L - 0.2):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=(xx, sy * 0.022, 0.017), segments=8, ring_count=4)
            bpy.context.object.data.materials.append(st)
    # kozena omotavka v miste uchopu
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.02, depth=0.25, location=(0.9, 0, 0.017), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(_plain("kuze_rukojet", (0.16, 0.08, 0.04), 0.0, 0.65))
    return None


def weapon_hook(name):
    """Hak na zbrane: dubova lista na zed s kovanymi hacky (zbran nebo stit se na nej povesi);
    zed je rovina y = 0, lista vycniva do -y."""
    dub = _wood_mat("dub_lista", "tram", (0.45, 0.32, 0.2))
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    _box((0, -0.02, 0.06), (0.5, 0.04, 0.12), dub, bevel=0.006)
    # zkosene hrany listy a vyrezavany okraj
    _box((0, -0.042, 0.125), (0.52, 0.03, 0.015), dub, bevel=0.004)
    for sx in (-1, 1):
        x = sx * 0.16
        # hacek: kovana tyc od listy ven a nahoru, zakonceny spirálkou
        cu = bpy.data.curves.new("hacek", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for bp, co in zip(sp.bezier_points, [(x, -0.04, 0.05), (x, -0.1, 0.05), (x, -0.12, 0.11)]):
            bp.co = co
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cu.bevel_depth = 0.007
        cu.bevel_resolution = 3
        ob = bpy.data.objects.new("hacek", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(fe)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.012, minor_radius=0.004, location=(x, -0.115, 0.118), rotation=(0, math.pi / 2, 0))
        bpy.context.object.data.materials.append(fe)
        _box((x, -0.042, 0.05), (0.04, 0.006, 0.05), fe, bevel=0.002)
        for zz in (0.035, 0.065):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.007, location=(x, -0.046, zz), segments=8, ring_count=4)
            bpy.context.object.data.materials.append(fe)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.01, location=(sx * 0.23, -0.042, 0.06), segments=8, ring_count=4)
        bpy.context.object.data.materials.append(fe)
    return None


BUILD.update({k: (lambda k=k: heraldic_shield(k, (STITY[k][0], STITY[k][1], STITY[k][2] if len(STITY[k]) > 2 else None, len(k))))
              for k in STITY})
BUILD.update({
    "paveza": lambda: pavise("paveza"),
    "puklir": lambda: buckler("puklir"),
    "koberec_zeleny": lambda: rug("koberec_zeleny", 1.4, 2.0, ((34, 74, 46), (120, 30, 24), (214, 180, 100)), 13),
    "koberec_velky": lambda: rug("koberec_velky", 2.4, 3.4, ((110, 28, 22), (40, 34, 30), (220, 180, 90)), 14),
    "behoun": lambda: rug("behoun", 0.8, 3.0, ((60, 40, 90), (130, 30, 26), (214, 170, 80)), 15),
    "mec_dlouhy": lambda: longsword("mec_dlouhy"),
    "halapartna": lambda: polearm("halapartna"),
    "kopi": lambda: polearm("kopi", "kopi"),
    "hak_zbrane": lambda: weapon_hook("hak_zbrane"),
})


def weapon_rack(name):
    """Stojan na zbrane do zbrojnice: dve svisle bocnice na patkach se soustruzenymi hlavicemi, dole tram
    s kovanymi kruhy pro paty zbrani, nahore tram se sesti vyrezy obloženými kuzi a kovanymi koliky mezi nimi,
    vzadu sikme vzpery a stredni latka."""
    dub = _wood_mat("dub_stojan", "tram", (0.5, 0.36, 0.24))
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    kuze = _plain("remen", (0.2, 0.11, 0.05), 0.0, 0.7)
    W = 1.5
    for sx in (-1, 1):
        x = sx * W / 2
        _box((x, 0.05, 0.05), (0.12, 0.6, 0.1), dub, bevel=0.012)
        _box((x, 0.0, 0.75), (0.09, 0.09, 1.4), dub, bevel=0.01)
        _turned((x, 0.0, 1.45), [(0.0, 0.0), (0.05, 0.0), (0.055, 0.03), (0.035, 0.06), (0.05, 0.1), (0.03, 0.15), (0.0, 0.17)], dub, 12)
        for zz in (0.12, 1.3):
            _box((x, -0.046, zz), (0.1, 0.006, 0.04), fe, bevel=0.001)
    _box((0, 0.0, 0.2), (W, 0.2, 0.07), dub, bevel=0.01)
    _box((0, 0.0, 1.27), (W, 0.14, 0.09), dub, bevel=0.01)
    _box((0, 0.05, 0.75), (W, 0.05, 0.06), dub, bevel=0.006)
    for i in range(6):
        x = -0.55 + 0.22 * i
        bpy.ops.mesh.primitive_torus_add(major_radius=0.04, minor_radius=0.007, location=(x, -0.02, 0.24))
        bpy.context.object.data.materials.append(fe)
        _box((x, -0.075, 1.27), (0.07, 0.012, 0.07), kuze, bevel=0.002)
        if i < 5:
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.009, depth=0.1, location=(x + 0.11, -0.11, 1.29), rotation=(math.pi / 2, 0, 0))
            bpy.context.object.data.materials.append(fe)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.014, location=(x + 0.11, -0.16, 1.29), segments=8, ring_count=5)
            bpy.context.object.data.materials.append(fe)
    return None


def torch_stand(name):
    """Kovany stojan na louc: trojnozka s volutami, kroucena tyc ze tri drátu, uzel a kalich s ozdobnym okrajem."""
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.5)
    H = 1.3
    for k in range(3):
        a = 2 * math.pi * k / 3
        cu = bpy.data.curves.new("noha", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(3)
        pts = [(0, 0, 0.32), (math.cos(a) * 0.16, math.sin(a) * 0.16, 0.12), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.015),
               (math.cos(a) * 0.36, math.sin(a) * 0.36, 0.05)]
        for bp, co in zip(sp.bezier_points, pts):
            bp.co = co
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cu.bevel_depth = 0.012
        cu.bevel_resolution = 3
        ob = bpy.data.objects.new("noha", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(fe)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.025, minor_radius=0.007, location=(math.cos(a) * 0.36, math.sin(a) * 0.36, 0.075),
                                         rotation=(math.pi / 2, 0, a + math.pi / 2))
        bpy.context.object.data.materials.append(fe)
    # kroucena tyc: tri drata ve sroubovici
    for k in range(3):
        cu = bpy.data.curves.new("drat", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        n = 60
        sp.points.add(n - 1)
        for i, p_ in enumerate(sp.points):
            t = i / (n - 1)
            z = 0.3 + (H - 0.42) * t
            a = 2 * math.pi * k / 3 + t * 2 * math.pi * 7
            p_.co = (math.cos(a) * 0.011, math.sin(a) * 0.011, z, 1)
        cu.bevel_depth = 0.008
        cu.bevel_resolution = 2
        ob = bpy.data.objects.new("drat", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(fe)
    for zz in (0.3, 0.75):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(0, 0, zz), segments=12, ring_count=8)
        bpy.context.object.data.materials.append(fe)
    # kalich: soustruzeny profil s rozevrenym zubatym okrajem
    _turned((0, 0, H - 0.13), [(0.0, 0.0), (0.03, 0.0), (0.045, 0.04), (0.05, 0.09), (0.075, 0.13), (0.08, 0.14), (0.068, 0.14), (0.04, 0.1),
                              (0.0, 0.1)], fe, 16)
    for i in range(8):
        a = 2 * math.pi * i / 8
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.012, depth=0.04, location=(math.cos(a) * 0.075, math.sin(a) * 0.075, H + 0.03))
        bpy.context.object.data.materials.append(fe)
    return None


BUILD.update({
    "stojan_zbrani": lambda: weapon_rack("stojan_zbrani"),
    "stojan_louce": lambda: torch_stand("stojan_louce"),
})


# ======================================================================= prapory, vlajky a rodove tapiserie

def _arms_tex(rod, W, H, prefix):
    f = STITY[rod]
    return tex_shield(rod, f[0], f[1], f[2] if len(f) > 2 else None, len(rod) + W, W=W, H=H, prefix=prefix)


def _shield_png(rod):
    """Erb ve tvaru stitu s pruhlednym okolim (do stredu tapiserie)."""
    import erby
    src = Image.open(_arms_tex(rod, 512, 512, "erb_")).convert("RGBA")
    mask = Image.new("L", (512, 512), 0)
    out = erby.outline(48)
    ys = [y for _, y in out]
    y0, y1 = min(ys), max(ys)
    pts = [((x + 1) / 2 * 500 + 6, (y1 - y) / (y1 - y0) * 500 + 6) for x, y in out]
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    src.putalpha(mask)
    ImageDraw.Draw(src).line(pts + [pts[0]], fill=(214, 170, 80, 255), width=10)
    return _save(src, "erb_stit_" + rod)


def _grid_cloth(name, mat, nx, nz, point, thick):
    """Latka z mrizky: point(u, v) -> poloha (u pres sirku, v shora dolu), UV podle u, v."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = [[bm.verts.new(point(i / nx, j / nz)) for i in range(nx + 1)] for j in range(nz + 1)]
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]))
            for l, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                l[uv].uv = (ii / nx, 1.0 - jj / nz)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    so = ob.modifiers.new("t", "SOLIDIFY")
    so.thickness = thick
    return ob


def banner(name, rod, w=0.7, h=1.5):
    """Rodovy prapor na zed: erb pres celou latku, dole tri cipy, mekke svisle zvlneni,
    nahore dubova tyc se zlatymi hlavicemi a snury se strapci."""
    m = _mat(name, _arms_tex(rod, 512, 1024, "prapor_"), 0.85)
    tail = 0.22

    def pt(u, v):
        tri = abs(((u * 3) % 1.0) - 0.5) * 2
        zb = tail * (1 - tri)
        z = h - (h - zb) * v
        return (-w / 2 + w * u, -0.015 - 0.012 * math.sin(u * math.pi * 4) * v, z)
    _grid_cloth(name, m, 18, 32, pt, 0.006)
    dub = _wood_mat("dub_tyc", "tram", (0.4, 0.28, 0.18))
    gold = _plain("zlato_strapec", (0.85, 0.62, 0.2), 0.6, 0.4)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.018, depth=w + 0.14, location=(0, -0.03, h + 0.01), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(dub)
    for sx in (-1, 1):
        _turned((sx * (w / 2 + 0.07), -0.03, h - 0.025), [(0.0, 0.0), (0.02, 0.0), (0.03, 0.02), (0.02, 0.045), (0.0, 0.06)], gold, 10)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.004, depth=0.3, location=(sx * (w / 2 + 0.04), -0.035, h - 0.15))
        bpy.context.object.data.materials.append(gold)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.022, radius2=0.006, depth=0.08, location=(sx * (w / 2 + 0.04), -0.035, h - 0.33))
        bpy.context.object.data.materials.append(gold)
    return None


def wall_flag(name, rod, w=0.95, h=0.65):
    """Vlajka na sikme zerdi z kovaneho drzaku na zdi: zerd 45 stupnu ven a nahoru, latka uchycena podel
    zerdi u hrotu, visi a vlni se; na hrotu kovana spice."""
    m = _mat(name, _arms_tex(rod, 768, 512, "vlajka_"), 0.85)
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    dub = _wood_mat("dub_tyc", "tram", (0.4, 0.28, 0.18))
    d = Vector((0.0, -0.7071, 0.7071))
    L = 1.7
    base = Vector((0.0, -0.06, 0.0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.02, depth=L, location=base + d * (L / 2), rotation=(math.radians(45), 0, 0))
    bpy.context.object.data.materials.append(dub)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.03, depth=0.14, location=base + d * (L + 0.07), rotation=(math.radians(45), 0, 0))
    bpy.context.object.data.materials.append(fe)
    _box((0, -0.006, 0.1), (0.1, 0.012, 0.32), fe, bevel=0.002)
    for t in (0.05, 0.3):
        p_ = base + d * t
        bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.007, location=p_, rotation=(math.radians(45), 0, 0))
        bpy.context.object.data.materials.append(fe)
    _box((0, -0.1, 0.13), (0.014, 0.2, 0.014), fe, bevel=0.002)
    a0 = base + d * (L - 0.1 - w)

    def pt(u, v):
        top = a0 + d * (w * u)
        sag = 0.08 * math.sin(u * math.pi) * v
        wave = 0.035 * math.sin(u * math.pi * 3 + v * 2) * v
        return tuple(top + Vector((wave, -0.02 * v, -h * v - sag)))
    _grid_cloth(name, m, 24, 16, pt, 0.005)
    return None


RODY = {"lipa": "pánů z Lipé", "lichtenburk": "Lichtenburků", "rozmberk": "Rožmberků", "hradec": "pánů z Hradce", "krumlov": "pánů z Krumlova",
        "sternberk": "Šternberků", "pernstejn": "Pernštejnů", "svamberk": "Švamberků", "michalovic": "Michaloviců",
        "vartenberk": "Vartenberků", "kolovrat": "Kolovratů", "lobkovic": "Lobkoviců"}
TAPISERIE = {"rozmberk": ((120, 24, 20), (30, 38, 80), (214, 170, 80)), "hradec": ((32, 46, 104), (150, 120, 60), (230, 210, 150)),
             "sternberk": ((28, 72, 40), (90, 24, 20), (220, 190, 110)), "lipa": ((70, 20, 70), (30, 30, 30), (214, 170, 80)),
             "pernstejn": ((90, 22, 18), (40, 34, 30), (226, 182, 52)), "svamberk": ((34, 54, 96), (120, 30, 26), (220, 200, 150))}
for _r in RODY:
    BUILD["prapor_" + _r] = (lambda r=_r: banner("prapor_" + r, "stit_" + r))
    BUILD["vlajka_" + _r] = (lambda r=_r: wall_flag("vlajka_" + r, "stit_" + r))
for _r, _c in TAPISERIE.items():
    BUILD["tapiserie_" + _r] = (lambda r=_r, c=_c: tapestry("tapiserie_" + r, 1.3, 1.9, c, _shield_png("stit_" + r), len(r) + 40))


# ======================================================================= naradi 13.-14. stoleti, slama a drevo
# Vsechno lezi na zemi (nebo stoji), delka podel X. Drevo: jasan/buk (svetly), dub (tmavsi), kovane casti.

def _tex_bark(name, base, seed):
    """Kura: svisle brazdy, tmavsi praskliny, sem tam lisejnik."""
    R = random.Random(seed)
    W, H = 512, 1024
    im = Image.new("RGB", (W, H), base)
    d = ImageDraw.Draw(im)
    for _ in range(420):
        x = R.uniform(0, W)
        y = R.uniform(0, H)
        L = R.uniform(40, 200)
        col = tuple(int(c * R.uniform(0.45, 0.75)) for c in base)
        d.line((x, y, x + R.uniform(-8, 8), y + L), fill=col, width=R.randint(2, 5))
    for _ in range(60):
        x, y = R.uniform(0, W), R.uniform(0, H)
        r = R.uniform(4, 14)
        d.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=(96, 100, 74))
    return _save(im.filter(ImageFilter.GaussianBlur(0.8)), name)


def _tex_endgrain(name, seed):
    """Rez kmenem: letokruhy, praskliny od stredu."""
    R = random.Random(seed)
    W = 256
    im = Image.new("RGB", (W, W), (196, 160, 112))
    d = ImageDraw.Draw(im)
    for k in range(40, 0, -1):
        r = W / 2 * k / 40
        c = (int(196 - k * 1.2), int(160 - k * 1.3), int(112 - k * 1.1)) if k % 2 else (176, 136, 92)
        d.ellipse((W / 2 - r, W / 2 - r * 0.97, W / 2 + r, W / 2 + r * 0.97), fill=c)
    for _ in range(5):
        a = R.uniform(0, 2 * math.pi)
        d.line((W / 2, W / 2, W / 2 + math.cos(a) * W * 0.45, W / 2 + math.sin(a) * W * 0.45), fill=(90, 60, 36), width=2)
    return _save(im, name)


def _log(c, length, r, axis, bark, end, rot=0.0, split=0):
    """Poleno: valec s kurou a rezy na koncich; split = pulene/ctvrcene (rez rovne)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=length, location=c)
    o = bpy.context.object
    if axis == "x":
        o.rotation_euler = (0, math.pi / 2, rot)
    elif axis == "y":
        o.rotation_euler = (math.pi / 2, 0, rot)
    o.data.materials.append(bark)
    o.data.materials.append(end)
    for poly in o.data.polygons:
        if abs(poly.normal.z) > 0.9:
            poly.material_index = 1
    if split:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        for v in bm.verts:
            if split == 1 and v.co.y > r * 0.15:
                v.co.y = r * 0.15
        bm.to_mesh(o.data)
        bm.free()
    return o


def _handle(a, b, r, mat, r1=None, seg=10):
    """Rukojet / topurko mezi body a, b (Blender souradnice)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=r, radius2=r1 if r1 is not None else r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    return o


def _woods():
    jasan = _wood_mat("jasan_naradi", "tram", (0.95, 0.8, 0.62))
    dub = _wood_mat("dub_naradi", "tram", (0.55, 0.4, 0.28))
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.55)
    ocel = _plain("ocel_naradi", (0.32, 0.31, 0.3), 0.9, 0.38)
    provaz = _plain("provaz", (0.55, 0.45, 0.3), 0.0, 0.9)
    return jasan, dub, fe, ocel, provaz


def broom(name):
    """Brezova metla: jasanova hul, svazek brezovych prutu (stovky prutku s vetvickami) stazeny dvema vazbami z vrbovych prutu."""
    jasan, dub, fe, ocel, provaz = _woods()
    pruty = _plain("brezove_pruty", (0.28, 0.17, 0.1), 0.0, 0.8)
    R = random.Random(7)
    _handle((0, 0, 0.04), (1.05, 0, 0.04), 0.017, jasan)
    for k in range(320):
        a = R.uniform(0, 2 * math.pi)
        rr = math.sqrt(R.random()) * 0.045
        y0, z0 = math.cos(a) * rr, 0.045 + math.sin(a) * rr * 0.8
        L = R.uniform(0.45, 0.6)
        spread = rr / 0.045 * 0.09
        _handle((0.12, y0 * 0.6, z0), (0.12 - L, y0 + math.cos(a) * spread, max(0.004, z0 + math.sin(a) * spread * 0.6)), 0.003, pruty, 0.0012, 4)
    for xx in (0.05, -0.05):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.007, location=(xx, 0, 0.045), rotation=(0, math.pi / 2, 0))
        bpy.context.object.data.materials.append(provaz)
    return None


def pitchfork(name, prongs=3, wooden=True):
    """Vidle: dreveny troj- nebo dvojzub z jedne rozvetvene vetve (celodrevene, jak se delaly), nebo kovane dvojzube."""
    jasan, dub, fe, ocel, provaz = _woods()
    _handle((0, 0, 0.02), (1.35, 0, 0.02), 0.017, jasan)
    mat = jasan if wooden else fe
    for k in range(prongs):
        y = (k - (prongs - 1) / 2) * 0.07
        cu = bpy.data.curves.new("zub", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for bp, co in zip(sp.bezier_points, [(1.3, 0, 0.02), (1.45, y * 0.8, 0.025), (1.75, y, 0.06)]):
            bp.co = co
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cu.bevel_depth = 0.011 if wooden else 0.007
        cu.bevel_resolution = 2
        cu.taper_object = None
        ob = bpy.data.objects.new("zub", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(mat)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.021, minor_radius=0.005, location=(1.29, 0, 0.02), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(fe if not wooden else provaz)
    return None


def rake(name):
    """Hrabe: jasanova hul, bukovy hrebinek se dvanacti zuby a dve vzpery (rozsoch) do hrebinku."""
    jasan, dub, fe, ocel, provaz = _woods()
    _handle((0, 0, 0.03), (1.6, 0, 0.03), 0.016, jasan)
    _box((1.62, 0, 0.03), (0.05, 0.58, 0.045), dub, bevel=0.006)
    for k in range(12):
        y = -0.26 + k * 0.0473
        _handle((1.62, y, 0.03), (1.62, y, -0.07 + 0.1), 0.006, jasan, 0.004, 6).location = (1.62, y, -0.015)
    for sy in (-1, 1):
        _handle((1.3, 0, 0.03), (1.6, sy * 0.18, 0.03), 0.008, jasan)
    return None


def scythe(name):
    """Kosa: zahnute kosiste s dvema rucickami (horni a dolni), kovana cepel s hrbetem a ostrim, objimka s klinem."""
    jasan, dub, fe, ocel, provaz = _woods()
    cu = bpy.data.curves.new("kosiste", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(0, 0, 0.025), (0.8, 0.08, 0.025), (1.6, 0.0, 0.025)]):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.018
    cu.bevel_resolution = 2
    ob = bpy.data.objects.new("kosiste", cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(jasan)
    for x, ln in ((0.55, 0.16), (1.05, 0.14)):
        _handle((x, 0.06, 0.025), (x + 0.02, 0.06 + ln, 0.025), 0.014, jasan, 0.012)
    # cepel: plochy oblouk (hrbet tlustsi), zuzeny ke spicce
    bm = bmesh.new()
    n = 24
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        a = math.radians(-8 + 70 * t)
        rr = 0.75
        cx, cy = 1.6 - math.sin(a) * rr * 0.2, -math.cos(a) * 0.0 - t * 0.78
        wd = 0.075 * (1 - t) + 0.006
        for lst, z in ((top, 0.03), (bot, 0.022)):
            pass
        top.append((bm.verts.new((cx - 0.02 * t, cy, 0.03)), bm.verts.new((cx - 0.02 * t + wd, cy - 0.01, 0.026))))
        bot.append((bm.verts.new((cx - 0.02 * t, cy, 0.021)), bm.verts.new((cx - 0.02 * t + wd, cy - 0.01, 0.025))))
    for i in range(n):
        bm.faces.new((top[i][0], top[i][1], top[i + 1][1], top[i + 1][0]))
        bm.faces.new((bot[i][0], bot[i + 1][0], bot[i + 1][1], bot[i][1]))
        bm.faces.new((top[i][0], top[i + 1][0], bot[i + 1][0], bot[i][0]))
        bm.faces.new((top[i][1], bot[i][1], bot[i + 1][1], top[i + 1][1]))
    me = bpy.data.meshes.new("cepel")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ocel)
    o = bpy.data.objects.new("cepel", me)
    bpy.context.scene.collection.objects.link(o)
    _box((1.6, 0.0, 0.025), (0.06, 0.05, 0.05), fe, bevel=0.004)
    return None


def sickle(name):
    """Srp: zubata cepel do pulkruhu na bukove rukojeti s kovanou objimkou."""
    jasan, dub, fe, ocel, provaz = _woods()
    _handle((0, 0, 0.015), (0.13, 0, 0.015), 0.016, dub, 0.014)
    _box((0.14, 0, 0.015), (0.02, 0.026, 0.026), fe, bevel=0.002)
    bm = bmesh.new()
    n = 30
    rings = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(180 - 250 * t)
        R1, R2 = 0.15, 0.15 - 0.03 * (1 - t) - 0.004
        cx, cy = 0.305, 0.0
        o_ = bm.verts.new((cx + math.cos(a) * R1, cy + math.sin(a) * R1, 0.015))
        # zoubky na vnitrnim ostri
        z = 0.004 if i % 2 else 0.0
        i_ = bm.verts.new((cx + math.cos(a) * (R2 - z), cy + math.sin(a) * (R2 - z), 0.015))
        rings.append((o_, i_))
    for i in range(n):
        bm.faces.new((rings[i][0], rings[i][1], rings[i + 1][1], rings[i + 1][0]))
    me = bpy.data.meshes.new("srp")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ocel)
    o = bpy.data.objects.new("srp", me)
    bpy.context.scene.collection.objects.link(o)
    so = o.modifiers.new("t", "SOLIDIFY")
    so.thickness = 0.003
    return None


def flail(name):
    """Cep: dlouha jasanova nasada a kratsi bukovy tlouk spojeny kozenym kloubem (gouz)."""
    jasan, dub, fe, ocel, provaz = _woods()
    kuze = _plain("remen", (0.2, 0.11, 0.05), 0.0, 0.7)
    _handle((0, 0, 0.02), (1.3, 0, 0.02), 0.018, jasan, 0.016)
    _handle((1.36, 0.06, 0.03), (2.0, 0.16, 0.03), 0.026, dub, 0.03)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.008, location=(1.31, 0.02, 0.025), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(kuze)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.008, location=(1.36, 0.06, 0.03), rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(kuze)
    return None


def shovel(name):
    """Drevena lopata: z jednoho kusu buku, list mirne vyduty, na okraji kovane obiti (jako ve 14. st.)."""
    jasan, dub, fe, ocel, provaz = _woods()
    _handle((0, 0, 0.02), (1.05, 0, 0.02), 0.017, jasan)
    _box((-0.04, 0, 0.02), (0.06, 0.12, 0.025), jasan, bevel=0.008)             # priculi rukojeti
    bm = bmesh.new()
    W, L = 0.26, 0.36
    nx, ny = 10, 8
    vs = [[bm.verts.new((1.05 + L * i / nx, -W / 2 + W * j / ny * (1 - 0.15 * (1 - i / nx)), 0.02 + 0.025 * ((j / ny - 0.5) * 2) ** 2))
           for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    me = bpy.data.meshes.new("list")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(jasan)
    o = bpy.data.objects.new("list", me)
    bpy.context.scene.collection.objects.link(o)
    so = o.modifiers.new("t", "SOLIDIFY")
    so.thickness = 0.015
    _box((1.05 + L, 0, 0.032), (0.03, W + 0.01, 0.022), fe, bevel=0.003)
    for sy in (-1, 1):
        _box((1.05 + L * 0.85, sy * W / 2, 0.032), (L * 0.32, 0.012, 0.02), fe, bevel=0.003)
    return None


def mallet(name):
    """Drevena palice (tesarska): bukova hlava s kovanymi obrucemi, jasanove topurko."""
    jasan, dub, fe, ocel, provaz = _woods()
    _handle((0, 0, 0.065), (0.42, 0, 0.065), 0.016, jasan, 0.018)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.065, depth=0.24, location=(0.45, 0, 0.065), rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(dub)
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.066, minor_radius=0.006, location=(0.45, sy * 0.105, 0.065), rotation=(math.pi / 2, 0, 0))
        bpy.context.object.data.materials.append(fe)
    return None


def frame_saw(name):
    """Ramova pila: dva rameny, priecka, zkrouceny provaz s kolíkem (napinak) a tenky list se zuby."""
    jasan, dub, fe, ocel, provaz = _woods()
    for sx in (-1, 1):
        _box((sx * 0.32, 0, 0.3), (0.035, 0.022, 0.6), dub, bevel=0.004)
        _handle((sx * 0.32, 0, 0.0), (sx * 0.32, 0, -0.12), 0.014, dub)
    _box((0, 0, 0.3), (0.64, 0.02, 0.03), dub, bevel=0.003)
    for k in range(3):
        _handle((-0.32, 0.006 * (k - 1), 0.58), (0.32, 0.006 * (1 - k), 0.58), 0.004, provaz)
    _box((0.05, 0.015, 0.62), (0.015, 0.012, 0.12), dub, bevel=0.002)
    bm = bmesh.new()
    n = 60
    pts = [(-0.32, 0.03), (0.32, 0.03)] + [(0.32 - 0.64 * i / n, 0.005 if i % 2 else -0.006) for i in range(n + 1)]
    top = [bm.verts.new((x, 0.0, z)) for x, z in pts]
    bm.faces.new(top)
    me = bpy.data.meshes.new("list")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ocel)
    o = bpy.data.objects.new("list", me)
    bpy.context.scene.collection.objects.link(o)
    so = o.modifiers.new("t", "SOLIDIFY")
    so.thickness = 0.0015
    o.location = (0, 0, 0.0)
    # cela pila lezi na boku
    return None


def adze(name):
    """Teslice: kovane ostri napric k topurku (jako motyka), na tesani tramu a korýtek."""
    jasan, dub, fe, ocel, provaz = _woods()
    _handle((0, 0, 0.02), (0.5, 0, 0.02), 0.016, jasan, 0.019)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.028, depth=0.06, location=(0.5, 0, 0.02), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(fe)
    bm = bmesh.new()
    pts = [(0.48, 0.02), (0.52, 0.02), (0.56, 0.16), (0.44, 0.16)]
    top = [bm.verts.new((x, y, 0.028)) for x, y in pts]
    bot = [bm.verts.new((x, y, 0.012 if i < 2 else 0.02)) for i, (x, y) in enumerate(pts)]
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    me = bpy.data.meshes.new("ostri")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ocel)
    o = bpy.data.objects.new("ostri", me)
    bpy.context.scene.collection.objects.link(o)
    return None


def tongs(name):
    """Kovarske kleste: dve kovana ramena na nytu, celisti zahnute."""
    jasan, dub, fe, ocel, provaz = _woods()
    for sy in (-1, 1):
        cu = bpy.data.curves.new("rameno", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for bp, co in zip(sp.bezier_points, [(0.0, sy * 0.03, 0.01), (0.38, sy * 0.008, 0.01), (0.5, -sy * 0.012, 0.012)]):
            bp.co = co
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cu.bevel_depth = 0.007
        ob = bpy.data.objects.new("rameno", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(fe)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.012, depth=0.03, location=(0.38, 0, 0.01))
    bpy.context.object.data.materials.append(fe)
    return None


def ladder(name, L=3.0):
    """Zebrik: dva stipane jedlove stráně (polokulate), zasazene priecle (picle) s klinky."""
    jasan, dub, fe, ocel, provaz = _woods()
    for sy in (-1, 1):
        _handle((0, sy * 0.22, 0.03), (L, sy * 0.19, 0.03), 0.03, jasan, 0.026, 8)
    n = int(L / 0.3)
    for k in range(1, n):
        x = k * L / n
        w = 0.22 - 0.03 * x / L
        _handle((x, -w - 0.02, 0.03), (x, w + 0.02, 0.03), 0.016, dub, 0.016, 8)
    return None


def wheelbarrow(name):
    """Dreveny trakar: rám ze dvou ojnic s rukojetmi, loukotove kolo s kovanou obruci, korba z prken."""
    jasan, dub, fe, ocel, provaz = _woods()
    for sy in (-1, 1):
        _handle((0.0, sy * 0.28, 0.48), (1.25, sy * 0.18, 0.22), 0.025, dub)
        _handle((0.85, sy * 0.21, 0.27), (0.85, sy * 0.24, 0.0), 0.022, dub)       # nozky
    # korba
    _box((0.7, 0, 0.32), (0.75, 0.5, 0.025), dub, bevel=0.004)
    for sy in (-1, 1):
        o = _box((0.7, sy * 0.27, 0.43), (0.75, 0.025, 0.22), dub, bevel=0.004)
        o.rotation_euler = (sy * -0.25, 0, 0)
    _box((0.33, 0, 0.43), (0.025, 0.55, 0.22), dub, bevel=0.004)
    _box((1.08, 0, 0.43), (0.025, 0.55, 0.22), dub, bevel=0.004)
    # kolo
    c = (1.32, 0, 0.2)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.025, location=c, rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(dub)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.008, location=c, rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(fe)
    for k in range(6):
        a = math.pi * k / 3
        _handle(c, (c[0] + math.cos(a) * 0.17, 0, c[2] + math.sin(a) * 0.17), 0.012, jasan)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.04, depth=0.1, location=c, rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(dub)
    return None


def churn(name):
    """Maselnice: vysoky sudek z dуžek s obručemi, viko a tlouk."""
    jasan, dub, fe, ocel, provaz = _woods()
    _turned((0, 0, 0), [(0.0, 0.0), (0.15, 0.0), (0.15, 0.02), (0.13, 0.75), (0.12, 0.75), (0.0, 0.75)], dub, 20)
    for zz in (0.08, 0.38, 0.68):
        rr = 0.15 - 0.02 * zz / 0.75
        bpy.ops.mesh.primitive_torus_add(major_radius=rr + 0.004, minor_radius=0.008, location=(0, 0, zz))
        bpy.context.object.data.materials.append(provaz)
    _turned((0, 0, 0.75), [(0.0, 0.0), (0.135, 0.0), (0.135, 0.02), (0.03, 0.03), (0.0, 0.03)], jasan, 16)
    _handle((0, 0, 0.75), (0, 0, 1.25), 0.016, jasan)
    return None


def mortar(name):
    """Hmozdir: soustruzena bukova nadoba s okrajem a tlouček."""
    jasan, dub, fe, ocel, provaz = _woods()
    _turned((0, 0, 0), [(0.0, 0.0), (0.1, 0.0), (0.11, 0.03), (0.1, 0.06), (0.12, 0.18), (0.13, 0.2), (0.1, 0.2), (0.08, 0.06), (0.0, 0.06)], dub, 20)
    o = _turned((0, 0, 0), [(0.0, 0.0), (0.035, 0.0), (0.03, 0.08), (0.02, 0.2), (0.025, 0.28), (0.0, 0.3)], jasan, 12)
    o.location = (0.05, 0, 0.08)
    o.rotation_euler = (0, 0.4, 0)
    return None


def quern(name):
    """Rucni zernov: dva kamenne kotouce, horni s otvorem a kolíkem na otaceni, na drevenem podstavci."""
    jasan, dub, fe, ocel, provaz = _woods()
    kamen = _plain("zernov_kamen", (0.2, 0.19, 0.17), 0.0, 0.9)
    _box((0, 0, 0.15), (0.6, 0.6, 0.3), dub, bevel=0.01)
    _turned((0, 0, 0.3), [(0.0, 0.0), (0.24, 0.0), (0.25, 0.02), (0.25, 0.08), (0.0, 0.09)], kamen, 24)
    _turned((0, 0, 0.39), [(0.035, 0.0), (0.245, 0.0), (0.25, 0.02), (0.24, 0.08), (0.05, 0.1), (0.035, 0.1)], kamen, 24)
    _handle((0.18, 0, 0.47), (0.18, 0, 0.62), 0.015, jasan)
    return None


def _tex_straw(name, seed):
    R = random.Random(seed)
    W, H = 256, 1024
    im = Image.new("RGB", (W, H), (176, 148, 84))
    d = ImageDraw.Draw(im)
    for _ in range(1400):
        x = R.uniform(0, W)
        c = R.choice([(214, 186, 112), (196, 166, 92), (150, 122, 66), (226, 204, 138)])
        d.line((x, 0, x + R.uniform(-6, 6), H), fill=c, width=R.randint(1, 3))
    return _save(im, name)


def sheaf(name, h=1.0, standing=True):
    """Snop slamy: stovky stebel, uprostred stazen povreslem, nahore klasy, dole rovne useknuto."""
    straws = [_plain("slama_%d" % i, c, 0.0, 0.75) for i, c in enumerate(((0.42, 0.3, 0.1), (0.52, 0.38, 0.14), (0.36, 0.25, 0.08), (0.6, 0.45, 0.18)))]
    straw = straws[0]
    klas = _plain("klasy", (0.6, 0.47, 0.22), 0.0, 0.85)
    R = random.Random(11)
    zb = h * 0.42                       # povreslo
    for k in range(260):
        a = R.uniform(0, 2 * math.pi)
        rr = math.sqrt(R.random())
        rb = 0.13 * rr
        rt = 0.07 * rr
        x0, y0 = math.cos(a) * rb * 1.25, math.sin(a) * rb * 1.25
        xm, ym = math.cos(a) * rb * 0.55, math.sin(a) * rb * 0.55
        x1, y1 = math.cos(a) * (rt + 0.08 * rr), math.sin(a) * (rt + 0.08 * rr)
        z1 = h * R.uniform(0.88, 1.0)
        st = straws[k % 4]
        _handle((x0, y0, 0.0), (xm, ym, zb), 0.0045, st, 0.0045, 4)
        _handle((xm, ym, zb), (x1, y1, z1), 0.0045, st, 0.003, 4)
        if R.random() < 0.45:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(x1, y1, z1 + 0.03), segments=5, ring_count=4)
            o = bpy.context.object
            o.scale = (0.5, 0.5, 2.2)
            o.data.materials.append(klas)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.075, minor_radius=0.014, location=(0, 0, zb), major_segments=20, minor_segments=6)
    bpy.context.object.data.materials.append(straw)
    return None


def sheaf_stack(name):
    """Panak: osm snopu oprenych o sebe klasy nahoru, navrchu snop klasy dolu jako stříška."""
    BUILD_LOCAL = []
    for k in range(8):
        a = 2 * math.pi * k / 8
        before = set(bpy.data.objects)
        sheaf(name + str(k), 1.0)
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            o.select_set(False)
        empty = bpy.data.objects.new("e", None)
        bpy.context.scene.collection.objects.link(empty)
        for o in new:
            o.parent = empty
        empty.location = (math.cos(a) * 0.22, math.sin(a) * 0.22, 0.0)
        empty.rotation_euler = (-math.sin(a) * 0.25, math.cos(a) * 0.25, 0)
        BUILD_LOCAL.append(empty)
    before = set(bpy.data.objects)
    sheaf(name + "_vrch", 1.0)
    new = [o for o in bpy.data.objects if o not in before]
    empty = bpy.data.objects.new("e", None)
    bpy.context.scene.collection.objects.link(empty)
    for o in new:
        o.parent = empty
    empty.location = (0, 0, 1.55)
    empty.rotation_euler = (math.pi, 0, 0)
    bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.type == "MESH" and o.parent:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
    return None


def firewood_pile(name, L=1.6, rows=7):
    """Hranice stipaneho dreva: polena (pulena i cela, s kurou a letokruhy) v radach, na koncich krizem
    skladane sloupky, dole dva podkladove tramky, navrchu par polen ledabyle."""
    bark = _mat("kura_buk", _tex_bark("kura_buk", (112, 96, 80), 3), 0.9)
    end = _mat("rez_drevo", _tex_endgrain("letokruhy", 4), 0.8)
    jasan, dub, fe, ocel, provaz = _woods()
    R = random.Random(21)
    r = 0.06
    depth = 0.42
    for sy in (-1, 1):
        _box((0, 0, 0.04), (L + 0.1, 0.08, 0.08), dub, bevel=0.006).location = (0, sy * 0.13, 0.04)
    for row in range(rows):
        z = 0.08 + r + row * r * 1.72
        x = -L / 2 + 0.08 + (r if row % 2 else 0)
        while x < L / 2 - 0.08:
            rr = r * R.uniform(0.8, 1.15)
            _log((x, R.uniform(-0.02, 0.02), z), depth * R.uniform(0.92, 1.05), rr, "y", bark, end, R.uniform(0, 6.28), split=1 if R.random() < 0.6 else 0)
            x += 2 * r + 0.004

    # zatlucene kuly na koncich drzi rady
    for sx in (-1, 1):
        for sy in (-1, 1):
            _log((sx * (L / 2 + 0.02), sy * 0.16, (rows * r * 1.72 + 0.2) / 2), rows * r * 1.72 + 0.2, 0.035, "z", bark, end)
    for k in range(3):
        _log((R.uniform(-0.4, 0.4), R.uniform(-0.05, 0.05), 0.08 + 2 * r + rows * r * 1.72), depth, r, "y", bark, end, R.uniform(-0.5, 0.5))
    return None


def chopping_log(name):
    """Spalek na stipani se sekerou zatnutou nahore a par polen kolem."""
    bark = _mat("kura_buk", _tex_bark("kura_buk", (112, 96, 80), 3), 0.9)
    end = _mat("rez_drevo", _tex_endgrain("letokruhy", 4), 0.8)
    _log((0, 0, 0.25), 0.5, 0.22, "z", bark, end)
    jasan, dub, fe, ocel, provaz = _woods()
    _handle((0.0, 0.0, 0.52), (0.38, 0.12, 0.85), 0.017, jasan)
    _box((0.0, 0.0, 0.52), (0.04, 0.16, 0.1), fe, bevel=0.004).rotation_euler = (0, -0.7, 0.3)
    return None


BUILD.update({
    "metla": lambda: broom("metla"),
    "vidle": lambda: pitchfork("vidle"),
    "vidle_kovane": lambda: pitchfork("vidle_kovane", 2, False),
    "hrabe": lambda: rake("hrabe"),
    "kosa": lambda: scythe("kosa"),
    "srp": lambda: sickle("srp"),
    "cep": lambda: flail("cep"),
    "lopata": lambda: shovel("lopata"),
    "palice": lambda: mallet("palice"),
    "pila": lambda: frame_saw("pila"),
    "teslice": lambda: adze("teslice"),
    "kleste": lambda: tongs("kleste"),
    "zebrik": lambda: ladder("zebrik"),
    "trakar": lambda: wheelbarrow("trakar"),
    "maselnice": lambda: churn("maselnice"),
    "hmozdir": lambda: mortar("hmozdir"),
    "zernov": lambda: quern("zernov"),
    "snop": lambda: sheaf("snop"),
    "panak_snopu": lambda: sheaf_stack("panak_snopu"),
    "hranice_dreva": lambda: firewood_pile("hranice_dreva"),
    "spalek_stipani": lambda: chopping_log("spalek_stipani"),
})
