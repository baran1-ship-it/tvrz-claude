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
ODBOCKA = [CROSS, (36.0, 432.0), (110.0, 492.0), (225.0, 600.0), (340.0, 712.0), (398.0, 766.0)]
CESTY = [(HLAVNI, 3.4), (ODBOCKA, 2.8)]

NEAR = (-60.0, 60.0, -55.0, 70.0)          # pasmo 1 m (fort.terrain)
ACT = (-250.0, 900.0, -250.0, 1350.0)      # pasmo 5 m
VRECT = (310.0, 630.0, 670.0, 990.0)        # pasmo 2 m ve vesnici (drobne nerovnosti, krtince)
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


def ves_r(x, z):
    """Nepravidelna 'vzdalenost od vsi': pokrivena sumem a protazena, aby myti, pole ani kopce kolem vsi
    netvorily kruh (krajina kolem vsi je ruzne siroka podle terenu a historie)."""
    dx, dz = x - VES[0], z - VES[1]
    wx = 70.0 * perlin(x / 230.0 + 1.7, z / 230.0 - 4.1) + 28.0 * perlin(x / 85.0 + 6.0, z / 85.0 + 3.0)
    wz = 70.0 * perlin(x / 230.0 - 8.2, z / 230.0 + 2.6) + 28.0 * perlin(x / 85.0 - 2.0, z / 85.0 - 7.0)
    r = math.hypot(dx + wx, dz + wz)
    a = math.atan2(dz, dx)
    return r * (1.0 + 0.2 * math.sin(2.0 * a + 0.6) + 0.12 * perlin(a * 1.3 + 4.0, r / 300.0 + 9.0))


# ---- hony poli (bloky lanu s vlastnim smerem) - stejna celociselna nahoda jako v shaders/zem.gdshader

HON = 125.0                                # rozestup stredu honu (m)


def _hash(v):
    v &= 0xFFFFFFFF
    v ^= v >> 16
    v = (v * 0x7FEB352D) & 0xFFFFFFFF
    v ^= v >> 15
    v = (v * 0x846CA68B) & 0xFFFFFFFF
    v ^= v >> 16
    return v


def _cell_hash(ci, cj):
    return _hash((((ci + 1000) * 73856093) ^ ((cj + 1000) * 19349663)) & 0xFFFFFFFF)


def hon(x, z):
    """Nejblizsi hon (Voronoi): (hash, vzdalenost k hranici honu, souradnice napric lany v m, sirka lanu)."""
    gx, gz = math.floor(x / HON), math.floor(z / HON)
    best = (1e18, 0, 0.0, 0.0)
    second = 1e18
    for i in range(gx - 1, gx + 2):
        for j in range(gz - 1, gz + 2):
            h = _cell_hash(i, j)
            sx = (i + 0.15 + 0.7 * ((h & 0xFFFF) / 65535.0)) * HON
            sz = (j + 0.15 + 0.7 * ((h >> 16) / 65535.0)) * HON
            d = (x - sx) ** 2 + (z - sz) ** 2
            if d < best[0]:
                second = best[0]
                best = (d, h, sx, sz)
            elif d < second:
                second = d
    d1, h, sx, sz = best
    edge = (math.sqrt(second) - math.sqrt(d1)) * 0.5
    h2 = _hash(h ^ 0x9E3779B9)
    ang = (h2 & 0xFFFF) / 65535.0 * math.pi
    w = 9.0 + 9.0 * ((h2 >> 16) / 65535.0)
    t = x * -math.sin(ang) + z * math.cos(ang)
    return h, edge, t, w


# ---- cesty a potok se klikati (stare cesty obchazely terenni prekazky, nikdy nesly po pravitku)

def _meander(path, amp, wl, seed, taper0=50.0, taper1=50.0, step=6.0, start=0.0):
    """Lomenou caru prevzorkuje po 'step' m a vychyli kolmo nizkofrekvencnim sumem (zakruty),
    na koncich (taper) bez vychyleni, aby navazovala na branu, krizovatku a ves."""
    pts = []
    for (ax, az), (bx, bz) in zip(path[:-1], path[1:]):
        L = math.hypot(bx - ax, bz - az)
        n = max(1, int(L / step))
        for i in range(n):
            t = i / n
            pts.append((ax + (bx - ax) * t, az + (bz - az) * t))
    pts.append(path[-1])
    acc = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = acc[-1]
    out = []
    for i, (x, z) in enumerate(pts):
        a = pts[max(0, i - 2)]
        b = pts[min(len(pts) - 1, i + 2)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / L, dx / L
        s_ = acc[i]
        f = (smooth(start, start + taper0, s_) if taper0 > 0 else 1.0) * (smooth(0.0, taper1, tot - s_) if taper1 > 0 else 1.0)
        o = amp * (perlin(s_ / wl + seed, seed * 0.37) * 1.25 + 0.35 * perlin(s_ / (wl * 0.37) - seed, 2.0 + seed))
        out.append((x + nx * o * f, z + nz * o * f))
    # vyhlazeni (zadne ostre lomy)
    sm = []
    for i in range(len(out)):
        a = out[max(0, i - 2):i + 3]
        sm.append((sum(p[0] for p in a) / len(a), sum(p[1] for p in a) / len(a)))
    sm[0], sm[-1] = out[0], out[-1]
    return sm


def _setup_paths():
    global HLAVNI, ODBOCKA, CESTY, CROSS, REKA
    raw = HLAVNI
    HLAVNI = _meander(raw, 75.0, 170.0, 3.3, taper0=170.0, taper1=0.0, start=75.0)
    # krizovatka: bod klikate hlavni cesty nejblize puvodni
    CROSS = min(HLAVNI, key=lambda p: (p[0] - CROSS[0]) ** 2 + (p[1] - CROSS[1]) ** 2)
    ODBOCKA = _meander([CROSS] + ODBOCKA[1:], 60.0, 130.0, 7.1, taper0=40.0, taper1=45.0)
    CESTY = [(HLAVNI, 3.4), (ODBOCKA, 2.8)]
    # potok Bystrice: od severovychodu z lesa, udolim pod odbockou (most), luhem na jih
    REKA = _meander([(940.0, 120.0), (720.0, 300.0), (520.0, 430.0), (330.0, 520.0), (215.0, 610.0), (165.0, 730.0),
                     (185.0, 880.0), (245.0, 1060.0), (300.0, 1250.0), (330.0, 1500.0)], 50.0, 90.0, 11.7, 0.0, 0.0, step=5.0)


REKA = []
_setup_paths()


def _road_point(path, dist):
    """Bod a smer na lomene care ve vzdalenosti dist od zacatku."""
    acc = 0.0
    for (ax, az), (bx, bz) in zip(path[:-1], path[1:]):
        L = math.hypot(bx - ax, bz - az)
        if acc + L >= dist:
            t = (dist - acc) / L
            return ax + (bx - ax) * t, az + (bz - az) * t, (bx - ax) / L, (bz - az) / L
        acc += L
    (ax, az), (bx, bz) = path[-2], path[-1]
    L = math.hypot(bx - ax, bz - az)
    return bx, bz, (bx - ax) / L, (bz - az) / L


def _arc_to(path, pt):
    acc, best = 0.0, (1e18, 0.0)
    for (ax, az), (bx, bz) in zip(path[:-1], path[1:]):
        L = math.hypot(bx - ax, bz - az)
        d = math.hypot(ax - pt[0], az - pt[1])
        if d < best[0]:
            best = (d, acc)
        acc += L
    return best[1]


def _stavby():
    """Stavby u hlavni cesty (vpravo pri ceste od tvrze, tj. na -x strane):
    kupecky stan 200 m od brany 10 m od cesty, zajezdni hostinec 500 m za odbockou do Lhoty 20 m od cesty.
    [(id, x, z, natoceni, polomer rovne plochy)]; predek stavby (+Z modelu) hledi k ceste."""
    out = []
    for id_, dist, off, r in (("stan_kupce", 200.0, 10.0 + 6.0, 7.5), ("hostinec", _arc_to(HLAVNI, CROSS) + 500.0, 20.0 + 8.0, 12.5)):
        x, z, dx, dz = _road_point(HLAVNI, dist)
        nx, nz = -dz, dx                       # vpravo pri chuzi od tvrze (+z) je -x
        if nx > 0:
            nx, nz = -nx, -nz
        cx, cz = x + nx * off, z + nz * off
        yaw = math.atan2(-nx, -nz)             # +Z modelu smerem k ceste
        out.append((id_, cx, cz, yaw, r))
    return out


STAVBY = _stavby()

# ruiny v lesich a na hrebeni (mista pro pribeh): (id, x, z, natoceni, polomer myti/srovnani)
RUINY = [("kostel", 220.0, 40.0, 0.6, 15.0), ("zanikla_ves", 300.0, 340.0, -0.3, 24.0), ("hradek", -190.0, 540.0, 1.2, 17.0)]
RUINY_NAZVY = {"kostel": "Zřícený kostel", "zanikla_ves": "Zaniklá ves", "hradek": "Zřícenina hrádku"}

# stred pudorysu modelu (souradnice Blenderu po importu glTF, z nahoru); ve hre je model na stredu, zem v z = 0
STRED = {"hostinec": (1.319, 4.649), "stan_kupce": (-1.275, 0.93)}


def stavba_bod(id_, bx, by):
    """Bod modelu stavby (Blender x, y) -> svet (x, z). Model: lokalne x = bx - sx, z = -(by - sy), otoceny o yaw."""
    for i, cx, cz, yaw, r in STAVBY:
        if i == id_:
            sx, sy = STRED[id_]
            lx, lz = bx - sx, -(by - sy)
            return (cx + lx * math.cos(yaw) + lz * math.sin(yaw), cz - lx * math.sin(yaw) + lz * math.cos(yaw))
    raise KeyError(id_)


def stavba_yaw(id_):
    return [s[3] for s in STAVBY if s[0] == id_][0]


def _stavby_cesty():
    """Hlinene odbocky z hlavni cesty k predku staveb (mirne zahnute); u hostince ke dverim pod pavlaci a pred nim placek
    se stoly a lavicemi (tri stoly podel prucelí, lavice tesne u desky)."""
    out, placky, stoly = [], [], []
    for id_, cx, cz, yaw, r in STAVBY:
        _, rx, rz = seg_info(cx, cz, HLAVNI)
        if id_ == "hostinec":
            front = stavba_bod(id_, 2.7, -2.4)          # pred dvermi pod pavlaci
        else:
            k = r / math.hypot(rx - cx, rz - cz)
            front = (cx + (rx - cx) * k, cz + (rz - cz) * k)
        # z cesty sikmo (ve smeru od tvrze), zahnuta ke vchodu
        sx, sz = rx - 0.0, rz - 6.0
        mx, mz = (sx + front[0]) / 2 + 2.5, (sz + front[1]) / 2 - 2.0
        pts = []
        for k in range(9):
            t = k / 8
            pts.append(((1 - t) ** 2 * sx + 2 * t * (1 - t) * mx + t * t * front[0], (1 - t) ** 2 * sz + 2 * t * (1 - t) * mz + t * t * front[1]))
        out.append((pts, 2.2 if id_ == "hostinec" else 1.7))
        if id_ == "hostinec":
            pc = stavba_bod(id_, 1.5, -5.2)
            placky.append((pc[0], pc[1], 8.5))
            # stul 1.14 x 2.64 m (delka podel prucelí), lavice 0.36 m siroka: stred lavice 0.6 m od stredu stolu (pod hranou desky)
            for bx in (-3.9, -0.7, 7.4):
                px, pz = stavba_bod(id_, bx, -4.4)
                stoly.append(("stul_hospoda", px, pz, yaw + math.pi / 2))
                for sg in (-1, 1):
                    qx, qz = stavba_bod(id_, bx, -4.4 + sg * 0.6)
                    stoly.append(("lavice_selska", qx, qz, yaw + (0.0 if sg > 0 else math.pi)))
    return out, placky, stoly


CESTY_STAVBY, PLACKY, STOLY_VENKU = _stavby_cesty()
CESTY = CESTY + CESTY_STAVBY


def placek(x, z):
    """Mira hliny na placku pred hostincem 0..1 (nepravidelny okraj)."""
    m = 0.0
    for px, pz, r in PLACKY:
        d = math.hypot(x - px, z - pz) + 2.0 * perlin(x / 4.0, z / 4.0)
        m = max(m, 1.0 - smooth(r - 2.0, r + 1.0, d))
    return m


def stavba_near(x, z, extra=0.0):
    for id_, cx, cz, yaw, r in STAVBY:
        if math.hypot(x - cx, z - cz) < r + extra:
            return True
    return ruina_near(x, z, min(extra, 2.0))


def ruina_near(x, z, extra=0.0):
    """Jadro ruiny (zdi a pruchody) - les a nalet roste az k nemu, okraj ruiny je zarostly."""
    for id_, cx, cz, yaw, r in RUINY:
        if math.hypot(x - cx, z - cz) < r * 0.75 + extra:
            return True
    return False


_PADY = {}


def stavba_pad(x, z, y, land_raw):
    """Teren pod stavbou (i ruinou) srovnany na prumer puvodni vysky, plynuly prechod 9 m."""
    for id_, cx, cz, yaw, r in STAVBY + RUINY:
        d = math.hypot(x - cx, z - cz)
        if d > r + 9.0:
            continue
        if id_ not in _PADY:
            ys = [land_raw(cx + math.cos(a) * r * 0.8, cz + math.sin(a) * r * 0.8) for a in [k * 0.785 for k in range(8)]] + [land_raw(cx, cz)]
            _PADY[id_] = sum(ys) / len(ys)
        k = 1.0 - smooth(r, r + 9.0, d)
        y = y + (_PADY[id_] - y) * k
    return y


class _Line:
    """Lomena cara s mrizkou useku (rychle hledani nejblizsiho bodu do vzdalenosti reach)."""

    def __init__(self, pts, reach, cell=40.0):
        self.pts = pts
        self.cell = cell
        self.b = {}
        for i, ((ax, az), (bx, bz)) in enumerate(zip(pts[:-1], pts[1:])):
            for ci in range(int(math.floor((min(ax, bx) - reach) / cell)), int(math.floor((max(ax, bx) + reach) / cell)) + 1):
                for cj in range(int(math.floor((min(az, bz) - reach) / cell)), int(math.floor((max(az, bz) + reach) / cell)) + 1):
                    self.b.setdefault((ci, cj), []).append(i)

    def near(self, x, z):
        """(vzdalenost, bod x, bod z, index useku + t) nebo None mimo dosah."""
        segs = self.b.get((int(math.floor(x / self.cell)), int(math.floor(z / self.cell))))
        if not segs:
            return None
        best = None
        for i in segs:
            (ax, az), (bx, bz) = self.pts[i], self.pts[i + 1]
            dx, dz = bx - ax, bz - az
            t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
            px, pz = ax + dx * t, az + dz * t
            d = math.hypot(x - px, z - pz)
            if best is None or d < best[0]:
                best = (d, px, pz, i + t)
        return best


_ROAD_LINES = [(_Line(path, 70.0), w) for path, w in CESTY]
_REKA_LINE = _Line(REKA, 90.0)
_BED = None
_NO_RIVER = False


def _river_bed():
    """Vyska dna potoka podel toku (v prostoru hills()): nikdy nestoupa po proudu, nejvys 11 m pod terenem."""
    global _BED, _NO_RIVER
    if _BED is None:
        _NO_RIVER = True
        bed = []
        cur = 1e9
        for i, (x, z) in enumerate(REKA):
            a_, b_ = REKA[max(0, i - 1)], REKA[min(len(REKA) - 1, i + 1)]
            L = math.hypot(b_[0] - a_[0], b_[1] - a_[1]) or 1.0
            nx, nz = -(b_[1] - a_[1]) / L, (b_[0] - a_[0]) / L
            # dno pod nejnizsim mistem napric (potok nikdy nebezi po hrbetu)
            base = min(hills(x + nx * o, z + nz * o) for o in (-12.0, -6.0, 0.0, 6.0, 12.0)) - 2.4
            cur = min(cur - 0.01, base)
            cur = max(cur, base - 12.0)
            bed.append(cur)
        _NO_RIVER = False
        _BED = bed
    return _BED


def river(x, z):
    """(vzdalenost od osy potoka, vyska dna v prostoru hills) nebo None daleko."""
    r = _REKA_LINE.near(x, z)
    if r is None:
        return None
    bed = _river_bed()
    i = int(r[3])
    t = r[3] - i
    b = bed[i] * (1 - t) + bed[min(i + 1, len(bed) - 1)] * t
    return r[0], b


def river_bank(d):
    """Povolena vyska terenu nad dnem ve vzdalenosti d od osy: koryto, brehy, mirne svahy udoli."""
    # koryto: dno ~4 m siroke, strme brehy ~2.4 m vysoke, nahore mirny svah udoli
    return 2.4 * smooth(2.6, 7.5, d) + 0.25 * smooth(4.0, 5.0, d) + max(0.0, d - 7.5) * 0.2


_BR = []


def bridge():
    """Misto mostu (kde odbocka prechazi potok): (x, z, smer cesty dx, dz) nebo None."""
    if _BR:
        return _BR[0]
    _BR.append(_bridge())
    return _BR[0]


def _bridge():
    best = None
    for i, (x, z) in enumerate(ODBOCKA):
        r = _REKA_LINE.near(x, z)
        if r and (best is None or r[0] < best[0]):
            best = (r[0], i)
    if best is None or best[0] > 6.0:
        return None
    i = best[1]
    a, b = ODBOCKA[max(0, i - 2)], ODBOCKA[min(len(ODBOCKA) - 1, i + 2)]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    x, z = ODBOCKA[i]
    dx, dz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    # cesta krizi potok sikmo: most siaha od brehu ke brehu (kde je osa potoka dal nez 7.8 m)
    ends = []
    for sg in (-1, 1):
        t = 0.0
        while t < 40.0:
            r = _REKA_LINE.near(x + dx * sg * t, z + dz * sg * t)
            if r is None or r[0] > 7.8:
                break
            t += 0.5
        ends.append(sg * t)
    mid = (ends[0] + ends[1]) / 2
    return x + dx * mid, z + dz * mid, dx, dz, (ends[1] - ends[0]) / 2 + 1.5


def detail(x, z):
    """Nerovnosti krajiny: terenni vlny, hrbolky, mezicky a prohlubne (m)."""
    v = 11.0 * perlin(x / 150.0 + 3.1, z / 150.0 - 7.3)
    v += 5.0 * perlin(x / 65.0 - 1.7, z / 65.0 + 4.4)
    v += 1.5 * perlin(x / 26.0 + 9.2, z / 26.0 + 2.5)
    v += 0.55 * perlin(x / 11.0 - 5.0, z / 11.0 - 3.3)
    # ostre hrbety (ridged) tu a tam: kamenite vycnelky
    v += 1.6 * max(0.0, 0.55 - abs(perlin(x / 90.0 + 20.0, z / 90.0 - 11.0))) ** 2 * 4.0
    return v


def ves_hills(x, z):
    """Kopecky kolem vsi: zvlneny hreben 300-650 m od navsi, nejvyssi za vsi (na severovychod),
    smerem k tvrzi (odkud vede cesta) nizky, aby byl z vesnice videt hrad."""
    dx, dz = x - VES[0], z - VES[1]
    r = ves_r(x, z)
    if r < 200.0 or r > 900.0:
        return 0.0
    k = (dx * -0.49 + dz * -0.87) / r                    # 1 = smer k tvrzi
    side = 1.0 - 0.85 * smooth(0.3, 0.85, k)
    band = smooth(240.0, 380.0, r) * (1.0 - smooth(650.0, 880.0, r))
    a = math.atan2(dz, dx)
    crest = 0.65 + 0.35 * math.sin(a * 3.0 + 0.7) + 0.25 * perlin(a * 2.0 + 5.0, r / 120.0)
    knobs = 0.5 + 0.5 * perlin(x / 70.0 + 11.0, z / 70.0 - 4.0)
    return 58.0 * band * side * crest * (0.6 + 0.6 * knobs)


def _hills_raw(x, z):
    r = math.hypot(x, z)
    w = smooth(140.0, 330.0, r)
    if w <= 0.0:
        return 0.0
    big = 32.0 * smooth(350.0, 1600.0, r) * (0.55 + 0.45 * math.sin(x * 0.0042 + 1.3) * math.cos(z * 0.0035 + 0.4))
    mid = 8.0 * math.sin(x * 0.012 + z * 0.004) * math.cos(z * 0.010 - 1.0) + 3.5 * math.sin(x * 0.027 - 0.7) * math.sin(z * 0.023 + 2.1)
    micro = 0.32 * perlin(x / 7.3 + 1.3, z / 7.3 - 2.2) + 0.14 * perlin(x / 3.1 - 4.0, z / 3.1 + 1.0)
    return w * (big + mid + detail(x, z) + micro) + ridge(x, z) * (1.0 + 0.12 * perlin(x / 30.0, z / 30.0)) + ves_hills(x, z)


_HV = None


def hills(x, z):
    """Pridavek k vysce terenu daleko od tvrze: kopce, pod vesnici mirna rovina."""
    global _HV
    if _HV is None:
        _HV = _hills_raw(*VES)
    h = _hills_raw(x, z)
    dv = ves_r(x, z)
    dh = math.hypot(x - VES[0], z - VES[1])
    if dv < VES_R + 140.0 or dh < 140.0:
        # rovina pod vsi: nepravidelne ohranicena, samotna ves (do 90 m) je srovnana vzdy
        k = max(1.0 - smooth(VES_R, VES_R + 140.0, dv), 1.0 - smooth(90.0, 140.0, dh))
        # rovina s mirnym sklonem k potoku na vychode navsi
        flat = _HV - 0.6 * smooth(-40.0, 120.0, x - VES[0])
        h = h + (flat - h) * k * 0.6               # ves neni placka: kopecky zustanou
        import vesnice
        h -= vesnice.pond_depth(x, z)
    if not _NO_RIVER:
        rv = river(x, z)
        if rv is not None and rv[0] < 80.0:
            # brehy rozbite jako u prikopu: zatoky, vymoly, sesuvy, misty sirsi tune
            dn = rv[0] + 1.7 * perlin(x / 6.0 + 4.1, z / 6.0 - 2.3) + 0.7 * perlin(x / 2.3 - 8.0, z / 2.3 + 1.1)
            h = min(h, rv[1] + river_bank(max(0.0, dn)))
    return h


def road_near(x, z):
    """Nejblizsi cesta: (vzdalenost, bod x, bod z, polovicni sirka) nebo None (daleko)."""
    best = None
    for ln, w in _ROAD_LINES:
        r = ln.near(x, z)
        if r and (best is None or r[0] < best[0]):
            best = (r[0], r[1], r[2], w / 2.0)
    return best


def flatten(x, z, y, land_fn):
    """Srovnani terenu pod cestami (mimo tvrz): jadro 15 cm pod povrchem cesty, plynuly prechod do okoli."""
    if math.hypot(x, z) < 70.0:
        return y
    rn = road_near(x, z)
    if rn is None or rn[0] > 26.0:
        return y
    d, px, pz, hw = rn
    yr = land_fn(px, pz, False) - 0.15
    br = bridge()
    if br and math.hypot(px - br[0], pz - br[1]) < br[4] + 24.0:
        # najezd na most: nasyp pod cestou, jen ne v korytu potoka pod mostovkou
        rv = river(x, z)
        if rv is None or rv[0] > 6.9:
            yr2 = road_y(px, pz, land_fn) - 0.12
            if yr2 > y:
                # nasyp najezdu: koruna 7 m siroka (opery zasypane hlinou), svahy 1:2.5 do okoli,
                # u vody se nasyp zaobli do brehu
                core = 3.6 + 0.4 * perlin(x / 5.0, z / 5.0)
                slope = max(5.0, (yr2 - y) * 2.5)
                k2 = 1.0 - smooth(core, core + slope, d)
                if rv is not None:
                    k2 *= smooth(6.9, 8.4, rv[0])
                return y + (yr2 - y) * k2
    k = 1.0 - smooth(hw + 0.6, hw + 6.0, d)
    return y + (yr - y) * k


_DECK = None


def deck_y(land_fn):
    """Vyska mostovky (svet): nad brehem potoku v miste mostu."""
    global _DECK
    if _DECK is None:
        br = bridge()
        # mostovka kousek nad hranou brehu (mereno 9.5-11 m od osy po ceste na obe strany)
        sp = br[4] if br else 0.0
        _DECK = (max(land_fn(br[0] + br[2] * s_, br[1] + br[3] * s_, False) for s_ in (-sp - 1.5, -sp, sp, sp + 1.5)) + 0.3) if br else -1e9
    return _DECK


def road_y(px, pz, land_fn):
    """Vyska povrchu cesty (pas hliny lezi 12 cm nad srovnanym terenem); u mostu najede na mostovku."""
    y = land_fn(px, pz, False) - 0.03
    br = bridge()
    if br:
        dd = math.hypot(px - br[0], pz - br[1])
        if dd < br[4] + 30.0:
            y = max(y, deck_y(land_fn) - max(0.0, dd - br[4] - 0.6) * 0.22)
    return y


def reka(coll, land_fn):
    """Potok Bystrice: hladina v korytu (pas po proudu), dreveny most na odbocce do vsi."""
    from lib import M, Part
    from mathutils import Matrix, Vector
    # hladina jako u prikopu: mrizka 1.5 m, plocha jen tam, kde je teren pod hladinou (okraj sleduje breh)
    import lib
    import veg
    if "voda_prikop" not in lib.MAT:
        lib.MAT["voda_prikop"] = veg.mat_pond("voda_prikop")
    P = Part("Reka_voda")
    wl = [land_fn(x, z) + 0.75 for x, z in REKA]
    step = 1.5
    xs_ = [p[0] for p in REKA]
    zs_ = [p[1] for p in REKA]
    x0 = max(ACT[0] + 5, min(xs_) - 12)
    x1 = min(ACT[1] - 5, max(xs_) + 12)
    z0 = max(ACT[2] + 5, min(zs_) - 12)
    z1 = min(ACT[3] - 5, max(zs_) + 12)
    vid, verts, faces = {}, [], []
    lcache = {}

    def lev(i, k):
        key = (i, k)
        if key not in lcache:
            x, z = x0 + i * step, z0 + k * step
            r = _REKA_LINE.near(x, z)
            if r is None or r[0] > 11.0:
                lcache[key] = None
            else:
                j = int(r[3])
                t = r[3] - j
                lcache[key] = (wl[j] * (1 - t) + wl[min(j + 1, len(wl) - 1)] * t, land_fn(x, z))
        return lcache[key]

    def v(i, k, y):
        if (i, k) not in vid:
            vid[(i, k)] = len(verts)
            verts.append((x0 + i * step, y, z0 + k * step))
        return vid[(i, k)]
    ni, nk = int((x1 - x0) / step), int((z1 - z0) / step)
    for i in range(ni):
        for k in range(nk):
            r = _REKA_LINE.near(x0 + (i + 0.5) * step, z0 + (k + 0.5) * step)
            if r is None or r[0] > 9.5:
                continue
            cs = [lev(i, k), lev(i + 1, k), lev(i + 1, k + 1), lev(i, k + 1)]
            if any(c is None for c in cs) or min(c[1] for c in cs) > max(c[0] for c in cs) - 0.02:
                continue
            y = sum(c[0] for c in cs) / 4
            faces.append((v(i, k, cs[0][0]), v(i, k + 1, cs[3][0]), v(i + 1, k + 1, cs[2][0]), v(i + 1, k, cs[1][0])))
    P.mesh(verts, faces, "voda_prikop")
    P.commit(coll)
    br = bridge()
    if not br:
        return
    B = Part("Most_potok", bevel=0.01)
    R = random.Random(21)
    bx, bz, dx, dz, span = br
    yd = deck_y(land_fn)
    au = Vector((dx, 0.0, dz))
    av = Vector((-dz, 0.0, dx))
    bas = Matrix((au, Vector((0, 1, 0)), av)).transposed()
    c = Vector((bx, yd, bz))

    def q(u, y, v):
        return c + au * u + av * v + Vector((0, y, 0))
    rv = river(bx, bz)
    ybed = land_fn(bx, bz) - 0.2
    # kamenne opery na koncich, dva hlavni tramy, mostovka z kulatych fosen napric, piloty v korytu, zabradli
    # drevene opery: rada zatlucenych kulatin a za nimi vodorovne fosny drzi hlinu nasypu
    for su in (-1, 1):
        uo = su * (span - 1.0)
        ybot = land_fn(*(c + au * uo).xz) - yd - 0.8
        for k in range(12):
            sv = -2.3 + k * 4.6 / 11
            B.rod(q(uo, ybot, sv), q(uo + R.uniform(-0.03, 0.03), -0.32 + R.uniform(-0.05, 0.05), sv), 0.13 + R.uniform(-0.02, 0.02), 7, "kura")
        yy = ybot + 0.3
        while yy < -0.4:
            B.beam(q(uo - su * 0.2, yy, -2.5), q(uo - su * 0.2, yy, 2.5), 0.12, 0.24, "deska_stodola", j=0.8)
            yy += 0.25
        B.cols.append((M(q(uo - su * 0.1, (ybot - 0.3) / 2, 0.0), basis=bas), (0.4, -ybot, 4.8)))
    for sv in (-1.5, -0.5, 0.5, 1.5):
        B.beam(q(-span, -0.3, sv), q(span, -0.3, sv), 0.28, 0.32, "dub_ven", j=0.8)
    u = -span + 0.1
    while u < span:
        wpl = R.uniform(0.2, 0.3)
        B.box(M(q(u + wpl / 2, -0.03 + R.uniform(-0.01, 0.01), R.uniform(-0.05, 0.05)), basis=bas), (wpl - 0.015, 0.09, 4.0 + R.uniform(-0.1, 0.1)),
              "drevo_plot", rnd=R.random())
        u += wpl
    npil = max(2, int(span / 3.5))
    for pu in [(-span + 1.0) + (2 * span - 2.0) * (k_ + 1) / (npil + 1) for k_ in range(npil)]:
        for sv in (-1.6, 1.6):
            B.rod(q(pu, land_fn(*q(pu, 0.0, sv).xz) - yd - 0.6, sv), q(pu, -0.45, sv), 0.17, 8, "kura")
        B.beam(q(pu, -0.55, -1.9), q(pu, -0.55, 1.9), 0.25, 0.25, "dub_ven", j=0.6)
        B.beam(q(pu, land_fn(*q(pu, 0.0, -1.6).xz) - yd + 0.4, -1.6), q(pu, -0.7, 1.6), 0.12, 0.12, "dub_ven", j=0.5)
    for sv in (-2.05, 2.05):
        nst = int(2 * span / 1.9) + 1
        for k in range(nst):
            pu = -span + 0.5 + k * (2 * span - 1.0) / (nst - 1)
            B.beam(q(pu, -0.1, sv), q(pu, 1.05, sv), 0.13, 0.13, "dub_ven", j=0.8)
        B.rod(q(-span + 0.4, 1.0, sv), q(span - 0.4, 1.0, sv), 0.07, 7, "kura")
        B.rod(q(-span + 0.4, 0.55, sv), q(span - 0.4, 0.55, sv), 0.05, 6, "kura")
        B.cols.append((M(q(0.0, 0.6, sv), basis=bas), (2 * span - 0.8, 1.2, 0.15)))
    B.cols.append((M(q(0.0, -0.2, 0.0), basis=bas), (2 * span, 0.3, 4.0)))
    B.commit(coll)
    print("potok: %d ploch, most v (%.0f, %.0f) mostovka %.2f" % (len(faces), bx, bz, yd))


# ------------------------------------------------------------------ pouziti zeme (barva terenu)

def _forest_raw(x, z):
    v = (math.sin(x * 0.0061 + 0.7) * math.cos(z * 0.0049 - 1.1) + 0.55 * math.sin(x * 0.0157 + z * 0.0113 + 2.0)
         + 0.3 * math.sin(x * 0.041 - z * 0.033))
    return v


def field_strip(x, z, mez=True):
    """Pole kolem vsi v honech: kazdy hon (nepravidelny blok) ma lany jinym smerem a jinak siroke, mezi hony
    travnate meze s kerim, nektere hony jsou louka nebo pastvina (uhor). Vnejsi hranice nepravidelna.
    Vraci (cislo lanu, plodina 0..3) nebo None. Vzor lanu kresli shaders/zem.gdshader stejnou nahodou."""
    r = ves_r(x, z)
    wob = 22.0 * perlin(x / 90.0 + 5.0, z / 90.0 - 3.0)
    if r < 60.0 + 0.5 * wob or r > VES_R + 270.0 + 2.0 * wob:
        return None
    if math.hypot(x - VES[0], z - VES[1]) < 110.0:
        # zahumenky: pole zacinaji hned za humny, ale ne na navsi, ve dvorech, zahradach a u rybnika
        import vesnice
        if vesnice.in_homestead(x, z, 5.0) or vesnice.pond_depth(x, z) > 0.0:
            return None
        nu, nv = vesnice.naves_uv(x, z)
        if abs(nv) < vesnice.NAVES[1] + 30.0 and -100.0 < nu < 90.0:
            return None
    # na vychode luka u potoka a les (hranice sektoru zvlnena)
    a = math.atan2(z - VES[1], x - VES[0]) + 0.35 * perlin(r / 90.0, 1.0)
    if -0.9 < a < 0.55:
        return None
    rv = river(x, z)
    if rv is not None and rv[0] < 22.0 + 6.0 * perlin(x / 40.0, z / 40.0):
        return None                                   # luh u potoka (zaplavova louka)
    h, edge, t, w = hon(x, z)
    if (h >> 8) % 5 == 0:
        return None                                   # hon ladem: louka / pastvina
    if mez and edge < 3.0:
        return None                                   # mez mezi hony
    n = math.floor(t / w)
    f = t / w - n
    if mez and f < 0.09:
        return None
    crop = _hash(h ^ ((n * 2654435761) & 0xFFFFFFFF)) % 4
    return n, crop


def a_seed(dx, dz):
    return 3.7 + 0.0 * dx


def forest(x, z):
    """Mira lesa 0..1 (tmava lesni puda; v pasmu 5 m tam stoji stromy)."""
    r = math.hypot(x, z)
    if r < 170.0:
        return 0.0
    rn = road_near(x, z)
    if rn and rn[0] < rn[3] + 9.0:
        return 0.0
    rp = river(x, z)
    if rp is not None and rp[0] < 9.0:
        return 0.0
    if any(math.hypot(x - cx, z - cz) < r + 14.0 for _, cx, cz, _, r in STAVBY):
        return 0.0                                        # u staveb mytina; ruiny stoji v lese (lesni puda i uvnitr)
    rv = ves_r(x, z)
    if rv < VES_R + 300.0 and field_strip(x, z) is not None:
        return 0.0
    if rv < VES_R + 25.0 or math.hypot(x - VES[0], z - VES[1]) < 95.0:
        return 0.0
    v = _forest_raw(x, z) + 0.6 * smooth(500.0, 1600.0, r) + 0.22 * perlin(x / 28.0 + 7.0, z / 28.0 - 1.0)
    # kopecky za vsi jsou zalesnene (husty smrkovy les s brizami po okraji)
    v += 1.1 * min(1.0, ves_hills(x, z) / 12.0)
    return smooth(0.38, 0.62, v)


def ground_attrs(x, z):
    """(trava 0..1, les 0..1, pole 0..1 kod plodiny) pro barvu terenu."""
    les = forest(x, z)
    fs = field_strip(x, z, mez=False)
    pole = 0.0
    g = 0.85
    if fs is not None:
        pole = 1.0                     # plodiny a meze pocita shader
        g = 0.6
    dv = math.hypot(x - VES[0], z - VES[1])
    if dv < 90.0:
        # naves travnata, udusana hlina jen ve dvorech u chalup a v pruhu cesty pres naves
        import vesnice
        g = 0.75
        g = min(g, 0.75 - 0.55 * vesnice.yard_dirt(x, z))
        # cesty ve vsi: hlavni stredem navsi a odbocky k vratum; mimo ne trava (krovi a trsy jsou 3D)
        pd = vesnice.path_dist(x, z) + 0.6 * perlin(x / 3.0, z / 3.0)
        if pd < 2.5:
            g = min(g, 0.08 + 0.7 * smooth(-0.3, 2.2, pd))
    pl = placek(x, z)
    if pl > 0.0:
        g = min(g, 0.75 - 0.62 * pl)
    rn = road_near(x, z)
    if rn and rn[0] < rn[3] + 3.0 and math.hypot(x, z) > 60:
        # vyslapana hlina kolem cesty s nepravidelnym okrajem
        ed = rn[0] - rn[3] + 1.1 * perlin(x / 3.5, z / 3.5) + 0.6 * perlin(x / 1.4 + 7.0, z / 1.4)
        g = min(g, 0.15 + 0.5 * smooth(-0.4, 1.6, ed))
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
    skips = skip if isinstance(skip, list) else [skip]
    for i in range(len(xs) - 1):
        for k in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[k] + zs[k + 1]) / 2
            if any(x0 < cx < x1 and z0 < cz < z1 for x0, x1, z0, z1 in skips):
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
    br = bridge()
    bx5, bz5 = round(br[0] / 5.0) * 5.0, round(br[1] / 5.0) * 5.0
    BRECT = (bx5 - 40.0, bx5 + 40.0, bz5 - 40.0, bz5 + 40.0)          # jemny teren u mostu (nasep, brehy)
    for name, rect, inner, step in (("Teren_ves", VRECT, [], 2.0), ("Teren_most", BRECT, [], 1.0),
                                    ("Teren_okoli", ACT, [NEAR, VRECT, BRECT], 5.0), ("Teren_obzor", FAR, ACT, 25.0)):
        xs = [rect[0] + step * i for i in range(int(round((rect[1] - rect[0]) / step)) + 1)]
        zs = [rect[2] + step * k for k in range(int(round((rect[3] - rect[2]) / step)) + 1)]
        verts, faces, attrs = _grid(xs, zs, inner, land_fn, name, None, coll)
        # obzor: lesy jako tmava vyvysena koruna (z dalky vypada jako les, stromy by stály moc)
        if name == "Teren_obzor":
            verts = [(x, y + 11.0 * a[1] * smooth(0.0, 1.0, a[1]), z) for (x, y, z), a in zip(verts, attrs)]
        # jemnejsi pasma: lem dolu po obvodu (zakryje skulinky na styku s hrubsim pasmem)
        if name in ("Teren_most", "Teren_okoli"):
            _skirt(verts, faces, attrs, rect, step, land_fn, depth=5.0 if name == "Teren_most" else 8.0)
        # hladke stinovani (ne ploskove trojuhelniky se zlomy)
        P = Part(name, smooth=True)
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
    """Pasek pod okrajem pasma 1 m a pasma vesnice (2 m)."""
    from lib import Part
    verts, faces, attrs = [], [], []
    _skirt(verts, faces, attrs, NEAR, 1.0, land_fn, depth=3.0)
    _skirt(verts, faces, attrs, VRECT, 2.0, land_fn, depth=3.0)
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
        prof = [(-0.75, -0.32, 0.8), (-0.45, -0.02, 0.3), (-0.22, -0.035, 0.0), (-0.12, 0.0, 0.08), (0.12, 0.0, 0.08),
                (0.22, -0.035, 0.0), (0.45, -0.02, 0.3), (0.75, -0.32, 0.8)]
        rowlen = len(prof)
        base = len(verts)
        for i, (x, z) in enumerate(sm):
            a = sm[max(0, i - 1)]
            b = sm[min(len(sm) - 1, i + 1)]
            dx, dz = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dz) or 1.0
            nx, nz = -dz / L, dx / L
            yc = road_y(x, z, land_fn)
            wv = w * (1.0 + 0.22 * perlin(x / 25.0 + 3.0, z / 25.0))
            for s, dy, g in prof:
                # kraje cesty rozbite: kazda strana jinak, vyjezdene vymoly, zarostle useky (jako brehy prikopu)
                sd = 1.0 if s > 0 else -1.0
                e = 0.0
                if abs(s) > 0.3:
                    e = 0.28 * perlin(x / 7.0 + sd * 13.0, z / 7.0) + 0.14 * perlin(x / 2.6 - sd * 5.0, z / 2.6 + 3.0)
                    e *= 1.0 if abs(s) > 0.6 else 0.55
                ww = wv * (1.0 + e)
                px, pz = x + nx * s * ww, z + nz * s * ww
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
    P = Part("Teren_cesta", smooth=True)
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

def tree_spots(R, n=7000):
    """Mista pro stromy v pasmu 5 m: husty les tam, kde forest() > 0.5, rozptylene stromy a meze v polich."""
    out = []
    tries = 0
    taken = {}

    def free(x, z, r2):
        if stavba_near(x, z, 6.0):
            return False
        cx, cz = int(x // 6), int(z // 6)
        for i in (-1, 0, 1):
            for k in (-1, 0, 1):
                for (a, b) in taken.get((cx + i, cz + k), []):
                    if (x - a) ** 2 + (z - b) ** 2 < r2:
                        return False
        return True

    while len(out) < n and tries < n * 40:
        tries += 1
        x = R.uniform(ACT[0] + 5, ACT[1] - 5)
        z = R.uniform(ACT[2] + 5, ACT[3] - 5)
        if math.hypot(x + 4, z) < 160:
            continue
        f = forest(x, z)
        if f < 0.5:
            # osamele stromy a hloucky na mezich, pastvinach a u cest (lipy, duby, brizy)
            if R.random() > 0.05:
                continue
            rn = road_near(x, z)
            if rn and rn[0] < rn[3] + 3.0:
                continue
            if math.hypot(x - VES[0], z - VES[1]) < VES_R:
                continue
            kind = "solo"
        else:
            kind = "les"
        if not free(x, z, 18.0 if kind == "les" else 30.0):
            continue
        taken.setdefault((int(x // 6), int(z // 6)), []).append((x, z))
        out.append((x, z, kind, f))
    return out


# ------------------------------------------------------------------ piskovcove skalni mesto na hrebeni

ROCK_PLANTS = []          # (model, x, z, vyska, y nebo None) - rostliny na skalach a u jejich paty, pro veg


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
    # na vrsku stromek nebo trs, u paty kapradi, trava a kere (vlhko ve stinu skal)
    top = m @ Vector((lean * height, height - 0.15, 0.0))
    if R.random() < 0.45:
        k = R.random()
        ROCK_PLANTS.append(("smrk" if k < 0.6 else ("briza" if k < 0.8 else "shrub_02"), top.x, top.z, R.uniform(1.5, 5.0), top.y))
    for _ in range(R.randint(5, 10)):
        a = R.uniform(0, 2 * math.pi)
        d = rad * R.uniform(1.0, 1.6)
        bx, bz = c[0] + math.cos(a) * d, c[2] + math.sin(a) * d
        ROCK_PLANTS.append((R.choice(["fern_02", "fern_02", "divoka_trava", "shrub_02", "grass_medium_02", "sipek"]), bx, bz,
                            R.uniform(0.5, 1.6), None))
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
            if stavba_near(xx, zz, 14.0):
                continue                                  # misto zriceniny hradku nechat volne
            y = land_fn(xx, zz)
            mid = 1.0 - abs(o) / (cnt * 4.0)
            h = R.uniform(6.0, 13.0) + 14.0 * mid * R.random()
            rad = R.uniform(4.0, 7.5)
            _tower(P, (xx, y, zz), h, rad, R, lean=R.uniform(-0.04, 0.04))
            towers += 1
        if R.random() < 0.35 and not stavba_near(gx, gz, 45.0):
            xx, zz = gx + R.uniform(-30, 30), gz + R.uniform(-30, 30)
            _tower(P, (xx, land_fn(xx, zz), zz), R.uniform(16.0, 30.0), R.uniform(1.8, 3.0), R, lean=R.uniform(-0.05, 0.05))
            towers += 1
        import nove
        # balvany a kameny z pisku u paty skal (modely z druheho chatu), sem tam spadly velky blok
        for _ in range(R.randint(5, 11)):
            xx, zz = gx + R.gauss(0.0, 12.0), gz + R.gauss(0.0, 12.0)
            sz = R.uniform(0.8, 3.5)
            pid = R.choice(nove.KAMENY_PISKOVEC) if sz < 1.4 else R.choice(nove.BALVANY_PISKOVEC)
            if stavba_near(xx, zz, 3.0):
                continue
            nove.misto(pid, xx, land_fn(xx, zz), zz, sz / nove.DIM[pid][0], R.uniform(0, 2 * math.pi), P, sink=0.2)
        for _ in range(R.randint(1, 3)):
            xx, zz = gx + R.gauss(0.0, 9.0), gz + R.gauss(0.0, 9.0)
            if stavba_near(xx, zz, 3.0):
                continue
            nove.misto("balvan_piskovec_3", xx, land_fn(xx, zz), zz, R.uniform(1.8, 3.2), R.uniform(0, 2 * math.pi), P, sink=0.25)
        for _ in range(R.randint(6, 14)):
            xx, zz = gx + R.gauss(0.0, 10.0), gz + R.gauss(0.0, 10.0)
            pid = R.choice(nove.KAMINKY)
            if stavba_near(xx, zz, 3.0):
                continue
            nove.misto(pid, xx, land_fn(xx, zz), zz, R.uniform(1.0, 2.5), R.uniform(0, 2 * math.pi), None, sink=0.3)
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
                import nove
                pid = R.choice(nove.KAMINKY) if s < 0.5 else R.choice(nove.KAMENY_POLE)
                nove.misto(pid, px, land_fn(px, pz), pz, s / nove.DIM[pid][0], R.uniform(0, 2 * math.pi), Rk, sink=0.25)
    Rk.commit(coll)
    P.commit(coll)
    print("skalni mesto: %d vezi" % towers)
    return P


# ------------------------------------------------------------------ drobnosti v krajine: skalky, kameny, trsy, kere

def _wild(x, z):
    """Misto v divocine (ne na ceste, poli, navsi ani u tvrze)."""
    if not (ACT[0] + 4 < x < ACT[1] - 4 and ACT[2] + 4 < z < ACT[3] - 4):
        return False
    if stavba_near(x, z, 6.0) or placek(x, z) > 0.0:
        return False
    if math.hypot(x + 4, z) < 75:
        return False
    rn = road_near(x, z)
    if rn and rn[0] < rn[3] + 1.2:
        return False
    rp = river(x, z)
    if rp is not None and rp[0] < 6.0:
        return False                                      # v korytu potoka
    if math.hypot(x - VES[0], z - VES[1]) < VES_R + 20:
        # ve vsi ano, jen ne ve dvorech, na zahradach a v rybnicku
        import vesnice
        if vesnice.yard_dist(x, z) < 15.0 or vesnice.pond_depth(x, z) > 0.0:
            return False
        if vesnice.path_dist(x, z) < 0.8:
            return False                                  # na ceste nic neroste
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
        # skalka: polni balvany a kameny (zula, droba), u skalniho hrebene piskovec
        import nove
        pis = ridge(x, z) > 2.0
        for _ in range(R.randint(2, 7)):
            xx, zz = x + R.gauss(0, 2.5), z + R.gauss(0, 2.5)
            s = R.uniform(0.5, 2.6) if R.random() < 0.7 else R.uniform(2.5, 4.5)
            if s < 1.4:
                pid = R.choice(nove.KAMENY_PISKOVEC if pis else nove.KAMENY_POLE)
            else:
                pid = R.choice(nove.BALVANY_PISKOVEC if pis else nove.BALVANY_POLE)
            nove.misto(pid, xx, land_fn(xx, zz), zz, s / nove.DIM[pid][0], R.uniform(0, 2 * math.pi), P, sink=R.uniform(0.15, 0.35))
        for _ in range(R.randint(3, 8)):
            xx, zz = x + R.gauss(0, 3.5), z + R.gauss(0, 3.5)
            pid = R.choice(nove.KAMINKY)
            nove.misto(pid, xx, land_fn(xx, zz), zz, R.uniform(0.8, 2.0), R.uniform(0, 2 * math.pi), None, sink=0.3)
        n += 1
    import nove
    for _ in range(700):
        x, z = R.uniform(ACT[0], ACT[1]), R.uniform(ACT[2], ACT[3])
        if not _wild(x, z):
            continue
        s = R.uniform(0.12, 0.5)
        pid = R.choice(nove.KAMINKY)
        nove.misto(pid, x, land_fn(x, z), z, s / nove.DIM[pid][0], R.uniform(0, 2 * math.pi), None, sink=0.3)
    P.commit(coll)
    print("skalky:", n)


def plant_spots(R):
    """Trsy travy, kvetiny, kere a naletove stromky v divocine: [(model, x, z, vyska, naklon)]."""
    out = []
    # kere a nalet: na okrajich lesa, na mezich, kolem skalek, v dolinkach
    k = 0
    while k < 2600:
        x, z = R.uniform(ACT[0], ACT[1]), R.uniform(ACT[2], ACT[3])
        if not _wild(x, z):
            continue
        f = forest(x, z)
        edge = 1.0 - abs(f - 0.35) * 2.5
        if R.random() > 0.25 + max(0.0, edge) * 0.75:
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
    # kraje cest: trsy travy, kopřivy, sem tam ker (zadny rakos)
    for path, w in CESTY:
        acc = 0.0
        for (ax, az), (bx, bz) in zip(path[:-1], path[1:]):
            L = math.hypot(bx - ax, bz - az)
            if L < 1e-6:
                continue
            nx, nz = -(bz - az) / L, (bx - ax) / L
            t = 0.0
            while t < L:
                x, z = ax + (bx - ax) * t / L, az + (bz - az) * t / L
                t += R.uniform(1.0, 2.2)
                if not (ACT[0] + 5 < x < ACT[1] - 5 and ACT[2] + 5 < z < ACT[3] - 5) or math.hypot(x, z) < 60:
                    continue
                for sd in (-1, 1):
                    o = sd * (w / 2 + R.uniform(0.7, 3.2))
                    xx, zz = x + nx * o, z + nz * o
                    if stavba_near(xx, zz, 2.0) or placek(xx, zz) > 0.0:
                        continue
                    c = R.random()
                    if c < 0.04:
                        out.append((R.choice(["shrub_02", "sipek"]), xx, zz, R.uniform(0.9, 2.0), 0.0))
                    elif c < 0.55:
                        out.append(("divoka_trava", xx, zz, R.uniform(0.4, 0.9), 0.12))
                    elif c < 0.75:
                        out.append(("grass_medium_02", xx, zz, R.uniform(0.3, 0.55), 0.0))
                    elif c < 0.85:
                        out.append(("nettle_plant", xx, zz, R.uniform(0.3, 0.55), 0.0))
                    elif c < 0.92:
                        out.append(("dandelion_01", xx, zz, R.uniform(0.2, 0.35), 0.0))
    # brehy potoka: vrby, kere, kopřivy a vysoka trava; u vody hustsi
    for i, (x, z) in enumerate(REKA):
        if not (ACT[0] + 5 < x < ACT[1] - 5 and ACT[2] + 5 < z < ACT[3] - 5) or i % 2:
            continue
        a, b = REKA[max(0, i - 1)], REKA[min(len(REKA) - 1, i + 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        nx, nz = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        br = bridge()
        if br and math.hypot(x - br[0], z - br[1]) < 14.0:
            continue
        for side in (-1, 1):
            o = side * R.uniform(5.8, 9.0)
            xx, zz = x + nx * o, z + nz * o
            rn = road_near(xx, zz)
            if rn and rn[0] < rn[3] + 1.5:
                continue
            c = R.random()
            if c < 0.1:
                out.append(("vrba", xx, zz, R.uniform(6.0, 10.0), 0.0))
            elif c < 0.32:
                out.append((R.choice(["shrub_02", "sipek"]), xx, zz, R.uniform(1.0, 2.6), 0.0))
            elif c < 0.55:
                out.append(("nettle_plant", xx, zz, R.uniform(0.4, 0.75), 0.0))
            else:
                out.append(("divoka_trava", xx, zz, R.uniform(0.6, 1.2), 0.12))
    return out
