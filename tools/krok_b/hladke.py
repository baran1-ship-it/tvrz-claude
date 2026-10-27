import json, math, astar
def hz(x,z):
    fx=(x-astar.X0)/astar.K; fz=(z-astar.Z0)/astar.K; i=int(fx); j=int(fz); tx=fx-i; tz=fz-j
    a,b,c,d=astar.h(i,j),astar.h(i+1,j),astar.h(i,j+1),astar.h(i+1,j+1)
    return (a*(1-tx)+b*tx)*(1-tz)+(c*(1-tx)+d*tx)*tz
def chaikin(p,n=3):
    for _ in range(n):
        q=[p[0]]
        for a,b in zip(p[:-1],p[1:]):
            q+= [(0.75*a[0]+0.25*b[0],0.75*a[1]+0.25*b[1]),(0.25*a[0]+0.75*b[0],0.25*a[1]+0.75*b[1])]
        q.append(p[-1]); p=q
    return p
def resample(p,step=6.0):
    out=[p[0]]; acc=0
    for a,b in zip(p[:-1],p[1:]):
        L=math.hypot(b[0]-a[0],b[1]-a[1]); t=0
        while acc+L-t>=step:
            t+=step-acc; acc=0
            out.append((a[0]+(b[0]-a[0])*t/L, a[1]+(b[1]-a[1])*t/L))
        acc+=L-t
    out.append(p[-1]); return out
def grade(p, base=12.0):
    # sklon po 12 m po hladke ose (jako svet.gd log)
    acc=[0]
    for a,b in zip(p[:-1],p[1:]): acc.append(acc[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
    mx=0; sp=0; kde=None
    for i in range(len(p)):
        j=i
        while j<len(p)-1 and acc[j]-acc[i]<base: j+=1
        if acc[j]-acc[i]<1: continue
        g=abs(hz(*p[j])-hz(*p[i]))/(acc[j]-acc[i])
        if g>mx: mx=g; kde=p[i]
        if g>0.125: sp+=acc[min(i+1,len(p)-1)]-acc[i]
    return mx, sp, kde
if __name__=='__main__':
  T=json.load(open('trasy1.json'))
  out={}
  for k,p in T.items():
    s=resample(chaikin([tuple(x) for x in p],4),6.0)
    mx,sp,kde=grade(s)
    print(k, len(s),mx,sp)
    out[k]=[[round(x,2),round(z,2)] for x,z in s]
  json.dump(out,open('trasy_hladke.json','w'))
