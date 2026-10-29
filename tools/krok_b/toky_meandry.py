"""Meandry malych toku (Misa 0.992, potreti: „potok je furt jak vybagrovany, mel by mit prirozene zatacky a meandry“).
Osa z planovace sledovala udolnici lomenou carou (lomy az 124 st., mezi nimi rovne useky) - koryto vypadalo jako kanal.
Reserse (Leopold & Langbein 1966, Williams 1986, USGS „River meanders and channel size“): vlna meandru ~11 sirek
koryta (10-14), polomer zatacky 2-3 sirky, krivolakost nizinneho toku od 1,3; na prudkem svahu je tok primejsi.
Postup (cisla voda.json toky_tvar.meandry):
  1. osa po 1 m, vyhlazeni (gauss vyhlazeni_m) = udolnice bez lomu
  2. bocni posun A(s) sin(phi(s)), phi s promennou vlnou (vlna_sirek x sirka +- nahodnost), A = amplituda_vlny x vlna,
     zmensena na svahu (sklon_od..sklon_do) a k pevnym bodum (brody/mosty z cesty.json prechody, dil mlyna, rybniky,
     konce toku) nulova s nabehem nabeh_m
  3. kontrola: nejmensi polomer zatacky >= polomer_min_sirek x sirka (jinak mensi amplituda v tom useku)
Hladinu pak prepocita tools/krok_b/toky_hladina.py (hladina po proudu jen klesa, breh nad hladinou).
  /opt/bl/bin/python tools/krok_b/toky_meandry.py          vypis
  /opt/bl/bin/python tools/krok_b/toky_meandry.py zapis    prepise osa_xzy ve voda.json"""
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "blender"))
import kraj  # noqa: E402

VP = os.path.join(ROOT, "pravidla", "svet", "voda.json")
V = json.load(open(VP))
M = V["toky_tvar"]["meandry"]
C = json.load(open(os.path.join(ROOT, "pravidla", "svet", "cesty.json")))
zapis = sys.argv[1:2] == ["zapis"]


def preved(o, krok=1.0):
    """Osa po krok m (linearne), bez zdvojenych bodu; y linearne."""
    p = [o[0]]
    for q in o[1:]:
        if math.hypot(q[0] - p[-1][0], q[1] - p[-1][1]) > 1e-3:
            p.append(q)
    out = [list(p[0])]
    zbytek = 0.0
    for a, b in zip(p, p[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        t = krok - zbytek
        while t <= d:
            f = t / d
            out.append([a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f])
            t += krok
        zbytek = d - (t - krok)
    if math.hypot(out[-1][0] - p[-1][0], out[-1][1] - p[-1][1]) > 0.3:
        out.append(list(p[-1]))
    return out


def vyhlad(o, sigma):
    """Gauss v x, z (konce pevne, okno 3 sigma)."""
    n = len(o)
    w = int(3 * sigma)
    g = [math.exp(-0.5 * (k / sigma) ** 2) for k in range(-w, w + 1)]
    out = []
    for i in range(n):
        sx = sz = sw = 0.0
        for k in range(-w, w + 1):
            j = min(n - 1, max(0, i + k))
            sx += o[j][0] * g[k + w]
            sz += o[j][1] * g[k + w]
            sw += g[k + w]
        f = min(1.0, min(i, n - 1 - i) / max(1.0, w))     # u koncu puvodni bod (napojeni na nadrz, pramen)
        out.append([o[i][0] * (1 - f) + sx / sw * f, o[i][1] * (1 - f) + sz / sw * f, o[i][2]])
    return out


def polomer_min(o):
    r = 1e9
    for i in range(1, len(o) - 1):
        a, b, c = o[i - 1], o[i], o[i + 1]
        ab = math.hypot(b[0] - a[0], b[1] - a[1])
        bc = math.hypot(c[0] - b[0], c[1] - b[1])
        ac = math.hypot(c[0] - a[0], c[1] - a[1])
        cr = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        if cr > 1e-9:
            r = min(r, ab * bc * ac / (2 * cr))
    return r


def lom_max(o):
    m = 0.0
    for i in range(1, len(o) - 1):
        a = math.atan2(o[i][1] - o[i - 1][1], o[i][0] - o[i - 1][0])
        b = math.atan2(o[i + 1][1] - o[i][1], o[i + 1][0] - o[i][0])
        m = max(m, abs((b - a + math.pi) % (2 * math.pi) - math.pi) * 57.2958)
    return m


for tj in V["toky"]:
    rng = random.Random(sum(ord(ch) * (k + 1) for k, ch in enumerate(tj["id"])))
    w = float(tj["sirka_m"])
    puv = preved(tj["osa_xzy"])
    zakl = vyhlad(puv, float(M["vyhlazeni_m"]))
    n = len(zakl)
    # pevne body: brody a mosty tohoto toku, dil mlyna, rybniky, konce
    pevne = [(p["stred"], float(p["polomer_m"])) for p in C["prechody"] if p.get("tok") == tj["id"]]
    for r in kraj.RYBNIKY:
        pevne.append((r["stred"], float(r.get("polomer_m", r.get("voda_polomer_m", 0.0)))))
    nab = float(M["nabeh_m"])
    taper = []
    for i, (x, z, y) in enumerate(zakl):
        d = min(i, n - 1 - i) - nab * 0.5
        for (c, rr) in pevne:
            d = min(d, math.hypot(x - c[0], z - c[1]) - rr)
        if kraj.v_dilu_mlyna(x, z):
            d = -1.0
        taper.append(max(0.0, min(1.0, d / nab)))
    # sklon hladiny (puvodni y po proudu) - na prudkem svahu primejsi
    sk = []
    for i in range(n):
        a, b = max(0, i - 5), min(n - 1, i + 5)
        sk.append(abs(zakl[a][2] - zakl[b][2]) / max(1.0, b - a))
    s0, s1 = float(M["sklon_od"]), float(M["sklon_do"])
    # normala zakladni osy
    nor = []
    for i in range(n):
        a, b = zakl[max(0, i - 1)], zakl[min(n - 1, i + 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        nor.append((-(b[1] - a[1]) / L, (b[0] - a[0]) / L))
    zmena = float(M["nahodnost"])
    if "-v" in sys.argv:
        fs_ = [1.0 if sk[i] <= s0 else max(0.0, 1.0 - (sk[i] - s0) / max(1e-6, s1 - s0)) for i in range(n)]
        print("  %s: utlum pevnymi body prumer %.2f (nula u %d %%), sklonem prumer %.2f (sklon median %.3f, max %.3f)" % (
            tj["id"], sum(taper) / n, 100 * sum(1 for x in taper if x == 0) // n, sum(fs_) / n, sorted(sk)[n // 2], max(sk)))
    # sinusovka ve smeru toku (sine-generated curve, Langbein & Leopold 1966): odklon od udolnice theta(s) =
    # omega sin(2 pi s / vlna); bocni posun = integral sin(theta) ds, bez pomaleho driftu (odecten klouzavy prumer
    # pres vlnu). Krivolakost ~ 1/J0(omega), polomer v zatacce ~ vlna / (2 pi omega).
    for pokus in range(6):
        nas = 1.0 - 0.12 * pokus
        phi = rng.random() * math.tau
        lam = float(M["vlna_sirek"]) * w * (1 + zmena * (rng.random() * 2 - 1))
        off = [0.0]
        for i in range(1, n):
            if i % int(max(3, lam / 2)) == 0:                 # vlna se meni po pul vlnach (zadna pravidelna sinusovka)
                lam = float(M["vlna_sirek"]) * w * (1 + zmena * (rng.random() * 2 - 1))
            phi += math.tau / lam
            f_s = 1.0 if sk[i] <= s0 else max(0.0, 1.0 - (sk[i] - s0) / max(1e-6, s1 - s0))
            om = math.radians(float(M["odklon_st"])) * f_s * nas
            off.append(off[-1] + math.sin(om * math.sin(phi)))
        okno = int(float(M["vlna_sirek"]) * w)
        pr_off = []
        for i in range(n):
            a, b = max(0, i - okno // 2), min(n, i + okno // 2 + 1)
            pr_off.append(sum(off[a:b]) / (b - a))
        out = []
        for i, (x, z, y) in enumerate(zakl):
            o = (off[i] - pr_off[i]) * taper[i]
            out.append([x + nor[i][0] * o, z + nor[i][1] * o, y])
        out = preved(out)
        rmin = polomer_min(vyhlad(out, 1.0))
        if rmin >= float(M["polomer_min_sirek"]) * w:
            break
    out = vyhlad(out, 1.0)
    # hladina: z puvodni osy podle nejblizsiho bodu zakladni osy (preved y nese linearne) - toky_hladina ji upravi
    Lp = sum(math.hypot(out[i + 1][0] - out[i][0], out[i + 1][1] - out[i][1]) for i in range(len(out) - 1))
    Lz = sum(math.hypot(zakl[i + 1][0] - zakl[i][0], zakl[i + 1][1] - zakl[i][1]) for i in range(n - 1))
    pr = math.hypot(out[-1][0] - out[0][0], out[-1][1] - out[0][1]) or 1.0
    for i in range(len(out)):
        j = min(n - 1, int(round(i * (n - 1) / max(1, len(out) - 1))))
        out[i][2] = zakl[j][2]
    for i in range(1, len(out)):                         # po proudu jen klesa
        out[i][2] = min(out[i][2], out[i - 1][2])
    print("%s: %d -> %d bodu, delka %.0f -> %.0f m, krivolakost %.2f (puvodne %.2f), polomer min %.1f m (%.1f sirky), "
          "lom max %.0f -> %.0f st, utlum %.2f" % (tj["id"], len(tj["osa_xzy"]), len(out), Lz, Lp, Lp / pr,
                                                    sum(math.hypot(puv[i + 1][0] - puv[i][0], puv[i + 1][1] - puv[i][1]) for i in range(len(puv) - 1)) / pr,
                                                    rmin, rmin / w, lom_max(puv), lom_max(out), nas))
    if zapis:
        tj["osa_xzy"] = [[round(p[0], 3), round(p[1], 3), round(p[2], 3)] for p in out]
if zapis:
    open(VP, "w").write(json.dumps(V, ensure_ascii=False, indent=1))
    print("zapsano", VP)
