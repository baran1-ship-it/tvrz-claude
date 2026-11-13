"""Funkční dveře domů nových míst (pravidla/svet/pohyb_mista.json; Míša 13. 11.: „ves, hospoda, hájovna – funkční dveře“):
z modelu domů Havrana (hra/modely/stavby_h/domy.glb) uzly <Dům>_Dvere_* → hra/data/pohyb_mista.json ve formátu
hra/data/pohyb.json (name, kind, group, cols, open, dur) + glb_zavreno (v modelu zavřené) a use_mistni (místo ovládání
v souřadnicích uzlu dveří). Údaje jsou v souřadnicích modelu, takže platí pro každou instanci domu (dvere.gd: skupina
dveře@instance) a nezávisí na rozmístění (mista_rozmisteni.py).
  python3 nastroje/pohyb_mista.py <koren>"""
import sys, os, json, struct, math
K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
PR = json.load(open(K + "/pravidla/svet/pohyb_mista.json"))
f = open(K + "/hra/modely/stavby_h/domy.glb", "rb").read()
j = json.loads(f[20:20 + struct.unpack("<I", f[12:16])[0]])
N = j["nodes"]; A = j["accessors"]
dily = []
for n in N:
    jm = n.get("name", "")
    if "_Dvere" not in jm or "mesh" not in n: continue
    a = A[j["meshes"][n["mesh"]]["primitives"][0]["attributes"]["POSITION"]]
    lo, hi = a["min"], a["max"]
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]; s = [max(hi[i] - lo[i], PR["tloustka_min_m"]) for i in range(3)]
    tx, _, tz = n.get("translation", [0, 0, 0])
    # směr křídla od pantu (místní xz) a směr ke středu domu kolmo na křídlo
    dx, dz = (c[0], c[2]); L = math.hypot(dx, dz) or 1.0; dx, dz = dx / L, dz / L
    kx, kz = -tx, -tz   # ke středu modelu (počátek domu)
    best = None
    for a_ in (PR["uhel_deg"], -PR["uhel_deg"]):
        r = math.radians(a_); ox, oz = dx * math.cos(r) + dz * math.sin(r), -dx * math.sin(r) + dz * math.cos(r)   # Basis(UP, a) * d
        sc = ox * kx + oz * kz
        if best is None or sc > best[0]: best = (sc, a_)
    dum = jm.split("_Dvere")[0]
    dily.append({"name": jm, "dum": dum, "kind": "dvere", "group": jm, "glb_zavreno": True,
                 "cols": [[round(c[0], 3), round(c[1], 3), round(c[2], 3), round(s[0], 3), round(s[1], 3), round(s[2], 3)]],
                 "use_mistni": [round(c[0], 3), PR["ovladani_y_m"], round(c[2], 3)], "open": best[1], "dur": PR["doba_s"]})
json.dump({"popis": "dveře domů nových míst (nastroje/pohyb_mista.py z pravidla/svet/pohyb_mista.json a domy.glb) – čte dvere.gd pod uzlem Mista; souřadnice uzlu dveří, platí pro každou instanci",
           "dily": dily}, open(K + "/hra/data/pohyb_mista.json", "w"), ensure_ascii=False, indent=1)
print("POHYB_MISTA dveří %d (%s)" % (len(dily), ", ".join(sorted({d["dum"] for d in dily}))))
