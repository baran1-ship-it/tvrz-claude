"""Vyhodnocení hlídače scén (GPT bod 8–9): rozpočty podle typu scény, podezření na doskok, změna proti schválenému
stavu (pravidla/svet/sceny_schvaleno.json – zapíše --schvalit po schválení Míšou). rc 1 = nevydávat.
  python3 nastroje/kontrola_scen.py <koren> [--schvalit]"""
import sys, json, os
import numpy as np
K = sys.argv[1]; SP = json.load(open(K + "/pravidla/svet/sceny_pravidla.json"))
S = json.load(open(K + "/build/sceny.json"))["snimky"]
chyby, prehled = [], {}
for typ, rz in SP["rozpocty_typu"].items():
    if typ == "popis": continue
    b = [s for s in S if s["typ"] == typ]
    if not b: continue
    tr = np.array([s["troj"] for s in b]); kr = np.array([s["kresleni"] for s in b])
    prehled[typ] = {"snimku": len(b), "troj_p95": int(np.percentile(tr, 95)), "troj_max": int(tr.max()), "kresleni_p95": int(np.percentile(kr, 95)),
                    "kresleni_m_median": float(np.median([s["kresleni_m"] for s in b]))}
    nad = [s for s in b if s["troj"] > rz["troj_max"] or s["kresleni"] > rz["kresleni_max"]]
    if len(nad) > 0.05 * len(b): chyby.append("typ %s: %d/%d snímků nad rozpočtem (např. %s)" % (typ, len(nad), len(b), {k: nad[0][k] for k in ("x", "z", "troj", "kresleni")}))
z = np.array([s["zmena"] for s in S if s["zmena"] >= 0]); med = float(np.median(z)) if len(z) else 0
D = SP["doskok"]
skoky = [s for s in S if s["zmena"] >= 0 and s["zmena"] > max(D["nasobek_medianu"] * med, D["min_zmena"])]
prehled["zmena_median"] = med; prehled["doskoky"] = [{k: s[k] for k in ("x", "z", "typ", "zmena")} for s in skoky[:20]]
if skoky: chyby.append("podezření na doskok: %d míst (např. %s)" % (len(skoky), prehled["doskoky"][0]))
sch_p = K + "/pravidla/svet/sceny_schvaleno.json"
if "--schvalit" in sys.argv:
    json.dump({"popis": "schválený stav hlídače scén (nastroje/kontrola_scen.py --schvalit)", "prehled": prehled}, open(sch_p, "w"), ensure_ascii=False, indent=1)
elif os.path.exists(sch_p):
    sch = json.load(open(sch_p))["prehled"]
    for typ in ("A", "B", "C"):
        if typ in sch and typ in prehled and prehled[typ]["troj_p95"] > sch[typ]["troj_p95"] * 1.15:
            chyby.append("typ %s: troj p95 %d proti schváleným %d (+15 %% povoleno)" % (typ, prehled[typ]["troj_p95"], sch[typ]["troj_p95"]))
print("SCENY", json.dumps(prehled, ensure_ascii=False))
print("KONTROLA_SCEN", "OK" if not chyby else chyby)
json.dump({"prehled": prehled, "chyby": chyby}, open(K + "/build/kontrola_scen.json", "w"), ensure_ascii=False, indent=1)
sys.exit(1 if chyby else 0)
