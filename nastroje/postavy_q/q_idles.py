"""Tři uvolněné idle animace na kostře UAL (Quaternius) -> knihovna postavy_idle.glb pro Godot.
  Idle_Volne_1_Loop – váha na pravé noze, levé koleno povolené, paže volně, prsty povolené (UAL Idle má pěsti)
  Idle_Volne_2_Loop – palce za opaskem, váha na levé noze
  Idle_Volne_3_Loop – založené ruce (UAL2 Idle_FoldArms), váha na pravé noze, hlava mírně na stranu
Godot odřízne "_Loop" (smyčka zapnutá): v knihovně jsou Idle_Volne_1..3.
python3 q_idles.py <vystup.glb>
"""
import bpy, sys, math
from mathutils import Vector, Matrix, Quaternion
OUT = sys.argv[sys.argv.index("--") + 1]
UAL1 = "/home/claude/dl/ual1/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb"
UAL2 = "/home/claude/dl/ual2/Universal Animation Library 2[Standard]/Unreal-Godot/UAL2_Standard.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
def imp(p):
    b = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p); return [o for o in bpy.data.objects if o not in b]
o1 = imp(UAL1); rig = next(o for o in o1 if o.type == 'ARMATURE')
o2 = imp(UAL2)
for o in o2: bpy.data.objects.remove(o)
for o in o1:
    if o is not rig: bpy.data.objects.remove(o)
rig.name = "Armature"
bpy.context.view_layer.objects.active = rig; rig.select_set(True)
if rig.animation_data is None: rig.animation_data_create()
for tr in list(rig.animation_data.nla_tracks): rig.animation_data.nla_tracks.remove(tr)
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'

def set_act(a):
    rig.animation_data.action = a
    try: rig.animation_data.action_slot = a.slots[0]
    except Exception: pass
def wpos(bone, tail=False):
    pb = rig.pose.bones[bone]; return rig.matrix_world @ (pb.tail if tail else pb.head)
def rot_about(pb, axis, ang, pivot=None):
    M = pb.matrix.copy(); p = pivot if pivot is not None else M.translation.copy()
    pb.matrix = Matrix.Translation(p) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-p) @ M

FINGERS = [b.name for b in rig.pose.bones if b.name.startswith(("index_", "middle_", "ring_", "pinky_", "thumb_"))]

def make(name, base, shift_x, lean, roll, head_tilt, arms_belt, relax):
    src = bpy.data.actions[base]
    act = src.copy(); act.name = name; set_act(act)
    f0, f1 = int(src.frame_range[0]), int(src.frame_range[1])
    tg = {}
    for side in "lr":
        e = bpy.data.objects.new(f"_ik_{side}", None); scn.collection.objects.link(e); tg[side] = e
        p = bpy.data.objects.new(f"_pole_{side}", None); scn.collection.objects.link(p); tg["p" + side] = p
    for f in range(f0, f1 + 1):
        scn.frame_set(f)
        for side in "lr":
            tg[side].location = wpos(f"foot_{side}"); tg[side].keyframe_insert("location", frame=f)
            tg["p" + side].location = wpos(f"calf_{side}") + Vector((0, -0.6, 0)); tg["p" + side].keyframe_insert("location", frame=f)
    for f in range(f0, f1 + 1):
        scn.frame_set(f)
        pel = rig.pose.bones["pelvis"]
        M = pel.matrix.copy(); M.translation += Vector((shift_x, 0, -0.012)); pel.matrix = M
        bpy.context.view_layer.update(); rot_about(pel, 'Y', roll); bpy.context.view_layer.update()
        rot_about(rig.pose.bones["spine_02"], 'Y', -roll * 1.4); bpy.context.view_layer.update()
        rot_about(rig.pose.bones["spine_01"], 'X', lean); bpy.context.view_layer.update()
        rot_about(rig.pose.bones["neck_01"], 'Y', -roll * 0.5 + head_tilt); bpy.context.view_layer.update()
        rot_about(rig.pose.bones["neck_01"], 'X', -lean * 0.8); bpy.context.view_layer.update()
        for b in ("pelvis", "spine_01", "spine_02", "neck_01"):
            pb = rig.pose.bones[b]; pb.keyframe_insert("rotation_quaternion", frame=f)
            if b == "pelvis": pb.keyframe_insert("location", frame=f)
    cons = []
    def pick_pole(c, joint, ref):
        best = None
        for a in (0.0, math.pi / 2, -math.pi / 2, math.pi):
            c.pole_angle = a; scn.frame_set(f0); bpy.context.view_layer.update()
            d = (wpos(joint) - ref).length
            if best is None or d < best[0]: best = (d, a)
        c.pole_angle = best[1]
    scn.frame_set(f0)
    knee_ref = {sd: wpos(f"calf_{sd}") for sd in "lr"}
    for side in "lr":
        c = rig.pose.bones[f"calf_{side}"].constraints.new('IK'); c.target = tg[side]; c.chain_count = 2
        c.pole_target = tg["p" + side]; cons.append(c); pick_pole(c, f"calf_{side}", knee_ref[side])
    if arms_belt:
        scn.frame_set(f0)
        pz = wpos("pelvis").z; pf = wpos("spine_01")
        for side, sg in (("l", 1), ("r", -1)):
            h = bpy.data.objects.new(f"_hand_{side}", None); scn.collection.objects.link(h)
            h.parent = rig; h.parent_type = 'BONE'; h.parent_bone = "pelvis"; bpy.context.view_layer.update()
            h.matrix_world = Matrix.Translation(Vector((sg * 0.13, pf.y - 0.12, pz + 0.08)))
            po = bpy.data.objects.new(f"_epole_{side}", None); scn.collection.objects.link(po)
            po.location = Vector((sg * 0.45, pf.y + 0.35, pz + 0.25))
            c = rig.pose.bones[f"lowerarm_{side}"].constraints.new('IK'); c.target = h; c.chain_count = 2
            c.pole_target = po; cons.append(c); pick_pole(c, f"lowerarm_{side}", Vector((sg * 0.28, pf.y + 0.06, pz + 0.28)))
    bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(frame_start=f0, frame_end=f1, only_selected=False, visual_keying=True, clear_constraints=True,
                     use_current_action=True, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        if o.name.startswith("_"): bpy.data.objects.remove(o)
    act = rig.animation_data.action; act.name = name
    # povolené prsty: rotace prstů jen částečně (UAL idle = sevřené pěsti)
    if relax < 1.0:
        for f in range(f0, f1 + 1):
            scn.frame_set(f)
            for b in FINGERS:
                pb = rig.pose.bones[b]
                pb.rotation_quaternion = Quaternion().slerp(pb.rotation_quaternion, relax if not b.startswith("thumb") else max(relax, 0.6))
                pb.keyframe_insert("rotation_quaternion", frame=f)
    scn.frame_set(f0)
    print(name, "snímky", f0, f1, "kyčle L-P dz", round(wpos("thigh_l").z - wpos("thigh_r").z, 3),
          "chodidlo L", tuple(round(x, 3) for x in wpos("foot_l")))
    rig.animation_data.action = None
    return act

A = [make("Idle_Volne_1_Loop", "Idle_Loop", -0.022, math.radians(4), math.radians(3), math.radians(2), False, 0.3),
     make("Idle_Volne_2_Loop", "Idle_Loop", 0.02, math.radians(2), math.radians(-2.5), math.radians(-3), True, 0.55),
     make("Idle_Volne_3_Loop", "Idle_FoldArms_Loop", -0.018, math.radians(2), math.radians(3.5), math.radians(4), False, 1.0)]
for a in list(bpy.data.actions):
    if a not in A: bpy.data.actions.remove(a)
for a in A:
    tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, int(a.frame_range[0]), a)
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=True,
                          export_animation_mode='NLA_TRACKS', export_skins=True, export_yup=True)
print("IDLE OK", OUT)
