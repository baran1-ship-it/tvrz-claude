extends Node
## Hrac a voda: paprsek shora na hladiny (Area3D z svet.gd) zjisti, jestli hrac stoji ve vode a jak hluboko.
## Ve vode se kolem nohou hladina ceri, kazdy krok pusti kruhove vlnky (pri behu silnejsi), kroky clapou.
## Spolecne kruhove vlnky (8 naraz) pro vsechny vody - pouziva i life.gd (zaby, ryby v prikopu).

var main: Node
var ve_vode := false
var hloubka := 0.0
var _rips: Array = []
var _rip_i := 0
var _t := 0.0
var _last := Vector3.ZERO


func setup(p_main: Node) -> void:
	main = p_main
	for i in 8:
		_rips.append(Vector4.ZERO)


func _cas() -> float:
	return fmod(Time.get_ticks_msec() / 1000.0, 3600.0)


func vlna(x: float, z: float, sila: float) -> void:
	_rips[_rip_i] = Vector4(x, z, _cas(), sila)
	_rip_i = (_rip_i + 1) % _rips.size()
	for m: ShaderMaterial in main.svet.vodni:
		m.set_shader_parameter("rip", _rips)


## Misa 0.89 (rybnik, tablet fyzika 43-63 ms): cas tohoto skriptu ve fyzice zvlast do diag (detail, nesecte se)
func _physics_process(dt: float) -> void:
	var t0 := Time.get_ticks_usec()
	_fyz_krok(dt)
	var dg: Object = Engine.get_meta("diag", null)
	if dg:
		dg.cas("fyz: voda", Time.get_ticks_usec() - t0)


func _fyz_krok(dt: float) -> void:
	var pl: Node3D = main.player
	if pl == null or main.svet == null or main.svet.vodni.is_empty():
		return
	var p := pl.global_position
	var q := PhysicsRayQueryParameters3D.create(p + Vector3(0, 2.0, 0), p + Vector3(0, -0.3, 0), main.svet.VRSTVA_VODA)
	q.collide_with_areas = true
	q.collide_with_bodies = false
	var h := pl.get_world_3d().direct_space_state.intersect_ray(q)
	var bylo := ve_vode
	ve_vode = false
	if not h.is_empty():
		hloubka = (h["position"] as Vector3).y - p.y
		ve_vode = hloubka > 0.02 and hloubka < 1.9
	var sila := 0.0
	if ve_vode:
		var v := Vector2(p.x - _last.x, p.z - _last.z).length() / maxf(dt, 1e-3)
		sila = clampf(0.45 + v * 0.12, 0.45, 1.0)
		_t -= dt
		if _t <= 0.0:
			# chuze: vlna kazdy krok, stani: obcas slabe (prestupovani)
			_t = 0.32 if v > 0.5 else 1.4
			vlna(p.x, p.z, clampf(0.35 + v * 0.18, 0.25, 1.2))
		if not bylo:
			vlna(p.x, p.z, 1.3)            # vstup do vody: silny kruh
	for m: ShaderMaterial in main.svet.vodni:
		m.set_shader_parameter("hrac", Vector4(p.x, p.z, 0.22 + clampf(hloubka, 0.0, 1.0) * 0.12, sila if ve_vode else 0.0))
	_last = p
