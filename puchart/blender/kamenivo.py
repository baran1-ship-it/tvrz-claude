"""Kámen jako kámen zblízka (Míša 18. 11., pravidlo: „Kámen musí být kámen a dřevo dřevo – ne tapeta: zblízka skutečný tvar
v geometrii, z dálky zjednodušená síť s texturou (LOD)“; plán F2 v docs/rozpracovane/plan_z_reserse_17_11.md, předloha
docs/reference/zdivo_kcd_18_11/ 07, 08, 01, 11; Míšin snímek misa_cimburi_kostky.jpg: „vezmu kostku a potáhnu ji kamennou tapetou“).

Společné pro oba hrady (puchart_hrad.py i hrady.py volají tytéž funkce):
  stinka()   zub cimbuří složený z 2–4 řad nepravidelných kamenů se spárou a otlučenými hranami + krycí deska navrchu
  kryti()    koruna zídky / předprseně v prolukách cimbuří: nepravidelné krycí kameny (silueta koruny není rovná čára)
  patka()    patka zdi: řada větších kamenů u terénu, vystupují o pár cm
  narozi()   nárožní kvádry střídavě na vazbu (odložené – staví se až v dokonci(), kdy jsou známé všechny zdi: na nároží, ke
             kterému přiléhá jiná zeď, se nekladou – trčely ze styku zdí jako svislý tmavý šev, Míša 20. 11. misa_20_11_svy.jpg, H6)
Kameny LOD0 jsou v samostatných sítích po buňkách (Kameny_i_j_k); hra je kreslí jen do hrad_vzhled.json kameny_lod0.do_m
(hlavni.gd _hrad_lod: visibility_range). Dál zůstává dnešní jednoduchá síť zdi (zub = kvádr zdiva, nároží = kvádr s texturou
kamene). Žádná globální náhoda (lib.R, kit.RND): každý kámen má vlastní semínko z polohy – přidaný kámen neposune chvění
trámů jinde (kontrola_spoju 16.–17. 11.: změna počtu volání náhody přenášela spoje).
"""
import json, math, os, random
from mathutils import Vector, Matrix
from lib import Part, M, frame
import kit

UP = Vector((0, 1, 0))
CFG = {}
ZAP = True          # hrady.nastav_detail: False = dálková verze (*_daleko.glb) – kameny LOD0 se nestaví, nároží jen kvádry
ter = None          # výška terénu (hrady.ter)
CASTI = {}          # buňka -> Part("Kameny_…")
NAROZI = []         # odložená nároží
KOL_BLIZKO = None   # kolizní kvádry zdí z blízké verze (dálková je bez kolizí) – test přiléhající zdi u nároží
STAT = {"kamenu": 0, "stinek": 0, "kryti": 0, "patka": 0, "narozi_kamenu": 0, "narozi_vynechano": 0}


KOREN = None
NAR_BODY = []       # položené nárožní kameny: vzorky 6 cm před lícem (test smyslu narozi_bez_styku – nesmí ležet v cizí zdi)


def init(K, ter_fn):
    global ter, KOREN
    KOREN = K
    CFG.clear(); CFG.update(json.load(open(os.path.join(K, "pravidla/svet/hrad_vzhled.json")))["kameny_lod0"])
    ter = ter_fn


def _rg(*a):
    return random.Random(int(abs(sum(x * k for x, k in zip(a, (131.0, 71.0, 37.0, 17.0, 7.0)))) * 1000) % 2147483647)


def _cast(p):
    b = CFG["bunka_m"]; k = (math.floor(p.x / b), math.floor(p.y / b), math.floor(p.z / b))
    if k not in CASTI:
        CASTI[k] = Part("Kameny_" + "_".join(("m%d" % -i) if i < 0 else str(i) for i in k))
    return CASTI[k]


def _uv(pts, ou, ov):
    """Krabicová projekce po ploše (bez natažení): svislá plocha u = vodorovně v rovině plochy, v = výška; vodorovná x, z."""
    n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    if n.length < 1e-12: return [(ou, ov)] * len(pts)
    n.normalize()
    if abs(n.y) > 0.7: return [(p.x + ou, p.z + ov) for p in pts]
    t = UP.cross(n).normalized()
    return [(p.dot(t) + ou, p.y + ov) for p in pts]


def kamen(c, bz, size, rg, cham=None, otluk=None, mat=None, P=None):
    """Jeden kámen: kvádr se sraženými hranami, náhodně otlučené rohy a nerovné plochy (vlastní náhoda rg).
    c = střed, bz = báze 3×3 (sloupce = místní osy x, y, z), size = (x, y, z). Do buňky LOD0 (P None) nebo do P."""
    a, b, cc = (s / 2 for s in size)
    ch0 = CFG["sraz_m"] if cham is None else cham; ot = CFG["nerovnost_m"] if otluk is None else otluk
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                h = ch0 * rg.uniform(0.6, 1.5)
                if rg.random() < CFG["otluceny_roh_p"]: h *= 1.9   # otlučený roh
                h = min(h, a * 0.45, b * 0.45, cc * 0.45)
                for p in ((sx * a, sy * (b - h), sz * (cc - h)), (sx * (a - h), sy * b, sz * (cc - h)), (sx * (a - h), sy * (b - h), sz * cc)):
                    pts.append(Vector((p[0] + rg.uniform(-ot, ot), p[1] + rg.uniform(-ot, ot), p[2] + rg.uniform(-ot, ot))))
    verts, faces = kit._hull(pts)
    W = [c + bz @ v for v in verts]
    ou, ov = rg.uniform(0, 5), rg.uniform(0, 5)
    uvs = [_uv([W[k] for k in f], ou, ov) for f in faces]
    (P or _cast(c)).mesh(W, faces, mat or CFG["material"], uvs=uvs, rnd=rg.random())
    STAT["kamenu"] += 1


def kvadr(P, c, bz, size, mat, rg):
    """Hladký kvádr bez globální náhody (dálková / střední verze nároží): krabicové UV s posunem, odstín z rg."""
    a, b, cc = (s / 2 for s in size)
    lv = [(-a, -b, -cc), (a, -b, -cc), (a, b, -cc), (-a, b, -cc), (-a, -b, cc), (a, -b, cc), (a, b, cc), (-a, b, cc)]
    W = [c + bz @ Vector(v) for v in lv]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]
    ou, ov = rg.uniform(0, 5), rg.uniform(0, 5)
    P.mesh(W, faces, mat, uvs=[_uv([W[k] for k in f], ou, ov) for f in faces], rnd=rg.random())


def _baze(d, n, sklon=0.0):
    d = Vector((d.x, 0, d.z)).normalized(); n = Vector((n.x, 0, n.z)).normalized()
    bz = Matrix((d, UP, n)).transposed()
    if sklon: bz = bz @ Matrix.Rotation(math.atan(sklon), 3, "Z")
    return bz


def _delky(L, rg, lo, hi, posun):
    """Rozdělení délky L na kameny (spáry střídavě na vazbu: posun = první kámen zkrácený)."""
    out = []; x = 0.0; prvni = True
    while x < L - 1e-4:
        l_ = rg.uniform(lo, hi)
        if prvni and posun: l_ *= rg.uniform(0.45, 0.7)
        prvni = False
        if L - (x + l_) < lo * 0.55: l_ = L - x
        out.append((x, x + l_)); x += l_
    return out


def jadro_stinky(P, base, d, n, tl, h, L, mat, sklon=0.0):
    """Kvádr zubu v blízké verzi zmenšený o CFG stinka.jadro_m pod kameny LOD0: líc kamenů je pak dost před ním a jeho stín
    na ně nedělá pruhy (stínový posun); 28–60 m je zub o pár cm menší (nepostřehnutelné), daleká verze má plný kvádr."""
    j_ = CFG["stinka"]["jadro_m"]; bz = _baze(d, n, sklon)
    rg = _rg(base.x, base.z, base.y, L, 3.0)
    kvadr(P, base + bz.col[1] * ((h - j_) / 2), bz, (max(0.1, L - 2 * j_), h - j_, max(0.1, tl - 2 * j_)), mat, rg)


def stinka(base, d, n, tl, h, L, sklon=0.0):
    """Zub cimbuří (stínka) z kamenů: base = střed spodní hrany zubu (na koruně zídky), d = podél zdi, n = ven, tl = tloušťka,
    h = výška, L = délka, sklon = tg sklonu koruny (plynulá hradba). Kameny obalují dnešní kvádr zubu (vystupují o
    vystup_m, ve spárách je vidět jeho líc = malta) – z dálky zůstává kvádr, zblízka kameny."""
    if not ZAP or L < 0.3 or h < 0.3: return
    C = CFG["stinka"]; rg = _rg(base.x, base.z, base.y, L)
    bz = _baze(d, n, sklon); dd = bz.col[0]; nn = bz.col[2]; up = bz.col[1]
    hc = rg.uniform(*C["kryci_deska_m"]); hb = h - 0.02   # krycí deska leží na zubu: vrch o 6–10 cm nad kvádrem zubu (těsněji – stín kvádru pod deskou dělal pruhy)
    nr = max(C["rad"][0], min(C["rad"][1], round(hb / C["vrstva_m"])))
    rv_ = C.get("vrstva_rozptyl", [0.8, 1.2]); vy = [rg.uniform(*rv_) for _ in range(nr)]; s_ = sum(vy); vy = [v * hb / s_ for v in vy]
    sp = C["spara_m"]; y = 0.0
    for j, hv in enumerate(vy):
        for x0, x1 in _delky(L, rg, C["kamen_delka_m"][0], C["kamen_delka_m"][1], j % 2 == 1):
            v_ = rg.uniform(*C["vystup_m"])
            c = base + dd * (x0 + x1 - L) / 2 + up * (y + hv / 2) + nn * rg.uniform(-C.get("lic_rozptyl_m", 0.006), C.get("lic_rozptyl_m", 0.006))
            b_ = bz @ Matrix.Rotation(math.radians(rg.uniform(-C.get("natoceni_st", 1.5), C.get("natoceni_st", 1.5))), 3, "Z")
            kamen(c, b_, (x1 - x0 - sp, hv - sp, tl + 2 * v_), rg, cham=C.get("sraz_m"), otluk=C.get("nerovnost_m"))
        y += hv
    # krycí deska (1–2 desky přes celý zub, přesah, sražené hrany)
    kd_ = C.get("kryci_desek", [1, 2]); nd = rg.randint(kd_[0], kd_[1]) if L >= 1.0 else kd_[0]; ps = C["kryci_presah_m"]
    for x0, x1 in _delky(L + 2 * ps, rg, (L + 2 * ps) / nd * 0.75, (L + 2 * ps) / nd * 1.25, False)[:nd]:
        c = base + dd * ((x0 + x1) / 2 - L / 2 - ps) + up * (hb + hc / 2)
        b_ = bz @ Matrix.Rotation(math.radians(rg.uniform(-1.2, 1.2)), 3, "X")
        kamen(c, b_, (x1 - x0 - sp, hc, tl + 2 * ps), rg, cham=CFG["sraz_m"] * 1.3)
    STAT["stinek"] += 1


def kryti(a, d, n, tl, y_top, s0, s1, sklon=0.0):
    """Krycí kameny koruny zídky / předprseně mezi s0 a s1 (od bodu a podél d, osa zídky): nepravidelné desky, horní hrana
    nerovná (Míša 18. 11.: koruna zdí nepravidelná, ne ostrá hrana kvádru)."""
    if not ZAP or s1 - s0 < 0.15: return
    C = CFG["kryti"]; rg = _rg(a.x, a.z, s0, y_top)
    bz = _baze(d, n, sklon); dd = bz.col[0]; up = bz.col[1]
    for x0, x1 in _delky(s1 - s0, rg, C["kamen_delka_m"][0], C["kamen_delka_m"][1], rg.random() < 0.5):
        hv = rg.uniform(*C["vyska_m"]); xm = s0 + (x0 + x1) / 2
        c = a + dd * xm + up * (y_top - C["zapust_m"] + hv / 2 + rg.uniform(-0.008, 0.008))
        b_ = bz @ Matrix.Rotation(math.radians(rg.uniform(-2.0, 2.0)), 3, "X") @ Matrix.Rotation(math.radians(rg.uniform(-1.5, 1.5)), 3, "Y")
        kamen(c, b_, (x1 - x0 - CFG["stinka"]["spara_m"], hv, tl + 2 * rg.uniform(*C["presah_m"])), rg)
    STAT["kryti"] += 1


def patka(a, d, n, s0, s1, vynechat=()):
    """Patka zdi: řada větších kamenů na vnějším líci u terénu (a = bod na líci v ose s = 0, d podél, n ven), vynechat =
    [(s_od, s_do)] otvory (brána, dveře). Kámen sedí pod terénem a vyčnívá nad něj (kontrola_geometrie pod_terenem)."""
    if not ZAP or s1 - s0 < 0.4: return
    C = CFG["patka"]; rg = _rg(a.x, a.z, s0, s1)
    bz = _baze(d, n); dd = bz.col[0]; nn = bz.col[2]
    for x0, x1 in _delky(s1 - s0, rg, C["kamen_delka_m"][0], C["kamen_delka_m"][1], rg.random() < 0.5):
        u0, u1 = s0 + x0, s0 + x1
        if any(u1 > o0 - 0.25 and u0 < o1 + 0.25 for o0, o1 in vynechat): continue
        tt = [ter(*(a + dd * u + nn * 0.1).xz) for u in (u0, (u0 + u1) / 2, u1)]
        if max(tt) - min(tt) > C["max_spad_m"]: continue   # strmá skála: kámen by visel nebo trčel
        y0 = min(tt) - C["pod_terenem_m"]; hv = max(rg.uniform(*C["vyska_m"]), max(tt) - y0 + C["nad_terenem_min_m"])
        v_ = rg.uniform(*C["vystup_m"]); hl = C["hloubka_m"]
        c = a + dd * ((u0 + u1) / 2) + nn * (v_ - hl / 2) + UP * (y0 + hv / 2)
        kamen(c, bz @ Matrix.Rotation(math.radians(rg.uniform(-1.5, 1.5)), 3, "Z"), (u1 - u0 - CFG["stinka"]["spara_m"], hv, hl), rg,
              cham=CFG["sraz_m"] * 1.4)
    STAT["patka"] += 1


def narozi(P, R, stena_a, stena_b, y0, y1, mat, seme=0):
    """Nárožní kvádry – odložené do dokonci() (až budou známé všechny zdi, kvůli přiléhajícím zdem)."""
    NAROZI.append((P, R.copy(), (stena_a[0].copy(), stena_a[1].copy()), (stena_b[0].copy(), stena_b[1].copy()), y0, y1, mat, seme))


def _kolize_mrizka(cols):
    g = {}
    for m, sz in cols:
        if sz[1] < 1.5 or min(sz[0], sz[2]) < 0.3: continue   # jen zdivo (ne zábradlí, schody, výplně)
        mi = m.inverted(); c = m.translation; r = 0.5 * math.sqrt(sz[0] ** 2 + sz[2] ** 2)
        for i in range(math.floor((c.x - r) / 4), math.floor((c.x + r) / 4) + 1):
            for k in range(math.floor((c.z - r) / 4), math.floor((c.z + r) / 4) + 1):
                g.setdefault((i, k), []).append((mi, sz))
    return g


def _v_kolizi(g, p):
    for mi, sz in g.get((math.floor(p.x / 4), math.floor(p.z / 4)), ()):
        l = mi @ p
        if abs(l.x) <= sz[0] / 2 and abs(l.y) <= sz[1] / 2 and abs(l.z) <= sz[2] / 2: return True
    return False


def dokonci(parts):
    """Postaví odložená nároží a vrátí buňky kamenů LOD0 (sítě navíc pro uloz). Volá hrady.uloz na začátku."""
    global KOL_BLIZKO
    if not NAROZI and not CASTI: return []
    if ZAP: KOL_BLIZKO = [c for P in parts for c in P.cols]
    g = _kolize_mrizka(KOL_BLIZKO or [])
    C = CFG["narozi"]; km = CFG["material"]
    for P, R, (dxa, nxa), (dxb, nxb), y0, y1, mat, seme in NAROZI:
        if y1 - y0 < 0.5: continue
        rg = _rg(R.x, R.z, seme)
        y = y0; k = rg.randrange(2)
        while y < y1 - 0.12:
            h = min(rg.uniform(*C["vrstva_m"]), y1 - y)
            for i_, (dx, nx) in enumerate(((dxa, nxa), (dxb, nxb))):
                dlouhy = (i_ == k % 2)
                L = rg.uniform(*C["vazak_m"]) if dlouhy else rg.uniform(*C["kratky_m"])
                dep = rg.uniform(*C["hloubka_m"]); pv = rg.uniform(*C["vystup_m"]); pk = rg.uniform(0.0, 0.04)
                c = R + dx * (L / 2 - pk) - nx * (dep / 2 - pv) + UP * (y + h / 2 + rg.uniform(-0.01, 0.01))
                bz = frame(dx) @ Matrix.Rotation(math.radians(rg.uniform(-2.5, 2.5)), 3, "Z") @ Matrix.Rotation(math.radians(rg.uniform(-2.0, 2.0)), 3, "Y")
                # přiléhající zeď: vzorky 6 cm před lícem obou stěn nároží v kolizi zdiva = roh není volný (zeď navazuje) → bez kvádru
                ym = y + h / 2
                if any(_v_kolizi(g, R + e * s + o * 0.06 + UP * ym) for e, o in ((dxa, nxa), (dxb, nxb)) for s in (0.12, 0.4)):
                    STAT["narozi_vynechano"] += 1; continue
                sz = (dep, h - 0.03, L)
                if ZAP:   # blízká verze: jen kámen LOD0 (kvádr pod ním by stínil na jeho líc – pruhy); 28–60 m roh bez nárožních kvádrů, dál daleká verze s kvádry
                    kamen(c, bz, sz, rg, cham=rg.uniform(*C["sraz_m"]), otluk=rg.uniform(0.02, 0.035), mat=C.get("material", "kamen_kus"))
                    STAT["narozi_kamenu"] += 1
                    for e, o in ((dxa, nxa), (dxb, nxb)):
                        q = R + e * 0.25 + o * 0.06 + UP * ym; NAR_BODY.append([round(q.x, 3), round(q.z, 3), round(q.y, 3)])
                else:
                    kvadr(P, c, bz, sz, km, rg)
            y += h; k += 1
    NAROZI.clear()
    out = list(CASTI.values()); CASTI.clear()
    if ZAP and KOREN and out:
        os.makedirs(os.path.join(KOREN, "build"), exist_ok=True)
        json.dump({"popis": "kameny LOD0 hradů (blender/kamenivo.py): počty a vzorky před lícem položených nárožních kamenů – test smyslu kameny_lod0, narozi_bez_styku",
                   "stat": dict(STAT), "bunek": len(out), "troj": sum(sum(len(f[0]) - 2 for f in P.f) for P in out), "narozi_body": NAR_BODY},
                  open(os.path.join(KOREN, "build/kameny_lod0.json"), "w"), ensure_ascii=False)
        print("KAMENY_LOD0", dict(STAT), "buněk", len(out), flush=True)
    NAR_BODY.clear()
    for k_ in STAT: STAT[k_] = 0
    return out
