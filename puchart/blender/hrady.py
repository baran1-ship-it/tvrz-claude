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
HRADBA_OKENKA = False   # úzká okénka v nejvyšším patře i na straně ve zdi (hrad A podle kresby misa_04)
STRECHA_POMER = 0.62   # výška sedlové střechy / šířka (palác B 1,0 podle kresby misa_01)
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

OKNA_SVETLA = []   # denní světlo z oken do místnosti (Míša 9. 11.: „ve většině místností je tma“) → hra/data/svetla.json
POSL_OKNA = []   # okna poslední postavené budovy (strana, od, šířka, y0, y1, …) – vnitřek paláce (obklad světnice) se jim vyhne
BEZ_OKEN = []   # [(a, b, y0, y1)] vnitřní schodiště u zdí – okna tam ne (puchart_hrad plní před stavbou paláce)
def _dist_seg(p, a, b):
    p = Vector((p.x, 0, p.z)); a = Vector((a.x, 0, a.z)); b = Vector((b.x, 0, b.z)); ab = b - a
    t_ = 0.0 if ab.length < 1e-6 else max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t_)).length
HRADBY = []  # [(a, b, koruna_y)] osy hradeb (puchart_hrad plní) – strany budov v hradbě kamenné, okna nad korunou
DIRY = []    # díry v terénu (studna): shader terénu je nekreslí
BRANY = []   # (práh vnějšího líce průjezdu, výška podlahy) – mosty se napojují na nejbližší

# ------------------------------------------------------------------ zdi
CIMB = json.load(open(os.path.join(K, "pravidla/svet/hrad_vzhled.json")))["cimburi"]
def zed_plynula(P, a, b, t, h, mat="zdivo", pata=2.0, krok=1.5, e0=0.0, e1=0.0):
    """Hradba s korunou plynule po terénu (vlnka nahoru a dolů, bez stupňů – Míša 5. 11., kresba misa_04): kusy po krok m
    se šikmou korunou, sousední kusy sdílejí čela (odstran_vnitrni_cela je smaže), pata pod nejnižším terénem úseku."""
    a = Vector((a[0], 0, a[1])); b = Vector((b[0], 0, b[1])); L = (b - a).length; d = (b - a) / L; s = d.cross(UP).normalized()
    n = max(1, int(math.ceil((L + e0 + e1) / krok))); ss = np.linspace(-e0, L + e1, n + 1)
    tr = [max(ter(*(a + d * q + s * o).xz) for o in (-t / 2, 0, t / 2)) for q in ss]
    tr = np.convolve(np.pad(tr, 2, mode="edge"), np.ones(5) / 5, mode="valid")   # vyhlazená koruna (vlnka, ne kopie každé nerovnosti)
    yt = [float(v) + h for v in tr]; y0 = min(ter(*(a + d * q).xz) for q in ss) - pata
    out = []
    for k in range(n):
        q0, q1 = a + d * ss[k], a + d * ss[k + 1]
        vs = [q0 - s * t / 2 + UP * y0, q1 - s * t / 2 + UP * y0, q1 + s * t / 2 + UP * y0, q0 + s * t / 2 + UP * y0,
              q0 - s * t / 2 + UP * yt[k], q1 - s * t / 2 + UP * yt[k + 1], q1 + s * t / 2 + UP * yt[k + 1], q0 + s * t / 2 + UP * yt[k]]
        P.mesh([tuple(v) for v in vs], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)], mat)
        ym = (yt[k] + yt[k + 1]) / 2; c = (q0 + q1) / 2
        P.cols.append((M((c.x, (y0 + ym) / 2, c.z), basis=frame(d)), (t, ym - y0, ss[k + 1] - ss[k])))
        out.append((float(ss[k]), float(ss[k + 1]), ym))
    return out

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
                P.box(M((p.x, y1 + CIMB["vyska_m"] / 2, p.z), basis=frame(d)), (t * 0.4, CIMB["vyska_m"], sw), mat + "_koruna" if mat == "zdivo" else mat)   # stínka holý kámen (Míša 10. 11.)
    return out

NAROZI_POKOS = True
def zed_cara(P, osa, t, h, mat="zdivo", cimburi=True, koruny=None, plynule=False):
    """Hradba po lomené čáře (3. 11., Míša: hradby nenavazují): úseky bez přesahů, v každém vrcholu nárožní pilíř t × t
    natočený podle osy úhlu, výška = vyšší z korun sousedních úseků (žádné prolínání kvádrů a světlé čelo v rohu)."""
    if plynule:   # koruna plynule po terénu: konce úseků na pokos (přesah t/2·tg(úhel/2)), nároží bez pilíře
        def _e(i_, kon):
            if (kon == 0 and i_ == 0) or (kon == 1 and i_ == len(osa) - 2): return 0.02
            p0 = np.array(osa[i_ - 1 if kon == 0 else i_], float); p1 = np.array(osa[i_ if kon == 0 else i_ + 1], float); p2 = np.array(osa[i_ + 1 if kon == 0 else i_ + 2], float)
            u = p1 - p0; v = p2 - p1; u /= np.linalg.norm(u); v /= np.linalg.norm(v)
            return t / 2 * math.tan(math.acos(max(-1.0, min(1.0, float(u @ v)))) / 2) + 0.02
        return [zed_plynula(P, p, q, t, h, mat=mat, e0=_e(k, 0), e1=_e(k, 1)) for k, (p, q) in enumerate(zip(osa, osa[1:]))]
    useky = [zed(P, p, q, t, h, mat=mat, cimburi=cimburi and not (koruny and koruny[k] is not None), pilire=True, koruna=(koruny[k] if koruny else None)) for k, (p, q) in enumerate(zip(osa, osa[1:]))]   # úsek s pevnou korunou (pod ochozem u branky) bez stínek – ochoz po něm vede k portálku (povrch_kolize 10. 11.)
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

STRECHA = json.load(open(os.path.join(K, "pravidla/svet/hrad_vzhled.json"))).get("strecha", {})

def strecha_okraje(P, eL, eR, rR, rL, w_okap):
    """Tloušťka střechy a co je vidět pod okapem (Míša 5. 11.: „přesahy střech“; KCD reference): bednění na spodní straně
    přesahu, čelní prkno okapu, prkna na štítových hranách a konce krokví od líce zdi k okapu."""
    tl = STRECHA.get("tloustka_m", 0.16)
    e_ = (eR - eL); L_ = e_.length; e_ /= L_; sp = (rL - eL); sl = sp.length; sp /= sl
    n_ = e_.cross(sp).normalized()
    if n_.y < 0: n_ = -n_
    P.box(M((eL + eR) / 2 - n_ * (tl / 2 - 0.03), basis=frame(e_, up=n_)), (0.05, tl, L_), "prkna_ven", collide=None)   # čelní prkno okapu
    for q in (eL, eR):   # štítová prkna podél spádu
        r_ = q + sp * sl
        P.box(M((q + r_) / 2 - n_ * (tl / 2 - 0.03), basis=frame(sp, up=n_)), (0.05, tl, sl), "prkna_ven", collide=None)
    ww = min(w_okap, sl)   # bednění pod přesahem (od okapu k líci zdi)
    P.mesh([eL - n_ * (tl - 0.03), eR - n_ * (tl - 0.03), eR + sp * ww - n_ * (tl - 0.03), eL + sp * ww - n_ * (tl - 0.03)], [(0, 3, 2, 1)], "prkna_ven")
    kr = STRECHA.get("krokve_po_m", 0.9); pr = STRECHA.get("krokev_prurez_m", [0.12, 0.15]); nk = max(2, int(L_ / kr))
    for i in range(1, nk):   # konce krokví pod přesahem
        q = eL + e_ * (L_ * i / nk) - n_ * (tl - 0.03 + pr[1] / 2)
        P.beam(q + sp * 0.05, q + sp * max(0.1, ww - 0.03), pr[0], pr[1], "dub", up=n_, collide=None)

OKAP_STRANY = {}   # přesah okapu podle strany budovy (0 = +s, 2 = −s): v hradbě 0 (střecha končí na koruně – Míša 9. 11.: střecha
                   # trčela přes vnější líc hradby pod cimbuřím), nad pavlačí krátký (Míša 6. 11.: „co přesahuje, useknout“)

def strecha_sedlova(P, a, b, hloubka, y, vyska, presah=0.5, stity="drevo", t_zdi=0.0, okap_s=None):
    """Sedlová střecha nad obdélníkem s osou a->b (hřeben podél osy) a štíty na koncích. Přesahy z hrad_vzhled.json strecha
    (okap 0,75 m, štít 0,35 m – Míša 5. 11.), tloušťka, bednění a krokve pod okapem."""
    a = Vector((a[0], 0, a[1])); b = Vector((b[0], 0, b[1])); d = (b - a).normalized(); s = d.cross(UP).normalized()
    po_ = STRECHA.get("presah_okap_m", presah); ps_ = STRECHA.get("presah_stit_m", presah)
    po = po_ + t_zdi / 2; ps = ps_ + t_zdi / 2   # přesah od vnějšího líce zdi (hloubka je mezi osami zdí – u paláce zbylo jen 0,2 m)
    a2, b2 = a - d * ps, b + d * ps
    sk_ = vyska / (hloubka / 2)   # sklon střechy
    # rovina střechy prochází VNĚJŠÍ hranou koruny zdi (dřív osou zdi → vnější polovina koruny trčela střechou o sk·t/2,
    # Míša 10. 11. „pořád ti lezou zdi ze střech“, test smyslu zed_nad_strechou); štíty dorovnané o stejný kus
    dz_ = sk_ * t_zdi / 2; y0_ = y; y = y + dz_
    okap_s = okap_s or {}
    def okap(sg):   # vodorovný přesah od osy zdi a výška okapu na dané straně
        po_s = okap_s.get(0 if sg > 0 else 2, po_)
        po_t = po_s + (t_zdi / 2 if po_s > 0 else 0.0)
        return hloubka / 2 + po_t, y - sk_ * po_t, po_s
    w1, ye1, p1 = okap(1); w2, ye2, p2 = okap(-1)
    eL1, eR1 = a2 + s * w1 + UP * ye1, b2 + s * w1 + UP * ye1
    eL2, eR2 = b2 - s * w2 + UP * ye2, a2 - s * w2 + UP * ye2
    rA, rB = a2 + UP * (y + vyska), b2 + UP * (y + vyska)
    lib.shingle_roof(P, eL1, eR1, rB, rA)
    lib.shingle_roof(P, eL2, eR2, rA, rB)
    if DETAIL:
        for (eL, eR, r1, r2, pp) in ((eL1, eR1, rB, rA, p1), (eL2, eR2, rA, rB, p2)):
            if pp > 0.05: strecha_okraje(P, eL, eR, r1, r2, math.hypot(pp, sk_ * pp))   # přesah podél spádu od okapu k líci zdi
    hs_ = hloubka / 2 + t_zdi / 2   # štít až k vnějším lícům bočních zdí (Míša 12. 11.: díry v podkroví paláce na obou stranách –
    for e, f, r in ((a + s * hs_, a - s * hs_, a), (b - s * hs_, b + s * hs_, b)):   # štít končil v osách zdí, nad vnější polovinou koruny
        if stity == "drevo":                                                         # zůstal trojúhelník do nebe)
            # bedněný štít ze svislých prken, prkna se o 2 cm překrývají (dřív 1 cm mezery – světlé čáry)
            k = 0.0; L = (f - e).length; dd = (f - e).normalized(); PK_ = 0.24
            while k < L - 0.01:
                u_ = abs((k + PK_ / 2) - L / 2); hh = dz_ + vyska - sk_ * u_ + min(sk_ * PK_ / 2, 0.04)   # střed prkna pod střechou + do tloušťky krytiny (štěrbiny pod šikmou střechou zakryté)
                if hh > 0.03:
                    x = e + dd * min(k + PK_ / 2, L - PK_ / 2)
                    kit.plank(P, x + UP * y0_, x + UP * (y0_ + hh), PK_ + 0.02, 0.04, "prkna_ven", up=(r - (a + b) / 2).normalized(), wear=0.5)
                k += PK_
            for k_ in range(4):   # kolize prkenného štítu: trojúhelník ze 4 zužujících se desek (povrch_kolize 9. 11.: štítem se procházelo)
                h0_, h1_ = (vyska + dz_) * k_ / 4, (vyska + dz_) * (k_ + 1) / 4
                P.cols.append((M((e + f) / 2 + UP * (y0_ + (h0_ + h1_) / 2), basis=frame(dd)), (0.12, h1_ - h0_, L * (1 - k_ / 4))))
        else:   # kamenný štít od vnějších líců bočních zdí (koruna y0_) k hřebeni – přesně v rovině střechy, bez klínu do nebe nad korunou
            P.tri(e + UP * y0_, f + UP * y0_, r + UP * (y + vyska), 0.6, "zdivo")

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
def vez(P, stred, rozmer, vyska, strecha="jehlan", yaw_d=(1, 0), brana=False, yf=None, patro=False, portalky=None, vyklenek=0.0):
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
                if jm == "-s":   # okénko stráže do pole před bránou (Míša 6. 11.: „ať stráž vidí, kdo je před branou, nic velkého“)
                    ow_, oy0_, oy1_ = 0.36, yp + 1.05, yp + 1.85
                    kusy = [k for k in kusy if not (k[0] < 0 < k[1])] + [(k[0], -ow_ / 2, yp, y1) for k in kusy if k[0] < 0 < k[1]] + \
                           [(ow_ / 2, k[1], yp, y1) for k in kusy if k[0] < 0 < k[1]] + [(-ow_ / 2, ow_ / 2, yp, oy0_), (-ow_ / 2, ow_ / 2, oy1_, y1)]
                    fo_ = c + nrm * vzd   # tesané ostění: překlad a práh z kvádru
                    for yy_, hh_ in ((oy0_ - 0.06, 0.12), (oy1_ + 0.06, 0.12)):
                        kit.stone(P, M(fo_ - nrm * (tw / 2) + UP * yy_, basis=frame(T)), (tw + 0.04, hh_, ow_ + 0.3), "kvadr_okno", cham=0.02, rough=0.0)
                for u0_, u1_, ya, yb in kusy:
                    if u1_ - u0_ > 0.02: q = cc + T * ((u0_ + u1_) / 2); P.box(M((q.x, (ya + yb) / 2, q.z), basis=frame(T)), (tw, yb - ya, u1_ - u0_), "zdivo")
            P.box(M((c.x, yp - 0.03, c.z), basis=frame(d)), (dpt - 2 * tw, 0.06, w - 2 * tw), "prkna_ven")   # podlaha strážnice
            VEZ_PATRO.append({"stred": c.copy(), "d": d.copy(), "s": s.copy(), "w": w, "dpt": dpt, "yp": yp, "dvere": dvere_, "dvere_w": dw_, "tw": tw})
        P.box(M((c.x, (y0 + yf) / 2, c.z), basis=frame(d)), (dpt, yf - y0, pw + 0.02), "zdivo")                          # pod podlahou
        # valenou lomenou klenbu průjezdu staví portál (portaly.doorway přes celou hloubku věže)
        P.box(M(c + UP * (yf - 0.05), basis=frame(d)), (dpt, 0.1, Wo), "kvadr_sedy")
        # portály na obou lících a vrata (vnitřní strana otevřená)
        f = c - s * (dpt / 2 - vyklenek)   # vnější líc (ven = −s): ostění, křídla v polodrážce, klenba skrz, na vnitřním líci záklenek;
        m = M(f + UP * yf, basis=Matrix((-d, UP, -s)).transposed())   # s padacím mostem portál na dně výklenku (otvor průjezdu Wo × Ho, Míša 12. 11.)
        kit.doorway(P, m, kind="hlavni", w=pw, h=ph, depth=dpt - vyklenek, top="lomeny", leaf=True, double=True, venec_vnitrni=True)
        BRANY.append((c - s * (dpt / 2 - vyklenek), yf))   # práh na dně výklenku – sem vede most
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
        strecha_sedlova(P, (a.x, a.z), (b.x, b.z), dpt, top, dpt * 0.8, presah=0.35, stity=STRECHA.get("stity", "drevo"))
    return y1

# ------------------------------------------------------------------ budovy
def narozi(P, R, stena_a, stena_b, y0, y1, mat="zdivo", seme=0):
    """Nárožní kameny (Míša 9. 11.: „hrany nemůžou být takhle dokonalé, je to postavené z kamení“; rozhodnutí: nárožní kameny):
    na svislém vnějším rohu R lomové kameny ze stejného zdiva – střídavě vazák dlouhý podél stěny a a krátký podél b, vrstvy
    0,25–0,45 m, vystupují 1–5 cm z líce a přesahují roh, otlučené hrany (kit.stone). Silueta hrany je zubatá jako u
    lomového zdiva (Puchart GC80T08: lomový kámen, nároží z větších kamenů). stena = (směr podél líce od rohu, vnější normála)."""
    if mat == "zdivo": mat = "zdivo_narozi"   # nárožní kameny holé, bez ostrůvků omítky (Míša 10. 11.)
    if y1 - y0 < 0.5: return
    # rozpočet scén (hlídač 9. 11.: +100 k troj.): otlučené kameny jen do 6 m nad terénem (vidět zblízka), výš a ve vzdálené
    # verzi hradu kvádry se stejným natočením a výstupkem (silueta stejná – bez doskoku při přepnutí LOD)
    rg = __import__("random").Random(int(abs(R.x * 131 + R.z * 71)) + seme)
    y = y0; k = rg.randrange(2)
    while y < y1 - 0.12:
        h = min(rg.uniform(0.25, 0.45), y1 - y)
        for i_, (dx, nx) in enumerate((stena_a, stena_b)):
            dlouhy = (i_ == k % 2)
            L = rg.uniform(0.55, 0.85) if dlouhy else rg.uniform(0.28, 0.42)
            dep = rg.uniform(0.28, 0.4); pv = rg.uniform(0.01, 0.035); pk = rg.uniform(0.0, 0.04)   # výstupek z líce a přes roh
            c = R + dx * (L / 2 - pk) - nx * (dep / 2 - pv) + UP * (y + h / 2 + rg.uniform(-0.01, 0.01))
            bz = frame(dx) @ Matrix.Rotation(math.radians(rg.uniform(-2.5, 2.5)), 3, "Z") @ Matrix.Rotation(math.radians(rg.uniform(-2.0, 2.0)), 3, "Y")   # lomový kámen není v lati
            if DETAIL and y - y0 < 2.5: kit.stone(P, M(c, basis=bz), (dep, h - 0.03, L), mat, cham=rg.uniform(0.05, 0.09), rough=rg.uniform(0.03, 0.05))
            else: P.box(M(c, basis=bz), (dep, h - 0.03, L), mat, collide=None)
        y += h; k += 1

def vypln_okna(P, m, x0, x1, y0, y1, z, mat):
    """Výplň okna dvěma plochami (KCD fotky: okna zvenku tmavá): dovnitř `mat` (ve hře svítí denním světlem), ven `mat_ven`
    (tmavé, stíněné); m = rám okna s lokální osou z ven. Neviditelná kolize přes celou výplň (povrch_kolize)."""
    for zz, mt, fc in ((z + 0.003, mat + "_ven", (0, 1, 2, 3)), (z - 0.003, mat, (0, 3, 2, 1))):
        P.mesh([(x0, y0, zz), (x1, y0, zz), (x1, y1, zz), (x0, y1, zz)], [fc], mt, m=m)
    P.cols.append((m @ M(((x0 + x1) / 2, (y0 + y1) / 2, z)), (x1 - x0, y1 - y0, 0.04)))

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
        # výplň (Míša 9. 11.: „okna nedodělaná“; rozhodnutí: panské místnosti v patře terčíkové sklo v olovu, jinde napnutá blána;
        # ve hře shaders/okno.gdshader – terčíky a denní světlo, bez průhlednosti)
        if DETAIL: vypln_okna(P, m, x0, x1, ya + 0.02, yb - 0.02, zg, "sklo" if dvoj else "blana")
    OKNA_SVETLA.append(f - nout * (t + 1.2) + UP * ((ya + yb) / 2))
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
                krok_ = 3.6 if dvoj else 4.2; v_hr_ = STR_HR.get(si) is not None and ya < STR_HR[si] + 1.0
                if v_hr_:   # v hradbě: pod korunou bez oken – kromě úzkých okének v nejvyšším patře (kresba misa_04: palác ve zdi jádra má na vnější straně pár malých oken)
                    if not (HRADBA_OKENKA and ui == len(urovne) - 1): continue
                    dvoj = False; w_ = 0.32; yb = min(ya + 0.85, strop - 0.6); krok_ = 3.4
                    if yb - ya < 0.5: continue
                for k in np.arange(2.5, Ls - 1.5, krok_):
                    if any(o[0] == si and abs(o[1] - k) < o[2] / 2 + w_ / 2 + 0.9 for o in otvory) or any(o[0] == si and abs(o[1] - k) < 1.6 and abs(o[3] - ya) < 0.1 for o in OKNA): continue
                    nn_ = -(p1 - p0).normalized().cross(UP).normalized(); hk_ = u_hradby(p0 + (p1 - p0).normalized() * k - nn_ * (t / 2 + 0.5), 2.2)
                    if hk_ is not None and ya < hk_ + 1.0 and not v_hr_: continue   # před oknem hradba – zazděné okno (Míša 4. 11.)
                    wc_ = p0 + (p1 - p0).normalized() * float(k)
                    if any(_dist_seg(wc_, sa_, sb_) < 1.3 and ya < sy1_ + 0.5 and yb > sy0_ - 0.3 for sa_, sb_, sy0_, sy1_ in BEZ_OKEN): continue   # za oknem schody (Míša 5. 11.)
                    OKNA.append((si, float(k), w_, ya, yb, dvoj, ya - 0.12, yb + 0.3))
        POSL_OKNA[:] = OKNA
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
            os_ = sorted((o for o in ot if o[1] - o[2] / 2 - 1e-6 <= sm <= o[1] + o[2] / 2 + 1e-6), key=lambda o: o[3])   # víc otvorů nad sebou (vstup dole, dveře z pavlače v patře – dřív se bral jen první)
            useky_ = []; yc_ = y0
            for o in os_: useky_.append((yc_, o[3])); yc_ = max(yc_, o[4])
            useky_.append((yc_, yk))
            for ya, yb in useky_:
                if yb - ya > 0.05:
                    ov_ = 0.0 if any(abs(s0 - (o[1] + o[2] / 2)) < 1e-6 or abs(s1 - (o[1] - o[2] / 2)) < 1e-6 for o in os_) else 0.04
                    # pruhy zdi mezi okny se o 4 cm překrývají (Míša 10. 11.: „černé a bílé čáry – švy z bloků“: pruhy na sraz s reliéfem
                    # zdiva po kusech nechávaly vlasovou škvíru odshora dolů); u ostění otvoru ne (líc ostění)
                    P.box(M((cc.x, (ya + yb) / 2, cc.z), basis=frame(dd)), (t, yb - ya, s1 - s0 + 2 * ov_), "zdivo")
    if typ == "palac" and not OMITKA:   # kamenný palác (B): nárožní kameny na vnějších rozích (Míša 9. 11.)
        for k_ in range(4):
            r_ = rohy[k_]; e1 = (rohy[k_ - 1] - r_).normalized(); e2 = (rohy[(k_ + 1) % 4] - r_).normalized()
            R_ = r_ - e1 * (t / 2) - e2 * (t / 2)
            narozi(P, R_, (e1, -e2), (e2, -e1), ter(R_.x, R_.z) - 0.2, yk)
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
        # vstup: výchozí uprostřed strany −s; vstup=(strana 0/2, od rohu A, šířka, výška) = skutečný otvor (otvory) na dané straně
        if vstup is None:
            f = A + d * (L * 0.5) - s * (hloubka / 2 + t / 2 + 0.05)
            kit.doorway(P, M(f + UP * podl, basis=Matrix((-d, UP, -s)).transposed()), kind="hlavni", w=1.4, h=2.6, depth=1.1, open_deg=25)
        else:
            sg = 1 if vstup[0] == 0 else -1
            f = A + d * vstup[1] + s * sg * (hloubka / 2 + t / 2 + 0.02)
            kit.doorway(P, M(f + UP * podl, basis=Matrix((d * sg, UP, s * sg)).transposed()), kind="hlavni", w=vstup[2], h=vstup[3], depth=t, top="lomeny", proud_max=0.045)
    # okna paláce (rám, výplň, okenice) na všech stranách – dřív jen uvnitř větve omítky: palác B (kamenný) a strany v hradbě
    # měly holé díry (Míša 9. 11.: „nemáš okna dodělaná“)
    for si, (p0, p1) in enumerate(zip(rohy, rohy[1:] + rohy[:1])):
        dd = (p1 - p0).normalized(); nn = -dd.cross(UP).normalized()
        for o in OKNA:
            if o[0] == si: okno_palace(P, p0 + dd * o[1], dd, -nn, t, *o[2:])
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
                    if DETAIL: vypln_okna(P, M(q, basis=frame(-nn)), -(wq / 2 - 0.04), wq / 2 - 0.04, ytop + ya + 0.04, ytop + yb - 0.04, 0.0, "blana")   # napnutá blána (Míša 9. 11.); osa z ven = −nn
                    OKNA_SVETLA.append(q + nn * 1.4 + UP * yc)   # nn = dovnitř (okenice jsou na −nn venku)
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
        ok_ = dict(OKAP_STRANY)
        for si_ in (0, 2):
            if STR_HR.get(si_) is not None: ok_[si_] = 0.0   # strana v hradbě: střecha končí na koruně, nepřetéká za vnější líc
        strecha_sedlova(P, (a2.x, a2.z), (b2.x, b2.z), hl, ytop, hl * STRECHA_POMER, presah=0.5, stity=STRECHA.get("stity", "drevo"), t_zdi=t, okap_s=ok_)   # kamenný palác B: kamenné štíty (kresba misa_01)
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
    "hlina": ("dirt_floor", 2.0, 0.5),   # násyp nájezdu mostu (Havran: hlína za fošnami opěry)
    "omitka": ("omitka_vapno", 2.5, 1.0), "zdivo_omitka": ("omitka_vapno", 2.5, 0.95),   # vápenná omítka světlá (okna_palace.md)
    "kvadr_okno": ("kamen_teseny", 0.8, 1.0),   # tesané ostění oken – světlejší než zdivo
    "sindel": ("sindel", 1.5, 1.35), "sindel_hra": ("sindel", 1.5, 1.35),
    "rez_drevo": ("letokruhy", 1.0, 0.85),   # čela (textura zešedlá na tón zvětralého dubu – čerstvě oranžová svítila, 3. 11.) trámů a prken: letokruhy (Havran vlastni._tex_endgrain; Míša 3. 11.: „víš jak vypadá řez dřeva?“)
    "provaz": ("rough_wood", 0.3, 0.55), "voda": ("droba", 2.0, 0.12),
    "dub": ("rough_wood", 0.5, 0.75), "hraz": ("rough_wood", 0.5, 0.6), "prkna_ven": ("wood_planks_grey", 1.5, 0.95),
    "okenice": ("wood_planks_grey", 1.5, 0.8), "dvere": ("wood_planks_grey", 1.5, 0.7),
    "prkno": ("rough_wood_sedy", 0.6, 0.95), "prkno_ven": ("prkna_atlas", 2.56, 1.0), "prkno_dvere": ("rough_wood_sedy", 0.6, 0.72),   # jedno prkno (hrad_vzhled.json drevo.deska)
    "skala_mech": ("mossy_rock", 2.0, 1.0), "skala_tm": ("droba", 2.5, 0.6), "skala_sv": ("droba", 3.0, 0.92), "skala": ("droba", 2.5, 0.78), "sut": ("droba", 1.2, 0.7),
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
    elif jm.startswith("blana"):   # napnutá blána (i blana_ven) / plátno v okně (ve hře shaders/okno.gdshader)
        bs.inputs["Base Color"].default_value = (0.8, 0.68, 0.45, 1); bs.inputs["Roughness"].default_value = 0.8
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
        else:   # pevné osy (Míša 9. 11.: „minecraft“ – tečna z normály buňky reliéfu natočená o 1–2° posunula UV o metry → čtverce)
            wx_, wy_ = n.x * n.x, n.y * n.y; c_ = poly.center
            vyber = wx_ / (wx_ + wy_ + 1e-6) + (math.sin(c_.x * 0.71 + c_.y * 1.37 + c_.z * 0.53) * 0.5) * 0.3
            t = Vector((0.0, 1.0 if n.x >= 0 else -1.0, 0.0)) if vyber > 0.5 else Vector((1.0 if n.y < 0 else -1.0, 0.0, 0.0))
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

def zapec_ao(obs, paprsku=10, dosah=2.5):
    """Zapečené stínění (KCD vzhled bez SSAO – tablet Compatibility ho nemá): pro každý vrchol paprsky do polokoule podél
    normály proti celé stavbě (BVH) → zakryté kouty u střech, pod okapy, v rozích zdí tmavší; k tomu tmavší vlhká pata u terénu
    (Havran spina_dole). Zapisuje se do barvy vrcholu G (R = odstín kusu, B = semeno – barva_kusu)."""
    import bmesh, time
    from mathutils.bvhtree import BVHTree
    t0 = time.time(); bm = bmesh.new()
    for ob in obs:
        tmp = bmesh.new(); tmp.from_mesh(ob.data); tmp.transform(ob.matrix_world); me_ = bpy.data.meshes.new("_ao"); tmp.to_mesh(me_); tmp.free()
        bm.from_mesh(me_); bpy.data.meshes.remove(me_)
    tree = BVHTree.FromBMesh(bm); bm.free()
    smery = []
    for i in range(paprsku):   # rovnoměrně po polokouli (Fibonacci), kosinově vážené
        z_ = math.sqrt(1 - (i + 0.5) / paprsku); r_ = math.sqrt(max(0.0, 1 - z_ * z_)); a_ = i * 2.39996
        smery.append(Vector((r_ * math.cos(a_), r_ * math.sin(a_), z_)))
    nv = 0
    for ob in obs:
        me = ob.data; mw = ob.matrix_world; nm = mw.to_3x3().inverted().transposed()
        ao = [1.0] * len(me.vertices)
        sid = {i for i, m_ in enumerate(me.materials) if m_ is not None and m_.name.startswith("sindel")}
        bez_ao = {vi for p_ in me.polygons if p_.material_index in sid for vi in p_.vertices}
        for v in me.vertices:
            p = mw @ v.co; n = (nm @ v.normal).normalized()
            if n.length < 0.5: continue
            t_ = n.orthogonal().normalized(); b_ = n.cross(t_)
            if v.index in bez_ao: ao[v.index] = 1.0; continue   # velké plochy (střechy): vrcholy jen v rozích, AO by ztmavilo celou plochu
            a = 0.0
            for sn in (1.0, -1.0):   # obě strany: tenké desky (střecha, prkna) mívají normálu dovnitř – jinak černé střechy
                hit = 0.0
                for sm in smery:
                    dv = (t_ * sm.x + b_ * sm.y + n * sm.z) * sn
                    loc, _, _, dist = tree.ray_cast(p + n * (0.03 * sn), dv, dosah)
                    if loc is not None: hit += 1.0 - (dist / dosah) * 0.6
                a = max(a, 1.0 - hit / paprsku)
            g = ter(p.x, -p.y)   # Blender: hra z = −y
            pata = min(1.0, max(0.0, (p.z - g) / 1.6))   # do 1,6 m nad terénem vlhko a hlína
            ao[v.index] = max(0.05, a) * (0.62 + 0.38 * pata)
        nv += len(me.vertices)
        barva_kusu(ob, ao)
    print("AO zapečeno: vrcholů %d, %.0f s" % (nv, time.time() - t0), flush=True)

def barva_kusu(ob, ao=None):
    """Havran blender/export_game.py vertex_colors(): atribut rnd (každý kus jiný) -> barva vrcholu: R = odstín kusu
    0,8 + 0,2·rnd, B = semeno kusu (shadery textura/zdivo: jiný výřez fotky, jas po délce – Míša 5. 11.: „vše je jen rastr“)."""
    me = ob.data; rnd = me.attributes.get("rnd")
    rv = [0.5] * len(me.polygons)
    if rnd is not None and rnd.domain == "FACE": rnd.data.foreach_get("value", rv)
    elif ao is None: return
    col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER"); data = [0.0] * (len(me.loops) * 4)
    for poly in me.polygons:
        r = rv[poly.index]
        for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
            data[li * 4:li * 4 + 4] = [0.8 + 0.2 * r, ao[me.loops[li].vertex_index] if ao else 1.0, r, 1.0]
    col.data.foreach_set("color", data); me.color_attributes.active_color = col

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
    if vzhled: zapec_ao([o for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith(("KOLIZE", "Pohyb_"))])
    for ob in [o for o in bpy.data.objects if o.name.startswith("Pohyb_") and o.type == "MESH"]:   # křídla vrat: UV v metrech -> fotka
        if vzhled: vlakna_dreva(ob, vzhled)   # křídla vrat: prkna s vlákny (dřív bez – tablet 3. 11. „vrata průsvitná, žádné dřevo“)
        me = ob.data; uv = me.uv_layers[0].data
        for poly in me.polygons:
            mt = me.materials[poly.material_index] if me.materials else None
            vel = mt.get("vel", 1.0) if mt else 1.0
            for li in poly.loop_indices: uv[li].uv = (uv[li].uv[0] / vel, uv[li].uv[1] / vel)
        for mo in list(ob.modifiers): ob.modifiers.remove(mo)
    out = os.path.join(K, "hra/modely/hrady"); os.makedirs(out, exist_ok=True)
    kw_ = {"export_vertex_color": "ACTIVE"} if vzhled else {}
    try:
        bpy.ops.export_scene.gltf(filepath=os.path.join(out, jmeno + ".glb"), export_format="GLB", export_yup=True,
                                  export_apply=True, export_image_format="JPEG", **kw_)
    except TypeError:   # starší exportér bez export_vertex_color
        bpy.ops.export_scene.gltf(filepath=os.path.join(out, jmeno + ".glb"), export_format="GLB", export_yup=True,
                                  export_apply=True, export_image_format="JPEG", export_colors=bool(vzhled))
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
