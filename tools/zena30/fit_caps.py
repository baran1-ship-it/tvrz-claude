"""Kapsle kolizí přesně podle těla: osa = těžiště řezů v prostoru kosti, poloměr = max vzdálenost (konce)."""
import sys, json; sys.path.insert(0, "/home/claude/z30/scripts")
from common import *
import numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/claude/z30/head.blend")
b = bpy.data.objects["zena30_telo"]; a = bpy.data.objects["zena30_kostra"]
V = np.array([b.matrix_world @ v.co for v in b.data.vertices])
out = {}
groups = {"thigh": ["thigh"], "calf": ["calf"], "foot": ["foot", "ball"], "lowerarm": ["lowerarm"], "hand": ["hand", "index", "middle", "ring", "pinky", "thumb"]}
for side in "lr":
    for key, pre in groups.items():
        bn = f"{key}_{side}"; bb = a.data.bones[bn]; Mi = bb.matrix_local.inverted()
        gids = [g.index for g in b.vertex_groups if any(g.name.startswith(p) for p in pre) and g.name.endswith("_" + side)]
        w = np.zeros(len(V))
        for v in b.data.vertices:
            for g in v.groups:
                if g.group in gids: w[v.index] += g.weight
        P = V[w > 0.5]
        L = np.array([Mi @ Vector(p) for p in P])     # y = podél kosti
        ys = L[:, 1]; lo, hi = np.percentile(ys, 3), np.percentile(ys, 97)
        def cen(y0, y1):
            m = (ys >= y0) & (ys <= y1); return L[m][:, [0, 2]].mean(0)
        span = hi - lo
        c0 = cen(lo, lo + span * 0.3); c1 = cen(hi - span * 0.3, hi)
        A = np.array([c0[0], lo, c0[1]]); B = np.array([c1[0], hi, c1[1]])
        ab = B - A; t = np.clip(((L - A) @ ab) / (ab @ ab), 0, 1); d = np.linalg.norm(L - (A + t[:, None] * ab), axis=1)
        r0 = max(np.percentile(d[t < 0.35], 95) if (t < 0.35).any() else d.max(), np.percentile(d[(t >= 0.2) & (t < 0.6)], 97) if ((t >= 0.2) & (t < 0.6)).any() else 0)
        r1 = np.percentile(d[t > 0.65], 95) if (t > 0.65).any() else d.max()
        if key == "calf":
            rb = [np.percentile(d[(t >= lo_) & (t < lo_ + 0.25)], 98) for lo_ in (0, 0.25, 0.5, 0.75)]
            M_ = A + (B - A) * 0.5
            out[bn] = dict(a=A.tolist(), b=M_.tolist(), r0=float(max(rb[0], rb[1])), r1=float(max(rb[1], rb[2])))
            out[bn + "_dol"] = dict(a=M_.tolist(), b=B.tolist(), r0=float(max(rb[1], rb[2])), r1=float(rb[3]), bone=bn)
            print(bn, "profil", np.round(rb, 3)); continue
        out[bn] = dict(a=A.tolist(), b=B.tolist(), r0=float(r0), r1=float(r1))
        print(bn, np.round(A, 3), np.round(B, 3), round(r0, 3), round(r1, 3))
json.dump(out, open("/home/claude/z30/caps.json", "w"), indent=1)
