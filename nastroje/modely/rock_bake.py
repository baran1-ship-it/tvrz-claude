"""High-poly skála -> herní model (.glb) se zapečenými texturami.
Spuštění: python3 rock_bake.py <hi.blend> <název_bez_přípony> [tris] [tex_px] [bake_samples]
Výstup: <název>.glb + <název>_game.blend (pro náhled) do ./out
"""
import sys, os, math
import numpy as np
import bpy, bmesh
import importlib.util

SRC = sys.argv[1]
NAME = sys.argv[2]
TRIS = int(sys.argv[3]) if len(sys.argv) > 3 else 24000
PX = int(sys.argv[4]) if len(sys.argv) > 4 else 2048
BS = int(sys.argv[5]) if len(sys.argv) > 5 else 32
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)

_spec = importlib.util.spec_from_file_location("rock_mat", os.path.join(HERE, "rock_mat.py"))
rock_mat = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(rock_mat)

bpy.ops.wm.open_mainfile(filepath=SRC)
scn = bpy.context.scene
hi = bpy.data.objects["rock_hi"]
rock_mat.apply(hi)

# ---------------------------------------------------------- low-poly
lo = hi.copy(); lo.data = hi.data.copy(); lo.name = NAME
scn.collection.objects.link(lo)
for a in [a.name for a in lo.data.attributes if a.name in ("strata", "crack", "honey")]:
    lo.data.attributes.remove(lo.data.attributes[a])
lo.data.materials.clear()
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = lo; lo.select_set(True)
dec = lo.modifiers.new("dec", 'DECIMATE')
dec.ratio = TRIS / (len(hi.data.polygons) * 2 if all(len(p.vertices) == 4 for p in hi.data.polygons[:100]) else len(hi.data.polygons))
bpy.ops.object.modifier_apply(modifier="dec")
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

# unikátní UV pro celý kámen: švy navrhneme na vyhlazené kopii (málo velkých ostrovů),
# pak rozbalíme skutečný tvar podle těch švů (malé zkreslení)
proxy = lo.copy(); proxy.data = lo.data.copy(); scn.collection.objects.link(proxy)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = proxy; proxy.select_set(True)
smm = proxy.modifiers.new("sm", 'SMOOTH'); smm.factor = 1.0; smm.iterations = 80
bpy.ops.object.modifier_apply(modifier="sm")
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(48), island_margin=0.0, area_weight=0.0)
bpy.ops.uv.seams_from_islands()
bpy.ops.object.mode_set(mode='OBJECT')
seams = [e.use_seam for e in proxy.data.edges]
bpy.data.objects.remove(proxy)
for e, s in zip(lo.data.edges, seams):
    e.use_seam = s
# podstava (zaboří se do země) = samostatný ostrov se zmenšeným rozlišením
bmb = bmesh.new(); bmb.from_mesh(lo.data)
bottom = {f.index for f in bmb.faces if f.normal.z < -0.75 and f.calc_center_median().z < 0.08}
for e in bmb.edges:
    fs = [f.index in bottom for f in e.link_faces]
    if len(fs) == 2 and fs[0] != fs[1]:
        e.seam = True
bmb.to_mesh(lo.data); bmb.free()
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = lo; lo.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')
uvl = lo.data.uv_layers.active.data
idx = [li for f in lo.data.polygons if f.index in bottom for li in f.loop_indices]
if idx:
    c = sum((uvl[i].uv for i in idx), uvl[idx[0]].uv * 0) / len(idx)
    for i in idx:
        uvl[i].uv = c + (uvl[i].uv - c) * 0.2
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(margin=0.003, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
print("uv islands seams", sum(seams))
for p in lo.data.polygons:
    p.use_smooth = True
ntris = len(lo.data.polygons)
print("low tris", ntris)

# ---------------------------------------------------------- herní materiál s obrázky
def img(name, color=True):
    im = bpy.data.images.new(f"{NAME}_{name}", PX, PX, alpha=False, float_buffer=not color and name == "normal")
    im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    return im

imgs = {"basecolor": img("basecolor"), "normal": img("normal", False),
        "roughness": img("roughness", False), "ao": img("ao", False)}

gmat = bpy.data.materials.new(f"game_{NAME}"); gmat.use_nodes = True
gt = gmat.node_tree; gt.nodes.clear()
gout = gt.nodes.new("ShaderNodeOutputMaterial"); gout.location = (900, 0)
gb = gt.nodes.new("ShaderNodeBsdfPrincipled"); gb.location = (600, 0)
gt.links.new(gb.outputs[0], gout.inputs[0])
tex = {}
for i, (k, im) in enumerate(imgs.items()):
    t = gt.nodes.new("ShaderNodeTexImage"); t.image = im; t.location = (-400, 300 - i * 300)
    tex[k] = t
lo.data.materials.append(gmat)

# ---------------------------------------------------------- bake hi -> lo
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'
scn.cycles.samples = BS
bk = scn.render.bake
bk.use_selected_to_active = True
bk.use_cage = False
_f = min(1.0, max(hi.dimensions) / 2.6)
bk.cage_extrusion = 0.04 * _f
bk.max_ray_distance = 0.08 * _f
bk.margin = 12
bpy.ops.object.select_all(action='DESELECT')
hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo

def bake(kind, key, **kw):
    for n in gt.nodes: n.select = False
    tex[key].select = True; gt.nodes.active = tex[key]
    bpy.ops.object.bake(type=kind, **kw)
    path = os.path.join(OUT, f"{NAME}_{key}.png")
    imgs[key].filepath_raw = path; imgs[key].file_format = 'PNG'; imgs[key].save()
    print("baked", key)

# AO uzel v materiálu potřebuje vzorky; barva bez světla
scn.cycles.samples = 8
bake('DIFFUSE', "basecolor", pass_filter={'COLOR'})
bake('ROUGHNESS', "roughness")
scn.render.bake.normal_space = 'TANGENT'   # Blender = OpenGL (Y+), jak chce zadání
bake('NORMAL', "normal")
scn.cycles.samples = max(BS, 48)
hi_hide = hi.hide_render
bake('AO', "ao")

# zapojení obrázků
gt.links.new(tex["basecolor"].outputs[0], gb.inputs["Base Color"])
gt.links.new(tex["roughness"].outputs[0], gb.inputs["Roughness"])
nm = gt.nodes.new("ShaderNodeNormalMap"); nm.location = (200, -400)
gt.links.new(tex["normal"].outputs[0], nm.inputs["Color"]); gt.links.new(nm.outputs[0], gb.inputs["Normal"])
gb.inputs["Metallic"].default_value = 0.0
# AO pro glTF exportér (skupina "glTF Material Output")
grp = bpy.data.node_groups.get("glTF Material Output") or bpy.data.node_groups.new("glTF Material Output", 'ShaderNodeTree')
if "Occlusion" not in [i.name for i in grp.interface.items_tree]:
    grp.interface.new_socket("Occlusion", in_out='INPUT', socket_type='NodeSocketFloat')
gg = gt.nodes.new("ShaderNodeGroup"); gg.node_tree = grp; gg.location = (600, -500)
sepc = gt.nodes.new("ShaderNodeSeparateColor"); sepc.location = (200, -650)
gt.links.new(tex["ao"].outputs[0], sepc.inputs[0]); gt.links.new(sepc.outputs[0], gg.inputs["Occlusion"])
for k in ("normal", "roughness", "ao"):
    tex[k].image.colorspace_settings.name = 'Non-Color'

# ---------------------------------------------------------- pivot dole uprostřed, transformace
bpy.data.objects.remove(hi)
co = np.empty(len(lo.data.vertices) * 3); lo.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
cx, cy = (co[:, 0].max() + co[:, 0].min()) / 2, (co[:, 1].max() + co[:, 1].min()) / 2
co[:, 0] -= cx; co[:, 1] -= cy          # z = 0 už je rovina podstavy
lo.data.vertices.foreach_set("co", co.ravel()); lo.data.update()
lo.location = (0, 0, 0); lo.rotation_euler = (0, 0, 0); lo.scale = (1, 1, 1)
dims = lo.dimensions.copy()

for im in imgs.values():
    im.pack()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{NAME}_game.blend"))

bpy.ops.object.select_all(action='DESELECT'); lo.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"{NAME}.glb"), export_format='GLB',
                          use_selection=True, export_yup=True, export_apply=True,
                          export_image_format='JPEG', export_jpeg_quality=92,
                          export_cameras=False, export_lights=False, export_animations=False)
print(f"RESULT {NAME} tris={ntris} dims_m(sxvxh)={dims.x:.2f} x {dims.z:.2f} x {dims.y:.2f}")
