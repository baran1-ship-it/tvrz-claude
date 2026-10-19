extends RefCounted
## Rybnik a prikop (radce 04:55 bod 5): teren pod hladinou neni prohlubne s melkym okrajem -> cerna deska s ostrou
## hranou. Hladiny (site s materialem voda_prikop / voda) se rasterizuji do mrizky 0,5 m, vzdalenost od brehu
## (chamfer) urci dno: svah 1:4 do HLOUBKA, za brehem pas bahna 1,2 m tesne nad hladinou. Hloubka jde do barvy
## vrcholu hladiny (COLOR.r * 4 m): u brehu pruhledna, uprostred tmava (shaders/voda.gdshader).

const K := 0.5                 # mrizka (m)
const HLOUBKA := 1.8
const SVAH := 4.0              # 1:4
const BAHNO := 1.2             # pas bahna za brehem (m)

var nadrze: Array = []         # [{x0, z0, nx, nz, y, uvnitr: PackedFloat32Array (vzdal. od brehu, <0 venku)}]


## Hladiny: [[MeshInstance3D, surface]]
func priprav(hladiny: Array) -> void:
	for h: Array in hladiny:
		var mi: MeshInstance3D = h[0]
		var arr := mi.mesh.surface_get_arrays(h[1])
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		var xf := mi.global_transform
		var w := PackedVector3Array()
		for q in v:
			w.append(xf * q)
		if idx.is_empty():
			for i in w.size():
				idx.append(i)
		var lo := Vector2(INF, INF)
		var hi := Vector2(-INF, -INF)
		var ys := 0.0
		for q in w:
			lo = lo.min(Vector2(q.x, q.z))
			hi = hi.max(Vector2(q.x, q.z))
			ys += q.y
		lo -= Vector2(4, 4)
		hi += Vector2(4, 4)
		var nx := int((hi.x - lo.x) / K) + 1
		var nz := int((hi.y - lo.y) / K) + 1
		var m := PackedByteArray()
		m.resize(nx * nz)
		for t in range(0, idx.size(), 3):
			var a := Vector2(w[idx[t]].x, w[idx[t]].z)
			var b := Vector2(w[idx[t + 1]].x, w[idx[t + 1]].z)
			var c := Vector2(w[idx[t + 2]].x, w[idx[t + 2]].z)
			var tl := a.min(b).min(c)
			var th := a.max(b).max(c)
			for j in range(int((tl.y - lo.y) / K), int((th.y - lo.y) / K) + 2):
				for i in range(int((tl.x - lo.x) / K), int((th.x - lo.x) / K) + 2):
					if i < 0 or j < 0 or i >= nx or j >= nz:
						continue
					var p := lo + Vector2(i, j) * K
					if Geometry2D.point_is_inside_triangle(p, a, b, c):
						m[j * nx + i] = 1
		# vzdalenost od brehu: uvnitr kladna, venku zaporna (dva pruchody chamfer 3-4)
		var din := _vzdal(m, nx, nz, 1)
		var dout := _vzdal(m, nx, nz, 0)
		var d := PackedFloat32Array()
		d.resize(nx * nz)
		for i in nx * nz:
			d[i] = din[i] if m[i] == 1 else -dout[i]
		nadrze.append({"x0": lo.x, "z0": lo.y, "nx": nx, "nz": nz, "y": ys / w.size(), "d": d})


func _vzdal(m: PackedByteArray, nx: int, nz: int, uvnitr: int) -> PackedFloat32Array:
	var d := PackedFloat32Array()
	d.resize(nx * nz)
	for i in nx * nz:
		d[i] = 1e6 if m[i] == uvnitr else 0.0
	for j in nz:
		for i in nx:
			var k := j * nx + i
			if i > 0:
				d[k] = minf(d[k], d[k - 1] + K)
			if j > 0:
				d[k] = minf(d[k], d[k - nx] + K)
				if i > 0:
					d[k] = minf(d[k], d[k - nx - 1] + K * 1.414)
				if i < nx - 1:
					d[k] = minf(d[k], d[k - nx + 1] + K * 1.414)
	for j in range(nz - 1, -1, -1):
		for i in range(nx - 1, -1, -1):
			var k := j * nx + i
			if i < nx - 1:
				d[k] = minf(d[k], d[k + 1] + K)
			if j < nz - 1:
				d[k] = minf(d[k], d[k + nx] + K)
				if i < nx - 1:
					d[k] = minf(d[k], d[k + nx + 1] + K * 1.414)
				if i > 0:
					d[k] = minf(d[k], d[k + nx - 1] + K * 1.414)
	return d


## [vzdalenost od brehu (+ uvnitr), hladina] nebo []
func misto(x: float, z: float) -> Array:
	for n: Dictionary in nadrze:
		var i := roundi((x - float(n["x0"])) / K)
		var j := roundi((z - float(n["z0"])) / K)
		if i < 0 or j < 0 or i >= int(n["nx"]) or j >= int(n["nz"]):
			continue
		return [(n["d"] as PackedFloat32Array)[j * int(n["nx"]) + i], n["y"]]
	return []


func strop(x: float, z: float) -> float:
	var m := misto(x, z)
	if m.is_empty():
		return INF
	var d: float = m[0]
	var y: float = m[1]
	if d > 0.0:
		return y - minf(HLOUBKA, 0.05 + d / SVAH)
	if d > -BAHNO:
		return y + 0.04 + 0.12 * (-d / BAHNO)
	return INF


func bahno(x: float, z: float) -> float:
	var m := misto(x, z)
	if m.is_empty():
		return 0.0
	var d: float = m[0]
	return 1.0 - smoothstep(BAHNO * 0.6, BAHNO * 1.6, -d) if d < 0.5 else 1.0


## Teren dolu + COLOR.a = 1 - 0,5 * bahno (koryto potoka pouziva a < 0,5).
func vyhloub(mi: MeshInstance3D) -> int:
	var am := mi.mesh as ArrayMesh
	if am == null:
		return 0
	var xf := mi.global_transform
	var inv := xf.affine_inverse()
	var nove := ArrayMesh.new()
	var zmen := 0
	for s in am.get_surface_count():
		var arr := am.surface_get_arrays(s)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var col: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
		if col.is_empty():
			col.resize(v.size())
			col.fill(Color(0, 0.85, 0, 1))
		var zde := 0
		for i in v.size():
			var w := xf * v[i]
			var st := strop(w.x, w.z)
			if st < INF:
				var b := bahno(w.x, w.z)
				if b > 0.0 and col[i].a >= 0.5:
					col[i].a = 1.0 - 0.5 * b
				if st < w.y:
					w.y = st
					v[i] = inv * w
					zde += 1
		zmen += zde
		arr[Mesh.ARRAY_VERTEX] = v
		arr[Mesh.ARRAY_COLOR] = col
		if zde > 0:
			arr[Mesh.ARRAY_NORMAL] = null
			arr[Mesh.ARRAY_TANGENT] = null
			var st2 := SurfaceTool.new()
			st2.create_from_arrays(arr)
			st2.generate_normals()
			if arr[Mesh.ARRAY_TEX_UV] != null:
				st2.generate_tangents()
			arr = st2.commit_to_arrays()
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(s, am.surface_get_material(s))
		nove.surface_set_name(s, am.surface_get_name(s))
	mi.mesh = nove
	return zmen


## Hloubka do barvy vrcholu hladiny (COLOR.r = hloubka / 4 m).
func hloubka_hladiny(mi: MeshInstance3D, surf: int) -> void:
	var am := mi.mesh as ArrayMesh
	var xf := mi.global_transform
	var nove := ArrayMesh.new()
	for s in am.get_surface_count():
		var arr := am.surface_get_arrays(s)
		if s == surf:
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var col := PackedColorArray()
			col.resize(v.size())
			for i in v.size():
				var w := xf * v[i]
				var m := misto(w.x, w.z)
				var h := 0.0 if m.is_empty() else minf(HLOUBKA, 0.05 + maxf(float(m[0]), 0.0) / SVAH)
				col[i] = Color(h / 4.0, 0, 0, 1)
			arr[Mesh.ARRAY_COLOR] = col
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(s, am.surface_get_material(s))
		nove.surface_set_name(s, am.surface_get_name(s))
	mi.mesh = nove
