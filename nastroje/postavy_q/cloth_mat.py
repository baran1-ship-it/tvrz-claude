"""Procedurální materiály oblečení (náhled + zapékání do textur pro .glb).
Vše v prostoru objektu postavy (metry), takže měřítko vazby/prošívání sedí.
"""
import bpy, math
from skin_mat import _N, _L, _math, _mix, _smooth, _noise

def _wave(nt, vec, scale, direction='X', bands='BANDS', dist=0.0):
    w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = bands; w.bands_direction = direction
    w.inputs["Scale"].default_value = scale; w.inputs["Distortion"].default_value = dist
    _L(nt, vec, w.inputs["Vector"]); return w.outputs["Fac"]

def _shade(c, k):
    return tuple(max(0.0, min(1.0, x * k)) for x in c)

def fabric(name, color, kind="linen", dirt=0.4, dirt_z=(0.0, 0.5), quilt=0, quilt_rings=None, dag=None,
           worn=0.3, alpha_attr=None, rough=0.85):
    """kind: linen | wool | quilted. quilt = počet svislých kanálů po obvodu (0 = bez).
    quilt_rings = (z_od, z_do, rozestup) vodorovné prošití (rukávy). dag = (počet jazyků, hloubka v UV v)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = _N(nt, "ShaderNodeOutputMaterial", (1600, 0)); b = _N(nt, "ShaderNodeBsdfPrincipled", (1300, 0))
    _L(nt, b.outputs[0], out.inputs[0])
    tc = _N(nt, "ShaderNodeTexCoord"); P = tc.outputs["Object"]
    sep = _N(nt, "ShaderNodeSeparateXYZ"); _L(nt, P, sep.inputs[0])
    Z = sep.outputs["Z"]
    # nerovnoměrné vybarvení (ručně barvená látka)
    n1 = _noise(nt, P, 4.0, 5, 0.55); n2 = _noise(nt, P, 18.0, 4, 0.6)
    col = _mix(nt, n1, _shade(color, 0.86), _shade(color, 1.1))
    col = _mix(nt, _math(nt, 'MULTIPLY', n2, 0.25), col, _shade(color, 0.75))
    # vazba: jemná mřížka nití
    wx = _wave(nt, P, 1800.0 if kind == "linen" else 1100.0, 'X'); wz = _wave(nt, P, 1800.0 if kind == "linen" else 1100.0, 'Z')
    weave = _math(nt, 'MULTIPLY', _math(nt, 'ADD', wx, wz), 0.5)
    fib = _noise(nt, P, 300.0, 3, 0.7)
    col = _mix(nt, _math(nt, 'MULTIPLY', weave, 0.05), col, _shade(color, 0.8))
    height = _math(nt, 'ADD', _math(nt, 'MULTIPLY', weave, 0.08), _math(nt, 'MULTIPLY', fib, 0.3 if kind == "wool" else 0.12))
    # prošívání: svislé kanály kolem těla (radiální úhel kolem osy postavy)
    if quilt:
        gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = 'RADIAL'; _L(nt, P, gr.inputs["Vector"])
        a = _math(nt, 'FRACT', _math(nt, 'MULTIPLY', gr.outputs["Fac"], float(quilt)))
        tri = _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', a, 0.5))       # 0 uprostřed kanálu, 0.5 na švu
        seam = _smooth(nt, tri, 0.36, 0.5)                                 # 1 = šev
        puff = _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', tri, 2.0))
        puff = _math(nt, 'POWER', _math(nt, 'MAXIMUM', puff, 0.0), 0.5)
        if quilt_rings:
            z0, z1, sp = quilt_rings
            rz = _math(nt, 'FRACT', _math(nt, 'DIVIDE', Z, sp))
            rtri = _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', rz, 0.5))
            inr = _math(nt, 'MULTIPLY', _smooth(nt, Z, z0 - 0.01, z0), _smooth(nt, Z, z1 + 0.01, z1))
            inr = _math(nt, 'MULTIPLY', inr, _smooth(nt, _math(nt, 'ABSOLUTE', sep.outputs['X']), 0.19, 0.22))
            seam = _math(nt, 'MAXIMUM', seam, _math(nt, 'MULTIPLY', _smooth(nt, rtri, 0.4, 0.5), inr))
        height = _math(nt, 'ADD', height, _math(nt, 'MULTIPLY', puff, 2.5))
        height = _math(nt, 'SUBTRACT', height, _math(nt, 'MULTIPLY', seam, 1.5))
        col = _mix(nt, _math(nt, 'MULTIPLY', seam, 0.45), col, _shade(color, 0.55))
    # špína a opotřebení: dole víc, plus fleky
    lowd = _smooth(nt, Z, dirt_z[1], dirt_z[0])
    spots = _smooth(nt, _noise(nt, P, 9.0, 6, 0.65), 0.55, 0.75)
    dmask = _math(nt, 'MULTIPLY', _math(nt, 'ADD', _math(nt, 'MULTIPLY', lowd, 0.8), _math(nt, 'MULTIPLY', spots, 0.35)), dirt)
    col = _mix(nt, _math(nt, 'MINIMUM', dmask, 0.5), col, (0.12, 0.095, 0.07))
    fade = _math(nt, 'MULTIPLY', _smooth(nt, _noise(nt, P, 3.0, 3, 0.5), 0.5, 0.7), worn * 0.5)
    col = _mix(nt, fade, col, _shade(color, 1.25))
    _L(nt, col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    if kind == "wool":
        b.inputs["Sheen Weight"].default_value = 0.12; b.inputs["Sheen Roughness"].default_value = 0.6
    bump = _N(nt, "ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6; bump.inputs["Distance"].default_value = 0.002
    _L(nt, height, bump.inputs["Height"]); _L(nt, bump.outputs[0], b.inputs["Normal"])
    if dag:
        n_t, depth = dag
        uvn = _N(nt, "ShaderNodeUVMap"); uvn.uv_map = "UVMap"
        sp = _N(nt, "ShaderNodeSeparateXYZ"); _L(nt, uvn.outputs[0], sp.inputs[0])
        f = _math(nt, 'FRACT', _math(nt, 'MULTIPLY', sp.outputs["X"], float(n_t)))
        q = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', f, 0.5), 2.0)
        circ = _math(nt, 'SQRT', _math(nt, 'MAXIMUM', _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', q, q)), 0.0))
        thr = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, circ), depth)
        a = _math(nt, 'GREATER_THAN', sp.outputs["Y"], thr)
        _L(nt, a, b.inputs["Alpha"])
    return m

def leather(name, color, dirt=0.3, rough=0.6, worn=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = _N(nt, "ShaderNodeOutputMaterial"); b = _N(nt, "ShaderNodeBsdfPrincipled"); _L(nt, b.outputs[0], out.inputs[0])
    tc = _N(nt, "ShaderNodeTexCoord"); P = tc.outputs["Object"]
    sep = _N(nt, "ShaderNodeSeparateXYZ"); _L(nt, P, sep.inputs[0])
    n1 = _noise(nt, P, 7.0, 6, 0.6)
    col = _mix(nt, n1, _shade(color, 0.75), _shade(color, 1.15))
    vor = _N(nt, "ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 420.0; _L(nt, P, vor.inputs["Vector"])
    grain = _smooth(nt, vor.outputs["Distance"], 0.0, 0.5)
    scr = _smooth(nt, _noise(nt, P, 60.0, 8, 0.75), 0.62, 0.7)
    col = _mix(nt, _math(nt, 'MULTIPLY', scr, worn), col, _shade(color, 1.45))
    crease = _smooth(nt, _noise(nt, P, 25.0, 6, 0.7), 0.3, 0.2)
    col = _mix(nt, _math(nt, 'MULTIPLY', crease, 0.4), col, _shade(color, 0.5))
    low = _smooth(nt, sep.outputs["Z"], 0.35, 0.02)
    col = _mix(nt, _math(nt, 'MULTIPLY', low, 0.4 * dirt), col, (0.13, 0.1, 0.07))
    _L(nt, col, b.inputs["Base Color"])
    r = _math(nt, 'ADD', rough, _math(nt, 'MULTIPLY', scr, 0.2))
    _L(nt, r, b.inputs["Roughness"])
    h = _math(nt, 'ADD', _math(nt, 'MULTIPLY', grain, 0.4), _math(nt, 'MULTIPLY', crease, -0.6))
    bump = _N(nt, "ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.001
    _L(nt, h, bump.inputs["Height"]); _L(nt, bump.outputs[0], b.inputs["Normal"])
    return m

def metal(name, color=(0.55, 0.55, 0.56), rust=0.2, rough=0.35):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = _N(nt, "ShaderNodeOutputMaterial"); b = _N(nt, "ShaderNodeBsdfPrincipled"); _L(nt, b.outputs[0], out.inputs[0])
    tc = _N(nt, "ShaderNodeTexCoord"); P = tc.outputs["Object"]
    n1 = _noise(nt, P, 30.0, 6, 0.6); scr = _noise(nt, P, 200.0, 4, 0.7)
    col = _mix(nt, n1, _shade(color, 0.8), _shade(color, 1.05))
    rm = _math(nt, 'MULTIPLY', _smooth(nt, _noise(nt, P, 12.0, 8, 0.7), 0.6, 0.75), rust)
    col = _mix(nt, rm, col, (0.25, 0.11, 0.04))
    _L(nt, col, b.inputs["Base Color"])
    _L(nt, _math(nt, 'SUBTRACT', 1.0, rm), b.inputs["Metallic"])
    _L(nt, _math(nt, 'ADD', rough, _math(nt, 'ADD', _math(nt, 'MULTIPLY', scr, 0.15), _math(nt, 'MULTIPLY', rm, 0.5))), b.inputs["Roughness"])
    return m
