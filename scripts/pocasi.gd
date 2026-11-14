extends Node3D
const Pravidla := preload("res://scripts/pravidla.gd")
## Pocasi - dest (prevzato z Pucharta 13. 11., commit 6d4c1b0e; Misa: „u Pucharta je pripravena zmena pocasi, vem si ji i
## pro Havrana“). Cisla v pravidla/svet/pocasi.json. Rozvrh deterministicky podle cisla dne (daylight day_n, hour) - stejny
## po nahrani hry, nic se neuklada: zatahovani (obloha sedne) -> mrholeni -> vrchol -> dozniva -> osychani (mokro).
## Vzhled: zavoj kapek na dvou valcich kolem kamery (shaders/dest.gdshader, bez cteni obrazovky - pravidlo tabletu),
## drobne odstriky u hrace, zatazena obloha (daylight.zatazeni), mokre povrchy (uniform „mokro“ v shaderech, ktere ho maji),
## zvuk venku / ze strechy (paprsek nad kamerou jako Puchart). TVRZ_DEST=0..1 vynuti silu (snimky, mereni).

var main: Node
var day: Node
var P: Dictionary = {}
var sila := 0.0          # 0..1 kapky a zvuk
var zatazeni := 0.0      # 0..1 obloha
var mokro := 0.0         # 0..1 povrchy
var vynuceno := -1.0
var _vrstvy: Array = []  # [MeshInstance3D, ShaderMaterial]
var _dopady: CPUParticles3D
var _zv_venku: AudioStreamPlayer
var _zv_strecha: AudioStreamPlayer
var _uvnitr := 0.0       # 0 venku .. 1 pod strechou (plynule)
var _uvnitr_cil := 0.0
var _t_paprsek := 0.0
var _mat_mokro: Array = []
var _posl_mokro := -1.0
var _posl_st := -1.0
var _posl_zat := -1.0
var _sh_mokro := {}      # Shader -> ma uniform dest_mokro (kontrolni sber 13. 11.: kod shaderu jen jednou)


func setup(m: Node, d: Node) -> void:
	main = m
	day = d
	P = Pravidla.soubor("pocasi")
	for k: String in ["rozestup_dni", "start_hodina", "trvani_h", "sila", "zatahovani_h", "doznivani_h", "osychani_h", "mokro", "prechod_uvnitr_s", "strecha_m", "strecha_kontrola_s", "sber_uzlu_snimek"]:
		Pravidla.cti("pocasi", k)                   # zapis cteni (test pravidla_cteni); dal z P
	if OS.has_environment("TVRZ_DEST"):
		vynuceno = float(OS.get_environment("TVRZ_DEST"))
	if not bool(Pravidla.cti("pocasi", "zapnuto")) and vynuceno < 0.0:
		set_process(false)
		return
	var k: Dictionary = Pravidla.cti("pocasi", "kapky")
	for i in (k["vrstvy"] as Array).size():
		var rv: Array = k["vrstvy"][i]
		var cm := CylinderMesh.new()
		cm.top_radius = float(rv[0])
		cm.bottom_radius = float(rv[0])
		cm.height = float(rv[1])
		cm.radial_segments = 24
		cm.rings = 1
		cm.cap_top = false
		cm.cap_bottom = false
		var sm := ShaderMaterial.new()
		sm.shader = load("res://shaders/dest.gdshader")
		sm.set_shader_parameter("hustota", float(k["hustota"][i]))
		sm.set_shader_parameter("rychlost", float(k["rychlost"][i]))
		sm.set_shader_parameter("delka", float(k["delka"][i]))
		sm.set_shader_parameter("jas", float(k["jas"][i]))
		var mi := MeshInstance3D.new()
		mi.mesh = cm
		mi.material_override = sm
		mi.top_level = true
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.extra_cull_margin = float(rv[1])
		mi.visible = false
		add_child(mi)
		_vrstvy.append([mi, sm])
	var dp: Dictionary = Pravidla.cti("pocasi", "dopady")
	_dopady = CPUParticles3D.new()
	_dopady.top_level = true
	_dopady.emitting = false
	_dopady.amount = int(dp["pocet"])
	_dopady.lifetime = float(dp["zivot_s"])
	_dopady.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	var pl := float(dp["plocha_m"])
	_dopady.emission_box_extents = Vector3(pl, 0.05, pl)
	_dopady.direction = Vector3.UP
	_dopady.spread = float(dp["rozptyl_st"])
	_dopady.initial_velocity_min = float(dp["rychlost_m_s"][0])
	_dopady.initial_velocity_max = float(dp["rychlost_m_s"][1])
	var qm := QuadMesh.new()
	qm.size = Vector2(float(dp["velikost_m"][0]), float(dp["velikost_m"][1]))
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	var b: Array = dp["barva"]
	mat.albedo_color = Color(float(b[0]), float(b[1]), float(b[2]), float(b[3]))
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	qm.material = mat
	_dopady.mesh = qm
	_dopady.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_dopady)
	var z: Dictionary = Pravidla.cti("pocasi", "zvuk")
	_zv_venku = _smycka(String(z["venku"]))
	_zv_strecha = _smycka(String(z["strecha"]))


func _smycka(cesta: String) -> AudioStreamPlayer:
	var a: AudioStream = (load(cesta) as AudioStream).duplicate()
	if a is AudioStreamOggVorbis:
		(a as AudioStreamOggVorbis).loop = true
	var p := AudioStreamPlayer.new()
	p.stream = a
	p.bus = "Zvuky"
	p.volume_db = -80.0
	add_child(p)
	return p


## Materialy s parametrem „dest_mokro“ (trasa 0.999995: sber pres celou scenu najednou = zasek 357 ms na zacatku deste):
## pruchod stromu po castech - nejvys sber_uzlu_snimek uzlu za snimek, zacina pri zatahovani (pred kapkami), nalezeny
## material dostane hned aktualni mokro. Po dokonceni znovu pri dalsim destu (bunky kolem hrace se mohly pridat).
var _sber_fronta: Array = []          # uzly k prohledani (zasobnik)
var _sber_videno := {}
var _sber_hotov := false


func _sber_zacni() -> void:
	_mat_mokro.clear()
	_sber_videno.clear()
	_sber_fronta = [main]
	_sber_hotov = false


func _sber_krok() -> void:
	var n_max := int(P["sber_uzlu_snimek"])
	var pv: Array = (P["mokro"] as Dictionary)["povrch"]
	var n := 0
	while n < n_max and not _sber_fronta.is_empty():
		var u: Node = _sber_fronta.pop_back()
		n += 1
		if not is_instance_valid(u):
			continue
		for ch: Node in u.get_children():
			_sber_fronta.append(ch)
		if not (u is GeometryInstance3D):
			continue
		var g := u as GeometryInstance3D
		var ms: Array = [g.material_override]
		if g is MeshInstance3D and (g as MeshInstance3D).mesh:
			for si in (g as MeshInstance3D).get_surface_override_material_count():
				ms.append((g as MeshInstance3D).get_surface_override_material(si))
			for si in (g as MeshInstance3D).mesh.get_surface_count():
				ms.append((g as MeshInstance3D).mesh.surface_get_material(si))
		for m: Variant in ms:
			if not (m is ShaderMaterial) or _sber_videno.has(m):
				continue
			_sber_videno[m] = true
			var sh: Shader = (m as ShaderMaterial).shader
			if sh == null:
				continue
			if not _sh_mokro.has(sh):
				_sh_mokro[sh] = "uniform float dest_mokro" in sh.code
			if _sh_mokro[sh]:
				_mat_mokro.append(m)
				(m as ShaderMaterial).set_shader_parameter("dest_povrch", Vector3(float(pv[0]), float(pv[1]), float(pv[2])))
				(m as ShaderMaterial).set_shader_parameter("dest_mokro", _mokro_pro(m as ShaderMaterial))
	if _sber_fronta.is_empty():
		_sber_hotov = true


func _mokro_pro(m: ShaderMaterial) -> float:
	return maxf(_posl_st, 0.0) if (P["mokro"]["stavby_shadery"] as Array).has(m.shader.resource_path) else maxf(_posl_mokro, 0.0)


## Den d je destivy, kdyz na nej padne rada rozestupu (rozestup_dni); zacatek, delka a sila ze semínka dne.
func _dest_dne(d: int) -> Dictionary:
	var rz: Array = P["rozestup_dni"]
	var dd := int(rz[0]) + int(_h(0.5) * (int(rz[1]) - int(rz[0]) + 1))
	while dd < d:
		dd += int(rz[0]) + int(_h(float(dd)) * (int(rz[1]) - int(rz[0]) + 1))
	if dd != d:
		return {}
	var sh: Array = P["start_hodina"]
	var tr: Array = P["trvani_h"]
	var si: Array = P["sila"]
	return {"start": lerpf(float(sh[0]), float(sh[1]), _h(d * 1.31)), "trvani": lerpf(float(tr[0]), float(tr[1]), _h(d * 2.17)),
		"sila": lerpf(float(si[0]), float(si[1]), _h(d * 3.7))}


static func _h(x: float) -> float:
	return fposmod(sin(x * 91.345 + 3.1) * 43758.5453, 1.0)


## Stav v case t (hodiny od zacatku hry): [zatazeni, sila kapek, mokro]
func stav(t: float) -> Vector3:
	var za := float(P["zatahovani_h"])
	var do_ := float(P["doznivani_h"])
	var os_ := float(P["osychani_h"])
	var nab := float((P["mokro"] as Dictionary)["nabeh_h"])
	var v := Vector3.ZERO
	var d0 := int(floor(t / 24.0)) + 1
	for d in [d0 - 1, d0, d0 + 1]:  # dest muze zacit vecer a prejit pres pulnoc; zatahovani pred destem tesne po pulnoci
		if d < 1:
			continue
		var r := _dest_dne(d)
		if r.is_empty():
			continue
		var s := (float(d) - 1.0) * 24.0 + float(r["start"])
		var e := s + float(r["trvani"])
		var zz := smoothstep(s - za, s, t) * (1.0 - smoothstep(e, e + do_, t))
		var kk := float(r["sila"]) * smoothstep(s, s + 0.25, t) * (1.0 - smoothstep(e - 0.1, e + do_, t))
		var mm := smoothstep(s, s + nab, t) * (1.0 - smoothstep(e + do_, e + do_ + os_, t))
		v = Vector3(maxf(v.x, zz), maxf(v.y, kk), maxf(v.z, mm))
	return v


func _process(dt: float) -> void:
	var t_us := Time.get_ticks_usec()
	_krok(dt)
	var dg: Object = Engine.get_meta("diag", null)
	if dg:
		dg.cas("pocasi", Time.get_ticks_usec() - t_us)


func _krok(dt: float) -> void:
	var st: Vector3
	if vynuceno >= 0.0:
		st = Vector3(minf(1.0, vynuceno * 1.5), vynuceno, vynuceno)
	else:
		st = stav((float(day.day_n) - 1.0) * 24.0 + float(day.hour))
	zatazeni = st.x
	sila = st.y
	mokro = st.z
	# kontrola 13. 11.: konecnou 0 (a 1) propsat vzdy - jinak zatazeni zustalo tesne nad nulou a obloha se prepocitavala dal
	if absf(zatazeni - _posl_zat) > 0.02 or (zatazeni <= 0.0 and _posl_zat > 0.0) or (zatazeni >= 1.0 and _posl_zat < 1.0):
		_posl_zat = zatazeni
		day.zatazeni = zatazeni
		day.prekresli()
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	_t_paprsek -= dt
	if _t_paprsek <= 0.0 and (sila > 0.001 or mokro > 0.001):
		_t_paprsek = float(P["strecha_kontrola_s"])
		var q := PhysicsRayQueryParameters3D.create(cam.global_position, cam.global_position + Vector3.UP * float(P["strecha_m"]))
		var sv: Object = main.get("svet")
		_uvnitr_cil = 0.0 if get_world_3d().direct_space_state.intersect_ray(q).is_empty() and not (sv and sv.pod_strechou(cam.global_position)) else 1.0
	_uvnitr = move_toward(_uvnitr, _uvnitr_cil, dt / float(P["prechod_uvnitr_s"]))
	var venku := sila * (1.0 - _uvnitr)
	var p := cam.global_position
	for v: Array in _vrstvy:
		var mi: MeshInstance3D = v[0]
		mi.visible = venku > 0.004
		if mi.visible:
			mi.global_position = p
			(v[1] as ShaderMaterial).set_shader_parameter("sila", venku)
	var dp: Dictionary = P["dopady"]
	_dopady.emitting = venku > float(dp["od_sily"])
	if _dopady.emitting:
		var hr: Node3D = main.get("player")
		_dopady.global_position = (hr.global_position if hr else p - Vector3.UP * 1.6) + Vector3.UP * 0.02
	var db0 := float((P["zvuk"] as Dictionary)["db_max"])
	_hlas(_zv_venku, clampf(sila * 2.0, 0.0, 1.0) * (1.0 - _uvnitr), db0)
	_hlas(_zv_strecha, clampf(sila * 2.0, 0.0, 1.0) * _uvnitr, db0)
	# sber materialu po castech: zacne se zatahovanim (pred kapkami a mokrem), skonci, az projde cely strom
	if (zatazeni > 0.001 or mokro > 0.001) and _sber_fronta.is_empty() and not _sber_hotov:
		_sber_zacni()
	if not _sber_fronta.is_empty():
		_sber_krok()
	if zatazeni <= 0.0 and mokro <= 0.0 and _sber_hotov:
		_sber_hotov = false                  # pristi dest sbira znovu
	var mk_st := mokro * (1.0 - float((P["mokro"] as Dictionary)["stavby_uvnitr"]) * _uvnitr)
	if absf(mokro - _posl_mokro) > 0.02 or absf(mk_st - _posl_st) > 0.02 or (mokro <= 0.0 and _posl_mokro > 0.0) or (mk_st <= 0.0 and _posl_st > 0.0):
		_posl_mokro = mokro
		_posl_st = mk_st
		for m: ShaderMaterial in _mat_mokro:
			m.set_shader_parameter("dest_mokro", mk_st if (P["mokro"]["stavby_shadery"] as Array).has(m.shader.resource_path) else mokro)


func _hlas(p: AudioStreamPlayer, h: float, db0: float) -> void:
	if h <= 0.001:
		if p.playing:
			p.stop()
		return
	p.volume_db = db0 + linear_to_db(h)
	if not p.playing:
		p.play()
