"""Oblékne postavu: python3 outfit.py <muz|kluk> <kroj>
kroje: prosivanice (muž: prošívanice, kapuce s pláštíkem, nohavice, boty, opasek)
       zelena (kluk: zelená kapuce s dagged pláštíkem, kožený kabátek, tunika, nohavice, boty, opasek)
"""
import sys
exec(open("/home/claude/chars/mpfb_boot.py").read())
import bpy, numpy as np, math
sys.path.insert(0, "/home/claude/chars")
import head_features as hf, clothes as cl, cloth_mat as cm

NAME, KROJ = sys.argv[1], sys.argv[2]
import os
_src = f"/home/claude/chars/{NAME}_foto.blend" if os.path.exists(f"/home/claude/chars/{NAME}_foto.blend") else f"/home/claude/chars/{NAME}_head.blend"
bpy.ops.wm.open_mainfile(filepath=_src)
body = bpy.data.objects[NAME]
co, no, W = cl.body_data(body)
L = hf.landmarks(body)
def jc(g):
    w = hf.group_weights(body, g); return co[w > 0.5].mean(0)
pel = jc("joint-pelvis"); knee = jc("joint-l-knee"); ank = jc("joint-l-ankle"); neck = jc("joint-neck")
shl = jc("joint-l-shoulder"); elb = jc("joint-l-elbow"); wri = jc("joint-l-hand")
E = (L["eye_l"] + L["eye_r"]) / 2
H = co[:, 2].max()
print("LM pelvis", pel.round(3), "knee", knee.round(3), "neck", neck.round(3), "H", round(H, 3))
x, y, z = co[:, 0], co[:, 1], co[:, 2]
isbody = W["body"] > 0.5
hand = (W.get("hand_l", 0) + W.get("hand_r", 0) + sum(W.get(f"{f}_0{i}_{s}", 0) for f in ("index", "middle", "ring", "pinky", "thumb") for i in (1, 2, 3) for s in "lr")) > 0.3
headg = (W["head"] > 0.5)
armsall = (W["upperarm_l"] + W["upperarm_r"] + W["lowerarm_l"] + W["lowerarm_r"]) > 0.3
legs = (W["thigh_l"] + W["thigh_r"] + W["calf_l"] + W["calf_r"] + W["foot_l"] + W["foot_r"] + W["ball_l"] + W["ball_r"]) > 0.3

P = dict(
 muz=dict(gamb=(0.105, 0.105, 0.065), hood=(0.075, 0.08, 0.05), hose=(0.04, 0.032, 0.024), boot=(0.045, 0.027, 0.016),
          belt=(0.09, 0.05, 0.025), hem_k=0.16, quilt=46, gamb_off=0.016, dag=(16, 0.32), cape_len=0.26, jerkin=None),
 kluk=dict(gamb=(0.11, 0.12, 0.06), hood=(0.07, 0.11, 0.04), hose=(0.07, 0.05, 0.03), boot=(0.08, 0.045, 0.025),
          belt=(0.1, 0.055, 0.03), hem_k=0.14, quilt=0, gamb_off=0.006, dag=(14, 0.38), cape_len=0.24, jerkin=(0.16, 0.08, 0.035)),
 zena=dict(gamb=(0.045, 0.06, 0.085), hood=None, hose=None, boot=(0.07, 0.045, 0.03), belt=(0.075, 0.05, 0.03),
          hem_k=None, quilt=0, gamb_off=0.004, dag=None, cape_len=0, jerkin=None, flare=0.17, top_smooth=7, belt_up=0.07),
)[NAME]
P.setdefault("flare", 0.05); P.setdefault("top_smooth", 3); P.setdefault("belt_up", 0.0)

hidden = np.zeros(len(co), bool)
objs = []
# --- kabátec / tunika: horní část ze slupky těla
z_hip = pel[2] + 0.04
top = isbody & ~hand & ~headg & (z > z_hip - 0.01) & (z < neck[2]) & ~legs
gamb_up = cl.shell(body, co, no, top, P["gamb_off"], f"{NAME}_kabatec", smooth=P["top_smooth"])
# výstřih a ramena: hladký řez po křivce + podvinutý lem (zena kulatý hlubší, muži úzký u krku)
_ex, _ez, _dzc, _dzt = (0.11, 0.09, -0.02, -0.016) if NAME == "zena" else (0.085, 0.05, -0.005, -0.022)
_zc = neck[2] + _dzc; _zt = neck[2] + _dzt
def _fn(p, ex=_ex, ez=_ez, zc=_zc, zt=_zt):
    e = (p[0] / ex) ** 2 + ((p[2] - zc) / ez) ** 2 - 1.0 + max(0.0, p[1]) * 40.0
    return min(e, (zt - p[2]) * 20.0)
cl.cut_iso(gamb_up, _fn, lip=P["gamb_off"] + 0.002)
_ell = (x / _ex) ** 2 + ((z - _zc) / _ez) ** 2 - 1.0 + np.maximum(0.0, y) * 40.0
hidden |= top & (_ell > 0.8) & ((_zt - z) > -0.004)
# rukávy končí nad zápěstím: vrcholy těla pod úrovní zápěstí (podél paže) už nejsou v masce – řeší hand
# --- sukně kabátce
hem = knee[2] + P["hem_k"] if P["hem_k"] is not None else ank[2] + 0.05
lower = isbody & (z < z_hip + 0.06) & (z > hem - 0.05) & ~hand & ~armsall
skirt, ctr, R, zs = cl.tube(body, co, lower & ~armsall, z_hip + 0.05, hem, f"{NAME}_sukne",
                            N=72, ease=P["gamb_off"] + 0.008, flare=P["flare"], hem_noise=0.006, seed=1)
crotch = jc("joint-l-upper-leg")[2] - 0.05
cl.transfer_weights(skirt, body, co, k=10, pelvis_blend=lambda p: np.clip((crotch + 0.05 - p[:, 2]) / 0.25, 0, 0.55) * 0 + 0.35 * np.clip((z_hip - p[:, 2]) / 0.1, 0, 1))
cl._link(skirt, body)
hidden |= isbody & (z > hem + 0.03) & (z < z_hip + 0.02) & ~hand
gm = cm.fabric(f"{NAME}_kabatec_mat", P["gamb"], kind="quilted" if P["quilt"] else "wool", dirt=0.5,
               dirt_z=(hem - 0.05, hem + 0.35), quilt=P["quilt"], quilt_rings=(elb[2] - 0.35, shl[2] + 0.05, 0.035) if P["quilt"] else None)
for o in (gamb_up, skirt):
    o.data.materials.append(gm)
# kožený kabátek (kluk): kratší slupka přes trup bez rukávů
if P["jerkin"]:
    arms = (W["upperarm_l"] + W["upperarm_r"] + W["lowerarm_l"] + W["lowerarm_r"]) > 0.4
    jt = isbody & ~hand & ~headg & (z > z_hip - 0.02) & (z < neck[2] - 0.02) & ~legs
    jer = cl.shell(body, co, no, jt, P["gamb_off"] + 0.008, f"{NAME}_kabatek", smooth=3)
    _xa = abs(shl[0]) - 0.03
    cl.cut_iso(jer, lambda p: min(_fn(p, ex=0.12, ez=0.11, zc=neck[2] - 0.03, zt=neck[2] - 0.045), (_xa - abs(p[0])) * 20.0), lip=P["gamb_off"] + 0.008)
    jer.data.materials.append(cm.leather(f"{NAME}_kabatek_mat", P["jerkin"], worn=0.6))
    jsk, *_ = cl.tube(body, co, lower & ~armsall, z_hip + 0.05, z_hip - 0.12, f"{NAME}_kabatek_sukne",
                      N=72, ease=P["gamb_off"] + 0.022, flare=0.03, hem_noise=0.004, seed=3)
    cl.transfer_weights(jsk, body, co, k=10); cl._link(jsk, body)
    jsk.data.materials.append(bpy.data.materials[f"{NAME}_kabatek_mat"])
# --- nohavice (punčochy)
if P["hose"]:
    hose_m = isbody & legs & (z < hem + 0.02) & (z > ank[2] + 0.12)
    hose = cl.shell(body, co, no, hose_m, 0.0025, f"{NAME}_nohavice", smooth=1)
    hose.data.materials.append(cm.fabric(f"{NAME}_nohavice_mat", P["hose"], kind="wool", dirt=0.6, dirt_z=(0.0, 0.45)))
    hidden |= hose_m & (z > ank[2] + 0.14)
else:
    hidden |= isbody & legs & (z > ank[2] + 0.06) & (z < hem + 0.03)
# --- boty (po lýtka)
boot_m = isbody & legs & (z < ank[2] + (0.2 if P["hose"] else 0.09))
btop = ank[2] + (0.17 if P["hose"] else 0.065)
bmat = cm.leather(f"{NAME}_boty_mat", P["boot"], dirt=0.8, worn=0.7)
for side, sg in (("l", 1), ("r", -1)):
    bs = boot_m & (x * sg > 0)
    bt, *_ = cl.tube(body, co, bs, btop, 0.0, f"{NAME}_bota_{side}", N=40, rows=14, ease=0.007, hang=False,
                     cap_bottom=True, slice_tol=0.012, row_center=True)
    cl.transfer_weights(bt, body, co, k=8); cl._link(bt, body); bt.data.materials.append(bmat)
hidden |= boot_m & (z < ank[2] + (0.18 if P["hose"] else 0.07))
# --- opasek přes boky
belt, *_ = cl.tube(body, co, (isbody & ~hand & ~armsall & (z < z_hip + 0.2) & (z > z_hip - 0.1)), z_hip + P["belt_up"], z_hip + P["belt_up"] - 0.04, f"{NAME}_opasek",
                   N=72, rows=2, ease=P["gamb_off"] + 0.016 + (0.016 if P["jerkin"] else 0), hang=False)
cl.transfer_weights(belt, body, co, k=12); cl._link(belt, body)
belt.data.materials.append(cm.leather(f"{NAME}_opasek_mat", P["belt"], worn=0.8))
if P["hood"]:
    # --- kapuce: slupka přes hlavu a krk, otvor pro obličej
    face_open = (y < E[1] + 0.06) & (((x / 0.078) ** 2 + ((z - (E[2] - 0.015)) / 0.115) ** 2) < 1.0)
    hood_m = isbody & ((W["head"] + W["neck_01"]) > 0.3) & ~face_open & (z > neck[2] - 0.06)
    hood_m &= ~((y < E[1] + 0.03) & (z < E[2] + 0.05) & (np.abs(x) < 0.09))        # nic přes bradu a ústa
    hood = cl.shell(body, co, no, hood_m, 0.02, f"{NAME}_kapuce", smooth=10, smooth_border=12,
                    offset_fn=lambda c, o: o + 0.025 * max(0.0, (c.z - E[2]) / (H - E[2])) ** 2)
    hm = cm.fabric(f"{NAME}_kapuce_mat", P["hood"], kind="wool", dirt=0.2, dirt_z=(0, 0.2))
    hood.data.materials.append(hm)
    # --- pláštík (kápě) s vykrajovaným okrajem
    cape_sel = isbody & ~hand & ~headg & (z > neck[2] - P["cape_len"] - 0.1) & (z < neck[2] + 0.02) & ~legs
    sh_r = np.linalg.norm(co - shl * np.array([1, 1, 1]), axis=1); sh_l = np.linalg.norm(co - shl * np.array([-1, 1, 1]), axis=1)
    cape_sel &= ~armsall | (np.minimum(sh_r, sh_l) < 0.07)
    cape, *_ = cl.tube(body, co, cape_sel, neck[2] + 0.035, neck[2] - P["cape_len"], f"{NAME}_plastik",
                       N=96, ease=P["gamb_off"] + 0.022, flare=0.04, hang=True, hem_noise=0.0)
    cl.transfer_weights(cape, body, co, k=12); cl._link(cape, body)
    cape.data.materials.append(cm.fabric(f"{NAME}_plastik_mat", P["hood"], kind="wool", dirt=0.25, dirt_z=(0, 0.2), dag=P["dag"]))
cl.hide_body_under(body, hidden)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != body.name:
        for m in o.data.materials:
            if m and m.node_tree and any(n.type == 'BSDF_PRINCIPLED' and n.inputs["Alpha"].is_linked for n in m.node_tree.nodes):
                m.surface_render_method = 'DITHERED' if hasattr(m, "surface_render_method") else None
# vlasy pod kapucí schovat (v .glb budou zvlášť – kapuce se dá sundat)
hair = bpy.data.objects.get(f"{NAME}_vlasy")
if hair and P["hood"]: hair.hide_render = True
_h2 = bpy.data.objects.get(f"{NAME}_vlasy2")
if _h2 and P["hood"]: _h2.hide_render = True
_lh = bpy.data.objects.get(f"{NAME}_rozpustene")
if _lh: _lh.hide_render = True        # náhled s copem; rozpuštěné vlasy jsou v .glb zvlášť
bpy.ops.wm.save_as_mainfile(filepath=f"/home/claude/chars/{NAME}_{KROJ}.blend")
print("OUTFIT OK", [o.name for o in bpy.data.objects if o.type == 'MESH'])
