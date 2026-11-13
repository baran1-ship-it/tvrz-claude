"""Test prořezů přes všechny animace UAL1+UAL2.
Nohy (punčochy) ven ze sukně = prořez, pokud nejbližší místo sukně není u lemu.
Ruce uvnitř sukně = prořez. Výstup: JSON s výsledky + souhrn."""
import sys, json, time; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import anim_util, numpy as np, bmesh
from mathutils.bvhtree import BVHTree
blend = sys.argv[sys.argv.index("--") + 1]; outj = sys.argv[sys.argv.index("--") + 2]
STEP = int(os.environ.get("STEP", "4")); ONLY = os.environ.get("ONLY", "")
bpy.ops.wm.open_mainfile(filepath=blend)
arm = bpy.data.objects["zena30_kostra"]
acts = anim_util.load_actions()
sk = bpy.data.objects["zena30_sukne"]; body = bpy.data.objects["zena30_telo"]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in (sk, body): o.hide_viewport = True; o.hide_set(True)
# řady sukně podle výšky v klidu
rest = np.array([v.co[:] for v in sk.data.vertices]); zr = np.unique(np.round(rest[:, 2], 4))[::-1]
row = {z: i for i, z in enumerate(zr)}; nrows = len(zr)
vrow = np.array([row[round(z, 4)] for z in rest[:, 2]])
frow = np.array([vrow[list(p.vertices)].max() for p in sk.data.polygons])
brest = np.array([v.co[:] for v in body.data.vertices])
names = [g.name for g in body.vertex_groups]
def gidx(*bn):
    s = np.zeros(len(brest))
    for v in body.data.vertices:
        for g in v.groups:
            if names[g.group].startswith(bn): s[v.index] += g.weight
    return s
legw = gidx("calf", "thigh"); handw = gidx("hand", "index", "middle", "ring", "pinky", "thumb")
LEG = np.where((legw > 0.5) & (brest[:, 2] > 0.09))[0]
HAND = np.where(handw > 0.5)[0]
dg = bpy.context.evaluated_depsgraph_get()
res = {}
t0 = time.time()
for name, act in sorted(acts.items()):
    if ONLY and not any(o == name for o in ONLY.split(',')): continue
    anim_util.assign(arm, act)
    f0, f1 = map(int, act.frame_range)
    worst_leg = 0; worst_hand = 0; bad_frames = 0; nf = 0; worst_f = None
    for f in range(f0, f1 + 1, STEP):
        bpy.context.scene.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        se = sk.evaluated_get(dg); me = se.to_mesh()
        V = [se.matrix_world @ v.co for v in me.vertices]
        tri = [list(p.vertices) for p in me.polygons]
        bvh = BVHTree.FromPolygons(V, tri); se.to_mesh_clear()
        be = body.evaluated_get(dg); bm_ = be.to_mesh(); BV = [be.matrix_world @ v.co for v in bm_.vertices]; be.to_mesh_clear()
        leg_pen = 0; hand_pen = 0
        for i in LEG:
            p = BV[i]; loc, n, fi, d = bvh.find_nearest(p, 0.4)
            if loc is None: continue
            s = (p - loc).dot(n)
            if s > 0.004 and frow[fi] < nrows - 2: leg_pen = max(leg_pen, s)
        for i in HAND:
            p = BV[i]; loc, n, fi, d = bvh.find_nearest(p, 0.15)
            if loc is None: continue
            s = (p - loc).dot(n)
            if s < -0.006 and frow[fi] > 2: hand_pen = max(hand_pen, -s)
        nf += 1
        if leg_pen > 0.01 or hand_pen > 0.01: bad_frames += 1
        if leg_pen + hand_pen > worst_leg + worst_hand: worst_f = f
        worst_leg = max(worst_leg, leg_pen); worst_hand = max(worst_hand, hand_pen)
    res[name] = dict(noha_cm=round(worst_leg * 100, 1), ruka_cm=round(worst_hand * 100, 1), spatne=bad_frames, snimku=nf, nejhorsi=worst_f)
    print(f"{name:40s} noha {worst_leg*100:5.1f} cm  ruka {worst_hand*100:5.1f} cm  špatně {bad_frames}/{nf}", flush=True)
json.dump(res, open(outj, "w"), indent=1, ensure_ascii=False)
print("ČAS", round(time.time() - t0), "s; animací", len(res))
