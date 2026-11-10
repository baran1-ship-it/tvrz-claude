"""Sdilene textury predmetu (Misa 10. 11.: zasek 0,5-1,9 s pri prvnim zobrazeni noveho predmetu - kovarna, ves, lom).
Priciny: modely/predmety/*.glb nesou vlozene obrazky (268 MB, z toho jen 139 MB unikatnich) a Godot kazdou kopii rozbali
zvlast (<id>_Image_N.*) -> stejna textura je v graficke pameti 12-21x a kazdy novy predmet nahrava vlastni kopii.
Reseni: obrazky se z glb vyjmou, ulozi JEDNOU podle md5 do slozky z pravidla/svet/kvalita.json textury_predmetu.slozka
a v glb zustane jen uri (stejna cesta res:// = jeden zdroj, jedna textura v pameti). Normalova mapa je zvlast soubor
(<md5>_n.*, import compress/normal_map=1), protoze Godot ji u externiho obrazku sam nepozna.
  python3 tools/textury_predmetu.py            prevede vsechna glb (idempotentni; vola ho blender/predmety.py build)
  python3 tools/textury_predmetu.py kontrola   rc 1 = vlozeny obrazek v glb, duplicitni md5 nebo textura nad mez
Po prevodu: godot --import (a smazat osirele <id>_Image_N.* tools/textury_predmetu.py uklid)."""
import glob
import hashlib
import io
import json
import os
import struct
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CFG = json.load(open("pravidla/svet/kvalita.json", encoding="utf-8"))["textury_predmetu"]
SLOZKA = CFG["slozka"]
MEZ = int(CFG["mez_px"])
LIMIT_IMPORTU = int(CFG["size_limit_importu"])
PRIPONA = {"image/png": ".png", "image/jpeg": ".jpg"}

IMPORT = """[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="res://%(rel)s"

[params]

compress/mode=2
compress/high_quality=false
compress/lossy_quality=0.7
compress/hdr_compression=1
compress/normal_map=%(nm)d
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=%(lim)d
detect_3d/compress_to=1
"""


def nacti(cesta):
    d = open(cesta, "rb").read()
    if d[:4] != b"glTF":
        raise ValueError(cesta + ": neni GLB")
    jl = struct.unpack_from("<I", d, 12)[0]
    j = json.loads(d[20:20 + jl])
    bl = struct.unpack_from("<I", d, 20 + jl)[0]
    return j, d[28 + jl:28 + jl + bl]


def zapis(cesta, j, b):
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * ((-len(js)) % 4)
    b += b"\0" * ((-len(b)) % 4)
    out = struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(b)) + struct.pack("<I4s", len(js), b"JSON") + js
    out += struct.pack("<I4s", len(b), b"BIN\0") + b
    open(cesta + ".tmp", "wb").write(out)
    os.replace(cesta + ".tmp", cesta)


def role_normal(j):
    """Index obrazku -> True, kdyz se pouzije jen jako normalTexture."""
    tex = j.get("textures", [])
    nm, jine = set(), set()
    for m in j.get("materials", []):
        pbr = m.get("pbrMetallicRoughness", {})
        for klic, cil in (("normalTexture", nm), ("baseColorTexture", jine), ("metallicRoughnessTexture", jine),
                          ("occlusionTexture", jine), ("emissiveTexture", jine)):
            t = m.get(klic) or pbr.get(klic)
            if t is not None and t["index"] < len(tex) and "source" in tex[t["index"]]:
                cil.add(tex[t["index"]]["source"])
    return {i: (i in nm and i not in jine) for i in nm | jine}


def preved(cesta):
    j, b = nacti(cesta)
    imgs = [(i, im) for i, im in enumerate(j.get("images", [])) if "bufferView" in im]
    if not imgs:
        return 0, 0
    roly = role_normal(j)
    pryc, ulozeno = set(), 0
    os.makedirs(SLOZKA, exist_ok=True)
    for i, im in imgs:
        bv = j["bufferViews"][im["bufferView"]]
        raw = b[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
        pr = PRIPONA.get(im.get("mimeType"), ".png")
        pil = Image.open(io.BytesIO(raw))
        if max(pil.size) > MEZ:                       # mez z dat: zmensit na nejvetsi stranu MEZ
            f = MEZ / max(pil.size)
            pil = pil.resize((max(1, round(pil.size[0] * f)), max(1, round(pil.size[1] * f))), Image.LANCZOS)
            buf = io.BytesIO()
            pil.save(buf, format="PNG" if pr == ".png" else "JPEG", **({} if pr == ".png" else {"quality": 92}))
            raw = buf.getvalue()
        nm = roly.get(i, False)
        jm = hashlib.md5(raw).hexdigest()[:16] + ("_n" if nm else "") + pr
        rel = SLOZKA + "/" + jm
        if not os.path.exists(rel):
            open(rel, "wb").write(raw)
            ulozeno += 1
        if not os.path.exists(rel + ".import"):
            open(rel + ".import", "w").write(IMPORT % {"rel": rel, "nm": 1 if nm else 0, "lim": LIMIT_IMPORTU})
        pryc.add(im["bufferView"])
        del im["bufferView"]
        im.pop("mimeType", None)
        im["uri"] = os.path.relpath(rel, os.path.dirname(cesta)).replace("\\", "/")
    # bufferViews bez obrazku zustanou, vyjmute se jen vlozene; indexy se prepisou
    nove, mapa, blob = [], {}, bytearray()
    for k, bv in enumerate(j["bufferViews"]):
        if k in pryc:
            continue
        data = b[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
        blob += b"\0" * ((-len(blob)) % 4)
        bv = dict(bv)
        bv["byteOffset"] = len(blob)
        blob += data
        mapa[k] = len(nove)
        nove.append(bv)
    for a in j.get("accessors", []):
        if "bufferView" in a:
            a["bufferView"] = mapa[a["bufferView"]]
        sp = a.get("sparse")
        if sp:
            sp["indices"]["bufferView"] = mapa[sp["indices"]["bufferView"]]
            sp["values"]["bufferView"] = mapa[sp["values"]["bufferView"]]
    j["bufferViews"] = nove
    j["buffers"][0]["byteLength"] = len(blob)
    zapis(cesta, j, bytes(blob))
    return len(imgs), ulozeno


def kontrola():
    chyby = []
    for g in sorted(glob.glob("modely/predmety/*.glb")):
        j, _ = nacti(g)
        n = sum(1 for im in j.get("images", []) if "bufferView" in im)
        if n:
            chyby.append("%s: %d vlozenych obrazku (spustit tools/textury_predmetu.py)" % (g, n))
    md5 = {}
    for f in sorted(glob.glob(SLOZKA + "/*")):
        if f.endswith(".import"):
            continue
        h = hashlib.md5(open(f, "rb").read()).hexdigest()
        if h in md5:
            chyby.append("%s a %s: stejny obsah (md5 %s)" % (md5[h], f, h))
        md5[h] = f
        if max(Image.open(f).size) > MEZ:
            chyby.append("%s: nad mez %d px" % (f, MEZ))
    return chyby


if __name__ == "__main__":
    if "kontrola" in sys.argv:
        ch = kontrola()
        print("TEXTURY_PREDMETU %s %s" % ("OK" if not ch else "CHYBA", ch[:20]))
        sys.exit(1 if ch else 0)
    n_img = n_nove = 0
    for g in sorted(glob.glob("modely/predmety/*.glb")):
        a, b_ = preved(g)
        n_img += a
        n_nove += b_
    print("textury predmetu: %d vlozenych obrazku prevedeno, %d novych souboru v %s" % (n_img, n_nove, SLOZKA))
