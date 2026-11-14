"""Stodoly a kůlna usedlostí z dat (pravidla/svet/stodoly.json) – PŘEVZATO Z HAVRANA (blender/vlastni.py stodola(), kolna(),
_desky_stena, _desky_stena_y, _horni_hrana, _strecha_plocha, _hlidac_strechy, _PODEZDIVKA; větev claude/new-session-0dtk58),
upraveno pro Puchart (Míša 14. 11.: „projdi všechny kůlny a stodoly ve hře, chci v nich mít funkční vrata a ať nejsou ze
čtverečků jako ty schody“):
- každé prkno = jeden kus dřeva: řádek atlasu jednotlivých prken (blender/tex/prkna_atlas, nastroje/drevo_tex.py) přes celou
  šířku prkna, vlákna podél – jako mostovka hradu (blender/hrady.py TEX prkno_ven, kit.plank). Havran dával na každé prkno
  fotku celé podlahy z prken (prkna_ven) → každé prkno mřížka drobných čtverečků.
- dřevo hnědé opotřebované jako hrad (hrad_vzhled.json drevo; trámy rough_wood_sedy, čela letokruhy, šindel, zdivo z droby)
- vrata stodol jako samostatné uzly <Uzel>_Dvere_L / _P (počátek = pant na vnější svislé hraně, v modelu zavřená) –
  nastroje/pohyb_mista.py z nich udělá funkční vrata (dvere.gd, otvírají se ven); průjezd vrat bez prahu a podezdívky
  (mlat v úrovni dvora), kolize nechává průjezd volný (křídla mají kolizi z dvere.gd)
- rozměry, počátek, natočení a jména souborů jako dosud (hra/modely/predmety_h/<id>.glb, <id>_kolize.glb; viditelný model
  vystředěný na pivot kolize z katalogu predmety_h.json) – umístění ve vsi (nastroje/mista_rozmisteni.py) se nemění
- hlídač střechy (Havran _hlidac_strechy, Míša 0.9998 „vrata od stodoly ve střeše“): žádný díl nad šindelem, jinak výjimka
Střední stupeň *_stredni.glb se nestaví a starý (model Havrana) se maže: ves.gd ho má vypnutý (mista.json lod_ves
stredni_zapnuto false – kreslil se černě), predmety.gd by jinak ukazoval z dálky starou stodolu.
  /opt/bl/bin/python blender/stodoly.py <koren_puchartu> [id ...]
"""
import sys, os, json, math, random, glob, shutil, tempfile
K = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ".")
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

C = json.load(open(os.path.join(K, "pravidla/svet/stodoly.json")))
PK = C["prkna"]
OUT = os.path.join(K, "hra/modely/predmety_h")
TEXDIR = os.path.join(K, "blender/tex")
UP = Vector((0, 0, 1))
X = Vector((1, 0, 0))
Y = Vector((0, 1, 0))


# ------------------------------------------------------------------ síť (lokální seznamy, objekt až na konci)
class Sit:
    """Plochy s UV a materiálem; tag plochy: strecha (hlídač ji bere jako šindel), hrebenac (smí ležet na střeše)."""
    def __init__(s):
        s.v, s.f, s.uv, s.m, s.tag = [], [], [], [], []

    def plocha(s, pts, uvs, mat, tag=""):
        i0 = len(s.v)
        s.v.extend(Vector(p) for p in pts)
        s.f.append(tuple(range(i0, i0 + len(pts))))
        s.uv.append([tuple(u) for u in uvs])
        s.m.append(mat)
        s.tag.append(tag)


# rohy stěny osy ax (0/1 = strana): (i, j, k) indexy kvádru
def _rohy(ax, sd):
    if ax == 0: return [(sd, 0, 0), (sd, 1, 0), (sd, 1, 1), (sd, 0, 1)]
    if ax == 1: return [(0, sd, 0), (0, sd, 1), (1, sd, 1), (1, sd, 0)]
    return [(0, 0, sd), (1, 0, sd), (1, 1, sd), (0, 1, sd)]


def hexa(S, P, druh, mat, R, g=2, tenka=1, tag="", rada=None, uo=None):
    """Šestistěn z 8 vrcholů P[(i,j,k)] (osy i, j, k). druh:
    tram  – vlákna podél osy g (UV v metrech / velikost fotky), čela (stěny osy g) letokruhy (rez)
    prkno – atlas prken: široké stěny (osa `tenka`) = celý řádek `rada` přes šířku (osa, která není g ani tenka), boky úzký
            pruh téhož řádku, čela letokruhy; posun po délce uo (jako kit.plank uvo)
    kamen – rovinné UV podle světa (velikost fotky), zelezo – bez UV."""
    vel = C["materialy"][mat][1] if mat in C["materialy"] and isinstance(C["materialy"][mat][0], str) else 1.0
    cen = sum((P[k] for k in P), Vector()) / 8.0
    w = 3 - g - tenka
    if uo is None: uo = R.random()
    ov = R.random()
    n_r = PK["atlas_radku"]; okr = PK["atlas_okraj"]
    gv = (sum((P[k] for k in P if k[g] == 1), Vector()) - sum((P[k] for k in P if k[g] == 0), Vector())) / 4.0
    gL = gv.length; gv = gv.normalized() if gL > 1e-9 else UP
    for ax in range(3):
        for sd in (0, 1):
            idx = _rohy(ax, sd)
            pts = [P[k] for k in idx]
            n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
            if n.length < 1e-12: n = (pts[2] - pts[1]).cross(pts[3] - pts[1])
            fc = sum(pts, Vector()) / 4.0
            if n.dot(fc - cen) < 0: idx = idx[::-1]; pts = pts[::-1]
            nn = n.normalized() if n.dot(fc - cen) >= 0 else -n.normalized()
            if druh == "zelezo":
                S.plocha(pts, [(0, 0)] * 4, mat, tag); continue
            if druh == "kamen":
                a_ = max(range(3), key=lambda q: abs(nn[q])); o_ = [q for q in range(3) if q != a_]
                S.plocha(pts, [(p[o_[0]] / vel + uo, p[o_[1]] / vel + ov) for p in pts], mat, tag); continue
            if ax == g:   # čelo: letokruhy přes průřez
                e1 = Vector(pts[1] - pts[0]); e2 = Vector(pts[3] - pts[0])
                r1 = max(e1.length, 1e-4); r2 = max(e2.length, 1e-4); e1.normalize(); e2.normalize()
                S.plocha(pts, [(0.05 + 0.9 * (p - pts[0]).dot(e1) / r1, 0.05 + 0.9 * (p - pts[0]).dot(e2) / r2) for p in pts], "rez", tag)
                continue
            if druh == "tram":
                b_ = nn.cross(gv).normalized()
                S.plocha(pts, [(p.dot(b_) / vel + uo, p.dot(gv) / vel + ov) for p in pts], mat, tag)
            else:   # prkno z atlasu: u = délka (řádek atlasu je vodorovný), v = poloha přes šířku v řádku
                uvs = []
                for k_, p in zip(idx, pts):
                    u = (p - P[(0, 0, 0)]).dot(gv) / vel + uo
                    if ax == tenka: s_ = k_[w]
                    else: s_ = 0.5 + 0.12 * (k_[tenka] - 0.5)
                    uvs.append((u, (rada + okr + (1 - 2 * okr) * s_) / n_r))
                S.plocha(pts, uvs, mat, tag)


def obox(S, c, A, H, druh, mat, R, tag="", rada=None, uo=None):
    """Natočený kvádr: střed c, osy A (3 jednotkové vektory), poloviční rozměry H. Vlákna podél nejdelší osy,
    prkno: tenká osa = nejkratší."""
    c = Vector(c); A = [Vector(a).normalized() for a in A]
    P = {(i, j, k): c + A[0] * H[0] * (2 * i - 1) + A[1] * H[1] * (2 * j - 1) + A[2] * H[2] * (2 * k - 1)
         for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    g = max(range(3), key=lambda q: H[q]); t = min((q for q in range(3) if q != g), key=lambda q: H[q])
    if rada is None: rada = R.randrange(PK["atlas_radku"])
    hexa(S, P, druh, mat, R, g=g, tenka=t, tag=tag, rada=rada, uo=uo)


def box(S, c, size, druh, mat, R, tag=""):
    """Kvádr v osách (Havran _box: střed, rozměry)."""
    obox(S, c, (X, Y, UP), [size[0] / 2, size[1] / 2, size[2] / 2], druh, mat, R, tag)


def tram(S, a, b, sir, vys, mat, R, up=UP, tag=""):
    """Trám z a do b (šířka vodorovně, výška ve směru up)."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized()
    sd = Vector(up).cross(d)
    if sd.length < 1e-6: sd = X.cross(d)
    sd.normalize(); uu = d.cross(sd).normalized()
    obox(S, (a + b) / 2, (sd, uu, d), [sir / 2, vys / 2, (b - a).length / 2], "tram", mat, R, tag)


# ------------------------------------------------------------------ prkna stěn (Havran _desky_stena, _horni_hrana)
def prkno_svisle(S, O, ex, en, x0, w, t, zb, ztop, mat, R, off=0.0, tag=""):
    """Svislé prkno ve stěně: O = počátek stěny (z = 0), ex = podél stěny, en = normála ven; od x0 šířky w, tloušťky t,
    střed tloušťky posunutý o off ven. Spodek zb, horní hrana ztop(x, y) po vrcholech (šikmý štít – Havran _horni_hrana)."""
    nak = math.tan(math.radians(R.uniform(-PK["naklon_deg"], PK["naklon_deg"])))
    dn = R.uniform(-PK["odchylka_m"], PK["odchylka_m"]) + off
    zb = zb + R.uniform(*PK["pata_zkraceni_m"])
    P = {}
    for i in (0, 1):
        for j in (0, 1):
            xy0 = O + ex * (x0 + w * i) + en * (dn + t * (j - 0.5))
            for k in (0, 1):
                if k == 0: P[(i, j, k)] = Vector((xy0.x, xy0.y, zb))
                else:
                    zt = ztop(xy0.x, xy0.y)
                    p = xy0 + ex * (nak * (zt - zb))                 # náklon prkna (ruční práce)
                    P[(i, j, k)] = Vector((p.x, p.y, ztop(p.x, p.y)))
    if min(P[(i, j, 1)].z for i in (0, 1) for j in (0, 1)) - zb < 0.05: return
    hexa(S, P, "prkno", mat, R, g=2, tenka=1, tag=tag, rada=R.randrange(PK["atlas_radku"]))


def stena(S, O, ex, en, x0, x1, zb, ztop, mat, R, laty=True, mimo=None, tag=""):
    """Stěna ze svislých prken (Havran _desky_stena: šířka 0,2–0,3 m, mezery 0–1 cm) od x0 do x1 podél ex; přes spáru každého
    latka_kazda-tého prkna lať (Havran popis „přes ně latka na spáře každého druhého prkna“). mimo(x) = True: lať tam ne."""
    t = PK["tloustka_m"]; lw, lt = PK["latka_m"]
    x = x0; n = 0
    while x < x1 - 0.02:
        w = min(R.uniform(*PK["sirka_m"]), x1 - x)
        if x1 - (x + w) < 0.08: w = x1 - x                     # žádná úzká lišta na konci stěny
        prkno_svisle(S, O, ex, en, x, w - R.uniform(*PK["mezera_m"]), t, zb, ztop, mat, R, tag=tag)
        x += w; n += 1
        if laty and n % PK["latka_kazda"] == 0 and x < x1 - 0.05 and not (mimo and mimo(x)):
            prkno_svisle(S, O, ex, en, x - lw / 2, lw, lt, zb + 0.02, ztop, mat, R, off=t / 2 + lt / 2, tag=tag)


# ------------------------------------------------------------------ střecha (Havran _strecha_plocha)
def strecha(S, a, b, c, d, R, tl=0.06):
    """Střecha jako deska mezi rohy a-b (okap) a d-c (hřeben), plocha a..d je spodek, deska nad ní; šindel po vel m."""
    a, b, c, d = Vector(a), Vector(b), Vector(c), Vector(d)
    n = (b - a).cross(d - a).normalized() * tl
    vel = C["materialy"]["sindel"][1]
    sirka, spad = (b - a).length, (d - a).length
    vs = (a, b, c, d, a - n, b - n, c - n, d - n)
    for idx, uv in (((0, 1, 2, 3), ((0, 0), (sirka, 0), (sirka, spad), (0, spad))),
                    ((7, 6, 5, 4), ((0, spad), (sirka, spad), (sirka, 0), (0, 0))),
                    ((0, 4, 5, 1), ((0, 0), (0, tl), (sirka, tl), (sirka, 0))),
                    ((3, 2, 6, 7), ((0, 0), (sirka, 0), (sirka, tl), (0, tl))),
                    ((0, 3, 7, 4), ((0, 0), (spad, 0), (spad, tl), (0, tl))),
                    ((1, 5, 6, 2), ((0, 0), (0, tl), (spad, tl), (spad, 0)))):
        pts = [vs[i] for i in idx]
        S.plocha(pts, [(u / vel, v / vel) for u, v in uv], "sindel", "strecha")


def hlidac_strechy(jm, site):
    """Havran _hlidac_strechy (Míša 0.9998 „vrata od stodoly ve střeše“): žádný vrchol jiného dílu nesmí být NAD střechou –
    paprsek dolů z vrcholu (a z bodů po hranách) nesmí jako první trefit horní plochu šindele (normála nahoru). Uvnitř desky střechy je dovoleno,
    hřebenáče leží na střeše záměrně. Selže-li, model se nepostaví (výjimka) – opravit generátor, ne výjimku."""
    V, F = [], []
    for S in site:
        for f, tg in zip(S.f, S.tag):
            if tg == "strecha":
                o = len(V); V += [S.v[i] for i in f]; F.append(list(range(o, o + len(f))))
    if not F: return
    strom = BVHTree.FromPolygons(V, F)
    spatne = []
    for S in site:
        for f, tg in zip(S.f, S.tag):
            if tg in ("strecha", "hrebenac"): continue
            body = []   # vrcholy a body po hranách à 5 cm (dlouhá hrana křídla nad tenkým okapem mezi vrcholy, 14. 11.)
            for a_, b_ in zip(f, f[1:] + f[:1]):
                pa, pb = S.v[a_], S.v[b_]; n_ = max(1, int((pb - pa).length / 0.05))
                body += [pa.lerp(pb, q / n_) for q in range(n_)]
            for w in body:
                hit, nrm, _i, dist = strom.ray_cast(w + Vector((0, 0, 0.001)), Vector((0, 0, -1)))
                if hit is not None and nrm.z > 0.0:
                    spatne.append("(%.2f, %.2f, %.2f) %.2f m nad střechou" % (w.x, w.y, w.z, dist)); break
    if spatne:
        raise RuntimeError("HLIDAC strechy %s: %d ploch trčí střechou: %s" % (jm, len(spatne), "; ".join(spatne[:6])))
    print("HLIDAC strechy %s: OK" % jm, flush=True)


# ------------------------------------------------------------------ stodola (Havran vlastni.stodola)
def stodola(m, R):
    """Prkenná stodola: kamenná podezdívka (vpředu přerušená průjezdem vrat), kostra z tesaných trámů (práh, sloupy, veřeje
    vrat, pozednice, paždík, vazné trámy, krokve), svislá prkna s laťmi, sedlová střecha ze šindele (přesah okap 0,55,
    štít 0,4), hřebenáče, dvoukřídlá vrata 3 m na delší straně (−y = předek) pod pozednicí, dvířka na seno ve štítu.
    Vrací (tělo, [(jméno křídla, síť, pant)], kolize)."""
    P_ = C["stodola"]; zap, sp = C["podezdivka"]["zapust_m"], C["podezdivka"]["sirka_m"]
    L, D, Hw = m["L"], m["D"], m["Hw"]
    t = math.tan(math.radians(m["sklon_deg"]))
    o = P_["odsazeni_prken_m"]
    dz_s = (o + 0.04) * t                                 # spodek střechy na líci stěny, ne na ose (Havran 0.9998)
    hreben = Hw + dz_s + D / 2 * t
    z0 = P_["z0_m"]; tr = P_["tram_m"]; prw, prh = P_["prah_m"]; pzw, pzh = P_["pozednice_m"]
    stit = lambda x, y: Hw + dz_s + (D / 2 - abs(y - D / 2)) * t
    # prkna okapových stěn končí pod krokvemi (krokve leží na pozednici a přečnívají přes stěnu – Havran měl prkna do Hw a
    # krokve by jimi prostupovaly); mezi krokvemi nad prkny okapová mezera, pozednice je nadpražím vrat (Havran)
    z_okap = Hw - 0.06 - (o + PK["tloustka_m"] / 2) * t - 0.01
    rovna = lambda x, y: z_okap
    vw = P_["vrata_sirka_m"]; vx0, vx1 = -vw / 2, vw / 2
    # horní hrana průjezdu: pod pozednicí (Havran), ale i pod okapem – otevřené křídlo (ven, kolmo od stěny) jinak prošlo
    # přesahem střechy (snímek 14. 11.; Havran 0.9998 „vrata od stodoly ve střeše“); nad vraty nadpraží a prkna
    z_ok_ = Hw + dz_s - P_["presah_okap_m"] * t
    z_nad = min(Hw - pzw - P_["vrata_pod_pozednici_m"] - 0.02, z_ok_ - P_["vrata_pod_okapem_m"])
    S = Sit(); KOL = Sit()
    # kamenná podezdívka pod prahem (Havran: zapuštěná pod nulu modelu); vpředu jen mimo průjezd vrat
    hz = z0 + zap; cz = (z0 - zap) / 2
    box(S, (0, D, cz), (L + sp, sp, hz), "kamen", "kamen", R)
    for xa, xb in ((-L / 2 - sp / 2, vx0), (vx1, L / 2 + sp / 2)):
        box(S, ((xa + xb) / 2, 0, cz), (xb - xa, sp, hz), "kamen", "kamen", R)
    for x in (-L / 2, L / 2):
        box(S, (x, D / 2, cz), (sp, D - sp, hz), "kamen", "kamen", R)
    # práh (vpředu přerušený průjezdem), pozednice
    box(S, (0, D, z0 + prh / 2), (L + 0.2, prw, prh), "tram", "tram", R)
    for xa, xb in ((-L / 2 - 0.1, vx0), (vx1, L / 2 + 0.1)):
        box(S, ((xa + xb) / 2, 0, z0 + prh / 2), (xb - xa, prw, prh), "tram", "tram", R)
    for x in (-L / 2, L / 2):
        box(S, (x, D / 2, z0 + prh / 2), (prw, D - prw, prh), "tram", "tram", R)
    for y in (0.0, D):
        box(S, (0, y, Hw - pzw / 2 - 0.06), (L + 0.3, pzw, pzh), "tram", "tram", R)
    zp0, zp1 = z0 + prh, Hw - 0.06 - pzh               # sloup čepem v prahu a pozednici (neprostupuje)
    xs_z = (-L / 2, -L / 6, L / 6, L / 2)
    xs_p = (-L / 2, vx0 - tr / 2, vx1 + tr / 2, L / 2)   # vpředu veřeje vrat po stranách průjezdu
    for xs, y in ((xs_p, 0.0), (xs_z, D)):
        for x in xs:
            box(S, (x, y, (zp0 + zp1) / 2), (tr, tr, zp1 - zp0), "tram", "tram", R)
    # paždík uvnitř stěn mezi sloupy (prkna jsou na něm přibitá)
    zpz = z0 + (Hw - z0) * P_["padlo_vyska"]
    for xs, y in ((xs_p, 0.0), (xs_z, D)):
        for xa, xb in zip(xs[:-1], xs[1:]):
            if y == 0.0 and xa < 0 < xb: continue        # průjezd vrat
            box(S, ((xa + xb) / 2, y - (tr / 2 - 0.06) * (1 if y == 0 else -1), zpz), (xb - xa - tr, 0.12, 0.12), "tram", "tram", R)
    for x in (-L / 2, L / 2):
        box(S, (x + (tr / 2 - 0.06) * (-1 if x < 0 else 1), D / 2, zpz), (0.12, D - tr, 0.12), "tram", "tram", R)
    # vazné trámy na pozednicích nad sloupy, krokve s osedláním na pozednici (svislý řez u hřebene a okapu)
    zv = Hw - 0.06 + 0.08
    for x in xs_z:
        box(S, (x, D / 2, zv), (0.16, D + 0.1, 0.16), "tram", "tram", R)
    kw = P_["krokev_sirka_m"]
    pe, ps = P_["presah_okap_m"], P_["presah_stit_m"]
    hloubka = dz_s + 0.06 - 0.003                        # svisle: od spodku šindele na líci osy stěny k vršku pozednice
    nk = max(2, round(L / P_["krokve_rozestup_m"]))
    xk = [-L / 2 + L * i / nk for i in range(nk + 1)]
    xk = [x + (0.16 / 2 + kw / 2 + 0.01) * (1 if x <= 0 else -1) if min(abs(x - v) for v in xs_z) < 0.15 else x for x in xk]
    xk += [-(L / 2 + o + 0.1), L / 2 + o + 0.1]          # krokve štítu za prkny štítu (pod přesahem)
    for x in xk:
        for s in (-1, 1):
            y_e = (-pe + 0.08) if s < 0 else (D + pe - 0.08); y_h = D / 2
            zt = lambda y: stit(0, y) - 0.003
            Pk = {}
            for i in (0, 1):
                for k, y in ((0, y_e), (1, y_h)):
                    Pk[(i, 1, k)] = Vector((x + kw * (i - 0.5), y, zt(y)))
                    Pk[(i, 0, k)] = Vector((x + kw * (i - 0.5), y, zt(y) - hloubka))
            hexa(S, Pk, "tram", "tram", R, g=2, tenka=0)
    # stěny: předek s průjezdem, zadní, štíty (Havran: prkna o ven od osy sloupů)
    O_p, O_z = Vector((0, -o, 0)), Vector((0, D + o, 0))
    stena(S, O_p, X, -Y, -L / 2, vx0, z0, rovna, "prkno", R)
    stena(S, O_p, X, -Y, vx1, L / 2, z0, rovna, "prkno", R)
    stena(S, O_p, X, -Y, vx0, vx1, z_nad, rovna, "prkno", R)          # prkna nad vraty (do spodku krokví)
    box(S, (0, 0, z_nad + 0.07), (vw, tr, 0.14), "tram", "tram", R)   # nadpraží mezi veřejemi
    stena(S, O_z, X, Y, -L / 2, L / 2, z0, rovna, "prkno", R)
    dv_w, dv_h, dv_z = P_["dvirka_seno_m"]
    for x, ex, en in ((-L / 2 - o, Y, -X), (L / 2 + o, Y, X)):   # štíty přes rohy (bez škvíry u nároží)
        mimo = (lambda yy: abs(yy - D / 2) < dv_w / 2 + 0.06) if x < 0 else None
        stena(S, Vector((x, 0, 0)), ex, en, -o - PK["tloustka_m"] / 2, D + o + PK["tloustka_m"] / 2, z0, stit, "prkno", R, mimo=mimo)
    # dvířka na seno v levém štítu (Havran: 0,9 × 1,0, střed 0,9 m nad pozednicí): prkna, dvě svlaky, závěsy
    xd = -L / 2 - o - PK["tloustka_m"] / 2 - 0.016
    yd0 = D / 2 - dv_w / 2
    zd0, zd1 = Hw + dv_z - dv_h / 2, Hw + dv_z + dv_h / 2
    stena(S, Vector((xd, 0, 0)), Y, -X, yd0, yd0 + dv_w, zd0, lambda x_, y_: zd1, "prkno_vrata", R, laty=False)
    for zz in (zd0 + 0.15, zd1 - 0.15):
        box(S, (xd - 0.035, D / 2, zz), (0.04, dv_w - 0.08, 0.11), "prkno", "prkno_vrata", R)
        box(S, (xd - 0.06, yd0 + 0.2, zz), (0.01, 0.4, 0.04), "zelezo", "zelezo", R)
    # vrata: dvě křídla (samostatné uzly, počátek = pant), zavřená
    kridla = []
    zb = P_["vrata_nad_zemi_m"]; zt_ = z_nad - 0.02
    y_pl = -o - 0.05                                     # střed prken křídla (Havran −o − 0,05)
    sw, st_ = P_["svlak_m"]; vzw, vzt = P_["vzpera_m"]; zl, zw, zt3 = P_["zaves_m"]
    y_sv = y_pl - PK["tloustka_m"] / 2 - st_ / 2
    y_pant = y_sv - st_ / 2 - zt3                        # vnější líc závěsů = osa otáčení (vrata ven)
    mez = P_["vrata_mezera_stred_m"] / 2
    for strana, a, b in (("L", vx0 + P_["vrata_veje_m"] / 2, -mez), ("P", mez, vx1 - P_["vrata_veje_m"] / 2)):
        Kr = Sit(); sg = 1 if strana == "L" else -1       # sg: od pantu ke středu
        xp = a if strana == "L" else b                   # pant na vnější svislé hraně
        stena(Kr, Vector((0, y_pl, 0)), X, -Y, a, b, zb, lambda x_, y_: zt_, "prkno_vrata", R, laty=False)
        zs = (zb + P_["svlak_od_kraje_m"], zt_ - P_["svlak_od_kraje_m"])
        for zz in zs:
            box(Kr, ((a + b) / 2, y_sv, zz), (b - a - 0.08, st_, sw), "prkno", "prkno_vrata", R)
            box(Kr, (xp + sg * zl / 2, y_sv - st_ / 2 - zt3 / 2, zz), (zl, zt3, zw), "zelezo", "zelezo", R)   # pásový závěs
            box(S, (xp - sg * 0.03, (y_pant + (-o - PK["tloustka_m"])) / 2, zz), (0.05, abs(y_pant + o + PK["tloustka_m"]), 0.05), "zelezo", "zelezo", R)   # hák na stěně
        # šikmá vzpěra (Z): od pantu dole nahoru k zámku – tlačená (Havran: vzpěra mezi svlaky)
        p0 = Vector((xp + sg * 0.12, y_sv, zs[0] + sw / 2))
        p1 = Vector((xp + sg * (b - a - 0.12), y_sv, zs[1] - sw / 2))
        d_ = (p1 - p0).normalized(); q_ = Y.cross(d_).normalized()
        obox(Kr, (p0 + p1) / 2, (d_, q_, Y), [(p1 - p0).length / 2, vzw / 2, vzt / 2], "prkno", "prkno_vrata", R)
        kridla.append((strana, Kr, Vector((xp, y_pant, 0.0))))
    # střecha (šindel), hřebenáče (prkna z atlasu, leží na střeše)
    for s in (-1, 1):
        y_ok = D / 2 + s * (D / 2 + pe)
        z_ok = Hw + dz_s - pe * t
        a = (-L / 2 - ps, y_ok, z_ok); b = (L / 2 + ps, y_ok, z_ok)
        c = (L / 2 + ps, D / 2, hreben); d = (-L / 2 - ps, D / 2, hreben)
        if s < 0: a, b = b, a; c, d = d, c
        strecha(S, a, b, c, d, R)
    for s in (-1, 1):
        r = s * math.radians(m["sklon_deg"])
        ey = Vector((0, math.cos(r), math.sin(r))); ez = Vector((0, -math.sin(r), math.cos(r)))
        obox(S, (0, D / 2 + s * 0.08, hreben + 0.02), (X, ey, ez), [(L + 2 * ps + 0.1) / 2, 0.11, 0.015], "prkno", "prkno", R, tag="hrebenac")
    # kolize: stěny (vpředu průjezd vrat volný – křídla mají vlastní kolizi z dvere.gd), střecha jako hranol (Havran)
    hk = Hw + 0.1
    box(KOL, (0, D + 0.05, hk / 2), (L + 0.3, 0.3, hk), "zelezo", "k", R)
    for x in (-L / 2 - 0.05, L / 2 + 0.05):
        box(KOL, (x, D / 2, hk / 2), (0.3, D + 0.3, hk), "zelezo", "k", R)
    for xa, xb in ((-L / 2 - 0.15, vx0), (vx1, L / 2 + 0.15)):
        box(KOL, ((xa + xb) / 2, -0.05, hk / 2), (xb - xa, 0.3, hk), "zelezo", "k", R)
    box(KOL, (0, -0.05, (z_nad + hk) / 2), (vw, 0.3, hk - z_nad), "zelezo", "k", R)
    box(KOL, (0, D / 2, Hw + (hreben - Hw) / 2), (L, D * 0.6, hreben - Hw), "zelezo", "k", R)
    return S, kridla, KOL


# ------------------------------------------------------------------ kůlna (Havran vlastni.kolna)
def kolna(m, R):
    """Otevřená kůlna na sloupech: zadní a boční stěna z prken, vpředu 3 otevřená pole na sloupech s pásky, pultová
    střecha ze šindele spadající dozadu (vpředu Hp, vzadu Hz), přesah 0,5 m. Předek = −y."""
    P_ = C["kolna"]; zap, sp = C["podezdivka"]["zapust_m"], C["podezdivka"]["sirka_m"]
    L, D, Hp, Hz = m["L"], m["D"], m["Hp"], m["Hz"]
    z0 = P_["z0_m"]; tr = P_["tram_m"]
    vys = lambda y: Hp + (Hz - Hp) * (y / D)
    xs = [-L / 2 + i * L / 3 for i in range(4)]
    S = Sit(); KOL = Sit()
    box(S, (0, D + 0.1, (z0 - zap) / 2), (L + 0.2 + sp, sp, z0 + zap), "kamen", "kamen", R)
    for x in (-L / 2 - 0.1, L / 2 + 0.1):
        box(S, (x, D / 2 + 0.05, (z0 - zap) / 2), (sp, D + 0.1 - sp, z0 + zap), "kamen", "kamen", R)
    for x in xs:
        box(S, (x, 0.0, (0.2 - zap) / 2), (0.35, 0.35, 0.2 + zap), "kamen", "kamen", R)
        for y in (0.0, D):
            hh = vys(y)
            box(S, (x, y, z0 + (hh - z0) / 2), (tr, tr, hh - z0), "tram", "tram", R)
        # pásky u předních sloupů (Havran 0.9998: od sloupu šikmo nahoru pod vaznici)
        for s in (-1, 1):
            if (x == xs[0] and s < 0) or (x == xs[-1] and s > 0): continue
            ang = math.radians(45)
            d_ = Vector((s * math.cos(ang), 0, math.sin(ang)))
            c_ = Vector((x + s * 0.40, 0.0, Hp - 0.30))
            tram(S, c_ - d_ * 0.45, c_ + d_ * 0.45, 0.12, 0.12, "tram", R, up=Y)
    for y in (0.0, D):
        box(S, (0, y, vys(y) + 0.08), (L + 0.3, 0.18, 0.16), "tram", "tram", R)
    for x in xs:                                         # krokve po spádu střechy (pod šindelem)
        a_ = Vector((x, -0.35, vys(-0.35) + 0.2)); b_ = Vector((x, D + 0.35, vys(D + 0.35) + 0.2))
        tram(S, a_, b_, 0.14, 0.12, "tram", R)
    stena(S, Vector((0, D + 0.1, 0)), X, Y, -L / 2, L / 2, z0, lambda x_, y_: Hz, "prkno", R)
    yk = D + 0.1 + PK["tloustka_m"] / 2                  # boční stěny přes roh zadní stěny (bez škvíry u nároží)
    stena(S, Vector((-L / 2 - 0.1, 0, 0)), Y, -X, 0.0, yk, z0, lambda x_, y_: vys(min(y_, D)), "prkno", R)
    stena(S, Vector((L / 2 + 0.1, 0, 0)), Y, X, 0.0, yk, z0, lambda x_, y_: vys(min(y_, D)), "prkno", R)
    pe = P_["presah_m"]; spd = (Hz - Hp) / D
    a = (L / 2 + 0.35, -pe, Hp + 0.3 - pe * spd)
    b = (-L / 2 - 0.35, -pe, Hp + 0.3 - pe * spd)
    c = (-L / 2 - 0.35, D + pe, Hz + 0.3 + pe * spd)
    d = (L / 2 + 0.35, D + pe, Hz + 0.3 + pe * spd)
    strecha(S, a, b, c, d, R)
    # kolize (Havran): zadní a boční stěny, sloupy vpředu (do kůlny se dá vejít), střecha
    box(KOL, (0, D + 0.1, (z0 + Hz) / 2), (L + 0.3, 0.2, Hz), "zelezo", "k", R)
    for x in (-L / 2 - 0.1, L / 2 + 0.1):
        box(KOL, (x, D / 2, (z0 + Hz) / 2), (0.2, D, Hz), "zelezo", "k", R)
    for x in xs[1:-1]:
        box(KOL, (x, 0.0, Hp / 2), (0.2, 0.2, Hp), "zelezo", "k", R)
    box(KOL, (0, D / 2, (Hp + Hz) / 2 + 0.35), (L + 0.6, D + 0.8, 0.25), "zelezo", "k", R)
    return S, [], KOL


# ------------------------------------------------------------------ materiály (fotky jako hrad, zmenšené – textury)
TMP = tempfile.mkdtemp(prefix="stodoly_")
MATS = {}
JMENA = {"prkno": "prkno_stodoly", "prkno_vrata": "prkno_vrata", "tram": "tram_stodoly", "rez": "rez_drevo",
         "sindel": "sindel_stodoly", "kamen": "kamen_podezdivka", "zelezo": "zelezo_kovani"}


def _obraz(foto, sfx, px, jas, jm, non_color=False):
    im = bpy.data.images.load(os.path.join(TEXDIR, "%s_%s.jpg" % (foto, sfx)))
    if im.size[0] > px: im.scale(px, px)
    if abs(jas - 1.0) > 0.01:   # jas jako hrad (TEX), zapečený do fotky (sRGB: jas lineárně → mocnina 1/2,2)
        p = np.empty(len(im.pixels), dtype=np.float32); im.pixels.foreach_get(p); p = p.reshape(-1, 4)
        p[:, :3] = np.clip(p[:, :3] * (jas ** (1 / 2.2)), 0, 1); im.pixels.foreach_set(p.ravel())
    fn = os.path.join(TMP, jm + ".jpg")
    im.filepath_raw = fn; im.file_format = "JPEG"; im.save()
    im.name = jm
    if non_color: im.colorspace_settings.name = "Non-Color"
    return im


def material(k):
    if k in MATS: return MATS[k]
    jm = JMENA[k]; m = bpy.data.materials.new(jm); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    e = C["materialy"][k]
    bs.inputs["Roughness"].default_value = 0.92
    if k == "zelezo":
        bs.inputs["Base Color"].default_value = (*e, 1); bs.inputs["Metallic"].default_value = 0.7; bs.inputs["Roughness"].default_value = 0.6
    else:
        foto, vel, jas = e; T = C["textury"]
        atl = foto == "prkna_atlas"
        a = nt.nodes.new("ShaderNodeTexImage"); a.image = _obraz(foto, "Diffuse", T["atlas_px"] if atl else T["albedo_px"], jas, jm + "_albedo")
        nt.links.new(a.outputs["Color"], bs.inputs["Base Color"])
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = _obraz(foto, "nor_gl", T["atlas_normala_px"] if atl else T["normala_px"], 1.0, jm + "_normal", True)
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    MATS[k] = m
    return m


def objekt(S, jm, posun, s_uv=True):
    me = bpy.data.meshes.new(jm)
    me.from_pydata([tuple(v - posun) for v in S.v], [], S.f)
    if s_uv:
        uvl = me.uv_layers.new(name="UVMap")
        flat = [c for f in S.uv for uv in f for c in uv]
        uvl.data.foreach_set("uv", flat)
        klice = sorted(set(S.m))
        for k in klice: me.materials.append(material(k))
        me.polygons.foreach_set("material_index", [klice.index(k) for k in S.m])
    me.validate(); me.update()
    o = bpy.data.objects.new(jm, me); bpy.context.scene.collection.objects.link(o)
    return o


def export(objs, cesta, s_mat=True):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=cesta, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                              export_image_format="JPEG", export_materials="EXPORT" if s_mat else "NONE")


def _aabb(vs):
    return [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]


# ------------------------------------------------------------------ stavba
def postav(mid):
    m = C["modely"][mid]; R = random.Random(m["seed"])
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    S, kridla, KOL = (stodola if m["druh"] == "stodola" else kolna)(m, R)
    hlidac_strechy(mid, [S] + [k[1] for k in kridla])
    if kridla:   # i otevřená vrata (pohyb_mista.json stodoly: ven o uhel_deg) nesmí projít střechou
        uh = math.radians(json.load(open(os.path.join(K, "pravidla/svet/pohyb_mista.json")))["stodoly"]["uhel_deg"])
        otev = []
        for strana, Kr, pant in kridla:
            O_ = Sit(); r = -uh if strana == "L" else uh
            cr, sr = math.cos(r), math.sin(r)
            for f, tg in zip(Kr.f, Kr.tag):
                pts = []
                for i in f:
                    d_ = Kr.v[i] - pant
                    pts.append(pant + Vector((d_.x * cr - d_.y * sr, d_.x * sr + d_.y * cr, d_.z)))
                O_.plocha(pts, [(0, 0)] * len(pts), "zelezo", tg)
            otev.append(O_)
        hlidac_strechy(mid + " (vrata otevřená)", [S] + otev)
    # viditelný model vystředěný na pivot kolize z katalogu (predmety_h.json dily.kolize.pivot = střed obalu Havrana):
    # hra: kolize (souřadnice Blenderu) + pivot = model
    vse = S.v + [v for k in kridla for v in k[1].v]
    lo, hi = _aabb(vse)
    py = (lo[1] + hi[1]) / 2
    kat = os.path.join(K, "hra/modely/predmety_h.json")
    if os.path.exists(kat):
        pv = json.load(open(kat)).get(mid, {}).get("dily", {}).get("kolize", {}).get("pivot")
        if pv:
            print("PIVOT %s katalog %.3f, střed obalu %.3f" % (mid, pv[2], py))
            py = pv[2]
    posun = Vector((0.0, py, 0.0))
    obs = [objekt(S, mid, posun)]
    for strana, Kr, pant in kridla:
        o = objekt(Kr, "%s_Dvere_%s" % (m["uzel"], strana), pant)
        o.location = pant - posun
        obs.append(o)
    ko = objekt(KOL, mid + "_kolize", Vector(), s_uv=False)
    export(obs, os.path.join(OUT, mid + ".glb"))
    export([ko], os.path.join(OUT, mid + "_kolize.glb"), s_mat=False)
    lo, hi = _aabb([v - posun for v in vse])
    tri = sum(len(f) - 2 for f in S.f) + sum(len(f) - 2 for k in kridla for f in k[1].f)
    print("STODOLY %s: troj %d, křídel %d, obal hry x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (
        mid, tri, len(kridla), lo[0], hi[0], lo[2], hi[2], -hi[1], -lo[1]), flush=True)


def uklid(mid):
    """Starý model Havrana: střední stupeň, vytažené textury jeho materiálů, kopie v modely/stavby_h (ves.gd bere stavby_h
    přednostně – zůstala by tam stará stodola) a jejich importy."""
    pryc = [os.path.join(OUT, mid + "_stredni.glb")]
    for mat in ("kamen_patky", "prkna_stodola", "prkna_vrata", "sindel_stodola", "tram_stodola"):
        for sf in ("albedo", "normal"):
            pryc.append(os.path.join(OUT, "%s_%s_%s.jpg" % (mid, mat, sf)))
    SH = os.path.join(K, "hra/modely/stavby_h")
    pryc += [os.path.join(SH, mid + ".glb"), os.path.join(SH, mid + "_stredni.glb")]
    for mat in ("kamen_patky", "prkna_stodola", "prkna_vrata", "sindel_stodola", "tram_stodola"):
        for sf in ("albedo", "normal"):
            pryc.append(os.path.join(SH, "%s_%s_%s.jpg" % (mid, mat, sf)))
    n = 0
    for f in pryc:
        for g in (f, f + ".import"):
            if os.path.exists(g): os.remove(g); n += 1
        for g in glob.glob(os.path.join(K, "hra/.godot/imported", os.path.basename(f) + "-*")):
            os.remove(g)
    if n: print("STODOLY úklid %s: smazáno %d starých souborů" % (mid, n))


if __name__ == "__main__":
    ids = [a for a in sys.argv[2:] if not a.startswith("-")] or [k for k in C["modely"] if isinstance(C["modely"][k], dict)]
    os.makedirs(OUT, exist_ok=True)
    try:
        for mid in ids:
            postav(mid)
            uklid(mid)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("STODOLY OK")
