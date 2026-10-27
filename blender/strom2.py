"""Stromy v3 (radce 19:40, Misa: max kvalita jako borovice z Disku): jablon, lipa, dub modelovane v Blenderu z fotek.
Postup jako u kupovanych stromu (SpeedTree): 1) vetvicky s listy z fotoskenu (ambientCG LeafSet, CC0) a plody
(jablko Poly Haven food_apple_01, CC0; zalud modelovany) se vyfoti shora do atlasu 2x2 - barva s alfou a normala
(tecny prostor karty); 2) kostra stromu roste po urovnich (kmen s korenovym nabehem, ramena, vetve, vetvicky),
krivi se nizkofrekvencnim sumem, gravitaci a za svetlem; trubky s kurou z fotek (Poly Haven), UV v metrech;
3) na koncove vetve se nasadi zalomene karty z atlasu (natocene od stredu koruny a k nebi); normaly listi od stredu
koruny, AO do alfy barvy vrcholu (pravidla_modelu.json trida strom). LOD1 = mene karet + vetve bez nejmensich
(decimace), impostor dela impostory.py z LOD0.

  /opt/bl/bin/python blender/strom2.py [druh ...] [--nahled soubor.png]
Vystup: modely/nove/<druh>.glb (LOD0), <druh>_daleko.glb (LOD1), blender/tex_cache/strom2/<druh>_listi_{c,n}.png
Predlohy (Misa 27. 10.): jablon - nizky kmen deleny do 2-3 pokroucenych ramen, hadovite vetve, konce pod plody
previsle, koruna sirsi nez vyssi; dub - mohutny kmen s hlubokymi brazdami, ve 3-4 m deleny do mnoha krivych ramen
vzhuru a do stran, koruna siroka husta, listi tmave zelene lalocnate, zaludy v trsech; lipa - vzrostla 15 m,
prubezny kmen, vejcita husta koruna, srdcite listy."""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEX = os.path.join(HERE, "tex_cache")
OUT_TEX = os.path.join(TEX, "strom2")
OUT_GLB = os.path.join(ROOT, "modely", "nove")
SKIN = False

# list v sade: (y0, y1, x0, x1) v pixelech 2048 (radek 0 nahore), stopka dole, spicka nahore
LISTY = {
    "LeafSet001": [(73, 932, 131, 490), (193, 938, 1412, 1746), (1132, 1942, 820, 1181), (1147, 1890, 149, 482), (1161, 1917, 1494, 1806)],
    "LeafSet004": [(86, 994, 224, 698), (89, 1011, 766, 1272), (124, 958, 1322, 1857), (1084, 1961, 256, 726), (1107, 1959, 849, 1285), (1123, 1953, 1380, 1848)],
    "LeafSet016": [(71, 936, 93, 539), (96, 873, 691, 1217), (122, 871, 1349, 1913), (1146, 1934, 73, 653), (1163, 1935, 1413, 1882), (1170, 1915, 780, 1283)],
}

DRUHY = {
    "jablon": dict(
        vyska=5.2, listy="LeafSet001", tint=(0.62, 0.78, 0.55), kura="bark_brown_02", kura_m=0.9,
        karta_m=0.65, list_m=0.075, listu=26, plod="jablko", plodu=(1, 3), plod_karet=3,
        kmen=dict(delka=1.5, r=0.24, krivost=0.3, sklon=0.05),
        ramena=dict(n=(3, 4), od=1.0, uhel=(38, 58), delka=(3.0, 3.8), r=0.75, krivost=0.6, gravitace=0.06, svetlo=0.05),
        vetve=dict(rozestup=(0.22, 0.35), uhel=(45, 80), delka=(1.2, 2.2), r=0.6, krivost=0.5, gravitace=0.3, svetlo=0.0, od=0.1),
        vetvicky=dict(rozestup=(0.18, 0.28), uhel=(40, 75), delka=(0.4, 0.8), r=0.5, krivost=0.35, gravitace=0.35, svetlo=0.05, od=0.1),
        karet_m=0.065, koruna=(1.25, 0.62), listi_od=0.2, cil_troj=12000),
    "dub": dict(
        vyska=15.0, listy="LeafSet016", tint=(0.42, 0.62, 0.36), kura="jolcham_oak_bark_01", kura_m=1.4,
        karta_m=1.0, list_m=0.11, listu=22, plod="zalud", plodu=(2, 4), plod_karet=1,
        kmen=dict(delka=3.6, r=0.55, krivost=0.12, sklon=0.04),
        ramena=dict(n=(4, 6), od=2.9, uhel=(22, 55), delka=(6.0, 8.5), r=0.55, krivost=0.6, gravitace=0.0, svetlo=0.06),
        vetve=dict(rozestup=(0.7, 1.1), uhel=(40, 70), delka=(2.2, 3.8), r=0.42, krivost=0.55, gravitace=0.1, svetlo=0.05, od=0.15),
        vetvicky=dict(rozestup=(0.45, 0.7), uhel=(35, 65), delka=(0.8, 1.5), r=0.5, krivost=0.4, gravitace=0.15, svetlo=0.05, od=0.15),
        karet_m=0.2, koruna=(0.95, 0.62), listi_od=0.35, cil_troj=12000),
    "lipa": dict(
        vyska=15.5, listy="LeafSet004", tint=(0.55, 0.72, 0.45), kura="tree_bark_03", kura_m=1.2,
        karta_m=0.9, list_m=0.085, listu=24, plod=None, plodu=(0, 0), plod_karet=0,
        kmen=dict(delka=14.0, r=0.42, krivost=0.08, sklon=0.03, provod=True),
        ramena=dict(rozestup=(0.38, 0.6), od=3.4, uhel=(50, 75), delka=(3.0, 5.5), r=0.42, krivost=0.4, gravitace=0.06, svetlo=0.1),
        vetve=dict(rozestup=(0.55, 0.85), uhel=(40, 65), delka=(1.2, 2.4), r=0.45, krivost=0.4, gravitace=0.1, svetlo=0.06, od=0.15),
        vetvicky=dict(rozestup=(0.4, 0.6), uhel=(35, 60), delka=(0.5, 1.0), r=0.5, krivost=0.3, gravitace=0.12, svetlo=0.05, od=0.15),
        karet_m=0.17, koruna=(0.62, 0.8), listi_od=0.3, cil_troj=12000),
}


# ------------------------------------------------------------------ materialy

def _img(path, data=False):
    im = bpy.data.images.load(path, check_existing=True)
    if data:
        im.colorspace_settings.name = "Non-Color"
    return im


def _mat_emise(name, color_img, alpha_img=None, nrm_img=None, tint=(1, 1, 1), mode="barva", uv_vc=True):
    """Material pro foceni atlasu: barva (emise = albedo, zadne svetlo) nebo normala (emise = N * 0.5 + 0.5)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    ct = nt.nodes.new("ShaderNodeTexImage")
    ct.image = color_img
    if mode == "barva":
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        nt.links.new(ct.outputs["Color"], mul.inputs[6])
        if uv_vc:
            vc = nt.nodes.new("ShaderNodeVertexColor")
            vc.layer_name = "Tint"
            nt.links.new(vc.outputs["Color"], mul.inputs[7])
        else:
            mul.inputs[7].default_value = (*tint, 1.0)
        nt.links.new(mul.outputs[2], em.inputs["Color"])
    else:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        nsrc = geo.outputs["Normal"]
        if nrm_img is not None:
            nt_ = nt.nodes.new("ShaderNodeTexImage")
            nt_.image = nrm_img
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nm.uv_map = "UVMap"
            nt.links.new(nt_.outputs["Color"], nm.inputs["Color"])
            nsrc = nm.outputs["Normal"]
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "MULTIPLY_ADD"
        sc.inputs[1].default_value = (0.5, 0.5, 0.5)
        sc.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(nsrc, sc.inputs[0])
        nt.links.new(sc.outputs[0], em.inputs["Color"])
    if alpha_img is not None:
        at = nt.nodes.new("ShaderNodeTexImage")
        at.image = alpha_img
        nt.links.new(at.outputs["Color"], mix.inputs["Fac"])
    else:
        mix.inputs["Fac"].default_value = 1.0
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


# ------------------------------------------------------------------ atlas vetvicek

class _Geo:
    def __init__(self):
        self.v, self.f, self.uv, self.tint = [], [], [], []

    def add(self, pts, faces, uvs, tint):
        i0 = len(self.v)
        self.v += pts
        for fc, uvf in zip(faces, uvs):
            self.f.append(tuple(i0 + k for k in fc))
            self.uv.append(uvf)
            self.tint.append(tint)

    def mesh(self, name):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p) for p in self.v], [], self.f)
        me.uv_layers.new(name="UVMap")
        me.color_attributes.new("Tint", "FLOAT_COLOR", "CORNER")
        uvl, ca = me.uv_layers["UVMap"], me.color_attributes["Tint"]
        for poly, uvf, t in zip(me.polygons, self.uv, self.tint):
            for k in range(poly.loop_total):
                uvl.data[poly.loop_start + k].uv = uvf[k]
                ca.data[poly.loop_start + k].color = (*t, 1.0)
        return me


def _leaf(G, rnd, base, d, nrm, L, box, tint):
    """List z fotoskenu: dva pasy podel zilky (preloz do V), 4 rady po delce prohnute dolu."""
    y0, y1, x0, x1 = box
    W = L * (x1 - x0) / (y1 - y0)
    side = d.cross(nrm).normalized()
    nrm = side.cross(d).normalized()
    fold = rnd.uniform(0.12, 0.3)
    curl = rnd.uniform(0.05, 0.18)
    rows = 5
    pts, uvs = [], []
    for r in range(rows):
        t = r / (rows - 1)
        c = base + d * (L * t) - nrm * (curl * L * t * t)
        for s in (-1.0, 0.0, 1.0):
            pts.append(c + side * (s * W / 2) + nrm * (abs(s) * fold * W * 0.5))
            uvs.append(((x0 + (s + 1) / 2 * (x1 - x0)) / 2048.0, 1.0 - (y1 - t * (y1 - y0)) / 2048.0))
    faces, fuv = [], []
    for r in range(rows - 1):
        for c in range(2):
            a = r * 3 + c
            q = (a, a + 1, a + 4, a + 3)
            faces.append(q)
            fuv.append([uvs[k] for k in q])
    G.add(pts, faces, fuv, tint)


def _tube(G, pts, radii, sides, uvbox, tint):
    """Trubka pro vetvicku v atlasu (UV na kousek kury)."""
    u0, v0, u1, v1 = uvbox
    rings = []
    for k, (p, r) in enumerate(zip(pts, radii)):
        d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        a = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))).normalized()
        b = d.cross(a)
        rings.append([p + (a * math.cos(2 * math.pi * s / sides) + b * math.sin(2 * math.pi * s / sides)) * r for s in range(sides)])
    for k in range(len(pts) - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            q = [rings[k][s], rings[k][s2], rings[k + 1][s2], rings[k + 1][s]]
            uv = [(u0 + (u1 - u0) * s / sides, v0 + (v1 - v0) * k / len(pts)), (u0 + (u1 - u0) * (s + 1) / sides, v0 + (v1 - v0) * k / len(pts)),
                  (u0 + (u1 - u0) * (s + 1) / sides, v0 + (v1 - v0) * (k + 1) / len(pts)), (u0 + (u1 - u0) * s / sides, v0 + (v1 - v0) * (k + 1) / len(pts))]
            G.add(q, [(0, 1, 2, 3)], [uv], tint)


def _zalud(G, c, s, tint_cupule, tint_nut):
    """Zalud: ciska (polokoule s hrbolky) a protahly orisek, osa dolu."""
    seg = 10
    for part, (rz, rr, z0, tint) in enumerate(((0.55, 0.52, 0.0, tint_cupule), (1.3, 0.42, -0.2, tint_nut))):
        rings = []
        for k in range(7):
            t = k / 6
            ang = t * math.pi * (0.5 if part == 0 else 1.0)
            if part == 0:
                z = z0 - rz * math.sin(ang) * s * 0.6
                r = rr * s * (math.cos(ang) * 0.4 + 0.6) * (1.0 if k else 0.3)
            else:
                z = z0 * s - rz * s * t
                r = rr * s * math.sin(math.pi * min(1.0, 0.15 + t * 0.85)) ** 0.7
            rings.append([c + Vector((r * math.cos(2 * math.pi * j / seg), r * math.sin(2 * math.pi * j / seg), z)) for j in range(seg)])
        for k in range(6):
            for j in range(seg):
                j2 = (j + 1) % seg
                G.add([rings[k][j], rings[k][j2], rings[k + 1][j2], rings[k + 1][j]], [(0, 1, 2, 3)], [[(0.5, 0.5)] * 4], tint)


def bake_atlas(druh, res=2048):
    """Atlas 2x2 vetvicek druhu: <druh>_listi_c.png (barva + alfa), <druh>_listi_n.png (normala tecneho prostoru)."""
    P = DRUHY[druh]
    os.makedirs(OUT_TEX, exist_ok=True)
    import scene
    scene.reset()
    rnd = random.Random(hash(druh) & 0xffff)
    ls = P["listy"]
    LD = os.path.join(TEX, "listy", ls)
    cimg = _img(os.path.join(LD, "%s_2K-PNG_Color.png" % ls))
    aimg = _img(os.path.join(LD, "%s_2K-PNG_Opacity.png" % ls), True)
    nimg = _img(os.path.join(LD, "%s_2K-PNG_NormalGL.png" % ls), True)
    KD = os.path.join(TEX, "kury")
    kimg = _img(os.path.join(KD, "%s_diff_1k.jpg" % P["kura"]))
    knimg = _img(os.path.join(KD, "%s_nor_gl_1k.jpg" % P["kura"]), True)
    S = P["karta_m"]
    GL, GT = _Geo(), _Geo()          # listy, vetvicky
    GP = _Geo()                      # plody (zaludy) z geometrie
    apples = []
    boxes = LISTY[ls]
    for cell in range(4):
        ox, oy = (cell % 2) * 1.0, (cell // 2) * 1.0
        base = Vector((ox + 0.5 + rnd.uniform(-0.04, 0.04), oy + 0.03, 0.0))
        # hlavni osa vetvicky: od dolniho okraje nahoru, mirne prohnuta
        n = 9
        ang0 = rnd.uniform(-0.15, 0.15)
        axis = []
        d = Vector((math.sin(ang0), math.cos(ang0), 0.0))
        p = base.copy()
        for k in range(n):
            axis.append(p.copy())
            d = (d + Vector((rnd.uniform(-0.12, 0.12), 0, 0))).normalized()
            p = p + d * (0.86 / (n - 1))
        twigs = [axis]
        for k in range(2, n - 1):
            sg = 1 if (k + cell) % 2 else -1
            a = math.radians(rnd.uniform(30, 55))
            dd = (Matrix.Rotation(sg * a, 3, "Z") @ (axis[k + 1] - axis[k]).normalized())
            ln = rnd.uniform(0.18, 0.3) * (1.1 - 0.6 * k / n)
            tw = [axis[k] + dd * (ln * j / 4) + Vector((0, 0, 0.002 * j)) for j in range(5)]
            # mirne zahnuti vedlejsi vetvicky k ose
            tw = [q + Vector((0, 0.03 * ln * (j / 4) ** 2, 0)) for j, q in enumerate(tw)]
            twigs.append(tw)
        L = P["list_m"] / S
        nleaf = 0
        for ti, tw in enumerate(twigs):
            r0 = 0.006 if ti == 0 else 0.0035
            _tube(GT, tw, [r0 * (1 - 0.6 * j / len(tw)) for j in range(len(tw))], 5, (0.4, 0.0, 0.6, 0.3), (1, 1, 1))
            tot = sum((tw[j + 1] - tw[j]).length for j in range(len(tw) - 1))
            step = L * 0.42
            s_ = step * 0.5
            side = 1
            while s_ < tot and nleaf < P["listu"] * 2:
                acc = 0.0
                for j in range(len(tw) - 1):
                    sl = (tw[j + 1] - tw[j]).length
                    if acc + sl >= s_:
                        t = (s_ - acc) / sl
                        pp = tw[j].lerp(tw[j + 1], t)
                        td = (tw[j + 1] - tw[j]).normalized()
                        break
                    acc += sl
                side = -side
                a = math.radians(rnd.uniform(35, 75)) * side
                ld = (Matrix.Rotation(a, 3, "Z") @ td)
                ld = (ld + Vector((0, 0, rnd.uniform(-0.15, 0.25)))).normalized()
                nrm = (Matrix.Rotation(rnd.uniform(-0.7, 0.7), 3, ld) @ Vector((0, 0, 1))).normalized()
                petiole = L * rnd.uniform(0.08, 0.18)
                lb = pp + ld * petiole + Vector((0, 0, 0.004 + rnd.uniform(0, 0.012)))
                _tube(GT, [pp, lb], [0.0018, 0.0012], 3, (0.45, 0.0, 0.55, 0.1), (0.75, 0.85, 0.6))
                tip = lb + ld * L * 1.15
                if not all(ox + 0.03 < q.x < ox + 0.97 and oy + 0.02 < q.y < oy + 0.98 for q in (lb, tip)):
                    s_ += step
                    continue
                tone = rnd.uniform(0.82, 1.12)
                tint = tuple(min(1.0, c * tone * rnd.uniform(0.95, 1.05)) for c in P["tint"])
                _leaf(GL, rnd, lb, ld, nrm, L * rnd.uniform(0.85, 1.15), rnd.choice(boxes), tint)
                nleaf += 1
                s_ += step * rnd.uniform(0.8, 1.2)
        # plody: jablka (fotosken) na konci osy, zaludy v trsech
        if P["plod"] and cell < P["plod_karet"]:
            for _ in range(rnd.randint(*P["plodu"])):
                tw = rnd.choice(twigs)
                c = tw[rnd.randint(len(tw) // 2, len(tw) - 1)] + Vector((rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), 0.03))
                if P["plod"] == "jablko":
                    apples.append((c, rnd.uniform(0.065, 0.085) / S, rnd.uniform(0, 6.28)))
                else:
                    for _k in range(rnd.randint(1, 3)):
                        cc = c + Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), 0.01))
                        _zalud(GP, cc, 0.018 / S, (0.42, 0.45, 0.22), (0.45, 0.55, 0.2))
    sc = bpy.context.scene
    obs = []
    for G, nm in ((GL, "listy"), (GT, "vetvicky"), (GP, "plody")):
        if not G.f:
            continue
        me = G.mesh(nm)
        ob = bpy.data.objects.new(nm, me)
        sc.collection.objects.link(ob)
        obs.append((ob, nm))
    if apples:
        bpy.ops.import_scene.gltf(filepath=os.path.join(TEX, "jablko", "food_apple_01_1k.gltf"))
        src = [o for o in bpy.context.selected_objects if o.type == "MESH"][0]
        dz = src.dimensions.z or 1.0
        for (c, s, yaw) in apples:
            o = src.copy()
            sc.collection.objects.link(o)
            o.matrix_world = Matrix.Translation(c) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Scale(s / dz, 4)
            obs.append((o, "jablko"))
        sc.collection.objects.unlink(src)
    am = bpy.data.materials.get("food_apple_01") or (src.data.materials[0] if apples else None)
    ap_img = None
    ap_nimg = None
    if am:
        for n in am.node_tree.nodes:
            if n.type == "TEX_IMAGE" and "diff" in n.image.name:
                ap_img = n.image
            if n.type == "TEX_IMAGE" and "nor" in n.image.name:
                ap_nimg = n.image
                ap_nimg.colorspace_settings.name = "Non-Color"
    cam = bpy.data.cameras.new("K")
    cam.type = "ORTHO"
    cam.ortho_scale = 2.0
    co = bpy.data.objects.new("K", cam)
    sc.collection.objects.link(co)
    co.location = (1.0, 1.0, 5.0)
    sc.camera = co
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 32
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 0
    sc.render.filter_size = 0.8
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    w = bpy.data.worlds.new("W")
    sc.world = w
    outs = {}
    for mode in ("barva", "normala"):
        # normala bez prevodu do sRGB (jinak 0,5 -> 0,73 a vsechny listy zkosene -> cerne)
        sc.view_settings.view_transform = "Standard" if mode == "barva" else "Raw"
        sc.view_settings.look = "None"          # scene.reset nastavuje kontrastni look - posunul by barvy i normaly
        sc.view_settings.exposure = 0.0
        sc.view_settings.gamma = 1.0
        mats = {
            "listy": _mat_emise("l_" + mode, cimg, aimg, nimg, mode=mode),
            "vetvicky": _mat_emise("v_" + mode, kimg, None, knimg, mode=mode),
            "plody": _mat_emise("p_" + mode, kimg, None, None, mode=mode),
            "jablko": _mat_emise("j_" + mode, ap_img, None, ap_nimg, mode=mode, uv_vc=False) if ap_img else None,
        }
        if mode == "barva":
            # vetvicky hnedozelene (mlada kura), plody jen barvou vrcholu
            pn = mats["plody"].node_tree
            for n in pn.nodes:
                if n.type == "TEX_IMAGE":
                    n.image = None
        for ob, nm in obs:
            ob.data.materials.clear()
            ob.data.materials.append(mats[nm])
        fp = os.path.join(OUT_TEX, "%s_listi_%s.png" % (druh, "c" if mode == "barva" else "n"))
        sc.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        outs[mode] = fp
    _dilate(outs["barva"], outs["normala"])
    print("atlas", druh, outs)
    return outs


def _dilate(cp, np_, kroku=40):
    """Barva pod pruhlednymi pixely = barva sousednich listu (jinak tmave lemy v mipmapach), postupne po 1 px;
    zbytek prumer. Normala dostane alfu z barvy."""
    import numpy as np
    from PIL import Image
    c = np.array(Image.open(cp).convert("RGBA")).astype(np.float32)
    n = np.array(Image.open(np_).convert("RGBA")).astype(np.float32)
    a0 = c[..., 3] > 160
    for img in (c, n):
        filled = a0.copy()
        rgb = img[..., :3]
        for _ in range(kroku):
            acc = np.zeros_like(rgb)
            cnt = np.zeros(filled.shape, np.float32)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                acc += np.roll(np.where(filled[..., None], rgb, 0), (dy, dx), (0, 1))
                cnt += np.roll(filled, (dy, dx), (0, 1))
            new = (~filled) & (cnt > 0)
            rgb[new] = acc[new] / cnt[new][:, None]
            filled |= new
        rgb[~filled] = rgb[a0].mean(0)
    n[..., 3] = c[..., 3]
    Image.fromarray(c.astype(np.uint8)).save(cp)
    Image.fromarray(n.astype(np.uint8)).save(np_)


# ------------------------------------------------------------------ kostra stromu

class Vetev:
    def __init__(self, pts, radii, uroven):
        self.pts, self.radii, self.uroven = pts, radii, uroven


def _noise(rnd):
    """Nizkofrekvencni sum podel delky: soucet 3 sinusu v kazde ose."""
    ks = [(rnd.uniform(0.4, 1.3), rnd.uniform(0, 6.28), rnd.uniform(0.5, 1.0)) for _ in range(9)]

    def f(s):
        v = [0.0, 0.0, 0.0]
        for i, (fr, ph, am) in enumerate(ks):
            v[i % 3] += am * math.sin(s * fr * 2.2 + ph)
        return Vector(v) / 1.6
    return f


def _rust(rnd, p0, d0, delka, r0, uroven, Q, seg):
    """Jedna vetev: body po seg m, smer = predchozi + krivost * sum + gravitace dolu + svetlo nahoru."""
    nz = _noise(rnd)
    pts, rr = [p0.copy()], [r0]
    d = d0.normalized()
    p = p0.copy()
    n = max(3, int(delka / seg) + 1)
    for k in range(1, n + 1):
        s = k * delka / n
        t = min(1.0, s / delka)
        tur = nz(s / max(delka, 1.0) * 3.0 + uroven)
        d = (d + tur * Q["krivost"] * 0.35 + Vector((0, 0, -1)) * Q.get("gravitace", 0.0) * 0.25 * (0.4 + t)
             + Vector((0, 0, 1)) * Q.get("svetlo", 0.0) * 0.25).normalized()
        p = p + d * (delka / n)
        pts.append(p.copy())
        rr.append(max(0.006, r0 * (1.0 - 0.8 * t) ** 1.3))
    return Vetev(pts, rr, uroven)


def _bod(v, t):
    """Bod a smer na vetvi v pomernem miste t (0..1)."""
    L = [0.0]
    for a, b in zip(v.pts, v.pts[1:]):
        L.append(L[-1] + (b - a).length)
    s = t * L[-1]
    for k in range(len(L) - 1):
        if L[k + 1] >= s:
            u = (s - L[k]) / max(L[k + 1] - L[k], 1e-6)
            return v.pts[k].lerp(v.pts[k + 1], u), (v.pts[k + 1] - v.pts[k]).normalized(), v.radii[k] * (1 - u) + v.radii[k + 1] * u, L[-1]
    return v.pts[-1], (v.pts[-1] - v.pts[-2]).normalized(), v.radii[-1], L[-1]


def _deti(rnd, rodic, Q, uroven, seg, koruna_fn, obal=None):
    """Vedlejsi vetve podel rodice: rozestup, uhel od rodice, spiralove natoceni (137,5 st.), delka podle koruny."""
    out = []
    _, _, _, Lr = _bod(rodic, 1.0)
    s = Lr * Q.get("od", 0.1)
    rot = rnd.uniform(0, 6.28)
    while s < Lr * 0.97:
        t = s / Lr
        p, d, r, _ = _bod(rodic, t)
        rot += math.radians(137.5) + rnd.uniform(-0.4, 0.4)
        a = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))).normalized()
        b = d.cross(a)
        radial = (a * math.cos(rot) + b * math.sin(rot)).normalized()
        uh = math.radians(rnd.uniform(*Q["uhel"]))
        dd = (d * math.cos(uh) + radial * math.sin(uh)).normalized()
        delka = rnd.uniform(*Q["delka"]) * koruna_fn(p, t)
        if delka > 0.15:
            rc = min(r * 0.85, max(0.008, r * Q["r"] * (0.6 + 0.4 * (1 - t))))
            b = _rust(rnd, p - radial * r * 0.4, dd, delka, rc, uroven, Q, seg)
            if obal is not None:
                k = len(b.pts)
                while k > 2 and not obal(b.pts[k - 1]):
                    k -= 1
                b.pts, b.radii = b.pts[:k], b.radii[:k]
                b.radii[-1] = min(b.radii[-1], 0.012)
            if len(b.pts) >= 2:
                out.append(b)
        s += rnd.uniform(*Q["rozestup"])
    return out


def kostra(druh, seed):
    P = DRUHY[druh]
    rnd = random.Random(seed)
    H = P["vyska"]
    K = P["kmen"]
    ks, kz = P["koruna"]
    stred = Vector((0, 0, H * (1 - kz * 0.5)))
    rx, rz = H * ks * 0.5, H * kz * 0.5

    def koruna_fn(p, t):
        # vetve konci uvnitr obalu koruny (elipsoid): delka podle zbyvajici vzdalenosti k obalu
        q = Vector(((p.x) / rx, (p.y) / rx, (p.z - stred.z) / rz))
        return max(0.25, min(1.2, 1.15 - 0.55 * q.length))
    vetve = []
    lean = Vector((rnd.uniform(-1, 1) * K["sklon"], rnd.uniform(-1, 1) * K["sklon"], 1.0)).normalized()
    kmen = _rust(rnd, Vector((0, 0, -0.3)), lean, K["delka"] + 0.3, K["r"], 0, dict(krivost=K["krivost"], svetlo=0.05), 0.15)
    # kmen pod rozvetvenim skoro valec (ubyva jen o tretinu), ne kuzel do spicky
    kmen.radii = [K["r"] * (1 - 0.3 * i / (len(kmen.pts) - 1)) for i in range(len(kmen.pts))]
    if K.get("provod"):
        # lipa: prubezny kmen do vrcholu, tloustne dolu; ramena po cele delce od 'od'
        kmen.radii = [max(0.02, K["r"] * (1 - i / len(kmen.pts)) ** 1.1) for i in range(len(kmen.pts))]
    vetve.append(kmen)
    Qr = P["ramena"]
    if K.get("provod"):
        Qr2 = dict(Qr)
        Qr2["od"] = Qr["od"] / (K["delka"] + 0.3)

        def kf(p, t):
            # vejcita koruna: nejdelsi ramena ve 40 % vysky koruny, nahoru kratsi
            h = (p.z - Qr["od"]) / max(H - Qr["od"], 1)
            return max(0.2, math.sin(math.pi * min(1, max(0, h * 0.9 + 0.12))) ** 0.8)
        ramena = _deti(rnd, kmen, Qr2, 1, 0.3, kf)
    else:
        ramena = []
        top, dtop, rtop, _ = _bod(kmen, 1.0)
        n = rnd.randint(*Qr["n"])
        a0 = rnd.uniform(0, 6.28)
        for i in range(n):
            a = a0 + 2 * math.pi * i / n + rnd.uniform(-0.35, 0.35)
            radial = Vector((math.cos(a), math.sin(a), 0))
            uh = math.radians(rnd.uniform(*Qr["uhel"]))
            dd = (dtop * math.cos(uh) + radial * math.sin(uh)).normalized()
            # ramena odchazeji z ruznych vysek posledniho metru kmene (ne z jednoho bodu)
            t = 1.0 - rnd.uniform(0.0, 0.25)
            p, _, r, _ = _bod(kmen, t)
            ramena.append(_rust(rnd, p - radial * r * 0.3, dd, rnd.uniform(*Qr["delka"]), r * Qr["r"] * rnd.uniform(0.85, 1.1), 1, Qr, 0.3))
        # kmen konci v rozvetveni (ramena ho prebiraji)
        kmen.radii[-1] = kmen.radii[-2] * 0.8
    vetve += ramena
    v2 = []
    for rm in ramena:
        v2 += _deti(rnd, rm, P["vetve"], 2, 0.25, koruna_fn, lambda q: _uvnitr(q, stred, (rx, rz), 1.0))
    vetve += v2
    v3 = []
    for v in v2 + ramena:
        v3 += _deti(rnd, v, P["vetvicky"], 3, 0.2, koruna_fn, lambda q: _uvnitr(q, stred, (rx, rz), 0.97))
    vetve += v3
    return vetve, stred, (rx, rz)


# ------------------------------------------------------------------ sit stromu

class _Sit:
    def __init__(self):
        self.v, self.f, self.uv, self.mat, self.n = [], [], [], [], []

    def quad(self, pts, uv, mat, nrm=None):
        i = len(self.v)
        self.v += pts
        self.f.append(tuple(range(i, i + len(pts))))
        self.uv.append(uv)
        self.mat.append(mat)
        self.n += nrm if nrm else [None] * len(pts)


def _trubka(S, v, kura_m, lod):
    """Vetev jako trubka: strany podle polomeru; kmen s korenovym nabehem a laloky u paty."""
    pts, radii = v.pts, v.radii
    if lod == 1:
        if v.uroven >= 3:
            return
        pts, radii = pts[::2] + ([pts[-1]] if len(pts) % 2 == 0 else []), radii[::2] + ([radii[-1]] if len(radii) % 2 == 0 else [])
    r0 = radii[0]
    sides = 12 if r0 > 0.25 else (9 if r0 > 0.1 else (6 if r0 > 0.04 else (4 if v.uroven < 3 else 3)))
    if lod == 1:
        sides = max(3, sides // 2)
    circ = max(1, round(2 * math.pi * r0 / kura_m))
    rings = []
    acc = [0.0]
    for k in range(1, len(pts)):
        acc.append(acc[-1] + (pts[k] - pts[k - 1]).length)
    prev_a = None
    for k, (p, r) in enumerate(zip(pts, radii)):
        d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        if prev_a is None:
            a = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))).normalized()
        else:
            a = (prev_a - d * prev_a.dot(d)).normalized()       # paralelni prenos (UV se nekrouti)
        prev_a = a
        b = d.cross(a)
        ring = []
        for s in range(sides + 1):
            th = 2 * math.pi * s / sides
            rr = r
            if v.uroven <= 1:
                # nepravidelny prurez (boule, zkrouceni) - kmen a ramena nejsou valce z trubky
                rr = r * (1 + 0.07 * math.sin(3 * th + p.z * 1.7 + v.uroven) + 0.05 * math.sin(5 * th - p.z * 2.9))
            if v.uroven == 0 and p.z < 0.6:
                # korenovy nabeh jen tesne u zeme (do ~20 cm), laloky koreny - ne kuzel
                f = math.exp(-max(p.z, -0.3) / 0.13)
                rr = rr * (1 + 0.22 * f * (1 + 0.6 * math.sin(5 * th + 0.7)))
            ring.append((p + (a * math.cos(th) + b * math.sin(th)) * rr, (a * math.cos(th) + b * math.sin(th))))
        rings.append(ring)
    for k in range(len(pts) - 1):
        for s in range(sides):
            q = [rings[k][s], rings[k][s + 1], rings[k + 1][s + 1], rings[k + 1][s]]
            us = [circ * s / sides, circ * (s + 1) / sides, circ * (s + 1) / sides, circ * s / sides]
            vs = [acc[k] / kura_m, acc[k] / kura_m, acc[k + 1] / kura_m, acc[k + 1] / kura_m]
            S.quad([x[0] for x in q], list(zip(us, vs)), 1, [x[1] for x in q])


def _drevo_skin(vetve, P, lod, rnd):
    """Kmen a ramena jako jeden organicky kus (ne trubky): kostra (body vetvi) -> modifikator Skin (plynule srusty
    do Y v rozvetveni) -> deleni -> sum (boule, zkrouceni, kořenove naběhy) -> decimace na rozpocet. Kořeny: 5 kratkych
    vetvi z paty sikmo do zeme. UV kury z nejblizsi osy kostry (u dokola, v po delce v metrech). Vraci (body, plochy,
    uv rohu, normaly bodu) a seznam vetvi, ktere pokryva (ty se uz nestavi trubkou)."""
    from mathutils import kdtree
    rmin = 0.035 if P["vyska"] > 8 else 0.025
    vybr = [v for v in vetve if v.uroven <= 1 or (v.uroven == 2 and v.radii[0] >= rmin)]
    kmen = vetve[0]
    # kořeny z paty
    koreny = []
    r0 = kmen.radii[0]
    a0 = rnd.uniform(0, 6.28)
    for i in range(5):
        a = a0 + 2 * math.pi * i / 5 + rnd.uniform(-0.3, 0.3)
        o = Vector((math.cos(a), math.sin(a), 0))
        # kořen: z kmene tesne nad zemi, hned sikmo do zeme - nad terenem jen nabeh (lalok), ne noha
        p0 = Vector((kmen.pts[0].x, kmen.pts[0].y, 0.0)) + Vector((0, 0, r0 * 0.9))
        L = r0 * rnd.uniform(2.0, 2.8)
        pts = [p0 + o * (L * t) + Vector((0, 0, -L * 1.1 * t ** 1.2)) for t in (0.0, 0.33, 0.66, 1.0)]
        koreny.append(Vetev(pts, [r0 * 0.5 * (1 - 0.7 * t) for t in (0.0, 0.33, 0.66, 1.0)], 1))
    retez = vybr + koreny
    V, E, R = [], [], []
    kd_par = None
    for ci, v in enumerate(retez):
        i0 = len(V)
        for k, (p, r) in enumerate(zip(v.pts, v.radii)):
            V.append(p.copy())
            R.append(max(r, 0.012))
            if k:
                E.append((len(V) - 2, len(V) - 1))
        if ci > 0:
            # napojit zacatek na nejblizsi bod predchozich (rodic)
            best, bi = 1e9, 0
            q = v.pts[0]
            for j in range(i0):
                d = (V[j] - q).length
                if d < best:
                    best, bi = d, j
            E.append((bi, i0))
            V[i0] = V[bi].lerp(V[i0 + 1] if len(v.pts) > 1 else V[i0], 0.35) if best < 0.5 else V[i0]
    me = bpy.data.meshes.new("drevo_kostra")
    me.from_pydata([tuple(p) for p in V], E, [])
    ob = bpy.data.objects.new("drevo_kostra", me)
    bpy.context.scene.collection.objects.link(ob)
    sk = ob.modifiers.new("skin", "SKIN")
    sk.branch_smoothing = 0.6
    sk.use_smooth_shade = True
    sd = me.skin_vertices[0].data
    for i, r in enumerate(R):
        sd[i].radius = (r, r)
    sd[0].use_root = True
    sub = ob.modifiers.new("sub", "SUBSURF")
    sub.levels = 1 if lod == 0 else 0
    sub.render_levels = sub.levels
    # sum: boule a brazdy - silne u kmene, slabe u tenkych vetvi (skupina vah podle polomeru)
    vg = ob.vertex_groups.new(name="vaha")
    for i, r in enumerate(R):
        vg.add([i], min(1.0, r / 0.3), "REPLACE")
    tex = bpy.data.textures.new("boule", "CLOUDS")
    tex.noise_scale = 0.35 * P["vyska"] / 10
    tex.noise_depth = 2
    ds = ob.modifiers.new("disp", "DISPLACE")
    ds.texture = tex
    ds.strength = 0.06 * kmen.radii[0] / 0.25
    ds.mid_level = 0.5
    ds.texture_coords = "LOCAL"
    ds.vertex_group = "vaha"
    tex2 = bpy.data.textures.new("brazdy", "STUCCI")
    tex2.noise_scale = 0.06
    tex2.turbulence = 3
    ds2 = ob.modifiers.new("disp2", "DISPLACE")
    ds2.texture = tex2
    ds2.strength = 0.025 * kmen.radii[0] / 0.25
    ds2.texture_coords = "LOCAL"
    ds2.vertex_group = "vaha"
    dec = ob.modifiers.new("dec", "DECIMATE")
    cil = (P["cil_troj"] * 0.38) if lod == 0 else (P["cil_troj"] * 0.08)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m0 = ev.to_mesh()
    tri0 = sum(len(p.vertices) - 2 for p in m0.polygons)
    ev.to_mesh_clear()
    dec.ratio = min(1.0, cil / max(tri0, 1))
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    m.calc_loop_triangles()
    pts = [Vector(v.co) for v in m.vertices]
    nrm = [Vector(v.normal) for v in m.vertices]
    faces = [tuple(p.vertices) for p in m.polygons]
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    # UV z kostry: vzorky os po 3 cm s ramcem (paralelni prenos), nejblizsi vzorek -> (uhel, delka)
    kd_n = []
    for ci, v in enumerate(retez):
        acc = 0.0
        prev_a = None
        for k in range(len(v.pts) - 1):
            p, q = v.pts[k], v.pts[k + 1]
            d = (q - p)
            sl = d.length
            d = d / max(sl, 1e-6)
            a = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))).normalized() if prev_a is None else (prev_a - d * prev_a.dot(d)).normalized()
            prev_a = a
            n = max(1, int(sl / 0.03))
            for j in range(n):
                t = j / n
                kd_n.append((p.lerp(q, t), d, a, acc + sl * t, max(1, round(2 * math.pi * v.radii[0] / P["kura_m"]))))
            acc += sl
    kd = kdtree.KDTree(len(kd_n))
    for i, x in enumerate(kd_n):
        kd.insert(x[0], i)
    kd.balance()
    vuv = []
    for p in pts:
        _, i, _ = kd.find(p)
        c, d, a, sL, rep = kd_n[i]
        w = p - c
        w = w - d * w.dot(d)
        b = d.cross(a)
        ang = math.atan2(w.dot(b), w.dot(a)) / (2 * math.pi) % 1.0
        vuv.append((ang * rep, (sL + (p - c).dot(d)) / P["kura_m"], rep))
    fuv = []
    for f in faces:
        us = [vuv[i] for i in f]
        rep = max(u[2] for u in us)
        base = us[0][0]
        row = []
        for u, vv, rp in us:
            # sev u dokola: roh na druhe strane svu posunout o celou obratku
            while u - base > rp / 2:
                u -= rp
            while base - u > rp / 2:
                u += rp
            row.append((u, vv))
        fuv.append(row)
    return pts, faces, fuv, nrm, set(id(v) for v in vybr)


def _uvnitr(p, stred, kor, k=1.0):
    rx, rz = kor
    return Vector((p.x / rx, p.y / rx, (p.z - stred.z) / rz)).length <= k


def _karty(S, rnd, vetve, P, stred, kor, lod):
    """Karty z atlasu v chomacich na koncich vetvi (ne rovnomerne - mezi chomaci prosvita nebe a ramena):
    vetvicka lezi skoro vodorovne podel vetve a ven od kmene, licem k nebi (listy se stavi ke svetlu), konec
    mirne previsa; ctvrtina karet stoji bokem ven (objem koruny z boku). Nic za obalem koruny."""
    rozestup = P["karet_m"] * (2.4 if lod == 1 else 1.0)
    vel = P["karta_m"] * (1.45 if lod == 1 else 1.0)
    n = 0
    up = Vector((0, 0, 1))
    for v in vetve:
        if v.uroven < 2:
            continue
        _, _, _, L = _bod(v, 1.0)
        # listi jen na koncove casti vetve (chomac), na vetvickach (3) hustsi nez na vetvich (2)
        s = L * (0.25 if v.uroven == 3 else 0.45)
        while s <= L:
            p, d, r, _ = _bod(v, s / L)
            s += rozestup * rnd.uniform(0.7, 1.3) * (1.0 if v.uroven == 3 else 1.6)
            if not _uvnitr(p, stred, kor, 1.02):
                continue
            out = Vector((p.x - stred.x, p.y - stred.y, 0.0))
            out = out.normalized() if out.length > 1e-3 else Vector((1, 0, 0))
            h = Vector((d.x, d.y, 0.0))
            h = h.normalized() if h.length > 1e-3 else out
            cd = (h * 0.55 + out * 0.45 + Vector((rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), 0.0))).normalized()
            cd = (cd + Vector((0, 0, -rnd.uniform(0.05, 0.4)))).normalized()
            if rnd.random() < 0.25:
                nrm = (out + Vector((0, 0, 0.5))).normalized()          # bokem ven
            else:
                nrm = (up + Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), 0.0))).normalized()
            nrm = (nrm - cd * nrm.dot(cd)).normalized()
            side = cd.cross(nrm).normalized()
            sz = vel * rnd.uniform(0.8, 1.2)
            cell = rnd.randrange(4)
            u0, v0 = (cell % 2) * 0.5, (cell // 2) * 0.5
            bend = rnd.uniform(0.15, 0.35)
            b0 = p - cd * (sz * 0.08)
            b1 = b0 + cd * (sz * 0.5)
            b2 = b1 + (cd - nrm * bend).normalized() * (sz * 0.5)
            w = sz * 0.5
            rows = [(b0, 0.0), (b1, 0.25), (b2, 0.5)]
            for (pa, va), (pb, vb) in zip(rows, rows[1:]):
                S.quad([pa - side * w, pa + side * w, pb + side * w, pb - side * w],
                       [(u0, v0 + va), (u0 + 0.5, v0 + va), (u0 + 0.5, v0 + vb), (u0, v0 + vb)], 0, None)
            n += 1
    return n


def _mat_hra(name, cimg, nimg, alpha):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = cimg
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Color"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(t.outputs["Color"], mix.inputs[6])
    nt.links.new(vc.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    if alpha:
        nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.blend_method = "CLIP"
        m.alpha_threshold = 0.5
        m.use_backface_culling = False
    nn = nt.nodes.new("ShaderNodeTexImage")
    nn.image = nimg
    nimg.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.88
    return m


def postav(druh, seed=1, lod=0, vetve=None):
    P = DRUHY[druh]
    rnd = random.Random(seed * 31 + lod)
    if vetve is None:
        vetve, stred, kor = kostra(druh, seed)
    else:
        vetve, stred, kor = vetve
    S = _Sit()
    kryte = set()
    if SKIN:
        # organicky kmen (Skin) - Misa 27. 10.: „ma bricho“, zustava vypnuty (predchozi trubky lepsi)
        dp, df, duv, dn, kryte = _drevo_skin(vetve, P, lod, random.Random(seed))
        for f, uv in zip(df, duv):
            S.quad([dp[i] for i in f], uv, 1, [dn[i] for i in f])
    for v in vetve:
        if id(v) not in kryte:
            _trubka(S, v, P["kura_m"], lod)
    nb = len(S.f)
    nk = _karty(S, rnd, vetve, P, stred, kor, lod)
    name = druh if lod == 0 else druh + "_daleko"
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in S.v], [], S.f)
    me.update()
    me.uv_layers.new(name="UVMap")
    me.color_attributes.new("Color", "BYTE_COLOR", "CORNER")
    # odkazy az po zalozeni obou vrstev (nova vrstva realokuje data rohu -> stary odkaz pise do uvolnene pameti)
    uvl = me.uv_layers["UVMap"]
    ca = me.color_attributes["Color"]
    rx, rz = kor
    # material a hladkost az po smycce (zapis atributu ploch behem iterace realokuje pole -> pad Blenderu)
    for poly, uv, mt in zip(me.polygons, S.uv, S.mat):
        for k in range(poly.loop_total):
            li = poly.loop_start + k
            uvl.data[li].uv = uv[k]
            co = Vector(S.v[poly.vertices[k]])
            if mt == 0:
                q = Vector((co.x / rx, co.y / rx, (co.z - stred.z) / rz))
                ao = max(0.3, min(1.0, 0.25 + 0.8 * q.length))
                ca.data[li].color = (1.0, 1.0, 1.0, ao)
            else:
                ca.data[li].color = (1.0, 1.0, 1.0, 1.0)
    me.polygons.foreach_set("material_index", S.mat)
    me.shade_smooth()
    # normaly: listi od stredu koruny (koruna se stinuje jako koule), kura hladce z trubek (z dat, ne z bpy)
    nrm = []
    for fi, (fc, mt) in enumerate(zip(S.f, S.mat)):
        p0, p1, p2 = (Vector(S.v[fc[0]]), Vector(S.v[fc[1]]), Vector(S.v[fc[2]]))
        fn = (p1 - p0).cross(p2 - p0)
        fn = fn.normalized() if fn.length > 1e-9 else Vector((0, 0, 1))
        for vi in fc:
            co = Vector(S.v[vi])
            if mt == 0:
                q = Vector((co.x / rx, co.y / rx, (co.z - stred.z) / rz))
                nn = (q.normalized() * 0.75 + fn * 0.25 * (1 if fn.z >= 0 else -1) + Vector((0, 0, 0.2))).normalized()
            else:
                nn = Vector(S.n[vi]) if S.n[vi] is not None else fn
            nrm.append((nn.x, nn.y, nn.z))
    me.normals_split_custom_set(nrm)
    cimg = _img(os.path.join(OUT_TEX, "%s_listi_c.png" % druh))
    nimg = _img(os.path.join(OUT_TEX, "%s_listi_n.png" % druh), True)
    kimg = _img(os.path.join(TEX, "kury", "%s_diff_1k.jpg" % P["kura"]))
    knimg = _img(os.path.join(TEX, "kury", "%s_nor_gl_1k.jpg" % P["kura"]), True)
    me.materials.append(_mat_hra("%s_listi" % druh, cimg, nimg, True))
    me.materials.append(_mat_hra("kura_%s" % druh, kimg, knimg, False))
    tri = sum(len(p.vertices) - 2 for p in me.polygons)
    print("strom", name, "troj", tri, "vetvi", len(vetve), "karet", nk, "kura troj", sum(len(S.f[i]) - 2 for i in range(nb)))
    return me, (vetve, stred, kor)


def export(me, fp):
    sc = bpy.context.scene
    for o in list(sc.objects):
        bpy.data.objects.remove(o)
    # prosvit listi jako ve hre (backlight z pravidla tridy strom): translucent pridany k BSDF
    for m in bpy.data.materials:
        if m.name.endswith("_listi") and m.node_tree and "nahled_tr" not in m.node_tree.nodes:
            nt = m.node_tree
            bsdf = nt.nodes["Principled BSDF"]
            out = nt.nodes["Material Output"]
            tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
            tr.name = "nahled_tr"
            nt.links.new(bsdf.inputs["Base Color"].links[0].from_socket, tr.inputs["Color"])
            mx = nt.nodes.new("ShaderNodeMixShader")
            mx.inputs["Fac"].default_value = 0.35
            nt.links.new(bsdf.outputs[0], mx.inputs[1])
            nt.links.new(tr.outputs[0], mx.inputs[2])
            tp = nt.nodes.new("ShaderNodeBsdfTransparent")
            mx2 = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(bsdf.inputs["Alpha"].links[0].from_socket, mx2.inputs["Fac"])
            nt.links.new(tp.outputs[0], mx2.inputs[1])
            nt.links.new(mx.outputs[0], mx2.inputs[2])
            nt.links.new(mx2.outputs[0], out.inputs["Surface"])
    ob = bpy.data.objects.new(me.name, me)
    sc.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=fp, use_selection=True, export_format="GLB", export_yup=True,
                              export_image_format="AUTO", export_attributes=True)
    sc.collection.objects.unlink(ob)


def nahled(objs, fp):
    """Snimek k posouzeni: stromy vedle sebe na trave, slunce zboku, obloha (site zustavaji, jen nova scena)."""
    sc = bpy.context.scene
    for o in list(sc.objects):
        bpy.data.objects.remove(o)
    # prosvit listi jako ve hre (backlight z pravidla tridy strom): translucent pridany k BSDF
    for m in bpy.data.materials:
        if m.name.endswith("_listi") and m.node_tree and "nahled_tr" not in m.node_tree.nodes:
            nt = m.node_tree
            bsdf = nt.nodes["Principled BSDF"]
            out = nt.nodes["Material Output"]
            tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
            tr.name = "nahled_tr"
            nt.links.new(bsdf.inputs["Base Color"].links[0].from_socket, tr.inputs["Color"])
            mx = nt.nodes.new("ShaderNodeMixShader")
            mx.inputs["Fac"].default_value = 0.35
            nt.links.new(bsdf.outputs[0], mx.inputs[1])
            nt.links.new(tr.outputs[0], mx.inputs[2])
            tp = nt.nodes.new("ShaderNodeBsdfTransparent")
            mx2 = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(bsdf.inputs["Alpha"].links[0].from_socket, mx2.inputs["Fac"])
            nt.links.new(tp.outputs[0], mx2.inputs[1])
            nt.links.new(mx.outputs[0], mx2.inputs[2])
            nt.links.new(mx2.outputs[0], out.inputs["Surface"])
    x = 0.0
    for me in objs:
        ob = bpy.data.objects.new(me.name + "_n", me)
        sc.collection.objects.link(ob)
        w = max(v.co.x for v in me.vertices) - min(v.co.x for v in me.vertices)
        ob.location = (x + w / 2, 0, 0)
        x += w + 1.5
    gm = bpy.data.meshes.new("g")
    gm.from_pydata([(-50, -60, 0), (x + 50, -60, 0), (x + 50, 60, 0), (-50, 60, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("g", gm)
    sc.collection.objects.link(g)
    mg = bpy.data.materials.new("gm")
    mg.use_nodes = True
    mg.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.13, 0.2, 0.06, 1)
    gm.materials.append(mg)
    cam = bpy.data.cameras.new("C")
    co = bpy.data.objects.new("C", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    hmax = max(max(v.co.z for v in me.vertices) for me in objs)
    co.location = (x / 2, -max(x, hmax * 1.6) * 0.95, hmax * 0.45)
    co.rotation_euler = (math.radians(88), 0, 0)
    cam.lens = 30
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.7, 0.95, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.4
    sc.world = w
    sun = bpy.data.lights.new("S", "SUN")
    sun.energy = 3.5
    so = bpy.data.objects.new("S", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(35))
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.render.film_transparent = False
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 900
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.view_settings.view_transform = "Filmic" if "Filmic" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "AgX"
    sc.render.filepath = fp
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    nfp = None
    if "--nahled" in args:
        nfp = args[args.index("--nahled") + 1]
        args = args[:args.index("--nahled")]
    druhy = args or list(DRUHY)
    hotove = []
    os.makedirs(OUT_GLB, exist_ok=True)
    for d in druhy:
        bake_atlas(d)
        me0, kos = postav(d, 1, 0)
        me1, _ = postav(d, 1, 1, kos)
        export(me0, os.path.join(OUT_GLB, d + ".glb"))
        export(me1, os.path.join(OUT_GLB, d + "_daleko.glb"))
        hotove += [me0, me1]
    if nfp:
        nahled(hotove, nfp)
