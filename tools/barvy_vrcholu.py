"""Barvy vrcholu modelu od modelare linearni -> sRGB pro Compatibility (pravidla/svet/barvy_vrcholu.json; Puchart
nastroje/barvy_vrcholu.py glb_sada). COLOR_0 v GLB katalogu (float / normalizovane uint16 / uint8) se prevede jednou,
znacka v asset.extras; materialy podle albedo_modulace dostanou baseColorFactor. Po prevodu godot --import (beh.sh cmd).
  python3 tools/barvy_vrcholu.py            prevod (idempotentni)
  python3 tools/barvy_vrcholu.py kontrola   rc 1 = GLB v modely/ s COLOR_0 u materialu bez znacky (mimo vyjimky),
                                            stredni stupen jen z importu mimo hra_linearni_stredni, dvoji prevod"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from textury_predmetu import nacti, zapis  # noqa: E402

C = json.load(open("pravidla/svet/barvy_vrcholu.json", encoding="utf-8"))
DT = {5126: (np.float32, 1.0), 5123: (np.uint16, 65535.0), 5121: (np.uint8, 255.0)}
NC = {"VEC3": 3, "VEC4": 4}


def srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def preved(cesta, modulace):
    j, b = nacti(cesta)
    b = bytearray(b)
    ex = j.setdefault("asset", {}).setdefault("extras", {})
    hot = bool(ex.get(C["znacka"], False))
    acc = sorted({p["attributes"]["COLOR_0"] for m in j.get("meshes", []) for p in m["primitives"] if "COLOR_0" in p["attributes"]})
    zmena = False
    if acc and not hot:
        for i in acc:
            a = j["accessors"][i]
            dt, mx = DT[a["componentType"]]
            n = NC[a["type"]]
            bv = j["bufferViews"][a["bufferView"]]
            if bv.get("byteStride", 0) not in (0, np.dtype(dt).itemsize * n):
                sys.exit("BARVY_VRCHOLU_CHYBA %s: prokladany COLOR_0" % cesta)
            off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
            cnt = a["count"] * n
            d = np.frombuffer(bytes(b[off:off + cnt * np.dtype(dt).itemsize]), dtype=dt).reshape(-1, n).astype(np.float64) / mx
            d[:, :3] = srgb(d[:, :3])
            raw = (d.astype(np.float32) if dt == np.float32 else np.round(d * mx).astype(dt)).tobytes()
            b[off:off + len(raw)] = raw
        ex[C["znacka"]] = True
        zmena = True
    for m in j.get("materials", []):
        for pre, f in modulace.items():
            if m.get("name", "").startswith(pre):
                pbr = m.setdefault("pbrMetallicRoughness", {})
                cil = [float(f[0]), float(f[1]), float(f[2]), 1.0]
                if pbr.get("baseColorFactor") != cil:
                    pbr["baseColorFactor"] = cil
                    zmena = True
    if zmena:
        zapis(cesta, j, bytes(b))
    return len(acc), zmena


def soubory():
    for f in C.get("soubory", []):                # dalsi GLB s barvou vrcholu (stredni stupen domu vsi, Misa 17. 11. r. 5)
        if os.path.exists(f):
            yield "soubory", {}, f
    for s, sd in C["sady"].items():
        for i in sd["ids"]:
            for suf in ("", "_lod1"):
                f = "modely/predmety/%s%s.glb" % (i, suf)
                if os.path.exists(f):
                    yield s, sd, f


def kontrola():
    """Kazdy GLB v modely/ s COLOR_0 u materialu (import Godotu zapne Vertex Color -> albedo, sonda build/beh/vcf.log)
    nese znacku, nebo je ve vyjimky (barva = data / import bez barvy); stredni stupen predmetu jen z importu (bez GLB)
    musi byt v hra_linearni_stredni; id v hra_linearni_stredni s GLB se znackou = dvoji prevod."""
    import glob
    ch = []
    vyj = C.get("vyjimky", {})
    for f in sorted(glob.glob("modely/**/*.glb", recursive=True)):
        if f in vyj:
            continue
        j, _ = nacti(f)
        ma = any("COLOR_0" in p["attributes"] and "material" in p for m in j.get("meshes", []) for p in m["primitives"])
        if ma and not j.get("asset", {}).get("extras", {}).get(C["znacka"]):
            ch.append("bez znacky " + f)
    hl = C.get("hra_linearni_stredni", [])
    for imp in sorted(glob.glob("modely/predmety/*_stredni.glb.import")):
        f = imp[:-len(".import")]
        pid = os.path.basename(f)[:-len("_stredni.glb")]
        if not os.path.exists(f) and pid not in hl:
            ch.append("stredni jen z importu, stav barvy neznamy (hra_linearni_stredni?) " + f)
    for pid in hl:
        f = "modely/predmety/%s_stredni.glb" % pid
        if os.path.exists(f) and nacti(f)[0].get("asset", {}).get("extras", {}).get(C["znacka"]):
            ch.append("dvoji prevod (znacka v GLB i hra_linearni_stredni) " + f)
    for f in vyj:
        if not os.path.exists(f):
            ch.append("vyjimka bez souboru " + f)
    print("BARVY_VRCHOLU %s %d %s" % ("OK" if not ch else "CHYBA", len(ch), ch[:12]))
    return 1 if ch else 0


if __name__ == "__main__":
    if "kontrola" in sys.argv:
        sys.exit(kontrola())
    n = 0
    for s, sd, f in soubory():
        k, z = preved(f, sd.get("albedo_modulace", {}))
        n += z
        print("BARVY_VRCHOLU %s %s: %d proudu COLOR_0%s" % (s, os.path.basename(f), k, " -> zmeneno" if z else ""))
    print("BARVY_VRCHOLU zmeneno %d souboru" % n)
