"""Otisk exportu (Astra 08efee6 bod 7+8, rádce 28. 10. 12:15): hash vsech vystupu exportu, ktere se vydavaji
(svet.json, modely/*.glb a jejich textury, predpeceny potok), i vstupu, ze kterych vznikly (pravidla/svet/*,
pravidla_sveta.json, blender/*.py). tools/export.sh ho po uspesnem exportu ulozi (build/export_otisk.json),
tools/vydani.py pred balenim overi, ze vystupy jsou presne z toho exportu (zadny stary ani rozpracovany kus - jako
stary balik reky) a vstupy se od exportu nezmenily (jinak data neodpovidaji pravidlum - znovu exportovat).
  python3 tools/otisk_exportu.py zapis      po exportu
  python3 tools/otisk_exportu.py over       pred vydanim (rc 1 + vypis rozdilu)"""
import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
VYSTUPY = ["modely/svet.json", "modely/tvrz.glb", "modely/predmety.json", "modely/reka/*", "modely/rostliny/*",
           "modely/ves/*", "modely/textury/*"]
VSTUPY = ["pravidla/svet/*.json", "pravidla/pravidla_sveta.json", "blender/*.py"]


def otisk(vzory):
    out = {}
    for v in vzory:
        for f in sorted(glob.glob(v)):
            if os.path.isfile(f) and not f.endswith(".import"):
                out[f] = hashlib.md5(open(f, "rb").read()).hexdigest()
    return out


def soucet(d):
    return hashlib.md5(json.dumps(d, sort_keys=True).encode()).hexdigest()


if sys.argv[1:2] == ["zapis"]:
    vy, vs = otisk(VYSTUPY), otisk(VSTUPY)
    json.dump({"vystupy": vy, "vstupy": vs, "otisk": soucet(vy), "otisk_vstupu": soucet(vs)},
              open("build/export_otisk.json", "w"), indent=0)
    print("otisk exportu %s (%d vystupu), vstupu %s (%d)" % (soucet(vy)[:10], len(vy), soucet(vs)[:10], len(vs)))
    sys.exit(0)
try:
    st = json.load(open("build/export_otisk.json"))
except (OSError, ValueError):
    sys.exit("OTISK: build/export_otisk.json chybi - export nebyl pres tools/export.sh")
chyby = []
for nm, ted, puv in (("vystup", otisk(VYSTUPY), st["vystupy"]), ("vstup", otisk(VSTUPY), st["vstupy"])):
    for f in sorted(set(ted) | set(puv)):
        if ted.get(f) != puv.get(f):
            chyby.append("%s %s: %s" % (nm, f, "novy" if f not in puv else ("chybi" if f not in ted else "zmenen od exportu")))
# predpeceny potok musi byt z tohoto exportu (reka_otisk)
sj = json.load(open("modely/svet.json"))
rj = json.load(open("modely/reka/reka.json")) if os.path.exists("modely/reka/reka.json") else {}
if rj.get("reka_otisk") != sj.get("reka_otisk"):
    chyby.append("vystup modely/reka: predpeceny potok neni z tohoto exportu (tools/reka_bake.gd)")
for c in chyby[:40]:
    print("OTISK", c)
print("OTISK souhrn %s" % ("OK " + st["otisk"][:10] if not chyby else "%d rozdilu - nevydavat, znovu exportovat" % len(chyby)))
sys.exit(1 if chyby else 0)
