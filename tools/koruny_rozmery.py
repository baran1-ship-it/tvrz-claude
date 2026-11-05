#!/usr/bin/env python3
"""Rozmery korun stromu z modelu (rozbor travy unshaded 5. 11.) -> pravidla/svet/modely.json trava_unshaded.koruny.

Polomer koruny v masce stanoviste (svet.gd: koule impostoru, nejmene 18 % vysky) je u listnacu 2-3x mensi nez skutecna
koruna (dub_stary 3,4 m proti 11 m) - stin stromu na trave unshaded pak skoro chybel. Tady se meri primo z glb
(min/max akcesoru POSITION; site z Blenderu maji jednotkove transformace): polomer = prumer polovin sirky x a z,
vyska = rozsah y. Druh = jmeno souboru bez _daleko; svet.gd bere nejdelsi shodu zacatku jmena druhu.

python3 tools/koruny_rozmery.py   (zapise do modely.json)
"""
import glob
import json
import os
import re
import struct

STROMY = ("smrk", "briza", "borovice", "dub", "lipa", "olse", "buk", "vrba", "jablon")


def rozmery(f):
    b = open(f, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    g = json.loads(b[20:20 + n])
    mn, mx = [1e9] * 3, [-1e9] * 3
    for m in g["meshes"]:
        for p in m["primitives"]:
            a = g["accessors"][p["attributes"]["POSITION"]]
            mn = [min(x, y) for x, y in zip(mn, a["min"])]
            mx = [max(x, y) for x, y in zip(mx, a["max"])]
    return round(((mx[0] - mn[0]) + (mx[2] - mn[2])) / 4.0, 2), round(mx[1] - mn[1], 2)


def main():
    out = {}
    for f in sorted(glob.glob("modely/rostliny/*.glb")):
        n = os.path.basename(f)[:-4]
        if n.endswith("_daleko") or not n.startswith(STROMY):
            continue
        out[n] = list(rozmery(f))
    p = "pravidla/svet/modely.json"
    s = open(p).read()
    txt = json.dumps(out, ensure_ascii=False)
    s2, k = re.subn(r'("trava_unshaded"\s*:\s*\{.*?"koruny"\s*:\s*)\{[^{}]*\}', lambda m: m.group(1) + txt, s, count=1, flags=re.S)
    if k == 0:
        raise SystemExit("modely.json: trava_unshaded.koruny chybi (zalozit klic rucne)")
    json.loads(s2)
    open(p, "w").write(s2)
    print(txt)


if __name__ == "__main__":
    main()
