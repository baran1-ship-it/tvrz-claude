"""Dvojhradí Puchart podle dochovaných zdrojů a kreseb (pravidla/svet/hrad_puchart.json; zdroje docs/hrady_zdroje.md).

Královský architekt (Míša 30. 10.): tvary a průchody, ne textury. Každá pochozí plocha je v kolizi jako kvádr nebo
rampa (Havran fort.py: covered_walk, wall_stair, bridge – kolize z kvádrů, ne z prken): mosty od nástupu až na práh
brány bez schodu, brány skrz plášť rovnou do nádvoří, ochoz na koruně + pavlač do nádvoří (světlá šířka 2,2 m),
schodiště s podestou na ochoz, ochoz prochází věžičkou / vede k věži. Zdivo dostává kolizi samo (materiály PEVNE),
dřevo jen tam, kde se po něm chodí nebo kde drží (zábradlí).
  /opt/bl/bin/python blender/puchart_hrad.py <koren_puchartu>
Výstup: hra/modely/hrady/puchart.glb (+ uzel KOLIZE, ve hře skrytý) a puchart_daleko.glb.
"""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrady as H
import portaly
from hrady import Part, M, R, frame, kit, lib, ter, UP, Vector, Matrix
import numpy as np
sys.path.insert(0, os.path.join(H.K, "nastroje"))
import hrad_geom

K = H.K
D = json.load(open(os.path.join(K, "pravidla/svet/hrad_puchart.json")))
A, B = D["A"], D["B"]

# ------------------------------------------------------------------ kolize zdiva automaticky
_KA = json.load(open(os.path.join(H.K, "pravidla/svet/hrad_puchart.json")))["kolize_auto"]
PEVNE = _KA["materialy"]; SVISLE = set(_KA.get("jen_svisle", []))   # materiál -> min. tloušťka; dřevo jen svislé díly
_box = Part.box
def _auto_kol(self, m, size, mat):
    if mat not in PEVNE or min(size) < PEVNE[mat] or self.name == "KOLIZE": return False
    if mat in SVISLE:   # nejdelší osa kvádru musí být svislá (sloupek, koza, svislé prkno) – ne stupeň, schodnice, trám pod podlahou
        i = max(range(3), key=lambda k: size[k]); osa = m.to_3x3().col[i].normalized()
        svisly = abs(osa.y) > 0.9
        if svisly: return size[i] >= _KA.get("svisle_min_delka_m", 0.0)   # krátký svislý sloupek zábradlí: kryje ho panel zábradlí
        return min(size) >= _KA.get("tram_min_m", 9.0)   # silný trám v jiném směru (vzpěry, kozy); prkna stupňů a schodnice ne
    return True
def _box_kol(self, m, size, mat, uvo=None, rnd=None, collide=False):
    if _DBG and collide is not None and (collide or _auto_kol(self, m, size, mat)):
        import sys as _s; f_ = _s._getframe(2); _DBGL.append((m.translation.copy(), tuple(size), "auto %s %s:%d" % (mat, f_.f_code.co_name, f_.f_lineno)))
    _box(self, m, size, mat, uvo=uvo, rnd=rnd, collide=False if collide is None else (collide or _auto_kol(self, m, size, mat)))   # None = výslovně bez kolize (kryje ji rampa)
Part.box = _box_kol

_DBG = os.environ.get("PUCHART_DBG"); _DBGL = []   # ladění kolizí: PUCHART_DBG="x,z,y" vypíše kolizní kvádry do 2 m
POCH = []; ZABR = []   # pochozí plochy (plošiny, pavlače, podlahy) a zábradlí – hlídač volných hran (Míša 4. 11.)
STAVBY = []   # záznamy staveb pro test smyslu (hra/data/stavby_kontrola.json): vstupy budov, kozy mostů
NABEHY = []   # nájezdy na prahy [x, z, y, spad, délka, kdo] → hra/data/nabehy.json (test smyslu nabeh_vyska)
NASTUPY = []   # nástupy mostů [x, z, y] → hra/data/nastupy_mostu.json: cesty.py tam zvedne cestu (násyp v terénu, ne hranol)
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
    if _DBG: import sys as _s; f_ = _s._getframe(1); _DBGL.append((c.copy(), tuple(size), "%s:%d d=%s" % (f_.f_code.co_name, f_.f_lineno, [round(x, 2) for x in hz(d).normalized().xz])))

def vnitrek(pts):
    return Vector((sum(p[0] for p in pts) / len(pts), 0, sum(p[1] for p in pts) / len(pts)))

def usek(pts, i):
    a, b = V(pts[i]), V(pts[(i + 1) % len(pts)]); L = (b - a).length; d = (b - a) / L
    vn = d.cross(UP).normalized()
    if (vnitrek(pts) - (a + b) / 2).dot(vn) < 0: vn = -vn
    return a, b, L, d, vn

# ------------------------------------------------------------------ plášť a ochoz
def _kol(P, m, size, mat):
    """Jen kolizní kvádr (stejná pravidla jako automatická kolize zdiva) – viditelná zeď je souvislá síť (stena_sit)."""
    if _auto_kol(P, m, size, mat):
        if _DBG:
            import sys as _s; f_ = _s._getframe(1); _DBGL.append((m.translation.copy(), tuple(size), "auto %s %s:%d" % (mat, f_.f_code.co_name, f_.f_lineno)))
        P.cols.append((m.copy(), tuple(size)))

ZDI_SIT = []   # záznam zdí stavěných jako jedna síť – hlídač švů (build/zdi.json, test smyslu zdi_bez_svu)
RELIEF_KROK = json.load(open(os.path.join(H.K, "pravidla/svet/hrad_vzhled.json")))["zdivo"]["mrizka_m"] * 1.33   # < mrizka·1,4: reliéf síť zdi nedělí
def stena_sit(P, a, d, vo, t, xs, ys, hloubka, mat, cela=(True, True), y_jemne=-1e9):
    """Zeď jako JEDNA síť se sdílenými vrcholy (Míša 5. 11.: „černé čáry máš pořád a všude“ – skládaná zeď z kvádrů má
    vnitřní čela, jejichž hrana leží v rovině líce souseda: hloubkový buffer je nerozliší a čelo prosvítá černou čárou).
    Mřížka xs (podél osy d od a) × ys (výšky); hloubka(x, y) středu buňky = do jaké hloubky od líce (vo) je buňka plná, None = prázdná.
    Líc je ve hloubce −PRESAH; rub buňky v její hloubce; ostění/koruna/pata jen tam, kde se hloubky sousedů liší."""
    PR = lib.PRESAH
    def jemne(hr, od=-1e9):   # reliéf kamene (hrady.relief) dělí hrany delší než mrizka·1,4 každou plochu zvlášť – T-spoje = škvíry
        out = [hr[0]]                # (od: úseky celé pod touto výškou = pata v zemi, nejsou vidět – nedělit, šetří trojúhelníky)
        for u0, u1 in zip(hr, hr[1:]):
            if u1 <= od: out.append(u1); continue
            n_ = max(1, math.ceil((u1 - u0) / RELIEF_KROK - 1e-9))
            out += [u0 + (u1 - u0) * k / n_ for k in range(1, n_ + 1)]
        return out
    if H.DETAIL: xs = jemne(xs); ys = jemne(ys, y_jemne)   # dálková verze je bez reliéfu
    nx, ny = len(xs) - 1, len(ys) - 1
    D = [[hloubka((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2) for j in range(ny)] for i in range(nx)]
    Q = sorted({round(q, 5) for r in D for q in r if q is not None} | {round(-PR, 5)})
    if H.DETAIL: Q = jemne(Q)   # společné hloubkové hladiny pro všechna ostění (sdílené vrcholy i v tloušťce zdi)
    def qs(q0, q1): return [q for q in Q if q0 - 1e-6 <= q <= q1 + 1e-6]
    V_ = {}; verts = []; faces = []
    def v(i, j, q):
        k = (i, j, round(q, 5))
        if k not in V_:
            V_[k] = len(verts); verts.append(a + d * xs[i] + UP * ys[j] + vo * (t / 2 - q))
        return V_[k]
    def quad(ks, n):
        p0, p1, p2 = (verts[k] for k in ks[:3])
        if (p1 - p0).cross(p2 - p0).dot(n) < 0: ks = ks[::-1]
        faces.append(tuple(ks))
    for i in range(nx):
        for j in range(ny):
            q = D[i][j]
            if q is None: continue
            quad([v(i, j, -PR), v(i + 1, j, -PR), v(i + 1, j + 1, -PR), v(i, j + 1, -PR)], vo)    # líc
            quad([v(i, j, q), v(i + 1, j, q), v(i + 1, j + 1, q), v(i, j + 1, q)], -vo)           # rub (nika: dno niky)
    hl = lambda i, j: None if (i < 0 or j < 0 or i >= nx or j >= ny) else D[i][j]
    for i in range(nx + 1):   # svislé hrany mřížky: boky (ostění, konce zdi)
        if (i == 0 and not cela[0]) or (i == nx and not cela[1]): continue
        for j in range(ny):
            l, r = hl(i - 1, j), hl(i, j); ql = -PR if l is None else l; qr = -PR if r is None else r
            if abs(ql - qr) < 1e-6: continue
            hq = qs(min(ql, qr), max(ql, qr))
            for q0, q1 in zip(hq, hq[1:]):
                quad([v(i, j, q0), v(i, j + 1, q0), v(i, j + 1, q1), v(i, j, q1)], d if ql > qr else -d)
    for j in range(ny + 1):   # vodorovné hrany: koruna, pata, parapet a nadpraží otvorů
        for i in range(nx):
            dn, up = hl(i, j - 1), hl(i, j); qd = -PR if dn is None else dn; qu = -PR if up is None else up
            if abs(qd - qu) < 1e-6: continue
            hq = qs(min(qd, qu), max(qd, qu))
            for q0, q1 in zip(hq, hq[1:]):
                quad([v(i, j, q0), v(i + 1, j, q0), v(i + 1, j, q1), v(i, j, q1)], UP if qd > qu else -UP)
    if faces:
        P.mesh([tuple(p) for p in verts], faces, mat)
        if H.DETAIL:
            vid = [f for f in faces if min(verts[k].y for k in f) > y_jemne - 1e-6] or faces   # pata v zemi se nedělí (není vidět)
            dl = max(max((verts[f[k]] - verts[f[k - 1]]).length for k in range(4)) for f in vid)
            ZDI_SIT.append({"bod": [round(a.x, 2), round(a.z, 2)], "ploch": len(faces), "max_hrana": round(dl, 3)})

def zed2(P, a, b, t, koruna, vn, otvory=(), cimburi=True, mat="zdivo", krok=3.5, ext0=None, ext1=None, parapet=1.0, par=None,
         cela=(True, True)):
    """Hradba s vodorovnou korunou (= podlaha ochozu) a pata stupňovitě po terénu. otvory = [(s_stred, šířka, y_podlahy,
    výška[, zbytek])]: pod podlahou zdivo (práh = podlaha průjezdu), nad otvorem překlad až do koruny; zbytek = nika zevnitř,
    na líci zůstane zeď této tloušťky (slupka okna). Cimbuří na vnější hraně. Viditelná zeď je jedna síť (stena_sit),
    kolize zůstávají kvádry. cela = zda jsou konce zdi vidět (False: konec zalícovaný do jiné zdi – čelo by dělalo čáru)."""
    L = (b - a).length; d = (b - a) / L; vo = -vn; PR = lib.PRESAH
    e0 = t / 2 if ext0 is None else ext0; e1 = t / 2 if ext1 is None else ext1
    # --- kolize: stejné kvádry jako dřív; dálková verze (bez kolizí, švy z dálky nejsou vidět) z nich staví i viditelnou zeď
    def kus(m, size, mat):
        if H.DETAIL: _kol(P, m, size, mat)
        else: P.box(m, size, mat, collide=None)
    hrany = {-e0, L + e1}
    for o in otvory: hrany |= {o[0] - o[1] / 2, o[0] + o[1] / 2}
    for k in np.arange(-e0, L + e1, krok): hrany.add(float(k))
    hrany = sorted(h for h in hrany if -e0 <= h <= L + e1)
    pata = []   # (s0, s1, y0) sloupce paty po terénu
    for s0, s1 in zip(hrany, hrany[1:]):
        if s1 - s0 < 0.01: continue
        sm = (s0 + s1) / 2; c = a + d * sm
        y0 = min(ter(*(a + d * s).xz) for s in np.linspace(s0, s1, 4)) - 1.5
        pata.append((s0, s1, y0))
        ots = sorted((o for o in otvory if len(o) < 5 and o[0] - o[1] / 2 - 1e-6 <= sm <= o[0] + o[1] / 2 + 1e-6), key=lambda o: o[2])
        dily = []; yc = y0
        for o in ots:
            dily.append((yc, o[2])); yc = max(yc, o[2] + o[3])
        dily.append((yc, koruna))
        for ya, yb in dily:
            if yb - ya > 0.05: kus(M((c.x, (ya + yb) / 2, c.z), basis=frame(d)), (t, yb - ya, s1 - s0), mat)
    stinky = []; pz = []
    if parapet > 0:
        pc = vo * (t / 2 - 0.275)
        rez = [(o[0] - o[1] / 2, o[0] + o[1] / 2) for o in otvory if len(o) < 5 and o[2] + o[3] >= koruna - 0.01]
        pa, pb = par if par else (-e0, L + e1)   # zídka nesmí vést skrz věž (test průchodu A_vezicka)
        hr = sorted({pa, pb} | {x for r in rez for x in r if pa < x < pb})
        for s0, s1 in zip(hr, hr[1:]):
            sm = (s0 + s1) / 2
            if any(r0 <= sm <= r1 for r0, r1 in rez) or s1 - s0 < 0.05: continue
            c = a + d * sm + pc; pz.append((s0, s1))
            kus(M((c.x, koruna + parapet / 2, c.z), basis=frame(d)), (0.55, parapet, s1 - s0), mat)
            if cimburi:   # stínky z lomového kamene, každá jinak dlouhá a vysoká, proluky nepravidelné (Míša 5. 11.: cimbuří se zuby, ne „minecraft“)
                rg_ = random.Random(int(abs(a.x * 131 + a.z * 71 + s0 * 13)))
                k = s0 + rg_.uniform(0.25, 0.6)
                while True:
                    dl_ = rg_.uniform(0.9, 1.35); hs_ = rg_.uniform(0.62, 0.9)
                    if k + dl_ > s1 - 0.2: break
                    q = a + d * (k + dl_ / 2) + pc; stinky.append((k, k + dl_, hs_))
                    kus(M((q.x, koruna + parapet + hs_ / 2, q.z), basis=frame(d)), (0.55, hs_, dl_), mat)
                    k += dl_ + rg_.uniform(0.55, 0.85)
    if not H.DETAIL: return
    # --- viditelná zeď: jedna síť
    xs = {-e0 - PR, L + e1 + PR}
    for o in otvory: xs |= {o[0] - o[1] / 2 + PR, o[0] + o[1] / 2 - PR}
    for s0, s1, _ in pata: xs |= {s0, s1}
    for s0, s1 in pz: xs |= {s0 - PR, s1 + PR}
    for k0, k1, _ in stinky: xs |= {k0 - PR, k1 + PR}
    xs = sorted(x for x in xs if -e0 - PR - 1e-6 <= x <= L + e1 + PR + 1e-6)
    xs = [x for i_, x in enumerate(xs) if i_ == 0 or x - xs[i_ - 1] > 0.004]
    ys = {koruna + PR}
    for s0, s1, y0 in pata: ys.add(y0 - PR)
    for o in otvory: ys |= {o[2] + PR, o[2] + o[3] - PR}
    if pz: ys |= {koruna + parapet + PR}
    for _, _, hs_ in stinky: ys.add(koruna + parapet + hs_ + PR)
    ys = sorted(ys); ys = [y for i_, y in enumerate(ys) if i_ == 0 or y - ys[i_ - 1] > 0.004]
    def y0_(xm):
        for s0, s1, y0 in pata:
            if s0 - 1e-6 <= xm <= s1 + 1e-6: return y0
        return pata[0][2] if xm < pata[0][0] else pata[-1][2]
    def hloubka(xm, ym):
        if ym < y0_(xm) - PR: return None
        if ym < koruna + PR:
            q = t + PR
            for o in otvory:
                if o[0] - o[1] / 2 + PR <= xm <= o[0] + o[1] / 2 - PR and o[2] + PR <= ym <= o[2] + o[3] - PR:
                    if len(o) < 5 or o[4] <= 0: return None
                    q = min(q, o[4] + PR)
            return q
        if ym < koruna + parapet + PR:
            return 0.55 + PR if any(s0 - PR <= xm <= s1 + PR for s0, s1 in pz) else None
        if ym < koruna + parapet + 0.9 + PR:
            return 0.55 + PR if any(k0 - PR <= xm <= k1 + PR and ym < koruna + parapet + hs_ + PR for k0, k1, hs_ in stinky) else None
        return None
    stena_sit(P, a, d, vo, t, xs, ys, hloubka, mat, cela=cela, y_jemne=min(y0 for _, _, y0 in pata) + 1.5 - 0.3)   # pata 1,5 m pod nejnižším terénem

def pokos_ext(poly, i, t):
    """Délka přesahu konců úseku i za vrcholy tak, aby se vnější líce sousedních úseků sešly přesně v pokosu (Míša 5. 11.:
    švy v nároží – s pevným přesahem t/2 vyčnívaly konce v tupém úhlu z líce souseda)."""
    n_ = len(poly); P0 = np.array(poly[i - 1], float); A_ = np.array(poly[i], float); B_ = np.array(poly[(i + 1) % n_], float); C_ = np.array(poly[(i + 2) % n_], float)
    def uhel(p, q, r):
        u = q - p; v = r - q; u /= np.linalg.norm(u); v /= np.linalg.norm(v)
        return math.acos(max(-1.0, min(1.0, float(u @ v))))
    return (t / 2 * math.tan(uhel(P0, A_, B_) / 2) + 0.02, t / 2 * math.tan(uhel(A_, B_, C_) / 2) + 0.02)

def naroze(P, poly, t, koruna, parapet=0.0, vynechat=()):   # zídka na pilíři zatarasila ochoz v rohu (test průchodu)
    """Nároží obvodové hradby: klín na pokos mezi úseky, líce v rovině obou zdí (dřív čtverec t·1,12 natočený do osy úhlu –
    vystupoval z líců jako „zeď navíc“, Míša 4. 11.)."""
    n_ = len(poly); cen = Vector((sum(p[0] for p in poly) / n_, 0, sum(p[1] for p in poly) / n_)); h = t / 2
    for i, p in enumerate(poly):
        if i in vynechat: continue   # roh s věží: klín nestavět, ale sousedé zůstávají skutečné (dřív se vrchol vyřadil ze seznamu → soused z protějšího rohu, zub z nároží, Míša 5. 11.)
        c = V(p); a = V(poly[i - 1]); b = V(poly[(i + 1) % n_])
        def ven(p0, p1):
            dd = (p1 - p0).normalized(); nn = dd.cross(UP).normalized()
            return -nn if (cen - (p0 + p1) / 2).dot(nn) > 0 else nn
        na, nb = ven(a, c), ven(c, b); k = 1.0 + na.dot(nb)
        mo = (na + nb) / k * h if k > 0.15 else (na + nb).normalized() * h * 2.5
        body = [c + na * h, c + mo, c + nb * h, c - na * h, c - nb * h]   # bez vnitřního hrotu (trčel z paláce B)
        # konvexní obal v rovině xz
        import math as _m
        body = sorted(body, key=lambda q: _m.atan2(q.z - c.z, q.x - c.x))
        if (body[1] - body[0]).cross(body[2] - body[0]).dot(UP) < 0: body.reverse()
        y0 = min(ter(c.x + dx, c.z + dz) for dx in (-t, 0, t) for dz in (-t, 0, t)) - 1.5
        P.prism([q + UP * y0 for q in body], UP * (koruna - y0), "zdivo")
        if k > 0.15 and (b - c).normalized().dot(na) < -0.05:   # vypouklé nároží: nárožní kameny (Míša 9. 11.)
            R_ = c + mo; H.narozi(P, R_, ((a - c).normalized(), na), ((b - c).normalized(), nb), ter(R_.x, R_.z) - 0.2, koruna)
        bis_ = ((c - a).normalized() + (b - c).normalized()).normalized()
        P.cols.append((M((c.x, (y0 + koruna) / 2, c.z), basis=frame(bis_)), (t * 0.8, koruna - y0, t * 0.8)))   # uvnitř klínu: čtverec t·1,12 natočený do osy úhlu trčel z líce jako neviditelná stěna (test povrch_kolize skala_540, hrad B); zbytek rohu kryjí kolize zdí s pokosovým přesahem
        mh_ = Vector((mo.x, 0, mo.z))
        if mh_.length > 0.56 * t:   # vnější hrot klínu: kvádr jen ven od rohu (dovnitř nádvoří nic)
            for sg_ in (1,):   # vnější hrot klínu
                q_ = c + mh_ * 0.3   # jen vnitřní část hrotu (0,6 délky): plný kvádr t·0,4 až do špičky trčel z líců klínu (neviditelná stěna)
                P.cols.append((M((q_.x, (y0 + koruna) / 2, q_.z), basis=frame(mh_.normalized())), (t * 0.4, koruna - y0, mh_.length * 0.6)))
        if parapet > 0:
            P.prism([q + UP * koruna for q in body], UP * parapet, "zdivo")

def ochoz2(P, a, b, t, koruna, vn, s0=None, s1=None, mezery=(), kryty=False, sirka=0.9, r0=None, r1=None, lehka=False, pod=(0, 0)):
    """Pavlač ochozu vyložená do nádvoří na krakorcích (Havran gallery) v úrovni koruny: prkna, kolizní deska, krakorce,
    zábradlí se sloupky po 1,5 m a kolizí. r0/r1 = konce zábradlí (v rozích průsečík se zábradlím sousední zdi – souvislé,
    Míša 30. 10.: zábradlí na ochozech), mezery = sjezdy schodišť a lávky."""
    L = (b - a).length; d = (b - a) / L
    s0 = -t / 2 if s0 is None else s0; s1 = L + t / 2 if s1 is None else s1
    roh0 = r0 is not None; r1_dan = r1 is not None   # roh se sousední pavlačí: krakorec v rohu staví sousední úsek (svůj konec r1) – ne dva v sobě
    r0 = s0 if r0 is None else r0; r1 = s1 if r1 is None else r1
    if s1 - s0 < 0.3: return
    lic = vn * (t / 2); g = lic + vn * (sirka / 2); hr = lic + vn * (sirka - 0.06)
    p0, p1 = a + d * s0, a + d * s1
    if H.DETAIL and lehka:   # dlouhé pavlače hradeb: každé prkno kvádr (12 troj. místo ~70 u kit.plank) – rozpočet scén 2,1 M (hlídač scén 3. 11.)
        rg_ = random.Random(int(abs(p0.x * 100 + p0.z * 37))); u_ = s0
        o_r = t / 2 + sirka - 0.06
        while u_ < s1 - 0.05:
            pw = min(rg_.uniform(0.24, 0.3), s1 - u_); uc = u_ + pw / 2; omax = t / 2 + sirka
            # v rohu prkna končí na úhlopříčce rohu (pokos) – dřív prkna obou pavlačí přes sebe (Míša 4. 11.: „ochoz překřížený“)
            if roh0 and uc < r0 and r0 > 1e-3: omax = min(omax, o_r * max(uc, 0.0) / r0 + 0.03)
            if r1_dan and uc > r1 and L - r1 > 1e-3: omax = min(omax, o_r * max(L - uc, 0.0) / (L - r1) + 0.03)
            if omax - t / 2 > 0.06:
                q_ = a + d * uc + vn * ((t / 2 + omax) / 2) + UP * (koruna - 0.03)   # délka prkna napříč pavlačí (lokální z), atlas prken
                P.box(M(q_, basis=frame(vn)), (pw - 0.012, 0.06, omax - t / 2), "prkno_ven", uvo=(rg_.uniform(0, 2.56), rg_.randrange(8) * 0.32 + 0.16))
            u_ += pw
    elif H.DETAIL:
        kit.deck(P, p0 + g + UP * (koruna - 0.03), p1 + g + UP * (koruna - 0.03), sirka / 2, "prkna_ven", beams=(-sirka / 2 + 0.12, sirka / 2 - 0.12))
    else:
        P.box(M((p0 + p1) / 2 + g + UP * (koruna - 0.04), basis=frame(d)), (sirka, 0.08, s1 - s0), "prkna_ven")
    k0, k1 = s0 + pod[0], s1 - pod[1]   # kolize desky ne pod schody (hrana desky nad rampou schodů zastavila postavu)
    kol(P, a + d * ((k0 + k1) / 2) + g - vn * 0.1 + UP * (koruna - 0.1), d, (sirka + 0.2, 0.2, k1 - k0)); POCH.append((P.cols[-1], koruna, "ochoz", P))
    # krakorce (vetknuté do zdi) a vzpěry čepem do krakorce (dřív končily pod ním jen půlkou čela – tesařské spoje 3. 11.)
    nk = max(1, round((s1 - s0 - 0.8) / 1.2)); ks = [s0 + 0.4 + (s1 - s0 - 0.8) * i / nk for i in range(nk + 1)]
    hrn = sorted({r0, r1} | {min(max(x, r0), r1) for m_ in mezery for x in m_})
    # u rohu: krakorce obou úseků zůstávají (bez nich mezi deskami pavlačí v rohu díra – postava uvízla, test B_ochoz_vez);
    # vzpěry krakorců blíž než 0,6 m od rohu ne (vrůstaly do krakorce sousední zdi)
    if roh0: ks = [k for k in ks if k > r0 + 0.5]   # roh nese krakorec sousedního úseku (jeho konec r1); naše krakorce v rohu ho křížily (spoje 9. 11.)
    for x in hrn:   # krakorec se sloupkem i v rohu a na kraji mezery (dřív madlo končilo u posledního krakorce – v rohu chybělo)
        if roh0 and abs(x - r0) < 1e-6: x = r0 + 0.55   # rohový krakorec za rohem – nekříží se s krakorcem sousední zdi
        x = min(max(x, s0 + 0.09), s1 - 0.09)
        ks = [k for k in ks if abs(k - x) > 0.45] + [x]
    ks.sort()
    if pod[0]: ks = [k for k in ks if not (k < s0 + pod[0] - 1e-3)]   # pod schody v pavlači: krakorec jen na konci schodnice (osedlání), ne pod ní
    if pod[1]: ks = [k for k in ks if not (k > s1 - pod[1] + 1e-3)]
    for k in ks:
        q = a + d * k
        P.beam(q + lic - vn * 0.25 + UP * (koruna - 0.18), q + lic + vn * (sirka + 0.08) + UP * (koruna - 0.18), 0.18, 0.2, "dub")   # hlava přečnívá za sloupek
        if H.DETAIL and not (roh0 and k < r0 + 0.6): P.beam(q + lic + UP * (koruna - 1.1), q + lic + vn * (sirka - 0.3) + UP * (koruna - 0.18), 0.12, 0.12, "dub", j=0.3)
    # zábradlí: sloupky na hlavách krakorců (čep do krakorce), madlo na hlavách sloupků (čep), střední tyč z líce sloupků
    # kde za zábradlím stojí zeď (věž, budova) do 0,3 m, zábradlí nestavět (Míša 4. 11.: „zábradlí u zdi“)
    zd = zdi_za(P, [a + d * u + hr + vn * 0.3 + UP * (koruna + 0.6) for u in np.arange(r0, r1, 0.3)])
    us_ = list(np.arange(r0, r1, 0.3)); zm = []
    for u, z_ in zip(us_, zd):
        if z_ and zm and abs(zm[-1][1] - u) < 0.35: zm[-1][1] = u + 0.3
        elif z_: zm.append([u - 0.15, u + 0.3])
    if zm:
        mezery = list(mezery) + [tuple(x) for x in zm]
        hrn = sorted(set(hrn) | {min(max(x, r0), r1) for m_ in zm for x in m_})
    for u0, u1 in zip(hrn, hrn[1:]):
        if any(m0 - 1e-6 <= (u0 + u1) / 2 <= m1 + 1e-6 for m0, m1 in mezery) or u1 - u0 < 0.15: continue
        sl = [k for k in ks if u0 - 0.05 <= k <= u1 + 0.05]
        if not sl: continue
        q0, q1 = a + d * u0 + hr, a + d * u1 + hr
        for k in sl:
            q = a + d * k + hr
            P.beam(q + UP * (koruna - 0.18), q + UP * (koruna + (2.3 if kryty else 1.0)), 0.12, 0.12, "dub", up=d, j=0.3)
        bok = -vn * (0.06 + 0.05) if kryty else Vector()
        P.beam(q0 + bok + UP * (koruna + 1.0), q1 + bok + UP * (koruna + 1.0), 0.14, 0.12, "dub", j=0.3, collide=None)   # madla: kolize vlastní (kol), ne automatická
        if H.DETAIL: P.beam(q0 - vn * 0.095 + UP * (koruna + 0.5), q1 - vn * 0.095 + UP * (koruna + 0.5), 0.07, 0.09, "dub", j=0.3, collide=None)
        kol(P, (q0 + q1) / 2 + UP * (koruna + 0.55), d, (0.12, 1.1, (q1 - q0).length)); ZABR.append((q0.copy(), q1.copy(), koruna, "ochoz2"))
    if not kryty: return
    P.beam(p0 + hr + UP * (koruna + 2.3), p1 + hr + UP * (koruna + 2.3), 0.16, 0.18, "dub")
    vo = -vn
    lib.shingle_roof(P, p0 + hr + vn * 0.3 + UP * (koruna + 2.25), p1 + hr + vn * 0.3 + UP * (koruna + 2.25),
                     p1 + vo * (t / 2 + 0.1) + UP * (koruna + 2.95), p0 + vo * (t / 2 + 0.1) + UP * (koruna + 2.95), ridge=False)

def k_lici(P, a, d, g, y, s_od, s_do, krok=0.05):
    """Konec pavlače u líce stavby: od s_od směrem k s_do první poloha mimo zdivo (osa pavlače a + d·s + g, 1 m nad podlahou).
    None = po celé délce volno (konec do prázdna, tam zábradlí)."""
    C = [(m, sz) for m, sz in P.cols if sz[1] > 1.5]
    sm = 1 if s_do > s_od else -1; s_ = s_od; byla_zed = False
    while (s_ - s_do) * sm < 0:
        q = a + d * s_ + g + UP * (y + 1.0)
        if any(_v_kvadru(m, sz, q) for m, sz in C if (m.translation - q).length < 0.87 * sum(sz) / 2 + 0.1): byla_zed = True
        elif byla_zed: return s_ - sm * 0.01   # 1 cm do líce (žádná škvíra)
        else: return None
        s_ += sm * krok
    return None

def ochoz_hradby(P, osa, uk, t, konce, mezery=None, sirka=0.9, odstup=3.0):
    """Ochoz hradby (Míša 3. 11.: „proč hradba nemá ochoz“; docs/reference/branka_ochoz.md): pavlač na krakorcích (ochoz2,
    Havran gallery) na vnitřní straně v úrovni koruny, po stupních koruny (zed() zaokrouhluje po 0,5 m) – kde koruna skočí,
    v pavlači krátké dřevěné schody. konce = {0|1: (y_prahu, bod portálku)} – u věže schody na práh portálku.
    mezery = {(x, z) horní konec schodiště ze země: délka mezery v zábradlí}. Vrací body trasy po pavlači (pořadí osy)."""
    body = []; cur = None; n = len(osa) - 1
    def podesta_k_portalku(p, dv, y):   # prkenná podesta od konce pavlače k prahu portálku, na krakorcích ve zdi věže
        v = hz(dv - p); Lp = v.length
        if Lp < 0.2: return
        vv = v / Lp; plosina(P, p + vv * ((Lp + 0.2) / 2), v, Lp + 0.2, sirka, y, sloupy=False)   # od konce schodů (bez přesahu – hrana desky zastavila postavu) do prahu
    for i in range(n):
        a, b = V(osa[i]), V(osa[i + 1]); L = (b - a).length; d = (b - a) / L
        vn = -d.cross(UP).normalized(); g = vn * (t / 2 + sirka / 2)
        ps = []
        for s0, s1, y in uk[i]:
            if ps and abs(ps[-1][2] - y) < 1e-3: ps[-1] = (ps[-1][0], s1, y)
            else: ps.append((s0, s1, y))
        pos = -t / 2 if i > 0 else 0.0; pod_ = False
        def rovne(dv, y):   # portálek v ose pavlače a v její výšce (Havran: ochoz vchází do věže rovně) – stačí pavlač až k líci
            s_d = (dv - a).dot(d); ods = abs((dv - (a + d * s_d + g)).dot(vn)); dy = max(abs(ps[0 if i == 0 else -1][2] - y), abs((cur if i else y) - y))
            n_ = konce[0 if i == 0 else 1][2]; uhel = math.degrees(math.acos(min(1.0, abs(d.dot(n_)))))
            STAVBY.append({"vstup_ochoz": [round(dv.x, 2), round(dv.z, 2)], "uhel_st": round(uhel, 1), "odsazeni_m": round(ods, 3), "vyska_m": round(dy, 3)})
            return ods < 0.15 and dy < 0.05, s_d
        if i == 0 and 0 in konce:
            cur, dv = konce[0][:2]; ok_, s_d = rovne(dv, cur)
            if ok_: pos = s_d; body.append(bod(dv, cur))
            else:   # záloha: podesta podél líce k portálku (osa pavlače míjí portálek)
                pos = max(0.0, s_d) + 1.4; podesta_k_portalku(a + d * pos + g, dv, cur)
                body.append(bod(dv, cur)); body.append(bod(a + d * pos + g, cur))
        if cur is None: cur = ps[0][2]; body.append(bod(a + d * pos + g, cur))
        mez = [(sm, sm + dl) for (q, dl) in (mezery or {}).items() for sm in [(V(q) - a).dot(d)]
               if -0.5 < sm < L and abs((V(q) - a).dot(vn)) < t + 3]
        def roh_s(j, k):   # průsečík linií zábradlí úseků j a k, poloha podél úseku j
            o = t / 2 + sirka - 0.06
            aj, bj = V(osa[j]), V(osa[j + 1]); dj = (bj - aj).normalized(); nj = -dj.cross(UP).normalized()
            ak, bk = V(osa[k]), V(osa[k + 1]); dk = (bk - ak).normalized(); nk = -dk.cross(UP).normalized()
            p, q = aj + nj * o, ak + nk * o; den = dj.x * dk.z - dj.z * dk.x
            if abs(den) < 1e-6: return None
            return ((q.x - p.x) * dk.z - (q.z - p.z) * dk.x) / den
        rr0 = roh_s(i, i - 1) if i > 0 else None; rr1 = roh_s(i, i + 1) if i < n - 1 else None
        def plocha(u0, u1, y, pod=(0, 0)):   # pod = přesah plochy pod schody na začátku/konci (bez zábradlí – tam je zábradlí schodů)
            if u1 - u0 > 0.3:
                ochoz2(P, a, b, t, y, vn, u0, u1, lehka=True, pod=pod, mezery=mez + ([(u0, u0 + pod[0])] if pod[0] else []) + ([(u1 - pod[1], u1)] if pod[1] else []), sirka=sirka,
                       r0=rr0 if u0 <= -t / 2 + 1e-3 else None, r1=rr1 if u1 >= L + t / 2 - 1e-3 else None)
                body.append(bod(a + d * u1 + g, y))
        def schod(u0, y0_, y1_):
            run = max(1, round(abs(y1_ - y0_) / 0.19)) * 0.27
            if y1_ > y0_: schody2(P, a + d * u0 + g, d, y0_, y1_, sirka - 0.05, zabradli=(-1,), podklad=y0_)
            else: schody2(P, a + d * (u0 + run) + g, -d, y1_, y0_, sirka - 0.05, zabradli=(1,), podklad=y1_)
            body.append(bod(a + d * (u0 + run) + g, y1_)); return run
        for p0, p1, y in ps:
            if abs(y - cur) > 1e-3:   # schody v pavlači: schodnice dosedají na krakorce na koncích ploch (plochy přesahují pod schody o 0,3 m)
                bnd = max(p0, pos); plocha(pos, bnd + 0.3, cur, (0.3 if pod_ else 0, 0.3)); run = schod(bnd, cur, y); pos = bnd + run - 0.3; pod_ = True; cur = y
        if i == 0 and 0 not in konce:   # volný konec: ochoz až k líci stavby (Míša 4. 11.: „proč není ochoz až ke zdi, zbytečné zábradlí“),
            zs_ = k_lici(P, a, d, g, cur, -t / 2, 6.0)   # koncové zábradlí jen kde žádná zeď není
            if zs_ is not None: pos = max(pos, zs_)
            else: pos = max(pos, odstup); zabradli(P, a + d * pos + vn * (t / 2), a + d * pos + vn * (t / 2 + sirka), cur)
        if i == n - 2 and 1 in konce and abs(uk[i + 1][0][2] - cur) > 1e-3:   # výšku koruny u věže vyrovnat schody PŘED rohem –
            ny = uk[i + 1][0][2]; run = max(1, round(abs(ny - cur) / 0.19)) * 0.27; endS = L - (t / 2 + sirka + 0.3)   # rovný úsek do věže zůstane rovný; schody končí před deskou rohu
            if endS - run - 0.3 > pos:
                plocha(pos, endS - run + 0.3, cur, (0.3 if pod_ else 0, 0.3)); schod(endS - run, cur, ny); pos = endS - 0.3; pod_ = True; cur = ny
        if i == n - 1 and 1 in konce and abs(cur - konce[1][0]) < 0.05 and rovne(konce[1][1], konce[1][0])[0]:   # pavlač už je ve výšce prahu
            yk, dv = konce[1][:2]; s_d = (dv - a).dot(d)
            plocha(pos, s_d, cur, (0.3 if pod_ else 0, 0))   # konec pavlače = práh portálku (bod trasy přidá plocha)
        elif i == n - 1 and 1 in konce:
            yk, dv = konce[1][:2]; endT = (dv - a).dot(d) - 1.4; run = max(1, round(abs(yk - cur) / 0.19)) * 0.27
            plocha(pos, endT - run + 0.3, cur, (0.3 if pod_ else 0, 0.3)); schod(endT - run, cur, yk); cur = yk
            podesta_k_portalku(a + d * endT + g, dv, yk); body.append(bod(dv, yk))
        else:
            zk_ = k_lici(P, a, d, g, cur, L + t / 2, L - 6.0) if i == n - 1 else None
            konec = L + t / 2 if i < n - 1 else (zk_ if zk_ is not None else L - odstup)
            plocha(pos, konec, cur, (0.3 if pod_ else 0, 0))
            if i == n - 1 and zk_ is None: zabradli(P, a + d * konec + vn * (t / 2), a + d * konec + vn * (t / 2 + sirka), cur)
    return body

def delka_ochozu(osa, hd, u_t):
    """Délka ochozu od branky (Míša 4. 11.: ochoz se schody jen u branné věže, ne po hradbách k hornímu hradu): z dat
    ochoz_od_branky_m; u hradby se schody ze země až za horní konec schodů (+ podesta)."""
    L = hd.get("ochoz_od_branky_m", 0.0)
    if L > 0 and "schody" in hd:
        q = V(hd["schody"]["horni_konec"]); pts = [V(p) for p in (osa if not u_t else osa[::-1])]; acc = 0.0; best = (1e9, 0)
        for a, b in zip(pts, pts[1:]):
            d = b - a; Ls = d.length; t_ = max(0, min(Ls, (q - a).dot(d / Ls))); e = (a + d / Ls * t_ - q).length
            if e < best[0]: best = (e, acc + t_)
            acc += Ls
        L = max(L, best[1] + 2.0)
    return L

def orez_ochozu(osa, uk, u_t, L):
    """Část osy (a korun úseků) délky L od konce u branky (u_t = 0 začátek, 1 konec osy)."""
    n = len(osa) - 1; idx = list(range(n)) if u_t == 0 else list(range(n - 1, -1, -1)); zbyva = L; vyb = {}
    for i in idx:
        a, b = V(osa[i]), V(osa[i + 1]); Ls = (b - a).length
        if zbyva >= Ls: vyb[i] = (osa[i], osa[i + 1], uk[i]); zbyva -= Ls; continue
        d = (b - a) / Ls
        if u_t == 0:
            nb = a + d * zbyva; vyb[i] = (osa[i], [nb.x, nb.z], [(s0, min(s1, zbyva), y) for s0, s1, y in uk[i] if s0 < zbyva])
        else:
            c = Ls - zbyva; na = a + d * c
            vyb[i] = ([na.x, na.z], osa[i + 1], [(max(s0, c) - c, s1 - c, y) for s0, s1, y in uk[i] if s1 > c])
        break
    ks = sorted(vyb); osa_o = [vyb[ks[0]][0]] + [vyb[k][1] for k in ks]; return osa_o, [vyb[k][2] for k in ks]

def pres_trasu(b, n_, r=0.5):
    """Kříží v bodě b (hrana s normálou n_) některá trasa průchodu hranu? (zábradlí nesmí stát přes cestu)"""
    for body in TR.values():
        for p, q in zip(body, body[1:]):
            P0 = Vector((p[0], 0, p[1])); Q0 = Vector((q[0], 0, q[1])); d = Q0 - P0; L = d.length
            if L < 1e-3: continue
            bb = Vector((b.x, 0, b.z)); t = max(0.0, min(L, (bb - P0).dot(d / L)))
            if (P0 + d / L * t - bb).length < r and abs((d / L).dot(Vector((n_.x, 0, n_.z)))) > 0.3: return True
    return False

def hrany_a_zabradli(parts, doplnit=True):
    """Hlídač (Míša 4. 11.: „někde je zábradlí u zdi a za ním, kde má být, není“): volná hrana pochozí plochy s pádem > 1 m
    bez zábradlí/zdi/navazující plochy = chyba; zábradlí, které má zeď do 0,25 m na jedné straně = zbytečné."""
    import numpy as _np
    C = [(m, sz) for Pt in parts for m, sz in Pt.cols]
    Ri = _np.array([_np.array(m.to_3x3().inverted()) for m, sz in C]); T = _np.array([list(m.translation) for m, sz in C])
    Hs = _np.array([[sz[0] / 2, sz[1] / 2, sz[2] / 2] for m, sz in C])
    def uvnitr(p, krom=None):
        q = _np.einsum("nij,nj->ni", Ri, _np.array(p)[None] - T); k = _np.all(_np.abs(q) <= Hs + 0.01, axis=1)   # 1 cm: vzorek přesně na spáře dvou kusů zdi
        if krom is not None: k[krom] = False
        return bool(k.any())
    idx = {id(c): i for i, c in enumerate(Pt_c for Pt in parts for Pt_c in Pt.cols)}
    volne = []; behy = {}
    for col, y, druh, Pd in POCH:
        m, sz = col; i0 = idx.get(id(col)); R = m.to_3x3(); c = m.translation
        for ax, sg in ((0, 1), (0, -1), (2, 1), (2, -1)):
            o = 2 - ax; n_ = R.col[ax].normalized() * sg; t_ = R.col[o].normalized(); Lh = sz[o]
            k = -Lh / 2 + 0.15
            while k < Lh / 2 - 0.1:
                b = c + n_ * (sz[ax] / 2) + t_ * k; b = Vector((b.x, y, b.z)); ven = b + n_ * 0.2
                zab = any(uvnitr(b + n_ * o_ + UP * h_, i0) for o_ in (-0.2, -0.08, -0.03, 0.0, 0.03, 0.05, 0.2) for h_ in (0.5, 0.95))   # zábradlí/zeď u hrany
                navaz = any(uvnitr(b + n_ * o_ - UP * h_, i0) for o_ in (0.2, 0.5, 0.8) for h_ in (0.12, 0.3, 0.45, -0.15, -0.3))   # schody dolů i nahoru, práh, další plocha
                navaz = navaz or pres_trasu(b, n_)   # tudy vede trasa průchodu (výstup, sestup) – zábradlí by zatarasilo cestu
                # kout u zdi: zeď do 0,35 m podél hrany – štěrbina užší než postava (r 0,3), zábradlí by stálo u zdi (Míša 5. 11.)
                navaz = navaz or any(uvnitr(b + t_ * sg_ * 0.35 + UP * 0.5, i0) for sg_ in (-1, 1)) \
                    or any(uvnitr(b + n_ * o2_ + UP * h2_, i0) for o2_ in (0.1, 0.25, 0.35) for h2_ in (0.2, 0.4, 1.4)) \
                    or any(uvnitr(b + vv_ * 0.45 + UP * hh_, i0) for vv_ in (n_, -n_, t_, -t_) for hh_ in (0.5, 1.2))   # u zdi (0,45 m): zábradlí ne (Míša 5. 11.)
                if not (zab or navaz):
                    pad = all(not uvnitr(ven - UP * h_, i0) for h_ in (0.6, 0.85, 1.1)) and ven.y - ter(ven.x, ven.z) > 1.0
                    if pad:
                        volne.append([round(b.x, 2), round(b.z, 2), round(y, 2), druh]); behy.setdefault((round(y, 2), round(n_.x, 2), round(n_.z, 2), round(b.dot(n_) * 5) / 5), (Pd, y, n_, []))[3].append(b)   # jedna hrana přes více polí podlahy = jedno zábradlí
                k += 0.3
    if doplnit:   # zábradlí na volné hrany: souvislé úseky vzorků (po 0,3 m) → jedno zábradlí s přesahem 0,15 m
        for _k, (Pd, y, n_, bs) in behy.items():
            t0 = n_.cross(UP).normalized(); bs = sorted(bs, key=lambda b: b.dot(t0)); run = [bs[0]]
            for b in bs[1:] + [None]:
                if b is not None and (b - run[-1]).length < 0.45: run.append(b); continue
                t_ = (run[-1] - run[0]).normalized() if len(run) > 1 else n_.cross(UP).normalized()
                q0_ = run[0] - t_ * 0.15 - n_ * 0.06; q1_ = run[-1] + t_ * 0.15 - n_ * 0.06; q0_.y = q1_.y = 0.0   # zabradli čeká body v y = 0
                # krátký úsek (≤ 2 vzorky): prodloužit do 0,6 m, aby sloupky stály na desce (dřív 0,3 m „zábradlí ve vzduchu“ vedle hrany – kontrola_geometrie)
                if (q1_ - q0_).length < 0.6:   # krátký úsek: prodloužit podél hrany na 0,6 m, sloupky o 0,12 m dovnitř plochy (stojí na desce)
                    st_ = (q0_ + q1_) / 2; q0_ = st_ - t_ * 0.3 - n_ * 0.06; q1_ = st_ + t_ * 0.3 - n_ * 0.06
                dd_ = hz(q1_ - q0_); LL_ = dd_.length; sv_ = dd_.normalized().cross(UP) if LL_ > 1e-3 else n_
                vz_ = [q0_ + dd_ * f_ + Vector((0, y + 0.6, 0)) for f_ in (0.15, 0.5, 0.85)]
                u_zdi_ = sum(1 for q in vz_ if uvnitr(q + sv_ * 0.22) or uvnitr(q - sv_ * 0.22))
                if u_zdi_ < 3: zabradli(Pd, q0_, q1_, y)   # těsně u zdi zábradlí ne (Míša 4. 11.: „moc zábradlí v patře i u zdi“)
                if b is not None: run = [b]
        STAVBY.append({"doplnena_zabradli": len(behy)})
        return hrany_a_zabradli(parts, doplnit=False)
    u_zdi = []
    for p0, p1, y, kdo in ZABR:
        d = hz(p1 - p0); L = d.length
        if L < 0.2: continue
        d /= L; sv = d.cross(UP); n = 0; m_ = 0
        for k in _np.arange(0.15, L - 0.1, 0.3):
            q = p0 + d * k; q = Vector((q.x, y + 0.6, q.z)); m_ += 1
            if uvnitr(q + sv * 0.22) or uvnitr(q - sv * 0.22): n += 1   # 0,22: zdivo je o 1,5 cm větší (lib.PRESAH)
        if m_ and n / m_ > 0.6: u_zdi.append([round(p0.x, 2), round(p0.z, 2), round(p1.x, 2), round(p1.z, 2), round(y, 2), kdo])
    STAVBY.append({"volne_hrany": volne, "zabradli_u_zdi": u_zdi})
    print("HRANY volných hran (vzorků po 0,3 m) %d, zábradlí u zdi %d" % (len(volne), len(u_zdi)))

def zdi_za(P, body):
    """Pro každý bod: leží v kolizním kvádru některého dílu (zeď, věž)? (P.cols + uložené díly hradu)"""
    C = list(P.cols)
    if not C or not body: return [False] * len(body)
    Ri = np.array([np.array(m.to_3x3().inverted()) for m, sz in C]); T = np.array([list(m.translation) for m, sz in C])
    Hs = np.array([[sz[0] / 2, sz[1] / 2, sz[2] / 2] for m, sz in C]); out = []
    for p in body:
        q = np.einsum("nij,nj->ni", Ri, np.array(list(p))[None] - T); out.append(bool(np.all(np.abs(q) <= Hs, axis=1).any()))
    return out

def zabr_konce(U, i, t, walked, sirka=0.9):
    """Konce zábradlí úseku i: v rohu se sousedním ochozem průsečík linií zábradlí (souvislé zábradlí kolem rohu)."""
    o = t / 2 + sirka - 0.06; a, b, L, d, vn = U[i]; n = len(U)
    r0 = (roh(U, (i - 1) % n, o) - a).dot(d) if (i - 1) % n in walked else None
    r1 = (roh(U, i, o) - a).dot(d) if (i + 1) % n in walked else None
    return r0, r1

def brana_vyska(br, yf, strop):
    """Výška vrcholu podhledí brány: věnec záklenku nejvýš 0,1 m pod korunou (Míša 4. 11.: kámen trčel z ochozu)."""
    return min(br["vyska"], strop - yf - portaly.nadvyseni_vence("lomeny", br["sirka"], br["vyska"]) - 0.1)

def brana_otvor(br, s_stred, yf, strop):
    """Otvor ve zdi pro bránu (zed2 otvory): obdélník portaly.otvor – portál ho vyplní obloukem a klenbou průjezdu."""
    W, H = portaly.otvor(br["sirka"], brana_vyska(br, yf, strop), "lomeny"); return (s_stred, W, yf, H)

def portal(P, stred, nrm, w, h, yf, hloubka, kridla=True):
    """Brána ve zdi tloušťky hloubka: stred = osa na VNĚJŠÍM líci, nrm ven. Ostění s lomeným záklenkem v líci, křídla v polodrážce
    za ostěním (otevřená podél boků průjezdu), lomená valená klenba průjezdu, na vnitřním líci záklenek (portaly.py)."""
    nrm = hz(nrm).normalized(); x = UP.cross(nrm)
    m = M(stred + UP * yf, basis=Matrix((x, UP, nrm)).transposed())
    kit.doorway(P, m, kind="hlavni", w=w, h=h, depth=hloubka, top="lomeny", leaf=kridla, double=True, venec_vnitrni=True)

def dlazba(P, c, d, w, L, yf):
    P.box(M(c + UP * (yf - 0.04), basis=frame(d)), (w, 0.08, L), "kvadr_sedy")

# ------------------------------------------------------------------ věž s komorou na úrovni ochozu
OKN_CFG = None
def vez2(P, c, d, w, dp, dno, ytop, strecha="jehlan", dvere=(), tw=0.9, okna=(), strilny=()):
    """Hranolová věž: plná do výšky dno (podlaha nejnižší místnosti), nad ní duté zdivo tloušťky tw do ytop s dveřmi
    dvere = [(strana '+s'|'-s'|'+d'|'-d', posun, šířka, y_prahu)] – z ochozu (věžička) nebo z lávky (věž). Stropy, schody
    a zábradlí uvnitř staví vnitrek_veze()."""
    d = hz(d).normalized(); s = d.cross(UP).normalized()
    rohy = [c + d * (w / 2) * i + s * (dp / 2) * j for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    lo = min(ter(p.x, p.z) for p in rohy + [c]) - 2.0
    for i_, j_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)):   # nárožní kameny (Míša 9. 11.)
        R_ = c + d * (w / 2) * i_ + s * (dp / 2) * j_
        H.narozi(P, R_, (-d * i_, s * j_), (-s * j_, d * i_), ter(R_.x, R_.z) - 0.2, ytop - 0.05)
    P.box(M((c.x, (lo + dno) / 2, c.z), basis=frame(d)), (dp, dno - lo, w), "zdivo")
    steny = {"+s": (c + s * (dp / 2 - tw / 2), d, w, s), "-s": (c - s * (dp / 2 - tw / 2), d, w, -s),
             "+d": (c + d * (w / 2 - tw / 2), s, dp - 2 * tw, d), "-d": (c - d * (w / 2 - tw / 2), s, dp - 2 * tw, -d)}
    for jm, (cc, osa, L, nrm) in steny.items():
        otv = [(L / 2 + o,) + (lambda WH: (WH[0], yd, WH[1]))(portaly.otvor(dw, 2.3, "segment")) for st, o, dw, yd in dvere if st == jm]
        # okna v patrech (Míša 4. 11.: „věž nemá vůbec okna“) – skutečný otvor skrz zeď v tesaném ostění, mříž; střílny = úzký
        # otvor skrz zeď (dřív jen černý pruh na líci)
        OK_ = [(o, ow, yo, oh) for st, o, ow, yo, oh in okna if st == jm]; SL_ = [(o, yo) for st, o, yo in strilny if st == jm]
        NK = OKN_CFG or {"nika_sirka": 1.1, "nika_nad": 0.45, "slupka_m": 0.45}
        jw, lh, sh = 0.18, 0.2, 0.1
        for o, ow, yo, oh in OK_:   # zevnitř nika, na líci slupka zdi (souvislá síť, ne přiložené kvádry – švy) s otvorem pro ostění
            otv.append((L / 2 + o, NK["nika_sirka"], yo - 0.05, oh + NK["nika_nad"], NK["slupka_m"]))
            otv.append((L / 2 + o, ow + 2 * jw, yo - sh, oh + lh + sh, 0))   # 0 = otvor jen viditelně, kolize plná
        for o, yo in SL_: otv.append((L / 2 + o, 0.14, yo, 0.9))
        zed2(P, cc - osa * (L / 2), cc + osa * (L / 2), tw, ytop, -nrm, otvory=otv, cimburi=False, ext0=0, ext1=0, parapet=0,
             cela=(jm in ("+s", "-s"),) * 2)   # boční stěny ±d jsou zalícované mezi ±s – jejich čela by na nároží dělala čáru
        for st, o, dw, yd in dvere:
            if st == jm and H.DETAIL:
                f = cc + osa * o + nrm * (tw / 2)
                kit.doorway(P, M(f + UP * yd, basis=Matrix((UP.cross(nrm), UP, nrm)).transposed()), kind="obycejne", w=dw, h=2.3,
                            depth=tw, top="segment", leaf=False)
        if H.DETAIL:
            for o, ow, yo, oh in OK_:   # vnější slupka zdi s úzkým okénkem v tesaném ostění, uvnitř nika (rešerše 4. 11.)
                f = cc + osa * o + nrm * (tw / 2); sl = NK["slupka_m"]; nw = NK["nika_sirka"]; nh = oh + NK["nika_nad"]
                mw = M(f + UP * yo, basis=Matrix((UP.cross(nrm), UP, nrm)).transposed())   # slupka je součástí sítě zdi (zed2)
                kit.stone_window(P, mw, w=ow, h=oh, depth=sl, fill="mriz", jw=jw, lh=lh, sh=sh, proud=0.01)
                H.vypln_okna(P, mw, -ow / 2, ow / 2, 0.0, oh, -sl - 0.04, "blana")   # blána za mříží (Míša 9. 11.: okna nedodělaná)
                H.OKNA_SVETLA.append(f - nrm * (tw + 1.0) + UP * (yo + oh / 2))
            for o, yo in SL_:   # střílna: kamenný překlad a práh, boky otvoru = zdivo
                f = cc + osa * o + nrm * (tw / 2)
                mm_ = M(f + UP * yo, basis=Matrix((UP.cross(nrm), UP, nrm)).transposed())
                for yy_ in (-0.06, 0.96): kit.stone(P, mm_ @ M((0, yy_, -tw / 2 + 0.01)), (0.5, 0.12, tw + 0.02), "kvadr_okno", cham=0.02, rough=0.0)
    if strecha == "jehlan":
        H.strecha_jehlan(P, [(p.x, p.z) for p in rohy], ytop, max(w, dp) * 1.1, presah=0.35)
    elif strecha == "valba":
        a = c - d * (w / 2); b = c + d * (w / 2)
        H.strecha_valba(P, (a.x, a.z), (b.x, b.z), dp, ytop, dp * 0.75, presah=0.4)
    elif strecha == "sedlova":   # dlouhá budova (štít B): sedlová střecha, hřeben podél delší strany (d), kamenné štíty
        a = c - d * (w / 2); b = c + d * (w / 2)
        H.strecha_sedlova(P, (a.x, a.z), (b.x, b.z), dp, ytop, dp * 0.9, presah=0.4, stity=H.STRECHA.get("stity", "drevo"))   # štít z prken (KCD, Míša 9. 11.)
    elif strecha.startswith("pult"):   # štítová zeď / donjon (kresba GC80T08 misa_01): pultová střecha, vysoká strana = štít k příkopu
        st_ = strecha.split(":")[1] if ":" in strecha else "-s"; s3 = d.cross(UP).normalized()
        nh = {"+s": s3, "-s": -s3, "+d": d, "-d": -d}[st_]; uu = d if st_ in ("+s", "-s") else s3
        ext = dp if st_ in ("+s", "-s") else w; wu = w if st_ in ("+s", "-s") else dp
        hh = ext * PULT_SKLON
        P.box(M(c + nh * (ext / 2 - tw / 2) + UP * (ytop + hh / 2), basis=frame(uu)), (tw, hh, wu), "zdivo")   # štít nad korunou
        for sg in (-1, 1):   # boční trojúhelníky (zeď stoupá se střechou)
            b0 = c + uu * (sg * (wu / 2 - tw / 2))
            pts = [b0 - nh * (ext / 2) + UP * ytop, b0 + nh * (ext / 2 - tw) + UP * ytop, b0 + nh * (ext / 2 - tw) + UP * (ytop + hh)]
            P.prism([q - uu * (tw / 2) for q in pts], uu * tw, "zdivo")
        ov = 0.45
        eL = c - nh * (ext / 2 + ov) - uu * (wu / 2 + 0.2) + UP * (ytop - ov * PULT_SKLON); eR = eL + uu * (wu + 0.4)
        rL = c + nh * (ext / 2 - tw) - uu * (wu / 2 + 0.2) + UP * (ytop + hh - 0.05); rR = rL + uu * (wu + 0.4)
        lib.shingle_roof(P, eL, eR, rR, rL, ridge=False)
    return rohy
PULT_SKLON = 0.62   # tg sklonu pultové střechy štítové zdi (kresba misa_01: ~32°)

def zabradli(P, p0, p1, y):
    """Dřevěné zábradlí se sloupky a kolizí (otvory v podlahách)."""
    d = hz(p1 - p0); L = d.length
    if L < 0.1: return
    import sys as _s; ZABR.append((p0.copy(), p1.copy(), y, "%s:%d" % (_s._getframe(1).f_code.co_name, _s._getframe(1).f_lineno)))
    if os.environ.get("PUCHART_DBGZ"):
        _q = [float(x) for x in os.environ["PUCHART_DBGZ"].split(",")]
        if min((Vector((_q[0], 0, _q[1])) - hz(p_)).length for p_ in (p0, p1, (p0 + p1) / 2)) < 1.5: print("DBGZ", [round(v, 2) for v in (p0.x, p0.z, p1.x, p1.z, y)], ZABR[-1][3], _s._getframe(2).f_code.co_name, _s._getframe(2).f_lineno, flush=True)
    s_ = d.normalized().cross(UP).normalized()
    P.beam(p0 + UP * (y + 1.0), p1 + UP * (y + 1.0), 0.15, 0.1, "dub", j=0.2, ext=0.1, collide=None)                         # madlo na hlavách sloupků (čep), přesah přes krajní
    P.beam(p0 + s_ * 0.09 + UP * (y + 0.5), p1 + s_ * 0.09 + UP * (y + 0.5), 0.06, 0.08, "dub", j=0.2, ext=0.08, collide=None)   # střední tyč přiložená z líce sloupků (0,05 + 0,03 + vůle)
    n = max(1, round(L / 1.2))
    for i in range(n + 1):
        q = p0.lerp(p1, i / n); P.beam(q + UP * (y - 0.02), q + UP * (y + 1.0), 0.1, 0.1, "dub", up=d, j=0.4)
    kol(P, (p0 + p1) / 2 + UP * (y + 0.55), d, (0.1, 1.1, L))

def podlaha(P, c, d, iw, idp, y, otvory=(), tl=0.24, mat="prkna_ven"):
    """Trámový strop/podlaha ve věži (lokálně u podél d, v podél s, střed c) s otvory [(u0, u1, v0, v1)] pro schody."""
    d = hz(d).normalized(); s = d.cross(UP).normalized()
    us = sorted({-iw / 2, iw / 2} | {x for o in otvory for x in o[:2]}); vs = sorted({-idp / 2, idp / 2} | {x for o in otvory for x in o[2:]})
    for u0, u1 in zip(us, us[1:]):
        for v0, v1 in zip(vs, vs[1:]):
            um, vm = (u0 + u1) / 2, (v0 + v1) / 2
            if u1 - u0 < 0.02 or v1 - v0 < 0.02 or any(o[0] <= um <= o[1] and o[2] <= vm <= o[3] for o in otvory): continue
            q = c + d * um + s * vm
            P.box(M(q + UP * (y - 0.04), basis=frame(d)), (v1 - v0, 0.08, u1 - u0), mat)
            P.box(M(q + UP * (y - 0.08 - (tl - 0.08) / 2), basis=frame(d)), (v1 - v0, tl - 0.08, u1 - u0), "dub")
            kol(P, q + UP * (y - tl / 2), d, (v1 - v0, tl, u1 - u0)); POCH.append((P.cols[-1], y, "podlaha", P))

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
def most2(P, a, ya, b, yb, w, Lp, na_terenu=True):
    """Dřevěný most na kozách od nástupu a (terén srovnaný na ya) na práh brány b (yb): mostovka souvislá, kolize jedna
    šikmá deska zapuštěná na začátku do terénu (žádný schod), u brány padací most na řetězech."""
    d = hz(b - a); L = d.length; d /= L; s = d.cross(UP).normalized()
    if na_terenu: NASTUPY.append([round(a.x, 2), round(a.z, 2), round(ya, 2), round(-d.x, 3), round(-d.z, 3)])   # ne z podlahy branky
    sk = math.atan2(yb - ya, L); tg = (yb - ya) / L
    g0_ = min(ter(*(a - d * k_).xz) for k_ in (0.3, 0.9, 1.5))   # nájezd z terénu na začátek mostu (hlídač 5. 11.: hrana 0,26–0,5 m zastavila postavu)
    if ya - g0_ > 0.03:
        nabeh(P, a, -d, ya, w, L=max(0.6, round((ya - g0_ + 0.1) / 0.17) * 0.32), spad=ya - g0_ + 0.1)   # zbytek výšky: kolizní rampa (násyp dělá terén – cesty.py, nastupy_mostu.json)
    y = lambda t: ya + tg * t
    t0 = 0.0   # kolize od začátku viditelné mostovky (terén srovnaný na ya); s −1 m vyčuhovala před mostem 0,2 m nad terén (povrch_kolize)
    c = a + d * ((t0 + L) / 2) + UP * (y((t0 + L) / 2) - 0.15 / math.cos(sk))
    kol(P, c, d, (w, 0.3, (L - t0) / math.cos(sk)), sk)
    Lf = L - Lp
    # začátek mostovky na kamenném prahu (tablet 3. 11.: prkna končila zubatě v terénu): prkna od místa, kde je mostovka
    # celou šířkou nad terénem; před tím kamenný práh s vrchem v rovině mostovky, zapuštěný do terénu
    t_op = 0.0
    while t_op < Lf / 3 and y(t_op) - max(ter(*(a + d * t_op + s * o).xz) for o in (-w / 2 - 0.1, 0, w / 2 + 0.1)) < 0.08: t_op += 0.1
    # práh: dubový trám napříč na zemi pod začátkem prken (Míša 4. 11.: kamenná deska ležela samostatně v trávě před mostem)
    q_ = a + d * (t_op + 0.12); gq_ = min(ter(*(q_ + s * o).xz) for o in (-w / 2, 0, w / 2))
    hp_ = max(0.25, y(t_op) - 0.07 - gq_ + 0.15)   # pod prkny až do země (podélné trámy na něm leží), bez vlastní kolize (chodí se po mostovce)
    P.box(M(q_ + UP * (y(t_op) - 0.07 - hp_ / 2), basis=frame(d)), (w + 0.5, hp_, 0.3), "dub", collide=None)
    # prkna jako Havran (_deck → kit.deck): každé jiné, mezery, hřeby nad trámy, vyšlapaná stopa
    kit.deck(P, a + d * t_op + UP * (y(t_op) - 0.065), a + d * Lf + UP * (y(Lf) - 0.065), w / 2 - 0.05, "prkna_ven", worn=1.0,
             beams=(-w / 2 + 0.25, 0.0, w / 2 - 0.25))
    for o in (-w / 2 + 0.25, 0.0, w / 2 - 0.25):   # podélné trámy
        P.beam(a + s * o + UP * (ya - 0.22), a + d * Lf + s * o + UP * (y(Lf) - 0.22), 0.26, 0.3, "dub")
    # kozy (Míša 2. 11.: most „není po zem“ – pod 0,7 m výšky koza neměla sloupy a příčný trám visel): každá koza = dva
    # sloupy na kamenných patkách až k terénu, příčný trám pod podélnými trámy, od 1,2 m křížové ztužení napříč a
    # vzpěry podél; na obou koncích kamenná opěra (mostovka nikde nekončí ve vzduchu). Rozteč z hrad_puchart.json most.
    MO = A["most"]; rozt = MO.get("rozestup_koz_m", 3.5); KOZY_T = []
    n = max(2, int(round(Lf / rozt)))
    for i in range(1, n + 1):   # i koza na konci pevné části (nese padací most – bez ní visel, kontrola_geometrie 3. 11.)
        tm = Lf * i / n; p = a + d * tm; yy = y(tm)
        if yy - max(ter(*(p + s * o).xz) for o in (-w / 2, 0, w / 2)) < MO.get("koza_od_m", 0.9): continue   # mostovka u země / v zářezu: bez kozy (patky trčely nad mostovkou – tablet 3. 11.)
        P.beam(p - s * (w / 2 + 0.2) + UP * (yy - 0.49), p + s * (w / 2 + 0.2) + UP * (yy - 0.49), 0.28, 0.24, "dub")   # příčník: leží na hlavách sloupů, podélníky na něm (docs/reference/tesarske_spoje.md)
        KOZY_T.append(tm)
        STAVBY.append({"koza": [round(p.x, 2), round(p.z, 2)], "mostovka_y": round(yy, 2), "patka_vrch_y": round(max(ter(*(p + s * o).xz) for o in (-w / 2 + 0.25, w / 2 - 0.25)) + 0.3, 2)})
        gs = []
        for o in (-w / 2 + 0.25, w / 2 - 0.25):   # sloup přesně pod krajním podélným trámem (dřív o 10 cm vedle – pásky končily vedle trámu)
            q = p + s * o; g = ter(q.x, q.z); gs.append(g)
            P.box(M(q + UP * (g + 0.05), basis=frame(d)), (0.6, 0.5, 0.6), "kvadr_sedy")      # patka (do terénu 0,2 m)
            P.beam(q + UP * (g + 0.28), q + UP * (yy - 0.49), 0.28, 0.28, "dub", up=d, j=0.4)   # čep do příčníku
            if yy - g > 1.6:   # pásky ze sloupu pod podélník (čep do sloupu, čep do podélníku), pod příčníkem volně (dřív končily v něm)
                pd_ = yy - 1.16; dx = (yy - 0.22) - pd_
                for sm in (-1, 1):
                    P.beam(q + d * (sm * 0.07) + UP * pd_, q + d * (sm * dx) + UP * (y(tm + sm * dx) - 0.22), 0.16, 0.16, "dub", j=0.4)   # každý pásek vlastní dlab
        g = max(gs)
        if yy - g > 1.2:   # křížové ztužení napříč
            od_ = 0.28 / 2 + 0.14 / 2 + 0.005   # ztužení přiložené z líce a z rubu sloupů (tesařsky), ne skrz sloupy; v kříži se neprostupují
            vrch = yy - 1.3 if yy - g > 1.6 else yy - 0.75   # pod dlaby pásků (pásky jdou podél mostu skrz rovinu ztužení)
            P.beam(p - s * (w / 2 - 0.25) + d * od_ + UP * (g + 0.5), p + s * (w / 2 - 0.25) + d * od_ + UP * vrch, 0.14, 0.14, "dub")
            P.beam(p + s * (w / 2 - 0.25) - d * od_ + UP * (g + 0.5), p - s * (w / 2 - 0.25) - d * od_ + UP * vrch, 0.14, 0.14, "dub")
    # opěry na koncích pevné části: kamenný blok od terénu pod podélné trámy
    for tm in (0.0, Lf):
        p = a + d * tm; yy = y(tm); g = min(ter(*(p + s * o).xz) for o in (-w / 2, 0, w / 2)) - 0.3
        if yy - 0.37 - g > 0.1 and yy - max(ter(*(p + s * o).xz) for o in (-w / 2, 0, w / 2)) > -0.05:   # opěra jen pod mostovkou, ne nad ní
            vys_ = yy - 0.37 - g
            if tm > 0 and vys_ > 2.0:   # pilíř před padacím mostem (Míša 9. 11.: „kamenná zeď“ jako deska; rozhodnutí: zděný pilíř vyrostlý ze skály)
                # zdivo hradu, dřík 2,2 m podél mostu, dole sokl širší o 0,5 m na každou stranu do třetiny výšky, pata 1 m ve skále;
                # nárožní kameny na rozích dříku (detaily_hradu_1393.md: most na zděných pilířích, Helfštýn)
                g0_ = g - 0.7; ys_ = g0_ + (yy - 0.37 - g0_) * 0.33; wp_ = w + 0.8; dp_ = 2.2
                P.box(M(p + UP * ((g0_ + ys_) / 2), basis=frame(d)), (wp_ + 1.0, ys_ - g0_, dp_ + 1.0), "zdivo")
                P.box(M(p + UP * ((ys_ - 0.05 + yy - 0.37) / 2), basis=frame(d)), (wp_, yy - 0.37 - ys_ + 0.05, dp_), "zdivo")
                kol(P, p + UP * ((g0_ + yy - 0.37) / 2), d, (wp_, yy - 0.37 - g0_, dp_))
                for i_ in (-1, 1):
                    for j_ in (-1, 1):
                        R_ = p + d * (i_ * dp_ / 2) + s * (j_ * wp_ / 2)
                        H.narozi(P, R_, (-d * i_, s * j_), (-s * j_, d * i_), max(ys_, ter(R_.x, R_.z) - 0.2), yy - 0.4)   # na svahu od terénu (pod_terenem 9. 11.)
            else:
                P.box(M(p + UP * ((g + yy - 0.37) / 2), basis=frame(d)), (w + 0.6, vys_, 1.0), "kvadr")
    # zábradlí: sloupky čepem do konců příčníků koz; mezi kozami krátké příčníky (pražce) pod podélníky; madlo na hlavách
    # sloupků, střední tyč z vnějšího líce (dřív sloupky stály vedle mostovky ve vzduchu a madla jimi procházela)
    ts = sorted(set([0.0, Lf] + KOZY_T)); sl = []
    for t0_, t1_ in zip(ts, ts[1:]):
        k = max(1, math.ceil((t1_ - t0_) / 1.8)); sl += [t0_ + (t1_ - t0_) * i / k for i in range(k)]
    sl.append(Lf)
    zem_ = lambda tm: max(ter(*(a + d * tm + s * o).xz) for o in (-w / 2 - 0.2, 0, w / 2 + 0.2))
    v_zemi = [tm for tm in sl if not (any(abs(tm - kt) < 0.05 for kt in KOZY_T) or y(tm) - 0.57 > zem_(tm) + 0.05)]   # u nástupu: sloupek zapuštěný do země
    sl = [tm for tm in sl if tm not in v_zemi]   # sloupek s pražcem jen nad terénem (pražec v zemi = kus pod terénem, hlídač 3. 11.)
    for tm in sl:
        if not any(abs(tm - kt) < 0.05 for kt in KOZY_T):
            P.beam(a + d * tm - s * (w / 2 + 0.2) + UP * (y(tm) - 0.47), a + d * tm + s * (w / 2 + 0.2) + UP * (y(tm) - 0.47), 0.2, 0.2, "dub", j=0.3)
    for sg in (-1, 1):
        o = s * sg * (w / 2 + 0.1)
        P.beam(a + o + UP * (ya + 1.05), a + d * Lf + o + UP * (y(Lf) + 1.05), 0.14, 0.12, "dub", j=0.5, ext=0.1, collide=None)
        P.beam(a + o + s * sg * 0.105 + UP * (ya + 0.55), a + d * Lf + o + s * sg * 0.105 + UP * (y(Lf) + 0.55), 0.08, 0.1, "dub", j=0.5, ext=0.1, collide=None)
        for tm in sl:
            q = a + d * tm + o
            P.beam(q + UP * (y(tm) - 0.48), q + UP * (y(tm) + 1.05), 0.13, 0.13, "dub", up=d, j=0.6, collide=None)   # kolizi kryje kol() zábradlí (vlastní kolize sloupku s rozhozem = neviditelná stěna, povrch_kolize 5. 11.)
        for tm in v_zemi[:1] + [t_ for t_ in v_zemi[1:] if t_ - v_zemi[0] > 1.0]:   # koncový sloupek u nástupu (Míša 4. 11.: „chybí sloupky zábradlí“ – madlo končilo ve vzduchu)
            q = a + d * max(tm, 0.06) + o
            P.beam(q + UP * (ter(q.x, q.z) - 0.3), q + UP * (y(tm) + 1.05), 0.13, 0.13, "dub", up=d, j=0.6, collide=None)
        kol(P, a + d * (Lf / 2) + o + UP * (y(Lf / 2) + 0.6), d, (0.14, 1.2, Lf / math.cos(sk)), sk)   # jen pevná část se zábradlím (dřív celá délka – přes padací most až ke skále: neviditelná stěna, test skala_540)
    # padací most: osa otáčení na prahu, vede od brány
    bb = a + d * L
    if H.DETAIL:
        mb = M(bb + UP * yb, basis=Matrix((s, UP, -d)).transposed())
        oka = kit.drawbridge(P, mb, w=w - 0.2, L=Lp, angle=math.degrees(sk))   # konec dolů k pevné části (rotace kolem X kladná = dolů)
        for q in oka:
            kit.chain(P, q, bb + UP * (yb + 4.0) + (q - (bb + UP * yb)).project(s) + d * 0.1, sag=0.15)
    else:
        P.box(M(bb - d * (Lp / 2) + UP * (yb - Lp / 2 * tg), basis=frame(d) @ Matrix.Rotation(-sk, 3, "X")), (w, 0.2, Lp), "prkna_ven")

def nabeh(P, prah, ven, y, w, L=1.8, spad=0.7, hlina=False):
    """Kolizní nájezd z terénu na práh brány: šikmá deska od prahu ven, zapuštěná do terénu.
    hlina=True (nástup mostu, Míša 6. 11.: „dodělej tam hlínu a desky“): hliněný násyp se svahy do stran a dřevěná opěra
    z fošen mezi kulatinami u začátku mostovky (jako mosty údolní cesty, Havran kraj.py) místo kamenných stupňů."""
    ven = hz(ven).normalized(); sk = math.atan2(spad, L)
    import sys as _s; NABEHY.append([round(prah.x, 2), round(prah.z, 2), round(y, 2), round(spad, 2), round(L, 2), "%s:%d" % (_s._getframe(1).f_code.co_name, _s._getframe(1).f_lineno)])
    kol(P, prah + ven * (L / 2) + UP * (y - spad / 2 - 0.1), -ven, (w, 0.2, L / math.cos(sk) + 0.1), sk)
    if hlina:
        s_ = ven.cross(UP).normalized(); hw = w / 2 + 0.25; n_ = 6; vs = []; fs = []
        for k in range(n_ + 1):   # násyp: vrch = rampa, boky svahem 1:1,5 do terénu (0,3 m pod něj)
            c = prah + ven * (L * k / n_ + 0.02); yt = y - 0.06 - spad * k / n_
            for sg in (-1, 1):
                q = c + s_ * (sg * hw); g = ter(q.x, q.z); hgt = max(0.0, yt - g)
                qb = c + s_ * (sg * (hw + hgt * 1.5 + 0.2)); vs += [(q.x, yt, q.z), (qb.x, ter(qb.x, qb.z) - 0.3, qb.z)]
        for k in range(n_):
            a0 = 4 * k; a1 = 4 * (k + 1)   # pořadí: [L_top, L_bot, R_top, R_bot]
            fs += [(a0, a0 + 2, a1 + 2, a1), (a0 + 1, a0, a1, a1 + 1), (a0 + 2, a0 + 3, a1 + 3, a1 + 2)]
        P.mesh(vs, fs, "hlina")
        g0 = min(ter(*(prah + s_ * o_).xz) for o_ in (-hw, 0, hw))
        for o_ in (-hw - 0.1, hw + 0.1):   # kulatiny opěry zatlučené do země
            q = prah + s_ * o_ - ven * 0.12
            P.beam(q + UP * (g0 - 0.8), q + UP * (y - 0.08), 0.22, 0.22, "dub", up=ven, j=0.4, collide=None)
        for yy_ in np.arange(max(g0 - 0.05, y - 2.5), y - 0.2, 0.26):   # fošny držící hlínu (líc k průrvě)
            P.beam(prah - s_ * (hw + 0.2) - ven * 0.02 + UP * yy_, prah + s_ * (hw + 0.2) - ven * 0.02 + UP * yy_, 0.06, 0.24, "prkna_ven", up=ven, j=0.3, collide=None)
        return
    # viditelné kamenné stupně pod rampou (test pruchod:povrch_kolize: rampa byla jen kolize – postava stála 0,64 m nad terénem);
    # vrch stupně = rampa uprostřed stupně, hrany do ±spad/2n; stupně bez vlastní kolize (chodí se po rampě), zapuštěné do terénu
    n = max(1, round(spad / 0.17)); hl = L / n
    for k in range(n):
        top = y - (k + 0.5) * spad / n; c = prah + ven * (hl * (k + 0.5)); g = min(ter(*(c + ven * a).xz) for a in (-hl / 2, hl / 2)) - 0.25
        if top - g < 0.05: continue
        P.box(M(c + UP * ((top + g) / 2), basis=frame(ven)), (w, top - g, hl + 0.02), "kvadr_sedy", collide=None)

def plosina(P, c, d, delka, sirka, y, sloupy=True):
    d = hz(d).normalized(); s = d.cross(UP).normalized()
    kit.deck(P, c - d * (delka / 2) + UP * (y - 0.06), c + d * (delka / 2) + UP * (y - 0.06), sirka / 2 - 0.05, "prkna_ven", worn=0.8,
             beams=(-sirka / 2 + 0.12, sirka / 2 - 0.12), plank_w=(0.22, 0.3), t=0.06)   # Havran wall_stair.platform: prkna, ne deska
    kol(P, c + UP * (y - 0.1), d, (sirka, 0.2, delka)); POCH.append((P.cols[-1], y, "plosina", P))
    for o in (-delka / 2 + 0.1, delka / 2 - 0.1):
        P.beam(c + d * o - s * sirka / 2 + UP * (y - 0.18), c + d * o + s * sirka / 2 + UP * (y - 0.18), 0.18, 0.2, "dub")
    if sloupy:
        for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q = c + d * (i * (delka / 2 - 0.12)) + s * (j * (sirka / 2 - 0.12))
            P.beam(q + UP * (ter(q.x, q.z) - 0.2), q + UP * (y - 0.18), 0.16, 0.16, "dub", up=d, j=0.5)   # čep do trámu podesty

BUDOVY = []   # půdorysy budov (stavby_vegetace: bez trávy uvnitř – Míša 4. 11.: tráva prorůstala podlahou)
SCHODY = []   # ramena (a, d, y0, y1, délka, šířka, kamenné) – hlídač nástupu a výstupu
STUPNE = []   # konce stupňů (hlídač schody × zdivo, build/stupne.json)
def volno_u_zdi(P, c, s, hw, krok=0.02):
    """Volný úsek <u0, u1> (u podél s, |u| <= hw) kolem bodu c mimo zdivo (kolizní kvádry vyšší než 1,5 m – zdi, věže,
    pilíře; ne podlahy): stupně schodiště nekončí ve zdi, ale 1 cm před jejím lícem."""
    C = [(m, sz) for m, sz in P.cols if sz[1] > 1.5 and (m.translation - c).length < 0.87 * (sz[0] + sz[1] + sz[2]) / 2 + hw + 0.1]
    if not C: return -hw, hw
    us = np.arange(-hw, hw + 1e-6, krok)
    vol = [not any(_v_kvadru(m, sz, c + s * u) for m, sz in C) for u in us]
    if all(vol): return -hw, hw
    i0 = int(np.argmin(np.abs(us)))
    if not vol[i0]: return -hw, hw   # střed ve zdi – nechat (hlídač to nahlásí)
    lo = i0; hi = i0
    while lo > 0 and vol[lo - 1]: lo -= 1
    while hi < len(us) - 1 and vol[hi + 1]: hi += 1
    return max(-hw, us[lo] - (0.0 if lo == 0 else 0.01 - krok)), min(hw, us[hi] + (0.0 if hi == len(us) - 1 else krok - 0.01))
def _v_kvadru(m, sz, p):
    q = m.inverted() @ p
    return abs(q.x) <= sz[0] / 2 and abs(q.y) <= sz[1] / 2 and abs(q.z) <= sz[2] / 2

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
        else:   # Havran stairs: stupeň ze dvou ošlapaných prken (kit.plank), ne holý kvádr
            base = a + UP * (y0 + h * (k + 1) - 0.055)
            for a0, a1 in ((0.0, 0.52), (0.5, 1.0)):
                c0 = base + d * (r * k + (r + 0.05) * a0); c1 = base + d * (r * k + (r + 0.05) * a1); cm = (c0 + c1) / 2
                u0_, u1_ = volno_u_zdi(P, cm + UP * 0.03, s, w / 2)   # stupeň končí 1 cm před lícem zdi (Míša 4. 11.: „schody zapuštěné ve stěně“)
                kit.plank(P, cm + s * (u0_ - (kit.J(0.02) if u0_ <= -w / 2 + 1e-3 else 0.0)), cm + s * (u1_ + (kit.J(0.02) if u1_ >= w / 2 - 1e-3 else 0.0)),
                          (c1 - c0).length - 0.008, 0.05, "prkna_ven", up=(0, 1, 0), wear=0.7, seg_len=0.3)
                STUPNE.append((cm + s * u0_, cm + s * u1_))
    if not kamenne:   # dvě šikmé schodnice (Havran); podpěry jen pod podestami – sloupky v půli ramene byly „mrda podpěr“ (tablet 3. 11.)
        for o in (-w / 2 + 0.06, w / 2 - 0.06):
            P.beam(a + s * o + UP * (y0 - 0.12), a + d * run + s * o + UP * (y1 - 0.12), 0.08, 0.24, "dub", j=0.5)
        if run > 4.6:   # dlouhé rameno: jedna kozlíková podpěra uprostřed (sloupy pod schodnicemi + příčník)
            q = a + d * (run / 2); yq = y0 + (y1 - y0) / 2 - 0.24 - 0.07 * math.tan(sk) - 0.08   # příčník: schodnice na něm leží (osedlání), sloupky čepem do něj
            if yq - zem(q.x, q.z) > 0.8:
                for o in (-w / 2 + 0.06, w / 2 - 0.06):
                    qq = q + s * o; P.beam(qq + UP * (zem(qq.x, qq.z) - 0.05), qq + UP * yq, 0.16, 0.16, "dub", up=d, j=0.4)
                P.beam(q - s * (w / 2 + 0.05) + UP * yq, q + s * (w / 2 + 0.05) + UP * yq, 0.14, 0.16, "dub", j=0.4)
    SCHODY.append((a.copy(), d.copy(), y0, y1, run, w, kamenne))
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
    for sg in zabradli:   # sloupky přiložené z vnějšího líce schodnice (plát s kolíkem), madlo na jejich hlavách
        o = s * sg * (w / 2 + 0.02)
        P.beam(a + o + UP * (y0 + 1.0), a + d * run + o + UP * (y1 + 1.0), 0.12, 0.1, "dub", j=0.4, ext=0.1, collide=None)
        for i in range(max(2, int(run / 1.3)) + 1):
            tt = i / max(2, int(run / 1.3)); q = a + d * (run * tt) + o
            P.beam(q + UP * (y0 + (y1 - y0) * tt - 0.34), q + UP * (y0 + (y1 - y0) * tt + 1.0), 0.1, 0.1, "dub", up=d, j=0.5)
        nk = max(1, math.ceil(run / 0.5))   # kolize po svislých dílech 0,5 m podél sklonu: celá délka jako viditelné zábradlí, nic nepřečnívá patu
        for i in range(nk):                  # (šikmý kvádr musel být o 1,5 m kratší – konce zábradlí byly bez kolize, povrch_kolize 3. 11.)
            t0_, t1_ = run * i / nk, run * (i + 1) / nk; yl = y0 + (y1 - y0) * t0_ / run; yh = y0 + (y1 - y0) * t1_ / run
            kol(P, a + d * ((t0_ + t1_) / 2) + s * sg * (w / 2 + 0.05) + UP * ((yl + yh) / 2 + 0.55), d, (0.12, 1.1 + (yh - yl), t1_ - t0_))   # kolize na původní linii (o 3 cm dovnitř zúžila průchod v paláci)
    return a + d * run, y1


def podkrovi_vystup(P, c, d, L_in, H_out, t_zdi, y0, y1, pomer, kon=-1, sirka=1.0, smer=1, u_steny=None):
    """Přístupné podkroví pod sedlovou střechou (Míša 5. 11.: „nesmysl nemít podkroví přístupné“): strmé schody (≈41°)
    podél štítové zdi (konec kon=±1 osy d) napříč budovou, výstup uprostřed pod hřebenem; podlaha podkroví s otvorem,
    zábradlí kolem otvoru, bedněné kolenní stěny u okapů. Vrací body trasy testu (od paty schodů do středu podkroví)."""
    d = hz(d).normalized(); s = d.cross(UP).normalized() * smer; vl = H_out / 2 - t_zdi   # smer: od které dlouhé stěny schody vycházejí
    n = max(1, round((y1 - y0) / 0.195)); r_ = 0.22; run = n * r_
    v_s = -vl + 1.0; v_e = v_s + run
    if u_steny is None: u_steny = kon * L_in / 2   # stěna, u které schody stojí (štít, nebo příčka)
    u_g = u_steny - kon * (0.05 + sirka / 2)
    a = c + d * u_g + s * v_s
    schody2(P, a, s, y0, y1, sirka, zabradli=(), podklad=y0, r=r_, vyska_st=(y1 - y0) / n)
    o = (u_g - sirka / 2 - 0.05, u_g + sirka / 2 + 0.05) + ((v_s - 0.1, v_e + 0.1) if smer > 0 else (-v_e - 0.1, -v_s + 0.1))
    podlaha(P, c, d, L_in, 2 * vl, y1, [o])
    ui = u_g - kon * (sirka / 2 + 0.06)   # volná strana otvoru (k vnitřku budovy)
    zabradli(P, c + d * ui + s * (v_s - 0.1), c + d * ui + s * (v_e - 1.1), y1)
    zabradli(P, c + d * u_steny + s * (v_s - 0.1), c + d * ui + s * (v_s - 0.1), y1)
    kolenni_steny(P, c, d, L_in, H_out, y1, pomer)
    return [(c + d * (ui - kon * 0.9) + s * (v_s - 0.6), y0), (a - s * 0.5, y0), (a + s * 0.8, None), (c + d * u_g + s * (v_e + 0.4), y1), (c + d * (ui - kon * 0.9) + s * (v_e + 0.4), y1), (c + d * (ui - kon * 0.9) + s * 0.0, y1)]   # od výstupu nejdřív vedle otvoru, pak do středu (ne přes zábradlí)

def kolenni_steny(P, c, d, delka, hloubka, y, pomer, vyska=1.75):
    """Podkroví pod sedlovou střechou (Míša 5. 11.: „přístupné aspoň středem, nebo ho zbedni“): bedněné kolenní stěny
    v místě, kde střecha klesne pod výšku postavy – nízký okraj u okapu je za nimi (s kolizí), střed volný."""
    d = hz(d).normalized(); s = d.cross(UP).normalized()
    k_ = 2.0 * pomer   # sklon střechy: výška = pomer · hloubka na polovinu hloubky (hloubka = vnější, okap na líci zdi)
    off = hloubka / 2 - vyska / k_ - 0.1
    if off <= 0.4: return False
    for sg in (-1, 1):
        q = c + s * (sg * off) + UP * (y + vyska / 2)
        P.box(M(q, basis=frame(d)), (0.05, vyska, delka - 0.2), "prkna_ven", collide=True)
    return True

def budova_k(P, a, b, hloubka, hk, hd, typ, podl=None, otvory=(), vstup=None, plna_kolize=True, k_bodu=None, vnitrek=None, patro_y=None, patra=None, patro2_y=None, podkrovi=True):
    """Budova stavebnice. k_bodu (nádvoří) = budova je průchozí (3. 11., Míša: vstupy do ostatních budov chybí): dveře
    uprostřed strany k nádvoří (nebo vstup z dat), podlaha uvnitř, kolize stěn s mezerou dveří, náběh z terénu, světlo
    a vybavení podle vnitrek; jinak plná kolize půdorysu (starší chování). podl zadaná = pod budovou je sklep."""
    A_, B_ = V(a), V(b); d_ = (B_ - A_).normalized(); s_ = d_.cross(UP).normalized()
    BUDOVY.append([[round(q.x, 2), round(q.z, 2)] for q in (A_ - s_ * hloubka / 2, B_ - s_ * hloubka / 2, B_ + s_ * hloubka / 2, A_ + s_ * hloubka / 2)])
    if k_bodu is not None:
        A_, B_ = V(a), V(b); d = (B_ - A_).normalized(); s = d.cross(UP).normalized(); L = (B_ - A_).length
        sg = 1 if (V(k_bodu) - (A_ + B_) / 2).dot(s) > 0 else -1
        strana = 0 if sg > 0 else 2
        vs = vstup or (strana, L / 2, 1.2, 2.3)
        if patro_y and typ == "palac":   # schody do patra podél stěny na straně k nádvoří (vnitrek_veze stena 0/2): okna za nimi ne (Míša 5. 11.)
            cS = (A_ + B_) / 2; vS = hloubka / 2
            rh_ = [A_ + s * hloubka / 2, A_ - s * hloubka / 2, B_ + s * hloubka / 2, B_ - s * hloubka / 2]
            p0_ = podl if podl is not None else H.ter_rozsah([(q.x, q.z) for q in rh_])[1] + 0.3   # jako H.budova
            H.BEZ_OKEN[:] = [(cS - d * (L / 2) - s * sg * vS, cS + d * (L / 2) - s * sg * vS, p0_, p0_ + patro_y),        # rameno 1 u stěny −sg
                             (cS - d * (L / 2) + s * sg * vS, cS + d * (L / 2) + s * sg * vS, p0_ + patro_y, p0_ + (patro2_y or hk))]  # rameno 2 u stěny +sg
        podl = H.budova(P, a, b, hloubka, hk, hd, "sedlova", typ, podl=podl, otvory=otvory, vstup=vs, patra_rel=(([0.0, patro_y] + ([patro2_y] if patro2_y else [])) if patro_y else None))
        t = 1.1 if typ == "palac" else 0.5; hi_ = (hk + hd) if typ == "palac" else 0.6 + (hd if hd > 0 else hk)
        c = (A_ + B_) / 2; wi = hloubka - (t if typ == "palac" else 0.4); li = L - (t if typ == "palac" else 0.4)
        P.box(M(c + UP * (podl - 0.06), basis=frame(d)), (wi, 0.12, li), "kvadr_sedy" if typ == "palac" else "prkna_ven")   # podlaha
        kol(P, c + UP * (podl - 0.15), d, (wi, 0.3, li))   # jako viditelná podlaha (celý půdorys přesahoval vnější líc zdí o 0,55 m – neviditelná římsa, test povrch_kolize)
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
            Ln = max(0.4, round((podl - g) / 0.17) * 0.32); sk_ = math.atan2(podl - g, Ln)   # krátké stupně u prahu (Míša 4. 11.: „malý schodek nebo dva jako v realitě“, ne rampa ze stupňů)
            top = dvere + nn * (tz - 0.05); foot = top + nn * Ln   # v podlaze ve vnějším líci zdi (dál je zeď pod prahem v úrovni podlahy)
            mid = (top + foot) / 2 + UP * ((podl + g) / 2 - 0.12)
            bas = frame(hz(-nn)) @ Matrix.Rotation(-sk_, 3, "X")
            kol(P, mid, -nn, (vs[2] + 0.4, 0.24, Ln / math.cos(sk_) + 0.1), sk_)   # chůze po rampě (bez zadrhnutí na hraně)
            # viditelně kamenné stupně 17/30 cm (Míša 4. 11.: „vjezd pro vozíčkáře? středověk neměl bezbariérové vstupy“)
            n_ = max(1, round((podl - g) / 0.17)); hs_ = (podl - g) / n_; rs_ = Ln / n_   # stupně po celé délce rampy, vrch = rampa uprostřed stupně (±půl stupně)
            for k_ in range(n_):
                yt_ = podl - hs_ * (k_ + 0.5); q_ = top + nn * (rs_ * (k_ + 0.5) + 0.05); gq_ = min(ter(*(q_ + nn * a_).xz) for a_ in (-rs_ / 2, rs_ / 2)) - 0.25
                P.box(M(q_ + UP * ((yt_ + gq_) / 2), basis=frame(hz(nn))), (vs[2] + 0.4 - k_ * 0.04, yt_ - gq_, rs_ + 0.01), "kvadr_schod", collide=None)
        svetlo(c + UP * (podl + 2.0), 1.0, 6.0)
        jm_b = "budova_%s_%d_%d" % (typ, round(c.x), round(c.z))
        TR[jm_b] = [bod(dvere + nn * (tz + 3.0)), bod(dvere + nn * (tz + 0.6)), bod(dvere - nn * 0.6, podl), bod(c, podl)]
        if typ == "palac" and patro_y:   # palác: schody do patra podél stěny naproti dveřím, otvor se zábradlím
            # tři podlaží: přízemí → patro → hrázděné patro (Míša 5. 11.: „nechybí tam ještě jedny schody, budova je vyšší“ –
            # do hrázděného patra se nedalo dojít); ramena střídavě u protilehlých dlouhých stěn
            pkv_ = None
            if podkrovi and not patro2_y:   # nejvyšší podlaží = podkroví pod střechou: schody u štítové zdi do středu (Míša 5. 11.)
                pkv_ = podkrovi_vystup(P, c, d, li, hloubka, t, podl + patro_y, podl + hk, H.STRECHA_POMER, kon=1, smer=-1 if sg > 0 else 1)   # od protější stěny než rameno z přízemí (jeho otvor v podlaze)
            ram = vnitrek_veze(P, c, d, li, wi, [podl, podl + patro_y] + ([podl + (patro2_y or hk)] if (podkrovi and patro2_y) else []), [0 if sg > 0 else 2, 2 if sg > 0 else 0], sq=1.1, sirka=1.0)
            svetlo(c + UP * (podl + patro_y + 2.0), 1.0, 6.0)
            sa, se, sdir, y0_, y1_ = ram[0]
            w_ = (c - sa) - sdir * (c - sa).dot(sdir); w_.y = 0; w_ = w_.normalized()   # k patě schodů z volné strany, ne napříč bokem schodiště (test 3. 11.)
            TR[jm_b] += [bod(sa - sdir * 0.45 + w_ * 1.3, podl), bod(sa - sdir * 0.45, podl), bod(sa + sdir * 0.8), bod(se + sdir * 0.5, y1_), bod(se + sdir * 0.5 + w_ * 1.6, y1_), bod(c, y1_)]   # od schodů nejdřív od zdi, ne přes otvor v podlaze
            if len(ram) < 2:
                if pkv_: TR[jm_b] += [bod(q_, y_) for q_, y_ in pkv_]
            else:
             sa2, se2, sdir2, y02, y12 = ram[1]; w2 = (c - sa2) - sdir2 * (c - sa2).dot(sdir2); w2.y = 0; w2 = w2.normalized()
             TR[jm_b] += [bod(sa2 - sdir2 * 0.45 + w2 * 1.3, y02), bod(sa2 - sdir2 * 0.45, y02), bod(sa2 + sdir2 * 0.8), bod(se2 + sdir2 * 0.5, y12), bod(se2 + sdir2 * 0.5 + w2 * 1.6, y12), bod(c, y12)]
        for k, (uu, vv) in enumerate(vnitrek or []):   # sudy / bedny podél stěn
            sud(P, c + d * (uu * li / 2) + s * (-sg) * (vv * wi / 2), podl)
        STAVBY.append({"budova": "%s_%s" % (typ, round(c.x, 1)), "vstup": True, "podl": round(podl, 2)})
        return podl
    sk = podl is not None
    podl = H.budova(P, a, b, hloubka, hk, hd, "sedlova", typ, podl=podl, otvory=otvory, vstup=vstup, patra=patra)
    if not plna_kolize: return podl   # obytná budova: kolize mají zdi (zdivo) a podlahy (palac_A)
    A_, B_ = V(a), V(b); d = B_ - A_; hh = (hk + hd) if typ == "palac" else 0.6 + (hd if hd > 0 else hk)   # jen stěny, střecha bez kolize
    dole = 0.05 if sk else 1.0
    kol(P, (A_ + B_) / 2 + UP * (podl - dole + (hh + dole) / 2), d, (hloubka + 0.2, hh + dole, d.length + 0.2))
    return podl

_VYSTUP = json.load(open(os.path.join(H.K, "pravidla/svet/hrad_vzhled.json")))["zdivo"]["kamen_vystup_m"][1]   # reliéf: nejvyšší vystupující kámen
def klenba(P, o, du, dv, u0, u1, v0, v1, osa, y_patka, vzepeti, tl=0.35, mat="kvadr", diry=(), n=10, kus=0.7, y_strop=None):
    """Valená (segmentová) klenba z klenáků nad obdélníkem u0..u1 × v0..v1 (lokálně od o po du, dv); osa 'u' nebo 'v' =
    směr osy klenby, rozpětí je v druhém směru. diry = [(u0, u1, v0, v1)] – otvor v klenbě (hladomorna)."""
    du3, dv3 = hz(du).normalized(), hz(dv).normalized()
    if osa == "u": a_ax, a_sp, l0, l1, s0, s1 = du3, dv3, u0, u1, v0, v1
    else: a_ax, a_sp, l0, l1, s0, s1 = dv3, du3, v0, v1, u0, u1
    if y_strop is not None:   # rub klenby (+ klenák šikmo, + reliéf) nesmí prorůst podlahou nad ní (sál paláce A, 3. 11.)
        assert y_patka + vzepeti + tl * 1.5 + _VYSTUP <= y_strop, "klenba prorůstá stropem: %.2f > %.2f" % (y_patka + vzepeti + tl * 1.5 + _VYSTUP, y_strop)
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
    kol(P, p + UP * (y + 0.45), Vector((1, 0, 0)), (0.52, 0.9, 0.52))   # vepsaný do dna 0,3 m (hrana kvádru 0,7 m byla mimo sud – povrch_kolize)

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
    Wk_, Hk_ = portaly.otvor(dk["sirka"], dk["vyska"], "segment")
    otv = [((k["u0"] + k["u1"]) / 2, Wk_, y, Hk_) for k in S["kobky"]] + [((zs["u0"] + Li) / 2, zs["otvor"], y, 2.0)]
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
         otvory=[(sj["u_dvere"],) + (lambda WH: (WH[0], y, WH[1]))(portaly.otvor(sj["dvere"][0], sj["dvere"][1], "segment"))])
    Wv = Wi - ob["v_tl"]
    # klenby: sál (osa podél paláce), kobky a zásobárna (osa napříč)
    sa = S["sal"]; klenba(P, o, du, dv, ob["u_tl"], Li, sa["v0"], Wv, "u", y + sa["patka_nad_podlahou"], sa["vzepeti"], y_strop=S["podlaha_palace_y"] - 0.24)
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
    sj = S["sije"]; v0 = Wi + tl; vm = v0 + sj["sirka"] / 2
    # horní stupeň v úrovni skutečného dvora u šíje (nádvoří je tu o 0,3–0,4 m výš než nadvori_y – ze sklepa schod nahoru, test A_sklep_ven)
    ytop = max(A["nadvori_y"], max(ter(*W(sj["u_horni"] - k_, vm + o_).xz) for k_ in (1.5, 2.5) for o_ in (-0.7, 0.0, 0.7)))
    n_st = round((ytop - y) / 0.19); run = n_st * 0.30; u_dole = sj["u_horni"] + run
    schody2(P, W(u_dole, vm), -du, y, ytop, w=sj["sirka"] + 0.1, kamenne=True, zabradli=())   # stupně až pod zdi (dřív 2,5cm škvíra u obou zdí – díra do terénu)
    # šíje bez trávy (Míša 4. 11.: „díry ve schodech do sklepa, bylo tam vidět trávu“ – tráva rostla v původní výšce terénu nad schody)
    BUDOVY.append([[round(q.x, 2), round(q.z, 2)] for q in (W(sj["u_horni"] - 0.6, v0 - 0.3), W(sj["u_dvere"] + 1.5, v0 - 0.3),
                                                          W(sj["u_dvere"] + 1.5, v0 + sj["sirka"] + sj["zed"]), W(sj["u_horni"] - 0.6, v0 + sj["sirka"] + sj["zed"]))])
    P.box(M(W((u_dole + sj["u_dvere"] + 1.5) / 2, vm, y - 0.4), basis=frame(du)), (sj["sirka"] + 0.8, 0.8, sj["u_dvere"] + 1.5 - u_dole + 0.6), "kvadr_sedy")   # podlaha šíje přes celý otvor v terénu (Míša 5. 11.: díra do ničeho u dveří)
    vz_ = v0 + sj["sirka"] + sj["zed"] / 2; kz = ytop + 0.9
    zed2(P, W(sj["u_horni"] - 0.6, vz_), W(sj["u_dvere"] + 1.3 + sj["zed"], vz_), sj["zed"], kz, -dv, cimburi=False, parapet=0, ext0=0, ext1=0)
    zed2(P, W(sj["u_dvere"] + 1.3 + sj["zed"] / 2, v0), W(sj["u_dvere"] + 1.3 + sj["zed"] / 2, v0 + sj["sirka"] + sj["zed"]), sj["zed"], kz, du,
         cimburi=False, parapet=0, ext0=0, ext1=0)
    # zdi šíje až k podlaze šíje (pata zed2 je podle terénu nádvoří – nad podlahou zůstala díra do ničeho, Míša 5. 11.)
    P.box(M(W(sj["u_dvere"] + 1.3 + sj["zed"] / 2, v0 + (sj["sirka"] + sj["zed"]) / 2, (y - 0.8 + ytop) / 2), basis=frame(du)), (sj["sirka"] + sj["zed"], ytop - y + 0.8, sj["zed"]), "zdivo")
    P.box(M(W((sj["u_horni"] - 0.6 + sj["u_dvere"] + 1.3 + sj["zed"]) / 2, vz_, (y - 0.8 + ytop) / 2), basis=frame(du)), (sj["zed"], ytop - y + 0.8, sj["u_dvere"] + 1.9 + sj["zed"] - sj["u_horni"]), "zdivo")
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
    if not S.get("sije_dira"): deska(e0 - dl, e1, vo, vo + dl); deska(e0 - dl, sj["u_horni"], v0, vo)   # s otvorem v terénu bez dlažby (Míša 4. 11.)
    else:   # nástupní plotna nad horním stupněm v úrovni nádvoří, sahá pod terén (Míša 6. 11.: ze sklepa poslední schod díra)
        g_ = min(ter(*W(uu, vv).xz) for uu in (sj["u_horni"] - 2.6, sj["u_horni"]) for vv in (v0 - 0.6, v0 + sj["sirka"] + 0.6)) - 0.3
        P.box(M(W(sj["u_horni"] - 1.3, vm, (ytop + 0.03 + g_) / 2), basis=frame(du)), (sj["sirka"] + 1.2, ytop + 0.03 - g_, 2.62), "kvadr_sedy", collide=True)   # 2,6 m: přes okraj jámy v terénu (test A_sklep_ven)
    if not A["palac_interier"].get("dispozice", {}).get("pavlac"):   # nad šíjí krytá pavlač paláce (5. 11.) – stříška by se s jejími vzpěrami křížila
        for uu in np.linspace(e0 + 0.2, e1 - 0.2, 4):   # sloupky stříšky na opěrné zdi
            P.beam(W(uu, vz_, kz), W(uu, vz_, kz + 1.4), 0.16, 0.16, "dub", j=0.4)
        P.beam(W(e0, vz_, kz + 1.4), W(e1, vz_, kz + 1.4), 0.18, 0.2, "dub")
        lib.shingle_roof(P, W(e0, vz_ + 0.4, kz + 1.35), W(e1, vz_ + 0.4, kz + 1.35), W(e1, v0 - 0.1, kz + 2.2), W(e0, v0 - 0.1, kz + 2.2), ridge=False)
    # pochodně
    svetlo(W(Li * 0.25, (sa["v0"] + Wv) / 2, y + 2.0)); svetlo(W(Li * 0.7, (sa["v0"] + Wv) / 2, y + 2.0))
    svetlo(W((zs["u0"] + Li) / 2, 1.1, y + 1.6), 0.8, 4.0); svetlo(W(sj["u_dvere"], vm, y + 2.4), 1.0, 5.0)
    # trasa testu: ze dvora šíjí dolů, do sálu, do každé kobky a do zásobárny
    tr = [bod(W(sj["u_horni"] - 2.5, vm + 1.2)), bod(W(sj["u_horni"] - 0.8, vm)), bod(W(sj["u_horni"] + 0.4, vm)), bod(W(u_dole + 0.6, vm), y),
          bod(W(sj["u_dvere"] + 0.2, vm), y), bod(W(sj["u_dvere"] + 0.2, Wv - 0.6), y), bod(W(sj["u_dvere"] + 0.2, (sa["v0"] + Wv) / 2), y)]   # osa dveří (5. 11.: trasa o 0,2 m vedle osy se otírala o ostění)
    for k in S["kobky"]:
        um = (k["u0"] + k["u1"]) / 2
        tr += [bod(W(um, pr["v1"] + 0.9), y, 0.15), bod(W(um, 1.0), y), bod(W(um, pr["v1"] + 0.9), y, 0.15)]
    tr += [bod(W((zs["u0"] + Li) / 2, pr["v1"] + 0.9), y, 0.15), bod(W((zs["u0"] + Li) / 2 - 0.4, 1.2), y)]
    TR["A_sklep_kobky"] = tr
    # cesta ven ze sklepa (Míša 6. 11.: „když se jde ze sklepa, poslední schod díra a chytne to hráče“ – test dřív jen dolů)
    TR["A_sklep_ven"] = [bod(W(sj["u_dvere"] + 0.2, Wv - 0.6), y), bod(W(sj["u_dvere"] + 0.2, vm), y), bod(W(u_dole + 0.6, vm), y),
                         bod(W((u_dole + sj["u_horni"]) / 2, vm)),   # půlka schodů na ose šíje (v plném běhu se postava stáčela ke kraji rampy, 9. 11.)
                         bod(W(sj["u_horni"] + 0.4, vm)), bod(W(sj["u_horni"] - 0.8, vm)), bod(W(sj["u_horni"] - 2.5, vm + 1.2))]

# ------------------------------------------------------------------ obytný palác
def schody_palace_seg(p0, p1, bd, PI):
    """Schodiště u obvodových zdí paláce A – okna za nimi se nestaví. Od 5. 11. do patra venkovní schody na pavlač,
    uvnitř jen strmé schody do podkroví u dřevěné příčky → žádné."""
    return []

def _pricka(P, W, d, s, u, v0, v1, y0, y1, dvere_v=None, sirka_dv=0.9):
    """Dřevěná prkenná příčka napříč budovou (Libštejn: dřevěné příčky v paláci) s dveřmi, kolize."""
    useky = [(v0, v1)] if dvere_v is None else [(v0, dvere_v - sirka_dv / 2), (dvere_v + sirka_dv / 2, v1)]
    for a_, b_ in useky:
        if b_ - a_ < 0.05: continue
        P.box(M(W(u, (a_ + b_) / 2, (y0 + y1) / 2), basis=frame(d)), (b_ - a_, y1 - y0, 0.12), "dub", collide=True)
    if dvere_v is not None:
        P.box(M(W(u, dvere_v, (y0 + 2.1 + y1) / 2), basis=frame(d)), (sirka_dv, y1 - y0 - 2.1, 0.12), "dub", collide=True)
        for sg in (-1, 1): P.box(M(W(u, dvere_v + sg * (sirka_dv / 2 + 0.06), (y0 + y0 + 2.15) / 2), basis=frame(d)), (0.12, 2.15, 0.16), "dub")   # zárubeň

def _lavice(P, q, d, delka=1.8):
    P.box(M(q + UP * 0.45, basis=frame(d)), (0.35, 0.06, delka), "dub", collide=True)
    for k in (-delka / 2 + 0.25, delka / 2 - 0.25): P.box(M(q + d * k + UP * 0.21, basis=frame(d)), (0.25, 0.42, 0.08), "dub")

def _stul(P, q, d, delka=2.4, lavice=True):
    s_ = d.cross(UP).normalized()
    P.box(M(q + UP * 0.75, basis=frame(d)), (0.9, 0.08, delka), "dub", collide=True)
    for k in (-delka / 2 + 0.3, delka / 2 - 0.3): P.box(M(q + d * k + UP * 0.37, basis=frame(d)), (0.7, 0.74, 0.1), "dub")   # kozy stolu
    kol(P, q + UP * 0.38, d, (0.9, 0.76, delka))   # celý stůl má kolizi (test povrch_kolize: kozy se procházely)
    if lavice:
        for sg in (-1, 1): _lavice(P, q + s_ * sg * 0.75, d, delka - 0.2)

def _truhla(P, q, d):
    P.box(M(q + UP * 0.3, basis=frame(d)), (0.55, 0.6, 1.1), "dub", collide=True)
    for k in (-0.4, 0.4): P.box(M(q + d * k + UP * 0.3, basis=frame(d)), (0.58, 0.62, 0.05), "zelezo")   # kování

def _loze(P, q, d, s_):
    """Lože: rám z fošen na nohách, slamník, houně (truhlářsky: rám čepovaný do nohou)."""
    P.box(M(q + UP * 0.32, basis=frame(d)), (1.0, 0.24, 2.0), "dub", collide=True)
    for a_ in (-0.9, 0.9):
        for b_ in (-0.42, 0.42): P.box(M(q + d * a_ + s_ * b_ + UP * 0.2, basis=frame(d)), (0.1, 0.4, 0.1), "dub")
    P.box(M(q - d * 0.95 + UP * 0.6, basis=frame(d)), (1.0, 0.6, 0.08), "dub")   # čelo
    P.box(M(q + UP * 0.5, basis=frame(d)), (0.9, 0.14, 1.85), "prkna_ven")   # slamník s houní

def palac_A(P, p0, p1, bd, PI):
    """Vnitřek paláce A podle typu malých hradů 14. st. (docs/reference/reserse_dispozice_palacu.md; Míša 5. 11.: „musí se tam
    dát bydlet, každá místnost svou funkci“): přízemí = provoz (černá kuchyně s ohništěm a dýmníkem | síň se zásobami, vstup
    z nádvoří); patro = trojdílný byt (roubená světnice s kamny | síň | komora s ložem), každá místnost portálkem z kryté
    pavlače na nádvorní straně, na pavlač venkovní dřevěné schody (Bezděz, Valdek); podkroví strmými schody ze síně
    (sklad, čeleď). Kolize = zdi + podlahy + příčky + nábytek."""
    d = hz(p1 - p0); L = d.length; d /= L; s = d.cross(UP).normalized()
    h = bd["hloubka"]; t = 1.1; vi = h / 2 - t / 2
    W = lambda u, v, y=0.0: p0 + d * u + s * v + UP * y
    F0, F1, F2 = PI["patra_y"]; iw = L - t; c = W(L / 2, 0)
    DS = PI["dispozice"]; dw = DS["dvere_sirka"]
    vl = vi - t / 2   # vnitřní líc
    podlaha(P, c, d, iw, h - t, F0 + 0.02, (), tl=0.12, mat="kvadr_sedy")   # přízemí: kamenná dlažba (kuchyně s ohništěm, ne prkna)
    podlaha(P, c, d, iw, h - t, F1, [])
    PK_ = PI.get("podkrovi", True); PKV_ = None
    if PK_:   # podkroví: strmé schody v síni podél příčky komory, výstup pod hřebenem (Míša 5. 11.)
        ps_ = DS["podkrovi_schody"]
        PKV_ = podkrovi_vystup(P, c, d, L - 2 * t, h, t, F1, F2, H.STRECHA_POMER, kon=ps_["kon"], u_steny=ps_["u_steny"] - L / 2 - ps_["kon"] * 0.06)
    else:
        podlaha(P, c, d, L + 0.5, h + 0.5, F2, [])
    # přízemí: příčka (kuchyně | síň) s dveřmi
    pu = PI["pricka_u"]
    dv_ = PI["pricka_dvere_v"]
    for v0_, v1_ in ((-vi, dv_ - 0.48), (dv_ + 0.48, vi)):
        P.box(M(W(pu, (v0_ + v1_) / 2, (F0 + F1 - 0.25) / 2), basis=frame(s)), (0.5, F1 - 0.25 - F0, v1_ - v0_), "zdivo")
    P.box(M(W(pu, dv_, (F0 + 2.1 + F1 - 0.25) / 2), basis=frame(s)), (0.5, F1 - 0.25 - F0 - 2.1, 0.96), "zdivo")
    # černá kuchyně: zvýšené ohniště u jižního čela, nad ním dýmník – omítnutý plášť jehlanu na trámcích, kouř do podkroví
    # (Žebrák), kotel na trojnožce, polena; pracovní stůl, sudy
    oh_ = W(1.45, 0, F0)
    P.box(M(oh_ + UP * 0.25, basis=frame(d)), (2.2, 0.5, 1.6), "kvadr", collide=True)
    P.box(M(oh_ + UP * 0.51, basis=frame(d)), (1.5, 0.03, 1.0), "tma")   # popel a uhlíky
    for k_ in range(4): P.beam(oh_ + s * (-0.27 + k_ * 0.18) - d * 0.35 + UP * 0.57, oh_ + s * (-0.25 + k_ * 0.17) + d * 0.3 + UP * 0.57, 0.09, 0.09, "dub", j=0.3)   # polena vedle sebe (spoje: křížení)
    for a_ in range(3):   # trojnožka a kotel
        an_ = a_ * 2.094; f_ = oh_ + (d * math.cos(an_) + s * math.sin(an_)) * 0.45 + UP * 0.52
        P.beam(f_, oh_ + UP * 1.35, 0.04, 0.04, "zelezo")
    P.lathe(M(oh_ + UP * 0.78), [(0.18, 0), (0.3, 0.12), (0.32, 0.3), (0.28, 0.42)], 10, "zelezo")
    hw_ = 1.3; y_d = F0 + 2.0   # dýmník: čtyřboký jehlan (lathe o 4 stěnách, hrany podél zdí)
    hc_ = W(0.55 + hw_ + 0.02, 0, F0)   # plášť přiléhá k čelní zdi
    P.lathe(M(hc_ + UP * (y_d - F0), basis=frame(d)), [(hw_ * 1.414, 0.0), (0.45 * 1.414, F1 - 0.24 - y_d)], 4, "omitka", phase=math.pi / 4, cap_bot=False)
    for sg_ in (-1, 1): P.beam(hc_ + s * sg_ * (hw_ - 0.06) - d * (hw_ - 0.02) + UP * (y_d - F0 - 0.07), hc_ + s * sg_ * (hw_ - 0.06) + d * (hw_ + 0.1) + UP * (y_d - F0 - 0.07), 0.12, 0.14, "dub")   # trámky pod pláštěm
    _stul(P, W(4.3, -vl + 0.6, F0), d, 1.8, lavice=False)
    sud(P, W(4.9, vl - 0.6), F0); sud(P, W(4.1, vl - 0.6), F0)
    # síň přízemí: zásoby podél zdí
    for u_ in (6.9, 7.7, 8.5): sud(P, W(u_, -vl + 0.55), F0)
    _truhla(P, W(11.3, -vl + 0.5, F0), d)
    # patro: dřevěné příčky (Libštejn), pokoje
    for pr_ in DS["patro_pricky"]:
        _pricka(P, W, d, s, pr_["u"], -vl - 0.1, vi, F1, F2 - 0.24, pr_.get("dvere_v"))   # od líce hradby (−3,0) po líc nádvorní zdi (vi)
    # roubená světnice (Templštejn, Kašperk, Bezděz: světnice vyložená dřevem): trámky na sraz po zdech, kolem oken a dveří
    # volno (okna z H.POSL_OKNA – budova_k je postavila těsně předtím)
    sv_ = next(m_ for m_ in DS["patro_mistnosti"] if m_["jm"] == "svetnice"); yo0, yo1 = F1 + 0.02, F2 - 0.26
    ok_ = [(o[0], o[1], o[2] + 0.45) for o in H.POSL_OKNA if o[3] > F1 - 0.1]
    def obklad(q0, q1, n_, mezery_):   # trámky 0,2 m po výšce podél líce q0→q1 (n_ = směr do místnosti), mezery = [(t0, t1)] v metrech od q0
        dl_ = (q1 - q0).length; e_ = (q1 - q0) / dl_; hr_ = sorted({0.0, dl_} | {min(max(x, 0), dl_) for m_ in mezery_ for x in m_})
        for t0, t1 in zip(hr_, hr_[1:]):
            if t1 - t0 < 0.08 or any(m0 - 1e-6 <= (t0 + t1) / 2 <= m1 + 1e-6 for m0, m1 in mezery_): continue
            nr_ = int((yo1 - yo0) / 0.2)
            for r_ in range(nr_):
                yy_ = yo0 + (yo1 - yo0) * (r_ + 0.5) / nr_
                P.box(M(q0 + e_ * ((t0 + t1) / 2) + n_ * 0.06 + UP * yy_, basis=frame(e_)), (0.12, (yo1 - yo0) / nr_ - 0.008, t1 - t0), "dub", collide=None)
    vh_ = -vl - 0.1   # líc hradby
    obklad(W(sv_["u0"], vi), W(sv_["u1"] - 0.06, vi), -s, [(dp["u"] - sv_["u0"] - dw / 2 - 0.12, dp["u"] - sv_["u0"] + dw / 2 + 0.12) for dp in DS["dvere_pavlac"]] +
           [(o[1] - sv_["u0"] - o[2] / 2, o[1] - sv_["u0"] + o[2] / 2) for o in ok_ if o[0] == 0])
    obklad(W(sv_["u0"], vh_), W(sv_["u1"] - 0.06, vh_), s, [(L - o[1] - sv_["u0"] - o[2] / 2, L - o[1] - sv_["u0"] + o[2] / 2) for o in ok_ if o[0] == 2])
    obklad(W(sv_["u0"], vh_), W(sv_["u0"], vi), d, [(o[1] - (vh_ + h / 2) - o[2] / 2, o[1] - (vh_ + h / 2) + o[2] / 2) for o in ok_ if o[0] == 3])
    # kachlová kamna v rohu světnice u příčky, přikládá se otvorem ze síně (Žebrák, Radyně): kamenný sokl, hliněné těleso
    # s vmazanými miskovými kachli (14. st. – hrnčířské misky ústím ven), kopule
    km = DS["kamna"]; kv_ = vh_ + 0.75 if km["strana"] == "hradba" else vi - 0.75; ku_ = DS["patro_pricky"][0]["u"] - 0.75
    k0_ = W(ku_, kv_, F1)
    P.box(M(k0_ + UP * 0.2, basis=frame(d)), (1.4, 0.4, 1.4), "kvadr", collide=True)
    P.box(M(k0_ + UP * 0.95, basis=frame(d)), (1.2, 1.1, 1.2), "omitka", collide=True)
    P.lathe(M(k0_ + UP * 1.5, basis=frame(d)), [(0.6 * 1.414, 0.0), (0.55, 0.25), (0.42, 0.5), (0.2, 0.68), (0.02, 0.72)], 8, "omitka", phase=math.pi / 8, cap_bot=False)
    for (e_, n_) in ((d, s), (s, -d)):   # dvě viditelné stěny tělesa (k místnosti, od rohu u hradby a příčky): 3 × 3 kachle
        for a_ in (-0.39, -0.13, 0.13, 0.39):   # miskové kachle: mělké misky ústím ven, vmazané v hlíně (ne černé čtverce)
            for yk_ in (0.6, 0.86, 1.12, 1.38):
                mk_ = M(k0_ + n_ * 0.6 + e_ * a_ + UP * yk_, basis=frame(UP, n_))
                P.lathe(mk_, [(0.1, 0.0), (0.105, 0.03), (0.085, 0.035)], 10, "kvadr_okno", cap_top=False)
                P.lathe(mk_, [(0.08, 0.0), (0.07, 0.03)], 10, "tma", cap_bot=False)
    P.box(M(W(DS["patro_pricky"][0]["u"] + 0.08, kv_, F1) + UP * 0.6, basis=frame(d)), (0.55, 0.5, 0.03), "tma")   # topeniště ze síně
    _stul(P, W(2.3, 0.6, F1), d, 2.2)
    _truhla(P, W(1.0, vh_ + 0.45, F1), d)
    # komora: lože a truhla
    _loze(P, W(10.4, -vl + 0.65, F1), d, s)
    _truhla(P, W(11.55, 1.2, F1), s)
    # síň patra: lavice u zdi
    _lavice(P, W(6.4, -vl + 0.3, F1), d, 1.6)
    if PK_:   # podkroví: sklad (sudy, pytle obilí) a spaní čeledi (slamníky) u kolenních stěn
        for u_ in (1.4, 2.3): sud(P, W(u_, -1.2), F2)
        for k_, u_ in enumerate((3.4, 4.0, 4.6)):
            P.lathe(M(W(u_, -1.3, F2)), [(0.2, 0), (0.28, 0.15), (0.26, 0.5), (0.12, 0.62)], 7, "prkna_ven")   # pytle
        for u_ in (10.2, 11.2):
            P.box(M(W(u_, 1.25, F2) + UP * 0.08, basis=frame(s)), (0.8, 0.16, 1.9), "prkna_ven", collide=None)   # slamník
    # dveře z pavlače (portálky v nádvorní zdi; otvory dělá budova_k), pavlač, venkovní schody
    PV = DS["pavlac"]; sv = DS["schody_ven"]; dw = DS["dvere_sirka"]
    for dp in DS["dvere_pavlac"]:
        if H.DETAIL:
            kit.doorway(P, M(W(dp["u"], h / 2, F1), basis=Matrix((d, UP, s)).transposed()), kind="vnitrni", w=dw, h=DS["dvere_vyska"],
                        depth=0.3, top="rovny", leaf=False, inner=False)   # v ose zdi jako dveře budov (hrady.budova); křídlo otevřené do pavlače ji zatarasilo
    mez_ = [(sv["u"] - sv["sirka"] / 2 - 0.05, sv["u"] + sv["sirka"] / 2 + 0.05)]
    ochoz2(P, W(0, h / 2), W(L, h / 2), t, F1, s, PV["u0"], PV["u1"], mezery=mez_, kryty=PV.get("kryta", False), sirka=PV["sirka"])
    ven = h / 2 + t / 2 + PV["sirka"]   # osa nádvorní zdi je h/2, líc h/2 + t/2
    for u_ in (PV["u0"], PV["u1"]):   # čela pavlače: zábradlí napříč (jinak pád z konce)
        zabradli(P, W(u_ + (0.1 if u_ == PV["u0"] else -0.1), h / 2 + t / 2 + 0.05), W(u_ + (0.1 if u_ == PV["u0"] else -0.1), ven - 0.42), F1)   # body bez výšky (zabradli přičte y), konec před zábradlím pavlače (spoje: křížení)
    top_ = W(sv["u"], ven)
    g_ = ter(*(top_ + s * 4.0).xz)
    for _ in range(4):   # pata schodů na terénu nádvoří (iterace přes délku ramene)
        n_ = max(2, round((F1 - g_) / 0.19)); run_ = n_ * 0.27; foot_ = top_ + s * run_; g_ = ter(*foot_.xz)
    schody2(P, foot_, -s, g_, F1, sv["sirka"], r=0.27, vyska_st=(F1 - g_) / n_)
    # nájezd z nádvoří přes práh vstupu do přízemí (kamenné stupně + rampa – jako dřív)
    vs_ = PI["vstup"]; prah = W(vs_["od_m"], h / 2 + t / 2 + 0.02)
    zem = min(ter(*(prah + s * 2.0 + d * k).xz) for k in (-0.6, 0, 0.6))
    nabeh(P, prah, s, F0, vs_["sirka"] + 0.4, L=2.2, spad=F0 - zem + 0.15)
    # světla: kuchyně (ohniště), síň dole, světnice, síň, komora, podkroví
    for (u, v, y, e) in ((2.5, 0.0, F0, 1.0), (9.0, 0.0, F0, 0.9), (2.6, 0.0, F1, 1.2), (6.9, 0.0, F1, 0.9), (10.4, 0.0, F1, 0.8), (3.0, 0.0, F2, 1.1), (9.5, 0.0, F2, 1.1)):
        svetlo(W(u, v, y + 2.1), e, 6.0)
    svetlo(W(1.4, 0, F0) + UP * 1.0, 1.4, 5.0)   # žhavé ohniště
    # trasy testu: přízemí (síň → kuchyně), patro po schodech a pavlači do síně a podkroví, světnice, komora
    vs = PI["vstup"]
    pav = lambda u: bod(W(u, h / 2 + t / 2 + PV["sirka"] / 2), F1)
    # trasa: ze dveří přízemí nejdřív dál od zábradlí venkovních schodů (test 9. 11.: úhlopříčně podél zábradlí uvízla)
    TR["A_palac"] = [bod(W(vs["od_m"], vi + 3.5)), bod(W(vs["od_m"], vi + 1.2)), bod(W(vs["od_m"], vi - 0.8), F0),
                     bod(W(pu + 0.9, dv_), F0), bod(W(pu - 1.2, dv_), F0), bod(W(pu + 0.9, dv_), F0), bod(W(vs["od_m"], vi - 0.8), F0),
                     bod(W(vs["od_m"], vi + 1.2)), bod(W(vs["od_m"], vi + 2.2)), bod(foot_ + s * 2.2), bod(foot_ + s * 1.0), bod(foot_ - s * 0.6), bod(top_ - s * 0.4, F1), pav(sv["u"]), pav(DS["dvere_pavlac"][1]["u"]),
                     bod(W(DS["dvere_pavlac"][1]["u"], vi - 1.0), F1)] + ([bod(q_, y_) for q_, y_ in PKV_] if PKV_ else [])
    TR["A_palac_svetnice"] = [bod(top_ - s * 0.4, F1), pav(sv["u"]), pav(DS["dvere_pavlac"][0]["u"]), bod(W(DS["dvere_pavlac"][0]["u"], vi - 1.0), F1), bod(W(3.95, 1.2), F1), bod(W(3.95, -0.6), F1)]   # kolem stolu k kamnům
    TR["A_palac_komora"] = [bod(top_ - s * 0.4, F1), pav(sv["u"]), pav(DS["dvere_pavlac"][2]["u"]), bod(W(DS["dvere_pavlac"][2]["u"], vi - 1.0), F1), bod(W(10.4, 0.6), F1)]
    TR["A_palac_sin_svetnice"] = [bod(W(6.3, 0.9), F1), bod(W(5.6, DS["patro_pricky"][0]["dvere_v"]), F1), bod(W(4.2, DS["patro_pricky"][0]["dvere_v"]), F1)]

# ------------------------------------------------------------------ přední hrad
def postav_A(P):
    j = A["jadro"]; t = A["kurtina_tloustka"]; kor = A["koruna_y"]; br = A["brana"]
    H.HRADBY[:] = [(j[i], j[(i + 1) % len(j)], kor) for i in range(len(j))]
    U = [usek(j, i) for i in range(len(j))]
    # plášť; brána v seříznutém SV nároží
    for i, (a, b, L, d, vn) in enumerate(U):
        ot = [brana_otvor(br, L / 2, br["prah_y"], kor)] if i == br["usek"] else []
        rv = A["vezicka"]["roh"]; wv = A["vezicka"]["rozmer"] / 2
        par = (-t / 2, L - wv) if i == rv - 1 else ((wv, L + t / 2) if i == rv else None)
        if A["vezicka"].get("zarovnat"):   # zarovnaná věžička: zeď nad úrovní koruny končí u věže (vnitřek věže volný – schody věžičky)
            wz = 2 * wv - t / 2
            if i == rv - 1: ot.append((L - wz / 2 + 0.6, wz + 1.2, kor - 0.02, 30.0)); par = (-t / 2, L - 2 * wv + t / 2)
            if i == rv: ot.append((wz / 2 - 0.6, wz + 1.2, kor - 0.02, 30.0)); par = (2 * wv - t / 2, L + t / 2)
        e0_, e1_ = pokos_ext(j, i, t); zed2(P, a, b, t, kor, vn, otvory=ot, par=par, cela=(False, False), ext0=e0_, ext1=e1_, cimburi=A.get("cimburi", True))   # čela kusů v nároží by v tupém úhlu vyčnívala z líce (Míša 5. 11.: švy) – roh kryje klín naroze()
    naroze(P, j, t, kor, vynechat=(A["vezicka"]["roh"],))
    a, b, L, d, vn = U[br["usek"]]; C = (a + b) / 2
    portal(P, C - vn * (t / 2), -vn, br["sirka"], brana_vyska(br, br["prah_y"], kor), br["prah_y"], t)
    dlazba(P, C, -vn, br["sirka"], t + 0.2, br["prah_y"] + 0.04)
    nA = -vn
    # nárožní věžička (kresba) – komora na úrovni koruny, dveře k ochozu východní zdi
    vz = A["vezicka"]; ri = vz["roh"]; aE, bE, LE, dE, vnE = U[ri - 1]
    rc = V(j[ri]); w = vz["rozmer"]; tv = 0.9
    zo_ = (w / 2 - t / 2) if vz.get("zarovnat") else 0.0   # zarovnaná: střed dovnitř rohu, vnější líce v líci zdí
    rc = rc + vnE * zo_ - dE * zo_
    sD_ = dE.cross(UP).normalized(); och_v = OCH - zo_ * (1 if sD_.dot(vnE) > 0 else -1)   # zarovnaná věž: dveře v ose ochozu (střed věže posunut o zo_)
    dv_v = [("-d", och_v, 1.2, kor)]
    if vz.get("dvere_ochoz3"):   # dveře ze západní stěny (+s) na ochoz jižní hradby k paláci (úsek ri)
        sS = dE.cross(UP).normalized(); q3 = pochozi(U, ri, w / 2 + 0.6); o3 = (q3 - rc).dot(dE)
        o3 = max(-(w / 2 - tv - 0.55), min(w / 2 - tv - 0.55, o3)); dv_v.append(("+s", o3, 1.0, kor))
    vez2(P, rc, dE, w, w, kor, kor + vz["nad_korunou"], "jehlan", dvere=dv_v, tw=tv,
         strilny=[(st_, 0.0, kor + vz["patro_nad_ochozem"] + 1.2) for st_ in ("+d", "+s", "-s")])
    ram_v = vnitrek_veze(P, rc, dE, w - 2 * tv, w - 2 * tv, [kor, kor + vz["patro_nad_ochozem"]], [0], sq=0.7, run=2.64)
    if vz.get("dvere_ochoz3"):   # ochoz úseku ri: od líce věžičky po líc paláce (budova na tomto úseku)
        a3, b3, L3, d3, vn3 = U[ri]
        pal = [bd_ for bd_ in A["budovy"] if bd_["usek"] == ri]
        s1_3 = min([bd_["od_m"] for bd_ in pal] + [L3]) - 0.01
        s0_3 = w / 2 - 0.02
        if s1_3 - s0_3 > 1.0:
            ochoz2(P, a3, b3, t, kor, vn3, s0_3, s1_3, lehka=True)
            TR["A_vezicka_ochoz_palac"] = [bod(rc - sS * 0.3, kor), bod(rc + sS * (w / 2 - tv - 0.3) + dE * o3, kor),
                                           bod(pochozi(U, ri, s0_3 + 0.6), kor), bod(pochozi(U, ri, s1_3 - 0.5), kor)]
    svetlo(rc + UP * (kor + 2.0), 0.9, 4.0); svetlo(rc + UP * (kor + vz["patro_nad_ochozem"] + 2.0), 0.9, 4.0)
    # budovy podél plášťě
    SK = A.get("sklep"); g = hrad_geom.sklep(A) if SK else None
    for bd in A["budovy"]:
        H.OMITKA = bd.get("omitka", True); H.HRADBA_OKENKA = bd.get("okenka_ve_zdi", False)
        a, b, L, d, vn = U[bd["usek"]]
        o = t / 2 + bd.get("odsazeni", -1.0) + bd["hloubka"] / 2
        p0 = a + d * bd["od_m"] + vn * o; p1 = a + d * bd["do_m"] + vn * o
        if SK and bd["id"] == SK["budova"]:   # palác se sklepem: podlaha zadaná, dveře ze šíje v S zdi (strana 0 = k nádvoří)
            sj = SK["sije"]
            PI = A["palac_interier"]; vs = PI["vstup"]
            H.BEZ_OKEN[:] = schody_palace_seg(p0, p1, bd, PI)
            H.OKAP_STRANY.clear(); H.OKAP_STRANY[0] = PI["dispozice"]["pavlac"].get("okap_nad_m", 0.3)   # strana k nádvoří: okap končí nad stříškou pavlače
            budova_k(P, (p0.x, p0.z), (p1.x, p1.z), bd["hloubka"], bd["vyska_kamen"], bd["vyska_drevo"], bd["typ"], podl=SK["podlaha_palace_y"],
                     otvory=[(0, sj["u_dvere"] + g["tl"] / 2, sj["dvere"][0], SK["podlaha_y"], SK["podlaha_y"] + sj["dvere"][1]),
                             (vs["strana"], vs["od_m"], vs["sirka"], SK["podlaha_palace_y"], SK["podlaha_palace_y"] + vs["vyska"])] +
                            [(0, dp_["u"], PI["dispozice"]["dvere_sirka"], PI["patra_y"][1], PI["patra_y"][1] + PI["dispozice"]["dvere_vyska"]) for dp_ in PI["dispozice"]["dvere_pavlac"]],
                     vstup=(vs["strana"], vs["od_m"], vs["sirka"], vs["vyska"]), plna_kolize=False, patra=PI["patra_y"][:2])
            H.OKAP_STRANY.clear()
            palac_A(P, p0, p1, bd, PI)
        else:
            H.BEZ_OKEN[:] = []
            budova_k(P, (p0.x, p0.z), (p1.x, p1.z), bd["hloubka"], bd["vyska_kamen"], bd["vyska_drevo"], bd["typ"],
                     k_bodu=tuple(np.mean(np.array(A["jadro"], float), axis=0)), vnitrek=bd.get("vnitrek", [(0.7, 0.6), (0.5, 0.6)]),
                     patro_y=bd.get("patro_y"), podkrovi=bd.get("podkrovi", True))
    H.OMITKA = True; H.HRADBA_OKENKA = False
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
    plosina(P, pod, d, 1.6, sch["odsazeni"] + sch["sirka"] / 2 - t / 2 - 0.8, kor, sloupy=False)   # nese ji zeď (trámy vetknuté do zdi); sloupy procházely roubenou budovou pod ní (hlídač spojů 3. 11.)
    mez = (s_top - 1.6, s_top + 0.05)
    oz = A["ochoz"]
    for i in oz["useky"]:
        a, b, L, d, vn = U[i]
        s0 = oz.get("usek%d_od_m" % i, -t / 2); s1 = L + t / 2
        if i == ri - 1: s1 = L - w / 2 - zo_       # východní zeď končí u věžičky
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
    # Konec hradby u branky jako Havran (fort.walls + gatehouse): poslední úsek kolmo do boční stěny věže, koruna = podlaha
    # strážnice (ochoz vchází portálkem rovně a v jedné výšce; Míša 4. 11.: „nevychází vchod z ochozu rovně do věže“).
    # Osa krajního úseku posunutá tak, aby osa pavlače (vnitřní strana, ke dvoru = +s) šla středem portálku.
    s_b = dB.cross(UP).normalized(); yp_b = H.patro_brany_y(vb["podlaha_y"]); Lr = vb["hradba_rovne_m"]
    def konec_k_vezi(sg_, hd):
        v_osy = H.portal_v(vb["rozmer"][1]) - (hd["tloustka"] / 2 + hd["ochoz_sirka_m"] / 2)
        pf = O + dB * sg_ * (vb["rozmer"][0] / 2 + Lr) + s_b * v_osy; pe = O + dB * sg_ * (vb["rozmer"][0] / 2 - 0.3) + s_b * v_osy
        return [[pf.x, pf.z], [pe.x, pe.z]]
    def bez_blizkych(osa_, kon):   # vrchol blíž než 6 m od začátku rovného úseku vynechat (krátký úsek by nepobral schody pavlače mimo roh)
        return [q for q in osa_ if (V(q) - V(kon[0])).length > 6.0]
    hw = A["hradba_vychod"]; kv, kw = konec_k_vezi(sg, hv), konec_k_vezi(-sg, hw)
    pts = bez_blizkych(hv["osa"], kv) + kv
    HRADBY = []
    for osa, hd in ((pts, hv), (kw[::-1] + bez_blizkych(hw["osa"], kw), hw)):
        # hrady.zed staví cimbuří vpravo od směru: osu orientovat tak, aby cimbuří bylo ven od jádra (tablet 2. 11.)
        p, q = osa[0], osa[1]; dpq = Vector((q[0] - p[0], 0, q[1] - p[1])); mid = Vector(((p[0] + q[0]) / 2, 0, (p[1] + q[1]) / 2))
        if (mid - jadro_stred).dot(dpq.cross(UP)) < 0: osa = osa[::-1]
        u_v = 1 if (V(osa[-1]) - O).length < (V(osa[0]) - O).length else 0   # konec u branky
        kor_ = [None] * (len(osa) - 1)
        if delka_ochozu(osa, hd, u_v) > 0: kor_[-1 if u_v else 0] = yp_b   # krajní úsek: koruna ve výšce strážnice (jen kde je ochoz)
        j_ = -2 if u_v else 1   # úsek před ním jednou výškou koruny – pavlač vyrovná výšku jedněmi schody (dva stupně koruny se nevešly)
        a_, b_ = V(osa[j_]), V(osa[j_ + 1])
        if kor_[-1 if u_v else 0] is not None: kor_[j_] = round((max(ter(*(a_.lerp(b_, k / 12)).xz) for k in range(13)) + hd["vyska"]) * 2) / 2
        uk = H.zed_cara(P, osa, hd["tloustka"], hd["vyska"], cimburi=A.get("cimburi_vnejsi", A.get("cimburi", True)), koruny=kor_, plynule=hd.get("plynula_koruna", False) and not any(k_ is not None for k_ in kor_))
        HRADBY.append((osa, uk, hd))
    H.VEZ_PATRO.clear()
    # portálky strážnice: kde osa pavlače ochozu narazí do věže (hradba přiléhá k věži šikmo – pevná boční stěna nestačila, test průchodu)
    d_v = Vector((-nA.z, 0, nA.x)).normalized(); s_v = d_v.cross(UP).normalized(); wv, dv_ = vb["rozmer"]; POR = []
    for osa, uk, hd in HRADBY:
        konec = 1 if (V(osa[-1]) - O).length < (V(osa[0]) - O).length else 0
        if delka_ochozu(osa, hd, konec) <= 0: POR.append(None); continue   # bez ochozu = bez portálku (Míša 4. 11.)
        a_, b_ = (V(osa[-2]), V(osa[-1])) if konec else (V(osa[0]), V(osa[1]))
        dd = (b_ - a_).normalized(); vn_ = -dd.cross(UP).normalized(); g_ = vn_ * (hd["tloustka"] / 2 + hd["ochoz_sirka_m"] / 2)
        start, smer = (a_, dd) if konec else (b_, -dd)
        pred = None
        for k in range(1, 400):
            p_ = start + smer * (k * 0.05) + g_; u_ = (p_ - O).dot(d_v); v_ = (p_ - O).dot(s_v)
            if abs(u_) <= wv / 2 and abs(v_) <= dv_ / 2:
                st_ = ("+d" if u_ > 0 else "-d", v_) if pred is not None and abs(pred[0]) > wv / 2 else ("+s" if v_ > 0 else "-s", u_)
                POR.append(st_); break
            pred = (u_, v_)
        else: POR.append(None)
    H.vez(P, (O.x, O.z), tuple(vb["rozmer"]), vb["vyska"], "jehlan", yaw_d=(-nA.z, nA.x), brana=True, yf=vb["podlaha_y"], patro=vb.get("patro", True),
          portalky=[q for q in POR if q])
    if H.VEZ_PATRO:   # strážnice: portálky v bočních stěnách -> ochozy obou hradeb (docs/reference/branka_ochoz.md)
        vp = H.VEZ_PATRO[0]; c_, d_, s_ = vp["stred"], vp["d"], vp["s"]; yp = vp["yp"]
        trasa_t = None; BODY_OCHOZ = {}
        for (osa, uk, hd), por in zip(HRADBY, POR):
            if por is None: continue
            u_tower = 1 if (V(osa[-1]) - O).length < (V(osa[0]) - O).length else 0   # který konec osy je u branky
            dvere, n_dv = next((f_, n_) for jm, f_, n_ in vp["dvere"] if jm == por[0])
            mz = {tuple(hd["schody"]["horni_konec"]): 1.2} if "schody" in hd else None
            osa_o, uk_o = orez_ochozu(osa, uk, u_tower, delka_ochozu(osa, hd, u_tower))
            body = ochoz_hradby(P, osa_o, uk_o, hd["tloustka"], {u_tower: (yp, dvere, n_dv)}, mezery=mz, odstup=0.0, sirka=hd["ochoz_sirka_m"])
            BODY_OCHOZ[id(osa)] = (body, u_tower)
            svetlo(c_ + UP * (yp + 2.0), 1.0, 5.0)
            if hd is hw: trasa_t = (osa, uk, body, dvere, n_dv)
        # ze země: schodiště podél vnitřního líce hradby_vychod v předhradí (úsek a poloha z dat)
        osa, uk, body, dvere, n_dv = trasa_t; vs = hw["schody"]; q_ = V(vs["horni_konec"])
        i = min(range(len(osa) - 1), key=lambda k: (q_ - (V(osa[k]) + V(osa[k + 1])) / 2).length)
        a = V(osa[i]); b = V(osa[i + 1]); L = (b - a).length; d = (b - a) / L
        vn = -d.cross(UP).normalized(); tt = hw["tloustka"]; y_k = max(u[2] for u in uk[i] if u[0] <= (q_ - a).dot(d) <= u[1] + 1e-3)
        SW = hw["ochoz_sirka_m"]; sT = (q_ - a).dot(d); st_o = tt / 2 + SW + 0.1 + 0.55   # osa schodiště hned vedle pavlače
        plosina(P, a + d * (sT + 0.6) + vn * (tt / 2 + SW + 0.55), d, 1.2, 1.3, y_k, sloupy=True)   # podesta z pavlače na schody
        n_ = round((y_k - ter(*(a + d * (sT - 3) + vn * st_o).xz)) / 0.19); run = n_ * 0.27
        for _ in range(3):
            f_ = a + d * (sT - run) + vn * st_o; run = round((y_k - ter(f_.x, f_.z)) / 0.19) * 0.27
        f_ = a + d * (sT - run) + vn * st_o
        schody2(P, f_, d, ter(f_.x, f_.z), y_k, 1.0, zabradli=(1, -1))
        zabradli(P, a + d * (sT + 1.2) + vn * (tt / 2 + SW), a + d * (sT + 1.2) + vn * (tt / 2 + SW + 1.2), y_k)
        zabradli(P, a + d * sT + vn * (tt / 2 + SW + 1.2), a + d * (sT + 1.2) + vn * (tt / 2 + SW + 1.2), y_k)
        bb, ut = BODY_OCHOZ[id(osa)]; q2 = a + d * (sT + 0.6)
        k0 = min(range(len(bb)), key=lambda k: (Vector((bb[k][0], 0, bb[k][1])) - q2).length)
        sm_ = 1 if ut == 1 else -1   # směr k věži v pořadí bodů
        if ((Vector((bb[k0][0], 0, bb[k0][1])) - a).dot(d) - (sT + 0.6)) * sm_ < 0: k0 += sm_   # první bod za podestou
        po_k_vezi = bb[k0:] if ut == 1 else bb[:k0 + 1][::-1]
        STAVBY.append({"ochoz_hradby_mezera": [i, round(sT, 2), round(sT + 1.2, 2)]})
        TR["A_branka_patro"] = [bod(f_ - d * 1.8 + vn * 0.0), bod(f_ - d * 0.5), bod(a + d * (sT + 0.6) + vn * st_o, y_k),
                                bod(a + d * (sT + 0.6) + vn * (tt / 2 + SW / 2), y_k, 0.25)] + po_k_vezi + [bod(dvere - n_dv * 0.9, yp), bod(dvere - n_dv * 1.6, yp)]
    mv_ = A.get("most_vnejsi")
    for sg in ((-1,) if mv_ else (1, -1)):   # nájezd přes práh branky z terénu (žádný schod, test průchodu A_vstup)
        pr_ = O + nA * sg * (vb["rozmer"][1] / 2); g_ = min(ter(*(pr_ + nA * sg * k_).xz) for k_ in (0.3, 0.9, 1.5))
        sp_ = vb["podlaha_y"] - g_ + 0.1   # skutečná výška nad terénem (dřív výchozí 0,7 m – test nabeh_vyska)
        if sp_ > 0.05: nabeh(P, pr_, nA * sg, vb["podlaha_y"], vb["rozmer"][0] - 2.0, L=max(0.6, round(sp_ / 0.17) * 0.32), spad=sp_)
    if mv_:   # most před vnější brankou přes vnější příkop (náčrt Míši 5. 11.), rovně v ose brány
        kv_ = O + nA * (vb["rozmer"][1] / 2); zv_ = kv_ + nA * mv_["delka_m"]
        pl_ = next(q for q in D["teren"]["plosiny"] if q["id"] == "A_nastup_vnejsi")
        most2(P, zv_, pl_["y"], kv_, vb["podlaha_y"], mv_["sirka"], mv_["padaci_m"])
    m = A["most"]; zac = C + nA * vb["predprostor_t_m"][0]; kon = C + nA * (t / 2)
    most2(P, zac, vb["podlaha_y"], kon, br["prah_y"], m["sirka"], m["padaci_m"], na_terenu=False)
    yp = vb["podlaha_y"]; dvur = C - nA * 9
    if mv_:   # vnější most (vlastní trasa – A_vstup má bránu jádra na indexu 4, test vrata_funkce)
        TR["A_most_vnejsi"] = [bod(C + nA * (vb["t_m"] + vb["rozmer"][1] / 2 + mv_["delka_m"] + 2.0)), bod(C + nA * (vb["t_m"] + vb["rozmer"][1] / 2 + mv_["delka_m"])),
                               bod(C + nA * (vb["t_m"] + 1.0), yp), bod(C + nA * vb["t_m"], yp)]
    TR["A_vstup"] = [bod(C + nA * (vb["t_m"] + (1.5 if mv_ else 5.5)), yp if mv_ else None), bod(C + nA * vb["t_m"], yp), bod(C + nA * (vb["t_m"] - 4.0), yp), bod(C + nA * 13), bod(C + nA * 0.95, br["prah_y"]),
                     bod(C - nA * 3), bod(dvur), bod(V((6.5, 5.0)))]   # dvůr (mimo studnu) (palác a šíje jsou teď u Z zdi)
    a, b, L, d, vn = U[sch["usek"]]
    TR["A_ochoz"] = [bod(dvur), bod(st + d * 1.4 + vn * 2.2), bod(st + d * 1.2), bod(st), bod(e1, ym), bod(e1 - d * 1.4, ym), bod(e2, kor), bod(pod, kor),
                     bod(pochozi(U, sch["usek"], s_top - 0.8), kor)] + [bod(roh(U, k_), kor) for k_ in A.get("ochoz_rohy", [3, 2, 1, 0])]
    sv = dE.cross(UP).normalized()
    (sa, se, sdir, sy0, sy1), = ram_v
    TR["A_vezicka"] = [bod(pochozi(U, ri - 1, 14.0), kor), bod(pochozi(U, ri - 1, LE - w / 2 - zo_ - 0.8), kor), bod(rc - dE * 0.9 + sv * och_v, kor),
                       bod(sa - sdir * 0.3, kor), bod(sa + sdir * 0.8), bod(se - sdir * 0.05, None, 0.2), bod(se - sdir * 0.05 + sv * 1.6, sy1)]
    return C, nA

# ------------------------------------------------------------------ zadní hrad
def postav_B(P):
    hp = B["hradba"]; t = B["tloustka"]; kor = B["koruna_y"]; br = B["brana"]
    H.HRADBY[:] = [(hp[i], hp[(i + 1) % len(hp)], kor) for i in range(len(hp))]
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
        if i in B.get("hradba_palac", []): continue   # zeď paláce je hranou hradu (bez hradby před ní)
        ot = [brana_otvor(br, br["stred_m"], B["dolni_y"], kor)] if i == br["usek"] else []
        iv = usek_v_palaci(a, b)
        if iv:   # u konce úseku i přesah zdi za vrchol (t/2)
            s0_ = iv[0] - (t if iv[0] < 0.1 else 0.05); s1_ = iv[1] + (t if iv[1] > L - 0.1 else 0.05)
            ot.append(((s0_ + s1_) / 2, s1_ - s0_, pa_.get("podlaha_min_y", -100.0), 200.0))
        e0_, e1_ = pokos_ext(hp, i, t); zed2(P, a, b, t, kor, vn, otvory=ot, krok=3.0, cimburi=B.get("cimburi", True), cela=(False, False), ext0=e0_, ext1=e1_)
    naroze(P, hp, t, kor, vynechat=tuple(k for k, q in enumerate(hp) if v_palaci(V(q), -t) or k in B.get("hradba_palac", []) or (k - 1) % len(hp) in B.get("hradba_palac", [])))   # rohy úseků, kde hranou je palác: klín by trčel do paláce (test 5. 11.)
    a, b, L, d, vn = U[br["usek"]]; G = a + d * br["stred_m"]; vnG = vn
    portal(P, G - vn * (t / 2), -vn, br["sirka"], brana_vyska(br, B["dolni_y"], kor), B["dolni_y"], t)
    dlazba(P, G, -vn, br["sirka"], t + 0.2, B["dolni_y"] + 0.04)
    gi = min(ter(*(G + vn * (t / 2 + k)).xz) for k in (0.3, 0.9, 1.5, 2.0))   # nádvoří níž než práh: nájezd i dovnitř (Míša 4. 11.: ven branou
    if B["dolni_y"] - gi > 0.03:                                              # nešlo vyjít, u země překážka – hrana prahu 14 cm)
        nabeh(P, G + vn * (t / 2), vn, B["dolni_y"], br["sirka"], L=max(0.4, round((B["dolni_y"] - gi + 0.1) / 0.17) * 0.32), spad=B["dolni_y"] - gi + 0.1)   # stupeň nebo dva u prahu
    # most přes průrvu: vodorovně z nástupu na práh
    m = B["most"]; zac = V(m["od"])
    most2(P, zac, m["nastup_y"], G - vn * (t / 2), B["dolni_y"], m["sirka"], m["padaci_m"])
    zt = B["terasa_z"]; xs = B["schody_terasa"]["x"]; sts = None
    if B.get("terasa", True):
        zt = B["terasa_z"]; xs = B["schody_terasa"]["x"]
        x0 = min(p[0] for p in hp) - 1; x1 = max(p[0] for p in hp) + 1
        ta, tb = V((x0 + 1.4, zt)), V((x1 - 1.6, zt))
        # konce terasy až k líci hradby (Míša 4. 11.: „vedle věže proč není zábradlí“ – mezi koncem opěrné zdi a hradbou byla mezera bez zídky)
        for kon_, smer_ in ((0, -1), (1, 1)):
            q_ = ta if kon_ == 0 else tb
            for k_ in range(80):
                pr_ = q_ + Vector((smer_ * 0.05 * (k_ + 1), 0, 0))
                if zdi_za(P, [pr_ + UP * (B["horni_y"] + 0.5)])[0]: q_ = pr_ + Vector((smer_ * 0.1, 0, 0)); break
            if kon_ == 0: ta = q_
            else: tb = q_
        Lt = (tb - ta).length
        vz_ = B["vez"]; ox_ = [((xs[0] + xs[1]) / 2 - ta.x, xs[1] - xs[0], B["horni_y"], 3.0)]
        if abs(vz_["stred"][1] - zt) < vz_["rozmer"] / 2:   # štít mezi nádvořími stojí na terase: opěrná zeď přerušená půdorysem štítu
            ox_.append((vz_["stred"][0] - ta.x, vz_["rozmer"] + 0.1, B["dolni_y"] - 6.0, 20.0))
        zed2(P, ta, tb, 1.0, B["horni_y"], Vector((0, 0, 1)), otvory=ox_,
             cimburi=False, parapet=1.0, ext0=0, ext1=0)
        sts = V(((xs[0] + xs[1]) / 2, zt - 0.5 - (B["horni_y"] - B["dolni_y"]) / 0.19 * 0.3))
        schody2(P, sts, Vector((0, 0, 1)), B["dolni_y"], B["horni_y"],
                w=xs[1] - xs[0] - 0.1, kamenne=True, zabradli=())
    # hranolová věž: komora v úrovni ochozu, lávka z pavlače západní zdi
    vz = B["vez"]; c = V(vz["stred"]); w = vz["rozmer"]; tv = vz["steny"]
    # okna na všech stranách každého patra nad vstupním (Míša 4. 11.: „okna ve věži jen někde, jinde plná“); na stěnách se schody
    # okno v polovině stěny nad ramenem (rameno vede od rohu k rohu, ve středu stěny je ~1,6 m nad podlahou)
    global OKN_CFG; OKN_CFG = vz.get("okna"); oc_ = OKN_CFG
    ok_b = [(st_, 0.0) + ((oc_["horni"][0], y_ + 0.9, oc_["horni"][1]) if y_ == vz["patra_y"][-1] else
                          (oc_["stredni"][0], y_ + (1.0 if st_ in ("+d", "-d") else 2.0), oc_["stredni"][1]))
            for y_ in vz["patra_y"][1:] for st_ in ("+d", "-d", "+s", "-s") if not (st_ == "-d" and abs(y_ - kor) < 0.1)]
    sl_b = [(st_, 0.0, vz["patra_y"][0] + 1.3) for st_ in ("+s", "-s", "+d")]
    dvz = B.get("dvorek", {}).get("dvere_veze")
    dv_b = [(vz.get("dvere_strana", "-d"), 0.0, 1.2, kor)] + ([(dvz["stena"], dvz["posun"], dvz["sirka"], kor)] if dvz else [])
    vn_ = vz.get("vstup_nadvori")
    if vn_: dv_b.append((vn_["stena"], vn_["posun"], vn_["sirka"], vz["dno_y"]))
    ok_b = [o for o in ok_b if o[0] in vz.get("okna_strany", ("+d", "-d", "+s", "-s"))]   # štítová zeď: okna jen do nádvoří (kresba misa_01)
    wd = vz.get("delka", w)   # štít B: dlouhá budova (delka podél x, rozmer napříč)
    vez2(P, c, Vector((1, 0, 0)), wd, w, vz["dno_y"], vz["vrch_y"], vz.get("strecha", "valba"), dvere=dv_b, tw=tv, okna=ok_b, strilny=sl_b)
    if dvz:   # lávka z dveří věže (+s) podél jižní stěny věže k hornímu konci schodů dvorku a ochozu
        dvo = B["dvorek"]; xd = c.x + dvz["posun"]; zl = c.z + w / 2 + 0.6
        x0l = dvo["lavka_x0"]; x1l = xd + dvz["sirka"] / 2 + 0.3
        plosina(P, V(((x0l + x1l) / 2, zl)), Vector((1, 0, 0)), x1l - x0l, 1.2, kor, sloupy=True)
    if vn_:   # schody z vnitřního nádvoří podél jižní (+s) stěny věže k podestě u dveří přízemí (Míša 9. 11.)
        sz_ = 1.0 if vn_["stena"] == "+s" else -1.0; zf_ = c.z + sz_ * (w / 2)   # líc stěny
        zs_ = zf_ + sz_ * 0.68; xd_ = c.x + vn_["posun"]
        n_ = round((vz["dno_y"] - B["horni_y"]) / 0.19); run_ = n_ * 0.27
        sm_ = float(vn_.get("smer_schodu", 1)); dx_ = Vector((sm_, 0, 0))   # +1 schody stoupají k +x, −1 k −x
        x1_ = xd_ - sm_ * (vn_["sirka"] / 2 + 0.15); x0_ = x1_ - sm_ * run_
        zab_ = (1,) if sz_ * sm_ > 0 else (-1,)
        e_n, _ = schody2(P, V((x0_, zs_)), dx_, B["horni_y"], vz["dno_y"], 1.2, zabradli=zab_)
        xk_ = xd_ + sm_ * (vn_["sirka"] / 2 + 0.2)
        plosina(P, V(((x1_ + xk_) / 2, zs_)), Vector((1, 0, 0)), abs(xk_ - x1_), 1.36, vz["dno_y"], sloupy=True)
        TR["B_vez_nadvori"] = [bod(V((x0_ + sm_ * 1.0, zs_ + sz_ * 2.2)), B["horni_y"]), bod(V((x0_ - sm_ * 0.6, zs_)), B["horni_y"]), bod(V((x0_ + sm_ * 0.3, zs_))),
                               bod(e_n, vz["dno_y"]), bod(V((xd_, zs_)), vz["dno_y"]), bod(V((xd_, zf_ - sz_ * 1.6)), vz["dno_y"]), bod(c, vz["dno_y"])]
    ram_b = vnitrek_veze(P, c, Vector((1, 0, 0)), wd - 2 * tv, w - 2 * tv, [vz["dno_y"]] + vz["patra_y"], vz["steny_ramen"], sq=1.0)   # podesty 1,0 m (Míša 4. 11.: „schody moc blízko zdi, ne pansky“; reference 1,0–1,4 m), ramena 3,2 m = 45° (při 45° postava občas uvízla na konci ramene)
    # hladomorna v přízemí věže: valená klenba (osa S–J) s otvorem nad schody, kruhy s řetězy, slabé světlo
    iv = w - 2 * tv; ivu = wd - 2 * tv; ov = c - Vector((ivu / 2, 0, iv / 2)); hl = vz.get("hladomorna")
    if hl: klenba(P, ov, Vector((1, 0, 0)), Vector((0, 0, 1)), 0, ivu, 0, iv, "u" if wd > w else "v", vz["dno_y"] + hl["patka_nad_dnem"], hl["vzepeti"],
           diry=[(0, ivu, iv - 1.3, iv)])   # celý pás nad schody (klenák u hrany otvoru vyčníval nad podlahu – test B_vez_sklep)
    if hl:
        kruh_retez(P, c - Vector((0, 0, iv / 2)), Vector((0, 0, 1)), vz["dno_y"] + 1.3, 1.0)
        kruh_retez(P, c - Vector((iv / 2, 0, -0.8)), Vector((1, 0, 0)), vz["dno_y"] + 1.3, 1.0)
        svetlo(c + UP * (vz["dno_y"] + 1.5), 0.5, 4.0)
    for yp in vz["patra_y"]:
        svetlo(c - Vector((0, 0, iv / 2 - 0.4)) + UP * (yp + 2.0), 1.1, 5.0)
    lav0 = c + Vector((wd / 2, 0, 0)) * (1 if vz.get("dvere_strana", "-d") == "+d" else -1)
    # západní pavlač: najít úsek hradby nejblíž dveřím
    iw = min(range(len(U)), key=lambda i: abs((lav0 - (U[i][0] + U[i][1]) / 2).length))
    a, b, L, d, vn = U[iw]
    sproj = max(0, min(L, (lav0 - a).dot(d))); hrana = a + d * sproj + vn * (t / 2 + 0.9)
    dl = (lav0 - hrana); dl.y = 0
    STIT_SCHODY = vz.get("vstup_schody")   # štít uprostřed nádvoří (kresba misa_01): vstup po dřevěných schodech z předního nádvoří podél Z čela
    if STIT_SCHODY:
        dz_ = Vector((0, 0, 1)); dx_ = Vector((-1, 0, 0)) if vz.get("dvere_strana", "-d") == "-d" else Vector((1, 0, 0))
        pod_ = lav0 + dx_ * 1.3   # podesta 2,4 m: schody o 1,9 m západněji než dveře – dřív 0,4 m v příčné zdi (hlídač schody_nastup_vystup 5. 11.)
        plosina(P, pod_, dz_, 1.6, 2.4, kor, sloupy=True)
        n_st = round((kor - B["horni_y"]) / 0.19); run_ = n_st * 0.27
        st_stit = pod_ + dz_ * (0.8 + run_) + dx_ * 0.6
        e_stit, _ = schody2(P, st_stit, -dz_, B["horni_y"], kor, 1.2, zabradli=(1,) if dx_.x < 0 else (-1,))
        TR["B_stit_vstup"] = [bod(st_stit + dz_ * 2.0, B["horni_y"]), bod(st_stit + dz_ * 0.6, B["horni_y"]), bod(st_stit), bod(e_stit, kor), bod(pod_, kor), bod(lav0, kor), bod(c, kor)]
    elif dl.length > 0.1:
        plosina(P, (hrana + lav0) / 2, dl, dl.length + 0.3, 1.3, kor, sloupy=False)
    # palác 10×12
    p = B["palac"]; H.BEZ_OKEN[:] = []; H.OMITKA = p.get("omitka", True); H.STRECHA_POMER = p.get("strecha_pomer", 0.62)   # kresba misa_01: palác B kamenný (Míša 5. 11.: omítka jen dle obrázku)
    budova_k(P, p["osa"][0], p["osa"][1], p["hloubka"], p["vyska_kamen"], p["vyska_drevo"], "palac",
             k_bodu=tuple(np.mean(np.array(B["hradba"], float), axis=0)), vnitrek=p.get("vnitrek", [(-0.8, -0.7), (-0.6, -0.7)]), patro_y=p.get("patro_y", 4.0),
             patro2_y=p.get("patro2_y"))
    H.OMITKA = True; H.STRECHA_POMER = 0.62
    for z_ in p.get("zarizeni", []):   # obytný palác B (Míša 5. a 9. 11.): síň, komnata, hospodářská místnost
        q_ = V((z_["x"], z_["z"])) + UP * z_["y"]; dz_ = Vector((z_["smer"][0], 0, z_["smer"][1])).normalized()
        if z_["co"] == "stul": _stul(P, q_, dz_, z_.get("delka", 2.2), lavice=z_.get("lavice", True))
        elif z_["co"] == "truhla": _truhla(P, q_, dz_)
        elif z_["co"] == "loze": _loze(P, q_, dz_, dz_.cross(UP).normalized())
    ps_ = B.get("prujezd_stisek") or None   # pultová stříška průchodu u paty štítu (kresba misa_01)
    if ps_:
        x0s, x1s = ps_["x"]; z0s, z1s = ps_["z"]
        lib.shingle_roof(P, Vector((x0s, ps_["y_nizko"], z1s)), Vector((x0s, ps_["y_nizko"], z0s)), Vector((x1s, ps_["y_vysoko"], z0s)), Vector((x1s, ps_["y_vysoko"], z1s)), ridge=False)
    # příčná zeď mezi štítem a palácem s druhou bránou (kresba misa_01, Míša 5. 11.)
    pz_ = B.get("pricna_zed"); Gp_ = None
    if pz_:
        a_, b_ = V(pz_["od"]), V(pz_["do"]); Lp_ = (b_ - a_).length; dp_ = (b_ - a_) / Lp_
        vp_ = dp_.cross(UP).normalized()
        if vp_.x < 0: vp_ = -vp_   # vn = dovnitř (k východu, vnitřní nádvoří); parapet a líc brány na západ (přední nádvoří)
        bp_ = dict(pz_["brana"]); tp_ = pz_["tloustka"]
        zed2(P, a_, b_, tp_, pz_["koruna_y"], vp_, otvory=[brana_otvor(bp_, Lp_ / 2, B["horni_y"], pz_["koruna_y"])], cimburi=False, parapet=0.9,
             ext0=0, ext1=0, cela=(False, False))
        Gp_ = a_ + dp_ * (Lp_ / 2)
        portal(P, Gp_ - vp_ * (tp_ / 2), -vp_, bp_["sirka"], brana_vyska(bp_, B["horni_y"], pz_["koruna_y"]), B["horni_y"], tp_)
        dlazba(P, Gp_, -vp_, bp_["sirka"], tp_ + 0.2, B["horni_y"] + 0.04)
    # schodiště na ochoz z horního nádvoří
    so = B["schody_ochoz"]; a, b, L, d, vn = U[so["usek"]]
    st = a + d * so["od_m"] + vn * 2.45
    e, _ = schody2(P, st, -d, B["horni_y"], kor, 1.2)
    s_top = so["od_m"] - round((kor - B["horni_y"]) / 0.19) * 0.27
    plosina(P, a + d * (s_top - 0.75) + vn * ((t / 2 + 0.85 + 3.05) / 2), d, 1.5, 3.05 - t / 2 - 0.8, kor)
    mez = {so["usek"]: (s_top - 1.5, s_top + 0.05)}
    if not STIT_SCHODY: mez[iw] = (sproj - 0.8, sproj + 0.8)
    dv = B.get("dvorek")
    if dv and dv.get("dvere_veze"):   # dvorek mezi věží a palácem (Míša 4. 11.: „dveře z věžičky, ať je to místo hradeb přístupné“):
        # dveře z věže v úrovni ochozu na lávku podél jižní stěny věže, lávka ústí na pavlač ochozu úseku 7 (mezera v zábradlí)
        cv_ = V(B["vez"]["stred"]); xd_ = cv_.x + dv["dvere_veze"]["posun"]; zl_ = cv_.z + B["vez"]["rozmer"] / 2 + 0.6
        a7, b7, L7, d7, vn7 = U[7]; s7 = (V((dv["lavka_x0"] + 0.5, zl_)) - a7).dot(d7)
        mez[7] = (s7 - 0.8, s7 + 0.8)
        TR["B_vez_dvorek"] = [bod(cv_ + Vector((xd_ - cv_.x, 0, 1.2)), kor), bod(V((xd_, zl_ - 0.9)), kor), bod(V((xd_, zl_)), kor),
                              bod(V((dv["lavka_x0"] + 0.5, zl_)), kor), bod(pochozi(U, 7, s7), kor), bod(pochozi(U, 8, 3.0), kor)]
    for i in B["ochoz"]["useky"]:
        a, b, L, d, vn = U[i]
        r0, r1 = zabr_konce(U, i, t, B["ochoz"]["useky"])
        mz = ([mez[i]] if i in mez else [])
        iv = usek_v_palaci(a, b)
        if iv: mz.append((iv[0] - 1.0, iv[1] + 1.0))   # ochoz nevede palácem
        ochoz2(P, a, b, t, kor, vn, mezery=mz, r0=r0, r1=r1, lehka=True)   # prkna na pokos v rozích (Míša 4. 11.: B pořád křížem)
    a, b, L, d, vn = U[so["usek"]]; yd, yh = B["dolni_y"], B["horni_y"]; zz = Vector((0, 0, 1))
    if sts is not None:
        TR["B_vstup"] = [bod(zac - (G - zac).normalized() * 8.0), bod(zac - (G - zac).normalized() * 1.2), bod(zac, m["nastup_y"]), bod(zac.lerp(G, 0.5)), bod(G - vnG * (t / 2), yd), bod(G, yd),
                         bod(G + vnG * 3), bod(sts - zz * 0.8, yd), bod(sts + zz * 2.6, yh), bod(V(((xs[0] + xs[1]) / 2, zt + 1.5)), yh)]
        v0_ = [bod(V(((xs[0] + xs[1]) / 2, zt + 1.5)), yh)]
    else:   # parkán od brány k bráně vnitřního nádvoří (půdorys gc_00)
        TR["B_vstup"] = [bod(zac - (G - zac).normalized() * 8.0), bod(zac - (G - zac).normalized() * 1.2), bod(zac, m["nastup_y"]), bod(zac.lerp(G, 0.5)), bod(G - vnG * (t / 2), yd), bod(G, yd),
                         bod(G + vnG * 2.5)] + [bod(V(q)) for q in B.get("parkan_body", [])] + ([bod(Gp_ - vp_ * 2.0, yh), bod(Gp_, yh), bod(Gp_ + vp_ * 2.0, yh)] if Gp_ is not None else [])
        v0_ = [bod(Gp_ - vp_ * 2.0, yh)] if Gp_ is not None else []   # přední nádvoří (schody na ochoz jsou na Z hradbě)
    TR["B_ochoz_vez"] = v0_ + ([bod(Gp_ - vp_ * 2.0, yh), bod(Gp_, yh), bod(Gp_ + vp_ * 2.0, yh)] if (Gp_ is not None and sts is not None) else []) + [bod(st + d * 1.2), bod(st, yh), bod(e, kor),
                         bod(a + d * (s_top - 0.75) + vn * ((t / 2 + 0.85 + 3.05) / 2), kor), bod(pochozi(U, so["usek"], s_top - 0.75), kor),
                         *[bod(roh(U, k_), kor) for k_ in B.get("ochoz_rohy", [1, 0, 10, 9, 8])]] + ([] if STIT_SCHODY else [bod(pochozi(U, iw, sproj), kor), bod(lav0, kor), bod(c, kor)])
    q = (w - 2 * tv) / 2 - 0.4   # střed rohové podesty od středu věže
    nahoru = [bod(c, kor)]
    for (sa, se, sdir, y0, y1) in (ram_b[1:] if hl else ram_b):   # vstupní patro -> strážní patra -> podkroví: přes volný střed patra k nástupu
        bok = (c - se) - sdir * (c - se).dot(sdir); bok.y = 0; bok = bok.normalized()   # z rohové podesty kolmo od stěny, mimo otvor
        nahoru += [bod(c, y0), bod(sa - sdir * 0.5, y0), bod(sa + sdir * 0.8), bod(se + sdir * 0.5, y1), bod(se + sdir * 0.5 + bok * 1.4, y1)]
    TR["B_vez_nahoru"] = nahoru
    sa, se, sdir, y0, y1 = ram_b[0]   # dolů do skladu (jen shora, po schodech)
    of_ = (c - se) - sdir * (c - se).dot(sdir); of_.y = 0; of_ = of_.normalized()   # od stěny ke středu (budova je obdélník, ne čtverec)
    if hl: TR["B_vez_sklep"] = [bod(c, kor), bod(se + sdir * 0.5 + of_ * 1.0, kor), bod(se + sdir * 0.5, kor), bod(se - sdir * 0.3, y1), bod(sa + sdir * 0.3),
                         bod(sa - sdir * 0.5, y0), bod(c + Vector((0, 0, 0.5)), y0)]
    return G

def stavba(suf):
    H.TRAMY.clear(); POCH.clear(); ZABR.clear(); SCHODY.clear(); BUDOVY.clear(); STUPNE.clear(); portaly.ZAZNAM.clear()
    if _DBG and suf == "_daleko":
        x_, z_, y_ = map(float, _DBG.split(",")); q_ = Vector((x_, y_, z_))
        for c_, sz_, kdo in _DBGL:
            if (c_ - q_).length < 2.0 + max(sz_) / 2: print("DBGKOL", [round(v, 2) for v in (c_.x, c_.z, c_.y)], [round(v, 2) for v in sz_], kdo)
    import bpy
    SV.clear(); TR.clear(); STAVBY.clear(); lib.MOVABLE.clear()
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    PA = Part("hrad_A"); postav_A(PA)
    PB = Part("hrad_B"); postav_B(PB)
    if suf == "":   # kolizní kvádry jako neprůhledné clony pro rozbor viditelnosti (nastroje/viditelnost.py, scény)
        kv = []
        for Pt in (PA, PB):
            for m, sz in Pt.cols:
                if sz[1] < 2.0 or min(sz[0], sz[2]) < 0.3: continue   # jen zdivo: zábradlí a výplně pod schody nejsou zeď (dělaly „patu zdi“ kolem schodů a mostů – Míša 4. 11.)
                c = m.translation; rohy = [m @ Vector((sx * sz[0] / 2, 0, sz2 * sz[2] / 2)) for sx, sz2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                kv.append({"vrch": round(c.y + sz[1] / 2, 2), "rohy": [[round(q.x, 2), round(q.z, 2)] for q in rohy]})
        json.dump({"popis": "půdorysy budov (puchart_hrad.budova_k) – stavby_vegetace bez porostu uvnitř", "budovy": BUDOVY},
                  open(os.path.join(K, "hra/data/stavby_pudorysy.json"), "w"))
        json.dump({"popis": "kolizní kvádry hradů vyšší než 1 m (zdi, věže, budovy) – clony pro rozbor viditelnosti", "kvadry": kv},
                  open(os.path.join(K, "hra/data/stavby_clony.json"), "w"))
    json.dump({"popis": "díry v terénu (studna) – evidence pro hlídače; otvor v síti terénu dělá teren_dlazdice.dira z hrad_puchart.json", "diry": H.DIRY},
              open(os.path.join(K, "hra/data/diry_terenu.json"), "w"), ensure_ascii=False, indent=1)
    if suf == "": hrany_a_zabradli([PA, PB])
    VZ = json.load(open(os.path.join(K, "pravidla/svet/hrad_vzhled.json")))
    if os.environ.get("PUCHART_DBGB"):   # ladění: které kolizní kvádry obsahují bod (x, z, y)
        qx_, qz_, qy_ = [float(v_) for v_ in os.environ["PUCHART_DBGB"].split(",")]
        for Pq in (PA, PB):
            for m_, sz_ in Pq.cols:
                l_ = m_.inverted() @ Vector((qx_, qy_, qz_))
                if all(abs(l_[k]) <= sz_[k] / 2 + 0.05 for k in range(3)): print("DBGB", Pq.name if hasattr(Pq, "name") else "", [round(v_, 2) for v_ in m_.translation], sz_, flush=True)
    H.uloz([PA, PB], "puchart" + suf, kolize=(suf == ""), vzhled=VZ if suf == "" else None)
    if suf == "":
        cc = json.load(open(os.path.join(K, "pravidla/svet/cesty_puchart.json")))
        for k_ in ("A_vstup", "B_vstup"):   # ven branou (Míša 4. 11.: „ve vstupu do dolního hradu jsem nemohl vyjít, u země překážka“)
            if k_ in TR: TR[k_ + "_ven"] = TR[k_][::-1][:-2]   # ven po nástup na most (dál ruční body vstupu mimo pěšinu, přímka přes kraj skály)
        TR["cesta_mezi_hrady"] = [[p[0], p[1], None] for p in next(c for c in cc["cesty"] if c["id"] == "hrebenova")["osa"]] + [TR["B_vstup"][2]]
        json.dump({"popis": "pohyblivé díly (kit.movable): uzel Pohyb_* je ve glb OTEVŘENÝ; zavřený = otočení o −open° kolem místní osy Y (pant). "
                   "cols = kolize v místních souřadnicích uzlu, use = místo ovládání (svět). Čte hra/scripts/dvere.gd.",
                   "dily": [{k: e[k] for k in ("name", "kind", "group", "cols", "use", "open", "dur") if k in e} for e in lib.MOVABLE]},
                  open(os.path.join(K, "hra/data/pohyb.json"), "w"), ensure_ascii=False)
        json.dump({"popis": "trámy hradu (Part.beam) pro hlídač tesařských spojů nastroje/kontrola_spoju.py: [střed xyz, osy 3×3 (sloupce), poloviční rozměry, materiál, díl]",
                   "tramy": [[[round(x, 4) for x in c], [[round(bs[r][k], 5) for r in range(3)] for k in range(3)], [round(x, 4) for x in hs], m_, dn]
                             for c, bs, hs, m_, dn in H.TRAMY]}, open(os.path.join(K, "build/tramy.json"), "w"))
        vad_ = []   # hlídač schodů (Míša 4. 11.: „schody začínají nebo končí moc blízko stěny, malý průchod, ne pansky“):
        for a_, d_, y0_, y1_, run_, w_, kam_ in SCHODY:   # před nástupem a za výstupem 1,0 m volna v šířce ramene
            s_ = d_.cross(UP).normalized()
            for jm_, base_, sm_ in (("nastup", a_ + UP * (y0_ + 1.0), -1), ("vystup", a_ + d_ * run_ + UP * (y1_ + 1.0), 1)):
                body_ = [base_ + d_ * (sm_ * t_) + s_ * u_ for t_ in (0.3, 0.6, 0.9) for u_ in np.linspace(-w_ / 2 + 0.1, w_ / 2 - 0.1, 4)]
                zz_ = [any(_v_kvadru(m, sz, q) for m, sz in PA.cols + PB.cols if sz[1] > 1.5 and (m.translation - q).length < 0.87 * sum(sz) / 2 + 0.1) for q in body_]
                if any(zz_):
                    q_ = body_[zz_.index(True)]; bl_ = next((m, sz) for m, sz in PA.cols + PB.cols if sz[1] > 1.5 and _v_kvadru(m, sz, q_))
                    vad_.append({"kde": jm_, "bod": [round(base_.x, 2), round(base_.z, 2), round(base_.y - 1.0, 2)], "blokovano": sum(zz_),
                                 "zed": [[round(v, 2) for v in (bl_[0].translation.x, bl_[0].translation.z, bl_[0].translation.y)], [round(v, 2) for v in bl_[1]]],
                                 "smer": [round(d_.x, 2), round(d_.z, 2)]})
        json.dump({"popis": "schody: nástup/výstup blokovaný zdivem (puchart_hrad.py SCHODY)", "vady": vad_, "stupne": [[[round(v, 3) for v in p] for p in st] for st in STUPNE]},
                  open(os.path.join(K, "build/schody.json"), "w"), ensure_ascii=False)
        print("SCHODY ramen %d, blokovaný nástup/výstup %d" % (len(SCHODY), len(vad_)), flush=True)
        json.dump({"popis": "zdi zed2 jako jedna síť (stena_sit); max_hrana musí být ≤ relief_krok (jinak reliéf dělí hrany = T-spoje, černé čáry)",
                   "relief_krok": RELIEF_KROK, "zdi": ZDI_SIT}, open(os.path.join(K, "build/zdi.json"), "w"), ensure_ascii=False)
        json.dump({"popis": "portály (blender/portaly.py): místo, směr ven, rozměry – snímky zblízka a hlídač portálů", "portaly": portaly.ZAZNAM},
                  open(os.path.join(K, "build/portaly.json"), "w"), ensure_ascii=False, indent=0)
        json.dump({"popis": "záznamy staveb pro test smyslu (blender/puchart_hrad.py)", "stavby": STAVBY}, open(os.path.join(K, "hra/data/stavby_kontrola.json"), "w"), ensure_ascii=False)
        # denní světlo z oken: jedno na shluk oken do 4 m (≈ místnost), bez stínů (rozhodnutí 9. 11.: „světlo z oken“)
        shl_ = []
        for q_ in H.OKNA_SVETLA:
            for g_ in shl_:
                if (g_[0] / g_[1] - q_).length < 4.0: g_[0] += q_; g_[1] += 1; break
            else: shl_.append([q_.copy(), 1])
        for g_ in shl_:
            q_ = g_[0] / g_[1]; SV.append({"pos": [round(q_.x, 2), round(q_.y, 2), round(q_.z, 2)], "energie": 1.2 + 0.3 * min(g_[1], 3), "dosah": 8.0, "den": True})
        print("světel z oken", len(shl_), "z oken", len(H.OKNA_SVETLA))
        json.dump({"popis": "nástupy mostů [x, z, y, směr ven x, z] – cesty.py zvedne konec cesty na y (Míša 9. 11.: nájezd jako hranol)", "nastupy": NASTUPY, "nabehy": NABEHY},
                  open(os.path.join(K, "hra/data/nastupy_mostu.json"), "w"), ensure_ascii=False)
        json.dump({"popis": "Pochodně (OmniLight3D bez stínů) ve věžích, hladomorně a sklepě – generuje blender/puchart_hrad.py.", "svetla": SV},
                  open(os.path.join(K, "hra/data/svetla.json"), "w"), ensure_ascii=False, indent=1)
        json.dump({"popis": "Trasy testu průchodu (generuje blender/puchart_hrad.py ze stejné geometrie jako hrad): body [x, z, y_podlahy|null], "
                   "postava jde po přímkách, musí dojít ke každému bodu (±0,6 m) ve výšce podlahy (±0,5 m).", "trasy": TR},
                  open(os.path.join(K, "hra/data/pruchody.json"), "w"), ensure_ascii=False, indent=1)

for det, suf in ((True, ""), (False, "_daleko")):
    R.seed(1393); H.nastav_detail(det)
    stavba(suf)
