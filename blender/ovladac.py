"""Bily herni ovladac (Xbox) jako 3D model vyrenderovany pro napovedu v menu.
  /opt/bl/bin/python ovladac.py  -> ../obrazky/ovladac.png (RGBA) a ../obrazky/ovladac.json (body popisku 0..1)
Telo vznikne sjednocenim elipsoidu (stred, ramena, rukojeti) a voxelovym remeshem, ovladaci prvky se usazuji
na povrch paprskem shora. Souradnice: x doprava, y nahoru (k ramennim tlacitkum), z z licni plochy ven."""
import json
import math
import os

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PNG = os.path.join(HERE, "..", "obrazky", "ovladac.png")
OUT_JSON = os.path.join(HERE, "..", "obrazky", "ovladac.json")


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, col, rough=0.45, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 1.0
    return m


def ellipsoid(loc, scale, rot_z=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=loc)
    o = bpy.context.object
    o.scale = scale
    o.rotation_euler = (0, 0, math.radians(rot_z))
    return o


def rounded_box(loc, size, rot_z=0.0, bevel=0.2):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.rotation_euler = (0, 0, math.radians(rot_z))
    bpy.ops.object.transform_apply(scale=True, rotation=False, location=False)
    m = o.modifiers.new("b", "BEVEL")
    m.width = bevel
    m.segments = 5
    return o


def cyl(loc, r, h, m, verts=48, bevel=0.04):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=(loc[0], loc[1], loc[2] + h / 2))
    o = bpy.context.object
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 3
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def build():
    white = mat("bila", (0.86, 0.86, 0.84), 0.42)
    grey = mat("seda", (0.62, 0.63, 0.64), 0.5)
    dark = mat("tmava", (0.035, 0.035, 0.04), 0.45)
    rubber = mat("guma", (0.06, 0.06, 0.065), 0.8)
    silver = mat("stribro", (0.75, 0.76, 0.78), 0.25, 0.8)
    cols = {"A": (0.1, 0.55, 0.15), "B": (0.75, 0.1, 0.08), "X": (0.1, 0.3, 0.8), "Y": (0.85, 0.65, 0.05)}
    letters = {k: mat("pismeno_" + k, c, 0.4) for k, c in cols.items()}

    # --- telo
    parts = [
        ellipsoid((0, 0.7, 0), (5.9, 3.5, 1.35)),
        ellipsoid((0, 2.5, -0.1), (6.6, 1.9, 1.15)),
        ellipsoid((-4.5, -1.5, -0.15), (2.25, 3.5, 1.4), -26),
        ellipsoid((4.5, -1.5, -0.15), (2.25, 3.5, 1.4), 26),
    ]
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    body = bpy.context.object
    bpy.ops.object.transform_apply(scale=True, rotation=True, location=False)
    r = body.modifiers.new("r", "REMESH")
    r.mode = "VOXEL"
    r.voxel_size = 0.07
    bpy.ops.object.modifier_apply(modifier="r")
    s = body.modifiers.new("s", "SMOOTH")
    s.factor = 1.0
    s.iterations = 12
    bpy.ops.object.modifier_apply(modifier="s")
    # zplostit lic (horni stranu) jako u skutecneho ovladace
    for v in body.data.vertices:
        if v.co.z > 0.95:
            v.co.z = 0.95 + (v.co.z - 0.95) * 0.35
    body.data.materials.append(white)
    bpy.ops.object.shade_smooth()

    dg = bpy.context.evaluated_depsgraph_get()

    def surf(x, y):
        hit, loc, nrm, *_ = body.ray_cast(Vector((x, y, 20)), Vector((0, 0, -1)), depsgraph=dg)
        return loc if hit else Vector((x, y, 1.0))

    anchors = {}
    # packy: kruzek v tele, krcek, hlava s gumovym okrajem a prohlubni
    for name, (x, y) in (("LS", (-4.35, 1.35)), ("RS", (2.15, -1.05))):
        p = surf(x, y)
        cyl((x, y, p.z - 0.25), 1.15, 0.3, rubber, bevel=0.05)
        cyl((x, y, p.z), 0.45, 0.55, dark, bevel=0.0)
        cyl((x, y, p.z + 0.5), 0.95, 0.35, dark, bevel=0.1)
        cyl((x, y, p.z + 0.82), 0.78, 0.06, rubber, bevel=0.03)
        anchors[name] = (x, y, p.z + 0.9)
    # krizovy ovladac
    x, y = -2.15, -1.05
    p = surf(x, y)
    cyl((x, y, p.z - 0.2), 1.05, 0.28, grey, bevel=0.05)
    for rot in (0, 90):
        o = rounded_box((x, y, p.z + 0.18), (1.6, 0.52, 0.22), rot, 0.08)
        o.data.materials.append(dark)
    anchors["DPAD"] = (x, y, p.z + 0.3)
    # ABXY
    cx, cy = 4.35, 1.35
    for k, (dx, dy) in {"A": (0, -0.9), "B": (0.9, 0), "X": (-0.9, 0), "Y": (0, 0.9)}.items():
        bx, by = cx + dx, cy + dy
        p = surf(bx, by)
        cyl((bx, by, p.z - 0.15), 0.43, 0.45, dark, bevel=0.08)
        bpy.ops.object.text_add(location=(bx, by, p.z + 0.31))
        t = bpy.context.object
        t.data.body = k
        t.data.size = 0.55
        t.data.align_x = "CENTER"
        t.data.align_y = "CENTER"
        t.data.extrude = 0.01
        t.data.materials.append(letters[k])
        anchors[k] = (bx, by, p.z + 0.3)
    # tlacitko Xbox (stribrny kruh s tmavym stredem), Zobrazeni, Nabidka, Sdileni
    p = surf(0, 2.55)
    cyl((0, 2.55, p.z - 0.1), 0.66, 0.24, silver, bevel=0.06)
    cyl((0, 2.55, p.z + 0.12), 0.5, 0.03, dark, bevel=0.0)
    anchors["XBOX"] = (0, 2.55, p.z + 0.15)
    for name, (x, y) in (("VIEW", (-1.25, 1.2)), ("MENU", (1.25, 1.2)), ("SHARE", (0, 0.55))):
        p = surf(x, y)
        cyl((x, y, p.z - 0.1), 0.25, 0.2, dark, bevel=0.04)
        anchors[name] = (x, y, p.z + 0.1)
    # ramenni tlacitka a spouste na horni hrane
    for sx, nb, nt in ((-1, "LB", "LT"), (1, "RB", "RT")):
        o = rounded_box((sx * 4.3, 3.85, -0.05), (3.4, 0.9, 0.7), -sx * 10, 0.25)
        o.data.materials.append(dark)
        o = rounded_box((sx * 4.6, 4.2, -0.7), (2.3, 1.1, 1.3), -sx * 10, 0.3)
        o.data.materials.append(dark)
        anchors[nb] = (sx * 4.4, 4.3, 0.4)
        anchors[nt] = (sx * 4.7, 4.85, -0.2)
    return anchors


def render(anchors):
    sc = bpy.context.scene
    cam = bpy.data.cameras.new("K")
    cam.lens = 85
    co = bpy.data.objects.new("K", cam)
    sc.collection.objects.link(co)
    co.location = (0, -13, 45)
    d = Vector((0, 0.3, 0)) - co.location
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    sc.render.resolution_x = 1400
    sc.render.resolution_y = 1000
    sc.render.film_transparent = True
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 96
    sc.cycles.device = "CPU"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.88, 0.82, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    sc.world = w
    for loc, en, size in (((-8, -10, 18), 2200, 10), ((10, 6, 12), 700, 8)):
        L = bpy.data.lights.new("L", "AREA")
        L.energy = en
        L.size = size
        lo = bpy.data.objects.new("L", L)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)
    pts = {}
    for k, p in anchors.items():
        v = world_to_camera_view(sc, co, Vector(p))
        pts[k] = [round(v.x, 4), round(1.0 - v.y, 4)]
    # orez na obrys ovladace a zmenseni, body prepocitat
    from PIL import Image
    im = Image.open(OUT_PNG)
    bb = im.getchannel("A").getbbox()
    bb = (bb[0] - 10, bb[1] - 10, bb[2] + 10, bb[3] + 10)
    c = im.crop(bb)
    c = c.resize((c.width * 3 // 4, c.height * 3 // 4), Image.LANCZOS)
    c.save(OUT_PNG, optimize=True)
    for k, (x, y) in pts.items():
        pts[k] = [round((x * 1400 - bb[0]) / (bb[2] - bb[0]), 4), round((y * 1000 - bb[1]) / (bb[3] - bb[1]), 4)]
    json.dump({"size": list(c.size), "body": pts}, open(OUT_JSON, "w"), indent=1)
    print("ulozeno", OUT_PNG, pts)


if __name__ == "__main__":
    reset()
    render(build())
