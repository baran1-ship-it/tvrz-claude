"""Dobové oblečení (Čechy kolem 1393, venkov) šité na tělo Quaternius pomocí clothes.py.
build(body, kroj, NAME) -> {kus: [objekty]}, {kus: [díly těla, které zakrývá]}, {kus: barva/druh}
Kusy: kosile (spodní), kotle (muž, ke kolenům), cotte (žena, ke kotníkům), nohavice, skorne, opasek, kape (kápě s límcem), rouska (závoj vdané ženy).
"""
import sys, math, bpy, bmesh, numpy as np
from mathutils import Vector
sys.path.insert(0, "/home/claude/chars")
import clothes as cl
cl.BONE_NAMES |= {"Head", "neck_02"}

def _prep(body):
    if "body" not in body.vertex_groups:
        g = body.vertex_groups.new(name="body"); g.add(list(range(len(body.data.vertices))), 1.0, 'REPLACE')
    if "head" not in body.vertex_groups and "Head" in body.vertex_groups:
        pass
    return cl.body_data(body)

def _wsum(W, names):
    s = 0
    for n in names:
        if n in W: s = s + W[n]
    return s if not np.isscalar(s) else np.zeros(len(W["body"]))

def _smooth_ring_weights(ob, N, it=8):
    """váhy sukně vyhladit po obvodu (řádky po N vrcholech) – bok se při chůzi netrhá do zubů"""
    names = [g.name for g in ob.vertex_groups]; nv = len(ob.data.vertices)
    Wm = np.zeros((nv, len(names)))
    for v in ob.data.vertices:
        for g in v.groups: Wm[v.index, g.group] = g.weight
    R = nv // N
    Wr = Wm[:R * N].reshape(R, N, -1)
    for _ in range(it):
        Wr = 0.25 * np.roll(Wr, 1, 1) + 0.5 * Wr + 0.25 * np.roll(Wr, -1, 1)
    Wm[:R * N] = Wr.reshape(R * N, -1)
    Wm /= np.maximum(Wm.sum(1, keepdims=True), 1e-9)
    for gi, g in enumerate(ob.vertex_groups):
        for i in range(nv):
            if Wm[i, gi] > 0.005: g.add([i], float(Wm[i, gi]), 'REPLACE')
            else: g.remove([i])

def build(body, kroj, NAME):
    co, no, W = _prep(body)
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    hand = _wsum(W, ["hand_l", "hand_r"] + [k for k in W if k.startswith(("index_", "middle_", "ring_", "pinky_", "thumb_"))]) > 0.3
    headw = _wsum(W, ["Head", "neck_01", "neck_02"])
    arms_u = _wsum(W, ["upperarm_l", "upperarm_r"]); arms_l = _wsum(W, ["lowerarm_l", "lowerarm_r"])
    legs = _wsum(W, ["thigh_l", "thigh_r", "calf_l", "calf_r"]); calf = _wsum(W, ["calf_l", "calf_r"])
    foot = _wsum(W, ["foot_l", "foot_r", "ball_l", "ball_r"])
    torso = _wsum(W, ["pelvis", "spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r"])
    def bz(b): return (body.parent.matrix_world @ body.parent.data.bones[b].head_local).z
    arm = body.parent
    z_pel = bz("pelvis"); z_knee = bz("calf_l"); z_ank = bz("foot_l"); z_neck = bz("neck_01")
    z_hip = z_pel + 0.02
    print("KROJ výšky pánev %.3f koleno %.3f kotník %.3f krk %.3f" % (z_pel, z_knee, z_ank, z_neck))
    K = {}; HIDE = {}; MAT = {}
    def neckline(ob, ex, ez, dz, lip=0.009):
        zc = z_neck + dz
        cl.cut_iso(ob, lambda p: ((p[0] / ex) ** 2 + ((p[2] - zc) / ez) ** 2 - 1.0) if p[1] < 0.02 else
                   ((p[0] / (ex * 0.9)) ** 2 + ((p[2] - (zc + 0.03)) / (ez * 0.6)) ** 2 - 1.0), lip=lip)
    female = kroj.get("zena", False)
    # --- spodní košile (len): trup + paže
    m_sh = (torso + arms_u + arms_l > 0.4) & ~hand & (headw < 0.5) & (z > z_hip - 0.12) & (legs < 0.5)
    if kroj.get("rukav", 1.0) >= 1.0:          # rukávy košile kratší než rukávy svrchního šatu (nevykukují u zápěstí)
        m_sh &= ~((arms_l > 0.5) & (np.abs(x) > np.abs(x)[arms_l > 0.5].max() * 0.9))
    sh = cl.shell(body, co, no, m_sh, 0.004, f"{NAME}_kosile", smooth=3)
    fem_ = kroj.get("zena", False)
    neckline(sh, (0.09 if fem_ else 0.085) - 0.004, (0.07 if fem_ else 0.055) - 0.004, -0.012, lip=0.0)
    K["kosile"] = [sh]; HIDE["kosile"] = ["trup", "paze"]; MAT["kosile"] = ("len", kroj.get("kosile", [0.78, 0.74, 0.64]))
    # --- svrchní šat: kotle (muž) nebo cotte (žena): horní díl + sukně
    top_len = kroj.get("delka", "kolena")
    m_top = (torso + arms_u + arms_l > 0.4) & ~hand & (headw < 0.5) & (z > z_hip - 0.04) & (legs < 0.5)
    sleeve_end = kroj.get("rukav", 1.0)
    if sleeve_end < 1.0:
        m_top &= ~((arms_l > 0.5) & (np.abs(x) > np.abs(x)[arms_l > 0.5].max() * sleeve_end))
    top = cl.shell(body, co, no, m_top, 0.017, f"{NAME}_svrchni_h", smooth=4)
    neckline(top, 0.085 if not female else 0.09, 0.055 if not female else 0.07, -0.012)
    z_bot = z_knee - 0.03 if top_len == "kolena" else z_ank - 0.04
    sel = (legs + torso > 0.3) & ~hand & (arms_u + arms_l < 0.3)
    sk, c_, R_, zs_ = cl.tube(body, co, sel, z_hip + 0.03, z_bot, f"{NAME}_svrchni_d", N=40, ease=0.026 if not female else 0.02,
                              flare=kroj.get("flare", 0.07 if not female else 0.14), hem_noise=0.006, seed=3)
    cl.transfer_weights(sk, body, co, k=10, pelvis_blend=lambda p: (0.55 - 0.4 * np.clip((z_hip + 0.03 - p[:, 2]) / 0.3, 0, 1)) if not female else (0.6 - 0.25 * np.clip((z_hip + 0.03 - p[:, 2]) / 0.6, 0, 1)))
    _smooth_ring_weights(sk, 40, it=8)
    cl._link(sk, body)
    nm = "cotte" if female else "kotle"
    K[nm] = [top, sk]
    HIDE[nm] = ["trup", "paze", "stehna"] + (["lytka"] if top_len != "kolena" else [])
    MAT[nm] = ("vlna", kroj["barva"])
    # --- nohavice (muž): přiléhavé, stehna + lýtka
    if not female:
        m_h = (legs > 0.4) & (z > z_ank + 0.02) & (z < z_hip + 0.05)
        ho = cl.shell(body, co, no, m_h, 0.005, f"{NAME}_nohavice", smooth=3)
        K["nohavice"] = [ho]; HIDE["nohavice"] = ["stehna", "lytka"]; MAT["nohavice"] = ("vlna", kroj.get("nohavice", [0.22, 0.2, 0.17]))
    # --- škorně: nízké kožené (chodidlo + kotník)
    m_s = ((foot > 0.3) | ((calf > 0.3) & (z < z_ank + 0.07)))
    sh_ = cl.shell(body, co, no, m_s, 0.008, f"{NAME}_skorne", smooth=4)
    K["skorne"] = [sh_]; HIDE["skorne"] = ["chodidla"]; MAT["skorne"] = ("kuze", kroj.get("skorne", [0.2, 0.13, 0.08]))
    # --- opasek
    ob, *_ = cl.tube(body, co, (torso + legs > 0.3) & ~hand & (arms_u + arms_l < 0.3), z_hip + 0.07, z_hip + 0.035, f"{NAME}_opasek",
                     N=40, rows=2, ease=0.022, flare=0.0, hang=False)
    cl.transfer_weights(ob, body, co, k=8); cl._link(ob, body)
    K["opasek"] = [ob]; HIDE["opasek"] = []; MAT["opasek"] = ("kuze", kroj.get("opasek", [0.16, 0.1, 0.06]))
    # --- kápě s límcem (muž, volitelná) / rouška (vdaná žena)
    E_z = bz("Head") + 0.09
    if kroj.get("kape", False) or (female and kroj.get("rouska", True)):
        face = (y < 0.0) & (((x / (0.07 if female else 0.075)) ** 2 + ((z - (E_z - 0.02)) / (0.105 if female else 0.11)) ** 2) < 1.0)
        m_hd = (headw > 0.3) & ~face & (z > z_neck - 0.06)
        if female:
            m_hd &= (z > E_z - 0.13) | (y > 0.02)            # rouška: temeno, boky, týl, zadní krk
        hd = cl.shell(body, co, no, m_hd, 0.018 if female else 0.014, f"{NAME}_{'rouska' if female else 'kapuce'}", smooth=5)
        parts = [hd]
        if not female or kroj.get("rouska_cip", True):
            ln = 0.16 if not female else 0.22
            cp, *_ = cl.tube(body, co, (torso + headw > 0.3) & ~hand & (z > z_neck - ln - 0.05), z_neck + 0.02, z_neck - ln,
                             f"{NAME}_{'limec' if not female else 'rouska_cip'}", N=40, ease=0.02, flare=0.05, hang=True, hem_noise=0.004)
            cl.transfer_weights(cp, body, co, k=10); cl._link(cp, body)
            if female:
                # cíp roušky jen vzadu a po stranách
                b2 = bmesh.new(); b2.from_mesh(cp.data)
                bmesh.ops.delete(b2, geom=[v for v in b2.verts if v.co.y < 0.015], context='VERTS')
                b2.to_mesh(cp.data); b2.free()
            parts.append(cp)
        kn = "rouska" if female else "kape"
        K[kn] = parts; HIDE[kn] = []; MAT[kn] = ("len" if female else "vlna", kroj.get(kn + "_barva", [0.86, 0.84, 0.78] if female else [0.3, 0.28, 0.2]))
    return K, HIDE, MAT
