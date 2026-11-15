"""LOD navaznost dilu (Puchart test_smyslu lod_navaznost, docs/rozpracovane/hlidaci_z_pucharta.md #11): LOD1 dilu
(modely/<dil>/<x>_lod1.glb) ma obal jako LOD0 - rohy obalu (bez kolizi -colonly) do max_obal_m, jinak dum pri prepnuti
LOD poskoci / zmensi se. Dvojice a prah v pravidla/svet/kontroly.json lod_navaznost. Chybejici .glb = NEOVERENO (vypis).
Navaznost dosahu (LOD0 konci, LOD1 zacina) hlida hra testem lod_mezera.
  /opt/bl/bin/python tools/kontrola_lod.py      rc 1 = rozdil obalu nad prah"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KC = json.load(open(os.path.join(ROOT, "pravidla", "svet", "kontroly.json"), encoding="utf-8"))["lod_navaznost"]
VYN = json.load(open(os.path.join(ROOT, "pravidla", "svet", "kontroly.json"), encoding="utf-8"))["geometrie"]["vynechat_obsahuje"]


def obal(cesta):
    import bpy
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    bpy.ops.import_scene.gltf(filepath=cesta)
    P = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or any(s in ob.name for s in VYN if s != "lod1"):
            continue
        mw = ob.matrix_world
        P += [tuple(mw @ v.co) for v in ob.data.vertices]
    P = np.array(P).reshape(-1, 3)
    P = np.c_[P[:, 0], P[:, 2], -P[:, 1]]
    return P.min(0), P.max(0)


chyby, neov = [], []
for a, b in KC["pary"]:
    pa, pb = os.path.join(ROOT, a), os.path.join(ROOT, b)
    if not (os.path.exists(pa) and os.path.exists(pb)):
        neov.append(a)
        print("LOD %s / %s chybi - NEOVERENO" % (a, b))
        continue
    lo0, hi0 = obal(pa)
    lo1, hi1 = obal(pb)
    d = float(max(np.abs(lo0 - lo1).max(), np.abs(hi0 - hi1).max()))
    print("LOD %s: obal LOD0 %s..%s, LOD1 %s..%s, nejvetsi rozdil rohu %.2f m" % (os.path.basename(a), np.round(lo0, 2).tolist(), np.round(hi0, 2).tolist(),
                                                                              np.round(lo1, 2).tolist(), np.round(hi1, 2).tolist(), d))
    if d > KC["max_obal_m"]:
        chyby.append("%s: LOD1 obal se lisi o %.2f m (> %.2f)" % (a, d, KC["max_obal_m"]))
for c in chyby:
    print("LOD CHYBA " + c)
print("lod_navaznost: dvojic %d, chyb %d, neovereno %d" % (len(KC["pary"]), len(chyby), len(neov)))
sys.exit(1 if chyby else 0)
