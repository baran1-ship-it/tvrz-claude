"""Hlídač vody (Míša 5. 11.: „někde chybí voda, pracujeme s reálnými daty, tohle se nemá dít“): po ose každého toku po 1 m
paprsek shora na hladinu (hra/modely/voda.glb, materiál voda) a na viditelný terén (hra/data/vysek_sit.r16): chyba = v ose
toku není hladina, nebo je viditelný terén nad ní (voda schovaná). Spouští Blender (BVH):
  /opt/bl/bin/python nastroje/kontrola_vody.py <koren>"""
import sys, os, json
import numpy as np
K = sys.argv[-1] if len(sys.argv) > 1 else "."
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(K, "hra/modely/voda.glb"))
V_ = []; F_ = []
for o in bpy.data.objects:
    if o.type != "MESH" or not o.name.startswith("VODA_") or o.name.startswith("VODA_DALEKO"): continue
    b = len(V_); V_ += [o.matrix_world @ v.co for v in o.data.vertices]; F_ += [[b + i for i in p.vertices] for p in o.data.polygons]
bvh = BVHTree.FromPolygons(V_, F_)
VI = json.load(open(os.path.join(K, "hra/data/vysek.json")))
sit = np.fromfile(os.path.join(K, "hra/data/vysek_sit.r16"), "<u2").reshape(VI["vyska"], VI["sirka"]) / 200.0 + 300.0 - VI["pocatek_H"]
def ter(x, z):   # viditelná síť dlaždic: trojúhelníky po 2 m (LOD0) – lineárně z rohů buňky 2 m
    c = (x - VI["x0_hra"]) / 2.0; r = (z - VI["z0_hra"]) / 2.0; c0 = int(c); r0 = int(r); fc = c - c0; fr = r - r0
    a = sit[r0 * 2, c0 * 2]; b = sit[r0 * 2, c0 * 2 + 2]; cc = sit[r0 * 2 + 2, c0 * 2]; d = sit[r0 * 2 + 2, c0 * 2 + 2]
    return a + fc * (b - a) + fr * (cc - a) if fc + fr <= 1 else d + (1 - fc) * (cc - d) + (1 - fr) * (b - d)
TH = json.load(open(os.path.join(K, "hra/data/toky_hladina.json")))["toky"]
chyb = []; n = 0
for k, t in TH.items():
    o = np.array(t["osa"])
    for x, z, hl in o[::2]:
        if not (VI["x0_hra"] + 5 < x < VI["x0_hra"] + VI["sirka"] - 5 and VI["z0_hra"] + 5 < z < VI["z0_hra"] + VI["vyska"] - 5): continue
        n += 1
        h = bvh.ray_cast(Vector((x, -z, hl + 5.0)), Vector((0, 0, -1)), 10.0)   # Blender: y = −z_hra, z = výška
        tv = ter(x, z)
        if h[0] is None: chyb.append((k, round(x, 1), round(z, 1), "bez hladiny"))
        elif tv > h[0].z + 0.02: chyb.append((k, round(x, 1), round(z, 1), "terén nad hladinou %.2f m" % (tv - h[0].z)))
from collections import Counter
print("VODA bodů osy %d, chyb %d" % (n, len(chyb)), Counter(c[3].split(" ")[0] for c in chyb))
for c in chyb[:15]: print("  ", c)
json.dump({"chyby": chyb}, open(os.path.join(K, "build/kontrola_vody.json"), "w"))
