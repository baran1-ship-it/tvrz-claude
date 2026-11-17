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
  cesta_sklon - vozova cesta: sklon na useku pasma.cesta.vozova.podelny_okno_m nejvys podelny_max (vetrny mlyn 28. 10.)
  brod      - kazdy prusecik osy cesty / pesiny s tokem nebo Bystrici ma zaznam cesty.json prechody se stejnym ID cesty
              a toku do polomeru od pruseciku; zaznam bez pruseciku je taky chyba (Astra 22:00)
  koryto    - osa cesty nevede podel koryta (blize nez pul sirky vody + pul sirky cesty) mimo zaznam prechodu
  podklad   - chybejici podklad (vysky.json, svet.json pro --po) = chyba, ne varovani (Astra 22:00)
  most      - osa cesty vede rovne po cele mostovce a najezdu (prechody najezd_m) - na mostovce neni vedle mostu
  hlina     - maska hliny (kraj.ground_attrs) jen kde ma zdroj: ne pod mostovkou, ne ve vode malych toku
  pole      - pole ne pres tok a jeho breh
  stanoviste - kazdy kus rostliny z posledniho exportu (vzorek) roste na stanovisti sveho druhu (druhy.json stanoviste);
              vypis podilu mimo stanoviste po druzich, chyba nad pasma test stanoviste_max_podil
  krtinec   - (--po) samostatna mala kupka z hliny (krtinec, „hnedy klobouk“ r. 67/78) v modely/tvrz.glb = chyba
  hladina   - (--po) tekouci hladina (material s "tekouci") v modely/tvrz.glb ma barvy proudu: prumerna pena (R) do
              pasma test hladina_max_pena (Misa 28. 10.: bez barev cela hladina toku bila pena)"""
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
        elif hist[i].get("pouzit", True) is False and posledni[k]:
            chyba("druh", "svet.json", "%s = %s ma pouzit false (%s), a presto je v exportu (%d kusu)" % (k, hist[i]["nazev"], hist[i].get("duvod", ""), len(posledni[k])))

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


smax = plochy["teren"]["stavba_max_sklon"]
stavby = [(s["id"], s["stred"], s["rovina_r_m"] * 0.6, s["id"]) for s in lok["stavby"]]
stavby += [("ves_dum_%d" % u["k"], u["novy_stred"], math.hypot(u["L"], u["W"]) / 2 * 0.8, None) for u in lok["ves"]["usedlosti"]]
MDIL = voda["mlyn"].get("dil")
stavby += [("mlyn", voda["mlyn"]["stred"], 6.0 if MDIL else voda["mlyn"].get("rovina_r_m", 6.0) * 0.6, None)]
VET = lok.get("vetrak", {})
if VET.get("stred"):
    stavby += [("vetrak", VET["stred"], VET["rovina_r_m"] * 0.6, None)]
    if VET["chalupa"].get("stred"):
        stavby += [("vetrak_chalupa", VET["chalupa"]["stred"], VET["chalupa"]["rovina_r_m"] * 0.6, None)]
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
    if vys and not (sid == "mlyn" and MDIL):         # dil ma vlastni teren - hlida se hrana dilu (nize)
        hs = [vyska(x + r * math.cos(a), z + r * math.sin(a)) for a in [k * math.pi / 4 for k in range(8)]]
        s = (max(hs) - min(hs)) / (2 * r) if r > 1.0 else 0.0
        if s > smax:
            chyba("stavba", "(%.0f, %.0f)" % (x, z), "%s na svahu %.0f %% (max %.0f %%)" % (sid, s * 100, smax * 100))

# Misa 14. 11. („proc stoji dum kovare na potoce, na co mas 1000 hlidacu“): seznam stavby vyse je rucni - kovarna_ves,
# jeji dum a krcma_l v nem nebyly. Kazdy zaznam lokace se stredem (a vnoreny dum) = kruh placky (plac_r_m / rovina_r_m)
# mimo koryto a breh kazdeho toku i Bystrice (jako dvorec nize)
_pb0 = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["budova"]
_tt0 = voda["toky_tvar"]
_vse_vody = toky + [(voda["potok"]["id"], voda["potok"]["pulsirka_vody_m"], [(p[0], p[1]) for p in voda["potok"]["osa"]])]
for _kl, _zv in lok.items():
    if not isinstance(_zv, dict) or "stred" not in _zv or "rovina_r_m" not in _zv:
        continue
    _zz = [(_kl, _zv)] + ([(_kl + ".dum", _zv["dum"])] if isinstance(_zv.get("dum"), dict) and "stred" in _zv["dum"] else [])
    for sid, zz in _zz:
        x, z = zz["stred"]
        r = max(float(zz.get("plac_r_m", 0.0)), float(zz.get("rovina_r_m", 0.0)) * 0.6)
        for tid, tw, tp in _vse_vody:
            mez = tw + max(_tt0["breh_sirka_m"], _tt0["breh_sirka_vnitrni_m"]) + _pb0["placka_prechod_m"]
            d = d_osa(x, z, tp) - r
            if d < mez:
                chyba("stavba", "(%.0f, %.0f)" % (x, z), "%s u toku %s: placka (r %.1f) %.1f m od osy, mez koryto+breh+prechod %.1f" % (sid, tid, r, d, mez))

# ves B (lokace.json ves.dvorec_zaznam, tools/ves_dvorce.py --zapis): stodoly a kulny ne ve vode, na ceste a na svahu;
# stromy a kere zahumenku a ziveho plotu ne ve vode a na ceste (Astra 29. 10.: kazda zmena projde pravidly)
_dz = lok["ves"].get("dvorec_zaznam", {})
_pb = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["budova"]
_tt = voda["toky_tvar"]
for _rec in _dz.get("stavby", []):
    nm_, k_, x, z, r = _rec[:5]
    sid = "ves_%s_%d" % (nm_, k_)
    # Misa r. 60/77 (stodola 7 na patkach nad dolinou odtoku): placka stavby i s prechodem (pasma.budova placka_okraj_m,
    # placka_prechod_m) mimo koryto a breh maleho toku - jinak dolina (krok voda) placku podkope nebo placka zasype breh
    if len(_rec) < 6:
        chyba("dvorec", "(%.0f, %.0f)" % (x, z), "%s bez pudorysu v zaznamu (tools/ves_dvorce.py --zapis)" % sid)
    else:
        pg_ = _rec[5]
        body_ = pg_ + [((pg_[i][0] + pg_[(i + 1) % len(pg_)][0]) / 2, (pg_[i][1] + pg_[(i + 1) % len(pg_)][1]) / 2) for i in range(len(pg_))]
        for tid, tw, tp in toky:
            mez = tw + max(_tt["breh_sirka_m"], _tt["breh_sirka_vnitrni_m"]) + _pb["placka_okraj_m"] + _pb["placka_prechod_m"]
            dmin = min(d_osa(bx, bz, tp) for bx, bz in body_)
            if dmin < mez:
                chyba("dvorec", "(%.0f, %.0f)" % (x, z), "%s u toku %s: pudorys %.1f m od osy, placka s prechodem do koryta a brehu (mez %.1f)" % (sid, tid, dmin, mez))
    if kraj.ve_vode(x, z, 1e9) < r:
        chyba("dvorec", "(%.0f, %.0f)" % (x, z), "%s ve vode" % sid)
    for oid, typ, w, pts in osy:
        if d_osa(x, z, pts) - w < r * 0.7:
            chyba("dvorec", "(%.0f, %.0f)" % (x, z), "%s na ceste %s" % (sid, oid))
    if vys:
        hs = [vyska(x + r * math.cos(a), z + r * math.sin(a)) for a in [k * math.pi / 4 for k in range(8)]]
        if (max(hs) - min(hs)) / (2 * r) > smax:
            chyba("dvorec", "(%.0f, %.0f)" % (x, z), "%s na svahu %.0f %% (max %.0f %%)" % (sid, (max(hs) - min(hs)) / (2 * r) * 100, smax * 100))
for pid, x, z, h in _dz.get("zahumenky", []) + _dz.get("zivy_plot", []) + ([_dz["lipa_navsi"]] if _dz.get("lipa_navsi") else []):
    if kraj.ve_vode(x, z, 1e9) < 1.0:
        chyba("dvorec", "(%.0f, %.0f)" % (x, z), "%s ve vode" % pid)
    for oid, typ, w, pts in osy:
        if d_osa(x, z, pts) - w < 1.0:
            chyba("dvorec", "(%.0f, %.0f)" % (x, z), "%s na ceste %s" % (pid, oid))

# dil mlyna: hrana dilu (teren dilu na obvodu) do pasma dil hrana_max_m (rms) od terenu sveta pred napojenim
if MDIL and vys:
    pd = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["dil"]
    obvod = [(lx, lz) for lx in range(-22, 19, 2) for lz in (-25, 15)] + [(lx, lz) for lx in (-22, 18) for lz in range(-25, 16, 2)]
    dif = []
    for lx, lz in obvod:
        c, s_ = math.cos(MDIL["natoceni"]), math.sin(MDIL["natoceni"])
        wx, wz = MDIL["stred"][0] + lx * c + lz * s_, MDIL["stred"][1] - lx * s_ + lz * c
        dif.append(vyska(wx, wz) - (MDIL["y_dvora"] + kraj._mlyn_teren(lx, lz)))
    rms = math.sqrt(sum(d * d for d in dif) / len(dif))
    print("SMYSL dil mlyn: hrana od terenu rms %.2f m, max %.2f m (mez %.1f)" % (rms, max(abs(d) for d in dif), pd["hrana_max_m"]))
    if rms > pd["hrana_max_m"]:
        chyba("dil", "(%.0f, %.0f)" % tuple(MDIL["stred"]), "hrana dilu mlyna %.2f m (rms) od terenu, mez %.1f" % (rms, pd["hrana_max_m"]))

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
    # osa cesty na most a z nej (Misa 5. 11. u (205, 594): „cesta na most nevede, je vedle nej“): na obou koncich
    # mostovky a na konci rovneho najezdu (prechody najezd_m, hra svet.gd najezd_y) lezi osa cesty do 0,3 m od osy mostu
    for pr in prechody:
        if pr["druh"] != "most":
            continue
        osa_c = [(p[0], p[1]) for e in cesty["vozove"] if e["id"] == pr["cesta"] for p in e["osa"]]
        for sg in (-1, 1):
            for t in (br[4], br[4] + pr.get("najezd_m", 0.0)):
                x, z = br[0] + br[2] * sg * t, br[1] + br[3] * sg * t
                if d_osa(x, z, osa_c) > 0.3:
                    chyba("most", "(%.0f, %.0f)" % (x, z), "%s: osa %s %.1f m od osy mostu (konec mostovky / najezdu) - tools/krok_b/most_napojeni.py" % (pr["id"], pr["cesta"], d_osa(x, z, osa_c)))
# rastr (Misa 27. 10. "zeleny rastr kolem zahonu bez logiky", "zelene i mezi domy a stodolami"): maska travy na siti
# vsi (Teren_ves, krok 2 m) - osamely vrchol (od vsech 4 sousedu jinak o vic nez rastr_skok stejnym smerem) je ctverec
# bez zdroje v datech; smi jich byt nejvic rastr_max_podil
pt = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["test"]
kraj._KROK_SITE[0] = 2.0
vx0, vx1, vz0, vz1 = kraj.VRECT
gs = {}
for i in range(int((vx1 - vx0) / 2.0) + 1):
    for k in range(int((vz1 - vz0) / 2.0) + 1):
        gs[(i, k)] = kraj.ground_attrs(vx0 + 2.0 * i, vz0 + 2.0 * k)[0]
osam, vz = 0, []
for (i, k), g in gs.items():
    nb = [gs.get((i + 1, k)), gs.get((i - 1, k)), gs.get((i, k + 1)), gs.get((i, k - 1))]
    if None in nb:
        continue
    if all(g - n > pt["rastr_skok"] for n in nb) or all(n - g > pt["rastr_skok"] for n in nb):
        osam += 1
        if len(vz) < 5:
            vz.append((round(vx0 + 2.0 * i), round(vz0 + 2.0 * k), round(g, 2)))
podil = osam / max(1, len(gs))
print("SMYSL rastr ves: osamelych vrcholu masky %d z %d (%.1f %%, mez %.1f %%) napr. %s" % (osam, len(gs), podil * 100, pt["rastr_max_podil"] * 100, vz))
if podil > pt["rastr_max_podil"]:
    chyba("rastr", "ves", "osamele ctverce masky travy %.1f %% vrcholu (mez %.1f %%)" % (podil * 100, pt["rastr_max_podil"] * 100))
kraj._KROK_SITE[0] = 1.0

# pole ne v dilu s vlastnim terenem (Misa 28. 10.: oranice az u dilu mlyna)
for _id, _cx, _cz, _y, _r in kraj.MISTA:
    for _k in range(16):
        _a = _k * math.pi / 8
        for _rr in (0.5 * _r, _r):
            if kraj.field_strip(_cx + _rr * math.cos(_a), _cz + _rr * math.sin(_a)) is not None:
                chyba("pole", "(%.0f, %.0f)" % (_cx + _rr * math.cos(_a), _cz + _rr * math.sin(_a)), "pole v dilu %s" % _id)
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
        budovy.append((bp.x, bp.z, byaw, bL / 2, bW / 2, "chlev" if "dvorec" not in h else "stodola"))
        if "kolna" in h:                              # ves B (lokace.json ves.dvorec)
            kp, kyaw, kL, kW = h["kolna"]
            budovy.append((kp.x, kp.z, kyaw, kL / 2, kW / 2, "kolna"))
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

# ------------------------------------------------------------------ hladiny vody ve vysledku exportu
if "--po" in sys.argv:
    import struct
    try:
        import numpy as np
        with open(os.path.join(ROOT, "modely", "tvrz.glb"), "rb") as f:
            f.read(12)
            ln, _ = struct.unpack("<II", f.read(8))
            g = json.loads(f.read(ln))
            bl, _ = struct.unpack("<II", f.read(8))
            B = f.read(bl)
        svj = json.load(open(os.path.join(ROOT, "modely", "svet.json")))["materialy"]
        pmax = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["test"].get("hladina_max_pena", 0.3)

        def acc(i):
            a = g["accessors"][i]
            bv = g["bufferViews"][a["bufferView"]]
            ct = {5126: np.float32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]]
            nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
            arr = np.frombuffer(B, dtype=ct, count=a["count"] * nc, offset=bv.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(-1, nc)
            return arr / (65535.0 if ct == np.uint16 else 255.0) if ct != np.float32 else arr
        for n in g["nodes"]:
            if "mesh" not in n:
                continue
            for pr in g["meshes"][n["mesh"]]["primitives"]:
                mn = g["materials"][pr["material"]]["name"].split(".")[0] if "material" in pr else ""
                if svj.get(mn, {}).get("tekouci", 0.0) < 0.5:
                    continue
                if "COLOR_0" not in pr["attributes"]:
                    chyba("hladina", n.get("name", "?"), "tekouci hladina %s bez barev proudu" % mn)
                    continue
                pena = float(acc(pr["attributes"]["COLOR_0"])[:, 0].mean())
                if pena > pmax:
                    chyba("hladina", n.get("name", "?"), "tekouci hladina %s: prumerna pena %.2f > %.2f (bez barev proudu = bila)" % (mn, pena, pmax))
        # krtinec (Misa 6. a 9. 11. r. 67/78 „hnede klobouky“, „cerna placka v trave“ 505,898): samostatna mala kupka
        # z hliny ve vysledku exportu (souvisly kus site materialu hliny do pasma test krtinec_max_m vodorovne a aspon
        # krtinec_vyska_m vysoky) = chyba; nerovnosti patri terenu. Udusana hlina dvoru je plocha (0,06 m) a velka.
        pt = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["test"]

        def acc_raw(i):
            a = g["accessors"][i]
            bv = g["bufferViews"][a["bufferView"]]
            ct = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a["componentType"]]
            nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
            return np.frombuffer(B, dtype=ct, count=a["count"] * nc, offset=bv.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(-1, nc)
        for n in g["nodes"]:
            if "mesh" not in n:
                continue
            for pr in g["meshes"][n["mesh"]]["primitives"]:
                if "material" not in pr or "indices" not in pr or not g["materials"][pr["material"]]["name"].startswith(tuple(pt["krtinec_materialy"])):
                    continue
                P = acc_raw(pr["attributes"]["POSITION"])
                ix = acc_raw(pr["indices"]).reshape(-1, 3)
                q = {}
                key = [q.setdefault(tuple(np.round(p_ * 100).astype(int)), len(q)) for p_ in P]
                par = list(range(len(q)))

                def fd(x):
                    while par[x] != x:
                        par[x] = par[par[x]]
                        x = par[x]
                    return x
                for t in ix:
                    a0, b0, c0 = fd(key[t[0]]), fd(key[t[1]]), fd(key[t[2]])
                    par[b0] = a0
                    par[fd(c0)] = fd(a0)
                komp = {}
                for vi, k in enumerate(key):
                    komp.setdefault(fd(k), []).append(vi)
                for vs in komp.values():
                    pp = P[vs]
                    mn_, mx_ = pp.min(0), pp.max(0)
                    sz = mx_ - mn_
                    if max(sz[0], sz[2]) <= pt["krtinec_max_m"] and sz[1] >= pt["krtinec_vyska_m"]:
                        chyba("krtinec", "(%.0f, %.0f)" % ((mn_[0] + mx_[0]) / 2, (mn_[2] + mx_[2]) / 2),
                              "%s: samostatna kupka hliny %.2f x %.2f m (nerovnosti patri terenu)" % (n.get("name", "?"), max(sz[0], sz[2]), sz[1]))
        # koryto malych toku ve vysledne siti terenu: pod osou toku je teren aspon hloubka_dno_min_m pod hladinou
        # (Misa 28. 10. „voda v trave“: v siti 5 m koryto nebylo, hladina lezela zahrabana)
        uzly = {n.get("name"): n for n in g["nodes"] if "mesh" in n}
        tvx = []
        for nm_, nd in uzly.items():
            # lem = skryty pasek 3 m dolu pod okrajem pasma (kraj.near_skirt), ne povrch
            if nm_ and nm_.startswith(("Teren", "Mlyn_Teren")) and not nm_.endswith("_sukne") and nm_ != "Teren_lem":
                for pr in g["meshes"][nd["mesh"]]["primitives"]:
                    tvx.append(acc(pr["attributes"]["POSITION"]))
        if tvx:
            T = np.concatenate(tvx)
            # sukne siti terenu (kraj._skirt: vrcholy 0,8-8 m pod okrajem pasma, skryte) - jen povrch: v tomtez bode xz
            # nejvyssi vrchol
            kl = np.round(T[:, 0] * 50).astype(np.int64) * 1000003 + np.round(T[:, 2] * 50).astype(np.int64)
            ymax = {}
            for k_, y_ in zip(kl.tolist(), T[:, 1].tolist()):
                if y_ > ymax.get(k_, -1e9):
                    ymax[k_] = y_
            T = T[np.array([y_ > ymax[k_] - 0.5 for k_, y_ in zip(kl.tolist(), T[:, 1].tolist())])]
            mriz = {}
            for i_, (x_, y_, z_) in enumerate(T):
                mriz.setdefault((int(x_ // 2), int(z_ // 2)), []).append(i_)
            hmin = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["test"].get("hloubka_dno_min_m", 0.1)
            for t in kraj.TOKY:
                spatne = []
                for k_, (x_, z_) in enumerate(t.osa):
                    if kraj.v_dilu_mlyna(x_, z_):
                        continue                    # v dilu mlyna je videt teren modelu (koryto z modelu), svet je pod nim
                    ids = [j for dx in (-1, 0, 1) for dz in (-1, 0, 1) for j in mriz.get((int(x_ // 2) + dx, int(z_ // 2) + dz), [])]
                    if not ids:
                        continue
                    blizko = [j for j in ids if math.hypot(T[j][0] - x_, T[j][2] - z_) < 2.6]
                    if blizko and min(T[j][1] for j in blizko) > t.hl[k_] - hmin:
                        spatne.append((round(x_), round(z_)))
                if spatne:
                    chyba("koryto_toku", t.id, "%d z %d bodu osy: teren neni pod hladinou (voda v trave), napr. %s" % (len(spatne), len(t.osa), spatne[:4]))
                # Misa 0.99 „kanal vykopany bagrem“: breh strmejsi nez toky_tvar breh_max_st (svisle steny, zuby) a nasyp
                # (hladina nad okolim, tok na hrazi) - reserse_potok_1osoba_kun.md
                tt_ = voda["toky_tvar"]
                MEZ_V = J("vztahy.json")["meze"]
                strme, nasyp = [], []
                # pas napojeni dilu mlyna (pasma.dil.napojeni_m) pokracuje terenem dilu vcetne jeho koryta: mez sklonu brehu
                # = nejstrmejsi stena koryta dilu na hrane (jeho vlastni teren, mrizka 1 m)
                # (3. 11.: dil z Disku ma koryto vytoku se stenami 42 st.; drive tam svet pod hranou = blok travniku ve vzduchu)
                dil_st = tt_["breh_max_st"]
                if kraj._MDIL and "teren_obdelnik" in kraj._MDIL:
                    ox0, oz0, ox1, oz1 = [int(v_) for v_ in kraj._MDIL["teren_obdelnik"]]
                    for ex_, ez_, sx_, sz_ in [(i_, oz0, 1, 0) for i_ in range(ox0, ox1)] + [(i_, oz1, 1, 0) for i_ in range(ox0, ox1)] + \
                            [(ox0, j_, 0, 1) for j_ in range(oz0, oz1)] + [(ox1, j_, 0, 1) for j_ in range(oz0, oz1)]:
                        dil_st = max(dil_st, math.degrees(math.atan(abs(kraj._mlyn_teren(ex_ + sx_, ez_ + sz_) - kraj._mlyn_teren(ex_, ez_)))))
                for k_ in range(0, len(t.osa), 2):
                    x_, z_ = t.osa[k_]
                    if kraj.v_dilu_mlyna(x_, z_) or any(math.hypot(x_ - b_[0], z_ - b_[1]) < b_[2] + 1.0 for b_ in kraj._BRODY_TOKU):
                        continue
                    # 15. 11. (rybnik v2): u cela vypusti tvori breh kamenne celo s kridly 45 st. (stavba jako brod), ne svah -
                    # zona = pul sirky cela + delka kridla (vyska cela / sklon svahu hraze), cisla ze zaznamu rybnika
                    if any("vypust" in r_ and r_["vypust"].get("tok") == t.id and "celo" in r_["vypust"]
                           and math.hypot(x_ - r_["vypust"]["celo"][0], z_ - r_["vypust"]["celo"][1])
                           < r_["vypust"]["celo_sirka_m"] / 2.0 + r_["vypust"]["celo_vyska_m"] / r_["hraz"]["sklon_svahu"]
                           for r_ in kraj.RYBNIKY):
                        continue
                    # v pasu napojeni (dil_dolina_vaha < 1) mez = stena koryta dilu, jinde breh_max_st
                    tg = math.tan(math.radians(dil_st if kraj.dil_dolina_vaha(x_, z_) < 1.0 else tt_["breh_max_st"]))
                    # jez u vtoku nahonu (toky_hladina: hladina vzduta na uroven nahonu) je stavba mlyna jako brod
                    if kraj._MDIL and t.id == kraj._MDIL["tok"]:
                        jx_, _, jz_ = kraj.mlyn_svet(*kraj._MVODA["nahon"]["body"][0])
                        if math.hypot(x_ - jx_, z_ - jz_) < tt_["breh_sirka_m"] + 3.0:
                            continue
                    ids = [j for dx in (-2, -1, 0, 1, 2) for dz in (-2, -1, 0, 1, 2) for j in mriz.get((int(x_ // 2) + dx, int(z_ // 2) + dz), [])]
                    pas = [j for j in ids if math.hypot(T[j][0] - x_, T[j][2] - z_) < t.w / 2.0 + tt_["breh_sirka_vnitrni_m"] + 0.5]
                    tnj = {j: kraj.tok_near(float(T[j][0]), float(T[j][2])) for j in pas}
                    dos = {j: (tnj[j] or (1e9,))[0] for j in pas}
                    # vyska nad mistni hladinou (kolmy bod osy): na prudkem toku (u pramene spad 0,6 m na 1 m) sikma dvojice
                    # bodu brala spad podel toku za strmy breh (0.993 export: lhota_potok (760-766, 910))
                    nad = {j: T[j][1] - (tnj[j][1] if tnj[j] else 0.0) for j in pas}
                    for a_ in pas:
                        for b_ in pas:
                            dh = math.hypot(T[a_][0] - T[b_][0], T[a_][2] - T[b_][2])
                            # jen napric tokem (rozdil vzdalenosti od osy) - podel toku je spad hladiny, ne breh
                            # pravidlo z reserse: strmeji nez breh_max_st nikdy na useku delsim nez breh_strmy_usek_m
                            # (svisla stena kanalu 0,57 m na 0,22 m = 69 st.; mrizka 0,5 m na svahu dava zuby 37 st. na 0,4 m)
                            if MEZ_V["breh_strmy_usek_m"] <= dh < MEZ_V["breh_strmy_usek_m"] + 0.5 and abs(dos[a_] - dos[b_]) > 0.7 * dh \
                                    and (nad[a_] - nad[b_]) / dh > tg:
                                strme.append((round(x_), round(z_), round(math.degrees(math.atan((nad[a_] - nad[b_]) / dh))),
                                              round(math.degrees(math.atan(tg)))))
                                break
                        else:
                            continue
                        break
                    for a_ in ids:
                        # vzdalenost od osy toku (ne od bodu osy - po proudu niz lezi dno, falesny nasyp), hladina v kolmem bode
                        tn_ = kraj.tok_near(float(T[a_][0]), float(T[a_][2]))
                        if tn_ is None or tn_[3] is not t:
                            continue
                        d_ = tn_[0]
                        # hladina: nejnizsi z bodu osy v dosahu - v ohybu meandru lezi bod i u dolniho (nizsiho) useku toku
                        # (0.993: lhota_odtok (291, 959) porovnany s hornim usekem)
                        dos_m = t.w / 2.0 + tt_["breh_sirka_m"] + 4.0
                        hl_ = min([tn_[1]] + [t.hl[q_] for q_ in range(max(0, k_ - 40), min(len(t.osa), k_ + 40))
                                              if math.hypot(t.osa[q_][0] - T[a_][0], t.osa[q_][1] - T[a_][2]) < dos_m])
                        if t.w / 2.0 + tt_["breh_sirka_m"] + 2.0 < d_ < dos_m and T[a_][1] < hl_ - MEZ_V["nasyp_tolerance_m"] \
                                and not any(math.hypot(x_ - r_["stred"][0], z_ - r_["stred"][1]) < r_.get("polomer_m", r_.get("voda_polomer_m", 0.0)) + 6.0 for r_ in kraj.RYBNIKY):
                            nasyp.append((round(x_), round(z_), round(float(hl_ - T[a_][1]), 2), round(d_, 1)))
                            break
                print("SMYSL breh %s: strmy breh %d mist, nasyp %d mist" % (t.id, len(strme), len(nasyp)))
                if strme:
                    chyba("breh_toku", t.id, "breh strmejsi nez mez (%.0f st., v pasu dilu az %.0f st.) v %d mistech osy (kanal), napr. (x, z, sklon, mez) %s" % (tt_["breh_max_st"], dil_st, len(strme), strme[:4]))
                if nasyp:
                    chyba("toky_nasyp", t.id, "teren vedle koryta pod hladinou v %d mistech (tok na nasypu), napr. %s" % (len(nasyp), nasyp[:4]))
    except FileNotFoundError as e:
        chyba("podklad", "tvrz.glb", str(e))

# ------------------------------------------------------------------ podelny sklon vozovych cest (pasma.cesta.vozova)
# 28. 10. (vetrny mlyn na navrsi): vozova cesta do kopce serpentinou, ne primo - sklon na useku podelny_okno_m po ose
# (teren pred stavbou, vysky.json) nejvys podelny_max
_PV = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["cesta"]["vozova"]
# povoleni (vztahy.json, radce 18:20: konkretni odchylka s duvodem a platnosti): cesta:<id> do verze plati_do
_VER = tuple(map(int, re.search(r'config/version="([0-9.]+)', open(os.path.join(ROOT, "project.godot")).read()).group(1).split(".")))
_POV = {pv["zdroj"][6:]: pv for pv in J("vztahy.json").get("povoleni", []) if pv.get("zdroj", "").startswith("cesta:")
        and _VER <= tuple(map(int, str(pv["plati_do"]).split(".")))}
def _v_mrizce(p):
    return vys["X0"] <= p[0] <= vys["X0"] + (vys["nx"] - 1) * vys["K"] and vys["Z0"] <= p[1] <= vys["Z0"] + (vys["nz"] - 1) * vys["K"]


def _u_prechodu(cid, p):
    return any(pr.get("cesta") == cid and math.dist(p, pr["stred"]) < pr.get("polomer_m", 8.0) for pr in prechody)


if vys and "podelny_max" in _PV:
    for id_, typ, _pw, pts in osy:
        if typ != "vozova":
            continue
        if id_ in _POV:
            print("SMYSL povoleni %s: cesta_sklon %s (%s, plati do %s)" % (_POV[id_]["id"], id_, _POV[id_]["duvod"][:60], _POV[id_]["plati_do"]))
            continue
        s = [0.0]
        for a_, b_ in zip(pts, pts[1:]):
            s.append(s[-1] + math.dist(a_, b_))
        j = 0
        for i in range(len(pts)):
            while j < len(pts) - 1 and s[j] - s[i] < _PV["podelny_okno_m"]:
                j += 1
            # podminene: okno u prechodu cesty (most/brod ma vlastni profil) a mimo mrizku terenu se nehodnoti -
            # stejne jako tools/krok_b/cesty_sklon.py
            if s[j] - s[i] >= _PV["podelny_okno_m"] and _v_mrizce(pts[i]) and _v_mrizce(pts[j]) and not _u_prechodu(id_, pts[i]) \
                    and not _u_prechodu(id_, pts[j]):
                g = abs(vyska(*pts[j]) - vyska(*pts[i])) / (s[j] - s[i])
                if g > _PV["podelny_max"]:
                    chyba("cesta_sklon", "%s (%.0f, %.0f)" % (id_, pts[i][0], pts[i][1]), "podelny sklon %.0f %% > %.0f %%" % (100 * g, 100 * _PV["podelny_max"]))
                    break

# ------------------------------------------------------------------ stoly venku ne na hline cesty (hostinec 28. 10.)
for id_, x, z, _yaw in kraj.STOLY_VENKU:
    for e in cesty["vozove"] + cesty["pesiny"]:
        if len(e["osa"]) < 2:
            continue
        pts = [(p[0], p[1]) for p in e["osa"]]
        if d_osa(x, z, pts) < e.get("pulsirka_m", 1.0) + 0.6:
            chyba("stul", "(%.0f, %.0f)" % (x, z), "%s na hline cesty %s" % (id_, e["id"]))

# ------------------------------------------------------------------ lomova stena (Misa 28. 10. „lom je nizky“)
LOMJ = json.load(open(os.path.join(SV, "plochy.json")))["lom"]
import fort  # noqa: E402  (vysledny teren vcetne lomu; vysky.json je teren pred stavbami)
nizka = []
zz = LOMJ["z"][0] + LOMJ["okraj_m"]
while zz < LOMJ["z"][1] - LOMJ["okraj_m"]:
    hore = max(fort.land(LOMJ["pata_x"] - 3.0 - k, zz) for k in range(0, 6))
    dole = fort.land(LOMJ["pata_x"] + 3.0, zz)
    if hore - dole < LOMJ["stena_min_m"]:
        nizka.append((round(zz), round(hore - dole, 1)))
    zz += 5.0
if nizka:
    chyba("lom", "stena", "lomova stena nizsi nez %.0f m v %d mistech, napr. %s" % (LOMJ["stena_min_m"], len(nizka), nizka[:4]))

# ------------------------------------------------------------------ rybniky: odtok za hrazi, breh po obvodu hladiny
# Misa 9. 11. r. 61/79 („bila hladina nad terenem, hlineny sraz kolem“, „kolikrat jsme to resili“): odtok zacinal uvnitr
# hraze 1,3-1,6 m pod hladinou, koryto a dolina hraz rozkopaly -> dira v hrazi, hladina visela nad terenem.
sys.path.insert(0, os.path.join(ROOT, "tools", "krok_b"))
import odtok_za_hrazi  # noqa: E402
VJ = J("voda.json")
for tid, n, p0 in odtok_za_hrazi.v_hrazi(VJ):
    if n:
        chyba("odtok_za_hrazi", tid, "%d bodu osy odtoku v telese hraze (koryto by hraz rozkopalo) - tools/krok_b/odtok_za_hrazi.py --zapis" % n)
# breh rybnika tvrze (generuje kraj.py): po obvodu hladiny (ryb_polomer + presah, jako Rybnik_tvrz_voda) teren
# vysledku (fort.land) ne pod hladinou - mez a pas z pasma.test breh_nadrzi_* (jako test breh_nadrzi ve hre), svah
# brehu do voda.json toky_tvar.breh_max_st; okraj hladiny kraj.ryb_hladina_r (stejne jako export)
PT_ = pt
for ryb in kraj.RYBNIKY:
    if "polomer_m" not in ryb:
        continue
    hl = ryb["hladina_y"]
    visi, sraz = [], []
    for k in range(0, 360, 3):
        a = math.radians(k)
        cx, cz = ryb["stred"]
        r = kraj.ryb_hladina_r(ryb, a, fort.land)
        py = None
        nj = int(PT_["breh_nadrzi_pas_m"] / 0.5)
        for j in range(0, nj + 1):
            x, z = cx + math.cos(a) * (r + 0.5 * j), cz + math.sin(a) * (r + 0.5 * j)
            tn_ = kraj.tok_near(x, z)
            if tn_ is not None and tn_[0] < tn_[2] + VJ["toky_tvar"]["breh_sirka_m"]:
                break                       # ustí toku: voda toku, ne breh rybnika
            y = fort.land(x, z)
            # okraj hladiny pod terenem (j = 0) = voda visi; na konci pasu porad pod hladinou = prorva (dira v brehu,
            # vypust) - i v dvojnasobku pasu; melka prohlubenka za valem brehu neni chyba (voda tam nedotece)
            dal = fort.land(cx + math.cos(a) * (r + 1.0 * nj), cz + math.sin(a) * (r + 1.0 * nj)) if j == nj else y
            if (j == 0 or j == nj) and max(y, dal if j == nj else y) < hl - PT_["breh_nadrzi_visi_m"]:
                visi.append((round(x), round(z), round(hl - y, 2), "visi" if j == 0 else "prorva"))
                break
            if py is not None and math.degrees(math.atan2(abs(y - py), 0.5)) > VJ["toky_tvar"]["breh_max_st"]:
                sraz.append((round(x), round(z)))
                break
            py = y
    if visi:
        chyba("breh_nadrze", "rybnik_tvrz", "hladina %.2f nad terenem po obvodu v %d smerech z 120 (napr. %s)" % (hl, len(visi), visi[:30]))
    if sraz:
        chyba("breh_nadrze", "rybnik_tvrz", "sraz u vody v %d smerech (napr. %s)" % (len(sraz), sraz[:4]))
    print("SMYSL breh rybnika %.2f: obvod 120 smeru, visi %d, sraz %d" % (hl, len(visi), len(sraz)))

# vyslapano (Misa 15. 11. ř. 11: „okolo kovarny jen louka, ve vsi moc travy“, Puchart usedlosti.vyslapano): KAZDA stavba
# vsi (vesnice.stavby_vsi - usedlosti, kovarna, dum kovare, krcma, chalupa u vetrniku) ma vstup, pas hliny okap_m kolem
# pudorysu a plochu pred kazdym vstupem (kraj.placek = barva i masky trsu). Seznam se nepise rucne: kazdy zaznam lokace
# s modelem a stredem do ves.rovina_r_m od navsi a kazdy vnoreny dum (model z ves.domy_podezdivka) musi v nem byt.
import vesnice  # noqa: E402
_LV = lok["ves"]
_VY = _LV["vyslapano"]
_SV = vesnice.stavby_vsi()
_ids = {s_["id"] for s_ in _SV}
_chce = ["ves_dum_%d" % u["k"] for u in _LV["usedlosti"]]
for _kl, _zv in lok.items():
    if not isinstance(_zv, dict):
        continue
    if "stred" in _zv and "model" in _zv and math.dist(_zv["stred"], _LV["stred_stare_navsi"]) < _LV["rovina_r_m"]:
        _chce.append(_kl)
    for _k2, _z2 in _zv.items():
        if isinstance(_z2, dict) and "stred" in _z2 and _z2.get("model") in _LV["domy_podezdivka"]:
            _chce.append(_kl + "." + _k2)
for _i in _chce:
    if _i not in _ids:
        chyba("vyslapano", _i, "stavba neni ve vesnice.stavby_vsi (bez okapu a hliny pred vstupem) - doplnit pudorys a vstupy do dat")
_HL = _VY["hlina"]
for s_ in _SV:
    if not s_["vstupy"]:
        chyba("vyslapano", s_["id"], "stavba bez vstupu (vstupy_domu / vstupy_hosp / vstupy_lok)")
    spat = []
    for x0, x1, z0, z1 in s_["boxy"]:
        h_ = _VY["okap_m"] / 2
        for mx, mz in (((x0 + x1) / 2, z1 + h_), ((x0 + x1) / 2, z0 - h_), (x1 + h_, (z0 + z1) / 2), (x0 - h_, (z0 + z1) / 2),
                       (x0 - h_, z0 - h_), (x1 + h_, z0 - h_), (x0 - h_, z1 + h_), (x1 + h_, z1 + h_)):
            if kraj.placek(*vesnice.svet_bod(s_, mx, mz)) < _HL["okap"] - 0.01:
                spat.append(("okap", round(mx, 1), round(mz, 1)))
    for px, pz, nx, nz, w in s_["vstupy"]:
        sx, sz = -nz, nx
        q = w / 2 + _VY["pred_okraj_m"] - 0.05
        t = _VY["pred_vstupem_m"] - 0.05
        for a, b in ((t / 2, 0.0), (t, q), (t, -q), (0.1, q), (0.1, -q)):
            mx, mz = px + nx * a + sx * b, pz + nz * a + sz * b
            if kraj.placek(*vesnice.svet_bod(s_, mx, mz)) < _HL["pred_vstupem"] - 0.01:
                spat.append(("pred_vstupem", round(mx, 1), round(mz, 1)))
    if spat:
        chyba("vyslapano", s_["id"], "tráva tam, kde se chodí (%d bodů, souřadnice modelu): %s" % (len(spat), spat[:6]))
# dvere domu: ves.vyslapano.vstupy_domu = svet.gd DUM_MER vstup/dvur (hra vede chodnicky ke stejnym dverim)
_sg = open(os.path.join(ROOT, "scripts", "svet.gd"), encoding="utf-8").read()
for _typ, _vs in _VY["vstupy_domu"].items():
    _m = re.search(r'"%s": \{"vstup": (-?[\d.]+), "dvur": (-?[\d.]+)' % _typ, _sg)
    if not _m or abs(float(_m.group(1)) - _vs[0][1]) > 0.01 or abs(float(_m.group(2)) - _vs[1][1]) > 0.01:
        chyba("vyslapano", _typ, "vstupy_domu %s nesouhlasi se svet.gd DUM_MER vstup/dvur (%s)" % (_vs, _m.groups() if _m else "chybi"))
print("SMYSL vyslapano: %d staveb vsi, %d vstupu" % (len(_SV), sum(len(s_["vstupy"]) for s_ in _SV)))

# okraj_stavby (rozpor #8, docs/rozpracovane/rozpory_blender_godot.md): JEDEN obrys domu vsi pro Blender i hru. Blender:
# placka (vesnice._pads) = podezdivka ves.domy_podezdivka + pasma.budova.placka_okraj_m, okraj_stavby (barva terenu a maska
# trsu) od ni; hra: louka._v_budove = svet._dum_zabira (DUM_MER z tychz domy_podezdivka, ramec _domy_ramce = stavby_vsi
# dum) + pasma.budova.prah_m. Kontrola: (a) kazdy dum stavby_vsi ma placku se stejnym stredem a rozmerem (podezdivka +
# placka_okraj_m), (b) v pasmu prah_m za zdi je Blender okraj_stavby 0 (udusana hlina, maska trsu 0) - hra tam travu
# zakazuje taky, zadny pas, kde jedno pravidlo travu ma a druhe ne.
_PB = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json"), encoding="utf-8"))["pasma"]["budova"]
_pady = vesnice._pads()
_okr_n = 0
for s_ in _SV:
    if not s_["id"].startswith("ves_dum_") or len(s_["boxy"]) != 1:
        continue
    x0, x1, z0, z1 = s_["boxy"][0]
    if not any(abs(x1 - m_["hw"]) < 1e-6 and abs(z0 - m_["b"]) < 1e-6 and abs(z1 - m_["f"]) < 1e-6 for m_ in _LV["domy_podezdivka"].values()):
        continue                                      # stara chalupa Blenderu (bez domy_typ) - hra ji nestavi
    cx_, cz_ = vesnice.svet_bod(s_, 0.0, (z0 + z1) / 2.0)
    hu_, hv_ = (z1 - z0) / 2.0 + _PB["placka_okraj_m"], (x1 - x0) / 2.0 + _PB["placka_okraj_m"]
    shoda = [p for p in _pady if math.hypot(p[0].x - cx_, p[0].z - cz_) < 0.05 and abs(p[3] - hu_) < 0.05 and abs(p[4] - hv_) < 0.05]
    if not shoda:
        bl = min(_pady, key=lambda p: math.hypot(p[0].x - cx_, p[0].z - cz_))
        chyba("okraj_stavby", s_["id"], "placka Blenderu nesedi na podezdivku domu hry: stred %.2f m vedle, polodelky %.2f/%.2f x %.2f/%.2f" % (
            math.hypot(bl[0].x - cx_, bl[0].z - cz_), bl[3], hu_, bl[4], hv_))
    pr_ = _PB["prah_m"]
    trava = []
    for mx, mz in ((0.0, z1 + pr_), (0.0, z0 - pr_), (x1 + pr_, (z0 + z1) / 2), (x0 - pr_, (z0 + z1) / 2),
                   (x0 - pr_, z0 - pr_), (x1 + pr_, z0 - pr_), (x0 - pr_, z1 + pr_), (x1 + pr_, z1 + pr_)):
        o_ = vesnice.okraj_stavby(*vesnice.svet_bod(s_, mx, mz))
        if o_ > 0.0:
            trava.append((round(mx, 2), round(mz, 2), round(o_, 2)))
    if trava:
        chyba("okraj_stavby", s_["id"], "v pasmu prah_m %.2f m za zdi Blender okraj_stavby > 0 (trsy), hra tam travu zakazuje: %s" % (pr_, trava[:4]))
    _okr_n += 1
print("SMYSL okraj_stavby: %d domu vsi, placka = podezdivka + %.2f m, prah %.2f m v udusanem okraji" % (_okr_n, _PB["placka_okraj_m"], _PB["prah_m"]))

# plot_ulice (rozpor #11): ploty usedlosti (vesnice.ploty_usedlosti - totez stavi build) nelezi na hline ulice ani v
# nejsirsim rozbitem okraji hry. Hra plot na hline usekne (svet._ves_site_vyrez podle cesta_kraj_osa = cesta_ok), Blender
# kresli hlinu ulice podle pulsirky (ves_ramec.ulice_pas). Obalka okraje hry = pulsirka x (1 + soucet amplitud sumu) +
# amplituda v metrech - cisla ctena z svet.gd cesta_ok (|_vln| <= 1), ne opsana. Mez: aspon 0 m za obalkou.
import ves_ramec  # noqa: E402
_mok = re.search(r"static func cesta_ok\(hw: float, s: float, sd: float\) -> float:\s*return hw \* \(1\.0 \+ ([\d.]+) \* _vln\([^)]*\) \+ ([\d.]+) \* _vln\([^)]*\)\) \+ ([\d.]+) \* _vln", _sg)
if not _mok:
    chyba("plot_ulice", "svet.gd", "cesta_ok nenalezena nebo zmeneny tvar - obalku okraje hliny nejde precist")
else:
    _a1, _a2, _am = (float(g_) for g_ in _mok.groups())
    _osa_u = ves_ramec.osa_ulice()
    _plot_nej = (1e9, None)
    _plot_zle = []
    for h_ in vesnice.layout():
        if not h_.get("novy_ramec"):
            continue
        for nm_, pts_ in vesnice.ploty_usedlosti(h_).items():
            for a_, b_ in zip(pts_, pts_[1:]):
                n_ = int((b_ - a_).length / 0.25) + 1
                for i_ in range(n_ + 1):
                    q_ = a_ + (b_ - a_) * (i_ / n_)
                    bi_, d_ = ves_ramec._blizko(q_.x, q_.z)
                    if bi_ < 0:
                        continue
                    hw_ = ves_ramec.pulsirka(bi_ / max(len(_osa_u) - 1, 1))
                    e_ = d_ - (hw_ * (1.0 + _a1 + _a2) + _am)
                    if e_ < _plot_nej[0]:
                        _plot_nej = (e_, (round(q_.x, 1), round(q_.z, 1), nm_))
                    if e_ < 0.0:
                        _plot_zle.append((round(q_.x, 1), round(q_.z, 1), nm_, round(e_, 2)))
    if _plot_zle:
        chyba("plot_ulice", "ves", "%d bodu plotu v obalce okraje hliny ulice (hra je usekne): %s" % (len(_plot_zle), _plot_zle[:5]))
    print("SMYSL plot_ulice: nejblize %.2f m za obalkou okraje ulice %s (obalka pulsirka x %.2f + %.2f m)" % (
        _plot_nej[0], _plot_nej[1], 1.0 + _a1 + _a2, _am))

# ves_barva (Misa 15. 11. ř. 10: „bile budovy vzadu ve vsi nechci, chci hnede jako Puchart“): stredni stupen (barvy
# vrcholu domy_stredni.glb) a hruby obal _Daleko (barva materialu domy.glb) kazdeho domu: prumer sRGB R > G > B a jas
# nejvys modely.json ves_jas.stredni_daleko.test_jas_max (bez hnedeho cinitele 0,5 a seda). Soubory jsou vystup
# blender/ves_domy.py + tools/zesvetli_ves.py (krok 16 exportu); chybi-li (kontejner bez zdroju vsi) = NEOVERENO.
_SDJ = J("modely.json")["ves_jas"]["stredni_daleko"]
_LUMK = (0.2126, 0.7152, 0.0722)


def _srgb1(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * max(c, 0.0) ** (1 / 2.4) - 0.055


def _glb_json(p):
    import struct
    d_ = open(p, "rb").read()
    jl_ = struct.unpack("<I", d_[12:16])[0]
    return json.loads(d_[20:20 + jl_]), d_[28 + jl_:]


def _ves_barva(koren, rgb, kde):
    jas_ = sum(a * b for a, b in zip(rgb, _LUMK))
    ok_ = rgb[0] > rgb[1] > rgb[2] and jas_ <= _SDJ["test_jas_max"]
    print("SMYSL ves_barva %s %s: sRGB %s jas %.2f%s" % (kde, koren, [round(c, 2) for c in rgb], jas_, "" if ok_ else " CHYBA"))
    if not ok_:
        chyba("ves_barva", koren, "%s: prumer sRGB %s jas %.2f - ne hneda (R>G>B) nebo nad test_jas_max %.2f (tools/zesvetli_ves.py krok 5)"
              % (kde, [round(c, 2) for c in rgb], jas_, _SDJ["test_jas_max"]))


_pS, _pD = os.path.join(ROOT, "modely", "ves", "domy_stredni.glb"), os.path.join(ROOT, "modely", "ves", "domy.glb")
if not (os.path.exists(_pS) and os.path.exists(_pD)):
    print("SMYSL ves_barva NEOVERENO: chybi modely/ves/domy_stredni.glb nebo domy.glb (zdroje vsi v kontejneru nejsou)")
else:
    import numpy as _np
    _js, _b = _glb_json(_pS)
    for _nd in _js["nodes"]:
        if "mesh" not in _nd or not _nd.get("name", "").endswith("_Stredni"):
            continue
        _sum, _n = _np.zeros(3), 0
        for _pr in _js["meshes"][_nd["mesh"]]["primitives"]:
            _ai = _pr["attributes"].get("COLOR_0")
            if _ai is None:
                continue
            _a = _js["accessors"][_ai]
            _v = _js["bufferViews"][_a["bufferView"]]
            _k = {"VEC3": 3, "VEC4": 4}[_a["type"]]
            _dt = {5126: _np.float32, 5121: _np.uint8, 5123: _np.uint16}[_a["componentType"]]
            _sz = _np.dtype(_dt).itemsize
            _st = _v.get("byteStride", 0) or _k * _sz
            _off = _v.get("byteOffset", 0) + _a.get("byteOffset", 0)
            _raw = _np.frombuffer(_b, _np.uint8, _st * (_a["count"] - 1) + _k * _sz, _off)
            _ix = (_np.arange(_a["count"])[:, None] * _st + _np.arange(_k * _sz)[None, :]).ravel()
            _c = _raw[_ix].view(_dt).reshape(-1, _k)[:, :3].astype(float) / {5126: 1.0, 5121: 255.0, 5123: 65535.0}[_a["componentType"]]
            # COLOR_0 uz prevedene do sRGB (tools/barvy_vrcholu.py, znacka v asset.extras; Misa 17. 11. r. 5) se neprevadi znovu
            if not _js.get("asset", {}).get("extras", {}).get(J("barvy_vrcholu.json")["znacka"]):
                _c = _np.where(_c <= 0.0031308, _c * 12.92, 1.055 * _np.power(_np.clip(_c, 0, None), 1 / 2.4) - 0.055)
            _sum += _c.sum(0)
            _n += len(_c)
        if _n:
            _ves_barva(_nd["name"][:-len("_Stredni")], list(_sum / _n), "stredni")
    _js, _b = _glb_json(_pD)
    for _nd in _js["nodes"]:
        if "mesh" not in _nd or not _nd.get("name", "").endswith("_Daleko"):
            continue
        _cs = []
        for _pr in _js["meshes"][_nd["mesh"]]["primitives"]:
            _pbr = _js["materials"][_pr["material"]].get("pbrMetallicRoughness", {}) if "material" in _pr else {}
            if "baseColorTexture" not in _pbr:
                _cs.append([_srgb1(c) for c in _pbr.get("baseColorFactor", [1, 1, 1])[:3]])
        if _cs:
            _ves_barva(_nd["name"][:-len("_Daleko")], [sum(c[i] for c in _cs) / len(_cs) for i in range(3)], "daleko")

# ------------------------------------------------------------------ rybnik v2: vtok, hladina bez hrany, voda jen nad dnem, vypust
# Misa 15. 11. r. 13 („pritok a odtok porad spatne“, 7 oprav vzdy jedne vrstvy): rybnik z jednoho zaznamu voda.json
# (obrys, vtok, vypust) - kontroly stejnymi funkcemi, jake stavi export (kraj.ryb2_*), na vyslednem terenu fort.land.
for ryb in kraj.RYBNIKY:
    if "obrys" not in ryb:
        continue
    hl = ryb["hladina_y"]
    vt, vy = ryb["vtok"], ryb["vypust"]
    pts_o = kraj.ryb2(ryb)["pts"]
    # rybnik_vtok: pritok kolmo na kraj vody (+-30 st.), skok hladiny <= 2 cm, na hladinu rybnika az v usti, osa ne podel
    # brehu, dno koryta proti proudu stoupa
    tkj = next(t for t in VJ["toky"] if t["id"] == vt["tok"])
    o_ = tkj["osa_xzy"]
    bx_, bz_ = vt["bod"]
    _, seg_i = min((dseg(bx_, bz_, a, b)[0], k) for k, (a, b) in enumerate(zip(pts_o, pts_o[1:] + pts_o[:1])))
    a_, b_ = pts_o[seg_i], pts_o[(seg_i + 1) % len(pts_o)]
    tl_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1]) or 1.0
    nrm = (-(b_[1] - a_[1]) / tl_, (b_[0] - a_[0]) / tl_)
    if kraj.ryb_de(ryb, bx_ + nrm[0] * 0.3, bz_ + nrm[1] * 0.3) < 0:
        nrm = (-nrm[0], -nrm[1])                          # normala do vody
    uhel = lambda u, v: math.degrees(math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))))
    if abs(kraj.ryb_de(ryb, bx_, bz_)) > 0.1:
        chyba("rybnik_vtok", "(%.0f, %.0f)" % (bx_, bz_), "bod vtoku %.2f m od kraje vody (obrys)" % kraj.ryb_de(ryb, bx_, bz_))
    if uhel(vt["smer"], nrm) > 30.0:
        chyba("rybnik_vtok", "(%.0f, %.0f)" % (bx_, bz_), "smer vtoku %.0f st. od kolmice na kraj vody (max 30)" % uhel(vt["smer"], nrm))
    if math.hypot(o_[-1][0] - bx_, o_[-1][1] - bz_) > 0.1:
        chyba("rybnik_vtok", vt["tok"], "osa nekonci ve vtoku (%.2f m)" % math.hypot(o_[-1][0] - bx_, o_[-1][1] - bz_))
    s_, k_ = 0.0, len(o_) - 1
    while k_ > 0 and s_ < 3.0:
        s_ += math.hypot(o_[k_][0] - o_[k_ - 1][0], o_[k_][1] - o_[k_ - 1][1])
        k_ -= 1
    d_ = ((o_[-1][0] - o_[k_][0]) / (s_ or 1.0), (o_[-1][1] - o_[k_][1]) / (s_ or 1.0))
    if uhel(d_, nrm) > 30.0:
        chyba("rybnik_vtok", vt["tok"], "poslednich 3 m osy %.0f st. od kolmice na kraj vody (max 30)" % uhel(d_, nrm))
    skok = o_[-1][2] - hl
    if not 0.0 <= skok <= 0.02 + 1e-6:
        chyba("rybnik_vtok", vt["tok"], "skok hladiny ve vtoku %.3f m (0..0,02)" % skok)
    s_ = 0.0
    dno_p = None
    podel, plocho, dno_dolu = [], [], []
    for k_ in range(len(o_) - 1, 0, -1):
        x_, z_, y_ = o_[k_]
        if s_ > 0.5 and -kraj.ryb_de(ryb, x_, z_) < 0.5 * s_:
            podel.append((round(x_), round(z_)))
        if s_ > vt["usti_m"] and y_ <= hl + vt["skok_m"] + 1e-3:
            plocho.append((round(x_), round(z_)))
        dno = fort.land(x_, z_)
        if dno_p is not None and dno < dno_p - 0.02:
            dno_dolu.append((round(x_), round(z_), round(dno_p - dno, 2)))
        dno_p = dno
        s_ += math.hypot(o_[k_][0] - o_[k_ - 1][0], o_[k_][1] - o_[k_ - 1][1])
        if s_ > 15.0:
            break
    if podel:
        chyba("rybnik_vtok", vt["tok"], "osa vede podel brehu (od kraje mene nez polovina vzdalenosti od vtoku) %s" % podel[:5])
    if plocho:
        chyba("rybnik_vtok", vt["tok"], "hladina pritoku na urovni rybnika uz pred ustim (%.1f m) %s" % (vt["usti_m"], plocho[:5]))
    if dno_dolu:
        chyba("rybnik_vtok", vt["tok"], "dno koryta proti proudu klesa %s" % dno_dolu[:5])
    # voda_bez_hrany (Puchart test_smyslu): kazda okrajova hrana hladiny ma vrchol s kryti 0 (hloubka 0), krome rezu vtoku;
    # kontrola_vody (Puchart): voda jen nad vyhloubenym dnem - vrchol hladiny s hloubkou > 0 nad terenem nad hladinou ne,
    # a bod mrizky (stredy bunek 0,5 m) pod siti hladiny ma teren pod hladinou; dno pod hladinou uvnitr obrysu ma vodu
    vs_, tr_, hh_, rez_ = kraj.ryb2_hladina_sit(ryb, fort.land)
    kr_ = kraj.ryb2_kraj(vs_, tr_, hh_)
    tvrde = [(round(vs_[i][0], 1), round(vs_[i][2], 1)) for i, j in kr_ if hh_[i] > 0.01 and hh_[j] > 0.01 and not (rez_[i] and rez_[j])]
    if not tr_ or tvrde:
        chyba("voda_bez_hrany", "rybnik", "hladina %d troj., tvrdych hran na kraji %d %s" % (len(tr_), len(tvrde), tvrde[:6]))
    mriz_ = {}
    for t_ in tr_:
        xs_ = [vs_[i][0] for i in t_]
        zs_ = [vs_[i][2] for i in t_]
        for gi in range(int(math.floor(min(xs_))), int(math.ceil(max(xs_))) + 1):
            for gj in range(int(math.floor(min(zs_))), int(math.ceil(max(zs_))) + 1):
                mriz_.setdefault((gi, gj), []).append(t_)

    def pod_hladinou(x, z):
        for t_ in mriz_.get((int(math.floor(x)), int(math.floor(z))), []):
            (ax, _, az), (bx, _, bz), (cx_, _, cz_) = (vs_[i] for i in t_)
            d1 = (x - bx) * (az - bz) - (ax - bx) * (z - bz)
            d2 = (x - cx_) * (bz - cz_) - (bx - cx_) * (z - cz_)
            d3 = (x - ax) * (cz_ - az) - (cx_ - ax) * (z - az)
            if not ((d1 < -1e-9 or d2 < -1e-9 or d3 < -1e-9) and (d1 > 1e-9 or d2 > 1e-9 or d3 > 1e-9)):
                return True
        return False
    nad_brehem, bez_vody = [], []
    bb_ = kraj.ryb2(ryb)["bb"]
    zx = bb_[0] - 3.0
    while zx < bb_[1] + 3.0:
        zz = bb_[2] - 3.0
        while zz < bb_[3] + 3.0:
            y_ = fort.land(zx, zz)
            pv = pod_hladinou(zx, zz)
            if pv and y_ > hl + 0.02:
                nad_brehem.append((round(zx, 1), round(zz, 1), round(y_ - hl, 2)))
            if not pv and y_ < hl - 0.05 and kraj.ryb_de(ryb, zx, zz) > 0.3 and kraj.ryb2_vtok_rez(ryb, zx, zz) is None:
                bez_vody.append((round(zx, 1), round(zz, 1), round(hl - y_, 2)))
            zz += 0.5
        zx += 0.5
    if nad_brehem:
        chyba("kontrola_vody", "rybnik", "hladina nad brehem (teren nad hladinou pod siti vody) v %d bodech %s" % (len(nad_brehem), nad_brehem[:6]))
    if bez_vody:
        chyba("kontrola_vody", "rybnik", "dno pod hladinou bez vody v %d bodech %s" % (len(bez_vody), bez_vody[:6]))
    # vypust: odtok zacina <= 1 m za licem cela vypusti, pred nim (po proudu), v hladine vypusti
    tko = next(t for t in VJ["toky"] if t["id"] == vy["tok"])
    p0 = tko["osa_xzy"][0]
    dv = math.hypot(p0[0] - vy["celo"][0], p0[1] - vy["celo"][1])
    tv = (p0[0] - vy["celo"][0]) * vy["smer"][0] + (p0[1] - vy["celo"][1]) * vy["smer"][1]
    if dv > 1.0 or tv <= 0.0 or abs(p0[2] - vy["hladina_y"]) > 0.005:
        chyba("vypust", vy["tok"], "odtok zacina %.2f m od cela vypusti (max 1 m, pred licem %.2f), hladina %.3f / vypust %.3f" % (dv, tv, p0[2], vy["hladina_y"]))
    # preliv_vypust (Misa 17. 11. r. 2, snimek 03 x 501 z 881: „kvadry nesedi na sebe“): dlazba prelivu s obrubou (pas
    # v ramci hraze a .. a + sirka/2 + obruba, t od navodni hrany koruny - presah po konec + presah) nesmi zasahovat do zdi
    # cela ani kridel vypusti (osa zdi kraj.ryb2_vypust_zdi, pul tloustky + spara dlazby). 16. 11.: kridlo l1 (1,6 m pod
    # 45 st.) prochazelo pres obrubu a dlazbu v t 4,7-5,3 m.
    if "preliv" in ryb and "dlazba" in ryb["preliv"]:
        g_ = kraj.ryb2(ryb)
        pr_, dl_ = ryb["preliv"], ryb["preliv"]["dlazba"]
        ap_, t0_, t1_, _y0, _y1 = kraj.ryb2_preliv(ryb)
        sir_ = pr_["sirka_m"] / 2.0 + dl_["obruba_sirka_m"]
        ta_, tb_ = t0_ - dl_["presah_m"], t1_ + dl_["presah_m"]
        hz_ = ryb["hraz"]
        kolize_pv = []
        for (pa, pb) in kraj.ryb2_vypust_zdi(ryb):
            L_ = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
            for i_ in range(int(L_ / 0.05) + 1):
                f_ = i_ * 0.05 / max(L_, 1e-6)
                qx, qz = pa[0] + (pb[0] - pa[0]) * f_, pa[1] + (pb[1] - pa[1]) * f_
                a_q = (qx - hz_["stred"][0]) * g_["u"][0] + (qz - hz_["stred"][1]) * g_["u"][1]
                t_q = (qx - hz_["stred"][0]) * g_["n"][0] + (qz - hz_["stred"][1]) * g_["n"][1]
                da = max(0.0, abs(a_q - ap_) - sir_)
                dt = max(0.0, ta_ - t_q, t_q - tb_)
                if math.hypot(da, dt) < kraj.ZED_VYPUSTI_M / 2.0 + dl_["spara_m"]:
                    kolize_pv.append((round(qx, 2), round(qz, 2)))
        if kolize_pv:
            chyba("preliv_vypust", "rybnik", "dlazba prelivu (osa a %.2f, +-%.2f m) zasahuje do zdi vypusti v %d bodech %s" % (
                ap_, sir_, len(kolize_pv), kolize_pv[:4]))
        print("SMYSL preliv: osa a %.2f m, pas +-%.2f, t %.2f..%.2f; kolize se zdi vypusti %d" % (ap_, sir_, ta_, tb_, len(kolize_pv)))
        # preliv_rostliny (Misa 17. 11. r. 2: „trava roste skrz dlazbu“): v exportu (--po, modely/svet.json rostliny)
        # zadna rostlina na dlazbe prelivu ani na zdi vypusti (kraj.ryb2_stavba) - hra by kvadry dlazby u mekke rostliny
        # vyradila jako kolize rostlin a kryti louky by dlazbu nevidelo
        _sj = os.path.join(ROOT, "modely", "svet.json")
        if "--po" in sys.argv and os.path.exists(_sj):
            _na = []
            for _k, _v in json.load(open(_sj))["rostliny"].items():
                for _t in _v:
                    if kraj.ryb2_stavba(float(_t[3]), float(_t[11]), kraj.RYB2_BEZ_ROSTLIN_M):
                        _na.append("%s (%.1f, %.1f)" % (_k, _t[3], _t[11]))
            if _na:
                chyba("preliv_rostliny", "rybnik", "%d rostlin na dlazbe prelivu / zdi vypusti %s" % (len(_na), _na[:5]))
            print("SMYSL preliv_rostliny: %d" % len(_na))
    print("SMYSL rybnik v2: vtok %.0f st. od kolmice, skok %.3f m; hladina %d troj., okraj %d hran, tvrdych %d; nad brehem %d, bez vody %d; odtok %.2f m od cela" % (
        uhel(vt["smer"], nrm), skok, len(tr_), len(kr_), len(tvrde), len(nad_brehem), len(bez_vody), dv))

# ------------------------------------------------------------------ houstina: clony, zelen ulice, meze, breh (16. 11.)
# Misa 15./16. 11. (sceny_kcd_15_11.md, les_podrost.json houstina): kazdy kus houstiny z generatoru (pred exportem
# z dat) zvlast prepocitanymi pravidly: ne na ceste ani pesine (pasma.cesta ker_od_m / kmen_m od kraje), ne na hline
# ulice, ve vode ani na holem brehu (Bystrice i male toky), v pruchodu zriceniny, ve zdi, ve vstupu (pasma.budova
# pruchod_m + dvur_m), na vysalpane hline dvoru, ve vyhledu; clona nikdy pres reku (okluzor pres vodu).
try:
    import random as _rnd
    import vesnice as _ves
    import ves_ramec as _vr
    _pas = json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]
    _pc, _pb, _pv = _pas["cesta"], _pas["budova"], _pas["voda"]
    _cj = J("cesty.json")
    _osy = [([tuple(q) for q in e["osa"]], e.get("pulsirka_m", e.get("blender_sirka_m", 2 * _cj["pesina_zaklad_m"]) / 2.0),
             e.get("typ", "vozova")) for e in _cj["vozove"] + _cj["pesiny"] if len(e.get("osa") or []) > 1]
    _vyh = J("lokace.json").get("kompozice", {}).get("vyhledy", [])
    _Rt = _rnd.Random(1515)
    _kusy = [("clona:" + q[4], q[0], q[1], q[2]) for q in kraj.clony(_Rt)]
    _kusy += [("ulice", q[0], q[1], q[2]) for q in _ves.zelen_ulice()]
    _kusy += [("mez", q[0], q[1], q[2]) for q in kraj.houstiny_meze(_Rt)]
    _kusy += [("breh", q[0], q[1], q[2]) for q in kraj.houstiny_breh(_Rt)]
    _zle = {}

    def _hz(druh, zd, pid, x, z, txt):
        _zle.setdefault(druh, []).append("%s %s (%.1f, %.1f) %s" % (zd, pid, x, z, txt))
    for zd, pid, x, z in _kusy:
        strom = kraj.je_strom(pid)
        for pts, pw, typ in _osy:
            if abs(pts[0][0] - x) > 2500:
                continue
            pp = _pc.get(typ, _pc["vozova"])
            d_ = d_osa(x, z, pts) - pw
            if d_ < (pp["kmen_m"] if strom else pp["ker_od_m"]):
                _hz("houstina_cesta", zd, pid, x, z, "%.1f m od kraje cesty (pasmo %s)" % (d_, typ))
                break
        if _vr.zapnuto() and _vr.od_kraje_hliny(x, z) < (_pc["ulice_vsi"]["kmen_m"] if strom else _pc["ulice_vsi"]["ker_od_m"]):
            _hz("houstina_cesta", zd, pid, x, z, "%.1f m od hliny ulice" % _vr.od_kraje_hliny(x, z))
        rv_ = kraj.river(x, z)
        if (rv_ is not None and rv_[0] < kraj._PO["pulsirka_vody_m"] * (1.0 + 0.75 * rv_[2]) + _pv["holy_breh_m"]) \
                or kraj.ve_vode(x, z, 1e9) < _pv["holy_breh_m"]:
            _hz("houstina_voda", zd, pid, x, z, "ve vode nebo na holem brehu")
        if kraj.v_pruchodu_ruiny(x, z):
            _hz("houstina_pruchod", zd, pid, x, z, "v pruchodu zriceniny")
        for e in _ves.stavby_vsi():
            ox, oz = e["o"]
            lx = (x - ox) * e["ex"][0] + (z - oz) * e["ex"][1]
            lz = (x - ox) * e["ez"][0] + (z - oz) * e["ez"][1]
            if abs(lx) > 60 or abs(lz) > 60:
                continue
            for x0, x1, z0, z1 in e["boxy"]:
                dz_ = math.hypot(max(x0 - lx, lx - x1, 0.0), max(z0 - lz, lz - z1, 0.0))
                if dz_ < (_pb["kmen_od_zdi_m"] if strom else _pb["plevel_u_zdi_m"]):
                    _hz("houstina_budova", zd, pid, x, z, "%.1f m od zdi %s" % (dz_, e["id"]))
            for vx, vz, nx_, nz_, w in e["vstupy"]:
                if math.hypot(lx - vx, lz - vz) < _pb["pruchod_m"] + w * 0.5 + _pb["dvur_m"]:
                    _hz("houstina_vstup", zd, pid, x, z, "ve vstupu %s" % e["id"])
        if _ves.vyslapano(x, z) > 0.0:
            _hz("houstina_dvur", zd, pid, x, z, "na vyslapane hline")
        for v in _vyh:
            if math.hypot(x - v["stred"][0], z - v["stred"][1]) < v["polomer_m"]:
                _hz("houstina_vyhled", zd, pid, x, z, "ve vyhledu %s" % v["id"])
    # clona (okluzor) nikdy pres reku: osa + pul sirky dal nez voda a holy breh
    for c in J("lokace.json").get("kompozice", {}).get("clony", []):
        for (ax, az), (bx, bz) in zip(c["osa"][:-1], c["osa"][1:]):
            for k_ in range(11):
                qx, qz = ax + (bx - ax) * k_ / 10, az + (bz - az) * k_ / 10
                rv_ = kraj.river(qx, qz)
                if rv_ is not None and rv_[0] < kraj._PO["pulsirka_vody_m"] * 1.75 + _pv["holy_breh_m"] + c["sirka_m"] / 2:
                    _hz("houstina_reka", "clona:" + c["id"], "osa", qx, qz, "clona zasahuje k vode reky (%.1f m od osy)" % rv_[0])
    for druh, lst in sorted(_zle.items()):
        chyba(druh, "%d kusu" % len(lst), "; ".join(lst[:5]))
    print("SMYSL houstina: %d kusu (clony %d, ulice %d, meze %d, breh %d), chyb %d" % (
        len(_kusy), sum(1 for q in _kusy if q[0].startswith("clona")), sum(1 for q in _kusy if q[0] == "ulice"),
        sum(1 for q in _kusy if q[0] == "mez"), sum(1 for q in _kusy if q[0] == "breh"), sum(len(v) for v in _zle.values())))
except Exception as ex_:
    chyba("podklad", "houstina", "generator houstiny selhal: %r" % ex_)

souhrn = {}
for c in CHYBY:
    souhrn[c] = souhrn.get(c, 0) + 1
print("SMYSL souhrn", souhrn if souhrn else "OK")
sys.exit(1 if CHYBY else 0)
