"""Vystroj kone z Balt Horse 12.-13. stol. (Sketchfab, RumiFerrus, licence Free Standard; Misa 28. 10. „sedlo,
uzdecka, cabraka bonus“): sit vystroje (jedna na variantu) se rozdeli na souvisle kusy; kusy na hlave a oteze
(stred y < UZDECKA_Y, hlava je v predloze na -y) = uzdecka, ostatni (sedlo, cabraka, podsedlova deka, poprsnik,
podbrisnik, trmeny) = sedlo. Kazda cast vlastni glb s pocatkem v kotvicim bode (sedlo: hrbet kone pod stredem
sedla, uzdecka: temeno hlavy) - hra je privesi na kosti kone (kun.gd, jizda.json kun.vystroj).
  /opt/bl/bin/python tools/kun_vystroj.py <balt.glb> modely/kone"""
import os
import sys

import bpy
from mathutils import Vector

SRC, OUT = sys.argv[-2], sys.argv[-1]
UZDECKA_Y = -0.75
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
for var, mat_s, mat_k in (("hneda", "balt_saddle", "balt_horse"), ("cervena", "balt_saddle2", "balt_horse2")):
    s = [o for o in bpy.data.objects if o.type == "MESH" and o.data.materials and o.data.materials[0].name == mat_s][0]
    k = [o for o in bpy.data.objects if o.type == "MESH" and o.data.materials and o.data.materials[0].name == mat_k][0]
    kp = [k.matrix_world @ v.co for v in k.data.vertices]
    cx = (min(p.x for p in kp) + max(p.x for p in kp)) / 2
    bpy.ops.object.select_all(action="DESELECT")
    s.select_set(True)
    bpy.context.view_layer.objects.active = s
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    kusy = [o for o in bpy.data.objects if o.type == "MESH" and o.data.materials and o.data.materials[0].name == mat_s]
    skup = {"sedlo": [], "uzdecka": []}
    for o in kusy:
        ps = [o.matrix_world @ v.co for v in o.data.vertices]
        cy = sum(p.y for p in ps) / len(ps)
        skup["uzdecka" if cy < UZDECKA_Y else "sedlo"].append(o)
    sp = [o.matrix_world @ v.co for o in skup["sedlo"] for v in o.data.vertices]
    sy = (min(p.y for p in sp) + max(p.y for p in sp)) / 2
    # hrbet pod stredem sedla: nejvyssi bod tela kone v pasu 10 cm kolem sy
    hrbet = max(p.z for p in kp if abs(p.y - sy) < 0.1 and abs(p.x - cx) < 0.15)
    up = [o.matrix_world @ v.co for o in skup["uzdecka"] for v in o.data.vertices]
    hy = min(p.y for p in kp)                                   # spicka nosu
    temeno = max((p for p in kp if p.y < hy + 0.45), key=lambda p: p.z)
    kotvy = {"sedlo": Vector((cx, sy, hrbet)), "uzdecka": Vector((cx, temeno.y, temeno.z))}
    for cast, obs in skup.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active
        j.name = "%s_%s" % (cast, var)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        j.data.transform(__import__("mathutils").Matrix.Translation(-kotvy[cast]))
        j.location = (0, 0, 0)
        bpy.ops.object.select_all(action="DESELECT")
        j.select_set(True)
        p = os.path.join(OUT, "vystroj_%s_%s.glb" % (cast, var))
        bpy.ops.export_scene.gltf(filepath=p, use_selection=True, export_format="GLB", export_yup=True)
        print("VYSTROJ", cast, var, len(j.data.polygons), "kotva", tuple(round(v, 3) for v in kotvy[cast]), p)
    print("PREDLOHA", var, "nos y %.3f, zad y %.3f, hrbet z %.3f, temeno z %.3f, delka %.3f" % (
        hy, max(p.y for p in kp), hrbet, temeno.z, max(p.y for p in kp) - hy))
