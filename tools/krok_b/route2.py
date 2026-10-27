# Krok B trasy (radce 12:15): vozova <= 12,5 % (usek <= 30 m 15 %), odchylka <= 40 m od dnesni (u hostince bez
# omezeni), pevne body (brana, krizovatka, most, brod, napojeni), jinak uvoz do 3 m; oblouky R >= 15 m.
import json, math, heapq
import astar
from hladke import chaikin, resample, hz
K=astar.K
C=json.load(open('/home/user/tvrz-claude/pravidla/svet/cesty.json'))
VOZ={v['id']:v for v in C['vozove']}
H=[tuple(p) for p in VOZ['hlavni']['osa']]; O=[tuple(p) for p in VOZ['odbocka_ves']['osa']]
PES={p['id']:p for p in C['pesiny']}
LOM=[tuple(p) for p in PES['lom_brod_odbocka']['osa']]
def dist_to(line, x, z):
    b=1e9
    for (ax,az),(bx,bz) in zip(line[:-1],line[1:]):
        dx,dz=bx-ax,bz-az; L2=dx*dx+dz*dz or 1
        t=max(0,min(1,((x-ax)*dx+(z-az)*dz)/L2)); b=min(b,math.hypot(x-ax-dx*t,z-az-dz*t))
    return b
def route(a,b,ref,max_dev=40.0,volno=None,gmax=0.15,gok=0.125):
    sa,sb=astar.idx(*a),astar.idx(*b)
    nb=[(di,dj) for di in range(-3,4) for dj in range(-3,4) if (di,dj)!=(0,0) and math.gcd(abs(di),abs(dj))==1]
    devc={}
    def dev_ok(v):
        if v in devc: return devc[v]
        x,z=astar.pos(*v)
        ok = dist_to(ref,x,z)<=max_dev or (volno is not None and volno(x,z))
        devc[v]=ok; return ok
    g={sa:0.0}; prev={}; pq=[(0.0,sa)]
    while pq:
        f,u=heapq.heappop(pq)
        if u==sb: break
        if f-math.hypot(u[0]-sb[0],u[1]-sb[1])*K>g[u]+1e-6: continue
        for di,dj in nb:
            v=(u[0]+di,u[1]+dj)
            if not (0<=v[0]<astar.nx and 0<=v[1]<astar.nz) or not dev_ok(v): continue
            L=math.hypot(di,dj)*K; gr=abs(astar.h(*v)-astar.h(*u))/L
            if gr>gmax: continue
            c=L*(1.0+4.0*max(0.0,gr-0.06)+(25.0 if gr>gok else 0.0))
            ng=g[u]+c
            if ng<g.get(v,1e18):
                g[v]=ng; prev[v]=u; heapq.heappush(pq,(ng+math.hypot(v[0]-sb[0],v[1]-sb[1])*K,v))
    if sb not in prev: return None
    p=[sb]
    while p[-1]!=sa: p.append(prev[p[-1]])
    return [astar.pos(*q) for q in reversed(p)]
def profil(p, gok=0.125, gmax=0.15, kratky=30.0, uvoz=3.0):
    # podelny profil s uvozem do 3 m (jako svet.gd _cesty_profil): mezi body po 6 m; vraci (nejprudsi usek, delka nad gok, max zarez)
    acc=[0.0]
    for a,b in zip(p[:-1],p[1:]): acc.append(acc[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
    t=[hz(*q) for q in p]
    y=list(t)
    for _ in range(60):          # vyhlazeni s mezi: sklon <= gok kde to jde v ramci uvozu
        for i in range(1,len(p)):
            d=acc[i]-acc[i-1] or 1
            y[i]=max(min(y[i], y[i-1]+gok*d), y[i-1]-gok*d)
        for i in range(len(p)-2,-1,-1):
            d=acc[i+1]-acc[i] or 1
            y[i]=max(min(y[i], y[i+1]+gok*d), y[i+1]-gok*d)
        y=[max(min(y[i],t[i]+uvoz),t[i]-uvoz) for i in range(len(p))]
    zarez=max(abs(y[i]-t[i]) for i in range(len(p)))
    nad=0.0; run=0.0; maxrun=0.0; mx=0.0
    for i in range(1,len(p)):
        d=acc[i]-acc[i-1] or 1; gr=abs(y[i]-y[i-1])/d; mx=max(mx,gr)
        if gr>gok+1e-3: run+=d; nad+=d; maxrun=max(maxrun,run)
        else: run=0
    return mx,nad,maxrun,zarez
def radius_min(p):
    rm=1e9
    for i in range(1,len(p)-1):
        a,b,c=p[i-1],p[i],p[i+1]
        ab=math.hypot(b[0]-a[0],b[1]-a[1]); bc=math.hypot(c[0]-b[0],c[1]-b[1]); ca=math.hypot(a[0]-c[0],a[1]-c[1])
        cr=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
        if cr>1e-6: rm=min(rm, ab*bc*ca/(2*cr))
    return rm
def hladka(raw, pevne=()):
    s=resample(chaikin(raw,4),6.0)
    return s
if __name__=='__main__':
    import sys


DIRS=[(1,0),(2,1),(1,1),(1,2),(0,1),(-1,2),(-1,1),(-2,1),(-1,0),(-2,-1),(-1,-1),(-1,-2),(0,-1),(1,-2),(1,-1),(2,-1)]
def route_dir(a,b,ref,max_dev=40.0,volno=None,gmax=0.30,gok=0.125,smer0=None):
    # A* se stavem (bunka, smer): v kazdem kroku zatocit nejvys o 1 z 16 smeru (22,5 st.) -> oblouky R ~ 13-28 m
    sa,sb=astar.idx(*a),astar.idx(*b)
    devc={}
    def dev_ok(v):
        if v in devc: return devc[v]
        x,z=astar.pos(*v)
        ok = dist_to(ref,x,z)<=max_dev or (volno is not None and volno(x,z))
        devc[v]=ok; return ok
    pq=[]; g={}; prev={}
    for d in range(16):
        if smer0 is not None and min(abs(d-smer0),16-abs(d-smer0))>1: continue
        g[(sa,d)]=0.0; heapq.heappush(pq,(0.0,sa,d))
    cil=None
    while pq:
        f,u,d=heapq.heappop(pq)
        if u==sb: cil=(u,d); break
        if f-math.hypot(u[0]-sb[0],u[1]-sb[1])*K>g[(u,d)]+1e-6: continue
        for dd in (-1,0,1):
            nd=(d+dd)%16; di,dj=DIRS[nd]
            v=(u[0]+di,u[1]+dj)
            if not (0<=v[0]<astar.nx and 0<=v[1]<astar.nz) or not dev_ok(v): continue
            L=math.hypot(di,dj)*K; gr=abs(astar.h(*v)-astar.h(*u))/L
            if gr>gmax: continue
            c=L*(1.0+4.0*max(0.0,gr-0.06)+(4.0 if gr>gok else 0.0)+(12.0 if gr>0.15 else 0.0)+(0.05 if dd else 0.0))   # strmeji = uvoz (do 3 m, overi profil) - levnejsi nez smycka (radce 12:15: uvoz pred prelozenim)
            ng=g[(u,d)]+c
            if ng<g.get((v,nd),1e18):
                g[(v,nd)]=ng; prev[(v,nd)]=(u,d); heapq.heappush(pq,(ng+math.hypot(v[0]-sb[0],v[1]-sb[1])*K,v,nd))
    if cil is None: return None
    p=[cil]
    while p[-1] in prev: p.append(prev[p[-1]])
    return [astar.pos(*q[0]) for q in reversed(p)]
