"""Rybnik Lhota v2 z jednoho zaznamu (Misa 15. 11. r. 13: „pritok a odtok porad spatne… nechces si udelat komplet novy
model? nechám na tobe“; rozbor docs/rozpracovane/misa_15_11_chyby.md r. 13).

Planovac pocita z cisel zaznamu voda.json rybnik_lhota (hladina, hloubka, hraz, vtok/vypust/preliv/pozerak/lavka
parametry) odvozena mista - nic neni v kodu jako vlastni cislo:
  obrys   kraj vody: tvar rybnika (puvodni okraj_vlny, pri dalsim behu ulozeny obrys) oriznuty vodni carou hraze (kde
          navodni svah hraze protne hladinu) a u vtoku rovny kus kolmo na pritok (vtok.rovny_kraj_m)
  vtok    bod na obrysu nejblize kotve pritoku (bod osy lhota_potok vtok.prima_m od kraje) -> smer kotva->bod je
          kolmy na kraj (nejblizsi bod); osa pritoku od kotvy rovne do vtoku po 1 m; hladina pritoku od posledniho bodu
          aspon vtok.spad_od_m nad rybnikem linearne na hladinu + vtok.skok_m ve vtoku (driv 15 m vodorovne 2 cm nad
          rybnikem a podel brehu - cerny mnohouhelnik pres koryto)
  vypust  osa trouby kolmo pod hrazi pres prvni bod puvodni osy odtoku; lice cela tam, kde vzdusny svah hraze je
          vypust.celo_vyska_m nad hladinou odtoku; odtok zacina vypust.zacatek_m za licem (test smyslu vypust <= 1 m)
  pozerak na navodnim svahu hraze v ose trouby, pozerak.od_vodni_cary_m do vody
  lavka   kolmo do vody z bodu obrysu nejblize smeru k vsi (lokace ves stred_stare_navsi), mimo hraz
  python3 tools/krok_b/rybnik_v2.py            vypis
  python3 tools/krok_b/rybnik_v2.py --zapis    zapise rybnik_lhota, lhota_potok a lhota_odtok (jen tyto zaznamy)"""
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VP = os.path.join(ROOT, "pravidla", "svet", "voda.json")


def nacti():
    with open(VP, encoding="utf-8") as f:
        return f.read()


def usek_objektu(txt, start):
    """(zacatek, konec) objektu {...}, ktery zacina na indexu start (znak '{'), s ohledem na retezce."""
    hl = 0
    i = start
    v_ret = False
    while i < len(txt):
        c = txt[i]
        if v_ret:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                v_ret = False
        elif c == '"':
            v_ret = True
        elif c == "{":
            hl += 1
        elif c == "}":
            hl -= 1
            if hl == 0:
                return start, i + 1
        i += 1
    raise ValueError("neuzavreny objekt")


def nahrad_objekt(txt, kotva_re, novy, odsazeni):
    """Nahradi objekt najity regexem kotva_re (konci na '{' nebo v nem lezi "id": ...) - zbytek souboru beze zmeny
    (soubor je misty rucne formatovany, ostatni zaznamy pisi jine planovace)."""
    m = re.search(kotva_re, txt)
    if not m:
        raise ValueError("nenalezeno: " + kotva_re)
    i = txt.rfind("{", 0, m.end())
    a, b = usek_objektu(txt, i)
    s = json.dumps(novy, ensure_ascii=False, indent=1)
    s = s.replace("\n", "\n" + " " * odsazeni)
    return txt[:a] + s + txt[b:]


def seg_d(px, pz, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dz * dz or 1e-12
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (pz - a[1]) * dz) / L))
    return math.hypot(px - a[0] - dx * t, pz - a[1] - dz * t), (a[0] + dx * t, a[1] + dz * t)


def nejblizsi(pts, px, pz):
    best = None
    n = len(pts)
    for k in range(n):
        d, q = seg_d(px, pz, pts[k], pts[(k + 1) % n])
        if best is None or d < best[0]:
            best = (d, q, k)
    return best


def uvnitr(pts, x, z):
    u = False
    n = len(pts)
    for k in range(n):
        (ax, az), (bx, bz) = pts[k], pts[(k + 1) % n]
        if (az > z) != (bz > z) and x < ax + (z - az) * (bx - ax) / (bz - az):
            u = not u
    return u


def plan(V):
    R = V["rybnik_lhota"]
    cx, cz = R["stred"]
    hl = R["hladina_y"]
    hz = R["hraz"]
    vt, vy, pz_, pr, lv = R["vtok"], R["vypust"], R["pozerak"], R["preliv"], R["lavka"]
    potok = next(t for t in V["toky"] if t["id"] == vt["tok"])
    odtok = next(t for t in V["toky"] if t["id"] == vy["tok"])
    # ramec hraze: u po ose, n po proudu (od rybnika)
    ux, uz = hz["smer_osy"]
    L = math.hypot(ux, uz)
    ux, uz = ux / L, uz / L
    nx, nz = -uz, ux
    if (hz["stred"][0] - cx) * nx + (hz["stred"][1] - cz) * nz < 0.0:
        nx, nz = -nx, -nz
    hx, hz0 = hz["stred"]
    t_voda = -(hz["koruna_sirka_m"] / 2.0 + hz["koruna_nad_hladinou_m"] / hz["sklon_svahu"])   # vodni cara navodniho svahu

    # 1) tvar: ulozeny obrys (opakovany beh) nebo puvodni polomer s vlnami
    N = int(R["obrys_bodu"])
    if "obrys" in R and len(R["obrys"]) >= 8:
        zakl = [tuple(p) for p in R["obrys"]]

        def r_tvar(a):
            dx, dz = math.cos(a), math.sin(a)
            best = None
            for k in range(len(zakl)):
                (ax, az), (bx, bz) = zakl[k], zakl[(k + 1) % len(zakl)]
                ex, ez = bx - ax, bz - az
                den = dx * ez - dz * ex
                if abs(den) < 1e-12:
                    continue
                t = ((ax - cx) * ez - (az - cz) * ex) / den
                s = ((ax - cx) * dz - (az - cz) * dx) / den
                if t > 0 and -1e-9 <= s <= 1 + 1e-9 and (best is None or t < best):
                    best = t
            return best
    else:
        def r_tvar(a):
            return R["polomer_m"] * (1.0 + sum(v[1] * math.sin(v[0] * a + v[2]) for v in R.get("okraj_vlny", [])))
    pts = []
    for k in range(N):
        a = 2 * math.pi * k / N
        r = r_tvar(a)
        dx, dz = math.cos(a), math.sin(a)
        # paprsek x vodni cara hraze (t = t_voda) v delce hraze
        dn = dx * nx + dz * nz
        if dn > 1e-6:
            tt = (t_voda - ((cx - hx) * nx + (cz - hz0) * nz)) / dn
            if 0 < tt < r:
                ax_ = (cx + dx * tt - hx) * ux + (cz + dz * tt - hz0) * uz
                if abs(ax_) <= hz["delka_m"] / 2.0:
                    r = tt
        pts.append((cx + dx * r, cz + dz * r))

    # 2) vtok: kotva = prvni bod osy pritoku (od pramene), ktery je vtok.prima_m od kraje nebo bliz; bod = nejblizsi bod
    # obrysu (smer kotva -> bod je kolmy na kraj)
    o = [list(p) for p in potok["osa_xzy"]]
    # pri opakovanem behu je konec osy uz rovny kus - kotva se hleda na ose bez nej (puvodni body pred vtokem)
    if "bod" in vt:
        while len(o) > 2 and math.hypot(o[-1][0] - vt["bod"][0], o[-1][1] - vt["bod"][1]) < vt["prima_m"] - 0.5:
            o.pop()
    ik = next(i for i in range(len(o)) if nejblizsi(pts, o[i][0], o[i][1])[0] <= vt["prima_m"] or uvnitr(pts, o[i][0], o[i][1]))
    if uvnitr(pts, o[ik][0], o[ik][1]):
        ik -= 1
    kot = o[ik]
    d0, V0, kseg = nejblizsi(pts, kot[0], kot[1])
    sx, sz = (V0[0] - kot[0]) / d0, (V0[1] - kot[1]) / d0          # smer do rybnika
    # rovny kraj u vtoku: body obrysu do rovny_kraj_m od vtoku na tecnu (kolmo na smer), vtok jako vrchol
    tx, tz = -sz, sx
    nove = []
    for (x, z) in pts:
        if math.hypot(x - V0[0], z - V0[1]) < vt["rovny_kraj_m"]:
            continue
        nove.append((x, z))
    # vlozit vrcholy rovneho kraje na misto vynechanych (podle uhlu od stredu)
    rk = vt["rovny_kraj_m"]
    vlozit = [(V0[0] + tx * s, V0[1] + tz * s) for s in (-rk, 0.0, rk)]
    vse = nove + vlozit
    vse.sort(key=lambda p: math.atan2(p[1] - cz, p[0] - cx) % (2 * math.pi))
    pts = vse
    # osa pritoku: puvodni body do kotvy, pak rovne po 1 m do vtoku; hladina
    tail = []
    s_ = 1.0
    while s_ < d0 - 0.3:
        tail.append([kot[0] + sx * s_, kot[1] + sz * s_])
        s_ += 1.0
    tail.append([V0[0], V0[1]])
    osa = [p[:] for p in o[:ik + 1]] + [[p[0], p[1], 0.0] for p in tail]
    cil = hl + vt["skok_m"]
    # kotva hladiny: posledni puvodni bod aspon spad_od_m nad rybnikem (driv vodorovny konec o 2 cm vys)
    j0 = max(i for i in range(ik + 1) if osa[i][2] >= hl + vt["spad_od_m"])
    sl = [0.0]
    for i in range(j0 + 1, len(osa)):
        sl.append(sl[-1] + math.hypot(osa[i][0] - osa[i - 1][0], osa[i][1] - osa[i - 1][1]))
    y0 = osa[j0][2]
    for k, i in enumerate(range(j0, len(osa))):
        osa[i][2] = y0 + (cil - y0) * sl[k] / sl[-1]
    osa = [[round(p[0], 3), round(p[1], 3), round(p[2], 3)] for p in osa]

    # 3) vypust: osa trouby kolmo na hraz pres prvni bod puvodni osy odtoku
    od = [list(p) for p in odtok["osa_xzy"]]
    y_vyp = od[0][2]
    ref = vy.get("osa_bod", od[0][:2])
    a0 = (ref[0] - hx) * ux + (ref[1] - hz0) * uz
    t_celo = hz["koruna_sirka_m"] / 2.0 + (hl + hz["koruna_nad_hladinou_m"] - (y_vyp + vy["celo_vyska_m"])) / hz["sklon_svahu"]
    celo = (hx + ux * a0 + nx * t_celo, hz0 + uz * a0 + nz * t_celo)
    zac = (celo[0] + nx * vy["zacatek_m"], celo[1] + nz * vy["zacatek_m"])
    # puvodni body odtoku pred zacatkem (v ramci trouby t < t zacatku + 1 m) pryc, novy zacatek a rovny kus po 1 m
    tz_ = lambda p: (p[0] - hx) * nx + (p[1] - hz0) * nz
    k1 = next(i for i in range(len(od)) if tz_(od[i]) > t_celo + vy["zacatek_m"] + 1.0)
    b = od[k1]
    dl = math.hypot(b[0] - zac[0], b[1] - zac[1])
    hlava = [[zac[0], zac[1], y_vyp]]
    s_ = 1.0
    while s_ < dl - 0.5:
        hlava.append([zac[0] + (b[0] - zac[0]) * s_ / dl, zac[1] + (b[1] - zac[1]) * s_ / dl, y_vyp])
        s_ += 1.0
    osa_od = [[round(p[0], 3), round(p[1], 3), round(min(p[2], y_vyp), 3)] for p in hlava] + od[k1:]

    # 4) pozerak na navodnim svahu v ose trouby
    t_poz = t_voda - pz_["od_vodni_cary_m"]
    poz = (hx + ux * a0 + nx * t_poz, hz0 + uz * a0 + nz * t_poz)

    # 5) lavka: bod obrysu nejblize smeru k vsi, mimo hraz (osa hraze +- delka/2 + lavka.od_hraze_m)
    ves = V["_ves_stred"]
    av = math.atan2(ves[1] - cz, ves[0] - cx)
    kand = []
    for k in range(len(pts)):
        (ax, az), (bx, bz) = pts[k], pts[(k + 1) % len(pts)]
        mx, mz = (ax + bx) / 2, (az + bz) / 2
        a_h = (mx - hx) * ux + (mz - hz0) * uz
        t_h = (mx - hx) * nx + (mz - hz0) * nz
        if abs(a_h) < hz["delka_m"] / 2.0 + lv["od_hraze_m"] and t_h > t_voda - 6.0:
            continue
        if math.hypot(mx - V0[0], mz - V0[1]) < 8.0:
            continue
        da = abs((math.atan2(mz - cz, mx - cx) - av + math.pi) % (2 * math.pi) - math.pi)
        kand.append((da, k, (mx, mz), (-(bz - az), bx - ax)))
    _, kl, lb, ln = min(kand)
    Ln = math.hypot(*ln)
    ln = (ln[0] / Ln, ln[1] / Ln)
    if not uvnitr(pts, lb[0] + ln[0] * 0.5, lb[1] + ln[1] * 0.5):
        ln = (-ln[0], -ln[1])

    # preliv: posun od osy trouby k prostredku hraze (koryto prelivu na hrazi, ne za jejim koncem)
    posun = abs(pr["posun_m"]) * (-1.0 if a0 > 0 else 1.0)
    obal = max(math.hypot(x - cx, z - cz) for x, z in pts)
    return {
        "obrys": [[round(x, 2), round(z, 2)] for x, z in pts],
        "polomer_m": round(obal, 2),
        "vtok": {"bod": [round(V0[0], 3), round(V0[1], 3)], "smer": [round(sx, 4), round(sz, 4)]},
        "vypust": {"celo": [round(celo[0], 3), round(celo[1], 3)], "smer": [round(nx, 4), round(nz, 4)], "hladina_y": round(y_vyp, 3),
                   "osa_bod": [round(ref[0], 3), round(ref[1], 3)]},
        "pozerak": {"bod": [round(poz[0], 3), round(poz[1], 3)]},
        "preliv": {"posun_m": round(posun, 3)},
        "lavka": {"bod": [round(lb[0], 3), round(lb[1], 3)], "smer": [round(ln[0], 4), round(ln[1], 4)]},
        "potok_osa": osa, "odtok_osa": osa_od, "kotva": (ik, j0, d0),
    }


if __name__ == "__main__":
    txt = nacti()
    V = json.loads(txt)
    L = json.load(open(os.path.join(ROOT, "pravidla", "svet", "lokace.json"), encoding="utf-8"))
    V["_ves_stred"] = L["ves"].get("stred_stare_navsi", L["ves"].get("stred"))
    p = plan(V)
    R = V["rybnik_lhota"]
    ik, j0, d0 = p["kotva"]
    print("obrys %d bodu, obal %.2f m" % (len(p["obrys"]), p["polomer_m"]))
    print("vtok %s smer %s: kotva bod %d (%.1f m od kraje), hladina od bodu %d -> %.3f" % (
        p["vtok"]["bod"], p["vtok"]["smer"], ik, d0, j0, R["hladina_y"] + R["vtok"]["skok_m"]))
    print("pritok konec:", p["potok_osa"][-8:])
    print("vypust celo %s, hladina odtoku %.3f, odtok zacina %s" % (p["vypust"]["celo"], p["vypust"]["hladina_y"], p["odtok_osa"][:3]))
    print("pozerak %s, lavka %s smer %s" % (p["pozerak"]["bod"], p["lavka"]["bod"], p["lavka"]["smer"]))
    if "--zapis" in sys.argv:
        R["obrys"] = p["obrys"]
        R["polomer_m"] = p["polomer_m"]
        for k in ("vtok", "vypust", "pozerak", "preliv", "lavka"):
            R[k].update(p[k])
        for k in ("okraj_vlny", "voda_polomer_m", "tok_konec_polomer_m", "_tok_konec_polomer_m", "dil", "breh"):
            R.pop(k, None)
        txt = nahrad_objekt(txt, r'\n "rybnik_lhota": \{', R, 1)
        for tid, osa in (("lhota_potok", p["potok_osa"]), ("lhota_odtok", p["odtok_osa"])):
            t = next(t for t in V["toky"] if t["id"] == tid)
            t["osa_xzy"] = osa
            txt = nahrad_objekt(txt, r'\{\s*"id": "%s"' % tid, t, 2)
        json.loads(txt)
        open(VP, "w", encoding="utf-8").write(txt)
        print("zapsano", VP)
