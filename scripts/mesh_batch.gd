extends RefCounted
## Sklada geometrii po materialech do velkych siti a k nim kolizni telesa.
## UV se pocitaji ze svetovych souradnic, takze textura navazuje pres sousedni kvadry.

class Surf:
	var v := PackedVector3Array()
	var n := PackedVector3Array()
	var uv := PackedVector2Array()
	var c := PackedColorArray()
	var i := PackedInt32Array()

const PX := 1
const NX := 2
const PY := 4
const NY := 8
const PZ := 16
const NZ := 32

var mats: Dictionary
var surf: Dictionary = {}
var boxes: Array = []      # [Transform3D, Vector3]
var hulls: Array = []      # PackedVector3Array
var tint_noise := FastNoiseLite.new()
var rng := RandomNumberGenerator.new()
var ground_y := 0.0


func _init(p_mats: Dictionary, seed_value: int = 1) -> void:
	mats = p_mats
	rng.seed = seed_value
	tint_noise.seed = seed_value
	tint_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	tint_noise.frequency = 0.16
	tint_noise.fractal_octaves = 3


func _surface(key: String) -> Surf:
	if not surf.has(key):
		surf[key] = Surf.new()
	return surf[key]


func jitter(amount: float) -> float:
	return rng.randf_range(-amount, amount)


## Zakladni ctyruhelnik. Poradi rohu je libovolne dokola, orientaci urci normala.
func quad(key: String, a: Vector3, b: Vector3, c: Vector3, d: Vector3, nrm: Vector3,
		col: Color = Color.WHITE, grain: Vector3 = Vector3.ZERO) -> void:
	quad4(key, a, b, c, d, nrm, col, col, col, col, grain)


func quad4(key: String, a: Vector3, b: Vector3, c: Vector3, d: Vector3, nrm: Vector3,
		ca: Color, cb: Color, cc: Color, cd: Color, grain: Vector3 = Vector3.ZERO) -> void:
	var s := _surface(key)
	var tile: float = mats[key]["tile"]
	var uu: Vector3
	var vd: Vector3
	var done := false
	if grain != Vector3.ZERO:
		vd = grain - nrm * grain.dot(nrm)
		if vd.length_squared() > 0.01:
			vd = vd.normalized()
			uu = vd.cross(nrm).normalized()
			done = true
	if not done:
		if absf(nrm.y) > 0.985:
			uu = Vector3(1, 0, 0)
			vd = Vector3(0, 0, 1)
		else:
			uu = Vector3.UP.cross(nrm).normalized()
			vd = uu.cross(nrm).normalized()
	var base := s.v.size()
	s.v.append(a)
	s.v.append(b)
	s.v.append(c)
	s.v.append(d)
	for k in 4:
		s.n.append(nrm)
	s.uv.append(Vector2(a.dot(uu), a.dot(vd)) / tile)
	s.uv.append(Vector2(b.dot(uu), b.dot(vd)) / tile)
	s.uv.append(Vector2(c.dot(uu), c.dot(vd)) / tile)
	s.uv.append(Vector2(d.dot(uu), d.dot(vd)) / tile)
	s.c.append(ca)
	s.c.append(cb)
	s.c.append(cc)
	s.c.append(cd)
	# Godot ma predni stranu po smeru hodinovych rucicek
	if (b - a).cross(c - a).dot(nrm) > 0.0:
		s.i.append(base)
		s.i.append(base + 2)
		s.i.append(base + 1)
		s.i.append(base)
		s.i.append(base + 3)
		s.i.append(base + 2)
	else:
		s.i.append(base)
		s.i.append(base + 1)
		s.i.append(base + 2)
		s.i.append(base)
		s.i.append(base + 2)
		s.i.append(base + 3)


func tri(key: String, a: Vector3, b: Vector3, c: Vector3, nrm: Vector3, col: Color = Color.WHITE) -> void:
	var s := _surface(key)
	var tile: float = mats[key]["tile"]
	var uu: Vector3
	var vd: Vector3
	if absf(nrm.y) > 0.985:
		uu = Vector3(1, 0, 0)
		vd = Vector3(0, 0, 1)
	else:
		uu = Vector3.UP.cross(nrm).normalized()
		vd = uu.cross(nrm).normalized()
	var base := s.v.size()
	for p: Vector3 in [a, b, c]:
		s.v.append(p)
		s.n.append(nrm)
		s.uv.append(Vector2(p.dot(uu), p.dot(vd)) / tile)
		s.c.append(col)
	if (b - a).cross(c - a).dot(nrm) > 0.0:
		s.i.append(base)
		s.i.append(base + 2)
		s.i.append(base + 1)
	else:
		s.i.append(base)
		s.i.append(base + 1)
		s.i.append(base + 2)


## Odstin zdi podle polohy: velke skvrny a ztmavnuti u zeme.
func tint(p: Vector3, col: Color) -> Color:
	var t := 0.92 + 0.13 * tint_noise.get_noise_3d(p.x, p.y * 1.4, p.z)
	var g := clampf((p.y - ground_y) / 1.5, 0.0, 1.0)
	t *= 0.74 + 0.26 * g
	return Color(col.r * t, col.g * t, col.b * t * 0.985, col.a)


## Ctyruhelnik rozdeleny na bunky, aby slo po vrcholech menit odstin.
func gquad(key: String, o: Vector3, eu: Vector3, ev: Vector3, nrm: Vector3, col: Color, cell: float = 1.6) -> void:
	var nu := maxi(1, int(ceil(eu.length() / cell)))
	var nv := maxi(1, int(ceil(ev.length() / cell)))
	for j in nv:
		for i in nu:
			var a := o + eu * (float(i) / nu) + ev * (float(j) / nv)
			var b := o + eu * (float(i + 1) / nu) + ev * (float(j) / nv)
			var c := o + eu * (float(i + 1) / nu) + ev * (float(j + 1) / nv)
			var d := o + eu * (float(i) / nu) + ev * (float(j + 1) / nv)
			quad4(key, a, b, c, d, nrm, tint(a, col), tint(b, col), tint(c, col), tint(d, col))


## Kvadr s libovolnou transformaci. grain_axis 0/1/2 = leta dreva podel mistni osy.
func box(key: String, xf: Transform3D, size: Vector3, col: Color = Color.WHITE, collide: bool = false,
		grain_axis: int = -1, skip: int = 0, tinted: bool = false) -> void:
	var h := size * 0.5
	var ax := xf.basis.x.normalized()
	var ay := xf.basis.y.normalized()
	var az := xf.basis.z.normalized()
	var o := xf.origin
	var grain := Vector3.ZERO
	if grain_axis == 0:
		grain = ax
	elif grain_axis == 1:
		grain = ay
	elif grain_axis == 2:
		grain = az
	var ex := ax * h.x
	var ey := ay * h.y
	var ez := az * h.z
	if tinted:
		if not (skip & PX):
			gquad(key, o + ex - ey - ez, ez * 2.0, ey * 2.0, ax, col)
		if not (skip & NX):
			gquad(key, o - ex - ey - ez, ez * 2.0, ey * 2.0, -ax, col)
		if not (skip & PZ):
			gquad(key, o - ex - ey + ez, ex * 2.0, ey * 2.0, az, col)
		if not (skip & NZ):
			gquad(key, o - ex - ey - ez, ex * 2.0, ey * 2.0, -az, col)
		if not (skip & PY):
			gquad(key, o - ex + ey - ez, ex * 2.0, ez * 2.0, ay, col, 3.0)
		if not (skip & NY):
			quad(key, o - ex - ey - ez, o + ex - ey - ez, o + ex - ey + ez, o - ex - ey + ez, -ay, col)
	else:
		if not (skip & PX):
			quad(key, o + ex - ey - ez, o + ex + ey - ez, o + ex + ey + ez, o + ex - ey + ez, ax, col, grain)
		if not (skip & NX):
			quad(key, o - ex - ey - ez, o - ex + ey - ez, o - ex + ey + ez, o - ex - ey + ez, -ax, col, grain)
		if not (skip & PY):
			quad(key, o - ex + ey - ez, o + ex + ey - ez, o + ex + ey + ez, o - ex + ey + ez, ay, col, grain)
		if not (skip & NY):
			quad(key, o - ex - ey - ez, o + ex - ey - ez, o + ex - ey + ez, o - ex - ey + ez, -ay, col, grain)
		if not (skip & PZ):
			quad(key, o - ex - ey + ez, o + ex - ey + ez, o + ex + ey + ez, o - ex + ey + ez, az, col, grain)
		if not (skip & NZ):
			quad(key, o - ex - ey - ez, o + ex - ey - ez, o + ex + ey - ez, o - ex + ey - ez, -az, col, grain)
	if collide:
		boxes.append([xf, size])


## Kvadr rovnobezny s osami, zadany stredem a rozmery.
func bx(key: String, center: Vector3, size: Vector3, col: Color = Color.WHITE, collide: bool = false,
		grain_axis: int = -1, skip: int = 0, tinted: bool = false) -> void:
	box(key, Transform3D(Basis.IDENTITY, center), size, col, collide, grain_axis, skip, tinted)


## Kvadr rovnobezny s osami, zadany dvema protilehlymi rohy.
func bb(key: String, p0: Vector3, p1: Vector3, col: Color = Color.WHITE, collide: bool = false,
		grain_axis: int = -1, skip: int = 0, tinted: bool = false) -> void:
	var lo := Vector3(minf(p0.x, p1.x), minf(p0.y, p1.y), minf(p0.z, p1.z))
	var hi := Vector3(maxf(p0.x, p1.x), maxf(p0.y, p1.y), maxf(p0.z, p1.z))
	box(key, Transform3D(Basis.IDENTITY, (lo + hi) * 0.5), hi - lo, col, collide, grain_axis, skip, tinted)


## Kvadr otoceny kolem svisle osy.
func bxr(key: String, center: Vector3, size: Vector3, yaw_deg: float, col: Color = Color.WHITE,
		collide: bool = false, grain_axis: int = -1) -> void:
	box(key, Transform3D(Basis(Vector3.UP, deg_to_rad(yaw_deg)), center), size, col, collide, grain_axis)


## Tram z bodu do bodu, leta po delce.
func beam(key: String, from: Vector3, to: Vector3, w: float, h: float, col: Color = Color.WHITE,
		collide: bool = false, roll_deg: float = 0.0) -> void:
	var dir := to - from
	var ln := dir.length()
	if ln < 0.001:
		return
	var z := dir / ln
	var up := Vector3.UP if absf(z.y) < 0.99 else Vector3(1, 0, 0)
	var x := up.cross(z).normalized()
	var y := z.cross(x).normalized()
	var b := Basis(x, y, z)
	if roll_deg != 0.0:
		b = b * Basis(Vector3(0, 0, 1), deg_to_rad(roll_deg))
	box(key, Transform3D(b, (from + to) * 0.5), Vector3(w, h, ln), col, collide, 2)


## Deska: ctyruhelnik vytazeny do tloustky proti sve normale (strechy, rampy).
func slab(key: String, a: Vector3, b: Vector3, c: Vector3, d: Vector3, thick: float,
		col: Color = Color.WHITE, collide: bool = false, key_under: String = "", grain: Vector3 = Vector3.ZERO) -> void:
	var n := (b - a).cross(d - a).normalized()
	if n.y < 0.0 or (absf(n.y) < 0.001 and n.dot(Vector3(1, 0, 1)) < 0.0):
		n = -n
	var off := -n * thick
	var a2 := a + off
	var b2 := b + off
	var c2 := c + off
	var d2 := d + off
	quad(key, a, b, c, d, n, col, grain)
	var ku := key if key_under == "" else key_under
	quad(ku, a2, b2, c2, d2, -n, col, grain)
	var cen := (a + b + c + d) * 0.25 + off * 0.5
	var top := [a, b, c, d]
	var bot := [a2, b2, c2, d2]
	for k in 4:
		var p: Vector3 = top[k]
		var q: Vector3 = top[(k + 1) % 4]
		var p2: Vector3 = bot[k]
		var q2: Vector3 = bot[(k + 1) % 4]
		var sn := (q - p).cross(n).normalized()
		if sn.dot((p + q) * 0.5 - cen) < 0.0:
			sn = -sn
		quad(ku, p, q, q2, p2, sn, col, grain)
	if collide:
		hulls.append(PackedVector3Array([a, b, c, d, a2, b2, c2, d2]))


## Trojuhelnikova deska (stity).
func tri_slab(key: String, a: Vector3, b: Vector3, c: Vector3, thick: float, col: Color = Color.WHITE,
		collide: bool = false, tinted: bool = false) -> void:
	var n := (b - a).cross(c - a).normalized()
	if n.y < -0.001 or (absf(n.y) <= 0.001 and n.dot(Vector3(1, 0, 1)) < 0.0):
		n = -n
	var off := -n * thick
	var ca := tint(a, col) if tinted else col
	var cb := tint(b, col) if tinted else col
	var cc := tint(c, col) if tinted else col
	_tri_col(key, a, b, c, n, ca, cb, cc)
	_tri_col(key, a + off, b + off, c + off, -n, ca, cb, cc)
	var cen := (a + b + c) / 3.0 + off * 0.5
	var pts := [a, b, c]
	for k in 3:
		var p: Vector3 = pts[k]
		var q: Vector3 = pts[(k + 1) % 3]
		var sn := (q - p).cross(n).normalized()
		if sn.dot((p + q) * 0.5 - cen) < 0.0:
			sn = -sn
		quad(key, p, q, q + off, p + off, sn, col)
	if collide:
		hulls.append(PackedVector3Array([a, b, c, a + off, b + off, c + off]))


func _tri_col(key: String, a: Vector3, b: Vector3, c: Vector3, nrm: Vector3, ca: Color, cb: Color, cc: Color) -> void:
	var s := _surface(key)
	var start := s.c.size()
	tri(key, a, b, c, nrm, ca)
	s.c[start + 1] = cb
	s.c[start + 2] = cc


## Rotacni teleso z profilu (polomer, vyska). Hladke normaly.
func lathe(key: String, xf: Transform3D, prof: PackedVector2Array, segs: int, col: Color = Color.WHITE,
		cap_bottom: bool = false, cap_top: bool = false) -> void:
	var s := _surface(key)
	var tile: float = mats[key]["tile"]
	var base := s.v.size()
	var count := prof.size()
	var rmax := 0.0
	for p in prof:
		rmax = maxf(rmax, p.x)
	var run := 0.0
	var nb := xf.basis.orthonormalized()
	for i in count:
		var prev := prof[maxi(i - 1, 0)]
		var next := prof[mini(i + 1, count - 1)]
		var t := (next - prev)
		var n2 := Vector2(t.y, -t.x).normalized() if t.length() > 0.00001 else Vector2(1, 0)
		if i > 0:
			run += (prof[i] - prof[i - 1]).length()
		for j in segs + 1:
			var ang := TAU * float(j) / segs
			var cs := cos(ang)
			var sn := sin(ang)
			s.v.append(xf * Vector3(cs * prof[i].x, prof[i].y, sn * prof[i].x))
			s.n.append((nb * Vector3(cs * n2.x, n2.y, sn * n2.x)).normalized())
			s.uv.append(Vector2(float(j) / segs * TAU * rmax, -run) / tile)
			s.c.append(col)
	for i in count - 1:
		for j in segs:
			var i0 := base + i * (segs + 1) + j
			var i1 := i0 + 1
			var i2 := i0 + segs + 1
			var i3 := i2 + 1
			_tri_idx(s, i0, i2, i1)
			_tri_idx(s, i1, i2, i3)
	if cap_bottom:
		_cap(key, xf, prof[0], segs, col, false)
	if cap_top:
		_cap(key, xf, prof[count - 1], segs, col, true)


func _cap(key: String, xf: Transform3D, p: Vector2, segs: int, col: Color, up: bool) -> void:
	var nrm := (xf.basis.orthonormalized() * (Vector3.UP if up else Vector3.DOWN)).normalized()
	var cen := xf * Vector3(0, p.y, 0)
	for j in segs:
		var a0 := TAU * float(j) / segs
		var a1 := TAU * float(j + 1) / segs
		tri(key, cen, xf * Vector3(cos(a0) * p.x, p.y, sin(a0) * p.x), xf * Vector3(cos(a1) * p.x, p.y, sin(a1) * p.x), nrm, col)


func _tri_idx(s: Surf, i0: int, i1: int, i2: int) -> void:
	var g := (s.v[i1] - s.v[i0]).cross(s.v[i2] - s.v[i0])
	if g.dot(s.n[i0] + s.n[i1] + s.n[i2]) > 0.0:
		s.i.append(i0)
		s.i.append(i2)
		s.i.append(i1)
	else:
		s.i.append(i0)
		s.i.append(i1)
		s.i.append(i2)


## Valec nebo komoly kuzel stojici na base.
func cyl(key: String, base_pos: Vector3, r0: float, r1: float, height: float, segs: int = 12,
		col: Color = Color.WHITE, caps: bool = true, basis: Basis = Basis.IDENTITY, collide: bool = false) -> void:
	var xf := Transform3D(basis, base_pos)
	lathe(key, xf, PackedVector2Array([Vector2(r0, 0), Vector2(r1, height)]), segs, col, caps, caps)
	if collide:
		var r := maxf(r0, r1)
		boxes.append([Transform3D(basis, base_pos + basis * Vector3(0, height * 0.5, 0)), Vector3(r * 1.6, height, r * 1.6)])


## Valec mezi dvema body.
func rod(key: String, from: Vector3, to: Vector3, r: float, segs: int = 8, col: Color = Color.WHITE, r_end: float = -1.0) -> void:
	var dir := to - from
	var ln := dir.length()
	if ln < 0.0001:
		return
	var y := dir / ln
	var up := Vector3.UP if absf(y.y) < 0.99 else Vector3(1, 0, 0)
	var x := up.cross(y).normalized()
	var z := x.cross(y).normalized()
	cyl(key, from, r, r if r_end < 0.0 else r_end, ln, segs, col, true, Basis(x, y, z))


## Koule (nebo zplostela) ze dvou polokouli.
func ball(key: String, center: Vector3, radius: Vector3, segs: int = 12, col: Color = Color.WHITE) -> void:
	var prof := PackedVector2Array()
	var rings := maxi(4, segs / 2)
	for i in rings + 1:
		var a := -PI * 0.5 + PI * float(i) / rings
		prof.append(Vector2(cos(a), sin(a)))
	lathe(key, Transform3D(Basis.from_scale(radius), center), prof, segs, col)


## Trubka podel lomene cary (lana, luciste).
func tube(key: String, pts: PackedVector3Array, radius: float, segs: int = 6, col: Color = Color.WHITE,
		radius_end: float = -1.0) -> void:
	if pts.size() < 2:
		return
	var s := _surface(key)
	var tile: float = mats[key]["tile"]
	var base := s.v.size()
	var run := 0.0
	var ref := Vector3.UP
	for i in pts.size():
		var d := (pts[mini(i + 1, pts.size() - 1)] - pts[maxi(i - 1, 0)]).normalized()
		if absf(d.dot(ref)) > 0.98:
			ref = Vector3(1, 0, 0)
		var x := ref.cross(d).normalized()
		var y := d.cross(x).normalized()
		ref = y
		if i > 0:
			run += (pts[i] - pts[i - 1]).length()
		var t := float(i) / (pts.size() - 1)
		var r := radius if radius_end < 0.0 else lerpf(radius, radius_end, t)
		for j in segs + 1:
			var ang := TAU * float(j) / segs
			var nrm := x * cos(ang) + y * sin(ang)
			s.v.append(pts[i] + nrm * r)
			s.n.append(nrm)
			s.uv.append(Vector2(float(j) / segs * TAU * radius, run) / tile)
			s.c.append(col)
	for i in pts.size() - 1:
		for j in segs:
			var i0 := base + i * (segs + 1) + j
			_tri_idx(s, i0, i0 + segs + 1, i0 + 1)
			_tri_idx(s, i0 + 1, i0 + segs + 1, i0 + segs + 2)


## Schodiste: viditelne stupne a pod nimi neviditelna rampa pro plynulou chuzi.
func stairs(key: String, start: Vector3, dir: Vector3, run: float, rise: float, width: float, steps: int,
		col: Color = Color.WHITE, solid: bool = false, tread: float = 0.06) -> void:
	var d := dir.normalized()
	var side := Vector3.UP.cross(d).normalized()
	var sr := run / steps
	var sh := rise / steps
	var b := Basis(side, Vector3.UP, d)
	for k in steps:
		var top := start.y + sh * (k + 1)
		var cz := start + d * (sr * (k + 0.5))
		if solid:
			var hgt := top - start.y
			box(key, Transform3D(b, Vector3(cz.x, start.y + hgt * 0.5, cz.z)), Vector3(width, hgt, sr), col, false, -1, 0, false)
		else:
			box(key, Transform3D(b, Vector3(cz.x, top - tread * 0.5, cz.z)), Vector3(width, tread, sr + 0.04), col, false, 0)
	# rampa
	var a0 := start - side * (width * 0.5)
	var a1 := start + side * (width * 0.5)
	var e := d * run + Vector3(0, rise, 0)
	hulls.append(PackedVector3Array([a0, a1, a1 + e, a0 + e,
			a0 - Vector3(0, 0.3, 0), a1 - Vector3(0, 0.3, 0), a1 + e - Vector3(0, 0.3, 0), a0 + e - Vector3(0, 0.3, 0)]))


## Karta s vlastnimi UV a normalami (listi). uv = [Vector2 x4], nrm = [Vector3 x4], cols = [Color x4].
func card(key: String, pts: Array, nrm: Array, uv: Array, cols: Array) -> void:
	var s := _surface(key)
	var base := s.v.size()
	for k in 4:
		s.v.append(pts[k])
		s.n.append(nrm[k])
		s.uv.append(uv[k])
		s.c.append(cols[k])
	s.i.append(base)
	s.i.append(base + 1)
	s.i.append(base + 2)
	s.i.append(base)
	s.i.append(base + 2)
	s.i.append(base + 3)


## Vse nasbirane jako jedna sit s povrchem na kazdy material (pro MultiMesh).
func to_mesh() -> ArrayMesh:
	var mesh := ArrayMesh.new()
	for key: String in surf:
		var s: Surf = surf[key]
		if s.v.is_empty():
			continue
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = s.v
		arr[Mesh.ARRAY_NORMAL] = s.n
		arr[Mesh.ARRAY_TEX_UV] = s.uv
		arr[Mesh.ARRAY_COLOR] = s.c
		arr[Mesh.ARRAY_INDEX] = s.i
		var st := SurfaceTool.new()
		st.create_from_arrays(arr)
		st.generate_tangents()
		st.commit(mesh)
		mesh.surface_set_material(mesh.get_surface_count() - 1, mats[key]["mat"])
	surf = {}
	boxes = []
	hulls = []
	return mesh


## Jen kolizni kvadr bez viditelne geometrie.
func collider(center: Vector3, size: Vector3, yaw_deg: float = 0.0) -> void:
	boxes.append([Transform3D(Basis(Vector3.UP, deg_to_rad(yaw_deg)), center), size])


## Vytvori uzly: jednu sit na material a jedno staticke teleso s koliznimi tvary.
func commit(parent: Node3D, node_name: String, shadows: bool = true) -> Node3D:
	var root := Node3D.new()
	root.name = node_name
	parent.add_child(root)
	for key: String in surf:
		var s: Surf = surf[key]
		if s.v.is_empty():
			continue
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = s.v
		arr[Mesh.ARRAY_NORMAL] = s.n
		arr[Mesh.ARRAY_TEX_UV] = s.uv
		arr[Mesh.ARRAY_COLOR] = s.c
		arr[Mesh.ARRAY_INDEX] = s.i
		var st := SurfaceTool.new()
		st.create_from_arrays(arr)
		st.generate_tangents()
		var mi := MeshInstance3D.new()
		mi.name = key
		mi.mesh = st.commit()
		mi.material_override = mats[key]["mat"]
		if not shadows:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(mi)
	if not boxes.is_empty() or not hulls.is_empty():
		var body := StaticBody3D.new()
		body.name = "Body"
		root.add_child(body)
		for bdef: Array in boxes:
			var cs := CollisionShape3D.new()
			var shape := BoxShape3D.new()
			shape.size = bdef[1]
			cs.shape = shape
			cs.transform = bdef[0]
			body.add_child(cs)
		for pts: PackedVector3Array in hulls:
			var cs2 := CollisionShape3D.new()
			var hull := ConvexPolygonShape3D.new()
			hull.points = pts
			cs2.shape = hull
			body.add_child(cs2)
	surf = {}
	boxes = []
	hulls = []
	return root
