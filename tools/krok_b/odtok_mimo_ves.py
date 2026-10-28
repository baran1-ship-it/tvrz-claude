"""Odtok rybnika Lhota mimo ves (Misa 28. 10.: „klidne preloz potok mimo vesnici, ale podle systemu“; radce 17:40:
toky z terenu, cesty s vodou jako prekazkou, krizeni <= pasma.test.krizeni_max). Krok planu vody po voda_sit.py:
useku lhota_odtok od vypusti po prvni bod za vsi (smer mlyn) se naplanuje nova trasa po terenu pred vodou
(vysky.json, 5 m): zakazana plocha = obal usedlosti + lokace.json ves.toky_okraj_m, stavby, voda jen klesa (zarez
nejvys 3 m), cena = delka x (1 + 0,5 zarez) x 6 u osy cesty (protokol stavby). Zbytek toku (nahon, mlyn, udoli)
beze zmeny. Hladina jako voda_sit.hladina (min_spad, pod terenem o hloubku). Vypise krizeni s cestami.
  python3 tools/krok_b/odtok_mimo_ves.py [--zapis]"""
import heapq
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = json.load(open(os.path.join(ROOT, "tools", "krok_b", "vysky.json")))
K, X0, Z0, nx, nz, H = D["K"], D["X0"], D["Z0"], D["nx"], D["nz"], D["h"]
V = json.load(open(os.path.join(ROOT, "pravidla", "svet", "voda.json")))
L = json.load(open(os.path.join(ROOT, "pravidla", "svet", "lokace.json")))
PA = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]
try:
    CESTY = json.load(open(os.path.join(ROOT, "build", "protokol_stavby.json")))["cesty"]
except (OSError, ValueError, KeyError):
    CESTY = []
SPAD = V["potok"]["min_spad"]
ZAREZ_MAX = V["toky_tvar"]["zarez_max_m"]
OKRAJ = L["ves"]["toky_okraj_m"]


def hy(x, z):
    fi, fj = (x - X0) / K, (z - Z0) / K
    i, j = int(math.floor(fi)), int(math.floor(fj))
    i = max(0, min(nx - 2, i)); j = max(0, min(nz - 2, j))
    a, b = fi - i, fj - j
    h00, h10, h01, h11 = H[j * nx + i], H[j * nx + i + 1], H[(j + 1) * nx + i], H[(j + 1) * nx + i + 1]
    return (h00 * (1 - a) + h10 * a) * (1 - b) + (h01 * (1 - a) + h11 * a) * b


def obal(body):
    body = sorted(set(map(tuple, body)))
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in body:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(body):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


VES = obal([u["novy_stred"] for u in L["ves"]["usedlosti"]])


def od_obalu(x, z):
    """Kladne = venku (vzdalenost k obalu), zaporne uvnitr."""
    uvnitr = True
    best = 1e9
    for a, b in zip(VES, VES[1:] + VES[:1]):
        if (b[0] - a[0]) * (z - a[1]) - (b[1] - a[1]) * (x - a[0]) < 0:
            uvnitr = False
        dx, dz = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (z - a[1]) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(x - a[0] - t * dx, z - a[1] - t * dz))
    return -best if uvnitr else best


STAVBY = [(s["stred"], s.get("rovina_r_m", 10.0)) for s in L.get("stavby", [])]


def zakaz(x, z):
    if od_obalu(x, z) < OKRAJ:
        return True
    return any(math.hypot(x - c[0], z - c[1]) < r + 4.0 for c, r in STAVBY)


CM = {}
for c in CESTY:
    for p in c:
        CM.setdefault((int(p[0] // 8), int(p[1] // 8)), []).append(p)


def u_cesty(x, z):
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for p in CM.get((int(x // 8) + di, int(z // 8) + dj), []):
                if math.hypot(x - p[0], z - p[1]) < 6.0:
                    return True
    return False


def trasa(a, b, y0):
    def idx(x, z): return (int(round((x - X0) / K)), int(round((z - Z0) / K)))
    def pos(i, j): return (X0 + i * K, Z0 + j * K)
    sa, sb = idx(*a), idx(*b)
    nb = [(di, dj) for di in range(-2, 3) for dj in range(-2, 3) if (di, dj) != (0, 0) and math.gcd(abs(di), abs(dj)) == 1]
    g = {sa: 0.0}; lvl = {sa: y0}; prev = {}
    pq = [(0.0, sa)]
    while pq:
        f, u = heapq.heappop(pq)
        if u == sb:
            break
        if f > g[u] + math.hypot(u[0] - sb[0], u[1] - sb[1]) * K + 1e-6:
            continue
        for di, dj in nb:
            v = (u[0] + di, u[1] + dj)
            x, z = pos(*v)
            if v != sb and zakaz(x, z):
                continue
            hv = hy(x, z)
            zarez = max(0.0, hv - lvl[u])
            if zarez > ZAREZ_MAX:
                continue
            Lk = math.hypot(di, dj) * K
            # zarez drahy kvadraticky: tok drzi udolnici (ne kanal ve hrbetu)
            ng = g[u] + Lk * (1 + 4.0 * zarez * zarez) * (6.0 if u_cesty(x, z) else 1.0)
            if ng < g.get(v, 1e18):
                g[v] = ng; prev[v] = u; lvl[v] = min(lvl[u], hv)
                heapq.heappush(pq, (ng + math.hypot(v[0] - sb[0], v[1] - sb[1]) * K, v))
    if sb not in prev:
        return None
    p = [sb]
    while p[-1] != sa:
        p.append(prev[p[-1]])
    return [pos(*q) for q in reversed(p)]


def hladke(p, krok=1.0):
    for _ in range(3):
        n = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            n += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        n.append(p[-1]); p = n
    out = [p[0]]
    for q in p[1:]:
        if math.dist(q, out[-1]) >= krok:
            out.append(q)
    if out[-1] != p[-1]:
        out.append(p[-1])
    return out


def _main():
    tk = [t for t in V["toky"] if t["id"] == "lhota_odtok"][0]
    o = tk["osa_xzy"]
    # prvni bod za vsi smerem po proudu: posledni bod do obalu + okraj, pak az bod dal nez okraj + 10 m
    posl = max(i for i, q in enumerate(o) if od_obalu(q[0], q[1]) < OKRAJ)
    # napojeni: z kandidatu za vsi (az 60 bodu po proudu) ten, kde nova trasa prijde nejmin lomene (bez klicky) a krizi
    # nejmin cest - kazdy kandidat se naplanuje
    def lom(p):
        s = 0.0
        for a_, b_, c_ in zip(p, p[1:], p[2:]):
            u1 = (b_[0] - a_[0], b_[1] - a_[1]); u2 = (c_[0] - b_[0], c_[1] - b_[1])
            n1, n2 = math.hypot(*u1) or 1.0, math.hypot(*u2) or 1.0
            s += math.acos(max(-1.0, min(1.0, (u1[0] * u2[0] + u1[1] * u2[1]) / (n1 * n2))))
        return s


    j0 = next(i for i in range(posl, len(o)) if od_obalu(o[i][0], o[i][1]) > OKRAJ + 10.0)
    best = None
    # napojeni pred dilem mlyna (dil 40 x 40 m: polouhlopricka + pasma.dil.napojeni_m) - tok v dilu a s_toku zustavaji
    MD = V["mlyn"]["dil"]
    MLYN_R = 20.0 * math.sqrt(2.0) + PA["dil"]["napojeni_m"]
    for j in range(j0, min(len(o) - 2, j0 + 60), 6):
        if o[j][2] > o[0][2] or math.hypot(o[j][0] - MD["stred"][0], o[j][1] - MD["stred"][1]) < MLYN_R:
            continue
        r0 = trasa((o[0][0], o[0][1]), (o[j][0], o[j][1]), o[0][2])
        if r0 is None:
            continue
        cel = r0 + [tuple(q[:2]) for q in o[j:j + 12]]
        sk = lom(hladke(cel, 3.0))
        if best is None or sk < best[0]:
            best = (sk, j, r0)
    if best is None:
        sys.exit("odtok mimo ves: trasa nenalezena")
    _, j, r = best
    cil = o[j]
    r = hladke([(o[0][0], o[0][1])] + r[1:-1] + [(cil[0], cil[1])])
    nova = []
    y = o[0][2]
    for k, (x, z) in enumerate(r):
        if k:
            y = min(y - SPAD * math.dist(r[k], r[k - 1]), hy(x, z) - tk["hloubka_m"])
        nova.append([round(x, 2), round(z, 2), round(y, 3)])
    if nova[-1][2] < cil[2]:
        print("POZOR: hladina na konci nove trasy %.2f pod navazujici %.2f - zbytek toku se sklopi" % (nova[-1][2], cil[2]))
        for q in o[j:]:
            q[2] = min(q[2], nova[-1][2] - SPAD)
    osa = nova[:-1] + o[j:]
    delka = sum(math.dist(osa[k][:2], osa[k - 1][:2]) for k in range(1, len(osa)))


    def prusecik(p1, p2, p3, p4):
        d = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
        if abs(d) < 1e-9: return None
        t = ((p1[0] - p3[0]) * (p3[1] - p4[1]) - (p1[1] - p3[1]) * (p3[0] - p4[0])) / d
        u = -((p1[0] - p2[0]) * (p1[1] - p3[1]) - (p1[1] - p2[1]) * (p1[0] - p3[0])) / d
        return (round(p1[0] + t * (p2[0] - p1[0]), 1), round(p1[1] + t * (p2[1] - p1[1]), 1)) if 0 <= t <= 1 and 0 <= u <= 1 else None


    kr = []
    for ci, c in enumerate(CESTY):
        for a, b in zip(c[:-1], c[1:]):
            for k in range(len(osa) - 1):
                q = prusecik(osa[k][:2], osa[k + 1][:2], a, b)
                if q: kr.append((ci, q))
    print("zarez max %.2f m (mez %.1f)" % (max(hy(q[0], q[1]) - q[2] for q in nova), ZAREZ_MAX))
    print("odtok mimo ves: novy usek %d bodu (od vypusti po %s), cely tok %.0f m, nejblize vsi %.1f m za obalem, krizeni s cestami %d: %s"
          % (len(nova), [round(cil[0]), round(cil[1])], delka, min(od_obalu(q[0], q[1]) for q in osa[:len(nova)]), len(kr), kr))
    if "--zapis" in sys.argv:
        tk["osa_xzy"] = osa
        json.dump(V, open(os.path.join(ROOT, "pravidla", "svet", "voda.json"), "w"), ensure_ascii=False, indent=1)
        json.dump({"krizeni": kr}, open(os.path.join(ROOT, "build", "odtok_krizeni.json"), "w"))
        print("zapsano do voda.json")
        print("POZOR: mlyn.dil.s_toku (%s) je vzdalenost po toku - po zmene delky useku pred mlynem prepocitat tools/krok_b/mlyn_misto.py" % MD["s_toku"])


if __name__ == "__main__":
    _main()
