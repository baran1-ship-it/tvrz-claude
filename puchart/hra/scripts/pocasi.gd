extends Node3D
## Počasí – déšť (Míša 12. 11.: „déšť jednou za 4 dny, nemusí to být celý den“; „co nejlepší efekt, ať to vypadá reálně, ale
## nezasekat tablet“). Data hra/data/pocasi.json (pravidla/svet/pocasi.json, rešerše docs/reference/reserse_dest_kcd.md).
## Rozvrh deterministicky podle čísla dne (den.gd day_n, hour) – stejný po nahrání hry, nic se neukládá:
##   zatahování (obloha šedne) → mrholení → vrchol → doznívání → osychání (mokré povrchy).
## Vzhled jako KCD: závoj kapek na dvou válcích kolem kamery (shaders/dest.gdshader), drobné odstřiky u hráče, zatažená
## obloha a mlha (den.gd zatazeni), mokré povrchy (uniform „mokro“ v zem/zdivo/skala/textura), zvuk deště – pod střechou
## bez kapek a tlumeně (paprsek nad kamerou). Výkon: 2 průhledné vrstvy, 1 emitor částic, žádné nové světlo ani stín.
## PUCHART_DEST=0..1 vynutí sílu deště (snímky, měření varianta „déšť“).

var cfg: Dictionary = {}
var den: Node = null
var sila := 0.0          # 0..1 – kapky a zvuk
var zatazeni := 0.0      # 0..1 – obloha
var mokro := 0.0         # 0..1 – povrchy (náběh a osychání)
var vynuceno := -1.0     # ≥ 0: pevná síla (test, měření)
var _vrstvy: Array = []  # [MeshInstance3D, ShaderMaterial]
var _dopady: CPUParticles3D
var _zv_slaby: AudioStreamPlayer
var _zv_silny: AudioStreamPlayer
var _bus := -1
var _uvnitr := 0.0       # 0 venku .. 1 pod střechou (plynule)
var _t_paprsek := 0.0
var _mat_mokro: Array = []
var _t_mokro := 0.0
var _posl_mokro := -1.0
var _posl_zat := -1.0
var _posl_st := -1.0


func setup(d: Node) -> void:
	den = d
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/pocasi.json"))
	if OS.get_environment("PUCHART_DEST") != "": vynuceno = float(OS.get_environment("PUCHART_DEST"))
	var k: Dictionary = cfg["kapky"]
	for i in (k["vrstvy"] as Array).size():
		var rv: Array = k["vrstvy"][i]
		var cm := CylinderMesh.new(); cm.top_radius = float(rv[0]); cm.bottom_radius = float(rv[0]); cm.height = float(rv[1])
		cm.radial_segments = 24; cm.rings = 1; cm.cap_top = false; cm.cap_bottom = false
		var m := ShaderMaterial.new(); m.shader = load("res://shaders/dest.gdshader")
		m.set_shader_parameter("hustota", float(k["hustota"][i])); m.set_shader_parameter("rychlost", float(k["rychlost"][i]))
		m.set_shader_parameter("delka", float(k["delka"][i])); m.set_shader_parameter("jas", float(k["jas"][i]))
		var mi := MeshInstance3D.new(); mi.mesh = cm; mi.material_override = m; mi.top_level = true
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; mi.extra_cull_margin = 50.0; mi.visible = false
		add_child(mi); _vrstvy.append([mi, m])
	# odstřiky dopadů kolem hráče: malé světlé čárky, krátký život, bez stínu
	var dp: Dictionary = cfg["dopady"]
	_dopady = CPUParticles3D.new(); _dopady.top_level = true; _dopady.emitting = false; _dopady.amount = int(dp["pocet"])
	_dopady.lifetime = 0.25; _dopady.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	var pl := float(dp["plocha_m"]); _dopady.emission_box_extents = Vector3(pl, 0.05, pl)
	_dopady.direction = Vector3.UP; _dopady.spread = 35.0; _dopady.initial_velocity_min = 0.6; _dopady.initial_velocity_max = 1.4
	_dopady.gravity = Vector3(0, -9.8, 0); _dopady.scale_amount_min = 0.5; _dopady.scale_amount_max = 1.0
	var qm := QuadMesh.new(); qm.size = Vector2(0.015, 0.04)
	var sm := StandardMaterial3D.new(); sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; sm.albedo_color = Color(0.8, 0.84, 0.88, 0.3)
	sm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED; qm.material = sm
	_dopady.mesh = qm; _dopady.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_dopady)
	# zvuk: dvě smyčky (slabý / silný) prolínané podle síly, vlastní sběrnice s dolní propustí (uvnitř tlumený)
	_bus = AudioServer.bus_count; AudioServer.add_bus(_bus); AudioServer.set_bus_name(_bus, "Dest")
	var lp := AudioEffectLowPassFilter.new(); lp.cutoff_hz = 20000.0; AudioServer.add_bus_effect(_bus, lp)
	var z: Dictionary = cfg["zvuk"]
	_zv_slaby = _smycka(String(z["slaby"])); _zv_silny = _smycka(String(z["silny"]))
	call_deferred("_sber_materialu")


func _smycka(cesta: String) -> AudioStreamPlayer:
	var a: AudioStreamOggVorbis = (load(cesta) as AudioStreamOggVorbis).duplicate(); a.loop = true
	var p := AudioStreamPlayer.new(); p.stream = a; p.bus = "Dest"; p.volume_db = -80.0; add_child(p); return p


## Materiály s parametrem „mokro“ (zem, zdivo, skála, textura) – jednou po načtení světa, znovu při začátku deště
## (buňky kolem hráče se mohly přidat); nastavuje se jen při změně o víc než 0,02.
func _sber_materialu() -> void:
	_mat_mokro.clear(); var videno := {}
	for mi in get_tree().current_scene.find_children("*", "GeometryInstance3D", true, false):
		var g := mi as GeometryInstance3D
		var ms: Array = [g.material_override]
		if g is MeshInstance3D and (g as MeshInstance3D).mesh:
			for s in (g as MeshInstance3D).get_surface_override_material_count(): ms.append((g as MeshInstance3D).get_surface_override_material(s))
			for s in (g as MeshInstance3D).mesh.get_surface_count(): ms.append((g as MeshInstance3D).mesh.surface_get_material(s))
		for m in ms:
			if m is ShaderMaterial and not videno.has(m) and (m as ShaderMaterial).shader and "mokro" in String((m as ShaderMaterial).shader.code):
				videno[m] = true; _mat_mokro.append(m)
	_posl_mokro = -1.0


## Rozvrh: den d je deštivý, když na něj padne řada rozestupů 2–6 dní (od dne 1); začátek a délka ze semínka dne.
func _dest_dne(d: int) -> Dictionary:
	var rz: Array = cfg["rozestup_dni"]; var dd := 1 + int(_h(0.5) * (int(rz[1]) - int(rz[0]) + 1)) + int(rz[0]) - 1
	while dd < d: dd += int(rz[0]) + int(_h(float(dd)) * (int(rz[1]) - int(rz[0]) + 1))
	if dd != d: return {}
	var sh: Array = cfg["start_hodina"]; var tr: Array = cfg["trvani_h"]; var si: Array = cfg["sila"]
	return {"start": lerpf(float(sh[0]), float(sh[1]), _h(d * 1.31)), "trvani": lerpf(float(tr[0]), float(tr[1]), _h(d * 2.17)),
		"sila": lerpf(float(si[0]), float(si[1]), _h(d * 3.7))}

static func _h(x: float) -> float: return fposmod(sin(x * 91.345 + 3.1) * 43758.5453, 1.0)


## Stav počasí v čase t (hodiny od začátku hry): [zatažení, síla kapek, mokro]
func stav(t: float) -> Vector3:
	var za := float(cfg["zatahovani_h"]); var do_ := float(cfg["doznivani_h"]); var os_ := float(cfg["osychani_h"])
	var v := Vector3.ZERO
	var d0 := int(floor(t / 24.0)) + 1
	for d in [d0 - 1, d0]:   # déšť může začít večer a přejít přes půlnoc
		if d < 1: continue
		var r := _dest_dne(d)
		if r.is_empty(): continue
		var s := (float(d) - 1.0) * 24.0 + float(r["start"]); var e := s + float(r["trvani"])
		var z := smoothstep(s - za, s, t) * (1.0 - smoothstep(e, e + do_, t))
		var k := float(r["sila"]) * smoothstep(s, s + 0.25, t) * (1.0 - smoothstep(e - 0.1, e + do_, t))
		var m := smoothstep(s, s + float(cfg["mokro"]["nabeh_h"]), t) * (1.0 - smoothstep(e + do_, e + do_ + os_, t))
		v = Vector3(maxf(v.x, z), maxf(v.y, k), maxf(v.z, m))
	return v


func _process(dt: float) -> void:
	if den == null: return
	var st: Vector3
	if vynuceno >= 0.0: st = Vector3(minf(1.0, vynuceno * 1.5), vynuceno, vynuceno)
	else: st = stav((float(den.day_n) - 1.0) * 24.0 + float(den.hour))
	zatazeni = st.x; sila = st.y; mokro = st.z
	if absf(zatazeni - _posl_zat) > 0.02:   # obloha (den.gd) jen při znatelné změně
		_posl_zat = zatazeni; den.zatazeni = zatazeni; den.prekresli()
	var cam := get_viewport().get_camera_3d()
	if cam == null: return
	# pod střechou? paprsek nahoru po 0,25 s, plynulý přechod
	_t_paprsek -= dt
	if _t_paprsek <= 0.0 and (sila > 0.001 or mokro > 0.001):
		_t_paprsek = 0.25
		var q := PhysicsRayQueryParameters3D.create(cam.global_position, cam.global_position + Vector3.UP * float(cfg["strecha_m"]))
		_uvnitr_cil = 0.0 if get_world_3d().direct_space_state.intersect_ray(q).is_empty() else 1.0
	_uvnitr = move_toward(_uvnitr, _uvnitr_cil, dt * 2.0)
	var venku := sila * (1.0 - _uvnitr)
	var p := cam.global_position
	for v in _vrstvy:
		var mi: MeshInstance3D = v[0]
		mi.visible = venku > 0.004
		if mi.visible:
			mi.global_position = p; (v[1] as ShaderMaterial).set_shader_parameter("sila", venku)
	_dopady.emitting = venku > 0.15
	if _dopady.emitting:
		var hr: Node3D = get_tree().current_scene.get("hrac")
		_dopady.global_position = (hr.global_position if hr else p - Vector3.UP * 1.6) + Vector3.UP * 0.02
		_dopady.speed_scale = 1.0   # počet částic pevný (CPUParticles3D nemá amount_ratio); síla řídí viditelnost kapek
	# zvuk: slabý od mrholení, silný přibývá s lijákem; uvnitř tišší a tlumený
	var z: Dictionary = cfg["zvuk"]; var db0 := float(z["db_max"]) + float(z["uvnitr_db"]) * _uvnitr
	_hlas(_zv_slaby, clampf(sila * 2.0, 0.0, 1.0), db0)
	_hlas(_zv_silny, clampf(sila * 1.4 - 0.4, 0.0, 1.0), db0)
	var lp := AudioServer.get_bus_effect(_bus, 0) as AudioEffectLowPassFilter
	lp.cutoff_hz = lerpf(20000.0, float(z["uvnitr_lowpass_hz"]), _uvnitr)
	# mokré povrchy
	if mokro > 0.001 and _posl_mokro <= 0.001: _sber_materialu()
	# uvnitř budov dřevo a zdivo mokré nejsou (stejný materiál je venku i uvnitř): mokro staveb slábne, když je hráč pod střechou
	var mk_st := mokro * (1.0 - 0.9 * _uvnitr)
	if absf(mokro - _posl_mokro) > 0.02 or absf(mk_st - _posl_st) > 0.02:
		_posl_mokro = mokro; _posl_st = mk_st
		for m in _mat_mokro:
			var sm_ := m as ShaderMaterial; var stavba := sm_.shader.resource_path.ends_with("zdivo.gdshader") or sm_.shader.resource_path.ends_with("textura.gdshader")
			sm_.set_shader_parameter("mokro", mk_st if stavba else mokro)

var _uvnitr_cil := 0.0

func _hlas(p: AudioStreamPlayer, h: float, db0: float) -> void:
	if h <= 0.001:
		if p.playing: p.stop()
		return
	p.volume_db = db0 + linear_to_db(h)
	if not p.playing: p.play()
