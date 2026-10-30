"""Plánovač přístupových cest k hradu (A* nad terénem, cena = délka × (1 + k·nadsklon), zakázaný max. sklon).
Havran: vozová cesta ≤ 12,5 %. Středověké hradní cesty bývaly strmší (KCD Trosky, Pirkštejn ~15–18 %) – úvozy.
python3 pristup.py <vystup.json> "x,z" "x,z" [max_sklon]"""
import sys, json, heapq
import numpy as np
v = json.load(open("hra/data/vysek.json"))
r = np.fromfile("hra/data/vysek.r16", "<u2").reshape(v["vyska"], v["sirka"]) / 200 + 300 - v["pocatek_H"]
def h(x, z): return float(r[int(round(z - v["z0_hra"])), int(round(x - v["x0_hra"]))])
K = 4; x0, z0 = -600, -700; NX, NZ = 300, 330
H = np.array([[h(x0 + i * K, z0 + j * K) for i in range(NX)] for j in range(NZ)])
out, A, B = sys.argv[1], sys.argv[2], sys.argv[3]; maxs = float(sys.argv[4]) if len(sys.argv) > 4 else 0.16
st = tuple(map(float, A.split(","))); gl = tuple(map(float, B.split(",")))
s = (int((st[1] - z0) // K), int((st[0] - x0) // K)); g = (int((gl[1] - z0) // K), int((gl[0] - x0) // K))
dist = {s: 0}; prev = {}; q = [(0, s)]
while q:
    d, u = heapq.heappop(q)
    if u == g: break
    if d > dist[u]: continue
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            if not di and not dj: continue
            w = (u[0] + dj, u[1] + di)
            if not (0 <= w[0] < NZ and 0 <= w[1] < NX): continue
            X = x0 + w[1] * K; Z = z0 + w[0] * K
            if -12 < X < 48 and -50 < Z < 28 and w != g: continue      # jádro A
            L = K * np.hypot(di, dj); sl = abs(H[w] - H[u]) / L
            if sl > maxs and np.hypot(X - gl[0], Z - gl[1]) > 14 and np.hypot(X - st[0], Z - st[1]) > 14: continue
            c = d + L * (1 + 10 * max(0, sl - 0.06))
            if c < dist.get(w, 1e18): dist[w] = c; prev[w] = u; heapq.heappush(q, (c, w))
if g not in prev:
    print("NENALEZENO", A, B, maxs); sys.exit(1)
p = [g]
while p[-1] != s: p.append(prev[p[-1]])
c = [[x0 + b * K, z0 + a * K, round(float(H[a, b]), 1)] for a, b in p[::-1]]
L = sum(np.hypot(c[i + 1][0] - c[i][0], c[i + 1][1] - c[i][1]) for i in range(len(c) - 1))
sk = [abs(c[i + 1][2] - c[i][2]) / np.hypot(c[i + 1][0] - c[i][0], c[i + 1][1] - c[i][1]) for i in range(len(c) - 1)]
print(f"{A} -> {B}: délka {L:.0f} m, převýšení {c[-1][2]-c[0][2]:+.0f} m, max sklon {max(sk)*100:.0f} %, průměr {abs(c[-1][2]-c[0][2])/L*100:.1f} %")
json.dump(c, open(out, "w"))
