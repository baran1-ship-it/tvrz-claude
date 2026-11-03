"""Dvojhradí Puchart podle dochovaných zdrojů a kreseb (pravidla/svet/hrad_puchart.json; zdroje docs/hrady_zdroje.md).

Královský architekt (Míša 30. 10.): tvary a průchody, ne textury. Každá pochozí plocha je v kolizi jako kvádr nebo
rampa (Havran fort.py: covered_walk, wall_stair, bridge – kolize z kvádrů, ne z prken): mosty od nástupu až na práh
brány bez schodu, brány skrz plášť rovnou do nádvoří, ochoz na koruně + pavlač do nádvoří (světlá šířka 2,2 m),
schodiště s podestou na ochoz, ochoz prochází věžičkou / vede k věži. Zdivo dostává kolizi samo (materiály PEVNE),
dřevo jen tam, kde se po něm chodí nebo kde drží (zábradlí).
  /opt/bl/bin/python blender/puchart_hrad.py <koren_puchartu>
Výstup: hra/modely/hrady/puchart.glb (+ uzel KOLIZE, ve hře skrytý) a puchart_daleko.glb.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrady as H
from hrady import Part, M, R, frame, kit, lib, ter, UP, Vector, Matrix
import numpy as np
sys.path.insert(0, os.path.join(H.K, "nastroje"))
import hrad_geom

K = H.K
D = json.load(open(os.path.join(K, "pravidla/svet/hrad_puchart.json")))
A, B = D["A"], D["B"]

# ------------------------------------------------------------------ kolize zdiva automaticky
PEVNE = {"zdivo", "kvadr", "kvadr_sedy", "omitka", "zdivo_hole"}
_box = Part.box
def _box_kol(self, m, size, mat, uvo=None, rnd=None, collide=False):
    _box(self, m, size, mat, uvo=uvo, rnd=rnd, collide=collide or (mat in PEVNE and min(size) >= 0.12 and self.name != "KOLIZE"))
Part.box = _box_kol

STAVBY = []   # záznamy staveb pro test smyslu (hra/data/stavby_kontrola.json): vstupy budov, kozy mostů
SV = []   # světla (pochodně) pro hru: hra/data/svetla.json – věže a sklepy jsou bez nich černé
def svetlo(p, energie=1.4, dosah=6.0): SV.append({"pos": [round(p.x, 2), round(p.y, 2), round(p.z, 2)], "energie": energie, "dosah": dosah})
TR = {}   # trasy pro test průchodu (hra/data/pruchody.json): [[x, z, y_ocekavana | null], ...]
def bod(p, y=None, tol=None):
    b = [round(p.x, 2), round(p.z, 2), None if y is None else round(y, 2)]
    return b + [tol] if tol else b
OCH = 0.725   # střed světlé šířky ochozu od osy zdi dovnitř (zídka 0,55 m na vnější hraně, pavlač 0,9 m)
def pochozi(U, i, s, o=OCH): a, b, L, d, vn = U[i]; return a + d * s + vn * o
def roh(U, i, o=OCH):   # průsečík středů ochozu úseků i a i+1 (v rohu za úsekem i)
    a, b, L, d, vn = U[i]; vn2 = U[(i + 1) % len(U)][4]; return b + (vn + vn2) * (o / (1 + vn.dot(vn2)))

_mov = kit.movable
def _movable_otevrene(name, kind, mg, build, cols=(), use=None, group=None, **meta):
    if kind in ("dvere", "vrata") and meta.get("open"):
        mg = mg @ Matrix.Rotation(math.radians(meta["open"]), 4, "Y")
    return _mov(name, kind, mg, build, cols=cols, use=use, group=group, **meta)
kit.movable = _movable_otevrene

class _Materialy(dict):
    """lib.MAT, který materiál vyrobí při prvním použití (křídla vrat kit.movable se ukládají dřív než díly – byla bílá)."""
    def get(self, k, d=None):
        if k not in self: self[k] = H.material(k)
        return self[k]
lib.MAT = _Materialy(lib.MAT)

def V(p, y=0.0): return Vector((p[0], y, p[1]))
def hz(v): return Vector((v.x, 0, v.z))

def kol(P, c, d, size, sklon=0.0):
    """Kolizní kvádr: střed c, délka podél d (vodorovně), sklon = úhel stoupání podél d (rad)."""
    bas = frame(hz(d)) @ Matrix.Rotation(-sklon, 3, "X")
    P.cols.append((M(c, basis=bas), tuple(size)))

def vnitrek(pts):
    return Vector((sum(p[0] for p in pts) / len(pts), 0, sum(p[1] for p in pts) / len(pts)))

def usek(pts, i):
    a, b = V(pts[i]), V(pts[(i + 1) % len(pts)]); L = (b - a).length; d = (b - a) / L
    vn = d.cross(UP).normalized()
    if (vnitrek(pts) - (a + b) / 2).dot(vn) < 0: vn = -vn
    return a, b, L, d, vn

# ------------------------------------------------------------------ plášť a ochoz
def zed2(P, a, b, t, koruna, vn, otvory=(), cimburi=True, mat="zdivo", krok=3.5, ext0=None, ext1=None, parapet=1.0, par=None):
    """Hradba s vodorovnou korunou (= podlaha ochozu) a pata stupňovitě po terénu. otvory = [(s_stred, šířka, y_podlahy,
    výška)]: pod podlahou zdivo (práh = podlaha průjezdu), nad otvorem překlad až do koruny. Cimbuří na vnější hraně."""
    L = (b - a).length; d = (b - a) / L; vo = -vn
    e0 = t / 2 if ext0 is None else ext0; e1 = t / 2 if ext1 is None else ext1
    hrany = {-e0, L + e1}
    for sc, w, yf, h in otvory: hrany |= {sc - w / 2, sc + w / 2}
    for k in np.arange(-e0, L + e1, krok): hrany.add(float(k))
    hrany = sorted(h for h in hrany if -e0 <= h <= L + e1)
    for s0, s1 in zip(hrany, hrany[1:]):
        if s1 - s0 < 0.01: continue
        sm = (s0 + s1) / 2; c = a + d * sm
        y0 = min(ter(*(a + d * s).xz) for s in np.linspace(s0, s1, 4)) - 1.5
        ot = next((o for o in otvory if o[0] - o[1] / 2 - 1e-6 <= sm <= o[0] + o[1] / 2 + 1e-6), None)
        dily = [(y0, koruna)] if ot is None else [(y0, ot[2]), (ot[2] + ot[3], koruna)]
        for ya, yb in dily:
            if yb - ya > 0.05:
                P.box(M((c.x, (ya + yb) / 2, c.z), basis=frame(d)), (t, yb - ya, s1 - s0 + 0.02), mat)
    if parapet <= 0: return
    # poprsní zídka a stínky cimbuří na vnější hraně (otevřené otvory sahající nad korunu je přeruší)
    pc = vo * (t / 2 - 0.275)
    rez = [(o[0] - o[1] / 2, o[0] + o[1] / 2) for o in otvory if o[2] + o[3] >= koruna - 0.01]
    pa, pb = par if par else (-e0, L + e1)   # zídka nesmí vést skrz věž (test průchodu A_vezicka)
    hr = sorted({pa, pb} | {x for r in rez for x in r if pa < x < pb})
    for s0, s1 in zip(hr, hr[1:]):
        sm = (s0 + s1) / 2
        if any(r0 <= sm <= r1 for r0, r1 in rez) or s1 - s0 < 0.05: continue
        c = a + d * sm + pc
        P.box(M((c.x, koruna + parapet / 2, c.z), basis=frame(d)), (0.55, parapet, s1 - s0), mat)
        if cimburi:
            k = s0 + 0.35
            while k + 1.1 <= s1 - 0.2:
                q = a + d * (k + 0.55) + pc
                P.box(M((q.x, koruna + parapet + 0.4, q.z), basis=frame(d)), (0.55, 0.8, 1.1), mat)
                k += 2.0

def naroze(P, poly, t, koruna, parapet=0.0):   # zídka na pilíři zatarasila ochoz v rohu (test průchodu)
    """Nárožní pilíř v každém vrcholu obvodové hradby: úseky prodloužené o t/2 nechávaly na vnějším rohu klínovou
    mezeru (snímek z tabletu 2. 11.)."""
    for i, p in enumerate(poly):
        c = V(p); a = V(poly[i - 1]); b = V(poly[(i + 1) % len(poly)])
        d = ((c - a).normalized() + (b - c).normalized()); d = d.normalized() if d.length > 1e-6 else (b - c).normalized()
        y0 = min(ter(c.x + dx, c.z + dz) for dx in (-t, 0, t) for dz in (-t, 0, t)) - 1.5
        P.box(M((c.x, (y0 + koruna) / 2, c.z), basis=frame(d)), (t * 1.12, koruna - y0, t * 1.12), "zdivo")
        if parapet > 0:
            P.box(M((c.x, koruna + parapet / 2, c.z), basis=frame(d)), (t * 1.12, parapet, t * 1.12), "zdivo")

def ochoz2(P, a, b, t, koruna, vn, s0=None, s1=None, mezery=(), kryty=False, sirka=0.9, r0=None, r1=None):
    """Pavlač ochozu vyložená do nádvoří na krakorcích (Havran gallery) v úrovni koruny: prkna, kolizní deska, krakorce,
    zábradlí se sloupky po 1,5 m a kolizí. r0/r1 = konce zábradlí (v rozích průsečík se zábradlím sousední zdi – souvislé,
    Míša 30. 10.: zábradlí na ochozech), mezery = sjezdy schodišť a lávky."""
    L = (b - a).length; d = (b - a) / L
    s0 = -t / 2 if s0 is None else s0; s1 = L + t / 2 if s1 is None else s1
    r0 = s0 if r0 is None else r0; r1 = s1 if r1 is None else r1
    if s1 - s0 < 0.3: return
    lic = vn * (t / 2); g = lic + vn * (sirka / 2); hr = lic + vn * (sirka - 0.06)
    p0, p1 = a + d * s0, a + d * s1
    if H.DETAIL:
        kit.deck(P, p0 + g + UP * (koruna - 0.03), p1 + g + UP * (koruna - 0.03), sirka / 2, "prkna_ven", beams=(-sirka / 2 + 0.12, sirka / 2 - 0.12))
    else:
        P.box(M((p0 + p1) / 2 + g + UP * (koruna - 0.04), basis=frame(d)), (sirka, 0.08, s1 - s0), "prkna_ven")
    kol(P, (p0 + p1) / 2 + g - vn * 0.1 + UP * (koruna - 0.1), d, (sirka + 0.2, 0.2, s1 - s0))
    k = s0 + 0.4
    while k < s1 - 0.2:   # krakorce a vzpěry
        q = a + d * k
        P.beam(q + lic - vn * 0.25 + UP * (koruna - 0.18), q + lic + vn * sirka + UP * (koruna - 0.18), 0.18, 0.2, "dub")
        if H.DETAIL: P.beam(q + lic + UP * (koruna - 1.1), q + lic + vn * (sirka - 0.15) + UP * (koruna - 0.28), 0.12, 0.12, "dub", j=0.3)
        k += 1.2
    # zábradlí: úseky mezi mezerami, každý má sloupky na koncích a po 1,5 m (stojí na krakorcích pavlače)
    hrn = sorted({r0, r1} | {min(max(x, r0), r1) for m_ in mezery for x in m_})
    vys = 2.3 if kryty else 1.1
    for u0, u1 in zip(hrn, hrn[1:]):
        if any(m0 - 1e-6 <= (u0 + u1) / 2 <= m1 + 1e-6 for m0, m1 in mezery) or u1 - u0 < 0.15: continue
        q0, q1 = a + d * u0 + hr, a + d * u1 + hr
        P.beam(q0 + UP * (koruna + 1.0), q1 + UP * (koruna + 1.0), 0.1, 0.12, "dub", j=0.3)
        if H.DETAIL: P.beam(q0 + UP * (koruna + 0.5), q1 + UP * (koruna + 0.5), 0.07, 0.09, "dub", j=0.3)
        n = max(1, round((u1 - u0) / 1.5))
        for i in range(n + 1):
            q = q0.lerp(q1, i / n)
            P.beam(q + UP * (koruna - 0.25), q + UP * (koruna + vys), 0.12, 0.12, "dub", j=0.3)
        kol(P, (q0 + q1) / 2 + UP * (koruna + 0.55), d, (0.12, 1.1, u1 - u0))
    if not kryty: return
    P.beam(p0 + hr + UP * (koruna + 2.3), p1 + hr + UP * (koruna + 2.3), 0.16, 0.18, "dub")
    vo = -vn
    lib.shingle_roof(P, p0 + hr + vn * 0.3 + UP * (koruna + 2.25), p1 + hr + vn * 0.3 + UP * (koruna + 2.25),
                     p1 + vo * (t / 2 + 0.1) + UP * (koruna + 2.95), p0 + vo * (t / 2 + 0.1) + UP * (koruna + 2.95), ridge=False)

def zabr_konce(U, i, t, walked, sirka=0.9):
    """Konce zábradlí úseku i: v rohu se sousedním ochozem průsečík linií zábradlí (souvislé zábradlí kolem rohu)."""
    o = t / 2 + sirka - 0.06; a, b, L, d, vn = U[i]; n = len(U)
    r0 = (roh(U, (i - 1) % n, o) - a).dot(d) if (i - 1) % n in walked else None
    r1 = (roh(U, i, o) - a).dot(d) if (i + 1) % n in walked else None
    return r0, r1

def portal(P, stred, nrm, w, h, yf, hloubka, kridla=True):
    """Kamenné ostění brány na líci (nrm = ven z líce) – kit Havrana; křídla vrat otevřená ke zdi."""
    nrm = hz(nrm).normalized(); x = UP.cross(nrm)
    m = M(stred + UP * yf, basis=Matrix((x, UP, nrm)).transposed())
    kit.doorway(P, m, kind="hlavni", w=w, h=h, depth=hloubka, top="lomeny", leaf=kridla, open_deg=82, double=True, open2=-82, inner=False)

def dlazba(P, c, d, w, L, yf):
    P.box(M(c + UP * (yf - 0.04), basis=frame(d)), (w, 0.08, L), "kvadr_sedy")

# ------------------------------------------------------------------ věž s komorou na úrovni ochozu
def vez2(P, c, d, w, dp, dno, ytop, strecha="jehlan", dvere=(), tw=0.9):
    """Hranolová věž: plná do výšky dno (podlaha nejnižší místnosti), nad ní duté zdivo tloušťky tw do ytop s dveřmi
    dvere = [(strana '+s'|'-s'|'+d'|'-d', posun, šířka, y_prahu)] – z ochozu (věžička) nebo z lávky (věž). Stropy, schody
    a zábradlí uvnitř staví vnitrek_veze()."""
    d = hz(d).normalized(); s = d.cross(UP).normalized()
    rohy = [c + d * (w / 2) * i + s * (dp / 2) * j for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    lo = min(ter(p.x, p.z) for p in rohy + [c]) - 2.0
    P.box(M((c.x, (lo + dno) / 2, c.z), basis=frame(d)), (dp, dno - lo, w), "zdivo")
    steny = {"+s": (c + s * (dp / 2 - tw / 2), d, w, s), "-s": (c - s * (dp / 2 - tw / 2), d, w, -s),
             "+d": (c + d * (w / 2 - tw / 2), s, dp - 2 * tw, d), "-d": (c - d * (w / 2 - tw / 2), s, dp - 2 * tw, -d)}
    for jm, (cc, osa, L, nrm) in steny.items():
        otv = [(L / 2 + o, dw, yd, 2.3) for st, o, dw, yd in dvere if st == jm]
        zed2(P, cc - osa * (L / 2), cc + osa * (L / 2), tw, ytop, -nrm, otvory=otv, cimburi=False, ext0=0, ext1=0, parapet=0)
        for st, o, dw, yd in dvere:
            if st == jm and H.DETAIL:
                f = cc + osa * o + nrm * (tw / 2)
                kit.doorway(P, M(f + UP * yd, basis=Matrix((UP.cross(nrm), UP, nrm)).transposed()), kind="obycejne", w=dw, h=2.3,
                            depth=tw, top="segment", leaf=False)
        for y in np.arange(dno + 1.6, ytop - 1.0, 3.5):   # střílny (zvenku tmavé) – ne ve dveřích (tablet 2. 11.: černý pruh v otvoru)
            if any(st == jm and abs(o) < dw / 2 + 0.4 and yd - 0.6 < y < yd + 2.9 for st, o, dw, yd in dvere): continue
            f = cc + nrm * (tw / 2 + 0.01)
            P.box(M(f + UP * y, basis=frame(osa)), (0.12, 1.1, 0.16), "tma")
    if strecha == "jehlan":
        H.strecha_jehlan(P, [(p.x, p.z) for p in rohy], ytop, max(w, dp) * 1.1, presah=0.35)
    elif strecha == "valba":
        a = c - d * (w / 2); b = c + d * (w / 2)
        H.strecha_valba(P, (a.x, a.z), (b.x, b.z), dp, ytop, dp * 0.75, presah=0.4)
    return rohy

def zabradli(P, p0, p1, y):
    """Dřevěné zábradlí se sloupky a kolizí (otvory v podlahách)."""
    d = hz(p1 - p0); L = d.length
    if L < 0.1: return
    P.beam(p0 + UP * (y + 1.0), p1 + UP * (y + 1.0), 0.09, 0.1, "dub", j=0.3)
    P.beam(p0 + UP * (y + 0.5), p1 + UP * (y + 0.5), 0.06, 0.08, "dub", j=0.3)
    n = max(1, round(L / 1.2))
    for i in range(n + 1):
        q = p0.lerp(p1, i / n); P.beam(q + UP * (y - 0.02), q + UP * (y + 1.06), 0.1, 0.1, "dub", j=0.4)
    kol(P, (p0 + p1) / 2 + UP * (y + 0.55), d, (0.1, 1.1, L))

def podlaha(P, c, d, iw, idp, y, otvory=(), tl=0.24):
    """Trámový strop/podlaha ve věži (lokálně u podél d, v podél s, střed c) s otvory [(u0, u1, v0, v1)] pro schody."""
    d = hz(d).normalized(); s = d.cross(UP).normalized()
    us = sorted({-iw / 2, iw / 2} | {x for o in otvory for x in o[:2]}); vs = sorted({-idp / 2, idp / 2} | {x for o in otvory for x in o[2:]})
    for u0, u1 in zip(us, us[1:]):
        for v0, v1 in zip(vs, vs[1:]):
            um, vm = (u0 + u1) / 2, (v0 + v1) / 2
            if u1 - u0 < 0.02 or v1 - v0 < 0.02 or any(o[0] <= um <= o[1] and o[2] <= vm <= o[3] for o in otvory): continue
            q = c + d * um + s * vm
            P.box(M(q + UP * (y - 0.04), basis=frame(d)), (v1 - v0, 0.08, u1 - u0), "prkna_ven")
            P.box(M(q + UP * (y - 0.08 - (tl - 0.08) / 2), basis=frame(d)), (v1 - v0, tl - 0.08, u1 - u0), "dub")
            kol(P, q + UP * (y - tl / 2), d, (v1 - v0, tl, u1 - u0))

def vnitrek_veze(P, c, d, iw, idp, patra, steny_ramen, sq=1.0, run=None, sirka=1.0):
    """Patra a schodiště věže: rameno k vede z patra k do k+1 podél stěny steny_ramen[k] (0 S, 1 V, 2 J, 3 Z v lokálních
    osách). Začíná sq od rohu a končí sq před dalším rohem – čtverec v rohu je pevná podesta, ze které vychází další
    rameno (podél další stěny). Nad ramenem otvor v podlaze, zábradlí podél otvoru a přes jeho dolní konec, výstup
    nahoře volný. Vrací ramena [(start, konec, směr, y0, y1)] pro test průchodu."""
    d = hz(d).normalized(); s = d.cross(UP).normalized()
    L = lambda u, v: c + d * u + s * v
    steny = [((-iw / 2, -idp / 2), (1, 0), (0, 1)), ((iw / 2, -idp / 2), (0, 1), (-1, 0)),
             ((iw / 2, idp / 2), (-1, 0), (0, -1)), ((-iw / 2, idp / 2), (0, -1), (1, 0))]
    ramena = []; otv = {k: [] for k in range(len(patra))}; zabr = []
    for k in range(len(patra) - 1):
        (cu, cv), (du, dv), (lu, lv) = steny[steny_ramen[k]]
        delka = iw if du else idp
        y0, y1 = patra[k], patra[k + 1]
        n = round((y1 - y0) / 0.215); rn = run or (delka - 2 * sq); r = rn / n
        su, sv = cu + du * sq + lu * sirka / 2, cv + dv * sq + lv * sirka / 2
        a = L(su, sv); dirw = d * du + s * dv
        e, _ = schody2(P, a, dirw, y0, y1, sirka - 0.05, zabradli=(), podklad=y0, r=r, vyska_st=(y1 - y0) / n)
        ramena.append((a, e, dirw, y0, y1))
        pts = [(cu + du * (sq - 0.05) + lu * x, cv + dv * (sq - 0.05) + lv * x) for x in (0, sirka + 0.05)] + \
              [(cu + du * (sq + rn) + lu * x, cv + dv * (sq + rn) + lv * x) for x in (0, sirka + 0.05)]
        otv[k + 1].append((min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)))
        e0 = L(cu + du * sq + lu * (sirka + 0.05), cv + dv * sq + lv * (sirka + 0.05))
        e1 = L(cu + du * (sq + rn - (1.1 if run else 0)) + lu * (sirka + 0.05), cv + dv * (sq + rn - (1.1 if run else 0)) + lv * (sirka + 0.05))
        zabr += [(e0, e1, y1), (L(cu + du * sq, cv + dv * sq), e0, y1)]
    for k, y in enumerate(patra):
        if k > 0: podlaha(P, c, d, iw, idp, y, otv[k])
    for p0, p1, y in zabr: zabradli(P, p0, p1, y)
    return ramena

# ------------------------------------------------------------------ most, schody, plošiny
def most2(P, a, ya, b, yb, w, Lp):
    """Dřevěný most na kozách od nástupu a (terén srovnaný na ya) na práh brány b (yb): mostovka souvislá, kolize jedna
    šikmá deska zapuštěná na začátku do terénu (žádný schod), u brány padací most na řetězech."""
    d = hz(b - a); L = d.length; d /= L; s = d.cross(UP).normalized()
    sk = math.atan2(yb - ya, L); tg = (yb - ya) / L
    y = lambda t: ya + tg * t
    t0 = -1.0
    c = a + d * ((t0 + L) / 2) + UP * (y((t0 + L) / 2) - 0.15 / math.cos(sk))
    kol(P, c, d, (w, 0.3, (L - t0) / math.cos(sk)), sk)
    Lf = L - Lp
    nd = max(1, int(Lf / 0.3))
    for i in range(nd):   # příčná prkna
        tm = Lf * (i + 0.5) / nd
        q = a + d * tm + UP * (y(tm) - 0.035)
        P.box(M(q, basis=frame(d) @ Matrix.Rotation(-sk, 3, "X")), (w, 0.07, Lf / nd - 0.015), "prkna_ven")
    for o in (-w / 2 + 0.25, 0.0, w / 2 - 0.25):   # podélné trámy
        P.beam(a + s * o + UP * (ya - 0.22), a + d * Lf + s * o + UP * (y(Lf) - 0.22), 0.26, 0.3, "dub")
    # kozy (Míša 2. 11.: most „není po zem“ – pod 0,7 m výšky koza neměla sloupy a příčný trám visel): každá koza = dva
    # sloupy na kamenných patkách až k terénu, příčný trám pod podélnými trámy, od 1,2 m křížové ztužení napříč a
    # vzpěry podél; na obou koncích kamenná opěra (mostovka nikde nekončí ve vzduchu). Rozteč z hrad_puchart.json most.
    MO = A["most"]; rozt = MO.get("rozestup_koz_m", 3.5)
    n = max(2, int(round(Lf / rozt)))
    for i in range(1, n):
        tm = Lf * i / n; p = a + d * tm; yy = y(tm)
        if yy - max(ter(*(p + s * o).xz) for o in (-w / 2, 0, w / 2)) < MO.get("koza_od_m", 0.9): continue   # mostovka u země / v zářezu: bez kozy (patky trčely nad mostovkou – tablet 3. 11.)
        P.beam(p - s * (w / 2 + 0.2) + UP * (yy - 0.51), p + s * (w / 2 + 0.2) + UP * (yy - 0.51), 0.28, 0.24, "dub")   # příčný trám pod podélnými
        STAVBY.append({"koza": [round(p.x, 2), round(p.z, 2)], "mostovka_y": round(yy, 2), "patka_vrch_y": round(max(ter(*(p + s * o).xz) for o in (-w / 2 + 0.15, w / 2 - 0.15)) + 0.3, 2)})
        gs = []
        for o in (-w / 2 + 0.15, w / 2 - 0.15):
            q = p + s * o; g = ter(q.x, q.z); gs.append(g)
            P.box(M(q + UP * (g + 0.05), basis=frame(d)), (0.6, 0.5, 0.6), "kvadr_sedy")      # patka (do terénu 0,2 m)
            P.beam(q + UP * (g + 0.28), q + UP * (yy - 0.62), 0.28, 0.28, "dub", j=0.4)
            if yy - g > 2.0:   # vzpěry podél mostu
                P.beam(q + UP * (g + 0.6) - d * 1.0, q + UP * (yy - 0.9), 0.16, 0.16, "dub", j=0.4)
                P.beam(q + UP * (g + 0.6) + d * 1.0, q + UP * (yy - 0.9), 0.16, 0.16, "dub", j=0.4)
        g = max(gs)
        if yy - g > 1.2:   # křížové ztužení napříč
            P.beam(p - s * (w / 2 - 0.15) + UP * (g + 0.5), p + s * (w / 2 - 0.15) + UP * (yy - 0.75), 0.14, 0.14, "dub")
            P.beam(p + s * (w / 2 - 0.15) + UP * (g + 0.5), p - s * (w / 2 - 0.15) + UP * (yy - 0.75), 0.14, 0.14, "dub")
    # opěry na koncích pevné části: kamenný blok od terénu pod podélné trámy
    for tm in (0.0, Lf):
        p = a + d * tm; yy = y(tm); g = min(ter(*(p + s * o).xz) for o in (-w / 2, 0, w / 2)) - 0.3
        if yy - 0.37 - g > 0.1 and yy - max(ter(*(p + s * o).xz) for o in (-w / 2, 0, w / 2)) > -0.05:   # opěra jen pod mostovkou, ne nad ní
            P.box(M(p + UP * ((g + yy - 0.37) / 2), basis=frame(d)), (w + 0.6, yy - 0.37 - g, 1.0), "kvadr")
    for sg in (-1, 1):   # zábradlí s kolizí (celé, i podél padacího mostu – padací most je spuštěný)
        o = s * sg * (w / 2 + 0.06)
        P.beam(a + o + UP * (ya + 1.05), a + d * Lf + o + UP * (y(Lf) + 1.05), 0.12, 0.12, "dub", j=0.5)
        P.beam(a + o + UP * (ya + 0.55), a + d * Lf + o + UP * (y(Lf) + 0.55), 0.08, 0.1, "dub", j=0.5)
        k = max(2, int(Lf / 1.75))
        for i in range(k + 1):
            tm = Lf * i / k; q = a + d * tm + o
            P.beam(q + UP * (y(tm) - 0.05), q + UP * (y(tm) + 1.12), 0.13, 0.13, "dub", j=0.6)
        kol(P, a + d * (L / 2) + o + UP * (y(L / 2) + 0.6), d, (0.14, 1.2, L / math.cos(sk)), sk)
    # padací most: osa otáčení na prahu, vede od brány
    bb = a + d * L
    if H.DETAIL:
        mb = M(bb + UP * yb, basis=Matrix((s, UP, -d)).transposed())
        oka = kit.drawbridge(P, mb, w=w - 0.2, L=Lp, angle=math.degrees(sk))   # konec dolů k pevné části (rotace kolem X kladná = dolů)
        for q in oka:
            kit.chain(P, q, bb + UP * (yb + 4.0) + (q - (bb + UP * yb)).project(s) + d * 0.1, sag=0.15)
    else:
        P.box(M(bb - d * (Lp / 2) + UP * (yb - Lp / 2 * tg), basis=frame(d) @ Matrix.Rotation(-sk, 3, "X")), (w, 0.2, Lp), "prkna_ven")

def nabeh(P, prah, ven, y, w, L=1.8, spad=0.7):
    """Kolizní nájezd z terénu na práh brány: šikmá deska od prahu ven, zapuštěná do terénu."""
    ven = hz(ven).normalized(); sk = math.atan2(spad, L)
    kol(P, prah + ven * (L / 2) + UP * (y - spad / 2 - 0.1), -ven, (w, 0.2, L / math.cos(sk) + 0.1), sk)

def plosina(P, c, d, delka, sirka, y, sloupy=True):
    d = hz(d).normalized(); s = d.cross(UP).normalized()
    P.box(M(c + UP * (y - 0.04), basis=frame(d)), (sirka, 0.08, delka), "prkna_ven")
    kol(P, c + UP * (y - 0.1), d, (sirka, 0.2, delka))
    for o in (-delka / 2 + 0.1, delka / 2 - 0.1):
        P.beam(c + d * o - s * sirka / 2 + UP * (y - 0.18), c + d * o + s * sirka / 2 + UP * (y - 0.18), 0.18, 0.2, "dub")
    if sloupy:
        for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q = c + d * (i * (delka / 2 - 0.12)) + s * (j * (sirka / 2 - 0.12))
            P.beam(q + UP * (ter(q.x, q.z) - 0.2), q + UP * (y - 0.25), 0.2, 0.2, "dub", j=0.5)

def schody2(P, a, d, y0, y1, w=1.2, kamenne=False, zabradli=(1, -1), podklad=None, r=None, vyska_st=0.19):
    """Schodiště od a ve směru d z y0 na y1 (stupeň 19 cm × 27 cm, ~35°). Kolize = šikmá rampa přes hrany stupňů
    zapuštěná do terénu + plná výplň pod nízkou částí (Havran stairs). Vrací konec (bod, y)."""
    d = hz(d).normalized(); s = d.cross(UP).normalized()
    zem = (lambda x, z: podklad) if podklad is not None else ter   # ve věži stojí schody na podlaze, ne na terénu
    n = max(2, round((y1 - y0) / vyska_st)); h = (y1 - y0) / n; r = r or (0.27 if not kamenne else 0.3); run = n * r
    sk = math.atan2(y1 - y0, run)
    for k in range(n):
        q = a + d * (r * (k + 0.5))
        if kamenne:
            yb = y0 + h * (k + 1)
            P.box(M(q + UP * (yb - (yb - y0 + 0.3) / 2), basis=frame(d)), (w, yb - y0 + 0.3, r + 0.02), "kvadr_schod")
        else:
            P.box(M(q + UP * (y0 + h * (k + 1) - 0.03), basis=frame(d)), (w, 0.06, r + 0.03), "prkna_ven")
    if not kamenne:
        for o in (-w / 2 + 0.05, w / 2 - 0.05):
            P.beam(a + s * o + UP * (y0 - 0.15), a + d * run + s * o + UP * (y1 - 0.15), 0.08, 0.26, "dub", j=0.4)
        for t in (0.45, 0.85):
            for o in (-w / 2 + 0.1, w / 2 - 0.1):
                q = a + d * (run * t) + s * o
                if y0 + (y1 - y0) * t - zem(q.x, q.z) > 1.0:
                    P.beam(q + UP * (zem(q.x, q.z) - 0.05), q + UP * (y0 + (y1 - y0) * t - 0.3), 0.16, 0.16, "dub", j=0.4)
    tm = -0.6; tk = run
    c = a + d * ((tm + tk) / 2) + UP * (y0 + h * 0.25 + math.tan(sk) * (tm + tk) / 2 - 0.08 / math.cos(sk))   # horní konec rampy ~ v úrovni podlahy (lem 0,1 m: uvíznutí ve věži)
    kol(P, c, d, (w, 0.16, (tk - tm) / math.cos(sk)), sk)
    for i in range(1, 10):   # výplň pod schody do výšky 2 m (nikdo pod ně nevleze)
        t0, t1 = run * i / 10, run * (i + 1) / 10; hh = (y1 - y0) * i / 10 - 0.15
        if hh > 2.0: break
        g = zem(*(a + d * ((t0 + t1) / 2)).xz)
        top = y0 + hh
        if top - g > 0.2:
            kol(P, a + d * ((t0 + t1) / 2) + UP * ((top + g - 0.3) / 2), d, (w - 0.1, top - g + 0.3, t1 - t0))
    for sg in zabradli:
        o = s * sg * (w / 2 + 0.05)
        P.beam(a + o + UP * (y0 + 1.0), a + d * run + o + UP * (y1 + 1.0), 0.09, 0.1, "dub", j=0.4)
        for i in range(max(2, int(run / 1.3)) + 1):
            tt = i / max(2, int(run / 1.3)); q = a + d * (run * tt) + o
            P.beam(q + UP * (y0 + (y1 - y0) * tt - 0.05), q + UP * (y0 + (y1 - y0) * tt + 1.06), 0.1, 0.1, "dub", j=0.5)
        kol(P, a + d * (run / 2) + o + UP * ((y0 + y1) / 2 + 0.55), d, (0.12, 1.1, max(0.5, run / math.cos(sk) - 1.5)), sk)   # konce kratší: šikmý kvádr přesahoval patu schodů (palác)
    return a + d * run, y1


def budova_k(P, a, b, hloubka, hk, hd, typ, podl=None, otvory=(), vstup=None, plna_kolize=True, k_bodu=None, vnitrek=None, patro_y=None):
    """Budova stavebnice. k_bodu (nádvoří) = budova je průchozí (3. 11., Míša: vstupy do ostatních budov chybí): dveře
    uprostřed strany k nádvoří (nebo vstup z dat), podlaha uvnitř, kolize stěn s mezerou dveří, náběh z terénu, světlo
    a vybavení podle vnitrek; jinak plná kolize půdorysu (starší chování). podl zadaná = pod budovou je sklep."""
    if k_bodu is not None:
        A_, B_ = V(a), V(b); d = (B_ - A_).normalized(); s = d.cross(UP).normalized(); L = (B_ - A_).length
        sg = 1 if (V(k_bodu) - (A_ + B_) / 2).dot(s) > 0 else -1
        strana = 0 if sg > 0 else 2
        vs = vstup or (strana, L / 2, 1.2, 2.3)
        podl = H.budova(P, a, b, hloubka, hk, hd, "sedlova", typ, podl=podl, otvory=otvory, vstup=vs)
        t = 1.1 if typ == "palac" else 0.5; hi_ = (hk + hd) if typ == "palac" else 0.6 + (hd if hd > 0 else hk)
        c = (A_ + B_) / 2; wi = hloubka - (t if typ == "palac" else 0.4); li = L - (t if typ == "palac" else 0.4)
        P.box(M(c + UP * (podl - 0.06), basis=frame(d)), (wi, 0.12, li), "kvadr_sedy" if typ == "palac" else "prkna_ven")   # podlaha
        kol(P, c + UP * (podl - 0.15), d, (hloubka, 0.3, L))
        if typ != "palac":   # dřevěné stěny nemají kolizi zdiva: 4 stěny, mezera dveří
            for si_, (p0, p1) in enumerate(((A_ + s * hloubka / 2, B_ + s * hloubka / 2), (B_ + s * hloubka / 2, B_ - s * hloubka / 2),
                                            (B_ - s * hloubka / 2, A_ - s * hloubka / 2), (A_ - s * hloubka / 2, A_ + s * hloubka / 2))):
                dd = p1 - p0; Lw = dd.length; dd = dd / Lw
                kusy = [(0.0, Lw)]
                if si_ == vs[0]:
                    od = vs[1] if si_ == 0 else Lw - vs[1]; kusy = [(0.0, od - vs[2] / 2), (od + vs[2] / 2, Lw)]
                for u0, u1 in kusy:
                    if u1 - u0 > 0.05: kol(P, p0 + dd * ((u0 + u1) / 2) + UP * (podl + hi_ / 2), dd, (0.3, hi_, u1 - u0))
        dvere = A_ + d * vs[1] + s * sg * (hloubka / 2)
        nn = s * sg; tz = t / 2   # náběh končí v úrovni podlahy na vnějším líci (hrana prahu zastavila postavu – test 3. 11.)
        g = min(ter(*(dvere + nn * (tz + k)).xz) for k in (0.3, 0.8, 1.5, 2.5))
        if podl - g > 0.02:
            Ln = max(1.5, (podl - g) / 0.17); sk_ = math.atan2(podl - g, Ln)
            top = dvere + nn * (tz - 0.05); foot = top + nn * Ln   # v podlaze ve vnějším líci zdi (dál je zeď pod prahem v úrovni podlahy)
            mid = (top + foot) / 2 + UP * ((podl + g) / 2 - 0.12)
            bas = frame(hz(-nn)) @ Matrix.Rotation(-sk_, 3, "X")
            P.box(M(mid, basis=bas), (vs[2] + 0.4, 0.24, Ln / math.cos(sk_) + 0.1), "kvadr_sedy")
            kol(P, mid, -nn, (vs[2] + 0.4, 0.24, Ln / math.cos(sk_) + 0.1), sk_)
        svetlo(c + UP * (podl + 2.0), 1.0, 6.0)
        jm_b = "budova_%s_%d_%d" % (typ, round(c.x), round(c.z))
        TR[jm_b] = [bod(dvere + nn * (tz + 4.5)), bod(dvere + nn * (tz + 0.6)), bod(dvere - nn * 0.6, podl), bod(c, podl)]
        if typ == "palac" and patro_y:   # palác: schody do patra podél stěny naproti dveřím, otvor se zábradlím
            ram = vnitrek_veze(P, c, d, li, wi, [podl, podl + patro_y], [0 if sg > 0 else 2], sq=0.9, sirka=1.0)
            podlaha(P, c, d, li, wi, podl + hk - 0.1)   # strop pod dřevěným patrem
            svetlo(c + UP * (podl + patro_y + 2.0), 1.0, 6.0)
            sa, se, sdir, y0_, y1_ = ram[0]
            w_ = (c - sa) - sdir * (c - sa).dot(sdir); w_.y = 0; w_ = w_.normalized()   # k patě schodů z volné strany, ne napříč bokem schodiště (test 3. 11.)
            TR[jm_b] += [bod(sa - sdir * 0.45 + w_ * 1.3, podl), bod(sa - sdir * 0.45, podl), bod(sa + sdir * 0.8), bod(se + sdir * 0.5, y1_), bod(c, y1_)]
        for k, (uu, vv) in enumerate(vnitrek or []):   # sudy / bedny podél stěn
            sud(P, c + d * (uu * li / 2) + s * (-sg) * (vv * wi / 2), podl)
        STAVBY.append({"budova": "%s_%s" % (typ, round(c.x, 1)), "vstup": True, "podl": round(podl, 2)})
        return podl
    sk = podl is not None
    podl = H.budova(P, a, b, hloubka, hk, hd, "sedlova", typ, podl=podl, otvory=otvory, vstup=vstup)
    if not plna_kolize: return podl   # obytná budova: kolize mají zdi (zdivo) a podlahy (palac_A)
    A_, B_ = V(a), V(b); d = B_ - A_; hh = (hk + hd) if typ == "palac" else 0.6 + (hd if hd > 0 else hk)   # jen stěny, střecha bez kolize
    dole = 0.05 if sk else 1.0
    kol(P, (A_ + B_) / 2 + UP * (podl - dole + (hh + dole) / 2), d, (hloubka + 0.2, hh + dole, d.length + 0.2))
    return podl

def klenba(P, o, du, dv, u0, u1, v0, v1, osa, y_patka, vzepeti, tl=0.35, mat="kvadr", diry=(), n=10, kus=0.7):
    """Valená (segmentová) klenba z klenáků nad obdélníkem u0..u1 × v0..v1 (lokálně od o po du, dv); osa 'u' nebo 'v' =
    směr osy klenby, rozpětí je v druhém směru. diry = [(u0, u1, v0, v1)] – otvor v klenbě (hladomorna)."""
    du3, dv3 = hz(du).normalized(), hz(dv).normalized()
    if osa == "u": a_ax, a_sp, l0, l1, s0, s1 = du3, dv3, u0, u1, v0, v1
    else: a_ax, a_sp, l0, l1, s0, s1 = dv3, du3, v0, v1, u0, u1
    pol = (s1 - s0) / 2; R = (pol * pol + vzepeti * vzepeti) / (2 * vzepeti); fi0 = math.asin(min(1.0, pol / R))
    yc = y_patka + vzepeti - R; sm = (s0 + s1) / 2
    nk = max(1, round((l1 - l0) / kus))
    for i in range(n):
        f0, f1 = -fi0 + 2 * fi0 * i / n, -fi0 + 2 * fi0 * (i + 1) / n
        q0 = (sm + R * math.sin(f0), yc + R * math.cos(f0)); q1 = (sm + R * math.sin(f1), yc + R * math.cos(f1))
        fm = (f0 + f1) / 2; rad = Vector((0, 0, 0)) + a_sp * math.sin(fm) + UP * math.cos(fm)
        tet = math.hypot(q1[0] - q0[0], q1[1] - q0[1])
        for k in range(nk):
            lm0, lm1 = l0 + (l1 - l0) * k / nk, l0 + (l1 - l0) * (k + 1) / nk
            sp = (q0[0] + q1[0]) / 2
            uu, vv = ((lm0 + lm1) / 2, sp) if osa == "u" else (sp, (lm0 + lm1) / 2)
            if any(d0[0] <= uu <= d0[1] and d0[2] <= vv <= d0[3] for d0 in diry): continue
            c = o + a_ax * ((lm0 + lm1) / 2) + a_sp * (sp - 0) + UP * ((q0[1] + q1[1]) / 2) + rad * (tl / 2)
            c = c - a_sp * 0   # (o je počátek lokálních souřadnic)
            P.box(M(c, basis=frame(a_ax, up=rad)), (tet + 0.03, tl, lm1 - lm0 + 0.02), mat)

def kruh_retez(P, p, nrm, y, delka=0.9):
    """Železný kruh ve zdi s řetězem (kobky, hladomorna)."""
    nrm = hz(nrm).normalized(); x = UP.cross(nrm); c = p + nrm * 0.06 + UP * y
    pts = [c + x * (0.07 * math.cos(t)) + UP * (0.07 * math.sin(t)) for t in [i / 10 * 2 * math.pi for i in range(11)]]
    for q0, q1 in zip(pts, pts[1:]): P.rod(q0, q1, 0.013, 5, "zelezo")
    if H.DETAIL: kit.chain(P, c - UP * 0.07, c - UP * 0.07 - UP * delka + nrm * 0.15, sag=0.05)

def sud(P, p, y):
    P.lathe(M(p + UP * y), [(0.3, 0), (0.37, 0.25), (0.39, 0.45), (0.37, 0.65), (0.3, 0.9)], 12, "dub")
    kol(P, p + UP * (y + 0.45), Vector((1, 0, 0)), (0.7, 0.9, 0.7))

# ------------------------------------------------------------------ sklep pod palácem s kobkami
def sklep_A(P, g):
    S = g["S"]; y = g["y"]; Li, Wi, tl = g["Li"], g["Wi"], g["tl"]
    o = Vector((g["o"][0], 0, g["o"][1])); du = Vector((g["du"][0], 0, g["du"][1])); dv = Vector((g["dv"][0], 0, g["dv"][1]))
    W = lambda u, v, yy=0.0: o + du * u + dv * v + UP * yy
    strop = g["podl"] - 0.25                      # pod podlahou paláce
    # podlaha z kamenných desek
    P.box(M(W(Li / 2, Wi / 2, y - 0.15), basis=frame(du)), (Wi + 0.4, 0.3, Li + 0.4), "kvadr_sedy")
    # příčka mezi sálem a kobkami s dveřmi, zdi mezi kobkami
    pr = S["pricka"]; vp = (pr["v0"] + pr["v1"]) / 2; tp = pr["v1"] - pr["v0"]; dk = S["dvere_kobky"]; zs = S["zasobarna"]
    otv = [((k["u0"] + k["u1"]) / 2, dk["sirka"], y, dk["vyska"]) for k in S["kobky"]] + [((zs["u0"] + Li) / 2, zs["otvor"], y, 2.0)]
    zed2(P, W(0, vp), W(Li, vp), tp, strop, dv, otvory=otv, cimburi=False, parapet=0, ext0=0, ext1=0)
    hrany = [k["u1"] for k in S["kobky"]]
    for k, u1 in enumerate(hrany):
        u2 = S["kobky"][k + 1]["u0"] if k + 1 < len(S["kobky"]) else zs["u0"]
        um = (u1 + u2) / 2; zed2(P, W(um, 0), W(um, pr["v0"]), u2 - u1, strop, du, cimburi=False, parapet=0, ext0=0, ext1=0)
    # okapový chodník u V čela paláce v úrovni nádvoří (kryje hranu výkopu)
    oc = S["okapovy_chodnik"]; P.box(M(W(-tl - oc["sirka"] / 2, Wi / 2, A["nadvori_y"] - 0.12), basis=frame(du)),
                                     (Wi + 2 * tl + 0.4, 0.4, oc["sirka"]), "kvadr_sedy")
    # vyzdívka V čela a S stěny (schová hranu terénní jámy), dveře ze šíje i skrz ni
    ob = S["obklad"]; sj = S["sije"]
    zed2(P, W(ob["u_tl"] / 2, 0), W(ob["u_tl"] / 2, Wi), ob["u_tl"], strop, du, cimburi=False, parapet=0, ext0=0, ext1=0)
    zed2(P, W(0, Wi - ob["v_tl"] / 2), W(Li, Wi - ob["v_tl"] / 2), ob["v_tl"], strop, -dv, cimburi=False, parapet=0, ext0=0, ext1=0,
         otvory=[(sj["u_dvere"], sj["dvere"][0], y, sj["dvere"][1])])
    Wv = Wi - ob["v_tl"]
    # klenby: sál (osa podél paláce), kobky a zásobárna (osa napříč)
    sa = S["sal"]; klenba(P, o, du, dv, ob["u_tl"], Li, sa["v0"], Wv, "u", y + sa["patka_nad_podlahou"], sa["vzepeti"])
    kk = S["kobka_klenba"]
    for k in S["kobky"]:
        klenba(P, o, du, dv, k["u0"], k["u1"], 0, pr["v0"], "v", y + kk["patka_nad_podlahou"], kk["vzepeti"], tl=0.3)
        kruh_retez(P, W((k["u0"] + k["u1"]) / 2, 0), dv, y + 1.2)      # kruh v zadní (hradební) stěně
        if H.DETAIL:   # okované dveře kobky (otevřené)
            kit.doorway(P, M(W((k["u0"] + k["u1"]) / 2, pr["v1"], y), basis=Matrix((UP.cross(dv), UP, dv)).transposed()), kind="obycejne",
                        w=dk["sirka"], h=dk["vyska"], depth=tp, top="segment", leaf=True, lattice=True)
    klenba(P, o, du, dv, zs["u0"], Li, 0, pr["v0"], "v", y + kk["patka_nad_podlahou"] + 0.2, kk["vzepeti"] + 0.2, tl=0.3)
    for i, (uu, vv) in enumerate(((zs["u0"] + 0.6, 0.6), (zs["u0"] + 1.4, 0.6), (Li - 0.6, 0.6), (Li - 0.6, 1.5))):
        sud(P, W(uu, vv), y)
    sud(P, W(Li - 0.7, Wv - 0.6), y); sud(P, W(Li - 1.5, Wv - 0.6), y)
    # sklepní šíje: kamenné schody ze dvora podél S zdi paláce, opěrná zeď s poprsní, stříška, dveře do sálu
    sj = S["sije"]; v0 = Wi + tl; ytop = A["nadvori_y"]; vm = v0 + sj["sirka"] / 2
    n_st = round((ytop - y) / 0.19); run = n_st * 0.30; u_dole = sj["u_horni"] + run
    schody2(P, W(u_dole, vm), -du, y, ytop, w=sj["sirka"] - 0.05, kamenne=True, zabradli=())
    P.box(M(W((u_dole + sj["u_dvere"] + 1.3) / 2, vm, y - 0.15), basis=frame(du)), (sj["sirka"] + 0.2, 0.3, sj["u_dvere"] + 1.3 - u_dole + 0.3), "kvadr_sedy")
    vz_ = v0 + sj["sirka"] + sj["zed"] / 2; kz = ytop + 0.9
    zed2(P, W(sj["u_horni"] - 0.6, vz_), W(sj["u_dvere"] + 1.3 + sj["zed"], vz_), sj["zed"], kz, -dv, cimburi=False, parapet=0, ext0=0, ext1=0)
    zed2(P, W(sj["u_dvere"] + 1.3 + sj["zed"] / 2, v0), W(sj["u_dvere"] + 1.3 + sj["zed"] / 2, v0 + sj["sirka"] + sj["zed"]), sj["zed"], kz, du,
         cimburi=False, parapet=0, ext0=0, ext1=0)
    if H.DETAIL:
        kit.doorway(P, M(W(sj["u_dvere"], v0, y), basis=Matrix((UP.cross(dv), UP, dv)).transposed()), kind="obycejne", w=sj["dvere"][0],
                    h=sj["dvere"][1], depth=tl, top="segment", leaf=True)
    e0, e1 = sj["u_horni"] - 0.6, sj["u_dvere"] + 1.3 + sj["zed"]
    # kamenná dlažba kolem šíje v úrovni nádvoří: terénní mřížka 1 m dělala vedle opěrné zdi a před schody příkop
    # (tablet 2. 11.: „kolem vstupu do sklepa všude díry“); pruh 1,3 m podél zdi, kolem čela a podesta před prvním stupněm
    # (pruh končí u čelní zdi šíje – dál je nájezd ke dveřím paláce, test A_palac)
    dl = sj["dlazba_m"]; vo = v0 + sj["sirka"] + sj["zed"]
    def deska(u0, u1, v0_, v1_):   # dlažba jako blok až pod nejnižší terén (na vyklenutém nádvoří visela / zapadala – tablet 3. 11.)
        g = min(ter(*W(uu, vv).xz) for uu in np.linspace(u0, u1, 5) for vv in np.linspace(v0_, v1_, 3)) - 0.15
        P.box(M(W((u0 + u1) / 2, (v0_ + v1_) / 2, (ytop + 0.03 + g) / 2), basis=frame(du)), (v1_ - v0_, ytop + 0.03 - g, u1 - u0), "kvadr_sedy")
    deska(e0 - dl, e1, vo, vo + dl); deska(e0 - dl, sj["u_horni"], v0, vo)
    for uu in np.linspace(e0 + 0.2, e1 - 0.2, 4):   # sloupky stříšky na opěrné zdi
        P.beam(W(uu, vz_, kz), W(uu, vz_, kz + 1.4), 0.16, 0.16, "dub", j=0.4)
    P.beam(W(e0, vz_, kz + 1.4), W(e1, vz_, kz + 1.4), 0.18, 0.2, "dub")
    lib.shingle_roof(P, W(e0, vz_ + 0.4, kz + 1.35), W(e1, vz_ + 0.4, kz + 1.35), W(e1, v0 - 0.1, kz + 2.2), W(e0, v0 - 0.1, kz + 2.2), ridge=False)
    # pochodně
    svetlo(W(Li * 0.25, (sa["v0"] + Wv) / 2, y + 2.0)); svetlo(W(Li * 0.7, (sa["v0"] + Wv) / 2, y + 2.0))
    svetlo(W((zs["u0"] + Li) / 2, 1.1, y + 1.6), 0.8, 4.0); svetlo(W(sj["u_dvere"], vm, y + 2.4), 1.0, 5.0)
    # trasa testu: ze dvora šíjí dolů, do sálu, do každé kobky a do zásobárny
    tr = [bod(W(sj["u_horni"] - 2.5, vm + 1.2)), bod(W(sj["u_horni"] - 0.8, vm)), bod(W(sj["u_horni"] + 0.4, vm)), bod(W(u_dole + 0.6, vm), y),
          bod(W(sj["u_dvere"], vm), y), bod(W(sj["u_dvere"], Wv - 0.6), y), bod(W(sj["u_dvere"], (sa["v0"] + Wv) / 2), y)]
    for k in S["kobky"]:
        um = (k["u0"] + k["u1"]) / 2
        tr += [bod(W(um, pr["v1"] + 0.9), y, 0.15), bod(W(um, 1.0), y), bod(W(um, pr["v1"] + 0.9), y, 0.15)]
    tr += [bod(W((zs["u0"] + Li) / 2, pr["v1"] + 0.9), y, 0.15), bod(W((zs["u0"] + Li) / 2 - 0.4, 1.2), y)]
    TR["A_sklep_kobky"] = tr

# ------------------------------------------------------------------ obytný palác
def palac_A(P, p0, p1, bd, PI):
    """Vnitřek paláce (Míša 2. 11.: obytné místnosti): přízemí síň se schodištěm + kuchyně za příčkou, patro obytný sál
    s krbem, podkroví (hrázděné patro). Stropy trámové s otvory nad schody, zábradlí, světla; kolize = zdi + podlahy."""
    d = hz(p1 - p0); L = d.length; d /= L; s = d.cross(UP).normalized()
    h = bd["hloubka"]; t = 1.1; vi = h / 2 - t / 2
    W = lambda u, v, y=0.0: p0 + d * u + s * v + UP * y
    F0, F1, F2 = PI["patra_y"]; iw = L - t; c = W(L / 2, 0)
    s1 = PI["schody1"]; s2 = PI["schody2"]
    run1 = round((F1 - F0) / 0.195) * 0.25; run2 = round((F2 - F1) / 0.195) * 0.25
    v1 = -vi + s1["v_od_zdi"]; v2 = vi - s2["v_od_zdi"]
    u1t = s1["u0"] + s1["smer"] * run1; u2t = s2["u0"] + s2["smer"] * run2
    o1 = (min(s1["u0"], u1t) - 0.2 - L / 2, max(s1["u0"], u1t) + 0.2 - L / 2, -vi - 0.05, -vi + s1["sirka"] + 0.15)
    o2 = (min(s2["u0"], u2t) - 0.2 - L / 2, max(s2["u0"], u2t) + 0.2 - L / 2, vi - s2["sirka"] - 0.15, vi + 0.05)
    podlaha(P, c, d, iw, h - t, F0 + 0.02, (), tl=0.12)
    podlaha(P, c, d, iw, h - t, F1, [o1])
    podlaha(P, c, d, L + 0.5, h + 0.5, F2, [o2])
    # příčka v přízemí (síň | kuchyně) s dveřmi
    pu = PI["pricka_u"]
    dv_ = PI["pricka_dvere_v"]   # příčka stojí na podlaze (zed2 by šla až do sklepa pod palácem)
    for v0_, v1_ in ((-vi, dv_ - 0.48), (dv_ + 0.48, vi)):
        P.box(M(W(pu, (v0_ + v1_) / 2, (F0 + F1 - 0.25) / 2), basis=frame(s)), (0.5, F1 - 0.25 - F0, v1_ - v0_), "zdivo")
    P.box(M(W(pu, dv_, (F0 + 2.1 + F1 - 0.25) / 2), basis=frame(s)), (0.5, F1 - 0.25 - F0 - 2.1, 0.96), "zdivo")
    # schodiště: síň -> sál (podél hradební zdi), sál -> podkroví (podél nádvorní zdi)
    schody2(P, W(s1["u0"], v1), d * s1["smer"], F0 + 0.02, F1, s1["sirka"], zabradli=(1,) if s1["smer"] > 0 else (-1,), podklad=F0, r=0.25, vyska_st=0.195)
    schody2(P, W(s2["u0"], v2), d * s2["smer"], F1, F2, s2["sirka"], zabradli=(-1,) if s2["smer"] > 0 else (1,), podklad=F1, r=0.25, vyska_st=0.195)
    # zábradlí kolem otvorů (výstup u horního konce zůstává volný)
    zabradli(P, W(u1t - s1["smer"] * 1.1, -vi + s1["sirka"] + 0.15), W(s1["u0"] + s1["smer"] * -0.2, -vi + s1["sirka"] + 0.15), F1)
    zabradli(P, W(s1["u0"] + s1["smer"] * -0.2, -vi), W(s1["u0"] + s1["smer"] * -0.2, -vi + s1["sirka"] + 0.15), F1)
    zabradli(P, W(s2["u0"] - s2["smer"] * 0.2, vi - s2["sirka"] - 0.15), W(u2t - s2["smer"] * 1.1, vi - s2["sirka"] - 0.15), F2)
    zabradli(P, W(s2["u0"] - s2["smer"] * 0.2, vi), W(s2["u0"] - s2["smer"] * 0.2, vi - s2["sirka"] - 0.15), F2)
    # krb v sále u hradební zdi (ohniště, plášť, digestoř do komína), pec v kuchyni
    kr = PI["krb"]; kv = -vi if kr["strana"] == "hradba" else vi; kn = s if kv < 0 else -s
    P.box(M(W(kr["u"], kv, F1) + kn * 0.45 + UP * 0.15, basis=frame(d)), (0.9, 0.3, 1.8), "kvadr")
    for sg in (-1, 1): P.box(M(W(kr["u"] + sg * 0.8, kv, F1) + kn * 0.4 + UP * 0.8, basis=frame(d)), (0.8, 1.6, 0.25), "kvadr")
    P.box(M(W(kr["u"], kv, F1) + kn * 0.5 + UP * 2.0, basis=frame(d)), (1.0, 0.8, 1.9), "omitka")
    P.box(M(W(1.4, 0, F0) + UP * 0.5, basis=frame(d)), (2.0, 1.0, 1.4), "zdivo")   # kuchyňská pec / ohniště u čela
    # stůl a lavice v sále
    st = W(8.6, 1.0, F1)   # mimo průchod schody -> sál -> schody do podkroví
    P.box(M(st + UP * 0.75, basis=frame(d)), (0.9, 0.08, 3.0), "dub", collide=True)
    for sg in (-1, 1):
        P.box(M(st + s * sg * 0.75 + UP * 0.45, basis=frame(d)), (0.35, 0.06, 2.8), "dub", collide=True)
        for k in (-1.2, 1.2): P.box(M(st + d * k + s * sg * 0.75 + UP * 0.21, basis=frame(d)), (0.25, 0.42, 0.08), "dub")   # nohy lavice (visela – kontrola_geometrie)
        for k in (-1.2, 1.2): P.box(M(st + d * k + s * sg * 0.3 + UP * 0.37, basis=frame(d)), (0.08, 0.74, 0.08), "dub")
    # nájezd z nádvoří přes práh vstupu
    vs = PI["vstup"]; prah = W(vs["od_m"], vi + t + 0.02)   # vnější líc zdi (osa zdi je h/2, líc h/2 + t/2)
    zem = min(ter(*(prah + s * 2.0 + d * k).xz) for k in (-0.6, 0, 0.6))   # nájezd až na skutečný terén (u šíje je níž)
    nabeh(P, prah, s, F0, vs["sirka"] + 0.4, L=2.2, spad=F0 - zem + 0.15)
    # světla
    for (u, v, y, e) in ((9.0, 0.0, F0, 1.1), (3.0, 0.0, F0, 0.9), (3.5, 0.0, F1, 1.3), (8.5, 0.0, F1, 1.1), (6.0, 0.0, F2, 0.9)):
        svetlo(W(u, v, y + 2.1), e, 6.0)
    svetlo(W(kr["u"], kv, F1) + kn * 0.8 + UP * 0.5, 1.6, 5.0)
    # trasa testu: z nádvoří do síně, do kuchyně, po schodech do sálu a do podkroví
    TR["A_palac"] = [bod(W(vs["od_m"], vi + 3.5)), bod(W(vs["od_m"], vi + 1.2)), bod(W(vs["od_m"], vi - 0.8), F0),
                     bod(W(pu + 0.9, PI["pricka_dvere_v"]), F0), bod(W(pu - 1.2, PI["pricka_dvere_v"]), F0), bod(W(pu + 0.9, PI["pricka_dvere_v"]), F0),
                     bod(W(s1["u0"] + 0.75, 0.0), F0), bod(W(s1["u0"] + 0.75, v1), F0), bod(W(s1["u0"] - 0.6, v1)), bod(W(u1t - 0.6, v1), F1),
                     bod(W(4.0, 0.0), F1), bod(W(s2["u0"] - 0.75, 0.0), F1), bod(W(s2["u0"] - 0.75, v2), F1), bod(W(s2["u0"] + 0.6, v2)), bod(W(u2t + 0.7, v2), F2), bod(W(8.0, 0.0), F2)]

# ------------------------------------------------------------------ přední hrad
def postav_A(P):
    j = A["jadro"]; t = A["kurtina_tloustka"]; kor = A["koruna_y"]; br = A["brana"]
    U = [usek(j, i) for i in range(len(j))]
    # plášť; brána v seříznutém SV nároží
    for i, (a, b, L, d, vn) in enumerate(U):
        ot = [(L / 2, br["sirka"], br["prah_y"], br["vyska"])] if i == br["usek"] else []
        rv = A["vezicka"]["roh"]; wv = A["vezicka"]["rozmer"] / 2
        par = (-t / 2, L - wv) if i == rv - 1 else ((wv, L + t / 2) if i == rv else None)
        zed2(P, a, b, t, kor, vn, otvory=ot, par=par)
    naroze(P, [p for k, p in enumerate(j) if k != A["vezicka"]["roh"]], t, kor)
    a, b, L, d, vn = U[br["usek"]]; C = (a + b) / 2
    for sg in (-1, 1): portal(P, C - vn * sg * (t / 2), -vn * sg, br["sirka"], br["vyska"], br["prah_y"], 0.9, kridla=(sg < 0))
    dlazba(P, C, -vn, br["sirka"], t + 0.2, br["prah_y"] + 0.04)
    nA = -vn
    # nárožní věžička (kresba) – komora na úrovni koruny, dveře k ochozu východní zdi
    vz = A["vezicka"]; ri = vz["roh"]; aE, bE, LE, dE, vnE = U[ri - 1]
    rc = V(j[ri]); w = vz["rozmer"]; tv = 0.9
    vez2(P, rc, dE, w, w, kor, kor + vz["nad_korunou"], "jehlan", dvere=[("-d", OCH, 1.2, kor)], tw=tv)
    ram_v = vnitrek_veze(P, rc, dE, w - 2 * tv, w - 2 * tv, [kor, kor + vz["patro_nad_ochozem"]], [0], sq=0.7, run=2.64)
    svetlo(rc + UP * (kor + 2.0), 0.9, 4.0); svetlo(rc + UP * (kor + vz["patro_nad_ochozem"] + 2.0), 0.9, 4.0)
    # budovy podél plášťě
    SK = A.get("sklep"); g = hrad_geom.sklep(A) if SK else None
    for bd in A["budovy"]:
        a, b, L, d, vn = U[bd["usek"]]
        o = t / 2 + bd.get("odsazeni", -1.0) + bd["hloubka"] / 2
        p0 = a + d * bd["od_m"] + vn * o; p1 = a + d * bd["do_m"] + vn * o
        if SK and bd["id"] == SK["budova"]:   # palác se sklepem: podlaha zadaná, dveře ze šíje v S zdi (strana 0 = k nádvoří)
            sj = SK["sije"]
            PI = A["palac_interier"]; vs = PI["vstup"]
            budova_k(P, (p0.x, p0.z), (p1.x, p1.z), bd["hloubka"], bd["vyska_kamen"], bd["vyska_drevo"], bd["typ"], podl=SK["podlaha_palace_y"],
                     otvory=[(0, sj["u_dvere"] + g["tl"] / 2, sj["dvere"][0], SK["podlaha_y"], SK["podlaha_y"] + sj["dvere"][1]),
                             (vs["strana"], vs["od_m"], vs["sirka"], SK["podlaha_palace_y"], SK["podlaha_palace_y"] + vs["vyska"])],
                     vstup=(vs["strana"], vs["od_m"], vs["sirka"], vs["vyska"]), plna_kolize=False)
            palac_A(P, p0, p1, bd, PI)
        else:
            budova_k(P, (p0.x, p0.z), (p1.x, p1.z), bd["hloubka"], bd["vyska_kamen"], bd["vyska_drevo"], bd["typ"],
                     k_bodu=tuple(np.mean(np.array(A["jadro"], float), axis=0)), vnitrek=bd.get("vnitrek", [(0.7, 0.6), (0.5, 0.6)]))
    if SK: sklep_A(P, g)
    # ochoz: pavlače na úsecích, schodiště na východní zdi s podestou a sjezdem na pavlač
    sch = A["schody"]; a, b, L, d, vn = U[sch["usek"]]
    y_dole = ter(*(a + d * sch["od_m"] + vn * sch["odsazeni"]).xz)
    rise = kor - y_dole; n2 = round(rise / 2 / 0.19); run2 = n2 * 0.27
    st = a + d * sch["od_m"] + vn * sch["odsazeni"]
    e1, ym = schody2(P, st, -d, y_dole, y_dole + rise / 2, sch["sirka"], zabradli=(1, -1))
    plosina(P, e1 - d * 0.7, d, 1.4, sch["sirka"], ym)
    e2, _ = schody2(P, e1 - d * 1.4, -d, ym, kor, sch["sirka"], zabradli=(1, -1))
    s_top = sch["od_m"] - (run2 * 2 + 1.4)          # konec horního ramene (s na zdi)
    pod = a + d * (s_top - 0.8) + vn * ((t / 2 + 0.85 + sch["odsazeni"] + sch["sirka"] / 2) / 2)
    plosina(P, pod, d, 1.6, sch["odsazeni"] + sch["sirka"] / 2 - t / 2 - 0.8, kor, sloupy=True)
    mez = (s_top - 1.6, s_top + 0.05)
    oz = A["ochoz"]
    for i in oz["useky"]:
        a, b, L, d, vn = U[i]
        s0 = oz.get("usek%d_od_m" % i, -t / 2); s1 = L + t / 2
        if i == ri - 1: s1 = L - w / 2       # východní zeď končí u věžičky
        r0, r1 = zabr_konce(U, i, t, oz["useky"])
        if "usek%d_od_m" % i in oz: r0 = None
        if i == ri - 1: r1 = None
        ochoz2(P, a, b, t, kor, vn, s0, s1, mezery=[mez] if i == sch["usek"] else (), r0=r0, r1=r1)
    H.studna(P, *A["studna"])
    # hradba po hřebeni valu, vnější branka, předbraní a most
    vb = A["vnejsi_brana"]; O = C + nA * vb["t_m"]
    jadro_stred = Vector((float(np.mean([q[0] for q in A["jadro"]])), 0, float(np.mean([q[1] for q in A["jadro"]]))))
    hv = A["hradba_val"]; dB = Vector((-nA.z, 0, nA.x))   # zdi končí na bocích branky (ne v průjezdu – test průchodu A_vstup)
    sg = -1 if (V(hv["osa"][-1]) - O).dot(dB) < 0 else 1
    kon_z = O + dB * sg * (vb["rozmer"][0] / 2 - 0.3); pts = hv["osa"] + [[kon_z.x, kon_z.z]]
    hw = A["hradba_vychod"]; zac_v = O - dB * sg * (vb["rozmer"][0] / 2 - 0.3)   # druhá strana: po V valu k jádru
    for osa, hd in ((pts, hv), ([[zac_v.x, zac_v.z]] + hw["osa"], hw)):
        # hrady.zed staví cimbuří vpravo od směru: osu orientovat tak, aby cimbuří bylo ven od jádra (tablet 2. 11.)
        p, q = osa[0], osa[1]; dpq = Vector((q[0] - p[0], 0, q[1] - p[1])); mid = Vector(((p[0] + q[0]) / 2, 0, (p[1] + q[1]) / 2))
        if (mid - jadro_stred).dot(dpq.cross(UP)) < 0: osa = osa[::-1]
        H.zed_cara(P, osa, hd["tloustka"], hd["vyska"], cimburi=True)
    H.VEZ_PATRO.clear()
    H.vez(P, (O.x, O.z), tuple(vb["rozmer"]), vb["vyska"], "jehlan", yaw_d=(-nA.z, nA.x), brana=True, yf=vb["podlaha_y"], patro=vb.get("patro", True))
    if H.VEZ_PATRO:   # schody ke strážnici: dveře uvnitř šířky místnosti, podesta podél líce, schody kolmo od líce vedle mostu (průjezd i most volné)
        vp = H.VEZ_PATRO[0]; c_, d_, s_ = vp["stred"], vp["d"], vp["s"]; yp = vp["yp"]; du_ = vp["dvere_u"]; us = vp["w"] / 2 - 0.35
        lan = c_ + s_ * (vp["dpt"] / 2 + 0.75) + d_ * ((du_ + us) / 2)
        plosina(P, lan, d_, (us - du_) + 1.3, 1.4, yp)
        zab = c_ + s_ * (vp["dpt"] / 2 + 1.45) + d_ * us
        run = (yp - ter(zab.x, zab.z)) / 0.19 * 0.27
        for _ in range(3):
            a_ = zab + s_ * run; run = (yp - ter(a_.x, a_.z)) / 0.19 * 0.27
        a_ = zab + s_ * run
        schody2(P, a_, -s_, ter(a_.x, a_.z), yp, 1.0, zabradli=(1, -1))
        svetlo(c_ + UP * (yp + 2.0), 1.0, 5.0)
        TR["A_branka_patro"] = [bod(a_ + s_ * 1.8), bod(a_ + s_ * 0.6), bod(zab - s_ * 0.2, yp), bod(c_ + s_ * (vp["dpt"] / 2 + 0.75) + d_ * us, yp),
                                bod(c_ + s_ * (vp["dpt"] / 2 + 0.75) + d_ * du_, yp), bod(c_ + s_ * (vp["dpt"] / 2 - 0.3) + d_ * du_, yp), bod(c_, yp)]
    for sg in (1, -1):   # nájezd přes práh branky z terénu (žádný schod, test průchodu A_vstup)
        nabeh(P, O + nA * sg * (vb["rozmer"][1] / 2), nA * sg, vb["podlaha_y"], vb["rozmer"][0] - 2.0)
    m = A["most"]; zac = C + nA * vb["predprostor_t_m"][0]; kon = C + nA * (t / 2)
    most2(P, zac, vb["podlaha_y"], kon, br["prah_y"], m["sirka"], m["padaci_m"])
    yp = vb["podlaha_y"]; dvur = C - nA * 9
    TR["A_vstup"] = [bod(C + nA * 36), bod(C + nA * 30.5, yp), bod(C + nA * 26.5, yp), bod(C + nA * 13), bod(C + nA * 0.95, br["prah_y"]),
                     bod(C - nA * 3), bod(dvur), bod(V((0.0, 6.0)))]
    a, b, L, d, vn = U[sch["usek"]]
    TR["A_ochoz"] = [bod(dvur), bod(st + d * 1.4 + vn * 2.2), bod(st + d * 1.2), bod(st), bod(e1, ym), bod(e1 - d * 1.4, ym), bod(e2, kor), bod(pod, kor),
                     bod(pochozi(U, sch["usek"], s_top - 0.8), kor), bod(roh(U, 1), kor), bod(roh(U, 0), kor), bod(roh(U, 4), kor),
                     bod(pochozi(U, 4, oz["usek4_od_m"] + 0.6), kor)]
    sv = dE.cross(UP).normalized()
    (sa, se, sdir, sy0, sy1), = ram_v
    TR["A_vezicka"] = [bod(pochozi(U, ri - 1, 14.0), kor), bod(pochozi(U, ri - 1, LE - w / 2 - 0.8), kor), bod(rc - dE * 0.9 + sv * OCH, kor),
                       bod(sa - sdir * 0.3, kor), bod(sa + sdir * 0.8), bod(se - sdir * 0.05, None, 0.2), bod(se - sdir * 0.05 + sv * 1.6, sy1)]
    return C, nA

# ------------------------------------------------------------------ zadní hrad
def postav_B(P):
    hp = B["hradba"]; t = B["tloustka"]; kor = B["koruna_y"]; br = B["brana"]
    U = [usek(hp, i) for i in range(len(hp))]
    # hradba nesmí vést vnitřkem paláce (3. 11.: palác byl plný blok, po zprůchodnění v něm stála hradba do 14 m – test průchodu):
    # úsek uvnitř světlé plochy paláce se vynechá (palác má vlastní zdi), stejně nárožní pilíře a ochoz
    pa_ = B["palac"]; PA0, PA1 = V(pa_["osa"][0]), V(pa_["osa"][1]); pd = (PA1 - PA0).normalized(); ps = pd.cross(UP).normalized()
    pL = (PA1 - PA0).length; pW = pa_["hloubka"] / 2 - 0.55; pC = (PA0 + PA1) / 2
    def v_palaci(q, rez=0.0): q = q - pC; return abs(q.dot(pd)) < pL / 2 - 0.55 - rez and abs(q.dot(ps)) < pW - rez
    def usek_v_palaci(a, b):   # interval [s0, s1] úsečky a→b uvnitř světlé plochy paláce (vzorkováním po 5 cm)
        L_ = (b - a).length; ss = [k * 0.05 for k in range(int(L_ / 0.05) + 1)]; vn_ = [x for x in ss if v_palaci(a + (b - a) * (x / L_))]
        return (min(vn_), max(vn_)) if vn_ else None
    for i, (a, b, L, d, vn) in enumerate(U):
        ot = [(br["stred_m"], br["sirka"], B["dolni_y"], br["vyska"])] if i == br["usek"] else []
        iv = usek_v_palaci(a, b)
        if iv:   # u konce úseku i přesah zdi za vrchol (t/2)
            s0_ = iv[0] - (t if iv[0] < 0.1 else 0.05); s1_ = iv[1] + (t if iv[1] > L - 0.1 else 0.05)
            ot.append(((s0_ + s1_) / 2, s1_ - s0_, pa_.get("podlaha_min_y", -100.0), 200.0))
        zed2(P, a, b, t, kor, vn, otvory=ot, krok=3.0)
    hp_naroze = [q for q in hp if not v_palaci(V(q), -t)]
    naroze(P, hp_naroze, t, kor)
    a, b, L, d, vn = U[br["usek"]]; G = a + d * br["stred_m"]; vnG = vn
    for sg in (-1, 1): portal(P, G - vn * sg * (t / 2), -vn * sg, br["sirka"], br["vyska"], B["dolni_y"], 0.8, kridla=(sg < 0))
    dlazba(P, G, -vn, br["sirka"], t + 0.2, B["dolni_y"] + 0.04)
    # most přes průrvu: vodorovně z nástupu na práh
    m = B["most"]; zac = V(m["od"])
    most2(P, zac, m["nastup_y"], G - vn * (t / 2), B["dolni_y"], m["sirka"], m["padaci_m"])
    # terasa: opěrná zeď dolní/horní nádvoří s poprsní zídkou, kamenné schody uprostřed
    zt = B["terasa_z"]; xs = B["schody_terasa"]["x"]
    x0 = min(p[0] for p in hp) - 1; x1 = max(p[0] for p in hp) + 1
    ta, tb = V((x0 + 1.4, zt)), V((x1 - 1.6, zt))
    Lt = (tb - ta).length
    zed2(P, ta, tb, 1.0, B["horni_y"], Vector((0, 0, 1)), otvory=[((xs[0] + xs[1]) / 2 - ta.x, xs[1] - xs[0], B["horni_y"], 3.0)],
         cimburi=False, parapet=1.0, ext0=0, ext1=0)
    sts = V(((xs[0] + xs[1]) / 2, zt - 0.5 - (B["horni_y"] - B["dolni_y"]) / 0.19 * 0.3))
    schody2(P, sts, Vector((0, 0, 1)), B["dolni_y"], B["horni_y"],
            w=xs[1] - xs[0] - 0.1, kamenne=True, zabradli=())
    # hranolová věž: komora v úrovni ochozu, lávka z pavlače západní zdi
    vz = B["vez"]; c = V(vz["stred"]); w = vz["rozmer"]; tv = vz["steny"]
    vez2(P, c, Vector((1, 0, 0)), w, w, vz["dno_y"], vz["vrch_y"], "valba", dvere=[("-d", 0.0, 1.2, kor)], tw=tv)
    ram_b = vnitrek_veze(P, c, Vector((1, 0, 0)), w - 2 * tv, w - 2 * tv, [vz["dno_y"]] + vz["patra_y"], vz["steny_ramen"], sq=0.8)   # ramena 3,6 m = 40° (při 45° postava občas uvízla na konci ramene)
    # hladomorna v přízemí věže: valená klenba (osa S–J) s otvorem nad schody, kruhy s řetězy, slabé světlo
    iv = w - 2 * tv; ov = c - Vector((iv / 2, 0, iv / 2)); hl = vz["hladomorna"]
    klenba(P, ov, Vector((1, 0, 0)), Vector((0, 0, 1)), 0, iv, 0, iv, "v", vz["dno_y"] + hl["patka_nad_dnem"], hl["vzepeti"],
           diry=[(0, iv, iv - 1.3, iv)])   # celý pás nad schody (klenák u hrany otvoru vyčníval nad podlahu – test B_vez_sklep)
    kruh_retez(P, c - Vector((0, 0, iv / 2)), Vector((0, 0, 1)), vz["dno_y"] + 1.3, 1.0)
    kruh_retez(P, c - Vector((iv / 2, 0, -0.8)), Vector((1, 0, 0)), vz["dno_y"] + 1.3, 1.0)
    svetlo(c + UP * (vz["dno_y"] + 1.5), 0.5, 4.0)
    for yp in vz["patra_y"]:
        svetlo(c - Vector((0, 0, iv / 2 - 0.4)) + UP * (yp + 2.0), 1.1, 5.0)
    lav0 = c - Vector((w / 2, 0, 0));
    # západní pavlač: najít úsek hradby nejblíž dveřím
    iw = min(range(len(U)), key=lambda i: abs((lav0 - (U[i][0] + U[i][1]) / 2).length))
    a, b, L, d, vn = U[iw]
    sproj = max(0, min(L, (lav0 - a).dot(d))); hrana = a + d * sproj + vn * (t / 2 + 0.9)
    dl = (lav0 - hrana); dl.y = 0
    if dl.length > 0.1:
        plosina(P, (hrana + lav0) / 2, dl, dl.length + 0.3, 1.3, kor, sloupy=False)
    # palác 10×12
    p = B["palac"]
    budova_k(P, p["osa"][0], p["osa"][1], p["hloubka"], p["vyska_kamen"], p["vyska_drevo"], "palac",
             k_bodu=tuple(np.mean(np.array(B["hradba"], float), axis=0)), vnitrek=p.get("vnitrek", [(-0.8, -0.7), (-0.6, -0.7)]), patro_y=p.get("patro_y", 4.0))
    # schodiště na ochoz z horního nádvoří
    so = B["schody_ochoz"]; a, b, L, d, vn = U[so["usek"]]
    st = a + d * so["od_m"] + vn * 2.45
    e, _ = schody2(P, st, -d, B["horni_y"], kor, 1.2)
    s_top = so["od_m"] - round((kor - B["horni_y"]) / 0.19) * 0.27
    plosina(P, a + d * (s_top - 0.75) + vn * ((t / 2 + 0.85 + 3.05) / 2), d, 1.5, 3.05 - t / 2 - 0.8, kor)
    mez = {so["usek"]: (s_top - 1.5, s_top + 0.05), iw: (sproj - 0.8, sproj + 0.8)}
    for i in B["ochoz"]["useky"]:
        a, b, L, d, vn = U[i]
        r0, r1 = zabr_konce(U, i, t, B["ochoz"]["useky"])
        mz = ([mez[i]] if i in mez else [])
        iv = usek_v_palaci(a, b)
        if iv: mz.append((iv[0] - 1.0, iv[1] + 1.0))   # ochoz nevede palácem
        ochoz2(P, a, b, t, kor, vn, mezery=mz, r0=r0, r1=r1)
    a, b, L, d, vn = U[so["usek"]]; yd, yh = B["dolni_y"], B["horni_y"]; zz = Vector((0, 0, 1))
    TR["B_vstup"] = [bod(V((45.0, 96.0))), bod(V((48.2, 104.0))), bod(zac, m["nastup_y"]), bod(zac.lerp(G, 0.5)), bod(G - vnG * (t / 2), yd), bod(G, yd),
                     bod(G + vnG * 3), bod(sts - zz * 0.8, yd), bod(sts + zz * 2.6, yh), bod(V(((xs[0] + xs[1]) / 2, zt + 1.5)), yh)]
    TR["B_ochoz_vez"] = [bod(V(((xs[0] + xs[1]) / 2, zt + 1.5)), yh), bod(st + d * 1.2), bod(st, yh), bod(e, kor),
                         bod(a + d * (s_top - 0.75) + vn * ((t / 2 + 0.85 + 3.05) / 2), kor), bod(pochozi(U, so["usek"], s_top - 0.75), kor),
                         bod(roh(U, 1), kor), bod(roh(U, 0), kor), bod(roh(U, 9), kor), bod(roh(U, 8), kor), bod(pochozi(U, iw, sproj), kor), bod(lav0, kor), bod(c, kor)]
    q = (w - 2 * tv) / 2 - 0.4   # střed rohové podesty od středu věže
    nahoru = [bod(c, kor)]
    for (sa, se, sdir, y0, y1) in ram_b[1:]:   # vstupní patro -> strážní patra -> podkroví: přes volný střed patra k nástupu
        bok = (c - se) - sdir * (c - se).dot(sdir); bok.y = 0; bok = bok.normalized()   # z rohové podesty kolmo od stěny, mimo otvor
        nahoru += [bod(c, y0), bod(sa - sdir * 0.5, y0), bod(sa + sdir * 0.8), bod(se + sdir * 0.5, y1), bod(se + sdir * 0.5 + bok * 1.4, y1)]
    TR["B_vez_nahoru"] = nahoru
    sa, se, sdir, y0, y1 = ram_b[0]   # dolů do skladu (jen shora, po schodech)
    TR["B_vez_sklep"] = [bod(c, kor), bod(c + Vector((-q, 0, 1.0)), kor), bod(se + sdir * 0.5, kor), bod(se - sdir * 0.3, y1), bod(sa + sdir * 0.3),
                         bod(sa - sdir * 0.5, y0), bod(c + Vector((0, 0, 0.5)), y0)]
    return G

def stavba(suf):
    import bpy
    SV.clear(); TR.clear(); STAVBY.clear()
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    PA = Part("hrad_A"); postav_A(PA)
    PB = Part("hrad_B"); postav_B(PB)
    if suf == "":   # kolizní kvádry jako neprůhledné clony pro rozbor viditelnosti (nastroje/viditelnost.py, scény)
        kv = []
        for Pt in (PA, PB):
            for m, sz in Pt.cols:
                if sz[1] < 1.0: continue   # podlahy, mostovky, zábradlí výhled nezakryjí
                c = m.translation; rohy = [m @ Vector((sx * sz[0] / 2, 0, sz2 * sz[2] / 2)) for sx, sz2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                kv.append({"vrch": round(c.y + sz[1] / 2, 2), "rohy": [[round(q.x, 2), round(q.z, 2)] for q in rohy]})
        json.dump({"popis": "kolizní kvádry hradů vyšší než 1 m (zdi, věže, budovy) – clony pro rozbor viditelnosti", "kvadry": kv},
                  open(os.path.join(K, "hra/data/stavby_clony.json"), "w"))
    H.uloz([PA, PB], "puchart" + suf, kolize=(suf == ""))
    if suf == "":
        cc = json.load(open(os.path.join(K, "pravidla/svet/cesty_puchart.json")))
        TR["cesta_mezi_hrady"] = [[p[0], p[1], None] for p in next(c for c in cc["cesty"] if c["id"] == "hrebenova")["osa"]] + [TR["B_vstup"][2]]
        json.dump({"popis": "záznamy staveb pro test smyslu (blender/puchart_hrad.py)", "stavby": STAVBY}, open(os.path.join(K, "hra/data/stavby_kontrola.json"), "w"), ensure_ascii=False)
        json.dump({"popis": "Pochodně (OmniLight3D bez stínů) ve věžích, hladomorně a sklepě – generuje blender/puchart_hrad.py.", "svetla": SV},
                  open(os.path.join(K, "hra/data/svetla.json"), "w"), ensure_ascii=False, indent=1)
        json.dump({"popis": "Trasy testu průchodu (generuje blender/puchart_hrad.py ze stejné geometrie jako hrad): body [x, z, y_podlahy|null], "
                   "postava jde po přímkách, musí dojít ke každému bodu (±0,6 m) ve výšce podlahy (±0,5 m).", "trasy": TR},
                  open(os.path.join(K, "hra/data/pruchody.json"), "w"), ensure_ascii=False, indent=1)

for det, suf in ((True, ""), (False, "_daleko")):
    R.seed(1393); H.nastav_detail(det)
    stavba(suf)
