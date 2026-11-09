"""Odtok rybniku zacina za vzdusnou patou hraze (Misa 9. 11. r. 61/79: „bila hladina nad terenem, hlineny sraz kolem“).

Planovac toku (voda_sit / odtok_mimo_ves) planoval odtoky po terenu bez rybniku: lhota_odtok zacinal uprostred hraze
(515, 870) 1,56 m pod hladinou rybnika a 16 m vedl podel hraze, tvrz_odtok zacinal 0,3 m od osy hraze 1,34 m pod
hladinou. Koryto a dolina odtoku pak hraz rozkopaly (kraj.voda_tvar, svet._ryb_hraz_toky: vypust) - rybnik mel diru
sirokou jako dolina a hladina visela 1-2 m nad terenem. U skutecneho rybnika voda odtece vypusti (pozerak, trubka) pod
hrazi a otevrene koryto zacina za vzdusnou patou hraze.

Pravidlo: bod osy odtoku, kde je hraz (vzorec kraj._hraz z voda.json hraz) vys nez dno toku (hladina - hloubka), lezi
v telese hraze -> z osy pryc (od zacatku toku, dokud tak je). Zbytek osy beze zmeny (hladina, meandry, mlyn).
  python3 tools/krok_b/odtok_za_hrazi.py           vypis
  python3 tools/krok_b/odtok_za_hrazi.py --zapis   zapise voda.json (pak export: koryta, hraz)"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, "pravidla", "svet", "voda.json")


def hraz_y(x, z, ryb):
    """Vyska koruny a svahu hraze v bode (-inf mimo) - stejne jako blender/kraj.py _hraz."""
    hz = ryb.get("hraz")
    if not hz:
        return -1e9
    cx, cz = hz["stred"]
    ux, uz = hz["smer_osy"]
    dx, dz = x - cx, z - cz
    a = max(0.0, abs(dx * ux + dz * uz) - hz["delka_m"] / 2.0)
    b = abs(-dx * uz + dz * ux)
    d = math.hypot(a, max(0.0, b - hz["koruna_sirka_m"] / 2.0))
    return ryb["hladina_y"] + hz["koruna_nad_hladinou_m"] - d * hz["sklon_svahu"]


def rybnik_toku(V, t):
    """Rybnik, ze ktereho odtok vytece (nejblizsi stred k prvnimu bodu osy), nebo None."""
    if not t["id"].endswith("odtok"):
        return None
    x, z = t["osa_xzy"][0][0], t["osa_xzy"][0][1]
    best = None
    for k in ("rybnik_lhota", "rybnik_tvrz"):
        r = V[k]
        d = math.hypot(x - r["stred"][0], z - r["stred"][1])
        if best is None or d < best[0]:
            best = (d, r)
    return best[1] if best and best[0] < 60.0 else None


def v_hrazi(V):
    """[(id toku, pocet bodu v hrazi od zacatku, prvni bod za hrazi)]."""
    out = []
    for t in V["toky"]:
        r = rybnik_toku(V, t)
        if r is None:
            continue
        n = 0
        for p in t["osa_xzy"]:
            if hraz_y(p[0], p[1], r) > p[2] - t["hloubka_m"]:
                n += 1
            else:
                break
        out.append((t["id"], n, t["osa_xzy"][n] if n < len(t["osa_xzy"]) else None))
    return out


if __name__ == "__main__":
    V = json.load(open(P, encoding="utf-8"))
    for tid, n, p in v_hrazi(V):
        print("odtok %s: %d bodu osy v telese hraze, zacatek za hrazi %s" % (tid, n, p))
    if "--zapis" in sys.argv:
        for tid, n, p in v_hrazi(V):
            t = [t for t in V["toky"] if t["id"] == tid][0]
            t["osa_xzy"] = t["osa_xzy"][n:]
        # format souboru = json indent 1 (round-trip beze zmeny)
        open(P, "w", encoding="utf-8").write(json.dumps(V, ensure_ascii=False, indent=1) + "\n")
        print("zapsano", P)
