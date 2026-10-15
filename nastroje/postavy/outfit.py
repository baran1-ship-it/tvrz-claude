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
bpy.ops.wm.open_mainfile(filepath=f"/home/claude/chars/{NAME}_head.blend")
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
 muz=dict(gamb=(0.105, 0.105, 0.065), hood=(0.075, 0.08, 0.05), hose=(0.06, 0.045, 0.03), boot=(0.07, 0.04, 0.022),
          belt=(0.09, 0.05, 0.025), hem_k=0.16, quilt=46, gamb_off=0.016, dag=(16, 0.32), cape_len=0.26, jerkin=None),
 kluk=dict(gamb=(0.11, 0.12, 0.06), hood=(0.07, 0.11, 0.04), hose=(0.07, 0.05, 0.03), boot=(0.08, 0.045, 0.025),
          belt=(0.1, 0.055, 0.03), hem_k=0.14, quilt=0, gamb_off=0.006, dag=(14, 0.38), cape_len=0.24, jerkin=(0.16, 0.08, 0.035)),
)[NAME]

hidden = np.zeros(len(co), bool)
objs = []
# --- kabátec / tunika: horní část ze slupky těla
z_hip = pel[2] + 0.04
top = isbody & ~hand & ~headg & (z > z_hip - 0.01) & (z < neck[2] - 0.035) & ~legs
gamb_up = cl.shell(body, co, no, top, P["gamb_off"], f"{NAME}_kabatec", smooth=3)
hidden |= top & (z < neck[2] - 0.05)
# rukávy končí nad zápěstím: vrcholy těla pod úrovní zápěstí (podél paže) už nejsou v masce – řeší hand
# --- sukně kabátce
hem = knee[2] + P["hem_k"]
lower = isbody & (z < z_hip + 0.06) & (z > hem - 0.05) & ~hand & ~armsall
skirt, ctr, R, zs = cl.tube(body, co, lower & ~armsall, z_hip + 0.05, hem, f"{NAME}_sukne",
                            N=72, ease=P["gamb_off"] + 0.008, flare=0.05, hem_noise=0.006, seed=1)
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
    jt = isbody & ~arms & ~hand & ~headg & (z > z_hip - 0.02) & (z < neck[2] - 0.05) & ~legs
    jer = cl.shell(body, co, no, jt, P["gamb_off"] + 0.008, f"{NAME}_kabatek", smooth=3)
    jer.data.materials.append(cm.leather(f"{NAME}_kabatek_mat", P["jerkin"], worn=0.6))
    jsk, *_ = cl.tube(body, co, lower & ~armsall, z_hip + 0.05, z_hip - 0.12, f"{NAME}_kabatek_sukne",
                      N=72, ease=P["gamb_off"] + 0.022, flare=0.03, hem_noise=0.004, seed=3)
    cl.transfer_weights(jsk, body, co, k=10); cl._link(jsk, body)
    jsk.data.materials.append(bpy.data.materials[f"{NAME}_kabatek_mat"])
# --- nohavice (punčochy)
hose_m = isbody & legs & (z < hem + 0.02) & (z > ank[2] + 0.12)
hose = cl.shell(body, co, no, hose_m, 0.0025, f"{NAME}_nohavice", smooth=1)
hose.data.materials.append(cm.fabric(f"{NAME}_nohavice_mat", P["hose"], kind="wool", dirt=0.6, dirt_z=(0.0, 0.45)))
hidden |= hose_m & (z > ank[2] + 0.14)
# --- boty (po lýtka)
boot_m = isbody & legs & (z < ank[2] + 0.2)
boot = cl.shell(body, co, no, boot_m, 0.006, f"{NAME}_boty", smooth=6)
boot.data.materials.append(cm.leather(f"{NAME}_boty_mat", P["boot"], dirt=0.8, worn=0.7))
hidden |= boot_m & (z < ank[2] + 0.18)
# --- opasek přes boky
belt, *_ = cl.tube(body, co, lower & ~armsall, z_hip + 0.0, z_hip - 0.045, f"{NAME}_opasek",
                   N=72, rows=2, ease=P["gamb_off"] + 0.016 + (0.016 if P["jerkin"] else 0), hang=False)
cl.transfer_weights(belt, body, co, k=12); cl._link(belt, body)
belt.data.materials.append(cm.leather(f"{NAME}_opasek_mat", P["belt"], worn=0.8))
# --- kapuce: slupka přes hlavu a krk, otvor pro obličej
face_open = (y < E[1] + 0.055) & (z < E[2] + 0.075) & (z > L["jaw"][2] - 0.05) & (np.abs(x) < 0.075)
hood_m = isbody & ((W["head"] + W["neck_01"]) > 0.3) & ~face_open & (z > neck[2] - 0.06)
hood_m &= ~((y < E[1] + 0.03) & (z < E[2] + 0.05))        # nic přes bradu a ústa
hood = cl.shell(body, co, no, hood_m, 0.02, f"{NAME}_kapuce", smooth=10,
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
if hair: hair.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=f"/home/claude/chars/{NAME}_{KROJ}.blend")
print("OUTFIT OK", [o.name for o in bpy.data.objects if o.type == 'MESH'])
