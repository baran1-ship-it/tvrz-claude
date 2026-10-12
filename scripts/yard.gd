extends RefCounted
## Nadvori: zem, straznice, kovarna, strelnice, studna a drobne vybaveni.

const Batch := preload("res://scripts/mesh_batch.gd")
const Fort := preload("res://scripts/fort.gd")
const Props := preload("res://scripts/props.gd")

const WOOD := Color(0.8, 0.74, 0.66)
const DARK := Color(0.56, 0.5, 0.44)
const OLD := Color(0.66, 0.63, 0.6)
const PLASTER := Color(0.97, 0.95, 0.92)
const PATHS := [
	[Vector2(0, 14), Vector2(0, 3.5), Vector2(8, -4.5), Vector2(8, -7)],
	[Vector2(0, 3.5), Vector2(-8, -6), Vector2(-11.6, -12.8)],
	[Vector2(0, 6), Vector2(-6, 8.3)],
	[Vector2(1, 5), Vector2(11, 6.2)],
	[Vector2(2, 9), Vector2(14.2, 12.6)],
	[Vector2(8, -4.5), Vector2(-0.05, -6.6)],
	[Vector2(0, 3.5), Vector2(-9.4, -6.3)],
]

var M: Dictionary
var info: Dictionary
var P: Props
var noise := FastNoiseLite.new()


func _init(p_mats: Dictionary, p_info: Dictionary, props: Props) -> void:
	M = p_mats
	info = p_info
	P = props
	noise.seed = 31
	noise.frequency = 0.35


func build(parent: Node3D) -> void:
	_ground(parent)
	_guardhouse(parent)
	_smithy(parent)
	_range(parent)
	_misc(parent)


func _path_dist(x: float, z: float) -> float:
	var p := Vector2(x, z)
	var best := 1.0e9
	for path: Array in PATHS:
		for i in path.size() - 1:
			var a: Vector2 = path[i]
			var c: Vector2 = path[i + 1]
			var ac := c - a
			var t := clampf((p - a).dot(ac) / ac.length_squared(), 0.0, 1.0)
			best = minf(best, p.distance_to(a + ac * t))
	return best


func _ground(parent: Node3D) -> void:
	var x0 := -17.0
	var z0 := -14.0
	var nx := 35
	var nz := 29
	var v := PackedVector3Array()
	var nr := PackedVector3Array()
	var c := PackedColorArray()
	var idx := PackedInt32Array()
	for j in nz:
		for i in nx:
			var x := x0 + i
			var z := z0 + j
			var nzv := noise.get_noise_2d(x, z)
			v.append(Vector3(x, 0.0 + 0.03 * nzv, z))
			nr.append(Vector3.UP)
			var pd := _path_dist(x, z)
			var cob := smoothstep(2.6, 1.3, pd + 0.6 * nzv)
			var wall_d := minf(17.0 - absf(x), 14.0 - absf(z))
			var grass := smoothstep(2.4, 0.8, wall_d + 0.8 * nzv) * (1.0 - cob)
			grass = maxf(grass, smoothstep(0.25, 0.6, noise.get_noise_2d(x * 0.4 + 9.0, z * 0.4)) * (1.0 - cob) * 0.9)
			# strelnice: udupana hlina
			if x < -12.2 and z > -8.0:
				grass *= 0.35
			var dirt := maxf(0.0, 1.0 - cob - grass)
			c.append(Color(grass, dirt, cob, 1.0))
	for j in nz - 1:
		for i in nx - 1:
			var a := j * nx + i
			idx.append(a)
			idx.append(a + 1)
			idx.append(a + nx)
			idx.append(a + 1)
			idx.append(a + nx + 1)
			idx.append(a + nx)
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nr
	arr[Mesh.ARRAY_COLOR] = c
	arr[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mi := MeshInstance3D.new()
	mi.name = "Dvur"
	mi.mesh = mesh
	mi.material_override = info["terrain_mat"]
	parent.add_child(mi)
	var body := StaticBody3D.new()
	body.name = "DvurKolize"
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(36.0, 1.0, 30.0)
	cs.shape = sh
	cs.position = Vector3(0, -0.5, 0)
	body.add_child(cs)
	parent.add_child(body)


func _guardhouse(parent: Node3D) -> void:
	var b := Batch.new(M, 201)
	var x0 := -12.0
	var x1 := -4.2
	var z0 := 8.5
	var z1 := 14.0
	var h := 3.0
	var t := 0.5
	var slope := 2.4 / (z1 - z0)
	Fort.wall_x(b, "plaster_worn", x0, x1, z0, z0 + t, 0.0, h, [[-6.6, -5.5, 0.0, 2.05], [-10.2, -9.2, 1.2, 2.2]], PLASTER)
	Fort.wall_z(b, "plaster_worn", z0 + t, z1, x0, x0 + t, 0.0, h, [], PLASTER)
	Fort.wall_z(b, "plaster_worn", z0 + t, z1, x1 - t, x1, 0.0, h, [], PLASTER)
	b.tri_slab("plaster_worn", Vector3(x0 + t, h, z0), Vector3(x0 + t, h, z1), Vector3(x0 + t, h + 2.4, z1), t, PLASTER)
	b.tri_slab("plaster_worn", Vector3(x1, h, z0), Vector3(x1, h, z1), Vector3(x1, h + 2.4, z1), t, PLASTER)
	b.bb("stone", Vector3(x0 - 0.05, 0.0, z0 - 0.06), Vector3(x1 + 0.05, 0.5, z0 + 0.02), Color.WHITE, false, -1, 0, true)
	b.bb("ashlar", Vector3(x0 - 0.05, 0.0, z0 - 0.05), Vector3(x0 + 0.45, h, z0 + 0.5), Color(0.9, 0.88, 0.84))
	b.bb("ashlar", Vector3(x1 - 0.45, 0.0, z0 - 0.05), Vector3(x1 + 0.05, h, z0 + 0.5), Color(0.9, 0.88, 0.84))
	# pultova strecha
	var ya := h - 0.45 * slope
	b.slab("shingles", Vector3(x0 - 0.4, ya, z0 - 0.45), Vector3(x1 + 0.4, ya, z0 - 0.45), Vector3(x1 + 0.4, h + 2.4, z1), Vector3(x0 - 0.4, h + 2.4, z1), 0.14, Color(0.9, 0.87, 0.83), false, "planks")
	var rx := x0 + 0.9
	while rx < x1 - 0.3:
		b.beam("beam", Vector3(rx, h - 0.16, z0 + 0.1), Vector3(rx, h + 2.24, z1), 0.12, 0.16, DARK)
		rx += 1.2
	b.beam("beam", Vector3(x0, h - 0.1, z0 + 0.25), Vector3(x1, h - 0.1, z0 + 0.25), 0.2, 0.2, DARK)
	b.bb("planks", Vector3(x0 + t, 0.0, z0 + t), Vector3(x1 - t, 0.03, z1), WOOD, false, 0)
	b.bb("beam", Vector3(-6.75, 2.05, z0 - 0.04), Vector3(-5.35, 2.25, z0 + t + 0.04), DARK, false, 0)
	b.bb("beam", Vector3(-10.3, 1.1, z0 - 0.05), Vector3(-9.1, 1.2, z0 + t + 0.03), DARK, false, 0)
	b.bb("beam", Vector3(-10.3, 2.2, z0 - 0.05), Vector3(-9.1, 2.32, z0 + t + 0.03), DARK, false, 0)
	for bx: float in [-9.95, -9.7, -9.45]:
		b.rod("iron", Vector3(bx, 1.2, z0 + 0.25), Vector3(bx, 2.2, z0 + 0.25), 0.014, 5)
	# vybaveni
	P.weapon_rack(b, Props.at(Vector3(-8.3, 0.03, 13.72)), 2.4, 6, true)
	P.sword_rack(b, Props.at(Vector3(x0 + t + 0.01, 1.8, 10.2), 90.0), 4)
	P.shield(b, Props.at(Vector3(x1 - t - 0.03, 1.95, 10.3), -90.0), Color(0.5, 0.12, 0.1), Color(0.86, 0.82, 0.7))
	P.shield(b, Props.at(Vector3(x1 - t - 0.03, 1.95, 11.2), -90.0), Color(0.14, 0.2, 0.36), Color(0.82, 0.7, 0.3))
	P.shield(b, Props.at(Vector3(x1 - t - 0.03, 1.95, 12.1), -90.0), Color(0.5, 0.12, 0.1), Color(0.2, 0.2, 0.2))
	P.armor_stand(b, Vector3(-5.5, 0.03, 13.3), 180.0)
	P.armor_stand(b, Vector3(-6.4, 0.03, 13.4), 170.0)
	P.table(b, Props.at(Vector3(-8.0, 0.03, 10.7)), 2.0, 0.8)
	P.bench(b, Props.at(Vector3(-8.0, 0.03, 10.0)), 1.9)
	P.bench(b, Props.at(Vector3(-8.0, 0.03, 11.4)), 1.9)
	P.mug(b, Vector3(-8.4, 0.81, 10.6))
	P.mug(b, Vector3(-7.6, 0.81, 10.85))
	P.jug(b, Vector3(-8.0, 0.81, 10.7))
	P.candle(b, Vector3(-7.3, 0.81, 10.6), true)
	b.rod("beam", Vector3(-8.75, 0.83, 10.75), Vector3(-8.55, 0.83, 10.95), 0.012, 4)
	P.bed(b, Props.at(Vector3(-10.75, 0.03, 12.9)), Color(0.36, 0.33, 0.28))
	P.chest(b, Props.at(Vector3(-10.75, 0.03, 11.5)), 1.0)
	P.brazier(b, Vector3(-6.4, 0.03, 11.6))
	P.barrel(b, Vector3(-5.1, 0.03, 9.5))
	for k in 4:
		P.spear(b, Vector3(-5.1 + 0.05 * k, 0.5, 9.45 + 0.03 * k), Vector3(-5.0 + 0.1 * k, 2.3, 9.6 - 0.05 * k))
	P.shelf(b, Props.at(Vector3(-8.2, 0.03, z0 + t + 0.2)), 1.6, 1.8, 3)
	for k in 3:
		b.lathe("steel", Transform3D(Basis.IDENTITY, Vector3(-8.7 + 0.5 * k, 1.07, z0 + t + 0.2)),
				PackedVector2Array([Vector2(0.2, 0.0), Vector2(0.12, 0.02), Vector2(0.115, 0.09), Vector2(0.08, 0.15), Vector2(0.0, 0.18)]), 10)
	P.torch(b, Vector3(-9.0, 2.0, z1 - 0.02), Vector3(0, 0, -1), false)
	info["rooms"].append({"name": "straznice", "aabb": AABB(Vector3(x0 + t, 0, z0 + t), Vector3(x1 - x0 - 2 * t, 5.2, z1 - z0 - t)), "ambient": Color(0.21, 0.2, 0.19)})
	b.commit(parent, "Straznice")


func _smithy(parent: Node3D) -> void:
	var b := Batch.new(M, 202)
	var x0 := 11.0
	var x1 := 17.0
	var z0 := 3.0
	var z1 := 9.5
	# sloupy a krov
	for pz: float in [z0 + 0.2, (z0 + z1) * 0.5, z1 - 0.2]:
		b.beam("beam", Vector3(x0 + 0.2, 0.0, pz), Vector3(x0 + 0.2, 2.95, pz), 0.2, 0.2, DARK, true)
		b.beam("beam", Vector3(x0 + 0.2, 2.2, pz), Vector3(x0 + 1.0, 3.05, pz), 0.1, 0.1, DARK)
		b.beam("beam", Vector3(x0 + 0.2, 2.9, pz), Vector3(x1, 4.6, pz), 0.14, 0.18, DARK)
	b.beam("beam", Vector3(x0 + 0.2, 2.95, z0 - 0.2), Vector3(x0 + 0.2, 2.95, z1 + 0.2), 0.2, 0.2, DARK)
	b.slab("shingles", Vector3(x0 - 0.5, 2.78, z0 - 0.4), Vector3(x0 - 0.5, 2.78, z1 + 0.4), Vector3(x1, 4.78, z1 + 0.4), Vector3(x1, 4.78, z0 - 0.4), 0.14, Color(0.9, 0.87, 0.83), false, "planks")
	# bocni steny z prken
	var nb := 0
	var px := x0 + 0.5
	while px < x1 - 0.05:
		var top := 2.9 + (px - x0) * 0.283
		b.bb("planks", Vector3(px, 0.0, z0 + 0.08), Vector3(px + 0.27, top, z0 + 0.13), Color(OLD.r + b.jitter(0.05), OLD.g + b.jitter(0.05), OLD.b + b.jitter(0.04)), false, 1)
		px += 0.29
		nb += 1
	b.boxes.append([Transform3D(Basis.IDENTITY, Vector3((x0 + x1) * 0.5 + 0.25, 1.6, z0 + 0.1)), Vector3(x1 - x0 - 0.5, 3.2, 0.12)])
	px = 13.2
	while px < x1 - 0.05:
		b.bb("planks", Vector3(px, 0.0, z1 - 0.13), Vector3(px + 0.27, 1.05 + b.jitter(0.03), z1 - 0.08), Color(OLD.r + b.jitter(0.05), OLD.g + b.jitter(0.05), OLD.b + b.jitter(0.04)), false, 1)
		px += 0.29
	b.boxes.append([Transform3D(Basis.IDENTITY, Vector3(15.1, 0.55, z1 - 0.1)), Vector3(3.8, 1.1, 0.12)])
	b.bb("flag", Vector3(13.4, 0.0, 4.2), Vector3(x1, 0.04, 8.3), Color(0.8, 0.78, 0.74))
	# vyhen
	b.bb("stone", Vector3(15.6, 0.0, 5.2), Vector3(x1, 0.95, 7.2), Color.WHITE, true, -1, 0, true)
	b.bb("ashlar", Vector3(15.55, 0.95, 5.15), Vector3(x1, 1.05, 7.25), Color(0.8, 0.78, 0.74))
	b.bb("coal", Vector3(15.85, 1.05, 5.5), Vector3(16.8, 1.08, 6.9))
	b.ball("ember", Vector3(16.3, 1.09, 6.2), Vector3(0.36, 0.05, 0.42), 10)
	for k in 9:
		b.ball("coal", Vector3(15.95 + 0.1 * (k % 3) + b.jitter(0.25), 1.1, 5.7 + 0.14 * k), Vector3(0.06, 0.04, 0.06), 6)
	info["fires"].append({"kind": "forge", "pos": Vector3(16.3, 1.16, 6.2), "night_only": false, "size": 0.7, "name": "vyhen"})
	info["use"].append({"kind": "fire", "pos": Vector3(15.3, 1.1, 6.2), "r": 1.9, "name": "vyhen"})
	# digestor a komin
	var pc := Color(0.74, 0.72, 0.68)
	b.slab("plaster", Vector3(15.5, 2.0, 5.1), Vector3(15.5, 2.0, 7.3), Vector3(16.15, 3.5, 6.65), Vector3(16.15, 3.5, 5.75), 0.1, pc)
	b.slab("plaster", Vector3(15.5, 2.0, 5.1), Vector3(x1, 2.0, 5.1), Vector3(x1, 3.5, 5.75), Vector3(16.15, 3.5, 5.75), 0.1, pc)
	b.slab("plaster", Vector3(15.5, 2.0, 7.3), Vector3(x1, 2.0, 7.3), Vector3(x1, 3.5, 6.65), Vector3(16.15, 3.5, 6.65), 0.1, pc)
	b.bb("stone", Vector3(16.15, 3.4, 5.75), Vector3(x1, 8.4, 6.65), Color.WHITE, true, -1, 0, true)
	b.bb("flag", Vector3(16.05, 8.4, 5.65), Vector3(x1 + 0.1, 8.5, 6.75), Color(0.8, 0.8, 0.78))
	info["smoke"].append(Vector3(16.55, 8.7, 6.2))
	# mech
	b.box("leather", Transform3D(Basis(Vector3(0, 0, 1), deg_to_rad(8.0)), Vector3(14.75, 1.15, 5.55)), Vector3(1.1, 0.26, 0.6), Color(0.8, 0.7, 0.6))
	b.box("planks", Transform3D(Basis(Vector3(0, 0, 1), deg_to_rad(14.0)), Vector3(14.75, 1.32, 5.55)), Vector3(1.15, 0.03, 0.62), DARK, false, 0)
	b.box("planks", Transform3D(Basis.IDENTITY, Vector3(14.75, 0.99, 5.55)), Vector3(1.15, 0.03, 0.62), DARK, false, 0)
	b.rod("iron", Vector3(15.3, 1.1, 5.55), Vector3(15.9, 1.12, 5.8), 0.03, 6)
	for sz: float in [5.3, 5.8]:
		b.beam("beam", Vector3(14.3, 0.0, sz), Vector3(14.3, 0.98, sz), 0.08, 0.08, DARK)
		b.beam("beam", Vector3(15.2, 0.0, sz), Vector3(15.2, 0.98, sz), 0.08, 0.08, DARK)
	b.rod("beam", Vector3(14.2, 1.45, 5.55), Vector3(13.4, 1.9, 5.55), 0.025, 5, DARK)
	# kovadlina, kaleni, brus
	P.anvil(b, Vector3(13.7, 0.0, 6.3), 25.0)
	info["use"].append({"kind": "anvil", "pos": Vector3(13.7, 0.95, 6.3), "r": 1.6})
	info["anvil"] = Vector3(13.7, 0.9, 6.3)
	P.hammer(b, Props.at(Vector3(13.75, 0.89, 6.3), 60.0))
	P.barrel(b, Vector3(14.7, 0.0, 8.5), 0.36, 0.8)
	b.lathe("water", Transform3D(Basis.IDENTITY, Vector3(14.7, 0.0, 8.5)), PackedVector2Array([Vector2(0.0, 0.7), Vector2(0.3, 0.7)]), 12)
	P.grindstone(b, Vector3(12.3, 0.0, 8.5), 90.0)
	# ponk s naradim
	P.table(b, Props.at(Vector3(13.6, 0.0, 3.75)), 2.6, 0.7, 0.86)
	P.hammer(b, Props.at(Vector3(13.0, 0.87, 3.7), 20.0))
	P.hammer(b, Props.at(Vector3(13.4, 0.87, 3.85), -40.0))
	P.tongs(b, Props.at(Vector3(14.0, 0.87, 3.7), 10.0))
	P.tongs(b, Props.at(Vector3(14.3, 0.87, 3.85), -25.0))
	P.sword(b, Vector3(12.5, 0.88, 3.55), Vector3(13.5, 0.88, 3.5), Vector3(0, 0, 1))
	for k in 4:
		var hy := 1.55
		var hx := 12.6 + 0.5 * k
		b.rod("iron", Vector3(hx, hy, z0 + 0.14), Vector3(hx, hy, z0 + 0.24), 0.008, 4)
		var pts := PackedVector3Array()
		for q in 9:
			var a := PI + PI * q / 8.0
			pts.append(Vector3(hx + cos(a) * 0.06, hy - 0.08 + sin(a) * -0.08 - 0.02, z0 + 0.2))
		b.tube("iron", pts, 0.012, 4)
	b.beam("beam", Vector3(12.2, 1.9, z0 + 0.16), Vector3(15.2, 1.9, z0 + 0.16), 0.07, 0.07, DARK)
	for k in 5:
		P.tongs(b, Transform3D(Basis(Vector3(0, 0, 1), PI * 0.5), Vector3(12.5 + 0.55 * k, 1.6, z0 + 0.2)))
	# uhli, zelezo, sud
	b.ball("coal", Vector3(16.3, 0.12, 8.3), Vector3(0.65, 0.3, 0.5), 10)
	b.bb("planks", Vector3(15.6, 0.0, 7.7), Vector3(15.66, 0.45, 8.9), DARK, false, 2)
	for k in 6:
		b.rod("iron", Vector3(12.0 + 0.05 * k, 0.03 + 0.03 * (k % 2), 4.6), Vector3(12.1 + 0.05 * k, 0.03 + 0.03 * (k % 2), 6.4), 0.014, 4)
	P.bucket(b, Vector3(13.0, 0.0, 7.4), true)
	P.torch(b, Vector3(x0 + 0.32, 2.3, (z0 + z1) * 0.5), Vector3(1, 0, 0))
	b.commit(parent, "Kovarna")


func _range(parent: Node3D) -> void:
	var b := Batch.new(M, 203)
	# terce v nadvori
	P.straw_target(b, Props.at(Vector3(-14.9, 0.0, -3.4)), 0.6)
	P.straw_target(b, Props.at(Vector3(-13.5, 0.0, -6.6)), 0.6)
	# zachytna stena ze slamy a prken
	for r in 3:
		for k in 4:
			P.hay_bale(b, Props.at(Vector3(-16.4 + 1.03 * k + (0.4 if r % 2 == 1 else 0.0), 0.5 * r, -8.2), b.jitter(3.0)))
	var px := -16.9
	while px < -12.2:
		b.bb("planks", Vector3(px, 0.0, -8.62), Vector3(px + 0.3, 2.6 + b.jitter(0.08), -8.56), Color(OLD.r + b.jitter(0.05), OLD.g + b.jitter(0.05), OLD.b + b.jitter(0.04)), false, 1)
		px += 0.32
	# strelecka cara a stojan s luky
	b.beam("beam", Vector3(-16.6, 0.9, 10.6), Vector3(-12.9, 0.9, 10.6), 0.08, 0.1, WOOD, true)
	for sx: float in [-16.6, -14.75, -12.9]:
		b.beam("beam", Vector3(sx, 0.0, 10.6), Vector3(sx, 0.92, 10.6), 0.1, 0.1, DARK)
	var st := Props.at(Vector3(-15.9, 0.0, 12.9))
	for sx: float in [-0.6, 0.6]:
		b.beam("beam", st * Vector3(sx, 0.0, 0.0), st * Vector3(sx, 1.5, 0.0), 0.08, 0.08, DARK)
		b.beam("beam", st * Vector3(sx, 0.04, -0.3), st * Vector3(sx, 0.04, 0.3), 0.08, 0.08, DARK)
	b.beam("beam", st * Vector3(-0.7, 1.45, 0.0), st * Vector3(0.7, 1.45, 0.0), 0.06, 0.08, DARK)
	b.beam("beam", st * Vector3(-0.7, 0.35, 0.0), st * Vector3(0.7, 0.35, 0.0), 0.06, 0.08, DARK)
	for k in 3:
		P.bow(b, st * Transform3D(Basis(Vector3(1, 0, 0), deg_to_rad(-7.0)), Vector3(-0.4 + 0.4 * k, 0.86, -0.12)))
	P.quiver(b, Vector3(-14.9, 0.0, 12.9))
	P.quiver(b, Vector3(-14.6, 0.0, 13.1), 6)
	b.boxes.append([Transform3D(Basis.IDENTITY, Vector3(-15.9, 0.8, 12.9)), Vector3(1.5, 1.6, 0.5)])
	info["use"].append({"kind": "bow", "pos": Vector3(-15.6, 1.0, 12.8), "r": 2.2})
	# ohrazeni drahy
	var z := -7.2
	while z < 10.0:
		b.beam("beam", Vector3(-12.45, 0.0, z), Vector3(-12.45, 0.85, z), 0.09, 0.09, DARK)
		z += 2.86
	b.rod("fabric", Vector3(-12.45, 0.75, -7.2), Vector3(-12.45, 0.75, 9.96), 0.012, 4, Color(0.7, 0.62, 0.45))
	# terce pod hradbami, na ktere se strili z ochozu
	var T: RefCounted = info["terrain"]
	for o: Array in [[Vector2(-44, -2), 0.8], [Vector2(-60, 9), 0.9], [Vector2(-80, -8), 1.0]]:
		var p: Vector2 = o[0]
		P.straw_target(b, Props.at(Vector3(p.x, T.height(p.x, p.y) - 0.05, p.y), 90.0), o[1])
	b.commit(parent, "Strelnice")


func _misc(parent: Node3D) -> void:
	var b := Batch.new(M, 204)
	P.well(b, Vector3(-3.6, 0.0, -1.6))
	P.cart(b, Props.at(Vector3(8.6, 0.0, 1.2), 35.0))
	P.hay_pile(b, Vector3(10.2, 0.0, -1.2), 1.1)
	# drivi pod pavlaci a spalek se sekerou
	P.woodpile(b, Props.at(Vector3(12.6, 0.0, -6.45)), 2.2, 6)
	b.cyl("bark", Vector3(15.6, 0.0, -5.2), 0.3, 0.27, 0.5, 10, Color(0.9, 0.86, 0.8))
	b.lathe("planks", Transform3D(Basis.IDENTITY, Vector3(15.6, 0.0, -5.2)), PackedVector2Array([Vector2(0.0, 0.5), Vector2(0.27, 0.5)]), 10, Color(0.85, 0.76, 0.62))
	b.rod("beam", Vector3(15.55, 0.52, -5.2), Vector3(15.9, 1.15, -5.3), 0.018, 5, WOOD)
	b.box("steel", Transform3D(Basis(Vector3(0, 0, 1), deg_to_rad(-60.0)), Vector3(15.58, 0.58, -5.2)), Vector3(0.18, 0.02, 0.12), Color(0.6, 0.6, 0.62))
	P.logs(b, Props.at(Vector3(15.0, 0.0, -4.8), 30.0), 3, 0.5)
	# sudy, bedny a pytle
	P.barrel(b, Vector3(1.6, 0.0, -6.3))
	P.barrel(b, Vector3(2.3, 0.0, -6.25), 0.3, 0.85)
	P.bucket(b, Vector3(-4.9, 0.0, -0.6), true)
	P.crate(b, Props.at(Vector3(3.2, 0.0, 8.6), 12.0))
	P.crate(b, Props.at(Vector3(3.3, 0.7, 8.55), -8.0), 0.5)
	P.sack(b, Vector3(2.5, 0.0, 8.0))
	P.sack(b, Vector3(2.9, 0.0, 7.6), 0.3, true)
	P.barrel(b, Vector3(-3.0, 0.0, 8.8), 0.36, 1.0)
	# napajeci zlab u schodu na hradbu
	b.bb("planks", Vector3(6.0, 0.25, 11.0), Vector3(8.2, 0.3, 11.6), OLD, false, 0)
	for sz: float in [11.0, 11.57]:
		b.bb("planks", Vector3(6.0, 0.3, sz), Vector3(8.2, 0.6, sz + 0.04), OLD, false, 0)
	for sx: float in [6.0, 8.16]:
		b.bb("planks", Vector3(sx, 0.0, 10.95), Vector3(sx + 0.05, 0.62, 11.65), OLD, false, 2)
	b.bb("water", Vector3(6.05, 0.5, 11.04), Vector3(8.16, 0.52, 11.57))
	b.boxes.append([Transform3D(Basis.IDENTITY, Vector3(7.1, 0.3, 11.3)), Vector3(2.3, 0.6, 0.7)])
	b.beam("beam", Vector3(5.4, 0.0, 10.4), Vector3(5.4, 1.1, 10.4), 0.12, 0.12, DARK, true)
	b.beam("beam", Vector3(9.0, 0.0, 10.4), Vector3(9.0, 1.1, 10.4), 0.12, 0.12, DARK, true)
	b.beam("beam", Vector3(5.3, 1.0, 10.4), Vector3(9.1, 1.0, 10.4), 0.09, 0.09, DARK, true)
	# lavice pod stromem na dvore
	for k in 4:
		var a := k * 90.0 + 20.0
		var o := Vector3(sin(deg_to_rad(a)), 0, cos(deg_to_rad(a))) * 1.25
		P.bench(b, Props.at(Vector3(-7.0, 0.0, 1.6) + o, a), 1.5)
	b.collider(Vector3(-7.0, 1.5, 1.6), Vector3(0.9, 3.0, 0.9))
	info["yard_tree"] = Vector3(-7.0, 0.0, 1.6)
	# zebrik opreny o hradbu a sudy na ochozu
	P.ladder(b, Vector3(-16.0, 0.0, 4.0), Vector3(-16.25, 6.3, 5.2), Vector3(0, 0, 1))
	P.barrel(b, Vector3(-17.7, 6.53, 13.2), 0.3, 0.8)
	P.barrel(b, Vector3(18.0, 6.53, 15.0), 0.3, 0.8)
	P.quiver(b, Vector3(-17.75, 6.53, 0.5))
	P.crate(b, Props.at(Vector3(-7.5, 6.53, 14.75), 5.0), 0.55)
	# louce: brana, dvere, hradby
	P.torch(b, Vector3(-1.58, 2.3, 11.0), Vector3(1, 0, 0))
	P.torch(b, Vector3(1.58, 2.3, 15.0), Vector3(-1, 0, 0))
	P.torch(b, Vector3(6.6, 2.5, -6.98), Vector3(0, 0, 1))
	P.torch(b, Vector3(9.4, 2.5, -6.98), Vector3(0, 0, 1))
	P.torch(b, Vector3(-5.0, 2.35, 8.48), Vector3(0, 0, -1))
	P.torch(b, Vector3(-11.78, 2.5, -11.7), Vector3(1, 0, 0))
	P.torch(b, Vector3(-3.6, 5.2, 13.98), Vector3(0, 0, -1))
	P.torch(b, Vector3(-16.98, 5.2, 2.0), Vector3(1, 0, 0))
	P.torch(b, Vector3(16.98, 5.2, 0.0), Vector3(-1, 0, 0))
	P.torch(b, Vector3(-1.2, 5.6, -6.98), Vector3(0, 0, 1))
	P.torch(b, Vector3(12.8, 5.6, -6.98), Vector3(0, 0, 1))
	# vez: vybaveni
	P.barrel(b, Vector3(-14.0, 0.0, -11.0))
	P.barrel(b, Vector3(-14.0, 0.0, -10.8 + 0.75), 0.3, 0.85)
	P.crate(b, Props.at(Vector3(-15.0, 0.0, -10.9), 10.0))
	P.sack(b, Vector3(-16.0, 0.0, -10.9))
	P.torch(b, Vector3(-13.32, 2.2, -11.0), Vector3(-1, 0, 0), false)
	P.torch(b, Vector3(-15.8, 8.6, -10.32), Vector3(0, 0, -1), false)
	P.chest(b, Props.at(Vector3(-14.0, 6.5, -10.8), 0.0), 1.0)
	P.weapon_rack(b, Props.at(Vector3(-15.6, 6.5, -10.5), 0.0), 1.6, 4, false)
	P.brazier(b, Vector3(-15.8, 13.0, -12.4))
	P.bench(b, Props.at(Vector3(-14.2, 13.0, -11.0), 0.0), 1.6)
	# branka nad prujezdem
	P.table(b, Props.at(Vector3(0.0, 6.54, 12.2)), 1.6, 0.7)
	P.stool(b, Props.at(Vector3(-0.4, 6.54, 11.5)))
	P.stool(b, Props.at(Vector3(0.6, 6.54, 12.9)))
	P.candle(b, Vector3(0.3, 7.32, 12.2), true)
	P.mug(b, Vector3(-0.3, 7.32, 12.1))
	P.barrel(b, Vector3(2.1, 6.54, 10.9), 0.3, 0.85)
	P.weapon_rack(b, Props.at(Vector3(-1.8, 6.54, 10.8), 180.0), 1.2, 3, true)
	b.commit(parent, "Dvur")

	# prapor na vezi
	var f := Batch.new(M, 205)
	var pole: Vector3 = info["flag_pole"]
	f.cyl("beam", pole - Vector3(0, 0.6, 0), 0.05, 0.03, 4.6, 6, DARK)
	P.banner_card(f, pole + Vector3(0.04, 3.9, 0), Vector3(1.5, 0, 0), Vector3(0, -2.6, 0))
	f.commit(parent, "Prapor", false)
