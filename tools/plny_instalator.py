"""Plny instalator (Misa 15. 11., zaloha na Disk jako Puchart; CLAUDE.md oddil „Zaloha hry na Disk“).
APK se VSEMI herni daty uvnitr: baliky z data/ (podle data_manifest.json, spojene casti, overene md5) jdou do
data_vlozena/ a export Android je pribali (include_filter); hra je pri prvnim spusteni zkopiruje do user://data
(scripts/data.gd _z_apk) a stahovani preskoci. Podpis stejnym klicem jako normalni APK (otisk se overi).
Vystup: build/zaloha/OdkazHavrana-<verze>-plny.7z.001, .002 ... (7z bez komprese po 350 MB, overene testzip).
  python3 tools/plny_instalator.py            (spoustet pres tools/beh.sh <jmeno> cmd ..., zabere ~3x velikost dat)
Uklizi prubezne: data_vlozena po exportu, APK po zabaleni."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
GODOT = shutil.which("godot") or "godot"
KEY = "/root/keys/tvrz_release.keystore"
OTISK = "C6:1B:DC:1E:35:2B:3A:DC:58:63:4A:B1:E4:C2:5C:FB:B5:FE:91:B3:BA:3D:C5:AE:18:24:06:13:3B:EC:6C:59"
CAST_MB = 350
VL = "data_vlozena"


def stop(msg):
    print("CHYBA:", msg)
    sys.exit(1)


man = json.load(open("data_manifest.json"))
ver = man["verze"]
data_b = sum(int(p["size"]) for p in man["packs"].values())
volno = shutil.disk_usage(ROOT).free
print("verze %s, data %.0f MB, volno %.0f MB" % (ver, data_b / 1e6, volno / 1e6))
# data_vlozena + APK + casti 7z (APK se maze az po zabaleni) ~ 3x data + rezerva
if volno < 3.2 * data_b:
    stop("malo mista: potreba ~%.0f MB, volno %.0f MB (uklidit nebo nova session)" % (3.2 * data_b / 1e6, volno / 1e6))

# klic: stejny jako normalni APK (jinak nejde nainstalovat pres starou verzi)
heslo = re.search(r'KEYSTORE_RELEASE_PASSWORD="([^"]+)"', open("tools/vydani.py").read()).group(1)
if not os.path.exists(KEY):
    stop("chybi %s - stahnout z Disku (CLAUDE.md, id keystore) a overit sha256sum" % KEY)
kl = subprocess.run(["keytool", "-list", "-v", "-keystore", KEY, "-storepass", heslo], capture_output=True, text=True).stdout
if OTISK not in kl:
    stop("otisk klice nesedi")

# 1) baliky do data_vlozena (jmeno jako v user://data: <balik>-<md5[:10]>.pck)
shutil.rmtree(VL, ignore_errors=True)
os.makedirs(VL)
for name, pk in man["packs"].items():
    dst = "%s/%s-%s.pck" % (VL, name, pk["md5"][:10])
    h = hashlib.md5()
    with open(dst, "wb") as out:
        for p in pk["parts"]:
            with open("data/" + p["file"], "rb") as f:
                while True:
                    b = f.read(8 << 20)
                    if not b:
                        break
                    h.update(b)
                    out.write(b)
    if h.hexdigest() != pk["md5"] or os.path.getsize(dst) != int(pk["size"]):
        stop("balik %s: md5/velikost nesedi" % name)
print("baliky do APK: %d" % len(man["packs"]))

# 2) export s pribalenymi baliky (preset Android + include data_vlozena/*.pck), cfg se vrati
cfg = open("export_presets.cfg").read()
inc = re.search(r'\[preset\.0\][\s\S]*?\ninclude_filter="([^"]*)"', cfg)
cfg2 = cfg[:inc.start(1)] + inc.group(1) + ", %s/*.pck" % VL + cfg[inc.end(1):]
apk = "build/OdkazHavrana-%s-plny.apk" % ver
env = dict(os.environ, GODOT_ANDROID_KEYSTORE_RELEASE_PATH=KEY, GODOT_ANDROID_KEYSTORE_RELEASE_USER="havran",
           GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD=heslo)
try:
    open("export_presets.cfg", "w").write(cfg2)
    subprocess.run([GODOT, "--headless", "--path", ".", "--export-release", "Android", apk], env=env, check=True)
finally:
    open("export_presets.cfg", "w").write(cfg)
shutil.rmtree(VL, ignore_errors=True)

# 3) overeni: podpis, data uvnitr (kazdy balik ve spravne velikosti)
asg = sorted(__import__("glob").glob("/opt/android/build-tools/*/apksigner"))[-1]
pod = subprocess.run([asg, "verify", "--print-certs", apk], capture_output=True, text=True).stdout
if OTISK.replace(":", "").lower() not in pod:
    stop("APK neni podepsane klicem havran")
uvnitr = {}
with zipfile.ZipFile(apk) as z:
    for i in z.infolist():
        if "/%s/" % VL in "/" + i.filename:
            uvnitr[os.path.basename(i.filename)] = i.file_size
chybi = [n for n, pk in man["packs"].items() if uvnitr.get("%s-%s.pck" % (n, pk["md5"][:10])) != int(pk["size"])]
if chybi:
    stop("v APK chybi nebo nesedi baliky: %s" % chybi[:10])
print("APK %s: %.0f MB, podpis OK, baliku uvnitr %d" % (apk, os.path.getsize(apk) / 1e6, len(uvnitr)))

# 4) 7z po 350 MB bez komprese, overit, APK smazat
import multivolumefile  # noqa: E402
import py7zr  # noqa: E402
os.makedirs("build/zaloha", exist_ok=True)
cil = "build/zaloha/OdkazHavrana-%s-plny.7z" % ver
for f in __import__("glob").glob(cil + ".*"):
    os.remove(f)
with multivolumefile.open(cil, mode="wb", volume=CAST_MB * 1024 * 1024) as mv:
    with py7zr.SevenZipFile(mv, "w", filters=[{"id": py7zr.FILTER_COPY}]) as a:
        a.write(apk, os.path.basename(apk))
with multivolumefile.open(cil, mode="rb") as mv:
    with py7zr.SevenZipFile(mv, "r") as a:
        if a.testzip() is not None:
            stop("archiv 7z je poskozeny")
os.remove(apk)
casti = sorted(__import__("glob").glob(cil + ".*"))
print("ZALOHA OK: %d casti po %d MB: %s" % (len(casti), CAST_MB, ", ".join(casti)))
