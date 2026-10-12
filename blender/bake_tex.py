"""Vlastni dlazdicove textury vyrenderovane z geometrie (postup jako Substance Designer):
z modelu z jednotlivych kusu se vyrenderuje barva (albedo), normala a vyska.

  python bake_tex.py sindel   -> tex_cache/sindel_{diff,nor,rough,disp}_1k.jpg + zaznam v meta_1k.json/meta_2k.json

Sindel: stare stipane dubove/smrkove sindele, zesedle sluncem a destem, ruzne odstiny, nektere
zkroucene, pootocene nebo odstipnute, misty mech u spodnich hran. Dlazdice 1 x 1 m, 7 rad na metr.
"""
import json
import math
import os
import random
import sys

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene  # noqa: E402
from lib import TEX_ROOT  # noqa: E402

SIZE = 1.5          # dlazdice v metrech
ROWS = 7            # rad na metr (viditelna delka sindele ~14 cm)


def _wood_image():
    path = os.path.join(TEX_ROOT, "prkna_ven_diff_2k.jpg")
    return bpy.data.images.load(path, check_existing=True)


def shingle_patch(seed=7):
    """Sindele jako tenke kvadry, kazdy s vlastnim odstinem (atribut 'ton', 'sed', 'mech')."""
    rnd = random.Random(seed)
    verts, faces, ton, sed, mech, uvo = [], [], [], [], [], []
    row = SIZE / ROWS
    length = row * 3.2

    def box(m, sx, sy, sz, t, g, ms, off):
        i = len(verts)
        for dz in (-sz / 2, sz / 2):
            for dy in (-sy / 2, sy / 2):
                for dx in (-sx / 2, sx / 2):
                    verts.append(m @ Vector((dx, dy, dz)))
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            faces.append(tuple(i + k for k in f))
            ton.append(t)
            sed.append(g)
            mech.append(ms)
            uvo.append(off)

    for r in range(ROWS):
        y_butt = r * row + rnd.uniform(-0.004, 0.004)
        x = rnd.uniform(0, 0.1)
        while x < SIZE:
            w = rnd.uniform(0.07, 0.15)
            gap = rnd.uniform(0.002, 0.009)
            cx = x + w / 2
            # spodni (viditelny) konec v y_butt, sindel vede nahoru po spadu pres dalsi rady
            t = rnd.random()
            g = rnd.uniform(0.55, 0.85)                                          # vse jednotne zesedle
            ms = 0.4 + 0.6 * rnd.random() if rnd.random() < 0.25 else 0.0
            off = (rnd.random(), rnd.random())
            tilt = -math.atan2(0.03, length) + rnd.uniform(-0.012, 0.008)      # spodni konec nahore, hlava pod vyssi radou
            twist = rnd.uniform(-0.035, 0.035)
            yaw = rnd.uniform(-0.03, 0.03)
            thick = rnd.uniform(0.008, 0.014)
            ln = length * rnd.uniform(0.92, 1.05)
            # po sobe jdouci rady: nizsi rada lezi nahore (vyssi z)
            base_z = 0.0
            for dxw in (-SIZE, 0.0, SIZE):
                for dyw in (-SIZE, 0.0, SIZE):
                    c = Vector((cx + dxw, y_butt + ln / 2 + dyw, base_z + thick / 2 + 0.012))
                    m = (Matrix.Translation(c) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(tilt, 4, "X")
                         @ Matrix.Rotation(twist, 4, "Y"))
                    # odstipnuty roh: obcas uzsi
                    box(m, w - gap, ln, thick, t, g, ms, off)
            x += w
    me = bpy.data.meshes.new("sindele")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for name, arr in (("ton", ton), ("sed", sed), ("mech", mech)):
        a = me.attributes.new(name, "FLOAT", "FACE")
        a.data.foreach_set("value", arr)
    a = me.attributes.new("uvo", "FLOAT2", "FACE")
    a.data.foreach_set("vector", [v for o in uvo for v in o])
    ob = bpy.data.objects.new("Sindele", me)
    bpy.context.scene.collection.objects.link(ob)
    # podklad (latovani) pod sindeli
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0.5, 0.5, -0.05))
    return ob


def _emission_mat(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs[0])
    nt.links.new(build(nt), em.inputs["Color"])
    return m


def albedo(nt):
    """Drevo: fotka prken posunuta pro kazdy sindel, sednuti podle 'sed', mech u spodni hrany."""
    att = lambda n, t="FLOAT": nt.nodes.new("ShaderNodeAttribute")  # noqa: E731
    a_sed = nt.nodes.new("ShaderNodeAttribute"); a_sed.attribute_name = "sed"
    a_ton = nt.nodes.new("ShaderNodeAttribute"); a_ton.attribute_name = "ton"
    a_mech = nt.nodes.new("ShaderNodeAttribute"); a_mech.attribute_name = "mech"
    a_uvo = nt.nodes.new("ShaderNodeAttribute"); a_uvo.attribute_name = "uvo"
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # souradnice dreva: podel sindele (y) vlakna, posun podle sindele
    mp = nt.nodes.new("ShaderNodeVectorMath"); mp.operation = "MULTIPLY_ADD"
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    mp.inputs[1].default_value = (0.35, 1.4, 1.0)
    nt.links.new(a_uvo.outputs["Vector"], mp.inputs[2])
    rot = nt.nodes.new("ShaderNodeVectorRotate"); rot.rotation_type = "Z_AXIS"; rot.inputs["Angle"].default_value = 0.0
    nt.links.new(mp.outputs[0], rot.inputs["Vector"])
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = _wood_image()
    nt.links.new(rot.outputs[0], tex.inputs["Vector"])
    # tonovani: teplejsi/tmavsi podle 'ton'
    tone = nt.nodes.new("ShaderNodeMix"); tone.data_type = "RGBA"; tone.blend_type = "MULTIPLY"
    nt.links.new(a_ton.outputs["Fac"], tone.inputs["Factor"])
    nt.links.new(tex.outputs["Color"], tone.inputs[6])
    tone.inputs[7].default_value = (0.62, 0.48, 0.34, 1)
    # zesednuti: smer k sedostribrne
    grey = nt.nodes.new("ShaderNodeMix"); grey.data_type = "RGBA"; grey.blend_type = "MIX"
    nt.links.new(a_sed.outputs["Fac"], grey.inputs["Factor"])
    nt.links.new(tone.outputs[2], grey.inputs[6])
    grey.inputs[7].default_value = (0.31, 0.305, 0.29, 1)
    # skvrny a vybleднuti sumem
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    blot = nt.nodes.new("ShaderNodeMix"); blot.data_type = "RGBA"; blot.blend_type = "MULTIPLY"
    blot.inputs["Factor"].default_value = 0.15
    nt.links.new(grey.outputs[2], blot.inputs[6])
    nt.links.new(nz.outputs["Color"], blot.inputs[7])
    # leta: vlnite pruhy podel vlaken
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"
    wv.inputs["Distortion"].default_value = 1.2
    wv.inputs["Scale"].default_value = 5.0
    wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 3.0
    nt.links.new(rot.outputs[0], wv.inputs["Vector"])
    grain = nt.nodes.new("ShaderNodeMix"); grain.data_type = "RGBA"; grain.blend_type = "MULTIPLY"
    grain.inputs["Factor"].default_value = 0.45
    nt.links.new(blot.outputs[2], grain.inputs[6])
    nt.links.new(wv.outputs["Color"], grain.inputs[7])
    # mech jen ve skvrnach
    mn = nt.nodes.new("ShaderNodeTexNoise"); mn.inputs["Scale"].default_value = 38.0; mn.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], mn.inputs["Vector"])
    mth = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mn.outputs["Fac"], mth.inputs["Value"])
    mth.inputs["From Min"].default_value = 0.52
    mth.inputs["From Max"].default_value = 0.62
    mmul = nt.nodes.new("ShaderNodeMath"); mmul.operation = "MULTIPLY"
    nt.links.new(mth.outputs["Result"], mmul.inputs[0])
    nt.links.new(a_mech.outputs["Fac"], mmul.inputs[1])
    mo = nt.nodes.new("ShaderNodeMix"); mo.data_type = "RGBA"; mo.blend_type = "MIX"
    nt.links.new(mmul.outputs[0], mo.inputs["Factor"])
    nt.links.new(grain.outputs[2], mo.inputs[6])
    mo.inputs[7].default_value = (0.08, 0.08, 0.07, 1)   # tmave lisejniky
    return mo.outputs[2]


def normal_col(nt):
    g = nt.nodes.new("ShaderNodeNewGeometry")
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = "MULTIPLY_ADD"
    nt.links.new(g.outputs["Normal"], vm.inputs[0])
    vm.inputs[1].default_value = (0.5, 0.5, 0.5)
    vm.inputs[2].default_value = (0.5, 0.5, 0.5)
    return vm.outputs[0]


def height_col(nt):
    g = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(g.outputs["Position"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    mr.inputs["From Min"].default_value = -0.02
    mr.inputs["From Max"].default_value = 0.05
    return mr.outputs["Result"]


def render_patch(kind="sindel", res=1024):
    scene.reset()
    shingle_patch()
    sc = bpy.context.scene
    cam = bpy.data.cameras.new("K"); cam.type = "ORTHO"; cam.ortho_scale = SIZE
    co = bpy.data.objects.new("K", cam); sc.collection.objects.link(co)
    co.location = (SIZE / 2, SIZE / 2, 3.0)
    sc.camera = co
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 16
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92
    sc.world = bpy.data.worlds.new("W")
    obs = [o for o in sc.objects if o.type == "MESH"]
    out = {}
    for key, build, cs in (("diff", albedo, "sRGB"), ("nor", normal_col, "Non-Color"), ("disp", height_col, "Non-Color")):
        m = _emission_mat("bake_" + key, build)
        for o in obs:
            o.data.materials.clear()
            o.data.materials.append(m)
        sc.view_settings.view_transform = "Standard" if cs == "sRGB" else "Raw"
        for res_k in ("1k", "2k"):
            path = os.path.join(TEX_ROOT, "%s_%s_%s.jpg" % (kind, key, res_k))
            sc.render.resolution_x = sc.render.resolution_y = 1024 if res_k == "1k" else 2048
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            out.setdefault(res_k, {})[key] = os.path.basename(path)
    # drsnost: drevo matne, mech jeste vic -> konstantni svetla seda
    for res_k, n in (("1k", 1024), ("2k", 2048)):
        path = os.path.join(TEX_ROOT, "%s_rough_%s.jpg" % (kind, res_k))
        img = bpy.data.images.new("r", 4, 4)
        img.pixels = [0.82, 0.82, 0.82, 1.0] * 16
        img.filepath_raw = path
        img.file_format = "JPEG"
        img.save()
        out[res_k]["rough"] = os.path.basename(path)
    for res_k in ("1k", "2k"):
        mp = os.path.join(TEX_ROOT, "meta_%s.json" % res_k)
        meta = json.load(open(mp))
        meta[kind] = {"id": "vlastni", "size_m": [SIZE, SIZE], "maps": out[res_k]}
        json.dump(meta, open(mp, "w"), indent=1)
    print("hotovo", out)




def post_sindel():
    """Dokresleni: stin pod kazdou radou (z vyskove mapy), hluboka vlakna a praskliny podel spadu."""
    import numpy as np
    from PIL import Image, ImageFilter
    for res_k in ("1k", "2k"):
        dp = os.path.join(TEX_ROOT, "sindel_diff_%s.jpg" % res_k)
        hp = os.path.join(TEX_ROOT, "sindel_disp_%s.jpg" % res_k)
        d = np.asarray(Image.open(dp).convert("RGB")).astype(np.float32) / 255
        h = np.asarray(Image.open(hp).convert("L")).astype(np.float32) / 255
        n = h.shape[0]
        rng = np.random.default_rng(3)
        # vlakna: sum natazeny podel spadu (svisle), dlazdicovy
        f = rng.random((n // 8, n))
        fib = np.asarray(Image.fromarray((f * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC)).astype(np.float32) / 255
        fib = np.roll(fib, 0, axis=0)
        cr = (rng.random((n // 32, n)) > 0.985).astype(np.float32)
        crack = np.asarray(Image.fromarray((cr * 255).astype(np.uint8)).resize((n, n), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
        # stin: spodni hrana rady je nejvyse, hlava pod dalsi radou nejnize -> tmavsi
        ao = np.clip(0.38 + 0.75 * h ** 0.8, 0, 1.05)
        # okraj sindele: hrana ve vysce -> tenka tmava cara (spara)
        gy, gx = np.gradient(h)
        edge = np.clip(np.hypot(gx, gy) * n * 0.08, 0, 1)
        out = d * ao[..., None] * (0.82 + 0.3 * fib[..., None]) * (1 - 0.55 * crack[..., None]) * (1 - 0.6 * edge[..., None])
        Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(dp, quality=92)
    print("post sindel hotovo")


if __name__ == "__main__":
    render_patch(sys.argv[1] if len(sys.argv) > 1 else "sindel")
    post_sindel()
