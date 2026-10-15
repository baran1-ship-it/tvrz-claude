extends Node3D
## Zkusebni misto u mostu pres Bystrici: krajina "plna jako v realu" - koberec travy, ostruvky divoke travy,
## kvety v barevnych skupinkach, lem vysoke travy a plevele podel cesty, rakos a orobinec podel potoka,
## kameny a vetve na brehu, okraj lesa s kerovym patrem a kapradim. Generuje se za behu (zadny export sveta),
## jen kdyz je hrac blizko. Po odladeni na tabletu se postup prenese do cele krajiny.

const STRED := Vector2(245.0, 592.0)
const R := 75.0
const BUNKA := 12.0
const LES := Vector2(212.0, 560.0)           # stred okraje lesa (na strani od cesty)
const LES_R := 30.0

var main: Node
var hustota := 1.0                            # 1 = plna; nastavi se podle kvality grafiky
var _g := {}
var _ys: PackedByteArray
var _ms: PackedByteArray
var _rng := RandomNumberGenerator.new()
var _sum := FastNoiseLite.new()
var _sum2 := FastNoiseLite.new()
var _meshes := {}                             # druh -> [Mesh] (varianty) a jejich vyska
var _vysky := {}
var _bunky := {}                              # [druh, varianta, Vector2i] -> Array[Transform3D]
var _dosah := {}                              # druh -> viditelnost (m)
var _postaveno := false
var _root: Node3D
var _kvety: Array = []                        # site kvetu podle barvy
var _trsy: Array = []                         # trsy ze stebel: 0 nizky, 1 stredni, 2 vysoky s klasy, 3 susy


func setup(p_main: Node) -> void:
	main = p_main
	process_mode = Node.PROCESS_MODE_ALWAYS
	hustota = [0.5, 0.75, 1.0][int(main.quality)]
	_g = main.svet.data.get("trava_kraj", {})
	if _g.is_empty():
		return
	_ys = Marshalls.base64_to_raw(String(_g["y"]))
	_ms = Marshalls.base64_to_raw(String(_g["m"]))
	_sum.seed = 1393
	_sum.frequency = 0.045
	_sum2.seed = 77
	_sum2.frequency = 0.16


func _process(_dt: float) -> void:
	if main == null or main.player == null or _g.is_empty():
		return
	var p: Vector3 = main.player.global_position
	var d := Vector2(p.x, p.z).distance_to(STRED)
	if not _postaveno and d < 260.0:
		_postav()
	elif _postaveno and d > 420.0:
		_root.queue_free()
		_root = null
		_postaveno = false


# ------------------------------------------------------------------ teren a misto

## (hustota travy 0..1, vyska terenu) z mrizky 2 m (stejna jako trava.gd)
func _vzorek(px: float, pz: float) -> Vector2:
	var fx := (px - float(_g["x0"])) / float(_g["k"])
	var fz := (pz - float(_g["z0"])) / float(_g["k"])
	var nx := int(_g["nx"])
	var i := floori(fx)
	var j := floori(fz)
	if i < 0 or j < 0 or i >= nx - 1 or j >= int(_g["nz"]) - 1:
		return Vector2(0.0, 0.0)
	fx -= i
	fz -= j
	var a0 := j * nx + i
	var m := lerpf(lerpf(_ms[a0], _ms[a0 + 1], fx), lerpf(_ms[a0 + nx], _ms[a0 + nx + 1], fx), fz) / 255.0
	var h0 := _ys.decode_s16(a0 * 2)
	var h1 := _ys.decode_s16((a0 + 1) * 2)
	var h2 := _ys.decode_s16((a0 + nx) * 2)
	var h3 := _ys.decode_s16((a0 + nx + 1) * 2)
	return Vector2(m, lerpf(lerpf(h0, h1, fx), lerpf(h2, h3, fx), fz) / 100.0)


func _reka(px: float, pz: float) -> float:
	var q := Vector2(px, pz)
	var reka: Array = preload("res://scripts/ruchy.gd").REKA
	var bd := 1e9
	for i in reka.size() - 1:
		var a: Vector2 = reka[i]
		if a.distance_to(q) > 120.0:
			continue
		var b: Vector2 = reka[i + 1]
		var ab := b - a
		var t := clampf((q - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
		bd = minf(bd, (a + ab * t).distance_to(q))
	return bd


# ------------------------------------------------------------------ modely

func _druh(kind: String) -> Array:
	if _meshes.has(kind):
		return _meshes[kind]
	var arr: Array = []
	var path: String = main.svet.MOD + "rostliny/%s.glb" % kind
	if ResourceLoader.exists(path):
		var inst: Node = (load(path) as PackedScene).instantiate()
		for n in inst.find_children("*", "MeshInstance3D", true, false):
			var mesh: Mesh = (n as MeshInstance3D).mesh
			if kind == "divoka_trava":
				mesh = mesh.duplicate()
				for s in mesh.get_surface_count():
					var sm := mesh.surface_get_material(s)
					var nm := sm.resource_name if sm else ""
					mesh.surface_set_material(s, main.svet.material(nm if nm != "" else "trava_divoka"))
			arr.append(mesh)
		inst.free()
	_meshes[kind] = arr
	var h := 1.0
	if not arr.is_empty():
		h = maxf(0.05, (arr[0] as Mesh).get_aabb().size.y)
	_vysky[kind] = h
	return arr


## Rostlinu na misto (vyska v m), do bunky podle polohy; dosah = do kolika metru je videt.
func _dej(kind: String, x: float, z: float, vyska: float, dosah: float, y_off := 0.0, sklon := 0.0) -> void:
	var arr := _druh(kind)
	if arr.is_empty():
		return
	var v := _vzorek(x, z)
	var var_i := _rng.randi() % arr.size()
	var k := vyska / float(_vysky[kind])
	var b := Basis(Vector3.UP, _rng.randf() * TAU)
	if sklon > 0.0:
		b = Basis(Vector3(_rng.randf() - 0.5, 0, _rng.randf() - 0.5).normalized(), _rng.randf() * sklon) * b
	var xf := Transform3D(b.scaled(Vector3(k, k * _rng.randf_range(0.85, 1.15), k)), Vector3(x, v.y - 0.04 + y_off, z))
	var key := [kind, var_i, Vector2i(floori(x / BUNKA), floori(z / BUNKA))]
	if not _bunky.has(key):
		_bunky[key] = []
	_bunky[key].append(xf)
	_dosah[kind] = dosah


# ------------------------------------------------------------------ kvety (vlastni lehke karty)

func _kvet_mesh(barva: Color, stred: Color, seed: int) -> Mesh:
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var r := RandomNumberGenerator.new()
	r.seed = seed
	var zelena := Color(0.25, 0.42, 0.13)
	for k in 9:
		var bx := r.randf_range(12, n - 12)
		var top := r.randf_range(8, n * 0.55)
		# stonek
		for y in range(int(top), n):
			var x := bx + sin(y * 0.05 + k) * 2.0
			for dx in range(-1, 2):
				img.set_pixel(clampi(int(x) + dx, 0, n - 1), y, zelena * (0.8 + 0.2 * r.randf()))
		# lisky
		for q in 3:
			var ly := r.randf_range(top + 15, n - 4)
			for t in 10:
				var lx := bx + (t if q % 2 == 0 else -t)
				img.set_pixel(clampi(int(lx), 0, n - 1), clampi(int(ly - t * 0.5), 0, n - 1), zelena)
		# kvet: kolecko okvetnich listku a stred
		var rad := r.randf_range(4.0, 7.0)
		for y in range(-8, 9):
			for x in range(-8, 9):
				var d := Vector2(x, y).length()
				if d < rad:
					var c := stred if d < rad * 0.35 else barva * r.randf_range(0.85, 1.1)
					c.a = 1.0
					img.set_pixel(clampi(int(bx) + x, 0, n - 1), clampi(int(top) + y, 0, n - 1), c)
	img.generate_mipmaps()
	var tex := ImageTexture.create_from_image(img)
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = tex
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.5
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.roughness = 0.9
	mat.backlight_enabled = true
	mat.backlight = Color(0.25, 0.25, 0.15)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for q in 2:
		var ang := PI * q / 2.0 + 0.3
		var tg := Vector3(cos(ang), 0, sin(ang)) * 0.22
		var up := Vector3(0, 0.42, 0)
		var pts := [-tg, tg, tg + up, -tg + up]
		var uvs := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]
		for i: int in [0, 1, 2, 0, 2, 3]:
			st.set_uv(uvs[i])
			st.set_normal(Vector3.UP)
			st.add_vertex(pts[i])
	var mesh := st.commit()
	mesh.surface_set_material(0, mat)
	return mesh


# ------------------------------------------------------------------ trsy travy ze stebel

func _trs_mesh(typ: int, seed: int) -> Mesh:
	var r := RandomNumberGenerator.new()
	r.seed = seed
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# 4 = trs pro stredni vzdalenost: malo sirokych stebel (zdalky stejny dojem, zlomek trojuhelniku)
	var n: int = [20, 16, 11, 13, 26][typ]
	var hmin: float = [0.18, 0.35, 0.55, 0.3, 0.35][typ]
	var hmax: float = [0.4, 0.7, 1.05, 0.6, 0.75][typ]
	# barvy podle srovnani s KCD2: sytejsi, tmavsi a chladnejsi zelena (ne zluta)
	var pata := Color(0.04, 0.08, 0.02)
	var spicky := [Color(0.2, 0.36, 0.09), Color(0.26, 0.42, 0.11), Color(0.4, 0.44, 0.16), Color(0.18, 0.33, 0.13), Color(0.55, 0.5, 0.28)]
	for i in n:
		var a := r.randf() * TAU
		var rr := r.randf() * (0.45 if typ == 4 else 0.12)
		var base := Vector3(cos(a) * rr, 0.0, sin(a) * rr)
		var h := r.randf_range(hmin, hmax)
		var smer := Vector3(cos(a), 0, sin(a)) * r.randf_range(0.15, 0.55) + Vector3(r.randf() - 0.5, 0, r.randf() - 0.5) * 0.3
		var w := r.randf_range(0.012, 0.022) * (1.4 if typ == 0 else (1.7 if typ == 4 else 1.0))
		var bok := Vector3(-smer.z, 0, smer.x).normalized() if smer.length() > 0.01 else Vector3.RIGHT
		var tip: Color
		if typ == 3:
			tip = spicky[4] if r.randf() < 0.7 else spicky[2]
		else:
			tip = spicky[r.randi() % 4] if r.randf() < 0.8 else spicky[2]
		tip = tip * r.randf_range(0.85, 1.15)
		var segs := 2 if typ == 4 else 3
		var ohyb := r.randf_range(0.4, 1.6) if typ != 2 else r.randf_range(0.1, 0.7)
		var pts: Array = []
		for k in segs + 1:
			var t := float(k) / segs
			# stebla se ohybaji a previsaji do stran (mekky koberec, ne obili)
			var p := base + Vector3(0, h * t * (1.0 - 0.38 * t * ohyb), 0) + smer * h * t * t * (0.6 + ohyb)
			var sirka := w * (1.0 - t * 0.92)
			pts.append([p - bok * sirka, p + bok * sirka, t])
		for k in segs:
			var a0: Array = pts[k]
			var a1: Array = pts[k + 1]
			var nrm := (bok.cross(((a1[0] as Vector3) - (a0[0] as Vector3)).normalized())).normalized()
			for q: Array in [[a0, 0], [a0, 1], [a1, 1], [a0, 0], [a1, 1], [a1, 0]]:
				var pp: Array = q[0]
				var tt: float = pp[2]
				st.set_color(pata.lerp(tip, pow(tt, 0.7)))
				st.set_uv(Vector2(q[1], tt))
				st.set_normal(nrm)
				st.add_vertex(pp[q[1]])
	if typ == 2:
		# klasy (lipnice, psarka): tenke stonky se zrnitou hlavou
		for i in 2:
			var a := r.randf() * TAU
			var b := Vector3(cos(a), 0, sin(a)) * r.randf() * 0.08
			var h := r.randf_range(0.8, 1.25)
			var top := b + Vector3(cos(a) * 0.12, h, sin(a) * 0.12)
			var bok := Vector3(-sin(a), 0, cos(a))
			var c1 := Color(0.24, 0.32, 0.12)
			var c2 := Color(0.5, 0.46, 0.3)
			for q: Array in [[b - bok * 0.004, 0.0, c1], [b + bok * 0.004, 0.0, c1], [top + bok * 0.004, 1.0, c1],
					[b - bok * 0.004, 0.0, c1], [top + bok * 0.004, 1.0, c1], [top - bok * 0.004, 1.0, c1]]:
				st.set_color(q[2]); st.set_uv(Vector2(0, q[1])); st.set_normal(Vector3.UP); st.add_vertex(q[0])
			var hl := top - Vector3(0, 0.12, 0)
			for q: Array in [[hl - bok * 0.018, c2], [hl + bok * 0.018, c2], [top + bok * 0.006, c2],
					[hl - bok * 0.018, c2], [top + bok * 0.006, c2], [top - bok * 0.006, c2]]:
				st.set_color(q[1]); st.set_uv(Vector2(0, 1.0)); st.set_normal(Vector3.UP); st.add_vertex(q[0])
	var mesh := st.commit()
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://shaders/stebla.gdshader")
	mesh.surface_set_material(0, mat)
	return mesh


func _ruzice_mesh(seed: int, barva: Color, list_d: float, n: int) -> Mesh:
	# nizka bylina: ruzice ovalnych listu tesne nad zemi (jitrocel, jetel, smetanka bez kvetu)
	var r := RandomNumberGenerator.new()
	r.seed = seed
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in n:
		var a := TAU * i / n + r.randf_range(-0.3, 0.3)
		var d := Vector3(cos(a), 0, sin(a))
		var bok := Vector3(-d.z, 0, d.x)
		var L := list_d * r.randf_range(0.7, 1.2)
		var zv := r.randf_range(0.02, 0.09)
		var c := barva * r.randf_range(0.85, 1.12)
		var tip := d * L + Vector3(0, zv, 0)
		var mid := d * L * 0.5 + Vector3(0, zv * 0.8 + 0.01, 0)
		var w := L * 0.32
		for q: Array in [[Vector3(0, 0.01, 0), 0.0], [mid + bok * w, 0.5], [tip, 1.0], [Vector3(0, 0.01, 0), 0.0], [tip, 1.0], [mid - bok * w, 0.5]]:
			st.set_color(c * (0.6 + 0.4 * q[1]))
			st.set_uv(Vector2(0, 0.3 + 0.7 * q[1]))
			st.set_normal(Vector3.UP)
			st.add_vertex(q[0])
	var mesh := st.commit()
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://shaders/stebla.gdshader")
	mat.set_shader_parameter("vitr", 0.15)
	mesh.surface_set_material(0, mat)
	return mesh


# ------------------------------------------------------------------ stavba

func _postav() -> void:
	var t0 := Time.get_ticks_msec()
	_postaveno = true
	_bunky.clear()
	_rng.seed = 1393
	_root = Node3D.new()
	_root.name = "Zkusebni"
	add_child(_root)
	if _kvety.is_empty():
		for c: Array in [[Color(1.0, 0.85, 0.15), Color(0.9, 0.55, 0.05)], [Color(0.98, 0.98, 0.93), Color(1.0, 0.85, 0.2)],
				[Color(0.95, 0.55, 0.75), Color(0.75, 0.3, 0.45)], [Color(0.6, 0.45, 0.9), Color(0.95, 0.9, 0.5)]]:
			_kvety.append(_kvet_mesh(c[0], c[1], _kvety.size() * 31 + 5))
	if _trsy.is_empty():
		for t in 5:
			_trsy.append(_trs_mesh(t, 11 + t * 7))
		_trsy.append(_ruzice_mesh(3, Color(0.17, 0.32, 0.1), 0.14, 9))     # 5 jitrocel
		_trsy.append(_ruzice_mesh(4, Color(0.2, 0.38, 0.13), 0.07, 14))    # 6 jetel
		_trsy.append(_ruzice_mesh(5, Color(0.24, 0.36, 0.1), 0.11, 11))    # 7 smetanka (listy)
	var H := hustota
	# 1) koberec: trsy travy (lehke karty) hustě, mezi nimi ostruvky divoke travy a vyssi travy
	var krok := 0.42 / sqrt(H)
	var x := STRED.x - R
	while x < STRED.x + R:
		var z := STRED.y - R
		while z < STRED.y + R:
			var px := x + _rng.randf_range(-0.45, 0.45) * krok
			var pz := z + _rng.randf_range(-0.45, 0.45) * krok
			z += krok
			if Vector2(px, pz).distance_to(STRED) > R:
				continue
			var v := _vzorek(px, pz)
			var dr := _reka(px, pz)
			if v.x < 0.12 or dr < 2.6:
				continue
			var n1 := _sum.get_noise_2d(px, pz) * 0.5 + 0.5
			if _rng.randf() > v.x * 1.15:
				continue
			_dej_trs(px, pz, v, n1)
			if _rng.randf() < 0.22:
				var bx := px + _rng.randf_range(-0.2, 0.2)
				var bz := pz + _rng.randf_range(-0.2, 0.2)
				var s := _rng.randf_range(0.8, 1.4)
				var xf := Transform3D(Basis(Vector3.UP, _rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(bx, v.y - 0.01, bz))
				var key := ["_trs", 5 + _rng.randi() % 3, Vector2i(floori(bx / BUNKA), floori(bz / BUNKA))]
				if not _bunky.has(key):
					_bunky[key] = []
				_bunky[key].append(xf)
		x += krok
	# 1b) stredni vzdalenost (22-110 m): siroke trsy hustě az k obzoru zkusebni oblasti (zblizka neviditelne)
	var k3 := 0.8 / sqrt(H)
	var RD := 150.0
	x = STRED.x - RD
	while x < STRED.x + RD:
		var z := STRED.y - RD
		while z < STRED.y + RD:
			var px := x + _rng.randf_range(-1.5, 1.5) * k3
			var pz := z + _rng.randf_range(-1.5, 1.5) * k3
			z += k3
			if Vector2(px, pz).distance_to(STRED) > RD:
				continue
			var v := _vzorek(px, pz)
			if v.x < 0.15 or _rng.randf() > v.x * 1.1 or _reka(px, pz) < 2.6:
				continue
			var s := _rng.randf_range(0.8, 1.3) * lerpf(0.8, 1.2, _sum.get_noise_2d(px, pz) * 0.5 + 0.5)
			var xf := Transform3D(Basis(Vector3.UP, _rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(px, v.y - 0.03, pz))
			var key := ["_trs_d", 4, Vector2i(floori(px / BUNKA), floori(pz / BUNKA))]
			if not _bunky.has(key):
				_bunky[key] = []
			_bunky[key].append(xf)
		x += k3
	# 2) ostruvky: divoka trava a vyssi trava v zaplatach, jinde rideji
	var k2 := 1.6 / sqrt(H)
	x = STRED.x - R
	while x < STRED.x + R:
		var z := STRED.y - R
		while z < STRED.y + R:
			var px := x + _rng.randf_range(-0.5, 0.5) * k2
			var pz := z + _rng.randf_range(-0.5, 0.5) * k2
			z += k2
			if Vector2(px, pz).distance_to(STRED) > R:
				continue
			var v := _vzorek(px, pz)
			var dr := _reka(px, pz)
			if v.x < 0.1 or dr < 2.6:
				continue
			var n1 := _sum.get_noise_2d(px, pz) * 0.5 + 0.5
			var okraj := v.x < 0.5          # lem cesty: vysoka trava a plevel
			if okraj:
				_dej("divoka_trava", px, pz, _rng.randf_range(0.7, 1.15), 40.0)
				if _rng.randf() < 0.25:
					_dej("weed_plant_02", px + _rng.randf_range(-0.5, 0.5), pz + _rng.randf_range(-0.5, 0.5), _rng.randf_range(0.5, 0.9), 35.0)
				if _rng.randf() < 0.12:
					_dej("nettle_plant", px, pz, _rng.randf_range(0.5, 0.9), 35.0)
			elif n1 > 0.48 or _rng.randf() < 0.25:
				_dej("divoka_trava" if _rng.randf() < 0.65 else "grass_medium_02", px, pz, _rng.randf_range(0.45, 0.85) * (0.8 + n1 * 0.6), 38.0)
		x += k2
	# 3) kvety ve skupinkach (barva na skupinku), kopretiny a pampelisky na slunci, zvonky u lesa
	for _i in int(120 * H):
		var a := _rng.randf() * TAU
		var d := sqrt(_rng.randf()) * R
		var cx := STRED.x + cos(a) * d
		var cz := STRED.y + sin(a) * d
		var v := _vzorek(cx, cz)
		if v.x < 0.4 or _reka(cx, cz) < 4.0:
			continue
		var mi := _rng.randi() % _kvety.size()
		var nn := _rng.randi_range(18, 50)
		var rr := _rng.randf_range(0.8, 2.2)
		for _j in nn:
			var aa := _rng.randf() * TAU
			var dd := sqrt(_rng.randf()) * rr
			var px := cx + cos(aa) * dd
			var pz := cz + sin(aa) * dd
			var vv := _vzorek(px, pz)
			var s := _rng.randf_range(1.1, 1.9)
			var xf := Transform3D(Basis(Vector3.UP, _rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(px, vv.y - 0.03, pz))
			var key := ["_kvet", mi, Vector2i(floori(px / BUNKA), floori(pz / BUNKA))]
			if not _bunky.has(key):
				_bunky[key] = []
			_bunky[key].append(xf)
	_dosah["_kvet"] = 34.0
	# 4) potok: hustý rakos a orobinec v pasech, kameny a naplavene vetve na brehu
	x = STRED.x - R
	while x < STRED.x + R:
		var z := STRED.y - R
		while z < STRED.y + R:
			var px := x + _rng.randf_range(-0.6, 0.6)
			var pz := z + _rng.randf_range(-0.6, 0.6)
			z += 0.9
			if Vector2(px, pz).distance_to(STRED) > R:
				continue
			var dr := _reka(px, pz)
			if dr < 2.0 or dr > 6.5:
				continue
			var n2 := _sum2.get_noise_2d(px, pz) * 0.5 + 0.5
			if dr < 4.5 and n2 > 0.4:
				var kind: String = ["rakos_1", "rakos_2", "orobinec_1", "orobinec_2"][int(n2 * 7.0) % 4]
				_dej(kind, px, pz, _rng.randf_range(1.4, 2.4), 70.0)
			elif dr < 3.8 and _rng.randf() < 0.18:
				var kk: String = ["kamen_maly_1", "kamen_maly_2", "kamen_maly_3", "kamen_maly_5", "kamen_zula_2"][_rng.randi() % 5]
				_dej(kk, px, pz, _rng.randf_range(0.12, 0.45), 45.0, -0.05)
			elif _rng.randf() < 0.35:
				_dej("divoka_trava", px, pz, _rng.randf_range(0.8, 1.3), 45.0)
			if _rng.randf() < 0.02:
				_dej("dry_branches_medium_01", px, pz, _rng.randf_range(0.2, 0.4), 40.0)
		x += 0.9
	# 5) okraj lesa: stromy, kerove patro (bez, sipek, ker, mlade brizy a smrcky), kapradi a trava pod nimi
	var stromy := ["dub_stredni", "buk_stredni", "lipa_stredni", "buk_stredni"]
	# stena lesa za okrajem: smrky a brizy (lehke), do hloubky
	for _i in int(160 * H):
		var a := _rng.randf() * TAU
		var d := LES_R + _rng.randf() * 45.0
		var px := LES.x + cos(a) * d
		var pz := LES.y + sin(a) * d
		if _vzorek(px, pz).x < 0.25 or _reka(px, pz) < 9.0 or Vector2(px, pz).distance_to(STRED) < 30.0:
			continue
		if _rng.randf() < 0.6:
			_dej("smrk", px, pz, _rng.randf_range(13.0, 22.0), 600.0, -0.1)
		else:
			_dej("briza", px, pz, _rng.randf_range(10.0, 16.0), 600.0, -0.1)
	for _i in 24:
		var a := _rng.randf() * TAU
		var d := sqrt(_rng.randf()) * LES_R
		var px := LES.x + cos(a) * d
		var pz := LES.y + sin(a) * d
		if _vzorek(px, pz).x < 0.3 or _reka(px, pz) < 8.0:
			continue
		_dej(stromy[_rng.randi() % stromy.size()], px, pz, _rng.randf_range(12.0, 17.0), 400.0, -0.1)
	for _i in int(320 * H):
		var a := _rng.randf() * TAU
		var d := sqrt(_rng.randf()) * (LES_R + 6.0)
		var px := LES.x + cos(a) * d
		var pz := LES.y + sin(a) * d
		if _vzorek(px, pz).x < 0.3 or _reka(px, pz) < 5.0:
			continue
		var c := _rng.randf()
		if c < 0.07:
			_dej(["bez_cerny_1", "bez_cerny_2", "bez_cerny_3"][_rng.randi() % 3], px, pz, _rng.randf_range(2.2, 3.6), 120.0)
		elif c < 0.17:
			_dej("shrub_02", px, pz, _rng.randf_range(1.2, 2.4), 90.0)
		elif c < 0.3:
			_dej("sipek", px, pz, _rng.randf_range(1.0, 1.8), 80.0)
		elif c < 0.4:
			_dej("briza", px, pz, _rng.randf_range(2.0, 4.5), 120.0)
		elif c < 0.47:
			_dej("smrk", px, pz, _rng.randf_range(1.2, 3.0), 120.0)
		elif c < 0.75:
			_dej(["kapradi_1", "kapradi_2", "kapradi_3"][_rng.randi() % 3], px, pz, _rng.randf_range(0.6, 1.0), 45.0)
		else:
			_dej("fern_02", px, pz, _rng.randf_range(0.6, 1.0), 45.0)
	# sitě
	var n_inst := 0
	for key: Array in _bunky:
		var kind: String = key[0]
		var mesh: Mesh
		if kind == "_kvet":
			mesh = _kvety[key[1]]
		elif kind == "_trs" or kind == "_trs_d":
			mesh = _trsy[key[1]]
		else:
			mesh = _druh(kind)[key[1]]
		var list: Array = _bunky[key]
		var c: Vector2i = key[2]
		var cen := Vector3((c.x + 0.5) * BUNKA, 0.0, (c.y + 0.5) * BUNKA)
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = list.size()
		for i in list.size():
			var t: Transform3D = list[i]
			t.origin -= cen
			mm.set_instance_transform(i, t)
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.position = cen
		var dos: float = _dosah.get(kind, 40.0)
		if kind == "_trs_d":
			dos = 115.0
			mmi.visibility_range_begin = 22.0
			mmi.visibility_range_begin_margin = 5.0
		mmi.visibility_range_end = dos
		mmi.visibility_range_end_margin = dos * 0.15
		mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		var stin := dos > 60.0 or kind in ["divoka_trava", "rakos_1", "rakos_2", "orobinec_1", "orobinec_2"]
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if stin and main.quality > 0 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_root.add_child(mmi)
		n_inst += list.size()
	_dosah["_trs"] = 26.0
	print("zkusebni misto: %d instanci, %d bunek, %d ms" % [n_inst, _bunky.size(), Time.get_ticks_msec() - t0])


func _dej_trs(px: float, pz: float, v: Vector2, n1: float) -> void:
	var s := _rng.randf_range(0.75, 1.25) * lerpf(0.85, 1.15, v.x)
	var xf := Transform3D(Basis(Vector3.UP, _rng.randf() * TAU).scaled(Vector3(s, s * _rng.randf_range(0.85, 1.25), s)), Vector3(px, v.y - 0.03, pz))
	# druh trsu podle zaplat: v nizinach a na slunci nizka hustá, v zaplatach vysoka s klasy, misty sucha
	var n2 := _sum2.get_noise_2d(px, pz) * 0.5 + 0.5
	var typ := 0 if n1 < 0.45 else (1 if n1 < 0.72 else 2)
	if n2 > 0.72:
		typ = 3
	if _rng.randf() < 0.25:
		typ = _rng.randi() % 3
	var key := ["_trs", typ, Vector2i(floori(px / BUNKA), floori(pz / BUNKA))]
	if not _bunky.has(key):
		_bunky[key] = []
	_bunky[key].append(xf)
	_dosah["_trs"] = 26.0
