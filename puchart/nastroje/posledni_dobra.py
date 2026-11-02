"""Poslední dobrá verze (hlídač regresí): když hlídači projdou, výsledky (test smyslu, průchod, scény, matice) se uloží
do pravidla/dobra_verze.json s commitem. Když neprojdou, vypíše se, co bylo v dobré verzi OK a teď není, a commit dobré
verze – odtud `git diff <commit> -- <dotčené soubory>` k izolaci příčiny.  python3 nastroje/posledni_dobra.py <koren> <rc>"""
import sys, json, os, subprocess
K, rc = sys.argv[1], int(sys.argv[2]); B = K + "/build/"
def nacti(f):
    try: return json.load(open(B + f))
    except Exception: return None
ted = {"smysl": {k: v["ok"] for k, v in (nacti("test_smyslu.json") or {}).get("testy", {}).items()},
       "pruchod": {k: v == "OK" for k, v in (nacti("pruchod.json") or {}).items()},
       "sceny": (nacti("kontrola_scen.json") or {}).get("prehled", {}), "matice": (nacti("matice.json") or {}).get("pokryto")}
p = K + "/pravidla/dobra_verze.json"
commit = subprocess.run(["git", "-C", K, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
if rc == 0:
    json.dump({"popis": "výsledky hlídačů poslední dobré verze (nastroje/posledni_dobra.py)", "commit": commit, "vysledky": ted}, open(p, "w"), ensure_ascii=False, indent=1)
    print("DOBRA_VERZE uložena (%s)" % commit)
elif os.path.exists(p):
    d = json.load(open(p)); h = []
    for druh in ("smysl", "pruchod"):
        for k, ok in d["vysledky"].get(druh, {}).items():
            if ok and not ted[druh].get(k, False): h.append("%s:%s" % (druh, k))
    print("REGRESE proti dobré verzi %s: %s" % (d["commit"], h or "(nové selhání bez předchozího výsledku)"))
    print("  k izolaci: git diff %s -- puchart/" % d["commit"])
