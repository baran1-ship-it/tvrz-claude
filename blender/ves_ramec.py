"""Ves v novem ramci pro Blender - jediny zdroj pravdy (Misa 3. 11. „uz jsme resili, aby se Godot nebil s blenderem,
naprav to“; soupis docs/rozpracovane/rozpory_blender_godot.md). Prepis scripts/ves_oblouk.gd do Pythonu: usedlosti
(stary -> novy ramec), osa ulice (plan + klikani ke stitum), pulsirka, pas hliny a drnu (ulice_pas).
Blender z toho stavi ves rovnou na novem miste (lokace.json ves.blender_novy_ramec), hra uz nic nepresouva.
Cisla jen z pravidla/svet/lokace.json ves (usedlosti, ulice, prechod_terenu_m) a pravidla_sveta.json pasma.cesta.ulice_vsi."""
import json
import math
import os

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
_LOK = json.load(open(os.path.join(_ROOT, "pravidla", "svet", "lokace.json"), encoding="utf-8"))["ves"]
_PAS = json.load(open(os.path.join(_ROOT, "pravidla", "pravidla_sveta.json"), encoding="utf-8"))["pasma"]["cesta"]["ulice_vsi"]


def zapnuto():
    # TVRZ_VES_BLENDER=1: zkouska bez zmeny zaznamu (test smyslu, export nanecisto)
    return bool(_LOK.get("blender_novy_ramec", False)) or os.environ.get("TVRZ_VES_BLENDER") == "1"


def _smooth(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0) if b != a else (1.0 if x >= b else 0.0)
    return t * t * (3.0 - 2.0 * t)


U = []
for _e in _LOK["usedlosti"]:
    _oy, _ny = float(_e["stary_yaw"]), float(_e["novy_yaw"])
    _L, _W = float(_e["L"]), float(_e["W"])
    U.append({"k": int(_e["k"]), "oc": tuple(_e["stary_stred"]), "oau": (math.cos(_oy), math.sin(_oy)),
              "oav": (-math.sin(_oy), math.cos(_oy)), "hu0": -(_L / 2.0 + 14.0), "hu1": _L / 2.0 + 2.5,
              "hv0": -_W / 2.0 - 7.2, "hv1": _W / 2.0 + 10.5, "nc": tuple(_e["novy_stred"]),
              "nau": (math.cos(_ny), math.sin(_ny)), "nav": (-math.sin(_ny), math.cos(_ny)), "dyaw": _ny - _oy})


def _ab(e, x, z, novy):
    c = e["nc"] if novy else e["oc"]
    a = e["nau"] if novy else e["oau"]
    b = e["nav"] if novy else e["oav"]
    dx, dz = x - c[0], z - c[1]
    return dx * a[0] + dz * a[1], dx * b[0] + dz * b[1]


def _venku(e, a, b):
    return max(max(e["hu0"] - a, a - e["hu1"]), max(e["hv0"] - b, b - e["hv1"]))


def stara(x, z, okraj=0.0):
    """Index usedlosti, do jejiz stareho pudorysu bod patri (-1 zadna)."""
    for i, e in enumerate(U):
        if _venku(e, *_ab(e, x, z, False)) < okraj:
            return i
    return -1


def podle_stredu(x, z):
    """Usedlost podle stareho stredu chalupy (vesnice.layout h["p"])."""
    for i, e in enumerate(U):
        if math.hypot(x - e["oc"][0], z - e["oc"][1]) < 0.5:
            return i
    return -1


def nova(x, z, okraj=0.0):
    best, bd = -1, 1e9
    for i, e in enumerate(U):
        d = _venku(e, *_ab(e, x, z, True))
        if d < okraj and d < bd:
            best, bd = i, d
    return best, bd


def presun2(i, x, z):
    """Bod stareho ramce usedlosti i -> novy ramec (xz)."""
    e = U[i]
    a, b = _ab(e, x, z, False)
    return e["nc"][0] + e["nau"][0] * a + e["nav"][0] * b, e["nc"][1] + e["nau"][1] * a + e["nav"][1] * b


_OSA = None


def osa_ulice():
    """Body osy ulice po 1 m od vjezdu (presne jako ves_oblouk.gd osa_ulice)."""
    global _OSA
    if _OSA is not None:
        return _OSA
    ul = _LOK["ulice"]
    p = [float(ul["vjezd"][0]), float(ul["vjezd"][1])]
    zak = [tuple(p)]
    h = float(ul["smer"])
    turn = math.radians(float(ul["turn_st"]))
    rb = float(ul["R"])
    for _ in range(int(ul["L1"])):
        p = [p[0] + math.cos(h), p[1] + math.sin(h)]
        zak.append(tuple(p))
    n = int(abs(turn) * rb)
    for _ in range(n):
        h += turn / n
        s = abs(turn) * rb / n
        p = [p[0] + math.cos(h) * s, p[1] + math.sin(h) * s]
        zak.append(tuple(p))
    for _ in range(int(ul["L2"])):
        p = [p[0] + math.cos(h), p[1] + math.sin(h)]
        zak.append(tuple(p))
    m = len(zak)
    nrm = []
    for i in range(m):
        a, b = zak[min(i + 1, m - 1)], zak[max(i - 1, 0)]
        tx, tz = a[0] - b[0], a[1] - b[1]
        ln = math.hypot(tx, tz) or 1.0
        nrm.append((-tz / ln, tx / ln))
    domy = []
    for e in U:
        c = e["nc"]
        bi = min(range(m), key=lambda i: (c[0] - zak[i][0]) ** 2 + (c[1] - zak[i][1]) ** 2)
        lat = (c[0] - zak[bi][0]) * nrm[bi][0] + (c[1] - zak[bi][1]) * nrm[bi][1]
        domy.append((bi, math.copysign(1.0, lat) if lat != 0 else 0.0, abs(lat) - (e["hu1"] - 2.5)))
    ks = ul["ke_stitu"]
    off = []
    for i in range(m):
        o = 0.0
        for vl in ul["vlny"]:
            o += float(vl[0]) * math.sin(i / float(vl[1]) + float(vl[2]))
        for bi, sd, dd in domy:
            o += sd * min(max((dd - float(ks["od_m"])) * float(ks["nasobek"]), float(ks["min"])), float(ks["max"])) \
                * math.exp(-((i - bi) / float(ks["dosah"])) ** 2)
        off.append(o * _smooth(0.0, float(ul["napojeni_vjezdu_m"]), float(i)))
    for _ in range(6):
        for i in range(m):
            if nova(zak[i][0] + nrm[i][0] * off[i], zak[i][1] + nrm[i][1] * off[i], float(ul["od_pudorysu_m"]))[0] >= 0:
                off[i] *= 0.6
        o2 = list(off)
        for i in range(2, m - 2):
            o2[i] = (off[i - 2] + off[i - 1] + off[i] + off[i + 1] + off[i + 2]) / 5.0
        off = o2
    _OSA = [(zak[i][0] + nrm[i][0] * off[i], zak[i][1] + nrm[i][1] * off[i]) for i in range(m)]
    return _OSA


def pulsirka(f):
    ps = _LOK["ulice"]["pulsirka"]
    w = float(ps["zaklad"]) + float(ps["vjezd"]) * math.exp(-(f / float(ps["vjezd_delka"])) ** 2)
    for vl in ps["vlny"]:
        w += float(vl[0]) * math.sin(f * float(vl[1]) + float(vl[2]))
    return min(max(w, float(ps["min"])), float(ps["max"]))


_MRIZ = None


def _blizko(x, z):
    """(index nejblizsiho bodu osy, vzdalenost) - mrizka 4 m jako ves_oblouk.gd _yc_mriz."""
    global _MRIZ
    osa = osa_ulice()
    if _MRIZ is None:
        _MRIZ = {}
        for i, q in enumerate(osa):
            cx, cz = math.floor(q[0] / 4.0), math.floor(q[1] / 4.0)
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    _MRIZ.setdefault((cx + dx, cz + dz), []).append(i)
    lst = _MRIZ.get((math.floor(x / 4.0), math.floor(z / 4.0)), [])
    if not lst:
        return -1, 1e9
    bi = min(lst, key=lambda i: (x - osa[i][0]) ** 2 + (z - osa[i][1]) ** 2)
    return bi, math.hypot(x - osa[bi][0], z - osa[bi][1])


def od_kraje_hliny(x, z):
    """Vzdalenost od kraje hliny ulice (< 0 na hline), 1e9 daleko."""
    bi, d = _blizko(x, z)
    if bi < 0:
        return 1e9
    return d - pulsirka(bi / max(len(osa_ulice()) - 1, 1))


def ulice_pas(x, z):
    """(hlina 0..1 pro barvu, nasobek masky trsu 0..1) - totez pravidlo jako ves_oblouk.gd ulice_pas."""
    e = od_kraje_hliny(x, z)
    if e > 1e8:
        return 0.0, 1.0
    return 1.0 - _smooth(0.0, float(_PAS["drn_m"]), e), _smooth(0.0, float(_PAS["trsy_od_m"]), e)


_YC = None


def ulice_vysky(landfn):
    """Vyska osy ulice: teren v bodech osy (bez srovnani ulice) vyhlazeny podel +-6 bodu (ves_oblouk.gd ulice_vysky)."""
    global _YC
    if _YC is None:
        osa = osa_ulice()
        h = [landfn(q[0], q[1]) for q in osa]
        _YC = []
        for i in range(len(h)):
            a, b = max(i - 6, 0), min(i + 7, len(h))
            _YC.append(sum(h[a:b]) / (b - a))
    return _YC


def uprav_y(x, z, y, landfn):
    """Ulice napric rovna (ves_oblouk.gd uprav_y, pasma.cesta.ulice_vsi pricny_podil, rovne_m, prechod_m)."""
    bi, d = _blizko(x, z)
    if bi < 0:
        return y
    yc = ulice_vysky(landfn)
    hw = pulsirka(bi / max(len(osa_ulice()) - 1, 1))
    r0 = hw + float(_PAS["rovne_m"])
    w = 1.0 - _smooth(r0, r0 + float(_PAS["prechod_m"]), d)
    if w <= 0.0:
        return y
    cil = yc[bi] + (y - yc[bi]) * float(_PAS["pricny_podil"])
    return y + (cil - y) * w
