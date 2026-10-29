"""Ves B (lokace.json ves.dvorec, dvorec_zaznam): uprav blender/vesnice.py, nove.py, veg.py, export_game.py,
impostory.py a scripts/svet.gd. Spoustet az po exportu 0995c (export tyto soubory cte)."""
import re
import sys

R = "/home/user/tvrz-claude/"


def nahrad(cesta, stare, nove, n=1):
    s = open(R + cesta).read()
    if s.count(stare) != n:
        sys.exit("NENALEZENO %s (%d x): %s" % (cesta, s.count(stare), stare[:80]))
    open(R + cesta, "w").write(s.replace(stare, nove))


# ---------------------------------------------------------------- vesnice.py
nahrad("blender/vesnice.py", '''    _LAYOUT = out
    return out
''', '''    _dvorce(out)
    _LAYOUT = out
    return out


def _dvorce(out):
    """Ves B (lokace.json ves.dvorec, Misa/Astra 29. 10.): za dvorem napric stodola (misto maleho chleva) a na stejne care
    kulna az k boku dvora; zaznam dvorec_zaznam.zrcadlo prohodi strany (stodola od praveho boku). Rozmery z ves.dvorec
    (= modely katalogu stodola, kolna). Stodola a kulna jsou predmety katalogu (VYBAVENI) ve starem ramci - presunou se
    s usedlosti (svet.gd _vo_data) i s plackou terenu pod nimi (_pads)."""
    ves = _lokace_ves()
    dv = ves.get("dvorec")
    if not dv:
        return
    zrc = ves.get("dvorec_zaznam", {}).get("zrcadlo", {})
    sd, kl = dv["stodola"], dv["kolna"]
    for k, h in enumerate(out):
        F = Frame((h["p"].x, h["p"].z), h["yaw"], 0.0)
        L, W = h["L"], h["W"]
        vL, vR = -W / 2 - 6.2, W / 2 + 9.5
        ub = -L / 2 - sd["za_domem_m"] - sd["hloubka_m"] / 2
        v0 = vL + sd["od_boku_m"]
        v1 = v0 + sd["delka_m"] + kl["mezera_m"]
        v2 = min(vR - 0.5, v1 + kl["delka_m"])
        vs, vk = v0 + sd["delka_m"] / 2, (v1 + v2) / 2
        if zrc.get(str(_usedlost_k(h)), False):
            vs, vk = vL + vR - vs, vL + vR - vk
        uk = ub + sd["hloubka_m"] / 2 - kl["hloubka_m"] / 2
        h["barn"] = (F.c + F.au * ub + F.av * vs, h["yaw"] + math.pi / 2, sd["delka_m"], sd["hloubka_m"])
        h["kolna"] = (F.c + F.au * uk + F.av * vk, h["yaw"] + math.pi / 2, v2 - v1, kl["hloubka_m"])
        h["dvorec"] = (sd["model"], kl["model"], vs > (vL + vR) / 2)


def _lokace_ves():
    import json
    import os
    return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pravidla", "svet", "lokace.json")))["ves"]


def _usedlost_k(h):
    """Cislo usedlosti v lokace.json ves.usedlosti (stary_stred = stred chalupy v layoutu)."""
    for e in _lokace_ves().get("usedlosti", []):
        if math.hypot(e["stary_stred"][0] - h["p"].x, e["stary_stred"][1] - h["p"].z) < 0.5:
            return e["k"]
    return -1
''')
# placka terenu i pod kulnou
nahrad("blender/vesnice.py", '''        for (p, yaw, L, W) in ((h["p"], h["yaw"], h["L"], h["W"]), h["barn"]):
            F = Frame((p.x, p.z), yaw, 0.0)''', '''        for (p, yaw, L, W) in ((h["p"], h["yaw"], h["L"], h["W"]), h["barn"]) + ((h["kolna"],) if "kolna" in h else ()):
            F = Frame((p.x, p.z), yaw, 0.0)''')
# stavba: maly chlev jen bez dvorce, jinak stodola a kulna z katalogu (celem do dvora = k domu)
nahrad("blender/vesnice.py", '''        bp, byaw, bL, bW = h["barn"]
        barn(P, (bp.x, bp.z), byaw, bL, bW, h["barn_roof"], ypad=pad_y(bp, byaw, bL, bW))''', '''        bp, byaw, bL, bW = h["barn"]
        if "dvorec" in h:
            yw = _yaw_along(-F.av)                       # model: celo (vrata, otevrena strana kulny) na +z = k domu (+au)
            for (q, qyaw, qL, qW), mid in ((h["barn"], h["dvorec"][0]), (h["kolna"], h["dvorec"][1])):
                VYBAVENI.append({"id": mid, "p": [round(q.x, 3), round(pad_y(q, qyaw, qL, qW), 3), round(q.z, 3)], "yaw": round(yw, 4),
                                 "dvorec": True})
        else:
            barn(P, (bp.x, bp.z), byaw, bL, bW, h["barn_roof"], ypad=pad_y(bp, byaw, bL, bW))''')
# zelen a dvur podle skutecne polohy stodoly (ne pevne L/2 + 6,5)
nahrad("blender/vesnice.py", '''    # sad a louka za chlevem az k zadnimu plotu: vysoka trava, kopřivy, kvety
    for _ in range(90):
        q = F.c + F.au * Rt.uniform(back + 0.6, -(L / 2 + 6.5) - barn[3] / 2 - 0.4) + F.av * Rt.uniform(vL + 0.6, vR - 0.6)''', '''    # sad a louka za chlevem az k zadnimu plotu: vysoka trava, kopřivy, kvety
    bu = (barn[0] - F.c).dot(F.au)                      # stred chleva / stodoly na ose u
    for _ in range(90):
        q = F.c + F.au * Rt.uniform(back + 0.6, max(back + 0.7, bu - barn[3] / 2 - 0.4)) + F.av * Rt.uniform(vL + 0.6, vR - 0.6)''')
nahrad("blender/vesnice.py", '''    for cu, cv in ((-(L / 2 + 6.5) + barn[3] / 2 + 0.6, vR - 0.6), (L / 2 - 0.6, vR - 0.7), (-(L / 2 + 6.5) + barn[3] / 2 + 0.6, W / 2 + 0.7)):''',
       '''    for cu, cv in ((bu + barn[3] / 2 + 0.6, vR - 0.6), (L / 2 - 0.6, vR - 0.7), (bu + barn[3] / 2 + 0.6, W / 2 + 0.7)):''')
nahrad("blender/vesnice.py", '''            _YARDS.append((F.c, F.au, F.av, h["L"], h["W"], -(h["L"] / 2 + 6.5) + bW / 2))''',
       '''            _YARDS.append((F.c, F.au, F.av, h["L"], h["W"], (h["barn"][0] - F.c).dot(F.au) + bW / 2))''')
# stromy u staveni (ve starem ramci uvnitr pudorysu usedlosti - presunou se s ni): pro veg pred nove.rozmistit
nahrad("blender/vesnice.py", '''def village_trees():''', '''def dvorec_stromy():
    """Zelen u staveni (lokace.json ves.dvorec.zelen, tradicni schema): strom u vjezdu, na dvore, u stodoly v humne -
    (model stromu v2, x, z, vyska) ve starem ramci usedlosti. Predzahradka (kvetiny) zatim ne."""
    dv = _lokace_ves().get("dvorec", {})
    out = []
    for h in layout():
        if "dvorec" not in h:
            continue
        F = Frame((h["p"].x, h["p"].z), h["yaw"], 0.0)
        L, W = h["L"], h["W"]
        vL, vR = -W / 2 - 6.2, W / 2 + 9.5
        bu = (h["barn"][0] - F.c).dot(F.au)
        for zn, z_ in dv.get("zelen", {}).items():
            if not isinstance(z_, dict) or "strom" not in z_:
                continue
            uu = {"predek": L / 2, "stodola": bu - h["barn"][3] / 2, "dum": 0.0}[z_["u"][0]] + z_["u"][1]
            vv = {"vR": vR, "vL": vL, "dum": W / 2}[z_["v"][0]] + z_["v"][1]
            if zn == "u_stodoly" and h["dvorec"][2]:
                vv = vL + vR - vv
            q = F.c + F.au * uu + F.av * vv
            out.append((z_["strom"], q.x, q.z, z_["vyska_m"]))
    return out


def village_trees():''')

# ---------------------------------------------------------------- nove.py: jablon (stromy v3 z blender/strom2.py)
nahrad("blender/nove.py", '''    "olse_mlada": (4.19, 7.69, 4.15), "vrba_hlavata_1": (6.05, 6.60, 6.40), "vrba_hlavata_2": (9.21, 7.65, 9.43),
}''', '''    "olse_mlada": (4.19, 7.69, 4.15), "vrba_hlavata_1": (6.05, 6.60, 6.40), "vrba_hlavata_2": (9.21, 7.65, 9.43),
    # jablon v3 (blender/strom2.py, modely/nove/jablon.glb - sady vsi, lokace.json ves.dvorec)
    "jablon": (5.82, 6.11, 6.13),
}''')
nahrad("blender/nove.py", '''MISTA = []      # (model, x, y, z, meritko, yaw ve hre) - doplni kraj/vesnice, rozmisti veg''',
       '''MISTA = []      # (model, x, y, z, meritko, yaw ve hre) - doplni kraj/vesnice, rozmisti veg
NOVY_RAMEC = set()   # (x, z) po 0,1 m: instance v ramci nove vsi (zahumenky) - export je zapise do rostliny_ves_novy


def zaznam(pid, x, y, z, vyska, novy_ramec=False, sink=0.1):
    """Strom nebo ker ze zaznamu (lokace.json ves.dvorec_zaznam): stanoviste dava zaznam (sad, zivy plot), jen ne ve
    vode. novy_ramec = souradnice nove vsi (hra je neposouva s usedlostmi)."""
    import kraj
    if kraj.rostlina_ve_vode(pid, x, z, y):
        return
    MISTA.append((pid, x, y - sink, z, vyska / DIM[pid][1], R_.uniform(0, 2 * math.pi)))
    if novy_ramec:
        NOVY_RAMEC.add((round(x, 1), round(z, 1)))''')

# ---------------------------------------------------------------- veg.py: pred nove.rozmistit
nahrad("blender/veg.py", '''        nove.rozmistit(V, place, LIB)''', '''        # ves B (lokace.json ves.dvorec): stromy u staveni ve starem ramci, zahumenky, zivy plot a lipa na navsi v novem
        import vesnice
        for pid, x, z, h in vesnice.dvorec_stromy():
            nove.zaznam(pid, x, F.land(x, z), z, h)
        zz = vesnice._lokace_ves().get("dvorec_zaznam", {})
        for pid, x, z, h in zz.get("zahumenky", []) + zz.get("zivy_plot", []) + ([zz["lipa_navsi"]] if zz.get("lipa_navsi") else []):
            if pid in nove.DIM:
                nove.zaznam(pid, x, F.land(x, z), z, h, novy_ramec=True)
            else:
                put(pid, (x, F.land(x, z), z), h)        # ker z knihovny (sipek) - jen mimo stare usedlosti
        nove.rozmistit(V, place, LIB)''')

# ---------------------------------------------------------------- export_game.py: oddil rostliny_ves_novy
nahrad("blender/export_game.py", '''        mg = C @ mw @ CI
        key = "%s_%d" % hit
        inst.setdefault(key, []).append([round(v, 4) for row in mg[:3] for v in row])''', '''        mg = C @ mw @ CI
        key = "%s_%d" % hit
        # instance v ramci nove vsi (nove.NOVY_RAMEC: zahumenky, lipa na navsi) zvlast - hra je pripoji az po presunu vsi
        cil = inst_novy if (round(mg[0][3], 1), round(mg[2][3], 1)) in nove.NOVY_RAMEC else inst
        cil.setdefault(key, []).append([round(v, 4) for row in mg[:3] for v in row])''')
nahrad("blender/export_game.py", '''    inst = {}
    lookup =''', '''    inst = {}
    inst_novy = {}
    import nove
    lookup =''')
nahrad("blender/export_game.py", '''        "rostliny": inst,''', '''        "rostliny": inst,
        "rostliny_ves_novy": inst_novy,''')

# ---------------------------------------------------------------- impostory.py
s = open(R + "blender/impostory.py").read()
if '"jablon"' not in s:
    nahrad("blender/impostory.py", '''    "lipa_stredni": ("lipa_stredni", "lipa_stredni_0"),''', '''    "lipa_stredni": ("lipa_stredni", "lipa_stredni_0"), "jablon": ("jablon", "jablon_0"),''')
# ---------------------------------------------------------------- svet.gd: pripojit rostliny nove vsi
nahrad("scripts/svet.gd", '''	_plants(parent, quality)
	_krok_cas("_plants")''', '''	_ves_rostliny_novy()
	_plants(parent, quality)
	_krok_cas("_plants")''')
nahrad("scripts/svet.gd", '''func _plants(parent: Node3D, quality: int) -> void:''', '''## Ves B (lokace.json ves.dvorec_zaznam): stromy a kere v ramci nove vsi (zahumenky, zivy plot, lipa na navsi) - export
## je dava zvlast (svet.json rostliny_ves_novy), _vo_data je tedy neposouva s usedlostmi; pata z hotoveho terenu.
func _ves_rostliny_novy() -> void:
	var rn: Dictionary = data.get("rostliny_ves_novy", {})
	var n := 0
	for key: String in rn:
		if not (data["rostliny"] as Dictionary).has(key):
			data["rostliny"][key] = []
		for t: Array in rn[key]:
			var t2 := t.duplicate()
			t2[7] = _vyska(float(t[3]), float(t[11])) - float(Pravidla.cti("lokace", "ves", "dvorec", "zapusteni_m"))
			(data["rostliny"][key] as Array).append(t2)
			n += 1
	print("ves: %d rostlin v ramci nove vsi" % n)


func _plants(parent: Node3D, quality: int) -> void:''')
print("PATCH OK")

# ---------------------------------------------------------------- test smyslu: ves B
nahrad("tools/test_smyslu.py", '''# dil mlyna: hrana dilu (teren dilu na obvodu)''', '''# ves B (lokace.json ves.dvorec_zaznam, tools/ves_dvorce.py --zapis): stodoly a kulny ne ve vode, na ceste a na svahu;
# stromy a kere zahumenku a ziveho plotu ne ve vode a na ceste (Astra 29. 10.: kazda zmena projde pravidly)
_dz = lok["ves"].get("dvorec_zaznam", {})
for nm_, k_, x, z, r in _dz.get("stavby", []):
    sid = "ves_%s_%d" % (nm_, k_)
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

# dil mlyna: hrana dilu (teren dilu na obvodu)''')
print("PATCH TEST OK")
