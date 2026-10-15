extends Node3D
## Louka v cele krajine (postup odladeny na zkusebni louce): kolem hrace se po bunkach 16 m generuje
## blizko (do ~38 m) husty koberec trsu ze stebel, byliny (jitrocel, jetel, smetanka) a kvety ve skupinkach,
## dal (do ~115 m) sirsi levne trsy, aby louka pokracovala k obzoru. Hustota z mrizek Blenderu
## (trava_kraj = krajina, trava_ves = ves). Vse deterministicke podle bunky (stejne pri navratu).
## Pasma se prekryvaji: stredni trsy stoji uz od nohou (blizke jen pridava detail), kupy travy (zelena hmota)
## zacinaji pred koncem trsu - pri chuzi nic "nevyrusta z niceho".
## LADENI VYKONU (kdyz se seka, ubirat tady): BLIZ_KROK vetsi = ridsi blizko, DAL/KUPY dosah, *_HUST hustota.

const BUNKA := 16.0
const BLIZ := 50.0                    # husty koberec stebel, byliny, kvety
const BLIZ_KROK := 0.36               # rozestup trsu blizko (m)
const DAL := 110.0                    # siroke trsy od nohou az sem
const DAL_HUST := 1.6                 # trsu na m2
const NA_SNIMEK := 3
const KUPY := [                       # kupy travy: [bunka, od, do, meritko min, max, pokryti]
	[32.0, 80.0, 280.0, 1.2, 2.0, 1.1],
	[64.0, 240.0, 650.0, 2.6, 4.2, 1.0],
]

var main: Node
var hustota := 1.0
var _mriz: Array = []                 # [{x0, z0, k, nx, nz, ys, ms}]
var _trsy: Array = []
var _kvety: Array = []
var _sum := FastNoiseLite.new()
var _sum2 := FastNoiseLite.new()
var _bliz := {}                       # Vector2i -> Node3D (nebo null)
var _dal := {}
var _kupy: Array = [{}, {}]
var _kupa: Mesh
var _player: Node3D
var _n_trsu := 0


func setup(p_main: Node) -> void:
	main = p_main
	process_mode = Node.PROCESS_MODE_ALWAYS
	_player = main.player
	hustota = [0.45, 0.7, 1.0][int(main.quality)]
	for key: String in ["trava_kraj", "trava_ves"]:
		var g: Dictionary = main.svet.data.get(key, {})
		if g.is_empty():
			continue
		_mriz.append({"x0": float(g["x0"]), "z0": float(g["z0"]), "k": float(g["k"]),
				"nx": int(g.get("nx", g.get("n", 0))), "nz": int(g.get("nz", g.get("n", 0))),
				"ys": Marshalls.base64_to_raw(String(g["y"])), "ms": Marshalls.base64_to_raw(String(g["m"]))})
	_sum.seed = 1393
	_sum.frequency = 0.045
	_sum2.seed = 77
	_sum2.frequency = 0.16
	for t in 5:
		_trsy.append(_trs_mesh(t, 11 + t * 7))
	_trsy.append(_ruzice_mesh(3, Color(0.17, 0.32, 0.1), 0.14, 9))
	_trsy.append(_ruzice_mesh(4, Color(0.2, 0.38, 0.13), 0.07, 14))
	_trsy.append(_ruzice_mesh(5, Color(0.24, 0.36, 0.1), 0.11, 11))
	for c: Array in [[Color(1.0, 0.85, 0.15), Color(0.9, 0.55, 0.05)], [Color(0.98, 0.98, 0.93), Color(1.0, 0.85, 0.2)],
			[Color(0.95, 0.55, 0.75), Color(0.75, 0.3, 0.45)], [Color(0.6, 0.45, 0.9), Color(0.95, 0.9, 0.5)]]:
		_kvety.append(_kvet_mesh(c[0], c[1], _kvety.size() * 31 + 5))
	_kupa = _kupa_mesh(41)
	print("louka: %d mrizek, hustota %.2f" % [_mriz.size(), hustota])


## (hustota 0..1, vyska) - vetsi z mrizek (ves ma vlastni)
func _vzorek(px: float, pz: float) -> Vector2:
	var best := Vector2(0.0, 0.0)
	for g: Dictionary in _mriz:
		var fx := (px - float(g["x0"])) / float(g["k"])
		var fz := (pz - float(g["z0"])) / float(g["k"])
		var nx: int = g["nx"]
		var i := floori(fx)
		var j := floori(fz)
		if i < 0 or j < 0 or i >= nx - 1 or j >= int(g["nz"]) - 1:
			continue
		fx -= i
		fz -= j
		var a0 := j * nx + i
		var ms: PackedByteArray = g["ms"]
		var ys: PackedByteArray = g["ys"]
		var m := lerpf(lerpf(ms[a0], ms[a0 + 1], fx), lerpf(ms[a0 + nx], ms[a0 + nx + 1], fx), fz) / 255.0
		if m <= best.x:
			continue
		var h0 := ys.decode_s16(a0 * 2)
		var h1 := ys.decode_s16((a0 + 1) * 2)
		var h2 := ys.decode_s16((a0 + nx) * 2)
		var h3 := ys.decode_s16((a0 + nx + 1) * 2)
		best = Vector2(m, lerpf(lerpf(h0, h1, fx), lerpf(h2, h3, fx), fz) / 100.0)
	return best


func _process(_dt: float) -> void:
	if _player == null or _mriz.is_empty() or not main.ready_done:
		return
	var p := _player.global_position
	var c0 := Vector2i(floori(p.x / BUNKA), floori(p.z / BUNKA))
	var q := Vector2(p.x, p.z)
	var fronta: Array = []
	var rd := int(ceil(DAL / BUNKA)) + 1
	for dx in range(-rd, rd + 1):
		for dz in range(-rd, rd + 1):
			var c := c0 + Vector2i(dx, dz)
			var d := Vector2((c.x + 0.5) * BUNKA, (c.y + 0.5) * BUNKA).distance_to(q)
			if d < BLIZ + BUNKA * 0.75 and not _bliz.has(c):
				fronta.append([d, c, true])
			elif d < DAL + BUNKA * 0.75 and not _dal.has(c):
				fronta.append([d + 1000.0, c, false])
	fronta.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	for i in mini(NA_SNIMEK, fronta.size()):
		var c: Vector2i = fronta[i][1]
		if fronta[i][2]:
			_bliz[c] = _postav_bliz(c)
		else:
			_dal[c] = _postav_dal(c)
	# kupy: v kazdem pasmu nejblizsi chybejici bunka za snimek (i za chuze)
	for li in KUPY.size():
		var L: Array = KUPY[li]
		var bk: float = L[0]
		var dosah: float = L[2]
		var hot: Dictionary = _kupy[li]
		var co := Vector2i(floori(p.x / bk), floori(p.z / bk))
		var ro := int(ceil(dosah / bk)) + 1
		var best := Vector2i(0, 0)
		var bd := 1e9
		for dx in range(-ro, ro + 1):
			for dz in range(-ro, ro + 1):
				var c := co + Vector2i(dx, dz)
				if hot.has(c):
					continue
				var d := Vector2((c.x + 0.5) * bk, (c.y + 0.5) * bk).distance_to(q)
				if d < dosah + bk * 0.75 and d < bd:
					bd = d
					best = c
		if bd < 1e9:
			hot[best] = _postav_kupy(best, L)
		for c: Vector2i in hot.keys():
			if Vector2((c.x + 0.5) * bk, (c.y + 0.5) * bk).distance_to(q) > dosah + bk * 2.0:
				var n: Node = hot[c]
				if n:
					n.queue_free()
				hot.erase(c)
	# uvolnit vzdalene
	for dct: Dictionary in [_bliz, _dal]:
		var lim := (BLIZ if dct == _bliz else DAL) + BUNKA * 2.0
		for c: Vector2i in dct.keys():
			if Vector2((c.x + 0.5) * BUNKA, (c.y + 0.5) * BUNKA).distance_to(q) > lim:
				var n: Node = dct[c]
				if n:
					n.queue_free()
				dct.erase(c)


func _mm(root: Node3D, mesh: Mesh, xfs: Array, cen: Vector3, dos0: float, dos1: float, stin: bool) -> void:
	if xfs.is_empty():
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = xfs.size()
	for i in xfs.size():
		var t: Transform3D = xfs[i]
		t.origin -= cen
		mm.set_instance_transform(i, t)
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.position = cen
	# prolinani dela shader (po trsech, i v rendereru compatibility); viditelnost jen hrube orezava
	var mat := mesh.surface_get_material(0)
	if mat is ShaderMaterial:
		mmi.material_override = _mat_pas(mat, dos0, dos1)
	if dos0 > 0.0:
		mmi.visibility_range_begin = maxf(0.0, dos0 - 20.0)
	mmi.visibility_range_end = dos1 + 30.0 if mat is ShaderMaterial else dos1
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if stin else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mmi)


var _mat_cache := {}


func _mat_pas(mat: Material, od: float, do_: float) -> Material:
	var key := "%d_%d_%d" % [mat.get_instance_id(), int(od), int(do_)]
	if not _mat_cache.has(key):
		var m := mat.duplicate() as ShaderMaterial
		m.set_shader_parameter("fade_od", od if od > 0.0 else -1.0)
		m.set_shader_parameter("fade_do", do_)
		_mat_cache[key] = m
	return _mat_cache[key]


func _postav_bliz(c: Vector2i) -> Node3D:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(c) ^ 0x5eed
	var cen := Vector3((c.x + 0.5) * BUNKA, 0.0, (c.y + 0.5) * BUNKA)
	var vrstvy := {}                  # index site -> [xf]
	var krok := BLIZ_KROK / sqrt(hustota)
	var x := 0.0
	var celkem := 0
	while x < BUNKA:
		var z := 0.0
		while z < BUNKA:
			var px := c.x * BUNKA + x + rng.randf_range(-0.45, 0.45) * krok
			var pz := c.y * BUNKA + z + rng.randf_range(-0.45, 0.45) * krok
			z += krok
			var v := _vzorek(px, pz)
			if v.x < 0.1 or rng.randf() > v.x * 1.6:
				continue
			var n1 := _sum.get_noise_2d(px, pz) * 0.5 + 0.5
			var n2 := _sum2.get_noise_2d(px, pz) * 0.5 + 0.5
			var typ := 0 if n1 < 0.45 else (1 if n1 < 0.72 else 2)
			if n2 > 0.72:
				typ = 3
			if v.x < 0.45:
				typ = 2 if rng.randf() < 0.5 else 1          # lem cest a okraje: vyssi trava
			elif rng.randf() < 0.25:
				typ = rng.randi() % 3
			var s := rng.randf_range(0.75, 1.25) * lerpf(0.85, 1.15, v.x)
			if not vrstvy.has(typ):
				vrstvy[typ] = []
			vrstvy[typ].append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.85, 1.25), s)),
					Vector3(px, v.y - 0.03, pz)))
			celkem += 1
			if rng.randf() < 0.22:
				var t := 5 + rng.randi() % 3
				var s2 := rng.randf_range(0.8, 1.4)
				if not vrstvy.has(t):
					vrstvy[t] = []
				vrstvy[t].append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s2, s2, s2)),
						Vector3(px + rng.randf_range(-0.2, 0.2), v.y - 0.01, pz + rng.randf_range(-0.2, 0.2))))
		x += krok
	# kvety ve skupinkach (na louce, ne v lese ani na cestach)
	var kv := {}
	var nsk := rng.randi_range(0, 3) if hustota > 0.5 else rng.randi_range(0, 1)
	for _i in nsk:
		var cx := c.x * BUNKA + rng.randf() * BUNKA
		var cz := c.y * BUNKA + rng.randf() * BUNKA
		if _vzorek(cx, cz).x < 0.55:
			continue
		var mi := rng.randi() % _kvety.size()
		var rr := rng.randf_range(0.8, 2.2)
		for _j in rng.randi_range(14, 40):
			var aa := rng.randf() * TAU
			var dd := sqrt(rng.randf()) * rr
			var px := cx + cos(aa) * dd
			var pz := cz + sin(aa) * dd
			var vv := _vzorek(px, pz)
			var s := rng.randf_range(1.1, 1.9)
			if not kv.has(mi):
				kv[mi] = []
			kv[mi].append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(px, vv.y - 0.03, pz)))
	if celkem == 0 and kv.is_empty():
		return null
	var root := Node3D.new()
	add_child(root)
	var stin: bool = int(main.quality) > 0
	for t: int in vrstvy:
		_mm(root, _trsy[t], vrstvy[t], cen, 0.0, BLIZ - 8.0, stin and t <= 3)
	for mi: int in kv:
		_mm(root, _kvety[mi], kv[mi], cen, 0.0, BLIZ, false)
	_n_trsu += celkem
	return root


func _postav_kupy(c: Vector2i, L: Array) -> Node3D:
	# kupy travy (nizka hruda s trcicimi stebly): souvisla zelena hmota nad zemi i daleko
	var bk: float = L[0]
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(c) ^ (0x0b20 + int(bk))
	var cen := Vector3((c.x + 0.5) * bk, 0.0, (c.y + 0.5) * bk)
	var xfs: Array = []
	var s0: float = L[3]
	var s1: float = L[4]
	var pl := PI * pow((s0 + s1) * 0.5, 2.0)        # plocha jedne kupy
	var n := int(bk * bk / pl * float(L[5]) * 1.3 * lerpf(0.6, 1.0, hustota))
	for _i in n:
		var px := c.x * bk + rng.randf() * bk
		var pz := c.y * bk + rng.randf() * bk
		var v := _vzorek(px, pz)
		if v.x < 0.12 or rng.randf() > v.x * 1.3:
			continue
		var n1 := _sum.get_noise_2d(px, pz) * 0.5 + 0.5
		var s := rng.randf_range(s0, s1) * lerpf(0.8, 1.2, n1)
		xfs.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.7, 1.1) * lerpf(0.9, 1.25, v.x), s)),
				Vector3(px, v.y - 0.08 * s, pz)))
	if xfs.is_empty():
		return null
	var root := Node3D.new()
	add_child(root)
	_mm(root, _kupa, xfs, cen, float(L[1]), float(L[2]), false)
	return root


func _kupa_mesh(seed: int) -> Mesh:
	# hruda (polokoule, nerovna) a kolem a navrch siroka stebla - zdalky zrnita travni hmota
	var r := RandomNumberGenerator.new()
	r.seed = seed
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pata := Color(0.07, 0.12, 0.04)
	var vrch := Color(0.2, 0.33, 0.1)
	var nx := 10
	var rows: Array = []
	for j in 3:
		var th := PI * 0.5 * (1.0 - j / 2.0)
		var row: Array = []
		for i in nx:
			var ph := TAU * i / nx
			var k := r.randf_range(0.85, 1.12) if j < 2 else 1.0
			row.append(Vector3(sin(th) * cos(ph) * k, cos(th) * 0.42 * k, sin(th) * sin(ph) * k))
		rows.append(row)
	for j in 2:
		for i in nx:
			var a: Vector3 = rows[j][i]
			var b: Vector3 = rows[j][(i + 1) % nx]
			var c2: Vector3 = rows[j + 1][i]
			var d2: Vector3 = rows[j + 1][(i + 1) % nx]
			for v: Vector3 in [a, c2, d2, a, d2, b]:
				var t := clampf(v.y / 0.42, 0.0, 1.0)
				st.set_color(pata.lerp(vrch, t) * r.randf_range(0.92, 1.08))
				st.set_uv(Vector2(0, 0.3 + 0.7 * t))
				st.set_normal(Vector3.UP)
				st.add_vertex(v)
	# stebla z povrchu hrudy (obrys neni hladky)
	var spicky := [Color(0.22, 0.38, 0.1), Color(0.28, 0.42, 0.12), Color(0.42, 0.44, 0.18), Color(0.18, 0.32, 0.12)]
	for i in 34:
		var a := r.randf() * TAU
		var d := sqrt(r.randf()) * 0.95
		var base := Vector3(cos(a) * d, 0.42 * sqrt(maxf(0.0, 1.0 - d * d)) - 0.05, sin(a) * d)
		var smer := Vector3(cos(a), 0, sin(a)) * (0.15 + d * 0.5)
		var h := r.randf_range(0.2, 0.45)
		var top := base + Vector3(0, h, 0) + smer * h
		var bok := Vector3(-sin(a), 0, cos(a)) * r.randf_range(0.05, 0.09)
		var tip: Color = spicky[r.randi() % 4] * r.randf_range(0.85, 1.12)
		for q: Array in [[base - bok, 0.3, pata], [base + bok, 0.3, pata], [top, 1.0, tip]]:
			st.set_color(q[2])
			st.set_uv(Vector2(0, q[1]))
			st.set_normal(Vector3.UP)
			st.add_vertex(q[0])
	var mesh := st.commit()
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://shaders/stebla.gdshader")
	mat.set_shader_parameter("vitr", 0.25)
	mesh.surface_set_material(0, mat)
	return mesh


func _postav_dal(c: Vector2i) -> Node3D:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(c) ^ 0xd1a1
	var cen := Vector3((c.x + 0.5) * BUNKA, 0.0, (c.y + 0.5) * BUNKA)
	var xfs: Array = []
	var n := int(BUNKA * BUNKA * DAL_HUST * hustota)
	for _i in n:
		var px := c.x * BUNKA + rng.randf() * BUNKA
		var pz := c.y * BUNKA + rng.randf() * BUNKA
		var v := _vzorek(px, pz)
		if v.x < 0.12 or rng.randf() > v.x * 1.4:
			continue
		var s := rng.randf_range(0.8, 1.3) * lerpf(0.8, 1.2, _sum.get_noise_2d(px, pz) * 0.5 + 0.5)
		xfs.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(px, v.y - 0.03, pz)))
	if xfs.is_empty():
		return null
	var root := Node3D.new()
	add_child(root)
	_mm(root, _trsy[4], xfs, cen, 0.0, DAL, false)
	return root



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
			var c2 := Color(0.42, 0.42, 0.26)
			for q: Array in [[b - bok * 0.004, 0.0, c1], [b + bok * 0.004, 0.0, c1], [top + bok * 0.004, 1.0, c1],
					[b - bok * 0.004, 0.0, c1], [top + bok * 0.004, 1.0, c1], [top - bok * 0.004, 1.0, c1]]:
				st.set_color(q[2]); st.set_uv(Vector2(0, q[1])); st.set_normal(Vector3.UP); st.add_vertex(q[0])
			# lata: tenke klasky stridave podel konce stonku (ne kornout)
			for q in 7:
				var t := 0.55 + 0.45 * q / 6.0
				var p0 := b.lerp(top, t)
				var sm := (bok if q % 2 == 0 else -bok) * 0.03 + Vector3(0, 0.035, 0)
				var c3 := c2 * r.randf_range(0.85, 1.1)
				for v: Vector3 in [p0, p0 + sm + bok * 0.003, p0 + sm - bok * 0.003]:
					st.set_color(c3); st.set_uv(Vector2(0, 1.0)); st.set_normal(Vector3.UP); st.add_vertex(v)
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
