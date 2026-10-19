extends RefCounted
## Koryto potoka Bystrice (radce 04:55 bod 4): hladina z osy toku (modely/reka/osa.json), ne ze dna; teren se pod
## hladinou vyhloubi a nad ni je zarez udoli az k puvodnimu terenu. Stejne pro hru (svet.gd: site terenu, mrizka
## vysek) i pro peceni vody (tools/reka_bake.gd) - hladina a koryto tak vzdy sedi.
##   hladina(s): z nejnizsiho terenu kolem osy, vyhlazena a nikdy nestoupa po proudu - pres hrbolaty teren tece
##     2-15 m pod okolim, proto zarez nesmi koncit kousek nad vodou (byla tam svisla stena, 0.54)
##   profil(d) jako udoli v Posazavi (zaklesle meandry, radce 17:00): pod hladinou dno, u vody kratky prah, pak svah,
##     ktery se nahore rozevira (cim hloubeji, tim sire); vnejsi (narazovy) breh zatacky strmy skalnaty ~40 st.,
##     vnitrni plochy jesep s oblazky a pak mirny svah; sklon se meni i podel toku, svah zvlneny sumem 0,4 m.
##     Teren se jen snizuje: zarez konci, kde potka puvodni teren.

const HLOUBKA := 0.6           # voda nad dnem uprostred (m), podel toku +-20 %
const PRAH := 0.6              # od kraje vody do vysky hladiny + 5 cm (pod vodou to schova hladina z peceni)
const DOSAH := 34.0            # nejdal od osy, kam zarez muze sahat (m)
const S_VNEJSI := 0.85         # sklon svahu (vyska / delka): narazovy breh zatacky ~40 st.
const S_ROVNY := 0.42          # rovny usek ~23 st.
const S_VNITRNI := 0.2         # jesep a vnitrni breh ~11 st.
const ROZEVRENI := 0.012       # kvadraticky clen: udoli se nahore rozevira (V -> neckovite)
const KRIVOST := 0.025         # krivost osy (1/m), od ktere je zatacka "plna" (polomer 40 m)

var body: PackedVector2Array = PackedVector2Array()    # osa (x, z)
var hladiny: PackedFloat32Array = PackedFloat32Array()
var sirky: PackedFloat32Array = PackedFloat32Array()   # pul sirky vody
var hloubky: PackedFloat32Array = PackedFloat32Array() # hloubka vody uprostred
var sklony: PackedFloat32Array = PackedFloat32Array()  # nasobek sklonu svahu podel toku (strida strmejsi a mirnejsi)
var krivost: PackedFloat32Array = PackedFloat32Array() # se znamenkem: > 0 zatacka doleva (stred zatacky vlevo od smeru osy)
var _mriz := {}                                        # bunka 16 m -> [indexy useku]
var _sum := FastNoiseLite.new()                        # zvlneni svahu


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
	hloubky.resize(n)
	sklony.resize(n)
	krivost.resize(n)
	var ns2 := FastNoiseLite.new()
	ns2.seed = 91
	ns2.frequency = 0.012
	_sum.seed = 13
	_sum.frequency = 0.18
	_sum.fractal_octaves = 2
	for k in n:
		var a := body[maxi(0, k - 1)]
		var c := body[mini(n - 1, k + 1)]
		var nrm := (c - a).normalized().orthogonal()
		var m := INF
		for o: float in [-3.0, -1.5, 0.0, 1.5, 3.0]:
			var q := body[k] + nrm * o
			m = minf(m, float(vyska.call(q.x, q.y)))
		dno[k] = m
		# sirka vody +-30 % a hloubka +-20 % podel toku (sum ~[-0,6; 0,6] -> x 1,6)
		sirky[k] = 2.4 * (1.0 + 0.5 * ns.get_noise_2dv(body[k]))
		hloubky[k] = HLOUBKA * (1.0 + 0.33 * ns.get_noise_2dv(body[k] * 1.7 + Vector2(40.0, 0.0)))
		sklony[k] = 1.0 + 0.5 * ns2.get_noise_2dv(body[k])
		if k > 0 and k < n - 1:
			var t1 := (body[k] - body[k - 1]).normalized()
			var t2 := (body[k + 1] - body[k]).normalized()
			krivost[k] = (t1.x * t2.y - t1.y * t2.x) / maxf(0.5 * (body[k + 1].distance_to(body[k - 1])), 0.5)
	# krivost vyhladit (+-3 body ~ 30 m): zatacka je oblouk, ne zlom jednoho bodu
	var kv := krivost.duplicate()
	for k in n:
		var s := 0.0
		var c := 0
		for j in range(maxi(0, k - 3), mini(n, k + 4)):
			s += kv[j]
			c += 1
		krivost[k] = s / c
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
	var r := ceili(DOSAH / 16.0)
	for k in n - 1:
		var lo := Vector2i(floori(minf(body[k].x, body[k + 1].x) / 16.0) - r, floori(minf(body[k].y, body[k + 1].y) / 16.0) - r)
		var hi := Vector2i(floori(maxf(body[k].x, body[k + 1].x) / 16.0) + r, floori(maxf(body[k].y, body[k + 1].y) / 16.0) + r)
		for i in range(lo.x, hi.x + 1):
			for j in range(lo.y, hi.y + 1):
				var cc := Vector2i(i, j)
				if not _mriz.has(cc):
					_mriz[cc] = []
				_mriz[cc].append(k)
	return true


## [vzdalenost od osy, hladina, pul sirky, vnitrni breh -1..1 (1 vnitrni = jesep, -1 vnejsi = narazovy), hloubka,
## nasobek sklonu] nebo [] daleko (> DOSAH)
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
			var strana := signf(ab.x * (p.y - a.y) - ab.y * (p.x - a.x))     # > 0 vlevo od smeru osy
			var kr := lerpf(krivost[k], krivost[k + 1], t)
			out = [d, lerpf(hladiny[k], hladiny[k + 1], t), lerpf(sirky[k], sirky[k + 1], t),
					clampf(strana * kr / KRIVOST, -1.0, 1.0), lerpf(hloubky[k], hloubky[k + 1], t), lerpf(sklony[k], sklony[k + 1], t)]
	return out if best < DOSAH else []


## Nejvyssi povolena vyska terenu v bode (INF = bez omezeni).
## sum = false: bez zvlneni svahu (FastNoiseLite neni pro souběžna vlakna louky).
func strop(x: float, z: float, sum := true) -> float:
	var b := blizko(x, z)
	if b.is_empty():
		return INF
	var d: float = b[0]
	var h: float = b[1]
	var w: float = b[2]
	var vn: float = b[3]
	var hl: float = b[4]
	if d <= w:
		return h - hl * (1.0 - 0.5 * smoothstep(w * 0.6, w, d))
	if d <= w + PRAH:
		return lerpf(h - hl * 0.5, h + 0.05, (d - w) / PRAH)
	# vnitrni breh: plochy jesep 0-4 m tesne nad vodou, pak svah
	var e := d - w - PRAH
	var jesep := 4.0 * maxf(vn, 0.0)
	var y := h + 0.05 + 0.03 * minf(e, jesep)
	e = maxf(e - jesep, 0.0)
	var s: float = b[5] * (lerpf(S_ROVNY, S_VNITRNI, vn) if vn > 0.0 else lerpf(S_ROVNY, S_VNEJSI, -vn))
	y += s * e + ROZEVRENI * e * e
	return y + (_sum.get_noise_2d(x, z) * 0.45 * smoothstep(0.0, 2.0, e) if sum else 0.0)


## Mira dna koryta 0..1 (oblazky v zem.gdshader): koryto + 0,5 m brehu, na vnitrnim brehu jesep az 4 m.
func dno(x: float, z: float) -> float:
	var b := blizko(x, z)
	if b.is_empty():
		return 0.0
	var j := float(b[2]) + PRAH + 4.0 * maxf(float(b[3]), 0.0)
	return 1.0 - smoothstep(j - 0.3, j + 0.6, float(b[0]))


## Sirka zarezu na jedne strane (od osy, m): kde svah koryta potka teren. o = bod osy, smer = jednotkovy vektor
## kolmo k ose; vyska = teren (pred i po vyhloubeni - ve zarezu je teren roven stropu).
func hrana(o: Vector2, smer: Vector2, w: float, vyska: Callable) -> float:
	var r := w + PRAH
	while r < DOSAH:
		var q := o + smer * r
		if strop(q.x, q.y) >= float(vyska.call(q.x, q.y)) - 0.02:
			return r
		r += 1.0
	return DOSAH


## Vyhloubit sit (MeshInstance3D teren): vrcholy jen dolu; COLOR.a = 0,5 - 0,5 * dno (oblazky ve shaderu;
## a 0,5-1 je bahno rybniku a prikopu, scripts/nadrz.gd).
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
				col[i].a = 0.5 - 0.5 * dd
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
