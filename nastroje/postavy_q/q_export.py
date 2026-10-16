"""Export hrdiny (z .blend od q_postava.py) do Godotu jako skládačka glTF se sdílenými texturami.
python3 q_export.py <jmeno> <postava.blend> <vystupni_slozka>
  <slozka>/<jmeno>_telo.gltf      – kostra + hlava, oči, obočí/řasy, vlasy (+ kůže rukou je v kusu "paze")
  <slozka>/<jmeno>_<kus>.gltf     – kusy oblečení (kostra + síť), převlékání = skrýt/zobrazit kus
  <slozka>/textury/*.png          – sdílené textury (max 2048 px)
  <slozka>/<jmeno>_sada.json      – kusy, výchozí oblečení, trojúhelníky
"""
import bpy, sys, os, json, numpy as np
NAME, BLEND, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
CFG = json.load(open("/home/claude/chars/q/postavy.json"))[NAME]
os.makedirs(os.path.join(OUT, "textury"), exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
arm = bpy.data.objects[f"{NAME}_kostra"]
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT') or o.name == "Plane": bpy.data.objects.remove(o)
arm.name = "Armature"                     # stejná cesta jako v UAL knihovně (Armature/Skeleton3D) -> animace bez retargetu
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
def sel_only(objs, active=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.hide_set(False); o.hide_viewport = False; o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]
# zmenšení textur na max 2048
# zmenšení textur: kůže obličeje 2048, vše ostatní 1024 (tablet; Godot je navíc komprimuje)
for im in bpy.data.images:
    if not im.has_data: continue
    lim = 2048 if im.name.endswith("_kuze") else 1024
    if im.size[0] > lim: im.scale(lim, lim)
# decimace přetížených kusů (boty Ranger 9 tis.)
LIMIT = CFG.get("limit", {"boots": 3500, "feet": 2600, "arms": 5400})
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    key = o.name.split("_", 1)[1] if "_" in o.name else o.name
    lim = LIMIT.get(key)
    if lim and tris(o) > lim:
        sel_only([o]); md = o.modifiers.new("dec", 'DECIMATE'); md.ratio = lim / tris(o)
        while o.modifiers.find("dec") > 0: bpy.ops.object.modifier_move_up(modifier="dec")
        bpy.ops.object.modifier_apply(modifier="dec"); print("DECIMACE", o.name, tris(o))
# rozdělení na tělo a kusy
TELO = [o for o in bpy.data.objects if o.type == 'MESH' and (o.name.endswith(("_hlava", "_oci", "_oboci")) or "_hair_" in o.name)]
KUSY = {}
CZ = {"body": "trup", "arms": "paze", "legs": "kalhoty", "feet": "boty", "boots": "boty", "sukne": "sukne", "1": "doplnek1", "2": "doplnek2"}
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in TELO and o.parent == arm:
        k = CZ.get(o.name.split("_", 1)[1], o.name.split("_", 1)[1]); KUSY.setdefault(k, []).append(o)
default = [k for k in KUSY if not (k == "kalhoty" and "sukne" in KUSY)]
def export(objs, path):
    sel_only([arm] + objs, active=arm)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', export_texture_dir="textury", use_selection=True,
                              export_yup=True, export_skins=True, export_animations=False, export_apply=True,
                              export_image_format='AUTO', export_morph=False)
    print("GLTF", os.path.basename(path), sum(tris(o) for o in objs), "tris")
export(TELO, os.path.join(OUT, f"{NAME}_telo.gltf"))
for k, objs in KUSY.items():
    export(objs, os.path.join(OUT, f"{NAME}_{k}.gltf"))
tri = {k: sum(tris(o) for o in objs) for k, objs in KUSY.items()}
telo_t = sum(tris(o) for o in TELO)
sada = {"postava": NAME, "kostra": "Quaternius / Universal Animation Library (UE názvy kostí)",
        "telo": f"{NAME}_telo.gltf", "telo_trojuhelniky": telo_t,
        "kusy": {k: {"soubor": f"{NAME}_{k}.gltf", "trojuhelniky": tri[k]} for k in KUSY},
        "vychozi": default, "oblecena_trojuhelniky": telo_t + sum(tri[k] for k in default),
        "animace": "UAL1_Standard.glb, UAL2_Standard.glb (stejná kostra, bez retargetu)"}
json.dump(sada, open(os.path.join(OUT, f"{NAME}_sada.json"), "w"), indent=1, ensure_ascii=False)
print("SADA", json.dumps(sada, ensure_ascii=False))
# glTF exportér kopíruje původní soubory -> zmenšit až na disku
from PIL import Image
td = os.path.join(OUT, "textury")
for f in os.listdir(td):
    p = os.path.join(td, f); im = Image.open(p)
    lim = 2048 if f.endswith("_kuze.png") else 1024
    if im.size[0] > lim:
        im.resize((lim, lim), Image.LANCZOS).save(p, optimize=True)
print("TEXTURY MB", round(sum(os.path.getsize(os.path.join(td, f)) for f in os.listdir(td)) / 1e6, 1))
