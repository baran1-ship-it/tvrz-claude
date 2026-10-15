"""Procedurální materiál skály (droba / pískovec) – pro náhledy a pro zapékání."""
import bpy

# ------------------------------------------------------------ helpers
def N(nt, t, loc=(0, 0), **kw):
    n = nt.nodes.new(t); n.location = loc
    for k, v in kw.items():
        if k in n.inputs.keys() and not hasattr(n, k):
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n

def L(nt, a, b):
    nt.links.new(a, b)

def ramp(nt, inp, stops, loc=(0, 0), interp='LINEAR'):
    r = nt.nodes.new("ShaderNodeValToRGB"); r.location = loc
    r.color_ramp.interpolation = interp
    el = r.color_ramp.elements
    while len(el) < len(stops):
        el.new(0.5)
    for e, (p, c) in zip(el, stops):
        e.position = p
        e.color = c if len(c) == 4 else (*c, 1.0)
    L(nt, inp, r.inputs[0])
    return r

def mix(nt, fac, a, b, blend='MIX', loc=(0, 0)):
    m = nt.nodes.new("ShaderNodeMix"); m.location = loc
    m.data_type = 'RGBA'; m.blend_type = blend
    for s, v in ((m.inputs[0], fac), (m.inputs[6], a), (m.inputs[7], b)):
        if isinstance(v, bpy.types.NodeSocket): L(nt, v, s)
        else: s.default_value = v if not isinstance(v, tuple) or len(v) != 3 else (*v, 1)
    return m.outputs[2]

def math_(nt, op, a, b=0.0, clamp=False, loc=(0, 0)):
    m = nt.nodes.new("ShaderNodeMath"); m.location = loc
    m.operation = op; m.use_clamp = clamp
    for s, v in ((m.inputs[0], a), (m.inputs[1], b)):
        if isinstance(v, bpy.types.NodeSocket): L(nt, v, s)
        else: s.default_value = v
    return m.outputs[0]

def noise_tex(nt, vec, scale, detail=6, rough=0.55, dim='3D', loc=(0, 0)):
    n = nt.nodes.new("ShaderNodeTexNoise"); n.location = loc
    n.noise_dimensions = dim
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    L(nt, vec, n.inputs["Vector"])
    return n

def smooth(nt, x, e0, e1):
    m = nt.nodes.new("ShaderNodeMapRange")
    m.interpolation_type = 'SMOOTHSTEP'
    m.inputs["From Min"].default_value = e0
    m.inputs["From Max"].default_value = e1
    L(nt, x, m.inputs["Value"])
    return m.outputs["Result"]


PALS = {
  "droba": dict(
    base=[(0.25, (0.105, 0.105, 0.098)), (0.45, (0.165, 0.160, 0.145)),
          (0.62, (0.215, 0.205, 0.180)), (0.80, (0.250, 0.232, 0.198))],
    fe=(0.30, 0.17, 0.08), fe_amt=0.7, edge=(0.36, 0.345, 0.31), streak=0.0, crust=0.0),
  "piskovec": dict(   # křemenný pískovec Českého ráje: okr, béž, rezavé pruhy, šedočerná kůra
    base=[(0.25, (0.215, 0.165, 0.105)), (0.45, (0.300, 0.235, 0.150)),
          (0.62, (0.370, 0.300, 0.200)), (0.80, (0.420, 0.355, 0.255))],
    fe=(0.27, 0.115, 0.045), fe_amt=0.85, edge=(0.47, 0.41, 0.31), streak=0.8, crust=0.7),
  "zula": dict(       # šedá až narůžovělá žula: živec, křemen, slída
    base=[(0.25, (0.13, 0.125, 0.12)), (0.45, (0.19, 0.18, 0.17)),
          (0.62, (0.23, 0.22, 0.20)), (0.80, (0.27, 0.255, 0.24))],
    fe=(0.30, 0.20, 0.13), fe_amt=0.45, edge=(0.36, 0.34, 0.32), streak=0.45, crust=0.6, speckle=0.55),
}

def apply(rock):
    RT = rock.get("rtype", "droba")
    PAL = PALS[RT]
    # ------------------------------------------------------------ materiál skály
    mat = bpy.data.materials.new("rock_droba")
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial", (1400, 0))
    bsdf = N(nt, "ShaderNodeBsdfPrincipled", (1100, 0))
    L(nt, bsdf.outputs[0], out.inputs[0])

    tc = N(nt, "ShaderNodeTexCoord", (-1600, 0))
    _ps = N(nt, "ShaderNodeVectorMath", (-1450, 0)); _ps.operation = 'SCALE'
    L(nt, tc.outputs["Object"], _ps.inputs[0])
    _ps.inputs["Scale"].default_value = float(rock.get("mat_scale", 1.0))
    P = _ps.outputs[0]
    geo = N(nt, "ShaderNodeNewGeometry", (-1600, -300))
    strata = N(nt, "ShaderNodeAttribute", (-1600, 300)); strata.attribute_name = "strata"
    crack = N(nt, "ShaderNodeAttribute", (-1600, 450)); crack.attribute_name = "crack"
    sep = N(nt, "ShaderNodeSeparateXYZ", (-1400, -300)); L(nt, geo.outputs["Normal"], sep.inputs[0])
    sepP = N(nt, "ShaderNodeSeparateXYZ", (-1400, -500)); L(nt, P, sepP.inputs[0])
    up = sep.outputs["Z"]
    height = sepP.outputs["Z"]

    # --- základní barva droby: šedá s olivovým/hnědým nádechem, pruhy po vrstvách
    n_big = noise_tex(nt, P, 1.4, 8, 0.6)
    n_mid = noise_tex(nt, P, 7.0, 10, 0.6)
    strata_n = math_(nt, 'ADD', strata.outputs["Fac"], math_(nt, 'MULTIPLY', n_big.outputs[0], 0.15))
    # per-vrstva odstín: sinus přes strata
    sv = math_(nt, 'SINE', math_(nt, 'MULTIPLY', strata.outputs["Fac"], 23.0))
    sv2 = math_(nt, 'SINE', math_(nt, 'MULTIPLY', strata.outputs["Fac"], 61.0))
    layer_tone = math_(nt, 'ADD', math_(nt, 'MULTIPLY', sv, 0.5), math_(nt, 'MULTIPLY', sv2, 0.25))
    layer_tone = math_(nt, 'ADD', math_(nt, 'MULTIPLY', layer_tone, 0.35), math_(nt, 'MULTIPLY', n_mid.outputs[0], 0.65))
    base = ramp(nt, layer_tone, PAL["base"], (-800, 300))
    col = base.outputs[0]

    # zrnitost (pískovcová/drobová zrna)
    grain = noise_tex(nt, P, 180.0, 2, 0.5)
    gr = ramp(nt, grain.outputs[0], [(0.35, (0.82, 0.82, 0.82)), (0.65, (1.12, 1.10, 1.06))], (-800, 0))
    col = mix(nt, 1.0, col, gr.outputs[0], 'MULTIPLY')
    if PAL.get("speckle"):
        # krystaly žuly: mozaika živce (narůžovělý/bílý), křemene (šedý) a slídy (černá)
        cv = N(nt, "ShaderNodeTexVoronoi", (-1100, 120))
        cv.inputs["Scale"].default_value = 140.0
        L(nt, P, cv.inputs["Vector"])
        cs = N(nt, "ShaderNodeSeparateColor", (-900, 120)); L(nt, cv.outputs["Color"], cs.inputs[0])
        crys = ramp(nt, cs.outputs[0], [
            (0.00, (0.03, 0.03, 0.03)),     # biotit
            (0.14, (0.03, 0.03, 0.03)),
            (0.15, (0.24, 0.24, 0.25)),     # křemen
            (0.45, (0.27, 0.27, 0.28)),
            (0.46, (0.36, 0.30, 0.27)),     # růžový živec
            (0.75, (0.34, 0.29, 0.26)),
            (0.76, (0.40, 0.39, 0.37)),     # bílý živec
        ], (-700, 120), 'CONSTANT')
        col = mix(nt, 0.7 * PAL["speckle"], col, crys.outputs[0], 'MIX')

    # železité (rezavé) zabarvení podél některých vrstev
    fe_n = noise_tex(nt, P, 2.2, 6, 0.65)
    fe = math_(nt, 'MULTIPLY', smooth(nt, fe_n.outputs[0], 0.55, 0.72), smooth(nt, sv, 0.3, 0.9))
    col = mix(nt, math_(nt, 'MULTIPLY', fe, PAL["fe_amt"]), col, PAL["fe"], 'MIX')

    # šedočerná zvětralá kůra na vystavených plochách + černé stékance od vody
    crust_n = noise_tex(nt, P, 1.1, 6, 0.6)
    crust = math_(nt, 'MULTIPLY', smooth(nt, crust_n.outputs[0], 0.36, 0.56), PAL["crust"])
    col = mix(nt, crust, col, (0.105, 0.098, 0.085), 'MIX')
    stretch = N(nt, "ShaderNodeMapping", (-1300, 700))
    stretch.inputs["Scale"].default_value = (7.0, 7.0, 0.35)
    L(nt, P, stretch.inputs["Vector"])
    st_n = noise_tex(nt, stretch.outputs[0], 2.5, 5, 0.6)
    st_side = smooth(nt, up, 0.55, 0.15)
    st = math_(nt, 'MULTIPLY', smooth(nt, st_n.outputs[0], 0.46, 0.6), st_side)
    st = math_(nt, 'MULTIPLY', st, smooth(nt, height, 0.1, 0.9))
    col = mix(nt, math_(nt, 'MULTIPLY', st, PAL["streak"]), col, (0.05, 0.047, 0.042), 'MIX')

    # světlejší ošoupané/zvětralé hrany (pointiness)
    edge = smooth(nt, geo.outputs["Pointiness"], 0.505, 0.56)
    col = mix(nt, math_(nt, 'MULTIPLY', edge, 0.55), col, PAL["edge"], 'MIX')

    # špína a hlína v dutinách (AO)
    ao = N(nt, "ShaderNodeAmbientOcclusion", (-1100, -700))
    ao.samples = 16; ao.only_local = True
    ao.inputs["Distance"].default_value = 0.12 / float(rock.get("mat_scale", 1.0))
    cav = smooth(nt, ao.outputs["AO"], 0.85, 0.35)
    col = mix(nt, math_(nt, 'MULTIPLY', cav, 0.75), col, (0.075, 0.058, 0.040), 'MIX')

    # voštiny: uvnitř buněk světlejší čerstvý pískovec, stěnky tmavé
    hon = N(nt, "ShaderNodeAttribute", (-1600, 600)); hon.attribute_name = "honey"
    hon_f = math_(nt, 'MULTIPLY', smooth(nt, hon.outputs["Fac"], 0.1, 0.5), cav)
    col = mix(nt, math_(nt, 'MULTIPLY', hon_f, 0.6), col, (0.40, 0.31, 0.19), 'MIX')

    # praskliny tmavé
    crk = smooth(nt, crack.outputs["Fac"], 0.25, 0.85)
    col = mix(nt, math_(nt, 'MULTIPLY', crk, 0.85), col, (0.035, 0.030, 0.024), 'MIX')

    # vlhký, zablácený spodek (od země nahoru, nepravidelně)
    wet_n = noise_tex(nt, P, 3.5, 6, 0.6)
    wet_h = math_(nt, 'ADD', height, math_(nt, 'MULTIPLY', wet_n.outputs[0], 0.22))
    wet = smooth(nt, wet_h, 0.42, 0.12)
    splash = noise_tex(nt, P, 25.0, 4, 0.6)
    splash_m = math_(nt, 'MULTIPLY', smooth(nt, splash.outputs[0], 0.5, 0.62), smooth(nt, height, 0.35, 0.05))
    col = mix(nt, math_(nt, 'MULTIPLY', wet, 0.65), col, (0.065, 0.055, 0.043), 'MIX')
    col = mix(nt, math_(nt, 'MULTIPLY', splash_m, 0.8), col, (0.11, 0.085, 0.06), 'MIX')

    # --- lišejníky: nepravidelné kolonie (šedozelené) a vzácněji oranžový terčovník
    lich_warp = noise_tex(nt, P, 4.0, 5, 0.6)
    wp = N(nt, "ShaderNodeVectorMath", (-1250, -1000)); wp.operation = 'ADD'
    sc = N(nt, "ShaderNodeVectorMath", (-1350, -1100)); sc.operation = 'SCALE'
    L(nt, lich_warp.outputs["Color"], sc.inputs[0]); sc.inputs["Scale"].default_value = 0.12
    L(nt, P, wp.inputs[0]); L(nt, sc.outputs[0], wp.inputs[1])
    lich_v = N(nt, "ShaderNodeTexVoronoi", (-1100, -1000))
    lich_v.inputs["Scale"].default_value = 9.0
    L(nt, wp.outputs[0], lich_v.inputs["Vector"])
    lich_edge = noise_tex(nt, P, 30.0, 4, 0.7)              # laločnatý okraj kolonie
    radius = math_(nt, 'ADD', lich_v.outputs["Distance"], math_(nt, 'MULTIPLY', lich_edge.outputs[0], 0.18))
    lich_c = N(nt, "ShaderNodeSeparateColor", (-700, -1000)); L(nt, lich_v.outputs["Color"], lich_c.inputs[0])
    size = math_(nt, 'ADD', 0.25, math_(nt, 'MULTIPLY', lich_c.outputs[1], 0.18))
    lich = smooth(nt, math_(nt, 'SUBTRACT', radius, size), 0.10, -0.05)
    lich_mask_n = noise_tex(nt, P, 1.3, 4, 0.6)
    lich = math_(nt, 'MULTIPLY', lich, smooth(nt, lich_mask_n.outputs[0], 0.52, 0.66))
    lich = math_(nt, 'MULTIPLY', lich, smooth(nt, height, 0.3, 0.7))
    lich = math_(nt, 'MULTIPLY', lich, math_(nt, 'SUBTRACT', 1.0, cav, clamp=True))
    orange = smooth(nt, lich_c.outputs[0], 0.86, 0.9)
    lich_in = noise_tex(nt, P, 60.0, 3, 0.6)               # střed kolonie tmavší a hrbolatější
    lich_col = mix(nt, smooth(nt, lich_in.outputs[0], 0.4, 0.65), (0.29, 0.31, 0.25), (0.41, 0.43, 0.35))
    lich_col = mix(nt, orange, lich_col, (0.60, 0.34, 0.08))
    col = mix(nt, math_(nt, 'MULTIPLY', lich, 0.65), col, lich_col, 'MIX')

    # --- mech: na horních plochách a na severní (−Y) straně, v prohlubních hustší
    moss_n = noise_tex(nt, P, 2.6, 8, 0.7)
    moss_d = noise_tex(nt, P, 55.0, 4, 0.7)
    north = smooth(nt, math_(nt, 'MULTIPLY', sep.outputs["Y"], -1.0), 0.15, 0.75)
    moss_dir = math_(nt, 'MAXIMUM', smooth(nt, up, 0.45, 0.85),
                     math_(nt, 'MULTIPLY', north, smooth(nt, up, -0.2, 0.3)))
    moss = math_(nt, 'MULTIPLY', moss_dir, smooth(nt, moss_n.outputs[0], 0.42, 0.55))
    moss = math_(nt, 'ADD', moss, math_(nt, 'MULTIPLY', cav, math_(nt, 'MULTIPLY', moss_dir, 0.5)))
    moss = math_(nt, 'MULTIPLY', moss, smooth(nt, moss_d.outputs[0], 0.38, 0.5), clamp=True)
    moss = math_(nt, 'MULTIPLY', moss, smooth(nt, height, 0.08, 0.3))
    moss_tone = ramp(nt, moss_d.outputs[0], [
        (0.35, (0.030, 0.045, 0.012)),
        (0.55, (0.085, 0.115, 0.025)),
        (0.70, (0.150, 0.170, 0.045)),
        (0.85, (0.120, 0.100, 0.045)),     # zaschlé hnědé konečky
    ], (-600, -1300))
    col = mix(nt, moss, col, moss_tone.outputs[0], 'MIX')

    L(nt, col, bsdf.inputs["Base Color"])

    # drsnost
    rough = math_(nt, 'ADD', 0.82, math_(nt, 'MULTIPLY', n_mid.outputs[0], 0.12))
    rough = math_(nt, 'SUBTRACT', rough, math_(nt, 'MULTIPLY', wet, 0.22))
    rough = math_(nt, 'MAXIMUM', rough, math_(nt, 'MULTIPLY', moss, 0.95))
    L(nt, rough, bsdf.inputs["Roughness"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.4

    # bump: jemné zrno + mech a lišejník vystupují
    b_h = math_(nt, 'ADD', math_(nt, 'MULTIPLY', grain.outputs[0], 0.4),
                math_(nt, 'MULTIPLY', moss, math_(nt, 'MULTIPLY', moss_d.outputs[0], 1.6)))
    b_h = math_(nt, 'ADD', b_h, math_(nt, 'MULTIPLY', lich, 0.3))
    bump = N(nt, "ShaderNodeBump", (900, -400))
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.004
    L(nt, b_h, bump.inputs["Height"])
    L(nt, bump.outputs[0], bsdf.inputs["Normal"])

    rock.data.materials.clear()
    rock.data.materials.append(mat)

    return mat
