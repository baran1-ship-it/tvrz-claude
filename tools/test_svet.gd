extends Node
const Pravidla := preload("res://scripts/pravidla.gd")
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


static func _otisk_souboru(cesty: Array, pripona: String) -> String:
	var soubory: Array = []
	for c: String in cesty:
		if DirAccess.dir_exists_absolute(c):
			for f in DirAccess.get_files_at(c):
				if f.ends_with(pripona):
					soubory.append(c.trim_prefix("res://") + "/" + f)
		else:
			soubory.append(c.trim_prefix("res://"))
	soubory.sort()
	var s := ""
	for f: String in soubory:
		s += FileAccess.get_md5("res://" + f)
	return s.md5_text()


func run(p_main: Node) -> void:
	main = p_main
	player = main.player
	sv = main.svet
	var jen := OS.get_environment("TVRZ_TEST_JEN").split(",", false)
	# vysledky patri k jednomu otisku exportu (radce 18:20 bod 5) - tools/kontrola_vztahu.py jine nepocita
	var ot = JSON.parse_string(FileAccess.get_file_as_string("res://build/export_otisk.json"))
	print("OTISK %s" % (String(ot.get("otisk", "")) if ot is Dictionary else "zadny"))
	# Astra 29. 10. 07:10 bod 5: vysledky patri i ke kodu hry a pravidlum - zmena skriptu nebo vztahy/pasem je zneplatni
	# (stejny vypocet v tools/kontrola_vztahu.py: md5 ze spojenych md5 souboru v abecednim poradi)
	print("KOD %s" % _otisk_souboru(["res://scripts", "res://tools/test_svet.gd"], ".gd"))
	print("PRAVIDLA %s" % _otisk_souboru(["res://pravidla/svet/vztahy.json", "res://pravidla/pravidla_sveta.json"], ".json"))
	sv.kolize_vse(true)                         # paprsky pres celou mapu (visici, pokryv...) vidi i vzdalene skaly
	sv.rostliny_vse(true)                       # visici, stanoviste a dalsi prochazi vsechny instance
	for i in 10:
		await get_tree().process_frame
	await get_tree().physics_frame
	for t: String in ["shadery", "sonda", "breh", "visici", "kolize_drobne", "stanoviste", "pokryv", "dira", "pasmo", "dalka", "prochod", "teleport", "pamet", "sekani", "stuj", "autotest", "bod", "louc_zed", "svetla", "vratka", "pamet_stani", "pamet_okruh", "pamet_pauza", "nizka_trava", "interier", "cesty_volne", "steny", "briza", "rybnik_ves", "fyzika", "vlastni_site", "lom_na_zemi", "co_tu", "stavby_na_zemi", "dvere_domu", "dvere_chysi", "menu_hrace", "ohrady", "zvirata_chuze", "prikop", "lezeni", "fyz_misto", "fyz_nadvori", "fyz_stani", "kresleni_rozbor", "kresleni_ab", "kolize_troj", "mapa_vyhledu", "ves_uzly", "zasazeni", "zamek_terenu", "voda_v_korytu", "site_natazene", "telo_zaber", "mlyn", "breh_hladky", "vztahy", "vztahy_hra", "vetrak", "pravidla_cteni", "vyska_mriz", "logika", "vyska_bod", "louka_bod", "ves_maska", "prolinani", "lod_mezera", "dil_okraj", "dil_kryti", "rybnik_dil", "prikop_hloubka", "ves_osa", "trava_dorust", "bylina_velikost", "louka_profil", "trasa_sceny", "kun_terenem", "kun_prekazky", "most", "postavy_vzhled", "lide_chovani", "interier_trsy", "sklep", "prace_rostliny", "spanek_hra", "lide_zasek", "predmety_cas", "slepice_noc", "les_trava", "hostinec_prochod", "mlyn_zlab", "hostinec_trava", "lednice_blok", "ryb_napojeni", "pocasi", "postavy_modif", "duplicity", "menu_posun"]:
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
				# tvar zasahu (bunkove kolize Kolize_x_z_od nemaji jmeno zdroje): trida tvaru, poloha, meta
				var hc: Object = h["collider"]
				if hc is CollisionObject3D and int(h.get("shape", -1)) >= 0:
					var ow := (hc as CollisionObject3D).shape_find_owner(int(h["shape"]))
					var sh := (hc as CollisionObject3D).shape_owner_get_shape(ow, 0)
					var xf_s := (hc as CollisionObject3D).shape_owner_get_transform(ow)
					co += " tvar %s v %s" % [sh.get_class() if sh else "?", str((hc as Node3D).global_transform * xf_s.origin)]
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
	var breh := float(pa["voda"]["holy_breh_m"])
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
		for n in get_tree().root.find_children("Teren*" if not OS.has_environment("TVRZ_VSE") else "*", "MeshInstance3D", true, false):
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
				radek += " %s%s [%.0f-%.0f] %.2f" % [mi.name, "" if mi.is_visible_in_tree() else "(skryta)", mi.visibility_range_begin, mi.visibility_range_end, best]
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
			["nadvori2", Vector3(4, 0, 1), Vector3(-10, 1.6, -10)],
			# zaseky z tabletu 0.991 (Misa 29. 10.): remizek, listnaty les u lomu, lom-reka, smrkovy les
			["z_remizek", Vector3(-145, 0, 470), Vector3(-112, 1.6, 480)], ["z_les_lom", Vector3(127, 0, 895), Vector3(127, 1.6, 930)],
			["z_lom_reka", Vector3(188, 0, 935), Vector3(188, 1.6, 900)], ["z_smrky", Vector3(16, 0, 988), Vector3(-10, 1.6, 980)],
			# 13. 11. trasa 0.999992: ves-vjezd 560-690 kresleni (tvrz ~330) - rozbor pred sloucenim staveb vsi
			["ves_vjezd", Vector3(355, 0, 738), Vector3(440, 1.6, 790)], ["ves_dvory", Vector3(420, 0, 869), Vector3(421, 1.6, 900)],
			["ves_k_tvrzi", Vector3(440, 0, 790), Vector3(355, 4.1, 738)]]
	var jen_m := OS.get_environment("TVRZ_ROZBOR_MISTA").split(",", false)
	for m: Array in mista:
		if not jen_m.is_empty() and not jen_m.has(String(m[0])):
			continue
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
		var skup := {}
		var celk := [0, 0, 0]
		var nezn := 0
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
				# Astra 07:10 bod 3: troj. jen kde se daji spocitat (porost MultiMesh, site >= 4 povrchy, >= 50 instanci
				# a LOD se nepocitaji) - jinak NEOVERENO (-1), ne 0
				if not (mesh is ArrayMesh and mesh.get_surface_count() < 4 and inst < 50):
					tr = -1
				else:
					for si in mesh.get_surface_count():
						var ar := mesh.surface_get_arrays(si)
						tr += ((ar[Mesh.ARRAY_INDEX] as PackedInt32Array).size() if ar[Mesh.ARRAY_INDEX] != null else (ar[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3 * inst
			var stin := gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF and d < 40.0
			var nm := String(gi.name)
			var rod := String(gi.get_parent().name) if gi.get_parent() else ""
			var druh := (nm + "<" + rod).replace("0", "").replace("1", "").replace("2", "").replace("3", "").replace("4", "").replace("5", "").replace("6", "").replace("7", "").replace("8", "").replace("9", "").replace("@", "")
			# 13. 11.: soucet po skupinach sveta (prvni predek pod korenem sceny) - kde lezi kresleni
			var kor: Node = gi
			while kor.get_parent() != null and kor.get_parent() != get_tree().current_scene and kor.get_parent().get_parent() != get_tree().current_scene:
				kor = kor.get_parent()
			var kg := String(kor.name)
			skup[kg] = int(skup.get(kg, 0)) + kr
			if not sk.has(druh):
				sk[druh] = [0, 0, 0, 0]
			sk[druh][0] += kr
			sk[druh][1] = -1 if tr < 0 or int(sk[druh][1]) < 0 else int(sk[druh][1]) + tr
			sk[druh][2] += kr if stin else 0
			sk[druh][3] += 1
			celk[0] += kr
			celk[1] += maxi(tr, 0)
			celk[2] += kr if stin else 0
			if tr < 0:
				nezn += 1
		var kl: Array = sk.keys()
		kl.sort_custom(func(a: String, b: String) -> bool: return int(sk[a][0]) > int(sk[b][0]))
		# inventura (orientacni): povrchy != volani kresleni (instancovani, LOD); presna cisla jen z enginu (posledni dve)
		print("INVENTURA (orientacni) %s: povrchu %d (+stin %d), troj spocitanych %.2f M + NEOVERENO u %d uzlu, druhu %d | engine kresleni %d troj %.2f M" % [
				m[0], celk[0], celk[2], celk[1] / 1e6, nezn, kl.size(), Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
				Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1e6])
		var ks: Array = skup.keys()
		ks.sort_custom(func(a: String, b: String) -> bool: return int(skup[a]) > int(skup[b]))
		for k: String in ks.slice(0, 25):
			print("INVENTURA SKUPINA %s %-40s povrchu %4d" % [m[0], k.left(40), int(skup[k])])
		for k: String in kl.slice(0, 40):
			print("INVENTURA   %-50s uzlu %4d povrchu %4d stin %4d troj %s" % [k.left(50), sk[k][3], sk[k][0], sk[k][2],
					"NEOVERENO" if int(sk[k][1]) < 0 else "%.3f M" % (float(sk[k][1]) / 1e6)])
	_vysledek("kresleni_rozbor", true, "inventura (orientacni) - viz INVENTURA, troj. NEOVERENO se nepocitaji")


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
## Misa 13. 11. (zasek fyzika 2641 ms u (0, 9) pri vstupu na nadvori a ze sine na nadvori): hrac jde po krocich ze sine
## a z prujezdu na nadvori; kazdy snimek cas fyziky (diag _sn) - nejdelsi snimky s polohou. Rozpocet fyz_nadvori_ms.
func _fyz_nadvori() -> void:
	_jako_hra()
	var dg: Object = Engine.get_meta("diag")
	var cesty := [[Vector3(3.2, 0.0, -14.0), Vector3(0.0, 0.0, 9.0)], [Vector3(0.0, 0.0, 30.0), Vector3(0.0, 0.0, 9.0)]]
	var nej: Array = []
	for ce: Array in cesty:
		await main.fast_travel(ce[0], ce[1], 0.0, "test")
		for _i in 60:
			await get_tree().process_frame
		var a: Vector3 = player.global_position
		var b: Vector3 = ce[1]
		for k in 120:
			var q := a.lerp(Vector3(b.x, a.y, b.z), float(k) / 119.0)
			player.global_position = Vector3(q.x, player.global_position.y, q.z)
			await get_tree().physics_frame
			await get_tree().process_frame
			var f := float(dg.get("_sn").get("fyzika", 0)) / 1000.0
			nej.append([f, player.global_position.round()])
	nej.sort_custom(func(x: Array, y: Array) -> bool: return float(x[0]) > float(y[0]))
	print("FYZNADVORI nejdelsi fyzika: %s" % str(nej.slice(0, 8)))
	_vysledek("fyz_nadvori", float(nej[0][0]) < 50.0, "nejdelsi snimek fyziky %.1f ms u %s" % [float(nej[0][0]), str(nej[0][1])])


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
## Misa 0.991 (#25): dvere chatrci u lomu nejdou otevrit. Kazda chyse: skupina dveri v pohyb.gd, misto pouziti
## (info use kind pohyb) a po prepnuti se kridlo otoci.
func _dvere_chysi() -> void:
	var spatne := []
	var n := 0
	for d: Dictionary in sv._domy:
		if not String(d["typ"]).begins_with("Chyse"):
			continue
		n += 1
		var g := "dum_%d_" % int(d["k"])
		var c := Vector3((d["c"] as Vector2).x, 0.0, (d["c"] as Vector2).y)
		if not main.pohyb.groups.has(g):
			var mam := []
			for k: String in main.pohyb.groups:
				if k.begins_with("dum_%d" % int(d["k"])):
					mam.append(k)
			spatne.append("%s %s: bez skupiny dveri %s (podobne %s)" % [d["typ"], c.snapped(Vector3.ONE), g, str(mam)])
			continue
		var u := (main.info["use"] as Array).filter(func(e: Dictionary) -> bool: return String(e.get("kind", "")) == "pohyb" and String(e.get("id", "")) == g)
		if u.is_empty():
			spatne.append("%s %s: bez mista pouziti" % [d["typ"], c.snapped(Vector3.ONE)])
			continue
		# hrac pred dvermi (1,2 m ven od mista pouziti, smer pruceli), pohled na dvere: nabidka musi byt tyto dvere
		var up: Vector3 = u[0]["pos"]
		var ven := Vector3((d["au"] as Vector2).x, 0.0, (d["au"] as Vector2).y).normalized()
		player.flying = false
		player.global_position = up + ven * 1.2 - Vector3(0, 0.95, 0)
		for i in 20:
			await get_tree().physics_frame
		player.cam.look_at(up)
		await get_tree().process_frame
		var nab: Dictionary = main.life.usable(player.cam)
		if String(nab.get("id", "")) != g:
			spatne.append("%s %s: pred dvermi nabidka %s %s (hrac %s, dvere %s)" % [d["typ"], c.snapped(Vector3.ONE), nab.get("kind", "nic"), nab.get("id", nab.get("name", "")),
					player.global_position.snapped(Vector3.ONE * 0.1), up.snapped(Vector3.ONE * 0.1)])
		var it: Dictionary = (main.pohyb.groups[g]["items"] as Array)[0]
		var nd: Node3D = it["node"]
		var r0 := nd.global_basis
		main.pohyb.toggle(g)
		for i in 90:
			await get_tree().physics_frame
		var uhel := rad_to_deg(r0.get_rotation_quaternion().angle_to(nd.global_basis.get_rotation_quaternion()))
		main.pohyb.toggle(g)
		if uhel < 45.0:
			spatne.append("%s %s: kridlo se otocilo jen o %.0f st." % [d["typ"], c.snapped(Vector3.ONE), uhel])
	_vysledek("dvere_chysi", n > 0 and spatne.is_empty(), "chysi %d, spatne %s" % [n, str(spatne)])


## Menu hrace (Misa 29. 10.: vyzbrojit, obleci, statistiky, dovednosti): kazda stranka ma polozky, A ve Postave
## oblece vec z brasny do slotu a dalsi A ji vymeni / sundá, polozena vec slot uvolni.
func _menu_hrace() -> void:
	var mh: Node = main.menu_hrace
	var P: Node = main.predmety
	var spatne := []
	P.add_inv("stit")
	P.add_inv("barbuta")
	var pocty := {}
	for pg: String in ["brasna", "postava", "dovednosti", "denik"]:
		mh.show_page(pg)
		for i in 3:
			await get_tree().process_frame
		pocty[pg] = mh._items(0).size()
		if pg != "denik" and pocty[pg] == 0:
			spatne.append("%s prazdna" % pg)
		mh.close()
	mh.show_page("postava")
	var sl: Array = mh._items(0)
	mh.sel[0] = sl.find("stit")
	mh._act()
	if String(P.vybava.get("stit", "")) != "stit":
		spatne.append("A ve slotu Stit neoblekl stit (%s)" % str(P.vybava))
	mh._act()
	if P.vybava.has("stit"):
		spatne.append("druhe A stit nesundalo (%s)" % str(P.vybava))
	mh._act()
	P.inv.erase("stit")                       # vsechny stity pryc z brasny (hrac jich mohl mit vic)
	P.vybava_over()
	if P.vybava.has("stit"):
		spatne.append("stit mimo brasnu zustal oblecen")
	mh.close()
	for pg: String in ["dovednosti", "denik"]:
		mh.show_page(pg)
		for tb in mh._tabs().size():
			mh.tab = tb
			for it: String in mh._items(0):
				if mh._dv_nazev(it) == "" or mh._dv_hodnota(it) == "":
					spatne.append("%s %s bez jmena/hodnoty" % [pg, it])
		mh.close()
	_vysledek("menu_hrace", spatne.is_empty(), "polozek %s, spatne %s" % [str(pocty), str(spatne)])


## Ohrady a zvirata (Misa 29. 10.): kazda ohrada ze zvirata.json postavena (plutky), plutek nestoji v jine stavbe,
## strome ani na pesine/ceste, zvirat tolik, kolik chce zaznam, a po 8 s chuze jsou vsechna uvnitr sve meze.
func _ohrady() -> void:
	var spatne := []
	var chci := 0
	for o: Dictionary in Pravidla.cti("zvirata", "ohrady"):
		chci += int(o["kusu"])
	for dv: Dictionary in Pravidla.cti("zvirata", "dvory"):
		chci += int(dv["kusu"])
	var zv: Node = main.zvirata
	var n_zv: int = zv._zv.size()
	if n_zv != chci:
		spatne.append("zvirat %d, zaznam chce %d" % [n_zv, chci])
	var ohr := {}
	var space := player.get_world_3d().direct_space_state
	var vlastni: Array = []                   # kolize plutku samotnych (vynechat)
	for rec: Dictionary in main.predmety.placed:
		if String(rec["id"]) == String(Pravidla.cti("zvirata", "plutek")) and rec.has("node"):
			for b in (rec["node"] as Node).find_children("*", "CollisionObject3D", true, false):
				vlastni.append((b as CollisionObject3D).get_rid())
	# postavene plutky (ne jen zaznamy): uzel ve scene, viditelny, dosah (Misa 0.992 „za rychtou neni plot“ - kosar)
	var post := {}
	for rec: Dictionary in main.predmety.placed:
		if String(rec["id"]) != String(Pravidla.cti("zvirata", "plutek")) or not rec.has("node"):
			continue
		var nd := rec["node"] as Node3D
		var gp := nd.global_position
		var ve := INF
		for g in nd.find_children("*", "GeometryInstance3D", true, false):
			ve = minf(ve, (g as GeometryInstance3D).visibility_range_end if (g as GeometryInstance3D).visibility_range_end > 0.0 else INF)
		if gp.distance_to(Vector3(400.5, gp.y, 834.4)) < 9.0:
			var ab := AABB()
			for g in nd.find_children("*", "MeshInstance3D", true, false):
				var a2: AABB = (g as MeshInstance3D).global_transform * (g as MeshInstance3D).get_aabb()
				ab = a2 if ab.size == Vector3.ZERO else ab.merge(a2)
			print("KOSAR plutek %s zem %.2f yaw %.0f aabb %s" % [gp.snapped(Vector3.ONE * 0.01), float(sv._vyska(gp.x, gp.z)), rad_to_deg(nd.global_rotation.y), ab])
		var klic := "%d,%d" % [roundi(gp.x / 20.0), roundi(gp.z / 20.0)]
		post[klic] = int(post.get(klic, 0)) + 1
		for g in nd.find_children("*", "GeometryInstance3D", true, false):
			if (g as GeometryInstance3D).lod_bias < float(Pravidla.cti("zvirata", "plutek_lod_bias")):
				spatne.append("plutek %s lod_bias %.1f (pruty zmizi)" % [gp.snapped(Vector3.ONE * 0.1), (g as GeometryInstance3D).lod_bias])
				break
		if not nd.is_visible_in_tree() or ve < 15.0:
			spatne.append("plutek %s skryty nebo dosah %.0f m" % [gp.snapped(Vector3.ONE * 0.1), ve])
	print("OHRADY postavene plutky po bunkach 20 m: %s" % str(post))
	for it: Dictionary in sv.data["vybaveni"]:
		if not it.has("ohrada"):
			continue
		ohr[it["ohrada"]] = int(ohr.get(it["ohrada"], 0)) + 1
		var u := "%d,%d" % [roundi(float(it["p"][0]) / 20.0), roundi(float(it["p"][2]) / 20.0)]
		if int(post.get(u, 0)) == 0:
			spatne.append("%s plutek %s nepostaven" % [it["ohrada"], Vector3(it["p"][0], it["p"][1], it["p"][2]).snapped(Vector3.ONE * 0.1)])
		var p := Vector3(it["p"][0], it["p"][1], it["p"][2])
		if _na_ceste(p.x, p.z):
			spatne.append("%s plutek %s na ceste" % [it["ohrada"], p.snapped(Vector3.ONE * 0.1)])
		for i in sv.PESINY.size():
			var pl: Array = sv.PESINY[i]
			for j in pl.size() - 1:
				var q := Geometry2D.get_closest_point_to_segment(Vector2(p.x, p.z), pl[j], pl[j + 1])
				if q.distance_to(Vector2(p.x, p.z)) < float(sv.PES_SIRKA[i]) + 0.3:
					spatne.append("%s plutek %s na pesine %d" % [it["ohrada"], p.snapped(Vector3.ONE * 0.1), i])
		# kolize s cimkoli krome terenu a jinych plutku
		var q2 := PhysicsShapeQueryParameters3D.new()
		var bx := BoxShape3D.new()
		bx.size = Vector3(0.1, 0.6, 1.8)
		q2.shape = bx
		q2.transform = Transform3D(Basis(Vector3.UP, float(it["yaw"])), p + Vector3(0, 0.55, 0))
		q2.exclude = vlastni
		for h: Dictionary in space.intersect_shape(q2, 8):
			var nm := String((h["collider"] as Node).name)
			var par := String((h["collider"] as Node).get_parent().name) if (h["collider"] as Node).get_parent() else ""
			if nm.begins_with("Teren"):
				continue
			# co to je: nejblizsi rostlina (kmen, ker, kamen) do 2,5 m
			var co := ""
			var nej := 2.5
			for key: String in sv.data["rostliny"]:
				for tr: Array in sv.data["rostliny"][key]:
					var dd := Vector2(float(tr[3]), float(tr[11])).distance_to(Vector2(p.x, p.z))
					if dd < nej:
						nej = dd
						co = "%s %.1f m" % [key, dd]
			spatne.append("%s plutek %s narazi na %s/%s (%s)" % [it["ohrada"], p.snapped(Vector3.ONE * 0.1), par, nm, co])
	# kandidati: za kazdym domem (z za strechou) a na strane dvora - volno pro ohradu 4 x 4 m (cesta, pesina, kolize)
	for d: Dictionary in sv._domy:
		if not (d["m"] as Dictionary).has("ix"):
			continue
		var m: Dictionary = d["m"]
		var xf: Transform3D = d["xf"]
		var vys := []
		for kand: Array in [["za", 0.0, float(m["rz0"]) - 3.2], ["dvur", -(float(m["hw"]) + 3.2), (float(m["f"]) + float(m["b"])) * 0.5], ["dvur_zad", -(float(m["hw"]) + 3.2), float(m["b"]) + 1.0]]:
			var zle := 0
			for gx in [-1.6, 0.0, 1.6]:
				for gz in [-1.6, 0.0, 1.6]:
					var w := xf * Vector3(float(kand[1]) + gx, 0.0, float(kand[2]) + gz)
					if _na_ceste(w.x, w.z):
						zle += 1
						continue
					for i in sv.PESINY.size():
						var pl: Array = sv.PESINY[i]
						for j in pl.size() - 1:
							if Geometry2D.get_closest_point_to_segment(Vector2(w.x, w.z), pl[j], pl[j + 1]).distance_to(Vector2(w.x, w.z)) < float(sv.PES_SIRKA[i]) + 0.3:
								zle += 1
			vys.append("%s %d" % [kand[0], zle])
		print("OHRADA_KANDIDAT dum %d: %s" % [int(d["k"]), ", ".join(vys)])
	# vyska: pata plutku a zvirete na skutecne siti terenu (paprsek na Teren*) - zapusteny / visici
	var zem := func(x: float, z: float, y0: float) -> float:
		var rq := PhysicsRayQueryParameters3D.create(Vector3(x, y0 + 3.0, z), Vector3(x, y0 - 6.0, z))
		for _k in 6:
			var h := space.intersect_ray(rq)
			if h.is_empty():
				return INF
			if String((h["collider"] as Node).name).begins_with("Teren"):
				return float((h["position"] as Vector3).y)
			rq.exclude = rq.exclude + [h["rid"]]
		return INF
	for it2: Dictionary in sv.data["vybaveni"]:
		if not it2.has("ohrada"):
			continue
		var ty: float = zem.call(float(it2["p"][0]), float(it2["p"][2]), float(it2["p"][1]))
		# kuly plutku jsou zapichnute: do 0,25 m v zemi v poradku, nad zemi ne vic nez 0,1 m
		if ty != INF and (float(it2["p"][1]) < ty - 0.25 or float(it2["p"][1]) > ty + 0.1):
			spatne.append("%s plutek %s %s o %.2f m" % [it2["ohrada"], Vector3(it2["p"][0], it2["p"][1], it2["p"][2]).snapped(Vector3.ONE * 0.1),
					"zapusteny" if float(it2["p"][1]) < ty else "visi", absf(float(it2["p"][1]) - ty)])
	for z1: Dictionary in zv._zv:
		var g1: Vector3 = (z1["node"] as Node3D).global_position
		var ty1: float = zem.call(g1.x, g1.z, g1.y)
		if ty1 != INF and absf(g1.y - ty1) > 0.12:
			spatne.append("%s %s o %.2f m" % [(z1["node"] as Node3D).name, "v zemi" if g1.y < ty1 else "ve vzduchu", absf(g1.y - ty1)])
	# stavba nad ohradou (strecha, stodola): paprsek shora do stredu a rohu ohrady - prvni zasah musi byt teren
	# nebo plutek (obalka domu na sikmem pudorysu pokryla i dvur - planne hlaseni)
	for z2: Dictionary in sv.data.get("zvirata", []):
		if not z2.has("pul"):
			continue
		var b2 := Basis(Vector3.UP, float(z2["yaw"]))
		for o2: Vector2 in [Vector2.ZERO, Vector2(0.8, 0.8), Vector2(-0.8, 0.8), Vector2(0.8, -0.8), Vector2(-0.8, -0.8)]:
			var w2 := Vector3(z2["stred"][0], z2["stred"][1], z2["stred"][2]) + b2 * Vector3(o2.x * float(z2["pul"][0]), 0.0, o2.y * float(z2["pul"][1]))
			var rq2 := PhysicsRayQueryParameters3D.create(w2 + Vector3(0, 8.0, 0), w2 - Vector3(0, 2.0, 0))
			rq2.exclude = vlastni
			var h2 := space.intersect_ray(rq2)
			if not h2.is_empty() and not String((h2["collider"] as Node).name).begins_with("Teren") and float((h2["position"] as Vector3).y) > w2.y + 0.5:
				spatne.append("%s pod stavbou %s/%s (roh %s, zasah %s, zem %.1f)" % [z2["id"], String((h2["collider"] as Node).get_parent().name), String((h2["collider"] as Node).name),
						str(o2), (h2["position"] as Vector3).snapped(Vector3.ONE * 0.1), w2.y])
				break
	# zadna rostlina (strom, ker, kamen) uvnitr ohrady - ohrada nic nehybe, misto musi byt volne
	for z0: Dictionary in sv.data.get("zvirata", []):
		if not z0.has("pul"):
			continue
		var b0 := Basis(Vector3.UP, float(z0["yaw"]))
		var c0 := Vector3(z0["stred"][0], 0.0, z0["stred"][2])
		for key: String in sv.data["rostliny"]:
			if ["grass", "trav", "kvet", "kopret", "jetel", "pampel", "mech", "jitrocel", "nettle", "weed", "dandelion", "clover", "ribwort"].any(func(s: String) -> bool: return key.contains(s)):
				continue                                   # nizke byliny v ohrade nevadi (zvirata je spasou)
			for tr: Array in sv.data["rostliny"][key]:
				var l0 := b0.inverse() * (Vector3(float(tr[3]), 0.0, float(tr[11])) - c0)
				if absf(l0.x) < float(z0["pul"][0]) + 0.3 and absf(l0.z) < float(z0["pul"][1]) + 0.3:
					spatne.append("%s rostlina %s uvnitr (v ohrade x %.1f z %.1f)" % [z0["id"], key, l0.x, l0.z])
	# hledani mista pro kosar 10 x 8 m kolem rychty (usedlost 5): bez kolize, cesty, pesiny, stromu, sklon do 1 m
	for d5: Dictionary in sv._domy:
		if int(d5["k"]) != 5:
			continue
		var yaw5 := PI / 2.0 - atan2(float((d5["au"] as Vector2).y), float((d5["au"] as Vector2).x))
		var b5 := Basis(Vector3.UP, yaw5)
		var c5: Vector2 = d5["c"]
		var nalez := 0
		for r5 in [16.0, 20.0, 24.0, 28.0, 32.0, 38.0]:
			for a5 in 24:
				if nalez >= 6:
					break
				var w5: Vector2 = Vector2(c5.x, c5.y) + Vector2.from_angle(TAU * a5 / 24.0) * float(r5)
				var ys5: Array = []
				var ok5 := true
				for qx in [-5.0, 0.0, 5.0]:
					for qz in [-4.0, 0.0, 4.0]:
						var q5 := b5 * Vector3(qx, 0.0, qz) + Vector3(w5.x, 0.0, w5.y)
						ys5.append(float(sv.call("_vyska", q5.x, q5.z)))
						if _na_ceste(q5.x, q5.z):
							ok5 = false
						for i in sv.PESINY.size():
							var pl5: Array = sv.PESINY[i]
							for j in pl5.size() - 1:
								if Geometry2D.get_closest_point_to_segment(Vector2(q5.x, q5.z), pl5[j], pl5[j + 1]).distance_to(Vector2(q5.x, q5.z)) < float(sv.PES_SIRKA[i]) + 0.5:
									ok5 = false
				if not ok5 or float(ys5.max()) - float(ys5.min()) > 1.0:
					continue
				var y5 := float(sv.call("_vyska", w5.x, w5.y))
				var qq := PhysicsShapeQueryParameters3D.new()
				var bx5 := BoxShape3D.new()
				bx5.size = Vector3(10.6, 2.5, 8.6)
				qq.shape = bx5
				qq.transform = Transform3D(b5, Vector3(w5.x, y5 + 1.6, w5.y))
				var hity := space.intersect_shape(qq, 8).filter(func(h: Dictionary) -> bool: return not String((h["collider"] as Node).name).begins_with("Teren"))
				if not hity.is_empty():
					continue
				nalez += 1
				var lok := (d5["inv"] as Transform3D) * Vector3(w5.x, 0.0, w5.y)
				print("KOSAR_MISTO svet (%.1f, %.1f) v ramci domu 5 [%.1f, %.1f] sklon %.2f" % [w5.x, w5.y, lok.x, lok.z, float(ys5.max()) - float(ys5.min())])
	for o: Dictionary in Pravidla.cti("zvirata", "ohrady"):
		if int(ohr.get(o["id"], 0)) == 0:
			spatne.append("ohrada %s nepostavena" % o["id"])
	# 8 s chuze (hrac u kosare, at se zvirata hybou): vsechna v mezi
	if n_zv > 0:
		player.global_position = (zv._zv[0]["node"] as Node3D).global_position + Vector3(6, 0, 0)
		for i in 480:
			await get_tree().process_frame
		for z: Dictionary in zv._zv:
			var g: Vector3 = (z["node"] as Node3D).global_position
			var v: Vector2 = zv._do_meze(z["mez"], Vector2(g.x, g.z))
			if v.distance_to(Vector2(g.x, g.z)) > 0.05:
				spatne.append("%s mimo mez o %.2f m" % [(z["node"] as Node3D).name, v.distance_to(Vector2(g.x, g.z))])
	var souhrn := {}
	for s: String in spatne:
		var k := s.split(" ")[0]
		souhrn[k] = int(souhrn.get(k, 0)) + 1
	print("OHRADY_SOUHRN %s" % str(souhrn))
	_vysledek("ohrady", spatne.is_empty() and n_zv > 0, "zvirat %d, plutku %s, spatne %s" % [n_zv, str(ohr), str(spatne.slice(0, 20))])


## Cesta (hlavni cesty - kraj vozovky svet.cesta_kraj, ulice vsi - osa ves_oblouk + nejvetsi pulsirka z lokace).
## Pozor: svet.ves_cesta je maska bez travy (i udusany dvur), ne cesta.
func _na_ceste(x: float, z: float) -> bool:
	if float(sv.call("cesta_kraj", x, z)) < 0.3:
		return true
	var ul: Dictionary = Pravidla.cti("lokace", "ves", "ulice")
	return sv.vo != null and float(sv.vo.od_ulice(Vector2(x, z))) < float(ul["pulsirka"]["max"]) + 0.3


## Chuze zvirat (Misa 0.994 „ovce a slepice nechodi, sankuji“): kazdy druh rozejit k cili 3 m daleko a merit, o kolik
## se kosti nohou otoci proti klidu (zvirata.json noha_st) a ze se zvire hybe; vypis i kost a osu.
func _zvirata_chuze() -> void:
	var zv: Node = main.zvirata
	var spatne := []
	var vid := {}
	for z: Dictionary in zv._zv:
		var druh := String(z["druh"])
		if vid.has(druh):
			continue
		vid[druh] = true
		var n: Node3D = z["node"]
		player.global_position = n.global_position + Vector3(0, 0, 8)    # hrac blizko (zvire se hybe jen v dosahu)
		var sk: Skeleton3D = z["kostra"]
		if sk == null or (z["nohy"] as Array).is_empty():
			spatne.append("%s bez kostry nebo nohou" % druh)
			continue
		z["cil"] = Vector2(n.global_position.x + 1.5, n.global_position.z + 1.5)
		z["mez"] = {"c": n.global_position, "yaw": 0.0, "r": 50.0}
		var p0 := n.global_position
		var mx := 0.0
		for _f in 40:
			zv._process(0.05)                                     # primo, bez cekani na snimky (headless)
			for nf: Array in z["nohy"]:
				var b := int(nf[0])
				var q: Quaternion = sk.get_bone_pose_rotation(b)
				var r: Quaternion = sk.get_bone_rest(b).basis.get_rotation_quaternion()
				mx = maxf(mx, rad_to_deg(q.angle_to(r)))
		var posun := n.global_position.distance_to(p0)
		print("ZVIRE_CHUZE %s posun %.2f m, max otoceni nohy %.1f st, jde %s, ap %s, kost %s" % [druh, posun, mx, z["jde"], z["ap"] != null, sk.get_bone_name(int(z["nohy"][0][0]))])
		if posun < 0.1:
			spatne.append("%s se nehnul" % druh)
		elif mx < 5.0:
			spatne.append("%s jde, ale nohy %.1f st" % [druh, mx])
	_vysledek("zvirata_chuze", spatne.is_empty(), str(spatne))


## Slepice v noci spi (Misa 0.99994, r. 70; zvirata.json chovani.slepice.spanek): ve 22 h dojdou z dvora na nocleh
## (kurnik / zed chalupy) a zmizi, v 7 h jsou zase venku; v noci bez zvuku.
## Bod mezi korunami lesa: aspon 3 ze 4 bodu ve vzdalenosti ok_r pixelu (2 m) pod korunou.
func _les_kolem(kr: Image, r: Rect2, x: float, z: float, ok_r: int) -> bool:
	var ki := clampi(roundi((x - r.position.x) / 2.0), ok_r, kr.get_width() - 1 - ok_r)
	var kj := clampi(roundi((z - r.position.y) / 2.0), ok_r, kr.get_height() - 1 - ok_r)
	var n := 0
	for d: Vector2i in [Vector2i(ok_r, 0), Vector2i(-ok_r, 0), Vector2i(0, ok_r), Vector2i(0, -ok_r)]:
		if kr.get_pixel(ki + d.x, kj + d.y).r > 0.5:
			n += 1
	return n >= 3


## Tráva v lese podle světla (Míša 9. 11., KCD 18_kcd_les, tabulka misa_28_chyby ř. 88/86; pravidla/svet/les_podrost.json):
## v bodech plného zápoje (koruna všech stromů svet.koruny >= 0,9 v bodě a průměr korun okolí ±okoli_m >= okoli_do,
## dál než pesina_svetlo_m od pěšiny, mimo cesty, vodu a stavby) průměrná hustota louky <= test.max_hustota a podíl
## bodů, kde louka zasije (hustota >= louka._prah v bodě - tentýž práh jako rozsev drnu, vějíře a trsů), <= max_podil.
## Zápoj počítá test sám z masky korun (ne funkcí louky). Vypíše i světlá místa lesa (mezery mezi korunami) - tam
## tráva zůstává (ne globální zředění) - a počty instancí louky v buňkách lesa měřicí trasy (před/po).
func _les_trava() -> void:
	var lk: Node = main.get_node_or_null("Louka")
	if lk == null:
		_vysledek("les_trava", false, "neni louka")
		return
	var P = preload("res://scripts/pravidla.gd")
	var z_od := float(P.cti("les_podrost", "trava", "zapoj_od"))
	var pes_m := float(P.cti("les_podrost", "trava", "pesina_svetlo_m"))
	var mx := float(P.cti("les_podrost", "test", "max_hustota"))
	var ok_do := float(P.cti("les_podrost", "trava", "okoli_do"))
	var ok_r := maxi(1, roundi(float(P.cti("les_podrost", "trava", "okoli_m")) / 2.0))
	var mx_pod := float(P.cti("les_podrost", "test", "max_podil_travy"))
	var r: Rect2 = sv.stan_rect
	var n_z := 0
	var s_z := 0.0
	var tr_z := 0
	var n_s := 0
	var s_s := 0.0
	var n_kor := 0
	var kor_bez_zapoje := 0
	var kr: Image = sv.koruny
	var priklady: Array = []
	var x := r.position.x + 2.0
	while x < r.end.x - 2.0:
		var z := r.position.y + 2.0
		while z < r.end.y - 2.0:
			var rg: float = sv._st(0, x, z) + sv._st(1, x, z)
			var kv := 0.0
			if kr:
				kv = kr.get_pixel(clampi(roundi((x - r.position.x) / 2.0), 0, kr.get_width() - 1), clampi(roundi((z - r.position.y) / 2.0), 0, kr.get_height() - 1)).r
			if kv > 0.9:
				n_kor += 1
				if rg < z_od:
					kor_bez_zapoje += 1             # pod korunou (vsechny stromy), ale maska zapoje rika svetlo (samotar, novy les)
			var plny := false
			if kv >= 0.9:
				var ki := clampi(roundi((x - r.position.x) / 2.0), ok_r, kr.get_width() - 1 - ok_r)
				var kj := clampi(roundi((z - r.position.y) / 2.0), ok_r, kr.get_height() - 1 - ok_r)
				var so := 0.0
				for dj in range(-ok_r, ok_r + 1):
					for di in range(-ok_r, ok_r + 1):
						so += kr.get_pixel(ki + di, kj + dj).r
				plny = so / float((2 * ok_r + 1) * (2 * ok_r + 1)) >= ok_do
			if plny and sv.pes_d(x, z) >= pes_m and sv.cesta_kraj_osa(x, z).x > 0.0 and sv.od_vody(x, z) > 1.5 and not lk._v_budove(x, z):
				var v: float = (lk._vzorek(x, z) as Vector3).x
				n_z += 1
				s_z += v
				if v >= lk._prah(x, z):                    # tentyz prah jako rozsev (drn, vejir, trsy)
					tr_z += 1
					if priklady.size() < 6:
						priklady.append("(%.0f, %.0f) %.2f" % [x, z, v])
			elif kv < 0.05 and kr and _les_kolem(kr, r, x, z, ok_r) and sv._louka_m(x, z) > 0.2 and sv.cesta_kraj_osa(x, z).x > 0.0:
				n_s += 1
				s_s += (lk._vzorek(x, z) as Vector3).x
			z += 4.0
		x += 4.0
	var prum := s_z / maxf(n_z, 1)
	var podil := float(tr_z) / maxf(n_z, 1)
	print("LES_TRAVA zapoj: %d bodu, prumer hustoty %.3f, s travou (nad prahem rozsevu) %d = %.1f %% %s" % [n_z, prum, tr_z, podil * 100.0, str(priklady)])
	print("LES_TRAVA svetla mista lesa (mezi korunami, maska lesa R+G > 0,05): %d bodu, prumer hustoty %.3f" % [n_s, s_s / maxf(n_s, 1)])
	print("LES_TRAVA pod korunou (svet.koruny > 0,9, vsechny stromy): %d bodu, z toho maska zapoje svetlo (R+G < %.2f) %d = %.1f %%" % [n_kor, z_od, kor_bez_zapoje, 100.0 * kor_bez_zapoje / maxf(n_kor, 1)])
	# rozbor zapoje na mistech snimku (lesA haj 205,250 -> 213,300; lesB 175,893; lesC -3,490): koruna v bode, prumer
	# korun okoli, zapoj sveta a hustota louky
	for q: Vector2 in [Vector2(205, 255), Vector2(207, 265), Vector2(209, 275), Vector2(211, 285), Vector2(175, 893), Vector2(185, 888), Vector2(-3, 490), Vector2(-10, 505)]:
		var ki := clampi(roundi((q.x - r.position.x) / 2.0), ok_r, kr.get_width() - 1 - ok_r)
		var kj := clampi(roundi((q.y - r.position.y) / 2.0), ok_r, kr.get_height() - 1 - ok_r)
		var so := 0.0
		for dj in range(-ok_r, ok_r + 1):
			for di in range(-ok_r, ok_r + 1):
				so += kr.get_pixel(ki + di, kj + dj).r
		print("LES_TRAVA bod (%.0f, %.0f): koruna %.2f, okoli %.2f, zapoj %.2f, hustota louky %.3f" % [q.x, q.y, kr.get_pixel(ki, kj).r,
				so / float((2 * ok_r + 1) * (2 * ok_r + 1)), sv.zapoj_v(q.x, q.y), (lk._vzorek(q.x, q.y) as Vector3).x])
	# instance louky v bunkach lesa merici trasy (bunka 32 m + 8 sousedu)
	var vrst := ["trsy", "kvety", "drn", "vysoka", "vejir"]
	for b: Array in P.cti("les_podrost", "test", "bunky"):
		var c0 := Vector2i(floori(float(b[0]) / lk.BUNKA), floori(float(b[1]) / lk.BUNKA))
		var poc := [0, 0, 0, 0, 0]
		for dj in range(-1, 2):
			for di in range(-1, 2):
				var by: PackedByteArray = lk._rozsej(c0 + Vector2i(di, dj))
				if by.is_empty():
					continue
				for k in 5:
					poc[k] += by.decode_u32(k * 4)
		var t := ""
		var celk := 0
		for k in 5:
			t += " %s %d" % [vrst[k], poc[k]]
			celk += poc[k]
		print("LES_TRAVA instance louky u (%.0f, %.0f) 9 bunek 96x96 m: celkem %d,%s (R+G v bode %.2f, zapoj %.2f)" % [float(b[0]), float(b[1]), celk, t,
				sv._st(0, float(b[0]), float(b[1])) + sv._st(1, float(b[0]), float(b[1])), sv.zapoj_v(float(b[0]), float(b[1]))])
	_vysledek("les_trava", n_z > 0 and prum <= mx and podil <= mx_pod, "plny zapoj %d bodu: hustota %.3f (max %.2f), s travou %.1f %% (max %.0f %%)" % [n_z, prum, mx, podil * 100.0, mx_pod * 100.0])


func _slepice_noc() -> void:
	var zv: Node = main.zvirata
	var spatne := []
	var h0: float = main.day.hour
	var dvur: Array = zv._zv.filter(func(z: Dictionary) -> bool: return (z["mez"] as Dictionary).has("noc"))
	if dvur.is_empty():
		_vysledek("slepice_noc", false, "zadny dvur s noclehem")
		return
	main.day.hour = 22.0
	var n0: Node3D = dvur[0]["node"]
	player.global_position = n0.global_position + Vector3(0, 0, 4)
	for _f in 600:
		zv._process(0.05)
	for z: Dictionary in dvur:
		var n: Node3D = z["node"]
		if n.visible:
			spatne.append("%s ve 22 h venku %s (nocleh %s)" % [n.name, n.global_position.snapped(Vector3.ONE * 0.1), z["mez"]["noc"]])
	main.day.hour = 7.0
	for _f in 5:
		zv._process(0.05)
	for z: Dictionary in dvur:
		if not (z["node"] as Node3D).visible:
			spatne.append("%s v 7 h schovana" % (z["node"] as Node3D).name)
	main.day.hour = h0
	print("SLEPICE_NOC slepic s noclehem %d, chyby %s" % [dvur.size(), str(spatne.slice(0, 10))])
	_vysledek("slepice_noc", spatne.is_empty(), str(spatne.slice(0, 10)))


## Mokry prikop (Misa 0.992 „v prikopu nekde chybi voda“, (-24, 19)): po obvodu tvrze po 5 st. nejnizsi bod skutecne
## site terenu (paprsek na Teren*) mezi 15 a 45 m od stredu musi byt pod hladinou prikopu (voda.json prikop) - jinak
## suche dno. Vypisuje usek a co tam teren zvedlo (jmeno site).
func _prikop() -> void:
	var hl := float(Pravidla.cti("voda", "prikop")["hladina_y"])
	var sp := player.get_world_3d().direct_space_state
	var suche := []
	for a in range(0, 360, 5):
		var nej := INF
		var nej_p := Vector3.ZERO
		var nej_jm := ""
		for d in range(15, 46):
			var x := cos(deg_to_rad(a)) * d
			var z := sin(deg_to_rad(a)) * d
			var rq := PhysicsRayQueryParameters3D.create(Vector3(x, 20.0, z), Vector3(x, -20.0, z))
			for _k in 6:
				var h := sp.intersect_ray(rq)
				if h.is_empty():
					break
				var jm := String((h["collider"] as Node).name)
				if jm.begins_with("Teren") or jm.begins_with("Prikop") or jm.begins_with("Val"):
					if float((h["position"] as Vector3).y) < nej:
						nej = float((h["position"] as Vector3).y)
						nej_p = h["position"]
						nej_jm = jm
					break
				rq.exclude = rq.exclude + [h["rid"]]
		if nej > hl - 0.1:
			suche.append("%d st.: dno %.2f u (%.0f, %.0f) %s" % [a, nej, nej_p.x, nej_p.z, nej_jm])
	_vysledek("prikop", suche.is_empty(), "hladina %.2f, suche useky %d: %s" % [hl, suche.size(), str(suche.slice(0, 12))])


func _lezeni() -> void:
	var zbs: Array = []
	var typy := {}
	for u: Dictionary in main.info["use"]:
		if String(u.get("kind", "")) == "zebrik" and not bool(u["nahore"]):
			# jeden zebrik z kazdeho mista (bunka 60 m: lom, kazdy dum, mlyn, vetrny mlyn) - drive 3 z lomu a 3 z vsi,
			# zebriky mlyna a vetrniku test nevidel (Misa 0.991: „ve mlyne nejdou“)
			var pa: Vector3 = u["zb"]["pata"]
			var k := "%d_%d" % [floori(pa.x / 60.0), floori(pa.z / 60.0)]
			if not typy.has(k) and typy.size() < 10:
				typy[k] = 1
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
			# co je pod mistem sestupu (podlaha s kolizi? ktera?) - at se z vypisu pozna pricina
			var pod := []
			var od := s + Vector3(0, 0.6, 0)
			for kk in 4:
				var rq := PhysicsRayQueryParameters3D.create(od, s - Vector3(0, 4.0, 0))
				rq.exclude = [player.get_rid()]
				rq.collision_mask = player.collision_mask
				var h := player.get_world_3d().direct_space_state.intersect_ray(rq)
				if h.is_empty():
					break
				pod.append("%.2f %s" % [(h["position"] as Vector3).y, String((h["collider"] as Node).name) if h["collider"] is Node else "?"])
				od = (h["position"] as Vector3) - Vector3(0, 0.05, 0)
			spatne.append("%s: nahore %s (%s vs %s) dole %s, pod sestupem %s" % [(zb["pata"] as Vector3).snapped(Vector3.ONE * 0.1), nahore, p.snapped(Vector3.ONE * 0.01), s.snapped(Vector3.ONE * 0.01), dole, str(pod)])
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
	var kat_lom: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://modely/predmety.json"))
	var pp_pr: Dictionary = sv.pasma()["predmet"]
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
		# Misa 0.9998 „v lomu zase lezi naradi na zemi, to uz jsme resili“ (129-133, 952): dlouhe naradi a zebrik
		# (pasma.predmet opreny_delka_m) na zemi lomu musi byt opreny - naklon od svisle v mezich pasma, ne naplocho
		var inf: Dictionary = kat_lom.get(String(it["id"]), {})
		var rz: Array = inf.get("rozmer", [0.0, 0.0, 0.0])
		if (inf.get("kat") == "naradi" or String(it["id"]) == "zebrik") and maxf(float(rz[0]), maxf(float(rz[1]), float(rz[2]))) >= float(pp_pr["opreny_delka_m"]):
			var a := INF
			if it.has("up"):
				var up := Vector3(it["up"][0], it["up"][1], it["up"][2]).normalized()
				a = rad_to_deg(acos(clampf(up.y, -1.0, 1.0)))
			if a < float(pp_pr["opreny_uhel_st"][0]) or a > float(pp_pr["opreny_uhel_st"][1]) + 0.5:
				spatne.append("%s (%.0f,%.0f) lezi na zemi, neni opreny" % [it["id"], pp[0], pp[2]])
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
	# jez u vtoku nahonu mlyna (hladina vzduta na uroven nahonu) je stavba jako brod - stejna vyjimka a dosah jako test
	# smyslu breh_toku a dil_okraj (toky_tvar breh_sirka_m + 3 m od prvniho bodu nahonu, tools/krok_b/mlyn_voda.json)
	var mv: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://tools/krok_b/mlyn_voda.json"))
	if mv is Dictionary and (mv as Dictionary).has("nahon"):
		var b0: Array = mv["nahon"]["body"][0]
		var w0: Vector3 = sv._mlyn_inv.affine_inverse() * Vector3(float(b0[0]), 0.0, float(b0[2]))
		vynech.append([Vector2(w0.x, w0.z), float(tt["breh_sirka_m"]) + 3.0])
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
	# krizeni toku s osami cest (po stavbe hry): nejvic krizeni_max na tok, kazde v zaznamu prechodu pro ten tok
	n["krizeni_bez_prechodu"] = 0
	n["toku_nad_max"] = 0
	var prech: Array = P.cti("cesty", "prechody")
	for tk: Dictionary in P.cti("voda", "toky"):
		var o: Array = tk["osa_xzy"]
		var kr := 0
		for oc: Dictionary in sv.cesty_osy:
			var cp: PackedVector2Array = oc["p"]
			for k in cp.size() - 1:
				for i in o.size() - 1:
					var a := Vector2(float(o[i][0]), float(o[i][1]))
					var b := Vector2(float(o[i + 1][0]), float(o[i + 1][1]))
					var x: Variant = Geometry2D.segment_intersects_segment(a, b, cp[k], cp[k + 1])
					if x == null:
						continue
					kr += 1
					var ma := prech.any(func(pr: Dictionary) -> bool: return String(pr["tok"]) == String(tk["id"]) and (x as Vector2).distance_to(Vector2(float(pr["stred"][0]), float(pr["stred"][1]))) < float(pr["polomer_m"]))
					if not ma:
						n["krizeni_bez_prechodu"] += 1
						print("KORYTO krizeni_bez_prechodu (%.0f, %.0f) %s" % [(x as Vector2).x, (x as Vector2).y, tk["id"]])
		if kr > int(pt["krizeni_max"]):
			n["toku_nad_max"] += 1
			print("KORYTO krizeni_nad_max (%.0f, %.0f) %s %d krizeni" % [float(o[0][0]), float(o[0][1]), tk["id"], kr])
	_vysledek("voda_v_korytu", n["suche"] == 0 and n["pres_breh"] == 0 and n["soubeh"] == 0 and n["krizeni_bez_prechodu"] == 0 and n["toku_nad_max"] == 0, str(n))


## Site natazene (pasma.test _hrana_max_m): trojuhelnik siti vsi s hranou delsi nez hrana_max_m.
func _v_pudorysu_domu(body: Array, okap: float) -> bool:
	for d: Dictionary in sv._domy:
		if float(d["L"]) <= 0.0:
			continue
		var ok := true
		for p: Vector3 in body:
			var q := Vector2(p.x, p.z) - (d["c"] as Vector2)
			if absf(q.dot(d["au"])) > float(d["L"]) * 0.5 + okap or absf(q.dot(d["av"])) > float(d["W"]) * 0.5 + okap:
				ok = false
				break
		if ok:
			return true
	return false


func _site_natazene() -> void:
	var lim := float(sv.pasma()["test"]["hrana_max_m"])
	var okap := float(sv.pasma()["budova"]["okap_m"])
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
			# dlouha plocha cela v pudorysu jednoho domu vcetne okapu (strecha 16,8 m dlouhe usedlosti, rozbor 10. 11. r. 28)
			# neni natazeni - natazeny dil vede ze stareho mista na nove, tedy mimo pudorys
			if m > lim and not _v_pudorysu_domu([a, b, c], okap):
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
	# plamen louce v obraze (9. 11.: ruka telem nedosahne do zaberu - rameno 0,3 m za kamerou; jako v KCD ruka
	# u spodniho okraje, louc s plamenem v obraze)
	v_obraze.call("hand_r")
	var hn: Node3D = main.predmety.get("_hand")
	var plamen := hn.global_transform * (main.predmety.SVETLA["louc"][0] as Vector3)
	var sp0 := cam.unproject_position(plamen) / Vector2(cam.get_viewport().get_visible_rect().size)
	print("ZABER plamen louce obraz %s" % sp0.snapped(Vector2.ONE * 0.01))
	if cam.is_position_behind(plamen) or sp0.x < okraj or sp0.x > 1.0 - okraj or sp0.y < okraj or sp0.y > 1.0 - okraj:
		chyby.append("louc")
		print("ZABER louc (%.0f, %.0f) plamen louce mimo obraz" % [player.global_position.x, player.global_position.z])
	# Misa 0.99994 (r. 73) „ruka s louci se trepe a drzi ji spatne“: v chuzi louc v uchopu z dat (natoceni louce vuci
	# ruce = jizda.json telo.drzeni.louc rot_st) a ruka v obraze bez skoku mezi snimky
	var ih := ks.find_bone("hand_r")
	var rs: Array = (Pravidla.cti("jizda", "telo", "drzeni", "louc") as Dictionary)["rot_st"]
	var uchop := Basis.from_euler(Vector3(deg_to_rad(float(rs[0])), deg_to_rad(float(rs[1])), deg_to_rad(float(rs[2]))))
	var minule := Vector2.INF
	var skok := 0.0
	var uchop_st := 0.0
	for kn in ["clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"]:
		var ib := ks.find_bone(kn)
		print("ZABER %s kamera %s" % [kn, (cam.global_transform.affine_inverse() * (ks.global_transform * ks.get_bone_global_pose(ib).origin)).snapped(Vector3.ONE * 0.01)])
	player.velocity = Vector3(1.4, 0.0, 0.0)
	for _i in 40:
		await get_tree().process_frame
		var bh := (ks.global_transform * ks.get_bone_global_pose(ih)).basis.orthonormalized()
		for ch in (telo.get("ruka_r") as Node3D).get_children():
			var lb := (bh.inverse() * (ch as Node3D).global_basis.orthonormalized())
			uchop_st = maxf(uchop_st, rad_to_deg(lb.get_rotation_quaternion().angle_to(uchop.get_rotation_quaternion())))
		# skok ruky v soustave kamery (m za snimek): pohyb kamery a perspektiva u oka nemeri trepani
		var hk := cam.global_transform.affine_inverse() * (ks.global_transform * ks.get_bone_global_pose(ih).origin)
		var sp := Vector2(hk.x, hk.y) + Vector2(0.0, hk.z) * 0.0
		if minule != Vector2.INF and _i > 5:
			skok = maxf(skok, sp.distance_to(minule))
		minule = sp
	player.velocity = Vector3.ZERO
	print("ZABER louc v chuzi: odchylka uchopu %.1f st, nejvetsi skok ruky %.3f m za snimek (soustava kamery)" % [uchop_st, skok])
	if uchop_st > 5.0:
		chyby.append("louc mimo uchop %.0f st" % uchop_st)
	if skok > 0.01:
		chyby.append("ruka s louci skace %.3f m" % skok)
	main.predmety.hold("", false)
	var kun: Node = main.get("kun")
	if kun:
		player.global_position = (kun as Node3D).global_position + Vector3(1.5, 0.3, 0)
		kun.nasedni(player)
		# jezdec vidi ruce na otezich, kdyz se podiva na krk kone (jizda.json telo.otezi.test_pohled_st): ruce nad
		# kohoutkem jsou ~60 st. pod vodorovnou oci - v rovnem pohledu (svisle pole 70 st.) je nevidi nikdo (r. 73 rozbor)
		player.pitch = deg_to_rad(float((Pravidla.cti("jizda", "telo", "otezi") as Dictionary)["test_pohled_st"]))
		player.yaw = (kun as Node3D).rotation.y           # pohled po smeru kone (driv zustal pohled z chuze k nemu)
		for _i in 30:
			await get_tree().physics_frame
		print("ZABER otezi: pitch hrace %.1f st, kamera %.1f st (svet)" % [rad_to_deg(float(player.pitch)), rad_to_deg(cam.global_basis.z.angle_to(Vector3(cam.global_basis.z.x, 0.0, cam.global_basis.z.z))) * signf(-cam.global_basis.z.y)])
		for r in ["hand_r", "hand_l"]:
			if not v_obraze.call(r):
				chyby.append("otezi " + r)
				print("ZABER otezi (%.0f, %.0f) %s mimo obraz" % [player.global_position.x, player.global_position.z, r])
		# Misa 9. 11. r. 86 (snimek 17: chybi otezi): remeny od udidla (krouzky u huby, obe strany hlavy) do dlani
		var ot: Node = telo.get("_otezi")
		if ot == null or not (ot as Node3D).visible or (ot.get("konce") as Array).size() < 4:
			chyby.append("otezi nejsou")
		else:
			var kc: Array = ot.get("konce")
			var kk0: Skeleton3D = kun.get("_kostra")
			var hl1 := -1
			for i in kk0.get_bone_count():
				if kk0.get_bone_name(i).begins_with("BN_Head_01"):
					hl1 = i
			var hp := kk0.global_transform * kk0.get_bone_global_pose(hl1).origin
			var rozpeti := (kc[0] as Vector3).distance_to(kc[1])
			var od_hlavy := maxf((kc[0] as Vector3).distance_to(hp), (kc[1] as Vector3).distance_to(hp))
			var dl: Array = (Pravidla.cti("jizda", "kun", "otezi") as Dictionary)["dlan"]
			var dlan_r := ks.global_transform * (ks.get_bone_global_pose(ks.find_bone("hand_r")) * Vector3(float(dl[0]), float(dl[1]), float(dl[2])))
			print("ZABER otezi: udidla %s / %s, rozpeti %.2f m, od kosti hlavy %.2f m, konec v dlani %.3f m, delka k ruce %.2f m" % [(kc[0] as Vector3).snapped(Vector3.ONE * 0.01), (kc[1] as Vector3).snapped(Vector3.ONE * 0.01), rozpeti, od_hlavy, (kc[3] as Vector3).distance_to(dlan_r), (kc[1] as Vector3).distance_to(kc[3])])
			if rozpeti < 0.08 or rozpeti > 0.35:
				chyby.append("udidla %.2f m od sebe (huba 0,1-0,3)" % rozpeti)
			if od_hlavy > 0.45:
				chyby.append("udidlo %.2f m od kosti hlavy" % od_hlavy)
			if (kc[3] as Vector3).distance_to(dlan_r) > 0.02:
				chyby.append("otez neni v dlani")
		# Misa 0.9998 „sedlo na prdeli, hrac drepi“: panev nad sedlem, chodidla dolu podel boku (ne kolena nahore),
		# sedadlo sedla vystroje nad bodem sedla kone, sedlo pred polovinou trupu (ne na zadi)
		var sg: Vector3 = kun.sedlo_global()
		var kb: Basis = (kun as Node3D).global_transform.basis.orthonormalized()
		var bod := func(kost: String) -> Vector3:
			var i := ks.find_bone(kost)
			return kb.inverse() * ((ks.global_transform * ks.get_bone_global_pose(i)).origin - sg) if i >= 0 else Vector3.INF
		var pv: Vector3 = bod.call("pelvis")
		print("ZABER sed: panev %s koleno %s chodidlo %s (soustava kone od sedla)" % [pv, bod.call("calf_l"), bod.call("foot_l")])
		if Vector2(pv.x, pv.z).length() > 0.1 or pv.y < 0.0 or pv.y > 0.2:
			chyby.append("panev mimo sedlo %s" % pv)
		for st in ["l", "r"]:
			var ko: Vector3 = bod.call("calf_" + st)
			var ch: Vector3 = bod.call("foot_" + st)
			if not (ko.y < -0.1 and ch.y < ko.y - 0.3):
				chyby.append("noha %s nevisi dolu (koleno %.2f, chodidlo %.2f m pod sedlem)" % [st, -ko.y, -ch.y])
		var ksl: Vector3 = (kun as Node3D).global_transform.affine_inverse() * sg
		for c in (kun as Node3D).get_children():
			if String(c.name).begins_with("vystroj_sedlo") and c is Node3D:
				var bb := AABB()
				var prvni := true
				for mi in (c as Node3D).find_children("*", "MeshInstance3D", true, false):
					var b2 := (kun as Node3D).global_transform.affine_inverse() * ((mi as MeshInstance3D).global_transform * (mi as MeshInstance3D).get_aabb())
					bb = b2 if prvni else bb.merge(b2)
					prvni = false
				if not prvni and (ksl.z < bb.position.z or ksl.z > bb.end.z):
					chyby.append("bod sedla mimo sedlo vystroje")
		# sedadlo blizko kohoutku nez kycli kone: pred pulkou mezi kosti kohoutku (kohoutek_kosti) a panve (Pelvis)
		var kk: Skeleton3D = kun.get("_kostra")
		var z_koh := INF
		var z_pan := INF
		for i in kk.get_bone_count():
			var n := kk.get_bone_name(i)
			var z := ((kun as Node3D).global_transform.affine_inverse() * (kk.global_transform * kk.get_bone_global_pose(i)).origin).z
			if n.begins_with(String((Pravidla.cti("jizda", "kun", "kohoutek_kosti") as Array).back()) + "_"):
				z_koh = z
			if n.contains("Pelvis"):
				z_pan = z
		print("ZABER sedlo z %.2f, kohoutek z %.2f, panev kone z %.2f" % [ksl.z, z_koh, z_pan])
		if z_koh != INF and z_pan != INF and ksl.z > (z_koh + z_pan) * 0.5:
			chyby.append("sedlo vzadu na zadi (z %.2f, kohoutek %.2f, panev %.2f)" % [ksl.z, z_koh, z_pan])
		kun.sesedni()
		player.pitch = 0.0
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
	# Misa 0.994 mlyn c (598, 904): teren dilu (Mlyn_Teren, mlyn_teren) pod hladinou potoka dilu a napojeni lednice
	# (svet._mlyn_teren_koryto) - po 0,5 m podel osy toku v dilu a useku lednice_napojeni
	var nad := 0
	for tk: Dictionary in P.cti("voda", "toky"):
		var o: Array = tk["osa_xzy"]
		for i in o.size() - 1:
			for k in 4:
				var t := k / 4.0
				var x := lerpf(float(o[i][0]), float(o[i + 1][0]), t)
				var z := lerpf(float(o[i][1]), float(o[i + 1][1]), t)
				var mt: Vector2 = sv.mlyn_teren(x, z)
				var hl := lerpf(float(o[i][2]), float(o[i + 1][2]), t)
				if mt.x != INF and mt.x > hl - 0.05:
					nad += 1
					if nad <= 6:
						print("MLYN teren_nad_vodou (%.1f, %.1f) teren dilu %.2f nad hladinou %.2f" % [x, z, mt.x, hl])
	var ln: Dictionary = d.get("lednice_napojeni", {})
	if not ln.is_empty():
		for k in 9:
			var t := k / 8.0
			var x := lerpf(float(ln["a"][0]), float(ln["b"][0]), t)
			var z := lerpf(float(ln["a"][2]), float(ln["b"][2]), t)
			var mt: Vector2 = sv.mlyn_teren(x, z)
			var hl := lerpf(float(ln["a"][1]), float(ln["b"][1]), t)
			if mt.x != INF and mt.x > hl - 0.05:
				nad += 1
				print("MLYN teren_nad_vodou (%.1f, %.1f) lednice: teren dilu %.2f nad hladinou %.2f" % [x, z, mt.x, hl])
	if nad > 0:
		chyby.append("teren dilu nad vodou toku v %d bodech" % nad)
	# Misa 0.99993 r. 54 (snimek misa_6_11/23): breh potoka v dilu ostra hrana (sraz po 1 m mrizce, skala zem.gdshader).
	# Napric osou toku od kraje vody do mlyn.dil.breh_svah_pas_m po 0,5 m: sklon terenu dilu na 1 m nejvys toky_tvar.breh_max_st
	var tt: Dictionary = P.cti("voda", "toky_tvar")
	var bmax := float(tt["breh_max_st"])
	var jez := Vector3(0.0, 0.0, -1.0)            # jez u vtoku nahonu = stavba (jako breh_toku, dil_okraj)
	var mvj: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://tools/krok_b/mlyn_voda.json"))
	if mvj is Dictionary and (mvj as Dictionary).has("nahon"):
		var jb: Array = mvj["nahon"]["body"][0]
		var jw: Vector3 = sv._mlyn_inv.affine_inverse() * Vector3(float(jb[0]), 0.0, float(jb[2]))
		jez = Vector3(jw.x, jw.z, float(tt["breh_sirka_m"]) + 3.0)
	var sraz := 0
	var nej_st := 0.0
	for tk: Dictionary in P.cti("voda", "toky"):
		var o: Array = tk["osa_xzy"]
		var pw := float(tk["sirka_m"]) * 0.5
		for i in o.size() - 1:
			var a := Vector2(float(o[i][0]), float(o[i][1]))
			var b := Vector2(float(o[i + 1][0]), float(o[i + 1][1]))
			if sv.mlyn_teren(a.x, a.y).x == INF or a.distance_to(b) < 0.01:
				continue
			var nrm := (b - a).normalized().orthogonal()
			for sg: float in [-1.0, 1.0]:
				var k := 0.0
				while k + 1.0 <= float(d["breh_svah_pas_m"]):
					var p0 := a + nrm * sg * (pw + k)
					var p1 := a + nrm * sg * (pw + k + 1.0)
					var y0: float = sv.mlyn_teren(p0.x, p0.y).x
					var y1: float = sv.mlyn_teren(p1.x, p1.y).x
					if y0 != INF and y1 != INF and sv.od_vody(p0.x, p0.y) >= -0.05 and p0.distance_to(Vector2(jez.x, jez.y)) >= jez.z:
						var st := rad_to_deg(atan(absf(y1 - y0)))
						nej_st = maxf(nej_st, st)
						if st > bmax + 0.5:                 # 0,5 st zaokrouhleni: svah presne breh_max_st je v mezi
							sraz += 1
							if sraz <= 6:
								print("MLYN breh_sraz (%.1f, %.1f) %s %.0f st (%.2f -> %.2f m)" % [p0.x, p0.y, tk["id"], st, y0, y1])
					k += 0.5
	if sraz > 0:
		chyby.append("breh toku v dilu strmejsi nez %.0f st v %d bodech (nejvic %.0f st)" % [bmax, sraz, nej_st])
	print("MLYN breh toku v dilu: nejvetsi sklon %.0f st, srazu %d" % [nej_st, sraz])
	_vysledek("mlyn", chyby.is_empty(), "dveri %d %s" % [dvere, str(chyby)])


## Breh hladky (pasma.test _breh_hladky): okraj vody bez zubu, hladina bez dlouhe roviny a schodu.
func _breh_hladky() -> void:
	var P = preload("res://scripts/pravidla.gd")
	var pt: Dictionary = sv.pasma()["test"]
	var sp := player.get_world_3d().direct_space_state
	sv.kolize_vse(true)
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
	var vynech: Array = []
	var md: Dictionary = P.cti("voda", "mlyn")["dil"]
	vynech.append([Vector2(float(md["stred"][0]), float(md["stred"][1])), 20.0 * sqrt(2.0) + float(sv.pasma()["dil"]["napojeni_m"])])
	for k in ["rybnik_lhota", "rybnik_tvrz"]:
		var r: Dictionary = P.cti("voda", k)
		vynech.append([Vector2(float(r["stred"][0]), float(r["stred"][1])), float(r.get("polomer_m", r.get("voda_polomer_m", 12.0))) + 4.0])
	for pr: Dictionary in P.cti("cesty", "prechody"):
		vynech.append([Vector2(float(pr["stred"][0]), float(pr["stred"][1])), float(pr.get("polomer_m", 8.0))])
	# osy: [id, body Vector2, hladiny, pul sirky, krok vzorku, krok kolmo]
	var osy: Array = []
	for tk: Dictionary in P.cti("voda", "toky"):
		var b := PackedVector2Array()
		var hl := PackedFloat32Array()
		for q: Array in tk["osa_xzy"]:
			b.append(Vector2(float(q[0]), float(q[1])))
			hl.append(float(q[2]))
		osy.append([String(tk["id"]), b, hl, float(tk["sirka_m"]) * 0.5, 1.0, 0.1])
	if sv.koryto:
		osy.append(["bystrice", sv.koryto.get("body"), sv.koryto.get("hladiny"), float(P.cti("voda", "potok")["pulsirka_vody_m"]), 2.0, 0.25])
	var n := {"zub": 0, "rovina": 0, "schod": 0, "bodu": 0}
	for o: Array in osy:
		var b: PackedVector2Array = o[1]
		var hl: PackedFloat32Array = o[2]
		var kr := float(o[4])
		var hrany := {-1.0: [], 1.0: []}
		var stanice: Array = []
		var s := 0.0
		var rov := 0.0
		var hl_minule := NAN
		for i in b.size() - 1:
			var L := b[i].distance_to(b[i + 1])
			while s < L:
				var f := s / maxf(L, 1e-4)
				var q := b[i].lerp(b[i + 1], f)
				var h := lerpf(hl[i], hl[i + 1], f)
				s += kr
				if vynech.any(func(v: Array) -> bool: return q.distance_to(v[0]) < float(v[1])):
					for sd: float in [-1.0, 1.0]:
						(hrany[sd] as Array).append(NAN)
					stanice.append(q)
					hl_minule = NAN
					rov = 0.0
					continue
				n["bodu"] += 1
				# hladina: schod a rovina (tekouci voda)
				if not is_nan(hl_minule):
					if hl_minule - h > float(pt["schod_max_m"]):
						n["schod"] += 1
						if n["schod"] <= 20:
							print("KORYTO schod (%.0f, %.0f) %s %.2f m" % [q.x, q.y, o[0], hl_minule - h])
					rov = rov + kr if absf(hl_minule - h) < 1e-4 else 0.0
					if rov > float(pt["rovina_max_m"]):
						n["rovina"] += 1
						if n["rovina"] <= 20:
							print("KORYTO rovina (%.0f, %.0f) %s hladina vodorovne %.0f m" % [q.x, q.y, o[0], rov])
						rov = 0.0
				hl_minule = h
				var nr := (b[i + 1] - b[i]).normalized().orthogonal()
				for sd: float in [-1.0, 1.0]:
					var e := NAN
					var t := 0.0
					while t < float(o[3]) * 2.0 + 4.0:
						var yt: float = teren.call(q + nr * sd * t)
						if not is_nan(yt) and yt >= h:
							e = t
							break
						t += float(o[5])
					(hrany[sd] as Array).append(e)
				stanice.append(q)
			s -= L
		for sd: float in [-1.0, 1.0]:
			var a: Array = hrany[sd]
			for k in range(1, a.size() - 1):
				if is_nan(a[k]) or is_nan(a[k - 1]) or is_nan(a[k + 1]):
					continue
				var dz := absf(float(a[k]) - 0.5 * (float(a[k - 1]) + float(a[k + 1])))
				if dz > float(pt["breh_zub_m"]):
					n["zub"] += 1
					if n["zub"] <= 40:
						var qq: Vector2 = stanice[k]
						print("KORYTO zub (%.0f, %.0f) %s okraj %.2f m mimo sousedy" % [qq.x, qq.y, o[0], dz])
	_vysledek("breh_hladky", n["zub"] == 0 and n["rovina"] == 0 and n["schod"] == 0, str(n))


## Vztahy (pravidla/svet/vztahy.json): obecna kontrola dvojic druhu s povolenimi ze zaznamu. Vypis VZTAH <dvojice>
## (x, z) popis; souhrn podle dvojic a pocet pouzitych povoleni.
func _vztahy() -> void:
	var P = preload("res://scripts/pravidla.gd")
	var V: Dictionary = {"dvojice": P.cti("vztahy", "dvojice"), "druhy": P.cti("vztahy", "druhy"), "povoleni": P.cti("vztahy", "povoleni")}
	var pa: Dictionary = sv.pasma()
	var pt: Dictionary = pa["test"]
	sv.rostliny_vse(true)
	for _i in 5:
		await get_tree().process_frame
	# --- povoleni: dvojice -> seznam matcheru
	var plochy := {"dil:mlyn": [], "dil:rybnik_lhota": [], "prechody": []}
	var md: Dictionary = P.cti("voda", "mlyn")["dil"]
	plochy["dil:mlyn"].append([Vector2(float(md["stred"][0]), float(md["stred"][1])), 20.0 * sqrt(2.0)])
	var rl: Dictionary = P.cti("voda", "rybnik_lhota")
	plochy["dil:rybnik_lhota"].append([Vector2(float(rl["stred"][0]), float(rl["stred"][1])), 30.0 * sqrt(2.0)])
	for pr: Dictionary in P.cti("cesty", "prechody"):
		plochy["prechody"].append([Vector2(float(pr["stred"][0]), float(pr["stred"][1])), float(pr.get("polomer_m", 8.0))])
	var vrata: Array = []
	for e: Dictionary in sv.data.get("pohyb", []):
		var nm := String(e.get("name", ""))
		if String(e.get("kind", "")) == "vrata" or nm.contains("vrata") or nm.contains("branka"):
			var p3: Array = e.get("use", e["pos"])
			vrata.append(Vector2(float(p3[0]), float(p3[2])))
	var povoleno := {}
	var pouzito := {}
	var podm_id := {}
	# podminena pravidla dvojic (radce 18:20 bod 2: most nad vodou, mlyn na toku, vrata = pravidlo, ne vyjimka)
	for dv: String in V["dvojice"]:
		for pd: Dictionary in (V["dvojice"][dv] as Dictionary).get("podminky", []):
			if not povoleno.has(dv):
				povoleno[dv] = []
			(povoleno[dv] as Array).append(pd)
			podm_id[pd["id"]] = true
	for pv: Dictionary in V.get("povoleni", []):
		for dv: String in pv["dvojice"]:
			if not povoleno.has(dv):
				povoleno[dv] = []
			(povoleno[dv] as Array).append(pv)
	var smi := func(dv: String, q: Vector2, geom: Dictionary = {}) -> bool:
		for pv: Dictionary in povoleno.get(dv, []):
			var z := String(pv["zdroj"])
			var ok := false
			if plochy.has(z):
				ok = (plochy[z] as Array).any(func(a: Array) -> bool: return q.distance_to(a[0]) < float(a[1]))
			elif z == "pohyb:vrata":
				ok = vrata.any(func(v: Vector2) -> bool: return q.distance_to(v) < float(pa["budova"]["pruchod_m"]) + 1.5)
			elif z == "geometrie:na_sobe" or z == "geometrie:na_podlaze":
				ok = bool(geom.get(z, false))
			if ok:
				pouzito[pv["id"]] = int(pouzito.get(pv["id"], 0)) + 1
				return true
		return false
	var pocty := {}
	var kontrol := {}
	var chyba := func(dv: String, q: Vector2, co: String) -> void:
		pocty[dv] = int(pocty.get(dv, 0)) + 1
		if int(pocty[dv]) <= 25:
			print("VZTAH %s (%.0f, %.0f) %s" % [dv, q.x, q.y, co])
	# --- objekty: stromy, kere, kameny (instance MultiMesh), predmety (obal), ploty (body siti)
	var mriz := {}                                   # bunka 8 m -> [[druh, Vector2, r, y0, y1, jmeno]]
	var pridej := func(o: Array) -> void:
		var c := Vector2i(floori((o[1] as Vector2).x / 8.0), floori((o[1] as Vector2).y / 8.0))
		if not mriz.has(c):
			mriz[c] = []
		(mriz[c] as Array).append(o)
	for mmi in main.find_children("*", "MultiMeshInstance3D", true, false):
		var mm := (mmi as MultiMeshInstance3D).multimesh
		if mm == null or mm.mesh == null:
			continue
		var nm := String(mmi.name)
		var dr := ""
		if nm.begins_with("balvan") or nm.begins_with("skala") or nm.begins_with("kamen"):
			dr = "kamen"
		else:
			var sk := String((sv._druhy_hra.get(sv.druh_klice(nm.get_slice("_", 0) + "_" + nm.get_slice("_", 1)), sv._druhy_hra.get(sv.druh_klice(nm), {})) as Dictionary).get("skupina", ""))
			dr = "strom" if sk == "strom" else ("ker" if sk == "ker" else "")
		if dr == "":
			continue
		var ab := mm.mesh.get_aabb()
		var gx := (mmi as Node3D).global_transform
		# jen viditelne instance (za visible_instance_count jsou nepouzite s polohou 0, 0 - 28. 10. „kmen v kameni (0, 0)“)
		for i in (mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count):
			var xl := mm.get_instance_transform(i)
			if xl.origin == Vector3.ZERO and xl.basis == Basis():
				continue                              # nevyplnena instance (bunka se plni po davkach) - ne strom v (0, 0)
			var xf := gx * xl
			var s := xf.basis.get_scale().x
			var r := float(pt["kmen_polomer_m"]) * s if dr == "strom" else maxf(ab.size.x, ab.size.z) * 0.5 * s * (0.6 if dr == "kamen" else 0.4)
			pridej.call([dr, Vector2(xf.origin.x, xf.origin.z), r, xf.origin.y, xf.origin.y + ab.end.y * s, nm])
	var predm: Array = []
	for nd in main.find_children("Staticky_*", "Node3D", true, false) + main.predmety.placed.map(func(e: Dictionary) -> Node: return e.get("node")):
		if nd == null or not (nd is Node3D):
			continue
		var bb := AABB()
		var prvni := true
		for gi in (nd as Node).find_children("*", "VisualInstance3D", true, false):
			var b2 := (gi as VisualInstance3D).global_transform * (gi as VisualInstance3D).get_aabb()
			bb = b2 if prvni else bb.merge(b2)
			prvni = false
		if prvni:
			continue
		var o := ["predmet", Vector2(bb.get_center().x, bb.get_center().z), maxf(bb.size.x, bb.size.z) * 0.5, bb.position.y, bb.end.y, String(nd.name), bb]
		predm.append(o)
		pridej.call(o)
	var ploty: Array = []
	for nd in main.find_children("Vesnice_ploty*", "MeshInstance3D", true, false):
		var mi := nd as MeshInstance3D
		var f := mi.mesh.get_faces() if mi.mesh else PackedVector3Array()
		for i in range(0, f.size(), 9):
			var w := mi.global_transform * f[i]
			ploty.append(Vector2(w.x, w.z))
	var okoli := func(q: Vector2, r: float) -> Array:
		var out: Array = []
		for dx in range(floori((q.x - r) / 8.0), floori((q.x + r) / 8.0) + 1):
			for dz in range(floori((q.y - r) / 8.0), floori((q.y + r) / 8.0) + 1):
				out.append_array(mriz.get(Vector2i(dx, dz), []))
		return out
	# --- budovy: pudorys domu vsi (_domy) a stavby z lokace (kruh rovina_r_m)
	var v_domu := func(q: Vector2, okraj: float) -> Dictionary:
		for d: Dictionary in sv._domy:
			if float(d["y"]) == INF:
				continue
			var o3: Vector3 = (d["xf"] as Transform3D).origin
			if absf(q.x - o3.x) > 16.0 + okraj or absf(q.y - o3.z) > 16.0 + okraj:
				continue                              # rychle: dum je mensi nez 32 m (100 tisic rostlin x domy)
			var m: Dictionary = d["m"]
			var lq: Vector2 = sv._dum_mist(d, q.x, q.y)
			if absf(lq.x) < float(m["hw"]) + okraj and lq.y > float(m["b"]) - okraj and lq.y < float(m.get("ft", m["f"])) + okraj:
				return d
		return {}
	# budova|budova: stredy a rohy domu v jinem dome
	for d: Dictionary in sv._domy:
		if float(d["y"]) == INF:
			continue
		var m: Dictionary = d["m"]
		for lq: Vector2 in [Vector2(0, (float(m["b"]) + float(m["f"])) * 0.5), Vector2(float(m["hw"]) * 0.9, float(m["b"]) * 0.9), Vector2(-float(m["hw"]) * 0.9, float(m["f"]) * 0.9)]:
			var w: Vector3 = (d["xf"] as Transform3D) * Vector3(lq.x, 0, lq.y)
			var q := Vector2(w.x, w.z)
			for d2: Dictionary in sv._domy:
				if d2 == d or float(d2["y"]) == INF:
					continue
				var m2: Dictionary = d2["m"]
				var l2: Vector2 = sv._dum_mist(d2, q.x, q.y)
				if absf(l2.x) < float(m2["hw"]) and l2.y > float(m2["b"]) and l2.y < float(m2.get("ft", m2["f"])):
					chyba.call("budova|budova", q, "%s_%d v %s_%d" % [d["typ"], d["k"], d2["typ"], d2["k"]])
	var kmen_zed := float(pa["budova"]["kmen_od_zdi_m"])
	var breh := float(pa["voda"]["holy_breh_m"])
	for c: Vector2i in mriz:
		for o: Array in mriz[c]:
			var q: Vector2 = o[1]
			var dr: String = o[0]
			if dr == "strom":
				kontrol["budova|strom"] = int(kontrol.get("budova|strom", 0)) + 1
				kontrol["strom|posun"] = int(kontrol.get("strom|posun", 0)) + 1      # svet po posunu vsi: pudorysy a vstupy noveho mista
				if not (v_domu.call(q, kmen_zed) as Dictionary).is_empty() and not smi.call("budova|strom", q):
					chyba.call("budova|strom", q, "%s kmen blize nez %.1f m od zdi" % [o[5], kmen_zed])
				for o2: Array in okoli.call(q, 3.0):
					if o2 == o:
						continue
					for kk in ["strom|strom", "strom|kamen", "strom|predmet"]:
						kontrol[kk] = int(kontrol.get(kk, 0)) + 1
					var dd := q.distance_to(o2[1])
					if o2[0] == "strom" and dd < float(o[2]) + float(o2[2]) and q < (o2[1] as Vector2):
						chyba.call("strom|strom", q, "kmeny %s a %s se prekryvaji" % [o[5], o2[5]])
					elif o2[0] == "kamen" and dd < float(o2[2]):
						chyba.call("strom|kamen", q, "kmen %s v kameni %s" % [o[5], o2[5]])
					elif o2[0] == "predmet" and dd < float(o2[2]) and float(o2[3]) < float(o[4]):
						chyba.call("strom|predmet", q, "kmen %s v predmetu %s" % [o[5], o2[5]])
			elif dr == "ker":
				kontrol["budova|ker"] = int(kontrol.get("budova|ker", 0)) + 1
				kontrol["ker|posun"] = int(kontrol.get("ker|posun", 0)) + 1      # svet po posunu vsi: pudorysy a vstupy noveho mista
				if not (v_domu.call(q, 0.0) as Dictionary).is_empty():
					chyba.call("budova|ker", q, "%s uvnitr stavby" % o[5])
			elif dr == "kamen":
				kontrol["budova|kamen"] = int(kontrol.get("budova|kamen", 0)) + 1
				kontrol["kamen|posun"] = int(kontrol.get("kamen|posun", 0)) + 1      # svet po posunu vsi: pudorysy a vstupy noveho mista
				kontrol["voda|kamen"] = int(kontrol.get("voda|kamen", 0)) + 1
				if not (v_domu.call(q, 0.0) as Dictionary).is_empty():
					chyba.call("budova|kamen", q, "%s uvnitr stavby" % o[5])
				# kamen ve vode: vycniva vic nez 0,3 m nad hloubku toku (teren pod nim + hloubka)
				if sv.od_vody(q.x, q.y) < 0.0 and float(o[4]) - float(sv._vyska(q.x, q.y)) > 0.75 and not smi.call("voda|kamen", q):
					chyba.call("voda|kamen", q, "%s trci z vody (%.1f m nad dnem)" % [o[5], float(o[4]) - float(sv._vyska(q.x, q.y))])
	for o: Array in predm:
		for kk in ["budova|predmet", "teren|predmet", "voda|predmet", "predmet|predmet", "ker|predmet", "kamen|predmet"]:
			kontrol[kk] = int(kontrol.get(kk, 0)) + 1
		var q: Vector2 = o[1]
		var bb: AABB = o[6]
		var dm: Dictionary = v_domu.call(q, 0.0)
		if not dm.is_empty():
			var podl := float(dm["y"]) + float((dm["m"] as Dictionary).get("pod", 0.45))
			if bb.position.y < podl - 0.2 and not smi.call("budova|predmet", q, {"geometrie:na_podlaze": absf(bb.position.y - podl) < 0.2}):
				chyba.call("budova|predmet", q, "%s pod podlahou / ve zdi (spodek %.2f, podlaha %.2f)" % [o[5], bb.position.y, podl])
		else:
			var ty := float(sv._vyska(q.x, q.y))
			if bb.position.y - ty > float(pt["predmet_visi_m"]) and bb.position.y - ty < 2.0:
				chyba.call("teren|predmet", q, "%s visi %.2f m nad terenem" % [o[5], bb.position.y - ty])
		if sv.od_vody(q.x, q.y) < 0.0 and not smi.call("voda|predmet", q):
			chyba.call("voda|predmet", q, "%s ve vode" % o[5])
		for o2: Array in okoli.call(q, 3.0):
			if o2 == o or o2[0] != "predmet" or q >= (o2[1] as Vector2):
				continue
			var b2: AABB = o2[6]
			var prunik := bb.grow(-0.05).intersects(b2.grow(-0.05))
			var na_sobe := absf(bb.position.y - b2.end.y) < float(pt["na_sobe_m"]) or absf(b2.position.y - bb.end.y) < float(pt["na_sobe_m"])
			if prunik and not smi.call("predmet|predmet", q, {"geometrie:na_sobe": na_sobe}):
				chyba.call("predmet|predmet", q, "%s a %s se prekryvaji" % [o[5], o2[5]])
		for o2: Array in okoli.call(q, 2.0):
			if o2[0] == "ker" and q.distance_to(o2[1]) < float(o[2]) and float(o2[3]) < bb.end.y:
				chyba.call("ker|predmet", q, "ker %s v predmetu %s" % [o2[5], o[5]])
			elif o2[0] == "kamen" and q.distance_to(o2[1]) < float(o2[2]) * 0.8:
				chyba.call("kamen|predmet", q, "predmet %s v kameni %s" % [o[5], o2[5]])
	for q: Vector2 in ploty:
		for kk in ["voda|plot", "cesta|plot", "budova|plot", "plot|strom", "plot|kamen", "plot|predmet"]:
			kontrol[kk] = int(kontrol.get(kk, 0)) + 1
		if sv.od_vody(q.x, q.y) < 0.0 and not smi.call("voda|plot", q):
			chyba.call("voda|plot", q, "plot ve vode")
		var ck: Vector2 = sv.cesta_kraj_osa(q.x, q.y)
		if ck.y >= 0.0 and ck.x < 0.0 and not smi.call("cesta|plot", q):
			chyba.call("cesta|plot", q, "plot na jizdnim pasu cesty %d" % int(ck.y))
		if not (v_domu.call(q, -0.3) as Dictionary).is_empty():
			chyba.call("budova|plot", q, "plot uvnitr domu")
		for o2: Array in okoli.call(q, 1.5):
			if o2[0] == "strom" and q.distance_to(o2[1]) < float(o2[2]):
				chyba.call("plot|strom", q, "plot v kmeni %s" % o2[5])
			elif o2[0] == "kamen" and q.distance_to(o2[1]) < float(o2[2]) * 0.8:
				chyba.call("plot|kamen", q, "plot v kameni %s" % o2[5])
			elif o2[0] == "predmet" and (o2[6] as AABB).grow(-0.05).has_point(Vector3(q.x, (o2[6] as AABB).get_center().y, q.y)):
				chyba.call("plot|predmet", q, "plot v predmetu %s" % o2[5])
	# budovy u vody: dum vsi blize ke kraji vody nez breh_m
	for d: Dictionary in sv._domy:
		if float(d["y"]) == INF:
			continue
		kontrol["voda|budova"] = int(kontrol.get("voda|budova", 0)) + 1
		kontrol["budova|budova"] = int(kontrol.get("budova|budova", 0)) + 1
		kontrol["budova|posun"] = int(kontrol.get("budova|posun", 0)) + 1
		kontrol["plot|posun"] = int(kontrol.get("plot|posun", 0)) + 1
		var cq: Vector2 = d["c"]
		if sv.od_vody(cq.x, cq.y) < breh and not smi.call("voda|budova", cq):
			chyba.call("voda|budova", cq, "%s_%d u vody %.1f m" % [d["typ"], d["k"], sv.od_vody(cq.x, cq.y)])
	for kk in kontrol:
		print("POKRYTI %s %d" % [kk, kontrol[kk]])
	for kk in pouzito:
		print("%s %s %d" % ["PODMINKA" if podm_id.has(kk) else "POVOLENI", kk, pouzito[kk]])
	print("VZTAHY souhrn %s, povoleni pouzita %s" % [str(pocty), str(pouzito)])
	var n := 0
	for k in pocty:
		n += int(pocty[k])
	_vysledek("vztahy", n == 0, "%d chyb %s, povoleni %s" % [n, str(pocty), str(pouzito)])


## Matice vztahu - herni dvojice (radce 18:15/18:20): kun, postavy, hrac, LOD, svetla. Kazda provedena kontrola se
## pocita (POKRYTI <dvojice> n), chyba = radek VZTAH <dvojice> (x, z) - tools/kontrola_vztahu.py z nich dela pokryti
## a uspesnost k otisku exportu. Meze z vztahy.json meze (kun_zem_m, postava_odstup_m, stinu_max).
func _vztahy_hra() -> void:
	var P = preload("res://scripts/pravidla.gd")
	var pt: Dictionary = P.cti("vztahy", "meze")
	var kontrol := {}
	var chyb := {}
	var k := func(dv: String) -> void:
		kontrol[dv] = int(kontrol.get(dv, 0)) + 1
	var ch := func(dv: String, q: Vector2, co: String) -> void:
		chyb[dv] = int(chyb.get(dv, 0)) + 1
		if int(chyb[dv]) <= 10:
			print("VZTAH %s (%.1f, %.1f) %s" % [dv, q.x, q.y, co])
	var prechody: Array = []
	for pr: Dictionary in P.cti("cesty", "prechody"):
		prechody.append([Vector2(float(pr["stred"][0]), float(pr["stred"][1])), float(pr.get("polomer_m", 8.0))])
	var na_prechodu := func(q: Vector2) -> bool:
		return prechody.any(func(a: Array) -> bool: return q.distance_to(a[0]) < float(a[1]))
	var bez_lod := func(n: Node) -> int:
		var c := 0
		for g in n.find_children("*", "GeometryInstance3D", true, false):
			if (g as GeometryInstance3D).visibility_range_end <= 0.0 and (g as GeometryInstance3D).is_visible_in_tree():
				c += 1
		return c
	for _i in 10:
		await get_tree().physics_frame
	var space: PhysicsDirectSpaceState3D = player.get_world_3d().direct_space_state
	# --- kun (jizda.json kun, lokace.json kun)
	var kun: Node3D = main.kun
	if kun:
		var kq := Vector2(kun.global_position.x, kun.global_position.z)
		k.call("teren|kun")
		var dy: float = kun.global_position.y - float(sv._vyska(kq.x, kq.y))
		if absf(dy) > float(pt["kun_zem_m"]):
			ch.call("teren|kun", kq, "kun %.2f m od zeme" % dy)
		k.call("voda|kun")
		if float(sv.od_vody(kq.x, kq.y)) < 0.0 and not na_prechodu.call(kq):
			ch.call("voda|kun", kq, "kun stoji ve vode mimo prechod")
		k.call("cesta|kun")
		if (kun.get("_cesta_mriz") as Dictionary).is_empty():
			ch.call("cesta|kun", kq, "kun nema mriz cest - drzet_cestu nefunguje")
		k.call("kun|kolize")
		var tvary := kun.find_children("*", "CollisionShape3D", true, false)
		if not tvary.any(func(c: Node) -> bool: return (c as CollisionShape3D).shape is CylinderShape3D):
			ch.call("kun|kolize", kq, "kun bez kolize nohou (valec)")
		# kun narazi na vse, na co hrac (stejna maska) a na startu v nicem nestoji
		for dv in ["budova|kun", "plot|kun", "strom|kun", "kamen|kun", "predmet|kun"]:
			k.call(dv)
		var cb := kun as CollisionObject3D
		if (cb.collision_mask & player.collision_mask) != player.collision_mask:
			ch.call("budova|kun", kq, "maska kolize kone %d nepokryva masku hrace %d" % [cb.collision_mask, player.collision_mask])
		for cs in tvary:
			var qq := PhysicsShapeQueryParameters3D.new()
			qq.shape = (cs as CollisionShape3D).shape
			qq.transform = (cs as Node3D).global_transform
			qq.collision_mask = player.collision_mask
			qq.exclude = [cb.get_rid(), player.get_rid()]
			for h: Dictionary in space.intersect_shape(qq, 4):
				var nm := str((h["collider"] as Node).get_path())
				if not nm.contains("Teren"):
					ch.call("budova|kun", kq, "kun na startu v kolizi %s" % nm.right(50))
		k.call("kun|lod")
		var bl: int = bez_lod.call(kun)
		if bl > 0:
			ch.call("kun|lod", kq, "%d siti kone bez visibility_range" % bl)
	# --- postavy (lide.gd): body tras po posunu vsi - na zemi, mimo vodu (krome prechodu), kapsle v nicem nestoji
	var lide: Node = main.get_node_or_null("World/Lide")
	if lide == null:
		lide = get_tree().root.find_child("Lide", true, false)
	var kap := CapsuleShape3D.new()
	kap.radius = 0.25
	kap.height = 1.6
	var qp := PhysicsShapeQueryParameters3D.new()
	qp.shape = kap
	qp.collision_mask = player.collision_mask
	qp.exclude = [player.get_rid()]
	var starty: Array = []
	if lide:
		for c: Dictionary in lide.get("_lide"):
			# mista vsech bloku rozvrhu obyvatele (postavy.json) - kam postava chodi
			var tr: Array = []
			var doma: Array = []
			for bl: Dictionary in c["role"]["rozvrh"]:
				var mq: Vector2 = lide.call("_misto", c, String(bl["kde"]))[0]
				if not tr.has(mq):
					tr.append(mq)
					if String(bl["kde"]) == "domov":
						doma.append(mq)
				# obchuzka (celedin nosi): i mista obchuzky jsou trasa (Misa 0.992 „zase sel pres zed“ - nadvori)
				var cnt: Dictionary = (lide.get("P") as Dictionary)["cinnosti"].get(String(bl.get("cinnost", "")), {})
				for om: Variant in cnt.get("obchuzka", []):
					var oq: Vector2 = lide.call("_misto", c, String(om))[0]
					if not tr.has(oq):
						tr.append(oq)
			c["mista_testu"] = tr
			c["doma_testu"] = doma
			starty.append(tr[0])
			for q: Vector2 in tr:
				for dv in ["teren|postava", "voda|postava", "budova|postava", "plot|postava", "strom|postava", "kamen|postava",
						"predmet|postava", "posun|postava"]:
					k.call(dv)
				if float(sv.od_vody(q.x, q.y)) < 0.0 and not na_prechodu.call(q):
					ch.call("voda|postava", q, "bod trasy ve vode mimo prechod")
				var y := float(sv._vyska(q.x, q.y))
				if not is_finite(y):
					ch.call("teren|postava", q, "bod trasy bez terenu")
					continue
				qp.transform = Transform3D(Basis(), Vector3(q.x, y + 0.15 + kap.height * 0.5, q.y))
				for h: Dictionary in space.intersect_shape(qp, 4):
					var nm := str((h["collider"] as Node).get_path())
					if nm.contains("Teren"):
						continue
					var lo := nm.to_lower()
					var dv := "budova|postava"
					if lo.contains("plot") or lo.contains("vrat") or lo.contains("brank"):
						dv = "plot|postava"
					elif lo.contains("strom") or lo.contains("kmen"):
						dv = "strom|postava"
					elif lo.contains("kamen") or lo.contains("balvan"):
						dv = "kamen|postava"
					elif lo.contains("predmet"):
						dv = "predmet|postava"
					ch.call(dv, q, "trasa postavy v kolizi %s" % nm.right(50))
			k.call("postava|lod")
			var bp: int = bez_lod.call(c["uzel"])
			if bp > 0:
				ch.call("postava|lod", tr[0], "%d siti postavy bez visibility_range" % bp)
		var od := float(pt["postava_odstup_m"])
		var hq := Vector2(player.global_position.x, player.global_position.z)
		for i in starty.size():
			k.call("postava|kolize")
			k.call("hrac|postava")
			if hq.distance_to(starty[i]) < od:
				ch.call("hrac|postava", starty[i], "postava startuje v hraci")
			for j in range(i + 1, starty.size()):
				k.call("postava|postava")
				if (starty[i] as Vector2).distance_to(starty[j]) < od:
					ch.call("postava|postava", starty[i], "dve postavy na jednom miste")
	# --- predmety a ploty: kazda geometrie ma dosah (predmety.gd podle velikosti) - nic se nekresli pres celou mapu
	for rec: Dictionary in main.predmety.placed:
		var nd: Node = rec.get("node")
		if nd == null:
			continue
		var plot := String(rec["id"]).contains("plot") or String(rec["id"]).contains("vrat") or String(rec["id"]).contains("brank")
		var dv := "plot|lod" if plot else "predmet|lod"
		k.call(dv)
		var bpr: int = bez_lod.call(nd)
		if bpr > 0:
			ch.call(dv, Vector2(float(rec["p"].x), float(rec["p"].z)), "%s: %d siti bez dosahu" % [rec["id"], bpr])
	# --- postavy na ulici (start do napojeni na cestu): cela trasa po cesta (kraj cesty <= postava_kraj_cesty_m);
	# delnici v lome a na nadvori chodi u pracoviste (trasa nezacina u cesty) - podminka pracoviste
	if lide:
		if lide.get("_g").get_point_count() == 0:
			lide.call("_graf")
		for c: Dictionary in lide.get("_lide"):
			# chuze mezi misty rozvrhu vede po siti cest (body cesty krome posledniho = na ose cesty)
			var tr2: Array = c.get("mista_testu", [])
			for mi in range(1, tr2.size()):
				var cs: PackedVector2Array = lide.call("cesta", tr2[mi - 1], tr2[mi])
				# kazdy usek chuze bez zdi (paprsek v kolenou a hlave, Misa 0.992 „zase sel pres zed“)
				var pq: Vector2 = tr2[mi - 1]
				for qq: Vector2 in cs:
					# domov = uvnitr domu (postava skryta): posledni usek vede dvermi, branky (Pohyb_*) se otviraji
					if (c.get("doma_testu", []) as Array).has(qq) or (c.get("doma_testu", []) as Array).has(pq):
						pq = qq
						continue
					k.call("zed|postava")
					for hh: float in [0.5, 1.6]:
						var r0 := Vector3(pq.x, float(sv._vyska(pq.x, pq.y)) + hh, pq.y)
						var r1 := Vector3(qq.x, float(sv._vyska(qq.x, qq.y)) + hh, qq.y)
						var hr := space.intersect_ray(PhysicsRayQueryParameters3D.create(r0, r1, player.collision_mask, [player.get_rid()]))
						if not hr.is_empty() and not str((hr["collider"] as Node).get_path()).contains("Teren") and not str((hr["collider"] as Node).get_path()).contains("Pohyb_"):
							ch.call("zed|postava", Vector2(hr["position"].x, hr["position"].z), "%s usek (%.0f,%.0f)->(%.0f,%.0f) pres %s" % [
									c["id"], pq.x, pq.y, qq.x, qq.y, str((hr["collider"] as Node).get_path()).right(50)])
							break
					pq = qq
				for qi in range(1, cs.size() - 1):
					k.call("cesta|postava")
					var kq2: Vector2 = sv.cesta_kraj_osa(cs[qi].x, cs[qi].y)
					if kq2.x > float(pt["postava_kraj_cesty_m"]):
						ch.call("cesta|postava", cs[qi], "cesta postavy %s mimo cestu (%.1f m za krajem)" % [c["id"], kq2.x])
	# --- voda v dalce: site hladiny bez dosahu nebo s dosahem nad voda_dosah_min_m (zadny skok hladiny)
	for g in get_tree().root.find_children("*", "GeometryInstance3D", true, false):
		var gi := g as GeometryInstance3D
		var nm2 := String(gi.name).to_lower()
		if not (nm2.contains("voda") or nm2.contains("reka") or nm2.contains("potok") or nm2.contains("hladina")):
			continue
		k.call("voda|lod")
		if gi.visibility_range_end > 0.0 and gi.visibility_range_end < float(pt["voda_dosah_min_m"]):
			ch.call("voda|lod", Vector2(gi.global_position.x, gi.global_position.z), "%s dosah %.0f m" % [gi.name, gi.visibility_range_end])
	# --- posun vsi: na mistech starych chalup (stary_stred dal nez posun_duch_m od noveho mista) zadna geometrie
	# (duch stare vsi: impostor, LOD, zbytek site)
	var stare: Array = []
	var usd: Array = P.cti("lokace", "ves")["usedlosti"]
	for u: Dictionary in usd:
		var sq := Vector2(float(u["stary_stred"][0]), float(u["stary_stred"][1]))
		if usd.all(func(u2: Dictionary) -> bool: return sq.distance_to(Vector2(float(u2["novy_stred"][0]), float(u2["novy_stred"][1]))) > float(pt["posun_duch_m"])):
			stare.append(sq)
	for sq: Vector2 in stare:
		k.call("posun|lod")
	for g in get_tree().root.find_children("*", "MeshInstance3D", true, false):
		var mi2 := g as MeshInstance3D
		if not mi2.is_visible_in_tree() or mi2.mesh == null or String(mi2.name).begins_with("Teren"):
			continue
		var gp := Vector2(mi2.global_position.x, mi2.global_position.z)
		for sq: Vector2 in stare:
			if gp.distance_to(sq) < float(pt["posun_duch_m"]) * 0.5 and mi2.get_aabb().size.length() > 2.0:
				ch.call("posun|lod", sq, "na miste stare chalupy %s" % mi2.name)
	# --- kaminky: lod_bias z pasma.skala (ne jehlany v dalce)
	var bias := float(sv.pasma()["skala"]["kamen_lod_bias"])
	for mm in get_tree().root.find_children("*", "MultiMeshInstance3D", true, false):
		var mmi := mm as MultiMeshInstance3D
		if mmi.multimesh and mmi.multimesh.mesh and String(mmi.multimesh.mesh.resource_name + mmi.name).to_lower().contains("kamen"):
			k.call("kamen|lod")
			if mmi.lod_bias < bias - 0.01:
				ch.call("kamen|lod", Vector2(mmi.global_position.x, mmi.global_position.z), "lod_bias %.1f < %.1f" % [mmi.lod_bias, bias])
	# --- svetla v noci: stinova svetla nejvys stinu_max (vykon tabletu, life.gd dle kvality + svetlo hrace)
	main.day.set_time("noc", 0.01)
	for _f in 30:
		await get_tree().process_frame
	var stin := 0
	for l in get_tree().root.find_children("*", "Light3D", true, false):
		var lt := l as Light3D
		if not (lt is DirectionalLight3D) and lt.shadow_enabled and lt.is_visible_in_tree():
			stin += 1
	k.call("svetlo|svetlo")
	if stin > int(pt["stinu_max"]):
		ch.call("svetlo|svetlo", Vector2(player.global_position.x, player.global_position.z), "%d svetel se stinem > %d" % [stin, int(pt["stinu_max"])])
	main.day.set_time("poledne", 0.01)
	for kk in kontrol:
		print("POKRYTI %s %d" % [kk, kontrol[kk]])
	var n := 0
	for kk in chyb:
		n += int(chyb[kk])
	_vysledek("vztahy_hra", n == 0, "%d chyb %s; kontrol %s" % [n, str(chyb), str(kontrol)])


## Vetrny mlyn na samote (Misa 28. 10.): dil stoji na zemi (patky do kun_zem_m), kridla se toci, dvere jsou zaznam
## pohybu, chalupa mlynare (usedlost 30) stoji, cesta k_vetraku konci u placu.
func _vetrak() -> void:
	var P = preload("res://scripts/pravidla.gd")
	var ve: Dictionary = P.cti("lokace", "vetrak")
	var sc := get_tree().root.find_child("Vetrak_dil", true, false) as Node3D
	if sc == null:
		_vysledek("vetrak", false, "dil Vetrak_dil chybi")
		return
	var q := Vector2(float(ve["stred"][0]), float(ve["stred"][1]))
	var dy: float = sc.global_position.y - float(sv._vyska(q.x, q.y))
	var kr := sc.find_child("Vetrak_Kridla", true, false) as Node3D
	var r0 := kr.rotation.z if kr else 0.0
	for _i in 30:
		await get_tree().process_frame
	var toci := kr != null and absf(kr.rotation.z - r0) > 0.01
	var dvere := (sv.data["pohyb"] as Array).any(func(e: Dictionary) -> bool: return String(e["name"]).begins_with("Pohyb_vetrak"))
	var chal := (sv._domy as Array).any(func(d: Dictionary) -> bool: return int(d["k"]) == 30 and float(d["y"]) != INF)
	var osa: Array = []
	for e: Dictionary in P.cti("cesty", "pesiny"):
		if e["id"] == "k_vetraku":
			osa = e["osa"]
	var konec := Vector2(float(osa[-1][0]), float(osa[-1][1])) if not osa.is_empty() else Vector2.INF
	var ok := absf(dy) < float(P.cti("vztahy", "meze")["kun_zem_m"]) and toci and dvere and chal and konec.distance_to(q) < float(ve["plac_r_m"]) + 2.0
	_vysledek("vetrak", ok, "y od zeme %.2f, kridla se toci %s, dvere %s, chalupa %s, konec cesty %.1f m od stredu" % [dy, toci, dvere, chal, konec.distance_to(q)])


## Sklep pod vezi (Misa 9. 11., lokace.json sklep_tvrz, blender/sklep.py): cesta hrace dolu i nahoru bez diry (Puchart:
## posledni schod ze sklepa byla dira), svetla vyska nad trasou (pasma.budova.svetla_vyska_m), teren mimo vez neni
## vyhlouben (nad chodbou je zem nadvori), v otvoru veze zadna zem (Teren/Nadvori) pres schody, kolize klenby a zdi
## tam, kde jsou videt; hrac postaveny na schody nepropadne.
func _sklep() -> void:
	var s: Dictionary = Pravidla.cti("lokace", "sklep_tvrz")
	var pas := float(sv.pasma()["budova"]["svetla_vyska_m"])
	var chyby: Array = []
	# bez fast_travel (headless: Tween bez tweeneru, await visel - beh sk_test2 10. 11.)
	player.place(Vector3(-22.0, 0.0, -12.0), Vector3(-25.0, 1.6, -12.0))
	for _i in 120:
		await get_tree().physics_frame
	var sp := player.get_world_3d().direct_space_state
	var y := float(s["y"])
	var sc: Dictionary = s["schody"]
	var n := roundi(-y / float(sc["stupen_vyska"]))
	var xs := (float(sc["x"][0]) + float(sc["x"][1])) * 0.5
	var zh := float(sc["z_horni"])
	var zd := zh + n * float(sc["stupen_hloubka"])
	var xc := (float(s["chodba"]["x"][0]) + float(s["chodba"]["x"][1])) * 0.5
	var kob: Array = s["kobky"]["z"]
	var zk := (float(kob[1][0]) + float(kob[1][1])) * 0.5
	# trasa [x, z, y ocekavana]: prizemi veze -> pod podestu -> schody dolu -> sklep -> chodba -> kobka 2
	var tr: Array = [[-22.5, -14.75, 0.0], [xs, -14.75, 0.0], [xs, zh, 0.0], [xs, zd, y], [xs, zd + 0.25, y], [xc, zd + 0.25, y],
			[xc, float(s["chodba"]["z"][0]) + 0.6, y], [xc, zk, y], [float(s["kobky"]["x"][1]) - 0.6, zk, y]]
	var cizi := func(col: Object) -> bool:
		var jm := str((col as Node).get_path()) if col is Node else ""
		return not jm.contains("Pohyb_") and col != player
	var box := BoxShape3D.new()
	box.size = Vector3(0.3, pas - 0.35, 0.3)
	var sq := PhysicsShapeQueryParameters3D.new()
	sq.shape = box
	var vzorku := 0
	for smer in 2:                     # 0 dolu, 1 nahoru (stejne body v opacnem poradi)
		var body: Array = tr.duplicate()
		if smer == 1:
			body.reverse()
		for i in body.size() - 1:
			var a: Array = body[i]
			var b: Array = body[i + 1]
			var d := Vector2(float(a[0]), float(a[1])).distance_to(Vector2(float(b[0]), float(b[1])))
			var m := maxi(1, ceili(d / 0.2))
			for k in m + 1:
				var t := float(k) / m
				var p := Vector3(lerpf(a[0], b[0], t), lerpf(a[2], b[2], t), lerpf(a[1], b[1], t))
				vzorku += 1
				var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(p + Vector3(0, 0.6, 0), p - Vector3(0, 1.0, 0)))
				if h.is_empty() or absf(float((h["position"] as Vector3).y) - p.y) > 0.3:
					chyby.append("%s %s: %s" % ["dolu" if smer == 0 else "nahoru", p.snapped(Vector3.ONE * 0.01), "dira" if h.is_empty() else "podlaha %.2f" % float((h["position"] as Vector3).y)])
					continue
				if smer == 1:
					continue
				var f := float((h["position"] as Vector3).y)
				if String((h["collider"] as Node).name).begins_with("Teren") or String((h["collider"] as Node).name).begins_with("Nadvori"):
					if p.y < -0.5:
						chyby.append("zem nadvori pres sklep %s" % p.snapped(Vector3.ONE * 0.01))
				sq.transform = Transform3D(Basis.IDENTITY, Vector3(p.x, f + 0.2 + box.size.y * 0.5, p.z))
				for hh: Dictionary in sp.intersect_shape(sq, 8):
					if cizi.call(hh["collider"]):
						chyby.append("hlava %s narazi do %s" % [p.snapped(Vector3.ONE * 0.01), String((hh["collider"] as Node).name)])
						break
	# teren nad chodbou (mimo vez) zustava: paprsek shora trefi zem nadvori nad klenbou
	for z: float in [-7.0, -4.0, -1.5]:
		var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(xc + 2.0, 5.0, z), Vector3(xc + 2.0, -5.0, z)))
		var ok := false
		var ex: Array[RID] = []
		for _k in 12:                  # vyloucene kolize se hromadi (driv jen posledni - paprsek se tocil mezi dvema, test visel)
			if h.is_empty() or float((h["position"] as Vector3).y) < -0.5:
				break
			var jm := String((h["collider"] as Node).name)
			if jm.begins_with("Teren") or jm.begins_with("Nadvori"):
				ok = true
				break
			ex.append((h["collider"] as CollisionObject3D).get_rid())
			var q := PhysicsRayQueryParameters3D.create(Vector3(xc + 2.0, 5.0, z), Vector3(xc + 2.0, -5.0, z))
			q.exclude = ex
			h = sp.intersect_ray(q)
		if not ok:
			chyby.append("nad sklepem z %.1f neni zem (teren vyhlouben mimo vez?)" % z)
	# klenba chodby: paprsek nahoru z podlahy trefi kolizi pod vrchem klenby (videt = kolize)
	var hv := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(xc, y + 0.5, zk), Vector3(xc, y + 4.0, zk)))
	var vrch := y + float(s["klenba"]["patka"]) + float(s["klenba"]["vzepeti"])
	if hv.is_empty() or absf(float((hv["position"] as Vector3).y) - vrch) > 0.15:
		chyby.append("klenba chodby: kolize %s, viditelna %.2f" % ["zadna" if hv.is_empty() else "%.2f" % float((hv["position"] as Vector3).y), vrch])
	# klenba sklepa pod vezi (Misa 9. 11. klenuty strop, ne tramy): paprsek nahoru uprostred trefi kolizi v hrebeni
	var ks: Dictionary = s["sklep"]["klenba"]
	var xsk := (float(s["sklep"]["x"][0]) + float(s["sklep"]["x"][1])) * 0.5
	var zsk := (float(s["sklep"]["z"][0]) + float(s["sklep"]["z"][1])) * 0.5
	var hk := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(xsk, y + 0.5, zsk), Vector3(xsk, y + 4.0, zsk)))
	if hk.is_empty() or absf(float((hk["position"] as Vector3).y) - float(ks["vrchol_y"])) > 0.15:
		chyby.append("klenba sklepa: kolize %s, viditelna %.2f" % ["zadna" if hk.is_empty() else "%.2f" % float((hk["position"] as Vector3).y), float(ks["vrchol_y"])])
	# hrac na schodech nepropadne (fyzika): horni, prostredni a dolni stupen
	var stoji: Array = []
	for t: float in [0.1, 0.5, 0.95]:
		var z := lerpf(zh, zd, t)
		var ye := lerpf(0.0, y, t)
		player.place(Vector3(xs, ye + 0.3, z), Vector3(xs, ye, z + 3.0))
		for _i in 90:
			await get_tree().physics_frame
		var yp := float(player.global_position.y)
		stoji.append("%.2f/%.2f" % [yp, ye])
		if yp < ye - 0.5:
			chyby.append("hrac na schodech propadl: z %.2f y %.2f (ocekavano %.2f)" % [z, yp, ye])
	print("SKLEP vzorku %d, hrac na schodech %s, chyby %s" % [vzorku, str(stoji), str(chyby.slice(0, 12))])
	_vysledek("sklep", chyby.is_empty(), "%d chyb %s; vzorku trasy %d (dolu i nahoru), hrac %s" % [chyby.size(), str(chyby.slice(0, 5)), vzorku, str(stoji)])


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
				if pos.x > 350.0 and pos.x < 650.0 and pos.z > 700.0 and pos.z < 1000.0 and gap > 0.6:
					print("VISI ves %s %.1f m @ (%.1f, %.1f, %.1f)" % [mmi.name, gap, pos.x, pos.y, pos.z])     # Misa 0.992 balvan ve vzduchu (420, 819)
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
			# pata trsu je v custom data; bez nich (nebo s barvami) jiny krok bufferu - pad focení f141 (index 13)
			if not mm.use_custom_data:
				continue
			var krok := 12 + (4 if mm.use_colors else 0) + 4
			var buf := mm.buffer
			n = mini(n, buf.size() / krok)
			for i in n:
				var o := xf * Vector3(buf[i * krok + krok - 3], buf[i * krok + krok - 2], buf[i * krok + krok - 1])
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
	var zatmeni := 0
	var max_ms := 0.0
	# PC bez GPU: kresleni v 0,25 x (vlakna louky a hlavni vlakno pracuji stejne, jen snimek je levny)
	var sc0 := get_viewport().scaling_3d_scale
	get_viewport().scaling_3d_scale = 0.25
	var n := int(OS.get_environment("TVRZ_SKOKU")) if OS.has_environment("TVRZ_SKOKU") else 9
	for k in n:
		var cl: Array = cile[k % 3]
		await main.fast_travel(cl[0], cl[1], 0.0, "test")
		# Misa 0.995 „po cestovani cerna obrazovka“: po navratu z cestovani zadne zatmeni (CanvasLayer vrstvy 30 s ColorRect)
		for cl2 in main.get_children():
			if cl2 is CanvasLayer and (cl2 as CanvasLayer).layer == 30 and not cl2.is_queued_for_deletion():
				for fr in cl2.get_children():
					if fr is ColorRect and (fr as ColorRect).color.a > 0.05:
						zatmeni += 1
						print("TELEPORT zatmeni (%.0f, %.0f) po cestovani zustalo (alfa %.2f)" % [cl[0].x, cl[0].z, (fr as ColorRect).color.a])
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
	_vysledek("teleport", uviz == 0 and zatmeni == 0, "zatmeni po cestovani %d, %d skoku bez padu, uviznuti %d, nejdelsi snimek pri rozhlizeni %.0f ms, bunek louky %d" % [zatmeni, n, uviz, max_ms,
			louka._bunky.size() if louka else -1])


## Misa 3. 11. (0.9996): „pri chuzi nejdriv zeleny rastr louky a az potom trava, na koni uplne“. Hrac jede rovne pres
## louku rychlosti chuze, behu a cvalu (pravidla/svet/hrac.json, jizda.json); kazdy snimek: bunky louky pred hracem blize
## nez pasma.test.trava_dorust_m, ktere nejsou postavene nebo maji hrubsi uroven, nez jejich vzdalenost potrebuje = pozde.
func _trava_dorust() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	if louka == null:
		_vysledek("trava_dorust", false, "louka chybi")
		return
	var mez := float(sv.pasma()["test"]["trava_dorust_m"])
	var a := Vector2(0.0, 170.0)
	var b := Vector2(-10.0, 540.0)
	var smer := (b - a).normalized()
	player.set_flying(true)
	var vys := []
	var ok := true
	# rychlosti z dat: chody kone (jizda.json kun.chody) - krok ~ chuze, cval, trysk ~ beh na koni
	var chody: Dictionary = Pravidla.cti("jizda", "kun", "chody")
	for rv: Array in [["krok", float(chody["krok"])], ["cval", float(chody["cval"])], ["trysk", float(chody["trysk"])]]:
		var v := float(rv[1])
		var q := a
		player.global_position = Vector3(q.x, sv._vyska(q.x, q.y) + 1.7, q.y)
		for f in 1800:                                 # usazeni: okoli hotove (po skoku), nejvys ~30 s
			await get_tree().process_frame
			if louka.okoli_hotove(mez + louka.BUNKA):
				break
		var pozde := 0
		var snimku := 0
		var nej := INF
		var nej_m := Vector2.ZERO
		var t0 := Time.get_ticks_msec()
		while q.distance_to(a) < minf(a.distance_to(b), v * 30.0):
			var dt := get_process_delta_time()
			q += smer * v * maxf(dt, 1.0 / 60.0)
			player.global_position = Vector3(q.x, sv._vyska(q.x, q.y) + 1.7, q.y)
			player.velocity = Vector3(smer.x * v, 0.0, smer.y * v)
			player.yaw = atan2(-smer.x, -smer.y)
			await get_tree().process_frame
			snimku += 1
			var spatne := false
			var c0 := Vector2i(floori(q.x / louka.BUNKA), floori(q.y / louka.BUNKA))
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					var c := c0 + Vector2i(dx, dz)
					var cen := Vector2((c.x + 0.5) * louka.BUNKA, (c.y + 0.5) * louka.BUNKA)
					if (cen - q).dot(smer) < -louka.BUNKA * 0.5:
						continue                       # za hracem
					var d: float = louka._vzdal_bunky(c, q)
					if d > mez:
						continue
					var bu: Dictionary = louka._bunky.get(c, {})
					var lv := int(bu.get("lvl", 0)) if louka._bunky.has(c) else 9      # prazdna bunka (cesta, les) je hotova bez uzlu
					if lv > louka._uroven(d):
						if not spatne and pozde < 3:
							print("TRAVA_POZDE %s q (%.0f, %.0f) bunka %s d %.1f ma %d potrebuje %d, ceka %s, stavba %d, bunek %d" % [rv[0], q.x, q.y, c, d, lv, louka._uroven(d), str(louka._ceka.has(c)), louka._stavba.size(), louka._bunky.size()])
						spatne = true
						if d < nej:
							nej = d
							nej_m = q
			if spatne:
				pozde += 1
		var txt := "%s %.1f m/s: pozde %d z %d snimku" % [rv[0], v, pozde, snimku]
		if pozde > 0:
			txt += ", nejbliz %.0f m u (%.0f, %.0f)" % [nej, nej_m.x, nej_m.y]
			ok = false
		vys.append(txt)
		print("TRAVA_DORUST %s, %d ms" % [txt, Time.get_ticks_msec() - t0])
	player.set_flying(false)
	_vysledek("trava_dorust", ok, " | ".join(vys))


## Misa 3. 11. (0.9996, desatkrat): „hnede klobouky“ na pesinach = podsit skenu koprivy (prizemni semenacek) zvetsena
## na vysku cele rostliny (0,7-1,4 m siroka placka). Kazda instance byliny s vyskou v tabulce (svet.VYSKA_BYLIN):
## vykreslena vyska nejvys horni mez tabulky a sirka nejvys pasma.test.bylina_sirka_nasobek x horni mez.
func _bylina_velikost() -> void:
	var nas := float(sv.pasma()["test"]["bylina_sirka_nasobek"])
	var smx: Dictionary = sv.pasma()["bylina"]["sirka_max_m"]
	var spatne := []
	for key: String in sv.bylina_max:
		var lim := Vector2.ZERO
		for pf: String in sv.VYSKA_BYLIN:
			if key.begins_with(pf):
				lim = sv.VYSKA_BYLIN[pf]
		var smax := lim.y * nas
		for pf2: String in smx:
			if key.begins_with(pf2):
				smax = float(smx[pf2])
		var m: Vector4 = sv.bylina_max[key]
		if m.y > lim.y * 1.05 or m.x > smax * 1.05:
			spatne.append("%s %.2f x %.2f m (mez %.2f x %.2f) u (%.0f, %.0f)" % [key, m.x, m.y, smax, lim.y, m.z, m.w])
	_vysledek("bylina_velikost", spatne.is_empty(), "druhu %d, prilis velke %d %s" % [sv.bylina_max.size(), spatne.size(), str(spatne.slice(0, 6))])

func _louka_profil() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	var n := 10000
	var c := Vector2i(0, 5)
	var kr: PackedByteArray = main.svet.kryti_tab.get(c, louka._kr_nic)
	var okr: PackedFloat32Array = louka._okraje(c)
	var cas := {}
	var fs := {
		"vzorek": func(x: float, z: float) -> void: louka._vzorek(x, z),
		"okraj": func(x: float, z: float) -> void: louka._okraj(okr, c, x, z),
		"divokost": func(x: float, z: float) -> void: sv.divokost(x, z),
		"kryto": func(x: float, z: float) -> void: louka._kryto(kr, c, x, z),
		"cesta_trava": func(x: float, z: float) -> void: sv.cesta_trava(x, z),
		"prah": func(x: float, z: float) -> void: louka._prah(x, z),
		"nizka": func(x: float, z: float) -> void: louka._nizka(x, z),
		"v_kruhu": func(x: float, z: float) -> void: sv.nadrz._v_kruhu(x, z) if sv.nadrz else 0.0,
		"ryb_vyska": func(x: float, z: float) -> void: sv.ryb_vyska(x, z),
		"terasa_svah": func(x: float, z: float) -> void: sv.terasa_svah(x, z),
		"v_zahrade": func(x: float, z: float) -> void: sv.v_zahrade(x, z),
		"v_nove_zahrade": func(x: float, z: float) -> void: sv.v_nove_zahrade(x, z),
		"v_pruchodu": func(x: float, z: float) -> void: sv.v_pruchodu(x, z),
		"v_trzisti": func(x: float, z: float) -> void: sv.v_trzisti(x, z),
		"v_budove": func(x: float, z: float) -> void: louka._v_budove(x, z),
		"kor": func(x: float, z: float) -> void: louka._kor.blizko(x, z) if louka._kor else [],
		"cesta_kraj_osa": func(x: float, z: float) -> void: sv.cesta_kraj_osa(x, z),
		"vyplnovy_mix": func(x: float, z: float) -> void: louka._vyplnovy_mix(sv.divokost(x, z), 0.0, 0.0),
		"zarez": func(x: float, z: float) -> void: louka._zarez(x, z, 0.0),
		"kryti_hodnota": func(x: float, z: float) -> void: louka._kryti_hodnota(kr, c, x, z),
		"zaznam": func(x: float, z: float) -> void: louka._zaznam([], c, x, 0.0, z, 0.0, 1.0, 1.0, 0, 0),
	}
	for k: String in fs:
		var f: Callable = fs[k]
		var t0 := Time.get_ticks_usec()
		for i in n:
			f.call(c.x * 32.0 + fmod(i * 0.37, 32.0), c.y * 32.0 + fmod(i * 0.61, 32.0))
		cas[k] = "%.1f us" % [(Time.get_ticks_usec() - t0) / float(n)]
	var t1 := Time.get_ticks_usec()
	var by: PackedByteArray = louka._rozsej(c)
	_vysledek("louka_profil", true, "na volani %s; cela bunka %.0f ms (%d B)" % [str(cas), (Time.get_ticks_usec() - t1) / 1000.0, by.size()])


## Hlidac scen (Misa 3. 11., pravidla/svet/mereni_trasa.json hlidac_sceny): kamera jede po trase tvrz -> les -> ves
## (osy cest), zapisuje typ sceny po usecich a doskoky (geometrie, ktera se objevi v zaberu blize nez doskok_m).
## Vystup build/trasa_sceny.json; je-li build/trasa_schvalena.json, vic doskoku nez ve schvalene = chyba.
func _trasa_sceny() -> void:
	var cfg: Dictionary = Pravidla.cti("mereni_trasa", "hlidac_sceny")
	var vozove: Array = Pravidla.cti("cesty", "vozove")
	var osy := {}
	for o: Dictionary in vozove:
		osy[String(o["id"])] = o["osa"]
	var hl: Array = osy["hlavni"]
	var od: Array = osy["odbocka_ves"]
	var napoj := Vector2(float(od[0][0]), float(od[0][1]))
	var body: Array[Vector2] = []
	for p: Array in hl:
		var q := Vector2(float(p[0]), float(p[1]))
		body.append(q)
		if q.distance_to(napoj) < 6.0:
			break
	for p: Array in od:
		body.append(Vector2(float(p[0]), float(p[1])))
	var cam: Camera3D = player.get("cam")
	var space := player.get_world_3d().direct_space_state
	var dosk := float(cfg["doskok_m"])
	var vz := float(cfg["vzorek_s"])
	var oci := float(cfg["oci_m"])
	var usek_m := float(cfg["usek_m"])
	var chody: Dictionary = Pravidla.cti("jizda", "kun", "chody")
	var vysl := {}
	player.set_flying(true)
	for rv: Array in [["chuze", float(chody["krok"])], ["cval", float(chody["cval"])]]:
		var v := float(rv[1])
		var i := 0
		var q := body[0]
		player.global_position = Vector3(q.x, sv._vyska(q.x, q.y) + 0.1, q.y)
		for f in 1800:
			await get_tree().process_frame
			var lk: Node = main.get_node_or_null("Louka")
			if lk == null or lk.okoli_hotove(80.0):
				break
		var videno := {}                         # instance id -> bylo viditelne
		for n in main.find_children("*", "GeometryInstance3D", true, false):
			videno[n.get_instance_id()] = (n as Node3D).is_visible_in_tree()
		var dosky: Array = []
		var useky: Array = []
		var ujeto := 0.0
		var t_vz := 0.0
		var obz: Array = []
		while i < body.size() - 1:
			var dt := 1.0 / 60.0
			var krok := v * dt
			while krok > 0.0 and i < body.size() - 1:
				var dd := q.distance_to(body[i + 1])
				if dd <= krok:
					krok -= dd
					q = body[i + 1]
					i += 1
				else:
					q = q + (body[i + 1] - q).normalized() * krok
					krok = 0.0
			ujeto += v * dt
			var smer := (body[mini(i + 1, body.size() - 1)] - q).normalized()
			var y: float = sv._vyska(q.x, q.y)
			player.global_position = Vector3(q.x, y + 0.1, q.y)
			player.velocity = Vector3(smer.x * v, 0, smer.y * v)
			player.yaw = atan2(-smer.x, -smer.y)
			player.pitch = 0.0
			await get_tree().process_frame
			t_vz += dt
			if t_vz < vz:
				continue
			t_vz = 0.0
			var cp := cam.global_position
			# doskoky: uzel nove v zaberu (novy nebo zviditelneny) blize nez doskok_m
			for n in main.find_children("*", "GeometryInstance3D", true, false):
				var g := n as GeometryInstance3D
				var id := g.get_instance_id()
				var vis := g.is_visible_in_tree()
				var bylo: bool = videno.get(id, false)
				videno[id] = vis
				if not vis or bylo:
					continue
				var bb := g.global_transform * g.get_aabb()
				var stred := bb.get_center()
				var d := maxf(0.0, cp.distance_to(stred) - bb.size.length() * 0.5)
				if d < dosk and cam.is_position_in_frustum(stred) and String(g.name) != "":
					if g.visibility_range_begin > 0.0 and d >= g.visibility_range_begin - 2.0:
						continue                      # LOD prechod na sve mezi (neni doskok)
					dosky.append([snappedf(q.x, 1), snappedf(q.y, 1), snappedf(d, 0.1), String(g.name).left(40)])
			# obzor: 9 paprsku vpred
			var ds: Array = []
			for k in 9:
				var a := deg_to_rad(-40.0 + 10.0 * k)
				var dirv := Vector3(sin(player.yaw + a) * -1.0, 0.0, cos(player.yaw + a) * -1.0)
				var pq := PhysicsRayQueryParameters3D.create(cp, cp + dirv * 1500.0)
				var h := space.intersect_ray(pq)
				ds.append(cp.distance_to(h["position"]) if not h.is_empty() else 1500.0)
			ds.sort()
			obz.append(float(ds[4]))
			if ujeto >= usek_m * (useky.size() + 1):
				obz.sort()
				var o := float(obz[obz.size() / 2]) if not obz.is_empty() else 0.0
				var typ := "A" if o < float(cfg["obzor_a_m"]) else ("C" if o > float(cfg["obzor_c_m"]) else "B")
				useky.append([snappedf(q.x, 1), snappedf(q.y, 1), typ, snappedf(o, 1)])
				obz.clear()
		var typy := ""
		for u: Array in useky:
			typy += String(u[2])
		vysl[rv[0]] = {"doskoky": dosky.size(), "priklady": dosky.slice(0, 12), "useky": useky, "typy": typy, "delka_m": snappedf(ujeto, 1)}
		print("TRASA_SCENY %s: %d m, doskoku %d, typy %s" % [rv[0], ujeto, dosky.size(), typy])
		for dk: Array in dosky.slice(0, 8):
			print("TRASA_DOSKOK %s %s" % [rv[0], str(dk)])
	player.set_flying(false)
	var f := FileAccess.open("res://build/trasa_sceny.json", FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(vysl, " "))
	var ok := true
	var srov := ""
	if FileAccess.file_exists("res://build/trasa_schvalena.json"):
		var sch: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://build/trasa_schvalena.json"))
		for k: String in vysl:
			if sch.has(k) and int(vysl[k]["doskoky"]) > int(sch[k]["doskoky"]):
				ok = false
				srov += " %s: doskoku %d > schvaleno %d" % [k, vysl[k]["doskoky"], sch[k]["doskoky"]]
	else:
		srov = " (schvalena verze zatim neni - build/trasa_schvalena.json)"
	_vysledek("trasa_sceny", ok, "chuze %d doskoku %s | cval %d doskoku %s%s" % [vysl["chuze"]["doskoky"], vysl["chuze"]["typy"], vysl["cval"]["doskoky"], vysl["cval"]["typy"], srov])


## Misa 4. 11.: „meris jen cesty, ja jezdim i na louce a v lese“ - jizda cvalem mimo cesty (louka s vysokou travou,
## les) ve vysce jezdce: kolik buněk louky a instanci v zaberu, pozdni trava (jako trava_dorust) a doskoky (jako
## trasa_sceny). Mista z jejich snimku 0.9997 se zasekem 17 FPS.
func _kun_terenem() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	var cam: Camera3D = player.get("cam")
	var chody: Dictionary = Pravidla.cti("jizda", "kun", "chody")
	var v := float(chody["cval"])
	var oci := float(Pravidla.cti("jizda", "kun", "kohoutek_m")) + float(Pravidla.cti("jizda", "kun", "oci_nad_sedlem_m"))
	var vys := []
	var ok := true
	player.set_flying(true)
	for tr: Array in [["louka", Vector2(-20, 300), Vector2(-30, 420)], ["les", Vector2(150, 905), Vector2(230, 870)]]:
		var a: Vector2 = tr[1]
		var b: Vector2 = tr[2]
		var smer := (b - a).normalized()
		var q := a
		player.global_position = Vector3(q.x, sv._vyska(q.x, q.y) + oci - 1.7, q.y)
		for f in 1800:
			await get_tree().process_frame
			if louka == null or louka.okoli_hotove(60.0):
				break
		var pozde := 0
		var snimku := 0
		var mm_max := 0
		var inst_max := 0
		var videno := {}
		for n in main.find_children("*", "GeometryInstance3D", true, false):
			videno[n.get_instance_id()] = (n as Node3D).is_visible_in_tree()
		var dosky := 0
		while q.distance_to(a) < a.distance_to(b):
			q += smer * v / 60.0
			var y: float = sv._vyska(q.x, q.y)
			player.global_position = Vector3(q.x, y + oci - 1.7, q.y)
			player.velocity = Vector3(smer.x * v, 0, smer.y * v)
			player.yaw = atan2(-smer.x, -smer.y)
			player.pitch = deg_to_rad(-8.0)
			await get_tree().process_frame
			snimku += 1
			if louka:
				var c0 := Vector2i(floori(q.x / louka.BUNKA), floori(q.y / louka.BUNKA))
				for dx in range(-1, 2):
					for dz in range(-1, 2):
						var c := c0 + Vector2i(dx, dz)
						var d: float = louka._vzdal_bunky(c, q)
						var lv := int((louka._bunky[c] as Dictionary).get("lvl", 0)) if louka._bunky.has(c) else 9
						if d < 20.0 and lv > louka._uroven(d):
							if pozde < 3:
								print("KUN_POZDE %s q (%.0f, %.0f) bunka %s d %.1f ma %d ceka %s stavba %d bunek %d hotove %d" % [tr[0], q.x, q.y, c, d, lv, louka._ceka.has(c), louka._stavba.size(), louka._bunky.size(), louka._hotove.size()])
							pozde += 1
							break
			if snimku % 15 == 0:
				var mmn := 0
				var inst := 0
				var cp := cam.global_position
				for n in main.find_children("*", "GeometryInstance3D", true, false):
					var g := n as GeometryInstance3D
					var vis := g.is_visible_in_tree()
					var bylo: bool = videno.get(g.get_instance_id(), false)
					videno[g.get_instance_id()] = vis
					if not vis:
						continue
					var bb := g.global_transform * g.get_aabb()
					if not cam.is_position_in_frustum(bb.get_center()) and bb.get_center().distance_to(cp) > bb.size.length():
						continue
					if g is MultiMeshInstance3D:
						mmn += 1
						var mm := (g as MultiMeshInstance3D).multimesh
						if mm:
							inst += mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
					if not bylo and maxf(0.0, cp.distance_to(bb.get_center()) - bb.size.length() * 0.5) < 45.0 \
							and not (g.visibility_range_begin > 0.0):
						dosky += 1
				mm_max = maxi(mm_max, mmn)
				inst_max = maxi(inst_max, inst)
		var t := "%s: pozde %d z %d snimku, v zaberu az %d MultiMeshu / %d instanci, doskoku %d" % [tr[0], pozde, snimku, mm_max, inst_max, dosky]
		print("KUN_TERENEM " + t)
		vys.append(t)
		ok = ok and pozde == 0
	player.set_flying(false)
	_vysledek("kun_terenem", ok, " | ".join(vys))


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


## Most (Misa 5. 11., 0.99991 u (205, 594): „cesta na most nevede, je vedle nej; proc trava roste na moste“):
## 1) osa cesty (svet.cesty_osy) navazuje na oba konce mostovky kazdeho mostu: na konci mostovky i na konci rovneho
##    najezdu (NAJEZD_DELKA, cesty.json prechody najezd_m) je osa do 0,5 m a rovnobezne s mostem;
##    tesne za koncem mostovky teren 8 cm pod prkny (najezd, bez schodu);
## 2) na mostovce zadny trs louky (louka._rozsej, vsechny zapnute vrstvy) ani rostlina z dat, ktera by sahala na
##    prkna (pata vys nez mostovka - 0,8 m = nejvyssi trs).
func _most() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	var nj: Array = sv._najezdy
	var chyby: Array = []
	var mostu := 0
	var trsu := 0
	for k in range(0, nj.size() - 1, 2):
		mostu += 1
		var osa: Vector2 = nj[k][1]
		var bok: Vector2 = nj[k][2]
		var pul_s := float(nj[k][3])
		var y_most := float(nj[k][4])
		var e0: Vector2 = nj[k][0]
		var e1: Vector2 = nj[k + 1][0]
		var c := (e0 + e1) * 0.5
		var pul_d := e0.distance_to(e1) * 0.5
		# 1) napojeni cesty
		for e: Array in [[e0, nj[k][1]], [e1, nj[k + 1][1]]]:
			for dal: float in [0.0, float(sv.NAJEZD_DELKA)]:
				var q: Vector2 = (e[0] as Vector2) + (e[1] as Vector2) * dal
				var best := INF
				var rov := 0.0
				for o: Dictionary in sv.cesty_osy:
					var pp: PackedVector2Array = o["p"]
					for i in pp.size() - 1:
						var b := Geometry2D.get_closest_point_to_segment(q, pp[i], pp[i + 1])
						if b.distance_to(q) < best:
							best = b.distance_to(q)
							rov = absf((pp[i + 1] - pp[i]).normalized().dot(osa))
				if best > 0.5 or rov < 0.98:
					chyby.append("most %d konec (%.1f, %.1f) +%.0f m: osa cesty %.1f m, rovnobeznost %.2f" % [mostu, q.x, q.y, dal, best, rov])
			# bez schodu: teren tesne za koncem mostovky (najezd_y: 8 cm pod prkny), profil cesty ho nesmi zariznout
			var qe: Vector2 = (e[0] as Vector2) + (e[1] as Vector2) * 0.5
			var ye: float = sv._vyska(qe.x, qe.y)
			if absf(ye - (y_most - 0.08)) > 0.3:
				chyby.append("most %d konec (%.1f, %.1f): teren %.2f, mostovka %.2f - schod" % [mostu, qe.x, qe.y, ye, y_most])
		# 2) trava na mostovce
		var bunky := {}
		for t in range(-int(pul_d), int(pul_d) + 1):
			for sb: float in [-pul_s, 0.0, pul_s]:
				var p := c + osa * t + bok * sb
				bunky[Vector2i(floori(p.x / 32.0), floori(p.y / 32.0))] = true
		var na_moste := func(x: float, z: float) -> bool:
			var d := Vector2(x, z) - c
			return absf(d.dot(osa)) < pul_d and absf(d.dot(bok)) < pul_s
		var vyp: Array = louka.get("_vypnute") if louka else []
		for cc: Vector2i in bunky:
			var by: PackedByteArray = louka._rozsej(cc) if louka else PackedByteArray()
			if by.is_empty():
				continue
			var o := 5 * 4
			for v in 5:
				var pocet := by.decode_u32(v * 4)
				for r in pocet:
					var x := cc.x * 32.0 + by.decode_u16(o) / 65535.0 * 32.0
					var z := cc.y * 32.0 + by.decode_u16(o + 2) / 65535.0 * 32.0
					var y := by.decode_s16(o + 4) / 100.0
					o += 12
					if not vyp.has(v) and na_moste.call(x, z) and y > y_most - 0.8:
						trsu += 1
						if trsu <= 10:
							chyby.append("trs vrstvy %d na mostovce (%.1f, %.1f) y %.2f (mostovka %.2f)" % [v, x, z, y, y_most])
		var rostlin := 0
		for key: String in sv.data["rostliny"]:
			for t: Array in sv.data["rostliny"][key]:
				if na_moste.call(float(t[3]), float(t[11])) and float(t[7]) > y_most - 0.8:
					rostlin += 1
					if rostlin <= 10:
						chyby.append("%s na mostovce (%.1f, %.1f) y %.2f" % [key, float(t[3]), float(t[11]), float(t[7])])
		trsu += rostlin
		print("MOST %d: stred (%.1f, %.1f), delka %.1f, mostovka %.2f, bunek louky %d" % [mostu, c.x, c.y, 2.0 * pul_d, y_most, bunky.size()])
	for ch: String in chyby:
		print("MOST ", ch)
	_vysledek("most", mostu > 0 and chyby.is_empty(), "mostu %d, trsu a rostlin na mostovce %d, chyb %d %s" % [mostu, trsu, chyby.size(), str(chyby.slice(0, 3))])


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


## Misa 0.9998 (rybnik Lhota, 4. 11.: „kameny porad levituji, uz jsem to dával nekolikrat“, pritok useknuty pred hladinou,
## tok pod valem): vysledny dil po hrazi a korytech toku (svet._ryb_hraz_toky), ne model.
## 1) kameny: kazdy souvisly kamen Rybnik_Kameny - nejnizsi bod spodku nad povrchem dilu nejvys pasma.test.predmet_visi_m;
## 2) okraj hladiny Rybnik_Voda: teren dilu pod okrajem ne niz nez hladina - predmet_visi_m (jinak hladina visi nad
##    snizenym brehem), krome mist pod hladinou toku (vtok, vypust);
## 3) toky pres dil (osa do pulsirka dilu + pas napojeni): teren dilu pod osou aspon hloubka_dno_min_m pod hladinou toku
##    (jinak tok pod valem = tunel) a nad osou voda (pas toku Toky_voda nebo hladina rybnika) az do rybnika.
func _rybnik_dil() -> void:
	if sv._ryb_y == INF:
		_vysledek("rybnik_dil", false, "dil rybnika Lhota neni")
		return
	var pt: Dictionary = sv.pasma()["test"]
	var visi := float(pt["predmet_visi_m"])
	var dno := float(pt["hloubka_dno_min_m"])
	var ryb_y: float = sv._ryb_y
	# hladiny nad bodem: trojuhelniky Toky_voda (do 60 m od dilu) a Rybnik_Voda v mrizce 2 m
	var hl_tok := {}
	var hl_ryb := {}
	for jm: String in ["Toky_voda", "Rybnik_Voda*", "Rybnik_lhota_voda*"]:
		var hladiny: Dictionary = hl_tok if jm == "Toky_voda" else hl_ryb
		for mi0 in main.find_children(jm, "MeshInstance3D", true, false):
			var mi := mi0 as MeshInstance3D
			var f := mi.mesh.get_faces()
			var xf := mi.global_transform
			var g: Dictionary = sv._tri_mrizka(f, xf) if jm != "Toky_voda" else {}
			if jm == "Toky_voda":
				var blizko := PackedVector3Array()
				for i in range(0, f.size(), 3):
					var c := xf * f[i]
					if Vector2(c.x, c.z).distance_to(sv.RYB_C) < sv.RYB_POL * 1.5 + sv.RYB_PAS:
						blizko.append(c)
						blizko.append(xf * f[i + 1])
						blizko.append(xf * f[i + 2])
				g = sv._tri_mrizka(blizko, Transform3D())
			for k in g:
				if not hladiny.has(k):
					hladiny[k] = []
				(hladiny[k] as Array).append_array(g[k])
	# teren sveta (Teren*) nad dilem - pod dilem ma byt niz nez dil (povrchy B; Misa (555, 886) nasyp toku nad dilem = val)
	var ter_svet := {}
	for mi0 in main.find_children("Teren*", "MeshInstance3D", true, false):
		var mi := mi0 as MeshInstance3D
		if mi.mesh == null or not mi.is_visible_in_tree() or String(mi.name) == "Teren_obzor":
			continue
		var ab := mi.global_transform * mi.mesh.get_aabb()
		if ab.position.x > sv.RYB_C.x + sv.RYB_POL * 1.5 or ab.end.x < sv.RYB_C.x - sv.RYB_POL * 1.5 or ab.position.z > sv.RYB_C.y + sv.RYB_POL * 1.5 or ab.end.z < sv.RYB_C.y - sv.RYB_POL * 1.5:
			continue
		var f := mi.mesh.get_faces()
		var xf := mi.global_transform
		var blizko := PackedVector3Array()
		for i in range(0, f.size(), 3):
			var c := xf * f[i]
			if Vector2(c.x, c.z).distance_to(sv.RYB_C) < sv.RYB_POL * 1.5:
				blizko.append(c)
				blizko.append(xf * f[i + 1])
				blizko.append(xf * f[i + 2])
		var g: Dictionary = sv._tri_mrizka(blizko, Transform3D())
		for k in g:
			if not ter_svet.has(k):
				ter_svet[k] = []
			(ter_svet[k] as Array).append_array(g[k])
	var hladina := func(x: float, z: float) -> float:
		var a: float = sv._tri_vyska(hl_tok, x, z)
		var b: float = sv._tri_vyska(hl_ryb, x, z)
		return b if a == INF else (a if b == INF else maxf(a, b))
	# 1) kameny
	var kamenu := 0
	var kam_visi := 0
	var kam_nej := -INF
	for mi0 in main.find_children("Rybnik_Kameny*", "MeshInstance3D", true, false):
		var km := mi0 as MeshInstance3D
		var xf := km.global_transform
		for kus: Array in sv._souvisle_kusy(km.mesh):
			var pts: PackedVector3Array = sv._kus_body(km.mesh, kus)
			var ymin := INF
			for p in pts:
				ymin = minf(ymin, (xf * p).y)
			var mez := INF                       # nejnizsi mezera spodku nad terenem dilu (dotyk kdekoli staci)
			var c := Vector3.ZERO
			for p in pts:
				var w := xf * p
				c += w / pts.size()
				if w.y > ymin + 0.05:
					continue
				var h: float = sv.ryb_vyska(w.x, w.z)
				if h != INF:
					mez = minf(mez, w.y - h)
			if mez == INF:
				continue
			kamenu += 1
			kam_nej = maxf(kam_nej, mez)
			if mez > visi:
				kam_visi += 1
				if kam_visi <= 20:
					print("RYBNIK_DIL kamen visi (%.1f, %.1f) spodek %.2f nad terenem dilu %.2f m" % [c.x, c.z, ymin, mez])
	# 2) okraj hladiny rybnika
	var okraj := 0
	var okraj_visi := 0
	for mi0 in main.find_children("Rybnik_Voda*", "MeshInstance3D", true, false):
		var mi := mi0 as MeshInstance3D
		var f := mi.mesh.get_faces()
		var hrany := {}
		for i in range(0, f.size(), 3):
			for j in 3:
				var a := (f[i + j] * 100.0).round()
				var b := (f[i + (j + 1) % 3] * 100.0).round()
				var k := [a, b] if (a.x < b.x or (a.x == b.x and a.z < b.z)) else [b, a]
				hrany[k] = int(hrany.get(k, 0)) + 1
		for k: Array in hrany:
			if int(hrany[k]) != 1:
				continue
			var w := mi.global_transform * ((k[0] as Vector3) / 100.0)
			var h: float = sv.ryb_vyska(w.x, w.z)
			if h == INF:
				continue
			okraj += 1
			if h < ryb_y - visi:
				# vtok a vypust: okraj hladiny pod pasem toku (hladina toku nad hladinou rybnika - visi)
				var ht: float = sv._tri_vyska(hl_tok, w.x, w.z)
				if ht != INF and ht >= ryb_y - visi and ht > h:
					continue
				okraj_visi += 1
				if okraj_visi <= 12:
					print("RYBNIK_DIL okraj hladiny nad brehem (%.1f, %.1f) hladina %.2f teren dilu %.2f" % [w.x, w.z, ryb_y, h])
	# 3) toky pres dil
	var bodu := 0
	var tunel := 0
	var sucho := 0
	var nad_dilem := 0
	var schod := float(sv.pasma()["dil"]["okraj_schod_m"])    # jako dil_okraj: sit sveta u hrany dilu triangluje jinak
	for tk: Dictionary in Pravidla.cti("voda", "toky"):
		var o: Array = tk["osa_xzy"]
		var s := 0.0
		for i in o.size() - 1:
			var a := Vector2(float(o[i][0]), float(o[i][1]))
			var b := Vector2(float(o[i + 1][0]), float(o[i + 1][1]))
			var L := a.distance_to(b)
			while s < L:
				var q := a.lerp(b, s / maxf(L, 1e-4))
				var hl := lerpf(float(o[i][2]), float(o[i + 1][2]), s / maxf(L, 1e-4))
				s += 0.5
				var h: float = sv.ryb_vyska(q.x, q.y)
				if h == INF:
					continue
				bodu += 1
				var nr := (b - a).normalized().orthogonal()
				for sd: float in [-3.0, -1.5, 0.0, 1.5, 3.0]:
					var q2 := q + nr * sd
					var h2: float = sv.ryb_vyska(q2.x, q2.y)
					var hs: float = sv._tri_vyska(ter_svet, q2.x, q2.y)
					if h2 != INF and hs != INF and sv._ryb_mist(q2.x, q2.y).z < 0.0 and hs > h2 + schod:
						nad_dilem += 1
						if nad_dilem <= 15:
							print("RYBNIK_DIL teren sveta nad dilem (%.1f, %.1f) %s svet %.2f dil %.2f" % [q2.x, q2.y, tk["id"], hs, h2])
				if h > hl - dno:
					tunel += 1
					if tunel <= 15:
						print("RYBNIK_DIL tok pod terenem dilu (%.1f, %.1f) %s hladina %.2f teren %.2f" % [q.x, q.y, tk["id"], hl, h])
				var hv: float = hladina.call(q.x, q.y)
				if hv == INF or hv < h + dno:
					sucho += 1
					if sucho <= 15:
						print("RYBNIK_DIL bez vody nad osou (%.1f, %.1f) %s voda %s teren %.2f" % [q.x, q.y, tk["id"], "-" if hv == INF else "%.2f" % hv, h])
			s -= L
	# Misa 6. 11. (snimek 20): „neni tam trava ani krovi“ - rakos a orobinec u vody (svet._rybnik_breh_dil skoncil
	# „chybi druh“, 0 rostlin); breh bez vodnich rostlin = chyba
	var rakos := 0
	for key: String in sv.data["rostliny"]:
		if key.begins_with("rakos") or key.begins_with("orobinec"):
			for t: Array in sv.data["rostliny"][key]:
				if Vector2(float(t[3]), float(t[11])).distance_to(sv.RYB_C) < sv.RYB_POL:
					rakos += 1
	if rakos < 50:
		print("RYBNIK_DIL breh bez rakosu (%.1f, %.1f) jen %d rostlin" % [sv.RYB_C.x, sv.RYB_C.y, rakos])
	var ok := kamenu > 0 and kam_visi == 0 and okraj_visi == 0 and tunel == 0 and sucho == 0 and nad_dilem == 0 and rakos >= 50
	_vysledek("rybnik_dil", ok, "kameny visi %d z %d (nejvys %.2f m) | okraj hladiny nad brehem %d z %d | osa toku v dilu %d bodu: pod terenem %d, bez vody %d, teren sveta nad dilem %d | rakos %d" % [kam_visi, kamenu, kam_nej, okraj_visi, okraj, bodu, tunel, sucho, nad_dilem, rakos])


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


## Louka v bodech (Misa 0.994 potok ve vsi (489, 895): holy zeleny obdelnik bez travy): hustota a podminky na mrizce.
func _louka_bod() -> void:
	var lk = main.get_node_or_null("Louka")
	var v := OS.get_environment("TVRZ_CO").split_floats(",") if OS.has_environment("TVRZ_CO") else PackedFloat64Array([480.0, 860.0, 540.0, 905.0])
	var z := float(v[1])
	var krok := float(OS.get_environment("TVRZ_KROK")) if OS.has_environment("TVRZ_KROK") else 4.0
	while z <= float(v[3]):
		var radek := ""
		var x := float(v[0])
		while x <= float(v[2]):
			var s: Vector3 = lk._vzorek(x, z)
			var proc := ""
			if main.svet.v_zahrade(x, z):
				proc += "Z"
			if main.svet.v_nove_zahrade(x, z) == 2:
				proc += "N"
			if main.svet.v_pruchodu(x, z):
				proc += "P"
			if main.svet.od_vody(x, z) < 1.5:
				proc += "V"
			if lk._v_budove(x, z):
				proc += "B"
			if main.svet.cesta_kraj_osa(x, z).x < 0.0:
				proc += "C"
			radek += " %3d%-3s" % [roundi(s.x * 100.0), proc]
			x += krok
		print("LOUKA z %5.1f:%s" % [z, radek])
		z += krok
	# kontrola (Misa 0.994 potok ve vsi: holy ctverec dilu rybnika Lhota): v dilu rybnika mimo vodu (od_vody > breh)
	# a mimo stavby, zahrady a pruchody musi louka mit travu
	var hole := 0
	var vse := 0
	var rl: Dictionary = preload("res://scripts/pravidla.gd").cti("voda", "rybnik_lhota")
	var c := Vector2(float(rl["stred"][0]), float(rl["stred"][1]))
	var r := float(rl["pulsirka_dilu_m"])
	var zx := c.x - r
	while zx <= c.x + r:
		var zz := c.y - r
		while zz <= c.y + r:
			if main.svet.ryb_vyska(zx, zz) != INF and not main.svet.ryb_voda(zx, zz) and main.svet.od_vody(zx, zz) > 1.5 and not main.svet.v_zahrade(zx, zz) \
					and main.svet.v_nove_zahrade(zx, zz) != 2 and not main.svet.v_pruchodu(zx, zz) and not lk._v_budove(zx, zz) \
					and main.svet.cesta_kraj_osa(zx, zz).x > 0.0:
				vse += 1
				if (lk._vzorek(zx, zz) as Vector3).x < 0.05:
					hole += 1
					if hole <= 5:
						print("LOUKA hola (%.0f, %.0f) dil rybnika bez travy" % [zx, zz])
			zz += 3.0
		zx += 3.0
	_vysledek("louka_bod", vse == 0 or hole <= vse / 10, "dil rybnika Lhota: holych bodu %d z %d" % [hole, vse])


## Misa 0.994 (413, 781), snimek f124 cesta_shora: svetle zelene hole schody na okraji ulice - barva terenu (zem.gdshader
## COLOR.g) rika trava, maska louky (trava_ves) nic. Obe z jednoho pravidla (kraj.ground_attrs: m = (g - 0,3) / 0,45)
## a po presunu usedlosti (svet._vo_data / _vo_teren) stejnymi vahami: na terenu vsi v presunute oblasti, kde je
## vrchol jasne travnaty (G >= 0,75) mimo stavby a zahrady, musi maska byt aspon 0,15 (nejvic 2 % vyjimek).
func _ves_maska() -> void:
	var g: Dictionary = main.svet.data["trava_ves"]
	var nn := int(g["n"])
	var k := float(g["k"])
	var x0 := float(g["x0"])
	var z0 := float(g["z0"])
	var ms := Marshalls.base64_to_raw(String(g["m"]))
	var lk = main.get_node_or_null("Louka")
	var vse := 0
	var spatne := 0
	# TVRZ_CO=x0,z0,x1,z1: vypis vrcholu (x z G maska y) do build/beh/ves_barva.txt (rozbor pruhu)
	var co := OS.get_environment("TVRZ_CO").split_floats(",") if OS.has_environment("TVRZ_CO") else PackedFloat64Array()
	var fd: FileAccess = FileAccess.open("res://build/beh/ves_barva.txt", FileAccess.WRITE) if co.size() == 4 else null
	for mi: MeshInstance3D in get_tree().root.find_children("Teren_ves*", "MeshInstance3D", true, false):
		var am := mi.mesh as ArrayMesh
		if am == null:
			continue
		for si in am.get_surface_count():
			var arr := am.surface_get_arrays(si)
			if arr[Mesh.ARRAY_COLOR] == null:
				continue
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var cl: PackedColorArray = arr[Mesh.ARRAY_COLOR]
			for vi in range(0, v.size(), 1 if fd else 3):
				var w := mi.global_transform * v[vi]
				var p := Vector2(w.x, w.z)
				var dump := fd != null and p.x >= co[0] and p.x <= co[2] and p.y >= co[1] and p.y <= co[3]
				if not dump and ((main.svet.vo.vahy(p) as Array).is_empty() or cl[vi].g < 0.75):
					continue
				if fd and not dump:
					continue
				var fx := clampf((p.x - x0) / k, 0.0, nn - 1.001)
				var fz := clampf((p.y - z0) / k, 0.0, nn - 1.001)
				var i0 := floori(fx)
				var j0 := floori(fz)
				var m := lerpf(lerpf(ms[j0 * nn + i0], ms[j0 * nn + i0 + 1], fx - i0), lerpf(ms[(j0 + 1) * nn + i0], ms[(j0 + 1) * nn + i0 + 1], fx - i0), fz - j0) / 255.0
				if dump:
					fd.store_line("%.2f %.2f %.3f %.3f %.3f" % [p.x, p.y, cl[vi].g, m, w.y])
					continue
				if (lk and lk._v_budove(p.x, p.y)) or main.svet.v_zahrade(p.x, p.y) or main.svet.v_nove_zahrade(p.x, p.y) == 2:
					continue
				vse += 1
				if m < 0.15:
					spatne += 1
					if spatne <= 5:
						print("VES_MASKA (%.1f, %.1f) barva G %.2f, maska %.2f" % [p.x, p.y, cl[vi].g, m])
	_vysledek("ves_maska", vse > 0 and spatne * 50 <= vse, "travnate vrcholy bez masky %d z %d" % [spatne, vse])


## Misa 0.997 (tablet: souvisle 55-75 ms, „neco se domrvilo“): prolinani na hranici dosahu (visibility_range_fade_mode)
## kresli objekt v pasmu dvakrat a pruhledne - u stromu a listi overdraw (reserse Otevreny svet bod 3). Ve svete zadne
## prolinani, dokud ho mereni na tabletu nepovoli (modely.json prolinani_stromu, prolinani_dosahu).
func _prolinani() -> void:
	var n := 0
	var pr: Array = []
	for g in get_tree().root.find_children("*", "GeometryInstance3D", true, false):
		# povoleno jen tam, kde to chce zaznam (modely.json prolinani_stromu: stromy, impostory a skaly - bez nej blikaji)
		var nm := String(g.name)
		var strom_skala := bool(Pravidla.cti("modely", "prolinani_stromu")) and (g is MultiMeshInstance3D)
		if (g as GeometryInstance3D).visibility_range_fade_mode != GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED and not String(g.get_path()).contains("Predehrati") and not strom_skala:
			n += 1
			if pr.size() < 5:
				pr.append(String(g.name))
	_vysledek("prolinani", n == 0, "uzlu s prolinanim %d %s" % [n, pr])


## Misa 0.997 (440, 851): „dum nebyl videt, jen stodola, pak se najednou objevil“ - stredni stupen domu ve 30-75 m
## (tablet) rozpustilo automaticke LOD. Kazdy dum vsi: z 20 az 120 m je aspon jeden stupen v dosahu viditelnosti a stredni
## stupen ma vypnute automaticke LOD (lod_bias z modely.json); totez stredni stupne predmetu.
func _lod_mezera() -> void:
	var chyby: Array = []
	var bias := float(Pravidla.cti("modely", "ves_domy_lod", "lod_bias"))
	for d in get_tree().root.find_children("Dum_ves_*", "Node3D", true, false):
		var st: Array = []
		for ch in d.get_children():
			if ch is GeometryInstance3D and (ch as GeometryInstance3D).cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
				var cn := String(ch.name)
				if cn.ends_with("_Vnejsek") or cn.ends_with("_Stredni") or cn.ends_with("_Daleko"):
					st.append(ch)
					if cn.ends_with("_Stredni") and (ch as GeometryInstance3D).lod_bias < bias:
						chyby.append("%s %s lod_bias %.0f" % [d.name, cn, (ch as GeometryInstance3D).lod_bias])
		if OS.has_environment("TVRZ_LOD_VYPIS"):
			for g: GeometryInstance3D in st:
				print("LOD_VYPIS %s %s %.1f-%.1f bias %.0f" % [d.name, g.name, g.visibility_range_begin, g.visibility_range_end, g.lod_bias])
		var dist := 20.0
		while dist <= 120.0:
			var ok := false
			for g: GeometryInstance3D in st:
				var e := g.visibility_range_end if g.visibility_range_end > 0.0 else INF
				if dist >= g.visibility_range_begin and dist < e:
					ok = true
			if not ok:
				chyby.append("%s mezera v %.0f m" % [d.name, dist])
				break
			dist += 5.0
	for g in get_tree().root.find_children("*_Stredni", "MeshInstance3D", true, false):
		if not String(g.get_parent().name).begins_with("Dum_ves_") and (g as GeometryInstance3D).lod_bias < float(Pravidla.cti("modely", "predmety_lod", "lod_bias")):
			chyby.append("%s lod_bias" % g.name)
	_vysledek("lod_mezera", chyby.is_empty(), "%d chyb %s" % [chyby.size(), chyby.slice(0, 5)])


## Misa 0.9991/0.9992 mlyn (575, 889): „blok travniku stoji ve vzduchu“ (posesté). Okraj terenu dilu (Mlyn_Teren) musi
## navazat na teren sveta: po obvodu dilu kazdych 0,5 m vyska dilu tesne uvnitr (svet.mlyn_teren) proti terenu sveta
## tesne venku (paprsek na kolizi Teren*). Schod > pasma.dil.okraj_schod_m = chyba s polohou (vypis DIL_OKRAJ).
func _dil_okraj() -> void:
	var sp := player.get_world_3d().direct_space_state
	sv.kolize_vse(true)
	for _i in 3:
		await get_tree().physics_frame
	var teren := func(q: Vector2) -> float:
		var pq := PhysicsRayQueryParameters3D.create(Vector3(q.x, 300.0, q.y), Vector3(q.x, -100.0, q.y))
		pq.exclude = [player.get_rid()]
		for _j in 8:
			var h := sp.intersect_ray(pq)
			if h.is_empty():
				return NAN
			var nm := String((h["collider"] as Node).name)
			if nm.begins_with("Teren") and not nm.begins_with("Teren_dil"):
				return float((h["position"] as Vector3).y)
			pq.exclude.append((h["collider"] as CollisionObject3D).get_rid())
		return NAN
	var mez := float(sv.pasma()["dil"].get("okraj_schod_m", 0.15))
	var chyb := 0
	var bodu := 0
	var nej := 0.0
	# vtok nahonu (jez, nasep nahonu v modelu dilu) je stavba mlyna jako brod - stejna vyjimka a dosah jako test smyslu
	# breh_toku (toky_tvar breh_sirka_m + 3 m od prvniho bodu nahonu, tools/krok_b/mlyn_voda.json)
	var mv: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://tools/krok_b/mlyn_voda.json"))
	var vtok := Vector2.INF
	if mv is Dictionary and (mv as Dictionary).has("nahon"):
		var b0: Array = mv["nahon"]["body"][0]
		var w0: Vector3 = sv._mlyn_inv.affine_inverse() * Vector3(float(b0[0]), 0.0, float(b0[2]))
		vtok = Vector2(w0.x, w0.z)
	var vtok_r := float(Pravidla.cti("voda", "toky_tvar")["breh_sirka_m"]) + 3.0
	for mi in get_tree().root.find_children("Mlyn_Teren*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		var bb := m.get_aabb()
		var gx := m.global_transform
		var x0 := bb.position.x
		var x1 := bb.end.x
		var z0 := bb.position.z
		var z1 := bb.end.z
		var obvod: Array = []
		var t := 0.0
		while t <= 1.0:
			obvod.append([Vector3(lerpf(x0, x1, t), 0, z0), Vector3(0, 0, -1)])
			obvod.append([Vector3(lerpf(x0, x1, t), 0, z1), Vector3(0, 0, 1)])
			obvod.append([Vector3(x0, 0, lerpf(z0, z1, t)), Vector3(-1, 0, 0)])
			obvod.append([Vector3(x1, 0, lerpf(z0, z1, t)), Vector3(1, 0, 0)])
			t += 0.5 / maxf(x1 - x0, z1 - z0)
		for o: Array in obvod:
			var vnitr := gx * ((o[0] as Vector3) - (o[1] as Vector3) * 0.25)
			var ven := gx * ((o[0] as Vector3) + (o[1] as Vector3) * 0.5)
			var hd: Vector2 = sv.mlyn_teren(vnitr.x, vnitr.z)
			if hd.x == INF:
				continue
			var hs: float = teren.call(Vector2(ven.x, ven.z))
			if is_nan(hs) or sv.od_vody(ven.x, ven.z) < 0.5 or Vector2(ven.x, ven.z).distance_to(vtok) < vtok_r:
				continue
			bodu += 1
			var sch := hd.x - hs
			nej = maxf(nej, absf(sch))
			if absf(sch) > mez:
				chyb += 1
				if chyb <= 8:
					print("DIL_OKRAJ mlyn (%.1f, %.1f) dil %.2f, svet %.2f, schod %+.2f m" % [ven.x, ven.z, hd.x, hs, sch])
	_vysledek("dil_okraj", bodu > 0 and chyb == 0, "mlyn: schodu nad %.2f m %d z %d bodu, nejvetsi %.2f m" % [mez, chyb, bodu, nej])


## Misa 0.99993 r. 54 (snimek misa_6_11/23, mlyn): „hladka trava bez trsu“ - offline kryti louky (kryti.bin) bralo teren
## dilu Mlyn_Teren jako strechu (paprsek shora narazil na sit dilu, ne Teren*), cely dil 40 x 40 m zakryty. Kontrola: po
## 0,5 m na trave dilu (mlyn: G vrcholu >= 0,8 mimo podezdivku; Lhota: ryb_od_vody > holy breh + 1 m) - bod zakryty
## v kryti.bin, ale paprsek shora (jako louka._zasah) nad nim narazi jen na sit terenu (pasma.dil.teren_site) = chyba.
func _dil_kryti() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	var sp := player.get_world_3d().direct_space_state
	sv.kolize_vse(true)
	for _i in 3:
		await get_tree().physics_frame
	var site: Array = sv.pasma()["dil"]["teren_site"]
	var holy := float(sv.pasma()["voda"]["holy_breh_m"])
	var dily := {"mlyn": Rect2(), "lhota": Rect2()}
	var dm: Dictionary = Pravidla.cti("voda", "mlyn", "dil")
	dily["mlyn"] = Rect2(float(dm["stred"][0]) - 30.0, float(dm["stred"][1]) - 30.0, 60.0, 60.0)
	var rl: Variant = Pravidla.cti("voda", "rybnik_lhota", "stred") if Pravidla.cti("voda", "rybnik_lhota").has("stred") else null
	if rl is Array:
		dily["lhota"] = Rect2(float(rl[0]) - 30.0, float(rl[1]) - 30.0, 60.0, 60.0)
	var pop := []
	var n := {"mlyn": [0, 0, 0], "lhota": [0, 0, 0]}
	for jm: String in dily:
		var r: Rect2 = dily[jm]
		if r.size == Vector2.ZERO:
			continue
		# stred bunky kryti 0,5 m (louka.KRYTI_K) - tam peceni vrha paprsek (driv roh bunky: na brehu jiny bod nez peceni)
		var x := floorf(r.position.x / 0.5) * 0.5 + 0.25
		while x < r.end.x:
			var z := floorf(r.position.y / 0.5) * 0.5 + 0.25
			while z < r.end.y:
				var y := INF
				if jm == "mlyn":
					var mt: Vector2 = sv.mlyn_teren(x, z)
					if mt.x != INF and mt.y >= 0.8:
						y = mt.x
				else:
					var rv: float = sv.ryb_vyska(x, z)
					var dv: float = sv.ryb_od_vody(x, z)
					if rv != INF and dv != INF and dv > holy + 1.0:
						y = rv
				if y != INF:
					var c := Vector2i(floori(x / 32.0), floori(z / 32.0))
					var kr: PackedByteArray = sv.kryti_tab.get(c, PackedByteArray())
					if not kr.is_empty() and louka._kryto(kr, c, x, z):
						var pq := PhysicsRayQueryParameters3D.create(Vector3(x, y + 9.0, z), Vector3(x, y - 2.0, z))
						pq.exclude = [player.get_rid()]
						var h := sp.intersect_ray(pq)
						var nm := ""
						if not h.is_empty():
							nm = String((h["collider"] as Node).name)
							if nm.begins_with("StaticBody3D") and (h["collider"] as Node).get_parent():
								nm = String((h["collider"] as Node).get_parent().name)
						var je_teren := false
						for pf: String in site:
							je_teren = je_teren or nm.begins_with(pf)
						var yl: float = louka._vzorek(x, z).y
						var hy: float = (h["position"] as Vector3).y if not h.is_empty() else NAN
						if je_teren and hy >= yl - 0.5:
							n[jm][1] += 1
							if pop.size() < 6:
								# louka._zasah ted (stejny paprsek jako offline kryti): true = trvale zakryti, false = kryti.bin
								# zastaraly nebo pri peceni stal v ceste pohyblivy objekt
								var zn: bool = louka._zasah(sp, PhysicsRayQueryParameters3D.new(), x, z)
								pop.append("%s (%.1f, %.1f) %s zasah %.2f louka %.2f, _zasah ted %s" % [jm, x, z, nm, hy, yl, zn])
						elif je_teren:
							# teren o 0,5 m niz nez vyska louky (louka._zasah: trs by levitoval) - jina chyba (vyska louky), vypis
							n[jm][2] += 1
							if pop.size() < 12:
								pop.append("%s (%.1f, %.1f) LEVITACE %s zasah %.2f louka %.2f teren dilu %.2f" % [jm, x, z, nm, hy, yl, y])
					n[jm][0] += 1
				z += 0.5
			x += 0.5
	for p: String in pop:
		print("DIL_KRYTI zakryto terenem dilu ", p)
	var ok: bool = n["mlyn"][0] > 0 and n["mlyn"][1] == 0 and n["lhota"][1] == 0
	_vysledek("dil_kryti", ok, "trava dilu zakryta jako strechou: mlyn %d z %d, Lhota %d z %d bodu (louka nad terenem dilu o 0,5 m: mlyn %d, Lhota %d)" % [n["mlyn"][1], n["mlyn"][0], n["lhota"][1], n["lhota"][0], n["mlyn"][2], n["lhota"][2]])


## Misa 0.9992 prikop (-24, 29): rovny pas „hliny“ pres vodu - hladina tam byla pruhledna (hloubka vrcholu 0), protoze
## nadrz.misto vratilo prvni nadrz, jejiz obdelnik mrizky bod obsahoval (cizi, d < 0). V prikopu kolem tvrze: kde je
## teren aspon 0,6 m pod hladinou, musi byt bod uvnitr nadrze (misto d > 0).
func _prikop_hloubka() -> void:
	# body na hladine prikopu (vrcholy site Prikop_voda): hloubka ve vrcholu (COLOR.r * 4) tam, kde je teren aspon
	# 0,6 m pod hladinou, musi byt > 0,3 m (jinak hladina pruhledna - Misa 0.9992 prikop (-24, 29), rovny pas)
	var hl := float(preload("res://scripts/pravidla.gd").cti("voda", "prikop")["hladina_y"])
	var vse := 0
	var spatne := 0
	for mi0 in get_tree().root.find_children("Prikop_voda*", "MeshInstance3D", true, false):
		var mi := mi0 as MeshInstance3D
		for si in mi.mesh.get_surface_count():
			var arr := mi.mesh.surface_get_arrays(si)
			if arr[Mesh.ARRAY_COLOR] == null:
				continue
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var cl: PackedColorArray = arr[Mesh.ARRAY_COLOR]
			for i in v.size():
				var w := mi.global_transform * v[i]
				var ter: float = sv._vyska(w.x, w.z)
				if ter > hl - 0.6:
					continue
				vse += 1
				if cl[i].r * 4.0 < 0.3:
					spatne += 1
					if spatne <= 8:
						print("PRIKOP_HLOUBKA (%.1f, %.1f) teren %.2f, hloubka vrcholu %.2f, misto %s" % [w.x, w.z, ter, cl[i].r * 4.0, str(sv.nadrz.misto(w.x, w.z))])
	_vysledek("prikop_hloubka", vse > 0 and spatne * 50 <= vse, "vrcholy hladiny prikopu bez hloubky %d z %d" % [spatne, vse])


## Shoda osy ulice hra x Blender (blender/ves_ramec.py osa_ulice - jediny zdroj vsi, 3. 11.): osa ze hry do
## build/beh/osa_godot.json, tools/porovnej_osu.py porovna s Pythonem (nejvic 0,05 m).
func _ves_osa() -> void:
	var osa: PackedVector2Array = sv.vo.osa_ulice()
	var out: Array = []
	for q in osa:
		out.append([q.x, q.y])
	var f := FileAccess.open("res://build/beh/osa_godot.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(out))
	f.close()
	_vysledek("ves_osa", osa.size() > 10, "bodu %d (porovnani tools/porovnej_osu.py)" % osa.size())


## Misa 0.99991 (5. 11.): „kun nevejde na most“, „kun by se nemel bat vody, normalne prebrodit nebo preplavat“,
## „na nekterych mistech kun nechtel jit dal, jakoby stena, ale nic tam nebylo“, „portovani na koni nefunguje“.
## Cisla jizda.json test_prekazky. Jizda fyzikou (kun.gd _physics_process, jezdec packou vpred, cval):
##   most        od most_pred_m pred koncem mostovky (svet._najezdy) pres most za druhy konec - musi projet
##   brody       brody na Bystrici (cesty.json prechody) po ose cesty +-brod_pred_m - musi projet
##   bystrice    3 mista pres Bystrici bez srazu na brezich (mrizka vysek) - musi prebrodit
##   plavani     do rybnika tvrze (hloubka nad plavat_od_m) - musi plavat a projet
##   sit         body po sit_m po cele mape x smeru: telo kone (test_move o draha_m) - narazi-li kun na kolizi bez
##               viditelneho modelu do viditelne_m (nebo na kolizi skryte site) = CHYBA, vypis KUN_STENA x z co
##   cestovani   rychle cestovani na koni: kun i jezdec v cili (do 10 m), jezdec dal v sedle
func _kun_prekazky() -> void:
	var kun: Node = main.get("kun")
	if kun == null:
		_vysledek("kun_prekazky", false, "kun chybi")
		return
	var tp: Dictionary = Pravidla.cti("jizda", "test_prekazky")
	var vys: Array = []
	var ok := true
	var chyby_jizdy: Array = []          # lambda jed meni jen kopii mistni promenne ok - selhani jizdy sem (5. 11.)
	player.set_flying(false)
	kun.nasedni(player)
	kun.set("drzet_cestu", false)
	var jed := func(nm: String, a: Vector2, b: Vector2, chce_plavat := false) -> void:
		var r: Dictionary = await _kun_jed(kun, a, b, tp)
		var st_d := _kun_stara(a, (b - a).normalized(), a.distance_to(b))
		var dobre: bool = r["dojel"] and (r["plaval"] or not chce_plavat)
		var t := "%s (%.0f, %.0f)->(%.0f, %.0f): %s %.1f/%.1f m, hloubka az %.2f m%s%s%s" % [nm, a.x, a.y, b.x, b.y,
				"projel" if r["dojel"] else "STOJI", r["ujeto"], a.distance_to(b), r["hloubka_max"], ", plaval" if r["plaval"] else "",
				"" if r["dojel"] else " u (%.1f, %.1f) duvod %s" % [r["poloha"].x, r["poloha"].y, r["duvod"]],
				(" kolize " + String(r["kolize"])) if String(r["kolize"]) != "" else ""]
		t += " (kontrola do 0.99991: %s)" % ("projel" if st_d == INF else "stal by po %.1f m" % st_d)
		print("KUN_JIZDA " + t)
		vys.append(t)
		if not dobre:
			chyby_jizdy.append(nm)
	# --- most
	var naj: Array = sv.get("_najezdy")
	if naj.size() >= 2:
		await jed.call("most", (naj[0][0] as Vector2) + (naj[0][1] as Vector2) * float(tp["most_pred_m"]),
				(naj[1][0] as Vector2) + (naj[1][1] as Vector2) * float(tp["most_pred_m"]))
	else:
		vys.append("most: svet._najezdy prazdne")
		ok = false
	# --- most po ose cesty (Misa jela po ceste k mostu - drzet cestu): osa odbocka_ves +-40 m od stredu mostu
	for pr: Dictionary in Pravidla.cti("cesty", "prechody"):
		if String(pr["druh"]) != "most":
			continue
		var st := Vector2(float(pr["stred"][0]), float(pr["stred"][1]))
		for oi in sv.cesty_osy.size():
			var pp: PackedVector2Array = sv.cesty_osy[oi]["p"]
			var bl := -1
			for i in pp.size():
				if pp[i].distance_to(st) < 6.0:
					bl = i
					break
			if bl < 0:
				continue
			var i0 := bl
			var i1 := bl
			while i0 > 0 and pp[i0].distance_to(st) < 40.0:
				i0 -= 1
			while i1 < pp.size() - 1 and pp[i1].distance_to(st) < 40.0:
				i1 += 1
			for sm: Array in [[i0, i1, 1], [i1, i0, -1]]:
				var stara_d := INF
				var stara_p := Vector2.ZERO
				var u := 0.0
				var i: int = sm[0]
				while i != int(sm[1]) and stara_d == INF:
					var j: int = i + int(sm[2])
					var dd := _kun_stara(pp[i], (pp[j] - pp[i]).normalized(), pp[i].distance_to(pp[j]) + 1.6)
					if dd != INF:
						stara_d = u + dd
						stara_p = pp[i] + (pp[j] - pp[i]).normalized() * dd
					u += pp[i].distance_to(pp[j])
					i = j
				var t_o := "most po ose cesty %d od (%.0f, %.0f): kontrola do 0.99991 %s" % [oi, pp[sm[0]].x, pp[sm[0]].y,
						"projel" if stara_d == INF else "stal by po %.1f m u (%.1f, %.1f)" % [stara_d, stara_p.x, stara_p.y]]
				# a jizda po ceste (drzet cestu): od bodu osy pred mostem k bodu za nim
				var r: Dictionary = await _kun_jed(kun, pp[sm[0]], pp[sm[1]], tp, true)
				t_o += ", jizda po ceste: %s %.1f/%.1f m%s" % ["projel" if r["dojel"] else "STOJI", r["ujeto"], pp[sm[0]].distance_to(pp[sm[1]]),
						"" if r["dojel"] else " u (%.1f, %.1f) duvod %s kolize %s" % [r["poloha"].x, r["poloha"].y, r["duvod"], r["kolize"]]]
				ok = ok and bool(r["dojel"])
				print("KUN_JIZDA " + t_o)
				vys.append(t_o)
	# --- brody na Bystrici po ose cesty
	for pr: Dictionary in Pravidla.cti("cesty", "prechody"):
		if String(pr["tok"]) != "bystrice" or String(pr["druh"]) != "brod":
			continue
		var st := Vector2(float(pr["stred"][0]), float(pr["stred"][1]))
		var best := INF
		var bo := -1
		var bi := -1
		for oi in sv.cesty_osy.size():
			var pp: PackedVector2Array = sv.cesty_osy[oi]["p"]
			for i in pp.size():
				if pp[i].distance_to(st) < best:
					best = pp[i].distance_to(st)
					bo = oi
					bi = i
		if bo < 0:
			continue
		var pp2: PackedVector2Array = sv.cesty_osy[bo]["p"]
		var ab: Array = []
		for sg: int in [-1, 1]:
			var j := bi
			while j + sg >= 0 and j + sg < pp2.size() and pp2[j + sg].distance_to(pp2[bi]) < float(tp["brod_pred_m"]):
				j += sg
			ab.append(pp2[j])
		await jed.call(String(pr["id"]), ab[0], ab[1])
	# --- Bystrice mimo brody: 3 mista, kde breh v mrizce vysek nema sraz
	var kor: Object = sv.get("koryto")
	if kor:
		var body: PackedVector2Array = kor.get("body")
		var sraz := float(Pravidla.cti("jizda", "kun", "sraz_m"))
		var krok := float(Pravidla.cti("jizda", "kun", "draha_krok_m"))
		var nalez := 0
		var i := 40
		while i < body.size() - 40 and nalez < 3:
			var osa := (body[i + 1] - body[i - 1]).normalized()
			var bok := Vector2(-osa.y, osa.x)
			var a := body[i] + bok * float(tp["brod_pred_m"])
			var b := body[i] - bok * float(tp["brod_pred_m"])
			var y0: float = sv._vyska(a.x, a.y)
			var hladke := true
			var t := krok
			while t <= a.distance_to(b):
				var q := a + (b - a).normalized() * t
				var yq: float = maxf(sv._vyska(q.x, q.y), float(sv.hladina(q.x, q.y)))
				hladke = hladke and y0 - yq < sraz * 0.8 and yq - y0 < sraz * 0.8
				y0 = yq
				t += krok
			if hladke and absf(float(sv.od_vody(a.x, a.y))) > 3.0:
				var r: Dictionary = await _kun_jed(kun, a, b, tp)
				if not r["dojel"] and String(r["kolize"]) != "":
					# kmen nebo kamen v ceste (viditelne - vypis) neni chyba vody: jine misto
					print("KUN_JIZDA bystrice_%d: u (%.1f, %.1f) duvod %s kolize %s - jine misto" % [i, r["poloha"].x, r["poloha"].y, r["duvod"], r["kolize"]])
					i += 7
					continue
				await jed.call("bystrice_%d" % i, a, b)
				nalez += 1
				i += maxi(1, body.size() / 6)
			else:
				i += 7
	# --- plavani: rybnik tvrze ze strany bez srazu
	var rt: Dictionary = Pravidla.cti("voda", "rybnik_tvrz")
	var rs := Vector2(float(rt["stred"][0]), float(rt["stred"][1]))
	var rp := float(rt["polomer_m"])
	for k in 8:
		var dv := Vector2.from_angle(TAU * k / 8.0)
		var a := rs + dv * (rp + 10.0)
		var b := rs - dv * (rp * 0.3)
		var y0: float = sv._vyska(a.x, a.y)
		var hladke := true
		for s in 30:
			var q := a.lerp(b, (s + 1) / 30.0)
			var yq: float = maxf(sv._vyska(q.x, q.y), float(rt["hladina_y"]))
			hladke = hladke and absf(y0 - yq) < 0.8
			y0 = yq
		if hladke:
			await jed.call("rybnik_tvrz", a, b, true)
			break
		if k == 7:
			vys.append("plavani: rybnik tvrze bez mirneho brehu")
			ok = false
	# --- rychle cestovani na koni
	var cil := Vector3(413.0, 0.0, 781.0)
	await main.fast_travel(cil, Vector3(470.0, 3.0, 830.0), 0.0, "test")
	for f in 10:
		await get_tree().physics_frame
	var kp := (kun as Node3D).global_position
	var d_k := Vector2(kp.x, kp.z).distance_to(Vector2(cil.x, cil.z))
	var v_sedle: bool = player.get("na_koni") == kun and player.global_position.distance_to(kun.sedlo_global()) < 0.6
	var t_c := "cestovani na koni: kun %.1f m od cile, jezdec %s" % [d_k, "v sedle" if v_sedle else "MIMO SEDLO (%.1f m)" % player.global_position.distance_to(kun.sedlo_global())]
	print("KUN_JIZDA " + t_c)
	vys.append(t_c)
	ok = ok and d_k < 10.0 and v_sedle
	player.move_input = Vector2.ZERO
	kun.sesedni()
	# --- sit: neviditelne steny
	var t_s: Dictionary = _kun_sit(kun, tp)
	vys.append(String(t_s["text"]))
	ok = ok and int(t_s["chyb"]) == 0
	ok = ok and chyby_jizdy.is_empty()
	if not chyby_jizdy.is_empty():
		vys.push_front("NEPROJEL: %s" % ", ".join(chyby_jizdy))
	_vysledek("kun_prekazky", ok, " | ".join(vys))


func _kun_zem(kun: Node, q: Vector2) -> float:
	var r := PhysicsRayQueryParameters3D.create(Vector3(q.x, 400.0, q.y), Vector3(q.x, -200.0, q.y))
	r.exclude = [(kun as CollisionObject3D).get_rid(), player.get_rid()]
	var h := (kun as Node3D).get_world_3d().direct_space_state.intersect_ray(r)
	return float((h["position"] as Vector3).y) if not h.is_empty() else float(sv._vyska(q.x, q.y))


## Jizda kone z a do b cvalem (jezdec se diva po smeru); vraci dojel, ujeto, polohu a duvod zastaveni.
func _kun_jed(kun: Node, a: Vector2, b: Vector2, tp: Dictionary, po_ceste := false) -> Dictionary:
	var smer := (b - a).normalized()
	var yaw := atan2(-smer.x, -smer.y)
	kun.premisti(Vector3(a.x, _kun_zem(kun, a) + 0.05, a.y), yaw)
	for f in 3:
		await get_tree().physics_frame
	player.yaw = yaw
	player.pitch = 0.0
	player.move_input = Vector2(0, 1)
	kun.set("_stupen", 1)
	kun.set("drzet_cestu", po_ceste)
	var res := {"dojel": false, "plaval": false, "hloubka_max": 0.0, "duvod": "", "kolize": "", "poloha": a, "ujeto": 0.0}
	var hist: Array = []
	var nz := int(float(tp["zaseknuti_s"]) * Engine.physics_ticks_per_second)
	for f in int(float(tp["limit_s"]) * Engine.physics_ticks_per_second):
		await get_tree().physics_frame
		player.yaw = yaw
		kun.set("_stupen", 1)
		var p := Vector2((kun as Node3D).global_position.x, (kun as Node3D).global_position.z)
		res["ujeto"] = (p - a).dot(smer)
		res["poloha"] = p
		res["plaval"] = bool(res["plaval"]) or bool(kun.get("plave"))
		res["hloubka_max"] = maxf(float(res["hloubka_max"]), float(kun.get("hloubka")))
		if float(res["ujeto"]) >= a.distance_to(b):
			res["dojel"] = true
			break
		hist.append(p)
		if hist.size() > nz:
			hist.pop_front()
			if (hist[0] as Vector2).distance_to(p) < float(tp["zaseknuti_m"]):
				res["duvod"] = String(kun.get("duvod"))
				var kc := (kun as CharacterBody3D).get_last_slide_collision()
				for si in (kun as CharacterBody3D).get_slide_collision_count():
					var k2 := (kun as CharacterBody3D).get_slide_collision(si)
					if k2.get_normal().y < 0.7:
						kc = k2
				if kc and kc.get_collider():
					res["kolize"] = "%s %s v (%.1f, %.1f, %.1f) n %s" % [(kc.get_collider() as Node).name, _kun_tvar(kc.get_collider(), kc.get_collider_shape_index()),
							kc.get_position().x, kc.get_position().y, kc.get_position().z, kc.get_normal().snapped(Vector3.ONE * 0.01)]
				break
	player.move_input = Vector2.ZERO
	kun.set("drzet_cestu", false)
	return res


## Sit bodu po mape: telo kone o draha_m v kazdem smeru (test_move). Kolize, ktera neni podlaha (sklon do
## podlaha_max_st), musi mit viditelny model: trimesh skryte site = chyba; kvadr exportu bez viditelne site nebo
## instance rostliny do viditelne_m = chyba.
func _kun_sit(kun: Node, tp: Dictionary) -> Dictionary:
	var kb := kun as CharacterBody3D
	var g: Dictionary = sv.data["trava_kraj"]
	var krok := float(tp["sit_m"])
	var draha := float(tp["draha_m"])
	var vid := float(tp["viditelne_m"])
	var podlaha := cos(deg_to_rad(float(Pravidla.cti("jizda", "kun", "podlaha_max_st"))))
	var louka: Node = main.get_node_or_null("Louka")
	# viditelne modely: instance rostlin z dat (stromy, kere, skaly - kreslene impostory, LOD i MultiMeshe; kolize kmenu
	# a skal vznikaji z tychz zaznamu), male site (obal, mrizka 8 m), velke site (obaly trojuhelniku, az na dotaz)
	var rost := {}
	for key: String in sv.data["rostliny"]:
		if key.contains("_daleko"):
			continue
		var rp := 0.0
		if key.begins_with("skala_") or key.begins_with("balvan_"):
			var me: Mesh = sv._skala_sit(key)
			if me:
				rp = maxf(me.get_aabb().size.x, me.get_aabb().size.z) * 0.5
		for t: Array in sv.data["rostliny"][key]:
			var c := Vector2i(floori(float(t[3]) / 8.0), floori(float(t[11]) / 8.0))
			if not rost.has(c):
				rost[c] = []
			(rost[c] as Array).append([Vector2(float(t[3]), float(t[11])), rp * Vector3(t[0], t[4], t[8]).length(), key])
	var male := {}
	var velke: Array = []
	for n in main.find_children("*", "MeshInstance3D", true, false):
		var gi := n as MeshInstance3D
		if gi.mesh == null or not gi.is_visible_in_tree() or String(gi.name).begins_with("Teren") or (louka and louka.is_ancestor_of(gi)) \
				or kun.is_ancestor_of(gi) or player.is_ancestor_of(gi) or gi.transparency >= 1.0:
			continue
		var bb := gi.global_transform * gi.get_aabb()
		if bb.size.length() < 30.0:
			for cx in range(floori(bb.position.x / 8.0), floori(bb.end.x / 8.0) + 1):
				for cz in range(floori(bb.position.z / 8.0), floori(bb.end.z / 8.0) + 1):
					var c := Vector2i(cx, cz)
					if not male.has(c):
						male[c] = []
					(male[c] as Array).append([bb, String(gi.name)])
		else:
			velke.append([gi, bb])
	var videt := func(p: Vector3) -> String:
		var c0 := Vector2i(floori(p.x / 8.0), floori(p.z / 8.0))
		for e: Array in male.get(c0, []):
			if (e[0] as AABB).grow(vid).has_point(p):
				return String(e[1])
		var q := Vector2(p.x, p.z)
		for dx in range(-1, 2):
			for dz in range(-1, 2):
				for e: Array in rost.get(c0 + Vector2i(dx, dz), []):
					if q.distance_to(e[0]) <= vid + 0.6 + float(e[1]):
						return String(e[2])
		for e: Array in velke:
			if not (e[1] as AABB).grow(vid).has_point(p):
				continue
			# trojuhelniky velke site v mrizce 4 m (svetove souradnice), jednou na sit
			if (e as Array).size() < 3:
				var mi := e[0] as MeshInstance3D
				var xf := mi.global_transform
				var f := mi.mesh.get_faces()
				var tm := {}
				for i in range(0, f.size(), 3):
					var tb := AABB(xf * f[i], Vector3.ZERO).expand(xf * f[i + 1]).expand(xf * f[i + 2])
					for cx in range(floori(tb.position.x / 4.0), floori(tb.end.x / 4.0) + 1):
						for cz in range(floori(tb.position.z / 4.0), floori(tb.end.z / 4.0) + 1):
							var c := Vector2i(cx, cz)
							if not tm.has(c):
								tm[c] = []
							(tm[c] as Array).append(tb)
				e.append(tm)
			for tb: AABB in (e[2] as Dictionary).get(Vector2i(floori(p.x / 4.0), floori(p.z / 4.0)), []):
				if tb.grow(vid).has_point(p):
					return String((e[0] as Node).name)
		return ""
	var tvary := {}                           # kolize (teleso, tvar) -> uz posouzeno: jmeno modelu nebo ""
	var bodu := 0
	var v_kolizi := 0
	var steny := 0
	var teren := 0
	var videne := 0
	var sraz := 0
	var stara_falesne := 0
	var prekroci := 0
	var chyby: Dictionary = {}
	var nx := int(g["nx"])
	var nz := int(g["nz"])
	var x0 := float(g["x0"])
	var z0 := float(g["z0"])
	var x1 := x0 + (nx - 1) * float(g["k"])
	var z1 := z0 + (nz - 1) * float(g["k"])
	var x := x0 + krok * 0.5
	print("KUN_SIT priprava: rostlin v %d bunkach, malych siti v %d bunkach, velkych siti %d" % [rost.size(), male.size(), velke.size()])
	while x < x1:
		if int(x / krok) % 8 == 0:
			print("KUN_SIT x %.0f: bodu %d, sten %d, viditelnych %d" % [x, bodu, steny, videne])
		var z := z0 + krok * 0.5
		while z < z1:
			var q := Vector2(x, z)
			z += krok
			var y := _kun_zem(kun, q)
			if float(sv.hladina(q.x, q.y)) > y:
				continue
			bodu += 1
			var o := Vector3(q.x, y + 0.25, q.y)
			if kb.test_move(Transform3D(Basis(), o), Vector3(0, 0.05, 0)):
				v_kolizi += 1
				continue
			for s in int(tp["smeru"]):
				var yaw := TAU * s / float(tp["smeru"])
				var dv := Vector3(-sin(yaw), 0.0, -cos(yaw))
				var kc := KinematicCollision3D.new()
				if kb.test_move(Transform3D(Basis(Vector3.UP, yaw), o), dv * draha, kc, 0.001, false, 4):
					# podlaha (i kamen pod paprskem nohou = krok pres) neni prekazka; prvni srazka, ktera neni podlaha
					var ci := -1
					for k in kc.get_collision_count():
						if kc.get_normal(k).y < podlaha:
							ci = k
							break
					if ci < 0:
						continue
					# krok pres nizkou prekazku (kun.gd _prekroc): nad ni volno o krok_pres_m vys
					var up := Vector3(0, float(Pravidla.cti("jizda", "kun", "krok_pres_m")) + 0.02, 0)
					var x1t := Transform3D(Basis(Vector3.UP, yaw), o + kc.get_travel() + up)
					if not kb.test_move(Transform3D(Basis(Vector3.UP, yaw), o + kc.get_travel()), up) and not kb.test_move(x1t, dv * float(Pravidla.cti("jizda", "kun", "nohy_polomer_m"))):
						prekroci += 1
						continue
					var col := kc.get_collider(ci) as Node
					var cp := kc.get_position(ci)
					var jm := String(col.name) if col else "?"
					var rodic := col.get_parent() if col else null
					if jm.begins_with("Teren") or (rodic and String(rodic.name).begins_with("Teren")):
						teren += 1
						continue
					var kl := "%d_%d" % [col.get_instance_id() if col else 0, kc.get_collider_shape_index(ci)]
					var co := ""
					if tvary.has(kl):
						co = String(tvary[kl])
					elif rodic is GeometryInstance3D and jm.ends_with("_kolize"):
						co = String(rodic.name) if (rodic as GeometryInstance3D).is_visible_in_tree() else ""
					else:
						co = videt.call(cp)
					tvary[kl] = co
					if co != "":
						videne += 1
						continue
					steny += 1
					var c := Vector2i(floori(cp.x), floori(cp.z))
					if not chyby.has(c):
						chyby[c] = "%s %s" % [jm, (rodic.name if rodic else "")]
						if chyby.size() <= 40:
							print("KUN_STENA %.1f %.1f y %.1f kolize %s %s (rodic %s) normala %s" % [cp.x, cp.z, cp.y, jm, _kun_tvar(col, kc.get_collider_shape_index(ci)), rodic.name if rodic else "-", kc.get_normal(ci).snapped(Vector3.ONE * 0.01)])
				else:
					var nova: bool = kun.prekazka(o - Vector3(0, 0.25, 0), dv, draha + 1.6) != INF
					var stara := _kun_stara(q, Vector2(dv.x, dv.z), draha + 1.6) != INF
					if nova:
						sraz += 1
					elif stara:
						stara_falesne += 1
						if stara_falesne <= 15:
							print("KUN_STARA_STENA %.1f %.1f smer %.0f st: kontrola do 0.99991 by zastavila, povrch fyziky sraz nema" % [q.x, q.y, rad_to_deg(yaw)])
		x += krok
	var t := "sit %.0f m: %d bodu (%d v kolizi na startu), smeru %d: steny bez modelu %d (%d mist), viditelne prekazky %d, strmy teren %d, sraz v draze %d, prekroci (do krok_pres_m) %d; stara kontrola (do 0.99991) by navic zastavila %d" % [krok, bodu, v_kolizi, int(tp["smeru"]), steny, chyby.size(), videne, teren, sraz, prekroci, stara_falesne]
	print("KUN_SIT " + t)
	return {"text": t, "chyb": chyby.size()}


## Popis tvaru kolize (druh, rozmer, stred) pro vypis.
func _kun_tvar(col: Object, idx: int) -> String:
	var co := col as CollisionObject3D
	if co == null:
		return "?"
	var own := co.shape_find_owner(idx)
	var cs := co.shape_owner_get_owner(own) as CollisionShape3D
	if cs == null or cs.shape == null:
		return "?"
	var sh := cs.shape
	var roz := ""
	if sh is BoxShape3D:
		roz = str((sh as BoxShape3D).size.snapped(Vector3.ONE * 0.01))
	elif sh is CylinderShape3D:
		roz = "r %.2f v %.1f" % [(sh as CylinderShape3D).radius, (sh as CylinderShape3D).height]
	return "%s %s stred %s%s" % [sh.get_class(), roz, cs.global_position.snapped(Vector3.ONE * 0.1), " tok" if cs.has_meta("tok") else ""]


## Kontrola drahy kone do 0.99991 (pro srovnani v testu): sraz z mrizky vysek louky _vyska (2 m) mezi body po 1,6 m
## nad 1,1 m, nebo voda hloubeji nez 1,1 m od kraje (od_vody). Vraci vzdalenost prvniho zastaveni nebo INF.
func _kun_stara(a: Vector2, smer: Vector2, delka: float) -> float:
	var y_pred: float = sv._vyska(a.x, a.y)
	var d := 1.6
	while d <= delka:
		var q := a + smer * d
		var yq: float = sv._vyska(q.x, q.y)
		if y_pred - yq > 1.1 or float(sv.od_vody(q.x, q.y, yq)) < -1.1:
			return d
		y_pred = yq
		d += 1.6
	return INF


## Vzhled postav (Misa 5. 11.: dobove postavy, kazdy obyvatel vlastni sada; scripts/vzhled.gd): kazda sada z
## pravidla/svet/postavy_vzhled.json a telo hrace (telo.gd HRDINA) se nacte, ma kostru UAL (pelvis, Head, hand_r),
## nejvys 3 povrchy a LOD0 <= troj_lod[0] tridy postava (pravidla_modelu.json); LOD1 = prvni uroven automatickych LOD
## importu (headless bez dat sit = NEOVERENO). Kazdy obyvatel dostane sadu; pracovni klipy (UAL_prace.glb) v knihovne.
func _postavy_vzhled() -> void:
	var Vz := preload("res://scripts/vzhled.gd")
	var trida: Dictionary = {}
	var pm = JSON.parse_string(FileAccess.get_file_as_string("res://pravidla/pravidla_modelu.json"))
	var hledej := func(f: Callable, v: Variant) -> void:
		if v is Dictionary:
			if String((v as Dictionary).get("trida", "")) == "postava":
				trida.merge(v)
			for k in v:
				f.call(f, v[k])
		elif v is Array:
			for x in v:
				f.call(f, x)
	hledej.call(hledej, pm)
	var lim0 := int(trida.get("troj_lod", [14000])[0])
	var lim1 := int(trida.get("troj_lod", [14000, 3000])[1])
	var d: Dictionary = Vz.data()
	var sady := {}
	for k in d.get("obyvatele", {}).values() + d.get("podle_role", {}).values() + d["zalozni"]["muz"] + d["zalozni"]["zena"]:
		sady[String(k)] = Vz.cesta(String(k))
	sady["hrac"] = "res://modely/postavy/hrdina/hrac_cela.gltf"
	var chyby: Array = []
	var radky: Array = []
	for k: String in sady:
		var p: String = sady[k]
		if not ResourceLoader.exists(p):
			chyby.append(k + " chybi")
			continue
		var ps: PackedScene = load(p)
		var n := ps.instantiate()
		var sk := n.find_children("*", "Skeleton3D", true, false)
		if sk.is_empty() or (sk[0] as Skeleton3D).find_bone("pelvis") < 0 or (sk[0] as Skeleton3D).find_bone("Head") < 0 or (sk[0] as Skeleton3D).find_bone("hand_r") < 0:
			chyby.append(k + " bez kostry UAL")
		var t0 := 0
		var t1 := 0
		var pov := 0
		var lod_ok := true
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var m := (mi as MeshInstance3D).mesh
			pov += m.get_surface_count()
			for si in m.get_surface_count():
				var ic: int = m.surface_get_array_index_len(si)
				t0 += ic / 3
				var sd: Dictionary = RenderingServer.mesh_get_surface(m.get_rid(), si)
				var lods: Array = sd.get("lods", [])
				if sd.is_empty():
					lod_ok = false
				elif lods.is_empty():
					t1 += ic / 3
				else:
					var b := 2 if int(sd.get("vertex_count", 0)) <= 65535 else 4
					var nb: int = preload("res://tools/foto_vzhled.gd").lod1_indexu(lods)
					t1 += (nb / b / 3) if nb > 0 else ic / 3
		n.free()
		radky.append("%s %d/%s" % [k, t0, str(t1) if lod_ok else "?"])
		print("POSTAVA %s troj LOD0 %d LOD1 %s povrchu %d" % [k, t0, str(t1) if lod_ok else "NEOVERENO", pov])
		if t0 > lim0:
			chyby.append("%s LOD0 %d > %d" % [k, t0, lim0])
		if pov > 3:
			chyby.append("%s povrchu %d > 3" % [k, pov])
	var bez := 0
	for o: Dictionary in Pravidla.cti("postavy", "obyvatele"):
		if Vz.sada(o) == "":
			bez += 1
	if bez > 0:
		chyby.append("obyvatel bez sady %d" % bez)
	var lib: AnimationLibrary = preload("res://scripts/anim_ual.gd").knihovna("Armature/Skeleton3D")
	for kl: String in ["Prace_Zametani_Loop", "Prace_Kovar_Loop", "Piti", "Hovor_Gesta_Loop", "Ceka_Loop"]:
		if not lib.has_animation(kl):
			chyby.append("klip " + kl + " chybi")
	_vysledek("postavy_vzhled", chyby.is_empty(), "sad %d, LOD0 <= %d (LOD1 cil %d, tabulka POSTAVA): %s %s" % [sady.size(), lim0, lim1, " ".join(radky), str(chyby)])


## Lide - chovani (postavy_plan.md kroky 2-5, pomocnik 5. 11.): predmety v rukou z katalogu s drzenim, sed jen na
## skutecnem sedaku (vybaveni sveta), hovor ve skupine celem k sobe, rozvrh role rozptyleny, skryta cinnost u dveri,
## animace v dalce bezi (ne ztuhla poza), stin jen zblizka. Vypis LIDE ...; chyby LIDE CHYBA ...
func _lide_chovani() -> void:
	var lide: Node = main.get_node_or_null("World/Lide")
	if lide == null:
		lide = get_tree().root.find_child("Lide", true, false)
	if lide == null:
		_vysledek("lide_chovani", false, "uzel Lide nenalezen")
		return
	var P: Dictionary = lide.get("P")
	var LideS := preload("res://scripts/lide.gd")
	var kat: Dictionary = LideS.katalog()
	var chyby: Array = []
	var ch := func(t: String) -> void:
		chyby.append(t)
		print("LIDE CHYBA ", t)
	var ll: Array = lide.get("_lide")
	var ap0: AnimationPlayer = ll[0]["ap"]
	# 1) predmety v rukou: katalog, model, drzeni, klip existuje; klipy s naradim (Farm_, TreeChopping, Fixing) maji predmet
	var predmetu := 0
	for cid: String in P["cinnosti"]:
		var cn: Dictionary = P["cinnosti"][cid]
		var vr: Dictionary = cn.get("v_rukou", {})
		for kl: String in vr:
			if kl != "*" and not ap0.has_animation(kl):
				ch.call("%s v_rukou: klip %s neni v UAL" % [cid, kl])
			for ruka: String in vr[kl]:
				var id := String(vr[kl][ruka])
				predmetu += 1
				if not kat.has(id):
					ch.call("%s: predmet %s neni v katalogu" % [cid, id])
				if not ResourceLoader.exists("res://modely/predmety/%s.glb" % id):
					ch.call("%s: predmet %s nema model" % [cid, id])
				if not (P["drzeni"] as Dictionary).has(id):
					ch.call("%s: predmet %s nema drzeni" % [cid, id])
		for kl: String in cn.get("klipy", []):
			if (kl.begins_with("Farm_") or kl.begins_with("TreeChopping") or kl.begins_with("Fixing") or kl.begins_with("Prace_Uder") or kl.begins_with("Prace_Kovar")) and not vr.has(kl) and not vr.has("*") and not (Pravidla.cti("postavy", "klipy_rucni") as Array).has(kl):
				ch.call("%s: klip %s s naradim bez predmetu v ruce" % [cid, kl])
	# predmet opravdu v ruce: postava s klipem prace ma pod kosti ruky model
	var lamac: Dictionary = {}
	for c: Dictionary in ll:
		if String(c["o"]["role"]) == "lamac":
			lamac = c
	if not lamac.is_empty():
		var cn0: Dictionary = lamac["cn"]
		lamac["cn"] = P["cinnosti"]["prace_lom"]
		lamac["klip"] = ""
		lide.call("_klip", lamac, String((P["cinnosti"]["prace_lom"]["klipy"] as Array)[0]), 1.0)
		var ruce: Dictionary = lamac["ruce"]
		if String(ruce.get("r_id", "")) != "krumpac" or ruce.get("r_uzel") == null or (ruce["r_uzel"] as Node).get_parent() == null:
			ch.call("lamac s klipem prace nema krumpac na kosti ruky (%s)" % str(ruce.get("r_id", "")))
		else:
			var ba: Node = (ruce["r_uzel"] as Node).get_parent()
			print("LIDE predmet v ruce: %s na %s (%s)" % [ruce["r_id"], ba.get_class(), (ba as BoneAttachment3D).bone_name])
		lamac["cn"] = cn0
	# 2) sed: kazdy blok se sedem - sedak z vybaveni (id ze sedani.sedaky, vyska v toleranci) pod panvi, nebo stoji
	var sd: Dictionary = P["sedani"]
	var sedi := 0
	var stoji := 0
	var vb: Array = sv.data.get("vybaveni", [])
	for c: Dictionary in ll:
		for bl: Dictionary in c["role"]["rozvrh"]:
			var cn: Dictionary = P["cinnosti"][bl["cinnost"]]
			if not bool(cn.get("sed", false)):
				continue
			lide.call("_uvolni", c)
			var m: Array = lide.call("_misto_cinnosti", c, String(bl["kde"]), cn)
			var sk: Dictionary = c["sedak"]
			if sk.is_empty():
				stoji += 1
				print("LIDE sed %s %s: zadny sedak do %.0f m - stoji" % [c["id"], bl["kde"], float(sd["hledat_m"])])
				if (cn.get("klipy_bez_sedu", []) as Array).is_empty():
					ch.call("%s: bez sedaku a bez klipy_bez_sedu" % c["id"])
				continue
			sedi += 1
			var q: Vector2 = sk["sedak"]
			# vzdalenost od pudorysu sedaku (kvadr z katalogu otoceny yaw), ne od stredu: 13. 11. krajni misto 4m hodovni
			# lavice v krcme je 1,50 m od jejiho stredu, ale 1,46 m od stredu vedlejsi 1,8m selske lavice - stred nejblizsiho
			# sedaku s jeho pul delkou hlasil sed mimo sedak, ktery tam nebyl
			var nej := INF
			var vys := 0.0
			var nej_id := ""
			for r: Dictionary in vb:
				if (sd["sedaky"] as Array).has(String(r["id"])):
					var rzq: Array = kat[String(r["id"])]["rozmer"]
					var ywq := float(r["yaw"])
					var dv := q - Vector2(float(r["p"][0]), float(r["p"][2]))
					var lxq := dv.dot(Vector2(cos(ywq), -sin(ywq)))
					var lzq := dv.dot(Vector2(sin(ywq), cos(ywq)))
					var dq := Vector2(maxf(absf(lxq) - float(rzq[0]) * 0.5, 0.0), maxf(absf(lzq) - float(rzq[2]) * 0.5, 0.0)).length()
					if dq < nej:
						nej = dq
						nej_id = String(r["id"])
						vys = float(r["p"][1]) + float(rzq[1])
			var panev_y := float(sk["y"]) + float(sd["vyska_klipu_m"])
			print("LIDE sed %s %s: sedak %.2f m od mista, %s %.2f m od pudorysu, panev %.2f / sedak %.2f, koren %s" % [c["id"], bl["kde"], (m[0] as Vector2).distance_to(q), nej_id, nej, panev_y, vys, (m[0] as Vector2).round()])
			if nej > float(sd["sirka_mista_m"]) * 0.5 or absf(panev_y - vys) > 0.02:
				ch.call("%s sedi mimo sedak (%s %.2f m od pudorysu, panev %.2f, sedak %.2f)" % [c["id"], nej_id, nej, panev_y, vys])
			# Misa 9. 11. r. 82 (hostinec 09-10: hoste sedi u stolu bokem): sedak do ke_stolu_m od stolu - celem ke stolu
			var st_nej := INF
			var st_bod := Vector2.ZERO
			for r: Dictionary in vb:
				if String(r["id"]).begins_with("stul"):
					var rzs: Array = (kat.get(String(r["id"]), {}) as Dictionary).get("rozmer", [1.0, 0.75, 1.0])
					var yws := float(r["yaw"])
					var ps := Vector2(float(r["p"][0]), float(r["p"][2]))
					var lx := clampf((q - ps).dot(Vector2(cos(yws), -sin(yws))), -float(rzs[0]) * 0.5, float(rzs[0]) * 0.5)
					var lz := clampf((q - ps).dot(Vector2(sin(yws), cos(yws))), -float(rzs[2]) * 0.5, float(rzs[2]) * 0.5)
					var bod := ps + Vector2(cos(yws), -sin(yws)) * lx + Vector2(sin(yws), cos(yws)) * lz
					if bod.distance_to(q) < st_nej:
						st_nej = bod.distance_to(q)
						st_bod = bod
			if st_nej < float(sd["ke_stolu_m"]):
				var fw := Vector2(sin(float(sk["yaw"])), cos(float(sk["yaw"])))
				var uh := rad_to_deg(fw.angle_to(st_bod - q))
				print("LIDE sed %s u stolu %.2f m, odchylka od smeru ke stolu %.0f st" % [c["id"], st_nej, absf(uh)])
				if absf(uh) > float(sd["sed_ke_stolu_st"]):
					ch.call("%s sedi u stolu bokem (%.0f st)" % [c["id"], absf(uh)])
		lide.call("_uvolni", c)
	# 2b) r. 82: KAZDE misto na sedacich u stolu (driv jen nejblizsi sedak mista - vsichni hoste dostali tentyz):
	# sedaky se obsazuji jeden po druhem (bez uvolneni), kazde misto do ke_stolu_m od pudorysu stolu celem ke stolu
	var stoly_mist := 0
	var c_sed: Dictionary = ll[0]
	for mk: String in ["hostinec_sin", "hostinec_venku", "krcma_senk"]:
		if not (P["mista"] as Dictionary).has(mk):
			continue
		var mm: Dictionary = P["mista"][mk]
		var obs: Array = []
		for _k in 40:
			var c2 := {"id": "test_sed_%d" % obs.size()}
			var mpos: Array = lide.call("_misto", c_sed, mk)
			if mpos.is_empty():
				break
			var sk2: Dictionary = lide.call("_sedak", c2, mpos[0], String(mm.get("mistnost", "")))
			if sk2.is_empty():
				break
			obs.append(sk2)
			var q2: Vector2 = sk2["sedak"]
			var st2 := INF
			var bod2 := Vector2.ZERO
			for r: Dictionary in vb:
				if String(r["id"]).begins_with("stul"):
					var rz2: Array = (kat.get(String(r["id"]), {}) as Dictionary).get("rozmer", [1.0, 0.75, 1.0])
					var yw2 := float(r["yaw"])
					var ps2 := Vector2(float(r["p"][0]), float(r["p"][2]))
					var ox2 := Vector2(cos(yw2), -sin(yw2))
					var oz2 := Vector2(sin(yw2), cos(yw2))
					var b2 := ps2 + ox2 * clampf((q2 - ps2).dot(ox2), -float(rz2[0]) * 0.5, float(rz2[0]) * 0.5) + oz2 * clampf((q2 - ps2).dot(oz2), -float(rz2[2]) * 0.5, float(rz2[2]) * 0.5)
					if b2.distance_to(q2) < st2:
						st2 = b2.distance_to(q2)
						bod2 = b2
			if st2 < float(sd["ke_stolu_m"]):
				stoly_mist += 1
				var uh2 := rad_to_deg(Vector2(sin(float(sk2["yaw"])), cos(float(sk2["yaw"]))).angle_to(bod2 - q2))
				print("LIDE sed_vsechny %s sedak %s u stolu %.2f m, odchylka %.0f st" % [mk, q2.snapped(Vector2.ONE * 0.01), st2, absf(uh2)])
				if absf(uh2) > float(sd["sed_ke_stolu_st"]):
					ch.call("%s: misto %s sedi u stolu bokem (%.0f st)" % [mk, q2.snapped(Vector2.ONE * 0.01), absf(uh2)])
		for sk2: Dictionary in obs:
			(lide.get("_obsazeno") as Dictionary).erase(sk2["klic"])
	print("LIDE sed_vsechny: mist u stolu %d" % stoly_mist)
	if stoly_mist < 4:
		ch.call("sed u stolu: jen %d mist - test nic neoveril" % stoly_mist)
	# 3) hovor ve skupine: vsichni s hovorem v 17:50 - kazdy ma partnera (nejvys jeden sam), celem ke stredu
	var hv: Dictionary = P["hovor"]
	var hovori: Array = []
	for c: Dictionary in ll:
		var bi: int = lide.call("_blok", c, 17.85)
		if String(c["role"]["rozvrh"][bi]["cinnost"]) == "hovor":
			lide.call("_novy_blok", c, bi, false)
			if String(c.get("cinnost_ted", "hovor")) == "hovor":      # moznost bloku (denni pribeh) muze byt jina
				hovori.append(c)
	var sami := 0
	for c: Dictionary in hovori:
		var p: Vector2 = c["misto"]
		var partner := 0
		for c2: Dictionary in hovori:
			if c2 != c and (c2["misto"] as Vector2).distance_to(p) < float(hv["polomer_m"]) * 2.0 + 0.05:
				partner += 1
				# partner pred postavou (yaw mista miri ke stredu skupiny)
				var k := (c2["misto"] as Vector2) - p
				var fw := Vector2(sin(float(c["yaw_mista"])), cos(float(c["yaw_mista"])))
				if fw.dot(k.normalized()) < 0.0:
					ch.call("hovor %s: partner %s za zady" % [c["id"], c2["id"]])
		if partner == 0:
			sami += 1
		print("LIDE hovor %s u %s: partneru %d" % [c["id"], p.round(), partner])
	if sami > 1:
		ch.call("hovor: %d postav samo (nejvys 1 pri lichem poctu)" % sami)
	if hovori.size() < 2:
		ch.call("hovor v 17:50: jen %d postav - test nic neoveril" % hovori.size())
	# 4) rozvrh: obyvatele stejne role nemeni blok ve stejnou minutu
	var zmeny := {}
	for c: Dictionary in ll:
		var r := String(c["o"]["role"])
		var mn := roundi(float(c["posun_h"]) * 60.0)
		if (zmeny.get(r, []) as Array).has(mn):
			ch.call("rozvrh %s: %s ve stejnou minutu jako jiny %s" % [r, c["id"], r])
		zmeny[r] = zmeny.get(r, []) + [mn]
	print("LIDE rozvrh posun min po rolich %s" % str(zmeny))
	# 5) skryta cinnost (doma, spi, jidlo) u dveri: domu vsi (bod pred dvermi) nebo dvere dilu Pohyb_dvere*/mlyn
	var dvere_body: Array = []
	for e: Dictionary in sv.data.get("pohyb", []):
		var u: Array = e.get("use", e["pos"])
		dvere_body.append(Vector2(float(u[0]), float(u[2])))
	for c: Dictionary in ll:
		for bl: Dictionary in c["role"]["rozvrh"]:
			var cn: Dictionary = P["cinnosti"][bl["cinnost"]]
			if not bool(cn.get("skryty", false)):
				continue
			var m: Array = lide.call("_misto_cinnosti", c, String(bl["kde"]), cn)
			var q: Vector2 = m[0]
			var u_domu := String(bl["kde"]) in ["domov", "dvere"] and not (c["o"]["domov"] as Dictionary).has("misto")
			var nd := INF
			for dq: Vector2 in dvere_body:
				nd = minf(nd, dq.distance_to(q))
			if not u_domu and nd > 1.0:
				ch.call("%s %s %s: skryva se %.1f m od dveri" % [c["id"], bl["cinnost"], bl["kde"], nd])
			elif not u_domu:
				print("LIDE dvere %s %s -> %s (dvere %.1f m)" % [c["id"], bl["kde"], q.round(), nd])
	# 6) LOD animace a stin: postava za anim_do_m (do dosahu) animaci posouva, stin jen do stin_m
	var h6: float = main.day.hour if main.day != null else 12.0
	var c6: Dictionary = ll[0]
	for c: Dictionary in ll:
		var b6: int = lide.call("_blok", c, h6)
		if not bool(P["cinnosti"][c["role"]["rozvrh"][b6]["cinnost"]].get("skryty", false)):
			c6 = c
			lide.call("_novy_blok", c, b6, false)
			break
	var u6: Node3D = c6["uzel"]
	var pp := player.global_position
	var stin_m: float = LideS.STIN_M
	var dosah: float = lide.get("DOSAH")
	var vysl6 := []
	for d6: float in [float(P["do"]) + 10.0, stin_m * 0.5]:
		if d6 >= dosah:
			ch.call("LOD: zkusebni vzdalenost %.0f za dosahem" % d6)
			continue
		# pred kamerou (11. 11.: mimo zaber se neanimuje - postava na vychod od hrace mohla byt za zady)
		var fw6 := -(player.cam as Camera3D).global_basis.z
		fw6.y = 0.0
		fw6 = fw6.normalized() if fw6.length() > 0.01 else Vector3.FORWARD
		u6.position = Vector3(pp.x, pp.y, pp.z) + fw6 * d6
		c6["cesta"] = PackedVector2Array()
		c6["na_miste"] = true
		var ap6: AnimationPlayer = c6["ap"]
		var t0 := ap6.current_animation_position
		for i in 10:
			lide.call("_process_vlastni", 0.1)
		var pohyb := absf(ap6.current_animation_position - t0) > 0.01
		var stin := (c6["geo"][0] as GeometryInstance3D).cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		vysl6.append("%.0f m: animace %s, stin %s" % [d6, "bezi" if pohyb else "STOJI", "ano" if stin else "ne"])
		if not pohyb:
			ch.call("LOD: postava v %.0f m ma ztuhlou pozu" % d6)
		if stin != (d6 < stin_m):
			ch.call("stin: postava v %.0f m stin %s (stin_m %.0f)" % [d6, stin, stin_m])
	print("LIDE LOD %s" % str(vysl6))
	# 7) spanek a dvere (Misa 5. 11.): kazdy obyvatel ma zaznam spanek (postel nebo dira s popisem); zapsana postel se
	# ve svete najde; dvere domu, kam postava vchazi, maji pohyblive kridlo (pohyb skupina)
	var postele := 0
	var diry: Array = []
	for c: Dictionary in ll:
		if bool((c["o"] as Dictionary).get("poutnik", false)):
			continue                                  # poutnici nespi (postavy.json poutnici)
		var sp: Dictionary = (c["o"] as Dictionary).get("spanek", {})
		if sp.is_empty() or (String(sp.get("postel", "")) == "" and String(sp.get("dira", "")) == ""):
			ch.call("%s: chybi zaznam spanek (postel nebo dira)" % c["id"])
			continue
		if String(sp.get("postel", "")) != "":
			var pst: Dictionary = lide.call("_postel", c)
			if pst.is_empty():
				ch.call("%s: postel %s v %s ve svete neni" % [c["id"], sp["postel"], sp["budova"]])
				for m: Dictionary in sv.data.get("mistnosti", []):
					if String(m["name"]).begins_with(String(sp["budova"]) + "_"):
						print("LIDE mistnost %s pos %s size %s yaw %s" % [m["name"], str(m["pos"]), str(m["size"]), str(m.get("yaw", 0.0))])
				for r: Dictionary in sv.data.get("vybaveni", []):
					if String(r["id"]) == String(sp["postel"]):
						print("LIDE postel ve vybaveni %s yaw %s" % [str(r["p"]), str(r.get("yaw", 0.0))])
			else:
				postele += 1
				print("LIDE postel %s v %s: %s" % [c["id"], sp["budova"], (pst["p"] as Vector3).snapped(Vector3.ONE * 0.1)])
		else:
			diry.append("%s (%s)" % [c["id"], sp.get("budova", sp.get("dira", ""))])
		var bi7 := 0
		for i7 in (c["role"]["rozvrh"] as Array).size():
			if String(c["role"]["rozvrh"][i7]["cinnost"]) == "spi":
				bi7 = i7
		var bl7: Dictionary = c["role"]["rozvrh"][bi7]
		var m7: Array = lide.call("_misto_cinnosti", c, String(bl7["kde"]), P["cinnosti"][bl7["cinnost"]])
		var sk7: String = lide.call("_dvere_skupina", m7[0])
		print("LIDE dvere spanku %s: %s skupina %s" % [c["id"], (m7[0] as Vector2).round(), sk7 if sk7 != "" else "ZADNA"])
	print("LIDE spanek: postele %d, diry %s" % [postele, str(diry)])
	# 7b) v hodinu spanku lezi (Misa 0.99993 r. 59: „v noci stoji na luzku“ - prolinani do pozy s tempem 0 se nedokoncilo):
	# z chuze do postele, po 1 s animace je klip spani, hlava a panev v jedne vysce (lezi), panev nad patou luzka
	var lezi := 0
	var pel_i := -1
	for c: Dictionary in ll:
		if lide.call("_postel", c).is_empty():
			continue
		var kos: Skeleton3D = c["kostra"]
		c["v_posteli"] = false
		lide.call("_klip", c, "Walk_Loop", 1.0)
		(c["ap"] as AnimationPlayer).advance(0.3)
		lide.call("_do_postele", c, P["cinnosti"]["spi"])
		(c["ap"] as AnimationPlayer).advance(1.0)
		pel_i = kos.find_bone("pelvis")
		var hd_i := kos.find_bone("Head")
		var yp := (kos.global_transform * kos.get_bone_global_pose(pel_i).origin).y
		var yh := (kos.global_transform * kos.get_bone_global_pose(hd_i).origin).y
		var py := float((c["postel_z"]["p"] as Vector3).y)
		if String(c["klip"]) != String(P["spani"]["klip"]) or absf(yh - yp) > 0.35 or yp < py:
			ch.call("spanek %s: nelezi (klip %s, hlava %.2f, panev %.2f, pata luzka %.2f)" % [c["id"], c["klip"], yh, yp, py])
		else:
			lezi += 1
		c["v_posteli"] = false                      # zpet do hry (umele ulozeni do postele neplati pro dalsi testy)
		c["vchazi"] = 0
	print("LIDE spanek: lezi %d" % lezi)
	# 7c) chuze mrizkou (Misa 0.99993 r. 46: pres zed, po posteli): obchuzky nadvori - kazdy usek bez zdi a nabytku
	# (paprsky 0,35 / 1,0 / 1,6 m nad podlahou zjistenou fyzikou, ne nad mrizkou vysek louky)
	var spc := player.get_world_3d().direct_space_state
	var useku := 0
	for cid: String in ["nosi", "prochazka", "obchuzka_tvrz"]:
		var ob: Array = P["cinnosti"][cid]["obchuzka"]
		for oi in ob.size():
			var a: Vector2 = lide.call("_misto", ll[0], String(ob[oi]))[0]
			var b: Vector2 = lide.call("_misto", ll[0], String(ob[(oi + 1) % ob.size()]))[0]
			var cs: PackedVector2Array = lide.call("cesta", a, b)
			if cs.is_empty() and a.distance_to(b) > 0.5:
				ch.call("chuze %s %s->%s: cesta nenalezena (postava by stala)" % [cid, ob[oi], ob[(oi + 1) % ob.size()]])
			var pq := a
			for qq: Vector2 in cs:
				useku += 1
				for hh: float in [0.35, 1.0, 1.6]:
					var r0 := Vector3(pq.x, float(lide.call("podlaha", pq)) + hh, pq.y)
					var r1 := Vector3(qq.x, float(lide.call("podlaha", qq)) + hh, qq.y)
					var hr := spc.intersect_ray(PhysicsRayQueryParameters3D.create(r0, r1, 0xFFFFFFFF, [player.get_rid()]))
					if not hr.is_empty() and not str((hr["collider"] as Node).get_path()).contains("Pohyb_"):
						ch.call("chuze %s %s->%s: usek (%.1f,%.1f)->(%.1f,%.1f) narazi v %.2f m do %s" % [cid, ob[oi], ob[(oi + 1) % ob.size()], pq.x, pq.y, qq.x, qq.y, hh, str((hr["collider"] as Node).get_path()).right(45)])
						break
				pq = qq
	print("LIDE chuze mrizkou: %d useku obchuzek nadvori, selhani mrizky %d" % [useku, int(lide.get("_nav_selhani"))])
	_mista_prace(lide, ll, P, ch)
	# 8) nabytek (Misa 5. 11. postele, stoly a lavice): kazde luzko (svet data postele, nabytek.json) a sedak vnitrniho mista
	# stoji na podlaze (paprsek dolu), ma nad sebou strop (je v budove), nekoliduje se zdi ani jinym predmetem (krabice
	# pudorysu z katalogu) a postava k nemu dojde dvermi (prohledani mrizky 0,25 m od dveri, kterymi do budovy vchazi;
	# v patre jen vypis - schody mrizka nepozna)
	var n8 := _nabytek_kontrola(lide, ll, kat, P, ch)
	_pribeh_kontrola(lide, ll, P, ch)
	_vysledek("lide_chovani", chyby.is_empty(), "%d chyb %s; predmetu %d, sed %d / stoji %d, hovor %d (sami %d), postele %d, diry spanku %d, nabytek %s" % [chyby.size(), str(chyby.slice(0, 6)), predmetu, sedi, stoji, hovori.size(), sami, postele, diry.size(), n8])


## Hostinec: hrac se nezasekne u stolicek a lavic (Misa 0.99996 r. 98, snimek 16 (-68, 933): zasekl se, pod nohama
## stolicky). Pro kazdou stolicku a lavici hostince (vybaveni do 14 m od stredu): hrac se postavi na jeji misto (na sedak,
## v kolizi) a ma dojit o 1,2 m na vsechny strany (8 smeru) - kazdy smer, kam ho neblokuje jiny predmet nebo zed, se
## musi povest; stolicka smi blokovat nejvys polovinu smeru (jinak je to past). Pak 2 trasy mezi stoly a stolickami
## podle skutecnych poloh (stul-stul, stolicka-stolicka).
func _hostinec_prochod() -> void:
	var stred := Vector2(-67.3, 926.6)
	var chyby: Array = []
	var kus: Array = []
	var podlaha := 0.0
	for r: Dictionary in sv.data["vybaveni"]:
		var q := Vector2(float(r["p"][0]), float(r["p"][2]))
		if q.distance_to(stred) < 14.0 and float(r["p"][1]) < 37.0 and (String(r["id"]).begins_with("stolicka") or String(r["id"]).begins_with("lavice")):
			kus.append([String(r["id"]), q, float(r["p"][1])])
			podlaha = float(r["p"][1])
	if kus.is_empty():
		_vysledek("hostinec_prochod", false, "zadne stolicky a lavice hostince v datech")
		return
	player.set_flying(false)
	var s := ""
	# 1) hrac na miste kazde stolicky a lavice (v kolizi) - nesmi uvaznout
	for k: Array in kus:
		var q: Vector2 = k[1]
		var ok_smeru := 0
		for i in 8:
			var r: Array = await _jdi_poschodi([q, q + Vector2.from_angle(TAU * i / 8.0) * 1.2], float(k[2]), 0.3)
			if bool(r[0]):
				ok_smeru += 1
		if ok_smeru < 4 and q.distance_to(Vector2(-61.5, 921.6)) > 0.5:       # lavice (-61,5, 921,6) je za zdi sine (v tele zdi)
			chyby.append("%s (%.1f, %.1f): vyjde jen %d z 8 smeru" % [k[0], q.x, q.y, ok_smeru])
		s += " %s(%.0f,%.0f)=%d" % [String(k[0]).left(4), q.x, q.y, ok_smeru]
	# 2) mezery kolem nabytku u mista snimku 16 (-68, 933): body 0,8 m od kazdeho kusu do 4 m od mista, odtud hrac
	#    musi dojit o 1,5 m (aspon 1 ze 6 smeru bez uvaznuti; roh u zdi ma volny smer od zdi)
	var misto := Vector2(-68.0, 933.0)
	var mezery := 0
	var uvazlo := 0
	for k: Array in kus:
		var q2: Vector2 = k[1]
		if q2.distance_to(misto) > 4.0:
			continue
		for i in 8:
			var p0 := q2 + Vector2.from_angle(TAU * i / 8.0 + 0.3) * 0.8
			if p0.distance_to(misto) > 4.5:
				continue
			# start jen na volnem miste (kapsle hrace se nesmi protinat s nabytkem ani zdi)
			var sq := PhysicsShapeQueryParameters3D.new()
			var cap := CapsuleShape3D.new()
			cap.radius = 0.28
			cap.height = 1.7
			sq.shape = cap
			sq.exclude = [player.get_rid()]
			sq.transform = Transform3D(Basis(), Vector3(p0.x, float(k[2]) + 0.95, p0.y))
			if not player.get_world_3d().direct_space_state.intersect_shape(sq, 1).is_empty():
				continue
			mezery += 1
			var ok4 := 0
			var kde := ""
			for sm in 6:
				var r2: Array = await _jdi_poschodi([p0, p0 + Vector2.from_angle(TAU * sm / 6.0 + 0.7) * 1.5], float(k[2]), 0.15)
				if bool(r2[0]):
					ok4 += 1
				else:
					kde += " [%s]" % String(r2[1]).get_slice("narazil na", 1)
			if ok4 == 0:
				uvazlo += 1
				chyby.append("bod (%.1f, %.1f) u %s: uvazl na vsechny strany, narazil na%s" % [p0.x, p0.y, k[0], kde])
	s += " | mezer %d, uvaznuti %d" % [mezery, uvazlo]
	_vysledek("hostinec_prochod", chyby.is_empty(), "%d chyb %s; smeru z 8:%s" % [chyby.size(), str(chyby.slice(0, 6)), s])


## Chuze hrace po bodech (x, z) ve vysce podlahy (ne _ground_hi: nad mistnosti je strecha); start o vyska_nad m nad podlahou.
## Vraci [ok, text]; ok = vsechny body do 0,5 m, hrac se nezasekl (3 s), nepropadl.
func _jdi_poschodi(body: Array, podlaha: float, vyska_nad: float) -> Array:
	var a: Vector2 = body[0]
	player.place(Vector3(a.x, podlaha + vyska_nad, a.y), Vector3(a.x, podlaha + 1.6, a.y + 1.0))
	for i in 20:
		await get_tree().physics_frame
	for j in range(1, body.size()):
		var wp: Vector2 = body[j]
		var stuck := 0.0
		var t := 0.0
		var last := player.global_position
		while Vector2(wp.x - player.global_position.x, wp.y - player.global_position.z).length() > 0.5:
			var to := Vector2(wp.x - player.global_position.x, wp.y - player.global_position.z)
			player.yaw = atan2(-to.x, -to.y)
			player.move_input = Vector2(0.0, 1.0)
			await get_tree().physics_frame
			t += 1.0 / 60.0
			if player.global_position.distance_to(last) > 0.15:
				last = player.global_position
				stuck = 0.0
			else:
				stuck += 1.0 / 60.0
			if stuck > 1.0 or t > 8.0 or player.global_position.y < podlaha - 2.0:
				player.move_input = Vector2.ZERO
				var kdo := ""
				for si in player.get_slide_collision_count():
					var ow := player.get_slide_collision(si).get_collider() as Node
					kdo += " %s" % (str(ow.get_parent().name) if ow else "?")
				return [false, "uvazl u bodu %d (%.1f, %.1f) y %.2f, cil (%.1f, %.1f), narazil na%s" % [j, player.global_position.x, player.global_position.z, player.global_position.y, wp.x, wp.y, kdo]]
	player.move_input = Vector2.ZERO
	return [true, "ok"]


## Trava v hostinci (Misa 0.99996 r. 92, snimek 15 (-63, 930): trava u dveri uvnitr). Skutecne instance MultiMeshu
## (Louka, Rostliny, TravaGPU) po dostaveni okoli hostince: zadna s pocatkem v pudorysu stavby (sv._uvnitr, cely obrys
## bez zmenseni) ani do pasma budova pruchod_m + dvur_m od stredu dveri (Pohyb_dvere*, pohyb.kind dvere) - tam se rostlina
## nesmi objevit (v_pruchodu). Mimo to rostlina uvnitr nesmi stat ani pod strechou (paprsek nahoru, 4 m).
func _hostinec_trava() -> void:
	var stred := Vector2(-67.3, 926.6)
	var louka: Node = main.get_node_or_null("Louka")
	var inv := Transform3D()
	var bb := AABB()
	for st: Array in sv._uvnitr:
		if st.size() > 2:
			continue
		var q: Vector3 = (st[0] as Transform3D) * Vector3(stred.x, 0.0, stred.y)
		var b2: AABB = st[1]
		if q.x > b2.position.x and q.x < b2.end.x and q.z > b2.position.z and q.z < b2.end.z:
			inv = st[0]
			bb = b2
	bb = bb.grow(0.1)                                # cely obrys (uvnitr ho svet smenuje o 0,1 m)
	print("HOSTINEC_TRAVA obrys stavby (misto): x %.1f..%.1f, z %.1f..%.1f" % [bb.position.x, bb.end.x, bb.position.z, bb.end.z])
	var dvere: Array = []
	for e: Dictionary in sv.data.get("pohyb", []):
		var p3: Array = e.get("use", e["pos"])
		if String(e.get("kind", "")) == "dvere" and Vector2(float(p3[0]), float(p3[2])).distance_to(stred) < 14.0:
			dvere.append(Vector2(float(p3[0]), float(p3[2])))
	var r_dv := float(sv.pasma()["budova"]["pruchod_m"]) + float(sv.pasma()["budova"]["dvur_m"])     # jako svet.v_pruchodu
	await main.fast_travel(Vector3(-63.0, 0.0, 930.0), Vector3(-66.0, 1.6, 932.0), 0.0, "test")
	for f in 1800:
		await get_tree().process_frame
		if louka == null or louka.okoli_hotove(40.0):
			break
	var oblast := AABB(Vector3(stred.x - 20.0, -50.0, stred.y - 20.0), Vector3(40.0, 200.0, 40.0))
	var inst := 0
	var spatne: Array = []
	# 14. 11. (snimek Misy: trava u dveri a u stolu v hostinci, test hlasil 0 - hlidal jen Louka/Rostliny/TravaGPU):
	# vsechny MultiMesh ve scene
	for kor: String in ["*"]:
		var uz: Node = get_tree().root
		for g: Node in uz.find_children("*", "MultiMeshInstance3D", true, false):
			var mmi := g as MultiMeshInstance3D
			if not mmi.is_visible_in_tree() or mmi.multimesh == null or not (mmi.global_transform * mmi.get_aabb()).intersects(oblast):
				continue
			var mm := mmi.multimesh
			var n := mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
			for i in n:
				var p := mmi.global_transform * mm.get_instance_transform(i).origin
				if not oblast.has_point(p):
					continue
				inst += 1
				var l: Vector3 = inv * p
				var v_obrysu: bool = l.x > bb.position.x and l.x < bb.end.x and l.z > bb.position.z and l.z < bb.end.z and p.y < 37.5
				var u_dveri := false
				for dv: Vector2 in dvere:
					u_dveri = u_dveri or dv.distance_to(Vector2(p.x, p.z)) < r_dv
				if v_obrysu or u_dveri:
					if spatne.size() < 40:
						print("HOSTINEC_TRAVA %s (%.2f, %.2f, %.2f) misto (%.1f, %.1f) %s uzel %s" % [mm.mesh.resource_name if mm.mesh else "?", p.x, p.y, p.z, l.x, l.z,
								"v obrysu" if v_obrysu else "u dveri", str(mmi.get_path()).right(50)])
					spatne.append(p)
	# 14. 11.: i samostatne site rostlin (MeshInstance3D: trs, trava, kapradi, ker) uvnitr obrysu - Misa videla travu u dveri a u stolu
	var sl_rostl: Array = Pravidla.cti("modely", "rostliny_jmena")
	for mi: Node in get_tree().root.find_children("*", "MeshInstance3D", true, false):
		var m3 := mi as MeshInstance3D
		if not m3.is_visible_in_tree() or m3.mesh == null:
			continue
		var p3 := m3.global_transform * m3.get_aabb().get_center()
		if not oblast.has_point(p3):
			continue
		var l3: Vector3 = inv * p3
		if not (l3.x > bb.position.x and l3.x < bb.end.x and l3.z > bb.position.z and l3.z < bb.end.z and p3.y < 37.5):
			continue
		var jm := (String(m3.name) + " " + m3.mesh.resource_name + " " + m3.mesh.resource_path).to_lower()
		if sl_rostl.any(func(w: String) -> bool: return jm.contains(w)):
			print("HOSTINEC_TRAVA sit %s (%.1f, %.1f, %.1f) uzel %s" % [jm, p3.x, p3.y, p3.z, str(m3.get_path()).right(70)])
			spatne.append(p3)
	_vysledek("hostinec_trava", inst > 0 and spatne.is_empty(), "instanci v okoli %d, v obrysu stavby nebo u dveri %d, dveri %d" % [inst, spatne.size(), dvere.size()])


## Zlab odtoku mlyna (Misa 0.99996 r. 91, snimky 04-05: zlab prazdny, voda tece siroky pas vedle): hladina lednice
## (mlyn_voda.json lednice.body, svet) musi byt nad nejblizsim pevnym povrchem pod osou zlabu (kolize hry: dno
## modelu Mlyn_Lednice, teren dilu) a nejvyse mlyn_zlab hloubka_max nad nim. Paprsek jen 1,2 m nad hladinou (nad ni je
## vantrok a kolo). Vypis kazdeho 3. bodu.
func _mlyn_zlab() -> void:
	var P = preload("res://scripts/pravidla.gd")
	var d: Dictionary = P.cti("voda", "mlyn")["dil"]
	var f := FileAccess.open("res://tools/krok_b/mlyn_voda.json", FileAccess.READ)
	var body: Array = (JSON.parse_string(f.get_as_text()) as Dictionary)["lednice"]["body"]
	var xf := Transform3D(Basis(Vector3.UP, float(d["natoceni"])), Vector3(float(d["stred"][0]), float(d["y_dvora"]), float(d["stred"][1])))
	var space := player.get_world_3d().direct_space_state
	var chyby: Array = []
	for i in body.size():
		var w: Vector3 = xf * Vector3(float(body[i][0]), float(body[i][1]), float(body[i][2]))
		var q := PhysicsRayQueryParameters3D.create(w + Vector3(0, 1.2, 0), w - Vector3(0, 6.0, 0))
		var h := space.intersect_ray(q)
		var nm := "nic"
		var y := -999.0
		if not h.is_empty():
			y = float(h["position"].y)
			nm = str((h["collider"] as Node).get_parent().name)
		var nad := w.y - y
		if i % 3 == 0 or nad < 0.05:
			print("MLYN_ZLAB bod %d (%.1f, %.1f) hladina %.2f, povrch %.2f (%s), hloubka vody %.2f" % [i, w.x, w.z, w.y, y, nm, nad])
		if nad < 0.05 or nad > 0.8:
			chyby.append("bod %d (%.1f, %.1f): voda %.2f m nad povrchem %s" % [i, w.x, w.z, nad, nm])
	_vysledek("mlyn_zlab", chyby.is_empty(), "%d chyb %s" % [chyby.size(), str(chyby.slice(0, 5))])


## V interieru zadna trava (Misa 0.99993 r. 57, snimky misa_6_11/30-31: trsy v sini hostince u sudu a dveri). Test
## interier meri jen louka._vzorek; tady skutecne instance: kazdy MultiMesh louky a rostlin (uzly Louka, Rostliny) v okoli
## hostince a nadvori tvrze po dostaveni bunek - pocatek instance v pudorysu mistnosti (svet.info rooms, od podlahy do
## stropu) = chyba s cestou uzlu (zdroj).
func _interier_trsy() -> void:
	var louka: Node = main.get_node_or_null("Louka")
	var spatne: Array = []
	var inst := 0
	var rooms: Array = (sv.info as Dictionary).get("rooms", [])
	for kde: Vector2 in [Vector2(-66.0, 929.0), Vector2(0.0, 0.0)]:
		await main.fast_travel(Vector3(kde.x, 0.0, kde.y), Vector3(kde.x + 3.0, 1.6, kde.y), 0.0, "test")
		for f in 1800:
			await get_tree().process_frame
			if louka == null or louka.okoli_hotove(40.0):
				break
		var oblast := AABB(Vector3(kde.x - 30.0, -50.0, kde.y - 30.0), Vector3(60.0, 200.0, 60.0))
		for kor: String in ["Louka", "Rostliny", "TravaGPU"]:
			var uz := get_tree().root.find_child(kor, true, false)
			if uz == null:
				continue
			for g: Node in uz.find_children("*", "MultiMeshInstance3D", true, false):
				var mmi := g as MultiMeshInstance3D
				if not mmi.is_visible_in_tree() or mmi.multimesh == null or not (mmi.global_transform * mmi.get_aabb()).intersects(oblast):
					continue
				var mm := mmi.multimesh
				var n := mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
				for i in n:
					var p := mmi.global_transform * mm.get_instance_transform(i).origin
					if not oblast.has_point(p):
						continue
					inst += 1
					for r: Dictionary in rooms:
						var ab: AABB = r["aabb"]
						var q: Vector3 = (r["inv"] as Transform3D) * p if r.has("inv") else p
						if q.x > ab.position.x + 0.05 and q.x < ab.end.x - 0.05 and q.z > ab.position.z + 0.05 and q.z < ab.end.z - 0.05 \
								and q.y > ab.position.y - 0.3 and q.y < ab.end.y:
							if spatne.size() < 30:
								print("INTERIER_TRSY %s v %s (%.2f, %.2f, %.2f) uzel %s" % [mmi.multimesh.mesh.resource_name if mmi.multimesh.mesh else "?", r["name"], p.x, p.y, p.z, str(mmi.get_path()).right(60)])
							spatne.append(r["name"])
							break
	_vysledek("interier_trsy", inst > 0 and spatne.is_empty(), "instanci v okoli %d, v mistnostech %d %s" % [inst, spatne.size(), str(spatne.slice(0, 5))])


## Spanek ve hre (Misa 0.99993 r. 59 „v noci stoji na luzku“, 9. 11. r. 85 „v ubytovne stoji postava na posteli“):
## hrac v budove s luzky, hodina spanku - postavy dojdou samy (ne umele _do_postele jako 7b), pak kazda, ktera ma
## cinnost se spankem a je uvnitr, lezi (klip spani, hlava a panev v jedne vysce); nikdo, kdo nelezi, nestoji nad
## pudorysem luzka (ani rano pri vstavani). Budovy: ubytovna tvrze a dum_4 (439,787).
func _spanek_hra() -> void:
	var lide: Node = main.get_node_or_null("World/Lide")
	if lide == null:
		lide = get_tree().root.find_child("Lide", true, false)
	if lide == null:
		_vysledek("spanek_hra", false, "uzel Lide nenalezen")
		return
	var P: Dictionary = lide.get("P")
	var ll: Array = lide.get("_lide")
	var kat: Dictionary = preload("res://scripts/lide.gd").katalog()
	var chyby: Array = []
	var lezi := 0
	var h0: float = main.day.hour
	var nad_luzkem := func(c: Dictionary) -> String:
		var u: Node3D = c["uzel"]
		for r: Dictionary in sv.data.get("postele", []):
			var rz: Array = (kat.get(String(r["id"]), {}) as Dictionary).get("rozmer", [1.0, 0.5, 2.0])
			var pp: Vector3 = r["p"]
			var dq := Vector2(u.global_position.x - pp.x, u.global_position.z - pp.z)
			var yw := float(r["yaw"])
			if absf(dq.dot(Vector2(cos(yw), -sin(yw)))) < float(rz[0]) * 0.5 - 0.05 and absf(dq.dot(Vector2(sin(yw), cos(yw)))) < float(rz[2]) * 0.5 - 0.05 \
					and u.global_position.y > pp.y + 0.15 and u.global_position.y < pp.y + 1.2:
				return String(r["id"])
		return ""
	for kde: Array in [["tvrz_ubytovna", Vector3(13.0, 0.0, 9.5), Vector3(13.0, 1.0, 13.0)], ["dum_4", Vector3(438.5, 0.0, 788.5), Vector3(436.5, 5.0, 786.6)]]:
		await main.fast_travel(kde[1], kde[2], 0.0, "test")
		for hod: float in [23.5, 6.2, 10.0]:
			main.day.hour = hod
			var spat := 0
			for f in (2400 if hod > 12.0 else 900):
				await get_tree().process_frame
				main.day.hour = hod
				spat = 0
				for c: Dictionary in ll:
					if not (c["uzel"] as Node3D).visible:
						continue
					var lz := bool(c.get("v_posteli", false))
					var nl := String(nad_luzkem.call(c))
					if not lz and nl != "" and chyby.size() < 20 and not chyby.any(func(t: String) -> bool: return t.begins_with(String(c["id"]) + " ")):
						chyby.append("%s %.1f h: stoji nad luzkem %s (klip %s, cinnost %s, y %.2f)" % [c["id"], hod, nl, c["klip"], str((c["cn"] as Dictionary).keys()), (c["uzel"] as Node3D).global_position.y])
					var sp: Dictionary = (c["o"] as Dictionary).get("spanek", {})
					if String(sp.get("budova", "")) != String(kde[0]):
						continue
					if bool((c["cn"] as Dictionary).get("spanek", false)) and int(c.get("vchazi", 0)) == 2:
						spat += 1
				var ocek := 0
				for c2: Dictionary in ll:
					if String(((c2["o"] as Dictionary).get("spanek", {}) as Dictionary).get("budova", "")) == String(kde[0]) and bool((c2["cn"] as Dictionary).get("spanek", false)):
						ocek += 1
				if f > 300 and hod > 12.0 and spat >= ocek:
					break
			if hod > 12.0:
				var pel := -1
				for c: Dictionary in ll:
					var sp: Dictionary = (c["o"] as Dictionary).get("spanek", {})
					if String(sp.get("budova", "")) != String(kde[0]) or not bool((c["cn"] as Dictionary).get("spanek", false)) or int(c.get("vchazi", 0)) != 2:
						continue
					var kos: Skeleton3D = c["kostra"]
					pel = kos.find_bone("pelvis")
					var yp := (kos.global_transform * kos.get_bone_global_pose(pel).origin).y
					var yh := (kos.global_transform * kos.get_bone_global_pose(kos.find_bone("Head")).origin).y
					var ok := bool(c.get("v_posteli", false)) and String(c["klip"]) == String(P["spani"]["klip"]) and absf(yh - yp) < 0.35
					print("SPANEK_HRA %s %s %.1f h: v posteli %s klip %s hlava %.2f panev %.2f viditelny %s" % [kde[0], c["id"], hod, c.get("v_posteli", false), c["klip"], yh, yp, (c["uzel"] as Node3D).visible])
					if ok:
						lezi += 1
					else:
						chyby.append("%s %s: spi, ale nelezi (klip %s, hlava %.2f, panev %.2f)" % [kde[0], c["id"], c["klip"], yh, yp])
	main.day.hour = h0
	_vysledek("spanek_hra", lezi > 0 and chyby.is_empty(), "lezi %d, chyby %s" % [lezi, str(chyby.slice(0, 8))])


## Chodidla na zemi (Misa 9. 11. KCD kvalita; postavy.json nohy_ik): stojici postavy do nohy_ik.do_m od hrace (nadvori
## tvrze, ves) - spicka (ball_*) kazde nohy, ktera stoji (nizsi z obou), nejvys test_nohy_m nad / pod zemi pod ni
## (paprsek), a zadna spicka vic nez test_nohy_m pod zemi. Vypise i stav bez IK (modifikator vypnuty) pro srovnani.
func _nohy_na_zemi() -> void:
	# neni v seznamu testu, dokud je nohy_ik vypnute (postavy.json nohy_ik._stav) - pro overeni pridat do seznamu
	var lide: Node = main.get_node_or_null("World/Lide")
	if lide == null:
		lide = get_tree().root.find_child("Lide", true, false)
	if lide == null:
		_vysledek("nohy_na_zemi", false, "uzel Lide nenalezen")
		return
	var P: Dictionary = lide.get("P")
	var D: Dictionary = P["nohy_ik"]
	var ll: Array = lide.get("_lide")
	var sp := player.get_world_3d().direct_space_state
	var mez := float(D["test_nohy_m"])
	var chyby: Array = []
	var mereno := 0
	var h0: float = main.day.hour
	main.day.hour = 10.0
	var vysl := {}
	for kde: Vector3 in [Vector3(-2.0, 0.0, 6.0), Vector3(430.0, 0.0, 800.0)]:
		await main.fast_travel(kde, kde + Vector3(0, 1.6, 3.0), 0.0, "test")
		for f in 600:
			await get_tree().process_frame
			main.day.hour = 10.0
		for ik: bool in [false, true]:
			for c: Dictionary in ll:
				if c.has("nohy_ik"):
					(c["nohy_ik"] as Node).set("D", D if ik else {})
			for f in 20:
				await get_tree().process_frame
			var odch: Array = []
			for c: Dictionary in ll:
				var u: Node3D = c["uzel"]
				if not u.visible or u.global_position.distance_to(player.global_position) > float(D["do_m"]) or bool(c.get("sedi", false)) or bool(c.get("v_posteli", false)) or not bool(c["na_miste"]):
					continue
				var ks: Skeleton3D = c["kostra"]
				var dz: Array = []
				for st in ["l", "r"]:
					var ib := ks.find_bone("ball_" + st)
					var w := ks.global_transform * ks.get_bone_global_pose(ib).origin
					# vyska klubu spicky nad podrazkou = klidova poza (koren na zemi)
					var klid := (ks.global_transform * ks.get_bone_global_rest(ib).origin).y - u.global_position.y
					var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(w + Vector3(0, 0.6, 0), w - Vector3(0, 0.8, 0), int(D["maska"])))
					if not h.is_empty():
						dz.append(w.y - klid - (h["position"] as Vector3).y)
				if dz.size() < 2:
					continue
				var nizsi := minf(float(dz[0]), float(dz[1]))
				odch.append(absf(nizsi))
				if ik:
					mereno += 1
					print("NOHY %s %s: spicky nad zemi %.3f / %.3f m (klip %s)" % [str(kde.round()), c["id"], float(dz[0]), float(dz[1]), c["klip"]])
					if absf(nizsi) > mez or minf(float(dz[0]), float(dz[1])) < -mez:
						chyby.append("%s %.2f m" % [c["id"], nizsi])
			odch.sort()
			vysl["%s %s" % [str(kde.round()), "IK" if ik else "bez IK"]] = "%d postav, nejhorsi %.3f m" % [odch.size(), float(odch.back()) if not odch.is_empty() else 0.0]
	for c: Dictionary in ll:
		if c.has("nohy_ik"):
			(c["nohy_ik"] as Node).set("D", D)
	main.day.hour = h0
	print("NOHY srovnani %s" % str(vysl))
	_vysledek("nohy_na_zemi", mereno > 0 and chyby.is_empty(), "mereno %d, chyby %s; %s" % [mereno, str(chyby.slice(0, 6)), str(vysl)])


## Misto prace bez rostlin (kontrola snimku 9. 11., docs/screens/postavy_9_11/lom1d.jpg: delnici v lomu stoji v trsech
## rostlin u paty skalni steny): kolem mist s praci (postavy.json u_predmetu.bez_rostlin: lom, zahon...) do
## bez_rostlin_m zadna instance Louka / Rostliny / TravaGPU vyssi nez nizka_m (nizky drn smi). Vypise druh rostliny.
func _prace_rostliny() -> void:
	var lide: Node = main.get_node_or_null("World/Lide")
	if lide == null:
		lide = get_tree().root.find_child("Lide", true, false)
	if lide == null:
		_vysledek("prace_rostliny", false, "uzel Lide nenalezen")
		return
	var P: Dictionary = lide.get("P")
	var br: Dictionary = P["u_predmetu"]["bez_rostlin"]
	var ll: Array = lide.get("_lide")
	var spatne: Array = []
	var mist := 0
	for k: String in br["mista"]:
		var q: Vector2 = lide.call("_misto", ll[0], k)[0]
		var y := float(sv.call("_vyska", q.x, q.y))
		await main.fast_travel(Vector3(q.x + 4.0, y, q.y), Vector3(q.x, y + 1.0, q.y), 0.0, "test")
		var louka: Node = main.get_node_or_null("Louka")
		for f in 1800:
			await get_tree().process_frame
			if louka == null or louka.okoli_hotove(30.0):
				break
		for f in 30:
			await get_tree().process_frame
		mist += 1
		var r := float(br["polomer_m"])
		var n := 0
		var druhy := {}
		var okoli := 0
		var druhy6 := {}
		for kor: String in ["Louka", "Rostliny", "TravaGPU"]:
			var uz := get_tree().root.find_child(kor, true, false)
			if uz == null:
				continue
			for g: Node in uz.find_children("*", "MultiMeshInstance3D", true, false):
				var mmi := g as MultiMeshInstance3D
				if not mmi.is_visible_in_tree() or mmi.multimesh == null:
					continue
				var mm := mmi.multimesh
				var cnt := mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
				for i in cnt:
					var xf := mmi.global_transform * mm.get_instance_transform(i)
					var p := xf.origin
					if Vector2(p.x - q.x, p.z - q.y).length() < 6.0 and absf(p.y - y) < 3.0:
						okoli += 1
						var jm6 := "%s/%s" % [kor, mm.mesh.resource_name if mm.mesh and mm.mesh.resource_name != "" else String(mmi.name)]
						druhy6[jm6] = int(druhy6.get(jm6, 0)) + 1
					if Vector2(p.x - q.x, p.z - q.y).length() > r or absf(p.y - y) > 2.0:
						continue
					var vys := (mm.mesh.get_aabb().size.y if mm.mesh else 0.0) * xf.basis.get_scale().y
					if vys <= float(br["nizka_m"]):
						continue
					n += 1
					var jm := "%s/%s" % [kor, mm.mesh.resource_name if mm.mesh and mm.mesh.resource_name != "" else String(mmi.name)]
					druhy[jm] = int(druhy.get(jm, 0)) + 1
		print("PRACE_ROSTLINY %s (%.1f, %.1f): %d rostlin vyssich nez %.2f m do %.1f m %s; do 6 m vsech %d %s" % [k, q.x, q.y, n, float(br["nizka_m"]), r, str(druhy), okoli, str(druhy6)])
		if okoli == 0:
			spatne.append("%s: v okoli 6 m zadna instance (test nevidi rostliny)" % k)
		if n > 0:
			spatne.append("%s %d %s" % [k, n, str(druhy.keys().slice(0, 3))])
	_vysledek("prace_rostliny", mist > 0 and spatne.is_empty(), "mist %d, s rostlinami %s" % [mist, str(spatne)])


## Mista cinnosti postav (Misa 0.99994 r. 48, 57, 63, 71): kazde misto z postavy.json ma do cil_m volnou bunku mrizky
## (ne ve zdi jako nadvori_brana (-3,14)); lom u paty skalni steny a krumpac dosahne na skalu; zahon - misto u dlouhe
## strany zahonu, dva lide ne v sobe; obsluha hostince u cela stolu; rozestup cilu (tri s kbeliky na jednom miste).
func _mista_prace(lide: Node, ll: Array, P: Dictionary, ch: Callable) -> void:
	var sp := player.get_world_3d().direct_space_state
	var bb := float(P["graf"]["mrizka"]["bunka_m"])
	var cil_m := float(P["graf"]["mrizka"]["cil_m"])
	var n_ok := 0
	for k: String in P["mista"]:
		var z: Dictionary = P["mista"][k]
		if not (z.has("p") or z.has("lom_stena_z") or z.has("u_predmetu")):
			continue
		var q: Vector2 = lide.call("_misto", ll[0], k)[0]
		var y0 := float(lide.call("podlaha", q))
		var volno := false
		var rr := ceili(cil_m / bb)
		for dx in range(-rr, rr + 1):
			for dz in range(-rr, rr + 1):
				if not volno and Vector2(dx, dz).length() * bb <= cil_m and not is_nan(float(lide.call("_nav_bunka", lide.call("_nav_ij", q) + Vector2i(dx, dz), y0))):
					volno = true
		if not volno:
			ch.call("misto %s (%.1f,%.1f): do %.1f m zadna pruchozi bunka (ve zdi/predmetu)" % [k, q.x, q.y, cil_m])
		else:
			n_ok += 1
	# lom: u paty steny, celem ke skale, paprsek ve vysce rukou do dosahu narazi do skaly/terenu
	var lp: Dictionary = P["lom"]
	for k: String in ["lom_stena_1", "lom_stena_2"]:
		var m: Array = lide.call("_misto", ll[0], k)
		var q: Vector2 = m[0]
		var pata := float(sv.call("lom_stena_x", q.y))
		var y := float(sv.call("_vyska", q.x, q.y))
		var fw := Vector3(sin(float(m[1])), 0.0, cos(float(m[1])))
		var tref := ""
		for hh: float in [0.6, 1.0, 1.4]:
			var h := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(q.x, y + hh, q.y), Vector3(q.x, y + hh, q.y) + fw * float(lp["dosah_m"]), 0xFFFFFFFF, [player.get_rid()]))
			if not h.is_empty():
				tref = "%.2f m %s" % [Vector3(q.x, y + hh, q.y).distance_to(h["position"]), str((h["collider"] as Node).get_path()).right(50)]
				break
		var yd := float(sv.call("_vyska", q.x, q.y))
		var nad := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(q.x, yd + 0.3, q.y), Vector3(q.x, yd + float(lp["volno_nad_m"]), q.y), 0xFFFFFFFF, [player.get_rid()]))
		if not nad.is_empty():
			ch.call("lom %s: nad hlavou %s (pod lesenim)" % [k, str((nad["collider"] as Node).get_path()).right(40)])
		print("LIDE lom %s: (%.1f,%.1f) %.2f m od paty steny, podlaha %.2f, dno %.2f, skala %s" % [k, q.x, q.y, q.x - pata, y, yd, tref])
		if tref == "" or not (tref.contains("Teren") or tref.to_lower().contains("lom") or tref.to_lower().contains("skal")):
			ch.call("lom %s: misto %.2f m od paty steny, skala v dosahu %s" % [k, q.x - pata, tref if tref != "" else "ne"])
	# zahony: kazdy, kdo ma v rozvrhu zahon, stoji u dlouhe strany zahonu (ne vedle), dva ne v sobe
	var body: Array = []
	var puv: Array = ll.map(func(c0: Dictionary) -> Variant: return c0.get("misto"))
	var obs: Dictionary = lide.get("_obsazeno")
	var obs0: Dictionary = obs.duplicate()
	for c: Dictionary in ll:
		for bl: Dictionary in c["role"]["rozvrh"]:
			if String(bl["cinnost"]) == "zahon":
				var m: Array = lide.call("_misto_cinnosti", c, String(bl["kde"]), P["cinnosti"]["zahon"])
				# vzdalenost od obdelniku zahonu (katalog rozmer, natoceni): u zahonu = do od_m (+ pul bunky)
				var nej := INF
				for r: Dictionary in sv.data["vybaveni"]:
					if String(r["id"]).begins_with(String(P["u_predmetu"]["zahrada"])):
						var rz: Array = (lide.call("katalog") as Dictionary).get(String(r["id"]), {}).get("rozmer", [3.07, 0.37, 1.17])
						var yw := float(r["yaw"])
						var dv: Vector2 = (m[0] as Vector2) - Vector2(float(r["p"][0]), float(r["p"][2]))
						var lx := absf(dv.dot(Vector2(cos(yw), -sin(yw)))) - float(rz[0]) * 0.5
						var lz := absf(dv.dot(Vector2(sin(yw), cos(yw)))) - float(rz[2]) * 0.5
						nej = minf(nej, Vector2(maxf(lx, 0.0), maxf(lz, 0.0)).length())
				var v_zah := 0
				for r: Dictionary in sv.data["vybaveni"]:
					if String(r["id"]).begins_with(String(P["u_predmetu"]["zahrada"])):
						var rz2: Array = (lide.call("katalog") as Dictionary).get(String(r["id"]), {}).get("rozmer", [3.07, 0.37, 1.17])
						var dv2: Vector2 = (m[0] as Vector2) - Vector2(float(r["p"][0]), float(r["p"][2]))
						if absf(dv2.dot(Vector2(cos(float(r["yaw"])), -sin(float(r["yaw"]))))) < float(rz2[0]) * 0.5 + 0.12 and absf(dv2.dot(Vector2(sin(float(r["yaw"])), cos(float(r["yaw"]))))) < float(rz2[2]) * 0.5 + 0.12:
							v_zah += 1
				if v_zah > 0:
					ch.call("zahon %s: misto prace (%.2f, %.2f) v zahonu" % [c["id"], (m[0] as Vector2).x, (m[0] as Vector2).y])
				if nej > float(P["u_predmetu"]["od_m"]) + 0.15:
					ch.call("zahon %s: misto prace %.2f m od okraje zahonu (vedle zahonu)" % [c["id"], nej])
				for b2: Array in body:
					if (b2[1] as Vector2).distance_to(m[0]) < float(P["rozestup"]["misto_m"]) * 0.99:
						ch.call("zahon %s a %s: mista prace %.2f m od sebe (v sobe)" % [c["id"], b2[0], (b2[1] as Vector2).distance_to(m[0])])
				body.append([c["id"], m[0]])
				c["misto"] = m[0]
				break
	print("LIDE zahony: %d lidi u zahonu" % body.size())
	obs.clear()
	obs.merge(obs0)
	for i in ll.size():
		ll[i]["misto"] = puv[i]
	# obsluha hostince: cela stolu v sini, obchuzka se stoly, hostinsky i senkyrka ji maji v rozvrhu
	for k: String in ["hostinec_stul_1", "hostinec_stul_2"]:
		var q: Vector2 = lide.call("_misto", ll[0], k)[0]
		if q == Vector2.ZERO:
			ch.call("hostinec %s: stul nenalezen" % k)
		# Misa 9. 11. (hospoda_sin2): obsluha tesne za zady sediciho - misto od pudorysu sedaku >= u_predmetu.od_sedaku_m
		var od_sed := INF
		for r: Dictionary in sv.data["vybaveni"]:
			if (P["sedani"]["sedaky"] as Array).has(String(r["id"])) and Vector2(float(r["p"][0]), float(r["p"][2])).distance_to(q) < 4.0:
				var rz3: Array = (lide.call("katalog") as Dictionary).get(String(r["id"]), {}).get("rozmer", [0.4, 0.45, 0.4])
				var dv3: Vector2 = q - Vector2(float(r["p"][0]), float(r["p"][2]))
				var lx3 := absf(dv3.dot(Vector2(cos(float(r["yaw"])), -sin(float(r["yaw"]))))) - float(rz3[0]) * 0.5
				var lz3 := absf(dv3.dot(Vector2(sin(float(r["yaw"])), cos(float(r["yaw"]))))) - float(rz3[2]) * 0.5
				od_sed = minf(od_sed, Vector2(maxf(lx3, 0.0), maxf(lz3, 0.0)).length())
		print("LIDE obsluha %s (%.2f, %.2f): od sedaku %.2f m" % [k, q.x, q.y, od_sed])
		if od_sed < float(P["u_predmetu"]["od_sedaku_m"]) - 0.01:
			ch.call("hostinec %s: obsluha %.2f m od sedaku (za zady sediciho)" % [k, od_sed])
	for rid: String in ["hostinsky", "senkyrka"]:
		var ma := false
		for bl: Dictionary in P["role"][rid]["rozvrh"]:
			# 10. 11.: i moznosti bloku (denni pribeh - obsluha jen pri hostech)
			for m9: Dictionary in [bl] + (bl.get("moznosti", []) as Array):
				ma = ma or (P["cinnosti"][String(m9["cinnost"])] as Dictionary).has("obchuzka") and String(m9["kde"]).begins_with("hostinec")
		if not ma:
			ch.call("hostinec %s: v rozvrhu neni obsluha mezi stoly" % rid)
	# rozestup: tri postavy se stejnym cilem (nosi u studny) -> cile aspon misto_m od sebe
	var cil: Vector2 = lide.call("_misto", ll[0], "nadvori_studna")[0]
	var tri: Array = []
	for i in 3:
		var q: Vector2 = lide.call("_rozestup", ll[i], cil)
		ll[i]["misto"] = q
		tri.append(q)
	for i in 3:
		for j in range(i + 1, 3):
			if (tri[i] as Vector2).distance_to(tri[j]) < float(P["rozestup"]["misto_m"]) * 0.99:
				ch.call("rozestup: cile %d a %d jen %.2f m od sebe" % [i, j, (tri[i] as Vector2).distance_to(tri[j])])
	for i in ll.size():
		ll[i]["misto"] = puv[i]
	print("LIDE mista: %d s volnou bunkou, rozestup tri cilu %s" % [n_ok, str(tri)])


## Cas skriptu predmety v sini tvrze (Misa 6. 11. panel: predmety 15-26 ms v sini a komnatach se svicny): hrac v sini,
## otaci se dokola (okna v zaberu / mimo = rezim vnitrku), nejdelsi snimek _process_vlastni pod predmety_ms z dat.
func _predmety_cas() -> void:
	var pr: Node = main.get("predmety")
	if pr == null:
		pr = get_tree().root.find_child("Predmety", true, false)
	await main.fast_travel(Vector3(6.0, 0.0, -12.0), Vector3(12.0, 1.6, -12.0), 0.0, "test")
	for _i in 120:
		await get_tree().physics_frame
	var mez := float(Pravidla.cti("rozpocty", "predmety_vnitrek", "test_snimek_ms"))
	var max_us := 0
	var sum_us := 0
	var kde := ""
	for f in 240:
		player.yaw += deg_to_rad(4.5)
		if f % 60 == 30:
			player.global_position += Vector3(0.0, 0.0, 2.5 if f < 120 else -2.5)
		await get_tree().process_frame
		var t0 := Time.get_ticks_usec()
		pr.call("_interier", 1.0 / 30.0)
		var t1 := Time.get_ticks_usec()
		pr.call("_vnitrek_krok")
		var us := Time.get_ticks_usec() - t0
		if us > max_us:
			max_us = us
			kde = "snimek %d: _interier %.2f ms, _vnitrek_krok %.2f ms, rezim %d" % [f, (t1 - t0) / 1000.0, (Time.get_ticks_usec() - t1) / 1000.0, int(pr.get("_vn_rez"))]
		sum_us += us
	var txt := "mistnost '%s', nejdelsi %.2f ms (%s), prumer %.3f ms" % [main.life.room_name, max_us / 1000.0, kde, sum_us / 240000.0]
	print("PREDMETY CAS ", txt)
	_vysledek("predmety_cas", max_us / 1000.0 < mez, txt)


## Zasek pri zmene rozvrhu (Misa 6. 11., panel tabletu: skript lide 692 / 868 / 957 ms v jednom snimku): vsechny postavy
## zmeni blok v jednom snimku (6:01, 18:01) u hrace v miste s nejvic postavami, prazdna pamet mrizky. Varianta bez
## rozpoctu (= stav pred opravou) a s rozpoctem (postavy.json graf.mrizka sondy_snimek, cas_ms_snimek): nejdelsi snimek
## _process_vlastni s rozpoctem pod test_snimek_ms; cesty s rozpoctem stejne jako bez (odlozeni nemeni cestu, nikdy rovne).
func _lide_zasek() -> void:
	var lide: Node = main.get_node_or_null("World/Lide")
	if lide == null:
		lide = get_tree().root.find_child("Lide", true, false)
	if lide == null:
		_vysledek("lide_zasek", false, "uzel Lide nenalezen")
		return
	var P: Dictionary = lide.get("P")
	var mz: Dictionary = P["graf"]["mrizka"]
	var ll: Array = lide.get("_lide")
	var chyby: Array = []
	# rozmisteni v 5:59 (LOD: rovnou na miste), stred = postava s nejvic sousedy do 60 m
	main.day.hour = 5.99
	for c: Dictionary in ll:
		c["blok"] = -1
		(c["uzel"] as Node3D).position = Vector3.ZERO
	lide.call("_process_vlastni", 0.0)
	var nej := Vector3.ZERO
	var nej_n := -1
	for c: Dictionary in ll:
		var q: Vector3 = (c["uzel"] as Node3D).position
		var n := 0
		for c2: Dictionary in ll:
			if Vector2(q.x, q.z).distance_to(Vector2((c2["uzel"] as Node3D).position.x, (c2["uzel"] as Node3D).position.z)) < 60.0:
				n += 1
		if n > nej_n:
			nej_n = n
			nej = q
	await main.fast_travel(nej + Vector3(3.0, 0.0, 3.0), nej + Vector3(3.0, 1.6, -7.0), 0.0, "test")
	for _i in 120:
		await get_tree().physics_frame
	var vysl: Array = []
	var meze := [int(mz["sondy_snimek"]), float(mz["cas_ms_snimek"])]
	for hh: Array in [[5.99, 6.01], [17.99, 18.01]]:
		# vychozi poloha pred zmenou (LOD na miste bloku h0, vyska usazena)
		main.day.hour = hh[0]
		for c: Dictionary in ll:
			c["blok"] = -1
			c.erase("ceka")
			(c["uzel"] as Node3D).position = Vector3.ZERO
		for _i in 20:
			lide.call("_process_vlastni", 1.0 / 30.0)
		var poz: Array = ll.map(func(c: Dictionary) -> Vector3: return (c["uzel"] as Node3D).position)
		var cesty := {}
		for var_i in 2:
			var bez := var_i == 0
			mz["sondy_snimek"] = 1 << 30 if bez else meze[0]
			mz["cas_ms_snimek"] = 1.0e6 if bez else meze[1]
			(lide.get("_nav_kes") as Dictionary).clear()
			(lide.get("_nav_hotove") as Dictionary).clear()
			(lide.get("_nav_rozpr") as Dictionary).clear()
			(lide.get("_nav_nelze") as Dictionary).clear()
			(lide.get("_nav_fronta") as Array).clear()
			lide.set("_nav_sond", -1)
			lide.set("_nav_sond_n", 0)
			(lide.get("_rng") as RandomNumberGenerator).seed = 1393
			for i in ll.size():
				var c: Dictionary = ll[i]
				(c["uzel"] as Node3D).position = poz[i]
				c["blok"] = -1
				c.erase("ceka")
				c["cesta"] = PackedVector2Array()
				c["v"] = 0.0
				c["ve_fronte"] = false
			var obs: Dictionary = lide.get("_obsazeno")
			for k: String in obs.keys():
				if not k.begins_with("postel:"):
					obs.erase(k)
			main.day.hour = hh[1]
			var max_us := 0
			var snimku := 0
			var hotovo_s := -1
			var hotove := {}
			for f in 900:
				var t0 := Time.get_ticks_usec()
				lide.call("_process_vlastni", 1.0 / 30.0)
				max_us = maxi(max_us, Time.get_ticks_usec() - t0)
				snimku += 1
				var ceka := 0
				for c: Dictionary in ll:
					if c.has("ceka"):
						ceka += 1
					elif not hotove.has(c["id"]) and not (c["cesta"] as PackedVector2Array).is_empty():
						hotove[c["id"]] = [c["misto"], (c["cesta"] as PackedVector2Array).duplicate(), f + 1, Vector2((c["uzel"] as Node3D).position.x, (c["uzel"] as Node3D).position.z)]
				# 14. 11.: rozpocet zmen cinnosti (graf.zmena_bloku_snimek) odklada cast postav - hotovo az kdyz vsechny
				# zmenily blok a zadna neceka na cestu
				var vsechny := ll.all(func(c9: Dictionary) -> bool: return int(c9["blok"]) == int(lide.call("_blok", c9, hh[1])))
				if ceka == 0 and vsechny and hotovo_s < 0:
					hotovo_s = f + 1
					break
			vysl.append("%.2f->%.2f %s: nejdelsi snimek %.1f ms, cest %d, sond %d, dopocitano za %d snimku" % [hh[0], hh[1], "bez rozpoctu" if bez else "s rozpoctem", max_us / 1000.0, hotove.size(), int(lide.get("_nav_sond_n")), hotovo_s])
			print("LIDE ZASEK ", vysl[-1])
			var po_snimcich: Array = hotove.keys().map(func(id: String) -> String: return "%s %d" % [id, int(hotove[id][2])])
			print("LIDE ZASEK dopocitano (postava snimek): ", po_snimcich)
			if bez:
				cesty = hotove
				# rozbor: kolik sond a ms stoji cesta kazde postavy samostatne (prazdna pamet mrizky)
				for id: String in hotove:
					(lide.get("_nav_kes") as Dictionary).clear()
					(lide.get("_nav_nelze") as Dictionary).clear()
					lide.set("_nav_sond_n", 0)
					var sel0: int = lide.get("_nav_selhani")
					var t1 := Time.get_ticks_usec()
					var cs1: PackedVector2Array = lide.call("cesta", hotove[id][3], hotove[id][0])
					print("LIDE ZASEK rozbor %s: %s -> %s, %d sond, %.0f ms, %d bodu, selhani %d" % [id, (hotove[id][3] as Vector2).round(), (hotove[id][0] as Vector2).round(), int(lide.get("_nav_sond_n")), (Time.get_ticks_usec() - t1) / 1000.0, cs1.size(), int(lide.get("_nav_selhani")) - sel0])
			else:
				if max_us / 1000.0 > float(mz["test_snimek_ms"]):
					chyby.append("%.2f: snimek %.1f ms > %.1f" % [hh[1], max_us / 1000.0, float(mz["test_snimek_ms"])])
				if hotovo_s < 0:
					chyby.append("%.2f: cesty nedopocitany za 900 snimku" % hh[1])
				var stejne := 0
				for id: String in hotove:
					if not cesty.has(id) or (cesty[id][0] as Vector2) != (hotove[id][0] as Vector2):
						continue                     # jine misto (nahodna skupina hovoru) - nesrovnatelne
					if cesty[id][1] != hotove[id][1]:
						# jina cesta (svet se mezitim zmenil - otevrene dvere): smi byt jina, ne pres zed (paprsky jako 7c)
						var spc := player.get_world_3d().direct_space_state
						var pq: Vector2 = hotove[id][3]
						var narazi := ""
						for qq: Vector2 in (hotove[id][1] as PackedVector2Array):
							for hv: float in [0.35, 1.0, 1.6]:
								var r0 := Vector3(pq.x, float(lide.call("podlaha", pq)) + hv, pq.y)
								var r1 := Vector3(qq.x, float(lide.call("podlaha", qq)) + hv, qq.y)
								var hr := spc.intersect_ray(PhysicsRayQueryParameters3D.create(r0, r1, 0xFFFFFFFF, [player.get_rid()]))
								if not hr.is_empty() and not str((hr["collider"] as Node).get_path()).contains("Pohyb_"):
									narazi = "(%.1f,%.1f)->(%.1f,%.1f) v %.2f m do %s" % [pq.x, pq.y, qq.x, qq.y, hv, str((hr["collider"] as Node).get_path()).right(40)]
							pq = qq
						print("LIDE ZASEK %s: cesta s rozpoctem jina nez bez (%s / %s) %s" % [id, str(hotove[id][1]), str(cesty[id][1]), narazi])
						if narazi != "":
							chyby.append("%s: cesta s rozpoctem narazi %s" % [id, narazi])
					else:
						stejne += 1
				print("LIDE ZASEK stejnych cest %d z %d" % [stejne, hotove.size()])
				if hotove.size() < 3:
					chyby.append("%.2f: jen %d cest - test nic neoveril" % [hh[1], hotove.size()])
	mz["sondy_snimek"] = meze[0]
	mz["cas_ms_snimek"] = meze[1]
	lide.set("_nav_sond", -1)
	_vysledek("lide_zasek", chyby.is_empty(), "%d chyb %s; %s" % [chyby.size(), str(chyby.slice(0, 5)), str(vysl)])


## Bod 9 testu lide_chovani (Misa 10. 11.: delsi denni pribeh, obsluha hostince, hoste, dvere): role z postavy.json
## pribeh maji v rozvrhu aspon min_cinnosti ruznych cinnosti; pracujici v poledne (poledne_h) blok bez sve prace;
## obsluha s hostem v sini nema zadnou platnou moznost mimo obsluha_cinnosti (zadna prestavka, dokud sedi host), bez hostu
## prestavku mit muze; obchuzka obsluhy stridave krb (kuchyne) a stoly, ke stolum nese predmet z katalogu s drzenim;
## hoste vsedě stridaji aspon 3 klipy (vykladani, piti, jidlo); zavrene dvere hostince se pred postavou otevrou a za
## ni zavrou (pohyb.gd skupina).
func _pribeh_kontrola(lide: Node, ll: Array, P: Dictionary, ch: Callable) -> void:
	var pb: Dictionary = Pravidla.cti("postavy", "pribeh")
	for rid: String in pb["role"]:
		var cin := {}
		for bl: Dictionary in P["role"][rid]["rozvrh"]:
			cin[String(bl["cinnost"])] = true
			for m: Dictionary in bl.get("moznosti", []):
				cin[String(m["cinnost"])] = true
		print("LIDE pribeh %s: %d cinnosti %s" % [rid, cin.size(), str(cin.keys())])
		if cin.size() < int(pb["min_cinnosti"]):
			ch.call("pribeh %s: jen %d cinnosti za den" % [rid, cin.size()])
	for rid: String in pb["prace"]:
		var prace := String(pb["prace"][rid])
		var rz: Array = P["role"][rid]["rozvrh"]
		var pauza := false
		var h := float(pb["poledne_h"][0])
		while h < float(pb["poledne_h"][1]) and not pauza:
			var bi := rz.size() - 1
			for i in rz.size():
				if h >= float(rz[i]["od"]):
					bi = i
			var bl: Dictionary = rz[bi]
			var vse: Array = [String(bl["cinnost"])]
			for m: Dictionary in bl.get("moznosti", []):
				vse.append(String(m["cinnost"]))
			pauza = not vse.has(prace) and vse.all(func(x: String) -> bool: return (pb["prestavky"] as Array).has(x))
			h += 0.25
		print("LIDE pribeh %s: poledni prestavka %s" % [rid, "ano" if pauza else "NE"])
		if not pauza:
			ch.call("pribeh %s: v poledne bez prestavky" % rid)
	# obsluha a hoste: host v sini (podminka), pak bez hostu
	var host: Dictionary = {}
	for c: Dictionary in ll:
		if String(c["o"]["role"]).begins_with("pocestny"):
			host = c
	var zal := [host.get("cinnost_ted", ""), host.get("kde_ted", ""), host.get("na_miste", false)]
	var zal_ost := {}
	for c: Dictionary in ll:
		zal_ost[c["id"]] = c.get("cinnost_ted", "")
	for c: Dictionary in ll:
		var ro := String(c["o"]["role"])
		if not (pb["obsluha_role"] as Dictionary).has(ro):
			continue
		var pdn := String(pb["obsluha_role"][ro])
		var pd: Dictionary = P["podminky"][pdn]
		for s_host: bool in [true, false]:
			for c2: Dictionary in ll:
				if c2 != c:
					c2["cinnost_ted"] = "spi"
			host["cinnost_ted"] = String(pd["cinnosti"][0]) if s_host else "spi"
			host["kde_ted"] = String(pd["kde"][0])
			host["na_miste"] = true
			var plati := bool(lide.call("podminka", c, pdn))
			if plati != s_host:
				ch.call("obsluha %s: podminka %s = %s, host %s" % [c["id"], pdn, plati, s_host])
			var mimo: Array = []
			for bl: Dictionary in c["role"]["rozvrh"]:
				for m: Dictionary in bl.get("moznosti", []):
					if bool(lide.call("podminka_moznosti", c, m)) and not (pb["obsluha_cinnosti"] as Array).has(String(m["cinnost"])):
						mimo.append("%s@%s" % [m["cinnost"], bl["od"]])
			print("LIDE obsluha %s %s: moznosti mimo obsluhu %s" % [c["id"], "s hostem" if s_host else "bez hostu", str(mimo)])
			if s_host and not mimo.is_empty():
				ch.call("obsluha %s ma s hostem prestavku %s" % [c["id"], str(mimo)])
			if not s_host and mimo.is_empty():
				ch.call("obsluha %s nema bez hostu zadnou prestavku" % c["id"])
	for c: Dictionary in ll:
		c["cinnost_ted"] = zal_ost[c["id"]]
	host["cinnost_ted"] = zal[0]
	host["kde_ted"] = zal[1]
	host["na_miste"] = zal[2]
	# volny cas na sedacich mimo hostince (Misa 10. 11.: lavice po svete, lide jen chodi kolem)
	var sedi_v := 0
	for c: Dictionary in ll:
		for bl: Dictionary in c["role"]["rozvrh"]:
			var vs: Array = [bl] + (bl.get("moznosti", []) as Array)
			for m: Dictionary in vs:
				if String(m["cinnost"]) != "volno":
					continue
				lide.call("_uvolni", c)
				lide.call("_misto_cinnosti", c, String(m["kde"]), P["cinnosti"]["volno"])
				var sk: Dictionary = c["sedak"]
				print("LIDE volno %s %s: %s" % [c["id"], m["kde"], "sedi %s" % str((sk.get("sedak", Vector2.ZERO) as Vector2).round()) if not sk.is_empty() else "stoji (bez sedaku)"])
				if sk.is_empty():
					# diagnostika: nejblizsi sedak z katalogu a proc nevyhovel (mistnost, vyska, obsazeno)
					var mq: Vector2 = c["misto"] if c.has("misto") else (lide.call("_misto", c, String(m["kde"])) as Array)[0]
					var nej_d := INF
					var nej_t := ""
					for r: Dictionary in sv.data.get("vybaveni", []):
						if bool((lide.call("katalog") as Dictionary).get(String(r["id"]), {}).get("sed", false)):
							var q3 := Vector3(float(r["p"][0]), float(r["p"][1]), float(r["p"][2]))
							var dd := Vector2(q3.x, q3.z).distance_to(mq)
							if dd < nej_d:
								nej_d = dd
								nej_t = "%s %s mistnost '%s'" % [r["id"], Vector2(q3.x, q3.z).round(), lide.call("_mistnost_u", q3)]
					print("LIDE volno %s: misto %s, nejblizsi sedak %.1f m: %s" % [c["id"], mq.round(), nej_d, nej_t])
				if not sk.is_empty():
					sedi_v += 1
				break
		lide.call("_uvolni", c)
	if sedi_v < int(pb["volno_min_sedi"]):
		ch.call("volno: mimo hostince sedi jen %d" % sedi_v)
	# kostky po tazich (Misa 10. 11.): dva sedici hoste v sini - kdo je na tahu, trese/hodi/odkryje, druhy ceka; pak druhy
	var K: Dictionary = P["kostky"]
	var hraci: Array = []
	for c: Dictionary in ll:
		if hraci.size() < 2 and String(c["o"]["role"]) in ["pocestny", "lamac"]:
			hraci.append(c)
	var zal_k: Array = []
	for c: Dictionary in hraci:
		zal_k.append([c.get("kde_ted", ""), c.get("cinnost_ted", ""), c.get("sedi", false), c.get("na_miste", false)])
		c["kde_ted"] = String(K["kde"][0])
		c["cinnost_ted"] = String(K["cinnost"])
		c["sedi"] = true
		c["na_miste"] = true
	var sance_k := float(K["sance_s"])
	var hraci_k: Array = K["hraci"]
	K["sance_s"] = 1e6
	K["hraci"] = [2, 2]
	var h_k := float(K["hodiny"][0]) + 0.5
	(lide.get("_hry") as Dictionary).clear()
	var zal_ost_k := {}
	for c: Dictionary in ll:
		if not hraci.has(c) and String(c.get("kde_ted", "")) == String(K["kde"][0]):
			zal_ost_k[c["id"]] = c.get("cinnost_ted", "")
			c["cinnost_ted"] = "spi"                 # ostatni hoste mimo hru testu
	lide.call("kostky_krok", 0.1, h_k)
	K["sance_s"] = sance_k
	K["hraci"] = hraci_k
	var tahy: Array = []
	for _i in 12:
		lide.call("kostky_krok", 30.0, h_k)
		var radek: Array = []
		for c: Dictionary in hraci:
			radek.append(String(c["klip"]))
		tahy.append(radek)
		var na := -1
		var n_tah := 0
		for j in hraci.size():
			if (K["tah"] as Array).has(String(hraci[j]["klip"])):
				n_tah += 1
				na = j
		if n_tah > 1:
			ch.call("kostky: na tahu vic hracu naraz %s" % str(radek))
		if n_tah == 1 and String(hraci[1 - na]["klip"]) != String(K["ceka"]):
			ch.call("kostky: kdo neni na tahu, neceka %s" % str(radek))
	print("LIDE kostky: %s" % str(tahy))
	var hraje: Dictionary = {}
	for r9: Array in tahy:
		for j in r9.size():
			if (K["tah"] as Array).has(String(r9[j])):
				hraje[j] = true
	if hraje.size() < 2:
		ch.call("kostky: tahy se nestridaji (hrali %s)" % str(hraje.keys()))
	for i in hraci.size():
		hraci[i]["sedi"] = false
	lide.call("kostky_krok", 0.1, h_k)
	for c: Dictionary in ll:
		if zal_ost_k.has(c["id"]):
			c["cinnost_ted"] = zal_ost_k[c["id"]]
	for i in hraci.size():
		var c: Dictionary = hraci[i]
		c["kde_ted"] = zal_k[i][0]
		c["cinnost_ted"] = zal_k[i][1]
		c["sedi"] = zal_k[i][2]
		c["na_miste"] = zal_k[i][3]
	# Misa 11. 11. (rešerše: vyznam klipu) - klip cinnosti ma vyznam (klipy_vyznam) a je ve vyskach cinnosti (stoji
	# vzdy smi); opreni jen na miste u_steny; sed jen v cinnosti se sedem (sed nebo klipy vsedě v kostkach)
	var vyz: Dictionary = Pravidla.cti("postavy", "klipy_vyznam")
	for ck: String in P["cinnosti"]:
		var cnx: Variant = P["cinnosti"][ck]
		if not (cnx is Dictionary):
			continue
		var povol: Array = (cnx as Dictionary).get("vysky", []) + ["stoji"]
		var vsech: Array = []
		for lst: Variant in [cnx.get("klipy", []), cnx.get("klipy_bez_sedu", [])] + (cnx.get("sceny", []) as Array):
			vsech.append_array(lst)
		for mk: String in (cnx.get("obchuzka_klipy", {}) as Dictionary):
			for kl: String in cnx["obchuzka_klipy"][mk]:
				if String(vyz.get(kl, "")) == "opreni" and not (P["mista"].get(mk, {}) as Dictionary).has("u_steny"):
					ch.call("vyznam: %s opreni na %s bez steny" % [ck, mk])
			vsech.append_array(cnx["obchuzka_klipy"][mk])
		for kl: String in vsech:
			var v := String(vyz.get(kl, ""))
			if v == "":
				ch.call("vyznam: klip %s (cinnost %s) nema vyznam v klipy_vyznam" % [kl, ck])
			elif v == "sed":
				if not bool(cnx.get("sed", false)) and not povol.has("sed"):
					ch.call("vyznam: %s sed klip %s v cinnosti bez sedu" % [ck, kl])
			elif not povol.has(v):
				ch.call("vyznam: %s klip %s (%s) nepatri k cinnosti (vysky %s)" % [ck, kl, v, str(povol)])
	# Misa 11. 11. spolecne sceny: ucastnici maji v cas sceny blok se stejnou cinnosti na stejnem miste
	for sc: Dictionary in Pravidla.cti("postavy", "spolecne_sceny"):
		var cinn := {}
		for c: Dictionary in ll:
			if (sc["kdo"] as Array).has(String(c["o"]["role"])) or (sc["kdo"] as Array).has(String(c["id"])):
				var bl: Dictionary = c["role"]["rozvrh"][int(lide.call("_blok", c, float(sc["od"]) + 0.05 + float(c.get("posun_h", 0.0))))]
				cinn[c["id"]] = "%s@%s" % [bl["cinnost"], bl["kde"]]
				if String(bl["kde"]) != String(sc["kde"]):
					ch.call("scena %s v %.1f: %s je %s" % [sc["kde"], float(sc["od"]), c["id"], cinn[c["id"]]])
		if cinn.size() < 2:
			ch.call("scena %s v %.1f: ucastniku %d (%s)" % [sc["kde"], float(sc["od"]), cinn.size(), str(sc["kdo"])])
	# Misa 13. 11. (bylinkarka trha jablka ze stromu, ale stoji nad zahonem): kazdy blok s trhanim (vsechny klipy 'nad')
	# ma misto u kmene ovocneho stromu (lide.u_stromu); (kucharky pily a pleli v kuchyni): v kuchyni zadne Napiti/Hleda_Loop
	var vyz_o: Dictionary = Pravidla.cti("postavy", "klipy_vyznam")
	var ust: Dictionary = Pravidla.cti("postavy", "u_stromu")
	for c: Dictionary in ll:
		for bl: Dictionary in c["role"]["rozvrh"]:
			var cn2: Dictionary = P["cinnosti"][bl["cinnost"]]
			var kl2: Array = cn2.get("klipy", [])
			if kl2.is_empty() or not kl2.all(func(k: String) -> bool: return String(vyz_o.get(k, "")) == "nad"):
				continue
			lide.call("_uvolni", c)
			var mt: Array = lide.call("_misto_cinnosti", c, String(bl["kde"]), cn2)
			var ut: Array = lide.call("u_stromu", mt[0])
			if ut.is_empty() or (ut[0] as Vector2).distance_to(mt[0]) > float(ust["od_kmene_m"]) * 0.5:
				ch.call("%s %s@%s: trha ovoce mimo strom %s" % [c["id"], bl["cinnost"], bl["kde"], (mt[0] as Vector2).round()])
	# Misa 14. 11. (senkyrka i hospodsky jen mezi 1. stolem a krbem, porad truhla): obchuzka obsluhy hostince
	var ohp: Dictionary = Pravidla.cti("postavy", "obsluha_hostinec_pravidla")
	for kc: String in ohp["cinnosti"]:
		var cc: Dictionary = P["cinnosti"][kc]
		var obz: Array = cc.get("obchuzka", [])
		var ruzne := {}
		for kk: String in obz:
			ruzne[kk] = true
		if ruzne.size() < int(ohp["min_mist"]):
			ch.call("%s: obchuzka jen %d mist (min %d)" % [kc, ruzne.size(), int(ohp["min_mist"])])
		if not (ohp["kuchyne"] as Array).any(func(k: String) -> bool: return ruzne.has(k)):
			ch.call("%s: obchuzka bez kuchyne" % kc)
		var vse_k := 0
		var truhla := 0
		for kk: String in obz:
			for kl: String in (cc.get("obchuzka_klipy", {}) as Dictionary).get(kk, []):
				vse_k += 1
				truhla += 1 if kl == "Truhla_Otevri" else 0
		if vse_k > 0 and float(truhla) / vse_k > float(ohp["truhla_podil_max"]):
			ch.call("%s: truhla %d z %d klipu obchuzky" % [kc, truhla, vse_k])
		for kk: String in ruzne:
			var mz: Array = lide.call("_misto", ll[0], kk)
			if (mz[0] as Vector2) == Vector2.ZERO or float(mz[1]) == INF and not (P["mista"].get(kk, {}) as Dictionary).has("p"):
				ch.call("%s: misto %s nenalezeno" % [kc, kk])
	# Misa 14. 11. (hospodsky se opira o vzduch, tram je dal za nim): kazde misto u_steny - za zady do od_m + rezerva
	# pevna plocha (ne dvere Pohyb_*), paprsek ve vysce u_steny.vyska_m
	var us9: Dictionary = Pravidla.cti("postavy", "u_steny")
	var sp9 := get_tree().root.get_world_3d().direct_space_state
	for k9: String in (P["mista"] as Dictionary):
		if not (P["mista"][k9] as Dictionary).has("u_steny"):
			continue
		var m9: Array = lide.call("_misto", ll[0], k9)
		if float(m9[1]) == INF:
			ch.call("%s: stena k opreni nenalezena" % k9)
			continue
		var q9: Vector2 = m9[0]
		var y9: float = float(lide.call("podlaha", q9)) + float(us9["vyska_m"])
		var za9 := -Vector2(sin(float(m9[1])), cos(float(m9[1])))
		var o9 := Vector3(q9.x, y9, q9.y)
		var r9 := sp9.intersect_ray(PhysicsRayQueryParameters3D.create(o9, o9 + Vector3(za9.x, 0.0, za9.y) * (float(us9["od_m"]) + 0.15), 1))
		if r9.is_empty():
			ch.call("%s: oprena postava (%.1f, %.1f) - za zady do %.2f m nic (opira se o vzduch)" % [k9, q9.x, q9.y, float(us9["od_m"]) + 0.15])
		elif lide.call("_je_pohyblive", r9.get("collider")):
			ch.call("%s: oprena o dvere (%.1f, %.1f)" % [k9, q9.x, q9.y])
	# Misa 13. 11. (hostinsky s hostinskou pleji travu u krbu): predklon k zemi jen u prace na zemi (k_zemi_cinnosti)
	var kz: Array = Pravidla.cti("postavy", "klipy_k_zemi")
	var kz_ok: Array = Pravidla.cti("postavy", "k_zemi_cinnosti")
	for k5: String in (P["cinnosti"] as Dictionary):
		if kz_ok.has(k5):
			continue
		var c5: Dictionary = P["cinnosti"][k5]
		var vse5: Array = (c5.get("klipy", []) as Array) + ((c5.get("sceny", []) as Array).reduce(func(a: Array, x: Array) -> Array: return a + x, []) as Array)
		for l5: Array in (c5.get("obchuzka_klipy", {}) as Dictionary).values():
			vse5 += l5
		for kl5: String in vse5:
			if kz.has(kl5):
				ch.call("%s: klip %s (predklon k zemi = vypada jako pleti) mimo k_zemi_cinnosti" % [k5, kl5])
				break
	var bez_pr: Array = Pravidla.cti("postavy", "klipy_bez_predmetu")
	for k4: String in (P["cinnosti"] as Dictionary):
		var c4: Dictionary = P["cinnosti"][k4]
		if (c4.get("v_rukou", {}) as Dictionary).has("*"):
			for kl4: String in (c4.get("klipy", []) as Array) + ((c4.get("sceny", []) as Array).reduce(func(a: Array, x: Array) -> Array: return a + x, []) as Array):
				if bez_pr.has(kl4):
					ch.call("%s: klip %s se zkrizenyma rukama a predmetem v ruce (projde telem)" % [k4, kl4])
	for k3: String in (P["cinnosti"] as Dictionary):
		if k3 == "vareni" and (str(P["cinnosti"][k3].get("klipy", [])) + str(P["cinnosti"][k3].get("sceny", []))).contains("Napiti"):
			ch.call("vareni: piti v kuchyni")
	# Misa 11. 11. (tri poutnici sli spolu): cile poutniku (c.misto) od sebe aspon poutnici_od_m
	var pt_m: Array = []
	for c: Dictionary in ll:
		if bool((c["o"] as Dictionary).get("poutnik", false)) and c.has("misto"):
			pt_m.append([c["id"], c["misto"]])
	for i in pt_m.size():
		for j in range(i + 1, pt_m.size()):
			if (pt_m[i][1] as Vector2).distance_to(pt_m[j][1]) < 20.0:
				ch.call("poutnici %s a %s spolu (%s, %s)" % [pt_m[i][0], pt_m[j][0], pt_m[i][1], pt_m[j][1]])
	# Misa 11. 11. (lavice od studny skoncila v pruchodu brany): venkovni nabytek ne v mistnosti stavby
	for r: Dictionary in sv.data.get("vybaveni", []):
		if bool(r.get("venku", false)):
			var mn := String(lide.call("_mistnost_u", Vector3(float(r["p"][0]), float(r["p"][1]), float(r["p"][2]))))
			if mn != "":
				ch.call("lavice venku %s v mistnosti %s" % [str(r["p"]), mn])
	# dvojice (Misa 10. 11.): jeden sedi na lavici, druhy stoji u nej celem k nemu (sance 1 pro test), nebo sedi vedle
	var cv: Dictionary = P["cinnosti"]["volno"]
	var a_c: Dictionary = ll[0]
	var b_c: Dictionary = ll[1]
	var zal_ab := [a_c.get("cinnost_ted", ""), b_c.get("cinnost_ted", "")]
	# ostatni postavy mimo (11. 11.: s novymi rozvrhy ma volno u studny i celedin/dvorka - druhy se postavil k nim)
	var zal_ost_d := {}
	for c: Dictionary in ll:
		if c != a_c and c != b_c:
			zal_ost_d[c["id"]] = c.get("cinnost_ted", "")
			c["cinnost_ted"] = "spi"
			lide.call("_uvolni", c)               # i rezervace sedaku (lavice u studny obsazena celedinem)
	a_c["cinnost_ted"] = "volno"
	b_c["cinnost_ted"] = "volno"
	lide.call("_uvolni", a_c)
	lide.call("_uvolni", b_c)
	var ma: Array = lide.call("_misto_cinnosti", a_c, "nadvori_studna", cv)
	var sance0 := float(cv["dvojice_stoji"])
	cv["dvojice_stoji"] = 1.0
	var mb: Array = lide.call("_misto_cinnosti", b_c, "nadvori_studna", cv)
	cv["dvojice_stoji"] = sance0
	if (a_c["sedak"] as Dictionary).is_empty():
		ch.call("dvojice: prvni u studny nesedi (zadna lavice)")
	elif String(b_c.get("stoji_u", "")) != String(a_c["id"]):
		for ri in (sv.data.get("vybaveni", []) as Array).size():
			var r: Dictionary = sv.data["vybaveni"][ri]
			var rp := Vector2(float(r["p"][0]), float(r["p"][2]))
			if String(r["id"]).begins_with("lavice") and rp.distance_to(Vector2(-2, 6)) < 14.0:
				var obs := []
				for k: String in (lide.get("_obsazeno") as Dictionary):
					if k.begins_with("sed:%d:" % ri):
						obs.append("%s=%s" % [k, lide.get("_obsazeno")[k]])
				print("LIDE lavice u studny %s %s mistnost '%s' obsazeno %s" % [r["id"], rp, lide.call("_mistnost_u", Vector3(rp.x, float(r["p"][1]), rp.y)), obs])
		ch.call("dvojice: druhy nestoji u sediciho (stoji_u %s, sedak %s, misto %s)" % [b_c.get("stoji_u", ""), str((a_c["sedak"] as Dictionary).get("stani", "")), str(ma[0])])
	else:
		var kb := (ma[0] as Vector2) - (mb[0] as Vector2)
		var fwb := Vector2(sin(float(mb[1])), cos(float(mb[1])))
		print("LIDE dvojice: %s sedi %s, %s stoji %.2f m od nej, odchylka pohledu %.0f st" % [a_c["id"], (ma[0] as Vector2).round(), b_c["id"], kb.length(), absf(rad_to_deg(fwb.angle_to(kb)))])
		if kb.length() > 1.5 or absf(rad_to_deg(fwb.angle_to(kb))) > 20.0:
			ch.call("dvojice: stojici neni u sediciho celem k nemu")
	lide.call("_uvolni", a_c)
	lide.call("_uvolni", b_c)
	a_c["cinnost_ted"] = zal_ab[0]
	b_c["cinnost_ted"] = zal_ab[1]
	for c: Dictionary in ll:
		if zal_ost_d.has(c["id"]):
			c["cinnost_ted"] = zal_ost_d[c["id"]]
	# obchuzka obsluhy: krb <-> stoly s predmetem
	var cn: Dictionary = P["cinnosti"]["obsluha_hostinec"]
	var hs: Dictionary = {}
	for c: Dictionary in ll:
		if String(c["o"]["role"]) == "hostinsky":
			hs = c
	if not hs.is_empty():
		var cn0: Dictionary = hs["cn"]
		var ob0 := int(hs["obch"])
		hs["cn"] = cn
		hs["obch"] = 0
		var u: Node3D = hs["uzel"]
		var krb := 0
		var stul_s := 0
		var seq: Array = []
		for i in (cn["obchuzka"] as Array).size():
			lide.call("_obchuzka_dalsi", hs, cn, Vector2(u.position.x, u.position.z))
			var kde := String(cn["obchuzka"][int(hs["obch"])])
			var nese: Dictionary = hs.get("nese", {})
			seq.append(kde + ("+" + str(nese.values()) if not nese.is_empty() else ""))
			if kde.contains("krb"):
				krb += 1
			if kde.contains("stul") and not nese.is_empty():
				stul_s += 1
				for rk: String in nese:
					if not (P["drzeni"] as Dictionary).has(String(nese[rk])) or not ResourceLoader.exists("res://modely/predmety/%s.glb" % nese[rk]):
						ch.call("obsluha nese %s bez drzeni/modelu" % nese[rk])
			var m: Vector2 = hs["misto"]
			var mi := String(lide.call("_mistnost_u", Vector3(m.x, u.position.y + 0.5, m.y)))
			if (P["mista"][kde] as Dictionary).has("dvere") and mi == "":
				print("LIDE obsluha misto %s %s mimo mistnost (NEOVERENO podlaha)" % [kde, m.round()])
		print("LIDE obsluha obchuzka: %s" % " -> ".join(seq))
		if krb < 1 or stul_s < 1:
			ch.call("obsluha nechodi krb <-> stul s predmetem (krb %d, stul s predmetem %d)" % [krb, stul_s])
		hs["cn"] = cn0
		hs["obch"] = ob0
		hs["nese"] = {}
		hs.erase("ceka")
		hs["blok"] = -1
	# hoste: vsedě aspon 3 ruzne klipy, vsechny v knihovne
	var hk: Array = P["cinnosti"]["hospoda"]["klipy"]
	var ap: AnimationPlayer = ll[0]["ap"]
	for k: String in hk:
		if not ap.has_animation(k):
			ch.call("hospoda: klip %s chybi" % k)
	if hk.size() < 3:
		ch.call("hospoda: hoste jen %d klipy" % hk.size())
	# dvere: postava zvenku do sine - dvere hostince se otevrou, za ni zavrou
	var ph: Node = main.get("pohyb")
	if ph != null and not host.is_empty():
		var pr: Dictionary = lide.call("_pruchod", "hostinec_sin")
		var sk := String(pr.get("skupina", ""))
		var g: Dictionary = (ph.get("groups") as Dictionary).get(sk, {})
		if g.is_empty():
			ch.call("dvere hostince: skupina %s v pohyb.gd neni" % sk)
		else:
			if float(g["target"]) > 0.5:
				ph.call("toggle", sk)
			var uv0: Dictionary = host.get("uvnitr", {})
			var dv0: Dictionary = host.get("dvere", {})
			host["uvnitr"] = {}
			lide.call("_cesta_pruchod", host, pr["venku"] as Vector2 + Vector2(3, 0), Vector2(float(P["mista"]["hostinec_sin"]["p"][0]), float(P["mista"]["hostinec_sin"]["p"][1])), pr)
			lide.call("_dvere_otevri", host, false)
			var otevreno := float(g["target"]) > 0.5
			print("LIDE dvere hostince %s: postava prochazi - otevreno %s" % [sk, otevreno])
			if not otevreno:
				ch.call("dvere hostince se pred postavou neotevrou")
			if otevreno:
				ph.call("toggle", sk)
			host["uvnitr"] = uv0
			host["dvere"] = dv0


## Bod 8 testu lide_chovani: luzka a sedaky vnitrnich mist - podlaha, strop, kolize, dojiti dvermi.
func _nabytek_kontrola(lide: Node, ll: Array, kat: Dictionary, P: Dictionary, ch: Callable) -> String:
	var sp := player.get_world_3d().direct_space_state
	# luzko v mistnosti bez luzek (nabytek.json bez_luzek: hodovni sin - Misa 6. 11. „neni mozne dat postele do sine“)
	for e: String in sv.call("luzka_bez_luzek"):
		ch.call(e)
	var kusy: Array = []                  # [jmeno, p, yaw, rozmer nebo [], start dveri (Vector2 nebo INF), patro]
	for r: Dictionary in sv.data.get("postele", []):
		var start := Vector2.INF
		for c: Dictionary in ll:
			var sp7: Dictionary = (c["o"] as Dictionary).get("spanek", {})
			if String(sp7.get("budova", "")) != String(r["budova"]) or String(sp7.get("postel", "")) != String(r["id"]):
				continue
			var pz: Dictionary = lide.call("_postel", c)
			if pz.is_empty() or (pz["p"] as Vector3).distance_to(r["p"]) > 0.01:
				continue
			for bl: Dictionary in c["role"]["rozvrh"]:
				if String(bl["cinnost"]) == "spi":
					start = lide.call("_misto_cinnosti", c, String(bl["kde"]), P["cinnosti"]["spi"])[0]
		kusy.append(["luzko %s %s" % [r["id"], r["budova"]], r["p"], float(r["yaw"]), (kat.get(String(r["id"]), {}) as Dictionary).get("rozmer", []), start])
		if start == Vector2.INF:
			print("LIDE nabytek: luzko %s v %s %s nikdo nepouziva" % [r["id"], r["budova"], (r["p"] as Vector3).snapped(Vector3.ONE * 0.01)])
	for k: String in P["mista"]:
		var z: Dictionary = P["mista"][k]
		if not z.has("mistnost"):
			continue
		for r: Dictionary in sv.data.get("vybaveni", []):
			var p0 := Vector3(float(r["p"][0]), float(r["p"][1]), float(r["p"][2]))
			if (P["sedani"]["sedaky"] as Array).has(String(r["id"])) and String(lide.call("_mistnost_u", p0)) == String(z["mistnost"]):
				kusy.append(["sedak %s %s" % [r["id"], k], p0, float(r["yaw"]), (kat.get(String(r["id"]), {}) as Dictionary).get("rozmer", []), Vector2(float(z["venku"][0]), float(z["venku"][1]))])
	# vnitrni mista (mista.dvere): od bodu pred dvermi k mistu cinnosti (podlaha paprskem z vysky dveri)
	for k: String in P["mista"]:
		var z: Dictionary = P["mista"][k]
		if not z.has("dvere") or not z.has("p"):
			continue
		var uy := INF
		for e: Dictionary in sv.data.get("pohyb", []):
			if String(e["name"]) == String(z["dvere"]):
				uy = float(e.get("use", e["pos"])[1])
		if uy == INF:
			ch.call("misto %s: dvere %s ve svete nejsou" % [k, z["dvere"]])
			continue
		var hm := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(float(z["p"][0]), uy + 0.5, float(z["p"][1])), Vector3(float(z["p"][0]), uy - 3.0, float(z["p"][1]))))
		if hm.is_empty():
			ch.call("misto %s: pod mistem neni podlaha" % k)
			continue
		kusy.append(["misto %s" % k, hm["position"], 0.0, [], Vector2(float(z["venku"][0]), float(z["venku"][1]))])
	var vlastni := func(col: Object, p: Vector3) -> bool:
		var nd := col as Node
		while nd != null:
			if nd is Node3D and (nd as Node3D).global_position.distance_to(p) < 0.02:
				return true
			nd = nd.get_parent()
		return false
	var cizi := func(col: Object) -> bool:
		var jm := str((col as Node).get_path()) if col is Node else ""
		return not (jm.contains("Teren") or jm.contains("Pohyb_"))
	var ok := 0
	var patro := 0
	for kus: Array in kusy:
		var jm: String = kus[0]
		var p: Vector3 = kus[1]
		var yaw: float = kus[2]
		var rz: Array = kus[3]
		# podlaha: paprsek z 5 cm nad patou dolu (zacina uvnitr vlastni kolize - ta se nepocita)
		var q := PhysicsRayQueryParameters3D.create(p + Vector3(0, 0.05, 0), p - Vector3(0, 0.5, 0))
		var h := sp.intersect_ray(q)
		if h.is_empty() or absf(float((h["position"] as Vector3).y) - p.y) > 0.06:
			ch.call("%s %s: neni na podlaze (%s)" % [jm, p.snapped(Vector3.ONE * 0.01), "nic" if h.is_empty() else "%.2f" % float((h["position"] as Vector3).y)])
			continue
		# v budove: vodorovne paprsky 1 m nad patou do 8 smeru narazi do zdi / strechy do 12 m (pokoj hostince 9 m) (krovy kovarny a paláce
		# kolizi nemaji - strop paprskem nahoru nejde)
		var zdi := 0
		for a8 in 8:
			var sm := Vector3(sin(a8 * PI / 4.0), 0.0, cos(a8 * PI / 4.0))
			# smer je uzavreny, kdyz zed trefi aspon jeden ze 3 paprsku (pod parapetem, v okne, nad oknem - pokoj hostince
			# v patre ma okna a dvere na pavlac)
			for vy: float in [0.4, 1.0, 1.6]:
				var hz := sp.intersect_ray(PhysicsRayQueryParameters3D.create(p + Vector3(0, vy, 0), p + Vector3(0, vy, 0) + sm * 12.0))
				if not hz.is_empty() and cizi.call(hz["collider"]):
					zdi += 1
					break
		if zdi < 6:
			ch.call("%s %s: neni v budove (zed jen v %d z 8 smeru)" % [jm, p.snapped(Vector3.ONE * 0.01), zdi])
		# kolize: krabice pudorysu (zmensena o 3 cm) od 10 cm nad patou; sedak u stolu (lavice zasunuta pod desku) ne
		if rz.size() >= 3 and jm.begins_with("luzko"):
			var bx := BoxShape3D.new()
			var vys := clampf(float(rz[1]) - 0.12, 0.1, 0.6)
			bx.size = Vector3(float(rz[0]) - 0.06, vys, float(rz[2]) - 0.06)
			var sq := PhysicsShapeQueryParameters3D.new()
			sq.shape = bx
			sq.transform = Transform3D(Basis(Vector3.UP, yaw), p + Vector3(0, 0.1 + vys * 0.5, 0))
			for hh: Dictionary in sp.intersect_shape(sq, 16):
				if cizi.call(hh["collider"]) and not vlastni.call(hh["collider"], p):
					ch.call("%s %s: koliduje s %s" % [jm, p.snapped(Vector3.ONE * 0.01), str((hh["collider"] as Node).get_path()).get_slice("/", 4) + "/" + String((hh["collider"] as Node).name)])
		# dojiti dvermi: mrizka 0,25 m, volna bunka = krabice 0,3 x 1,4 m (0,3-1,7 m nad podlahou) bez kolize; cil = bunka
		# do 0,5 m od pudorysu predmetu
		var st: Vector2 = kus[4]
		if st == Vector2.INF:
			continue
		if p.y - float(sv.call("_vyska", p.x, p.z)) > 1.6:
			patro += 1
			print("LIDE nabytek %s v patre (y %.2f) - dojiti dvermi NEOVERENO (schody)" % [jm, p.y])
			continue
		var bc := BoxShape3D.new()
		bc.size = Vector3(0.3, 1.2, 0.3)          # 0,55-1,75 m nad zemi u dveri (prah, podlaha chyse 0,5 m, preklad 1,86 m)
		# vyska mrizky od zeme u dveri (slamnik na prycne je nad podlahou, prah a pata dveri podle vstupu)
		var hs := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(st.x, p.y + 1.2, st.y), Vector3(st.x, p.y - 3.0, st.y)))
		var y0 := float((hs["position"] as Vector3).y) if not hs.is_empty() else p.y
		var sq2 := PhysicsShapeQueryParameters3D.new()
		sq2.shape = bc
		var krok := 0.25
		var p2 := Vector2(p.x, p.z)
		var o := (st + p2) * 0.5 - Vector2.ONE * (st.distance_to(p2) * 0.5 + 4.0)
		var n := int((st.distance_to(p2) + 8.0) / krok)
		var volna := func(i: int, j: int) -> bool:
			var w := o + Vector2(i, j) * krok
			sq2.transform = Transform3D(Basis.IDENTITY, Vector3(w.x, y0 + 1.15, w.y))
			for hh: Dictionary in sp.intersect_shape(sq2, 8):
				if cizi.call(hh["collider"]):
					return false
			return true
		var inv := Transform3D(Basis(Vector3.UP, yaw), p).affine_inverse()
		var u_cile := func(i: int, j: int) -> bool:
			var w := o + Vector2(i, j) * krok
			var lq := inv * Vector3(w.x, p.y, w.y)
			var hx := (float(rz[0]) if rz.size() >= 3 else 1.0) * 0.5 + 0.5
			var hz := (float(rz[2]) if rz.size() >= 3 else 2.0) * 0.5 + 0.5
			return absf(lq.x) < hx and absf(lq.z) < hz
		var s0 := Vector2i(roundi((st.x - o.x) / krok), roundi((st.y - o.y) / krok))
		var fronta: Array = [s0]
		var videno := {s0: true}
		var dosel := false
		while not fronta.is_empty() and not dosel:
			var b: Vector2i = fronta.pop_front()
			for dd: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var nb := b + dd
				if nb.x < 0 or nb.y < 0 or nb.x > n or nb.y > n or videno.has(nb):
					continue
				videno[nb] = true
				if not volna.call(nb.x, nb.y):
					continue
				if u_cile.call(nb.x, nb.y):
					dosel = true
					break
				fronta.append(nb)
		if not dosel:
			ch.call("%s %s: postava k nemu od dveri %s nedojde (%d bunek)" % [jm, p.snapped(Vector3.ONE * 0.01), st.snapped(Vector2.ONE * 0.1), videno.size()])
		else:
			ok += 1
	print("LIDE nabytek: %d kusu, %d dojiti overeno, %d v patre" % [kusy.size(), ok, patro])
	return "%d kusu / %d dojiti / %d v patre" % [kusy.size(), ok, patro]



## Lednice jako plny blok (Misa 12. 11.: „koryto od mlyna do potoka ma jen jednu stranu jako ohnuty papir“): v kazdem
## 2. bodu osy lednice paprsek zvenku (bok osy sirka/2 + 1 m) vodorovne k ose 0,15 m pod rimsou musi narazit na kolizi
## steny (Lednice_blok) drive nez na vnitrni lic (sirka/2) - z obou stran. Bez vnejsiho lice paprsek projde.
func _lednice_blok() -> void:
	var P = preload("res://scripts/pravidla.gd")
	var d: Dictionary = P.cti("voda", "mlyn")["dil"]
	var f := FileAccess.open("res://tools/krok_b/mlyn_voda.json", FileAccess.READ)
	var u: Dictionary = (JSON.parse_string(f.get_as_text()) as Dictionary)["lednice"]
	var body: Array = u["body"]
	var pul := float(u["sirka"]) * 0.5
	var xf := Transform3D(Basis(Vector3.UP, float(d["natoceni"])), Vector3(float(d["stred"][0]), float(d["y_dvora"]), float(d["stred"][1])))
	var space := player.get_world_3d().direct_space_state
	var blok := get_tree().root.find_child("Lednice_blok", true, false)
	var chyby: Array = []
	var zkous := 0
	if blok == null:
		_vysledek("lednice_blok", false, "Lednice_blok v dilu mlyna chybi")
		return
	for i in range(2, body.size() - 2, 2):
		var a: Array = body[i - 1]
		var b: Array = body[i + 1]
		var sm := Vector3(float(b[0]) - float(a[0]), 0.0, float(b[2]) - float(a[2])).normalized()
		var bok := Vector3(-sm.z, 0.0, sm.x)
		var o := Vector3(float(body[i][0]), float(body[i][1]), float(body[i][2]))
		for s: float in [-1.0, 1.0]:
			zkous += 1
			var y := o.y + 0.5                                      # stena nad hladinou (rimsa modelu 0,8-1,0 m nad hladinou)
			var z0 := xf * Vector3(o.x + bok.x * s * (pul + 1.0), y, o.z + bok.z * s * (pul + 1.0))
			var z1 := xf * Vector3(o.x + bok.x * s * (pul - 0.02), y, o.z + bok.z * s * (pul - 0.02))
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(z0, z1))
			var nm := String((h["collider"] as Node).get_parent().name) if not h.is_empty() else "nic"
			# kolize trojuhelniku jen z licove strany (ConcavePolygonShape3D backface_collision false): zasah = zvenku je
			# lic (blok, roubeni modelu, teren); vnitrni lic zezadu paprsek neda - projde = papir
			if h.is_empty():
				chyby.append("bod %d strana %d: %s" % [i, int(s), nm])
	_vysledek("lednice_blok", chyby.is_empty(), "paprsku %d, bez vnejsiho lice %d %s" % [zkous, chyby.size(), str(chyby.slice(0, 8))])



## Napojeni toku na rybnik Lhota (Misa 12. 11., fotky (534, 888) a (495, 881): pritok u rybnika neni videt, odtok je
## tmavy pas v trave bez napojeni). Po ose pritoku od 30 m pred stredem az do hladiny rybnika a po ose odtoku od
## zacatku 30 m dal: kazdy 1 m musi byt nad osou viditelna voda (Toky_voda nebo Rybnik_Voda) nad zemi (kolize) -
## mezera bez vody > 1 m = chyba. Odtok musi zacinat u hraze (voda.json rybnik_lhota.hraz: do koruna/2 + svah od osy hraze).
func _ryb_napojeni() -> void:
	var tri := PackedVector3Array()
	for jm: String in ["Toky_voda", "Rybnik_Voda*", "Rybnik_lhota_voda*"]:
		for mi0 in main.find_children(jm, "MeshInstance3D", true, false):
			var mi := mi0 as MeshInstance3D
			if mi.mesh == null or not mi.is_visible_in_tree():
				continue
			var f := mi.mesh.get_faces()
			var xf := mi.global_transform
			for i in range(0, f.size(), 3):
				var c := xf * f[i]
				if Vector2(c.x, c.z).distance_to(sv.RYB_C) < 70.0:
					tri.append(c)
					tri.append(xf * f[i + 1])
					tri.append(xf * f[i + 2])
	var g: Dictionary = sv._tri_mrizka(tri, Transform3D())
	# viditelny teren (site Teren* a Rybnik_Teren*) - kolize muze lezet jinde nez to, co je videt
	var ter := PackedVector3Array()
	for jm2: String in ["Teren*", "Rybnik_Teren*"]:
		for mi0 in main.find_children(jm2, "MeshInstance3D", true, false):
			var mi := mi0 as MeshInstance3D
			if mi.mesh == null or not mi.is_visible_in_tree() or String(mi.name) == "Teren_obzor":
				continue
			var ab := mi.global_transform * mi.mesh.get_aabb()
			if ab.position.x > sv.RYB_C.x + 70.0 or ab.end.x < sv.RYB_C.x - 70.0 or ab.position.z > sv.RYB_C.y + 70.0 or ab.end.z < sv.RYB_C.y - 70.0:
				continue
			var f := mi.mesh.get_faces()
			var xf := mi.global_transform
			for i in range(0, f.size(), 3):
				var c := xf * f[i]
				if Vector2(c.x, c.z).distance_to(sv.RYB_C) < 70.0:
					ter.append(c)
					ter.append(xf * f[i + 1])
					ter.append(xf * f[i + 2])
	var gt: Dictionary = sv._tri_mrizka(ter, Transform3D())
	var space := player.get_world_3d().direct_space_state
	var chyby: Array = []
	var radky: Array = []
	var hz: Dictionary = Pravidla.cti("voda", "rybnik_lhota", "hraz")
	for t: Dictionary in Pravidla.cti("voda", "toky"):
		var id := String(t["id"])
		if id != "lhota_potok" and id != "lhota_odtok":
			continue
		var o: Array = t["osa_xzy"]
		var body: Array = []
		for k in o.size():
			var p := Vector2(float(o[k][0]), float(o[k][1]))
			var d := p.distance_to(sv.RYB_C)
			if (id == "lhota_potok" and d < 30.0) or (id == "lhota_odtok" and k < 40):
				body.append(p)
		if id == "lhota_potok" and not body.is_empty():
			# az do stredu rybnika: posledni bod osy -> stred (voda rybnika ji ma prevzit)
			var b0: Vector2 = body[body.size() - 1]
			for j in range(1, int(b0.distance_to(sv.RYB_C))):
				body.append(b0.move_toward(sv.RYB_C, float(j)))
		var bez := 0.0
		var nej := 0.0
		var nad_min := INF
		var kde := Vector2.ZERO
		var pred := Vector2.INF
		for p: Vector2 in body:
			var krok := 1.0 if pred == Vector2.INF else p.distance_to(pred)
			pred = p
			var wy: float = sv._tri_vyska(g, p.x, p.y)
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(p.x, 80.0, p.y), Vector3(p.x, -40.0, p.y)))
			var zem := float((h["position"] as Vector3).y) if not h.is_empty() else -INF
			var zv: float = sv._tri_vyska(gt, p.x, p.y)                    # viditelny teren
			if zv != INF and zv != -INF:
				zem = maxf(zem, zv)
			if wy != -INF and wy != INF:
				nad_min = minf(nad_min, wy - zem)
			if wy == -INF or wy == INF or wy < zem + 0.02:
				bez += krok
				if bez > nej:
					nej = bez
					kde = p
			else:
				bez = 0.0
		# trava a rostliny v korytu (louka MultiMesh): instance do sirka/2 od osy = voda zarostla, neni videt
		var tr := 0
		var pul := float(t["sirka_m"]) * 0.5
		for mmi0 in main.find_children("*", "MultiMeshInstance3D", true, false):
			var mmi := mmi0 as MultiMeshInstance3D
			if mmi.multimesh == null or not mmi.is_visible_in_tree():
				continue
			var gx := mmi.global_transform
			var ab := gx * mmi.multimesh.get_aabb()
			if ab.position.x > sv.RYB_C.x + 70.0 or ab.end.x < sv.RYB_C.x - 70.0 or ab.position.z > sv.RYB_C.y + 70.0 or ab.end.z < sv.RYB_C.y - 70.0:
				continue
			var mm := mmi.multimesh
			for ii in mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count:
				var q := gx * mm.get_instance_transform(ii).origin
				var q2 := Vector2(q.x, q.z)
				for k2 in range(0, body.size(), 2):
					if q2.distance_to(body[k2]) < pul:
						tr += 1
						break
		radky.append("%s: bodu %d, nejdelsi usek bez vody %.1f m u (%.0f, %.0f), hladina nad zemi nejmene %.2f m, rostlin v korytu %d" % [id, body.size(), nej, kde.x, kde.y, nad_min, tr])
		if tr > 0:
			chyby.append("%s: %d rostlin v korytu" % [id, tr])
		if nej > 1.0:
			chyby.append("%s bez vody %.1f m u (%.0f, %.0f)" % [id, nej, kde.x, kde.y])
		if id == "lhota_odtok" and not body.is_empty():
			var hc := Vector2(hz["stred"][0], hz["stred"][1])
			var hu := Vector2(hz["smer_osy"][0], hz["smer_osy"][1])
			var dd: Vector2 = (body[0] as Vector2) - hc
			var podel := absf(dd.dot(hu)) - float(hz["delka_m"]) / 2.0
			var napric := absf(dd.dot(hu.orthogonal()))
			# vzdusna pata = koruna/2 + (vyska koruny nad hladinou odtoku) / sklon svahu (+0,5 m na zaobleni)
			var ryb_h := float(Pravidla.cti("voda", "rybnik_lhota")["hladina_y"])
			var o0: Array = t["osa_xzy"][0]
			# pata na urovni dna koryta (pravidlo tools/krok_b/odtok_za_hrazi.py: koryto nesmi do telesa hraze)
			var pata := float(hz["koruna_sirka_m"]) / 2.0 + (ryb_h + float(hz["koruna_nad_hladinou_m"]) - float(o0[2]) + float(t["hloubka_m"])) / float(hz["sklon_svahu"]) + 1.0   # +1 m: body osy po 1 m
			radky.append("odtok zacina %.1f m napric od osy hraze (pata %.1f), podel za koncem hraze %.1f m" % [napric, pata, podel])
			if napric > pata or podel > 0.0:
				chyby.append("odtok nezacina u hraze: %.1f m od osy, %.1f m za jejim koncem" % [napric, podel])
	# diagnostika usti pritoku (12. 11.: poslednich ~8 m svetlych): ktere vodni site a materialy lezi nad osou
	for t2: Dictionary in Pravidla.cti("voda", "toky"):
		if String(t2["id"]) != "lhota_potok":
			continue
		var o2: Array = t2["osa_xzy"]
		for k in range(o2.size() - 18, o2.size(), 2):
			var px := float(o2[k][0])
			var pz := float(o2[k][1])
			var co_je: Array = []
			for mi0 in main.find_children("*", "MeshInstance3D", true, false):
				var mi := mi0 as MeshInstance3D
				if mi.mesh == null or not mi.is_visible_in_tree():
					continue
				var ab := mi.global_transform * mi.mesh.get_aabb()
				if px < ab.position.x or px > ab.end.x or pz < ab.position.z or pz > ab.end.z:
					continue
				for si in mi.mesh.get_surface_count():
					var mt := mi.get_active_material(si)
					var jm := String(mt.resource_name) if mt else "?"
					if jm.begins_with("voda") or jm.contains("hladina") or String(mi.name).contains("oda"):
						co_je.append("%s/%s" % [mi.name, jm])
			# nejblizsi vrchol terenu a jeho barva (g = trava) - zda sit koryto zachyti
			var nej := INF
			var nej_t := ""
			var nej_g := -1.0
			for mi1 in main.find_children("Teren*", "MeshInstance3D", true, false):
				var mt1 := mi1 as MeshInstance3D
				if mt1.mesh == null or not mt1.is_visible_in_tree():
					continue
				var ab1 := mt1.global_transform * mt1.mesh.get_aabb()
				if px < ab1.position.x or px > ab1.end.x or pz < ab1.position.z or pz > ab1.end.z:
					continue
				var arr := mt1.mesh.surface_get_arrays(0)
				var vv: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
				var cc: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
				for vi in vv.size():
					var w := mt1.global_transform * vv[vi]
					var dd := Vector2(w.x - px, w.z - pz).length()
					if dd < nej:
						nej = dd
						nej_t = "%s vrchol %.2f m od osy, barva %s" % [mt1.name, dd, cc[vi] if vi < cc.size() else "-"]
						nej_g = cc[vi].g if vi < cc.size() else -1.0
			print("USTI_HRA (%.1f, %.1f): %s | %s" % [px, pz, ", ".join(co_je), nej_t])
			# dno pod potokem bahno/sterk, ne louka (g = trava; Blender ground_attrs u toku 0,05)
			if nej < 0.5 and nej_g > 0.3:
				chyby.append("dno toku v (%.0f, %.0f) barvy louky g %.2f" % [px, pz, nej_g])
	# 12. 11. (snimek build/ryb8: prazdna misa - hladinu skryl kod stareho navesniho rybnicku): nad stredem rybnika
	# viditelna voda (trojuhelnik hladiny bez skryteho materialu) nad dnem
	var vid := false
	for mi0 in main.find_children("Rybnik_*voda*", "MeshInstance3D", true, false):
		var mi := mi0 as MeshInstance3D
		if not mi.is_visible_in_tree():
			continue
		for si in mi.mesh.get_surface_count():
			var mo := mi.get_surface_override_material(si)
			if mo != null and String(mo.resource_name) == "skryta_hladina":
				continue
			var ab := mi.global_transform * mi.mesh.get_aabb()
			if ab.grow(0.5).has_point(Vector3(sv.RYB_C.x, ab.get_center().y, sv.RYB_C.y)):
				vid = true
	radky.append("hladina rybnika viditelna: %s" % vid)
	if not vid:
		chyby.append("rybnik bez viditelne hladiny")
	print("RYB_NAPOJENI " + " | ".join(radky))
	_vysledek("ryb_napojeni", chyby.is_empty(), "; ".join(radky) + ("" if chyby.is_empty() else " CHYBY " + str(chyby)))


## Dest z Pucharta (13. 11.): rozvrh za 60 dni - destivych dni v rozsahu rozestupu, zadny dest delsi nez trvani_h + doznivani,
## zatazeni pred kapkami; uvnitr (daylight.interior 1) zadny zavoj kapek ani dopady.
func _pocasi() -> void:
	var pc: Node = main.get("pocasi")
	if pc == null or not pc.is_processing():
		_vysledek("pocasi", false, "uzel Pocasi chybi nebo je vypnuty (pocasi.json zapnuto)")
		return
	var chyby: Array = []
	var rz: Array = Pravidla.cti("pocasi", "rozestup_dni")
	var tr: Array = Pravidla.cti("pocasi", "trvani_h")
	var dni := 0
	var nejdelsi := 0.0
	var beh := 0.0
	var pred := 0
	var t := 0.0
	var krok := 0.05
	while t < 60.0 * 24.0:
		var s: Vector3 = pc.stav(t)
		if s.y > 0.05:
			beh += krok
			if beh <= krok and pc.stav(t - 0.3).x < 0.2:
				pred += 1                               # kapky bez zatazeni predem
		else:
			if beh > 0.0:
				dni += 1
			nejdelsi = maxf(nejdelsi, beh)
			beh = 0.0
		t += krok
	var ocek := 60.0 / float(rz[1])
	if dni < int(ocek):
		chyby.append("destu za 60 dni %d (< %d)" % [dni, int(ocek)])
	if dni > int(60.0 / float(rz[0])) + 1:
		chyby.append("destu za 60 dni %d (> %d)" % [dni, int(60.0 / float(rz[0])) + 1])
	if nejdelsi > float(tr[1]) + float(Pravidla.cti("pocasi", "doznivani_h")) + 0.3:
		chyby.append("nejdelsi dest %.1f h" % nejdelsi)
	if pred > 0:
		chyby.append("%d destu bez zatazeni predem" % pred)
	# venku za deste zavoj kapek, v hostinci (pod strechou, paprsek vzhuru) zadny
	pc.vynuceno = 1.0
	await main.fast_travel(Vector3(-40.0, 0.0, 905.0), Vector3(-45.0, 1.6, 910.0), 0.0, "test")
	# trasa 0.999995: zacatek deste zasek 357 ms (sber materialu najednou) - sber po castech, nejdelsi krok pocasi < limit
	var krok_max := 0.0
	for i in 90:
		var t0 := Time.get_ticks_usec()
		pc.call("_krok", 0.0)
		krok_max = maxf(krok_max, (Time.get_ticks_usec() - t0) / 1000.0)
		await get_tree().process_frame
	if not bool(pc.get("_sber_hotov")):
		chyby.append("sber mokrych materialu nedobehl za 90 snimku")
	if (pc.get("_mat_mokro") as Array).is_empty():
		chyby.append("zadny material s dest_mokro (zem, zdivo, skala, drevo)")
	if krok_max > float(Pravidla.cti("postavy", "graf")["mrizka"]["test_snimek_ms"]):
		chyby.append("krok pocasi %.1f ms" % krok_max)
	var venku := 0
	for c: Node in pc.get_children():
		if c is MeshInstance3D and (c as MeshInstance3D).visible:
			venku += 1
	if venku == 0:
		chyby.append("venku za deste zadna vrstva kapek")
	await main.fast_travel(Vector3(-63.0, 0.0, 930.0), Vector3(-66.0, 1.6, 932.0), 0.0, "test")
	for i in 90:
		await get_tree().process_frame
	var vidno := 0
	for c: Node in pc.get_children():
		if c is MeshInstance3D and (c as MeshInstance3D).visible:
			vidno += 1
	if vidno > 0:
		chyby.append("v hostinci viditelne vrstvy kapek %d" % vidno)
	pc.vynuceno = -1.0
	_vysledek("pocasi", chyby.is_empty(), "%d chyb %s; destu za 60 dni %d, nejdelsi %.1f h, mokrych materialu %d" % [chyby.size(), str(chyby), dni, nejdelsi, (pc.get("_mat_mokro") as Array).size()])


## 13. 11. (trasa 0.999994: postavy stoji -9..-12 ms; PC: ridic sukne +18 ms, hlava +13 ms na 20 postav): aktivnich ridicu
## sukne a pruzin nejvys modif_max.sukne, aktivnich LookAt hlav nejvys 2 x modif_max.hlava (hlava + krk) - ve vsi u hostince
func _postavy_modif() -> void:
	var li: Node = main.world.get_node_or_null("Lide") if main.world else null
	if li == null:
		_vysledek("postavy_modif", false, "uzel Lide nenalezen")
		return
	await main.fast_travel(Vector3(-58.0, 0.0, 918.0), Vector3(-66.0, 1.6, 926.0), 0.0, "test")
	var mm: Dictionary = Pravidla.cti("postavy", "modif_max")
	var nejvic := [0, 0, 0]
	for i in 240:
		await get_tree().process_frame
		var n := [0, 0, 0]
		for c: Dictionary in li.get("_lide"):
			if c.has("sukne_ridic") and is_instance_valid(c["sukne_ridic"]) and (c["sukne_ridic"] as SkeletonModifier3D).active:
				n[0] += 1
			if c.has("sukne") and is_instance_valid(c["sukne"]) and (c["sukne"] as SkeletonModifier3D).active:
				n[1] += 1
			for la: SkeletonModifier3D in c.get("hlava_mod", []):
				n[2] += 1 if la.active else 0
		for k in 3:
			nejvic[k] = maxi(nejvic[k], n[k])
	var ok: bool = nejvic[0] <= int(mm["sukne"]) and nejvic[1] <= int(mm["sukne"]) and nejvic[2] <= 2 * int(mm["hlava"])
	_vysledek("postavy_modif", ok, "nejvic aktivnich: ridic sukne %d, pruzina %d, LookAt %d (meze %d / %d / %d), postav %d" % [nejvic[0], nejvic[1], nejvic[2],
			int(mm["sukne"]), int(mm["sukne"]), 2 * int(mm["hlava"]), (li.get("_lide") as Array).size()])


## Generalni kontrola sveta (Misa 14. 11.: „jestli nemame nekde neco, co spolu koliduje a dela zbytecne zaseky nebo
## chyby“): (1) zdvojene site - stejna sit na stejnem miste dvakrat (2x kresleni, z-fighting); (2) zdvojene kolize -
## dva staticke tvary stejneho typu a velikosti na stejnem miste (2x fyzika); (3) MultiMesh se zdvojenymi instancemi.
func _duplicity() -> void:
	var chyby: Array = []
	var site := {}
	var n_s := 0
	for n: Node in get_tree().root.find_children("*", "MeshInstance3D", true, false):
		var m := n as MeshInstance3D
		if m.mesh == null or not m.is_visible_in_tree():
			continue
		n_s += 1
		var k := "%d|%s" % [m.mesh.get_instance_id(), str(m.global_position.snapped(Vector3.ONE * 0.02))]
		if site.has(k):
			if chyby.size() < 30:
				chyby.append("sit 2x: %s a %s u %s" % [str(site[k]).right(50), str(m.get_path()).right(50), m.global_position.snapped(Vector3.ONE * 0.1)])
		else:
			site[k] = m.get_path()
	var tvary := {}
	var n_k := 0
	for n: Node in get_tree().root.find_children("*", "CollisionShape3D", true, false):
		var cs := n as CollisionShape3D
		if cs.shape == null or cs.disabled:
			continue
		n_k += 1
		var k2 := "%s|%s|%s" % [cs.shape.get_class(), str(cs.global_position.snapped(Vector3.ONE * 0.02)), str(cs.shape.get_debug_mesh().get_aabb().size.snapped(Vector3.ONE * 0.02)) if cs.shape.get_debug_mesh() else ""]
		if tvary.has(k2):
			if chyby.size() < 60:
				chyby.append("kolize 2x: %s a %s" % [str(tvary[k2]).right(50), str(cs.get_path()).right(50)])
		else:
			tvary[k2] = cs.get_path()
	var n_mm := 0
	for n: Node in get_tree().root.find_children("*", "MultiMeshInstance3D", true, false):
		var mmi := n as MultiMeshInstance3D
		if mmi.multimesh == null:
			continue
		var mm := mmi.multimesh
		var poc := mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
		if poc > 20000:
			continue
		var vid := {}
		for i in poc:
			var kp := str(mm.get_instance_transform(i).origin.snapped(Vector3.ONE * 0.01))
			if vid.has(kp):
				n_mm += 1
				if n_mm <= 10:
					chyby.append("MultiMesh %s: instance 2x u %s" % [str(mmi.get_path()).right(50), kp])
			vid[kp] = true
	print("DUPLICITY sit %d, kolizi %d, zdvojenych instanci MultiMesh %d" % [n_s, n_k, n_mm])
	for ch9: String in chyby:
		print("DUPLICITA ", ch9)
	_vysledek("duplicity", chyby.is_empty(), "%d nalezu (sit %d, kolize %d) %s" % [chyby.size(), n_s, n_k, str(chyby.slice(0, 5))])


## Misa 14. 11. (nastaveni: po prepnuti denni doby menu skoci nahoru, znovu scrolovat): obnova stranky nastaveni drzi posun
func _menu_posun() -> void:
	var mn: Node = main.menu
	mn.call("show_menu", true, true)
	mn.call("show_page", "settings")
	for i in 3:
		await get_tree().process_frame
	var sc: ScrollContainer = mn.get("_scroll")
	sc.scroll_vertical = 200
	for i in 2:
		await get_tree().process_frame
	var pred := sc.scroll_vertical
	mn.call("refresh_settings", mn.get("settings_text"))
	for i in 4:
		await get_tree().process_frame
	var po := sc.scroll_vertical
	mn.call("hide_menu")
	_vysledek("menu_posun", pred > 0 and po == pred, "posun pred %d, po obnove %d (0 = obsah se vejde, test neplatny)" % [pred, po])
