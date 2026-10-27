"""Navrh kompozice z mapy dohledu (krok C bod 7): kde je z cesty nebo louky dohled > max (build/vyhledy.json z
tools/mapa_vyhledu.py) a misto neni zamerny vyhled, navrhne zaver - remizek (skupina stromu a keru na mezi / okraji
louky) ve smeru otevreneho pohledu: z cesty 60-120 m po smeru a 8-15 m stranou od osy (mimo pasmo cesty), z louky
na 150-200 m (louka ma okraj do 150-200 m, Misa 19:28). Misto musi byt na stanovisti remizku (louka/okraj/mez,
ne pole, voda, cesta, stavba - kraj.stanoviste a kraj.druh_smi). Blizke navrhy se slouci (60 m).
Zapis do pravidla/svet/lokace.json kompozice.remizky az s --zapis (kazdy zaznam ma duvod).

  /opt/bl/bin/python tools/kompozice_navrh.py [--zapis]"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "blender"))
import bpy  # noqa: E402,F401
import kraj  # noqa: E402

MAXD = 300.0
vy = json.load(open(os.path.join(ROOT, "build", "vyhledy.json")))
navrhy = []


_LOK = json.load(open(os.path.join(ROOT, "pravidla", "svet", "lokace.json")))
_VODA = json.load(open(os.path.join(ROOT, "pravidla", "svet", "voda.json")))
_STAVBY = [u["novy_stred"] for u in _LOK["ves"]["usedlosti"]] + [s["stred"] for s in _LOK["stavby"]] + [_VODA["mlyn"]["stred"]]


def vhodne(x, z):
    if any(math.hypot(x - c[0], z - c[1]) < 28.0 for c in _STAVBY):
        return False                                      # usedlost (dvur, sad) i stavby
    if kraj.ves_r(x, z) < kraj.VES_R:
        return False
    st = kraj.stanoviste(x, z, kraj.F_land(x, z) if hasattr(kraj, "F_land") else 0.0)
    if st & {"pole", "voda", "cesta", "tvrz"}:
        return False
    if kraj.v_pudorysu(x, z, 6.0) or kraj.ve_vode(x, z, 1e9) < 6.0:
        return False
    rn = kraj.road_near(x, z)
    if rn and rn[0] - rn[3] < 6.0:
        return False
    return bool(st & {"louka", "okraj", "mez", "les"})


for o in vy:
    if not o["chyba"]:
        continue
    x0, z0 = o["x"], o["z"]
    cesta = o["typ"].startswith("cesta:")
    for k, d in enumerate(o["dohled"]):
        if d <= MAXD:
            continue
        a = k * math.pi / 8
        dx, dz = math.sin(a), math.cos(a)
        best = None
        for dist in ((60, 80, 100, 120) if cesta else (150, 170, 190, 200)):
            for bok in ((8, -8, 12, -12, 15, -15) if cesta else (0, 10, -10)):
                x = x0 + dx * dist - dz * bok
                z = z0 + dz * dist + dx * bok
                if vhodne(x, z):
                    best = (x, z, dist)
                    break
            if best:
                break
        if best:
            navrhy.append({"stred": [round(best[0], 1), round(best[1], 1)], "polomer_m": 9.0 if cesta else 14.0,
                           "duvod": "zaviera dohled %d m %s z %s (%.0f, %.0f), oci %.1f m" % (d, ["S", "SSV", "SV", "VSV", "V", "VJV", "JV", "JJV", "J", "JJZ", "JZ", "ZJZ", "Z", "ZSZ", "SZ", "SSZ"][k], o["typ"], x0, z0, o["oko"])})
# slouceni blizkych
slouc = []
for n in navrhy:
    for m in slouc:
        if math.hypot(n["stred"][0] - m["stred"][0], n["stred"][1] - m["stred"][1]) < 60.0:
            break
    else:
        slouc.append(n)
print("KOMPOZICE navrhu %d -> po slouceni %d remizku" % (len(navrhy), len(slouc)))
for n in slouc[:60]:
    print("KOMPOZICE remizek (%.0f, %.0f) r %.0f m: %s" % (n["stred"][0], n["stred"][1], n["polomer_m"], n["duvod"]))
if "--zapis" in sys.argv:
    p = os.path.join(ROOT, "pravidla", "svet", "lokace.json")
    L = json.load(open(p))
    kp = L.setdefault("kompozice", {"popis": "Kompozice z pohledu hrace (krok C bod 7, radce 19:35): remizky zaviraji dohled > 300 m z cest a luk (tools/kompozice_navrh.py z tools/mapa_vyhledu.py), vyhledy = zamerne otevrena mista (test je nepocita). Stavi blender/kraj.py (remizky: stromy a kere podle stanovist).", "vyhledy": []})
    kp["remizky"] = slouc
    jb = L.setdefault("jen_blender", [])
    for k in ("kompozice",):
        if k not in jb:
            jb.append(k)
    json.dump(L, open(p, "w"), ensure_ascii=False, indent=1)
    print("KOMPOZICE zapsano %d remizku do lokace.json" % len(slouc))
