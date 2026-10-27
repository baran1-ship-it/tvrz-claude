# Vodni sit kroku B z odtoku po terenu (tok.json): toky = udolnice D8, vyhlazene; hladina jen klesa (min_spad), pod terenem.
import json, math
exec(open('tok_tvrz.py').read().split("C=json.load")[0])
V = json.load(open('/home/user/tvrz-claude/pravidla/svet/voda.json'))
SPAD = V['potok']['min_spad']
def trasa(cells):
    p = [pos(q) for q in cells]
    for _ in range(3):                                    # Chaikin
        n = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            n += [(0.75*a[0]+0.25*b[0], 0.75*a[1]+0.25*b[1]), (0.25*a[0]+0.75*b[0], 0.25*a[1]+0.75*b[1])]
        n.append(p[-1]); p = n
    out = [p[0]]; s = 0.0
    for q in p[1:]:
        if math.dist(q, out[-1]) >= 6.0: out.append(q)
    if out[-1] != p[-1]: out.append(p[-1])
    return out
def hy(x, z):
    i = (x - X0) / K; j = (z - Z0) / K; i0, j0 = int(i), int(j); fi, fj = i - i0, j - j0
    g = lambda a, b: H[min(nz-1, b) * nx + min(nx-1, a)]
    return (g(i0,j0)*(1-fi)+g(i0+1,j0)*fi)*(1-fj)+(g(i0,j0+1)*(1-fi)+g(i0+1,j0+1)*fi)*fj
def hladina(osa, y0, hloubka):
    out = []; y = y0
    for k, (x, z) in enumerate(osa):
        if k: y = min(y - SPAD * math.dist(osa[k], osa[k-1]), hy(x, z) - hloubka)
        else: y = min(y0, hy(x, z) - hloubka)
        out.append([round(x, 2), round(z, 2), round(y, 2)])
    return out
def cesta_dolu(c, stop):
    p = [c]
    while DIR[p[-1]] >= 0 and not stop(pos(p[-1])): p.append(DIR[p[-1]])
    return p
L0 = (525.08, 879.45); HL = 3.35
# Lhota: pritok z pramene (795, 895) do rybnika
pr = cesta_dolu(idx(795, 895), lambda q: math.dist(q, L0) < 14.0)
# odtok: z jihozapadniho okraje (vypust) po udolnici k Bystrici
reka = V['potok']['osa']
def u_reky(q): return min(math.dist(q, r) for r in reka) < 10.0
od = cesta_dolu(idx(515.7, 871.9), u_reky)
# tvrz (radce 18:20: tok rohem mapy 200-300 m, rybnik uprostred delky): udolnice od severniho okraje (-160, -238)
# (pramen na nejvyssim miste rohu (-155, -205), 0,9 m) k zapadnimu okraji; rybnik na polovine delky toku, hraz na jeho dolnim konci kolmo na proud
cela = cesta_dolu(idx(-155, -205), lambda q: q[0] <= -238.0)
osa_c = trasa(cela)
sdel = [0.0]
for k in range(1, len(osa_c)): sdel.append(sdel[-1] + math.dist(osa_c[k], osa_c[k-1]))
RT = 17.0
km = min(range(len(osa_c)), key=lambda k: abs(sdel[k] - sdel[-1] * 0.5))
T0 = osa_c[km]
kd = min(range(len(osa_c)), key=lambda k: abs(sdel[k] - (sdel[km] + RT)))
ku = min(range(len(osa_c)), key=lambda k: abs(sdel[k] - (sdel[km] - RT)))
yT = round(min(hy(*osa_c[ku]), hy(*T0) + 0.5) - 0.2, 2)
tp_osa = osa_c[:ku + 1]
to_osa = osa_c[kd:]
hd = osa_c[kd]; hv = (osa_c[min(kd + 1, len(osa_c) - 1)][0] - osa_c[kd - 1][0], osa_c[min(kd + 1, len(osa_c) - 1)][1] - osa_c[kd - 1][1])
hn = math.hypot(*hv); hv = (hv[0] / hn, hv[1] / hn)
print('tvrz: delka toku', round(sdel[-1]), 'm, rybnik', [round(v, 1) for v in T0], 'hladina', yT, 'hraz', [round(v, 1) for v in hd])
toky = [
 {"id": "lhota_potok", "popis": "pramen na svahu vychodnich kopcu -> rybnik Lhota (udolnice odtoku po terenu)", "sirka_m": 1.2, "hloubka_m": 0.35,
  "do": "rybnik_lhota", "osa_xzy": hladina(trasa(pr), hy(795, 895) - 0.2, 0.35)},
 {"id": "lhota_odtok", "popis": "vypust v hrazi na jihozapadnim brehu -> nahon a mlyn -> udolim do Bystrice", "sirka_m": 1.4, "hloubka_m": 0.4,
  "do": "potok", "osa_xzy": hladina(trasa(od), HL - 0.3, 0.4)},
 {"id": "tvrz_potok", "popis": "pramen v rohu mapy u tvrze (-155, -235) -> rybnik na rovince v udolnici", "sirka_m": 0.9, "hloubka_m": 0.3,
  "do": "rybnik_tvrz", "osa_xzy": hladina(tp_osa, hy(*tp_osa[0]) - 0.2, 0.3)},
 {"id": "tvrz_odtok", "popis": "z rybnika pres hraz dolinou k zapadnimu okraji mapy (vlastni povodi, rozvodi s Bystrici)", "sirka_m": 1.0, "hloubka_m": 0.35,
  "do": "okraj", "osa_xzy": hladina(to_osa, yT - 0.3, 0.35)},
]
for t in toky:
    o = t['osa_xzy']; print(t['id'], len(o), 'bodu', round(sum(math.dist(o[k][:2], o[k-1][:2]) for k in range(1, len(o)))), 'm, hladina', o[0][2], '->', o[-1][2], 'nejhlubsi zarez', round(max(hy(x, z) - y for x, z, y in o), 2))
# mlyn na odtoku: kde je spad od hladiny nahonu nejvic 3,5 m
od_o = toky[1]['osa_xzy']
mi = min(range(len(od_o)), key=lambda k: abs((HL - 0.3) - hy(od_o[k][0], od_o[k][1]) - 3.5))
print('mlyn', od_o[mi], 'teren', round(hy(od_o[mi][0], od_o[mi][1]), 2), 'spad', round(HL - 0.3 - hy(od_o[mi][0], od_o[mi][1]), 2))
json.dump({"toky": toky, "mlyn": od_o[mi], "tvrz_hladina": yT}, open('voda_sit.json', 'w'))
# zapis do pravidla/svet/voda.json (jediny zdroj): toky, rybnik u tvrze, mlyn
V['toky'] = toky
rt = V['rybnik_tvrz']
rt['stred'] = [round(T0[0], 1), round(T0[1], 1)]; rt['hladina_y'] = yT; rt['polomer_m'] = RT
rt['hraz'].update({"stred": [round(hd[0], 1), round(hd[1], 1)], "smer_osy": [round(-hv[1], 3), round(hv[0], 3)]})
m = V['mlyn']; na = od_o[mi]
k2 = mi; a2, b2 = od_o[max(0, k2 - 1)], od_o[min(len(od_o) - 1, k2 + 1)]
nx2, nz2 = -(b2[1] - a2[1]), b2[0] - a2[0]; n2 = math.hypot(nx2, nz2)
m['na_toku'] = na[:2]; m['stred'] = [round(na[0] + nx2 / n2 * 11.0, 1), round(na[1] + nz2 / n2 * 11.0, 1)]
m['spad_m'] = round(HL - 0.3 - hy(na[0], na[1]), 2)
import sys
if '--zapis' in sys.argv: json.dump(V, open('/home/user/tvrz-claude/pravidla/svet/voda.json', 'w'), ensure_ascii=False, indent=1)
print('zapsano do voda.json')
