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
# brana (Astra 22:00): balit se smi jen svet z exportu, ktery prosel testem smyslu pred i po (tools/export.sh ->
# build/export_stav.json, md5 svet.json musi sedet); --jen bez zdrojovych dat svet nebali
if JEN is None or "z_svet" in JEN:
    try:
        _st = json.load(open("build/export_stav.json"))
    except (OSError, ValueError):
        sys.exit("CHYBA: build/export_stav.json chybi - svet nebyl exportovan pres tools/export.sh")
    _md5 = hashlib.md5(open("modely/svet.json", "rb").read()).hexdigest()
    if _st.get("stav") != "OK" or _st.get("svet_md5") != _md5:
        sys.exit("CHYBA: export sveta neprosel (%s, rc %s) nebo svet.json je jiny nez z exportu - nevydavat" % (_st.get("stav"), _st.get("rc")))
    # manifest vydani (Astra 08efee6): vsechny vystupy presne z tohoto exportu, vstupy od exportu beze zmeny, potok
    # predpeceny z tohoto exportu - balik je kompatibilni sada s jednim otiskem
    if subprocess.run([sys.executable, "tools/otisk_exportu.py", "over"]).returncode != 0:
        sys.exit("CHYBA: otisk exportu nesedi (tools/otisk_exportu.py over) - nevydavat")
# kazda chyba od cloveka = kontrola v testu (CLAUDE.md, Misa 28. 10. „at nelepime diry“): radek tabulky chyb
# (docs/rozpracovane/*chyby*.md), ktery je opraveny, musi mit vyplneny sloupec kontroly - jinak se nevydava
# matice vztahu (pravidla/svet/vztahy.json): kazda dvojice druhu hlidana testem, povoleni jen ze zaznamu
# radce 18:20: pokryti a uspesnost 100 % z behu testu k otisku tohoto exportu (snimky a vykon okruhu jsou dalsi kroky)
if subprocess.run([sys.executable, "tools/kontrola_vztahu.py", "--vydani"]).returncode != 0:
    sys.exit("CHYBA: matice vztahu - diry, nepokryte nebo neuspesne dvojice k otisku exportu (tools/kontrola_vztahu.py) - nevydavat")
_bez = subprocess.run([sys.executable, "tools/kontrola_tabulek.py"])
if _bez.returncode != 0:
    sys.exit("CHYBA: opravene chyby bez kontroly v testu (tools/kontrola_tabulek.py) - doplnit test, pak vydat")
# rozpocet graficke pameti: limity textur a reimport pred kazdym vydanim
if JEN is None:                 # bez zdrojovych .jpg by albedo_textur prepsal kalibraci a import nema co delat
    subprocess.run([sys.executable, "tools/limity_textur.py"], check=True)
    if len(glob.glob("modely/textury/*_diff.jpg")) > 10:      # bez zdrojovych fotek by prepsal kalibraci (albedo.json)
        subprocess.run([sys.executable, "tools/albedo_textur.py"], check=True)
    # import s kontrolou (Astra 08efee6: check=False bylo totez co || true o patro vys): log, pri chybe konec
    with open("build/beh/vydani_import.log", "w") as _lg:
        _ri = subprocess.run([GODOT, "--headless", "--path", ".", "--import"], stdout=_lg, stderr=subprocess.STDOUT, timeout=3600)
    _imp = open("build/beh/vydani_import.log", errors="replace").read()
    _spatne = [l for l in _imp.splitlines() if any(k in l for k in ("ERR_FILE_CORRUPT", "Error loading image", "Failed loading resource", "No loader found"))]
    if _ri.returncode != 0 or _spatne:
        print("\n".join(_spatne[:20]))
        sys.exit("CHYBA: import Godotu (rc %d, %d chyb nacteni) - log build/beh/vydani_import.log" % (_ri.returncode, len(_spatne)))
# ETC2 bez hornich mip urovni nad limit (tools/textury_tablet.py): kazdy import je vrati v plne velikosti
# (0.98: po havarii disku reimport -> APK 100.6 MB nad limit GitHubu, grafika 1065 MB misto 620 MB)
subprocess.run([sys.executable, "tools/textury_tablet.py"], check=True)
# verze do instalacniho balicku (Android ji ukazuje v hlaseni o padu) i do projektu (hlidac padu)
import re as _re
_ep = open("export_presets.cfg").read()
_sec = _ep.index('name="Android Data"')
_hd = _re.sub(r'version/name="[^"]*"', 'version/name="%s"' % ver, _ep[:_sec])
_hd = _re.sub(r'version/code=\d+', 'version/code=%d' % int(round(float(ver.split("-")[0]) * 100)), _hd)
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
if JEN and "z_textury" in JEN:
    groups["z_textury"] = ["build/z_textury.pck"]          # tools/textury_tablet.py + pck_textury.gd (bez zdroju)
if JEN and "z_postavy" in JEN:
    # lide (scripts/lide.gd): Quaternius postavy a odev (gltf + textury), CC0 - zatim jen opravny balik
    groups["z_postavy"] = sorted(f for f in glob.glob("modely/postavy/*") if f.endswith((".gltf", ".png")))
if JEN and "z_stromy" in JEN:
    # nove stromy z Misova Disku (blender/stromy.py, duby_nove.py): glb + textury, ktere maji zdroj (stare jen .import)
    groups["z_stromy"] = sorted(f for f in glob.glob("modely/rostliny/*")
                                if f.split("/")[-1].startswith(("briza", "dub_stredni", "dub_stary", "ker_husty", "kapradi_les", "kopretiny", "kvety_bile",
                                                                  "smrk", "borovice", "buk_stredni", "lipa_stredni", "lipa_stara",
                                                                  "olse_stredni", "olse_mlada", "byliny", "ker_kulaty"))
                                and "_daleko" not in f and not f.endswith(".import") and os.path.exists(f))
if JEN and "z_katalog" in JEN:
    # katalog predmetu (modely/predmety.json) je v baliku svet, ktery se v kontejneru nepresestavi (bez zdroju) -
    # novy predmet (lom 0.71: stany) by tablet neznal; oprava s prepisem
    groups["z_katalog"] = ["modely/predmety.json"]
if JEN and "z_rostliny" in JEN:
    # rostliny z exportu sveta v kontejneru (0.97: decimace podle tridy, druhy.json) - balik svet se nepresestavi
    groups["z_rostliny"] = sorted(f for f in glob.glob("modely/rostliny/*") if not f.endswith(".import") and os.path.isfile(f))
if JEN and "z_kone" in JEN:
    # kone ve staji tvrze (Misa 28. 10., lokace.json staj_kone; svet.gd _staj_kone)
    groups["z_kone"] = sorted(f for f in glob.glob("modely/kone/*") if not f.endswith(".import"))
if JEN and "z_mlyn" in JEN:
    # vodni mlyn (Misa, Disk Modely/budovy/mlyn-1.zip -> modely/mlyn/mlyn.glb, mlyn_lod1.glb; svet.gd _mlyn_dil)
    groups["z_mlyn"] = sorted(f for f in glob.glob("modely/mlyn/*") if not f.endswith(".import"))
if JEN and "z_rybnik" in JEN:
    # navesni rybnik Lhota (Misa, rybnik_lhota_v3.zip -> modely/rybnik/rybnik.glb bez textur terenu)
    groups["z_rybnik"] = sorted(f for f in glob.glob("modely/rybnik/*") if not f.endswith(".import"))
if JEN and "z_ves" in JEN:
    # nove domy vsi a chyse (blender/ves_domy.py z Misovych zipu, Disk "budovy") - modely/ves/domy.glb
    groups["z_ves"] = sorted(f for f in glob.glob("modely/ves/*") if not f.endswith(".import"))
if JEN and "z_svet" in JEN:
    # krok B 0.97 (cesty po terenu, hostinec u hlavni cesty): novy export sveta z Blenderu v kontejneru bez zdroju
    # baliku svet - jen co export zmenil (geometrie, svet.json, portaly hostince)
    groups["z_svet"] = ["modely/tvrz.glb", "modely/svet.json", "modely/portaly.json"]
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
        jf = [f for f in files if f.endswith(".json")]
        flt = ", ".join(jf) if name == "z_katalog" else "%s/*.json" % os.path.dirname(files[0])
        cfg = cfg.replace('\ninclude_filter=""', '\ninclude_filter="%s"' % flt, 1)
    elif name == "louka":
        # .bin nejsou zdroje Godotu: jen pres include_filter, zadne zdroje
        cfg = preset_with(None, [])
        cfg = cfg.replace('\ninclude_filter=""', '\ninclude_filter="modely/louka/*.bin"', 1)
    else:
        cfg = preset_with(None, [f for f in files if f.endswith((".glb", ".png", ".ogg"))])
    if name == "z_textury":
        pck = open("build/z_textury.pck", "rb").read()
    else:
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
_ot = json.load(open("build/export_otisk.json")) if os.path.exists("build/export_otisk.json") else {}
# pojistka (28. 10.: 0.98 bez --jen vydala stary svet - balik svet se v kontejneru neprestavi, novy export by na tablet
# nedosel): vystupy exportu, ktere nejsou v zadnem prave sestavenem baliku, = chyba se seznamem opravnych baliku
if _ot:
    _vbal = {f for n in packs if packs[n] is not old.get(n) for f in groups.get(n, [])}
    _chybi = sorted(f for f in _ot.get("vystupy", {}) if f.startswith(("modely/svet.json", "modely/tvrz.glb", "modely/rostliny/", "modely/reka/"))
                    and f not in _vbal and _ot["vystupy"][f] != (json.load(open("build/vydany_otisk.json")).get("vystupy", {}).get(f)
                                                                 if os.path.exists("build/vydany_otisk.json") else None))
    if _chybi:
        sys.exit("CHYBA: export zmenil %d souboru, ktere v zadnem prestavenem baliku nejsou (napr. %s) - vydat s --jen "
                 "z_svet,z_rostliny,z_reka,... (docs/predani.md)" % (len(_chybi), ", ".join(_chybi[:4])))
    shutil.copy("build/export_otisk.json", "build/vydany_otisk.json")
json.dump({"verze": ver, "packs": packs, "otisk_exportu": _ot.get("otisk", ""), "otisk_vstupu": _ot.get("otisk_vstupu", "")},
          open("data_manifest.json", "w"), indent=1)
# radce 25. 10. 06:20: co je na tabletu - verze, commit, hash manifestu a prestavene baliky (panel diag, posledni radek)
import subprocess as _sp
_commit = _sp.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
_mh = hashlib.md5(open("data_manifest.json", "rb").read()).hexdigest()[:8]
_prest = sorted(n for n in packs if packs[n] is not old.get(n))
json.dump({"verze": ver, "commit": _commit, "manifest": _mh, "prestavene": ", ".join(_prest) or "zadne"},
          open("sestaveni.json", "w"), ensure_ascii=False)
print("baliky prestavene: %s" % (", ".join(_prest) or "zadne"))
print("baliky beze zmeny: %d" % (len(packs) - len(_prest)))
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
