"""Scena, svetlo, kamery a renderovani nahledu."""
import math

import bpy
from mathutils import Vector

from lib import to_bl


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = 64
    s.cycles.use_denoising = True
    s.cycles.denoiser = "OPENIMAGEDENOISE"
    s.cycles.max_bounces = 6
    s.cycles.diffuse_bounces = 3
    s.cycles.glossy_bounces = 2
    s.cycles.transparent_max_bounces = 4
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.cycles.light_sampling_threshold = 0.01
    s.render.resolution_x = 1600
    s.render.resolution_y = 900
    s.render.image_settings.file_format = "JPEG"
    s.render.image_settings.quality = 90
    s.view_settings.view_transform = "AgX"
    try:
        s.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    s.unit_settings.system = "METRIC"
    return s


def coll(name: str):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def sky(elev_deg=28.0, azim_deg=135.0, strength=1.0, sun_strength=4.5, haze=1.0):
    """Fyzikalni obloha + slunce. azim: 0 = slunce na severu (-Z ve hre), 90 = na vychode."""
    s = bpy.context.scene
    w = bpy.data.worlds.new("Svet")
    s.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    sk = nt.nodes.new("ShaderNodeTexSky")
    sk.sky_type = "MULTIPLE_SCATTERING"
    sk.sun_disc = False
    sk.sun_elevation = math.radians(elev_deg)
    # Blender: sun_rotation 0 = slunce ve smeru +Y (= sever ve hre, -Z)
    sk.sun_rotation = math.radians(-azim_deg)
    try:
        sk.air_density = 1.0
        sk.aerosol_density = haze
    except AttributeError:
        pass
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sk.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    # slunce
    ld = bpy.data.lights.new("Slunce", "SUN")
    ld.energy = sun_strength
    ld.angle = math.radians(0.8)
    ld.color = (1.0, 0.93, 0.82)
    ob = bpy.data.objects.new("Slunce", ld)
    s.collection.objects.link(ob)
    el = math.radians(elev_deg)
    az = math.radians(azim_deg)
    # smer ke slunci ve hre: sever = -Z, vychod = +X
    d = Vector((math.sin(az) * math.cos(el), math.sin(el), -math.cos(az) * math.cos(el)))
    db = Vector(to_bl(d))
    ob.rotation_euler = (-db).to_track_quat("-Z", "Y").to_euler()
    return ob


def camera(pos, target, lens=24.0, name="Kamera"):
    s = bpy.context.scene
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 2000
    cd.sensor_width = 36
    ob = bpy.data.objects.new(name, cd)
    s.collection.objects.link(ob)
    p = Vector(to_bl(Vector(pos)))
    t = Vector(to_bl(Vector(target)))
    ob.location = p
    ob.rotation_euler = (t - p).to_track_quat("-Z", "Y").to_euler()
    s.camera = ob
    return ob


def point_light(pos, energy, color=(1.0, 0.55, 0.25), radius=0.08, name="Svetlo"):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = to_bl(Vector(pos))
    return ob


def render(path, samples=None, res=None):
    s = bpy.context.scene
    if samples:
        s.cycles.samples = samples
    if res:
        s.render.resolution_x, s.render.resolution_y = res
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)
