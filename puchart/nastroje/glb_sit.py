"""Společné čtení a zápis binárního glb bez Blenderu (numpy) – pro úpravy modelů, které Blender poškodí (domy.glb vyvezl Godot
s kolizemi OMI_physics_body/shape, Blender je při importu ztratí – viz blender/okap_vstupu.py) a pro přebalení modelů
od modeláře (nastroje/topeni_modely.py). Funkce:
  nacti(p) -> (j, b, zbytek)        json, bytearray binárního bloku, zbytek souboru za ním
  uloz(p, j, b, zbytek=b"")
  cti(j, b, i) -> ndarray (n, k)    accessor i (i s byteStride)
  pridej(j, b, data, typ)           nový accessor na konci bufferu (typ: "f" float32 s min/max, "i" indexy uint32, "a" atribut float32)
  rozrizni(A, I, osa, c, vyber)     rozřízne vybrané trojúhelníky rovinou souřadnice osa = c (atributy lineárně, body řezu sdílené)
  smaz_uzly(j, jmena)              odstraní uzly (i s potomky) a přečísluje odkazy
  matice(n)                         4×4 místní matice uzlu"""
import json, struct
import numpy as np

CT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def nacti(p):
    f = open(p, "rb").read()
    n = struct.unpack("<I", f[12:16])[0]; j = json.loads(f[20:20 + n])
    o = 20 + n
    if o >= len(f): return j, bytearray(), b""
    bl = struct.unpack("<I", f[o:o + 4])[0]
    return j, bytearray(f[o + 8:o + 8 + bl]), f[o + 8 + bl:]


def uloz(p, j, b, zbytek=b""):
    b = bytes(b) + b"\0" * ((4 - len(b) % 4) % 4)
    if j.get("buffers"): j["buffers"][0]["byteLength"] = len(b)
    js = json.dumps(j, separators=(",", ":"), ensure_ascii=False).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    dl = 12 + 8 + len(js) + (8 + len(b) if len(b) else 0) + len(zbytek)
    out = struct.pack("<III", 0x46546C67, 2, dl) + struct.pack("<I", len(js)) + b"JSON" + js
    if len(b): out += struct.pack("<I", len(b)) + b"BIN\0" + b
    open(p, "wb").write(out + zbytek)


def cti(j, b, i):
    a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]; nc = NC[a["type"]]; dt = np.dtype(CT[a["componentType"]])
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0); st = bv.get("byteStride", 0) or dt.itemsize * nc
    if st == dt.itemsize * nc:
        return np.frombuffer(bytes(b[off:off + a["count"] * st]), dtype=dt).reshape(a["count"], nc).copy()
    return np.array([np.frombuffer(bytes(b[off + k * st:off + k * st + dt.itemsize * nc]), dtype=dt) for k in range(a["count"])])


def jako_float(j, i, d):
    """data accessoru i → float64 (normalizované celé typy na 0…1)"""
    a = j["accessors"][i]
    if a.get("normalized"): return d.astype(np.float64) / float(np.iinfo(d.dtype).max)
    return d.astype(np.float64)


def z_floatu(j, i, d):
    a = j["accessors"][i]; dt = np.dtype(CT[a["componentType"]])
    if a.get("normalized"): return np.clip(np.round(d * np.iinfo(dt).max), 0, np.iinfo(dt).max).astype(dt)
    if dt.kind in "iu": return np.round(d).astype(dt)
    return d.astype(dt)


def pridej(j, b, data, typ="f", vzor=None):
    """typ "f" = POSITION (min/max), "i" = indexy uint32, "a" = jiný atribut; vzor = accessor, jehož componentType/normalized převzít"""
    if typ == "i": d = np.ascontiguousarray(data.astype(np.uint32).reshape(-1))
    elif vzor is not None: d = np.ascontiguousarray(data)
    else: d = np.ascontiguousarray(data.astype(np.float32))
    b.extend(b"\0" * ((4 - len(b) % 4) % 4)); off = len(b); b.extend(d.tobytes())
    j["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": d.nbytes, "target": 34963 if typ == "i" else 34962})
    a = {"bufferView": len(j["bufferViews"]) - 1, "count": len(d)}
    if typ == "i": a.update(componentType=5125, type="SCALAR")
    else:
        a["type"] = {1: "SCALAR", 2: "VEC2", 3: "VEC3", 4: "VEC4"}[d.shape[1]]
        if vzor is not None:
            a["componentType"] = j["accessors"][vzor]["componentType"]
            if j["accessors"][vzor].get("normalized"): a["normalized"] = True
        else: a["componentType"] = 5126
    if typ == "f": a["min"] = d.min(0).tolist(); a["max"] = d.max(0).tolist()
    j["accessors"].append(a); return len(j["accessors"]) - 1


def rozrizni(A, I, osa, c, vyber):
    """Rozřízne trojúhelníky I[vyber] protínající rovinu P[:, osa] = c na 3 trojúhelníky (1 + čtyřúhelník); A = {atribut: float pole},
    nové vrcholy na hranách (sdílené mezi sousedy – bez trhlin). Vrací (A, I)."""
    P = A["POSITION"]; d = P[:, osa] - c
    s = np.sign(np.where(np.abs(d) < 1e-7, 0.0, d))
    T = I[vyber]; st = s[T]
    kriz = (st.max(1) > 0) & (st.min(1) < 0)
    if not kriz.any(): return A, I
    nove = {k: [] for k in A}; klic = {}; n0 = len(P)
    def bod(u, v):
        k = (min(u, v), max(u, v))
        if k not in klic:
            t = d[u] / (d[u] - d[v])
            for a in A: nove[a].append(A[a][u] + (A[a][v] - A[a][u]) * t)
            klic[k] = n0 + len(klic)
        return klic[k]
    tri = []
    for f in T[kriz]:
        pol = []
        for r in range(3):
            u, v = int(f[r]), int(f[(r + 1) % 3]); pol.append(u)
            if s[u] * s[v] < 0: pol.append(bod(u, v))
        # rozdělit mnohoúhelník (4–5 vrcholů) podle strany roviny: dvě části, každá vějířem
        for zn in (1, -1):
            cast = [q for q in pol if (s[q] if q < n0 else 0) * zn >= 0]
            for i in range(1, len(cast) - 1): tri.append((cast[0], cast[i], cast[i + 1]))
    if nove["POSITION"]:
        A = {k: np.vstack([A[k], np.array(nove[k])]) for k in A}
    idx = np.where(vyber)[0][kriz]
    I = np.vstack([np.delete(I, idx, axis=0), np.array(tri, dtype=np.int64).reshape(-1, 3)])
    return A, I


def matice(n):
    if "matrix" in n: return np.array(n["matrix"], float).reshape(4, 4).T
    t = n.get("translation", [0, 0, 0]); r = n.get("rotation", [0, 0, 0, 1]); s = n.get("scale", [1, 1, 1])
    x, y, z, w = r
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4); M[:3, :3] = R * np.array(s); M[:3, 3] = t; return M


def smaz_uzly(j, jmena):
    """odstraní uzly daných jmen i s potomky; přečísluje children, scenes, skins; vrátí počet odstraněných"""
    pryc = set()
    def pridej_(i):
        pryc.add(i)
        for c in j["nodes"][i].get("children", []): pridej_(c)
    for i, n in enumerate(j["nodes"]):
        if n.get("name") in jmena: pridej_(i)
    if not pryc: return 0
    nove = {}; seznam = []
    for i, n in enumerate(j["nodes"]):
        if i not in pryc: nove[i] = len(seznam); seznam.append(n)
    for n in seznam:
        if "children" in n:
            n["children"] = [nove[c] for c in n["children"] if c in nove]
            if not n["children"]: del n["children"]
    for s in j.get("scenes", []):
        s["nodes"] = [nove[c] for c in s.get("nodes", []) if c in nove]
    for sk in j.get("skins", []):
        sk["joints"] = [nove[c] for c in sk["joints"] if c in nove]
    j["nodes"] = seznam
    return len(pryc)


def zhutni(j, b):
    """nový binární blok jen s bufferView, na které něco odkazuje (accessory, obrázky) – po úpravách přes pridej() zůstávají
    stará data nevyužitá; vrací nový bytearray"""
    # accessory, na které nic neodkazuje (smazané primitivy, nahrazená data) – Godot odmítne i neodkazovaný accessor s 0 prvky
    ref = set()
    for m in j.get("meshes", []):
        for p in m["primitives"]:
            ref |= set(p["attributes"].values())
            if "indices" in p: ref.add(p["indices"])
            for t in p.get("targets", []): ref |= set(t.values())
    for sk in j.get("skins", []):
        if "inverseBindMatrices" in sk: ref.add(sk["inverseBindMatrices"])
    for an in j.get("animations", []):
        for sm in an["samplers"]: ref |= {sm["input"], sm["output"]}
    am = {}; acs = []
    for i, a in enumerate(j["accessors"]):
        if i in ref: am[i] = len(acs); acs.append(a)
    j["accessors"] = acs
    for m in j.get("meshes", []):
        for p in m["primitives"]:
            p["attributes"] = {k: am[v] for k, v in p["attributes"].items()}
            if "indices" in p: p["indices"] = am[p["indices"]]
            if "targets" in p: p["targets"] = [{k: am[v] for k, v in t.items()} for t in p["targets"]]
    for sk in j.get("skins", []):
        if "inverseBindMatrices" in sk: sk["inverseBindMatrices"] = am[sk["inverseBindMatrices"]]
    for an in j.get("animations", []):
        for sm in an["samplers"]: sm["input"] = am[sm["input"]]; sm["output"] = am[sm["output"]]
    pouzite = sorted({a["bufferView"] for a in j["accessors"] if "bufferView" in a} | {i["bufferView"] for i in j.get("images", []) if "bufferView" in i})
    nb = bytearray(); mapa = {}; bvs = []
    for i in pouzite:
        bv = dict(j["bufferViews"][i]); o = bv.get("byteOffset", 0)
        nb.extend(b"\0" * ((4 - len(nb) % 4) % 4)); bv["byteOffset"] = len(nb); nb.extend(b[o:o + bv["byteLength"]])
        mapa[i] = len(bvs); bvs.append(bv)
    for a in j["accessors"]:
        if "bufferView" in a: a["bufferView"] = mapa[a["bufferView"]]
    for im in j.get("images", []):
        if "bufferView" in im: im["bufferView"] = mapa[im["bufferView"]]
    j["bufferViews"] = bvs
    return nb
