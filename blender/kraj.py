"""Sirsi krajina kolem tvrze: kopce az k obzoru, hlavni cesta od brany, krizovatka s bozimi muky
a odbocka vlevo (na +x) do vesnice asi kilometr od tvrze. Lesy na kopcich, pole v lanech kolem vesnice.

Teren je ve trech pasmech: u tvrze po 1 m (fort.terrain), okoli po 5 m, obzor po 25 m.
Vysky vsude pocita fort.land (sem jen pridava kopce, rovinu vesnice a srovnani pod cestami)."""
import math
import random

# souradnice hry: x vpravo pri pohledu od tvrze k jihu, z od brany ven (+z), y nahoru
VES = (470.0, 830.0)                       # stred navsi
VES_R = 120.0                              # polomer roviny vesnice
CROSS = (3.0, 400.0)                       # krizovatka hlavni cesty a odbocky do vesnice
HLAVNI = [(0.0, 16.0), (0.0, 120.0), (4.0, 240.0), (3.0, 400.0), (-12.0, 560.0), (-30.0, 800.0), (-42.0, 1100.0),
          (-48.0, 1500.0), (-50.0, 2400.0)]
ODBOCKA = [CROSS, (36.0, 432.0), (110.0, 492.0), (225.0, 600.0), (340.0, 712.0), (418.0, 786.0), (VES[0] - 10.0, VES[1] - 8.0)]
CESTY = [(HLAVNI, 3.4), (ODBOCKA, 2.8)]

NEAR = (-60.0, 60.0, -55.0, 70.0)          # pasmo 1 m (fort.terrain)
ACT = (-250.0, 700.0, -250.0, 1150.0)      # pasmo 5 m
FAR = (-1500.0, 2000.0, -1500.0, 2600.0)   # pasmo 25 m (obzor)


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def seg_info(x, z, path):
    """Nejblizsi bod lomene cary: (vzdalenost, bod x, bod z)."""
    best = (1e9, 0.0, 0.0)
    for (ax, az), (bx, bz) in zip(path[:-1], path[1:]):
        dx, dz = bx - ax, bz - az
        t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
        px, pz = ax + dx * t, az + dz * t
        d = math.hypot(x - px, z - pz)
        if d < best[0]:
            best = (d, px, pz)
    return best


# skalni hreben (piskovcove skalni mesto) zapadne od hlavni cesty: osa od jihu k severu
HREBEN = [(-120.0, 230.0), (-175.0, 380.0), (-190.0, 540.0), (-160.0, 720.0), (-120.0, 900.0)]


def ridge(x, z):
    """Vyska skalniho hrebenu (m): siroky zalesneny hrbet, na nem stoji skaly."""
    d, px, pz = seg_info(x, z, HREBEN)
    if d > 160.0:
        return 0.0
    along = smooth(200.0, 300.0, z) * (1.0 - smooth(860.0, 960.0, z))
    return 34.0 * math.exp(-(d / 70.0) ** 2) * along


_PERM = list(range(256))
random.Random(77).shuffle(_PERM)
_PERM += _PERM


def _grad(h, x, z):
    h &= 7
    u = x if h < 4 else z
    v = z if h < 4 else x
    return (u if h & 1 == 0 else -u) + (v if h & 2 == 0 else -v)


def perlin(x, z):
    """Gradientni sum -1..1 (perioda 256)."""
    xi, zi = int(math.floor(x)) & 255, int(math.floor(z)) & 255
    xf, zf = x - math.floor(x), z - math.floor(z)
    u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
    w = zf * zf * zf * (zf * (zf * 6 - 15) + 10)
    aa, ab = _PERM[_PERM[xi] + zi], _PERM[_PERM[xi] + zi + 1]
    ba, bb = _PERM[_PERM[xi + 1] + zi], _PERM[_PERM[xi + 1] + zi + 1]
    x1 = _grad(aa, xf, zf) + u * (_grad(ba, xf - 1, zf) - _grad(aa, xf, zf))
    x2 = _grad(ab, xf, zf - 1) + u * (_grad(bb, xf - 1, zf - 1) - _grad(ab, xf, zf - 1))
    return (x1 + w * (x2 - x1)) * 0.7


def detail(x, z):
    """Nerovnosti krajiny: terenni vlny, hrbolky, mezicky a prohlubne (m)."""
    v = 7.0 * perlin(x / 140.0 + 3.1, z / 140.0 - 7.3)
    v += 3.6 * perlin(x / 60.0 - 1.7, z / 60.0 + 4.4)
    v += 1.5 * perlin(x / 26.0 + 9.2, z / 26.0 + 2.5)
    v += 0.55 * perlin(x / 11.0 - 5.0, z / 11.0 - 3.3)
    # ostre hrbety (ridged) tu a tam: kamenite vycnelky
    v += 1.6 * max(0.0, 0.55 - abs(perlin(x / 90.0 + 20.0, z / 90.0 - 11.0))) ** 2 * 4.0
    return v


def _hills_raw(x, z):
    r = math.hypot(x, z)
    w = smooth(140.0, 330.0, r)
    if w <= 0.0:
        return 0.0
    big = 32.0 * smooth(350.0, 1600.0, r) * (0.55 + 0.45 * math.sin(x * 0.0042 + 1.3) * math.cos(z * 0.0035 + 0.4))
    mid = 8.0 * math.sin(x * 0.012 + z * 0.004) * math.cos(z * 0.010 - 1.0) + 3.5 * math.sin(x * 0.027 - 0.7) * math.sin(z * 0.023 + 2.1)
    return w * (big + mid + detail(x, z)) + ridge(x, z) * (1.0 + 0.12 * perlin(x / 30.0, z / 30.0))


_HV = None


def hills(x, z):
    """Pridavek k vysce terenu daleko od tvrze: kopce, pod vesnici mirna rovina."""
    global _HV
    if _HV is None:
        _HV = _hills_raw(*VES)
    h = _hills_raw(x, z)
    dv = math.hypot(x - VES[0], z - VES[1])
    if dv < VES_R + 140.0:
        k = 1.0 - smooth(VES_R, VES_R + 140.0, dv)
        # rovina s mirnym sklonem k potoku na vychode navsi
        flat = _HV - 0.6 * smooth(-40.0, 120.0, x - VES[0])
        h = h + (flat - h) * k * 0.6               # ves neni placka: kopecky zustanou
        import vesnice
        h -= vesnice.pond_depth(x, z)
    return h


def road_near(x, z):
    """Nejblizsi cesta: (vzdalenost, bod x, bod z, polovicni sirka) nebo None (daleko)."""
    best = None
    for path, w in CESTY:
        d, px, pz = seg_info(x, z, path)
        if best is None or d < best[0]:
            best = (d, px, pz, w / 2.0)
    return best


def flatten(x, z, y, land_fn):
    """Srovnani terenu pod cestami (mimo tvrz): jadro 15 cm pod povrchem cesty, plynuly prechod do okoli."""
    if math.hypot(x, z) < 70.0:
        return y
    rn = road_near(x, z)
    if rn is None or rn[0] > 10.0:
        return y
    d, px, pz, hw = rn
    yr = land_fn(px, pz, False) - 0.15
    k = 1.0 - smooth(hw + 0.6, hw + 6.0, d)
    return y + (yr - y) * k


def road_y(px, pz, land_fn):
    """Vyska povrchu cesty (pas hliny lezi 12 cm nad srovnanym terenem)."""
    return land_fn(px, pz, False) - 0.03


# ------------------------------------------------------------------ pouziti zeme (barva terenu)

def _forest_raw(x, z):
    v = (math.sin(x * 0.0061 + 0.7) * math.cos(z * 0.0049 - 1.1) + 0.55 * math.sin(x * 0.0157 + z * 0.0113 + 2.0)
         + 0.3 * math.sin(x * 0.041 - z * 0.033))
    return v


def field_strip(x, z):
    """Lan pole kolem vesnice: (cislo lanu, plodina 0..3) nebo None. Lany jsou pruhy kolmo od navsi."""
    dx, dz = x - VES[0], z - VES[1]
    r = math.hypot(dx, dz)
    if r < VES_R + 15.0 or r > VES_R + 260.0:
        return None
    a = math.atan2(dz, dx)
    # pole jen na zapad, sever a jih od vesnice (na vychode luka u potoka a les)
    if -0.9 < a < 0.6:
        return None
    n = int((a + math.pi) / 0.075)
    crop = (n * 7 + 3) % 4
    return n, crop


def forest(x, z):
    """Mira lesa 0..1 (tmava lesni puda; v pasmu 5 m tam stoji stromy)."""
    r = math.hypot(x, z)
    if r < 170.0:
        return 0.0
    rn = road_near(x, z)
    if rn and rn[0] < rn[3] + 9.0:
        return 0.0
    if math.hypot(x - VES[0], z - VES[1]) < VES_R + 290.0 and field_strip(x, z) is not None:
        return 0.0
    if math.hypot(x - VES[0], z - VES[1]) < VES_R + 40.0:
        return 0.0
    v = _forest_raw(x, z) + 0.6 * smooth(500.0, 1600.0, r)
    return smooth(0.35, 0.65, v)


def ground_attrs(x, z):
    """(trava 0..1, les 0..1, pole 0..1 kod plodiny) pro barvu terenu."""
    les = forest(x, z)
    fs = field_strip(x, z)
    pole = 0.0
    g = 0.85
    if fs is not None:
        pole = (fs[1] + 1) / 4.0
        g = 0.6
    dv = math.hypot(x - VES[0], z - VES[1])
    if dv < 90.0:
        # naves travnata, udusana hlina jen ve dvorech u chalup a v pruhu cesty pres naves
        import vesnice
        g = 0.75
        yd = vesnice.yard_dist(x, z)
        if yd < 13.0:
            g = 0.2 + 0.55 * smooth(7.0, 13.0, yd)
    rn = road_near(x, z)
    if rn and rn[0] < rn[3] + 1.5 and math.hypot(x, z) > 60:
        g = min(g, 0.15 + 0.5 * smooth(rn[3] - 0.2, rn[3] + 1.5, rn[0]))
    return g, les, pole


# ------------------------------------------------------------------ geometrie terenu

def _grid(xs, zs, skip, land_fn, name, P, coll):
    """Mrizka terenu: ctverce uvnitr obdelniku skip vynechat; atributy trava / les / pole."""
    import bpy  # noqa: F401
    verts, faces = [], []
    idx = {}
    attrs = []
    for i, x in enumerate(xs):
        for k, z in enumerate(zs):
            idx[(i, k)] = len(verts)
            y = land_fn(x, z)
            g, les, pole = ground_attrs(x, z)
            verts.append((x, y, z))
            attrs.append((g, les, pole))
    x0, x1, z0, z1 = skip
    for i in range(len(xs) - 1):
        for k in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[k] + zs[k + 1]) / 2
            if x0 < cx < x1 and z0 < cz < z1:
                continue
            faces.append((idx[(i, k)], idx[(i, k + 1)], idx[(i + 1, k + 1)], idx[(i + 1, k)]))
    return verts, faces, attrs


def _skirt(verts, faces, attrs, rect, step, land_fn, depth=0.8):
    """Svisly pasek dolu po obvodu jemnejsiho pasma: zakryje skulinky mezi pasmy s ruznou hustotou."""
    x0, x1, z0, z1 = rect
    pts = []
    n = int(round((x1 - x0) / step))
    m = int(round((z1 - z0) / step))
    pts += [(x0 + (x1 - x0) * i / n, z0) for i in range(n)]
    pts += [(x1, z0 + (z1 - z0) * k / m) for k in range(m)]
    pts += [(x1 - (x1 - x0) * i / n, z1) for i in range(n)]
    pts += [(x0, z1 - (z1 - z0) * k / m) for k in range(m)]
    pts.append(pts[0])
    prev = None
    for x, z in pts:
        y = land_fn(x, z)
        a = len(verts)
        verts.append((x, y, z))
        verts.append((x, y - depth, z))
        ga = ground_attrs(x, z)
        attrs += [ga, ga]
        if prev is not None:
            faces.append((prev, prev + 1, a + 1, a))
        prev = a


def tiles(coll, land_fn):
    """Pasma 5 m a 25 m (pasmo 1 m dela fort.terrain), kazde jako vlastni objekt Teren_*."""
    from lib import Part
    out = []
    for name, rect, inner, step in (("Teren_okoli", ACT, NEAR, 5.0), ("Teren_obzor", FAR, ACT, 25.0)):
        xs = [rect[0] + step * i for i in range(int(round((rect[1] - rect[0]) / step)) + 1)]
        zs = [rect[2] + step * k for k in range(int(round((rect[3] - rect[2]) / step)) + 1)]
        verts, faces, attrs = _grid(xs, zs, inner, land_fn, name, None, coll)
        # obzor: lesy jako tmava vyvysena koruna (z dalky vypada jako les, stromy by stály moc)
        if name == "Teren_obzor":
            verts = [(x, y + 11.0 * a[1] * smooth(0.0, 1.0, a[1]), z) for (x, y, z), a in zip(verts, attrs)]
        P = Part(name)
        P.mesh(verts, faces, "zem")
        o = P.commit(coll)
        _set_attrs(o, attrs)
        out.append(o)
    return out


def _set_attrs(o, attrs):
    me = o.data
    for key, j in (("grass", 0), ("les", 1), ("pole", 2)):
        at = me.attributes.new(key, "FLOAT", "POINT")
        at.data.foreach_set("value", [a[j] for a in attrs])


def near_skirt(coll, land_fn):
    """Pasek pod okrajem pasma 1 m."""
    from lib import Part
    verts, faces, attrs = [], [], []
    _skirt(verts, faces, attrs, NEAR, 1.0, land_fn)
    P = Part("Teren_lem")
    P.mesh(verts, faces, "zem")
    o = P.commit(coll)
    _set_attrs(o, attrs)
    return o


# ------------------------------------------------------------------ cesty (pas udusane hliny s kolejemi)

def roads(coll, land_fn):
    """Pasy cest: pruh vrcholu napric (kraje vys o travnatou mez, uprostred koleje), UV podel cesty."""
    from lib import Part
    verts, faces, attrs = [], [], []
    sfaces = []
    for path, w in CESTY:
        pts = []
        # zacit za pasmem 1 m (tam je cesta namalovana v terenu)
        for (ax, az), (bx, bz) in zip(path[:-1], path[1:]):
            L = math.hypot(bx - ax, bz - az)
            n = max(1, int(L / 2.0))
            for i in range(n):
                t = i / n
                pts.append((ax + (bx - ax) * t, az + (bz - az) * t))
        pts.append(path[-1])
        pts = [p for p in pts if not (NEAR[0] - 2 < p[0] < NEAR[1] + 2 and p[1] < NEAR[3] - 4)]
        # vyhlazeni lomu: klouzavy prumer
        sm = []
        for i in range(len(pts)):
            a = pts[max(0, i - 3):i + 4]
            sm.append((sum(p[0] for p in a) / len(a), sum(p[1] for p in a) / len(a)))
        sm[0], sm[-1] = pts[0], pts[-1]
        prof = [(-0.62, -0.16, 0.7), (-0.4, 0.0, 0.2), (-0.22, -0.035, 0.0), (-0.12, 0.0, 0.08), (0.12, 0.0, 0.08),
                (0.22, -0.035, 0.0), (0.4, 0.0, 0.2), (0.62, -0.16, 0.7)]
        rowlen = len(prof)
        base = len(verts)
        for i, (x, z) in enumerate(sm):
            a = sm[max(0, i - 1)]
            b = sm[min(len(sm) - 1, i + 1)]
            dx, dz = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dz) or 1.0
            nx, nz = -dz / L, dx / L
            yc = road_y(x, z, land_fn)
            for s, dy, g in prof:
                px, pz = x + nx * s * w, z + nz * s * w
                verts.append((px, yc + dy, pz))
                attrs.append((g, 0.0, 0.0))
            if i:
                r0 = base + (i - 1) * rowlen
                r1 = base + i * rowlen
                stone = _stone_road(x, z)
                for j in range(rowlen - 1):
                    fc = (r0 + j, r0 + j + 1, r1 + j + 1, r1 + j)
                    # kamenny usek: dlazba z kocicich hlav jen uprostred, kraje zustanou hlinene
                    (sfaces if stone and 0 < j < rowlen - 2 else faces).append(fc)
    P = Part("Teren_cesta")
    P.mesh(verts, faces, "zem")
    o = P.commit(coll)
    _set_attrs(o, attrs)
    if sfaces:
        used = sorted({k for fc in sfaces for k in fc})
        remap = {k: i for i, k in enumerate(used)}
        P2 = Part("Teren_cesta_kamen")
        P2.mesh([(verts[k][0], verts[k][1] + 0.025, verts[k][2]) for k in used], [tuple(remap[k] for k in fc) for fc in sfaces], "kocicky")
        P2.commit(coll)
    return o


def _stone_road(x, z):
    """Mista s kamennou cestou: stoupani pres kopec na hlavni ceste a vjezd do vesnice."""
    if 500.0 < z < 640.0 and x < 0.0:
        return True
    return math.hypot(x - VES[0], z - VES[1]) < 75.0


# ------------------------------------------------------------------ rozmisteni stromu (veg.scatter)

def tree_spots(R, n=2600):
    """Mista pro stromy v pasmu 5 m: husty les tam, kde forest() > 0.5, rozptylene stromy a meze v polich."""
    out = []
    tries = 0
    taken = {}

    def free(x, z, r2):
        cx, cz = int(x // 6), int(z // 6)
        for i in (-1, 0, 1):
            for k in (-1, 0, 1):
                for (a, b) in taken.get((cx + i, cz + k), []):
                    if (x - a) ** 2 + (z - b) ** 2 < r2:
                        return False
        return True

    while len(out) < n and tries < n * 30:
        tries += 1
        x = R.uniform(ACT[0] + 5, ACT[1] - 5)
        z = R.uniform(ACT[2] + 5, ACT[3] - 5)
        if math.hypot(x + 4, z) < 160:
            continue
        f = forest(x, z)
        if f < 0.5:
            # osamele stromy na mezich a u cest (lipy, duby, brizy), ridce
            if R.random() > 0.015:
                continue
            rn = road_near(x, z)
            if rn and rn[0] < rn[3] + 3.0:
                continue
            if math.hypot(x - VES[0], z - VES[1]) < VES_R:
                continue
            kind = "solo"
        else:
            kind = "les"
        if not free(x, z, 22.0 if kind == "les" else 60.0):
            continue
        taken.setdefault((int(x // 6), int(z // 6)), []).append((x, z))
        out.append((x, z, kind, f))
    return out


# ------------------------------------------------------------------ piskovcove skalni mesto na hrebeni

def _tower(P, c, height, rad, R, lean=0.0):
    """Piskovcova vez: prstenec bodu po vysce; vodorovne vrstvy vymlete do zlabku, svisle pukliny ji deli na
    'prsty', vrsek zaobleny jako u Apoleny. UV valcove (m)."""
    from mathutils import Matrix, Vector
    from lib import M
    n = 24
    lay = R.uniform(0.45, 0.8)                     # tloustka vrstvy piskovce
    levels = max(8, int(height / 0.35))
    cracks = [(R.uniform(0, 2 * math.pi), R.uniform(0.08, 0.22), R.uniform(0.2, 0.45)) for _ in range(R.randint(2, 6))]
    phase = R.uniform(0, 6.28)
    s1, s2 = R.uniform(0, 100), R.uniform(0, 100)
    ell = R.uniform(0.45, 0.9)
    u_off = R.uniform(0, 30)
    verts, faces, uvs = [], [], []
    rows = []
    for j in range(levels + 1):
        t = j / levels
        y = height * t
        # silueta: dole sirsi, uprostred mirne zuzena, nahore zaoblena kopule
        prof = 1.0 + 0.15 * (1 - t) ** 2 - 0.1 * math.sin(math.pi * t)
        if t > 0.8:
            prof *= math.sqrt(max(0.03, 1 - ((t - 0.8) / 0.2) ** 2))
        # vymlete zlabky mezi vrstvami a vystupujici tvrdsi vrstvy
        band = 1.0 - 0.035 * math.sin(y / lay * math.pi + phase + 2.5 * perlin(s2, y * 0.1)) ** 6 + 0.05 * perlin(s1, y / (lay * 2.3))
        row = []
        for i in range(n):
            a = 2 * math.pi * i / n
            ca, sa = math.cos(a), math.sin(a)
            r = rad * prof * band * (1.0 + 0.42 * perlin(ca * 1.1 + s1, sa * 1.1 + s2 + y * 0.06)
                                     + 0.07 * perlin(ca * 3.0 + s2, y * 0.25 + sa * 3.0))
            for cA, w, dep in cracks:
                da = math.atan2(math.sin(a - cA), math.cos(a - cA))
                if abs(da) < w:
                    r *= 1.0 - dep * (1 - abs(da) / w) ** 1.5 * smooth(0.0, 0.12, t)
            x = ca * r + lean * y
            z = sa * r * ell
            row.append(len(verts))
            verts.append((x, y, z))
        rows.append(row)
    for j in range(levels):
        for i in range(n):
            a0, a1 = rows[j][i], rows[j][(i + 1) % n]
            b0, b1 = rows[j + 1][i], rows[j + 1][(i + 1) % n]
            faces.append((a0, b0, b1, a1))
            u0, u1 = u_off + i / n * 2 * math.pi * rad * 0.8, u_off + (i + 1) / n * 2 * math.pi * rad * 0.8
            v0, v1 = height * j / levels * 0.6, height * (j + 1) / levels * 0.6
            uvs.append([(u0, v0), (u0, v1), (u1, v1), (u1, v0)])
    top = len(verts)
    verts.append((lean * height, height + 0.05, 0.0))
    for i in range(n):
        faces.append((rows[-1][i], top, rows[-1][(i + 1) % n]))
        uvs.append([(i * 0.3, 0.0), (0.0, 0.3), ((i + 1) * 0.3, 0.0)])
    rot = Matrix.Rotation(R.uniform(0, 2 * math.pi), 3, "Y")
    m = M(Vector(c) - Vector((0, 0.25 * rad + 0.8, 0)), basis=rot)
    P.mesh(verts, faces, "piskovec_skala", uvs=uvs, m=m, smooth=True)
    P.cols.append((M(Vector(c) + Vector((0, height / 2 - 1.2, 0)), basis=rot), (rad * 1.5, height, rad * 1.5 * ell)))


def rocks(coll, land_fn):
    """Skupiny piskovcovych vezi a balvanu podel hrebene (jako Apolena a Prachovske skaly)."""
    from lib import Part
    R = random.Random(1394)
    P = Part("Skalni_mesto", bevel=0.0)
    spots = []
    # podel osy hrebene skupiny po 30-60 m
    L = 0.0
    segs = list(zip(HREBEN[:-1], HREBEN[1:]))
    for (ax, az), (bx, bz) in segs:
        d = math.hypot(bx - ax, bz - az)
        k = 0.0
        while k < d:
            t = k / d
            spots.append((ax + (bx - ax) * t, az + (bz - az) * t, -(bz - az) / d, (bx - ax) / d))
            k += R.uniform(28.0, 55.0)
    towers = 0
    for x, z, nx, nz in spots:
        if z < 250 or z > 880:
            continue
        # skupina: srostly masiv z nekolika vezi (jako Apolena), nekdy samostatna jehla, kolem balvany
        cnt = R.randint(3, 8)
        gx, gz = x + R.uniform(-10, 10), z + R.uniform(-10, 10)
        # masiv protazeny podel hrebene: veze tesne vedle sebe, uprostred nejvyssi
        for q in range(cnt):
            o = (q - (cnt - 1) / 2) * R.uniform(4.5, 7.5)
            xx, zz = gx - nx * 0 + (-nz) * o + R.gauss(0.0, 2.0), gz + nx * o + R.gauss(0.0, 2.0)
            y = land_fn(xx, zz)
            mid = 1.0 - abs(o) / (cnt * 4.0)
            h = R.uniform(6.0, 13.0) + 14.0 * mid * R.random()
            rad = R.uniform(4.0, 7.5)
            _tower(P, (xx, y, zz), h, rad, R, lean=R.uniform(-0.04, 0.04))
            towers += 1
        if R.random() < 0.35:
            xx, zz = gx + R.uniform(-30, 30), gz + R.uniform(-30, 30)
            _tower(P, (xx, land_fn(xx, zz), zz), R.uniform(16.0, 30.0), R.uniform(1.8, 3.0), R, lean=R.uniform(-0.05, 0.05))
            towers += 1
        import krajina
        for _ in range(R.randint(4, 10)):
            xx, zz = gx + R.gauss(0.0, 12.0), gz + R.gauss(0.0, 12.0)
            sz = R.uniform(0.8, 3.5)
            krajina.rock(P, (xx, land_fn(xx, zz), zz), (sz * R.uniform(1.0, 1.6), sz * R.uniform(0.5, 0.9), sz), 0.3)
    # kameny u krajnic cest (vyorane z poli, odhozene z cesty)
    import krajina
    Rk = Part("Skaly_cesty", bevel=0.0)
    for path, w in CESTY:
        for (ax, az), (bx, bz) in zip(path[:-1], path[1:]):
            L = math.hypot(bx - ax, bz - az)
            k = R.uniform(0, 10)
            while k < L:
                t = k / L
                x, z = ax + (bx - ax) * t, az + (bz - az) * t
                k += R.uniform(6.0, 22.0)
                if math.hypot(x, z) < 75 or math.hypot(x - VES[0], z - VES[1]) < 60:
                    continue
                side = R.choice((-1, 1))
                nx, nz = -(bz - az) / L, (bx - ax) / L
                off = w / 2 + R.uniform(0.3, 1.8)
                px, pz = x + nx * off * side, z + nz * off * side
                s = R.uniform(0.15, 0.55) if R.random() < 0.85 else R.uniform(0.6, 1.1)
                krajina.rock(Rk, (px, land_fn(px, pz), pz), (s * R.uniform(1.0, 1.5), s * R.uniform(0.5, 0.8), s), 0.35,
                             collide=s > 0.6)
    Rk.commit(coll)
    P.commit(coll)
    print("skalni mesto: %d vezi" % towers)
    return P


# ------------------------------------------------------------------ drobnosti v krajine: skalky, kameny, trsy, kere

def _wild(x, z):
    """Misto v divocine (ne na ceste, poli, navsi ani u tvrze)."""
    if not (ACT[0] + 4 < x < ACT[1] - 4 and ACT[2] + 4 < z < ACT[3] - 4):
        return False
    if math.hypot(x + 4, z) < 75:
        return False
    rn = road_near(x, z)
    if rn and rn[0] < rn[3] + 1.2:
        return False
    if math.hypot(x - VES[0], z - VES[1]) < VES_R + 20:
        # ve vsi ano, jen ne ve dvorech, na zahradach a v rybnicku
        import vesnice
        if vesnice.yard_dist(x, z) < 15.0 or vesnice.pond_depth(x, z) > 0.0:
            return False
    return field_strip(x, z) is None


def outcrops(coll, land_fn):
    """Skalky (vycnivajici skaliska a hromady kamenu) na hrbolcich a svazich, rozhazene kameny v trave."""
    import krajina
    from lib import Part
    R = random.Random(1395)
    P = Part("Skalky", bevel=0.0)
    n = 0
    tries = 0
    while n < 150 and tries < 20000:
        tries += 1
        x, z = R.uniform(ACT[0], ACT[1]), R.uniform(ACT[2], ACT[3])
        if not _wild(x, z):
            continue
        # skalky hlavne na vyvysenych hrbetech (ridged sum) a na svazich
        rid = max(0.0, 0.55 - abs(perlin(x / 90.0 + 20.0, z / 90.0 - 11.0)))
        if R.random() > 0.15 + rid * 1.6:
            continue
        for _ in range(R.randint(2, 7)):
            xx, zz = x + R.gauss(0, 2.5), z + R.gauss(0, 2.5)
            s = R.uniform(0.5, 2.6) if R.random() < 0.7 else R.uniform(2.5, 4.5)
            krajina.rock(P, (xx, land_fn(xx, zz), zz), (s * R.uniform(1.0, 1.7), s * R.uniform(0.45, 0.9), s * R.uniform(0.8, 1.3)),
                         R.uniform(0.25, 0.45))
        n += 1
    for _ in range(700):
        x, z = R.uniform(ACT[0], ACT[1]), R.uniform(ACT[2], ACT[3])
        if not _wild(x, z):
            continue
        s = R.uniform(0.12, 0.5)
        krajina.rock(P, (x, land_fn(x, z), z), (s * R.uniform(1.0, 1.5), s * R.uniform(0.5, 0.8), s), 0.35, collide=False)
    P.commit(coll)
    print("skalky:", n)


def plant_spots(R):
    """Trsy travy, kvetiny, kere a naletove stromky v divocine: [(model, x, z, vyska, naklon)]."""
    out = []
    # kere a nalet: na okrajich lesa, na mezich, kolem skalek, v dolinkach
    k = 0
    while k < 1100:
        x, z = R.uniform(ACT[0], ACT[1]), R.uniform(ACT[2], ACT[3])
        if not _wild(x, z):
            continue
        f = forest(x, z)
        edge = 1.0 - abs(f - 0.35) * 2.5
        if R.random() > 0.12 + max(0.0, edge) * 0.8:
            continue
        k += 1
        for _ in range(R.randint(1, 4)):
            xx, zz = x + R.uniform(-2.5, 2.5), z + R.uniform(-2.5, 2.5)
            c = R.random()
            if c < 0.35:
                out.append(("shrub_02", xx, zz, R.uniform(0.9, 2.2), 0.0))
            elif c < 0.6:
                out.append(("sipek", xx, zz, R.uniform(0.8, 2.0), 0.0))
            elif c < 0.85:
                out.append(("briza", xx, zz, R.uniform(1.6, 5.0), 0.0))
            else:
                out.append(("smrk", xx, zz, R.uniform(1.2, 3.5), 0.0))
    # trsy vysoke travy a kvetiny: hustsi u cest, mezi a skalek, v lese ridce
    k = 0
    while k < 26000:
        x, z = R.uniform(ACT[0], ACT[1]), R.uniform(ACT[2], ACT[3])
        if not _wild(x, z):
            continue
        rn = road_near(x, z)
        near = rn is not None and rn[0] < 40.0
        dv = math.hypot(x - VES[0], z - VES[1])
        if not near and dv > 260 and R.random() > 0.35:
            continue
        k += 1
        c = R.random()
        if c < 0.62:
            out.append(("divoka_trava", x, z, R.uniform(0.5, 1.1), 0.12))
        elif c < 0.82:
            out.append(("grass_medium_02", x, z, R.uniform(0.3, 0.6), 0.0))
        elif c < 0.9:
            out.append(("dandelion_01", x, z, R.uniform(0.2, 0.35), 0.0))
        elif c < 0.96:
            out.append(("nettle_plant", x, z, R.uniform(0.3, 0.55), 0.0))
        else:
            out.append(("fern_02", x, z, R.uniform(0.5, 0.9), 0.0))
    return out
