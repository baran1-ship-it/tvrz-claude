extends Node3D
## 3D trava v cele krajine: mrizka z Blenderu (svet.json "trava_kraj": vyska terenu v cm a hustota 0..255
## po 2 m). Trsy se skladaji jen v bunkach 16 m kolem hrace (podle kvality 30-55 m), vzdalene bunky se uvolni.
## Ves ma vlastni hustou travu (svet.gd _ves_grass), tvrz svou.

const BUNKA := 16.0
const NA_SNIMEK := 2              # kolik bunek se postavi za snimek (plynule, bez zaseku)

var _x0 := 0.0
var _z0 := 0.0
var _k := 2.0
var _nx := 0
var _nz := 0
var _ys: PackedByteArray
var _ms: PackedByteArray
var _mesh: Mesh
var _step := 0.75
var _dosah := 42.0
var _cells := {}                  # Vector2i -> MultiMeshInstance3D (nebo null = prazdna)
var _player: Node3D
var _fronta: Array = []
var _trsu := 0
var _hlaseno := false


func setup(g: Dictionary, quality: int, player: Node3D, mesh: Mesh) -> void:
	if g.is_empty():
		return
	_x0 = float(g["x0"])
	_z0 = float(g["z0"])
	_k = float(g["k"])
	_nx = int(g["nx"])
	_nz = int(g["nz"])
	_ys = Marshalls.base64_to_raw(String(g["y"]))
	_ms = Marshalls.base64_to_raw(String(g["m"]))
	_mesh = mesh
	_player = player
	process_mode = Node.PROCESS_MODE_ALWAYS
	_step = [0.95, 0.75, 0.62][quality]
	_dosah = [30.0, 42.0, 55.0][quality]
	print("trava v krajine: mrizka %d x %d, dosah %d m" % [_nx, _nz, int(_dosah)])


func _process(_dt: float) -> void:
	if _player == null or _ms.is_empty():
		return
	var p := _player.global_position
	var c0 := Vector2i(floori(p.x / BUNKA), floori(p.z / BUNKA))
	var rc := int(ceil((_dosah + 8.0) / BUNKA))
	# nove bunky v dosahu (nejblizsi napred)
	_fronta.clear()
	for dx in range(-rc, rc + 1):
		for dz in range(-rc, rc + 1):
			var c := c0 + Vector2i(dx, dz)
			if _cells.has(c):
				continue
			var cen := Vector2((c.x + 0.5) * BUNKA, (c.y + 0.5) * BUNKA)
			var d := cen.distance_to(Vector2(p.x, p.z))
			if d < _dosah + BUNKA * 0.75:
				_fronta.append([d, c])
	_fronta.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	for i in mini(NA_SNIMEK, _fronta.size()):
		var c: Vector2i = _fronta[i][1]
		_cells[c] = _postav(c)
		if _cells[c]:
			_trsu += (_cells[c] as MultiMeshInstance3D).multimesh.instance_count
	if _fronta.size() <= NA_SNIMEK and not _hlaseno and _trsu > 0:
		_hlaseno = true
		print("trava v krajine: %d bunek, %d trsu kolem hrace" % [_cells.size(), _trsu])
	# vzdalene pryc
	for c: Vector2i in _cells.keys():
		if absi(c.x - c0.x) > rc + 1 or absi(c.y - c0.y) > rc + 1:
			var n: Node = _cells[c]
			if n:
				n.queue_free()
			_cells.erase(c)


func _vzorek(px: float, pz: float) -> Vector2:
	# (hustota 0..1, vyska) bilinearne z mrizky; mimo mrizku hustota 0
	var fx := (px - _x0) / _k
	var fz := (pz - _z0) / _k
	var i := floori(fx)
	var j := floori(fz)
	if i < 0 or j < 0 or i >= _nx - 1 or j >= _nz - 1:
		return Vector2(0.0, 0.0)
	fx -= i
	fz -= j
	var a0 := j * _nx + i
	var dens := lerpf(lerpf(_ms[a0], _ms[a0 + 1], fx), lerpf(_ms[a0 + _nx], _ms[a0 + _nx + 1], fx), fz) / 255.0
	if dens <= 0.0:
		return Vector2(0.0, 0.0)
	var h0 := _ys.decode_s16(a0 * 2)
	var h1 := _ys.decode_s16((a0 + 1) * 2)
	var h2 := _ys.decode_s16((a0 + _nx) * 2)
	var h3 := _ys.decode_s16((a0 + _nx + 1) * 2)
	return Vector2(dens, lerpf(lerpf(h0, h1, fx), lerpf(h2, h3, fx), fz) / 100.0)


func _postav(c: Vector2i) -> MultiMeshInstance3D:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(c) ^ 1393
	var cen := Vector3((c.x + 0.5) * BUNKA, 0.0, (c.y + 0.5) * BUNKA)
	var xfs: Array[Transform3D] = []
	var x := 0.0
	while x < BUNKA:
		var z := 0.0
		while z < BUNKA:
			var px := c.x * BUNKA + x + rng.randf_range(-0.4, 0.4) * _step
			var pz := c.y * BUNKA + z + rng.randf_range(-0.4, 0.4) * _step
			z += _step
			var v := _vzorek(px, pz)
			if v.x <= 0.0 or rng.randf() > v.x * 1.1:
				continue
			var sc := rng.randf_range(0.55, 1.2) * lerpf(0.7, 1.1, v.x)
			xfs.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sc, sc * rng.randf_range(0.75, 1.35), sc)),
					Vector3(px, v.y - 0.04, pz) - cen))
		x += _step
	if xfs.is_empty():
		return null
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = _mesh
	mm.instance_count = xfs.size()
	for i in xfs.size():
		mm.set_instance_transform(i, xfs[i])
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.position = cen
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mmi.visibility_range_end = _dosah
	mmi.visibility_range_end_margin = 8.0
	mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	add_child(mmi)
	return mmi
