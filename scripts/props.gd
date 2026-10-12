extends RefCounted
## Knihovna vybaveni: nabytek, zbrane, sudy, svice... Vse se sklada z kvadru, valcu a rotacnich teles.
## Kazda funkce dostane davku (Batch) a transformaci, kam vec postavit (osa -Z je "dopredu").

const Batch := preload("res://scripts/mesh_batch.gd")

const WOOD := Color(0.82, 0.76, 0.68)
const DARK := Color(0.58, 0.52, 0.46)
const OLD := Color(0.66, 0.63, 0.6)
const IRON := Color(0.75, 0.75, 0.75)

var info: Dictionary
var rng := RandomNumberGenerator.new()


func _init(p_info: Dictionary) -> void:
	info = p_info
	rng.seed = 808


static func at(pos: Vector3, yaw_deg: float = 0.0) -> Transform3D:
	return Transform3D(Basis(Vector3.UP, deg_to_rad(yaw_deg)), pos)


func _b(b: Batch, key: String, t: Transform3D, c: Vector3, size: Vector3, col: Color = Color.WHITE, grain: int = -1, collide: bool = false) -> void:
	b.box(key, t * Transform3D(Basis.IDENTITY, c), size, col, collide, grain)


func _br(b: Batch, key: String, t: Transform3D, c: Vector3, size: Vector3, euler_deg: Vector3, col: Color = Color.WHITE, grain: int = -1) -> void:
	var rot := Basis.from_euler(Vector3(deg_to_rad(euler_deg.x), deg_to_rad(euler_deg.y), deg_to_rad(euler_deg.z)))
	b.box(key, t * Transform3D(rot, c), size, col, false, grain)


func _col(base: Color, amount: float = 0.06) -> Color:
	var k := 1.0 + rng.randf_range(-amount, amount)
	return Color(base.r * k, base.g * k, base.b * k)


# ------------------------------------------------------------------ nabytek

func table(b: Batch, t: Transform3D, length: float, width: float, height: float = 0.78) -> void:
	var n := 3
	for i in n:
		var z := -width * 0.5 + width * (i + 0.5) / n
		_b(b, "planks", t, Vector3(0, height - 0.035, z), Vector3(length, 0.07, width / n - 0.012), _col(WOOD), 0)
	for sx: float in [-1.0, 1.0]:
		var x := sx * (length * 0.5 - 0.4)
		b.beam("beam", t * Vector3(x, 0.0, -width * 0.42), t * Vector3(x, height - 0.07, -width * 0.12), 0.08, 0.1, DARK)
		b.beam("beam", t * Vector3(x, 0.0, width * 0.42), t * Vector3(x, height - 0.07, width * 0.12), 0.08, 0.1, DARK)
		_b(b, "beam", t, Vector3(x, height - 0.11, 0), Vector3(0.09, 0.08, width * 0.8), DARK, 2)
	b.beam("beam", t * Vector3(-length * 0.5 + 0.4, 0.3, 0), t * Vector3(length * 0.5 - 0.4, 0.3, 0), 0.07, 0.09, DARK)
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, height * 0.5, 0)), Vector3(length, height, width)])


func bench(b: Batch, t: Transform3D, length: float) -> void:
	_b(b, "planks", t, Vector3(0, 0.45, 0), Vector3(length, 0.06, 0.3), _col(WOOD), 0)
	for sx: float in [-1.0, 1.0]:
		_b(b, "planks", t, Vector3(sx * (length * 0.5 - 0.25), 0.21, 0), Vector3(0.06, 0.42, 0.28), DARK, 1)
	b.beam("beam", t * Vector3(-length * 0.5 + 0.25, 0.2, 0), t * Vector3(length * 0.5 - 0.25, 0.2, 0), 0.05, 0.07, DARK)
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, 0.24, 0)), Vector3(length, 0.48, 0.3)])


func stool(b: Batch, t: Transform3D) -> void:
	b.cyl("planks", t * Vector3(0, 0.42, 0), 0.19, 0.19, 0.05, 10, _col(WOOD))
	for k in 3:
		var a := TAU * k / 3.0
		b.rod("beam", t * Vector3(cos(a) * 0.2, 0, sin(a) * 0.2), t * Vector3(cos(a) * 0.1, 0.43, sin(a) * 0.1), 0.025, 6, DARK)


func chair(b: Batch, t: Transform3D) -> void:
	_b(b, "planks", t, Vector3(0, 0.46, 0), Vector3(0.5, 0.05, 0.46), _col(WOOD), 0)
	for sx: float in [-0.22, 0.22]:
		_b(b, "beam", t, Vector3(sx, 0.22, -0.2), Vector3(0.06, 0.45, 0.06), DARK, 1)
		_b(b, "beam", t, Vector3(sx, 0.7, 0.2), Vector3(0.06, 1.4, 0.06), DARK, 1)
	_b(b, "planks", t, Vector3(0, 1.0, 0.2), Vector3(0.44, 0.6, 0.04), _col(WOOD), 1)
	_b(b, "beam", t, Vector3(0, 1.38, 0.2), Vector3(0.52, 0.08, 0.07), DARK, 0)
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, 0.4, 0)), Vector3(0.5, 0.8, 0.46)])


func bed(b: Batch, t: Transform3D, cover: Color = Color(0.5, 0.16, 0.14)) -> void:
	var l := 2.05
	var w := 1.4
	# ram
	for sx: float in [-1.0, 1.0]:
		_b(b, "beam", t, Vector3(sx * w * 0.5, 0.75, -l * 0.5), Vector3(0.1, 1.5, 0.1), DARK, 1)
		_b(b, "beam", t, Vector3(sx * w * 0.5, 0.45, l * 0.5), Vector3(0.1, 0.9, 0.1), DARK, 1)
		_b(b, "planks", t, Vector3(sx * w * 0.5, 0.4, 0), Vector3(0.05, 0.24, l), _col(WOOD), 2)
	_b(b, "planks", t, Vector3(0, 0.9, -l * 0.5), Vector3(w, 0.9, 0.05), _col(WOOD), 1)
	_b(b, "planks", t, Vector3(0, 0.5, l * 0.5), Vector3(w, 0.5, 0.05), _col(WOOD), 1)
	_b(b, "planks", t, Vector3(0, 0.3, 0), Vector3(w, 0.04, l), DARK, 2)
	# slamnik, prosteradlo, prikryvka, polstar
	_b(b, "straw", t, Vector3(0, 0.42, 0), Vector3(w - 0.08, 0.2, l - 0.1), Color(0.9, 0.86, 0.75))
	_b(b, "fabric", t, Vector3(0, 0.535, -0.05), Vector3(w - 0.06, 0.04, l - 0.16), Color(0.92, 0.9, 0.84))
	_b(b, "fabric", t, Vector3(0, 0.57, 0.28), Vector3(w + 0.04, 0.07, l * 0.62), cover)
	_b(b, "fabric", t, Vector3(0, 0.6, -0.26), Vector3(w + 0.04, 0.03, 0.3), Color(cover.r * 1.3, cover.g * 1.3, cover.b * 1.3))
	b.ball("fabric", t * Vector3(0, 0.63, -l * 0.5 + 0.34), Vector3(0.42, 0.1, 0.2), 10, Color(0.94, 0.92, 0.86))
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, 0.35, 0)), Vector3(w + 0.1, 0.7, l + 0.1)])
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, 0.75, -l * 0.5)), Vector3(w + 0.1, 1.5, 0.1)])


func chest(b: Batch, t: Transform3D, w: float = 1.0) -> void:
	var d := 0.5
	var h := 0.48
	_b(b, "planks", t, Vector3(0, h * 0.5, 0), Vector3(w, h, d), _col(WOOD), 0)
	_b(b, "planks", t, Vector3(0, h + 0.05, 0), Vector3(w + 0.03, 0.1, d + 0.03), _col(DARK), 0)
	_b(b, "planks", t, Vector3(0, h + 0.12, 0), Vector3(w - 0.06, 0.06, d - 0.1), _col(DARK), 0)
	for sx: float in [-0.35, 0.35]:
		_b(b, "iron", t, Vector3(sx * w, h * 0.5 + 0.05, 0), Vector3(0.05, h + 0.14, d + 0.05), IRON)
	_b(b, "iron", t, Vector3(0, h - 0.04, d * 0.5 + 0.015), Vector3(0.1, 0.14, 0.03), IRON)
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, 0.3, 0)), Vector3(w, 0.62, d)])


func barrel(b: Batch, pos: Vector3, r: float = 0.33, h: float = 0.95, lying_yaw: float = -1000.0) -> void:
	var prof := PackedVector2Array([Vector2(r * 0.82, 0.0), Vector2(r * 0.95, h * 0.2), Vector2(r, h * 0.5), Vector2(r * 0.95, h * 0.8), Vector2(r * 0.82, h)])
	var xf := Transform3D(Basis.IDENTITY, pos)
	if lying_yaw > -999.0:
		xf = Transform3D(Basis(Vector3.UP, deg_to_rad(lying_yaw)) * Basis(Vector3(0, 0, 1), PI * 0.5), pos + Vector3(0, r, 0))
	b.lathe("planks", xf, prof, 14, _col(WOOD), false, false)
	for fy: float in [0.1, 0.32, 0.68, 0.9]:
		var rr := r * (0.86 + 0.15 * sin(fy * PI))
		b.lathe("iron", xf, PackedVector2Array([Vector2(rr + 0.008, h * fy - 0.025), Vector2(rr + 0.008, h * fy + 0.025)]), 14, IRON)
	b.lathe("planks", xf, PackedVector2Array([Vector2(0.0, h - 0.04), Vector2(r * 0.8, h - 0.04)]), 14, _col(DARK))
	b.lathe("planks", xf, PackedVector2Array([Vector2(r * 0.8, 0.04), Vector2(0.0, 0.04)]), 14, _col(DARK))
	if lying_yaw > -999.0:
		b.boxes.append([Transform3D(Basis(Vector3.UP, deg_to_rad(lying_yaw)), pos + Vector3(0, r, 0)), Vector3(h, r * 2, r * 2)])
	else:
		b.boxes.append([Transform3D(Basis.IDENTITY, pos + Vector3(0, h * 0.5, 0)), Vector3(r * 1.7, h, r * 1.7)])


func crate(b: Batch, t: Transform3D, s: float = 0.7) -> void:
	_b(b, "planks", t, Vector3(0, s * 0.5, 0), Vector3(s, s, s), _col(WOOD, 0.1), 0, true)
	for sx: float in [-1.0, 1.0]:
		for sz: float in [-1.0, 1.0]:
			_b(b, "beam", t, Vector3(sx * s * 0.5, s * 0.5, sz * s * 0.5), Vector3(0.07, s + 0.02, 0.07), DARK, 1)


func sack(b: Batch, pos: Vector3, s: float = 0.32, lying: bool = false) -> void:
	var col := _col(Color(0.62, 0.52, 0.36), 0.1)
	if lying:
		b.ball("fabric", pos + Vector3(0, s * 0.55, 0), Vector3(s * 1.5, s * 0.6, s), 10, col)
	else:
		b.ball("fabric", pos + Vector3(0, s * 1.0, 0), Vector3(s, s * 1.05, s * 0.9), 10, col)
		b.cyl("fabric", pos + Vector3(0, s * 1.9, 0), s * 0.2, s * 0.32, s * 0.25, 8, col)


func bucket(b: Batch, pos: Vector3, water: bool = false) -> void:
	var xf := Transform3D(Basis.IDENTITY, pos)
	b.lathe("planks", xf, PackedVector2Array([Vector2(0.13, 0.0), Vector2(0.17, 0.3)]), 10, _col(WOOD))
	b.lathe("planks", xf, PackedVector2Array([Vector2(0.155, 0.3), Vector2(0.12, 0.02), Vector2(0.0, 0.02)]), 10, DARK)
	b.lathe("iron", xf, PackedVector2Array([Vector2(0.158, 0.2), Vector2(0.168, 0.25)]), 10, IRON)
	if water:
		b.lathe("water", xf, PackedVector2Array([Vector2(0.0, 0.24), Vector2(0.15, 0.24)]), 10)
	var pts := PackedVector3Array()
	for k in 7:
		var a := PI * k / 6.0
		pts.append(pos + Vector3(cos(a) * 0.17, 0.3 + sin(a) * 0.16, 0))
	b.tube("iron", pts, 0.008, 4, IRON)


func shelf(b: Batch, t: Transform3D, w: float, h: float, levels: int, depth: float = 0.35) -> void:
	for sx: float in [-1.0, 1.0]:
		_b(b, "planks", t, Vector3(sx * w * 0.5, h * 0.5, 0), Vector3(0.05, h, depth), _col(WOOD), 1)
	for k in levels:
		var y := 0.15 + (h - 0.2) * k / maxf(levels - 1, 1)
		_b(b, "planks", t, Vector3(0, y, 0), Vector3(w, 0.04, depth), _col(WOOD), 0)
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, h * 0.5, 0)), Vector3(w, h, depth)])


func rug(b: Batch, t: Transform3D, l: float, w: float, col: Color) -> void:
	_b(b, "fabric", t, Vector3(0, 0.012, 0), Vector3(l, 0.02, w), col)
	_b(b, "fabric", t, Vector3(0, 0.014, 0), Vector3(l - 0.3, 0.02, w - 0.3), Color(col.r * 0.6, col.g * 0.6, col.b * 0.7))
	_b(b, "fabric", t, Vector3(0, 0.016, 0), Vector3(l - 0.7, 0.02, w - 0.7), col)


func hanging(b: Batch, t: Transform3D, w: float, h: float, col: Color) -> void:
	# zaves nebo goblen na tyci
	b.rod("iron", t * Vector3(-w * 0.5 - 0.1, 0, 0.03), t * Vector3(w * 0.5 + 0.1, 0, 0.03), 0.018, 6, IRON)
	_b(b, "fabric", t, Vector3(0, -h * 0.5, 0.03), Vector3(w, h, 0.02), col)
	_b(b, "fabric", t, Vector3(0, -h * 0.5, 0.036), Vector3(w * 0.7, h * 0.75, 0.02), Color(col.r * 0.55, col.g * 0.6, col.b * 0.6))
	_b(b, "fabric", t, Vector3(0, -h * 0.5, 0.042), Vector3(w * 0.3, h * 0.35, 0.02), Color(0.78, 0.66, 0.3))


# ------------------------------------------------------------------ nadobi a drobnosti

func mug(b: Batch, pos: Vector3) -> void:
	b.lathe("planks", Transform3D(Basis.IDENTITY, pos), PackedVector2Array([Vector2(0.04, 0), Vector2(0.045, 0.11), Vector2(0.036, 0.11), Vector2(0.034, 0.02), Vector2(0.0, 0.02)]), 8, _col(DARK))


func jug(b: Batch, pos: Vector3, s: float = 1.0) -> void:
	var prof := PackedVector2Array([Vector2(0.05, 0), Vector2(0.09, 0.07), Vector2(0.1, 0.14), Vector2(0.06, 0.22), Vector2(0.045, 0.26), Vector2(0.06, 0.29)])
	var sc := PackedVector2Array()
	for p in prof:
		sc.append(p * s)
	b.lathe("clay", Transform3D(Basis.IDENTITY, pos), sc, 10, _col(Color(1, 1, 1), 0.12), true)


func plate(b: Batch, pos: Vector3, food: bool = false) -> void:
	b.lathe("planks", Transform3D(Basis.IDENTITY, pos), PackedVector2Array([Vector2(0.0, 0.012), Vector2(0.09, 0.012), Vector2(0.13, 0.03), Vector2(0.13, 0.02), Vector2(0.09, 0.0), Vector2(0.0, 0.0)]), 10, _col(WOOD))
	if food:
		b.ball("paint", pos + Vector3(0, 0.05, 0), Vector3(0.07, 0.04, 0.055), 8, Color(0.62, 0.44, 0.24))


func bread(b: Batch, pos: Vector3) -> void:
	b.ball("paint", pos + Vector3(0, 0.05, 0), Vector3(0.13, 0.06, 0.1), 8, Color(0.58, 0.4, 0.2))


func candle(b: Batch, pos: Vector3, lit: bool = true, height: float = 0.14) -> void:
	b.cyl("iron", pos, 0.045, 0.03, 0.02, 8, IRON)
	b.cyl("wax", pos + Vector3(0, 0.02, 0), 0.016, 0.014, height, 6)
	if lit:
		info["fires"].append({"kind": "candle", "pos": pos + Vector3(0, height + 0.04, 0), "night_only": false})


func book(b: Batch, t: Transform3D, col: Color) -> void:
	_b(b, "leather", t, Vector3(0, 0.025, 0), Vector3(0.2, 0.05, 0.28), col)
	_b(b, "paint", t, Vector3(0.012, 0.025, 0), Vector3(0.19, 0.036, 0.26), Color(0.86, 0.8, 0.66))


func logs(b: Batch, t: Transform3D, n: int = 4, length: float = 0.55) -> void:
	for k in n:
		var x := -0.18 + 0.12 * k
		var y := 0.07 + (0.11 if k % 2 == 1 else 0.0)
		var a := t * Vector3(x, y, -length * 0.5 + rng.randf_range(-0.04, 0.04))
		var c := t * Vector3(x + rng.randf_range(-0.05, 0.05), y, length * 0.5)
		b.rod("bark", a, c, 0.065, 7, _col(Color(0.9, 0.85, 0.8), 0.1))


func woodpile(b: Batch, t: Transform3D, w: float, rows: int) -> void:
	for r in rows:
		var n := int(w / 0.15)
		for k in n:
			var x := -w * 0.5 + 0.075 + 0.15 * k + (0.07 if r % 2 == 1 else 0.0)
			var y := 0.07 + 0.125 * r
			b.rod("bark", t * Vector3(x, y, -0.22), t * Vector3(x, y, 0.22 + rng.randf_range(-0.03, 0.03)), 0.068, 6, _col(Color(0.95, 0.9, 0.85), 0.12))
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, rows * 0.065, 0)), Vector3(w, rows * 0.13, 0.5)])


func hay_pile(b: Batch, pos: Vector3, r: float = 1.0) -> void:
	b.ball("straw", pos + Vector3(0, r * 0.2, 0), Vector3(r, r * 0.55, r * 0.9), 12, Color(0.95, 0.92, 0.8))
	b.ball("straw", pos + Vector3(r * 0.35, r * 0.25, r * 0.2), Vector3(r * 0.6, r * 0.5, r * 0.6), 10, Color(0.9, 0.86, 0.74))
	b.boxes.append([Transform3D(Basis.IDENTITY, pos + Vector3(0, r * 0.3, 0)), Vector3(r * 1.5, r * 0.6, r * 1.4)])


func hay_bale(b: Batch, t: Transform3D) -> void:
	_b(b, "straw", t, Vector3(0, 0.25, 0), Vector3(1.0, 0.5, 0.55), Color(0.95, 0.92, 0.8), -1, true)
	for sx: float in [-0.25, 0.25]:
		_b(b, "leather", t, Vector3(sx, 0.25, 0), Vector3(0.02, 0.51, 0.56), Color(0.5, 0.42, 0.3))


# ------------------------------------------------------------------ svetla

func torch(b: Batch, pos: Vector3, out: Vector3, night_only: bool = true) -> void:
	# drzak na zdi, louc trci sikmo ven
	var o := out.normalized()
	b.rod("iron", pos, pos + o * 0.16 + Vector3(0, -0.05, 0), 0.012, 5, IRON)
	var base := pos + o * 0.16 + Vector3(0, -0.22, 0)
	var tip := pos + o * 0.3 + Vector3(0, 0.3, 0)
	b.rod("beam", base, tip, 0.022, 6, DARK)
	b.rod("soot", tip - (tip - base).normalized() * 0.1, tip + (tip - base).normalized() * 0.04, 0.038, 6)
	b.lathe("iron", Transform3D(Basis.IDENTITY, pos + o * 0.16 + Vector3(0, -0.06, 0)), PackedVector2Array([Vector2(0.03, 0.0), Vector2(0.03, 0.03)]), 6, IRON)
	info["fires"].append({"kind": "torch", "pos": tip + Vector3(0, 0.08, 0), "night_only": night_only})


func chandelier(b: Batch, pos: Vector3, r: float, ceiling_y: float, n: int = 8) -> void:
	var ring := PackedVector3Array()
	for k in 25:
		var a := TAU * k / 24.0
		ring.append(pos + Vector3(cos(a) * r, 0, sin(a) * r))
	b.tube("iron", ring, 0.022, 5, IRON)
	for k in 4:
		var a2 := TAU * k / 4.0 + 0.4
		b.rod("iron", pos + Vector3(cos(a2) * r, 0, sin(a2) * r), Vector3(pos.x, minf(pos.y + 1.3, ceiling_y - 0.4), pos.z), 0.008, 4, IRON)
		b.rod("iron", pos + Vector3(cos(a2) * r, 0, sin(a2) * r), pos, 0.012, 4, IRON)
	b.rod("iron", Vector3(pos.x, minf(pos.y + 1.3, ceiling_y - 0.4), pos.z), Vector3(pos.x, ceiling_y, pos.z), 0.01, 4, IRON)
	for k in n:
		var a3 := TAU * k / n
		var p := pos + Vector3(cos(a3) * r, 0.02, sin(a3) * r)
		b.cyl("iron", p, 0.03, 0.04, 0.02, 6, IRON)
		b.cyl("wax", p + Vector3(0, 0.02, 0), 0.015, 0.013, 0.12, 6)
	info["fires"].append({"kind": "chandelier", "pos": pos + Vector3(0, 0.2, 0), "r": r, "n": n, "night_only": false})


func brazier(b: Batch, pos: Vector3) -> void:
	var xf := Transform3D(Basis.IDENTITY, pos)
	for k in 3:
		var a := TAU * k / 3.0
		b.rod("iron", pos + Vector3(cos(a) * 0.28, 0, sin(a) * 0.28), pos + Vector3(cos(a) * 0.16, 0.6, sin(a) * 0.16), 0.016, 5, IRON)
	b.lathe("iron", xf, PackedVector2Array([Vector2(0.1, 0.56), Vector2(0.26, 0.66), Vector2(0.3, 0.8), Vector2(0.27, 0.8), Vector2(0.1, 0.6), Vector2(0.0, 0.6)]), 10, IRON)
	b.ball("ember", pos + Vector3(0, 0.74, 0), Vector3(0.22, 0.06, 0.22), 8)
	b.boxes.append([Transform3D(Basis.IDENTITY, pos + Vector3(0, 0.4, 0)), Vector3(0.5, 0.8, 0.5)])
	info["fires"].append({"kind": "brazier", "pos": pos + Vector3(0, 0.85, 0), "night_only": false})


# ------------------------------------------------------------------ zbrane a zbroj

func sword(b: Batch, base: Vector3, tip: Vector3, flat_dir: Vector3 = Vector3(1, 0, 0)) -> void:
	# base = konec hlavice, tip = hrot
	var d := (tip - base).normalized()
	var ln := (tip - base).length()
	var grip_end := base + d * 0.2
	b.ball("steel", base + d * 0.02, Vector3(0.03, 0.03, 0.03), 6)
	b.rod("leather", base + d * 0.04, grip_end, 0.016, 6)
	var side := flat_dir - d * flat_dir.dot(d)
	if side.length() < 0.01:
		side = d.cross(Vector3.UP)
	side = side.normalized()
	b.beam("steel", grip_end - side * 0.11, grip_end + side * 0.11, 0.025, 0.025)
	var up := d.cross(side).normalized()
	var blade_b := Basis(side, up, d)
	b.box("steel", Transform3D(blade_b, grip_end + d * ((ln - 0.2) * 0.5)), Vector3(0.05, 0.008, ln - 0.2))


func spear(b: Batch, base: Vector3, tip: Vector3, halberd: bool = false) -> void:
	var d := (tip - base).normalized()
	var ln := (tip - base).length()
	b.rod("beam", base, base + d * (ln - 0.3), 0.02, 6, DARK)
	var head := base + d * (ln - 0.3)
	b.rod("steel", head, tip, 0.024, 6, Color.WHITE, 0.002)
	if halberd:
		var side := d.cross(Vector3(0.3, 0.2, 1.0)).normalized()
		var up := d.cross(side).normalized()
		var basis := Basis(side, up, d)
		b.box("steel", Transform3D(basis, head + d * 0.02 + side * 0.09), Vector3(0.16, 0.008, 0.22))
		b.box("steel", Transform3D(basis, head + d * 0.02 - side * 0.07), Vector3(0.1, 0.008, 0.04))


func shield(b: Batch, t: Transform3D, col: Color, col2: Color) -> void:
	# pavezka na zdi: celo miri ve smeru +Z
	_b(b, "paint", t, Vector3(0, 0.18, 0), Vector3(0.56, 0.44, 0.04), col)
	b.tri_slab("paint", t * Vector3(-0.28, -0.04, 0.02), t * Vector3(0.28, -0.04, 0.02), t * Vector3(0, -0.42, 0.02), 0.04, col)
	_b(b, "paint", t, Vector3(0, 0.18, 0.022), Vector3(0.16, 0.44, 0.012), col2)
	_b(b, "iron", t, Vector3(0, 0.39, 0.012), Vector3(0.58, 0.03, 0.05), IRON)
	b.ball("steel", t * Vector3(0, 0.12, 0.04), Vector3(0.06, 0.06, 0.03), 8)


func weapon_rack(b: Batch, t: Transform3D, w: float, items: int, halberds: bool = true) -> void:
	for sx: float in [-1.0, 1.0]:
		_b(b, "beam", t, Vector3(sx * w * 0.5, 0.95, 0), Vector3(0.08, 1.9, 0.08), DARK, 1)
		_b(b, "beam", t, Vector3(sx * w * 0.5, 0.04, -0.2), Vector3(0.08, 0.08, 0.5), DARK, 2)
	_b(b, "beam", t, Vector3(0, 1.7, -0.05), Vector3(w, 0.07, 0.1), DARK, 0)
	_b(b, "beam", t, Vector3(0, 0.25, -0.25), Vector3(w, 0.07, 0.1), DARK, 0)
	for k in items:
		var x := -w * 0.5 + w * (k + 0.5) / items
		var ln := 2.25 + rng.randf_range(-0.1, 0.15)
		spear(b, t * Vector3(x, 0.02, -0.3), t * Vector3(x + rng.randf_range(-0.03, 0.03), ln, -0.02), halberds and k % 2 == 0)
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, 0.95, -0.12)), Vector3(w, 1.9, 0.5)])


func sword_rack(b: Batch, t: Transform3D, n: int) -> void:
	# vodorovna lista na zdi s mecemi hrotem dolu
	var w := 0.22 * n + 0.2
	_b(b, "beam", t, Vector3(0, 0, 0.04), Vector3(w, 0.1, 0.08), DARK, 0)
	for k in n:
		var x := -w * 0.5 + 0.21 + 0.22 * k
		b.rod("iron", t * Vector3(x - 0.05, 0.0, 0.08), t * Vector3(x - 0.05, 0.0, 0.16), 0.008, 4, IRON)
		b.rod("iron", t * Vector3(x + 0.05, 0.0, 0.08), t * Vector3(x + 0.05, 0.0, 0.16), 0.008, 4, IRON)
		sword(b, t * Vector3(x, 0.22, 0.12), t * Vector3(x, -0.82 - rng.randf_range(0.0, 0.12), 0.12), t.basis.x)


func armor_stand(b: Batch, pos: Vector3, yaw: float = 0.0) -> void:
	var t := at(pos, yaw)
	_b(b, "beam", t, Vector3(0, 0.75, 0), Vector3(0.08, 1.5, 0.08), DARK, 1)
	_b(b, "beam", t, Vector3(0, 0.04, 0), Vector3(0.6, 0.07, 0.08), DARK, 0)
	_b(b, "beam", t, Vector3(0, 0.04, 0), Vector3(0.08, 0.07, 0.6), DARK, 2)
	_b(b, "beam", t, Vector3(0, 1.32, 0), Vector3(0.62, 0.06, 0.06), DARK, 0)
	# kyrys a prilba (klobouk)
	b.lathe("steel", t * Transform3D(Basis.from_scale(Vector3(1.0, 1.0, 0.72)), Vector3(0, 0.82, 0)),
			PackedVector2Array([Vector2(0.17, 0.0), Vector2(0.22, 0.12), Vector2(0.25, 0.34), Vector2(0.22, 0.5), Vector2(0.11, 0.56)]), 12)
	b.lathe("steel", t * Transform3D(Basis.IDENTITY, Vector3(0, 1.5, 0)),
			PackedVector2Array([Vector2(0.24, 0.0), Vector2(0.13, 0.03), Vector2(0.125, 0.1), Vector2(0.09, 0.17), Vector2(0.0, 0.2)]), 12)
	b.boxes.append([Transform3D(Basis.IDENTITY, pos + Vector3(0, 0.85, 0)), Vector3(0.5, 1.7, 0.4)])


func bow(b: Batch, t: Transform3D, strung: bool = true) -> void:
	# luk stoji svisle, bricho miri do +Z
	var pts := PackedVector3Array()
	for k in 13:
		var f := float(k) / 12.0 * 2.0 - 1.0
		pts.append(t * Vector3(0, f * 0.82, -0.2 * (1.0 - f * f)))
	b.tube("beam", pts, 0.018, 6, _col(Color(0.9, 0.8, 0.62)), 0.018)
	if strung:
		b.rod("fabric", t * Vector3(0, -0.82, 0), t * Vector3(0, 0.82, 0), 0.003, 3, Color(0.9, 0.88, 0.8))


func arrow(b: Batch, tail: Vector3, tip: Vector3) -> void:
	var d := (tip - tail).normalized()
	b.rod("beam", tail, tip - d * 0.05, 0.006, 4, Color(0.92, 0.84, 0.66))
	b.rod("steel", tip - d * 0.05, tip, 0.009, 4, Color.WHITE, 0.001)
	var side := d.cross(Vector3.UP if absf(d.y) < 0.9 else Vector3(1, 0, 0)).normalized()
	var up := d.cross(side).normalized()
	for ax: Vector3 in [side, up]:
		b.box("paint", Transform3D(Basis(ax, d.cross(ax).normalized(), d), tail + d * 0.07), Vector3(0.05, 0.002, 0.1), Color(0.9, 0.9, 0.86))


func quiver(b: Batch, pos: Vector3, arrows: int = 8) -> void:
	b.lathe("leather", Transform3D(Basis.IDENTITY, pos), PackedVector2Array([Vector2(0.06, 0.0), Vector2(0.075, 0.6)]), 8, Color(1, 1, 1), true)
	for k in arrows:
		var a := TAU * k / arrows
		var o := Vector3(cos(a), 0, sin(a)) * 0.035
		arrow(b, pos + o * 1.6 + Vector3(0, 0.82 + rng.randf_range(-0.03, 0.03), 0), pos + o + Vector3(0, 0.08, 0))


func straw_target(b: Batch, t: Transform3D, radius: float = 0.6) -> void:
	# kulaty slameny terc na trojnozce, celo miri do +Z
	var c := Vector3(0, 1.15, 0)
	var basis := t.basis * Basis(Vector3(1, 0, 0), PI * 0.5)
	b.lathe("straw", Transform3D(basis, t * (c + Vector3(0, 0, -0.14))), PackedVector2Array([Vector2(radius, 0.0), Vector2(radius, 0.26)]), 20, Color(0.95, 0.92, 0.8))
	b.lathe("straw", Transform3D(basis, t * (c + Vector3(0, 0, -0.14))), PackedVector2Array([Vector2(0.0, 0.0), Vector2(radius, 0.0)]), 20, Color(0.8, 0.76, 0.66))
	# celo s kruhy: ctverec s texturou terce
	var s := b._surface("target")
	var base := s.v.size()
	var seg := 24
	s.v.append(t * (c + Vector3(0, 0, 0.125)))
	s.n.append(t.basis.z.normalized())
	s.uv.append(Vector2(0.5, 0.5))
	s.c.append(Color.WHITE)
	for k in seg + 1:
		var a := TAU * k / seg
		s.v.append(t * (c + Vector3(cos(a) * radius, sin(a) * radius, 0.125)))
		s.n.append(t.basis.z.normalized())
		s.uv.append(Vector2(0.5 + cos(a) * 0.47, 0.5 - sin(a) * 0.47))
		s.c.append(Color.WHITE)
	for k in seg:
		b._tri_idx(s, base, base + 1 + k, base + 2 + k)
	# trojnozka
	b.beam("beam", t * Vector3(-0.5, 0, 0.25), t * Vector3(-0.2, 1.75, -0.2), 0.07, 0.07, DARK)
	b.beam("beam", t * Vector3(0.5, 0, 0.25), t * Vector3(0.2, 1.75, -0.2), 0.07, 0.07, DARK)
	b.beam("beam", t * Vector3(0, 0, -1.0), t * Vector3(0, 1.75, -0.22), 0.07, 0.07, DARK)
	b.beam("beam", t * Vector3(-0.42, 0.52, 0.14), t * Vector3(0.42, 0.52, 0.14), 0.06, 0.06, DARK)
	info["targets"].append({"center": t * (c + Vector3(0, 0, 0.125)), "normal": t.basis.z.normalized(), "radius": radius})
	b.boxes.append([t * Transform3D(Basis.IDENTITY, c), Vector3(radius * 2.0, radius * 2.0, 0.26)])


# ------------------------------------------------------------------ dvur

func cart(b: Batch, t: Transform3D, loaded: bool = true) -> void:
	_b(b, "planks", t, Vector3(0, 0.75, 0), Vector3(1.3, 0.06, 2.4), _col(OLD), 2)
	for sx: float in [-1.0, 1.0]:
		_b(b, "planks", t, Vector3(sx * 0.66, 1.0, 0), Vector3(0.04, 0.5, 2.4), _col(OLD), 2)
		wheel(b, t * Transform3D(Basis(Vector3(0, 0, 1), PI * 0.5), Vector3(sx * 0.82, 0.55, 0.1)), 0.55)
		b.beam("beam", t * Vector3(sx * 0.45, 0.72, -1.2), t * Vector3(sx * 0.3, 0.55, -3.1), 0.07, 0.08, DARK)
	_b(b, "planks", t, Vector3(0, 1.0, 1.2), Vector3(1.3, 0.5, 0.04), _col(OLD), 0)
	b.rod("beam", t * Vector3(-0.85, 0.55, 0.1), t * Vector3(0.85, 0.55, 0.1), 0.045, 6, DARK)
	b.beam("beam", t * Vector3(0, 0.0, -1.0), t * Vector3(0, 0.72, -1.05), 0.08, 0.08, DARK)
	if loaded:
		b.ball("straw", t * Vector3(0, 1.15, 0.1), Vector3(0.62, 0.5, 1.15), 12, Color(0.95, 0.92, 0.8))
	b.boxes.append([t * Transform3D(Basis.IDENTITY, Vector3(0, 0.7, 0)), Vector3(1.7, 1.4, 2.5)])


func wheel(b: Batch, xf: Transform3D, r: float) -> void:
	# osa kola = mistni Y
	var ring := PackedVector3Array()
	for k in 21:
		var a := TAU * k / 20.0
		ring.append(xf * Vector3(cos(a) * r, 0, sin(a) * r))
	b.tube("beam", ring, 0.045, 6, DARK)
	b.cyl("beam", xf.origin - xf.basis.y.normalized() * 0.07, 0.09, 0.09, 0.14, 8, DARK, true, xf.basis.orthonormalized())
	for k in 8:
		var a2 := TAU * k / 8.0
		b.rod("beam", xf.origin, xf * Vector3(cos(a2) * r, 0, sin(a2) * r), 0.022, 5, _col(WOOD))


func well(b: Batch, pos: Vector3) -> void:
	var seg := 12
	for k in seg:
		var a := TAU * (k + 0.5) / seg
		var c := pos + Vector3(cos(a) * 0.95, 0.45, sin(a) * 0.95)
		b.box("stone", Transform3D(Basis(Vector3.UP, -a + PI * 0.5), c), Vector3(0.56, 0.9, 0.36), Color(0.95, 0.95, 0.93), false, -1, 0, false)
		b.box("flag", Transform3D(Basis(Vector3.UP, -a + PI * 0.5), c + Vector3(0, 0.48, 0)), Vector3(0.6, 0.07, 0.44), Color(0.85, 0.85, 0.83))
	b.lathe("water", Transform3D(Basis.IDENTITY, pos), PackedVector2Array([Vector2(0.0, 0.2), Vector2(0.8, 0.2)]), 12)
	b.lathe("soot", Transform3D(Basis.IDENTITY, pos), PackedVector2Array([Vector2(0.78, 0.9), Vector2(0.78, 0.2)]), 12)
	for sx: float in [-1.0, 1.0]:
		b.beam("beam", pos + Vector3(sx * 1.15, 0, 0), pos + Vector3(sx * 1.15, 2.5, 0), 0.16, 0.16, DARK)
		b.beam("beam", pos + Vector3(sx * 1.15, 1.9, 0), pos + Vector3(sx * 0.6, 2.45, 0), 0.08, 0.08, DARK)
	b.beam("beam", pos + Vector3(-1.3, 2.5, 0), pos + Vector3(1.3, 2.5, 0), 0.14, 0.14, DARK)
	b.slab("shingles", pos + Vector3(-1.5, 2.55, -0.9), pos + Vector3(1.5, 2.55, -0.9), pos + Vector3(1.5, 3.2, 0), pos + Vector3(-1.5, 3.2, 0), 0.06, Color(0.85, 0.82, 0.78), false, "planks")
	b.slab("shingles", pos + Vector3(-1.5, 2.55, 0.9), pos + Vector3(1.5, 2.55, 0.9), pos + Vector3(1.5, 3.2, 0), pos + Vector3(-1.5, 3.2, 0), 0.06, Color(0.85, 0.82, 0.78), false, "planks")
	b.rod("beam", pos + Vector3(-1.1, 1.55, 0), pos + Vector3(1.1, 1.55, 0), 0.08, 8, DARK)
	b.rod("iron", pos + Vector3(1.1, 1.55, 0), pos + Vector3(1.45, 1.55, 0), 0.015, 5, IRON)
	b.rod("iron", pos + Vector3(1.45, 1.55, 0), pos + Vector3(1.45, 1.3, 0.1), 0.015, 5, IRON)
	b.rod("fabric", pos + Vector3(0.1, 1.5, 0), pos + Vector3(0.1, 0.95, 0), 0.012, 4, Color(0.7, 0.62, 0.45))
	bucket(b, pos + Vector3(0.1, 0.62, 0))
	b.boxes.append([Transform3D(Basis.IDENTITY, pos + Vector3(0, 0.5, 0)), Vector3(2.2, 1.0, 2.2)])
	b.boxes.append([Transform3D(Basis.IDENTITY, pos + Vector3(0, 1.3, 0)), Vector3(2.5, 2.6, 0.2)])


func ladder(b: Batch, base: Vector3, top: Vector3, side: Vector3) -> void:
	var s := side.normalized() * 0.24
	b.beam("beam", base - s, top - s, 0.06, 0.07, _col(OLD))
	b.beam("beam", base + s, top + s, 0.06, 0.07, _col(OLD))
	var n := int((top - base).length() / 0.3)
	for k in range(1, n):
		var p := base.lerp(top, float(k) / n)
		b.rod("beam", p - s, p + s, 0.02, 5, _col(WOOD))


func anvil(b: Batch, pos: Vector3, yaw: float = 0.0) -> void:
	var t := at(pos, yaw)
	b.cyl("bark", pos, 0.32, 0.29, 0.55, 10, Color(0.9, 0.86, 0.8))
	b.lathe("planks", Transform3D(Basis.IDENTITY, pos), PackedVector2Array([Vector2(0.0, 0.55), Vector2(0.29, 0.55)]), 10, Color(0.8, 0.72, 0.6))
	_b(b, "iron", t, Vector3(0, 0.6, 0), Vector3(0.3, 0.1, 0.2), IRON)
	_b(b, "iron", t, Vector3(0, 0.71, 0), Vector3(0.16, 0.13, 0.12), IRON)
	_b(b, "steel", t, Vector3(0.02, 0.83, 0), Vector3(0.46, 0.11, 0.17), Color(0.5, 0.5, 0.52))
	b.cyl("steel", t * Vector3(-0.21, 0.83, 0), 0.055, 0.008, 0.28, 8, Color(0.5, 0.5, 0.52), true, t.basis * Basis(Vector3(0, 0, 1), PI * 0.5))
	b.boxes.append([Transform3D(Basis.IDENTITY, pos + Vector3(0, 0.45, 0)), Vector3(0.6, 0.9, 0.6)])


func hammer(b: Batch, t: Transform3D) -> void:
	b.rod("beam", t * Vector3(-0.16, 0.02, 0), t * Vector3(0.16, 0.02, 0), 0.014, 5, WOOD)
	_b(b, "iron", t, Vector3(0.16, 0.02, 0), Vector3(0.05, 0.05, 0.12), IRON)


func tongs(b: Batch, t: Transform3D) -> void:
	b.rod("iron", t * Vector3(-0.3, 0.01, 0.02), t * Vector3(0.2, 0.01, -0.02), 0.008, 4, IRON)
	b.rod("iron", t * Vector3(-0.3, 0.01, -0.02), t * Vector3(0.2, 0.01, 0.02), 0.008, 4, IRON)


func grindstone(b: Batch, pos: Vector3, yaw: float = 0.0) -> void:
	var t := at(pos, yaw)
	for sx: float in [-1.0, 1.0]:
		b.beam("beam", t * Vector3(sx * 0.22, 0, -0.35), t * Vector3(sx * 0.22, 0.75, 0), 0.07, 0.07, DARK)
		b.beam("beam", t * Vector3(sx * 0.22, 0, 0.35), t * Vector3(sx * 0.22, 0.75, 0), 0.07, 0.07, DARK)
	b.cyl("ashlar", t * Vector3(-0.07, 0.75, 0), 0.36, 0.36, 0.14, 16, Color(0.85, 0.85, 0.85), true, t.basis * Basis(Vector3(0, 0, 1), -PI * 0.5))
	b.rod("iron", t * Vector3(-0.3, 0.75, 0), t * Vector3(0.42, 0.75, 0), 0.015, 5, IRON)
	b.rod("iron", t * Vector3(0.42, 0.75, 0), t * Vector3(0.42, 0.6, 0.12), 0.015, 5, IRON)
	b.boxes.append([Transform3D(Basis.IDENTITY, pos + Vector3(0, 0.5, 0)), Vector3(0.7, 1.0, 0.8)])


func banner_card(b: Batch, top_left: Vector3, right: Vector3, down: Vector3) -> void:
	var n := right.cross(down).normalized()
	var p := [top_left, top_left + right, top_left + right + down, top_left + down]
	b.card("banner", p, [n, n, n, n], [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)],
			[Color(1, 1, 1, 0), Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 1)])
