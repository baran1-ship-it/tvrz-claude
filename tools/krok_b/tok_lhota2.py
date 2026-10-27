import json, math
exec(open('tok_tvrz.py').read().split("C=json.load")[0])
c0=(525.08,879.45)
vede=bytearray(len(DIR))
# bunky, jejichz odtok projde rybnikem (do 25 m od stredu)
pres={}
def projde(c):
    if c in pres: return pres[c]
    path=[]; q=c; r=False
    while q>=0 and q not in pres:
        x,z=pos(q)
        if math.hypot(x-c0[0],z-c0[1])<25: r=True; break
        path.append(q); q=DIR[q]
    if q in pres: r=pres[q]
    for p in path: pres[p]=r
    return r
best=None
for c in range(len(DIR)):
    x,z=pos(c)
    if x<540 or ACC[c]!=1: continue
    if projde(c):
        # delka cesty k rybniku a prevyseni
        n=0;q=c
        while math.hypot(pos(q)[0]-c0[0],pos(q)[1]-c0[1])>=25: q=DIR[q]; n+=1
        sc=(n*K, H[c])
        if best is None or sc[0]>best[0][0]: best=(sc,c)
print('nejdelsi pritok do Lhoty z vychodu', best[0], 'pramen', pos(best[1]))
q=best[1]; pts=[]
while math.hypot(pos(q)[0]-c0[0],pos(q)[1]-c0[1])>=25: pts.append(q); q=DIR[q]
for p in pts[::10]: print('  ', tuple(round(v) for v in pos(p)), round(H[p],1), round(ACC[p]*K*K/1e4,2))
