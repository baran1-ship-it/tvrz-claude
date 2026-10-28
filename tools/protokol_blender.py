"""Protokol stavby terenu v Blenderu (radce 28. 10. 16:40): fort.land po krocich (teren, vypln, cesty, stavby, dil
mlyna, lom, ves, voda) na mrizce 8 m - co ktery krok zmenil, kde a o kolik. Vystup build/protokol_blender.json ve
formatu svet.gd protokolu (kroky s bunkami 8 m); tools/protokol_mapa.py ho kresli spolu s kroky hry.
  /opt/bl/bin/python tools/protokol_blender.py [--krok 8]"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "blender"))
import fort  # noqa: E402

K = float(sys.argv[sys.argv.index("--krok") + 1]) if "--krok" in sys.argv else 8.0
X0, X1, Z0, Z1 = -240.0, 900.0, -240.0, 1340.0
kroky = {}
poradi = []
z = Z0
while z <= Z1:
    x = X0
    while x <= X1:
        zz = []
        fort.land(x, z, zaznam=zz)
        for (k, y), (_, y0) in zip(zz[1:], zz[:-1]):
            dy = y - y0
            if k not in kroky:
                kroky[k] = {"krok": "blender: " + k, "site": ["fort.land"], "vrcholu": 0, "max_dy": 0.0, "bunky": {}}
                poradi.append(k)
            if abs(dy) > 0.02:
                e = kroky[k]
                e["vrcholu"] += 1
                e["max_dy"] = max(e["max_dy"], abs(dy))
                e["bunky"]["%d,%d" % (int(x // 8), int(z // 8))] = round(abs(dy), 2)
        x += K
    z += K
out = [kroky[k] for k in poradi if kroky[k]["vrcholu"] > 0]
json.dump({"kroky": out}, open(os.path.join(ROOT, "build", "protokol_blender.json"), "w"))
for e in out:
    print("PROTOKOL %-28s %6d bodu, max dy %.2f m" % (e["krok"], e["vrcholu"], e["max_dy"]))


# hlidani kazdeho kroku: mez z pasma.test.meze_kroku, krok bez meze nebo nad mez = rc 9 s nejhorsim mistem
meze = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["test"]["meze_kroku"]
chyby = 0
for e in out:
    m = meze.get(e["krok"])
    if m is None:
        print("MEZ CHYBI %s (max dy %.2f m) - doplnit pasma.test.meze_kroku" % (e["krok"], e["max_dy"]))
        chyby += 1
    elif e["max_dy"] > float(m["max_dy_m"]):
        c, dy = max(e["bunky"].items(), key=lambda kv: kv[1])
        cx, cz = [int(v) * 8 + 4 for v in c.split(",")]
        print("MEZ PREKROCENA %s: %.2f m > %.1f m (%s) nejvic u (%d, %d)" % (e["krok"], e["max_dy"], float(m["max_dy_m"]), m["proc"], cx, cz))
        chyby += 1
print("meze kroku Blenderu: %d chyb" % chyby)
sys.exit(9 if chyby else 0)
