"""Matice vztahu (pravidla/svet/vztahy.json): kazda dvojice druhu ma pravidlo a testy, ktere existuji - jinak je to
dira v hlidani (Misa 28. 10.: hlidace na vsechno a ve vztahu ke vsem ostatnim). Test hry = funkce _<jmeno> v
tools/test_svet.gd, test smyslu = chyba("<druh>" v tools/test_smyslu.py, krok:meze_kroku = pasma.test.meze_kroku.
Vypise chybejici dvojice a testy, rc 1 (brana ve vydani.py)."""
import glob
import itertools
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = json.load(open(os.path.join(ROOT, "pravidla", "svet", "vztahy.json")))
hra = set(re.findall(r"^func _([a-z_]+)\(", open(os.path.join(ROOT, "tools", "test_svet.gd")).read(), re.M))
smysl = set(re.findall(r'chyba\("([a-z_]+)"', open(os.path.join(ROOT, "tools", "test_smyslu.py")).read())) | set(re.findall(r"SMYSL ([a-z_]+)", open(os.path.join(ROOT, "tools", "test_smyslu.py")).read()))
krok = {"meze_kroku"} if "meze_kroku" in json.load(open(os.path.join(ROOT, "pravidla", "pravidla_sveta.json")))["pasma"]["test"] else set()
zdroje = {"hra": hra, "smysl": smysl, "krok": krok}
dr = V["druhy"]
chyby = []
pokryto = 0
bez_sloupce = {}
for a, b in itertools.combinations_with_replacement(dr, 2):
    k = "%s|%s" % (a, b)
    e = V["dvojice"].get(k)
    if e is None:
        chyby.append("%s: dvojice v matici chybi" % k)
        continue
    if e.get("nezavisle"):
        if not e.get("duvod"):
            chyby.append("%s: nezavisle bez duvodu" % k)
        else:
            pokryto += 1
        continue
    if not e.get("smysl") and not e.get("pravidlo"):
        chyby.append("%s: chybi smysl" % k)
    for sl in ("estetika", "vykon"):
        if not e.get(sl):
            bez_sloupce.setdefault(sl, []).append(k)
    if not e.get("testy") and e.get("nenastava"):
        print("VZTAH %s: ve svete nenastava (%s)" % (k, e["nenastava"]))
        pokryto += 1
        continue
    if not e.get("testy"):
        chyby.append("%s: pravidlo bez testu" % k)
        continue
    spatne = [t for t in e["testy"] if t.split(":")[1] not in zdroje.get(t.split(":")[0], set())]
    if spatne:
        chyby.append("%s: test neexistuje %s" % (k, spatne))
    else:
        pokryto += 1
# podminena pravidla (radce 18:20 bod 2) a povoleni: znamy typ zdroje, existujici zaznam, duvod, dvojice z matice
VO = json.load(open(os.path.join(ROOT, "pravidla", "svet", "voda.json")))
CE = json.load(open(os.path.join(ROOT, "pravidla", "svet", "cesty.json")))
ver = re.search(r'config/version="([0-9.]+)', open(os.path.join(ROOT, "project.godot")).read())


def over_zdroj(co, z):
    if z.startswith("dil:"):
        dd = z[4:]
        if not ((dd == "mlyn" and VO.get("mlyn", {}).get("dil")) or (dd in VO and "stred" in VO[dd])):
            chyby.append("%s: dil %s v voda.json neni" % (co, dd))
    elif z == "prechody":
        if not CE.get("prechody"):
            chyby.append("%s: cesty.json prechody prazdne" % co)
    elif z not in ("pohyb:vrata", "geometrie:na_sobe", "geometrie:na_podlaze"):
        chyby.append("%s: neznamy zdroj %s" % (co, z))


for k, e in V["dvojice"].items():
    for pd in e.get("podminky", []):
        if not pd.get("smi_kdyz"):
            chyby.append("%s podminka %s: chybi smi_kdyz" % (k, pd.get("id")))
        over_zdroj("%s podminka %s" % (k, pd.get("id")), pd.get("zdroj", ""))
for pv in V.get("povoleni", []):
    co = "povoleni %s" % pv.get("id")
    if not pv.get("duvod"):
        chyby.append(co + " bez duvodu")
    for dv in pv.get("dvojice", []):
        if dv not in V["dvojice"]:
            chyby.append("%s: dvojice %s neni v matici" % (co, dv))
    over_zdroj(co, pv.get("zdroj", ""))
    for pole in ("schvalil", "plati_do", "max_pouziti", "rozsah"):
        if not pv.get(pole):
            chyby.append("%s: chybi %s" % (co, pole))
    if ver and pv.get("plati_do") and tuple(map(int, ver.group(1).split("."))) > tuple(map(int, str(pv["plati_do"]).split("."))):
        chyby.append("%s: proslo (plati do %s, verze %s)" % (co, pv["plati_do"], ver.group(1)))
for c in chyby:
    print("VZTAH " + c)
n = len(list(itertools.combinations_with_replacement(dr, 2)))
for sl, ks in bez_sloupce.items():
    print("VZTAH bez sloupce %s: %d dvojic (napr. %s)" % (sl, len(ks), ", ".join(ks[:6])))
print("matice vztahu: %d z %d dvojic s pravidlem a testem, %d der" % (pokryto, n, len(chyby)))
chyby += ["%s: chybi sloupec %s" % (k, sl) for sl, ks in bez_sloupce.items() for k in ks]

# --- dve cisla z behu testu (radce 18:20 bod 1+5): jen log k otisku tohoto exportu (OTISK <otisk> v logu)
try:
    OT = json.load(open(os.path.join(ROOT, "build", "export_otisk.json")))["otisk"]
except (OSError, ValueError, KeyError):
    OT = ""
log = sys.argv[sys.argv.index("--log") + 1] if "--log" in sys.argv else None
if log is None:             # nejnovejsi log testu, ktery bezel k tomuto otisku
    for f in sorted(glob.glob(os.path.join(ROOT, "build", "beh", "*_godot.log")), key=os.path.getmtime, reverse=True):
        tx = open(f, errors="replace").read()
        if OT and ("OTISK " + OT) in tx and "POKRYTI " in tx:
            log = f
            break
povinne = [k for k, e in V["dvojice"].items() if not e.get("nezavisle") and not e.get("nenastava")]
if log and os.path.exists(log):
    txt = open(log, errors="replace").read()
    if not OT or ("OTISK " + OT) not in txt:
        print("VYSLEDKY %s nejsou k otisku exportu %s - nepocitaji se" % (log, OT[:10]))
        txt = ""
else:
    txt = ""
kon = {m.group(1): int(m.group(2)) for m in re.finditer(r"^POKRYTI (\S+) (\d+)", txt, re.M)}
spatne_t = set(m.group(1) for m in re.finditer(r"^TEST (\S+)\s+CHYBA", txt, re.M))
bezelo = set(m.group(1) for m in re.finditer(r"^TEST (\S+)\s+(?:OK|CHYBA)", txt, re.M))
chyb_dv = {}
for m in re.finditer(r"^VZTAH (\S+\|\S+) \(", txt, re.M):
    chyb_dv[m.group(1)] = chyb_dv.get(m.group(1), 0) + 1
pokr, usp, nepokr, neusp = [], [], [], []
for k in povinne:
    hry = [t.split(":")[1] for t in V["dvojice"][k].get("testy", []) if t.startswith("hra:")]
    if hry:
        ok = (kon.get(k, 0) > 0) if k in kon or any(h in ("vztahy", "vztahy_hra") for h in hry) else any(h in bezelo for h in hry)
    else:
        ok = bool(V["dvojice"][k].get("testy"))       # smysl/krok: brany exportu (test_smyslu, meze_kroku)
    (pokr if ok else nepokr).append(k)
    if ok:
        bad = chyb_dv.get(k, 0) > 0 or any(h in spatne_t for h in hry if h not in ("vztahy", "vztahy_hra"))
        (neusp if bad else usp).append(k)
print("POKRYTI_MATICE %d/%d (%.0f %%)%s" % (len(pokr), len(povinne), 100.0 * len(pokr) / max(1, len(povinne)),
      "" if not nepokr else "; nepokryto: " + ", ".join(nepokr[:12])))
print("USPESNOST_MATICE %d/%d (%.0f %%)%s" % (len(usp), len(pokr), 100.0 * len(usp) / max(1, len(pokr)),
      "" if not neusp else "; s chybou: " + ", ".join(neusp[:12])))
print("vysledky z %s, otisk %s" % (os.path.relpath(log, ROOT) if log else "(zadny beh k otisku)", OT[:10]))
if "--vydani" in sys.argv:
    if not txt:
        chyby.append("zadny beh testu k otisku exportu")
    if nepokr or neusp:
        chyby.append("pokryti %d/%d, uspesnost %d/%d - nevydavat" % (len(pokr), len(povinne), len(usp), len(pokr)))
sys.exit(1 if chyby else 0)
