"""Zesvetleni domu vsi podle Pucharta (Misa 14. 11.). Pravidla pravidla/svet/modely.json ves_jas.
python3 tools/zesvetli_ves.py [--jen-vypis]   - textury modely/ves/domy_*_(diff|albedo).jpg, barvy vrcholu domy_stredni.glb,
barva materialu _Daleko v domy.glb. Prepocet na cil = opakovane spusteni nic nemeni."""
import glob, json, struct, sys, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
R = json.load(open("pravidla/svet/modely.json"))["ves_jas"]
VYPIS = "--jen-vypis" in sys.argv
LUM = np.array([0.2126, 0.7152, 0.0722])


def cil_pro(jm):
    if any(k in jm for k in R["vynechat"]):
        return None, None
    if any(k in jm for k in R["zacouzene"]["pripony"]):
        return R["zacouzene"]["cil"], R["zacouzene"]["max_x"]
    return R["cil"], R["max_x"]


def uprav(rgb, k):
    """rgb sRGB 0..1 (N,3): jas x k, sytost (jako Godot adjust_bcs)."""
    rgb = np.clip(rgb * k, 0, 1)
    g = (rgb @ LUM)[..., None]
    return np.clip(g + (rgb - g) * R["sytost"], 0, 1)


# znacka zpracovani (14. 11.: textury zastropene max_x zustanou pod cilem - druhe spusteni by je zesvetlilo znovu)
import hashlib
ZN = "modely/ves/zesvetleno.json"
zn = json.load(open(ZN)) if os.path.exists(ZN) else {}


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


# 1) textury
for f in sorted(f for v in R["textury"] for f in glob.glob(v)):
    jm = os.path.basename(f)
    cil, mx = cil_pro(jm)
    if cil is None or zn.get(jm) == md5(f):
        continue
    im = Image.open(f).convert("RGB")
    a = np.asarray(im).astype(float) / 255
    j = float((a @ LUM).mean())
    if j >= cil * 0.98 or j <= 0.005:
        continue
    k = min(cil / j, mx)
    print("TEXTURA %-42s %.3f -> x%.2f" % (jm, j, k))
    if not VYPIS:
        b = uprav(a.reshape(-1, 3), k).reshape(a.shape)
        Image.fromarray((b * 255 + 0.5).astype(np.uint8)).save(f, quality=92)
        zn[jm] = md5(f)


# 2) glb: barvy vrcholu (stredni) a barva materialu _Daleko
def glb_cti(p):
    d = open(p, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    js = json.loads(d[20:20 + jl])
    bo = 20 + jl
    bl = struct.unpack("<I", d[bo:bo + 4])[0]
    return js, bytearray(d[bo + 8:bo + 8 + bl])


def glb_zapis(p, js, bin_):
    j = json.dumps(js, separators=(",", ":")).encode()
    j += b" " * ((4 - len(j) % 4) % 4)
    bin_ = bytes(bin_) + b"\0" * ((4 - len(bin_) % 4) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(bin_)) + struct.pack("<II", len(j), 0x4E4F534A) + j \
        + struct.pack("<II", len(bin_), 0x004E4942) + bin_
    open(p, "wb").write(out)


def srgb(x):
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - 0.055)


def lin(x):
    return np.where(x <= 0.04045, x / 12.92, np.power((x + 0.055) / 1.055, 2.4))


def barva_jas(rgb_lin):
    s = srgb(rgb_lin)
    j = s @ LUM
    k = np.where((j < R["cil"]) & (j > 0.01), np.minimum(R["cil"] / np.maximum(j, 1e-6), R["max_x"]), 1.0)
    return lin(np.clip(s * k[..., None], 0, 1))


for p, druh in (("modely/ves/domy_stredni.glb", "stredni"), ("modely/ves/domy.glb", "daleko")):
    if not os.path.exists(p):
        continue
    js, b = glb_cti(p)
    if js.get("asset", {}).get("extras", {}).get("zesvetleno"):
        print("GLB %s: uz zesvetleno" % p)
        continue
    js.setdefault("asset", {}).setdefault("extras", {})["zesvetleno"] = True
    zmen = 0
    if druh == "stredni":
        hot = set()
        for m in js["meshes"]:
            for pr in m["primitives"]:
                ai = pr["attributes"].get("COLOR_0")
                if ai is None or ai in hot:
                    continue
                hot.add(ai)
                a = js["accessors"][ai]
                v = js["bufferViews"][a["bufferView"]]
                n = {"VEC3": 3, "VEC4": 4}[a["type"]]
                off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
                st = v.get("byteStride", 0)
                dt = {5126: np.float32, 5121: np.uint8, 5123: np.uint16}[a["componentType"]]
                sz = np.dtype(dt).itemsize
                if st and st != n * sz:
                    print("STREDNI preskoceno (prokladane) accessor", ai)
                    continue
                arr = np.frombuffer(b, dt, a["count"] * n, off).reshape(-1, n).astype(float)
                norm = {np.float32: 1.0, np.uint8: 255.0, np.uint16: 65535.0}[dt]
                rgb = arr[:, :3] / norm
                nove = barva_jas(rgb)
                if np.allclose(nove, rgb, atol=1e-3):
                    continue
                arr[:, :3] = nove * norm
                b[off:off + a["count"] * n * sz] = arr.astype(dt).tobytes()
                zmen += 1
        pass
    if druh == "daleko":
        # obrazky zabalene v domy.glb (Godot je pri importu vybaluje do domy_<jmeno>.jpg) - stejne jako soubory vyse
        import io
        vys = [bytes(b[js["bufferViews"][i].get("byteOffset", 0):js["bufferViews"][i].get("byteOffset", 0) + js["bufferViews"][i]["byteLength"]]) for i in range(len(js["bufferViews"]))]
        for im_ in js.get("images", []):
            jm = "domy_" + im_.get("name", "") + "_" + ("diff" if "diff" in im_.get("name", "") else "")
            jm = "domy_" + im_.get("name", "")
            if not ("diff" in jm or "albedo" in jm):
                continue
            cil, mx = cil_pro(jm)
            if cil is None or "bufferView" not in im_:
                continue
            raw = vys[im_["bufferView"]]
            pil = Image.open(io.BytesIO(raw)).convert("RGB")
            a = np.asarray(pil).astype(float) / 255
            j = float((a @ LUM).mean())
            if j >= cil * 0.98 or j <= 0.005:
                continue
            k = min(cil / j, mx)
            print("GLB OBRAZEK %-36s %.3f -> x%.2f" % (im_["name"], j, k))
            out = io.BytesIO()
            Image.fromarray((uprav(a.reshape(-1, 3), k).reshape(a.shape) * 255 + 0.5).astype(np.uint8)).save(out, "JPEG", quality=92)
            vys[im_["bufferView"]] = out.getvalue()
            im_["mimeType"] = "image/jpeg"
            zmen += 1
        nb = bytearray()
        for i, v in enumerate(vys):
            nb += b"\0" * ((4 - len(nb) % 4) % 4)
            js["bufferViews"][i]["byteOffset"] = len(nb)
            js["bufferViews"][i]["byteLength"] = len(v)
            nb += v
        js["buffers"][0]["byteLength"] = len(nb)
        b = nb
    if druh == "daleko":
        mats = set()
        for nd in js["nodes"]:
            if "mesh" in nd and nd.get("name", "").endswith("_Daleko"):
                for pr in js["meshes"][nd["mesh"]]["primitives"]:
                    if "material" in pr:
                        mats.add(pr["material"])
        for mi in mats:
            pbr = js["materials"][mi].setdefault("pbrMetallicRoughness", {})
            if "baseColorTexture" in pbr:
                continue
            c = np.array(pbr.get("baseColorFactor", [1, 1, 1, 1]), float)
            nc = barva_jas(c[:3])
            if not np.allclose(nc, c[:3], atol=1e-3):
                pbr["baseColorFactor"] = [float(x) for x in nc] + [float(c[3])]
                zmen += 1
    print("GLB %s: zmeneno %d" % (p, zmen))
    if zmen and not VYPIS:
        glb_zapis(p, js, b)

if not VYPIS:
    json.dump(zn, open(ZN, "w"), indent=1)


# 3) hnede drevo (ves_jas.hneda): sede drevo na hnedy pomer pri stejnem jasu; idempotentni (po uprave B/R pod prahem)
H = R["hneda"]


def je_drevo(jm):
    return any(k in jm for k in H["pripony"]) and not any(k in jm for k in R["vynechat"]) \
        and not any(k in jm for k in R["zacouzene"]["pripony"])


def hneda(a):
    """a sRGB 0..1 (H,W,3) -> (nove, nebo None kdyz netreba)."""
    m = a.reshape(-1, 3).mean(0)
    if m[0] <= 0.01 or m[2] / m[0] <= H["prah_br"]:
        return None
    po = np.array(H["pomer"], float)
    cil = po * (m @ LUM) / (po @ LUM)
    return np.clip(a * (cil / np.maximum(m, 1e-4)), 0, 1)


import io
for f in sorted(f for v in R["textury"] for f in glob.glob(v)):
    jm = os.path.basename(f)
    if not je_drevo(jm):
        continue
    a = np.asarray(Image.open(f).convert("RGB")).astype(float) / 255
    b = hneda(a)
    if b is None:
        continue
    print("HNEDA %-42s B/R %.2f" % (jm, a.reshape(-1, 3).mean(0)[2] / a.reshape(-1, 3).mean(0)[0]))
    if not VYPIS:
        Image.fromarray((b * 255 + 0.5).astype(np.uint8)).save(f, quality=92)
        zn[jm] = md5(f)          # znacka kroku 1 na novy obsah (jinak by krok 1 pri dalsim behu zesvetlil znovu)
if not VYPIS:
    json.dump(zn, open(ZN, "w"), indent=1)
p = "modely/ves/domy.glb"
if os.path.exists(p):
    js, bb = glb_cti(p)
    vys = [bytes(bb[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]) for v in js["bufferViews"]]
    zmen = 0
    for im_ in js.get("images", []):
        jm = "domy_" + im_.get("name", "")
        if "bufferView" not in im_ or not je_drevo(jm) or not ("diff" in jm or "albedo" in jm):
            continue
        a = np.asarray(Image.open(io.BytesIO(vys[im_["bufferView"]])).convert("RGB")).astype(float) / 255
        b = hneda(a)
        if b is None:
            continue
        print("HNEDA GLB %-36s" % im_["name"])
        out = io.BytesIO()
        Image.fromarray((b * 255 + 0.5).astype(np.uint8)).save(out, "JPEG", quality=92)
        vys[im_["bufferView"]] = out.getvalue()
        im_["mimeType"] = "image/jpeg"
        zmen += 1
    if zmen and not VYPIS:
        nb = bytearray()
        for i, v in enumerate(vys):
            nb += b"\0" * ((4 - len(nb) % 4) % 4)
            js["bufferViews"][i]["byteOffset"] = len(nb)
            js["bufferViews"][i]["byteLength"] = len(v)
            nb += v
        js["buffers"][0]["byteLength"] = len(nb)
        glb_zapis(p, js, nb)
    print("HNEDA GLB zmeneno %d" % zmen)


# 4) jas podrobneho modelu (ves_jas.jas_podrobny, Misa 15. 11. ř. 10 „bile budovy vzadu, chce hnede jako Puchart“):
# vnejsek domu (textury po zesvetleni, i omitka) x jas_podrobny jednou - znacka podrobny:<jmeno> (soubor) a
# asset.extras.podrobny (domy.glb); znacka kroku 1 na novy obsah (jinak by krok 1 pri dalsim behu zesvetlil zpet)
JP = float(R.get("jas_podrobny", 1.0))


def je_podrobny(jm):
    return not any(k in jm for k in R.get("jas_podrobny_vynechat", [])) and not any(k in jm for k in R["zacouzene"]["pripony"])


if JP < 1.0:
    for f in sorted(f for v in R.get("jas_podrobny_textury", []) for f in glob.glob(v)):
        jm = os.path.basename(f)
        if not je_podrobny(jm) or zn.get("podrobny:" + jm) == md5(f):
            continue
        print("PODROBNY %-42s x%.2f" % (jm, JP))
        if not VYPIS:
            a = np.asarray(Image.open(f).convert("RGB")).astype(float) / 255
            Image.fromarray((np.clip(a * JP, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f, quality=92)
            zn[jm] = zn["podrobny:" + jm] = md5(f)
    if not VYPIS:
        json.dump(zn, open(ZN, "w"), indent=1)
    p = "modely/ves/domy.glb"
    if os.path.exists(p):
        js, bb = glb_cti(p)
        ex = js.setdefault("asset", {}).setdefault("extras", {})
        if ex.get("podrobny") != JP:
            k_ = JP / float(ex.get("podrobny", 1.0))
            vys = [bytes(bb[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]) for v in js["bufferViews"]]
            zmen = 0
            for im_ in js.get("images", []):
                jm = "domy_" + im_.get("name", "")
                if "bufferView" not in im_ or not je_podrobny(jm) or not ("diff" in jm or "albedo" in jm):
                    continue
                a = np.asarray(Image.open(io.BytesIO(vys[im_["bufferView"]])).convert("RGB")).astype(float) / 255
                out = io.BytesIO()
                Image.fromarray((np.clip(a * k_, 0, 1) * 255 + 0.5).astype(np.uint8)).save(out, "JPEG", quality=92)
                vys[im_["bufferView"]] = out.getvalue()
                im_["mimeType"] = "image/jpeg"
                zmen += 1
            ex["podrobny"] = JP
            print("PODROBNY GLB zmeneno %d (x%.2f)" % (zmen, k_))
            if not VYPIS:
                nb = bytearray()
                for i, v in enumerate(vys):
                    nb += b"\0" * ((4 - len(nb) % 4) % 4)
                    js["bufferViews"][i]["byteOffset"] = len(nb)
                    js["bufferViews"][i]["byteLength"] = len(v)
                    nb += v
                js["buffers"][0]["byteLength"] = len(nb)
                glb_zapis(p, js, nb)


# 5) hnedy ton stredniho a dalkoveho stupne (ves_jas.stredni_daleko, Puchart modely.domy.daleko_textury.jas): barva
# (sRGB) stazena na jas nejvys jas_strop, pak x cinitel strechy / sten. Znacka asset.extras.stredni_daleko = pouzite
# cinitele; pri zmene cinitelu jen pomer novy/stary (puvodni barva uz v souboru neni).
SD = R["stredni_daleko"]
CIN = {"strecha": np.array(SD["strecha"], float), "steny": np.array(SD["steny"], float)}


def _acc(js, b, ai):
    """(pole float (N, n), zapis(pole)) pro accessor ai (i s byteStride)."""
    a = js["accessors"][ai]
    v = js["bufferViews"][a["bufferView"]]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    dt = {5126: np.float32, 5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[a["componentType"]]
    sz = np.dtype(dt).itemsize
    off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    st = v.get("byteStride", 0) or n * sz
    raw = np.frombuffer(bytes(b[off:off + st * (a["count"] - 1) + n * sz]), np.uint8)
    idx = (np.arange(a["count"])[:, None] * st + np.arange(n * sz)[None, :]).ravel()
    arr = raw[idx].view(dt).reshape(-1, n).astype(float)

    def zapis(nove):
        cel = np.frombuffer(bytes(b[off:off + st * (a["count"] - 1) + n * sz]), np.uint8).copy()
        cel[idx] = np.frombuffer(nove.astype(dt).tobytes(), np.uint8)
        b[off:off + len(cel)] = cel.tobytes()
    return arr, zapis


def hneda_lod(s, cin, prvni):
    """s sRGB 0..1 (N, 3), cin (N, 3) cinitel -> sRGB."""
    if prvni:
        j = s @ LUM
        s = s * np.minimum(1.0, SD["jas_strop"] / np.maximum(j, 1e-6))[:, None]
    return np.clip(s * cin, 0, 1)


def cinitel(ex):
    """(cinitele strecha, steny k pouziti, prvni beh) podle znacky v asset.extras."""
    st = ex.get("stredni_daleko")
    if st is None:
        return CIN["strecha"], CIN["steny"], True
    return CIN["strecha"] / np.array(st["strecha"], float), CIN["steny"] / np.array(st["steny"], float), False


for p, druh in (("modely/ves/domy_stredni.glb", "stredni"), ("modely/ves/domy.glb", "daleko")):
    if not os.path.exists(p):
        continue
    js, b = glb_cti(p)
    ex = js.setdefault("asset", {}).setdefault("extras", {})
    if ex.get("stredni_daleko") == {"strecha": SD["strecha"], "steny": SD["steny"]}:
        print("HNEDY %s: uz hotovo" % p)
        continue
    c_st, c_sn, prvni = cinitel(ex)
    zmen = 0
    if druh == "stredni":
        hot = set()
        for m in js["meshes"]:
            for pr in m["primitives"]:
                ai = pr["attributes"].get("COLOR_0")
                if ai is None or ai in hot or "POSITION" not in pr["attributes"]:
                    continue
                hot.add(ai)
                col, zap = _acc(js, b, ai)
                pos = _acc(js, b, pr["attributes"]["POSITION"])[0]
                if "indices" in pr:
                    tri = _acc(js, b, pr["indices"])[0].astype(np.int64).reshape(-1, 3)
                else:
                    tri = np.arange(len(pos)).reshape(-1, 3)
                fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])     # 2 x plocha x normala
                acc = np.zeros_like(pos)
                for k in range(3):
                    np.add.at(acc, tri[:, k], fn)
                ny = acc[:, 1] / np.maximum(np.linalg.norm(acc, axis=1), 1e-9)
                cin = np.where((ny > SD["strecha_ny_min"])[:, None], c_st[None, :], c_sn[None, :])
                mx = {5121: 255.0, 5123: 65535.0}.get(js["accessors"][ai]["componentType"], 1.0)   # normalizovane cele
                rgb = col[:, :3] / mx
                s = hneda_lod(srgb(rgb), cin, prvni)
                col[:, :3] = lin(s) * mx
                if mx > 1.0:
                    col = np.round(col)
                zap(col)
                zmen += 1
    else:
        for nd in js["nodes"]:
            if "mesh" not in nd or not nd.get("name", "").endswith("_Daleko"):
                continue
            for pr in js["meshes"][nd["mesh"]]["primitives"]:
                if "material" not in pr:
                    continue
                mt = js["materials"][pr["material"]]
                pbr = mt.setdefault("pbrMetallicRoughness", {})
                if "baseColorTexture" in pbr or mt.get("extras", {}).get("hnedy"):
                    continue
                c = np.array(pbr.get("baseColorFactor", [1, 1, 1, 1]), float)
                cin = c_st if "_daleko_Sindel" in mt.get("name", "") else c_sn
                s = hneda_lod(srgb(c[None, :3]), cin[None, :], prvni)[0]
                pbr["baseColorFactor"] = [float(x) for x in lin(s)] + [float(c[3])]
                mt.setdefault("extras", {})["hnedy"] = True      # material sdileny vic uzly: jen jednou za beh
                zmen += 1
        for mt in js.get("materials", []):
            mt.get("extras", {}).pop("hnedy", None)
            if mt.get("extras") == {}:
                mt.pop("extras")
    ex["stredni_daleko"] = {"strecha": SD["strecha"], "steny": SD["steny"]}
    print("HNEDY %s: zmeneno %d (%s)" % (p, zmen, "prvni" if prvni else "pomer cinitelu"))
    if not VYPIS:
        glb_zapis(p, js, b)
