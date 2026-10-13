"""Erbovni stity pro zalozky menu: 3D render (smaltove pole s jemnym damaskem, zlaty zaobleny lem s nyty,
vypoukla figura z kovu). Figury jsou SVG ikony z game-icons.net (CC BY 3.0, autori Lorc a Delapouite).
  /opt/bl/bin/python erby.py   -> ../obrazky/erby/<nazev>.png (RGBA, 384 px)
"""
import math
import os
import sys

import bpy  # noqa: E402
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "obrazky", "erby")
SVG = os.path.join(HERE, "tex_cache", "game_icons")

# nazev: (barva pole, kov figury, ikona)
STITY = {
    "vse": ((0.2, 0.008, 0.008), "stribro", "lion"),
    "zbrane": ((0.008, 0.03, 0.17), "zlato", "crossed-swords"),
    "zbroj": ((0.01, 0.09, 0.025), "stribro", "visored-helm"),
    "naradi": ((0.012, 0.011, 0.01), "zlato", "claw-hammer"),
    "jidlo": ((0.26, 0.06, 0.005), "zlato", "wheat"),
    "nadoby": ((0.09, 0.012, 0.1), "zlato", "barrel"),
    "ostatni": ((0.05, 0.05, 0.055), "zlato", "key"),
    "venku": ((0.01, 0.09, 0.025), "zlato", "castle"),
    "uvnitr": ((0.2, 0.008, 0.008), "zlato", "bed"),
    "dekorace": ((0.008, 0.03, 0.17), "zlato", "candle-light"),
    "remeslo": ((0.012, 0.011, 0.01), "zlato", "anvil"),
    "zbrojnice": ((0.09, 0.012, 0.1), "stribro", "battle-axe"),
    "polozene": ((0.01, 0.09, 0.025), "stribro", "fleur-de-lys"),
}


def outline(n=40):
    """Obrys gotickeho stitu (heater): rovny horni okraj, svisle boky a dva kruhove oblouky do spice
    (stred oblouku v protejsim rohu, polomer = sirka stitu)."""
    w, top, mid = 1.0, 1.15, 0.3
    R = 2 * w
    right = []
    tmax = math.acos((0 + w) / R)       # x = 0 -> cos t = w / R
    for i in range(n + 1):
        t = tmax * i / n
        right.append((-w + R * math.cos(t), mid - R * math.sin(t)))
    pts = [(-w, top), (w, top)] + right[:-1] + [(0.0, right[-1][1])]
    pts += [(-x, y) for x, y in reversed(right[:-1])]
    return pts


def mat(name, col, metal=0.0, rough=0.4, damask=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if damask:
        # jemny damask (kosoctverecna mrizka) a sumovy povrch smaltu
        tc = nt.nodes.new("ShaderNodeTexCoord")
        w1 = nt.nodes.new("ShaderNodeTexWave")
        w1.inputs["Scale"].default_value = 3.0
        w1.bands_direction = "DIAGONAL"
        w2 = nt.nodes.new("ShaderNodeTexWave")
        w2.inputs["Scale"].default_value = 3.0
        w2.bands_direction = "DIAGONAL"
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, 0, math.pi / 2)
        nt.links.new(tc.outputs["Object"], w1.inputs["Vector"])
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], w2.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMath")
        mx.operation = "MULTIPLY"
        nt.links.new(w1.outputs["Fac"], mx.inputs[0])
        nt.links.new(w2.outputs["Fac"], mx.inputs[1])
        ramp = nt.nodes.new("ShaderNodeMix")
        ramp.data_type = "RGBA"
        nt.links.new(mx.outputs[0], ramp.inputs["Factor"])
        ramp.inputs["A"].default_value = (*col, 1)
        ramp.inputs["B"].default_value = (col[0] * 1.18 + 0.01, col[1] * 1.18 + 0.01, col[2] * 1.18 + 0.01, 1)
        nt.links.new(ramp.outputs["Result"], b.inputs["Base Color"])
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 18.0
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.12
        nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def curve_from(pts, name, z=0.0):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "2D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, (x, y) in zip(sp.points, pts):
        p.co = (x, y, z, 1)
    sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def shield(field_col, metal, icon):
    gold = mat("zlato", (0.95, 0.68, 0.28), 1.0, 0.28)
    silver = mat("stribro", (0.9, 0.9, 0.92), 1.0, 0.22)
    field = mat("pole", field_col, 0.0, 0.5, damask=True)
    # figura: kov s lesklym povrchem, ale s difuzni slozkou (lic miri do kamery a jinak by odrazel tmu)
    fig_gold = mat("fig_zlato", (1.0, 0.72, 0.3), 0.55, 0.32)
    fig_silver = mat("fig_stribro", (0.92, 0.92, 0.95), 0.45, 0.28)
    pts = outline()
    # pole: vyplnena krivka s tloustkou a zaoblenou hranou
    f = curve_from(pts, "pole")
    f.data.fill_mode = "BOTH"
    f.data.extrude = 0.06
    f.data.materials.append(field)
    # zlaty lem: trubka po obrysu + tenka vnitrni linka
    r = curve_from(pts, "lem", 0.07)
    r.data.dimensions = "3D"
    r.data.bevel_depth = 0.075
    r.data.bevel_resolution = 4
    r.data.materials.append(gold)
    inner = [(x * 0.86, y * 0.88 + 0.02) for x, y in pts]
    r2 = curve_from(inner, "linka", 0.065)
    r2.data.dimensions = "3D"
    r2.data.bevel_depth = 0.018
    r2.data.materials.append(gold)
    # nyty po lemu
    for i in range(1, len(pts), 7):
        x, y = pts[i]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(x, y, 0.15), segments=12, ring_count=6)
        bpy.context.object.data.materials.append(gold)
    # figura ze SVG
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=os.path.join(SVG, icon + ".svg"))
    new = [o for o in bpy.data.objects if o not in before and o.type == "CURVE"]
    # prvni cesta je cerny ctverec pozadi
    new.sort(key=lambda o: -(o.dimensions.x * o.dimensions.y))
    for o in new[:1]:
        bpy.data.objects.remove(o)
    figs = new[1:]
    for o in figs:
        o.data.extrude = 0.0012
        o.data.bevel_depth = 0.0004
        o.data.materials.clear()
        o.data.materials.append(fig_gold if metal == "zlato" else fig_silver)
    bpy.context.view_layer.update()
    # sjednotit velikost a stred (SVG ma 512 px ~ 0.18 m v Blenderu)
    mn = Vector((1e9, 1e9))
    mx = Vector((-1e9, -1e9))
    for o in figs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn.x, mn.y = min(mn.x, w.x), min(mn.y, w.y)
            mx.x, mx.y = max(mx.x, w.x), max(mx.y, w.y)
    size = max(mx.x - mn.x, mx.y - mn.y)
    k = 1.25 / size
    cx, cy = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2
    for o in figs:
        o.location = ((o.location.x - cx) * k, (o.location.y - cy) * k + 0.05, 0.07)
        o.scale = (o.scale.x * k, o.scale.y * k, o.scale.z * k * 25)


def scene_setup():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64
    sc.render.resolution_x = 384
    sc.render.resolution_y = 384
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    cam = bpy.data.cameras.new("K")
    cam.type = "ORTHO"
    cam.ortho_scale = 2.95
    co = bpy.data.objects.new("K", cam)
    co.location = (0, -0.12, 6)
    sc.collection.objects.link(co)
    sc.camera = co
    # studiove HDRI (Poly Haven, CC0): kovy maji co odrazet
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    env = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(HERE, "tex_cache", "studio_small_09_1k.hdr"))
    w.node_tree.links.new(env.outputs["Color"], w.node_tree.nodes["Background"].inputs[0])
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    sc.world = w
    for loc, en, sz in (((-3, 3, 5), 350, 3), ((3, -2, 3), 80, 4)):
        L = bpy.data.lights.new("L", "AREA")
        L.energy = en
        L.size = sz
        lo = bpy.data.objects.new("L", L)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)
    return co


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(STITY)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for n in names:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene_setup()
        shield(*STITY[n])
        bpy.context.scene.render.filepath = os.path.join(OUT, n + ".png")
        bpy.ops.render.render(write_still=True)
        print("erb", n)
