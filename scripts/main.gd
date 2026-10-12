extends Node3D

const Mats := preload("res://scripts/mats.gd")
const Fort := preload("res://scripts/fort.gd")
const Daylight := preload("res://scripts/daylight.gd")
const Terrain := preload("res://scripts/terrain.gd")
const Flora := preload("res://scripts/flora.gd")
const Props := preload("res://scripts/props.gd")
const Palace := preload("res://scripts/palace.gd")
const Yard := preload("res://scripts/yard.gd")
const Player := preload("res://scripts/player.gd")
const Life := preload("res://scripts/life.gd")
const Bow := preload("res://scripts/bow.gd")
const Hud := preload("res://scripts/hud.gd")
const Pad := preload("res://scripts/pad.gd")

const QUALITY_NAMES := ["Nízká", "Střední", "Vysoká"]
const SENS := [0.65, 1.0, 1.45]
const SENS_NAMES := ["Nízká", "Normální", "Vysoká"]
const SPAWN := Vector3(2.5, 0.0, 40.0)
const SPAWN_LOOK := Vector3(0.0, 4.5, 15.0)

var info := {"rooms": [], "fires": [], "use": [], "smoke": [], "targets": []}
var mats: RefCounted
var props: RefCounted
var world: Node3D
var day: Node
var terrain: RefCounted
var player: CharacterBody3D
var life: Node3D
var bow: Node3D
var hud: CanvasLayer
var pad: Node
var ready_done := false

var quality := 1
var sens_i := 1
var _grass: Array = []
var _cfg := ConfigFile.new()
var _use: Dictionary = {}


func _ready() -> void:
	get_tree().quit_on_go_back = false
	hud = Hud.new()
	add_child(hud)
	# nech vykreslit nacitaci obrazovku, nez se zacne stavet
	await get_tree().process_frame
	await get_tree().process_frame
	_build()


func _build() -> void:
	var t0 := Time.get_ticks_msec()
	mats = Mats.new()
	world = Node3D.new()
	world.name = "Svet"
	add_child(world)
	terrain = Terrain.new(mats.m, info)
	info["terrain"] = terrain
	terrain.build(world)
	props = Props.new(info)
	Fort.new(mats.m, info).build(world)
	Palace.new(mats.m, info, props).build(world)
	Yard.new(mats.m, info, props).build(world)
	Flora.new(mats.m, terrain, info).build(world)
	day = Daylight.new()
	day.name = "Den"
	day.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(day)

	_cfg.load("user://nastaveni.cfg")
	quality = int(_cfg.get_value("hra", "kvalita", 1 if OS.has_feature("mobile") else 2))
	sens_i = int(_cfg.get_value("hra", "citlivost", 1))
	day.setup(String(_cfg.get_value("hra", "cas", "odpoledne")))

	player = Player.new()
	player.name = "Hrac"
	add_child(player)
	var sy: float = terrain.height(SPAWN.x, SPAWN.z) + 0.05
	player.place(Vector3(SPAWN.x, sy, SPAWN.z), SPAWN_LOOK)

	life = Life.new()
	life.name = "Zivot"
	add_child(life)
	life.setup(info, day, player)
	player.surface_at = life.surface_at
	player.stepped.connect(life.step_sound)
	life.place_changed.connect(hud.show_place)

	bow = Bow.new()
	bow.name = "Luk"
	add_child(bow)
	bow.setup(player, life, world, mats.m, props, info["targets"])
	bow.scored.connect(_on_scored)

	hud.player = player
	hud.bow = bow
	hud.sens = SENS[sens_i]
	hud.use_pressed.connect(_on_use)
	hud.menu_action.connect(_on_menu)
	pad = Pad.new()
	pad.name = "Ovladac"
	pad.main = self
	add_child(pad)

	for n in world.find_children("*", "GeometryInstance3D", true, false):
		var g := n as GeometryInstance3D
		if g.visibility_range_end > 0.0 and g.visibility_range_end < 100.0:
			_grass.append(g)
	apply_quality()
	_update_menu_texts()
	print("build ms: ", Time.get_ticks_msec() - t0, "  fires ", info["fires"].size(), " rooms ", info["rooms"].size(),
			" use ", info["use"].size(), " targets ", info["targets"].size())
	ready_done = true
	hud.hide_loading()
	if OS.has_environment("TVRZ_SHOTS"):
		add_child(load("res://scripts/dev_shots.gd").new())
	if OS.has_environment("TVRZ_TEST"):
		add_child(load("res://scripts/dev_test.gd").new())


func _process(_delta: float) -> void:
	if not ready_done:
		return
	_use = life.usable(player.cam)
	hud.use_text = life.use_label(_use, bow.equipped) if not _use.is_empty() else ""


# ------------------------------------------------------------------ akce

func _on_use() -> void:
	if _use.is_empty():
		return
	life.sfx("click", -8.0)
	match _use["kind"]:
		"bow":
			bow.equip(not bow.equipped)
			if bow.equipped:
				hud.toast("Drž RT a pusť. Míř na terče." if hud.gamepad else "Drž červené tlačítko a pusť. Míř na terče.", 3.2)
				_on_scored(-1, bow.total, "")
			else:
				hud.toast("Luk je zpátky na stojanu", 1.6)
		"bed":
			var nxt: String = day.next_key()
			hud.fade_through(func() -> void:
				day.set_time(nxt, 0.01)
				life.sfx("chime", -6.0)
				_save())
			hud.toast("Odpočíváš… (%s)" % day.NAMES[nxt], 3.0)
		"fire":
			life.stoke(String(_use.get("name", "krb")))
			hud.toast("Přiložil jsi polínko", 1.4)
		"anvil":
			life.strike_anvil()


func _on_scored(points: int, total: int, text: String) -> void:
	if text != "":
		hud.toast(text, 1.6)
	hud.set_score_line("Body: %d   ·   Výstřely: %d" % [total, bow.shots])


func _on_menu(what: String) -> void:
	match what:
		"open":
			_pause(true)
		"resume":
			_pause(false)
		"time":
			day.set_time(day.next_key(), 2.0)
			_save()
		"quality":
			quality = (quality + 1) % 3
			apply_quality()
			_save()
		"sens":
			sens_i = (sens_i + 1) % 3
			hud.sens = SENS[sens_i]
			_save()
		"quit":
			_save()
			get_tree().quit()
	_update_menu_texts()


func _pause(on: bool) -> void:
	get_tree().paused = on
	hud.show_menu(on)
	_update_menu_texts()


func _update_menu_texts() -> void:
	hud.set_menu_text("resume", "Pokračovat")
	if day:
		hud.set_menu_text("time", "Denní doba: %s" % day.NAMES[day.current])
	hud.set_menu_text("quality", "Grafika: %s" % QUALITY_NAMES[quality])
	hud.set_menu_text("sens", "Citlivost otáčení: %s" % SENS_NAMES[sens_i])
	hud.set_menu_text("quit", "Ukončit hru")


func _save() -> void:
	_cfg.set_value("hra", "kvalita", quality)
	_cfg.set_value("hra", "citlivost", sens_i)
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
	var scales := [0.55, 0.7, 0.85] if mobile else [0.7, 0.85, 1.0]
	var sc: float = scales[quality]
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if sc < 0.99 else Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = sc
	vp.fsr_sharpness = 0.25
	var env: Environment = day.env
	env.ssao_enabled = quality >= 1
	env.ssao_radius = 1.1
	env.ssao_intensity = 1.9
	env.ssao_power = 1.6
	env.ssao_detail = 0.5
	env.ssao_horizon = 0.06
	env.ssao_sharpness = 0.98
	env.ssao_light_affect = 0.05
	env.glow_enabled = quality >= 1
	var sun: DirectionalLight3D = day.sun
	sun.directional_shadow_max_distance = [55.0, 90.0, 120.0][quality]
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if quality == 0 else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	RenderingServer.directional_shadow_atlas_set_size(2048 if quality == 0 else 4096, true)
	for g: GeometryInstance3D in _grass:
		g.visibility_range_end = [32.0, 50.0, 66.0][quality]
	life.set_quality(quality)
