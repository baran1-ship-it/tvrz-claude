"""Pracovni animace z CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu, volne pro jakekoli pouziti)
prenesene na kostru Quaternius UAL (stejna kostra jako postavy) -> modely/postavy/anim/UAL_prace.glb.
Mixamo (Misa 5. 11. povolila) bez prihlaseni nejde stahnout (API: 403 "Api Key is required"), proto CMU.
BVH: github.com/una-dinosauria/cmu-mocap (data/0SS/SS_KK.bvh, prevod cgspeed).
  /opt/bl/bin/python -I tools/postavy_q/anim_cmu.py <slozka_bvh> [vystup.glb]
Prenos: smer kazde kosti jako ve zdroji (rotace svetova vuci klidu, srovnani klidovych smeru kosti), panev posun
v meritku delky nohou, bez driftu (jen kmitani kolem mista), stredni natoceni dopredu; smycky prolnute na konci.
Prsty: uchop z klipu UAL Sword_Idle (prava ruka; leva zrcadlove), kdyz klip drzi nastroj.
"""
import bpy, sys, os, math, numpy as np
from mathutils import Quaternion, Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
BVH = args[0]; OUT = args[1] if len(args) > 1 else os.path.join(REPO, "modely/postavy/anim/UAL_prace.glb")
FPS = 30
# jmeno klipu (pripona _Loop = smycka), soubor CMU, zacatek s, delka s, uchop (r, lr, "")
CLIPS = [
    ("Prace_Zametani_Loop", "13_23", 6.0, 5.0, "lr"),     # zametani (koste)
    # Misa 9. 11. r. 83 (kovar „ma krec“): 62_07 je zatloukani hrebiku v predklonu (ruka se hybe o 5 cm, hlava 0,36 m
    # pred panvi) - ne kovani. 79_01 „chopping wood“: uder obema rukama shora dolu na spalek = mlatec s perlikem u kovadliny
    ("Prace_Kovar_Loop", "79_01", 2.25, 1.2, "lr"),       # uder perlikem shora (kovar u kovadliny)
    # Misa 0.99993 r. 48 (krumpac obourucne) a test_drzeni: TreeChopping_Loop (UAL) je sek JEDNOU rukou - ruce 0,94-1,23 m
    # od sebe, leva paze (0,55 m) na topurko nedosahne. Obourucni uder shora (prvni uder 79_01) pro krumpac a sekeru.
    ("Prace_Uder_Loop", "79_01", 0.45, 1.2, "lr"),        # uder obema rukama (krumpac v lomu, sekera na spalku)
    # Misa 10. 11. (varianta B, svizna chuze hrace 2,3 m/s): UAL Walk_Loop / Walk_Formal_Loop jdou 0,98 m/s - nohy by
    # kluzaly o 134 %. Hledano: UAL1/UAL2 (jen Walk, Walk_Formal, Walk_Carry, Jog_Fwd, Sprint), CMU index
    # (brisk walk 07_12, 81_04, 82_12, Walk Fast 132_17-22): nejrychlejsi chuze 07_12 „brisk walk“ 1,82 m/s (median panve).
    ("Chuze_Svizna_Loop", "07_12", 0.2, 1.0, ""),         # svizna chuze (telo hrace)
    ("Prace_Pila_Loop", "62_03", 2.5, 4.0, "r"),          # rezani pilou
    ("Prace_Uklid_Loop", "62_11", 4.0, 6.0, "lr"),        # uklizeni, prenaseni veci
    ("Prace_Sbirani_Loop", "02_06", 0.5, 6.0, "r"),       # predklon, nabrat ze zeme, vstat (sber, prace u zeme)
    ("Piti", "13_09", 1.0, 6.0, "r"),                     # napit se (dzban, korbel)
    ("Piti_Unavene", "62_12", 0.5, 7.0, "r"),             # „hard day's drink" (hostinec)
    ("Hovor_Gesta_Loop", "18_08", 3.0, 8.0, ""),          # vysvetlovani rukama
    ("Hovor_Gesta2_Loop", "19_08", 3.0, 8.0, ""),         # druhy z dvojice
    ("Ceka_Loop", "40_10", 10.0, 8.0, ""),                # postavani, prešlapování (straz, cekani)
    ("Mavani", "13_26", 0.8, 4.0, ""),                    # mavani, ukazovani
    ("Otocka", "69_18", 0.5, 3.0, ""),                    # otoceni na miste
    # Mixamo (zdroj .fbx, zacatek 0, delka None = cely klip, prsty z klipu)
    ("Chuze_Mix_Loop", "Walking.fbx", 0.0, None, ""),           # chuze hrace (svizna)
    ("Chuze_Mix1_Loop", "Walking_1.fbx", 0.0, None, ""),
    ("Spanek_Lezmo_Loop", "Laying_Sleeping.fbx", 0.0, None, ""), # spanek vleze (r. 59/85)
]
MAP = {"Hips": "pelvis", "LowerBack": "spine_01", "Spine": "spine_02", "Spine1": "spine_03", "Neck": "neck_01", "Head": "Head"}
for s, t in (("Left", "l"), ("Right", "r")):
    MAP.update({f"{s}Shoulder": f"clavicle_{t}", f"{s}Arm": f"upperarm_{t}", f"{s}ForeArm": f"lowerarm_{t}", f"{s}Hand": f"hand_{t}",
                f"{s}UpLeg": f"thigh_{t}", f"{s}Leg": f"calf_{t}", f"{s}Foot": f"foot_{t}", f"{s}ToeBase": f"ball_{t}"})
PRSTY = ("index", "middle", "ring", "pinky", "thumb")
# Mixamo (Misa 10. 11.: „na internetu to urcite je“ - FBX z mixamo.com, tools/postavy_q/mixamo, 30 fps, na miste)
MIX = os.path.join(HERE, "mixamo")
MAPM = {"mixamorig:Hips": "pelvis", "mixamorig:Spine": "spine_01", "mixamorig:Spine1": "spine_02", "mixamorig:Spine2": "spine_03",
        "mixamorig:Neck": "neck_01", "mixamorig:Head": "Head"}
for s_, t in (("Left", "l"), ("Right", "r")):
    MAPM.update({f"mixamorig:{s_}Shoulder": f"clavicle_{t}", f"mixamorig:{s_}Arm": f"upperarm_{t}",
                 f"mixamorig:{s_}ForeArm": f"lowerarm_{t}", f"mixamorig:{s_}Hand": f"hand_{t}",
                 f"mixamorig:{s_}UpLeg": f"thigh_{t}", f"mixamorig:{s_}Leg": f"calf_{t}", f"mixamorig:{s_}Foot": f"foot_{t}",
                 f"mixamorig:{s_}ToeBase": f"ball_{t}"})
    for pr in PRSTY:
        for i in (1, 2, 3):
            MAPM[f"mixamorig:{s_}Hand{pr.capitalize()}{i}"] = f"{pr}_0{i}_{t}"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, "modely/postavy/anim/UAL1.glb"))
T = next(o for o in bpy.data.objects if o.type == "ARMATURE")
for o in [o for o in bpy.data.objects if o.type == "MESH"]: bpy.data.objects.remove(o)
# uchop prstu z klipu UAL (lokalni rotace kosti prstu prave ruky v 1. snimku)
grip = {}
ga = bpy.data.actions.get("Sword_Idle_Armature")
if ga:
    for fc in ga.fcurves:
        dp = fc.data_path
        if 'pose.bones["' in dp and dp.endswith("rotation_quaternion"):
            bn = dp.split('"')[1]
            if bn.endswith("_r") and bn.startswith(PRSTY):
                grip.setdefault(bn, [1, 0, 0, 0])[fc.array_index] = fc.evaluate(ga.frame_range[0])
print("UCHOP kosti", len(grip))
if T.animation_data:
    T.animation_data.action = None
    for tr in list(T.animation_data.nla_tracks): T.animation_data.nla_tracks.remove(tr)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
TB = [b for b in T.data.bones]
order = []
def walk(b):
    order.append(b.name)
    for c in b.children: walk(c)
for b in TB:
    if b.parent is None: walk(b)
Qr = {b.name: b.matrix_local.to_quaternion() for b in TB}
dirT = {b.name: (b.tail_local - b.head_local).normalized() for b in TB}
par = {b.name: (b.parent.name if b.parent else None) for b in TB}
H_T = T.data.bones["pelvis"].head_local.z
for pb in T.pose.bones: pb.rotation_mode = 'QUATERNION'
FWD = Vector((0, -1, 0))

def nacti(cid):
    if cid.endswith(".fbx"):
        for o in [o for o in bpy.data.objects if o is not T]: bpy.data.objects.remove(o)
        bpy.ops.import_scene.fbx(filepath=os.path.join(MIX, cid), automatic_bone_orientation=False)
        return next(o for o in bpy.context.selected_objects if o.type == "ARMATURE")
    s3 = cid.split("_")[0].zfill(3)
    p = os.path.join(BVH, f"{cid}.bvh")
    for o in [o for o in bpy.data.objects if o is not T]: bpy.data.objects.remove(o)
    bpy.ops.import_anim.bvh(filepath=p, axis_forward='-Z', axis_up='Y', global_scale=1.0, update_scene_fps=False, update_scene_duration=False)
    return bpy.context.object

def prenes(name, cid, t0, dl, uchop):
    S = nacti(cid)
    act_s = S.animation_data.action
    n_src = int(act_s.frame_range[1])
    mix = cid.endswith(".fbx")
    MP = MAPM if mix else MAP
    src_fps = 30 if mix else 120
    if dl is None:
        dl = (n_src - 1) / src_fps
    QsR = {b.name: b.matrix_local.to_quaternion() for b in S.data.bones}
    A = {}
    for sb, tb in MP.items():
        b = S.data.bones[sb]; ds = (b.tail_local - b.head_local).normalized()
        A[tb] = ds.rotation_difference(dirT[tb])
    step = src_fps // FPS
    loop = name.endswith("_Loop") and not mix         # Mixamo: smycka uz je hotova (prvni = posledni poza)
    K = int(0.4 * FPS) if loop else 0
    f0 = max(1, int(t0 * src_fps) - K * step)
    f1 = min(n_src + (1 if mix else 0), int((t0 + dl + (0 if mix else 1.5)) * src_fps) + (1 if mix else 0))
    frames = list(range(f0, f1, step))
    sc = bpy.context.scene
    Ds, Ps = [], []
    for f in frames:
        sc.frame_set(f)
        D = {}
        for sb, tb in MP.items():
            q = (S.matrix_world @ S.pose.bones[sb].matrix).to_quaternion()
            D[tb] = q @ QsR[sb].inverted() @ A[tb].inverted()
        Ds.append(D); Ps.append(S.matrix_world @ S.pose.bones["mixamorig:Hips" if mix else "Hips"].head)
    P = np.array([p[:] for p in Ps])
    # meritko podle vysky panve ve stoji (90. percentil celeho klipu), drift pryc (klouzavy prumer 1,5 s)
    zs = []
    for f in range(1, n_src, max(1, src_fps // 4)):
        sc.frame_set(f); zs.append((S.matrix_world @ S.pose.bones["mixamorig:Hips" if mix else "Hips"].head).z)
    zst = float(np.percentile(zs, 90)); k = H_T / zst
    w = int(1.5 * FPS) | 1
    ker = np.ones(w) / w
    sm = np.stack([np.convolve(np.pad(P[:, i], (w // 2, w // 2), mode="edge"), ker, mode="valid") for i in (0, 1)], 1)
    if name.startswith("Chuze"):
        # chuze: posun panve = stala rychlost -> odecist primku (klouzavy prumer 1,5 s pri cyklu ~1 s nechal v panvi
        # cast posunu: 10. 11. test_klipy_chuze Chuze_Svizna_Loop spicky z -1,07..0,45 m, opora 5 %, 0,26 m/s)
        t = np.arange(len(P))
        sm = np.stack([np.polyval(np.polyfit(t, P[:, i], 1), t) for i in (0, 1)], 1)
    # stredni natoceni panve -> dopredu (-Y)
    yaws = []
    for D in Ds:
        v = D["pelvis"] @ FWD; yaws.append(math.atan2(v.y, v.x))
    my = math.atan2(np.mean(np.sin(yaws)), np.mean(np.cos(yaws)))
    Cy = Quaternion((0, 0, 1), math.atan2(FWD.y, FWD.x) - my)
    # mistni rotace vsech kosti cile
    L = []
    for i, D in enumerate(Ds):
        Dall = {}
        loc = {}
        for bn in order:
            if bn in D: Dall[bn] = (Cy @ D[bn]) if True else D[bn]
            else: Dall[bn] = Dall[par[bn]] if par[bn] else Quaternion()
        fr = {}
        for bn in order:
            Dp = Dall[par[bn]] if par[bn] else Quaternion()
            fr[bn] = Qr[bn].inverted() @ Dp.inverted() @ Dall[bn] @ Qr[bn]
        d = Vector(((P[i, 0] - sm[i, 0]) * k, (P[i, 1] - sm[i, 1]) * k, (P[i, 2] - zst) * k))
        d = Cy @ d
        fr["_loc"] = Qr["pelvis"].inverted() @ d
        if uchop:
            for bn, q in grip.items():
                fr[bn] = Quaternion(q)
                if "l" in uchop and uchop != "r": fr[bn[:-2] + "_l"] = Quaternion(q)
        L.append(fr)
    # smycka: konec vybrat tak, aby se poza co nejvic shodovala se zacatkem, a prolnout
    i0 = K
    nlen = int(dl * FPS)
    if loop:
        def dist(a, b): return sum(1 - abs(L[a][bn].dot(L[b][bn])) for bn in MP.values())
        cand = range(i0 + max(FPS, nlen - FPS), min(len(L) - 1, i0 + nlen + FPS))
        iend = min(cand, key=lambda j: dist(j, i0)) if len(cand) else min(len(L) - 1, i0 + nlen)
        for j in range(K):
            wgt = (j + 1) / (K + 1)
            a, b = L[iend - K + j], L[i0 - K + j]
            for bn in a:
                if bn == "_loc": a[bn] = a[bn].lerp(b[bn], wgt)
                else: a[bn] = a[bn].slerp(b[bn], wgt)
        seq = L[i0:iend]
    else:
        seq = L[i0:i0 + nlen]
    act = bpy.data.actions.new(name)
    for bn in order:
        prev = None
        vals = []
        for fr in seq:
            q = fr.get(bn, Quaternion())
            if prev is not None and q.dot(prev) < 0: q = -q
            prev = q; vals.append(q)
        for c in range(4):
            fc = act.fcurves.new(f'pose.bones["{bn}"].rotation_quaternion', index=c, action_group=bn)
            fc.keyframe_points.add(len(vals))
            co = np.zeros(len(vals) * 2, np.float32); co[0::2] = np.arange(len(vals)); co[1::2] = [v[c] for v in vals]
            fc.keyframe_points.foreach_set("co", co); fc.update()
    for c in range(3):
        fc = act.fcurves.new('pose.bones["pelvis"].location', index=c, action_group="pelvis")
        fc.keyframe_points.add(len(seq))
        co = np.zeros(len(seq) * 2, np.float32); co[0::2] = np.arange(len(seq)); co[1::2] = [fr["_loc"][c] for fr in seq]
        fc.keyframe_points.foreach_set("co", co); fc.update()
    act.use_fake_user = True
    T.animation_data_create()
    tr = T.animation_data.nla_tracks.new(); tr.name = name
    tr.strips.new(name, 0, act)
    bpy.data.actions.remove(act_s)
    print("KLIP", name, cid, "snimku", len(seq), "smycka" if loop else "", "meritko %.4f" % k)
    sys.stdout.flush()

for c in CLIPS:
    try: prenes(*c)
    except Exception as e: print("CHYBA", c[0], e); sys.stdout.flush()
for o in [o for o in bpy.data.objects if o is not T]: bpy.data.objects.remove(o)
bpy.context.scene.render.fps = FPS
T.animation_data.action = None
bpy.ops.object.select_all(action="DESELECT"); T.select_set(True); bpy.context.view_layer.objects.active = T
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_animations=True,
                          export_animation_mode="ACTIONS", export_force_sampling=True, export_skins=True, export_def_bones=False)
print("ANIM", OUT, [a.name for a in bpy.data.actions])
sys.stdout.flush(); os._exit(0)
