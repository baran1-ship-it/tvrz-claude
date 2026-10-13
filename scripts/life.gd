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
	for n: String in ["otevrit", "zavrit", "presun", "polozit", "menu", "listovat", "mince"]:
		var o = load("res://zvuky/predmety/%s.ogg" % n)
		if o != null:
			_sounds[n] = o
	for n: String in ["birds", "fire", "night", "wind"]:
		if _sounds.has(n):
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


## Prehraje kratky zvuk; s pozici prostorove.
func sfx(n: String, db: float = 0.0, pitch: float = 1.0, pos = null) -> void:
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
				p3.global_position = pos
				p3.play()
				return


## skutecne nahravky kroku (Kenney Impact Sounds, CC0): povrch -> sada peti variant
const KROKY := {"stone": "concrete", "wood": "wood", "grass": "grass", "dirt": "carpet"}
var _kroky := {}
var _krok_last := -1


func step_sound(surface: String, loud: float) -> void:
	var set_name: String = KROKY.get(surface, "concrete")
	if not _kroky.has(set_name):
		var arr: Array = []
		for i in 5:
			arr.append(load("res://zvuky/kroky/footstep_%s_%03d.ogg" % [set_name, i]))
		_kroky[set_name] = arr
	var i := randi_range(0, 4)
	if i == _krok_last:
		i = (i + 1) % 5
	_krok_last = i
	_sounds["_krok"] = _kroky[set_name][i]
	sfx("_krok", linear_to_db(0.3 + 0.5 * loud) - 4.0, randf_range(0.92, 1.06))


func surface_at(pos: Vector3) -> String:
	if room_name != "":
		return "wood" if WOOD_FLOOR.has(room_name) else "stone"
	if pos.y > 5.6:
		return "wood"
	if absf(pos.x + 4.0) < 21.0 and absf(pos.z) < 14.0:
		if extra[1]["aabb"].has_point(pos + Vector3(0, 0.5, 0)):
			return "wood"
		return "dirt"
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
				var l := _light(pos + Vector3(0.6, 0.55, 0), 2.7, 9.5, true, night, fx)
				fire_spots[f.get("name", "krb")] = {"fx": fx, "light": l, "boost": 0.0, "pos": pos}
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
	_add_fire_loop("krb", 2.0)
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
	for d: Dictionary in lights:
		var l: OmniLight3D = d["light"]
		l.shadow_enabled = d["shadow"] and q >= 1


# ------------------------------------------------------------------ denni doba

func _on_time(_key: String, night: bool) -> void:
	for d: Dictionary in lights:
		if d["night_only"]:
			(d["light"] as OmniLight3D).visible = night
	for n: Node3D in night_fx:
		n.visible = night
		if n is CPUParticles3D:
			(n as CPUParticles3D).emitting = night
	if night:
		if not _amb_night.playing:
			_amb_night.play()
		_amb_day.stop()
	else:
		if not _amb_day.playing:
			_amb_day.play()
		_amb_night.stop()
	if not _amb_wind.playing:
		_amb_wind.play()


# ------------------------------------------------------------------ prace kazdy snimek

func _process(delta: float) -> void:
	_t += delta
	for d: Dictionary in lights:
		var l: OmniLight3D = d["light"]
		if not l.visible:
			continue
		var ph: float = d["phase"] + _t * d["speed"]
		var fl := 0.82 + 0.1 * sin(ph) + 0.06 * sin(ph * 2.3 + 1.7) + 0.05 * sin(ph * 5.1)
		l.light_energy = d["base"] * fl
	for n: String in fire_spots:
		var s: Dictionary = fire_spots[n]
		if s["boost"] > 0.0:
			s["boost"] = maxf(0.0, s["boost"] - delta / 7.0)
			var l2: OmniLight3D = s["light"]
			l2.light_energy *= 1.0 + s["boost"] * 0.9
			var fl2: CPUParticles3D = s["fx"][0]
			fl2.speed_scale = 1.0 + s["boost"] * 0.6
			fl2.scale_amount_max = fl2.get_meta("smax", fl2.scale_amount_max) * (1.0 + s["boost"] * 0.5)
	if player == null:
		return
	_update_place(delta)


func _update_place(delta: float) -> void:
	var pos := player.global_position + Vector3(0, 0.9, 0)
	var rn := ""
	var amb := 1.0
	for r: Dictionary in rooms:
		var box: AABB = r["aabb"]
		if box.grow(0.05).has_point(pos):
			rn = r["name"]
			var c: Color = r["ambient"]
			amb = clampf(c.get_luminance() * 2.3, 0.32, 1.0)
			break
	room_name = rn
	var title := ""
	if rn != "":
		title = ROOM_TITLES.get(rn, "")
	else:
		for e: Dictionary in extra:
			if (e["aabb"] as AABB).has_point(pos):
				title = e["name"]
				break
		if title == "":
			if pos.y > 6.0 and (absf(pos.x) > 15.5 or absf(pos.z) > 12.5):
				title = "Na hradbách"
			elif absf(pos.x + 4.0) < 21.0 and absf(pos.z) < 14.0:
				title = "Nádvoří"
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
	# vnitrek: mene svetla z oblohy, oko se prizpusobi
	var target := 1.0 - amb
	_interior = lerpf(_interior, target, minf(1.0, delta * 1.6))
	day.set_interior(_interior)
	var muffle := linear_to_db(1.0 - _interior * 0.75)
	for p: AudioStreamPlayer in [_amb_day, _amb_wind, _amb_night]:
		p.volume_db = float(p.get_meta("base_db")) + muffle


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
		# jen v tesne blizkosti a pri pohledu na predmet
		if d > float(u["r"]) * 0.62:
			continue
		if d > 0.7 and fwd.dot(to / d) < 0.6:
			continue
		if d < best_d:
			best_d = d
			best = u
	return best


func use_label(u: Dictionary, has_bow: bool) -> String:
	match u.get("kind", ""):
		"bow":
			return "Vrátit luk" if has_bow else "Vzít luk"
		"bed":
			return "Lehnout si"
		"fire":
			return "Přiložit do ohně"
		"anvil":
			return "Kout"
	return "Použít"


func stoke(n: String) -> void:
	if not fire_spots.has(n):
		return
	var s: Dictionary = fire_spots[n]
	s["boost"] = 1.0
	var fl: CPUParticles3D = s["fx"][0]
	if not fl.has_meta("smax"):
		fl.set_meta("smax", fl.scale_amount_max)
	var em: CPUParticles3D = s["fx"][1]
	em.restart()
	sfx("whoosh", -6.0, 0.7, s["pos"])


func strike_anvil() -> void:
	var pos: Vector3 = info.get("anvil", Vector3.ZERO) + Vector3(0, 0.12, 0)
	sfx("anvil%d" % randi_range(1, 2), 0.0, randf_range(0.95, 1.05), pos)
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
