"""Atlas trsu psenice pro pole (obrazky/psenice_atlas.png, 1024x512, 2x1 bunky, alfa) - Misa 28. 10.: „rovnou tam
vysad aspon psenici, at je to videt“. CC0 model psenice nebyl (Poly Haven ani jinde zdarma) - stebla se modeluji:
steblo (krivka s tlouskou, mirne prohnute), 2-3 listy, klas z klasku stridave na 8-10 cm s osinami. Bunka 0 zrala
(zlatava, klasy sklonene), bunka 1 zelena (cervnova). Ortograficky pohled z boku (Cycles, rovnomerne nebe), okraje
rozlite jako atlas travy (blender/atlas_travy.py).
  /opt/bl/bin/python blender/atlas_psenice.py"""
import bpy
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VYSTUP = os.path.join(KOREN, "obrazky", "psenice_atlas.png")
SIRKA, VYSKA = 1024, 512
BW = SIRKA // 2
VZORKY = int(os.environ.get("ATLAS_VZORKY", "64"))
ZABER_M = 0.62                          # sirka zaberu bunky (vyska = 1,24 m pri 512 px)


def material(nm, barva, drsnost=0.75):
    m = bpy.data.materials.new(nm)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*barva, 1.0)
    b.inputs["Roughness"].default_value = drsnost
    return m


def krivka(body, tloustka, mat, kol):
    cd = bpy.data.curves.new("k", "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = tloustka
    cd.bevel_resolution = 2
    sp = cd.splines.new("POLY")
    sp.points.add(len(body) - 1)
    for i, p in enumerate(body):
        sp.points[i].co = (*p, 1.0)
    o = bpy.data.objects.new("k", cd)
    o.data.materials.append(mat)
    kol.objects.link(o)
    return o


def list_(x, y, z0, delka, smer, mat, kol, rng):
    """Uzky list (pas trojuhelniku) odstavajici od stebla, prohnuty dolu."""
    me = bpy.data.meshes.new("l")
    v, f = [], []
    n = 8
    for i in range(n + 1):
        t = i / n
        sir = 0.006 * math.sin(math.pi * min(1.0, t * 1.3 + 0.1))
        dx = math.cos(smer) * delka * t
        dy = math.sin(smer) * delka * t
        dz = delka * (0.55 * t - 0.65 * t * t)
        px, py = -math.sin(smer) * sir, math.cos(smer) * sir
        v += [(x + dx + px, y + dy + py, z0 + dz), (x + dx - px, y + dy - py, z0 + dz)]
        if i:
            a = 2 * (i - 1)
            f.append((a, a + 1, a + 3, a + 2))
    me.from_pydata(v, [], f)
    o = bpy.data.objects.new("l", me)
    o.data.materials.append(mat)
    kol.objects.link(o)


def klas(vrch, smer_sklonu, sklon, mat_klas, mat_osina, kol, rng):
    """Klas: osa 9 cm sklonena, klasky stridave do dvou rad (zplostele elipsoidy), z kazdeho osina."""
    delka = rng.uniform(0.075, 0.1)
    n = 16
    for i in range(n):
        t = i / (n - 1)
        # osa klasu: od vrchu stebla dal ve smeru sklonu
        ax = vrch[0] + math.cos(smer_sklonu) * math.sin(sklon) * delka * t
        ay = vrch[1] + math.sin(smer_sklonu) * math.sin(sklon) * delka * t
        az = vrch[2] + math.cos(sklon) * delka * t
        strana = 1 if i % 2 else -1
        bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=4, radius=0.0042, location=(ax + strana * 0.003, ay, az))
        k = bpy.context.active_object
        k.scale = (0.8, 0.6, 1.5)
        k.rotation_euler = (0.0, strana * 0.5 + sklon * 0.6, smer_sklonu)
        k.data.materials.append(mat_klas)
        for c in k.users_collection:
            c.objects.unlink(k)
        kol.objects.link(k)
        # osina 3-5 cm sikmo vzhuru od klasku
        osa = rng.uniform(0.03, 0.05)
        krivka([(ax, ay, az), (ax + strana * osa * 0.35, ay, az + osa)], 0.00035, mat_osina, kol)


def trs(kol, rng, zrala):
    zel = (0.16, 0.32, 0.06)
    zlat = (0.62, 0.48, 0.18)
    m_st = material("steblo", zlat if zrala else zel, 0.8)
    m_li = material("list", (0.5, 0.42, 0.2) if zrala else (0.14, 0.3, 0.05), 0.85)
    m_kl = material("klas", (0.72, 0.56, 0.24) if zrala else (0.22, 0.4, 0.08), 0.7)
    m_os = material("osina", (0.78, 0.66, 0.36) if zrala else (0.3, 0.46, 0.14), 0.7)
    for _ in range(26):
        x = rng.uniform(-0.26, 0.26)
        y = rng.uniform(-0.12, 0.12)
        h = rng.uniform(0.85, 1.05)
        smer = rng.uniform(0, 2 * math.pi)
        ohyb = rng.uniform(0.02, 0.07) + (0.05 if zrala else 0.0)
        body = []
        for i in range(9):
            t = i / 8
            body.append((x + math.cos(smer) * ohyb * t * t, y + math.sin(smer) * ohyb * t * t, h * t))
        krivka(body, 0.0016, m_st, kol)
        for _l in range(rng.randint(2, 3)):
            list_(x, y, rng.uniform(0.15, 0.55) * h, rng.uniform(0.16, 0.26), rng.uniform(0, 2 * math.pi), m_li, kol, rng)
        sklon = rng.uniform(0.5, 1.1) if zrala else rng.uniform(0.05, 0.3)    # zrale klasy tezke, sklonene
        klas(body[-1], smer, sklon, m_kl, m_os, kol, rng)


def vykresli(nazev, zrala, tmp):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = VZORKY
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("nebe")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    sc.world = w
    sd = bpy.data.lights.new("slunce", "SUN")
    sd.energy = 1.2
    so = bpy.data.objects.new("slunce", sd)
    so.rotation_euler = (math.radians(35), 0.0, 0.0)
    sc.collection.objects.link(so)
    kol = bpy.data.collections.new("zaber")
    sc.collection.children.link(kol)
    trs(kol, random.Random(nazev), zrala)
    cd = bpy.data.cameras.new("kam")
    cd.type = "ORTHO"
    cd.ortho_scale = ZABER_M
    co = bpy.data.objects.new("kam", cd)
    sc.collection.objects.link(co)
    vyska = ZABER_M * VYSKA / BW
    co.location = (0.0, -5.0, vyska * 0.5)
    co.rotation_euler = (math.radians(90), 0.0, 0.0)
    sc.camera = co
    sc.render.resolution_x, sc.render.resolution_y = BW, VYSKA
    cesta = os.path.join(tmp, nazev + ".png")
    sc.render.filepath = cesta
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(cesta)
    return np.array(img.pixels[:], dtype=np.float32).reshape(VYSKA, BW, 4)[::-1]


def main():
    import atlas_travy as at             # rozlij: barva okraju do pruhlednych pixelu (stejne jako atlas travy)
    tmp = os.path.join(KOREN, "blender", "tex_cache", "atlas_psenice")
    os.makedirs(tmp, exist_ok=True)
    atlas = np.zeros((VYSKA, SIRKA, 4), dtype=np.float32)
    for i, (nm, zr) in enumerate([("zrala", True), ("zelena", False)]):
        a = vykresli(nm, zr, tmp)
        a[:4, :, 3] = 0.0
        a[:, :3, 3] = 0.0
        a[:, -3:, 3] = 0.0
        atlas[:, i * BW:(i + 1) * BW] = a
        print("psenice: bunka %d %s, %.2f x %.2f m" % (i, nm, ZABER_M, ZABER_M * VYSKA / BW))
    atlas = at.rozlij(atlas)
    img = bpy.data.images.new("psenice_atlas", SIRKA, VYSKA, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels[:] = atlas[::-1].ravel()
    img.filepath_raw = VYSTUP
    img.file_format = "PNG"
    img.save()
    print("atlas ulozen:", VYSTUP)


main()
