extends Node3D
## Zivot tvrze: ohne se svetlem, kour, zvuky prostredi, mistnosti a vyuzitelne predmety.

signal place_changed(title: String)

const ROOM_TITLES := {
	"branka": "Strážní komora nad branou", "prujezd": "Průjezd brány",
	"vez0": "Věž – přízemí", "vez1": "Věž – patro", "vez2": "Věž – ochoz",
	"sin": "Hodovní síň", "spiz": "Spíž", "komnata": "Komnata", "loznice": "Ložnice",
	"zbrojnice": "Zbrojnice",
}
const WOOD_FLOOR := ["branka", "vez1", "vez2", "komnata", "loznice", "zbrojnice"]
const FIRE_COL := Color(1.0, 0.64, 0.38)

var info: Dictionary
var day: Node
var player: Node3D
var rooms: Array = []
var extra: Array = []                 # dalsi oblasti bez stropu (kovarna, strelnice)
var _svetel := 0
var lights: Array = []                # {light, base, phase, speed, night_only, fx}
var night_fx: Array = []              # uzly zobrazene jen v noci
var fire_spots: Dictionary = {}       # jmeno -> {fx: Array, light, boost}
var place := ""
var room_name := ""
var _place_t := 0.0
var _pending := ""
var _interior := 0.0
var _amb_mul := 1.0
var _t := 0.0

var _sounds: Dictionary = {}
var _amb_day: AudioStreamPlayer
var _amb_wind: AudioStreamPlayer
var _amb_night: AudioStreamPlayer
var _pool: Array = []
var _pool3d: Array = []
var quality := 1


func setup(p_info: Dictionary, p_day: Node, p_player: Node3D) -> void:
	info = p_info
	day = p_day
	player = p_player
	rooms = info["rooms"]
	extra = [
		{"name": "Kovárna", "aabb": AABB(Vector3(-19.9, -0.5, 9.0), Vector3(9.0, 4.5, 5.0)), "wood": false},
		{"name": "Stáj", "aabb": AABB(Vector3(-25.0, -0.5, -8.3), Vector3(4.6, 4.0, 9.3)), "wood": true},
	]
	process_priority = 10
	_load_sounds()
	_build_fires()
	_build_smoke()
	_build_ambience()
	day.time_changed.connect(_on_time)
	_on_time(day.current, day.is_night())


# ------------------------------------------------------------------ zvuky

func _load_sounds() -> void:
	var names := ["anvil1", "anvil2", "birds", "bow_draw", "bow_shot", "chime", "click", "fire", "hit_target",
			"hit_wood", "night", "whoosh", "wind", "step_grass1", "step_grass2", "step_grass3",
			"step_stone1", "step_stone2", "step_stone3", "step_wood1", "step_wood2", "step_wood3"]
	for n: String in names:
		var s = load("res://audio/%s.wav" % n)
		if s != null:
			_sounds[n] = s
	for n: String in ["otevrit", "zavrit", "presun", "polozit", "menu", "listovat", "mince", "myti"]:
		var o = load("res://zvuky/predmety/%s.ogg" % n)
		if o != null:
			_sounds[n] = o
	# nove nahravky (zvuky/predmety2, zvuky/prostredi; autori v zvuky/seznam.txt) - kratke zvuky s variantami
	for f: String in DirAccess.get_files_at("res://zvuky/rozhrani"):
		var f3 := f.trim_suffix(".import").trim_suffix(".remap")
		if f3.ends_with(".ogg"):
			_sounds[f3.get_basename()] = load("res://zvuky/rozhrani/" + f3)
	for f: String in DirAccess.get_files_at("res://zvuky/predmety2"):
		var f2 := f.trim_suffix(".import").trim_suffix(".remap")
		if f2.ends_with(".ogg"):
			_sounds[f2.get_basename()] = load("res://zvuky/predmety2/" + f2)
	if _sounds.has("mince_1"):
		_sounds.erase("mince")                     # nove varianty mince_1..4 misto stareho cinknuti
	var krb: AudioStream = load("res://zvuky/prostredi/krb.ogg") if ResourceLoader.exists("res://zvuky/prostredi/krb.ogg") else null
	if krb is AudioStreamOggVorbis:
		(krb as AudioStreamOggVorbis).loop = true
		_sounds["fire"] = krb
	for n: String in ["birds", "night", "wind"]:
		if _sounds.has(n) and _sounds[n] is AudioStreamWAV:
			var w: AudioStreamWAV = _sounds[n]
			w.loop_mode = AudioStreamWAV.LOOP_FORWARD
			w.loop_begin = 0
			w.loop_end = int(w.get_length() * w.mix_rate)
	for k in 8:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_pool.append(p)
	for k in 8:
		var p3 := AudioStreamPlayer3D.new()
		p3.unit_size = 3.0
		p3.max_distance = 40.0
		add_child(p3)
		_pool3d.append(p3)


## Nahodna varianta zvuku (napr. "polozit_drevo" -> polozit_drevo_1..4); bez variant primo n.
func varianta(n: String) -> String:
	if _sounds.has(n):
		return n
	var arr: Array = []
	for i in range(1, 9):
		if _sounds.has("%s_%d" % [n, i]):
			arr.append("%s_%d" % [n, i])
	return arr.pick_random() if not arr.is_empty() else n


## Prehraje dany zvuk (stream) v prostoru, napr. hlasy zvirat.
func sfx_stream(st: AudioStream, db: float, pitch: float, pos: Vector3) -> void:
	for p3: AudioStreamPlayer3D in _pool3d:
		if not p3.playing:
			p3.stream = st
			p3.volume_db = db
			p3.pitch_scale = pitch
			p3.max_distance = 70.0
			p3.global_position = pos
			p3.play()
			return


## Prehraje kratky zvuk; s pozici prostorove.
func sfx(n: String, db: float = 0.0, pitch: float = 1.0, pos = null) -> void:
	n = varianta(n)
	if not _sounds.has(n):
		return
	if pos == null:
		for p: AudioStreamPlayer in _pool:
			if not p.playing:
				p.stream = _sounds[n]
				p.volume_db = db
				p.pitch_scale = pitch
				p.play()
				return
	else:
		for p3: AudioStreamPlayer3D in _pool3d:
			if not p3.playing:
				p3.stream = _sounds[n]
				p3.volume_db = db
				p3.pitch_scale = pitch
				p3.max_distance = 40.0
				p3.global_position = pos
				p3.play()
				return


## kroky: nahravky (zvukovy chat, CC BY 3.0 / CC0) - povrch -> sada: chuze 8 variant, beh 4, doskok 3
const KROKY := {"stone": "kamen", "wood": "drevo", "grass": "trava", "dirt": "hlina", "listi": "listi", "most": "most",
		"voda": "voda", "sterk": "sterk", "blato": "blato", "seno": "seno"}
var _kroky := {}
var _krok_last := -1


func step_sound(surface: String, loud: float) -> void:
	var p: String = KROKY.get(surface, "trava")
	var druh := "krok_%s" % p
	var n := 8
	if loud >= 1.1:
		druh = "doskok_%s" % p
		n = 3
	elif loud >= 0.8:
		druh = "krok_%s_beh" % p
		n = 4
	# zvuky kroku noveho povrchu se nacitaji ve vlakne (0.62 bod 8: 8 souboru v hlavnim vlakne = zasek na prvnim
	# kroku v lese/na kameni); do nacteni prvni kroky bez zvuku
	if not _kroky.has(druh):
		var cesty: PackedStringArray = []
		for i in n:
			var path := "res://zvuky/kroky/%s_%d.ogg" % [druh, i + 1]
			if ResourceLoader.exists(path):
				ResourceLoader.load_threaded_request(path)
				cesty.append(path)
		_kroky[druh] = cesty
	if _kroky[druh] is PackedStringArray:
		var cesty2: PackedStringArray = _kroky[druh]
		for path in cesty2:
			if ResourceLoader.load_threaded_get_status(path) == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
				return
		var arr: Array = []
		for path in cesty2:
			if ResourceLoader.load_threaded_get_status(path) == ResourceLoader.THREAD_LOAD_LOADED:
				arr.append(ResourceLoader.load_threaded_get(path))
		_kroky[druh] = arr
	var arr2: Array = _kroky[druh]
	if arr2.is_empty():
		return
	var i := randi_range(0, arr2.size() - 1)
	if i == _krok_last and arr2.size() > 1:
		i = (i + 1) % arr2.size()
	_krok_last = i
	_sounds["_krok"] = arr2[i]
	sfx("_krok", linear_to_db(0.25 + 0.45 * minf(loud, 1.2)) - 3.0, randf_range(0.95, 1.05))


func surface_at(pos: Vector3) -> String:
	if room_name != "":
		return "wood" if WOOD_FLOOR.has(room_name) else "stone"
	if pos.y > 5.6:
		return "wood"
	var vd: Node = get_parent().get("voda")
	if vd and vd.ve_vode:
		return "voda"
	if absf(pos.x + 4.0) < 21.0 and absf(pos.z) < 14.0:
		if extra[1]["aabb"].has_point(pos + Vector3(0, 0.5, 0)):
			return "wood"
		return "dirt"
	# v ruinach (sut, listi, kopriva) sustí listi
	for m: Dictionary in info.get("mista", []):
		if Vector2(pos.x - float(m["x"]), pos.z - float(m["z"])).length() < float(m["r"]) - 8.0:
			return "listi"
	return "grass"


func _build_ambience() -> void:
	_amb_day = _loop_player("birds", -9.0)
	_amb_wind = _loop_player("wind", -15.0)
	_amb_night = _loop_player("night", -11.0)


func _loop_player(n: String, db: float) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	if _sounds.has(n):
		p.stream = _sounds[n]
	p.volume_db = db
	p.set_meta("base_db", db)
	add_child(p)
	return p


# ------------------------------------------------------------------ ohne

func _flame_mat(tex: String, additive: bool) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	if additive:
		m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_texture = load("res://textures/%s.png" % tex)
	m.vertex_color_use_as_albedo = true
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.billboard_keep_scale = true
	m.disable_receive_shadows = true
	m.no_depth_test = false
	return m


func _flames(pos: Vector3, size: float, amount: int, life: float) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = amount
	p.lifetime = life
	p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(0.22, 0.03, 0.12) * size
	p.direction = Vector3.UP
	p.spread = 12.0
	p.gravity = Vector3(0, 0.9 * size, 0)
	p.initial_velocity_min = 0.25 * size
	p.initial_velocity_max = 0.55 * size
	p.scale_amount_min = 0.55 * size
	p.scale_amount_max = 0.95 * size
	var curve := Curve.new()
	curve.add_point(Vector2(0.0, 0.6))
	curve.add_point(Vector2(0.25, 1.0))
	curve.add_point(Vector2(1.0, 0.15))
	p.scale_amount_curve = curve
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.85, 0.5, 0.0))
	g.set_color(1, Color(0.6, 0.12, 0.02, 0.0))
	g.add_point(0.12, Color(1.0, 0.78, 0.38, 0.9))
	g.add_point(0.5, Color(1.0, 0.42, 0.1, 0.6))
	p.color_ramp = g
	var q := QuadMesh.new()
	q.size = Vector2(0.32, 0.42)
	q.material = _flame_mat("p_flame", true)
	p.mesh = q
	p.position = pos
	add_child(p)
	return p


func _embers(pos: Vector3, size: float, amount: int) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = amount
	p.lifetime = 1.6
	p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(0.25, 0.05, 0.12) * size
	p.direction = Vector3.UP
	p.spread = 25.0
	p.gravity = Vector3(0.1, 0.6, 0)
	p.initial_velocity_min = 0.6
	p.initial_velocity_max = 1.4
	p.scale_amount_min = 0.25
	p.scale_amount_max = 0.6
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.8, 0.4, 1.0))
	g.set_color(1, Color(1.0, 0.25, 0.05, 0.0))
	p.color_ramp = g
	var q := QuadMesh.new()
	q.size = Vector2(0.03, 0.03)
	q.material = _flame_mat("p_soft", true)
	p.mesh = q
	p.position = pos
	add_child(p)
	return p


func _candle_flame(pos: Vector3, h: float = 0.07) -> Sprite3D:
	var s := Sprite3D.new()
	s.texture = load("res://textures/p_flame.png")
	s.pixel_size = h / 256.0
	s.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	s.shaded = false
	s.alpha_cut = SpriteBase3D.ALPHA_CUT_DISABLED
	s.modulate = Color(1.0, 0.75, 0.4, 0.95)
	s.position = pos + Vector3(0, h * 0.35, 0)
	s.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(s)
	return s


func _light(pos: Vector3, energy: float, rng: float, shadow: bool, night_only: bool, fx: Array) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.light_color = FIRE_COL
	l.light_energy = energy
	l.omni_range = rng
	l.omni_attenuation = 1.3
	l.shadow_enabled = shadow
	l.shadow_bias = 0.08
	l.shadow_normal_bias = 1.5
	l.light_specular = 0.35
	l.position = pos
	add_child(l)
	lights.append({"light": l, "base": energy, "phase": randf() * 50.0, "speed": randf_range(7.0, 11.0),
			"night_only": night_only, "fx": fx, "shadow": shadow})
	return l


func _build_fires() -> void:
	var candles := 0
	for f: Dictionary in info["fires"]:
		var pos: Vector3 = f["pos"]
		var kind: String = f["kind"]
		var night: bool = f.get("night_only", false)
		var fx: Array = []
		match kind:
			"hearth":
				fx.append(_flames(pos, 1.25, 30, 0.75))
				fx.append(_embers(pos, 1.2, 10))
				var lo: Array = f.get("svetlo", [0.6, 0.55, 0.0])      # posun svetla od ohne do mistnosti
				var l := _light(pos + Vector3(lo[0], lo[1], lo[2]), 2.7, 9.5, true, night, fx)
				fire_spots[f.get("name", "krb")] = {"fx": fx, "light": l, "boost": 0.0, "pos": pos, "on": true, "zap": f.get("zap", false)}
			"forge":
				fx.append(_flames(pos, 0.7, 18, 0.55))
				fx.append(_embers(pos, 0.7, 8))
				var l2 := _light(pos + Vector3(-0.5, 0.4, 0), 2.1, 6.5, true, night, fx)
				fire_spots[f.get("name", "vyhen")] = {"fx": fx, "light": l2, "boost": 0.0, "pos": pos}
			"brazier":
				fx.append(_flames(pos, 0.6, 16, 0.55))
				fx.append(_embers(pos, 0.6, 5))
				_light(pos + Vector3(0, 0.45, 0), 1.7, 6.0, false, night, fx)
			"torch":
				fx.append(_flames(pos, 0.38, 10, 0.45))
				_light(pos + Vector3(0, 0.2, 0), 1.35, 6.0, false, night, fx)
			"chandelier":
				var r: float = f.get("r", 0.5)
				var n: int = f.get("n", 6)
				for k in n:
					var a := TAU * k / n
					fx.append(_candle_flame(pos + Vector3(cos(a) * r, 0.0, sin(a) * r), 0.08))
				_light(pos + Vector3(0, -0.15, 0), 1.5, 7.5, false, night, fx)
			"candle":
				fx.append(_candle_flame(pos))
				candles += 1
				if candles <= 10:
					_light(pos + Vector3(0, 0.08, 0), 0.35, 2.4, false, night, fx)
		if night:
			night_fx.append_array(fx)
		# rad 12:40, Misa 0.69: louce, lustry, panve a svice (kandelabr u (9,-10)) jde zapalit a zhasnout jako svicen;
		# samy sviti jako predmety (vecer a v noci ty "jen v noci"), dokud je hrac neovlada rucne
		if kind in ["torch", "chandelier", "brazier", "candle"]:
			var sn := "svetlo_%d" % _svetel
			_svetel += 1
			var sl: OmniLight3D = null
			if not lights.is_empty() and (lights[-1]["fx"] as Array) == fx:
				sl = lights[-1]["light"]
				lights[-1]["spot"] = sn
			for f3: Node3D in fx:
				f3.set_meta("spot", sn)
			fire_spots[sn] = {"fx": fx, "light": sl, "boost": 0.0, "pos": pos, "on": true, "zap": true, "auto": true, "night_only": night,
					"svetlo": true}
			info["use"].append({"kind": "svetlo", "pos": pos, "r": 1.5 if kind != "chandelier" else 2.2, "name": sn,
					"nazev": {"torch": "Louč", "chandelier": "Lustr", "brazier": "Pánev s ohněm", "candle": "Svíce"}[kind]})
	_add_fire_loop("krb", 2.0)
	for n: String in fire_spots:
		if n.begins_with("krb_hostinec"):
			_add_fire_loop(n, 0.0)
	_add_fire_loop("vyhen", 0.0)


func _add_fire_loop(n: String, db: float) -> void:
	if not fire_spots.has(n) or not _sounds.has("fire"):
		return
	var p3 := AudioStreamPlayer3D.new()
	p3.stream = _sounds["fire"]
	p3.volume_db = db
	p3.unit_size = 2.5
	p3.max_distance = 22.0
	p3.position = fire_spots[n]["pos"]
	add_child(p3)
	p3.play()
	p3.set_meta("base_db", db)
	fire_spots[n]["sound"] = p3


func _build_smoke() -> void:
	for pos: Vector3 in info["smoke"]:
		var p := CPUParticles3D.new()
		p.amount = 14
		p.lifetime = 8.0
		p.preprocess = 8.0
		p.local_coords = false
		p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
		p.emission_sphere_radius = 0.2
		p.direction = Vector3.UP
		p.spread = 10.0
		p.gravity = Vector3(0.35, 0.12, 0.15)
		p.initial_velocity_min = 0.5
		p.initial_velocity_max = 0.8
		p.scale_amount_min = 1.0
		p.scale_amount_max = 1.6
		var curve := Curve.new()
		curve.add_point(Vector2(0.0, 0.4))
		curve.add_point(Vector2(1.0, 3.2))
		p.scale_amount_curve = curve
		var g := Gradient.new()
		g.set_color(0, Color(0.55, 0.55, 0.55, 0.0))
		g.set_color(1, Color(0.7, 0.7, 0.72, 0.0))
		g.add_point(0.1, Color(0.5, 0.5, 0.5, 0.32))
		p.color_ramp = g
		var q := QuadMesh.new()
		q.size = Vector2(1.0, 1.0)
		var m := _flame_mat("p_smoke", false)
		m.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
		m.disable_receive_shadows = false
		q.material = m
		p.mesh = q
		p.position = pos
		add_child(p)


func set_quality(q: int) -> void:
	quality = q
	_shadow_t = 0.0
	_shadow_budget()


var _shadow_t := 0.0
const MAX_LIT := 7


func _shadow_budget() -> void:
	# stiny vsesmerovych svetel jsou drahe (kazde prekresli scenu 6x): stin vrha jen nejblizsi svetlo
	# (na vysoke kvalite dve), ostatni sviti bez stinu; vzdalena svetla se plynule vypinaji.
	# Mobilni vykreslovani bere na jeden model jen 8 svetel (a ne nutne nejblizsich): zapnutych
	# zustane jen MAX_LIT nejblizsich, jinak by treba louc v ruce na zemi vubec nesvitila.
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var eye := cam.global_position
	var cand: Array = []
	for d: Dictionary in lights:
		var l: OmniLight3D = d["light"]
		if not is_instance_valid(l):
			continue
		if not d.has("gate"):
			var g := Node3D.new()
			g.name = "brana_svetla"
			var par := l.get_parent()
			par.add_child(g)
			g.transform = Transform3D.IDENTITY
			l.reparent(g, false)
			d["gate"] = g
			l.distance_fade_enabled = true
			l.distance_fade_begin = 28.0
			l.distance_fade_length = 8.0
		var g2: Node3D = d["gate"]
		if l.visible and g2.get_parent().is_visible_in_tree():
			cand.append([eye.distance_squared_to(l.global_position), l, d])
		else:
			l.shadow_enabled = false
	cand.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	var n: int = [0, 1, 2][clampi(quality, 0, 2)]
	for i in cand.size():
		var l2: OmniLight3D = cand[i][1]
		# hystereze: zapnute svetlo zhasne az o kus dal (jinak na hranici blika)
		var was: bool = bool(cand[i][2].get("on", true))
		var lim := 38.0 if was else 34.0
		var on: bool = i < MAX_LIT and cand[i][0] < lim * lim
		cand[i][2]["on"] = on
		l2.shadow_enabled = on and d_shadow(cand[i][2]) and i < n and cand[i][0] < 18.0 * 18.0


func d_shadow(d: Dictionary) -> bool:
	return bool(d.get("shadow", false))


# ------------------------------------------------------------------ denni doba

func _on_time(_key: String, night: bool) -> void:
	for d: Dictionary in lights:
		if d.has("spot"):
			continue                                      # zapalitelne svetlo: nize podle "auto"
		if d["night_only"]:
			(d["light"] as OmniLight3D).visible = night
	for n: String in fire_spots:
		var s: Dictionary = fire_spots[n]
		if bool(s.get("svetlo", false)) and bool(s.get("auto", false)) and bool(s.get("night_only", false)) and fire_on(n) != night:
			set_fire(n, night, true)
	for n: Node3D in night_fx:
		if n.has_meta("spot"):
			continue
		n.visible = night
		if n is CPUParticles3D:
			(n as CPUParticles3D).emitting = night
	# ruchy prostredi podle mista a casu ma na starosti ruchy.gd


# ------------------------------------------------------------------ prace kazdy snimek

func _process(delta: float) -> void:
	_t += delta
	for d: Dictionary in lights:
		var l: OmniLight3D = d["light"]
		if not l.visible:
			continue
		# jemne mihotani plamene (pomale, male) a plynule zapinani/vypinani vzdalenych svetel
		var ph: float = d["phase"] + _t * float(d["speed"]) * 0.35
		var fl := 0.93 + 0.04 * sin(ph) + 0.025 * sin(ph * 2.3 + 1.7) + 0.015 * sin(ph * 4.1)
		var tgt := 1.0 if bool(d.get("on", true)) else 0.0
		var fd := move_toward(float(d.get("fade", 1.0)), tgt, delta * 1.6)
		d["fade"] = fd
		if d.has("gate"):
			(d["gate"] as Node3D).visible = fd > 0.01
		l.light_energy = d["base"] * fl * fd * fd
	for n: String in fire_spots:
		var s: Dictionary = fire_spots[n]
		if s["boost"] > 0.0:
			s["boost"] = maxf(0.0, s["boost"] - delta / 7.0)
			var l2: OmniLight3D = s["light"]
			l2.light_energy *= 1.0 + s["boost"] * 0.9
			var fl2: CPUParticles3D = s["fx"][0]
			fl2.speed_scale = 1.0 + s["boost"] * 0.6
			fl2.scale_amount_max = fl2.get_meta("smax", fl2.scale_amount_max) * (1.0 + s["boost"] * 0.5)
	_moat(delta)
	_shadow_t -= delta
	if _shadow_t <= 0.0:
		_shadow_t = 0.3
		_shadow_budget()
	if player == null:
		return
	_update_place(delta)


func _update_place(delta: float) -> void:
	var pos := player.global_position + Vector3(0, 0.9, 0)
	var rn := ""
	var amb := 1.0
	for r: Dictionary in rooms:
		var box: AABB = r["aabb"]
		var lp := pos
		if r.has("inv"):
			var cc: Vector3 = r["c"]
			if absf(pos.x - cc.x) > 12.0 or absf(pos.z - cc.z) > 12.0:
				continue
			lp = (r["inv"] as Transform3D) * pos
		if box.grow(0.05).has_point(lp):
			rn = r["name"]
			var c: Color = r["ambient"]
			amb = clampf(c.get_luminance() * 2.3, 0.32, 1.0)
			break
	room_name = rn
	var title := ""
	if rn != "":
		title = ROOM_TITLES.get(rn, "")
		for r2: Dictionary in rooms:
			if r2["name"] == rn and String(r2.get("title", "")) != "":
				title = r2["title"]
	else:
		for e: Dictionary in extra:
			if (e["aabb"] as AABB).has_point(pos):
				title = e["name"]
				break
		if title == "":
			for m: Dictionary in info.get("mista", []):
				if Vector2(pos.x - float(m["x"]), pos.z - float(m["z"])).length() < float(m["r"]):
					title = String(m["name"])
					break
		if title == "":
			if pos.y > 6.0 and (absf(pos.x) > 15.5 or absf(pos.z) > 12.5):
				title = "Na hradbách"
			elif absf(pos.x + 4.0) < 21.0 and absf(pos.z) < 14.0:
				title = "Nádvoří"
			elif Vector2(pos.x - 470.0, pos.z - 830.0).length() < 130.0:
				title = "Lhota"
			elif Vector2(pos.x - 5.0, pos.z - 400.0).length() < 25.0:
				title = "Boží muka na rozcestí"
			elif pos.x < -90.0 and pos.z > 220.0 and pos.z < 920.0:
				title = "Skalní město"
			else:
				title = "Okolí tvrze"
	if title != _pending:
		_pending = title
		_place_t = 0.0
	else:
		_place_t += delta
		if _place_t > 0.35 and title != place:
			place = title
			place_changed.emit(title)
	# vnitrek: svetlo z oblohy jen tolik, kolik je ji videt (okna, otevrene dvere); oko se prizpusobi
	var target := 1.0 - amb
	if rn != "":
		_sky_probe(pos)
		# svetlo z oblohy jen kolik je ji videt oknem: v mistnosti s jednim oknem je sero, sviti slunce oknem a ohen
		target = clampf(1.0 - _sky_open * 1.1, 0.0, 1.0)
	_interior = lerpf(_interior, target, minf(1.0, delta * 1.6))
	day.set_interior(_interior)
	var muffle := linear_to_db(1.0 - _interior * 0.75)
	for p: AudioStreamPlayer in [_amb_day, _amb_wind, _amb_night]:
		p.volume_db = float(p.get_meta("base_db")) + muffle


var _sky_open := 1.0
var _sky_rays: Array = []
var _sky_i := 0


## Kolik oblohy je videt z mista hrace: paprsky do horni polokoule a do stran; po 6 za snimek.
func _sky_probe(pos: Vector3) -> void:
	if _sky_rays.is_empty():
		for k in 32:
			var a := k * 2.39996
			var el := lerpf(0.03, 1.2, fmod(k * 0.618034, 1.0))
			_sky_rays.append(Vector3(cos(a) * cos(el), sin(el), sin(a) * cos(el)))
			_sky_rays[k] = (_sky_rays[k] as Vector3).normalized()
		_sky_rays.append(0.0)
	var space := get_viewport().get_world_3d().direct_space_state
	var hits: Array = _sky_rays[32] if _sky_rays[32] is Array else []
	if hits.size() != 32:
		hits = []
		hits.resize(32)
		hits.fill(1.0)
	for j in 6:
		var k := _sky_i % 32
		_sky_i += 1
		var q := PhysicsRayQueryParameters3D.create(pos + Vector3(0, 0.6, 0), pos + Vector3(0, 0.6, 0) + (_sky_rays[k] as Vector3) * 30.0)
		q.exclude = [player.get_rid()]
		hits[k] = 0.0 if not space.intersect_ray(q).is_empty() else 1.0
	_sky_rays[32] = hits
	var sm := 0.0
	for h: float in hits:
		sm += h
	_sky_open = lerpf(_sky_open, sm / 32.0, 0.25)


# ------------------------------------------------------------------ predmety k pouziti

## Nejblizsi vyuzitelny predmet pred hracem, nebo prazdny slovnik.
func usable(cam: Camera3D) -> Dictionary:
	var best := {}
	var best_d := 1e9
	var eye := cam.global_position
	var fwd := -cam.global_transform.basis.z
	for u: Dictionary in info["use"]:
		var p: Vector3 = u["pos"]
		var to := p - eye
		var d := to.length()
		# jen v tesne blizkosti a pri pohledu na predmet; vyska se pocita mene (veci na zemi i na polici)
		var dr := Vector3(to.x, to.y * 0.45, to.z).length()
		var lim := float(u["r"]) * 0.62
		if String(u.get("kind", "")) == "predmet":
			lim = maxf(lim, 1.35)          # i drobnost na zemi jde vzit, kdyz stojim u ni
		if dr > lim:
			continue
		if d > 0.7 and fwd.dot(to / d) < 0.6:
			continue
		# vybira se to, na co miri stred obrazovky (kolma vzdalenost od paprsku pohledu), blizkost jen mirne
		var perp := (to - fwd * maxf(to.dot(fwd), 0.0)).length()
		var sc := perp + dr * 0.15
		if sc < best_d:
			best_d = sc
			best = u
	return best


func use_label(u: Dictionary, has_bow: bool) -> String:
	match u.get("kind", ""):
		"bow":
			return "Vrátit luk" if has_bow else "Vzít luk"
		"bed":
			return "Lehnout si"
		"sed":
			return "Sednout si"
		"fire":
			return "Přiložit do ohně" if fire_on(String(u.get("name", "krb"))) else "Zapálit oheň"
		"svetlo":
			return "Zhasnout" if fire_on(String(u.get("name", ""))) else "Zapálit"
		"anvil":
			return "Kout"
	return "Použít"


func fires_save() -> Dictionary:
	var out := {}
	for n: String in fire_spots:
		if can_light(n) and not bool(fire_spots[n].get("auto", false)):
			out[n] = fire_on(n)                      # svetla "sviti samo" se neukladaji
	return out


func fires_load(d: Dictionary) -> void:
	for n: String in d:
		if can_light(n):
			if bool(fire_spots[n].get("svetlo", false)):
				fire_spots[n]["auto"] = false
			if fire_on(n) != bool(d[n]):
				set_fire(n, bool(d[n]), true)


func fire_on(n: String) -> bool:
	return fire_spots.has(n) and bool(fire_spots[n].get("on", true))


func can_light(n: String) -> bool:
	return fire_spots.has(n) and bool(fire_spots[n].get("zap", false))


func set_fire(n: String, on: bool, tise := false) -> void:
	# krb: zapalit / zhasnout (plameny, jiskry, svetlo, praskani)
	if not fire_spots.has(n):
		return
	var s: Dictionary = fire_spots[n]
	s["on"] = on
	for f: Node3D in s["fx"]:
		f.visible = on
		if f is CPUParticles3D:
			(f as CPUParticles3D).emitting = on
	if s["light"] != null:
		(s["light"] as OmniLight3D).visible = on
	if bool(s.get("svetlo", false)):
		if not tise:
			sfx("click", -10.0, 1.0, s["pos"])
		return
	if s.has("sound"):
		var p3: AudioStreamPlayer3D = s["sound"]
		if on:
			p3.play()
		else:
			p3.stop()
	# krb: vzplanuti polen (hlubsi nez louc), uhaseni = syceni zalitych uhliku; pak smycka praskani krbu
	if on:
		sfx("whoosh", -2.0, 0.6, s["pos"])
	else:
		sfx("kaleni", -8.0, 0.85, s["pos"])


func stoke(n: String) -> void:
	if not fire_spots.has(n):
		return
	if not fire_on(n):
		set_fire(n, true)
		return
	var s: Dictionary = fire_spots[n]
	s["boost"] = 1.0
	var fl: CPUParticles3D = s["fx"][0]
	if not fl.has_meta("smax"):
		fl.set_meta("smax", fl.scale_amount_max)
	var em: CPUParticles3D = s["fx"][1]
	em.restart()
	sfx("polozit_drevo", -4.0, 0.8, s["pos"])


func strike_anvil() -> void:
	var pos: Vector3 = info.get("anvil", Vector3.ZERO) + Vector3(0, 0.12, 0)
	sfx("kovadlina", 0.0, randf_range(0.97, 1.03), pos)
	var p := CPUParticles3D.new()
	p.amount = 24
	p.lifetime = 0.7
	p.one_shot = true
	p.explosiveness = 0.95
	p.local_coords = false
	p.direction = Vector3.UP
	p.spread = 70.0
	p.gravity = Vector3(0, -9.0, 0)
	p.initial_velocity_min = 2.0
	p.initial_velocity_max = 4.5
	p.scale_amount_min = 0.4
	p.scale_amount_max = 1.0
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.95, 0.7, 1.0))
	g.set_color(1, Color(1.0, 0.35, 0.05, 0.0))
	p.color_ramp = g
	var q := QuadMesh.new()
	q.size = Vector2(0.025, 0.025)
	q.material = _flame_mat("p_soft", true)
	p.mesh = q
	p.position = pos
	add_child(p)
	p.emitting = true
	get_tree().create_timer(1.5).timeout.connect(p.queue_free)


# ------------------------------------------------------------------ prikop: vlnky a zaby

var _moat_pts: Array = []
var _rip_t := 4.0
var _rip_i := 0
var _rips := [Vector4.ZERO, Vector4.ZERO, Vector4.ZERO, Vector4.ZERO]
var _frog_t := 20.0
var _frog: AudioStreamPlayer3D
var _frogs: Array = []


func _moat_setup() -> void:
	# mista s vodou kolem hradeb: paprsek shora, dno pod hladinou
	var main_ := get_parent()
	var wy: float = main_.svet.water_y if main_.svet else -2.75
	var space := get_world_3d().direct_space_state
	var R := RandomNumberGenerator.new()
	R.seed = 5
	for k in 260:
		var side := R.randi() % 4
		var t := R.randf()
		var off := R.randf_range(3.0, 10.0)
		var p := Vector3.ZERO
		match side:
			0: p = Vector3(lerpf(-30.0, 22.0, t), 0, -15.8 - off)
			1: p = Vector3(lerpf(-30.0, 22.0, t), 0, 15.8 + off)
			2: p = Vector3(-26.8 - off, 0, lerpf(-19.0, 19.0, t))
			3: p = Vector3(18.8 + off, 0, lerpf(-19.0, 19.0, t))
		var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, 6.0, p.z), Vector3(p.x, -12.0, p.z))
		var h := space.intersect_ray(q)
		if not h.is_empty() and (h["position"] as Vector3).y < wy - 0.15:
			_moat_pts.append(Vector3(p.x, wy, p.z))
	for n in []:            # zaby vypnute (zvuky zvirat hracovi vadily)
		var st: AudioStream = load("res://zvuky/zaby/%s.ogg" % n)
		if st:
			_frogs.append(st)
	_frog = AudioStreamPlayer3D.new()
	_frog.unit_size = 6.0
	_frog.max_distance = 70.0
	add_child(_frog)


func _moat(delta: float) -> void:
	if _moat_pts.is_empty():
		if _rip_t > -1.0:
			_rip_t = -2.0
			_moat_setup.call_deferred()
		return
	var main_ := get_parent()
	var wm: ShaderMaterial = main_.svet.water_mat if main_.svet else null
	var now := fmod(Time.get_ticks_msec() / 1000.0, 3600.0)
	_rip_t -= delta
	if _rip_t <= 0.0 and wm:
		# obcas se hladina zavlni (zaba skocila, ryba, kapka)
		_rip_t = randf_range(5.0, 20.0)
		var p: Vector3 = _moat_pts[randi() % _moat_pts.size()]
		var vd: Node = main_.get("voda")
		if vd:
			vd.vlna(p.x, p.z, randf_range(0.6, 1.0))
	_frog_t -= delta
	if _frog_t <= 0.0 and not _frogs.is_empty():
		var night: bool = main_.day != null and String(main_.day.current) in ["soumrak", "noc"]
		# v noci kazdou chvili (ne porad), ve dne jen vyjimecne
		_frog_t = randf_range(12.0, 45.0) if night else randf_range(120.0, 300.0)
		_croak(randi_range(1, 3) if night else 1)


func _croak(n: int) -> void:
	var p: Vector3 = _moat_pts[randi() % _moat_pts.size()]
	for k in n:
		var pl := _frog if k == 0 else AudioStreamPlayer3D.new()
		if k > 0:
			pl.unit_size = 6.0
			pl.max_distance = 70.0
			add_child(pl)
			pl.finished.connect(pl.queue_free)
		pl.global_position = p + Vector3(randf_range(-4, 4), 0.1, randf_range(-4, 4))
		pl.stream = _frogs[randi() % _frogs.size()]
		pl.pitch_scale = randf_range(0.85, 1.15)
		pl.volume_db = randf_range(-6.0, 0.0)
		if k == 0:
			pl.play()
		else:
			get_tree().create_timer(randf_range(0.4, 2.5)).timeout.connect(pl.play)
