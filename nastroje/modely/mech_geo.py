"""Mech na kameny: nízké nepravidelné polštáře s texturou mechu (alpha clip na okraji).
Spuštění: python3 mech_geo.py   -> out/mech_1..3.glb
"""
import os, math, random
import numpy as np
import bpy
from mathutils import Vector, noise
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")
PX = 1024

def fbm(n, cells, seed, oct=5):
    out = np.zeros((n, n)); amp = 1; tot = 0
    for o in range(oct):
        r = np.random.RandomState(seed + o); c = cells * 2 ** o
        g = r.rand(c + 1, c + 1)
        t = np.linspace(0, c, n, endpoint=False); i = t.astype(int); f = t - i; f = f * f * (3 - 2 * f)
        a = g[i][:, i]; b = g[i][:, i + 1]; cc = g[i + 1][:, i]; d = g[i + 1][:, i + 1]
        top = a + (b - a) * f[None, :]; bot = cc + (d - cc) * f[None, :]
        out += amp * (top + (bot - top) * f[:, None]); tot += amp; amp *= 0.5
    return out / tot

def moss_texture(seed):
    n1 = fbm(PX, 4, seed); n2 = fbm(PX, 32, seed + 10, 3); n3 = fbm(PX, 128, seed + 20, 2)
    dark = np.array((30, 42, 16)); mid = np.array((60, 76, 28)); light = np.array((96, 106, 44))
    t = np.clip(n1 * 0.5 + n2 * 0.35 + n3 * 0.3, 0, 1)
    col = np.where(t[..., None] < 0.5, dark + (mid - dark) * (t[..., None] / 0.5), mid + (light - mid) * ((t[..., None] - 0.5) / 0.5))
    dry = np.clip((fbm(PX, 6, seed + 30) - 0.6) * 4, 0, 1)                       # zaschlá hnědá místa
    col = col * (1 - 0.6 * dry[..., None]) + np.array((104, 86, 46)) * 0.6 * dry[..., None]
    rr = np.random.RandomState(seed + 40)                                         # štětinky s tobolkami
    for _ in range(900):
        y, x = rr.randint(0, PX), rr.randint(0, PX)
        col[max(0, y - 2):y + 2, max(0, x - 1):x + 1] = (120, 64, 38)
    yy, xx = np.mgrid[0:PX, 0:PX] / PX - 0.5
    r = np.sqrt(xx ** 2 + yy ** 2) * 2
    edge = fbm(PX, 5, seed + 50) * 0.45
    alpha = (r < 0.72 + edge - 0.15).astype(np.float64)
    alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))) / 255.0
    frayed = (n3 > 0.45) | (r < 0.6 + edge - 0.15)
    alpha = alpha * frayed
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).convert("RGBA")
    img.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
    img.save(os.path.join(HERE, "atlas", "mech_color.png"))
    hgt = n2 * 0.6 + n3 * 0.4
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5; gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
    nx, ny = -gx * 12, gy * 12; ln = np.sqrt(nx ** 2 + ny ** 2 + 1)
    Image.fromarray(((np.stack([nx / ln, ny / ln, 1 / ln], -1) * 0.5 + 0.5) * 255).astype(np.uint8)).save(
        os.path.join(HERE, "atlas", "mech_normal.png"))

moss_texture(7)
for vi, (size, height, seed) in enumerate(((0.35, 0.03, 1), (0.7, 0.045, 2), (0.45, 0.09, 3)), start=1):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    N = 18
    verts, faces, uvs = [], [], []
    for j in range(N + 1):
        for i in range(N + 1):
            u, v = i / N, j / N
            x, y = (u - 0.5) * size, (v - 0.5) * size
            r = math.sqrt((u - 0.5) ** 2 + (v - 0.5) ** 2) * 2
            z = height * max(0.0, 1 - r * r) * (0.75 + 0.5 * (noise.noise(Vector((u * 4 + seed, v * 4, 0.3))) * 0.5 + 0.5))
            verts.append((x, y, z)); uvs.append((u, v))
    for j in range(N):
        for i in range(N):
            a = j * (N + 1) + i
            faces.append((a, a + 1, a + N + 2, a + N + 1))
    me = bpy.data.meshes.new(f"mech_{vi}"); me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    for p in me.polygons: p.use_smooth = True
    m = bpy.data.materials.new("game_mech"); m.use_nodes = True; m.use_backface_culling = False
    t = m.node_tree; b = t.nodes["Principled BSDF"]
    tx = t.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(HERE, "atlas", "mech_color.png"))
    nx = t.nodes.new("ShaderNodeTexImage"); nx.image = bpy.data.images.load(os.path.join(HERE, "atlas", "mech_normal.png"))
    nx.image.colorspace_settings.name = 'Non-Color'
    t.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    r = t.nodes.new("ShaderNodeMath"); r.operation = 'ROUND'
    t.links.new(tx.outputs["Alpha"], r.inputs[0]); t.links.new(r.outputs[0], b.inputs["Alpha"])
    nm = t.nodes.new("ShaderNodeNormalMap"); t.links.new(nx.outputs[0], nm.inputs["Color"]); t.links.new(nm.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.95
    me.materials.append(m)
    o = bpy.data.objects.new(f"mech_{vi}", me); bpy.context.collection.objects.link(o)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"mech_{vi}.glb"), export_format='GLB', use_selection=True,
                              export_yup=True, export_cameras=False, export_lights=False)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"mech_{vi}.blend"))
    d = o.dimensions
    print(f"RESULT mech_{vi} tris={len(faces) * 2} dims_m(sxvxh)={d.x:.2f} x {d.z:.2f} x {d.y:.2f}")
