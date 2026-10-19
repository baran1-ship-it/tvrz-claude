extends RefCounted
## Koryto potoka Bystrice (radce 04:55 bod 4): hladina z osy toku (modely/reka/osa.json), ne ze dna; teren se pod
## hladinou vyhloubi na konstantni hloubku a breh je sikmy. Stejne pro hru (svet.gd: site terenu, mrizka vysek)
## i pro peceni vody (tools/reka_bake.gd) - hladina a koryto tak vzdy sedi.
##   hladina(s): z nejnizsiho terenu kolem osy, vyhlazena a nikdy nestoupa po proudu
##   profil(d): pod hladinou HLOUBKA do d = pul sirky, pak breh 1:1,5 nad hladinu; teren se jen snizuje

const HLOUBKA := 0.6           # voda nad dnem uprostred (m)
const BREH := 1.5              # sirka sikmeho brehu (m)
const NAD := 0.35              # breh konci tolik nad hladinou

var body: PackedVector2Array = PackedVector2Array()    # osa (x, z)
var hladiny: PackedFloat32Array = PackedFloat32Array()
var sirky: PackedFloat32Array = PackedFloat32Array()   # pul sirky vody
var _mriz := {}                                        # bunka 16 m -> [indexy useku]


## vyska: Callable(x, z) -> vyska terenu PRED vyhloubenim
func priprav(vyska: Callable) -> bool:
	if not FileAccess.file_exists("res://modely/reka/osa.json"):
		return false
	var osa: Array = JSON.parse_string(FileAccess.get_file_as_string("res://modely/reka/osa.json"))
	for p: Array in osa:
		body.append(Vector2(p[0], p[1]))
	var n := body.size()
	var dno := PackedFloat32Array()
	dno.resize(n)
	var ns := FastNoiseLite.new()
	ns.seed = 77
	ns.frequency = 0.02
	sirky.resize(n)
	for k in n:
		var a := body[maxi(0, k - 1)]
		var c := body[mini(n - 1, k + 1)]
		var nrm := (c - a).normalized().orthogonal()
		var m := INF
		for o: float in [-3.0, -1.5, 0.0, 1.5, 3.0]:
			var q := body[k] + nrm * o
			m = minf(m, float(vyska.call(q.x, q.y)))
		dno[k] = m
		sirky[k] = 2.0 + 0.8 * (ns.get_noise_2dv(body[k]) * 0.5 + 0.5)
	# vyhladit (klouzavy prumer 9 bodu) a hladina nikdy nestoupa po proudu (smer podle koncu)
	hladiny.resize(n)
	for k in n:
		var s := 0.0
		var c := 0
		for j in range(maxi(0, k - 4), mini(n, k + 5)):
			s += dno[j]
			c += 1
		hladiny[k] = s / c + 0.35
	var dolu := dno[0] > dno[n - 1]
	if dolu:
		for k in range(1, n):
			hladiny[k] = minf(hladiny[k], hladiny[k - 1])
	else:
		for k in range(n - 2, -1, -1):
			hladiny[k] = minf(hladiny[k], hladiny[k + 1])
	for k in n - 1:
		var lo := Vector2i(floori(minf(body[k].x, body[k + 1].x) / 16.0) - 1, floori(minf(body[k].y, body[k + 1].y) / 16.0) - 1)
		var hi := Vector2i(floori(maxf(body[k].x, body[k + 1].x) / 16.0) + 1, floori(maxf(body[k].y, body[k + 1].y) / 16.0) + 1)
		for i in range(lo.x, hi.x + 1):
			for j in range(lo.y, hi.y + 1):
				var cc := Vector2i(i, j)
				if not _mriz.has(cc):
					_mriz[cc] = []
				_mriz[cc].append(k)
	return true


## [vzdalenost od osy, hladina, pul sirky] nebo [] daleko (> 12 m)
func blizko(x: float, z: float) -> Array:
	var cc := Vector2i(floori(x / 16.0), floori(z / 16.0))
	if not _mriz.has(cc):
		return []
	var p := Vector2(x, z)
	var best := INF
	var out := []
	for k: int in _mriz[cc]:
		var a := body[k]
		var b := body[k + 1]
		var ab := b - a
		var t := clampf((p - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
		var d := p.distance_to(a + ab * t)
		if d < best:
			best = d
			out = [d, lerpf(hladiny[k], hladiny[k + 1], t), lerpf(sirky[k], sirky[k + 1], t)]
	return out if best < 12.0 else []


## Nejvyssi povolena vyska terenu v bode (INF = bez omezeni).
func strop(x: float, z: float) -> float:
	var b := blizko(x, z)
	if b.is_empty():
		return INF
	var d: float = b[0]
	var h: float = b[1]
	var w: float = b[2]
	if d <= w:
		return h - HLOUBKA * (1.0 - 0.5 * smoothstep(w * 0.6, w, d))
	if d <= w + BREH:
		return lerpf(h - HLOUBKA * 0.5, h + NAD, (d - w) / BREH)
	return INF


## Mira dna koryta 0..1 (oblazky v zem.gdshader): koryto + 0,5 m brehu.
func dno(x: float, z: float) -> float:
	var b := blizko(x, z)
	if b.is_empty():
		return 0.0
	return 1.0 - smoothstep(float(b[2]) + 0.3, float(b[2]) + 1.0, float(b[0]))


## Vyhloubit sit (MeshInstance3D teren): vrcholy jen dolu; COLOR.a = 1 - dno (oblazky ve shaderu).
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
		for i in v.size():
			var w := xf * v[i]
			var st := strop(w.x, w.z)
			if st < w.y:
				w.y = st
				v[i] = inv * w
				zmen += 1
			var dd := dno(w.x, w.z)
			if dd > 0.0:
				col[i].a = 1.0 - dd
		arr[Mesh.ARRAY_VERTEX] = v
		arr[Mesh.ARRAY_COLOR] = col
		arr[Mesh.ARRAY_NORMAL] = null
		arr[Mesh.ARRAY_TANGENT] = null
		var st2 := SurfaceTool.new()
		st2.create_from_arrays(arr)
		st2.generate_normals()
		if arr[Mesh.ARRAY_TEX_UV] != null:
			st2.generate_tangents()
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, st2.commit_to_arrays())
		nove.surface_set_material(s, am.surface_get_material(s))
		nove.surface_set_name(s, am.surface_get_name(s))
	if zmen > 0:
		mi.mesh = nove
	return zmen
