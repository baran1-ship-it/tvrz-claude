"""Kovadlina 1393 na dubovém špalku se sperhákem (Míša 15. 11.: „kovadlinu chci novou, ale musí být vymazlená, krásný
fotorealistický model … já chci čistou“ – bez meče a nářadí; „podívej se na KCD“ – závazná předloha tvaru
docs/reference/kovarna/kcd2_kovadlina_misa_15_11.jpg). Rozměry a zdroje: pravidla/svet/kovadlina_1393.json.

Postup (modelový filtr): high-poly z lofted dílů (tělo s pasem a čtyřmi patkami, kónický roh, patka s otvory, sperhák)
→ voxel remesh (sjednocení) → otlučené hrany (koule odečtené z hran dráhy) → nerovnosti kování a důlky po kladivu
(displace, dráha zůstává rovná) → decimace na low-poly → zapečení (Cycles) albedo, normal, ORM 2048 px z high-poly
a z materiálu: dráha vyleštěná (kov, nízká drsnost, škrábance), boky tmavé okuje, rez v dutinách a u dřeva,
hrany oťukané (zakřivení = pointiness), AO v dutinách. Špalek: dub bez kůry (Poly Haven rough_wood), čelo
s letokruhy, dřeňovými paprsky, výsušnými trhlinami a okujemi kolem kovadliny (vlastní numpy textura), pásek
u horní hrany, kramle přes patky kovadliny.

Cizí podklady (Poly Haven, CC0 1.0, staženo 15. 11. 2026, 2k jpg):
  rust_coarse_01 – Dimitrios Savva (foto), Rico Cilliers (zpracování), https://polyhaven.com/a/rust_coarse_01
  rough_wood     – Rob Tuytel, https://polyhaven.com/a/rough_wood
Výstup (hra/modely/predmety_h/):
  kovadlina_1393.glb          podrobný (2 materiály: železo, dřevo; každý albedo + normal + ORM 2048) + kolize
                              Kovadlina_1393_kolize-convcolonly (jeden konvexní obal)
  kovadlina_1393_stredni.glb  ~3 tis. troj., barva vrcholů + textury 512 (konvence predmety.gd _stredni)
  kovadlina_1393_daleko.glb   ~500 troj., barva vrcholů + textury 256
Počátek na zemi uprostřed špalku, 1 m = 1, v Godotu Y nahoru, dráha a roh podél +X.

  /opt/bl/bin/python blender/kovadlina.py <koren_puchartu> [--tex DIR] [--prac DIR] [--vzorky N]
  (--tex: složka s texturami Poly Haven; chybějící se stáhnou z api.polyhaven.com)
"""
import sys, os, json, math, random, argparse, urllib.request
import numpy as np
import bpy, bmesh
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("koren", nargs="?", default=".")
ap.add_argument("--tex", default=None)
ap.add_argument("--prac", default=None)
ap.add_argument("--vzorky", type=int, default=24)
ap.add_argument("--px", type=int, default=2048)
ap.add_argument("--nahled", action="store_true", help="jen geometrie + náhled (workbench), bez pečení")
A = ap.parse_args([a for a in sys.argv[1:] if a != "--"])
K = os.path.abspath(A.koren)
D = json.load(open(os.path.join(K, "pravidla/svet/kovadlina_1393.json")))
TEX = os.path.abspath(A.tex or os.path.join(K, "blender/tex"))
PRAC = os.path.abspath(A.prac or os.path.join(K, "build/kovadlina"))
OUT = os.path.join(K, "hra/modely/predmety_h")
os.makedirs(PRAC, exist_ok=True); os.makedirs(OUT, exist_ok=True); os.makedirs(TEX, exist_ok=True)
PX = A.px
random.seed(1393); RNG = np.random.default_rng(1393)

SP = D["spalek"]; KV = D["kovadlina"]; SH = D["sperhak"]
R0, H, FIL = SP["polomer_m"], SP["vyska_m"], SP["zaobleni_hrany_m"]
F = KV["drah_vyska_nad_zemi_m"]                 # výška dráhy
B = H - KV["zapusteni_do_spalku_m"]             # spodek kovadliny
CX = KV["stred_x_m"]


# ------------------------------------------------------------------ textury Poly Haven
def stahni(aid, kanaly=("Diffuse", "nor_gl", "Rough", "Displacement")):
    for k in kanaly:
        p = os.path.join(TEX, f"{aid}_{k}.jpg")
        if os.path.exists(p):
            continue
        info = json.load(urllib.request.urlopen(f"https://api.polyhaven.com/files/{aid}"))
        urllib.request.urlretrieve(info[k]["2k"]["jpg"]["url"], p)


stahni("rust_coarse_01"); stahni("rough_wood")


def img(nazev, barva=True):
    p = os.path.join(TEX, nazev + ".jpg")
    i = bpy.data.images.load(p, check_existing=True)
    i.colorspace_settings.name = "sRGB" if barva else "Non-Color"
    return i


# ------------------------------------------------------------------ geometrie
def obj_z_bm(bm, jmeno):
    me = bpy.data.meshes.new(jmeno); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(jmeno, me); bpy.context.scene.collection.objects.link(o)
    return o


def superelipsa(hu, hv, p, n, faze=0.0):
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n + faze
        c, s = math.cos(t), math.sin(t)
        out.append((hu * math.copysign(abs(c) ** (2 / p), c), hv * math.copysign(abs(s) ** (2 / p), s)))
    return out


def loft(kruhy, jmeno):
    """kruhy: seznam seznamů bodů (stejný počet), uzavřené víčky na koncích."""
    bm = bmesh.new()
    vv = [[bm.verts.new(p) for p in k] for k in kruhy]
    n = len(kruhy[0])
    for a, b in zip(vv[:-1], vv[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(vv[0]))); bm.faces.new(vv[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_z_bm(bm, jmeno)


def loft_z(rezy, jmeno, n=96):
    """rezy (z, cx, cy, hx, hy, p) – vodorovné průřezy podél Z."""
    return loft([[Vector((cx + u, cy + v, z)) for u, v in superelipsa(hx, hy, p, n)] for z, cx, cy, hx, hy, p in rezy], jmeno)


def loft_x(rezy, jmeno, n=64):
    """rezy (x, cy, cz, hy, hz, p) – svislé průřezy podél X."""
    return loft([[Vector((x, cy + u, cz + v)) for u, v in superelipsa(hy, hz, p, n)] for x, cy, cz, hy, hz, p in rezy], jmeno)


def aktivni(o, *dalsi):
    bpy.ops.object.select_all(action="DESELECT")
    for d in dalsi:
        d.select_set(True)
    o.select_set(True); bpy.context.view_layer.objects.active = o


def aplikuj(o):
    aktivni(o)
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def spoj(objs, jmeno):
    aktivni(objs[0], *objs[1:]); bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = jmeno; o.data.name = jmeno
    return o


def odecti(o, rezaky):
    r = spoj(rezaky, "rezaky")
    m = o.modifiers.new("odecti", "BOOLEAN"); m.operation = "DIFFERENCE"; m.solver = "EXACT"; m.object = r
    m.use_self = True; m.use_hole_tolerant = True
    aplikuj(o); bpy.data.objects.remove(r)


def remesh(o, voxel, vyhlad=0, fakt=0.5):
    m = o.modifiers.new("rm", "REMESH"); m.mode = "VOXEL"; m.voxel_size = voxel; m.use_smooth_shade = True
    if vyhlad:
        s = o.modifiers.new("sm", "SMOOTH"); s.factor = fakt; s.iterations = vyhlad
    aplikuj(o)


def displace(o, typ, meritko, sila, skupina=None, stred=0.5, **kw):
    t = bpy.data.textures.new(f"t_{typ}_{meritko}", typ); t.noise_scale = meritko
    for k, v in kw.items():
        setattr(t, k, v)
    m = o.modifiers.new("d", "DISPLACE"); m.texture = t; m.strength = sila; m.mid_level = stred
    m.texture_coords = "GLOBAL"
    if skupina:
        m.vertex_group = skupina
    aplikuj(o)


def skupina_mimo_drahu(o):
    """váha 0 na dráze a horní ploše rohu (rovné, vyleštěné), 1 jinde – kování a důlky jen na bocích."""
    g = o.vertex_groups.new(name="boky")
    me = o.data
    for v in me.vertices:
        z, nz = v.co.z, v.normal.z
        w = 1.0
        if nz > 0.75 and z > F - 0.006:
            w = 0.0
        elif nz > 0.6 and z > F - 0.05 and v.co.x > CX + 0.18:
            w = 0.15
        g.add([v.index], w, "REPLACE")
    return g.name


def kovadlina_high():
    p = 6.0
    hl = KV["drah_delka_m"] / 2          # půl délky dráhy (bez patky a rohu)
    xb = CX - 0.06                       # střed těla (roh vpravo, patka vlevo)
    pa, ps = KV["pata_m"][0] / 2, KV["pata_m"][1] / 2
    wa, ws = KV["pas_m"][0] / 2, KV["pas_m"][1] / 2
    hw = KV["drah_sirka_m"] / 2
    h = F - B
    rezy = [(0.000, xb, 0, pa, ps, p), (0.040, xb, 0, pa - 0.004, ps - 0.004, p), (0.058, xb, 0, pa - 0.03, ps - 0.03, p),
            (0.085, xb, 0, wa + 0.05, ws + 0.035, p), (0.112, xb, 0, wa + 0.015, ws + 0.01, p), (0.150, xb, 0, wa, ws, p), (0.205, xb, 0, wa + 0.005, ws - 0.002, p),
            (0.250, xb + 0.01, 0, wa + 0.04, ws + 0.002, p), (0.290, xb + 0.02, 0, hl - 0.05, hw - 0.002, p),
            (h - 0.045, xb + 0.03, 0, hl - 0.02, hw, 8.0), (h - 0.002, xb + 0.03, 0, hl - 0.02, hw, 8.0),
            (h, xb + 0.03, 0, hl - 0.022, hw - 0.002, 8.0)]
    telo = loft_z([(B + z, cx, cy, hx, hy, pp) for z, cx, cy, hx, hy, pp in rezy], "telo")
    x_tela_l = xb + 0.03 - (hl - 0.02)   # levý konec dráhy na těle
    x_tela_p = xb + 0.03 + (hl - 0.02)
    # patka (heel): hranatá, dráha pokračuje, spodek se zvedá ke konci
    pd = KV["patka_delka_m"]
    pat = loft_x([(x_tela_l + 0.05, 0, F - 0.06, hw, 0.06, 8.0), (x_tela_l - pd * 0.6, 0, F - 0.042, hw, 0.042, 8.0),
                  (x_tela_l - pd + 0.003, 0, F - 0.034, hw - 0.002, 0.034, 8.0), (x_tela_l - pd, 0, F - 0.034, hw - 0.004, 0.031, 8.0)],
                 "patka")
    # roh: kónický, štíhne do špičky, horní hrana mírně pod dráhou a klesá; spodek (hrdlo) vybíhá z pasu konkávně
    L = KV["roh_delka_m"]
    xa = xb + 0.05; xt = x_tela_p + L
    bz0 = B + 0.16; top_t = F - 0.008 - 0.024; bt = top_t - 0.022
    rr = []
    for k in range(25):
        q = k / 24
        x = xa + (xt - xa) * q
        sr = min(1.0, max(0.0, (x - x_tela_p) / L))
        top = F - 0.004 if sr == 0 else F - 0.008 - 0.024 * sr ** 1.3
        bot = bz0 + (bt - bz0) * (1 - (1 - q) ** 2.4)
        hy = (hw - 0.004) * (1 - sr) ** 0.95 + 0.011
        if sr == 0:
            hy = ws + (hw - 0.004 - ws) * min(1.0, (x - xa) / max(1e-3, x_tela_p - xa)) ** 0.5
        hz = max(0.011, (top - bot) / 2)
        rr.append((x, 0, top - hz, hy, hz, 3.4 - 1.2 * sr))
    roh = loft_x(rr, "roh")
    o = spoj([telo, pat, roh], "kovadlina_high")
    remesh(o, 0.004)
    # odečíst: oblouky mezi patkami, otvor pro sperhák (hranatý) a průbojník (kulatý) v patce, otlučené hrany
    rez = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.12, depth=1.0, location=(xb, 0, B - 0.058), rotation=(math.pi / 2, 0, 0))
    rez.append(bpy.context.object)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.095, depth=1.0, location=(xb, 0, B - 0.05), rotation=(0, math.pi / 2, 0))
    rez.append(bpy.context.object)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_tela_l - pd * 0.62, 0, F - 0.05)); c = bpy.context.object
    c.scale = (0.026, 0.026, 0.14); rez.append(c)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0085, depth=0.14, location=(x_tela_l - pd * 0.22, 0, F - 0.05))
    rez.append(bpy.context.object)
    # otlučené hrany dráhy a patky (koule na obvodu dráhy, víc u konců – tam se kove nejvíc)
    for i in range(16):
        strana = random.choice((-1, 1))
        x = random.uniform(x_tela_l - pd + 0.01, x_tela_p - 0.01)
        if random.random() < 0.35:
            x = random.choice((x_tela_l - pd + random.uniform(0.0, 0.05), x_tela_p - random.uniform(0.0, 0.06)))
        r = random.uniform(0.003, 0.0085)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r,
                                             location=(x, strana * (hw - 0.002 + r * 0.35), F - 0.001 + r * 0.25))
        sk = bpy.context.object; sk.scale = (random.uniform(1.0, 2.2), 1.0, random.uniform(0.6, 1.0)); rez.append(sk)
    for xk in (x_tela_l - pd, ):                  # čelo patky
        for i in range(3):
            r = random.uniform(0.004, 0.008)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r,
                                                 location=(xk - r * 0.3, random.uniform(-hw, hw), F - 0.002))
            rez.append(bpy.context.object)
    odecti(o, rez)
    remesh(o, 0.0018, vyhlad=3, fakt=0.5)
    g = skupina_mimo_drahu(o)
    displace(o, "CLOUDS", 0.09, 0.004, g, noise_depth=2)           # nerovnosti kování (vlny po kladivu)
    displace(o, "VORONOI", 0.02, -0.0006, g, stred=0.5, distance_metric="DISTANCE")    # ploché fazety po kladivu
    displace(o, "CLOUDS", 0.005, 0.00025, g, noise_depth=1)        # jemný povrch okují
    return o, (x_tela_l - pd, x_tela_p + L), hw


def sperhak_high():
    x0, y0 = SH["poloha_m"]
    hp, hs = SH["pata_m"] / 2, SH["sloupek_m"] / 2
    v = SH["vyska_nad_spalkem_m"]
    rezy = [(H - 0.03, hp, hp, 8.0), (H + 0.045, hp, hp, 8.0), (H + 0.055, hp - 0.006, hp - 0.006, 8.0),
            (H + 0.07, hs, hs, 8.0), (H + v - 0.075, hs, hs, 8.0), (H + v - 0.055, hs + 0.008, hs + 0.002, 6.0),
            (H + v - 0.03, hs + 0.01, hs - 0.004, 5.0), (H + v - 0.006, hs + 0.004, 0.007, 4.0), (H + v, hs - 0.004, 0.003, 3.0)]
    o = loft_z([(z, x0, y0, hx, hy, p) for z, hx, hy, p in rezy], "sperhak_high", n=64)
    remesh(o, 0.0015, vyhlad=3, fakt=0.5)
    g = o.vertex_groups.new(name="v"); g.add([v.index for v in o.data.vertices], 1.0, "REPLACE")
    displace(o, "CLOUDS", 0.03, 0.0015, "v", noise_depth=2)
    displace(o, "VORONOI", 0.008, -0.0007, "v", distance_metric="DISTANCE")
    return o


def r_spalku(t, z=0.0, sin=math.sin):
    """poloměr špalku v úhlu t (nepravidelný dubový kmen), dole mírný náběh."""
    r = R0 * (1 + 0.035 * sin(2 * t + 0.4) + 0.028 * sin(3 * t + 0.7) + 0.02 * sin(5 * t + 2.1) + 0.012 * sin(9 * t + 0.3)
              + 0.007 * sin(17 * t + 1.0) + 0.004 * sin(29 * t + 2.0))
    return r + 0.02 * max(0.0, 1 - z / 0.08) ** 2 - 0.006 * z / H


DLAZD = 6                      # boky špalku: 6 dlaždic po 60° (atlas dřeva 2 řady × 3)
T_UV = 0.245                   # velikost dlaždice v UV (0,5 m → ~1000 px/m při 2048)
DISK = (0.0025, 0.5025, 0.49, 1.04)   # u0, v0, velikost v UV, velikost v m (čelo špalku)
S_BOK = (H - FIL) + FIL * math.pi / 2   # délka profilu boku (zem → zaoblení → čelo)


def uv_bok(t_index_frac, s):
    """t_index_frac = úhel v dlaždicích (0..6), s = délka profilu od země (m) → UV atlasu dřeva."""
    k = min(int(t_index_frac), DLAZD - 1)
    fu = t_index_frac - k
    radek, sl = divmod(k, 3)
    return (sl * 0.25 + 0.0025 + fu * T_UV, radek * 0.25 + 0.0025 + s / 0.5 * T_UV)


def uv_disk(x, y):
    u0, v0, w, m = DISK
    return (u0 + (x + m / 2) / m * w, v0 + (y + m / 2) / m * w)


def vyska_cela(x, y):
    return H + 0.003 * math.sin(7 * x + 1.3) * math.sin(5 * y + 0.4) + 0.002 * math.sin(13 * x - 9 * y)


def spalek(n=96, zbok=(0, 0.02, 0.05, 0.09, 0.14, 0.20, 0.26, 0.31, 0.345), nfil=5, krouzky=(0.88, 0.72, 0.55, 0.38, 0.22, 0.09)):
    bm = bmesh.new()
    uvb = bm.loops.layers.uv.new("bake"); uvt = bm.loops.layers.uv.new("tex")
    prof = []                                   # (z, dr, s) podél profilu boku
    for z in zbok:
        prof.append((z, 0.0, z))
    for k in range(nfil + 1):
        a = k / nfil * math.pi / 2
        prof.append((H - FIL + FIL * math.sin(a), -FIL + FIL * math.cos(a), (H - FIL) + FIL * a))
    rows = []
    for z, dr, s in prof:
        row = []
        for i in range(n):
            t = 2 * math.pi * i / n
            r = r_spalku(t, z) + dr
            zz = z if dr == 0.0 else min(z, vyska_cela(r * math.cos(t), r * math.sin(t)) + (z - H))
            row.append(bm.verts.new((r * math.cos(t), r * math.sin(t), zz)))
        rows.append((row, s))
    for (ra, sa), (rb, sb) in zip(rows[:-1], rows[1:]):
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
            ti, tj = i / n * DLAZD, (i + 1) / n * DLAZD
            kt = min(int(ti + 1e-9), DLAZD - 1)
            radek, sl = divmod(kt, 3)
            for lp, (tt, ss) in zip(f.loops, ((ti, sa), (tj, sa), (tj, sb), (ti, sb))):
                lp[uvb].uv = (sl * 0.25 + 0.0025 + (tt - kt) * T_UV, radek * 0.25 + 0.0025 + ss / 0.5 * T_UV)
                lp[uvt].uv = (tt, ss / 0.5)
    # čelo: soustředné kroužky k dřeni
    okraj = rows[-1][0]
    prev = okraj
    for q in krouzky:
        row = []
        for i in range(n):
            t = 2 * math.pi * i / n
            r = (r_spalku(t, H) - FIL) * q
            x, y = r * math.cos(t), r * math.sin(t)
            row.append(bm.verts.new((x, y, vyska_cela(x, y))))
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((prev[i], prev[j], row[j], row[i]))
        prev = row
    c = bm.verts.new((0, 0, vyska_cela(0, 0)))
    for i in range(n):
        bm.faces.new((prev[i], prev[(i + 1) % n], c))
    n_bok = len(bm.faces) - (len(krouzky) * n + n)
    bm.faces.ensure_lookup_table()
    for f in list(bm.faces)[n_bok:]:
        for lp in f.loops:
            x, y = lp.vert.co.x, lp.vert.co.y
            lp[uvb].uv = uv_disk(x, y); lp[uvt].uv = (x, y)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_z_bm(bm, "spalek")
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def obruc(n=96, tl=0.006):
    """železný pásek u horní hrany špalku (KCD1), přibitý hřeby."""
    z0 = H - SP["obruc_od_vrchu_m"] - SP["obruc_sirka_m"]; z1 = z0 + SP["obruc_sirka_m"]
    bm = bmesh.new()
    prof = [(z0, -0.003), (z0, tl - 0.003), (z1, tl - 0.003), (z1, -0.003)]
    rows = []
    for z, dr in prof:
        rows.append([bm.verts.new(((r_spalku(2 * math.pi * i / n, z) + dr) * math.cos(2 * math.pi * i / n),
                                   (r_spalku(2 * math.pi * i / n, z) + dr) * math.sin(2 * math.pi * i / n), z)) for i in range(n)])
    for a, b in zip(rows, rows[1:] + rows[:1]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    # hřeby (kovaná hlava)
    for k in range(7):
        t = 2 * math.pi * (k + 0.3) / 7
        z = (z0 + z1) / 2
        r = r_spalku(t, z) + tl - 0.003
        geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.0075, radius2=0.004, depth=0.005)
        vs = geom["verts"]
        bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=__import__("mathutils").Matrix.Rotation(math.pi / 2, 3, "Y"))
        bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=__import__("mathutils").Matrix.Rotation(t, 3, "Z"))
        bmesh.ops.translate(bm, verts=vs, vec=(r * math.cos(t), r * math.sin(t), z))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_z_bm(bm, "obruc")
    return o


def kramle(xb, hw_pata):
    """kramle (psí skoby) přes patky kovadliny – drží kovadlinu ve špalku."""
    objs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = xb + sx * 0.15
            cu = bpy.data.curves.new("kr", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0055; cu.bevel_resolution = 1
            sp = cu.splines.new("POLY"); pts = [(x, sy * (hw_pata + 0.026), H - 0.03), (x, sy * (hw_pata + 0.026), H + 0.05),
                                              (x, sy * (hw_pata - 0.012), H + 0.047)]
            sp.points.add(len(pts) - 1)
            for p, c in zip(sp.points, pts):
                p.co = (*c, 1)
            o = bpy.data.objects.new("kr", cu); bpy.context.scene.collection.objects.link(o)
            aktivni(o); bpy.ops.object.convert(target="MESH"); objs.append(bpy.context.object)
    return spoj(objs, "kramle")


def decimuj(o, cil):
    n = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if n <= cil:
        return o
    m = o.modifiers.new("dec", "DECIMATE"); m.ratio = cil / n; m.use_collapse_triangulate = True
    aplikuj(o)
    return o


def troj(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def kopie(o, jmeno):
    c = o.copy(); c.data = o.data.copy(); c.name = jmeno; bpy.context.scene.collection.objects.link(c)
    return c


# ------------------------------------------------------------------ uzly materiálu
class Uzly:
    def __init__(s, mat):
        mat.use_nodes = True; s.nt = mat.node_tree; s.n = s.nt.nodes; s.l = s.nt.links
        s.n.clear()

    def u(s, typ, **kw):
        x = s.n.new(typ)
        for k, v in kw.items():
            setattr(x, k, v)
        return x

    def ln(s, a, b):
        s.l.new(a, b)

    def math(s, op, a, b=None, clamp=False):
        m = s.u("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                s.ln(v, m.inputs[i])
        return m.outputs[0]

    def mr(s, v, a, b, c=0.0, d=1.0):
        m = s.u("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
        if isinstance(v, (int, float)):
            m.inputs[0].default_value = v
        else:
            s.ln(v, m.inputs[0])
        m.inputs[1].default_value, m.inputs[2].default_value, m.inputs[3].default_value, m.inputs[4].default_value = a, b, c, d
        return m.outputs[0]

    def mix(s, f, a, b, blend="MIX"):
        m = s.u("ShaderNodeMix", data_type="RGBA", blend_type=blend, clamp_result=True)
        for sock, v in ((m.inputs[0], f), (m.inputs[6], a), (m.inputs[7], b)):
            if isinstance(v, (int, float)) and sock.type == "RGBA":
                sock.default_value = (v, v, v, 1.0)
            elif isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = (*v, 1.0)
            else:
                s.ln(v, sock)
        return m.outputs[2]

    def obr(s, image, vektor=None, box=False, uv=None):
        t = s.u("ShaderNodeTexImage", image=image)
        if box:
            t.projection = "BOX"; t.projection_blend = 0.3
        if uv:
            m = s.u("ShaderNodeUVMap", uv_map=uv); s.ln(m.outputs[0], t.inputs[0])
        elif vektor is not None:
            s.ln(vektor, t.inputs[0])
        return t


def bake_obr(jmeno, barva=False, px=None):
    i = bpy.data.images.new(jmeno, px or PX, px or PX, alpha=False, float_buffer=not barva)
    i.colorspace_settings.name = "sRGB" if barva else "Non-Color"
    return i


# ------------------------------------------------------------------ materiál železa (pro zapečení, na high-poly)
def mat_zelezo_autorsky():
    mat = bpy.data.materials.new("zelezo_autor"); U = Uzly(mat)
    geo = U.u("ShaderNodeNewGeometry")
    xyz = U.u("ShaderNodeSeparateXYZ"); U.ln(geo.outputs["Position"], xyz.inputs[0])
    nxyz = U.u("ShaderNodeSeparateXYZ"); U.ln(geo.outputs["Normal"], nxyz.inputs[0])
    tc = U.u("ShaderNodeTexCoord")
    mp = U.u("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (2.6, 2.6, 2.6); U.ln(tc.outputs["Object"], mp.inputs[0])
    rD = U.obr(img("rust_coarse_01_Diffuse"), mp.outputs[0], box=True)
    rH = U.obr(img("rust_coarse_01_Displacement", False), mp.outputs[0], box=True)
    rR = U.obr(img("rust_coarse_01_Rough", False), mp.outputs[0], box=True)
    z, nz, x = xyz.outputs[2], nxyz.outputs[2], xyz.outputs[0]
    ao = U.u("ShaderNodeAmbientOcclusion", samples=16, only_local=False); ao.inputs["Distance"].default_value = 0.05
    ao_f = ao.outputs["AO"]
    # masky
    draha = U.math("MULTIPLY", U.mr(z, F - 0.0045, F - 0.0012), U.mr(nz, 0.82, 0.95))
    roh_vrch = U.math("MULTIPLY", U.math("MULTIPLY", U.mr(nz, 0.35, 0.85), U.mr(z, F - 0.075, F - 0.02)), U.mr(x, CX + 0.18, CX + 0.24))
    sp_vrch = U.math("MULTIPLY", U.mr(z, H + SH["vyska_nad_spalkem_m"] - 0.03, H + SH["vyska_nad_spalkem_m"] - 0.005),
                     U.mr(x, SH["poloha_m"][0] + 0.09, SH["poloha_m"][0] + 0.06))
    lesk = U.math("MAXIMUM", draha, U.math("MULTIPLY", U.math("MAXIMUM", roh_vrch, sp_vrch), 0.85))
    hrana = U.mr(geo.outputs["Pointiness"], 0.53, 0.64)
    pas_hor = U.math("MULTIPLY", U.mr(z, F - 0.05, F - 0.003), 0.55)          # horní pás boků ohlazený prací
    opotr = U.math("MINIMUM", U.math("MAXIMUM", hrana, pas_hor), U.math("SUBTRACT", 1.0, lesk), clamp=True)
    sum1 = U.u("ShaderNodeTexNoise"); sum1.inputs["Scale"].default_value = 11.0; sum1.inputs["Detail"].default_value = 8.0
    sum1.inputs["Roughness"].default_value = 0.62; U.ln(geo.outputs["Position"], sum1.inputs["Vector"])
    sum2 = U.u("ShaderNodeTexNoise"); sum2.inputs["Scale"].default_value = 38.0; sum2.inputs["Detail"].default_value = 4.0
    U.ln(geo.outputs["Position"], sum2.inputs["Vector"])
    dutiny = U.math("SUBTRACT", 1.0, ao_f, clamp=True)
    rez_zaklad = U.mr(sum1.outputs["Fac"], 0.50, 0.66)
    u_dreva = U.mr(z, B + 0.09, B + 0.005, 0.0, 0.55)                           # vlhko od dřeva
    pas_k = U.math("MULTIPLY", U.mr(z, B + 0.10, B + 0.13), U.mr(z, B + 0.24, B + 0.20))   # jemná rez v pasu
    dal = U.math("MULTIPLY", U.mr(U.math("ADD", U.math("POWER", x, 2.0), U.math("POWER", xyz.outputs[1], 2.0)),
                                  0.40 ** 2, 0.44 ** 2), 0.35)                  # pásek a kramle venku víc
    rez = U.math("ADD", U.math("MULTIPLY", rez_zaklad, U.math("ADD", 0.35, U.math("MULTIPLY", dutiny, 1.6))),
                 U.math("ADD", U.math("ADD", u_dreva, U.math("MULTIPLY", pas_k, 0.35)), dal))
    rez = U.math("MULTIPLY", rez, U.math("SUBTRACT", 1.0, U.math("MAXIMUM", lesk, U.math("MULTIPLY", hrana, 0.8))), clamp=True)
    # barvy
    okuje = U.mix(0.35, (0.040, 0.039, 0.040), rD.outputs[0], "MULTIPLY")
    okuje = U.mix(U.math("MULTIPLY", sum2.outputs["Fac"], 0.5), okuje, (0.055, 0.050, 0.046))
    rez_b = U.mix(0.25, rD.outputs[0], (0.20, 0.11, 0.06), "MULTIPLY")
    rez_b = U.mix(0.5, rez_b, rD.outputs[0])
    skr = U.u("ShaderNodeMapping"); skr.inputs["Scale"].default_value = (3.0, 160.0, 3.0); U.ln(geo.outputs["Position"], skr.inputs[0])
    skr_n = U.u("ShaderNodeTexNoise"); skr_n.inputs["Scale"].default_value = 1.6; skr_n.inputs["Detail"].default_value = 3.0
    U.ln(skr.outputs[0], skr_n.inputs["Vector"])
    skrab = U.mr(skr_n.outputs["Fac"], 0.56, 0.68)
    jamky = U.mr(rH.outputs[0], 0.30, 0.18)
    lesk_b = U.mix(U.math("MULTIPLY", skrab, 0.25), (0.52, 0.515, 0.50), (0.62, 0.62, 0.61))
    lesk_b = U.mix(U.math("MULTIPLY", jamky, 0.7), lesk_b, (0.16, 0.15, 0.14))
    hrana_b = U.mix(U.math("MULTIPLY", sum2.outputs["Fac"], 0.4), (0.25, 0.245, 0.24), (0.33, 0.325, 0.32))
    alb = U.mix(rez, okuje, rez_b)
    alb = U.mix(opotr, alb, hrana_b)
    alb = U.mix(lesk, alb, lesk_b)
    alb = U.mix(U.math("SUBTRACT", 1.0, U.math("ADD", 0.45, U.math("MULTIPLY", ao_f, 0.55))), alb, (0, 0, 0))
    # drsnost a kov
    dr_ok = U.math("ADD", 0.50, U.math("MULTIPLY", rR.outputs[0], 0.25))
    dr = U.mix(rez, dr_ok, 0.9)
    dr = U.mix(opotr, dr, 0.42)
    dr = U.mix(lesk, dr, U.math("ADD", 0.16, U.math("MULTIPLY", skrab, 0.22)))
    kov = U.mix(rez, 0.55, 0.0)
    kov = U.mix(opotr, kov, 0.88)
    kov = U.mix(lesk, kov, 1.0)
    # reliéf
    vyska = U.math("MULTIPLY", rH.outputs[0], U.math("SUBTRACT", 1.0, U.math("MULTIPLY", lesk, 0.9)))
    vyska = U.math("ADD", vyska, U.math("MULTIPLY", rez, U.math("MULTIPLY", sum2.outputs["Fac"], 0.6)))
    vyska = U.math("SUBTRACT", vyska, U.math("MULTIPLY", U.math("MULTIPLY", skrab, lesk), 0.08))
    bump = U.u("ShaderNodeBump"); bump.inputs["Strength"].default_value = 1.0; bump.inputs["Distance"].default_value = 0.0007
    U.ln(vyska, bump.inputs["Height"])
    bsdf = U.u("ShaderNodeBsdfPrincipled"); U.ln(alb, bsdf.inputs["Base Color"]); U.ln(dr, bsdf.inputs["Roughness"])
    U.ln(kov, bsdf.inputs["Metallic"]); U.ln(bump.outputs[0], bsdf.inputs["Normal"])
    em = U.u("ShaderNodeEmission"); out = U.u("ShaderNodeOutputMaterial")
    U.ln(bsdf.outputs[0], out.inputs[0])
    return mat, {"albedo": alb, "drsnost": dr, "kov": kov}, (U, bsdf, em, out)


# ------------------------------------------------------------------ textura čela špalku (numpy, v prostoru atlasu)
def _sum(shape, bunky, seed):
    r = np.random.default_rng(seed)
    g = r.random((bunky + 2, bunky + 2))
    h, w = shape
    yy = np.linspace(0, bunky, h); xx = np.linspace(0, bunky, w)
    y0 = np.floor(yy).astype(int); x0 = np.floor(xx).astype(int)
    fy = yy - y0; fx = xx - x0
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy[:, None]) + (c * (1 - fx) + d * fx) * fy[:, None]


def fbm(shape, bunky, seed, okt=5):
    s = np.zeros(shape); a = 1.0; t = 0.0
    for o in range(okt):
        s += a * _sum(shape, bunky * 2 ** o, seed + o); t += a; a *= 0.5
    return s / t


def textura_dreva(anvil_rect, sperhak_xy):
    """RGB: na čele barva dřeva (letokruhy, dřeňové paprsky, trhliny, okuje, spáleniny), na bocích násobič
    (trhliny, saze nahoře, hlína dole); výška: reliéf pro normálu. Vše v prostoru UV atlasu dřeva."""
    W = PX
    vv, uu = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(W) + 0.5) / W, indexing="ij")   # řádek = v
    rgb = np.ones((W, W, 3)); vys = np.full((W, W), 0.5)
    sumA = fbm((W, W), 6, 11); sumB = fbm((W, W), 24, 12, 4); sumC = fbm((W, W), 90, 13, 3)
    # trhliny (výsušné, radiální od obvodu k dřeni) – sdílené čelem i boky
    trh = []
    for k in range(11):
        t = 2 * math.pi * k / 11 + RNG.uniform(-0.2, 0.2)
        trh.append((t, RNG.uniform(0.10, 0.36), RNG.uniform(0.003, 0.0075), RNG.uniform(0.06, 0.30), RNG.uniform(0, 6)))
    # --- čelo
    u0, v0, w, m = DISK
    x = (uu - u0) / w * m - m / 2; y = (vv - v0) / w * m - m / 2
    disk = (uu >= u0 - 0.002) & (uu <= u0 + w + 0.002) & (vv >= v0 - 0.002) & (vv <= v0 + w + 0.002)
    px_, py_ = 0.045, -0.032                                    # dřeň mimo střed
    dx, dy = x - px_, y - py_
    r = np.hypot(dx, dy); fi = np.arctan2(dy, dx)
    tt = np.arctan2(y, x); rr = np.hypot(x, y)
    rmax = r_spalku(tt, H, np.sin) - FIL
    rp = r * (1 + 0.035 * np.sin(3 * fi + 2.0) + 0.02 * np.sin(5 * fi + 0.5)) + 0.004 * (sumA - 0.5)
    roky = rp / 0.0034 + 3.0 * np.sin(rp * 21.0)
    fr = roky - np.floor(roky)
    pozdni = np.clip((fr - 0.55) / 0.2, 0, 1) * np.clip((1.0 - fr) / 0.1, 0, 1)
    jarni_p = np.clip(1 - np.abs(fr - 0.05) / 0.06, 0, 1)          # póry jarního dřeva (dub – kruhovitě pórovitý)
    zakl = np.stack([0.33 + 0.0 * r, 0.255 + 0.0 * r, 0.185 + 0.0 * r], -1)
    pozd_c = np.array([0.215, 0.160, 0.115])
    col = zakl * (1 - pozdni[..., None]) + pozd_c * pozdni[..., None]
    col *= (1 - 0.25 * jarni_p * (sumC > 0.45))[..., None]
    # dřeňové paprsky (dub): tenké světlé radiální čárky
    b = (fi / (2 * np.pi) + 0.5) * 900
    bi = np.floor(b).astype(int) % 900
    rnd = np.random.default_rng(5).random((900, 3))
    pap = (np.abs(b - np.floor(b) - 0.5) < 0.09 + 0.05 * rnd[bi, 2]) & (rnd[bi, 0] > 0.55) & \
          (r > 0.03 + 0.35 * rnd[bi, 1]) & (r < rmax * (0.75 + 0.25 * rnd[bi, 1]))
    col = np.where(pap[..., None], col * 1.22 + 0.02, col)
    # běl a obvod (zešedlé, ohlazené)
    bel = np.clip((r - (rmax - 0.045)) / 0.02, 0, 1)
    col = col * (1 - bel[..., None] * 0.4) + np.array([0.36, 0.33, 0.29]) * bel[..., None] * 0.4
    # stáří, saze, špína (KCD2: tmavé, ohlazené)
    col *= (0.62 + 0.30 * sumA + 0.12 * sumB)[..., None]
    # kolem kovadliny: saze, okuje (černé šupinky), spáleniny od žhavého železa
    ax0, ax1, ay = anvil_rect
    ddx = np.maximum(np.maximum(ax0 - x, x - ax1), 0); ddy = np.maximum(np.abs(y) - ay, 0)
    dk = np.hypot(ddx, ddy)
    saze = np.clip(1 - dk / 0.22, 0, 1) ** 1.5
    col *= (1 - 0.35 * saze)[..., None]
    okuje = (RNG.random((W, W)) < (0.004 + 0.05 * saze)) & disk
    from_ = okuje.copy()
    for sh in ((0, 1), (1, 0), (1, 1)):
        from_ |= np.roll(okuje, sh, (0, 1)) & (RNG.random((W, W)) < 0.6)
    col = np.where(from_[..., None], np.array([0.05, 0.045, 0.042]), col)
    vys = np.where(from_, 0.62, vys)
    for k in range(4):                                           # spáleniny (odložené žhavé kusy)
        cx_, cy_ = RNG.uniform(ax1 - 0.05, ax1 + 0.15), RNG.uniform(-0.30, 0.30)
        if k == 3:
            cx_, cy_ = RNG.uniform(-0.25, 0.0), RNG.uniform(0.20, 0.32)
        sp = np.hypot((x - cx_) * RNG.uniform(0.6, 1.4), y - cy_) / RNG.uniform(0.025, 0.05)
        sp_m = np.clip(1.2 - sp, 0, 1) * (0.6 + 0.4 * sumC)
        col *= (1 - 0.75 * np.clip(sp_m, 0, 1))[..., None]
    # důlky po kladivu a sekáči na čele
    for k in range(40):
        cx_, cy_ = RNG.uniform(-0.4, 0.4), RNG.uniform(-0.4, 0.4)
        d = np.hypot(x - cx_, (y - cy_)) / RNG.uniform(0.004, 0.012)
        vys -= 0.18 * np.clip(1 - d, 0, 1)
    # trhliny na čele
    tr_m = np.zeros((W, W))
    for t, delka, sir, bok, fz in trh:
        dt = np.angle(np.exp(1j * (tt - t - 0.03 * np.sin(rr * 30 + fz))))
        prc = np.abs(dt) * rr
        od_okr = rmax - rr
        sir_r = sir * np.clip(1 - od_okr / delka, 0, 1) ** 0.7
        tr_m = np.maximum(tr_m, np.clip(1 - prc / np.maximum(sir_r, 1e-5), 0, 1) * (od_okr < delka))
    for k in range(3):                                           # srdcová trhlina od dřeně
        t = RNG.uniform(0, 2 * np.pi)
        dt = np.angle(np.exp(1j * (fi - t))); prc = np.abs(dt) * r
        sir_r = 0.0035 * np.clip(1 - r / 0.07, 0, 1)
        tr_m = np.maximum(tr_m, np.clip(1 - prc / np.maximum(sir_r, 1e-5), 0, 1))
    col = col * (1 - 0.88 * tr_m[..., None])
    vys = vys + 0.18 * pozdni - 0.07 * jarni_p - 0.55 * tr_m + 0.06 * (sumB - 0.5)
    rgb = np.where(disk[..., None], col, rgb)
    vys_all = np.where(disk, vys, 0.5)
    # --- boky (násobič barvy rough_wood)
    for k in range(DLAZD):
        radek, sl = divmod(k, 3)
        bu0 = sl * 0.25 + 0.0025; bv0 = radek * 0.25 + 0.0025
        sel = (uu >= bu0 - 0.002) & (uu <= bu0 + T_UV + 0.002) & (vv >= bv0 - 0.002) & (vv <= bv0 + T_UV + 0.002)
        tdl = (k + (uu - bu0) / T_UV) * 2 * np.pi / DLAZD
        s = (vv - bv0) / T_UV * 0.5
        mul = (0.50 + 0.25 * sumA + 0.1 * sumB)
        mul = mul * (1 - 0.35 * np.clip((s - (S_BOK - 0.10)) / 0.08, 0, 1))      # saze u horní hrany
        mul = mul * (1 - 0.25 * np.clip((0.06 - s) / 0.06, 0, 1))               # hlína a vlhko dole
        trm = np.zeros((W, W))
        for t, delka, sir, bok, fz in trh:
            dt = np.angle(np.exp(1j * (tdl - t)))
            prc = np.abs(dt) * R0 + 0.002 * np.sin(s * 40 + fz)
            od_vrchu = S_BOK - s
            sir_r = sir * np.clip(1 - od_vrchu / bok, 0, 1) ** 0.8
            trm = np.maximum(trm, np.clip(1 - prc / np.maximum(sir_r, 1e-5), 0, 1) * (od_vrchu < bok))
        tint = np.stack([mul, mul * 0.93, mul * 0.84], -1) * (1 - 0.85 * trm[..., None])
        rgb = np.where(sel[..., None], tint, rgb)
        vys_all = np.where(sel, 0.5 - 0.5 * trm + 0.05 * (sumB - 0.5), vys_all)
    return rgb, vys_all


def np_do_obr(jmeno, pole, barva):
    W = pole.shape[0]
    i = bpy.data.images.new(jmeno, W, W, alpha=False, float_buffer=False)
    i.colorspace_settings.name = "sRGB" if barva else "Non-Color"
    if pole.ndim == 2:
        pole = np.repeat(pole[..., None], 3, -1)
    rgba = np.concatenate([np.clip(pole, 0, 1), np.ones(pole.shape[:2] + (1,))], -1).astype(np.float32)
    i.pixels.foreach_set(rgba.ravel())
    i.filepath_raw = os.path.join(PRAC, jmeno + ".png"); i.file_format = "PNG"; i.save()
    return i


def mat_drevo_autorsky(prekryv, vyska):
    mat = bpy.data.materials.new("drevo_autor"); U = Uzly(mat)
    uvb = U.u("ShaderNodeUVMap", uv_map="bake")
    sepb = U.u("ShaderNodeSeparateXYZ"); U.ln(uvb.outputs[0], sepb.inputs[0])
    celo = U.math("MULTIPLY", U.math("GREATER_THAN", sepb.outputs[1], 0.5), U.math("LESS_THAN", sepb.outputs[0], 0.5))
    uvt = U.u("ShaderNodeUVMap", uv_map="tex")
    mp = U.u("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 1.0, 1.0); U.ln(uvt.outputs[0], mp.inputs[0])
    wD = U.obr(img("rough_wood_Diffuse"), mp.outputs[0]); wR = U.obr(img("rough_wood_Rough", False), mp.outputs[0])
    wN = U.obr(img("rough_wood_nor_gl", False), mp.outputs[0])
    pr = U.obr(prekryv, uvb.outputs[0]); vy = U.obr(vyska, uvb.outputs[0])
    ao = U.u("ShaderNodeAmbientOcclusion", samples=16, only_local=False); ao.inputs["Distance"].default_value = 0.12
    bok = U.mix(1.0, wD.outputs[0], pr.outputs[0], "MULTIPLY")
    bok = U.mix(0.35, bok, (0.30, 0.27, 0.24), "SATURATION")
    alb = U.mix(celo, bok, pr.outputs[0])
    alb = U.mix(U.math("SUBTRACT", 1.0, U.math("ADD", 0.5, U.math("MULTIPLY", ao.outputs["AO"], 0.5))), alb, (0, 0, 0))
    dr = U.mix(celo, U.math("ADD", 0.25, U.math("MULTIPLY", wR.outputs[0], 0.75)), U.math("ADD", 0.58, U.math("MULTIPLY", vy.outputs[0], 0.25)))
    nm = U.u("ShaderNodeNormalMap", uv_map="tex"); nm.inputs["Strength"].default_value = 1.0; U.ln(wN.outputs[0], nm.inputs["Color"])
    bump = U.u("ShaderNodeBump"); bump.inputs["Distance"].default_value = 0.004; bump.inputs["Strength"].default_value = 1.0
    U.ln(vy.outputs[0], bump.inputs["Height"])
    nmix = U.u("ShaderNodeMix", data_type="VECTOR"); U.ln(celo, nmix.inputs[0]); U.ln(nm.outputs[0], nmix.inputs[4])
    geo = U.u("ShaderNodeNewGeometry"); U.ln(geo.outputs["Normal"], nmix.inputs[5])
    U.ln(nmix.outputs[1], bump.inputs["Normal"])
    bsdf = U.u("ShaderNodeBsdfPrincipled"); U.ln(alb, bsdf.inputs["Base Color"]); U.ln(dr, bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = 0.0; U.ln(bump.outputs[0], bsdf.inputs["Normal"])
    em = U.u("ShaderNodeEmission"); out = U.u("ShaderNodeOutputMaterial"); U.ln(bsdf.outputs[0], out.inputs[0])
    return mat, {"albedo": alb, "drsnost": dr}, (U, bsdf, em, out)


# ------------------------------------------------------------------ pečení
def nastav_cycles():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = A.vzorky
    sc.cycles.use_denoising = False
    sc.render.bake.margin = 8
    if sc.world is None:
        sc.world = bpy.data.worlds.new("svet")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    sc.world.light_settings.distance = 0.2


def cil_obr(o, image):
    """obrázek jako aktivní uzel ve všech materiálech cíle"""
    for ms in o.material_slots:
        nt = ms.material.node_tree
        t = nt.nodes.get("_cil") or nt.nodes.new("ShaderNodeTexImage")
        t.name = "_cil"; t.image = image
        for nn in nt.nodes:
            nn.select = False
        t.select = True; nt.nodes.active = t


def peč(typ, low, high=None, **kw):
    if high:
        aktivni(low, *high)
        bpy.ops.object.bake(type=typ, use_selected_to_active=True, cage_extrusion=0.012, max_ray_distance=0.03, **kw)
    else:
        aktivni(low)
        bpy.ops.object.bake(type=typ, use_selected_to_active=False, **kw)


def emit_kanal(mat_info, kanal):
    U, bsdf, em, out = mat_info[2]
    U.ln(mat_info[1][kanal], em.inputs["Color"]); U.ln(em.outputs[0], out.inputs[0])


def uloz(i, jmeno):
    i.filepath_raw = os.path.join(PRAC, jmeno + ".png"); i.file_format = "PNG"; i.save()
    return i


def pixely(i):
    a = np.empty(i.size[0] * i.size[1] * 4, np.float32); i.pixels.foreach_get(a)
    return a.reshape(i.size[1], i.size[0], 4)


def orm(jmeno, ao, dr, kov=None):
    a = pixely(ao); d = pixely(dr)
    k = pixely(kov) if kov is not None else np.zeros_like(a)
    out = np.stack([a[..., 0], d[..., 0], k[..., 0]], -1)
    return np_do_obr(jmeno, out[::1], False)


def mat_finalni(jmeno, alb, nor, orm_i):
    mat = bpy.data.materials.new(jmeno); U = Uzly(mat)
    out = U.u("ShaderNodeOutputMaterial"); bsdf = U.u("ShaderNodeBsdfPrincipled"); U.ln(bsdf.outputs[0], out.inputs[0])
    ta = U.u("ShaderNodeTexImage", image=alb); U.ln(ta.outputs[0], bsdf.inputs["Base Color"])
    tn = U.u("ShaderNodeTexImage", image=nor); nm = U.u("ShaderNodeNormalMap"); U.ln(tn.outputs[0], nm.inputs["Color"])
    U.ln(nm.outputs[0], bsdf.inputs["Normal"])
    to = U.u("ShaderNodeTexImage", image=orm_i); sep = U.u("ShaderNodeSeparateColor"); U.ln(to.outputs[0], sep.inputs[0])
    U.ln(sep.outputs[1], bsdf.inputs["Roughness"]); U.ln(sep.outputs[2], bsdf.inputs["Metallic"])
    g = bpy.data.node_groups.get("glTF Material Output")
    if g is None:
        g = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    gn = U.u("ShaderNodeGroup"); gn.node_tree = g; U.ln(sep.outputs[0], gn.inputs["Occlusion"])
    return mat


def zmensi(i, px, jmeno):
    c = i.copy(); c.name = jmeno; c.scale(px, px)
    c.filepath_raw = os.path.join(PRAC, jmeno + ".png"); c.file_format = "PNG"; c.save()
    return c


def barva_vrcholu(o, obr_mat):
    """COLOR_0 = albedo pod UV rohu (lineárně) – střední/daleký stupeň (predmety.gd: barva vrcholů jako albedo)."""
    me = o.data
    cache = {}
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    uv = me.uv_layers["bake"].data if "bake" in me.uv_layers else me.uv_layers[0].data
    for p in me.polygons:
        im = obr_mat[p.material_index]
        if im.name not in cache:
            cache[im.name] = pixely(im)
        a = cache[im.name]; hh, ww = a.shape[:2]
        for li in p.loop_indices:
            u, v = uv[li].uv
            c = a[min(hh - 1, max(0, int(v * hh))), min(ww - 1, max(0, int(u * ww)))][:3]
            c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
            ca.data[li].color = (*c, 1.0)
    me.color_attributes.active_color = ca


def export(objs, cesta, barvy=False):
    aktivni(objs[0], *objs[1:])
    kw = dict(filepath=cesta, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
              export_image_format="JPEG", export_jpeg_quality=90, export_tangents=False, export_materials="EXPORT")
    if barvy:
        kw["export_vertex_color"] = "ACTIVE"
    bpy.ops.export_scene.gltf(**kw)


def nahled(objs):
    sc = bpy.context.scene; nastav_cycles(); sc.cycles.samples = 12; sc.render.resolution_x = 1200; sc.render.resolution_y = 800
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.32, 0.35, 1)
    sl = bpy.data.objects.new("sl", bpy.data.lights.new("sl", "SUN")); sc.collection.objects.link(sl)
    sl.data.energy = 4.0; sl.rotation_euler = (0.9, 0.2, 0.8)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50
    for k, (pos, cil) in enumerate((((1.2, -1.5, 1.3), (0.02, 0, 0.55)), ((0.0, -0.75, 1.05), (0.02, 0, 0.72)),
                                    ((-0.9, 0.6, 1.1), (0.0, 0, 0.6)))):
        cam.location = pos
        d = Vector(cil) - Vector(pos); cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(PRAC, f"nahled_{k}.png"); bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------ stavba
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    nastav_cycles()
    an_h, (ax0, ax1), hw = kovadlina_high()
    sp_h = sperhak_high()
    ob = obruc(); kr = kramle(CX - 0.06, KV["pata_m"][1] / 2)
    st = spalek()
    print("HIGH kovadlina", troj(an_h), "sperhak", troj(sp_h), "spalek", troj(st), "obruc", troj(ob), "kramle", troj(kr), flush=True)
    if A.nahled:
        nahled([an_h, sp_h, ob, kr, st]); return
    # low-poly železa
    an_l = decimuj(kopie(an_h, "kovadlina_low"), 9000)
    sp_l = decimuj(kopie(sp_h, "sperhak_low"), 1400)
    ob_l = kopie(ob, "obruc_low"); kr_l = kopie(kr, "kramle_low")
    zel = spoj([an_l, sp_l, ob_l, kr_l], "Kovadlina_zelezo")
    for p in zel.data.polygons:
        p.use_smooth = True
    while zel.data.uv_layers:
        zel.data.uv_layers.remove(zel.data.uv_layers[0])
    zel.data.uv_layers.active = zel.data.uv_layers.new(name="bake")
    aktivni(zel); bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(58), island_margin=0.003, area_weight=0.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    # pásek a kramle na atlasu menší (z blízka je skoro nevidět)
    bm = bmesh.new(); bm.from_mesh(zel.data); uvl = bm.loops.layers.uv["bake"]
    for f in bm.faces:
        c = f.calc_center_median()
        if math.hypot(c.x, c.y) > 0.40 or c.z < H + 0.06 and math.hypot(c.x - SH["poloha_m"][0], c.y - SH["poloha_m"][1]) > 0.06:
            for lp in f.loops:
                lp[uvl].uv *= 0.45
    bm.to_mesh(zel.data); bm.free()
    aktivni(zel); bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, margin=0.002)
    bpy.ops.object.mode_set(mode="OBJECT")
    # high sada železa (pásek a kramle samy sebou)
    ob_h = kopie(ob, "obruc_high"); kr_h = kopie(kr, "kramle_high")
    bpy.data.objects.remove(ob); bpy.data.objects.remove(kr)
    for o in (ob_h, kr_h):
        for p in o.data.polygons:
            p.use_smooth = True
    high = [an_h, sp_h, ob_h, kr_h]
    mz, kanaly_z, info_z = mat_zelezo_autorsky()
    mzi = (mz, kanaly_z, info_z)
    for o in high:
        o.data.materials.append(mz)
    tgt = bpy.data.materials.new("cil_zelezo"); tgt.use_nodes = True
    zel.data.materials.append(tgt)
    # špalek: textura čela + materiál
    print("textura dreva …", flush=True)
    rgb, vys = textura_dreva((ax0 + 0.01, ax1 - KV["roh_delka_m"] + 0.02, KV["pata_m"][1] / 2 + 0.02), SH["poloha_m"])
    prek = np_do_obr("drevo_prekryv", rgb, True); vysk = np_do_obr("drevo_vyska", vys, False)
    md, kanaly_d, info_d = mat_drevo_autorsky(prek, vysk)
    st.data.materials.append(md)
    mdi = (md, kanaly_d, info_d)
    st.data.uv_layers.active = st.data.uv_layers["bake"]
    zel.data.uv_layers.active = zel.data.uv_layers["bake"]
    vystup = {}
    # --- železo: high → low (low neviditelný pro paprsky)
    for v in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_shadow", "visible_transmission"):
        setattr(zel, v, False)
    for kanal, barva in (("albedo", True), ("drsnost", False), ("kov", False)):
        print("pece zelezo", kanal, flush=True)
        emit_kanal(mzi, kanal); i = bake_obr("zelezo_" + kanal, barva); cil_obr(zel, i)
        peč("EMIT", zel, high); vystup["z_" + kanal] = uloz(i, "zelezo_" + kanal)
    print("pece zelezo normal", flush=True)
    U, bsdf, em, out = info_z; U.ln(bsdf.outputs[0], out.inputs[0])
    i = bake_obr("zelezo_normal"); cil_obr(zel, i); peč("NORMAL", zel, high); vystup["z_normal"] = uloz(i, "zelezo_normal")
    for v in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_shadow", "visible_transmission"):
        setattr(zel, v, True)
    for o in high:
        o.hide_render = True
    print("pece zelezo ao", flush=True)
    i = bake_obr("zelezo_ao"); cil_obr(zel, i); peč("AO", zel); vystup["z_ao"] = uloz(i, "zelezo_ao")
    # --- dřevo (na sobě; kovadlina vrhá AO)
    for kanal, barva in (("albedo", True), ("drsnost", False)):
        print("pece drevo", kanal, flush=True)
        emit_kanal(mdi, kanal); i = bake_obr("drevo_" + kanal, barva); cil_obr(st, i)
        peč("EMIT", st); vystup["d_" + kanal] = uloz(i, "drevo_" + kanal)
    U, bsdf, em, out = info_d; U.ln(bsdf.outputs[0], out.inputs[0])
    print("pece drevo normal", flush=True)
    i = bake_obr("drevo_normal"); cil_obr(st, i); peč("NORMAL", st); vystup["d_normal"] = uloz(i, "drevo_normal")
    print("pece drevo ao", flush=True)
    i = bake_obr("drevo_ao"); cil_obr(st, i); peč("AO", st); vystup["d_ao"] = uloz(i, "drevo_ao")
    # --- finální materiály
    orm_z = orm("zelezo_orm", vystup["z_ao"], vystup["z_drsnost"], vystup["z_kov"])
    orm_d = orm("drevo_orm", vystup["d_ao"], vystup["d_drsnost"])
    MZ = mat_finalni("kovadlina_zelezo", vystup["z_albedo"], vystup["z_normal"], orm_z)
    MD = mat_finalni("kovadlina_drevo", vystup["d_albedo"], vystup["d_normal"], orm_d)
    for o in high:
        bpy.data.objects.remove(o)
    zel.data.materials.clear(); zel.data.materials.append(MZ)
    st.data.materials.clear(); st.data.materials.append(MD)
    # uv "tex" pryč (glTF: jen jedna sada UV)
    st.data.uv_layers.remove(st.data.uv_layers["tex"])
    # --- podrobný stupeň = jeden uzel se dvěma materiály + kolize
    pod = spoj([zel, st], "Kovadlina_1393")
    pod.data.uv_layers[0].name = "UVMap"
    # kolize: jeden konvexní obal (špalek + kovadlina + sperhák)
    body = [Vector(((r_spalku(2 * math.pi * i / 24, 0) + 0.0) * math.cos(2 * math.pi * i / 24),
                    (r_spalku(2 * math.pi * i / 24, 0)) * math.sin(2 * math.pi * i / 24), 0.0)) for i in range(24)]
    body += [Vector(((r_spalku(2 * math.pi * i / 24, H) - 0.01) * math.cos(2 * math.pi * i / 24),
                     (r_spalku(2 * math.pi * i / 24, H) - 0.01) * math.sin(2 * math.pi * i / 24), H)) for i in range(24)]
    body += [Vector((x, y, F)) for x in (ax0, ax1 - KV["roh_delka_m"]) for y in (-hw, hw)] + [Vector((ax1, 0, F - 0.03))]
    body += [Vector((SH["poloha_m"][0], SH["poloha_m"][1], H + SH["vyska_nad_spalkem_m"]))]
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in body]
    bmesh.ops.convex_hull(bm, input=vs)
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    kol = obj_z_bm(bm, "Kovadlina_1393_kolize-convcolonly")
    n_pod = troj(pod)
    export([pod, kol], os.path.join(OUT, "kovadlina_1393.glb"))
    print("PODROBNY troj", n_pod, "kolize", troj(kol), flush=True)
    # --- střední a daleký stupeň (vlastní zjednodušení, textury menší, barva vrcholů)
    stat = {"podrobny": n_pod}
    for nazev, cil_k, n_sp, zb, kr_, px, obr_ in (("stredni", 1900, 48, (0, 0.05, 0.14, 0.26, 0.345), 2, 512, True),
                                                   ("daleko", 300, 18, (0, 0.2), 1, 256, False)):
        ob2 = kopie(pod, "lod_" + nazev)
        # rozdělit materiály: železo decimovat, dřevo postavit znovu s méně segmenty
        aktivni(ob2); bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT")
        ob2.active_material_index = 1; bpy.ops.object.material_slot_select(); bpy.ops.mesh.delete(type="FACE")
        bpy.ops.object.mode_set(mode="OBJECT")
        if nazev == "daleko":                  # bez pásku, hřebů a kramlí
            bm = bmesh.new(); bm.from_mesh(ob2.data)
            pryc = [f for f in bm.faces if math.hypot(f.calc_center_median().x, f.calc_center_median().y) > 0.40
                    or (f.calc_center_median().z < H + 0.06 and abs(f.calc_center_median().y) > 0.12)]
            bmesh.ops.delete(bm, geom=pryc, context="FACES"); bm.to_mesh(ob2.data); bm.free()
        decimuj(ob2, cil_k)
        st2 = spalek(n=n_sp, zbok=zb, nfil=kr_, krouzky=(0.6, 0.25) if nazev == "stredni" else (0.4,))
        st2.data.uv_layers.remove(st2.data.uv_layers["tex"])
        st2.data.uv_layers[0].name = "UVMap"
        st2.data.materials.append(MD)
        lod = spoj([ob2, st2], "Kovadlina_1393_" + nazev)
        az = zmensi(vystup["z_albedo"], px, f"zelezo_albedo_{px}"); ad = zmensi(vystup["d_albedo"], px, f"drevo_albedo_{px}")
        barva_vrcholu(lod, {0: az, 1: ad})
        mz2 = mat_finalni(f"kovadlina_zelezo_{nazev}", az, zmensi(vystup["z_normal"], px, f"zn{px}"), zmensi(orm_z, px, f"zo{px}"))
        md2 = mat_finalni(f"kovadlina_drevo_{nazev}", ad, zmensi(vystup["d_normal"], px, f"dn{px}"), zmensi(orm_d, px, f"do{px}"))
        lod.data.materials[0] = mz2; lod.data.materials[1] = md2
        stat[nazev] = troj(lod)
        export([lod], os.path.join(OUT, f"kovadlina_1393_{nazev}.glb"), barvy=True)
        print("LOD", nazev, stat[nazev], flush=True)
    json.dump(stat, open(os.path.join(PRAC, "stat.json"), "w"))
    print("HOTOVO", stat)


main()

os._exit(0)
