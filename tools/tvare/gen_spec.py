"""Návrh tváří pro všechny npc_* z postavy.json: věk, role, posuvníky (každý jiný), pleť, účes, vousy, barvy."""
import json, numpy as np, sys
sys.path.insert(0, "/home/claude/tv/scripts"); import face2
P = json.load(open("/tmp/postavy.json"))
ROLE = {"npc_sedlak": "sedlák", "npc_kovar": "kovář", "npc_mestan": "měšťan", "npc_stary": "stařec", "npc_mladik": "mladík",
        "npc_selka": "selka", "npc_babka": "bába", "npc_divka": "dívka", "npc_mestka": "měšťka", "npc_rychtar": "rychtář",
        "npc_havel": "sedlák Havel", "npc_mikulas": "stařec Mikuláš", "npc_jakub": "chalupník Jakub", "npc_petr": "sedlák Petr",
        "npc_vavra": "pacholek Vávra", "npc_stepan": "mlynář Štěpán", "npc_matej": "chalupník Matěj", "npc_bartos": "sedlák Bartoš",
        "npc_linhart": "Linhart", "npc_hostinsky": "hostinský", "npc_straz": "stráž", "npc_pastyr": "pastýř", "npc_ponocny": "ponocný",
        "npc_hoch": "hoch", "npc_marketa": "selka Markéta", "npc_dorota": "kuchařka Dorota", "npc_anezka": "bába Anežka",
        "npc_katerina": "Kateřina", "npc_hostinska": "šenkýřka", "npc_pasacka": "pasačka", "npc_bilek": "stařec Bílek",
        "npc_martin": "Martin", "npc_bara": "Bára", "npc_eliska": "Eliška"}
DETI = {"npc_hoch": 12, "npc_pasacka": 13, "npc_divka": 16, "npc_katerina": 18, "npc_mladik": 18, "npc_eliska": 20}
rng = np.random.default_rng(1393)
S = face2.SLIDERS
OCI = [[0.30, 0.42, 0.55], [0.40, 0.45, 0.48], [0.35, 0.48, 0.30], [0.50, 0.45, 0.25], [0.55, 0.38, 0.20], [0.35, 0.24, 0.14], [0.45, 0.50, 0.55]]
VLASY = [[0.10, 0.07, 0.05], [0.18, 0.11, 0.06], [0.28, 0.18, 0.09], [0.45, 0.32, 0.18], [0.06, 0.045, 0.035], [0.38, 0.17, 0.07], [0.55, 0.42, 0.25]]
chosen = {"Male": [], "Female": []}
out = {}
for k, v in P.items():
    if not k.startswith("npc_"): continue
    sex = v["sex"]; tv = v.get("tvar") or {}
    vek01 = tv.get("vek", 0.0); vek = DETI.get(k, int(round((24 + vek01 * 46 + rng.uniform(-2, 4)) if vek01 else rng.uniform(21, 38))))
    vek = {'npc_kovar': 38, 'npc_straz': 31}.get(k, vek)
    dite = vek < 17
    # nejvzdálenější kandidát
    best, bd = None, -1
    for _ in range(60):
        c = rng.uniform(-1, 1, len(S)) * 0.85
        d = min([np.linalg.norm(c - o) for o in chosen[sex]] or [9])
        if d > bd: best, bd = c, d
    chosen[sex].append(best)
    s = dict(zip(S, [round(float(x), 2) for x in best]))
    ag = min(1.0, max(0.0, (vek - 30) / 40))
    s["vek_pokles"] = round(ag * 0.9 + rng.uniform(0, 0.15), 2)
    if sex == "Female":
        s["vaha"] = round(float(rng.uniform(-0.6, 0.6)), 2); s["tvare_plnost"] = round(float(rng.uniform(-0.8, 0.9)), 2)
        for kk in ("celist", "nadocnice", "brada_sirka", "lebka_sirka"): s[kk] = round(min(s[kk], 0.25) - 0.25, 2)
        s["nos_hrbet"] = round(min(s["nos_hrbet"], 0.3), 2)
    if dite:
        s.update(oci=0.7, nos_delka=-0.6, nos_hrbet=-0.5, celist=-0.8, brada_delka=-0.6, obliceji_delka=-0.9, tvare_plnost=0.5, nadocnice=-0.6, vek_pokles=0, vaha=0.0)
    role = ROLE.get(k, k[4:])
    if "kovář" in role: s.update(celist=0.9, nadocnice=0.8, nos_sirka=0.7, vaha=0.2)
    if role in ("hostinský", "rychtář", "šenkýřka") or "kuchařka" in role: s["vaha"] = 0.75
    if "ponocný" in role or "stařec" in role: s.update(vaha=-0.5, nos_hacek=0.7, nos_delka=0.6)
    if "stráž" in role: s.update(celist=0.7, brada_vpred=0.6)
    # pleť
    ton = [round(float(x), 3) for x in (np.array([1.0, 0.96, 0.93]) * rng.uniform(0.9, 1.1) + rng.uniform(-0.035, 0.035, 3))]
    plet = dict(ton=ton, opaleni=tv.get("opaleni", 0.0), vek=round(max(vek01, ag * 0.8), 2), kruhy=tv.get("kruhy", 0.0),
                rumenec=tv.get("rumenec", 0.0) + (0.25 if dite else 0), pihy=round(float(rng.choice([0, 0, 0, 0.6, 1.0])), 1), odlicit=1.0)
    # vlasy
    hcol = v.get("hair_col"); hcol = [round(c ** (1 / 2.2), 3) for c in hcol] if hcol else VLASY[rng.integers(len(VLASY))]
    if sex == "Female": hcol = VLASY[[1, 2, 3, 5, 0, 6, 4][len(chosen[sex]) % 7]]
    grey = v.get("grey") or 0.0
    hs = v.get("hair", [])
    vl = dict(barva=hcol, sedive=round(min(1, grey * 1.1), 2), linie={}, cepice=0.005, objem=0.003, chomacu=6, delka_chomacu=0.12, sirka_chomacu=0.035)
    vous = None
    if sex == "Male":
        if "Hair_Long" in hs:
            vl.update(smer="temeno", doplnek="dlouhe", dlouhe_delka=0.20, objem=0.006, chomacu=7)
        elif "Hair_SimpleParted" in hs:
            if rng.random() < 0.5: vl.update(smer="pesinka", chomacu=8, delka_chomacu=0.12)
            else: vl.update(smer="temeno", linie={"predni": 0.040, "spanky": 0.030, "nad_usima": 0.012, "za_usima": -0.03, "tyl": -0.06}, objem=0.008, chomacu=7, delka_chomacu=0.10)   # mísa
        else:
            vl.update(smer="pesinka", cepice=0.004, objem=0.001, chomacu=5, delka_chomacu=0.09)
        if vek > 45 and rng.random() < 0.6:
            vl["linie"] = dict(vl["linie"], predni=0.075 + rng.uniform(0, 0.01), kouty=0.012)
        if vek > 60 and rng.random() < 0.6:
            vl["linie"] = dict(vl["linie"], plesh=0.045 + rng.uniform(0, 0.02)); vl["chomacu"] = 3
        if "Hair_Beard" in hs:
            typ = str(rng.choice(["plny", "kratky", "plny", "bradka", "knir"]))
            vous = dict(typ=typ, tloustka=0.003 + rng.uniform(0, 0.002), delka=float({"plny": rng.uniform(0.012, 0.03), "kratky": 0.004, "bradka": 0.012, "knir": 0.002}[typ]))
            if typ in ("knir", "bradka"): plet["strniste"] = 0.35
        else:
            plet["strniste"] = 0.0 if dite or vek < 18 else round(float(rng.uniform(0.2, 0.5)), 2)
            vous = {"typ": "strniste"} if plet["strniste"] else None
    else:
        if "Hair_Long" in hs:
            if k in ("npc_katerina",): vl.update(smer="pesinka", doplnek="dlouhe", dlouhe_delka=0.26, chomacu=8)
            else: vl.update(smer="pesinka", doplnek="cop", cop_delka=0.38 if not dite else 0.3, chomacu=8)
        else:
            vl.update(smer="pesinka", doplnek="drdol", chomacu=7, drdol_z=float(rng.uniform(-0.02, 0.03)))
    ob = [round(float(rng.uniform(0.75, 1.25) * (0.8 if sex == "Female" else 1.0)), 2), round(float(rng.uniform(-0.002, 0.003)), 4), round(float(rng.uniform(-0.08, 0.06)), 3)]
    out[k] = dict(pohlavi=sex, vek_let=vek, role=role, seed=int(rng.integers(1e6)), tvar=s, plet=plet, vlasy=vl, vousy=vous,
                  oboci=ob, oci=OCI[rng.integers(len(OCI))])
json.dump(out, open("/home/claude/tv/scripts/tvare_spec.json", "w"), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, v["role"], v["pohlavi"][0], v["vek_let"], v["vlasy"].get("doplnek") or v["vlasy"].get("smer"), (v["vousy"] or {}).get("typ"))
