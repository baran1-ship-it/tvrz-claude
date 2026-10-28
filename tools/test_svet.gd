extends Node
## Testy sveta pred vydanim (radce 20:05): TVRZ_TEST=svet (dev_test.gd), musi projit, vysledek do docs/stav.md.
##   pokryv         louka bez mezer (radce 07:45): v bode mimo cesty, dvory, vodu, skaly a les soucet pokryvu trsu a drnu
##                  do 0,5 m >= 0,95 u 98 % bodu (5 mist, 200 bodu do 12 m od hrace).
##   dira           oko nevidi diru (radce 09:05/10:50/13:50): snimek z 1,7 m na 3-20 m pred hracem, 3 mista; souvisle
##                  tmave skvrny (< 0,5 x median, otevreni 3 px) >= 400 px: < 0,5 na m2 louky, zadna > 2400 px (~0,3 m2).
##   pasmo          louka bez hrany pasem (radce 10:55): z 1,7 m barva louky na 30, 60 a 100 m proti medianu 5-25 m - jas +-10 %,
##                  odstin +-8 st; 3 mista na slunci.
##   teleport       20x rychle cestovani tvrz - hostinec - Pusta skala a hned otoceni kamery o 360 st za 2 s (louka stavi
##                  bunky ve vlaknech, hlavni vlakno pocita viditelnost; 0.57c pad). Projde = bez padu, hrac ne v kolizi.
##   shadery        nejvic 13 vzorkovacu na shader (Adreno: 14. = shader se nesestavi, teren pruhledny - 0.56).
##   visici         spodek kazde instance MultiMeshe v krajine <= povrch pod ni + 0,3 m (paprsek na fyziku sveta);
##                  louka (vlastni vysky z mrizky) a skaly samy vyjimka. Limit 0.
##   kolize_drobne  fyzika (Misa 20:10): mekke rostliny bez kolize, stromy s kmenem (tvrde veci kolizi maji vzdy).
##   stanoviste     skaly (vychozy) a smrky ne v kosene louce, kameni ne v louce (jen bor, pesiny, voda). Limit 0.
##   dalka          kopec ve 300 m: jas vuci louce u hrace 0,5-0,8, odstin +-10 st.
##   pamet          (0.59, pady 0.58 = dosla RAM) chuze 6 m/s ~5 min tvrz-hostinec-skaly-tvrz: RAM a GPU buffery po
##                  30 s nerostou (plato, +15 %), nejdelsi cas hlavniho vlakna <= 40 ms, bunek louky <= strop.
##   sekani         (0.62 bod 8) let 6 m/s s kreslenim tvrz - les - skalni mesto - Pusta skala: nejdelsi snimek <= 40 ms
##                  (po 5 s); snimky > 30 ms s rozpadem (_process kazdeho uzlu, kresleni CPU, zbytek). Test spoustet s TVRZ_MOBIL=1.
##   prochod        bot projde 5 tras (tvrz-ves, tvrz-Doubrava, tvrz-skaly-hostinec, breh potoka, brana tvrze).
## TVRZ_TEST_JEN=visici,dalka  pusti jen vyjmenovane.

var main: Node
var player: CharacterBody3D
var sv
var vysledky: Array = []


func run(p_main: Node) -> void:
	main = p_main
	player = main.player
	sv = main.svet
	var jen := OS.get_environment("TVRZ_TEST_JEN").split(",", false)
	sv.kolize_vse(true)                         # paprsky pres celou mapu (visici, pokryv...) vidi i vzdalene skaly
	sv.rostliny_vse(true)                       # visici, stanoviste a dalsi prochazi vsechny instance
	for i in 10:
		await get_tree().process_frame
	await get_tree().physics_frame
	for t: String in ["shadery", "sonda", "breh", "visici", "kolize_drobne", "stanoviste", "pokryv", "dira", "pasmo", "dalka", "prochod", "teleport", "pamet", "sekani", "stuj", "autotest", "bod", "louc_zed", "svetla", "vratka", "pamet_stani", "pamet_okruh", "pamet_pauza", "nizka_trava", "interier", "cesty_volne", "steny", "briza", "rybnik_ves", "fyzika", "vlastni_site", "lom_na_zemi", "co_tu", "stavby_na_zemi", "dvere_domu", "lezeni", "fyz_misto", "fyz_stani", "kresleni_rozbor", "kresleni_ab", "kolize_troj", "mapa_vyhledu", "ves_uzly", "zasazeni", "zamek_terenu", "voda_v_korytu", "site_natazene", "telo_zaber", "mlyn", "pravidla_cteni", "vyska_mriz", "logika", "vyska_bod"]:
		if jen.is_empty() or jen.has(t):
			await call("_" + t)
	var ok := true
	print("TEST SVET ------------------------------")
	for v: Array in vysledky:
		print("TEST %-14s %s  %s" % [v[0], "OK   " if v[1] else "CHYBA", v[2]])
		ok = ok and bool(v[1])
	print("TEST SVET %s" % ("PROSEL" if ok else "NEPROSEL"))


## Pravidla ctena (radce 27. 10. 10:45 krok A): kazdy klic pravidla/svet/*.json musi hra precist (pravidla.gd zapisuje
## cteni) - klic, ktery nikdo necte, je chyba; „zapojeno“: false a jen_blender se vypisou zvlast (dalsi krok migrace).
func _pravidla_cteni() -> void:
	# Astra 22:00: nacteni vetve (cti("voda", "rybnik_lhota") -> cely objekt) drive oznacilo vsechny potomky za prectene
	# a zapojeno false / jen_blender se tise preskocily. Ted ctyri skupiny listu: pouzite (hra cetla presne ten klic),
	# vetev (jen predek - pouziti neovereno), odlozene (jen_blender, zapojeno false = pripraveno, ne hotovo),
	# neprectene (= chyba). Do stav.md se pise podil pouzitych, ne "hotovo".
	var P = preload("res://scripts/pravidla.gd")
	var sum := {"pouzite": 0, "vetev": 0, "odlozene": 0, "neprectene": 0}
	var chyby: Array = []
	for f in DirAccess.get_files_at(P.SLOZKA):
		if not f.ends_with(".json"):
			continue
		var nm := f.get_basename()
		var r: Dictionary = P.rozbor(nm)
		for sk: String in sum:
			sum[sk] += (r[sk] as Array).size()
		print("PRAVIDLA %-10s pouzite %3d  vetev %3d  odlozene %3d  neprectene %3d" % [nm, r["pouzite"].size(), r["vetev"].size(), r["odlozene"].size(), r["neprectene"].size()])
		for k in r["neprectene"]:
			chyby.append(k)
			print("PRAVIDLA neprecteno ", k)
		for k in r["vetev"]:
			print("PRAVIDLA jen vetev (pouziti neovereno) ", k)
	_vysledek("pravidla_cteni", chyby.is_empty(), "pouzite %d, jen vetev %d, odlozene %d, neprectene %d %s" % [sum["pouzite"], sum["vetev"], sum["odlozene"], sum["neprectene"], str(chyby)])


## Zasazeni (radce 27. 10. 09:55 bod 5): pro cely svet podle pasem (pravidla_sveta.json pasma) - nic nad jizdnim
## pasem cest (paprsek shora po 4 m na ose a na 0,7 sire hliny: jen teren, mosty), vegetace mimo pasma cest, stromy
## a kere ne ve vzduchu, ulice vsi napric v mezi, teren u zdi domu vsi pod podlahou a ne pod podezdivkou.
## Vypis ZASAZENI <druh> <misto> ...; souhrn podle druhu.
func _zasazeni() -> void:
	var sv: Object = main.svet
	var pa: Dictionary = sv.pasma()
	var pt: Dictionary = pa["test"]
	# hrac ve vsi (kolize stromu a predmetu se nacitaji kolem nej; jeho kapsle je z paprsku vyloucena)
	await main.fast_travel(Vector3(440.0, 0.0, 820.0), Vector3(440.0, 1.6, 810.0), 0.0, "test")
	for _i in 120:
		await get_tree().physics_frame
	var sp := player.get_world_3d().direct_space_state
	var vyl: Array[RID] = [player.get_rid()]
	var pocty := {}
	var chyba := func(druh: String, q: Vector2, co: String) -> void:
		pocty[druh] = int(pocty.get(druh, 0)) + 1
		if int(pocty[druh]) <= 40:
			print("ZASAZENI %s %s %s" % [druh, q.round(), co])
	var trefa := func(q: Vector2, y0: float, y1: float) -> Dictionary:
		var pq := PhysicsRayQueryParameters3D.create(Vector3(q.x, y0, q.y), Vector3(q.x, y1, q.y))
		pq.exclude = vyl
		return sp.intersect_ray(pq)
	# 1) nad jizdnim pasem cest (mosty ze zaznamu cesty.json prechody: osa cesty tam lezi pod mostovkou)
	var mosty: Array = []
	for pr0: Dictionary in load("res://scripts/pravidla.gd").cti("cesty", "prechody"):
		if String(pr0["druh"]) == "most":
			mosty.append([Vector2(float(pr0["stred"][0]), float(pr0["stred"][1])), float(pr0.get("polomer_m", 8.0))])
	for oi in sv.cesty_osy.size():
		var o: Dictionary = sv.cesty_osy[oi]
		var pp: PackedVector2Array = o["p"]
		var ws: PackedFloat32Array = o["w"]
		for i in range(0, pp.size(), 5):
			var t := (pp[mini(i + 1, pp.size() - 1)] - pp[maxi(i - 1, 0)]).normalized()
			var nr := Vector2(-t.y, t.x)
			for b: float in [-0.7, 0.0, 0.7]:
				var q := pp[i] + nr * b * ws[i]
				if mosty.any(func(m: Array) -> bool: return q.distance_to(m[0]) < float(m[1])):
					continue
				var h: Dictionary = trefa.call(q, 300.0, -100.0)
				if h.is_empty() or not (h["collider"] is Node):
					continue
				# povrch, po kterem cesta vede (mostovka, teren dilu): zasah do 0,5 m nad osou cesty neni "nad cestou"
				var ys_o: PackedFloat32Array = o["y"]
				if ys_o.size() > i and float((h["position"] as Vector3).y) < ys_o[i] + 0.5:
					continue
				var nm := String((h["collider"] as Node).name)
				# kolize mostu je uzel "Kolize" pod objektem mostu (Most*, glb) - jmeno predka rozhoduje
				var pr := (h["collider"] as Node).get_parent()
				var nm_p := String(pr.name) + "/" + String(pr.get_parent().name) if pr and pr.get_parent() else ""
				if nm.begins_with("Teren") or nm.to_lower().contains("most") or nm_p.to_lower().contains("most") or nm.begins_with("Nadvori") or nm.begins_with("Rybnik_Lavka"):
					continue
				var co := ""
				if pr:
					for mm in pr.find_children("*", "MeshInstance3D", true, false):
						co = String(mm.name) if co == "" else co
					for mk in pr.get_meta_list():
						co += " %s=%s" % [mk, str(pr.get_meta(mk))]
				chyba.call("nad_cestou_" + sv.typ_osy(oi), q, nm + " (" + nm_p + ") " + co)
	# 2) vegetace v pasmu cest a ve vzduchu
	var r: Dictionary = sv.data["rostliny"]
	var druhy_pasmo := {}
	var visi := float(pt["visi_m"])
	# skaly a balvany: rostlina na nich stoji zamerne nad terenem a jejich kolize se nacita jen kolem hrace
	var skaly := {}
	for k0: String in r:
		if k0.begins_with("skala_") or k0.begins_with("balvan_"):
			for t0: Array in r[k0]:
				var c0 := Vector2i(floori(float(t0[3]) / 8.0), floori(float(t0[11]) / 8.0))
				for dx in range(-1, 2):
					for dz in range(-1, 2):
						skaly[c0 + Vector2i(dx, dz)] = true
	for k: String in r:
		if k.contains("daleko"):
			continue
		var skup: String = sv.skupina(k)
		for tf: Array in r[k]:
			var q := Vector2(float(tf[3]), float(tf[11]))
			var ck: Vector2 = sv.cesta_kraj_osa(q.x, q.y)
			if ck.y >= 0.0 and ck.x < float(sv.odstup_cesty(k, int(ck.y))) - 0.05:
				chyba.call("v_pasmu_" + sv.typ_osy(int(ck.y)) + "_" + skup, q, "%s %.1f m od kraje" % [k, ck.x])
				druhy_pasmo[k] = int(druhy_pasmo.get(k, 0)) + 1
			# levitujici trava a byliny (Misa 27. 10.: „uz nechci videt levitujici travu“): vzorek kazdy 10. kus
			var nizka := skup != "strom" and skup != "ker" and skup != "balvan" and not k.begins_with("skala_") and not k.begins_with("kamen")
			if nizka and (int(tf[3] * 7.0 + tf[11] * 13.0) % 10 == 0) and not skaly.has(Vector2i(floori(q.x / 8.0), floori(q.y / 8.0))):
				var h4: Dictionary = trefa.call(q, float(tf[7]) + sv.NA_POVRCH_NAD, float(tf[7]) - 30.0)
				if not h4.is_empty() and float(tf[7]) - float((h4["position"] as Vector3).y) > visi:
					chyba.call("visi_bylina", q, "%s %.2f m" % [k, float(tf[7]) - float((h4["position"] as Vector3).y)])
			if (skup == "strom" or skup == "ker") and not skaly.has(Vector2i(floori(q.x / 8.0), floori(q.y / 8.0))):
				var h2: Dictionary = trefa.call(q, float(tf[7]) + sv.NA_POVRCH_NAD, float(tf[7]) - 30.0)
				if not h2.is_empty() and float(tf[7]) - float((h2["position"] as Vector3).y) > visi:
					chyba.call("visi_" + skup, q, "%s %.2f m" % [k, float(tf[7]) - float((h2["position"] as Vector3).y)])
	# 2b) rostliny ve vode malych toku a rybniku a na brehovem pasu (pasma voda breh_m) - krome vodnich
	# (rakos, orobinec, lekniny, okrehek) a kamenu; 27. 10.: 249 trsu, keru a stromu v novych tocich kroku B
	var P2 := load("res://scripts/pravidla.gd")
	var breh := float(pa["voda"]["breh_m"])
	var osy: Array = []
	for t: Dictionary in P2.cti("voda", "toky"):
		var o2: Array = t["osa_xzy"]
		var pts := PackedVector2Array()
		for b3: Array in o2:
			pts.append(Vector2(float(b3[0]), float(b3[1])))
		osy.append([pts, float(t["sirka_m"]) * 0.5])
	var rt2: Dictionary = P2.cti("voda", "rybnik_tvrz")
	var rl2: Dictionary = P2.cti("voda", "rybnik_lhota")
	var rts := Vector2(float(rt2["stred"][0]), float(rt2["stred"][1]))
	var rls := Vector2(float(rl2["stred"][0]), float(rl2["stred"][1]))
	for k: String in r:
		if k.contains("daleko") or k.begins_with("skala_") or k.begins_with("balvan_") or k.begins_with("kamen"):
			continue
		if k.contains("rakos") or k.contains("orobinec") or k.contains("leknin") or k.contains("okreh"):
			continue
		for tf: Array in r[k]:
			var q := Vector2(float(tf[3]), float(tf[11]))
			var d: float = sv.od_vody(q.x, q.y, float(tf[7]))          # tataz definice jako rozsev (svet.gd)
			if d < breh:
				chyba.call("ve_vode_" + sv.skupina(k), q, "%s %.1f m od vody" % [k, d])
	# 3) ulice vsi napric
	var pmax := float(pt["pricny_max"])
	for oi in sv.cesty_osy.size():
		if sv.typ_osy(oi) != "ulice_vsi":
			continue
		var pc: Dictionary = sv.pasmo_cesty(oi)
		var o: Dictionary = sv.cesty_osy[oi]
		var pp: PackedVector2Array = o["p"]
		var ws: PackedFloat32Array = o["w"]
		for i in range(0, pp.size(), 5):
			var t := (pp[mini(i + 1, pp.size() - 1)] - pp[maxi(i - 1, 0)]).normalized()
			var nr := Vector2(-t.y, t.x)
			var h0: Dictionary = trefa.call(pp[i], 300.0, -100.0)
			if h0.is_empty():
				continue
			var y0 := float((h0["position"] as Vector3).y)
			var dd := ws[i] + float(pc["rovne_m"])
			for sd: float in [-1.0, 1.0]:
				var h1: Dictionary = trefa.call(pp[i] + nr * sd * dd, 300.0, -100.0)
				if h1.is_empty() or not String((h1["collider"] as Node).name).begins_with("Teren"):
					continue
				var g := absf(float((h1["position"] as Vector3).y) - y0) / dd
				if g > pmax:
					chyba.call("ulice_pricne", pp[i], "%.0f %%" % (g * 100.0))
	# 4) teren u zdi domu vsi
	var pod_m := float(pt["podlaha_teren_m"])
	for d: Dictionary in sv._domy:
		var m: Dictionary = d["m"]
		if not m.has("ix") or not m.has("pod"):
			continue
		var podl := float(d["y"]) + float(m["pod"])
		for qx: float in [-1.0, 1.0]:
			for qz: float in [float(m["b"]), 0.0, float(m.get("ft", m["f"]))]:
				var w: Vector3 = (d["xf"] as Transform3D) * Vector3(qx * (float(m["hw"]) + 0.3), 0.0, qz)
				var h3: Dictionary = trefa.call(Vector2(w.x, w.z), podl + 0.6, podl - 10.0)
				if h3.is_empty() or not String((h3["collider"] as Node).name).begins_with("Teren"):
					continue
				var ty := float((h3["position"] as Vector3).y)
				if ty > podl + 0.05 or ty < float(d["y"]) - pod_m:
					chyba.call("dum_teren", Vector2(w.x, w.z), "%s_%d podlaha %.2f teren %.2f" % [d["typ"], d["k"], podl, ty])
	# 5) dum v ceste (Misa 27. 10.: „dum 1 ve vsi stal v ceste“): body os cest (i ulice vsi) uvnitr pudorysu domu
	# rozsireneho o pul sirky cesty; ulice vsi smi koncit u vrat, ne vest skrz dum
	for d: Dictionary in sv._domy:
		var m: Dictionary = d["m"]
		if not m.has("hw"):
			continue
		var inv: Transform3D = (d["xf"] as Transform3D).affine_inverse()
		var hw := float(m["hw"])
		var zb := minf(float(m["b"]), float(m.get("ft", m["f"])))
		var zf := maxf(float(m["b"]), float(m.get("ft", m["f"])))
		for oi in sv.cesty_osy.size():
			var o: Dictionary = sv.cesty_osy[oi]
			var pp: PackedVector2Array = o["p"]
			var ws: PackedFloat32Array = o["w"]
			# cesticka ke dverim (konec osy u domu) neni chyba
			var dvere := false
			for e: Vector2 in [pp[0], pp[pp.size() - 1]]:
				var le: Vector3 = inv * Vector3(e.x, float(d["y"]), e.y)
				if absf(le.x) < hw + 1.5 and le.z > zb - 1.5 and le.z < zf + 1.5:
					dvere = true
			if dvere:
				continue
			for i in pp.size():
				var l: Vector3 = inv * Vector3(pp[i].x, float(d["y"]), pp[i].y)
				var w := ws[i] * 0.5
				# cesticka ke dverim konci u prucelí (z ~ f) - to neni chyba; chyba = osa uvnitr pudorysu
				if absf(l.x) < hw + w and l.z > zb - w and l.z < zf - 0.3:
					chyba.call("dum_v_ceste_" + sv.typ_osy(oi), pp[i], "%s_%d" % [d["typ"], d["k"]])
					break
	var dk := druhy_pasmo.keys()
	dk.sort_custom(func(a: String, b: String) -> bool: return int(druhy_pasmo[a]) > int(druhy_pasmo[b]))
	for k3: String in dk.slice(0, 20):
		print("ZASAZENI v pasmu druh %s %d" % [k3, druhy_pasmo[k3]])
	var celkem := 0
	for k2: String in pocty:
		celkem += int(pocty[k2])
		print("ZASAZENI souhrn %s %d" % [k2, pocty[k2]])
	_vysledek("zasazeni", celkem == 0, "chyb %d (%s)" % [celkem, str(pocty)])


## Radce 27. 10. 16:45: teren cele mapy podle logiky a fyziky, na mrizce trava_kraj (2 m) po zamku terenu = hotova sit.
## Hlasi shluky 40 m: prohlubne bez vody (priority-flood), svahy nad svah_max bez skaly, hrby a zarezy bez duvodu.
func _logika() -> void:
	var sv: Object = main.svet
	var pl: Dictionary = sv.pasma()["test"]["logika"]
	sv._vyska(0.0, 0.0)
	var g: Dictionary = sv._vys["trava_kraj"]
	var x0 := float(g["x0"])
	var z0 := float(g["z0"])
	var k := float(g["k"])
	var nx: int = g["nx"]
	var nz: int = g["nz"]
	var ys: PackedByteArray = g["y"]
	var h := PackedFloat32Array()
	h.resize(nx * nz)
	for i in nx * nz:
		h[i] = ys.decode_s16(i * 2) / 100.0
	var hk: Dictionary = load("res://scripts/pravidla.gd").cti("svet", "hranice_kresleni")
	var st: Image = sv.stanoviste
	# male toky a generovane rybniky z voda.json (krok B): bunky 4 m podel osy do pul sirky + 2 m
	var mokre := {}
	var P := load("res://scripts/pravidla.gd")
	for t: Dictionary in P.cti("voda", "toky"):
		var o: Array = t["osa_xzy"]
		for k2 in o.size() - 1:
			var a := Vector2(o[k2][0], o[k2][1])
			var b2 := Vector2(o[k2 + 1][0], o[k2 + 1][1])
			for s2 in int(a.distance_to(b2)) + 1:
				var q := a.lerp(b2, s2 / maxf(a.distance_to(b2), 1.0))
				for dx in range(-1, 2):
					for dz in range(-1, 2):
						mokre[Vector2i(floori(q.x / 4.0) + dx, floori(q.y / 4.0) + dz)] = true
	var rt: Dictionary = P.cti("voda", "rybnik_tvrz")
	var voda := func(x: float, z: float, y: float) -> bool:
		if mokre.has(Vector2i(floori(x / 4.0), floori(z / 4.0))):
			return true
		if Vector2(x, z).distance_to(Vector2(rt["stred"][0], rt["stred"][1])) < float(rt["polomer_m"]) + 3.0:
			return true
		var b: Array = sv.koryto.blizko(x, z) if sv.koryto else []
		if not b.is_empty() and float(b[0]) < float(b[2]) + 4.0:
			return true
		if sv.nadrz:
			for nd: Dictionary in sv.nadrz.nadrze:
				if x >= float(nd["x0"]) - 2.0 and z >= float(nd["z0"]) - 2.0 and x <= float(nd["x0"]) + int(nd["nx"]) * 0.5 + 2.0 \
						and z <= float(nd["z0"]) + int(nd["nz"]) * 0.5 + 2.0 and y < float(nd["y"]) + 0.3:
					return true
		if Vector2(x, z).distance_to(sv.RYB_C) < 45.0 and y < float(sv._ryb_y) + 0.3:
			return true
		return absf(x + 4.5) < 70.0 and absf(z) < 70.0          # tvrz: prikop a nadvori maji vlastni teren
	# skala: maska stanoviste, skalni veze a balvany (do 12 m), lom (stena)
	var skaly := {}
	var rr: Dictionary = sv.data["rostliny"]
	for k0: String in rr:
		if k0.begins_with("skala_") or k0.begins_with("balvan_"):
			for t0: Array in rr[k0]:
				var c0 := Vector2i(floori(float(t0[3]) / 6.0), floori(float(t0[11]) / 6.0))
				for dx in range(-2, 3):
					for dz in range(-2, 3):
						skaly[c0 + Vector2i(dx, dz)] = true
	var skala := func(i: int, j: int) -> bool:
		var x := x0 + i * k
		var z := z0 + j * k
		if skaly.has(Vector2i(floori(x / 6.0), floori(z / 6.0))) or float(sv.v_lomu(x, z)) < 8.0:
			return true
		return st != null and i < st.get_width() and j < st.get_height() and st.get_pixel(i, j).b > float(pl["skala_stanoviste"])
	var uvnitr := func(i: int, j: int) -> bool:
		var x := x0 + i * k
		var z := z0 + j * k
		return x > float(hk["x0"]) and x < float(hk["x1"]) and z > float(hk["z0"]) and z < float(hk["z1"])
	var shluky := {}
	var zapis := func(druh: String, i: int, j: int, v: float) -> void:
		var c := "%s (%d, %d)" % [druh, floori((x0 + i * k) / 40.0) * 40 + 20, floori((z0 + j * k) / 40.0) * 40 + 20]
		var e: Array = shluky.get(c, [0, 0.0])
		shluky[c] = [int(e[0]) + 1, maxf(float(e[1]), v)]
	# 1) prohlubne: priority-flood z okraje oblasti kresleni (binarni halda)
	var fil := h.duplicate()
	var hot := PackedByteArray()
	hot.resize(nx * nz)
	var hv: Array[float] = []           # Array (odkaz): lambda by Packed pole zkopirovala
	var hi: Array[int] = []
	var push := func(v: float, idx: int) -> void:
		hv.append(v)
		hi.append(idx)
		var c := hv.size() - 1
		while c > 0:
			var p := (c - 1) >> 1
			if hv[p] <= hv[c]:
				break
			var tv := hv[p]; hv[p] = hv[c]; hv[c] = tv
			var ti := hi[p]; hi[p] = hi[c]; hi[c] = ti
			c = p
	for j in nz:
		for i in nx:
			if not uvnitr.call(i, j):
				hot[j * nx + i] = 1
			elif not uvnitr.call(i - 1, j) or not uvnitr.call(i + 1, j) or not uvnitr.call(i, j - 1) or not uvnitr.call(i, j + 1):
				hot[j * nx + i] = 1
				push.call(h[j * nx + i], j * nx + i)
	while hv.size() > 0:
		var v := hv[0]
		var idx := hi[0]
		var lv := hv[hv.size() - 1]
		var li := hi[hi.size() - 1]
		hv.resize(hv.size() - 1)
		hi.resize(hi.size() - 1)
		if hv.size() > 0:
			hv[0] = lv
			hi[0] = li
			var c := 0
			while true:
				var l := 2 * c + 1
				if l >= hv.size():
					break
				var m := l
				if l + 1 < hv.size() and hv[l + 1] < hv[l]:
					m = l + 1
				if hv[c] <= hv[m]:
					break
				var tv := hv[m]; hv[m] = hv[c]; hv[c] = tv
				var ti := hi[m]; hi[m] = hi[c]; hi[c] = ti
				c = m
		var ci := idx % nx
		var cj := idx / nx
		for d: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var ni := ci + d.x
			var nj := cj + d.y
			if ni < 0 or nj < 0 or ni >= nx or nj >= nz:
				continue
			var n2 := nj * nx + ni
			if hot[n2]:
				continue
			hot[n2] = 1
			fil[n2] = maxf(h[n2], v)
			push.call(fil[n2], n2)
	var min_hl := float(pl["prohlub_m"])
	var bunky_min := int(float(pl["prohlub_plocha_m2"]) / (k * k))
	var vid := PackedByteArray()
	vid.resize(nx * nz)
	var prohlubni := 0
	for j in nz:
		for i in nx:
			var i0 := j * nx + i
			if vid[i0] or fil[i0] - h[i0] < 0.05 or not uvnitr.call(i, j):
				continue
			# souvisla prohlub (fil > h): plocha, nejvetsi hloubka, voda v ni
			var fr: Array[int] = [i0]
			vid[i0] = 1
			var n := 0
			var hl := 0.0
			var mokra := false
			var stred := i0
			while not fr.is_empty():
				var c: int = fr.pop_back()
				n += 1
				if fil[c] - h[c] > hl:
					hl = fil[c] - h[c]
					stred = c
				if voda.call(x0 + (c % nx) * k, z0 + (c / nx) * k, h[c]):
					mokra = true
				for d: int in [1, -1, nx, -nx]:
					var c2 := c + d
					if c2 >= 0 and c2 < nx * nz and not vid[c2] and fil[c2] - h[c2] >= 0.05:
						vid[c2] = 1
						fr.append(c2)
			if hl > min_hl and n >= bunky_min and not mokra:
				prohlubni += 1
				zapis.call("prohlub", stred % nx, stred / nx, hl)
	# 2) svah bez skaly, 3) hrb / zarez bez duvodu
	var tmax := tan(deg_to_rad(float(pl["svah_max_stupne"])))
	var r := int(float(pl["hrb_zaklad_m"]) / k)
	var hrb_m := float(pl["hrb_m"])
	var svahu := 0
	var hrbu := 0
	for j in range(r, nz - r):
		for i in range(r, nx - r):
			if not uvnitr.call(i, j):
				continue
			var x := x0 + i * k
			var z := z0 + j * k
			var c := j * nx + i
			if absf(x + 4.5) < 70.0 and absf(z) < 70.0:
				continue
			var gx := (h[c + 1] - h[c - 1]) / (2.0 * k)
			var gz := (h[c + nx] - h[c - nx]) / (2.0 * k)
			var tn := sqrt(gx * gx + gz * gz)
			var sk: bool = skala.call(i, j)
			if tn > tmax and not sk and not voda.call(x, z, h[c]):
				svahu += 1
				zapis.call("svah", i, j, rad_to_deg(atan(tn)))
			var lap := h[c] - (h[c - r] + h[c + r] + h[c - r * nx] + h[c + r * nx]) / 4.0
			if absf(lap) > hrb_m and not sk:
				var ck: Vector2 = sv.cesta_kraj_osa(x, z)
				var b: Array = sv.koryto.blizko(x, z) if sv.koryto else []
				var duvod: bool = (ck.y >= 0.0 and ck.x < 6.0) or (not b.is_empty() and float(b[0]) < float(b[2]) + 15.0) or voda.call(x, z, h[c])
				if not duvod:
					hrbu += 1
					zapis.call("hrb" if lap > 0.0 else "zarez", i, j, absf(lap))
	var ks := shluky.keys()
	ks.sort_custom(func(a: String, b: String) -> bool: return int(shluky[a][0]) > int(shluky[b][0]))
	for c2: String in ks.slice(0, 80):
		print("LOGIKA %s bodu %d nejvic %.1f" % [c2, shluky[c2][0], shluky[c2][1]])
	_vysledek("logika", prohlubni + svahu + hrbu == 0, "prohlubni bez vody %d, bodu svahu nad %.0f st. bez skaly %d, bodu hrbu/zarezu %d, shluku %d" % [prohlubni, float(pl["svah_max_stupne"]), svahu, hrbu, shluky.size()])


## Diagnostika: v bodech TVRZ_BODY="x,z;x,z" vyska mrizky a vsech siti Teren* pod bodem (ktera sit dela schod).
func _vyska_bod() -> void:
	var sv: Object = main.svet
	var body := OS.get_environment("TVRZ_BODY").split(";", false)
	for b: String in body:
		var v := b.split_floats(",")
		var x := v[0]
		var z := v[1]
		var radek := "VYSKABOD (%.0f, %.0f) mrizka %.2f |" % [x, z, float(sv._vyska(x, z))]
		for n in main.find_children("Teren*", "MeshInstance3D", true, false):
			var mi := n as MeshInstance3D
			if mi.mesh == null:
				continue
			var bb: AABB = mi.global_transform * mi.get_aabb()
			if x < bb.position.x or x > bb.end.x or z < bb.position.z or z > bb.end.z:
				continue
			var inv := mi.global_transform.affine_inverse()
			var o := inv * Vector3(x, 500.0, z)
			var dd := (inv.basis * Vector3.DOWN).normalized()
			var f := mi.mesh.get_faces()
			var best := -INF
			for i in range(0, f.size(), 3):
				var h: Variant = Geometry3D.ray_intersects_triangle(o, dd, f[i], f[i + 1], f[i + 2])
				if h != null:
					best = maxf(best, (mi.global_transform * (h as Vector3)).y)
			if best > -INF:
				radek += " %s%s %.2f" % [mi.name, "" if mi.visible else "(skryta)", best]
		print(radek)
	_vysledek("vyska_bod", true, "viz VYSKABOD")


## Misa 0.96 „levitovala trava a kere“: louka i _na_zem berou vysku z mrizky (svet._vyska), kolize z site terenu.
## Kde se lisi o vic nez pasma.test.visi_m, rostliny levituji nebo jsou zakopane. Vypise shluky 20 m (pocet, nejvetsi).
func _vyska_mriz() -> void:
	var sv: Object = main.svet
	var visi := float(sv.pasma()["test"]["visi_m"])
	var hk: Dictionary = load("res://scripts/pravidla.gd").cti("svet", "hranice_kresleni")
	var sp := player.get_world_3d().direct_space_state
	var shluky := {}
	var n := 0
	var x := float(hk["x0"])
	while x < float(hk["x1"]):
		var z := float(hk["z0"])
		while z < float(hk["z1"]):
			if absf(x + 4.5) > 60.0 or absf(z) > 60.0:          # tvrz ma vlastni teren
				var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 300.0, z), Vector3(x, -100.0, z)))
				if not h.is_empty() and String((h["collider"] as Node).name).begins_with("Teren"):
					var d := float(sv._vyska(x, z)) - float((h["position"] as Vector3).y)
					if absf(d) > visi:
						n += 1
						var c := Vector2i(floori(x / 20.0), floori(z / 20.0))
						var e: Array = shluky.get(c, [0, 0.0])
						shluky[c] = [int(e[0]) + 1, d if absf(d) > absf(float(e[1])) else float(e[1])]
			z += 3.0
		x += 3.0
	var ks := shluky.keys()
	ks.sort_custom(func(a: Vector2i, b: Vector2i) -> bool: return int(shluky[a][0]) > int(shluky[b][0]))
	for c: Vector2i in ks.slice(0, 60):
		print("VYSKAMRIZ shluk (%d, %d) bodu %d nejvic %+.2f m (+ = mrizka nad siti: levituje)" % [c.x * 20 + 10, c.y * 20 + 10, shluky[c][0], shluky[c][1]])
	_vysledek("vyska_mriz", n == 0, "bodu po 3 m s rozdilem nad %.2f m: %d, shluku 20 m: %d" % [visi, n, shluky.size()])


## Ves v oblouku: ktere uzly sveta lezi ve vsi (obal v 340..640 x 700..960) - jmeno, rodic, troj., stred.
func _ves_uzly() -> void:
	var r := Rect2(340, 700, 300, 260)
	var n := 0
	for g in get_tree().root.find_children("*", "MeshInstance3D", true, false):
		var mi := g as MeshInstance3D
		if mi.mesh == null:
			continue
		var bb: AABB = mi.global_transform * mi.get_aabb()
		if not r.intersects(Rect2(bb.position.x, bb.position.z, bb.size.x, bb.size.z)):
			continue
		var t := 0
		for si in mi.mesh.get_surface_count():
			t += mi.mesh.surface_get_array_index_len(si) / 3 if mi.mesh.surface_get_array_index_len(si) > 0 else mi.mesh.surface_get_array_len(si) / 3
		if bb.size.x > 30 or bb.size.z > 30 or n < 400:
			print("VESUZEL %s <%s> troj %d stred %s vel %s" % [mi.name, mi.get_parent().name, t, bb.get_center().round(), bb.size.round()])
		n += 1
	print("VESUZEL celkem ", n)
	_vysledek("ves_uzly", true, "viz VESUZEL")


## Radce 21:15 bod 2: mapa vyhledu - na 8 mistech 8 smeru: kresleni, troj. (render, TVRZ_MOBIL) a vzdalenost
## horizontu (paprsky po terenu z oci, 3 sklony): kde vyhled jde „do Tramtarie“. Vystup VYHLED misto smer ...
func _mapa_vyhledu() -> void:
	var mista := [["louka_tvrz", Vector2(3, 95)], ["ves_naves", Vector2(440, 800)], ["ves_rybnik", Vector2(525, 888)],
			["hostinec", Vector2(-47.8, 927.5)], ["lom", Vector2(150, 935)], ["les", Vector2(-11, 568)], ["pole", Vector2(275, 720)],
			["tabor", Vector2(3, 222)]]
	var jen := OS.get_environment("TVRZ_MISTO")
	var sp := player.get_world_3d().direct_space_state
	for m: Array in mista:
		if jen != "" and not jen.split(",").has(m[0]):
			continue
		var q: Vector2 = m[1]
		await main.fast_travel(Vector3(q.x, 0.0, q.y), Vector3(q.x, 1.6, q.y - 10.0), 0.0, "test")
		var t0 := Time.get_ticks_msec()
		while Time.get_ticks_msec() - t0 < 12000:
			await get_tree().process_frame
		var radky: Array = []
		for k in 8:
			var uhel := k * PI / 4.0
			player.yaw = uhel
			for _i in 4:
				await get_tree().process_frame
			var kr := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
			var tr := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1e6
			var oko: Vector3 = player.cam.global_position
			var d := Vector3(-sin(uhel), 0, -cos(uhel))
			var hor := 0.0
			for sk: float in [-0.02, 0.0, 0.03]:
				var dir := (d + Vector3(0, sk, 0)).normalized()
				var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(oko, oko + dir * 1500.0))
				hor = maxf(hor, oko.distance_to(h["position"]) if not h.is_empty() else 1500.0)
			radky.append("%s %3d kr %4d tr %.2f hor %4.0f" % [["S", "SZ", "Z", "JZ", "J", "JV", "V", "SV"][k], 0, kr, tr, hor])
		print("VYHLED %-11s %s" % [m[0], " | ".join(radky)])
	_vysledek("mapa_vyhledu", true, "viz VYHLED")


## Radce 20:35 K2: kolizni tvary sveta - ConcavePolygon s poctem troj., dlouhe troj. (hrana > 8 m, velky obal v BVH),
## degenerovane (plocha < 1e-4); pak chuze ve vsi (413,781) s merenim fyziky snimku. Chyba: tvar v kontaktu s kapsli
## > 15 k troj.
func _kolize_troj() -> void:
	var vys: Array = []
	for cs in get_tree().root.find_children("*", "CollisionShape3D", true, false):
		var sh := (cs as CollisionShape3D).shape
		if not (sh is ConcavePolygonShape3D):
			continue
		var f := (sh as ConcavePolygonShape3D).get_faces()
		var n := f.size() / 3
		var dl := 0
		var deg := 0
		var mx := 0.0
		for i in n:
			var a := f[i * 3]
			var b := f[i * 3 + 1]
			var c := f[i * 3 + 2]
			var e := maxf(a.distance_to(b), maxf(b.distance_to(c), c.distance_to(a)))
			mx = maxf(mx, e)
			if e > 8.0:
				dl += 1
			if (b - a).cross(c - a).length() < 2e-4:
				deg += 1
		vys.append([n, "%s/%s troj %d, hran > 8 m %d, degen %d, max hrana %.0f m" % [cs.get_parent().get_parent().name if cs.get_parent().get_parent() else "", cs.get_parent().name, n, dl, deg, mx]])
	vys.sort_custom(func(a: Array, b: Array) -> bool: return int(a[0]) > int(b[0]))
	for v: Array in vys.slice(0, 15):
		print("KOLTROJ ", v[1])
	_jako_hra()
	var dg: Object = Engine.get_meta("diag")
	var mx := 0.0
	for tr: Array in [[Vector2(405, 775), Vector2(440, 805)], [Vector2(413, 781), Vector2(470, 830)], [Vector2(-56.6, 930.8), Vector2(-65.9, 919.8)]]:
		var a: Vector2 = tr[0]
		var b: Vector2 = tr[1]
		await main.fast_travel(Vector3(a.x, 0.0, a.y), Vector3(b.x, 1.6, b.y), 0.0, "test")
		for _i in 30:
			await get_tree().process_frame
		var n2 := int(a.distance_to(b) / 0.08)
		var tm := 0.0
		for i in n2:
			player.move_input = Vector2(0, 1)
			var d := (b - a).normalized()
			player.yaw = atan2(-d.x, -d.y)
			await get_tree().process_frame
			tm = maxf(tm, float(dg.get("_sn").get("fyzika", 0)) / 1000.0)
		player.move_input = Vector2.ZERO
		print("KOLTROJ chuze %s -> %s: max fyzika snimku %.1f ms, hrac %s" % [a, b, tm, player.global_position.round()])
		mx = maxf(mx, tm)
	_vysledek("kolize_troj", mx < 8.0, "max fyzika %.1f ms" % mx)


## Kresleni A/B s renderem (xvfb, TVRZ_MOBIL): na miste skutecny pocet kresleni a troj. (engine), pak po jednom skryt
## kazdy velky uzel sveta (2. a 3. uroven s >= 20 geometriemi) a stin slunce -> o kolik kresleni ubude. Top 16.
func _kresleni_ab() -> void:
	var mista := [["hostinec", Vector3(-56.6, 0, 930.8), Vector3(-29.8, 1.6, 928.8)], ["les_hostinec", Vector3(-2, 0, 867), Vector3(30, 1.6, 850)],
			["rybnik", Vector3(525, 0, 888), Vector3(525, 1.6, 860)], ["ves", Vector3(448, 0, 810), Vector3(470, 1.6, 830)]]
	var jen := OS.get_environment("TVRZ_MISTO")
	var mer := func() -> Vector2:
		for _i in 3:
			await get_tree().process_frame
		return Vector2(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1e6)
	var slunce: DirectionalLight3D = null
	for n in get_tree().root.find_children("*", "DirectionalLight3D", true, false):
		if (n as DirectionalLight3D).shadow_enabled:
			slunce = n
	for m: Array in mista:
		if jen != "" and jen != m[0]:
			continue
		await main.fast_travel(m[1], m[2], 0.0, "test")
		var t0 := Time.get_ticks_msec()
		while Time.get_ticks_msec() - t0 < 15000:
			await get_tree().process_frame
		var z: Vector2 = await mer.call()
		print("KRAB %s: kresleni %d troj %.2f M" % [m[0], z.x, z.y])
		# skupiny podle jmena uzlu nebo predka (diag.SKUPINY + stavby, lide, zivot) - kazda skryta naraz
		var skup := [["louka", ["louka_", "kupy", "Louka"]], ["impostory", ["imp_", "impostor"]],
				["stromy", ["dub", "buk", "lipa", "smrk", "borovice", "briza", "olse", "vrba", "fir_", "pine_", "willow"]],
				["kere+puda", ["kapradi", "ker_", "shrub", "bez_", "mech", "moss", "fern", "bark", "dry_", "tree_stump", "root_", "dead_"]],
				["byliny", ["kopretiny", "kvety", "dandelion", "nettle", "byliny", "celandine", "periwinkle", "weed"]],
				["rakos", ["rakos", "orobinec", "reed", "cattail", "leknin", "lily"]], ["skaly", ["skala", "balvan", "kamen", "rock"]],
				["domy vsi", ["Dum_ves", "Dum_", "Stodola", "Pohyb_dum", "Pohyb_stodola", "Pohyb_ves"]], ["vesnice", ["Vesnice"]],
				["tvrz", ["Palac", "Vez", "Brana", "Sin", "Zbrojnice", "Ruiny", "Hradba", "Hnojiste"]], ["hostinec", ["hostinec", "Hostinec"]],
				["predmety", ["Predmety", "predmet"]], ["lide+zivot", ["Lide", "Zivot", "clovek", "CPUParticles"]],
				["teren", ["Teren"]], ["voda", ["Voda", "voda", "Reka", "Potok", "Rybnik_Voda"]]]
		var vsechny := get_tree().root.find_children("*", "GeometryInstance3D", true, false)
		var vys: Array = []
		if slunce:
			slunce.shadow_enabled = false
			var v0: Vector2 = await mer.call()
			slunce.shadow_enabled = true
			vys.append([z.x - v0.x, z.y - v0.y, "STIN SLUNCE"])
		var vzato := {}
		for g: Array in skup:
			var skryte: Array = []
			for n in vsechny:
				var gi := n as GeometryInstance3D
				if vzato.has(gi) or not gi.visible:
					continue
				var hit := false
				var nd: Node = gi
				for _u in 5:
					if nd == null:
						break
					var nm := String(nd.name)
					for pf: String in g[1]:
						if nm.begins_with(pf):
							hit = true
					if hit:
						break
					nd = nd.get_parent()
				if hit:
					skryte.append(gi)
					vzato[gi] = true
					gi.visible = false
			var v: Vector2 = await mer.call()
			for gi: GeometryInstance3D in skryte:
				gi.visible = true
			vys.append([z.x - v.x, z.y - v.y, "%s (%d uzlu)" % [g[0], skryte.size()]])
		var zbyle: Array = []
		for n in vsechny:
			if not vzato.has(n) and (n as GeometryInstance3D).visible:
				zbyle.append(n)
				(n as GeometryInstance3D).visible = false
		var vz: Vector2 = await mer.call()
		for gi: GeometryInstance3D in zbyle:
			gi.visible = true
		vys.append([z.x - vz.x, z.y - vz.y, "ZBYTEK (%d uzlu)" % zbyle.size()])
		var jm := {}
		for gi: GeometryInstance3D in zbyle:
			var k := String(gi.get_parent().name if gi.get_parent() else gi.name).left(20)
			jm[k] = int(jm.get(k, 0)) + 1
		print("KRAB zbytek rodice: %s" % str(jm).left(400))
		# stin po skupinach: cast_shadow vypnout (kolik kresleni stinu skupina stoji)
		for g: Array in skup:
			var vyp: Array = []
			for n in vsechny:
				var gi := n as GeometryInstance3D
				if gi.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
					continue
				var nd: Node = gi
				var hit := false
				for _u in 5:
					if nd == null or hit:
						break
					for pf: String in g[1]:
						if String(nd.name).begins_with(pf):
							hit = true
					nd = nd.get_parent()
				if hit:
					vyp.append([gi, gi.cast_shadow])
					gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if vyp.is_empty():
				continue
			var vs: Vector2 = await mer.call()
			for q: Array in vyp:
				(q[0] as GeometryInstance3D).cast_shadow = q[1]
			vys.append([z.x - vs.x, z.y - vs.y, "  stin: %s (%d)" % [g[0], vyp.size()]])
		vys.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) > float(b[0]))
		for v: Array in vys.slice(0, 26):
			print("KRAB   %-45s -%4d kresleni  -%.2f M troj" % [String(v[2]).left(45), v[0], v[1]])
	_vysledek("kresleni_ab", true, "viz KRAB")


## Misa 0.92 „sekame se vsude“: zaseky = kresleni (1000-1400 kresleni, 2,6-3,7 M troj. u hostince, lesa, rybnika, vsi).
## Na kazdem miste (jako tablet: TVRZ_MOBIL) spocitat viditelne instance v zornem poli a dosahu: kresleni (povrchy,
## MultiMesh = 1 na povrch) a troj. po druzich (jmeno bez cisel / rodic) + kolik z nich vrha stin do 40 m. Top 14.
func _kresleni_rozbor() -> void:
	_jako_hra()
	var mista := [["hostinec", Vector3(-56.6, 0, 930.8), Vector3(-29.8, 1.6, 928.8)], ["les_hostinec", Vector3(-2, 0, 867), Vector3(30, 1.6, 850)],
			["rybnik", Vector3(525, 0, 888), Vector3(525, 1.6, 860)], ["ves", Vector3(448, 0, 810), Vector3(470, 1.6, 830)],
			["nadvori2", Vector3(4, 0, 1), Vector3(-10, 1.6, -10)]]
	for m: Array in mista:
		await main.fast_travel(m[1], m[2], 0.0, "test")
		var lk: Node = main.get_node_or_null("Louka")
		if lk:
			await _dobehni_fronty(lk)
		for _i in 60:
			await get_tree().process_frame
		var cam := get_viewport().get_camera_3d()
		var cp := cam.global_position
		var fr := cam.get_frustum()
		var sk := {}
		var celk := [0, 0, 0]
		for n in get_tree().root.find_children("*", "GeometryInstance3D", true, false):
			var gi := n as GeometryInstance3D
			if not gi.is_visible_in_tree():
				continue
			var bb := gi.get_aabb()
			var w: AABB = gi.global_transform * bb
			var d := w.get_center().distance_to(cp)
			if gi.visibility_range_end > 0.0 and d > gi.visibility_range_end + gi.visibility_range_end_margin:
				continue
			if gi.visibility_range_begin > 0.0 and d < gi.visibility_range_begin:
				continue
			var vfr := true
			for pl: Plane in fr:
				var c := w.get_center()
				var e := w.size * 0.5
				var r := absf(pl.normal.x) * e.x + absf(pl.normal.y) * e.y + absf(pl.normal.z) * e.z
				if pl.distance_to(c) > r:
					vfr = false
					break
			if not vfr:
				continue
			var kr := 0
			var tr := 0
			var mesh: Mesh = null
			var inst := 1
			if gi is MeshInstance3D:
				mesh = (gi as MeshInstance3D).mesh
			elif gi is MultiMeshInstance3D and (gi as MultiMeshInstance3D).multimesh:
				var mm := (gi as MultiMeshInstance3D).multimesh
				mesh = mm.mesh
				inst = mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
			if mesh == null:
				kr = 1
			else:
				kr = mesh.get_surface_count()
				for si in mesh.get_surface_count():
					var ar := mesh.surface_get_arrays(si) if mesh is ArrayMesh and mesh.get_surface_count() < 4 and inst < 50 else []
					if not ar.is_empty():
						tr += ((ar[Mesh.ARRAY_INDEX] as PackedInt32Array).size() if ar[Mesh.ARRAY_INDEX] != null else (ar[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3 * inst
			var stin := gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF and d < 40.0
			var nm := String(gi.name)
			var rod := String(gi.get_parent().name) if gi.get_parent() else ""
			var druh := (nm + "<" + rod).replace("0", "").replace("1", "").replace("2", "").replace("3", "").replace("4", "").replace("5", "").replace("6", "").replace("7", "").replace("8", "").replace("9", "").replace("@", "")
			if not sk.has(druh):
				sk[druh] = [0, 0, 0, 0]
			sk[druh][0] += kr
			sk[druh][1] += tr
			sk[druh][2] += kr if stin else 0
			sk[druh][3] += 1
			celk[0] += kr
			celk[1] += tr
			celk[2] += kr if stin else 0
		var kl: Array = sk.keys()
		kl.sort_custom(func(a: String, b: String) -> bool: return int(sk[a][0]) > int(sk[b][0]))
		print("KRESLENI %s: kresleni %d (+stin %d), troj (cast) %.2f M, druhu %d | engine kresleni %d troj %.2f M" % [m[0], celk[0], celk[2],
				celk[1] / 1e6, kl.size(), Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
				Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1e6])
		for k: String in kl.slice(0, 14):
			print("KRESLENI   %-50s uzlu %4d kresleni %4d stin %4d troj %.3f M" % [k.left(50), sk[k][3], sk[k][0], sk[k][2], float(sk[k][1]) / 1e6])
	_vysledek("kresleni_rozbor", true, "viz KRESLENI")


## Misa 0.90 (tablet, molo 525,888): fyzika 21-63 ms, z toho skript hrace 11 ms, ostatni = server. Stani 240 s
## jako na tabletu (bez rost_vse), kazde 2 s: fyzika/snimek, hrac, voda, aktivni telesa, pary, ostrovy, nejvetsi.
func _fyz_stani() -> void:
	sv.rostliny_vse(false)
	_jako_hra()
	await main.fast_travel(Vector3(525.0, 0.0, 888.0), Vector3(525.0, 3.7, 860.0), 0.0, "test")
	var dg: Object = Engine.get_meta("diag")
	var mx := 0.0
	for k in 120:
		var f := 0.0
		var h := 0.0
		var n := 0
		var t0 := Time.get_ticks_msec()
		while Time.get_ticks_msec() - t0 < 2000:
			await get_tree().process_frame
			f += float(dg.get("_sn").get("fyzika", 0)) / 1000.0
			h += float(dg.get("_cas_minule").get("fyz: hrac", 0)) / 1000.0
			n += 1
		mx = maxf(mx, f / maxf(n, 1))
		print("FYZSTANI t %3d s fyzika %.2f ms hrac %.2f | aktivnich %d paru %d ostrovu %d | hrac %s" % [k * 2, f / maxf(n, 1), h / maxf(n, 1),
				Performance.get_monitor(Performance.PHYSICS_3D_ACTIVE_OBJECTS), Performance.get_monitor(Performance.PHYSICS_3D_COLLISION_PAIRS),
				Performance.get_monitor(Performance.PHYSICS_3D_ISLAND_COUNT), player.global_position.snapped(Vector3.ONE * 0.1)])
	_vysledek("fyz_stani", mx < 4.0, "nejvetsi prumer fyziky za 2 s %.2f ms" % mx)


## Misa 0.89 (tablet, rybnik 525,888 na mole): fyzika 43-63 ms kazdy snimek i ve stani. Rozbor: prumer fyziky
## snimku (razitka diag) ve stani, pak po jednom vypnout kazdy objekt fyziky do 60 m (vrstvy/zpracovani) a zmerit znovu.
func _fyz_misto() -> void:
	_jako_hra()
	await main.fast_travel(Vector3(525.0, 0.0, 888.0), Vector3(525.0, 3.7, 860.0), 0.0, "test")
	for _i in 90:
		await get_tree().process_frame
	var dg: Object = Engine.get_meta("diag")
	var mer := func() -> float:
		var sum := 0.0
		for _i in 60:
			await get_tree().process_frame
			sum += float(dg.get("_sn").get("fyzika", 0)) / 1000.0
		return sum / 60.0
	var zaklad: float = await mer.call()
	print("FYZMISTO zaklad %.2f ms/snimek, hrac %s" % [zaklad, player.global_position.round()])
	var pp := player.global_position
	var obj: Array = []
	for n in main.find_children("*", "CollisionObject3D", true, false):
		var co := n as CollisionObject3D
		if co == player or not co.is_inside_tree():
			continue
		if co.global_position.distance_to(pp) < 60.0 or co is CharacterBody3D or co is RigidBody3D or co is Area3D:
			obj.append(co)
	print("FYZMISTO objektu %d" % obj.size())
	var vys: Array = []
	for co: CollisionObject3D in obj:
		if not is_instance_valid(co):
			continue
		var pm := co.process_mode
		co.process_mode = Node.PROCESS_MODE_DISABLED      # vypne zpracovani i fyziku (disable_mode remove)
		var t: float = await mer.call()
		co.process_mode = pm
		var tvary := 0
		for sh in co.get_children():
			if sh is CollisionShape3D and (sh as CollisionShape3D).shape is ConcavePolygonShape3D:
				tvary += ((sh as CollisionShape3D).shape as ConcavePolygonShape3D).get_faces().size() / 3
		vys.append([zaklad - t, "%s %s (%s) troj %d" % [co.get_class(), co.name, co.get_parent().name if co.get_parent() else "-", tvary]])
	vys.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) > float(b[0]))
	for v: Array in vys.slice(0, 15):
		print("FYZMISTO bez %-60s usetri %.2f ms" % [v[1], v[0]])
	_vysledek("fyz_misto", zaklad < 8.0, "fyzika ve stani %.2f ms, nejvic %s" % [zaklad, vys[0][1] if not vys.is_empty() else "-"])


## Radce 19:10: vlastni sit, ktera ma vypadat jako teren (stena lomu za lesenim): normaly ven (od steny do lomu)
## a obraz neni cerny - 10 bodu na siti z 6 m pred ni, jas > 0,05; prumer jako okolni skala (zprava).
func _vlastni_site() -> void:
	var st: MeshInstance3D = null
	for n in main.find_children("Teren_lom_stena", "MeshInstance3D", true, false):
		st = n
	if st == null:
		_vysledek("vlastni_site", false, "Teren_lom_stena nenalezena")
		return
	var arr := st.mesh.surface_get_arrays(0)
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var nr: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
	var ven := 0
	var kolme := 0
	for i in range(0, v.size(), 3):
		var nn: Vector3 = nr[i]
		if absf(nn.y) < 0.6:                       # lic steny (ne lem nahore)
			kolme += 1
			var n2: Vector2 = sv.nrm_lom(v[i].z)
			if nn.x * n2.x + nn.z * n2.y > 0.0:
				ven += 1
	player.set_flying(true)
	var jasy: Array = []
	var cerne := 0
	var z_list := [915.0, 920.0, 925.0, 930.0, 935.0, 940.0, 945.0, 948.0, 922.0, 938.0]
	for z: float in z_list:
		var f: float = sv.lom_stena_x(z)
		var y0: float = sv._vyska(f + 6.0, z)
		var cil := Vector3(f, y0 + 3.0, z)
		var n2: Vector2 = sv.nrm_lom(z)
		player.place(cil + Vector3(n2.x, 0.0, n2.y) * 6.0 - Vector3(0, 1.0, 0), cil)
		for i in 30:
			await get_tree().process_frame
		var img := get_viewport().get_texture().get_image()
		var c := img.get_pixel(img.get_width() / 2, img.get_height() / 2)
		var j := c.r * 0.3 + c.g * 0.55 + c.b * 0.15
		jasy.append(j)
		if j <= 0.05:
			cerne += 1
	player.set_flying(false)
	var prum := 0.0
	for j: float in jasy:
		prum += j
	prum /= maxf(jasy.size(), 1)
	var ok := kolme > 0 and ven > kolme * 0.9 and cerne == 0
	_vysledek("vlastni_site", ok, "stena lomu: licem ven %d z %d, cernych bodu %d z %d, jas prumer %.2f" % [ven, kolme, cerne, jasy.size(), prum])


## Radce 21:35 (Misa 0.75 "v lomu predmety levituji"): vybaveni lomu a kvadry (Lom_sut) - pata proti terenu
## paprskem dolu (jen teren, ne jine predmety): nejvys 6 cm nad, veci na podlahach leseni (> 1,5 m) se nepocitaji.
## Radce 07:45 "nic ve vzduchu, nic v zemi": nove domy a chyse (svet._domy) - teren (paprsek, kolize Teren*) kolem
## podezdivky 0,1 m za zdi: mezi dnem podezdivky (-0,45) a podlahou (pod); prah vstupu nad terenem pred dvermi <= 0,35 m.
## Pruchod domem (Misa 0.78 "do komory z chodby nelze, tram ve dverich"): kapsle hrace (r 0,3, 1,76 m) ze stredu sine
## do jizby a do komory / chleva; dvere otevrene (kolize kridel vypnute). Vypise, o co se zasekne.
func _dvere_domu() -> void:
	for b in main.find_children("Pohyb_dum_*", "", true, false):
		for c in b.find_children("*", "CollisionShape3D", true, false):
			(c as CollisionShape3D).disabled = true
	await get_tree().physics_frame
	await get_tree().physics_frame
	var space := player.get_world_3d().direct_space_state
	var cap := CapsuleShape3D.new()
	cap.radius = 0.28
	cap.height = 1.7
	var spatne := []
	var n := 0
	for d: Dictionary in sv._domy:
		var m: Dictionary = d["m"]
		if not m.has("sin"):
			continue
		var xf: Transform3D = d["xf"]
		var pod := float(m["pod"])
		var sz := (float(m["sin"][0]) + float(m["sin"][1])) * 0.5
		for cil: String in ["jizba", "komora"]:
			var cz := (float(m[cil][0]) + float(m[cil][1])) * 0.5
			var dvere_x := 0.0
			# x dveri: z modelu (Dvere_Jizba / _Komora / _Chlev) - stred otvoru
			for ch in main.find_children("Pohyb_dum_%d_*" % int(d["k"]), "", true, false):
				var nm := String(ch.name)
				if (cil == "jizba" and nm.ends_with("Jizba")) or (cil == "komora" and (nm.ends_with("Komora") or nm.ends_with("_Chlev"))):
					var ab := (ch as MeshInstance3D).get_aabb()
					dvere_x = ((ch as Node3D).position + ab.get_center()).x
			var y0 := pod + 0.95 + (0.0 if not (String(d["typ"]) == "Rychta" and cil == "komora") else 0.0)
			# rychta: komora zahloubena 0,75 m - cil o tolik niz (po schodech)
			var y1 := y0
			if String(d["typ"]) == "Rychta" and cil == "komora":
				cz = -5.3                          # dvermi a pod patrem k hornimu schodu (komora 0,75 m niz)
			var body := [Vector3(dvere_x, y0, sz), Vector3(dvere_x, y1, cz)]
			var q := PhysicsShapeQueryParameters3D.new()
			q.shape = cap
			q.exclude = [player.get_rid()]
			var a: Vector3 = xf * body[0]
			var b: Vector3 = xf * body[1]
			q.transform = Transform3D(Basis.IDENTITY, a)
			q.motion = b - a
			var r := space.cast_motion(q)
			n += 1
			if r[0] < 0.9:
				q.transform = Transform3D(Basis.IDENTITY, a + (b - a) * r[1])
				q.motion = Vector3.ZERO
				var hit := space.get_rest_info(q)
				var co: Object = instance_from_id(hit.get("collider_id", 0)) if hit.has("collider_id") else null
				spatne.append("%s_%d %s %.0f%% %s %s" % [d["typ"], d["k"], cil, r[0] * 100, co.name if co else "?", (xf.affine_inverse() * (hit.get("point", Vector3.ZERO) as Vector3)).snapped(Vector3.ONE * 0.01)])
	_vysledek("dvere_domu", spatne.is_empty() and n > 0, "%d pruchodu, spatne %s" % [n, str(spatne)])


## Lezeni (FUNKCE 1): po kazdem typu zebriku (dum, rychta, leseni v lomu) nahoru - hrac stoji nahore na podlaze
## (is_on_floor, ne propad) - a zase dolu na nastup.
func _lezeni() -> void:
	var zbs: Array = []
	var typy := {}
	for u: Dictionary in main.info["use"]:
		if String(u.get("kind", "")) == "zebrik" and not bool(u["nahore"]):
			var k := "lom" if (u["zb"]["pata"] as Vector3).x < 300.0 else "dum"
			if typy.get(k, 0) < 3:
				typy[k] = typy.get(k, 0) + 1
				zbs.append(u["zb"])
	var spatne := []
	for zb: Dictionary in zbs:
		player.flying = false
		player.global_position = zb["nastup"]
		await get_tree().physics_frame
		player.climb(zb, false)
		player.move_input = Vector2(0, 1)
		for i in 400:
			await get_tree().physics_frame
			if not player.climbing:
				break
		player.move_input = Vector2.ZERO
		for i in 40:
			await get_tree().physics_frame
		var p := player.global_position
		var s: Vector3 = zb["sestup"]
		var nahore: bool = player.is_on_floor() and absf(p.y - s.y) < 0.35 and not player.climbing
		# Misa 0.82 „kliknu a hodi me to vedle zebriku“: klik na Slezt dolu bez packy - hrac musi zustat na zebriku
		player.climb(zb, true)
		for i in 20:
			await get_tree().physics_frame
		if not player.climbing:
			spatne.append("%s: shora bez packy hned pustil zebrik" % (zb["pata"] as Vector3).snapped(Vector3.ONE * 0.1))
			player.climb(zb, true)
		player.move_input = Vector2(0, -1)
		for i in 400:
			await get_tree().physics_frame
			if not player.climbing:
				break
		player.move_input = Vector2.ZERO
		for i in 30:
			await get_tree().physics_frame
		var dole: bool = absf(player.global_position.y - (zb["nastup"] as Vector3).y) < 0.35
		if not (nahore and dole):
			spatne.append("%s: nahore %s (%s vs %s) dole %s" % [(zb["pata"] as Vector3).snapped(Vector3.ONE * 0.1), nahore, p.snapped(Vector3.ONE * 0.01), s.snapped(Vector3.ONE * 0.01), dole])
	_vysledek("lezeni", spatne.is_empty() and zbs.size() > 2, "%d zebriku %s, spatne %s" % [zbs.size(), str(typy), str(spatne)])


func _stavby_na_zemi() -> void:
	var space := player.get_world_3d().direct_space_state
	var spatne := []
	var n := 0
	for d: Dictionary in sv._domy:
		var m: Dictionary = d["m"]
		var xf: Transform3D = d["xf"]
		var pod := float(m["pod"])
		for qx in [-1.0, 0.0, 1.0]:
			for qz in [-1.0, 0.0, 1.0]:
				if qx == 0.0 and qz == 0.0:
					continue
				var lx: float = qx * (float(m["hw"]) + 0.1)
				var lz: float = (float(m["f"]) + 0.1) if qz > 0.0 else ((float(m["b"]) - 0.1) if qz < 0.0 else 0.0)
				var w := xf * Vector3(lx, 0.0, lz)
				var q := PhysicsRayQueryParameters3D.create(Vector3(w.x, w.y + 30.0, w.z), Vector3(w.x, w.y - 30.0, w.z))
				var ex: Array[RID] = []
				var g := INF
				for k in 8:
					var h := space.intersect_ray(q)
					if h.is_empty():
						break
					if String((h["collider"] as Node).name).begins_with("Teren"):
						g = float((h["position"] as Vector3).y)
						break
					ex.append((h["collider"] as CollisionObject3D).get_rid())
					q.exclude = ex
				if g == INF:
					continue
				n += 1
				var nad := g - xf.origin.y                # teren vuci nule modelu
				# dum: podezdivka -0,45..podlaha; chyse prkenna: zidka 0..0,5 (do svahu zapustena); kurova: kuly 0,29 v zemi
				var dno := -0.45 if d["m"].has("ix") else (-0.03 if pod > 0.2 else -0.28)
				var vrch := pod - 0.02 if d["m"].has("ix") else (0.47 if pod > 0.2 else 0.16)
				if nad < dno or nad > vrch:
					spatne.append("%s_%d (%.0f,%.0f) teren %+.2f" % [d["typ"], d["k"], w.x, w.z, nad])
	_vysledek("stavby_na_zemi", spatne.is_empty() and n > 0, "%d bodu u %d staveb, spatne %d %s" % [n, sv._domy.size(), spatne.size(), str(spatne.slice(0, 6))])


func _lom_na_zemi() -> void:
	var space := player.get_world_3d().direct_space_state
	var zem := func(x: float, z: float) -> float:
		var q := PhysicsRayQueryParameters3D.create(Vector3(x, 80.0, z), Vector3(x, -80.0, z))
		var ex: Array[RID] = []
		for k in 6:
			var h := space.intersect_ray(q)
			if h.is_empty():
				return INF
			if String((h["collider"] as Node).name).begins_with("Teren"):
				return float((h["position"] as Vector3).y)
			ex.append((h["collider"] as CollisionObject3D).get_rid())
			q.exclude = ex
		return INF
	var spatne := []
	var n := 0
	for it: Dictionary in sv.data.get("vybaveni", []):
		var pp: Array = it["p"]
		if sv.v_lomu(float(pp[0]), float(pp[2])) > 0.0 or it.has("leseni") or String(it["id"]).begins_with("leseni") or String(it["id"]) in ["zebrinak", "trakar", "jerab_slapaci"]:
			continue
		var g: float = zem.call(float(pp[0]), float(pp[2]))
		if g == INF:
			continue
		var d := float(pp[1]) - g
		if d > 1.5:
			continue                                   # na podlaze leseni
		n += 1
		if d > 0.06:
			spatne.append("%s (%.0f,%.0f) +%.2f" % [it["id"], pp[0], pp[2], d])
	var kv := 0
	# headless (rychle testy): multimesh nema transformace (dummy renderer) - kvadry jen v sade s renderem
	for mmi in ([] if DisplayServer.get_name() == "headless" else main.find_children("*", "MultiMeshInstance3D", true, false)):
		if not String((mmi as Node).get_parent().name).begins_with("Lom_sut"):
			continue
		var mm := (mmi as MultiMeshInstance3D).multimesh
		var vse: Array = []
		for mmj in main.find_children("*", "MultiMeshInstance3D", true, false):
			if String((mmj as Node).get_parent().name).begins_with("Lom_sut"):
				var m2 := (mmj as MultiMeshInstance3D).multimesh
				for j in m2.instance_count:
					vse.append(m2.get_instance_transform(j).origin)
		for i in mm.instance_count:
			var xf := mm.get_instance_transform(i)
			var na_jinem := false                      # horni vrstva skladu lezi na spodnim kvadru
			for o: Vector3 in vse:
				if o.y < xf.origin.y - 0.15 and Vector2(o.x - xf.origin.x, o.z - xf.origin.z).length() < 0.9:
					na_jinem = true
			if na_jinem:
				continue
			var g2: float = zem.call(xf.origin.x, xf.origin.z)
			if g2 == INF:
				continue
			kv += 1
			# spodni kvadr stoji patou na zemi (druha vrstva je vys - jen kdyz vys nez 0,8 m nad zemi)
			var d2 := xf.origin.y - g2
			if d2 > 0.08 and d2 < 0.4:
				spatne.append("kvadr (%.0f,%.0f) +%.2f" % [xf.origin.x, xf.origin.z, d2])
	_vysledek("lom_na_zemi", spatne.is_empty() and n > 10, "predmetu %d, kvadru %d, nad zemi %d: %s" % [n, kv, spatne.size(), ", ".join(spatne.slice(0, 12))])


## Ladeni (TVRZ_CO="x,z"): co se kresli do 6 m od bodu - MultiMesh instance (jmeno uzlu, vzdalenost, vyska, meritko)
## a ostatni geometrie, jejiz obalka bod obsahuje.
func _co_tu() -> void:
	var v := OS.get_environment("TVRZ_CO").split_floats(",") if OS.has_environment("TVRZ_CO") else PackedFloat64Array([-44.0, 9.0])
	var p := Vector2(v[0], v[1])
	var out := []
	for n in main.find_children("*", "MultiMeshInstance3D", true, false):
		var mmi := n as MultiMeshInstance3D
		if mmi.multimesh == null or not mmi.is_visible_in_tree():
			continue
		var mm := mmi.multimesh
		for i in mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count:
			var xf := mmi.global_transform * mm.get_instance_transform(i)
			var d := Vector2(xf.origin.x, xf.origin.z).distance_to(p)
			if d < 6.0:
				out.append("%s d%.1f y%.1f s%.2f r[%.0f-%.0f]" % [mmi.name, d, xf.origin.y, xf.basis.get_scale().y, mmi.visibility_range_begin, mmi.visibility_range_end])
	for n in main.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if not mi.is_visible_in_tree() or mi.mesh == null:
			continue
		var ab := mi.global_transform * mi.get_aabb()
		if ab.size.x < 40.0 and ab.has_point(Vector3(p.x, ab.position.y + 0.1, p.y)):
			out.append("MI %s %s" % [mi.get_path(), ab])
	for o in out.slice(0, 120):
		print("CO_TU ", o)
	_vysledek("co_tu", true, "%d veci u (%.0f, %.0f)" % [out.size(), p.x, p.y])


## Zamek terenu (docs/pipeline.md, pasma.test.poradi_terenu): kroky stavby, ktere zmenily sit terenu (svet.gd
## teren_kroky), jen ze seznamu a v jeho poradi. Vypis ZAMEK <krok> (0, 0) ... pro mapu stavby.
func _zamek_terenu() -> void:
	var por: Array = sv.pasma()["test"]["poradi_terenu"]
	var chyby: Array = []
	var posl := -1
	for k: Array in sv.teren_kroky:
		var i := por.find(String(k[0]))
		if i < 0:
			chyby.append("%s mimo seznam" % k[0])
			print("ZAMEK mimo_seznam (0, 0) %s (%d siti)" % [k[0], k[1]])
		elif i < posl:
			chyby.append("%s po %s" % [k[0], por[posl]])
			print("ZAMEK poradi (0, 0) %s po %s" % [k[0], por[posl]])
		posl = maxi(posl, i)
	print("ZAMEK kroky: %s" % str(sv.teren_kroky))
	_vysledek("zamek_terenu", chyby.is_empty(), "%d kroku meni teren %s" % [sv.teren_kroky.size(), str(chyby)])


## Voda v korytu (pasma.test _koryto): po vsech upravach hry teren v ose toku pod hladinou a na kraji pasu nad ni.
func _voda_v_korytu() -> void:
	var P = preload("res://scripts/pravidla.gd")
	var pt: Dictionary = sv.pasma()["test"]
	var tt: Dictionary = P.cti("voda", "toky_tvar")
	var sp := player.get_world_3d().direct_space_state
	var vynech: Array = []
	for pr: Dictionary in P.cti("cesty", "prechody"):
		vynech.append([Vector2(float(pr["stred"][0]), float(pr["stred"][1])), float(pr.get("polomer_m", 8.0))])
	for k in ["rybnik_lhota", "rybnik_tvrz"]:
		var r: Dictionary = P.cti("voda", k)
		vynech.append([Vector2(float(r["stred"][0]), float(r["stred"][1])), float(r.get("polomer_m", r.get("voda_polomer_m", 12.0))) + 2.0])
	var teren := func(q: Vector2) -> float:
		var pq := PhysicsRayQueryParameters3D.create(Vector3(q.x, 300.0, q.y), Vector3(q.x, -100.0, q.y))
		pq.exclude = [player.get_rid()]
		for _i in 6:
			var h := sp.intersect_ray(pq)
			if h.is_empty():
				return NAN
			if String((h["collider"] as Node).name).begins_with("Teren"):
				return float((h["position"] as Vector3).y)
			pq.exclude.append((h["collider"] as CollisionObject3D).get_rid())
		return NAN
	var n := {"bodu": 0, "suche": 0, "pres_breh": 0}
	sv.kolize_vse(true)
	for tk: Dictionary in P.cti("voda", "toky"):
		var o: Array = tk["osa_xzy"]
		var kraj := float(tk["sirka_m"]) * 0.5 + float(tt["breh_sirka_m"])
		var s := 0.0
		for i in o.size() - 1:
			var a := Vector2(float(o[i][0]), float(o[i][1]))
			var b := Vector2(float(o[i + 1][0]), float(o[i + 1][1]))
			var L := a.distance_to(b)
			while s < L:
				var q := a.lerp(b, s / maxf(L, 1e-4))
				var hl := lerpf(float(o[i][2]), float(o[i + 1][2]), s / maxf(L, 1e-4))
				s += float(pt["koryto_krok_m"])
				if vynech.any(func(v: Array) -> bool: return q.distance_to(v[0]) < float(v[1])):
					continue
				var y0: float = teren.call(q)
				if is_nan(y0):
					continue
				n["bodu"] += 1
				if y0 > hl - float(pt["hloubka_dno_min_m"]):
					n["suche"] += 1
					if n["suche"] <= 30:
						print("KORYTO suche (%.0f, %.0f) %s dno %.2f hladina %.2f" % [q.x, q.y, tk["id"], y0, hl])
				var nr := (b - a).normalized().orthogonal()
				for sd: float in [-1.0, 1.0]:
					var yk: float = teren.call(q + nr * sd * kraj)
					if not is_nan(yk) and yk < hl - float(pt["koryto_breh_pod_hladinou_m"]):
						n["pres_breh"] += 1
						if n["pres_breh"] <= 30:
							print("KORYTO pres_breh (%.0f, %.0f) %s breh %.2f hladina %.2f" % [(q + nr * sd * kraj).x, (q + nr * sd * kraj).y, tk["id"], yk, hl])
			s -= L
	# soubeh s cestou: osa toku blize ose cesty nez pulsirka + sirka/2 + tok_od_cesty_m, mimo prechody
	n["soubeh"] = 0
	for tk: Dictionary in P.cti("voda", "toky"):
		var o: Array = tk["osa_xzy"]
		for i in range(0, o.size(), 2):
			var q := Vector2(float(o[i][0]), float(o[i][1]))
			if vynech.any(func(v: Array) -> bool: return q.distance_to(v[0]) < float(v[1])):
				continue
			var ck: Vector2 = sv.cesta_kraj_osa(q.x, q.y)
			if ck.y < 0.0:
				continue
			# ck.x = vzdalenost od kraje jizdniho pasu (zaporna uvnitr)
			if ck.x < float(tk["sirka_m"]) * 0.5 + float(pt["tok_od_cesty_m"]):
				n["soubeh"] += 1
				if n["soubeh"] <= 30:
					print("KORYTO soubeh_s_cestou (%.0f, %.0f) %s %.1f m od kraje cesty %d" % [q.x, q.y, tk["id"], ck.x, int(ck.y)])
	_vysledek("voda_v_korytu", n["suche"] == 0 and n["pres_breh"] == 0 and n["soubeh"] == 0, str(n))


## Site natazene (pasma.test _hrana_max_m): trojuhelnik siti vsi s hranou delsi nez hrana_max_m.
func _site_natazene() -> void:
	var lim := float(sv.pasma()["test"]["hrana_max_m"])
	var n := 0
	for nd in main.find_children("Vesnice*", "MeshInstance3D", true, false):
		var mi := nd as MeshInstance3D
		if mi.mesh == null:
			continue
		var xf := mi.global_transform
		var f := mi.mesh.get_faces()
		for i in range(0, f.size(), 3):
			var a := xf * f[i]
			var b := xf * f[i + 1]
			var c := xf * f[i + 2]
			var m := maxf(a.distance_to(b), maxf(b.distance_to(c), c.distance_to(a)))
			if m > lim:
				n += 1
				if n <= 30:
					var s := (a + b + c) / 3.0
					print("SIT natazena (%.0f, %.0f) %s hrana %.1f m" % [s.x, s.z, mi.name, m])
	_vysledek("site_natazene", n == 0, "%d trojuhelniku s hranou > %.0f m" % [n, lim])


## Telo v zaberu (pasma.test _zaber): ruka s louci a ruce na otezich v obraze kamery.
func _telo_zaber() -> void:
	var telo: Node3D = main.get("telo")
	if telo == null:
		_vysledek("telo_zaber", true, "telo vypnute (jizda.json zapojeno_do_hry)")
		return
	var okraj := float(sv.pasma()["test"]["zaber_okraj"])
	var cam: Camera3D = player.get("cam")
	var ks: Skeleton3D = telo.get("kostra")
	var chyby: Array = []
	var v_obraze := func(kost: String) -> bool:
		var i := ks.find_bone(kost)
		if i < 0:
			return false
		var w := ks.global_transform * ks.get_bone_global_pose(i).origin
		if cam.is_position_behind(w):
			return false
		var s := cam.unproject_position(w) / Vector2(cam.get_viewport().get_visible_rect().size)
		print("ZABER kost %s svet %s kamera %s obraz %s" % [kost, w.snapped(Vector3.ONE * 0.01), (cam.global_transform.affine_inverse() * w).snapped(Vector3.ONE * 0.01), s.snapped(Vector2.ONE * 0.01)])
		return s.x > okraj and s.x < 1.0 - okraj and s.y > okraj and s.y < 1.0 - okraj
	player.pitch = 0.0
	main.predmety.hold("louc", true)
	for _i in 30:
		await get_tree().process_frame
	if not v_obraze.call("hand_r"):
		chyby.append("louc")
		print("ZABER louc (%.0f, %.0f) ruka s louci mimo obraz" % [player.global_position.x, player.global_position.z])
	main.predmety.hold("", false)
	var kun: Node = main.get("kun")
	if kun:
		player.global_position = (kun as Node3D).global_position + Vector3(1.5, 0.3, 0)
		kun.nasedni(player)
		for _i in 30:
			await get_tree().physics_frame
		for r in ["hand_r", "hand_l"]:
			if not v_obraze.call(r):
				chyby.append("otezi " + r)
				print("ZABER otezi (%.0f, %.0f) %s mimo obraz" % [player.global_position.x, player.global_position.z, r])
		kun.sesedni()
	_vysledek("telo_zaber", chyby.is_empty(), str(chyby))


## Mlyn (voda.json mlyn.dil, Misa 28. 10.): kolo se po stavidle rozjede a je v chodu do rozjezd_s (mleti), pri
## bezicim kole viditelny dopad vody, dvere mlyna v zaznamu pohybu, uzly vynechat_uzly ve hre nejsou.
func _mlyn() -> void:
	var P = preload("res://scripts/pravidla.gd")
	var d: Dictionary = P.cti("voda", "mlyn")["dil"]
	var chyby: Array = []
	var kola := get_tree().get_nodes_in_group("mlyn_kolo")
	if kola.is_empty():
		_vysledek("mlyn", false, "kolo mlyna chybi (skupina mlyn_kolo)")
		return
	var kolo: Node = kola[0]
	for k in kola:
		k.set("bezi", true)
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < int((float(d["ovladani"]["rozjezd_s"]) + 1.0) * 1000.0):
		await get_tree().process_frame
	if not kolo.call("v_chodu"):
		chyby.append("kolo po stavidle neni v chodu (_w %.2f)" % float(kolo.get("_w")))
	var pad: Node3D = kolo.get("pad")
	if pad == null:
		chyby.append("dopad vody (Mlyn_pad_vody) chybi")
	elif not pad.visible:
		chyby.append("dopad vody pri chodu kola neviditelny")
	for k in kola:
		k.set("bezi", bool(d["ovladani"]["bezi_na_zacatku"]))
	var dvere := 0
	for e: Dictionary in sv.data.get("pohyb", []):
		if String(e.get("name", "")).begins_with("Pohyb_mlyn"):
			dvere += 1
	if dvere == 0:
		chyby.append("dvere mlyna nejsou v zaznamu pohybu")
	for jm: String in d.get("vynechat_uzly", []):
		if main.find_child(jm, true, false) != null:
			chyby.append("uzel %s ve hre (vynechat_uzly)" % jm)
	for c in chyby:
		print("MLYN chyba (%.0f, %.0f) %s" % [float(d["stred"][0]), float(d["stred"][1]), c])
	_vysledek("mlyn", chyby.is_empty(), "dveri %d %s" % [dvere, str(chyby)])


func _vysledek(nazev: String, ok: bool, text: String) -> void:
	vysledky.append([nazev, ok, text])


func _je_skala(nm: String) -> bool:
	return nm.begins_with("skala_")


## Druh rostliny z nazvu uzlu MultiMeshe ("<druh>_<bx>_<bz>").
func _druh(nm: String) -> String:
	var c := nm.split("_")
	while c.size() > 1 and (c[c.size() - 1].is_valid_int() or c[c.size() - 1].begins_with("-")):
		c.remove_at(c.size() - 1)
	return "_".join(c)


## Co je pod body z hlaseni (propad u potoka, stromy bez povrchu pod sebou): vsechny zasahy paprsku shora.
func _sonda() -> void:
	var space := player.get_world_3d().direct_space_state
	var s := ""
	for p: Vector2 in [Vector2(276, 592), Vector2(-109, 595), Vector2(-147, 851), Vector2(10, 61), Vector2(-97, 237)]:
		var o := Vector3(p.x, 200, p.y)
		var zasahy := []
		var ex: Array[RID] = []
		for k in 4:
			var q := PhysicsRayQueryParameters3D.create(o, Vector3(p.x, -150, p.y))
			q.exclude = ex
			var h := space.intersect_ray(q)
			if h.is_empty():
				break
			var c: CollisionObject3D = h["collider"]
			zasahy.append("%s %.1f" % [c.name, (h["position"] as Vector3).y])
			ex.append(c.get_rid())
		s += " | (%.0f, %.0f) mrizka %.1f: %s" % [p.x, p.y, sv._vyska(p.x, p.y), ", ".join(zasahy)]
	# diry v kolizi terenu kolem propadu u mostu (mrizka 0,5 m)
	var diry := 0
	var bb := Rect2()
	for i in 100:
		for j in 100:
			var x := 255.0 + i * 0.5
			var z := 565.0 + j * 0.5
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 200, z), Vector3(x, -150, z)))
			if h.is_empty():
				if diry == 0:
					bb = Rect2(x, z, 0, 0)
				bb = bb.expand(Vector2(x, z))
				diry += 1
	s += " | diry u mostu: %d bodu %s" % [diry, str(bb) if diry > 0 else ""]
	# hladina potoka (Misa 0.62 bod 5): viditelny vrchol hladiny (hloubka > 5 cm) musi mit dno do 1,5 m nebo hloubku
	# shodnou se dnem (tune); jinak visi nad dirou ("trojuhelnik u brehu")
	var ok := true
	var pm := player.get_tree().root.find_child("Potok", true, false) as MeshInstance3D
	if pm and pm.mesh:
		var arr := pm.mesh.surface_get_arrays(0)
		var vv: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var cc: PackedColorArray = arr[Mesh.ARRAY_COLOR]
		var hot := {}
		var visi: Array = []
		for i in vv.size():
			var w := pm.global_transform * vv[i]
			var key := Vector3i(roundi(w.x * 20.0), roundi(w.y * 20.0), roundi(w.z * 20.0))
			if hot.has(key) or cc[i].r * 4.0 < 0.05:
				continue
			hot[key] = true
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(w + Vector3(0, 3.0, 0), w - Vector3(0, 40.0, 0)))
			var hl: float = 99.0 if h.is_empty() else w.y - (h["position"] as Vector3).y
			if hl > 1.5 and absf(hl - cc[i].r * 4.0) > 0.5:
				visi.append("%.0f,%.0f %.1f m" % [w.x, w.z, hl])
		ok = visi.is_empty()
		s += " | hladina: %d viditelnych vrcholu, bez dna do 1,5 m %d %s" % [hot.size(), visi.size(), str(visi.slice(0, 8))]
	_vysledek("sonda", ok, s.substr(3))


func _visici() -> void:
	var space := player.get_world_3d().direct_space_state
	var rostliny: Node = main.find_child("Rostliny", true, false)
	var n := 0
	var zakop := 0
	var celkem := 0
	var nejhorsi: Array = []
	var po_druhu := {}
	for mmi in rostliny.find_children("*", "MultiMeshInstance3D", true, false):
		var nm := String(mmi.name)
		if _je_skala(nm):
			continue
		var mm: MultiMesh = (mmi as MultiMeshInstance3D).multimesh
		if mm == null:
			continue
		var imp := nm.begins_with("impostor_")
		var tol := 0.3
		var xf := (mmi as Node3D).global_transform
		for i in mm.instance_count:
			var pos: Vector3
			if imp:
				var cd := mm.get_instance_custom_data(i)
				pos = xf.origin + Vector3(cd.r, cd.g, cd.b)
			else:
				pos = xf * mm.get_instance_transform(i).origin
			celkem += 1
			var q := PhysicsRayQueryParameters3D.create(pos + Vector3(0, 0.5, 0), pos - Vector3(0, 60, 0))
			var h := space.intersect_ray(q)
			if imp:
				h = sv.paprsek_imp(space, pos, h)
			if h.is_empty():
				# pod nicim nic: zakopane pod terenem (paprsek shora najde povrch nad pate), ne visici
				var hu := space.intersect_ray(PhysicsRayQueryParameters3D.create(pos + Vector3(0, 80, 0), pos))
				if not hu.is_empty():
					zakop += 1
					continue
			var gap := 60.0 if h.is_empty() else pos.y - (h["position"] as Vector3).y
			if gap > tol:
				n += 1
				var d := _druh(nm)
				po_druhu[d] = int(po_druhu.get(d, 0)) + 1
				nejhorsi.append([gap, d, pos, String(mmi.name) + " " + (String((h["collider"] as Node).name) if not h.is_empty() else "-")])
	nejhorsi.sort_custom(func(a: Array, b: Array) -> bool: return a[0] > b[0])
	var s := ""
	# priklady: po jednom z kazdeho druhu (nejvetsi mezera), at je videt kazda pricina
	var videno := {}
	for x: Array in nejhorsi:
		if videno.has(x[1]) or videno.size() >= 14:
			continue
		videno[x[1]] = true
		s += " | %s %.1f m @ (%.0f, %.0f, %.0f) %s" % [x[1], x[0], x[2].x, x[2].y, x[2].z, x[3]]
	_vysledek("visici", n == 0, "%d z %d instanci (zakopanych %d) %s%s" % [n, celkem, zakop, str(po_druhu) if n > 0 else "", s])


## Fyzika (Misa 20:10): mekke rostliny (svet.MEKKE) zadnou kolizi; stromy (plne modely) kmen; tvrde veci kolizi maji.
func _kolize_drobne() -> void:
	var body: Node = main.find_child("Kolize", true, false)
	var tvary := {}                                  # bunka 1 m -> [stred, polomer] kolizi mimo kvadry staveb
	var kvadry := {}
	var vse: Array = []                              # Kolize + bunky Kolize_x_z (sv.kolize_vse)
	for b in body.get_parent().get_children():
		if String(b.name).begins_with("Kolize"):
			vse.append_array(b.get_children())
	for c in vse:
		var cs := c as CollisionShape3D
		if cs == null:
			continue
		var o := cs.global_position
		var key := Vector2i(floori(o.x), floori(o.z))
		if cs.shape is BoxShape3D:
			var sz: Vector3 = (cs.shape as BoxShape3D).size
			if maxf(sz.x, sz.z) < 2.0:
				if not kvadry.has(key):
					kvadry[key] = []
				(kvadry[key] as Array).append(Vector2(o.x, o.z))   # maly kvadr (kamen, vuz, rostlina z exportu)
		else:
			tvary[key] = true
	var r: Dictionary = sv.data["rostliny"]
	var mekke := 0
	var stromy := 0
	var bez_kmene := 0
	var priklad := ""
	for k: String in r:
		if k.contains("_daleko"):
			continue
		var mek := false
		for m: String in sv.MEKKE:
			if k.begins_with(m):
				mek = true
		var strom: bool = sv._imp_druh(k.substr(0, k.rfind("_"))) != "" and not k.contains("sapling")
		if not mek and not strom:
			continue
		for t: Array in r[k]:
			var key := Vector2i(floori(float(t[3])), floori(float(t[11])))
			var u_kvadru := false
			var pt := Vector2(float(t[3]), float(t[11]))
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for c2: Vector2 in kvadry.get(key + Vector2i(dx, dz), []):
						u_kvadru = u_kvadru or c2.distance_to(pt) < 0.6       # kvadr te rostliny, ne soused
			if mek and u_kvadru:
				mekke += 1
				if priklad == "":
					priklad = "%s (%.0f, %.0f)" % [k, t[3], t[11]]
			if strom:
				stromy += 1
				if not tvary.has(key):
					bez_kmene += 1
	_vysledek("kolize", mekke == 0 and bez_kmene < stromy / 100, "mekke s kolizi %d %s, stromy bez kmene %d z %d" % [mekke, priklad, bez_kmene, stromy])


## Vzorkovace na material (0.56: 14 v zem.gdshader -> na Adrenu se shader nesestavil, teren pruhledny; na PC je
## jednotek 32, tak se to neprojevi): Adreno 16, Godot Compatibility si cast bere - nejvic 13 (zem.gdshader 0.55 fungoval).
func _shadery() -> void:
	var nad := ""
	var nej := 0
	for f: String in DirAccess.get_files_at("res://shaders"):
		if not f.ends_with(".gdshader"):
			continue
		var n := 0
		var txt := FileAccess.get_file_as_string("res://shaders/" + f)
		for r: String in txt.split("\n"):
			if r.strip_edges().begins_with("uniform sampler"):
				n += 1
			if r.begins_with("#include"):
				for r2: String in FileAccess.get_file_as_string(r.get_slice("\"", 1)).split("\n"):
					if r2.strip_edges().begins_with("uniform sampler"):
						n += 1
		nej = maxi(nej, n)
		if n > 13:
			nad += " %s %d" % [f, n]
	_vysledek("shadery", nad == "", "nejvic vzorkovacu %d (limit 13)%s" % [nej, nad])


func _pokryv() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	if louka == null:
		_vysledek("pokryv", false, "neni louka")
		return
	player.set_flying(true)
	# 5 mist na louce rozlozenych po mape (kosena i neudrzovana)
	var mista: Array = []
	var r := sv.stan_rect as Rect2
	for j in range(1, 30):
		for i in range(1, 30):
			var a := Vector2(r.position.x + r.size.x * i / 30.0, r.position.y + r.size.y * j / 30.0)
			if sv._louka_m(a.x, a.y) > 0.6 and sv._les(a.x, a.y) < 0.05 and sv._st(2, a.x, a.y) < 0.05 and sv.pes_d(a.x, a.y) >= sv.PES_DMAX - 0.1:          # pes_d konci na PES_DMAX
				mista.append(a)
	var vyber: Array = []
	for k in 5:
		if not mista.is_empty():
			vyber.append(mista[(k * mista.size()) / 5])
	var dobre := 0
	var vse := 0
	var nejhorsi := ""
	var rng := RandomNumberGenerator.new()
	rng.seed = 56
	for a: Vector2 in vyber:
		var y: float = main._ground_hi(a.x, a.y)
		player.place(Vector3(a.x, y + 1.7, a.y), Vector3(a.x + 5.0, y, a.y))
		louka.nacti_okoli()
		for i in 300:
			louka._process(0.0)
		for i in 10:
			await get_tree().process_frame
		var bunky := {}
		var vrstvy := {}
		for mmi in louka.find_children("*", "MultiMeshInstance3D", true, false):
			var mm: MultiMesh = (mmi as MultiMeshInstance3D).multimesh
			if mm == null:
				continue
			var w := 0.0
			var nm := "drn" if mm.mesh == louka._drn else ("trs" if mm.mesh == louka._trs else ("vys" if mm.mesh == louka._vysoka else ("vej" if mm.mesh == louka._vejir else "?")))
			vrstvy[nm] = int(vrstvy.get(nm, 0)) + (mm.instance_count if mm.visible_instance_count < 0 else mm.visible_instance_count)
			if mm.mesh == louka._drn:
				w = 0.25
			elif mm.mesh == louka._trs:
				w = 0.15
			elif mm.mesh == louka._vysoka:
				w = 0.3
			elif mm.mesh == louka._vejir:
				w = 0.25
			if w == 0.0:
				continue
			var xf := (mmi as Node3D).global_transform
			var n := mm.instance_count if mm.visible_instance_count < 0 else mm.visible_instance_count
			# louka: transformace instance jednotkova, pata trsu je v custom data (yzw, soustava bunky)
			var buf := mm.buffer
			for i in n:
				var o := xf * Vector3(buf[i * 16 + 13], buf[i * 16 + 14], buf[i * 16 + 15])
				if Vector2(o.x, o.z).distance_to(a) > 14.0:
					continue
				var key := Vector2i(floori(o.x), floori(o.z))
				if not bunky.has(key):
					bunky[key] = []
				(bunky[key] as Array).append(Vector3(o.x, o.z, w))
		var nb := 0
		for kk in bunky:
			nb += (bunky[kk] as Array).size()
		print("POKRYV misto %s: instanci do 14 m %d, viditelne po vrstvach %s" % [a, nb, str(vrstvy)])
		var tady := 0
		var ok := 0
		var pokusu := 0
		while tady < 40 and pokusu < 400:
			pokusu += 1
			var q := a + Vector2.from_angle(rng.randf() * TAU) * sqrt(rng.randf()) * 12.0
			# mimo cesty, dvory, vodu, skaly, les a stavby (tam louka travu nesmi mit)
			if louka._vzorek(q.x, q.y).x < 0.5 or sv.pes_d(q.x, q.y) < 1.5 or sv._st(2, q.x, q.y) > 0.05 or sv._les(q.x, q.y) > 0.3:
				continue
			tady += 1
			var suma := 0.0
			var kq := Vector2i(floori(q.x), floori(q.y))
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for e: Vector3 in bunky.get(kq + Vector2i(dx, dz), []):
						if Vector2(e.x, e.y).distance_to(q) < 0.5:
							suma += e.z
			var pk := suma / (PI * 0.25)
			if pk >= 0.95:
				ok += 1
			elif nejhorsi == "":
				nejhorsi = "(%.0f, %.0f) %.2f" % [q.x, q.y, pk]
		dobre += ok
		vse += tady
	var podil := float(dobre) / maxf(vse, 1)
	_vysledek("pokryv", vse > 50 and podil >= 0.98, "%d z %d bodu pokryto >= 0,95 (%.0f %%), mist %d%s" % [dobre, vse, podil * 100.0, vyber.size(),
			(", priklad mezery " + nejhorsi) if nejhorsi != "" else ""])


func _dira() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	player.set_flying(true)
	var mista: Array = []
	var r := sv.stan_rect as Rect2
	for j in range(1, 30):
		for i in range(1, 30):
			var a := Vector2(r.position.x + r.size.x * i / 30.0, r.position.y + r.size.y * j / 30.0)
			if sv._louka_m(a.x, a.y) > 0.7 and sv._les(a.x, a.y) < 0.02 and sv._st(2, a.x, a.y) < 0.02 and sv.pes_d(a.x, a.y) >= sv.PES_DMAX - 0.1:
				mista.append(a)
	# plne slunce: paprsek z mista ke slunci nic netrefi (stin stromu by byl "dira", ktera diru neni)
	var slunce: DirectionalLight3D = null
	for n in main.find_children("*", "DirectionalLight3D", true, false):
		slunce = n
	var space := player.get_world_3d().direct_space_state
	var na_slunci: Array = []
	for a: Vector2 in mista:
		if slunce == null:
			na_slunci.append(a)
			continue
		var y0: float = sv._vyska(a.x, a.y)
		var ks := slunce.global_transform.basis.z.normalized()
		var volno := true
		for o: Vector2 in [Vector2(0, 0), Vector2(1.7, 0), Vector2(1.7, 1.0), Vector2(1.7, -1.0), Vector2(3.0, 0)]:
			var z := Vector3(a.x + o.x, y0 + 0.5, a.y + o.y)
			if not space.intersect_ray(PhysicsRayQueryParameters3D.create(z, z + ks * 60.0)).is_empty():
				volno = false
		# koruny nemaji kolizi: ve smeru ke slunci 4-50 m zadna koruna (mapa stanovist R+G)
		var kxz := Vector2(ks.x, ks.z).normalized()
		for dd in range(4, 52, 3):
			var q := a + kxz * dd
			if sv._st(0, q.x, q.y) + sv._st(1, q.x, q.y) > 0.1:
				volno = false
		if volno:
			na_slunci.append(a)
	mista = na_slunci
	var s := ""
	var ok := mista.size() >= 3
	for k in 3:
		if mista.is_empty():
			break
		var a: Vector2 = mista[(k * mista.size()) / 3 + mista.size() / 7]
		var y: float = main._ground_hi(a.x, a.y)
		# pohled na 3-20 m pred hracem (radce 10:50: tam se dira vidi; dal plossi uhel), stred obrazu na 8 m
		player.place(Vector3(a.x, y + 1.7, a.y), Vector3(a.x + 8.0, y, a.y))
		if louka:
			louka.nacti_okoli()
			for i in 300:
				louka._process(0.0)
		for i in 40:
			await get_tree().process_frame
		var img := get_viewport().get_texture().get_image()
		img.save_png("user://test_dira_%d.png" % k)
		var w := img.get_width()
		var h := img.get_height()
		# oblast louky 3-20 m pred hracem: radky 45-95 %, sloupce 20-80 % obrazu
		var x0 := int(w * 0.2)
		var y0 := int(h * 0.45)
		var rw := int(w * 0.6)
		var rh := int(h * 0.5)
		var jasy: Array = []
		var lum := PackedFloat32Array()
		lum.resize(rw * rh)
		var zel := PackedByteArray()
		zel.resize(rw * rh)
		for yy in rh:
			for xx in rw:
				var c := img.get_pixel(x0 + xx, y0 + yy)
				lum[yy * rw + xx] = c.get_luminance()
				if c.g >= c.r * 0.9 and c.g >= c.b:          # travnate pixely
					zel[yy * rw + xx] = 1
					if (xx + yy) % 3 == 0:
						jasy.append(c.get_luminance())
		if jasy.size() < 1000:
			s += " | (%.0f, %.0f) malo zelenych pixelu %d" % [a.x, a.y, jasy.size()]
			ok = false
			continue
		jasy.sort()
		var med: float = jasy[jasy.size() / 2]
		# radce 13:50: dira = souvisla skvrna tmavych pixelu po otevreni 3 px, >= 400 px (~0,05 m2 na 5 m);
		# pixelovy podil jen informativne (stiny mezi stebly ma i KCD)
		var tm := PackedByteArray()
		tm.resize(rw * rh)
		var ntm := 0
		for k2 in rw * rh:
			if lum[k2] < med * 0.5:
				tm[k2] = 1
				ntm += 1
		var er := _morf(tm, rw, rh, true)
		var ot := _morf(er, rw, rh, false)
		var sk := _skvrny(ot, rw, rh)
		var der := 0
		var nejvetsi := 0
		for vel: int in sk:
			nejvetsi = maxi(nejvetsi, vel)
			if vel >= 400:
				der += 1
		# plocha louky v zaberu: rohy oblasti promitnute na zem
		var cam: Camera3D = player.cam
		var sc := get_viewport().get_visible_rect().size / Vector2(w, h)
		var pts: Array = []
		for pc: Vector2 in [Vector2(x0, y0), Vector2(x0 + rw, y0), Vector2(x0 + rw, y0 + rh), Vector2(x0, y0 + rh)]:
			var o := cam.project_ray_origin(pc * sc)
			var dr := cam.project_ray_normal(pc * sc)
			var t := (y - o.y) / minf(dr.y, -0.01)
			pts.append(Vector2(o.x + dr.x * t, o.z + dr.z * t))
		var pl := 0.0
		for k3 in 4:
			var p1: Vector2 = pts[k3]
			var p2: Vector2 = pts[(k3 + 1) % 4]
			pl += p1.x * p2.y - p2.x * p1.y
		pl = absf(pl) * 0.5
		var na_m2 := der / maxf(pl, 1.0)
		ok = ok and na_m2 < 0.5 and nejvetsi < 2400
		s += " | (%.0f, %.0f) der %d na %.0f m2 (%.2f/m2), nejvetsi %d px, tmavych %.1f %%" % [a.x, a.y, der, pl, na_m2, nejvetsi,
				100.0 * ntm / float(rw * rh)]
	_vysledek("dira", ok, s.substr(3) if s != "" else "malo mist")


func _pasmo() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	player.set_flying(true)
	# poledne: kratke stiny (odpoledne 22 st = stin stromu 50 m pres louku, kazde misto by bylo ve stinu)
	main.day.set_time("poledne", 0.01)
	# test meri barvu pasem louky, ne stiny: stiny stromu vypnout (pruh stinu pres 100 m byl "hrana")
	var stiny := {}
	for sl in main.find_children("*", "DirectionalLight3D", true, false):
		stiny[sl] = (sl as DirectionalLight3D).shadow_enabled
		(sl as DirectionalLight3D).shadow_enabled = false
	for k in 10:
		await get_tree().process_frame
	var s := ""
	var ok := true
	var n := 0
	var r := sv.stan_rect as Rect2
	for j in range(1, 72):
		for i in range(1, 72):
			if n >= 3:
				break
			var a := Vector2(r.position.x + r.size.x * i / 72.0, r.position.y + r.size.y * j / 72.0)
			if not r.grow(-160.0).has_point(a):
				continue                                  # u okraje mapy je v zaberu konec terenu (0.58 okraj mapy)
			var smer := _pasmo_smer(a)
			var louka_cela := smer != Vector2.ZERO
			if not louka_cela:
				continue
			n += 1
			var y: float = main._ground_hi(a.x, a.y)
			var cil: Vector2 = a + smer * 100.0
			player.place(Vector3(a.x, y + 1.7, a.y), Vector3(cil.x, sv._vyska(cil.x, cil.y), cil.y))
			if louka:
				louka.nacti_okoli()
				for k in 300:
					louka._process(0.0)
			for k in 40:
				await get_tree().process_frame
			var img := get_viewport().get_texture().get_image()
			img.save_png("user://test_pasmo_%d.png" % n)
			var cam: Camera3D = player.cam
			var sc := Vector2(img.get_width(), img.get_height()) / get_viewport().get_visible_rect().size
			var barvy := {}
			for d: float in [30.0, 60.0, 100.0]:
				var q := a + smer * d
				# v dalce maly ramecek: +-6 px na 100 m = desitky metru do hloubky (les za loukou)
				barvy[d] = _barva(img, cam.unproject_position(Vector3(q.x, main._ground_hi(q.x, q.y), q.y)) * sc, 160, 2)
			# pasmo 0-25 m (radce 10:55): median z 5 bodu 5-25 m, ne jeden bod (pod nohama tmavsi, 8-14 m svetlejsi)
			var bl: Array = []
			for d: float in [5.0, 10.0, 15.0, 20.0, 25.0]:
				var q := a + smer * d
				bl.append(_barva(img, cam.unproject_position(Vector3(q.x, main._ground_hi(q.x, q.y), q.y)) * sc))
			bl.sort_custom(func(c1: Color, c2: Color) -> bool: return c1.get_luminance() < c2.get_luminance())
			var c0: Color = bl[2]
			var t := " | (%.0f, %.0f)" % [a.x, a.y]
			for d: float in [30.0, 60.0, 100.0]:
				var c: Color = barvy[d]
				var jas := c.get_luminance() / maxf(c0.get_luminance(), 0.001)
				var dh := absf(fposmod(c.h * 360.0 - c0.h * 360.0 + 180.0, 360.0) - 180.0)
				ok = ok and absf(jas - 1.0) <= 0.10 and dh <= 8.0
				t += " %d m jas %.2f odstin %.0f" % [d, jas, dh]
			s += t
	main.day.set_time("odpoledne", 0.01)
	for sl in stiny:
		(sl as DirectionalLight3D).shadow_enabled = stiny[sl]
	for k in 10:
		await get_tree().process_frame
	_vysledek("pasmo", ok and n >= 3, (s.substr(3) if s != "" else "") + ("" if n >= 3 else " | malo mist (%d)" % n))


## Morfologie 3 x 3 nad bitovou maskou: eroze (vse kolem 1) nebo dilatace (cokoli kolem 1).
## Smer (z 8), ve kterem je pred hracem 110 m rovne louky bez stromu u merenych bodu a bez stinu; jinak ZERO.
func _pasmo_smer(a: Vector2) -> Vector2:
	_stin_korun(a)                                     # naplni _stromy_mriz
	for kd in 8:
		var smer := Vector2.from_angle(kd * TAU / 8.0)
		var dobre := true
		# louka i do stran (+-20 m) a za 100 m do 140 m: u 100 m je v ramecku i okraj lesa (tmava barva lesa v dalce)
		for m in range(0, 29):
			var q := a + smer * (m * 5.0)
			for bok in [-10.0, 0.0, 10.0]:
				var qb: Vector2 = q + smer.orthogonal() * bok
				if dobre and m >= 18 and sv._les(qb.x, qb.y) > 0.05:
					dobre = false
			if sv._louka_m(q.x, q.y) < 0.7 or sv._les(q.x, q.y) > 0.02 or sv._st(2, q.x, q.y) > 0.02 \
					or sv.pes_d(q.x, q.y) < 2.0 or absf(sv._vyska(q.x, q.y) - sv._vyska(a.x, a.y)) > 6.0:
				dobre = false
				break
		for m2 in [30.0, 60.0, 100.0]:
			var q2: Vector2 = a + smer * m2
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for st: Vector2 in _stromy_mriz.get(Vector2i(floori(q2.x / 16.0) + dx, floori(q2.y / 16.0) + dz), []):
						if dobre and st.distance_to(q2) < (15.0 if m2 > 90.0 else 10.0):   # u 100 m pata stromu u horizontu
							dobre = false
		if dobre:
			return smer
	return Vector2.ZERO


func _morf(m: PackedByteArray, w: int, h: int, eroze: bool) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(w * h)
	for y in range(1, h - 1):
		for x in range(1, w - 1):
			var i := y * w + x
			var su := m[i - w - 1] + m[i - w] + m[i - w + 1] + m[i - 1] + m[i] + m[i + 1] + m[i + w - 1] + m[i + w] + m[i + w + 1]
			out[i] = (1 if su == 9 else 0) if eroze else (1 if su > 0 else 0)
	return out


## Velikosti souvislych skvrn (4-sousedstvi) v masce.
func _skvrny(m: PackedByteArray, w: int, h: int) -> Array:
	var vis := m.duplicate()
	var out: Array = []
	var zas := PackedInt32Array()
	for i in w * h:
		if vis[i] != 1:
			continue
		vis[i] = 2
		zas.clear()
		zas.append(i)
		var n := 0
		while not zas.is_empty():
			var j := zas[zas.size() - 1]
			zas.resize(zas.size() - 1)
			n += 1
			var x := j % w
			for k in [j - 1, j + 1, j - w, j + w]:
				if k < 0 or k >= w * h or vis[k] != 1:
					continue
				if (k == j - 1 and x == 0) or (k == j + 1 and x == w - 1):
					continue
				vis[k] = 2
				zas.append(k)
		out.append(n)
	return out


func _teleport() -> void:
	player.set_flying(false)
	# kde jsou uzly (0.65: 77 tis. uzlu, RAM 1440-1490 MB na tabletu): podle tridy a jmena (bez cisel)
	var tridy := {}
	var jmena := {}
	var zas: Array[Node] = [main.get_tree().root]
	while not zas.is_empty():
		var n: Node = zas.pop_back()
		tridy[n.get_class()] = int(tridy.get(n.get_class(), 0)) + 1
		var jm := String(n.name).rstrip("0123456789_@").left(24)
		jmena[jm] = int(jmena.get(jm, 0)) + 1
		zas.append_array(n.get_children())
	for d: Dictionary in [tridy, jmena]:
		var pole: Array = []
		for k in d:
			pole.append([d[k], k])
		pole.sort_custom(func(a2: Array, b2: Array) -> bool: return a2[0] > b2[0])
		print("UZLY celkem %d: %s" % [Performance.get_monitor(Performance.OBJECT_NODE_COUNT), str(pole.slice(0, 14))])
	var cile := [[Vector3(2.5, 0.0, 40.0), Vector3(0.0, 4.5, 15.0)], [Vector3(-51.3, 0.0, 935.0), Vector3(-67.2, 3.0, 926.4)],
			[Vector3(-197.2, 0.0, 558.6), Vector3(-190.0, 4.0, 540.0)]]
	var louka: Node = main.get_node_or_null("Louka")
	var uviz := 0
	var max_ms := 0.0
	# PC bez GPU: kresleni v 0,25 x (vlakna louky a hlavni vlakno pracuji stejne, jen snimek je levny)
	var sc0 := get_viewport().scaling_3d_scale
	get_viewport().scaling_3d_scale = 0.25
	var n := int(OS.get_environment("TVRZ_SKOKU")) if OS.has_environment("TVRZ_SKOKU") else 9
	for k in n:
		var cl: Array = cile[k % 3]
		await main.fast_travel(cl[0], cl[1], 0.0, "test")
		# rozhlizeni 360 st za 2 s (120 snimku), louka bezi (vlakna stavi bunky)
		for f in 120:
			var t0 := Time.get_ticks_usec()
			player.yaw += TAU / 120.0
			await get_tree().process_frame
			max_ms = maxf(max_ms, (Time.get_ticks_usec() - t0) / 1000.0)
		# hrac neni v kolizi
		var q := PhysicsShapeQueryParameters3D.new()
		var cap := CapsuleShape3D.new()
		cap.radius = 0.3
		cap.height = 1.6
		q.shape = cap
		q.transform = Transform3D(Basis(), player.global_position + Vector3(0, 0.95, 0))
		q.exclude = [player.get_rid()]
		if not player.get_world_3d().direct_space_state.intersect_shape(q, 1).is_empty():
			uviz += 1
	get_viewport().scaling_3d_scale = sc0
	_vysledek("teleport", uviz == 0, "%d skoku bez padu, uviznuti %d, nejdelsi snimek pri rozhlizeni %.0f ms, bunek louky %d" % [n, uviz, max_ms,
			louka._bunky.size() if louka else -1])


func _stanoviste() -> void:
	var r: Dictionary = sv.data["rostliny"]
	var chyby := {}
	var priklad := {}
	for k: String in r:
		if k.contains("_daleko"):
			continue
		var co := ""
		if k.begins_with("skala_") or k.begins_with("borovice_"):
			co = "vychoz/skala" if k.begins_with("skala_") else ""
		if k.begins_with("smrk_"):
			co = "smrk"
		if k.begins_with("kamen_"):
			co = "kameni"
		if co == "":
			continue
		for t: Array in r[k]:
			var x := float(t[3])
			var z := float(t[11])
			if sv.kosena_louka(x, z):
				chyby[co] = int(chyby.get(co, 0)) + 1
				if not priklad.has(co):
					priklad[co] = Vector2(x, z)
	var n := 0
	for c: String in chyby:
		n += int(chyby[c])
	_vysledek("stanoviste", n == 0, "v kosene louce: %s, priklad %s" % [str(chyby), str(priklad)])


## Kopec ve 300 m vs. louka u hrace: prumer pasu obrazu kolem promitnuteho bodu terenu (stromy a obloha se odfiltruji
## jen tim, ze se bere median jasu radku).
func _dalka() -> void:
	player.set_flying(true)
	var vysl: Array = []
	for v: Array in _vyhledy():
		if vysl.size() >= 3:
			break
		var a: Vector2 = v[0]
		var b: Vector2 = v[1]
		var ya: float = main._ground_hi(a.x, a.y)
		var yb: float = main._ground_hi(b.x, b.y)
		player.place(Vector3(a.x, ya + 1.7, a.y), Vector3(b.x, yb + 0.5, b.y))
		var louka: Node = main.get_node_or_null("Louka")
		if louka:
			louka.nacti_okoli()
			for i in 300:
				louka._process(0.0)
		for i in 40:
			await get_tree().process_frame
		var img := get_viewport().get_texture().get_image()
		var cam: Camera3D = player.cam
		var vs := get_viewport().get_visible_rect().size
		var sc := Vector2(img.get_width(), img.get_height()) / vs
		# louka u hrace: median jasu z 8-20 m (jeden bod muze padnout do stinu stromu)
		var bl: Array = []
		for m in [8.0, 12.0, 16.0, 20.0, 24.0]:
			var q: Vector2 = a + (b - a) * m / a.distance_to(b)
			bl.append(_barva(img, cam.unproject_position(Vector3(q.x, main._ground_hi(q.x, q.y), q.y)) * sc))
		bl.sort_custom(func(c1: Color, c2: Color) -> bool: return c1.get_luminance() < c2.get_luminance())
		var cb: Color = bl[2]
		if cb.get_luminance() < 0.15:
			continue                           # louka u hrace ve stinu (budova, svah): srovnani by nedavalo smysl
		var cd := _barva(img, cam.unproject_position(Vector3(b.x, yb, b.y)) * sc)
		var jas := cd.get_luminance() / maxf(cb.get_luminance(), 0.001)
		var dh := absf(fposmod(cd.h * 360.0 - cb.h * 360.0 + 180.0, 360.0) - 180.0)
		var ok := jas >= 0.5 and jas <= 0.8 and dh <= 10.0
		vysl.append([ok, "%s->%s louka %s kopec %s jas %.2f odstin %.0f st" % [a, b, _rgb(cb), _rgb(cd), jas, dh]])
		img.save_png("user://test_dalka_%d.png" % vysl.size())
	var ok_vse := not vysl.is_empty()
	var s := "" if not vysl.is_empty() else " | zadny volny vyhled 300 m pres louku"
	for x: Array in vysl:
		ok_vse = ok_vse and bool(x[0])
		s += " | " + String(x[1])
	_vysledek("dalka", ok_vse, s.substr(3))


## Mista s volnym vyhledem pres louku na 300 m (bez koruny a terenu v ceste, cil je louka): az 3, deterministicky.
func _vyhledy() -> Array:
	var out: Array = []
	var r := sv.stan_rect as Rect2
	for j in range(1, 48):
		for i in range(1, 48):
			var a := Vector2(r.position.x + r.size.x * i / 48.0, r.position.y + r.size.y * j / 48.0)
			# louka u hrace (kosena je od 0.57 jen kolem tvrze a vsi - stacila by malo vyhledu)
			if sv._louka_m(a.x, a.y) <= 0.5 or sv._les(a.x, a.y) >= 0.1 or sv._st(2, a.x, a.y) >= 0.15:
				continue
			var ya: float = sv._vyska(a.x, a.y) + 1.7
			for k in 16:
				var dr := Vector2.from_angle(k * TAU / 16.0)
				var b := a + dr * 300.0
				if not r.has_point(b) or sv._louka_m(b.x, b.y) < 0.5 or sv._les(b.x, b.y) > 0.1:
					continue
				var yb: float = sv._vyska(b.x, b.y)
				var volno := true
				for m in range(1, 60):
					var q := a + dr * (m * 5.0)
					var yq: float = lerpf(ya, yb + 0.3, m / 60.0)
					if sv._vyska(q.x, q.y) > yq - 0.3 or sv._les(q.x, q.y) > 0.15 or sv._st(2, q.x, q.y) > 0.05:
						volno = false
						break
				# louka u hrace na slunci (koruny ve smeru slunce by ji zastinily - pak srovnani nedava smysl)
				if volno and _stin_korun(a + dr * 16.0, false):
					volno = false
				if volno:
					out.append([a, b])
					break
			if out.size() >= 6:
				return out
	return out


## Lezi bod ve stinu korun? Ve smeru ke slunci 4-50 m koruna (mapa stanovist R+G) nebo samostatny strom do 6 m
## od paprsku ke slunci (osamely strom mapa korun nema - "les je zapoj").
var _stromy_mriz := {}


func _stin_korun(a: Vector2, samostatne := true) -> bool:
	var slunce: DirectionalLight3D = null
	for n in main.find_children("*", "DirectionalLight3D", true, false):
		slunce = n
	if slunce == null:
		return false
	if _stromy_mriz.is_empty():
		var r: Dictionary = sv.data["rostliny"]
		for k: String in r:
			if k.contains("_daleko") or sv._imp_druh(k.substr(0, k.rfind("_"))) == "":
				continue
			for t: Array in r[k]:
				var c := Vector2i(floori(float(t[3]) / 16.0), floori(float(t[11]) / 16.0))
				if not _stromy_mriz.has(c):
					_stromy_mriz[c] = []
				(_stromy_mriz[c] as Array).append(Vector2(float(t[3]), float(t[11])))
	var ks := slunce.global_transform.basis.z
	var kxz := Vector2(ks.x, ks.z).normalized()
	# delka stinu podle vysky slunce (strom ~18 m)
	var delka := clampf(18.0 / maxf(tan(asin(clampf(ks.y, 0.05, 1.0))), 0.1), 4.0, 52.0)
	for dd in range(2, int(delka) + 1, 2):
		var q: Vector2 = a + kxz * dd
		if sv._st(0, q.x, q.y) + sv._st(1, q.x, q.y) > 0.3:
			return true
		if not samostatne:
			continue
		for dx in range(-1, 2):
			for dz in range(-1, 2):
				for st: Vector2 in _stromy_mriz.get(Vector2i(floori(q.x / 16.0) + dx, floori(q.y / 16.0) + dz), []):
					if st.distance_to(q) < 7.0:
						return true
	return false


func _barva(img: Image, p: Vector2, sx := 40, sy := 6) -> Color:
	var c := Color(0, 0, 0)
	var k := 0
	for dx in range(-sx, sx + 1, 4):
		for dy in range(-sy, sy + 1, maxi(1, sy / 2)):
			var q := Vector2i(clampi(int(p.x) + dx, 0, img.get_width() - 1), clampi(int(p.y) + dy, 0, img.get_height() - 1))
			c += img.get_pixelv(q)
			k += 1
	return c / float(maxi(k, 1))


func _rgb(c: Color) -> String:
	return "(%d,%d,%d)" % [roundi(c.r * 255), roundi(c.g * 255), roundi(c.b * 255)]


func _prochod() -> void:
	var P: Array = sv.PESINY
	var trasy := {
		"tvrz-ves": _osa(P[1]) + _osa(P[3]),
		"tvrz-Doubrava": _osa(P[0]),
		"tvrz-skaly-hostinec": _osa(P[2]),
		"breh potoka": _breh_potoka(),
		"brana tvrze": [Vector2(-4, 2), Vector2(0, 8), Vector2(0, 16), Vector2(0, 26), Vector2(2.5, 40)],
		# radce 18:35 (Misa: na schodech na ochoz se zasekl, predtim propadl podestou): nahoru po obou ramenech
		"schody na ochoz": [Vector2(12.0, 5.65), Vector2(9.0, 5.65), Vector2(4.6, 5.65), Vector2(4.6, 7.2), Vector2(4.6, 9.0), Vector2(4.6, 11.5)],
		# bokem (hrac nejde stredem): u jizniho zabradli nahoru, u severniho dolu, zatacka na podeste u okraju
		# vez v SZ rohu: dve patra po schodech do L (Misa 0.70 "ve vezi 2x propadl")
		"schody ve vezi": [Vector2(-23.5, -11.0), Vector2(-25.75, -11.0), Vector2(-25.75, -14.75), Vector2(-21.0, -14.75),
				Vector2(-25.75, -14.75), Vector2(-25.75, -11.0), Vector2(-25.75, -14.75), Vector2(-20.6, -14.75)],
		# ochoz zapadni hradby u veze (Misa 0.70 "propadl z ochozu", (-13,14) y 6,5)
		"ochoz": [Vector2(4.6, 11.5), Vector2(4.6, 14.65), Vector2(-6.0, 14.65), Vector2(-8.0, 14.0), Vector2(-20.0, 14.0), Vector2(-24.6, 13.6),
				Vector2(-20.0, 14.0), Vector2(-8.0, 14.0), Vector2(-6.0, 14.65), Vector2(6.0, 14.65), Vector2(10.0, 14.0), Vector2(16.8, 13.0), Vector2(17.0, 2.0)],
		# palac: schody ze dvora od zapadu na pavlac (F1 3,9), po pavlaci a zpet dolu
		"schody na pavlac": [Vector2(-11.0, -6.3), Vector2(-3.6, -6.3), Vector2(-2.4, -6.3), Vector2(4.0, -6.3),
				Vector2(-2.4, -6.3), Vector2(-11.0, -6.3), Vector2(-3.6, -6.3), Vector2(3.0, -6.3)],
		"schody na ochoz bokem": [Vector2(12.0, 6.0), Vector2(9.0, 6.0), Vector2(5.0, 6.0), Vector2(4.95, 7.2), Vector2(4.95, 9.0),
				Vector2(4.6, 11.5), Vector2(4.3, 9.0), Vector2(4.3, 7.2), Vector2(4.3, 5.4), Vector2(6.0, 5.3), Vector2(9.0, 5.3), Vector2(12.0, 5.3)],
	}
	player.set_flying(false)
	# 4x zrychleni s 240 kroky fyziky/s: krok hry zustava 1/60 s (jinak pad pres tenkou trimesh terenu)
	Engine.physics_ticks_per_second = 240
	Engine.max_physics_steps_per_frame = 16
	Engine.time_scale = 4.0
	get_viewport().disable_3d = true          # chuze nepotrebuje obraz: snimek 3 M troj. brzdil 2 km tras nad 50 min
	for i in 120:
		await get_tree().physics_frame
	var s := ""
	var ok_vse := true
	var jen_t := OS.get_environment("TVRZ_PROCHOD")          # jen vybrane trasy (napr. "schody na ochoz")
	for nm: String in trasy:
		if jen_t != "" and not jen_t.split(",").has(nm):
			continue
		var r: Array = await _jdi(trasy[nm])
		if nm == "schody ve vezi":
			var yv := player.global_position.y
			r = [r[0] and yv > 12.5, "%s, %s (y %.1f)" % [r[1], "nahore podruhe" if yv > 12.5 else "nahore ne", yv]]
		if nm == "ochoz":
			var yo := player.global_position.y
			r = [r[0] and yo > 5.5, "%s, %s (y %.1f)" % [r[1], "na ochozu" if yo > 5.5 else "spadl", yo]]
		if nm == "schody na pavlac":
			var yp := player.global_position.y
			r = [r[0] and yp > 3.7, "%s, %s (y %.1f)" % [r[1], "na pavlaci" if yp > 3.7 else "pavlac ne", yp]]
		if nm == "schody na ochoz":
			# dosel nahoru (podesta ochozu ~7 m), ne pod schody
			var y := player.global_position.y
			if y < 5.5:
				r = [false, "%s, nahore ne (y %.1f)" % [r[1], y]]
			else:
				r = [r[0], "%s, y %.1f" % [r[1], y]]
		ok_vse = ok_vse and bool(r[0])
		s += " | %s: %s" % [nm, r[1]]
	Engine.time_scale = 1.0
	get_viewport().disable_3d = false
	Engine.physics_ticks_per_second = 60
	_vysledek("prochod", ok_vse, s.substr(3))


## Po svahu zarezu potoka u mostu (vnitrni a vnejsi breh se stridaji), 2 m od vody.
## Pesina tak, jak je vykreslena (sv.pes_osa - obchazi skaly), ne ridici body PESINY: usek osy od bodu nejbliz
## zacatku k bodu nejbliz konci, po 4 m.
func _osa(ridici: Array) -> Array:
	var osa: PackedVector2Array = sv.pes_osa
	var a: Vector2 = ridici[0]
	var b: Vector2 = ridici[ridici.size() - 1]
	# useky osy mezi Vector2.INF; vybrat ten, kde je zacatek i konec nejbliz (pesiny se v ose potkavaji u tvrze)
	var best := INF
	var ia := 0
	var ib := 0
	var s0 := 0
	for i in osa.size() + 1:
		if i < osa.size() and osa[i] != Vector2.INF:
			continue
		var ja := -1
		var jb := -1
		for j in range(s0, i):
			if ja < 0 or osa[j].distance_to(a) < osa[ja].distance_to(a):
				ja = j
			if jb < 0 or osa[j].distance_to(b) < osa[jb].distance_to(b):
				jb = j
		if ja >= 0 and osa[ja].distance_to(a) + osa[jb].distance_to(b) < best:
			best = osa[ja].distance_to(a) + osa[jb].distance_to(b)
			ia = ja
			ib = jb
		s0 = i + 1
	var krok := 2 if ib >= ia else -2
	var out: Array = []
	var i := ia
	while (krok > 0 and i < ib) or (krok < 0 and i > ib):
		out.append(osa[i])
		i += krok
	out.append(osa[ib])
	return out


func _breh_potoka() -> Array:
	# breh, po kterem se da jit: strana s mensim prevysenim nad vodou (jesep), ne narazovy breh pod stenou zarezu
	var k = sv.koryto
	var strany: Array = [[], []]
	var prev := [0.0, 0.0]
	for i in range(150, 186, 3):
		var a: Vector2 = k.body[i]
		var b: Vector2 = k.body[i + 1]
		for si in 2:
			var q: Vector2 = a + (b - a).normalized().orthogonal() * (float(k.sirky[i]) + 2.0) * (1.0 if si == 0 else -1.0)
			strany[si].append(q)
			prev[si] += absf(sv._vyska(q.x, q.y) - sv._vyska(a.x, a.y))
	return strany[0] if prev[0] <= prev[1] else strany[1]


func _jdi(body: Array) -> Array:
	var a: Vector2 = body[0]
	# start na volnem miste (ne uvnitr kamene na zacatku pesiny): spirala do 4 m
	var space := player.get_world_3d().direct_space_state
	var sq := PhysicsShapeQueryParameters3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.35
	cap.height = 1.7
	sq.shape = cap
	for k in 24:
		var q := a + Vector2.from_angle(k * 2.4) * (k * 0.17)
		sq.transform = Transform3D(Basis(), Vector3(q.x, main._ground_hi(q.x, q.y) + 1.0, q.y))
		if space.intersect_shape(sq, 1).is_empty():
			a = q
			break
	player.place(Vector3(a.x, main._ground_hi(a.x, a.y) + 1.0, a.y), Vector3(a.x, 0, a.y + 1.0))
	for i in 20:
		await get_tree().physics_frame
	var ujito := 0.0
	var na_zemi := player.global_position
	for j in range(1, body.size()):
		var c: Vector2 = body[j - 1]
		var d: Vector2 = body[j]
		var n := maxi(1, int(c.distance_to(d) / 5.0))
		for m in range(1, n + 1):
			var wp := c.lerp(d, float(m) / n)
			var stuck := 0.0
			var t := 0.0
			var last := player.global_position
			if OS.has_environment("TVRZ_PROCHOD"):
				print("PROCHOD k ", wp, " z ", player.global_position)
			var tol := 1.5 if not OS.has_environment("TVRZ_PROCHOD") else 0.5
			while Vector2(wp.x - player.global_position.x, wp.y - player.global_position.z).length() > tol:
				var to := Vector2(wp.x - player.global_position.x, wp.y - player.global_position.z)
				player.yaw = atan2(-to.x, -to.y)
				var side := 0.0
				var vpred := 1.0
				if stuck > 0.6:
					side = 0.8 if int(stuck * 1.5) % 2 == 0 else -0.8
				if stuck > 2.0:
					# obejit prekazku jako hrac (kmen olse na brehu, 0.69): hlavne bokem, strida strany po 1,2 s
					side = 1.0 if int(stuck / 1.2) % 2 == 0 else -1.0
					vpred = 0.25
				player.move_input = Vector2(side, vpred)
				await get_tree().physics_frame
				t += 1.0 / 60.0
				if OS.has_environment("TVRZ_PROCHOD") and fmod(t, 0.1) < 1.0 / 60.0:
					print("PROCHOD  ", player.global_position, " zem ", player.is_on_floor(), " v ", player.velocity)
				if player.is_on_floor():
					na_zemi = player.global_position
				if player.global_position.distance_to(last) > 0.4:
					ujito += Vector2(player.global_position.x - last.x, player.global_position.z - last.z).length()
					last = player.global_position
					stuck = 0.0
				else:
					stuck += 1.0 / 60.0
				if stuck > 6.0 or t > 40.0 or player.global_position.y < -60.0:
					player.move_input = Vector2.ZERO
					for si in player.get_slide_collision_count():
						var kc := player.get_slide_collision(si)
						var ow := kc.get_collider() as CollisionObject3D
						var sh = ow.shape_owner_get_owner(ow.shape_find_owner(kc.get_collider_shape_index())) if ow else null
						print("PROCHOD naraz ", kc.get_position(), " normala ", kc.get_normal(), " tvar ",
								(sh as Node3D).global_position if sh is Node3D else "?", " ", (sh as CollisionShape3D).shape.get("size") if sh is CollisionShape3D else "")
					# co stoji v ceste: paprsek ve vysce kolen a hrudi smerem k cili
					var pp := player.global_position
					var smer := Vector3(to.x, 0, to.y).normalized()
					var co := ""
					for hv: float in [-0.8, -0.4, 0.4, 1.2]:
						var q := PhysicsRayQueryParameters3D.create(pp + Vector3(0, hv, 0), pp + Vector3(0, hv, 0) + smer * 1.5)
						q.exclude = [player.get_rid()]
						var h := player.get_world_3d().direct_space_state.intersect_ray(q)
						if not h.is_empty():
							var col: CollisionObject3D = h["collider"]
							var tv := ""
							var own = col.shape_owner_get_owner(col.shape_find_owner(int(h["shape"])))
							if own is CollisionShape3D:
								var cs3 := own as CollisionShape3D
								tv = " [%s @ (%.0f, %.1f, %.0f)]" % [cs3.shape.get_class(), cs3.global_position.x, cs3.global_position.y, cs3.global_position.z]
							co += " %s%s v %.1f m (%.0f, %.1f, %.0f)" % [col.name, tv, hv, h["position"].x, h["position"].y, h["position"].z]
					# v cem hrac vezi (start uvnitr telesa)
					var sq2 := PhysicsShapeQueryParameters3D.new()
					var cap2 := CapsuleShape3D.new()
					cap2.radius = 0.32
					cap2.height = 1.7
					sq2.shape = cap2
					sq2.transform = Transform3D(Basis(), pp + Vector3(0, 0.9, 0))
					sq2.exclude = [player.get_rid()]
					for hh: Dictionary in player.get_world_3d().direct_space_state.intersect_shape(sq2, 4):
						var c4: CollisionObject3D = hh["collider"]
						var own4 = c4.shape_owner_get_owner(c4.shape_find_owner(int(hh["shape"])))
						co += " VEZI v %s %s" % [c4.name, ("[%s @ %s]" % [(own4 as CollisionShape3D).shape.get_class(), (own4 as Node3D).global_position]) if own4 is CollisionShape3D else ""]
					var pad := "" if pp.y > -50.0 else ", PROPAD od (%.1f, %.1f, %.1f) mrizka %.1f" % [na_zemi.x, na_zemi.y, na_zemi.z, sv._vyska(na_zemi.x, na_zemi.z)]
					return [false, "ZASEKL u (%.0f, %.1f, %.0f), usek %d, ujito %.0f m, v ceste:%s%s" % [pp.x, pp.y, pp.z, j, ujito, co if co != "" else " nic (svah?)", pad]]
	player.move_input = Vector2.ZERO
	return [true, "OK %.0f m" % ujito]


func _pamet() -> void:
	sv.kolize_vse(false)                        # jako ve hre: kolize jen v okoli hrace
	sv.rostliny_vse(false)
	for b: Vector2i in sv._rost_uzly.keys():     # testy predtim postavily vse: zpet na stav hry
		for m: Node in sv._rost_uzly[b]:
			m.queue_free()
	sv._rost_uzly.clear()
	var louka: Node = main.get_node_or_null("Louka")
	var trasa := [Vector2(2.5, 40.0), Vector2(-95.0, 225.0), Vector2(-51.3, 935.0), Vector2(-197.2, 558.6), Vector2(2.5, 40.0)]
	await main.fast_travel(Vector3(2.5, 0.0, 40.0), Vector3(0.0, 4.5, 15.0), 0.0, "test")
	player.set_flying(true)
	# PC bez GPU kresli snimek ~2 s: kresleni vypnout (buffery se alokuji i tak, cas procesu se meri zvlast);
	# chuze 6 m/s v realnem case (vlakna louky stavi bunky jako na tabletu)
	# TVRZ_PAMET_KRESLI=1: s kreslenim (unik v ovladaci grafiky?), krok 1,5 m za snimek misto realneho casu
	var kresli := OS.has_environment("TVRZ_PAMET_KRESLI")
	RenderingServer.render_loop_enabled = kresli
	if kresli:
		get_viewport().scaling_3d_scale = 0.25
	var snimek := 0
	var useky: Array = []
	var delka := 0.0
	for i in trasa.size() - 1:
		delka += (trasa[i] as Vector2).distance_to(trasa[i + 1])
	var t0 := Time.get_ticks_msec()
	var body: Array = []                         # [s, ram, buffery, bunky, proces max ms]
	var max_proc := 0.0
	var max_10 := 0.0
	var max_bunek := 0
	var dalsi := 10.0
	while true:
		var t := (Time.get_ticks_msec() - t0) / 1000.0
		if kresli:
			t = snimek * 0.25                       # 6 m/s po 1,5 m za snimek
			snimek += 1
		var s := t * 6.0
		if s >= delka:
			break
		var i := 0
		while s > (trasa[i] as Vector2).distance_to(trasa[i + 1]):
			s -= (trasa[i] as Vector2).distance_to(trasa[i + 1])
			i += 1
		var a: Vector2 = trasa[i]
		var b: Vector2 = trasa[i + 1]
		var p := a + (b - a).normalized() * s
		player.global_position = Vector3(p.x, main._ground_hi(p.x, p.y) + 1.7, p.y)
		player.velocity = Vector3.ZERO
		player.yaw = atan2(-(b - a).x, -(b - a).y)
		var tf := Time.get_ticks_usec()
		await get_tree().process_frame
		var pr := (Time.get_ticks_usec() - tf) / 1000.0     # cely snimek (kresleni vypnute) - monitor TIME_PROCESS se obnovuje jen obcas
		max_10 = maxf(max_10, pr)
		if pr > 40.0 and t > 5.0 and OS.has_environment("TVRZ_LOUKA_CAS"):
			print("PAMET spicka %.0f ms v %.1f s u %d,%d (bunek %d, ceka %d)" % [pr, t, p.x, p.y, louka._bunky.size() if louka else 0,
					louka._ceka.size() if louka else 0])
		if t > 5.0:
			max_proc = maxf(max_proc, pr)
		if louka:
			max_bunek = maxi(max_bunek, louka._bunky.size())
		if t >= dalsi:
			dalsi += 10.0
			body.append([int(t), main.diag.ram_mb(), Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0,
					louka._bunky.size() if louka else 0, max_10])
			print("PAMET %3d s  ram %4d MB  buffery %4d MB  bunek %d  proces max %.0f ms" % body[-1]
					+ "  | halda %d MB  objekty %d  zdroje %d  sirotci %d  uzly %d" % [OS.get_static_memory_usage() / 1048576,
					Performance.get_monitor(Performance.OBJECT_COUNT), Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT),
					Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT), Performance.get_monitor(Performance.OBJECT_NODE_COUNT)])
			max_10 = 0.0
	player.set_flying(false)
	RenderingServer.render_loop_enabled = true
	var r30: float = body[2][1] if body.size() > 2 else 0.0
	var b30: float = body[2][2] if body.size() > 2 else 0.0
	var rmax := 0.0
	var bmax := 0.0
	for v: Array in body.slice(3):
		rmax = maxf(rmax, v[1])
		bmax = maxf(bmax, v[2])
	var ok: bool = body.size() > 3 and rmax <= r30 * 1.15 and bmax <= b30 * 1.15 + 10.0 and max_proc <= 40.0 and max_bunek <= int(louka.STROP if louka else 0)
	_vysledek("pamet", ok, "%d m za %d s: ram 30 s %d -> max %d MB, buffery %d -> max %d MB, proces max %.0f ms, bunek max %d" % [delka,
			(Time.get_ticks_msec() - t0) / 1000, r30, rmax, b30, bmax, max_proc, max_bunek])


## Sekani pri chuzi (0.62 bod 8): skripty s _process vola test sam a meri kazdy zvlast (uzly maji process vypnuty);
## kresleni CPU z mereni viewportu, zbytek = engine (fyzika, odlozena volani, GPU/swap).
func _sekani() -> void:
	var trasa := [Vector2(2.5, 40.0), Vector2(-20.0, 50.0), Vector2(-80.0, 180.0), Vector2(-112.0, 290.0), Vector2(-150.0, 420.0),
			Vector2(-190.0, 540.0)]
	await main.fast_travel(Vector3(2.5, 0.0, 40.0), Vector3(0.0, 4.5, 15.0), 0.0, "test")
	player.set_flying(true)
	for i in 30:
		await get_tree().process_frame
	var vp_rid := get_viewport().get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(vp_rid, true)
	var delka := 0.0
	for i in trasa.size() - 1:
		delka += (trasa[i] as Vector2).distance_to(trasa[i + 1])
	var uzly: Array = []
	var hledej := func() -> void:
		for n: Node in get_tree().root.find_children("*", "", true, false):
			if n != self and n.is_processing() and n.get_script() != null and n.has_method("_process") \
					and n.process_mode != Node.PROCESS_MODE_DISABLED:
				n.set_process(false)
				if not uzly.has(n):
					uzly.append(n)
	var t0 := Time.get_ticks_msec()
	var t_hl := -1.0
	var skr_max := 0.0
	var orez_max := 0.0
	# PC bez GPU (llvmpipe): snimek kresli ~1 s, vypisuji jen snimky se spickou skriptu nebo orezu > 5 ms
	var llvmpipe := RenderingServer.get_video_adapter_name().to_lower().contains("llvmpipe")
	var casy: Array = []
	var spicky: Array = []
	var nejhorsi := {}             # uzel -> max ms
	var predchozi := Time.get_ticks_usec()
	while true:
		var t := (Time.get_ticks_msec() - t0) / 1000.0
		var s := t * 6.0
		if s >= delka:
			break
		if t - t_hl > 1.0:
			t_hl = t
			hledej.call()
		var i := 0
		while s > (trasa[i] as Vector2).distance_to(trasa[i + 1]):
			s -= (trasa[i] as Vector2).distance_to(trasa[i + 1])
			i += 1
		var a: Vector2 = trasa[i]
		var b: Vector2 = trasa[i + 1]
		var p := a + (b - a).normalized() * s
		player.global_position = Vector3(p.x, main._ground_hi(p.x, p.y) + 1.7, p.y)
		player.velocity = Vector3.ZERO
		player.yaw = atan2(-(b - a).x, -(b - a).y)
		# skripty tohoto snimku (process_frame se vysila pred _process uzlu)
		var dt := get_process_delta_time()
		var rozpad: Array = []
		var skripty := 0.0
		for n: Node in uzly:
			if not is_instance_valid(n) or not n.is_inside_tree():
				continue
			var u0 := Time.get_ticks_usec()
			n.call("_process", dt)
			var ms := (Time.get_ticks_usec() - u0) / 1000.0
			skripty += ms
			var nm := String(n.name)
			nejhorsi[nm] = maxf(float(nejhorsi.get(nm, 0.0)), ms)
			if ms >= 1.0:
				rozpad.append("%s %.1f" % [nm, ms])
		await get_tree().process_frame
		var ted := Time.get_ticks_usec()
		var cely := (ted - predchozi) / 1000.0
		predchozi = ted
		var orez := RenderingServer.get_frame_setup_time_cpu()          # orezani, visibility_range, priprava
		var kresli := RenderingServer.viewport_get_measured_render_time_cpu(vp_rid)
		if t > 5.0:
			casy.append(cely)
			skr_max = maxf(skr_max, skripty)
			orez_max = maxf(orez_max, orez)
			var radek := "%.0f ms v %.1f s u %d,%d: skripty %.1f (%s), orez %.1f, kresleni cpu %.1f, zbytek %.1f" % [cely, t,
					p.x, p.y, skripty, ", ".join(rozpad), orez, kresli, cely - skripty - kresli - orez]
			if OS.has_environment("TVRZ_SEKANI_VSE"):
				print("SEKANI_SN ", radek)
			if cely > 30.0 and (skripty > 5.0 or orez > 5.0 or not llvmpipe):
				spicky.append(radek)
	for n: Node in uzly:
		if is_instance_valid(n):
			n.set_process(true)
	RenderingServer.viewport_set_measure_render_time(vp_rid, false)
	player.set_flying(false)
	casy.sort()
	var prumer := 0.0
	for c: float in casy:
		prumer += c
	prumer /= maxf(1.0, casy.size())
	var mx: float = casy[-1] if not casy.is_empty() else 0.0
	var p99: float = casy[int(casy.size() * 0.99)] if not casy.is_empty() else 0.0
	for sp: String in spicky:
		print("SEKANI ", sp)
	var nh: Array = nejhorsi.keys()
	nh.sort_custom(func(x: String, y: String) -> bool: return nejhorsi[x] > nejhorsi[y])
	var nhs := ""
	for k: String in nh.slice(0, 8):
		nhs += " %s %.1f" % [k, nejhorsi[k]]
	print("SEKANI skripty max ms:", nhs)
	# llvmpipe: snimek meri kresleni na CPU (~1 s) - kriterium jen CPU hlavniho vlakna (skripty <= 5 ms, orez <= 5 ms)
	var ok := (skr_max <= 5.0 and orez_max <= 5.0) if llvmpipe else mx <= 40.0
	_vysledek("sekani", ok, "%d m, %d snimku%s: prumer %.1f ms, 99 %% %.1f ms, max %.1f ms (max/prumer %.1f), skripty max %.1f ms, orez max %.1f ms, spicek %d" % [
			delka, casy.size(), " (llvmpipe)" if llvmpipe else "", prumer, p99, mx, mx / maxf(0.01, prumer), skr_max, orez_max, spicky.size()])


## Stani na miste s kreslenim (0.59c: na tabletu RAM +4 MB/s bez pohybu): kvalita 1 jako tablet, halda Godotu
## po 50 snimcich - unik za snimek v Godotu (ne v ovladaci) se ukaze i na PC.
func _stuj() -> void:
	main.quality = 1
	main.apply_quality()
	await main.fast_travel(Vector3(2.5, 0.0, 40.0), Vector3(0.0, 4.5, 15.0), 0.0, "test")
	var h0 := 0
	for k in int(OS.get_environment("TVRZ_STUJ_KOL")) if OS.has_environment("TVRZ_STUJ_KOL") else 9:
		for f in 50:
			await get_tree().process_frame
		var h := OS.get_static_memory_usage() / 1048576
		if k == 0:
			h0 = h
		var lk: Node = main.get_node_or_null("Louka")
		print("STUJ %3d snimku  halda %d MB  ram %d MB  objekty %d  zdroje %d  postaveno bunek %d kup %d" % [(k + 1) * 50, h, main.diag.ram_mb(),
				Performance.get_monitor(Performance.OBJECT_COUNT), Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT),
				lk.postaveno if lk else -1, lk.postaveno_kupy if lk else -1])
	var h1 := OS.get_static_memory_usage() / 1048576
	_vysledek("stuj", h1 - h0 < 20, "halda za 400 snimku %+d MB" % (h1 - h0))


## Automaticky test pameti z nastaveni (0.59e) - doběhne vsech 9 kroku bez chyby a vse vrati.
func _autotest() -> void:
	await main.fast_travel(Vector3(2.5, 0.0, 40.0), Vector3(0.0, 4.5, 15.0), 0.0, "test")
	main._on_menu_action("set:test_pameti", null)
	while main._test_auto:
		await get_tree().create_timer(5.0).timeout
	var lk: Node = main.get_node_or_null("Louka")
	_vysledek("autotest", main.test_vysledky.size() == main.TEST_PAMETI.size() and lk.is_processing() and not get_viewport().disable_3d,
			"kroky " + "  ".join(main.test_vysledky))


## Ladici vypis bodu (TVRZ_BODY="x,z;x,z"): co o miste vi louka a svet (proc tam neroste trava).
## Misa 0.67 (reka (237,1015) (240,1031) (293,1119) (270,1204)): "koryto komplet zkontrolovat" (radce 08:55).
## Podel osy toku kazde 2 m na obou stranach: bod 1 m za krajem vody musi byt 0,1-1,0 m nad hladinou (ne pod ni =
## voda nad terenem, ne sraz), bod 0,5 m pred krajem pod hladinou. Teren = paprsek shora na kolize terenu.
func _breh() -> void:
	var kr = sv.koryto
	if kr == null:
		_vysledek("breh", false, "bez koryta")
		return
	var sp := player.get_world_3d().direct_space_state
	var vse := 0
	var nad := 0
	var pod := 0
	var sraz := 0
	var sucho := 0
	var priklady: Array = []
	for k in kr.body.size() - 1:
		var a: Vector2 = kr.body[k]
		var b: Vector2 = kr.body[k + 1]
		var dl := a.distance_to(b)
		var nrm := (b - a).normalized().orthogonal()
		var t := 0.0
		while t < dl:
			var o := a.lerp(b, t / dl)
			var w: float = lerpf(kr.sirky[k], kr.sirky[k + 1], t / dl)
			var hl: float = lerpf(kr.hladiny[k], kr.hladiny[k + 1], t / dl)
			if not Rect2(-245.0, -245.0, 1140.0, 1590.0).has_point(o):     # potok za jemnym terenem (Teren_obzor)
				t += 2.0
				continue
			for sg: float in [1.0, -1.0]:
				var q := o + nrm * sg * (w + 1.0)
				var q2 := o + nrm * sg * maxf(w - 0.5, 0.0)
				var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(q.x, hl + 40.0, q.y), Vector3(q.x, hl - 20.0, q.y)))
				var h2 := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(q2.x, hl + 40.0, q2.y), Vector3(q2.x, hl - 20.0, q2.y)))
				if h.is_empty() or h2.is_empty():
					continue
				# jen teren (ne kamen, kmen, skala nad vodou); u mostu breh dela najezd (pod mostovkou)
				if not String((h["collider"] as Node).name).begins_with("Teren") or not String((h2["collider"] as Node).name).begins_with("Teren") \
						or q.distance_to(Vector2(232.0, 598.0)) < 18.0:
					continue
				vse += 1
				var dy: float = (h["position"] as Vector3).y - hl
				var dy2: float = (h2["position"] as Vector3).y - hl
				if dy < -0.03:                       # breh pod hladinou (mezi vrcholy site +-3 cm)
					pod += 1
					if priklady.size() < 12:
						priklady.append("%.0f,%.0f breh %+.2f" % [q.x, q.y, dy])
				elif dy > 1.0:
					sraz += 1
				else:
					nad += 1
				if dy2 > 0.0:
					sucho += 1
					if priklady.size() < 12:
						priklady.append("%.0f,%.0f dno %+.2f" % [q2.x, q2.y, dy2])
			t += 2.0
	# hladina potoka (Potok, reka.res): vrchol dal nez 0,8 m za krajem vody nad terenem = voda na trave
	var na_trave := 0
	var vrch := 0
	var pot: MeshInstance3D = main.find_child("Potok", true, false)
	if pot:
		var f := pot.mesh.get_faces()
		for i in range(0, f.size(), 7):
			var wv := pot.global_transform * f[i]
			var bl: Array = kr.blizko(wv.x, wv.z)
			if bl.is_empty() or float(bl[0]) < float(bl[2]) + 0.8 or Vector2(wv.x, wv.z).distance_to(Vector2(232.0, 598.0)) < 18.0:
				continue
			vrch += 1
			var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(wv + Vector3(0, 3.0, 0), wv - Vector3(0, 5.0, 0)))
			if not h.is_empty() and (h["position"] as Vector3).y < wv.y - 0.05:
				na_trave += 1
				if priklady.size() < 16:
					priklady.append("%.0f,%.0f voda na trave %.2f" % [wv.x, wv.z, wv.y - (h["position"] as Vector3).y])
	var ok := vse > 0 and pod < vse * 0.03 and sucho < vse * 0.02 and na_trave < 20
	_vysledek("breh", ok, "%d bodu: breh 0,1-1 m nad hladinou %d, pod hladinou %d, sraz %d, dno nad vodou %d; voda za brehem nad terenem %d z %d | %s" % [vse, nad, pod, sraz,
			sucho, na_trave, vrch, ", ".join(priklady)])


## Misa 0.69 / radce 12:40: svetla jako predmety (svicny, louce, kandelabr) - vecer a v noci hori sama (auto), ve dne ne,
## rucne zhasnute zustane; svicen s vencem jde zapalit; hostinec: louce v mistnostech bez vlastniho svetla.
func _svetla() -> void:
	var pr: Node = main.predmety
	var p0 := Vector3(-2.0, pr.ground_y(-2.0, 4.0), 4.0)
	pr.spawn({"id": "svicen_venec", "p": p0, "yaw": 0.0, "obsah": {}})
	var venec: Dictionary = pr.placed[-1]
	pr.use2({"kind": "predmet", "rec": venec})
	var venec_ok := bool(venec.get("hori", false))
	main.day.set_time("noc", 0.01)
	for _fa in 30:
		await get_tree().process_frame
	var auto_n := 0
	var noc := 0
	var hos := 0
	for rec: Dictionary in pr.placed:
		if bool(rec.get("auto", false)):
			auto_n += 1
			noc += int(bool(rec.get("hori", false)))
		if rec["id"] == "drzak_louce" and Vector2(float(rec["p"].x), float(rec["p"].z)).distance_to(Vector2(-66.4, 927.0)) < 15.0:
			hos += 1
	main.day.set_time("poledne", 0.01)
	for _fb in 30:
		await get_tree().process_frame
	var den := 0
	for rec: Dictionary in pr.placed:
		if bool(rec.get("auto", false)):
			den += int(bool(rec.get("hori", false)))
	pr.remove(venec)
	var ok := auto_n > 10 and noc == auto_n and den == 0 and venec_ok and hos >= 3
	_vysledek("svetla", ok, "samo svitici %d: v noci hori %d, ve dne %d; svicen s vencem zapalen %s; hostinec louci navic %d" % [
			auto_n, noc, den, venec_ok, hos])


## Radce 17:05 bod 1: zadna karta travy nelezi - kazda plocha site louky (trs, drn, vysoka, vejir, kupa, kvety)
## max 50 st. od svislice (normala y < 0,77).
func _nizka_trava() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	var spatne := 0
	var vse := 0
	var co := []
	for nm: String in ["_trs", "_drn", "_vysoka", "_vejir", "_kupa"]:
		var m: Mesh = louka.get(nm)
		if m == null:
			continue
		var f := m.get_faces()
		var n0 := 0
		for i in range(0, f.size(), 3):
			var n := (f[i + 1] - f[i]).cross(f[i + 2] - f[i]).normalized()
			vse += 1
			if absf(n.y) > 0.77:
				n0 += 1
		if n0 > 0:
			co.append("%s %d" % [nm, n0])
		spatne += n0
	# radce 21:35: na louce jen stojici trsy (vrstvy 0, 1, 3); drn (2) a vejir (4) shora jako hvezdice - vyrazene
	var vyp: Array = louka.get("_vypnute")
	var ok_v := vyp.has(2) and vyp.has(4)
	_vysledek("nizka_trava", spatne == 0 and vse > 0 and ok_v, "%d ploch, lezicich %d %s; vyrazene vrstvy %s (drn+vejir: %s)" % [vse, spatne, str(co), str(vyp), ok_v])


## Radce 17:05 bod 4: v pudorysu hostince a dalsich statickych staveb zadna trava (vzorek louky = 0).
func _interier() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	var spatne := 0
	var vse := 0
	for st: Array in sv._uvnitr:
		var inv: Transform3D = st[0]
		var b: AABB = st[1]
		var xf := inv.affine_inverse()
		for i in 12:
			for j in 12:
				var q := xf * Vector3(lerpf(b.position.x + 0.3, b.end.x - 0.3, i / 11.0), 0.0, lerpf(b.position.z + 0.3, b.end.z - 0.3, j / 11.0))
				vse += 1
				if (louka._vzorek(q.x, q.z) as Vector3).x > 0.0:
					spatne += 1
	# tvrz: vstup do veze, kovarna, zbrojnice, prujezd (Misa 0.70)
	for b: Vector2 in [Vector2(-23.0, -13.0), Vector2(-24.0, -11.0), Vector2(-12.0, 8.5), Vector2(-17.0, 11.5), Vector2(-10.0, 11.0), Vector2(-1.6, 12.0)]:
		vse += 1
		if (louka._vzorek(b.x, b.y) as Vector3).x > 0.0:
			spatne += 1
			print("INTERIER trava v %.0f,%.0f" % [b.x, b.y])
	_vysledek("interier", vse > 0 and spatne == 0, "staveb %d, bodu %d, s travou %d" % [sv._uvnitr.size(), vse, spatne])


## Radce 17:05 bod 3: bríza - zadna plocha kmene (pod korunou) neni v materialu listi.
func _briza() -> void:
	var lim := float(sv.pasma()["test"]["listi_nad_zemi_m"])
	var spatne := 0
	var n := 0
	for k in sv._briza_kmeny:
		var m: Mesh = sv._briza_kmeny[k]
		n += 1
		var y0 := INF
		var kura := false
		for si in m.get_surface_count():
			for q: Vector3 in m.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
				y0 = minf(y0, q.y)
			var mt := m.surface_get_material(si)
			kura = kura or (mt != null and String(mt.resource_name).contains("kura"))
		for si in m.get_surface_count():
			var mt := m.surface_get_material(si)
			if mt != null and String(mt.resource_name).contains("kura"):
				continue
			var nizko := 0
			for q: Vector3 in m.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
				if q.y - y0 < lim:
					nizko += 1
			if nizko > 0:
				spatne += 1
				print("BRIZA listi_u_zeme (0, 0) varianta %d povrch %d: %d vrcholu pod %.1f m" % [n, si, nizko, lim])
		if not kura and m.get_surface_count() < 3:
			spatne += 1
	_vysledek("briza", n >= 4 and spatne == 0, "variant %d, spatnych povrchu %d" % [n, spatne])


## Radce 17:05 bod 7: na cestach a dvorech ve vsi zadny ker, kamen ani bylina (multimeshe rostlin, i bunky okoli).
func _cesty_volne() -> void:
	var spatne := 0
	var pr: Array = []
	for mmi in main.find_children("*", "MultiMeshInstance3D", true, false):
		var nm := String(mmi.name)
		if not (nm.begins_with("ker_") or nm.begins_with("shrub") or nm.begins_with("sipek") or nm.begins_with("bez_") \
				or nm.begins_with("kamen") or nm.begins_with("balvan") or nm.begins_with("nettle") or nm.begins_with("dandelion")):
			continue
		var mm := (mmi as MultiMeshInstance3D).multimesh
		for i in mm.instance_count:
			var o := (mmi as Node3D).global_transform * mm.get_instance_transform(i).origin
			if o.x > 350.0 and o.x < 590.0 and o.z > 710.0 and o.z < 950.0 and sv.ves_cesta(o.x, o.z):
				spatne += 1
				if pr.size() < 6:
					pr.append("%s %.0f,%.0f" % [nm.get_slice("_", 0), o.x, o.z])
	_vysledek("cesty_volne", spatne == 0, "na cestach ve vsi %d %s" % [spatne, str(pr)])


## Radce 17:05 bod 2 / 12:40 (Misa: "nemuzu povesit tapiserii na prostredni zed dole v palaci", (11,-12)): v palaci
## (prizemi a patro) paprsky ze stredu mistnosti na kazdou zed po 0,5 m ve vyskach 1,0-2,4 m; zed musi mit kolizi
## (svisla normala) do 0,25 m od sve viditelne polohy. Vypise mista, kde paprsek proleti nebo trefi neco jineho.
func _steny() -> void:
	var sp := player.get_world_3d().direct_space_state
	# [osa, poloha zdi, od, do (druha souradnice), stred mistnosti druhe osy, smer, y0 podlahy]
	var zdi := [["z", -14.0, 3.6, 16.6, -10.8, -1.0, 0.0], ["z", -7.6, 3.6, 16.6, -10.8, 1.0, 0.0], ["x", 17.0, -13.6, -8.0, 10.0, 1.0, 0.0],
			["x", 3.2, -13.6, -8.0, 10.0, -1.0, 0.0], ["z", -14.0, -2.0, 2.6, -10.8, -1.0, 0.0], ["x", -2.4, -13.6, -8.0, 0.3, -1.0, 0.0],
			["z", -14.0, -2.0, 16.6, -10.8, -1.0, 3.9], ["z", -7.6, -2.0, 16.6, -10.8, 1.0, 3.9]]
	var vse := 0
	var spatne := 0
	var pr: Array = []
	for zd: Array in zdi:
		var u := float(zd[2])
		while u <= float(zd[3]):
			for hy: float in [1.0, 1.6, 2.2]:
				var y := float(zd[6]) + hy
				var a: Vector3
				var b: Vector3
				if zd[0] == "z":
					a = Vector3(u, y, float(zd[4]))
					b = Vector3(u, y, float(zd[1]) + float(zd[5]) * 1.5)
				else:
					a = Vector3(float(zd[4]), y, u)
					b = Vector3(float(zd[1]) + float(zd[5]) * 1.5, y, u)
				if _otvor_palace(zd, u, y):
					continue
				var q := PhysicsRayQueryParameters3D.create(a, b)
				q.exclude = [player.get_rid()]
				var h := sp.intersect_ray(q)
				vse += 1
				var ok := false
				var co := "nic"
				if not h.is_empty():
					var hp: Vector3 = h["position"]
					var d := absf((hp.z if zd[0] == "z" else hp.x) - float(zd[1]))
					ok = d < 0.25 and absf((h["normal"] as Vector3).y) < 0.35
					co = "%s d %.2f" % [(h["collider"] as Node).name, d]
				if not ok:
					spatne += 1
					if hy == 1.6:
						pr.append("%s=%.1f/%.0f u %.1f: %s" % [zd[0], zd[1], zd[6], u, co])
			u += 0.5
	# vnejsi zdi vezi z nadvori (Misa 0.70: "venkovni zed veze u dveri - nelze umistit louc"): SZ vez z vychodu
	# (x -20,55 +- 0,6) a z jihu, vez brany zevnitr; aspon 85 % paprsku ve 1,6 m trefi svislou zed do 8 m
	var vez_ok := 0
	var vez_n := 0
	for zz in range(-16, -8):
		for yy: float in [1.4, 2.0]:
			var q2 := PhysicsRayQueryParameters3D.create(Vector3(-13.0, yy, zz + 0.5), Vector3(-22.0, yy, zz + 0.5))
			q2.exclude = [player.get_rid()]
			var h2 := sp.intersect_ray(q2)
			vez_n += 1
			if not h2.is_empty() and absf((h2["normal"] as Vector3).y) < 0.35:
				vez_ok += 1
	_vysledek("steny", spatne == 0 and vez_ok >= vez_n * 0.85, "%d paprsku, bez zdi %d; vez z nadvori %d/%d | %s" % [vse, spatne, vez_ok, vez_n, " ; ".join(pr)])


## Otvory palace (blender/palace.py): okna, dvere, vyklenky severni zdi, krb - tam zed byt nema.
func _otvor_palace(zd: Array, u: float, y: float) -> bool:
	var F1 := 3.9
	if zd[0] == "z" and float(zd[1]) == -14.0:
		for w: Array in [[5.7, 6.3, false], [9.7, 10.3, false], [13.7, 14.3, false], [1.6, 2.4, true], [11.6, 12.4, true]]:
			var c := (float(w[0]) + float(w[1])) * 0.5
			var hw := 0.78 if w[2] else 0.72
			if (y > F1) == bool(w[2]) and absf(u - c) < hw + 0.25:
				return true
	if zd[0] == "z" and float(zd[1]) == -7.6:
		for w: Array in [[4.5, 5.5], [11.0, 12.0], [14.0, 15.0], [7.2, 9.0], [0.6, 2.0], [10.2, 11.4], [6.6, 7.4], [13.6, 14.4]]:
			if u > float(w[0]) - 0.25 and u < float(w[1]) + 0.25:
				return true
	if zd[0] == "x" and (float(zd[1]) == 3.2 or float(zd[1]) == -2.4) and u > -11.6 and u < -9.8:
		return true                                     # dvere v pricce a do sine
	if zd[0] == "x" and float(zd[1]) == 17.0 and y < F1 and u > -12.8 and u < -7.6:
		return true                                     # krb a dvere ve vychodni zdi
	return false


## Radce 17:05 bod 5: rybnik ve vsi (512,871) - hladina (oblast vody) nad dnem 0,3-1,8 m uprostred, kruh bodu
## po obvodu na 70 % polomeru je voda.
func _rybnik_ves() -> void:
	var sp := player.get_world_3d().direct_space_state
	var ok := true
	var co: Array = []
	var n := 0
	var stredy: Array = []
	for nd2: Dictionary in sv.nadrz.nadrze:
		if not (nd2["kruh"] as Array).is_empty():
			stredy.append(nd2["kruh"][0])
	if sv._ryb_y != INF:
		stredy.append(sv.RYB_C)                     # dil rybnik_lhota (NAVOD): hladina z modelu, kolize -col
	for c: Vector2 in stredy:
		n += 1
		var r0 := 7.0
		var voda := 0
		var hl: Array = []
		for k in 9:
			var p := c if k == 0 else c + Vector2.from_angle(TAU * k / 8.0) * r0 * 0.6
			var qv := PhysicsRayQueryParameters3D.create(Vector3(p.x, 60, p.y), Vector3(p.x, -60, p.y), sv.VRSTVA_VODA)
			qv.collide_with_areas = true
			qv.collide_with_bodies = false
			var hv := sp.intersect_ray(qv)
			var ht := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(p.x, 60, p.y), Vector3(p.x, -60, p.y)))
			if not hv.is_empty() and not ht.is_empty():
				var dh: float = (hv["position"] as Vector3).y - (ht["position"] as Vector3).y
				hl.append(snappedf(dh, 0.01))
				if dh > 0.1:
					voda += 1
		var stred_ok: bool = not hl.is_empty() and float(hl[0]) > 0.3
		ok = ok and stred_ok and voda >= 7
		co.append("%.0f,%.0f: voda %d/9 hloubky %s" % [c.x, c.y, voda, str(hl)])
	var rh: Node3D = main.find_child("Rybnik_hladina", true, false)
	if rh:
		print("RYBNIK uzel %s aabb %s deti %s vis %s" % [rh.get_path(), (rh as MeshInstance3D).global_transform * (rh as MeshInstance3D).get_aabb(), rh.get_children(), rh.is_visible_in_tree()])
	else:
		print("RYBNIK uzel nenalezen")
	_vysledek("rybnik_ves", ok and n > 0, "malych nadrzi %d | %s" % [n, " ; ".join(co)])


## Radce 17:05 bod 6 (Misa 0.70 "vratka ve vzduchu"): spodek kridla branky / vrat ve vsi 0-0,25 m nad zemi
## (paprsek jen na teren Teren*), a kuly branky stoji na zemi.
func _vratka() -> void:
	var sp := player.get_world_3d().direct_space_state
	var pr: Array = []
	var spatne := 0
	var n := 0
	for nd in main.find_children("Pohyb_ves_*", "Node3D", true, false):
		var g := nd as Node3D
		if String(g.name).contains("dvere"):
			continue                                    # dvere chalup jsou na podezdivce (prah)
		var bb := AABB()
		var prv := true
		for mi in [g] + g.find_children("*", "MeshInstance3D", true, false):
			if not (mi is MeshInstance3D):
				continue
			var b := (mi as MeshInstance3D).global_transform * (mi as MeshInstance3D).get_aabb()
			bb = b if prv else bb.merge(b)
			prv = false
		if prv:
			continue
		var c := bb.get_center()
		var y0 := INF
		for o: Vector2 in [Vector2(0, 0), Vector2(0.3, 0), Vector2(-0.3, 0), Vector2(0, 0.3), Vector2(0, -0.3)]:
			var q := PhysicsRayQueryParameters3D.create(Vector3(c.x + o.x, bb.end.y + 3.0, c.z + o.y), Vector3(c.x + o.x, bb.position.y - 6.0, c.z + o.y))
			for _k in 4:
				var h := sp.intersect_ray(q)
				if h.is_empty():
					break
				if String((h["collider"] as Node).name).begins_with("Teren"):
					y0 = minf(y0, (h["position"] as Vector3).y)
					break
				q.exclude = q.exclude + [h["rid"]]
		n += 1
		var dy := bb.position.y - y0
		pr.append("%s %+.2f" % [String(g.name).trim_prefix("Pohyb_ves_"), dy])
		if y0 == INF or dy > 0.25 or dy < -0.1:
			spatne += 1
	_vysledek("vratka", n > 0 and spatne == 0, "kridel %d, spatne %d | %s" % [n, spatne, ", ".join(pr)])


## Radce 20:00 - tri testy pameti (halda Godotu OS.get_static_memory_usage + rezidentni pamet procesu).
func _mem() -> Vector2:
	var rss := 0.0
	var f := FileAccess.open("/proc/self/statm", FileAccess.READ)
	if f:
		rss = float(f.get_line().split(" ")[1]) * 4096.0 / 1048576.0
	return Vector2(OS.get_static_memory_usage() / 1048576.0, rss)


func _jako_hra() -> void:
	sv.kolize_vse(false)
	sv.rostliny_vse(false)
	for b: Vector2i in sv._rost_uzly.keys():
		for m: Node in sv._rost_uzly[b]:
			m.queue_free()
	sv._rost_uzly.clear()


func _dobehni_fronty(louka: Node) -> int:
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 120000:
		await get_tree().process_frame
		if louka._ceka.is_empty() and louka._stavba.is_empty() and sv._kol_fronta.is_empty() and Time.get_ticks_msec() - t0 > 8000:
			break
	var ck: Array = []
	for c in louka._ceka:
		ck.append("%s hotovo %s" % [c, WorkerThreadPool.is_task_completed(louka._ceka[c])])
	print("FRONTY louka process %s snimek %d" % [louka.is_processing(), louka._snimek])
	print("FRONTY po %d ms: louka vlakna %s, hotove %d, stavba %d, kolize %d, rostliny rozestavene %s" % [Time.get_ticks_msec() - t0,
			str(ck), louka._hotove.size(), louka._stavba.size(), sv._kol_fronta.size(), str(sv._rost_rozest)])
	return Time.get_ticks_msec() - t0


## Sklon primky (MB/min) a rozpeti vzorku [[s, MB], ...].
func _sklon(v: Array) -> Vector2:
	var n := v.size()
	if n < 3:
		return Vector2.ZERO
	var sx := 0.0
	var sy := 0.0
	var sxx := 0.0
	var sxy := 0.0
	var lo := INF
	var hi := -INF
	for e: Vector2 in v:
		sx += e.x
		sy += e.y
		sxx += e.x * e.x
		sxy += e.x * e.y
		lo = minf(lo, e.y)
		hi = maxf(hi, e.y)
	return Vector2((n * sxy - sx * sy) / maxf(n * sxx - sx * sx, 1e-6) * 60.0, hi - lo)


## 1) Stani v lese po dobehnuti front (TVRZ_STANI_S, vychozi 600 s): pamet se ustali - posledni polovina sklon
## < 2 MB/min a rozpeti < 25 MB.
func _pamet_stani() -> void:
	_jako_hra()
	var louka: Node = main.get_node_or_null("Louka")
	await main.fast_travel(Vector3(-96.0, 0.0, 343.0), Vector3(-80.0, 1.6, 360.0), 0.0, "test")
	get_viewport().scaling_3d_scale = 0.25
	var fr := await _dobehni_fronty(louka)
	var dur := float(OS.get_environment("TVRZ_STANI_S")) if OS.has_environment("TVRZ_STANI_S") else 600.0
	var t0 := Time.get_ticks_msec()
	var vz: Array = []
	var dalsi := 0.0
	while true:
		var t := (Time.get_ticks_msec() - t0) / 1000.0
		if t > dur:
			break
		player.yaw += 0.003
		await get_tree().process_frame
		if t >= dalsi:
			dalsi += 10.0
			var m := _mem()
			vz.append([t, m])
			print("STANI %4.0f s  halda %.0f MB  proces %.0f MB  louka %d  rostliny %d  kolize %d" % [t, m.x, m.y, louka._bunky.size(),
					sv._rost_uzly.size(), sv._kol_uzly.size()])
	get_viewport().scaling_3d_scale = 1.0
	var h2: Array = []
	var p2: Array = []
	for e: Array in vz.slice(vz.size() / 2):
		h2.append(Vector2(e[0], (e[1] as Vector2).x))
		p2.append(Vector2(e[0], (e[1] as Vector2).y))
	var sh := _sklon(h2)
	var sp := _sklon(p2)
	_vysledek("pamet_stani", sh.x < 2.0 and sh.y < 25.0 and sp.x < 3.0, "fronty dobehly za %d ms; %d s v lese, 2. polovina: halda %+.1f MB/min (rozpeti %.0f), proces %+.1f MB/min (rozpeti %.0f); halda %.0f -> %.0f MB" % [
			fr, int(dur), sh.x, sh.y, sp.x, sp.y, (vz[0][1] as Vector2).x, (vz[-1][1] as Vector2).x])


## 2) Opakovany stejny okruh kolem prikopu (3x, 6 m/s): navrat na stejne misto nezvysuje zaklad - pamet na konci
## okruhu 3 <= okruh 1 + 3 % + 10 MB.
func _pamet_okruh() -> void:
	_jako_hra()
	var louka: Node = main.get_node_or_null("Louka")
	await main.fast_travel(Vector3(-4.0, 0.0, 45.0), Vector3(-4.0, 1.6, 0.0), 0.0, "test")
	player.set_flying(true)
	get_viewport().scaling_3d_scale = 0.25
	var zaklad: Array = []
	for kolo in 3:
		var t0 := Time.get_ticks_msec()
		while true:
			var t := (Time.get_ticks_msec() - t0) / 1000.0
			var a := t * 6.0 / 45.0
			if a > TAU:
				break
			var p := Vector2(-4.0, 0.0) + Vector2(sin(a), cos(a)) * 45.0
			player.global_position = Vector3(p.x, main.svet._vyska(p.x, p.y) + 1.7, p.y)
			player.velocity = Vector3.ZERO
			player.yaw = -a - PI * 0.5
			await get_tree().process_frame
		await _dobehni_fronty(louka)
		var m := _mem()
		zaklad.append(m)
		print("OKRUH %d: halda %.0f MB proces %.0f MB" % [kolo + 1, m.x, m.y])
	player.set_flying(false)
	get_viewport().scaling_3d_scale = 1.0
	var ok: bool = (zaklad[2] as Vector2).x <= (zaklad[0] as Vector2).x * 1.03 + 10.0
	_vysledek("pamet_okruh", ok, "halda po okruzich %s MB, proces %s MB" % [str(zaklad.map(func(v: Vector2) -> int: return int(v.x))),
			str(zaklad.map(func(v: Vector2) -> int: return int(v.y)))])


## 3) Stani s pozastavenym generovanim (louka, rostliny a kolize okoli stoji): pamet nesmi rust (sklon < 1 MB/min).
func _pamet_pauza() -> void:
	_jako_hra()
	var louka: Node = main.get_node_or_null("Louka")
	await main.fast_travel(Vector3(470.0, 0.0, 830.0), Vector3(480.0, 1.6, 830.0), 0.0, "test")
	await _dobehni_fronty(louka)
	louka.set_process(false)
	sv.rost_vse = true
	sv.kol_vse = true
	var dur := float(OS.get_environment("TVRZ_PAUZA_S")) if OS.has_environment("TVRZ_PAUZA_S") else 180.0
	var t0 := Time.get_ticks_msec()
	var vz: Array = []
	var dalsi := 0.0
	while (Time.get_ticks_msec() - t0) / 1000.0 < dur:
		await get_tree().process_frame
		var t := (Time.get_ticks_msec() - t0) / 1000.0
		if t >= dalsi:
			dalsi += 10.0
			vz.append(Vector2(t, _mem().x))
	louka.set_process(true)
	sv.rost_vse = false
	sv.kol_vse = false
	var sk := _sklon(vz)
	_vysledek("pamet_pauza", sk.x < 1.0, "%d s bez generovani: halda %+.2f MB/min, rozpeti %.1f MB" % [int(dur), sk.x, sk.y])


func _bod() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	for b: String in OS.get_environment("TVRZ_BODY").split(";", false):
		var xz := b.split(",")
		var x := float(xz[0])
		var z := float(xz[1])
		var c := Vector2i(floori(x / 32.0), floori(z / 32.0))
		var kr: PackedByteArray = sv.kryti_tab.get(c, PackedByteArray())
		var kh: int = louka._kryti_hodnota(kr, c, x, z) if louka and not kr.is_empty() else -1
		var v: Vector3 = louka._vzorek(x, z) if louka else Vector3.ZERO
		var cl: Array = sv.cesta_lat(x, z)
		print("BOD %.1f,%.1f cesta %s trava %s" % [x, z, str(cl), sv.cesta_trava(x, z)])
		# Misa 0.80: co lezi pod/nad cestou - vsechny site s trojuhelnikem nad bodem a jejich vyska
		for n in main.find_children("*", "MeshInstance3D", true, false):
			var mi := n as MeshInstance3D
			if mi.mesh == null or not mi.is_visible_in_tree():
				continue
			var ab := mi.global_transform * mi.mesh.get_aabb()
			if x < ab.position.x or x > ab.end.x or z < ab.position.z or z > ab.end.z or ab.size.y > 400.0:
				continue
			# materialy povrchu s trojuhelnikem nad bodem (Misa 0.83: hneda krabice ve vsi - jaky material)
			var mats := []
			for si in mi.mesh.get_surface_count():
				var sa := mi.mesh.surface_get_arrays(si)
				var sv2: PackedVector3Array = sa[Mesh.ARRAY_VERTEX]
				var sx: PackedInt32Array = sa[Mesh.ARRAY_INDEX] if sa[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
				for t in sx.size() / 3:
					var c0 := mi.global_transform * ((sv2[sx[t * 3]] + sv2[sx[t * 3 + 1]] + sv2[sx[t * 3 + 2]]) / 3.0)
					if Vector2(c0.x - x, c0.z - z).length() < 1.5:
						var mt := mi.get_active_material(si)
						var mn := String(mt.resource_name) if mt else "?"
						if mi.mesh is ArrayMesh:
							mn += "/" + String((mi.mesh as ArrayMesh).surface_get_name(si))
						if mt is ShaderMaterial:
							mn += " sh=" + String((mt as ShaderMaterial).shader.resource_path.get_file())
						if mt is BaseMaterial3D:
							mn += " tex=%s" % ((mt as BaseMaterial3D).albedo_texture != null)
						mats.append(mn)
						break
			if not mats.is_empty() and mi.name == "Vesnice":
				print("BOD %.1f,%.1f materialy %s" % [x, z, str(mats)])
			var f := mi.mesh.get_faces()
			var hy := -INF
			for t in f.size() / 3:
				var p0 := mi.global_transform * f[t * 3]
				var p1 := mi.global_transform * f[t * 3 + 1]
				var p2 := mi.global_transform * f[t * 3 + 2]
				var v0 := Vector2(p1.x - p0.x, p1.z - p0.z)
				var v1 := Vector2(p2.x - p0.x, p2.z - p0.z)
				var v2 := Vector2(x - p0.x, z - p0.z)
				var den := v0.x * v1.y - v1.x * v0.y
				if absf(den) < 1e-9:
					continue
				var uu := (v2.x * v1.y - v1.x * v2.y) / den
				var ww := (v0.x * v2.y - v2.x * v0.y) / den
				if uu >= 0.0 and ww >= 0.0 and uu + ww <= 1.0:
					hy = maxf(hy, p0.y + uu * (p1.y - p0.y) + ww * (p2.y - p0.y))
			if hy > -INF:
				print("BOD %.1f,%.1f sit %s y %.3f vis %.0f-%.0f" % [x, z, mi.get_path(), hy, mi.visibility_range_begin, mi.visibility_range_end])
		print("BOD %.1f,%.1f vzorek %s prah %.2f kryti %d divokost %.2f smi %s pes_d %.2f vyska %.2f sklon %.2f" % [x, z, v,
				louka._prah(x, z) if louka else 0.0, kh, sv.divokost(x, z), sv.smi_tu_byt(x, z), sv.pes_d(x, z), sv._vyska(x, z), sv.sklon_bunky(x, z)])
		# voda a koryto (Misa 0.67: reka (237,1015) (240,1031) (293,1119) (270,1204))
		var sp := player.get_world_3d().direct_space_state
		var qv := PhysicsRayQueryParameters3D.create(Vector3(x, 300, z), Vector3(x, -200, z), sv.VRSTVA_VODA)
		qv.collide_with_areas = true
		qv.collide_with_bodies = false
		var hv := sp.intersect_ray(qv)
		var ht := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 300, z), Vector3(x, -200, z)))
		var bl: Array = sv.koryto.blizko(x, z) if sv.koryto else []
		print("BOD %.1f,%.1f voda %s (%s) zem %s (%s) koryto %s" % [x, z, (hv["position"] as Vector3).y if hv else "-",
				(hv["collider"] as Node).get_parent().name if hv else "", (ht["position"] as Vector3).y if ht else "-",
				(ht["collider"] as Node).name if ht else "", str(bl)])
	_vysledek("bod", true, "vypsano")


## Pad 0.64 (Misa: v hospode "chtel jsem dat louc na zed a spadlo to"): hrac s horici louci v ruce v hostinci,
## pokladani drzaku louce na zed ve 12 smerech, kazde potvrdit; pak louc z ruky do drzaku.
func _louc_zed() -> void:
	print("POLOHA panel: ", main.diag.poloha_text())
	var pr: Node = main.predmety
	var p := Vector3(-65.9, 37.0, 919.8)          # krok B: hostinec u hlavni cesty (teren ~36 m)
	player.set_flying(false)
	player.place(p + Vector3(0, 1.0, 0), p + Vector3(0, 1.0, 1.0))
	for i in 30:
		await get_tree().physics_frame
	var n := 0
	for k in 12:
		player.yaw = k * TAU / 12.0
		pr.begin_place("drzak_louce", false)
		for i in 6:
			await get_tree().process_frame
		# Misa: drzak na zdi otacel potreti (tma, nebylo videt uhel) - pad
		for rr in 8:
			pr.rotate_place(0.4)
			if pr.has_method("toggle_tilt"):
				pr.toggle_tilt()
			for i in 3:
				await get_tree().process_frame
		print("LOUC_ZED smer %d zed %s valid %s" % [k, pr._wall, pr._valid])
		pr.confirm_place()
		for i in 10:
			await get_tree().process_frame
		if main.menu_hrace and main.menu_hrace.has_method("close"):
			main.menu_hrace.close()
		n += 1
	for i in 60:
		await get_tree().process_frame
	_vysledek("louc_zed", true, "polozeno %d, drzaku %d, svetel %d" % [n,
			pr.placed.filter(func(r: Dictionary) -> bool: return r["id"] == "drzak_louce").size(), main.life.lights.size()])


## Radce 09:20 bod 1 (tablet 0.73 u potoka (-35,27): fyzika 150 ms): chuze po trase u potoka a u lomu; kazdy snimek
## cas fyziky; pri spicce > 8 ms (PC) vypis tvaru kolize do 6 m od hrace (druh, pocet trojuhelniku) a fronty kolizi.
func _fyzika() -> void:
	_jako_hra()
	var trasy := [[Vector2(-20.0, 40.0), Vector2(-60.0, 10.0)], [Vector2(-35.0, 27.0), Vector2(-45.0, 60.0)],
			[Vector2(150.0, 930.0), Vector2(160.0, 975.0)], [Vector2(450.0, 790.0), Vector2(530.0, 880.0)],
			[Vector2(-47.8, 927.5), Vector2(-72.8, 927.1)], [Vector2(520.0, 880.0), Vector2(535.0, 892.0)]]   # Misa 0.88: fyzika 25-34 ms hostinec, rybnik
	var mx := 0.0
	var pr: Array = []
	for tr: Array in trasy:
		var a: Vector2 = tr[0]
		var b: Vector2 = tr[1]
		await main.fast_travel(Vector3(a.x, 0.0, a.y), Vector3(b.x, 1.6, b.y), 0.0, "test")
		for _i in 30:
			await get_tree().process_frame
		var n := int(a.distance_to(b) / 0.08)
		var t_max := 0.0
		for i in n:
			var p := a.lerp(b, float(i) / n)
			player.velocity = Vector3((b - a).normalized().x, 0.0, (b - a).normalized().y) * 5.0
			player.global_position.x = p.x
			player.global_position.z = p.y
			await get_tree().process_frame
			# overeni 16:45: TIME_PHYSICS_PROCESS = max jednoho kroku za posledni 1 s (main.cpp 4.4) - po teleportu v nem
			# zustavalo nacitani; ted fyzika prave uzavreneho snimku z razitek diag (vsechny kroky)
			var t := float((Engine.get_meta("diag") as Object).get("_sn").get("fyzika", 0)) / 1000.0
			if t > t_max:
				t_max = t
			if t > 8.0:
				var sp := player.get_world_3d().direct_space_state
				var q := PhysicsShapeQueryParameters3D.new()
				var sh := SphereShape3D.new()
				sh.radius = 6.0
				q.shape = sh
				q.transform = Transform3D(Basis(), player.global_position)
				var co: Array = []
				for h: Dictionary in sp.intersect_shape(q, 32):
					var o: Object = h["collider"]
					var s2: Shape3D = null
					if o is CollisionObject3D:
						var ow := (o as CollisionObject3D).shape_find_owner(int(h["shape"]))
						s2 = (o as CollisionObject3D).shape_owner_get_shape(ow, 0) if ow >= 0 else null
					var f := (s2 as ConcavePolygonShape3D).get_faces().size() / 3 if s2 is ConcavePolygonShape3D else 0
					co.append("%s %s %d" % [(o as Node).name if o is Node else "?", s2.get_class() if s2 else "?", f])
				print("FYZIKA %.1f ms u (%.0f, %.0f) fronta %d | %s" % [t, p.x, p.y, sv._kol_fronta.size(), ", ".join(co)])
		pr.append("(%.0f,%.0f) %.1f ms" % [a.x, a.y, t_max])
		mx = maxf(mx, t_max)
	_vysledek("fyzika", mx < 16.0, "nejdelsi krok fyziky %.1f ms | %s" % [mx, " ; ".join(pr)])
