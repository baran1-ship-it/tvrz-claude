"""Vlasy z MakeHuman system assets (CC0): mhclo napasované na tělo, textura z barevné varianty, tónování."""
import bpy, os
HG = "/home/claude/dl/mhassets/hair_geo"
HV = "/home/claude/dl/mhassets/hair"
def add(HumanService, body, style, name, variant=None, tint=(1, 1, 1), grey=0.0, recolor=None):
    path = f"{HG}/{style}/{style}.mhclo"
    before = set(bpy.data.objects)
    ob = HumanService.add_mhclo_asset(path, body, asset_type="Hair", subdiv_levels=0, material_type="GAMEENGINE")
    ob.name = name; ob.data.name = name
    tex = None
    if variant:
        d = f"{HV}/{style}/{variant}"
        pngs = [f for f in os.listdir(d) if f.endswith(".png")] if os.path.isdir(d) else []
        if pngs: tex = os.path.join(d, pngs[0])
    if recolor:
        # přebarvení podle jasu: zachová kresbu pramenů, barva = recolor (sRGB)
        import numpy as np
        from PIL import Image
        src = tex or f"{HG}/{style}/{style}_diffuse.png"
        im = np.asarray(Image.open(src).convert("RGBA")).astype(float) / 255
        L = im[..., :3].mean(-1); m_ = im[..., 3] > 0.3
        lo, hi = (np.percentile(L[m_], 5), np.percentile(L[m_], 95)) if m_.any() else (0, 1)
        Ln = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)
        col = np.array(recolor)[None, None, :] * (0.65 + 0.6 * Ln[..., None])
        out = np.dstack([np.clip(col, 0, 1), im[..., 3:]])
        tex = f"/home/claude/chars/hair_{name}.png"; Image.fromarray((out * 255).astype(np.uint8)).save(tex)
    for m in ob.data.materials:
        nt = m.node_tree
        bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        img_nodes = [n for n in nt.nodes if n.type == 'TEX_IMAGE']
        diff = next((n for n in img_nodes if "iffuse" in n.name or "iffuse" in (n.label or "")), img_nodes[0] if img_nodes else None)
        if diff is None or bsdf is None: print("HAIR MAT?", [n.name for n in nt.nodes]); continue
        if tex: diff.image = bpy.data.images.load(tex)
        # tónování barvy (násobení) + šediny
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
        nt.links.new(diff.outputs["Color"], mul.inputs[6]); mul.inputs[7].default_value = (*tint, 1)
        out = mul.outputs[2]
        if grey > 0:
            gm = nt.nodes.new("ShaderNodeMix"); gm.data_type = 'RGBA'; gm.inputs[0].default_value = grey
            nt.links.new(out, gm.inputs[6]); gm.inputs[7].default_value = (0.32, 0.31, 0.3, 1); out = gm.outputs[2]
        nt.links.new(out, bsdf.inputs["Base Color"])
        if not bsdf.inputs["Alpha"].links: nt.links.new(diff.outputs["Alpha"], bsdf.inputs["Alpha"])
        bsdf.inputs["Roughness"].default_value = 0.78
        try: m.blend_method = 'CLIP'
        except Exception: pass
        m.use_backface_culling = False
    print("MHHAIR", name, style, variant, len(ob.data.polygons), "tex", tex)
    return ob
