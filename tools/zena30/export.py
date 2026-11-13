"""Export pro Godot: postava (glb, kostra + díly) a knihovna animací (glb, všechny zapečené animace).
Měřítko 0.94 (výška ~1,66 m) jako transformace uzlu kostry – animace UAL sedí beze změny."""
import sys, json; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import numpy as np, bmesh
from mathutils import Vector
SRC = sys.argv[sys.argv.index("--") + 1]; OUTD = sys.argv[sys.argv.index("--") + 2]
os.makedirs(OUTD, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects["zena30_kostra"]
SCALE = 0.94
# --- košile: pod živůtkem neviditelná -> pryč (zůstane výstřih a předloktí)
kos = bpy.data.objects["zena30_kosile"]
bm = bmesh.new(); bm.from_mesh(kos.data)
def hidden(v):
    c = v.co; ax = abs(c.x)
    if ax > 0.36: return False                      # rukáv pod loktem viditelný
    nz_front = 1.345 + 0.115 * (c.x / 0.11) ** 2 - 0.03
    if c.y < 0.03 and c.z > nz_front: return False  # výstřih
    if c.y >= 0.03 and c.z > 1.40 + 0.05 * (c.x / 0.11) ** 2: return False
    return c.z > 0.86
kill = [f for f in bm.faces if all(hidden(v) for v in f.verts)]
bmesh.ops.delete(bm, geom=kill, context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(kos.data); bm.free()
# --- UV látek: hustota vazby (vlna ~4 mm, len ~1,6 mm)
import cloth
for nm in ("zena30_kosile", "zena30_zivutek", "zena30_sukne", "zena30_zastera", "zena30_opasek", "zena30_boty"):
    o = bpy.data.objects[nm]; mat = o.data.materials[0]
    tm = mat.get("tile_m", 0.06) * float(os.environ.get("TILE_K", "2.5"))
    cloth.triplanar_uv(o, tm, (lambda c: 'x' if abs(c.x) > 0.17 and c.z > 1.3 else 'z') if nm in ("zena30_kosile", "zena30_zivutek") else None)
# --- mrkání a oči jako samostatné uzly (postava_oci.gd v Tvrzi je natáčí a mrká)
import q_oci
body = bpy.data.objects["zena30_telo"]; brows = bpy.data.objects["zena30_obocí"]; eyes = bpy.data.objects["zena30_oci"]
lm = np.array([(brows.matrix_world @ v.co).z < 1.668 for v in brows.data.vertices])
q_oci.add_blink(body, brows, eyes, lm)
brows.name = "zena30_oboci"
# --- zástěra o kus dál od sukně (žádné z-fighting na tabletu); váhy podle úhlu a výšky se nemění
ap = bpy.data.objects["zena30_zastera"]
G = np.load("/home/claude/z30/skirt_grid.npz"); CEN = G["CEN"]
for v in ap.data.vertices:
    d = Vector((v.co.x - CEN[0], v.co.y - CEN[1], 0))
    if d.length > 1e-6: v.co += d.normalized() * float(os.environ.get("APRON_OFF", "0.009"))
# --- punčochy: uzavřít horní okraj (ať není vidět dutá trubka, když se sukně zvedne)
body = bpy.data.objects["zena30_telo"]
bm = bmesh.new(); bm.from_mesh(body.data)
uvl = bm.loops.layers.uv.active
allb = [e for e in bm.edges if e.is_boundary]; seen = set(); bnd = []
for e in allb:
    if e in seen: continue
    comp = []; st = [e]; seen.add(e)
    while st:
        x = st.pop(); comp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen: seen.add(y); st.append(y)
    zc = np.mean([v.co.z for x in comp for v in x.verts]); xc = np.mean([v.co.x for x in comp for v in x.verts])
    if 0.15 < zc < 0.45 and abs(xc) < 0.3: bnd += comp
res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
for f in res["faces"]:
    ref = None
    for l in f.loops:
        for l2 in l.vert.link_loops:
            if l2.face is not f: ref = l2[uvl].uv.copy(); break
        if ref: break
    for l in f.loops: l[uvl].uv = ref
    f.smooth = True
print("UZAVRENO", len(res["faces"]))
bm.to_mesh(body.data); bm.free()
# --- decimace vlasů (chomáče) a slupek
def decimate(name, ratio):
    o = bpy.data.objects[name]; md = o.modifiers.new("dec", 'DECIMATE'); md.ratio = ratio
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        if m.type == 'ARMATURE': o.modifiers.move(o.modifiers.find(m.name), len(o.modifiers) - 1)
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier="dec")
decimate("zena30_vlasy", float(os.environ.get("HAIR_DEC", "0.6")))
decimate("zena30_zivutek", 0.7); decimate("zena30_boty", 0.6)
# zástěra/sukně/opasek: trojúhelníky necháme (jemná síť kvůli ohybům látky)
# --- akce: jen zapečené UAL (bez duplikátů a T-pózy)
keep = [a for a in bpy.data.actions if a.use_fake_user and not a.name.endswith(".001") and a.name not in ("A_TPose",)]
for a in list(bpy.data.actions):
    if a not in keep: bpy.data.actions.remove(a)
print("akcí", len(keep))
tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'}
print("TROJ", tris, sum(tris.values()))
json.dump(dict(trojuhelniky=tris, celkem=sum(tris.values()), animace=sorted(a.name for a in keep)), open(f"{OUTD}/_info.json", "w"), indent=1, ensure_ascii=False)
arm.scale = (SCALE,) * 3
arm.name = "Armature"; arm.data.name = "Armature"
for o in bpy.data.objects: o.select_set(o.type in ('MESH', 'ARMATURE'))
common = dict(export_format='GLB', use_selection=True, export_yup=True, export_apply=False, export_skins=True,
              export_image_format='AUTO', export_texcoords=True, export_normals=True, export_materials='EXPORT')
# 1) postava bez animací
bpy.ops.export_scene.gltf(filepath=f"{OUTD}/zena30.glb", export_animations=False, **common)
# 2) animace: jen kostra
for o in bpy.data.objects: o.select_set(o.type == 'ARMATURE')
arm.animation_data_create()
bpy.ops.export_scene.gltf(filepath=f"{OUTD}/zena30_animace.glb", export_animations=True, export_animation_mode='ACTIONS',
                          export_force_sampling=True, export_frame_step=1, export_def_bones=False,
                          export_optimize_animation_size=True, export_anim_single_armature=True,
                          **{k: v for k, v in common.items() if k != 'export_materials'}, export_materials='NONE')
print("HOTOVO")
