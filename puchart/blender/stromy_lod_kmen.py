"""LOD1 stromů – decimace kmene a větví v Blenderu (plán A4 z rešerše 17. 11.: Halcyon flora.mjs, Havran K13 – „vlastní LOD
z Blenderu místo automatických“). nastroje/stromy_lod.py dělá LOD1 jen z listí (podíl karet zvětšených kolem středu), kůra
zůstávala celá – u javoru, jasanu, jedle, dubu je kůra v LOD1 4–24 tis. troj. na strom (víc než listí). Tento krok po něm
zmenší v každém *_lod1.glb síť kůry (materiál bez alfy, ne listí) Blenderovou decimací (collapse) na podíl z dat
(stromy_modely.json lod1_kmen) se zachováním UV a barvy vrcholů (COLOR_0 = vítr/AO v kura.gdshader); uzly, materiály
a pořadí ploch zůstávají (les.gd přebírá materiály z LOD0 podle pořadí ploch). Nová data se připíší na konec bufferu
(glb_sit.pridej), staré accessory zůstanou nevyužité. Opakované spuštění: decimuje se vždy z LOD0 (<model>.glb), ne z LOD1.
  /opt/bl/bin/python blender/stromy_lod_kmen.py <koren_puchartu> [model ...]
"""
import sys, os, glob, json, math
import numpy as np
import bpy

K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, os.path.join(K, "nastroje"))
from glb_sit import nacti, uloz, cti, pridej

CFG = json.load(open(os.path.join(K, "pravidla/svet/stromy_modely.json")))["lod1_kmen"]
D = os.path.join(K, "hra/modely/stromy")


def je_listi(mat):
    jm = (mat.get("name") or "").lower()
    return mat.get("alphaMode") in ("MASK", "BLEND") or "list" in jm or "jehl" in jm


def decimuj(P, N, UV, COL, I, podil):
    """Trojúhelníky (P, UV, COL po vrcholech, I indexy) → decimované (P, N, UV, COL, I) po rozích (vrchol = jedinečný roh)."""
    klic = np.round(P, 5)
    u, inv = np.unique(klic, axis=0, return_inverse=True); inv = inv.ravel()
    me = bpy.data.meshes.new("kura")
    T = I.reshape(-1, 3)
    me.from_pydata(u.tolist(), [], inv[T].tolist())
    uvl = me.uv_layers.new(name="UV")
    uvl.data.foreach_set("uv", UV[T.ravel()].astype(np.float32).ravel())
    if COL is not None:
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        c4 = np.ones((len(COL), 4), np.float32); c4[:, :COL.shape[1]] = COL
        ca.data.foreach_set("color", c4[T.ravel()].ravel())
    me.validate(clean_customdata=False); me.update()
    ob = bpy.data.objects.new("kura", me); bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth = True
    md = ob.modifiers.new("dec", "DECIMATE"); md.decimate_type = "COLLAPSE"; md.ratio = podil
    md.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg)
    m2 = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    m2.calc_loop_triangles()
    nt = len(m2.loop_triangles)
    lp = np.zeros(nt * 3, np.int64); m2.loop_triangles.foreach_get("loops", lp)
    vi = np.zeros(len(m2.loops), np.int64); m2.loops.foreach_get("vertex_index", vi)
    co = np.zeros(len(m2.vertices) * 3, np.float32); m2.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    cn = np.zeros(len(m2.loops) * 3, np.float32); m2.corner_normals.foreach_get("vector", cn); cn = cn.reshape(-1, 3)
    uv2 = np.zeros(len(m2.loops) * 2, np.float32); m2.uv_layers[0].data.foreach_get("uv", uv2); uv2 = uv2.reshape(-1, 2)
    c2 = None
    if COL is not None:
        c2 = np.zeros(len(m2.loops) * 4, np.float32); m2.color_attributes["Col"].data.foreach_get("color", c2); c2 = c2.reshape(-1, 4)[:, :COL.shape[1]]
    # rohy se stejným vrcholem, UV, normálou a barvou sloučit
    rad = np.c_[vi[lp], np.round(uv2[lp], 5), np.round(cn[lp], 3)] if c2 is None else np.c_[vi[lp], np.round(uv2[lp], 5), np.round(cn[lp], 3), np.round(c2[lp], 4)]
    _, prv, inv2 = np.unique(rad, axis=0, return_index=True, return_inverse=True)
    L = lp[prv]
    out = (co[vi[L]], cn[L], uv2[L], None if c2 is None else c2[L], inv2.ravel().astype(np.uint32))
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(me); bpy.data.meshes.remove(m2)
    return out


def komponenty(P, I):
    """Souvislé kusy sítě (větve jsou samostatné trubky) – štítek pro každý trojúhelník."""
    u, inv = np.unique(np.round(P, 5), axis=0, return_inverse=True); inv = inv.ravel()
    par = np.arange(len(u))
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    T = inv[I.reshape(-1, 3)]
    for a_, b_, c_ in T:
        ra = f(a_); par[f(b_)] = ra; par[f(c_)] = ra
    return np.array([f(x) for x in T[:, 0]])


def lod_kury(P, NO, UV, COL, I):
    """LOD1 kůry jako SpeedTree: (1) nejtenčí větvičky (poloměr pod vetvicky_r_m, z dálky schované v listí) pryč, nejvýš
    do podílu; (2) velké kusy (kmen, silné větve ≥ decimovat_od_troj) decimovat (collapse dec_podil) – přijmout jen, když
    zůstane délka kusu (≥ 92 %), jinak kus beze změny. Malé trubky větví se nedecimují (collapse je smaže celé – kmen
    buku zmizel, test smyslu stromy_lod1_kmen)."""
    T = I.reshape(-1, 3); lab = komponenty(P, I); ids = np.unique(lab)
    A = np.linalg.norm(np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]), axis=1) / 2
    info = []; lo, hi = P.min(0), P.max(0); tol = 0.04 * np.ptp(P, axis=0).max()
    for c in ids:
        sel = lab == c; Q = P[np.unique(T[sel])]
        L = float(np.ptp(Q, axis=0).max()); r = A[sel].sum() / (2 * math.pi * max(L, 1e-3))
        obr = bool((Q.min(0) <= lo + tol).any() or (Q.max(0) >= hi - tol).any())   # kus určuje obrys stromu → nemazat
        info.append((c, int(sel.sum()), L, r if not obr else 1e9))
    celk = len(T); cil_pryc = (1 - float(CFG["podil"])) * celk * float(CFG["vetvicky_max_podil"])
    hlavni = max(info, key=lambda e: e[1])[0]
    pryc = set(); n_pryc = 0
    for c, n, L, r in sorted(info, key=lambda e: e[3]):
        if c == hlavni or r > float(CFG["vetvicky_r_m"]) or n_pryc + n > cil_pryc: continue
        pryc.add(c); n_pryc += n
    casti = []
    for c, n, L, r in info:
        if c in pryc: continue
        sel = lab == c; Ic = T[sel].ravel(); uv_ = np.unique(Ic); mp = np.full(len(P), -1); mp[uv_] = np.arange(len(uv_))
        orig = (P[uv_], NO[uv_], UV[uv_], None if COL is None else COL[uv_], mp[Ic].astype(np.uint32))
        if n >= int(CFG["decimovat_od_troj"]):
            d = decimuj(P[uv_], None, UV[uv_], None if COL is None else COL[uv_], mp[Ic], float(CFG["dec_podil"]))
            if len(d[4]) and np.ptp(d[0], axis=0).max() >= 0.92 * L: orig = d
        casti.append(orig)
    Pn, Nn, UVn, Cn, In = [], [], [], [], []; o = 0
    for q in casti:
        Pn.append(q[0]); Nn.append(q[1]); UVn.append(q[2]); Cn.append(q[3]); In.append(q[4].astype(np.int64) + o); o += len(q[0])
    return (np.concatenate(Pn), np.concatenate(Nn), np.concatenate(UVn), None if COL is None else np.concatenate(Cn),
            np.concatenate(In).astype(np.uint32))


def zpracuj(model):
    src = os.path.join(D, model + ".glb"); dst = os.path.join(D, model + "_lod1.glb")
    if not (os.path.exists(src) and os.path.exists(dst)): return None
    j0, b0, _ = nacti(src); j, b, zb = nacti(dst)
    pred = po = 0
    for mi, m in enumerate(j["meshes"]):
        for pi, pr in enumerate(m["primitives"]):
            mat = j["materials"][pr["material"]] if "material" in pr else {}
            n_tri = j["accessors"][pr["indices"]]["count"] // 3
            if je_listi(mat): continue
            p0 = j0["meshes"][mi]["primitives"][pi]   # kůra z LOD0 (stejná jako v LOD1 ze stromy_lod.py)
            P = cti(j0, b0, p0["attributes"]["POSITION"]).astype(np.float64)
            UV = cti(j0, b0, p0["attributes"]["TEXCOORD_0"]).astype(np.float64)
            COL = cti(j0, b0, p0["attributes"]["COLOR_0"]).astype(np.float64) if "COLOR_0" in p0["attributes"] else None
            ct = j0["accessors"][p0["attributes"]["COLOR_0"]]["componentType"] if COL is not None else 5126
            if ct == 5121: COL = COL / 255.0
            elif ct == 5123: COL = COL / 65535.0
            I = cti(j0, b0, p0["indices"]).ravel().astype(np.int64)
            NO = cti(j0, b0, p0["attributes"]["NORMAL"]).astype(np.float64)
            Pn, Nn, UVn, Cn, In = lod_kury(P, NO, UV, COL, I)
            if len(In) >= len(I): continue
            at = pr["attributes"]
            at["POSITION"] = pridej(j, b, Pn.astype(np.float32), "f")
            at["NORMAL"] = pridej(j, b, Nn.astype(np.float32), "a")
            at["TEXCOORD_0"] = pridej(j, b, UVn.astype(np.float32), "a")
            at.pop("TANGENT", None)
            if Cn is not None: at["COLOR_0"] = pridej(j, b, Cn.astype(np.float32), "a")
            pr["indices"] = pridej(j, b, In, "i")
            pred += n_tri; po += len(In) // 3
    uloz(dst, j, b, zb)
    return pred, po


if __name__ == "__main__":
    vyb = [a for a in sys.argv[2:] if not a.startswith("-")]
    modely = vyb or sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(D, "*.glb"))
                           if not f.endswith(("_lod1.glb", "_daleko.glb")))
    sp = sn = 0
    for mdl in modely:
        r = zpracuj(mdl)
        if r is None: continue
        sp += r[0]; sn += r[1]
        print("STROMY_LOD1 %s: kůra %d → %d troj." % (mdl, r[0], r[1]), flush=True)
    print("STROMY_LOD1 celkem kůra %d → %d troj." % (sp, sn))
