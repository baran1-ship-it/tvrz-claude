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
##   Zarez se uzavre do PAS od osy (jemna sit Teren_reka siaha ~18 m): kde je potok hluboko pod okolim, je stena strmejsi
##     (skalnaty kanon) - za pasem by hruba sit Teren_okoli (vrcholy po 8 m) delala skviry a zubate steny (0.55: propad
##     hrace u mostu, steny ze zubu na fotkach). Hruba sit pod jemnou se stahne niz (POD_JEMNOU), okraj jemne site ma
##     svislou sukni dolu (sukne()).

const HLOUBKA := 0.6           # voda nad dnem uprostred (m), podel toku +-20 %
const PRAH := 0.6              # od kraje vody do vysky hladiny + 5 cm (pod vodou to schova hladina z peceni)
const DOSAH := 34.0            # nejdal od osy, kam se koryto vyhodnocuje (rostliny, maska)
const PAS := 17.0              # zarez konci nejpozdeji tady (uvnitr jemne site Teren_reka)
const POD_JEMNOU := 2.5        # hruba sit v pasu jemne o tolik niz (nikdy neprorazi jemnou)
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
var hrana_l: PackedFloat32Array = PackedFloat32Array() # puvodni teren ve vzdalenosti PAS vlevo / vpravo od osy
var hrana_p: PackedFloat32Array = PackedFloat32Array()


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
	hrana_l.resize(n)
	hrana_p.resize(n)
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
		hrana_l[k] = float(vyska.call(body[k].x + nrm.x * PAS, body[k].y + nrm.y * PAS))
		hrana_p[k] = float(vyska.call(body[k].x - nrm.x * PAS, body[k].y - nrm.y * PAS))
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
			var hr := lerpf(hrana_l[k], hrana_l[k + 1], t) if strana > 0.0 else lerpf(hrana_p[k], hrana_p[k + 1], t)
			out = [d, lerpf(hladiny[k], hladiny[k + 1], t), lerpf(sirky[k], sirky[k + 1], t),
					clampf(strana * kr / KRIVOST, -1.0, 1.0), lerpf(hloubky[k], hloubky[k + 1], t), lerpf(sklony[k], sklony[k + 1], t), hr]
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
	y += (_sum.get_noise_2d(x, z) * 0.45 * smoothstep(0.0, 2.0, e) if sum else 0.0)
	# do PAS musi zarez potkat puvodni teren: primka od kraje vody k terenu na hranici pasu (strmejsi = skalnata stena)
	var e_pas := maxf(PAS - w - PRAH - jesep, 1.0)
	var rampa := h + 0.05 + (float(b[6]) - h - 0.05) * clampf((d - w - PRAH - jesep) / e_pas, 0.0, 1.0)
	return maxf(y, rampa) if d < PAS else INF


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
## Bunky 2 m pokryte jemnou siti (Teren_reka, Teren_most): jen tam se hruba sit zapusti pod jemnou. Mimo ne
## (breh za koncem Teren_most, test prochod 0.56) by hruba lezela 2,5 m pod terenem - schod do sukne mostu.
var jemne := {}


func pokryj(mi: MeshInstance3D) -> void:
	if mi.mesh == null:
		return
	var xf := mi.global_transform
	var f := mi.mesh.get_faces()
	for i in range(0, f.size(), 3):
		var a := xf * f[i]
		var b := xf * f[i + 1]
		var c := xf * f[i + 2]
		var lo := Vector2(minf(a.x, minf(b.x, c.x)), minf(a.z, minf(b.z, c.z)))
		var hi := Vector2(maxf(a.x, maxf(b.x, c.x)), maxf(a.z, maxf(b.z, c.z)))
		# bunka, do ktere padne vrchol nebo jejiz stred lezi v trojuhelniku (obdelnik obalu byl moc stedry:
		# dlouhe trojuhelniky kolem vyrezu Teren_most oznacily breh, kde jemna sit neni)
		var a2 := Vector2(a.x, a.z)
		var b2 := Vector2(b.x, b.z)
		var c2 := Vector2(c.x, c.z)
		for q: Vector2 in [a2, b2, c2]:
			jemne[Vector2i(floori(q.x / 2.0), floori(q.y / 2.0))] = true
		for jx in range(floori(lo.x / 2.0), floori(hi.x / 2.0) + 1):
			for jz in range(floori(lo.y / 2.0), floori(hi.y / 2.0) + 1):
				if Geometry2D.point_is_inside_triangle(Vector2(jx * 2.0 + 1.0, jz * 2.0 + 1.0), a2, b2, c2):
					jemne[Vector2i(jx, jz)] = true


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
		var hruba := not (String(mi.name) == "Teren_reka" or String(mi.name) == "Teren_most")
		for i in v.size():
			var w := xf * v[i]
			var st := strop(w.x, w.z)
			if st < w.y:
				# hruba sit v pasu jemne: niz, at mezi svymi ridkymi vrcholy neprorazi stenu kanonu
				var b2 := blizko(w.x, w.z)
				if hruba and not b2.is_empty() and float(b2[0]) < PAS + 2.0 \
						and jemne.has(Vector2i(floori(w.x / 2.0), floori(w.z / 2.0))):
					st -= POD_JEMNOU
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
		if String(mi.name) == "Teren_reka" or String(mi.name) == "Teren_most":
			sukne(mi)
	return zmen


## Svisla sukne 3 m dolu po okraji site (hrany patrici jedinemu trojuhelniku), jen kde je okraj v zarezu - skviru
## k sousedni hrubsi siti nevidi oko ani hrac (sukne je bez kolize - diry zalepi svet._zaplaty).
func sukne(mi: MeshInstance3D) -> void:
	var am := mi.mesh as ArrayMesh
	var arr := am.surface_get_arrays(0)
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
	if idx.is_empty():
		for i in v.size():
			idx.append(i)
	var klic := func(q: Vector3) -> Vector3i: return Vector3i(roundi(q.x * 100.0), roundi(q.y * 100.0), roundi(q.z * 100.0))
	var hrany := {}
	for t in range(0, idx.size(), 3):
		for e in 3:
			var a: Vector3i = klic.call(v[idx[t + e]])
			var b: Vector3i = klic.call(v[idx[t + (e + 1) % 3]])
			var kk := [a, b] if a < b else [b, a]
			var hk := str(kk)
			if hrany.has(hk):
				hrany[hk] = null
			else:
				hrany[hk] = [idx[t + e], idx[t + (e + 1) % 3]]
	var xf := mi.global_transform
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 0
	for hk: String in hrany:
		var e2 = hrany[hk]
		if e2 == null:
			continue
		var a := v[e2[0]]
		var b := v[e2[1]]
		var wa := xf * a
		if blizko(wa.x, wa.z).is_empty():
			continue
		var a2 := a - Vector3(0, 3.0, 0)
		var b2 := b - Vector3(0, 3.0, 0)
		for q: Vector3 in [a, b, b2, a, b2, a2]:
			st.add_vertex(q)
		n += 1
	if n == 0:
		return
	st.generate_normals()
	st.set_material(am.surface_get_material(0))
	var sk := MeshInstance3D.new()
	sk.name = String(mi.name) + "_sukne"            # Teren*: svet.build da material zeme, kolizi ne
	sk.mesh = st.commit()
	mi.add_child(sk)
