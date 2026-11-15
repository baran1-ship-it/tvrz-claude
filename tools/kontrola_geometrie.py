"""Hlidac geometrie (Puchart blender/kontrola_geometrie.py, docs/rozpracovane/hlidaci_z_pucharta.md #1): kazdy samostatny kus
site (ostrov po svareni vrcholu) v hotovych modelech musi stat na terenu, nebo se dotykat kusu, ktery stoji (retez opor
od zeme). Ostrov bez opory = visi ve vzduchu (strecha, tram, lavice, dil mostu, lano studny). Druha kontrola: cely kus
vic nez pod_terenem_m pod terenem. Prahy a soubory: pravidla/svet/kontroly.json geometrie; nalezy prochazi rohatkou
(tools/rohatka.py, schvalene.geometrie) - novy nalez = rc 1. Vysledek build/kontrola_geometrie.json.

  /opt/bl/bin/python tools/kontrola_geometrie.py [soubor.glb ...]      (bez argumentu soubory z kontroly.json)
  KONTROLA_DBG=x,y,z  vypise ostrovy u bodu (souradnice hry) s oporami

Opory (jako Puchart): 1) paprsky z nejnizsich bodu ostrova dolu a do 4 stran do tolerance_dotyk_m; 2) prunik BVH ostrova
s celou siti; 3) bod ostrova blize nez tolerance_dotyk_m k cizi geometrii; 4) bod ostrova uvnitr cizi uzavrene site.
Sireni od terenu v obou smerech (zed drzi strechu i naopak), 2. kolo pro ostrovy, ktere se opiraly jen o sebe."""
import json
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rohatka  # noqa: E402

KJ = json.load(open(os.path.join(ROOT, "pravidla", "svet", "kontroly.json"), encoding="utf-8"))
KC = KJ["geometrie"]


def teren_fn(druh):
    if druh == "rovina":
        return lambda x, z: np.zeros_like(x)
    vys = json.load(open(os.path.join(ROOT, "tools", "krok_b", "vysky.json")))
    H = np.array(vys["h"], float).reshape(vys["nz"], vys["nx"])

    def f(x, z):
        i = np.clip(np.round((x - vys["X0"]) / vys["K"]).astype(int), 0, vys["nx"] - 1)
        j = np.clip(np.round((z - vys["Z0"]) / vys["K"]).astype(int), 0, vys["nz"] - 1)
        return H[j, i]
    return f


def komponenty(n, E):
    """souvisle komponenty grafu (n uzlu, hrany E) bez scipy: pripojovani korenu + zkracovani cest"""
    par = np.arange(n)
    a, b = E[:, 0], E[:, 1]
    while True:
        while True:
            p2 = par[par]
            if np.array_equal(p2, par):
                break
            par = p2
        ra, rb = par[a], par[b]
        m = ra != rb
        if not m.any():
            break
        lo, hi = np.minimum(ra[m], rb[m]), np.maximum(ra[m], rb[m])
        np.minimum.at(par, hi, lo)
    _, lab = np.unique(par, return_inverse=True)
    return lab.ravel()


def kontrola(cesta, druh_terenu):
    import bpy
    from mathutils import Vector as Vb
    from mathutils.bvhtree import BVHTree
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    bpy.ops.import_scene.gltf(filepath=cesta)
    obj = [ob for ob in bpy.data.objects if ob.type == "MESH" and not any(ob.name.startswith(p) for p in KC["vynechat_objekty"])
           and not any(s in ob.name for s in KC["vynechat_obsahuje"])]
    V, polys, off = [], [], 0
    for ob in obj:
        me = ob.data
        mw = ob.matrix_world
        v = np.array([tuple(mw @ x.co) for x in me.vertices], float).reshape(-1, 3)
        if not len(v):
            continue
        V.append(np.c_[v[:, 0], v[:, 2], -v[:, 1]])        # Blender Z nahoru -> hra (x, y = z, z = -y)
        polys += [[off + q for q in p.vertices] for p in me.polygons]
        off += len(v)
    if not V:
        return None
    V = np.vstack(V)
    n = len(V)
    E = np.array([(pp[0], q) for pp in polys for q in pp[1:]], np.int64)
    # glTF deli vrcholy podle UV a normal (kazda stena kvadru = vlastni ostrov) -> svarit podle polohy (svar_mm)
    _, svar = np.unique(np.round(V * 1000.0 / KC["svar_mm"]).astype(np.int64), axis=0, return_inverse=True)
    svar = svar.ravel()
    E2 = np.r_[E, np.c_[np.arange(n), n + svar]]
    lab = komponenty(n + svar.max() + 1, E2)[:n]
    _, lab = np.unique(lab, return_inverse=True)
    lab = lab.ravel()
    nc = lab.max() + 1
    lo = np.full((nc, 3), 1e9)
    hi = np.full((nc, 3), -1e9)
    np.minimum.at(lo, lab, V)
    np.maximum.at(hi, lab, V)
    ter = teren_fn(druh_terenu)
    nad = V[:, 1] - ter(V[:, 0], V[:, 2])
    min_nad = np.full(nc, 1e9)
    np.minimum.at(min_nad, lab, nad)
    max_nad = np.full(nc, -1e9)
    np.maximum.at(max_nad, lab, nad)
    stoji = min_nad <= KC["tolerance_teren_m"]
    pod = max_nad < -KC["pod_terenem_m"]
    bvh = BVHTree.FromPolygons([Vb(v) for v in V], polys, all_triangles=False)
    plab = np.array([lab[pp[0]] for pp in polys])
    t = KC["tolerance_dotyk_m"]
    dno = lo[lab, 1]
    spodni = np.nonzero(V[:, 1] <= dno + 0.05)[0]
    smery = [Vb((0, -1, 0)), Vb((1, 0, 0)), Vb((-1, 0, 0)), Vb((0, 0, 1)), Vb((0, 0, -1))]
    opira = defaultdict(set)
    for vi in spodni:
        i = lab[vi]
        if stoji[i]:
            continue
        p0 = Vb(V[vi])
        for sm in smery:
            hit = bvh.ray_cast(p0 + sm * 0.005, sm, t)
            if hit[0] is not None and plab[hit[2]] != i:
                opira[i].add(int(plab[hit[2]]))
    velikost = (hi - lo).max(1)
    pol_ostrova = defaultdict(list)
    for pi, l_ in enumerate(plab):
        pol_ostrova[int(l_)].append(pi)
    vz = KC["vzorek_bodu"]

    def dopln(bez, nove):
        for i in bez:
            bi = BVHTree.FromPolygons([Vb(v) for v in V], [polys[q] for q in pol_ostrova[i]], all_triangles=False)
            for _, b2 in bi.overlap(bvh):
                j = int(plab[b2])
                if j != i:
                    opira[i].add(j)
        for i in bez:
            if opira.get(i) and i not in nove:
                continue
            vv = np.nonzero(lab == i)[0]
            for vi in vv[:: max(1, len(vv) // vz)]:
                for _, _, pi, _ in bvh.find_nearest_range(Vb(V[vi]), t):
                    j = int(plab[pi])
                    if j != i:
                        opira[i].add(j)
                if opira.get(i) and i not in nove:
                    break
        for i in bez:
            if opira.get(i) and i not in nove:
                continue
            vv = np.nonzero(lab == i)[0]
            for vi in vv[:: max(1, len(vv) // vz)]:
                p0 = Vb(V[vi])
                for sm in smery[1:]:
                    hit = bvh.ray_cast(p0, sm, 5.0)
                    if hit[0] is not None and plab[hit[2]] != i and hit[1].dot(sm) > 0.5:
                        opira[i].add(int(plab[hit[2]]))
                        break
                if opira.get(i) and i not in nove:
                    break

    bez = [i for i in range(nc) if not stoji[i] and not opira.get(i) and velikost[i] >= KC["min_velikost_m"]]
    dopln(bez, set())

    def sir(bez_s):
        nese = defaultdict(set)
        for i, js in opira.items():
            for j in js:
                nese[j].add(i)
                if i in bez_s:
                    nese[i].add(j)
        op = stoji.copy()
        fr = list(np.nonzero(stoji)[0])
        while fr:
            j = fr.pop()
            for i in nese[j]:
                if not op[i]:
                    op[i] = True
                    fr.append(i)
        return op, nese
    op, nese = sir(set(bez))
    zbyva = [i for i in range(nc) if not op[i] and velikost[i] >= KC["min_velikost_m"]]
    if zbyva:
        bez = sorted(set(bez) | set(zbyva))
        dopln(zbyva, set(zbyva))
        op, nese = sir(set(bez))
    if os.environ.get("KONTROLA_DBG"):
        q_ = np.array([float(c) for c in os.environ["KONTROLA_DBG"].split(",")])
        for i in np.nonzero(np.all((lo - 0.6 <= q_) & (q_ <= hi + 0.6), axis=1))[0]:
            print("DBGOSTROV", i, np.round(lo[i], 2).tolist(), np.round(hi[i], 2).tolist(), "stoji", bool(stoji[i]), "op", bool(op[i]),
                  "opira", sorted(opira.get(i, []))[:8], "nese", sorted(nese.get(i, []))[:8], flush=True)
    visi = np.nonzero(~op & (velikost >= KC["min_velikost_m"]))[0]
    pod_t = np.nonzero(pod & (velikost >= KC["min_velikost_m"]))[0]
    # jmeno objektu ostrova (prvni polygon) - kde hledat v Blenderu
    jm_vrch = []
    for ob in obj:
        jm_vrch += [ob.name] * len(ob.data.vertices)
    jm = {int(lab[vi]): jm_vrch[vi] for vi in range(n - 1, -1, -1)}
    return {"ostrovu": int(nc),
            "visi": [{"stred": [round(float(c), 2) for c in (lo[i] + hi[i]) / 2], "rozmer": [round(float(c), 2) for c in hi[i] - lo[i]],
                      "nad_terenem_m": round(float(min_nad[i]), 2), "objekt": jm.get(int(i), "")} for i in visi[:200]],
            "visi_pocet": int(len(visi)),
            "pod_terenem": [{"stred": [round(float(c), 2) for c in (lo[i] + hi[i]) / 2], "objekt": jm.get(int(i), "")} for i in pod_t[:50]],
            "pod_terenem_pocet": int(len(pod_t))}


def main():
    arg = [a for a in sys.argv[1:] if a.endswith(".glb")]
    sez = [{"soubor": a, "teren": "rovina"} for a in arg] if arg else KC["soubory"]
    vysl = {"popis": "ostrovy siti bez opory (visi) a cele pod terenem - tools/kontrola_geometrie.py", "soubory": {}, "chybi": []}
    for z in sez:
        cesta = os.path.join(ROOT, z["soubor"])
        if not os.path.exists(cesta):
            vysl["chybi"].append(z["soubor"])
            print("GEOMETRIE %s chybi (neovereno - zdrojovy .glb jen po exportu, v baliku je jen import)" % z["soubor"])
            continue
        r = kontrola(cesta, z["teren"])
        if r is None:
            continue
        vysl["soubory"][z["soubor"]] = r
        print("GEOMETRIE %s ostrovu %d visi %d pod terenem %d" % (z["soubor"], r["ostrovu"], r["visi_pocet"], r["pod_terenem_pocet"]))
        for v in r["visi"][:12]:
            print("  visi %s rozmer %s nad terenem %.2f %s" % (v["stred"], v["rozmer"], v["nad_terenem_m"], v["objekt"]))
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    out = os.path.join(ROOT, "build", "kontrola_geometrie.json")
    json.dump(vysl, open(out, "w"), ensure_ascii=False, indent=1)
    nal = rohatka.nalezy_ze_souboru(out)
    nove, pouz, zmiz, chyby = rohatka.porovnej("geometrie", nal, KJ)
    for c in chyby:
        print("ROHATKA " + c)
    print("GEOMETRIE souhrn: nalezu %d, schvalenych %d, novych %d, souboru neovereno %d" % (len(nal), len(pouz), len(nove), len(vysl["chybi"])))
    sys.exit(1 if nove or chyby else 0)


if __name__ == "__main__":
    main()
