"""Korekce shrbení po retargetu: konstantní lokální rotace páteře/krku/hlavy ve všech akcích,
aby v 'stani' měly hrudník a hlava stejný sklon jako v klidové póze.
python3 posture_fix.py <anim.blend>"""
import sys, math
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy
from mathutils import Vector, Quaternion
AB = sys.argv[1]
bpy.ops.wm.open_mainfile(filepath=AB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for tr in rig.animation_data.nla_tracks: tr.mute = True
scn = bpy.context.scene
def pitch(bn):
    m = rig.matrix_world @ rig.pose.bones[bn].matrix
    y = (m.to_3x3() @ Vector((0, 1, 0))).normalized()
    return math.degrees(math.atan2(y.y, y.z))
def set_act(a):
    rig.animation_data.action = a
    try: rig.animation_data.action_slot = a.slots[0]
    except Exception: pass
rig.animation_data.action = None
for pb in rig.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
bpy.context.view_layer.update()
CH = ["spine_02", "spine_03", "neck_01", "head"]
rest = {b: pitch(b) for b in CH}
ref = bpy.data.actions["stani"]
def avg_delta(b):
    set_act(ref); s = 0; n = 0; M = None
    for f in range(int(ref.frame_range[0]), int(ref.frame_range[1]) + 1, 2):
        scn.frame_set(f); s += pitch(b) - rest[b]; n += 1
        M = (rig.matrix_world @ rig.pose.bones[b].matrix).to_3x3()
    return s / n, M
def apply_corr(b, q):
    path = f'pose.bones["{b}"].rotation_quaternion'
    for a in bpy.data.actions:
        fcs = []
        for fc in (a.fcurves if hasattr(a, "fcurves") else []):
            if fc.data_path == path: fcs.append(fc)
        if not fcs:
            try:
                for lay in a.layers:
                    for st in lay.strips:
                        for cb in st.channelbags:
                            fcs += [fc for fc in cb.fcurves if fc.data_path == path]
            except Exception: pass
        fcs = sorted(fcs, key=lambda c: c.array_index)
        if len(fcs) != 4: continue
        n = len(fcs[0].keyframe_points)
        if any(len(c.keyframe_points) != n for c in fcs): print("WARN keys", a.name, b); continue
        for i in range(n):
            qo = Quaternion([fcs[k].keyframe_points[i].co[1] for k in range(4)])
            qn = qo @ q
            for k in range(4):
                kp = fcs[k].keyframe_points[i]; d = qn[k] - kp.co[1]
                kp.co[1] = qn[k]; kp.handle_left[1] += d; kp.handle_right[1] += d
        for c in fcs: c.update()
for b in CH:
    d, M = avg_delta(b)
    ax_local = (M.inverted() @ Vector((1, 0, 0))).normalized()
    q = Quaternion(ax_local, math.radians(-d))
    apply_corr(b, q)
    d2, _ = avg_delta(b)
    if abs(d2) > abs(d):
        apply_corr(b, q.inverted()); apply_corr(b, q.inverted()); d2, _ = avg_delta(b)
    print("FIX", b, round(d, 1), "->", round(d2, 1))
for an in ("stani", "chuze", "beh", "luk_mirit"):
    a = bpy.data.actions[an]; set_act(a); vals = {b: 0 for b in CH}; n = 0
    for f in range(int(a.frame_range[0]), int(a.frame_range[1]) + 1, 3):
        scn.frame_set(f); n += 1
        for b in CH: vals[b] += pitch(b) - rest[b]
    print(an, {b: round(vals[b] / n, 1) for b in CH})
rig.animation_data.action = None
for tr in rig.animation_data.nla_tracks: tr.mute = False
bpy.ops.wm.save_as_mainfile(filepath=AB)
print("SAVED")
