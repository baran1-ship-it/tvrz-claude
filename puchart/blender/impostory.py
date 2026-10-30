"""PŘEVZATO Z HAVRANA (blender/impostory.py), upraveno pro Puchart: modely hra/modely/stromy/<druh>_stredni.glb, výstup hra/textury/impostory.
Impostory stromu (K3): kazdy druh vyfotit z 8x8 smeru horni polokoule (hemi-oktaedricke mapovani)
do atlasu 1024 px - barva s alfou (*_a.png) a normala ve svete hry (*_n.png). Ve hre jeden ctverec (2 troj.)
na strom, shader vybere pohled podle smeru ke kamere (shaders/impostor.gdshader).

Pouziti:  /opt/bl/bin/python blender/impostory.py       (cte modely/rostliny/<druh>.glb z exportu)
Vystup:   obrazky/impostory/<druh>_a.png, <druh>_n.png, obrazky/impostory/impostory.json (stred, polomer)"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hra", "textury", "impostory")
N = 8                 # pohledu na stranu
PX = 128              # pixelu na pohled (8 x 128 = 1024)
# druh impostoru: (soubor glb, uzel) - varianty stejneho druhu sdileji jeden impostor
DRUHY = {d: (d + ("_stredni"), None) for d in ("buk", "jedle", "smrk", "dub", "lipa", "olse", "vrba", "briza", "borovice")}


def smer(i, j):
    """Stred pohledu (i, j) -> jednotkovy smer ve hre (y nahoru), hemi-oktaedricke dekodovani."""
    u = (i + 0.5) / N * 2.0 - 1.0
    v = (j + 0.5) / N * 2.0 - 1.0
    px, pz = (u + v) * 0.5, (u - v) * 0.5
    y = 1.0 - abs(px) - abs(pz)
    return Vector((px, max(y, 0.0), pz)).normalized()


def _emise(mat, normal):
    """Material -> jen emise (barva z textury nebo normala ve svete hry), alfa zachovana."""
    nt = mat.node_tree
    out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    bsdf = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"]
    em = nt.nodes.new("ShaderNodeEmission")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    if normal:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        # Blender (z nahoru) -> hra (y nahoru): (x, z, -y), pak 0..1
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        com = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(geo.outputs["Normal"], sep.inputs[0])
        neg = nt.nodes.new("ShaderNodeMath")
        neg.operation = "MULTIPLY"
        neg.inputs[1].default_value = -1.0
        nt.links.new(sep.outputs["Y"], neg.inputs[0])
        nt.links.new(sep.outputs["X"], com.inputs["X"])
        nt.links.new(sep.outputs["Z"], com.inputs["Y"])
        nt.links.new(neg.outputs[0], com.inputs["Z"])
        ma = nt.nodes.new("ShaderNodeVectorMath")
        ma.operation = "MULTIPLY_ADD"
        ma.inputs[1].default_value = (0.5, 0.5, 0.5)
        ma.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(com.outputs[0], ma.inputs[0])
        nt.links.new(ma.outputs[0], em.inputs["Color"])
    elif bsdf and bsdf[0].inputs["Base Color"].links:
        nt.links.new(bsdf[0].inputs["Base Color"].links[0].from_socket, em.inputs["Color"])
    elif bsdf:
        em.inputs["Color"].default_value = bsdf[0].inputs["Base Color"].default_value
    if bsdf and bsdf[0].inputs["Alpha"].links:
        nt.links.new(bsdf[0].inputs["Alpha"].links[0].from_socket, mix.inputs["Fac"])
    else:
        mix.inputs["Fac"].default_value = 1.0 if not bsdf else bsdf[0].inputs["Alpha"].default_value
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    for l in list(out.inputs["Surface"].links):
        nt.links.remove(l)
    nt.links.new(mix.outputs[0], out.inputs["Surface"])


def druh(name, soubor, uzel, meta):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "hra", "modely", "stromy", soubor + ".glb"))
    ob = bpy.data.objects.get(uzel) if uzel else next((o for o in bpy.data.objects if o.type == "MESH"), None)
    if ob is None:
        print("PRESKOCENO", name, "uzel", uzel)
        return
    for o in list(bpy.data.objects):
        if o is not ob and o.type == "MESH":
            bpy.data.objects.remove(o)
    ws = [ob.matrix_world @ v.co for v in ob.data.vertices]
    mn = Vector((min(w.x for w in ws), min(w.y for w in ws), min(w.z for w in ws)))
    mx = Vector((max(w.x for w in ws), max(w.y for w in ws), max(w.z for w in ws)))
    cen = (mn + mx) / 2
    rad = max((w - cen).length for w in ws)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 8
    sc.cycles.use_denoising = False
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = PX
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    w = bpy.data.worlds.new("w")
    sc.world = w
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = rad * 2.0
    cam.data.clip_start = 0.01
    cam.data.clip_end = rad * 4.0
    tmp = os.path.join(OUT, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    from PIL import Image
    puvodni = [m.copy() if m else None for m in ob.data.materials]
    for pruchod, normal in (("a", False), ("n", True)):
        for i, m in enumerate(ob.data.materials):
            if m is None:
                continue
            m2 = puvodni[i].copy()
            _emise(m2, normal)
            ob.data.materials[i] = m2
        sc.view_settings.view_transform = "Raw" if normal else "Standard"
        atlas = Image.new("RGBA", (N * PX, N * PX), (0, 0, 0, 0))
        for j in range(N):
            for i in range(N):
                d = smer(i, j)
                db = Vector((d.x, -d.z, d.y))                       # hra -> Blender
                cam.location = cen + db * rad * 2.0
                # pohled k stredu, nahoru = svisla osa (stejne jako billboard ve hre)
                cam.rotation_euler = (-db).to_track_quat("-Z", "Y").to_euler()
                sc.render.filepath = os.path.join(tmp, "v.png")
                bpy.ops.render.render(write_still=True)
                atlas.paste(Image.open(sc.render.filepath).convert("RGBA"), (i * PX, j * PX))
        if not normal:
            # okraje listi: barva pod pruhlednymi pixely z okoli (mipmapy netahnou cerny lem)
            bg = atlas.copy()
            for _ in range(4):
                from PIL import ImageFilter
                bg = Image.alpha_composite(bg.filter(ImageFilter.MaxFilter(3)), atlas)
            atlas = Image.merge("RGBA", (*bg.convert("RGB").split(), atlas.split()[3]))
        atlas.save(os.path.join(OUT, "%s_%s.png" % (name, pruchod)))
    # stred a polomer v metrech hry (y nahoru), vztazeno k pate modelu (vyska v knihovne = mx.z - mn.z)
    meta[name] = {"stred": [cen.x, cen.z - mn.z, -cen.y], "polomer": rad, "vyska": mx.z - mn.z}
    print("impostor", name, round(rad, 2), "m")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    only = [a for a in sys.argv[1:] if a in DRUHY]
    for name, (soubor, uzel) in DRUHY.items():
        if only and name not in only:
            continue
        druh(name, soubor, uzel, meta)
    mp = os.path.join(OUT, "impostory.json")
    old = json.load(open(mp)) if os.path.exists(mp) else {}
    old.update(meta)
    json.dump(old, open(mp, "w"), indent=1)
