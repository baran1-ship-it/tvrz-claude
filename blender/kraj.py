"""Sirsi krajina kolem tvrze: kopce az k obzoru, hlavni cesta od brany, krizovatka s bozimi muky
a odbocka vlevo (na +x) do vesnice asi kilometr od tvrze. Lesy na kopcich, pole v lanech kolem vesnice.

Teren je ve trech pasmech: u tvrze po 1 m (fort.terrain), okoli po 5 m, obzor po 25 m.
Vysky vsude pocita fort.land (sem jen pridava kopce, rovinu vesnice a srovnani pod cestami)."""
import json
import math
import os
import random

# jediny zdroj (radce 27. 10. 10:45 krok A): lokace, cesty a voda z pravidla/svet/*.json - ctou je Blender i Godot
_SVET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pravidla", "svet")


def _svet(nm):
    with open(os.path.join(_SVET, nm), encoding="utf-8") as f:
        return json.load(f)


_CESTY_J = _svet("cesty.json")
_VODA_J = _svet("voda.json")
_LOKACE_J = _svet("lokace.json")

# souradnice hry: x vpravo pri pohledu od tvrze k jihu, z od brany ven (+z), y nahoru
VES = tuple(_LOKACE_J["ves"]["stred_stare_navsi"])      # stred (stare) navsi
VES_R = float(_LOKACE_J["ves"]["rovina_r_m"])          # polomer roviny vesnice
_VOZ = {c["id"]: c for c in _CESTY_J["vozove"]}
CROSS = tuple(_CESTY_J["krizovatka_hlavni_odbocka"])  # krizovatka hlavni cesty a odbocky do vesnice
HLAVNI = [tuple(p) for p in _VOZ["hlavni"]["osa"]]
ODBOCKA = [tuple(p) for p in _VOZ["odbocka_ves"]["osa"]]
CESTY = [(HLAVNI, _VOZ["hlavni"]["blender_sirka_m"]), (ODBOCKA, _VOZ["odbocka_ves"]["blender_sirka_m"])]

_GEN_J = _svet("generovani.json")
_PLOCHY_J = _svet("plochy.json")
NEAR = tuple(_GEN_J["blender_pasmo_tvrz_1m"])      # pasmo 1 m (fort.terrain)
ACT = tuple(_GEN_J["blender_pasmo_okoli_5m"])      # pasmo 5 m
VRECT = tuple(_GEN_J["blender_pasmo_ves_2m"])      # pasmo 2 m ve vesnici (drobne nerovnosti, krtince)
FAR = tuple(_GEN_J["blender_pasmo_obzor_25m"])     # pasmo 25 m (obzor)


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
HREBEN = [tuple(p) for p in _LOKACE_J["skalni_hreben_osa"]]


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

def _setup_paths():
    # osy cest a potoka po klikateni (_meander) jsou ulozene v pravidla/svet (krok A) - tady se uz nepocitaji
    global REKA
    REKA = [tuple(p) for p in _VODA_J["potok"]["osa"]]


REKA = []
_setup_paths()


STAVBY = [(e["id"], e["stred"][0], e["stred"][1], e["natoceni"], e["rovina_r_m"]) for e in _LOKACE_J["stavby"]]

# ruiny v lesich a na hrebeni (mista pro pribeh): (id, x, z, natoceni, polomer myti/srovnani)
RUINY = [(e["id"], e["stred"][0], e["stred"][1], e["natoceni"], e["myti_r_m"]) for e in _LOKACE_J["ruiny"]]
RUINY_ROVINA = [(e["id"], e["stred"][0], e["stred"][1], e["natoceni"], e["rovina_r_m"]) for e in _LOKACE_J["ruiny"]]
RUINY_NAZVY = {e["id"]: e["nazev"] for e in _LOKACE_J["ruiny"]}   # podle pribehu

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


def stavba_lokal(id_, x, z):
    """Opak stavba_bod: svet (x, z) -> bod modelu stavby (Blender x, y)."""
    for i, cx, cz, yaw, r in STAVBY:
        if i == id_:
            sx, sy = STRED[id_]
            dx, dz = x - cx, z - cz
            lx = dx * math.cos(yaw) - dz * math.sin(yaw)
            lz = dx * math.sin(yaw) + dz * math.cos(yaw)
            return lx + sx, sy - lz
    raise KeyError(id_)


## pudorys staveb v souradnicich modelu (bez travy uvnitr): x0, x1, y0, y1
PUDORYS = {"hostinec": (-6.9, 9.6, -2.3, 12.2), "stan_kupce": (-4.5, 4.5, -3.5, 4.5)}


def v_pudorysu(x, z, okraj=0.3):
    for id_, (x0, x1, y0, y1) in PUDORYS.items():
        bx, by = stavba_lokal(id_, x, z)
        if x0 - okraj <= bx <= x1 + okraj and y0 - okraj <= by <= y1 + okraj:
            return True
    return False


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
            sv = next(s_ for s_ in _LOKACE_J["stavby"] if s_["id"] == id_)["stoly_venku"]
            for bx in sv["bx"]:
                px, pz = stavba_bod(id_, bx, sv["by"])
                stoly.append(("stul_hospoda", px, pz, yaw + math.pi / 2))
                for sg in (-1, 1):
                    qx, qz = stavba_bod(id_, bx, sv["by"] + sg * sv["lavice_od_m"])
                    stoly.append(("lavice_selska", qx, qz, yaw + (0.0 if sg > 0 else math.pi)))
    return out, placky, stoly


_CS, PLACKY, STOLY_VENKU = _stavby_cesty()
# cesty ke stavbam: osa ze souboru (stejna jako drive _stavby_cesty), placky a stoly se odvozuji od stavby
CESTY_STAVBY = [([tuple(p) for p in _VOZ[i]["osa"]], _VOZ[i]["blender_sirka_m"]) for i in ("ke_stanu", "k_hostinci")]
CESTY = CESTY + CESTY_STAVBY


def placek(x, z):
    """Mira hliny na placku pred hostincem 0..1 (nepravidelny okraj)."""
    m = 0.0
    for px, pz, r in PLACKY:
        d = math.hypot(x - px, z - pz) + 2.0 * sum_m(x, z, 4.0)
        m = max(m, 1.0 - smooth(r - 2.0, r + 1.0, d))
    return m


# mista budoucich staveb bez modelu (krok B: mlyn na odtoku Lhoty, voda.json mlyn) - plosina a mytina jako u stavby
MISTA = [("mlyn", _VODA_J["mlyn"]["stred"][0], _VODA_J["mlyn"]["stred"][1], 0.0, _VODA_J["mlyn"]["rovina_r_m"])] if "mlyn" in _VODA_J else []

# dil mlyna (voda.json mlyn.dil, Misa 21:44 model z Disku; tools/krok_b/mlyn_misto.py): 40 x 40 m s vlastnim terenem,
# potokem, nahonem a dvorem. Teren sveta pod dilem tesne pod terenem dilu (tools/krok_b/mlyn_teren.json z modelu),
# kolem dilu plynule napojeni z hrany dilu na teren (pasma dil). Mlyn je budova: krok po plosinach staveb.
_MDIL = _VODA_J.get("mlyn", {}).get("dil")
if _MDIL:
    with open(os.path.join(os.path.dirname(_SVET), "pravidla_sveta.json"), encoding="utf-8") as _f:
        _PASMA_DIL = json.load(_f)["pasma"]["dil"]
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "krok_b", "mlyn_teren.json")) as _f:
        _MTER = json.load(_f)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "krok_b", "mlyn_voda.json")) as _f:
        _MVODA = json.load(_f)                                # hladiny dilu z modelu (NAVOD_MLYN.md tabulka vody)
    MISTA = [("mlyn", _MDIL["stred"][0], _MDIL["stred"][1], 0.0, 28.0)]      # myti a stavba_near: polouhlopricka dilu


def mlyn_lok(x, z):
    """Svet -> lokalni souradnice dilu mlyna (Godot: x, z; dil x -22..18, z -25..15)."""
    c, s_ = math.cos(_MDIL["natoceni"]), math.sin(_MDIL["natoceni"])
    dx, dz = x - _MDIL["stred"][0], z - _MDIL["stred"][1]
    return dx * c - dz * s_, dx * s_ + dz * c


def mlyn_svet(lx, ly, lz):
    """Lokalni bod dilu mlyna (Godot x, y od dvora, z) -> svet."""
    c, s_ = math.cos(_MDIL["natoceni"]), math.sin(_MDIL["natoceni"])
    return _MDIL["stred"][0] + lx * c + lz * s_, _MDIL["y_dvora"] + ly, _MDIL["stred"][1] - lx * s_ + lz * c


def _mlyn_teren(lx, lz):
    m = _MTER
    fi = min(max((lx - m["x0"]), 0.0), m["nx"] - 1.001)
    fj = min(max((lz - m["z0"]), 0.0), m["nz"] - 1.001)
    i, j = int(fi), int(fj)
    fi, fj = fi - i, fj - j
    g = lambda a, b: m["h"][b * m["nx"] + a]
    return (g(i, j) * (1 - fi) + g(i + 1, j) * fi) * (1 - fj) + (g(i, j + 1) * (1 - fi) + g(i + 1, j + 1) * fi) * fj


def v_dilu_mlyna(x, z):
    """Lezi bod v pudorysu terenu dilu mlyna (tam je videt teren modelu, svet je pod nim)?"""
    if not _MDIL:
        return False
    lx, lz = mlyn_lok(x, z)
    return _MTER["x0"] <= lx <= _MTER["x0"] + _MTER["nx"] - 1 and _MTER["z0"] <= lz <= _MTER["z0"] + _MTER["nz"] - 1


def mlyn_pad(x, z, y):
    """Teren sveta u dilu mlyna: uvnitr pod terenem dilu (pod_dilem_m, k hrane na nulu), v pasu napojeni_m plynule
    z hrany dilu (vcetne koryta potoka na hrane) na teren."""
    if not _MDIL:
        return y
    lx, lz = mlyn_lok(x, z)
    x0, x1 = _MTER["x0"], _MTER["x0"] + _MTER["nx"] - 1
    z0, z1 = _MTER["z0"], _MTER["z0"] + _MTER["nz"] - 1
    ex = max(x0 - lx, lx - x1, 0.0)
    ez = max(z0 - lz, lz - z1, 0.0)
    d = math.hypot(ex, ez)
    pas = _PASMA_DIL["napojeni_m"]
    if d >= pas:
        return y
    hr = _MDIL["y_dvora"] + _mlyn_teren(min(max(lx, x0), x1), min(max(lz, z0), z1))
    if d > 0.0:
        return hr + (y - hr) * smooth(0.0, pas, d)
    dov = min(lx - x0, x1 - lx, lz - z0, z1 - lz)                # vzdalenost dovnitr od hrany
    return hr - _PASMA_DIL["pod_dilem_m"] * smooth(0.0, 2.0, dov)


def stavba_near(x, z, extra=0.0):
    for id_, cx, cz, yaw, r in STAVBY + MISTA:
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
    for id_, cx, cz, yaw, r in STAVBY + RUINY_ROVINA + MISTA:
        if r <= 0.0:
            continue                                          # ruina bez roviny (lokace.json ruiny rovina_r_m)
        if id_ == "mlyn" and _MDIL:
            continue                                          # dil ma vlastni teren (mlyn_pad)
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


def perej(x, z):
    """Brod / perej 0..1 podle bodu na ose: koryto sirsi a melci, plne kamenu (stridaji se s tunemi)."""
    return smooth(0.02, 0.3, perlin(x / 38.0 + 7.7, z / 38.0 - 1.3))


def river(x, z):
    """(vzdalenost od osy potoka, vyska dna v prostoru hills, perej 0..1) nebo None daleko."""
    r = _REKA_LINE.near(x, z)
    if r is None:
        return None
    bed = _river_bed()
    i = int(r[3])
    t = r[3] - i
    b = bed[i] * (1 - t) + bed[min(i + 1, len(bed) - 1)] * t
    pj = perej(r[1], r[2])
    return r[0], b + 0.32 * pj, pj


_PO = _VODA_J["potok"]


def river_bank(d, pj=0.0):
    """Povolena vyska terenu nad dnem ve vzdalenosti d od osy: koryto, brehy, svahy doliny az na puvodni teren.
    Brehy vymlete: u vody strmy stupen (podemlety breh), nad nim pozvolneji; v brodu koryto sirsi a mělke.
    Sirka (breh_nasobek) a svah doliny z voda.json: do udoli_zlom_m mirny, dal strmejsi, at dolina dosedne na teren
    driv, nez koryto skonci (radce 16:45: zadny schod)."""
    wf = _PO["breh_nasobek"] * (1.0 + 0.75 * pj)
    dd = d / wf
    return ((0.75 - 0.35 * pj) * smooth(1.5, 2.5, dd) + 1.0 * smooth(2.4, 8.0, dd) + max(0.0, d - 8.0 * wf) * _PO["udoli_svah_blizko"]
            + max(0.0, d - _PO["udoli_zlom_m"]) * (_PO["udoli_svah_daleko"] - _PO["udoli_svah_blizko"]))


def smin(a, b, k):
    """Mekke minimum (polomer k): dolina dosedne na teren bez hrany."""
    hh = max(0.0, k - abs(a - b)) / k
    return min(a, b) - hh * hh * k * 0.25


# ---- toky a rybniky z voda.json (krok B, radce 16:50): koryto a dolina, hraze; hladina jen klesa (data)
class _Tok:
    def __init__(self, t):
        self.id = t["id"]
        self.osa = [(p[0], p[1]) for p in t["osa_xzy"]]
        self.hl = [p[2] for p in t["osa_xzy"]]
        self.w = t["sirka_m"]
        self.hloubka = t["hloubka_m"]
        self.line = _Line(self.osa, 30.0)

    def hladina(self, r):
        i = int(r[3])
        t = r[3] - i
        return self.hl[i] * (1 - t) + self.hl[min(i + 1, len(self.hl) - 1)] * t


TOKY = [_Tok(t) for t in _VODA_J.get("toky", [])]
_BEZ_VODY_TVAR = bool(os.environ.get("TVRZ_BEZ_VODY_TVAR"))
_TT = _VODA_J["toky_tvar"]
RYBNIKY = [_VODA_J[k] for k in ("rybnik_lhota", "rybnik_tvrz") if k in _VODA_J]


with open(os.path.join(os.path.dirname(_SVET), "pravidla_sveta.json"), encoding="utf-8") as _f:
    _PASMA_VODA = json.load(_f)["pasma"]["voda"]
VODNI_ROSTLINY = ("rakos", "orobinec", "leknin", "okreh")       # rostou ve vode a na breznim pasu


def ve_vode(x, z, y):
    """Vzdalenost bodu (x, z) s vyskou terenu y od okraje vody malych toku a rybniku (zaporna = ve vode).
    Rostliny (krome vodnich) se sazi az za pasmo brehu (pravidla_sveta.json pasma voda breh_m) - jedno pravidlo
    pro vsechny rozsevy (27. 10.: 249 trsu, keru a stromu stalo v novych tocich kroku B)."""
    best = 1e9
    tn = tok_near(x, z)
    if tn:
        best = tn[0] - tn[2]
    for ryb in RYBNIKY:
        cx, cz = ryb["stred"]
        dc = math.hypot(x - cx, z - cz)
        if "polomer_m" in ryb:
            best = min(best, dc - ryb["polomer_m"])
        elif dc < 60.0:
            # rybnik z dilu: voda = teren pod hladinou, jinak vzdalenost od okraje hladiny (voda_polomer_m, zmereno v dilu)
            best = min(best, -0.1 if y < ryb["hladina_y"] else dc - ryb.get("voda_polomer_m", 0.0))
    return best


def rostlina_ve_vode(pid, x, z, y):
    """True, kdyz se rostlina pid na (x, z, y) nesmi sadit (ve vode nebo na brehovem pasu)."""
    if any(k in pid for k in VODNI_ROSTLINY):
        return False
    return ve_vode(x, z, y) < _PASMA_VODA["breh_m"]


# ------------------------------------------------------------------ stanoviste druhu (druhy.json, krok C)
_DRUHY_J = _svet("druhy.json")["druhy"]
_DRUHY_ID = sorted((d["id"] for d in _DRUHY_J), key=len, reverse=True)
DRUHY = {d["id"]: d for d in _DRUHY_J}
SKALY_MRIZKA = {}                    # bunky 8 m u skalnich vezi a balvanu (zapisuje nove.misto; test ze svet.json)


def druh_id(pid):
    """Klic rostliny (model_varianta, _daleko) -> id druhu z druhy.json nebo None."""
    import re
    for i in _DRUHY_ID:
        if pid == i or re.fullmatch(re.escape(i) + r"(_\d+|_daleko2?)*", pid):
            return i
    return None


def zapis_skalu(x, z):
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            SKALY_MRIZKA[(int(x // 8) + dx, int(z // 8) + dz)] = True


def stanoviste(x, z, y):
    """Stanoviste bodu (druhy.json popis): voda, breh, les, okraj, pole, mez, tvrz, ves, cesta, skala, louka."""
    out = set()
    vv = ve_vode(x, z, y)
    rv = river(x, z)
    pul = 4.8 * _PO["breh_nasobek"] * 0.5
    if vv < 0.0 or (rv is not None and rv[0] < pul):
        out.add("voda")
    if vv < 8.0 or (rv is not None and rv[0] < pul + 8.0):
        out.add("breh")
    f = forest(x, z)
    if f > 0.5:
        out.add("les")
    if 0.05 < f <= 0.5 or (f <= 0.5 and any(forest(x + dx, z + dz) > 0.5 for dx, dz in ((25, 0), (-25, 0), (0, 25), (0, -25)))):
        out.add("okraj")
    if field_strip(x, z, mez=False) is not None:
        out.add("pole" if field_strip(x, z) is not None else "mez")
    if math.hypot(x, z) < 70.0:
        out.add("tvrz")
    if ves_r(x, z) < VES_R + 30.0 or any(math.hypot(x - cx, z - cz) < 40.0 for _, cx, cz, _, _ in STAVBY):
        out.add("ves")
    rn = road_near(x, z)
    if rn and rn[0] - rn[3] < 6.0:
        out.add("cesta")
    if SKALY_MRIZKA.get((int(x // 8), int(z // 8))):
        out.add("skala")
    if not out & {"les", "pole", "mez", "voda", "tvrz"}:
        out.add("louka")
    return out


with open(os.path.join(os.path.dirname(_SVET), "pravidla_sveta.json"), encoding="utf-8") as _f:
    _PASMA_BUDOVA = json.load(_f)["pasma"]["budova"]
_BUDOVY = []


def _budovy():
    """Pudorysy staveb pro pravidlo uzivani: domy a chlevy vsi (vesnice.layout), hostinec a stan (PUDORYS)."""
    if not _BUDOVY:
        import vesnice
        for h in vesnice.layout():
            _BUDOVY.append((h["p"].x, h["p"].z, h["yaw"], h["L"] / 2, h["W"] / 2))
            bp, byaw, bL, bW = h["barn"]
            _BUDOVY.append((bp.x, bp.z, byaw, bL / 2, bW / 2))
        for id_, (x0, x1, y0, y1) in PUDORYS.items():
            cx, cz = stavba_bod(id_, (x0 + x1) / 2, (y0 + y1) / 2)
            _BUDOVY.append((cx, cz, -stavba_yaw(id_), (x1 - x0) / 2, (y1 - y0) / 2))
    return _BUDOVY


def od_zdi(x, z):
    """Vzdalenost bodu od nejblizsi zdi stavby (0 uvnitr) nebo 1e9."""
    best = 1e9
    for cx, cz, yaw, hu, hv in _budovy():
        dx, dz = x - cx, z - cz
        if abs(dx) > 40.0 or abs(dz) > 40.0:
            continue
        u = dx * math.cos(yaw) + dz * math.sin(yaw)
        v = -dx * math.sin(yaw) + dz * math.cos(yaw)
        best = min(best, math.hypot(max(abs(u) - hu, 0.0), max(abs(v) - hv, 0.0)))
    return best


VYSOKE_U_DOMU = ("divoka_trava", "grass_medium", "fern", "kapradi", "shrub", "sipek", "bez_cerny")


def uzivani_smi(pid, x, z):
    """Pravidlo uzivani (Misa 27. 10.): u paty zdi (pasma.budova plevel_u_zdi_m) plevel a trava, dal do drn_m jen
    nizky seslapany drn - zadna vysoka trava, kapradi ani kere; strom az od kmen_od_zdi_m."""
    i = druh_id(pid)
    sk = DRUHY[i]["skupina"] if i else ""
    if sk not in ("strom", "ker", "trava", "bylina"):
        return True
    d = od_zdi(x, z)
    if sk == "strom":
        return d >= _PASMA_BUDOVA["kmen_od_zdi_m"]
    if pid.startswith(VYSOKE_U_DOMU):
        return not (_PASMA_BUDOVA["plevel_u_zdi_m"] < d < _PASMA_BUDOVA["drn_m"])
    return True


def druh_smi(pid, x, z, y):
    """Sit druh pid na (x, z, y)? Jen na jeho stanovisti (druhy.json) a historicky; nezname druhy a 'vse' ano."""
    i = druh_id(pid)
    if i is None:
        return True
    d = DRUHY[i]
    if not d["historicky"] or d.get("pouzit", True) is False or not uzivani_smi(pid, x, z):
        return False
    st = d.get("stanoviste", ["vse"])
    return "vse" in st or bool(stanoviste(x, z, y) & set(st))


def kompozice_remizky():
    """Remizky z lokace.json kompozice (krok C bod 7): kazdy zaviera prilis otevreny dohled (duvod v zaznamu).
    Uprostred stromy (dub, lipa, briza - stromy v2), na kraji kere (lieska/hloh = shrub_02, sipek, bez), vse podle
    stanovist a vody (druh_smi). Vraci ([(model v2, x, z, vyska)], [(model, x, z, vyska)])."""
    R = random.Random(1979)
    stromy, kere = [], []
    # kere okraje jen druhy s pouzit (druhy.json; sipek vyrazen - drive se tise vynechal a okraj remizku ridl)
    kere_modely = [m for m in ("shrub_02", "sipek", "bez_cerny_1", "shrub_02")
                   if DRUHY.get(druh_id(m) or "", {}).get("pouzit", True)]
    for r in _LOKACE_J.get("kompozice", {}).get("remizky", []):
        cx, cz = r["stred"]
        rad = r["polomer_m"]
        for _ in range(int(rad * 0.6)):
            a, d = R.uniform(0, 2 * math.pi), rad * math.sqrt(R.random()) * 0.6
            stromy.append((R.choice(["dub_stredni", "lipa_stredni", "dub_stredni", "lipa_stredni", "dub_stary"]),
                           cx + math.cos(a) * d, cz + math.sin(a) * d, R.uniform(9.0, 15.0)))
        for _ in range(int(rad * 1.6)):
            a, d = R.uniform(0, 2 * math.pi), rad * R.uniform(0.55, 1.05)
            kere.append((R.choice(kere_modely), cx + math.cos(a) * d, cz + math.sin(a) * d,
                         R.uniform(1.2, 3.0)))
    return stromy, kere


def tok_near(x, z):
    """(vzdalenost, hladina, pul sirky vody, tok) nejblizsiho maleho toku nebo None."""
    best = None
    for t in TOKY:
        r = t.line.near(x, z)
        if r and (best is None or r[0] < best[0]):
            best = (r[0], t.hladina(r), t.w / 2.0, t)
    return best


def _hraz(x, z, ryb):
    """Vyska koruny a svahu hraze rybnika v bode (nebo -inf mimo)."""
    hz = ryb.get("hraz")
    if not hz:
        return -1e9
    cx, cz = hz["stred"]
    ux, uz = hz["smer_osy"]
    dx, dz = x - cx, z - cz
    a = dx * ux + dz * uz
    b = abs(-dx * uz + dz * ux)
    a = max(0.0, abs(a) - hz["delka_m"] / 2.0)
    d = math.hypot(a, max(0.0, b - hz["koruna_sirka_m"] / 2.0))
    return ryb["hladina_y"] + hz["koruna_nad_hladinou_m"] - d * hz["sklon_svahu"]


_BRODY_TOKU = [(p["stred"][0], p["stred"][1], p["polomer_m"]) for p in _svet("cesty.json").get("prechody", [])
               if p["druh"] == "brod" and p["tok"] != "bystrice"]


def voda_tvar(x, z, h):
    """Teren po vode: koryta a doliny malych toku, dno a breh rybniku (mimo dil), hraze."""
    if _BEZ_VODY_TVAR:
        return h                                              # planovani tras toku (tools/krok_b) nad terenem bez nich
    tn = tok_near(x, z)
    if tn is not None:
        d, hl, pw, t = tn
        brod = any(math.hypot(x - b[0], z - b[1]) < b[2] for b in _BRODY_TOKU)
        hk = _TT["brod_hloubka_m"] if brod else t.hloubka      # zaznam prechodu (cesty.json druh brod): melke koryto
        bed = hl - hk
        allow = (hk + _TT["breh_m"]) * smooth(pw, pw + _TT["breh_sirka_m"], d) + _TT["svah"] * max(0.0, d - pw - _TT["breh_sirka_m"])
        # dolina jen do dosahu (toky_tvar dolina_m), dal plynule puvodni teren - ne sikma rovina pres cely kopec
        kraj_d = pw + _TT["breh_sirka_m"] + _TT["dolina_m"]
        w_d = 1.0 - smooth(kraj_d, kraj_d + _TT["dolina_nabeh_m"], d)
        h = h + (smin(h, bed + allow, 0.8) - h) * w_d
        u_nadrze = any(math.hypot(x - r["stred"][0], z - r["stred"][1]) < r.get("polomer_m", r.get("voda_polomer_m", 0.0)) + _TT["breh_sirka_m"] + 2.0
                       for r in RYBNIKY)
        if d >= pw and not u_nadrze and not brod:
            # breh ne nize nez hladina + breh_m (na svahu nasep spodniho brehu, voda nevytece), dal svah nasypu;
            # u nadrze ne - tok do ni vtece
            h = max(h, hl + _TT["breh_m"] - _TT["nasyp_svah"] * max(0.0, d - pw - _TT["breh_sirka_m"]))
    for ryb in RYBNIKY:
        if "polomer_m" in ryb:
            cx, cz = ryb["stred"]
            d = math.hypot(x - cx, z - cz)
            r = ryb["polomer_m"]
            if d < r + 25.0:
                dno = ryb["hladina_y"] - ryb["hloubka_m"] * max(0.0, 1.0 - (d / r) ** 2)
                breh = ryb["hladina_y"] + 0.3 * smooth(r - 1.0, r + 1.0, d) + _TT["svah"] * max(0.0, d - r - 1.0)
                h = smin(h, min(breh, dno) if d < r else breh, 0.8)
        hr = _hraz(x, z, ryb)
        if hr > h and not (tn is not None and tn[0] < tn[2] + 0.6 and tn[3].id.endswith("odtok")):
            h = hr                                            # hraz; vypust (koryto odtoku) prochazi
    return h


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
            if r is None or r[0] > 7.8 * _PO["breh_nasobek"]:
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
    return w * (big + mid + detail(x, z) + micro) + ridge(x, z) * (1.0 + 0.12 * perlin(x / 30.0, z / 30.0)) + ves_hills(x, z) + skaly_podstava(x, z)


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
        if rv is not None:
            # brehy rozbite jako u prikopu: zatoky, vymoly, sesuvy, misty sirsi tune
            dn = rv[0] + 0.9 * perlin(x / 7.0 + 4.1, z / 7.0 - 2.3) + 0.3 * perlin(x / 2.6 - 8.0, z / 2.6 + 1.1)
            h = smin(h, rv[1] + river_bank(max(0.0, dn), rv[2]), 1.5)
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
        if rv is None or rv[0] > 4.8 * _PO["breh_nasobek"]:
            yr2 = road_y(px, pz, land_fn) - 0.12
            if yr2 > y:
                # nasyp najezdu: koruna 7 m siroka (opery zasypane hlinou), svahy 1:2.5 do okoli,
                # u vody se nasyp zaobli do brehu
                core = 4.8 + 0.4 * perlin(x / 5.0, z / 5.0)      # sirsi nez mostovka: konec mostu nevisi nad srazem
                slope = max(5.0, (yr2 - y) * 2.5)
                k2 = 1.0 - smooth(core, core + slope, d)
                if rv is not None:
                    k2 *= smooth(4.8 * _PO["breh_nasobek"], 6.6 * _PO["breh_nasobek"], rv[0])
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


_VYP = None
_VYP_POCITAM = False


_LOM = _PLOCHY_J["lom"]


def lom_tvar(x, z, y):
    """Lom (plochy.json lom): dno vychodne od paty steny, stena = sraz z kopce na dno; na koncich lomu a u Bystrice
    plynule do terenu. Jen snizuje (lom je vykopany)."""
    z0, z1 = _LOM["z"]
    ok = _LOM["okraj_m"]
    if not (z0 - ok < z < z1 + ok and _LOM["pata_x"] - 4.0 < x < _LOM["x_konec"] + 12.0):
        return y
    wz = smooth(z0 - ok, z0, z) * (1.0 - smooth(z1, z1 + ok, z))
    wx = smooth(_LOM["pata_x"] - _LOM["stena_sirka_m"], _LOM["pata_x"], x) * (1.0 - smooth(_LOM["x_konec"], _LOM["x_konec"] + 12.0, x))
    w = wz * wx
    return min(y, y + (_LOM["dno_y"] - y) * w)


def vypln(x, z):
    """Vyplne bezodtokych prohlubni (voda.json vyplne, radce 16:45): mrizka puvodniho terenu (fort.land bez cest a
    plosin), priority-flood od okraje mapy a od vody (potok, toky, rybniky, prikop tvrze, lom) s mirnym spadem;
    vraci o kolik teren zvednout. Voda tak vzdy odtece, dira zustane jen tam, kde je voda."""
    global _VYP, _VYP_POCITAM
    if _VYP_POCITAM:
        return 0.0
    if _VYP is None:
        import heapq
        import fort
        _VYP_POCITAM = True
        cfg = _VODA_J["vyplne"]
        k = cfg["mrizka_m"]
        hp = _svet("svet.json")["hranice_pruchod"]
        x0, z0 = hp["x0"] - 2 * k, hp["z0"] - 2 * k
        nx = int((hp["x1"] - hp["x0"]) / k) + 5
        nz = int((hp["z1"] - hp["z0"]) / k) + 5
        H = [fort.land(x0 + (c % nx) * k, z0 + (c // nx) * k, False, False) for c in range(nx * nz)]
        F = list(H)
        hot = bytearray(nx * nz)
        pq = []

        def voda(px, pz):
            if any(a <= px <= c and b <= pz <= d for a, b, c, d in (r["obdelnik"] for r in _PLOCHY_J["teren"].get("bez_srazeni", []))):
                return True                                   # tvrz a lom maji vlastni tvar (plochy.json teren.bez_srazeni)
            rv = river(px, pz)
            if rv is not None and rv[0] < _PO["pulsirka_vody_m"] + 1.5:
                return True
            tn = tok_near(px, pz)
            if tn is not None and tn[0] < tn[2] + 0.5:
                return True
            for ryb in RYBNIKY:
                cx, cz = ryb["stred"]
                if math.hypot(px - cx, pz - cz) < ryb.get("polomer_m", ryb.get("pulsirka_dilu_m", 30.0)):
                    return True
            return False
        for c in range(nx * nz):
            i, j = c % nx, c // nx
            if i in (0, nx - 1) or j in (0, nz - 1) or voda(x0 + i * k, z0 + j * k):
                hot[c] = 1
                heapq.heappush(pq, (H[c], c))
        eps = cfg["spad"] * k
        while pq:
            v, c = heapq.heappop(pq)
            i, j = c % nx, c // nx
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = i + di, j + dj
                if 0 <= a < nx and 0 <= b < nz:
                    n = b * nx + a
                    if not hot[n]:
                        hot[n] = 1
                        F[n] = max(H[n], v + eps)
                        heapq.heappush(pq, (F[n], n))
        # svahy bez skaly nejvys plochy.json teren.svah_max_stupne: kuzel zdola (od nejnizsich bunek), vrcholy se srazi;
        # nevznikne dira (bunka nikdy pod souseda + sklon). Skalni hreben, tvrz, lom a voda beze zmeny.
        tp = _PLOCHY_J["teren"]
        s_max = math.tan(math.radians(tp["svah_max_stupne"]))

        bez = [r["obdelnik"] for r in tp.get("bez_srazeni", [])]

        def volno(px, pz):
            if voda(px, pz):
                return False
            if any(a <= px <= c and b <= pz <= d for a, b, c, d in bez):
                return False                                    # lom, tvrz (plochy.json teren.bez_srazeni)
            d = seg_info(px, pz, HREBEN)[0]
            return d > tp["bez_omezeni_u_hrebene_m"]
        VOL = bytearray(1 if volno(x0 + (c % nx) * k, z0 + (c // nx) * k) else 0 for c in range(nx * nz))
        G = list(F)
        pq2 = [(G[c], c) for c in range(nx * nz)]
        heapq.heapify(pq2)
        hot2 = bytearray(nx * nz)
        srazeno = 0
        while pq2:
            v, c = heapq.heappop(pq2)
            if hot2[c] or v > G[c] + 1e-6:
                continue
            hot2[c] = 1
            i, j = c % nx, c // nx
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                a, b = i + di, j + dj
                if 0 <= a < nx and 0 <= b < nz:
                    n = b * nx + a
                    lim = max(G[c] + s_max * k * math.hypot(di, dj), F[n] - tp["srazeni_max_m"])
                    if not hot2[n] and G[n] > lim + 1e-6 and VOL[n]:
                        G[n] = lim                              # nejvys o srazeni_max_m, strmejsi zbytek = skala
                        srazeno += 1
                        heapq.heappush(pq2, (G[n], n))
        D = [G[c] - H[c] for c in range(nx * nz)]
        DF = [F[c] - H[c] for c in range(nx * nz)]           # jen vyplne (protokol stavby: zvlast od srazeni svahu)
        n = sum(1 for d in D if d > cfg["nechat_m"])
        print("vyplne prohlubni: %d bunek %.0f m nad %.1f m, nejvic %.1f m; svahy srazene na %.0f st.: %d bunek, nejvic %.1f m"
              % (n, k, cfg["nechat_m"], max(D), tp["svah_max_stupne"], srazeno, -min(D)))
        _VYP = (x0, z0, k, nx, nz, D, DF)
        _VYP_POCITAM = False
    return _vyp_mriz(x, z, 6)


def vypln_jen_vyplne(x, z):
    """Cast vypln bez srazeni svahu (protokol stavby rozlisuje vyplne prohlubni a srazeni svahu)."""
    if _VYP_POCITAM:
        return 0.0
    if _VYP is None:
        vypln(x, z)
    return _vyp_mriz(x, z, 7)


def _vyp_mriz(x, z, ix):
    x0, z0, k, nx, nz = _VYP[:5]
    D = _VYP[ix - 1]
    fi = (x - x0) / k
    fj = (z - z0) / k
    i = min(max(int(math.floor(fi)), 0), nx - 2)
    j = min(max(int(math.floor(fj)), 0), nz - 2)
    fi = min(max(fi - i, 0.0), 1.0)
    fj = min(max(fj - j, 0.0), 1.0)
    a = D[j * nx + i] * (1 - fi) + D[j * nx + i + 1] * fi
    b = D[(j + 1) * nx + i] * (1 - fi) + D[(j + 1) * nx + i + 1] * fi
    return a * (1 - fj) + b * fj


def toky_voda(coll, land_fn):
    """Hladina malych toku (pas po proudu, sirka toku) a generovanych rybniku (mrizka 1 m, jen nad dnem)."""
    from lib import Part
    import lib
    import veg
    if "voda_potok" not in lib.MAT:
        lib.MAT["voda_potok"] = veg.mat_pond("voda_potok")
        lib.GAMEMAT["voda_potok"]["tekouci"] = 1.0
    if "voda_prikop" not in lib.MAT:
        lib.MAT["voda_prikop"] = veg.mat_pond("voda_prikop")
    P = Part("Toky_voda")
    smery = []                      # smer po proudu kazde plochy (poradi ploch = poradi P.mesh)
    def v_nadrzi(x, z):
        # hladina rybniku (polomer_m / voda_polomer_m z voda.json): pas toku konci na kraji vody - uvnitr lezel 2 cm
        # nad hladinou rybnika, dve pruhledne vrstvy = tmavy mnohouhelnik (Misa 0.98, rybnik Lhota)
        for ryb in RYBNIKY:
            r = ryb.get("polomer_m", ryb.get("voda_polomer_m"))
            if r and math.hypot(x - ryb["stred"][0], z - ryb["stred"][1]) < r:
                return True
        return False

    for t in TOKY:
        pts = t.osa
        for k2 in range(len(pts) - 1):
            (ax, az), (bx, bz) = pts[k2], pts[k2 + 1]
            if v_nadrzi(ax, az) and v_nadrzi(bx, bz):
                continue
            if v_nadrzi(bx, bz) or v_nadrzi(ax, az):
                vn = v_nadrzi(bx, bz)
                lo, hi = 0.0, 1.0                  # pulenim k okraji vody
                for _ in range(12):
                    m = (lo + hi) / 2.0
                    ins = v_nadrzi(ax + (bx - ax) * m, az + (bz - az) * m)
                    if ins == vn:
                        hi = m
                    else:
                        lo = m
                if vn:
                    bx, bz = ax + (bx - ax) * lo, az + (bz - az) * lo
                else:
                    ax, az = ax + (bx - ax) * hi, az + (bz - az) * hi
            L = math.hypot(bx - ax, bz - az) or 1.0
            nx_, nz_ = -(bz - az) / L * t.w / 2.0, (bx - ax) / L * t.w / 2.0
            ya, yb = t.hl[k2], t.hl[k2 + 1]
            P.mesh([(ax - nx_, ya, az - nz_), (ax + nx_, ya, az + nz_), (bx + nx_, yb, bz + nz_), (bx - nx_, yb, bz - nz_)],
                   [(0, 1, 2, 3)], "voda_potok", uvs=[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]])
            smery.append(((bx - ax) / L, (bz - az) / L))
    # dil mlyna: nahon, vantrok a lednice (osy a hladiny z modelu, tools/krok_b/mlyn_voda.json); potok dilu je tok
    if _MDIL:
        for usek in ("nahon", "vantrok", "lednice"):
            u = _MVODA[usek]
            pts = [mlyn_svet(*p) for p in u["body"]]
            for k2 in range(len(pts) - 1):
                (ax, ya, az), (bx, yb, bz) = pts[k2], pts[k2 + 1]
                L = math.hypot(bx - ax, bz - az) or 1.0
                nx_, nz_ = -(bz - az) / L * u["sirka"] / 2.0, (bx - ax) / L * u["sirka"] / 2.0
                P.mesh([(ax - nx_, ya, az - nz_), (ax + nx_, ya, az + nz_), (bx + nx_, yb, bz + nz_), (bx - nx_, yb, bz - nz_)],
                       [(0, 1, 2, 3)], "voda_potok", uvs=[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]])
                smery.append(((bx - ax) / L, (bz - az) / L))
    o = P.commit(coll)
    if _MDIL:
        _mlyn_pad_vody(coll)
    _toky_proud(o, smery)
    _toky_kameny(coll, land_fn)
    for ryb in RYBNIKY:
        if "polomer_m" not in ryb:
            continue
        Q = Part("Rybnik_tvrz_voda")
        cx, cz = ryb["stred"]
        r = ryb["polomer_m"] + 1.5
        y = ryb["hladina_y"]
        st = 1.0
        n = int(2 * r / st)
        for i in range(n):
            for j in range(n):
                x, z = cx - r + i * st, cz - r + j * st
                if math.hypot(x + st / 2 - cx, z + st / 2 - cz) > r:
                    continue
                if min(land_fn(x, z), land_fn(x + st, z), land_fn(x, z + st), land_fn(x + st, z + st)) > y:
                    continue
                Q.mesh([(x, y, z), (x + st, y, z), (x + st, y, z + st), (x, y, z + st)], [(0, 1, 2, 3)], "voda_prikop",
                       uvs=[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]])
        Q.commit(coll)


def _toky_kameny(coll, land_fn):
    """Kameny v korytu a na brezich malych toku jako u Bystrice (_reka_kameny), hustota z voda.json toky_tvar
    kameny_na_m (Misa 28. 10.: „takove dno a kameny okolo by mely mit i potoky a strouhy“). Zapustene, jen kde je
    teren pod hladinou nebo do pul metru od kraje vody."""
    import nove
    from lib import Part
    R = random.Random(1393)
    Pk = Part("Toky_kameny", bevel=0.0)
    hust = _TT["kameny_na_m"]
    n = 0
    for t in TOKY:
        pts = t.osa
        for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
            L = math.hypot(bx - ax, bz - az)
            if L < 1e-3:
                continue
            tx, tz = (bx - ax) / L, (bz - az) / L
            k = 0.0
            while k < L:
                k += R.expovariate(hust)
                if k >= L:
                    break
                o = R.uniform(-1.0, 1.0) * (t.w / 2.0 + 0.5)
                x, z = ax + tx * k - tz * o, az + tz * k + tx * o
                size = R.uniform(0.15, 0.45) if R.random() < 0.85 else R.uniform(0.45, 0.8)
                sink = R.uniform(0.25, 0.4)
                if abs(o) < t.w / 2.0:
                    # v korytu kamen pod hladinou (Misa 0.98: kameny trci z vody): vyska nad dnem size*(1-sink) <= hloubka
                    size = min(size, t.hloubka / (1.0 - sink))
                pid = R.choice(nove.KAMENY_POLE)
                nove.misto(pid, x, land_fn(x, z), z, size / nove.DIM[pid][0], R.uniform(0, 2 * math.pi),
                           Pk if size > 0.6 else None, sink=sink)
                n += 1
    Pk.commit(coll)
    print("toky: %d kamenu v korytu a na brezich" % n)


def _toky_proud(o, smery):
    """Barva vrcholu hladiny malych toku jako u Bystrice (_reka_pena): R pena 0, G perej 0, B/A smer po proudu.
    Bez ni mel export barvu vychozi (R ~0,9) a shader voda (tekouci) kreslil celou hladinu jako penu - bile pasy
    (Misa 28. 10.: toky, nahon a lednice mlyna). Smer v hernich souradnicich (x, z) jako _reka_pena."""
    if o is None:
        return
    me = o.data
    col = me.color_attributes.new("Pena", "BYTE_COLOR", "CORNER")
    vals = [0.0] * (len(me.loops) * 4)
    for poly in me.polygons:
        dx, dz = smery[poly.index]
        for li in poly.loop_indices:
            vals[li * 4:li * 4 + 4] = [0.0, 0.0, 0.5 + 0.5 * dx, 0.5 + 0.5 * dz]
    col.data.foreach_set("color", vals)
    me.color_attributes.active_color = col
    me.color_attributes.render_color_index = me.color_attributes.active_color_index


def reka(coll, land_fn):
    """Potok Bystrice: hladina v korytu (pas po proudu), dreveny most na odbocce do vsi."""
    from lib import M, Part
    from mathutils import Matrix, Vector
    # hladina jako u prikopu: mrizka 1.5 m, plocha jen tam, kde je teren pod hladinou (okraj sleduje breh)
    import lib
    import veg
    if "voda_prikop" not in lib.MAT:
        lib.MAT["voda_prikop"] = veg.mat_pond("voda_prikop")
    if "voda_potok" not in lib.MAT:
        lib.MAT["voda_potok"] = veg.mat_pond("voda_potok")
        lib.GAMEMAT["voda_potok"]["tekouci"] = 1.0             # tekouci voda: bez okrehku, vlnky po proudu
    P = Part("Reka_voda")
    # hladina 0.5 m nad dnem v ose (dno jsem nejnizsi misto napric), v brodu melci; vyhlazena: souvisly tok, ne louze
    wl0 = [min(land_fn(x, z), land_fn(x + 0.8, z), land_fn(x - 0.8, z), land_fn(x, z + 0.8), land_fn(x, z - 0.8))
           + 0.5 - 0.3 * perej(x, z) for x, z in REKA]
    wl = [sum(wl0[max(0, i - 4):i + 5]) / len(wl0[max(0, i - 4):i + 5]) for i in range(len(wl0))]
    wl = [max(a, b - 0.05) for a, b in zip(wl, wl0)]           # nikde pod mistni hladinou (jinak susi useky)
    step = 1.0                       # rozpocet: mrizka hladiny 1 m (0,5 m = 116 tis. troj.)
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

    # delka podel toku (UV.x) pro tekouci vlnky; po proudu = smer klesajici hladiny
    cum = [0.0]
    for (ax_, az_), (bx_, bz_) in zip(REKA[:-1], REKA[1:]):
        cum.append(cum[-1] + math.hypot(bx_ - ax_, bz_ - az_))
    sgn = 1.0 if wl0[0] >= wl0[-1] else -1.0
    uvv = {}

    def v(i, k, y):
        if (i, k) not in vid:
            vid[(i, k)] = len(verts)
            x_, z_ = x0 + i * step, z0 + k * step
            verts.append((x_, y, z_))
            r_ = _REKA_LINE.near(x_, z_)
            if r_ is None:
                uvv[(i, k)] = (0.0, 0.0)
            else:
                j_ = min(int(r_[3]), len(cum) - 2)
                t_ = r_[3] - j_
                sl = cum[j_] + (cum[j_ + 1] - cum[j_]) * t_
                uvv[(i, k)] = (sgn * sl * 0.25, r_[0] * 0.25)
        return vid[(i, k)]
    fkeys = []
    ni, nk = int((x1 - x0) / step), int((z1 - z0) / step)
    for i in range(ni):
        for k in range(nk):
            r = _REKA_LINE.near(x0 + (i + 0.5) * step, z0 + (k + 0.5) * step)
            if r is None or r[0] > 11.0:
                continue
            cs = [lev(i, k), lev(i + 1, k), lev(i + 1, k + 1), lev(i, k + 1)]
            if any(c is None for c in cs) or min(c[1] for c in cs) > max(c[0] for c in cs) - 0.02:
                continue
            y = sum(c[0] for c in cs) / 4
            faces.append((v(i, k, cs[0][0]), v(i, k + 1, cs[3][0]), v(i + 1, k + 1, cs[2][0]), v(i + 1, k, cs[1][0])))
            fkeys.append([(i, k), (i, k + 1), (i + 1, k + 1), (i + 1, k)])
    P.mesh(verts, faces, "voda_potok", [[uvv[q] for q in fk] for fk in fkeys])
    kam = _reka_kameny(coll, land_fn, wl, sgn)
    o = P.commit(coll)
    _reka_pena(o, kam, sgn, verts)
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


_SKLON = {}


def sklon(x, z):
    """(sklon, dh/dz) terenu na zakladne plochy.json sklon_zaklad_m (bez plosin a cest); mrizka 5 m, pamet."""
    k = (round(x / 5.0), round(z / 5.0))
    v = _SKLON.get(k)
    if v is None:
        import fort
        b = _PLOCHY_J["sklon_zaklad_m"] / 2.0
        cx, cz = k[0] * 5.0, k[1] * 5.0
        L = lambda a, c: fort.land(a, c, flat=False, pads=False)
        gx = (L(cx + b, cz) - L(cx - b, cz)) / (2 * b)
        gz = (L(cx, cz + b) - L(cx, cz - b)) / (2 * b)
        v = (math.hypot(gx, gz), gz)
        _SKLON[k] = v
    return v


def field_strip(x, z, mez=True):
    """Pole kolem vsi v honech: kazdy hon (nepravidelny blok) ma lany jinym smerem a jinak siroke, mezi hony
    travnate meze s kerim, nektere hony jsou louka nebo pastvina (uhor). Vnejsi hranice nepravidelna.
    Vraci (cislo lanu, plodina 0..3) nebo None. Vzor lanu kresli shaders/zem.gdshader stejnou nahodou."""
    r = ves_r(x, z)
    wob = 22.0 * perlin(x / 90.0 + 5.0, z / 90.0 - 3.0)
    if r < 60.0 + 0.5 * wob:
        return None
    tn = tok_near(x, z)
    if tn and tn[0] < tn[2] + _PASMA_VODA["breh_m"]:
        return None                                       # tok a jeho breh nejsou pole
    if r > VES_R + 270.0 + 2.0 * wob:
        # krok B (plochy.json pole_dolina): dal od vsi jen lany v doline u potoka
        pd = _PLOCHY_J["pole_dolina"]
        rv = river(x, z)
        if (rv is None or not (pd["od_potoka_m"] < rv[0] < pd["do_potoka_m"])
                or math.hypot(x - VES[0], z - VES[1]) > pd["od_vsi_max_m"]):
            return None
        rn = road_near(x, z)
        if (rn and rn[0] < rn[3] + 6.0) or stavba_near(x, z, 10.0):
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
    if sklon(x, z)[0] > _PLOCHY_J["pole"]["max_sklon"]:
        return None                                   # krok B: ve svahu pastvina (plochy.json), lany jen po rovine
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
    # krok B (plochy.json): strme svahy a severni svahy (teren klesa k -z) zalesnene
    s_, gz = sklon(x, z)
    if s_ > _PLOCHY_J["les"]["od_sklonu"] or (gz > 0.0 and s_ > _PLOCHY_J["les"]["sever_od_sklonu"]):
        v += 1.0
    return smooth(0.38, 0.62, v)


# Maska povrchu (ground_attrs) se vzorkuje ve vrcholech site terenu nebo v mrizce travy: sum s periodou pod ~2 kroky
# vzorkovani se navzorkuje do nahodnych ctvercu (Misa 27. 10. "zeleny rastr bez logiky" kolem zahonu a mezi domy:
# perioda 2,5 m na siti vsi 2 m). Pravidlo: oktava sumu masky se tlumi podle kroku prave vzorkovane site (Nyquist:
# nic pod 1,5 kroku, plne az od 3 kroku). Krok nastavuje ten, kdo masku vzorkuje (tiles, export mrizek travy).
_KROK_SITE = [1.0]


def sum_m(x, z, perioda, ox=0.0, oz=0.0):
    """Oktava sumu masky povrchu s periodou perioda (m), utlumena pod rozlisenim site (_KROK_SITE)."""
    w = smooth(1.5 * _KROK_SITE[0], 3.0 * _KROK_SITE[0], perioda)
    return perlin(x / perioda + ox, z / perioda + oz) * w if w > 0.0 else 0.0


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
        pd = vesnice.path_dist(x, z) + 0.6 * sum_m(x, z, 3.0)
        if pd < 2.5:
            g = min(g, 0.08 + 0.7 * smooth(-0.3, 2.2, pd))
    pl = placek(x, z)
    if pl > 0.0:
        g = min(g, 0.75 - 0.62 * pl)
    rn = road_near(x, z)
    br = bridge()
    pod_mostem = False
    if br and rn:
        # pod mostovkou neni cesta (Misa 27. 10. „pod mostem je cesta“): usek osy v rozpeti mostu = breh
        t = (rn[1] - br[0]) * br[2] + (rn[2] - br[1]) * br[3]
        pod_mostem = abs(t) < br[4] - 1.0 and math.hypot(rn[1] - br[0] - br[2] * t, rn[2] - br[1] - br[3] * t) < 3.0
    if rn and rn[0] < rn[3] + 3.0 and math.hypot(x, z) > 60 and not pod_mostem:
        # vyslapana hlina kolem cesty s nepravidelnym okrajem
        ed = rn[0] - rn[3] + 1.1 * sum_m(x, z, 3.5) + 0.6 * sum_m(x, z, 1.4, 7.0)
        g = min(g, 0.15 + 0.5 * smooth(-0.4, 1.6, ed))
    if not _NO_RIVER:
        rv = river(x, z)
        if rv is not None and rv[0] < 6.0:
            # vymlete brehy potoka: hola hlina a sterk u vody, nepravidelny okraj drnu
            wf = 1.0 + 0.75 * rv[2]
            ed = rv[0] / wf + 0.5 * sum_m(x, z, 2.2, 3.0) + 0.25 * sum_m(x, z, 0.9, 0.0, -4.0)
            g = min(g, 0.05 + 0.8 * smooth(2.1, 3.4, ed))
    # breh malych toku a generovanych rybniku: hola hlina a sterk u vody jako u Bystrice (toky_tvar breh_hlina_m;
    # Misa 28. 10.: „neni tam koryto, kaminky, hlina, je to v trave“)
    tn = tok_near(x, z)
    if tn is not None and tn[0] < tn[2] + _TT["breh_hlina_m"] + 2.0:
        ed = (tn[0] - tn[2]) + 0.4 * sum_m(x, z, 1.6, 2.0)
        g = min(g, 0.05 + 0.8 * smooth(0.2, _TT["breh_hlina_m"], ed))
    for ryb in RYBNIKY:
        if "polomer_m" in ryb:
            dr = math.hypot(x - ryb["stred"][0], z - ryb["stred"][1]) - ryb["polomer_m"]
            if dr < _TT["breh_hlina_m"] + 2.0:
                ed = dr + 0.5 * sum_m(x, z, 1.8, 5.0)
                g = min(g, 0.05 + 0.8 * smooth(0.0, _TT["breh_hlina_m"], ed))
    return g, les, pole


# ------------------------------------------------------------------ geometrie terenu

def _grid(xs, zs, skip, land_fn, name, P, coll, skip_fn=None):
    """Mrizka terenu: ctverce uvnitr obdelniku skip (nebo kde skip_fn(x, z)) vynechat; atributy trava / les / pole."""
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
            if skip_fn is not None and skip_fn(cx, cz):
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
    _REKA_MIMO[:] = [VRECT, BRECT]
    jemne = {}
    for name, rect, inner, step in (("Teren_ves", VRECT, [], 2.0), ("Teren_most", BRECT, [], 1.0),
                                    ("Teren_okoli", ACT, [NEAR, VRECT, BRECT], 5.0), ("Teren_obzor", FAR, ACT, 25.0)):
        _KROK_SITE[0] = step                                  # sum masky povrchu podle rozliseni pasma
        xs = [rect[0] + step * i for i in range(int(round((rect[1] - rect[0]) / step)) + 1)]
        zs = [rect[2] + step * k for k in range(int(round((rect[3] - rect[2]) / step)) + 1)]
        jem = _bunky_u_vody(rect, inner, step) if name in ("Teren_ves", "Teren_okoli") else set()
        jemne[name] = (rect, step, jem)

        def vynech(cx, cz, rect=rect, step=step, jem=jem, name=name):
            if name == "Teren_okoli" and _v_pasu_reky(cx, cz):
                return True
            return (int((cx - rect[0]) // step), int((cz - rect[2]) // step)) in jem
        verts, faces, attrs = _grid(xs, zs, inner, land_fn, name, None, coll,
                                    skip_fn=vynech if name in ("Teren_okoli", "Teren_ves") else None)
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
    _KROK_SITE[0] = 1.0                                       # pas reky po 1 m
    out.append(_teren_reka(coll, land_fn, [VRECT, BRECT]))
    out.append(_teren_u_vody(coll, land_fn, jemne))
    return out


def _mlyn_pad_vody(coll):
    """Dopad vody z vantroku na korecky kola (voda.json mlyn.dil.pad_vody, body z mlyn_voda.json): pas sirky zlabu
    po parabole volneho padu ve smeru zlabu. Samostatny objekt Mlyn_pad_vody - hra ho ukaze jen pri chodu kola."""
    from lib import Part
    u = _MVODA["vantrok"]
    pv = u["pad_vody"]
    cf = _MDIL["pad_vody"]
    a, b = u["body"][-2], u["body"][-1]
    L = math.hypot(b[0] - a[0], b[2] - a[2]) or 1.0
    sx, sz = (b[0] - a[0]) / L, (b[2] - a[2]) / L
    x0, y0, z0 = pv["z"]
    h = y0 - pv["do_koreckuu_y"]
    t_pad = math.sqrt(2.0 * h / 9.81)
    n = int(cf["segmentu"])
    w = u["sirka"] / 2.0
    vs, fs, uv = [], [], []
    for i in range(n + 1):
        t = t_pad * i / n
        s = cf["rychlost_m_s"] * t
        px, py, pz = mlyn_svet(x0 + sx * s, y0 - 0.5 * 9.81 * t * t, z0 + sz * s)
        vs += [(px - sz * w, py, pz + sx * w), (px + sz * w, py, pz - sx * w)]
    for i in range(n):
        fs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
        uv.append([(0.0, i / n), (1.0, i / n), (1.0, (i + 1) / n), (0.0, (i + 1) / n)])
    Q = Part("Mlyn_pad_vody")
    Q.mesh(vs, fs, "voda_potok", uvs=uv)
    o = Q.commit(coll)
    _toky_proud(o, [(sx, sz)] * n)
    return o


def _bunky_u_vody(rect, inner, step):
    """Bunky pasma (indexy) do toky_tvar pas_jemny_m od vody malych toku a generovanych rybniku: koryto 1-1,5 m
    siroke v siti po 5 m (2 m ve vsi) neexistuje, hladina pak lezi zahrabana v trave (Misa 28. 10.). Tyto bunky
    nahradi jemny teren po 1 m (_teren_u_vody) - stejne pravidlo jako pas Bystrice (potok pas_jemny_m)."""
    pas = _TT["pas_jemny_m"]
    nx = int(round((rect[1] - rect[0]) / step))
    nz = int(round((rect[3] - rect[2]) / step))
    out = set()

    def pridej(x, z, r):
        for i in range(int((x - r - rect[0]) // step), int((x + r - rect[0]) // step) + 1):
            for k in range(int((z - r - rect[2]) // step), int((z + r - rect[2]) // step) + 1):
                if 0 <= i < nx and 0 <= k < nz:
                    cx, cz = rect[0] + (i + 0.5) * step, rect[2] + (k + 0.5) * step
                    if not any(x0 < cx < x1 and z0 < cz < z1 for x0, x1, z0, z1 in inner):
                        out.add((i, k))
    for t in TOKY:
        r = t.w / 2.0 + pas
        for (ax, az), (bx, bz) in zip(t.osa[:-1], t.osa[1:]):
            L = math.hypot(bx - ax, bz - az)
            n = max(1, int(L / (step * 0.5)))
            for j in range(n + 1):
                pridej(ax + (bx - ax) * j / n, az + (bz - az) * j / n, r)
    for ryb in RYBNIKY:
        if "polomer_m" in ryb:
            cx, cz = ryb["stred"]
            r = ryb["polomer_m"] + pas
            a = 0.0
            while a < 2 * math.pi:
                for f in (0.0, 0.5, 1.0):
                    pridej(cx + math.cos(a) * r * f, cz + math.sin(a) * r * f, step)
                a += step * 0.5 / r
    return out


def _teren_u_vody(coll, land_fn, jemne):
    """Jemny teren (1 m) v bunkach _bunky_u_vody: koryto, breh a dno malych toku a rybniku. Vrchol na hrane bunky
    sousedici s hrubou bunkou ma vysku hrube hrany (linearne mezi rohy) - sit bez skulin a bez lemu."""
    from lib import Part
    verts, faces, attrs = [], [], []
    idx = {}
    for name, (rect, step, jem) in jemne.items():
        n = int(round(step / _TT["jemny_krok_m"]))

        def bod(i, k, a, b, rect=rect, step=step, jem=jem, n=n):
            x, z = rect[0] + i * step + a, rect[2] + k * step + b
            key = (round(x * 8), round(z * 8))
            if key in idx:
                return idx[key]
            y = None
            # hrana bunky k hrube sousedni bunce: vyska jako v hrube siti
            if 0 < b < step and a in (0.0, step):
                ii = i - 1 if a == 0.0 else i + 1
                if (ii, k) not in jem:
                    z0, z1 = rect[2] + k * step, rect[2] + (k + 1) * step
                    y = land_fn(x, z0) + (land_fn(x, z1) - land_fn(x, z0)) * b / step
            if 0 < a < step and b in (0.0, step):
                kk = k - 1 if b == 0.0 else k + 1
                if (i, kk) not in jem:
                    x0, x1 = rect[0] + i * step, rect[0] + (i + 1) * step
                    y = land_fn(x0, z) + (land_fn(x1, z) - land_fn(x0, z)) * a / step
            if y is None:
                y = land_fn(x, z)
            idx[key] = len(verts)
            verts.append((x, y, z))
            attrs.append(ground_attrs(x, z))
            return idx[key]
        d = step / n
        for (i, k) in sorted(jem):
            for u in range(n):
                for v in range(n):
                    a0, a1, b0, b1 = u * d, (u + 1) * d, v * d, (v + 1) * d
                    faces.append((bod(i, k, a0, b0), bod(i, k, a0, b1), bod(i, k, a1, b1), bod(i, k, a1, b0)))
    if not faces:
        return None
    P = Part("Teren_toky", smooth=True)
    P.mesh(verts, faces, "zem")
    o = P.commit(coll)
    _set_attrs(o, attrs)
    print("teren u malych toku a rybniku: %d bodu, %d bunek" % (len(verts), sum(len(j[2]) for j in jemne.values())))
    return o


REKA_PAS = _VODA_J["potok"]["pas_jemny_m"]          # polosirka jemneho pasu terenu podel potoka (voda.json)


_REKA_MIMO = []          # obdelniky s vlastnim jemnym terenem (ves, most) - tam pas reky neni


def _osa(x, z):
    """(bod osy, jednotkovy smer toku po proudu dle sgn=1, perej) nejblize k (x, z)."""
    r = _REKA_LINE.near(x, z)
    if r is None:
        return None
    j = min(int(r[3]), len(REKA) - 2)
    ax, az = REKA[j]
    bx, bz = REKA[j + 1]
    L = math.hypot(bx - ax, bz - az) or 1.0
    return r, (bx - ax) / L, (bz - az) / L


def _reka_kameny(coll, land_fn, wl, sgn):
    """Kameny v korytu a na brezich: balvany v tuni ridce, v brodu hodne kamenu (voda je obtéká),
    na brezich vymyte kaminky a kameny na care vody. Vraci [(x, z, polomer, vycniva_nad_hladinu)] pro penu."""
    import nove
    from lib import Part
    R = random.Random(77)
    Pk = Part("Reka_kameny", bevel=0.0)
    br = bridge()
    out = []
    cum = 0.0
    n = 0
    for j in range(len(REKA) - 1):
        ax, az = REKA[j]
        bx, bz = REKA[j + 1]
        L = math.hypot(bx - ax, bz - az)
        if L < 1e-3:
            continue
        tx, tz = (bx - ax) / L, (bz - az) / L
        nx, nz = -tz, tx
        t = 0.0
        while t < L:
            x0, z0 = ax + tx * t, az + tz * t
            t += 0.7
            if not _reka_pokryva(x0, z0):
                continue
            if br and math.hypot(x0 - br[0], z0 - br[1]) < 5.0:
                continue
            pj = perej(x0, z0)
            wf = 1.0 + 0.75 * pj
            w = wl[j] * (1 - t / L) + wl[j + 1] * (t / L)

            def put(pid, o, size, sink, kol):
                x, z = x0 + nx * o + tx * R.uniform(-0.35, 0.35), z0 + nz * o + tz * R.uniform(-0.35, 0.35)
                y = land_fn(x, z)
                nove.misto(pid, x, y, z, size / nove.DIM[pid][0], R.uniform(0, 2 * math.pi), Pk if kol else None, sink=sink)
                vys = y + nove.DIM[pid][1] * size / nove.DIM[pid][0] * (1 - sink)
                return x, z, y, vys
            # kameny v korytu: v tuni ridke balvany, v brodu hodne kamenu ruzne velkych
            if R.random() < 0.09 + 0.6 * pj:
                big = R.random() < 0.12
                size = R.uniform(0.9, 1.7) if big else R.uniform(0.35, 0.9) * (1.0 + 0.3 * pj)
                pid = R.choice(nove.BALVANY_POLE if big else nove.KAMENY_POLE)
                x, z, y, vys = put(pid, R.uniform(-1.9, 1.9) * wf, size, R.uniform(0.12, 0.28), size > 0.6)
                if vys > w - 0.15:
                    out.append((x, z, size * 0.5, vys > w + 0.02))
                n += 1
            # dno brodu: kaminky
            for _ in range(int(pj * 4)):
                put(R.choice(nove.KAMINKY), R.uniform(-2.2, 2.2) * wf, R.uniform(0.12, 0.35), 0.35, False)
                n += 1
            # brehy: vymyte kaminky a kameny na care vody (obe strany)
            for sg in (-1, 1):
                for _ in range(2):
                    put(R.choice(nove.KAMINKY), sg * R.uniform(1.4, 3.0) * wf, R.uniform(0.1, 0.3), 0.35, False)
                    n += 1
                if R.random() < 0.3:
                    put(R.choice(nove.KAMENY_POLE), sg * R.uniform(1.6, 2.6) * wf, R.uniform(0.3, 0.7), 0.4, False)
                    n += 1
        cum += L
    Pk.commit(coll)
    print("potok: %d kamenu, %d obtekanych" % (n, len(out)))
    return out


def _reka_pena(o, kam, sgn, verts):
    """Barva vrcholu hladiny potoka: R = pena kolem a za kameny (obtekani), G = perej (rychla, cerena voda).
    verts = herni souradnice vrcholu (poradi stejne jako v siti, Part je nepreusporadava)."""
    me = o.data
    grid = {}
    for s_ in kam:
        grid.setdefault((int(s_[0] // 4), int(s_[1] // 4)), []).append(s_)
    per_v = [_pena_bod(x, z, grid, sgn) for x, _, z in verts]
    # B, A = smer toku (po proudu) v rovine xz: hra posouva vlnky po nem (mapa proudeni, bez svu v ohybech)
    flow = []
    for x, _, z in verts:
        a = _osa(x, z)
        if a is None:
            flow.append((0.5, 0.5))
        else:
            flow.append((0.5 + 0.5 * a[1] * sgn, 0.5 + 0.5 * a[2] * sgn))
    # vyhladit smer (sousedni vrcholy ve mrizce): v ohybu se meni plynule
    pos = {(round(x * 2), round(z * 2)): i for i, (x, _, z) in enumerate(verts)}
    hf = []
    for i, (x, _, z) in enumerate(verts):
        kx, kz = round(x * 2), round(z * 2)
        sb = sa = 0.0
        n = 0
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                j = pos.get((kx + dx, kz + dz))
                if j is not None:
                    sb += flow[j][0]
                    sa += flow[j][1]
                    n += 1
        hf.append((sb / n, sa / n))
    col = me.color_attributes.new("Pena", "BYTE_COLOR", "CORNER")
    vals = [0.0] * (len(me.loops) * 4)
    for li, lp in enumerate(me.loops):
        f, pj = per_v[lp.vertex_index]
        fb, fa = hf[lp.vertex_index]
        vals[li * 4:li * 4 + 4] = [f, pj, fb, fa]
    col.data.foreach_set("color", vals)
    me.color_attributes.active_color = col
    me.color_attributes.render_color_index = me.color_attributes.active_color_index


def _pena_bod(x, z, grid, sgn):
    a = _osa(x, z)
    if a is None:
        return 0.0, 0.0
    r, fx, fz = a
    fx, fz = fx * sgn, fz * sgn
    pj = perej(r[1], r[2])
    f = 0.0
    gx, gz = int(x // 4), int(z // 4)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for sx, sz, rad, ven in grid.get((gx + dx, gz + dz), ()):
                ddx, ddz = x - sx, z - sz
                d = math.hypot(ddx, ddz)
                kruh = math.exp(-((d - rad) / 0.3) ** 2) if d > rad * 0.6 else 1.0
                po = ddx * fx + ddz * fz                     # po proudu za kamenem
                bok = abs(ddx * fz - ddz * fx)
                ocas = math.exp(-(bok / (rad * 1.1 + 0.15)) ** 2) * math.exp(-po / 3.0) if po > 0 else 0.0
                f = max(f, kruh * (1.0 if ven else 0.6) + ocas * (0.9 if ven else 0.5))
    return min(1.0, f), pj


def _reka_pokryva(cx, cz):
    """Ma bod osy reky (cx, cz) radu jemneho pasu? (stejne pravidlo pro pas i pro vyrez hrubeho terenu)"""
    return ACT[0] + 6 < cx < ACT[1] - 6 and ACT[2] + 6 < cz < ACT[3] - 6 and \
        not any(x0 - 4 < cx < x1 + 4 and z0 - 4 < cz < z1 + 4 for x0, x1, z0, z1 in _REKA_MIMO)


def _v_pasu_reky(x, z):
    """Ctverec hrubeho terenu vynechat jen tam, kde ho jisto prekryva pas reky (jinak by vznikla dira)."""
    r = _REKA_LINE.near(x, z)
    return r is not None and r[0] < REKA_PAS - 6.0 and _reka_pokryva(r[1], r[2])


def _teren_reka(coll, land_fn, mimo):
    """Jemny teren podel cele reky (1 m napric, 1.5 m podel): koryto a brehy bez ostrych trojuhelniku hrubeho
    pasma; po okrajich lem dolu, ktery zakryje styk s pasmem 5 m."""
    from lib import Part
    pts = []
    for (ax, az), (bx, bz) in zip(REKA[:-1], REKA[1:]):
        L = math.hypot(bx - ax, bz - az)
        n = max(1, int(L / 1.5))
        for i in range(n):
            pts.append((ax + (bx - ax) * i / n, az + (bz - az) * i / n))
    pts.append(REKA[-1])
    cols = int(REKA_PAS * 2) + 1
    verts, faces, attrs = [], [], []
    rows = []
    for j, (x, z) in enumerate(pts):
        a = pts[max(0, j - 2)]
        b = pts[min(len(pts) - 1, j + 2)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / tl, tx / tl
        inside = _reka_pokryva(x, z)
        if not inside:
            rows.append(None)
            continue
        row = []
        for c in range(cols):
            o = -REKA_PAS + c * 1.0
            px, pz = x + nx * o, z + nz * o
            row.append(len(verts))
            verts.append((px, land_fn(px, pz), pz))
            attrs.append(ground_attrs(px, pz))
        # lem dolu na obou okrajich
        for c in (0, cols - 1):
            px, py, pz = verts[row[c]]
            row.append(len(verts))
            verts.append((px, py - 6.0, pz))
            attrs.append(attrs[row[c]])
        rows.append(row)
    for j in range(len(rows) - 1):
        r0, r1 = rows[j], rows[j + 1]
        if r0 is None or r1 is None:
            continue
        for c in range(cols - 1):
            faces.append((r0[c], r0[c + 1], r1[c + 1], r1[c]))
        faces.append((r0[cols], r0[0], r1[0], r1[cols]))                  # lem vlevo
        faces.append((r0[cols - 1], r0[cols + 1], r1[cols + 1], r1[cols - 1]))  # lem vpravo
    P = Part("Teren_reka", smooth=True)
    P.mesh(verts, faces, "zem")
    o = P.commit(coll)
    _set_attrs(o, attrs)
    print("teren podel reky: %d bodu" % len(verts))
    return o


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


_PLAN = []


def skaly_plan():
    """Rozmisteni skalnich vezi (bez terenu): [(model, x, z, meritko, yaw)] a zony [(x, z, polomer)].
    Pocita se predem, aby teren mohl kolem vezi vytvorit svahy (skaly vyrustaji z kopce)."""
    if _PLAN:
        return _PLAN[0]
    R = random.Random(1394)
    spots = []
    segs = list(zip(HREBEN[:-1], HREBEN[1:]))
    for (ax, az), (bx, bz) in segs:
        d = math.hypot(bx - ax, bz - az)
        k = 0.0
        while k < d:
            t = k / d
            spots.append((ax + (bx - ax) * t, az + (bz - az) * t, -(bz - az) / d, (bx - ax) / d))
            k += R.uniform(28.0, 55.0)
    import nove
    out = []
    zony_out = []
    # skalni mesta jako Adrspach / Prachov: piskovcova plotna rozpukana dvema soustavami puklin skoro v pravem
    # uhlu -> bludiste vezi oddelenych uzkymi roklemi (3-6 m), uprostred nejvyssi, k okrajum nizsi, na okraji
    # osamele jehly; tu a tam mytinka nebo sirsi soutesku. Kazde bludiste ma vlastni smer puklin.
    zony = []
    for x, z, nx, nz in spots:
        if 250 <= z <= 880 and (not zony or math.hypot(x - zony[-1][0], z - zony[-1][1]) > 95.0):
            zony.append((x + nx * R.uniform(-15, 15), z + nz * R.uniform(-15, 15), nx, nz))
    for x, z, nx, nz in zony:
        zony_out.append(None)
        uhel = math.atan2(nz, nx) + R.uniform(-0.5, 0.5)            # smer hlavni pukliny
        ux, uz = math.cos(uhel), math.sin(uhel)
        vx, vz = -uz, ux
        rz = R.uniform(48.0, 70.0)                                   # polomer bludiste
        zony_out[-1] = (x, z, rz)
        cu, cv = R.uniform(10.0, 13.0), R.uniform(8.5, 11.5)         # rozestup puklin (bloky)
        su = R.uniform(-0.12, 0.12)                                  # pukliny mirne kose
        n_u, n_v = int(rz / cu) + 1, int(rz / cv) + 1
        soutesk = R.uniform(-rz * 0.4, rz * 0.4)                     # sirsi souteska napric bludistem
        for i in range(-n_u, n_u + 1):
            for j in range(-n_v, n_v + 1):
                lu = i * cu + R.gauss(0.0, 0.9) + j * cv * su
                lv = j * cv + R.gauss(0.0, 0.9)
                xx, zz = x + ux * lu + vx * lv, z + uz * lu + vz * lv
                dk = math.hypot(lu, lv) / rz + 0.25 * perlin(xx / 30.0 + 5.0, zz / 30.0)
                if dk > 1.0:
                    # za okrajem jen obcas osamela jehla
                    if dk < 1.2 and R.random() < 0.03 and not stavba_near(xx, zz, 20.0):
                        out.append(("skala_jehla", xx, zz, R.uniform(0.6, 1.0), uhel + R.uniform(-0.3, 0.3)))
                    continue
                if abs(lv - soutesk) < 3.0 or R.random() < 0.05:
                    continue                                         # souteska / mytinka
                if stavba_near(xx, zz, 14.0):
                    continue                                         # misto zriceniny hradku nechat volne
                rn = road_near(xx, zz)
                if rn and rn[0] < rn[3] + 8.0:
                    continue
                vys = 1.0 - 0.55 * smooth(0.25, 1.0, dk)            # uprostred vysoke, k okraji nizsi
                if dk < 0.5 and R.random() < 0.35:
                    pid = R.choice(["skala_masiv_2veze", "skala_masiv_3veze"])
                else:
                    pid = R.choice(["skala_vez", "skala_hlava", "skala_naklonena", "skala_vez", "skala_jehla", "skala_hlava"])
                w0 = nove.DIM[pid][0]
                # sirka bloku = rozestup puklin minus rokle (3-6 m); vyska podle polohy v bludisti
                k = min((min(cu, cv) - R.uniform(1.5, 3.5)) / w0, R.uniform(0.9, 1.6) * vys)
                k = max(k, 0.45)
                yaw = uhel + (R.choice([0.0, math.pi / 2]) if pid != "skala_naklonena" else R.uniform(0, 6.28)) + R.uniform(-0.12, 0.12)
                if dk < 0.9 and R.random() < 0.6:
                    # skalni masiv: 2-4 veze tesne vedle sebe / do sebe vnorene podel pukliny, kazda jinak vysoka
                    # -> delsi blok se zubatym hrebenem, jen melke pukliny mezi vezemi
                    n_m = R.randint(2, 4)
                    krok = w0 * k * R.uniform(0.4, 0.6)
                    smer = R.choice([(ux, uz), (vx, vz)])
                    for m_ in range(n_m):
                        o = (m_ - (n_m - 1) / 2) * krok
                        mx, mz = xx + smer[0] * o + R.gauss(0.0, 0.4), zz + smer[1] * o + R.gauss(0.0, 0.4)
                        pm = R.choice(["skala_vez", "skala_hlava", "skala_masiv_2veze", "skala_vez", "skala_masiv_3veze"])
                        km = k * w0 / nove.DIM[pm][0] * R.uniform(0.85, 1.15)
                        out.append((pm, mx, mz, max(km, 0.45), yaw + R.choice([0.0, math.pi]) + R.uniform(-0.1, 0.1)))
                    continue
                out.append((pid, xx, zz, k, yaw))
    grid = {}
    for pid, x, z, k, yaw in out:
        import nove
        r = max(nove.DIM[pid][0], nove.DIM[pid][2]) * k * 0.5
        grid.setdefault((int(x // 24), int(z // 24)), []).append((x, z, r, nove.DIM[pid][1] * k))
    _PLAN.append((out, [zz for zz in zony_out if zz], grid))
    return _PLAN[0]


def skaly_podstava(x, z):
    """Zvednuti terenu ve skalnim meste: cele bludiste na sirokem kopci a kolem kazde veze sutovy svah
    (pata veze zasypana piskem a sutí), rokle mezi vezemi zustanou zahloubene."""
    if not (-320.0 < x < -40.0 and 200.0 < z < 960.0):
        return 0.0
    out, zony, grid = skaly_plan()
    h = 0.0
    for zx, zz, rz in zony:
        dd = math.hypot(x - zx, z - zz)
        if dd < rz * 1.6:
            h = max(h, 9.0 * math.exp(-(dd / (rz * 0.85)) ** 2))
    gx, gz = int(x // 24), int(z // 24)
    best = 0.0
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for sx, sz, r, vy in grid.get((gx + dx, gz + dz), ()):
                d = math.hypot(x - sx, z - sz)
                if d < r + 12.0:
                    # suťový kužel u paty: vysky az 1/5 veze, svah do 10 m od steny
                    best = max(best, min(6.0, vy * 0.2) * (1.0 - smooth(r * 0.5, r + 10.0, d)))
    h += best
    if h <= 0.0:
        return 0.0
    # u staveb (hostinec) a cest kopec skal plynule mizi: stavby a cesty zustanou na puvodnim terenu
    for _, cx, cz, _, r in STAVBY:
        h *= smooth(r + 6.0, r + 35.0, math.hypot(x - cx, z - cz))
    rn = road_near(x, z)
    if rn:
        h *= smooth(rn[3] + 2.0, rn[3] + 18.0, rn[0])
    return h


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
    import nove
    out, zony_p, _g = skaly_plan()
    Rb = random.Random(5150)
    for pid, xx, zz, k, yaw in out:
        y0 = land_fn(xx, zz)
        nove.skala(pid, xx, y0, zz, k, yaw, P)
        towers += 1
        # borovice na vrcholu (v modelu skaly byla za 5750 troj.; samostatna ma LOD a dal nez 120 m se nekresli)
        if pid != "skala_naklonena" and Rb.random() < 0.65:
            # na skutecny vrchol kamene (DIM obsahuje i puvodni borovici z modelu: visela by ~3 m nad skalou)
            vh, vx, vy = nove.SKALY_VRCHOL[pid]
            from mathutils import Matrix, Vector
            o = Matrix.Rotation(yaw, 3, "Y") @ Vector((vx * k, 0.0, -vy * k))
            top = y0 + (vh - nove.SKALY_POD) * k - 0.5 * k
            ROCK_PLANTS.append(("borovice", xx + o.x, zz + o.z, Rb.uniform(2.5, 6.0), top))
    zony = [(x, z, 0.0, 0.0) for x, z, rz in zony_p]
    # zarostle rokle a paty skal: kapradi, mech, borůvčí a trava, keře, mlade brizy a smrcky (vlhko ve stinu)
    Rv = random.Random(4411)
    for x, z, rz in zony_p:
        for _ in range(int(rz * rz * 0.22)):
            a_ = Rv.uniform(0, 2 * math.pi)
            d_ = rz * 1.15 * math.sqrt(Rv.random())
            px, pz = x + math.cos(a_) * d_, z + math.sin(a_) * d_
            if v_skale(px, pz, 0.3) or stavba_near(px, pz, 4.0):
                continue
            c = Rv.random()
            if c < 0.28:
                ROCK_PLANTS.append((Rv.choice(["kapradi_1", "kapradi_2", "kapradi_3", "fern_02"]), px, pz, Rv.uniform(0.7, 1.5), None))
            elif c < 0.45:
                ROCK_PLANTS.append((Rv.choice(["mech_1", "mech_2", "mech_3", "moss_01", "rock_moss_set_01"]), px, pz, Rv.uniform(0.04, 0.1), None))      # mech: vyska modelu 3-10 cm (0.6-1.6 m = plachty 30 m)
            elif c < 0.62:
                ROCK_PLANTS.append((Rv.choice(["divoka_trava", "grass_medium_02", "grass_medium_01"]), px, pz, Rv.uniform(0.5, 1.0), None))
            elif c < 0.8:
                ROCK_PLANTS.append((Rv.choice(["shrub_02", "sipek", "shrub_02"]), px, pz, Rv.uniform(0.7, 1.8), None))
            elif c < 0.86:
                ROCK_PLANTS.append(("briza", px, pz, Rv.uniform(2.0, 7.0), None))
            else:
                # na piskovci rostou hlavne borovice (pokroucene, ruzne vysoke)
                ROCK_PLANTS.append(("borovice", px, pz, Rv.uniform(3.0, 12.0), None))
    for x, z, nx, nz in zony:
        gx, gz = x, z
        import nove
        # balvany a kameny z pisku u paty skal (modely z druheho chatu), sem tam spadly velky blok
        for _ in range(R.randint(30, 50)):
            xx, zz = gx + R.gauss(0.0, 30.0), gz + R.gauss(0.0, 30.0)
            sz = R.uniform(0.8, 3.5)
            pid = R.choice(nove.KAMENY_PISKOVEC) if sz < 1.4 else R.choice(nove.BALVANY_PISKOVEC)
            if stavba_near(xx, zz, 3.0):
                continue
            nove.misto(pid, xx, land_fn(xx, zz), zz, sz / nove.DIM[pid][0], R.uniform(0, 2 * math.pi), P, sink=0.2)
        for _ in range(R.randint(6, 12)):
            xx, zz = gx + R.gauss(0.0, 28.0), gz + R.gauss(0.0, 28.0)
            if stavba_near(xx, zz, 3.0):
                continue
            nove.misto("balvan_piskovec_3", xx, land_fn(xx, zz), zz, R.uniform(1.8, 3.2), R.uniform(0, 2 * math.pi), P, sink=0.25)
        for _ in range(R.randint(40, 70)):
            xx, zz = gx + R.gauss(0.0, 30.0), gz + R.gauss(0.0, 30.0)
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


_SKALY_MRIZ = {}


def v_skale(x, z, okraj=1.0):
    """Lezi bod v pudorysu skalni veze (stromy a rostliny tam nerostou)?"""
    import nove
    if not _SKALY_MRIZ:
        _SKALY_MRIZ[None] = True
        for pid, sx, sy, sz, k, yaw in nove.MISTA:
            if pid.startswith("skala_"):
                r = max(nove.DIM[pid][0], nove.DIM[pid][2]) * k * 0.5
                _SKALY_MRIZ.setdefault((int(sx // 16), int(sz // 16)), []).append((sx, sz, r))
    gx, gz = int(x // 16), int(z // 16)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for sx, sz, r in _SKALY_MRIZ.get((gx + dx, gz + dz), ()):
                if math.hypot(x - sx, z - sz) < r + okraj:
                    return True
    return False


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
    # brehy potoka: kere, kopřivy a vysoka trava; u vody hustsi
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
            # smutecni vrba pryc (Misa 27. 10. „hnusne vrby“; Salix babylonica je novoveka) - stromy na brehu
            # Bystrice jsou olse a vrby hlavate z veg.py
            if c < 0.32:
                out.append((R.choice(["shrub_02", "sipek"]), xx, zz, R.uniform(1.0, 2.6), 0.0))
            elif c < 0.55:
                out.append(("nettle_plant", xx, zz, R.uniform(0.4, 0.75), 0.0))
            else:
                out.append(("divoka_trava", xx, zz, R.uniform(0.6, 1.2), 0.12))
    return out
