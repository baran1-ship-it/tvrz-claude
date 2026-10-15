"""Zapečení procedurálního materiálu vozu do textur na vlastní UV a export .glb.
Spuštění: python3 wagon_bake.py <hi.blend> <název> [px] [samples]
"""
import sys, os
import bpy
import importlib.util

SRC, NAME = sys.argv[1], sys.argv[2]
PX = int(sys.argv[3]) if len(sys.argv) > 3 else 2048
BS = int(sys.argv[4]) if len(sys.argv) > 4 else 8
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
_s = importlib.util.spec_from_file_location("wagon_mat", os.path.join(HERE, "wagon_mat.py"))
wagon_mat = importlib.util.module_from_spec(_s); _s.loader.exec_module(wagon_mat)

bpy.ops.wm.open_mainfile(filepath=SRC)
scn = bpy.context.scene
ob = bpy.data.objects["wagon"]
ob.name = NAME
mat = (wagon_mat.apply_log if ob.get("kind") == "log" else wagon_mat.apply)(ob)
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
outn = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')

imgs = {}
for k, color in (("basecolor", True), ("normal", False), ("roughness", False), ("metallic", False), ("ao", False)):
    im = bpy.data.images.new(f"{NAME}_{k}", PX, PX, alpha=False)
    im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    imgs[k] = im
tex = nt.nodes.new("ShaderNodeTexImage"); tex.location = (1600, 600)

scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = BS
scn.render.bake.use_selected_to_active = False
scn.render.bake.margin = 6
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
bpy.context.view_layer.objects.active = ob

def bake(kind, key, **kw):
    tex.image = imgs[key]
    for n in nt.nodes: n.select = False
    tex.select = True; nt.nodes.active = tex
    bpy.ops.object.bake(type=kind, **kw)
    imgs[key].filepath_raw = os.path.join(OUT, f"{NAME}_{key}.png"); imgs[key].file_format = 'PNG'
    imgs[key].save(); print("baked", key, flush=True)

bake('DIFFUSE', "basecolor", pass_filter={'COLOR'})
bake('ROUGHNESS', "roughness")
scn.render.bake.normal_space = 'TANGENT'
bake('NORMAL', "normal")
# metalicita přes emisi
met_src = bsdf.inputs["Metallic"].links[0].from_socket if bsdf.inputs["Metallic"].links else None
em = nt.nodes.new("ShaderNodeEmission")
if met_src is not None: nt.links.new(met_src, em.inputs["Color"])
else: em.inputs["Color"].default_value = (0, 0, 0, 1)
old = outn.inputs["Surface"].links[0].from_socket
nt.links.new(em.outputs[0], outn.inputs["Surface"])
bake('EMIT', "metallic")
nt.links.new(old, outn.inputs["Surface"])
scn.cycles.samples = max(BS, 48)
bake('AO', "ao")

# herní materiál jen z obrázků
g = bpy.data.materials.new(f"game_{NAME}"); g.use_nodes = True
gt = g.node_tree; gt.nodes.clear()
go = gt.nodes.new("ShaderNodeOutputMaterial"); gb = gt.nodes.new("ShaderNodeBsdfPrincipled")
gt.links.new(gb.outputs[0], go.inputs[0])
T = {}
for k, im in imgs.items():
    t = gt.nodes.new("ShaderNodeTexImage"); t.image = im; T[k] = t
    if k != "basecolor": im.colorspace_settings.name = 'Non-Color'
gt.links.new(T["basecolor"].outputs[0], gb.inputs["Base Color"])
gt.links.new(T["roughness"].outputs[0], gb.inputs["Roughness"])
gt.links.new(T["metallic"].outputs[0], gb.inputs["Metallic"])
nm = gt.nodes.new("ShaderNodeNormalMap"); gt.links.new(T["normal"].outputs[0], nm.inputs["Color"])
gt.links.new(nm.outputs[0], gb.inputs["Normal"])
grp = bpy.data.node_groups.get("glTF Material Output") or bpy.data.node_groups.new("glTF Material Output", 'ShaderNodeTree')
if "Occlusion" not in [i.name for i in grp.interface.items_tree]:
    grp.interface.new_socket("Occlusion", in_out='INPUT', socket_type='NodeSocketFloat')
gg = gt.nodes.new("ShaderNodeGroup"); gg.node_tree = grp
sc = gt.nodes.new("ShaderNodeSeparateColor"); gt.links.new(T["ao"].outputs[0], sc.inputs[0])
gt.links.new(sc.outputs[0], gg.inputs["Occlusion"])
ob.data.materials.clear(); ob.data.materials.append(g)
# atributy pro procedurál už nejsou potřeba
for a in [a.name for a in ob.data.attributes if a.name in ("lp", "wl", "wd", "pid", "age", "metal", "wheel", "handled", "fresh", "rust_near", "bark", "rad", "fung")]:
    ob.data.attributes.remove(ob.data.attributes[a])
for im in imgs.values(): im.pack()

# ---- plachta: vlastní sada textur
cv = bpy.data.objects.get("plachta")
if cv is not None:
    cmat = wagon_mat.apply_canvas(cv)
    cn = cmat.node_tree
    cb = next(n for n in cn.nodes if n.type == 'BSDF_PRINCIPLED')
    cim = {}
    for k, color in (("basecolor", True), ("normal", False), ("roughness", False), ("ao", False)):
        im = bpy.data.images.new(f"{NAME}_plachta_{k}", PX, PX, alpha=False)
        im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
        cim[k] = im
    ct = cn.nodes.new("ShaderNodeTexImage")
    bpy.ops.object.select_all(action='DESELECT'); cv.select_set(True)
    bpy.context.view_layer.objects.active = cv
    scn.cycles.samples = BS
    def cbake(kind, key, **kw):
        ct.image = cim[key]
        for n in cn.nodes: n.select = False
        ct.select = True; cn.nodes.active = ct
        bpy.ops.object.bake(type=kind, **kw)
        cim[key].filepath_raw = os.path.join(OUT, f"{NAME}_plachta_{key}.png"); cim[key].file_format = 'PNG'
        cim[key].save(); print("baked plachta", key, flush=True)
    cbake('DIFFUSE', "basecolor", pass_filter={'COLOR'})
    cbake('ROUGHNESS', "roughness")
    cbake('NORMAL', "normal")
    scn.cycles.samples = max(BS, 48)
    cbake('AO', "ao")
    g2 = bpy.data.materials.new(f"game_{NAME}_plachta"); g2.use_nodes = True
    g2.use_backface_culling = False
    t2 = g2.node_tree; t2.nodes.clear()
    o2 = t2.nodes.new("ShaderNodeOutputMaterial"); b2 = t2.nodes.new("ShaderNodeBsdfPrincipled")
    t2.links.new(b2.outputs[0], o2.inputs[0])
    TT = {}
    for k, im in cim.items():
        t = t2.nodes.new("ShaderNodeTexImage"); t.image = im; TT[k] = t
        if k != "basecolor": im.colorspace_settings.name = 'Non-Color'
    t2.links.new(TT["basecolor"].outputs[0], b2.inputs["Base Color"])
    t2.links.new(TT["roughness"].outputs[0], b2.inputs["Roughness"])
    nm2 = t2.nodes.new("ShaderNodeNormalMap"); t2.links.new(TT["normal"].outputs[0], nm2.inputs["Color"])
    t2.links.new(nm2.outputs[0], b2.inputs["Normal"])
    gg2 = t2.nodes.new("ShaderNodeGroup"); gg2.node_tree = grp
    sc2 = t2.nodes.new("ShaderNodeSeparateColor"); t2.links.new(TT["ao"].outputs[0], sc2.inputs[0])
    t2.links.new(sc2.outputs[0], gg2.inputs["Occlusion"])
    cv.data.materials.clear(); cv.data.materials.append(g2)
    if "lp" in cv.data.attributes: cv.data.attributes.remove(cv.data.attributes["lp"])
    for im in cim.values(): im.pack()
    cv.name = f"{NAME}_plachta"
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{NAME}_game.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"{NAME}.glb"), export_format='GLB',
                          use_selection=True, export_yup=True, export_apply=True,
                          export_image_format='JPEG', export_jpeg_quality=92,
                          export_cameras=False, export_lights=False, export_animations=False)
d = ob.dimensions
_tris = sum(len(p.vertices) - 2 for o in bpy.context.selected_objects for p in o.data.polygons)
print(f"RESULT {NAME} tris={_tris} dims_m(sxvxh)={d.x:.2f} x {d.z:.2f} x {d.y:.2f}", flush=True)
