extends Node3D
## Louka v cele krajine (postup odladeny na zkusebni louce): kolem hrace se po bunkach 16 m generuje
## blizko (do ~38 m) husty koberec trsu, byliny (jitrocel, kapradi, drobne kvety) a kvety ve skupinkach,
## dal (do ~115 m) ridsi vetsi trsy, aby louka pokracovala k obzoru. Trs = 3 zkrizene karty (6 troj.) s obrazkem
## z atlasu obrazky/trava_atlas.png (fotky naskenovanych trsu, blender/atlas_travy.py); bunku vybira custom.b.
## Hustota z mrizek Blenderu (trava_kraj = krajina, trava_ves = ves). Vse deterministicke podle bunky (stejne pri navratu).
## Pasma se prekryvaji: stredni trsy stoji uz od nohou (blizke jen pridava detail), kupy travy (zelena hmota)
## zacinaji pred koncem trsu - pri chuzi nic "nevyrusta z niceho".
## LADENI VYKONU (kdyz se seka, ubirat tady): BLIZ_KROK vetsi = ridsi blizko, DAL/KUPY dosah, *_HUST hustota.

const BUNKA := 32.0                   # velke bunky: 4x mene objektu a volani kresleni (pady ovladace pri ~7500 volanich)
const BLIZ := 25.0                    # husty koberec stebel, byliny, kvety
const BLIZ_KROK := 0.36               # rozestup trsu blizko (m)
const DAL := 100.0                    # siroke trsy od nohou az sem
const DAL_HUST := 1.2                 # trsu na m2
const NA_SNIMEK := 1                  # bunek za snimek (vic = zakousnuti pri behu)
const KUPY := [                       # kupy travy: [bunka, od, do, meritko min, max, pokryti]
	[64.0, 80.0, 280.0, 1.2, 2.0, 0.5],          # velke bunky: malo objektu (pad pri hromadnem pridavani, 16. 10.)
	[128.0, 240.0, 650.0, 2.6, 4.2, 0.4],
]

var main: Node
var hustota := 1.0
var _mriz: Array = []                 # [{x0, z0, k, nx, nz, ys, ms}]
var _trs: Mesh                        # trs travy = 3 zkrizene karty s obrazkem z atlasu (bunku vybira custom.b)
var _trs_dal: Mesh
var _kvety: Array = []
var _sum := FastNoiseLite.new()
var _sum2 := FastNoiseLite.new()
var _bliz := {}                       # Vector2i -> Node3D (nebo null)
var _dal := {}
var _kupy: Array = [{}, {}]
var _kupa: Mesh
var _snimek := 0
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
	_trs = _karta_mesh(3, ATLAS_POMER, 1.0, 0.0, 0.0, 1.0)          # blizko: trs vysoky 1 (meritko instance = vyska v m)
	_trs_dal = _karta_mesh(3, ATLAS_POMER * 1.15, 1.0, 0.0, 0.0, 0.6)  # stredni pasmo: o neco sirsi karty, mene vetru
	_kvety.append(_kvety_atlas([[Color(1.0, 0.85, 0.15), Color(0.9, 0.55, 0.05)], [Color(0.98, 0.98, 0.93), Color(1.0, 0.85, 0.2)],
			[Color(0.95, 0.55, 0.75), Color(0.75, 0.3, 0.45)], [Color(0.6, 0.45, 0.9), Color(0.95, 0.9, 0.5)]]))
	_kupa = _karta_mesh(3, 1.9, 0.6, 0.3, 0.08, 0.25)               # kupa (jako drive hruda o prumeru 2): husty spodek bunky
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
	# kupy: stridave jedno pasmo za snimek, jen kdyz blizke a stredni pasmo nic nestavelo
	_snimek += 1
	for li in ([(_snimek / 3) % KUPY.size()] if fronta.is_empty() and _snimek % 3 == 0 else []):
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


func _mm(root: Node3D, mesh: Mesh, xfs: Array, cen: Vector3, dos0: float, dos1: float, stin: bool, cust: Array = []) -> void:
	if xfs.is_empty():
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = not cust.is_empty()
	mm.mesh = mesh
	mm.instance_count = xfs.size()
	for i in xfs.size():
		var t: Transform3D = xfs[i]
		t.origin -= cen
		mm.set_instance_transform(i, t)
		if not cust.is_empty():
			mm.set_instance_custom_data(i, cust[i])
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
	var vrstvy: Array = []            # [[xf], [custom]] - vsechny trsy bunky v jednom MultiMeshi
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
			# karta z atlasu podle druhu (bunka, vyska karty v m); nizka/stredni/vysoka/sucha = jedna sit, rozdil dela
			# bunka atlasu, meritko a barva (custom)
			var bun := 0
			var h := 0.3
			var such := rng.randf() * 0.15
			if typ == 1:
				bun = 0 if rng.randf() < 0.5 else 1
				h = 0.42 if bun == 0 else 0.5
			elif typ == 2:
				bun = 1
				h = 0.68
			elif typ == 3:
				bun = 2
				h = 0.5
				such = 0.1
			h *= s * 1.2                                   # karta je ridsi nez stebla: o neco vetsi, aby zakryla zem
			var vy := h * rng.randf_range(0.85, 1.15)
			_trs_pridej(vrstvy, Vector3(px, v.y - 0.04, pz), rng.randf() * TAU, h, vy, Color(such, rng.randf(), (bun + 0.5) / 6.0, 1.0))
			celkem += 1
			if rng.randf() < 0.22:
				# byliny mezi travou: jitrocel, drobne kvety, na okrajich (u lesa a cest) kapradi
				var s2 := rng.randf_range(0.8, 1.4)
				var bb := 3
				var hb := 0.28
				var r2 := rng.randf()
				if v.x < 0.45 and r2 < 0.3:
					bb = 4
					hb = 0.55
				elif r2 < 0.18:
					bb = 5
					hb = 0.32
				_trs_pridej(vrstvy, Vector3(px + rng.randf_range(-0.2, 0.2), v.y - 0.03, pz + rng.randf_range(-0.2, 0.2)),
						rng.randf() * TAU, hb * s2, hb * s2, Color(0.0, rng.randf(), (bb + 0.5) / 6.0, 1.0))
		x += krok
	# kvety ve skupinkach (na louce, ne v lese ani na cestach)
	var kv := {}
	var nsk := (rng.randi_range(0, 3) if hustota > 0.5 else rng.randi_range(0, 1)) * int(BUNKA * BUNKA / 256.0)   # skupinky kvetu na 16x16 m
	for _i in nsk:
		var cx := c.x * BUNKA + rng.randf() * BUNKA
		var cz := c.y * BUNKA + rng.randf() * BUNKA
		if _vzorek(cx, cz).x < 0.55:
			continue
		var mi := rng.randi() % 4
		var rr := rng.randf_range(0.8, 2.2)
		for _j in rng.randi_range(14, 40):
			var aa := rng.randf() * TAU
			var dd := sqrt(rng.randf()) * rr
			var px := cx + cos(aa) * dd
			var pz := cz + sin(aa) * dd
			var vv := _vzorek(px, pz)
			var s := rng.randf_range(1.1, 1.9)
			if not kv.has(0):
				kv[0] = [[], []]
			kv[0][0].append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(px, vv.y - 0.03, pz)))
			kv[0][1].append(Color(mi * 0.25, 0.0, 0.0, 1.0))
	if celkem == 0 and kv.is_empty():
		return null
	var root := Node3D.new()
	root.name = "bliz"
	add_child(root)
	if not vrstvy.is_empty():
		_mm(root, _trs, vrstvy[0], cen, 0.0, BLIZ - 8.0, false, vrstvy[1])   # trava i byliny jednim volanim, bez stinu
	if kv.has(0):
		_mm(root, _kvety[0], kv[0][0], cen, 0.0, BLIZ, false, kv[0][1])
	_n_trsu += celkem
	return root


func _trs_pridej(vrstvy: Array, pos: Vector3, rot: float, h: float, vy: float, cust: Color) -> void:
	if vrstvy.is_empty():
		vrstvy.append_array([[], []])
	vrstvy[0].append(Transform3D(Basis(Vector3.UP, rot).scaled(Vector3(h, vy, h)), pos))
	vrstvy[1].append(cust)


func _postav_kupy(c: Vector2i, L: Array) -> Node3D:
	# kupy travy (siroke nizke karty z husteho spodku bunky atlasu): souvisla zelena hmota nad zemi i daleko
	var bk: float = L[0]
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(c) ^ (0x0b20 + int(bk))
	var cen := Vector3((c.x + 0.5) * bk, 0.0, (c.y + 0.5) * bk)
	var xfs: Array = []
	var cust: Array = []
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
		# nizka trava, misty sucha (stejne skvrny jako blizko)
		var bun := 2 if _sum2.get_noise_2d(px, pz) * 0.5 + 0.5 > 0.72 else (0 if rng.randf() < 0.7 else 1)
		cust.append(Color(rng.randf() * 0.15, rng.randf(), (bun + 0.5) / 6.0, 1.0))
	if xfs.is_empty():
		return null
	var root := Node3D.new()
	root.name = "kupy_mala" if bk < 100.0 else "kupy_velka"
	add_child(root)
	_mm(root, _kupa, xfs, cen, float(L[1]), float(L[2]), false, cust)
	return root


func _postav_dal(c: Vector2i) -> Node3D:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(c) ^ 0xd1a1
	var cen := Vector3((c.x + 0.5) * BUNKA, 0.0, (c.y + 0.5) * BUNKA)
	var xfs: Array = []
	var cust: Array = []
	var n := int(BUNKA * BUNKA * DAL_HUST * hustota)
	for _i in n:
		var px := c.x * BUNKA + rng.randf() * BUNKA
		var pz := c.y * BUNKA + rng.randf() * BUNKA
		var v := _vzorek(px, pz)
		if v.x < 0.12 or rng.randf() > v.x * 1.4:
			continue
		var n1 := _sum.get_noise_2d(px, pz) * 0.5 + 0.5
		var s := rng.randf_range(0.8, 1.3) * lerpf(0.8, 1.2, n1)
		# druh jako blizko (stejny sum): nizka / vyssi / sucha trava; vyska karty v m
		var bun := 0 if n1 < 0.45 else 1
		if _sum2.get_noise_2d(px, pz) * 0.5 + 0.5 > 0.72:
			bun = 2
		var h := s * (0.6 if bun == 0 else 0.75)          # vetsi nez blizko: ridsi pasmo musi zakryt zem
		xfs.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(h, h * rng.randf_range(0.85, 1.15), h)), Vector3(px, v.y - 0.04, pz)))
		cust.append(Color(rng.randf() * 0.15, rng.randf(), (bun + 0.5) / 6.0, 1.0))
	if xfs.is_empty():
		return null
	var root := Node3D.new()
	root.name = "dal"
	add_child(root)
	_mm(root, _trs_dal, xfs, cen, 0.0, DAL, false, cust)
	return root



## Vsechny kvety v jednom MultiMeshi (rozpocet kresleni): atlas 4 barev vedle sebe, barvu vybira INSTANCE_CUSTOM.r.
func _kvety_atlas(barvy: Array) -> Mesh:
	var atlas := Image.create(512, 128, false, Image.FORMAT_RGBA8)
	for i in barvy.size():
		var im := _kvet_img(barvy[i][0], barvy[i][1], i * 31 + 5)
		atlas.blit_rect(im, Rect2i(0, 0, 128, 128), Vector2i(i * 128, 0))
	atlas.generate_mipmaps()
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://shaders/kvety.gdshader")
	mat.set_shader_parameter("atlas", ImageTexture.create_from_image(atlas))
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


func _kvet_img(barva: Color, stred: Color, seed: int) -> Image:
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
	return img


# ------------------------------------------------------------------ trsy travy z karet (atlas)


const ATLAS_POMER := 341.0 / 256.0      # sirka : vyska bunky atlasu obrazky/trava_atlas.png (3x2 bunky, 1024x512)


## Trs = n zkrizenych svislych karet (n = 3: 6 troj., obe strany: cull_disabled v shaderu), sirka x vyska v jednotkach
## meritka instance. UV v ramci bunky (v = 0 nahore); bunku atlasu vybira INSTANCE_CUSTOM.b.
## orez = kolik shora bunky vynechat (kupy berou jen husty spodek), ponor = o kolik karta zasahuje pod zem.
func _karta_mesh(n: int, sirka: float, vyska: float, orez: float, ponor: float, vitr: float) -> Mesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hw := 0.5 * sirka
	# karty se nekrizi v jednom bode a lisi se vyskou a zrcadlenim: shora neni videt hvezdice, zboku opakovani
	var posun := [Vector3(0.0, 0, 0.0), Vector3(0.09, 0, -0.06), Vector3(-0.07, 0, 0.08), Vector3(0.05, 0, 0.1)]
	var vysky := [1.0, 0.86, 0.93, 0.8]
	for q in n:
		var ang := PI * q / n + 0.35
		var tg := Vector3(cos(ang), 0, sin(ang)) * hw
		var nrm := Vector3(-sin(ang), 0, cos(ang))
		var stred: Vector3 = posun[q % 4] * sirka
		var up := Vector3(0, vyska * float(vysky[q % 4]), 0)
		var dole := Vector3(0, -ponor, 0)
		var pts := [stred - tg + dole, stred + tg + dole, stred + tg + up, stred - tg + up]
		var u0 := 1.0 if q == 1 else 0.0
		var uvs := [Vector2(u0, 1), Vector2(1.0 - u0, 1), Vector2(1.0 - u0, orez), Vector2(u0, orez)]
		for i: int in [0, 1, 2, 0, 2, 3]:
			st.set_uv(uvs[i])
			st.set_normal(nrm)
			st.add_vertex(pts[i])
	var mesh := st.commit()
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://shaders/stebla.gdshader")
	mat.set_shader_parameter("atlas", preload("res://obrazky/trava_atlas.png"))
	mat.set_shader_parameter("vitr", vitr)
	mesh.surface_set_material(0, mat)
	return mesh


# ------------------------------------------------------------------ stavba
