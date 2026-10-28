"""Misto pro dil vodniho mlyna (Misa 21:44: model mlyn-1.zip z Disku, nemodelovat): dil 40 x 40 m s vlastnim potokem
(dno z 2,98 na -2,28 na 42 m), naonem z jizku, vantrokem, kolem a lednici. Hledani podel toku (voda.json toky) a
napric: potok dilu v ose toku (prumer odchylky < 2 m), vstup dilu ne nad hladinou toku proti proudu, vystup ne pod
hladinou po proudu (voda tece dolu), hrana dilu (bilinearni rohy) co nejbliz terenu (tools/krok_b/vysky.json, teren
pred vodou). Vypise nejlepsi mista; --zapis ulozi do voda.json mlyn.dil (stred, natoceni, y dvora).
  python3 tools/krok_b/mlyn_misto.py <mlyn_voda.json> [--tok lhota_odtok] [--zapis]"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
M = json.load(open(sys.argv[1]))
TOK = sys.argv[sys.argv.index("--tok") + 1] if "--tok" in sys.argv else "lhota_odtok"
V = json.load(open(os.path.join(ROOT, "pravidla", "svet", "voda.json")))
vys = json.load(open(os.path.join(ROOT, "tools", "krok_b", "vysky.json")))
K, X0, Z0, nx, nz = vys["K"], vys["X0"], vys["Z0"], vys["nx"], vys["nz"]


def hy(x, z):
    i, j = (x - X0) / K, (z - Z0) / K
    i0, j0 = max(0, min(nx - 2, int(i))), max(0, min(nz - 2, int(j)))
    fi, fj = min(1, max(0, i - i0)), min(1, max(0, j - j0))
    g = lambda a, b: vys["h"][b * nx + a]
    return (g(i0, j0) * (1 - fi) + g(i0 + 1, j0) * fi) * (1 - fj) + (g(i0, j0 + 1) * (1 - fi) + g(i0 + 1, j0 + 1) * fi) * fj


t = [x for x in V["toky"] if x["id"] == TOK][0]["osa_xzy"]
s = [0.0]
for i in range(1, len(t)):
    s.append(s[-1] + math.hypot(t[i][0] - t[i - 1][0], t[i][1] - t[i - 1][1]))
pv = M["potok_v_dilu"]["body"]
R = M["hrana_dilu"]["rohy"]
HLADINA_VSTUP = M["nahon"]["body"][0][1]          # hladina nad jizkem = hladina nahonu u odbocky (NAVOD_MLYN.md)


def hrana(lx, lz):
    """Bilinearni hrana dilu (lokalne)."""
    u = (lx - R["SW"][0]) / (R["SE"][0] - R["SW"][0])
    w = (lz - R["NW"][2]) / (R["SW"][2] - R["NW"][2])
    n = R["NW"][1] * (1 - u) + R["NE"][1] * u
    sj = R["SW"][1] * (1 - u) + R["SE"][1] * u
    return n * (1 - w) + sj * w


def do_sveta(lx, lz, cx, cz, yaw):
    c, si = math.cos(yaw), math.sin(yaw)
    return cx + lx * c + lz * si, cz - lx * si + lz * c


def d_osa(x, z):
    best = 1e9
    for a, b in zip(t, t[1:]):
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dz * dz or 1e-9
        u = max(0, min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / L))
        best = min(best, math.hypot(x - a[0] - dx * u, z - a[1] - dz * u))
    return best


def hladina_u(x, z):
    """Hladina toku v nejblizsim bode osy a jeho poloha s."""
    bi = min(range(len(t)), key=lambda i: math.hypot(t[i][0] - x, t[i][1] - z))
    return t[bi][2], s[bi]


LOK = json.load(open(os.path.join(ROOT, "pravidla", "svet", "lokace.json")))
DOMY = [u["novy_stred"] for u in LOK["ves"]["usedlosti"]] + [x["stred"] for x in LOK["stavby"]]
REKA = V["potok"]["osa"]
REKA_ODSTUP = V["potok"]["pulsirka_vody_m"] * V["potok"]["breh_nasobek"] + 3.0   # dil cely mimo koryto Bystrice


def d_reka(x, z):
    best = 1e9
    for a, b in zip(REKA, REKA[1:]):
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dz * dz or 1e-9
        u = max(0, min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / L))
        best = min(best, math.hypot(x - a[0] - dx * u, z - a[1] - dz * u))
    return best


SPAD = V["potok"]["min_spad"]
ZAREZ_MAX = V["toky_tvar"]["zarez_max_m"]
ZA_DILEM_M = V["mlyn"]["dil"]["odpad_za_dilem_m"]
vysledky = []
for i in range(len(t) - 1):
    # smer toku v useku ~ 42 m od bodu i
    j = i
    while j < len(t) - 1 and s[j] - s[i] < 42.0:
        j += 1
    if s[j] - s[i] < 30.0:
        continue
    fx, fz = t[j][0] - t[i][0], t[j][1] - t[i][1]
    fl = math.hypot(fx, fz)
    for dyaw in (-0.25, -0.12, 0.0, 0.12, 0.25):
        # lokalni +z (smer potoka v dilu) = smer toku; yaw: lokalni (lx, lz) -> svet
        yaw = math.atan2(fx / fl, fz / fl) - math.atan2(0.0623, 0.998) + dyaw
        for strana in (1, -1):
            yaw2 = yaw if strana > 0 else yaw  # dil je asymetricky (mlyn vpravo od potoka); zrcadlit nelze
            # poloha: vstup potoka dilu = bod toku i
            ex, ez = do_sveta(pv[0][0], pv[0][2], 0, 0, yaw2)
            cx, cz = t[i][0] - ex, t[i][1] - ez
            odch = sum(d_osa(*do_sveta(p[0], p[2], cx, cz, yaw2)) for p in pv) / len(pv)
            if odch > 2.5:
                continue
            if min(d_reka(*do_sveta(lx, lz, cx, cz, yaw2)) for lx in range(-22, 19, 4) for lz in range(-25, 16, 4)) < REKA_ODSTUP:
                continue
            # y dvora: hrana dilu na teren (nejmensi ctverce)
            obvod = [(lx, lz) for lx in range(-22, 19, 4) for lz in (-25, 15)] + [(lx, lz) for lx in (-22, 18) for lz in range(-25, 16, 4)]
            dif = [hy(*do_sveta(lx, lz, cx, cz, yaw2)) - hrana(lx, lz) for lx, lz in obvod]
            y0 = sum(dif) / len(dif)
            # voda navazuje: hladina na vstupu dilu (nad jizkem) = hladina toku proti proudu -> y dvora; tok za dilem
            # se pak jen prohloubi k hladine vystupu (vada = o kolik); hrana dilu se k terenu pritahne
            h_in, s_in = hladina_u(*do_sveta(pv[0][0], pv[0][2], cx, cz, yaw2))
            h_out, s_out = hladina_u(*do_sveta(pv[-1][0], pv[-1][2], cx, cz, yaw2))
            chyba_h = math.sqrt(sum((d - y0) ** 2 for d in dif) / len(dif))
            y0n = h_in - HLADINA_VSTUP
            chyba_h = math.sqrt(chyba_h ** 2 + (y0n - y0) ** 2)
            y0 = y0n
            vstup = h_in
            vystup = y0 + pv[-1][1] + 0.25
            vada = max(0.0, h_out - vystup)
            # odpad za dilem (28. 10. protokol Blenderu: zarez 4,7 m pod dilem): tok z vystupu klesa min_spad, teren nad
            # nim na dalsich ZA_DILEM_M nejvys toky_tvar.zarez_max_m - jinak misto nema spad pro kolo (vyska kola
            # musi byt v udoli, ne v prikopu)
            zarez = max([hy(t[k][0], t[k][1]) - (vystup - SPAD * (s[k] - s_out)) for k in range(len(t))
                         if 0.0 <= s[k] - s_out <= ZA_DILEM_M] or [0.0])
            if zarez > ZAREZ_MAX:
                continue
            vysledky.append((chyba_h + 2.0 * vada, chyba_h, vada, round(cx, 1), round(cz, 1), round(yaw2, 3), round(y0, 2), round(s[i]), round(odch, 1), round(vstup, 2), round(h_in, 2), round(vystup, 2), round(h_out, 2)))
vysledky.sort(key=lambda v: (v[2] + 0.5 * v[1]) if "--voda" in sys.argv else v[0])
print("MLYN mist %d; nejlepsi (skore, hrana rms, vada vody, x, z, yaw, y dvora, s toku, odchylka osy, vstup/hladina, vystup/hladina):" % len(vysledky))
vysledky = [v for v in vysledky if not any(math.hypot(v[3] - c[0], v[4] - c[1]) < 45.0 for c in DOMY)]
for v in vysledky[:10]:
    print("MLYN", v)
if "--zapis" in sys.argv and vysledky:
    b = vysledky[0]
    V["mlyn"]["dil"] = dict(V["mlyn"].get("dil", {}), **{"model": "res://modely/mlyn/mlyn.glb", "lod1": "res://modely/mlyn/mlyn_lod1.glb", "stred": [b[3], b[4]],
                        "natoceni": b[5], "y_dvora": b[6], "tok": TOK, "s_toku": b[7],
                        "popis": "dil vodniho mlyna (Disk Modely/budovy/mlyn-1.zip, NAVOD_MLYN.md) usazeny tools/krok_b/mlyn_misto.py: potok dilu v ose toku, hrana dilu na teren"})
    V["mlyn"]["stred"] = [b[3], b[4]]
    # tok: body uvnitr dilu nahradi potok dilu (hladina = dno + 0,25, nad jizkem hladina nahonu), za dilem se hladina
    # jen snizi k vystupu (voda tece dolu, zadny schod nahoru)
    c, si = math.cos(b[5]), math.sin(b[5])
    lok = lambda x, z: ((x - b[3]) * c - (z - b[4]) * si, (x - b[3]) * si + (z - b[4]) * c)
    uvnitr = [i for i, p in enumerate(t) if -22.5 <= lok(p[0], p[1])[0] <= 18.5 and -25.5 <= lok(p[0], p[1])[1] <= 15.5]
    i0, i1 = min(uvnitr), max(uvnitr)
    nove = []
    for k, p in enumerate(pv[::3] + [pv[-1]]):
        x, z = do_sveta(p[0], p[2], b[3], b[4], b[5])
        y = b[6] + (HLADINA_VSTUP if k == 0 else p[1] + 0.25)
        nove.append([round(x, 2), round(z, 2), round(y, 2)])
    # pod dilem: puvodni trasa vede rovinou (hladina by pod vystupem musela do zarezu az 3 m na 200 m) - tok z vystupu
    # nejlevnejsi cestou terenem k Bystrici (vysky.json, 8 sousedu, Dijkstra): cena = delka x (1 + zarez pod terenem
    # nad hladinou vystupu), mimo dil a domy; vyhlazeny (Chaikin, body po 6 m); hladina jen klesa (min_spad)
    import heapq
    ox, oz = nove[-1][0], nove[-1][1]
    y_out = nove[-1][2]
    start = (int(round((ox - X0) / K)), int(round((oz - Z0) / K)))
    vdilu = lambda x, z: -23.0 <= lok(x, z)[0] <= 19.0 and -26.0 <= lok(x, z)[1] <= 14.0
    cena, odkud, pq, cil = {start: 0.0}, {}, [(0.0, start)], None
    while pq:
        c0, (gi, gj) = heapq.heappop(pq)
        if c0 > cena.get((gi, gj), 1e18):
            continue
        x, z = X0 + gi * K, Z0 + gj * K
        if d_reka(x, z) < V["potok"]["pulsirka_vody_m"] + 2.0:
            cil = (gi, gj)
            break
        for a2 in (-1, 0, 1):
            for b2 in (-1, 0, 1):
                n = (gi + a2, gj + b2)
                if (a2, b2) == (0, 0) or not (0 <= n[0] < nx and 0 <= n[1] < nz):
                    continue
                x2, z2 = X0 + n[0] * K, Z0 + n[1] * K
                if vdilu(x2, z2) or any(math.hypot(x2 - c[0], z2 - c[1]) < 14.0 for c in DOMY):
                    continue
                zarez = max(0.0, vys["h"][n[1] * nx + n[0]] - y_out)
                c1 = c0 + K * math.hypot(a2, b2) * (1.0 + zarez)
                if c1 < cena.get(n, 1e18):
                    cena[n], odkud[n] = c1, (gi, gj)
                    heapq.heappush(pq, (c1, n))
    cesta, q = [], cil
    while q is not None and q != start:
        cesta.append((X0 + q[0] * K, Z0 + q[1] * K))
        q = odkud.get(q)
    cesta = [(ox, oz)] + cesta[::-1]
    for _ in range(3):
        n2 = [cesta[0]]
        for a, b2 in zip(cesta[:-1], cesta[1:]):
            n2 += [(0.75 * a[0] + 0.25 * b2[0], 0.75 * a[1] + 0.25 * b2[1]), (0.25 * a[0] + 0.75 * b2[0], 0.25 * a[1] + 0.75 * b2[1])]
        n2.append(cesta[-1])
        cesta = n2
    rs = [cesta[0]]
    for q in cesta[1:]:
        if math.hypot(q[0] - rs[-1][0], q[1] - rs[-1][1]) >= 6.0:
            rs.append(q)
    hl_tok = [x for x in V["toky"] if x["id"] == TOK][0]["hloubka_m"]
    y_konec = hy(*rs[-1]) - hl_tok
    vyst, za = y_out, []
    for q in rs[1:]:
        vyst = min(vyst - V["potok"]["min_spad"] * 6.0, max(hy(*q) - hl_tok, y_konec))
        za.append([round(q[0], 2), round(q[1], 2), round(vyst, 2)])
    pred = t[:i0]
    tok = [x for x in V["toky"] if x["id"] == TOK][0]
    tok["osa_xzy"] = pred + nove + za
    print("MLYN tok %s: body od %d nahrazeny potokem dilu (%d) a trasou spadem k Bystrici (%d bodu, hladina %.2f -> %.2f, zarez max %.1f m)" % (
        TOK, i0, len(nove), len(za), nove[-1][2], za[-1][2] if za else 0, max([hy(p[0], p[1]) - p[2] for p in za] or [0])))
    print("MLYN zarez pod dilem po 30 m:", [round(hy(p[0], p[1]) - p[2], 1) for p in za[::5]])
    json.dump(V, open(os.path.join(ROOT, "pravidla", "svet", "voda.json"), "w"), ensure_ascii=False, indent=1)
    print("MLYN zapsano do voda.json mlyn.dil")
