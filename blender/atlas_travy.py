"""Atlas trsu travy pro louku (obrazky/trava_atlas.png, 1024x512, 3x2 bunky, alfa).

Bunky (index = sloupec + 3 * radek, shodne s TYP_* v scripts/louka.gd):
  0 nizka trava    (grass_medium_02 + grass_medium_01 small/mid)
  1 vysoka trava   (grass_medium_01 tall/large)
  2 sucha trava    (vysoka trava jinak poskladana, prebarvena do slamova)
  3 jitrocel / listnata bylina (weed_plant_02 + celandine bez kvetu)
  4 kapradi        (fern_02)
  5 drobne kvety   (dandelion_01, celandine_01, periwinkle_plant v trave)

Zdroj: naskenovane modely Poly Haven (CC0) v blender/tex_cache/models/. Kazda bunka = ortograficky
pohled z boku (Cycles CPU, rovnomerne bile nebe = albedo s mekkym zastinenim mezi stebly, pruhledne pozadi).
Okraje: barva se rozleje do pruhlednych pixelu (mipmapy pak nedavaji cerne lemy).

Spusteni (z korene projektu):  /opt/bl/bin/python blender/atlas_travy.py
"""
import bpy
import math
import mathutils
import os
import random
import subprocess
import sys

import numpy as np

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELY = os.environ.get("TVRZ_MODELY", os.path.join(KOREN, "blender", "tex_cache", "models"))
if not os.path.isdir(MODELY):
    MODELY = "/home/user/tvrz-claude/blender/tex_cache/models"
ALFA = os.path.join(KOREN, "blender", "tex_cache", "alfa")
VYSTUP = os.path.join(KOREN, "obrazky", "trava_atlas.png")
SIRKA, VYSKA = 1024, 512
SL, RA = 3, 2
BW, BH = SIRKA // SL, VYSKA // RA            # 341 x 256 (posledni sloupec o 1 px sirsi)
VZORKY = int(os.environ.get("ATLAS_VZORKY", "96"))

# bunka: (sirka zaberu v m, [(model, objekt, x, hloubka, otoceni, meritko)], dodatecne kusy nahodne)
# vyska zaberu = sirka * BH / BW; spodek zaberu = zem (z = 0)


def alfa(model):
    """Maska pruhlednosti listu (gltf z Poly Haven ma difuzni jpg bez alfy; maska je zvlast)."""
    cesta = os.path.join(ALFA, model + "_alpha_1k.jpg")
    if not os.path.exists(cesta):
        os.makedirs(ALFA, exist_ok=True)
        url = "https://dl.polyhaven.org/file/ph-assets/Models/jpg/1k/%s/%s_alpha_1k.jpg" % (model, model)
        if subprocess.call(["curl", "-sSfL", "-o", cesta, url]) != 0:
            if os.path.exists(cesta):
                os.remove(cesta)
            return None
    return cesta


def nacti(model):
    """Naimportuje gltf do skryte kolekce a vrati {jmeno objektu: objekt}."""
    pred = set(bpy.data.objects)
    predm = set(bpy.data.materials)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELY, model, model + ".gltf"))
    ma = alfa(model)
    for mat in [m for m in bpy.data.materials if m not in predm]:
        if not ma or not mat.use_nodes:
            continue
        nt = mat.node_tree
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        dif = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image and "diff" in n.image.name), None)
        if not bsdf or not dif:
            continue
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = bpy.data.images.load(ma, check_existing=True)
        tx.image.colorspace_settings.name = "Non-Color"
        if dif.inputs["Vector"].is_linked:
            nt.links.new(dif.inputs["Vector"].links[0].from_socket, tx.inputs["Vector"])
        nt.links.new(tx.outputs["Color"], bsdf.inputs["Alpha"])
    nove = [o for o in bpy.data.objects if o not in pred]
    out = {}
    for o in nove:
        if o.type == "MESH":
            out[o.name] = o
            o.hide_render = True
            o.hide_viewport = True
    return out


def kopie(zdroj, x, y, rot, s, kol):
    o = zdroj.copy()
    o.data = zdroj.data
    kol.objects.link(o)
    o.hide_render = False
    o.hide_viewport = False
    o.parent = None
    # stred zakladny objektu (ve svete) do pocatku, pak otocit, zmensit a posunout na (x, y)
    mw = zdroj.matrix_world.copy()
    vs = [mw @ v.co for v in zdroj.data.vertices]
    cx = (min(v.x for v in vs) + max(v.x for v in vs)) * 0.5
    cy = (min(v.y for v in vs) + max(v.y for v in vs)) * 0.5
    z0 = min(v.z for v in vs)
    m = (mathutils.Matrix.Translation((x, y, 0.0)) @ mathutils.Matrix.Rotation(rot, 4, "Z")
         @ mathutils.Matrix.Scale(s, 4) @ mathutils.Matrix.Translation((-cx, -cy, -z0)) @ mw)
    o.matrix_world = m
    return o


def scena():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = VZORKY
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.resolution_percentage = 100
    w = bpy.data.worlds.new("nebe")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs[1].default_value = 1.0
    sc.world = w
    # slaby sun shora zepredu: trochu tvaru, ale porad rovnomerne
    sd = bpy.data.lights.new("slunce", "SUN")
    sd.energy = 1.2
    sd.angle = math.radians(20)
    so = bpy.data.objects.new("slunce", sd)
    so.rotation_euler = (math.radians(35), 0.0, math.radians(0))
    sc.collection.objects.link(so)
    return sc


def kamera(sc, sirka, px_w, px_h):
    cd = bpy.data.cameras.new("kam")
    cd.type = "ORTHO"
    cd.ortho_scale = sirka
    cd.sensor_fit = "HORIZONTAL"
    co = bpy.data.objects.new("kam", cd)
    sc.collection.objects.link(co)
    vyska = sirka * px_h / px_w
    # pohled z boku (od -Y do +Y), spodek zaberu = zem
    co.location = (0.0, -5.0, vyska * 0.5)
    co.rotation_euler = (math.radians(90), 0.0, 0.0)
    sc.camera = co
    sc.render.resolution_x = px_w
    sc.render.resolution_y = px_h
    return co


def vykresli(nazev, sirka, px_w, px_h, sestava, tmp):
    """sestava(objekty, kolekce, rng) rozmisti kopie. Vrati RGBA float pole (px_h, px_w, 4), radky odshora."""
    sc = scena()
    zdroje = {}
    for m in ["grass_medium_01", "grass_medium_02", "fern_02", "dandelion_01", "weed_plant_02",
              "celandine_01", "periwinkle_plant", "nettle_plant"]:
        zdroje.update(nacti(m))
    kol = bpy.data.collections.new("zaber")
    sc.collection.children.link(kol)
    rng = random.Random(sum(map(ord, nazev)))
    sestava(zdroje, kol, rng, sirka)
    kamera(sc, sirka, px_w, px_h)
    cesta = os.path.join(tmp, nazev + ".png")
    sc.render.filepath = cesta
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(cesta)
    a = np.array(img.pixels[:], dtype=np.float32).reshape(px_h, px_w, 4)[::-1]
    return a


def najdi(zdroje, prefix):
    return [o for n, o in sorted(zdroje.items()) if n.startswith(prefix)]


def rada(zdroje, kol, rng, sirka, prefixy, n, s0, s1, hloubka=0.25, okraj=0.08):
    kusy = []
    for p in prefixy:
        kusy += najdi(zdroje, p)
    for i in range(n):
        o = rng.choice(kusy)
        x = (-0.5 + okraj + (1.0 - 2 * okraj) * (i + rng.random()) / n) * sirka
        kopie(o, x, rng.uniform(-hloubka, hloubka), rng.uniform(0, math.tau), rng.uniform(s0, s1), kol)


def b_nizka(z, k, r, w):
    rada(z, k, r, w, ["grass_medium_02_b", "grass_medium_02_c", "grass_medium_02_d", "grass_medium_01_small", "grass_medium_01_mid"], 14, 0.95, 1.2, okraj=0.16)


def b_vysoka(z, k, r, w):
    rada(z, k, r, w, ["grass_medium_01_mid", "grass_medium_02_c", "grass_medium_02_d"], 7, 1.1, 1.3, okraj=0.16)
    rada(z, k, r, w, ["grass_medium_01_tall", "grass_medium_02_e"], 7, 1.2, 1.5, okraj=0.2)


def b_sucha(z, k, r, w):
    rada(z, k, r, w, ["grass_medium_01_tall", "grass_medium_01_large", "grass_medium_02_e"], 10, 1.1, 1.4, okraj=0.16)


def b_jitrocel(z, k, r, w):
    rada(z, k, r, w, ["weed_plant_02_a", "weed_plant_02_b", "weed_plant_02_c"], 4, 0.9, 1.1, okraj=0.26, hloubka=0.1)
    rada(z, k, r, w, ["celandine_01_a", "celandine_01_b", "celandine_01_e"], 3, 0.9, 1.1, okraj=0.2, hloubka=0.1)
    rada(z, k, r, w, ["grass_medium_02_a", "grass_medium_02_b"], 4, 0.8, 1.0, okraj=0.15, hloubka=0.15)


def b_kapradi(z, k, r, w):
    kopie(najdi(z, "fern_02_b")[0], -0.17 * w, 0.0, 0.4, 0.62, k)
    kopie(najdi(z, "fern_02_c")[0], 0.19 * w, 0.2, 2.1, 0.6, k)
    kopie(najdi(z, "fern_02_a")[0], 0.0, -0.3, 1.0, 0.7, k)


def b_kvety(z, k, r, w):
    rada(z, k, r, w, ["grass_medium_02_b", "grass_medium_02_c", "grass_medium_01_small"], 6, 0.8, 1.0, okraj=0.14, hloubka=0.2)
    rada(z, k, r, w, ["dandelion_01_a", "dandelion_01_b", "dandelion_01_c"], 3, 1.0, 1.25, okraj=0.2, hloubka=0.1)
    rada(z, k, r, w, ["celandine_01_c", "celandine_01_d"], 2, 1.0, 1.2, okraj=0.25, hloubka=0.05)
    rada(z, k, r, w, ["periwinkle_plant_04", "periwinkle_plant_05"], 2, 0.8, 1.0, okraj=0.3, hloubka=0.25)


# (nazev, sirka zaberu v m, sestava)
BUNKY = [
    ("nizka", 0.4, b_nizka),
    ("vysoka", 0.62, b_vysoka),
    ("sucha", 0.6, b_sucha),
    ("jitrocel", 0.36, b_jitrocel),
    ("kapradi", 0.62, b_kapradi),
    ("kvety", 0.45, b_kvety),
]


def suchost(a):
    """prebarvi zelenou travu do slamove (sucha trava), jas zachova."""
    rgb = a[..., :3]
    l = rgb @ np.array([0.3, 0.55, 0.15], dtype=np.float32)
    slama = np.stack([l * 1.45, l * 1.22, l * 0.62], axis=-1)
    out = a.copy()
    out[..., :3] = np.clip(rgb * 0.25 + slama * 0.75, 0.0, 1.0)
    return out


# barevne doladeni bunek pro hru (sRGB nasobek, sytost): skenovana trava je suchá a sediva (pozdni leto);
# louka ve hre ma byt sytejsi zelena jako drive geometricka stebla (spicky ~ 0.22, 0.38, 0.1)
LADENI = {
    "nizka": ((0.7, 0.88, 0.5), 1.2),
    "vysoka": ((0.68, 0.85, 0.48), 1.2),
    "sucha": ((0.85, 0.82, 0.7), 1.0),
    "jitrocel": ((0.85, 0.98, 0.7), 1.15),
    "kapradi": ((0.9, 1.0, 0.8), 1.1),
    "kvety": ((0.85, 0.95, 0.75), 1.1),
}


def doladit(a, nasob, sytost):
    rgb = a[..., :3]
    l = (rgb @ np.array([0.3, 0.55, 0.15], dtype=np.float32))[..., None]
    rgb = l + (rgb - l) * sytost
    out = a.copy()
    out[..., :3] = np.clip(rgb * np.array(nasob, dtype=np.float32), 0.0, 1.0)
    return out


def rozlij(a, kroky=24):
    """barvu krajnich pixelu rozlije do pruhlednych (mipmapy bez tmavych lemu), alfa zustava."""
    rgb = a[..., :3].copy()
    m = (a[..., 3] > 0.5).astype(np.float32)
    rgb *= m[..., None]
    for _ in range(kroky):
        if m.min() > 0.0:
            break
        s = np.zeros_like(rgb)
        c = np.zeros_like(m)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            s += np.roll(np.roll(rgb * m[..., None], dy, 0), dx, 1)
            c += np.roll(np.roll(m, dy, 0), dx, 1)
        nove = (m == 0) & (c > 0)
        rgb[nove] = s[nove] / c[nove][:, None]
        m = np.where(nove, 1.0, m)
    # zbytek: prumerna barva
    if m.min() == 0.0:
        prum = rgb[m > 0].mean(axis=0) if (m > 0).any() else np.array([0.2, 0.3, 0.1])
        rgb[m == 0] = prum
    out = a.copy()
    out[..., :3] = rgb
    return out


def main():
    tmp = os.path.join(KOREN, "blender", "tex_cache", "atlas_travy")
    os.makedirs(tmp, exist_ok=True)
    jen = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    atlas = np.zeros((VYSKA, SIRKA, 4), dtype=np.float32)
    for i, (nazev, sirka, fn) in enumerate(BUNKY):
        sl, ra = i % SL, i // SL
        x0 = int(round(sl * SIRKA / SL))
        x1 = int(round((sl + 1) * SIRKA / SL))
        pw, ph = x1 - x0, BH
        cache = os.path.join(tmp, nazev + ".npy")
        if jen and nazev not in jen and os.path.exists(cache):
            a = np.load(cache)
        else:
            a = vykresli(nazev, sirka, pw, ph, fn, tmp)
            np.save(cache, a)
        if nazev == "sucha":
            a = suchost(a)
        a = doladit(a, *LADENI[nazev])
        # pruhledny lem bunky (mipmapy neprotecou do sousedni bunky)
        a[:4, :, 3] = 0.0
        a[:, :3, 3] = 0.0
        a[:, -3:, 3] = 0.0
        atlas[ra * BH:(ra + 1) * BH, x0:x1] = a
        print("atlas: bunka %d %s (%dx%d px, sirka %.2f m, vyska %.2f m)" % (i, nazev, pw, ph, sirka, sirka * ph / pw))
    atlas = rozlij(atlas)
    img = bpy.data.images.new("trava_atlas", SIRKA, VYSKA, alpha=True)
    img.colorspace_settings.name = "sRGB"
    img.alpha_mode = "STRAIGHT"
    img.pixels[:] = atlas[::-1].ravel()
    img.filepath_raw = VYSTUP
    img.file_format = "PNG"
    img.save()
    print("atlas ulozen:", VYSTUP)


if __name__ == "__main__":
    main()
