"""Presun dilu mlyna z toku (Misa 28. 10.: „dej ho kam chces, at je to cajk“; protokol Blenderu: odpad 2-5 m pod dnem
udoli lhota_odtok). Krok planu vody PRED mlyn_misto.py: z toku, na kterem dil stal (voda.json mlyn.dil.tok), se body
potoka dilu a odpadu odstrani a tok se od posledniho bodu pred dilem naplanuje znovu terenem k Bystrici (vysky.json:
zakaz obal vsi + lokace.json ves.toky_okraj_m a stavby, zarez nejvys toky_tvar.zarez_max_m, cena kvadraticka v zarezu).
Pak hladina celeho toku znovu podle pravidla (pod terenem o hloubku, jen klesa o min_spad). Osa vyhlazena po 1 m.
  python3 tools/krok_b/mlyn_presun.py [--zapis]
Potom: python3 tools/krok_b/mlyn_misto.py tools/krok_b/mlyn_voda.json --tok <novy tok> --za-puvodni --zapis"""
import heapq
import math
import os
import sys

sys.argv, _arg = sys.argv[:1], sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import odtok_mimo_ves as O                       # noqa: E402  (hy, zakaz, hladke, u_cesty, V, PA, CESTY - bez --zapis nic nepise)
sys.argv += _arg

import json                                       # noqa: E402
V = json.load(open(os.path.join(O.ROOT, "pravidla", "svet", "voda.json")))   # cerstve - import planovace muze menit O.V
MD = V["mlyn"]["dil"]
TOK = MD["tok"]
tk = [t for t in V["toky"] if t["id"] == TOK][0]
o = tk["osa_xzy"]
c, si = math.cos(MD["natoceni"]), math.sin(MD["natoceni"])


def lok(x, z):
    return (x - MD["stred"][0]) * c - (z - MD["stred"][1]) * si, (x - MD["stred"][0]) * si + (z - MD["stred"][1]) * c


uvnitr = [i for i, p in enumerate(o) if -22.5 <= lok(p[0], p[1])[0] <= 18.5 and -25.5 <= lok(p[0], p[1])[1] <= 15.5]
i0 = min(uvnitr)
REKA = V["potok"]["osa"]
R_CIL = V["potok"]["pulsirka_vody_m"] + 2.0


def d_reka(x, z):
    best = 1e9
    for a, b in zip(REKA, REKA[1:]):
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dz * dz or 1e-9
        u = max(0, min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / L))
        best = min(best, math.hypot(x - a[0] - dx * u, z - a[1] - dz * u))
    return best


K, X0, Z0, nx, nz = O.K, O.X0, O.Z0, O.nx, O.nz
start = (int(round((o[i0 - 1][0] - X0) / K)), int(round((o[i0 - 1][1] - Z0) / K)))
g, lvl, prev, pq, cil = {start: 0.0}, {start: o[i0 - 1][2]}, {}, [(0.0, start)], None
nb = [(di, dj) for di in range(-2, 3) for dj in range(-2, 3) if (di, dj) != (0, 0) and math.gcd(abs(di), abs(dj)) == 1]
while pq:
    f, u = heapq.heappop(pq)
    if f > g[u] + 1e-9:
        continue
    x, z = X0 + u[0] * K, Z0 + u[1] * K
    if d_reka(x, z) < R_CIL:
        cil = u
        break
    for di, dj in nb:
        v = (u[0] + di, u[1] + dj)
        if not (0 <= v[0] < nx and 0 <= v[1] < nz):
            continue
        x2, z2 = X0 + v[0] * K, Z0 + v[1] * K
        if O.zakaz(x2, z2):
            continue
        hv = O.hy(x2, z2)
        zarez = max(0.0, hv - lvl[u])
        if zarez > O.ZAREZ_MAX:
            continue
        ng = g[u] + math.hypot(di, dj) * K * (1 + 4.0 * zarez * zarez) * (6.0 if O.u_cesty(x2, z2) else 1.0)
        if ng < g.get(v, 1e18):
            g[v], prev[v], lvl[v] = ng, u, min(lvl[u], hv)
            heapq.heappush(pq, (ng, v))
if cil is None:
    sys.exit("mlyn_presun: trasa k Bystrici nenalezena")
p = [cil]
while p[-1] != start:
    p.append(prev[p[-1]])
r = O.hladke([tuple(o[i0 - 1][:2])] + [(X0 + q[0] * K, Z0 + q[1] * K) for q in reversed(p)][1:])
osa = [list(q) for q in o[:i0 - 1]] + [[round(x, 2), round(z, 2), 0.0] for x, z in r]
# hladina celeho toku podle pravidla (voda_sit.hladina): pod terenem o hloubku, jen klesa
hl = tk["hloubka_m"]
for k in range(1, len(osa)):
    ds = math.dist(osa[k][:2], osa[k - 1][:2])
    osa[k][2] = round(min(osa[k - 1][2] - O.SPAD * ds, O.hy(osa[k][0], osa[k][1]) - hl), 3)
zar = [O.hy(q[0], q[1]) - q[2] for q in osa]
print("mlyn_presun %s: dil od bodu %d pryc, nova trasa %d bodu k Bystrici, hladina %.2f -> %.2f, zarez max %.2f m u %s" % (
    TOK, i0, len(r), osa[0][2], osa[-1][2], max(zar), osa[zar.index(max(zar))][:2]))
if "--zapis" in sys.argv:
    tk["osa_xzy"] = osa
    json.dump(V, open(os.path.join(O.ROOT, "pravidla", "svet", "voda.json"), "w"), ensure_ascii=False, indent=1)
    print("zapsano do voda.json")
