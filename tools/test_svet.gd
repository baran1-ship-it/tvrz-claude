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
	for t: String in ["shadery", "sonda", "breh", "visici", "kolize_drobne", "stanoviste", "pokryv", "dira", "pasmo", "dalka", "prochod", "teleport", "pamet", "sekani", "stuj", "autotest", "bod", "louc_zed", "svetla", "vratka", "pamet_stani", "pamet_okruh", "pamet_pauza", "nizka_trava", "interier", "cesty_volne", "steny", "briza", "rybnik_ves", "fyzika", "vlastni_site", "lom_na_zemi", "co_tu", "stavby_na_zemi", "dvere_domu", "lezeni"]:
		if jen.is_empty() or jen.has(t):
			await call("_" + t)
	var ok := true
	print("TEST SVET ------------------------------")
	for v: Array in vysledky:
		print("TEST %-14s %s  %s" % [v[0], "OK   " if v[1] else "CHYBA", v[2]])
		ok = ok and bool(v[1])
	print("TEST SVET %s" % ("PROSEL" if ok else "NEPROSEL"))


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
	var cile := [[Vector3(2.5, 0.0, 40.0), Vector3(0.0, 4.5, 15.0)], [Vector3(-53.2, 0.0, 878.1), Vector3(-71.0, 3.0, 881.0)],
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
	var trasa := [Vector2(2.5, 40.0), Vector2(-95.0, 225.0), Vector2(-53.2, 878.1), Vector2(-197.2, 558.6), Vector2(2.5, 40.0)]
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
		if rec["id"] == "drzak_louce" and Vector2(float(rec["p"].x), float(rec["p"].z)).distance_to(Vector2(-70.0, 881.0)) < 15.0:
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
	var spatne := 0
	var n := 0
	for k in sv._briza_kmeny:
		var m: Mesh = sv._briza_kmeny[k]
		n += 1
		if m.get_surface_count() < 3:
			spatne += 1
	_vysledek("briza", n >= 4 and spatne == 0, "variant %d, bez oddeleneho kmene %d" % [n, spatne])


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
	var p := Vector3(-74.0, 44.0, 875.0)
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
			[Vector2(150.0, 930.0), Vector2(160.0, 975.0)], [Vector2(450.0, 790.0), Vector2(530.0, 880.0)]]
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
			await get_tree().physics_frame
			var t := Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
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
