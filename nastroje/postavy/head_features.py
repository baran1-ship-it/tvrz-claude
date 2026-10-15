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
        hl_front = Ez + 0.074 + 0.016 * np.exp(-((ax - 0.045) / 0.022) ** 2)
        side = Ez - 0.03          # kotlety před uchem
        back = L["neck"].z + 0.06
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
        f = np.minimum(f, d - 0.043)
    return f

def hair_shell(obj, L, style, color, name="vlasy"):
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
        off = (0.0025 + 0.0045 * h) if style == "muz" else (0.003 + 0.017 * max(h, 0) ** 1.5)
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
    t.links.new(ns.outputs[0], ramp.inputs[0]); t.links.new(ramp.outputs[0], b.inputs["Base Color"])
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
