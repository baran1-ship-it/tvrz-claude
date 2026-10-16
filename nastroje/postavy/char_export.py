"""Herní export postavy: smazání skrytých částí, sloučení do 3 materiálů (kůže, oblečení, vlasy),
zapečení procedurálních materiálů do textur (2K/1K), skinned .glb s kostrou game_engine.
python3 char_export.py <jmeno> <kroj> <vystup.glb>
"""
import sys, os, math
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy, bmesh, numpy as np
from mathutils import Vector

NAME, KROJ, OUTGLB = sys.argv[1], sys.argv[2], sys.argv[3]
TEX = os.path.join(os.path.dirname(OUTGLB), "tex_" + NAME); os.makedirs(TEX, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=f"/home/claude/chars/{NAME}_{KROJ}.blend")
scn = bpy.context.scene
rig = bpy.data.objects[f"{NAME}.rig"]
body = bpy.data.objects[NAME]
eyes = bpy.data.objects.get(f"{NAME}.high-poly")
hair = bpy.data.objects.get(f"{NAME}_vlasy")
hair_extra = [o for o in (bpy.data.objects.get(f"{NAME}_cop"), bpy.data.objects.get(f"{NAME}_rozpustene")) if o]
hair_extra += [o for o in bpy.data.objects if o.type == 'MESH' and "eyelash" in o.name.lower()]
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
if rig.animation_data: rig.animation_data.action = None

def sel_only(objs, active=None):
    bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.object and bpy.context.object.mode != 'OBJECT' else None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]

def gw(obj, name):
    w = np.zeros(len(obj.data.vertices))
    if name not in obj.vertex_groups: return w
    gi = obj.vertex_groups[name].index
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group == gi: w[v.index] = g.weight
    return w

# tvarové klíče (MPFB targety) zapéct do sítě
sel_only([body])
if body.data.shape_keys:
    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
# --- 1) tělo: smazat pomocnou geometrii a části pod oblečením (podle MASK modifikátorů)
keep = np.ones(len(body.data.vertices), bool)
for m in list(body.modifiers):
    if m.type == 'MASK':
        w = gw(body, m.vertex_group) > 0.5
        keep &= (~w) if m.invert_vertex_group else w
        body.modifiers.remove(m)
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.where(~keep)[0]], context='VERTS')
bm.to_mesh(body.data); bm.free()
print("BODY faces", len(body.data.polygons))

# --- 2) vlasy: váha na hlavu + armatura
if hair:
    hair.parent = rig; hair.matrix_parent_inverse.identity()
    if not hair.vertex_groups:
        g = hair.vertex_groups.new(name="head"); g.add(list(range(len(hair.data.vertices))), 1.0, 'REPLACE')
    md = hair.modifiers.new("Armature", 'ARMATURE'); md.object = rig
    hair.hide_render = False

# --- 3) obrázkové uzly bez UV vstupu dostanou explicitní UV (při zapékání bude aktivní jiná UV)
def pin_uv(obj):
    for m in obj.data.materials:
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type == 'TEX_IMAGE' and not n.inputs["Vector"].links:
                u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = obj.data.uv_layers[0].name
                nt.links.new(u.outputs[0], n.inputs["Vector"])
for o in [body, eyes, hair] + [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(NAME + "_")]:
    if o: pin_uv(o)

# --- 3b) kapuce nesmí protínat hlavu (uši): odsunout ven od kůže
def push_out(gar, src, gname, gap):
    from mathutils.kdtree import KDTree
    gi = src.vertex_groups.get(gname)
    if not gi: return
    idx = [v.index for v in src.data.vertices if any(g.group == gi.index and g.weight > 0.3 for g in v.groups)]
    kd = KDTree(len(idx))
    for k, i in enumerate(idx): kd.insert(src.data.vertices[i].co, k)
    kd.balance(); moved = 0
    for v in gar.data.vertices:
        co, k, d = kd.find(v.co)
        if d > 0.03: continue
        bv = src.data.vertices[idx[k]]; n = bv.normal
        depth = (v.co - bv.co).dot(n)
        if depth < gap:
            v.co += n * (gap - depth); moved += 1
    print("PUSH", gar.name, gname, moved)
for hn in (f"{NAME}_kapuce",):
    ho = bpy.data.objects.get(hn)
    if ho and body:
        push_out(ho, body, "head", 0.006)
        push_out(ho, body, "neck_01", 0.004)

# --- 4) skupiny pro zapékání
garments = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(NAME + "_") and o is not hair and o not in hair_extra]
hood_names = {f"{NAME}_kapuce", f"{NAME}_plastik"}
for o in garments:
    g = o.vertex_groups.new(name="_cast_kapuce" if o.name in hood_names else "_cast_obleceni")
    g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    # sjednotit název UV vrstvy (join páruje UV podle názvu)
    o.data.uv_layers[0].name = "UVMap"

def join(objs, name):
    sel_only(objs); bpy.ops.object.join(); o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    return o

telo = join([body] + ([eyes] if eyes else []), f"{NAME}_telo")
obl = join(garments, f"{NAME}_obleceni")

def new_bake_uv(obj, mode, head_scale=1.0):
    uv = obj.data.uv_layers.new(name="bake")
    obj.data.uv_layers.active = uv
    sel_only([obj]); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    if mode == "smart":
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003, area_weight=0.0)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    if head_scale != 1.0:
        # zvětšit ostrovy hlavy/obličeje (víc pixelů na obličej)
        hw = gw(obj, "head") + gw(obj, "neck_01")
        me = obj.data; uvd = uv.data
        bmx = bmesh.new(); bmx.from_mesh(me); ul = bmx.loops.layers.uv["bake"]
        bmx.faces.ensure_lookup_table()
        # ostrovy přes spojité UV
        seen = set()
        for f in bmx.faces:
            if f.index in seen: continue
            isl = []; st = [f]; seen.add(f.index)
            while st:
                g = st.pop(); isl.append(g)
                for e in g.edges:
                    if e.seam: continue
                    for h in e.link_faces:
                        if h.index in seen: continue
                        # sdílí UV na hraně?
                        a = [l[ul].uv.copy() for l in g.loops if l.vert in e.verts]
                        b = [l[ul].uv.copy() for l in h.loops if l.vert in e.verts]
                        if len(a) == 2 and len(b) == 2 and min((a[0] - b[0]).length + (a[1] - b[1]).length, (a[0] - b[1]).length + (a[1] - b[0]).length) < 1e-5:
                            seen.add(h.index); st.append(h)
            hv = np.mean([hw[v.index] for g in isl for v in g.verts])
            if hv > 0.5:
                c = sum((l[ul].uv for g in isl for l in g.loops), Vector((0, 0))) / sum(len(g.loops) for g in isl)
                for g in isl:
                    for l in g.loops: l[ul].uv = c + (l[ul].uv - c) * head_scale
        bmx.to_mesh(me); bmx.free()
    sel_only([obj]); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True, scale=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    # render UV pro zapékání = bake
    for u in obj.data.uv_layers: u.active_render = (u.name == "bake")

def decimate(obj, target_tris, unsub=0):
    if unsub:
        sel_only([obj]); md = obj.modifiers.new("uns", 'DECIMATE'); md.decimate_type = 'UNSUBDIV'; md.iterations = unsub
        while obj.modifiers.find("uns") > 0: bpy.ops.object.modifier_move_up(modifier="uns")
        bpy.ops.object.modifier_apply(modifier="uns")
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    if tris <= target_tris: return
    sel_only([obj]); md = obj.modifiers.new("dec", 'DECIMATE'); md.ratio = target_tris / tris
    # dekcimace musí být před armaturou
    while obj.modifiers.find("dec") > 0: bpy.ops.object.modifier_move_up(modifier="dec")
    bpy.ops.object.modifier_apply(modifier="dec")
    print("DECIMATE", obj.name, tris, "->", sum(len(p.vertices) - 2 for p in obj.data.polygons))
def thin_islands(obj, keep_every):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    seen = set(); kill = []; n = 0
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; comp = []
        while st:
            x = st.pop()
            if x.index in seen: continue
            seen.add(x.index); comp.append(x); st.extend(e.other_vert(x) for e in x.link_edges)
        if n % keep_every: kill += comp
        n += 1
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(obj.data); bm.free()
    print("THIN", obj.name, n, "->", (n + keep_every - 1) // keep_every)
# vlasové části: váhy (rozpuštěné z těla), značky, sloučení pro jeden atlas
if hair and hair_extra:
    import clothes as _cl
    co_b = np.array([v.co[:] for v in telo.data.vertices])
    for o in hair_extra:
        if not o.vertex_groups:
            _cl.transfer_weights(o, telo, co_b, k=8)
        o.parent = rig; o.matrix_parent_inverse.identity()
        if not any(m.type == 'ARMATURE' for m in o.modifiers):
            md = o.modifiers.new("Armature", 'ARMATURE'); md.object = rig
        o.data.uv_layers[0].name = "UVMap"
    for o in [hair] + hair_extra:
        g = o.vertex_groups.new(name="_cast_" + o.name.replace(NAME + "_", "")); g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    hair.data.uv_layers[0].name = "UVMap"
    for o in [hair] + hair_extra:
        print("HAIRPART", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons))
        if "eyelash" in o.name.lower():
            thin_islands(o, 3); decimate(o, 4000)
        elif o is not hair: decimate(o, 3500)
    hair = join([hair] + hair_extra, f"{NAME}_vlasy")
decimate(telo, 11500); decimate(obl, 12500)
pass
new_bake_uv(telo, "keep", head_scale=2.4)
new_bake_uv(obl, "smart")
if hair: new_bake_uv(hair, "smart")

# --- 5) zapékání
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 8
scn.render.bake.margin = 8
def bake_set(obj, px, tag, alpha=False):
    imgs = {}
    for k in ("color", "normal", "rough") + (("alpha",) if alpha else ()):
        im = bpy.data.images.new(f"{obj.name}_{k}", px, px, alpha=False)
        im.colorspace_settings.name = 'sRGB' if k == "color" else 'Non-Color'
        imgs[k] = im
    mats = [m for m in obj.data.materials if m]
    def put(k):
        for m in mats:
            nt = m.node_tree
            n = nt.nodes.get("_bake") or nt.nodes.new("ShaderNodeTexImage"); n.name = "_bake"
            n.image = imgs[k]
            for x in nt.nodes: x.select = False
            n.select = True; nt.nodes.active = n
    sel_only([obj])
    put("color"); bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
    put("rough"); bpy.ops.object.bake(type='ROUGHNESS')
    scn.render.bake.normal_space = 'TANGENT'
    put("normal"); bpy.ops.object.bake(type='NORMAL')
    if alpha:
        # alfa -> emise (dočasně)
        saved = []
        for m in mats:
            nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
            b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            em = nt.nodes.new("ShaderNodeEmission")
            if b and b.inputs["Alpha"].links: nt.links.new(b.inputs["Alpha"].links[0].from_socket, em.inputs["Color"])
            else: em.inputs["Color"].default_value = (1, 1, 1, 1)
            old = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
            nt.links.new(em.outputs[0], out.inputs["Surface"]); saved.append((nt, out, old, em))
        put("alpha"); bpy.ops.object.bake(type='EMIT')
        for nt, out, old, em in saved:
            if old: nt.links.new(old, out.inputs["Surface"])
            nt.nodes.remove(em)
    for k, im in imgs.items():
        im.filepath_raw = os.path.join(TEX, f"{obj.name}_{k}.png"); im.file_format = 'PNG'; im.save()
    print("BAKED", obj.name)
    return imgs

def game_mat(obj, imgs, name, alpha=False):
    from PIL import Image as PI
    col = PI.open(imgs["color"].filepath_raw).convert("RGB")
    if alpha:
        a = PI.open(imgs["alpha"].filepath_raw).convert("L")
        col.putalpha(a); cpath = os.path.join(TEX, f"{name}_barva.png"); col.save(cpath)
    else:
        cpath = os.path.join(TEX, f"{name}_barva.jpg"); col.save(cpath, quality=92)
    npath = os.path.join(TEX, f"{name}_normal.jpg"); PI.open(imgs["normal"].filepath_raw).convert("RGB").save(npath, quality=92)
    r = PI.open(imgs["rough"].filepath_raw).convert("L")
    import numpy as _n
    rr = _n.asarray(r); orm = PI.fromarray(_n.dstack([_n.full_like(rr, 255), rr, _n.zeros_like(rr)]))
    rpath = os.path.join(TEX, f"{name}_drsnost.jpg"); orm.save(rpath, quality=92)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs[0])
    uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "bake"
    def tex(p, cs):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(p); t.image.colorspace_settings.name = cs
        nt.links.new(uv.outputs[0], t.inputs["Vector"]); return t
    tc = tex(cpath, 'sRGB'); nt.links.new(tc.outputs["Color"], b.inputs["Base Color"])
    if alpha:
        nt.links.new(tc.outputs["Alpha"], b.inputs["Alpha"])
        m.blend_method = 'CLIP' if hasattr(m, "blend_method") else None
    tn = tex(npath, 'Non-Color'); nm = nt.nodes.new("ShaderNodeNormalMap"); nm.uv_map = "bake"
    nt.links.new(tn.outputs[0], nm.inputs["Color"]); nt.links.new(nm.outputs[0], b.inputs["Normal"])
    tr = tex(rpath, 'Non-Color'); sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(tr.outputs[0], sp.inputs[0])
    nt.links.new(sp.outputs[1], b.inputs["Roughness"]); nt.links.new(sp.outputs[2], b.inputs["Metallic"])
    m.use_backface_culling = not alpha
    obj.data.materials.clear(); obj.data.materials.append(m)
    # jen UV 'bake' (přejmenovat na UVMap), ostatní pryč
    for u in [u for u in obj.data.uv_layers if u.name != "bake"]: obj.data.uv_layers.remove(u)
    obj.data.uv_layers["bake"].name = "UVMap"; uv.uv_map = "UVMap"; nm.uv_map = "UVMap"
    return m

it = bake_set(telo, 2048, "kuze"); game_mat(telo, it, f"{NAME}_kuze")
io = bake_set(obl, 2048, "obleceni", alpha=True); mo = game_mat(obl, io, f"{NAME}_obleceni", alpha=True)
if hair:
    ih = bake_set(hair, 1024 if not hair_extra else 2048, "vlasy", alpha=True); game_mat(hair, ih, f"{NAME}_vlasy", alpha=True)
    for part in ("cop", "rozpustene"):
        gname = "_cast_" + part
        if gname in hair.vertex_groups:
            sel_only([hair]); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
            hair.vertex_groups.active_index = hair.vertex_groups[gname].index
            bpy.ops.object.vertex_group_select(); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
            newo = [o for o in bpy.context.selected_objects if o is not hair][0]; newo.name = f"{NAME}_{part}"
# kapuci oddělit (hra ji může skrýt)
sel_only([obl]); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
if "_cast_kapuce" in obl.vertex_groups:
    obl.vertex_groups.active_index = obl.vertex_groups["_cast_kapuce"].index
    bpy.ops.object.vertex_group_select(); bpy.ops.mesh.separate(type='SELECTED')
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(f"{NAME}_obleceni") and o is not obl: o.name = f"{NAME}_kapuce"
for o in bpy.data.objects:
    if o.type == 'MESH':
        for g in [g for g in o.vertex_groups if g.name.startswith("_cast")]: o.vertex_groups.remove(g)
        for a in [a.name for a in o.data.attributes if a.name in ("fotomaska", "edge", "hem", "src")]:
            try: o.data.attributes.remove(o.data.attributes[a])
            except Exception: pass
        for p in o.data.polygons: p.use_smooth = True
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
tris = sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons)
print("MESHES", [o.name for o in meshes], "TRIS", tris)
bpy.ops.wm.save_as_mainfile(filepath=OUTGLB.replace(".glb", "_export.blend"))
sel_only(meshes + [rig], rig)
bpy.ops.export_scene.gltf(filepath=OUTGLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                          export_skins=True, export_animations=False, export_image_format='AUTO', export_cameras=False,
                          export_lights=False, export_morph=False)
print("EXPORTED", OUTGLB, round(os.path.getsize(OUTGLB) / 1e6, 1), "MB", "dims", tuple(round(x, 2) for x in rig.dimensions))
