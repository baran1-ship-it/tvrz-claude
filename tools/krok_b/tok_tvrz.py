import json, math
D = json.load(open("vysky.json")); T = json.load(open("tok.json"))
K, X0, Z0, nx, nz, H = D['K'], D['X0'], D['Z0'], D['nx'], D['nz'], D['h']
DIR, ACC, F = T['DIR'], T['ACC'], T['F']
pos = lambda c: (X0 + (c % nx) * K, Z0 + (c // nx) * K)
idx = lambda x, z: int(round((z - Z0) / K)) * nx + int(round((x - X0) / K))
up = {}
for q in range(len(DIR)):
    if DIR[q] >= 0: up.setdefault(DIR[q], []).append(q)
def dolu(c):
    p=[c]
    while DIR[p[-1]]>=0: p.append(DIR[p[-1]])
    return p
def nahoru(c):
    p=[c]
    while up.get(p[-1]): p.append(max(up[p[-1]], key=lambda q: ACC[q]))
    return p
C=json.load(open('/home/user/tvrz-claude/pravidla/svet/cesty.json'))
def dcesta(x,z):
    return min(math.hypot(x-p[0],z-p[1]) for c in C['vozove'] for p in c['osa'][::2])
for nm,(x,z) in (("zapad",(20,150)),("sever",(320,30))):
    c=idx(x,z); pd=dolu(c); pu=nahoru(c)
    cela=list(reversed(pu))+pd[1:]
    print(nm, 'delka', len(cela)*K, 'pramen', pos(cela[0]), round(H[cela[0]],1), 'vystup', pos(cela[-1]), round(H[cela[-1]],1))
    for q in cela[::8]:
        x2,z2=pos(q)
        # sirka roviny napric: rozdil vysky v okruhu 15 m
        hs=[H[idx(x2+dx,z2+dz)] for dx in (-15,0,15) for dz in (-15,0,15) if 0<=idx(x2+dx,z2+dz)<len(H)]
        print('   ', (round(x2),round(z2)), 'y',round(H[q],1), 'povodi ha', round(ACC[q]*K*K/1e4,2), 'rozpeti30m', round(max(hs)-min(hs),1), 'od tvrze', round(math.hypot(x2,z2)), 'od cesty', round(dcesta(x2,z2)))
