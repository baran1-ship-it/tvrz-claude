# Odtok vody po terenu (krok B, radce 16:50-16:55): priority-flood (bez bezodtokych der), D8 smer, plocha povodi.
import json, math, heapq
D = json.load(open("vysky.json"))
K, X0, Z0, nx, nz, H = D['K'], D['X0'], D['Z0'], D['nx'], D['nz'], D['h']
N = nx * nz
F = list(H)
done = bytearray(N)
pq = []
for j in range(nz):
    for i in range(nx):
        if i in (0, nx - 1) or j in (0, nz - 1):
            heapq.heappush(pq, (H[j * nx + i], j * nx + i)); done[j * nx + i] = 1
NB = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
order = []
while pq:
    v, c = heapq.heappop(pq); order.append(c)
    ci, cj = c % nx, c // nx
    for di, dj in NB:
        a, b = ci + di, cj + dj
        if 0 <= a < nx and 0 <= b < nz:
            n = b * nx + a
            if not done[n]:
                done[n] = 1; F[n] = max(H[n], v + 1e-4); heapq.heappush(pq, (F[n], n))
# smer: nejprudsi sestup na vyplnenem terenu (z poradi vyplneni je vzdy kam tect)
DIR = [-1] * N
for c in range(N):
    ci, cj = c % nx, c // nx
    best, bd = None, 0.0
    for di, dj in NB:
        a, b = ci + di, cj + dj
        if 0 <= a < nx and 0 <= b < nz:
            n = b * nx + a
            s = (F[c] - F[n]) / math.hypot(di, dj)
            if s > bd: bd, best = s, n
    DIR[c] = best if best is not None else -1
ACC = [1] * N
for c in reversed(order):            # od nejvyssich (posledni ve fronte vyplneni) dolu
    if DIR[c] >= 0: ACC[DIR[c]] += ACC[c]
def pos(c): return (X0 + (c % nx) * K, Z0 + (c // nx) * K)
def idx(x, z): return int(round((z - Z0) / K)) * nx + int(round((x - X0) / K))
json.dump({"DIR": DIR, "ACC": ACC, "F": F}, open("tok.json", "w"))
print("hotovo", nx, nz)
