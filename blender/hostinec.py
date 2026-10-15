"""Zajezdni hostinec a kupecky stan u hlavni cesty (modely hrace z tvrz-modely).

Hostinec: v modelu jsou okna jen prazdne otvory a chybi vchod z pavlace. Pri stavbe predmetu (predmety.py)
se pod jednim oknem pod pavlaci vybori vchod a kamenne zdi dostanou fotografickou texturu (puvodni ma 256 px).
Ve svete (export_game.py) se do otvoru osadi okna (dubovy ram s krizem, olovene sklo, v patre okenice)
a otviraci dvere; stoly a lavice pred hostincem jsou pevne predmety (da se na lavice sednout).
Stan: kolize kvadry (stoly, sudy, bedny, stena platna, tyce) misto presne site (provazy chytaly hrace),
na stolickach a lavici pod pristreskem se da sednout.

Souradnice modelu = Blender po importu glTF (x, y vodorovne, z nahoru), predek hostince je strana -y."""
import math
import os

import kraj

HERE = os.path.dirname(os.path.abspath(__file__))
# vyska stavby nad srovnanym terenem: podlaha hostince musi byt nad zemi (jinak jimi prorusta trava)
ZVEDNUTI = {"hostinec": 0.06, "stan_kupce": -0.04}

# otvory hostince: (osa steny, rovina steny, smer ven, u0, u1, z0, z1); osa "y" = stena v rovine y (u = x), "x" = v rovine x (u = y)
OKNA = [
    # prizemi (parapet 1.07, nadprazi 2.19)
    ("y", -1.78, -1, -5.05, -3.95, 1.07, 2.19), ("y", -1.78, -1, -1.45, -0.35, 1.07, 2.19),
    ("x", -5.39, -1, 5.75, 6.85, 1.07, 2.19), ("x", -5.39, -1, 9.35, 10.45, 1.07, 2.19),
    ("y", -0.02, -1, 0.35, 1.45, 1.07, 2.19), ("y", -0.02, -1, 2.15, 3.25, 1.07, 2.19), ("y", -0.02, -1, 3.95, 5.05, 1.07, 2.19),
    ("y", -0.02, -1, 5.75, 6.85, 1.07, 2.19),
    ("x", 8.98, 1, 3.95, 5.05, 1.07, 2.19),
    # patro (parapet 3.72, nadprazi 4.85)
    ("y", -1.90, -1, -4.35, -3.27, 3.72, 4.85), ("y", -1.90, -1, -2.14, -1.05, 3.72, 4.85),
    ("x", -5.50, -1, 4.49, 5.58, 3.72, 4.85), ("x", -5.50, -1, 6.87, 7.95, 3.72, 4.85), ("x", -5.50, -1, 9.23, 10.33, 3.72, 4.85),
    ("y", -0.10, -1, 0.85, 1.97, 3.72, 4.85), ("y", -0.10, -1, 3.15, 4.26, 3.72, 4.85),
    ("x", 9.10, 1, 0.78, 1.86, 3.72, 4.85), ("x", 9.10, 1, 3.33, 4.42, 3.72, 4.85), ("x", 9.10, 1, 6.86, 7.94, 3.72, 4.85),
]
# puvodni otvory modelu: vchod do sine z pavlace (bok), zadni dvere skladu; dvere z patra na pavlac
DVERE = [("x", -0.2, 1, -1.45, -0.3, 0.0, 2.19), ("y", 7.8, 1, 2.1, 3.35, 0.0, 2.19), ("y", -0.10, -1, 5.43, 6.70, 2.80, 4.95)]
VCHOD_POLE = None                 # zed se nevyboruje (vchod uz v modelu je)

# dvere z balicku hrace (medieval_door_pack): kridlo vchodu s okenkem a mrizkou, na pavlac prkenne; spolecna textura
DVERE_KRIDLA = ["DoorCave_MainDoor_DoorCave_0", "DoorSimple_DoorSimple_0"]
DVERE_TEX = "dvere_hostinec"
TEXTURY = {DVERE_TEX: [1.0, 1.0]}       # rozmer textury v m (UV modelu jsou 0..1)
EXT = os.environ.get("TVRZ_EXT", "/home/user/tvrz-modely/stazene")
TEX_SRC = os.environ.get("TVRZ_EXT_TEX", "/home/user/tvrz-modely/textury/medieval_door_pack")

# vybaveni hostince: (id, x, y, vyska nad podlahou, smer). Smer: "-y" lic k ceste (predek), "+y", "-x", "+x";
# stoly "podel_x"/"podel_y" (delka stolu), lavice "x"/"y" (delka lavice). Koncovka "!" = venku na terenu.
SMER = {"-y": 0.0, "+y": math.pi, "-x": -math.pi / 2, "+x": math.pi / 2,
        "podel_x": math.pi / 2, "podel_y": 0.0, "x": 0.0, "y": math.pi / 2}
P1 = 2.84            # podlaha patra
LUSTR = 2.58 - 0.9   # lustr visi z tramu stropu (spodek modelu)
VYBAVENI = [
    # sin u krbu (leve kridlo vpredu): dva stoly s lavicemi, stolicky u ohne, stojaci svice
    ("stul_hospoda", -2.3, -0.5, 0, "podel_x"), ("lavice_selska", -2.3, -1.1, 0, "x"), ("lavice_selska", -2.3, 0.1, 0, "x"),
    ("stul_hospoda", -2.3, 2.3, 0, "podel_x"), ("lavice_selska", -2.3, 1.7, 0, "x"), ("lavice_selska", -2.3, 2.9, 0, "x"),
    ("stolicka", -4.5, 0.2, 0, "-x"), ("stolicka", -4.5, 1.8, 0, "-x"),
    ("svicen_stojaci", -0.55, -1.35, 0, "-y"), ("svicen_stojaci", -4.9, 3.2, 0, "-y"),
    ("svicen", -2.6, -0.5, 0.78, "-y"), ("korbel_okovany", -1.8, -0.75, 0.78, "-y"), ("dzban_kamenny", -2.0, -0.3, 0.78, "-y"),
    ("svicen", -2.0, 2.3, 0.78, "-y"), ("pohar_drevo", -2.8, 2.05, 0.78, "-y"), ("pohar_drevo", -2.9, 2.55, 0.78, "+y"),
    # kuchyn (leve kridlo vzadu u ohniste): kotlik na trojnozce, pracovni stul s jidlem, police, zasoby
    ("kotlik", -2.45, 10.9, 0.06, "-y"), ("stul_selsky", -2.7, 8.2, 0, "podel_y"), ("stolicka", -2.7, 7.5, 0, "-y"),
    ("police_stara", -5.05, 8.3, 0, "+x"), ("sud", -0.55, 10.25, 0, "-y"), ("pytel_mouky", -1.25, 10.4, 0, "-y"),
    ("maselnice", -4.9, 7.25, 0, "-y"), ("hranice_dreva", -4.3, 10.45, 0, "-y"), ("vedro", -1.0, 9.6, 0, "-y"),
    ("hrnec", -3.2, 8.2, 0.78, "-y"), ("prkenko", -2.5, 8.1, 0.78, "-y"), ("bochnik", -2.1, 8.3, 0.78, "-y"),
    ("zeli", -2.0, 7.95, 0.78, "-y"), ("mrkev", -3.5, 7.95, 0.78, "-y"), ("panev", -2.75, 8.35, 0.78, "-y"),
    # sklad v pristavku: sudy, bedna, pytle (stred a vchod z kuchyne volne)
    ("sud", 0.5, 7.35, 0, "-y"), ("sud", 3.15, 7.35, 0, "-y"), ("bedna", 3.15, 6.6, 0, "-x"),
    ("pytel_obili", 3.2, 5.95, 0, "-y"), ("pytel_mouky", 2.65, 5.95, 0, "-y"), ("sud", 0.55, 6.6, 0, "+x"),
    # senk za vchodem: dva stoly s lavicemi, nad nimi lustry se svickami, selska skrin, sudy
    ("stul_hospoda", 1.0, 3.0, 0, "podel_y"), ("lavice_selska", 0.4, 3.0, 0, "y"), ("lavice_selska", 1.6, 3.0, 0, "y"),
    ("stul_hospoda", 7.9, 2.0, 0, "podel_y"), ("lavice_selska", 7.3, 2.0, 0, "y"), ("lavice_selska", 8.5, 2.0, 0, "y"),
    ("lustr", 1.0, 3.0, LUSTR, "-y"), ("lustr", 7.9, 2.0, LUSTR, "-y"),
    ("skrin_selska", 3.6, 5.0, 0, "-y"), ("sud", 4.5, 0.45, 0, "-y"), ("sud", 6.3, 0.45, 0, "-y"),
    ("korbel", 1.1, 2.4, 0.78, "-y"), ("korbel", 0.9, 3.5, 0.78, "-y"), ("vino_dzban", 1.0, 2.9, 0.78, "-y"),
    ("pivo", 7.8, 1.5, 0.78, "-y"), ("pivo", 8.0, 2.6, 0.78, "-y"), ("bochnik", 7.95, 2.05, 0.78, "-y"),
    # patro: loznice nad kuchyni (dve postele, truhly, nocni stolek se svicnem), pokoj nad senkem
    ("truhla", -4.3, 7.9, P1, "-y"), ("truhla", -1.2, 7.9, P1, "-y"),
    ("nocni_stolek", -2.75, 10.1, P1, "-y"), ("svicen", -2.75, 10.1, P1 + 0.62, "-y"), ("stolicka", -2.75, 7.6, P1, "-y"),
    ("truhla", 1.0, 3.1, P1, "-y"), ("nocni_stolek", 2.15, 0.45, P1, "-y"),
    ("svicen", 2.15, 0.45, P1 + 0.62, "-y"),
    ("truhla", 8.25, 3.1, P1, "-y"),
    # venku pred hostincem: stojany s loucemi u stolu (stoly a lavice viz kraj.STOLY_VENKU)
    ("stojan_louce", -5.8, -4.4, 0, "-y!"), ("stojan_louce", 0.95, -4.4, 0, "-y!"), ("stojan_louce", 9.1, -4.4, 0, "-y!"),
]

# krby (ohen ve hre jde zapalit/zhasnout): (x, y ohniste v modelu, smer do mistnosti)
KRBY = [(-2.68, 10.95, (0.0, -1.0)), (-5.8, 0.9, (1.0, 0.0))]

# selska luzka v patre (vesnice.cot_bed): (x, y stredu, smer hlavy "+y"/"-y") - zajezdni hostinec, nic panskeho
LUZKA = [(-4.3, 9.4, "+y"), (-1.2, 9.4, "+y"), (1.0, 1.4, "-y"), (8.25, 1.4, "-y")]

MISTNOSTI = [
    ("loznice", -5.4, 0.0, 5.7, 10.8, P1, 5.3, (0.12, 0.11, 0.1)), ("pokoj", 0.0, 9.0, 0.0, 5.4, P1, 5.3, (0.14, 0.13, 0.12)),
    ("sin", -5.4, 0.0, -1.8, 5.4, 0.0, 5.3, (0.16, 0.15, 0.14)), ("kuchyne", -5.4, 0.0, 5.4, 10.8, 0.0, P1, (0.13, 0.12, 0.11)),
    ("senk", 0.0, 9.0, 0.0, 5.4, 0.0, P1, (0.16, 0.15, 0.14)), ("sklad", 0.0, 3.66, 5.5, 7.9, 0.0, 3.0, (0.1, 0.1, 0.09)),
    ("schody", 5.4, 9.0, 5.4, 9.0, 0.0, 5.3, (0.12, 0.11, 0.1)),
]
MISTNOSTI_NAZVY = {"loznice": "Ložnice", "pokoj": "Pokoj pro hosty", "sin": "Síň", "kuchyne": "Kuchyně", "senk": "Šenk",
                   "sklad": "Sklad", "schody": "Schodiště"}

# stan: kolizni kvadry (x0, y0, z0, x1, y1, z1) v souradnicich modelu
STAN_BOXY = [
    (-3.6, 1.82, 0.0, -2.53, 3.89, 0.76), (-1.45, 1.84, 0.0, -0.38, 3.67, 0.76), (0.54, 1.84, 0.0, 1.61, 3.67, 0.76),   # stoly
    (0.24, -1.83, 0.0, 1.86, 0.94, 1.4), (-1.53, 1.12, 0.0, -0.32, 1.77, 0.82), (1.38, 0.92, 0.0, 2.05, 1.92, 0.76),     # sudy, hrnce
    (0.83, -3.29, 0.0, 2.72, -2.05, 1.1), (-2.56, -2.48, 0.0, -2.11, -1.99, 0.49),                                       # bedny, spalek
    (2.0, -2.05, 0.0, 2.2, 3.95, 2.2), (-2.0, -2.15, 0.0, 2.2, -1.95, 2.4), (-2.0, 3.9, 0.0, 2.2, 4.05, 2.4),            # platno (zavrene strany)
] + [(x - 0.08, y - 0.08, 0.0, x + 0.08, y + 0.08, 2.2) for x, y in ((-0.03, 3.75), (-0.03, -0.08), (2.0, -0.03), (2.0, 1.9))]
# stan: sedatka (stred x, y, vyska sedaku, nazev) a stred stolu pod pristreskem, ke kteremu se sedi
STAN_SEDY = [(-2.655, 1.445, 0.32, "Stolička"), (-4.095, 2.525, 0.32, "Stolička"), (-3.04, 4.075, 0.38, "Lavice")]
STAN_STUL = (-3.07, 2.855)


def _land(x, z):
    import fort
    return fort.land(x, z)


def stan_boxy():
    """Kolize stanu v mistnich souradnicich hry (stred x, y, z a rozmer x, y, z) pro svet.json."""
    sx, sy = kraj.STRED["stan_kupce"]
    out = []
    for x0, y0, z0, x1, y1, z1 in STAN_BOXY:
        out.append([round((x0 + x1) / 2 - sx, 3), round((z0 + z1) / 2, 3), round(-((y0 + y1) / 2 - sy), 3),
                    round(x1 - x0, 3), round(z1 - z0, 3), round(y1 - y0, 3)])
    return out


def stan_sedy(y_stan):
    """Mista k sezeni ve stanu jako 'pouziti' (kind sed): hrac sedi celem ke stolu pod pristreskem."""
    tx, tz = kraj.stavba_bod("stan_kupce", *STAN_STUL)
    out = []
    for bx, by, h, nazev in STAN_SEDY:
        x, z = kraj.stavba_bod("stan_kupce", bx, by)
        yaw = math.atan2(-(tx - x), -(tz - z))
        out.append({"kind": "sed", "nazev": nazev, "pos": [x, y_stan + h + 0.3, z], "r": 1.4, "sit": [x, y_stan, z], "h": h, "yaw": yaw})
    return out


# ------------------------------------------------------------------ uprava modelu (predmety.py, Blender)

def uprav_model(ob):
    """Vchod pod pavlaci (smazat zed a podezdivku pod oknem v jednom poli) a kamenne zdi s texturou zdiva."""
    import bmesh
    import bpy
    me = ob.data
    stone = [i for i, m in enumerate(me.materials) if m and m.name.startswith(("StoneWall", "DarkStone"))]
    bm = bmesh.new()
    bm.from_mesh(me)
    a, b = VCHOD_POLE if VCHOD_POLE else (99.0, -99.0)
    kill = []
    for f in bm.faces:
        if f.material_index not in stone or not VCHOD_POLE:
            continue
        xs = [v.co.x for v in f.verts]
        ys = [v.co.y for v in f.verts]
        zs = [v.co.z for v in f.verts]
        if min(xs) > a - 0.01 and max(xs) < b + 0.01 and min(ys) > -0.12 and max(ys) < 0.1 and max(zs) < 1.08:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    print("hostinec: vchod, smazano %d ploch" % len(kill))
    # zdivo: UV promitnute z kostky v metrech (dlazdice 2.5 m), aby kameny mely vsude stejnou velikost
    wall = [i for i, m in enumerate(me.materials) if m and m.name.startswith("StoneWall")]
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new()
    T = 2.5
    for f in bm.faces:
        if f.material_index not in wall:
            continue
        n = f.normal
        for lp in f.loops:
            p = lp.vert.co
            if abs(n.z) > 0.7:
                u, v = p.x, p.y
            elif abs(n.x) > abs(n.y):
                u, v = (p.y if n.x > 0 else -p.y), p.z
            else:
                u, v = (-p.x if n.y > 0 else p.x), p.z
            lp[uv].uv = (u / T, v / T)
    bm.to_mesh(me)
    bm.free()
    mat = bpy.data.materials.new("zdivo_hostinec")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = os.path.join(HERE, "tex_cache")

    def img(name, non_color=False):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(os.path.join(tc, name))
        if non_color:
            n.image.colorspace_settings.name = "Non-Color"
        return n
    nt.links.new(img("zdivo_diff_2k.jpg").outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(img("zdivo_rough_2k.jpg", True).outputs["Color"], bsdf.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(img("zdivo_nor_2k.jpg", True).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    for i in wall:
        me.materials[i] = mat


def textury(td):
    """Textura dveri pro hru (modely/textury): z PNG v tvrz-modely, 1k, drsnost = zeleny kanal drsnost_kov."""
    import shutil

    from PIL import Image
    tc = os.path.join(HERE, "tex_cache")
    for k in ("diff", "nor", "rough", "disp"):
        f = os.path.join(tc, "%s_%s.jpg" % (DVERE_TEX, k))
        if not os.path.exists(f):
            if k == "disp":
                Image.new("RGB", (64, 64), (128, 128, 128)).save(f)
            elif k == "rough":
                g = Image.open(os.path.join(TEX_SRC, "DoorCave_drsnost_kov.png")).convert("RGB").split()[1].resize((1024, 1024))
                Image.merge("RGB", (g, g, g)).save(f, quality=90)
            else:
                src = "DoorCave_barva.png" if k == "diff" else "DoorCave_normala.png"
                Image.open(os.path.join(TEX_SRC, src)).convert("RGB").resize((1024, 1024)).save(f, quality=90)
        shutil.copyfile(f, os.path.join(td, "%s_%s.jpg" % (DVERE_TEX, k)))


def _kridla():
    """Sit kridel z balicku dveri: [(vrcholy, plochy, uv)] normovane na 0..1 sirky a vysky, lic v z = 0 (zadni strana z < 0)."""
    import bpy
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(EXT, "medieval_door_pack.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    out = []
    for name in DVERE_KRIDLA:
        o = [x for x in new if x.name == name][0]
        me = o.data
        vs = [o.matrix_world @ v.co for v in me.vertices]
        x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
        y0 = min(v.y for v in vs)
        z0, z1 = min(v.z for v in vs), max(v.z for v in vs)
        # Blender: lic dveri hledi do -y; mistne: x 0..1 (pant vlevo), y 0..1 nahoru, z = hloubka (lic 0, dozadu zaporne)
        loc = [((v.x - x0) / (x1 - x0), (v.z - z0) / (z1 - z0), -(v.y - y0) + 0.0) for v in vs]
        uvl = me.uv_layers.active.data
        faces, uvs = [], []
        for p in me.polygons:
            faces.append(list(p.vertices))
            uvs.append([tuple(uvl[li].uv) for li in p.loop_indices])
        out.append((loc, faces, uvs, max(v.y for v in vs) - y0))
    for o in new:
        bpy.data.objects.remove(o)
    return out


# ------------------------------------------------------------------ okna a dvere ve svete (export_game.py, Blender)

def build(coll):
    """Okna a dvere hostince, stoly a lavice pred nim (pevne predmety ve vesnici), sedatka ve stanu."""
    from mathutils import Matrix, Vector

    import kit
    import lib
    import vesnice
    from lib import M, Part
    hid = "hostinec"
    _, cx, cz, yaw, r = [s for s in kraj.STAVBY if s[0] == hid][0]
    y0 = _land(cx, cz) + ZVEDNUTI[hid]          # stejne jako umisteni modelu (export_game, "staticke")

    def pt(bx, by, bz):
        x, z = kraj.stavba_bod(hid, bx, by)
        return Vector((x, y0 + bz, z))

    up = Vector((0, 1, 0))

    def frame(ax, plane, out, u0, u1, z0):
        """Pocatek ve stredu spodni hrany otvoru v rovine steny, baze (podel, nahoru, ven)."""
        uc = (u0 + u1) / 2
        o = pt(uc, plane, z0) if ax == "y" else pt(plane, uc, z0)
        n = (pt(uc, plane + out, z0) if ax == "y" else pt(plane + out, uc, z0)) - o
        n.normalize()
        t = up.cross(n)
        return o, t, n, Matrix((t, up, n)).transposed()

    # material dveri z balicku (ve hre fotograficky material s UV modelu)
    lib.GAMEMAT[DVERE_TEX] = {"type": "tex", "tex": DVERE_TEX, "coord": "uv", "swap": False, "tint": [1.0, 1.0, 1.0], "grey": 0.0}
    lib.new_mat(DVERE_TEX)
    kridla = _kridla()
    P = Part("Hostinec_okna", bevel=0.006)
    for ax, plane, out, u0, u1, z0, z1 in OKNA:
        o, t, n, B = frame(ax, plane, out, u0, u1, z0)
        w, h = u1 - u0, z1 - z0
        k, d = 0.085, 0.2             # sila ramu, hloubka (pres celou zed, vystupuje na obe strany)

        def bx(c, size, mat, B=B):
            P.box(M(c, basis=B), size, mat)
        for sx in (-1, 1):
            bx(o + t * (sx * (w / 2 - k / 2)) + up * (h / 2), (k, h, d), "dub_ven")
        bx(o + up * (h - k / 2), (w - 2 * k + 0.002, k, d), "dub_ven")
        bx(o + up * (k / 2), (w - 2 * k + 0.002, k, d), "dub_ven")
        # parapet: prkno vystupujici ven a mirne sirsi nez otvor
        bx(o + up * 0.02 + n * 0.12, (w + 0.16, 0.05, 0.2), "dub_ven")
        # kriz (sloupek a pricel) a olovene sklo uprostred zdi
        bx(o + up * (h / 2), (0.06, h - 2 * k, 0.09), "dub_ven")
        bx(o + up * (k + (h - 2 * k) * 0.62), (w - 2 * k, 0.06, 0.09), "dub_ven")
        bx(o + up * (h / 2), (w - 2 * k, h - 2 * k, 0.012), "sklo_terce")
        if z0 > 3.0:
            # v patre okenice otevrene ke zdi (kolem pantu o 100 st.)
            for sgn in (-1, 1):
                hinge = o + t * (sgn * (w / 2 + 0.02)) + n * 0.05
                dirv = (t * sgn * math.cos(math.radians(10)) + n * math.sin(math.radians(10))).normalized()
                lw = w / 2 - 0.02
                c = hinge + dirv * (lw / 2) + up * (h / 2)
                nrm = up.cross(dirv).normalized()
                Bs = Matrix((dirv, up, nrm)).transposed()
                P.box(M(c, basis=Bs), (lw, h - 0.04, 0.035), "okenice")
                for yy in (-0.3, 0.3):
                    P.box(M(c + up * (yy * h) + nrm * 0.022 * (1 if nrm.dot(n) > 0 else -1), basis=Bs), (lw - 0.05, 0.05, 0.012), "zelezo")
    for di, (ax, plane, out, u0, u1, z0, z1) in enumerate(DVERE):
        o, t, n, B = frame(ax, plane, out, u0, u1, z0)
        w, h = u1 - u0, z1 - z0
        k = 0.09
        # dubova zarubeň s nadprazim a prah
        for sx in (-1, 1):
            P.box(M(o + t * (sx * (w / 2 - k / 2)) + up * (h / 2), basis=B), (k, h, 0.22), "dub_ven")
        P.box(M(o + up * (h - k / 2), basis=B), (w + 0.1, k, 0.24), "dub_ven")
        P.box(M(o + up * 0.02, basis=B), (w - 2 * k, 0.04, 0.26), "dub_ven")
        # kridlo jako pohyblivy dilek (otevrit / zavrit), pant u leveho ostění, otevira se dovnitr
        wl, hl = w - 2 * k - 0.01, h - k - 0.03
        m = M(o + t * 0.0 + n * 0.035 + up * 0.03, basis=B)
        kit.DOOR_N += 1
        gid = "dvere%d" % kit.DOOR_N
        hm = m @ M((-wl / 2, 0.0, 0.0))
        loc, faces, uvs, tl = kridla[0 if di < len(DVERE) - 1 else 1]          # vchody kridlo s kovanim, na pavlac prkenne

        def leaf(Q, wl=wl, hl=hl, loc=loc, faces=faces, uvs=uvs, tl=tl):
            # kridlo z balicku roztazene do otvoru; tloustka 6 cm (lic s kovanim v z = 0)
            kz = 0.06 / max(tl, 0.06)
            Q.mesh([(x * wl, y * hl, z * kz) for x, y, z in loc], faces, DVERE_TEX, uvs, rnd=0.85)
        kit.movable(gid, "dvere", hm, leaf,
                    cols=[((wl / 2, hl / 2, -0.03), (wl - 0.02, hl - 0.02, 0.09))], use=list(m @ Vector((0.0, 1.2, 0.0))),
                    group=gid, open=92.0, init=0.0, dur=1.0)
    # vozy s plachtou: u boku hostince (zajezd formanu) a vedle kupeckeho stanu
    import nove
    for sid, bx_, by_, dy in (("hostinec", 11.6, 3.0, 0.0), ("stan_kupce", 6.2, 0.6, 0.2)):
        x, z = kraj.stavba_bod(sid, bx_, by_)
        nove.misto("zebrinak_plachta_1", x, _land(x, z), z, 1.0, kraj.stavba_yaw(sid) + dy, P, sink=0.0)
    # selska luzka (lehnout si a vyspat se)
    for lx, ly, hl in LUZKA:
        sg = 1.0 if hl == "+y" else -1.0
        c = pt(lx, ly, P1)
        d = pt(lx, ly + sg, P1) - c
        F = vesnice.Frame((c.x, c.z), math.atan2(d.z, d.x), c.y)
        vesnice.cot_bed(P, F, 0.0, 0.0)
        lib.INFO["use"].append({"kind": "bed", "pos": [c.x, c.y + 0.7, c.z], "r": 2.2})
    P.commit(coll)
    # sklad v pristavku nemel podlahu (trava skrz): prkna
    ex = (pt(1, 0, 0) - pt(0, 0, 0)).normalized()
    ez = (pt(0, 1, 0) - pt(0, 0, 0)).normalized()
    Bf = Matrix((ex, up, ez)).transposed()
    Pf = Part("Hostinec_sklad_podlaha")
    Pf.box(M(pt(1.86, 6.7, 0.0), basis=Bf), (3.62, 0.06, 2.4), "prkna", collide=True)
    Pf.commit(coll)
    # ohen v krbech (kuchyne s kotlikem, sin): hori od zacatku
    # polena a popel v ohnisti (ohen hori na drevu, ne na holem kameni)
    Pk = Part("Hostinec_ohniste")
    for kx, ky, _ in KRBY:
        c = pt(kx, ky, 0.0)
        Pk.lathe(M(c + up * 0.01), [(0.42, 0.0), (0.0, 0.035)], 12, "popel")
        for q in range(3):
            a_ = q * 2.1 + 0.4
            dv = Vector((math.cos(a_), 0.0, math.sin(a_)))
            Pk.rod(c + dv * 0.32 + up * 0.06, c - dv * 0.06 + up * 0.17, 0.055, 7, "kura")
        Pk.rod(c + Vector((-0.3, 0.05, 0.12)), c + Vector((0.32, 0.05, 0.1)), 0.06, 7, "kura")
    Pk.commit(coll)
    for k, (kx, ky, (dx, dy)) in enumerate(KRBY):
        c = pt(kx, ky, 0.05)
        sv = pt(kx + dx * 0.8, ky + dy * 0.8, 0.65) - c
        nm = "krb_hostinec_%d" % k
        lib.fire("hearth", c, name=nm, size=0.75, zap=True, svetlo=[round(sv.x, 3), round(sv.y, 3), round(sv.z, 3)])
        lib.INFO["use"].append({"kind": "fire", "pos": list(pt(kx + dx * 1.2, ky + dy * 1.2, 0.9)), "r": 2.0, "name": nm})
    # stoly a lavice pred hostincem: pevne predmety (na lavici se da sednout)
    for id_, x, z, yw in kraj.STOLY_VENKU:
        vesnice.VYBAVENI.append({"id": id_, "p": [round(x, 3), round(_land(x, z), 3), round(z, 3)], "yaw": round(yw, 4)})
    # vybaveni uvnitr a louce venku (souradnice modelu; smer = kam hledi lic predmetu / podel ceho lezi)
    for id_, bx_, by_, bz_, smer in VYBAVENI:
        x, z = kraj.stavba_bod(hid, bx_, by_)
        yb = _land(x, z) if smer.endswith("!") else y0 + bz_
        vesnice.VYBAVENI.append({"id": id_, "p": [round(x, 3), round(yb + (bz_ if smer.endswith("!") else 0.0), 3), round(z, 3)],
                                 "yaw": round(yaw + SMER[smer.rstrip("!")], 4)})
    # mistnosti (ve hre ubyde svetla z oblohy podle oken, nazev mista): (nazev, x0, x1, y0, y1, z0, z1, ambient)
    for rn, x0_, x1_, ya, yb_, za, zb, amb in MISTNOSTI:
        c = pt((x0_ + x1_) / 2, (ya + yb_) / 2, za)
        vesnice.MISTNOSTI.append({"name": "hostinec_" + rn, "title": MISTNOSTI_NAZVY[rn] + " – Zájezdní hostinec",
                                  "pos": [c.x, c.y, c.z], "size": [x1_ - x0_, zb - za, yb_ - ya], "yaw": yaw, "ambient": list(amb)})
    # sedatka ve stanu
    _, sxx, szz, _, _ = [s for s in kraj.STAVBY if s[0] == "stan_kupce"][0]
    lib.INFO["use"].extend(stan_sedy(_land(sxx, szz) + ZVEDNUTI["stan_kupce"]))
    print("hostinec: %d oken, %d dveri, %d kusu u stolu; stan: %d sedatek" % (len(OKNA), len(DVERE), len(kraj.STOLY_VENKU), len(STAN_SEDY)))
