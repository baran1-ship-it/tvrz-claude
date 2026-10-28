# Trasa cesty po terenu (krok B, logika: vozova <= 12,5 %, po vrstevnici nebo sikmo svahem, blizko dnesni trasy).
import sys, json, math, heapq
D = json.load(open("vysky.json"))
K, X0, Z0, nx, nz, H = D['K'], D['X0'], D['Z0'], D['nx'], D['nz'], D['h']
def h(i, j): return H[j * nx + i]
def idx(x, z): return int(round((x - X0) / K)), int(round((z - Z0) / K))
def pos(i, j): return (X0 + i * K, Z0 + j * K)
def route(a, b, ref, gmax=0.10, w_ref=0.004, zakaz=lambda x, z: False, cena=lambda x, z: 1.0):
    # ref: dnesni osa (seznam bodu) - prirazka za vzdalenost od ni (svet zustane podobny)
    import bisect
    refg = {}
    for p in ref:
        refg.setdefault((int(p[0] // 20), int(p[1] // 20)), []).append(p)
    def dref(x, z):
        best = 1e9
        ci, cj = int(x // 20), int(z // 20)
        for di in range(-3, 4):
            for dj in range(-3, 4):
                for p in refg.get((ci + di, cj + dj), []):
                    best = min(best, (p[0] - x) ** 2 + (p[1] - z) ** 2)
        return math.sqrt(best) if best < 1e9 else 70.0
    sa, sb = idx(*a), idx(*b)
    nb = [(di, dj) for di in range(-2, 3) for dj in range(-2, 3) if (di, dj) != (0, 0) and math.gcd(abs(di), abs(dj)) == 1]
    g = {sa: 0.0}; prev = {}
    pq = [(0.0, sa)]
    while pq:
        f, u = heapq.heappop(pq)
        if u == sb: break
        if f > g[u] + math.hypot(u[0]-sb[0], u[1]-sb[1]) * K + 1e-6 and f != 0.0:
            pass
        for di, dj in nb:
            v = (u[0] + di, u[1] + dj)
            if not (0 <= v[0] < nx and 0 <= v[1] < nz): continue
            x, z = pos(*v)
            if zakaz(x, z): continue
            L = math.hypot(di, dj) * K
            gr = abs(h(*v) - h(*u)) / L
            if gr > gmax: continue
            c = L * (1.0 + 6.0 * max(0.0, gr - 0.05) + w_ref * min(dref(x, z), 70.0) ** 1.0) * cena(x, z)   # cena: prirazka (voda)
            ng = g[u] + c
            if ng < g.get(v, 1e18):
                g[v] = ng; prev[v] = u
                heapq.heappush(pq, (ng + math.hypot(v[0]-sb[0], v[1]-sb[1]) * K, v))
    if sb not in prev: return None
    p = [sb]
    while p[-1] != sa: p.append(prev[p[-1]])
    return [pos(*q) for q in reversed(p)]
if __name__ == '__main__':
    pass
