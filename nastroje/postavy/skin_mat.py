"""Procedurální kůže pro MPFB postavu (náhled i zapékání).
Masky obličeje/rtů/uší/víček/bradavek/nehtů z MPFB (CC0) přes původní UV MakeHumanu.
"""
import bpy, os

MASKS = "/home/claude/dl/mpfb2/src/mpfb/data/textures"

def _N(nt, t, loc=(0, 0)):
    n = nt.nodes.new(t); n.location = loc; return n

def _L(nt, a, b): nt.links.new(a, b)

def _math(nt, op, a, b=0.0, clamp=False):
    m = nt.nodes.new("ShaderNodeMath"); m.operation = op; m.use_clamp = clamp
    for s, v in ((m.inputs[0], a), (m.inputs[1], b)):
        if isinstance(v, bpy.types.NodeSocket): _L(nt, v, s)
        else: s.default_value = v
    return m.outputs[0]

def _mix(nt, fac, a, b, blend='MIX'):
    m = nt.nodes.new("ShaderNodeMix"); m.data_type = 'RGBA'; m.blend_type = blend
    for s, v in ((m.inputs[0], fac), (m.inputs[6], a), (m.inputs[7], b)):
        if isinstance(v, bpy.types.NodeSocket): _L(nt, v, s)
        else: s.default_value = v if not isinstance(v, tuple) or len(v) != 3 else (*v, 1)
    return m.outputs[2]

def _smooth(nt, x, e0, e1):
    m = nt.nodes.new("ShaderNodeMapRange"); m.interpolation_type = 'SMOOTHSTEP'
    m.inputs["From Min"].default_value = e0; m.inputs["From Max"].default_value = e1
    _L(nt, x, m.inputs["Value"]); return m.outputs["Result"]

def _noise(nt, vec, scale, detail=4, rough=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail; n.inputs["Roughness"].default_value = rough
    _L(nt, vec, n.inputs["Vector"]); return n.outputs[0]

def _mask(nt, uv, name):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(MASKS, f"mpfb_{name}.jpg"), check_existing=True)
    t.image.colorspace_settings.name = 'Non-Color'
    _L(nt, uv, t.inputs["Vector"]); return t.outputs["Color"]

def apply(obj, tone=(0.62, 0.42, 0.33), freckles=0.0, stubble=0.0, age=0.4, uv_name=None, ruddy=0.4,
          L=None, brow_col=(0.12, 0.08, 0.05)):
    """tone = lineární barva pleti; freckles/stubble/age 0..1; ruddy = zarudnutí tváří, nosu, uší."""
    mat = bpy.data.materials.new(f"{obj.name}_kuze"); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = _N(nt, "ShaderNodeOutputMaterial", (1600, 0)); b = _N(nt, "ShaderNodeBsdfPrincipled", (1300, 0))
    _L(nt, b.outputs[0], out.inputs[0])
    uvn = _N(nt, "ShaderNodeUVMap", (-1800, 300))
    uvn.uv_map = uv_name or obj.data.uv_layers[0].name
    uv = uvn.outputs[0]
    tc = _N(nt, "ShaderNodeTexCoord", (-1800, 0)); P = tc.outputs["Object"]
    face = _mask(nt, uv, "face"); lips = _mask(nt, uv, "lips"); ears = _mask(nt, uv, "ears")
    lids = _mask(nt, uv, "eyelids"); aur = _mask(nt, uv, "aureolae")
    nails = _mask(nt, uv, "fingernails"); tnails = _mask(nt, uv, "toenails")
    sepP = _N(nt, "ShaderNodeSeparateXYZ", (-1600, -300)); _L(nt, P, sepP.inputs[0])

    # základní tón s jemnou nerovnoměrností (skvrnky, žilky, pigment)
    n_big = _noise(nt, P, 6.0, 6, 0.55)
    n_mid = _noise(nt, P, 40.0, 5, 0.6)
    col = _mix(nt, 0.6, tone, _mix(nt, n_big, (tone[0] * 0.82, tone[1] * 0.72, tone[2] * 0.74),
                                     (tone[0] * 1.08, tone[1] * 1.0, tone[2] * 0.96)))
    col = _mix(nt, _math(nt, "MULTIPLY", n_mid, 0.22), col, (tone[0] * 0.8, tone[1] * 0.62, tone[2] * 0.58))
    # zarudnutí: tváře, nos, uši (maska obličeje + šum)
    red = _math(nt, 'MULTIPLY', face, _smooth(nt, _noise(nt, P, 12.0, 3, 0.5), 0.45, 0.7))
    red = _math(nt, 'MAXIMUM', red, ears)
    col = _mix(nt, _math(nt, 'MULTIPLY', red, 0.6 * ruddy), col, (tone[0] * 1.05, tone[1] * 0.62, tone[2] * 0.58))
    # rty, víčka, bradavky
    col = _mix(nt, _math(nt, 'MULTIPLY', lips, 0.75), col, (tone[0] * 0.95, tone[1] * 0.5, tone[2] * 0.5))
    col = _mix(nt, _math(nt, 'MULTIPLY', lids, 0.35), col, (tone[0] * 0.85, tone[1] * 0.62, tone[2] * 0.62))
    col = _mix(nt, _math(nt, 'MULTIPLY', aur, 0.7), col, (tone[0] * 0.75, tone[1] * 0.48, tone[2] * 0.42))
    nl = _math(nt, 'MAXIMUM', nails, tnails)
    col = _mix(nt, _math(nt, 'MULTIPLY', nl, 0.8), col, (0.62, 0.48, 0.44))
    # pihy
    if freckles > 0:
        fv = _N(nt, "ShaderNodeTexVoronoi", (-1200, -700)); fv.inputs["Scale"].default_value = 260.0
        _L(nt, P, fv.inputs["Vector"])
        fr = _math(nt, 'MULTIPLY', _smooth(nt, fv.outputs["Distance"], 0.28, 0.12),
                   _smooth(nt, _noise(nt, P, 3.0, 2, 0.5), 0.35, 0.6))
        fr = _math(nt, 'MULTIPLY', fr, _math(nt, 'ADD', 0.35, face))
        col = _mix(nt, _math(nt, 'MULTIPLY', fr, 0.55 * freckles), col, (tone[0] * 0.7, tone[1] * 0.42, tone[2] * 0.25))
    if L is not None:
        X = _math(nt, 'ABSOLUTE', sepP.outputs["X"]); Y = sepP.outputs["Y"]; Z = sepP.outputs["Z"]
        E = (L["eye_l"] + L["eye_r"]) / 2; Ex = abs(L["eye_l"].x)
        front = _smooth(nt, Y, E.y + 0.01, E.y - 0.005)
        # obočí: oblouk nad okem, u kořene nosu silnější, ke spánku slábne
        dx = _math(nt, 'SUBTRACT', X, Ex)
        arch = _math(nt, 'SUBTRACT', E.z + 0.025, _math(nt, 'MULTIPLY', _math(nt, 'POWER', _math(nt, 'SUBTRACT', dx, 0.004), 2.0), 9.0))
        dz = _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', Z, arch))
        th = _math(nt, 'SUBTRACT', 0.0042, _math(nt, 'MULTIPLY', _math(nt, 'MAXIMUM', dx, 0.0), 0.06))
        bm_ = _math(nt, 'LESS_THAN', dz, th)
        bm_ = _math(nt, 'MULTIPLY', bm_, _smooth(nt, dx, -0.027, -0.021))
        bm_ = _math(nt, 'MULTIPLY', bm_, _smooth(nt, dx, 0.033, 0.024))
        bm_ = _math(nt, 'MULTIPLY', bm_, front)
        smap = _N(nt, "ShaderNodeMapping", (0, 0)); smap.inputs["Scale"].default_value = (60.0, 60.0, 900.0)
        smap.inputs["Rotation"].default_value = (0.0, 0.35, 0.0)
        _L(nt, P, smap.inputs["Vector"])
        strands = _noise(nt, smap.outputs[0], 1.0, 4, 0.6)
        soft = _smooth(nt, _math(nt, 'DIVIDE', dz, th), 1.0, 0.4)
        brow = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', bm_, soft), _smooth(nt, strands, 0.38, 0.62))
        col = _mix(nt, _math(nt, 'MULTIPLY', brow, 0.85), col, brow_col)
        if stubble > 0:
            low = _math(nt, 'MULTIPLY', _smooth(nt, Z, L["jaw"].z - 0.035, L["jaw"].z - 0.01),
                        _smooth(nt, Z, L["mouth"].z + 0.03, L["mouth"].z + 0.012))
            low = _math(nt, 'MULTIPLY', low, _smooth(nt, Y, E.y + 0.06, E.y + 0.02))
            low = _math(nt, 'MULTIPLY', low, _smooth(nt, X, 0.072, 0.055))
            low = _math(nt, 'MULTIPLY', low, _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', lips, 1.5), clamp=True))
            dots = _N(nt, "ShaderNodeTexVoronoi", (0, 0)); dots.inputs["Scale"].default_value = 2600.0
            _L(nt, P, dots.inputs["Vector"])
            st = _math(nt, 'MULTIPLY', low, _smooth(nt, dots.outputs["Distance"], 0.35, 0.15))
            col = _mix(nt, _math(nt, 'MULTIPLY', st, 0.55 * stubble), col, (0.07, 0.055, 0.045))
            col = _mix(nt, _math(nt, 'MULTIPLY', low, 0.18 * stubble), col, (tone[0] * 0.7, tone[1] * 0.68, tone[2] * 0.72))
    _L(nt, col, b.inputs["Base Color"])
    # podpovrchový rozptyl (v Godotu: SSS u materiálu kůže)
    b.inputs["Subsurface Weight"].default_value = 0.12
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.006
    # drsnost: obličej (T-zóna) mastnější, rty lesklejší
    rough = _math(nt, 'ADD', 0.52, _math(nt, 'MULTIPLY', _noise(nt, P, 60.0, 3, 0.5), 0.12))
    rough = _math(nt, 'SUBTRACT', rough, _math(nt, 'MULTIPLY', face, 0.08))
    rough = _math(nt, 'SUBTRACT', rough, _math(nt, 'MULTIPLY', lips, 0.15))
    rough = _math(nt, 'SUBTRACT', rough, _math(nt, 'MULTIPLY', nl, 0.2))
    _L(nt, rough, b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = 0.45
    # póry a vrásky (bump)
    pores = _N(nt, "ShaderNodeTexVoronoi", (-1200, -1000)); pores.inputs["Scale"].default_value = 1400.0
    _L(nt, P, pores.inputs["Vector"])
    ph = _smooth(nt, pores.outputs["Distance"], 0.05, 0.35)
    wr = _noise(nt, P, 220.0, 3, 0.6)
    bh = _math(nt, 'ADD', _math(nt, 'MULTIPLY', ph, 0.5), _math(nt, 'MULTIPLY', wr, 0.25 + 0.6 * age))
    bump = _N(nt, "ShaderNodeBump", (1100, -500)); bump.inputs["Strength"].default_value = 0.12 + 0.12 * age
    bump.inputs["Distance"].default_value = 0.0004
    _L(nt, bh, bump.inputs["Height"]); _L(nt, bump.outputs[0], b.inputs["Normal"])
    obj.data.materials.clear(); obj.data.materials.append(mat)
    return mat
