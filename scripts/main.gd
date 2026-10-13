extends Node3D
## Odkaz Havrana: intro, hlavni menu, ukladani a hra (Příběh / Pískoviště).
## Svet je vymodelovany v Blenderu (blender/export_game.py) a nacita ho svet.gd.

const Svet := preload("res://scripts/svet.gd")
const Daylight := preload("res://scripts/daylight.gd")
const Player := preload("res://scripts/player.gd")
const Life := preload("res://scripts/life.gd")
const Hud := preload("res://scripts/hud.gd")
const Pad := preload("res://scripts/pad.gd")
const Menu := preload("res://scripts/menu.gd")
const Pohyb := preload("res://scripts/pohyb.gd")
const Data := preload("res://scripts/data.gd")
const Predmety := preload("res://scripts/predmety.gd")
const MenuHrace := preload("res://scripts/menu_hrace.gd")

const QUALITY_NAMES := ["Nízká", "Střední", "Vysoká"]
const SENS := [0.65, 1.0, 1.45]
const SENS_NAMES := ["Nízká", "Normální", "Vysoká"]
const MUSIC_DB := [-80.0, -16.0, -10.0, -5.0]
const MUSIC_NAMES := ["Vypnutá", "Tichá", "Střední", "Hlasitá"]
const SPAWN := Vector3(2.5, 0.0, 40.0)
const SPAWN_LOOK := Vector3(0.0, 4.5, 15.0)
const SAVE_DIR := "user://ulozeni"
const MODE_NAMES := {"pribeh": "Příběh", "piskoviste": "Pískoviště"}

var info := {"rooms": [], "fires": [], "use": [], "smoke": [], "targets": []}
var svet: RefCounted
var world: Node3D
var day: Node
var player: CharacterBody3D
var life: Node3D
var bow: Node3D = null
var hud: CanvasLayer
var pad: Node
var menu: CanvasLayer
var ready_done := false
var mode := ""

var quality := 1
var sens_i := 1
var music_i := 2
var _cfg := ConfigFile.new()
var _use: Dictionary = {}
var pohyb: Node
var predmety: Node
var build_mode := false        # piskoviste: jen umistovat, presouvat a odstranovat predmety
var menu_hrace: CanvasLayer
var _pending_save: Dictionary = {}


func _ready() -> void:
	get_tree().quit_on_go_back = false
	_cfg.load("user://nastaveni.cfg")
	quality = int(_cfg.get_value("hra", "kvalita", 1 if OS.has_feature("mobile") else 2))
	sens_i = int(_cfg.get_value("hra", "citlivost", 1))
	music_i = int(_cfg.get_value("hra", "hudba", 2))
	menu = Menu.new()
	add_child(menu)
	menu.action.connect(_on_menu_action)
	menu.music.volume_db = MUSIC_DB[music_i]
	menu.saves = _list_saves()
	_update_settings_texts()
	if OS.has_environment("TVRZ_SMOKE") or OS.has_environment("TVRZ_WALK") or OS.has_environment("TVRZ_INV_SHOT"):
		_start("piskoviste", {})
		return
	menu.play_intro()
	if OS.has_environment("TVRZ_MENU_SHOT"):
		_menu_shot(OS.get_environment("TVRZ_MENU_SHOT"))


func _menu_shot(path: String) -> void:
	# kontrola rozlozeni menu: snimek hlavni stranky a stranky Hrat
	await get_tree().create_timer(1.0).timeout
	menu._end_intro()
	await get_tree().create_timer(1.2).timeout
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_0.png"))
	menu.show_page("help")
	await get_tree().create_timer(0.3).timeout
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_1.png"))
	get_tree().quit()


# ------------------------------------------------------------------ menu

func _on_menu_action(what: String, arg: Variant) -> void:
	match what:
		"story":
			_start("pribeh", {})
		"sandbox":
			_start("piskoviste", {})
		"continue":
			if not menu.saves.is_empty():
				_load_file(String(menu.saves[0]["file"]))
		"load":
			_load_file(String(arg))
		"resume":
			_pause(false)
		"save":
			if ready_done:
				_save_game()
				hud.toast("Hra uložena", 1.6)
				menu.saves = _list_saves()
				menu.show_page("main")
		"save_quit":
			if ready_done:
				_save_game()
			_save_cfg()
			get_tree().quit()
		"set:quality":
			quality = (quality + 1) % 3
			if ready_done:
				apply_quality()
			_save_cfg()
		"set:sens":
			sens_i = (sens_i + 1) % 3
			if hud:
				hud.sens = SENS[sens_i]
			_save_cfg()
		"set:music":
			music_i = (music_i + 1) % MUSIC_DB.size()
			menu.music.volume_db = MUSIC_DB[music_i]
			if music_i == 0:
				menu.music.stop()
			elif not menu.music.playing:
				menu.music.play()
			_save_cfg()
		"set:time":
			if day:
				day.set_time(day.next_key(), 2.0)
	_update_settings_texts()


func _update_settings_texts() -> void:
	var t := {
		"quality": "Grafika: %s" % QUALITY_NAMES[quality],
		"sens": "Citlivost otáčení: %s" % SENS_NAMES[sens_i],
		"music": "Hudba: %s" % MUSIC_NAMES[music_i],
	}
	if day:
		t["time"] = "Denní doba: %s" % day.NAMES[day.current]
	menu.refresh_settings(t)


func _pause(on: bool) -> void:
	if not ready_done:
		return
	get_tree().paused = on
	if on:
		hud.show_menu(false)
		hud.paused = true
		menu.saves = _list_saves()
		_update_settings_texts()
		menu.show_menu(true, true)
		hud._release_all()
	else:
		menu.hide_menu()
		hud.paused = false


# ------------------------------------------------------------------ start hry

func _start(p_mode: String, save: Dictionary) -> void:
	if ready_done:
		# uz bezi svet: jen presun hrace a rezim
		mode = p_mode
		_apply_mode()
		_apply_save(save)
		_pause(false)
		return
	mode = p_mode
	_pending_save = save
	menu.hide_menu()
	var tw := create_tween()
	tw.tween_property(menu.music, "volume_db", -40.0, 3.0)
	tw.tween_callback(menu.music.stop)
	hud = Hud.new()
	add_child(hud)
	await get_tree().process_frame
	await get_tree().process_frame
	var dl := Data.new()
	add_child(dl)
	dl.status.connect(hud.loading_status)
	var ok: bool = await dl.ensure()
	if not ok:
		return
	hud.loading_status("Načítám tvrz…")
	_build()


func _build() -> void:
	var t0 := Time.get_ticks_msec()
	world = Node3D.new()
	world.name = "Svet"
	add_child(world)
	svet = Svet.new(info)
	svet.build(world, quality)
	pohyb = Pohyb.new()
	pohyb.name = "Pohyb"
	add_child(pohyb)
	pohyb.setup(world.get_node("Tvrz"), svet.data.get("pohyb", []), info)
	predmety = Predmety.new()
	predmety.name = "PredmetyHra"
	add_child(predmety)
	predmety.setup(self, world)
	menu_hrace = MenuHrace.new()
	menu_hrace.main = self
	menu_hrace.P = predmety
	add_child(menu_hrace)
	day = Daylight.new()
	day.name = "Den"
	day.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(day)
	day.setup(String(_cfg.get_value("hra", "cas", "odpoledne")))

	player = Player.new()
	player.name = "Hrac"
	add_child(player)
	player.place(SPAWN + Vector3(0, 30, 0), SPAWN_LOOK)

	life = Life.new()
	life.name = "Zivot"
	add_child(life)
	life.setup(info, day, player)
	player.surface_at = life.surface_at
	player.stepped.connect(life.step_sound)

	hud.player = player
	hud.bow = null
	hud.sens = SENS[sens_i]
	hud.use_pressed.connect(_on_use)
	hud.use2_pressed.connect(_on_use2)
	hud.menu_action.connect(func(w: String) -> void:
		if w == "brasna":
			open_player_menu()
		elif w == "stavba":
			toggle_build()
		else:
			_pause(true))
	pad = Pad.new()
	pad.name = "Ovladac"
	pad.main = self
	add_child(pad)
	apply_quality()
	# hrac stoji na terenu: najdi zem paprskem shora
	await get_tree().physics_frame
	await get_tree().physics_frame
	player.place(_ground(SPAWN), SPAWN_LOOK)
	_apply_mode()
	_apply_save(_pending_save)
	print("build ms: ", Time.get_ticks_msec() - t0, "  fires ", info["fires"].size(), " rooms ", info["rooms"].size(),
			" use ", info["use"].size())
	ready_done = true
	hud.hide_loading()
	if OS.has_environment("TVRZ_INV_SHOT"):
		_inv_shot(OS.get_environment("TVRZ_INV_SHOT"))
	elif OS.has_environment("TVRZ_WALK"):
		_walk_test()
	elif OS.has_environment("TVRZ_SMOKE"):
		_smoke()


func _inv_shot(path: String) -> void:
	# snimky menu hrace: brasna, staveni, vymena s truhlou
	player.place(Vector3(-7.0, 0.1, 11.0), Vector3(-6.6, 0.5, 14.0))
	for i in 40:
		await get_tree().process_frame
	var pages := [["brasna", {}], ["staveni", {}], ["vymena", predmety.placed[0]]]
	for i in pages.size():
		menu_hrace.show_page(pages[i][0], pages[i][1])
		if i == 1:
			menu_hrace.tab = 1
		for k in 6:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(path.replace(".png", "_%d.png" % i))
		menu_hrace.close()
	# pokladani lavice na nadvori a pohled na truhlu ve zbrojnici
	player.place(Vector3(-2.0, 0.1, 2.0), Vector3(-2.0, 0.6, 6.0))
	predmety.begin_place("lavice", false)
	for k in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_3.png"))
	predmety.cancel_place()
	player.place(Vector3(-8.5, 0.1, 11.6), Vector3(-6.6, 0.4, 13.4))
	for k in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_4.png"))
	# noc: louc v drzaku ve zbrojnici a louc v ruce na nadvori
	day.set_time("noc", 0.01)
	predmety.spawn_on_wall("drzak_louce", Vector3(-7.5, 1.95, 12.0), Vector3(0, 0, 1))
	player.place(Vector3(-7.0, 0.1, 10.6), Vector3(-7.5, 1.6, 14.0))
	for k in 30:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_5.png"))
	predmety.hold("lucerna", true)
	player.place(Vector3(-3.0, 0.1, 2.0), Vector3(-3.6, 1.0, -1.6))
	for k in 30:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_6.png"))
	# stit na zed zbrojnice (pokladani na zed) a nabidka spanku
	predmety.hold("", false)
	player.place(Vector3(-7.0, 0.1, 11.2), Vector3(-7.0, 1.4, 14.0))
	predmety.begin_place("stit", false)
	for k in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_7.png"))
	predmety.cancel_place()
	offer_sleep()
	for k in 6:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_8.png"))
	get_tree().quit()


func _walk_test() -> void:
	# automaticka pochuze: kazda trasa = start, smer, ocekavany cil (x/z blizko, vyska)
	var routes := [
		["most", Vector3(0.0, 0.0, 33.0), Vector3(0.0, 1.6, 0.0), 420, Vector3(0.0, 0.0, 12.0), 1.2],
		["schody_dole", Vector3(9.4, 0.0, 5.65), Vector3(-30.0, 1.6, 5.65), 260, Vector3(4.6, 3.25, 5.65), 0.8],
		["schody_hradba", Vector3(4.6, 3.4, 5.5), Vector3(4.6, 4.8, 40.0), 300, Vector3(4.6, 6.5, 12.0), 0.8],
		["vez_1", Vector3(-25.75, 0.6, -10.9), Vector3(-25.75, 1.6, -30.0), 240, Vector3(-25.75, 3.25, -14.6), 0.8],
		["vez_2", Vector3(-24.6, 3.8, -14.75), Vector3(10.0, 5.0, -14.75), 300, Vector3(-21.6, 6.5, -14.75), 0.8],
		["ochoz_brana", Vector3(-8.0, 6.6, 14.65), Vector3(10.0, 8.1, 14.65), 300, Vector3(0.0, 6.5, 14.65), 0.8],
		["kovarna", Vector3(-13.2, 0.0, 4.0), Vector3(-13.2, 1.6, 30.0), 300, Vector3(-13.2, 0.0, 12.5), 0.8],
		["podesta_ochoz", Vector3(4.6, 6.6, 10.2), Vector3(4.6, 8.1, 40.0), 200, Vector3(4.6, 6.5, 14.9), 0.8],
		["ochoz_brana_vychod", Vector3(7.0, 6.6, 14.65), Vector3(-30.0, 8.1, 14.65), 300, Vector3(-8.0, 6.5, 14.65), 0.8],
		["staj", Vector3(-15.0, 0.0, -2.2), Vector3(-40.0, 1.6, -2.2), 300, Vector3(-24.2, 0.0, -2.2), 0.8],
		["palac_pavlac", Vector3(-10.4, 0.0, -6.3), Vector3(10.0, 1.6, -6.3), 360, Vector3(-3.0, 3.9, -6.2), 1.0],
	]
	# dvere mezi kovarnou a zbrojnici otevrit (trasa kovarna_zbrojnice)
	for u: Dictionary in info["use"]:
		if u.get("kind", "") == "pohyb" and (u["pos"] as Vector3).distance_to(Vector3(-11.0, 1.2, 11.55)) < 1.0:
			pohyb.toggle(u["id"])
			print("POHYB dvere kovarna-zbrojnice: ", u["id"])
	routes.append(["kovarna_zbrojnice", Vector3(-14.0, 0.0, 11.55), Vector3(10.0, 1.6, 11.55), 300, Vector3(-8.0, 0.0, 11.55), 0.8])
	for r: Array in routes:
		var start: Vector3 = r[1]
		player.flying = false
		player.place(_ground(start + Vector3(0, 0.5, 0)) if start.y < 0.5 else start, r[2] + Vector3(0, start.y, 0))
		for i in 10:
			await get_tree().physics_frame
		player.move_input = Vector2(0, 1)
		var top := -100.0
		for i in int(r[3]):
			await get_tree().physics_frame
			top = maxf(top, player.global_position.y)
		player.move_input = Vector2.ZERO
		var p := player.global_position
		var goal: Vector3 = r[4]
		print("CHUZE %s: konec %s, max vyska %.2f, cil %s" % [r[0], p.snapped(Vector3(0.01, 0.01, 0.01)), top, goal])
	# predmety: vychozi truhla, vybrat ji, polozit sud z katalogu
	print("PREDMETY polozene: %d, brasna: %s" % [predmety.placed.size(), predmety.inv])
	open_container(predmety.placed[0])
	menu_hrace._take_all()
	print("PREDMETY po vybrani truhly: brasna %s, truhla %s" % [predmety.inv, predmety.placed[0]["obsah"]])
	menu_hrace.close()
	predmety.begin_place("sud", false)
	for i in 3:
		await get_tree().physics_frame
	predmety.confirm_place()
	predmety.cancel_place()
	menu_hrace.close()
	print("PREDMETY po polozeni: %d, menu staveni otevrene zpet: ok" % predmety.placed.size())
	# louce: vzit z drzaku, zhasnout, vratit; sednout na lavici a vstat
	predmety.spawn_on_wall("drzak_louce", Vector3(-7.5, 1.95, 12.0), Vector3(0, 0, 1))
	predmety.spawn({"id": "lavice_hodovni", "p": Vector3(-2.0, 0.0, 3.0), "yaw": 0.0, "obsah": {}})
	var dz: Dictionary = {}
	for r: Dictionary in predmety.placed:
		if r["id"] == "drzak_louce":
			dz = r
			break
	print("LOUCE drzaku: %d" % predmety.placed.filter(func(r: Dictionary) -> bool: return r["id"] == "drzak_louce").size())
	if not dz.is_empty():
		predmety.use({"rec": dz})
		print("LOUCE v ruce %s hori %s, drzak ma louc %s" % [predmety.held_torch, predmety.held_lit, dz["louc"]])
		predmety.use2({})
		print("LOUCE po X hori %s" % predmety.held_lit)
		predmety.use({"rec": dz})
		print("LOUCE vracena %s, v ruce %s" % [dz["louc"], predmety.held_torch])
	for r: Dictionary in predmety.placed:
		if r["id"] == "lavice_hodovni":
			predmety.use({"rec": r})
			print("SEZENI sedi %s" % player.seated)
			player.move_input = Vector2(0, 1)
			await get_tree().physics_frame
			await get_tree().physics_frame
			player.move_input = Vector2.ZERO
			print("SEZENI po pohybu sedi %s" % player.seated)
			break
	# presun truhly a zruseni: truhla se vrati i s obsahem
	predmety.placed[0]["obsah"] = {"miska": 1}
	predmety.begin_move(predmety.placed[0])
	for i in 3:
		await get_tree().physics_frame
	predmety.cancel_place()
	print("PREDMETY po zruseni presunu: %d, obsah %s" % [predmety.placed.size(), predmety.placed[-1]["obsah"]])
	# pokus postavit skrin do zdi zbrojnice
	player.place(Vector3(-6.0, 0.1, 12.6), Vector3(-6.0, 1.6, 20.0))
	predmety.begin_place("skrin", false)
	for i in 4:
		await get_tree().physics_frame
	print("PREDMETY skrin u zdi platna: %s" % predmety._valid)
	predmety.cancel_place()
	# stavebni rezim: presun a odstraneni truhly (obsah do brasny)
	toggle_build()
	var nb: int = predmety.placed.size()
	predmety.delete(predmety.placed[-1])
	print("PREDMETY stavebni rezim %s, odstraneno %d -> %d, brasna misek %d" % [build_mode, nb, predmety.placed.size(), int(predmety.inv.get("miska", 0))])
	toggle_build()
	# mechanismy: zvednout most a spustit mriz, otevrit prvni dvere
	for id: String in ["most", "mriz", "dvere1", "vrata", "studna"]:
		pohyb.toggle(id)
	# dvere veze: hrac u nich musi dostat nabidku
	player.place(Vector3(-18.0, 0.0, -12.8), Vector3(-30.0, 1.6, -12.8))
	await get_tree().physics_frame
	var u: Dictionary = life.usable(player.cam)
	print("POHYB u dveri veze: ", u.get("id", "nic"))
	player.move_input = Vector2(0, 1)
	for i in 200:
		await get_tree().physics_frame
	player.move_input = Vector2.ZERO
	print("POHYB do veze: x=%.2f" % player.global_position.x)
	for i in 500:
		await get_tree().physics_frame
	for id: String in ["most", "mriz", "dvere1", "vrata", "studna"]:
		var g: Dictionary = pohyb.groups[id]
		print("POHYB %s t=%.2f" % [id, g["t"]])
	# zvednuty most: hrac neprojde
	player.place(_ground(Vector3(0.0, 0.5, 23.0)), Vector3(0.0, 1.6, 0.0))
	player.move_input = Vector2(0, 1)
	for i in 240:
		await get_tree().physics_frame
	player.move_input = Vector2.ZERO
	print("POHYB pres zvednuty most: z=%.2f" % player.global_position.z)
	get_tree().quit()


func _smoke() -> void:
	# kontrola bez obrazu: hrac stoji na zemi, chuze a let, ulozeni a nacteni
	var shot := OS.get_environment("TVRZ_SMOKE")
	if shot.ends_with(".png"):
		var views := [[Vector3(-2.5, 0.0, 7.5), Vector3(6, 3.0, -8)], [Vector3(2.2, -1.0, 34.0), Vector3(0, 4.5, 15)],
				[Vector3(9.0, 3.9, -9.5), Vector3(16, 4.6, -13)]]
		for i in views.size():
			player.place(_ground(views[i][0]) if views[i][0].y < 1.0 and i < 2 else views[i][0], views[i][1])
			for k in 8:
				await get_tree().process_frame
			get_viewport().get_texture().get_image().save_png(shot.replace(".png", "_%d.png" % i))
			print("SMOKE snimek ", i)
		get_tree().quit()
		return
	print("SMOKE spawn ", player.global_position, " na zemi ", player.is_on_floor())
	player.move_input = Vector2(0, 1)
	for i in 90:
		await get_tree().physics_frame
	print("SMOKE po chuzi ", player.global_position)
	player.move_input = Vector2.ZERO
	player.jump()
	await get_tree().create_timer(0.1).timeout
	player.jump()
	player.fly_up = true
	for i in 60:
		await get_tree().physics_frame
	print("SMOKE let ", player.flying, " vyska ", player.global_position.y)
	player.fly_up = false
	_save_game()
	print("SMOKE ulozeni ", _list_saves().size())
	get_tree().quit()


func _ground(p: Vector3) -> Vector3:
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, 60.0, p.z), Vector3(p.x, -30.0, p.z))
	if player:
		q.exclude = [player.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit.is_empty():
		return Vector3(p.x, 1.0, p.z)
	return hit["position"] + Vector3(0, 0.05, 0)


func _apply_mode() -> void:
	player.can_fly = mode == "piskoviste"
	if mode != "piskoviste":
		build_mode = false
	hud.can_build = mode == "piskoviste"
	if not player.can_fly:
		player.set_flying(false)


func _process(_delta: float) -> void:
	if not ready_done:
		return
	if predmety.placing != "" or player.seated:
		_use = {}
	elif build_mode:
		_use = predmety.nearest(player.cam)
	else:
		_use = life.usable(player.cam)
	hud.build_mode = build_mode
	hud.use_text2 = "" if build_mode else predmety.use2_label(_use)
	if build_mode:
		hud.use_text = "" if _use.is_empty() else "Přesunout: %s" % predmety.name_of(_use["rec"]["id"])
		hud.use_text2 = "" if _use.is_empty() else "Odstranit"
		return
	if _use.is_empty():
		hud.use_text = predmety.drop_label()
	elif String(_use["kind"]) == "pohyb":
		hud.use_text = pohyb.label(String(_use["id"]))
	elif String(_use["kind"]) == "predmet":
		hud.use_text = predmety.use_label(_use)
	else:
		hud.use_text = life.use_label(_use, false)


# ------------------------------------------------------------------ akce

func _on_use2() -> void:
	# stavebni rezim, X: odstranit predmet; jinak zapalit/zhasnout louc
	if build_mode:
		if not _use.is_empty():
			predmety.delete(_use["rec"])
		return
	predmety.use2(_use)


func toggle_build() -> void:
	if mode != "piskoviste" or not ready_done or get_tree().paused:
		return
	build_mode = not build_mode
	predmety.cancel_place()
	life.sfx("listovat", -6.0)
	hud.toast("Stavební režim" if build_mode else "Stavební režim ukončen", 1.4)


func _on_use() -> void:
	if _use.is_empty():
		if not build_mode and predmety.held_id != "":
			predmety.drop_held()
		return
	if build_mode:
		predmety.begin_move(_use["rec"])
		return
	if String(_use["kind"]) == "pohyb":
		pohyb.toggle(String(_use["id"]))
		return
	if String(_use["kind"]) == "predmet":
		predmety.use(_use)
		return
	life.sfx("click", -8.0)
	match _use["kind"]:
		"bed":
			player.sit(Vector3(_use["pos"]) - Vector3(0, 0.5, 0), 0.62, player.global_position, player.yaw, deg_to_rad(55))
			offer_sleep()
		"fire":
			life.stoke(String(_use.get("name", "krb")))
			hud.toast("Přiložil jsi polínko", 1.4)


# ------------------------------------------------------------------ ukladani

func _list_saves() -> Array:
	var out: Array = []
	var d := DirAccess.open(SAVE_DIR)
	if d == null:
		return out
	for f in d.get_files():
		if not f.ends_with(".json"):
			continue
		var fa := FileAccess.open(SAVE_DIR + "/" + f, FileAccess.READ)
		if fa == null:
			continue
		var j: Variant = JSON.parse_string(fa.get_as_text())
		if typeof(j) != TYPE_DICTIONARY:
			continue
		out.append({"file": SAVE_DIR + "/" + f, "t": int(j.get("unix", 0)),
				"label": "%s – %s" % [MODE_NAMES.get(j.get("mode", ""), "Hra"), String(j.get("kdy", f))]})
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["t"] > b["t"])
	return out


func _save_game() -> void:
	DirAccess.make_dir_recursive_absolute(SAVE_DIR)
	var now := Time.get_unix_time_from_system()
	var dt := Time.get_datetime_dict_from_system()
	var p := player.global_position
	var j := {
		"mode": mode, "unix": int(now),
		"kdy": "%d. %d. %d  %02d:%02d" % [dt["day"], dt["month"], dt["year"], dt["hour"], dt["minute"]],
		"pos": [p.x, p.y, p.z], "yaw": player.yaw, "pitch": player.pitch,
		"cas": day.current, "let": player.flying,
		"predmety": predmety.to_save(),
	}
	var fa := FileAccess.open(SAVE_DIR + "/hra_%d.json" % int(now), FileAccess.WRITE)
	fa.store_string(JSON.stringify(j))
	_save_cfg()


func _load_file(path: String) -> void:
	var fa := FileAccess.open(path, FileAccess.READ)
	if fa == null:
		return
	var j: Variant = JSON.parse_string(fa.get_as_text())
	if typeof(j) != TYPE_DICTIONARY:
		return
	_start(String(j.get("mode", "piskoviste")), j)


func _apply_save(j: Dictionary) -> void:
	if j.has("predmety"):
		predmety.from_save(j["predmety"])
	else:
		_default_items()
	if j.is_empty():
		return
	var a: Array = j["pos"]
	player.global_position = Vector3(a[0], a[1], a[2])
	player.yaw = float(j.get("yaw", 0.0))
	player.pitch = float(j.get("pitch", 0.0))
	player.velocity = Vector3.ZERO
	player.reset_physics_interpolation()
	if player.can_fly and bool(j.get("let", false)):
		player.set_flying(true)
	if j.has("cas"):
		day.set_time(String(j["cas"]), 0.01)


func _default_items() -> void:
	# vychozi vybaveni sveta: truhla ve zbrojnici se zbranemi, sud a vedro v kovarne
	predmety.from_save({})
	if mode == "piskoviste":
		predmety.start_kit()
	predmety.spawn({"id": "truhla", "p": Vector3(-6.6, 0.04, 13.35), "yaw": PI, "obsah": {"sekera_valecna": 1, "kladivo_valecne": 1, "stit": 1}})
	predmety.spawn({"id": "sud", "p": Vector3(-15.4, 0.02, 13.2), "yaw": 0.0, "obsah": {}})
	predmety.spawn({"id": "vedro", "p": Vector3(-16.2, 0.02, 12.9), "yaw": 0.6, "obsah": {}})



func offer_sleep() -> void:
	menu_hrace.show_page("spanek")


func sleep_until(key: String) -> void:
	# prespani: zatmeni, posun denni doby, vstat z postele a ulozit hru
	hud.fade_through(func() -> void:
		day.set_time(key, 0.01)
		player.stand_up()
		life.sfx("chime", -6.0)
		_save_game()
		menu.saves = _list_saves())
	await get_tree().create_timer(1.6).timeout
	hud.toast("Hra uložena", 2.5)


func open_container(rec: Dictionary) -> void:
	menu_hrace.show_page("vymena", rec)


func open_player_menu() -> void:
	if ready_done and not get_tree().paused and predmety.placing == "":
		menu_hrace.show_page("staveni" if build_mode else "brasna")


func _save_cfg() -> void:
	_cfg.set_value("hra", "kvalita", quality)
	_cfg.set_value("hra", "citlivost", sens_i)
	_cfg.set_value("hra", "hudba", music_i)
	if day:
		_cfg.set_value("hra", "cas", day.current)
	_cfg.save("user://nastaveni.cfg")


func _notification(what: int) -> void:
	if not ready_done:
		return
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		_pause(not get_tree().paused)
	elif what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		if not get_tree().paused:
			_pause(true)


# ------------------------------------------------------------------ kvalita obrazu

func apply_quality() -> void:
	var vp := get_viewport()
	var mobile := OS.has_feature("mobile")
	var scales := [0.6, 0.75, 0.9] if mobile else [0.7, 0.85, 1.0]
	var sc: float = scales[quality]
	# bilinearni skalovani: FSR na Adrenu delal vodorovne pruhy
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = sc
	var env: Environment = day.env
	env.ssao_enabled = quality >= 2 and not mobile
	env.glow_enabled = quality >= 1
	var sun: DirectionalLight3D = day.sun
	sun.directional_shadow_max_distance = [45.0, 70.0, 110.0][quality]
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if quality < 2 else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	RenderingServer.directional_shadow_atlas_set_size(2048 if quality == 0 else 4096, true)
	life.set_quality(quality)
