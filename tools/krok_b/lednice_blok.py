"""Lednice mlyna jako plny kamenny blok (Misa 12. 11.: „koryto, ktere jde od mlyna do potoka, ma jen jednu stranu jako
ohnuty papir, neni to blok kamene“). Rozbor 12. 11. (rezy kolmo k ose lednice, Mlyn_Lednice-col modelu mlyn.glb): v
kazdem rezu jen vnitrni lic steny (bok osy +-sirka/2) a horni rimsa sirky ~0,4 m; vnejsi lic, cela a zaklad chybi -
kde je teren nize nez rimsa, je stena videt zvenku jako list. Zaznam: kazda stena lednice = hranol od vnitrniho lice
(sirka/2) k vnejsimu (sirka/2 + tloustka rimsy zmerena z modelu), shora tesne pod rimsou modelu, dole dno - zaklad_m;
cela na obou koncich. Lomovy kamen jako v modelu (material M_Kamen modelu prirazuje hra).
Vstup: modely/mlyn/mlyn.glb, tools/krok_b/mlyn_voda.json (osa lednice), pravidla/svet/voda.json mlyn.dil.lednice_blok.
Vystup: modely/mlyn/lednice_blok.glb (soustava dilu mlyna jako mlyn.glb).
  /opt/bl/bin/python -I tools/krok_b/lednice_blok.py"""
import json
import math
import os
import sys

import bpy  # noqa: I001 (bpy pred bmesh)
import bmesh

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V = json.load(open(os.path.join(ROOT, "pravidla", "svet", "voda.json")))["mlyn"]["dil"]["lednice_blok"]
U = json.load(open(os.path.join(ROOT, "tools", "krok_b", "mlyn_voda.json")))["lednice"]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "modely", "mlyn", "mlyn.glb"))
o = bpy.data.objects[V["sit_modelu"]]
bm = bmesh.new()
bm.from_mesh(o.data)
bm.transform(o.matrix_world)
H = [((e.verts[0].co.x, e.verts[0].co.z, -e.verts[0].co.y), (e.verts[1].co.x, e.verts[1].co.z, -e.verts[1].co.y)) for e in bm.edges]
B = U["body"]
pul = U["sirka"] / 2.0
dosah = pul + float(V["hledat_rimsu_m"])


def rez(i):
    """Rez kolmo k ose v bode i: (rimsa vlevo, rimsa vpravo, dno, sirka rimsy vlevo, vpravo) z hran modelu."""
    gx, _, gz = B[i]
    a, b = B[max(i - 1, 0)], B[min(i + 1, len(B) - 1)]
    dx, dz = b[0] - a[0], b[2] - a[2]
    L = math.hypot(dx, dz)
    dx, dz = dx / L, dz / L
    body = []
    for p, q in H:
        sa = (p[0] - gx) * dx + (p[2] - gz) * dz
        sb = (q[0] - gx) * dx + (q[2] - gz) * dz
        if sa * sb < 0:
            t = sa / (sa - sb)
            r = [p[k] + (q[k] - p[k]) * t for k in range(3)]
            lat = (r[0] - gx) * (-dz) + (r[2] - gz) * dx
            if abs(lat) <= dosah:
                body.append((lat, r[1]))
    vys = {}
    sir = {}
    for s in (-1, 1):
        st = [p for p in body if s * p[0] >= pul - 0.05]
        if st:
            top = max(p[1] for p in st)
            vys[s] = top
            sir[s] = max(abs(p[0]) for p in st if abs(p[1] - top) < 0.03) - pul
    dno = min((p[1] for p in body if abs(p[0]) < pul), default=None)
    return vys, dno, sir, (dx, dz)


R = [rez(i) for i in range(len(B))]
ok = [i for i in range(len(B)) if len(R[i][0]) == 2 and R[i][1] is not None]
sirky = [w for i in ok for w in R[i][2].values() if w > 0.05]
tl = sorted(sirky)[len(sirky) // 2] if sirky else float(V["tloustka_vychozi_m"])
print("LEDNICE_BLOK rezu s obema stenami %d z %d, tloustka rimsy (median) %.2f m" % (len(ok), len(B), tl))
mesh = bpy.data.meshes.new("Lednice_blok")
bmo = bmesh.new()
pod = float(V["pod_rimsou_m"])
zak = float(V["zaklad_m"])
for s in (-1, 1):
    pr = []
    for i in ok:
        vys, dno, _, (dx, dz) = R[i]
        gx, _, gz = B[i]
        nx, nz = -dz, dx
        prof = []
        for lat, y in ((pul, vys[s] - pod), (pul + tl, vys[s] - pod), (pul + tl, dno - zak), (pul, dno - zak)):
            x, z = gx + nx * lat * s, gz + nz * lat * s
            prof.append(bmo.verts.new((x, -z, y)))      # godot (x, y, z) -> blender (x, -z, y)
        pr.append(prof)
    for a, b in zip(pr, pr[1:]):
        for k in range(4):
            f = [a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]]
            bmo.faces.new(f if s > 0 else f[::-1])
    bmo.faces.new(pr[0][::-1] if s > 0 else pr[0])
    bmo.faces.new(pr[-1] if s > 0 else pr[-1][::-1])
bmesh.ops.recalc_face_normals(bmo, faces=bmo.faces)
uv = bmo.loops.layers.uv.new()
for f in bmo.faces:
    n = f.normal
    for lp in f.loops:
        c = lp.vert.co
        if abs(n.z) > 0.7:
            lp[uv].uv = (c.x, c.y)
        elif abs(n.x) > abs(n.y):
            lp[uv].uv = (c.y, c.z)
        else:
            lp[uv].uv = (c.x, c.z)
bmo.to_mesh(mesh)
mat = bpy.data.materials.new(V["material"])
mesh.materials.append(mat)
ob = bpy.data.objects.new("Lednice_blok-col", mesh)   # -col: Godot pridá kolizi (stena je pevna)
for x in list(bpy.context.scene.objects):
    bpy.data.objects.remove(x, do_unlink=True)
bpy.context.scene.collection.objects.link(ob)
out = os.path.join(ROOT, V["model"].replace("res://", ""))
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=False)
print("LEDNICE_BLOK zapsano %s, %d sten, tloustka %.2f m, zaklad %.2f m pod dnem" % (out, len(mesh.polygons), tl, zak))
