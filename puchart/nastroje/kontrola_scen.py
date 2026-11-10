"""Vyhodnocení hlídače scén (GPT bod 8–9): rozpočty podle typu scény, podezření na doskok, změna proti schválenému
stavu (pravidla/svet/sceny_schvaleno.json – zapíše --schvalit po schválení Míšou). rc 1 = nevydávat.
  python3 nastroje/kontrola_scen.py <koren> [--schvalit]"""
import sys, json, os
import numpy as np
K = sys.argv[1]; SP = json.load(open(K + "/pravidla/svet/sceny_pravidla.json"))
S0 = json.load(open(K + "/build/sceny.json"))["snimky"]
# kamera ve zdi = artefakt trasy hlídače (spojnice bodů přes stavbu), ne scéna: obrysy zdí (stavby_clony.json) –
# paprsek ve hře zevnitř tlusté zdi nic nezasáhne (2. 11.)
from matplotlib.path import Path
_cl = [Path(q["rohy"]) for q in json.load(open(K + "/hra/data/stavby_clony.json"))["kvadry"]]
for s_ in S0:
    if not s_.get("ve_zdi"): s_["ve_zdi"] = any(p_.contains_point((s_["x"], s_["z"])) for p_ in _cl)
S = []
for i, s_ in enumerate(S0):
    if s_["ve_zdi"]: continue
    if i > 0 and S0[i - 1]["ve_zdi"]: s_ = dict(s_, zmena=-1)   # první snímek po zdi se neporovnává
    S.append(s_)
chyby, prehled = [], {}
for typ, rz in SP["rozpocty_typu"].items():
    if typ == "popis": continue
    b = [s for s in S if s["typ"] == typ]
    if not b: continue
    tr = np.array([s["troj"] for s in b]); kr = np.array([s["kresleni"] for s in b])
    prehled[typ] = {"snimku": len(b), "troj_p95": int(np.percentile(tr, 95)), "troj_max": int(tr.max()), "kresleni_p95": int(np.percentile(kr, 95)),
                    "kresleni_m_median": float(np.median([s["kresleni_m"] for s in b]))}
    nad = [s for s in b if s["troj"] > rz["troj_max"] or s["kresleni"] > rz["kresleni_max"]]
    import datetime as _dt   # výjimky schválené Míšou (bod, důvod, do kdy) – po datu „do“ neplatí
    _vy = [v for v in rz.get("vyjimky", []) if v.get("do", "9999") >= _dt.date.today().isoformat()]
    nad = [s for s in nad if not any(abs(s["x"] - v["bod"][0]) < 3 and abs(s["z"] - v["bod"][1]) < 3 for v in _vy)]
    if len(nad) > 0.05 * len(b): chyby.append("typ %s: %d/%d snímků nad rozpočtem (např. %s)" % (typ, len(nad), len(b), {k: nad[0][k] for k in ("x", "z", "troj", "kresleni")}))
z = np.array([s["zmena"] for s in S]); med = float(np.median(z[z >= 0])) if (z >= 0).any() else 0
D = SP["doskok"]; skoky = []
for i, s_ in enumerate(S):
    if s_["zmena"] < 0: continue
    if i > 0 and "y" in s_ and "y" in S[i - 1] and abs(s_["y"] - S[i - 1]["y"]) > D.get("max_dy_m", 1e9): continue   # kamera sjela/vyjela o metry (průrva pod mostem B, 10. 11.) – skutečná změna pohledu, ne doskok
    okoli = [S[j]["zmena"] for j in range(max(0, i - D["okno"]), min(len(S), i + D["okno"] + 1)) if j != i and S[j]["zmena"] >= 0]
    if okoli and s_["zmena"] > max(D["nasobek"] * float(np.median(okoli)), D["min_zmena"]): skoky.append(s_)
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
prehled["ve_zdi"] = len(S0) - len(S)
if prehled["ve_zdi"] > 0.1 * len(S0): chyby.append("kamera ve zdi u %d/%d bodů – trasy hlídače vedou stavbami" % (prehled["ve_zdi"], len(S0)))
print("SCENY", json.dumps(prehled, ensure_ascii=False))
print("KONTROLA_SCEN", "OK" if not chyby else chyby)
json.dump({"prehled": prehled, "chyby": chyby}, open(K + "/build/kontrola_scen.json", "w"), ensure_ascii=False, indent=1)
sys.exit(1 if chyby else 0)
