extends RefCounted
## Rybnik a prikop (radce 04:55 bod 5): teren pod hladinou neni prohlubne s melkym okrajem -> cerna deska s ostrou
## hranou. Hladiny (site s materialem voda_prikop / voda) se rasterizuji do mrizky 0,5 m, vzdalenost od brehu
## (chamfer) urci dno: svah 1:4 do HLOUBKA, za brehem pas bahna 1,2 m tesne nad hladinou. Hloubka jde do barvy
## vrcholu hladiny (COLOR.r * 4 m): u brehu pruhledna, uprostred tmava (shaders/voda.gdshader).

const K := 0.5                 # mrizka (m)
const HLOUBKA := 1.8
const SVAH := 4.0              # 1:4
const BAHNO := 1.2             # pas bahna za brehem (m)
const OKRAJ := 0.4             # breh nejmene o tolik dovnitr od hrany hladiny z Blenderu (hrana site pod terenem)
const VLNA := 1.5              # + az tolik podle sumu (dve oktavy): breh zvlneny, zatocinky (Misa: "jak podle pravitka")
const BREH := 3.0              # do teto vzdalenosti za brehem se teren tvaruje (zvedne i snizi) podle krivky brehu

var stary := OS.has_environment("TVRZ_BREH_STARY")   # DOCASNE snimky pred
var nadrze: Array = []         # [{x0, z0, nx, nz, y, d: vzdal. od brehu (<0 venku), b: sirka bahna}] (mrizka K)


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
		# hladina z Blenderu je ze ctvercu 2 m -> breh by kopiroval schody (hlaseni 0.54 bod 2, Misa: hrany des).
		# Vzdalenost rozmazat (2x prumer 2,5 m) a breh posunout o OKRAJ dovnitr: hladina je pak vzdy nad zaoblenym
		# brehem (zubata hrana hladiny konci pod terenem), krivka brehu je hladka a sum ji zvlni.
		d = _rozmaz(_rozmaz(d, nx, nz, 2), nx, nz, 2)
		# Misa 10-22 "hrany vody jak podle pravitka": teren z Blenderu ma prikop jako rovny kanal (mrizka 1 m), voda
		# ho protinala v primce. Breh = krivka z rozmazane vzdalenosti posunuta dovnitr o OKRAJ + VLNA * sum (~11 m
		# a ~3 m), vyhloub() teren u brehu zvedne i snizi -> zvlnena linie styku, hrana site hladiny je vzdy pod terenem.
		var n1 := FastNoiseLite.new()
		n1.seed = 5
		n1.frequency = 0.09
		var n2 := FastNoiseLite.new()
		n2.seed = 17
		n2.frequency = 0.33
		var n3 := FastNoiseLite.new()
		n3.seed = 29
		n3.frequency = 0.14
		var bw := PackedFloat32Array()
		bw.resize(nx * nz)
		for j in nz:
			for i in nx:
				var x := lo.x + i * K
				var z := lo.y + j * K
				var u := clampf(0.5 + 0.75 * n1.get_noise_2d(x, z) + 0.3 * n2.get_noise_2d(x, z), 0.0, 1.0)
				d[j * nx + i] -= OKRAJ + VLNA * u
				if stary:
					d[j * nx + i] += OKRAJ + VLNA * u - 1.1 - 0.35 * n3.get_noise_2d(x, z)
				# sirka pasu bahna 0,4-2 m (u zatocinek sir, na vybezcich uzky)
				bw[j * nx + i] = clampf(1.1 + 1.2 * n3.get_noise_2d(x, z) + 0.5 * (0.5 - u), 0.4, 2.0)
		nadrze.append({"x0": lo.x, "z0": lo.y, "nx": nx, "nz": nz, "y": ys / w.size(), "d": d, "b": bw})


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


## [vzdalenost od brehu (+ uvnitr), hladina, sirka bahna] nebo []; bilinearne (nejblizsi bunka = schody 0,5 m)
func misto(x: float, z: float) -> Array:
	for n: Dictionary in nadrze:
		var fx := (x - float(n["x0"])) / K
		var fz := (z - float(n["z0"])) / K
		var nx := int(n["nx"])
		if fx < 0.0 or fz < 0.0 or fx > nx - 1.001 or fz > int(n["nz"]) - 1.001:
			continue
		var i := floori(fx)
		var j := floori(fz)
		if stary:
			return [(n["d"] as PackedFloat32Array)[roundi(fz) * nx + roundi(fx)], n["y"], 1.2]
		fx -= i
		fz -= j
		var k := j * nx + i
		var d: PackedFloat32Array = n["d"]
		var b: PackedFloat32Array = n["b"]
		return [lerpf(lerpf(d[k], d[k + 1], fx), lerpf(d[k + nx], d[k + nx + 1], fx), fz), n["y"],
				lerpf(lerpf(b[k], b[k + 1], fx), lerpf(b[k + nx], b[k + nx + 1], fx), fz)]
	return []


## Teren v bode podle krivky brehu (y = puvodni vyska): pod hladinou svah 1:SVAH do HLOUBKA (jen dolu); za brehem
## do BREH m mirna plaz tesne nad vodou (zvedne, kde byl teren z Blenderu pod hladinou) a nad ni strmejsi breh
## (snizi jen u vody, pata hradby zustava).
func vyska(x: float, z: float, y: float) -> float:
	var m := misto(x, z)
	if m.is_empty():
		return y
	var d: float = m[0]
	var wy: float = m[1]
	if d > 0.0:
		return minf(y, wy - minf(HLOUBKA, 0.03 + d / SVAH))
	var e := -d
	if stary:
		return minf(y, wy + 0.04 + 0.12 * (e / BAHNO)) if e < BAHNO else y
	if e >= BREH:
		return y
	var dno := wy + 0.03 + 0.12 * e                                   # plaz: vzdy nad vodou
	var cap := wy + 0.06 + 0.25 * e + 2.5 * pow(maxf(e - 0.6, 0.0), 2.0)  # breh: nad plazi zvedne strmeji
	return clampf(y, dno, maxf(cap, dno))


## Nejvyssi povolena vyska (INF = bez omezeni) - jen pro snizovani.
func strop(x: float, z: float) -> float:
	var v := vyska(x, z, 1e6)
	return INF if v >= 1e5 else v


## Bahno 0..1: u vody 1, pas promenlive sirky (m[2]), okraj roztrepi zem.gdshader sumem.
func bahno(x: float, z: float) -> float:
	var m := misto(x, z)
	if m.is_empty():
		return 0.0
	var d: float = m[0]
	var w: float = m[2]
	if stary:
		return 1.0 - smoothstep(BAHNO * 0.6, BAHNO * 1.6, -d) if d < 0.5 else 1.0
	return 1.0 if d >= 0.0 else 1.0 - smoothstep(w * 0.45, w * 1.35, -d)


## Kde muze byt trava (louka.gd): > 0 za pasem bahna (stejna krivka jako bahno a breh), INF daleko od nadrzi.
func trava(x: float, z: float) -> float:
	var m := misto(x, z)
	if m.is_empty() or stary:
		return INF
	return -float(m[0]) - 0.95 * float(m[2])


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
		arr[Mesh.ARRAY_COLOR] = col
		# u brehu zjemnit 1 m -> 0,5 m: krivka brehu a okraj bahna z vrcholu po 1 m byly lomene (zuby)
		var jemne := _zjemni(arr, xf)
		v = arr[Mesh.ARRAY_VERTEX]
		col = arr[Mesh.ARRAY_COLOR]
		var zde := jemne
		for i in v.size():
			var w := xf * v[i]
			var m := misto(w.x, w.z)
			if m.is_empty():
				continue
			var b := bahno(w.x, w.z)
			if b > 0.0 and col[i].a >= 0.5:
				col[i].a = 1.0 - 0.5 * b
			var y2 := vyska(w.x, w.z, w.y)
			if absf(y2 - w.y) > 0.002:
				w.y = y2
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


## Rozdeli hrany delsi nez 0,7 m v pasu u brehu (|d| < 2,2 m) na polovinu (bez T-spoju: hrana se deli v obou
## trojuhelnicich). Atributy linearne; normaly a tecny prepocita vyhloub(). Vraci pocet novych vrcholu.
func _zjemni(arr: Array, xf: Transform3D) -> int:
	var idx = arr[Mesh.ARRAY_INDEX]
	if idx == null or stary:
		return 0
	for k in Mesh.ARRAY_MAX:
		if arr[k] != null and not k in [Mesh.ARRAY_VERTEX, Mesh.ARRAY_NORMAL, Mesh.ARRAY_TANGENT, Mesh.ARRAY_COLOR, Mesh.ARRAY_TEX_UV, Mesh.ARRAY_INDEX]:
			return 0                                    # neznamy atribut (UV2, kosti) - nedelit
	var ix: PackedInt32Array = idx
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var col: PackedColorArray = arr[Mesh.ARRAY_COLOR]
	var ma_uv: bool = arr[Mesh.ARRAY_TEX_UV] != null
	var uv: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV] if ma_uv else PackedVector2Array()
	var nv0 := v.size()
	var mid := {}                                   # klic hrany -> novy vrchol
	var nove := PackedInt32Array()
	var tri := [0, 0, 0]
	var ms := [-1, -1, -1]
	for t in range(0, ix.size(), 3):
		var deli := false
		for e in 3:
			var a := ix[t + e]
			var b := ix[t + (e + 1) % 3]
			ms[e] = -1
			tri[e] = a
			var kl := mini(a, b) * 4194304 + maxi(a, b)
			if mid.has(kl):
				ms[e] = mid[kl]
				deli = true
				continue
			if v[a].distance_squared_to(v[b]) < 0.49:
				continue
			var p := xf * ((v[a] + v[b]) * 0.5)
			var m := misto(p.x, p.z)
			if m.is_empty() or absf(float(m[0])) > 2.2:
				continue
			var q := v.size()
			v.append((v[a] + v[b]) * 0.5)
			col.append(col[a].lerp(col[b], 0.5))
			if ma_uv:
				uv.append((uv[a] + uv[b]) * 0.5)
			mid[kl] = q
			ms[e] = q
			deli = true
		if not deli:
			nove.append_array([tri[0], tri[1], tri[2]])
			continue
		var c := int(ms[0] >= 0) + int(ms[1] >= 0) + int(ms[2] >= 0)
		var r := 0
		if c == 1:
			r = 0 if ms[0] >= 0 else (1 if ms[1] >= 0 else 2)
		elif c == 2:
			r = 0 if ms[2] < 0 else (1 if ms[0] < 0 else 2)
		var a0: int = tri[r]
		var a1: int = tri[(r + 1) % 3]
		var a2: int = tri[(r + 2) % 3]
		var m0: int = ms[r]
		var m1: int = ms[(r + 1) % 3]
		var m2: int = ms[(r + 2) % 3]
		if c == 3:
			nove.append_array([a0, m0, m2, m0, a1, m1, m2, m1, a2, m0, m1, m2])
		elif c == 1:
			nove.append_array([a0, m0, a2, m0, a1, a2])
		else:
			nove.append_array([a0, m0, m1, m0, a1, m1, a0, m1, a2])
	if v.size() == nv0:
		return 0
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_COLOR] = col
	if ma_uv:
		arr[Mesh.ARRAY_TEX_UV] = uv
	arr[Mesh.ARRAY_NORMAL] = null
	arr[Mesh.ARRAY_TANGENT] = null
	arr[Mesh.ARRAY_INDEX] = nove
	return v.size() - nv0


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
