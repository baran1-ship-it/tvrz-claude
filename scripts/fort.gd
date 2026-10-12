extends RefCounted
## Opevneni: hradby s ochozem, brana, vez, schodiste na hradbu, most.
## Souradnice: X vychod, Z jih, Y nahoru. Nadvori je na Y = 0.

const Batch := preload("res://scripts/mesh_batch.gd")

const IX := 17.0      # polovina nadvori v ose X (vnitrni lic hradby)
const IZ := 14.0
const OX := 18.8      # vnejsi lic
const OZ := 15.8
const WALK := 6.5     # vyska ochozu
const BASE := -4.5    # zaklad hradeb v prikopu
const STONE := Color(1, 1, 1)

var M: Dictionary
var info: Dictionary


func _init(p_mats: Dictionary, p_info: Dictionary) -> void:
	M = p_mats
	info = p_info


# ------------------------------------------------------------------ pomocne

## Zed podel X s otvory [xa, xb, ya, yb].
static func wall_x(b: Batch, key: String, x0: float, x1: float, z0: float, z1: float, y0: float, y1: float,
		holes: Array = [], col: Color = Color.WHITE, collide: bool = true, tinted: bool = true) -> void:
	var hs := holes.duplicate()
	hs.sort_custom(func(p, q): return p[0] < q[0])
	var cur := x0
	for h: Array in hs:
		if h[0] > cur + 0.001:
			b.bb(key, Vector3(cur, y0, z0), Vector3(h[0], y1, z1), col, collide, -1, 0, tinted)
		if h[2] > y0 + 0.001:
			b.bb(key, Vector3(h[0], y0, z0), Vector3(h[1], h[2], z1), col, collide, -1, 0, tinted)
		if h[3] < y1 - 0.001:
			b.bb(key, Vector3(h[0], h[3], z0), Vector3(h[1], y1, z1), col, collide, -1, 0, tinted)
		cur = h[1]
	if cur < x1 - 0.001:
		b.bb(key, Vector3(cur, y0, z0), Vector3(x1, y1, z1), col, collide, -1, 0, tinted)


## Zed podel Z s otvory [za, zb, ya, yb].
static func wall_z(b: Batch, key: String, z0: float, z1: float, x0: float, x1: float, y0: float, y1: float,
		holes: Array = [], col: Color = Color.WHITE, collide: bool = true, tinted: bool = true) -> void:
	var hs := holes.duplicate()
	hs.sort_custom(func(p, q): return p[0] < q[0])
	var cur := z0
	for h: Array in hs:
		if h[0] > cur + 0.001:
			b.bb(key, Vector3(x0, y0, cur), Vector3(x1, y1, h[0]), col, collide, -1, 0, tinted)
		if h[2] > y0 + 0.001:
			b.bb(key, Vector3(x0, y0, h[0]), Vector3(x1, h[2], h[1]), col, collide, -1, 0, tinted)
		if h[3] < y1 - 0.001:
			b.bb(key, Vector3(x0, h[3], h[0]), Vector3(x1, y1, h[1]), col, collide, -1, 0, tinted)
		cur = h[1]
	if cur < z1 - 0.001:
		b.bb(key, Vector3(x0, y0, cur), Vector3(x1, y1, z1), col, collide, -1, 0, tinted)


## Cimburi: nizka zidka a zuby. a, e = konce osy cimburi ve vysce ochozu.
func parapet(b: Batch, a: Vector3, e: Vector3, thick: float = 0.5) -> void:
	var ln := (e - a).length()
	var d := (e - a) / ln
	var side := Vector3.UP.cross(d).normalized()
	var basis := Basis(side, Vector3.UP, d)
	b.box("stone", Transform3D(basis, (a + e) * 0.5 + Vector3(0, 0.45, 0)), Vector3(thick, 0.9, ln), STONE, true, -1, 0, true)
	var mw := 1.25
	var gap := 0.8
	var n := int(floor((ln + gap) / (mw + gap)))
	if n < 1:
		return
	var margin := (ln - (n * mw + (n - 1) * gap)) * 0.5
	for k in n:
		var s0 := margin + k * (mw + gap)
		var w := mw
		if k == 0:
			s0 = 0.0
			w = mw + margin
		elif k == n - 1:
			w = ln - s0
		var c := a + d * (s0 + w * 0.5) + Vector3(0, 1.35, 0)
		b.box("stone", Transform3D(basis, c), Vector3(thick, 0.9, w), STONE, true, -1, 0, true)
		b.box("flag", Transform3D(basis, c + Vector3(0, 0.48, 0)), Vector3(thick + 0.08, 0.06, w + 0.06), Color(0.9, 0.9, 0.9))


## Dreveny ochoz vylozeny dovnitr nadvori. a, e = konce vnitrni hrany hradby ve vysce ochozu, inward = smer do nadvori.
func gallery(b: Batch, a: Vector3, e: Vector3, inward: Vector3, width: float = 0.8, rail: bool = true) -> void:
	var ln := (e - a).length()
	var d := (e - a) / ln
	var basis := Basis(inward, Vector3.UP, d)
	var wood := Color(0.78, 0.74, 0.7)
	# prkna
	b.box("planks", Transform3D(basis, (a + e) * 0.5 + inward * (width * 0.5) + Vector3(0, -0.04, 0)),
			Vector3(width, 0.08, ln), wood, true, 0)
	var n := maxi(2, int(round(ln / 1.9)) + 1)
	for k in n:
		var p := a + d * (0.12 + (ln - 0.24) * float(k) / (n - 1))
		# konzola a vzpera
		b.beam("beam", p + Vector3(0, -0.2, 0) - inward * 0.25, p + Vector3(0, -0.2, 0) + inward * (width + 0.05), 0.16, 0.2, wood)
		b.beam("beam", p + Vector3(0, -1.1, 0) + inward * 0.02, p + Vector3(0, -0.3, 0) + inward * (width - 0.05), 0.12, 0.12, wood)
		if rail:
			b.beam("beam", p + inward * (width - 0.06) + Vector3(0, -0.08, 0), p + inward * (width - 0.06) + Vector3(0, 1.08, 0), 0.1, 0.1, wood)
	if rail:
		var r0 := a + inward * (width - 0.06)
		var r1 := e + inward * (width - 0.06)
		b.beam("beam", r0 + Vector3(0, 1.05, 0), r1 + Vector3(0, 1.05, 0), 0.09, 0.1, wood)
		b.beam("beam", r0 + Vector3(0, 0.55, 0), r1 + Vector3(0, 0.55, 0), 0.06, 0.08, wood)
		b.boxes.append([Transform3D(basis, (r0 + r1) * 0.5 + Vector3(0, 0.55, 0)), Vector3(0.12, 1.1, ln)])


## Valena klenba pruchodu podel osy Z. Vyplni rohy nad obloukem a udela podhled.
func vault_z(b: Batch, cx: float, z0: float, z1: float, half_w: float, spring_y: float, key: String = "ashlar") -> void:
	var n := 12
	var top := spring_y + half_w
	var col := Color(0.86, 0.84, 0.8)
	for i in n:
		var a0 := PI - PI * float(i) / n
		var a1 := PI - PI * float(i + 1) / n
		var p0 := Vector2(cx + half_w * cos(a0), spring_y + half_w * sin(a0))
		var p1 := Vector2(cx + half_w * cos(a1), spring_y + half_w * sin(a1))
		# cela
		b.quad(key, Vector3(p0.x, p0.y, z0), Vector3(p1.x, p1.y, z0), Vector3(p1.x, top, z0), Vector3(p0.x, top, z0), Vector3(0, 0, -1), col)
		b.quad(key, Vector3(p0.x, p0.y, z1), Vector3(p1.x, p1.y, z1), Vector3(p1.x, top, z1), Vector3(p0.x, top, z1), Vector3(0, 0, 1), col)
		# podhled
		var am := (a0 + a1) * 0.5
		var nrm := Vector3(-cos(am), -sin(am), 0)
		var steps := maxi(1, int((z1 - z0) / 2.0))
		for s in steps:
			var za := z0 + (z1 - z0) * float(s) / steps
			var zb := z0 + (z1 - z0) * float(s + 1) / steps
			var shade := 0.62 + 0.3 * absf(float(s) + 0.5 - steps * 0.5) / (steps * 0.5)
			var c2 := Color(col.r * shade, col.g * shade, col.b * shade)
			b.quad(key, Vector3(p0.x, p0.y, za), Vector3(p1.x, p1.y, za), Vector3(p1.x, p1.y, zb), Vector3(p0.x, p0.y, zb), nrm, c2)


## Jehlanova strecha se sindelem.
func pyramid_roof(b: Batch, x0: float, x1: float, z0: float, z1: float, y: float, apex: Vector3) -> void:
	var c := [Vector3(x0, y, z0), Vector3(x1, y, z0), Vector3(x1, y, z1), Vector3(x0, y, z1)]
	for k in 4:
		b.tri_slab("shingles", c[k], c[(k + 1) % 4], apex, 0.14)
	# podbiti z prken
	b.bb("planks", Vector3(x0 + 0.1, y - 0.06, z0 + 0.1), Vector3(x1 - 0.1, y, z1 - 0.1), Color(0.7, 0.66, 0.6))
	b.cyl("iron", apex - Vector3(0, 0.1, 0), 0.07, 0.02, 0.9, 6)
	b.ball("iron", apex + Vector3(0, 0.25, 0), Vector3(0.13, 0.13, 0.13), 8)


# ------------------------------------------------------------------ stavba

func build(parent: Node3D) -> void:
	_walls(parent)
	_gatehouse(parent)
	_tower(parent)
	_wall_stair(parent)


func _walls(parent: Node3D) -> void:
	var b := Batch.new(M, 11)
	# hradby (cast u palace stavi palace.gd)
	b.bb("stone", Vector3(-OX, BASE, IZ), Vector3(-3.5, WALK, OZ), STONE, true, -1, 0, true)
	b.bb("stone", Vector3(3.5, BASE, IZ), Vector3(OX, WALK, OZ), STONE, true, -1, 0, true)
	b.bb("stone", Vector3(-OX, BASE, -8.8), Vector3(-IX, WALK, IZ), STONE, true, -1, 0, true)
	b.bb("stone", Vector3(IX, BASE, -7.0), Vector3(OX, WALK, IZ), STONE, true, -1, 0, true)
	b.bb("stone", Vector3(-11.8, BASE, -OZ), Vector3(-3.0, WALK, -IZ), STONE, true, -1, 0, true)
	# sikmy sokl z vnejsi strany
	_plinth(b)
	# cimburi
	parapet(b, Vector3(-OX, WALK, OZ - 0.25), Vector3(-3.5, WALK, OZ - 0.25))
	parapet(b, Vector3(3.5, WALK, OZ - 0.25), Vector3(OX, WALK, OZ - 0.25))
	parapet(b, Vector3(-OX + 0.25, WALK, -8.8), Vector3(-OX + 0.25, WALK, OZ - 0.5))
	parapet(b, Vector3(OX - 0.25, WALK, -7.0), Vector3(OX - 0.25, WALK, OZ - 0.5))
	parapet(b, Vector3(-11.8, WALK, -OZ + 0.25), Vector3(-3.0, WALK, -OZ + 0.25))
	# dlazba na korune hradby
	var fl := Color(0.82, 0.8, 0.76)
	b.bb("flag", Vector3(-OX + 0.5, WALK, IZ), Vector3(-3.5, WALK + 0.03, OZ - 0.5), fl)
	b.bb("flag", Vector3(3.5, WALK, IZ), Vector3(OX - 0.5, WALK + 0.03, OZ - 0.5), fl)
	b.bb("flag", Vector3(-OX + 0.5, WALK, -8.8), Vector3(-IX, WALK + 0.03, IZ), fl)
	b.bb("flag", Vector3(IX, WALK, -7.0), Vector3(OX - 0.5, WALK + 0.03, IZ), fl)
	b.bb("flag", Vector3(-11.8, WALK, -OZ + 0.5), Vector3(-3.0, WALK + 0.03, -IZ), fl)
	b.commit(parent, "Hradby")

	var g := Batch.new(M, 12)
	gallery(g, Vector3(-IX, WALK, IZ), Vector3(-3.5, WALK, IZ), Vector3(0, 0, -1))
	gallery(g, Vector3(4.7, WALK, IZ), Vector3(IX - 0.9, WALK, IZ), Vector3(0, 0, -1))
	gallery(g, Vector3(-IX, WALK, -8.8), Vector3(-IX, WALK, IZ - 0.9), Vector3(1, 0, 0))
	gallery(g, Vector3(IX, WALK, -7.0), Vector3(IX, WALK, IZ - 0.9), Vector3(-1, 0, 0))
	gallery(g, Vector3(-11.8, WALK, -IZ), Vector3(-3.0, WALK, -IZ), Vector3(0, 0, 1))
	# rohove kusy ochozu
	var wood := Color(0.78, 0.74, 0.7)
	g.bb("planks", Vector3(-IX, WALK - 0.08, IZ - 0.8), Vector3(-IX + 0.8, WALK, IZ), wood, true, 0)
	g.bb("planks", Vector3(IX - 0.8, WALK - 0.08, IZ - 0.8), Vector3(IX, WALK, IZ), wood, true, 0)
	# zabradli na slepem konci severniho ochozu u palace
	g.beam("beam", Vector3(-3.05, WALK + 1.05, -IZ + 0.8), Vector3(-3.05, WALK + 1.05, -OZ + 0.5), 0.09, 0.1, wood, true)
	g.beam("beam", Vector3(-3.05, WALK + 0.55, -IZ + 0.8), Vector3(-3.05, WALK + 0.55, -OZ + 0.5), 0.06, 0.08, wood, true)
	g.commit(parent, "Ochozy")


func _plinth(b: Batch) -> void:
	# sikma pata hradeb: desky opřené o vnejsi lic
	var y0 := BASE
	var y1 := -1.2
	var out := 0.9
	var col := Color(0.86, 0.85, 0.82)
	var segs := [
		[Vector3(-OX, 0, OZ), Vector3(-4.2, 0, OZ), Vector3(0, 0, 1)],
		[Vector3(4.2, 0, OZ), Vector3(OX, 0, OZ), Vector3(0, 0, 1)],
		[Vector3(-OX, 0, -8.0), Vector3(-OX, 0, OZ), Vector3(-1, 0, 0)],
		[Vector3(OX, 0, -OZ), Vector3(OX, 0, OZ), Vector3(1, 0, 0)],
		[Vector3(-11.0, 0, -OZ), Vector3(OX, 0, -OZ), Vector3(0, 0, -1)],
	]
	for s: Array in segs:
		var a: Vector3 = s[0]
		var e: Vector3 = s[1]
		var o: Vector3 = s[2]
		var n := (o * (y1 - y0) + Vector3(0, out, 0)).normalized()
		var nseg := maxi(1, int((e - a).length() / 2.0))
		for k in nseg:
			var p := a.lerp(e, float(k) / nseg)
			var q := a.lerp(e, float(k + 1) / nseg)
			var pa := Vector3(p.x, y1, p.z)
			var qa := Vector3(q.x, y1, q.z)
			var pb := Vector3(p.x, y0, p.z) + o * out
			var qb := Vector3(q.x, y0, q.z) + o * out
			b.quad4("stone", pa, qa, qb, pb, n, b.tint(pa, col), b.tint(qa, col), b.tint(qb, col), b.tint(pb, col))


func _gatehouse(parent: Node3D) -> void:
	var b := Batch.new(M, 21)
	var gx := 3.5
	var z0 := 9.5
	var z1 := 17.0
	var pw := 1.6        # polovina sirky prujezdu
	var top := 10.6
	# piliry a zdivo nad prujezdem
	b.bb("stone", Vector3(-gx, BASE, z0), Vector3(-pw, WALK, z1), STONE, true, -1, 0, true)
	b.bb("stone", Vector3(pw, BASE, z0), Vector3(gx, WALK, z1), STONE, true, -1, 0, true)
	b.bb("stone", Vector3(-pw, 3.9, z0), Vector3(pw, WALK, z1), STONE, true, -1, Batch.NY, true)
	vault_z(b, 0.0, z0, z1, pw, 2.3)
	# dlazba prujezdu a vypln pod ni
	b.bb("cobble", Vector3(-pw, -0.25, z0 - 0.5), Vector3(pw, 0.0, z1), Color(0.8, 0.8, 0.8), true)
	b.bb("stone", Vector3(-pw, BASE, IZ), Vector3(pw, -0.25, z1), STONE, false, -1, 0, true)
	# patro: strazni svetnice
	var t := 0.8
	wall_x(b, "stone", -gx, gx, z1 - t, z1, WALK, top, [[-2.3, -1.5, 7.5, 8.9], [1.5, 2.3, 7.5, 8.9]])
	wall_x(b, "stone", -gx, gx, z0, z0 + t, WALK, top, [[-0.5, 0.5, 7.5, 8.8]])
	wall_z(b, "stone", z0 + t, z1 - t, -gx, -gx + t, WALK, top, [[14.1, 15.2, WALK, 8.6]])
	wall_z(b, "stone", z0 + t, z1 - t, gx - t, gx, WALK, top, [[14.1, 15.2, WALK, 8.6]])
	b.bb("planks", Vector3(-gx + t, WALK, z0 + t), Vector3(gx - t, WALK + 0.04, z1 - t), Color(0.8, 0.76, 0.7), false, 0)
	# strop
	var wood := Color(0.7, 0.66, 0.6)
	for k in 5:
		var x := -2.6 + 1.3 * k
		b.beam("beam", Vector3(x, top - 0.14, z0 + 0.4), Vector3(x, top - 0.14, z1 - 0.4), 0.2, 0.26, wood)
	pyramid_roof(b, -gx - 0.5, gx + 0.5, z0 - 0.5, z1 + 0.5, top, Vector3(0, top + 4.8, (z0 + z1) * 0.5))
	# vrata: dve kridla otevrena dovnitr podel sten prujezdu
	for sx: float in [-1.0, 1.0]:
		var gx0 := sx * (pw - 0.07)
		b.bb("planks", Vector3(gx0 - 0.06, 0.05, 14.5), Vector3(gx0 + 0.06, 3.5, 16.1), Color(0.62, 0.56, 0.5), true, 1)
		for hy: float in [0.6, 1.8, 3.0]:
			b.bb("iron", Vector3(gx0 - 0.08, hy - 0.05, 14.55), Vector3(gx0 + 0.08, hy + 0.05, 16.05))
	# padaci mriz vytazena nahore
	for k in 9:
		var x2 := -1.4 + 0.35 * k
		b.rod("iron", Vector3(x2, 3.05, 16.55), Vector3(x2, 4.4, 16.55), 0.035, 6)
		b.cyl("iron", Vector3(x2, 2.85, 16.55), 0.0, 0.035, 0.2, 6)
	for hy2: float in [3.3, 3.75]:
		b.rod("iron", Vector3(-1.45, hy2, 16.55), Vector3(1.45, hy2, 16.55), 0.03, 6)
	info["rooms"].append({"name": "branka", "aabb": AABB(Vector3(-gx + t, WALK, z0 + t), Vector3(2 * (gx - t), top - WALK, z1 - z0 - 2 * t)), "ambient": Color(0.34, 0.33, 0.32)})
	info["rooms"].append({"name": "prujezd", "aabb": AABB(Vector3(-pw, 0, z0), Vector3(2 * pw, 3.9, z1 - z0)), "ambient": Color(0.30, 0.31, 0.33)})
	b.commit(parent, "Brana")


func _tower(parent: Node3D) -> void:
	var b := Batch.new(M, 31)
	var x0 := -19.8
	var x1 := -11.8
	var z0 := -16.8
	var z1 := -8.8
	var t := 1.5
	var top := 17.0
	var ix0 := x0 + t
	var ix1 := x1 - t
	var iz0 := z0 + t
	var iz1 := z1 - t
	var wy0 := 13.95
	var wy1 := 15.85
	# ctyri zdi s otvory
	wall_x(b, "stone", x0, x1, iz1, z1, BASE, top, [
		[-17.9, -16.7, WALK, 8.6],
		[-17.95, -16.45, wy0, wy1], [-15.15, -13.65, wy0, wy1]])
	wall_x(b, "stone", x0, x1, z0, iz0, BASE, top, [
		[-15.95, -15.65, 8.0, 9.3],
		[-17.95, -16.45, wy0, wy1], [-15.15, -13.65, wy0, wy1]])
	wall_z(b, "stone", iz0, iz1, ix1, x1, BASE, top, [
		[-13.4, -12.2, 0.0, 2.1],
		[-14.9, -13.7, WALK, 8.6],
		[-14.75, -13.25, wy0, wy1], [-12.35, -10.85, wy0, wy1]])
	wall_z(b, "stone", iz0, iz1, x0, ix0, BASE, top, [
		[-12.95, -12.65, 1.4, 2.6], [-12.95, -12.65, 8.0, 9.3],
		[-14.75, -13.25, wy0, wy1], [-12.35, -10.85, wy0, wy1]])
	# podlaha prizemi
	b.bb("stone", Vector3(ix0, BASE, iz0), Vector3(ix1, -0.25, iz1), STONE, false, -1, Batch.NY, true)
	b.bb("flag", Vector3(ix0, -0.25, iz0), Vector3(ix1, 0.0, iz1), Color(0.8, 0.8, 0.78), true)
	var wood := Color(0.74, 0.7, 0.64)
	var dark := Color(0.6, 0.56, 0.5)
	# patra: prkenne podlahy s otvorem nad schody
	for fy: float in [WALK, 13.0]:
		b.bb("planks", Vector3(ix0, fy - 0.1, -14.2), Vector3(ix1, fy, iz1), wood, true, 0)
		b.bb("planks", Vector3(ix0, fy - 0.1, iz0), Vector3(-17.2, fy, -14.2), wood, true, 0)
		for k in 4:
			var bz := -13.6 + 1.05 * k
			b.beam("beam", Vector3(ix0 - 0.2, fy - 0.24, bz), Vector3(ix1 + 0.2, fy - 0.24, bz), 0.22, 0.28, dark)
		# zabradli kolem otvoru
		b.beam("beam", Vector3(-17.2, fy + 1.0, -14.2), Vector3(-14.5, fy + 1.0, -14.2), 0.08, 0.1, wood, true)
		b.beam("beam", Vector3(-17.2, fy + 0.5, -14.2), Vector3(-14.5, fy + 0.5, -14.2), 0.06, 0.08, wood, true)
		for px: float in [-17.2, -15.85, -14.5]:
			b.beam("beam", Vector3(px, fy, -14.2), Vector3(px, fy + 1.02, -14.2), 0.1, 0.1, wood)
	# schody: dve ramena na patro
	for sy: float in [0.0, WALK]:
		# pata schodu je metr od zdi, aby se na ne dalo vejit zpredu
		b.stairs("planks", Vector3(-17.75, sy, -11.3), Vector3(0, 0, -1), 2.9, 3.25, 1.1, 16, wood)
		b.bb("planks", Vector3(ix0, sy + 3.15, iz0), Vector3(-17.2, sy + 3.25, -14.2), wood, true, 0)
		b.stairs("planks", Vector3(-17.2, sy + 3.25, -14.75), Vector3(1, 0, 0), 3.9, 3.25, 1.1, 16, wood)
		# schodnice a zabradli
		b.beam("beam", Vector3(-17.2, sy - 0.05, -11.3), Vector3(-17.2, sy + 3.2, -14.2), 0.08, 0.26, dark)
		b.beam("beam", Vector3(-17.2, sy + 0.95, -11.3), Vector3(-17.2, sy + 4.2, -14.2), 0.07, 0.09, wood, true)
		b.beam("beam", Vector3(-17.2, sy + 3.2, -14.2), Vector3(-13.3, sy + 6.45, -14.2), 0.08, 0.26, dark)
		b.beam("beam", Vector3(-17.2, sy, -11.35), Vector3(-17.2, sy + 1.0, -11.35), 0.1, 0.1, wood)
		b.beam("beam", Vector3(-17.2, sy + 3.25, -14.2), Vector3(-17.2, sy + 4.25, -14.2), 0.1, 0.1, wood)
		# podpera podesty
		b.beam("beam", Vector3(-17.3, sy, -14.3), Vector3(-17.3, sy + 3.15, -14.3), 0.14, 0.14, dark)
	# nadprazi oken vyhlidky
	for wx: float in [-17.2, -14.4]:
		b.bb("beam", Vector3(wx - 0.95, wy1 - 0.02, iz1 - 0.02), Vector3(wx + 0.95, wy1 + 0.2, z1 + 0.02), dark, false, 0)
		b.bb("beam", Vector3(wx - 0.95, wy1 - 0.02, z0 - 0.02), Vector3(wx + 0.95, wy1 + 0.2, iz0 + 0.02), dark, false, 0)
	for wz: float in [-14.0, -11.6]:
		b.bb("beam", Vector3(ix1 - 0.02, wy1 - 0.02, wz - 0.95), Vector3(x1 + 0.02, wy1 + 0.2, wz + 0.95), dark, false, 2)
		b.bb("beam", Vector3(x0 - 0.02, wy1 - 0.02, wz - 0.95), Vector3(ix0 + 0.02, wy1 + 0.2, wz + 0.95), dark, false, 2)
	# strop vyhlidky a strecha
	for k in 4:
		var bx2 := -17.6 + 1.2 * k
		b.beam("beam", Vector3(bx2, top - 0.2, z0 + 0.3), Vector3(bx2, top - 0.2, z1 - 0.3), 0.2, 0.26, dark)
	pyramid_roof(b, x0 - 0.6, x1 + 0.6, z0 - 0.6, z1 + 0.6, top, Vector3((x0 + x1) * 0.5, top + 7.0, (z0 + z1) * 0.5))
	# dvere do prizemi: zarubne
	b.bb("beam", Vector3(ix1 - 0.05, 2.1, -13.55), Vector3(x1 + 0.05, 2.32, -12.05), dark, false, 2)
	info["rooms"].append({"name": "vez0", "aabb": AABB(Vector3(ix0, 0, iz0), Vector3(5, WALK - 0.3, 5)), "ambient": Color(0.20, 0.20, 0.21)})
	info["rooms"].append({"name": "vez1", "aabb": AABB(Vector3(ix0, WALK, iz0), Vector3(5, 6.2, 5)), "ambient": Color(0.24, 0.24, 0.25)})
	info["rooms"].append({"name": "vez2", "aabb": AABB(Vector3(ix0, 13.0, iz0), Vector3(5, 4.0, 5)), "ambient": Color(0.5, 0.52, 0.56)})
	info["flag_pole"] = Vector3((x0 + x1) * 0.5, top + 7.3, (z0 + z1) * 0.5)
	b.commit(parent, "Vez")


func _wall_stair(parent: Node3D) -> void:
	var b := Batch.new(M, 41)
	var col := Color(0.9, 0.9, 0.88)
	# schody stoji pred ochozem (ne pod nim), aby nad nimi bylo dost mista na hlavu
	b.stairs("ashlar", Vector3(14.2, 0.0, 12.5), Vector3(-1, 0, 0), 9.6, WALK, 1.4, 36, col, true)
	b.bb("stone", Vector3(3.5, 0.0, 11.8), Vector3(4.6, WALK, 14.0), STONE, true, -1, 0, true)
	b.bb("flag", Vector3(3.5, WALK, 11.8), Vector3(4.6, WALK + 0.03, 14.0), Color(0.82, 0.8, 0.76))
	# zidka na strane do nadvori
	b.beam("ashlar", Vector3(14.3, 0.35, 11.92), Vector3(4.6, WALK + 0.45, 11.92), 0.26, 0.6, col, false)
	b.bb("ashlar", Vector3(3.5, WALK, 11.8), Vector3(4.6, WALK + 0.75, 12.06), col, true)
	b.commit(parent, "SchodyHradba")
