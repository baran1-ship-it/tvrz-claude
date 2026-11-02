"""Hlídač geometrie (test smyslu, vrstva 1 – Havran „levitující tráva, cesta pod mostem“; Míša 2. 11.: most není po zem,
kvádry visí na skále): každý samostatný kus sítě (ostrov) ve hotových modelech musí stát na terénu, nebo se dotýkat kusu,
který stojí (řetěz opor). Ostrov bez opory = visí ve vzduchu. Druhá kontrola: kus zapadlý celý pod terénem (zbytečný/
chyba výšky). Pravidla a výjimky v pravidla/svet/kontroly.json (geometrie). Výsledek build/kontrola_geometrie.json.
  /opt/bl/bin/python blender/kontrola_geometrie.py <koren>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrady as H
import numpy as np
import bpy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
K = H.K
KC = json.load(open(os.path.join(K, "pravidla/svet/kontroly.json")))["geometrie"]
vysl = {"popis": "ostrovy sítí bez opory (visí) a celé pod terénem – blender/kontrola_geometrie.py", "soubory": {}}
for soubor in KC["soubory"]:
    cesta = os.path.join(K, soubor)
    if not os.path.exists(cesta): continue
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    bpy.ops.import_scene.gltf(filepath=cesta)
    V, F, jm = [], [], []
    off = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or any(ob.name.startswith(p) for p in KC["vynechat_objekty"]): continue
        me = ob.data; mw = ob.matrix_world
        v = np.array([tuple(mw @ x.co) for x in me.vertices], float)
        if not len(v): continue
        # Blender Z nahoru -> hra: x = x, y = z, z = -y
        v = np.c_[v[:, 0], v[:, 2], -v[:, 1]]
        for p in me.polygons:
            vs = list(p.vertices); F += [(off + vs[0], off + q) for q in vs[1:]]
        V.append(v); off += len(v); jm.append(ob.name)
    V = np.vstack(V); E = np.array(F)
    # glTF rozdělí vrcholy podle UV a normál (každá stěna kvádru = vlastní ostrov) → svařit podle polohy (1 mm)
    _, svar = np.unique(np.round(V * 1000).astype(np.int64), axis=0, return_inverse=True); svar = svar.ravel()
    n = len(V); E2 = np.r_[E, np.c_[np.arange(n), n + svar]]
    g = coo_matrix((np.ones(len(E2)), (E2[:, 0], E2[:, 1])), shape=(n + svar.max() + 1,) * 2)
    nc, lab = connected_components(g, directed=False); lab = lab[:n]
    _, lab = np.unique(lab, return_inverse=True); nc = lab.max() + 1
    lo = np.full((nc, 3), 1e9); hi = np.full((nc, 3), -1e9)
    np.minimum.at(lo, lab, V); np.maximum.at(hi, lab, V)
    # opora od terénu: nejnižší body ostrova (do 5 cm od jeho dna) do tolerance nad terénem, nebo pod terénem
    stoji = np.zeros(nc, bool); pod = np.zeros(nc, bool)
    ter_v = np.array([H.ter(x, z) for x, z in V[:, [0, 2]]])
    nad = V[:, 1] - ter_v
    min_nad = np.full(nc, 1e9); np.minimum.at(min_nad, lab, nad)
    max_nad = np.full(nc, -1e9); np.maximum.at(max_nad, lab, nad)
    stoji = min_nad <= KC["tolerance_teren_m"]
    pod = max_nad < -KC["pod_terenem_m"]
    # opora paprsky (BVH celé sítě): z nejnižších bodů ostrova (do 5 cm nad jeho dnem) paprsek dolů a do 4 stran do
    # tolerance_dotyk_m; zásah cizí geometrie nebo terén do tolerance = opora. (AABB dotyk byl benevolentní – celá skála
    # je jeden ostrov a „dotýkala se“ všeho.)
    from mathutils import Vector as Vb
    from mathutils.bvhtree import BVHTree
    tri = []
    for f0, f1 in zip(E[:-1], E[1:]): pass
    polys = []; k = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or any(ob.name.startswith(p) for p in KC["vynechat_objekty"]): continue
        for p in ob.data.polygons: polys.append([k + q for q in p.vertices])
        k += len(ob.data.vertices)
    bvh = BVHTree.FromPolygons([Vb(v) for v in V], polys, all_triangles=False)
    plab = np.array([lab[pp[0]] for pp in polys])
    t = KC["tolerance_dotyk_m"]; dno = lo[lab, 1]
    spodni = np.nonzero(V[:, 1] <= dno + 0.05)[0]
    smery = [Vb((0, -1, 0)), Vb((1, 0, 0)), Vb((-1, 0, 0)), Vb((0, 0, 1)), Vb((0, 0, -1))]
    from collections import defaultdict
    opira = defaultdict(set)   # i -> ostrovy, o které se i opírá
    for vi in spodni:
        i = lab[vi]; p0 = Vb(V[vi])
        for sm in smery:
            hit = bvh.ray_cast(p0 + sm * 0.005, sm, t)
            if hit[0] is not None and plab[hit[2]] != i: opira[i].add(int(plab[hit[2]]))
    # druhá opora: průnik geometrie (střecha na zdi, podlaha zapuštěná do zdi, trám ve zdi) – BVH ostrova × celé sítě,
    # jen pro ostrovy bez opory z paprsků (jinak drahé)
    bez = [i for i in range(nc) if not stoji[i] and not opira.get(i) and (hi[i] - lo[i]).max() >= KC["min_velikost_m"]]
    pol_ostrova = defaultdict(list)
    for pi, l in enumerate(plab): pol_ostrova[int(l)].append(pi)
    for i in bez:
        pp = pol_ostrova[i]
        bi = BVHTree.FromPolygons([Vb(v) for v in V], [polys[q] for q in pp], all_triangles=False)
        for _, b2 in bi.overlap(bvh):
            j = int(plab[b2])
            if j != i: opira[i].add(j)
    # třetí opora: kterýkoli bod ostrova blíž než tolerance_dotyk k cizí geometrii (střecha položená na hraně zdi)
    for i in bez:
        if opira.get(i): continue
        vv = np.nonzero(lab == i)[0]
        for vi in vv[:: max(1, len(vv) // 300)]:
            for _, _, pi, _ in bvh.find_nearest_range(Vb(V[vi]), t):
                j = int(plab[pi])
                if j != i: opira[i].add(j)
            if opira.get(i): break
    # šíření od terénu: i stojí, když se opírá o stojící (opora i průnikem v obou směrech: zeď drží střechu i naopak)
    nese = defaultdict(set)
    for i, js in opira.items():
        for j in js: nese[j].add(i); nese[i].add(j) if i in bez else None
    op = stoji.copy(); fr = list(np.nonzero(stoji)[0])
    while fr:
        j = fr.pop()
        for i in nese[j]:
            if not op[i]: op[i] = True; fr.append(i)
    velikost = (hi - lo).max(1)
    visi = np.nonzero(~op & (velikost >= KC["min_velikost_m"]))[0]
    pod_t = np.nonzero(pod & (velikost >= KC["min_velikost_m"]))[0]
    vysl["soubory"][soubor] = {"ostrovu": int(nc),
        "visi": [{"stred": [round(float(c), 2) for c in (lo[i] + hi[i]) / 2], "rozmer": [round(float(c), 2) for c in hi[i] - lo[i]],
                  "nad_terenem_m": round(float(min_nad[i]), 2)} for i in visi[:200]], "visi_pocet": int(len(visi)),
        "pod_terenem": [{"stred": [round(float(c), 2) for c in (lo[i] + hi[i]) / 2]} for i in pod_t[:50]], "pod_terenem_pocet": int(len(pod_t))}
    print("GEOMETRIE", soubor, "ostrovů", nc, "visí", len(visi), "pod terénem", len(pod_t))
json.dump(vysl, open(os.path.join(K, "build/kontrola_geometrie.json"), "w"), ensure_ascii=False, indent=1)
