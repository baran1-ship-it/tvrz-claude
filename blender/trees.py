"""Hry-pratelne smrky: vetve z naskenovaneho stromu (Poly Haven fir_tree_01) vyrenderovane do textury
s pruhlednosti a poskladane na kmen v preslenech, jak se to dela pro stromy ve hrach (SpeedTree postup).

  python trees.py        -> tex_cache/smrk_vetev.png (vetev shora, RGBA)
Pak veg.load_library pridava do knihovny druh "smrk" (nekolik variant, ~1500 trojuhelniku).
"""
import math
import os
import random

import bpy  # noqa: E402 (musi byt pred bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector

from lib import TEX_ROOT

BRANCH_PNG = os.path.join(TEX_ROOT, "smrk_vetev.png")
BARK = os.path.join(TEX_ROOT, "models", "fir_tree_01", "textures", "fir_tree_01_bark_diff_1k.jpg")


# ------------------------------------------------------------------ zapeceni vetve do textury

def bake_branch(res=1024):
    """Vyrizne z naskenovaneho smrku jednu boci vetev a vyrenderuje ji shora na pruhledne pozadi.
    Vetev lezi v textuře od leveho okraje (u kmene) doprava, sirka = polovina delky."""
    import scene
    scene.reset()
    path = os.path.join(TEX_ROOT, "models", "fir_tree_01", "fir_tree_01.gltf")
    bpy.ops.import_scene.gltf(filepath=path)
    bpy.context.view_layer.update()
    meshes = sorted([o for o in bpy.data.objects if o.type == "MESH"], key=lambda o: o.name)
    src = [o for o in meshes if "_b_" in o.name][0]    # varianta b: husta a pravidelna
    for o in meshes:
        if o is not src:
            bpy.data.objects.remove(o)
    me = src.data
    me.transform(src.matrix_world)
    src.matrix_world = Matrix()
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    z0, z1 = min(zs), max(zs)
    H = z1 - z0
    # vyrez: vetve na jedne strane ve vysce 35-45 % (nejhustsi a nejdelsi)
    za, zb = z0 + 0.36 * H, z0 + 0.44 * H
    L = 2.6
    print("zdroj", src.name, len(me.polygons), "z", z0, z1, "cx", cx)
    bm = bmesh.new()
    bm.from_mesh(me)
    kill = [v for v in bm.verts if not (za < v.co.z < zb and 0.15 < v.co.x - cx < L and abs(v.co.y - cy) < 0.55 * L)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    # odstranit kmen/kuru (materialy bark/trunk)
    keep = [i for i, m in enumerate(me.materials) if m and ("twig" in m.name or "dead" in m.name)]
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in keep], context="FACES")
    bm.to_mesh(me)
    bm.free()
    print("vetev: %d trojuhelniku" % sum(len(p.vertices) - 2 for p in me.polygons))
    # kamera shora, ortograficka, vetev od x=cx (kmen) do cx+L
    cam = bpy.data.cameras.new("K")
    cam.type = "ORTHO"
    cam.ortho_scale = L
    co = bpy.data.objects.new("K", cam)
    bpy.context.scene.collection.objects.link(co)
    co.location = (cx + L / 2, cy, z1 + 5)
    co.rotation_euler = (0, 0, 0)
    sc = bpy.context.scene
    sc.camera = co
    sc.render.resolution_x = res
    sc.render.resolution_y = res // 2
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 32
    sc.view_settings.view_transform = "Standard"
    # mekke svetlo shora a z boku
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.95, 1.0, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sc.world = w
    sun = bpy.data.lights.new("S", "SUN")
    sun.energy = 3.0
    so = bpy.data.objects.new("S", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(25), math.radians(-15), 0)
    # textura y je v kamere vyska obrazu = 0.5*L -> vyrez y musi byt +-L/4
    sc.render.filepath = BRANCH_PNG
    bpy.ops.render.render(write_still=True)
    print("ulozeno", BRANCH_PNG)


# ------------------------------------------------------------------ procedurální smrk z karet

def spruce_mesh(name, seed, h=16.0):
    """Smrk: kuzelovity kmen, preslen vetvi kazdych ~0.45 m, karty ovesene dolu, vrchol z krizenych karet.
    UV: karty 0..1 na texturu vetve (u kmene vlevo), kmen na kuru. Vyska h v metrech, pata v 0."""
    rnd = random.Random(seed)
    verts, faces, uvs, mats = [], [], [], []

    def quad(p, mat, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
        i = len(verts)
        verts.extend(p)
        faces.append((i, i + 1, i + 2, i + 3))
        uvs.append(uv)
        mats.append(mat)

    # kmen: 7 stran, 6 segmentu, kura opakovana po metrech
    r0 = 0.012 * h + 0.1
    seg, sides = 6, 7
    rings = []
    for s in range(seg + 1):
        t = s / seg
        r = r0 * (1 - t) ** 1.1 + 0.02
        z = h * t * 0.97
        rings.append([Vector((r * math.cos(2 * math.pi * k / sides), r * math.sin(2 * math.pi * k / sides), z)) for k in range(sides)])
    for s in range(seg):
        for k in range(sides):
            k2 = (k + 1) % sides
            a, b, c, d = rings[s][k], rings[s][k2], rings[s + 1][k2], rings[s + 1][k]
            u0, u1 = k / sides, (k + 1) / sides
            v0, v1 = rings[s][0].z / 2.0, rings[s + 1][0].z / 2.0
            quad([a, b, c, d], 1, ((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
    # preslen vetvi: od 15-30 % vysky (spodek proschly) po vrchol
    z = h * rnd.uniform(0.12, 0.22)
    phase = rnd.uniform(0, 6.28)
    while z < h * 0.93:
        t = z / h
        length = (0.24 * h) * (1 - t) ** 0.85 * rnd.uniform(0.85, 1.12) + 0.25
        n = 8 if t < 0.7 else 6
        phase += 0.7 + rnd.uniform(-0.2, 0.2)
        for k in range(n + n // 2):
            inner = k >= n          # kratsi vnitrni vetve mezi dlouhymi = hustsi koruna
            k = k % n if not inner else (k - n) * 2 + 0.5
            a = phase + 2 * math.pi * k / n + rnd.uniform(-0.25, 0.25)
            d = Vector((math.cos(a), math.sin(a), 0))
            side = Vector((-d.y, d.x, 0))
            droop = math.radians(rnd.uniform(18, 34) * (1.1 - 0.5 * t))
            dirv = (d * math.cos(droop) - Vector((0, 0, math.sin(droop)))).normalized()
            ln_k = length * (0.6 if inner else 1.0)
            w = ln_k * 0.5
            base = Vector((0, 0, z)) + d * (r0 * (1 - t) * 0.8)
            tip = base + dirv * ln_k
            # karta mirne do V: dve poloviny podel vetve, okraje svesene (lepsi objem)
            sag = Vector((0, 0, -0.12 * w))
            l0, r0_ = base + side * (w * 0.5) + sag, base - side * (w * 0.5) + sag
            l1, r1 = tip + side * (w * 0.5) + sag, tip - side * (w * 0.5) + sag
            mid0, mid1 = base, tip
            quad([mid0, mid1, l1, l0], 0, ((0, 0.5), (1, 0.5), (1, 1), (0, 1)))
            quad([r0_, r1, mid1, mid0], 0, ((0, 0), (1, 0), (1, 0.5), (0, 0.5)))
        z += rnd.uniform(0.38, 0.55) * (h / 16.0) ** 0.5
    # vrchol: dve krizene svisle karty
    for a in (0.0, math.pi / 2):
        d = Vector((math.cos(a), math.sin(a), 0)) * (0.09 * h ** 0.5)
        zt = h * 0.86
        quad([Vector((0, 0, zt)) - d, Vector((0, 0, zt)) + d, Vector((0, 0, h)) + d * 0.2, Vector((0, 0, h)) - d * 0.2], 0,
             ((0, 0.05), (0, 0.95), (1, 0.6), (1, 0.4)))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    li = 0
    for f, uv in zip(me.polygons, uvs):
        for k in range(f.loop_total):
            uvl.data[f.loop_start + k].uv = uv[k]
        f.material_index = mats[f.index]
    me.materials.append(spruce_material())
    me.materials.append(bark_material())
    return me


def spruce_material():
    m = bpy.data.materials.get("smrk_vetve")
    if m:
        return m
    m = bpy.data.materials.new("smrk_vetve")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(BRANCH_PNG, check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.85
    m.blend_method = "CLIP" if hasattr(m, "blend_method") else m.blend_method
    try:
        m.surface_render_method = "DITHERED"
    except AttributeError:
        pass
    m.use_backface_culling = False
    return m


def bark_material():
    m = bpy.data.materials.get("smrk_kura")
    if m:
        return m
    m = bpy.data.materials.new("smrk_kura")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(BARK, check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return m


def add_to_library(LIB, nvar=5):
    """Prida druh 'smrk' do knihovny vegetace: [(mesh, vyska, sirka)]."""
    out = []
    for i in range(nvar):
        h = 16.0
        me = spruce_mesh("smrk_%d" % i, 100 + i, h)
        w = max(v.co.x for v in me.vertices) - min(v.co.x for v in me.vertices)
        out.append((me, h, w))
    LIB["smrk"] = out


if __name__ == "__main__":
    bake_branch()
