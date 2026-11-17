"""Přebalení modelů topení od Míšina modeláře do hry (pravidla/svet/topeni.json; modelový filtr CLAUDE.md: licence → měřítko →
materiály → LOD + kolize → katalog). Dodané glb (build/zdroj_modelar/<sada>/<Model>_LOD0/1.glb) obsahují celý Blender soubor
(všechny scény, uzly ostatních modelů) a v každém glb znovu vložené tytéž 1K textury (~7 MB na soubor). Nástroj z každého
vezme jen výchozí scénu, vynechá díly varianty (varianty[].vynechat – začátek jména uzlu), z LOD1 značky (prázdné uzly bez
potomků – značky čte hra jen z LOD0) a vložené obrázky uloží jednou do <vystup>/textury/ (glb na ně odkazuje uri, Godot je
importuje jako sdílené textury). Geometrie, materiály (COLOR_0 × albedo), kolize -convcolonly a jména uzlů zůstanou.
Nádobí (nadobi.predmety): stejně přebalené glb + scéna <vystup>/../predmety_h/topeni_<Model>.tscn podle dodané .tscn
(kořen RigidBody3D, freeze, hmotnost, jediná konvexní kolize; vnořená kolize glb vypnutá) s LOD podle nadobi.lod0_do_m.
  python3 nastroje/topeni_modely.py <K>"""
import sys, os, json, re
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_sit import nacti, uloz, cti, CT

K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
C = json.load(open(os.path.join(K, "pravidla/svet/topeni.json")))
ZD = os.path.join(K, C["zdroj"]["slozka"]); OUT = os.path.join(K, C["vystup"]); TEX = os.path.join(OUT, "textury")
os.makedirs(TEX, exist_ok=True)
PRED = os.path.join(K, "hra/modely/predmety_h")
EXT = {"image/jpeg": ".jpg", "image/png": ".png"}


def prebal(src, dst, vynechat=(), bez_znacek=False, odebrat=(), meritko=None):
    """meritko = [sx, sy, sz] varianty (topeni.json varianty[].meritko): zapečené do vrcholů, normál, tečen a poloh uzlů (značky
    Pec_Ohen, Pec_Usti…), kolize -convcolonly se škálují s nimi – v Godotu pak žádné nerovnoměrné měřítko uzlu (kolize ho nesnesou)."""
    """odebrat = [{"uzel": začátek jména uzlu se sítí, "kvadr": [x0, x1, y0, y1, z0, z1]}] – trojúhelníky sítě celé uvnitř
    kvádru (souřadnice sítě glTF) se vypustí: výbava sloučená modelářem do sítě pevného dílu (pekařská lopata v síti lavice)"""
    j, b, _ = nacti(src)
    sc = j["scenes"][j.get("scene", 0)]
    pryc = lambda n: any(n.get("name", "").startswith(v) for v in vynechat)
    uzly = []; mapa = {}
    def projdi(i):
        n = j["nodes"][i]
        if pryc(n): return None
        if bez_znacek and "mesh" not in n and not n.get("children") and i not in sc["nodes"]: return None
        k = len(uzly); mapa[i] = k; uzly.append(None)
        nn = {kk: vv for kk, vv in n.items() if kk not in ("children", "mesh")}
        if "mesh" in n: nn["mesh"] = n["mesh"]
        ch = [c for c in (projdi(c) for c in n.get("children", [])) if c is not None]
        if ch: nn["children"] = ch
        uzly[k] = nn; return k
    koreny = [r for r in (projdi(r) for r in sc["nodes"]) if r is not None]
    # sítě, materiály, textury, obrázky, accessory – jen použité, přečíslované
    out = {"asset": {"version": "2.0", "generator": "puchart nastroje/topeni_modely.py z " + os.path.basename(src)},
           "scene": 0, "scenes": [{"name": sc.get("name", ""), "nodes": koreny}], "nodes": uzly,
           "meshes": [], "materials": [], "textures": [], "images": [], "samplers": [], "accessors": [], "bufferViews": [], "buffers": [{"byteLength": 0}]}
    nb = bytearray(); mm = {}; mt = {}; mx = {}; mi = {}; ms = {}; ma = {}
    MS = np.array(meritko, float) if meritko else None
    def acc(i, role=None):
        kl = (i, role if MS is not None else None)
        if kl in ma: return ma[kl]
        a = dict(j["accessors"][i]); d = cti(j, b, i)
        if MS is not None and role in ("POSITION", "NORMAL", "TANGENT"):
            d = np.array(d, np.float32)
            if role == "POSITION": d[:, :3] *= MS; a["min"] = [float(v) for v in d[:, :3].min(0)]; a["max"] = [float(v) for v in d[:, :3].max(0)]
            else:
                d[:, :3] = d[:, :3] * (MS if role == "TANGENT" else 1.0 / MS)
                d[:, :3] /= np.maximum(np.linalg.norm(d[:, :3], axis=1, keepdims=True), 1e-8)
        nb.extend(b"\0" * ((4 - len(nb) % 4) % 4)); off = len(nb); dd = np.ascontiguousarray(d); nb.extend(dd.tobytes())
        bv = {"buffer": 0, "byteOffset": off, "byteLength": dd.nbytes}
        t = j["bufferViews"][a["bufferView"]].get("target")
        if t: bv["target"] = t
        out["bufferViews"].append(bv); a["bufferView"] = len(out["bufferViews"]) - 1; a.pop("byteOffset", None)
        out["accessors"].append(a); ma[kl] = len(out["accessors"]) - 1; return ma[kl]
    def img(i):
        if i in mi: return mi[i]
        im = j["images"][i]; nm = im.get("name") or "obr%d" % i; ext = EXT.get(im.get("mimeType"), ".png")
        cil = os.path.join(TEX, nm + ext)
        bv = j["bufferViews"][im["bufferView"]]; data = bytes(b[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]])
        if not os.path.exists(cil) or os.path.getsize(cil) != len(data): open(cil, "wb").write(data)
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
    def mat(i):
        if i in mt: return mt[i]
        m = json.loads(json.dumps(j["materials"][i])); prepis_tex(m)
        for k_, v_ in C.get("materialy", {}).get(m.get("name", ""), {}).items():   # úprava materiálu u zdroje (topeni.json materialy)
            if not k_.startswith("_"): m.setdefault("pbrMetallicRoughness", {})[k_] = v_
        out["materials"].append(m); mt[i] = len(out["materials"]) - 1; return mt[i]
    def bez_kusu(p, kv):   # nový accessor indexů bez trojúhelníků celých v kvádru kv
        X = cti(j, b, p["attributes"]["POSITION"]); I = cti(j, b, p["indices"]).reshape(-1, 3); V = X[I]
        uvnitr = np.ones(len(I), bool)
        for o_ in range(3): uvnitr &= (V[..., o_] >= kv[2 * o_]).all(1) & (V[..., o_] <= kv[2 * o_ + 1]).all(1)
        I = np.ascontiguousarray(I[~uvnitr].ravel().astype(np.uint32))
        nb.extend(b"\0" * ((4 - len(nb) % 4) % 4)); off = len(nb); nb.extend(I.tobytes())
        out["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": I.nbytes, "target": 34963})
        out["accessors"].append({"bufferView": len(out["bufferViews"]) - 1, "componentType": 5125, "count": int(I.size), "type": "SCALAR"})
        print("TOPENI_ODEBRANO %s troj %d" % (dst.split("/")[-1], int(uvnitr.sum())))
        return len(out["accessors"]) - 1
    for n in uzly:
        if "mesh" not in n: continue
        kv = next((o_["kvadr"] for o_ in odebrat if n.get("name", "").startswith(o_["uzel"])), None)
        if n["mesh"] not in mm or kv is not None:
            m = json.loads(json.dumps(j["meshes"][n["mesh"]]))
            for p, p0 in zip(m["primitives"], j["meshes"][n["mesh"]]["primitives"]):
                p["attributes"] = {k_: acc(v_, k_) for k_, v_ in p["attributes"].items()}
                if "indices" in p: p["indices"] = bez_kusu(p0, kv) if kv is not None else acc(p["indices"])
                if "material" in p: p["material"] = mat(p["material"])
                p.pop("targets", None)
            out["meshes"].append(m); mm[n["mesh"]] = len(out["meshes"]) - 1
        n["mesh"] = mm[n["mesh"]]
    if MS is not None:
        for k_ in koreny: assert not any(x in uzly[k_] for x in ("rotation", "scale", "matrix")), "meritko: kořen modelu s transformací"
        for n in uzly:
            if "translation" in n: n["translation"] = [float(v) for v in np.array(n["translation"]) * MS]
            assert "matrix" not in n
    for k_ in ("samplers", "images", "textures"):
        if not out[k_]: del out[k_]
    uloz(dst, out, nb)
    return len(uzly), os.path.getsize(dst)


def zdroj(model, lod):
    sada = C["modely"].get(model, {}).get("sada") or C["nadobi"]["sada"]
    return os.path.join(ZD, sada, "%s_%s.glb" % (model, lod))


hotovo = []
for model in C["modely"]:
    if model.startswith("_"): continue   # poznámky (_kolize_pozn) – dřív tu nástroj padal
    for lod in ("LOD0", "LOD1"):
        s = zdroj(model, lod)
        if not os.path.exists(s): print("TOPENI_CHYBI", s); continue
        n, vel = prebal(s, os.path.join(OUT, "%s_%s.glb" % (model, lod)), bez_znacek=lod == "LOD1", odebrat=C["modely"][model].get("odebrat", ()))
        hotovo.append(model); print("TOPENI %s_%s uzlů %d, %.2f MB" % (model, lod, n, vel / 1e6))
for jm, v in C["varianty"].items():
    if jm.startswith("_"): continue
    for lod in ("LOD0", "LOD1"):
        s = zdroj(v["z"], lod)
        if not os.path.exists(s): print("TOPENI_CHYBI", s); continue
        n, vel = prebal(s, os.path.join(OUT, "%s_%s.glb" % (jm, lod)), v.get("vynechat", ()), bez_znacek=lod == "LOD1", odebrat=C["modely"].get(v["z"], {}).get("odebrat", ()), meritko=v.get("meritko"))
        print("TOPENI %s_%s (z %s bez %s) uzlů %d, %.2f MB" % (jm, lod, v["z"], v.get("vynechat"), n, vel / 1e6))

# nádobí → katalog předmětů (RigidBody3D z dodané .tscn: freeze, mass, tvar FyzickaKolize)
ND = C["nadobi"]; os.makedirs(os.path.join(OUT, "nadobi"), exist_ok=True)
KATP = os.path.join(K, "hra/modely/predmety_h.json")   # katalog pískoviště (nastroje/predmety_z_havrana.sh) – doplní se nádobí
KAT = json.load(open(KATP)) if os.path.exists(KATP) else {}
for model in ND["predmety"]:
    src_t = os.path.join(ZD, ND["sada"], model + ".tscn")
    if not os.path.exists(zdroj(model, "LOD0")) or not os.path.exists(src_t): print("TOPENI_CHYBI", model); continue
    for lod in ("LOD0", "LOD1"):
        prebal(zdroj(model, lod), os.path.join(OUT, "nadobi", "%s_%s.glb" % (model, lod)))
    t = open(src_t).read()
    body = re.search(r'\[sub_resource type="ConvexPolygonShape3D" id="Hull"\]\s*points = (PackedVector3Array\([^)]*\))', t)
    mass = re.search(r"\nmass = ([0-9.]+)", t); freeze = "freeze = true" in t
    # jména sítí a uzlu vnořené kolize ze zdrojové scény (index + jméno – Godot je při instanci najde podle cesty)
    vis0 = re.findall(r'\[node name="([^"]+)" parent="LOD0/([^"]+)" index=\d+\]\nvisibility_range_end', t)
    vis1 = re.findall(r'\[node name="([^"]+)" parent="LOD1/([^"]+)" index=\d+\]\nvisibility_range_begin', t)
    kol = re.findall(r'\[node name="CollisionShape3D" parent="LOD0/([^"]+)" index=0\]\ndisabled = true', t)
    d0 = float(ND["lod0_do_m"])
    o = ['[gd_scene load_steps=4 format=3]', '',
         '[ext_resource type="PackedScene" path="res://modely/topeni/nadobi/%s_LOD0.glb" id="1"]' % model,
         '[ext_resource type="PackedScene" path="res://modely/topeni/nadobi/%s_LOD1.glb" id="2"]' % model, '',
         '[sub_resource type="ConvexPolygonShape3D" id="Hull"]', 'points = ' + body.group(1), '',
         '[node name="%s" type="RigidBody3D"]' % model, 'freeze = %s' % ("true" if freeze else "false"), 'mass = %s' % (mass.group(1) if mass else "1.0"), '',
         '[node name="FyzickaKolize" type="CollisionShape3D" parent="."]', 'shape = SubResource("Hull")', '',
         '[node name="LOD0" parent="." instance=ExtResource("1")]', '', '[node name="LOD1" parent="." instance=ExtResource("2")]', '']
    for p in sorted(set(kol)):
        o += ['[node name="CollisionShape3D" parent="LOD0/%s" index=0]' % p, 'disabled = true', '']
    for jm, p in vis0:
        o += ['[node name="%s" parent="LOD0/%s"]' % (jm, p), 'visibility_range_end = %.1f' % d0, 'visibility_range_end_margin = 0.5', '']
    for jm, p in vis1:
        o += ['[node name="%s" parent="LOD1/%s"]' % (jm, p), 'visibility_range_begin = %.1f' % d0, 'visibility_range_begin_margin = 0.5',
              'visibility_range_end = %.1f' % float(C["lod"]["vnitrek_do_m"]), '']
    o += ['[editable path="LOD0"]', '[editable path="LOD1"]', '']
    open(os.path.join(PRED, "topeni_%s.tscn" % model), "w").write("\n".join(o))
    # záznam katalogu pískoviště (rozměr z LOD0 bez kolizí – Godot osy, počátek na opěrné rovině)
    jj, bb, _ = nacti(os.path.join(OUT, "nadobi", "%s_LOD0.glb" % model)); body_ = []
    for n in jj["nodes"]:
        if "mesh" in n and "colonly" not in n.get("name", ""):
            for p in jj["meshes"][n["mesh"]]["primitives"]:
                body_.append(cti(jj, bb, p["attributes"]["POSITION"]) + np.array(n.get("translation", [0, 0, 0])))
    B = np.vstack(body_); kz = ND["katalog"].get(model, {})
    KAT["topeni_" + model] = {"nazev": kz.get("nazev", model), "kat": ND["kat"], "stav": ND["stav"], "vaha": float(mass.group(1)) if mass else 1.0,
                             "cena": kz.get("cena", 5), "rozmer": [round(float(v), 3) for v in (B.max(0) - B.min(0))]}
    print("TOPENI_NADOBI %s (mass %s, freeze %s, LOD0 %d sítí, vypnutá vnořená kolize %d)" % (model, mass.group(1) if mass else "?", freeze, len(vis0), len(set(kol))))
if os.path.exists(KATP):
    json.dump(KAT, open(KATP, "w"), ensure_ascii=False, indent=1); print("TOPENI_KATALOG %d nádobí v %s" % (sum(1 for k in KAT if k.startswith("topeni_")), KATP))
print("TOPENI hotovo: %d modelů, textury %d souborů v %s" % (len(set(hotovo)), len(os.listdir(TEX)), TEX))
