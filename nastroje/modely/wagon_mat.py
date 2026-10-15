"""Procedurální materiál vozu: dřevo (každý díl jiná kresba a stáří), železo, bláto, rez.
Atributy z wagon_geo.py: lp, wl, wd, pid, age, metal, wheel, handled, fresh, rust_near.
"""
import bpy, os, importlib.util
_s = importlib.util.spec_from_file_location("rock_mat", os.path.join(os.path.dirname(os.path.abspath(__file__)), "rock_mat.py"))
_rm = importlib.util.module_from_spec(_s); _s.loader.exec_module(_rm)
N, L, ramp, mix, math_, noise_tex, smooth = _rm.N, _rm.L, _rm.ramp, _rm.mix, _rm.math_, _rm.noise_tex, _rm.smooth

def attr(nt, name, loc, kind="Fac"):
    a = N(nt, "ShaderNodeAttribute", loc); a.attribute_name = name
    return a.outputs["Vector" if kind == "Vector" else ("Color" if kind == "Color" else "Fac")]

def vmath(nt, op, a, b=None, loc=(0, 0)):
    m = nt.nodes.new("ShaderNodeVectorMath"); m.operation = op; m.location = loc
    L(nt, a, m.inputs[0])
    if b is not None:
        if isinstance(b, bpy.types.NodeSocket): L(nt, b, m.inputs[1])
        else: m.inputs[1].default_value = b
    return m.outputs[0]

def apply(obj, mud_amount=1.0):
    mat = bpy.data.materials.new("wagon_wood"); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial", (1600, 0))
    bsdf = N(nt, "ShaderNodeBsdfPrincipled", (1300, 0))
    L(nt, bsdf.outputs[0], out.inputs[0])

    lp = attr(nt, "lp", (-2000, 0), "Vector")
    wl = attr(nt, "wl", (-2000, -150), "Color")
    wd = attr(nt, "wd", (-2000, -300), "Color")
    pid = attr(nt, "pid", (-2000, 200))
    age = attr(nt, "age", (-2000, 350))
    metal = attr(nt, "metal", (-2000, 500))
    wheel = attr(nt, "wheel", (-2000, 650))
    handled = attr(nt, "handled", (-2000, 800))
    fresh = attr(nt, "fresh", (-2000, 950))
    rustn = attr(nt, "rust_near", (-2000, 1100))
    geo = N(nt, "ShaderNodeNewGeometry", (-2000, -500))
    sepP = N(nt, "ShaderNodeSeparateXYZ", (-1800, -500)); L(nt, geo.outputs["Position"], sepP.inputs[0])
    sepN = N(nt, "ShaderNodeSeparateXYZ", (-1800, -650)); L(nt, geo.outputs["Normal"], sepN.inputs[0])
    zw = sepP.outputs["Z"]; up = sepN.outputs["Z"]

    # náhodný posun pro každý díl -> jiný střed let, jiný výřez kmene
    wn = N(nt, "ShaderNodeTexWhiteNoise", (-1800, 200)); wn.noise_dimensions = '1D'
    L(nt, pid, wn.inputs["W"])
    off = vmath(nt, 'MULTIPLY', wn.outputs["Color"], (0.0, 0.6, 0.6))
    off = vmath(nt, 'SUBTRACT', off, (0.0, 0.3, 0.3))
    p = vmath(nt, 'ADD', lp, off)

    # léta (soustředné válce kolem osy X = podél vláken) + zvlnění
    warp = noise_tex(nt, vmath(nt, 'MULTIPLY', p, (0.8, 6.0, 6.0)), 1.0, 4, 0.5)
    pw = vmath(nt, 'ADD', p, vmath(nt, 'MULTIPLY', warp.outputs["Color"], (0.0, 0.012, 0.012)))
    rings = N(nt, "ShaderNodeTexWave", (-1200, 0))
    rings.wave_type = 'RINGS'; rings.rings_direction = 'X'; rings.wave_profile = 'SAW'
    rings.inputs["Scale"].default_value = 28.0
    rings.inputs["Distortion"].default_value = 4.0
    rings.inputs["Detail"].default_value = 3.0
    L(nt, pw, rings.inputs["Vector"])
    ring_v = smooth(nt, rings.outputs["Fac"], 0.45, 0.97)
    # vlákna – protažený šum podél délky
    fib = noise_tex(nt, vmath(nt, 'MULTIPLY', p, (0.4, 55.0, 55.0)), 1.0, 6, 0.6)
    fib2 = noise_tex(nt, vmath(nt, 'MULTIPLY', p, (3.0, 18.0, 18.0)), 1.0, 4, 0.6)
    g = math_(nt, 'ADD', math_(nt, 'MULTIPLY', ring_v, 0.6), math_(nt, 'MULTIPLY', smooth(nt, fib.outputs[0], 0.3, 0.7), 0.4))
    g = math_(nt, 'ADD', g, math_(nt, 'MULTIPLY', fib2.outputs[0], 0.25), clamp=True)
    col = mix(nt, g, wl, wd, 'MIX')

    # suky
    kv = N(nt, "ShaderNodeTexVoronoi", (-1200, -300))
    kv.inputs["Scale"].default_value = 1.0
    L(nt, vmath(nt, 'MULTIPLY', p, (1.6, 9.0, 9.0)), kv.inputs["Vector"])
    kc = N(nt, "ShaderNodeSeparateColor", (-1000, -400)); L(nt, kv.outputs["Color"], kc.inputs[0])
    knot = math_(nt, 'MULTIPLY', smooth(nt, kv.outputs["Distance"], 0.12, 0.03), smooth(nt, kc.outputs[0], 0.72, 0.78))
    col = mix(nt, math_(nt, 'MULTIPLY', knot, 0.85), col, (0.06, 0.035, 0.02))

    # stáří: šednutí a vymývání na sluncem a deštěm exponovaných plochách
    wnz = noise_tex(nt, vmath(nt, 'MULTIPLY', p, (1.0, 4.0, 4.0)), 2.0, 5, 0.6)
    expo = math_(nt, 'ADD', 0.45, math_(nt, 'MULTIPLY', smooth(nt, up, -0.2, 0.9), 0.55))
    grey = math_(nt, 'MULTIPLY', age, math_(nt, 'MULTIPLY', expo, smooth(nt, wnz.outputs[0], 0.3, 0.65)))
    grey = math_(nt, 'MULTIPLY', grey, math_(nt, 'SUBTRACT', 1.0, fresh), clamp=True)
    grey_col = mix(nt, fib.outputs[0], (0.16, 0.145, 0.12), (0.09, 0.08, 0.065))
    col = mix(nt, math_(nt, 'MULTIPLY', grey, 0.5), col, grey_col)

    # praskliny podél vláken (víc u starých kusů)
    chk_n = noise_tex(nt, vmath(nt, 'MULTIPLY', p, (0.35, 70.0, 70.0)), 1.0, 3, 0.5)
    chk = smooth(nt, math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', chk_n.outputs[0], 0.5)), 0.012, 0.0)
    chk_m = noise_tex(nt, vmath(nt, 'MULTIPLY', p, (1.2, 3.0, 3.0)), 1.0, 2, 0.5)
    chk = math_(nt, 'MULTIPLY', chk, math_(nt, 'MULTIPLY', smooth(nt, chk_m.outputs[0], 0.45, 0.6), age))
    col = mix(nt, math_(nt, 'MULTIPLY', chk, 0.9), col, (0.03, 0.022, 0.015))

    # ošoupané hrany: světlejší, hladší
    edge = smooth(nt, geo.outputs["Pointiness"], 0.52, 0.62)
    col = mix(nt, math_(nt, 'MULTIPLY', edge, 0.45), col, mix(nt, 0.5, wl, (0.36, 0.30, 0.22)))
    # osahané (bidla, oj): tmavší umaštěné, lesklejší
    hand_n = noise_tex(nt, vmath(nt, 'MULTIPLY', p, (2.0, 2.0, 2.0)), 1.0, 3, 0.5)
    hand = math_(nt, 'MULTIPLY', handled, smooth(nt, hand_n.outputs[0], 0.35, 0.6))
    col = mix(nt, math_(nt, 'MULTIPLY', hand, 0.5), col, (0.10, 0.07, 0.045))

    # špína v koutech (AO)
    ao = N(nt, "ShaderNodeAmbientOcclusion", (-1200, -800)); ao.samples = 12; ao.only_local = True
    ao.inputs["Distance"].default_value = 0.08
    cav = smooth(nt, ao.outputs["AO"], 0.9, 0.35)
    col = mix(nt, math_(nt, 'MULTIPLY', cav, 0.7), col, (0.05, 0.04, 0.03))

    # rezavé stékance kolem železa
    rs_n = noise_tex(nt, vmath(nt, 'MULTIPLY', geo.outputs["Position"], (30.0, 30.0, 4.0)), 1.0, 4, 0.6)
    rs = math_(nt, 'MULTIPLY', rustn, smooth(nt, rs_n.outputs[0], 0.4, 0.6))
    col = mix(nt, math_(nt, 'MULTIPLY', rs, 0.8), col, (0.16, 0.075, 0.035))

    # ---- železo
    rust_n = noise_tex(nt, vmath(nt, 'MULTIPLY', geo.outputs["Position"], (14.0, 14.0, 14.0)), 1.0, 6, 0.65)
    rust_f = smooth(nt, rust_n.outputs[0], 0.5, 0.68)
    iron = mix(nt, rust_f, (0.035, 0.033, 0.032), (0.12, 0.055, 0.028))
    col = mix(nt, metal, col, iron)

    # ---- bláto: zespodu nahoru, nejvíc na kolech
    mud_n = noise_tex(nt, vmath(nt, 'MULTIPLY', geo.outputs["Position"], (5.0, 5.0, 5.0)), 1.0, 6, 0.65)
    spl = noise_tex(nt, vmath(nt, 'MULTIPLY', geo.outputs["Position"], (40.0, 40.0, 40.0)), 1.0, 3, 0.6)
    h = math_(nt, 'ADD', zw, math_(nt, 'MULTIPLY', mud_n.outputs[0], 0.25))
    mud_body = smooth(nt, h, 0.7, 0.2)
    mud_wheel = math_(nt, 'MULTIPLY', wheel, smooth(nt, h, 1.1, 0.35))
    mud = math_(nt, 'MAXIMUM', mud_body, mud_wheel)
    mud = math_(nt, 'MULTIPLY', mud, smooth(nt, spl.outputs[0], 0.3, 0.5))
    mud = math_(nt, 'MULTIPLY', mud, mud_amount, clamp=True)
    mud_col = mix(nt, smooth(nt, mud_n.outputs[0], 0.4, 0.7), (0.07, 0.055, 0.04), (0.21, 0.175, 0.13))
    col = mix(nt, mud, col, mud_col)

    L(nt, col, bsdf.inputs["Base Color"])

    rough = math_(nt, 'ADD', 0.78, math_(nt, 'MULTIPLY', fib.outputs[0], 0.15))
    rough = math_(nt, 'SUBTRACT', rough, math_(nt, 'MULTIPLY', edge, 0.15))
    rough = math_(nt, 'SUBTRACT', rough, math_(nt, 'MULTIPLY', hand, 0.35))
    rough = mix(nt, metal, rough, math_(nt, 'ADD', 0.55, math_(nt, 'MULTIPLY', rust_f, 0.35)))
    rough = math_(nt, 'MAXIMUM', rough, math_(nt, 'MULTIPLY', mud, 0.95))
    L(nt, rough, bsdf.inputs["Roughness"])
    metallic = math_(nt, 'MULTIPLY', metal, math_(nt, 'SUBTRACT', 1.0, rust_f))
    metallic = math_(nt, 'MULTIPLY', metallic, math_(nt, 'SUBTRACT', 1.0, mud), clamp=True)
    metallic = math_(nt, 'MULTIPLY', metallic, 0.85)
    L(nt, metallic, bsdf.inputs["Metallic"])

    # reliéf: vlákna, léta (vyčnívají u starého dřeva), praskliny, bláto
    bh = math_(nt, 'MULTIPLY', fib.outputs[0], math_(nt, 'ADD', 0.2, math_(nt, 'MULTIPLY', age, 0.6)))
    bh = math_(nt, 'ADD', bh, math_(nt, 'MULTIPLY', ring_v, math_(nt, 'MULTIPLY', age, 0.35)))
    bh = math_(nt, 'SUBTRACT', bh, math_(nt, 'MULTIPLY', chk, 1.5))
    bh = math_(nt, 'ADD', bh, math_(nt, 'MULTIPLY', mud, math_(nt, 'MULTIPLY', spl.outputs[0], 1.2)))
    bh = math_(nt, 'ADD', bh, math_(nt, 'MULTIPLY', metal, math_(nt, 'MULTIPLY', rust_n.outputs[0], 0.8)))
    bump = N(nt, "ShaderNodeBump", (1100, -500))
    bump.inputs["Strength"].default_value = 0.45
    bump.inputs["Distance"].default_value = 0.0025
    L(nt, bh, bump.inputs["Height"]); L(nt, bump.outputs[0], bsdf.inputs["Normal"])

    obj.data.materials.clear(); obj.data.materials.append(mat)
    return mat


def apply_canvas(obj):
    """Hrubé lněné plátno: švy po šířce role, záplaty, vybledlý vršek, špinavý spodek, mapy od vody."""
    mat = bpy.data.materials.new("canvas_len"); mat.use_nodes = True
    mat.use_backface_culling = False
    nt = mat.node_tree; nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial", (1600, 0))
    bsdf = N(nt, "ShaderNodeBsdfPrincipled", (1300, 0))
    L(nt, bsdf.outputs[0], out.inputs[0])
    lp = attr(nt, "lp", (-2000, 0), "Vector")
    sep = N(nt, "ShaderNodeSeparateXYZ", (-1800, 0)); L(nt, lp, sep.inputs[0])
    ly, ls = sep.outputs["X"], sep.outputs["Y"]          # délka vozu, obvod oblouku
    geo = N(nt, "ShaderNodeNewGeometry", (-2000, -500))
    sepN = N(nt, "ShaderNodeSeparateXYZ", (-1800, -500)); L(nt, geo.outputs["Normal"], sepN.inputs[0])
    sepP = N(nt, "ShaderNodeSeparateXYZ", (-1800, -650)); L(nt, geo.outputs["Position"], sepP.inputs[0])
    up = sepN.outputs["Z"]; zw = sepP.outputs["Z"]

    # pruhy plátna (role ~70 cm) – každý trochu jiný odstín, šev mezi nimi
    strip = math_(nt, 'DIVIDE', ly, 0.7)
    sid = math_(nt, 'FLOOR', strip)
    sfr = math_(nt, 'FRACT', strip)
    wn = N(nt, "ShaderNodeTexWhiteNoise", (-1400, 200)); wn.noise_dimensions = '1D'; L(nt, sid, wn.inputs["W"])
    base = mix(nt, wn.outputs["Value"], (0.20, 0.16, 0.105), (0.27, 0.22, 0.15))
    n1 = noise_tex(nt, lp, 3.0, 6, 0.6); n2 = noise_tex(nt, lp, 40.0, 4, 0.6)
    col = mix(nt, 0.35, base, mix(nt, n1.outputs[0], (0.15, 0.13, 0.095), (0.29, 0.255, 0.19)))
    col = mix(nt, 1.0, col, ramp(nt, n2.outputs[0], [(0.3, (0.9, 0.9, 0.9)), (0.7, (1.08, 1.06, 1.03))]).outputs[0], 'MULTIPLY')
    seam = math_(nt, 'MAXIMUM', smooth(nt, sfr, 0.012, 0.0), smooth(nt, sfr, 0.988, 1.0))
    col = mix(nt, math_(nt, 'MULTIPLY', seam, 0.6), col, (0.18, 0.15, 0.11))

    # záplaty (obdélníky jiné látky, novější = světlejší)
    pv = N(nt, "ShaderNodeTexVoronoi", (-1400, -200)); pv.distance = 'CHEBYCHEV'
    pv.inputs["Scale"].default_value = 2.2
    L(nt, lp, pv.inputs["Vector"])
    pc = N(nt, "ShaderNodeSeparateColor", (-1200, -200)); L(nt, pv.outputs["Color"], pc.inputs[0])
    patch = math_(nt, 'MULTIPLY', smooth(nt, pv.outputs["Distance"], 0.16, 0.14), smooth(nt, pc.outputs[0], 0.88, 0.9))
    col = mix(nt, patch, col, mix(nt, pc.outputs[1], (0.33, 0.29, 0.22), (0.17, 0.14, 0.095)))
    pedge = math_(nt, 'MULTIPLY', smooth(nt, pv.outputs["Distance"], 0.175, 0.16), smooth(nt, pv.outputs["Distance"], 0.14, 0.155))
    pedge = math_(nt, 'MULTIPLY', pedge, smooth(nt, pc.outputs[0], 0.88, 0.9))
    col = mix(nt, math_(nt, 'MULTIPLY', pedge, 0.7), col, (0.16, 0.13, 0.09))

    # vybledlý vršek od slunce, zelenošedé mapy a plíseň po dešti
    sun = math_(nt, 'MULTIPLY', smooth(nt, up, 0.2, 0.9), 0.35)
    col = mix(nt, sun, col, (0.34, 0.32, 0.27))
    ws = noise_tex(nt, vmath(nt, 'MULTIPLY', lp, (1.5, 1.5, 1.5)), 1.0, 6, 0.65)
    stain = smooth(nt, ws.outputs[0], 0.58, 0.66)
    ring = math_(nt, 'MULTIPLY', smooth(nt, ws.outputs[0], 0.555, 0.58), smooth(nt, ws.outputs[0], 0.61, 0.585))
    col = mix(nt, math_(nt, 'MULTIPLY', stain, 0.35), col, (0.14, 0.135, 0.10))
    col = mix(nt, math_(nt, 'MULTIPLY', ring, 0.5), col, (0.20, 0.17, 0.12))
    mild = noise_tex(nt, lp, 25.0, 3, 0.6)
    mildm = math_(nt, 'MULTIPLY', smooth(nt, mild.outputs[0], 0.62, 0.7), smooth(nt, n1.outputs[0], 0.55, 0.7))
    col = mix(nt, math_(nt, 'MULTIPLY', mildm, 0.6), col, (0.12, 0.13, 0.09))

    # špína a bláto u spodního okraje, tmavší v záhybech
    dn = noise_tex(nt, vmath(nt, 'MULTIPLY', lp, (4.0, 4.0, 4.0)), 1.0, 5, 0.6)
    dirt = smooth(nt, math_(nt, 'ADD', zw, math_(nt, 'MULTIPLY', dn.outputs[0], 0.3)), 1.95, 1.55)
    col = mix(nt, math_(nt, 'MULTIPLY', dirt, 0.7), col, (0.13, 0.10, 0.07))
    ao = N(nt, "ShaderNodeAmbientOcclusion", (-1200, -900)); ao.samples = 12; ao.only_local = True
    ao.inputs["Distance"].default_value = 0.06
    col = mix(nt, math_(nt, 'MULTIPLY', smooth(nt, ao.outputs["AO"], 0.95, 0.4), 0.5), col, (0.12, 0.10, 0.07))
    L(nt, col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.93
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.12

    # reliéf: vazba plátna, šev jako vystouplá linka, okraj záplaty
    weave = N(nt, "ShaderNodeTexWave", (-1200, -1200)); weave.wave_type = 'BANDS'; weave.bands_direction = 'X'
    weave.inputs["Scale"].default_value = 0.0
    bh = math_(nt, 'ADD', math_(nt, 'MULTIPLY', n2.outputs[0], 0.5), math_(nt, 'MULTIPLY', seam, 1.2))
    bh = math_(nt, 'ADD', bh, math_(nt, 'MULTIPLY', pedge, 1.0))
    fine = noise_tex(nt, vmath(nt, 'MULTIPLY', lp, (300.0, 300.0, 300.0)), 1.0, 2, 0.5)
    bh = math_(nt, 'ADD', bh, math_(nt, 'MULTIPLY', fine.outputs[0], 0.3))
    bump = N(nt, "ShaderNodeBump", (1100, -500)); bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.002
    L(nt, bh, bump.inputs["Height"]); L(nt, bump.outputs[0], bsdf.inputs["Normal"])
    obj.data.materials.clear(); obj.data.materials.append(mat)
    return mat


def apply_log(obj):
    """Pařez/kmen: brázditá kůra (dub), řezná plocha s letokruhy a prasklinami, mech, choroš."""
    mat = bpy.data.materials.new("log_mat"); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial", (1600, 0)); bsdf = N(nt, "ShaderNodeBsdfPrincipled", (1300, 0))
    L(nt, bsdf.outputs[0], out.inputs[0])
    lp = attr(nt, "lp", (-2000, 0), "Vector"); bark = attr(nt, "bark", (-2000, 200))
    rad = attr(nt, "rad", (-2000, 350)); fung = attr(nt, "fung", (-2000, 500))
    geo = N(nt, "ShaderNodeNewGeometry", (-2000, -500))
    sepN = N(nt, "ShaderNodeSeparateXYZ", (-1800, -500)); L(nt, geo.outputs["Normal"], sepN.inputs[0])
    up = sepN.outputs["Z"]
    sepP = N(nt, "ShaderNodeSeparateXYZ", (-1800, -650)); L(nt, geo.outputs["Position"], sepP.inputs[0])
    zw = sepP.outputs["Z"]
    # --- kůra: hluboké podélné brázdy
    fur = noise_tex(nt, vmath(nt, 'MULTIPLY', lp, (2.0, 14.0, 14.0)), 1.0, 6, 0.55)
    ridge = smooth(nt, fur.outputs[0], 0.42, 0.58)
    cross = noise_tex(nt, vmath(nt, 'MULTIPLY', lp, (12.0, 30.0, 30.0)), 1.0, 3, 0.5)
    ridge = math_(nt, 'MULTIPLY', ridge, smooth(nt, cross.outputs[0], 0.3, 0.45))
    bcol = mix(nt, ridge, (0.035, 0.03, 0.025), (0.17, 0.15, 0.125))
    lich = noise_tex(nt, vmath(nt, 'MULTIPLY', lp, (3.0, 6.0, 6.0)), 1.0, 5, 0.6)
    bcol = mix(nt, math_(nt, 'MULTIPLY', smooth(nt, lich.outputs[0], 0.58, 0.68), ridge), bcol, (0.30, 0.31, 0.25))
    # --- dřevo na řezu: letokruhy kolem osy, tmavší jádro, radiální praskliny, šednutí
    rings = N(nt, "ShaderNodeTexWave", (-1200, 0)); rings.wave_type = 'RINGS'; rings.rings_direction = 'X'
    rings.inputs["Scale"].default_value = 30.0; rings.inputs["Distortion"].default_value = 3.0
    L(nt, lp, rings.inputs["Vector"])
    rv = smooth(nt, rings.outputs["Fac"], 0.4, 0.95)
    wcol = mix(nt, rv, (0.30, 0.22, 0.14), (0.16, 0.11, 0.07))
    wcol = mix(nt, smooth(nt, rad, 0.75, 0.3), wcol, mix(nt, rv, (0.20, 0.13, 0.08), (0.10, 0.065, 0.04)))
    gr = N(nt, "ShaderNodeTexGradient", (-1200, -300)); gr.gradient_type = 'RADIAL'
    sw = N(nt, "ShaderNodeSeparateXYZ", (-1400, -300)); L(nt, lp, sw.inputs[0])
    cmb = N(nt, "ShaderNodeCombineXYZ", (-1300, -300)); L(nt, sw.outputs["Y"], cmb.inputs[0]); L(nt, sw.outputs["Z"], cmb.inputs[1])
    L(nt, cmb.outputs[0], gr.inputs["Vector"])
    crk_n = noise_tex(nt, lp, 8.0, 3, 0.5)
    ang = math_(nt, 'ADD', math_(nt, 'MULTIPLY', gr.outputs["Fac"], 9.0), math_(nt, 'MULTIPLY', crk_n.outputs[0], 0.6))
    crack = smooth(nt, math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', math_(nt, 'FRACT', ang), 0.5)), 0.03, 0.0)
    crack = math_(nt, 'MULTIPLY', crack, smooth(nt, rad, 0.15, 0.4))
    wcol = mix(nt, math_(nt, 'MULTIPLY', crack, 0.9), wcol, (0.03, 0.022, 0.015))
    old = noise_tex(nt, lp, 3.0, 4, 0.6)
    wcol = mix(nt, math_(nt, 'MULTIPLY', smooth(nt, old.outputs[0], 0.35, 0.6), 0.6), wcol, (0.18, 0.17, 0.15))
    col = mix(nt, smooth(nt, bark, 0.3, 0.7), wcol, bcol)
    # --- mech na horních plochách, víc u země
    mn = noise_tex(nt, vmath(nt, 'MULTIPLY', geo.outputs["Position"], (4.0, 4.0, 4.0)), 1.0, 6, 0.65)
    md = noise_tex(nt, vmath(nt, 'MULTIPLY', geo.outputs["Position"], (60.0, 60.0, 60.0)), 1.0, 3, 0.6)
    moss = math_(nt, 'MULTIPLY', smooth(nt, up, 0.1, 0.7), smooth(nt, mn.outputs[0], 0.45, 0.58))
    moss = math_(nt, 'MAXIMUM', moss, math_(nt, 'MULTIPLY', smooth(nt, zw, 0.25, 0.02), smooth(nt, mn.outputs[0], 0.35, 0.5)))
    moss = math_(nt, 'MULTIPLY', moss, smooth(nt, md.outputs[0], 0.35, 0.5), clamp=True)
    mcol = mix(nt, md.outputs[0], (0.03, 0.05, 0.012), (0.13, 0.16, 0.04))
    col = mix(nt, moss, col, mcol)
    # --- choroš: hnědé zóny, světlý okraj
    fz = N(nt, "ShaderNodeSeparateXYZ", (-1400, -900)); L(nt, lp, fz.inputs[0])
    fr = math_(nt, 'POWER', math_(nt, 'ADD', math_(nt, 'MULTIPLY', fz.outputs["X"], fz.outputs["X"]), math_(nt, 'MULTIPLY', fz.outputs["Y"], fz.outputs["Y"])), 0.5)
    zones = math_(nt, 'SINE', math_(nt, 'MULTIPLY', fr, 40.0))
    fcol = mix(nt, smooth(nt, zones, -0.5, 0.5), (0.10, 0.07, 0.045), (0.22, 0.16, 0.10))
    fcol = mix(nt, smooth(nt, fr, 0.96, 1.0), fcol, (0.40, 0.35, 0.27))
    col = mix(nt, fung, col, fcol)
    ao = N(nt, "ShaderNodeAmbientOcclusion", (-1200, -1100)); ao.samples = 12; ao.only_local = True
    ao.inputs["Distance"].default_value = 0.06
    col = mix(nt, math_(nt, 'MULTIPLY', smooth(nt, ao.outputs["AO"], 0.9, 0.35), 0.7), col, (0.02, 0.018, 0.014))
    L(nt, col, bsdf.inputs["Base Color"])
    rough = math_(nt, 'ADD', 0.8, math_(nt, 'MULTIPLY', moss, 0.15))
    L(nt, rough, bsdf.inputs["Roughness"])
    bh = math_(nt, 'MULTIPLY', ridge, math_(nt, 'MULTIPLY', bark, 2.0))
    bh = math_(nt, 'ADD', bh, math_(nt, 'MULTIPLY', rv, math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, bark), 0.4)))
    bh = math_(nt, 'SUBTRACT', bh, math_(nt, 'MULTIPLY', crack, 1.5))
    bh = math_(nt, 'ADD', bh, math_(nt, 'MULTIPLY', moss, math_(nt, 'MULTIPLY', md.outputs[0], 2.0)))
    bump = N(nt, "ShaderNodeBump", (1100, -500)); bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.006
    L(nt, bh, bump.inputs["Height"]); L(nt, bump.outputs[0], bsdf.inputs["Normal"])
    obj.data.materials.clear(); obj.data.materials.append(mat)
    return mat
