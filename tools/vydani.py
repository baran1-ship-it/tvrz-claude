"""Vydani hry: herni data mimo APK jako samostatne baliky (svet + kazdy predmet zvlast), velke rozdelene
na casti pod GitHub limit. Balik se znovu sestavi jen kdyz se zmenily jeho zdrojove soubory; hra si stahne
jen baliky, ktere jeste nema.
  python3 tools/vydani.py 0.17 [--vulkan]
Vysledek: data/<balik>-<md5>.pck.NNN (do repozitare), data_manifest.json (v APK), apk/OdkazHavrana-<verze>.apk
  --jen z_reka,...  kontejner bez zdrojovych dat (jen rozbalene baliky): neimportuje, nekalibruje, ostatni baliky
  necha z minuleho manifestu a sestavi jen vyjmenovane; z_<jmeno> = oprava, hra ji nacte posledni s prepisem."""
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

GODOT = "/opt/godot/Godot_v4.4.1-stable_linux.x86_64"
PART = 90 * 1024 * 1024
ver = sys.argv[1]
JEN = sys.argv[sys.argv.index("--jen") + 1].split(",") if "--jen" in sys.argv else None
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
env = dict(os.environ, GODOT_ANDROID_KEYSTORE_RELEASE_PATH="/root/keys/tvrz_release.keystore",
           GODOT_ANDROID_KEYSTORE_RELEASE_USER="havran", GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD="havran2026")
os.makedirs("build/packs", exist_ok=True)
# rozpocet graficke pameti: limity textur a reimport pred kazdym vydanim
if JEN is None:                 # bez zdrojovych .jpg by albedo_textur prepsal kalibraci a import nema co delat
    subprocess.run([sys.executable, "tools/limity_textur.py"], check=True)
    if len(glob.glob("modely/textury/*_diff.jpg")) > 10:      # bez zdrojovych fotek by prepsal kalibraci (albedo.json)
        subprocess.run([sys.executable, "tools/albedo_textur.py"], check=True)
    subprocess.run([GODOT, "--headless", "--path", ".", "--import"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3600)
# verze do instalacniho balicku (Android ji ukazuje v hlaseni o padu) i do projektu (hlidac padu)
import re as _re
_ep = open("export_presets.cfg").read()
_sec = _ep.index('name="Android Data"')
_hd = _re.sub(r'version/name="[^"]*"', 'version/name="%s"' % ver, _ep[:_sec])
_hd = _re.sub(r'version/code=\d+', 'version/code=%d' % int(round(float(ver) * 100)), _hd)
open("export_presets.cfg", "w").write(_hd + _ep[_sec:])
_pg = open("project.godot").read()
open("project.godot", "w").write(_re.sub(r'config/version="[^"]*"', 'config/version="%s"' % ver, _pg))
PRESETS = open("export_presets.cfg").read()


def src_hash(files):
    h = hashlib.md5()
    for f in sorted(files):
        h.update(f.encode())
        with open(f, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()


def preset_with(data_filter, files=None):
    """Kopie export_presets.cfg, kde preset 'Android Data' exportuje jen danou skupinu."""
    sec = PRESETS.index('name="Android Data"')
    head, tail = PRESETS[:sec], PRESETS[sec:]
    end = tail.index("[preset.1.options]")
    body, rest = tail[:end], tail[end:]
    if files is not None:
        body = re.sub(r'export_filter="[^"]*"', 'export_filter="resources"', body)
        lst = ", ".join('"res://%s"' % f for f in files)
        body = re.sub(r'\ninclude_filter="[^"]*"', '\nexport_files=PackedStringArray(%s)\ninclude_filter=""' % lst, body)
        body = body.replace("hudba/*, zvuky/*, ", "")          # zvukovy balik: hudba a ruchy nesmi byt vyloucene
    else:
        body = re.sub(r'exclude_filter="([^"]*)"', lambda m: 'exclude_filter="%s, %s"' % (m.group(1), data_filter), body)
    return head + body + rest


def export_pack(name, cfg):
    open("export_presets.cfg", "w").write(cfg)
    out = "build/packs/%s.pck" % name
    try:
        subprocess.run([GODOT, "--headless", "--path", ".", "--export-pack", "Android Data", out], env=env, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        open("export_presets.cfg", "w").write(PRESETS)
    return out


def jen_data(path):
    """Opravny balik z_* se nacita s prepisem: nechat v nem jen modely/ a .godot/imported/ (project.binary, seznam UID
    a ikona plati z APK - starsi oprava by jinak prebila novejsi APK). PCK v2 (Godot 4.4)."""
    import struct
    d = open(path, "rb").read()
    ver_hdr = d[:20]
    flags, base = struct.unpack_from("<IQ", d, 20)
    pos = 20 + 12 + 64
    n = struct.unpack_from("<I", d, pos)[0]
    pos += 4
    ents = []
    for _ in range(n):
        ln = struct.unpack_from("<I", d, pos)[0]
        pth = d[pos + 4:pos + 4 + ln]
        off, sz = struct.unpack_from("<QQ", d, pos + 4 + ln)
        md5 = d[pos + 4 + ln + 16:pos + 4 + ln + 32]
        fl = struct.unpack_from("<I", d, pos + 4 + ln + 32)[0]
        pos += 4 + ln + 36
        name = pth.rstrip(b"\0").decode()
        if name.startswith(("res://modely/", "res://.godot/imported/", "modely/", ".godot/imported/")):
            ents.append((pth, d[base + off:base + off + sz], md5, fl))
    tab = b"".join(struct.pack("<I", len(pth)) + pth + struct.pack("<QQ", 0, 0) + md5 + struct.pack("<I", fl) for pth, _, md5, fl in ents)
    hdr_len = 20 + 12 + 64 + 4 + len(tab)
    base2 = (hdr_len + 31) // 32 * 32
    out = bytearray(ver_hdr + struct.pack("<IQ", flags & ~2, base2) + b"\0" * 64 + struct.pack("<I", len(ents)))
    blob = bytearray()
    p2 = len(out)
    for pth, data, md5, fl in ents:
        out += struct.pack("<I", len(pth)) + pth + struct.pack("<QQ", len(blob), len(data)) + md5 + struct.pack("<I", fl)
        blob += data + b"\0" * ((-len(data)) % 32)
    out += b"\0" * (base2 - len(out))
    open(path, "wb").write(bytes(out + blob))
    return path


# --- skupiny: svet (vse krome predmetu) a kazdy predmet zvlast (model, ikona, vytazene textury)
items = sorted(json.load(open("modely/predmety.json")))
files_all = [f for f in os.listdir("modely/predmety") if not f.endswith(".import")]


def owner(f):
    stem = f.rsplit(".", 1)[0]
    best = None
    for i in items:
        if (stem == i or f.startswith(i + "_")) and (best is None or len(i) > len(best)):
            best = i
    return best


groups = {"svet": [f for f in glob.glob("modely/**", recursive=True) if os.path.isfile(f) and not f.startswith("modely/predmety/")
                   and not f.startswith("modely/louka/") and not f.endswith(".import")]}
# offline rozsev louky (TVRZ_ROZSEV=1): vlastni balik, zmena travy nestahuje znovu cely svet
groups["louka"] = sorted(glob.glob("modely/louka/*.bin"))
for i in items:
    groups["p_" + i] = ["modely/predmety/" + f for f in files_all if owner(f) == i]
# hudba (krome hudby menu, ta hraje pred stazenim dat) a ruchy prostredi: velke, meni se zridka
groups["zvuky"] = sorted([f for f in glob.glob("hudba/*.ogg") if not f.endswith("menu.ogg")] + glob.glob("zvuky/prostredi/*.ogg"))
# opravy (--jen): potok prepeceny pro nove koryto (tools/reka_bake.gd)
if JEN and "z_reka" in JEN:
    groups["z_reka"] = sorted(f for f in glob.glob("modely/reka/*") if not f.endswith(".import"))

old = {}
if os.path.exists("data_manifest.json"):
    om = json.load(open("data_manifest.json"))
    old = om.get("packs", {}) if isinstance(om.get("packs"), dict) else {}

def bez_zdroje(name):
    """Soubory oblasti baliku, ktere jsou jen importovane (.import bez zdroje) - kontejner s daty rozbalenymi z baliku
    (tools/stahni_zdroje.sh). Takovy balik nejde znovu sestavit, bere se z minuleho vydani (zmeny -> --jen z_<nazev>)."""
    if name == "svet":
        imp = [f for f in glob.glob("modely/**/*.import", recursive=True) if not f.startswith(("modely/predmety/", "modely/louka/"))]
    elif name.startswith("p_"):
        imp = ["modely/predmety/" + f for f in os.listdir("modely/predmety") if f.endswith(".import") and owner(f[:-7]) == name[2:]]
    else:
        return []
    return [f for f in imp if not os.path.exists(f[:-7])]


for i in items:                       # predmet bez zdroju (jen .import) ma mit skupinu i tak (jinak by balik z manifestu zmizel)
    groups.setdefault("p_" + i, [])

packs = {}
rebuilt = 0
for name, files in groups.items():
    if not name.startswith("z_") and bez_zdroje(name) and name in old:
        packs[name] = old[name]
        if JEN is None:
            print("balik %s: chybi zdroje (%d souboru jen importovanych) - beze zmeny z minuleho vydani" % (name, len(bez_zdroje(name))))
        continue
    if JEN is not None and name not in JEN:
        if name in old:
            packs[name] = old[name]
        continue
    if not files:
        continue
    h = src_hash(files)
    o = old.get(name)
    if o and o.get("src") == h and o.get("size", 0) > 0 and all(os.path.exists("data/" + p["file"]) for p in o["parts"]):
        packs[name] = o
        continue
    if name == "svet":
        cfg = preset_with("modely/predmety/*")
    elif name.startswith("z_"):
        cfg = preset_with(None, [f for f in files if not f.endswith(".json")])
        cfg = cfg.replace('\ninclude_filter=""', '\ninclude_filter="%s/*.json"' % os.path.dirname(files[0]), 1)
    elif name == "louka":
        # .bin nejsou zdroje Godotu: jen pres include_filter, zadne zdroje
        cfg = preset_with(None, [])
        cfg = cfg.replace('\ninclude_filter=""', '\ninclude_filter="modely/louka/*.bin"', 1)
    else:
        cfg = preset_with(None, [f for f in files if f.endswith((".glb", ".png", ".ogg"))])
    pck = open(jen_data(export_pack(name, cfg)) if name.startswith("z_") else export_pack(name, cfg), "rb").read()
    if len(pck) < 1024:
        sys.exit("CHYBA: balik %s je prazdny (plny disk?)" % name)
    md5 = hashlib.md5(pck).hexdigest()
    parts = []
    for k in range(0, len(pck), PART):
        chunk = pck[k:k + PART]
        fn = "%s-%s.pck.%03d" % (name, md5[:10], k // PART)
        open("data/" + fn, "wb").write(chunk)
        parts.append({"file": fn, "size": len(chunk), "md5": hashlib.md5(chunk).hexdigest()})
    packs[name] = {"src": h, "md5": md5, "size": len(pck), "parts": parts}
    rebuilt += 1
    print("balik", name, "%.1f MB" % (len(pck) / 1048576), len(parts), "casti")

# opravne baliky z minula zustavaji, dokud se znovu nesestavi svet (pak je jejich obsah uz v nem)
for name, o in old.items():
    if name.startswith("z_") and name not in packs and old.get("svet") is packs.get("svet"):
        packs[name] = o

# stare soubory dat pryc
keep ={p["file"] for pk in packs.values() for p in pk["parts"]}
os.makedirs("data", exist_ok=True)
for f in glob.glob("data/**", recursive=True):
    if os.path.isfile(f) and os.path.relpath(f, "data") not in keep:
        subprocess.run(["git", "rm", "-q", "--cached", "--ignore-unmatch", f])
        os.remove(f)
for d in glob.glob("data/*/"):
    shutil.rmtree(d, ignore_errors=True)
json.dump({"verze": ver, "packs": packs}, open("data_manifest.json", "w"), indent=1)
total = sum(p["size"] for p in packs.values())
print("data: %d baliku, %.1f MB, znovu sestaveno %d" % (len(packs), total / 1048576, rebuilt))

subprocess.run([GODOT, "--headless", "--path", ".", "--export-release", "Android", "build/OdkazHavrana.apk"], env=env, check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for old_apk in glob.glob("apk/*.apk"):
    subprocess.run(["git", "rm", "-q", "--ignore-unmatch", old_apk])
    if os.path.exists(old_apk):
        os.remove(old_apk)
os.makedirs("apk", exist_ok=True)
shutil.copyfile("build/OdkazHavrana.apk", "apk/OdkazHavrana-%s.apk" % ver)
print("apk %.1f MB" % (os.path.getsize("build/OdkazHavrana.apk") / 1048576))

# druhe APK s vykreslovanim pres Vulkan (Godot Mobile renderer) pro porovnani vykonu na tabletu;
# vlastni nazev balicku, aby slo mit nainstalovane obe verze vedle sebe.
# Jen na vyzadani: v 0.21 na Xiaomi Pad 8 (Godot 4.4.1) pada a v menu kresli pruhy.
if "--vulkan" in sys.argv:
    pg, ep = open("project.godot").read(), open("export_presets.cfg").read()
    try:
        # Vulkan + MSAA 2x od prvniho snimku (Adreno 8xx: bez MSAA vodorovne pruhy, diagnostika 16. 10.)
        open("project.godot", "w").write(pg.replace('renderer/rendering_method.mobile="gl_compatibility"',
                                                    'renderer/rendering_method.mobile="mobile"\nanti_aliasing/quality/msaa_3d=1'))
        sec = ep.index('name="Android Data"')
        open("export_presets.cfg", "w").write(
            ep[:sec].replace('package/unique_name="cz.tvrz.hra"', 'package/unique_name="cz.tvrz.hra.vulkan"')
                    .replace('package/name="Odkaz Havrana"', 'package/name="Havran Vulkan"') + ep[sec:])
        subprocess.run([GODOT, "--headless", "--path", ".", "--export-release", "Android", "build/OdkazHavranaVulkan.apk"], env=env,
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        open("project.godot", "w").write(pg)
        open("export_presets.cfg", "w").write(ep)
    shutil.copyfile("build/OdkazHavranaVulkan.apk", "apk/OdkazHavrana-%s-vulkan.apk" % ver)
    print("apk vulkan %.1f MB" % (os.path.getsize("build/OdkazHavranaVulkan.apk") / 1048576))
