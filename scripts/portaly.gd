extends RefCounted
const Pravidla := preload("res://scripts/pravidla.gd")
## Portaly mistnosti (okna a dvere) pro predmety.gd (_interier): {mistnost: {"portaly": [[x, y, z, nx, ny, nz, sirka, vyska, soused]],
## "budova", "sousedi", "cela"}}. Soused "" = otvor ven. Hostinec z modely/portaly.json (tools/portaly.py), tvrz z rozmeru
## v blender/palace.py, fort.py a hospodar.py (svet = souradnice modelu, vez posunuta o TX = -8); chalupy ne (radce 18:15:
## bez interieru s predmety). Bod portalu lezi na vnitrnim lici zdi, aby ve dverich predmety neblikly.


static func nacti(_rooms: Array) -> Dictionary:
	var out := {}
	if FileAccess.file_exists("res://modely/portaly.json"):
		var j: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://modely/portaly.json"))
		if j is Dictionary:
			for nm: String in j:
				out[nm] = {"portaly": j[nm]["portaly"], "budova": "hostinec", "cela": true}
	_tvrz(out)
	# sousedi pres vnitrni dvere (hostinec ma v datech jmena bez predpony)
	for nm: String in out:
		var d: Dictionary = out[nm]
		var s: Array = d.get("sousedi", [])
		for p: Array in d["portaly"]:
			var so := String(p[8])
			if so == "":
				continue
			if not out.has(so):
				so = String(d["budova"]) + "_" + so
			if out.has(so) and not s.has(so):
				s.append(so)
		d["sousedi"] = s
	return out


static func _add(out: Dictionary, nm: String, budova: String, p: Vector3, n: Vector3, w: float, h: float, soused := "") -> void:
	if not out.has(nm):
		out[nm] = {"portaly": [], "budova": budova, "sousedi": []}
	(out[nm]["portaly"] as Array).append([p.x, p.y, p.z, n.x, n.y, n.z, w, h, soused])


static func _tvrz(out: Dictionary) -> void:
	const ZS := -7.6        # vnitrni lic dvorniho pruceli palace (ZS - T)
	const ZN := -14.0       # vnitrni lic severni hradby
	const F1 := 3.9
	var J := Vector3(0, 0, 1)
	var S := Vector3(0, 0, -1)
	var V := Vector3(1, 0, 0)
	var Z := Vector3(-1, 0, 0)
	var b := "palac"
	# dvorni pruceli: DOOR_HALL, DOOR_PANTRY, WIN_GROUND, DOOR_UP, WIN_UP
	_add(out, "sin", b, Vector3(8.0, 1.475, ZS), J, 1.8, 2.95)
	for x: float in [5.0, 11.5, 14.5]:
		_add(out, "sin", b, Vector3(x, 1.95, ZS), J, 1.0, 1.3)
	_add(out, "kuchyne", b, Vector3(-0.05, 1.075, ZS), J, 1.1, 2.15)
	_add(out, "komnata", b, Vector3(1.05, (F1 + 5.95) * 0.5, ZS), J, 1.1, 5.95 - F1)
	_add(out, "komnata", b, Vector3(4.5, 5.55, ZS), J, 1.0, 1.3)
	_add(out, "loznice", b, Vector3(10.95, (F1 + 5.95) * 0.5, ZS), J, 1.1, 5.95 - F1)
	_add(out, "loznice", b, Vector3(14.0, 5.55, ZS), J, 1.0, 1.3)
	# severni hradba (NORTH_WIN), vychodni stit, zapadni stit
	for x2: float in [6.0, 10.0, 14.0]:
		_add(out, "sin", b, Vector3(x2, 2.5, ZN), S, 0.6, 1.2)
	_add(out, "komnata", b, Vector3(2.0, 5.55, ZN), S, 0.8, 1.3)
	_add(out, "loznice", b, Vector3(12.0, 5.55, ZN), S, 0.8, 1.3)
	_add(out, "loznice", b, Vector3(17.0, 5.6, -8.95), V, 0.9, 1.4)
	_add(out, "kuchyne", b, Vector3(-2.4, 2.0, -10.9), Z, 0.8, 1.0)
	_add(out, "komnata", b, Vector3(-2.4, 5.5, -11.1), Z, 1.0, 1.2)
	# vnitrni dvere v prickach
	# kuchyne (byvala spiz, Misa 6. 11.) - do sine pohyblive dvere (blender/palace.py, lokace.json kuchyne_tvrz)
	_add(out, "kuchyne", b, Vector3(3.0, 1.05, -10.6), V, 1.2, 2.1, "sin")
	_add(out, "sin", b, Vector3(3.0, 1.05, -10.6), Z, 1.2, 2.1, "kuchyne")
	_add(out, "komnata", b, Vector3(7.0, 4.925, -9.1), V, 1.2, 2.05, "loznice")
	_add(out, "loznice", b, Vector3(7.0, 4.925, -9.1), Z, 1.2, 2.05, "komnata")
	# vez (fort.tower posunuta o -8 v X): vnitrni lice x -26.3 / -21.3, z -15.3 / -10.3
	b = "vez"
	_add(out, "vez0", b, Vector3(-23.0, 2.75, -10.3), J, 0.2, 1.1)
	_add(out, "vez0", b, Vector3(-21.3, 1.05, -12.8), V, 1.2, 2.1)
	_add(out, "vez0", b, Vector3(-26.3, 2.0, -12.8), Z, 0.3, 1.2)
	_add(out, "vez1", b, Vector3(-25.3, 7.55, -10.3), J, 1.2, 2.1)
	_add(out, "vez1", b, Vector3(-23.0, 10.25, -10.3), J, 0.2, 1.3)
	_add(out, "vez1", b, Vector3(-23.8, 8.65, -15.3), S, 0.3, 1.3)
	_add(out, "vez1", b, Vector3(-21.3, 7.55, -14.3), V, 1.2, 2.1)
	_add(out, "vez1", b, Vector3(-26.3, 8.65, -12.8), Z, 0.3, 1.3)
	# vyhlidka: hrazdene patro, tri okna na kazde strane (lice -28.2 / -19.4, -17.2 / -8.4)
	for k in 3:
		var s := 1.425 + 2.8 * k
		_add(out, "vez2", b, Vector3(-28.2 + s, 14.7, -8.62), J, 0.95, 1.2)
		_add(out, "vez2", b, Vector3(-28.2 + s, 14.7, -16.98), S, 0.95, 1.2)
		_add(out, "vez2", b, Vector3(-19.62, 14.7, -17.2 + s), V, 0.95, 1.2)
		_add(out, "vez2", b, Vector3(-27.98, 14.7, -17.2 + s), Z, 0.95, 1.2)
	out["vez0"]["sousedi"] = ["vez1"]            # otvory nad schody
	out["vez1"]["sousedi"] = ["vez0", "vez2"]
	out["vez2"]["sousedi"] = ["vez1"]
	# strazni komora nad branou (fort.stone_storey): okna na jih a sever, vstupy z ochozu
	b = "brana"
	for x3: float in [-1.9, 1.9]:
		_add(out, "branka", b, Vector3(x3, 7.93, 16.45), J, 0.7, 1.05)
	for x4: float in [-2.3, 2.3]:
		_add(out, "branka", b, Vector3(x4, 7.93, 10.05), S, 0.6, 1.05)
	_add(out, "branka", b, Vector3(2.95, 7.48, 14.65), V, 1.1, 2.15)
	_add(out, "branka", b, Vector3(-2.95, 7.48, 14.65), Z, 1.1, 2.15)
	# zbrojnice (hospodar.forge_armory): dvere a okno do nadvori, dvere do kovarny (venkovni prostor)
	b = "zbrojnice"
	_add(out, "zbrojnice", b, Vector3(-5.45, 1.05, 9.8), S, 1.1, 2.1)
	_add(out, "zbrojnice", b, Vector3(-8.5, 1.62, 9.8), S, 0.6, 0.85)
	_add(out, "zbrojnice", b, Vector3(-10.2, 1.02, 11.55), Z, 1.0, 2.05)
	# sklep pod vezi a kobky (Misa 9. 11., blender/sklep.py, lokace.json sklep_tvrz): otvor pod ramenem schodu ve vezi
	# (vodorovny portal v podlaze prizemi) a pruchod zakladem veze do chodby s kobkami; ven nevede nic (zavrena mistnost)
	var sk: Dictionary = Pravidla.cti("lokace", "sklep_tvrz")
	var sch: Dictionary = sk["schody"]
	var xs := (float(sch["x"][0]) + float(sch["x"][1])) * 0.5
	var ws := float(sch["x"][1]) - float(sch["x"][0])
	var zs := (float(sch["z_horni"]) + float(sch["zabradli_z"][1])) * 0.5
	_add(out, "sklep", "vez", Vector3(xs, 0.0, zs), Vector3(0, 1, 0), ws, 2.0, "vez0")
	_add(out, "vez0", "vez", Vector3(xs, 0.0, zs), Vector3(0, -1, 0), ws, 2.0, "sklep")
	var ch: Dictionary = sk["chodba"]
	var yk := float(sk["y"])
	var xc := (float(ch["x"][0]) + float(ch["x"][1])) * 0.5
	var wc := float(ch["x"][1]) - float(ch["x"][0])
	_add(out, "sklep", "vez", Vector3(xc, yk + 1.0, float(ch["z"][0])), J, wc, 2.0, "kobky")
	_add(out, "kobky", "vez", Vector3(xc, yk + 1.0, float(ch["z"][0])), S, wc, 2.0, "sklep")
	# ubytovna sluzebnictva (Misa 6. 11., blender/hospodar.py quarters): dvere a dve okna do nadvori, ze zaznamu
	# lokace.json ubytovna_tvrz (vnitrni lic predni zdi zf + t)
	var u: Dictionary = Pravidla.cti("lokace", "ubytovna_tvrz")
	var zu := float(u["zf"]) + float(u["t"])
	var dv: Dictionary = u["dvere"]
	_add(out, "ubytovna", "ubytovna", Vector3(float(dv["x"]), float(dv["vyska"]) * 0.5, zu), S, float(dv["sirka"]), float(dv["vyska"]))
	for ok: Array in u["okna"]:
		_add(out, "ubytovna", "ubytovna", Vector3(float(ok[0]), float(ok[1]) + 0.425, zu), S, 0.6, 0.85)
