"""Citlive site bez automatickych LOD importu Godotu (plan 18. 11. C14, pravidla/lod_import.json).
Automaticke LOD (generate_lods) uz 3x rozbilo data (dum vsi, hladina rybnika, teren pod kolizi). Pravidlo rika, ktere
soubory / site LOD z importu nedostanou; jejich LOD je jen vlastni (stupne z Blenderu, dlazdice terenu).
  python3 tools/lod_import.py zapis      zapise nastaveni do .import (cely soubor nebo _subresources site) a smaze .md5
                                          importu zmenenych souboru (dalsi godot --import je importuje znovu; docs/predani.md
                                          13. 11.: Godot u scen jinak zmenu nepozna)
  python3 tools/lod_import.py kontrola   rc 1 = nektery .import pravidlu neodpovida (krok exportu chybi / novy soubor)
Jmeno site v importu = <jmeno souboru bez pripony>_<jmeno site glTF> (Godot 4.4 gltf_document.cpp _parse_meshes,
naming_version 0, jedinecna jmena jako _gen_unique_name). Overeni ve hre: tools/lod_import_over.gd."""
import fnmatch
import glob
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
P = json.load(open("pravidla/lod_import.json", encoding="utf-8"))
VYP = int(P["godot_vypnuto"])
NEPLATNE = '.:@/"%'


def nacti_gltf(p):
    if p.endswith(".gltf"):
        return json.load(open(p, encoding="utf-8"))
    with open(p, "rb") as f:
        f.read(12)
        ln, _ = struct.unpack("<II", f.read(8))
        return json.loads(f.read(ln))


def _platne(s):
    return "".join(c for c in s if c not in NEPLATNE)


def jmena_siti(p, g):
    """index site glTF -> jmeno ImporterMesh v Godotu"""
    base = os.path.splitext(os.path.basename(p))[0]
    sc = (g.get("scenes") or [{}])[g.get("scene", 0)] if g.get("scenes") else {}
    scena = sc.get("name", "")
    if not scena or scena.startswith("Scene"):
        scena = base
    uz = set()

    def uniq(n):
        n = _platne(n)
        u, i = n, 1
        while u in uz:
            i += 1
            u = n + str(i)
        uz.add(u)
        return u
    scena = uniq(scena)
    for nd in g.get("nodes", []):           # _assign_node_names pred _parse_meshes (pribliz.: jen jmena uzlu)
        if nd.get("name"):
            uniq(nd["name"])
    return [uniq("%s_%s" % (scena, m.get("name") or "mesh")) for m in g.get("meshes", [])]


def vybrane_site(p, sk):
    """None = cely soubor, jinak mnozina jmen siti v importu"""
    if "materialy" not in sk and "site" not in sk:
        return None
    g = nacti_gltf(p)
    mats = [m.get("name", "") for m in g.get("materials", [])]
    uzly = {}
    for nd in g.get("nodes", []):
        if "mesh" in nd:
            uzly.setdefault(nd["mesh"], []).append(nd.get("name", ""))
    jm = jmena_siti(p, g)
    out = set()
    for i, m in enumerate(g.get("meshes", [])):
        if "materialy" in sk:
            ms = [mats[q["material"]] for q in m.get("primitives", []) if "material" in q]
            if not any(fnmatch.fnmatch(x, v) for x in ms for v in sk["materialy"]):
                continue
        if "site" in sk:
            nazvy = [m.get("name", "")] + uzly.get(i, [])
            if not any(fnmatch.fnmatch(x, v) for x in nazvy for v in sk["site"]):
                continue
        out.add(jm[i])
    return out


def plan():
    """soubor -> None (cely) | set jmen siti; jen soubory se zdrojem (bez zdroje nelze jmena ani import)"""
    out = {}
    for sk in P["skupiny"]:
        for vz in sk["soubory"]:
            for p in sorted(glob.glob(vz)):
                if not os.path.isfile(p + ".import"):
                    continue
                s = vybrane_site(p, sk)
                if s is None or out.get(p, set()) is None:
                    out[p] = None
                else:
                    out[p] = out.get(p, set()) | s
    return out


def cti_import(p):
    return open(p + ".import", encoding="utf-8").read()


def subresources(t):
    i = t.find("\n_subresources=")
    if i < 0:
        return None, None
    j = i + len("\n_subresources=")
    hl, k = 0, j
    while k < len(t):
        if t[k] == "{":
            hl += 1
        elif t[k] == "}":
            hl -= 1
            if hl == 0:
                break
        k += 1
    return json.loads(t[j:k + 1]), (j, k + 1)


def stav(p, cil):
    """seznam rozdilu .import proti pravidlu"""
    t = cti_import(p)
    ch = []
    if cil is None:
        if "\nmeshes/generate_lods=false" not in t:
            ch.append("meshes/generate_lods neni false")
        return ch
    sub, _ = subresources(t)
    sm = (sub or {}).get("meshes", {})
    for n in sorted(cil):
        if int(sm.get(n, {}).get("generate/lods", 0)) != VYP:
            ch.append("sit %s ma LOD z importu" % n)
    return ch


def zapis(p, cil):
    t = cti_import(p)
    if cil is None:
        t2 = re.sub(r"\nmeshes/generate_lods=\w+", "\nmeshes/generate_lods=false", t)
        if "\nmeshes/generate_lods=" not in t2:
            # .import bez [params] (novy soubor po prestavbe, predani 28. 11.): Godot doplni vychozi = LOD zapnute
            t2 = t2.rstrip("\n") + ("\n" if "\n[params]" in t2 else "\n\n[params]\n") + "\nmeshes/generate_lods=false\n"
    else:
        if subresources(t)[0] is None:
            # .import bez _subresources (novy soubor, jen [remap]/[deps] - predani 28. 11.): doplnit prazdne na konec [params]
            t = t.rstrip("\n") + ("\n" if "\n[params]" in t else "\n\n[params]\n") + "\n_subresources={}\n"
        sub, (a, b) = subresources(t)
        sub = sub or {}
        sm = sub.setdefault("meshes", {})
        for n in sorted(cil):
            sm.setdefault(n, {})["generate/lods"] = VYP
        t2 = t[:a] + json.dumps(sub, indent=0, ensure_ascii=False).replace("\n\n", "\n") + t[b:]
    if t2 == t:
        return False
    open(p + ".import", "w", encoding="utf-8").write(t2)
    for f in glob.glob(".godot/imported/%s-*.md5" % os.path.basename(p)):
        os.remove(f)
    os.utime(p, None)                         # Godot soubor znovu kontroluje jen pri zmene casu (predani 13. 11.)
    return True


if __name__ == "__main__":
    pl = plan()
    os.makedirs("build", exist_ok=True)        # pro tools/lod_import_over.gd (overeni importu ve hre)
    json.dump({p: (None if c is None else sorted(c)) for p, c in pl.items()}, open("build/lod_import_plan.json", "w"), indent=0)
    if "zapis" in sys.argv:
        zm = [p for p, c in pl.items() if zapis(p, c)]
        print("LOD_IMPORT zapsano %d souboru z %d (%s)" % (len(zm), len(pl), ", ".join(zm[:12])))
        sys.exit(0)
    chyby = []
    for p, c in pl.items():
        chyby += ["%s: %s" % (p, x) for x in stav(p, c)]
    n_sit = sum(len(c) for c in pl.values() if c is not None)
    print("LOD_IMPORT %s souboru %d (cele %d, site %d) %s" % ("OK" if not chyby else "CHYBA", len(pl),
          sum(1 for c in pl.values() if c is None), n_sit, chyby[:10]))
    sys.exit(1 if chyby else 0)
