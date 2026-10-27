import sys, json, math, time, array
sys.path.insert(0, '/home/user/tvrz-claude/blender')
import fort
K=5.0; X0,X1,Z0,Z1=-240.0,890.0,-240.0,1340.0
nx=int((X1-X0)/K)+1; nz=int((Z1-Z0)/K)+1
t=time.time()
h=array.array('f')
for j in range(nz):
    z=Z0+j*K
    for i in range(nx):
        h.append(fort.land(X0+i*K, z, flat=False, pads=False))
json.dump({'K':K,'X0':X0,'Z0':Z0,'nx':nx,'nz':nz,'h':list(h)}, open(sys.argv[1],'w'))
print('hotovo', nx, nz, time.time()-t)
