extends Node
## Mech kovarny na vsi (NAVOD_KOVARNA.md, lokace.json kovarna_ves.mech): paka se otaci kolem osy o uhel x t, mech ma blend
## shape Nadech (0 stlaceny .. 1 nadechnuty); pumpovani t = 0,5 - 0,5 cos(tempo x cas). Pouziti „Měch“ (main._on_use)
## pumpuje doba_s sekund, pak se mech vrati do klidu (t 0).

var paka: Node3D
var mech: MeshInstance3D
var zaklad: Basis
var osa := Vector3(0.469, 0.0, 0.883)
var uhel := 0.278
var tempo := 2.5
var _zbyva := 0.0
var _cas := 0.0
var _shape := -1


func _ready() -> void:
	if mech and mech.mesh:
		_shape = mech.find_blend_shape_by_name("Nadech")
	set_process(false)


func pumpuj(doba_s: float) -> void:
	_zbyva = doba_s
	_cas = 0.0
	set_process(true)


func _process(dt: float) -> void:
	_cas += dt
	_zbyva -= dt
	var t := 0.5 - 0.5 * cos(_cas * tempo)
	if _zbyva <= 0.0 and t < 0.03:
		t = 0.0
		set_process(false)
	paka.transform.basis = zaklad * Basis(osa.normalized(), uhel * t)
	if _shape >= 0:
		mech.set_blend_shape_value(_shape, t)
