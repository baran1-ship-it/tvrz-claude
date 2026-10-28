"""Matice vztahu (pravidla/svet/vztahy.json): kazda dvojice druhu ma pravidlo a testy, ktere existuji - jinak je to
dira v hlidani (Misa 28. 10.: hlidace na vsechno a ve vztahu ke vsem ostatnim). Test hry = funkce _<jmeno> v
tools/test_svet.gd, test smyslu = chyba("<druh>" v tools/test_smyslu.py, krok:meze_kroku = pasma.test.meze_kroku.
Vypise chybejici dvojice a testy, rc 1 (brana ve vydani.py)."""
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
    if not e.get("testy"):
        chyby.append("%s: pravidlo bez testu" % k)
        continue
    spatne = [t for t in e["testy"] if t.split(":")[1] not in zdroje.get(t.split(":")[0], set())]
    if spatne:
        chyby.append("%s: test neexistuje %s" % (k, spatne))
    else:
        pokryto += 1
# povoleni: znamy typ zdroje, existujici zaznam, duvod, dvojice z matice
VO = json.load(open(os.path.join(ROOT, "pravidla", "svet", "voda.json")))
CE = json.load(open(os.path.join(ROOT, "pravidla", "svet", "cesty.json")))
for pv in V.get("povoleni", []):
    z = pv.get("zdroj", "")
    if not pv.get("duvod"):
        chyby.append("povoleni %s bez duvodu" % pv.get("id"))
    for dv in pv.get("dvojice", []):
        if dv not in V["dvojice"]:
            chyby.append("povoleni %s: dvojice %s neni v matici" % (pv.get("id"), dv))
    if z.startswith("dil:"):
        dd = z[4:]
        if not ((dd == "mlyn" and VO.get("mlyn", {}).get("dil")) or (dd in VO and "stred" in VO[dd])):
            chyby.append("povoleni %s: dil %s v voda.json neni" % (pv.get("id"), dd))
    elif z == "prechody":
        if not CE.get("prechody"):
            chyby.append("povoleni %s: cesty.json prechody prazdne" % pv.get("id"))
    elif z not in ("pohyb:vrata", "geometrie:na_sobe", "geometrie:na_podlaze"):
        chyby.append("povoleni %s: neznamy zdroj %s" % (pv.get("id"), z))
    for pole in ("schvalil", "plati_do", "max_pouziti"):
        if not pv.get(pole):
            chyby.append("povoleni %s: chybi %s" % (pv.get("id"), pole))
    ver = re.search(r'config/version="([0-9.]+)', open(os.path.join(ROOT, "project.godot")).read())
    if ver and pv.get("plati_do") and tuple(map(int, ver.group(1).split("."))) > tuple(map(int, str(pv["plati_do"]).split("."))):
        chyby.append("povoleni %s: proslo (plati do %s, verze %s)" % (pv.get("id"), pv["plati_do"], ver.group(1)))
# pokryti (radce 18:15): z posledniho logu testu - dvojice, ktere ve svete nastavaji, musi mit test, ktery neco
# zkontroloval (POKRYTI <dvojice> <pocet>); povoleni pouzite nad max_pouziti = chybejici pravidlo
log = sys.argv[sys.argv.index("--log") + 1] if "--log" in sys.argv else None
if log and os.path.exists(log):
    txt = open(log, errors="replace").read()
    kon = {m.group(1): int(m.group(2)) for m in re.finditer(r"^POKRYTI (\S+) (\d+)", txt, re.M)}
    for k, e in V["dvojice"].items():
        if "hra:vztahy" in e.get("testy", []) and kon.get(k, 0) == 0:
            chyby.append("%s: test vztahy v tomto behu nic nezkontroloval (pokryti 0)" % k)
    for m in re.finditer(r"^POVOLENI (\S+) (\d+)", txt, re.M):
        pv = next((x for x in V.get("povoleni", []) if x["id"] == m.group(1)), None)
        if pv and int(m.group(2)) > int(pv.get("max_pouziti", 0)):
            chyby.append("povoleni %s pouzito %s x (max %s) - to uz neni vyjimka, chybi pravidlo" % (m.group(1), m.group(2), pv["max_pouziti"]))
for c in chyby:
    print("VZTAH " + c)
n = len(list(itertools.combinations_with_replacement(dr, 2)))
for sl, ks in bez_sloupce.items():
    print("VZTAH bez sloupce %s: %d dvojic (napr. %s)" % (sl, len(ks), ", ".join(ks[:6])))
print("matice vztahu: %d z %d dvojic hlidano, %d der; bez estetiky %d, bez vykonu %d" % (pokryto, n, len(chyby), len(bez_sloupce.get("estetika", [])), len(bez_sloupce.get("vykon", []))))
chyby += ["%s: chybi sloupec %s" % (k, sl) for sl, ks in bez_sloupce.items() for k in ks]
sys.exit(1 if chyby else 0)
