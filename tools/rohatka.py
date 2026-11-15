"""Rohatka schvalenych nalezu (Puchart, docs/rozpracovane/hlidaci_z_pucharta.md #2): prisny hlidac se zavede bez zablokovani
vydani a bez vyjimek v kodu - dnesni nalezy schvali Misa (zaznam v pravidla/svet/kontroly.json schvalene.<kontrola>
ve formatu vztahy.json povoleni: id, misto [x, y, z], druh, duvod, schvalil, plati_do = verze), kazdy NOVY nalez je chyba.
Shoda nalezu se schvalenym: stejny druh a misto do rohatka.shoda_m. Schvaleny, ktery uz neni, se vypise k odebrani
(rohatka jen utahuje). Proslé schválení (plati_do < verze v project.godot) = chyba.

  python3 tools/rohatka.py <kontrola> <nalezy.json>      rc 1 = novy nalez nebo vadne schvaleni
  python3 tools/rohatka.py <kontrola> <nalezy.json> --navrh   vypise zaznamy k schvaleni (nezapisuje - schvaluje Misa)

nalezy.json: seznam {misto|p|stred: [x, y, z], druh|chyba: ...} nebo objekt s klicem "nalezy" (build/povrch.json) nebo
build/kontrola_geometrie.json (soubory -> visi / pod_terenem). Knihovna: from rohatka import porovnej."""
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KONTROLY = os.path.join(ROOT, "pravidla", "svet", "kontroly.json")


def _verze():
    m = re.search(r'config/version="([0-9.]+)', open(os.path.join(ROOT, "project.godot"), encoding="utf-8").read())
    return tuple(map(int, m.group(1).split("."))) if m else None


def misto(n):
    for k in ("misto", "p", "stred"):
        if k in n:
            v = [float(c) for c in n[k]]
            return v + [0.0] * (3 - len(v))
    return None


def druh(n):
    return str(n.get("chyba", n.get("druh", "")))


def nalezy_ze_souboru(cesta):
    d = json.load(open(cesta, encoding="utf-8"))
    if isinstance(d, list):
        return d
    if "nalezy" in d:
        return d["nalezy"]
    if "soubory" in d:                     # build/kontrola_geometrie.json
        out = []
        for sb, v in d["soubory"].items():
            for n in v.get("visi", []):
                out.append(dict(n, druh="visi", soubor=sb))
            for n in v.get("pod_terenem", []):
                out.append(dict(n, druh="pod_terenem", soubor=sb))
        return out
    return []


def porovnej(kontrola, nalezy, kontroly=None):
    """-> (nove, pouzite schvalene, zmizele schvalene, chyby schvaleni)"""
    K = kontroly or json.load(open(KONTROLY, encoding="utf-8"))
    shoda = float(K["rohatka"]["shoda_m"])
    schv = K.get("schvalene", {}).get(kontrola, [])
    ver = _verze()
    chyby = []
    for s in schv:
        co = "schvaleni %s/%s" % (kontrola, s.get("id"))
        for pole in ("id", "misto", "druh", "duvod", "schvalil", "plati_do"):
            if not s.get(pole):
                chyby.append("%s: chybi %s" % (co, pole))
        if ver and s.get("plati_do") and ver > tuple(map(int, str(s["plati_do"]).split("."))):
            chyby.append("%s: proslo (plati do %s)" % (co, s["plati_do"]))
    nove, pouzite = [], set()
    for n in nalezy:
        p = misto(n)
        hit = None
        for i, s in enumerate(schv):
            if p is not None and s.get("misto") and str(s.get("druh")) == druh(n) and \
                    math.dist(p, [float(c) for c in s["misto"]] + [0.0] * (3 - len(s["misto"]))) <= shoda:
                hit = i
                break
        if hit is None:
            nove.append(n)
        else:
            pouzite.add(hit)
    zmizele = [s for i, s in enumerate(schv) if i not in pouzite]
    return nove, [schv[i] for i in sorted(pouzite)], zmizele, chyby


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    kontrola, cesta = sys.argv[1], sys.argv[2]
    nalezy = nalezy_ze_souboru(cesta)
    nove, pouz, zmiz, chyby = porovnej(kontrola, nalezy)
    for c in chyby:
        print("ROHATKA " + c)
    for s in zmiz:
        print("ROHATKA %s: schvaleny nalez %s uz neni - odebrat ze schvalene (rohatka utahuje)" % (kontrola, s.get("id")))
    for n in nove[:40]:
        print("ROHATKA %s NOVY %s %s" % (kontrola, druh(n), json.dumps(n, ensure_ascii=False)[:300]))
    if "--navrh" in sys.argv:
        navrh = [{"id": "%s_%d" % (kontrola, i + 1), "misto": misto(n), "druh": druh(n), "duvod": "(doplnit - proc to neni chyba)",
                  "schvalil": "(Misa)", "plati_do": "(verze)"} for i, n in enumerate(nove)]
        print(json.dumps(navrh, ensure_ascii=False, indent=1))
    print("rohatka %s: nalezu %d, schvalenych %d, novych %d, zmizelych schvalenych %d, vadnych schvaleni %d"
          % (kontrola, len(nalezy), len(pouz), len(nove), len(zmiz), len(chyby)))
    sys.exit(1 if nove or chyby else 0)


if __name__ == "__main__":
    main()
