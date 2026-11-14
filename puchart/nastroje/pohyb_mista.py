"""Funkční dveře domů nových míst a vrata stodol (pravidla/svet/pohyb_mista.json; Míša 13. 11.: „ves, hospoda, hájovna –
funkční dveře“; 14. 11.: „chci v nich [kůlnách a stodolách] mít funkční vrata“):
- z modelu domů Havrana (hra/modely/stavby_h/domy.glb) uzly <Dům>_Dvere_* – dveře dovnitř, každé křídlo vlastní skupina,
  instance pod uzlem Mista (hlavni.gd _mista)
- z modelů stodol (hra/modely/predmety_h/stodola*.glb, blender/stodoly.py) uzly <Uzel>_Dvere_L/P – vrata ven, obě křídla
  jedna skupina <Uzel>_Dvere, instance pod uzlem Ves (ves.gd _hospodarske)
→ hra/data/pohyb_mista.json ve formátu hra/data/pohyb.json (name, kind, group, cols, open, dur) + glb_zavreno (v modelu
zavřené), use_mistni (místo ovládání v souřadnicích uzlu křídla) a koren (uzel hry, pod kterým dvere.gd instance hledá).
Údaje jsou v souřadnicích modelu, takže platí pro každou instanci (dvere.gd: skupina dveře@instance) a nezávisí na
rozmístění (mista_rozmisteni.py).
  python3 nastroje/pohyb_mista.py <koren>"""
import sys, os, json, struct, math
K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
PR = json.load(open(K + "/pravidla/svet/pohyb_mista.json"))


def uzly_dveri(cesta):
    """(jméno, translation, min, max obalu sítě – první primitivum) uzlů *_Dvere* se sítí v glb."""
    if not os.path.exists(cesta):
        print("POHYB_MISTA chybí %s" % cesta)
        return []
    f = open(cesta, "rb").read()
    j = json.loads(f[20:20 + struct.unpack("<I", f[12:16])[0]])
    A = j["accessors"]; out = []
    for n in j["nodes"]:
        jm = n.get("name", "")
        if "_Dvere" not in jm or "mesh" not in n: continue
        a = A[j["meshes"][n["mesh"]]["primitives"][0]["attributes"]["POSITION"]]   # první materiál = prkna křídla (bez kování)
        out.append((jm, n.get("translation", [0, 0, 0]), a["min"], a["max"]))
    return out


def zaznam(jm, tr, lo, hi, uhel, ven, kind, group, dur, koren, use_zamek=False):
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]; s = [max(hi[i] - lo[i], PR["tloustka_min_m"]) for i in range(3)]
    tx, _, tz = tr
    # směr křídla od pantu (místní xz) a směr ke středu modelu kolmo na křídlo
    dx, dz = (c[0], c[2]); L = math.hypot(dx, dz) or 1.0; dx, dz = dx / L, dz / L
    kx, kz = -tx, -tz   # ke středu modelu (počátek domu / stodoly)
    best = None
    for a_ in (uhel, -uhel):
        r = math.radians(a_); ox, oz = dx * math.cos(r) + dz * math.sin(r), -dx * math.sin(r) + dz * math.cos(r)   # Basis(UP, a) * d
        sc = (ox * kx + oz * kz) * (-1.0 if ven else 1.0)   # dovnitř: ke středu, ven: od středu
        if best is None or sc > best[0]: best = (sc, a_)
    # místo ovládání: střed křídla (dveře domu), u vrat stodoly zámková hrana = střed průjezdu (jedno místo pro obě křídla)
    ux, uz = (2 * c[0], 2 * c[2]) if use_zamek else (c[0], c[2])
    return {"name": jm, "dum": jm.split("_Dvere")[0], "kind": kind, "group": group, "glb_zavreno": True, "koren": koren,
            "cols": [[round(c[0], 3), round(c[1], 3), round(c[2], 3), round(s[0], 3), round(s[1], 3), round(s[2], 3)]],
            "use_mistni": [round(ux, 3), PR["ovladani_y_m"], round(uz, 3)], "open": best[1], "dur": dur}


dily = []
for jm, tr, lo, hi in uzly_dveri(K + "/hra/modely/stavby_h/domy.glb"):   # dveře domů: dovnitř (smer)
    dily.append(zaznam(jm, tr, lo, hi, PR["uhel_deg"], PR["smer"] == "ven", "dvere", jm, PR["doba_s"], PR.get("koren", "Mista")))
ST = PR["stodoly"]
for soubor in ST["soubory"]:   # vrata stodol: ven, obě křídla jedna skupina
    for jm, tr, lo, hi in uzly_dveri(os.path.join(K, soubor)):
        dily.append(zaznam(jm, tr, lo, hi, ST["uhel_deg"], ST["smer"] == "ven", ST["kind"], jm.split("_Dvere")[0] + "_Dvere",
                           ST["doba_s"], ST["koren"], use_zamek=True))
json.dump({"popis": "dveře domů a vrata stodol nových míst (nastroje/pohyb_mista.py z pravidla/svet/pohyb_mista.json, domy.glb a predmety_h/stodola*.glb) – čte dvere.gd pod uzlem koren (Mista / Ves); souřadnice uzlu křídla, platí pro každou instanci",
           "dily": dily}, open(K + "/hra/data/pohyb_mista.json", "w"), ensure_ascii=False, indent=1)
print("POHYB_MISTA dveří %d (%s)" % (len(dily), ", ".join(sorted({d["dum"] for d in dily}))))
