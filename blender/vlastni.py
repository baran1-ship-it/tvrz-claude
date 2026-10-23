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
    "stul_selsky": lambda: feast_table("stul_selsky", L=1.9, W=0.82, H=0.76),
    "lavice_selska": lambda: feast_bench("lavice_selska", L=1.8),
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
    if icon == "@drolerie":
        return _drollery(size)
    if icon == "@nyt":
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((0, 0, size - 1, size - 1), fill=(22, 24, 30, 255))
        d.ellipse((size * 0.25, size * 0.2, size * 0.5, size * 0.45), fill=(120, 125, 135, 255))
        return im
    svg = open(os.path.join(ICONS, icon + ".svg")).read()
    svg = svg.replace('<path d="M0 0h512v512H0z"/>', "").replace('fill="#fff"', 'fill="#ffffff"')
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    m = Image.open(io.BytesIO(png)).convert("RGBA").split()[3]          # alfa = tvar figury
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    edge = m.filter(ImageFilter.MaxFilter(7))
    out.paste((20, 16, 12, 255), (0, 0), edge)
    out.paste((*col, 255), (0, 0), m)
    return out



def _drollery(size):
    """Drolerie z okraju gotickych rukopisu: nahy mužik v predklonu, z rozkroku/zadku mu trci zlata trouba,
    hlava kudrnata otocena k divakovi. Vlastni kresba v duchu marginálií 14. stoleti."""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ink = (24, 18, 14, 255)
    kuze = (236, 224, 204, 255)
    stin = (205, 188, 165, 255)
    vlasy = (128, 66, 30, 255)
    zlato = (226, 176, 58, 255)
    zlato2 = (176, 122, 30, 255)

    def P(x, y):
        return (x * S, y * S)

    def limb(pts, w):
        pp = [P(*q) for q in pts]
        d.line(pp, fill=ink, width=int(S * (w + 0.022)), joint="curve")
        for q in (pp[0], pp[-1]):
            r = S * (w + 0.022) / 2
            d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=ink)
        d.line(pp, fill=kuze, width=int(S * w), joint="curve")
        for q in pp:
            r = S * w / 2
            d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=kuze)

    def blob(pts, fill):
        d.polygon([P(*q) for q in pts], fill=fill, outline=ink, width=int(S * 0.011))

    # predklon: hlava vepredu vlevo otocena k divakovi, trup skoro vodorovne, zadek nahore vpravo,
    # z nej trouba sikmo vzhuru; nohy rozkročené dolu, ruka visi k zemi
    limb([(0.5, 0.46), (0.45, 0.66), (0.4, 0.86)], 0.075)
    limb([(0.6, 0.46), (0.64, 0.66), (0.66, 0.85)], 0.075)
    blob([(0.42, 0.84), (0.35, 0.88), (0.27, 0.9), (0.28, 0.87), (0.36, 0.83)], kuze)
    blob([(0.64, 0.83), (0.7, 0.87), (0.78, 0.885), (0.77, 0.86), (0.69, 0.82)], kuze)
    for x0, y0, sg in ((0.28, 0.885, 1), (0.77, 0.872, -1)):
        for k in range(3):
            d.line([P(x0 + sg * 0.012 * k, y0 - 0.006), P(x0 + sg * 0.012 * k, y0 + 0.01)], fill=ink, width=2)
    limb([(0.36, 0.4), (0.35, 0.52), (0.37, 0.6)], 0.042)                                 # zadni ruka
    torso = [(0.3, 0.33), (0.38, 0.27), (0.48, 0.26), (0.57, 0.25), (0.64, 0.28), (0.66, 0.36), (0.63, 0.45), (0.55, 0.48),
             (0.45, 0.47), (0.36, 0.45), (0.3, 0.41)]
    blob(torso, kuze)
    d.polygon([P(*q) for q in [(0.36, 0.44), (0.46, 0.46), (0.55, 0.47), (0.5, 0.43), (0.4, 0.42)]], fill=stin)
    d.arc((*P(0.52, 0.24), *P(0.68, 0.44)), 250, 80, fill=ink, width=int(S * 0.006))     # zadek
    d.line([P(0.6, 0.25), P(0.62, 0.31)], fill=ink, width=int(S * 0.006))
    d.arc((*P(0.4, 0.36), *P(0.5, 0.49)), 30, 150, fill=ink, width=int(S * 0.005))      # bricho
    # trouba ze zadku sikmo vzhuru doprava
    d.line([P(0.645, 0.29), P(0.8, 0.15)], fill=ink, width=int(S * 0.04))
    d.line([P(0.645, 0.29), P(0.8, 0.15)], fill=zlato, width=int(S * 0.022))
    bell = [(0.77, 0.165), (0.84, 0.07), (0.885, 0.095), (0.9, 0.15), (0.88, 0.2), (0.8, 0.19)]
    blob(bell, zlato)
    d.ellipse((*P(0.86, 0.075), *P(0.905, 0.19)), fill=zlato2, outline=ink, width=int(S * 0.008))
    for t in (0.45, 0.6):
        x = 0.645 + (0.8 - 0.645) * t
        y = 0.29 + (0.15 - 0.29) * t
        d.line([P(x - 0.012, y - 0.016), P(x + 0.012, y + 0.016)], fill=ink, width=int(S * 0.006))
    # hlava: zvednuta, oblicej k divakovi s vyvalenyma ocima a pootevrenymi usty
    cx, cy, rr = 0.25, 0.32, 0.085
    d.ellipse((*P(cx - rr, cy - rr), *P(cx + rr, cy + rr)), fill=kuze, outline=ink, width=int(S * 0.011))
    R = random.Random(5)
    for k in range(15):
        a = math.pi * (0.15 + 1.05 * k / 14)
        hx, hy = cx + math.cos(a) * 0.075, cy - 0.01 - math.sin(a) * 0.07
        r = 0.03 + R.uniform(0, 0.01)
        d.ellipse((*P(hx - r, hy - r), *P(hx + r, hy + r)), fill=vlasy, outline=ink, width=int(S * 0.006))
    for k in range(10):
        hx, hy = cx - 0.06 + R.uniform(0, 0.12), cy - 0.09 + R.uniform(0, 0.04)
        d.arc((*P(hx - 0.014, hy - 0.014), *P(hx + 0.014, hy + 0.014)), 0, 270, fill=(80, 38, 16, 255), width=int(S * 0.005))
    for ex in (-0.03, 0.025):
        d.ellipse((*P(cx + ex - 0.016, cy - 0.012), *P(cx + ex + 0.016, cy + 0.016)), fill=(250, 248, 240, 255), outline=ink, width=int(S * 0.004))
        d.ellipse((*P(cx + ex - 0.006, cy - 0.002), *P(cx + ex + 0.006, cy + 0.01)), fill=ink)
        d.line([P(cx + ex - 0.018, cy - 0.025), P(cx + ex + 0.016, cy - 0.03)], fill=ink, width=int(S * 0.006))
    d.line([P(cx, cy + 0.0), P(cx - 0.006, cy + 0.03), P(cx + 0.008, cy + 0.032)], fill=ink, width=int(S * 0.005))   # nos
    d.ellipse((*P(cx - 0.016, cy + 0.045), *P(cx + 0.014, cy + 0.065)), fill=(120, 40, 30, 255), outline=ink, width=int(S * 0.004))
    d.ellipse((*P(cx - 0.065, cy + 0.015), *P(cx - 0.035, cy + 0.045)), fill=(240, 190, 175, 255))
    d.ellipse((*P(cx + 0.035, cy + 0.015), *P(cx + 0.065, cy + 0.045)), fill=(240, 190, 175, 255))
    return im.resize((size, size), Image.LANCZOS)

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
    "stit_drolerie": ((44, 70, 140), [("@drolerie", None, 0.92, 0.5, 0.55)] + [("@nyt", None, 0.022, x, y) for x, y in
                     ((0.22, 0.12), (0.5, 0.1), (0.78, 0.12), (0.3, 0.4), (0.72, 0.42), (0.5, 0.88), (0.22, 0.72))]),               # drolerie z marginalii
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
    if thick > 0.0:
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


# ======================================================================= dalsi varka: jidlo, hospodarstvi, zbroj, kniha

def _noise_img(name, base, dark, scale, seed=1, W=512):
    """Bezesva fraktalni sumova textura (PIL): base -> dark, jemne zrno i vetsi skvrny. Hra umi jen obrazkove textury."""
    import numpy as np
    R = np.random.default_rng(seed)
    acc = np.zeros((W, W))
    amp, tot = 1.0, 0.0
    g = max(2, int(scale / 4))
    for octave in range(5):
        small = Image.fromarray((R.random((g, g)) * 255).astype("uint8"))
        tiled = Image.new("L", (g * 3, g * 3))
        for i in range(3):
            for j in range(3):
                tiled.paste(small, (i * g, j * g))
        big = tiled.resize((W * 3, W * 3), Image.BICUBIC).crop((W, W, 2 * W, 2 * W))
        acc += np.asarray(big, dtype=float) / 255.0 * amp
        tot += amp
        amp *= 0.55
        g *= 2
    acc /= tot
    acc = (acc - acc.min()) / max(1e-6, acc.max() - acc.min())
    b = np.array(base, dtype=float)
    d = np.array(dark, dtype=float)
    img = (d[None, None, :] + (b - d)[None, None, :] * acc[:, :, None]) * 255.0
    return _save(Image.fromarray(np.clip(img, 0, 255).astype("uint8")), "sum_" + name)


def _noise_mat(name, base, dark, scale=18.0, rough=0.8, bump=0.3):
    """Material s obrazkovou sumovou texturou (puvodne procedurni uzly, ty se do hry neprenesou)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(_noise_img(name, base, dark, scale, abs(hash(name)) % 1000))
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    return m


def _blob(c, rad, mat, seg=24, rings=14, wob=0.04, seed=1, flat_bottom=True):
    """Hrouda: deformovana koule (bochnik, syr, pytel) s rovnym spodkem."""
    R = random.Random(seed)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=1.0, location=(0, 0, 0))
    o = bpy.context.object
    ph = [R.uniform(0, 6.28) for _ in range(4)]
    for v in o.data.vertices:
        p = v.co.copy()
        a = math.atan2(p.y, p.x)
        k = 1.0 + wob * (math.sin(3 * a + ph[0]) + 0.6 * math.sin(5 * a + ph[1]) + 0.5 * math.sin(4 * p.z + ph[2]))
        x, y, z = p.x * rad[0] * k, p.y * rad[1] * k, p.z * rad[2]
        if flat_bottom and z < 0:
            z *= 0.15
        v.co = Vector((x + c[0], y + c[1], z + c[2] + (rad[2] * 0.15 if flat_bottom else 0)))
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def bread(name, big=False):
    """Bochnik / pecen: kulaty chleb s popraskanou kurkou, tri naříznutí a moukou poprasene."""
    crust = _noise_mat("kurka", (0.55, 0.32, 0.12), (0.3, 0.15, 0.05), 25.0, 0.7, 0.5)
    rez = _noise_mat("chleb_rez", (0.85, 0.72, 0.5), (0.62, 0.48, 0.3), 40.0, 0.9, 0.2)
    s = 1.45 if big else 1.0
    _blob((0, 0, 0), (0.1 * s, 0.1 * s * (1.25 if big else 1.0), 0.06 * s), crust, seed=3 if big else 2, wob=0.03)
    # trojice nariznuti: svetla stridka v kurce, ohnuta po klenbe bochniku
    top = 0.069 * s
    for k in range(3):
        y = (k - 1) * 0.045 * s
        zz = top * (1 - (y / (0.1 * s)) ** 2) ** 0.5 - 0.004
        o = _box((0, y, zz), (0.12 * s * (1 - abs(k - 1) * 0.2), 0.012, 0.01), rez, bevel=0.003)
        o.rotation_euler = (0, 0, 0.5)
    return None


def cheese(name):
    """Bochnik syra s vosku podobnou kurkou a vykrojenou vyseci (vidno svetle vnitrek s okem)."""
    kur = _noise_mat("syr_kura", (0.85, 0.6, 0.18), (0.6, 0.38, 0.08), 12.0, 0.5, 0.15)
    vn = _noise_mat("syr_vnitrek", (0.98, 0.88, 0.55), (0.9, 0.78, 0.42), 30.0, 0.6, 0.1)
    bm = bmesh.new()
    n = 40
    R1, H = 0.16, 0.1
    gap = math.radians(50)
    ring = []
    for i in range(n + 1):
        a = gap / 2 + (2 * math.pi - gap) * i / n
        ring.append(a)
    top, bot = [], []
    for a in ring:
        rr = R1 * (1 + 0.02 * math.sin(a * 5))
        top.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, H)))
        bot.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, 0)))
    ct, cb = bm.verts.new((0, 0, H)), bm.verts.new((0, 0, 0))
    for i in range(n):
        f = bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
        f.material_index = 0
        bm.faces.new((ct, top[i], top[i + 1])).material_index = 0
        bm.faces.new((cb, bot[i + 1], bot[i])).material_index = 0
    bm.faces.new((cb, bot[0], top[0], ct)).material_index = 1
    bm.faces.new((cb, ct, top[-1], bot[-1])).material_index = 1
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(kur)
    me.materials.append(vn)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bv = ob.modifiers.new("b", "BEVEL")
    bv.width = 0.008
    bv.segments = 3
    # vykrojena vysec vedle
    o = _box((0.24, 0.06, 0.05), (0.12, 0.05, 0.1), vn, bevel=0.004)
    o.rotation_euler = (0, 0, 0.3)
    return None


def skep(name):
    """Slamena koshnice (ul): spirala z provazcu slamy stazenych vrbovymi pruty, cesno dole, na kamenném podstavci."""
    straw = _noise_mat("slama_kos", (0.62, 0.48, 0.22), (0.38, 0.27, 0.1), 60.0, 0.85, 0.6)
    kamen = _noise_mat("kamen_pod", (0.4, 0.38, 0.35), (0.22, 0.21, 0.19), 8.0, 0.9, 0.4)
    _box((0, 0, 0.05), (0.6, 0.6, 0.1), kamen, bevel=0.02)
    H = 0.55
    n = 14
    for k in range(n):
        t = k / n
        z = 0.1 + H * t + 0.02
        r = 0.24 * math.sqrt(max(0.0, 1 - (t * 0.92) ** 2)) + 0.02
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=H / n * 0.62, location=(0, 0, z), major_segments=32, minor_segments=8)
        bpy.context.object.data.materials.append(straw)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0, 0, 0.1 + H + 0.03), segments=12, ring_count=6)
    bpy.context.object.data.materials.append(straw)
    _box((0.24, 0, 0.13), (0.04, 0.08, 0.05), _plain("cesno", (0.02, 0.015, 0.01), 0.0, 1.0), bevel=0.0)
    return None


def sack(name, flour=False):
    """Pytel: lnena pytlovina, vrchem stazeny provazem (obili) nebo prehnuty a otevreny s mukou."""
    pyt = _noise_mat("pytlovina" + ("_m" if flour else ""), (0.66, 0.56, 0.4) if not flour else (0.82, 0.78, 0.68),
                     (0.45, 0.37, 0.25) if not flour else (0.68, 0.62, 0.52), 120.0, 0.95, 0.5)
    _blob((0, 0, 0), (0.22, 0.17, 0.27), pyt, seed=7 if flour else 8, wob=0.06)
    jasan, dub, fe, ocel, provaz = _woods()
    if flour:
        _blob((0, 0, 0.3), (0.15, 0.12, 0.05), _plain("mouka", (0.95, 0.93, 0.88), 0.0, 1.0), seed=9, wob=0.1)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.035, location=(0, 0, 0.31), major_segments=24, minor_segments=8)
        bpy.context.object.data.materials.append(pyt)
    else:
        _blob((0, 0, 0.33), (0.1, 0.08, 0.06), pyt, seed=11, wob=0.1, flat_bottom=False)
        _blob((0, 0, 0.42), (0.07, 0.06, 0.07), pyt, seed=10, wob=0.15, flat_bottom=False)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.012, location=(0, 0, 0.375))
        bpy.context.object.data.materials.append(provaz)
    return None


def haystack(name):
    """Kupka sena: kupovita hromada s rozcuchanym povrchem (stovky stébel), uprostred tyc."""
    seno = _noise_mat("seno", (0.55, 0.5, 0.22), (0.32, 0.3, 0.12), 50.0, 0.95, 0.8)
    R = random.Random(4)
    _blob((0, 0, 0), (0.9, 0.9, 1.1), seno, seed=12, wob=0.05)
    stebla = [_plain("steblo%d" % i, c, 0.0, 0.9) for i, c in enumerate(((0.5, 0.45, 0.18), (0.62, 0.56, 0.26), (0.4, 0.38, 0.15)))]
    for k in range(380):
        a = R.uniform(0, 2 * math.pi)
        z = R.uniform(0.05, 1.3)
        t = min(1.0, z / 1.38)
        r = 0.9 * math.sqrt(max(0.0, 1 - t * t)) + 0.01
        p0 = Vector((math.cos(a) * r, math.sin(a) * r, z))
        d = Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1.2, 0.3))).normalized() * R.uniform(0.15, 0.3)
        _handle(p0, p0 + d, 0.004, stebla[k % 3], 0.002, 3)
    jasan, dub, fe, ocel, provaz = _woods()
    _handle((0, 0, 0.5), (0, 0, 1.75), 0.03, dub, 0.02, 8)
    return None


def cauldron_tripod(name):
    """Kotlik na trojnozce nad ohnistem: kovana trojnozka, retez s hakem, cerny kotlik s uchem, kruh kamenu a ohořelá polena."""
    jasan, dub, fe, ocel, provaz = _woods()
    kam = _noise_mat("kamen_ohniste", (0.45, 0.43, 0.4), (0.18, 0.17, 0.16), 6.0, 0.9, 0.6)
    uhel = _plain("uhel", (0.03, 0.025, 0.02), 0.0, 0.9)
    cerny = _plain("kotlik_zelezo", (0.05, 0.05, 0.05), 0.8, 0.6)
    R = random.Random(6)
    for k in range(11):
        a = 2 * math.pi * k / 11
        _blob((math.cos(a) * 0.45, math.sin(a) * 0.45, 0), (0.1, 0.08, 0.07), kam, seg=12, rings=8, seed=k, wob=0.12)
    for k in range(5):
        a = R.uniform(0, 6.28)
        _handle((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.04), (-math.cos(a) * 0.05, -math.sin(a) * 0.05, 0.06), 0.03, uhel, 0.025, 8)
    H = 1.4
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        _handle((math.cos(a) * 0.6, math.sin(a) * 0.6, 0), (0, 0, H), 0.018, fe, 0.014, 8)
    for i in range(10):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.018, minor_radius=0.005, location=(0, 0, H - 0.05 - i * 0.04),
                                         rotation=(math.pi / 2 if i % 2 else 0, 0, math.pi / 2 if i % 2 else 0))
        bpy.context.object.data.materials.append(fe)
    _turned((0, 0, 0.35), [(0.0, 0.0), (0.12, 0.0), (0.2, 0.06), (0.22, 0.16), (0.2, 0.28), (0.21, 0.3), (0.19, 0.3), (0.0, 0.29)], cerny, 24)
    cu = bpy.data.curves.new("ucho", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(-0.21, 0, 0.62), (0, 0, 0.88), (0.21, 0, 0.62)]):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.007
    o = bpy.data.objects.new("ucho", cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(fe)
    return None


def tankard(name):
    """Dreveny korbel: dužky s dvema obručemi, ucho, víčko na pantu."""
    jasan, dub, fe, ocel, provaz = _woods()
    _turned((0, 0, 0), [(0.0, 0.0), (0.06, 0.0), (0.058, 0.15), (0.0, 0.15)], dub, 16)
    for z in (0.025, 0.125):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.061, minor_radius=0.004, location=(0, 0, z))
        bpy.context.object.data.materials.append(fe)
    cu = bpy.data.curves.new("ucho", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(0.055, 0, 0.12), (0.11, 0, 0.08), (0.055, 0, 0.03)]):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.008
    o = bpy.data.objects.new("ucho", cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(dub)
    _turned((0, 0, 0.15), [(0.0, 0.0), (0.062, 0.0), (0.062, 0.008), (0.03, 0.014), (0.0, 0.016)], dub, 16)
    _box((0.06, 0, 0.155), (0.03, 0.02, 0.012), fe, bevel=0.002)
    return None


def braid(name, kind="cibule"):
    """Venec cibule nebo cesneku na zed: pletenec z natí s hlavickami, nahore poutko na hřebík."""
    if kind == "cibule":
        slup = _noise_mat("cibule_slupka", (0.72, 0.42, 0.16), (0.45, 0.22, 0.06), 30.0, 0.5, 0.2)
        s = (0.045, 0.045, 0.04)
    elif kind == "cesnek":
        slup = _noise_mat("cesnek", (0.92, 0.88, 0.8), (0.78, 0.7, 0.62), 30.0, 0.5, 0.2)
        s = (0.03, 0.03, 0.028)
    nat = _noise_mat("nat_sucha", (0.55, 0.48, 0.3), (0.35, 0.3, 0.15), 40.0, 0.9, 0.3)
    R = random.Random(5 if kind == "cibule" else 6)
    _handle((0, -0.02, 0.0), (0, -0.02, 0.62), 0.016, nat, 0.01, 6)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.025, minor_radius=0.004, location=(0, -0.02, 0.66), rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(nat)
    n = 13 if kind == "cibule" else 18
    for k in range(n):
        z = 0.05 + 0.5 * k / n
        side = -1 if k % 2 else 1
        c = (side * R.uniform(0.02, 0.05), -0.05 - R.uniform(0, 0.03), z)
        o = _blob(c, s, slup, seg=12, rings=8, seed=k, wob=0.06, flat_bottom=False)
        o.scale = (1, 1, 1.15)
    return None


def herbs(name):
    """Svazky susenych bylin na zed: tri svazky hlavami dolu na provazku pres hrebik."""
    jasan, dub, fe, ocel, provaz = _woods()
    cols = [(0.35, 0.42, 0.22), (0.45, 0.38, 0.32), (0.5, 0.48, 0.25)]
    R = random.Random(8)
    for j, x in enumerate((-0.14, 0.0, 0.14)):
        m = _plain("bylina%d" % j, cols[j], 0.0, 0.9)
        _handle((x, -0.03, 0.42), (x, -0.03, 0.52), 0.004, provaz, 0.004, 4)
        for k in range(40):
            a = R.uniform(0, 6.28)
            rr = R.uniform(0, 0.04)
            p0 = Vector((x, -0.04, 0.4))
            p1 = Vector((x + math.cos(a) * rr * 2.2, -0.04 + math.sin(a) * rr, 0.1 + R.uniform(0, 0.08)))
            _handle(p0, p1, 0.003, m, 0.002, 3)
            if R.random() < 0.5:
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.01, location=p1)
                bpy.context.object.data.materials.append(m)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.012, minor_radius=0.004, location=(x, -0.04, 0.38))
        bpy.context.object.data.materials.append(provaz)
    _handle((-0.2, -0.03, 0.52), (0.2, -0.03, 0.52), 0.004, provaz, 0.004, 4)
    return None


def barbute(name):
    """Barbuta (Italie/Cechy 15. st.): ocelova prilba s hlubokym nadocnim vyrezem tvaru Y, hreben a nytý lem."""
    st = _plain("ocel_lestena", (0.62, 0.62, 0.64), 1.0, 0.22)
    bm = bmesh.new()
    nu, nv = 40, 24
    vs = []
    for j in range(nv + 1):
        v = j / nv
        th = math.pi * 0.5 * (1 - v)              # od temene (0) k okraji
        row = []
        for i in range(nu):
            a = 2 * math.pi * i / nu
            r = math.sin(th + 0.0001) if v < 1 else 1.0
            rr = 0.12 * (math.cos(math.pi / 2 * v) * 0 + 1.0) * (0.25 + 0.75 * math.sin(math.pi / 2 * (v * 1.15 if v < 0.87 else 1.0)))
            z = 0.27 * (1 - v ** 1.6)
            sx = 1.0 if math.sin(a) > 0 else 1.05
            row.append(bm.verts.new((math.cos(a) * rr * 0.92, math.sin(a) * rr * sx, z)))
        vs.append(row)
    faces = []
    for j in range(nv):
        for i in range(nu):
            i2 = (i + 1) % nu
            a = 2 * math.pi * (i + 0.5) / nu
            v = (j + 0.5) / nv
            # Y vyrez vpredu (-y): uzky pruh dolu a sirsi pro oci
            front = math.cos(a + math.pi / 2) > 0
            ang = abs(math.atan2(math.cos(a), -math.sin(a)))
            if front and ((v > 0.55 and ang < 0.12) or (0.55 < v < 0.72 and ang < 0.38)):
                continue
            faces.append(bm.faces.new((vs[j][i], vs[j][i2], vs[j + 1][i2], vs[j + 1][i])))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(st)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    so = ob.modifiers.new("t", "SOLIDIFY")
    so.thickness = 0.004
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth()
    _box((0, 0, 0.265), (0.012, 0.2, 0.025), st, bevel=0.004).rotation_euler = (0, 0, 0)
    for i in range(22):
        a = 2 * math.pi * i / 22
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.005, location=(math.cos(a) * 0.112, math.sin(a) * 0.12, 0.02), segments=6, ring_count=4)
        bpy.context.object.data.materials.append(st)
    return None


def kettle_hat(name):
    """Zelezny klobouk (kettle hat): kulovita kalota se hrebenem a siroka sikma krempa, kozeny podbradnik."""
    st = _plain("ocel_matna", (0.42, 0.42, 0.43), 0.9, 0.35)
    _turned((0, 0, 0), [(0.0, 0.17), (0.04, 0.168), (0.08, 0.155), (0.11, 0.12), (0.12, 0.06), (0.125, 0.03), (0.2, 0.0), (0.21, -0.008),
                        (0.12, 0.024), (0.115, 0.06), (0.105, 0.12), (0.075, 0.15), (0.0, 0.16)], st, 40)
    _box((0, 0, 0.165), (0.008, 0.2, 0.02), st, bevel=0.004)
    _box((0, 0.12, -0.03), (0.02, 0.006, 0.12), _plain("remen", (0.2, 0.11, 0.05), 0.0, 0.7), bevel=0.002)
    return None


def mail_stand(name):
    """Kruzkova kosile na drevenem stojanu (krizak s ramenem), pod ni prošívanice."""
    jasan, dub, fe, ocel, provaz = _woods()
    # kruzky: hustý vzor provlečených kroužků (obrazková textura)
    W = 1024
    im = Image.new("RGB", (W, W), (22, 22, 24))
    d = ImageDraw.Draw(im)
    st = 8
    for j in range(int(W / (st * 0.75)) + 2):
        for i in range(W // st + 2):
            x = i * st + (st / 2 if j % 2 else 0)
            y = j * st * 0.75
            d.ellipse((x - 5, y - 5, x + 5, y + 5), outline=(150, 150, 152), width=2)
            d.arc((x - 5, y - 5, x + 5, y + 5), 200, 330, fill=(205, 205, 210), width=1)
    mail = _mat("kruzky", _save(im, "kruzky"), 0.4)
    mail.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.85
    gamb = _noise_mat("prosivanice", (0.6, 0.5, 0.36), (0.42, 0.33, 0.22), 80.0, 0.9, 0.3)
    # stojan
    _box((0, 0, 0.03), (0.5, 0.08, 0.06), dub, bevel=0.008)
    _box((0, 0, 0.03), (0.08, 0.5, 0.06), dub, bevel=0.008)
    _handle((0, 0, 0.0), (0, 0, 1.55), 0.025, dub, 0.022, 10)
    _box((0, 0, 1.42), (0.5, 0.06, 0.05), dub, bevel=0.008)
    # trup: zuzeny valec (prosivanice) a pres nej kosile s rukavy
    g = _turned((0, 0, 0.62), [(0.0, 0.0), (0.2, 0.0), (0.19, 0.3), (0.21, 0.6), (0.24, 0.78), (0.12, 0.84), (0.0, 0.84)], gamb, 24)
    g.scale = (1.0, 0.62, 1.0)
    o = _turned((0, 0, 0.55), [(0.0, 0.0), (0.225, 0.0), (0.21, 0.3), (0.225, 0.62), (0.255, 0.84), (0.14, 0.9), (0.06, 0.92), (0.0, 0.92)], mail, 32)
    o.scale = (1.0, 0.7, 1.0)
    for sx in (-1, 1):
        _handle((sx * 0.22, 0, 1.3), (sx * 0.38, 0, 0.95), 0.06, mail, 0.05, 16)
    return None


def crossbow(name):
    """Kuse: dubove lucisko (pazba) s obložením, ocelovy luk, tětiva, ořech a spoušť, třmen na konci."""
    jasan, dub, fe, ocel, provaz = _woods()
    _box((0.0, 0, 0.04), (0.8, 0.045, 0.05), dub, bevel=0.008)
    _box((-0.32, 0, 0.03), (0.22, 0.05, 0.07), dub, bevel=0.012)
    cu = bpy.data.curves.new("luk", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(0.28, -0.36, 0.05), (0.38, 0, 0.065), (0.28, 0.36, 0.05)]):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.012
    o = bpy.data.objects.new("luk", cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(ocel)
    for sy in (-1, 1):
        _handle((0.28, sy * 0.36, 0.05), (0.08, 0, 0.065), 0.002, provaz, 0.002, 4)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.008, location=(0.44, 0, 0.05), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(fe)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.018, depth=0.04, location=(0.08, 0, 0.07), rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(_plain("kost", (0.85, 0.82, 0.72), 0.0, 0.5))
    _handle((-0.02, 0, 0.015), (-0.12, 0, -0.02), 0.006, fe, 0.005, 6)
    return None


def bow_quiver(name):
    """Luk s toulcem: tisovy luk (svetlejsi beli, tmavsi jadro) s tětivou, kozeny toulec se sipy s husimi brky."""
    jasan, dub, fe, ocel, provaz = _woods()
    tis = _noise_mat("tis", (0.7, 0.42, 0.2), (0.45, 0.22, 0.08), 6.0, 0.5, 0.1)
    kuze = _plain("toulec", (0.32, 0.18, 0.08), 0.0, 0.6)
    brk = _plain("brk", (0.88, 0.86, 0.8), 0.0, 0.8)
    cu = bpy.data.curves.new("luk", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(-0.85, 0.0, 0.02), (0, 0.13, 0.02), (0.85, 0.0, 0.02)]):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.014
    o = bpy.data.objects.new("luk", cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(tis)
    _handle((-0.84, 0.0, 0.02), (0.84, 0.0, 0.02), 0.0015, provaz, 0.0015, 4)
    _handle((-0.06, 0.13, 0.02), (0.06, 0.13, 0.02), 0.02, kuze, 0.02, 10)
    # toulec lezi vedle
    _handle((-0.35, 0.35, 0.06), (0.25, 0.35, 0.06), 0.055, kuze, 0.06, 16)
    for k in range(9):
        a = 2 * math.pi * k / 9
        y, z = 0.35 + math.cos(a) * 0.03, 0.06 + math.sin(a) * 0.03
        _handle((0.2, y, z), (0.55, y, z), 0.004, jasan, 0.004, 5)
        for f in range(3):
            fa = a + f * 2.09
            _box((0.5, y + math.cos(fa) * 0.008, z + math.sin(fa) * 0.008), (0.07, 0.002, 0.012), brk, bevel=0.0).rotation_euler = (fa, 0, 0)
    return None


def lectern(name):
    """Recnicky pult s otevrenou knihou: dubovy sloup na nohach do kříže, sikma deska s listou, kniha s pergamenem."""
    jasan, dub, fe, ocel, provaz = _woods()
    perg = _noise_mat("pergamen_listy", (0.92, 0.86, 0.7), (0.8, 0.7, 0.52), 20.0, 0.9, 0.05)
    vazba = _noise_mat("vazba_kuze", (0.35, 0.12, 0.08), (0.2, 0.06, 0.04), 30.0, 0.6, 0.3)
    for a in (0, math.pi / 2):
        o = _box((0, 0, 0.05), (0.6, 0.09, 0.1), dub, bevel=0.012)
        o.rotation_euler = (0, 0, a)
    _turned((0, 0, 0.1), [(0.0, 0.0), (0.06, 0.0), (0.05, 0.08), (0.04, 0.1), (0.045, 0.8), (0.06, 0.85), (0.0, 0.88)], dub, 12)
    tilt = math.radians(28)
    plate = _box((0, 0, 1.02), (0.55, 0.42, 0.03), dub, bevel=0.006)
    plate.rotation_euler = (tilt, 0, 0)
    lista = _box((0, -0.19 * math.cos(tilt), 1.02 - 0.19 * math.sin(tilt) + 0.025), (0.55, 0.02, 0.04), dub, bevel=0.004)
    lista.rotation_euler = (tilt, 0, 0)
    # otevrena kniha: dve vypoukle stránky a desky
    for sx in (-1, 1):
        o = _box((sx * 0.13, 0, 1.055), (0.25, 0.34, 0.035), perg, bevel=0.012)
        o.rotation_euler = (tilt, sx * -0.06, 0)
        d = _box((sx * 0.135, 0, 1.037), (0.27, 0.36, 0.008), vazba, bevel=0.003)
        d.rotation_euler = (tilt, sx * -0.06, 0)
    return None


def book(name, col=(0.35, 0.12, 0.08)):
    """Zavrena kniha: kozena vazba s kovanymi rohy a sponami, ořízka listů."""
    vazba = _noise_mat("vazba_%d" % int(col[0] * 100), col, tuple(c * 0.55 for c in col), 30.0, 0.6, 0.3)
    perg = _noise_mat("pergamen_listy", (0.92, 0.86, 0.7), (0.8, 0.7, 0.52), 20.0, 0.9, 0.05)
    mosaz = _plain("mosaz", (0.75, 0.55, 0.25), 1.0, 0.35)
    _box((0, 0, 0.045), (0.24, 0.32, 0.07), perg, bevel=0.004)
    for z in (0.006, 0.084):
        _box((0.005, 0, z), (0.26, 0.335, 0.012), vazba, bevel=0.004)
    _box((-0.123, 0, 0.045), (0.02, 0.335, 0.09), vazba, bevel=0.008)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _box((sx * 0.11 + 0.005, sy * 0.15, 0.091), (0.04, 0.04, 0.004), mosaz, bevel=0.002)
    for sy in (-0.08, 0.08):
        _box((0.13, sy, 0.045), (0.012, 0.03, 0.095), mosaz, bevel=0.002)
    return None


def inkwell(name):
    """Kalamar s inkoustem a husim brkem, vedle popsany list."""
    hlina = _plain("kalamar", (0.15, 0.12, 0.1), 0.0, 0.4)
    brk = _plain("brk", (0.9, 0.88, 0.82), 0.0, 0.8)
    perg = _noise_mat("pergamen_listy", (0.92, 0.86, 0.7), (0.8, 0.7, 0.52), 20.0, 0.9, 0.05)
    _turned((0, 0, 0), [(0.0, 0.0), (0.04, 0.0), (0.045, 0.02), (0.035, 0.05), (0.015, 0.06), (0.018, 0.07), (0.0, 0.065)], hlina, 16)
    _handle((0.0, 0.0, 0.05), (0.07, 0.05, 0.28), 0.0025, brk, 0.001, 6)
    for k in range(10):
        t = 0.3 + 0.07 * k
        p = Vector((0.0, 0.0, 0.05)).lerp(Vector((0.07, 0.05, 0.28)), t)
        for sgn in (-1, 1):
            _box((p.x + sgn * 0.008, p.y - sgn * 0.004, p.z), (0.016, 0.002, 0.02), brk, bevel=0.0).rotation_euler = (0.2, -0.3, sgn * 0.5)
    _box((0.16, 0.0, 0.002), (0.2, 0.26, 0.002), perg, bevel=0.0)
    return None


def floor_candle(name):
    """Stojaci kovany svicen na podlahu: trojnozka, kroucený dřík, miska na vosk s bodcem a silnou svící."""
    fe = _plain("zelezo_kovane", (0.06, 0.055, 0.05), 0.75, 0.5)
    vosk = _plain("vosk", (0.9, 0.85, 0.7), 0.0, 0.6)
    for k in range(3):
        a = 2 * math.pi * k / 3
        cu = bpy.data.curves.new("noha", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for bp, co in zip(sp.bezier_points, [(0, 0, 0.25), (math.cos(a) * 0.15, math.sin(a) * 0.15, 0.06), (math.cos(a) * 0.24, math.sin(a) * 0.24, 0.01)]):
            bp.co = co
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cu.bevel_depth = 0.01
        ob = bpy.data.objects.new("noha", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(fe)
    for k in range(3):
        cu = bpy.data.curves.new("drat", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        n = 50
        sp.points.add(n - 1)
        for i, p_ in enumerate(sp.points):
            t = i / (n - 1)
            a = 2 * math.pi * k / 3 + t * 2 * math.pi * 6
            p_.co = (math.cos(a) * 0.009, math.sin(a) * 0.009, 0.25 + 1.0 * t, 1)
        cu.bevel_depth = 0.006
        ob = bpy.data.objects.new("drat", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(fe)
    _turned((0, 0, 1.25), [(0.0, 0.0), (0.02, 0.0), (0.09, 0.03), (0.1, 0.045), (0.085, 0.04), (0.0, 0.03)], fe, 20)
    _turned((0, 0, 1.28), [(0.0, 0.0), (0.035, 0.0), (0.034, 0.22), (0.028, 0.24), (0.0, 0.245)], vosk, 16)
    return None


def cradle(name):
    """Dubova kolebka na ohnutych ližinách, bočnice z prken, v ní lněná peřinka."""
    jasan, dub, fe, ocel, provaz = _woods()
    plat = _noise_mat("platno", (0.86, 0.82, 0.74), (0.7, 0.66, 0.58), 90.0, 0.9, 0.2)
    for sx in (-1, 1):
        cu = bpy.data.curves.new("lizina", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for bp, co in zip(sp.bezier_points, [(sx * 0.32, -0.32, 0.12), (sx * 0.32, 0, 0.02), (sx * 0.32, 0.32, 0.12)]):
            bp.co = co
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cu.bevel_depth = 0.025
        ob = bpy.data.objects.new("lizina", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(dub)
    _box((0, 0, 0.17), (0.8, 0.42, 0.03), dub, bevel=0.005)
    for sy in (-1, 1):
        o = _box((0, sy * 0.22, 0.3), (0.82, 0.03, 0.26), dub, bevel=0.006)
        o.rotation_euler = (sy * 0.12, 0, 0)
    for sx in (-1, 1):
        _box((sx * 0.41, 0, 0.32 + (0.08 if sx > 0 else 0)), (0.03, 0.5, 0.32 + (0.16 if sx > 0 else 0)), dub, bevel=0.006)
    _blob((0, 0, 0.18), (0.36, 0.17, 0.06), plat, seed=13, wob=0.05)
    return None


def wagon_wheel(name):
    """Kolo od vozu: dubove louky (6), dvanact paprsku, náboj a kovana obruc."""
    jasan, dub, fe, ocel, provaz = _woods()
    R = 0.55
    c = (0, 0, 0.04)
    bpy.ops.mesh.primitive_torus_add(major_radius=R - 0.04, minor_radius=0.045, location=c, major_segments=48, minor_segments=8)
    o = bpy.context.object
    o.scale = (1, 1, 0.7)
    o.data.materials.append(dub)
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=0.012, location=c, major_segments=48, minor_segments=6)
    bpy.context.object.data.materials.append(fe)
    for k in range(12):
        a = 2 * math.pi * k / 12
        _handle((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.04), (math.cos(a) * (R - 0.06), math.sin(a) * (R - 0.06), 0.04), 0.02, jasan, 0.016, 8)
    _turned((0, 0, -0.03), [(0.0, 0.0), (0.07, 0.0), (0.1, 0.05), (0.1, 0.09), (0.07, 0.14), (0.03, 0.14), (0.0, 0.14)], dub, 16)
    for z in (0.005, 0.095):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.008, location=(0, 0, z))
        bpy.context.object.data.materials.append(fe)
    return None


def keg(name):
    """Soudek: dužky s ruznym odstinem, tri obruce, cep na boku, lezi na drevenem kozlíku."""
    jasan, dub, fe, ocel, provaz = _woods()
    R = random.Random(9)
    n = 16
    for k in range(n):
        a = 2 * math.pi * k / n
        m = _wood_mat("duzka%d" % (k % 3), "tram", (0.6 + 0.08 * (k % 3), 0.42, 0.28))
        bm = bmesh.new()
        prof = []
        for j in range(9):
            t = j / 8
            r = 0.17 + 0.035 * math.sin(math.pi * t)
            prof.append((r, -0.24 + 0.48 * t))
        rows = []
        w = math.pi / n * 0.97
        for r, x in prof:
            rows.append([bm.verts.new((x, math.cos(a + s_) * r, 0.25 + math.sin(a + s_) * r)) for s_ in (-w, w)] +
                        [bm.verts.new((x, math.cos(a + s_) * (r - 0.015), 0.25 + math.sin(a + s_) * (r - 0.015))) for s_ in (w, -w)])
        for p_, q_ in zip(rows, rows[1:]):
            for i in range(4):
                bm.faces.new((p_[i], p_[(i + 1) % 4], q_[(i + 1) % 4], q_[i]))
        me = bpy.data.meshes.new("duzka")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m)
        o = bpy.data.objects.new("duzka", me)
        bpy.context.scene.collection.objects.link(o)
    for x in (-0.2, -0.08, 0.08, 0.2):
        r = 0.17 + 0.035 * math.sin(math.pi * (x + 0.24) / 0.48) + 0.004
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.006, location=(x, 0, 0.25), rotation=(0, math.pi / 2, 0))
        bpy.context.object.data.materials.append(fe)
    for x in (-0.24, 0.24):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.165, depth=0.02, location=(x, 0, 0.25), rotation=(0, math.pi / 2, 0))
        bpy.context.object.data.materials.append(dub)
    _handle((0.24, 0, 0.18), (0.32, 0, 0.18), 0.012, dub, 0.01, 8)
    for x in (-0.15, 0.15):
        o = _box((x, 0, 0.05), (0.06, 0.4, 0.1), dub, bevel=0.008)
    return None


BUILD.update({
    "bochnik": lambda: bread("bochnik"),
    "pecen": lambda: bread("pecen", True),
    "syr": lambda: cheese("syr"),
    "kosnice": lambda: skep("kosnice"),
    "pytel_obili": lambda: sack("pytel_obili"),
    "pytel_mouky": lambda: sack("pytel_mouky", True),
    "kupka_sena": lambda: haystack("kupka_sena"),
    "kotlik_trojnozka": lambda: cauldron_tripod("kotlik_trojnozka"),
    "korbel": lambda: tankard("korbel"),
    "venec_cibule": lambda: braid("venec_cibule", "cibule"),
    "venec_cesneku": lambda: braid("venec_cesneku", "cesnek"),
    "byliny": lambda: herbs("byliny"),
    "barbuta": lambda: barbute("barbuta"),
    "klobouk_zelezny": lambda: kettle_hat("klobouk_zelezny"),
    "kosile_kruzkova": lambda: mail_stand("kosile_kruzkova"),
    "kuse": lambda: crossbow("kuse"),
    "luk_toulec": lambda: bow_quiver("luk_toulec"),
    "pult_kniha": lambda: lectern("pult_kniha"),
    "kniha": lambda: book("kniha"),
    "kniha_modra": lambda: book("kniha_modra", (0.1, 0.16, 0.35)),
    "kalamar": lambda: inkwell("kalamar"),
    "svicen_stojaci": lambda: floor_candle("svicen_stojaci"),
    "kolebka": lambda: cradle("kolebka"),
    "kolo_vozu": lambda: wagon_wheel("kolo_vozu"),
    "soudek": lambda: keg("soudek"),
})


# ======================================================================= jidlo a piti

def _pecene():
    return _noise_mat("pecene_maso", (0.55, 0.28, 0.1), (0.25, 0.1, 0.03), 22.0, 0.35, 0.6)


def chicken_leg(name):
    """Pecene kureci stehno: zlatohneda kurcicka s vypouklinami, svetla kost s kloubem."""
    kost = _plain("kost", (0.88, 0.84, 0.74), 0.0, 0.5)
    o = _blob((0, 0, 0), (0.07, 0.05, 0.04), _pecene(), seed=21, wob=0.08)
    o.location = (0.0, 0, 0)
    _handle((0.06, 0, 0.04), (0.16, 0, 0.035), 0.011, kost, 0.009, 10)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=(0.165, 0, 0.035), segments=10, ring_count=6)
    bpy.context.object.data.materials.append(kost)
    return None


def roast_chicken(name):
    """Pecene kure na drevenem prkenku: trup, stehna, kridla, vedle par plátků cibule a bylinky."""
    jasan, dub, fe, ocel, provaz = _woods()
    _box((0, 0, 0.012), (0.42, 0.3, 0.024), dub, bevel=0.008)
    p = _pecene()
    _blob((0, 0, 0.024), (0.11, 0.085, 0.07), p, seed=31, wob=0.05)
    for sy in (-1, 1):
        _blob((0.07, sy * 0.08, 0.03), (0.06, 0.04, 0.04), p, seed=32 + sy, wob=0.08)
        _blob((-0.06, sy * 0.09, 0.06), (0.05, 0.025, 0.025), p, seed=34 + sy, wob=0.08)
    kost = _plain("kost", (0.88, 0.84, 0.74), 0.0, 0.5)
    for sy in (-1, 1):
        _handle((0.12, sy * 0.09, 0.05), (0.17, sy * 0.1, 0.06), 0.008, kost, 0.007, 8)
    zel = _plain("petrzel", (0.15, 0.35, 0.1), 0.0, 0.8)
    for k in range(6):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.012, location=(-0.15 + k * 0.012, -0.1 + (k % 2) * 0.02, 0.03))
        bpy.context.object.data.materials.append(zel)
    return None


def bacon(name):
    """Bok slaniny: vrstvy tuku a masa (textura v rezu), uzena kurka nahore, na provazku k pověšení."""
    W, H = 512, 256
    im = Image.new("RGB", (W, H), (230, 214, 190))
    d = ImageDraw.Draw(im)
    y = 0
    R = random.Random(3)
    while y < H:
        h = R.randint(12, 40)
        c = (150, 50, 40) if (y // 30) % 2 else (236, 220, 196)
        d.rectangle((0, y, W, y + h), fill=c)
        y += h
    d.rectangle((0, 0, W, 20), fill=(90, 40, 20))
    rez = _mat("slanina_rez", _save(im.filter(ImageFilter.GaussianBlur(2)), "slanina_rez"), 0.6)
    kura = _noise_mat("uzena_kura", (0.42, 0.2, 0.08), (0.22, 0.09, 0.03), 18.0, 0.5, 0.4)
    o = _box((0, 0, 0.04), (0.32, 0.18, 0.08), kura, bevel=0.012)
    for sx in (-1, 1):
        _box((sx * 0.161, 0, 0.04), (0.004, 0.17, 0.075), rez, bevel=0.0)
    jasan, dub, fe, ocel, provaz = _woods()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.004, location=(0.15, 0, 0.11), rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(provaz)
    return None


def ham(name):
    """Uzena sunka (kyta) s kosti, opalena kurka, provaz se smyckou."""
    kura = _noise_mat("uzena_kura", (0.42, 0.2, 0.08), (0.22, 0.09, 0.03), 18.0, 0.5, 0.4)
    kost = _plain("kost", (0.88, 0.84, 0.74), 0.0, 0.5)
    jasan, dub, fe, ocel, provaz = _woods()
    o = _blob((0, 0, 0), (0.17, 0.12, 0.09), kura, seed=41, wob=0.06)
    o.scale = (1, 1, 1)
    _handle((0.15, 0, 0.1), (0.3, 0, 0.12), 0.022, kura, 0.016, 12)
    _handle((0.29, 0, 0.12), (0.34, 0, 0.125), 0.014, kost, 0.016, 10)
    for x in (0.2, 0.24):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.004, location=(x, 0, 0.115), rotation=(0, math.pi / 2, 0))
        bpy.context.object.data.materials.append(provaz)
    return None


def sausages(name):
    """Venec uzenych klobas: oblouky stocene do kruhu, uvazane provazkem."""
    kl = _noise_mat("klobasa", (0.45, 0.16, 0.08), (0.25, 0.06, 0.03), 25.0, 0.3, 0.5)
    jasan, dub, fe, ocel, provaz = _woods()
    for k in range(6):
        a0 = 2 * math.pi * k / 6
        cu = bpy.data.curves.new("klobasa", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for j, bp in enumerate(sp.bezier_points):
            a = a0 + j * math.pi / 5.6
            bp.co = (math.cos(a) * 0.14, math.sin(a) * 0.14, 0.022 + 0.004 * j)
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cu.bevel_depth = 0.02
        cu.bevel_resolution = 3
        cu.use_fill_caps = True
        ob = bpy.data.objects.new("klobasa", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(kl)
        a = a0
        bpy.ops.mesh.primitive_torus_add(major_radius=0.012, minor_radius=0.003, location=(math.cos(a) * 0.14, math.sin(a) * 0.14, 0.022))
        bpy.context.object.data.materials.append(provaz)
    return None


def jerky_pouch(name):
    """Susene maso v plátěném pytlíku: pytlik stazeny provazkem, z otvoru vykukuji tmave pruhy masa."""
    pyt = _noise_mat("pytlik", (0.72, 0.64, 0.5), (0.5, 0.43, 0.32), 110.0, 0.95, 0.4)
    maso = _noise_mat("susene_maso", (0.35, 0.12, 0.06), (0.15, 0.04, 0.02), 30.0, 0.6, 0.6)
    jasan, dub, fe, ocel, provaz = _woods()
    _blob((0, 0, 0), (0.09, 0.08, 0.1), pyt, seed=51, wob=0.08)
    R = random.Random(7)
    for k in range(5):
        a = R.uniform(0, 6.28)
        o = _box((math.cos(a) * 0.02, math.sin(a) * 0.02, 0.2), (0.025, 0.006, 0.09), maso, bevel=0.003)
        o.rotation_euler = (R.uniform(-0.4, 0.4), R.uniform(-0.4, 0.4), a)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.006, location=(0, 0, 0.17))
    bpy.context.object.data.materials.append(provaz)
    for k in range(3):
        a = 0.6 + k * 1.1
        o = _box((0.14 + k * 0.04, -0.05 + k * 0.04, 0.008), (0.09, 0.025, 0.006), maso, bevel=0.003)
        o.rotation_euler = (0, 0, a)
    return None


def smoked_fish(name):
    """Uzena ryba (kapr): zlatohneda kůže s šupinami, hlava, ocas a ploutve, na lnenem plátne."""
    kuze = _noise_mat("ryba_kuze", (0.7, 0.45, 0.15), (0.4, 0.22, 0.06), 70.0, 0.3, 0.5)
    plat = _noise_mat("platno", (0.86, 0.82, 0.74), (0.7, 0.66, 0.58), 90.0, 0.9, 0.2)
    _box((0, 0, 0.003), (0.5, 0.3, 0.006), plat, bevel=0.002)
    o = _blob((0, 0, 0.006), (0.16, 0.05, 0.06), kuze, seed=61, wob=0.03)
    bm = bmesh.new()
    pts = [(0.15, 0, 0.04), (0.24, 0.0, 0.1), (0.24, 0.0, -0.0)]
    vs = [bm.verts.new(p) for p in pts]
    bm.faces.new(vs)
    me = bpy.data.meshes.new("ocas")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(kuze)
    t = bpy.data.objects.new("ocas", me)
    bpy.context.scene.collection.objects.link(t)
    t.location = (0, 0, 0.012)
    so = t.modifiers.new("t", "SOLIDIFY")
    so.thickness = 0.004
    oko = _plain("oko", (0.05, 0.04, 0.03), 0.0, 0.2)
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.007, location=(-0.12, sy * 0.03, 0.05), segments=8, ring_count=5)
        bpy.context.object.data.materials.append(oko)
    return None


def egg_basket(name):
    """Prouteny kosik s vejci na slame."""
    proutky = _noise_mat("proutky", (0.55, 0.4, 0.22), (0.32, 0.22, 0.1), 60.0, 0.85, 0.7)
    vejce = _plain("vejce", (0.86, 0.74, 0.58), 0.0, 0.6)
    slama = _noise_mat("seno", (0.55, 0.5, 0.22), (0.32, 0.3, 0.12), 50.0, 0.95, 0.8)
    _turned((0, 0, 0), [(0.0, 0.0), (0.1, 0.0), (0.13, 0.04), (0.15, 0.1), (0.14, 0.1), (0.12, 0.045), (0.0, 0.02)], proutky, 24)
    for z in (0.03, 0.06, 0.09):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.11 + z * 0.35, minor_radius=0.005, location=(0, 0, z))
        bpy.context.object.data.materials.append(proutky)
    cu = bpy.data.curves.new("ucho", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(-0.14, 0, 0.1), (0, 0, 0.3), (0.14, 0, 0.1)]):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.009
    o = bpy.data.objects.new("ucho", cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(proutky)
    _blob((0, 0, 0.03), (0.12, 0.12, 0.03), slama, seed=71, wob=0.1)
    R = random.Random(5)
    for k in range(7):
        a = 2 * math.pi * k / 7
        r = 0.06 if k else 0.0
        o = _blob((0, 0, 0), (0.022, 0.022, 0.03), vejce, seg=12, rings=8, seed=k, wob=0.0, flat_bottom=False)
        o.rotation_euler = (R.uniform(-1.2, 1.2), R.uniform(-1.2, 1.2), 0)
        o.location = (math.cos(a) * r, math.sin(a) * r, 0.075 if k else 0.085)
    return None


def honey_pot(name):
    """Hlineny hrnec s medem: hnědá glazura, plátěné víko převázané provázkem, dřevěná lžíce s kapkou medu."""
    hlina = _noise_mat("hlina_glazura", (0.42, 0.24, 0.1), (0.25, 0.12, 0.05), 10.0, 0.25, 0.1)
    plat = _noise_mat("platno", (0.86, 0.82, 0.74), (0.7, 0.66, 0.58), 90.0, 0.9, 0.2)
    jasan, dub, fe, ocel, provaz = _woods()
    _turned((0, 0, 0), [(0.0, 0.0), (0.06, 0.0), (0.09, 0.05), (0.095, 0.1), (0.075, 0.15), (0.07, 0.165), (0.078, 0.17), (0.0, 0.17)], hlina, 24)
    _blob((0, 0, 0.165), (0.09, 0.09, 0.02), plat, seed=81, wob=0.1, flat_bottom=False)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.073, minor_radius=0.004, location=(0, 0, 0.158))
    bpy.context.object.data.materials.append(provaz)
    return None


def bowl_food(name, kind="kase"):
    """Dřevěná miska s kaší (jahelná se šlehačkou másla) nebo polévkou (s kousky zeleniny), lžíce na okraji."""
    jasan, dub, fe, ocel, provaz = _woods()
    _turned((0, 0, 0), [(0.0, 0.0), (0.05, 0.0), (0.055, 0.01), (0.1, 0.05), (0.11, 0.07), (0.1, 0.07), (0.09, 0.05), (0.0, 0.03)], dub, 28)
    if kind == "kase":
        obsah = _noise_mat("kase", (0.9, 0.78, 0.45), (0.75, 0.6, 0.3), 30.0, 0.7, 0.4)
        _blob((0, 0, 0.035), (0.088, 0.088, 0.02), obsah, seed=91, wob=0.05)
        _blob((0, 0, 0.058), (0.02, 0.02, 0.008), _plain("maslo", (0.98, 0.88, 0.5), 0.0, 0.3), seed=92, wob=0.1)
    else:
        obsah = _plain("polevka", (0.55, 0.32, 0.12), 0.0, 0.15)
        _turned((0, 0, 0.05), [(0.0, 0.0), (0.094, 0.0), (0.0, 0.0005)], obsah, 28)
        R = random.Random(3)
        for k in range(9):
            a, r = R.uniform(0, 6.28), R.uniform(0, 0.07)
            c = [(0.85, 0.45, 0.1), (0.3, 0.5, 0.15), (0.92, 0.88, 0.7)][k % 3]
            o = _box((math.cos(a) * r, math.sin(a) * r, 0.052), (0.014, 0.014, 0.008), _plain("zel%d" % (k % 3), c, 0.0, 0.5), bevel=0.002)
    _handle((0.0, 0.0, 0.06), (0.17, 0.06, 0.09), 0.006, jasan, 0.005, 8)
    _blob((0.0, 0.0, 0.055), (0.025, 0.018, 0.008), jasan, seed=93, wob=0.0, flat_bottom=False)
    return None


def nuts_bowl(name, kind="orechy"):
    """Miska s ořechy nebo hruskami."""
    jasan, dub, fe, ocel, provaz = _woods()
    _turned((0, 0, 0), [(0.0, 0.0), (0.06, 0.0), (0.12, 0.04), (0.14, 0.06), (0.13, 0.06), (0.11, 0.04), (0.0, 0.02)], dub, 28)
    R = random.Random(4)
    if kind == "orechy":
        m = _noise_mat("orech", (0.55, 0.4, 0.22), (0.35, 0.24, 0.12), 45.0, 0.7, 0.8)
        for k in range(22):
            a, r = R.uniform(0, 6.28), math.sqrt(R.random()) * 0.1
            _blob((math.cos(a) * r, math.sin(a) * r, 0.03 + R.uniform(0, 0.03)), (0.017, 0.017, 0.016), m, seg=10, rings=6, seed=k, wob=0.1,
                  flat_bottom=False)
    else:
        m = _noise_mat("hruska", (0.72, 0.65, 0.2), (0.45, 0.4, 0.1), 15.0, 0.4, 0.2)
        for k in range(5):
            a, r = 2 * math.pi * k / 5, 0.06
            o = _turned((math.cos(a) * r, math.sin(a) * r, 0.03), [(0.0, 0.0), (0.03, 0.01), (0.035, 0.035), (0.022, 0.06), (0.016, 0.085),
                                                                   (0.0, 0.095)], m, 14)
            o.rotation_euler = (R.uniform(-0.6, 0.6), R.uniform(-0.6, 0.6), 0)
    return None


def _glass(name, col, alpha=0.55):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Alpha"].default_value = alpha
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    return m


def wine_bottle(name):
    """Lahev vina z lesniho skla (zelenkava, s bublinkami), korkova zatka zapecetena voskem; vino uvnitr."""
    sklo = _glass("lesni_sklo", (0.35, 0.5, 0.25), 0.6)
    vino = _plain("vino", (0.25, 0.02, 0.04), 0.0, 0.1)
    vosk = _plain("pecet", (0.6, 0.05, 0.04), 0.0, 0.4)
    _turned((0, 0, 0), [(0.0, 0.0), (0.06, 0.0), (0.075, 0.03), (0.08, 0.1), (0.07, 0.16), (0.03, 0.2), (0.018, 0.26), (0.022, 0.27),
                       (0.018, 0.28), (0.0, 0.28)], sklo, 24)
    _turned((0, 0, 0.005), [(0.0, 0.0), (0.06, 0.0), (0.072, 0.03), (0.075, 0.1), (0.065, 0.14), (0.0, 0.14)], vino, 20)
    _turned((0, 0, 0.27), [(0.0, 0.0), (0.024, 0.0), (0.026, 0.02), (0.02, 0.03), (0.0, 0.03)], vosk, 14)
    return None


def wine_jug(name):
    """Kameninovy dzban na vino se zdobnym pásem a uchem."""
    kamenina = _noise_mat("kamenina", (0.62, 0.52, 0.4), (0.42, 0.33, 0.24), 12.0, 0.35, 0.2)
    _turned((0, 0, 0), [(0.0, 0.0), (0.07, 0.0), (0.1, 0.06), (0.11, 0.13), (0.085, 0.21), (0.05, 0.26), (0.06, 0.3), (0.055, 0.3),
                       (0.045, 0.26), (0.0, 0.25)], kamenina, 28)
    cu = bpy.data.curves.new("ucho", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(0.05, 0, 0.27), (0.14, 0, 0.22), (0.1, 0, 0.12)]):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.012
    o = bpy.data.objects.new("ucho", cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(kamenina)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.106, minor_radius=0.004, location=(0, 0, 0.14))
    bpy.context.object.data.materials.append(_plain("pruh_dzban", (0.3, 0.18, 0.1), 0.0, 0.4))
    return None


def demijohn(name):
    """Opleteny demizon (balon) na vino: sklo v proutěném opletu, ucha, zatka."""
    proutky = _noise_mat("proutky", (0.55, 0.4, 0.22), (0.32, 0.22, 0.1), 60.0, 0.85, 0.7)
    sklo = _glass("lesni_sklo", (0.35, 0.5, 0.25), 0.6)
    _turned((0, 0, 0), [(0.0, 0.0), (0.14, 0.0), (0.2, 0.08), (0.21, 0.22), (0.16, 0.36), (0.05, 0.42), (0.03, 0.5), (0.0, 0.5)], sklo, 28)
    for k in range(9):
        z = 0.02 + k * 0.035
        r = [0.15, 0.18, 0.2, 0.21, 0.21, 0.21, 0.2, 0.19, 0.17][k] + 0.008
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.012, location=(0, 0, z), major_segments=36, minor_segments=6)
        bpy.context.object.data.materials.append(proutky)
    for a in (0, math.pi):
        cu = bpy.data.curves.new("ucho", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for bp, co in zip(sp.bezier_points, [(math.cos(a) * 0.2, math.sin(a) * 0.2, 0.3), (math.cos(a) * 0.25, math.sin(a) * 0.25, 0.4),
                                             (math.cos(a) * 0.1, math.sin(a) * 0.1, 0.4)]):
            bp.co = co
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cu.bevel_depth = 0.012
        o = bpy.data.objects.new("ucho", cu)
        bpy.context.scene.collection.objects.link(o)
        o.data.materials.append(proutky)
    _handle((0, 0, 0.49), (0, 0, 0.55), 0.024, _plain("korek", (0.6, 0.45, 0.3), 0.0, 0.9), 0.026, 12)
    return None


def spirits(name):
    """Kořalka: mala placata baňka z čirého skla s cínovou zátkou, uvnitř jantarová pálenka, vedle cínový pohárek."""
    sklo = _glass("cire_sklo", (0.85, 0.9, 0.88), 0.35)
    palenka = _plain("palenka", (0.75, 0.45, 0.1), 0.0, 0.1)
    cin = _plain("cin", (0.6, 0.6, 0.6), 0.9, 0.35)
    o = _turned((0, 0, 0), [(0.0, 0.0), (0.04, 0.0), (0.05, 0.03), (0.05, 0.1), (0.03, 0.13), (0.012, 0.15), (0.0, 0.15)], sklo, 20)
    o.scale = (1.0, 0.55, 1.0)
    o = _turned((0, 0, 0.004), [(0.0, 0.0), (0.042, 0.0), (0.046, 0.03), (0.046, 0.07), (0.0, 0.07)], palenka, 18)
    o.scale = (1.0, 0.5, 1.0)
    _turned((0, 0, 0.15), [(0.0, 0.0), (0.016, 0.0), (0.016, 0.025), (0.0, 0.03)], cin, 12)
    _turned((0.1, 0.0, 0), [(0.0, 0.0), (0.02, 0.0), (0.022, 0.005), (0.006, 0.01), (0.006, 0.03), (0.022, 0.06), (0.018, 0.06), (0.0, 0.04)],
            cin, 16)
    return None


def beer_tankard(name):
    """Korbel piva s pěnou: dřevěný korbel s obručemi, pivo a pěna přes okraj."""
    tankard(name)
    pena = _noise_mat("pena", (0.96, 0.93, 0.85), (0.85, 0.8, 0.7), 60.0, 0.8, 0.4)
    _blob((0, 0, 0.145), (0.058, 0.058, 0.02), pena, seed=101, wob=0.12, flat_bottom=False)
    # vicko otevrene (odlozene stranou) - puvodni vicko nechat, je soucasti korbelu
    return None


def waterskin(name):
    """Kozeny mech na vodu: bachraty vak se švem, rohové hrdlo se zátkou, popruh."""
    kuze = _noise_mat("mech_kuze", (0.42, 0.26, 0.12), (0.22, 0.12, 0.05), 35.0, 0.55, 0.5)
    roh = _plain("roh", (0.82, 0.74, 0.58), 0.0, 0.4)
    jasan, dub, fe, ocel, provaz = _woods()
    _blob((0, 0, 0), (0.17, 0.11, 0.07), kuze, seed=111, wob=0.06)
    _handle((0.15, 0, 0.05), (0.22, 0, 0.07), 0.02, roh, 0.014, 12)
    _handle((0.22, 0, 0.07), (0.24, 0, 0.075), 0.012, _plain("korek", (0.6, 0.45, 0.3), 0.0, 0.9), 0.012, 10)
    cu = bpy.data.curves.new("popruh", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(-0.15, 0, 0.06), (0.0, -0.2, 0.01), (0.15, 0, 0.07)]):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = 0.006
    o = bpy.data.objects.new("popruh", cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(kuze)
    return None


BUILD.update({
    "kureci_stehno": lambda: chicken_leg("kureci_stehno"),
    "pecene_kure": lambda: roast_chicken("pecene_kure"),
    "slanina": lambda: bacon("slanina"),
    "sunka": lambda: ham("sunka"),
    "klobasy": lambda: sausages("klobasy"),
    "susene_maso": lambda: jerky_pouch("susene_maso"),
    "uzena_ryba": lambda: smoked_fish("uzena_ryba"),
    "vejce_kosik": lambda: egg_basket("vejce_kosik"),
    "med": lambda: honey_pot("med"),
    "kase": lambda: bowl_food("kase", "kase"),
    "polevka": lambda: bowl_food("polevka", "polevka"),
    "orechy": lambda: nuts_bowl("orechy", "orechy"),
    "hrusky": lambda: nuts_bowl("hrusky", "hrusky"),
    "vino_lahev": lambda: wine_bottle("vino_lahev"),
    "vino_dzban": lambda: wine_jug("vino_dzban"),
    "demizon": lambda: demijohn("demizon"),
    "koralka": lambda: spirits("koralka"),
    "pivo": lambda: beer_tankard("pivo"),
    "voda_mech": lambda: waterskin("voda_mech"),
})


# ------------------------------------------------------------------ jidlo 3: zelenina, houby, syrove maso, raci (KCD2)

def _cap_shell(rad, keep_z, mat, seg=20, rings=12):
    """Vyrez koule (kalota) se stredem v pocatku: list zeli, klobouk houby."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=1.0, location=(0, 0, 0))
    o = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < keep_z], context="VERTS")
    for v in bm.verts:
        v.co = Vector((v.co.x * rad[0], v.co.y * rad[1], v.co.z * rad[2]))
    bm.to_mesh(o.data)
    bm.free()
    o.data.materials.append(mat)
    so = o.modifiers.new("t", "SOLIDIFY")
    so.thickness = 0.004
    bpy.ops.object.shade_smooth()
    return o


def _veins_img(name, base, vein, W=512, seed=1, n=40):
    """List s zilkami: svetle zilky z dolniho okraje vzhuru (UV koule: v = vyska)."""
    R = random.Random(seed)
    im = Image.open(_noise_img(name + "_z", base, tuple(c * 0.8 for c in base), 30.0, seed)).convert("RGB")
    d = ImageDraw.Draw(im)
    vc = tuple(int(c * 255) for c in vein)
    for k in range(n):
        x = R.uniform(0, W)
        pts = [(x, W)]
        for s in range(8):
            x += R.uniform(-14, 14)
            pts.append((x, W - (s + 1) * W / 8))
        d.line(pts, fill=vc, width=R.choice((2, 3, 4)))
        for (px, py) in pts[1:-1:2]:
            d.line([(px, py), (px + R.uniform(-40, 40), py - R.uniform(15, 50))], fill=vc, width=1)
    return _mat(name, _save(im, name), 0.55)


def cabbage(name):
    """Hlavka zeli: pevna svetla hlava, kolem nadvidle vnejsi listy se zilkami, cast odklopena, kousek kocanu."""
    hl = _veins_img("zeli_hlava", (0.72, 0.82, 0.5), (0.9, 0.95, 0.75), seed=3)
    vn = _veins_img("zeli_list", (0.32, 0.5, 0.22), (0.7, 0.8, 0.55), seed=5)
    _blob((0, 0, 0.015), (0.085, 0.085, 0.075), hl, seed=91, wob=0.03)
    R = random.Random(9)
    for k in range(9):
        a = 2 * math.pi * k / 9 + R.uniform(-0.2, 0.2)
        out = k % 3 == 0
        o = _cap_shell((0.11 + (0.03 if out else 0.0), 0.095, 0.1), -0.15 if not out else 0.0, vn, 18, 10)
        o.rotation_euler = (0, (1.25 if out else 0.55) + R.uniform(-0.1, 0.1), a)
        o.location = (math.cos(a) * 0.012, math.sin(a) * 0.012, 0.075 if not out else 0.03)
    _handle((0, 0, 0.02), (0, 0, -0.005), 0.018, _plain("kocan", (0.75, 0.8, 0.6), 0.0, 0.6), 0.016, 10)
    return None


def carrots(name):
    """Svazek mrkvi: stredoveke mrkve byly fialove a zlute (oranzova az v 17. st.), nať svazana provazkem."""
    jasan, dub, fe, ocel, provaz = _woods()
    fial = _noise_mat("mrkev_fialova", (0.36, 0.08, 0.22), (0.2, 0.04, 0.12), 60.0, 0.55, 0.4)
    zlut = _noise_mat("mrkev_zluta", (0.86, 0.66, 0.22), (0.62, 0.44, 0.12), 60.0, 0.55, 0.4)
    nat = _plain("mrkev_nat", (0.16, 0.36, 0.08), 0.0, 0.8)
    R = random.Random(13)
    for k in range(5):
        y = (k - 2) * 0.03
        z = 0.018 + (0.012 if k % 2 else 0.0)
        L = R.uniform(0.17, 0.22)
        m = fial if k % 2 == 0 else zlut
        _handle((0.0, y, z), (L, y + R.uniform(-0.03, 0.03), z - 0.008), 0.017, m, 0.002, 12)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.017, location=(0.0, y, z), segments=12, ring_count=6)
        bpy.context.object.data.materials.append(m)
        for j in range(5):
            a = (j - 2) * 0.22
            _handle((-0.005, y, z), (-0.16 - R.uniform(0, 0.06), y + math.sin(a) * 0.09, z + R.uniform(-0.01, 0.03)), 0.0035, nat, 0.0015, 5)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.005, location=(-0.04, 0, 0.03), rotation=(0, math.pi / 2, 0))
    bpy.context.object.scale = (1.0, 1.6, 0.6)
    bpy.context.object.data.materials.append(provaz)
    return None


def turnips(name):
    """Vodnice (repa): bila bulva s fialovou hlavou, tenky koren, ulomena nať; tri kusy."""
    W = 256
    im = Image.new("RGB", (W, W))
    d = ImageDraw.Draw(im)
    for y in range(W):
        t = y / W           # 0 = nahore obrazku = v 1 (vrch koule)
        k = min(1.0, max(0.0, (t - 0.3) / 0.15))
        c = tuple(int(255 * (a * (1 - k) + b * k)) for a, b in zip((0.45, 0.12, 0.35), (0.9, 0.88, 0.8)))
        d.line([(0, y), (W, y)], fill=c)
    R = random.Random(2)
    for k in range(300):
        x, y = R.uniform(0, W), R.uniform(0, W)
        d.point((x, y), fill=(120, 100, 90))
    bul = _mat("vodnice", _save(im, "vodnice"), 0.45)
    nat = _plain("vodnice_nat", (0.2, 0.4, 0.1), 0.0, 0.8)
    for k, (x, y, s) in enumerate(((0, 0, 1.0), (0.11, 0.05, 0.85), (0.04, -0.1, 0.75))):
        o = _blob((0, 0, 0), (0.05 * s, 0.05 * s, 0.045 * s), bul, seed=k, wob=0.03, flat_bottom=False)
        o.location = (x, y, 0.045 * s)
        _handle((x, y, 0.01 * s), (x + 0.03, y - 0.02, -0.0), 0.006 * s, bul, 0.001, 6)
        for j in range(4):
            a = j * 1.57 + k
            _handle((x, y, 0.085 * s), (x + math.cos(a) * 0.02, y + math.sin(a) * 0.02, 0.12 * s), 0.004, nat, 0.003, 5)
    return None


def horseradish(name):
    """Kren: tri kroucene bezove koreny s hrbolky a vedlejsimi korinky, hlava s ulomenou nati."""
    m = _noise_mat("kren", (0.72, 0.62, 0.45), (0.45, 0.36, 0.24), 70.0, 0.85, 0.8)
    rez = _plain("kren_rez", (0.92, 0.9, 0.82), 0.0, 0.6)
    nat = _plain("kren_nat", (0.25, 0.4, 0.12), 0.0, 0.8)
    R = random.Random(17)
    for k in range(3):
        y = (k - 1) * 0.045
        L = 0.24 + k * 0.03
        pts = [(0.0, y, 0.025)]
        for s in range(1, 5):
            pts.append((L * s / 4, y + R.uniform(-0.02, 0.02), 0.025 - s * 0.004))
        for s in range(4):
            r0 = 0.024 * (1 - s / 4.3)
            r1 = 0.024 * (1 - (s + 1) / 4.3)
            _handle(pts[s], pts[s + 1], r0, m, r1, 12)
            if s in (1, 2):
                _handle(pts[s + 1], (pts[s + 1][0] + 0.04, pts[s + 1][1] + R.choice((-1, 1)) * 0.04, 0.005), 0.004, m, 0.001, 5)
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.024, depth=0.004, location=(-0.001, y, 0.025), rotation=(0, math.pi / 2, 0))
        bpy.context.object.data.materials.append(rez if k == 0 else m)
        if k:
            _handle((0.0, y, 0.025), (-0.05, y, 0.04), 0.008, nat, 0.004, 6)
    return None


def porcini(name):
    """Hriby: bacate svetle trene se sitkou, hnedy lesknouci se klobouk, spodek klobouku zlutave rourky; tri kusy."""
    tren = _noise_mat("hrib_tren", (0.88, 0.84, 0.72), (0.7, 0.64, 0.5), 80.0, 0.8, 0.5)
    klob = _noise_mat("hrib_klobouk", (0.5, 0.3, 0.14), (0.3, 0.17, 0.07), 12.0, 0.35, 0.2)
    rour = _noise_mat("hrib_rourky", (0.9, 0.85, 0.6), (0.75, 0.7, 0.45), 120.0, 0.9, 0.5)
    for k, (x, y, s, tilt) in enumerate(((0, 0, 1.0, 0.0), (0.11, 0.04, 0.75, 0.15), (0.05, -0.09, 0.55, -0.2))):
        o = _turned((x, y, 0), [(0.0, 0.0), (0.028 * s, 0.0), (0.04 * s, 0.03 * s), (0.036 * s, 0.07 * s), (0.026 * s, 0.11 * s), (0.0, 0.11 * s)],
                    tren, 18)
        o.rotation_euler = (tilt, 0, 0)
        c = _cap_shell((0.075 * s, 0.075 * s, 0.05 * s), 0.0, klob, 22, 10)
        c.location = (x, y - tilt * 0.1 * s, 0.1 * s)
        c.rotation_euler = (tilt, 0, 0)
        bpy.ops.mesh.primitive_cylinder_add(vertices=22, radius=0.073 * s, depth=0.006 * s, location=(x, y - tilt * 0.1 * s, 0.101 * s), rotation=(tilt, 0, 0))
        bpy.context.object.data.materials.append(rour)
    return None


def parasol(name):
    """Bedla: vysoky stihly tren s hadim vzorem a prstenem, plochy klobouk s hrbolkem a hnedymi supinami, bile lupeny."""
    W = 512
    R = random.Random(23)
    im = Image.new("RGB", (W, W), (226, 214, 190))
    d = ImageDraw.Draw(im)
    for k in range(700):
        y = R.uniform(0, W * 0.75) ** 1.0
        x = R.uniform(0, W)
        r = 3 + 9 * (1 - y / W)
        d.ellipse((x - r * 1.6, y - r, x + r * 1.6, y + r), fill=(R.randint(110, 140), R.randint(80, 95), R.randint(55, 70)))
    d.rectangle((0, 0, W, W * 0.08), fill=(110, 82, 58))
    klob = _mat("bedla_klobouk", _save(im, "bedla_klobouk"), 0.85)
    im2 = Image.new("RGB", (W, W), (230, 222, 205))
    d2 = ImageDraw.Draw(im2)
    for y in range(0, W, 10):
        for x in range(0, W, 24):
            d2.arc((x - 12 + (y % 20), y - 4, x + 12 + (y % 20), y + 6), 0, 180, fill=(150, 120, 90), width=2)
    tren = _mat("bedla_tren", _save(im2, "bedla_tren"), 0.8)
    lup = _plain("bedla_lupeny", (0.94, 0.92, 0.86), 0.0, 0.7)
    for k, (x, y, s) in enumerate(((0, 0, 1.0), (0.14, 0.06, 0.7))):
        _turned((x, y, 0), [(0.0, 0.0), (0.024 * s, 0.0), (0.016 * s, 0.03 * s), (0.011 * s, 0.15 * s), (0.009 * s, 0.25 * s), (0.0, 0.25 * s)], tren, 14)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.016 * s, minor_radius=0.004 * s, location=(x, y, 0.2 * s))
        bpy.context.object.scale = (1, 1, 0.5)
        bpy.context.object.data.materials.append(lup)
        c = _cap_shell((0.12 * s, 0.12 * s, 0.045 * s), 0.0, klob, 28, 12)
        c.location = (x, y, 0.235 * s)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022 * s, location=(x, y, 0.275 * s), segments=12, ring_count=6)
        bpy.context.object.scale = (1, 1, 0.6)
        bpy.context.object.data.materials.append(klob)
        bpy.ops.mesh.primitive_cone_add(vertices=28, radius1=0.118 * s, radius2=0.012 * s, depth=0.02 * s, location=(x, y, 0.245 * s))
        bpy.context.object.data.materials.append(lup)
    return None


def braided_roll(name):
    """Houska: pleteny bilý rohlik ze tri prameny (kreslene kroucenou trojici), zlata kurka, posypana mákem."""
    kurka = _noise_mat("houska_kurka", (0.82, 0.55, 0.22), (0.55, 0.3, 0.1), 25.0, 0.5, 0.4)
    mak = _plain("mak", (0.08, 0.08, 0.1), 0.0, 0.6)
    L = 0.2
    R = random.Random(29)
    for k in range(3):
        cu = bpy.data.curves.new("pramen", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        n = 40
        sp.points.add(n - 1)
        for i, p_ in enumerate(sp.points):
            t = i / (n - 1)
            a = 2 * math.pi * k / 3 + t * 2 * math.pi * 1.6
            env = math.sin(math.pi * t) ** 0.5
            p_.co = ((t - 0.5) * L, math.cos(a) * 0.022 * env, 0.03 + math.sin(a) * 0.012 * env, 1)
        cu.bevel_depth = 0.022
        cu.bevel_resolution = 4
        cu.use_fill_caps = True
        sp.use_smooth = True
        o = bpy.data.objects.new("pramen", cu)
        bpy.context.scene.collection.objects.link(o)
        o.data.materials.append(kurka)
        tm = o.data
        # zuzeni na koncich
        for i, p_ in enumerate(sp.points):
            t = i / (n - 1)
            p_.radius = 0.45 + 0.55 * math.sin(math.pi * t)
    for k in range(45):
        t = R.uniform(0.15, 0.85)
        env = math.sin(math.pi * t) ** 0.5
        top = 0.03 + 0.012 * env + 0.022 * (0.45 + 0.55 * math.sin(math.pi * t)) - 0.002
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.0022, location=((t - 0.5) * L, R.uniform(-0.012, 0.012), top))
        bpy.context.object.data.materials.append(mak)
    return None


def _marbled_img(name, base, fat, W=512, seed=1, n=60):
    """Syrove maso: cervena svalovina s bilymi tukovymi zilkami (mramorovani)."""
    R = random.Random(seed)
    im = Image.open(_noise_img(name + "_z", base, tuple(c * 0.7 for c in base), 20.0, seed)).convert("RGB")
    d = ImageDraw.Draw(im)
    fc = tuple(int(c * 255) for c in fat)
    for k in range(n):
        x, y = R.uniform(0, W), R.uniform(0, W)
        pts = [(x, y)]
        for s in range(10):
            x += R.uniform(-12, 12)
            y += R.uniform(-12, 12)
            pts.append((x, y))
        d.line(pts, fill=fc, width=R.choice((1, 1, 2)))
    from PIL import ImageFilter
    im = im.filter(ImageFilter.GaussianBlur(1.6))
    return _mat(name, _save(im, name), 0.5)


def raw_beef(name):
    """Kus syroveho hoveziho na prkenku: mramorovana svalovina, tukova vrstva na hrbetu, plát odkrojený vedle."""
    jasan, dub, fe, ocel, provaz = _woods()
    _box((0, 0, 0.012), (0.36, 0.26, 0.024), dub, bevel=0.008)
    maso = _marbled_img("hovezi", (0.48, 0.07, 0.06), (0.92, 0.84, 0.76), seed=31, n=160)
    tuk = _noise_mat("lůj", (0.95, 0.9, 0.78), (0.8, 0.72, 0.58), 40.0, 0.5, 0.3)
    o = _blob((0, 0, 0.024), (0.11, 0.075, 0.06), maso, seed=41, wob=0.06)
    o.scale = (1, 1, 1)
    t = _cap_shell((0.1, 0.07, 0.06), 0.55, tuk, 22, 12)
    t.location = (0.0, 0.022, 0.03)
    t.rotation_euler = (0.9, 0, 0)
    s = _blob((0.0, 0.0, 0.0), (0.05, 0.035, 0.008), maso, seed=43, wob=0.08)
    s.location = (0.11, -0.07, 0.024)
    s.rotation_euler = (0, 0, 0.4)
    return None


def boar_leg(name, roast=False):
    """Kanci kyta: silne stehno zuzene k hlezenu, tmava hrubá kuze se stetinami, nahore rez (maso, bila kost),
    dole dva paznehty. Pecena: zlatohneda kurka na prkenku, kost vycniva."""
    jasan, dub, fe, ocel, provaz = _woods()
    if roast:
        _box((0.02, 0, 0.012), (0.62, 0.32, 0.024), dub, bevel=0.008)
        kuze = _pecene()
        z0 = 0.024
    else:
        kuze = _noise_mat("kanci_kuze", (0.25, 0.18, 0.13), (0.08, 0.06, 0.05), 140.0, 0.95, 0.9)
        z0 = 0.0
    maso = _marbled_img("kanci_maso", (0.45, 0.08, 0.07), (0.9, 0.82, 0.75), seed=37, n=30)
    kost = _plain("kost", (0.88, 0.84, 0.74), 0.0, 0.5)
    # stehno: soustruzeny profil polozeny na bok (osa x)
    prof = [(0.0, 0.0), (0.075, 0.0), (0.085, 0.06), (0.08, 0.13), (0.06, 0.2), (0.035, 0.27), (0.025, 0.32), (0.028, 0.36), (0.0, 0.37)]
    o = _turned((0, 0, 0), prof, kuze, 24)
    o.rotation_euler = (0, math.pi / 2, 0)
    o.scale = (0.8, 1.0, 1.0)
    o.location = (-0.18, 0, z0 + 0.068)
    # rez: maso a kost
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.072, depth=0.006, location=(-0.181, 0, z0 + 0.068), rotation=(0, math.pi / 2, 0))
    bpy.context.object.scale = (0.8, 1.0, 1.0)
    bpy.context.object.data.materials.append(maso)
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.016, depth=0.03 if roast else 0.01, location=(-0.19 if roast else -0.184, 0.01, z0 + 0.07),
                                        rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(kost)
    if roast:
        _handle((0.17, 0, z0 + 0.065), (0.27, 0, z0 + 0.07), 0.014, kost, 0.012, 10)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=(0.28, 0, z0 + 0.07), segments=12, ring_count=7)
        bpy.context.object.data.materials.append(kost)
    else:
        rohovina = _plain("paznehet", (0.05, 0.04, 0.035), 0.0, 0.45)
        for sy in (-1, 1):
            _handle((0.18, sy * 0.012, z0 + 0.065), (0.24, sy * 0.016, z0 + 0.03), 0.016, rohovina, 0.006, 8)
        # stetiny: kratke tmave osinky po hrbetu
        st = _plain("stetiny", (0.06, 0.05, 0.04), 0.0, 0.9)
        R = random.Random(43)
        for k in range(70):
            x = R.uniform(-0.17, 0.15)
            a = R.uniform(0.3, 2.8)
            rr = 0.07 * (1 - (x + 0.18) / 0.5) + 0.025
            p = (x, math.cos(a) * rr * 0.8, z0 + 0.068 + math.sin(a) * rr)
            _handle(p, (p[0] + 0.012, p[1] * 1.2, p[2] + 0.012), 0.0012, st, 0.0003, 3)
    return None


def hare(name):
    """Ulovený zajic polozeny na boku: sedohneda srst, bile bricho, dlouhe usi s cernymi spickami, natazene behy."""
    W = 512
    base = Image.open(_noise_img("zajic_srst_z", (0.55, 0.45, 0.32), (0.3, 0.24, 0.16), 160.0, 7)).convert("RGB")
    d = ImageDraw.Draw(base)
    for y in range(int(W * 0.62), W):
        k = min(1.0, (y - W * 0.62) / (W * 0.1))
        for x in range(0, W, 2):
            c = base.getpixel((x, y))
            nc = tuple(int(a * (1 - k) + b * k) for a, b in zip(c, (232, 226, 214)))
            d.line([(x, y), (x + 1, y)], fill=nc)
    srst = _mat("zajic_srst", _save(base, "zajic_srst"), 0.95)
    tma = _plain("zajic_spicky", (0.05, 0.04, 0.035), 0.0, 0.9)
    oko = _plain("oko", (0.05, 0.04, 0.03), 0.0, 0.2)
    # trup lezi na boku: osa x, telo zplostele v ose z
    o = _blob((0, 0, 0), (0.17, 0.075, 0.06), srst, seed=51, wob=0.05, flat_bottom=False)
    o.rotation_euler = (math.pi / 2, 0, 0)
    o.location = (0, 0, 0.06)
    h = _blob((0, 0, 0), (0.06, 0.04, 0.038), srst, seed=52, wob=0.03, flat_bottom=False)
    h.rotation_euler = (math.pi / 2, 0, -0.25)
    h.location = (0.2, 0.02, 0.05)
    for k, sz in enumerate((0.0, 0.025)):
        u = _blob((0, 0, 0), (0.07, 0.018, 0.005), srst, seed=53 + k, wob=0.05, flat_bottom=False)
        u.location = (0.13 - k * 0.005, 0.045 + k * 0.015, 0.07 + sz * 0.4)
        u.rotation_euler = (0, -0.1, -0.12 + k * 0.1)
        t = _blob((0, 0, 0), (0.016, 0.014, 0.0055), tma, seed=55 + k, flat_bottom=False)
        t.location = (0.07 - k * 0.005, 0.052 + k * 0.022, 0.075 + sz * 0.4)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=(0.225, 0.04, 0.075), segments=10, ring_count=6)
    bpy.context.object.data.materials.append(oko)
    # behy: predni kratke natazene dopredu, zadni dlouhe dozadu
    for sz in (0.035, 0.075):
        _handle((0.11, -0.035, sz), (0.24, -0.07, sz - 0.012), 0.011, srst, 0.007, 8)
        th = _blob((0, 0, 0), (0.07, 0.04, 0.025), srst, seed=int(sz * 100), wob=0.04, flat_bottom=False)
        th.location = (-0.11, -0.01, sz + 0.005)
        th.rotation_euler = (0, 0, 0.3)
        _handle((-0.16, -0.03, sz), (-0.3, -0.05, sz - 0.012), 0.013, srst, 0.008, 8)
    _blob((-0.17, 0.0, 0.07), (0.025, 0.025, 0.022), _plain("ocasek", (0.92, 0.9, 0.86), 0.0, 0.95), seed=56, flat_bottom=False)
    return None


def crayfish_plate(name):
    """Vareni raci na drevenem talíri: cervene krunyre (hlavohrud, clanky zadecku, klepeta), tykadla, kopr."""
    jasan, dub, fe, ocel, provaz = _woods()
    _turned((0, 0, 0), [(0.0, 0.0), (0.12, 0.0), (0.16, 0.015), (0.17, 0.024), (0.155, 0.024), (0.14, 0.014), (0.0, 0.01)], dub, 32)
    kr = _noise_mat("rak_krunyr", (0.82, 0.22, 0.08), (0.55, 0.1, 0.04), 50.0, 0.35, 0.5)
    kopr = _plain("kopr", (0.2, 0.42, 0.12), 0.0, 0.8)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        cx, cy = math.cos(a) * 0.055, math.sin(a) * 0.055
        dx, dy = math.cos(a + 1.9), math.sin(a + 1.9)

        def at(t, side=0.0, z=0.0):
            return (cx + dx * t - dy * side, cy + dy * t + dx * side, 0.024 + z)
        b = _blob((0, 0, 0), (0.035, 0.016, 0.014), kr, seed=60 + k, wob=0.03, flat_bottom=False)
        b.location = at(0.02, 0, 0.012)
        b.rotation_euler = (0, 0, a + 1.9)
        for s in range(5):
            t = -0.022 - s * 0.012
            seg = _blob((0, 0, 0), (0.008, 0.014 - s * 0.0015, 0.008), kr, seg=12, rings=6, seed=s, wob=0.0, flat_bottom=False)
            seg.location = at(t, 0, 0.01 - s * 0.0015)
            seg.rotation_euler = (0, 0, a + 1.9)
        f = _blob((0, 0, 0), (0.01, 0.018, 0.003), kr, seg=12, rings=6, seed=9, wob=0.05, flat_bottom=False)
        f.location = at(-0.084, 0, 0.003)
        f.rotation_euler = (0, 0, a + 1.9)
        for sd in (-1, 1):
            _handle(at(0.04, sd * 0.01, 0.01), at(0.065, sd * 0.03, 0.008), 0.005, kr, 0.006, 8)
            c = _blob((0, 0, 0), (0.022, 0.009, 0.006), kr, seg=12, rings=6, seed=sd + 3, wob=0.02, flat_bottom=False)
            c.location = at(0.085, sd * 0.034, 0.008)
            c.rotation_euler = (0, 0, a + 1.9 + sd * 0.25)
            _handle(at(0.04, sd * 0.004, 0.016), at(0.12, sd * 0.06, 0.006), 0.0012, kr, 0.0005, 4)
    for k in range(5):
        a = k * 1.3
        _handle((0.0, 0.0, 0.03), (math.cos(a) * 0.04, math.sin(a) * 0.04, 0.034), 0.002, kopr, 0.001, 4)
    return None


def mead(name):
    """Medovina: kamenina s medove hnedou glazurou, kulate bricho, dve ousky, zatka zalita voskem; vedle hlinena cise."""
    glaz = _noise_mat("medovina_glazura", (0.55, 0.32, 0.1), (0.3, 0.16, 0.05), 14.0, 0.18, 0.1)
    vosk = _plain("vosk_pecet", (0.55, 0.08, 0.05), 0.0, 0.45)
    hl = _noise_mat("hlina_cise", (0.62, 0.42, 0.28), (0.45, 0.28, 0.18), 30.0, 0.8, 0.3)
    _turned((0, 0, 0), [(0.0, 0.0), (0.05, 0.0), (0.085, 0.04), (0.09, 0.09), (0.07, 0.15), (0.03, 0.19), (0.024, 0.24), (0.03, 0.25), (0.0, 0.25)], glaz, 28)
    _turned((0, 0, 0.245), [(0.0, 0.0), (0.028, 0.0), (0.03, 0.012), (0.018, 0.022), (0.0, 0.024)], vosk, 16)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.025, minor_radius=0.007, location=(sx * 0.06, 0, 0.17), rotation=(math.pi / 2, 0, 0))
        bpy.context.object.data.materials.append(glaz)
    _turned((0.15, 0.03, 0), [(0.0, 0.0), (0.025, 0.0), (0.03, 0.01), (0.04, 0.06), (0.044, 0.08), (0.038, 0.08), (0.034, 0.062), (0.022, 0.012), (0.0, 0.01)],
            hl, 22)
    med = _plain("medovina", (0.55, 0.3, 0.05), 0.0, 0.1)
    bpy.ops.mesh.primitive_cylinder_add(vertices=22, radius=0.036, depth=0.002, location=(0.15, 0.03, 0.065))
    bpy.context.object.data.materials.append(med)
    return None


def cinnamon(name):
    """Svazek skorice: stocene kury (dutinky), prevazane lnenou snurou."""
    jasan, dub, fe, ocel, provaz = _woods()
    sk = _noise_mat("skorice", (0.55, 0.3, 0.15), (0.35, 0.17, 0.08), 90.0, 0.8, 0.6)
    R = random.Random(71)
    for k in range(7):
        a = 2 * math.pi * k / 7
        r = 0.014 if k else 0.0
        o = _turned((0, 0, 0), [(0.0055, 0.0), (0.0065, 0.0), (0.0065, 0.14), (0.0055, 0.14)], sk, 12)
        o.rotation_euler = (0, math.pi / 2, 0)
        o.location = (-0.07 + R.uniform(-0.008, 0.008), math.cos(a) * r, 0.022 + math.sin(a) * r)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.023, minor_radius=0.003, location=(0, 0, 0.022), rotation=(0, math.pi / 2, 0))
    bpy.context.object.data.materials.append(provaz)
    return None


BUILD.update({
    "zeli": lambda: cabbage("zeli"),
    "mrkev": lambda: carrots("mrkev"),
    "vodnice": lambda: turnips("vodnice"),
    "kren": lambda: horseradish("kren"),
    "hriby": lambda: porcini("hriby"),
    "bedly": lambda: parasol("bedly"),
    "houska": lambda: braided_roll("houska"),
    "hovezi": lambda: raw_beef("hovezi"),
    "kanci_kyta": lambda: boar_leg("kanci_kyta"),
    "kanci_pecene": lambda: boar_leg("kanci_pecene", True),
    "raci": lambda: crayfish_plate("raci"),
    "medovina": lambda: mead("medovina"),
    "skorice": lambda: cinnamon("skorice"),
})


def wash_tub(name):
    """Velka kad s vodou (jako v KCD na myti): 26 dubovych duzek ruzne vysokych a otlucenych nahore, mirne se rozsiruje
    vzhuru, dve sirsi drevene/zelezne obruce, uvnitr hladina vody s jemnou vlnkou, dno."""
    jasan, dub, fe, ocel, provaz = _woods()
    R = random.Random(41)
    n = 26
    H = 0.82
    r0, r1 = 0.5, 0.56
    th = 0.035
    for k in range(n):
        a = 2 * math.pi * k / n
        m = _wood_mat("kad_duzka%d" % (k % 4), "tram", (0.5 + 0.06 * (k % 4), 0.4 + 0.02 * (k % 2), 0.3))
        top = H + R.uniform(-0.05, 0.03) + (0.06 if k % 7 == 3 else 0.0)
        w = math.pi / n * 0.985
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        rows = []
        steps = 6
        for j in range(steps + 1):
            t = j / steps
            z = top * t
            r = r0 + (r1 - r0) * t + 0.012 * math.sin(math.pi * t)
            # otluceny horni okraj: posledni rada sikmo a s vyrezem
            dz = (R.uniform(-0.03, 0.0), R.uniform(-0.03, 0.0)) if j == steps else (0.0, 0.0)
            rows.append([bm.verts.new((math.cos(a - w) * r, math.sin(a - w) * r, z + dz[0])),
                         bm.verts.new((math.cos(a + w) * r, math.sin(a + w) * r, z + dz[1])),
                         bm.verts.new((math.cos(a + w) * (r - th), math.sin(a + w) * (r - th), z + dz[1])),
                         bm.verts.new((math.cos(a - w) * (r - th), math.sin(a - w) * (r - th), z + dz[0]))])
        for p_, q_ in zip(rows, rows[1:]):
            for i in range(4):
                f = bm.faces.new((p_[i], p_[(i + 1) % 4], q_[(i + 1) % 4], q_[i]))
                for l in f.loops:
                    l[uv].uv = ((i + (1 if l.vert in (p_[(i + 1) % 4], q_[(i + 1) % 4]) else 0)) * 0.03 + k * 0.17, l.vert.co.z * 1.1)
        f = bm.faces.new(rows[-1][::-1])
        for l in f.loops:
            l[uv].uv = (l.vert.co.x, l.vert.co.y)
        me = bpy.data.meshes.new("duzka")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m)
        o = bpy.data.objects.new("duzka", me)
        bpy.context.scene.collection.objects.link(o)
    # obruce: dve ploche vrstvene pasy (dole a nahore)
    for z, h in ((0.12, 0.06), (0.62, 0.06)):
        t = z / H
        r = r0 + (r1 - r0) * t + 0.012 * math.sin(math.pi * t)
        o = _turned((0, 0, z), [(r + 0.002, 0.0), (r + 0.012, 0.004), (r + 0.012, h - 0.004), (r + 0.002, h), (r - 0.01, h), (r - 0.01, 0.0)], fe, 48)
    # dno
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r0 - 0.02, depth=0.04, location=(0, 0, 0.06))
    bpy.context.object.data.materials.append(dub)
    # voda: hladina s drobnymi vlnkami, tmave zelenomodra, leskla
    voda = _plain("voda_kad", (0.08, 0.12, 0.12), 0.0, 0.05)
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.0, fill_type="TRIFAN", location=(0, 0, 0))
    o = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
    zw = 0.66
    rw = r0 + (r1 - r0) * zw / H - th + 0.006
    for v in bm.verts:
        x, y = v.co.x * rw, v.co.y * rw
        v.co = Vector((x, y, zw + 0.004 * math.sin(x * 23) * math.sin(y * 19)))
    bm.to_mesh(o.data)
    bm.free()
    o.data.materials.append(voda)
    bpy.ops.object.shade_smooth()
    return None


BUILD.update({"kad": lambda: wash_tub("kad")})


# ------------------------------------------------------------------ bozi muka (krizovatka u vesnice)

def _quad(name, corners, mat):
    """Ctyruhelnik s UV 0..1 (obrazek v nike)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new(c) for c in corners]
    f = bm.faces.new(vs)
    for l, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        l[uv].uv = t
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def _niche_painting(seed):
    """Malba v nice: Ukrizovany na modrem poli s cervenym okrajem, vybledla a oprýskaná."""
    W, H = 256, 384
    R = random.Random(seed)
    im = Image.new("RGB", (W, H), (58, 78, 120))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(140, 40, 32), width=14)
    d.rectangle((14, 14, W - 15, H - 15), outline=(200, 170, 90), width=3)
    d.rectangle((W // 2 - 9, 50, W // 2 + 9, H - 40), fill=(92, 58, 34))          # kriz
    d.rectangle((40, 104, W - 40, 122), fill=(92, 58, 34))
    tel = (226, 206, 180)
    d.ellipse((W // 2 - 17, 70, W // 2 + 17, 104), fill=tel)                         # hlava
    d.ellipse((W // 2 - 24, 64, W // 2 + 24, 80), outline=(214, 170, 60), width=4)   # svatozar
    d.polygon([(W // 2 - 20, 108), (W // 2 + 20, 108), (W // 2 + 14, 210), (W // 2 - 14, 210)], fill=tel)
    d.polygon([(W // 2 - 20, 110), (52, 114), (52, 122), (W // 2 - 20, 124)], fill=tel)
    d.polygon([(W // 2 + 20, 110), (W - 52, 114), (W - 52, 122), (W // 2 + 20, 124)], fill=tel)
    d.polygon([(W // 2 - 18, 200), (W // 2 + 18, 200), (W // 2 + 12, 236), (W // 2 - 12, 236)], fill=(236, 232, 220))
    d.polygon([(W // 2 - 10, 236), (W // 2 + 10, 236), (W // 2 + 6, 320), (W // 2 - 6, 320)], fill=tel)
    d.polygon([(40, H - 40), (W - 40, H - 40), (W - 70, H - 70), (70, H - 70)], fill=(70, 96, 50))  # Golgota
    for k in range(70):                                                              # oprýskání
        x, y = R.uniform(0, W), R.uniform(0, H)
        r = R.uniform(2, 9)
        d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=(205, 198, 182))
    return _mat("malba_%d" % seed, _save(im.filter(ImageFilter.GaussianBlur(0.8)), "malba_%d" % seed), 0.85)


def _shingle_mat():
    """Stary sindel: rady stipanych desticek ruzne siroke, zesedla dub s vlaknem, tmave spary a stin pod radou."""
    m = bpy.data.materials.get("sindel_stary")
    if m:
        return m
    W = 512
    R = random.Random(77)
    im = Image.new("RGB", (W, W), (40, 36, 32))
    d = ImageDraw.Draw(im)
    rows = 16
    rh = W // rows
    for r in range(rows):
        y0 = r * rh
        x = -R.uniform(0, 30)
        while x < W:
            w = R.uniform(22, 44)
            g = R.uniform(0.75, 1.1)
            base = (int(118 * g), int(110 * g), int(98 * g))
            d.rectangle((x + 1, y0, x + w - 1, y0 + rh - 1), fill=base)
            for k in range(int(w / 3)):                                    # vlakna dreva
                xx = x + R.uniform(2, w - 2)
                c = tuple(int(v * R.uniform(0.82, 0.95)) for v in base)
                d.line([(xx, y0 + 2), (xx + R.uniform(-1.5, 1.5), y0 + rh - 2)], fill=c, width=1)
            if R.random() < 0.25:                                          # mech / lisejnik
                cx, cy = x + w / 2, y0 + rh * 0.7
                d.ellipse((cx - 7, cy - 4, cx + 7, cy + 4), fill=(92, 104, 60))
            x += w
        d.rectangle((0, y0 + rh - 4, W, y0 + rh - 1), fill=(34, 30, 26))   # stin spodni hrany rady nad
    # sev mezi kopiemi textury: radky navazuji
    m = _mat("sindel_stary", _save(im.filter(ImageFilter.GaussianBlur(0.6)), "sindel_stary"), 0.9)
    return m


def _shingle_roof(z0, half, h, mat, n=14, eave=0.035):
    """Ctyrboka prohnuta strisecka: ctverce ruznych velikosti po vysce, plochy s UV podle sklonu (rady sindele
    vodorovne), spodni hrana s tloustkou (okap)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings = []
    for i in range(n + 1):
        t = i / n
        sz = half * (1 - t) ** 1.5 + 0.03 * t
        z = z0 + h * (t ** 0.85)
        rings.append((sz, z))
    sl = [0.0]
    for (a, za), (b, zb) in zip(rings, rings[1:]):
        sl.append(sl[-1] + math.hypot(a - b, zb - za))
    corners = ((1, 1), (-1, 1), (-1, -1), (1, -1))
    V = []
    for sz, z in rings:
        V.append([bm.verts.new((cx * sz, cy * sz, z)) for cx, cy in corners])
    TEX = 1.4                     # metru na jednu kopii textury
    for i in range(n):
        for k in range(4):
            a0, a1 = V[i][k], V[i][(k + 1) % 4]
            b0, b1 = V[i + 1][k], V[i + 1][(k + 1) % 4]
            f = bm.faces.new((a0, a1, b1, b0))
            s0, s1 = rings[i][0], rings[i + 1][0]
            for l, (u, v) in zip(f.loops, ((-s0, sl[i]), (s0, sl[i]), (s1, sl[i + 1]), (-s1, sl[i + 1]))):
                l[uv].uv = (u / TEX, v / TEX)
    # okap: svisly pasek tloustky sindele
    lo = [bm.verts.new((cx * (half + 0.005), cy * (half + 0.005), z0 - eave)) for cx, cy in corners]
    for k in range(4):
        f = bm.faces.new((lo[k], lo[(k + 1) % 4], V[0][(k + 1) % 4], V[0][k]))
        for l, (u, v) in zip(f.loops, ((-half, -eave), (half, -eave), (half, 0.0), (-half, 0.0))):
            l[uv].uv = (u / TEX, v / TEX)
    bm.faces.new(lo[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("strisecka")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new("strisecka", me)
    bpy.context.scene.collection.objects.link(o)
    return o


def wayside_shrine(name):
    """Bozi muka: kamenny podstavec ze dvou stupnu, hranoly drik z lomoveho zdiva, bile omitnuta hlava se ctyrmi
    nikami (v kazde vybledla malba Ukrizovaneho), pyramidova strisecka z sindelu v radach a kovany krizek."""
    zdivo = _wood_mat("muka_zdivo", "zdivo", (0.95, 0.93, 0.88))
    omit = _wood_mat("muka_omitka", "omitka_bila", (0.96, 0.95, 0.9))
    pisk = _wood_mat("muka_kamen", "kamen", (0.92, 0.9, 0.86))
    jasan, dub, fe, ocel, provaz = _woods()
    _box((0, 0, 0.09), (1.1, 1.1, 0.18), pisk, bevel=0.03)
    _box((0, 0, 0.25), (0.86, 0.86, 0.16), pisk, bevel=0.025)
    # drik z lomoveho kamene: jadro z malty a na nem jednotlive kameny ruzne velke, vystupujici z lice
    malta = _wood_mat("muka_malta", "malta", (0.78, 0.74, 0.66))
    kamen = _wood_mat("muka_kamen", "kamen", (0.9, 0.86, 0.8))
    _box((0, 0, 1.17), (0.56, 0.56, 1.7), malta, bevel=0.01)
    Rs = random.Random(11)
    for face in range(4):
        a = face * math.pi / 2
        n = (math.cos(a), math.sin(a))
        t = (-math.sin(a), math.cos(a))
        z = 0.34
        while z < 2.0:
            hh = Rs.uniform(0.09, 0.17)
            sx = -0.3 + Rs.uniform(0.0, 0.05)
            while sx < 0.29:
                ww = min(Rs.uniform(0.11, 0.24), 0.31 - sx)
                if ww < 0.05:
                    break
                cx, cy = sx + ww / 2, z + hh / 2
                dep = Rs.uniform(0.07, 0.12)
                off = 0.28 + dep / 2 - 0.035 + Rs.uniform(0.0, 0.02)
                o = _box((n[0] * off + t[0] * cx, n[1] * off + t[1] * cx, cy), (ww - 0.018, dep, hh - 0.018), kamen,
                         bevel=Rs.uniform(0.01, 0.025))
                o.rotation_euler = (Rs.uniform(-0.05, 0.05), Rs.uniform(-0.05, 0.05), a + math.pi / 2 + Rs.uniform(-0.04, 0.04))
                sx += ww
            z += hh
    # rimsa pod hlavou
    _box((0, 0, 2.06), (0.74, 0.74, 0.08), pisk, bevel=0.02)
    # hlava: jadro, rohove pilire, spodni a horni deska -> ctyri niky
    z0, hn = 2.1, 0.62
    _box((0, 0, z0 + 0.15 + hn / 2), (0.46, 0.46, hn), omit, bevel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _box((sx * 0.31, sy * 0.31, z0 + 0.15 + hn / 2), (0.16, 0.16, hn), omit, bevel=0.015)
    _box((0, 0, z0 + 0.075), (0.78, 0.78, 0.15), omit, bevel=0.02)
    _box((0, 0, z0 + 0.15 + hn + 0.09), (0.78, 0.78, 0.18), omit, bevel=0.02)
    for k in range(4):
        a = k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        # malba na jadru
        m = _niche_painting(k + 1)
        n = Vector((ca, sa, 0))
        t = Vector((-sa, ca, 0))
        c = n * 0.232
        w, zb, zt = 0.17, z0 + 0.19, z0 + 0.15 + hn - 0.08
        _quad("malba", [c - t * w + Vector((0, 0, zb)), c + t * w + Vector((0, 0, zb)), c + t * w + Vector((0, 0, zt)),
                        c - t * w + Vector((0, 0, zt))], m)
    # strecha: hladka prohnuta strisecka (dole plossi presah, nahore strma) se sindelovou texturou
    zr = z0 + 0.15 + hn + 0.18
    _shingle_roof(zr - 0.04, 0.64, 0.98, _shingle_mat())
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0, 0, zr + 0.98), segments=12, ring_count=8)
    bpy.context.object.data.materials.append(dub)
    _handle((0, 0, zr + 0.98), (0, 0, zr + 1.38), 0.012, fe, 0.012, 6)
    _handle((-0.12, 0, zr + 1.25), (0.12, 0, zr + 1.25), 0.01, fe, 0.01, 6)
    return None


BUILD.update({"bozi_muka": lambda: wayside_shrine("bozi_muka")})


# ======================================================================= lom (radce 16:20, Misa: "lom podle obrazku KCD, at je fakt vybaveny")

def _kolo(c, R, dub, fe, jasan, paprsku=10):
    """Loukotove kolo ve svisle rovine XZ se stredem c: loukote, obruc, paprsky, naboj."""
    bpy.ops.mesh.primitive_torus_add(major_radius=R - 0.04, minor_radius=0.045, location=c, rotation=(math.pi / 2, 0, 0),
                                     major_segments=40, minor_segments=8)
    o = bpy.context.object
    o.scale = (1, 1, 0.75)
    o.data.materials.append(dub)
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=0.012, location=c, rotation=(math.pi / 2, 0, 0),
                                     major_segments=40, minor_segments=6)
    bpy.context.object.data.materials.append(fe)
    for k in range(paprsku):
        a = 2 * math.pi * k / paprsku
        _handle((c[0] + math.cos(a) * 0.08, c[1], c[2] + math.sin(a) * 0.08),
                (c[0] + math.cos(a) * (R - 0.06), c[1], c[2] + math.sin(a) * (R - 0.06)), 0.022, jasan, 0.017, 8)
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.1, depth=0.24, location=c, rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(dub)


def zebrinak(name):
    """Vuz zebrinak (KCD lom): dve napravy, predni kola mensi, podvozek z tramu, podlaha z prken, bocnice jako zebrik
    (dve zerdi a prickove kolíky) rozevrene do V, oj s vahadlem, klanicnice. Delka ~3,8 m."""
    jasan, dub, fe, ocel, provaz = _woods()
    R = random.Random(19)
    zadni = (-1.15, 0.55)
    predni = (1.05, 0.45)
    for x, r in (zadni, predni):
        for sy in (-1, 1):
            _kolo((x, sy * 0.68, r), r, dub, fe, jasan, 12 if r > 0.5 else 10)
        _box((x, 0, r), (0.12, 1.5, 0.12), dub, bevel=0.01)                          # naprava
        _box((x, 0, r + 0.14), (0.14, 1.1, 0.14), dub, bevel=0.01)                   # podsedek
    # podvozek: dva podelne tramy (vahy), spojeny
    for sy in (-1, 1):
        _box((0.0, sy * 0.38, 0.76), (3.3, 0.1, 0.12), dub, bevel=0.01)
    _box((0.0, 0, 0.7), (3.0, 0.1, 0.1), dub, bevel=0.01)                            # spojnice (lanok)
    # podlaha z prken, kazde trochu jine
    x = -1.6
    while x < 1.55:
        w = R.uniform(0.18, 0.26)
        o = _box((x + w / 2, 0, 0.86), (w - 0.012, 0.86, 0.035), dub, bevel=0.004)
        o.rotation_euler = (R.uniform(-0.01, 0.01), 0, 0)
        x += w
    # bocnice zebrinove: spodni a horni zerd, pricky; rozevrene ven
    for sy in (-1, 1):
        sk = sy * 0.32
        def bod(xx, h):
            return (xx, sy * 0.44 + math.sin(sk) * h, 0.88 + math.cos(sk) * h)
        _handle(bod(-1.75, 0.03), bod(1.75, 0.03), 0.04, dub, 0.035, 8)
        _handle(bod(-1.85, 0.62), bod(1.85, 0.62), 0.035, jasan, 0.03, 8)
        xx = -1.65
        while xx < 1.7:
            _handle(bod(xx, 0.03), bod(xx + R.uniform(-0.02, 0.02), 0.64), 0.016, jasan, 0.014, 6)
            xx += 0.2
        for xs in (-1.15, 1.05):                                                      # klanice (opery bocnic)
            _handle((xs, sy * 0.4, 0.8), bod(xs + 0.05, 0.66), 0.03, dub, 0.025, 8)
    # celo a zadni celo z prken
    for xs in (-1.78, 1.78):
        for k in range(3):
            _box((xs, 0, 0.96 + k * 0.15), (0.03, 0.86 + k * 0.14, 0.12), dub, bevel=0.004)
    # oj s vahadlem (lezi na zemi pred vozem) a retez
    _handle((1.2, 0, 0.6), (3.4, 0, 0.12), 0.05, jasan, 0.04, 10)
    _box((3.35, 0, 0.12), (0.08, 0.9, 0.07), dub, bevel=0.006)
    _box((1.2, 0, 0.62), (0.2, 0.2, 0.08), fe, bevel=0.004)
    # nalozeno: par kvadru a palice
    kamen = _plain("piskovec_lom", (0.42, 0.38, 0.31), 0.0, 0.92)
    for k, (cx, cy) in enumerate(((-0.9, -0.15), (-0.35, 0.18), (0.35, -0.1))):
        o = _box((cx, cy, 0.88 + 0.17), (0.55, 0.4, 0.32), kamen, bevel=0.02, uvs=0.8)
        o.rotation_euler = (0, 0, R.uniform(-0.2, 0.2))
    return None


def pristresek(name, L=4.2, W=3.2, H=3.4):
    """Plateny stanek jako v lomu u Talmberka (KCD, Misa: "drz se fotek, stan je nizky"): ctyri svisle rohove kuly
    a stredni kuly do vysky okapu 2,3 m, na celech vysoke kuly pod hrebenovou tyc (3,4 m), okapove tyce po obvodu;
    svetle lnene platno pres hreben na obe strany, mirne proveseni mezi krokvemi, po obvodu okapu svisly lem
    (kanafas ~0,35 m, dole zvlneny) - boky otevrene; provazy ze rohu ke kolikum."""
    jasan, dub, fe, ocel, provaz = _woods()
    R = random.Random(23)
    lin = _wood_mat("plachta_lnena", "plachta", (1.0, 1.0, 1.0))      # barva v texture (glTF nasobeni nevyexportuje)
    lin.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    lin.use_backface_culling = False                    # jedna oboustranna plocha: dve slupky 8 mm delaly stinovou sachovnici
    hx, hy = L / 2, W / 2
    he = H - 1.1                                        # vyska okapu (fotky: clovek projde pod okapem)
    # kuly: rohy a stredy delsich stran do okapu, na celech do hrebene
    for sy in (-1, 1):
        for sx in (-1, 0, 1):
            x = sx * hx
            _handle((x + R.uniform(-0.02, 0.02), sy * hy, -0.25), (x, sy * hy, he + 0.04), 0.055, dub, 0.05, 8)
        _handle((-hx - 0.12, sy * hy, he), (hx + 0.12, sy * hy, he), 0.045, jasan, 0.04, 8)
    for sx in (-1, 1):
        _handle((sx * hx, 0, -0.25), (sx * hx, 0, H + 0.08), 0.06, dub, 0.055, 8)
        _handle((sx * hx, -hy - 0.1, he), (sx * hx, hy + 0.1, he), 0.04, jasan, 0.035, 8)
    _handle((-hx - 0.15, 0, H + 0.02), (hx + 0.15, 0, H + 0.02), 0.055, dub, 0.05, 10)
    kro = []
    for k in range(5):                                  # krokve z hrebene na okap
        x = -hx + L * k / 4
        kro.append(x)
        for sy in (-1, 1):
            _handle((x, 0, H + 0.05), (x, sy * (hy + 0.05), he + 0.02), 0.026, jasan, 0.022, 6)
    # strecha: v od okapu pres hreben k okapu; na konci svisly lem
    slope = math.hypot(hy, H - he)
    lem = 0.36
    total = 2 * (slope + lem)
    def p(u, v):
        x = -hx - 0.1 + (L + 0.2) * u
        sv = v * total - total / 2
        side = 1 if sv >= 0 else -1
        a = abs(sv)
        dk = min(abs(x - c) for c in kro)
        # Misa: "ani dokonale vypnute plachty tam nebyly" - mezi krokvemi prohnuti 15-20 cm, hreben se mezi kuly
        # prohyba, platno zvlnene vraskami a lem dole nerovny (nestejne dlouhy, zvlneny)
        sag = (0.15 + 0.05 * math.sin(x * 1.7 + side)) * math.sin(min(dk / (L / 4) * math.pi, math.pi))
        if a <= slope:
            t = a / slope
            y = side * (hy + 0.06) * t
            z = H + 0.09 - (H - he) * t - sag * math.sin(t * math.pi)
        else:
            d = a - slope
            y = side * (hy + 0.07 + 0.04 * math.sin(x * 2.3 + side) * d / lem)
            dl = 0.06 * math.sin(x * 3.1 + side * 2.0) + 0.04 * math.sin(x * 7.7)
            z = he + 0.06 - d * (1.0 + dl / lem)
        # vrasky jen mezi krokvemi (na krokvi a hrebeni platno lezi), na lemu volne
        mk = math.sin(min(dk / (L / 4) * math.pi, math.pi)) * min(1.0, a / slope * 4.0) if a <= slope else 1.0
        z -= mk * (0.025 * (1.0 + math.sin(x * 5.0 + sv * 4.0)) + 0.012 * (1.0 + math.sin(x * 13.0 - sv * 7.0)))
        return (x, y, z)
    _grid_cloth("plachta", lin, 40, 36, p, 0.0)
    # lem na celech pod okapem (stit zustava otevreny jako na fotkach)
    for sx in (-1, 1):
        def q(u, v, sx=sx):
            y = -hy - 0.07 + (W + 0.14) * u
            z = he + 0.06 - v * lem * (1.0 + 0.2 * math.sin(y * 3.3 + sx))
            return (sx * (hx + 0.11 + 0.03 * math.sin(y * 5.0) * v), y, z)
        _grid_cloth("plachta_lem", lin, 24, 4, q, 0.0)
    # provazy z rohu okapu ke kolikum
    for sx in (-1, 1):
        for sy in (-1, 1):
            a = (sx * hx, sy * hy, he)
            b = (sx * (hx + 1.0), sy * (hy + 1.0), 0.05)
            _handle(a, b, 0.009, provaz, 0.009, 5)
            _handle((b[0], b[1], -0.15), (b[0] + sx * 0.04, b[1], 0.2), 0.025, jasan, 0.015, 6)
    # pracovni stul kamenika pod strechou (prkno na kozach)
    for sx in (-1, 1):
        for sz in (-1, 1):
            _handle((sx * 0.9, sz * 0.25, 0.0), (sx * 0.9, 0, 0.78), 0.035, dub, 0.03, 8)
    _box((0, 0, 0.8), (2.0, 0.6, 0.06), dub, bevel=0.006)
    return None


def _ven(ob, c=(0.0, 0.0, 1.0)):
    """Normaly latky ven od bodu c (jinak v Godotu stinova sachovnice na odvracene strane)."""
    me = ob.data
    pol = me.polygons[len(me.polygons) // 2]
    if pol.normal.dot(pol.center - Vector(c)) < 0.0:
        me.flip_normals()
    return ob


def stan_jehlan(name, S=3.2, H=3.6, hs=1.5):
    """Jehlanovy stan (KCD lom, fotka 2): stredni stozar, ctvercovy pudorys, svisle steny ~1,5 m, strecha jehlan
    se stredem na stozaru, po obvodu okapu zvlneny lem; vchod - jedna stena vpredu rozhrnuta. Kolíky a provazy."""
    jasan, dub, fe, ocel, provaz = _woods()
    R = random.Random(31)
    lin = _wood_mat("plachta_lnena", "plachta", (1.0, 1.0, 1.0))
    lin.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    lin.use_backface_culling = False
    h = S / 2
    _handle((0, 0, -0.3), (0, 0, H + 0.25), 0.06, dub, 0.05, 8)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(0, 0, H + 0.28), segments=10, ring_count=6)
    bpy.context.object.data.materials.append(dub)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _handle((sx * h, sy * h, -0.2), (sx * h, sy * h, hs + 0.05), 0.04, jasan, 0.035, 6)
    # strecha: 4 trojuhelnikove plochy z vrcholu na okap, kazda se zvlnenim
    for k in range(4):
        a = k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        def r(u, v, ca=ca, sa=sa):
            t = -h + 2 * h * u                          # podel okapu
            ex, ey = ca * h - sa * t, sa * h + ca * t   # bod na okapu
            x, y = ex * v, ey * v
            z = H + 0.05 - (H - hs) * v - 0.16 * math.sin(v * math.pi) * math.sin(u * math.pi) \
                - 0.03 * math.sin(t * 4.0 + v * 6.0) * v
            if v > 1.0:
                x, y, z = ex * 1.02, ey * 1.02, hs - (v - 1.0) * 1.8 * (1.0 + 0.25 * math.sin(t * 3.1 + ca))
            return (x, y, z)
        _ven(_grid_cloth("plachta_jehlan", lin, 18, 16, lambda u, v, r=r: r(u, v * 1.2), 0.0))
    # steny: tri cele, predni rozhrnuta (dva cipy shrnute k rohovym kulum)
    for k in range(4):
        a = k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        for t0, t1 in (((-h, h),) if k else ((-h, -h * 0.55), (h * 0.55, h))):
            def w(u, v, ca=ca, sa=sa, t0=t0, t1=t1):
                t = t0 + (t1 - t0) * u
                x, y = ca * h * 1.01 - sa * t, sa * h * 1.01 + ca * t
                z = hs - v * (hs + 0.02 + 0.06 * math.sin(t * 2.7 + k))        # dolni okraj nerovny
                f = (0.05 if k else 0.08) * (0.4 + v)                          # dole volnejsi, vic zvlnene
                return (x + ca * f * math.sin(t * 7.0 + v * 2.0), y + sa * f * math.sin(t * 7.0 + v * 2.0), z)
            _ven(_grid_cloth("plachta_stena", lin, 16 if k else 6, 6, w, 0.0), (0.0, 0.0, hs * 0.5))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        b = (math.cos(a) * h * 1.9, math.sin(a) * h * 1.9, 0.05)
        _handle((math.cos(a) * h * 1.41, math.sin(a) * h * 1.41, hs), b, 0.009, provaz, 0.009, 5)
        _handle((b[0], b[1], -0.15), (b[0], b[1], 0.2), 0.025, jasan, 0.015, 6)
    return None


BUILD.update({
    "zebrinak": lambda: zebrinak("zebrinak"),
    "pristresek_plachta": lambda: pristresek("pristresek_plachta"),
    "pristresek_maly": lambda: pristresek("pristresek_maly", 3.2, 2.8, 3.2),
    "stan_jehlan": lambda: stan_jehlan("stan_jehlan"),
})
