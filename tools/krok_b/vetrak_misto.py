"""Misto pro vetrny mlyn na samote (lokace.json vetrak, Misa 28. 10.). Krok planu PRED exportem: z terenu pred vodou
(vysky.json) a ze vseho, co ve svete uz stoji (modely/svet.json kolize, protokol cest hry, voda.json toky a rybniky,
lokace.json ves/stavby/ruiny/kompozice.vyhledy, mlyn), hleda navrsi: vyska nad prumerem okoli (okoli_m), rovny vrchol
(max - min v plac_r_m nejvys meze kroku stavby), nic postaveneho do samota_m, voda dal nez od_vody_m, kraj mapy dal
nez kraj_m. Vypise nejlepsi mista; --zapis ulozi stred do lokace.json vetrak.
  python3 tools/krok_b/vetrak_misto.py [--zapis]"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
J = lambda *p: json.load(open(os.path.join(ROOT, *p)))
D = J("tools", "krok_b", "vysky.json")
K, X0, Z0, nx, nz, H = D["K"], D["X0"], D["Z0"], D["nx"], D["nz"], D["h"]
L = J("pravidla", "svet", "lokace.json")
VE = L["vetrak"]
V = J("pravidla", "svet", "voda.json")
S = J("modely", "svet.json")
MEZ = J("pravidla", "pravidla_sveta.json")["pasma"]["test"]["meze_kroku"]["blender: stavby (stavba_pad)"]
MEZ = float(MEZ["max_dy_m"])


def h(i, j):
    return H[j * nx + i]


# --- obsazeno: body vseho postaveneho (mrizka 10 m)
# (kolize sveta ne: jsou v nich i skaly a balvany - priroda, ne stavba; tvrz a lom podle svet.json nazvy/mistnosti)
obs = [(m["pos"][0], m["pos"][2]) for m in S["mistnosti"]] + [(p["pos"][0], p["pos"][2]) for p in S["pohyb"]]
obs += [(m["x"], m["z"]) for m in S["nazvy_mist"]]
try:
    for c in J("build", "protokol_stavby.json")["cesty"]:
        obs += [tuple(p) for p in c[::2]]
except (OSError, ValueError, KeyError):
    pass
obs += [tuple(u["novy_stred"]) for u in L["ves"]["usedlosti"]]
obs += [tuple(e["stred"]) for e in L["stavby"] + L["ruiny"] + L["drobne"]]
obs += [tuple(v["stred"]) for v in L["kompozice"]["vyhledy"]]
obs += [tuple(V["mlyn"]["stred"])]
voda = []
for t in V["toky"]:
    voda += [tuple(p[:2]) for p in t["osa_xzy"][::3]]
voda += [tuple(p) for p in V["potok"]["osa"]]
for k in ("rybnik_tvrz", "rybnik_lhota"):
    voda.append(tuple(V[k]["stred"]))
mriz = {}
for p in obs:
    mriz.setdefault((int(p[0] // 50), int(p[1] // 50)), []).append(p)
vmriz = {}
for p in voda:
    vmriz.setdefault((int(p[0] // 50), int(p[1] // 50)), []).append(p)


def nejbl(m, x, z, r):
    best = 1e9
    n = int(r // 50) + 1
    for a in range(-n, n + 1):
        for b in range(-n, n + 1):
            for p in m.get((int(x // 50) + a, int(z // 50) + b), []):
                best = min(best, math.hypot(p[0] - x, p[1] - z))
    return best


X1, Z1 = X0 + (nx - 1) * K, Z0 + (nz - 1) * K
ro, rp = int(VE["okoli_m"] / K), int(VE["rovina_r_m"] / K)
vys = []
pocty = {"kraj": 0, "samota": 0, "voda": 0, "plac": 0}
for j in range(ro, nz - ro, 2):
    for i in range(ro, nx - ro, 2):
        x, z = X0 + i * K, Z0 + j * K
        if min(x - X0, X1 - x, z - Z0, Z1 - z) < VE["kraj_m"]:
            pocty["kraj"] += 1
            continue
        ds = nejbl(mriz, x, z, VE["samota_m"])
        if ds < VE["samota_m"]:
            pocty["samota"] += 1
            continue
        if nejbl(vmriz, x, z, VE["od_vody_m"]) < VE["od_vody_m"]:
            pocty["voda"] += 1
            continue
        plac = [h(i + a, j + b) for a in range(-rp, rp + 1) for b in range(-rp, rp + 1) if a * a + b * b <= rp * rp]
        rozptyl = max(plac) - min(plac)
        if rozptyl > MEZ:
            pocty["plac"] += 1
            continue
        okoli = [h(i + a, j + b) for a in range(-ro, ro + 1, 2) for b in range(-ro, ro + 1, 2) if a * a + b * b <= ro * ro]
        nad = h(i, j) - sum(okoli) / len(okoli)
        vyssi = sum(1 for v in okoli if v > h(i, j) + 1.0) / len(okoli)     # podil okoli vys nez vrchol (horizont)
        skore = nad - 10.0 * vyssi - 0.5 * rozptyl
        vys.append((round(skore, 2), x, z, round(h(i, j), 1), round(nad, 1), round(vyssi, 2), round(rozptyl, 1), round(ds)))
vys.sort(reverse=True)
print("vyrazeno", pocty)
print("VETRAK mist %d (skore, x, z, vyska, nad okolim, podil vyssiho okoli, rozptyl placu, k nejblizsi stavbe):" % len(vys))
vyb = []
for v in vys:
    if all(math.hypot(v[1] - w[1], v[2] - w[2]) > 80 for w in vyb):
        vyb.append(v)
    if len(vyb) >= 8:
        break
for v in vyb:
    print("VETRAK", v)
# skrin kridly (+z modelu) proti prevladajicimu vetru; chalupa stitem (+z) k mlynu, vstupem (+x) po vetru (zavetri)
w = {"zapad": (-1.0, 0.0), "vychod": (1.0, 0.0), "sever": (0.0, -1.0), "jih": (0.0, 1.0)}[VE["vitr_z"]]
a = math.atan2(-w[0], w[1])
CH = VE["chalupa"]


def rozptyl_kolem(x, z, r):
    i0, j0, rr = int(round((x - X0) / K)), int(round((z - Z0) / K)), int(r / K)
    v = [h(i0 + p, j0 + q) for p in range(-rr, rr + 1) for q in range(-rr, rr + 1) if p * p + q * q <= rr * rr]
    return max(v) - min(v)


SMAX = J("pravidla", "svet", "plochy.json")["teren"]["stavba_max_sklon"]


def svah(x, z, r):
    """Jako test smyslu (stavba na svahu): rozdil vysek na kruhu r (8 smeru, nejblizsi bunka) / 2r."""
    def vy(px, pz):
        return h(max(0, min(nx - 1, int(round((px - X0) / K)))), max(0, min(nz - 1, int(round((pz - Z0) / K)))))
    hs = [vy(x + r * math.cos(k * math.pi / 4), z + r * math.sin(k * math.pi / 4)) for k in range(8)]
    return (max(hs) - min(hs)) / (2 * r)


# mlyn i chalupa: plosina do meze kroku a svah do plochy.json teren.stavba_max_sklon (test smyslu: polomer 0,6 x rovina)
def chalupa_xz(v):
    return v[1] - math.cos(a) * CH["od_mlyna_m"], v[2] - math.sin(a) * CH["od_mlyna_m"]


vyb = [v for v in vys if rozptyl_kolem(*chalupa_xz(v), CH["rovina_r_m"]) <= MEZ and svah(v[1], v[2], VE["rovina_r_m"] * 0.6) <= SMAX
       and svah(*chalupa_xz(v), CH["rovina_r_m"] * 0.6) <= SMAX]
vyb2 = []
for v in vyb:
    if all(math.hypot(v[1] - w_[1], v[2] - w_[2]) > 80 for w_ in vyb2):
        vyb2.append(v)
vyb = vyb2[:8]
print("s chalupou v mezi (skore, x, z, vyska, nad okolim, podil vyssiho okoli, rozptyl, k stavbe):")
for v in vyb:
    print("  ", v)
if "--zapis" in sys.argv and vyb:
    ve = L["vetrak"]
    mx, mz = vyb[0][1], vyb[0][2]
    ve["stred"] = [mx, mz]
    ve["natoceni"] = round(math.atan2(w[0], w[1]), 4)
    ch = ve["chalupa"]
    ch["natoceni"] = round(a, 4)
    ch["stred"] = [round(mx - math.cos(a) * ch["od_mlyna_m"], 2), round(mz - math.sin(a) * ch["od_mlyna_m"], 2)]
    json.dump(L, open(os.path.join(ROOT, "pravidla", "svet", "lokace.json"), "w"), ensure_ascii=False, indent=1)
    print("zapsano lokace.json vetrak: stred %s natoceni %.2f, chalupa %s" % (ve["stred"], ve["natoceni"], ch["stred"]))
    # cesta k_vetraku (cesty.json pesiny, typ vozova): od nejblizsi cesty hry k okraji placu na strane chalupy,
    # tools/krok_b/astar.py, sklon do pasma.cesta.vozova.podelny_max, mimo vodu, domy a rybniky
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    import astar
    C = J("pravidla", "svet", "cesty.json")
    gmax = J("pravidla", "pravidla_sveta.json")["pasma"]["cesta"]["vozova"]["podelny_max"]
    cil = (mx - math.cos(a) * (ve["plac_r_m"] - 1.0) + math.sin(a) * 4.0, mz - math.sin(a) * (ve["plac_r_m"] - 1.0) - math.cos(a) * 4.0)
    domy = [u["novy_stred"] for u in L["ves"]["usedlosti"]] + [x["stred"] for x in L["stavby"]]
    # zakaz: domy, dil mlyna (polouhlopricka + napojeni); voda je prirazka (cesta tok prekroci kolmo brodem se zaznamem)
    MD = V["mlyn"]["dil"]
    R_DIL = 20.0 * math.sqrt(2.0) + J("pravidla", "pravidla_sveta.json")["pasma"]["dil"]["napojeni_m"]
    seg = [(p_[:2], q_[:2], t_["sirka_m"] / 2 + 3.0) for t_ in V["toky"] for p_, q_ in zip(t_["osa_xzy"], t_["osa_xzy"][1:])]

    def d_seg(x, z, p_, q_):
        dx, dz = q_[0] - p_[0], q_[1] - p_[1]
        u = max(0.0, min(1.0, ((x - p_[0]) * dx + (z - p_[1]) * dz) / (dx * dx + dz * dz or 1e-9)))
        return math.hypot(x - p_[0] - dx * u, z - p_[1] - dz * u)

    # domy jako test smyslu (stavba na ceste): polomer domu vsi 0,8 x pul uhlopricky L x W, stavby 0,6 x rovina, + pulsirka
    dr_ = [(u["novy_stred"], math.hypot(u["L"], u["W"]) / 2 * 0.8) for u in L["ves"]["usedlosti"]] + \
          [(x["stred"], x["rovina_r_m"] * 0.6) for x in L["stavby"]]
    PW = 1.4
    zak = lambda x, z: any(math.hypot(x - d[0][0], z - d[0][1]) < d[1] + PW + 1.0 for d in dr_) or math.hypot(x - MD["stred"][0], z - MD["stred"][1]) < R_DIL
    cena = lambda x, z: 40.0 if any(d_seg(x, z, p_, q_) < w_ for p_, q_, w_ in seg if abs(p_[0] - x) < 20 and abs(p_[1] - z) < 20) else 1.0
    cesty = J("build", "protokol_stavby.json")["cesty"]
    kand = sorted({(round(math.dist(p, cil)), tuple(p)) for c in cesty for p in c[::3]})
    best = None
    vid = []
    for d0, p0 in kand:
        if any(math.dist(p0, q) < 40 for q in vid) or zak(*p0):
            continue                                  # start i v zakazu (konec ulice u domu) ne
        vid.append(p0)
        if len(vid) > 5:
            break
        r = astar.route(p0, cil, [], gmax=gmax, zakaz=zak, cena=cena)
        if r:
            dl = sum(math.dist(u, v) for u, v in zip(r, r[1:]))
            print("k_vetraku od", p0, "delka %.0f m" % dl)
            if best is None or dl < best[0]:
                best = (dl, r)
    if best is None:
        sys.exit("k_vetraku: cesta nenalezena")
    # bez vyhlazeni: body mrizky planovace drzi sklon (vyhlazeni serpentiny zkracuje a zostruje - 28. 10. 26 %)
    osa = [[round(x, 2), round(z, 2)] for x, z in best[1]]
    # krizeni s toky: zaznam brodu (cesty.json prechody), maly tok melkym brodem
    def prus(p1, p2, p3, p4):
        d_ = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
        if abs(d_) < 1e-9:
            return None
        t_ = ((p1[0] - p3[0]) * (p3[1] - p4[1]) - (p1[1] - p3[1]) * (p3[0] - p4[0])) / d_
        u_ = -((p1[0] - p2[0]) * (p1[1] - p3[1]) - (p1[1] - p2[1]) * (p1[0] - p3[0])) / d_
        return (round(p1[0] + t_ * (p2[0] - p1[0]), 1), round(p1[1] + t_ * (p2[1] - p1[1]), 1)) if 0 <= t_ <= 1 and 0 <= u_ <= 1 else None
    C["prechody"] = [x for x in C["prechody"] if x.get("cesta") != "k_vetraku"]
    for t_ in V["toky"]:
        for p_, q_ in zip(t_["osa_xzy"], t_["osa_xzy"][1:]):
            for u_, w_ in zip(osa, osa[1:]):
                x_ = prus(p_[:2], q_[:2], u_, w_)
                if x_:
                    C["prechody"].append({"id": "brod_k_vetraku_%d" % (len([x for x in C["prechody"] if x.get("cesta") == "k_vetraku"]) + 1),
                                          "cesta": "k_vetraku", "tok": t_["id"], "druh": "brod", "stred": list(x_), "polomer_m": 6.0,
                                          "stavi": "svet.gd _brody_malych_toku -> _brody (kameny dna a najezdu); tools/krok_b/vetrak_misto.py"})
                    print("k_vetraku: brod pres %s u %s" % (t_["id"], x_))
    C["pesiny"] = [e for e in C["pesiny"] if e["id"] != "k_vetraku"] + [{
        "id": "k_vetraku", "typ": "vozova", "pulsirka_m": PW,
        "popis": "od nejblizsi cesty na navrsi k placu vetrneho mlyna (lokace.json vetrak, tools/krok_b/vetrak_misto.py --zapis): "
                 "tools/krok_b/astar.py po terenu do pasma.cesta.vozova.podelny_max, mimo vodu a domy - vyjezd s obilim do kopce serpentinou",
        "osa": osa}]
    json.dump(C, open(os.path.join(ROOT, "pravidla", "svet", "cesty.json"), "w"), ensure_ascii=False, indent=1)
    print("zapsano cesty.json k_vetraku: %d bodu, %.0f m" % (len(osa), best[0]))
