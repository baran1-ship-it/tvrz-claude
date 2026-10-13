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
