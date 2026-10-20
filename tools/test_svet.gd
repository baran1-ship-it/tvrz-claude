extends Node
## Testy sveta pred vydanim (radce 20:05): TVRZ_TEST=svet (dev_test.gd), musi projit, vysledek do docs/stav.md.
##   pokryv         louka bez mezer (radce 07:45): v bode mimo cesty, dvory, vodu, skaly a les soucet pokryvu trsu a drnu
##                  do 0,5 m >= 0,95 u 98 % bodu (5 mist, 200 bodu do 12 m od hrace).
##   shadery        nejvic 13 vzorkovacu na shader (Adreno: 14. = shader se nesestavi, teren pruhledny - 0.56).
##   visici         spodek kazde instance MultiMeshe v krajine <= povrch pod ni + 0,3 m (paprsek na fyziku sveta);
##                  louka (vlastni vysky z mrizky) a skaly samy vyjimka. Limit 0.
##   kolize_drobne  fyzika (Misa 20:10): mekke rostliny bez kolize, stromy s kmenem (tvrde veci kolizi maji vzdy).
##   stanoviste     skaly (vychozy) a smrky ne v kosene louce, kameni ne v louce (jen bor, pesiny, voda). Limit 0.
##   dalka          kopec ve 300 m: jas vuci louce u hrace 0,5-0,8, odstin +-10 st.
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
	for i in 10:
		await get_tree().process_frame
	await get_tree().physics_frame
	for t: String in ["shadery", "sonda", "visici", "kolize_drobne", "stanoviste", "pokryv", "dalka", "prochod"]:
		if jen.is_empty() or jen.has(t):
			await call("_" + t)
	var ok := true
	print("TEST SVET ------------------------------")
	for v: Array in vysledky:
		print("TEST %-14s %s  %s" % [v[0], "OK   " if v[1] else "CHYBA", v[2]])
		ok = ok and bool(v[1])
	print("TEST SVET %s" % ("PROSEL" if ok else "NEPROSEL"))


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
	_vysledek("sonda", true, s.substr(3))


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
	for c in body.get_children():
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
			if sv._louka_m(a.x, a.y) > 0.6 and sv._les(a.x, a.y) < 0.05 and sv._st(2, a.x, a.y) < 0.05 and sv.pes_d(a.x, a.y) > 6.0:
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
		for mmi in louka.find_children("*", "MultiMeshInstance3D", true, false):
			var mm: MultiMesh = (mmi as MultiMeshInstance3D).multimesh
			if mm == null:
				continue
			var w := 0.0
			if mm.mesh == louka._drn:
				w = 0.25
			elif mm.mesh == louka._trs:
				w = 0.15
			elif mm.mesh == louka._vysoka:
				w = 0.3
			if w == 0.0:
				continue
			var xf := (mmi as Node3D).global_transform
			var n := mm.instance_count if mm.visible_instance_count < 0 else mm.visible_instance_count
			for i in n:
				var o := xf * mm.get_instance_transform(i).origin
				if Vector2(o.x, o.z).distance_to(a) > 14.0:
					continue
				var key := Vector2i(floori(o.x), floori(o.z))
				if not bunky.has(key):
					bunky[key] = []
				(bunky[key] as Array).append(Vector3(o.x, o.z, w))
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
	for j in range(1, 24):
		for i in range(1, 24):
			var a := Vector2(r.position.x + r.size.x * i / 24.0, r.position.y + r.size.y * j / 24.0)
			if not sv.kosena_louka(a.x, a.y):
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
				if volno:
					out.append([a, b])
					break
			if out.size() >= 3:
				return out
	return out


func _barva(img: Image, p: Vector2) -> Color:
	var c := Color(0, 0, 0)
	var k := 0
	for dx in range(-40, 41, 4):
		for dy in range(-6, 7, 3):
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
	for nm: String in trasy:
		var r: Array = await _jdi(trasy[nm])
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
			while Vector2(wp.x - player.global_position.x, wp.y - player.global_position.z).length() > 1.5:
				var to := Vector2(wp.x - player.global_position.x, wp.y - player.global_position.z)
				player.yaw = atan2(-to.x, -to.y)
				var side := 0.0
				if stuck > 0.6:
					side = 0.8 if int(stuck * 1.5) % 2 == 0 else -0.8
				player.move_input = Vector2(side, 1.0)
				await get_tree().physics_frame
				t += 1.0 / 60.0
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
