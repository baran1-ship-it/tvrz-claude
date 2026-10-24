extends Node3D
## Slapaci jerab v lomu (Misa 24. 10. "pridej kladkostroj a udelej jerab funkcni"): hrac sesla do kola
## a kvadr vytahne nahoru nebo spusti dolu. Kolo 4,3 m, buben r 0,255 m, kladkostroj se dvema prameny:
## kvadr stoupa o polovinu navinuteho lana (kolo o radian = 0,128 m). Slapani 0,8 m/s po obvodu kola.
## Pohyblive dily jsou samostatne modely (<id>_kolo / _kladnice / _lano) s pocatkem v pivotu;
## pivoty v souradnicich modelu jsou v katalogu ("dily").

const R_KOLO := 2.15
const SLAPANI := 0.8                 # m/s po obvodu kola
var _kolo: Node3D
var _kladnice: Node3D
var _lana: Array[Node3D] = []
var _horni: Array[Vector3] = []
var _r_buben := 0.255
var _y0 := 0.0                       # pivot kladnice, kvadr lezi na zemi
var _y_max := 0.0
var h := 1.0                         # zdvih nad zemi (m); v klidu kvadr visi 1 m nad zemi (radce 17:55)
var cil := 1.0
var _krok := 0.0
var _vrz := 2.0
var _t := 0.0


func setup(id: String, info: Dictionary, predmety: Node) -> void:
	var dily: Dictionary = info["dily"]
	var dir := "res://modely/predmety/" + id + "_"
	_kolo = (load(dir + "kolo.glb") as PackedScene).instantiate()
	_kolo.position = _v(dily["kolo"]["pivot"])
	_r_buben = float(dily["kolo"].get("r_buben", 0.255))
	add_child(_kolo)
	_kladnice = (load(dir + "kladnice.glb") as PackedScene).instantiate()
	_kladnice.position = _v(dily["kladnice"]["pivot"])
	add_child(_kladnice)
	for hp: Array in dily["lano"]["horni"]:
		_horni.append(_v(hp))
		var l: Node3D = (load(dir + "lano.glb") as PackedScene).instantiate()
		l.position = _v(hp)
		add_child(l)
		_lana.append(l)
	_y0 = _kladnice.position.y
	_y_max = _horni[0].y - 0.75 - _y0
	# kvadr na zemi i na svahu: pivot nad terenem pod kladnici
	if predmety.main and predmety.main.svet:
		var gp := (get_parent() as Node3D).to_global(_kladnice.position)
		var zem: float = predmety.main.svet._vyska(gp.x, gp.z)
		var dno := float(dily["kladnice"].get("dno", 1.6))
		_y0 = (get_parent() as Node3D).to_local(Vector3(gp.x, zem + dno + 0.03, gp.z)).y
		_y_max = _horni[0].y - 0.75 - _y0
	if OS.has_environment("TVRZ_JERAB_H"):            # snimek: kvadr zvednuty o h m
		h = minf(float(OS.get_environment("TVRZ_JERAB_H")), _y_max)
		cil = h
	_uloz()


func _jede() -> bool:
	return absf(cil - h) > 0.0005


func _v(a: Array) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func label() -> String:
	if _jede():
		return "Zastavit kolo"
	return "Šlapat v kole – zvednout kámen" if h < _y_max * 0.5 else "Šlapat v kole – spustit kámen"


func prepni() -> void:
	if _jede():
		cil = h                                   # zastavit
	else:
		cil = _y_max if h < _y_max * 0.5 else 0.0
	set_process(true)


func _ready() -> void:
	set_process(false)


func _process(dt: float) -> void:
	var v := SLAPANI / R_KOLO * _r_buben * 0.5      # rychlost kvadru (m/s)
	var d := clampf(cil - h, -v * dt, v * dt)
	h += d
	_t += dt
	_uloz()
	var pos := global_position + global_basis * _kolo.position
	_krok -= dt
	if _krok <= 0.0 and main_life():
		_krok = 0.62
		main_life().sfx("krok_drevo", -16.0, 0.85, pos)
	_vrz -= dt
	if _vrz <= 0.0 and main_life():
		_vrz = randf_range(2.5, 5.0)
		main_life().sfx("dvere_otevrit", -20.0, randf_range(0.5, 0.65), pos)
	if not _jede():
		h = cil
		_uloz()
		set_process(false)


func main_life() -> Node:
	var m = get_tree().root.get_node_or_null("Main")
	return m.life if m else null


func _uloz() -> void:
	# lano na bubnu: dva prameny -> buben navine 2 h; kolo se toci kolem osy hridele (z modelu)
	_kolo.rotation.z = 2.0 * h / _r_buben
	var y := _y0 + h
	_kladnice.position.y = y
	_kladnice.rotation.z = sin(_t * 1.7) * 0.015 if _jede() else 0.0
	for i in _lana.size():
		var top: Vector3 = _horni[i]
		# prameny konci na kotouci kladnice (r 0,14) po stranach
		_lana[i].scale = Vector3(1.0, maxf(0.05, top.y - y), 1.0)
