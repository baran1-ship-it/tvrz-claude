"""Obecné přebalení glb (bez Blenderu – Blender ztratí kolize OMI_physics domů, viz glb_sit.py): z glb vezme jen vybrané
kořeny / uzly, vynechá uzly a primitivy podle jména (materiálu), přidá nové sítě a kolize a uloží jen použitá data.
Obrázky: vložené se uloží jednou do složky textur (podle obsahu – stejná textura v několika glb = jeden soubor) a glb na ně
odkazuje uri (Godot je importuje jako sdílené textury); volitelně zmenšené (max_px). Kolize OMI_physics_body/shape (domy.glb
z Godotu) se převezmou i se svými sítěmi. Použití: nastroje/zajimava_modely.py (zajímavá místa, Míša 15. 11.).
  Prebal(src).vyber(koreny, vynechat_uzly, vynechat_prim) → .pridej_sit(...) → .uloz(dst, tex_dir)"""
import os, io, json, hashlib
import numpy as np
from glb_sit import nacti, uloz, cti, matice

EXT = {"image/jpeg": ".jpg", "image/png": ".png"}


class Prebal:
    def __init__(s, src):
        s.j, s.b, _ = nacti(src); s.src = src
        s.uzly = []; s.koreny = []; s.nove_site = []; s.mat_nove = []

    def najdi(s, jm):
        for i, n in enumerate(s.j["nodes"]):
            if n.get("name") == jm: return i
        raise KeyError(jm)

    def vyber(s, koreny=None, vynechat=(), vynechat_prim=None, vynechat_fn=None):
        """koreny: jména uzlů (None = kořeny výchozí scény); vynechat: začátky jmen uzlů; vynechat_prim: {jméno uzlu:
        [začátky jmen materiálů]} nebo {"*": [...]} – primitivy těch materiálů se z uzlu vypustí; vynechat_fn(jméno) -> bool"""
        j = s.j; s._vp = vynechat_prim or {}
        sc = j["scenes"][j.get("scene", 0)]
        rr = sc["nodes"] if koreny is None else [s.najdi(k) for k in koreny]
        pryc = lambda n: any(n.get("name", "").startswith(v) for v in vynechat) or (vynechat_fn is not None and vynechat_fn(n.get("name", "")))
        s.mapa = {}
        def projdi(i):
            n = j["nodes"][i]
            if pryc(n): return None
            k = len(s.uzly); s.mapa[i] = k; s.uzly.append(None)
            nn = {kk: json.loads(json.dumps(vv)) for kk, vv in n.items() if kk != "children"}
            ch = [c for c in (projdi(c) for c in n.get("children", [])) if c is not None]
            if ch: nn["children"] = ch
            s.uzly[k] = nn; return k
        for r in rr:
            k = projdi(r)
            if k is not None:
                if koreny is not None:   # vybraný kořen = nový kořen bez posunu (počátek modelu)
                    for kk in ("translation", "rotation", "scale", "matrix"): s.uzly[k].pop(kk, None)
                s.koreny.append(k)
        return s

    def uzel(s, jm):
        for n in s.uzly:
            if n.get("name") == jm: return n
        return None

    def material(s, jm):
        """index materiálu zdroje podle jména (pro nové sítě)"""
        for i, m in enumerate(s.j.get("materials", [])):
            if m.get("name") == jm: return ("src", i)
        raise KeyError(jm)

    def novy_material(s, jm, obr=None, barva=(1, 1, 1, 1), drsnost=0.95):
        """nový materiál; obr = cesta k obrázku (vloží se jako textura)"""
        s.mat_nove.append({"name": jm, "obr": obr, "barva": list(barva), "drsnost": drsnost}); return ("new", len(s.mat_nove) - 1)

    def pridej_sit(s, jm, casti, rodic=None, poloha=(0, 0, 0), kolize=None):
        """casti = [(material, P (n,3), N (n,3), UV (n,2), I (m,))]; kolize = [P bodů konvexního tvaru, …] → OMI static
        konvexní (jako domy.glb); rodic = jméno uzlu (None = první kořen)"""
        s.nove_site.append({"jm": jm, "casti": casti, "rodic": rodic, "poloha": list(poloha), "kolize": kolize or []})

    def uloz(s, dst, tex_dir, max_px=None, rel_uri=True):
        j, b = s.j, s.b
        os.makedirs(tex_dir, exist_ok=True)
        out = {"asset": {"version": "2.0", "generator": "puchart nastroje/glb_prebal.py z " + os.path.basename(s.src)},
               "scene": 0, "scenes": [{"name": "Scene", "nodes": s.koreny}], "nodes": s.uzly,
               "meshes": [], "materials": [], "textures": [], "images": [], "samplers": [], "accessors": [], "bufferViews": [], "buffers": [{"byteLength": 0}]}
        nb = bytearray(); mm = {}; mt = {}; mx = {}; mi = {}; ms = {}; ma = {}; tvary = []; tvar_m = {}
        def nove_acc(d, typ):
            d = np.ascontiguousarray(d)
            nb.extend(b"\0" * ((4 - len(nb) % 4) % 4)); off = len(nb); nb.extend(d.tobytes())
            out["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": d.nbytes, "target": 34963 if typ == "i" else 34962})
            a = {"bufferView": len(out["bufferViews"]) - 1, "count": len(d)}
            if typ == "i": a.update(componentType=5125, type="SCALAR")
            else:
                a.update(componentType=5126, type={2: "VEC2", 3: "VEC3", 4: "VEC4"}[d.shape[1]])
                if typ == "p": a["min"] = d.min(0).tolist(); a["max"] = d.max(0).tolist()
            out["accessors"].append(a); return len(out["accessors"]) - 1
        def acc(i):
            if i in ma: return ma[i]
            a = dict(j["accessors"][i]); d = cti(j, b, i)
            nb.extend(b"\0" * ((4 - len(nb) % 4) % 4)); off = len(nb); dd = np.ascontiguousarray(d); nb.extend(dd.tobytes())
            bv = {"buffer": 0, "byteOffset": off, "byteLength": dd.nbytes}
            t = j["bufferViews"][a["bufferView"]].get("target")
            if t: bv["target"] = t
            out["bufferViews"].append(bv); a["bufferView"] = len(out["bufferViews"]) - 1; a.pop("byteOffset", None)
            out["accessors"].append(a); ma[i] = len(out["accessors"]) - 1; return ma[i]
        def uloz_obr(data, nm, ext):
            if max_px:
                from PIL import Image
                im = Image.open(io.BytesIO(data))
                if max(im.size) > max_px:
                    f = max_px / max(im.size); im = im.resize((max(1, int(im.size[0] * f)), max(1, int(im.size[1] * f))), Image.LANCZOS)
                    bb = io.BytesIO(); im.convert("RGB").save(bb, "JPEG", quality=88) if ext == ".jpg" else im.save(bb, "PNG"); data = bb.getvalue()
            h = hashlib.sha1(data).hexdigest()[:8]
            cist = "".join(c if c.isalnum() or c in "_-" else "_" for c in nm)[:40]
            cil = os.path.join(tex_dir, "%s_%s%s" % (cist, h, ext))
            if not os.path.exists(cil): open(cil, "wb").write(data)
            return cil
        def img(i):
            if i in mi: return mi[i]
            im = j["images"][i]; nm = im.get("name") or "obr%d" % i
            if "bufferView" in im:
                bv = j["bufferViews"][im["bufferView"]]; data = bytes(b[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]])
                cil = uloz_obr(data, nm, EXT.get(im.get("mimeType"), ".png"))
            else:
                cil = os.path.join(os.path.dirname(s.src), im["uri"])
            out["images"].append({"name": nm, "uri": os.path.relpath(cil, os.path.dirname(dst)).replace(os.sep, "/")}); mi[i] = len(out["images"]) - 1; return mi[i]
        def smp(i):
            if i not in ms: out["samplers"].append(j["samplers"][i]); ms[i] = len(out["samplers"]) - 1
            return ms[i]
        def tex(i):
            if i in mx: return mx[i]
            t = dict(j["textures"][i]); t["source"] = img(t["source"])
            if "sampler" in t: t["sampler"] = smp(t["sampler"])
            out["textures"].append(t); mx[i] = len(out["textures"]) - 1; return mx[i]
        def prepis_tex(o):
            if isinstance(o, dict):
                for k_, v_ in list(o.items()):
                    if k_ == "index" and isinstance(v_, int): o[k_] = tex(v_)
                    else: prepis_tex(v_)
            elif isinstance(o, list):
                for v_ in o: prepis_tex(v_)
        def mat(ref):
            if ref in mt: return mt[ref]
            if ref[0] == "src":
                m = json.loads(json.dumps(j["materials"][ref[1]])); prepis_tex(m)
            else:
                d = s.mat_nove[ref[1]]
                m = {"name": d["name"], "pbrMetallicRoughness": {"baseColorFactor": d["barva"], "metallicFactor": 0.0, "roughnessFactor": d["drsnost"]}}
                if d["obr"]:
                    cil = uloz_obr(open(d["obr"], "rb").read(), os.path.splitext(os.path.basename(d["obr"]))[0], os.path.splitext(d["obr"])[1].lower())
                    out["images"].append({"name": d["name"], "uri": os.path.relpath(cil, os.path.dirname(dst)).replace(os.sep, "/")})
                    out["textures"].append({"source": len(out["images"]) - 1}); m["pbrMetallicRoughness"]["baseColorTexture"] = {"index": len(out["textures"]) - 1}
            out["materials"].append(m); mt[ref] = len(out["materials"]) - 1; return mt[ref]
        def sit(mi_, jm_uzlu=""):
            vp = [v for k_, v in getattr(s, "_vp", {}).items() if k_ == "*" or jm_uzlu.startswith(k_)]
            vp = [x for v in vp for x in v]
            klic = (mi_, tuple(vp))
            if klic in mm: return mm[klic]
            m = json.loads(json.dumps(j["meshes"][mi_])); pr = []
            for p in m["primitives"]:
                mjm = j["materials"][p["material"]].get("name", "") if "material" in p else ""
                if any(mjm.startswith(v) for v in vp): continue
                p["attributes"] = {k_: acc(v_) for k_, v_ in p["attributes"].items()}
                if "indices" in p: p["indices"] = acc(p["indices"])
                if "material" in p: p["material"] = mat(("src", p["material"]))
                p.pop("targets", None); pr.append(p)
            if not pr: mm[klic] = None; return None
            m["primitives"] = pr; out["meshes"].append(m); mm[klic] = len(out["meshes"]) - 1; return mm[klic]
        sh_src = j.get("extensions", {}).get("OMI_physics_shape", {}).get("shapes", [])
        def tvar(i):
            if i in tvar_m: return tvar_m[i]
            t = json.loads(json.dumps(sh_src[i]))
            for typ in ("convex", "trimesh"):
                if typ in t and "mesh" in t[typ]: t[typ]["mesh"] = sit(t[typ]["mesh"])
            tvary.append(t); tvar_m[i] = len(tvary) - 1; return tvar_m[i]
        for n in list(out["nodes"]):
            if "mesh" in n:
                k = sit(n["mesh"], n.get("name", ""))
                if k is None: del n["mesh"]
                else: n["mesh"] = k
            col = n.get("extensions", {}).get("OMI_physics_body", {}).get("collider")
            if col and "shape" in col: col["shape"] = tvar(col["shape"])
        # nové sítě a kolize
        for ns in s.nove_site:
            pr = []
            for (mref, P, N, UV, I) in ns["casti"]:
                if len(I) == 0: continue
                at = {"POSITION": nove_acc(np.asarray(P, np.float32), "p"), "NORMAL": nove_acc(np.asarray(N, np.float32), "a")}
                if UV is not None: at["TEXCOORD_0"] = nove_acc(np.asarray(UV, np.float32), "a")
                pr.append({"attributes": at, "indices": nove_acc(np.asarray(I, np.uint32), "i"), "material": mat(mref)})
            rod = 0
            if ns["rodic"]:
                rod = next(i for i, n in enumerate(out["nodes"]) if n.get("name") == ns["rodic"])
            else: rod = s.koreny[0]
            if pr:
                out["meshes"].append({"name": ns["jm"], "primitives": pr})
                out["nodes"].append({"name": ns["jm"], "mesh": len(out["meshes"]) - 1, "translation": ns["poloha"]})
                out["nodes"][rod].setdefault("children", []).append(len(out["nodes"]) - 1)
            for ki, KP in enumerate(ns["kolize"]):
                KP = np.asarray(KP, np.float32)
                out["meshes"].append({"name": "%s_kol%d" % (ns["jm"], ki), "primitives": [{"attributes": {"POSITION": nove_acc(KP, "p")}}]})
                tvary.append({"type": "convex", "convex": {"mesh": len(out["meshes"]) - 1}})
                out["nodes"].append({"name": "CollisionShape3D_%s_%d" % (ns["jm"], ki), "extensions": {"OMI_physics_body": {"collider": {"shape": len(tvary) - 1}}}})
                out["nodes"].append({"name": "%s_Kol%d" % (ns["jm"], ki), "translation": ns["poloha"], "children": [len(out["nodes"]) - 1],
                                     "extensions": {"OMI_physics_body": {"motion": {"type": "static"}}}})
                out["nodes"][rod].setdefault("children", []).append(len(out["nodes"]) - 1)
        if tvary:
            out["extensions"] = {"OMI_physics_shape": {"shapes": tvary}}
            out["extensionsUsed"] = ["OMI_physics_body", "OMI_physics_shape"]
        for k_ in ("samplers", "images", "textures"):
            if not out[k_]: del out[k_]
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        uloz(dst, out, nb)
        tri = sum(cti_count(out, p) for m in out["meshes"] for p in m["primitives"] if "indices" in p and not m.get("name", "").endswith(tuple("kol%d" % i for i in range(20))))
        return len(out["nodes"]), os.path.getsize(dst), tri


def cti_count(out, p):
    return out["accessors"][p["indices"]]["count"] // 3


def kvadr(x0, x1, y0, y1, z0, z1, uv_m=1.0):
    """kvádr jako 6 stěn s normálami a UV (metry / uv_m) → (P, N, UV, I)"""
    P = []; N = []; UV = []; I = []
    sten = [((1, 0, 0), [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]), ((-1, 0, 0), [(x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (x0, y0, z0)]),
            ((0, 1, 0), [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)]), ((0, -1, 0), [(x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1)]),
            ((0, 0, 1), [(x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (x0, y0, z1)]), ((0, 0, -1), [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)])]
    for nrm, q in sten:
        b0 = len(P); nrm = np.array(nrm, float)
        for v in q:
            P.append(v); N.append(nrm)
            a = [k for k in range(3) if abs(nrm[k]) < 0.5]
            UV.append((v[a[0]] / uv_m, v[a[1]] / uv_m))
        I += [b0, b0 + 2, b0 + 1, b0, b0 + 3, b0 + 2]   # glTF: proti směru hodinových ručiček zvenku
    P = np.array(P, float); N = np.array(N, float)
    # pořadí: ověř, že normála trojúhelníku = normála stěny, jinak otoč
    I = np.array(I).reshape(-1, 3)
    for t in I:
        n_ = np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]])
        if np.dot(n_, N[t[0]]) < 0: t[1], t[2] = t[2], t[1]
    return P, N, np.array(UV, float), I.reshape(-1)


def spoj(*dily):
    """spojí několik (P, N, UV, I) do jednoho"""
    P = []; N = []; UV = []; I = []; o = 0
    for (p, n, uv, i) in dily:
        P.append(p); N.append(n); UV.append(uv); I.append(np.asarray(i) + o); o += len(p)
    return np.vstack(P), np.vstack(N), np.vstack(UV), np.concatenate(I)


def posun(d, t=(0, 0, 0), rot_y=0.0, rot_x=0.0, rot_z=0.0):
    """posune a otočí díl (P, N, UV, I)"""
    P, N, UV, I = d
    def R(a, osa):
        c, s_ = np.cos(a), np.sin(a)
        if osa == "x": return np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]])
        if osa == "y": return np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]])
        return np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
    M = R(rot_y, "y") @ R(rot_x, "x") @ R(rot_z, "z")
    return (P @ M.T + np.array(t), N @ M.T, UV, I)
