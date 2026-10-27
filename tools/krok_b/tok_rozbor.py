import json, math
D = json.load(open("vysky.json")); T = json.load(open("tok.json"))
K, X0, Z0, nx, nz, H = D['K'], D['X0'], D['Z0'], D['nx'], D['nz'], D['h']
DIR, ACC, F = T['DIR'], T['ACC'], T['F']
pos = lambda c: (X0 + (c % nx) * K, Z0 + (c // nx) * K)
idx = lambda x, z: int(round((z - Z0) / K)) * nx + int(round((x - X0) / K))
def dolu(c, n=100000):
    p = [c]
    while DIR[p[-1]] >= 0 and len(p) < n: p.append(DIR[p[-1]])
    return p
# vystupy z mapy (okraj) s nejvetsim povodim
out = {}
for c in range(len(ACC)):
    if DIR[c] < 0: out[c] = ACC[c]
top = sorted(out.items(), key=lambda t: -t[1])[:8]
print("vystupy:", [(pos(c), round(a * K * K / 1e4, 1)) for c, a in top], "ha")
# rybnik Lhota: kam z nej voda tece, a odkud do nej
c = idx(525, 879); p = dolu(c)
print("z Lhoty voda tece pres", [tuple(round(v) for v in pos(q)) for q in p[::20]], "-> vystup", pos(p[-1]), "delka", len(p) * K)
# povodi do Lhoty: nejvetsi pritok proti proudu
def proti(c):
    path = [c]
    while True:
        ups = [n for n in range(len(DIR)) if False]
        break
    return path
up = {}
for q in range(len(DIR)):
    if DIR[q] >= 0: up.setdefault(DIR[q], []).append(q)
def nahoru(c):
    path = [c]
    while up.get(path[-1]):
        path.append(max(up[path[-1]], key=lambda q: ACC[q]))
    return path
pr = nahoru(c)
print("pritok do Lhoty proti proudu:", [(tuple(round(v) for v in pos(q)), round(F[q], 1), ACC[q]) for q in pr[::15]], "pramen", pos(pr[-1]), round(F[pr[-1]], 1))
# Bystrice: kolik bodu osy lezi na odtokove care (ACC velke)
V = json.load(open('/home/user/tvrz-claude/pravidla/svet/voda.json'))
osa = V['potok']['osa']
na = sum(1 for x, z in osa if 0 <= idx(x, z) < len(ACC) and max(ACC[idx(x + dx, z + dz)] for dx in (-10, -5, 0, 5, 10) for dz in (-10, -5, 0, 5, 10) if 0 <= idx(x+dx, z+dz) < len(ACC)) > 400)
print("Bystrice: bodu osy u udolnice (povodi > 1 ha)", na, "z", len(osa))
# tvrz: udolnice 120-600 m od tvrze s povodim 2-30 ha, kam tecou
kand = []
for q in range(len(ACC)):
    x, z = pos(q); d = math.hypot(x, z)
    if 150 < d < 600 and 80 < ACC[q] < 1200:
        kand.append(q)
vys = {}
for q in kand:
    e = dolu(q)[-1]; vys.setdefault(e, []).append(q)
for e, qs in sorted(vys.items(), key=lambda t: -len(t[1]))[:8]:
    best = max(qs, key=lambda q: ACC[q])
    print("tvrz: vystup", tuple(round(v) for v in pos(e)), "bunek", len(qs), "nejvetsi povodi", round(ACC[best] * K * K / 1e4, 1), "ha u", tuple(round(v) for v in pos(best)), "y", round(F[best], 1))
