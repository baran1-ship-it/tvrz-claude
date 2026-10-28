"""Toky od cest (28. 10.: lhota_odtok tekl 15 m ulici vsi): krok planu vody po voda_sit.py, nad konecnymi osami cest
ze hry (build/protokol_stavby.json cesty - po posunu vsi). Bod osy toku blize ose cesty nez pulsirka cesty + pul
sirky toku + odstup (pasma.test.tok_od_cesty_m + voda breh_m), kde tok jde s cestou soubezne (uhel < 45 st.), se odsune
kolmo od osy cesty na tu vzdalenost - jako obejdi() kolem staveb. Krizeni (uhel >= 45 st.) zustava, potrebuje zaznam
prechodu v cesty.json (vypise se). Hladina bodu zustava (jen klesa). Pak vyhlazeni okoli posunu.

  python3 tools/krok_b/toky_od_cest.py [--zapis]
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V = json.load(open(os.path.join(ROOT, "pravidla", "svet", "voda.json")))
PA = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]
CESTY = json.load(open(os.path.join(ROOT, "build", "protokol_stavby.json")))["cesty"]
ODSTUP = PA["test"]["tok_od_cesty_m"] + PA["voda"]["breh_m"]
PUL_CESTY = 2.5                       # nejsirsi ulice/cesta ve vsi (pulsirka vozove 2,5 m, protokol nema sirky)


def nejblizsi(q):
    best = (1e9, None, None)
    for c in CESTY:
        for a, b in zip(c[:-1], c[1:]):
            dx, dz = b[0] - a[0], b[1] - a[1]
            L2 = dx * dx + dz * dz or 1e-9
            t = max(0.0, min(1.0, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dz) / L2))
            px, pz = a[0] + dx * t, a[1] + dz * t
            d = math.hypot(q[0] - px, q[1] - pz)
            if d < best[0]:
                L = math.sqrt(L2)
                best = (d, (px, pz), (dx / L, dz / L))
    return best


zmen = 0
krizeni = []
for tk in V["toky"]:
    o = tk["osa_xzy"]
    pul = tk["sirka_m"] * 0.5
    R = PUL_CESTY + pul + ODSTUP
    posun = [False] * len(o)
    for i in range(1, len(o) - 1):
        d, p, sc = nejblizsi(o[i][:2])
        if sc is None or d >= R:
            continue
        tx, tz = o[i + 1][0] - o[i - 1][0], o[i + 1][1] - o[i - 1][1]
        tn = math.hypot(tx, tz) or 1.0
        cos_u = abs((tx * sc[0] + tz * sc[1]) / tn)
        if cos_u < math.cos(math.radians(45.0)):
            krizeni.append((tk["id"], round(o[i][0]), round(o[i][1])))
            continue
        nx, nz = o[i][0] - p[0], o[i][1] - p[1]
        nn = math.hypot(nx, nz)
        if nn < 1e-3:
            nx, nz = -sc[1], sc[0]
            nn = 1.0
        o[i] = [round(p[0] + nx / nn * R, 2), round(p[1] + nz / nn * R, 2), o[i][2]]
        posun[i] = True
        zmen += 1
    # vyhlazeni okoli posunutych bodu (3 pruchody, krajni body a hladina beze zmeny)
    for _ in range(3):
        for i in range(1, len(o) - 1):
            if any(posun[max(0, i - 3):i + 4]) and not posun[i]:
                o[i] = [round(0.25 * o[i - 1][0] + 0.5 * o[i][0] + 0.25 * o[i + 1][0], 2),
                        round(0.25 * o[i - 1][1] + 0.5 * o[i][1] + 0.25 * o[i + 1][1], 2), o[i][2]]
print("toky od cest: posunuto %d bodu (odstup %.1f m od kraje)" % (zmen, ODSTUP))
uniq = sorted(set(krizeni))
print("krizeni toku s cestou (potreba zaznam prechodu v cesty.json): %d bodu, napr. %s" % (len(uniq), uniq[:10]))
if "--zapis" in sys.argv:
    json.dump(V, open(os.path.join(ROOT, "pravidla", "svet", "voda.json"), "w"), ensure_ascii=False, indent=1)
    print("zapsano do voda.json")
