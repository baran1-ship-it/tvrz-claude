extends Node
## Testy vody (Misa 9. 11., radky 51, 53, 61, 79 tabulky misa_28_chyby.md: „bila hladina nad terenem, hlineny sraz
## kolem, kolikrat jsme to resili“) - treti sada vedle test_svet.gd a test_stavby.gd (jine pomocniky). Spousti ji
## dev_test.gd v rezimu svet se stejnym TVRZ_TEST_JEN: tools/beh.sh jm testy "breh_nadrzi"
##   breh_nadrzi  hladina rybniku (dil Lhota Rybnik_Voda, rybnik tvrze Rybnik_tvrz_voda) lezi na vrstevnici terenu:
##                po obvodu hladiny (hrany site po 1 m) teren pod okrajem ne niz nez hladina - mez (VISI = voda nad
##                vzduchem), od okraje ven do breh_pas_m teren neklesne pod hladinu (PRORVA = breh nizsi nez voda,
##                vypust/koryto pres hraz) a svah brehu ne strmejsi nez breh_max_st (SRAZ). Meze voda.json toky_tvar
##                a pasma.test (popis v pasma.test._breh_nadrzi). Vystup BREH_NADRZI <DRUH> (x, z) popis.

const Pravidla := preload("res://scripts/pravidla.gd")
var main: Node
var sv
var vysledky: Array = []
const TESTY := ["breh_nadrzi"]


func run(p_main: Node) -> void:
	main = p_main
	sv = main.svet
	var jen := OS.get_environment("TVRZ_TEST_JEN").split(",", false)
	var nic := true
	for t: String in TESTY:
		if jen.has(t):
			nic = false
			await call("_" + t)
	if nic:
		return
	var ok := true
	print("TEST VODA ------------------------------")
	for v: Array in vysledky:
		print("TEST %-14s %s  %s" % [v[0], "OK   " if v[1] else "CHYBA", v[2]])
		ok = ok and bool(v[1])
	print("TEST VODA %s" % ("PROSEL" if ok else "NEPROSEL"))


func _vysledek(nazev: String, ok: bool, text: String) -> void:
	vysledky.append([nazev, ok, text])


## Teren pod bodem: paprsek shora na kolize terenu (sveta Teren*, dilu Rybnik_Teren*), ne na stromy a predmety.
func _teren(x: float, z: float, y0: float) -> float:
	var ss: PhysicsDirectSpaceState3D = main.get_world_3d().direct_space_state
	var od := Vector3(x, y0 + 8.0, z)
	var vyl: Array[RID] = []
	for k in 6:
		var q := PhysicsRayQueryParameters3D.create(od, Vector3(x, y0 - 8.0, z))
		q.exclude = vyl
		q.collide_with_areas = false
		var h := ss.intersect_ray(q)
		if h.is_empty():
			return -INF
		var n: Node = h["collider"]
		var jm := ""
		var u: Node = n
		for i in 4:
			if u == null:
				break
			jm += String(u.name) + "/"
			u = u.get_parent()
		if jm.contains("Teren"):
			return (h["position"] as Vector3).y
		vyl.append(h["rid"])
	return -INF


func _breh_nadrzi() -> void:
	await get_tree().physics_frame
	var tt: Dictionary = Pravidla.cti("voda", "toky_tvar")
	var pt: Dictionary = sv.pasma()["test"]
	var tol := float(pt["breh_nadrzi_visi_m"])
	var pas := float(pt["breh_nadrzi_pas_m"])
	var max_st := float(tt["breh_max_st"])
	var n := {"obvod": 0, "visi": 0, "prorva": 0, "sraz": 0, "usti": 0}
	# usti toku do rybnika: voda toku, ne breh (stejne jako test smyslu breh_nadrze)
	var usti: Array = []
	for t: Dictionary in Pravidla.cti("voda", "toky"):
		for q: Array in t["osa_xzy"]:
			usti.append(Vector3(float(q[0]), float(q[1]), float(t["sirka_m"]) / 2.0 + float(tt["breh_sirka_m"])))
	var vypis := 0
	for jm: String in ["Rybnik_Voda*", "Rybnik_tvrz_voda*"]:
		for mi0 in main.find_children(jm, "MeshInstance3D", true, false):
			var mi := mi0 as MeshInstance3D
			var xf := mi.global_transform
			var f := mi.mesh.get_faces()
			# hrany pouzite jednim trojuhelnikem = obvod hladiny
			var hrany := {}
			var stred := Vector3.ZERO
			for i in range(0, f.size(), 3):
				for k in 3:
					var a := xf * f[i + k]
					var b := xf * f[i + (k + 1) % 3]
					stred += a / f.size()
					var ka := Vector3i(roundi(a.x * 20), 0, roundi(a.z * 20))
					var kb := Vector3i(roundi(b.x * 20), 0, roundi(b.z * 20))
					var key := [ka, kb] if str(ka) < str(kb) else [kb, ka]
					var ks := str(key)
					if hrany.has(ks):
						hrany.erase(ks)
					else:
						hrany[ks] = [a, b]
			var hl := stred.y
			var nej_visi := 0.0
			for e: Array in hrany.values():
				var a: Vector3 = e[0]
				var b: Vector3 = e[1]
				var dl := Vector2(b.x - a.x, b.z - a.z).length()
				for s in maxi(1, ceili(dl)):
					var p := a.lerp(b, (s + 0.5) / maxi(1, ceili(dl)))
					var ven := Vector2(p.x - stred.x, p.z - stred.z).normalized()
					if _v_toku(usti, Vector2(p.x, p.z)):
						n["usti"] += 1
						continue
					var y0: float = _teren(p.x, p.z, hl)
					if y0 == -INF:
						continue
					n["obvod"] += 1
					var co := ""
					if y0 < hl - tol:
						n["visi"] += 1
						nej_visi = maxf(nej_visi, hl - y0)
						co = "VISI hladina %.2f nad terenem o %.2f m" % [hl, hl - y0]
					else:
						var py := y0
						var nej_sv := 0.0
						var pod := false
						for k in range(1, int(pas / 0.5) + 1):
							var q := Vector2(p.x, p.z) + ven * 0.5 * k
							if _v_toku(usti, q):
								break                   # dal koryto toku (voda toku, ne breh rybnika)
							var y: float = _teren(q.x, q.y, hl)
							if y == -INF:
								break
							if k == int(pas / 0.5) and y < hl - tol:
								# na konci pasu pod hladinou a i v dvojnasobku = dira v brehu (vypust, koryto pres hraz);
								# melka prohlubenka za valem brehu neni chyba (jako test smyslu breh_nadrze)
								var q2 := Vector2(p.x, p.z) + ven * pas * 2.0
								var y2: float = _teren(q2.x, q2.y, hl)
								pod = y2 != -INF and y2 < hl - tol and not _v_toku(usti, q2)
							nej_sv = maxf(nej_sv, rad_to_deg(atan2(absf(y - py), 0.5)))
							py = y
						if pod:
							n["prorva"] += 1
							co = "PRORVA breh do %.1f m klesne pod hladinu %.2f" % [pas, hl]
						elif nej_sv > max_st:
							n["sraz"] += 1
							co = "SRAZ svah brehu %.0f st. > %.0f" % [nej_sv, max_st]
					if co != "" and vypis < 60:
						vypis += 1
						print("BREH_NADRZI %s (%.1f, %.1f) %s" % [co.get_slice(" ", 0), p.x, p.z, co.substr(co.find(" ") + 1)])
			print("BREH_NADRZI souhrn %s hladina %.2f: obvod %d, nejvic visi %.2f m" % [mi.name, hl, hrany.size(), nej_visi])
	_vysledek("breh_nadrzi", n["obvod"] > 0 and n["visi"] == 0 and n["prorva"] == 0 and n["sraz"] == 0, str(n))


func _v_toku(usti: Array, p: Vector2) -> bool:
	for u: Vector3 in usti:
		if absf(u.x - p.x) < 4.0 and absf(u.y - p.y) < 4.0 and Vector2(u.x - p.x, u.y - p.y).length() < u.z:
			return true
	return false
