"""Kamenné portály bran a dveří Purchartu (Míša 4. 11.: hranaté oblouky z pár kvádrů, kameny ostění trčí, do oblouku leze
zeď, „díry“ vedle oblouku, vrata vrostlá do ostění). Pravidla pravidla/svet/portaly.json, reference
docs/reference/detaily_hradu_1393.md.

Jeden díl řeší celý otvor ve zdi tloušťky D (lokálně: x napříč, y nahoru od prahu, z ven z líce; líc z = 0, zeď do z = −D):
  * ostění (stojky) a záklenek z klenáků v líci zdi (výstupek 1 cm / 4,5 cm v omítce), sražená hrana do otvoru,
    oblouk hladký (každý klenák má zakřivené podhledí, ~0,32 m po oblouku);
  * za ostěním polodrážka: otvor širší o 'polodrazka_m' na každou stranu, klenba průchodu stejného tvaru (lomená/půlkruhová
    valená klenba) přes celou tloušťku zdi – nikde rovný strop pod obloukem;
  * výplň zdiva mezi obdélníkovým otvorem zdi (otvor(): W × H) a obloukem – na líci zarovnaná se zdí (UV světové,
    hrady.svet_uv), takže žádné díry a švy;
  * křídla v polodrážce za ostěním, pant odsazený o tloušťku křídla – otevřené leží podél boku průchodu, ne ve zdi.
Volající udělá ve zdi obdélníkový otvor otvor(w, h, top) a zavolá doorway() se stejnými w, h, top.
"""
import json, math, os
from mathutils import Vector, Matrix
import kit
from kit import M, RND

K = os.environ.get("PUCHART_K") or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PR = json.load(open(os.path.join(K, "pravidla/svet/portaly.json")))
LK = PR["lomeny_polomer_k_polovine_sirky"]
ZAZNAM = []   # každý portál (snímky zblízka – hlídač portálů, build/portaly.json)


def _kruhy(top, w, spring):
    """Středy a poloměry oblouku podhledí: [(cx, cy, r)] pro x < 0 a x >= 0."""
    hw = w / 2
    if top == "lomeny":
        r = hw * LK
        return (hw - r if False else -hw + r, spring, r), (hw - r, spring, r)
    if top == "pulkruh":
        return (0.0, spring, hw), (0.0, spring, hw)
    if top == "segment":
        rise = segment_vzepeti(w)
        R = (hw * hw + rise * rise) / (2 * rise)
        return (0.0, spring - (R - rise), R), (0.0, spring - (R - rise), R)
    return None


def segment_vzepeti(w):
    return max(0.12, w * 0.16)   # segmentový záklenek: vzepětí ~1/6 světlosti (sklepní a branné dveře 14. st.)


def podhledi(top, w, spring):
    """y(x) podhledí otvoru světlosti w (x v <-w/2, w/2>)."""
    kr = _kruhy(top, w, spring)
    if kr is None:
        return lambda x: spring
    def f(x):
        cx, cy, r = kr[0] if x < 0 else kr[1]
        return cy + math.sqrt(max(0.0, r * r - (x - cx) ** 2))
    return f


def patka(top, w, h):
    """Výška patky oblouku tak, aby vrchol podhledí byl přesně h (dřív lomený přerostl h o 0,35·w/2 – do oblouku lezla zeď)."""
    hw = w / 2
    if top == "lomeny":
        return h - hw * math.sqrt(LK * LK - (LK - 1) ** 2)
    if top == "pulkruh":
        return h - hw
    if top == "segment":
        return h - segment_vzepeti(w)
    return h


def otvor(w, h, top):
    """Obdélníkový otvor ve zdi pro portál: (šířka W, výška H nad prahem)."""
    W = w + 2 * PR["polodrazka_m"]
    sp = patka(top, w, h)
    H = podhledi(top, W, sp)(0.0) + PR["rezerva_otvoru_nad_obloukem_m"]
    return W, H


def nadvyseni_vence(top, w, h, ring=None):
    """O kolik je rub záklenku (věnec) nad vrcholem podhledí – pro omezení výšky brány pod korunou."""
    ring = ring or PR["venec_m"]; sp = patka(top, w, h)
    return _venec(top, w, sp, ring)(0.0) - h if top != "rovny" else ring


def _venec(top, w, spring, ring):
    """Rub záklenku: soustředné kružnice o ring větší."""
    kr = _kruhy(top, w, spring)
    if kr is None:
        return lambda x: spring + ring
    def f(x):
        cx, cy, r = kr[0] if x < 0 else kr[1]
        R = r + ring
        return cy + math.sqrt(max(0.0, R * R - (x - cx) ** 2))
    return f


def _normala(top, w, spring, p):
    kr = _kruhy(top, w, spring)
    if kr is None:
        return Vector((0, 1, 0))
    cx, cy, r = kr[0] if p.x < 0 else kr[1]
    v = Vector((p.x - cx, p.y - cy, 0.0))
    return v.normalized() if v.length > 1e-9 else Vector((0, 1, 0))


def _strip(P, m, inner, outer, z0, z1, mat, ch=0.0, nrm=None):
    """Kámen: 2D obrys (inner = body podhledí zleva doprava, outer = body rubu zleva doprava) vytažený z z0 (líc) do z1.
    ch = sražení hrany podhledí na líci (body inner posunuté po nrm o ch na líci, v z0 − ch původní)."""
    n = len(inner)
    fr = [(p + (nrm[i] * ch if ch > 0 else Vector()), z0) for i, p in enumerate(inner)] + [(p, z0) for p in reversed(outer)]
    bk = [(p, z1) for p in inner] + [(p, z1) for p in reversed(outer)]
    V = []
    def add(p, z):
        V.append(Vector((p.x, p.y, z))); return len(V) - 1
    F = [add(p, z) for p, z in fr]
    B = [add(p, z) for p, z in bk]
    mid = [add(p, z0 - ch) for p in inner] if ch > 0 else None
    faces = [list(reversed(F)), list(B)]
    no = len(outer)
    # rub (outer): F[n + j] odpovídá outer[no-1-j]
    for j in range(no - 1):
        a, b = n + j, n + j + 1
        faces.append([F[a], F[b], B[b], B[a]][::-1])
    # podhledí
    for i in range(n - 1):
        if mid:
            faces.append([F[i], F[i + 1], mid[i + 1], mid[i]][::-1])
            faces.append([mid[i], mid[i + 1], B[i + 1], B[i]][::-1])
        else:
            faces.append([F[i], F[i + 1], B[i + 1], B[i]][::-1])
    # čela (spáry)
    e0 = [F[0]] + ([mid[0]] if mid else []) + [B[0], B[n + no - 1], F[n + no - 1]]
    e1 = [F[n - 1], F[n], B[n], B[n - 1]] if not mid else [F[n - 1], F[n], B[n], B[n - 1], mid[n - 1]]
    faces.append(e0[::-1] if True else e0)
    faces.append(e1[::-1] if False else e1)
    P.mesh(V, [tuple(f) for f in faces], mat, m=m)


def zaklenek(P, m, w, spring, top, z0, z1, mat, ring=None, ch=None, delka=None):
    """Klenáky po oblouku podhledí světlosti w – každý se zakřiveným podhledím a rubem (hladký oblouk), lichý počet, závěrák
    uprostřed. Vrací body spár na rubu (pro výplň)."""
    ring = ring or PR["venec_m"]; ch = PR["sraz_hrany_m"] if ch is None else ch; delka = delka or PR["klenak_delka_m"]
    f = podhledi(top, w, spring); g = _venec(top, w, spring, ring); hw = w / 2
    N = 400
    xs = [-hw + w * i / N for i in range(N + 1)]
    pts = [Vector((x, f(x), 0.0)) for x in xs]; pts[0].y = pts[-1].y = spring
    acc = [0.0]
    for i in range(1, len(pts)): acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)
    n = max(5, round(acc[-1] / delka)); n += (n + 1) % 2   # lichý počet
    gap = PR["spara_m"]; S = PR["vzorku_na_klenak"]
    def bod(L):
        j = min(range(len(acc)), key=lambda i: abs(acc[i] - L)); return pts[j]
    for k in range(n):
        La = acc[-1] * k / n + (gap if k else 0.0); Lb = acc[-1] * (k + 1) / n - (gap if k < n - 1 else 0.0)
        inner = [bod(La + (Lb - La) * i / S) for i in range(S + 1)]
        nr = [_normala(top, w, spring, p + Vector((1e-4 if p.x <= -hw + 1e-6 else (-1e-4 if p.x >= hw - 1e-6 else 0), 0, 0))) for p in inner]
        if k == 0: nr[0] = _normala(top, w, spring, Vector((-hw + 1e-4, spring, 0)))
        if k == n - 1: nr[-1] = _normala(top, w, spring, Vector((hw - 1e-4, spring, 0)))
        qa = inner[0] + nr[0] * ring; qb = inner[-1] + nr[-1] * ring
        outer = [Vector((qa.x + (qb.x - qa.x) * i / S, 0, 0)) for i in range(S + 1)]
        outer = [Vector((o.x, g(o.x), 0.0)) for o in outer]
        outer[0] = qa; outer[-1] = qb
        if top == "lomeny" and k == n // 2:   # závěrák: rub s vrcholem uprostřed
            outer = [qa] + [Vector((x, g(x), 0)) for x in (qa.x * 0.5, 0.0, qb.x * 0.5)] + [qb]
        _strip(P, m, inner, outer, z0, z1, mat, ch, nr)
    q0 = Vector((-hw, spring, 0)) + _normala(top, w, spring, Vector((-hw + 1e-4, spring, 0))) * ring
    return q0


def _ostenistojka(P, m, x0, x1, y0, y1, z0, z1, mat, ch, vlevo):
    """Kvádr ostění (stojka) se sraženou hranou do otvoru na líci."""
    xi = x1 if vlevo else x0; xo = x0 if vlevo else x1; s = -1 if vlevo else 1
    sec = [(xi + s * ch, z0), (xo, z0), (xo, z1), (xi, z1), (xi, z0 - ch)]
    pts = [Vector((x, y0, z)) for x, z in sec]
    if s < 0: pts = list(reversed(pts))
    P.prism([m @ p for p in pts], m.to_3x3() @ Vector((0, y1 - y0, 0)), mat)


def vypln(P, m, poly, z0, z1, mat):
    if len(poly) < 3: return
    P.prism([m @ Vector((x, y, z0)) for x, y in poly], m.to_3x3() @ Vector((0, 0, z1 - z0)), mat)


def _nad_krivkou(fun, xa, xb, H, n=24):
    """Polygon oblasti nad křivkou y = fun(x) pro x z xa do xb a pod y = H (CCW při pohledu proti +z)."""
    xs = [xa + (xb - xa) * i / n for i in range(n + 1)]
    ys = [fun(x) for x in xs]
    pts = [(x, y) for x, y in zip(xs, ys) if y < H - 1e-4]
    if not pts: return []
    # průsečík s y = H
    out = []
    for i in range(len(xs)):
        if ys[i] < H - 1e-4:
            if i > 0 and ys[i - 1] >= H - 1e-4:
                t = (H - ys[i - 1]) / (ys[i] - ys[i - 1]); out.append((xs[i - 1] + (xs[i] - xs[i - 1]) * t, H))
            out.append((xs[i], ys[i]))
            if i < len(xs) - 1 and ys[i + 1] >= H - 1e-4:
                t = (H - ys[i]) / (ys[i + 1] - ys[i]); out.append((xs[i] + (xs[i + 1] - xs[i]) * t, H))
    a, b = out[0], out[-1]
    poly = out + ([(b[0], H)] if b[1] < H else []) + ([(a[0], H)] if a[1] < H else [])
    # směr: křivka zleva doprava dole, pak horem zpět – CCW při pohledu z +z
    return poly


def doorway(P, m, kind="hlavni", w=1.1, h=2.2, depth=0.7, top=None, open_deg=None, lattice=False, leaf=True, double=False,
            LP=None, open2=None, inner=True, fill_mat="zdivo", stone_mat="kvadr_okno", proud_max=None, venec_vnitrni=False):
    if top is None:
        top = {"hlavni": "lomeny", "obycejne": "segment", "vnitrni": "rovny"}[kind]
    if kind == "vnitrni":
        return kit._doorway_havran(P, m, kind=kind, w=w, h=h, depth=depth, top=top, open_deg=open_deg or 0.0, lattice=lattice,
                                   leaf=leaf, double=double, LP=LP, open2=open2, inner=False)
    reb = PR["polodrazka_m"]; ring = PR["venec_m"]; ch = PR["sraz_hrany_m"]
    o_ = m.translation; n_ = m.to_3x3() @ Vector((0, 0, 1))
    ZAZNAM.append({"kind": kind, "top": top, "w": round(w, 2), "h": round(h, 2), "hloubka": round(depth, 2),
                   "pos": [round(o_.x, 2), round(o_.y, 2), round(o_.z, 2)], "ven": [round(n_.x, 3), round(n_.z, 3)]})
    jd = min(PR["osteni_hloubka_m"], depth * 0.6)
    pr = PR["osteni_vystupek_m"] if proud_max is None or proud_max < 0.03 else PR["osteni_vystupek_omitka_m"]
    hw = w / 2; sp = patka(top, w, h); W, H = otvor(w, h, top)
    D = depth
    # ostění: stojky po řadách (stálá šíře = věnec, líc v rovině, sražená hrana)
    y = 0.0; k = 0; vy = 0.34 if kind == "hlavni" else 0.3
    q0 = Vector((-hw - ring, sp, 0)) if top != "rovny" else None
    while y < sp - 0.02:
        h_ = min(vy * RND.uniform(0.95, 1.05), sp - y)
        if sp - y - h_ < 0.14: h_ = sp - y
        for vl in (True, False):   # střídavě dlouhý a krátký kvádr (Havran kit.stone_jambs 0,42/0,27; KCD brána Talmberg – Míša 12. 11.)
            rw = ring * (PR["osteni_dlouhy_k"] if (k + (0 if vl else 1)) % 2 == 0 else PR["osteni_kratky_k"])
            x0, x1 = (-hw - rw, -hw) if vl else (hw, hw + rw)
            _ostenistojka(P, m, x0, x1, y + (PR["spara_m"] if k else 0.0), y + h_, pr, -jd, stone_mat, ch, vl)
        y += h_; k += 1
    if top == "rovny":
        L = w + 2 * ring
        kit.stone(P, m @ M((0.0, h + ring / 2, (pr - jd) / 2)), (L, ring, pr + jd), stone_mat, cham=0.02, rough=0.0)
        ext = lambda x: h + ring
    else:
        q0 = zaklenek(P, m, w, sp, top, pr, -jd, stone_mat, ring, ch)
        g = _venec(top, w, sp, ring)
        xq = abs(q0.x)   # nad patkou segmentu: vodorovně nad posledním kvádrem ostění
        if xq < hw + ring - 1e-3:   # segment: patní kámen pod šikmou spárou
            for sx in (-1, 1):
                pts = [(sx * hw, sp), (sx * (hw + ring), sp), (sx * (hw + ring), q0.y), (sx * xq, q0.y)]
                if sx < 0: pts = list(reversed(pts))
                vypln(P, m, pts, pr, -jd, stone_mat)
        ext = lambda x: (g(x) if abs(x) <= xq else q0.y)
    # výplň zdiva v otvoru W × H: před ostěním (z 0..−jd) nad rubem záklenku, za ním (−jd..−D) nad klenbou průchodu
    for sx in (-1, 1):
        a, b = (0.0, W / 2) if sx > 0 else (-W / 2, 0.0)
        poly = _nad_krivkou(ext, a, b, H)
        if poly: vypln(P, m, poly, 0.0, -jd, fill_mat)
    fr = podhledi(top, W, sp) if top != "rovny" else (lambda x: h)
    for sx in (-1, 1):
        a, b = (0.0, W / 2) if sx > 0 else (-W / 2, 0.0)
        poly = _nad_krivkou(fr, a, b, H)
        if poly: vypln(P, m, poly, -jd, -D, fill_mat)
    if venec_vnitrni and top != "rovny":   # vnitřní líc průchodu: záklenek z klenáků tvaru klenby (brány)
        mi = m @ M((0.0, 0.0, -D), 180)
        zaklenek(P, mi, W, sp, top, 0.01, -0.35, stone_mat, ring * 0.9, ch)
    elif inner and D - jd > 0.2:   # kamenné ostění i z vnitřní strany (Havran kit.doorway inner; Míša 12. 11.: „všude chci ostění
        mi = m @ M((0.0, 0.0, -D), 180)   # a dveře jako v Havranovi“ – zevnitř byl holý otvor): stojky kolem otvoru W a záklenek
        jdi = min(PR["osteni_vnitrni_hloubka_m"], (D - jd) * 0.8); pri = PR["osteni_vnitrni_vystupek_m"]; y = 0.0; k = 0
        while y < sp - 0.02:
            h_ = min(vy * RND.uniform(0.95, 1.05), sp - y)
            if sp - y - h_ < 0.14: h_ = sp - y
            for vl in (True, False):
                rw = ring * (PR["osteni_dlouhy_k"] if (k + (0 if vl else 1)) % 2 == 0 else PR["osteni_kratky_k"])
                x0, x1 = (-W / 2 - rw, -W / 2) if vl else (W / 2, W / 2 + rw)
                _ostenistojka(P, mi, x0, x1, y + (PR["spara_m"] if k else 0.0), y + h_, pri, -jdi, stone_mat, ch, vl)
            y += h_; k += 1
        if top == "rovny":
            kit.stone(P, mi @ M((0.0, h + ring / 2, (pri - jdi) / 2)), (W + 2 * ring, ring, pri + jdi), stone_mat, cham=0.02, rough=0.0)
        else:
            zaklenek(P, mi, W, sp, top, pri, -jdi, stone_mat, ring * 0.9, ch)
    kit.threshold(P, m, W, jd + 0.1)
    if not leaf:
        return
    LP = LP or P
    tk = {"hlavni": 0.07, "obycejne": 0.055}[kind]
    zl = -jd - PR["kridlo_za_osteni_m"]
    od = PR["otevreni_stupne"]
    kit.DOOR_N += 1
    gid = "dvere%d" % kit.DOOR_N
    use = m @ Vector((0.0, 1.2, -jd))
    Wl = W - 2 * (tk + 0.01)   # mezi panty (pant odsazený o tloušťku křídla – otevřené leží podél boku, ne ve zdi)
    hl = fr(0.0) - 0.02
    if double:
        hw2 = Wl / 2
        for sx, ang in ((-1, 1), (1, -1)):
            hm = m @ M((sx * (Wl / 2), 0.0, zl))
            def build(Q, sx=sx):
                n0 = len(Q.v); f0 = len(Q.f)
                kit.door_leaf(Q, M((hw2 / 2 - 0.005, 0.0, 0.0)), hw2 - 0.01, hl, kind, top if top != "segment" else "segment", sp - 0.01,
                              lattice, arch_w=W - 0.03, xoff=-hw2 / 2 - (W - Wl) / 2 * 0 )
                if sx > 0:
                    for i in range(n0, len(Q.v)): Q.v[i] = Vector((-Q.v[i].x, Q.v[i].y, Q.v[i].z))
                    for i in range(f0, len(Q.f)):
                        idx, uv, mt, rn, sm = Q.f[i]; Q.f[i] = (list(reversed(idx)), list(reversed(uv)), mt, rn, sm)
            kit.movable("%s_%s" % (gid, "l" if sx < 0 else "p"), "dvere", hm, build,
                        cols=[((-sx * hw2 / 2, hl / 2, -tk / 2), (hw2 - 0.03, hl - 0.04, tk + 0.02))], use=use, group=gid,
                        open=-sx * od, init=0.0, dur=1.1)
    else:
        hm = m @ M((-Wl / 2, 0.0, zl))
        def build(Q):
            kit.door_leaf(Q, M((Wl / 2 - 0.005, 0.0, 0.0)), Wl - 0.01, hl, kind, top, sp - 0.01, lattice, arch_w=W - 0.03,
                          xoff=0.0)
        kit.movable(gid, "dvere", hm, build, cols=[((Wl / 2, hl / 2, -tk / 2), (Wl - 0.04, hl - 0.04, tk + 0.02))], use=use,
                    group=gid, open=od, init=0.0, dur=1.1)
    # panty (kované čepy zazděné v boku polodrážky)
    for sx in ((-1, 1) if double else (-1,)):
        for yb in (0.18 * hl, 0.82 * sp):
            P.rod(m @ Vector((sx * (W / 2 - 0.005), yb - 0.07, zl - tk / 2)), m @ Vector((sx * (W / 2 - 0.005), yb + 0.07, zl - tk / 2)),
                  0.016, 6, "zelezo")
            P.rod(m @ Vector((sx * (W / 2 - 0.005), yb, zl - tk / 2)), m @ Vector((sx * (Wl / 2), yb, zl - tk / 2)), 0.01, 5, "zelezo")
