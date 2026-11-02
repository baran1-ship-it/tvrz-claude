"""Matice vztahů Puchartu (vrstva 6b z Havrana): každá dvojice druhů má test Puchartu, který existuje a prošel, nebo
důvod (nenastava/nezavisle). Díra = dvojice bez testu i důvodu; neexistující nebo neprošlý test = chyba.
Čte build/test_smyslu.json a build/pruchod.json. rc 1 = nevydávat (export_apk.sh).  python3 nastroje/kontrola_vztahu.py <koren>"""
import sys, json, itertools, os
K = sys.argv[1]; V = json.load(open(K + "/pravidla/svet/vztahy.json"))
TS = json.load(open(K + "/build/test_smyslu.json"))["testy"] if os.path.exists(K + "/build/test_smyslu.json") else {}
PR = json.load(open(K + "/build/pruchod.json")) if os.path.exists(K + "/build/pruchod.json") else {}
def stav(t):
    druh, jm = t.split(":", 1)
    if druh == "smysl": return None if jm not in TS else TS[jm]["ok"]
    if druh == "pruchod":
        if not PR: return None
        if jm == "vse": return all(v == "OK" for v in PR.values())
        return None if jm not in PR else PR[jm] == "OK"
    return None
diry, chyby, ok = [], [], 0
for a, b in itertools.combinations_with_replacement(V["druhy"], 2):
    k = "%s|%s" % (a, b); e = V["dvojice"].get(k, {})
    if e.get("nenastava_puchart") or e.get("nezavisle_puchart"): ok += 1; continue
    t = e.get("testy_puchart")
    if not t: diry.append(k); continue
    st = {x: stav(x) for x in t}
    if "--rychle" in sys.argv and all(v is None for x, v in st.items() if x.startswith("pruchod")) and all(v for x, v in st.items() if not x.startswith("pruchod")): ok += 1; continue   # rychlý běh: průchod se neověřuje
    if any(v is None for v in st.values()): chyby.append("%s: test neexistuje / neběžel %s" % (k, [x for x, v in st.items() if v is None]))
    elif not all(st.values()): chyby.append("%s: test neprošel %s" % (k, [x for x, v in st.items() if not v]))
    else: ok += 1
n = len(list(itertools.combinations_with_replacement(V["druhy"], 2)))
print("MATICE %d/%d dvojic pokryto, díry %d, chyby %d" % (ok, n, len(diry), len(chyby)))
for x in diry: print("  DIRA", x)
for x in chyby: print("  CHYBA", x)
json.dump({"pokryto": ok, "celkem": n, "diry": diry, "chyby": chyby}, open(K + "/build/matice.json", "w"), ensure_ascii=False, indent=1)
sys.exit(1 if (diry or chyby) else 0)
