"""Tabulka chyb (vrstva 7 z Havrana): každá chyba nalezená člověkem a označená jako opravená musí mít ve sloupci
„kontrola“ test (smysl:…, pruchod:…), který existuje a prošel, nebo výslovně snímek / měření na tabletu. Jinak se nevydává.
  python3 nastroje/kontrola_tabulek.py <koren>"""
import sys, re, json, os
K = sys.argv[1]
TS = json.load(open(K + "/build/test_smyslu.json"))["testy"] if os.path.exists(K + "/build/test_smyslu.json") else {}
PR = json.load(open(K + "/build/pruchod.json")) if os.path.exists(K + "/build/pruchod.json") else {}
chyby = []
for l in open(K + "/docs/chyby.md"):
    m = re.match(r"^\| (\d+) \|", l)
    if not m: continue
    c = [x.strip() for x in l.strip().strip("|").split("|")]
    stav, kontrola = c[-1].lower(), c[-2]
    if "opraven" not in stav: continue
    testy = re.findall(r"(smysl|pruchod|hlidac):([A-Za-z0-9_\-]+)", kontrola)
    if not testy:
        if not re.search(r"snímek|snimek|tablet|mereni|měření", kontrola): chyby.append("#%s bez kontroly" % m.group(1))
        continue
    for d, t in testy:
        if d == "hlidac":   # testy Godotu v hlidaci.sh s vlastním výpisem (KLIK_TEST, BEHLET_TEST) – výsledek z build/hlidaci.txt
            if "--rychle" in sys.argv: continue
            _ht = open(K + "/build/hlidaci.txt").read() if os.path.exists(K + "/build/hlidaci.txt") else ""
            ok = bool(re.search({"klik": r"KLIK_TEST dvere.*-> OK", "behlet": r"BEHLET_TEST OK", "louc": r"LOUC_TEST zapaleni.*-> OK"}.get(t, "^$NIKDY"), _ht))
            if not ok: chyby.append("#%s: hlidac:%s neprošel/neběžel" % (m.group(1), t))
            continue
        ok = TS.get(t, {}).get("ok") if d == "smysl" else (all(v == "OK" for v in PR.values()) if t == "vse" else PR.get(t) == "OK")
        if d == "pruchod" and "--rychle" in sys.argv: continue
        if not ok: chyby.append("#%s: %s:%s %s" % (m.group(1), d, t, "neprošel" if ok is False else "neexistuje/neběžel"))
print("TABULKA CHYB", "OK" if not chyby else chyby)
sys.exit(1 if chyby else 0)
