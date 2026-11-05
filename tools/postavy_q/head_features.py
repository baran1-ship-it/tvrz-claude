"""Obličejové prvky postavy: orientační body, obočí + strniště (do materiálu), vlasy jako slupka nad hlavou.
"""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector

def evaluated_coords(obj):
    """Souřadnice po tvarových klíčích, bez modifikátorů (aby sedělo číslování vrcholů)."""
    saved = [(m, m.show_viewport) for m in obj.modifiers]
    for m, _ in saved: m.show_viewport = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
    no = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("normal", no)
    ev.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    bpy.context.view_layer.update()
    return co.reshape(-1, 3), no.reshape(-1, 3)

def group_weights(obj, name):
    n = len(obj.data.vertices); w = np.zeros(n)
    if name not in obj.vertex_groups: return w
    gi = obj.vertex_groups[name].index
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group == gi: w[v.index] = g.weight
    return w

def landmarks(obj):
    co, _ = evaluated_coords(obj)
    L = {}
    for g, key in (("joint-l-eye", "eye_l"), ("joint-r-eye", "eye_r"), ("joint-mouth", "mouth"), ("joint-jaw", "jaw"),
                   ("joint-neck", "neck"), ("joint-head-2", "head_top")):
        w = group_weights(obj, g)
        L[key] = Vector(co[w > 0.5].mean(0)) if (w > 0.5).any() else Vector()
    lw = group_weights(obj, "lips")
    L["lips_front_y"] = float(co[lw > 0.3][:, 1].min())
    L["mouth"] = Vector(co[lw > 0.3].mean(0))
    L["co"], L["no"] = co, None
    return L

def _hair_field(p, L, style):
    """Kladné = vlasy (v metrech nad vlasovou linií), záporné = kůže."""
    eye = (L["eye_l"] + L["eye_r"]) / 2
    Ez, Ey = eye.z, eye.y
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    ax = np.abs(x)
    if style == "muz":
        hl_front = Ez + 0.082 + 0.009 * np.exp(-((ax - 0.045) / 0.02) ** 2)
        side = Ez - 0.03          # kotlety před uchem
        back = L["neck"].z + 0.06
    elif style == "zena":
        # vlasy sčesané dozadu s pěšinkou: oblouk, uprostřed nejvýš, ke spánkům níž
        hl_front = Ez + 0.068 - 0.025 * np.clip(ax / 0.065, 0, 1.3) ** 2
        side = Ez - 0.035
        back = L["neck"].z + 0.0
    else:
        hl_front = Ez + 0.040 + 0.012 * (ax / 0.06) ** 2
        side = Ez - 0.02
        back = L["neck"].z + 0.05
    t1 = np.clip((y - (Ey + 0.035)) / 0.035, 0, 1)
    t2 = np.clip((y - (Ey + 0.10)) / 0.05, 0, 1)
    line = hl_front * (1 - t1) + side * t1
    line = line * (1 - t2) + back * t2
    f = z - line
    # oblouk kolem ucha
    ec = L.get("ear_c")
    if ec is not None:
        d = np.sqrt(((y - ec[1]) / 1.0) ** 2 + ((z - ec[2]) / 1.15) ** 2)
        f = np.minimum(f, d - 0.036)
    return f

def hair_shell(obj, L, style, color, name="vlasy", grey=0.0):
    """style: 'muz' (krátké, ustupující čelo), 'kluk' (krátké po stranách, delší nahoře, ofina)."""
    co, no = evaluated_coords(obj)
    ears = group_weights(obj, "ears"); body = group_weights(obj, "body")
    eye = (L["eye_l"] + L["eye_r"]) / 2
    Ez, Ey = eye.z, eye.y
    top = co[:, 2].max()
    ew = ears > 0.5
    L = dict(L); L["ear_c"] = (0.0, co[ew][:, 1].mean(), co[ew][:, 2].mean())
    f = _hair_field(co, L, style)
    region = (body > 0.5) & (co[:, 2] > L["neck"].z - 0.01) & (f > -0.02) & (ears < 0.05)
    sel = set(np.where(region)[0])
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    nbm = bmesh.new(); vmap = {}
    for fc in bm.faces:
        if not all(v.index in sel for v in fc.verts): continue
        for v in fc.verts:
            if v.index not in vmap: vmap[v.index] = nbm.verts.new(Vector(co[v.index]))
        try: nbm.faces.new([vmap[v.index] for v in fc.verts])
        except ValueError: pass
    bm.free()
    bmesh.ops.subdivide_edges(nbm, edges=list(nbm.edges), cuts=2, use_grid_fill=True, smooth=0.6)
    nbm.verts.ensure_lookup_table(); nbm.normal_update()
    P = np.array([v.co[:] for v in nbm.verts])
    fv = _hair_field(P, L, style)
    # pryč s plochami úplně pod linií
    kill = [fc for fc in nbm.faces if all(fv[v.index] < -0.004 for v in fc.verts)]
    bmesh.ops.delete(nbm, geom=kill, context='FACES')
    loose = [v for v in nbm.verts if not v.link_faces]
    bmesh.ops.delete(nbm, geom=loose, context='VERTS')
    nbm.verts.ensure_lookup_table(); nbm.normal_update()
    P = np.array([v.co[:] for v in nbm.verts]); fv = _hair_field(P, L, style)
    edge_l = nbm.verts.layers.float.new("edge")
    for i, v in enumerate(nbm.verts):
        e = min(1.0, max(0.0, (fv[i] + 0.004) / 0.016))
        h = (v.co.z - Ez) / max(0.01, top - Ez)
        off = (0.0025 + 0.0045 * h) if style == "muz" else ((0.004 + 0.014 * max(h, 0) ** 0.8) if style == "zena" else (0.003 + 0.017 * max(h, 0) ** 1.5))
        off *= 0.12 + 0.88 * e
        v.co += v.normal * off
        v[edge_l] = e
    me = bpy.data.meshes.new(name); nbm.to_mesh(me); nbm.free()
    uvl = me.uv_layers.new(name="UVMap")
    c = Vector((0, Ey + 0.08, Ez))
    for poly in me.polygons:
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co - c
            uvl.data[li].uv = (0.5 + math.atan2(p.x, -p.y) / (2 * math.pi), 0.5 + math.atan2(p.z, math.hypot(p.x, p.y)) / math.pi)
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    ob.parent = obj.parent; ob.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
    m = bpy.data.materials.new(f"{obj.name}_vlasy"); m.use_nodes = True
    
    t = m.node_tree; b = t.nodes["Principled BSDF"]
    uv = t.nodes.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
    mp = t.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (520.0, 6.0, 1.0)
    t.links.new(uv.outputs[0], mp.inputs[0])
    ns = t.nodes.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 3.0; ns.inputs["Detail"].default_value = 8
    t.links.new(mp.outputs[0], ns.inputs["Vector"])
    ramp = t.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.32; ramp.color_ramp.elements[0].color = (*[c_ * 0.5 for c_ in color], 1)
    ramp.color_ramp.elements[1].position = 0.72; ramp.color_ramp.elements[1].color = (*[min(1, c_ * 1.5) for c_ in color], 1)
    t.links.new(ns.outputs[0], ramp.inputs[0])
    if grey > 0:
        # šediny: po stranách a vzadu víc, zrnitě
        tcg = t.nodes.new("ShaderNodeTexCoord"); sp = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(tcg.outputs["Object"], sp.inputs[0])
        ab = t.nodes.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; t.links.new(sp.outputs["X"], ab.inputs[0])
        sd = t.nodes.new("ShaderNodeMapRange"); sd.inputs["From Min"].default_value = 0.035; sd.inputs["From Max"].default_value = 0.075
        t.links.new(ab.outputs[0], sd.inputs["Value"])
        gn = t.nodes.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 400.0; t.links.new(tcg.outputs["Object"], gn.inputs["Vector"])
        gt_ = t.nodes.new("ShaderNodeMath"); gt_.operation = 'GREATER_THAN'; gt_.inputs[1].default_value = 0.6; t.links.new(gn.outputs[0], gt_.inputs[0])
        mm = t.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; t.links.new(sd.outputs["Result"], mm.inputs[0]); t.links.new(gt_.outputs[0], mm.inputs[1])
        mg = t.nodes.new("ShaderNodeMath"); mg.operation = 'MULTIPLY'; t.links.new(mm.outputs[0], mg.inputs[0]); mg.inputs[1].default_value = grey
        mx_ = t.nodes.new("ShaderNodeMix"); mx_.data_type = 'RGBA'
        t.links.new(mg.outputs[0], mx_.inputs[0]); t.links.new(ramp.outputs[0], mx_.inputs[6]); mx_.inputs[7].default_value = (0.3, 0.29, 0.28, 1)
        t.links.new(mx_.outputs[2], b.inputs["Base Color"])
    else:
        t.links.new(ramp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.68
    b.inputs["Specular IOR Level"].default_value = 0.3
    b.inputs["Coat Weight"].default_value = 0.0
    # alpha: okraj řídne (zrnitě), uvnitř plné
    at = t.nodes.new("ShaderNodeAttribute"); at.attribute_name = "edge"
    nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 700.0; nz.inputs["Detail"].default_value = 2
    tc = t.nodes.new("ShaderNodeTexCoord"); t.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ad = t.nodes.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'
    t.links.new(at.outputs["Fac"], ad.inputs[0]); ad.inputs[1].default_value = 1.2
    t.links.new(nz.outputs[0], ad.inputs[2])
    gt = t.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'
    t.links.new(ad.outputs[0], gt.inputs[0]); gt.inputs[1].default_value = 0.85
    t.links.new(gt.outputs[0], b.inputs["Alpha"])
    me.materials.append(m)
    return ob


def braid(obj, L, color, hair_ob, length=0.38, name="cop"):
    """Cop z týla dolů po zádech: trubka s pramenným vzorem, váhy hlava -> krk -> hrudní páteř."""
    co, no = evaluated_coords(obj)
    body = group_weights(obj, "body") > 0.5
    eye = (L["eye_l"] + L["eye_r"]) / 2
    Ez = eye.z
    # nejzadnější bod hlavy ve výšce očí
    m = body & (np.abs(co[:, 0]) < 0.02) & (np.abs(co[:, 2] - (Ez - 0.01)) < 0.015)
    back_y = co[m][:, 1].max()
    start = Vector((0, back_y + 0.012, Ez - 0.01))
    # dráha: dolů po zádech (drží odstup od těla)
    pts = []
    n = 24
    for i in range(n + 1):
        t = i / n
        z = start.z - length * t - 0.06 * t
        sl = body & (np.abs(co[:, 0]) < 0.03) & (np.abs(co[:, 2] - z) < 0.012)
        yb = co[sl][:, 1].max() if sl.any() else start.y
        y = max(yb + 0.03, start.y - 0.01 if t < 0.15 else yb + 0.03)
        pts.append(Vector((0.004 * math.sin(t * 5), y, z)))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    rings = []; N = 10
    for i, p in enumerate(pts):
        t = i / n
        r = (0.028 if t < 0.1 else 0.022) * (1 - 0.55 * t ** 1.5)
        if i == n: r *= 0.5
        tang = (pts[min(i + 1, n)] - pts[max(i - 1, 0)]).normalized()
        a = tang.cross(Vector((1, 0, 0))).normalized(); b = tang.cross(a).normalized()
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * k / N) + b * math.sin(2 * math.pi * k / N)) * r * (1 + 0.12 * math.cos(2 * math.pi * (k / N * 3 + t * 9)))) for k in range(N)])
    for i in range(n):
        for k in range(N):
            k2 = (k + 1) % N
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for lp, (u, v) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                lp[uvl].uv = (u / N, 1 - v / n)
    bmesh.ops.contextual_create(bm, geom=rings[-1])
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    # pramenný vzor copu: šikmé pruhy (3 prameny) + jemná vlákna
    mt = bpy.data.materials.new(f"{obj.name}_cop"); mt.use_nodes = True; t = mt.node_tree; bs = t.nodes["Principled BSDF"]
    uv = t.nodes.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
    sep = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(uv.outputs[0], sep.inputs[0])
    mul = t.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 3.0
    t.links.new(sep.outputs["X"], mul.inputs[0])
    mv = t.nodes.new("ShaderNodeMath"); mv.operation = 'MULTIPLY'; mv.inputs[1].default_value = 14.0
    t.links.new(sep.outputs["Y"], mv.inputs[0])
    ad = t.nodes.new("ShaderNodeMath"); ad.operation = 'ADD'; t.links.new(mul.outputs[0], ad.inputs[0]); t.links.new(mv.outputs[0], ad.inputs[1])
    fr = t.nodes.new("ShaderNodeMath"); fr.operation = 'PINGPONG'; fr.inputs[1].default_value = 0.5; t.links.new(ad.outputs[0], fr.inputs[0])
    ramp = t.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (*[c * 0.35 for c in color], 1)
    ramp.color_ramp.elements[1].position = 0.45; ramp.color_ramp.elements[1].color = (*[min(1, c * 1.5) for c in color], 1)
    t.links.new(fr.outputs[0], ramp.inputs[0]); t.links.new(ramp.outputs[0], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.6
    me.materials.append(mt)
    # váhy: kořen na hlavě, konec na hrudní páteři (export přidá skupiny podle těchto atributů)
    zs = np.array([v.co.z for v in me.vertices])
    wh = np.clip((zs - (start.z - 0.12)) / 0.12, 0, 1)
    gh = ob.vertex_groups.new(name="head"); gs = ob.vertex_groups.new(name="spine_03"); gn = ob.vertex_groups.new(name="neck_01")
    for i, w in enumerate(wh):
        gh.add([i], float(w), 'REPLACE'); gn.add([i], float(0.4 * (1 - w)), 'REPLACE'); gs.add([i], float(0.6 * (1 - w)), 'REPLACE')
    return ob


def loose_hair(obj, L, color, length=0.34, name="rozpustene"):
    """Rozpuštěné dlouhé vlasy: polootevřená slupka kolem zadní a boční části hlavy, krku a zad,
    visí přes ramena; konce řídnou (alfa podle UV v)."""
    co, no = evaluated_coords(obj)
    body = group_weights(obj, "body") > 0.5
    eye = (L["eye_l"] + L["eye_r"]) / 2
    Ez, Ey = eye.z, eye.y
    z_top = Ez + 0.02; z_bot = L["neck"].z - length
    cy = Ey + 0.09
    P = co[body & (co[:, 2] < z_top + 0.03) & (co[:, 2] > z_bot - 0.03)]
    # paže vynechat (jen blízko ramen)
    rows = 26; N = 34
    zs = np.linspace(z_top, z_bot, rows + 1)
    th = np.linspace(math.radians(-82), math.radians(82), N)    # 0 = dozadu (+Y)
    R = np.zeros((rows + 1, N))
    for r, z in enumerate(zs):
        sl = P[np.abs(P[:, 2] - z) < 0.015]
        sl = sl[np.abs(sl[:, 0]) < 0.24]
        if len(sl) < 3:
            R[r] = R[r - 1]; continue
        d = sl[:, :2] - np.array([0.0, cy])
        for i, t in enumerate(th):
            dirv = np.array([math.sin(t), math.cos(t)])
            proj = d @ dirv
            perp = np.abs(d[:, 0] * dirv[1] - d[:, 1] * dirv[0])
            m = perp < 0.03
            R[r, i] = proj[m].max() if m.any() else (R[r - 1, i] if r else 0.08)
    for _ in range(3):
        R[:, 1:-1] = 0.25 * R[:, :-2] + 0.5 * R[:, 1:-1] + 0.25 * R[:, 2:]
        R[1:-1] = 0.25 * R[:-2] + 0.5 * R[1:-1] + 0.25 * R[2:]
    for r in range(1, rows + 1):              # vlasy visí: pod hlavou nesmí zalézat dovnitř
        R[r] = np.maximum(R[r], R[r - 1] * 0.9)
    R += 0.014
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    vs = []
    for r, z in enumerate(zs):
        row = []
        for i, t in enumerate(th):
            row.append(bm.verts.new((R[r, i] * math.sin(t), cy + R[r, i] * math.cos(t), z)))
        vs.append(row)
    for r in range(rows):
        for i in range(N - 1):
            f = bm.faces.new((vs[r][i], vs[r][i + 1], vs[r + 1][i + 1], vs[r + 1][i]))
            for lp, (u, v) in zip(f.loops, ((i, r), (i + 1, r), (i + 1, r + 1), (i, r + 1))):
                lp[uvl].uv = (u / (N - 1), 1 - v / rows)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, c.y - cy, 0))) < 0: f.normal_flip()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    mt = bpy.data.materials.new(f"{obj.name}_rozpustene"); mt.use_nodes = True; t = mt.node_tree; bs = t.nodes["Principled BSDF"]
    uv = t.nodes.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
    mp = t.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (90.0, 1.5, 1.0); t.links.new(uv.outputs[0], mp.inputs[0])
    ns = t.nodes.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 3.0; ns.inputs["Detail"].default_value = 8
    t.links.new(mp.outputs[0], ns.inputs["Vector"])
    ramp = t.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[0].color = (*[c * 0.45 for c in color], 1)
    ramp.color_ramp.elements[1].position = 0.72; ramp.color_ramp.elements[1].color = (*[min(1, c * 1.6) for c in color], 1)
    t.links.new(ns.outputs[0], ramp.inputs[0]); t.links.new(ramp.outputs[0], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.55
    # konce pramenů: alfa = v + šum pramenů > práh
    sep = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(uv.outputs[0], sep.inputs[0])
    mp2 = t.nodes.new("ShaderNodeMapping"); mp2.inputs["Scale"].default_value = (160.0, 0.6, 1.0); t.links.new(uv.outputs[0], mp2.inputs[0])
    n2 = t.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 2.0; t.links.new(mp2.outputs[0], n2.inputs["Vector"])
    ad = t.nodes.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'
    t.links.new(sep.outputs["Y"], ad.inputs[0]); ad.inputs[1].default_value = 1.6; t.links.new(n2.outputs[0], ad.inputs[2])
    gt = t.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.62
    t.links.new(ad.outputs[0], gt.inputs[0]); t.links.new(gt.outputs[0], bs.inputs["Alpha"])
    me.materials.append(mt)
    return ob
