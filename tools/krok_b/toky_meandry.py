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
import fort  # noqa: E402
import kraj  # noqa: E402

VP = os.path.join(ROOT, "pravidla", "svet", "voda.json")
V = json.load(open(VP))
M = V["toky_tvar"]["meandry"]
C = json.load(open(os.path.join(ROOT, "pravidla", "svet", "cesty.json")))
zapis = sys.argv[1:2] == ["zapis"]
# zarez koryta do terenu nejvys jako mez kroku voda v protokolu stavby (pasma.test.meze_kroku), rezerva na breh a dolinu
MEZ_ZAREZ = float(json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["test"]["meze_kroku"][
    "blender: voda (voda_tvar)"]["max_dy_m"]) - float(V["toky_tvar"]["breh_m"])


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
    # u pevnych bodu (dil mlyna, brody, mosty) puvodni osa i bez vyhlazeni (dil mlyna ma vlastni koryto v ose toku -
    # vyhlazena osa v nem ujela az o 1,3 m)
    zakl = [[p[0] * (1 - f) + q[0] * f, p[1] * (1 - f) + q[1] * f, q[2]] for p, q, f in zip(puv, zakl, taper)]
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
        # vlna nesmi koryto zariznout do svahu hloub nez MEZ_ZAREZ (export 0.993: lhota_odtok u (444, 932) 3,64 m) ani
        # hloub nez puvodni osa: v takovem miste mensi rozkmit (po krocich), meritko vyhlazene pres pul vlny
        hk = float(tj["hloubka_m"])
        mer = []
        for i, (x, z, y) in enumerate(zakl):
            o = (off[i] - pr_off[i]) * taper[i]
            if i % 2 or abs(o) < 0.2:
                mer.append(None)
                continue
            lim = max(MEZ_ZAREZ, fort.land(x, z, voda=False) - (y - hk))
            f = 1.0
            while f > 0.0 and fort.land(x + nor[i][0] * o * f, z + nor[i][1] * o * f, voda=False) - (y - hk) > lim:
                f -= 0.25
            mer.append(max(0.0, f))
        mer = [m if m is not None else 1.0 for m in mer]
        pul = max(1, int(float(M["vlna_sirek"]) * w / 2))
        mer = [min(mer[max(0, i - pul):i + pul + 1]) for i in range(n)]
        out = []
        for i, (x, z, y) in enumerate(zakl):
            o = (off[i] - pr_off[i]) * taper[i] * mer[i]
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
    # tok uz krivolaky (krivolakost_max): puvodni osa bez vln - vlny navic ho na svahu posunuly do strany a srovnani
    # hladiny zarizlo koryto pres zarez_max_m (export 0.993: tvrz_potok krivolakost 2,1, zarez 4,2 m u (-140, -188))
    Lpuv = sum(math.hypot(puv[i + 1][0] - puv[i][0], puv[i + 1][1] - puv[i][1]) for i in range(len(puv) - 1))
    puvodni = Lpuv / (math.hypot(puv[-1][0] - puv[0][0], puv[-1][1] - puv[0][1]) or 1.0) >= float(M["krivolakost_max"])
    if puvodni:
        out = [list(p) for p in tj["osa_xzy"]]
    # dil mlyna: osa a hladina toku v dilu = koryto modelu mlyna (mlyn_voda.json potok_v_dilu: dno, hladina +
    # mlyn.dil.potok_hladina_m). Vyhlazena osa v nem ujela az o 0,8 m a hladina lezela pod dnem dilu (Misa 0.992-0.994
    # „u mlyna netece voda, sede desky“, potreti) - uvnitr dilu zadna vlastni osa, jen zaznam dilu
    if kraj._MDIL and kraj._MDIL["tok"] == tj["id"]:
        dil = [i for i in range(len(out)) if kraj.v_dilu_mlyna(out[i][0], out[i][1])]
        if dil:
            hl_dil = float(V["mlyn"]["dil"]["potok_hladina_m"])
            body = [kraj.mlyn_svet(*q) for q in kraj._MVODA["potok_v_dilu"]["body"]]
            # napojeni na tok sveta plynulym obloukem ve smeru koryta dilu (Misa 0.994: tok za dilem uhnul o 90 st. hned
            # na hrane - „napojeni do T“; pred dilem se osa vracela, lom 159 st.): body sveta do NAPOJ_M od kraju koryta
            # dilu pryc, mezi nimi kvadraticka krivka s tecnou koryta dilu
            napoj = float(V["mlyn"]["dil"]["potok_napojeni_m"])
            ped = [q for q in out[:dil[0]] if math.hypot(q[0] - body[0][0], q[1] - body[0][2]) >= napoj]
            za = [q for q in out[dil[-1] + 1:] if math.hypot(q[0] - body[-1][0], q[1] - body[-1][2]) >= napoj]
            def oblouk(a, smer, b, smer_b):
                # kubicka krivka: v a tecna koryta dilu, v b tecna toku sveta (zadny lom na obou koncich)
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                c1 = (a[0] + smer[0] * L / 3, a[1] + smer[1] * L / 3)
                c2 = (b[0] - smer_b[0] * L / 3, b[1] - smer_b[1] * L / 3)
                k = max(2, int(L))
                return [[(1 - s) ** 3 * a[i] + 3 * (1 - s) ** 2 * s * c1[i] + 3 * (1 - s) * s * s * c2[i] + s ** 3 * b[i]
                         for i in (0, 1)] + [b[2]] for s in [j / k for j in range(1, k)]]
            def tecna(p, q):
                L = math.hypot(q[0] - p[0], q[2] - p[2]) or 1.0
                return ((q[0] - p[0]) / L, (q[2] - p[2]) / L)
            dov = [[bx, bz, by + hl_dil] for (bx, by, bz) in body]
            sv = lambda p, q: ((q[0] - p[0]) / (math.hypot(q[0] - p[0], q[1] - p[1]) or 1.0), (q[1] - p[1]) / (math.hypot(q[0] - p[0], q[1] - p[1]) or 1.0))
            pred = list(reversed(oblouk((body[0][0], body[0][2]), tecna(body[1], body[0]), ped[-1],
                                        sv(ped[-1], ped[-2]) if len(ped) > 1 else tecna(body[1], body[0])))) if ped else []
            po = oblouk((body[-1][0], body[-1][2]), tecna(body[-2], body[-1]), za[0],
                        sv(za[0], za[1]) if len(za) > 1 else tecna(body[-2], body[-1])) if za else []
            for q in pred:
                q[2] = ped[-1][2]
            out = ped + pred + dov + po + za
    # tok konci na hrane vody nadrze (Misa 0.992 „napojeni pritoku: plocha deska sterku do vody“, potreti): body uvnitr
    # rybnika (kraj.ryb_polomer) pryc, posledni bod na hrane - koryto a hladina toku se neprekryvaji s rybnikem
    ryb = V.get(tj.get("do", ""))
    if isinstance(ryb, dict) and "polomer_m" in ryb:
        uvnitr = lambda q: math.hypot(q[0] - ryb["stred"][0], q[1] - ryb["stred"][1]) < kraj.ryb_polomer(ryb, q[0], q[1])
        k = next((i for i in range(len(out)) if uvnitr(out[i])), None)
        if k is not None and k > 0:
            a, b = out[k - 1], out[k]
            lo, hi = 0.0, 1.0
            for _ in range(20):
                m = (lo + hi) / 2
                if uvnitr([a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m]):
                    hi = m
                else:
                    lo = m
            out = out[:k] + [[a[0] + (b[0] - a[0]) * lo, a[1] + (b[1] - a[1]) * lo, b[2]]]
    for i in range(1, len(out)):                         # po proudu jen klesa
        out[i][2] = min(out[i][2], out[i - 1][2])
    if puvodni:
        print("%s: krivolaky uz puvodne (%.2f), osa beze zmeny krome konce u nadrze (%d bodu)" % (tj["id"], Lpuv / (math.hypot(puv[-1][0] - puv[0][0], puv[-1][1] - puv[0][1]) or 1.0), len(out)))
    else:
        print("%s: %d -> %d bodu, delka %.0f -> %.0f m, krivolakost %.2f (puvodne %.2f), polomer min %.1f m (%.1f sirky), "
          "lom max %.0f -> %.0f st, utlum %.2f" % (tj["id"], len(tj["osa_xzy"]), len(out), Lz, Lp, Lp / pr,
                                                    sum(math.hypot(puv[i + 1][0] - puv[i][0], puv[i + 1][1] - puv[i][1]) for i in range(len(puv) - 1)) / pr,
                                                    rmin, rmin / w, lom_max(puv), lom_max(out), nas))
    if zapis:
        tj["osa_xzy"] = [[round(p[0], 3), round(p[1], 3), round(p[2], 3)] for p in out]
if zapis:
    open(VP, "w").write(json.dumps(V, ensure_ascii=False, indent=1))
    print("zapsano", VP)
