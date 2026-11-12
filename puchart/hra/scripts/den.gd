extends Node
## Denní doba – plynulý den a noc převzatý z Havrana (scripts/daylight.gd; Míša 12. 11. večer: „Zkopíruj denní režim
## slunce jako u Havrana“). Data hra/data/den.json (pravidla/svet/den.json: délka dne, klíčové snímky, barvy – zdroj Havran).
## Řídí jediné slunce a oblohu z hlavni.gd _prostredi (žádné nové světlo ani stín – tablet). Barvy a síly = poměr Havranova
## presetu k jeho odpoledni × hodnota Puchartu (Puchart je vyladěný na odpoledne). hlavni.gd _atmosfera bere z uzlu barvu
## mlhy (mlha) a násobek okolního světla (okolni). Signál time_changed(doba, tma) jako Havran – predmety.gd on_time.

signal time_changed(key: String, night: bool)

var cfg: Dictionary = {}
var presets: Dictionary = {}
var NAMES: Dictionary = {}
var hour := 15.5
var day_n := 1
var running := true
var current := "odpoledne"
var mlha := Color(0.68, 0.75, 0.84)   # barva mlhy pro hlavni.gd _atmosfera
var okolni := 1.0                     # násobek neoblohové (teplé) složky okolního světla = poměr jasu oblohy
var okolni_e := 1.0                   # násobek síly okolního světla (Havran amb – v noci vyšší, obloha je tmavá)
var zatazeni := 0.0                   # 0..1 zatažení před deštěm a za deště (pocasi.gd)
var _poc: Dictionary = {}             # pocasi.json obloha
var svit_oken := 1.0                  # denní světlo prosvítající okny (okno.gdshader)

var slunce: DirectionalLight3D
var obloha: ShaderMaterial   # shaders/sky.gdshader (Havran)
var env: Environment
var _zakl := {}            # hodnoty Puchartu (odpoledne): slunce, obloha, mlha, přízemní mlha
var _ref := {}             # Havranův vztažný preset (odpoledne)
var _last := {}
var _from := {}
var _to := {}
var _t := 1.0
var _dur := 1.0
var _acc := 0.0
var _sun_d := Vector3.ZERO
var _rate := 24.0 / 5400.0
var okna: Array = []       # ShaderMaterial oken (hlavni.gd _okno_mat) – svit dovnitř podle dne
var hl: Node = null
var _okenni = null         # [[OmniLight3D, energie ve dne]]


func setup(sl: DirectionalLight3D, sky: ShaderMaterial, e: Environment, h: Node) -> void:
	slunce = sl; obloha = sky; env = e; hl = h
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/den.json"))
	NAMES = cfg["nazvy"]
	_rate = 24.0 / float(cfg["den_s"])
	for k: String in cfg["presety"]:
		var p: Dictionary = cfg["presety"][k]; var o := {}
		for f: String in p:
			o[f] = Color(p[f][0], p[f][1], p[f][2]) if p[f] is Array else float(p[f])
		o["night"] = k in cfg["tma"]
		presets[k] = o
	_ref = presets[String(cfg["vztazny"])]
	_zakl = {"sun": slunce.light_color, "sun_e": slunce.light_energy, "top": obloha.get_shader_parameter("zenith"), "hor": obloha.get_shader_parameter("horizon"),
		"g_hor": obloha.get_shader_parameter("horizon"), "g_bot": obloha.get_shader_parameter("ground"), "fog": env.fog_light_color, "mist": env.fog_height_density}
	var start := OS.get_environment("PUCHART_CAS")   # snímek / ladění: hodina (např. 12, 20.5) nebo název doby
	if start == "": start = String(cfg["start"])
	if presets.has(start): hour = float(cfg["klic_hodina"][start])
	else: hour = float(start)
	# snímky, testy a měření za stejných podmínek: čas stojí (měření pustí hlavni.gd po konci)
	if OS.get_environment("PUCHART_FOTO") != "" or OS.get_environment("PUCHART_TEST") != "": running = false
	_apply(state_at(hour))
	_update_key(true)


func next_key() -> String:
	var o: Array = cfg["poradi"]
	return o[(o.find(current) + 1) % o.size()]


func set_time(key: String, seconds: float = 2.5) -> void:
	if presets.has(key): set_hour(float(cfg["klic_hodina"][key]), seconds)


## Skok na hodinu (spánek, cestování, nahrání hry): když je cíl dřív než teď, začíná další den.
func set_hour(h: float, seconds: float = 2.5) -> void:
	h = fposmod(h, 24.0)
	if h < hour - 0.01 and seconds > 0.05: day_n += 1
	hour = h
	_from = _last.duplicate() if not _last.is_empty() else state_at(hour)
	_to = state_at(hour)
	_t = 0.0; _dur = maxf(seconds, 0.01)
	_update_key(true)


func key_at(h: float) -> String:
	var k := "noc"
	for u: Array in cfg["useky"]:
		if h >= float(u[0]): k = String(u[1])
	return k


func clock_text() -> String:
	var m := int(hour * 60.0)
	return "%d:%02d" % [m / 60, m % 60]


func is_night() -> bool:
	return bool(presets[current]["night"])


func _update_key(force: bool) -> void:
	var k := key_at(hour)
	if k != current or force:
		current = k
		time_changed.emit(k, is_night())


func state_at(h: float) -> Dictionary:
	var fr: Array = cfg["snimky"]
	var a: Array = fr[0]; var b: Array = fr[1]
	for i in range(fr.size() - 1):
		if h >= float(fr[i][0]) and h <= float(fr[i + 1][0]):
			a = fr[i]; b = fr[i + 1]; break
	var w := smoothstep(0.0, 1.0, (h - float(a[0])) / maxf(0.001, float(b[0]) - float(a[0])))
	return _mix(presets[a[1]], presets[b[1]], w)


func _mix(pa: Dictionary, pb: Dictionary, w: float) -> Dictionary:
	var m := {}
	for k: String in pb:
		var x = pa[k]; var y = pb[k]
		if x is bool: m[k] = y if w > 0.5 else x
		elif x is Color: m[k] = (x as Color).lerp(y, w)
		else: m[k] = lerpf(x, y, w)
	m["az"] = rad_to_deg(lerp_angle(deg_to_rad(pa["az"]), deg_to_rad(pb["az"]), w))
	return m


func _process(delta: float) -> void:
	if _t < 1.0:
		_t = minf(1.0, _t + delta / _dur)
		_apply(_mix(_from, _to, smoothstep(0.0, 1.0, _t)))
		return
	if not running or get_tree().paused: return
	hour += delta * _rate
	if hour >= 24.0:
		hour -= 24.0; day_n += 1
	_acc += delta
	if _acc >= float(cfg["obnova_s"]):
		_acc = 0.0
		_apply(state_at(hour))
		_update_key(false)


func sun_dir(p: Dictionary) -> Vector3:
	var el := deg_to_rad(p["el"]); var az := deg_to_rad(p["az"])
	return Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el)).normalized()


static func _pomer(c: Color, p: Color, r: Color) -> Color:   # hodnota Puchartu × (preset / vztažný preset) po kanálech
	return Color(c.r * p.r / maxf(r.r, 0.001), c.g * p.g / maxf(r.g, 0.001), c.b * p.b / maxf(r.b, 0.001))


static func _jas(c: Color) -> float:
	return c.r * 0.2126 + c.g * 0.7152 + c.b * 0.0722


## Zatažená obloha (pocasi.gd): slunce slábne, obloha a mraky šednou, mraky skoro celé, víc přízemní mlhy.
func _zatazit(p0: Dictionary) -> Dictionary:
	if zatazeni <= 0.001: return p0
	if _poc.is_empty(): _poc = JSON.parse_string(FileAccess.get_file_as_string("res://data/pocasi.json"))["obloha"]
	var p := p0.duplicate(); var z := zatazeni
	var sd: Array = _poc["seda"]; var seda := Color(sd[0], sd[1], sd[2]) * clampf((_jas(p["zenith"]) + _jas(p["horizon"])) / 0.9, 0.05, 1.0)
	p["sun_e"] = float(p["sun_e"]) * (1.0 - float(_poc["zatazeni_slunce"]) * z)
	p["_seda"] = seda   # obloha k šedé až po převodu na barvy Puchartu (_apply) – poměr k vztažnému presetu by šedou přebarvil
	if p.has("c_lit"): p["c_lit"] = (p["c_lit"] as Color).lerp(seda * 1.05, z); p["c_dark"] = (p["c_dark"] as Color).lerp(seda * float(_poc.get("tmave_mraky", 0.8)), z)
	if p.has("glow"): p["glow"] = float(p["glow"]) * (1.0 - z)
	if p.has("tint"): p["tint"] = (p["tint"] as Color).lerp(seda, z)
	p["mist"] = float(p["mist"]) * lerpf(1.0, float(_poc["mlha_nasobek"]), z)
	p["amb"] = float(p["amb"]) * lerpf(1.0, float(_poc["okolni"]), z)
	return p

func prekresli() -> void:   # pocasi.gd: změna zatažení – přepočet hned
	_apply(state_at(hour) if _t >= 1.0 else _mix(_from, _to, smoothstep(0.0, 1.0, _t)))

func _apply(p: Dictionary) -> void:
	_last = p   # bez zatažení (přechody set_hour mísí čisté předvolby)
	p = _zatazit(p)
	var d := sun_dir(p)
	if _sun_d == Vector3.ZERO or d.angle_to(_sun_d) > float(cfg["krok_slunce_rad"]):
		_sun_d = d
		slunce.look_at_from_position(d * 100.0, Vector3.ZERO, Vector3.UP)
	slunce.light_color = _pomer(_zakl["sun"], p["sun"], _ref["sun"])
	slunce.light_energy = float(_zakl["sun_e"]) * float(p["sun_e"]) / float(_ref["sun_e"])
	var hz: Color = p["horizon"]
	var obl_jas := _jas(p["zenith"]) + _jas(hz); var ref_jas := _jas(_ref["zenith"]) + _jas(_ref["horizon"])
	var nove := {"top": _pomer(_zakl["top"], p["zenith"], _ref["zenith"]), "hor": _pomer(_zakl["hor"], hz, _ref["horizon"]),
		"g_hor": _pomer(_zakl["g_hor"], hz, _ref["horizon"]), "g_bot": _pomer(_zakl["g_bot"], hz, _ref["horizon"])}
	if p.has("_seda"):   # zatažení (pocasi.gd)
		var sd_: Color = p["_seda"]
		for k_ in ["top", "hor", "g_hor"]: nove[k_] = (nove[k_] as Color).lerp(sd_ * (0.85 if k_ == "top" else 1.0), zatazeni)
	# obloha (a s ní odraz okolního světla) jen při znatelné změně – přepočet záře oblohy stojí i na tabletu
	if _rozdil(obloha.get_shader_parameter("zenith"), nove["top"]) > 0.004 or _rozdil(obloha.get_shader_parameter("horizon"), nove["hor"]) > 0.004 \
			or absf(_par_f("stars") - float(p.get("stars", 0.0))) > 0.01 or absf(_par_f("cloud_cover") - _kryti()) > 0.01:
		obloha.set_shader_parameter("zenith", nove["top"]); obloha.set_shader_parameter("horizon", nove["hor"])
		obloha.set_shader_parameter("ground", nove["g_bot"])
		obloha.set_shader_parameter("energy", float(p["sky_e"]))
		if not _poc.is_empty() or zatazeni > 0.0:
			if _poc.is_empty(): _poc = JSON.parse_string(FileAccess.get_file_as_string("res://data/pocasi.json"))["obloha"]
			var mk: Array = _poc["mraky_kryti"]; obloha.set_shader_parameter("cloud_cover", lerpf(float(mk[0]), float(mk[1]), zatazeni))
		for k_: String in ["tint", "glow", "c_lit", "c_dark", "stars"]:   # Havran daylight._apply: záře, mraky, hvězdy
			if p.has(k_): obloha.set_shader_parameter({"tint": "sun_tint", "glow": "sun_glow", "c_lit": "cloud_lit", "c_dark": "cloud_dark", "stars": "stars"}[k_], p[k_])
	mlha = _pomer(_zakl["fog"], p["fog"], _ref["fog"])
	env.fog_height_density = float(_zakl["mist"]) * float(p["mist"]) / float(_ref["mist"])
	okolni_e = float(p["amb"]) / float(_ref["amb"])
	okolni = obl_jas / ref_jas   # síla × tato barva = amb × jas oblohy jako u Havrana (den.json okolni_pozn)
	svit_oken = clampf(okolni * okolni_e, 0.0, 1.0)
	for m: ShaderMaterial in okna: m.set_shader_parameter("svit", svit_oken)
	# denní světlo z oken (svetla.json den) v noci zhasne – světla označená v hlavni.gd _svetla metou „den_svetlo“
	if _okenni == null and hl and hl.get_node_or_null("Hrad"):
		_okenni = []
		for l in hl.get_node("Hrad").get_children():
			if l is OmniLight3D and l.has_meta("den_svetlo"): _okenni.append([l, (l as OmniLight3D).light_energy])
	if _okenni != null:
		for z: Array in _okenni:
			(z[0] as OmniLight3D).light_energy = float(z[1]) * svit_oken; (z[0] as OmniLight3D).visible = svit_oken > 0.05


static func _rozdil(a: Color, b: Color) -> float:
	return absf(a.r - b.r) + absf(a.g - b.g) + absf(a.b - b.b)


func _par_f(jm: String) -> float:   # parametr shaderu oblohy (nenastavený = null → výchozí 0)
	var v = obloha.get_shader_parameter(jm)
	return 0.0 if v == null else float(v)

func _kryti() -> float:
	if _poc.is_empty(): return _par_f("cloud_cover")
	var mk: Array = _poc["mraky_kryti"]; return lerpf(float(mk[0]), float(mk[1]), zatazeni)
