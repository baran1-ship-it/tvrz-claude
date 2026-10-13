"""Vydani hry: datovy balik (modely, textury) mimo APK, rozdeleny na casti pod GitHub limit, a male APK.
  python3 tools/vydani.py 0.13
Vysledek: data/<id>/data.pck.NNN (do repozitare), data_manifest.json (v APK), apk/OdkazHavrana-<verze>.apk"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys

GODOT = "/opt/godot/Godot_v4.4.1-stable_linux.x86_64"
PART = 90 * 1024 * 1024
ver = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
env = dict(os.environ, GODOT_ANDROID_KEYSTORE_RELEASE_PATH="/root/keys/tvrz_release.keystore",
           GODOT_ANDROID_KEYSTORE_RELEASE_USER="havran", GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD="havran2026")
os.makedirs("build", exist_ok=True)
subprocess.run([GODOT, "--headless", "--path", ".", "--export-pack", "Android Data", "build/data.pck"], env=env, check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
pck = open("build/data.pck", "rb").read()
md5 = hashlib.md5(pck).hexdigest()
did = "%s-%s" % (ver, md5[:8])
for d in glob.glob("data/*"):
    if os.path.basename(d) != did:
        subprocess.run(["git", "rm", "-rq", "--ignore-unmatch", d])
        shutil.rmtree(d, ignore_errors=True)
os.makedirs("data/" + did, exist_ok=True)
parts = []
for i in range(0, len(pck), PART):
    chunk = pck[i:i + PART]
    name = "data.pck.%03d" % (i // PART)
    open("data/%s/%s" % (did, name), "wb").write(chunk)
    parts.append({"name": name, "size": len(chunk), "md5": hashlib.md5(chunk).hexdigest()})
json.dump({"id": did, "size": len(pck), "md5": md5, "parts": parts}, open("data_manifest.json", "w"), indent=1)
print("data", did, "%.1f MB" % (len(pck) / 1048576), len(parts), "casti")
subprocess.run([GODOT, "--headless", "--path", ".", "--export-release", "Android", "build/OdkazHavrana.apk"], env=env, check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for old in glob.glob("apk/*.apk"):
    subprocess.run(["git", "rm", "-q", "--ignore-unmatch", old])
os.makedirs("apk", exist_ok=True)
shutil.copyfile("build/OdkazHavrana.apk", "apk/OdkazHavrana-%s.apk" % ver)
print("apk %.1f MB" % (os.path.getsize("build/OdkazHavrana.apk") / 1048576))

# druhe APK s vykreslovanim pres Vulkan (Godot Mobile renderer) pro porovnani vykonu na tabletu;
# vlastni nazev balicku, aby slo mit nainstalovane obe verze vedle sebe
if "--bez-vulkanu" not in sys.argv:
    pg, ep = open("project.godot").read(), open("export_presets.cfg").read()
    try:
        open("project.godot", "w").write(pg.replace('renderer/rendering_method.mobile="gl_compatibility"',
                                                    'renderer/rendering_method.mobile="mobile"'))
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
