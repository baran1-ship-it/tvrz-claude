"""Kosti sukně (16 řetězů × 3) a copu (6), váhy, a zapečená simulace látky do všech animací UAL1+UAL2.
Sukně: hrubá „látka“ z kloubů (svislé délky, obvodové vazby, tvarová tuhost, gravitace) + kolize s kapslemi
nohou (stehna, lýtka, chodidla) a rukou (předloktí, dlaně) -> nohy ani ruce sukní neprojdou, látka se odhrne.
Cop: řetěz s gravitací a kolizí se zády. Výsledek: rotace nových kostí zapečené do každé animace (žádná fyzika za běhu)."""
import sys, os, math, time; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import numpy as np, anim_util, json
from mathutils import Vector, Matrix, Quaternion
P = json.load(open("/home/claude/z30/scripts/params.json"))
SRC = sys.argv[sys.argv.index("--") + 1]; DST = sys.argv[sys.argv.index("--") + 2]
ONLY = os.environ.get("ONLY", "")
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects["zena30_kostra"]
G = np.load("/home/claude/z30/skirt_grid.npz"); R, zs, th, CEN = G["R"], G["zs"], G["th"], G["CEN"]
N = len(th); K = 24; STEPC = N // K
ZJ = [1.0, 0.76, 0.53, 0.30, float(zs[-1])]
NS = len(ZJ) - 1
def R_at(i, z):
    col = R[:, i % N]; return float(np.interp(-z, -zs, col))
INSET = 0.012   # kost vede kousek pod povrchem látky
# ---------- kosti
bpy.context.view_layer.objects.active = arm; arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
SK = []   # [chain][seg] jména
for j in range(K):
    i = j * STEPC; t = th[i]; names_ = []
    prev = eb["pelvis"]
    for k in range(NS):
        za, zb = ZJ[k], ZJ[k + 1]
        ra, rb = R_at(i, za) - INSET, R_at(i, zb) - INSET
        b = eb.new(f"sukne_{j:02d}_{k+1}")
        b.head = (CEN[0] + ra * math.cos(t), CEN[1] + ra * math.sin(t), za)
        b.tail = (CEN[0] + rb * math.cos(t), CEN[1] + rb * math.sin(t), zb)
        b.roll = 0; b.parent = prev; b.use_connect = (k > 0); b.use_deform = True
        prev = b; names_.append(b.name)
    SK.append(names_)
# cop: dráha podél zad
def back_y(z):
    tab = [(1.585, 0.095), (1.52, 0.115), (1.46, 0.140), (1.40, 0.165), (1.32, 0.17), (1.22, 0.162), (1.10, 0.15), (1.00, 0.145), (0.9, 0.14)]
    return float(np.interp(z, [t[0] for t in tab][::-1], [t[1] for t in tab][::-1]))
ZC = [1.585, 1.48, 1.37, 1.26, 1.15, 1.04, 0.92]
COP = []; prev = eb["Head"]
for k in range(len(ZC) - 1):
    b = eb.new(f"cop_{k+1}"); b.head = (0, back_y(ZC[k]), ZC[k]); b.tail = (0, back_y(ZC[k+1]), ZC[k+1])
    b.roll = 0; b.parent = prev; b.use_connect = (k > 0); prev = b; COP.append(b.name)
bpy.ops.object.mode_set(mode='OBJECT')
REST = {b.name: b.matrix_local.copy() for b in arm.data.bones}

# ---------- váhy sukně, zástěry a copu
def ss(x, a, b): t = min(max((x - a) / (b - a), 0), 1); return t * t * (3 - 2 * t)
def chain_weights(ang, z):
    """[(kost, w)] pro bod látky v úhlu ang a výšce z (pod kořenem řetězů)"""
    jf = ((ang % (2 * math.pi)) / (2 * math.pi)) * K
    j0 = int(math.floor(jf)) % K; j1 = (j0 + 1) % K; a = jf - math.floor(jf)
    out = {}
    def along(j, wj):
        if z >= ZJ[0]:
            return
        for k in range(NS):
            za, zb = ZJ[k], ZJ[k + 1]
            if za >= z >= zb or (k == NS - 1 and z < zb):
                t = (za - z) / (za - zb)
                wk = 1.0
                if t < 0.3:
                    wp = 0.5 * (1 - t / 0.3)
                    pn = SK[j][k - 1] if k > 0 else "pelvis"
                    out[pn] = out.get(pn, 0) + wj * wp; wk -= wp
                if t > 0.7 and k < NS - 1:
                    wn = 0.5 * (t - 0.7) / 0.3
                    out[SK[j][k + 1]] = out.get(SK[j][k + 1], 0) + wj * wn; wk -= wn
                out[SK[j][k]] = out.get(SK[j][k], 0) + wj * wk
                return
    along(j0, 1 - a); along(j1, a)
    return out
def reweight_cloth(ob, top_from_existing=True):
    me = ob.data
    for v in me.vertices:
        c = v.co
        if c.z >= ZJ[0] + 0.04: continue
        ang = math.atan2(c.y - CEN[1], c.x - CEN[0])
        w = chain_weights(ang, c.z)
        # přechod nad kořenem: mix původních vah (pánev) a řetězů
        blend = ss(c.z, ZJ[0], ZJ[0] + 0.04)
        old = {ob.vertex_groups[g.group].name: g.weight for g in v.groups}
        for g in list(v.groups): ob.vertex_groups[g.group].remove([v.index])
        tot = {}
        for n_, x in w.items(): tot[n_] = tot.get(n_, 0) + x * (1 - blend)
        for n_, x in old.items(): tot[n_] = tot.get(n_, 0) + x * blend if blend > 0 else tot.get(n_, 0)
        if blend == 0 and not w: tot = old
        s = sum(tot.values()) or 1
        for n_, x in tot.items():
            if x / s < 0.005: continue
            g = ob.vertex_groups.get(n_) or ob.vertex_groups.new(name=n_)
            g.add([v.index], x / s, 'REPLACE')
for nm in ("zena30_sukne", "zena30_zastera"):
    reweight_cloth(bpy.data.objects[nm])
# cop: váhy podle výšky
hair = bpy.data.objects["zena30_vlasy"]
for v in hair.data.vertices:
    c = v.co
    old = {hair.vertex_groups[g.group].name: g.weight for g in v.groups}
    if "Head" in old and old["Head"] > 0.99: continue   # vlasy na hlavě
    if c.z > ZC[0]: continue
    for g in list(v.groups): hair.vertex_groups[g.group].remove([v.index])
    tot = {}
    for k in range(len(COP)):
        za, zb = ZC[k], ZC[k + 1]
        if za >= c.z >= zb or (k == len(COP) - 1 and c.z < zb):
            t = (za - c.z) / (za - zb); wk = 1.0
            if t < 0.3:
                wp = 0.5 * (1 - t / 0.3); pn = COP[k - 1] if k else "Head"
                tot[pn] = wp; wk -= wp
            if t > 0.7 and k < len(COP) - 1:
                wn = 0.5 * (t - 0.7) / 0.3; tot[COP[k + 1]] = wn; wk -= wn
            tot[COP[k]] = tot.get(COP[k], 0) + wk; break
    for n_, x in tot.items():
        g = hair.vertex_groups.get(n_) or hair.vertex_groups.new(name=n_); g.add([v.index], x, 'REPLACE')

# ---------- simulace
pb = arm.pose.bones
def M(n): return pb[n].matrix   # armature space (= svět, kostra v počátku bez transformace)
def seg_pts(n, r0, r1, ext=0.0):
    m = M(n); h = m.translation.copy(); t = (m @ Vector((0, pb[n].bone.length * (1 + ext), 0, 1))).to_3d() if False else (m @ Vector((0, pb[n].bone.length * (1 + ext), 0)))
    return (np.array(h), np.array(t), r0, r1)
MARG = P["sim_okraj"]
CAPS = json.load(open("/home/claude/z30/caps.json"))
def capsules():
    C = []
    for bn, c in CAPS.items():
        m = M(c.get("bone", bn))
        a = np.array(m @ Vector(c["a"])); b = np.array(m @ Vector(c["b"]))
        r0, r1 = c["r0"], c["r1"]
        if bn.startswith("hand"): r0, r1 = min(r0, 0.05), min(r1, 0.045)
        if bn.startswith("thigh"): a = a + (b - a) * 0.4; r0, r1 = 0.085, 0.078
        sg = -1 if bn.startswith(("hand", "lowerarm")) else 1
        if sg < 0 and not P["sim_ruce"]: continue
        if bn.startswith("lowerarm"): continue
        C.append((a, b, r0, r1, sg))
    C.sort(key=lambda c: -c[4])   # ruce první, nohy poslední (nohy mají přednost)
    C.reverse()
    return C
def body_caps():
    C = []
    h1 = np.array(M("spine_01").translation); h3 = np.array(M("neck_01").translation)
    C.append((h1, h3, 0.12, 0.10, 1))
    C.append((np.array(M("thigh_l").translation), np.array(M("thigh_r").translation), 0.13, 0.13, 1))
    C.append((np.array(M("Head").translation), np.array(M("Head").translation) + np.array([0, 0, 0.12]), 0.10, 0.10, 1))
    return C
def closest_seg_seg(p1, q1, p2, q2):
    d1 = q1 - p1; d2 = q2 - p2; r = p1 - p2
    a = d1 @ d1; e = d2 @ d2; f = d2 @ r
    if a < 1e-12 and e < 1e-12: return 0.0, 0.0
    if a < 1e-12: return 0.0, np.clip(f / e, 0, 1)
    c = d1 @ r
    if e < 1e-12: return np.clip(-c / a, 0, 1), 0.0
    b = d1 @ d2; den = a * e - b * b
    s = np.clip((b * f - c * e) / den, 0, 1) if den > 1e-12 else 0.0
    t = (b * s + f) / e
    if t < 0: t = 0; s = np.clip(-c / a, 0, 1)
    elif t > 1: t = 1; s = np.clip((b - c) / a, 0, 1)
    return s, t
def _outdir(d, ax, radial):
    """směr vytlačení: kolmo k ose kapsle, vždy na stranu ven od těla (žádné obtočení látky kolem nohy)"""
    dp = d - (d @ ax) * ax
    rp = radial - (radial @ ax) * ax
    if np.linalg.norm(rp) < 1e-6: rp = dp
    if dp @ rp < 0 or np.linalg.norm(dp) < 1e-6: dp = rp
    return dp / max(np.linalg.norm(dp), 1e-9), (dp @ rp) >= 0
def _outdir_v(d, ax, rad):
    dp = d - (d @ ax)[:, None] * ax[None]
    rp = rad - (rad @ ax)[:, None] * ax[None]
    rpn = np.linalg.norm(rp, axis=1); dpn = np.linalg.norm(dp, axis=1)
    rp = np.where((rpn < 1e-6)[:, None], dp, rp)
    same = np.einsum('ij,ij->i', dp, rp) >= 0
    n = np.where((~same | (dpn < 1e-6))[:, None], rp, dp)
    n = n / np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]
    return n, same
def _dir_prev(d, dprev, ax, rad):
    """směr ven z kapsle: na stranu, kde bod byl na začátku kroku (látka se nepřetáhne přes nohu);
    když byl uvnitř už tehdy, podle směru od těla"""
    pp = dprev - (dprev @ ax)[:, None] * ax[None]
    ppn = np.linalg.norm(pp, axis=1)
    n_r, _ = _outdir_v(d, ax, rad)
    n = np.where((ppn > 1e-4)[:, None], pp / np.maximum(ppn, 1e-9)[:, None], n_r)
    return n
def push_points(X, C, marg, fixed, center=None, Xprev=None):
    for (a, b, r0, r1, sg) in C:
        ab = b - a; L2 = ab @ ab + 1e-12; ax = ab / math.sqrt(L2)
        t = np.clip(((X - a) @ ab) / L2, 0, 1)
        cp = a + t[:, None] * ab; d = X - cp; dist = np.linalg.norm(d, axis=1)
        rr = r0 + (r1 - r0) * t + marg
        m = (dist < rr) & ~fixed
        if not m.any(): continue
        if center is not None:
            rad = (X - center) * sg; rad[:, 2] = 0
            rad = rad / np.maximum(np.linalg.norm(rad, axis=1), 1e-9)[:, None]
            rad[:, 2] += P["sim_nahoru"] * (1 - abs(ax[2])) * sg
        else: rad = d
        if Xprev is not None:
            tp = np.clip(((Xprev - a) @ ab) / L2, 0, 1); dpv = Xprev - (a + tp[:, None] * ab)
            inside_prev = np.linalg.norm(dpv, axis=1) < (r0 + (r1 - r0) * tp + marg) * 0.7
            n = _dir_prev(d, np.where(inside_prev[:, None], 0, dpv), ax, rad)
        else:
            n, _ = _outdir_v(d, ax, rad)
        newp = cp[m] + n[m] * rr[m][:, None]; dl = newp - X[m]
        ln = np.linalg.norm(dl, axis=1); dl *= np.minimum(1, (P['sim_max_posun'] * (2.0 if sg > 0 else 0.6)) / np.maximum(ln, 1e-9))[:, None]
        X[m] = X[m] + dl
def _cseg(P1, Q1, a, b):
    """nejbližší body úseček P1Q1 (n) a ab (1) -> s (n), t (n)"""
    d1 = Q1 - P1; d2 = b - a; r = P1 - a
    A = np.einsum('ij,ij->i', d1, d1); E = d2 @ d2; F = r @ d2
    Cc = np.einsum('ij,ij->i', d1, r); B = d1 @ d2
    den = A * E - B * B
    s = np.where(den > 1e-12, np.clip((B * F - Cc * E) / np.where(den > 1e-12, den, 1), 0, 1), 0.0)
    t = (B * s + F) / max(E, 1e-12)
    lo = t < 0; hi = t > 1
    s = np.where(lo, np.clip(-Cc / np.maximum(A, 1e-12), 0, 1), s)
    s = np.where(hi, np.clip((B - Cc) / np.maximum(A, 1e-12), 0, 1), s)
    t = np.clip(t, 0, 1)
    return s, t
def push_segments(X, segs, C, marg, fixed, center=None, Xprev=None):
    I = np.array([sg[0] for sg in segs]); Kk = np.array([sg[1] for sg in segs])
    for (a, b, r0, r1, sg) in C:
        ab = b - a; ax = ab / max(np.linalg.norm(ab), 1e-9)
        s, t = _cseg(X[I], X[Kk], a, b)
        p = X[I] + (X[Kk] - X[I]) * s[:, None]; q = a + t[:, None] * ab
        d = p - q; dist = np.linalg.norm(d, axis=1); rr = r0 + (r1 - r0) * t + marg
        m = dist < rr
        if not m.any(): continue
        if center is not None:
            rad = (p - center) * sg; rad[:, 2] = 0
            rad = rad / np.maximum(np.linalg.norm(rad, axis=1), 1e-9)[:, None]
            rad[:, 2] += P["sim_nahoru"] * (1 - abs(ax[2])) * sg
        else: rad = d
        if Xprev is not None:
            pp = Xprev[I] + (Xprev[Kk] - Xprev[I]) * s[:, None]
            tp = np.clip(((pp - a) @ ab) / (ab @ ab), 0, 1); dpv = pp - (a + tp[:, None] * ab)
            inside_prev = np.linalg.norm(dpv, axis=1) < (r0 + (r1 - r0) * tp + marg) * 0.7
            n = _dir_prev(d, np.where(inside_prev[:, None], 0, dpv), ax, rad)
        else:
            n, _ = _outdir_v(d, ax, rad)
        corr = (q + n * rr[:, None]) - p
        cl = np.linalg.norm(corr, axis=1); corr *= np.minimum(1, P["sim_max_posun"] / np.maximum(cl, 1e-9))[:, None]
        wi = np.where(fixed[I], 0, 1 - s); wk = np.where(fixed[Kk], 0, s)
        tot = wi * wi + wk * wk
        m &= tot >= 0.04
        for j in np.where(m)[0]:
            X[I[j]] += corr[j] * min(wi[j] / tot[j], 1.5); X[Kk[j]] += corr[j] * min(wk[j] / tot[j], 1.5)

# klidové klouby sukně v prostoru pánve
pel_rest = REST["pelvis"]
J0 = []   # (K,4,3)
for j in range(K):
    ch = []
    for k in range(NS): ch.append(np.array(REST[SK[j][k]].translation))
    tail = REST[SK[j][-1]] @ Vector((0, arm.data.bones[SK[j][-1]].length, 0)); ch.append(np.array(tail))
    J0.append(ch)
J0 = np.array(J0)
LEN = np.linalg.norm(J0[:, 1:] - J0[:, :-1], axis=2)                      # (K,3)
RING = np.linalg.norm(J0 - np.roll(J0, -1, 0), axis=2)                     # (K,4) obvodové vzdálenosti
C0 = [np.array(REST[n].translation) for n in COP] + [np.array(REST[COP[-1]] @ Vector((0, arm.data.bones[COP[-1]].length, 0)))]
C0 = np.array(C0); LENC = np.linalg.norm(C0[1:] - C0[:-1], axis=1)
STIFF = np.array(P["sim_tuhost"])   # pro klouby 1..3
def yaw_mat(m):
    f = m.to_3x3() @ Vector((0, 0, 1))   # osa Z kosti pánve ~ dopředu/dozadu
    m3 = m.to_3x3() @ pel_rest.to_3x3().inverted()
    # jen otočení kolem svislé osy
    fwd = m3 @ Vector((0, -1, 0)); fwd.z = 0
    if fwd.length < 1e-4: return Matrix.Identity(3)
    ang = math.atan2(fwd.x, -fwd.y)
    return Matrix.Rotation(ang, 3, 'Z')
GRAV = np.array([0, 0, -9.81])
SEGS = [(j * (NS + 1) + k, j * (NS + 1) + k + 1) for j in range(K) for k in range(NS)] + [(j * (NS + 1) + k, ((j + 1) % K) * (NS + 1) + k) for j in range(K) for k in range(1, NS + 1)]
def sim_action(act):
    anim_util.assign(arm, act)
    for n in [x for ch in SK for x in ch] + COP:
        pb[n].rotation_quaternion = (1, 0, 0, 0); pb[n].location = (0, 0, 0)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    loop = act.name.endswith("_Loop") or act.name in ("Walk_Loop",)
    frames = list(range(f0, f1 + 1))
    passes = 2 if loop else 1
    X = Xp = None; Y = Yp = None
    outS, outC = {}, {}
    dt = 1 / 30 / P["sim_kroky"]
    PRE = P["sim_nabeh"]
    seq = [("pre", f0, i / PRE) for i in range(PRE + 1)] + [(p_, f, 1.0) for p_ in range(passes) for f in frames]
    caps_prev = None
    bpy.context.scene.frame_set(f0)
    base = {b.name: (b.location.copy(), b.rotation_quaternion.copy()) for b in pb}
    newb = set([x for ch in SK for x in ch] + COP)
    for (ps, f, infl) in seq:
        if ps == "pre":
            arm.animation_data.action = None
            for b in pb:
                if b.name in newb: continue
                l, q = base[b.name]; b.location = l * infl; b.rotation_quaternion = Quaternion().slerp(q, infl)
            bpy.context.view_layer.update()
        else:
            if arm.animation_data.action is None: anim_util.assign(arm, act)
            bpy.context.scene.frame_set(f)
        if True:
            mp = M("pelvis"); rel = mp @ pel_rest.inverted()
            root = np.array([rel @ Vector(J0[j, 0]) for j in range(K)])
            yw = yaw_mat(mp); piv = np.array(rel @ Vector((CEN[0], CEN[1], ZJ[0])))
            tgt = np.array([[np.array(yw @ Vector(J0[j, k] - np.array([CEN[0], CEN[1], ZJ[0]]))) + piv for k in range(NS + 1)] for j in range(K)])
            tgt[:, 0] = root
            mh = M("Head"); relh = mh @ REST["Head"].inverted()
            m3 = M("spine_03"); rel3 = m3 @ REST["spine_03"].inverted()
            croot = np.array(relh @ Vector(C0[0]))
            ctgt = np.array([np.array(rel3 @ Vector(c)) for c in C0]); ctgt = ctgt - ctgt[0] + croot
            if X is None:
                X = tgt.copy(); Xp = X.copy(); Y = ctgt.copy(); Yp = Y.copy()
            caps_now = capsules(); bcaps = body_caps()
            if caps_prev is None: caps_prev = caps_now
            nsub = P["sim_kroky"]
            for sub in range(nsub):
                u = (sub + 1) / nsub
                caps = [(a0 + (a1 - a0) * u, b0 + (b1 - b0) * u, r0, r1, sg) for (a0, b0, r0, r1, sg), (a1, b1, _, _, _) in zip(caps_prev, caps_now)]
                X0s = X.reshape(-1, 3).copy()
                V = (X - Xp) * P["sim_tlumeni"]; Xp = X.copy(); X = X + V + GRAV * dt * dt
                X[:, 0] = root
                Y0s = Y.copy()
                Vc = (Y - Yp) * P["sim_tlumeni"]; Yp = Y.copy(); Y = Y + Vc + GRAV * dt * dt; Y[0] = croot
                for it in range(P["sim_iter"]):
                    X[:, 1:] += (tgt[:, 1:] - X[:, 1:]) * STIFF[None, :, None]
                    # vyhlazení posunu po obvodu (žádné ostré přehyby ani překřížení panelů)
                    D = X - tgt; D = D + P["sim_hladke"] * (0.5 * (np.roll(D, 1, 0) + np.roll(D, -1, 0)) - D); X[:, 1:] = (tgt + D)[:, 1:]
                    for k in range(NS):
                        d = X[:, k + 1] - X[:, k]; L = np.linalg.norm(d, axis=1)
                        corr = (d * ((L - LEN[:, k]) / np.maximum(L, 1e-6))[:, None])
                        if k == 0: X[:, 1] -= corr
                        else: X[:, k] += corr * 0.5; X[:, k + 1] -= corr * 0.5
                    for k in range(1, NS + 1):
                        A = X[:, k]; B = np.roll(X[:, k], -1, 0)
                        d = B - A; L = np.linalg.norm(d, axis=1); Lr = RING[:, k]
                        Lt = np.clip(L, Lr * 0.7, Lr * P['sim_obvod_max'])
                        corr = d * ((L - Lt) / np.maximum(L, 1e-6))[:, None] * 0.5
                        X[:, k] += corr; X[np.r_[1:K, 0], k] -= corr
                    fixed = np.zeros(K * (NS + 1), bool); fixed[0::NS + 1] = True
                    flat = X.reshape(-1, 3)
                    cen3 = np.array([piv[0], piv[1], 0.0])
                    if not os.environ.get('NOCOL'): push_points(flat, caps, MARG, fixed, cen3, None)
                    segs = SEGS
                    if not os.environ.get('NOCOL') and not os.environ.get('NOSEG'): push_segments(flat, segs, caps, MARG, fixed, cen3, None)
                    flat[:, 2] = np.maximum(flat[:, 2], 0.012)
                    X = flat.reshape(K, NS + 1, 3)
                    Y[1:] += (ctgt[1:] - Y[1:]) * P["cop_tuhost"]
                    for k in range(len(COP)):
                        d = Y[k + 1] - Y[k]; L = np.linalg.norm(d)
                        corr = d * (L - LENC[k]) / max(L, 1e-6)
                        if k == 0: Y[1] -= corr
                        else: Y[k] += corr * 0.5; Y[k + 1] -= corr * 0.5
                    fc = np.zeros(len(Y), bool); fc[0] = True
                    spc = np.array(M('spine_02').translation); spc[2] = 0
                    push_points(Y, bcaps, 0.028, fc, spc, Y0s)
                    push_points(Y, [c for c in caps if c[4] > 0], 0.028, fc, spc, Y0s)
                    Y[:, 2] = np.maximum(Y[:, 2], 0.02)
            caps_prev = caps_now
            if ps == passes - 1:
                outS[f] = X.copy(); outC[f] = Y.copy()
    return outS, outC, frames

def chain_quats(parent_mat, names_, pts):
    """armature-space klouby -> lokální kvaterniony kostí řetězu"""
    qs = []; Mp = parent_mat
    for k, n in enumerate(names_):
        b = arm.data.bones[n]; par = b.parent
        rel = par.matrix_local.inverted() @ b.matrix_local
        M0 = Mp @ rel
        y0 = (M0.to_3x3() @ Vector((0, 1, 0))).normalized()
        d = Vector(pts[k + 1]) - M0.translation
        if d.length < 1e-6: d = y0
        q = y0.rotation_difference(d.normalized())
        Mr = Matrix.Translation(M0.translation) @ (q.to_matrix() @ M0.to_3x3()).to_4x4()
        loc = (rel.inverted() @ Mp.inverted() @ Mr)
        qs.append(loc.to_quaternion()); Mp = Mr
    return qs

def bake(act, outS, outC, frames):
    data = {}
    for f in frames:
        bpy.context.scene.frame_set(f)
        mp = M("pelvis").copy(); mh = M("Head").copy()
        for j in range(K):
            for n, q in zip(SK[j], chain_quats(mp, SK[j], outS[f][j])): data.setdefault(n, []).append((f, q))
        for n, q in zip(COP, chain_quats(mh, COP, outC[f])): data.setdefault(n, []).append((f, q))
    # odstranit staré křivky nových kostí
    slot = act.slots[0]
    for n, kq in data.items():
        path = f'pose.bones["{n}"].rotation_quaternion'
        for i in range(4):
            fc = act.fcurve_ensure_for_datablock(arm, path, index=i, group_name=n)
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(kq))
            co = []
            prev = None
            for (f, q) in kq:
                if prev is not None and prev.dot(q) < 0: q = -q
                prev = q; co += [f, q[i]]
            fc.keyframe_points.foreach_set("co", co)
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
            fc.update()

acts = anim_util.load_actions()
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_viewport = True
t0 = time.time()
for name, act in sorted(acts.items()):
    if name.endswith(".001"): continue
    if ONLY and not any(o == name for o in ONLY.split(",")): continue
    oS, oC, fr = sim_action(act); bake(act, oS, oC, fr)
    print("SIM", name, len(fr), round(time.time() - t0, 1), flush=True)
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_viewport = False
arm.animation_data.action = None
for n in [x for ch in SK for x in ch] + COP: pb[n].rotation_quaternion = (1, 0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=DST)
