"""Prototyp: kotle (tunika ke kolenům s rukávy) ušitá ze střihových dílů kolem těla (Blender cloth + sewing springs)."""
import bpy, bmesh, math, sys
from mathutils import Vector
BD="/tmp/postavy_q/src/quaternius/base_characters/Base Characters/Godot - UE"
OUT=sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f"{BD}/Superhero_Male_FullBody.gltf")
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name.startswith("Icosphere"): bpy.data.objects.remove(o)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith("SuperHero"))
def bz(b): return arm.matrix_world@arm.data.bones[b].head_local
z_sh=bz("upperarm_l").z; z_neck=bz("neck_01").z; z_knee=bz("calf_l").z; x_wr=bz("hand_l").x
yc=0.03
# --- obrys poloviny dílu (x>=0) v rovině XZ: krk -> rameno/rukáv nahoře -> manžeta -> rukáv dole -> podpaží -> bok -> lem
z_hem=z_knee+0.06
neck_w=0.085; cuff_x=x_wr-0.04
def inside(x,z):
    ax=abs(x)
    if z>z_neck+0.02 or z<z_hem: return False
    if ax<neck_w and z>z_neck-0.06: return False                 # výstřih (předek i záda stejně – prototyp)
    # rukáv: pás kolem paže
    if ax>0.16 and z>z_sh-0.14:
        if ax>cuff_x: return False
        t=(ax-0.16)/(cuff_x-0.16)
        top=z_sh+0.085-0.03*t; bot=z_sh-0.13+0.07*t
        return bot<z<top
    # trup: šířka roste k lemu
    t=(z_sh-0.13-z)/(z_sh-0.13-z_hem)
    if z>z_sh-0.13:                                               # ramena: šikmo od krku
        top=z_neck+0.02-(ax-neck_w)*0.35
        return z<top
    half=0.2+0.14*max(0.0,t)**1.5
    return ax<half

YA=0.07
def wrap(x,z,y):
    sg=-1.0 if y<yc else 1.0
    ax=abs(x)
    if ax>0.16 and z>z_sh-0.14:                     # rukáv: půlka trubky kolem paže
        t=min(1.0,(ax-0.16)/(cuff_x-0.16))
        top=z_sh+0.085-0.03*t; bot=z_sh-0.13+0.07*t
        zc=(top+bot)/2; r=(top-bot)/2
        u=max(-1.0,min(1.0,(z-zc)/r))
        return (x, YA+sg*r*math.sqrt(max(0.0,1-u*u)), z)
    if z>z_sh-0.13:
        top=z_neck+0.02-(max(ax,neck_w)-neck_w)*0.35
        hw=0.2
        ds=math.sqrt(max(0.0,min(1.0,(top-z)/0.07)))
    else:
        t=(z_sh-0.13-z)/(z_sh-0.13-z_hem)
        hw=0.2+0.14*max(0.0,t)**1.5; ds=1.0
    d=(0.185+0.05*max(0.0,(z_sh-0.4-z))/0.5)*ds
    u=max(-1.0,min(1.0,x/(hw+0.001)))
    return (x, yc+sg*d*math.sqrt(max(0.0,1-u*u))*1.0, z)
step=0.014
def panel(name,y):
    bm=bmesh.new(); V={}
    nx=int(0.8/step); zs=[z_hem+i*step for i in range(int((z_neck+0.03-z_hem)/step)+1)]
    xs=[(i-nx)*step for i in range(2*nx+1)]
    for iz,z in enumerate(zs):
        for ix,x in enumerate(xs):
            V[(ix,iz)]=None
    for iz in range(len(zs)-1):
        for ix in range(len(xs)-1):
            cx=(xs[ix]+xs[ix+1])/2; cz=(zs[iz]+zs[iz+1])/2
            if not inside(cx,cz): continue
            q=[]
            for k in [(ix,iz),(ix+1,iz),(ix+1,iz+1),(ix,iz+1)]:
                if V[k] is None: V[k]=bm.verts.new(wrap(xs[k[0]],zs[k[1]],y))
                q.append(V[k])
            bm.faces.new(q)
    return bm,V,xs,zs
bmF,VF,xs,zs=panel("F",yc-0.19)
bmB,VB,_,_=panel("B",yc+0.19)
# spoj do jednoho meshe + šicí hrany mezi okrajovými vrcholy stejné polohy (krom krku, lemu a manžet)
bm=bmesh.new(); mF={}; mB={}
for k,v in VF.items():
    if v is not None: mF[k]=bm.verts.new(v.co)
for k,v in VB.items():
    if v is not None: mB[k]=bm.verts.new(v.co)
for src,m in [(bmF,mF),(bmB,mB)]:
    inv={v:k for k,v in (VF if src is bmF else VB).items() if v is not None}
    for f in src.faces: bm.faces.new([m[inv[v]] for v in f.verts])
bm.verts.ensure_lookup_table()
edge_b=set()
for e in bm.edges:
    if e.is_boundary: edge_b.update(e.verts)
sew=0
for k,vf in mF.items():
    vb=mB.get(k)
    if vb is None or vf not in edge_b or vb not in edge_b: continue
    x,z=vf.co.x,vf.co.z
    if z<z_hem+0.005 or abs(x)>cuff_x-step*1.1 or (abs(x)<neck_w+step and z>z_neck-0.07): continue
    bm.edges.new((vf,vb)); sew+=1
print("SIT sevu",sew,"vrcholu",len(bm.verts))
me=bpy.data.meshes.new("kotle"); bm.to_mesh(me); ob=bpy.data.objects.new("kotle",me); bpy.context.collection.objects.link(ob)
vg=ob.vertex_groups.new(name="pas")
z_pas=z_sh-0.48
for v in me.vertices:
    w=max(0.0,1.0-abs(v.co.z-z_pas)/0.05)
    if w>0: vg.add([v.index],w,'REPLACE')
sc=bpy.context.scene
# --- bez simulace: šicí hrany sloučit (díly už leží u sebe), sklady a nabrání v pase, odstup od těla
bm=bmesh.new(); bm.from_mesh(me)
for e in [e for e in bm.edges if not e.link_faces]:
    a_,b_=e.verts; m=(a_.co+b_.co)/2; a_.co=m; b_.co=m
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.009)
bv=[v for v in bm.verts if not v.is_boundary]
for _ in range(12):
    bmesh.ops.smooth_vert(bm,verts=bv,factor=0.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
z_pas=z_sh-0.48
for v in bm.verts:
    x,y,z=v.co
    if abs(x)>0.17 and z>z_sh-0.14: continue       # rukávy bez skladů
    dx,dy=x,y-yc; r=math.hypot(dx,dy)+1e-6; ang=math.atan2(dy,dx)
    if z<z_pas:                                     # sklady k lemu (víc dole), 9 skladů po obvodu
        t=min(1.0,(z_pas-z)/(z_pas-z_hem))
        r+=0.022*t*math.sin(ang*9.0)+0.03*t
    else:                                           # nad pasem volně nabrané (halenka přes opasek)
        t=max(0.0,1.0-(z-z_pas)/0.12)
        r+=0.012*t*math.sin(ang*12.0)
    v.co.x=r*math.cos(ang); v.co.y=yc+r*math.sin(ang)
    bw=max(0.0,1.0-abs(z-z_pas)/0.035)               # opasek stáhne látku k pasu
    if bw>0:
        v.co.x*=1.0-0.12*bw; v.co.y=yc+(v.co.y-yc)*(1.0-0.12*bw)
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth=True
ss=ob.modifiers.new("Sub",'SUBSURF'); ss.levels=1; ss.render_levels=1
sw=ob.modifiers.new("Odstup",'SHRINKWRAP'); sw.target=body; sw.wrap_method='NEAREST_SURFACEPOINT'
sw.wrap_mode='OUTSIDE'; sw.offset=0.012
sm=ob.modifiers.new("Tl",'SOLIDIFY'); sm.thickness=0.004; sm.offset=1
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT+".blend")
# náhled
sc.render.engine='CYCLES'; sc.cycles.samples=12; sc.render.resolution_x=900; sc.render.resolution_y=900
w=bpy.data.worlds.new('w'); sc.world=w; w.color=(0.8,0.8,0.8)
sun=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN')); sun.data.energy=3; sun.rotation_euler=(0.8,0.2,0.3); sc.collection.objects.link(sun)
mat=bpy.data.materials.new("vlna"); mat.diffuse_color=(0.25,0.18,0.12,1); mat.use_nodes=True
mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value=(0.25,0.18,0.12,1); ob.data.materials.append(mat)
cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera=cam
for nm,loc in [("pred",(0.0,-3.2,1.1)),("zad",(0.0,3.2,1.1)),("bok",(3.2,0.0,1.1))]:
    cam.location=loc; d=Vector((0,0.03,1.05))-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"{OUT}_{nm}.png"; bpy.ops.render.render(write_still=True)
