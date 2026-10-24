extends RefCounted
## Rybnik a prikop (radce 04:55 bod 5): teren pod hladinou neni prohlubne s melkym okrajem -> cerna deska s ostrou
## hranou. Hladiny (site s materialem voda_prikop / voda) se rasterizuji do mrizky 0,5 m, vzdalenost od brehu
## (chamfer) urci dno: svah 1:4 do HLOUBKA, za brehem pas bahna 1,2 m tesne nad hladinou. Hloubka jde do barvy
## vrcholu hladiny (COLOR.r * 4 m): u brehu pruhledna, uprostred tmava (shaders/voda.gdshader).

const K := 0.5                 # mrizka (m)
const HLOUBKA := 1.8
const SVAH := 4.0              # 1:4
const BAHNO := 1.2             # pas bahna za brehem (m)
const OKRAJ := 1.1             # breh o tolik dovnitr od hrany hladiny z Blenderu (schody mrizky 2 m)

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
		lo -= Vector2(12, 12)                       # 0.72: i ctvercovy okraj jamy z Blenderu (holy pas) do louky
		hi += Vector2(12, 12)
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
		# hladina z Blenderu je ze ctvercu 2 m -> breh by kopiroval schody (hlaseni 0.54 bod 2, Misa: hrany des).
		# Vzdalenost rozmazat (2x prumer 2,5 m) a breh posunout o OKRAJ dovnitr: hladina je pak vzdy nad zaoblenym
		# brehem (zubata hrana hladiny konci pod terenem), krivka brehu je hladka a sum ji zvlni.
		d = _rozmaz(_rozmaz(d, nx, nz, 2), nx, nz, 2)
		var ns := FastNoiseLite.new()
		ns.seed = 5
		ns.frequency = 0.15
		for j in nz:
			for i in nx:
				d[j * nx + i] -= OKRAJ + 0.35 * ns.get_noise_2d(lo.x + i * K, lo.y + j * K)
		# Misa 0.70 "rybnik ve vsi chybi" (512,871): u male nadrze (do 40 m) zbylo po posunu brehu o OKRAJ a rozmazani
		# skoro nic hloubky - hladina pruhledna, z Blenderu sestiuhelnik. Prirozeny tvar: kruh se stejnou plochou,
		# polomer zvlneny sumem podle uhlu (+-18 %), hladina vlastni siti (nova_hladina).
		var kruh := []
		# Misa 0.70: "rybnik hranaty, nemusi byt kruh, spis ovál nepravidelny": navesni rybnicek z blender/vesnice.py
		# (POND, pond_q) - ovál 14 x 9 m podel osy navsi, breh se zatokami a vybezky (3 harmonicke), d = vzdalenost
		# od brehu v m. Stejny tvar dela hladinu (nova_hladina) i breh (strop, podlaha, bahno).
		var stred_v := VES + VES_AU * POND.x + VES_AV * POND.y
		if (lo + hi) * 0.5 - stred_v == Vector2.ZERO or ((lo + hi) * 0.5).distance_to(stred_v) < 25.0:
			for j2 in nz:
				for i2 in nx:
					var q := lo + Vector2(i2, j2) * K
					d[j2 * nx + i2] = _pond_d(q)
			kruh = [stred_v]
		nadrze.append({"x0": lo.x, "z0": lo.y, "nx": nx, "nz": nz, "y": ys / w.size(), "d": d, "kruh": kruh})


const VES := Vector2(470.0, 830.0)
const VES_AU := Vector2(0.76193, 0.64764)
const VES_AV := Vector2(-0.64764, 0.76193)
const POND := Vector4(74.0, 2.0, 14.0, 9.0)       # blender/vesnice.py POND (u, v, poloosa u, poloosa v)


func _pond_r(a: float) -> float:
	return 1.0 + 0.16 * sin(2.0 * a + 0.7) + 0.09 * sin(3.0 * a + 2.1) + 0.05 * sin(5.0 * a + 4.0)


## Vzdalenost od brehu rybnicka (m, > 0 ve vode): pond_q z Blenderu prevedena na metry podle mistni poloosy.
func _pond_d(p: Vector2) -> float:
	var q := p - VES
	var u := q.dot(VES_AU) - POND.x
	var v := q.dot(VES_AV) - POND.y
	var eu := u / POND.z
	var ev := v / POND.w
	var a := atan2(ev, eu)
	var r := _pond_r(a)
	var qq := Vector2(eu, ev).length() / r
	var mist := r * Vector2(cos(a) * POND.z, sin(a) * POND.w).length()
	return (1.0 - qq) * mist


func _pond_bod(a: float, k: float) -> Vector2:
	var r := _pond_r(a)
	return VES + VES_AU * (POND.x + cos(a) * POND.z * r * k) + VES_AV * (POND.y + sin(a) * POND.w * r * k)


## Hladina male nadrze s prirozenym tvarem: polarni sit do brehu + 0,6 m (okraj pod terenem brehu), COLOR.r = hloubka.
func nova_hladina(n: Dictionary, mat: Material) -> MeshInstance3D:
	var y: float = n["y"]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var na := 72
	var nr := 10
	var body: Array = []
	for ri in nr + 1:
		var row: Array = []
		for ai in na:
			row.append(_pond_bod(TAU * ai / na, (1.0 + 0.45 / POND.w) * float(ri) / nr))    # 0.74: hladina pres breh 0,9 m = "pretekla"
		body.append(row)
	var vrchol := func(p: Vector2) -> void:
		var m := misto(p.x, p.y)
		var h := 0.0 if m.is_empty() or float(m[0]) <= 0.0 else minf(HLOUBKA, 0.05 + float(m[0]) / SVAH)
		st.set_color(Color(h / 4.0, 0, 0, 1))
		st.set_normal(Vector3.UP)
		st.set_uv(p * 0.25)
		st.add_vertex(Vector3(p.x, y, p.y))
	for ri in nr:
		for ai in na:
			var a0: Vector2 = body[ri][ai]
			var a1: Vector2 = body[ri][(ai + 1) % na]
			var b0: Vector2 = body[ri + 1][ai]
			var b1: Vector2 = body[ri + 1][(ai + 1) % na]
			for p: Vector2 in [a0, b0, b1, a0, b1, a1]:
				vrchol.call(p)
	var mesh := st.commit()
	mesh.surface_set_material(0, mat)
	var mi := MeshInstance3D.new()
	mi.name = "Rybnik_hladina"
	mi.mesh = mesh
	return mi


## Prumer ctverce (2r+1)^2 bunek, oddelene po radcich a sloupcich.
func _rozmaz(d: PackedFloat32Array, nx: int, nz: int, r: int) -> PackedFloat32Array:
	var a := PackedFloat32Array()
	a.resize(nx * nz)
	for j in nz:
		for i in nx:
			var s := 0.0
			var c := 0
			for q in range(maxi(0, i - r), mini(nx, i + r + 1)):
				s += d[j * nx + q]
				c += 1
			a[j * nx + i] = s / c
	var b := PackedFloat32Array()
	b.resize(nx * nz)
	for j in nz:
		for i in nx:
			var s := 0.0
			var c := 0
			for q in range(maxi(0, j - r), mini(nz, j + r + 1)):
				s += a[q * nx + i]
				c += 1
			b[j * nx + i] = s / c
	return b


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


## Mala nadrz s prirozenym tvarem: breh nesmi kopirovat ctvercovou jamu z Blenderu - za brehem (d < 0, do 5 m)
## teren aspon na hladine + 4-16 cm (bahno), dal mirne stoupa 1:12.
func podlaha(x: float, z: float) -> float:
	for n: Dictionary in nadrze:
		if (n["kruh"] as Array).is_empty():
			continue
		var i := roundi((x - float(n["x0"])) / K)
		var j := roundi((z - float(n["z0"])) / K)
		if i < 0 or j < 0 or i >= int(n["nx"]) or j >= int(n["nz"]):
			continue
		var d: float = (n["d"] as PackedFloat32Array)[j * int(n["nx"]) + i]
		if d > 0.0 or d < -6.0:
			return -INF
		# do 0,8 m za brehem tesne pod hladinou: okraj vody = hladky okraj site hladiny (pruhledny), ne zuby site
		# terenu 2 m; dal stoupa
		if d > -0.35:
			return float(n["y"]) - 0.05
		return float(n["y"]) - 0.05 + 0.15 * minf((-d - 0.35) / 0.8, 1.0) + 0.1 * maxf(-d - 1.15, 0.0)
	return -INF


## Znamenkova vzdalenost od kulateho brehu male nadrze (> 0 ve vode), jinak -INF.
func _v_kruhu(x: float, z: float) -> float:
	for n: Dictionary in nadrze:
		if (n["kruh"] as Array).is_empty():
			continue
		var i := roundi((x - float(n["x0"])) / K)
		var j := roundi((z - float(n["z0"])) / K)
		if i < 0 or j < 0 or i >= int(n["nx"]) or j >= int(n["nz"]):
			continue
		return (n["d"] as PackedFloat32Array)[j * int(n["nx"]) + i]
	return -INF


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
			var pd := podlaha(w.x, w.z)
			if pd > w.y + 0.01:
				w.y = pd
				v[i] = inv * w
				zde += 1
			if pd > -INF or _v_kruhu(w.x, w.z) > -14.0:     # i zbytek ctvercove jamy z Blenderu (hlina) -> louka
				# bahno a louka podle noveho (kulateho) brehu, ne ctvercu z Blenderu (Misa 0.70 "rybnik hranaty")
				var dk := _v_kruhu(w.x, w.z)
				col[i].a = 1.0 - 0.5 * (1.0 - smoothstep(-0.2, 0.7, -dk)) if dk > -1.0 else 1.0
				col[i].g = lerpf(0.3, 0.85, smoothstep(0.1, 0.8, -dk))
				continue
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
				# za vyhlazenym brehem hloubka 0 -> hladina pruhledna (shader ALPHA), zubaty okraj site neni videt
				var h := 0.0 if m.is_empty() or float(m[0]) <= 0.0 else minf(HLOUBKA, 0.05 + float(m[0]) / SVAH)
				col[i] = Color(h / 4.0, 0, 0, 1)
			arr[Mesh.ARRAY_COLOR] = col
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(s, am.surface_get_material(s))
		nove.surface_set_name(s, am.surface_get_name(s))
	mi.mesh = nove
