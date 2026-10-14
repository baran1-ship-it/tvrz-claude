extends Node
## Slunce, obloha, mlha a denni doba.

signal time_changed(key: String, night: bool)

const ORDER := ["rano", "poledne", "odpoledne", "soumrak", "noc"]
const NAMES := {"rano": "Ráno", "poledne": "Poledne", "odpoledne": "Odpoledne", "soumrak": "Soumrak", "noc": "Noc"}

var presets := {
	"rano": {"el": 13.0, "az": 100.0, "sun": Color(1.0, 0.80, 0.60), "sun_e": 2.3,
		"zenith": Color(0.19, 0.36, 0.64), "horizon": Color(0.88, 0.74, 0.62), "tint": Color(1.0, 0.76, 0.52), "glow": 0.7,
		"c_lit": Color(1.0, 0.88, 0.78), "c_dark": Color(0.50, 0.52, 0.62), "sky_e": 1.0, "amb": 0.85,
		"fog": Color(0.84, 0.76, 0.70), "fog_d": 0.0032, "mist": 0.05, "stars": 0.0, "night": false},
	"poledne": {"el": 57.0, "az": 180.0, "sun": Color(1.0, 0.97, 0.92), "sun_e": 3.2,
		"zenith": Color(0.13, 0.31, 0.66), "horizon": Color(0.60, 0.74, 0.88), "tint": Color(1.0, 0.95, 0.85), "glow": 0.3,
		"c_lit": Color(1.0, 0.99, 0.97), "c_dark": Color(0.56, 0.62, 0.72), "sky_e": 1.0, "amb": 1.0,
		"fog": Color(0.66, 0.76, 0.86), "fog_d": 0.0011, "mist": 0.008, "stars": 0.0, "night": false},
	"odpoledne": {"el": 27.0, "az": 238.0, "sun": Color(1.0, 0.89, 0.72), "sun_e": 3.0,
		"zenith": Color(0.14, 0.32, 0.63), "horizon": Color(0.72, 0.77, 0.80), "tint": Color(1.0, 0.86, 0.64), "glow": 0.45,
		"c_lit": Color(1.0, 0.96, 0.88), "c_dark": Color(0.54, 0.59, 0.68), "sky_e": 1.0, "amb": 0.95,
		"fog": Color(0.74, 0.77, 0.80), "fog_d": 0.0015, "mist": 0.012, "stars": 0.0, "night": false},
	"soumrak": {"el": 4.5, "az": 286.0, "sun": Color(1.0, 0.56, 0.30), "sun_e": 1.7,
		"zenith": Color(0.14, 0.20, 0.42), "horizon": Color(0.95, 0.56, 0.32), "tint": Color(1.0, 0.50, 0.25), "glow": 1.0,
		"c_lit": Color(1.0, 0.62, 0.42), "c_dark": Color(0.34, 0.30, 0.42), "sky_e": 0.8, "amb": 0.75,
		"fog": Color(0.72, 0.52, 0.44), "fog_d": 0.0022, "mist": 0.03, "stars": 0.08, "night": true},
	"noc": {"el": 38.0, "az": 150.0, "sun": Color(0.55, 0.66, 0.95), "sun_e": 0.32,
		"zenith": Color(0.010, 0.016, 0.040), "horizon": Color(0.030, 0.045, 0.085), "tint": Color(0.5, 0.6, 0.9), "glow": 0.5,
		"c_lit": Color(0.13, 0.15, 0.22), "c_dark": Color(0.025, 0.03, 0.05), "sky_e": 1.0, "amb": 1.6,
		"fog": Color(0.030, 0.042, 0.070), "fog_d": 0.0020, "mist": 0.02, "stars": 1.0, "night": true},
}

## Plynuly cas: 24 hernich hodin = 90 minut skutecnych. Klicove snimky oblohy podle hodiny, mezi nimi plynuly prechod.
const RATE := 24.0 / 5400.0
const KEY_HOUR := {"rano": 7.0, "poledne": 12.0, "odpoledne": 15.5, "soumrak": 19.6, "noc": 23.0}
const FRAMES := [[0.0, "noc"], [4.6, "noc"], [6.6, "rano"], [12.0, "poledne"], [15.5, "odpoledne"], [19.4, "soumrak"],
		[21.0, "noc"], [24.0, "noc"]]
var hour := 15.5
var day_n := 1
var running := true
var _last: Dictionary = {}
var _acc := 0.0

var sun: DirectionalLight3D
var env: Environment
var sky_mat: ShaderMaterial
var current := "odpoledne"
var amb_base := 1.0
var interior := 0.0            # 0 venku, 1 hluboko uvnitr (nastavuje zivot tvrze)
var _from: Dictionary = {}
var _to: Dictionary = {}
var _t := 1.0
var _dur := 1.0


func setup(start_key: String) -> void:
	sun = DirectionalLight3D.new()
	sun.name = "Slunce"
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 110.0
	sun.directional_shadow_blend_splits = true
	sun.shadow_bias = 0.04
	sun.shadow_normal_bias = 1.6
	sun.shadow_blur = 1.2
	sun.light_angular_distance = 0.7
	add_child(sun)

	sky_mat = ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/sky.gdshader")
	sky_mat.set_shader_parameter("cloud_tex", load("res://textures/cloud_noise.png"))
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_128
	sky.process_mode = Sky.PROCESS_MODE_QUALITY

	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_white = 6.0
	env.tonemap_exposure = 1.0
	env.fog_enabled = true
	env.fog_aerial_perspective = 0.55
	env.fog_sky_affect = 0.25
	env.fog_sun_scatter = 0.12
	env.fog_height = -6.0
	env.glow_enabled = true
	env.glow_intensity = 0.55
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 1.1
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.06
	env.adjustment_saturation = 1.06
	var we := WorldEnvironment.new()
	we.name = "Prostredi"
	we.environment = env
	add_child(we)
	current = start_key
	hour = KEY_HOUR.get(start_key, 15.5)
	_apply(state_at(hour))
	set_process(true)


func next_key() -> String:
	return ORDER[(ORDER.find(current) + 1) % ORDER.size()]


func set_time(key: String, seconds: float = 2.5) -> void:
	if not presets.has(key):
		return
	set_hour(KEY_HOUR[key], seconds)


## Skok na hodinu (spanek, nacteni hry): kdyz je cil drive nez ted, zacina dalsi den.
func set_hour(h: float, seconds: float = 2.5) -> void:
	h = fposmod(h, 24.0)
	if h < hour - 0.01 and seconds > 0.05:
		day_n += 1
	hour = h
	_from = _snapshot()
	_to = state_at(hour)
	_t = 0.0
	_dur = maxf(seconds, 0.01)
	set_process(true)
	_update_key(true)


func key_at(h: float) -> String:
	if h >= 5.5 and h < 10.5:
		return "rano"
	if h >= 10.5 and h < 14.0:
		return "poledne"
	if h >= 14.0 and h < 18.6:
		return "odpoledne"
	if h >= 18.6 and h < 21.0:
		return "soumrak"
	return "noc"


func clock_text() -> String:
	var m := int(hour * 60.0)
	return "%d:%02d" % [m / 60, m % 60]


func _update_key(force: bool) -> void:
	var k := key_at(hour)
	if k != current or force:
		current = k
		time_changed.emit(k, presets[k]["night"])


func is_night() -> bool:
	return presets[current]["night"]


## Stav oblohy pro danou hodinu: smichani dvou sousednich klicovych snimku.
func state_at(h: float) -> Dictionary:
	var a: Array = FRAMES[0]
	var b: Array = FRAMES[1]
	for i in range(FRAMES.size() - 1):
		if h >= float(FRAMES[i][0]) and h <= float(FRAMES[i + 1][0]):
			a = FRAMES[i]
			b = FRAMES[i + 1]
			break
	var w := smoothstep(0.0, 1.0, (h - float(a[0])) / maxf(0.001, float(b[0]) - float(a[0])))
	return _mix(presets[a[1]], presets[b[1]], w)


func _mix(pa: Dictionary, pb: Dictionary, w: float) -> Dictionary:
	var mixd := {}
	for k: String in pb:
		var x = pa[k]
		var y = pb[k]
		if x is bool:
			mixd[k] = y if w > 0.5 else x
		elif x is Color:
			mixd[k] = (x as Color).lerp(y, w)
		else:
			mixd[k] = lerpf(x, y, w)
	mixd["az"] = rad_to_deg(lerp_angle(deg_to_rad(pa["az"]), deg_to_rad(pb["az"]), w))
	return mixd


func _snapshot() -> Dictionary:
	return _last.duplicate() if not _last.is_empty() else state_at(hour)


func _process(delta: float) -> void:
	if _t < 1.0:
		_t = minf(1.0, _t + delta / _dur)
		_apply(_mix(_from, _to, smoothstep(0.0, 1.0, _t)))
		return
	if not running:
		return
	hour += delta * RATE
	if hour >= 24.0:
		hour -= 24.0
		day_n += 1
	# slunce se hybe pomalu: staci obnovit oblohu par krat za sekundu
	_acc += delta
	if _acc >= 0.25:
		_acc = 0.0
		_apply(state_at(hour))
		_update_key(false)


func sun_dir(p: Dictionary) -> Vector3:
	var el := deg_to_rad(p["el"])
	var az := deg_to_rad(p["az"])
	return Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el)).normalized()


func _apply(p: Dictionary) -> void:
	_last = p
	var d := sun_dir(p)
	sun.look_at_from_position(d * 100.0, Vector3.ZERO, Vector3.UP)
	sun.light_color = p["sun"]
	sun.light_energy = p["sun_e"]
	sky_mat.set_shader_parameter("zenith", p["zenith"])
	sky_mat.set_shader_parameter("horizon", p["horizon"])
	sky_mat.set_shader_parameter("sun_tint", p["tint"])
	sky_mat.set_shader_parameter("sun_glow", p["glow"])
	sky_mat.set_shader_parameter("cloud_lit", p["c_lit"])
	sky_mat.set_shader_parameter("cloud_dark", p["c_dark"])
	sky_mat.set_shader_parameter("stars", p["stars"])
	sky_mat.set_shader_parameter("energy", p["sky_e"])
	var hz: Color = p["horizon"]
	sky_mat.set_shader_parameter("ground", Color(hz.r * 0.32, hz.g * 0.31, hz.b * 0.3))
	amb_base = p["amb"]
	_amb()
	env.fog_light_color = p["fog"]
	env.fog_density = p["fog_d"]
	env.fog_height_density = p["mist"]


## Uvnitr ubude svetla z oblohy a oko se trochu prizpusobi tme.
func set_interior(f: float) -> void:
	interior = clampf(f, 0.0, 1.0)
	_amb()


func _amb() -> void:
	if env == null:
		return
	env.ambient_light_energy = amb_base * (1.0 - interior * 0.9)
	env.tonemap_exposure = 1.0 + interior * 0.45
