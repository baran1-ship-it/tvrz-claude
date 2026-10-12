extends RefCounted
## Stromy a trava. Vse pres MultiMesh, jedna sit na druh.

const Batch := preload("res://scripts/mesh_batch.gd")

var M: Dictionary
var T: RefCounted
var rng := RandomNumberGenerator.new()
var info: Dictionary


func _init(p_mats: Dictionary, terrain: RefCounted, p_info: Dictionary) -> void:
	M = p_mats
	T = terrain
	info = p_info
	rng.seed = 4242


func build(parent: Node3D) -> void:
	var near_spruce: Array[Transform3D] = []
	var near_oak: Array[Transform3D] = []
	var far_trees: Array[Transform3D] = []
	# blizky les
	var step := 6.4
	var lim := 236.0
	var x := -lim
	while x < lim:
		var z := -lim
		while z < lim:
			var px := x + rng.randf_range(-2.6, 2.6)
			var pz := z + rng.randf_range(-2.6, 2.6)
			var r := Vector2(px, pz).length()
			if r < lim:
				var f: float = T.forest(px, pz)
				var roll := rng.randf()
				var solitary := f <= 0.0 and r > 52.0 and roll < 0.012 and _free(px, pz)
				if roll < f * 0.92 or solitary:
					var xf := _xf(px, pz, 0.72, 1.38)
					if solitary or rng.randf() < 0.36:
						near_oak.append(xf)
					else:
						near_spruce.append(xf)
			z += step
		x += step
	# vzdaleny les
	step = 11.5
	lim = 780.0
	x = -lim
	while x < lim:
		var z2 := -lim
		while z2 < lim:
			var px2 := x + rng.randf_range(-4.5, 4.5)
			var pz2 := z2 + rng.randf_range(-4.5, 4.5)
			var r2 := Vector2(px2, pz2).length()
			if r2 >= 236.0 and r2 < lim and rng.randf() < float(T.forest(px2, pz2)) * 0.95:
				far_trees.append(_xf(px2, pz2, 0.9, 1.7))
			z2 += step
		x += step
	# par stromu blizko tvrze pro meritko
	for p: Vector2 in [Vector2(-34, 30), Vector2(-40, 24), Vector2(34, -32), Vector2(40, 34), Vector2(-30, -36), Vector2(27, 40)]:
		near_oak.append(_xf(p.x, p.y, 0.9, 1.2))
	if info.has("yard_tree"):
		var yt: Vector3 = info["yard_tree"]
		near_oak.append(Transform3D(Basis(Vector3.UP, 1.1).scaled(Vector3(0.82, 0.86, 0.82)), yt - Vector3(0, 0.1, 0)))
	_multi(parent, "Smrky", _spruce_mesh(9, 6, 4), near_spruce, true)
	_multi(parent, "Listnace", _oak_mesh(), near_oak, true)
	_multi(parent, "LesDaleko", _spruce_mesh(0, 0, 0), far_trees, false)
	_grass(parent)
	print("flora: smrky ", near_spruce.size(), ", listnace ", near_oak.size(), ", daleko ", far_trees.size())


func _free(x: float, z: float) -> bool:
	return T.road_dist(x, z) > 9.0 and T.field(x, z) < 0.05 and Vector2(x, z).distance_to(T.POND) > T.POND_R + 8.0 \
			and Vector2(x, z).distance_to(T.VILLAGE) > 50.0


func _xf(x: float, z: float, s0: float, s1: float) -> Transform3D:
	var s := rng.randf_range(s0, s1)
	var b := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.9, 1.15), s))
	return Transform3D(b, Vector3(x, T.height(x, z) - 0.15, z))


func _multi(parent: Node3D, node_name: String, mesh: Mesh, xfs: Array[Transform3D], shadows: bool) -> void:
	if xfs.is_empty():
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = xfs.size()
	for i in xfs.size():
		mm.set_instance_transform(i, xfs[i])
	var mi := MultiMeshInstance3D.new()
	mi.name = node_name
	mi.multimesh = mm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)


func _spruce_mesh(tiers: int, k_low: int, k_high: int) -> ArrayMesh:
	var b := Batch.new(M, 301)
	var h := 14.0
	var r := RandomNumberGenerator.new()
	r.seed = 99
	# telo stromu: zkrizene svisle karty se siluetou celeho smrku
	var crosses := 3 if tiers > 0 else 2
	for c in crosses:
		var ang := PI * float(c) / crosses + 0.2
		var tg := Vector3(cos(ang), 0, sin(ang)) * 3.4
		var top := Vector3(0, h + 0.6, 0)
		var bot := Vector3(0, -0.2, 0)
		var nl := (-tg.normalized() * 0.65 + Vector3.UP * 0.76).normalized()
		var nr := (tg.normalized() * 0.65 + Vector3.UP * 0.76).normalized()
		var ct := Color(1.0, 1.0, 1.0, 1.0)
		var cb := Color(0.72, 0.72, 0.72, 0.0)
		b.card("spruce_tree", [top - tg, top + tg, bot + tg, bot - tg], [nl, nr, nr, nl],
				[Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)], [ct, ct, cb, cb])
	if tiers <= 0:
		return b.to_mesh()
	b.lathe("bark", Transform3D.IDENTITY, PackedVector2Array([Vector2(0.24, 0.0), Vector2(0.17, 3.0), Vector2(0.03, h)]), 6)
	# vetve do stran pro objem pri pohledu zblizka
	for t in tiers:
		var f := float(t) / maxf(tiers - 1, 1)
		var y := lerpf(1.9, h - 1.6, f)
		var rad := lerpf(3.4, 0.7, pow(f, 0.85))
		var k := int(round(lerpf(k_low, k_high, f)))
		var off := r.randf() * TAU
		for c2 in k:
			var ang2 := off + TAU * float(c2) / k + r.randf_range(-0.2, 0.2)
			var o := Vector3(cos(ang2), 0, sin(ang2))
			var tg2 := Vector3(-sin(ang2), 0, cos(ang2))
			var rr := rad * r.randf_range(0.85, 1.15)
			var inner := Vector3(0, y + 0.3, 0) - o * 0.1
			var outer := o * rr + Vector3(0, y - rr * 0.3, 0)
			var w := rr * 1.25
			var nm := (o * 0.45 + Vector3.UP * 0.9).normalized()
			var tone := r.randf_range(0.8, 1.05)
			var ci := Color(tone * 0.75, tone * 0.75, tone * 0.75, 0.0)
			var co := Color(tone, tone, tone, 1.0)
			b.card("spruce", [inner - tg2 * w * 0.5, inner + tg2 * w * 0.5, outer + tg2 * w * 0.5, outer - tg2 * w * 0.5],
					[nm, nm, nm, nm], [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)], [ci, ci, co, co])
	return b.to_mesh()


func _oak_mesh() -> ArrayMesh:
	var b := Batch.new(M, 302)
	b.lathe("bark", Transform3D.IDENTITY, PackedVector2Array([Vector2(0.62, 0.0), Vector2(0.42, 0.5), Vector2(0.34, 2.8), Vector2(0.3, 4.4), Vector2(0.12, 6.6)]), 8)
	var r := RandomNumberGenerator.new()
	r.seed = 123
	for k in 5:
		var ang := TAU * k / 5.0 + r.randf_range(-0.3, 0.3)
		var o := Vector3(cos(ang), 0, sin(ang))
		b.tube("bark", PackedVector3Array([Vector3(0, 3.6 + 0.3 * k, 0), o * 1.2 + Vector3(0, 5.0 + 0.2 * k, 0), o * 2.6 + Vector3(0, 6.4, 0)]), 0.16, 5, Color.WHITE, 0.05)
	var cen := Vector3(0, 7.4, 0)
	var radii := Vector3(3.9, 2.9, 3.9)
	for i in 54:
		var d := Vector3(r.randf_range(-1, 1), r.randf_range(-0.35, 1), r.randf_range(-1, 1)).normalized()
		var pos := cen + d * radii * r.randf_range(0.5, 1.0)
		var n := (d + Vector3(r.randf_range(-0.6, 0.6), r.randf_range(-0.3, 0.6), r.randf_range(-0.6, 0.6))).normalized()
		var ax := n.cross(Vector3.UP if absf(n.y) < 0.9 else Vector3(1, 0, 0)).normalized()
		var ay := ax.cross(n).normalized()
		var s := r.randf_range(1.5, 2.1)
		var pts := [pos - ax * s - ay * s, pos + ax * s - ay * s, pos + ax * s + ay * s, pos - ax * s + ay * s]
		var nrm := []
		for p: Vector3 in pts:
			nrm.append(((p - cen).normalized() * 0.7 + Vector3.UP * 0.5).normalized())
		var tone := r.randf_range(0.78, 1.1)
		# spodek koruny tmavsi
		var dk := lerpf(0.62, 1.0, clampf((pos.y - 5.0) / 4.0, 0.0, 1.0))
		var col := Color(tone * dk, tone * dk, tone * dk * 0.95, 1.0)
		b.card("leaves", pts, nrm, [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)], [col, col, col, col])
	return b.to_mesh()


func _tuft_mesh() -> ArrayMesh:
	var b := Batch.new(M, 303)
	for k in 3:
		var ang := PI * k / 3.0
		var tg := Vector3(cos(ang), 0, sin(ang)) * 0.42
		var up := Vector3(0, 0.62, 0)
		var n := Vector3.UP
		var c0 := Color(0.82, 0.86, 0.8, 0.0)
		var c1 := Color(1.0, 1.0, 1.0, 1.0)
		b.card("grass_tuft", [up - tg, up + tg, tg, -tg], [n, n, n, n], [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)], [c1, c1, c0, c0])
	return b.to_mesh()


func _grass(parent: Node3D) -> void:
	var mesh := _tuft_mesh()
	var cells := {}
	var size := 18.0
	var lim := 84.0
	var step := 0.95
	var x := -lim
	while x < lim:
		var z := -lim
		while z < lim:
			var px := x + rng.randf_range(-0.45, 0.45)
			var pz := z + rng.randf_range(-0.45, 0.45)
			z += step
			var d: float = T.rect_dist(px, pz)
			if d < 0.4:
				continue
			var r := Vector2(px, pz).length()
			# hustota klesa se vzdalenosti, na ceste a v lese trava neni
			var dens := lerpf(0.85, 0.12, smoothstep(26.0, lim, r))
			if rng.randf() > dens:
				continue
			if T.road_dist(px, pz) < 2.6 or Vector2(px, pz).distance_to(T.POND) < T.POND_R + 0.5:
				continue
			var s := rng.randf_range(0.7, 1.7)
			var xf := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.7, 1.3), s)),
					Vector3(px, T.height(px, pz) - 0.03, pz))
			var key := Vector2i(int(floor(px / size)), int(floor(pz / size)))
			if not cells.has(key):
				cells[key] = []
			cells[key].append(xf)
		x += step
	var root := Node3D.new()
	root.name = "Trava"
	parent.add_child(root)
	var total := 0
	for key: Vector2i in cells:
		var arr: Array = cells[key]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = arr.size()
		var cen := Vector3((key.x + 0.5) * size, 0, (key.y + 0.5) * size)
		for i in arr.size():
			var xf: Transform3D = arr[i]
			xf.origin -= cen
			mm.set_instance_transform(i, xf)
		var mi := MultiMeshInstance3D.new()
		mi.multimesh = mm
		mi.position = cen
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.visibility_range_end = 62.0
		mi.visibility_range_end_margin = 10.0
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		root.add_child(mi)
		total += arr.size()
	print("trava: ", total, " trsu v ", cells.size(), " dilech")
