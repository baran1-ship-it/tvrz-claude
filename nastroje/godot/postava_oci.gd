extends Node
## Oči a mrkání postavy. Přidat jako dítě kořene postavy (scény z .glb).
##  - mrkání: morph "mrknuti" na hlavě, řasách a vlhké lince, každé 3–6 s (rychlé zavření 0,07 s, otevření 0,12 s)
##  - pohled: uzly *_oko_l / *_oko_r (připnuté ke kosti hlavy) se natáčejí na cíl;
##    bez cíle bloudí po okolí, nový bod každé 2–4 s. V dialogu nastav `cil` (Node3D, např. hlava hráče).

@export var cil: Node3D
@export var max_vodorovne_deg := 28.0
@export var max_svisle_deg := 16.0

var _morf_meshe: Array[MeshInstance3D] = []
var _oci: Array[Node3D] = []
var _klid: Dictionary = {}
var _blud_bod := Vector3.ZERO      # (vpravo, nahoru) odchylka bloudění v metrech na 2 m
var _blud_cas := 0.0
var _mrk_cas := 0.0

func _ready() -> void:
	_najdi(get_parent())
	_mrk_cas = randf_range(3.0, 6.0)
	_novy_blud()

func _najdi(n: Node) -> void:
	if n is MeshInstance3D and n.mesh and n.find_blend_shape_by_name("mrknuti") >= 0:
		_morf_meshe.append(n)
	if n is Node3D and (String(n.name).ends_with("_oko_l") or String(n.name).ends_with("_oko_r")):
		_oci.append(n)
		_klid[n] = n.transform.basis
	for c in n.get_children():
		_najdi(c)

func _process(dt: float) -> void:
	_mrk_cas -= dt
	if _mrk_cas <= 0.0:
		_mrkni()
		_mrk_cas = randf_range(3.0, 6.0)
	_blud_cas -= dt
	if _blud_cas <= 0.0:
		_novy_blud()
	for oko in _oci:
		var cilovy := cil.global_position if cil else _blud_bod_svet(oko)
		_natoc(oko, cilovy, dt)

func _mrkni() -> void:
	var tw := create_tween()
	for mi in _morf_meshe:
		var idx := mi.find_blend_shape_by_name("mrknuti")
		tw.parallel().tween_method(func(v): mi.set_blend_shape_value(idx, v), 0.0, 1.0, 0.07)
	tw.tween_interval(0.04)
	for mi in _morf_meshe:
		var idx := mi.find_blend_shape_by_name("mrknuti")
		tw.parallel().tween_method(func(v): mi.set_blend_shape_value(idx, v), 1.0, 0.0, 0.12)

func _novy_blud() -> void:
	_blud_cas = randf_range(2.0, 4.0)
	_blud_bod = Vector3(randf_range(-0.6, 0.6), randf_range(-0.25, 0.3), 0.0)

## bod 2 m před okem ve směru klidového pohledu (+Z oka v klidu), posunutý doprava/nahoru – nezávisí na osách kosti hlavy
func _blud_bod_svet(oko: Node3D) -> Vector3:
	var rodic := oko.get_parent() as Node3D
	if rodic == null:
		return oko.global_position + Vector3(0, 0, 2)
	var b: Basis = rodic.global_transform.basis * _klid[oko]
	var vpred := (b * Vector3(0, 0, 1)).normalized()
	var nahoru := Vector3.UP
	var vpravo := vpred.cross(nahoru).normalized()
	return oko.global_position + vpred * 2.0 + vpravo * _blud_bod.x + nahoru * _blud_bod.y

func _natoc(oko: Node3D, bod: Vector3, dt: float) -> void:
	var rodic := oko.get_parent() as Node3D
	if rodic == null:
		return
	var mistni := rodic.global_transform.affine_inverse() * bod - oko.position
	var klid: Basis = _klid[oko]
	var vpred := klid * Vector3(0, 0, 1)
	var smer := mistni.normalized()
	# omezení úhlů
	var yaw := clampf(atan2(smer.x, smer.z) - atan2(vpred.x, vpred.z), deg_to_rad(-max_vodorovne_deg), deg_to_rad(max_vodorovne_deg))
	var pitch := clampf(asin(clampf(smer.y, -1, 1)) - asin(clampf(vpred.y, -1, 1)), deg_to_rad(-max_svisle_deg), deg_to_rad(max_svisle_deg))
	var cilova := Basis.from_euler(Vector3(-pitch, yaw, 0)) * klid
	oko.transform.basis = oko.transform.basis.slerp(cilova, clampf(dt * 12.0, 0, 1))
