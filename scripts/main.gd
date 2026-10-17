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
const Mapa := preload("res://scripts/mapa.gd")

const QUALITY_NAMES := ["Nízká", "Střední", "Vysoká"]
const SENS := [0.35, 0.5, 0.7, 1.0, 1.25, 1.5, 1.8]
const SENS_NAMES := ["Velmi nízká", "Nízká", "Mírná", "Normální", "Vyšší", "Vysoká", "Velmi vysoká"]
## pohyb packou: exponent krivky (vetsi = vic mista pro pomalou chuzi, beh az na doraz)
const POHYB := [2.2, 1.6, 1.0]
const POHYB_NAMES := ["Jemný", "Střední", "Přímý"]
const HUDBA_DB := -6.0            # hudba pod ruchy a zvuky; hlasitost ridi kanal "Hudba" (nastaveni)
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
var voda: Node
var bow: Node3D = null
var hud: CanvasLayer
var pad: Node
var menu: CanvasLayer
var ready_done := false
var mode := ""
var objevena: Array = []         # pribeh: objevena mista (ruiny) - na mape a k rychlemu cestovani

var quality := 1
var sens_i := 3
var pohyb_i := 1
var hudba_on := true
var mereni_on := false
var diag: Node            # panel s FPS, kreslenim, trojuhelniky a pameti (nastaveni)
var hudba_vol := 0.7
var zvuky_on := true
var zvuky_vol := 1.0
var _cfg := ConfigFile.new()
var _use: Dictionary = {}
var pohyb: Node
var predmety: Node
var build_mode := false        # piskoviste: jen umistovat, presouvat a odstranovat predmety
var menu_hrace: CanvasLayer
var mapa: CanvasLayer
var ruchy: Node                    # zvuky prostredi podle mista, potok, rybnik, zvirata
var sber: Node                     # sber bylin a hub, dovednost bylinkarstvi
var _pending_save: Dictionary = {}
var _hudba: AudioStreamPlayer          # dobovy podkres uvnitr hradeb (Kevin MacLeod, CC BY 4.0)
var _hudba_i := -1
var _uvnitr := false
var _hudba_tw: Tween


func _ready() -> void:
	get_tree().quit_on_go_back = false
	# Vulkan na Adreno 8xx: MSAA 2x hned od startu (uz v menu), jinak vodorovne pruhy
	if RenderingServer.get_rendering_device() != null:
		get_viewport().msaa_3d = Viewport.MSAA_2X
	# hlidac vykonu a zprava o padu (user://diag.log) bezi od startu aplikace, i behem nacitani sveta
	diag = preload("res://scripts/diag.gd").new()
	diag.name = "Diag"
	add_child(diag)
	diag.setup(self)
	_cfg.load("user://nastaveni.cfg")
	quality = int(_cfg.get_value("hra", "kvalita", 1 if OS.has_feature("mobile") else 2))
	if OS.has_environment("TVRZ_MERENI"):
		quality = 1                      # mereni rozpoctu se stejnou kvalitou jako tablet
	sens_i = clampi(int(_cfg.get_value("hra", "citlivost2", [1, 3, 5][clampi(int(_cfg.get_value("hra", "citlivost", 1)), 0, 2)])), 0, SENS.size() - 1)
	pohyb_i = clampi(int(_cfg.get_value("hra", "pohyb", 1)), 0, POHYB.size() - 1)
	var stara := int(_cfg.get_value("hra", "hudba", 2))          # starsi nastaveni: 0 vypnuto, 1-3 hlasitost
	hudba_on = bool(_cfg.get_value("zvuk", "hudba_on", stara != 0))
	hudba_vol = float(_cfg.get_value("zvuk", "hudba_vol", [0.7, 0.35, 0.6, 0.9][clampi(stara, 0, 3)]))
	zvuky_on = bool(_cfg.get_value("zvuk", "zvuky_on", true))
	mereni_on = bool(_cfg.get_value("hra", "mereni", false))
	zvuky_vol = float(_cfg.get_value("zvuk", "zvuky_vol", 1.0))
	_audio_buses()
	menu = Menu.new()
	add_child(menu)
	menu.action.connect(_on_menu_action)
	menu.music.bus = "Hudba"
	menu.music.volume_db = HUDBA_DB
	menu.saves = _list_saves()
	_update_settings_texts()
	if OS.has_environment("TVRZ_SMOKE") or OS.has_environment("TVRZ_WALK") or OS.has_environment("TVRZ_INV_SHOT") or OS.has_environment("TVRZ_SAVETEST") or OS.has_environment("TVRZ_TALIR") or OS.has_environment("TVRZ_LOUC") or OS.has_environment("TVRZ_POHLED") or OS.has_environment("TVRZ_MERENI") or OS.has_environment("TVRZ_DALKA") or OS.has_environment("TVRZ_MAPA") or OS.has_environment("TVRZ_TEST"):
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
				# ulozit, zavrit nabidku a potvrdit ve hre (za nabidkou by hlaska nebyla videt)
				_save_game()
				menu.saves = _list_saves()
				_pause(false)
				life.sfx("ulozeno", -6.0)
				hud.toast("Hra uložena", 2.2)
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
			sens_i = (sens_i + 1) % SENS.size()
			if hud:
				hud.sens = SENS[sens_i]
			_save_cfg()
		"set:pohyb":
			pohyb_i = (pohyb_i + 1) % POHYB.size()
			if player:
				player.move_curve = POHYB[pohyb_i]
			_save_cfg()
		"set:music":
			hudba_on = not hudba_on
			apply_audio()
			if not hudba_on:
				menu.music.stop()
			elif not menu.music.playing and not ready_done:
				menu.music.play()
			_save_cfg()
		"set:mereni":
			mereni_on = not mereni_on
			_save_cfg()
		"set:zvuky":
			zvuky_on = not zvuky_on
			apply_audio()
			_save_cfg()
		"vol:hudba", "vol:zvuky":
			# posuvnik: jen hlasitost kanalu, stranka nastaveni se nepřekresluje (tah by se prerusil)
			if what == "vol:hudba":
				hudba_vol = float(arg)
			else:
				zvuky_vol = float(arg)
			apply_audio()
			_save_cfg()
			return
		"set:time":
			if day:
				day.set_time(day.next_key(), 2.0)
	_update_settings_texts()


func _update_settings_texts() -> void:
	var t := {
		"quality": "Grafika: %s" % QUALITY_NAMES[quality],
		"sens": "Citlivost otáčení: %s" % SENS_NAMES[sens_i],
		"pohyb": "Pohyb páčkou: %s" % POHYB_NAMES[pohyb_i],
		"music": "Hudba: %s" % ("zapnutá" if hudba_on else "vypnutá"),
		"zvuky": "Zvuky: %s" % ("zapnuté" if zvuky_on else "vypnuté"),
		"mereni": "Měření výkonu: %s" % ("zapnuté" if mereni_on else "vypnuté"),
		"vol:hudba": hudba_vol,
		"vol:zvuky": zvuky_vol,
	}
	if day:
		t["time"] = "Denní doba: %s (%s)" % [day.NAMES[day.current], day.clock_text()]
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
	diag.faze("data stazena, stavim svet")
	_build()


func _build() -> void:
	var t0 := Time.get_ticks_msec()
	world = Node3D.new()
	world.name = "Svet"
	add_child(world)
	svet = Svet.new(info)
	svet.build(world, quality)
	diag.faze("svet postaven (modely, rostliny, kolize)")
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
	mapa = Mapa.new()
	mapa.main = self
	add_child(mapa)
	day = Daylight.new()
	day.name = "Den"
	day.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(day)
	day.time_changed.connect(predmety.on_time)
	day.setup(String(_cfg.get_value("hra", "cas", "odpoledne")))
	# vyskova mlha (rano v nivach) jen nad nejnizsim mistem terenu: pevna hranice -6 m lezela nad celym udolim
	# (ves, louky -8 az -21 m), krajina pak stala cela v huste mlze a byla vybledla az bila
	var dno := 0.0
	for n in world.find_children("Teren*", "MeshInstance3D", true, false):
		dno = minf(dno, (n as MeshInstance3D).get_aabb().position.y)
	day.env.fog_height = dno + 4.0

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
	# louka v cele krajine (trsy ze stebel, byliny, kvety) misto starych karet travy
	var louka: Node3D = preload("res://scripts/louka.gd").new()
	louka.name = "Louka"
	add_child(louka)
	louka.setup(self)
	diag.faze("louka")
	voda = preload("res://scripts/voda.gd").new()
	voda.name = "Voda"
	add_child(voda)
	voda.setup(self)
	ruchy = preload("res://scripts/ruchy.gd").new()
	ruchy.name = "Ruchy"
	add_child(ruchy)
	ruchy.setup(self)
	sber = preload("res://scripts/sber.gd").new()
	sber.name = "Sber"
	add_child(sber)
	sber.setup(self)

	hud.player = player
	hud.bow = null
	hud.sens = SENS[sens_i]
	player.move_curve = POHYB[pohyb_i]
	hud.use_pressed.connect(func() -> void: do_act())
	hud.use2_pressed.connect(_on_use2)
	hud.act_pressed.connect(func(i: int) -> void: do_act(i))
	hud.menu_action.connect(func(w: String) -> void:
		if w == "brasna":
			open_player_menu()
		elif w == "stavba":
			toggle_build()
		elif w == "mapa":
			open_map()
		else:
			_pause(true))
	pad = Pad.new()
	pad.name = "Ovladac"
	pad.main = self
	add_child(pad)
	apply_quality()
	diag.faze("kvalita nastavena, prvni snimky")
	# hrac stoji na terenu: najdi zem paprskem shora
	await get_tree().physics_frame
	await get_tree().physics_frame
	player.place(_ground(SPAWN), SPAWN_LOOK)
	_apply_mode()
	_apply_save(_pending_save)
	print("build ms: ", Time.get_ticks_msec() - t0, "  fires ", info["fires"].size(), " rooms ", info["rooms"].size(),
			" use ", info["use"].size())
	ready_done = true
	diag.faze("hra bezi")
	hud.hide_loading()
	if OS.has_environment("TVRZ_INV_SHOT"):
		_inv_shot(OS.get_environment("TVRZ_INV_SHOT"))
	elif OS.has_environment("TVRZ_DALKA"):
		for p: Vector3 in [Vector3(-12, 0, 600), Vector3(470, 0, 830), Vector3(-170, 0, 450)]:
			player.place(Vector3(p.x, _ground_hi(p.x, p.z) + 0.5, p.z), Vector3(p.x, 0, p.z + 10))
			for i in 60:
				await get_tree().physics_frame
			print("DALKA cil %s -> %s" % [p, player.global_position])
		get_tree().quit()
	elif OS.has_environment("TVRZ_MERENI"):
		await _mereni(OS.get_environment("TVRZ_MERENI"))
		get_tree().quit()
	elif OS.has_environment("TVRZ_POHLED"):
		await _pohled_shot(OS.get_environment("TVRZ_POHLED"))
		get_tree().quit()
	elif OS.has_environment("TVRZ_MAPA"):
		# snimek mapy, dotaz na rychle cestovani do Lhoty, cesta, snimek po prichodu
		var out := OS.get_environment("TVRZ_MAPA")
		for i in 30:
			await get_tree().process_frame
		open_map()
		await get_tree().create_timer(0.5).timeout
		get_viewport().get_texture().get_image().save_png(out + "_mapa.png")
		mapa.sel = 1
		mapa._ask()
		mapa._c.queue_redraw()
		await get_tree().create_timer(0.4).timeout
		get_viewport().get_texture().get_image().save_png(out + "_dotaz.png")
		var h0: float = day.hour
		mapa._answer(true)
		await get_tree().create_timer(4.0).timeout
		print("MAPA cesta: hrac %s, cas %.2f -> %.2f" % [player.global_position, h0, day.hour])
		get_viewport().get_texture().get_image().save_png(out + "_lhota.png")
		get_tree().quit()
	elif OS.has_environment("TVRZ_LOUC"):
		await _louc_shot(OS.get_environment("TVRZ_LOUC"))
		get_tree().quit()
	elif OS.has_environment("TVRZ_TALIR"):
		for i in 5:
			await get_tree().physics_frame
		await _talir_test()
		get_tree().quit()
	elif OS.has_environment("TVRZ_SAVETEST"):
		_save_test()
	elif OS.has_environment("TVRZ_WALK"):
		_walk_test()
	elif OS.has_environment("TVRZ_SMOKE"):
		_smoke()
	elif OS.has_environment("TVRZ_TEST"):
		add_child(load("res://scripts/dev_test.gd").new())


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
	menu_hrace.close()
	player.stand_up()
	# sin: krb, vyklenek s oknem, okno do nadvori, svitek s nabidkou u lucerny
	day.set_time("odpoledne", 0.01)
	var shots := [[Vector3(11.8, 0.1, -10.8), Vector3(17.0, 1.7, -10.8)], [Vector3(6.0, 0.1, -12.0), Vector3(6.0, 1.6, -16.0)],
			[Vector3(11.5, 0.1, -9.6), Vector3(11.5, 1.9, -6.0)]]
	for i in shots.size():
		player.place(shots[i][0], shots[i][1])
		for k in 30:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(path.replace(".png", "_%d.png" % (9 + i)))
	predmety.spawn({"id": "lucerna", "p": Vector3(-2.0, 0.0, 3.4), "yaw": 0.0, "obsah": {}, "hori": true})
	player.place(Vector3(-2.0, 0.1, 2.3), Vector3(-2.0, 0.3, 3.4))
	for k in 30:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_12.png"))
	print("SVITEK use %s, akce %s, sedi %s, menu %s" % [_use.get("kind", "nic"), acts, player.seated, menu_hrace.open])
	day.set_time("noc", 0.01)
	player.place(Vector3(11.8, 0.1, -10.8), Vector3(17.0, 1.2, -10.8))
	for k in 30:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_13.png"))
	get_tree().quit()


func _save_test() -> void:
	# ulozit, zmenit svet, nacist pres menu: poloha, predmety, brasna, mechanismy, krb, svetlo v ruce
	for i in 5:
		await get_tree().physics_frame
	player.place(Vector3(-3.0, 0.1, 4.0), Vector3(-3.0, 1.6, -10.0))
	predmety.spawn({"id": "stul_dubovy", "p": Vector3(-2.0, 0.0, 1.0), "yaw": 0.3, "obsah": {}})
	predmety.add_inv("jablko", 3)
	predmety.hold("lucerna", true)
	pohyb.toggle("most")
	life.set_fire("krb", false)
	for i in 400:
		await get_tree().physics_frame
	var before := {"pos": player.global_position.snapped(Vector3(0.01, 0.01, 0.01)), "n": predmety.placed.size(),
			"inv": predmety.inv.duplicate(), "most": pohyb.groups["most"]["target"], "krb": life.fire_on("krb"), "ruka": predmety.held_id}
	_pause(true)
	_on_menu_action("save", null)
	print("ULOZENI souboru %d" % _list_saves().size())
	_pause(false)
	player.place(Vector3(5.0, 0.1, 5.0), Vector3(0, 1.6, 0))
	predmety.delete(predmety.placed[-1])
	predmety.inv = {}
	predmety.hold("", false)
	pohyb.toggle("most")
	life.set_fire("krb", true)
	for i in 30:
		await get_tree().physics_frame
	_pause(true)
	menu.saves = _list_saves()
	_on_menu_action("load", menu.saves[0]["file"])
	for i in 30:
		await get_tree().physics_frame
	var after := {"pos": player.global_position.snapped(Vector3(0.01, 0.01, 0.01)), "n": predmety.placed.size(),
			"inv": predmety.inv.duplicate(), "most": pohyb.groups["most"]["target"], "krb": life.fire_on("krb"), "ruka": predmety.held_id}
	print("ULOZENI pred  ", before)
	print("ULOZENI po    ", after)
	print("ULOZENI pauza %s, menu %s" % [get_tree().paused, menu.visible])
	# hak na zed a stojan se zbranemi, automaticka svetla
	predmety.spawn_on_wall("hak_zbrane", Vector3(-7.0, 1.8, 12.0), Vector3(0, 0, 1), {"obsah": {"stit_rozmberk": 1}})
	predmety.spawn({"id": "stojan_zbrani", "p": Vector3(-8.2, 0.02, 13.2), "yaw": 0.0, "obsah": {"mec_dlouhy": 1, "halapartna": 1, "kopi": 1}})
	predmety.spawn({"id": "stojan_louce", "p": Vector3(-2.0, 0.0, 6.0), "yaw": 0.0, "obsah": {}})
	for r: Dictionary in predmety.placed:
		if r["id"] in ["hak_zbrane", "stojan_zbrani"]:
			print("ZAVESENO %s: %d" % [r["id"], r.get("_hung", []).size()])
		if r["id"] == "stojan_louce":
			day.set_time("poledne", 0.01)
			print("SVETLA stojan v poledne hori %s" % r.get("hori"))
			day.set_time("noc", 0.01)
			print("SVETLA stojan v noci hori %s" % r.get("hori"))
	print("PRIKOP mist s vodou %d" % life._moat_pts.size())
	# postaveni: vidle nastojato
	player.place(Vector3(-2.0, 0.1, 4.0), Vector3(-2.0, 0.3, 1.0))
	predmety.begin_place("vidle", false)
	predmety.toggle_tilt()
	for i in 4:
		await get_tree().physics_frame
	var npos: int = predmety.placed.size()
	predmety.confirm_place()
	menu_hrace.close()
	var vr: Dictionary = predmety.placed[-1]
	print("POSTAVENI vidle orient %s, vyska modelu %.2f, polozeno %d -> %d" % [vr.get("orient"), predmety.dims("vidle", int(vr.get("orient", 0)))[1], npos, predmety.placed.size()])
	# zbran do stojanu: miri na prvni volne misto
	var stj: Dictionary = {}
	for r: Dictionary in predmety.placed:
		if r["id"] == "stojan_zbrani":
			stj = r
	if not stj.is_empty():
		var used: int = predmety._used_slots(stj)
		var sl: Array = predmety.slots("stojan_zbrani")[used]
		var wp: Vector3 = (stj["node"] as Node3D).to_global(Vector3(sl[0], sl[1] + 0.8, sl[2]))
		player.place(wp + (stj["node"] as Node3D).global_transform.basis.z * -1.6 + Vector3(0, -1.5, 0), wp)
		predmety.begin_place("estok", false)
		for i in 4:
			await get_tree().physics_frame
			await get_tree().process_frame
		print("STOJAN cil nalezen %s" % (not predmety._snap.is_empty()))
		predmety.confirm_place()
		menu_hrace.close()
		print("STOJAN zbrani %d -> %d" % [used, predmety._used_slots(stj)])
	await _talir_test()
	predmety.cancel_place()
	if OS.has_environment("TVRZ_SHOT"):
		day.set_time("poledne", 0.01)
		predmety.hold("", false)
		player.place(Vector3(-6.4, 0.1, 10.7), Vector3(-6.4, 1.0, 14.0))
		for i in 30:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(OS.get_environment("TVRZ_SHOT"))
	# truhla ovladacem: otevrit A, presouvat D-padem, A presunout polozku
	var tr: Dictionary = {}
	for r: Dictionary in predmety.placed:
		if predmety.kat[r["id"]].has("kont"):
			tr = r
	tr["obsah"] = {"miska": 2, "lzice": 1}
	open_container(tr)
	_pad_press(JOY_BUTTON_A)
	print("TRUHLA hned po otevreni: truhla %s" % [tr["obsah"]])
	await get_tree().create_timer(0.4).timeout
	_pad_press(JOY_BUTTON_DPAD_DOWN)
	_pad_press(JOY_BUTTON_DPAD_DOWN)
	print("TRUHLA strana %d vyber %s (2 polozky, wrap)" % [menu_hrace.side, menu_hrace.sel])
	_pad_press(JOY_BUTTON_A)
	print("TRUHLA po A: truhla %s" % [tr["obsah"]])
	_pad_press(JOY_BUTTON_DPAD_LEFT)
	_pad_press(JOY_BUTTON_DPAD_UP)
	_pad_press(JOY_BUTTON_A)
	print("TRUHLA vlevo, nahoru (wrap na konec), A: strana %d vyber %s, truhla %s" % [menu_hrace.side, menu_hrace.sel, tr["obsah"]])
	menu_hrace.close()
	get_tree().quit()


func _pad_press(b: JoyButton) -> void:
	for pr in [true, false]:
		var ev := InputEventJoypadButton.new()
		ev.button_index = b
		ev.pressed = pr
		Input.parse_input_event(ev)
		Input.flush_buffered_events()


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
	# krb v sini: zhasnout a znovu zapalit, sezeni ve vyklenku okna
	print("KRB hori %s, lze zapalit %s" % [life.fire_on("krb"), life.can_light("krb")])
	life.set_fire("krb", false)
	print("KRB po zhasnuti hori %s, svetlo %s" % [life.fire_on("krb"), (life.fire_spots["krb"]["light"] as OmniLight3D).visible])
	life.stoke("krb")
	print("KRB po zapaleni hori %s" % life.fire_on("krb"))
	var nsed := 0
	for uu: Dictionary in info["use"]:
		if uu.get("kind", "") == "sed":
			nsed += 1
			if nsed == 1:
				_use = uu
				_on_use()
				print("VYKLENEK sedi %s na %s" % [player.seated, player.global_position.snapped(Vector3(0.01, 0.01, 0.01))])
				player.stand_up()
	print("VYKLENEK sedatek %d" % nsed)
	# lucerna z brasny: do ruky, odlozit (A), znovu vzit, schovat (Y v brasne)
	_use = {}
	predmety.add_inv("lucerna")
	menu_hrace.show_page("brasna")
	menu_hrace.close()
	predmety.hold("lucerna", true)
	predmety.inv["lucerna"] = int(predmety.inv["lucerna"]) - 1
	var np0: int = predmety.placed.size()
	_on_use()
	print("LUCERNA odlozena: v ruce '%s', polozenych %d -> %d" % [predmety.held_id, np0, predmety.placed.size()])
	predmety.use({"rec": predmety.placed[-1]})
	menu_hrace.show_page("brasna")
	menu_hrace._stash()
	menu_hrace.close()
	print("LUCERNA schovana: v ruce '%s', v brasne %d" % [predmety.held_id, int(predmety.inv.get("lucerna", 0))])
	# menu staveni, zalozka Polozene: presun z menu a odstraneni
	menu_hrace.show_page("staveni")
	menu_hrace.tab = menu_hrace.KAT_S.size() - 1
	var npl: int = menu_hrace._items(0).size()
	menu_hrace._remove_sel()
	print("POLOZENE v menu %d, po odstraneni %d" % [npl, menu_hrace._items(0).size()])
	menu_hrace._act()
	for i in 3:
		await get_tree().physics_frame
	predmety.confirm_place()
	print("POLOZENE presun z menu: menu zpet otevrene %s, stranka %s, zalozka %s" % [menu_hrace.open, menu_hrace.page, menu_hrace.KAT_S[menu_hrace.tab][0]])
	menu_hrace.close()
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
	_music_inside()
	if predmety.placing != "" or player.seated:
		_use = {}
	elif build_mode:
		_use = predmety.nearest(player.cam)
	else:
		_use = life.usable(player.cam)
		if _use.is_empty() and sber != null and predmety.held_id == "":
			_use = sber.usable(player.cam)
	hud.build_mode = build_mode
	_build_acts()


# ------------------------------------------------------------------ nabidka akci (svitek u predmetu)

const NAZVY := {"most": "Padací most", "mriz": "Mříž", "vrata": "Vrata", "studna": "Studna", "bed": "Postel", "fire": "Krb",
		"sed": "Výklenek", "bow": "Luk", "anvil": "Kovadlina"}
var acts: Array = []            # [[text, klic]]
var act_sel := 0
var _acts_key := ""


func _build_acts() -> void:
	# podle predmetu na dosah: nazev a mozne akce; potvrzuje se jen A (dotyk na radek)
	var out: Array = []
	var title := ""
	var anchor = null
	if build_mode:
		if not _use.is_empty() and not bool(_use["rec"].get("pevne", false)):
			title = predmety.name_of(_use["rec"]["id"])
			out = [["Přesunout", "use"], ["Otočit", "rot"]]
			if predmety.can_tilt(String(_use["rec"]["id"])):
				out.append(["Postavení", "tilt"])
			if predmety.kat.get(_use["rec"]["id"], {}).get("kat", null) != null:
				out.append(["Vzít do brašny", "take"])
			out.append(["Odstranit", "use2"])
	elif not _use.is_empty():
		var kind := String(_use["kind"])
		var t1 := ""
		if kind == "pohyb":
			t1 = pohyb.label(String(_use["id"]))
			var gid := String(_use["id"])
			title = NAZVY.get(gid, "Dveře" if gid.begins_with("dvere") else "")
		elif kind == "predmet":
			t1 = predmety.use_label(_use)
			title = predmety.name_of(_use["rec"]["id"])
		elif kind == "sber":
			t1 = sber.label(_use)
			title = sber.nazev(String(_use["id"]))
		else:
			t1 = life.use_label(_use, false)
			title = String(_use.get("nazev", NAZVY.get(kind, "")))
		if t1 != "":
			out.append([t1, "use"])
		var t2: String = predmety.use2_label(_use) if predmety.held_id == "" else ""
		if kind == "fire" and predmety.held_id == "":
			var fn := String(_use.get("name", "krb"))
			t2 = "Zhasnout" if life.can_light(fn) and life.fire_on(fn) else ""
		if t2 != "":
			out.append([t2, "use2"])
		var t3: String = predmety.use3_label(_use) if kind == "predmet" else ""
		if t3 != "":
			out.append([t3, "use3"])
		anchor = _use.get("pos")
	if predmety.held_id != "" and not build_mode:
		# svetlo v ruce: vzdy jde zapalit/zhasnout, odlozit a schovat
		if out.is_empty():
			title = predmety.name_of(predmety.held_id)
		out.append(["Zhasnout" if predmety.held_lit else "Zapálit", "held"])
		if _use.is_empty():
			out.append(["Odložit", "drop"])
		out.append(["Schovat do brašny", "stash"])
	var key := title + "|" + "|".join(out.map(func(e: Array) -> String: return e[1]))
	if key != _acts_key:
		_acts_key = key
		act_sel = 0
	acts = out
	act_sel = clampi(act_sel, 0, maxi(0, acts.size() - 1))
	hud.acts = acts.map(func(e: Array) -> String: return e[0])
	hud.act_sel = act_sel
	hud.act_title = title
	hud.act_small = not _use.is_empty() and String(_use.get("kind", "")) == "sber"
	hud.use_text = "" if acts.is_empty() else String(acts[0][0])
	hud.use_text2 = ""
	var sp := Vector2(-1, -1)
	if anchor is Vector3 and not player.cam.is_position_behind(anchor):
		sp = player.cam.unproject_position(anchor)
	hud.act_anchor = sp


func act_cycle(d: int) -> bool:
	# D-pad nahoru/dolu: vyber akce, kdyz je jich vic
	if acts.size() < 2:
		return false
	act_sel = wrapi(act_sel + d, 0, acts.size())
	life.sfx("listovat", -14.0, 1.4)
	return true


func do_act(i := -1) -> void:
	if i < 0:
		i = act_sel
	if i >= acts.size():
		return
	match String(acts[i][1]):
		"use":
			_on_use()
		"use2":
			_on_use2()
		"use3":
			predmety.use3(_use)
		"rot":
			predmety.rotate_placed(_use["rec"], PI / 4)
		"tilt":
			predmety.toggle_tilt_placed(_use["rec"])
		"take":
			predmety.take_placed(_use["rec"])
		"held":
			predmety.hold(predmety.held_id, not predmety.held_lit)
			life.sfx("louc_zapalit" if predmety.held_lit else "louc_zhasnout", -8.0)
		"drop":
			predmety.drop_held()
		"stash":
			predmety.add_inv(predmety.held_id)
			predmety.hold("", false)
			life.sfx("presun", -8.0)


# ------------------------------------------------------------------ hudba v tvrzi

## dobova hudba (zvuky/seznam.txt, hudba/LICENCE.txt): v sence ziva hudba, v noci choral
const HUDBA := {
	"tvrz": ["tvrz_1", "tvrz_2", "tvrz1", "tvrz3", "tvrz4", "tvrz_3"],
	"ves": ["ves_1", "ves_2", "ves_3", "tvrz1"],
	"priroda": ["krajina_1", "krajina_2", "krajina_3"],
	"senk": ["senk_1", "senk_2"],
	"noc": ["noc_1", "noc_2"],
}
var _zona := ""
var _ticho := 0.0              # v prirode mezi skladbami chvili jen zvuky prirody


func _music_zone() -> String:
	var p := player.global_position
	if life and String(life.room_name).begins_with("hostinec_") and (life.room_name.ends_with("senk") or life.room_name.ends_with("sin")):
		return "senk"
	var m := 1.5 if _zona == "tvrz" else -0.5            # hystereze u brany
	if p.x > -25.0 - m and p.x < 17.0 + m and p.z > -14.0 - m and p.z < 14.0 + m and p.y < 14.0:
		return "tvrz"
	if day and day.is_night():
		return "noc"
	var dv := Vector2(p.x - 470.0, p.z - 830.0).length()
	if dv < (150.0 if _zona == "ves" else 135.0):
		return "ves"
	return "priroda"


func _music_inside() -> void:
	# hudba podle mista: v tvrzi dobova hudba, ve vsi vesnicka, v prirode dobrodruzna (s pauzami)
	if not hudba_on:
		if _hudba and _hudba.playing:
			_hudba.stop()
		return
	var z := _music_zone()
	_uvnitr = z == "tvrz"
	if _hudba == null:
		_hudba = AudioStreamPlayer.new()
		_hudba.bus = "Hudba"
		_hudba.process_mode = Node.PROCESS_MODE_ALWAYS
		_hudba.finished.connect(func() -> void: _ticho = randf_range(25.0, 70.0) if _zona in ["priroda", "noc"] else 2.0)
		add_child(_hudba)
	if z != _zona:
		_zona = z
		_ticho = 0.0
		if _hudba_tw:
			_hudba_tw.kill()
		_hudba_tw = create_tween()
		if _hudba.playing:
			_hudba_tw.tween_property(_hudba, "volume_db", -50.0, 3.0)
			_hudba_tw.tween_callback(_hudba.stop)
			_hudba_tw.tween_callback(_next_track)
		else:
			_next_track()
		return
	if not _hudba.playing and (_hudba_tw == null or not _hudba_tw.is_running()):
		_ticho -= get_process_delta_time()
		if _ticho <= 0.0:
			_next_track()


func _next_track() -> void:
	var seznam: Array = HUDBA.get(_zona, HUDBA["tvrz"])
	var n := seznam.size()
	_hudba_i = (_hudba_i + 1 + randi() % maxi(1, n - 1)) % n if _hudba_i >= 0 else randi() % n
	_hudba.stream = load("res://hudba/%s.ogg" % seznam[_hudba_i % n])
	_hudba.volume_db = -40.0
	_hudba.play()
	if _hudba_tw:
		_hudba_tw.kill()
	_hudba_tw = create_tween()
	var cil: float = HUDBA_DB - (3.0 if _zona in ["priroda", "noc"] else 0.0)
	_hudba_tw.tween_property(_hudba, "volume_db", cil, 5.0)


# ------------------------------------------------------------------ akce

func _on_use2() -> void:
	# stavebni rezim, X: odstranit predmet; jinak zapalit/zhasnout louc
	if build_mode:
		if not _use.is_empty():
			predmety.delete(_use["rec"])
		return
	if predmety.held_id == "" and not _use.is_empty() and String(_use["kind"]) == "fire":
		var fn := String(_use.get("name", "krb"))
		if life.can_light(fn) and life.fire_on(fn):
			life.set_fire(fn, false)
		return
	predmety.use2(_use)


func toggle_build() -> void:
	if mode != "piskoviste" or not ready_done or get_tree().paused:
		return
	build_mode = not build_mode
	predmety.cancel_place()
	life.sfx("listovat", -6.0)
	hud.toast("Stavební režim: přesouvání, otáčení a odstraňování" if build_mode else "Stavební režim ukončen", 1.8)


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
	if String(_use["kind"]) == "sber":
		sber.pick(_use)
		return
	life.sfx("click", -8.0)
	match _use["kind"]:
		"sed":
			var sp: Array = _use["sit"]
			player.sit(Vector3(sp[0], sp[1], sp[2]), float(_use.get("h", 0.46)) + 0.78, player.global_position, float(_use.get("yaw", 0.0)))
		"bed":
			player.sit(Vector3(_use["pos"]) - Vector3(0, 0.5, 0), 0.62, player.global_position, player.yaw, deg_to_rad(55))
			offer_sleep()
		"fire":
			var fn := String(_use.get("name", "krb"))
			var was: bool = life.fire_on(fn)
			life.stoke(fn)
			if was:
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
	# vsede ulozit misto, kde se vstava (poloha na sedatku je uvnitr jeho kolize)
	var p: Vector3 = player._stand_p if player.seated else player.global_position
	var j := {
		"mode": mode, "unix": int(now),
		"kdy": "%d. %d. %d  %02d:%02d:%02d" % [dt["day"], dt["month"], dt["year"], dt["hour"], dt["minute"], dt["second"]],
		"pos": [p.x, p.y, p.z], "yaw": player.yaw, "pitch": player.pitch,
		"cas": day.current, "hodina": day.hour, "den": day.day_n, "let": player.flying,
		"predmety": predmety.to_save(),
		"pohyb": pohyb.to_save(), "ohne": life.fires_save(), "objevena": objevena, "sber": sber.to_save(),
	}
	var fa := FileAccess.open(SAVE_DIR + "/hra_%d.json" % int(now), FileAccess.WRITE)
	fa.store_string(JSON.stringify(j))
	fa.close()
	# drzet jen poslednich 20 ulozeni
	var old := _list_saves()
	for k in range(20, old.size()):
		DirAccess.remove_absolute(String(old[k]["file"]))
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
	objevena = Array(j.get("objevena", []))
	if sber != null:
		sber.from_save(j.get("sber", {}))
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
	_volne_misto()
	player.reset_physics_interpolation()
	if player.can_fly and bool(j.get("let", false)):
		player.set_flying(true)
	if j.has("hodina"):
		day.day_n = int(j.get("den", 1))
		day.hour = float(j["hodina"])
		day.set_hour(float(j["hodina"]), 0.01)
	elif j.has("cas"):
		day.set_time(String(j["cas"]), 0.01)
	pohyb.from_save(j.get("pohyb", {}))
	life.fires_load(j.get("ohne", {}))


## Starsi ulozeni (vsede, v predmetu): je-li hrac v kolizi, posunout na nejblizsi volne misto s podlahou.
func _volne_misto() -> void:
	var shape: Shape3D = null
	for c in player.get_children():
		if c is CollisionShape3D:
			shape = (c as CollisionShape3D).shape
			var off := (c as CollisionShape3D).position
			var space := player.get_world_3d().direct_space_state
			var q := PhysicsShapeQueryParameters3D.new()
			q.shape = shape
			q.exclude = [player.get_rid()]
			q.collision_mask = player.collision_mask
			var p0 := player.global_position
			for r in [0.0, 0.4, 0.8, 1.2, 1.7, 2.3, 3.0]:
				var n := 1 if r == 0.0 else 12
				for k in n:
					var a := TAU * k / n
					for dy in [0.05, 0.4]:
						var p := p0 + Vector3(cos(a) * r, dy, sin(a) * r)
						q.transform = Transform3D(Basis(), p + off)
						if not space.intersect_shape(q, 1).is_empty():
							continue
						var down := PhysicsRayQueryParameters3D.create(p + Vector3(0, 0.3, 0), p + Vector3(0, -1.5, 0))
						down.exclude = [player.get_rid()]
						var h := space.intersect_ray(down)
						if h.is_empty() and not player.flying:
							continue
						if r > 0.0:
							print("hrac v kolizi po nacteni: posunut o %.1f m" % r)
							player.global_position = p
						return
			return


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
		life.sfx("spanek", -6.0)
		_save_game()
		menu.saves = _list_saves())
	await get_tree().create_timer(1.6).timeout
	hud.toast("Hra uložena", 2.5)


func open_container(rec: Dictionary) -> void:
	menu_hrace.show_page("vymena", rec)


func open_map() -> void:
	if ready_done and not get_tree().paused and predmety.placing == "" and not player.seated:
		mapa.show_map()


## Rychle cestovani z mapy: zatmit, presunout hrace, posunout herni cas o dobu chuze, rozednit.
func fast_travel(cil: Vector3, pohled: Vector3, hours: float, nazev: String) -> void:
	var cl := CanvasLayer.new()
	cl.layer = 30
	cl.process_mode = Node.PROCESS_MODE_ALWAYS
	var fade := ColorRect.new()
	fade.color = Color(0, 0, 0, 0)
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade.mouse_filter = Control.MOUSE_FILTER_STOP
	cl.add_child(fade)
	add_child(cl)
	get_tree().paused = true
	var tw := create_tween().set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tw.tween_property(fade, "color:a", 1.0, 0.7)
	await tw.finished
	if player.seated:
		player.stand_up()
	if player.flying:
		player.set_flying(false)
	day.set_hour(fmod(day.hour + hours, 24.0), 0.01)
	get_tree().paused = false
	await get_tree().physics_frame
	player.place(Vector3(cil.x, _ground_hi(cil.x, cil.z) + 0.1, cil.z), Vector3(pohled.x, _ground_hi(pohled.x, pohled.z) + 1.6, pohled.z))
	for i in 8:
		await get_tree().physics_frame
	var tw2 := create_tween()
	tw2.tween_property(fade, "color:a", 0.0, 0.9)
	await tw2.finished
	cl.queue_free()
	hud.toast("%s (%s)" % [nazev, day.clock_text()], 2.5)


func open_player_menu() -> void:
	if ready_done and not get_tree().paused and predmety.placing == "":
		menu_hrace.show_page("staveni" if build_mode else "brasna")


## Zvukove kanaly: Hudba a Zvuky (vse ostatni). Kazdy prehravac pridany do sceny s kanalem Master jde do Zvuky.
func _audio_buses() -> void:
	for n: String in ["Hudba", "Zvuky"]:
		if AudioServer.get_bus_index(n) < 0:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, n)
			AudioServer.set_bus_send(i, "Master")
	get_tree().node_added.connect(func(n: Node) -> void:
		if (n is AudioStreamPlayer or n is AudioStreamPlayer3D or n is AudioStreamPlayer2D) and n.get("bus") == &"Master":
			n.set("bus", &"Zvuky"))
	apply_audio()


func apply_audio() -> void:
	var h := AudioServer.get_bus_index("Hudba")
	var z := AudioServer.get_bus_index("Zvuky")
	AudioServer.set_bus_volume_db(h, linear_to_db(maxf(hudba_vol, 0.001)))
	AudioServer.set_bus_mute(h, not hudba_on or hudba_vol <= 0.01)
	AudioServer.set_bus_volume_db(z, linear_to_db(maxf(zvuky_vol, 0.001)))
	AudioServer.set_bus_mute(z, not zvuky_on or zvuky_vol <= 0.01)


func _save_cfg() -> void:
	_cfg.set_value("hra", "kvalita", quality)
	_cfg.set_value("hra", "citlivost2", sens_i)
	_cfg.set_value("hra", "pohyb", pohyb_i)
	_cfg.set_value("zvuk", "hudba_on", hudba_on)
	_cfg.set_value("zvuk", "hudba_vol", hudba_vol)
	_cfg.set_value("zvuk", "zvuky_on", zvuky_on)
	_cfg.set_value("zvuk", "zvuky_vol", zvuky_vol)
	_cfg.set_value("hra", "mereni", mereni_on)
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
	var scales := [0.6, 0.8, 1.0] if mobile else [0.7, 0.85, 1.0]
	var sc: float = scales[quality]
	# bilinearni skalovani: FSR na Adrenu delal vodorovne pruhy
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = sc
	# Vulkan (renderer Mobile) na Adreno 8xx: bez MSAA vodorovne pruhy pres obraz (diagnostika 16. 10.);
	# MSAA 2x je na dlazdicovych GPU skoro zadarmo. Compatibility (OpenGL) beze zmeny.
	if RenderingServer.get_rendering_device() != null:
		vp.msaa_3d = Viewport.MSAA_2X
	var env: Environment = day.env
	env.ssao_enabled = quality >= 2 and not mobile
	env.glow_enabled = quality >= 1
	var sun: DirectionalLight3D = day.sun
	# rozpocet (zadani faze 1): 2 kaskady, stiny do 80 m
	sun.directional_shadow_max_distance = [40.0, 60.0, 80.0][quality]
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	RenderingServer.directional_shadow_atlas_set_size(2048, true)        # rozpocet GPU pameti (4096 = 64 MB)
	life.set_quality(quality)


func _talir_test() -> void:
	# jablko na talir: duch se musi zvednout na horni plochu talire
	predmety.spawn({"id": "talir", "p": Vector3(-4.0, predmety.ground_y(-4.0, 3.0), 3.0), "yaw": 0.0, "obsah": {}})
	player.place(Vector3(-4.0, 0.1, 4.2), Vector3(-4.0, 0.0, 3.0))
	predmety.begin_place("jablko", false)
	predmety._gdist = 1.2
	for i in 6:
		await get_tree().physics_frame
		await get_tree().process_frame
	var tn: Node3D = predmety.placed[-1]["node"]
	print("TALIR jablko y %.3f, dno talire %.3f, vyska talire %.3f" % [predmety._ghost.global_position.y, tn.global_position.y, float(predmety.kat["talir"]["rozmer"][1])])


func _louc_shot(path: String) -> void:
	# noc, louc v ruce: okoli musi byt osvetlene (nadvori plne loucí na stojanech)
	day.set_time("noc", 0.01)
	for i in 10:
		predmety.spawn({"id": "stojan_louce", "p": Vector3(-14.0 + i * 3.0, predmety.ground_y(-14.0 + i * 3.0, 14.0), 14.0), "yaw": 0.0, "obsah": {}})
	predmety.on_time("noc", true)
	player.place(Vector3(-6.4, 0.1, 10.7), Vector3(-6.4, -0.6, 7.0))
	predmety.hold("louc", true)
	for i in 40:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path)
	predmety.hold("", false)
	player.place(Vector3(-6.4, 0.1, 10.7), Vector3(-6.4, 1.2, 14.0))
	for i in 20:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path.replace(".png", "_stojany.png"))


func _pohled_shot(spec: String) -> void:
	# snimky z danych mist: "soubor.png;x,y,z,tx,ty,tz;cas|soubor2.png;..." (y oka nad zemi se dopocita fyzikou)
	player.set_flying(true)
	if OS.has_environment("TVRZ_BEZ_HUD"):
		hud.visible = false
	for one: String in spec.split("|"):
		var parts := one.split(";")
		var absolute := parts[1].begins_with("a")
		var v := parts[1].trim_prefix("a").split_floats(",")
		day.set_hour(float(parts[2]) if parts.size() > 2 else 12.0, 0.01)
		# TVRZ_POHLED_PREDMETY='[{"id":"stojan_louce","p":[x,y,z],"yaw":0}]' - predmety jen pro snimek (y nad zemi)
		if OS.has_environment("TVRZ_POHLED_PREDMETY") and one == spec.split("|")[0]:
			for r: Dictionary in JSON.parse_string(OS.get_environment("TVRZ_POHLED_PREDMETY")):
				var pp: Array = r["p"]
				var yy: float = float(pp[1]) if bool(r.get("abs", false)) else _ground_hi(pp[0], pp[2]) + float(pp[1])
				predmety.spawn({"id": r["id"], "p": Vector3(pp[0], yy, pp[2]), "yaw": float(r.get("yaw", 0.0))})
		# vysky jsou nad zemi (oko i cil)
		var gy: float = 0.0 if absolute else _ground_hi(v[0], v[2])
		var ty: float = 0.0 if absolute else _ground_hi(v[3], v[5])
		player.place(Vector3(v[0], gy + v[1], v[2]), Vector3(v[3], ty + v[4], v[5]))
		for i in 40:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(parts[0])


## Mereni rozpoctu: "nazev;x,z,tx,tz|..." - hrac na zemi, louka dostavena naplno, prumer pres 30 snimku.
func _mereni(spec: String) -> void:
	player.set_flying(true)
	var louka: Node = get_node_or_null("Louka")
	for one: String in spec.split("|"):
		var parts := one.split(";")
		var v := parts[1].split_floats(",")
		player.place(Vector3(v[0], _ground_hi(v[0], v[1]) + 1.7, v[1]), Vector3(v[2], _ground_hi(v[2], v[3]) + 1.2, v[3]))
		for i in 10:
			await get_tree().process_frame
		if louka:
			for i in 4000:
				louka._process(0.0)
		for i in 20:
			await get_tree().process_frame
		var dc := 0.0
		var tr := 0.0
		var ob := 0.0
		for i in 30:
			await get_tree().process_frame
			dc += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
			tr += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
			ob += Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)
		print("MERENI %-18s kresleni %5d  troj %6.2f M  objekty %5d  gpu %4d MB (textury %d, buffery %d)" % [parts[0], dc / 30.0, tr / 30.0 / 1e6, ob / 30.0,
				Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0, Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0,
				Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0])
		if parts.size() > 2:
			get_viewport().get_texture().get_image().save_png(parts[2])
		# rozpad: o kolik ubyde, kdyz se skryje kazda cast sceny (deti hlavni sceny a sveta, Rostliny po druzich)
		var casti: Array = []
		if not OS.has_environment("TVRZ_ROZPAD"):
			continue
		for c in get_children() + world.get_children():
			if c is Node3D and c != world and (c as Node3D).visible:
				casti.append(c)
		var rs: Node = world.get_node_or_null("Rostliny")
		var po_druhu := {}
		if rs:
			for c in rs.get_children():
				var nm := String(c.name)
				var k := nm.left(nm.rfind("_", nm.rfind("_") - 1))
				k = k.left(k.rfind("_")) if k.rfind("_") > 0 and k.right(1).is_valid_int() else k
				if not po_druhu.has(k):
					po_druhu[k] = []
				po_druhu[k].append(c)
		for skup in ["Predmety", "Zivot", "Louka"]:
			var pn: Node = find_child(skup, true, false)
			if pn == null:
				continue
			for c in pn.get_children():
				if not (c is Node3D and (c as Node3D).visible):
					continue
				var k2: String = str(skup) + " " + String(c.name).rstrip("0123456789@_ ").replace("@", "")
				if not po_druhu.has(k2):
					po_druhu[k2] = []
				po_druhu[k2].append(c)
		var vys: Array = []
		for c: Node3D in casti:
			c.visible = false
			for i in 4:
				await get_tree().process_frame
			vys.append([String(c.name), dc / 30.0 - Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
					tr / 30.0 - Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)])
			c.visible = true
		for k: String in po_druhu:
			for c: Node3D in po_druhu[k]:
				c.visible = false
			for i in 3:
				await get_tree().process_frame
			vys.append([k if k.begins_with("Predmety") or k.begins_with("Zivot") or k.begins_with("Louka") else "rostlina " + k, dc / 30.0 - Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
					tr / 30.0 - Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)])
			for c: Node3D in po_druhu[k]:
				c.visible = true
		vys.sort_custom(func(x: Array, y: Array) -> bool: return x[2] + x[1] * 1000.0 > y[2] + y[1] * 1000.0)
		for v2: Array in vys.slice(0, 30):
			if v2[1] > 5 or v2[2] > 50000:
				print("   %-32s kresleni %5d  troj %6.2f M" % [v2[0], v2[1], v2[2] / 1e6])
	# textury pouzite materialy ve scene: 25 nejvetsich (odhad VRAM: 1 B/px + mipmapy)
	var tex := {}
	for n in get_tree().root.find_children("*", "GeometryInstance3D", true, false):
		var gi := n as GeometryInstance3D
		var mats: Array = [gi.material_override]
		var mesh: Mesh = null
		if gi is MeshInstance3D:
			mesh = (gi as MeshInstance3D).mesh
			for i in (gi as MeshInstance3D).get_surface_override_material_count():
				mats.append((gi as MeshInstance3D).get_surface_override_material(i))
		elif gi is MultiMeshInstance3D and (gi as MultiMeshInstance3D).multimesh:
			mesh = (gi as MultiMeshInstance3D).multimesh.mesh
		if mesh:
			for i in mesh.get_surface_count():
				mats.append(mesh.surface_get_material(i))
		for m: Material in mats:
			if m == null:
				continue
			var tt: Array = []
			if m is BaseMaterial3D:
				for prop in ["albedo_texture", "normal_texture", "orm_texture", "roughness_texture", "metallic_texture", "emission_texture", "heightmap_texture"]:
					tt.append(m.get(prop))
			elif m is ShaderMaterial:
				for u: Dictionary in (m as ShaderMaterial).shader.get_shader_uniform_list() if (m as ShaderMaterial).shader else []:
					tt.append((m as ShaderMaterial).get_shader_parameter(u["name"]))
			for t in tt:
				if t is Texture2D:
					tex[(t as Texture2D).get_rid()] = t
	var rad: Array = []
	var celk := 0.0
	for k in tex:
		var t: Texture2D = tex[k]
		var b := t.get_width() * t.get_height() * 1.33
		celk += b
		rad.append([b, t])
	rad.sort_custom(func(x: Array, y: Array) -> bool: return x[0] > y[0])
	print("TEXTURY pouzite: %d, odhad %d MB" % [rad.size(), celk / 1048576])
	for r: Array in rad.slice(0, 25):
		var t: Texture2D = r[1]
		print("   %5.1f MB  %dx%d  %s" % [r[0] / 1048576.0, t.get_width(), t.get_height(), t.resource_path.right(80) if t.resource_path != "" else "(vytvorena za behu)"])


func _ground_hi(x: float, z: float) -> float:
	var q := PhysicsRayQueryParameters3D.create(Vector3(x, 400.0, z), Vector3(x, -200.0, z))
	var h := get_viewport().get_world_3d().direct_space_state.intersect_ray(q)
	return float((h["position"] as Vector3).y) if not h.is_empty() else 0.0
