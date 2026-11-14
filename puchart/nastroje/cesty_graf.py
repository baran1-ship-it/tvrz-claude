"""Síť cest pro rychlé cestování po mapě (Míša 14. 11.: figurka jede po cestách jako v KCD, dá se zastavit).
Zdroj: osy cest pravidla/svet/cesty_puchart.json (stejné, ze kterých se kreslí terén). Osy se zhustí, blízké body
sloučí, konce cest se napojí na nejbližší bod jiné cesty (křižovatky), body různých cest blíž než spoj_dotyk_m se
propojí (křížení); oddělené kusy sítě se spojí nejbližší dvojicí bodů do spoj_dilu_max_m. Parametry
pravidla/svet/mapa_body.json cestovani. Výstup hra/data/cesty_graf.json {uzly: [[x, z]], hrany: [[a, b]]}.
Použití: python3 nastroje/cesty_graf.py <K>"""
import json, math, os, sys

K = sys.argv[1]
P = json.load(open(os.path.join(K, "pravidla/svet/mapa_body.json")))["cestovani"]
C = json.load(open(os.path.join(K, "pravidla/svet/cesty_puchart.json")))["cesty"]
ZH, SL, KON, DOT, DIL = (float(P[k]) for k in ("zhusteni_m", "slouceni_m", "spoj_konce_m", "spoj_dotyk_m", "spoj_dilu_max_m"))

uzly = []; hrany = set(); cesta_uzlu = []; mrizka = {}
def _bunka(p): return (int(math.floor(p[0] / 20)), int(math.floor(p[1] / 20)))
def blizke(p, r):
    b = _bunka(p); n = int(math.ceil(r / 20))
    for i in range(b[0] - n, b[0] + n + 1):
        for j in range(b[1] - n, b[1] + n + 1):
            for k in mrizka.get((i, j), ()):
                if math.dist(uzly[k], p) <= r: yield k
def uzel(p, ci):
    for k in blizke(p, SL):   # sloučit (duplicitní osy, např. žlutá značka po stejné stezce)
        return k
    uzly.append([round(p[0], 2), round(p[1], 2)]); cesta_uzlu.append(ci); mrizka.setdefault(_bunka(p), []).append(len(uzly) - 1)
    return len(uzly) - 1

konce = []
for ci, c in enumerate(C):
    o = c["osa"]; pred = None
    for a, b in zip(o, o[1:]):
        n = max(1, int(math.ceil(math.dist(a, b) / ZH)))
        for t in range(n + (1 if (a, b) == (o[-2], o[-1]) else 0)):
            q = (a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n)
            k = uzel(q, ci)
            if pred is not None and pred != k: hrany.add((min(pred, k), max(pred, k)))
            pred = k
    konce += [(uzel(tuple(o[0]), ci), ci), (uzel(tuple(o[-1]), ci), ci)]

for k, ci in konce:   # křižovatky: konec cesty na nejbližší bod jiné cesty
    kand = [j for j in blizke(uzly[k], KON) if cesta_uzlu[j] != ci and j != k]
    if kand:
        j = min(kand, key=lambda j: math.dist(uzly[j], uzly[k])); hrany.add((min(j, k), max(j, k)))
for k in range(len(uzly)):   # křížení cest uprostřed
    for j in blizke(uzly[k], DOT):
        if j > k and cesta_uzlu[j] != cesta_uzlu[k]: hrany.add((k, j))

def dily():
    sous = [[] for _ in uzly]
    for a, b in hrany: sous[a].append(b); sous[b].append(a)
    d = [-1] * len(uzly); n = 0
    for s in range(len(uzly)):
        if d[s] >= 0: continue
        st = [s]; d[s] = n
        while st:
            u = st.pop()
            for v in sous[u]:
                if d[v] < 0: d[v] = n; st.append(v)
        n += 1
    return d, n
spojky = 0
while True:
    d, n = dily()
    if n <= 1: break
    vel = [d.count(i) for i in range(n)]; hl = vel.index(max(vel)); best = None
    for k in range(len(uzly)):
        if d[k] == hl: continue
        for j in blizke(uzly[k], DIL):
            if d[j] == hl and (best is None or math.dist(uzly[k], uzly[j]) < best[0]): best = (math.dist(uzly[k], uzly[j]), k, j)
    if best is None: break
    hrany.add((min(best[1], best[2]), max(best[1], best[2]))); spojky += 1
d, n = dily()
vel = sorted((d.count(i) for i in range(n)), reverse=True)
hl = max(range(n), key=lambda i: d.count(i))   # jen hlavní síť (oddělené kousky u okraje výseku se nedají dojet)
nove = {}; u2 = []
for k in range(len(uzly)):
    if d[k] == hl: nove[k] = len(u2); u2.append(uzly[k])
h2 = sorted((nove[a], nove[b]) for a, b in hrany if a in nove and b in nove)
out = {"zdroj": "nastroje/cesty_graf.py z pravidla/svet/cesty_puchart.json", "uzly": u2, "hrany": h2}
json.dump(out, open(os.path.join(K, "hra/data/cesty_graf.json"), "w"), separators=(",", ":"))
print("CESTY_GRAF uzlů %d, hran %d, spojek dílů %d, dílů %d (velikosti %s) – zapsána hlavní síť %d uzlů" % (len(uzly), len(hrany), spojky, n, vel[:6], len(u2)))
