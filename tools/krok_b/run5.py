import json, math
from route2 import route_dir, profil, radius_min, dist_to, H, O, LOM
from hladke import chaikin, resample
P2=json.load(open('p2.json'))
HOST=(15.0,838.0); HOST_STARY=(-71.0,881.0); sirsi=P2['sirsi']
def volno(x,z):
    if min(math.hypot(x-HOST[0],z-HOST[1]), math.hypot(x-HOST_STARY[0],z-HOST_STARY[1]))<130: return True
    return any(math.hypot(x-s[0],z-s[1])<70 for s in sirsi)
CROSS=(12.891097684473024, 400.54114664029584); MOST_Z=(221.94,592.62); MOST_V=(244.25,605.0)
konec=min(H,key=lambda p:abs(p[1]-1335)); i_konec=H.index(konec)
def hlad(seg): return resample(chaikin([tuple(p) for p in seg],3),6.0)
def spoj(*segs):
    out=[]
    for s in segs: out += s if not out else s[1:]
    return out
def R3(a,b,c):
    ab=math.hypot(b[0]-a[0],b[1]-a[1]); bc=math.hypot(c[0]-b[0],c[1]-b[1]); ca=math.hypot(a[0]-c[0],a[1]-c[1])
    cr=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])); return 1e9 if cr<1e-9 else ab*bc*ca/(2*cr)
def oblouky(p, pevne, Rmin=15.0):
    p=[list(q) for q in p]
    fix={0,len(p)-1}|{min(range(len(p)),key=lambda k:math.hypot(p[k][0]-f[0],p[k][1]-f[1])) for f in pevne}
    for _ in range(300):
        zmena=False
        for i in range(1,len(p)-1):
            if i in fix: continue
            if R3(p[i-1],p[i],p[i+1])<Rmin:
                for j in (i-1,i,i+1):
                    if j in fix or j<=0 or j>=len(p)-1: continue
                    p[j]=[0.5*p[j][0]+0.25*(p[j-1][0]+p[j+1][0]), 0.5*p[j][1]+0.25*(p[j-1][1]+p[j+1][1])]
                zmena=True
        if not zmena: break
    return [tuple(q) for q in p]
p1=route_dir((0.0,71.06),CROSS,H,smer0=4,volno=lambda x,z: any(math.hypot(x-s[0],z-s[1])<70 for s in sirsi))
o1=route_dir(CROSS,MOST_Z,O); o2=route_dir(MOST_V,(372.0,744.0),O,smer0=2,volno=lambda x,z: math.hypot(x-372.0,z-744.0)<90)   # napojeni na novy vjezd vsi
hl=spoj(hlad(p1),hlad(P2['p2']))
od=spoj(hlad(o1),[MOST_Z,MOST_V],hlad(o2))
napoj=min(od,key=lambda p:math.hypot(p[0]-300,p[1]-673))
l1=route_dir((140.0,940.0),(210.0,853.0),LOM)
from route2 import DIRS
dx,dz=l1[-1][0]-l1[-2][0],l1[-1][1]-l1[-2][1]
s0=min(range(16),key=lambda d:-(DIRS[d][0]*dx+DIRS[d][1]*dz)/math.hypot(*DIRS[d]))
l2=route_dir((210.0,853.0),napoj,LOM,smer0=s0)
lom=spoj(hlad(l1),hlad(l2))
out={}
for nm,p,pevne,ref in (('hlavni',hl,[(0.0,71.06)],H),('odbocka',od,[CROSS,MOST_Z,MOST_V,(372.0,744.0)],O),('lom',lom,[(140.0,940.0),napoj],LOM)):
    q=oblouky(p,pevne)
    mx,nad,maxrun,zarez=profil(q)
    dev=max(dist_to(ref,*r) for r in q if not (nm=='hlavni' and volno(*r)))
    if nm=='lom': print('  brod: nejblizsi bod osy %.1f m od (210, 853)'%min(math.hypot(r[0]-210,r[1]-853) for r in q))
    print(nm,'%d bodu, max %.1f %%, nad 12,5 %%: %.0f m (usek %.0f), uvoz %.1f, R min %.0f, odch %.0f'%(len(q),mx*100,nad,maxrun,zarez,radius_min(q),dev))
    out[nm]=q
kriz=min(out['hlavni'],key=lambda p:math.hypot(p[0]-CROSS[0],p[1]-CROSS[1]))
print('krizovatka posunuta o %.1f m'%math.hypot(kriz[0]-CROSS[0],kriz[1]-CROSS[1]))
out['odbocka'][0]=kriz
out['krizovatka']=kriz
out['hlavni']=out['hlavni']+[tuple(x) for x in H[i_konec+1:]]
out['napojeni_lomu']=napoj
json.dump(out,open('trasy_final.json','w'))
