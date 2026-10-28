"""Pristupova cesta k mistu (krok planu cest po vode a dilech; 28. 10.: k_mlynu vedla pres dil rybnika Lhota -
test zasazeni nad_cestou_pesina u (489, 885)). Od nejblizsich bodu cest hry (build/protokol_stavby.json) k cili,
tools/krok_b/astar.py: sklon kroku do pasma.cesta.vozova.podelny_max, zakaz domy vsi a stavby (polomer jako test
smyslu + pulsirka), dily s vlastnim terenem (mlyn: polouhlopricka + napojeni; rybnik Lhota: ctverec pulsirka_dilu_m
+ pas_napojeni_m v natoceni dilu), voda s prirazkou - kolme krizeni toku dostane zaznam brodu (cesty.json prechody).
Osa bez vyhlazeni (body mrizky drzi sklon).
  python3 tools/krok_b/cesta_k.py <id cesty> <x> <z> [--zapis]"""
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
CID, CIL = sys.argv[1], (float(sys.argv[2]), float(sys.argv[3]))
C, L, V = J("pravidla", "svet", "cesty.json"), J("pravidla", "svet", "lokace.json"), J("pravidla", "svet", "voda.json")
PA = J("pravidla", "pravidla_sveta.json")["pasma"]
GMAX = PA["cesta"]["vozova"]["podelny_max"]
PW = 1.4
DR = [(u["novy_stred"], math.hypot(u["L"], u["W"]) / 2 * 0.8) for u in L["ves"]["usedlosti"]] + \
     [(x["stred"], x["rovina_r_m"] * 0.6) for x in L["stavby"]]
MD = V["mlyn"]["dil"]
R_MLYN = 20.0 * math.sqrt(2.0) + PA["dil"]["napojeni_m"]
RL = V["rybnik_lhota"]
seg = [(p[:2], q[:2], t["sirka_m"] / 2 + 3.0, t["id"]) for t in V["toky"] for p, q in zip(t["osa_xzy"], t["osa_xzy"][1:])]


def d_seg(x, z, p, q):
    dx, dz = q[0] - p[0], q[1] - p[1]
    u = max(0.0, min(1.0, ((x - p[0]) * dx + (z - p[1]) * dz) / (dx * dx + dz * dz or 1e-9)))
    return math.hypot(x - p[0] - dx * u, z - p[1] - dz * u)


def v_rybniku(x, z):
    c, s = math.cos(RL["natoceni"]), math.sin(RL["natoceni"])
    dx, dz = x - RL["stred"][0], z - RL["stred"][1]
    lx, lz = dx * c - dz * s, dx * s + dz * c
    h = RL["pulsirka_dilu_m"] + RL["pas_napojeni_m"]
    return abs(lx) < h and abs(lz) < h


def zakaz(x, z):
    if any(math.hypot(x - d[0][0], z - d[0][1]) < d[1] + PW + 1.0 for d in DR):
        return True
    if math.hypot(x - MD["stred"][0], z - MD["stred"][1]) < R_MLYN and math.dist((x, z), CIL) > R_MLYN - 2.0:
        return True
    return v_rybniku(x, z)


def cena(x, z):
    return 40.0 if any(d_seg(x, z, p, q) < w for p, q, w, _ in seg if abs(p[0] - x) < 20 and abs(p[1] - z) < 20) else 1.0


cesty = [c for c in J("build", "protokol_stavby.json")["cesty"]]
vlastni = next((e["osa"] for e in C["vozove"] + C["pesiny"] if e["id"] == CID), [])
kand = sorted({(round(math.dist(p, CIL)), tuple(p)) for c in cesty for p in c[::3]
               if not any(math.dist(p, q) < 3.0 for q in vlastni)})
best, vid = None, []
for _d, p0 in kand:
    if any(math.dist(p0, q) < 40 for q in vid) or zakaz(*p0):
        continue
    vid.append(p0)
    if len(vid) > 6:
        break
    r = astar.route(p0, CIL, [], gmax=GMAX, zakaz=zakaz, cena=cena)
    if r:
        dl = sum(math.dist(u, w) for u, w in zip(r, r[1:]))
        print("%s od %s: %.0f m" % (CID, p0, dl))
        if best is None or dl < best[0]:
            best = (dl, r)
if best is None:
    sys.exit("%s: cesta nenalezena" % CID)
osa = [[round(x, 2), round(z, 2)] for x, z in best[1]]


def prus(p1, p2, p3, p4):
    d_ = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
    if abs(d_) < 1e-9:
        return None
    t_ = ((p1[0] - p3[0]) * (p3[1] - p4[1]) - (p1[1] - p3[1]) * (p3[0] - p4[0])) / d_
    u_ = -((p1[0] - p2[0]) * (p1[1] - p3[1]) - (p1[1] - p2[1]) * (p1[0] - p3[0])) / d_
    return (round(p1[0] + t_ * (p2[0] - p1[0]), 1), round(p1[1] + t_ * (p2[1] - p1[1]), 1)) if 0 <= t_ <= 1 and 0 <= u_ <= 1 else None


brody = []
for p, q, _w, tid in seg:
    for u, w in zip(osa, osa[1:]):
        x = prus(p, q, u, w)
        if x:
            brody.append((tid, x))
print("%s: %d bodu, %.0f m, brody %s" % (CID, len(osa), best[0], brody))
if "--zapis" in sys.argv:
    e = next(e for e in C["pesiny"] if e["id"] == CID)
    e["osa"] = osa
    C["prechody"] = [x for x in C["prechody"] if x.get("cesta") != CID]
    for i, (tid, x) in enumerate(brody):
        C["prechody"].append({"id": "brod_%s_%d" % (CID, i + 1) if i else "brod_" + CID, "cesta": CID, "tok": tid, "druh": "brod",
                              "stred": list(x), "polomer_m": 6.0,
                              "stavi": "svet.gd _brody_malych_toku -> _brody (kameny dna a najezdu); tools/krok_b/cesta_k.py"})
    json.dump(C, open(os.path.join(ROOT, "pravidla", "svet", "cesty.json"), "w"), ensure_ascii=False, indent=1)
    print("zapsano cesty.json", CID)
