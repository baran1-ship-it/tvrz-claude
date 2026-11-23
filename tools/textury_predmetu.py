"""Sdilene textury predmetu (Misa 10. 11.: zasek 0,5-1,9 s pri prvnim zobrazeni noveho predmetu - kovarna, ves, lom).
Priciny: modely/predmety/*.glb nesou vlozene obrazky (268 MB, z toho jen 139 MB unikatnich) a Godot kazdou kopii rozbali
zvlast (<id>_Image_N.*) -> stejna textura je v graficke pameti 12-21x a kazdy novy predmet nahrava vlastni kopii.
Reseni: obrazky se z glb vyjmou, ulozi JEDNOU podle md5 do slozky z pravidla/svet/kvalita.json textury_predmetu.slozka
a v glb zustane jen uri (stejna cesta res:// = jeden zdroj, jedna textura v pameti). Normalova mapa je zvlast soubor
(<md5>_n.*, import compress/normal_map=1), protoze Godot ji u externiho obrazku sam nepozna.
Dily (Misa 16. 11., mereni 0.999999: zamrznuti po 2. kole trasy, textury +220 MB): stejny postup pro slozky modelu dilu
z Disku (kvalita.json textury_dilu.slozky_dilu: ruiny_ves 168 textur / 28 ruznych, krcma, kostel) do jedne spolecne
slozky textury_dilu.slozka; uklid smaze rozbalene kopie <model>_<obrazek>.* (+ .import a cache v .godot/imported).
  python3 tools/textury_predmetu.py            prevede vsechna glb predmetu (idempotentni; vola ho blender/predmety.py build)
  python3 tools/textury_predmetu.py dily       prevede glb dilu a uklidi rozbalene kopie (krok exportu tools/export.sh)
  python3 tools/textury_predmetu.py rostliny   (plan 18. 11. A2) glb rostlin z exportu -> kvalita.json textury_rostlin.slozka/<limit>/,
                                               rozbalene kopie v modely/rostliny pryc (krok exportu tools/export.sh)
  python3 tools/textury_predmetu.py kontrola   rc 1 = vlozeny obrazek v glb, duplicitni md5, textura nad mez nebo
                                               rozbalena kopie v slozce dilu (predmety i dily)
Po prevodu: godot --import."""
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
_KV = json.load(open("pravidla/svet/kvalita.json", encoding="utf-8"))
CFG = _KV["textury_predmetu"]
SLOZKA = CFG["slozka"]
MEZ = int(CFG["mez_px"])
LIMIT_IMPORTU = int(CFG["size_limit_importu"])
DILY = _KV["textury_dilu"]
ROSTLINY = _KV["textury_rostlin"]
OBRAZKY = (".png", ".jpg", ".jpeg", ".webp")
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


def preved(cesta, slozka=SLOZKA, mez=MEZ, lim=LIMIT_IMPORTU):
    j, b = nacti(cesta)
    imgs = [(i, im) for i, im in enumerate(j.get("images", [])) if "bufferView" in im]
    if not imgs:
        return 0, 0
    roly = role_normal(j)
    pryc, ulozeno = set(), 0
    os.makedirs(slozka, exist_ok=True)
    for i, im in imgs:
        bv = j["bufferViews"][im["bufferView"]]
        raw = b[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
        pr = PRIPONA.get(im.get("mimeType"), ".png")
        pil = Image.open(io.BytesIO(raw))
        if max(pil.size) > mez:                       # mez z dat: zmensit na nejvetsi stranu mez
            f = mez / max(pil.size)
            pil = pil.resize((max(1, round(pil.size[0] * f)), max(1, round(pil.size[1] * f))), Image.LANCZOS)
            buf = io.BytesIO()
            pil.save(buf, format="PNG" if pr == ".png" else "JPEG", **({} if pr == ".png" else {"quality": 92}))
            raw = buf.getvalue()
        nm = roly.get(i, False)
        jm = hashlib.md5(raw).hexdigest()[:16] + ("_n" if nm else "") + pr
        rel = slozka + "/" + jm
        if not os.path.exists(rel):
            open(rel, "wb").write(raw)
            ulozeno += 1
        if not os.path.exists(rel + ".import"):
            open(rel + ".import", "w").write(IMPORT % {"rel": rel, "nm": 1 if nm else 0, "lim": lim})
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


def rozbalene(slozka):
    """Kopie, ktere Godot rozbalil z vlozenych obrazku glb dilu (<model>_<jmeno obrazku>.*, i _N pri shode jmen)
    a .import bez zdroje (po smazani kopie) - po prevodu na uri uz nic nepouziva."""
    glb = {g[:-4]: [im.get("name", "") for im in nacti(g)[0].get("images", [])] for g in glob.glob(slozka + "/*.glb")}
    out = []
    for f in sorted(glob.glob(slozka + "/*")):
        zdroj = f[:-7] if f.endswith(".import") else f
        if not zdroj.lower().endswith(OBRAZKY):
            continue
        st = zdroj.rsplit(".", 1)[0]
        if any(st == g + "_" + n or (st.startswith(g + "_" + n + "_") and st[len(g + n) + 2:].isdigit())
               for g, jm in glb.items() for n in jm if n) or (f.endswith(".import") and not os.path.exists(zdroj)):
            out.append(f)
    return out


def uklid(slozka):
    n = 0
    for f in rozbalene(slozka):
        zdroj = f[:-7] if f.endswith(".import") else f
        for x in (zdroj, zdroj + ".import"):
            if os.path.exists(x):
                os.remove(x)
                n += 1
        for c in glob.glob(".godot/imported/%s-*" % glob.escape(os.path.basename(zdroj))):
            os.remove(c)
    return n


def zavislosti(cesta):
    """Textury ze spolecne slozky, na ktere glb odkazuje (uri) - tools/vydani.py je da do baliku dilu."""
    d = os.path.dirname(cesta)
    return sorted({os.path.normpath(os.path.join(d, im["uri"])) for im in nacti(cesta)[0].get("images", []) if "uri" in im})


def _kontrola_slozky(glby, slozka, mez, jak):
    chyby = []
    for g in glby:
        j, _ = nacti(g)
        n = sum(1 for im in j.get("images", []) if "bufferView" in im)
        if n:
            chyby.append("%s: %d vlozenych obrazku (spustit tools/textury_predmetu.py%s)" % (g, n, jak))
        for z in zavislosti(g):
            if not os.path.exists(z) and not os.path.exists(z + ".import"):
                chyby.append("%s: chybi textura %s" % (g, z))
    md5 = {}
    for f in sorted(glob.glob(slozka + "/*")):
        if f.endswith(".import"):
            continue
        h = hashlib.md5(open(f, "rb").read()).hexdigest()
        if h in md5:
            chyby.append("%s a %s: stejny obsah (md5 %s)" % (md5[h], f, h))
        md5[h] = f
        if max(Image.open(f).size) > mez:
            chyby.append("%s: nad mez %d px" % (f, mez))
    return chyby


def kontrola():
    chyby = _kontrola_slozky(sorted(glob.glob("modely/predmety/*.glb")), SLOZKA, MEZ, "")
    glby = sorted(g for s in DILY["slozky_dilu"] for g in glob.glob(s + "/*.glb"))
    chyby += _kontrola_slozky(glby, DILY["slozka"], int(DILY["mez_px"]), " dily")
    for lim_sl in sorted(glob.glob(ROSTLINY["slozka"] + "/*")):
        chyby += _kontrola_slozky([], lim_sl, int(os.path.basename(lim_sl)), " rostliny")
    chyby += _kontrola_slozky(sorted(glob.glob(ROSTLINY["soubory"])), "/nic", 0, " rostliny")   # jen glb (vlozene, chybejici)
    for s in DILY["slozky_dilu"]:
        r = rozbalene(s)
        if r:
            chyby.append("%s: %d rozbalenych kopii obrazku (napr. %s; tools/textury_predmetu.py dily)" % (s, len(r), r[0]))
    return chyby


if __name__ == "__main__":
    if "kontrola" in sys.argv:
        ch = kontrola()
        print("TEXTURY_PREDMETU %s %s" % ("OK" if not ch else "CHYBA", ch[:20]))
        sys.exit(1 if ch else 0)
    if "rostliny" in sys.argv:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        from limity_textur import limit as _limit          # jeden zdroj limitu importu rostlin (stromy, skaly 1024, jinak 512)
        n_img = n_nove = 0
        for g in sorted(glob.glob(ROSTLINY["soubory"])):
            lim = _limit(g[:-4] + "_x.png")
            a, b_ = preved(g, "%s/%d" % (ROSTLINY["slozka"], lim), lim, lim)
            n_img += a
            n_nove += b_
        n_pryc = uklid(os.path.dirname(ROSTLINY["soubory"]))
        print("textury rostlin: %d vlozenych obrazku prevedeno, %d novych souboru v %s, %d rozbalenych kopii smazano"
              % (n_img, n_nove, ROSTLINY["slozka"], n_pryc))
        sys.exit(0)
    if "dily" in sys.argv:
        n_img = n_nove = n_pryc = 0
        for sl in DILY["slozky_dilu"]:
            for g in sorted(glob.glob(sl + "/*.glb")):
                a, b_ = preved(g, DILY["slozka"], int(DILY["mez_px"]), int(DILY["size_limit_importu"]))
                n_img += a
                n_nove += b_
            n_pryc += uklid(sl)
        print("textury dilu: %d vlozenych obrazku prevedeno, %d novych souboru v %s, %d rozbalenych kopii smazano"
              % (n_img, n_nove, DILY["slozka"], n_pryc))
        sys.exit(0)
    n_img = n_nove = 0
    for g in sorted(glob.glob("modely/predmety/*.glb")):
        a, b_ = preved(g)
        n_img += a
        n_nove += b_
    print("textury predmetu: %d vlozenych obrazku prevedeno, %d novych souboru v %s" % (n_img, n_nove, SLOZKA))
