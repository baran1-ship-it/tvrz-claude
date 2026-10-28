"""Preplanovani vozovych cest nad podelny sklon (Misa/radce 28. 10. 19:10: „cesty nad 12,5 % nepovolovat, preplanovat
hned“). Pevne body zustavaji: zacatek az po hra_od_bodu, konce, prechody cesty (mosty, brody v polomeru zaznamu),
napojeni jinych cest (do napojeni_m), body mimo mrizku terenu. Kazdy shluk useku nad pasma.cesta.vozova.podelny_max
(okno podelny_okno_m, teren vysky.json - jako test smyslu cesta_sklon) se nahradi trasou tools/krok_b/astar.py mezi
nejblizsimi volnymi body pred a za shlukem: sklon kroku do podelny_max, nejdal odchylka_m od puvodni osy, mimo domy
a dil mlyna, voda s prirazkou; nejde-li to, usek se rozsiri (serpentina vznikne sama v koridoru).
  python3 tools/krok_b/cesty_sklon.py [--zapis]"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
os.chdir(HERE)
import astar  # noqa: E402

J = lambda *p: json.load(open(os.path.join(ROOT, *p)))
D = J("tools", "krok_b", "vysky.json")
K, X0, Z0, nx, nz, H = D["K"], D["X0"], D["Z0"], D["nx"], D["nz"], D["h"]
C = J("pravidla", "svet", "cesty.json")
L = J("pravidla", "svet", "lokace.json")
V = J("pravidla", "svet", "voda.json")
PV = J("pravidla", "pravidla_sveta.json")["pasma"]["cesta"]["vozova"]
GMAX, OKNO, ODCH, NAPOJ = PV["podelny_max"], PV["podelny_okno_m"], PV["odchylka_m"], PV["napojeni_m"]
PA_DIL = J("pravidla", "pravidla_sveta.json")["pasma"]["dil"]
X1, Z1 = X0 + (nx - 1) * K, Z0 + (nz - 1) * K


def v(x, z):
    i = max(0, min(nx - 1, int(round((x - X0) / K))))
    j = max(0, min(nz - 1, int(round((z - Z0) / K))))
    return H[j * nx + i]


def v_mrizce(p):
    return X0 <= p[0] <= X1 and Z0 <= p[1] <= Z1


def prechod_u(cid, p):
    return any(pr.get("cesta") == cid and math.dist(p, pr["stred"]) < pr.get("polomer_m", 8.0) for pr in C["prechody"])


def spatne(cid, pts):
    """Indexy zacatku oken nad podelny_max (jako test smyslu: okno OKNO m, mimo prechody a mimo mrizku)."""
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + math.dist(a, b))
    out, j = [], 0
    for i in range(len(pts)):
        while j < len(pts) - 1 and s[j] - s[i] < OKNO:
            j += 1
        if s[j] - s[i] < OKNO or not (v_mrizce(pts[i]) and v_mrizce(pts[j])) or prechod_u(cid, pts[i]) or prechod_u(cid, pts[j]):
            continue
        if abs(v(*pts[j]) - v(*pts[i])) / (s[j] - s[i]) > GMAX:
            out.append(i)
    return out


dr_ = [(u["novy_stred"], math.hypot(u["L"], u["W"]) / 2 * 0.8) for u in L["ves"]["usedlosti"]] + \
      [(x["stred"], x["rovina_r_m"] * 0.6) for x in L["stavby"]]
MD = V["mlyn"]["dil"]
R_DIL = 20.0 * math.sqrt(2.0) + PA_DIL["napojeni_m"]
seg = [(p[:2], q[:2], t["sirka_m"] / 2 + 3.0) for t in V["toky"] for p, q in zip(t["osa_xzy"], t["osa_xzy"][1:])]


def d_seg(x, z, p, q):
    dx, dz = q[0] - p[0], q[1] - p[1]
    u = max(0.0, min(1.0, ((x - p[0]) * dx + (z - p[1]) * dz) / (dx * dx + dz * dz or 1e-9)))
    return math.hypot(x - p[0] - dx * u, z - p[1] - dz * u)


def cena(x, z):
    return 40.0 if any(d_seg(x, z, p, q) < w for p, q, w in seg if abs(p[0] - x) < 20 and abs(p[1] - z) < 20) else 1.0


vsechny = {e["id"]: e for e in C["vozove"] + C["pesiny"] if len(e["osa"]) > 1}
cile = sys.argv[sys.argv.index("--cesty") + 1].split(",") if "--cesty" in sys.argv else \
    [k for k, e in vsechny.items() if e.get("typ", "vozova") == "vozova"]
celkem = 0
for cid in cile:
    e = vsechny[cid]
    pts = [tuple(p) for p in e["osa"]]
    jine = [tuple(p) for k, o in vsechny.items() if k != cid for p in o["osa"]]
    pevne = set(range(int(e.get("hra_od_bodu", 0)) + 1)) | {0, len(pts) - 1}
    for i, p in enumerate(pts):
        if prechod_u(cid, p) or not v_mrizce(p) or any(math.dist(p, q) < NAPOJ for q in jine):
            pevne.add(i)
    if cid == "hlavni":
        pevne |= {i for i, p in enumerate(pts) if math.dist(p, C["krizovatka_hlavni_odbocka"]) < NAPOJ}
    for kolo in range(12):
        bad = spatne(cid, pts)
        if not bad:
            break
        i = bad[0]
        # okno: od volneho bodu pred shlukem k volnemu bodu za nim, kazde kolo sirsi (rozsireni o ~30 m)
        rozs = 6 + 4 * kolo
        i0 = max(0, i - rozs)
        while i0 > 0 and i0 in pevne:
            i0 -= 1
        i1 = min(len(pts) - 1, max(b for b in bad if b - i < 40) + rozs)
        while i1 < len(pts) - 1 and i1 in pevne:
            i1 += 1
        if any(j in pevne for j in range(i0 + 1, i1)):
            # pevny bod uvnitr: planovat jen do nej
            pv_ = [j for j in range(i0 + 1, i1) if j in pevne]
            i1 = min([j for j in pv_ if j > i] or [i1])
            i0 = max([j for j in pv_ if j < i] or [i0])
        ref = pts[max(0, i0 - 5):i1 + 6]

        def zakaz(x, z, ref=ref):
            if min(math.dist((x, z), q) for q in ref) > ODCH:
                return True
            if math.hypot(x - MD["stred"][0], z - MD["stred"][1]) < R_DIL:
                return True
            return any(math.hypot(x - d[0][0], z - d[0][1]) < d[1] + e.get("pulsirka_m", 1.5) + 1.0 for d in dr_)
        r = astar.route(pts[i0], pts[i1], ref, gmax=GMAX, zakaz=zakaz, cena=cena)
        if r is None:
            print("  %s kolo %d: usek %d-%d bez trasy, sirsi" % (cid, kolo, i0, i1))
            continue
        nove = [pts[i0]] + [tuple(round(c, 2) for c in q) for q in r[1:-1]] + [pts[i1]]
        pts = pts[:i0] + nove + pts[i1 + 1:]
        pevne = {j if j <= i0 else j + len(nove) - (i1 - i0 + 1) for j in pevne if j <= i0 or j >= i1}
        print("  %s kolo %d: usek %d-%d -> %d bodu" % (cid, kolo, i0, i1, len(nove)))
    zb = spatne(cid, pts)
    print("%s: %d bodu, zbyva oken nad %.1f %%: %d %s" % (cid, len(pts), GMAX * 100, len(zb), [tuple(round(c) for c in pts[b]) for b in zb[:5]]))
    celkem += len(zb)
    e["osa"] = [list(p) for p in pts]
if "--zapis" in sys.argv:
    json.dump(C, open(os.path.join(ROOT, "pravidla", "svet", "cesty.json"), "w"), ensure_ascii=False, indent=1)
    print("zapsano cesty.json")
else:
    json.dump(C, open(sys.argv[sys.argv.index("--ven") + 1] if "--ven" in sys.argv else os.devnull, "w"), ensure_ascii=False, indent=1)
sys.exit(1 if celkem else 0)
