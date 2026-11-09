"""Hlidac statiky (Misa 9. 11., radek 87: „nesmysly typu tram podpira kamen“).

Stavitele (fort.py, sklep.py, hospodar.py) zapisuji nosne dily: jmeno, druh materialu a obal (kvadr ve svete, osa Y
nahoru). Export (export_game.main) po stavbe zavola kontrola(): kazdy dil, ktery nestoji na zemi, musi mit pod sebou
(nebo kolem sebe, kdyz je v nem vetknuty - tram ve zdi) dil z druhu, ktery ho smi nest (pravidla_sveta.json
statika.nese). Na zemi = spodek dilu u terenu (fort.land) a ne nad dutinou (sklep: otvor v terenu). Poruseni = chyba
exportu se jmenem dilu."""
import json
import os

DILY = []        # (jmeno, druh, (x0, y0, z0), (x1, y1, z1))
DUTINY = []      # (x0, y0, z0, x1, y1, z1): prostor bez zeminy (sklep) - dil nad ni na zemi nestoji

_PRAV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pravidla", "pravidla_sveta.json")


def pravidla():
    with open(_PRAV, encoding="utf-8") as f:
        return json.load(f)["statika"]


def dil(jmeno, druh, a, b, dx=0.0):
    """Zapise nosny dil (obal rohy a, b; dx = posun stavby, napr. vez o fort.TX)."""
    lo = (min(a[0], b[0]) + dx, min(a[1], b[1]), min(a[2], b[2]))
    hi = (max(a[0], b[0]) + dx, max(a[1], b[1]), max(a[2], b[2]))
    DILY.append((jmeno, druh, lo, hi))


def dutina(a, b):
    DUTINY.append((min(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2]), max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2])))


def reset():
    DILY.clear()
    DUTINY.clear()


def _na_zemi(lo, hi, zem, tol):
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    for d in DUTINY:
        if d[0] < cx < d[3] and d[2] < cz < d[5] and d[1] - tol <= lo[1] <= d[4] + tol:
            return False
    return lo[1] <= zem(cx, cz) + tol


def kontrola(zem):
    """zem(x, z) -> y terenu. Vrati pocet kontrolovanych dilu; poruseni -> ValueError se jmeny dilu."""
    pr = pravidla()
    nese = pr["nese"]
    tol = float(pr["tolerance_m"])
    chyby = []
    for jm, druh, lo, hi in DILY:
        if druh not in nese:
            chyby.append("%s: druh %s neni v pravidla_sveta.json statika.nese" % (jm, druh))
            continue
        if _na_zemi(lo, hi, zem, tol):
            continue
        podpora = []
        for jm2, druh2, lo2, hi2 in DILY:
            if jm2 == jm:
                continue
            # pudorys se prekryva (dotyk do tol), podpora siaha od spodku dilu dolu (lezi na ni nebo je v ni vetknuty)
            if lo2[0] > hi[0] + tol or hi2[0] < lo[0] - tol or lo2[2] > hi[2] + tol or hi2[2] < lo[2] - tol:
                continue
            if hi2[1] < lo[1] - tol or lo2[1] > lo[1] + tol:
                continue
            podpora.append((jm2, druh2))
        if not podpora:
            chyby.append("%s (%s, spodek y %.2f): nic pod nim - visi ve vzduchu" % (jm, druh, lo[1]))
        elif not any(d2 in nese[druh] for _, d2 in podpora):
            chyby.append("%s (%s) lezi jen na %s - %s smi nest jen %s" % (jm, druh, ", ".join("%s (%s)" % p for p in podpora[:3]), druh, nese[druh]))
    for c in chyby:
        print("STATIKA CHYBA", c)
    if chyby:
        raise ValueError("statika: %d poruseni, napr. %s" % (len(chyby), chyby[0]))
    print("statika: %d dilu OK" % len(DILY))
    return len(DILY)
