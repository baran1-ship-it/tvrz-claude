# Oblékne Quaternius Superhero_Male: oblasti podle vah kostí -> košile / kalhoty / boty / kůže, fotoskenové látky Poly Haven
import bpy, bmesh, sys, os
from mathutils import Vector
SRC, OUT, TEX = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT') or o.name in ('Cube', 'Icosphere'):
        bpy.data.objects.remove(o, do_unlink=True)
body = bpy.data.objects['SuperHero_Male']
REG = {}
for n in ['spine_01', 'spine_02', 'spine_03', 'clavicle_l', 'clavicle_r', 'upperarm_l', 'upperarm_r', 'lowerarm_l', 'lowerarm_r']: REG[n] = 'kosile'
for n in ['pelvis', 'thigh_l', 'thigh_r', 'calf_l', 'calf_r']: REG[n] = 'kalhoty'
for n in ['foot_l', 'foot_r', 'ball_l', 'ball_r']: REG[n] = 'boty'
gname = {g.index: g.name for g in body.vertex_groups}
me = body.data
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
W = arm.matrix_world; BI = body.matrix_world.inverted(); B = arm.data.bones
hw = lambda n: W @ B[n].head_local
up = Vector((0, 0, 1))
PL = {'waist': (hw('spine_01') + Vector((0, 0, .015)), up), 'neck': (hw('neck_01') + Vector((0, 0, .015)), up)}
for sd in 'lr':
    a, h = hw('lowerarm_' + sd), hw('hand_' + sd); dn = (h - a).normalized(); PL['wrist_' + sd] = (h - dn * .025, dn)
    PL['ankle_' + sd] = (hw('foot_' + sd) + Vector((0, 0, .07)), up)
bm = bmesh.new(); bm.from_mesh(me)
for k, (co, no) in PL.items():
    lc = BI @ co; ln = (BI.to_3x3() @ no).normalized()
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=lc, plane_no=ln)
bm.to_mesh(me); bm.free(); me.update()
gname = {g.index: g.name for g in body.vertex_groups}
def dom(v):
    best, bw = None, 0
    for g in v.groups:
        if g.weight > bw: bw, best = g.weight, gname[g.group]
    return best
vd = [dom(v) for v in me.vertices]
def side(k, p):
    co, no = PL[k]; return (p - co).dot(no)
def region(p):
    cnt = {}
    for vi in p.vertices: cnt[vd[vi]] = cnt.get(vd[vi], 0) + 1
    b = max(cnt, key=cnt.get) or ''; c = body.matrix_world @ p.center
    for sd in 'lr':
        if b.endswith('_' + sd) and (b.startswith(('upperarm', 'lowerarm', 'hand', 'index', 'middle', 'ring', 'pinky', 'thumb'))):
            return 'kosile' if side('wrist_' + sd, c) < 0 else 'kuze'
        if b.endswith('_' + sd) and b.startswith(('thigh', 'calf', 'foot', 'ball')):
            return 'boty' if side('ankle_' + sd, c) < 0 else 'kalhoty'
    if b in ('neck_01', 'Head'):
        return 'kuze' if side('neck', c) > 0 else 'kosile'
    if b.startswith(('spine', 'clavicle', 'pelvis')):
        nk = hw('neck_01')
        if side('neck', c) > 0 and Vector((c.x - nk.x, c.y - nk.y)).length < .085: return 'kuze'
        return 'kosile' if side('waist', c) > 0 else 'kalhoty'
    return 'kuze'
# zápěstí: konec předloktí blízko ruky nechat jako manžetu košile, ruka zůstane kůží; krk nad límcem kůže
mats = {}
def mat(name, base, col, rep):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (rep, rep, rep)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    def img(f, cs):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(TEX, f)); t.image.colorspace_settings.name = cs; nt.links.new(mp.outputs['Vector'], t.inputs['Vector']); return t
    d = img(base + '_diff.jpg', 'sRGB')
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
    mix.inputs[7].default_value = col; nt.links.new(d.outputs['Color'], mix.inputs[6]); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    r = img(base + '_rough.jpg', 'Non-Color'); nt.links.new(r.outputs['Color'], b.inputs['Roughness'])
    n = img(base + '_nor.jpg', 'Non-Color'); nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Metallic'].default_value = 0.0
    return m
M = {'kosile': mat('kosile', 'knitted_fleece', (0.36, 0.40, 0.28, 1), 6.0),
     'kalhoty': mat('kalhoty', 'ribbed_corduroy', (0.36, 0.30, 0.22, 1), 5.0),
     'boty': mat('boty', 'brown_leather', (0.5, 0.38, 0.28, 1), 3.0)}
for k, m in M.items(): me.materials.append(m)
idx = {k: i + 1 for i, k in enumerate(M)}
for p in me.polygons:
    r = region(p)
    if r != 'kuze': p.material_index = idx[r]
# oddělit oblečení do vlastních objektů, nové UV (Smart UV), lehce nafouknout mimo okraje
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
INF = {'kosile': .016, 'kalhoty': .018, 'boty': .014}
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('SuperHero_Male')]:
    mname = o.data.materials[o.data.polygons[0].material_index].name if o.data.polygons else ''
    if mname not in M:
        o.name = 'telo'; continue
    o.name = mname
    # odstranit nepoužité sloty materiálu
    keep = o.data.materials[o.data.polygons[0].material_index]
    o.data.materials.clear(); o.data.materials.append(keep)
    for p in o.data.polygons: p.material_index = 0
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    # nová UV mapa pro látku
    while len(o.data.uv_layers) > 0: o.data.uv_layers.remove(o.data.uv_layers[0])
    o.data.uv_layers.new(name='UVMap')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.01, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
    edge_v = {v for e in bm.edges if e.is_boundary for v in e.verts}
    inner = [v for v in bm.verts if v not in edge_v]
    for _ in range(8): bmesh.ops.smooth_vert(bm, verts=inner, factor=.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.normal_update()
    d = INF[mname]
    for v in bm.verts:
        k = 0.35 if v in edge_v else 1.0
        v.co += v.normal * d * k
    bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=False, export_skins=True, export_image_format='JPEG', export_jpeg_quality=86, use_selection=False)
print('DONE', [o.name for o in bpy.data.objects])
