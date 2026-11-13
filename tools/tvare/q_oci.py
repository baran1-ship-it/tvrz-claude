"""Oči pro postavy Quaternius:
  add_blink(head_obj, brows_obj, eyes_obj) – tvarový klíč "mrknuti" (horní víčko dolů, dolní mírně nahoru, řasy s víčkem)
  split_eyes(eyes_obj, arm, NAME)            – oči rozdělené na <NAME>_oko_l / _oko_r, počátek ve středu bulvy, připnuté ke kosti Head
                                             (Godot z nich udělá uzly pod BoneAttachment3D; postava_oci.gd je natáčí)
"""
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix

def _eye_centers(eyes):
    co = np.array([eyes.matrix_world @ v.co for v in eyes.data.vertices])
    out = {}
    for side, s in (("l", 1), ("r", -1)):
        p = co[np.sign(co[:, 0]) == s]
        # střed bulvy ~ střed obalu (kulové části), přední plocha = min y
        c = (p.min(0) + p.max(0)) / 2
        out[side] = (c, (p.max(0) - p.min(0)) / 2)
    return out

def _blink_delta(P, centers, close=1.0):
    d = np.zeros_like(P)
    for side, (c, r) in centers.items():
        rx, rz = r[0] * 1.45, r[2] * 1.25
        zl = c[2] - r[2] * 0.12                     # linie zavřeného oka (mírně pod středem)
        dx = (P[:, 0] - c[0]) / rx; dz = (P[:, 2] - c[2]) / rz
        front = P[:, 1] < c[1] + r[1] * 0.4          # jen přední část (víčka, ne spánky za okem)
        e = dx ** 2 + dz ** 2
        w = np.clip(1 - e, 0, 1) ** 0.7 * front
        up = P[:, 2] > zl
        # horní víčko: stáhnout k linii, mírně dopředu (přes bulvu)
        d[:, 2] += np.where(up, (zl - P[:, 2]) * w * close, (zl - P[:, 2]) * w * 0.35 * close)
        d[:, 1] += -0.0015 * w * close
    return d

def add_blink(head, brows, eyes, lash_mask=None):
    cen = _eye_centers(eyes)
    for ob in (head, brows):
        if ob is None: continue
        mw = ob.matrix_world; inv = mw.inverted().to_3x3()
        P = np.array([mw @ v.co for v in ob.data.vertices])
        D = _blink_delta(P, cen)
        if ob is brows and lash_mask is not None:
            D[~lash_mask] = 0
        if np.abs(D).max() < 1e-6: continue
        if not ob.data.shape_keys: ob.shape_key_add(name="Basis", from_mix=False)
        sk = ob.shape_key_add(name="mrknuti", from_mix=False)
        for i, v in enumerate(ob.data.vertices):
            sk.data[i].co = v.co + inv @ Vector(D[i])
        sk.value = 0.0
        print("MRKNUTI", ob.name, int((np.abs(D).max(1) > 1e-5).sum()), "vrcholu")

def split_eyes(eyes, arm, NAME):
    cen = _eye_centers(eyes)
    out = []
    for side, s in (("l", 1), ("r", -1)):
        bpy.ops.object.select_all(action='DESELECT'); eyes.select_set(True); bpy.context.view_layer.objects.active = eyes
        bpy.ops.object.duplicate(); e = bpy.context.view_layer.objects.active
        bm = bmesh.new(); bm.from_mesh(e.data)
        mw = e.matrix_world
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if np.sign((mw @ v.co).x) != s], context='VERTS')
        bm.to_mesh(e.data); bm.free()
        for m in list(e.modifiers): e.modifiers.remove(m)
        e.vertex_groups.clear()
        if e.data.shape_keys: e.shape_key_clear()
        c = Vector(cen[side][0])
        # síť do světových souřadnic, počátek ve středu bulvy
        e.data.transform(mw); e.parent = None; e.matrix_world = Matrix.Identity(4)
        e.data.transform(Matrix.Translation(-c)); e.matrix_world = Matrix.Translation(c)
        wm = e.matrix_world.copy()
        e.parent = arm; e.parent_type = 'BONE'; e.parent_bone = "Head"
        bpy.context.view_layer.update(); e.matrix_world = wm
        e.name = f"{NAME}_oko_{side}"; e.data.name = e.name
        out.append(e)
    bpy.data.objects.remove(eyes)
    return out
