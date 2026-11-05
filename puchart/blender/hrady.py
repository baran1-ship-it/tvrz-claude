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

# Záznam trámů pro hlídač tesařských spojů (docs/reference/tesarske_spoje.md): každý Part.beam -> (střed, osy, poloviční
# rozměry, materiál, díl). Kopie lib.Part.beam se stejnou nepravidelností j – záznam = skutečná geometrie.
TRAMY = []
def _beam_zaznam(self, a, b, w, h, mat="dub", up=Vector((0, 1, 0)), j=0.0, ext=0.0, collide=False, rnd=None):
    a, b = Vector(a), Vector(b); d = b - a; L = d.length
    if L < 1e-4: return
    bas = frame(d, Vector(up))
    if j > 0:
        rx = max(-0.005 / (L / 2), min(0.005 / (L / 2), jit(j * 0.012)))   # náklon osy nejvýš 5 mm na konci (13m vaznice ujížděla 3 cm ze zdi)
        bas = bas @ Matrix.Rotation(jit(j * 0.06), 3, "Z") @ Matrix.Rotation(rx, 3, "X")
        w *= 1 + jit(j * 0.12); h *= 1 + jit(j * 0.12)
    import sys as _s; f_ = _s._getframe(1)
    TRAMY.append(((a + b) * 0.5, bas.copy(), (w / 2, h / 2, (L + ext * 2) / 2), mat, "%s:%d" % (f_.f_code.co_name, f_.f_lineno)))
    self.box(M((a + b) * 0.5, basis=bas), (w, h, L + ext * 2), mat, rnd=rnd, collide=collide)
Part.beam = _beam_zaznam

lib.GAME = True       # střechy jako deska s fotkou šindele (hra), ne jednotlivé šindele
OMITKA = True        # False = palác bez omítky (hrad B podle kresby, Míša 5. 11.)
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

import portaly   # portály: ostění v líci, hladký oblouk, polodrážka, klenba průchodu (Míša 4. 11., pravidla/svet/portaly.json)
kit._doorway_havran = kit.doorway; kit.doorway = portaly.doorway; kit.PRAVIDELNE = True
_kit_window = kit.stone_window; _kit_door = kit.doorway; _kit_deck = kit.deck; _ht = lib.half_timber; _plank = kit.plank
def _okno_daleko(P, m, w=0.6, h=0.9, depth=0.7, fill=None, **k):
    P.box(m @ M((0, h / 2, 0.03)), (w, h, 0.08), "tma"); return (-w / 2, w / 2, 0, h)
def _dvere_daleko(P, m, kind="hlavni", w=1.1, h=2.2, depth=0.7, **k):
    P.box(m @ M((0, h / 2, 0.03)), (w, h, 0.1), "tma")
def _deck_daleko(P, a, b, hw, mat="prkna_ven", **k):
    a = Vector(a); b = Vector(b); d = b - a
    P.box(M((a + b) / 2, basis=frame(d)), (hw * 2, 0.08, d.length), mat)
def _deck_puchart(P, a, b, hw, mat="prkna_ven", *ar, **k):
    """Prkna mostovky a ochozu: každé prkno s texturou JEDNOHO prkna (dřív fotka celé podlahy na každém prkně – Míša 4. 11.:
    „všechny desky položené stejně, rastr“); posun textury a odstín jiný na každém prkně (kit.plank uvo/rnd)."""
    return _kit_deck(P, a, b, hw, "prkno_ven" if mat.startswith("prkna") else mat, *ar, **k)
kit.deck = _deck_puchart; _kit_deck_p = _deck_puchart
def nastav_detail(ano):
    global DETAIL
    DETAIL = ano
    kit.stone_window = _kit_window if ano else _okno_daleko
    kit.doorway = _kit_door if ano else _dvere_daleko
    kit.deck = _kit_deck_p if ano else _deck_daleko
    lib.half_timber = _ht if ano else (lambda *a, **k: None)
    kit.plank = _plank if ano else (lambda *a, **k: None)

BEZ_OKEN = []   # [(a, b, y0, y1)] vnitřní schodiště u zdí – okna tam ne (puchart_hrad plní před stavbou paláce)
def _dist_seg(p, a, b):
    p = Vector((p.x, 0, p.z)); a = Vector((a.x, 0, a.z)); b = Vector((b.x, 0, b.z)); ab = b - a
    t_ = 0.0 if ab.length < 1e-6 else max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t_)).length
HRADBY = []  # [(a, b, koruna_y)] osy hradeb (puchart_hrad plní) – strany budov v hradbě kamenné, okna nad korunou
DIRY = []    # díry v terénu (studna): shader terénu je nekreslí
BRANY = []   # (práh vnějšího líce průjezdu, výška podlahy) – mosty se napojují na nejbližší

# ------------------------------------------------------------------ zdi
CIMB = json.load(open(os.path.join(K, "pravidla/svet/hrad_vzhled.json")))["cimburi"]
def zed(P, a, b, t, h, mat="zdivo", krok=3.5, pata=2.0, cimburi=True, koruna=None, okna=0, pilire=False):
    """Hradba a->b (x, z). Koruna = terén + h po stupních (zaokrouhleno na stupen_po_m), nebo pevně koruna (y).
    Úseky mají délku násobku rytmu cimbuří (hrad_vzhled.json cimburi) – stupeň koruny je vždy v proluce mezi stínkami,
    stínky jdou v pravidelném rytmu po celé hradbě (Míša 4. 11.). Vrací seznam (s0, s1, y_koruny) úseků pro ochoz."""
    a = Vector((a[0], 0, a[1])); b = Vector((b[0], 0, b[1])); L = (b - a).length; d = (b - a) / L
    R = CIMB["rytmus_m"]; nr = max(1, round(L / R)); Rl = L / nr          # rytmus přizpůsobený délce (celý počet)
    kr = max(1, round(krok / Rl)); hr_ = list(range(0, nr, kr)) + [nr]; out = []; st_ = CIMB["stupen_po_m"]
    for i0, i1 in zip(hr_, hr_[1:]):
        s0, s1 = i0 * Rl, i1 * Rl
        vz = [ter(*(a + d * s).xz) for s in np.linspace(s0, s1, 5)]
        y0 = min(vz) - pata
        y1 = koruna if koruna is not None else round((max(vz) + h) / st_) * st_
        e0 = t * 0.45 if (i0 == 0 and not pilire) else 0.01; e1 = t * 0.45 if (i1 == nr and not pilire) else 0.01   # uvnitř hradby přesah 1 cm (stupeň koruny přesně v proluce)
        c = a + d * ((s0 - e0 + s1 + e1) / 2)
        P.box(M((c.x, (y0 + y1) / 2, c.z), basis=frame(d)), (t, y1 - y0, s1 - s0 + e0 + e1), mat)
        out.append((s0, s1, y1))
        if cimburi:   # stínky na vnější polovině koruny (+strana = vpravo od směru), uprostřed každého rytmu – proluky na hranách úseků
            out_n = d.cross(UP).normalized(); sw = min(CIMB["stinka_m"], Rl - 0.5)
            for k in range(i0, i1):
                p = a + d * ((k + 0.5) * Rl) + out_n * (t * 0.3)
                P.box(M((p.x, y1 + CIMB["vyska_m"] / 2, p.z), basis=frame(d)), (t * 0.4, CIMB["vyska_m"], sw), mat)
    return out

NAROZI_POKOS = True
def zed_cara(P, osa, t, h, mat="zdivo", cimburi=True, koruny=None):
    """Hradba po lomené čáře (3. 11., Míša: hradby nenavazují): úseky bez přesahů, v každém vrcholu nárožní pilíř t × t
    natočený podle osy úhlu, výška = vyšší z korun sousedních úseků (žádné prolínání kvádrů a světlé čelo v rohu)."""
    useky = [zed(P, p, q, t, h, mat=mat, cimburi=cimburi, pilire=True, koruna=(koruny[k] if koruny else None)) for k, (p, q) in enumerate(zip(osa, osa[1:]))]
    for i, v in enumerate(osa):
        sous = ([useky[i - 1][-1][2]] if i > 0 else []) + ([useky[i][0][2]] if i < len(useky) else [])
        a = Vector((osa[max(i - 1, 0)][0], 0, osa[max(i - 1, 0)][1])); b = Vector((osa[min(i + 1, len(osa) - 1)][0], 0, osa[min(i + 1, len(osa) - 1)][1]))
        c = Vector((v[0], 0, v[1])); d = (b - a).normalized() if (b - a).length > 1e-6 else Vector((1, 0, 0))
        y0 = ter(v[0], v[1]) - 2.0; y1 = max(sous)
        if 0 < i < len(osa) - 1 and NAROZI_POKOS:   # vnitřní vrchol: klín na pokos, líce v rovině obou úseků (dřív kvádr t·1,08 vystupoval – „zeď navíc“, Míša 4. 11.)
            pa_ = Vector((osa[i - 1][0], 0, osa[i - 1][1])); pb_ = Vector((osa[i + 1][0], 0, osa[i + 1][1]))
            n1 = (c - pa_).normalized().cross(UP).normalized(); n2 = (pb_ - c).normalized().cross(UP).normalized()
            k_ = 1.0 + n1.dot(n2); h_ = t / 2; mo = (n1 + n2) / k_ * h_ if k_ > 0.15 else (n1 + n2).normalized() * h_ * 2.5
            body = [c + n1 * h_, c + mo, c + n2 * h_, c - n1 * h_, c - n2 * h_]   # bez vnitřního hrotu (trčel z paláce B – povrch_kolize)
            body = sorted(body, key=lambda q: math.atan2(q.z - c.z, q.x - c.x))
            if (body[1] - body[0]).cross(body[2] - body[0]).dot(UP) < 0: body.reverse()
            P.prism([q + UP * y0 for q in body], UP * (y1 - y0), mat)
            P.cols.append((M((c.x, (y0 + y1) / 2, c.z), basis=frame(d)), (t * 1.08, y1 - y0, t * 1.08)))
            mh_ = Vector((mo.x, 0, mo.z))
            if mh_.length > 0.54 * t:
                for sg_ in (1,):
                    q_ = c + mh_ * (0.5 * sg_) + mh_.normalized() * (0.075 if sg_ < 0 else 0.0)
                    P.cols.append((M((q_.x, (y0 + y1) / 2, q_.z), basis=frame(mh_.normalized())), (t * 0.4, y1 - y0, mh_.length + (0.04 if sg_ > 0 else -0.15))))
        else:   # konec hradby (u věže): pilíř jako dřív – nese podestu u portálku
            P.box(M((c.x, (y0 + y1) / 2, c.z), basis=frame(d)), (t * 1.08, y1 - y0, t * 1.08), mat)
    return useky

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
    for p in rohy:   # okap níž, aby plocha střechy dosedla na hranu zdi ve výšce y (dřív mezera 0,3–0,5 m – kontrola_geometrie)
        v = Vector((p[0], 0, p[1])); r = (v - c).length; t = presah / (r + presah)
        ye = (y - t * (y + vyska)) / (1 - t)
        v = v + (v - c).normalized() * presah; pts.append(v + UP * ye)
    for i in range(len(pts)):
        lib.shingle_roof(P, pts[i], pts[(i + 1) % len(pts)], apex, apex, ridge=False)
    P.rod(apex - UP * 0.2, apex + UP * 1.4, 0.04, 6, "zelezo")           # žerď s praporkem
    P.ball(apex + UP * 0.1, (0.18, 0.22, 0.18), "zelezo", seg=8, rings=5)

def strecha_sedlova(P, a, b, hloubka, y, vyska, presah=0.5, stity="drevo"):
    """Sedlová střecha nad obdélníkem s osou a->b (hřeben podél osy) a štíty na koncích."""
    a = Vector((a[0], 0, a[1])); b = Vector((b[0], 0, b[1])); d = (b - a).normalized(); s = d.cross(UP).normalized()
    a2, b2 = a - d * presah, b + d * presah
    w = hloubka / 2 + presah
    t = presah / w; ye = (y - t * (y + vyska)) / (1 - t)   # okap níž – plocha dosedne na hranu zdi
    eL1, eR1 = a2 + s * w + UP * ye, b2 + s * w + UP * ye
    eL2, eR2 = b2 - s * w + UP * ye, a2 - s * w + UP * ye
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
    t = presah / w; ye = (y - t * (y + vyska)) / (1 - t)   # okap níž – plocha dosedne na hranu zdi (jako strecha_jehlan)
    E = [p + UP * ye for p in e]
    lib.shingle_roof(P, E[0], E[1], r2, r1)
    lib.shingle_roof(P, E[2], E[3], r1, r2)
    lib.shingle_roof(P, E[1], E[2], r2, r2, ridge=False)
    lib.shingle_roof(P, E[3], E[0], r1, r1, ridge=False)

# ------------------------------------------------------------------ věž
VEZ_PATRO = []   # strážnice nad průjezdem (pro schody a test průchodu ve stavitelích)
BRANA_PW, BRANA_PH, PATRO_TW, PORTAL_W = 3.2, 4.2, 0.9, 0.9   # průjezd branky (šířka, výška), zdi strážnice, portálek
def patro_brany_y(yf): return yf + BRANA_PH + 0.6              # podlaha strážnice = ochozy hradeb ve stejné výšce (Havran WALK)
def portal_v(dpt): return dpt / 2 - PATRO_TW - PORTAL_W / 2 - 0.05   # osa portálku v boční stěně (od osy průjezdu ke dvoru)
def vez(P, stred, rozmer, vyska, strecha="jehlan", yaw_d=(1, 0), brana=False, yf=None, patro=False, portalky=None):
    cx, cz = stred; w, dpt = rozmer
    d = Vector((yaw_d[0], 0, yaw_d[1])).normalized(); s = d.cross(UP).normalized()
    c = Vector((cx, 0, cz))
    rohy = [c + d * (w / 2) * i + s * (dpt / 2) * j for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    lo, hi = ter_rozsah([(p.x, p.z) for p in rohy])
    y0 = lo - 2.0; y1 = hi + vyska
    if brana:
        # PRŮJEZD skrz věž (Míša 30. 10.: brána musí mít průchod): osa průjezdu = s (ven = -s), šířka pw, výška ph
        pw, ph = BRANA_PW, BRANA_PH
        yf = round(ter(c.x, c.z) * 4) / 4 if yf is None else yf
        # patro nad průjezdem (Míša 3. 11.: branka bez místnosti): pilíře a strop do yp, nad ním dutá strážnice se zdmi tw,
        # dveře na vnitřní (+s) straně u kraje – přístup po dřevěných schodech zvenku (stavitel hradu, VEZ_PATRO)
        tw = PATRO_TW; yp = patro_brany_y(yf); hor = y1 if patro else None
        Wo, Ho = portaly.otvor(pw, ph, "lomeny")   # otvor průjezdu: portál ho vyplní ostěním, polodrážkou a lomenou klenbou
        for sg in (-1, 1):   # boční pilíře
            L = (w - Wo) / 2; cc = c + d * sg * (Wo / 2 + L / 2)
            P.box(M((cc.x, (y0 + (yp if patro else y1)) / 2, cc.z), basis=frame(d)), (dpt, (yp if patro else y1) - y0, L), "zdivo")
        P.box(M((c.x, (yf + Ho + (yp if patro else y1)) / 2, c.z), basis=frame(d)), (dpt, (yp if patro else y1) - yf - Ho, Wo + 0.02), "zdivo")   # nad průjezdem
        if patro:
            # vstup portálky v BOČNÍCH stěnách z ochozů přilehlých hradeb (docs/reference/branka_ochoz.md: Kost, Žebrák,
            # Hradní brána II…; Míša 3. 11.: „vstup není ve správném místě“) – dřív dveře do předbraní a 7m schody u mostu
            # portálky = [(stěna "+d"|"-d"|"+s", posun podél stěny)] – tam, kde do věže narazí osa pavlače (stavitel hradu)
            dw_ = PORTAL_W; dh_ = 2.0; dvere_ = []   # 0,8 m byl pro postavu těsný (test průchodu)
            por = portalky if portalky is not None else [("+d", dpt / 2 - tw - dw_ / 2 - 0.05), ("-d", dpt / 2 - tw - dw_ / 2 - 0.05)]
            steny = {"+s": (s, d, w / 2 - tw, dpt / 2, w), "-s": (-s, d, w / 2 - tw, dpt / 2, w),
                     "+d": (d, s, dpt / 2 - tw, w / 2, dpt - 2 * tw), "-d": (-d, s, dpt / 2 - tw, w / 2, dpt - 2 * tw)}
            for jm, (nrm, T, vnitr, vzd, L_) in steny.items():
                cc = c + nrm * (vzd - tw / 2); kusy = [(-L_ / 2, L_ / 2, yp, y1)]
                for st_, o_ in por:
                    if st_ != jm: continue
                    o_ = max(-(vnitr - dw_ / 2 - 0.05), min(vnitr - dw_ / 2 - 0.05, o_))
                    Wk, Hk = portaly.otvor(dw_, dh_, "segment")
                    kusy = [k for k in kusy if not (k[0] < o_ < k[1])] + [(k[0], o_ - Wk / 2, yp, y1) for k in kusy if k[0] < o_ < k[1]] + \
                           [(o_ + Wk / 2, k[1], yp, y1) for k in kusy if k[0] < o_ < k[1]] + [(o_ - Wk / 2, o_ + Wk / 2, yp + Hk, y1)]
                    f_ = c + nrm * vzd + T * o_
                    kit.doorway(P, M(f_ + UP * yp, basis=Matrix((UP.cross(nrm), UP, nrm)).transposed()), kind="obycejne",
                                w=dw_, h=dh_, depth=tw, top="segment", leaf=True)
                    dvere_.append((jm, f_.copy(), nrm.copy()))
                for u0_, u1_, ya, yb in kusy:
                    if u1_ - u0_ > 0.02: q = cc + T * ((u0_ + u1_) / 2); P.box(M((q.x, (ya + yb) / 2, q.z), basis=frame(T)), (tw, yb - ya, u1_ - u0_), "zdivo")
            P.box(M((c.x, yp - 0.03, c.z), basis=frame(d)), (dpt - 2 * tw, 0.06, w - 2 * tw), "prkna_ven")   # podlaha strážnice
            VEZ_PATRO.append({"stred": c.copy(), "d": d.copy(), "s": s.copy(), "w": w, "dpt": dpt, "yp": yp, "dvere": dvere_, "dvere_w": dw_, "tw": tw})
        P.box(M((c.x, (y0 + yf) / 2, c.z), basis=frame(d)), (dpt, yf - y0, pw + 0.02), "zdivo")                          # pod podlahou
        # valenou lomenou klenbu průjezdu staví portál (portaly.doorway přes celou hloubku věže)
        P.box(M(c + UP * (yf - 0.05), basis=frame(d)), (dpt, 0.1, Wo), "kvadr_sedy")
        # portály na obou lících a vrata (vnitřní strana otevřená)
        f = c - s * (dpt / 2)   # vnější líc (ven = −s): ostění, křídla v polodrážce, klenba skrz, na vnitřním líci záklenek
        m = M(f + UP * yf, basis=Matrix((-d, UP, -s)).transposed())
        kit.doorway(P, m, kind="hlavni", w=pw, h=ph, depth=dpt, top="lomeny", leaf=True, double=True, venec_vnitrni=True)
        BRANY.append((c - s * (dpt / 2), yf))   # práh vnějšího líce – sem vede most
    else:
        P.box(M((c.x, (y0 + y1) / 2, c.z), basis=frame(d)), (dpt, y1 - y0, w), "zdivo")
    # nároží z větších kamenů (KCD: kvádrová nároží) – střídavě
    # (Míša 2. 11.: kvádry visely – vyčnívaly 25 cm a mezi řadami byla mezera 4 cm; kontrola_geometrie je hlásila):
    # líc kvádru 2 cm před lícem zdi, řady na sebe dosedají, střídá se jen délka podél stěn (vazba nároží)
    VYS = 0.42; VYC = 0.02
    for p in rohy:
        sd = 1 if (p - c).dot(d) > 0 else -1; ss = 1 if (p - c).dot(s) > 0 else -1
        y = hi - 0.5; k = 0
        while y + VYS <= y1 - 0.2:
            lx, lz = (0.95, 0.55) if k % 2 else (0.55, 0.95)   # x podél s, z podél d
            q = p + s * ss * (VYC - lx / 2) + d * sd * (VYC - lz / 2)
            P.box(M((q.x, y + VYS / 2, q.z), basis=frame(d)), (lx, VYS, lz), "kvadr", collide=None)   # vyčnívá 2 cm: kolizi má tělo věže (o hranu kvádru se postava zachytila – test průchodu 3. 11.)
            y += VYS; k += 1
    # střílny a okna na čtyřech stranách
    for strana, nrm, L in ((0, s, w), (1, -s, w), (2, d, dpt), (3, -d, dpt)):
        osa = d if strana < 2 else s
        f = c + nrm * ((dpt if strana < 2 else w) / 2)
        for y in np.arange(hi + 4.0, y1 - 3.0, 4.5):
            if brana and strana < 2 and y < yf + portaly.otvor(BRANA_PW, BRANA_PH, "lomeny")[1] + portaly.PR["venec_m"] + 1.2: continue   # ne okno v záklenku brány (viselo nad obloukem)
            m = M(f + UP * y, basis=Matrix((osa * (1 if strana in (0, 3) else -1), UP, nrm)).transposed())
            if y > y1 - 8:   # okno v ostění s hlubokým tmavým světlíkem (dřív rám na plné zdi = „zazděné okno“, Míša 4. 11.)
                kit.stone_window(P, m, w=0.55, h=0.95, depth=0.8, fill="mriz")
                P.box(m @ M((0, 0.475, 0.006)), (0.56, 0.96, 0.01), "tma")   # věž je plná: tmavý světlík na líci v ostění
            else:   # střílna: kamenný překlad a práh, tmavý úzký světlík zapuštěný 0,3 m
                P.box(m @ M((0, 0.6, 0.006)), (0.14, 1.0, 0.01), "tma")
                for yy_ in (0.04, 1.16): kit.stone(P, m @ M((0, yy_, -0.1)), (0.5, 0.12, 0.24), "kvadr_okno", cham=0.02, rough=0.0)
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
def okno_palace(P, c, dd, nout, t, w, ya, yb, dvoj, ys, yn):
    """Okno paláce (docs/reference/okna_palace.md): c = osa okna na ose zdi (y = 0), dd podél zdi, nout ven, t tloušťka zdi.
    Vnější „slupka“ zdi (0,35 m) s užším světlíkem v tesaném ostění, za ní nika přes zbytek tloušťky (otvor dělá zeď),
    sedátko na dně niky, sklo zapuštěné 0,22 m za lícem, dřevěné okenice otevřené k ostění niky."""
    sl = 0.35 if dvoj else t   # nika se sedátkem jen v sále (patro); v přízemí světlík přes celou zeď (do niky se vlezlo zvenku přes sráz – povrch_kolize)
    f = c + nout * (t / 2); m = M(f, basis=Matrix((UP.cross(nout), UP, nout)).transposed())
    wn = w + 0.45; zc = -sl / 2
    def kus(x0, x1, y0, y1, mat="zdivo"):
        if x1 - x0 > 0.01 and y1 - y0 > 0.01: P.box(m @ M(((x0 + x1) / 2, (y0 + y1) / 2, zc)), (x1 - x0, y1 - y0, sl), mat)
    kus(-wn / 2, -w / 2, ys, yn); kus(w / 2, wn / 2, ys, yn); kus(-w / 2, w / 2, ys, ya); kus(-w / 2, w / 2, yb, yn)   # slupka kolem světlíku
    jw = 0.2; pr = 0.045   # ostění (lícuje s omítkou, o 5 mm před ní – Míša 4. 11.: „okolo vylézají kameny“): stojky, nadpraží, parapet s okapnicí, sražené hrany (kit.stone)
    for sx in (-1, 1):
        kit.stone(P, m @ M((sx * (w / 2 + jw / 2 - 0.02), (ya + yb) / 2, zc + pr / 2)), (jw, yb - ya, sl + pr), "kvadr_okno", cham=0.025, rough=0.0)
    kit.stone(P, m @ M((0, yb + 0.12, zc + pr / 2)), (w + 2 * jw, 0.24, sl + pr), "kvadr_okno", cham=0.025, rough=0.0)
    kit.stone(P, m @ M((0, ya - 0.07, zc + pr / 2 + 0.015)), (w + 2 * jw + 0.06, 0.14, sl + pr + 0.03), "kvadr_okno", cham=0.02, rough=0.0)   # parapet s okapnicí 3 cm
    if dvoj:   # křížové okno: sloupek a příčník (pole ~0,38 m)
        kit.stone(P, m @ M((0, (ya + yb) / 2, zc + pr / 2)), (0.14, yb - ya, sl + pr), "kvadr_okno", cham=0.02, rough=0.0)
        kit.stone(P, m @ M((0, ya + (yb - ya) * 0.62, zc + pr / 2)), (w, 0.12, sl + pr), "kvadr_okno", cham=0.02, rough=0.0)
    zg = -0.22
    for x0, x1 in (((-w / 2, -0.07), (0.07, w / 2)) if dvoj else ((-w / 2, w / 2),)):
        # bez skla (Míša 4. 11.: „okna zazděná“ – sklo vyšlo z exportu neprůhledné světlé jako omítka); jen dubový rám a příčle
        P.box(m @ M(((x0 + x1) / 2, ya + 0.02, zg)), (x1 - x0, 0.04, 0.05), "dub"); P.box(m @ M(((x0 + x1) / 2, yb - 0.02, zg)), (x1 - x0, 0.04, 0.05), "dub")
    hn = t - sl   # nika: sedátko a okenice
    if hn < 0.05:   # přízemí: okenice na vnitřním líci
        for sx in (-1, 1): P.box(m @ M((sx * (w / 2 + w / 4 + 0.02), (ya + yb) / 2, -t - 0.03)), (w / 2, yb - ya, 0.04), "okenice")
        return
    P.box(m @ M((0, ys - 0.03, -sl - hn / 2)), (wn, 0.06, hn), "kvadr_okno")
    for sx in (-1, 1):
        P.box(m @ M((sx * (wn / 2 - 0.03), (ya + yb) / 2, -sl - w / 4 - 0.02)), (0.04, yb - ya, w / 2), "okenice")

def budova(P, a, b, hloubka, h_kamen, h_drevo=0.0, strecha="sedlova", typ="palac", okna_ven=True, podl=None, otvory=(), vstup=None, patra=None, patra_rel=None):
    """Obdélník s osou a->b. typ palac: kamenné přízemí s omítkou + hrázděné patro; hrazdena: kamenná podezdívka +
    hrázdění; roubena: srub z trámů; pristresek: sloupy a pultová střecha."""
    A = Vector((a[0], 0, a[1])); B = Vector((b[0], 0, b[1])); L = (B - A).length; d = (B - A) / L; s = d.cross(UP).normalized()
    rohy = [A + s * hloubka / 2, B + s * hloubka / 2, B - s * hloubka / 2, A - s * hloubka / 2]
    lo, hi = ter_rozsah([(p.x, p.z) for p in rohy])
    podl = hi + 0.3 if podl is None else podl; y0 = lo - 1.0   # podl zadaná: pod budovou je sklep (terén vyhloubený)
    if otvory: y0 = min(y0, min(o[3] for o in otvory) - 0.4)   # zdi až pod práh nejnižšího otvoru (dveře do sklepa: pod zdí byla díra do ničeho, Míša 5. 11.)
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
    dv_ = None   # dveře (strana 0 = +s, 2 = −s; od = od rohu A podél osy) → skutečný otvor (3. 11.: vstupy jen namalované na zdi)
    if vstup is not None:
        dv_ = (vstup[0], vstup[1], vstup[2], vstup[3])
        od_s = vstup[1] if vstup[0] == 0 else L - vstup[1]
        Wv, Hv = portaly.otvor(vstup[2], vstup[3], "lomeny")
        otvory = list(otvory) + [(vstup[0], od_s, Wv, podl, podl + Hv)]
    # Okna paláce podle docs/reference/okna_palace.md (Křivoklát, Pražský hrad): hluboká nika se sedátkem uvnitř, ven užší
    # světlík v tesaném ostění (světlejší kámen, sražené hrany), v patře dvoudílné se sloupkem, sklo zapuštěné, okenice.
    # Okna po patrech (Míša 4. 11.: „okna splývají se stěnou“; dřív jedno okno přes podlahu sálu, ploché sklo v líci).
    # strany v hradbě (Míša 4. 11.: „když je budova v hradbě, neměla by mít okna pod úrovní hradby, a v tom místě kámen, ne kombinace
    # omítky a kamene“): strana do 2,5 m od osy hradby a s ní rovnoběžná (±25°) = kamenná, okna jen nad korunou hradby
    def v_hradbe(p0_, p1_):
        m_ = (p0_ + p1_) / 2; dd_ = (p1_ - p0_).normalized()
        for (ha, hb, hk) in HRADBY:
            ha_ = Vector((ha[0], 0, ha[1])); hb_ = Vector((hb[0], 0, hb[1])); hl_ = (hb_ - ha_).length
            if hl_ < 0.1: continue
            hd_ = (hb_ - ha_) / hl_; tt_ = max(0.0, min(hl_, (m_ - ha_).dot(hd_)))
            if (m_ - (ha_ + hd_ * tt_)).length < 2.5 and abs(dd_.dot(hd_)) > 0.9: return hk
        return None
    def u_hradby(q_, dosah_):   # koruna hradby, jejíž osa je blíž než dosah_ k bodu q_ (jinak None)
        for (ha, hb, hk) in HRADBY:
            ha_ = Vector((ha[0], 0, ha[1])); hb_ = Vector((hb[0], 0, hb[1])); hl_ = (hb_ - ha_).length
            if hl_ < 0.1: continue
            hd_ = (hb_ - ha_) / hl_; tt_ = max(0.0, min(hl_, (q_ - ha_).dot(hd_)))
            if (Vector((q_.x, 0, q_.z)) - (ha_ + hd_ * tt_)).length < dosah_: return hk
        return None
    STR_HR = {}
    for si_, (p0_, p1_) in enumerate(zip(rohy, rohy[1:] + rohy[:1])):
        STR_HR[si_] = v_hradbe(p0_, p1_)
        if STR_HR[si_] is None:   # strana hradbou protnutá (šikmá hradba u paláce B): kamenná, pokud se jí dotýká na víc než třetině
            nn_ = -(p1_ - p0_).normalized().cross(UP).normalized(); vz_ = [u_hradby(p0_.lerp(p1_, f_) - nn_ * (t / 2 + 0.4), 1.6) for f_ in np.linspace(0.05, 0.95, 10)]
            if sum(v is not None for v in vz_) >= 4: STR_HR[si_] = max(v for v in vz_ if v is not None)
    OKNA = []; OM = []   # OKNA: (strana, od, šířka světlíku, y0, y1, dvojdílné, y_sedátka, y_vrch_niky); OM = otvory pro omítku
    if typ == "palac" and okna_ven:
        urovne = sorted(patra) if patra else ([podl + r for r in patra_rel] if patra_rel else [podl])
        for si, (p0, p1) in enumerate(zip(rohy, rohy[1:] + rohy[:1])):
            Ls = (p1 - p0).length
            for ui, lv in enumerate(urovne):
                strop = urovne[ui + 1] if ui + 1 < len(urovne) else yk
                dvoj = ui >= 1; w_ = 0.7 if dvoj else 0.4   # (Míša 5. 11.: „výkladní skříně až k podlaze“) – malý světlík, nika jen kolem okna
                ya = lv + 1.1; yb = min(ya + (1.1 if dvoj else 0.75), strop - 0.75)
                if yb - ya < 0.6: continue
                if STR_HR.get(si) is not None and ya < STR_HR[si] + 1.0: continue   # v hradbě: pod korunou bez oken
                for k in np.arange(2.5, Ls - 1.5, 3.6 if dvoj else 4.2):
                    if any(o[0] == si and abs(o[1] - k) < o[2] / 2 + w_ / 2 + 0.9 for o in otvory) or any(o[0] == si and abs(o[1] - k) < 1.6 and abs(o[3] - ya) < 0.1 for o in OKNA): continue
                    nn_ = -(p1 - p0).normalized().cross(UP).normalized(); hk_ = u_hradby(p0 + (p1 - p0).normalized() * k - nn_ * (t / 2 + 0.5), 2.2)
                    if hk_ is not None and ya < hk_ + 1.0: continue   # před oknem hradba – zazděné okno (Míša 4. 11.)
                    wc_ = p0 + (p1 - p0).normalized() * float(k)
                    if any(_dist_seg(wc_, sa_, sb_) < 1.3 and ya < sy1_ + 0.5 and yb > sy0_ - 0.3 for sa_, sb_, sy0_, sy1_ in BEZ_OKEN): continue   # za oknem schody (Míša 5. 11.)
                    OKNA.append((si, float(k), w_, ya, yb, dvoj, ya - 0.12, yb + 0.3))
        otvory = list(otvory)
        OM = [(o[0], o[1], o[2] + 0.44, o[3] - 0.16, o[4] + 0.28) for o in OKNA]
        otvory_zed = otvory + [(o[0], o[1], o[2] + 0.45, o[6], o[7]) for o in OKNA]   # zeď: otvor niky (úzká nika)
    else:
        otvory_zed = list(otvory)
    otvory_omitka = list(otvory) + OM
    otvory = otvory_zed
    for si, (p0, p1) in enumerate(zip(rohy, rohy[1:] + rohy[:1])):
        dd = (p1 - p0).normalized(); Ls = (p1 - p0).length
        ot = [o for o in otvory if o[0] == si]   # otvory = [(strana, od rohu, šířka, y_dole, y_nahore)] – dveře do sklepa
        hr = sorted({-t / 2, Ls + t / 2} | {x for o in ot for x in (o[1] - o[2] / 2, o[1] + o[2] / 2)})
        for s0, s1 in zip(hr, hr[1:]):
            sm = (s0 + s1) / 2; cc = p0 + dd * sm
            o = next((o for o in ot if o[1] - o[2] / 2 - 1e-6 <= sm <= o[1] + o[2] / 2 + 1e-6), None)
            for ya, yb in ([(y0, yk)] if o is None else [(y0, o[3]), (o[4], yk)]):
                if yb - ya > 0.05:
                    P.box(M((cc.x, (ya + yb) / 2, cc.z), basis=frame(dd)), (t, yb - ya, s1 - s0), "zdivo")
    if typ == "palac" and OMITKA:
        # omítka na horní části kamenného patra (KCD: palác omítnutý, kámen u paty a nároží)
        for si, (p0, p1) in enumerate(zip(rohy, rohy[1:] + rohy[:1])):
            dd = (p1 - p0).normalized(); nn = -dd.cross(UP).normalized(); Ls = (p1 - p0).length
            if STR_HR.get(si) is not None: continue   # strana v hradbě: kamenná (bez omítky)
            ot = [o for o in otvory_omitka if o[0] == si]   # omítka po kusech mezi otvory (přes dveře visela deska bez kolize – povrch_kolize 3. 11.)
            # omítka celou plochou až do nároží a k zemi (Míša 4. 11.: „linka kamení na paláci není hezká“ – dřív kámen 0,3 m na
            # nárožích a 1,2 m u paty)
            e_ = t / 2 + 0.02; y_om = y0
            hr = sorted({-e_, Ls + e_} | {min(max(x, -e_), Ls + e_) for o in ot for x in (o[1] - o[2] / 2, o[1] + o[2] / 2)})
            for s0, s1 in zip(hr, hr[1:]):
                if s1 - s0 < 0.05: continue
                sm = (s0 + s1) / 2; cc = p0 + dd * sm + nn * (t / 2 + 0.02)
                o = next((o for o in ot if o[1] - o[2] / 2 - 1e-6 <= sm <= o[1] + o[2] / 2 + 1e-6), None)
                je_dvere = o is not None and abs(o[3] - podl) < 0.05 and o[2] >= 0.9 and o[4] - o[3] > 2.0
                if je_dvere:   # nad dveřmi s lomeným záklenkem omítka až k oblouku (po 10 cm) – dřív obdélník a v cviklech zdivo
                    wv_, hv_ = vstup[2], vstup[3]; f_ = portaly.podhledi("lomeny", wv_, portaly.patka("lomeny", wv_, hv_)); nst = max(1, int((s1 - s0) / 0.1))
                    for k_ in range(nst):   # omítka dobíhá k podhledí; klenáky (o 4,5 cm před lícem omítky) ji kryjí
                        u0_ = s0 + (s1 - s0) * k_ / nst; u1_ = s0 + (s1 - s0) * (k_ + 1) / nst; xm = (u0_ + u1_) / 2 - o[1]
                        yl = podl + max(f_(xm - (u1_ - u0_) / 2), f_(xm + (u1_ - u0_) / 2)) if abs(xm) < wv_ / 2 else y_om
                        yl = min(max(yl, y_om), yk); cc2 = p0 + dd * ((u0_ + u1_) / 2) - nn * (t / 2 + 0.02)
                        if yk - yl > 0.05: P.box(M((cc2.x, (yl + yk) / 2, cc2.z), basis=frame(dd)), (0.04, yk - yl, u1_ - u0_), "omitka", uvo=((u0_ + u1_) / 2 + si * 37.0, (yl + yk) / 2))   # souvislá textura přes pruhy
                    continue
                kusy_o = [(y_om, yk)] if o is None else [(y_om, o[3]), (max(y_om, o[4]), yk)]
                for ya, yb_ in kusy_o:
                    if yb_ - ya > 0.05:
                        cc2 = p0 + dd * sm - nn * (t / 2 + 0.02)   # na vnějším líci (nn míří dovnitř)
                        P.box(M((cc2.x, (ya + yb_) / 2, cc2.z), basis=frame(dd)), (0.04, yb_ - ya, s1 - s0), "omitka", uvo=(sm + si * 37.0, (ya + yb_) / 2))
            for o in OKNA:
                if o[0] == si: okno_palace(P, p0 + dd * o[1], dd, -nn, t, *o[2:])
        # vstup: výchozí uprostřed strany −s; vstup=(strana 0/2, od rohu A, šířka, výška) = skutečný otvor (otvory) na dané straně
        if vstup is None:
            f = A + d * (L * 0.5) - s * (hloubka / 2 + t / 2 + 0.05)
            kit.doorway(P, M(f + UP * podl, basis=Matrix((-d, UP, -s)).transposed()), kind="hlavni", w=1.4, h=2.6, depth=1.1, open_deg=25)
        else:
            sg = 1 if vstup[0] == 0 else -1
            f = A + d * vstup[1] + s * sg * (hloubka / 2 + t / 2 + 0.02)
            kit.doorway(P, M(f + UP * podl, basis=Matrix((d * sg, UP, s * sg)).transposed()), kind="hlavni", w=vstup[2], h=vstup[3], depth=t, top="lomeny", proud_max=0.045)
    ytop = yk
    if dv_ is not None and typ != "palac" and kit is not None:
        sg = 1 if dv_[0] == 0 else -1
        f = A + d * dv_[1] + s * sg * (hloubka / 2 + 0.02)
        kit.doorway(P, M(f + UP * podl, basis=Matrix((d * sg, UP, s * sg)).transposed()), kind="vnitrni", w=dv_[2], h=dv_[3], depth=0.3, top="rovny", leaf=True, open_deg=75, inner=False)
    if h_drevo > 0 or typ in ("hrazdena", "roubena"):
        hd = h_drevo if h_drevo > 0 else h_kamen
        o = 0.35 if typ == "palac" else 0.0      # vyložené patro
        R2 = [p + (p - c).normalized() * o for p in rohy]
        for si2, (p0, p1) in enumerate(zip(R2, R2[1:] + R2[:1])):
            dd = (p1 - p0).normalized(); nn = -dd.cross(UP).normalized(); Lw = (p1 - p0).length
            dvr = None   # dveře na této straně v tomto patře: (od, šířka, výška nad ytop)
            if dv_ is not None and si2 == dv_[0] and podl + dv_[3] > ytop:
                dvr = ((dv_[1] if si2 == 0 else Lw - dv_[1]), dv_[2], podl + dv_[3] - ytop)
            if typ == "roubena":   # liché stěny o půl trámu výš: v rozích se trámy přeplátují (rohový zámek), dřív se prostupovaly celé
                y = ytop + (0.13 if si2 % 2 else 0.0)
                while y < ytop + hd:
                    if dvr and y < ytop + dvr[2]:   # trámy přerušené dveřmi
                        P.beam(p0 - dd * 0.3 + UP * (y + 0.12), p0 + dd * (dvr[0] - dvr[1] / 2) + UP * (y + 0.12), 0.24, 0.26, "dub", j=0.6)
                        P.beam(p0 + dd * (dvr[0] + dvr[1] / 2) + UP * (y + 0.12), p1 + dd * 0.3 + UP * (y + 0.12), 0.24, 0.26, "dub", j=0.6)
                    else:
                        P.beam(p0 - dd * 0.3 + UP * (y + 0.12), p1 + dd * 0.3 + UP * (y + 0.12), 0.24, 0.26, "dub", j=0.6)
                    y += 0.26
            else:
                okna = [(k - 0.35, k + 0.35, 0.9, 1.9) for k in np.arange(1.6, Lw - 1.0, 2.6) if not (dvr and abs(k - dvr[0]) < dvr[1] / 2 + 0.6)]
                otv_ = list(okna) + ([(dvr[0] - dvr[1] / 2, dvr[0] + dvr[1] / 2, 0.0, dvr[2])] if dvr else [])
                # výplň hrázdění po kusech kolem oken a dveří – okna skutečné otvory (Míša 4. 11.: „ani jedno okno není průhledné“;
                # dřív plná omítka a před ní černá deska)
                hr_ = sorted({0.0, Lw} | {x for o0, o1, _, _ in otv_ for x in (o0, o1)})
                for u0, u1 in zip(hr_, hr_[1:]):
                    if u1 - u0 < 0.02: continue
                    um = (u0 + u1) / 2; ot_ = next((o_ for o_ in otv_ if o_[0] - 1e-6 <= um <= o_[1] + 1e-6), None)
                    for ya, yb in ([(0.0, hd)] if ot_ is None else [(0.0, ot_[2]), (ot_[3], hd)]):
                        if yb - ya > 0.02:
                            q = p0 + dd * um; P.box(M((q.x, ytop + (ya + yb) / 2, q.z), basis=frame(dd)), (0.2, yb - ya, u1 - u0), "omitka")
                lib.half_timber(P, p0 + nn * 0.1, p1 + nn * 0.1, nn, ytop, ytop + hd, openings=[(o0, o1, ytop + ya, ytop + yb) for o0, o1, ya, yb in otv_], bay=1.2, mat="hraz")   # výšky otvorů absolutně (relativní nikdy nepřekážely – trámy vedly přes dveře a okna, 3. 11.)
                for o0, o1, ya, yb in okna:   # okno: dubový rám v otvoru, okenice otevřené ven ke zdi (1393: sklo jen v sále – docs/reference/detaily_hradu_1393.md)
                    q = p0 + dd * ((o0 + o1) / 2); wq = o1 - o0; hq = yb - ya; yc = ytop + (ya + yb) / 2
                    for sx in (-1, 1):
                        P.box(M(q + dd * (sx * (wq / 2 - 0.03)) + UP * yc, basis=frame(dd)), (0.16, hq, 0.06), "dub")
                        P.box(M(q - nn * 0.12 + dd * (sx * (wq / 2 + wq / 4 + 0.03)) + UP * yc, basis=frame(dd)), (0.035, hq - 0.04, wq / 2), "okenice")
                    for yy in (ytop + ya + 0.03, ytop + yb - 0.03):
                        P.box(M(q + UP * yy, basis=frame(dd)), (0.16, 0.06, wq), "dub")
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
        strecha_sedlova(P, (a2.x, a2.z), (b2.x, b2.z), hl, ytop, hl * 0.62, presah=0.5, stity=("drevo" if (OMITKA or typ != "palac") else "kamen"))   # kamenný palác B: kamenné štíty (kresba misa_01)
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
    """Studna z tvrze Havrana (Míša 3. 11.: „vyměň studnu za tu z tvrze Havran, vše reálné a hezké“; Havran blender/studna.py):
    roubená z lomového šedého kamene (každý kámen jiný, nepravidelné vrstvy, spáry vystřídané), krycí desky, dva sloupy se
    vzpěrami a kovaným ložiskem, rumpál s klikou, navinuté lano a vědro, šindelová stříška na krokvích. Šachta: terén tu
    nemá díru → tmavé hrdlo (jako dřív), ne válec pod terénem."""
    import random as _r
    Rr = _r.Random(77)
    def jj(a): return Rr.uniform(-a, a)
    p = Vector((x, ter(x, z), z))
    r_in, r_out = 0.68, 1.12
    y = -0.12
    while y < 0.72:   # roubení: vrstvy lomových kamenů po obvodu
        h = Rr.uniform(0.17, 0.25); a = Rr.uniform(0, 0.4)
        while a < 2 * math.pi - 0.05:
            ln = Rr.uniform(0.32, 0.55); da = ln / ((r_in + r_out) / 2)
            if a + da > 2 * math.pi: da = 2 * math.pi - a
            am = a + da / 2; rr = (r_in + r_out) / 2 + jj(0.02)
            c = p + Vector((math.cos(am) * rr, y + h / 2, math.sin(am) * rr))
            kit.stone(P, M(c, -math.degrees(am) - 90), (ln * 0.97, h * Rr.uniform(0.9, 1.0), (r_out - r_in) * Rr.uniform(0.85, 1.0)),
                      "kvadr_sedy", cham=Rr.uniform(0.02, 0.05), rough=0.018)
            a += da
        y += h
    a = 0.0; yt = y
    while a < 2 * math.pi - 0.05:   # krycí desky: širší, plošší, mírně přes hranu
        ln = Rr.uniform(0.55, 0.8); da = min(ln / ((r_in + r_out) / 2), 2 * math.pi - a); am = a + da / 2
        c = p + Vector((math.cos(am) * ((r_in + r_out) / 2 + 0.02), yt + 0.06, math.sin(am) * ((r_in + r_out) / 2 + 0.02)))
        kit.stone(P, M(c, -math.degrees(am) - 90), (ln * 0.98, 0.12, (r_out - r_in) + 0.12), "kvadr", cham=0.025, rough=0.01)
        a += da
    for ya_ in range(0, 180, 15):   # kolize po horní plochu desek: 12 úzkých pásů přes průměr = kruh (čtverec i natočené čtverce měly rohy – povrch_kolize)
        P.cols.append((M(p + Vector((0, yt / 2 + 0.03, 0)), ya_), (2 * r_out * math.tan(math.radians(7.5)) * 2, yt + 0.24, 2 * r_out)))
    # šachta a voda hluboko dole (Míša 3. 11.: „šachtu chci, jsou výjimky pro některé hlídače“): terén uvnitř věnce
    # nekreslí shader (DIRY → hra/data/diry_terenu.json), šachta je pod terénem schváleně (kontroly.json geometrie)
    P.lathe(M(p + Vector((0, -3.4, 0))), [(r_in + 0.02, 0), (r_in + 0.02, 3.3)], 20, "zdivo_hole", False, False)
    P.lathe(M(p + Vector((0, -3.0, 0))), [(r_in, 0), (r_in, 0.002)], 20, "voda")
    d_ = {"x": round(p.x, 3), "z": round(p.z, 3), "r": round(r_in + 0.01, 3), "co": "studna – šachta (otvor v síti terénu: teren_dlazdice.dira)"}
    if d_ not in DIRY: DIRY.append(d_)
    yr = yt + 0.12; hy = yr + 0.95   # osa rumpálu
    for sx in (-1, 1):   # sloupy s vidlicí a vzpěrami, zapuštěné do roubení
        xx = sx * 1.02
        P.beam(p + Vector((xx, -0.2, 0)), p + Vector((xx, hy + 1.25, 0)), 0.17, 0.17, "dub_ven", j=1)
        P.beam(p + Vector((xx, yr + 0.35, -0.08)), p + Vector((xx - sx * 0.4, yr + 0.05, -0.08)), 0.08, 0.08, "dub_ven", j=0.6)
        P.rod(p + Vector((xx - sx * 0.1, hy - 0.08, 0)), p + Vector((xx - sx * 0.1, hy + 0.08, 0)), 0.035, 8, "zelezo")
    yb = hy + 1.2   # stříška: vaznice, krokve a šindel
    for sx in (-1, 1):
        P.beam(p + Vector((sx * 1.02, yb, -0.95)), p + Vector((sx * 1.02, yb, 0.95)), 0.12, 0.13, "dub_ven", j=0.5)
    P.beam(p + Vector((-1.35, yb + 0.85, 0)), p + Vector((1.35, yb + 0.85, 0)), 0.13, 0.13, "dub_ven", j=0.5)
    for sx in (-1, 1):
        P.beam(p + Vector((sx * 1.02, yb, 0)), p + Vector((sx * 1.02, yb + 0.85, 0)), 0.1, 0.1, "dub_ven")
        for sz in (-1, 1):
            P.beam(p + Vector((sx * 1.15, yb - 0.05, sz * 1.0)), p + Vector((sx * 1.15, yb + 0.88, 0)), 0.07, 0.09, "dub_ven")
    for sz in (-1, 1):
        lib.shingle_roof(P, p + Vector((-1.38 * sz, yb - 0.08, sz * 1.12)), p + Vector((1.38 * sz, yb - 0.08, sz * 1.12)),
                         p + Vector((1.38 * sz, yb + 0.94, 0)), p + Vector((-1.38 * sz, yb + 0.94, 0)), row=0.11, length=0.36)
    c = p + Vector((0, hy, 0)); L = 1.75; rot = Matrix.Rotation(-math.pi / 2, 4, "Z")   # rumpál s klikou, lano, vědro
    P.lathe(M(c + Vector((-L / 2, 0, 0))) @ rot, [(0.03, 0.0), (0.11, 0.0), (0.11, L), (0.03, L)], 12, "dub_ven")
    for sx in (-1, 1): P.lathe(M(c + Vector((sx * 0.55 - 0.02, 0, 0))) @ rot, [(0.15, 0.0), (0.15, 0.04)], 12, "dub_ven")
    P.rod(c + Vector((-L / 2 - 0.1, 0, 0)), c + Vector((L / 2 + 0.05, 0, 0)), 0.025, 6, "zelezo")
    P.rod(c + Vector((L / 2 + 0.05, 0, 0)), c + Vector((L / 2 + 0.05, 0.32, 0)), 0.022, 6, "zelezo")
    P.rod(c + Vector((L / 2 + 0.05, 0.32, 0)), c + Vector((L / 2 + 0.28, 0.32, 0)), 0.03, 6, "dub")
    P.lathe(M(c + Vector((-0.45, 0, 0))) @ rot, [(0.125, 0.0), (0.125, 0.6)], 12, "provaz")   # navinuté lano
    P.rod(c + Vector((0.0, -0.10, 0.0)), c + Vector((0.0, -0.78, 0.0)), 0.012, 5, "provaz")   # lano z navinutého lana na bubnu (v Havranovi 12 cm vedle – viselo)
    q = c + Vector((0.0, -0.75 - 0.48, 0.0))   # vědro na laně (Havran props.bucket i s uchem – lano končí na uchu, kontrola visi_puchart)
    P.lathe(M(q), [(0.0, 0.0), (0.13, 0.0), (0.16, 0.3), (0.145, 0.3), (0.12, 0.02), (0.0, 0.02)], 16, "dub")
    for t in (0.06, 0.24):   # obruče zapuštěné do stěny vědra (samostatně visely)
        P.lathe(M(q + Vector((0, t, 0))), [(0.13 + 0.03 * t / 0.3 - 0.01, 0), (0.13 + 0.03 * t / 0.3 - 0.01, 0.025)], 16, "zelezo", False, False)
    for k_ in range(8):   # kované ucho
        a0, a1 = math.pi * k_ / 8, math.pi * (k_ + 1) / 8
        P.rod(q + Vector((0.155 * math.cos(a0), 0.28 + 0.2 * math.sin(a0), 0)), q + Vector((0.155 * math.cos(a1), 0.28 + 0.2 * math.sin(a1), 0)), 0.008, 4, "zelezo")   # ucho zapuštěné do okraje vědra

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
    "zdivo": ("castle_wall_slates", 2.5, 0.8), "kvadr": ("castle_wall_slates", 2.5, 0.82), "kvadr_sedy": ("castle_wall_slates", 2.5, 0.8),   # jedno zdivo (Míša 4. 11.: dva odstíny zdí v blocích)
    "omitka": ("omitka_vapno", 2.5, 1.0), "zdivo_omitka": ("omitka_vapno", 2.5, 0.95),   # vápenná omítka světlá (okna_palace.md)
    "kvadr_okno": ("kamen_teseny", 0.8, 1.0),   # tesané ostění oken – světlejší než zdivo
    "sindel": ("sindel", 1.5, 1.35), "sindel_hra": ("sindel", 1.5, 1.35),
    "rez_drevo": ("letokruhy", 1.0, 0.85),   # čela (textura zešedlá na tón zvětralého dubu – čerstvě oranžová svítila, 3. 11.) trámů a prken: letokruhy (Havran vlastni._tex_endgrain; Míša 3. 11.: „víš jak vypadá řez dřeva?“)
    "provaz": ("rough_wood", 0.3, 0.55), "voda": ("droba", 2.0, 0.12),
    "dub": ("rough_wood", 0.5, 0.75), "hraz": ("rough_wood", 0.5, 0.6), "prkna_ven": ("wood_planks_grey", 1.5, 0.95),
    "okenice": ("wood_planks_grey", 1.5, 0.8), "dvere": ("wood_planks_grey", 1.5, 0.7),
    "prkno": ("rough_wood_sedy", 0.6, 0.95), "prkno_ven": ("prkna_atlas", 2.56, 1.0), "prkno_dvere": ("rough_wood_sedy", 0.6, 0.72),   # jedno prkno (hrad_vzhled.json drevo.deska)
    "skala_mech": ("mossy_rock", 2.0, 1.0), "skala_tm": ("droba", 2.5, 0.8), "skala_sv": ("droba", 3.0, 1.25), "skala": ("droba", 2.5, 1.05), "sut": ("droba", 1.2, 0.7),
}
MATS = {}
def material(jm):
    if jm in MATS: return MATS[jm]
    m = bpy.data.materials.new(jm); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    key = max((k for k in TEX if jm.startswith(k)), key=len, default=None)   # nejdelší shoda (prkno_dvere ≠ prkno)
    if jm in ("tma",):
        bs.inputs["Base Color"].default_value = (0.012, 0.01, 0.009, 1); bs.inputs["Roughness"].default_value = 1.0
    elif jm.startswith(("zelezo", "hreb", "kovani")) or "zelez" in jm:
        bs.inputs["Base Color"].default_value = (0.05, 0.048, 0.045, 1); bs.inputs["Metallic"].default_value = 0.8; bs.inputs["Roughness"].default_value = 0.6
    elif jm == "prapor":
        bs.inputs["Base Color"].default_value = (0.42, 0.05, 0.04, 1); bs.inputs["Roughness"].default_value = 0.9
    elif jm.startswith(("voda", "breh")):   # ve hře nahrazeno shaderem voda.gdshader / terénu (zem.gdshader)
        bs.inputs["Base Color"].default_value = (0.1, 0.13, 0.11, 1); bs.inputs["Roughness"].default_value = 0.1
    elif jm.startswith("sklo"):   # terčíkové sklo: průhledné, nazelenalé (Míša 4. 11.: „neprůhledná okna“ – dřív tmavé neprůhledné)
        bs.inputs["Base Color"].default_value = (0.55, 0.62, 0.52, 1); bs.inputs["Roughness"].default_value = 0.1
        bs.inputs["Alpha"].default_value = 0.28; m.blend_method = "BLEND"
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

def vlakna_dreva(ob, cfg):
    """Dřevo jako dřevo (Míša 3. 11.: „trám bude trám, deska bude deska… víš jak vypadá vazba a řez dřeva?“; Havran
    vlastni._box: vlákna podél nejdelší strany): každý dřevěný díl (ostrov sítě) dostane osu podle nejdelšího rozměru;
    boky mají UV s vlákny podél osy (v metrech, pak /vel jako ostatní), čela materiál rez_drevo s letokruhy přes průřez."""
    import bmesh, numpy as _np
    me = ob.data; mats = [mm.name if mm else "" for mm in me.materials]
    Dv = cfg["drevo"]; dm = {i for i, n in enumerate(mats) if any(n.startswith(x) for x in Dv["materialy"])}
    if not dm: return
    if "rez_drevo" not in mats: me.materials.append(material("rez_drevo")); mats.append("rez_drevo")
    ir = mats.index("rez_drevo")
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); uvl = bm.loops.layers.uv.verify()
    wf = [f for f in bm.faces if f.material_index in dm]; ws = set(wf); seen = set()
    for f0 in wf:
        if f0 in seen: continue
        isl = []; st = [f0]; seen.add(f0)   # ostrov: dřevěné plochy spojené vrcholy
        while st:
            f = st.pop(); isl.append(f)
            for v in f.verts:
                for g in v.link_faces:
                    if g in ws and g not in seen: seen.add(g); st.append(g)
        jm0 = mats[isl[0].material_index]; ds = Dv.get("deska")
        if ds and jm0.startswith(("dvere", "okenice")):   # křídla a okenice = prkna Havran kit.board/plank (spojená v jeden ostrov):
            cil = ds["material"][jm0.split(".")[0]]       # jejich UV má u = vlákna (Havran swap) -> prohodit na V jako ostatní dřevo
            if cil not in mats: me.materials.append(material(cil)); mats.append(cil)
            for f in isl:
                f.material_index = mats.index(cil)
                for l in f.loops: u_, v_ = l[uvl].uv; l[uvl].uv = (v_, u_)
            continue
        P = _np.array([v.co[:] for f in isl for v in f.verts]); c = P.mean(0)
        w, V = _np.linalg.eigh(_np.cov((P - c).T) + _np.eye(3) * 1e-9); osa = Vector(V[:, 2]).normalized()
        if w[2] < 1.5 * w[1]: continue   # krychle/deska bez jasné délky – nechat
        pr = [Vector(v.co) - Vector(c) for f in isl for v in f.verts]
        e1 = osa.orthogonal().normalized(); e2 = osa.cross(e1).normalized()
        a1 = [p.dot(e1) for p in pr]; a2 = [p.dot(e2) for p in pr]; r1 = (max(a1) - min(a1)) / 2 + 1e-4; r2 = (max(a2) - min(a2)) / 2 + 1e-4
        ds = Dv.get("deska"); im_bok = None   # prkno: boky texturou jednoho kusu dřeva (ne podlahy z prken)
        if ds and min(r1, r2) * 2 <= ds["max_tloustka_m"] and max(r1, r2) * 2 <= ds["max_sirka_m"]:
            jm0 = mats[isl[0].material_index]; cil = next((v for k, v in ds["material"].items() if jm0.startswith(k)), None)
            if cil:
                if cil not in mats: me.materials.append(material(cil)); mats.append(cil)
                im_bok = mats.index(cil)
        for f in isl:
            n = f.normal
            if im_bok is not None and abs(n.dot(osa)) <= 0.7: f.material_index = im_bok
            if abs(n.dot(osa)) > 0.7:   # čelo: letokruhy přes průřez (střed dřeně uprostřed)
                f.material_index = ir
                for l in f.loops:
                    q = Vector(l.vert.co) - Vector(c); l[uvl].uv = (0.5 + q.dot(e1) / (2 * r1) * 0.9, 0.5 + q.dot(e2) / (2 * r2) * 0.9)
            else:   # bok: vlákna podél osy
                b_ = osa.cross(n).normalized()
                for l in f.loops:
                    q = Vector(l.vert.co); l[uvl].uv = (q.dot(b_), q.dot(osa))
    bm.to_mesh(me); bm.free()

def relief(ob, cfg):
    """Kámen a dřevo jako geometrie (hrad_vzhled.json): plochy zdiva rozdělit na mřížku a posunout vrcholy podél normály
    podle vzoru kamenů v řádcích (spáry dovnitř, kameny ven); trámy a prkna rozdělit podél a hrubě rozsekat. Posun podle
    polohy ve světě a normály vrcholu – sousední plochy a kvádry zůstanou spojené (žádné škvíry v rozích)."""
    import bmesh, math as m_
    from mathutils import Vector
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me)
    mats = [mm.name if mm else "" for mm in me.materials]
    Z = cfg["zdivo"]; Dv = cfg["drevo"]
    def je(f, seznam): return any(mats[f.material_index].startswith(x) for x in seznam) if f.material_index < len(mats) else False
    # 1) dělení: hrany ploch zdiva a dřeva delší než krok
    for seznam, krok, minp in ((Z["materialy"], Z["mrizka_m"], Z["min_plocha_m2"]), (Dv["materialy"], Dv["krok_m"], 0.0)):
        fs = [f for f in bm.faces if je(f, seznam) and f.calc_area() >= minp]
        if not fs: continue
        hrany = {e for f in fs for e in f.edges if e.calc_length() > krok * 1.4}
        for e in list(hrany):
            pass
        if hrany:
            cuts = {}
            for e in hrany: cuts.setdefault(max(1, min(24, int(e.calc_length() / krok))), []).append(e)
            for n_, es in cuts.items():
                bmesh.ops.subdivide_edges(bm, edges=es, cuts=n_, use_grid_fill=True)
    bm.normal_update()
    def h(a, b, c=0): return (m_.sin(a * 127.1 + b * 311.7 + c * 74.7) * 43758.5453) % 1.0
    def kamen(p):   # 0 ve spáře .. 1 uprostřed kamene
        y = p.z   # Blender Z = nahoru
        r = m_.floor(y / Z["vrstva_m"]); fy = y / Z["vrstva_m"] - r
        u = p.x * 0.7071 + p.y * 0.7071 + (p.x - p.y) * 0.31   # vodorovná souřadnice (směrově neutrální)
        Lk = Z["kamen_delka_m"][0] + (Z["kamen_delka_m"][1] - Z["kamen_delka_m"][0]) * h(r, 1.0)
        su = u / Lk + h(r, 2.0); c = m_.floor(su); fu = su - c
        sp = Z["spara_m"] / Z["vrstva_m"]; spu = Z["spara_m"] / Lk
        dy = min(fy, 1 - fy) / sp; du = min(fu, 1 - fu) / spu
        t = max(0.0, min(1.0, min(dy, du)))
        return t * t * (3 - 2 * t), h(r, c)
    for v in bm.verts:
        fz = [f for f in v.link_faces if je(f, Z["materialy"])]
        fd = [f for f in v.link_faces if je(f, Dv["materialy"])]
        if fz:
            q = v.co / Z["vlna_m"]   # zvlnění líce (plynulé, stejné pro sousední plochy – podle polohy)
            vl = (m_.sin(q.x * 1.7 + m_.sin(q.z * 1.3)) + m_.sin(q.y * 1.9 + q.z * 0.7) + m_.sin((q.x + q.y) * 1.1 - q.z * 2.3)) / 3.0
            v.co += v.normal * (Z["vlna_ampl_m"] * vl)
        elif fd:
            v.co += v.normal * (Dv["amplituda_m"] * (h(round(v.co.x * 7), round(v.co.y * 7), round(v.co.z * 7)) - 0.5) * 2)
    # vystupující lomové kameny na velkých plochách zdiva (sražené hrany = zkosený kvádr ze 2 vrstev vrcholů)
    import random as rnd_
    rg = rnd_.Random(1393)
    for f in [f for f in bm.faces if je(f, Z["materialy"]) and f.calc_area() >= 0.05]:
        pass
    kridla = []   # křídla vrat/dveří (kit.movable, otevřená ke zdi): místní obálky
    for o_ in bpy.data.objects:
        if o_.name.startswith("Pohyb_") and o_.type == "MESH" and o_.data.vertices:
            vs_ = [v.co for v in o_.data.vertices]
            kridla.append((o_.matrix_world.inverted(),
                           [min(v[k] for v in vs_) for k in range(3)], [max(v[k] for v in vs_) for k in range(3)]))
    plochy = {}
    for f in bm.faces:   # po dělení jsou plochy malé – vybírat podle normály a polohy, hustota na m²
        if not je(f, Z["materialy"]) or abs(f.normal.z) > 0.5: continue
        if rg.random() > Z["kameny_na_m2"] * f.calc_area(): continue
        c = f.calc_center_median(); nrm = f.normal.copy()
        cw = ob.matrix_world @ c   # Blender z nahoru -> hra (x, z = -y): kámen pod zemí (základy) se nesází (kontrola pod_terenem)
        if cw.z < float(ter(cw.x, -cw.y)) + Z.get("kamen_nad_terenem_m", 0.15): continue
        if any(all(-0.2 - 1e-3 <= (im_ @ cw)[k] - lo[k] and (im_ @ cw)[k] <= hi[k] + 0.2 for k in range(3)) for im_, lo, hi in kridla): continue   # kámen by prorazil otevřené křídlo vrat (tablet 3. 11.)
        tx = nrm.cross(Vector((0, 0, 1))).normalized(); ty = Vector((0, 0, 1))
        sx = rg.uniform(*Z["kamen_rozmer_m"][0]) / 2; sy = rg.uniform(*Z["kamen_rozmer_m"][1]) / 2; vy = rg.uniform(*Z["kamen_vystup_m"])
        ch = min(sx, sy) * 0.35
        base = [c + tx * a * sx + ty * b * sy - nrm * 0.02 for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        top = [c + tx * a * (sx - ch) + ty * b * (sy - ch) + nrm * vy + tx * rg.uniform(-0.01, 0.01) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        vb = [bm.verts.new(p_) for p_ in base]; vt = [bm.verts.new(p_) for p_ in top]
        mi = f.material_index
        for i in range(4):
            nf = bm.faces.new((vb[i], vb[(i + 1) % 4], vt[(i + 1) % 4], vt[i])); nf.material_index = mi
        nf = bm.faces.new(vt); nf.material_index = mi
    bm.normal_update()
    uv = bm.loops.layers.uv.active
    if uv:   # UV nových ploch: planární podle polohy (měřítko jako zdivo)
        for f in bm.faces:
            if len(f.loops) and f.loops[0][uv].uv.length == 0 and f.loops[1][uv].uv.length == 0:
                n_ = f.normal; ax = 0 if abs(n_.x) < abs(n_.y) else 1
                for l in f.loops:
                    p_ = l.vert.co; l[uv].uv = ((p_.y if ax else p_.x) / 2.5, p_.z / 2.5)
    bm.to_mesh(me); bm.free(); me.update()

SVET_UV = ("zdivo", "omitka", "skala")
SVET_UV_PRESNE = {"kvadr"}   # nárožní kvádry: stejná fotka zdiva – musí navazovat (Míša 4. 11.: obdélníky jiné textury na rohu věže)
# zdivo s náhodným nafouknutím 0,4–3 mm (líce přesahujících kusů se nekryjí přesně – bez blikání); textura navazuje (světové UV)
def odstran_vnitrni_cela(P):
    """Kusy zdiva na sraz: dvojice stěn se shodnými rohy (čela sousedních kvádrů uvnitř zdi) pryč – nejsou vidět a na spoji
    dělaly tmavé čáry (stín/hloubka). Jen materiály zdi."""
    zid = {i for i, n in enumerate(P.mats) if n.startswith(("zdivo", "omitka")) or n == "kvadr"}
    kl = {}
    for fi, f in enumerate(P.f):
        if f[2] not in zid or len(f[0]) != 4: continue
        k = tuple(sorted(tuple(round(c, 3) for c in P.v[i]) for i in f[0]))
        kl.setdefault(k, []).append(fi)
    pryc = {fi for v in kl.values() if len(v) >= 2 for fi in v}
    if pryc: P.f = [f for fi, f in enumerate(P.f) if fi not in pryc]
    return len(pryc)   # zdivo a omítka: UV ve světových souřadnicích (Míša 4. 11.: „švy ve zdi“ – každý kvádr měl vlastní náhodný posun textury)
def svet_uv(me):
    """Líc zdi složený z více kvádrů: textura navazuje přes spáry dílů. Svislá plocha: u = vodorovně podél plochy, v = výška;
    vodorovná: u = x, v = y (Blender). Sousední souběžné plochy tak mají stejnou mapu – šev zmizí."""
    uv = me.uv_layers[0].data; vs = me.vertices
    for poly in me.polygons:
        mt = me.materials[poly.material_index]
        if mt is None or not (mt.name.startswith(SVET_UV) or mt.name in SVET_UV_PRESNE): continue
        n = poly.normal
        if abs(n.z) > 0.7:
            for li in poly.loop_indices:
                co = vs[me.loops[li].vertex_index].co; uv[li].uv = (co.x, co.y)
        else:
            t = Vector((-n.y, n.x, 0.0)).normalized()
            for li in poly.loop_indices:
                co = vs[me.loops[li].vertex_index].co; uv[li].uv = (co.dot(t), co.z)

def svar_zdi(me):
    """Kusy zdiva na sraz: svařit shodné vrcholy a smazat vnitřní čela (dvě shodné stěny proti sobě) – jinak tmavé svislé
    čáry na líci (Míša 4. 11.: „švy ve zdi“ i po světových UV; stín a mipmapy na styku dvou sítí)."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    zid = {i for i, m in enumerate(me.materials) if m is not None and m.name.startswith(("zdivo", "omitka"))}
    vs = {v for f in bm.faces if f.material_index in zid for v in f.verts}
    bmesh.ops.remove_doubles(bm, verts=list(vs), dist=0.002)
    klic = {}
    for f in bm.faces:
        if f.material_index not in zid: continue
        klic.setdefault(tuple(sorted(v.index for v in f.verts)), []).append(f)
    pryc = [f for fs in klic.values() if len(fs) >= 2 for f in fs]
    if pryc: bmesh.ops.delete(bm, geom=pryc, context="FACES")
    bm.to_mesh(me); bm.free()
    print("SVAR_ZDI vnitřních čel smazáno %d" % len(pryc), flush=True)

def uloz(parts, jmeno, kolize=False, vzhled=None):
    for o in list(bpy.data.objects):
        if not (kolize and o.name.startswith("Pohyb_")): bpy.data.objects.remove(o)   # křídla vrat (kit.movable) zůstanou
    coll = bpy.context.scene.collection
    if kolize:   # Havran: kolize z kvádrů (zdi, podlahy, mostovky, schody jako rampy), ne z jemné geometrie prken a zábradlí
        PK = Part("KOLIZE")
        for P in parts:
            for m, sz in P.cols: PK.box(m, sz, "kolize")
        parts = list(parts) + [PK]
    nc_ = sum(odstran_vnitrni_cela(P) for P in parts)
    print("VNITRNI_CELA odstraněno %d" % nc_, flush=True)
    for P in parts:
        for mn in P.mats: lib.MAT[mn] = material(mn)
        ob = P.commit(coll)
        if ob is None: continue
        if vzhled and not ob.name.startswith("KOLIZE"): vlakna_dreva(ob, vzhled)   # PŘED dělením UV/vel (dřív až po – měřítko textur dřeva se ztratilo)
        me = ob.data; uv = me.uv_layers[0].data
        svet_uv(me)
        for poly in me.polygons:
            vel = me.materials[poly.material_index].get("vel", 1.0) if me.materials[poly.material_index] else 1.0
            for li in poly.loop_indices:
                uv[li].uv = (uv[li].uv[0] / vel, uv[li].uv[1] / vel)
        for mo in list(ob.modifiers): ob.modifiers.remove(mo)   # bevel jen pro Cycles; ve hře ne
        if vzhled and not ob.name.startswith("KOLIZE"): relief(ob, vzhled)
    for ob in [o for o in bpy.data.objects if o.name.startswith("Pohyb_") and o.type == "MESH"]:   # křídla vrat: UV v metrech -> fotka
        if vzhled: vlakna_dreva(ob, vzhled)   # křídla vrat: prkna s vlákny (dřív bez – tablet 3. 11. „vrata průsvitná, žádné dřevo“)
        me = ob.data; uv = me.uv_layers[0].data
        for poly in me.polygons:
            mt = me.materials[poly.material_index] if me.materials else None
            vel = mt.get("vel", 1.0) if mt else 1.0
            for li in poly.loop_indices: uv[li].uv = (uv[li].uv[0] / vel, uv[li].uv[1] / vel)
        for mo in list(ob.modifiers): ob.modifiers.remove(mo)
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
