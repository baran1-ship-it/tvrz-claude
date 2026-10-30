"""Návrhy dvojhradu Puchart ze dat (pravidla/svet/hrady_navrhy.json) – stavebnice Havrana (blender/havran/lib.py, kit.py).

Zdi stojí na skutečném (upraveném) terénu: pata pod nejnižším bodem, koruna stupňovitě po terénu (KCD: hradby na
svahu stoupají po stupních). Materiály = fotografie Poly Haven (blender/tex), UV v metrech přepočtené na velikost fotky.
Výstup: hra/modely/hrady/<navrh>.glb (+ spolecne_A.glb, spolecne_B.glb).
  /opt/bl/bin/python blender/hrady.py <koren_puchartu> [id_navrhu ...]
"""
import sys, os, json, math
K = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.join(K, "blender", "havran"))
import numpy as np
import bpy
from mathutils import Vector, Matrix
import lib
import kit
from lib import Part, M, R, jit, frame

lib.GAME = True       # střechy jako deska s fotkou šindele (hra), ne jednotlivé šindele
DETAIL = True         # False = dálková verze (*_daleko.glb): jen hmoty, střechy, tmavá okna – bez kování, prken, trámků
D = json.load(open(os.path.join(K, "pravidla/svet/hrady_navrhy.json")))
VI = json.load(open(os.path.join(K, "hra/data/vysek.json")))
HH = np.fromfile(os.path.join(K, "hra/data/vysek.r16"), "<u2").reshape(VI["vyska"], VI["sirka"]).astype(np.float64) / 200 + 300 - VI["pocatek_H"]

def ter(x, z):
    c = min(max(x - VI["x0_hra"], 0), VI["sirka"] - 1.001); r = min(max(z - VI["z0_hra"], 0), VI["vyska"] - 1.001)
    c0, r0 = int(c), int(r); fc, fr = c - c0, r - r0
    a, b, cc, d = HH[r0, c0], HH[r0, c0 + 1], HH[r0 + 1, c0], HH[r0 + 1, c0 + 1]
    return float((a * (1 - fc) + b * fc) * (1 - fr) + (cc * (1 - fc) + d * fc) * fr)

def ter_rozsah(pts, krok=1.0):
    """min a max terénu pod polygonem / úsečkami (vzorky po krocích po obvodu a uvnitř)."""
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    v = [ter(x, z) for x in np.arange(min(xs), max(xs) + 0.01, krok) for z in np.arange(min(zs), max(zs) + 0.01, krok)]
    return min(v), max(v)

V3 = lambda x, y, z: Vector((x, y, z))
UP = Vector((0, 1, 0))

def baze(d):
    """lokální x podél d (vodorovně), y nahoru, z ven (vpravo od směru)."""
    d = Vector((d[0], 0, d[1])).normalized()
    z = d.cross(UP).normalized()
    return Matrix((d, UP, z)).transposed()

_kit_window = kit.stone_window; _kit_door = kit.doorway; _kit_deck = kit.deck; _ht = lib.half_timber; _plank = kit.plank
def _okno_daleko(P, m, w=0.6, h=0.9, depth=0.7, fill=None, **k):
    P.box(m @ M((0, h / 2, 0.03)), (w, h, 0.08), "tma"); return (-w / 2, w / 2, 0, h)
def _dvere_daleko(P, m, kind="hlavni", w=1.1, h=2.2, depth=0.7, **k):
    P.box(m @ M((0, h / 2, 0.03)), (w, h, 0.1), "tma")
def _deck_daleko(P, a, b, hw, mat="prkna_ven", **k):
    a = Vector(a); b = Vector(b); d = b - a
    P.box(M((a + b) / 2, basis=frame(d)), (hw * 2, 0.08, d.length), mat)
def nastav_detail(ano):
    global DETAIL
    DETAIL = ano
    kit.stone_window = _kit_window if ano else _okno_daleko
    kit.doorway = _kit_door if ano else _dvere_daleko
    kit.deck = _kit_deck if ano else _deck_daleko
    lib.half_timber = _ht if ano else (lambda *a, **k: None)
    kit.plank = _plank if ano else (lambda *a, **k: None)

BRANY = []   # (práh vnějšího líce průjezdu, výška podlahy) – mosty se napojují na nejbližší

# ------------------------------------------------------------------ zdi
def zed(P, a, b, t, h, mat="zdivo", krok=3.5, pata=2.0, cimburi=True, koruna=None, okna=0):
    """Hradba a->b (x, z). Koruna = terén + h po stupních (zaokrouhleno na 0,5 m), nebo pevně koruna (y).
    Vrací seznam (s0, s1, y_koruny) úseků pro ochoz."""
    a = Vector((a[0], 0, a[1])); b = Vector((b[0], 0, b[1])); L = (b - a).length; d = (b - a) / L
    n = max(1, math.ceil(L / krok)); out = []
    for i in range(n):
        s0, s1 = i * L / n, (i + 1) * L / n
        vz = [ter(*(a + d * s).xz) for s in np.linspace(s0, s1, 5)]
        y0 = min(vz) - pata
        y1 = koruna if koruna is not None else round((max(vz) + h) * 2) / 2
        c = a + d * ((s0 + s1) / 2)
        P.box(M((c.x, (y0 + y1) / 2, c.z), basis=frame(d)), (t, y1 - y0, s1 - s0 + t * 0.9), mat)
        out.append((s0, s1, y1))
        if cimburi:
            # cimbuří na vnější polovině koruny (+strana = vpravo od směru)
            out_n = d.cross(UP).normalized()
            k = s0 + 0.5
            while k < s1 - 0.6:
                p = a + d * (k + 0.45) + out_n * (t * 0.3)
                P.box(M((p.x, y1 + 0.55, p.z), basis=frame(d)), (t * 0.4, 1.1, 0.9), mat)
                k += 1.8
    return out

def ochoz_kryty(P, a, b, t, useky, sirka=1.4):
    """Krytý ochoz NA KORUNĚ hradby (Míša 30. 10.: ochozy nedomyšlené): chodí se po koruně za cimbuřím (vnější
    40 % tloušťky), sloupky stojí na vnitřní hraně koruny, pultová šindelová stříška od cimbuří k vnitřní hraně,
    nízké zábradlí na vnitřní hraně (KCD Rataje/Trosky)."""
    a = Vector((a[0], 0, a[1])); b = Vector((b[0], 0, b[1])); d = (b - a).normalized()
    vn = -d.cross(UP).normalized()          # dovnitř hradu
    hrana = vn * (t * 0.5 - 0.1)            # vnitřní hrana koruny
    for s0, s1, y in useky:
        p0 = a + d * s0; p1 = a + d * s1
        P.box(M((p0 + p1) / 2 + vn * (t * 0.1) + UP * (y + 0.04), basis=frame(d)), (t * 0.8, 0.08, (p1 - p0).length + 0.05), "prkna_ven")   # pochozí prkna
        if DETAIL:
            k = s0 + 0.3
            while k < s1 - 0.1:
                q = a + d * k + hrana
                P.beam(q + UP * (y + 0.05), q + UP * (y + 2.15), 0.16, 0.16, "dub", j=0.3)
                k += 2.4
            P.beam(p0 + hrana + UP * (y + 1.0), p1 + hrana + UP * (y + 1.0), 0.1, 0.12, "dub", j=0.4)    # zábradlí
            P.beam(p0 + hrana + UP * (y + 2.15), p1 + hrana + UP * (y + 2.15), 0.18, 0.2, "dub")           # vaznice
        lib.shingle_roof(P, p0 + hrana + vn * 0.35 + UP * (y + 2.1), p1 + hrana + vn * 0.35 + UP * (y + 2.1),
                         p1 - vn * (t * 0.5) + UP * (y + 2.75), p0 - vn * (t * 0.5) + UP * (y + 2.75), ridge=False)

# ------------------------------------------------------------------ střechy
def strecha_jehlan(P, rohy, y, vyska, presah=0.5):
    c = sum((Vector((p[0], 0, p[1])) for p in rohy), Vector()) / len(rohy)
    apex = c + UP * (y + vyska)
    pts = []
    for p in rohy:
        v = Vector((p[0], 0, p[1])); v = v + (v - c).normalized() * presah; pts.append(v + UP * y)
    for i in range(len(pts)):
        lib.shingle_roof(P, pts[i], pts[(i + 1) % len(pts)], apex, apex, ridge=False)
    P.rod(apex - UP * 0.2, apex + UP * 1.4, 0.04, 6, "zelezo")           # žerď s praporkem
    P.ball(apex + UP * 0.1, (0.18, 0.22, 0.18), "zelezo", seg=8, rings=5)

def strecha_sedlova(P, a, b, hloubka, y, vyska, presah=0.5, stity="drevo"):
    """Sedlová střecha nad obdélníkem s osou a->b (hřeben podél osy) a štíty na koncích."""
    a = Vector((a[0], 0, a[1])); b = Vector((b[0], 0, b[1])); d = (b - a).normalized(); s = d.cross(UP).normalized()
    a2, b2 = a - d * presah, b + d * presah
    w = hloubka / 2 + presah
    eL1, eR1 = a2 + s * w + UP * y, b2 + s * w + UP * y
    eL2, eR2 = b2 - s * w + UP * y, a2 - s * w + UP * y
    rA, rB = a2 + UP * (y + vyska), b2 + UP * (y + vyska)
    lib.shingle_roof(P, eL1, eR1, rB, rA)
    lib.shingle_roof(P, eL2, eR2, rA, rB)
    for e, f, r in ((a + s * (hloubka / 2), a - s * (hloubka / 2), a), (b - s * (hloubka / 2), b + s * (hloubka / 2), b)):
        if stity == "drevo":
            # bedněný štít ze svislých prken
            k = 0.0; L = (f - e).length; dd = (f - e).normalized()
            while k < L:
                x = e + dd * (k + 0.13); hh = vyska * (1 - abs((k + 0.13) - L / 2) / (L / 2))
                if hh > 0.05:
                    kit.plank(P, x + UP * y, x + UP * (y + hh), 0.25, 0.04, "prkna_ven", up=(r - (a + b) / 2).normalized(), wear=0.5)
                k += 0.26
        else:
            P.tri(e + UP * y, f + UP * y, r + UP * (y + vyska), 0.6, "zdivo")

def strecha_valba(P, a, b, hloubka, y, vyska, presah=0.5):
    a = Vector((a[0], 0, a[1])); b = Vector((b[0], 0, b[1])); d = (b - a).normalized(); s = d.cross(UP).normalized()
    L = (b - a).length; w = hloubka / 2 + presah
    zk = min(L / 2 - 0.1, w)     # zkrácení hřebene
    c1 = a - d * presah; c2 = b + d * presah
    e = [c1 + s * w, c2 + s * w, c2 - s * w, c1 - s * w]
    r1 = a + d * (zk - presah) + UP * (y + vyska); r2 = b - d * (zk - presah) + UP * (y + vyska)
    E = [p + UP * y for p in e]
    lib.shingle_roof(P, E[0], E[1], r2, r1)
    lib.shingle_roof(P, E[2], E[3], r1, r2)
    lib.shingle_roof(P, E[1], E[2], r2, r2, ridge=False)
    lib.shingle_roof(P, E[3], E[0], r1, r1, ridge=False)

# ------------------------------------------------------------------ věž
def vez(P, stred, rozmer, vyska, strecha="jehlan", yaw_d=(1, 0), brana=False, yf=None):
    cx, cz = stred; w, dpt = rozmer
    d = Vector((yaw_d[0], 0, yaw_d[1])).normalized(); s = d.cross(UP).normalized()
    c = Vector((cx, 0, cz))
    rohy = [c + d * (w / 2) * i + s * (dpt / 2) * j for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    lo, hi = ter_rozsah([(p.x, p.z) for p in rohy])
    y0 = lo - 2.0; y1 = hi + vyska
    if brana:
        # PRŮJEZD skrz věž (Míša 30. 10.: brána musí mít průchod): osa průjezdu = s (ven = -s), šířka pw, výška ph
        pw, ph = 3.2, 4.2
        yf = round(ter(c.x, c.z) * 4) / 4 if yf is None else yf
        for sg in (-1, 1):   # boční pilíře
            L = (w - pw) / 2; cc = c + d * sg * (pw / 2 + L / 2)
            P.box(M((cc.x, (y0 + y1) / 2, cc.z), basis=frame(d)), (dpt, y1 - y0, L), "zdivo")
        P.box(M((c.x, (yf + ph + 0.6 + y1) / 2, c.z), basis=frame(d)), (dpt, y1 - yf - ph - 0.6, pw + 0.02), "zdivo")   # nad průjezdem
        P.box(M((c.x, (y0 + yf) / 2, c.z), basis=frame(d)), (dpt, yf - y0, pw + 0.02), "zdivo")                          # pod podlahou
        # valená klenba průjezdu (segmenty) a dlažba
        for k in range(7):
            a0 = math.pi * k / 7; a1 = math.pi * (k + 1) / 7
            for sg2 in (0,):
                pa = c + d * (math.cos(a0) * pw / 2) + UP * (yf + ph - 0.6 + math.sin(a0) * 0.6 * 1.0)
                pb = c + d * (math.cos(a1) * pw / 2) + UP * (yf + ph - 0.6 + math.sin(a1) * 0.6 * 1.0)
                mid = (pa + pb) / 2; dl = (pb - pa)
                P.box(M(mid + UP * 0.12, basis=frame(s, up=dl.cross(s).normalized() if dl.length > 0 else UP)), (0.25, 0.3, dpt), "kvadr")
        P.box(M(c + UP * (yf - 0.05), basis=frame(d)), (dpt, 0.1, pw), "kvadr_sedy")
        # portály na obou lících a vrata (vnitřní strana otevřená)
        for sg in (-1, 1):
            f = c + s * sg * (dpt / 2)
            m = M(f + UP * yf, basis=Matrix((d * sg, UP, s * sg)).transposed())
            kit.doorway(P, m, kind="hlavni", w=pw, h=ph, depth=0.9, top="lomeny", leaf=(sg > 0), open_deg=80, double=True, open2=-80, inner=False)
        BRANY.append((c - s * (dpt / 2), yf))   # práh vnějšího líce – sem vede most
    else:
        P.box(M((c.x, (y0 + y1) / 2, c.z), basis=frame(d)), (dpt, y1 - y0, w), "zdivo")
    # nároží z větších kamenů (KCD: kvádrová nároží) – střídavě
    for p in rohy:
        y = hi - 0.5
        k = 0
        while y < y1 - 0.6:
            dd = d if k % 2 else s
            o = (p - c).normalized()
            q = p - o * 0.25
            P.box(M((q.x, y + 0.2, q.z), basis=frame(dd)), (0.62, 0.38, 0.95), "kvadr")
            y += 0.42; k += 1
    # střílny a okna na čtyřech stranách
    for strana, nrm, L in ((0, s, w), (1, -s, w), (2, d, dpt), (3, -d, dpt)):
        osa = d if strana < 2 else s
        f = c + nrm * ((dpt if strana < 2 else w) / 2)
        for y in np.arange(hi + 4.0, y1 - 3.0, 4.5):
            m = M(f + UP * y, basis=Matrix((osa * (1 if strana in (0, 3) else -1), UP, nrm)).transposed())
            if y > y1 - 8:
                kit.stone_window(P, m, w=0.55, h=0.95, depth=0.8, fill="mriz")
            else:
                P.box(m @ M((0, 0.6, 0.02)), (0.16, 1.2, 0.12), "tma")
    top = y1
    if strecha.startswith("stanova_hurdice"):
        # dřevěné patro (hurdice) s přesahem na krakorcích
        o = 0.7
        hr = [c + d * (w / 2 + o) * i + s * (dpt / 2 + o) * j for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        for p in rohy:   # krakorce
            for t in np.linspace(0.15, 0.85, 3):
                pass
        for i in range(4):
            p0, p1 = hr[i], hr[(i + 1) % 4]
            P.beam(p0 + UP * (top - 0.15), p1 + UP * (top - 0.15), 0.3, 0.3, "dub")
            # krakorce pod přesahem
            for t in np.linspace(0.1, 0.9, 4):
                q = p0.lerp(p1, t)
                inn = q + (c - q).normalized() * 1.2
                P.beam(inn + UP * (top - 1.2), q + UP * (top - 0.15), 0.22, 0.22, "dub")
            nrm = (p0.lerp(p1, 0.5) - c).normalized()
            P.box(M(p0.lerp(p1, 0.5) + UP * (top + 1.3), basis=frame(p1 - p0)), (0.2, 2.6, (p1 - p0).length), "omitka")
            lib.half_timber(P, p0 + nrm * 0.1, p1 + nrm * 0.1, nrm, top, top + 2.6, bay=1.3, mat="hraz")
            # okénka v hurdici
            for t in (0.3, 0.7):
                q = p0.lerp(p1, t) + nrm * 0.12
                P.box(M(q + UP * (top + 1.4), basis=frame(p1 - p0)), (0.1, 0.6, 0.5), "tma")
        top += 2.6
        strecha_jehlan(P, [(p.x, p.z) for p in hr], top, max(w, dpt) * 1.05, presah=0.45)
    elif strecha == "jehlan":
        strecha_jehlan(P, [(p.x, p.z) for p in rohy], top, max(w, dpt) * 1.0, presah=0.4)
    elif strecha == "valba":
        a = c - d * (w / 2); b = c + d * (w / 2)
        strecha_valba(P, (a.x, a.z), (b.x, b.z), dpt, top, dpt * 0.75, presah=0.45)
    elif strecha == "sedlova_veze":
        a = c - d * (w / 2); b = c + d * (w / 2)
        strecha_sedlova(P, (a.x, a.z), (b.x, b.z), dpt, top, dpt * 0.8, presah=0.35, stity="kamen")
    return y1

# ------------------------------------------------------------------ budovy
def budova(P, a, b, hloubka, h_kamen, h_drevo=0.0, strecha="sedlova", typ="palac", okna_ven=True):
    """Obdélník s osou a->b. typ palac: kamenné přízemí s omítkou + hrázděné patro; hrazdena: kamenná podezdívka +
    hrázdění; roubena: srub z trámů; pristresek: sloupy a pultová střecha."""
    A = Vector((a[0], 0, a[1])); B = Vector((b[0], 0, b[1])); L = (B - A).length; d = (B - A) / L; s = d.cross(UP).normalized()
    rohy = [A + s * hloubka / 2, B + s * hloubka / 2, B - s * hloubka / 2, A - s * hloubka / 2]
    lo, hi = ter_rozsah([(p.x, p.z) for p in rohy])
    podl = hi + 0.3; y0 = lo - 1.0
    c = (A + B) / 2
    t = 1.1 if typ == "palac" else 0.5
    if typ == "pristresek":
        for k in np.linspace(0, L, max(2, int(L / 3) + 1)):
            for o in (hloubka / 2 - 0.2, -hloubka / 2 + 0.2):
                p = A + d * k + s * o
                P.beam(p + UP * (ter(p.x, p.z) - 0.3), p + UP * (podl + h_kamen - (0.6 if o < 0 else 0)), 0.22, 0.22, "dub", j=0.5)
        E1, E2 = A - s * (hloubka / 2 + 0.4), B - s * (hloubka / 2 + 0.4)
        lib.shingle_roof(P, E1 + UP * (podl + h_kamen - 0.6), E2 + UP * (podl + h_kamen - 0.6), B + s * (hloubka / 2) + UP * (podl + h_kamen + 0.2), A + s * (hloubka / 2) + UP * (podl + h_kamen + 0.2))
        return podl
    # spodek (kámen) – u roubené a hrázděné jen podezdívka
    yk = podl + (h_kamen if typ == "palac" else 0.6)
    for p0, p1 in zip(rohy, rohy[1:] + rohy[:1]):
        dd = (p1 - p0).normalized()
        cc = (p0 + p1) / 2 - dd.cross(UP).normalized() * 0.0
        P.box(M((cc.x, (y0 + yk) / 2, cc.z), basis=frame(dd)), (t, yk - y0, (p1 - p0).length + t), "zdivo")
    if typ == "palac":
        # omítka na horní části kamenného patra (KCD: palác omítnutý, kámen u paty a nároží)
        for p0, p1 in zip(rohy, rohy[1:] + rohy[:1]):
            dd = (p1 - p0).normalized(); nn = -dd.cross(UP).normalized()
            cc = (p0 + p1) / 2 + nn * (t / 2 + 0.02)
            P.box(M((cc.x, (podl + 1.2 + yk) / 2, cc.z), basis=frame(dd)), (0.04, yk - podl - 1.2, (p1 - p0).length - 0.6), "omitka")
            # okna kamenného patra
            Lw = (p1 - p0).length
            for k in np.arange(2.5, Lw - 1.5, 3.2):
                f = p0 + dd * k + nn * (t / 2 + 0.06)
                kit.stone_window(P, M(f + UP * (podl + h_kamen * 0.45), basis=Matrix((dd, UP, nn)).transposed()), w=0.7, h=1.2, depth=0.9, fill="sklo")
        # vstup
        f = A + d * (L * 0.5) - s * (hloubka / 2 + t / 2 + 0.05)
        kit.doorway(P, M(f + UP * podl, basis=Matrix((-d, UP, -s)).transposed()), kind="hlavni", w=1.4, h=2.6, depth=1.1, open_deg=25)
    ytop = yk
    if h_drevo > 0 or typ in ("hrazdena", "roubena"):
        hd = h_drevo if h_drevo > 0 else h_kamen
        o = 0.35 if typ == "palac" else 0.0      # vyložené patro
        R2 = [p + (p - c).normalized() * o for p in rohy]
        for p0, p1 in zip(R2, R2[1:] + R2[:1]):
            dd = (p1 - p0).normalized(); nn = -dd.cross(UP).normalized()
            if typ == "roubena":
                y = ytop
                while y < ytop + hd:
                    P.beam(p0 - dd * 0.3 + UP * (y + 0.12), p1 + dd * 0.3 + UP * (y + 0.12), 0.24, 0.26, "dub", j=0.6)
                    y += 0.26
            else:
                cc = (p0 + p1) / 2
                P.box(M((cc.x, ytop + hd / 2, cc.z), basis=frame(dd)), (0.2, hd, (p1 - p0).length), "omitka")
                Lw = (p1 - p0).length
                okna = [(k - 0.35, k + 0.35, 0.9, 1.9) for k in np.arange(1.6, Lw - 1.0, 2.6)]
                lib.half_timber(P, p0 + nn * 0.1, p1 + nn * 0.1, nn, ytop, ytop + hd, openings=okna, bay=1.2, mat="hraz")
                for o0, o1, ya, yb in okna:
                    q = p0 + dd * ((o0 + o1) / 2) + nn * 0.11
                    P.box(M(q + UP * (ytop + (ya + yb) / 2), basis=frame(dd)), (0.05, yb - ya, o1 - o0), "tma")
        if o > 0:   # trámy vyložení
            for p0, p1 in zip(rohy, rohy[1:] + rohy[:1]):
                dd = (p1 - p0).normalized(); nn = -dd.cross(UP).normalized()
                for k in np.arange(0.5, (p1 - p0).length, 1.2):
                    q = p0 + dd * k
                    P.beam(q - nn * 0.3 + UP * (ytop - 0.1), q + nn * (o + 0.15) + UP * (ytop - 0.1), 0.2, 0.22, "dub")
        ytop += hd
        rohy = R2
    a2 = (rohy[0] + rohy[3]) / 2; b2 = (rohy[1] + rohy[2]) / 2
    hl = (rohy[0] - rohy[3]).length
    if strecha == "sedlova":
        strecha_sedlova(P, (a2.x, a2.z), (b2.x, b2.z), hl, ytop, hl * 0.62, presah=0.5)
    elif strecha == "valba":
        strecha_valba(P, (a2.x, a2.z), (b2.x, b2.z), hl, ytop, hl * 0.6)
    return podl

# ------------------------------------------------------------------ spojení
def most(P, a, b, vyska):
    A = Vector((a[0], 0, a[1])); B = Vector((b[0], 0, b[1])); d = (B - A).normalized(); s = d.cross(UP).normalized()
    ya = ter(*a) + 0.3; yb = ter(*b) + 0.3
    n = max(2, int((B - A).length / 4))
    for i in range(n + 1):
        p = A.lerp(B, i / n); y = ya + (yb - ya) * i / n
        if 0 < i < n:
            for o in (-1.2, 1.2):   # kozy
                q = p + s * o
                P.beam(q + UP * (ter(q.x, q.z) - 0.5), q + UP * y, 0.28, 0.28, "dub", j=0.4)
                P.beam(q + UP * (ter(q.x, q.z) + 0.2) + d * 1.2, q + UP * (y - 0.6), 0.18, 0.18, "dub", j=0.4)
            P.beam(p - s * 1.4 + UP * (y - 0.3), p + s * 1.4 + UP * (y - 0.3), 0.26, 0.26, "dub")
    kit.deck(P, A + UP * ya, B + UP * yb, 1.3, beams=(-0.9, 0.0, 0.9))
    for o in (-1.35, 1.35):   # zábradlí
        P.beam(A + s * o + UP * (ya + 1.05), B + s * o + UP * (yb + 1.05), 0.12, 0.12, "dub", j=0.5)
        for i in range(n + 1):
            p = A.lerp(B, i / n) + s * o; y = ya + (yb - ya) * i / n
            P.beam(p + UP * y, p + UP * (y + 1.1), 0.12, 0.12, "dub", j=0.5)

def kryta_chodba(P, osa, sirka=2.4, pilire_po=6.0):
    """Krytá dřevěná chodba na kamenných pilířích po svahu: podlaha po stupních (schodiště), bedněné stěny s okénky,
    sedlová šindelová stříška."""
    pts = [Vector((p[0], 0, p[1])) for p in osa]
    for A, B in zip(pts, pts[1:]):
        L = (B - A).length; d = (B - A) / L; s = d.cross(UP).normalized()
        n = max(1, math.ceil(L / pilire_po))
        for i in range(n):
            p0 = A + d * (L * i / n); p1 = A + d * (L * (i + 1) / n)
            y0 = max(ter(p0.x, p0.z), ter(p1.x, p1.z) - 1.0) + 2.5
            y1 = max(ter(p1.x, p1.z) + 2.5, y0 - 4.0) if i < n - 1 else ter(p1.x, p1.z) + 2.5
            # pilíř
            pm = p1
            P.box(M((pm.x, (ter(pm.x, pm.z) - 1.5 + min(y0, y1)) / 2, pm.z), basis=frame(d)), (sirka + 0.4, min(y0, y1) - ter(pm.x, pm.z) + 1.5, 1.2), "zdivo")
            # podlaha: když klesá o víc než 0,6 m, schodiště
            if abs(y1 - y0) > 0.6:
                k = int(abs(y1 - y0) / 0.22)
                for j in range(k):
                    q0 = p0.lerp(p1, j / k); q1 = p0.lerp(p1, (j + 1) / k); y = y0 + (y1 - y0) * (j + 0.5) / k
                    P.box(M((q0 + q1) / 2 + UP * y, basis=frame(d)), (sirka, 0.12, (q1 - q0).length + 0.04), "prkna_ven")
            else:
                kit.deck(P, p0 + UP * y0, p1 + UP * y1, sirka / 2, beams=(-sirka / 2 + 0.2, 0.0, sirka / 2 - 0.2))
            # stěny a střecha
            for o in (-1, 1):
                e0 = p0 + s * o * sirka / 2; e1 = p1 + s * o * sirka / 2
                for t in np.linspace(0, 1, 4):
                    q = e0.lerp(e1, t); y = y0 + (y1 - y0) * t
                    P.beam(q + UP * (y - 0.1), q + UP * (y + 2.3), 0.16, 0.16, "dub", j=0.3)
                P.beam(e0 + UP * (y0 + 2.3), e1 + UP * (y1 + 2.3), 0.18, 0.18, "dub")
                # parapet z prken do 1,1 m, nad ním otevřené (výhled)
                P.box(M((e0 + e1) / 2 + UP * ((y0 + y1) / 2 + 0.55), basis=frame(e1 - e0 + UP * (y1 - y0))), (0.06, 1.1, (e1 - e0).length), "prkna_ven")
            eL = p0 + s * (sirka / 2 + 0.4) + UP * (y0 + 2.2); eR = p1 + s * (sirka / 2 + 0.4) + UP * (y1 + 2.2)
            rL = p0 + UP * (y0 + 3.3); rR = p1 + UP * (y1 + 3.3)
            lib.shingle_roof(P, eL, eR, rR, rL)
            lib.shingle_roof(P, p1 - s * (sirka / 2 + 0.4) + UP * (y1 + 2.2), p0 - s * (sirka / 2 + 0.4) + UP * (y0 + 2.2), rL, rR)

def palisada(P, obrys, vyska):
    pts = [Vector((p[0], 0, p[1])) for p in obrys] + [Vector((obrys[0][0], 0, obrys[0][1]))]
    for A, B in zip(pts, pts[1:]):
        L = (B - A).length; d = (B - A) / L
        k = 0.0
        while k < L:
            p = A + d * k; y = ter(p.x, p.z); r = R.uniform(0.13, 0.17); hh = vyska + R.uniform(-0.3, 0.3)
            P.lathe(M((p.x, y - 0.8, p.z)), [(r, 0), (r, hh + 0.8), (0.02, hh + 1.25)], 7, "dub", cap_bot=False)
            k += 0.3
        P.beam(A + UP * (ter(A.x, A.z) + 1.6), B + UP * (ter(B.x, B.z) + 1.6), 0.14, 0.18, "dub")   # vodorovná latě uvnitř


# ------------------------------------------------------------------ doplňky (vymakanost: život a měřítko jako v KCD)
def komin(P, x, z, y0, y1):
    P.box(M((x, (y0 + y1) / 2, z)), (0.95, y1 - y0, 0.95), "zdivo")
    P.box(M((x, y1 + 0.12, z)), (1.15, 0.24, 1.15), "kvadr")
    P.box(M((x, y1 + 0.3, z)), (0.55, 0.2, 0.55), "tma")

def pavlac(P, a, b, smer_ven, y, hloubka=1.5):
    if not DETAIL:
        return
    """Dřevěná pavlač na sloupech podél líce a->b ve výšce y (patro), zábradlí, stříška."""
    A = Vector((a[0], 0, a[1])); B = Vector((b[0], 0, b[1])); s = Vector((smer_ven[0], 0, smer_ven[1])).normalized()
    A2, B2 = A + s * hloubka, B + s * hloubka
    kit.deck(P, (A + A2) / 2 + UP * y, (B + B2) / 2 + UP * y, hloubka / 2, beams=(-hloubka / 2 + 0.15, hloubka / 2 - 0.15))
    L = (B - A).length; n = max(2, int(L / 2.4) + 1)
    for i in range(n):
        q = A2.lerp(B2, i / (n - 1))
        P.beam(q + UP * (ter(q.x, q.z) - 0.2), q + UP * (y + 2.6), 0.2, 0.2, "dub", j=0.4)
        P.beam(q + UP * (y + 1.0), q + UP * (y - 0.15), 0.1, 0.1, "dub")
        P.beam(q - s * 0.9 + UP * (y - 0.1), q + UP * (y - 0.9), 0.14, 0.14, "dub", j=0.3)   # vzpěra
    P.beam(A2 + UP * (y + 1.0), B2 + UP * (y + 1.0), 0.12, 0.12, "dub", j=0.5)
    for i in range(int(L / 0.18)):
        q = A2.lerp(B2, (i + 0.5) / int(L / 0.18))
        P.beam(q + UP * (y + 0.08), q + UP * (y + 0.95), 0.05, 0.05, "dub")
    lib.shingle_roof(P, A2 + s * 0.3 + UP * (y + 2.5), B2 + s * 0.3 + UP * (y + 2.5), B + UP * (y + 3.3), A + UP * (y + 3.3), ridge=False)

def studna(P, x, z):
    y = ter(x, z)
    P.lathe(M((x, y - 0.3, z)), [(1.05, 0), (1.05, 1.1), (0.75, 1.1), (0.75, 0.2)], 14, "kvadr")
    P.lathe(M((x, y + 0.05, z)), [(0.74, 0), (0.74, 0.02)], 12, "tma", cap_bot=False)
    for o in (-1, 1):
        P.beam(V3(x + o * 1.1, y - 0.2, z), V3(x + o * 1.1, y + 2.6, z), 0.18, 0.18, "dub", j=0.5)
    P.rod(V3(x - 1.2, y + 1.7, z), V3(x + 1.2, y + 1.7, z), 0.12, 8, "dub")
    strecha_sedlova(P, (x - 1.3, z), (x + 1.3, z), 1.8, y + 2.5, 1.0, presah=0.25)

def schody(P, a, b, y0, y1, sirka=1.2):
    A = Vector((a[0], 0, a[1])); B = Vector((b[0], 0, b[1])); d = (B - A).normalized()
    n = max(2, int((y1 - y0) / 0.22))
    for i in range(n):
        q0 = A.lerp(B, i / n); q1 = A.lerp(B, (i + 1) / n); y = y0 + (y1 - y0) * (i + 1) / n
        P.box(M((q0 + q1) / 2 + UP * (y - 0.06), basis=frame(d)), (sirka, 0.1, (q1 - q0).length + 0.05), "prkna_ven")
    for o in (-sirka / 2, sirka / 2):   # schodnice a podpěry
        so = d.cross(UP).normalized() * o
        P.beam(A + so + UP * (y0 - 0.1), B + so + UP * (y1 - 0.1), 0.08, 0.25, "dub", up=d.cross(UP))
        for t in (0.35, 0.7):
            q = A.lerp(B, t) + so
            P.beam(q + UP * (ter(q.x, q.z) - 0.2), q + UP * (y0 + (y1 - y0) * t - 0.2), 0.16, 0.16, "dub", j=0.4)

def prapor(P, vrch, smer=(1, 0), barva="prapor"):
    v = Vector(vrch); d = Vector((smer[0], 0, smer[1])).normalized()
    P.face([v + UP * 1.3, v + UP * 1.3 + d * 1.6 + UP * -0.15, v + UP * 0.75 + d * 1.5, v + UP * 0.65], barva)
    P.face([v + UP * 0.65, v + UP * 0.75 + d * 1.5, v + UP * 1.3 + d * 1.6 + UP * -0.15, v + UP * 1.3], barva)

def palisada_val(P, pts, vyska=2.6):
    pts = [Vector((p[0], 0, p[1])) for p in pts]
    for A, B in zip(pts, pts[1:]):
        L = (B - A).length; d = (B - A) / L; k = 0.0
        while k < L:
            p = A + d * k; y = ter(p.x, p.z); r = R.uniform(0.12, 0.16); hh = vyska + R.uniform(-0.25, 0.25)
            P.lathe(M((p.x, y - 0.6, p.z)), [(r, 0), (r, hh + 0.6), (0.02, hh + 1.0)], 6, "dub", cap_bot=False)
            k += 0.28 if DETAIL else 0.7
        P.beam(A + UP * (ter(A.x, A.z) + 1.5), B + UP * (ter(B.x, B.z) + 1.5), 0.12, 0.16, "dub")


def most_padaci(P, m):
    """Most podle terénu (hrady_navrhy.json spolecne.mosty): nástup na srovnané plošině (teren_upravy.py), pevná část
    na kozách nad příkopem/průrvou se sklonem k prahu brány, u brány padací most na řetězech (kit.drawbridge, spuštěný)."""
    A = Vector((m["od"][0], 0, m["od"][1])); B = Vector((m["do"][0], 0, m["do"][1]))
    yb = ter(B.x, B.z) + 0.12
    if BRANY:   # most končí na prahu průjezdu nejbližší brány, ve výšce jeho podlahy
        pr, yfl = min(BRANY, key=lambda g: (g[0] - B).length)
        if (pr - B).length < 15:
            B = Vector((pr.x, 0, pr.z)); yb = yfl
    d = (B - A).normalized()
    s = d.cross(UP).normalized(); w = m["sirka"]; Lp = m["padaci_m"]
    ya = max(ter(A.x, A.z) + 0.12, yb - (B - A).length * 0.12)   # nástup nejvýš 12 % pod prahem
    Bf = B - d * Lp
    L = (Bf - A).length
    yf = ya + (yb - ya) * (L / (B - A).length)
    n = max(2, int(L / 3.5))
    for i in range(n + 1):
        p = A.lerp(Bf, i / n); y = ya + (yf - ya) * i / n
        if 0 < i:
            for o in (-w / 2 + 0.2, w / 2 - 0.2):
                q = p + s * o; g = ter(q.x, q.z)
                if y - g > 0.6:
                    P.beam(q + UP * (g - 0.5), q + UP * (y - 0.25), 0.3, 0.3, "dub", j=0.4)
                    P.beam(q + UP * (g + 0.2) - d * min(1.5, (y - g) * 0.5), q + UP * (y - 0.6), 0.2, 0.2, "dub", j=0.4)
            P.beam(p - s * (w / 2 + 0.2) + UP * (y - 0.32), p + s * (w / 2 + 0.2) + UP * (y - 0.32), 0.28, 0.28, "dub")
    nd = max(1, int(L / 0.3))   # mostovka z prken napříč (souvislá, žádné díry)
    for i in range(nd):
        q0 = A.lerp(Bf, i / nd); q1 = A.lerp(Bf, (i + 1) / nd); y = ya + (yf - ya) * (i + 0.5) / nd
        P.box(M((q0 + q1) / 2 + UP * y, basis=frame(d)), (w, 0.07, (q1 - q0).length - 0.015), "prkna_ven")
    for o in (-w / 2 + 0.25, 0.0, w / 2 - 0.25):   # podélné trámy pod mostovkou
        P.beam(A + s * o + UP * (ya - 0.2), Bf + s * o + UP * (yf - 0.2), 0.26, 0.3, "dub")
    if ya - ter(A.x, A.z) > 0.4:   # nástupní kamenná plošina, když je most nad terénem
        P.box(M(A - d * 0.8 + UP * ((ya + ter(A.x, A.z) - 1.0) / 2), basis=frame(d)), (w + 0.6, ya - ter(A.x, A.z) + 1.0, 1.8), "kvadr")
    for o in (-w / 2 - 0.05, w / 2 + 0.05):   # zábradlí na pevné části
        P.beam(A + s * o + UP * (ya + 1.05), Bf + s * o + UP * (yf + 1.05), 0.12, 0.12, "dub", j=0.5)
        for i in range(n + 1):
            q = A.lerp(Bf, i / n) + s * o; y = ya + (yf - ya) * i / n
            P.beam(q + UP * y, q + UP * (y + 1.1), 0.12, 0.12, "dub", j=0.5)
    # padací most: osa otáčení na prahu brány, most vede do +z = směrem od brány
    dd = (Bf + UP * yf) - (B + UP * yb); dd_h = Vector((dd.x, 0, dd.z)).normalized()
    sklon = math.degrees(math.atan2(-(yf - yb), Lp))
    mb = M(B + UP * yb, basis=Matrix((-s, UP, dd_h)).transposed()) if DETAIL else None
    if mb is not None:
        oka = kit.drawbridge(P, mb, w=w - 0.2, L=Lp, angle=-sklon)
        for o in oka:   # řetězy k bráně (nad vrata)
            kit.chain(P, o, B + UP * (yb + 4.2) + (o - (B + UP * yb)).project(s), sag=0.15)
    else:
        P.box(M((B + Bf) / 2 + UP * ((yb + yf) / 2), basis=frame(Bf - B)), (w, 0.2, Lp), "prkna_ven")

# ------------------------------------------------------------------ materiály a export
TEX = {  # jméno materiálu Havrana -> (fotka, velikost_m, jas)
    "zdivo": ("castle_wall_slates", 2.5, 1.0), "kvadr": ("castle_wall_slates", 1.6, 1.12), "kvadr_sedy": ("castle_wall_slates", 1.6, 0.95),
    "omitka": ("plastered_stone_wall", 2.5, 1.0), "zdivo_omitka": ("plastered_stone_wall", 2.5, 0.95),
    "sindel": ("sindel", 1.5, 1.35), "sindel_hra": ("sindel", 1.5, 1.35),
    "dub": ("rough_wood", 0.5, 0.75), "hraz": ("rough_wood", 0.5, 0.6), "prkna_ven": ("wood_planks_grey", 1.5, 0.95),
    "okenice": ("wood_planks_grey", 1.5, 0.8), "dvere": ("wood_planks_grey", 1.5, 0.7),
}
MATS = {}
def material(jm):
    if jm in MATS: return MATS[jm]
    m = bpy.data.materials.new(jm); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    key = next((k for k in TEX if jm.startswith(k)), None)
    if jm in ("tma",):
        bs.inputs["Base Color"].default_value = (0.012, 0.01, 0.009, 1); bs.inputs["Roughness"].default_value = 1.0
    elif jm.startswith(("zelezo", "hreb", "kovani")) or "zelez" in jm:
        bs.inputs["Base Color"].default_value = (0.05, 0.048, 0.045, 1); bs.inputs["Metallic"].default_value = 0.8; bs.inputs["Roughness"].default_value = 0.6
    elif jm == "prapor":
        bs.inputs["Base Color"].default_value = (0.42, 0.05, 0.04, 1); bs.inputs["Roughness"].default_value = 0.9
    elif jm.startswith("sklo"):
        bs.inputs["Base Color"].default_value = (0.06, 0.08, 0.07, 1); bs.inputs["Roughness"].default_value = 0.15
    else:
        if key is None: key = "dub"
        foto, vel, jas = TEX[key]
        tdir = os.path.join(K, "blender", "tex")
        def img(sfx, non_color=False):
            im = bpy.data.images.load(os.path.join(tdir, f"{foto}_{sfx}.jpg"), check_existing=True)
            if non_color: im.colorspace_settings.name = "Non-Color"
            n = nt.nodes.new("ShaderNodeTexImage"); n.image = im; return n
        cn = img("Diffuse")
        if abs(jas - 1.0) > 0.01:
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1.0
            nt.links.new(cn.outputs["Color"], mx.inputs[6]); mx.inputs[7].default_value = (jas, jas, jas, 1.0)
            nt.links.new(mx.outputs[2], bs.inputs["Base Color"])
        else:
            nt.links.new(cn.outputs["Color"], bs.inputs["Base Color"])
        bs.inputs["Roughness"].default_value = 0.92   # mapy drsnosti ve hře nejsou (APK: −1/3 textur hradu), kámen/dřevo matné
        nn = img("nor_gl", True); nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(nn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
        m["vel"] = vel
    MATS[jm] = m
    return m

def uloz(parts, jmeno, kolize=False):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    coll = bpy.context.scene.collection
    if kolize:   # Havran: kolize z kvádrů (zdi, podlahy, mostovky, schody jako rampy), ne z jemné geometrie prken a zábradlí
        PK = Part("KOLIZE")
        for P in parts:
            for m, sz in P.cols: PK.box(m, sz, "kolize")
        parts = list(parts) + [PK]
    for P in parts:
        for mn in P.mats: lib.MAT[mn] = material(mn)
        ob = P.commit(coll)
        if ob is None: continue
        me = ob.data; uv = me.uv_layers[0].data
        for poly in me.polygons:
            vel = me.materials[poly.material_index].get("vel", 1.0) if me.materials[poly.material_index] else 1.0
            for li in poly.loop_indices:
                uv[li].uv = (uv[li].uv[0] / vel, uv[li].uv[1] / vel)
        for mo in list(ob.modifiers): ob.modifiers.remove(mo)   # bevel jen pro Cycles; ve hře ne
    out = os.path.join(K, "hra/modely/hrady"); os.makedirs(out, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, jmeno + ".glb"), export_format="GLB", export_yup=True,
                              export_apply=True, export_image_format="JPEG")
    tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
    print("ULOZENO", jmeno, "troj", tri, flush=True)

# ------------------------------------------------------------------ stavba
S = D["spolecne"]

def postav_A(P, extra=None):
    A = S["A"]; jadro = A["jadro"]
    # kurtina jádra kolem obdélníka (bez úseku, kde je palác – palác má vlastní zeď)
    hr = A["kurtina"]
    useky = []
    for i in range(4):
        a, b = jadro[i], jadro[(i + 1) % 4]
        u = zed(P, a, b, hr["tloustka"], hr["vyska"], cimburi=True)
        useky.append((a, b, u))
    for a, b, u in useky:
        ochoz_kryty(P, b, a, hr["tloustka"], [(((Vector((b[0], 0, b[1])) - Vector((a[0], 0, a[1]))).length - s1), ((Vector((b[0], 0, b[1])) - Vector((a[0], 0, a[1]))).length - s0), y) for s0, s1, y in u])
    v = A["veze"][0]
    vez(P, v["stred"], v["rozmer"], v["vyska"], v["strecha"], yaw_d=(jadro[1][0] - jadro[0][0], jadro[1][1] - jadro[0][1]), brana=False)
    for v in (extra or {}).get("veze", []):
        vez(P, v["stred"], v["rozmer"], v["vyska"], v["strecha"], yaw_d=(jadro[2][0] - jadro[1][0], jadro[2][1] - jadro[1][1]))
    p = A["palac"]
    budova(P, p["osa"][0], p["osa"][1], p["hloubka"], p["vyska_kamen"], p["vyska_drevo"], "sedlova", "palac")
    for bd in A["budovy"]:
        budova(P, bd["osa"][0], bd["osa"][1], bd["hloubka"], bd["vyska"], 0, "sedlova", bd["typ"])
    # palác: komíny, pavlač na straně nádvoří
    pa = Vector((p["osa"][0][0], 0, p["osa"][0][1])); pb = Vector((p["osa"][1][0], 0, p["osa"][1][1]))
    dpal = (pb - pa).normalized(); sp = dpal.cross(UP).normalized()
    stred_j = Vector((21.0, 0, 5.0))
    k_ven = -sp if (stred_j - (pa + pb) / 2).dot(-sp) > 0 else sp
    lo, hi = ter_rozsah([(q.x, q.z) for q in (pa, pb)])
    podl = hi + 0.3
    for t in (0.3, 0.75):
        q = pa.lerp(pb, t) - k_ven * 1.2
        komin(P, q.x, q.z, podl + 2.0, podl + p["vyska_kamen"] + p["vyska_drevo"] + p["hloubka"] * 0.62 + 1.2)
    pv = pa + k_ven * (p["hloubka"] / 2 + 0.35); pw = pb + k_ven * (p["hloubka"] / 2 + 0.35)
    pavlac(P, (pv.x + dpal.x * 1.5, pv.z + dpal.z * 1.5), (pw.x - dpal.x * 6, pw.z - dpal.z * 6), (k_ven.x, k_ven.z), podl + p["vyska_kamen"])
    studna(P, 17.0, 1.0)
    # schody na ochoz u západní zdi
    c1, c2 = Vector((jadro[0][0], 0, jadro[0][1])), Vector((jadro[3][0], 0, jadro[3][1]))
    dz = (c2 - c1).normalized(); dovnitr = (stred_j - (c1 + c2) / 2); dovnitr = (dovnitr - dz * dovnitr.dot(dz)).normalized()
    s0 = c1.lerp(c2, 0.35) + dovnitr * 2.2; s1 = c1.lerp(c2, 0.62) + dovnitr * 2.2
    schody(P, (s0.x, s0.z), (s1.x, s1.z), ter(s0.x, s0.z), useky[3][2][-1][2] if useky[3][2] else ter(s1.x, s1.z) + hr["vyska"])
    # palisáda na vnějším valu (NAVRH; hřeben valu z plánu atlasu)
    vv = [q for q in A.get("val_vnejsi", []) if Vector((q[0] - 21.0, 0, q[1] - 5.0)).length > 45]
    if len(vv) > 2:
        palisada_val(P, vv)
    # praporce na věžích
    v0 = A["veze"][0]
    prapor(P, (v0["stred"][0], ter(v0["stred"][0], v0["stred"][1]) + v0["vyska"] + 2.6 + max(v0["rozmer"]) * 1.05, v0["stred"][1]), (1, 0.3))
    # branská věž u brány (sever), most přes příkop
    br = A["brana"]
    vez(P, br["stred"], (5.5, 6.0), 12.0, "sedlova_veze", yaw_d=(-br["smer"][1], br["smer"][0]), brana=True)   # smer = ven z brány
    if (extra or {}).get("mosty_teren"):
        most_padaci(P, next(m for m in S["mosty"] if m["id"] == "A_hlavni"))
    else:
        s = Vector((br["smer"][0], 0, br["smer"][1])).normalized()
        m0 = Vector((br["stred"][0], 0, br["stred"][1])) + s * 3.5; m1 = m0 + s * 18
        most(P, (m0.x, m0.z), (m1.x, m1.z), 0)

def postav_B(P, extra=None):
    B = S["B"]
    v = B["vez"]; vy = (extra or {}).get("vez_vyska", v["vyska"]); vs = (extra or {}).get("vez_strecha", v["strecha"])
    vez(P, v["stred"], v["rozmer"], vy, vs, yaw_d=(1.0, 0.45))
    z = B["stitova_zed"]
    zed(P, z["osa"][0], z["osa"][1], z["tloustka"], z["vyska"], cimburi=True)
    k = B["kurtina"]
    for a, b in zip(k["osa"], k["osa"][1:]):
        u = zed(P, a, b, k["tloustka"], k["vyska"], cimburi=True)
        ochoz_kryty(P, b, a, k["tloustka"], [(((Vector((b[0], 0, b[1])) - Vector((a[0], 0, a[1]))).length - s1), ((Vector((b[0], 0, b[1])) - Vector((a[0], 0, a[1]))).length - s0), y) for s0, s1, y in u])
    p = B["palac"]
    podl = budova(P, p["osa"][0], p["osa"][1], p["hloubka"], p["vyska_kamen"], p["vyska_drevo"], "sedlova", "palac")
    pa = Vector((p["osa"][0][0], 0, p["osa"][0][1])); pb = Vector((p["osa"][1][0], 0, p["osa"][1][1]))
    q = pa.lerp(pb, 0.4) + (pb - pa).normalized().cross(UP).normalized() * 1.0
    komin(P, q.x, q.z, podl + 2.0, podl + p["vyska_kamen"] + p["vyska_drevo"] + p["hloubka"] * 0.62 + 1.1)
    v = B["vez"]
    prapor(P, (v["stred"][0], ter(v["stred"][0], v["stred"][1]) + vy + (2.6 if vs.startswith("stanova") else 0) + max(v["rozmer"]) * (1.05 if vs.startswith("stanova") else 0.75), v["stred"][1]), (1, 0.3))

def navrh(n, sufix=""):
    sp = n["spojeni"]; parts = []
    ea = dict(n.get("A_navic") or {}); ea["mosty_teren"] = sp["typ"] == "final"
    PA = Part("hrad_A"); postav_A(PA, ea); parts.append(PA)
    PB = Part("hrad_B"); postav_B(PB, n.get("B_navic")); parts.append(PB)
    PS = Part("spojeni")
    if sp["typ"] == "hradba_ochoz":
        for a, b in zip(sp["osa"], sp["osa"][1:]):
            u = zed(PS, a, b, sp["tloustka"], sp["vyska"], cimburi=True)
            ochoz_kryty(PS, a, b, sp["tloustka"], u)
        for v in sp["veze"]:
            vez(PS, v["stred"], v["rozmer"], v["vyska"], v["strecha"], yaw_d=(sp["osa"][2][0] - sp["osa"][1][0], sp["osa"][2][1] - sp["osa"][1][1]), brana=v.get("brana", False))
    elif sp["typ"] == "final":
        ph = S["palisada_hrana"]
        palisada_val(PS, ph["zapad"], sp["vyska"]); palisada_val(PS, ph["vychod"], sp["vyska"])
        most_padaci(PS, next(m for m in S["mosty"] if m["id"] == "B_prurva"))
        br = sp["branka_dvora"]
        vez(PS, br["stred"], br["rozmer"], br["vyska"], "sedlova_veze", yaw_d=(-br["smer"][1], br["smer"][0]), brana=True)
        bb = S["B"]["brana"]   # branská věž zadního hradu v čelní hradbě (atlas: špaleta vstupní brány)
        vez(PS, bb["stred"], (4.0, 4.5), 9.0, "sedlova_veze", yaw_d=(-bb["smer"][1], bb["smer"][0]), brana=True)
    elif sp["typ"] == "palisady_most":
        for pal in sp["palisady"]:
            palisada_val(PS, pal, sp["vyska"])
        most(PS, sp["most"][0], sp["most"][1], sp["most_vyska"])
        for br in sp["brany"]:
            vez(PS, br["stred"], br["rozmer"], br["vyska"], "sedlova_veze", yaw_d=br["smer"], brana=True)
    elif sp["typ"] == "cesta_most":
        most(PS, sp["most"][0], sp["most"][1], sp["most_vyska"])
    elif sp["typ"] == "palisada":
        palisada(PS, sp["obrys"], sp["vyska"])
        for bd in sp["budovy"]:
            budova(PS, bd["osa"][0], bd["osa"][1], bd["hloubka"], bd["vyska"], 0, "sedlova", bd["typ"])
        br = sp["brana"]; vez(PS, br["stred"], (4.0, 4.5), 7.0, "sedlova_veze", yaw_d=br["smer"], brana=True)
    elif sp["typ"] == "kryta_chodba":
        kryta_chodba(PS, sp["osa"], sp["sirka"], sp["pilire_po"])
    parts.append(PS)
    uloz(parts, n["id"] + sufix)

chci = sys.argv[2:]
for n in (D["navrhy"] if __name__ == "__main__" else []):
    if chci and n["id"] not in chci and n["id"][:1] not in chci:
        continue
    for det, suf in ((True, ""), (False, "_daleko")):
        R.seed(1393); nastav_detail(det)
        navrh(n, suf)
