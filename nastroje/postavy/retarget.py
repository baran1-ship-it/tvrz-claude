"""Přenos animací Quaternius UAL (CC0) na kostru MPFB game_engine + vlastní doplňky.
python3 retarget.py <cilovy_blend> <rig_objekt> <vystup.blend>
Výsledek: rig s akcemi (30 fps, na místě) jako NLA stopy -> export do glb.
"""
import sys, math
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy
from mathutils import Matrix, Quaternion, Vector

SRC_BLEND, RIG, OUTB = sys.argv[1], sys.argv[2], sys.argv[3]
UAL = {1: "/home/claude/dl/ual1/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb",
       2: "/home/claude/dl/ual2/Universal Animation Library 2[Standard]/Unreal-Godot/UAL2_Standard.glb"}
FPS = 30
# název ve hře: (knihovna, akce, volby)
JOBS = {
    "stani": (1, "Idle_Loop", {}),
    "chuze": (1, "Walk_Loop", {}),
    "beh": (1, "Jog_Fwd_Loop", {}),
    "sprint": (1, "Sprint_Loop", {}),
    "skok_start": (1, "Jump_Start", {}),
    "pad": (1, "Jump_Loop", {}),
    "dopad": (1, "Jump_Land", {}),
    "sednout": (1, "Sitting_Enter", {}),
    "sedi": (1, "Sitting_Idle_Loop", {}),
    "vstat": (1, "Sitting_Exit", {}),
    "vstat_z_lehu": (2, "LayToIdle", {}),
    "lehnout": (2, "LayToIdle", {"reverse": True}),
    "lezi": (2, "LayToIdle", {"hold": 0, "len": 2.0}),
    "zvednout": (1, "PickUp_Table", {}),
    "zvednout_ze_zeme": (2, "Farm_Harvest", {}),
    "polozit": (1, "PickUp_Table", {"reverse": True}),
    "otevrit": (1, "Interact", {}),
    "otevrit_truhlu": (2, "Chest_Open", {}),
    "louc_stani": (1, "Idle_Torch_Loop", {}),
    "plavani": (1, "Swim_Fwd_Loop", {}),
    "plavani_na_miste": (1, "Swim_Idle_Loop", {}),
    "skrceni": (1, "Crouch_Idle_Loop", {}),
    "skrceni_chuze": (1, "Crouch_Fwd_Loop", {}),
    "kotoul": (1, "Roll", {}),
    "zasah": (1, "Hit_Chest", {}),
    "smrt": (1, "Death01", {}),
    "mec_stani": (1, "Sword_Idle", {}),
    "mec_utok": (1, "Sword_Attack", {}),
    "mec_kryt": (2, "Sword_Block", {}),
    "mec_kombo": (2, "Sword_Regular_Combo", {}),
    "stit_stani": (2, "Idle_Shield_Loop", {}),
    "kaceni": (2, "TreeChopping_Loop", {}),
    "jidlo_piti": (2, "Consume", {}),
    "nosit_naruci": (2, "Walk_Carry_Loop", {}),
    "sverakovani": (1, "Fixing_Kneeling", {}),
    "hod": (2, "OverhandThrow", {}),
    "vylez_1m": (2, "ClimbUp_1m", {}),
    "slozene_ruce": (2, "Idle_FoldArms_Loop", {}),
    "kyvnuti_ano": (2, "Yes", {}),
    "ne": (2, "Idle_No_Loop", {}),
    "mluveni": (1, "Idle_Talking_Loop", {}),
    "_bow_base": (1, "Spell_Simple_Idle_Loop", {}),
}

bpy.ops.wm.open_mainfile(filepath=SRC_BLEND)
scn = bpy.context.scene
for o in list(bpy.data.objects):
    if o.name != RIG: bpy.data.objects.remove(o)
tgt = bpy.data.objects[RIG]
tgt.animation_data_create()

def load_src(path):
    before = set(bpy.data.objects); acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE')
    for o in new:
        if o.type != 'ARMATURE': bpy.data.objects.remove(o)
    acts = {a.name: a for a in bpy.data.actions if a not in acts_before}
    return arm, acts

SRC = {k: load_src(p) for k, p in UAL.items()}

def bmap(src_arm):
    names = {b.name.lower(): b.name for b in src_arm.data.bones}
    return {tb.name: names[tb.name.lower()] for tb in tgt.data.bones if tb.name.lower() in names}

def order(arm):
    out = []
    def rec(b):
        out.append(b.name)
        for c in b.children: rec(c)
    for b in arm.data.bones:
        if b.parent is None: rec(b)
    return out

TORDER = order(tgt)
PREVQ = {}
Wt = tgt.matrix_world
def wrot(M): return M.to_quaternion()

def setup(src):
    M = bmap(src)
    Ws = src.matrix_world
    align = {}
    for tn, sn in M.items():
        tb = tgt.data.bones[tn]; sb = src.data.bones[sn]
        dt = (Wt.to_3x3() @ (tb.tail_local - tb.head_local)).normalized()
        ds = (Ws.to_3x3() @ (sb.tail_local - sb.head_local)).normalized()
        Ra = dt.rotation_difference(ds) if tn not in ("Root", "pelvis") else Quaternion()
        Rt_rest = wrot(Wt @ tb.matrix_local)
        Rs_rest = wrot(Ws @ sb.matrix_local)
        align[tn] = (Rs_rest.inverted() @ Ra @ Rt_rest)         # Rt = Rs_pose @ tohle
    # poměr výšky pánve
    k = (Wt @ tgt.data.bones["pelvis"].head_local).z / (Ws @ src.data.bones[M["pelvis"]].head_local).z
    return M, align, k

SETUP = {k: setup(v[0]) for k, v in SRC.items()}

def retarget(name, lib, aname, opt):
    src, acts = SRC[lib]; M, align, k = SETUP[lib]
    act = acts[aname]
    src.animation_data_create(); src.animation_data.action = act
    sfps = 24.0
    f0, f1 = act.frame_range
    dur = (f1 - f0) / sfps
    if "len" in opt: dur = opt["len"]
    n = max(1, int(round(dur * FPS)))
    ta = bpy.data.actions.new(name); tgt.animation_data.action = ta
    PREVQ.clear()
    Ws = src.matrix_world
    pel_rest_s = Ws @ src.data.bones[M["pelvis"]].head_local
    pel_rest_t = Wt @ tgt.data.bones["pelvis"].head_local
    for i in range(n + 1):
        t = i / FPS
        if opt.get("reverse"): t = dur - t
        if "hold" in opt: t = opt["hold"]
        sf = f0 + t * sfps
        scn.frame_set(int(math.floor(sf)), subframe=sf - math.floor(sf))
        world = {}
        for tn in TORDER:
            pb = tgt.pose.bones[tn]; tb = pb.bone
            if tn in M:
                spb = src.pose.bones[M[tn]]
                Rw = wrot(Ws @ spb.matrix) @ align[tn]
            else:
                # bez protějšku: drží klidovou orientaci vůči rodiči
                par = tb.parent
                if par is None: Rw = wrot(Wt @ tb.matrix_local)
                else: Rw = world[par.name] @ (wrot(par.matrix_local).inverted() @ wrot(tb.matrix_local))
            world[tn] = Rw
            if tb.parent is None:
                q = (wrot(Wt @ tb.matrix_local)).inverted() @ Rw
            else:
                off = wrot(tb.parent.matrix_local).inverted() @ wrot(tb.matrix_local)
                q = (world[tb.parent.name] @ off).inverted() @ Rw
            if tn in PREVQ and PREVQ[tn].dot(q) < 0: q = -q
            PREVQ[tn] = q
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=i + 1)
            if tn == "pelvis":
                spos = Ws @ src.pose.bones[M["pelvis"]].matrix.to_translation()
                d = (spos - pel_rest_s) * k
                d_local = (Wt @ tb.matrix_local).to_3x3().inverted() @ d
                if tb.parent is not None:
                    pass
                pb.location = d_local
                pb.keyframe_insert("location", frame=i + 1)
    # smyčky: poslední snímek = první
    tr = tgt.animation_data.nla_tracks.new(); tr.name = name
    st = tr.strips.new(name, 1, ta); tr.mute = True
    tgt.animation_data.action = None
    print("ANIM", name, n + 1, "snímků")
    return ta

for name, (lib, an, opt) in JOBS.items():
    retarget(name, lib, an, opt)
for k, (src, acts) in SRC.items():
    bpy.data.objects.remove(src)
scn.render.fps = FPS
bpy.ops.wm.save_as_mainfile(filepath=OUTB)
print("SAVED", OUTB)
