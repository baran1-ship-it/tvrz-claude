extends SkeletonModifier3D
## Kun nikdy nestoji jako socha (Misa 0.99 „kun stal v pozici behu, vubec se nepohnul“; reserse_potok_1osoba_kun.md:
## volny kun se pase aspon 60 % casu, odlehcuje nohu, svihne ocasem pres 45 st., hybe usima, dycha). Model kun_hnedak
## ma jednu animaci bez pastvy (krk se v useku „Eat“ pohne o 3 st.) - pohyby navic po animaci (SkeletonModifier3D):
## dech (hrbet), ocas (kyvani + svihnuti), usi, pohozeni hlavou, prenaseni vahy a pastva (krk a hlava dolu, zvykani).
## Cisla z pravidla/svet/jizda.json kun.zivy. Kun (kun.gd) nastavuje stoji / volny.

const Pravidla := preload("res://scripts/pravidla.gd")
static var Z: Dictionary = Pravidla.cti("jizda", "kun", "zivy")

var stoji := true                # kun stoji (rychlost ~0)
var volny := true                # bez jezdce (jen volny kun se pase)
var _t := 0.0
var _kosti := {}                 # skupina -> [index kosti]
var _bok := Vector3.RIGHT        # vodorovna osa napric kone (soustava kostry)
var _pastva := 0.0               # 0..1 hlava dole
var _pastva_cil := 0.0
var _pastva_t := 0.0
var _ocas := 0.0                 # svihnuti ocasem (0..1, dobiha)
var _ocas_smer := 1.0
var _ocas_t := 0.0
var _usi := [0.0, 0.0]
var _usi_cil := [0.0, 0.0]
var _usi_t := [0.0, 0.0]
var _hlava := 0.0                # pohozeni hlavou (0..1)
var _hlava_t := 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.randomize()
	var sk := get_skeleton()
	if sk == null:
		return
	for sk_jm: String in (Z["kosti"] as Dictionary):
		var a: Array = []
		for pre: String in Z["kosti"][sk_jm]:
			for i in sk.get_bone_count():
				if sk.get_bone_name(i).begins_with(pre):
					a.append(i)
					break
		_kosti[sk_jm] = a
	var hl: Array = _kosti.get("hlava", [])
	var pn: Array = _kosti.get("panev", [])
	if not hl.is_empty() and not pn.is_empty():
		var f := sk.get_bone_global_rest(hl[0]).origin - sk.get_bone_global_rest(pn[0]).origin
		f.y = 0.0
		_bok = f.normalized().cross(Vector3.UP).normalized()
	_pastva_t = _rng.randf_range(2.0, 6.0)
	_ocas_t = _rng.randf_range(2.0, 6.0)
	_hlava_t = _rng.randf_range(10.0, 25.0)


## Otoceni kosti kolem osy (soustava kostry) se stredem v kosti - po rodicich, potomci se pohnou s nimi.
func _toc(sk: Skeleton3D, i: int, osa: Vector3, uhel: float) -> void:
	if absf(uhel) < 1e-5:
		return
	var g := sk.get_bone_global_pose(i)
	g.basis = Basis(osa, uhel) * g.basis
	sk.set_bone_global_pose(i, g)


func _process_modification() -> void:
	var sk := get_skeleton()
	if sk == null or _kosti.is_empty():
		return
	var dt := get_process_delta_time() if is_inside_tree() else 0.016
	_t += dt
	# pastva: jen volny stojici kun; strida pastvu a zvednutou hlavu (pastva_s, zvednuta_s)
	_pastva_t -= dt
	if not (stoji and volny):
		_pastva_cil = 0.0
	elif _pastva_t <= 0.0:
		_pastva_cil = 1.0 - _pastva_cil
		var r: Array = Z["pastva_s"] if _pastva_cil > 0.5 else Z["zvednuta_s"]
		_pastva_t = _rng.randf_range(float(r[0]), float(r[1]))
	_pastva = move_toward(_pastva, _pastva_cil, dt / float(Z["sklon_hlavy_s"]))
	var p := smoothstep(0.0, 1.0, _pastva)
	# ocas: stale mirne kyvani + obcas svihnuti (mouchy) - i v pohybu
	_ocas_t -= dt
	if _ocas_t <= 0.0:
		_ocas = 1.0
		_ocas_smer = -_ocas_smer if _rng.randf() < 0.7 else _ocas_smer
		_ocas_t = _rng.randf_range(float(Z["ocas_s"][0]), float(Z["ocas_s"][1]))
	_ocas = maxf(0.0, _ocas - dt / float(Z["ocas_svih_s"]))
	# usi: kazde zvlast jinam (dopredu, do strany, dozadu)
	for k in 2:
		_usi_t[k] -= dt
		if _usi_t[k] <= 0.0:
			_usi_cil[k] = _rng.randf_range(-1.0, 1.0)
			_usi_t[k] = _rng.randf_range(float(Z["usi_s"][0]), float(Z["usi_s"][1]))
		_usi[k] = move_toward(_usi[k], _usi_cil[k], dt * 4.0)
	# pohozeni hlavou (jen ve stani, ne pri pastve)
	_hlava_t -= dt
	if _hlava_t <= 0.0 and stoji and p < 0.1:
		_hlava = 1.0
		_hlava_t = _rng.randf_range(float(Z["hlava_s"][0]), float(Z["hlava_s"][1]))
	_hlava = maxf(0.0, _hlava - dt / 1.2)
	var st := 1.0 if stoji else 0.35
	# dech: hrbet a bricho (perioda dech_s)
	var dech := sin(_t * TAU / float(Z["dech_s"])) * deg_to_rad(float(Z["dech_st"])) * st
	for i: int in _kosti.get("hrbet", []):
		_toc(sk, i, _bok, dech)
	# prenaseni vahy: panev se pomalu nakloni (odlehcena zadni noha)
	for i: int in _kosti.get("panev", []):
		_toc(sk, i, _bok.cross(Vector3.UP), sin(_t * 0.21) * deg_to_rad(float(Z["vaha_st"])) * st)
	# krk a hlava: pastva dolu (kladny uhel kolem _bok = osa vpred k nebi, proto zaporne) (rozdeleni uhlu po kostech krku), pohozeni nahoru-dolu, zvykani
	var krk: Array = _kosti.get("krk", [])
	var dolu := deg_to_rad(float(Z["pastva_krk_st"])) * p
	var poh := sin(_hlava * PI * 2.0) * deg_to_rad(12.0) * _hlava
	for j in krk.size():
		_toc(sk, krk[j], _bok, -(dolu + poh) / float(krk.size()) + sin(_t * 0.6 + j) * deg_to_rad(0.6))
	for i: int in _kosti.get("hlava", []):
		_toc(sk, i, _bok, -deg_to_rad(float(Z["pastva_hlava_st"])) * p + sin(_t * 0.37) * deg_to_rad(1.5))
	for i: int in _kosti.get("celist", []):
		_toc(sk, i, _bok, -absf(sin(_t * TAU * float(Z["zvykani_hz"]))) * deg_to_rad(6.0) * p)
	# usi
	var us: Array = _kosti.get("usi", [])
	for k in mini(2, us.size()):
		_toc(sk, us[k], Vector3.UP, float(_usi[k]) * deg_to_rad(float(Z["usi_st"])) * (1.0 if k == 0 else -1.0))
	# ocas: kyvani + svihnuti do strany, kazdy clanek o kus pozdeji
	var oc: Array = _kosti.get("ocas", [])
	for j in oc.size():
		var kyv := sin(_t * 1.3 - j * 0.5) * deg_to_rad(3.0)
		var svih := sin((1.0 - _ocas) * PI * 2.0 - j * 0.6) * _ocas * deg_to_rad(float(Z["ocas_st"])) / float(oc.size()) * _ocas_smer
		_toc(sk, oc[j], Vector3.UP, kyv + svih)
