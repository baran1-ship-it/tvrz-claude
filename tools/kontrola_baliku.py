"""Je na tabletu vsechno, co hra nacita? (0.99: animace modely/postavy/anim/UAL*.glb nebyly v zadnem baliku - postavy
i telo hrace na tabletu v T-poze, v kontejneru se hybaly, zadny test to nevidel.)
Cesty res://modely/... z kodu (scripts/*.gd: cele literaly a jmena souboru k const DIR) musi byt v nekterem baliku
z data_manifest.json (cesty v hlavicce pck jsou citelne). rc 1 = nevydavat.
  python3 tools/kontrola_baliku.py"""
import json
import mmap
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
cesty = set()
for f in sorted(os.listdir("scripts")):
    if not f.endswith(".gd"):
        continue
    t = open("scripts/" + f, encoding="utf-8").read()
    for m in re.finditer(r'"res://(modely/[^"]+\.(?:glb|gltf|png|json|tscn|tres|bin))"', t):
        cesty.add(m.group(1))
    dm = re.search(r'const DIR\s*:?=\s*"res://(modely/[^"]*/)"', t)
    if dm:
        for m in re.finditer(r'"([A-Za-z0-9_]+\.(?:glb|gltf))"', t):
            cesty.add(dm.group(1) + m.group(1))
cesty = {c for c in cesty if os.path.exists(c)}          # jen soubory, ktere v projektu jsou (zbytek hlida hra)
man = json.load(open("data_manifest.json"))
vpck = set()
rx = re.compile(rb"modely/[A-Za-z0-9_./-]+")
for p in man["packs"].values():
    for part in p["parts"]:
        fp = "data/" + part["file"]
        if not os.path.exists(fp) or os.path.getsize(fp) == 0:
            continue
        with open(fp, "rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for m in rx.finditer(mm):
                vpck.add(m.group(0).decode("ascii", "ignore"))
# APK samo (modely/*.json z presetu)
# importovany zdroj (glb, gltf, png) je v baliku jen s <soubor>.import - samotne jmeno se objevuje i v seznamech UID
# jinych baliku (0.99: UAL1.glb nalezen v 9 balicich, ale nikde jako soubor)
def v_baliku(c):
    return (c + ".import") in vpck if c.endswith((".glb", ".gltf", ".png")) else c in vpck


chybi = sorted(c for c in cesty if not v_baliku(c) and not c.endswith(".json"))
for c in chybi:
    print("BALIK chybi", c)
print("BALIKY: %d cest z kodu, %d chybi" % (len(cesty), len(chybi)))
sys.exit(1 if chybi else 0)
