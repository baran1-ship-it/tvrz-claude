"""Kameny v korytech (pravidla/svet/voda_hra.json kameny_koryta; Míša 10. 11.: „kamenný potok“): podél os toků
(hra/data/toky_hladina.json: osa [x, z, hladina], šířka) rozmístí valouny po dně, balvany vyčnívající nad hladinu a kamení
na březích; brody (hra/data/brody.json) a konce mostů (nastupy_udoli.json) nechá volné. Dno = hladina − hloubka·(1 − (2v/š)²)
jako nastroje/koryta.py. Výstup hra/data/koryto_kameny.json [tvar, x, y, z, otočení, měřítko] pro hlavni.gd _instance_seznam.
  python3 nastroje/koryto_kameny.py <koren>
"""
import sys, os, json, math
import numpy as np
K = sys.argv[1] if len(sys.argv) > 1 else "."
VH = json.load(open(os.path.join(K, "pravidla/svet/voda_hra.json"))); C = VH["kameny_koryta"]; HV = VH["koryto"]["hloubka_vody_m"]
TH = json.load(open(os.path.join(K, "hra/data/toky_hladina.json")))["toky"]
BR = json.load(open(os.path.join(K, "hra/data/brody.json")))["brody"]
NU = json.load(open(os.path.join(K, "hra/data/nastupy_udoli.json")))["nastupy"]
rg = np.random.default_rng(1393); out = []
VY = json.load(open(os.path.join(K, "hra/data/vysek.json"))); Hr = np.fromfile(os.path.join(K, "hra/data/vysek.r16"), "<u2").reshape(VY["vyska"], VY["sirka"])
Yt = Hr / 200.0 + 300.0 - VY["pocatek_H"]
def ter(x, z):   # skutečné dno koryta (kolize, vysek.r16 – stejně jako test_smyslu.ter)
    c = min(max(x - VY["x0_hra"], 0), VY["sirka"] - 1.001); r = min(max(z - VY["z0_hra"], 0), VY["vyska"] - 1.001)
    c0, r0 = int(c), int(r); fc, fr = c - c0, r - r0
    return (Yt[r0, c0] * (1 - fc) + Yt[r0, c0 + 1] * fc) * (1 - fr) + (Yt[r0 + 1, c0] * (1 - fc) + Yt[r0 + 1, c0 + 1] * fc) * fr
def volno(x, z):
    for b in BR:
        dx, dz = x - b["stred"][0], z - b["stred"][1]; s = b["smer"]
        podel = abs(dx * s[0] + dz * s[1]); napric = abs(-dx * s[1] + dz * s[0])
        if napric < C["brod_volno_m"] and podel < b.get("delka", 20) / 2: return False   # pruh cesty přes brod
    for n in NU:
        if math.hypot(x - n[0], z - n[1]) < C["most_volno_m"] + 1.5: return False
    return True
for k, t in TH.items():
    o = np.array(t["osa"], float); w = float(t["sirka"]); h0 = HV["zaklad"] + HV["na_m_sirky"] * w
    seg = np.diff(o[:, :2], axis=0); L = np.linalg.norm(seg, axis=1); s_ = np.concatenate([[0], np.cumsum(L)])
    for s in np.arange(0, s_[-1], C["krok_m"]):
        i = min(np.searchsorted(s_, s) - 1, len(L) - 1); i = max(i, 0); f = (s - s_[i]) / max(L[i], 1e-6)
        p = o[i] + (o[i + 1] - o[i]) * f; tg = seg[i] / max(L[i], 1e-6); nrm = np.array([-tg[1], tg[0]])
        def dej(v, tvar_m, typ):
            x, z = p[0] + nrm[0] * v, p[1] + nrm[1] * v
            if not volno(x, z): return
            yb = ter(x, z)   # pata na skutečném dně / břehu
            sc = rg.uniform(*tvar_m)
            if typ == "balvan":   # balvan: pata na dně, vrch nad hladinou
                vys = (p[2] + rg.uniform(*C["balvan_nad_hladinou"])) - yb
                sc = max(sc, vys / 0.6)
            if typ == "velky": yb -= sc * C["velky_zapusteni"] * 0.6
            out.append([int(rg.integers(0, 6)) + (6 if typ == "velky" else 0), round(float(x), 2), round(float(yb - sc * 0.15), 2), round(float(z), 2), round(float(rg.uniform(0, 6.283)), 2), round(float(sc), 2), round(float(rg.uniform(*C["plochost"])) if typ != "velky" else 0.8, 2)])
        a = C["krok_m"]
        for _ in range(rg.poisson(C["valouny_na_m2"] * w * a)): dej(rg.uniform(-w / 2, w / 2), C["valoun_m"], "valoun")
        if rg.random() < C["balvany_na_m"] * a: dej(rg.uniform(-w / 2 * 0.8, w / 2 * 0.8), C["balvan_m"], "balvan")
        if rg.random() < C.get("velke_balvany_na_m", 0) * a:   # velký balvan droby na břehu / zasahující do toku (fotky potok_01–02), mech nahoře
            sg_ = rg.choice([-1, 1]); dej(sg_ * (w / 2 + rg.uniform(*C["velky_od_kraje_m"])), C["velky_balvan_m"], "velky")
        for sg in (-1, 1):
            for _ in range(rg.poisson(C["breh_na_m2"] * C["breh_pas_m"] * a)): dej(sg * (w / 2 + rg.uniform(0, C["breh_pas_m"])), C["breh_kamen_m"], "breh")
            for _ in range(rg.poisson(C.get("okraj_na_m2", 0) * 2 * C.get("okraj_pas_m", 0.5) * a)):   # pás přes čáru vody a břehu
                dej(sg * (w / 2 + rg.uniform(-C["okraj_pas_m"], C["okraj_pas_m"])), C["okraj_m"], "okraj")
np.array(out, np.float32).tofile(os.path.join(K, "hra/data/koryto_kameny.bin"))   # 245 tis. kamenů: binárně (JSON 10 MB se na tabletu parsuje dlouho)
json.dump({"popis": "kameny v korytech (nastroje/koryto_kameny.py): koryto_kameny.bin = float32 [tvar 0–5 (6–11 velký balvan s mechem), x, y, z, otočení, měřítko, plochost]", "glb": "res://modely/hrady/kameny_koryta.glb",
           "dosah_m": C["dosah_m"], "velky_dosah_m": C["velky_dosah_m"], "bunka_m": C["bunka_m"], "pocet": len(out)}, open(os.path.join(K, "hra/data/koryto_kameny.json"), "w"))
print("kamenů v korytech", len(out))
