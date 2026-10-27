"""Test smyslu pred exportem (radce 27. 10. 20:50 bod 1): kontroluje DATA a pravidla generatoru za par sekund,
ne vysledek exportu. Neprojde -> export se nespousti (tools/export.sh).

  /opt/bl/bin/python tools/test_smyslu.py        (Blender python: masky povrchu se ptaji primo kraj.py)

Kontroly (kazda chyba: SMYSL <druh chyby> <misto> <podrobnosti>):
  druh      - kazdy druh rostliny v rozsevu (literaly v blender/veg|kraj|vesnice|nove|ruiny.py a klice posledniho
              modely/svet.json) je v pravidla/svet/druhy.json a historicky (Cechy 1393)
  stavba    - stavby, domy vsi, mlyn a drobne stavby ne ve vode, ne na ose cesty (krome vlastni odbocky na jejim konci),
              ne na svahu > plochy.json teren stavba_max_sklon (vysky z tools/krok_b/vysky.json, teren pred vodou)
  pesina    - osa pesiny ani vozove cesty nevede skrz dum vsi (zaznam novy_stred, L x W)
  brod      - cesta / pesina nekrizi tok bez prechodu (cesty.json prechody)
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
try:
    with open(os.path.join(ROOT, "modely", "svet.json"), encoding="utf-8") as f:
        posledni = json.load(f)["rostliny"]
    for k in posledni:
        i = druh_z(k)
        if i is None:
            chyba("druh", "svet.json", "%s neni v druhy.json" % k)
        elif not hist[i]["historicky"]:
            chyba("druh", "svet.json", "%s = %s neni v Cechach 1393" % (k, hist[i]["nazev"]))
except FileNotFoundError:
    pass

# ------------------------------------------------------------------ stavby
import bpy  # noqa: E402,F401  (mathutils pro vesnice.py)
import kraj  # noqa: E402

vys = None
try:
    with open(os.path.join(ROOT, "tools", "krok_b", "vysky.json")) as f:
        vys = json.load(f)
except FileNotFoundError:
    print("SMYSL pozor: tools/krok_b/vysky.json chybi - svah staveb se nekontroluje (python3 tools/krok_b/vysky.py)")


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
for oid, typ, w, pts in osy:
    for tid, tw, tp in toky:
        for a, b in zip(pts, pts[1:]):
            for c, d in zip(tp, tp[1:]):
                if krizi(a, b, c, d):
                    if not any(math.hypot(a[0] - p["stred"][0], a[1] - p["stred"][1]) < 15.0 for p in prechody):
                        chyba("brod", "(%.0f, %.0f)" % a, "%s krizi tok %s bez prechodu" % (oid, tid))

# ------------------------------------------------------------------ masky povrchu
br = kraj.bridge()
if br:
    for t in [k * 0.5 for k in range(-int(br[4] * 2) + 2, int(br[4] * 2) - 1)]:
        x, z = br[0] + br[2] * t, br[1] + br[3] * t
        g = kraj.ground_attrs(x, z)[0]
        rv = kraj.river(x, z)
        if g < 0.4 and (rv is None or rv[0] > 6.0):
            chyba("hlina", "(%.0f, %.0f)" % (x, z), "hlina cesty pod mostovkou (trava %.2f)" % g)
for tid, tw, tp in toky:
    for x, z in tp[::2]:
        if kraj.field_strip(x, z) is not None:
            chyba("pole", "(%.0f, %.0f)" % (x, z), "pole pres tok %s" % tid)

# ------------------------------------------------------------------ stanoviste rostlin
def stanoviste(x, z, y, skaly):
    out = set()
    vv = kraj.ve_vode(x, z, y)
    rv = kraj.river(x, z)
    if vv < 0.0 or (rv is not None and rv[0] < 4.8 * kraj._PO["breh_nasobek"] * 0.5):
        out.add("voda")
    if vv < 8.0 or (rv is not None and rv[0] < 4.8 * kraj._PO["breh_nasobek"] * 0.5 + 8.0):
        out.add("breh")
    f = kraj.forest(x, z)
    if f > 0.5:
        out.add("les")
    if 0.05 < f <= 0.5 or (f <= 0.5 and any(kraj.forest(x + dx, z + dz) > 0.5 for dx, dz in ((25, 0), (-25, 0), (0, 25), (0, -25)))):
        out.add("okraj")
    fs = kraj.field_strip(x, z, mez=False)
    if fs is not None:
        out.add("pole" if kraj.field_strip(x, z) is not None else "mez")
    if math.hypot(x, z) < 70.0:
        out.add("tvrz")                                   # tvrz a jeji okoli (zdi, nadvori, prikop)
    if kraj.ves_r(x, z) < kraj.VES_R + 30.0 or any(math.hypot(x - c[0], z - c[1]) < 40.0 for _, c, _, _ in stavby):
        out.add("ves")
    rn = kraj.road_near(x, z)
    if rn and rn[0] - rn[3] < 6.0:
        out.add("cesta")
    if skaly.get((int(x // 8), int(z // 8))):
        out.add("skala")
    if not out & {"les", "pole", "mez", "voda", "tvrz"}:
        out.add("louka")
    return out


try:
    skaly = {}
    for k, arr in posledni.items():
        if k.startswith(("skala_", "balvan_")):
            for m in arr:
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        skaly[(int(m[3] // 8) + dx, int(m[11] // 8) + dz)] = True
    mimo, celkem = {}, {}
    for k, arr in posledni.items():
        i = druh_z(k)
        if i is None or "daleko" in k or "vse" in hist[i].get("stanoviste", ["vse"]):
            continue
        dovol = set(hist[i]["stanoviste"])
        krok = 1 if hist[i]["skupina"] == "strom" else 7
        for m in arr[::krok]:
            celkem[i] = celkem.get(i, 0) + 1
            st_ = stanoviste(m[3], m[11], m[7], skaly)
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

souhrn = {}
for c in CHYBY:
    souhrn[c] = souhrn.get(c, 0) + 1
print("SMYSL souhrn", souhrn if souhrn else "OK")
sys.exit(1 if CHYBY else 0)
