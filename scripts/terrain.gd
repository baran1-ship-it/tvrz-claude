extends RefCounted
## Krajina kolem tvrze: kopec s prikopem, cesta, rybnik, pole, lesy, vesnice v udoli.

const Batch := preload("res://scripts/mesh_batch.gd")

const NEAR := 140.0       # polovina strany podrobne site
const CELL := 2.0
const FAR := 900.0
const FCELL := 20.0
const POND := Vector2(-78.0, 96.0)
const POND_R := 30.0
const VILLAGE := Vector2(150.0, 205.0)
const ROAD := [Vector2(0, 17), Vector2(0, 46), Vector2(8, 74), Vector2(30, 108), Vector2(66, 146), Vector2(108, 182), Vector2(150, 205), Vector2(200, 232), Vector2(320, 270)]

var M: Dictionary
var info: Dictionary
var n1 := FastNoiseLite.new()
var n2 := FastNoiseLite.new()
var n3 := FastNoiseLite.new()
var raw0 := 0.0
var pond_level := 0.0
var rng := RandomNumberGenerator.new()
var terrain_mat: ShaderMaterial


func _init(p_mats: Dictionary, p_info: Dictionary) -> void:
	M = p_mats
	info = p_info
	rng.seed = 77
	n1.seed = 5
	n1.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n1.frequency = 0.0038
	n1.fractal_octaves = 4
	n2.seed = 9
	n2.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n2.frequency = 0.021
	n2.fractal_octaves = 3
	n3.seed = 21
	n3.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n3.frequency = 0.0075
	n3.fractal_octaves = 2
	raw0 = _raw_base(0.0, 0.0)
	pond_level = _land(POND.x, POND.y) - 3.2


# ------------------------------------------------------------------ vyska

func _raw_base(x: float, z: float) -> float:
	var r := Vector2(x, z).length()
	var h := n1.get_noise_2d(x, z) * 17.0 + n2.get_noise_2d(x, z) * 2.2
	h -= 10.0 * smoothstep(22.0, 170.0, r)
	h += 34.0 * smoothstep(300.0, 720.0, r) * (0.55 + 0.45 * n1.get_noise_2d(x * 0.45 + 300.0, z * 0.45))
	return h


func rect_dist(x: float, z: float) -> float:
	var dx := absf(x) - 18.8
	var dz := absf(z) - 15.8
	return Vector2(maxf(dx, 0.0), maxf(dz, 0.0)).length() + minf(maxf(dx, dz), 0.0)


func road_dist(x: float, z: float) -> float:
	var p := Vector2(x, z)
	var best := 1.0e9
	for i in ROAD.size() - 1:
		var a: Vector2 = ROAD[i]
		var b: Vector2 = ROAD[i + 1]
		var ab := b - a
		var t := clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
		best = minf(best, p.distance_to(a + ab * t))
	return best


## Teren bez rybnika a cesty.
func _land(x: float, z: float) -> float:
	var d := rect_dist(x, z)
	if d < 0.0:
		return -0.6
	var prof: float
	if d < 1.5:
		prof = -0.35
	elif d < 5.5:
		prof = lerpf(-0.35, -3.6, smoothstep(1.5, 5.5, d))
	elif d < 8.5:
		prof = -3.6
	else:
		prof = lerpf(-3.6, -1.3, smoothstep(8.5, 12.5, d))
	var t := smoothstep(11.5, 34.0, d)
	return lerpf(prof, _raw_base(x, z) - raw0 - 1.3, t)


func height(x: float, z: float) -> float:
	var h := _land(x, z)
	# rybnik: misa
	var pd := Vector2(x, z).distance_to(POND)
	if pd < POND_R + 26.0:
		var bowl := pond_level - 2.2 * (1.0 - pow(minf(pd / POND_R, 1.0), 2.0)) + maxf(pd - POND_R, 0.0) * 0.12
		h = lerpf(bowl, h, smoothstep(POND_R - 4.0, POND_R + 26.0, pd))
	# vesnice: srovnany plac
	var vd := Vector2(x, z).distance_to(VILLAGE)
	if vd < 90.0:
		h = lerpf(_land(VILLAGE.x, VILLAGE.y), h, smoothstep(28.0, 90.0, vd))
	return h


func normal_at(x: float, z: float) -> Vector3:
	var e := 1.0
	return Vector3(height(x - e, z) - height(x + e, z), 2.0 * e, height(x, z - e) - height(x, z + e)).normalized()


## Maska lesa 0..1.
func forest(x: float, z: float) -> float:
	var r := Vector2(x, z).length()
	if r < 46.0:
		return 0.0
	if road_dist(x, z) < 7.0:
		return 0.0
	if Vector2(x, z).distance_to(POND) < POND_R + 9.0:
		return 0.0
	if Vector2(x, z).distance_to(VILLAGE) < 62.0:
		return 0.0
	if field(x, z) > 0.2:
		return 0.0
	var m := n3.get_noise_2d(x + 500.0, z - 200.0)
	return smoothstep(-0.12, 0.2, m) * smoothstep(46.0, 80.0, r)


## Maska poli 0..1 (kolem vesnice a v udoli).
func field(x: float, z: float) -> float:
	var vd := Vector2(x, z).distance_to(VILLAGE + Vector2(-30, -70))
	var m := smoothstep(150.0, 90.0, vd)
	if m <= 0.0:
		return 0.0
	# pruhy poli
	var u := (x * 0.82 + z * 0.57)
	var stripe := fmod(absf(u) / 34.0, 1.0)
	var on := 1.0 if fmod(floorf(absf(u) / 34.0), 2.0) < 1.0 else 0.0
	var edge := smoothstep(0.0, 0.06, stripe) * smoothstep(1.0, 0.94, stripe)
	if road_dist(x, z) < 5.0 or Vector2(x, z).distance_to(VILLAGE) < 40.0:
		return 0.0
	return m * on * edge


func _color(x: float, z: float, nrm: Vector3) -> Color:
	var d := rect_dist(x, z)
	var grass := 1.0
	var dirt := 0.0
	var cob := 0.0
	var rd := road_dist(x, z)
	var road := smoothstep(4.2, 1.6, rd)
	dirt = maxf(dirt, road)
	# prikop a upati hradeb
	if d < 13.0:
		dirt = maxf(dirt, 0.55 * smoothstep(13.0, 3.0, d) + 0.3 * n2.get_noise_2d(x * 3.0, z * 3.0))
	# strme svahy
	dirt = maxf(dirt, smoothstep(0.84, 0.66, nrm.y))
	# breh rybnika
	var pd := Vector2(x, z).distance_to(POND)
	dirt = maxf(dirt, smoothstep(POND_R + 3.0, POND_R - 3.0, pd))
	# navsi
	var vd := Vector2(x, z).distance_to(VILLAGE)
	dirt = maxf(dirt, 0.7 * smoothstep(34.0, 14.0, vd))
	# predbrani
	if z > 15.0 and z < 22.0 and absf(x) < 3.0:
		cob = 1.0
	dirt = clampf(dirt + 0.18 * n2.get_noise_2d(x * 1.7 + 40.0, z * 1.7), 0.0, 1.0)
	grass = 1.0 - dirt
	var f := field(x, z)
	var sh := 1.0 - 0.5 * forest(x, z)
	return Color(grass * sh, dirt * (1.0 - cob) * sh, cob * sh, 1.0 - f)


# ------------------------------------------------------------------ stavba

func build(parent: Node3D) -> void:
	terrain_mat = ShaderMaterial.new()
	terrain_mat.shader = load("res://shaders/terrain.gdshader")
	for k: String in ["grass", "dirt", "cobble"]:
		var tex := "grass" if k == "grass" else k
		terrain_mat.set_shader_parameter(k + "_a", load("res://textures/%s_a.png" % tex))
		terrain_mat.set_shader_parameter(k + "_n", load("res://textures/%s_n.png" % tex))
	terrain_mat.set_shader_parameter("macro_tex", load("res://textures/cloud_noise.png"))
	info["terrain_mat"] = terrain_mat
	_near_mesh(parent)
	_far_mesh(parent)
	_pond(parent)
	_bridge(parent)
	_village(parent)
	_bounds(parent)


func _edge_height(x: float, z: float) -> float:
	# na okraji podrobne site vysku interpoluj po hrube mrizce, aby nevznikly skviry
	if absf(absf(x) - NEAR) < 0.01:
		var z0 := floorf(z / FCELL) * FCELL
		var t := (z - z0) / FCELL
		return lerpf(height(x, z0), height(x, z0 + FCELL), t)
	if absf(absf(z) - NEAR) < 0.01:
		var x0 := floorf(x / FCELL) * FCELL
		var t2 := (x - x0) / FCELL
		return lerpf(height(x0, z), height(x0 + FCELL, z), t2)
	return height(x, z)


func _near_mesh(parent: Node3D) -> void:
	var n := int(NEAR * 2.0 / CELL) + 1
	var hs := PackedFloat32Array()
	hs.resize(n * n)
	var v := PackedVector3Array()
	var nr := PackedVector3Array()
	var c := PackedColorArray()
	var idx := PackedInt32Array()
	v.resize(n * n)
	nr.resize(n * n)
	c.resize(n * n)
	for j in n:
		var z := -NEAR + j * CELL
		for i in n:
			var x := -NEAR + i * CELL
			var h := _edge_height(x, z)
			hs[j * n + i] = h
			v[j * n + i] = Vector3(x, h, z)
			var nm := normal_at(x, z)
			nr[j * n + i] = nm
			c[j * n + i] = _color(x, z, nm)
	for j in n - 1:
		for i in n - 1:
			var x := -NEAR + i * CELL
			var z := -NEAR + j * CELL
			# pod tvrzi teren neni potreba
			if absf(x + CELL * 0.5) < 15.0 and absf(z + CELL * 0.5) < 12.0:
				continue
			var a := j * n + i
			idx.append(a)
			idx.append(a + 1)
			idx.append(a + n)
			idx.append(a + 1)
			idx.append(a + n + 1)
			idx.append(a + n)
	_add_mesh(parent, "TerenBlizko", v, nr, c, idx)
	# kolize: vyskova mapa po 1 m, bilinearne z mrizky site
	var cn := int(NEAR * 2.0) + 1
	var data := PackedFloat32Array()
	data.resize(cn * cn)
	for j in cn:
		var fj := float(j) / CELL
		var j0 := mini(int(fj), n - 2)
		var tj := fj - j0
		for i in cn:
			var fi := float(i) / CELL
			var i0 := mini(int(fi), n - 2)
			var ti := fi - i0
			var h00 := hs[j0 * n + i0]
			var h10 := hs[j0 * n + i0 + 1]
			var h01 := hs[(j0 + 1) * n + i0]
			var h11 := hs[(j0 + 1) * n + i0 + 1]
			data[j * cn + i] = lerpf(lerpf(h00, h10, ti), lerpf(h01, h11, ti), tj)
	var shape := HeightMapShape3D.new()
	shape.map_width = cn
	shape.map_depth = cn
	shape.map_data = data
	var body := StaticBody3D.new()
	body.name = "TerenKolize"
	var cs := CollisionShape3D.new()
	cs.shape = shape
	body.add_child(cs)
	parent.add_child(body)


func _far_mesh(parent: Node3D) -> void:
	var n := int(FAR * 2.0 / FCELL) + 1
	var v := PackedVector3Array()
	var nr := PackedVector3Array()
	var c := PackedColorArray()
	var idx := PackedInt32Array()
	v.resize(n * n)
	nr.resize(n * n)
	c.resize(n * n)
	for j in n:
		var z := -FAR + j * FCELL
		for i in n:
			var x := -FAR + i * FCELL
			var h := height(x, z)
			# okraj sveta stahni dolu, at neni videt hrana
			var edge := maxf(absf(x), absf(z))
			h -= 60.0 * smoothstep(FAR - 120.0, FAR, edge)
			v[j * n + i] = Vector3(x, h, z)
			var e := FCELL * 0.5
			var nm := Vector3(height(x - e, z) - height(x + e, z), 2.0 * e, height(x, z - e) - height(x, z + e)).normalized()
			nr[j * n + i] = nm
			var col := _color(x, z, nm)
			# vzdalene lesy jako tmavsi trava
			c[j * n + i] = col
	for j in n - 1:
		for i in n - 1:
			var x := -FAR + i * FCELL
			var z := -FAR + j * FCELL
			if x >= -NEAR - 0.01 and x + FCELL <= NEAR + 0.01 and z >= -NEAR - 0.01 and z + FCELL <= NEAR + 0.01:
				continue
			var a := j * n + i
			idx.append(a)
			idx.append(a + 1)
			idx.append(a + n)
			idx.append(a + 1)
			idx.append(a + n + 1)
			idx.append(a + n)
	_add_mesh(parent, "TerenDaleko", v, nr, c, idx)


func _add_mesh(parent: Node3D, node_name: String, v: PackedVector3Array, nr: PackedVector3Array, c: PackedColorArray, idx: PackedInt32Array) -> void:
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nr
	arr[Mesh.ARRAY_COLOR] = c
	arr[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mi := MeshInstance3D.new()
	mi.name = node_name
	mi.mesh = mesh
	mi.material_override = terrain_mat
	parent.add_child(mi)


func _pond(parent: Node3D) -> void:
	var mi := MeshInstance3D.new()
	mi.name = "Rybnik"
	var pm := PlaneMesh.new()
	pm.size = Vector2((POND_R + 8.0) * 2.0, (POND_R + 8.0) * 2.0)
	pm.subdivide_width = 4
	pm.subdivide_depth = 4
	mi.mesh = pm
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/water.gdshader")
	mat.set_shader_parameter("nmap", load("res://textures/water_n.png"))
	mi.material_override = mat
	mi.position = Vector3(POND.x, pond_level, POND.y)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)


func _bridge(parent: Node3D) -> void:
	var b := Batch.new(M, 51)
	var z0 := 17.0
	var z1 := 28.6
	var y0 := 0.0
	var y1 := height(0.0, z1) + 0.12
	var wood := Color(0.72, 0.68, 0.62)
	var dark := Color(0.6, 0.56, 0.5)
	var hw := 1.75
	var d := Vector3(0, y1 - y0, z1 - z0)
	# mostovka: jednotliva prkna napric
	var n := 46
	for k in n:
		var t := (float(k) + 0.5) / n
		var p := Vector3(0, y0 - 0.04, z0) + d * t
		var tilt := atan2(y1 - y0, z1 - z0)
		var basis := Basis(Vector3(1, 0, 0), -tilt) * Basis(Vector3(0, 1, 0), b.jitter(0.012))
		b.box("planks", Transform3D(basis, p + Vector3(0, b.jitter(0.008), 0)), Vector3(hw * 2.0 + b.jitter(0.05), 0.08, d.length() / n - 0.012),
				Color(wood.r + b.jitter(0.06), wood.g + b.jitter(0.05), wood.b + b.jitter(0.05)), false, 0)
	b.hulls.append(PackedVector3Array([Vector3(-hw, y0, z0), Vector3(hw, y0, z0), Vector3(hw, y1, z1), Vector3(-hw, y1, z1),
			Vector3(-hw, y0 - 0.4, z0), Vector3(hw, y0 - 0.4, z0), Vector3(hw, y1 - 0.4, z1), Vector3(-hw, y1 - 0.4, z1)]))
	# podelne tramy, kozy a zabradli
	for sx: float in [-1.3, 0.0, 1.3]:
		b.beam("beam", Vector3(sx, y0 - 0.24, z0), Vector3(sx, y1 - 0.24, z1), 0.24, 0.3, dark)
	for k in 3:
		var t := 0.28 + 0.26 * k
		var p := Vector3(0, y0, z0) + d * t
		var gy := height(0.0, p.z) - 0.4
		for sx: float in [-1.5, 1.5]:
			b.beam("beam", Vector3(sx, gy, p.z), Vector3(sx, p.y - 0.3, p.z), 0.26, 0.26, dark)
		b.beam("beam", Vector3(-1.8, p.y - 0.5, p.z), Vector3(1.8, p.y - 0.5, p.z), 0.24, 0.26, dark)
		b.beam("beam", Vector3(-1.5, gy + 0.6, p.z), Vector3(1.5, p.y - 0.7, p.z), 0.12, 0.16, dark)
	for sx: float in [-hw + 0.08, hw - 0.08]:
		var r0 := Vector3(sx, y0, z0 + 0.3)
		var r1 := Vector3(sx, y1, z1 - 0.2)
		b.beam("beam", r0 + Vector3(0, 1.05, 0), r1 + Vector3(0, 1.05, 0), 0.1, 0.12, wood, true)
		b.beam("beam", r0 + Vector3(0, 0.55, 0), r1 + Vector3(0, 0.55, 0), 0.07, 0.09, wood)
		for k in 6:
			var p := r0.lerp(r1, float(k) / 5.0)
			b.beam("beam", p - Vector3(0, 0.1, 0), p + Vector3(0, 1.12, 0), 0.12, 0.12, wood)
		b.boxes.append([Transform3D(Basis(Vector3(1, 0, 0), -atan2(y1 - y0, z1 - z0)), (r0 + r1) * 0.5 + Vector3(0, 0.55, 0)), Vector3(0.14, 1.2, (r1 - r0).length())])
	b.commit(parent, "Most")


func _house(b: Batch, c: Vector2, yaw: float, w: float, d: float, wall_h: float, roof_h: float, stone: bool = false) -> void:
	var gy := height(c.x, c.y) - 0.3
	var basis := Basis(Vector3.UP, deg_to_rad(yaw))
	var o := Vector3(c.x, gy, c.y)
	var key := "stone" if stone else "plaster_worn"
	b.box(key, Transform3D(basis, o + Vector3(0, wall_h * 0.5, 0)), Vector3(w, wall_h, d), Color(0.95, 0.93, 0.9), false, -1, 0, true)
	var hx := w * 0.5 + 0.5
	var hz := d * 0.5 + 0.4
	var e := wall_h + 0.3
	var p := func(lx: float, ly: float, lz: float) -> Vector3: return o + basis * Vector3(lx, ly, lz)
	b.slab("shingles", p.call(-hx, e - 0.3, -hz), p.call(hx, e - 0.3, -hz), p.call(hx, e + roof_h, 0.0), p.call(-hx, e + roof_h, 0.0), 0.2, Color(0.8, 0.76, 0.7))
	b.slab("shingles", p.call(-hx, e - 0.3, hz), p.call(hx, e - 0.3, hz), p.call(hx, e + roof_h, 0.0), p.call(-hx, e + roof_h, 0.0), 0.2, Color(0.8, 0.76, 0.7))
	for sx: float in [-1.0, 1.0]:
		b.tri_slab("planks", p.call(sx * w * 0.5, wall_h, -d * 0.5), p.call(sx * w * 0.5, wall_h, d * 0.5), p.call(sx * w * 0.5, e + roof_h - 0.1, 0.0), 0.12, Color(0.6, 0.55, 0.5))
	# dvere a okna jako tmave plochy
	b.box("soot", Transform3D(basis, p.call(0.0, 1.0, d * 0.5 + 0.02)), Vector3(1.0, 2.0, 0.05))
	b.box("soot", Transform3D(basis, p.call(w * 0.28, 1.5, d * 0.5 + 0.02)), Vector3(0.7, 0.7, 0.05))
	b.box("soot", Transform3D(basis, p.call(-w * 0.28, 1.5, d * 0.5 + 0.02)), Vector3(0.7, 0.7, 0.05))


func _village(parent: Node3D) -> void:
	var b := Batch.new(M, 61)
	b.ground_y = height(VILLAGE.x, VILLAGE.y)
	var hs := [
		[Vector2(-18, -10), 20.0, 9.0, 6.0, 3.0, 3.6], [Vector2(6, -16), -12.0, 11.0, 6.5, 3.2, 4.0],
		[Vector2(-24, 12), 80.0, 8.0, 5.5, 2.8, 3.4], [Vector2(20, 14), 100.0, 10.0, 6.0, 3.0, 3.8],
		[Vector2(-4, 22), 5.0, 8.5, 5.5, 2.8, 3.4], [Vector2(30, -6), 60.0, 7.5, 5.0, 2.6, 3.2],
		[Vector2(-38, -4), -30.0, 9.0, 5.5, 2.8, 3.5], [Vector2(12, 34), -70.0, 8.0, 5.0, 2.7, 3.3],
	]
	for h: Array in hs:
		_house(b, VILLAGE + h[0], h[1], h[2], h[3], h[4], h[5])
	# kostelik
	var cc: Vector2 = VILLAGE + Vector2(-8.0, 2.0)
	_house(b, cc, 8.0, 14.0, 7.5, 6.0, 5.0, true)
	var gy := height(cc.x, cc.y) - 0.3
	var basis := Basis(Vector3.UP, deg_to_rad(8.0))
	var to := Vector3(cc.x, gy, cc.y) + basis * Vector3(-9.0, 0, 0)
	b.box("stone", Transform3D(basis, to + Vector3(0, 8.0, 0)), Vector3(5.0, 16.0, 5.0), Color.WHITE, false, -1, 0, true)
	var ap := to + Vector3(0, 24.0, 0)
	var cr := [to + basis * Vector3(-2.9, 16, -2.9), to + basis * Vector3(2.9, 16, -2.9), to + basis * Vector3(2.9, 16, 2.9), to + basis * Vector3(-2.9, 16, 2.9)]
	for k in 4:
		b.tri_slab("shingles", cr[k], cr[(k + 1) % 4], ap, 0.2, Color(0.75, 0.72, 0.68))
	b.commit(parent, "Vesnice")
	info["village"] = Vector3(VILLAGE.x, height(VILLAGE.x, VILLAGE.y), VILLAGE.y)


func _bounds(parent: Node3D) -> void:
	var body := StaticBody3D.new()
	body.name = "Hranice"
	var lim := NEAR - 6.0
	for k in 4:
		var cs := CollisionShape3D.new()
		var sh := BoxShape3D.new()
		sh.size = Vector3(lim * 2.0 + 4.0, 200.0, 2.0)
		cs.shape = sh
		var ang := k * PI * 0.5
		cs.transform = Transform3D(Basis(Vector3.UP, ang), Vector3(sin(ang), 0, cos(ang)) * lim)
		body.add_child(cs)
	parent.add_child(body)
