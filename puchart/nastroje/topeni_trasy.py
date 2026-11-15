"""Trasy testu průchodu kolem topení od modeláře (pravidla/svet/topeni.json trasy): pro každou instanci modelu v hra/data/mista_stavby.json
vezme trasu vstupu do domu z hra/data/pruchody_mista.json (dum_<místo>_<model>_<i> / dum_<místo>_<model>) a připojí body
[x, z] v souřadnicích modelu (dveře jizby, kolem pece, ke krbu, kuchyní krčmy do dvora) převedené do světa jako hlavni.gd
(_mista: Basis(UP, yaw), celek + posun_x). Výstup hra/data/pruchody_topeni.json (test_pruchod.gd načte všechny pruchody_*.json).
  python3 nastroje/topeni_trasy.py <K>"""
import sys, os, json, math
K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
T = json.load(open(os.path.join(K, "pravidla/svet/topeni.json")))["trasy"]
S = json.load(open(os.path.join(K, "hra/data/mista_stavby.json")))["stavby"]
PM = json.load(open(os.path.join(K, "hra/data/pruchody_mista.json")))["trasy"]
out = {}
for i, s in enumerate(S):
    m = s.get("model")
    if m not in T: continue
    # trasa vstupu do této instance: dum_<místo>_<model>[_<n>], jejíž poslední bod je nejblíž středu domu (číslo n není index stavby)
    kand = [(math.hypot(v[-1][0] - float(s["x"]), v[-1][1] - float(s["z"])), k) for k, v in PM.items() if k.startswith("dum_%s_%s" % (s["misto"], m))]
    zaklad = PM[min(kand)[1]] if kand and min(kand)[0] < 15.0 else None
    if not zaklad: print("TOPENI_TRASA_CHYBI vstup", s["misto"], m, i); continue
    c, sn = math.cos(float(s["yaw"])), math.sin(float(s["yaw"])); px = float(s.get("posun_x", 0.0))
    body = [list(b) for b in zaklad]
    for q in T[m]:   # [x, z] nebo [x, z, tolerance] (přesný bod – test_pruchod [x, z, y, tolerance])
        x, z = q[0] + px, q[1]
        body.append([round(float(s["x"]) + x * c + z * sn, 2), round(float(s["z"]) - x * sn + z * c, 2), None] + ([q[2]] if len(q) > 2 else []))
    out["topeni_%s_%s_%d" % (s["misto"], m, i)] = body
json.dump({"popis": "trasy průchodu kolem topení (nastroje/topeni_trasy.py z pravidla/svet/topeni.json trasy) – test_pruchod.gd", "trasy": out},
          open(os.path.join(K, "hra/data/pruchody_topeni.json"), "w"), ensure_ascii=False, indent=1)
print("TOPENI_TRASY %d tras → hra/data/pruchody_topeni.json" % len(out))
