"""Ruiny v lesich a na hrebeni (mista pro pribeh): zriceny kostel se hrbitovem, zanikla ves, zricenina hradku.

Podle skutecnych lokalit:
- zanikle vsi v ceskych lesich (Ve Spalenem u Vyzlovky ~40 pozustatku domu a hospodarskych staveni, rybniky s hrazemi;
  Zabdisi u Zebraku 29 terennich utvaru po domech) - dnes nizke kamenne podezdivky a prohlubne radou podel nekdejsi
  navsi nebo cesty, studna, okolo stopy plužiny;
- vegetace zricenin: na sutich a u zdi dusikomilne a vapnomilne rostliny (kopriva, bez cerny, vlastovicnik),
  nalet javoru, jasanu a briz, ve stinu kapradi; zricenina zvysuje pestrost lesa.
Zarostle, ale pruchozi: uvnitr zdi a domu jen nizke byliny, kere a nalet u zdi a v rozich, prochody volne."""
import math
import random

import kraj

R = random.Random(1420)

ROSTLINY = []          # (model, x, z, vyska) - rozmisti veg
STATICKE = []          # (model, x, z, yaw, posun y) - modely ruin (export_game, trimesh kolize)
NAZVY = []             # {"name", "x", "z", "r"} - nazev mista ve hre


def _land(x, z):
    import fort
    return fort.land(x, z)


def _ruina(id_):
    return [r for r in kraj.RUINY if r[0] == id_][0]


class _F:
    """Mistni souradnice ruiny: u, v v metrech, otoceni yaw (jako ve hre kolem Y)."""

    def __init__(self, cx, cz, yaw):
        self.cx, self.cz, self.yaw = cx, cz, yaw

    def p(self, u, v):
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return self.cx + u * c + v * s, self.cz - u * s + v * c


def _wall(P, a, b, h0, h1, t=1.4, gaps=(), mat="zdivo_hole"):
    """Rozpadla zed z a do b (svet x, z): kusy 0.7-1.1 m, vyska nahodne mezi h0 a h1 (zubate temeno),
    v gaps (useky 0..1) proboreni az na zem. Kolize u kusu vyssich nez 0.5 m."""
    from lib import M
    ax, az = a
    bx, bz = b
    L = math.hypot(bx - ax, bz - az)
    if L < 0.3:
        return
    yaw = math.degrees(math.atan2(-(bz - az), bx - ax))         # mistni x podel zdi
    s = 0.0
    h = R.uniform(h0, h1)
    while s < L - 0.2:
        w = min(R.uniform(0.7, 1.1), L - s)
        t_ = (s + w / 2) / L
        s += w
        if any(g0 <= t_ <= g1 for g0, g1 in gaps):
            continue
        h = max(0.15, min(h1, h + R.uniform(-0.6, 0.6) * (h1 - h0) * 0.5))
        x, z = ax + (bx - ax) * t_, az + (bz - az) * t_
        y = _land(x, z) - 0.3
        P.box(M((x, y + (h + 0.3) / 2, z), yaw), (w + 0.04, h + 0.3, t * R.uniform(0.9, 1.05)), mat, collide=h > 0.5)


def _rect(P, F, u0, u1, v0, v1, h0, h1, t, door=None, mat="zdivo_hole"):
    """Obvod domu / ohrady z rozpadlych zdi; door = (strana 0-3, poloha 0..1) - vstup."""
    pts = [F.p(u0, v0), F.p(u1, v0), F.p(u1, v1), F.p(u0, v1)]
    for k in range(4):
        gaps = []
        if door and door[0] == k:
            gaps.append((door[1] - 0.12, door[1] + 0.12))
        if R.random() < 0.35:
            g = R.uniform(0.2, 0.8)
            gaps.append((g - 0.08, g + 0.08))          # proboreni
        _wall(P, pts[k], pts[(k + 1) % 4], h0, h1, t, gaps, mat)


def _plant(F, u, v, pid, h):
    x, z = F.p(u, v)
    ROSTLINY.append((pid, x, z, h))


def _kraj_ruiny(F, r, n_nettle, n_fern, n_bez, n_nalet, keep_out):
    """Zarust na okraji mytiny a u zdi; keep_out(u, v) = True tam, kde ma zustat pruchod."""
    import nove
    k = 0
    tries = 0
    while k < n_nettle + n_fern + n_bez + n_nalet and tries < 4000:
        tries += 1
        a = R.uniform(0, 2 * math.pi)
        d = r * math.sqrt(R.uniform(0.05, 1.0))
        u, v = math.cos(a) * d, math.sin(a) * d
        if keep_out(u, v):
            continue
        if R.random() < 0.45:
            _plant(F, u, v, "divoka_trava", R.uniform(0.5, 1.0))          # vysoka trava a plevel mezi sutí
        if R.random() < 0.3:
            _plant(F, u + R.uniform(-0.4, 0.4), v + R.uniform(-0.4, 0.4), "nettle_plant", R.uniform(0.4, 0.8))
        if k < n_nettle:
            _plant(F, u, v, "nettle_plant", R.uniform(0.35, 0.7))         # kopriva u sute a domu
        elif k < n_nettle + n_fern:
            _plant(F, u, v, "fern_02", R.uniform(0.5, 0.9))               # kapradi ve stinu
        elif k < n_nettle + n_fern + n_bez:
            x, z = F.p(u, v)
            pid = R.choice(["bez_cerny_1", "bez_cerny_2", "bez_cerny_3"])  # bez cerny - typicky ker zricenin
            nove.misto(pid, x, _land(x, z), z, R.uniform(0.7, 1.0), R.uniform(0, 2 * math.pi), None, sink=0.0)
        else:
            _plant(F, u, v, R.choice(["briza", "briza", "shrub_02"]), R.uniform(2.5, 6.0))   # nalet briz
        k += 1


def _wall_prof(P, a, b, hfun, t, gaps=(), okna=(), mat="zdivo_hole"):
    """Zed s vyskovym profilem hfun(t) (stit, presbytar) a okny okna = [(t0, t1, parapet, nadprazi)]."""
    from lib import M
    ax, az = a
    bx, bz = b
    L = math.hypot(bx - ax, bz - az)
    yaw = math.degrees(math.atan2(-(bz - az), bx - ax))
    s = 0.0
    while s < L - 0.15:
        w = min(R.uniform(0.6, 0.9), L - s)
        t_ = (s + w / 2) / L
        s += w
        if any(g0 <= t_ <= g1 for g0, g1 in gaps):
            continue
        h = max(0.2, hfun(t_) + R.uniform(-0.35, 0.35))
        x, z = ax + (bx - ax) * t_, az + (bz - az) * t_
        y = _land(x, z) - 0.3
        okno = [o for o in okna if o[0] <= t_ <= o[1]]
        if okno and h > okno[0][2]:
            sill, top = okno[0][2], okno[0][3]
            P.box(M((x, y + (sill + 0.3) / 2, z), yaw), (w + 0.03, sill + 0.3, t), mat, collide=True)
            if h > top + 0.2:
                P.box(M((x, y + 0.3 + (top + h) / 2, z), yaw), (w + 0.03, h - top, t), mat)
            continue
        P.box(M((x, y + (h + 0.3) / 2, z), yaw), (w + 0.03, h + 0.3, t * R.uniform(0.95, 1.05)), mat, collide=h > 0.5)


def kostel(P):
    """Zriceny romansko-goticky kostelik na lesni mytine (vlastni stavba ze zdiva): lod 12 x 7 m bez strechy,
    zapadni stit se vstupem, v bocnich zdech okna, na vychode polokruhovy presbytar; za nim hrbituvek."""
    id_, cx, cz, yaw, r = _ruina("kostel")
    F = _F(cx, cz, yaw)
    t = 0.95
    u0, u1, v0, v1 = -6.0, 6.0, -3.5, 3.5
    # zapadni stit: uprostred az 7 m, k okrajum 3 m; vstup uprostred
    _wall_prof(P, F.p(u0, v0), F.p(u0, v1), lambda q: 3.0 + 4.0 * (1 - abs(q - 0.5) * 2), t, gaps=[(0.42, 0.58)])
    # bocni zdi: postupne se rozpadaji k vychodu, okna (parapet 1.6, nadprazi 3.2), jedno proboreni
    _wall_prof(P, F.p(u0, v0), F.p(u1, v0), lambda q: 4.5 - 2.6 * q, t, gaps=[(0.62, 0.74)], okna=[(0.25, 0.33, 1.6, 3.2), (0.48, 0.56, 1.6, 3.2)])
    _wall_prof(P, F.p(u0, v1), F.p(u1, v1), lambda q: 4.2 - 3.4 * q * q, t, okna=[(0.25, 0.33, 1.6, 3.2), (0.48, 0.56, 1.6, 3.2), (0.8, 0.88, 1.4, 2.8)])
    # presbytar: polokruh na vychode, nizke zbytky, vitezny oblouk jen jako dva pilire
    n = 9
    pts = [F.p(u1 + math.sin(k / n * math.pi) * 3.3, -3.3 * math.cos(k / n * math.pi)) for k in range(n + 1)]
    for k in range(n):
        if k == 4:
            continue                                      # proboreni v zaveru
        _wall_prof(P, pts[k], pts[k + 1], lambda q, k=k: 1.0 + 1.6 * math.sin(k / n * math.pi), t * 0.9)
    for vv in (v0 + 0.7, v1 - 0.7):
        _wall_prof(P, F.p(u1 - 0.4, vv), F.p(u1 + 0.4, vv), lambda q: 4.0, 1.0)
    # zbytek oltarni menzy a sut uvnitr
    from lib import M
    x, z = F.p(u1 + 1.6, 0.0)
    P.box(M((x, _land(x, z) + 0.45, z), math.degrees(yaw)), (0.9, 1.0, 1.7), "kvadr_sedy", collide=True)
    import nove
    for _ in range(18):
        x, z = F.p(R.uniform(u0 + 1, u1 + 2), R.uniform(v0 + 0.8, v1 - 0.8) * (1.0 if R.random() < 0.5 else 1.1))
        pid = R.choice(nove.KAMENY_POLE + nove.KAMINKY)
        nove.misto(pid, x, _land(x, z), z, R.uniform(0.4, 0.8), R.uniform(0, 2 * math.pi), P, sink=0.35)
    # nalet uvnitr lodi: dve mlade brizy a ker bezu v koutech
    _plant(F, -4.6, 2.4, "briza", R.uniform(5.0, 7.0))
    _plant(F, 3.8, -2.5, "briza", R.uniform(3.5, 5.0))
    for u_, v_ in ((-4.8, -2.6), (4.5, 2.6), (8.2, 1.5)):
        for _ in range(6):
            _plant(F, u_ + R.uniform(-0.8, 0.8), v_ + R.uniform(-0.6, 0.6), R.choice(["nettle_plant", "fern_02", "divoka_trava"]), R.uniform(0.4, 0.9))
    # hrbitov za kostelem (v + 11): ohradni zed 16 x 11 m s branou ke kostelu
    _rect(P, F, -8.0, 8.0, 7.0, 18.0, 0.3, 1.1, 0.6, door=(0, 0.5))
    for i in range(9):
        u, v = R.uniform(-6.5, 6.5), R.uniform(9.0, 16.5)
        x, z = F.p(u, v)
        y = _land(x, z)
        lean = R.uniform(-14, 14)
        if R.random() < 0.2:
            continue                                    # uz jen hrob bez krize
        h = R.uniform(0.8, 1.3)
        ry = math.degrees(yaw) + R.uniform(-8, 8)
        m = M((x, y, z), ry) @ __import__("mathutils").Matrix.Rotation(math.radians(lean), 4, "Z")
        P.box(m @ M((0, h / 2 - 0.15, 0)), (0.08, h + 0.3, 0.07), "dub_ven")
        P.box(m @ M((0, h * 0.72, 0)), (0.5, 0.07, 0.06), "dub_ven")
        # hrobovy rov: nizka vyvysenina z hliny a kamenu
        for _ in range(3):
            import krajina
            krajina.rock(P, (x + R.uniform(-0.3, 0.3), y, z + R.uniform(0.3, 1.4)), (R.uniform(0.2, 0.35), 0.12, R.uniform(0.2, 0.3)), 0.4,
                         collide=False)

    def keep_out(u, v):
        # uvnitr lodi a presbytare, pristup k zapadnimu vstupu a branka hrbitova volne; hroby jen zcasti zarostle
        return ((-7.0 < u < 10.0 and abs(v) < 4.3) or (u < -6.0 and abs(v) < 1.6) or (abs(u) < 1.5 and 3.5 < v < 8.0)
                or (abs(u) < 7.5 and 7.5 < v < 17.5 and R.random() < 0.7))
    _kraj_ruiny(F, r + 6, 120, 60, 12, 16, keep_out)
    NAZVY.append({"name": kraj.RUINY_NAZVY[id_], "x": cx, "z": cz, "r": r + 12})


def zanikla_ves(P):
    """Zanikla ves: pet usedlosti radou podel nekdejsi navsi (cesty) - nizke kamenne podezdivky domu se vstupem,
    ohorele tramy, kamenna studna uprostred. Okolo kopriva a bez (dusik po lidech), v nekterych domech nalet briz."""
    from lib import M
    id_, cx, cz, yaw, r = _ruina("zanikla_ves")
    F = _F(cx, cz, yaw)
    import nove
    for i in range(5):
        u = -18.0 + i * 9.0 + R.uniform(-0.8, 0.8)
        side = 1 if i % 2 == 0 else -1
        v0 = side * R.uniform(4.0, 5.0)
        v1 = v0 + side * R.uniform(5.0, 6.5)
        L = R.uniform(7.0, 8.5)
        _rect(P, F, u - L / 2, u + L / 2, min(v0, v1), max(v0, v1), 0.15, 0.8, 0.55, door=(0 if side > 0 else 2, R.uniform(0.3, 0.7)))
        # ohorele tramy a kameny ze zdi
        for _ in range(R.randint(2, 4)):
            a = F.p(u + R.uniform(-L / 3, L / 3), (v0 + v1) / 2 + R.uniform(-1.5, 1.5))
            d = R.uniform(0, 2 * math.pi)
            ln = R.uniform(1.2, 3.0)
            y = _land(*a)
            P.beam((a[0], y + 0.1, a[1]), (a[0] + math.cos(d) * ln, y + R.uniform(0.05, 0.4), a[1] + math.sin(d) * ln),
                   R.uniform(0.14, 0.22), R.uniform(0.12, 0.2), "tma", j=0.8)
        for _ in range(R.randint(4, 8)):
            x, z = F.p(u + R.uniform(-L / 2 - 1, L / 2 + 1), v0 + side * R.uniform(-1.0, 7.0))
            pid = R.choice(nove.KAMENY_POLE + nove.KAMINKY)
            nove.misto(pid, x, _land(x, z), z, R.uniform(0.4, 0.9), R.uniform(0, 2 * math.pi), P, sink=0.35)
        if R.random() < 0.6:
            _plant(F, u + R.uniform(-1.5, 1.5), (v0 + v1) / 2 + R.uniform(-1, 1), "briza", R.uniform(4.0, 8.0))   # nalet v dome
    # studna uprostred navsi: kamenny venec, uvnitr tma
    x, z = F.p(1.0, 0.0)
    y = _land(x, z)
    for k in range(14):
        a = k / 14 * 2 * math.pi
        P.box(M((x + math.cos(a) * 0.95, y + 0.3, z + math.sin(a) * 0.95), math.degrees(math.atan2(-math.cos(a), -math.sin(a)))),
              (0.45, 0.6 + R.uniform(-0.15, 0.1), 0.3), "zdivo_hole", collide=True)
    P.box(M((x, y + 0.04, z)), (1.5, 0.02, 1.5), "tma")

    def keep_out(u, v):
        return abs(v) < 3.2 or (abs(u) < 2.5 and abs(v) < 3.5)       # bývalá náves / cesta průchozí
    _kraj_ruiny(F, r + 6, 160, 60, 16, 18, keep_out)
    NAZVY.append({"name": kraj.RUINY_NAZVY[id_], "x": cx, "z": cz, "r": r + 14})


def hradek(P):
    """Zricenina hradku na piskovcovem hrebeni: dve okrouhle veze (modely), mezi nimi a okolo zbytky hradby
    s proborenimi, pod zdmi sut z piskovce; na sutich bez a kopriva, na zdech nalet."""
    id_, cx, cz, yaw, r = _ruina("hradek")
    F = _F(cx, cz, yaw)
    import nove
    for pid, u, v, dy in (("ruina_vez_1", -7.0, 0.0, -0.4), ("ruina_vez_2", 8.0, 3.0, -0.3)):
        x, z = F.p(u, v)
        STATICKE.append((pid, x, z, yaw + R.uniform(-0.5, 0.5), dy))
    # obvodova hradba (ovál ~ 34 x 22 m) z rozpadlych useku, branou na jihu a proborenimi
    n = 14
    pts = [F.p(math.cos(k / n * 2 * math.pi) * 16.0, math.sin(k / n * 2 * math.pi) * 10.5) for k in range(n)]
    for k in range(n):
        if k in (3, 9):
            continue                                  # brana a velke proboreni
        _wall(P, pts[k], pts[(k + 1) % n], 0.4, 3.6 if k % 3 else 2.0, 1.6, gaps=[(0.4, 0.55)] if R.random() < 0.3 else [])
    # spojovaci zed mezi vezemi (zbytek palace)
    _wall(P, F.p(-3.0, -1.0), F.p(4.0, 1.5), 1.0, 4.5, 1.4, gaps=[(0.45, 0.6)])
    # sut z piskovce pod zdmi
    for _ in range(45):
        a = R.uniform(0, 2 * math.pi)
        x, z = F.p(math.cos(a) * R.uniform(13.0, 18.0), math.sin(a) * R.uniform(8.0, 12.5))
        pid = R.choice(nove.KAMENY_PISKOVEC + nove.KAMINKY + ["balvan_piskovec_2"])
        nove.misto(pid, x, _land(x, z), z, R.uniform(0.5, 1.2), R.uniform(0, 2 * math.pi), P, sink=0.3)

    def keep_out(u, v):
        e = (u / 14.0) ** 2 + (v / 8.5) ** 2
        return e < 1.0 and R.random() < 0.85              # nadvori hradku vetsinou volne
    _kraj_ruiny(F, r + 5, 120, 40, 12, 14, keep_out)
    NAZVY.append({"name": kraj.RUINY_NAZVY[id_], "x": cx, "z": cz, "r": r + 14})


def build(coll):
    from lib import Part
    ROSTLINY.clear()
    STATICKE.clear()
    NAZVY.clear()
    P = Part("Ruiny", bevel=0.0)
    kostel(P)
    zanikla_ves(P)
    hradek(P)
    P.commit(coll)
    print("ruiny: %d modelu, %d rostlin" % (len(STATICKE), len(ROSTLINY)))
