extends Node
## Jen pro vyvoj (do exportu se nebali): automaticke testy a snimky.
## TVRZ_TEST=walk  -> navigacni sit, bot obejde vsechny mistnosti, test luku, interakci a dotyku
## TVRZ_TEST=shots -> snimky z pohledu hrace vcetne HUD do TVRZ_OUT

var main: Node
var player: CharacterBody3D
var fails: Array = []
var log_lines: Array = []


func _ready() -> void:
	main = get_parent()
	player = main.player
	process_mode = Node.PROCESS_MODE_ALWAYS
	var mode := OS.get_environment("TVRZ_TEST")
	await _frames(3)
	if mode == "shots":
		await _shots()
	elif mode == "probe":
		await _probe()
	elif mode == "pad":
		await _pad_test()
	elif mode == "sber":
		await _sber_test()
	elif mode == "zvuky":
		await _zvuky_test()
	elif mode == "skala":
		player.flying = false
		player.place(Vector3(-112.32, 70.0, 308.75), Vector3(-100.0, 60.0, 308.75))
		await _frames(240)
		print("SKALA pristal na y %.2f (kvadr mel vrch 44.07)" % player.global_position.y)
	elif mode == "hostinec":
		await _hostinec_test()
	elif mode == "louka_chuze":
		# chuze loukou 6 m/s: casy louky v hlavnim vlakne (TVRZ_LOUKA_CAS=1)
		player.set_flying(true)
		var a := Vector3(100, 0, 150)
		for i in 600:
			var t := i / 60.0
			var p := a + Vector3(t * 6.0, 0, t * 2.0)
			p.y = main._ground_hi(p.x, p.z) + 1.7
			player.global_position = p
			await get_tree().process_frame
		print("CHUZE hotovo ", player.global_position)
	elif mode == "visici":
		# stromy vysoko nad terenem (po usazeni skal): ktere a proc
		await _frames(10)
		var sv = main.svet
		var r: Dictionary = sv.data["rostliny"]
		var space := player.get_world_3d().direct_space_state
		var n := 0
		for k: String in r:
			if not (k.begins_with("borovice") or k.begins_with("briza") or k.begins_with("smrk")) or k.contains("daleko"):
				continue
			for t: Array in r[k]:
				var x := float(t[3])
				var z := float(t[11])
				var y := float(t[7])
				if absf(x + 120.0) > 70.0 or absf(z - 310.0) > 70.0:
					continue
				var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, y + 0.5, z), Vector3(x, y - 40.0, z)))
				var gap := 99.0 if h.is_empty() else y + 0.5 - (h["position"] as Vector3).y - 0.5
				if gap > 1.0 and y > sv._vyska(x, z) + 3.0:
					n += 1
					if n < 15:
						print("VISI %s (%.1f, %.1f, %.1f) mezera %.1f teren %.1f" % [k, x, y, z, gap, sv._vyska(x, z)])
		print("VISI celkem ", n)
		# impostory a vsechny MultiMeshe stromu (polohy z bufferu, ne z tabulky)
		var ni := 0
		var prohl := 0
		for mmi in main.find_children("*", "MultiMeshInstance3D", true, false):
			var nm := String(mmi.name)
			var imp := nm.begins_with("impostor_")
			var stromy := ["borovice", "briza", "smrk", "dub", "lipa", "buk", "olse", "vrba"]
			var je := imp
			for sd: String in stromy:
				if nm.begins_with(sd):
					je = true
			if not je:
				continue
			var mm: MultiMesh = (mmi as MultiMeshInstance3D).multimesh
			prohl += mm.instance_count
			for i in mm.instance_count:
				var pos: Vector3 = (mmi as Node3D).global_position + Vector3(mm.get_instance_custom_data(i).r, mm.get_instance_custom_data(i).g, mm.get_instance_custom_data(i).b) if imp else (mmi as Node3D).global_transform * mm.get_instance_transform(i).origin
				if pos.y < sv._vyska(pos.x, pos.z) + 3.0:
					continue
				var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(pos + Vector3(0, 0.5, 0), pos - Vector3(0, 40, 0)))
				var gap := 99.0 if h.is_empty() else pos.y - (h["position"] as Vector3).y
				if gap > 1.0:
					ni += 1
					if ni < 8:
						print("VISI MM %s %s mezera %.1f" % [nm, pos, gap])
		print("VISI MM celkem %d z %d" % [ni, prohl])
	elif mode == "pixel":
		# co je na snimku v danych pixelech (K750_skaly): kamera jako TVRZ_MERENI, promitnout vsechny instance
		player.set_flying(true)
		var a := Vector2(-125, 325)
		var b := Vector2(-112, 308)
		player.place(Vector3(a.x, main._ground_hi(a.x, a.y) + 1.7, a.y), Vector3(b.x, main._ground_hi(b.x, b.y) + 1.2, b.y))
		await _frames(10)
		get_window().size = Vector2i(1280, 800)
		await _frames(3)
		var cam: Camera3D = player.cam
		var vs := get_viewport().get_visible_rect().size
		print("PIXEL smer ", -cam.global_transform.basis.z, " aktivni ", cam.current)
		print("PIXEL kamera ", cam.global_position, " vyrez ", vs, " fov ", cam.fov)
		for mmi in main.find_children("*", "MultiMeshInstance3D", true, false):
			var mm: MultiMesh = (mmi as MultiMeshInstance3D).multimesh
			if mm == null or mm.instance_count > 20000:
				continue
			var imp := String(mmi.name).begins_with("impostor_")
			for i in mm.instance_count:
				var pos: Vector3 = (mmi as Node3D).global_position + Vector3(mm.get_instance_custom_data(i).r, mm.get_instance_custom_data(i).g, mm.get_instance_custom_data(i).b) if imp else (mmi as Node3D).global_transform * mm.get_instance_transform(i).origin
				if cam.is_position_behind(pos + Vector3(0, 6, 0)):
					continue
				var sp := cam.unproject_position(pos + Vector3(0, 6, 0)) * Vector2(1280, 800) / vs
				if sp.y < 200.0 and sp.x > 0.0 and sp.x < 1280.0:
					print("PIXEL %s: %s %s vzdal %.0f teren %.1f" % [sp, mmi.name, pos, pos.distance_to(cam.global_position), main.svet._vyska(pos.x, pos.z)])
	elif mode == "podstromem":
		await _frames(10)
		for c: Vector3 in [Vector3(-114.21, 48.28, 319.12), Vector3(-126.87, 48.6, 305.9)]:
			for mmi in main.find_children("*", "MultiMeshInstance3D", true, false):
				var mm: MultiMesh = (mmi as MultiMeshInstance3D).multimesh
				if mm == null or not String(mmi.name).begins_with("skala"):
					continue
				for i in mm.instance_count:
					var xf: Transform3D = (mmi as Node3D).global_transform * mm.get_instance_transform(i)
					if Vector2(xf.origin.x - c.x, xf.origin.z - c.z).length() < 6.0:
						print("POD %s: %s %s meritko %.2f vis %.0f-%.0f" % [c, mmi.name, xf.origin, xf.basis.get_scale().y,
								(mmi as GeometryInstance3D).visibility_range_begin, (mmi as GeometryInstance3D).visibility_range_end])
	elif mode == "foto":
		# TVRZ_FOTO="x,y,z,tx,ty,tz;soubor.png": kamera kdekoli (i ve vzduchu)
		var f := OS.get_environment("TVRZ_FOTO").split(";")
		var v := f[0].split_floats(",")
		player.set_flying(true)
		player.place(Vector3(v[0], v[1], v[2]), Vector3(v[3], v[4], v[5]))
		main.get_node("Louka").nacti_okoli()
		await _frames(60)
		get_viewport().get_texture().get_image().save_png(f[1])
		print("FOTO ", f[1])
	elif mode == "balkon":
		await _frames(10)
		var space := player.get_world_3d().direct_space_state
		for y: float in [45.9, 46.3, 46.8, 47.4]:
			var qq := PhysicsRayQueryParameters3D.create(Vector3(-68.11, y, 875.98), Vector3(-65.94, y, 875.63))
			for ab in main.find_children("*", "AnimatableBody3D", true, false):
				qq.exclude += [(ab as CollisionObject3D).get_rid()]
			var h := space.intersect_ray(qq)
			print("BALKON dvermi y %.1f: %s" % [y, "volno" if h.is_empty() else "%s %s" % [(h["collider"] as Node).name, h["position"]]])
		for p: Vector3 in [Vector3(-68.11, 47.5, 875.98), Vector3(-67.4, 47.5, 875.86), Vector3(-67.03, 47.5, 875.8), Vector3(-66.6, 47.5, 875.74), Vector3(-65.94, 47.5, 875.63), Vector3(-65.4, 47.5, 875.55)]:
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(p, p - Vector3(0, 10, 0)))
			print("BALKON podlaha %s: %s" % [p, "nic" if h.is_empty() else "%s %.2f" % [(h["collider"] as Node).name, (h["position"] as Vector3).y]])
	elif mode == "materialy":
		await _frames(5)
		for n in main.find_children("Teren*", "MeshInstance3D", true, false):
			var mi := n as MeshInstance3D
			var mats := []
			for i in mi.mesh.get_surface_count():
				var m := mi.get_active_material(i)
				mats.append((m.shader.resource_path if m is ShaderMaterial else m.get_class()) if m else "nic")
			print("MAT ", mi.name, " ", mats, " ", mi.get_aabb().size)
		var hid := main.find_children("Staticky_hostinec*", "Node3D", true, false)
		for h in hid:
			for mi in h.find_children("*", "MeshInstance3D", true, false):
				var me := (mi as MeshInstance3D).mesh
				for i in me.get_surface_count():
					var m := me.surface_get_material(i)
					var nm := m.resource_name if m else ""
					if nm.to_lower().contains("krb") or nm.to_lower().contains("popel") or nm.to_lower().contains("fire") or nm.to_lower().contains("ash"):
						print("KRB mat ", mi.name, " ", nm)
	elif mode == "sit":
		for n in main.find_children("Teren*", "MeshInstance3D", true, false):
			var mi := n as MeshInstance3D
			var a := mi.mesh.surface_get_arrays(0)
			var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
			var bb := mi.get_aabb()
			print("SIT %s vrcholu %d plocha %.0f m2 -> %.2f m rozestup" % [mi.name, v.size(), bb.size.x * bb.size.z, sqrt(bb.size.x * bb.size.z / maxf(v.size(), 1))])
	elif mode == "vody":
		for n in main.find_children("*", "MeshInstance3D", true, false):
			var mi := n as MeshInstance3D
			if mi.mesh == null:
				continue
			for i in mi.mesh.get_surface_count():
				var m := mi.mesh.surface_get_material(i)
				var nm := m.resource_name if m else ""
				if nm.begins_with("voda"):
					var a := mi.mesh.surface_get_arrays(i)
					var bb := AABB()
					var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
					bb.position = mi.global_transform * v[0]
					for q in v:
						bb = bb.expand(mi.global_transform * q)
					print("VODA %s %s vrch %d %s viditelna %s" % [mi.get_path(), nm, v.size(), bb, mi.visible])
	elif mode == "paprsek":
		await _frames(5)
		var space := player.get_world_3d().direct_space_state
		var cnt := {}
		for j in range(-30, 31, 2):
			var row := ""
			for i in range(-40, 21, 2):
				var x := -71.0 + i
				var z := 881.0 + j
				var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, 120, z), Vector3(x, 0, z)))
				var nm := "-" if h.is_empty() else String((h["collider"] as Node).name)
				row += "T" if nm.begins_with("Teren") else nm.left(1)
				cnt[nm] = cnt.get(nm, 0) + 1
			print(row)
		print(cnt)
	elif mode == "pruchod":
		await _pruchod_test()
	elif mode == "svet":
		# testy pred vydanim (radce 20:05): tools/test_svet.gd
		var ts: Node = load("res://tools/test_svet.gd").new()
		add_child(ts)
		await ts.run(main)
	else:
		await _walk_test()
	get_tree().quit()


func _frames(n: int) -> void:
	for k in n:
		await get_tree().physics_frame


func _ok(cond: bool, what: String) -> void:
	if cond:
		print("  ok   ", what)
	else:
		print("  FAIL ", what)
		fails.append(what)


# ------------------------------------------------------------------ chuze po navigacni siti

func _bake_nav() -> RID:
	var nm := NavigationMesh.new()
	nm.cell_size = 0.1
	nm.cell_height = 0.05
	nm.agent_radius = 0.3
	nm.agent_height = 1.7
	nm.agent_max_climb = 0.42
	nm.agent_max_slope = 50.0
	nm.region_min_size = 4.0
	nm.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	nm.geometry_source_geometry_mode = NavigationMesh.SOURCE_GEOMETRY_ROOT_NODE_CHILDREN
	nm.filter_baking_aabb = AABB(Vector3(-40, -8, -32), Vector3(80, 34, 85))
	var src := NavigationMeshSourceGeometryData3D.new()
	var t0 := Time.get_ticks_msec()
	NavigationServer3D.parse_source_geometry_data(nm, src, main.world)
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	print("navmesh: ", nm.get_polygon_count(), " polygonu za ", Time.get_ticks_msec() - t0, " ms")
	var map := player.get_world_3d().navigation_map
	NavigationServer3D.map_set_cell_size(map, 0.1)
	NavigationServer3D.map_set_cell_height(map, 0.05)
	var region := NavigationRegion3D.new()
	region.navigation_mesh = nm
	main.add_child(region)
	await _frames(4)
	NavigationServer3D.map_force_update(map)
	return map


## Volne misto na podlaze blizko cile, ke kteremu vede cesta (stred mistnosti muze byt pod stolem).
func _free_goal(map: RID, target: Vector3) -> Vector3:
	var best := Vector3.INF
	for ring in 7:
		var r := ring * 0.5
		var steps := maxi(1, ring * 8)
		for k in steps:
			var a := TAU * k / steps
			var p := target + Vector3(cos(a) * r, 0.0, sin(a) * r)
			var c := NavigationServer3D.map_get_closest_point(map, p)
			if absf(c.y - target.y) > 0.35 or Vector2(c.x - p.x, c.z - p.z).length() > 0.3:
				continue
			var path := NavigationServer3D.map_get_path(map, player.global_position, c, true)
			if path.size() > 0 and path[path.size() - 1].distance_to(c) < 0.3:
				return c
	return best


func _go(map: RID, target: Vector3, name: String) -> bool:
	var goal := _free_goal(map, target)
	if goal == Vector3.INF:
		_ok(false, "%s: neexistuje cesta k %s" % [name, target])
		return false
	var path := NavigationServer3D.map_get_path(map, player.global_position, goal, true)
	var length := 0.0
	for k in range(1, path.size()):
		length += path[k - 1].distance_to(path[k])
	var limit := length / 1.6 + 8.0
	var t := 0.0
	var i := 1
	var stuck := 0.0
	var last := player.global_position
	while i < path.size():
		var wp: Vector3 = path[i]
		var to := wp - player.global_position
		var flat := Vector2(to.x, to.z)
		if flat.length() < 0.2 and absf(to.y) < 1.2:
			i += 1
			continue
		player.yaw = atan2(-to.x, -to.z)
		# kdyz se nehybe, uhni kousek bokem (jako by to udelal clovek)
		var side := 0.0
		if stuck > 0.5:
			side = 0.6 if int(stuck * 2.0) % 2 == 0 else -0.6
		player.move_input = Vector2(side, 0.7)
		await get_tree().physics_frame
		t += 1.0 / 60.0
		if player.global_position.distance_to(last) > 0.25:
			last = player.global_position
			stuck = 0.0
		else:
			stuck += 1.0 / 60.0
		if stuck > 4.0 or t > limit:
			player.move_input = Vector2.ZERO
			_ok(false, "%s: zaseknuty u %s (bod %d/%d)" % [name, player.global_position, i, path.size()])
			return false
	player.move_input = Vector2.ZERO
	await _frames(10)
	var d := player.global_position.distance_to(goal)
	_ok(d < 0.9, "%s: dosazeno za %.1f s, cesta %.0f m, mistnost '%s', misto '%s'" % [name, t, length, main.life.room_name, main.life.place])
	return d < 0.9


## Prima chuze po bodech (uvnitr mistnosti, kde neni co obchazet).
func _walk_direct(pts: Array, name: String) -> bool:
	for wp: Vector3 in pts:
		var t := 0.0
		while Vector2(wp.x - player.global_position.x, wp.z - player.global_position.z).length() > 0.15:
			var to: Vector3 = wp - player.global_position
			player.yaw = atan2(-to.x, -to.z)
			player.move_input = Vector2(0, 0.5)
			await get_tree().physics_frame
			t += 1.0 / 60.0
			if t > 8.0:
				player.move_input = Vector2.ZERO
				_ok(false, "%s: nedojdu k %s, stojim u %s" % [name, wp, player.global_position])
				return false
	player.move_input = Vector2.ZERO
	return true


func _center(r: Dictionary) -> Vector3:
	var a: AABB = r["aabb"]
	return Vector3(a.position.x + a.size.x * 0.5, a.position.y + 0.05, a.position.z + a.size.z * 0.5)


func _walk_test() -> void:
	print("=== TEST: chuze, mistnosti, luk, interakce, dotyk ===")
	var map := await _bake_nav()
	var spawn := player.global_position
	_ok(player.is_on_floor() or true, "start %s" % spawn)
	await _frames(30)
	_ok(player.is_on_floor(), "hrac stoji na zemi po startu (y=%.2f)" % player.global_position.y)
	var goals: Array = [
		["nadvori", Vector3(0, 0.1, 2.0)],
		["strelnice", Vector3(-14.75, 0.1, 11.6)],
		["kovarna", Vector3(13.6, 0.1, 7.6)],
	]
	for r: Dictionary in main.info["rooms"]:
		if r["name"] != "vez2":
			goals.append([r["name"], _center(r)])
	goals.append(["hradby jih", Vector3(-8.0, 6.6, 14.9)])
	goals.append(["hradby vychod", Vector3(17.9, 6.6, 0.0)])
	goals.append(["zpet ven", spawn])
	var reached := 0
	for g: Array in goals:
		if await _go(map, g[1], g[0]):
			reached += 1
		if g[0] == "vez1":
			# na ochoz veze rucne: navigacni sit tu horni schod nespoji, hrac ho ale vyjde
			if await _walk_direct([Vector3(-16.6, 6.5, -10.85), Vector3(-17.75, 6.5, -10.8)], "pata hornich schodu"):
				for leg: Array in [[Vector2(0, -1), 3.6], [Vector2(1, 0), 4.6], [Vector2(0, 1), 1.6]]:
					player.yaw = atan2(-leg[0].x, -leg[0].y)
					player.move_input = Vector2(0, 0.7)
					await _frames(int(leg[1] * 60))
				player.move_input = Vector2.ZERO
				await _frames(20)
				_ok(main.life.room_name == "vez2", "vez2: vyslap po schodech, mistnost '%s', y=%.2f" % [main.life.room_name, player.global_position.y])
				if main.life.room_name == "vez2":
					reached += 1
			# zpet dolu (sit horni patro veze nezna)
			player.global_position = Vector3(-15.8, 0.1, -12.8)
			player.velocity = Vector3.ZERO
			await _frames(20)
	print("dosazeno %d / %d cilu" % [reached, goals.size() + 1])

	# --- luk
	print("--- luk")
	var bow_use: Dictionary = {}
	for u: Dictionary in main.info["use"]:
		if u["kind"] == "bow":
			bow_use = u
	await _go(map, Vector3(bow_use["pos"].x + 0.3, 0.1, bow_use["pos"].z - 1.3), "ke stojanu s luky")
	_face(bow_use["pos"])
	await _frames(5)
	main._process(0.0)
	_ok(main.hud.use_text == "Vzít luk", "nabidka u stojanu: '%s'" % main.hud.use_text)
	main.hud.use_pressed.emit()
	await _frames(5)
	_ok(main.bow.equipped, "luk v ruce")
	await _go(map, Vector3(-14.75, 0.1, 11.2), "na streleckou caru")
	var hits := 0
	var tgt: Array = main.info["targets"]
	_ok(tgt.size() > 0, "terce: %d" % tgt.size())
	var shot_at := 0
	for t: Dictionary in tgt:
		var c: Vector3 = t["center"]
		if c.distance_to(player.global_position) > 24.0:
			continue
		shot_at += 1
		for shot in 2:
			_aim_ballistic(c, 1.0)
			main.bow.begin_draw()
			await _frames(70)
			var before: int = main.bow.total
			main.bow.release()
			await _frames(150)
			if main.bow.total > before:
				hits += 1
			print("    terc %s: body %d -> %d" % [c, before, main.bow.total])
	_ok(shot_at >= 2 and hits >= shot_at, "zasahy terce: %d z %d vystrelu, celkem %d bodu" % [hits, shot_at * 2, main.bow.total])
	# vystrel do zdi se zapichne
	player.look(0.0, 0.0)
	main.bow.begin_draw()
	await _frames(20)
	main.bow.release()
	await _frames(120)
	_ok(main.bow._flying.size() == 0, "zadny sip nezustal letet")
	await _go(map, Vector3(bow_use["pos"].x + 0.3, 0.1, bow_use["pos"].z - 1.3), "zpet ke stojanu")
	_face(bow_use["pos"])
	await _frames(3)
	main._process(0.0)
	_ok(main.hud.use_text == "Vrátit luk", "nabidka vratit: '%s'" % main.hud.use_text)
	main.hud.use_pressed.emit()
	await _frames(3)
	_ok(not main.bow.equipped, "luk vracen")

	# --- interakce
	print("--- interakce")
	for kind: String in ["anvil", "fire", "bed"]:
		for u: Dictionary in main.info["use"]:
			if u["kind"] != kind:
				continue
			var p: Vector3 = u["pos"]
			var floor_y := 0.1 if p.y < 2.5 else 3.95
			var near := Vector3(p.x, floor_y, p.z)
			if kind == "bed":
				near = Vector3(15.2, 3.95, -10.9)
			await _go(map, near, "k predmetu %s %s" % [kind, u.get("name", "")])
			_face(p)
			await _frames(3)
			main._process(0.0)
			var label: String = main.hud.use_text
			_ok(label != "", "%s: nabidka '%s'" % [kind, label])
			var before: String = main.day.current
			main.hud.use_pressed.emit()
			await _frames(200)
			if kind == "bed":
				_ok(main.day.current != before, "spanek zmenil denni dobu %s -> %s" % [before, main.day.current])
			break

	# --- dotykove ovladani pres skutecne vstupni udalosti
	print("--- dotyk")
	await _go(map, Vector3(0, 0.1, 2.0), "nadvori")
	var vs: Vector2 = main.hud._size()
	var y0: float = player.yaw
	_touch(0, Vector2(200, vs.y - 150), true)
	_drag(0, Vector2(200, vs.y - 260))
	await _frames(2)
	_ok(player.move_input.y > 0.8, "packa dopredu: %s" % player.move_input)
	var p0 := player.global_position
	await _frames(40)
	_ok(player.global_position.distance_to(p0) > 1.0, "hrac se pohnul o %.2f m" % player.global_position.distance_to(p0))
	_touch(1, Vector2(vs.x * 0.7, vs.y * 0.4), true)
	_drag(1, Vector2(vs.x * 0.7 + 150, vs.y * 0.4))
	await _frames(2)
	_ok(absf(player.yaw - y0) > 0.3, "tazeni vpravo otaci (%.2f rad)" % (player.yaw - y0))
	_touch(1, Vector2(vs.x * 0.7 + 150, vs.y * 0.4), false)
	_touch(0, Vector2(200, vs.y - 260), false)
	await _frames(2)
	_ok(player.move_input == Vector2.ZERO, "pusteni packy zastavi")
	_touch(2, Vector2(vs.x - 50, 45), true)
	await _frames(2)
	_ok(get_tree().paused, "tlacitko menu pozastavi hru")
	main._on_menu("quality")
	main._on_menu("time")
	main._on_menu("resume")
	await _frames(5)
	_ok(not get_tree().paused, "pokracovat")
	_touch(2, Vector2(vs.x - 50, 45), false)

	print("=== VYSLEDEK: %s (%d chyb) ===" % ["OK" if fails.is_empty() else "CHYBY", fails.size()])
	for f: String in fails:
		print("   - ", f)


func _face(p: Vector3) -> void:
	var to: Vector3 = p - player.cam.global_position
	player.yaw = atan2(-to.x, -to.z)
	player.pitch = atan2(to.y, Vector2(to.x, to.z).length())
	player.look(0.0, 0.0)


## Namiri s ohledem na pad sipu (rychlost odpovida plnemu napnuti).
func _aim_ballistic(c: Vector3, draw: float) -> void:
	var v := 16.0 + 46.0 * draw
	var eye: Vector3 = player.cam.global_position
	var to := c - eye
	var dx := Vector2(to.x, to.z).length()
	var tflight := dx / v
	var drop := 0.5 * 9.81 * tflight * tflight
	_face(c + Vector3(0, drop, 0))


func _touch(idx: int, pos: Vector2, pressed: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index = idx
	e.position = _to_window(pos)
	e.pressed = pressed
	Input.parse_input_event(e)


func _drag(idx: int, pos: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.index = idx
	e.position = _to_window(pos)
	Input.parse_input_event(e)


## Prevede souradnice HUD (zakladni rozliseni) na souradnice okna, jak by je poslal dotyk.
func _to_window(p: Vector2) -> Vector2:
	var xf := get_viewport().get_final_transform()
	return xf * p


# ------------------------------------------------------------------ snimky

func _shot(name: String, frames: int = 40) -> void:
	await _frames(frames)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var out := OS.get_environment("TVRZ_OUT")
	img.save_png(out.path_join(name + ".png"))
	print("shot ", name)


func _view(feet: Vector3, look: Vector3) -> void:
	player.place(feet, look)


func _shots() -> void:
	var day: Node = main.day
	var views: Array = String(OS.get_environment("TVRZ_VIEWS")).split(",", false)
	var all := views.is_empty()
	var V := {
		"01_prichod": [Vector3(2.5, -99, 40.0), Vector3(0.0, 4.5, 15.0), "odpoledne"],
		"02_nadvori": [Vector3(1.0, 0.0, 9.5), Vector3(5.0, 2.6, -7.0), "odpoledne"],
		"03_sin": [Vector3(4.6, 0.0, -9.6), Vector3(16.0, 1.2, -11.0), "odpoledne"],
		"04_loznice": [Vector3(8.4, 3.9, -8.8), Vector3(16.0, 4.6, -12.6), "odpoledne"],
		"05_straznice": [Vector3(-6.0, 0.0, 9.4), Vector3(-9.6, 1.3, 13.6), "odpoledne"],
		"06_kovarna": [Vector3(11.4, 0.0, 8.8), Vector3(16.0, 1.1, 5.6), "odpoledne"],
		"07_strelnice": [Vector3(-14.75, 0.0, 11.2), Vector3(-14.7, 1.3, -4.0), "odpoledne"],
		"08_hradby": [Vector3(-8.0, 6.5, 14.9), Vector3(40.0, -6.0, 140.0), "odpoledne"],
		"09_vez": [Vector3(-15.8, 13.0, -12.8), Vector3(-150.0, 0.0, 40.0), "rano"],
		"10_sin_noc": [Vector3(4.6, 0.0, -9.6), Vector3(16.0, 1.2, -11.0), "noc"],
		"11_nadvori_soumrak": [Vector3(-9.0, 0.0, -3.0), Vector3(14.0, 2.0, 6.0), "soumrak"],
		"12_luk": [Vector3(-14.75, 0.0, 11.2), Vector3(-14.7, 1.3, -4.0), "poledne"],
	}
	for key: String in V:
		if not all and not views.has(key.substr(0, 2)):
			continue
		var v: Array = V[key]
		if day.current != v[2]:
			day.set_time(v[2], 0.01)
		var feet: Vector3 = v[0]
		if feet.y < -50.0:
			feet.y = main.terrain.height(feet.x, feet.z) + 0.05
		_view(feet, v[1])
		if key == "12_luk":
			main.bow.equip(true)
			main.bow.begin_draw()
		elif main.bow.equipped:
			main.bow.equip(false)
		main.hud._place_t = 3.0
		await _shot(key, 50 if key != "01_prichod" else 90)
		if key == "12_luk":
			main.bow.release()
			main.bow.equip(false)


## TVRZ_PROBE="x,y,z,smer_x,smer_z,sekundy;..." - pusti hrace danym smerem a vypisuje, co se deje.
func _probe() -> void:
	if OS.has_environment("TVRZ_INSPECT"):
		var v := OS.get_environment("TVRZ_INSPECT").split(",")
		var q := PhysicsPointQueryParameters3D.new()
		q.position = Vector3(float(v[0]), float(v[1]), float(v[2]))
		for r: Dictionary in player.get_world_3d().direct_space_state.intersect_point(q, 32):
			var body: Node = r["collider"]
			var owner_id: int = body.shape_find_owner(r["shape"])
			var cs: Node3D = body.shape_owner_get_owner(owner_id)
			var sh: Shape3D = body.shape_owner_get_shape(owner_id, 0)
			print("  v bode je: ", body.get_path(), " tvar ", sh, " ", (sh as BoxShape3D).size if sh is BoxShape3D else "", " xf ", cs.global_transform)
		return
	for spec: String in OS.get_environment("TVRZ_PROBE").split(";", false):
		var v := spec.split(",")
		var pos := Vector3(float(v[0]), float(v[1]), float(v[2]))
		var dir := Vector2(float(v[3]), float(v[4])).normalized()
		var secs := float(v[5])
		player.global_position = pos
		player.velocity = Vector3.ZERO
		player.yaw = atan2(-dir.x, -dir.y)
		player.move_input = Vector2.ZERO
		await _frames(20)
		print("probe od ", player.global_position, " smer ", dir)
		player.move_input = Vector2(0, 0.7)
		var t := 0.0
		var seen := {}
		while t < secs:
			await get_tree().physics_frame
			t += 1.0 / 60.0
			for k in player.get_slide_collision_count():
				var c := player.get_slide_collision(k)
				var n: Node = c.get_collider() as Node
				var key := "%s n=%s" % [str(n.get_path()) if n else "?", c.get_normal().snapped(Vector3(0.1, 0.1, 0.1))]
				if not seen.has(key) and c.get_normal().y < 0.7:
					seen[key] = true
					print("   t=%.2f pos=%s naraz: %s v %s" % [t, player.global_position.snapped(Vector3(0.01, 0.01, 0.01)), key, c.get_position().snapped(Vector3(0.01, 0.01, 0.01))])
			if int(t * 60) % 30 == 0:
				print("   t=%.1f pos=%s floor=%s" % [t, player.global_position.snapped(Vector3(0.01, 0.01, 0.01)), player.is_on_floor()])
		player.move_input = Vector2.ZERO


func _joy_axis(axis: JoyAxis, v: float) -> void:
	var e := InputEventJoypadMotion.new()
	e.device = 0
	e.axis = axis
	e.axis_value = v
	Input.parse_input_event(e)


func _joy_button(b: JoyButton, pressed: bool) -> void:
	var e := InputEventJoypadButton.new()
	e.device = 0
	e.button_index = b
	e.pressed = pressed
	Input.parse_input_event(e)


func _pad_test() -> void:
	print("=== TEST: herni ovladac ===")
	player.place(Vector3(-15.0, 0.1, 11.6), Vector3(-15.6, 1.0, 12.8))
	await _frames(30)
	var p0 := player.global_position
	_joy_axis(JOY_AXIS_LEFT_Y, -1.0)
	await _frames(40)
	_ok(main.hud.gamepad, "ovladac rozpoznan, dotykove prvky skryte")
	_ok(player.global_position.distance_to(p0) > 1.0, "leva packa: posun o %.2f m" % player.global_position.distance_to(p0))
	_joy_axis(JOY_AXIS_LEFT_Y, 0.0)
	await _frames(10)
	_ok(player.move_input == Vector2.ZERO, "pusteni packy zastavi")
	var y0: float = player.yaw
	_joy_axis(JOY_AXIS_RIGHT_X, 1.0)
	await _frames(30)
	_joy_axis(JOY_AXIS_RIGHT_X, 0.0)
	_ok(player.yaw < y0 - 0.5, "prava packa otaci vpravo (%.2f rad)" % (player.yaw - y0))
	_joy_button(JOY_BUTTON_A, true)
	_joy_button(JOY_BUTTON_A, false)
	await _frames(8)
	_ok(not player.is_on_floor() or player.velocity.y > 0.5, "A: skok (vy=%.2f)" % player.velocity.y)
	await _frames(60)
	player.place(Vector3(-15.0, 0.1, 11.6), Vector3(-15.6, 1.0, 12.8))
	await _frames(20)
	main._process(0.0)
	_ok(main.hud.use_text == "Vzít luk", "u stojanu nabidka '%s'" % main.hud.use_text)
	_joy_button(JOY_BUTTON_X, true)
	_joy_button(JOY_BUTTON_X, false)
	await _frames(5)
	_ok(main.bow.equipped, "X: luk v ruce")
	_face(main.info["targets"][0]["center"])
	_joy_axis(JOY_AXIS_TRIGGER_RIGHT, 1.0)
	await _frames(60)
	_ok(main.bow.drawing and main.bow.draw > 0.9, "RT drzen: napnuto %.2f" % main.bow.draw)
	_joy_axis(JOY_AXIS_TRIGGER_RIGHT, 0.0)
	await _frames(5)
	_ok(main.bow.shots == 1, "pusteni RT vystreli (vystrelu %d)" % main.bow.shots)
	_joy_button(JOY_BUTTON_START, true)
	_joy_button(JOY_BUTTON_START, false)
	await _frames(5)
	_ok(get_tree().paused, "Start: menu")
	var fo := get_viewport().gui_get_focus_owner()
	_ok(fo != null and fo is Button, "v menu je vybrane tlacitko: %s" % (fo.text if fo else "nic"))
	_joy_button(JOY_BUTTON_B, true)
	_joy_button(JOY_BUTTON_B, false)
	await _frames(5)
	_ok(not get_tree().paused, "B: zpet do hry")
	_touch(0, Vector2(300, 300), true)
	_touch(0, Vector2(300, 300), false)
	await _frames(3)
	_ok(not main.hud.gamepad, "dotyk vrati dotykove ovladani")
	print("=== VYSLEDEK: %s (%d chyb) ===" % ["OK" if fails.is_empty() else "CHYBY", fails.size()])


# ------------------------------------------------------------------ sber bylin a hub

func _sber_test() -> void:
	await _frames(30)
	var sb: Node = main.sber
	print("SBER mist: %d, uroven %d" % [sb.spots.size(), sb.uroven()])
	var druhy := {}
	for s: Dictionary in sb.spots:
		druhy[s["id"]] = int(druhy.get(s["id"], 0)) + 1
	print("SBER druhy: ", druhy)
	# k nekolika mistum kazdeho druhu: postavit hrace, zamerit, utrhnout
	var n := 0
	for i in range(0, sb.spots.size(), maxi(1, sb.spots.size() / 60)):
		var p: Vector3 = (sb.spots[i]["xf"] as Transform3D).origin
		player.set_flying(true)
		player.place(p + Vector3(0.9, 1.6, 0.9), p)
		await _frames(3)
		var u: Dictionary = sb.usable(player.cam)
		if u.is_empty():
			continue
		var title: String = sb.nazev(String(u["id"]))
		sb.pick(u)
		n += 1
		if n % 10 == 1:
			print("SBER %s -> %s, uroven %d, xp %d" % [u["id"], title, sb.uroven(), sb.xp])
	print("SBER utrzeno mist: %d, uroven %d, xp %d" % [n, sb.uroven(), sb.xp])
	print("SBER brasna: ", main.predmety.inv)
	_ok(n > 20 and sb.uroven() > 1, "sber: utrzeno a dovednost roste")
	# dorustani
	var t0: int = sb.trhano.size()
	main.day.day_n += 3
	for k in 3:
		await get_tree().process_frame
	print("SBER po 3 dnech utrzenych %d -> %d (den %d, trhano %s, proces %s)" % [t0, sb.trhano.size(), main.day.day_n, str(sb.trhano.values().slice(0, 3)), sb.is_processing()])
	_ok(sb.trhano.size() < t0, "sber: dorusta")


func _zvuky_test() -> void:
	var r: Node = main.ruchy
	print("ZVUKY les bunek: ", r._les.size(), "  zvuku: ", main.life._sounds.size())
	for m in [["tvrz", Vector3(-4, 0.2, 0)], ["ves", Vector3(470, 0, 830)], ["les", Vector3(-150, 0, 300)], ["louka", Vector3(120, 0, 200)]]:
		var p: Vector3 = m[1]
		p.y = main._ground_hi(p.x, p.z) + 0.2
		player.global_position = p
		for k in 4:
			await get_tree().process_frame
		var hraje := []
		for n: String in r._hraj:
			if (r._hraj[n] as AudioStreamPlayer).playing:
				hraje.append(n)
		print("ZVUKY %s -> zona %s, hraje %s, hudba %s" % [m[0], r.zona, hraje, main._music_zone()])
	for n: String in ["luk_napnout", "kovadlina", "polozit_drevo", "truhla_otevrit", "sednout", "menu_vyber", "ulozeno", "louc_zapalit"]:
		_ok(main.life._sounds.has(main.life.varianta(n)), "zvuk " + n)
	print("ZVUKY kanaly: ", AudioServer.get_bus_index("Hudba"), " ", AudioServer.get_bus_index("Zvuky"), " ruchy bus ", (r._potok as AudioStreamPlayer3D).bus)


## Hostinec: pruchod vsemi dvermi tam i zpet a schody. Souradnice z blender/hostinec.py (Blender x, y modelu,
## stred stavby 1.323, 4.649) -> svet pres uzel Staticky_hostinec.
func _hl(bx: float, by: float, h: float = 0.0) -> Vector3:
	var n: Node3D = main.find_child("Staticky_hostinec", true, false)
	return n.global_transform * Vector3(bx - 1.323, h, -(by - 4.649))


func _hostinec_test() -> void:
	# vsechny dvere hostince otevrit
	for u: Dictionary in main.info["use"]:
		if u.get("kind", "") == "pohyb" and (u["pos"] as Vector3).distance_to(_hl(1.3, 4.6)) < 14.0:
			if OS.has_environment("OTEVRIT"):
				main.pohyb.toggle(u["id"])
				print("DVERE prepnuto ", u["id"], " cil ", main.pohyb.groups[u["id"]]["target"])
	await _frames(120)
	for u: Dictionary in main.info["use"]:
		if (u["pos"] as Vector3).distance_to(_hl(1.3, 4.6)) < 14.0:
			print("POUZITI ", u.get("kind", ""), " ", u.get("label", u.get("name", "")), " ", (u["pos"] as Vector3).snapped(Vector3(0.1, 0.1, 0.1)))
	for q: Vector2 in [Vector2(0.018, 6.28), Vector2(-0.02, -0.87), Vector2(-1.0, 5.377), Vector2(2.74, 7.862)]:
		print("DVERE model ", q, " -> ", _hl(q.x, q.y, 1.2).snapped(Vector3(0.1, 0.1, 0.1)))
	var trasy := [
		["sklad->kuchyne", Vector2(1.2, 6.28), Vector2(-2.0, 6.28)],
		["kuchyne->sklad", Vector2(-2.0, 6.28), Vector2(1.2, 6.28)],
		["sin->kuchyne", Vector2(-1.0, 3.5), Vector2(-2.6, 7.5)],
		["kuchyne->sin", Vector2(-2.6, 7.5), Vector2(-1.0, 3.5)],
		["vchod->sin", Vector2(1.5, -0.87), Vector2(-1.2, -0.87)],
		["sklad->ven", Vector2(2.7, 6.5), Vector2(2.7, 9.5)],
		["pokoj->pavlac", Vector2(6.07, 1.2), Vector2(6.07, -1.3), 3.1],
	]
	for r: Array in trasy:
		var a: Vector2 = r[1]
		var b: Vector2 = r[2]
		var zz: float = r[3] if r.size() > 3 else 0.3
		var p0 := _hl(a.x, a.y, zz)
		var p1 := _hl(b.x, b.y, zz)
		player.flying = false
		player.place(p0 + Vector3(0, 0.6, 0), p1 + Vector3(0, 1.5, 0))
		await _frames(10)
		player.move_input = Vector2(0, 1)
		var lim := int((p1 - p0).length() / 0.8 * 60.0) + 120
		var posl := player.global_position
		for i in lim:
			await get_tree().physics_frame
			if Vector2(player.global_position.x, player.global_position.z).distance_to(Vector2(p1.x, p1.z)) < 0.4:
				break
			if i % 60 == 59:
				if player.global_position.distance_to(posl) < 0.05:
					for k in player.get_slide_collision_count():
						var sc := player.get_slide_collision(k)
						var co: Object = sc.get_collider()
						print("   klouze o: %s / %s normala %s misto %s" % [co.name if co is Node else co, (co as Node).get_parent().name if co is Node else "",
								sc.get_normal().snapped(Vector3(0.01, 0.01, 0.01)), sc.get_position().snapped(Vector3(0.01, 0.01, 0.01))])
					print("   rychlost %s, na zemi %s" % [player.velocity.snapped(Vector3(0.01, 0.01, 0.01)), player.is_on_floor()])
					var sp2 := player.get_world_3d().direct_space_state
					for dx: float in [0.0, 0.3, 0.6]:
						var o2 := player.global_position + ((p1 - player.global_position) * Vector3(1, 0, 1)).normalized() * dx
						var ex: Array[RID] = [player.get_rid()]
						for k in 4:
							var q2 := PhysicsRayQueryParameters3D.create(o2 + Vector3(0, 1.0, 0), o2 + Vector3(0, -1.0, 0))
							q2.exclude = ex
							var h2 := sp2.intersect_ray(q2)
							if h2.is_empty():
								break
							print("     dolu +%.1f m: %s y %.3f n %s" % [dx, (h2["collider"] as Node).name, (h2["position"] as Vector3).y, (h2["normal"] as Vector3).snapped(Vector3(0.01, 0.01, 0.01))])
							ex.append(h2["rid"])
					var pos0 := player.global_position
					for k in 5:
						await get_tree().physics_frame
						print("     snimek: %s pauza %s seated %s flying %s proc %s" % [player.global_position.snapped(Vector3(0.001, 0.001, 0.001)), get_tree().paused, player.seated, player.flying, player.is_physics_processing()])
					break                       # stoji celou sekundu: zasekl se
				posl = player.global_position
		player.move_input = Vector2.ZERO
		var zb := Vector2(player.global_position.x, player.global_position.z).distance_to(Vector2(p1.x, p1.z))
		print("HOSTINEC %s: zbyva %.2f m %s, stoji %s" % [r[0], zb, "OK" if zb < 0.6 else "ZASEKL", player.global_position.snapped(Vector3(0.1, 0.1, 0.1))])
		var kol := player.move_and_collide((p1 - player.global_position) * Vector3(1, 0, 1).normalized() * 0.0 + ((p1 - player.global_position) * Vector3(1, 0, 1)).normalized() * 0.3, true)
		if kol:
			var cc: Object = kol.get_collider()
			print("   kapsle narazi: %s / %s, misto %s, normala %s" % [cc.name if cc is Node else cc, (cc as Node).get_parent().name if cc is Node else "",
					kol.get_position().snapped(Vector3(0.01, 0.01, 0.01)), kol.get_normal().snapped(Vector3(0.01, 0.01, 0.01))])
		var sp := player.get_world_3d().direct_space_state
		var smer := (p1 - player.global_position)
		smer.y = 0.0
		smer = smer.normalized()
		for hh: float in [0.15, 0.4, 1.0, 1.6]:
			for bok: float in [-0.3, 0.0, 0.3]:
				var o := player.global_position + Vector3(0, hh, 0) + smer.cross(Vector3.UP) * bok
				var q := PhysicsRayQueryParameters3D.create(o, o + smer * 0.8)
				q.exclude = [player.get_rid()]
				var hit := sp.intersect_ray(q)
				if not hit.is_empty():
					var c: Object = hit["collider"]
					print("   naraz v %.2f bok %.1f: %s (%s) %.2f m" % [hh, bok, c.name if c is Node else c, (c as Node).get_parent().name if c is Node else "", o.distance_to(hit["position"])])
		if OS.has_environment("TVRZ_OUT"):
			await _frames(5)
			get_viewport().get_texture().get_image().save_png(OS.get_environment("TVRZ_OUT") + "/h_%s.png" % String(r[0]).replace(">", ""))
	# schody (souradnice modelu x, z): 1. rameno x 7.0 z -0.5 -> -3.6 (podesta y 1.3), 2. rameno x 5.0 z -2.6 -> -0.5
	# (y 2.65), chodba patra z -0.45 smerem -x
	var useky := [[Vector2(7.0, 0.4), Vector2(7.0, -3.4)], [Vector2(7.0, -3.4), Vector2(5.0, -3.4)], [Vector2(5.0, -3.4), Vector2(5.0, -0.45)], [Vector2(5.0, -0.45), Vector2(0.0, -0.45)]]
	player.flying = false
	var s0: Vector2 = useky[0][0]
	player.place(_hl(s0.x + 1.323, 4.649 - s0.y, 0.9), _hl(7.0 + 1.323, 4.649 + 3.6, 1.5))
	await _frames(10)
	for u: Array in useky:
		var a: Vector2 = u[0]
		var b: Vector2 = u[1]
		var cil := _hl(b.x + 1.323, 4.649 - b.y, 0.0)
		player.look_at_point(cil + Vector3(0, player.global_position.y - cil.y + 1.5, 0)) if player.has_method("look_at_point") else player.place(player.global_position, cil + Vector3(0, player.global_position.y - cil.y + 1.5, 0))
		await _frames(3)
		player.move_input = Vector2(0, 1)
		var posl := player.global_position
		for i in 600:
			await get_tree().physics_frame
			if Vector2(player.global_position.x, player.global_position.z).distance_to(Vector2(cil.x, cil.z)) < 0.35:
				break
			if i % 60 == 59:
				if player.global_position.distance_to(posl) < 0.05:
					break
				posl = player.global_position
		player.move_input = Vector2.ZERO
		var zb := Vector2(player.global_position.x, player.global_position.z).distance_to(Vector2(cil.x, cil.z))
		print("HOSTINEC schody usek %s->%s: zbyva %.2f m, vyska nad prizemim %.2f %s" % [a, b, zb, player.global_position.y - _hl(0, 0, 0).y, "OK" if zb < 0.6 else "ZASEKL"])
		if zb >= 0.6:
			for kk in player.get_slide_collision_count():
				var sc := player.get_slide_collision(kk)
				print("   o: %s normala %s y %.2f" % [(sc.get_collider() as Node).name, sc.get_normal().snapped(Vector3(0.01, 0.01, 0.01)), sc.get_position().y - _hl(0, 0, 0).y])
			break


## Pruchody mezi skalami: stred mezi dvema blizkymi vezemi (6-12 m), shora volny az na teren -> kapsle hrace
## 1 m nad terenem nesmi narazit (konvexni obal tam delal neviditelne steny).
func _pruchod_test() -> void:
	await _frames(5)
	var data: Dictionary = main.svet.data
	var pts: Array[Vector2] = []
	for k: String in data["rostliny"]:
		if k.begins_with("skala_") and not k.contains("_daleko"):
			for t: Array in data["rostliny"][k]:
				pts.append(Vector2(t[3], t[11]))
	var space := player.get_world_3d().direct_space_state
	var cap := CapsuleShape3D.new()
	cap.radius = 0.35
	cap.height = 1.6
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = cap
	var volne := 0
	var zablok := 0
	for i in pts.size():
		for j in range(i + 1, pts.size()):
			var d := pts[i].distance_to(pts[j])
			if d < 6.0 or d > 12.0:
				continue
			var m := (pts[i] + pts[j]) * 0.5
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(m.x, 300, m.y), Vector3(m.x, -100, m.y)))
			if h.is_empty() or not String((h["collider"] as Node).name).begins_with("Teren"):
				continue                 # stred je pod skalou (viditelne zavreno)
			q.transform = Transform3D(Basis(), (h["position"] as Vector3) + Vector3(0, 1.15, 0))
			var hit := space.intersect_shape(q, 1)
			if hit.is_empty():
				volne += 1
			else:
				zablok += 1
				var co: Node = hit[0]["collider"]
				var sh: Node = co.shape_owner_get_owner(co.shape_find_owner(hit[0]["shape"])) if co is CollisionObject3D else co
				if zablok <= 12:
					print("  blok ", m, " ", co.name, " / ", sh.name, " ", (sh as Node3D).global_position if sh is Node3D else "")
	print("PRUCHOD volnych %d, zablokovanych %d" % [volne, zablok])
