"""Vlastní animace navíc k přeneseným: otočky na místě, louč za chůze, luk (napnout/mířit/výstřel), dýchání v lehu.
python3 custom_anims.py <anim.blend> <rig>
"""
import sys, math
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy
from mathutils import Matrix, Quaternion, Vector

AB, RIG = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=AB)
rig = bpy.data.objects[RIG]
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
B = rig.data.bones
ORDER = []
def _rec(b):
    ORDER.append(b.name)
    for c in b.children: _rec(c)
for b in B:
    if b.parent is None: _rec(b)

def nframes(act):
    return int(round(act.frame_range[1]))

def sample(act, f):
    """basis (quat, loc) všech kostí ze křivek akce ve snímku f."""
    P = {n: [Quaternion(), Vector()] for n in ORDER}
    for fc in act.fcurves if hasattr(act, "fcurves") else []:
        pass
    # Blender 5: kanály jsou v layers/strips/channelbags
    cbs = []
    for layer in act.layers:
        for st in layer.strips:
            for cb in st.channelbags: cbs.append(cb)
    for cb in cbs:
        for fc in cb.fcurves:
            dp = fc.data_path
            if not dp.startswith('pose.bones["'): continue
            bn = dp.split('"')[1]; prop = dp.split('.')[-1]
            if bn not in P: continue
            v = fc.evaluate(f)
            if prop == "rotation_quaternion": P[bn][0][fc.array_index] = v
            elif prop == "location": P[bn][1][fc.array_index] = v
    for n in P: P[n][0] = P[n][0].normalized() if P[n][0].magnitude > 1e-6 else Quaternion()
    return P

def fk(P):
    """pose matice (prostor armatury) pro basis P."""
    M = {}
    for n in ORDER:
        b = B[n]; q, l = P[n]
        basis = Matrix.Translation(l) @ q.to_matrix().to_4x4()
        if b.parent is None: M[n] = b.matrix_local @ basis
        else: M[n] = M[b.parent.name] @ (b.parent.matrix_local.inverted() @ b.matrix_local) @ basis
    return M

def set_world_rot(P, n, Rw):
    M = fk(P); b = B[n]
    if b.parent is None: par = b.matrix_local.to_quaternion(); q = par.inverted() @ Rw
    else:
        off = (b.parent.matrix_local.inverted() @ b.matrix_local).to_quaternion()
        q = (M[b.parent.name].to_quaternion() @ off).inverted() @ Rw
    P[n][0] = q

def rotate_world(P, n, R):
    M = fk(P); set_world_rot(P, n, R @ M[n].to_quaternion())

def point(P, n, d):
    """natočí kost n, aby mířila směrem d (prostor armatury)."""
    M = fk(P); y = (M[n].to_3x3() @ Vector((0, 1, 0))).normalized()
    rotate_world(P, n, y.rotation_difference(d.normalized()))

def copyP(P): return {n: [q.copy(), l.copy()] for n, (q, l) in P.items()}

def mixP(A, Bp, t, bones=None):
    out = copyP(A)
    for n in (bones or ORDER):
        out[n][0] = A[n][0].slerp(Bp[n][0], t); out[n][1] = A[n][1].lerp(Bp[n][1], t)
    return out

def write(name, frames):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    prev = {}
    for i, P in enumerate(frames):
        for n in ORDER:
            q = P[n][0]
            if n in prev and prev[n].dot(q) < 0: q = -q
            prev[n] = q
            pb = rig.pose.bones[n]; pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=i + 1)
            if n == "pelvis": pb.location = P[n][1]; pb.keyframe_insert("location", frame=i + 1)
    tr = rig.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 1, act); tr.mute = True
    rig.animation_data.action = None
    print("ANIM", name, len(frames))

A = {a.name: a for a in bpy.data.actions}
def ease(t): return t * t * (3 - 2 * t)
LEGS = [n for n in ORDER if n.startswith(("thigh", "calf", "foot", "ball"))]
LARM = [n for n in ORDER if n.endswith("_l") and not n.startswith(("thigh", "calf", "foot", "ball"))]

# ---------- otočky na místě: krok z chůze se zmenšeným rozsahem, trup se natáčí do směru
idle, walk = A["stani"], A["chuze"]
nw = nframes(walk)
for nm, sgn in (("otoceni_vlevo", 1), ("otoceni_vpravo", -1)):
    fr = []
    for i in range(1, nw + 1):
        Pi = sample(idle, i); Pw = sample(walk, i)
        P = mixP(Pi, Pw, 0.42, LEGS + ["pelvis"])
        ph = math.sin(2 * math.pi * (i - 1) / (nw - 1))
        rotate_world(P, "spine_02", Quaternion((0, 0, 1), sgn * math.radians(9)))
        rotate_world(P, "pelvis", Quaternion((0, 0, 1), sgn * math.radians(6 + 3 * ph)))
        fr.append(P)
    write(nm, fr)

# ---------- louč za chůze: levá paže z louc_stani (vůči trupu), zbytek chůze
torch = A["louc_stani"]; nt = nframes(torch)
fr = []
for i in range(1, nw + 1):
    Pw = sample(walk, i); Pt = sample(torch, 1 + (i - 1) % max(1, nt - 1))
    for n in LARM: Pw[n] = [Pt[n][0].copy(), Pt[n][1].copy()]
    fr.append(Pw)
write("louc_chuze", fr)

# ---------- lezi: dýchání (smyčka 2 s)
lay = A["lezi"]; lay.name = "_lezi_old"; base = sample(lay, 1); fr = []
for i in range(61):
    P = copyP(base); s = math.sin(2 * math.pi * i / 60)
    rotate_world(P, "spine_03", Quaternion((1, 0, 0), math.radians(1.2 * s)))
    fr.append(P)
write("lezi", fr)
# původní statickou 'lezi' (z retargetu) odstranit
for tr in list(rig.animation_data.nla_tracks):
    if tr.name == "lezi" and tr.strips[0].action.name != "lezi": rig.animation_data.nla_tracks.remove(tr)

# ---------- luk
def bow_pose(Pbase, draw=1.0, release=0.0):
    """draw 0 = luk dole před tělem, 1 = plně natažený; release = posun pravé ruky po výstřelu."""
    P = copyP(Pbase)
    tw = draw
    rotate_world(P, "pelvis", Quaternion((0, 0, 1), math.radians(-30 * tw)))
    for n, a in (("spine_01", -12), ("spine_02", -12), ("spine_03", -10)):
        rotate_world(P, n, Quaternion((0, 0, 1), math.radians(a * tw)))
    M = fk(P)
    shl = M["upperarm_l"].to_translation(); shr = M["upperarm_r"].to_translation()
    # cíl: dopředu (−Y), mírně nahoru
    fwd = Vector((0, -1, 0.06 * draw - 0.5 * (1 - draw))).normalized()
    point(P, "upperarm_l", fwd.lerp(Vector((0.15, -0.5, -0.85)), 1 - draw))
    point(P, "lowerarm_l", fwd.lerp(Vector((0.05, -0.75, -0.65)), 1 - draw))
    M = fk(P)
    hl = M["hand_l"].to_translation()
    head = M["head"].to_translation()
    chin = head + Vector((0.03, -0.06, -0.06))
    hand_r = hl.lerp(chin, draw) + Vector((0, 0.07 * release, 0.02 * release))
    line = (hand_r - hl).normalized() if (hand_r - hl).length > 0.05 else Vector((0, 1, 0))
    elbow = hand_r + line * (0.24 * draw + 0.05) + Vector((-0.05 * (1 - draw), 0, -0.22 * (1 - draw) + 0.03 * draw))
    point(P, "upperarm_r", elbow - shr)
    M = fk(P)
    point(P, "lowerarm_r", hand_r - M["lowerarm_r"].to_translation())
    # hlava a krk zpět dopředu (míří na cíl)
    M = fk(P)
    rest_head = B["head"].matrix_local.to_quaternion()
    cur = M["head"].to_quaternion()
    set_world_rot(P, "neck_01", Quaternion((0, 0, 1), math.radians(14 * tw)) @ fk(P)["neck_01"].to_quaternion())
    set_world_rot(P, "head", rest_head.slerp(cur, 1 - 0.8 * tw) if tw > 0 else cur)
    return P

idle1 = sample(idle, 1)
fr = []
for i in range(31):
    t = ease(i / 30); fr.append(bow_pose(idle1, draw=t))
write("luk_napnout", fr)
fr = []
for i in range(61):
    s = math.sin(2 * math.pi * i / 60)
    P = bow_pose(sample(idle, 1 + i % 60), draw=1.0)
    rotate_world(P, "spine_03", Quaternion((1, 0, 0), math.radians(0.6 * s)))
    fr.append(P)
write("luk_mirit", fr)
fr = []
for i in range(31):
    if i < 4: P = bow_pose(idle1, 1.0, release=i / 3)
    elif i < 12: P = bow_pose(idle1, 1.0, release=1.0)
    else:
        t = ease((i - 12) / 18); P = bow_pose(idle1, 1.0 - 0.6 * t, release=1.0 - t)
    fr.append(P)
write("luk_vystrel", fr)
# pomocná akce pryč
for tr in list(rig.animation_data.nla_tracks):
    if tr.name.startswith("_"): rig.animation_data.nla_tracks.remove(tr)
for a in list(bpy.data.actions):
    if a.name.startswith("_"): bpy.data.actions.remove(a)
bpy.ops.wm.save_as_mainfile(filepath=AB)
print("SAVED")
