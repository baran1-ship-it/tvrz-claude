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


def _pata(P, x, z, nx, nz, w, h, t, rozval=False):
    """Pata zdi: z obou stran sutovy val (nizky kopecek a napul zapadle kameny ze zdi) a na nem nejhustsi zarust.
    rozval = proboreni (zed tu spadla): hromada kameni pres celou sirku."""
    import krajina
    import nove
    for sd in ((-1, 1) if not rozval else (0,)):
        d = t / 2 + R.uniform(0.25, 0.7)
        cx, cz = x + nx * d * sd, z + nz * d * sd
        # kopecek sute: vyssi u vysoke zdi, v rozvalu nejvyssi
        hm = (0.18 + 0.06 * min(h, 5.0)) * (2.2 if rozval else 1.0)
        krajina.rock(P, (cx, _land(cx, cz), cz), (w * R.uniform(1.0, 1.5), hm, R.uniform(0.8, 1.4) * (1.6 if rozval else 1.0)), 0.55,
                     collide=False)
        for _ in range(R.randint(1, 3) + (3 if rozval else 0)):
            dd = d + R.uniform(-0.3, 0.9)
            xx, zz = x + nx * dd * sd + R.uniform(-w / 2, w / 2) * nz, z + nz * dd * sd - R.uniform(-w / 2, w / 2) * nx
            pid = R.choice(nove.KAMINKY + nove.KAMENY_POLE) if R.random() < 0.7 else R.choice(nove.KAMINKY)
            nove.misto(pid, xx, _land(xx, zz), zz, R.uniform(0.6, 1.3), R.uniform(0, 2 * math.pi), None, sink=0.45)
        # zarust u paty: kopriva, kapradi, vysoka trava; obcas bez nebo nalet
        for _ in range(R.randint(2, 4)):
            dd = t / 2 + R.uniform(0.1, 1.3)
            xx, zz = x + nx * dd * (sd or R.choice((-1, 1))) + R.uniform(-w / 2, w / 2) * nz, z + nz * dd * (sd or 1) - R.uniform(-w / 2, w / 2) * nx
            k = R.random()
            if k < 0.32:
                ROSTLINY.append(("nettle_plant", xx, zz, R.uniform(0.5, 1.0)))
            elif k < 0.5:
                ROSTLINY.append(("fern_02", xx, zz, R.uniform(0.6, 1.0)))
            elif k < 0.6:
                ROSTLINY.append(("celandine_01", xx, zz, R.uniform(0.3, 0.6)))        # vlastovicnik u zdi
            elif k < 0.68:
                ROSTLINY.append(("periwinkle_plant", xx, zz, R.uniform(0.15, 0.3)))   # barvinek (stare hrbitovy, zriceniny)
            elif k < 0.93:
                ROSTLINY.append(("divoka_trava", xx, zz, R.uniform(0.6, 1.1)))
            elif k < 0.97:
                nove.misto(R.choice(["bez_cerny_1", "bez_cerny_2", "bez_cerny_3"]), xx, _land(xx, zz), zz, R.uniform(0.5, 0.8),
                           R.uniform(0, 2 * math.pi), None, sink=0.0)
            else:
                ROSTLINY.append(("briza", xx, zz, R.uniform(2.0, 4.5)))


def _sum1(seed):
    """Hladky 1D sum (hodnoty -1..1) pro rozpadlou korunu zdi."""
    rr = random.Random(seed)
    k = [rr.uniform(-1.0, 1.0) for _ in range(97)]

    def f(x):
        i = math.floor(x)
        u = x - i
        u = u * u * (3 - 2 * u)
        return k[i % 97] * (1 - u) + k[(i + 1) % 97] * u
    return f


def _wall_mesh(P, a, b, hfun, t, gaps=(), okna=(), mat="zdivo_hole", amp=0.55, sut=True):
    """Rozpadla zed z a do b (svet x, z) ze zdiva ve vrstvach: kusy 0.3-0.8 m, kazdy jinak vysoky po vrstvach
    kamene (stupnovite vylamana koruna jako u skutecnych zricenin), mirne sikma temena, k proborenim (gaps,
    useky 0..1) zed sbiha az k zemi; okna = [(t0, t1, parapet, nadprazi)]. UV v metrech (zdivo neni natazene).
    U paty sutovy val a zarust (_pata), na korune mech a uvolnene kameny, kolize po kusech."""
    from lib import M
    import nove
    ax, az = a
    bx, bz = b
    L = math.hypot(bx - ax, bz - az)
    if L < 0.3:
        return
    dx, dz = (bx - ax) / L, (bz - az) / L
    nx, nz = -dz, dx
    yaw = math.degrees(math.atan2(-(bz - az), bx - ax))
    f = _sum1(R.randrange(1 << 30))
    ofs = R.uniform(0, 50)
    VR = 0.18                                           # vrstva kamene

    def in_gap(tt):
        return any(g0 <= tt <= g1 for g0, g1 in gaps)

    def gap_dist(s_):
        d = 99.0
        for g0, g1 in gaps:
            d = min(d, abs(s_ - g0 * L), abs(s_ - g1 * L))
        return d

    def blok(s0, s1, lo0, lo1, hi0, hi1, tt_, uo):
        """Kvadr zdiva od s0 do s1: spodek lo0/lo1, temeno hi0/hi1 (absolutni y); tt_ = tloustka."""
        p0 = (ax + dx * s0, az + dz * s0)
        p1 = (ax + dx * s1, az + dz * s1)
        h2 = tt_ / 2
        V = [(p0[0] + nx * h2, lo0, p0[1] + nz * h2), (p1[0] + nx * h2, lo1, p1[1] + nz * h2),
             (p1[0] + nx * h2, hi1, p1[1] + nz * h2), (p0[0] + nx * h2, hi0, p0[1] + nz * h2),
             (p0[0] - nx * h2, lo0, p0[1] - nz * h2), (p1[0] - nx * h2, lo1, p1[1] - nz * h2),
             (p1[0] - nx * h2, hi1, p1[1] - nz * h2), (p0[0] - nx * h2, hi0, p0[1] - nz * h2)]
        Fc = [(0, 1, 2, 3), (5, 4, 7, 6), (3, 2, 6, 7), (4, 0, 3, 7), (1, 5, 6, 2)]
        u0, u1 = s0 + uo, s1 + uo
        UV = [[(u0, lo0), (u1, lo1), (u1, hi1), (u0, hi0)],
              [(-u1, lo1), (-u0, lo0), (-u0, hi0), (-u1, hi1)],
              [(u0, h2), (u1, h2), (u1, -h2), (u0, -h2)],
              [(-h2, lo0), (h2, lo0), (h2, hi0), (-h2, hi0)],
              [(h2, lo1), (-h2, lo1), (-h2, hi1), (h2, hi1)]]
        P.mesh(V, Fc, mat, UV)
    uo = R.uniform(0, 7)
    s_ = 0.0
    kus = []
    while s_ < L - 0.05:
        w = min(R.uniform(0.3, 0.8), L - s_)
        if L - s_ - w < 0.2:
            w = L - s_
        s0, s1 = s_, s_ + w
        s_ += w
        tm = (s0 + s1) / 2 / L
        if in_gap(tm):
            kus.append((s0, s1, None))
            continue
        h = hfun(tm) + amp * f((s0 + s1) / 2 / 2.6 + ofs) + amp * 0.35 * f((s0 + s1) / 2 / 0.9 + ofs * 2)
        if gaps:
            h *= 0.15 + 0.85 * kraj.smooth(0.0, 1.8, gap_dist((s0 + s1) / 2))     # u proboreni zed sbiha k zemi
        h = max(VR, round(h / VR) * VR + R.uniform(-0.03, 0.03))
        kus.append((s0, s1, h))
    for s0, s1, h in kus:
        x0, z0 = ax + dx * s0, az + dz * s0
        x1, z1 = ax + dx * s1, az + dz * s1
        xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
        w = s1 - s0
        if h is None:
            if sut and R.random() < 0.6:
                _pata(P, xm, zm, nx, nz, w, 1.0, t, rozval=True)
            continue
        g0, g1 = _land(x0, z0) - 0.3, _land(x1, z1) - 0.3
        gm = (g0 + g1) / 2
        sk = R.uniform(-0.07, 0.07)                       # temeno kusu mirne sikme
        tt_ = t * R.uniform(0.94, 1.03)
        tm = (s0 + s1) / 2 / L
        ok = [o for o in okna if o[0] <= tm <= o[1]]
        if ok and h > ok[0][2]:
            sill, top = ok[0][2], ok[0][3]
            blok(s0, s1, g0, g1, gm + 0.3 + sill, gm + 0.3 + sill, tt_, uo)
            if h > top + 0.25:
                blok(s0, s1, gm + 0.3 + top, gm + 0.3 + top, gm + 0.3 + h - sk, gm + 0.3 + h + sk, tt_, uo)
            hc = sill
        else:
            blok(s0, s1, g0, g1, gm + 0.3 + h - sk, gm + 0.3 + h + sk, tt_, uo)
            hc = h
        if hc > 0.5:
            P.cols.append((M((xm, gm + (hc + 0.3) / 2, zm), yaw), (w + 0.02, hc + 0.3, tt_)))
        # na korune: mech, sem tam uvolneny kamen
        if R.random() < 0.3:
            nove.misto(R.choice(["mech_1", "mech_2", "mech_3"]), xm, gm + 0.3 + hc + 0.01, zm, R.uniform(0.5, 1.0),
                       R.uniform(0, 2 * math.pi), None, sink=0.0)
        if R.random() < 0.15:
            nove.misto(R.choice(nove.KAMINKY), xm + R.uniform(-0.2, 0.2), gm + 0.3 + hc, zm, R.uniform(1.0, 2.2),
                       R.uniform(0, 2 * math.pi), None, sink=0.1)
        if sut:
            _pata(P, xm, zm, nx, nz, w, hc, t)


def _wall(P, a, b, h0, h1, t=1.4, gaps=(), mat="zdivo_hole"):
    """Rozpadla zed z a do b (svet x, z): vyska kolem h0..h1, nepravidelne vylamana koruna, v gaps proboreni."""
    hm = (h0 + h1) / 2
    _wall_mesh(P, a, b, lambda tt: hm, t, gaps, (), mat, amp=max(0.25, (h1 - h0) * 0.6))


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
    """Zarust na okraji mytiny a u zdi; keep_out(u, v) = True tam, kde ma zustat pruchod.
    Na okraji ruiny par vzrostlych buku a dubu (stromy v2), na suti mech."""
    import nove
    for _ in range(R.randint(3, 5)):
        a = R.uniform(0, 2 * math.pi)
        x, z = F.p(math.cos(a) * (r + R.uniform(2.0, 7.0)), math.sin(a) * (r + R.uniform(2.0, 7.0)))
        nove.strom(R.choice(["buk_stredni", "buk_stredni", "dub_stredni"]), x, _land(x, z), z, R.uniform(13, 18))
    for _ in range(R.randint(1, 3)):
        a = R.uniform(0, 2 * math.pi)
        x, z = F.p(math.cos(a) * (r + R.uniform(0.0, 4.0)), math.sin(a) * (r + R.uniform(0.0, 4.0)))
        ROSTLINY.append((R.choice(["dead_tree_trunk", "dead_tree_trunk_02", "tree_stump_02"]), x, z, R.uniform(0.5, 1.2)))
    for _ in range(25):
        a = R.uniform(0, 2 * math.pi)
        d = r * math.sqrt(R.uniform(0.1, 1.0))
        x, z = F.p(math.cos(a) * d, math.sin(a) * d)
        nove.misto(R.choice(["mech_1", "mech_2", "mech_3"]), x, _land(x, z), z, R.uniform(1.0, 2.5), R.uniform(0, 2 * math.pi), None, sink=0.0)
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
            if R.random() < 0.5:
                _plant(F, u, v, "fern_02", R.uniform(0.5, 0.9))           # kapradi ve stinu
            else:
                x, z = F.p(u, v)
                pid = R.choice(["kapradi_1", "kapradi_2", "kapradi_3"])
                nove.misto(pid, x, _land(x, z), z, R.uniform(0.7, 1.1), R.uniform(0, 2 * math.pi), None, sink=0.05)
        elif k < n_nettle + n_fern + n_bez:
            x, z = F.p(u, v)
            pid = R.choice(["bez_cerny_1", "bez_cerny_2", "bez_cerny_3"])  # bez cerny - typicky ker zricenin
            nove.misto(pid, x, _land(x, z), z, R.uniform(0.7, 1.0), R.uniform(0, 2 * math.pi), None, sink=0.0)
        else:
            _plant(F, u, v, R.choice(["briza", "briza", "shrub_02"]), R.uniform(2.5, 6.0))   # nalet briz
        k += 1


def _wall_prof(P, a, b, hfun, t, gaps=(), okna=(), mat="zdivo_hole"):
    """Zed s vyskovym profilem hfun(t) (stit, presbytar) a okny okna = [(t0, t1, parapet, nadprazi)]."""
    _wall_mesh(P, a, b, hfun, t, gaps, okna, mat, amp=0.45)


def kostel(P):
    """Zricenina gotickeho kostela (Misa 15. 11.: nahrada za nas kostel, Disk kostel_ruiny.zip, NAVOD_KOSTEL.md): model
    stavi hra (svet._kostel_dil, lokace.json ruiny kostel model), tady jen porost - „at je taky hezky zarostly“:
    nalet a ker na znackach modelu (rostliny_lok), kopriva, bez, kapradi a vysoka trava kolem zdi a na hrbitove mimo
    pudorys zdi (stavba_lok) a volne pruchody (pruchody_lok); na okraji mytiny buky a duby (_kraj_ruiny)."""
    id_, cx, cz, yaw, r = _ruina("kostel")
    F = _F(cx, cz, yaw)
    import nove
    rec = [e for e in kraj._LOKACE_J["ruiny"] if e["id"] == "kostel"][0]
    for druh, u, v, h in rec.get("rostliny_lok", []):
        if druh == "bez":
            x, z = F.p(u, v)
            nove.misto(R.choice(["bez_cerny_1", "bez_cerny_2", "bez_cerny_3"]), x, _land(x, z), z, h, R.uniform(0, 2 * math.pi), None, sink=0.0)
        else:
            _plant(F, u, v, druh, h)
    stavba = rec.get("stavba_lok", [])
    pruchody = rec.get("pruchody_lok", [])

    def v_pruchodu(u, v):
        for u0, v0, u1, v1, w in pruchody:
            du, dv = u1 - u0, v1 - v0
            t = max(0.0, min(1.0, ((u - u0) * du + (v - v0) * dv) / max(du * du + dv * dv, 1e-6)))
            if math.hypot(u - (u0 + du * t), v - (v0 + dv * t)) < w:
                return True
        return False

    def keep_out(u, v):
        return any(a - 0.4 < u < c + 0.4 and b - 0.4 < v < e + 0.4 for a, b, c, e in stavba) or v_pruchodu(u, v)
    # hodne zarostle: kolem zdi a na hrbitove (Misa „hezky zarostly“) - vic koprivy, bezu a naletu nez stary kostelik
    _kraj_ruiny(F, r, 160, 70, 18, 14, keep_out)
    NAZVY.append({"name": kraj.RUINY_NAZVY[id_], "x": cx, "z": cz, "r": r + 12})


def zanikla_ves(P):
    """Zanikla ves Doubrava (Misa 15. 11.: Disk vesnice_ruiny.zip, NAVOD_VES.md „mam novou vesnici ruin, myslim, ze je
    lepsi“): dily (domy, usedlost, stodoly, studna, sklep, zidky, snosy) stavi hra (svet._ruiny_ves_dil, lokace.json
    ruiny zanikla_ves dily) na rovince pod kazdym dilem (kraj.MISTA ruiny_ves_N). Model je bez vegetace - tady porost:
    kopriva, bez, kapradi a nalet briz kolem zdi (dusik po lidech), ne v pudorysu zdi (pudorysy zdi), ne ve dverich,
    sini, brane, pruchodu stodoly a vchodu sklepa (pudorysy pruchody) ani na ose navsi (pruchody_lok); trava smi."""
    id_, cx, cz, yaw, r = _ruina("zanikla_ves")
    F = _F(cx, cz, yaw)
    rec = [e for e in kraj._LOKACE_J["ruiny"] if e["id"] == "zanikla_ves"][0]
    stavba = []                    # obdelniky zdi dilu v souradnicich vsi: (u, v stredu, cos, sin, x0, z0, x1, z1)
    pruchody = [tuple(p) for p in rec.get("pruchody_lok", [])]
    for sb, du, dv, st in rec.get("dily", []):
        a = math.radians(st)
        c, s = math.cos(a), math.sin(a)
        pud = rec["pudorysy"][sb]
        for b in pud["zdi"]:
            stavba.append((du, dv, c, s) + tuple(b))
        for x0, z0, x1, z1, w in pud["pruchody"]:
            pruchody.append((du + x0 * c + z0 * s, dv - x0 * s + z0 * c, du + x1 * c + z1 * s, dv - x1 * s + z1 * c, w))

    def v_zdi(u, v, m):
        for du, dv, c, s, x0, z0, x1, z1 in stavba:
            lu, lv = u - du, v - dv
            lx, lz = lu * c - lv * s, lu * s + lv * c          # zpet do souradnic dilu (inverze otoceni kolem Y)
            if x0 - m < lx < x1 + m and z0 - m < lz < z1 + m:
                return True
        return False

    def v_pruchodu(u, v):
        for u0, v0, u1, v1, w in pruchody:
            du, dv = u1 - u0, v1 - v0
            t = max(0.0, min(1.0, ((u - u0) * du + (v - v0) * dv) / max(du * du + dv * dv, 1e-6)))
            if math.hypot(u - (u0 + du * t), v - (v0 + dv * t)) < w:
                return True
        return False

    def keep_out(u, v):
        return v_zdi(u, v, 0.4) or v_pruchodu(u, v)
    # porost hlavne u zdi: _kraj_ruiny sazi po cele mytine, u kazdeho dilu navic kopriva a bez kolem obvodu
    _kraj_ruiny(F, r, 260, 90, 26, 30, keep_out)
    import nove
    for du, dv, c, s, x0, z0, x1, z1 in stavba:
        obvod = 2 * ((x1 - x0) + (z1 - z0))
        for _ in range(int(obvod / 2.5)):
            k = R.uniform(0, obvod)
            d = R.uniform(0.5, 1.6)
            if k < x1 - x0:
                lx, lz = x0 + k, z0 - d
            elif k < (x1 - x0) * 2:
                lx, lz = x0 + k - (x1 - x0), z1 + d
            elif k < (x1 - x0) * 2 + (z1 - z0):
                lx, lz = x0 - d, z0 + k - 2 * (x1 - x0)
            else:
                lx, lz = x1 + d, z0 + k - 2 * (x1 - x0) - (z1 - z0)
            u, v = du + lx * c + lz * s, dv - lx * s + lz * c
            if keep_out(u, v):
                continue
            q = R.random()
            if q < 0.45:
                _plant(F, u, v, "nettle_plant", R.uniform(0.5, 1.0))
            elif q < 0.65:
                _plant(F, u, v, "fern_02", R.uniform(0.6, 1.0))
            elif q < 0.8:
                _plant(F, u, v, "divoka_trava", R.uniform(0.6, 1.1))
            elif q < 0.93:
                x, z = F.p(u, v)
                nove.misto(R.choice(["bez_cerny_1", "bez_cerny_2", "bez_cerny_3"]), x, _land(x, z), z, R.uniform(0.6, 0.9),
                           R.uniform(0, 2 * math.pi), None, sink=0.0)
            else:
                _plant(F, u, v, "briza", R.uniform(2.5, 5.5))   # mlady nalet briz u zdi
    NAZVY.append({"name": kraj.RUINY_NAZVY[id_], "x": cx, "z": cz, "r": r + 14})


def _studna(P, x, z):
    """Kulata roubena studna z lomoveho kamene: venec (vnejsi r 1.15, vnitrni 0.72) s vylamanou korunou."""
    from lib import M
    y = _land(x, z) - 0.25
    n = 30
    f = _sum1(R.randrange(1 << 30))
    V, Fc = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        h = 0.95 + 0.3 * f(i / 4.0) + R.uniform(-0.06, 0.06)
        if 9 <= i <= 13:
            h -= 0.45 * math.sin((i - 9) / 4 * math.pi)                # vylomene misto
        ro, ri = 1.15 + R.uniform(-0.03, 0.03), 0.72 + R.uniform(-0.03, 0.03)
        c, s_ = math.cos(a), math.sin(a)
        V += [(x + c * ro, y, z + s_ * ro), (x + c * ri, y - 1.5, z + s_ * ri),
              (x + c * (ri + R.uniform(0, 0.05)), y + h, z + s_ * (ri + R.uniform(0, 0.05))),
              (x + c * (ro - R.uniform(0, 0.06)), y + h - R.uniform(0, 0.06), z + s_ * (ro - R.uniform(0, 0.06)))]
    for i in range(n):
        q, r_ = 4 * i, 4 * ((i + 1) % n)
        Fc.append((q + 0, q + 3, r_ + 3, r_ + 0))          # vnejsi lic
        Fc.append((r_ + 1, r_ + 2, q + 2, q + 1))          # vnitrni lic
        Fc.append((q + 3, q + 2, r_ + 2, r_ + 3))          # koruna
    P.mesh(V, Fc, "zdivo_hole")
    P.lathe(M((x, y - 1.2, z)), [(0.74, 0.0), (0.0, 0.01)], 16, "tma")
    for k in range(8):
        a = k * 2 * math.pi / 8
        P.cols.append((M((x + math.cos(a) * 0.93, y + 0.5, z + math.sin(a) * 0.93), math.degrees(-a)), (0.5, 1.0, 0.45)))
    import nove
    for _ in range(4):
        a = R.uniform(2.0, 3.3)
        d = R.uniform(1.4, 2.2)
        xx, zz = x + math.cos(a) * d, z + math.sin(a) * d
        nove.misto(R.choice(nove.KAMENY_POLE), xx, _land(xx, zz), zz, R.uniform(0.4, 0.7), R.uniform(0, 6.28), P, sink=0.3)


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
    P.decimace = ("skala", 30000)          # rozpocet: kamen ruin 113 tis. -> 30 tis. troj.
    kostel(P)
    zanikla_ves(P)
    hradek(P)
    P.commit(coll)
    print("ruiny: %d modelu, %d rostlin" % (len(STATICKE), len(ROSTLINY)))
