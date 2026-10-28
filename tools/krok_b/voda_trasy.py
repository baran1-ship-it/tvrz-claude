import astar, math, json, heapq
L=json.load(open('/home/user/tvrz-claude/pravidla/svet/lokace.json'))
domy=[tuple(e['novy_stred']) for e in L['ves']['usedlosti']]
def zakaz(x,z): return any(math.hypot(x-d[0],z-d[1])<26 for d in domy)
# konecne osy cest tak, jak je postavila hra (build/protokol_stavby.json cesty, po posunu vsi): tok nesmi vest po ceste
# ani podel ni (28. 10.: lhota_odtok tekl 15 m ulici vsi) - bunky do ODSTUP od osy cesty jsou drahe (prechod kolmo jde,
# souběh ne); kazde krizeni pak potrebuje zaznam prechodu v cesty.json
try:
    _CESTY=json.load(open('/home/user/tvrz-claude/build/protokol_stavby.json'))['cesty']
except (OSError, ValueError, KeyError):
    _CESTY=[]
ODSTUP=json.load(open('/home/user/tvrz-claude/pravidla/pravidla_sveta.json'))['pasma']['test']['tok_od_cesty_m']+3.0
_CM={}
for _c in _CESTY:
    for _p in _c:
        _CM.setdefault((int(_p[0]//8),int(_p[1]//8)),[]).append(_p)
def u_cesty(x,z):
    for di in (-1,0,1):
        for dj in (-1,0,1):
            for p in _CM.get((int(x//8)+di,int(z//8)+dj),[]):
                if math.hypot(x-p[0],z-p[1])<ODSTUP: return True
    return False
def potok_route(a, b, max_up=0.3):
    # odtok / pritok: voda jen klesa (nejvys max_up m vzestup terenu po ceste = zarez), cena = delka + zarez
    K=astar.K; sa=astar.idx(*a); sb=astar.idx(*b)
    nb=[(di,dj) for di in range(-2,3) for dj in range(-2,3) if (di,dj)!=(0,0) and math.gcd(abs(di),abs(dj))==1]
    best={ (sa, round(astar.h(*sa),1)) :0}
    g={sa:0.0}; lvl={sa:astar.h(*sa)}; prev={}
    pq=[(0.0,sa)]
    while pq:
        f,u=heapq.heappop(pq)
        if u==sb: break
        for di,dj in nb:
            v=(u[0]+di,u[1]+dj)
            x,z=astar.pos(*v)
            if zakaz(x,z): continue
            hv=astar.h(*v); hl=min(lvl[u], hv)          # hladina nikdy nestoupa
            zarez=max(0.0, hv-lvl[u])
            if zarez>3.0: continue
            Lk=math.hypot(di,dj)*K
            ng=g[u]+Lk*(1+0.5*zarez)*(6.0 if u_cesty(x,z) else 1.0)
            if ng<g.get(v,1e18):
                g[v]=ng; prev[v]=u; lvl[v]=hl
                heapq.heappush(pq,(ng+math.hypot(v[0]-sb[0],v[1]-sb[1])*K,v))
    if sb not in prev: return None
    p=[sb]
    while p[-1]!=sa: p.append(prev[p[-1]])
    p=list(reversed(p)); return [astar.pos(*q)+(round(lvl[q],2),round(astar.h(*q),2)) for q in p]
odtok=potok_route((498,857),(241,986))
pritok=potok_route((700,960),(549,900))
for nm,r in (("odtok",odtok),("pritok",pritok)):
    if r is None: print(nm,'NENI'); continue
    print(nm, len(r), 'bodu, start hladina', r[0][2], 'konec', r[-1][2], 'max zarez', round(max(q[3]-q[2] for q in r),2))
json.dump({'odtok':odtok,'pritok':pritok},open('voda_trasy.json','w'))
