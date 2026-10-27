"""Test smyslu pred exportem (radce 27. 10. 20:50 bod 1): kontroluje DATA a pravidla generatoru za par sekund,
ne vysledek exportu. Neprojde -> export se nespousti (tools/export.sh).

  /opt/bl/bin/python tools/test_smyslu.py        pred exportem: data a pravidla (masky povrchu se ptaji kraj.py)
  /opt/bl/bin/python tools/test_smyslu.py --po   po exportu: i vysledne rozmisteni (druhy, stanoviste, uzivani)

Kontroly (kazda chyba: SMYSL <druh chyby> <misto> <podrobnosti>):
  druh      - kazdy model rostliny v katalogu generatoru (textures.MODELS bez veg.SKIP, nove.DIM/STROMY/PODROST/SKALY,
              balvany a kameny) i v klicich posledniho modely/svet.json je v pravidla/svet/druhy.json (neznamy = chyba)
              a historicky (Cechy 1393); literaly v blender/veg|kraj|vesnice|nove|ruiny.py jen historicke
  stavba    - stavby, domy vsi, mlyn a drobne stavby ne ve vode, ne na ose cesty (krome vlastni odbocky na jejim konci),
              ne na svahu > plochy.json teren stavba_max_sklon (vysky z tools/krok_b/vysky.json, teren pred vodou)
  pesina    - osa pesiny ani vozove cesty nevede skrz dum vsi (zaznam novy_stred, L x W)
  brod      - kazdy prusecik osy cesty / pesiny s tokem nebo Bystrici ma zaznam cesty.json prechody se stejnym ID cesty
              a toku do polomeru od pruseciku; zaznam bez pruseciku je taky chyba (Astra 22:00)
  koryto    - osa cesty nevede podel koryta (blize nez pul sirky vody + pul sirky cesty) mimo zaznam prechodu
  podklad   - chybejici podklad (vysky.json, svet.json pro --po) = chyba, ne varovani (Astra 22:00)
  hlina     - maska hliny (kraj.ground_attrs) jen kde ma zdroj: ne pod mostovkou, ne ve vode malych toku
  pole      - pole ne pres tok a jeho breh
  stanoviste - kazdy kus rostliny z posledniho exportu (vzorek) roste na stanovisti sveho druhu (druhy.json stanoviste);
              vypis podilu mimo stanoviste po druzich, chyba nad pasma test stanoviste_max_podil"""
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SV = os.path.join(ROOT, "pravidla", "svet")
sys.path.insert(0, os.path.join(ROOT, "blender"))


def J(nm):
    with open(os.path.join(SV, nm), encoding="utf-8") as f:
        return json.load(f)


CHYBY = []


def chyba(druh, misto, text):
    CHYBY.append(druh)
    print("SMYSL %s %s %s" % (druh, misto, text))


def dseg(px, pz, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dz * dz or 1e-9
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (pz - a[1]) * dz) / L))
    return math.hypot(px - a[0] - dx * t, pz - a[1] - dz * t), t


def d_osa(x, z, pts):
    return min(dseg(x, z, a, b)[0] for a, b in zip(pts, pts[1:]))


def krizi(a, b, c, d):
    def cr(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    return cr(c, d, a) * cr(c, d, b) < 0 and cr(a, b, c) * cr(a, b, d) < 0


cesty, voda, lok, plochy = J("cesty.json"), J("voda.json"), J("lokace.json"), J("plochy.json")
osy = [(e["id"], e.get("typ", "vozova"), float(e.get("pulsirka_m", 1.0)), [(p[0], p[1]) for p in e["osa"]])
       for e in cesty["vozove"] + cesty["pesiny"] if len(e["osa"]) > 1]
toky = [(t["id"], t["sirka_m"] / 2.0, [(p[0], p[1]) for p in t["osa_xzy"]]) for t in voda["toky"]]
prechody = cesty.get("prechody", [])

# ------------------------------------------------------------------ druhy (Cechy 1393)
dr = J("druhy.json")["druhy"]
ids = sorted((d["id"] for d in dr), key=len, reverse=True)
hist = {d["id"]: d for d in dr}


def druh_z(lit):
    for i in ids:
        if lit == i or re.fullmatch(re.escape(i) + r"(_\d+|_daleko2?)*", lit):
            return i
    return None


for fn in ("veg.py", "kraj.py", "vesnice.py", "nove.py", "ruiny.py"):
    p = os.path.join(ROOT, "blender", fn)
    for n, line in enumerate(open(p, encoding="utf-8"), 1):
        if line.lstrip().startswith("#"):
            continue
        for lit in re.findall(r'"([a-z][a-z0-9_]*)"', line):
            i = druh_z(lit)
            if i and not hist[i]["historicky"]:
                chyba("druh", "%s:%d" % (fn, n), "%s = %s (%s) neni v Cechach 1393: %s" % (lit, hist[i]["nazev"], hist[i]["latinsky"], hist[i].get("poznamka", "")))
posledni = {}
if "--po" in sys.argv:
    try:
        with open(os.path.join(ROOT, "modely", "svet.json"), encoding="utf-8") as f:
            posledni = json.load(f)["rostliny"]
    except (OSError, ValueError, KeyError) as ex:
        chyba("podklad", "modely/svet.json", "chybi nebo je vadny (%s) - test po exportu nema co kontrolovat" % ex)
    for k in posledni:
        i = druh_z(k)
        if i is None:
            chyba("druh", "svet.json", "%s neni v druhy.json" % k)
        elif not hist[i]["historicky"]:
            chyba("druh", "svet.json", "%s = %s neni v Cechach 1393" % (k, hist[i]["nazev"]))

# ------------------------------------------------------------------ stavby
import bpy  # noqa: E402,F401  (mathutils pro vesnice.py)
import kraj  # noqa: E402
import nove  # noqa: E402
import textures  # noqa: E402
import veg  # noqa: E402

# katalog generatoru: kazdy model, ktery rozsev muze postavit, musi mit zaznam v druhy.json (neznamy druh = chyba)
katalog = [m for m in textures.MODELS if m not in veg.SKIP] + list(nove.DIM) + list(nove.STROMY) + list(nove.PODROST) + list(nove.SKALY)
katalog += nove.BALVANY_PISKOVEC + nove.BALVANY_POLE + nove.KAMENY_PISKOVEC + nove.KAMENY_POLE + nove.KAMINKY
for m in sorted(set(katalog)):
    i = druh_z(m)
    if i is None:
        chyba("druh", "katalog", "%s neni v druhy.json (neznamy druh)" % m)
    elif not hist[i]["historicky"]:
        chyba("druh", "katalog", "%s = %s neni v Cechach 1393" % (m, hist[i]["nazev"]))

vys = None
try:
    with open(os.path.join(ROOT, "tools", "krok_b", "vysky.json")) as f:
        vys = json.load(f)
except (OSError, ValueError):
    chyba("podklad", "tools/krok_b/vysky.json", "chybi - svah staveb nejde zkontrolovat (python3 tools/krok_b/vysky.py)")


def vyska(x, z):
    K, X0, Z0, nx = vys["K"], vys["X0"], vys["Z0"], vys["nx"]
    i = max(0, min(nx - 1, int(round((x - X0) / K))))
    j = max(0, min(vys["nz"] - 1, int(round((z - Z0) / K))))
    return vys["h"][j * nx + i]


smax = plochy["teren"].get("stavba_max_sklon", 0.15)
stavby = [(s["id"], s["stred"], s["rovina_r_m"] * 0.6, s["id"]) for s in lok["stavby"]]
stavby += [("ves_dum_%d" % u["k"], u["novy_stred"], math.hypot(u["L"], u["W"]) / 2 * 0.8, None) for u in lok["ves"]["usedlosti"]]
stavby += [("mlyn", voda["mlyn"]["stred"], voda["mlyn"].get("rovina_r_m", 6.0) * 0.6, None)]
stavby += [(d["id"], d["stred"], 0.8, None) for d in lok.get("drobne", [])]
odbocky = {"stan_kupce": "ke_stanu", "hostinec": "k_hostinci"}
for sid, c, r, _ in stavby:
    x, z = c
    if kraj.ve_vode(x, z, 1e9) < r:
        chyba("stavba", "(%.0f, %.0f)" % (x, z), "%s ve vode (%.1f m od okraje, polomer %.1f)" % (sid, kraj.ve_vode(x, z, 1e9), r))
    for oid, typ, w, pts in osy:
        if odbocky.get(sid) == oid:
            continue
        d = d_osa(x, z, pts) - w
        if d < r:
            chyba("stavba", "(%.0f, %.0f)" % (x, z), "%s na ceste %s (%.1f m od kraje, polomer %.1f)" % (sid, oid, d, r))
    if vys:
        hs = [vyska(x + r * math.cos(a), z + r * math.sin(a)) for a in [k * math.pi / 4 for k in range(8)]]
        s = (max(hs) - min(hs)) / (2 * r) if r > 1.0 else 0.0
        if s > smax:
            chyba("stavba", "(%.0f, %.0f)" % (x, z), "%s na svahu %.0f %% (max %.0f %%)" % (sid, s * 100, smax * 100))

# ------------------------------------------------------------------ cesty x voda
# prusecik osy cesty s osou toku (male toky z voda.json toky + Bystrice voda.json potok) -> zaznam prechodu se stejnym
# ID cesty a toku do jeho polomeru; zaznam, ke kteremu prusecik neni, je zastaraly (chyba). Podel koryta (osa cesty
# blize nez pul sirky vody + pul sirky cesty) smi cesta jen v polomeru prechodu.
def prusecik(a, b, c, d):
    den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
    if abs(den) < 1e-12:
        return None
    t = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / den
    u = -((a[0] - b[0]) * (a[1] - c[1]) - (a[1] - b[1]) * (a[0] - c[0])) / den
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])) if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0 else None


vody = toky + [(voda["potok"]["id"], voda["potok"]["pulsirka_vody_m"], [(p[0], p[1]) for p in voda["potok"]["osa"]])]
pouzite = set()
for oid, typ, w, pts in osy:
    for tid, tw, tp in vody:
        for a, b in zip(pts, pts[1:]):
            for c, d in zip(tp, tp[1:]):
                q = prusecik(a, b, c, d)
                if q is None:
                    continue
                pr = [p for p in prechody if p["cesta"] == oid and p["tok"] == tid and math.hypot(q[0] - p["stred"][0], q[1] - p["stred"][1]) < p.get("polomer_m", 8.0)]
                if pr:
                    pouzite.add(pr[0]["id"])
                else:
                    chyba("brod", "(%.1f, %.1f)" % q, "%s krizi %s bez zaznamu prechodu (cesty.json prechody: cesta, tok, stred, druh)" % (oid, tid))
        # podel koryta: body osy po 2 m
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2.0))
            for k in range(n):
                x, z = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
                if d_osa(x, z, tp) < tw + w and not any(p["cesta"] == oid and p["tok"] == tid and math.hypot(x - p["stred"][0], z - p["stred"][1]) < p.get("polomer_m", 8.0) for p in prechody):
                    chyba("koryto", "(%.0f, %.0f)" % (x, z), "%s vede korytem %s (%.1f m od osy, voda %.1f + cesta %.1f)" % (oid, tid, d_osa(x, z, tp), tw, w))
                    break
for p in prechody:
    if p["id"] not in pouzite:
        chyba("brod", "(%.0f, %.0f)" % tuple(p["stred"]), "zaznam prechodu %s (%s x %s) bez pruseciku - zastaraly" % (p["id"], p["cesta"], p["tok"]))

# ------------------------------------------------------------------ masky povrchu
br = kraj.bridge()
if br:
    for t in [k * 0.5 for k in range(-int(br[4] * 2) + 2, int(br[4] * 2) - 1)]:
        x, z = br[0] + br[2] * t, br[1] + br[3] * t
        g = kraj.ground_attrs(x, z)[0]
        rv = kraj.river(x, z)
        if g < 0.4 and (rv is None or rv[0] > 6.0):
            chyba("hlina", "(%.0f, %.0f)" % (x, z), "hlina cesty pod mostovkou (trava %.2f)" % g)
    # vedle mostovky na brehu a v korytu: hlina cesty jen tam, kde je osa cesty mimo rozpeti mostu (najezd)
    for dx in range(-30, 31):
        for dz in range(-30, 31):
            x, z = br[0] + dx, br[1] + dz
            rv = kraj.river(x, z)
            if rv is None or rv[0] > 4.8 * kraj._PO["breh_nasobek"] + 2.0:
                continue
            rn = kraj.road_near(x, z)
            if rn is None or rn[0] > rn[3] + 3.0:
                continue
            t = (rn[1] - br[0]) * br[2] + (rn[2] - br[1]) * br[3]
            if abs(t) < br[4] - 1.0:
                if kraj.ground_attrs(x, z)[0] < 0.15 and rv[0] > 6.0:
                    chyba("hlina", "(%.0f, %.0f)" % (x, z), "hlina cesty vedle mostovky / pod ni")
for tid, tw, tp in toky:
    for x, z in tp[::2]:
        if kraj.field_strip(x, z) is not None:
            chyba("pole", "(%.0f, %.0f)" % (x, z), "pole pres tok %s" % tid)

# ------------------------------------------------------------------ stanoviste rostlin
PO = "--po" in sys.argv          # po exportu: kontrola vysledneho rozmisteni (svet.json); pred exportem jen data a pravidla
try:
    if not PO:
        raise NameError
    skaly = {}
    for k, arr in posledni.items():
        if k.startswith(("skala_", "balvan_")):
            for m in arr:
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        skaly[(int(m[3] // 8) + dx, int(m[11] // 8) + dz)] = True
    kraj.SKALY_MRIZKA.update(skaly)
    mimo, celkem = {}, {}
    for k, arr in posledni.items():
        i = druh_z(k)
        if i is None or "daleko" in k or "vse" in hist[i].get("stanoviste", ["vse"]):
            continue
        dovol = set(hist[i]["stanoviste"])
        krok = 1 if hist[i]["skupina"] == "strom" else 7
        for m in arr[::krok]:
            celkem[i] = celkem.get(i, 0) + 1
            st_ = kraj.stanoviste(m[3], m[11], m[7])
            if not st_ & dovol:
                mimo.setdefault(i, []).append((round(m[3]), round(m[11]), sorted(st_)))
    pmax = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["test"].get("stanoviste_max_podil", 0.05)
    for i in sorted(mimo, key=lambda a: -len(mimo[a]) / celkem[a]):
        podil = len(mimo[i]) / celkem[i]
        print("SMYSL stanoviste %-18s mimo %4d / %5d (%.0f %%) napr. %s" % (i, len(mimo[i]), celkem[i], podil * 100, mimo[i][:3]))
        if podil > pmax:
            CHYBY.append("stanoviste")
except NameError:
    pass

# ------------------------------------------------------------------ uzivani (povrch a rostliny kolem staveb)
# Misa 27. 10.: kolem domu neni vysoka trava, jen u paty zdi plevel; kde jsou dvere, tam se chodi
try:
    if not PO:
        raise NameError
    import vesnice
    pb = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["budova"]
    VYSOKE = ("divoka_trava", "grass_medium", "fern", "kapradi", "shrub", "sipek", "bez_cerny")
    STROMY = ("dub", "lipa", "buk", "briza", "smrk", "borovice", "olse", "vrba", "jablon")
    budovy = []
    for h in vesnice.layout():
        budovy.append((h["p"].x, h["p"].z, h["yaw"], h["L"] / 2, h["W"] / 2, "dum_%d" % h.get("i", 0)))
        bp, byaw, bL, bW = h["barn"]
        budovy.append((bp.x, bp.z, byaw, bL / 2, bW / 2, "chlev"))
    mrizka_b = {}
    for b in budovy:
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                mrizka_b.setdefault((int(b[0] // 10) + dx, int(b[1] // 10) + dz), []).append(b)

    def od_zdi(x, z):
        best = None
        for cx, cz, yaw, hu, hv, nm in mrizka_b.get((int(x // 10), int(z // 10)), []):
            dx, dz = x - cx, z - cz
            u = dx * math.cos(yaw) + dz * math.sin(yaw)
            v = -dx * math.sin(yaw) + dz * math.cos(yaw)
            d = math.hypot(max(abs(u) - hu, 0.0), max(abs(v) - hv, 0.0))
            if best is None or d < best[0]:
                best = (d, nm)
        return best
    poc = {}
    for k, arr in posledni.items():
        if "daleko" in k:
            continue
        vys = k.startswith(VYSOKE)
        strom = k.startswith(STROMY)
        if not (vys or strom):
            continue
        for m in arr:
            r = od_zdi(m[3], m[11])
            if r is None:
                continue
            if vys and pb["plevel_u_zdi_m"] < r[0] < pb["drn_m"]:
                poc[("vysoka_u_domu", k.rsplit("_", 1)[0])] = poc.get(("vysoka_u_domu", k.rsplit("_", 1)[0]), 0) + 1
            if strom and r[0] < pb["kmen_od_zdi_m"]:
                poc[("strom_u_zdi", k.rsplit("_", 1)[0])] = poc.get(("strom_u_zdi", k.rsplit("_", 1)[0]), 0) + 1
    for (co, k), n in sorted(poc.items(), key=lambda a: -a[1]):
        chyba("uzivani", co, "%s %d kusu (do %.1f m od zdi jen nizky drn / strom od %.1f m)" % (k, n, pb["drn_m"], pb["kmen_od_zdi_m"]))
except NameError:
    pass

souhrn = {}
for c in CHYBY:
    souhrn[c] = souhrn.get(c, 0) + 1
print("SMYSL souhrn", souhrn if souhrn else "OK")
sys.exit(1 if CHYBY else 0)
