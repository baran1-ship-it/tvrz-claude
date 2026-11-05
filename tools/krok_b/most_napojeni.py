"""Osa cesty na most a z mostu (Misa 5. 11., 0.99991 u (205, 594): „cesta na most nevede, je vedle nej“).

Most pres Bystrici staví Blender (kraj.bridge -> Most_potok) rovne podel osy cesty v miste krizeni, delka z sirky
koryta (radce 27. 10. 17:20) = 2 x 26,75 m. Osa odbocka_ves ale byla rovna jen 27 m kolem stredu, za tim se stacela
(klikateni kraj._meander) -> na obou koncich mostovky vedla cesta 3-5 m vedle mostu a najezd (svet.gd najezd_y,
rovne za koncem mostovky) zustal v trave.

Pravidlo (zaznam cesty.json prechody, druh most): osa cesty lezi na ose mostu po celé mostovce a jeste najezd_m za
kazdym koncem (rovny najezd hry); dal se k puvodni ose vrati obloukem (kubicka krivka, tecny na obou koncich),
napojeni na puvodni bod nejdriv oblouk_m od konce najezdu. Body osy po krok_m (kraj._bridge chce body do 6 m).
Body osy na mostovce (na primce mostu) zustavaji, takze kraj.bridge() vychazi stejne - nastroj to overi.
Stred a polomer zaznamu = stred mostu a pul delky + najezd (plánovac cesty_sklon je drzi pevne, test smyslu brod).

Oblouk muze zkratit puvodni klikatou trasu do svahu -> potom vzdy tools/krok_b/cesty_sklon.py --zapis (body v polomeru
mostu drzi pevne) a test smyslu (cesta_sklon, brod, koryto). 5. 11.: oblouk zapadne od mostu 13 % -> cesty_sklon usek 25-37.

  python3 tools/krok_b/most_napojeni.py [--zapis]"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "blender"))
CESTA = os.path.join(ROOT, "pravidla", "svet", "cesty.json")
C = json.load(open(CESTA, encoding="utf-8"))

import kraj  # noqa: E402

br = kraj.bridge()
if br is None:
    sys.exit("most_napojeni: kraj.bridge() = None (osa cesty nema u potoka body do 6 m)")
bx, bz, dx, dz, span = br
zm = 0
for pr in C["prechody"]:
    if pr["druh"] != "most":
        continue
    voz = {o["id"]: o for o in C["vozove"]}
    osa = [tuple(p) for p in voz[pr["cesta"]]["osa"]]
    nj, obl, krok = pr["najezd_m"], pr["oblouk_m"], pr["krok_m"]
    t_ = lambda p: (p[0] - bx) * dx + (p[1] - bz) * dz             # podel mostu
    l_ = lambda p: -(p[0] - bx) * dz + (p[1] - bz) * dx            # napric
    i0 = min(range(len(osa)), key=lambda i: math.hypot(osa[i][0] - bx, osa[i][1] - bz))
    # souvisly usek puvodnich bodu na primce mostu kolem krizeni (zustava beze zmeny)
    a, b = i0, i0
    while a > 0 and abs(l_(osa[a - 1])) < 0.05 and abs(t_(osa[a - 1])) < span + nj + 0.01:
        a -= 1
    while b < len(osa) - 1 and abs(l_(osa[b + 1])) < 0.05 and abs(t_(osa[b + 1])) < span + nj + 0.01:
        b += 1
    smer = 1 if t_(osa[b]) > t_(osa[a]) else -1                   # osa jde po +t (1) nebo proti (-1)
    hotovo = min(abs(t_(osa[a])), abs(t_(osa[b]))) > span + nj - 0.01   # osa uz po pravidle (opakovany beh nic nemeni)

    def strana(idx, kam):
        """Body od konce rovneho useku (index idx) ven (kam = +1/-1 v indexech osy) az po napojeni (bez nej) a index napojeni."""
        sg = smer * kam                                           # znamenko t na teto strane
        e = (bx + dx * sg * (span + nj), bz + dz * sg * (span + nj))
        j = idx + kam
        while 0 <= j + kam < len(osa) and not (math.dist(osa[j], e) >= obl and t_(osa[j]) * sg > span + nj + 0.5 * obl):
            j += kam
        # rovne po mostovce a najezdu od posledniho puvodniho bodu na primce
        t0 = t_(osa[idx]) * sg
        n = max(1, math.ceil((span + nj - t0) / krok))
        body = [(bx + dx * sg * (t0 + (span + nj - t0) * k / n), bz + dz * sg * (t0 + (span + nj - t0) * k / n)) for k in range(1, n + 1)]
        # oblouk k puvodni ose: tecna na konci najezdu = osa mostu ven, v napojeni = smer puvodni osy dovnitr
        p0, p3 = e, osa[j]
        q = osa[j + kam] if 0 <= j + kam < len(osa) else osa[j]
        tx, tz = p3[0] - q[0], p3[1] - q[1]
        tl = math.hypot(tx, tz) or 1.0
        d = math.dist(p0, p3) / 3.0
        p1 = (p0[0] + dx * sg * d, p0[1] + dz * sg * d)
        p2 = (p3[0] + tx / tl * d, p3[1] + tz / tl * d)
        dl = sum(math.dist(u, w) for u, w in zip([p0, p1, p2], [p1, p2, p3]))
        m = max(2, math.ceil(dl / krok))
        for k in range(1, m):
            s = k / m
            u = 1 - s
            body.append((u ** 3 * p0[0] + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s ** 3 * p3[0],
                         u ** 3 * p0[1] + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s ** 3 * p3[1]))
        return body, j

    if hotovo:
        print("%s: osa uz vede po mostu a najezdech (body %d-%d)" % (pr["id"], a, b))
    else:
        pred, ja = strana(a, -1)
        za, jb = strana(b, 1)
        nova = osa[:ja + 1] + list(reversed(pred)) + osa[a:b + 1] + za + osa[jb:]
        nova = [[round(p[0], 2), round(p[1], 2)] for p in nova]
        print("%s: rovny usek %d-%d, napojeni %d a %d, bodu %d -> %d" % (pr["id"], a, b, ja, jb, len(osa), len(nova)))
        print("  pred: " + " ".join("(%.1f, %.1f)" % p for p in reversed(pred)))
        print("  za:   " + " ".join("(%.1f, %.1f)" % p for p in za))
        novy = nova[ja:ja + len(pred) + (b - a + 1) + len(za) + 2]          # od napojeni k napojeni
        mx = max(math.dist(u, w) for u, w in zip(novy, novy[1:]))
        if mx > 6.0:
            sys.exit("most_napojeni: krok osy %.1f m > 6 m (kraj._bridge)" % mx)
        voz[pr["cesta"]]["osa"] = nova
        zm += 1
    st = [round(bx, 2), round(bz, 2)]
    pol = round(span + nj, 1)
    if pr["stred"] != st or pr["polomer_m"] != pol:
        pr["stred"], pr["polomer_m"] = st, pol
        zm += 1
    # kontrola: most z nove osy stejny (body na mostovce se nehnuly)
    kraj.ODBOCKA[:] = [tuple(p) for p in voz["odbocka_ves"]["osa"]]
    kraj._BR.clear()
    br2 = kraj.bridge()
    if br2 is None or max(abs(u - w) for u, w in zip(br, br2)) > 1e-6:
        sys.exit("most_napojeni: most z nove osy jinde %s -> %s" % (br, br2))

print("zmen %d" % zm)
if "--zapis" in sys.argv and zm:
    with open(CESTA, "w", encoding="utf-8") as f:
        json.dump(C, f, ensure_ascii=False, indent=1)
    print("zapsano", CESTA)
