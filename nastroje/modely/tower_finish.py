"""Doplní na vrchol věže borovici / trsy trávy a vyexportuje .glb.
python3 tower_finish.py <nazev> <pocet_borovic> <pocet_travy> <seed>
"""
import sys, os, math, random
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
NAME, NP, NG, SEED = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
rng = random.Random(SEED)
OUT = "/home/claude/work/out"
bpy.ops.wm.open_mainfile(filepath=f"{OUT}/{NAME}_game.blend")
rock = bpy.data.objects[NAME]
from PIL import Image as PImage
import numpy as _np
for o in list(bpy.data.objects):
    if o is not rock: bpy.data.objects.remove(o)
for key in ("basecolor", "normal"):
    PImage.open(f"{OUT}/{NAME}_{key}.png").convert("RGB").save(f"{OUT}/{NAME}_{key}.jpg", quality=92)
ao = _np.asarray(PImage.open(f"{OUT}/{NAME}_ao.png").convert("L")); rg = _np.asarray(PImage.open(f"{OUT}/{NAME}_roughness.png").convert("L"))
PImage.fromarray(_np.dstack([ao, rg, _np.zeros_like(ao)])).save(f"{OUT}/{NAME}_orm.jpg", quality=92)
# materiál znovu z obrázků: barva, normála, ORM (R=AO, G=drsnost, B=kov)
mat = bpy.data.materials.new(NAME); mat.use_nodes = True; mat.use_backface_culling = True; nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(bsdf.outputs[0], out.inputs[0])
def tex(path, cs):
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True); t.image.colorspace_settings.name = cs; return t
tb = tex(f"{OUT}/{NAME}_basecolor.jpg", 'sRGB'); nt.links.new(tb.outputs[0], bsdf.inputs["Base Color"])
tn = tex(f"{OUT}/{NAME}_normal.jpg", 'Non-Color'); nm = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(tn.outputs[0], nm.inputs["Color"]); nt.links.new(nm.outputs[0], bsdf.inputs["Normal"])
to = tex(f"{OUT}/{NAME}_orm.jpg", 'Non-Color'); sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(to.outputs[0], sp.inputs[0])
nt.links.new(sp.outputs[1], bsdf.inputs["Roughness"]); nt.links.new(sp.outputs[2], bsdf.inputs["Metallic"])
grp = bpy.data.node_groups.get("glTF Material Output") or bpy.data.node_groups.new("glTF Material Output", 'ShaderNodeTree')
if "Occlusion" not in [i.name for i in grp.interface.items_tree]:
    grp.interface.new_socket("Occlusion", in_out='INPUT', socket_type='NodeSocketFloat')
gg = nt.nodes.new("ShaderNodeGroup"); gg.node_tree = grp; nt.links.new(sp.outputs[0], gg.inputs["Occlusion"])
rock.data.materials.clear(); rock.data.materials.append(mat)
dg = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(rock, dg)
co = np.array([v.co[:] for v in rock.data.vertices])
H = co[:, 2].max()
xmin, ymin = co[:, :2].min(0); xmax, ymax = co[:, :2].max(0)
# kandidáti: rovné plochy nahoře (normála nahoru, vysoko)
cand = []
for _ in range(4000):
    x = rng.uniform(xmin, xmax); y = rng.uniform(ymin, ymax)
    hit = bvh.ray_cast(Vector((x, y, H + 5)), Vector((0, 0, -1)), 200)
    if hit[0] is None: continue
    p, n = hit[0], hit[1]
    if n.z > 0.8 and p.z > H * 0.55:
        cand.append((p.copy(), n.copy()))
print("candidates", len(cand))
def place(glb, pos, scale, rot, squat=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    for o in roots:
        o.location = pos - Vector((0, 0, 0.12 * scale)); o.scale = (scale * squat ** -0.5, scale * squat ** -0.5, scale * squat); o.rotation_euler = (rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), rot)
    return new
used = []
def pick(mind):
    rng.shuffle(cand)
    for p, n in cand:
        if all((p - q).length > mind for q in used):
            used.append(p); return p
    return None
# borovice: nejvyšší místa preferovat
cand.sort(key=lambda t: -t[0].z)
top = cand[: max(10, len(cand) // 3)]
for i in range(NP):
    p = None
    for c in top:
        if all((c[0] - q).length > 2.5 for q in used): p = c[0]; used.append(p); break
    if p is None: break
    place(f"{OUT}/borovice_mlada.glb", p, rng.uniform(0.5, 0.65), rng.uniform(0, 6.28), squat=rng.uniform(0.55, 0.7))
for i in range(NG):
    p = pick(0.8)
    if p is None: break
    place(f"{OUT}/trava_{rng.choice(['vysoka', 'nizka'])}_{rng.randint(1, 3)}.glb", p, rng.uniform(0.8, 1.3), rng.uniform(0, 6.28))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
tris = sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects: o.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/{NAME}_final.blend")
bpy.ops.export_scene.gltf(filepath=f"{OUT}/{NAME}.glb", export_format='GLB', use_selection=True, export_yup=True,
                          export_apply=True, export_image_format='AUTO', export_cameras=False, export_lights=False,
                          export_animations=False, export_vertex_color='MATERIAL')
print("FINISH", NAME, "tris", tris, "MB", round(os.path.getsize(f"{OUT}/{NAME}.glb") / 1e6, 1))
