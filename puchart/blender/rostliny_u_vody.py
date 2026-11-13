"""Rostliny u potoků, které chyběly (docs/reference/potoky/README_jak_se_stavi.md krok 8, Míša 13. 11.: „pokud ti chybí
nějaké rostliny, stáhni si je z internetu“): ostřice (Carex), keřová vrba (Salix purpurea/triandra), devětsil
(Petasites hybridus).

Hotový 3D model těchto druhů s volnou licencí ke stažení bez účtu není (13. 11.: Poly Haven, ambientCG, Quaternius,
Kenney, OpenGameArt nemají; Sketchfab CC0 ffishAsia „Carex maximowiczii“, „Petasites japonicus“ a CC-BY „Salix Alba
Pollarded“ vyžadují k stažení účet – API vrací 401). Proto stejně jako Havranovy byliny a stromy (strom2.py):
karty a pruhy z fotoskenů s volnou licencí, stažených do build/stazene_rostliny/ (nastroje: viz níže):
  - ostřice: čepele z ambientCG Foliage001 (CC0, https://ambientcg.com/view?id=Foliage001), 2K PNG;
  - devětsil: list z „Dim's Arboretum“ (BurdockLeaf.png, autor Dim, CC-BY 3.0,
    https://opengameart.org/content/dims-arboretum) – lopuch/devětsil mají stejný srdčitě ledvinitý tvar;
  - keřová vrba: strom2.py (Havran) s parametry keře, listy ambientCG LeafSet013 (CC0) a kůra Poly Haven
    bark_willow (CC0) z build/tex_cache (už v projektu pro jasan).

Formát jako Havranovy byliny v hra/modely/rostliny: jedna síť <model>, materiál game_<model> (keř: listí + kůra),
alfa MASK (ořez 0,5), oboustranné, barva vrcholu COLOR_0 (AO u paty), textury max 1024, metry, Y nahoru (glTF),
pata v počátku. LOD dělá Godot při importu (generate_lods) + rozpouštění do dálky (byliny.json/kere.json zanik_m).

  /opt/bl/bin/python blender/rostliny_u_vody.py [ostrice] [devetsil] [vrba] [--nahled]
Výstup: build/rostliny_u_vody/*.glb (+ nahled_*.png); do hry kopírovat ručně do hra/modely/rostliny/.
"""
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Vector
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ST = os.path.join(ROOT, "build", "stazene_rostliny")
OUT = os.path.join(ROOT, "build", "rostliny_u_vody")
os.makedirs(OUT, exist_ok=True)


def reset():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.cameras,
                 bpy.data.lights, bpy.data.worlds):
        for x in list(coll):
            coll.remove(x)


# ------------------------------------------------------------------ atlasy (numpy/PIL)

def _dilate(rgb, mask, kroku=24):
    """Barva pod průhlednými pixely = barva sousedů (jinak tmavé lemy v mipmapách) – jako strom2._dilate."""
    rgb = rgb.astype(np.float32).copy()
    filled = mask.copy()
    for _ in range(kroku):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(filled.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            acc += np.roll(np.where(filled[..., None], rgb, 0), (dy, dx), (0, 1))
            cnt += np.roll(filled, (dy, dx), (0, 1))
        new = (~filled) & (cnt > 0)
        rgb[new] = acc[new] / cnt[new][:, None]
        filled |= new
    rgb[~filled] = rgb[mask].mean(0) if mask.any() else 128
    return rgb


def atlas_ostrice(res=1024):
    """Čepele z Foliage001 (šikmo položené) – každá otočená svisle (špička nahoru), oříznutá a roztažená do sloupce
    atlasu. Normála (tečný prostor) se otočí spolu s obrazem. Vrací (soubor barvy, soubor normály, počet sloupců)."""
    d = os.path.join(ST, "Foliage001")
    c = np.array(Image.open(os.path.join(d, "Foliage001_2K-PNG_Color.png")).convert("RGB"))
    a = np.array(Image.open(os.path.join(d, "Foliage001_2K-PNG_Opacity.png")).convert("L"))
    n = np.array(Image.open(os.path.join(d, "Foliage001_2K-PNG_NormalGL.png")).convert("RGB"))
    lab, k = ndimage.label(a > 128)
    cepele = []
    for i in range(1, k + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 4000:
            continue
        P = np.stack([xs, ys], 1).astype(np.float64)
        P -= P.mean(0)
        w, v = np.linalg.eigh(np.cov(P.T))
        if w[1] / max(w[0], 1e-6) < 60:      # zatočená čepel (S) – ne
            continue
        ax = v[:, 1]
        ang = math.degrees(math.atan2(ax[1], ax[0]))
        cepele.append((i, ang, xs.min(), ys.min(), xs.max(), ys.max()))
    cepele.sort(key=lambda e: e[2])
    ncol = len(cepele)
    colw = res // ncol
    C = np.zeros((res, res, 3), np.float32)
    A = np.zeros((res, res), np.uint8)
    N = np.zeros((res, res, 3), np.float32)
    for ci, (i, ang, x0, y0, x1, y1) in enumerate(cepele):
        m = 12
        x0, y0, x1, y1 = max(0, x0 - m), max(0, y0 - m), min(a.shape[1], x1 + m), min(a.shape[0], y1 + m)
        msk = (lab[y0:y1, x0:x1] == i)
        cc = Image.fromarray(c[y0:y1, x0:x1])
        aa = Image.fromarray((a[y0:y1, x0:x1] * msk).astype(np.uint8))
        nn = Image.fromarray(n[y0:y1, x0:x1])
        rot = ang - 90.0 if ang > 0 else ang + 90.0       # osa čepele svisle
        cc = cc.rotate(rot, Image.BICUBIC, expand=True)
        aa = aa.rotate(rot, Image.BICUBIC, expand=True)
        nn = nn.rotate(rot, Image.BICUBIC, expand=True, fillcolor=(128, 128, 255))
        an = np.array(aa)
        ys, xs = np.nonzero(an > 60)
        bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        # špička nahoru: užší konec je nahoře
        h = by1 - by0
        sir_h = (an[by0:by0 + h // 10] > 60).sum(1).mean()
        sir_d = (an[by1 - h // 10:by1] > 60).sum(1).mean()
        flip = sir_h > sir_d
        crop = (bx0, by0, bx1, by1)
        cc, aa, nn = cc.crop(crop), aa.crop(crop), nn.crop(crop)
        if flip:
            cc, aa, nn = (im.transpose(Image.ROTATE_180) for im in (cc, aa, nn))
        cw = colw - 4
        cc = np.array(cc.resize((cw, res), Image.LANCZOS)).astype(np.float32)
        aa = np.array(aa.resize((cw, res), Image.LANCZOS))
        nn = np.array(nn.resize((cw, res), Image.LANCZOS)).astype(np.float32)
        # otočení vektoru normály v rovině (obraz otočen o rot, případně o 180)
        t = math.radians(rot + (180 if flip else 0))
        nx, ny = nn[..., 0] / 127.5 - 1, nn[..., 1] / 127.5 - 1
        nx2 = nx * math.cos(t) - ny * math.sin(t)
        ny2 = nx * math.sin(t) + ny * math.cos(t)
        nn[..., 0], nn[..., 1] = (nx2 + 1) * 127.5, (ny2 + 1) * 127.5
        xo = ci * colw + 2
        C[:, xo:xo + cw] = cc
        A[:, xo:xo + cw] = aa
        N[:, xo:xo + cw] = nn
    msk = A > 128
    C = _dilate(C, msk)
    N = _dilate(N, msk)
    fc, fn = os.path.join(OUT, "ostrice_c.png"), os.path.join(OUT, "ostrice_n.png")
    Image.fromarray(np.dstack([C, A]).clip(0, 255).astype(np.uint8), "RGBA").save(fc)
    Image.fromarray(N.clip(0, 255).astype(np.uint8)).save(fn)
    print("atlas ostrice: cepeli", ncol, "sloupec px", colw)
    return fc, fn, ncol


def _normala_z_jasu(rgb, sila=2.0):
    L = rgb.astype(np.float32).mean(2) / 255.0
    L = ndimage.gaussian_filter(L, 1.0)
    gx = ndimage.sobel(L, 1)
    gy = ndimage.sobel(L, 0)
    nx, ny, nz = -gx * sila, gy * sila, np.ones_like(L)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.dstack([(nx / ln + 1) * 127.5, (ny / ln + 1) * 127.5, (nz / ln + 1) * 127.5])


def atlas_devetsil(res=512):
    """Atlas 512: nahoře list (BurdockLeaf z Dim's Arboretum, oříznutý, bílé skvrny vyretušované z okolí, stopka
    vlevo), dole pruh řapíku (barva z listu do světle zelené, u paty do červenohněda – řapíky devětsilu)."""
    src = Image.open(os.path.join(ST, "dims", "img", "BurdockLeaf.png")).convert("RGBA")
    s = np.array(src).astype(np.float32)
    a = s[..., 3]
    if a.min() > 250:           # bez alfy: pozadí bílé
        a = np.where(s[..., :3].mean(2) < 235, 255, 0).astype(np.float32)
    msk = a > 128
    msk = ndimage.binary_opening(msk, iterations=1)
    lab, k = ndimage.label(msk)
    big = np.argmax(ndimage.sum(msk, lab, range(1, k + 1))) + 1
    msk = ndimage.binary_fill_holes(lab == big)
    rgb = s[..., :3]
    # bílé skvrny (odlesky/papír) uvnitř listu -> medián okolí
    jas = rgb.mean(2)
    skvrny = msk & (jas > 150)
    skvrny = ndimage.binary_dilation(skvrny, iterations=2) & msk
    ok = msk & ~skvrny
    rgb = _dilate(np.where(ok[..., None], rgb, 0), ok, 12)
    ys, xs = np.nonzero(msk)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    W, H = res, int(res * 0.75)
    leaf = Image.fromarray(rgb[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)).resize((W - 8, H - 8), Image.LANCZOS)
    lm = Image.fromarray((msk[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((W - 8, H - 8), Image.LANCZOS)
    lm = lm.filter(ImageFilter.GaussianBlur(0.8))
    C = np.zeros((res, res, 3), np.float32)
    A = np.zeros((res, res), np.uint8)
    C[4:H - 4, 4:W - 4] = np.array(leaf)
    A[4:H - 4, 4:W - 4] = np.array(lm)
    # řapík: svislé pruhy (vodivá pletiva), nahoře zelený, dole do červenohnědé
    mean = np.array(leaf).reshape(-1, 3)[np.array(lm).reshape(-1) > 128].mean(0)
    rnd = np.random.default_rng(5)
    hh = res - H - 8
    for yy in range(hh):
        t = yy / max(hh - 1, 1)               # 0 nahoře (u čepele) .. 1 dole (u země)
        base = mean * 1.25 * (1 - t) + np.array([120, 72, 52]) * t ** 2 + mean * 1.1 * (t - t ** 2)
        C[H + 4 + yy, 8:res - 8] = base
    pruhy = 0.85 + 0.15 * np.sin(np.linspace(0, 40 * math.pi, res - 16))[None, :] + rnd.normal(0, 0.03, (hh, res - 16))
    C[H + 4:H + 4 + hh, 8:res - 8] *= pruhy[..., None]
    A[H + 4:H + 4 + hh, 8:res - 8] = 255
    msk = A > 128
    N = _normala_z_jasu(C, 1.6)
    C = _dilate(C, msk)
    N = _dilate(N, msk)
    fc, fn = os.path.join(OUT, "devetsil_c.png"), os.path.join(OUT, "devetsil_n.png")
    Image.fromarray(np.dstack([C, A]).clip(0, 255).astype(np.uint8), "RGBA").save(fc)
    Image.fromarray(N.clip(0, 255).astype(np.uint8)).save(fn)
    # kde je na obrázku listu úpon řapíku (záliv): nejlevější bod listu ve středním řádku – UV
    stred = np.array(lm)[(H - 8) // 2] > 128
    sx = np.nonzero(stred)[0]
    zaliv_u = (4 + (sx.min() if len(sx) else 0)) / res
    return fc, fn, dict(list_v=(4 / res, (H - 4) / res), list_u=(4 / res, (W - 4) / res),
                        rapik_v=((H + 4) / res, (res - 4) / res), zaliv_u=zaliv_u)


# ------------------------------------------------------------------ síť a materiál

class Sit:
    def __init__(self):
        self.v, self.f, self.uv, self.col, self.nrm = [], [], [], [], []

    def quad(self, pts, uvs, cols, nrms):
        i = len(self.v)
        self.v += [tuple(p) for p in pts]
        self.f.append(tuple(range(i, i + len(pts))))
        self.uv.append(uvs)
        self.col.append(cols)
        self.nrm += [tuple(n) for n in nrms]

    def mesh(self, name):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.update()
        me.uv_layers.new(name="UVMap")
        me.color_attributes.new("Color", "BYTE_COLOR", "CORNER")
        uvl = me.uv_layers["UVMap"]
        ca = me.color_attributes["Color"]
        nrm = []
        for poly, uv, col in zip(me.polygons, self.uv, self.col):
            for k in range(poly.loop_total):
                li = poly.loop_start + k
                uvl.data[li].uv = uv[k]
                g = col[k]
                ca.data[li].color = (g, g, g, 1.0)
                nrm.append(self.nrm[poly.vertices[k]])
        me.shade_smooth()
        me.normals_split_custom_set(nrm)
        return me


def material(name, fc, fn, rough=0.65):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(fc)
    vc = nt.nodes.new("ShaderNodeVertexColor")      # barva vrcholu (AO) -> COLOR_0 (jako strom2._mat_hra)
    vc.layer_name = "Color"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(t.outputs["Color"], mix.inputs[6])
    nt.links.new(vc.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    rd = nt.nodes.new("ShaderNodeMath")          # glTF exportér 4.2: Round -> alphaMode MASK (ořez 0,5)
    rd.operation = "ROUND"
    nt.links.new(t.outputs["Alpha"], rd.inputs[0])
    nt.links.new(rd.outputs[0], bsdf.inputs["Alpha"])
    m.blend_method = "CLIP"
    m.use_backface_culling = False
    ni = nt.nodes.new("ShaderNodeTexImage")
    ni.image = bpy.data.images.load(fn)
    ni.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(ni.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = rough
    return m


def export(objs, fp):
    sc = bpy.context.scene
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        if o.name not in sc.collection.objects:
            sc.collection.objects.link(o)
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=fp, use_selection=True, export_format="GLB", export_yup=True,
                              export_image_format="AUTO", export_attributes=True)
    for o in objs:
        sc.collection.objects.unlink(o)
    oprav_glb(fp)


def oprav_glb(fp):
    """Zajistit formát Havranových bylin: listí MASK 0,5 a oboustranné (exportér dá u kůry OPAQUE)."""
    try:
        from pygltflib import GLTF2
    except ImportError:
        return
    g = GLTF2().load(fp)
    for m in g.materials:
        if "kura" in m.name:
            m.alphaMode, m.alphaCutoff, m.doubleSided = "OPAQUE", None, False
        else:
            m.alphaMode, m.alphaCutoff, m.doubleSided = "MASK", 0.5, True
    g.save(fp)


def troj(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


# ------------------------------------------------------------------ ostřice

# Carex acuta / C. brizoides u potoků: trs 0,5–1 m, listy ploché 5–10 mm, obloukovitě převislé (Květena ČR 8;
# README_jak_se_stavi.md 2.3: „hustá tráva a ostřice 0,5–1 m“, převislé přes hranu vody).
OSTRICE = {
    "ostrice_1": dict(n=62, delka=(0.55, 0.9), sirka=(0.014, 0.022), polomer=0.08, seed=11),
    "ostrice_2": dict(n=48, delka=(0.45, 0.7), sirka=(0.012, 0.02), polomer=0.06, seed=12),
    "ostrice_3": dict(n=76, delka=(0.65, 1.05), sirka=(0.015, 0.024), polomer=0.1, seed=13),
}


def ostrice(name, P, atlas):
    fc, fn, ncol = atlas
    rnd = random.Random(P["seed"])
    S = Sit()
    seg = 5
    for i in range(P["n"]):
        az = rnd.uniform(0, 2 * math.pi)
        r0 = P["polomer"] * math.sqrt(rnd.random())
        base = Vector((math.cos(az) * r0, math.sin(az) * r0, -0.02))
        hor = Vector((math.cos(az + rnd.uniform(-0.4, 0.4)), math.sin(az + rnd.uniform(-0.4, 0.4)), 0)).normalized()
        L = rnd.uniform(*P["delka"])
        vnejsi = r0 / max(P["polomer"], 1e-3)
        elev = math.radians(rnd.uniform(60, 88) - 25 * vnejsi)     # vnější listy níž a víc převislé
        gravit = rnd.uniform(1.0, 2.0) * (0.5 + 0.8 * vnejsi)
        w = rnd.uniform(*P["sirka"])
        twist0, twist1 = rnd.uniform(-0.5, 0.5), rnd.uniform(-1.2, 1.2)
        col = rnd.randrange(ncol)
        u0, u1 = col / ncol + 2 / 1024, (col + 1) / ncol - 2 / 1024
        if rnd.random() < 0.5:
            u0, u1 = u1, u0
        pts, sides = [], []
        d = Vector((hor.x * math.cos(elev), hor.y * math.cos(elev), math.sin(elev)))
        p = base.copy()
        for k in range(seg + 1):
            t = k / seg
            pts.append(p.copy())
            tan = d.copy()
            side0 = hor.cross(Vector((0, 0, 1))).normalized()
            tw = twist0 + twist1 * t
            side = side0 * math.cos(tw) + tan.cross(side0) * math.sin(tw)
            side = (side - tan * side.dot(tan)).normalized()
            sides.append(side)
            # další úsek: směr se stáčí k zemi (gravitace) – oblouk, konec převislý
            d = (d + Vector((0, 0, -1)) * gravit * (1.0 / seg) * (0.5 + 1.5 * t)).normalized()
            p = p + d * (L / seg)
        for k in range(seg):
            a, b = pts[k], pts[k + 1]
            sa, sb = sides[k], sides[k + 1]
            wa, wb = w * (1 - 0.15 * k / seg), w * (1 - 0.15 * (k + 1) / seg)
            va, vb = k / seg, (k + 1) / seg
            ga, gb = 0.45 + 0.55 * va ** 0.7, 0.45 + 0.55 * vb ** 0.7     # AO u paty trsu (barva vrcholu)
            q = [a - sa * wa, a + sa * wa, b + sb * wb, b - sb * wb]
            # normály trsu: nahoru a ven (trs se stíní jako kupka, ne čepel po čepeli – jako Havran trava)
            nr = []
            for pp in q:
                o = Vector((pp.x, pp.y, 0))
                o = o.normalized() if o.length > 1e-4 else Vector((0, 0, 0))
                nr.append((Vector((0, 0, 1)) * 0.75 + o * 0.45).normalized())
            S.quad(q, [(u0, va), (u1, va), (u1, vb), (u0, vb)], [ga, ga, gb, gb], nr)
    me = S.mesh(name)
    me.materials.append(material("game_" + name, fc, fn, 0.7))
    return me


# ------------------------------------------------------------------ devětsil

# Petasites hybridus: listy okrouhle srdčité až 60 cm, řapíky 0,5–1,2 m, porost 1,0–1,5 m (Katalog biotopů ČR M5,
# README_jak_se_stavi.md 2.3). Rozměry trsu z Květeny ČR 7 (listy přízemní, dlouze řapíkaté) – tvar trsu NEOVERENO
# fotkou z Veličky.
DEVETSIL = {
    "devetsil_1": dict(n=7, list=(0.32, 0.5), rapik=(0.45, 0.85), seed=21),
    "devetsil_2": dict(n=5, list=(0.28, 0.42), rapik=(0.35, 0.65), seed=22),
    "devetsil_3": dict(n=9, list=(0.36, 0.58), rapik=(0.55, 1.0), seed=23),
}


def devetsil(name, P, atlas):
    fc, fn, uv = atlas
    rnd = random.Random(P["seed"])
    S = Sit()
    lu0, lu1 = uv["list_u"]
    # atlas má řádky shora (obrázek), UV Blenderu v zdola: v = 1 - řádek
    lv0, lv1 = 1 - uv["list_v"][1], 1 - uv["list_v"][0]
    rv0, rv1 = 1 - uv["rapik_v"][0], 1 - uv["rapik_v"][1]      # rv0 u čepele (zelený), rv1 u paty (hnědočervený)
    up = Vector((0, 0, 1))
    for i in range(P["n"]):
        az = 2 * math.pi * i / P["n"] + rnd.uniform(-0.3, 0.3)
        hor = Vector((math.cos(az), math.sin(az), 0))
        R = rnd.uniform(*P["rapik"])
        sz = rnd.uniform(*P["list"])
        base = hor * rnd.uniform(0.0, 0.06) + Vector((0, 0, -0.03))
        naklon = math.radians(rnd.uniform(8, 30))
        top = base + hor * (R * math.sin(naklon)) + up * (R * math.cos(naklon))
        # řapík: dvě zkřížené karty (šířka 1,6 cm), dole hnědočervený
        for rot in (0.0, math.pi / 2):
            sd = Vector((math.cos(az + rot + math.pi / 2), math.sin(az + rot + math.pi / 2), 0)) * 0.008
            q = [base - sd, base + sd, top + sd, top - sd]
            nr = [(hor * 0.4 + up * 0.8).normalized()] * 4
            S.quad(q, [(0.05, rv1), (0.95, rv1), (0.95, rv0), (0.05, rv0)], [0.55, 0.55, 0.9, 0.9], nr)
        # čepel: mřížka 3×3, záliv u úponu řapíku, list skloněný ven 15–35° a mírně miskovitý (okraje dolů)
        sklon = math.radians(rnd.uniform(12, 35))
        fwd = (hor * math.cos(sklon) - up * math.sin(sklon)).normalized()     # od úponu ke špičce
        side = up.cross(hor).normalized()
        sz_y = sz * 0.68                       # poměr list. obrázku (šířka/délka)
        zal = uv["zaliv_u"]
        G = 3
        grid = {}
        for gx in range(G + 1):
            for gy in range(G + 1):
                u = gx / G
                v = gy / G
                # u: 0 = levý okraj obrázku (záliv/úpon) .. 1 = špička; v: napříč
                along = (u - (zal - lu0) / (lu1 - lu0)) * sz
                across = (v - 0.5) * sz_y * 2 * 0.5 * 2
                cup = -0.12 * sz * (2 * (v - 0.5)) ** 2 - 0.05 * sz * max(0.0, u - 0.6)
                p = top + fwd * along + side * across + up * cup
                grid[gx, gy] = (p, (lu0 + u * (lu1 - lu0), lv1 - v * (lv1 - lv0)))
        tone = rnd.uniform(0.85, 1.0)
        for gx in range(G):
            for gy in range(G):
                ks = [(gx, gy), (gx + 1, gy), (gx + 1, gy + 1), (gx, gy + 1)]
                q = [grid[k][0] for k in ks]
                uvs = [grid[k][1] for k in ks]
                nr = []
                for pp in q:
                    o = Vector((pp.x, pp.y, 0))
                    o = o.normalized() if o.length > 1e-4 else Vector((0, 0, 0))
                    nr.append((up * 0.85 + o * 0.35).normalized())
                cc = [tone * (0.8 + 0.2 * min(1, k[0] / G + 0.3)) for k in ks]
                S.quad(q, uvs, cc, nr)
    me = S.mesh(name)
    me.materials.append(material("game_" + name, fc, fn, 0.6))
    return me


# ------------------------------------------------------------------ keřová vrba (strom2 Havrana)

# K2.1/K2.2 Katalogu biotopů ČR (Chytrý et al. 2010): vrbové křoviny 2–5(–10) m, vrba trojmužná, košíkářská,
# nachová. Keř = mnoho prutů z jedné paty, vzpřímeně do vějíře, úzké kopinaté listy 5–10 cm (LeafSet013),
# kůra bark_willow. Parametry ve formátu strom2.DRUHY.
VRBY = {
    "vrba_ker_1": dict(   # ~3,5 m (S. triandra / viminalis)
        vyska=3.6, listy="LeafSet013", tint=(0.5, 0.66, 0.44), kura="bark_willow", kura_m=0.5,
        karta_m=0.75, list_m=0.09, listu=40, plod=None, plodu=(0, 0), plod_karet=0,
        kmen=dict(delka=0.12, r=0.09, krivost=0.1, sklon=0.05),
        ramena=dict(n=(8, 10), od=0.05, uhel=(6, 34), delka=(2.6, 3.7), r=0.4, krivost=0.22, gravitace=0.03, svetlo=0.06),
        vetve=dict(rozestup=(0.3, 0.5), uhel=(15, 35), delka=(0.5, 1.0), r=0.55, krivost=0.25, gravitace=0.05, svetlo=0.06, od=0.12),
        vetvicky=dict(rozestup=(0.9, 1.3), uhel=(20, 40), delka=(0.25, 0.45), r=0.5, krivost=0.2, gravitace=0.05, svetlo=0.05, od=0.4),
        karet_m=0.11, koruna=(0.95, 0.95), listi_od=0.35, cil_troj=9000),
    "vrba_ker_2": dict(   # ~2,5 m (S. purpurea na štěrku, K2.2) – nižší, prutovitější, modrozelená
        vyska=2.6, listy="LeafSet013", tint=(0.47, 0.62, 0.48), kura="bark_willow", kura_m=0.5,
        karta_m=0.65, list_m=0.08, listu=40, plod=None, plodu=(0, 0), plod_karet=0,
        kmen=dict(delka=0.1, r=0.07, krivost=0.1, sklon=0.05),
        ramena=dict(n=(9, 11), od=0.05, uhel=(8, 40), delka=(1.9, 2.7), r=0.4, krivost=0.2, gravitace=0.05, svetlo=0.05),
        vetve=dict(rozestup=(0.3, 0.5), uhel=(15, 35), delka=(0.4, 0.75), r=0.55, krivost=0.22, gravitace=0.06, svetlo=0.05, od=0.12),
        vetvicky=dict(rozestup=(0.9, 1.3), uhel=(20, 40), delka=(0.2, 0.35), r=0.5, krivost=0.2, gravitace=0.05, svetlo=0.05, od=0.45),
        karet_m=0.11, koruna=(1.05, 0.95), listi_od=0.35, cil_troj=8000),
}


def vrby(nfp_list):
    sys.path.insert(0, os.path.join(HERE, "havran"))
    import strom2
    strom2.OUT_TEX = os.path.join(OUT, "tex_vrba")
    os.makedirs(strom2.OUT_TEX, exist_ok=True)
    orig = strom2._trubka

    def trubka(S, v, kura_m, lod):
        # keř (tablet, cíl 4–6 tis. troj.): tenké větve a pruty s polovinou prstenců (konec zůstává)
        if v.uroven >= 2 and len(v.pts) > 3:
            idx = list(range(0, len(v.pts), 2))
            if idx[-1] != len(v.pts) - 1:
                idx.append(len(v.pts) - 1)
            v = strom2.Vetev([v.pts[i] for i in idx], [v.radii[i] for i in idx], v.uroven)
        orig(S, v, kura_m, lod)
    strom2._trubka = trubka
    hotove = []
    for k, P in VRBY.items():          # atlasy napřed (bake_atlas maže scénu i sítě)
        strom2.DRUHY[k] = P
        strom2.bake_atlas(k, res=1024)
    for k, P in VRBY.items():
        me, _ = strom2.postav(k, 3, 0)
        # názvy materiálů jako Havranovy keře (game_<model>_listi / _kura)
        for m in me.materials:
            m.name = "game_%s_%s" % (k, "listi" if m.name.endswith("_listi") else "kura")
        fp = os.path.join(OUT, k + ".glb")
        ob = bpy.data.objects.new(k, me)
        export([ob], fp)
        print("MODEL", k, "troj", troj(me))
        hotove.append(me)
    return hotove


# ------------------------------------------------------------------ náhled

def nahled(mes, fp):
    sc = bpy.context.scene
    for o in list(sc.objects):
        bpy.data.objects.remove(o)
    x = 0.0
    for me in mes:
        ob = bpy.data.objects.new(me.name + "_n", me)
        sc.collection.objects.link(ob)
        w = max(v.co.x for v in me.vertices) - min(v.co.x for v in me.vertices)
        ob.location = (x + w / 2, 0, 0)
        x += w + 0.4
    gm = bpy.data.meshes.new("g")
    gm.from_pydata([(-20, -20, 0), (x + 20, -20, 0), (x + 20, 20, 0), (-20, 20, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("g", gm)
    sc.collection.objects.link(g)
    mg = bpy.data.materials.new("gm")
    mg.use_nodes = True
    mg.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.17, 0.1, 1)
    gm.materials.append(mg)
    cam = bpy.data.cameras.new("C")
    co = bpy.data.objects.new("C", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    hmax = max(max(v.co.z for v in me.vertices) for me in mes)
    co.location = (x / 2, -max(x, hmax * 1.6) * 1.0, hmax * 0.6)
    co.rotation_euler = (math.radians(84), 0, 0)
    cam.lens = 32
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.7, 0.95, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
    sc.world = w
    sun = bpy.data.lights.new("S", "SUN")
    sun.energy = 3.5
    so = bpy.data.objects.new("S", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(35))
    sc.render.engine = "CYCLES"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False
    sc.cycles.samples = 24
    sc.render.resolution_x = 1400
    sc.render.resolution_y = 700
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = fp
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    co = [a for a in args if not a.startswith("--")] or ["ostrice", "devetsil", "vrba"]
    nahl = "--nahled" in args
    if "ostrice" in co:
        reset()
        at = atlas_ostrice()
        mes = []
        for k, P in OSTRICE.items():
            me = ostrice(k, P, at)
            export([bpy.data.objects.new(k, me)], os.path.join(OUT, k + ".glb"))
            print("MODEL", k, "troj", troj(me))
            mes.append(me)
        if nahl:
            nahled(mes, os.path.join(OUT, "nahled_ostrice.png"))
    if "devetsil" in co:
        reset()
        at = atlas_devetsil()
        mes = []
        for k, P in DEVETSIL.items():
            me = devetsil(k, P, at)
            export([bpy.data.objects.new(k, me)], os.path.join(OUT, k + ".glb"))
            print("MODEL", k, "troj", troj(me))
            mes.append(me)
        if nahl:
            nahled(mes, os.path.join(OUT, "nahled_devetsil.png"))
    if "vrba" in co:
        reset()
        mes = vrby(None)
        if nahl:
            nahled(mes, os.path.join(OUT, "nahled_vrba.png"))
