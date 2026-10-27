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
# toky obchazeji stavby (CLAUDE.md poradi teren -> cesty -> budovy -> voda; 27. 10.: lhota_odtok tekl skrz dum 3 vsi):
# bod osy blize nez polomer stavby + pul sirky + breh (pasma voda breh_m) se odsune od stredu stavby na tu vzdalenost
LOK = json.load(open('/home/user/tvrz-claude/pravidla/svet/lokace.json'))
BREH = json.load(open('/home/user/tvrz-claude/pravidla/pravidla_sveta.json'))['pasma']['voda']['breh_m']
STAVBY_O = [(u['novy_stred'], math.hypot(u['L'], u['W']) / 2) for u in LOK['ves']['usedlosti']]
STAVBY_O += [(s_['stred'], s_['rovina_r_m']) for s_ in LOK['stavby']]
def obejdi(osa, pul):
    """Tok kolem stavby po oblouku: osa zhustena po 1 m, body v kruhu (polomer stavby + pul sirky + breh) se posunou
    na kruh - vsechny na stejnou stranu (ta, na kterou tok do kruhu vstoupil), pak vyhlazeni a zpet po 6 m."""
    p = [osa[0]]
    for a_, b_ in zip(osa, osa[1:]):
        n = max(1, int(math.dist(a_, b_)))
        p += [(a_[0] + (b_[0] - a_[0]) * k / n, a_[1] + (b_[1] - a_[1]) * k / n) for k in range(1, n + 1)]
    for (cx, cz), r in STAVBY_O:
        R = r + pul + BREH
        uvnitr = [i for i, q in enumerate(p) if math.hypot(q[0] - cx, q[1] - cz) < R]
        if not uvnitr:
            continue
        i0 = max(0, uvnitr[0] - 1)
        i1 = min(len(p) - 1, uvnitr[-1] + 1)
        dx, dz = p[i1][0] - p[i0][0], p[i1][1] - p[i0][1]
        dn = math.hypot(dx, dz) or 1.0
        dx, dz = dx / dn, dz / dn
        # strana: kde lezi stred toku (vstup a vystup) vuci stredu stavby; kdyz primo pres stred, vlevo
        mx, mz = (p[i0][0] + p[i1][0]) / 2 - cx, (p[i0][1] + p[i1][1]) / 2 - cz
        side = 1.0 if (-dz * mx + dx * mz) >= 0 else -1.0
        for i in uvnitr:
            vx, vz = p[i][0] - cx, p[i][1] - cz
            t = vx * dx + vz * dz                                    # poloha podel smeru toku
            h = math.sqrt(max(R * R - t * t, 0.0))
            p[i] = (cx + dx * t + (-dz) * side * h, cz + dz * t + dx * side * h)
    for _ in range(2):
        n2 = [p[0]]
        for a_, b_ in zip(p[:-1], p[1:]):
            n2 += [(0.75 * a_[0] + 0.25 * b_[0], 0.75 * a_[1] + 0.25 * b_[1]), (0.25 * a_[0] + 0.75 * b_[0], 0.25 * a_[1] + 0.75 * b_[1])]
        n2.append(p[-1])
        p = n2
    out = [p[0]]
    for q in p[1:]:
        if math.dist(q, out[-1]) >= 6.0:
            out.append(q)
    if out[-1] != p[-1]:
        out.append(p[-1])
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
  "do": "rybnik_lhota", "osa_xzy": hladina(obejdi(trasa(pr), 0.6), hy(795, 895) - 0.2, 0.35)},
 {"id": "lhota_odtok", "popis": "vypust v hrazi na jihozapadnim brehu -> nahon a mlyn -> udolim do Bystrice", "sirka_m": 1.4, "hloubka_m": 0.4,
  "do": "potok", "osa_xzy": hladina(obejdi(trasa(od), 0.7), HL - 0.3, 0.4)},
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
if '--zapis' in sys.argv:
    json.dump(V, open('/home/user/tvrz-claude/pravidla/svet/voda.json', 'w'), ensure_ascii=False, indent=1)
    print('zapsano do voda.json')
