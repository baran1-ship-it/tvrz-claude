import json, math
import astar
from route2 import route_dir, profil, radius_min, dist_to, H, O, LOM
from hladke import chaikin, resample, hz
T=json.load(open('trasy2.json'))
HOST=(15.0,838.0); HOST_STARY=(-71.0,881.0)
CROSS=(12.891097684473024, 400.54114664029584)
konec=min(H,key=lambda p:abs(p[1]-1335))
def hlad(seg): return resample(chaikin([tuple(p) for p in seg],3),6.0)
def profil_body(p, gok=0.125, uvoz=3.0):
    acc=[0.0]
    for a,b in zip(p[:-1],p[1:]): acc.append(acc[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
    t=[hz(*q) for q in p]; y=list(t)
    for _ in range(60):
        for i in range(1,len(p)):
            d=acc[i]-acc[i-1] or 1; y[i]=max(min(y[i],y[i-1]+gok*d),y[i-1]-gok*d)
        for i in range(len(p)-2,-1,-1):
            d=acc[i+1]-acc[i] or 1; y[i]=max(min(y[i],y[i+1]+gok*d),y[i+1]-gok*d)
        y=[max(min(y[i],t[i]+uvoz),t[i]-uvoz) for i in range(len(p))]
    return [p[i] for i in range(1,len(p)) if abs(y[i]-y[i-1])/(acc[i]-acc[i-1] or 1)>0.15+1e-3]
sirsi=[]   # mista, kde v 40 m nejde ani uvoz -> prelozit dal (radce 12:15)
def volno(x,z):
    if min(math.hypot(x-HOST[0],z-HOST[1]), math.hypot(x-HOST_STARY[0],z-HOST_STARY[1]))<130: return True
    return any(math.hypot(x-s[0],z-s[1])<70 for s in sirsi)
for kolo in range(4):
    p2=route_dir(CROSS,konec,H,volno=volno)
    s=hlad(p2); spatne=profil_body(s)
    print('kolo',kolo,'nad 15 %% po uvozu: %d bodu'%len(spatne), [tuple(round(v) for v in q) for q in spatne[:5]])
    if not spatne: break
    sirsi += spatne[::3]
json.dump({'p2':p2,'sirsi':sirsi},open('p2.json','w'))
